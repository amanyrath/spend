"""End-to-end ETL script for SpendSense data pipeline.

This script orchestrates the full data pipeline:
1. Optionally wipe SQLite/Firebase data (with confirmation)
2. Generate synthetic data
3. Load data into SQLite
4. Process data using vectorized operations (features, personas, recommendations)
5. Optionally push to Firebase (with confirmation)

All processing uses vectorized operations in SQLite for performance.
"""

import argparse
import sys
import os
import time
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import csv

from src.database import db
from src.database.db import DEFAULT_DB_PATH, init_schema, get_db_connection
from src.database.firestore import get_db
from src.ingest.data_generator import generate_all_data
from src.ingest.push_from_sqlite import push_all_from_sqlite


def archive_sqlite_to_parquet(db_path: Optional[str] = None, 
                                archive_dir: str = "data/archives") -> Optional[str]:
    """Archive SQLite database to Parquet files with timestamp.
    
    Exports all tables (users, accounts, transactions, computed_features,
    persona_assignments, recommendations) to Parquet format in a timestamped directory.
    
    Args:
        db_path: Path to SQLite database file
        archive_dir: Base directory for archives (default: data/archives)
        
    Returns:
        Path to archive directory if successful, None if failed or pandas not available
    """
    try:
        import pandas as pd
    except ImportError:
        print("Warning: pandas/pyarrow not installed. Cannot create archive.")
        print("Install with: pip install pandas pyarrow")
        return None
    
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    db_path_obj = Path(db_path)
    
    if not db_path_obj.exists():
        print("SQLite database does not exist. Nothing to archive.")
        return None
    
    # Create timestamped archive directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = Path(archive_dir) / f"archive_{timestamp}"
    archive_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\nArchiving SQLite database to: {archive_path}")
    
    try:
        # Connect to database
        with get_db_connection(db_path) as conn:
            # Get list of tables
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            if not tables:
                print("No tables found in database.")
                archive_path.rmdir()
                return None
            
            archived_count = 0
            total_records = 0
            
            for table in tables:
                # Skip system tables
                if table.startswith('sqlite_'):
                    continue
                
                try:
                    # Read table into DataFrame
                    query = f"SELECT * FROM {table}"
                    df = pd.read_sql_query(query, conn)
                    
                    if len(df) == 0:
                        print(f"  Skipping {table} (empty)")
                        continue
                    
                    # Parse JSON fields if they exist
                    if 'category' in df.columns:
                        df['category'] = df['category'].apply(
                            lambda x: json.loads(x) if isinstance(x, str) and x.startswith('[') else ([x] if x else [])
                        )
                    
                    if 'signal_data' in df.columns:
                        df['signal_data'] = df['signal_data'].apply(
                            lambda x: json.loads(x) if isinstance(x, str) and x.startswith('{') else ({})
                        )
                    
                    if 'criteria_met' in df.columns:
                        df['criteria_met'] = df['criteria_met'].apply(
                            lambda x: json.loads(x) if isinstance(x, str) and x.startswith('[') else ([x] if x else [])
                        )
                    
                    if 'decision_trace' in df.columns:
                        df['decision_trace'] = df['decision_trace'].apply(
                            lambda x: json.loads(x) if isinstance(x, str) and x.startswith('{') else ({})
                        )
                    
                    # Export to Parquet
                    parquet_file = archive_path / f"{table}.parquet"
                    df.to_parquet(parquet_file, index=False, compression='snappy')
                    
                    file_size_mb = parquet_file.stat().st_size / (1024 * 1024)
                    total_records += len(df)
                    archived_count += 1
                    
                    print(f"  Archived {table}: {len(df):,} records ({file_size_mb:.2f} MB)")
                    
                except Exception as e:
                    print(f"  Warning: Failed to archive {table}: {e}")
            
            # Create metadata file
            metadata = {
                "archived_at": datetime.now().isoformat(),
                "source_database": str(db_path),
                "tables_archived": archived_count,
                "total_records": total_records,
                "archive_format": "parquet",
                "compression": "snappy"
            }
            
            metadata_file = archive_path / "metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
            
            print(f"\nArchive complete: {archived_count} tables, {total_records:,} total records")
            print(f"Archive location: {archive_path}")
            
            return str(archive_path)
            
    except Exception as e:
        print(f"Error archiving SQLite database: {e}")
        import traceback
        traceback.print_exc()
        # Clean up partial archive
        if archive_path.exists():
            import shutil
            shutil.rmtree(archive_path, ignore_errors=True)
        return None


