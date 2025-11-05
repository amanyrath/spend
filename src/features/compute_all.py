"""Script to compute all features for all users.

This script loops through all users in the database and computes
features for both 30d and 180d time windows. It skips users that
already have features computed to allow resuming after failures.

Supports parallel processing for faster computation.
"""

import sys
import argparse
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from functools import partial
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import db
from src.features.signal_detection import compute_all_features, get_user_features

# Check if using Firestore (emulator or production)
USE_FIRESTORE = (
    os.getenv('FIRESTORE_EMULATOR_HOST') is not None or 
    os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true' or
    os.getenv('FIREBASE_SERVICE_ACCOUNT') is not None or 
    os.path.exists('firebase-service-account.json')
)

if USE_FIRESTORE:
    from src.database.firestore import get_all_users


def user_has_features(user_id: str) -> bool:
    """Check if user already has all features computed for both time windows.
    
    Args:
        user_id: User identifier
        
    Returns:
        True if user has all features for both 30d and 180d windows
    """
    expected_signal_types = {"subscriptions", "credit_utilization", "savings_behavior", "income_stability"}
    
    # Check 30d window
    features_30d = get_user_features(user_id, "30d")
    if set(features_30d.keys()) != expected_signal_types:
        return False
    
    # Check 180d window
    features_180d = get_user_features(user_id, "180d")
    if set(features_180d.keys()) != expected_signal_types:
        return False
    
    return True


def compute_user_features(user_id: str, force_recompute: bool, use_sqlite: bool) -> tuple:
    """Compute features for a single user (for parallel processing).
    
    Args:
        user_id: User identifier
        force_recompute: If True, recompute features even if they already exist
        use_sqlite: If True, force use of SQLite even if Firestore is available
        
    Returns:
        tuple: (user_id, success: bool, skipped: bool, error_message: str)
    """
    # Re-check if using SQLite (needed for subprocess)
    use_firestore_local = USE_FIRESTORE and not use_sqlite
    
    # Re-import db in subprocess (needed for multiprocessing)
    if not use_firestore_local:
        from src.database import db as local_db
        local_db.init_schema()
    
    try:
        # Check if features already exist
        if not force_recompute:
            expected_signal_types = {"subscriptions", "credit_utilization", "savings_behavior", "income_stability"}
            features_30d = get_user_features(user_id, "30d")
            features_180d = get_user_features(user_id, "180d")
            
            if (set(features_30d.keys()) == expected_signal_types and 
                set(features_180d.keys()) == expected_signal_types):
                return (user_id, False, True, None)
        
        # Compute for 30d window
        compute_all_features(user_id, "30d")
        
        # Compute for 180d window
        compute_all_features(user_id, "180d")
        
        return (user_id, True, False, None)
    except Exception as e:
        return (user_id, False, False, str(e))


