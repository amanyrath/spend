"""Pull a single user and their transactions from Firebase to local SQLite.

This script is useful for testing locally with real Firebase data.

Usage:
    python scripts/pull_single_user.py
    python scripts/pull_single_user.py --user-id user_042
    python scripts/pull_single_user.py --dry-run
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import db
from src.database.firestore import get_db, get_all_users, get_user, get_user_accounts, get_user_transactions


def pull_single_user(user_id: str = None, dry_run: bool = False):
    """Pull a single user and their transactions from Firebase to SQLite.
    
    Args:
        user_id: User ID to pull. If None, pulls the first user found.
        dry_run: If True, only preview what would be loaded without actually writing.
    """
    print("=" * 60)
    print("PULL SINGLE USER FROM FIREBASE")
    print("=" * 60)
    
    # Get Firebase client
    client = get_db()
    if client is None:
        print("ERROR: Firebase not initialized.")
        print()
        print("Make sure you have:")
        print("  1. Firebase emulator running (firebase emulators:start)")
        print("  OR")
        print("  2. Firebase credentials (FIREBASE_SERVICE_ACCOUNT or firebase-service-account.json)")
        return False
    
    # Get user
    if user_id:
        print(f"Looking for user: {user_id}")
        user = get_user(user_id)
        if not user:
            print(f"ERROR: User {user_id} not found in Firebase")
            return False
    else:
        print("No user_id specified, finding first user...")
        users = get_all_users()
        if not users:
            print("ERROR: No users found in Firebase")
            return False
        user = users[0]
        user_id = user['user_id']
        print(f"Found user: {user_id}")
    
    print()
    print(f"User: {user_id}")
    print(f"Name: {user.get('name', 'N/A')}")
    print(f"Created: {user.get('created_at', 'N/A')}")
    
    # Get accounts
    accounts = get_user_accounts(user_id)
    print(f"Accounts: {len(accounts)}")
    
    # Get transactions
    transactions = get_user_transactions(user_id)
    print(f"Transactions: {len(transactions)}")
    
    if dry_run:
        print()
        print("=" * 60)
        print("DRY RUN MODE - No data will be written")
        print("=" * 60)
        print()
        print("Summary:")
        print(f"  User: {user_id}")
        print(f"  Accounts: {len(accounts)}")
        print(f"  Transactions: {len(transactions)}")
        return True
    
    # Write to SQLite
    print()
    print("Writing to SQLite...")
    
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Insert or replace user
        cursor.execute(
            """
            INSERT OR REPLACE INTO users (user_id, name, created_at)
            VALUES (?, ?, ?)
            """,
            (user_id, user.get('name'), user.get('created_at'))
        )
        print(f"  ✓ User {user_id} written")
        
        # Insert or replace accounts
        for account in accounts:
            cursor.execute(
                """
                INSERT OR REPLACE INTO accounts 
                (account_id, user_id, type, subtype, balance, "limit", mask)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    account['account_id'],
                    account['user_id'],
                    account.get('type'),
                    account.get('subtype'),
                    account.get('balance', 0.0),
                    account.get('limit'),
                    account.get('mask')
                )
            )
        print(f"  ✓ {len(accounts)} accounts written")
        
        # Insert or replace transactions
        for txn in transactions:
            # Handle category field (may be list or string)
            category = txn.get('category', [])
            if isinstance(category, list):
                category = json.dumps(category)
            elif not isinstance(category, str):
                category = json.dumps([str(category)])
            
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
                    txn['transaction_id'],
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
        print(f"  ✓ {len(transactions)} transactions written")
    
    print()
    print("=" * 60)
    print("SUCCESS!")
    print("=" * 60)
    print()
    print("You can now:")
    print("  1. Run feature computation: python src/features/compute_all.py")
    print("  2. Assign personas: python src/personas/assign_all.py")
    print("  3. Generate recommendations: python src/recommend/generate_all.py")
    print("  4. Start the API: uvicorn src.api.main:app --reload")
    print()
    print(f"Test the API with: http://localhost:8000/api/users/{user_id}")
    print()
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Pull a single user from Firebase to SQLite")
    parser.add_argument(
        "--user-id",
        type=str,
        default=None,
        help="User ID to pull (default: first user found)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be loaded without actually writing"
    )
    
    args = parser.parse_args()
    
    success = pull_single_user(user_id=args.user_id, dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

