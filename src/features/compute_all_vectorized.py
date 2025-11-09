"""Vectorized feature computation using pandas.

This module provides a faster alternative to compute_all.py by loading
all data into pandas DataFrames and using vectorized operations.
"""

import sys
import argparse
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import numpy as np
from collections import defaultdict
import statistics
import json
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import db
from src.features.signal_detection import category_contains

# Check if using Firestore
USE_FIRESTORE = (
    os.getenv('FIRESTORE_EMULATOR_HOST') is not None or 
    os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true' or
    os.getenv('FIREBASE_SERVICE_ACCOUNT') is not None or 
    os.path.exists('firebase-service-account.json')
)


def load_all_transactions(window_days: int = 180, use_sqlite: bool = False) -> pd.DataFrame:
    """Load all transactions into a pandas DataFrame.
    
    Args:
        window_days: Number of days to look back
        use_sqlite: If True, force use of SQLite even if Firestore is available
        
    Returns:
        DataFrame with columns: user_id, account_id, date, amount, merchant_name, 
        category, payment_channel, authorized_date, location_city, location_region
    """
    cutoff_date = (datetime.now() - timedelta(days=window_days)).strftime("%Y-%m-%d")
    
    # Check if we should use Firestore (unless explicitly told to use SQLite)
    use_firestore = USE_FIRESTORE and not use_sqlite
    if use_firestore:
        # For Firestore, we'd need to load differently
        # For now, fall back to SQLite for vectorized operations
        print("Warning: Firestore detected. Vectorized operations work best with SQLite.")
        print("Consider using --sqlite flag or loading data to SQLite first.")
        return None
    
    # SQLite path - load all transactions at once
    query = """
        SELECT user_id, account_id, date, amount, merchant_name, category,
               payment_channel, authorized_date, location_city, location_region,
               iso_currency_code
        FROM transactions
        WHERE date >= ?
        ORDER BY user_id, date
    """
    
    rows = db.fetch_all(query, (cutoff_date,))
    
    if not rows:
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame([dict(row) for row in rows])
    
    # Parse dates
    df['date'] = pd.to_datetime(df['date'])
    df['authorized_date'] = pd.to_datetime(df['authorized_date'], errors='coerce')
    
    # Use authorized_date if available, otherwise date
    df['effective_date'] = df['authorized_date'].fillna(df['date'])
    
    # Parse category (handle JSON arrays)
    def parse_category(cat):
        if pd.isna(cat):
            return []
        if isinstance(cat, str) and cat.startswith('['):
            try:
                return json.loads(cat)
            except:
                return [cat] if cat else []
        return [cat] if cat else []
    
    df['category_list'] = df['category'].apply(parse_category)
    
    return df


def load_all_accounts(use_sqlite: bool = False) -> pd.DataFrame:
    """Load all accounts into a pandas DataFrame.
    
    Args:
        use_sqlite: If True, force use of SQLite even if Firestore is available
        
    Returns:
        DataFrame with columns: user_id, account_id, type, subtype, balance, limit
    """
    # Check if we should use Firestore (unless explicitly told to use SQLite)
    use_firestore = USE_FIRESTORE and not use_sqlite
    if use_firestore:
        return None
    
    query = """
        SELECT user_id, account_id, type, subtype, balance, "limit"
        FROM accounts
    """
    
    rows = db.fetch_all(query)
    
    if not rows:
        return pd.DataFrame()
    
    return pd.DataFrame([dict(row) for row in rows])


