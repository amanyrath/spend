"""Vectorized persona assignment using pandas.

This module provides a faster alternative to assign_all.py by loading
all user features at once and using vectorized operations for persona
score calculations.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import db
from src.personas.assignment import (
    calculate_persona_scores_vectorized,
    PERSONA_HIGH_UTILIZATION,
    PERSONA_VARIABLE_INCOME,
    PERSONA_SUBSCRIPTION_HEAVY,
    PERSONA_SAVINGS_BUILDER,
    PERSONA_GENERAL_WELLNESS
)
from src.database.db_config import USE_FIRESTORE


def load_all_user_features(time_windows: List[str] = None, use_sqlite: bool = False) -> pd.DataFrame:
    """Batch load all user features from database into pandas DataFrame.
    
    Args:
        time_windows: List of time windows to load (e.g., ['30d', '180d']). 
                     If None, loads all time windows.
        use_sqlite: If True, force use of SQLite even if Firestore is available
        
    Returns:
        DataFrame with columns: user_id, time_window, signal_type, signal_data
        where signal_data is parsed from JSON
    """
    use_firestore = USE_FIRESTORE and not use_sqlite
    if use_firestore:
        print("Error: Vectorized operations require SQLite database.")
        print("Use --sqlite flag or run assign_all.py instead.")
        return pd.DataFrame()
    
    # Build query
    if time_windows:
        placeholders = ','.join(['?' for _ in time_windows])
        query = f"""
            SELECT user_id, time_window, signal_type, signal_data
            FROM computed_features
            WHERE time_window IN ({placeholders})
            ORDER BY user_id, time_window, signal_type
        """
        params = tuple(time_windows)
    else:
        query = """
            SELECT user_id, time_window, signal_type, signal_data
            FROM computed_features
            ORDER BY user_id, time_window, signal_type
        """
        params = ()
    
    rows = db.fetch_all(query, params)
    
    if not rows:
        return pd.DataFrame(columns=['user_id', 'time_window', 'signal_type', 'signal_data'])
    
    # Convert to DataFrame
    df = pd.DataFrame([dict(row) for row in rows])
    
    # Parse signal_data JSON
    def parse_signal_data(signal_json):
        if pd.isna(signal_json):
            return {}
        try:
            return json.loads(signal_json) if isinstance(signal_json, str) else signal_json
        except (json.JSONDecodeError, TypeError):
            return {}
    
    df['signal_data'] = df['signal_data'].apply(parse_signal_data)
    
    return df


def pivot_features_to_wide(features_df: pd.DataFrame) -> pd.DataFrame:
    """Transform features DataFrame from long to wide format.
    
    Args:
        features_df: DataFrame with columns: user_id, time_window, signal_type, signal_data
        
    Returns:
        DataFrame with columns: user_id, time_window, subscriptions, credit_utilization,
        savings_behavior, income_stability where each column contains the signal_data dict
    """
    if features_df.empty:
        return pd.DataFrame(columns=['user_id', 'time_window', 'subscriptions', 
                                     'credit_utilization', 'savings_behavior', 'income_stability'])
    
    # Pivot to wide format
    pivoted = features_df.pivot_table(
        index=['user_id', 'time_window'],
        columns='signal_type',
        values='signal_data',
        aggfunc='first'  # Should only be one value per (user_id, time_window, signal_type)
    ).reset_index()
    
    # Ensure all expected columns exist
    expected_signals = ['subscriptions', 'credit_utilization', 'savings_behavior', 'income_stability']
    for signal in expected_signals:
        if signal not in pivoted.columns:
            pivoted[signal] = pd.Series([{}] * len(pivoted), dtype=object)
    
    # Fill NaN values with empty dicts
    for signal in expected_signals:
        pivoted[signal] = pivoted[signal].fillna({}).apply(lambda x: x if isinstance(x, dict) else {})
    
    return pivoted


def store_personas_vectorized(personas_df: pd.DataFrame, use_sqlite: bool = False) -> int:
    """Batch write persona assignments to database.
    
    Args:
        personas_df: DataFrame with columns: user_id, time_window, persona, 
                    match_high_utilization, match_variable_income, match_subscription_heavy,
                    match_savings_builder, match_general_wellness, primary_persona,
                    criteria_met, match_percentages, criteria_details
        use_sqlite: If True, force use of SQLite even if Firestore is available
        
    Returns:
        Number of persona assignments stored
    """
    # Check if we should use Firestore (unless explicitly told to use SQLite)
    use_firestore = USE_FIRESTORE and not use_sqlite
    if use_firestore:
        print("Error: Vectorized operations require SQLite database.")
        return 0
    
    if personas_df.empty:
        return 0
    
    assigned_at = datetime.now().isoformat()
    stored_count = 0
    
    with db.get_db_connection() as conn:
        for _, row in personas_df.iterrows():
            user_id = row['user_id']
            time_window = row['time_window']
            persona = row['persona']
            primary_persona = row.get('primary_persona', persona)
            
            # Serialize criteria_met
            criteria_met = row.get('criteria_met', [])
            if isinstance(criteria_met, str):
                try:
                    criteria_met = json.loads(criteria_met)
                except:
                    criteria_met = []
            criteria_json = json.dumps(criteria_met) if criteria_met else '[]'
            
            # Extract match percentages
            match_high_util = float(row.get('match_high_utilization', 0.0))
            match_var_income = float(row.get('match_variable_income', 0.0))
            match_sub_heavy = float(row.get('match_subscription_heavy', 0.0))
            match_savings = float(row.get('match_savings_builder', 0.0))
            match_general = float(row.get('match_general_wellness', 0.0))
            
            # Delete existing assignment if it exists
            delete_query = """
                DELETE FROM persona_assignments
                WHERE user_id = ? AND time_window = ?
            """
            conn.execute(delete_query, (user_id, time_window))
            
            # Insert new assignment
            insert_query = """
                INSERT INTO persona_assignments (
                    user_id, time_window, persona, criteria_met, assigned_at,
                    match_high_utilization, match_variable_income, match_subscription_heavy,
                    match_savings_builder, match_general_wellness, primary_persona
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            conn.execute(insert_query, (
                user_id, time_window, persona, criteria_json, assigned_at,
                match_high_util, match_var_income, match_sub_heavy,
                match_savings, match_general, primary_persona
            ))
            
            stored_count += 1
        
        conn.commit()
    
    return stored_count


def assign_all_users_vectorized(time_windows: List[str] = None, 
                                 users: List[str] = None,
                                 use_sqlite: bool = False,
                                 verbose: bool = True) -> Dict[str, Any]:
    """Assign personas to all users using vectorized operations.
    
    Args:
        time_windows: List of time windows to process (e.g., ['30d', '180d']).
                     If None, processes all available time windows.
        users: Optional list of user_ids to process (None = all users)
        use_sqlite: If True, force use of SQLite even if Firestore is available
        verbose: If True, show progress
        
    Returns:
        Dictionary with stats: total_users, total_assigned, persona_counts
    """
    use_firestore = USE_FIRESTORE and not use_sqlite
    if use_firestore:
        print("Error: Vectorized operations require SQLite database.")
        print("Use --sqlite flag or run assign_all.py instead.")
        return {}
    
    # Ensure database schema is initialized
    if verbose:
        print("Ensuring database schema is initialized...")
    db.init_schema()
    if verbose:
        print("Schema check complete.\n")
    
    # Default time windows if not specified
    if time_windows is None:
        time_windows = ['30d', '180d']
    
    if verbose:
        print(f"Loading all user features for time windows: {', '.join(time_windows)}...")
    
    start_time = datetime.now()
    
    # Load all features
    features_df = load_all_user_features(time_windows, use_sqlite=use_sqlite)
    
    if features_df.empty:
        print("No user features found in database.")
        print("Please run compute_all_features_vectorized.py first to compute features.")
        return {}
    
    load_time = (datetime.now() - start_time).total_seconds()
    
    if verbose:
        print(f"  Loaded {len(features_df):,} feature records in {load_time:.1f}s")
    
    # Filter to specific users if requested
    if users:
        features_df = features_df[features_df['user_id'].isin(users)]
    
    # Get unique user-time_window combinations
    unique_combos = features_df[['user_id', 'time_window']].drop_duplicates()
    total_combos = len(unique_combos)
    
    if verbose:
        print(f"  Processing {total_combos} user-time_window combinations...")
    
    # Pivot to wide format
    if verbose:
        print("  Transforming features to wide format...")
    features_wide = pivot_features_to_wide(features_df)
    
    if features_wide.empty:
        print("No valid features found after transformation.")
        return {}
    
    # Calculate persona scores for all users
    if verbose:
        print("  Calculating persona scores...")
    compute_start = datetime.now()
    
    personas_df = calculate_persona_scores_vectorized(features_wide)
    
    compute_time = (datetime.now() - compute_start).total_seconds()
    
    if verbose:
        print(f"  Calculated persona scores in {compute_time:.1f}s")
        print(f"  Storing persona assignments...")
    
    # Store persona assignments
    store_start = datetime.now()
    stored_count = store_personas_vectorized(personas_df, use_sqlite=use_sqlite)
    store_time = (datetime.now() - store_start).total_seconds()
    
    if verbose:
        print(f"  Stored {stored_count} persona assignments in {store_time:.1f}s")
    
    # Calculate persona distribution
    persona_counts = {}
    if not personas_df.empty:
        persona_counts = personas_df['persona'].value_counts().to_dict()
    
    total_time = (datetime.now() - start_time).total_seconds()
    
    if verbose:
        print(f"\nCompleted! Assigned personas for {stored_count} user-time_window combinations.")
        print(f"Total time: {total_time:.1f}s")
        print("\nPersona distribution:")
        for persona, count in sorted(persona_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {persona}: {count}")
    
    return {
        'total_users': len(features_wide['user_id'].unique()),
        'total_assigned': stored_count,
        'persona_counts': persona_counts,
        'total_time': total_time
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Assign personas to all users using vectorized operations')
    parser.add_argument('--time-windows', nargs='+', default=['30d', '180d'],
                       help='Time windows to process (default: 30d 180d)')
    parser.add_argument('--users', nargs='+', default=None,
                       help='Specific user IDs to process (default: all users)')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress progress output')
    parser.add_argument('--sqlite', action='store_true',
                       help='Force use of SQLite even if Firestore is available')
    
    args = parser.parse_args()
    
    assign_all_users_vectorized(
        time_windows=args.time_windows,
        users=args.users,
        use_sqlite=args.sqlite,
        verbose=not args.quiet
    )

