"""Push data from SQLite to Firebase Firestore.

This script implements the SQLite-first workflow by pushing all data
(raw + processed) from SQLite to Firebase after processing is complete.

Usage:
    python -m src.ingest.push_from_sqlite [--collections users,accounts,transactions,features,personas,recommendations] [--dry-run] [--batch-size 500] [--delay 0.5] [--max-retries 3]
"""

import argparse
import sys
import os
import json
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database import db
from src.database.firestore import get_db, store_user, store_feature, store_persona, store_recommendation

try:
    from google.api_core import exceptions as gcp_exceptions
except ImportError:
    # Fallback if google.api_core is not available
    class gcp_exceptions:
        class ResourceExhausted(Exception):
            pass
        class RetryError(Exception):
            pass


def get_row_value(row, key, default=None):
    """Get value from SQLite Row object with default fallback.
    
    SQLite Row objects don't have .get() method, so we use try/except.
    
    Args:
        row: SQLite Row object or dict
        key: Key to look up
        default: Default value if key doesn't exist
        
    Returns:
        Value from row or default
    """
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return default


def retry_with_backoff(func, max_retries: int = 3, initial_delay: float = 1.0, *args, **kwargs):
    """Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        *args, **kwargs: Arguments to pass to func
        
    Returns:
        Result of func
    """
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except (gcp_exceptions.ResourceExhausted, gcp_exceptions.RetryError) as e:
            if attempt < max_retries:
                delay = initial_delay * (2 ** attempt)
                print(f"  ⚠️  Quota error (attempt {attempt + 1}/{max_retries + 1}): {str(e)[:100]}")
                print(f"  ⏳ Waiting {delay:.1f}s before retry...")
                time.sleep(delay)
            else:
                print(f"  ❌ Failed after {max_retries + 1} attempts: {str(e)[:200]}")
                raise
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:200]}")
            raise


def push_users_from_sqlite(dry_run: bool = False, delay: float = 0.0) -> int:
    """Push users from SQLite to Firestore.
    
    Args:
        dry_run: If True, only preview what would be pushed without actually writing.
        delay: Delay in seconds between operations (default: 0.0).
        
    Returns:
        Number of users pushed.
    """
    use_emulator = os.getenv('FIRESTORE_EMULATOR_HOST') is not None or os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true'
    target = "EMULATOR" if use_emulator else "PRODUCTION"
    
    print(f"  🔌 Connecting to Firebase {target}...")
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    print(f"  ✅ Connected to Firebase {target}")
    
    start_time = time.time()
    print("  📥 Reading users from SQLite...")
    users = db.fetch_all("SELECT * FROM users")
    
    print(f"  📊 Found {len(users)} users in SQLite")
    print(f"  🎯 Target: Firebase {target}")
    
    if dry_run:
        print(f"  [DRY RUN] Would push {len(users)} users to {target}")
        return len(users)
    
    print(f"  🚀 Starting push to {target}...")
    pushed = 0
    failed = 0
    
    for i, user_row in enumerate(users, 1):
        try:
            user_data = {
                'user_id': user_row['user_id'],
                'name': user_row['name'],
                'created_at': user_row['created_at']
            }
            store_user(user_data)
            pushed += 1
            
            if i % 25 == 0 or i == 1:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                remaining = len(users) - i
                eta = remaining / rate if rate > 0 else 0
                percent = (i / len(users)) * 100
                print(f"  ✅ Progress: {i}/{len(users)} users ({percent:.1f}%) | {pushed} success, {failed} failed | Rate: {rate:.1f}/s | ETA: {eta:.0f}s")
            
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            failed += 1
            print(f"  ⚠️  Failed to push user {get_row_value(user_row, 'user_id', 'unknown')}: {str(e)[:100]}")
    
    elapsed = time.time() - start_time
    print(f"  ✅ Completed: Pushed {pushed}/{len(users)} users to {target} in {elapsed:.1f}s ({pushed} success, {failed} failed)")
    return pushed