def compute_subscriptions_vectorized(transactions_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Compute subscription signals for all users using vectorized operations.
    
    Args:
        transactions_df: DataFrame with all transactions
        
    Returns:
        Dict mapping user_id to subscription signals dict
    """
    results = {}
    
    # Filter to negative amounts (spending)
    spending = transactions_df[transactions_df['amount'] < 0].copy()
    
    if len(spending) == 0:
        return results
    
    # Group by user and merchant
    spending['abs_amount'] = spending['amount'].abs()
    
    # For each user, group by merchant and compute recurring patterns
    for user_id, user_txns in spending.groupby('user_id'):
        if len(user_txns) == 0:
            results[user_id] = {
                "recurring_merchants": [],
                "monthly_recurring": 0.0,
                "subscription_share": 0.0,
                "merchant_details": []
            }
            continue
        
        total_spend = user_txns['abs_amount'].sum()
        
        # Group by merchant
        merchant_groups = user_txns.groupby('merchant_name')
        
        recurring_merchants = []
        merchant_details = []
        monthly_recurring = 0.0
        
        for merchant, merchant_txns in merchant_groups:
            if len(merchant_txns) < 3:
                continue
            
            # Sort by date
            merchant_txns = merchant_txns.sort_values('effective_date')
            
            # Count online transactions
            online_count = (merchant_txns['payment_channel'] == 'online').sum()
            online_ratio = online_count / len(merchant_txns)
            is_likely_subscription = online_ratio >= 0.5
            
            # Calculate intervals
            dates = merchant_txns['effective_date'].values
            intervals = np.diff(dates).astype('timedelta64[D]').astype(float)
            
            if len(intervals) == 0:
                continue
            
            avg_interval = np.mean(intervals)
            avg_amount = merchant_txns['abs_amount'].mean()
            
            # Check for monthly (25-34 days) or weekly (6-8 days) pattern
            is_monthly = 25 <= avg_interval <= 34
            is_weekly = 6 <= avg_interval <= 8
            
            if (is_monthly or is_weekly) and (is_likely_subscription or len(merchant_txns) >= 4):
                recurring_merchants.append(merchant)
                
                if is_monthly:
                    monthly_cost = avg_amount
                elif is_weekly:
                    monthly_cost = avg_amount * 4.33
                else:
                    monthly_cost = avg_amount
                
                monthly_recurring += monthly_cost
                
                # Get primary payment channel
                payment_channels = merchant_txns['payment_channel'].dropna()
                primary_channel = payment_channels.mode()[0] if len(payment_channels) > 0 else None
                
                merchant_details.append({
                    "merchant": merchant,
                    "frequency": "monthly" if is_monthly else "weekly",
                    "amount": round(avg_amount, 2),
                    "monthly_equivalent": round(monthly_cost, 2),
                    "occurrences": len(merchant_txns),
                    "payment_channel": primary_channel,
                    "online_ratio": round(online_ratio, 2)
                })
        
        subscription_share = (monthly_recurring / total_spend * 100) if total_spend > 0 else 0.0
        
        results[user_id] = {
            "recurring_merchants": recurring_merchants,
            "monthly_recurring": round(monthly_recurring, 2),
            "subscription_share": round(subscription_share, 2),
            "merchant_details": merchant_details
        }
    
    return results


def compute_credit_utilization_vectorized(accounts_df: pd.DataFrame, transactions_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Compute credit utilization signals for all users using vectorized operations.
    
    Args:
        accounts_df: DataFrame with all accounts
        transactions_df: DataFrame with all transactions
        
    Returns:
        Dict mapping user_id to credit utilization signals dict
    """
    results = {}
    
    # Filter to credit accounts
    credit_accounts = accounts_df[accounts_df['type'] == 'credit'].copy()
    credit_accounts = credit_accounts[credit_accounts['limit'] > 0]
    
    if len(credit_accounts) == 0:
        return results
    
    # Filter to credit account transactions
    credit_account_ids = credit_accounts['account_id'].unique()
    credit_txns = transactions_df[transactions_df['account_id'].isin(credit_account_ids)].copy()
    
    # For each user, compute credit utilization
    for user_id, user_accounts in credit_accounts.groupby('user_id'):
        user_account_ids = user_accounts['account_id'].unique()
        user_txns = credit_txns[credit_txns['account_id'].isin(user_account_ids)]
        
        total_balance = user_accounts['balance'].sum()
        total_limit = user_accounts['limit'].sum()
        total_utilization = (total_balance / total_limit * 100) if total_limit > 0 else 0.0
        
        # Account-level details using vectorized operations
        user_accounts_copy = user_accounts.copy()
        user_accounts_copy['limit'] = user_accounts_copy['limit'].fillna(1.0)
        user_accounts_copy['balance'] = user_accounts_copy['balance'].fillna(0.0)
        user_accounts_copy['utilization'] = (
            (user_accounts_copy['balance'] / user_accounts_copy['limit'] * 100)
            .where(user_accounts_copy['limit'] > 0, 0.0)
        ).round(2)
        
        accounts_detail = user_accounts_copy[['account_id', 'balance', 'limit', 'utilization']].apply(
            lambda row: {
                "account_id": row['account_id'],
                "balance": round(float(row['balance']), 2),
                "limit": round(float(row['limit']), 2),
                "utilization": round(float(row['utilization']), 2)
            },
            axis=1
        ).tolist()
        
        # Calculate interest charges (simplified - would need category parsing)
        user_spending = user_txns[user_txns['amount'] < 0]
        interest_charged = 0.0  # Would need proper category matching
        
        # Payment channel analysis
        online_spending = user_spending[user_spending['payment_channel'] == 'online']
        online_spending_share = (online_spending['amount'].abs().sum() / user_spending['amount'].abs().sum() * 100) if len(user_spending) > 0 else 0.0
        
        # Determine utilization level
        if total_utilization >= 50:
            utilization_level = "high"
        elif total_utilization >= 30:
            utilization_level = "medium"
        else:
            utilization_level = "low"
        
        results[user_id] = {
            "total_utilization": round(total_utilization, 2),
            "utilization_level": utilization_level,
            "accounts": accounts_detail,
            "interest_charged": round(interest_charged, 2),
            "minimum_payment_only": False,  # Would need payment history analysis
            "is_overdue": False,  # Would need liability data
            "online_spending_share": round(online_spending_share, 2)
        }
    
    return results


def compute_savings_behavior_vectorized(accounts_df: pd.DataFrame, transactions_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Compute savings behavior signals for all users using vectorized operations.
    
    Args:
        accounts_df: DataFrame with all accounts
        transactions_df: DataFrame with all transactions
        
    Returns:
        Dict mapping user_id to savings behavior signals dict
    """
    results = {}
    
    # Filter to savings accounts
    savings_accounts = accounts_df[
        (accounts_df['type'] == 'depository') & 
        (accounts_df['subtype'].isin(['savings', 'money_market', 'hsa']) | 
         accounts_df['subtype'].str.contains('savings', case=False, na=False))
    ].copy()
    
    if len(savings_accounts) == 0:
        return results
    
    # Filter to savings account transactions
    savings_account_ids = savings_accounts['account_id'].unique()
    savings_txns = transactions_df[transactions_df['account_id'].isin(savings_account_ids)].copy()
    
    # For each user, compute savings behavior
    for user_id, user_accounts in savings_accounts.groupby('user_id'):
        user_account_ids = user_accounts['account_id'].unique()
        user_txns = savings_txns[savings_txns['account_id'].isin(user_account_ids)]
        
        total_savings = user_accounts['balance'].sum()
        
        # Calculate net inflow (deposits - withdrawals)
        deposits = user_txns[user_txns['amount'] > 0]['amount'].sum()
        withdrawals = user_txns[user_txns['amount'] < 0]['amount'].abs().sum()
        net_inflow = deposits - withdrawals
        
        # Calculate growth rate (simplified - would need historical balance)
        growth_rate = 0.0  # Would need balance history
        
        # Account-level details using vectorized operations
        user_accounts_copy = user_accounts.copy()
        user_accounts_copy['balance'] = user_accounts_copy['balance'].fillna(0.0)
        
        accounts_detail = user_accounts_copy[['account_id', 'balance', 'subtype']].apply(
            lambda row: {
                "account_id": row['account_id'],
                "balance": round(float(row['balance']), 2),
                "subtype": row['subtype']
            },
            axis=1
        ).tolist()
        
        # Simplified coverage level
        if total_savings > 10000:
            coverage_level = "excellent"
        elif total_savings > 5000:
            coverage_level = "good"
        elif total_savings > 1000:
            coverage_level = "building"
        else:
            coverage_level = "low"
        
        results[user_id] = {
            "total_savings": round(total_savings, 2),
            "net_inflow": round(net_inflow, 2),
            "growth_rate": round(growth_rate, 2),
            "emergency_fund_coverage": 0.0,  # Would need expense calculation
            "coverage_level": coverage_level,
            "accounts": accounts_detail,
            "travel_filtered_transactions": 0
        }
    
    return results


def compute_income_stability_vectorized(transactions_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Compute income stability signals for all users using vectorized operations.
    
    Args:
        transactions_df: DataFrame with all transactions
        
    Returns:
        Dict mapping user_id to income stability signals dict
    """
    results = {}
    
    # Filter to positive amounts (income/payments)
    income_txns = transactions_df[transactions_df['amount'] > 0].copy()
    
    # Look for payroll patterns
    payroll_keywords = ['payroll', 'salary', 'direct deposit', 'paycheck']
    
    for user_id, user_txns in income_txns.groupby('user_id'):
        # Filter for likely payroll transactions
        # Require keywords AND exclude savings/transfer patterns
        payroll_mask = user_txns['merchant_name'].str.contains('|'.join(payroll_keywords), case=False, na=False)
        
        # Exclude known non-payroll patterns
        exclude_patterns = ['savings', 'transfer', 'refund', 'tax']
        exclude_mask = user_txns['merchant_name'].str.contains('|'.join(exclude_patterns), case=False, na=False)
        
        # Also check for income category if available
        if 'category' in user_txns.columns:
            # Check if category contains income/payroll (simplified check)
            category_mask = user_txns['category'].astype(str).str.contains('income|payroll', case=False, na=False)
            payroll_mask = payroll_mask | category_mask
        
        # Final mask: has keywords/category AND not excluded
        payroll_mask = payroll_mask & ~exclude_mask
        
        payroll_txns = user_txns[payroll_mask]
        
        if len(payroll_txns) < 2:
            # Not enough data
            results[user_id] = {
                "median_pay_gap": 0,
                "irregular_frequency": False,
                "cash_flow_buffer": 0.0,
                "avg_monthly_expenses": 0.0
            }
            continue
        
        # Sort by date
        payroll_txns = payroll_txns.sort_values('effective_date')
        dates = payroll_txns['effective_date'].values
        
        # Calculate intervals
        intervals = np.diff(dates).astype('timedelta64[D]').astype(float)
        median_pay_gap = np.median(intervals) if len(intervals) > 0 else 0
        
        # Check for irregular frequency using standardized logic
        # Check if median gap matches known regular patterns
        if 6 <= median_pay_gap <= 8:  # Weekly
            irregular_frequency = False
        elif 13 <= median_pay_gap <= 15:  # Biweekly
            irregular_frequency = False
        elif 28 <= median_pay_gap <= 31:  # Monthly
            irregular_frequency = False
        else:
            # If median doesn't match patterns, check variance
            if len(intervals) > 1:
                std_dev = np.std(intervals)
                # High variance indicates irregularity
                irregular_frequency = std_dev > 7
            else:
                irregular_frequency = True  # Default to irregular if unclear
        
        # Calculate cash flow buffer (would need account balance and expenses)
        cash_flow_buffer = 0.0
        
        # Calculate average monthly expenses (from spending)
        user_spending = transactions_df[
            (transactions_df['user_id'] == user_id) & 
            (transactions_df['amount'] < 0)
        ]
        avg_monthly_expenses = user_spending['amount'].abs().sum() / 6.0 if len(user_spending) > 0 else 0.0
        
        results[user_id] = {
            "median_pay_gap": int(median_pay_gap),
            "irregular_frequency": bool(irregular_frequency),
            "cash_flow_buffer": round(cash_flow_buffer, 2),
            "avg_monthly_expenses": round(avg_monthly_expenses, 2)
        }
    
    return results


def store_features_vectorized(features_list: List[Dict[str, Any]], use_sqlite: bool = False) -> int:
    """Batch write features to SQLite database.
    
    Args:
        features_list: List of feature dictionaries, each must have:
                      {'user_id': str, 'signal_type': str, 'signal_data': dict, 'time_window': str}
        use_sqlite: If True, force use of SQLite even if Firestore is available
        
    Returns:
        Number of features stored
    """
    # Check if we should use Firestore (unless explicitly told to use SQLite)
    use_firestore = USE_FIRESTORE and not use_sqlite
    if use_firestore:
        print("Error: Vectorized operations require SQLite database.")
        return 0
    
    if not features_list:
        return 0
    
    computed_at = datetime.now().isoformat()
    stored_count = 0
    
    with db.get_db_connection() as conn:
        for feature in features_list:
            user_id = feature['user_id']
            signal_type = feature['signal_type']
            signal_data = feature['signal_data']
            time_window = feature['time_window']
            
            # Serialize signal_data to JSON
            signal_json = json.dumps(signal_data)
            
            # Delete existing feature if it exists
            delete_query = """
                DELETE FROM computed_features
                WHERE user_id = ? AND signal_type = ? AND time_window = ?
            """
            conn.execute(delete_query, (user_id, signal_type, time_window))
            
            # Insert new feature
            insert_query = """
                INSERT INTO computed_features (user_id, time_window, signal_type, signal_data, computed_at)
                VALUES (?, ?, ?, ?, ?)
            """
            
            conn.execute(insert_query, (user_id, time_window, signal_type, signal_json, computed_at))
            stored_count += 1
        
        conn.commit()
    
    return stored_count


def compute_all_features_vectorized(window_days: int = 30, time_window: str = "30d", 
                                    users: List[str] = None, verbose: bool = True,
                                    use_sqlite: bool = False):
    """Compute all features for all users using vectorized pandas operations.
    
    Args:
        window_days: Number of days to look back
        time_window: Time window string ("30d" or "180d")
        users: Optional list of user_ids to process (None = all users)
        verbose: If True, show progress
        use_sqlite: If True, force use of SQLite even if Firestore is available
    """
    # Check if we should use Firestore (unless explicitly told to use SQLite)
    use_firestore = USE_FIRESTORE and not use_sqlite
    if use_firestore:
        print("Error: Vectorized operations require SQLite database.")
        print("Use --sqlite flag or pass use_sqlite=True to force SQLite usage.")
        return
    
    if verbose:
        print(f"Loading all data into memory for {window_days} day window...")
    
    start_time = time.time()
    
    # Load all data at once
    transactions_df = load_all_transactions(window_days, use_sqlite=use_sqlite)
    accounts_df = load_all_accounts(use_sqlite=use_sqlite)
    
    if transactions_df is None or len(transactions_df) == 0:
        print("No transactions found.")
        return
    
    if accounts_df is None or len(accounts_df) == 0:
        print("No accounts found.")
        return
    
    load_time = time.time() - start_time
    
    if verbose:
        print(f"  Loaded {len(transactions_df):,} transactions and {len(accounts_df):,} accounts in {load_time:.1f}s")
        print(f"  Computing features for all users...")
    
    compute_start = time.time()
    
    # Filter to specific users if requested
    if users:
        transactions_df = transactions_df[transactions_df['user_id'].isin(users)]
        accounts_df = accounts_df[accounts_df['user_id'].isin(users)]
    
    # Get unique user IDs
    user_ids = transactions_df['user_id'].unique()
    total_users = len(user_ids)
    
    if verbose:
        print(f"  Processing {total_users} users...")
    
    # Compute all features using vectorized operations
    subscription_results = compute_subscriptions_vectorized(transactions_df)
    credit_results = compute_credit_utilization_vectorized(accounts_df, transactions_df)
    savings_results = compute_savings_behavior_vectorized(accounts_df, transactions_df)
    income_results = compute_income_stability_vectorized(transactions_df)
    
    compute_time = time.time() - compute_start
    
    if verbose:
        print(f"  Computed features in {compute_time:.1f}s")
        print(f"  Storing results...")
    
    # Collect all features for batch storage
    store_start = time.time()
    features_list = []
    
    for user_id in user_ids:
        all_features = {
            "subscriptions": subscription_results.get(user_id, {
                "recurring_merchants": [],
                "monthly_recurring": 0.0,
                "subscription_share": 0.0,
                "merchant_details": []
            }),
            "credit_utilization": credit_results.get(user_id, {
                "total_utilization": 0.0,
                "utilization_level": "low",
                "accounts": [],
                "interest_charged": 0.0,
                "minimum_payment_only": False,
                "is_overdue": False,
                "online_spending_share": 0.0
            }),
            "savings_behavior": savings_results.get(user_id, {
                "total_savings": 0.0,
                "net_inflow": 0.0,
                "growth_rate": 0.0,
                "emergency_fund_coverage": 0.0,
                "coverage_level": "low",
                "accounts": [],
                "travel_filtered_transactions": 0
            }),
            "income_stability": income_results.get(user_id, {
                "median_pay_gap": 0,
                "irregular_frequency": False,
                "cash_flow_buffer": 0.0,
                "avg_monthly_expenses": 0.0
            })
        }
        
        # Add each signal type to the features list for batch storage
        for signal_type, signal_data in all_features.items():
            features_list.append({
                'user_id': user_id,
                'signal_type': signal_type,
                'signal_data': signal_data,
                'time_window': time_window
            })
    
    # Batch store all features
    if verbose:
        print(f"  Storing {len(features_list)} features...")
    stored_count = store_features_vectorized(features_list, use_sqlite=use_sqlite)
    
    store_time = time.time() - store_start
    total_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"Completed in {total_time:.1f}s")
    print(f"  - Load time: {load_time:.1f}s")
    print(f"  - Compute time: {compute_time:.1f}s")
    print(f"  - Store time: {store_time:.1f}s")
    print(f"  - Features stored: {stored_count}")
    print(f"  - Users processed: {total_users}")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compute features for all users using vectorized pandas operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compute for 30d window (default)
  python src/features/compute_all_vectorized.py
  
  # Compute for 180d window
  python src/features/compute_all_vectorized.py --window 180d
  
  # Quiet mode
  python src/features/compute_all_vectorized.py --quiet
  
Note: This requires SQLite database. For Firestore, use compute_all.py instead.
        """
    )
    parser.add_argument(
        "--window",
        type=str,
        default="30d",
        choices=["30d", "180d"],
        help="Time window (default: 30d)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce verbosity"
    )
    parser.add_argument(
        "--sqlite",
        action="store_true",
        help="Force use of SQLite (no-op, this script requires SQLite)"
    )
    args = parser.parse_args()
    
    window_days = 30 if args.window == "30d" else 180
    
    compute_all_features_vectorized(
        window_days=window_days,
        time_window=args.window,
        verbose=not args.quiet,
        use_sqlite=args.sqlite
    )