def confirm_action(message: str, default: str = 'n') -> bool:
    """Interactive confirmation prompt.
    
    Args:
        message: Message to display to user
        default: Default answer ('y' or 'n')
        
    Returns:
        True if user confirms, False otherwise
    """
    valid_yes = ['y', 'yes']
    valid_no = ['n', 'no']
    
    default_upper = default.upper()
    prompt = f"{message} [{default_upper}]: "
    
    while True:
        try:
            response = input(prompt).strip().lower()
            if not response:
                response = default.lower()
            
            if response in valid_yes:
                return True
            elif response in valid_no:
                return False
            else:
                print("Please enter 'y' or 'n'")
        except KeyboardInterrupt:
            print("\nCancelled.")
            return False
        except EOFError:
            print("\nCancelled.")
            return False


def get_sqlite_stats(db_path: Optional[str] = None) -> Dict[str, int]:
    """Get current SQLite database statistics.
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        Dictionary with counts for each table
    """
    stats = {
        'users': 0,
        'accounts': 0,
        'transactions': 0,
        'features': 0,
        'personas': 0,
        'recommendations': 0
    }
    
    try:
        with db.get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if tables exist before querying
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            if 'users' in tables:
                cursor.execute("SELECT COUNT(*) FROM users")
                stats['users'] = cursor.fetchone()[0]
            
            if 'accounts' in tables:
                cursor.execute("SELECT COUNT(*) FROM accounts")
                stats['accounts'] = cursor.fetchone()[0]
            
            if 'transactions' in tables:
                cursor.execute("SELECT COUNT(*) FROM transactions")
                stats['transactions'] = cursor.fetchone()[0]
            
            if 'computed_features' in tables:
                cursor.execute("SELECT COUNT(*) FROM computed_features")
                stats['features'] = cursor.fetchone()[0]
            
            if 'persona_assignments' in tables:
                cursor.execute("SELECT COUNT(*) FROM persona_assignments")
                stats['personas'] = cursor.fetchone()[0]
            
            if 'recommendations' in tables:
                cursor.execute("SELECT COUNT(*) FROM recommendations")
                stats['recommendations'] = cursor.fetchone()[0]
    except Exception:
        # Database might not exist yet
        pass
    
    return stats