def push_accounts_from_sqlite(dry_run: bool = False, batch_size: int = 500, delay: float = 0.0, max_retries: int = 3) -> int:
    """Push accounts from SQLite to Firestore with batching.
    
    Args:
        dry_run: If True, only preview what would be pushed without actually writing.
        batch_size: Number of accounts per batch (default: 500, max: 500).
        delay: Delay in seconds between batches (default: 0.0).
        max_retries: Maximum retries for quota errors (default: 3).
        
    Returns:
        Number of accounts pushed.
    """
    use_emulator = os.getenv('FIRESTORE_EMULATOR_HOST') is not None or os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true'
    target = "EMULATOR" if use_emulator else "PRODUCTION"
    
    print(f"  🔌 Connecting to Firebase {target}...")
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    print(f"  ✅ Connected to Firebase {target}")
    
    start_time = time.time()
    print("  📥 Reading accounts from SQLite...")
    accounts = db.fetch_all("SELECT * FROM accounts")
    
    print(f"  📊 Found {len(accounts)} accounts in SQLite")
    print(f"  🎯 Target: Firebase {target}")
    
    if dry_run:
        print(f"  [DRY RUN] Would push {len(accounts)} accounts in ~{(len(accounts) + batch_size - 1) // batch_size} batches to {target}")
        return len(accounts)
    
    print(f"  🚀 Starting push to {target}...")
    batch = client.batch()
    pushed = 0
    total_batches = 0
    failed = 0
    
    for i, account_row in enumerate(accounts, 1):
        try:
            account_data = dict(account_row)
            user_id = account_row['user_id']
            account_id = account_row['account_id']
            
            txn_ref = client.collection('users').document(user_id)\
                          .collection('accounts').document(account_id)
            batch.set(txn_ref, account_data)
            pushed += 1
            
            # Commit batch every batch_size operations
            if pushed % batch_size == 0:
                def commit_batch():
                    batch.commit()
                
                retry_with_backoff(commit_batch, max_retries=max_retries, initial_delay=1.0)
                batch = client.batch()
                total_batches += 1
                
                elapsed = time.time() - start_time
                rate = pushed / elapsed if elapsed > 0 else 0
                remaining = len(accounts) - pushed
                eta = remaining / rate if rate > 0 else 0
                percent = (pushed / len(accounts)) * 100
                print(f"  ✅ Batch {total_batches}: {pushed:,}/{len(accounts):,} accounts ({percent:.1f}%) | Rate: {rate:.1f}/s | ETA: {eta:.0f}s")
                
                if delay > 0:
                    time.sleep(delay)
        except Exception as e:
            failed += 1
            print(f"  ⚠️  Failed to push account {get_row_value(account_row, 'account_id', 'unknown')}: {str(e)[:100]}")
    
    # Commit remaining
    if pushed % batch_size != 0:
        try:
            def commit_batch():
                batch.commit()
            retry_with_backoff(commit_batch, max_retries=max_retries, initial_delay=1.0)
            total_batches += 1
            print(f"  ✅ Final batch {total_batches}: Committed remaining accounts")
        except Exception as e:
            print(f"  ⚠️  Failed to commit final batch: {str(e)[:100]}")
    
    elapsed = time.time() - start_time
    print(f"  ✅ Completed: Pushed {pushed:,}/{len(accounts):,} accounts to {target} ({total_batches} batches) in {elapsed:.1f}s ({pushed} success, {failed} failed)")
    return pushed


