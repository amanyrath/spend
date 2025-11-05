"""Data loader for SpendSense.

This module loads synthetic data from CSV and JSON files into the SQLite database.
It handles idempotent operations, so it can be run multiple times safely.

NOTE: SQLite-First Workflow
----------------------------
This module is designed for the initial data generation workflow. The project follows
a SQLite-first approach:

1. Generate data → Load to SQLite only (via load_data_to_db)
2. Process everything in SQLite (features, personas, recommendations)
3. Push all data to Firebase when ready (via push_from_sqlite.py)

For pushing processed data to Firebase, use:
- src.ingest.push_from_sqlite: Push all data from SQLite to Firebase
- src.ingest.load_from_firebase: Load data from Firebase back to SQLite

The functions below (load_users_to_firestore, load_accounts_to_firestore, etc.)
are kept for backward compatibility but are primarily used during initial data
generation. For pushing processed data, use push_from_sqlite.py instead.
"""

import json
import csv
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import pandas as pd

# Add project root to path so imports work when run as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.db import get_db_connection, init_schema
from src.database.firestore import store_user, get_db


def load_data_to_db(data_dir: str = "data", db_path: Optional[str] = None) -> None:
    """Load data from files into SQLite database.
    
    This function:
    1. Initializes the database schema
    2. Reads users from JSON file
    3. Reads accounts, transactions, and liabilities from CSV files
    4. Inserts data into database tables (idempotent)
    5. Verifies data integrity
    
    Args:
        data_dir: Directory containing data files (default: "data")
        db_path: Path to SQLite database file. If None, uses default path.
    """
    data_path = Path(data_dir)
    
    # Initialize schema
    print("Initializing database schema...")
    init_schema(db_path)
    print("Schema initialized")
    
    # Get database connection
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
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
                    
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO transactions
                        (transaction_id, account_id, user_id, date, amount, merchant_name, category, pending,
                         location_address, location_city, location_region, location_postal_code,
                         location_country, location_lat, location_lon,
                         iso_currency_code, payment_channel, authorized_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
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
                        )
                    )
                    if cursor.rowcount > 0:
                        transactions_inserted += 1
                except Exception as e:
                    print(f"Error inserting transaction {row.get('transaction_id', 'unknown')}: {e}")
        
        print(f"Inserted {transactions_inserted} transactions")
        
        # Note: Liabilities are not stored in the database schema as a separate table
        # They are stored as part of account data or can be computed from transactions
        # For now, we'll skip loading liabilities into the database
        
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


def load_users_to_firestore(data_dir: str = "data"):
    """Load users from JSON to Firestore.
    
    NOTE: This function is primarily for initial data generation.
    For pushing processed data, use src.ingest.push_from_sqlite instead.
    """
    users_file = Path(data_dir) / "users.json"
    with open(users_file, 'r') as f:
        users = json.load(f)
    
    loaded_count = 0
    for user in users:
        store_user(user)
        loaded_count += 1
        if loaded_count % 25 == 0:
            print(f"  Loaded {loaded_count}/{len(users)} users...")
    
    print(f"  Loaded {loaded_count} users to Firestore")


def load_accounts_to_firestore(data_dir: str = "data"):
    """Load accounts from CSV to Firestore.
    
    NOTE: This function is primarily for initial data generation.
    For pushing processed data, use src.ingest.push_from_sqlite instead.
    """
    db = get_db()
    if db is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists, or set FIRESTORE_EMULATOR_HOST for emulator.")
    
    accounts_file = Path(data_dir) / "accounts.csv"
    accounts_df = pd.read_csv(accounts_file)
    
    loaded_count = 0
    for _, account in accounts_df.iterrows():
        user_id = account['user_id']
        account_data = account.to_dict()
        
        db.collection('users').document(user_id)\
          .collection('accounts').document(account['account_id'])\
          .set(account_data)
        
        loaded_count += 1
        if loaded_count % 100 == 0:
            print(f"  Loaded {loaded_count}/{len(accounts_df)} accounts...")
    
    print(f"  Loaded {loaded_count} accounts to Firestore")


def load_transactions_to_firestore(data_dir: str = "data", batch_size: int = 500):
    """Load transactions from CSV to Firestore with optimized batching.
    
    NOTE: This function is primarily for initial data generation.
    For pushing processed data, use src.ingest.push_from_sqlite instead.
    
    Args:
        data_dir: Directory containing transactions.csv (default: "data")
        batch_size: Number of transactions per batch (default: 500, max: 500)
    """
    db = get_db()
    if db is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists, or set FIRESTORE_EMULATOR_HOST for emulator.")
    
    transactions_file = Path(data_dir) / "transactions.csv"
    transactions_df = pd.read_csv(transactions_file)
    
    # Batch write for efficiency (max 500 per batch)
    batch = db.batch()
    count = 0
    total_batches = 0
    
    for _, txn in transactions_df.iterrows():
        user_id = txn['user_id']
        txn_data = txn.to_dict()
        
        # Parse category field (handle both JSON array and legacy string)
        category = txn_data.get('category', '')
        if isinstance(category, str):
            if category.startswith('['):
                try:
                    txn_data['category'] = json.loads(category)
                except:
                    # If parsing fails, wrap in array
                    txn_data['category'] = [category] if category else []
            else:
                # Legacy string format, convert to array
                txn_data['category'] = [category] if category else []
        
        # Handle None values for location fields
        for field in ['location_address', 'location_city', 'location_region', 
                     'location_postal_code', 'location_country', 'location_lat', 
                     'location_lon', 'payment_channel', 'authorized_date']:
            if field in txn_data and (pd.isna(txn_data[field]) or txn_data[field] == ''):
                txn_data[field] = None
        
        txn_ref = db.collection('users').document(user_id)\
                    .collection('transactions').document(txn['transaction_id'])
        batch.set(txn_ref, txn_data)
        count += 1
        
        # Commit batch every batch_size operations (Firestore limit is 500)
        if count % batch_size == 0:
            batch.commit()
            batch = db.batch()
            total_batches += 1
            print(f"  Committed batch {total_batches} ({count}/{len(transactions_df)} transactions)...")
    
    # Commit remaining
    if count % batch_size != 0:
        batch.commit()
        total_batches += 1
    
    print(f"  Loaded {count} transactions to Firestore ({total_batches} batches)")


if __name__ == "__main__":
    print("Loading users...")
    load_users_to_firestore()
    
    print("Loading accounts...")
    load_accounts_to_firestore()
    
    print("Loading transactions...")
    load_transactions_to_firestore()
    
    print("Data loading complete!")