def get_firebase_stats(timeout_seconds: int = 10) -> Dict[str, int]:
    """Get current Firebase/Firestore statistics.
    
    Args:
        timeout_seconds: Maximum time to spend collecting stats (default: 10)
    
    Returns:
        Dictionary with counts for each collection
    """
    stats = {
        'users': 0,
        'accounts': 0,
        'transactions': 0,
        'features': 0,
        'personas': 0,
        'recommendations': 0
    }
    
    # Check if Firebase is available before trying to connect
    use_emulator = os.getenv('FIRESTORE_EMULATOR_HOST') is not None or os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true'
    has_credentials = os.getenv('FIREBASE_SERVICE_ACCOUNT') is not None or os.path.exists('firebase-service-account.json')
    
    if not use_emulator and not has_credentials:
        # No Firebase configured, return empty stats
        return stats
    
    print("  🔌 Connecting to Firebase for stats...")
    if use_emulator:
        print("  📱 Target: Firebase Emulator")
        emulator_host = os.getenv('FIRESTORE_EMULATOR_HOST', 'localhost:8080')
        print(f"  📍 Host: {emulator_host}")
    else:
        print("  ⚠️  Target: Firebase PRODUCTION")
    
    client = get_db()
    if client is None:
        print("  ⚠️  Firebase not available (not initialized)")
        return stats
    print("  ✅ Connected to Firebase")
    
    import signal
    import time
    
    start_time = time.time()
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Stats collection timed out")
    
    try:
        # Set up timeout (Unix only)
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
        
        print("  📊 Counting users...")
        # Count users with aggressive limit to avoid hanging
        users_ref = client.collection('users')
        try:
            # Use a small limit and check time
            users_list = []
            for doc in users_ref.limit(500).stream():
                users_list.append(doc)
                if time.time() - start_time > timeout_seconds:
                    print(f"  ⏱️  Timeout reached, stopping at {len(users_list)} users")
                    break
            stats['users'] = len(users_list)
            print(f"  ✓ Found {stats['users']} users")
        except (TimeoutError, Exception) as e:
            print(f"  ⚠️  Could not count users: {e}")
            stats['users'] = 0
            users_list = []
        finally:
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)  # Cancel alarm
        
        # Count subcollections (accounts, transactions, features, personas, recommendations)
        total_accounts = 0
        total_transactions = 0
        total_features = 0
        total_personas = 0
        total_recommendations = 0
        
        if not users_list:
            print("  ℹ️  No users found, skipping subcollection counts")
        else:
            print("  📊 Counting subcollections (sample only, max 50 users)...")
            # Limit to first 50 users to avoid timeout
            max_users = min(50, len(users_list))
            for i, user_doc in enumerate(users_list[:max_users]):
                # Check timeout
                if time.time() - start_time > timeout_seconds:
                    print(f"  ⏱️  Timeout reached, stopping subcollection counts at user {i}/{max_users}")
                    break
                
                if i % 10 == 0 and i > 0:
                    print(f"    Processed {i}/{max_users} users...")
                
                try:
                    # Accounts (small limit)
                    accounts_ref = user_doc.reference.collection('accounts')
                    total_accounts += len(list(accounts_ref.limit(50).stream()))
                    
                    # Transactions (small limit)
                    transactions_ref = user_doc.reference.collection('transactions')
                    total_transactions += len(list(transactions_ref.limit(200).stream()))
                    
                    # Features (small limit)
                    features_ref = user_doc.reference.collection('computed_features')
                    total_features += len(list(features_ref.limit(50).stream()))
                    
                    # Personas (small limit)
                    personas_ref = user_doc.reference.collection('persona_assignments')
                    total_personas += len(list(personas_ref.limit(10).stream()))
                    
                    # Recommendations (small limit)
                    recommendations_ref = user_doc.reference.collection('recommendations')
                    total_recommendations += len(list(recommendations_ref.limit(50).stream()))
                except Exception as e:
                    print(f"    ⚠️  Error counting subcollections for user {user_doc.id}: {e}")
                    continue
            
            if max_users < len(users_list):
                print(f"  ℹ️  Note: Only counted subcollections for {max_users}/{len(users_list)} users (sample)")
        
        stats['accounts'] = total_accounts
        stats['transactions'] = total_transactions
        stats['features'] = total_features
        stats['personas'] = total_personas
        stats['recommendations'] = total_recommendations
        print("  ✓ Stats collection complete")
    except (TimeoutError, Exception) as e:
        print(f"  ⚠️  Warning: Could not get Firebase stats: {e}")
        if not isinstance(e, TimeoutError):
            import traceback
            traceback.print_exc()
    finally:
        # Ensure alarm is cancelled
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
    
    return stats