def push_transactions_from_sqlite(dry_run: bool = False, batch_size: int = 500, delay: float = 0.0, max_retries: int = 3) -> int:
    """Push transactions from SQLite to Firestore with batching.
    
    Args:
        dry_run: If True, only preview what would be pushed without actually writing.
        batch_size: Number of transactions per batch (default: 500, max: 500).
        delay: Delay in seconds between batches (default: 0.0).
        max_retries: Maximum retries for quota errors (default: 3).
        
    Returns:
        Number of transactions pushed.
    """
    use_emulator = os.getenv('FIRESTORE_EMULATOR_HOST') is not None or os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true'
    target = "EMULATOR" if use_emulator else "PRODUCTION"
    
    print(f"  🔌 Connecting to Firebase {target}...")
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    print(f"  ✅ Connected to Firebase {target}")
    
    start_time = time.time()
    print("  📥 Reading transactions from SQLite...")
    transactions = db.fetch_all("SELECT * FROM transactions")
    
    print(f"  📊 Found {len(transactions)} transactions in SQLite")
    print(f"  🎯 Target: Firebase {target}")
    
    if dry_run:
        print(f"  [DRY RUN] Would push {len(transactions)} transactions in ~{(len(transactions) + batch_size - 1) // batch_size} batches to {target}")
        return len(transactions)
    
    print(f"  🚀 Starting push to {target}...")
    batch = client.batch()
    pushed = 0
    total_batches = 0
    failed = 0
    
    for i, txn_row in enumerate(transactions, 1):
        try:
            txn_data = dict(txn_row)
            user_id = txn_row['user_id']
            transaction_id = txn_row['transaction_id']
            
            # Parse category field (handle JSON array strings)
            category = txn_data.get('category', '')
            if isinstance(category, str):
                if category.startswith('['):
                    try:
                        txn_data['category'] = json.loads(category)
                    except:
                        txn_data['category'] = [category] if category else []
                else:
                    txn_data['category'] = [category] if category else []
            
            # Handle None values for optional fields
            for field in ['location_address', 'location_city', 'location_region', 
                         'location_postal_code', 'location_country', 'location_lat', 
                         'location_lon', 'payment_channel', 'authorized_date']:
                if field in txn_data and txn_data[field] is None:
                    # Keep None - Firestore handles None values
                    pass
            
            txn_ref = client.collection('users').document(user_id)\
                        .collection('transactions').document(transaction_id)
            batch.set(txn_ref, txn_data)
            pushed += 1
            
            # Commit batch every batch_size operations (Firestore limit is 500)
            if pushed % batch_size == 0:
                def commit_batch():
                    batch.commit()
                
                retry_with_backoff(commit_batch, max_retries=max_retries, initial_delay=1.0)
                batch = client.batch()
                total_batches += 1
                
                elapsed = time.time() - start_time
                rate = pushed / elapsed if elapsed > 0 else 0
                remaining = len(transactions) - pushed
                eta = remaining / rate if rate > 0 else 0
                percent = (pushed / len(transactions)) * 100
                print(f"  ✅ Batch {total_batches}: {pushed:,}/{len(transactions):,} transactions ({percent:.1f}%) | Rate: {rate:.1f}/s | ETA: {eta:.0f}s")
                
                if delay > 0:
                    time.sleep(delay)
        except Exception as e:
            failed += 1
            if failed <= 5:  # Only print first 5 errors to avoid spam
                print(f"  ⚠️  Failed to push transaction {get_row_value(txn_row, 'transaction_id', 'unknown')}: {str(e)[:100]}")
            elif failed == 6:
                print(f"  ⚠️  ... (suppressing further transaction errors)")
    
    # Commit remaining
    if pushed % batch_size != 0:
        try:
            def commit_batch():
                batch.commit()
            retry_with_backoff(commit_batch, max_retries=max_retries, initial_delay=1.0)
            total_batches += 1
            print(f"  ✅ Final batch {total_batches}: Committed remaining transactions")
        except Exception as e:
            print(f"  ⚠️  Failed to commit final batch: {str(e)[:100]}")
    
    elapsed = time.time() - start_time
    print(f"  ✅ Completed: Pushed {pushed:,}/{len(transactions):,} transactions to {target} ({total_batches} batches) in {elapsed:.1f}s ({pushed} success, {failed} failed)")
    return pushed


