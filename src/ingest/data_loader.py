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

# Add project root to path so imports work when run as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.db import get_db_connection, init_schema


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


if __name__ == "__main__":
    load_data_to_db()

