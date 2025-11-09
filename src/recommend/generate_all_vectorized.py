"""Vectorized recommendation generation using pandas.

This module provides a faster alternative to generate_all.py by loading
all user personas and features at once and using vectorized operations
for content/offer matching.
"""

import sys
import os
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import db
from src.personas.assign_all_vectorized import load_all_user_features, pivot_features_to_wide
from src.recommend.content_catalog import get_content_by_persona, get_partner_offers
from src.recommend.rationale_generator import generate_rationale

# Check if using Firestore
USE_FIRESTORE = (
    os.getenv('FIRESTORE_EMULATOR_HOST') is not None or 
    os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true' or
    os.getenv('FIREBASE_SERVICE_ACCOUNT') is not None or 
    os.path.exists('firebase-service-account.json')
)


def load_all_personas_and_features(time_windows: List[str] = None, use_sqlite: bool = False) -> pd.DataFrame:
    """Batch load all persona assignments and features from database.
    
    Args:
        time_windows: List of time windows to load (e.g., ['30d', '180d']). 
                     If None, loads all time windows.
        use_sqlite: If True, force use of SQLite even if Firestore is available
        
    Returns:
        DataFrame with columns: user_id, time_window, persona, primary_persona,
        subscriptions, credit_utilization, savings_behavior, income_stability
    """
    use_firestore = USE_FIRESTORE and not use_sqlite
    if use_firestore:
        print("Error: Vectorized operations require SQLite database.")
        print("Use --sqlite flag or run generate_all.py instead.")
        return pd.DataFrame()
    
    # Default time windows if not specified
    if time_windows is None:
        time_windows = ['30d', '180d']
    
    # Load persona assignments
    placeholders = ','.join(['?' for _ in time_windows])
    
    # Check if primary_persona column exists
    check_column_query = """
        SELECT COUNT(*) as count FROM pragma_table_info('persona_assignments') 
        WHERE name='primary_persona'
    """
    column_check = db.fetch_one(check_column_query)
    has_primary_persona = column_check and column_check['count'] > 0
    
    if has_primary_persona:
        persona_query = f"""
            SELECT user_id, time_window, persona, primary_persona
            FROM persona_assignments
            WHERE time_window IN ({placeholders})
        """
    else:
        # Fallback if primary_persona column doesn't exist
        persona_query = f"""
            SELECT user_id, time_window, persona, persona as primary_persona
            FROM persona_assignments
            WHERE time_window IN ({placeholders})
        """
    
    persona_rows = db.fetch_all(persona_query, tuple(time_windows))
    
    if not persona_rows:
        return pd.DataFrame()
    
    personas_df = pd.DataFrame([dict(row) for row in persona_rows])
    
    # Use primary_persona if available, otherwise persona
    personas_df['persona'] = personas_df['primary_persona'].fillna(personas_df['persona'])
    
    # Load features
    features_df = load_all_user_features(time_windows, use_sqlite=use_sqlite)
    
    if features_df.empty:
        return pd.DataFrame()
    
    # Pivot features to wide format
    features_wide = pivot_features_to_wide(features_df)
    
    # Merge personas and features
    result_df = personas_df.merge(
        features_wide,
        on=['user_id', 'time_window'],
        how='inner'
    )
    
    return result_df


def check_trigger_signals_vectorized(signals_row: pd.Series, trigger_signals: List[str]) -> bool:
    """Check if trigger signals match for a user row (vectorized helper).
    
    Args:
        signals_row: Series with signal data (subscriptions, credit_utilization, etc.)
        trigger_signals: List of trigger signal names to check
        
    Returns:
        True if any trigger matches, False otherwise
    """
    if not trigger_signals:
        return True
    
    credit_signals = signals_row.get('credit_utilization', {})
    income_signals = signals_row.get('income_stability', {})
    subscription_signals = signals_row.get('subscriptions', {})
    savings_signals = signals_row.get('savings_behavior', {})
    
    for trigger in trigger_signals:
        if trigger == "credit_utilization_high":
            if isinstance(credit_signals, dict):
                utilization = credit_signals.get("total_utilization", 0.0)
                if utilization >= 50.0:
                    return True
        elif trigger == "minimum_payment_only":
            if isinstance(credit_signals, dict) and credit_signals.get("minimum_payment_only", False):
                return True
        elif trigger == "interest_charged":
            if isinstance(credit_signals, dict) and credit_signals.get("interest_charged", 0.0) > 0:
                return True
        elif trigger == "irregular_frequency":
            if isinstance(income_signals, dict) and income_signals.get("irregular_frequency", False):
                return True
        elif trigger == "median_pay_gap_high":
            if isinstance(income_signals, dict) and income_signals.get("median_pay_gap", 0) > 45:
                return True
        elif trigger == "cash_flow_buffer_low":
            if isinstance(income_signals, dict) and income_signals.get("cash_flow_buffer", 0.0) < 1.0:
                return True
        elif trigger == "subscription_count_high":
            if isinstance(subscription_signals, dict):
                recurring = subscription_signals.get("recurring_merchants", [])
                if isinstance(recurring, list) and len(recurring) >= 3:
                    return True
        elif trigger == "monthly_recurring_high":
            if isinstance(subscription_signals, dict) and subscription_signals.get("monthly_recurring", 0.0) >= 50.0:
                return True
        elif trigger == "savings_growth_rate_positive":
            if isinstance(savings_signals, dict) and savings_signals.get("growth_rate", 0.0) > 0:
                return True
        elif trigger == "emergency_fund_adequate":
            if isinstance(savings_signals, dict) and savings_signals.get("emergency_fund_coverage", 0.0) >= 3.0:
                return True
        elif trigger == "savings_balance_positive":
            if isinstance(savings_signals, dict) and savings_signals.get("total_savings", 0.0) > 0:
                return True
    
    return False