def push_features_from_sqlite(dry_run: bool = False, delay: float = 0.0) -> int:
    """Push computed features from SQLite to Firestore.
    
    Args:
        dry_run: If True, only preview what would be pushed without actually writing.
        delay: Delay in seconds between operations (default: 0.0).
        
    Returns:
        Number of features pushed.
    """
    use_emulator = os.getenv('FIRESTORE_EMULATOR_HOST') is not None or os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true'
    target = "EMULATOR" if use_emulator else "PRODUCTION"
    
    print(f"  🔌 Connecting to Firebase {target}...")
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    print(f"  ✅ Connected to Firebase {target}")
    
    start_time = time.time()
    print("  📥 Reading features from SQLite...")
    features = db.fetch_all("SELECT * FROM computed_features")
    
    print(f"  📊 Found {len(features)} features in SQLite")
    print(f"  🎯 Target: Firebase {target}")
    
    if dry_run:
        print(f"  [DRY RUN] Would push {len(features)} features to {target}")
        return len(features)
    
    print(f"  🚀 Starting push to {target}...")
    pushed = 0
    failed = 0
    
    for i, feature_row in enumerate(features, 1):
        try:
            user_id = feature_row['user_id']
            signal_type = feature_row['signal_type']
            signal_data = json.loads(feature_row['signal_data']) if isinstance(feature_row['signal_data'], str) else feature_row['signal_data']
            time_window = feature_row['time_window']
            
            store_feature(user_id, signal_type, signal_data, time_window)
            pushed += 1
            
            if i % 100 == 0 or i == 1:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                remaining = len(features) - i
                eta = remaining / rate if rate > 0 else 0
                percent = (i / len(features)) * 100
                print(f"  ✅ Progress: {i}/{len(features)} features ({percent:.1f}%) | {pushed} success, {failed} failed | Rate: {rate:.1f}/s | ETA: {eta:.0f}s")
            
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            failed += 1
            print(f"  ⚠️  Failed to push feature {get_row_value(feature_row, 'signal_type', 'unknown')}: {str(e)[:100]}")
    
    elapsed = time.time() - start_time
    print(f"  ✅ Completed: Pushed {pushed}/{len(features)} features to {target} in {elapsed:.1f}s ({pushed} success, {failed} failed)")
    return pushed


def push_personas_from_sqlite(dry_run: bool = False, delay: float = 0.0) -> int:
    """Push persona assignments from SQLite to Firestore.
    
    Args:
        dry_run: If True, only preview what would be pushed without actually writing.
        delay: Delay in seconds between operations (default: 0.0).
        
    Returns:
        Number of persona assignments pushed.
    """
    use_emulator = os.getenv('FIRESTORE_EMULATOR_HOST') is not None or os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true'
    target = "EMULATOR" if use_emulator else "PRODUCTION"
    
    print(f"  🔌 Connecting to Firebase {target}...")
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    print(f"  ✅ Connected to Firebase {target}")
    
    start_time = time.time()
    print("  📥 Reading persona assignments from SQLite...")
    personas = db.fetch_all("SELECT * FROM persona_assignments")
    
    print(f"  📊 Found {len(personas)} persona assignments in SQLite")
    print(f"  🎯 Target: Firebase {target}")
    
    if dry_run:
        print(f"  [DRY RUN] Would push {len(personas)} persona assignments to {target}")
        return len(personas)
    
    print(f"  🚀 Starting push to {target}...")
    pushed = 0
    failed = 0
    
    for i, persona_row in enumerate(personas, 1):
        try:
            persona_data = {
                'user_id': persona_row['user_id'],
                'time_window': persona_row['time_window'],
                'persona': persona_row['persona'],
                'primary_persona': get_row_value(persona_row, 'primary_persona'),
                'criteria_met': json.loads(persona_row['criteria_met']) if isinstance(persona_row['criteria_met'], str) else persona_row['criteria_met'],
                'match_high_utilization': get_row_value(persona_row, 'match_high_utilization', 0.0),
                'match_variable_income': get_row_value(persona_row, 'match_variable_income', 0.0),
                'match_subscription_heavy': get_row_value(persona_row, 'match_subscription_heavy', 0.0),
                'match_savings_builder': get_row_value(persona_row, 'match_savings_builder', 0.0),
                'match_general_wellness': get_row_value(persona_row, 'match_general_wellness', 0.0),
                'assigned_at': persona_row['assigned_at']
            }
            store_persona(persona_row['user_id'], persona_data)
            pushed += 1
            
            if i % 50 == 0 or i == 1:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                remaining = len(personas) - i
                eta = remaining / rate if rate > 0 else 0
                percent = (i / len(personas)) * 100
                print(f"  ✅ Progress: {i}/{len(personas)} persona assignments ({percent:.1f}%) | {pushed} success, {failed} failed | Rate: {rate:.1f}/s | ETA: {eta:.0f}s")
            
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            failed += 1
            print(f"  ⚠️  Failed to push persona {get_row_value(persona_row, 'user_id', 'unknown')}: {str(e)[:100]}")
    
    elapsed = time.time() - start_time
    print(f"  ✅ Completed: Pushed {pushed}/{len(personas)} persona assignments to {target} in {elapsed:.1f}s ({pushed} success, {failed} failed)")
    return pushed


