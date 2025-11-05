"""Regenerate synthetic data with Plaid-compatible schema.

This script follows a SQLite-first workflow:
1. Regenerates all synthetic data with 200 days of transaction history
2. Exports to CSV (and optionally Parquet for better compression)
3. Loads to SQLite database only
4. Optionally pushes all data to Firebase (if --push-to-firebase flag set)

All processing (features, personas, recommendations) should happen in SQLite.
After processing, use --push-to-firebase to sync everything to Firebase.

Usage:
    python -m src.ingest.regenerate_data [--push-to-firebase] [--parquet]
"""

import argparse
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.ingest.data_generator import generate_all_data
from src.ingest.data_loader import load_data_to_db


def main():
    parser = argparse.ArgumentParser(description="Regenerate synthetic data")
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
        "--push-to-firebase",
        action="store_true",
        help="Push all data (raw + processed) to Firebase after generation and processing"
    )
    parser.add_argument(
        "--parquet",
        action="store_true",
        help="Also export to Parquet format (smaller, faster reads)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Output directory (default: data)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Regenerating Synthetic Data (SQLite-First Workflow)")
    print("=" * 60)
    print(f"Users: {args.users}")
    print(f"Days: {args.days}")
    print(f"Push to Firebase: {args.push_to_firebase}")
    print(f"Parquet export: {args.parquet}")
    print("=" * 60)
    print()
    
    # Step 1: Generate data
    print("Step 1: Generating synthetic data...")
    generate_all_data(count=args.users, output_dir=args.output_dir, days=args.days)
    print()
    
    # Step 2: Export to Parquet if requested
    if args.parquet:
        print("Step 2: Exporting to Parquet format...")
        try:
            import pandas as pd
            
            # Export transactions to Parquet
            transactions_df = pd.read_csv(f"{args.output_dir}/transactions.csv")
            # Parse category JSON strings back to arrays for proper storage
            import json
            transactions_df['category'] = transactions_df['category'].apply(
                lambda x: json.loads(x) if isinstance(x, str) and x.startswith('[') else [x] if x else []
            )
            transactions_df.to_parquet(f"{args.output_dir}/transactions.parquet", index=False, compression='snappy')
            print(f"  Exported {len(transactions_df)} transactions to Parquet")
            
            # Export accounts to Parquet
            accounts_df = pd.read_csv(f"{args.output_dir}/accounts.csv")
            accounts_df.to_parquet(f"{args.output_dir}/accounts.parquet", index=False, compression='snappy')
            print(f"  Exported {len(accounts_df)} accounts to Parquet")
            
            # Export liabilities to Parquet if exists
            liabilities_path = Path(f"{args.output_dir}/liabilities.csv")
            if liabilities_path.exists():
                liabilities_df = pd.read_csv(liabilities_path)
                liabilities_df.to_parquet(f"{args.output_dir}/liabilities.parquet", index=False, compression='snappy')
                print(f"  Exported {len(liabilities_df)} liabilities to Parquet")
            
            print("  Parquet files are compressed and ready for efficient storage/loading")
        except ImportError:
            print("  Warning: pandas/pyarrow not installed. Install with: pip install pandas pyarrow")
            print("  Skipping Parquet export...")
        print()
    
    # Step 3: Load to SQLite
    print("Step 3: Loading data to SQLite database...")
    load_data_to_db(data_dir=args.output_dir)
    print()
    
    # Step 4: Push to Firebase (if requested)
    if args.push_to_firebase:
        print("Step 4: Pushing data to Firebase...")
        try:
            # Import here to avoid circular imports
            from src.ingest.push_from_sqlite import push_all_from_sqlite
            push_all_from_sqlite(collections=None)  # None = push all collections
            print("  Firebase push complete")
        except Exception as e:
            print(f"  Error: Firebase push failed: {e}")
            print("  Continuing with SQLite only...")
            import traceback
            traceback.print_exc()
    else:
        print("Step 4: Skipping Firebase push (use --push-to-firebase to enable)")
        print("  Next steps:")
        print("  1. Process data in SQLite:")
        print("     python src/features/compute_all.py --sqlite")
        print("     python src/personas/assign_all.py")
        print("     python src/recommend/generate_all.py")
        print("  2. Push everything to Firebase:")
        print("     python -m src.ingest.push_from_sqlite")
    
    print()
    print("=" * 60)
    print("Data regeneration complete!")
    print("=" * 60)
    print(f"Data files: {args.output_dir}/")
    print("  - users.json")
    print("  - accounts.csv" + (" (and .parquet)" if args.parquet else ""))
    print("  - transactions.csv" + (" (and .parquet)" if args.parquet else ""))
    print("  - liabilities.csv" + (" (and .parquet)" if args.parquet else ""))
    print()
    print("Database: SQLite (data/spendsense.db)")
    if args.push_to_firebase:
        print("Database: Firebase (data pushed)")
    print()


if __name__ == "__main__":
    main()