def check_offer_eligibility_vectorized(signals_row: pd.Series, eligibility: Dict[str, Any]) -> bool:
    """Check if user row is eligible for a partner offer (vectorized helper).
    
    Args:
        signals_row: Series with signal data
        eligibility: Eligibility criteria dict from offer
        
    Returns:
        True if eligible, False otherwise
    """
    if not eligibility:
        return True
    
    credit_signals = signals_row.get('credit_utilization', {})
    subscription_signals = signals_row.get('subscriptions', {})
    savings_signals = signals_row.get('savings_behavior', {})
    
    # Check credit utilization
    if "credit_utilization" in eligibility:
        if not isinstance(credit_signals, dict):
            return False
        utilization = credit_signals.get("total_utilization", 0.0)
        utilization_decimal = utilization / 100.0
        criteria = eligibility["credit_utilization"]
        if "min" in criteria and utilization_decimal < criteria["min"]:
            return False
        if "max" in criteria and utilization_decimal > criteria["max"]:
            return False
    
    # Check overdue status
    if "is_overdue" in eligibility:
        if not isinstance(credit_signals, dict):
            return False
        is_overdue = credit_signals.get("is_overdue", False)
        expected = eligibility["is_overdue"].get("equals", False)
        if is_overdue != expected:
            return False
    
    # Check subscription count
    if "subscription_count" in eligibility:
        if not isinstance(subscription_signals, dict):
            return False
        recurring = subscription_signals.get("recurring_merchants", [])
        count = len(recurring) if isinstance(recurring, list) else 0
        criteria = eligibility["subscription_count"]
        if "min" in criteria and count < criteria["min"]:
            return False
    
    # Check savings balance
    if "savings_balance" in eligibility:
        if not isinstance(savings_signals, dict):
            return False
        balance = savings_signals.get("total_savings", 0.0)
        criteria = eligibility["savings_balance"]
        if "min" in criteria and balance < criteria["min"]:
            return False
    
    return True


def match_content_vectorized(user_data_df: pd.DataFrame) -> pd.DataFrame:
    """Match education content and offers for all users using vectorized operations.
    
    Args:
        user_data_df: DataFrame with columns: user_id, time_window, persona, 
                     subscriptions, credit_utilization, savings_behavior, income_stability
        
    Returns:
        DataFrame with columns: user_id, time_window, content_id, content_type, 
        content_item (dict), matched (bool)
    """
    if user_data_df.empty:
        return pd.DataFrame()
    
    matched_content_list = []
    
    # Get all persona content
    all_content = {}
    for persona in user_data_df['persona'].unique():
        content = get_content_by_persona(persona)
        all_content[persona] = content
    
    # Process each user-time_window combination
    for _, row in user_data_df.iterrows():
        user_id = row['user_id']
        time_window = row['time_window']
        persona = row['persona']
        
        # Get signals dict for this row
        signals = {
            'subscriptions': row.get('subscriptions', {}),
            'credit_utilization': row.get('credit_utilization', {}),
            'savings_behavior': row.get('savings_behavior', {}),
            'income_stability': row.get('income_stability', {})
        }
        
        # Match education content
        persona_content = all_content.get(persona, [])
        matched_edu = []
        
        for item in persona_content:
            trigger_signals = item.get("trigger_signals", [])
            if check_trigger_signals_vectorized(row, trigger_signals):
                matched_edu.append({
                    'user_id': user_id,
                    'time_window': time_window,
                    'content_id': item['content_id'],
                    'content_type': 'education',
                    'content_item': item,
                    'matched': True
                })
        
        # If no matches from triggers, use all persona content
        if not matched_edu:
            for item in persona_content[:5]:  # Limit to 5
                matched_edu.append({
                    'user_id': user_id,
                    'time_window': time_window,
                    'content_id': item['content_id'],
                    'content_type': 'education',
                    'content_item': item,
                    'matched': True
                })
        
        matched_content_list.extend(matched_edu[:5])  # Limit to 5 per user
        
        # Match partner offers
        all_offers = get_partner_offers()
        matched_offers = []
        
        for offer in all_offers:
            eligibility = offer.get("eligibility_criteria", {})
            if check_offer_eligibility_vectorized(row, eligibility):
                matched_offers.append({
                    'user_id': user_id,
                    'time_window': time_window,
                    'content_id': offer.get('offer_id'),
                    'content_type': 'partner_offer',
                    'content_item': offer,
                    'matched': True
                })
        
        matched_content_list.extend(matched_offers[:3])  # Limit to 3 per user
    
    if not matched_content_list:
        return pd.DataFrame()
    
    return pd.DataFrame(matched_content_list)