def push_recommendations_from_sqlite(dry_run: bool = False, delay: float = 0.0) -> int:
    """Push recommendations from SQLite to Firestore.
    
    Args:
        dry_run: If True, only preview what would be pushed without actually writing.
        delay: Delay in seconds between operations (default: 0.0).
        
    Returns:
        Number of recommendations pushed.
    """
    use_emulator = os.getenv('FIRESTORE_EMULATOR_HOST') is not None or os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true'
    target = "EMULATOR" if use_emulator else "PRODUCTION"
    
    print(f"  🔌 Connecting to Firebase {target}...")
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    print(f"  ✅ Connected to Firebase {target}")
    
    start_time = time.time()
    print("  📥 Reading recommendations from SQLite...")
    recommendations = db.fetch_all("SELECT * FROM recommendations")
    
    print(f"  📊 Found {len(recommendations)} recommendations in SQLite")
    print(f"  🎯 Target: Firebase {target}")
    
    if dry_run:
        print(f"  [DRY RUN] Would push {len(recommendations)} recommendations to {target}")
        return len(recommendations)
    
    print(f"  🚀 Starting push to {target}...")
    pushed = 0
    failed = 0
    
    for i, rec_row in enumerate(recommendations, 1):
        try:
            recommendation_data = {
                'user_id': rec_row['user_id'],
                'type': rec_row['type'],
                'content_id': rec_row['content_id'],
                'title': rec_row['title'],
                'rationale': rec_row['rationale'],
                'decision_trace': json.loads(rec_row['decision_trace']) if isinstance(rec_row['decision_trace'], str) else rec_row['decision_trace'],
                'shown_at': rec_row['shown_at']
            }
            store_recommendation(rec_row['user_id'], recommendation_data)
            pushed += 1
            
            if i % 50 == 0 or i == 1:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                remaining = len(recommendations) - i
                eta = remaining / rate if rate > 0 else 0
                percent = (i / len(recommendations)) * 100
                print(f"  ✅ Progress: {i}/{len(recommendations)} recommendations ({percent:.1f}%) | {pushed} success, {failed} failed | Rate: {rate:.1f}/s | ETA: {eta:.0f}s")
            
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            failed += 1
            print(f"  ⚠️  Failed to push recommendation {get_row_value(rec_row, 'recommendation_id', 'unknown')}: {str(e)[:100]}")
    
    elapsed = time.time() - start_time
    print(f"  ✅ Completed: Pushed {pushed}/{len(recommendations)} recommendations to {target} in {elapsed:.1f}s ({pushed} success, {failed} failed)")
    return pushed


