"""Data loader for SpendSense.

This module loads synthetic data from CSV and JSON files into the SQLite database.
It handles idempotent operations, so it can be run multiple times safely.
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
from src.database.firestore import store_user, db


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
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO transactions
                        (transaction_id, account_id, user_id, date, amount, merchant_name, category, pending)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            row["transaction_id"],
                            row["account_id"],
                            row["user_id"],
                            row["date"],
                            float(row["amount"]),
                            row["merchant_name"],
                            row["category"],
                            int(row["pending"])
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


def load_users_to_firestore():
    """Load users from JSON to Firestore"""
    with open('data/users.json', 'r') as f:
        users = json.load(f)
    
    for user in users:
        store_user(user)
        print(f"Loaded user: {user['user_id']}")


def load_accounts_to_firestore():
    """Load accounts from CSV to Firestore"""
    accounts_df = pd.read_csv('data/accounts.csv')
    
    for _, account in accounts_df.iterrows():
        user_id = account['user_id']
        account_data = account.to_dict()
        
        db.collection('users').document(user_id)\
          .collection('accounts').document(account['account_id'])\
          .set(account_data)
        
        print(f"Loaded account: {account['account_id']}")


def load_transactions_to_firestore():
    """Load transactions from CSV to Firestore"""
    transactions_df = pd.read_csv('data/transactions.csv')
    
    # Batch write for efficiency (max 500 per batch)
    batch = db.batch()
    count = 0
    
    for _, txn in transactions_df.iterrows():
        user_id = txn['user_id']
        txn_data = txn.to_dict()
        
        txn_ref = db.collection('users').document(user_id)\
                    .collection('transactions').document(txn['transaction_id'])
        batch.set(txn_ref, txn_data)
        count += 1
        
        # Commit batch every 500 operations
        if count % 500 == 0:
            batch.commit()
            batch = db.batch()
            print(f"Loaded {count} transactions...")
    
    # Commit remaining
    batch.commit()
    print(f"Total transactions loaded: {count}")


if __name__ == "__main__":
    print("Loading users...")
    load_users_to_firestore()
    
    print("Loading accounts...")
    load_accounts_to_firestore()
    
    print("Loading transactions...")
    load_transactions_to_firestore()
    
    print("Data loading complete!")