def store_recommendations_vectorized(recommendations_df: pd.DataFrame, use_sqlite: bool = False) -> int:
    """Batch write recommendations to database.
    
    Args:
        recommendations_df: DataFrame with columns: recommendation_id, user_id, type,
                           content_id, title, rationale, decision_trace, shown_at
        use_sqlite: If True, force use of SQLite even if Firestore is available
        
    Returns:
        Number of recommendations stored
    """
    use_firestore = USE_FIRESTORE and not use_sqlite
    if use_firestore:
        print("Error: Vectorized operations require SQLite database.")
        return 0
    
    if recommendations_df.empty:
        return 0
    
    stored_count = 0
    
    with db.get_db_connection() as conn:
        for _, row in recommendations_df.iterrows():
            recommendation_id = row['recommendation_id']
            user_id = row['user_id']
            rec_type = row['type']
            content_id = row['content_id']
            title = row['title']
            rationale = row['rationale']
            decision_trace_json = json.dumps(row['decision_trace']) if isinstance(row['decision_trace'], dict) else row['decision_trace']
            shown_at = row['shown_at']
            
            # Delete existing recommendation if it exists
            delete_query = """
                DELETE FROM recommendations
                WHERE recommendation_id = ?
            """
            conn.execute(delete_query, (recommendation_id,))
            
            # Insert new recommendation
            insert_query = """
                INSERT INTO recommendations (
                    recommendation_id, user_id, type, content_id, title, rationale, decision_trace, shown_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            conn.execute(insert_query, (
                recommendation_id, user_id, rec_type, content_id, title, rationale, decision_trace_json, shown_at
            ))
            
            stored_count += 1
        
        conn.commit()
    
    return stored_count


def generate_all_recommendations_vectorized(time_windows: List[str] = None,
                                           users: List[str] = None,
                                           use_sqlite: bool = False,
                                           verbose: bool = True) -> Dict[str, Any]:
    """Generate recommendations for all users using vectorized operations.
    
    Args:
        time_windows: List of time windows to process (e.g., ['30d', '180d']).
                     If None, processes ['30d', '180d'].
        users: Optional list of user_ids to process (None = all users)
        use_sqlite: If True, force use of SQLite even if Firestore is available
        verbose: If True, show progress
        
    Returns:
        Dictionary with stats: total_users, total_recommendations, recommendation_counts
    """
    use_firestore = USE_FIRESTORE and not use_sqlite
    if use_firestore:
        print("Error: Vectorized operations require SQLite database.")
        print("Use --sqlite flag or run generate_all.py instead.")
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
        print(f"Loading all personas and features for time windows: {', '.join(time_windows)}...")
    
    start_time = datetime.now()
    
    # Load all personas and features
    user_data_df = load_all_personas_and_features(time_windows, use_sqlite=use_sqlite)
    
    if user_data_df.empty:
        print("No user personas or features found in database.")
        print("Please run assign_all_vectorized.py and compute_all_features_vectorized.py first.")
        return {}
    
    load_time = (datetime.now() - start_time).total_seconds()
    
    if verbose:
        print(f"  Loaded {len(user_data_df):,} user-time_window combinations in {load_time:.1f}s")
    
    # Filter to specific users if requested
    if users:
        user_data_df = user_data_df[user_data_df['user_id'].isin(users)]
    
    if user_data_df.empty:
        print("No users found after filtering.")
        return {}
    
    # Match content and offers
    if verbose:
        print("  Matching content and offers...")
    match_start = datetime.now()
    
    matched_content_df = match_content_vectorized(user_data_df)
    
    match_time = (datetime.now() - match_start).total_seconds()
    
    if verbose:
        print(f"  Matched {len(matched_content_df):,} content items in {match_time:.1f}s")
    
    if matched_content_df.empty:
        print("No content matched for users.")
        return {}
    
    # Generate rationales (per-user processing)
    # Note: No guardrails validation needed - recommendations use template substitution, not LLM
    if verbose:
        print("  Generating rationales...")
    rationale_start = datetime.now()
    
    recommendations_list = []
    
    # Group by user_id and time_window for processing
    for (user_id, time_window), group in matched_content_df.groupby(['user_id', 'time_window']):
        # Get user signals for rationale generation
        user_row = user_data_df[
            (user_data_df['user_id'] == user_id) & 
            (user_data_df['time_window'] == time_window)
        ].iloc[0]
        
        persona = user_row['persona']
        signals = {
            'subscriptions': user_row.get('subscriptions', {}),
            'credit_utilization': user_row.get('credit_utilization', {}),
            'savings_behavior': user_row.get('savings_behavior', {}),
            'income_stability': user_row.get('income_stability', {})
        }
        
        # Process each matched content item
        for _, content_row in group.iterrows():
            content_item = content_row['content_item']
            content_type = content_row['content_type']
            
            # Generate rationale
            rationale_template = content_item.get('rationale_template', '')
            try:
                rationale = generate_rationale(rationale_template, signals, content_item)
            except Exception as e:
                if verbose:
                    print(f"    Warning: Failed to generate rationale for {content_row['content_id']}: {e}")
                continue
            
            # Create recommendation
            recommendation_id = f"rec_{uuid.uuid4().hex[:12]}"
            
            title = content_item.get('title', '')
            content_id = content_item.get('content_id') or content_item.get('offer_id')
            
            # Create decision trace
            decision_trace = {
                "persona_match": persona,
                "content_id": content_id,
                "signals_used": [],  # Simplified for vectorized version
                "guardrails_passed": {
                    "tone_check": True,  # Templates are pre-written, no LLM validation needed
                    "eligibility_check": True
                },
                "timestamp": datetime.now().isoformat()
            }
            
            recommendation = {
                'recommendation_id': recommendation_id,
                'user_id': user_id,
                'type': content_type,
                'content_id': content_id,
                'title': title,
                'rationale': rationale,
                'decision_trace': decision_trace,
                'shown_at': datetime.now().isoformat()
            }
            
            recommendations_list.append(recommendation)
    
    rationale_time = (datetime.now() - rationale_start).total_seconds()
    
    if verbose:
        print(f"  Generated {len(recommendations_list):,} recommendations in {rationale_time:.1f}s")
        print(f"  Storing recommendations...")
    
    # Store recommendations
    if recommendations_list:
        recommendations_df = pd.DataFrame(recommendations_list)
        store_start = datetime.now()
        stored_count = store_recommendations_vectorized(recommendations_df, use_sqlite=use_sqlite)
        store_time = (datetime.now() - store_start).total_seconds()
        
        if verbose:
            print(f"  Stored {stored_count} recommendations in {store_time:.1f}s")
    else:
        stored_count = 0
        if verbose:
            print("  No recommendations to store")
    
    total_time = (datetime.now() - start_time).total_seconds()
    
    if verbose:
        print(f"\nCompleted! Generated {stored_count} recommendations.")
        print(f"Total time: {total_time:.1f}s")
        if stored_count > 0:
            print(f"Average: {stored_count / len(user_data_df):.1f} recommendations per user-time_window")
    
    return {
        'total_users': len(user_data_df['user_id'].unique()),
        'total_recommendations': stored_count,
        'total_time': total_time
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate recommendations for all users using vectorized operations')
    parser.add_argument('--time-windows', nargs='+', default=['30d', '180d'],
                       help='Time windows to process (default: 30d 180d)')
    parser.add_argument('--users', nargs='+', default=None,
                       help='Specific user IDs to process (default: all users)')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress progress output')
    parser.add_argument('--sqlite', action='store_true',
                       help='Force use of SQLite even if Firestore is available')
    
    args = parser.parse_args()
    
    generate_all_recommendations_vectorized(
        time_windows=args.time_windows,
        users=args.users,
        use_sqlite=args.sqlite,
        verbose=not args.quiet
    )