def push_all_from_sqlite(collections: Optional[List[str]] = None, dry_run: bool = False, batch_size: int = 500, delay: float = 0.5, max_retries: int = 3) -> Dict[str, int]:
    """Push all or selected collections from SQLite to Firebase.
    
    Args:
        collections: List of collection names to push. If None, pushes all collections.
                    Valid names: 'users', 'accounts', 'transactions', 'features', 'personas', 'recommendations'
        dry_run: If True, only preview what would be pushed without actually writing.
        batch_size: Batch size for transactions and accounts (default: 500).
        delay: Delay in seconds between batches (default: 0.5 to avoid quota).
        max_retries: Maximum retries for quota errors (default: 3).
        
    Returns:
        Dictionary mapping collection names to counts pushed.
    """
    overall_start = time.time()
    
    # Check if Firebase emulator is active (safety check)
    use_emulator = os.getenv('FIRESTORE_EMULATOR_HOST') is not None or os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true'
    
    print("=" * 60)
    print("🔥 FIREBASE CONNECTION CHECK")
    print("=" * 60)
    
    if use_emulator:
        print("📱 Target: Firebase Emulator")
        print("📍 Host: localhost:8080")
        print("=" * 60)
    else:
        print("⚠️  Target: Firebase PRODUCTION")
        print("=" * 60)
        
        # Initialize Firebase (will print warning if production)
        client = get_db()
        if client is None:
            raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
        
        if delay < 0.1:
            print(f"⚠️  Warning: Delay is very low ({delay}s). Consider using --delay 0.5 to avoid quota limits.")
        print("=" * 60)
    
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
    print("🚀 Pushing data from SQLite to Firebase")
    print("=" * 60)
    print(f"📦 Collections: {', '.join(collections)}")
    print(f"⚙️  Batch size: {batch_size}")
    print(f"⏱️  Delay between batches: {delay}s")
    print(f"🔄 Max retries: {max_retries}")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    results = {}
    
    # Push raw data first
    if 'users' in collections:
        print("👥 Pushing users...")
        print("-" * 60)
        results['users'] = push_users_from_sqlite(dry_run=dry_run, delay=delay)
        print()
    
    if 'accounts' in collections:
        print("💳 Pushing accounts...")
        print("-" * 60)
        results['accounts'] = push_accounts_from_sqlite(dry_run=dry_run, batch_size=batch_size, delay=delay, max_retries=max_retries)
        print()
    
    if 'transactions' in collections:
        print("💸 Pushing transactions...")
        print("-" * 60)
        results['transactions'] = push_transactions_from_sqlite(dry_run=dry_run, batch_size=batch_size, delay=delay, max_retries=max_retries)
        print()
    
    # Push processed data
    if 'features' in collections:
        print("📊 Pushing computed features...")
        print("-" * 60)
        results['features'] = push_features_from_sqlite(dry_run=dry_run, delay=delay)
        print()
    
    if 'personas' in collections:
        print("🎭 Pushing persona assignments...")
        print("-" * 60)
        results['personas'] = push_personas_from_sqlite(dry_run=dry_run, delay=delay)
        print()
    
    if 'recommendations' in collections:
        print("💡 Pushing recommendations...")
        print("-" * 60)
        results['recommendations'] = push_recommendations_from_sqlite(dry_run=dry_run, delay=delay)
        print()
    
    overall_elapsed = time.time() - overall_start
    
    print("=" * 60)
    print("✅ Push complete!")
    print("=" * 60)
    if not dry_run:
        total = sum(results.values())
        print(f"📊 Total records pushed: {total:,}")
        for collection, count in results.items():
            print(f"  {collection}: {count:,}")
        print(f"⏱️  Total time: {overall_elapsed:.1f}s ({overall_elapsed/60:.1f} minutes)")
        print(f"📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Push data from SQLite to Firebase")
    parser.add_argument(
        "--collections",
        type=str,
        default=None,
        help="Comma-separated list of collections to push: users,accounts,transactions,features,personas,recommendations (default: all)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be pushed without actually writing"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Batch size for transactions (default: 500, max: 500)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay in seconds between batches (default: 0.5 to avoid quota)"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retries for quota errors (default: 3)"
    )
    
    args = parser.parse_args()
    
    collections = None
    if args.collections:
        collections = [c.strip() for c in args.collections.split(',')]
    
    push_all_from_sqlite(collections=collections, dry_run=args.dry_run, batch_size=args.batch_size, delay=args.delay, max_retries=args.max_retries)


if __name__ == "__main__":
    main()