def wipe_sqlite_database(db_path: Optional[str] = None) -> bool:
    """Wipe SQLite database by deleting file and recreating schema.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        True if wiped successfully, False otherwise
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    db_path_obj = Path(db_path)
    
    # Get current stats
    stats = get_sqlite_stats(db_path)
    
    if stats['users'] == 0 and stats['accounts'] == 0:
        print("SQLite database is already empty or doesn't exist.")
        return True
    
    # Show summary
    print("\n" + "=" * 60)
    print("SQLite Database Summary")
    print("=" * 60)
    print(f"Users: {stats['users']:,}")
    print(f"Accounts: {stats['accounts']:,}")
    print(f"Transactions: {stats['transactions']:,}")
    print(f"Features: {stats['features']:,}")
    print(f"Personas: {stats['personas']:,}")
    print(f"Recommendations: {stats['recommendations']:,}")
    print("=" * 60)
    
    # Confirm
    if not confirm_action("Delete SQLite database? This will delete all data above", default='n'):
        print("Skipping SQLite wipe.")
        return False
    
    try:
        # Delete database file
        if db_path_obj.exists():
            db_path_obj.unlink()
            print(f"Deleted SQLite database: {db_path}")
        
        # Recreate schema
        init_schema(db_path)
        print("Recreated database schema.")
        
        return True
    except Exception as e:
        print(f"Error wiping SQLite database: {e}")
        return False


def wipe_firebase_data() -> bool:
    """Wipe all data from Firebase/Firestore.
    
    Returns:
        True if wiped successfully, False otherwise
    """
    client = get_db()
    if client is None:
        print("Firebase not initialized. Nothing to wipe.")
        return True
    
    # Get current stats
    stats = get_firebase_stats()
    
    if stats['users'] == 0:
        print("Firebase is already empty.")
        return True
    
    # Check if using emulator
    use_emulator = os.getenv('FIRESTORE_EMULATOR_HOST') is not None
    
    # Show summary
    print("\n" + "=" * 60)
    print("Firebase/Firestore Summary")
    print("=" * 60)
    if use_emulator:
        print("Target: Firebase Emulator (localhost:8080)")
    else:
        print("Target: Firebase Production")
    print(f"Users: {stats['users']:,}")
    print(f"Accounts: {stats['accounts']:,}")
    print(f"Transactions: {stats['transactions']:,}")
    print(f"Features: {stats['features']:,}")
    print(f"Personas: {stats['personas']:,}")
    print(f"Recommendations: {stats['recommendations']:,}")
    print("=" * 60)
    
    # Confirm
    if use_emulator:
        message = "Delete all Firebase emulator data? This will delete all data above"
    else:
        message = "WARNING: Delete all Firebase PRODUCTION data? This will delete all data above"
    
    if not confirm_action(message, default='n'):
        print("Skipping Firebase wipe.")
        return False
    
    try:
        # Delete all users and their subcollections
        users_ref = client.collection('users')
        deleted_users = 0
        
        for user_doc in users_ref.stream():
            user_ref = user_doc.reference
            
            # Delete subcollections
            for collection_name in ['accounts', 'transactions', 'computed_features', 
                                   'persona_assignments', 'recommendations']:
                subcollection_ref = user_ref.collection(collection_name)
                for doc in subcollection_ref.stream():
                    doc.reference.delete()
            
            # Delete user document
            user_ref.delete()
            deleted_users += 1
            
            if deleted_users % 50 == 0:
                print(f"  Deleted {deleted_users} users...")
        
        print(f"Deleted {deleted_users} users and all their subcollections.")
        return True
    except Exception as e:
        print(f"Error wiping Firebase data: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_data_to_sqlite(data_dir: str = "data", db_path: Optional[str] = None, 
                        clear_existing: bool = True) -> None:
    """Load data from files into SQLite database (SQLite-only, no Firebase).
    
    This function loads data directly to SQLite without Firebase dependencies.
    Based on scripts/load_data_sqlite_only.py logic.
    
    Args:
        data_dir: Directory containing data files (default: "data")
        db_path: Path to SQLite database file. If None, uses default path.
        clear_existing: If True, clear existing data before loading
    """
    data_path = Path(data_dir)
    
    # Initialize schema
    print("Initializing database schema...")
    init_schema(db_path)
    print("Schema initialized")
    
    # Get database connection
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Clear existing data if requested
        if clear_existing:
            print("Clearing existing data...")
            cursor.execute("DELETE FROM transactions")
            cursor.execute("DELETE FROM accounts")
            cursor.execute("DELETE FROM users")
            conn.commit()
            print("Existing data cleared")
        
        # Load users from JSON
        users_file = data_path / "users.json"
        if not users_file.exists():
            raise FileNotFoundError(f"Users file not found: {users_file}")
        
        print(f"Loading users from {users_file}...")
        with open(users_file, "r") as f:
            users = json.load(f)
        
        users_inserted = 0
        for user in users:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO users (user_id, name, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (user["user_id"], user["name"], user["created_at"])
                )
                if cursor.rowcount > 0:
                    users_inserted += 1
            except Exception as e:
                print(f"Error inserting user {user['user_id']}: {e}")
        
        print(f"Inserted {users_inserted} users")
        
        # Load accounts from CSV
        accounts_file = data_path / "accounts.csv"
        if not accounts_file.exists():
            raise FileNotFoundError(f"Accounts file not found: {accounts_file}")
        
        print(f"Loading accounts from {accounts_file}...")
        accounts_inserted = 0
        with open(accounts_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Handle empty limit field
                    limit = None if row["limit"] == "" else float(row["limit"])
                    
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO accounts 
                        (account_id, user_id, type, subtype, balance, "limit", mask)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            row["account_id"],
                            row["user_id"],
                            row["type"],
                            row["subtype"],
                            float(row["balance"]),
                            limit,
                            row["mask"]
                        )
                    )
                    if cursor.rowcount > 0:
                        accounts_inserted += 1
                except Exception as e:
                    print(f"Error inserting account {row.get('account_id', 'unknown')}: {e}")
        
        print(f"Inserted {accounts_inserted} accounts")
        
        # Load transactions from CSV
        transactions_file = data_path / "transactions.csv"
        if not transactions_file.exists():
            raise FileNotFoundError(f"Transactions file not found: {transactions_file}")
        
        print(f"Loading transactions from {transactions_file}...")
        transactions_inserted = 0
        batch_size = 1000
        batch = []
        
        with open(transactions_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Parse category (may be JSON array or legacy string)
                    category = row.get("category", "")
                    if category.startswith("["):
                        # It's already JSON, use as-is
                        pass
                    else:
                        # Legacy string format, convert to JSON array
                        if category:
                            category = json.dumps([category])
                        else:
                            category = json.dumps([])
                    
                    # Handle location fields (may be empty)
                    location_address = row.get("location_address", "") or None
                    location_city = row.get("location_city", "") or None
                    location_region = row.get("location_region", "") or None
                    location_postal_code = row.get("location_postal_code", "") or None
                    location_country = row.get("location_country", "") or None
                    location_lat = float(row["location_lat"]) if row.get("location_lat") else None
                    location_lon = float(row["location_lon"]) if row.get("location_lon") else None
                    
                    # Handle new Plaid fields
                    iso_currency_code = row.get("iso_currency_code", "USD") or "USD"
                    payment_channel = row.get("payment_channel", "") or None
                    authorized_date = row.get("authorized_date", "") or None
                    
                    batch.append((
                        row["transaction_id"],
                        row["account_id"],
                        row["user_id"],
                        row["date"],
                        float(row["amount"]),
                        row["merchant_name"],
                        category,
                        int(row["pending"]),
                        location_address,
                        location_city,
                        location_region,
                        location_postal_code,
                        location_country,
                        location_lat,
                        location_lon,
                        iso_currency_code,
                        payment_channel,
                        authorized_date
                    ))
                    
                    # Insert in batches for performance
                    if len(batch) >= batch_size:
                        cursor.executemany(
                            """
                            INSERT OR IGNORE INTO transactions
                            (transaction_id, account_id, user_id, date, amount, merchant_name, category, pending,
                             location_address, location_city, location_region, location_postal_code,
                             location_country, location_lat, location_lon,
                             iso_currency_code, payment_channel, authorized_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            batch
                        )
                        transactions_inserted += len(batch)
                        conn.commit()
                        if transactions_inserted % 10000 == 0:
                            print(f"  Loaded {transactions_inserted} transactions...")
                        batch = []
                except Exception as e:
                    print(f"Error inserting transaction {row.get('transaction_id', 'unknown')}: {e}")
        
        # Insert remaining batch
        if batch:
            cursor.executemany(
                """
                INSERT OR IGNORE INTO transactions
                (transaction_id, account_id, user_id, date, amount, merchant_name, category, pending,
                 location_address, location_city, location_region, location_postal_code,
                 location_country, location_lat, location_lon,
                 iso_currency_code, payment_channel, authorized_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                batch
            )
            transactions_inserted += len(batch)
            conn.commit()
        
        print(f"Inserted {transactions_inserted} transactions")
        
        # Verify data integrity
        print("\nVerifying data integrity...")
        
        # Count users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"Users in database: {user_count}")
        
        # Count accounts
        cursor.execute("SELECT COUNT(*) FROM accounts")
        account_count = cursor.fetchone()[0]
        print(f"Accounts in database: {account_count}")
        
        # Count transactions
        cursor.execute("SELECT COUNT(*) FROM transactions")
        transaction_count = cursor.fetchone()[0]
        print(f"Transactions in database: {transaction_count}")
        
        # Check for orphaned transactions
        cursor.execute("""
            SELECT COUNT(*) FROM transactions t
            LEFT JOIN accounts a ON t.account_id = a.account_id
            WHERE a.account_id IS NULL
        """)
        orphaned_count = cursor.fetchone()[0]
        if orphaned_count > 0:
            print(f"Warning: {orphaned_count} orphaned transactions found")
        else:
            print("No orphaned transactions found")
        
        # Check for accounts without users
        cursor.execute("""
            SELECT COUNT(*) FROM accounts a
            LEFT JOIN users u ON a.user_id = u.user_id
            WHERE u.user_id IS NULL
        """)
        orphaned_accounts = cursor.fetchone()[0]
        if orphaned_accounts > 0:
            print(f"Warning: {orphaned_accounts} orphaned accounts found")
        else:
            print("No orphaned accounts found")
        
        print("\nData loading complete!")


def generate_and_load_data(users: int, days: int, output_dir: str, 
                           wipe_sqlite: bool, db_path: Optional[str] = None) -> bool:
    """Generate synthetic data and load into SQLite.
    
    Args:
        users: Number of users to generate
        days: Number of days of transaction history
        output_dir: Output directory for data files
        wipe_sqlite: Whether to wipe SQLite before loading
        db_path: Path to SQLite database
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Step 1: Generate data
        print("\n" + "=" * 60)
        print("Step 1: Generating synthetic data")
        print("=" * 60)
        print(f"Users: {users}")
        print(f"Days: {days}")
        print(f"Output directory: {output_dir}")
        print("=" * 60)
        
        generate_all_data(count=users, output_dir=output_dir, days=days)
        print("\nData generation complete!")
        
        # Step 2: Load to SQLite (always uses SQLite, not Firestore)
        print("\n" + "=" * 60)
        print("Step 2: Loading data to SQLite")
        print("=" * 60)
        
        # If we wiped SQLite, don't clear again (already empty). If we didn't wipe, clear to start fresh.
        load_data_to_sqlite(data_dir=output_dir, db_path=db_path, clear_existing=not wipe_sqlite)
        
        print("\nData loading complete!")
        return True
        
    except Exception as e:
        print(f"\nError in generate_and_load_data: {e}")
        import traceback
        traceback.print_exc()
        return False


def process_data(time_windows: List[str], skip_processing: bool, 
                db_path: Optional[str] = None) -> bool:
    """Process data using vectorized operations in SQLite.
    
    This function ALWAYS uses SQLite for processing. The ETL pipeline loads data
    into SQLite first, then processes it using vectorized operations. Firestore
    is only used for push operations, not for processing.
    
    Args:
        time_windows: List of time windows to process (e.g., ['30d', '180d'])
        skip_processing: If True, skip feature/persona/recommendation computation
        db_path: Path to SQLite database (unused, kept for API compatibility)
        
    Returns:
        True if successful, False otherwise
    """
    if skip_processing:
        print("\nSkipping data processing (features, personas, recommendations).")
        return True
    
    try:
        # Step 3: Compute features (vectorized, SQLite-only)
        print("\n" + "=" * 60)
        print("Step 3: Computing features (vectorized, SQLite)")
        print("=" * 60)
        
        from src.features.compute_all_vectorized import compute_all_features_vectorized
        
        for time_window in time_windows:
            window_days = int(time_window.replace('d', ''))
            print(f"\nComputing features for {time_window} window...")
            compute_all_features_vectorized(window_days=window_days, time_window=time_window, verbose=True, use_sqlite=True)
        
        print("\nFeature computation complete!")
        
        # Step 4: Assign personas (vectorized, SQLite-only)
        print("\n" + "=" * 60)
        print("Step 4: Assigning personas (vectorized, SQLite)")
        print("=" * 60)
        
        from src.personas.assign_all_vectorized import assign_all_users_vectorized
        
        assign_all_users_vectorized(time_windows=time_windows, use_sqlite=True, verbose=True)
        
        print("\nPersona assignment complete!")
        
        # Step 5: Generate recommendations (vectorized, SQLite-only)
        print("\n" + "=" * 60)
        print("Step 5: Generating recommendations (vectorized, SQLite)")
        print("=" * 60)
        
        from src.recommend.generate_all_vectorized import generate_all_recommendations_vectorized
        
        generate_all_recommendations_vectorized(time_windows=time_windows, use_sqlite=True, verbose=True)
        
        print("\nRecommendation generation complete!")
        
        return True
        
    except Exception as e:
        print(f"\nError in process_data: {e}")
        import traceback
        traceback.print_exc()
        return False


def push_to_firebase(collections: Optional[List[str]] = None, 
                    delay: float = 0.1) -> bool:
    """Push data from SQLite to Firebase.
    
    Args:
        collections: List of collections to push (None = all)
        delay: Delay between batches
        
    Returns:
        True if successful, False otherwise
    """
    # Get SQLite stats
    stats = get_sqlite_stats()
    
    # Show summary
    print("\n" + "=" * 60)
    print("Data to Push to Firebase")
    print("=" * 60)
    
    use_emulator = os.getenv('FIRESTORE_EMULATOR_HOST') is not None
    if use_emulator:
        print("Target: Firebase Emulator (localhost:8080)")
    else:
        print("Target: Firebase Production")
    
    if collections is None:
        collections = ['users', 'accounts', 'transactions', 'features', 'personas', 'recommendations']
    
    total_records = 0
    for collection in collections:
        count = stats.get(collection, 0)
        total_records += count
        print(f"{collection}: {count:,}")
    
    print(f"\nTotal records: {total_records:,}")
    print("=" * 60)
    
    # Confirm
    if use_emulator:
        message = f"Push {total_records:,} records to Firebase emulator?"
    else:
        message = f"WARNING: Push {total_records:,} records to Firebase PRODUCTION?"
    
    if not confirm_action(message, default='n'):
        print("Skipping Firebase push.")
        return False
    
    try:
        print("\n" + "=" * 60)
        print("Pushing data to Firebase")
        print("=" * 60)
        
        push_all_from_sqlite(
            collections=collections,
            dry_run=False,
            batch_size=500,
            delay=delay,
            max_retries=3
        )
        
        print("\nFirebase push complete!")
        return True
        
    except Exception as e:
        print(f"\nError pushing to Firebase: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="End-to-end ETL script for SpendSense data pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline with prompts
  python scripts/run_etl.py --wipe-sqlite --push-to-firebase
  
  # Archive before wiping
  python scripts/run_etl.py --wipe-sqlite --archive-before-wipe --push-to-firebase
  
  # Generate and process only (no push)
  python scripts/run_etl.py --wipe-sqlite
  
  # Custom parameters
  python scripts/run_etl.py --users 100 --days 90 --time-windows 30d
  
  # Skip processing (just generate and load)
  python scripts/run_etl.py --wipe-sqlite --skip-processing
        """
    )
    
    parser.add_argument(
        "--users",
        type=int,
        default=200,
        help="Number of users to generate (default: 200)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=200,
        help="Number of days of transaction history (default: 200)"
    )
    parser.add_argument(
        "--wipe-sqlite",
        action="store_true",
        help="Wipe SQLite database before loading (requires confirmation)"
    )
    parser.add_argument(
        "--wipe-firebase",
        action="store_true",
        help="Wipe Firebase data before pushing (requires confirmation)"
    )
    parser.add_argument(
        "--push-to-firebase",
        action="store_true",
        help="Push processed data to Firebase (requires confirmation)"
    )
    parser.add_argument(
        "--time-windows",
        type=str,
        nargs="+",
        default=["30d", "180d"],
        choices=["30d", "180d"],
        help="Time windows for processing (default: 30d 180d)"
    )
    parser.add_argument(
        "--skip-processing",
        action="store_true",
        help="Skip feature/persona/recommendation computation"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Output directory for data files (default: data)"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to SQLite database file (default: data/spendsense.db)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.1,
        help="Delay between batches when pushing to Firebase (default: 0.1)"
    )
    parser.add_argument(
        "--archive-before-wipe",
        action="store_true",
        help="Archive SQLite data to Parquet before wiping (requires confirmation)"
    )
    parser.add_argument(
        "--archive-dir",
        type=str,
        default="data/archives",
        help="Directory for SQLite archives (default: data/archives)"
    )
    
    args = parser.parse_args()
    
    start_time = time.time()
    
    print("=" * 60)
    print("SpendSense ETL Pipeline")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Users: {args.users}")
    print(f"Days: {args.days}")
    print(f"Time windows: {', '.join(args.time_windows)}")
    print(f"Wipe SQLite: {args.wipe_sqlite}")
    print(f"Wipe Firebase: {args.wipe_firebase}")
    print(f"Push to Firebase: {args.push_to_firebase}")
    print(f"Skip processing: {args.skip_processing}")
    print(f"Archive before wipe: {args.archive_before_wipe}")
    print("=" * 60)
    
    # Step 0: Archive SQLite (if requested and before wipe)
    archive_path = None
    if args.archive_before_wipe:
        if not args.wipe_sqlite:
            print("Warning: --archive-before-wipe requires --wipe-sqlite. Skipping archive.")
        else:
            stats = get_sqlite_stats(args.db_path)
            if stats['users'] > 0 or stats['accounts'] > 0 or stats['transactions'] > 0:
                print("\n" + "=" * 60)
                print("Archive SQLite Database")
                print("=" * 60)
                print("Archive location will be:", args.archive_dir)
                print("=" * 60)
                
                if confirm_action("Archive SQLite data to Parquet before wiping?", default='y'):
                    archive_path = archive_sqlite_to_parquet(args.db_path, args.archive_dir)
                    if archive_path:
                        print(f"Archive saved to: {archive_path}")
                    else:
                        if not confirm_action("Archive failed. Continue with wipe anyway?", default='n'):
                            print("Aborted.")
                            return 1
                else:
                    print("Skipping archive.")
            else:
                print("SQLite database is empty. Nothing to archive.")
    
    # Step 1: Wipe SQLite (if requested)
    if args.wipe_sqlite:
        if not wipe_sqlite_database(args.db_path):
            print("Failed to wipe SQLite database. Exiting.")
            return 1
    
    # Step 2: Generate and load data
    if not generate_and_load_data(args.users, args.days, args.output_dir, 
                                  args.wipe_sqlite, args.db_path):
        print("Failed to generate and load data. Exiting.")
        return 1
    
    # Step 3: Process data
    if not process_data(args.time_windows, args.skip_processing, args.db_path):
        print("Failed to process data. Exiting.")
        return 1
    
    # Step 4: Wipe Firebase (if requested)
    if args.wipe_firebase:
        if not wipe_firebase_data():
            print("Failed to wipe Firebase data. Continuing anyway...")
    
    # Step 5: Push to Firebase (if requested)
    if args.push_to_firebase:
        if not push_to_firebase(collections=None, delay=args.delay):
            print("Failed to push to Firebase. Continuing...")
    
    # Final summary
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("ETL Pipeline Complete!")
    print("=" * 60)
    print(f"Total time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nSQLite Database:")
    sqlite_stats = get_sqlite_stats(args.db_path)
    for key, value in sqlite_stats.items():
        if value > 0:
            print(f"  {key}: {value:,}")
    
    if args.push_to_firebase:
        print("\nFirebase:")
        print("  Getting Firebase statistics...")
        try:
            firebase_stats = get_firebase_stats()
            for key, value in firebase_stats.items():
                if value > 0:
                    print(f"  {key}: {value:,}")
        except Exception as e:
            print(f"  Warning: Could not retrieve Firebase stats: {e}")
    
    if archive_path:
        print(f"\nArchive saved to: {archive_path}")
    
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

