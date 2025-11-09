"""Load data into SQLite without Firebase dependencies.

This script loads data from CSV/JSON files into SQLite database
without requiring Firebase initialization.
"""

import json
import csv
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
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
        
        # Clear existing data first (to start fresh)
        print("Clearing existing data...")
        cursor.execute("DELETE FROM transactions")
        cursor.execute("DELETE FROM liabilities")
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
                    INSERT INTO users (user_id, name, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (user["user_id"], user["name"], user["created_at"])
                )
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
                        INSERT INTO accounts 
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
                    accounts_inserted += 1
                except Exception as e:
                    print(f"Error inserting account {row.get('account_id', 'unknown')}: {e}")
        
        print(f"Inserted {accounts_inserted} accounts")
        
        # Load liabilities from CSV
        liabilities_file = data_path / "liabilities.csv"
        if not liabilities_file.exists():
            print(f"Warning: Liabilities file not found: {liabilities_file}, skipping...")
            liabilities_inserted = 0
        else:
            print(f"Loading liabilities from {liabilities_file}...")
            liabilities_inserted = 0
            with open(liabilities_file, "r", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        # Handle empty/null fields
                        def get_float(val):
                            return None if val == "" or val is None else float(val)
                        
                        def get_int(val):
                            return None if val == "" or val is None else int(val == "True" or val == "1")
                        
                        def get_str(val):
                            return None if val == "" or val is None else val
                        
                        cursor.execute(
                            """
                            INSERT INTO liabilities 
                            (account_id, account_type, account_subtype, aprs, 
                             minimum_payment_amount, last_payment_amount, is_overdue, last_statement_balance,
                             origination_date, original_principal_balance, interest_rate, 
                             next_payment_due_date, principal_balance, escrow_balance, 
                             property_address, guarantor)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                row["account_id"],
                                get_str(row["account_type"]),
                                get_str(row["account_subtype"]),
                                get_str(row["aprs"]),
                                get_float(row.get("minimum_payment_amount")),
                                get_float(row.get("last_payment_amount")),
                                get_int(row.get("is_overdue")),
                                get_float(row.get("last_statement_balance")),
                                get_str(row.get("origination_date")),
                                get_float(row.get("original_principal_balance")),
                                get_float(row.get("interest_rate")),
                                get_str(row.get("next_payment_due_date")),
                                get_float(row.get("principal_balance")),
                                get_float(row.get("escrow_balance")),
                                get_str(row.get("property_address")),
                                get_str(row.get("guarantor"))
                            )
                        )
                        liabilities_inserted += 1
                    except Exception as e:
                        print(f"Error inserting liability for account {row.get('account_id', 'unknown')}: {e}")
            
            print(f"Inserted {liabilities_inserted} liabilities")
        
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
                            INSERT INTO transactions
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
                INSERT INTO transactions
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
        
        # Count liabilities
        cursor.execute("SELECT COUNT(*) FROM liabilities")
        liability_count = cursor.fetchone()[0]
        print(f"Liabilities in database: {liability_count}")
        
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
    import argparse
    
    parser = argparse.ArgumentParser(description="Load data into SQLite database")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Directory containing data files (default: data)"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to SQLite database file (default: data/spendsense.db)"
    )
    
    args = parser.parse_args()
    
    load_data_to_db(data_dir=args.data_dir, db_path=args.db_path)

