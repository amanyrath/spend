"""Load data from Firebase Firestore to SQLite.

This script enables loading data from Firebase back into SQLite for
local processing or to sync data from production to local development.

Usage:
    python -m src.ingest.load_from_firebase [--collections users,accounts,transactions,features,personas,recommendations] [--overwrite] [--dry-run]
"""

import argparse
import sys
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database import db
from src.database.firestore import get_db, get_all_users, get_user_accounts, get_user_transactions, get_user_features, get_persona_assignments, get_recommendations


def load_users_from_firebase(overwrite: bool = False, dry_run: bool = False) -> int:
    """Load users from Firestore to SQLite.
    
    Args:
        overwrite: If True, overwrite existing records. If False, skip existing.
        dry_run: If True, only preview what would be loaded without actually writing.
        
    Returns:
        Number of users loaded.
    """
    users = get_all_users()
    
    if dry_run:
        print(f"  [DRY RUN] Would load {len(users)} users")
        return len(users)
    
    loaded = 0
    skipped = 0
    
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        
        for user in users:
            user_id = user['user_id']
            
            # Check if user already exists
            if not overwrite:
                cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
                if cursor.fetchone():
                    skipped += 1
                    continue
            
            # Insert or replace user
            cursor.execute(
                """
                INSERT OR REPLACE INTO users (user_id, name, created_at)
                VALUES (?, ?, ?)
                """,
                (user_id, user.get('name'), user.get('created_at'))
            )
            loaded += 1
            if loaded % 25 == 0:
                print(f"  Loaded {loaded}/{len(users)} users...")
    
    print(f"  Loaded {loaded} users")
    if skipped > 0:
        print(f"  Skipped {skipped} existing users (use --overwrite to replace)")
    return loaded


def load_accounts_from_firebase(overwrite: bool = False, dry_run: bool = False) -> int:
    """Load accounts from Firestore to SQLite.
    
    Args:
        overwrite: If True, overwrite existing records. If False, skip existing.
        dry_run: If True, only preview what would be loaded without actually writing.
        
    Returns:
        Number of accounts loaded.
    """
    users = get_all_users()
    
    all_accounts = []
    for user in users:
        accounts = get_user_accounts(user['user_id'])
        all_accounts.extend(accounts)
    
    if dry_run:
        print(f"  [DRY RUN] Would load {len(all_accounts)} accounts")
        return len(all_accounts)
    
    loaded = 0
    skipped = 0
    
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        
        for account in all_accounts:
            account_id = account['account_id']
            
            # Check if account already exists
            if not overwrite:
                cursor.execute("SELECT 1 FROM accounts WHERE account_id = ?", (account_id,))
                if cursor.fetchone():
                    skipped += 1
                    continue
            
            # Insert or replace account
            cursor.execute(
                """
                INSERT OR REPLACE INTO accounts 
                (account_id, user_id, type, subtype, balance, "limit", mask)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    account_id,
                    account['user_id'],
                    account.get('type'),
                    account.get('subtype'),
                    account.get('balance', 0.0),
                    account.get('limit'),
                    account.get('mask')
                )
            )
            loaded += 1
            if loaded % 100 == 0:
                print(f"  Loaded {loaded}/{len(all_accounts)} accounts...")
    
    print(f"  Loaded {loaded} accounts")
    if skipped > 0:
        print(f"  Skipped {skipped} existing accounts (use --overwrite to replace)")
    return loaded


def load_transactions_from_firebase(overwrite: bool = False, dry_run: bool = False) -> int:
    """Load transactions from Firestore to SQLite.
    
    Args:
        overwrite: If True, overwrite existing records. If False, skip existing.
        dry_run: If True, only preview what would be loaded without actually writing.
        
    Returns:
        Number of transactions loaded.
    """
    users = get_all_users()
    
    all_transactions = []
    for user in users:
        transactions = get_user_transactions(user['user_id'])
        all_transactions.extend(transactions)
    
    if dry_run:
        print(f"  [DRY RUN] Would load {len(all_transactions)} transactions")
        return len(all_transactions)
    
    loaded = 0
    skipped = 0
    
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        
        for txn in all_transactions:
            transaction_id = txn['transaction_id']
            
            # Check if transaction already exists
            if not overwrite:
                cursor.execute("SELECT 1 FROM transactions WHERE transaction_id = ?", (transaction_id,))
                if cursor.fetchone():
                    skipped += 1
                    continue
            
            # Handle category field (may be list or string)
            category = txn.get('category', [])
            if isinstance(category, list):
                category = json.dumps(category)
            elif not isinstance(category, str):
                category = json.dumps([str(category)])
            
            # Insert or replace transaction
            cursor.execute(
                """
                INSERT OR REPLACE INTO transactions
                (transaction_id, account_id, user_id, date, amount, merchant_name, category, pending,
                 location_address, location_city, location_region, location_postal_code,
                 location_country, location_lat, location_lon,
                 iso_currency_code, payment_channel, authorized_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transaction_id,
                    txn['account_id'],
                    txn['user_id'],
                    txn['date'],
                    txn['amount'],
                    txn.get('merchant_name'),
                    category,
                    txn.get('pending', 0),
                    txn.get('location_address'),
                    txn.get('location_city'),
                    txn.get('location_region'),
                    txn.get('location_postal_code'),
                    txn.get('location_country'),
                    txn.get('location_lat'),
                    txn.get('location_lon'),
                    txn.get('iso_currency_code', 'USD'),
                    txn.get('payment_channel'),
                    txn.get('authorized_date')
                )
            )
            loaded += 1
            if loaded % 500 == 0:
                print(f"  Loaded {loaded}/{len(all_transactions)} transactions...")
    
    print(f"  Loaded {loaded} transactions")
    if skipped > 0:
        print(f"  Skipped {skipped} existing transactions (use --overwrite to replace)")
    return loaded


