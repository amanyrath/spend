"""Utility to push existing data to Firebase production.

This script loads data from SQLite database or CSV files and pushes it to
Firebase production. It includes safety checks and confirmation prompts.

Usage:
    python -m src.ingest.push_to_production [--from-sqlite] [--from-csv] [--dry-run]
"""

import argparse
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.ingest.data_loader import load_users_to_firestore, load_accounts_to_firestore, load_transactions_to_firestore


def check_production_setup():
    """Check if Firebase production is properly configured.
    
    Returns:
        tuple: (is_production, error_message)
    """
    # Check for production credentials
    has_service_account = os.getenv('FIREBASE_SERVICE_ACCOUNT') is not None
    has_service_account_file = os.path.exists('firebase-service-account.json')
    
    # Check for emulator (should NOT be set for production)
    has_emulator_host = os.getenv('FIRESTORE_EMULATOR_HOST') is not None
    use_emulator = os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true'
    
    if has_emulator_host or use_emulator:
        return False, "Firestore emulator is detected. Unset FIRESTORE_EMULATOR_HOST and USE_FIREBASE_EMULATOR to use production."
    
    if not has_service_account and not has_service_account_file:
        return False, "Firebase production credentials not found. Set FIREBASE_SERVICE_ACCOUNT environment variable or create firebase-service-account.json"
    
    return True, None


def confirm_production_push(user_count: int = None, account_count: int = None, transaction_count: int = None):
    """Prompt user to confirm production push.
    
    Args:
        user_count: Number of users to push (optional)
        account_count: Number of accounts to push (optional)
        transaction_count: Number of transactions to push (optional)
    """
    print("\n" + "=" * 60)
    print("⚠️  WARNING: PUSHING TO FIREBASE PRODUCTION")
    print("=" * 60)
    
    if user_count:
        print(f"Users to push: {user_count}")
    if account_count:
        print(f"Accounts to push: {account_count}")
    if transaction_count:
        print(f"Transactions to push: {transaction_count}")
    
    print("\nThis will:")
    print("  - Overwrite existing data in Firebase production")
    print("  - May incur Firebase costs")
    print("  - Cannot be easily undone")
    
    print("\nAre you sure you want to proceed? (yes/no): ", end="")
    response = input().strip().lower()
    
    if response != 'yes':
        print("Aborted.")
        return False
    
    # Double confirmation
    print("\nType 'CONFIRM' to proceed with production push: ", end="")
    confirm = input().strip()
    
    if confirm != 'CONFIRM':
        print("Aborted.")
        return False
    
    return True


def push_from_sqlite(data_dir: str = "data", dry_run: bool = False):
    """Push data from SQLite database to Firebase production.
    
    Args:
        data_dir: Directory containing data files (default: "data")
        dry_run: If True, only show what would be pushed without actually pushing
    """
    from src.database import db
    
    # Get counts from SQLite
    users_query = "SELECT COUNT(*) as count FROM users"
    user_row = db.fetch_one(users_query)
    user_count = user_row["count"] if user_row else 0
    
    accounts_query = "SELECT COUNT(*) as count FROM accounts"
    account_row = db.fetch_one(accounts_query)
    account_count = account_row["count"] if account_row else 0
    
    transactions_query = "SELECT COUNT(*) as count FROM transactions"
    transaction_row = db.fetch_one(transactions_query)
    transaction_count = transaction_row["count"] if transaction_row else 0
    
    print(f"\nSQLite database contains:")
    print(f"  - {user_count} users")
    print(f"  - {account_count} accounts")
    print(f"  - {transaction_count} transactions")
    
    if dry_run:
        print("\n[DRY RUN] Would push:")
        print(f"  - {user_count} users")
        print(f"  - {account_count} accounts")
        print(f"  - {transaction_count} transactions")
        return
    
    if not confirm_production_push(user_count, account_count, transaction_count):
        return
    
    # Export SQLite data to CSV/JSON first (since loader functions expect files)
    print("\nExporting SQLite data to temporary files...")
    import json
    import csv
    
    temp_dir = Path(data_dir) / "temp_export"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Export users
    users = db.fetch_all("SELECT user_id, name, created_at FROM users")
    users_data = [{"user_id": row["user_id"], "name": row["name"], "created_at": row["created_at"]} for row in users]
    with open(temp_dir / "users.json", "w") as f:
        json.dump(users_data, f, indent=2)
    
    # Export accounts
    accounts = db.fetch_all("SELECT account_id, user_id, type, subtype, balance, \"limit\", mask FROM accounts")
    accounts_file = temp_dir / "accounts.csv"
    with open(accounts_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["account_id", "user_id", "type", "subtype", "balance", "limit", "mask"])
        writer.writeheader()
        for row in accounts:
            writer.writerow({
                "account_id": row["account_id"],
                "user_id": row["user_id"],
                "type": row["type"],
                "subtype": row["subtype"],
                "balance": row["balance"],
                "limit": row["limit"] or "",
                "mask": row["mask"]
            })
    
    # Export transactions
    transactions = db.fetch_all("""
        SELECT transaction_id, account_id, user_id, date, amount, merchant_name, category, pending,
               location_address, location_city, location_region, location_postal_code,
               location_country, location_lat, location_lon,
               iso_currency_code, payment_channel, authorized_date
        FROM transactions
    """)
    transactions_file = temp_dir / "transactions.csv"
    fieldnames = ["transaction_id", "account_id", "user_id", "date", "amount", "merchant_name", "category", "pending",
                  "location_address", "location_city", "location_region", "location_postal_code",
                  "location_country", "location_lat", "location_lon",
                  "iso_currency_code", "payment_channel", "authorized_date"]
    with open(transactions_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in transactions:
            writer.writerow({
                k: row[k] if row[k] is not None else "" for k in fieldnames
            })
    
    print(f"  Exported to {temp_dir}/")
    
    # Push to Firebase
    print("\nPushing to Firebase production...")
    try:
        load_users_to_firestore(data_dir=str(temp_dir))
        load_accounts_to_firestore(data_dir=str(temp_dir))
        load_transactions_to_firestore(data_dir=str(temp_dir))
        print("\n✅ Successfully pushed data to Firebase production!")
    except Exception as e:
        print(f"\n❌ Error pushing to Firebase: {e}")
        raise
    finally:
        # Clean up temp files
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"\nCleaned up temporary files")