def compute_all_users(force_recompute: bool = False, use_sqlite: bool = False, 
                      workers: int = None, verbose: bool = True):
    """Compute features for all users.
    
    Args:
        force_recompute: If True, recompute features even if they already exist
        use_sqlite: If True, force use of SQLite even if Firestore is available
        workers: Number of parallel workers (None = auto-detect CPU count)
        verbose: If True, show detailed progress for each user
    """
    # Determine which database to use
    use_firestore = USE_FIRESTORE and not use_sqlite
    
    # Ensure database schema is initialized (only for SQLite)
    if not use_firestore:
        print("Ensuring database schema is initialized...")
        db.init_schema()
        print("Schema check complete.\n")
    
    # Get all users
    if use_firestore:
        print("Using Firestore database...")
        users = get_all_users()
        # Convert to list of dicts with user_id key
        users = [{"user_id": user["user_id"]} for user in users]
    else:
        print("Using SQLite database...")
        users_query = "SELECT user_id FROM users"
        users = db.fetch_all(users_query)
    
    if not users:
        print("No users found in database.")
        return
    
    total_users = len(users)
    print(f"Found {total_users} users.")
    
    # Determine number of workers
    if workers is None:
        import multiprocessing
        workers = max(1, multiprocessing.cpu_count() - 1)  # Leave one CPU core free
    
    # Check if we should use parallel processing
    use_parallel = workers > 1 and total_users > 10  # Only parallelize if worthwhile
    
    if not force_recompute:
        print(f"Checking for existing features (use --force to recompute all)...")
    else:
        print(f"Force recompute mode: will recompute all features.")
    
    if use_parallel:
        print(f"Using {workers} parallel workers for faster processing...\n")
    else:
        print(f"Processing sequentially...\n")
    
    skipped_count = 0
    computed_count = 0
    error_count = 0
    start_time = time.time()
    
    # Extract user IDs
    user_ids = [user_row["user_id"] for user_row in users]
    
    if use_parallel:
        # Parallel processing
        compute_func = partial(compute_user_features, force_recompute=force_recompute, use_sqlite=use_sqlite)
        
        with ProcessPoolExecutor(max_workers=workers) as executor:
            # Submit all tasks
            future_to_user = {executor.submit(compute_func, user_id): user_id for user_id in user_ids}
            
            # Process completed tasks
            completed = 0
            for future in as_completed(future_to_user):
                completed += 1
                user_id, success, skipped, error_msg = future.result()
                
                if skipped:
                    skipped_count += 1
                    if verbose:
                        print(f"[{completed}/{total_users}] User {user_id} already has features computed. Skipping...")
                elif success:
                    computed_count += 1
                    if verbose:
                        print(f"[{completed}/{total_users}] ✓ User {user_id} features computed successfully")
                else:
                    error_count += 1
                    if verbose:
                        print(f"[{completed}/{total_users}] ✗ User {user_id} error: {error_msg}")
                    else:
                        print(f"[{completed}/{total_users}] ✗ User {user_id} error: {error_msg}")
                
                # Show progress every 10 users
                if not verbose and completed % 10 == 0:
                    print(f"Progress: {completed}/{total_users} ({completed/total_users*100:.1f}%)")
    else:
        # Sequential processing (original logic)
        for idx, user_row in enumerate(users, 1):
            user_id = user_row["user_id"]
            
            # Check if features already exist
            if not force_recompute and user_has_features(user_id):
                if verbose:
                    print(f"[{idx}/{total_users}] User {user_id} already has features computed. Skipping...")
                skipped_count += 1
                continue
            
            if verbose:
                print(f"[{idx}/{total_users}] Computing features for user {user_id}...")
            
            try:
                # Compute for 30d window
                compute_all_features(user_id, "30d")
                
                # Compute for 180d window
                compute_all_features(user_id, "180d")
                
                if verbose:
                    print(f"  ✓ Features computed successfully")
                computed_count += 1
            except Exception as e:
                if verbose:
                    print(f"  ✗ Error computing features: {e}")
                error_count += 1
                continue
            
            # Show progress every 10 users if not verbose
            if not verbose and idx % 10 == 0:
                print(f"Progress: {idx}/{total_users} ({idx/total_users*100:.1f}%)")
    
    elapsed_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"Completed in {elapsed_time:.1f} seconds ({elapsed_time/total_users:.2f}s per user)")
    print(f"{'='*60}")
    print(f"  - Computed: {computed_count} users")
    print(f"  - Skipped (already computed): {skipped_count} users")
    print(f"  - Errors: {error_count} users")
    if use_parallel:
        print(f"  - Workers used: {workers}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compute features for all users",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compute with default settings (auto-detects CPU count)
  python src/features/compute_all.py
  
  # Force recompute all features
  python src/features/compute_all.py --force
  
  # Use 4 parallel workers
  python src/features/compute_all.py --workers 4
  
  # Sequential processing (disable parallel)
  python src/features/compute_all.py --workers 1
  
  # Quiet mode (less verbose output)
  python src/features/compute_all.py --quiet
  
  # Use SQLite instead of Firestore
  python src/features/compute_all.py --sqlite
        """
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recomputation of features even if they already exist"
    )
    parser.add_argument(
        "--sqlite",
        action="store_true",
        help="Force use of SQLite database even if Firestore is available"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of parallel workers (default: auto-detect CPU count - 1)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce verbosity (only show progress every 10 users)"
    )
    args = parser.parse_args()
    
    compute_all_users(
        force_recompute=args.force, 
        use_sqlite=args.sqlite,
        workers=args.workers,
        verbose=not args.quiet
    )