def load_features_from_firebase(overwrite: bool = False, dry_run: bool = False) -> int:
    """Load computed features from Firestore to SQLite.
    
    Args:
        overwrite: If True, overwrite existing records. If False, skip existing.
        dry_run: If True, only preview what would be loaded without actually writing.
        
    Returns:
        Number of features loaded.
    """
    users = get_all_users()
    
    all_features = []
    for user in users:
        user_id = user['user_id']
        features = get_user_features(user_id)
        # Add user_id to each feature (not included by default)
        for feature in features:
            feature['user_id'] = user_id
        all_features.extend(features)
    
    if dry_run:
        print(f"  [DRY RUN] Would load {len(all_features)} features")
        return len(all_features)
    
    loaded = 0
    skipped = 0
    
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        
        for feature in all_features:
            user_id = feature['user_id']
            signal_type = feature['signal_type']
            time_window = feature['time_window']
            
            # Check if feature already exists
            if not overwrite:
                cursor.execute(
                    """
                    SELECT 1 FROM computed_features 
                    WHERE user_id = ? AND signal_type = ? AND time_window = ?
                    """,
                    (user_id, signal_type, time_window)
                )
                if cursor.fetchone():
                    skipped += 1
                    continue
            
            # Insert or replace feature
            signal_data = json.dumps(feature['signal_data']) if isinstance(feature['signal_data'], dict) else feature['signal_data']
            computed_at = feature.get('computed_at')
            if hasattr(computed_at, 'timestamp'):  # Firestore timestamp
                computed_at = datetime.fromtimestamp(computed_at.timestamp()).isoformat()
            elif isinstance(computed_at, str):
                computed_at = computed_at
            else:
                computed_at = datetime.now().isoformat()
            
            cursor.execute(
                """
                INSERT OR REPLACE INTO computed_features 
                (user_id, time_window, signal_type, signal_data, computed_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, time_window, signal_type, signal_data, computed_at)
            )
            loaded += 1
            if loaded % 100 == 0:
                print(f"  Loaded {loaded}/{len(all_features)} features...")
    
    print(f"  Loaded {loaded} features")
    if skipped > 0:
        print(f"  Skipped {skipped} existing features (use --overwrite to replace)")
    return loaded


def load_personas_from_firebase(overwrite: bool = False, dry_run: bool = False) -> int:
    """Load persona assignments from Firestore to SQLite.
    
    Args:
        overwrite: If True, overwrite existing records. If False, skip existing.
        dry_run: If True, only preview what would be loaded without actually writing.
        
    Returns:
        Number of persona assignments loaded.
    """
    users = get_all_users()
    
    all_personas = []
    for user in users:
        user_id = user['user_id']
        personas = get_persona_assignments(user_id)
        # Add user_id to each persona (not included by default)
        for persona in personas:
            persona['user_id'] = user_id
        all_personas.extend(personas)
    
    if dry_run:
        print(f"  [DRY RUN] Would load {len(all_personas)} persona assignments")
        return len(all_personas)
    
    loaded = 0
    skipped = 0
    
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        
        for persona in all_personas:
            user_id = persona['user_id']
            time_window = persona['time_window']
            
            # Check if persona already exists
            if not overwrite:
                cursor.execute(
                    """
                    SELECT 1 FROM persona_assignments 
                    WHERE user_id = ? AND time_window = ?
                    """,
                    (user_id, time_window)
                )
                if cursor.fetchone():
                    skipped += 1
                    continue
            
            # Insert or replace persona
            criteria_met = persona.get('criteria_met', [])
            if isinstance(criteria_met, list):
                criteria_met = json.dumps(criteria_met)
            elif not isinstance(criteria_met, str):
                criteria_met = json.dumps([str(criteria_met)])
            
            assigned_at = persona.get('assigned_at')
            if hasattr(assigned_at, 'timestamp'):  # Firestore timestamp
                assigned_at = datetime.fromtimestamp(assigned_at.timestamp()).isoformat()
            elif isinstance(assigned_at, str):
                assigned_at = assigned_at
            else:
                assigned_at = datetime.now().isoformat()
            
            cursor.execute(
                """
                INSERT OR REPLACE INTO persona_assignments (
                    user_id, time_window, persona, criteria_met, assigned_at,
                    match_high_utilization, match_variable_income, match_subscription_heavy,
                    match_savings_builder, match_general_wellness, primary_persona
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    time_window,
                    persona.get('persona'),
                    criteria_met,
                    assigned_at,
                    persona.get('match_high_utilization', 0.0),
                    persona.get('match_variable_income', 0.0),
                    persona.get('match_subscription_heavy', 0.0),
                    persona.get('match_savings_builder', 0.0),
                    persona.get('match_general_wellness', 0.0),
                    persona.get('primary_persona')
                )
            )
            loaded += 1
            if loaded % 50 == 0:
                print(f"  Loaded {loaded}/{len(all_personas)} persona assignments...")
    
    print(f"  Loaded {loaded} persona assignments")
    if skipped > 0:
        print(f"  Skipped {skipped} existing persona assignments (use --overwrite to replace)")
    return loaded