def push_from_csv(data_dir: str = "data", dry_run: bool = False):
    """Push data from CSV/JSON files to Firebase production.
    
    Args:
        data_dir: Directory containing data files (default: "data")
        dry_run: If True, only show what would be pushed without actually pushing
    """
    import json
    
    data_path = Path(data_dir)
    
    # Count users
    users_file = data_path / "users.json"
    if users_file.exists():
        with open(users_file, "r") as f:
            users = json.load(f)
        user_count = len(users)
    else:
        user_count = 0
        print(f"Warning: {users_file} not found")
    
    # Count accounts
    accounts_file = data_path / "accounts.csv"
    if accounts_file.exists():
        import pandas as pd
        accounts_df = pd.read_csv(accounts_file)
        account_count = len(accounts_df)
    else:
        account_count = 0
        print(f"Warning: {accounts_file} not found")
    
    # Count transactions
    transactions_file = data_path / "transactions.csv"
    if transactions_file.exists():
        import pandas as pd
        transactions_df = pd.read_csv(transactions_file)
        transaction_count = len(transactions_df)
    else:
        transaction_count = 0
        print(f"Warning: {transactions_file} not found")
    
    print(f"\nData files contain:")
    print(f"  - {user_count} users")
    print(f"  - {account_count} accounts")
    print(f"  - {transaction_count} transactions")
    
    if dry_run:
        print("\n[DRY RUN] Would push:")
        print(f"  - {user_count} users")
        print(f"  - {account_count} accounts")
        print(f"  - {transaction_count} transactions")
        return
    
    if not confirm_production_push(user_count, account_count, transaction_count):
        return
    
    # Push to Firebase
    print("\nPushing to Firebase production...")
    try:
        load_users_to_firestore(data_dir=data_dir)
        load_accounts_to_firestore(data_dir=data_dir)
        load_transactions_to_firestore(data_dir=data_dir)
        print("\n✅ Successfully pushed data to Firebase production!")
    except Exception as e:
        print(f"\n❌ Error pushing to Firebase: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Push existing data to Firebase production",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Push from SQLite database
  python -m src.ingest.push_to_production --from-sqlite
  
  # Push from CSV/JSON files
  python -m src.ingest.push_to_production --from-csv
  
  # Dry run (show what would be pushed without actually pushing)
  python -m src.ingest.push_to_production --from-sqlite --dry-run
        """
    )
    
    parser.add_argument(
        "--from-sqlite",
        action="store_true",
        help="Push data from SQLite database"
    )
    parser.add_argument(
        "--from-csv",
        action="store_true",
        help="Push data from CSV/JSON files"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Directory containing data files (default: data)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be pushed without actually pushing"
    )
    
    args = parser.parse_args()
    
    # Check production setup
    is_production, error_msg = check_production_setup()
    
    if not is_production:
        print(f"❌ {error_msg}")
        sys.exit(1)
    
    print("✅ Firebase production credentials detected")
    
    if args.dry_run:
        print("\n[DRY RUN MODE] No data will be pushed")
    
    # Determine source
    if args.from_sqlite and args.from_csv:
        print("❌ Error: Cannot specify both --from-sqlite and --from-csv")
        sys.exit(1)
    
    if not args.from_sqlite and not args.from_csv:
        # Default to SQLite if database exists
        db_path = Path(args.data_dir) / "spendsense.db"
        if db_path.exists():
            print("\n📊 SQLite database detected, using --from-sqlite")
            args.from_sqlite = True
        else:
            print("\n📁 No SQLite database found, using --from-csv")
            args.from_csv = True
    
    # Push data
    try:
        if args.from_sqlite:
            push_from_sqlite(data_dir=args.data_dir, dry_run=args.dry_run)
        else:
            push_from_csv(data_dir=args.data_dir, dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Failed to push data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

