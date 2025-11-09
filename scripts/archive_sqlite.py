"""Standalone utility to archive SQLite database to Parquet format.

This script can be run independently to create a timestamped archive of
all SQLite data without running the full ETL pipeline.

Usage:
    python scripts/archive_sqlite.py [--db-path PATH] [--archive-dir DIR]
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.run_etl import archive_sqlite_to_parquet


def main():
    parser = argparse.ArgumentParser(
        description="Archive SQLite database to Parquet format with timestamp",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Archive default database
  python scripts/archive_sqlite.py
  
  # Archive custom database location
  python scripts/archive_sqlite.py --db-path /path/to/spendsense.db
  
  # Custom archive directory
  python scripts/archive_sqlite.py --archive-dir backups/sqlite
        """
    )
    
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to SQLite database file (default: data/spendsense.db)"
    )
    parser.add_argument(
        "--archive-dir",
        type=str,
        default="data/archives",
        help="Directory for SQLite archives (default: data/archives)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("SQLite Database Archive Utility")
    print("=" * 60)
    print(f"Database: {args.db_path or 'data/spendsense.db'}")
    print(f"Archive directory: {args.archive_dir}")
    print("=" * 60)
    
    archive_path = archive_sqlite_to_parquet(args.db_path, args.archive_dir)
    
    if archive_path:
        print("\n" + "=" * 60)
        print("Archive Complete!")
        print("=" * 60)
        print(f"Archive location: {archive_path}")
        print("=" * 60)
        return 0
    else:
        print("\nArchive failed or no data to archive.")
        return 1


if __name__ == "__main__":
    sys.exit(main())