def load_recommendations_from_firebase(overwrite: bool = False, dry_run: bool = False) -> int:
    """Load recommendations from Firestore to SQLite.
    
    Args:
        overwrite: If True, overwrite existing records. If False, skip existing.
        dry_run: If True, only preview what would be loaded without actually writing.
        
    Returns:
        Number of recommendations loaded.
    """
    users = get_all_users()
    
    all_recommendations = []
    for user in users:
        user_id = user['user_id']
        recommendations = get_recommendations(user_id)
        # Add user_id to each recommendation (not included by default)
        for rec in recommendations:
            rec['user_id'] = user_id
        all_recommendations.extend(recommendations)
    
    if dry_run:
        print(f"  [DRY RUN] Would load {len(all_recommendations)} recommendations")
        return len(all_recommendations)
    
    loaded = 0
    skipped = 0
    
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        
        for rec in all_recommendations:
            recommendation_id = rec.get('recommendation_id')
            if not recommendation_id:
                # Skip recommendations without ID
                continue
            
            # Check if recommendation already exists
            if not overwrite:
                cursor.execute("SELECT 1 FROM recommendations WHERE recommendation_id = ?", (recommendation_id,))
                if cursor.fetchone():
                    skipped += 1
                    continue
            
            # Insert or replace recommendation
            decision_trace = rec.get('decision_trace', {})
            if isinstance(decision_trace, dict):
                decision_trace = json.dumps(decision_trace)
            elif not isinstance(decision_trace, str):
                decision_trace = json.dumps({})
            
            shown_at = rec.get('shown_at')
            if hasattr(shown_at, 'timestamp'):  # Firestore timestamp
                shown_at = datetime.fromtimestamp(shown_at.timestamp()).isoformat()
            elif isinstance(shown_at, str):
                shown_at = shown_at
            else:
                shown_at = datetime.now().isoformat()
            
            cursor.execute(
                """
                INSERT OR REPLACE INTO recommendations 
                (recommendation_id, user_id, type, content_id, title, rationale, decision_trace, shown_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    recommendation_id,
                    rec['user_id'],
                    rec.get('type'),
                    rec.get('content_id'),
                    rec.get('title'),
                    rec.get('rationale'),
                    decision_trace,
                    shown_at
                )
            )
            loaded += 1
            if loaded % 50 == 0:
                print(f"  Loaded {loaded}/{len(all_recommendations)} recommendations...")
    
    print(f"  Loaded {loaded} recommendations")
    if skipped > 0:
        print(f"  Skipped {skipped} existing recommendations (use --overwrite to replace)")
    return loaded


def load_all_from_firebase(collections: Optional[List[str]] = None, overwrite: bool = False, dry_run: bool = False) -> Dict[str, int]:
    """Load all or selected collections from Firebase to SQLite.
    
    Args:
        collections: List of collection names to load. If None, loads all collections.
                    Valid names: 'users', 'accounts', 'transactions', 'features', 'personas', 'recommendations'
        overwrite: If True, overwrite existing records. If False, skip existing.
        dry_run: If True, only preview what would be loaded without actually writing.
        
    Returns:
        Dictionary mapping collection names to counts loaded.
    """
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    
    if dry_run:
        print("=" * 60)
        print("DRY RUN MODE - No data will be written")
        print("=" * 60)
    
    all_collections = ['users', 'accounts', 'transactions', 'features', 'personas', 'recommendations']
    
    if collections is None:
        collections = all_collections
    else:
        # Validate collection names
        invalid = [c for c in collections if c not in all_collections]
        if invalid:
            raise ValueError(f"Invalid collection names: {invalid}. Valid names: {all_collections}")
    
    print("=" * 60)
    print("Loading data from Firebase to SQLite")
    print("=" * 60)
    print(f"Collections: {', '.join(collections)}")
    print(f"Overwrite: {overwrite}")
    print(f"Dry run: {dry_run}")
    print("=" * 60)
    print()
    
    results = {}
    
    # Load raw data first
    if 'users' in collections:
        print("Loading users...")
        results['users'] = load_users_from_firebase(overwrite=overwrite, dry_run=dry_run)
        print()
    
    if 'accounts' in collections:
        print("Loading accounts...")
        results['accounts'] = load_accounts_from_firebase(overwrite=overwrite, dry_run=dry_run)
        print()
    
    if 'transactions' in collections:
        print("Loading transactions...")
        results['transactions'] = load_transactions_from_firebase(overwrite=overwrite, dry_run=dry_run)
        print()
    
    # Load processed data
    if 'features' in collections:
        print("Loading computed features...")
        results['features'] = load_features_from_firebase(overwrite=overwrite, dry_run=dry_run)
        print()
    
    if 'personas' in collections:
        print("Loading persona assignments...")
        results['personas'] = load_personas_from_firebase(overwrite=overwrite, dry_run=dry_run)
        print()
    
    if 'recommendations' in collections:
        print("Loading recommendations...")
        results['recommendations'] = load_recommendations_from_firebase(overwrite=overwrite, dry_run=dry_run)
        print()
    
    print("=" * 60)
    print("Load complete!")
    print("=" * 60)
    if not dry_run:
        total = sum(results.values())
        print(f"Total records loaded: {total}")
        for collection, count in results.items():
            print(f"  {collection}: {count}")
    print()
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Load data from Firebase to SQLite")
    parser.add_argument(
        "--collections",
        type=str,
        default=None,
        help="Comma-separated list of collections to load: users,accounts,transactions,features,personas,recommendations (default: all)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing records (default: skip existing)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be loaded without actually writing"
    )
    
    args = parser.parse_args()
    
    collections = None
    if args.collections:
        collections = [c.strip() for c in args.collections.split(',')]
    
    load_all_from_firebase(collections=collections, overwrite=args.overwrite, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

