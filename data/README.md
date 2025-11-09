# Data Loading Guide

This directory contains data files and archives for the SpendSense application. This guide explains how to load, process, and manage your data.

## Directory Structure

```
data/
├── users.json              # User profiles (JSON)
├── accounts.csv            # Account information (CSV)
├── transactions.csv        # Transaction history (CSV)
├── transactions_formatted.csv  # Formatted transactions (CSV)
├── liabilities.csv         # Liability data (CSV)
├── spendsense.db          # SQLite database (created automatically)
└── archives/               # Timestamped Parquet archives (created automatically)
    └── archive_YYYYMMDD_HHMMSS/
        ├── users.parquet
        ├── accounts.parquet
        ├── transactions.parquet
        ├── computed_features.parquet
        ├── persona_assignments.parquet
        ├── recommendations.parquet
        └── metadata.json
```

## Quick Start

### Full ETL Pipeline (Recommended)

The easiest way to generate, load, and process data:

```bash
# Full pipeline with prompts (interactive)
python scripts/run_etl.py --wipe-sqlite --push-to-firebase

# Archive before wiping
python scripts/run_etl.py --wipe-sqlite --archive-before-wipe --push-to-firebase

# Generate and process only (no Firebase push)
python scripts/run_etl.py --wipe-sqlite

# Custom parameters
python scripts/run_etl.py --users 100 --days 90 --wipe-sqlite --time-windows 30d
```

### What the ETL Script Does

1. **Archive** (optional): Backs up existing SQLite data to Parquet format
2. **Wipe** (optional): Clears SQLite/Firebase data with confirmation prompts
3. **Generate**: Creates synthetic financial data (users, accounts, transactions, liabilities)
4. **Load**: Imports data into SQLite database
5. **Process**: Computes features, assigns personas, generates recommendations (vectorized)
6. **Push** (optional): Uploads processed data to Firebase/Firestore

## Data Loading Options

### Option 1: ETL Script (Recommended)

**Primary method** - End-to-end pipeline with all processing:

```bash
# Interactive mode (requires confirmations)
python scripts/run_etl.py --wipe-sqlite --push-to-firebase

# Non-interactive mode (auto-confirm)
# Not recommended for production wipe/push operations
```

**Key Features:**
- Vectorized SQLite processing (fast)
- Confirmation prompts for destructive operations
- Archive functionality before wiping
- Full feature computation and persona assignment
- Recommendation generation

### Option 2: Standalone Archive Utility

Archive existing SQLite data without running full ETL:

```bash
# Archive default database
python scripts/archive_sqlite.py

# Custom database location
python scripts/archive_sqlite.py --db-path /path/to/spendsense.db

# Custom archive directory
python scripts/archive_sqlite.py --archive-dir backups/sqlite
```

**What it does:**
- Exports all SQLite tables to Parquet format
- Creates timestamped archive directory
- Includes metadata JSON with archive info
- Uses Snappy compression for efficiency

### Option 3: Regenerate Data Script

Legacy script for data generation only:

```bash
# Generate and load to SQLite only
python -m src.ingest.regenerate_data --skip-firestore

# Generate with Parquet export
python -m src.ingest.regenerate_data --skip-firestore --parquet

# Custom parameters
python -m src.ingest.regenerate_data --users 100 --days 200 --parquet --skip-firestore
```

**Note:** This script only generates and loads raw data. Use `scripts/run_etl.py` for full processing.

## ETL Script Arguments

### Data Generation

```bash
--users NUM              # Number of users to generate (default: 200)
--days NUM               # Days of transaction history (default: 200)
--output-dir PATH        # Output directory for CSV/JSON files (default: data)
```

### Database Options

```bash
--db-path PATH           # SQLite database path (default: data/spendsense.db)
--wipe-sqlite            # Wipe SQLite before loading (requires confirmation)
--wipe-firebase          # Wipe Firebase before pushing (requires confirmation)
```

### Processing Options

```bash
--skip-processing        # Skip feature/persona/recommendation computation
--time-windows WINDOWS   # Time windows for processing (default: 30d 180d)
                         # Options: 30d, 180d
```

### Firebase Options

```bash
--push-to-firebase       # Push processed data to Firebase (requires confirmation)
--delay SECONDS          # Delay between batches when pushing (default: 0.1)
```

### Archive Options

```bash
--archive-before-wipe    # Archive SQLite data before wiping (requires confirmation)
--archive-dir PATH       # Directory for archives (default: data/archives)
```

## Common Workflows

### 1. Fresh Start (Development)

Clear everything and start fresh:

```bash
python scripts/run_etl.py --wipe-sqlite --wipe-firebase --push-to-firebase
```

### 2. Backup Before Changes

Archive existing data before making changes:

```bash
python scripts/run_etl.py --archive-before-wipe --wipe-sqlite --push-to-firebase
```

### 3. Local Development Only

Generate and process locally without Firebase:

```bash
python scripts/run_etl.py --wipe-sqlite
```

### 4. Regenerate with Different Parameters

Generate different dataset size:

```bash
python scripts/run_etl.py --wipe-sqlite --users 500 --days 365 --time-windows 30d 180d 365d
```

### 5. Skip Processing (Raw Data Only)

Generate and load without feature computation:

```bash
python scripts/run_etl.py --wipe-sqlite --skip-processing
```

### 6. Archive Existing Data

Archive without running ETL:

```bash
python scripts/archive_sqlite.py
```

## Data File Formats

### users.json

JSON array of user objects:
```json
[
  {
    "user_id": "user_001",
    "name": "John Doe",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### accounts.csv

CSV with columns:
- `user_id`, `account_id`, `name`, `type`, `subtype`, `balance`, `currency`, `mask`, `official_name`

### transactions.csv

CSV with columns:
- `transaction_id`, `user_id`, `account_id`, `amount`, `date`, `name`, `merchant_name`, `category`, `location`, `payment_channel`, `authorized_date`, `iso_currency_code`

### liabilities.csv

CSV with liability information:
- `user_id`, `account_id`, `type`, `payments`, `interest_rates`, etc.

## Data Processing

### Vectorized Operations

The ETL script uses vectorized operations in SQLite for performance:

1. **Feature Computation** (`compute_all_vectorized.py`):
   - Subscriptions detection
   - Credit utilization
   - Savings behavior
   - Income stability
   - Spending patterns

2. **Persona Assignment** (`assign_all_vectorized.py`):
   - Analyzes computed features
   - Assigns persona groups
   - Calculates match percentages

3. **Recommendation Generation** (`generate_all_vectorized.py`):
   - Generates personalized recommendations
   - Creates rationales
   - Stores decision traces

### Processing Time Windows

Recommendations are computed for multiple time windows:
- `30d`: Last 30 days (short-term patterns)
- `180d`: Last 180 days (medium-term trends)

These can be customized with `--time-windows` flag.

## Archive Format

Archives are stored in Parquet format for efficiency:

```
data/archives/archive_20241105_104530/
├── users.parquet
├── accounts.parquet
├── transactions.parquet
├── computed_features.parquet
├── persona_assignments.parquet
├── recommendations.parquet
└── metadata.json
```

### Reading Archives

```python
import pandas as pd

# Read archived data
df = pd.read_parquet('data/archives/archive_20241105_104530/transactions.parquet')

# Read metadata
import json
with open('data/archives/archive_20241105_104530/metadata.json') as f:
    metadata = json.load(f)
```

## Database Schema

The SQLite database (`spendsense.db`) contains:

- **users**: User profiles
- **accounts**: Account information
- **transactions**: Transaction history
- **computed_features**: Computed financial features
- **persona_assignments**: User persona assignments
- **recommendations**: Generated recommendations

See `src/database/schema.sql` for full schema definition.

## Firebase Integration

### Emulator vs Production

The ETL script automatically detects Firebase emulator:

```bash
# Using emulator (if FIRESTORE_EMULATOR_HOST is set)
export FIRESTORE_EMULATOR_HOST=localhost:8080
python scripts/run_etl.py --push-to-firebase

# Using production (requires service account)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
python scripts/run_etl.py --push-to-firebase
```

### Pushing to Firebase

The script pushes the following collections:
- `users`
- `accounts`
- `transactions`
- `features`
- `personas`
- `recommendations`

**Important:** The script requires confirmation before pushing to production.

## Troubleshooting

### "pandas/pyarrow not installed"

Archives require pandas and pyarrow:

```bash
pip install pandas pyarrow
```

### "Database locked"

Close other connections to SQLite database or delete and regenerate:

```bash
rm data/spendsense.db
python scripts/run_etl.py --wipe-sqlite
```

### "Firebase not initialized"

For emulator:
```bash
export FIRESTORE_EMULATOR_HOST=localhost:8080
```

For production:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### "No user features found"

Ensure processing step ran:
```bash
python scripts/run_etl.py --wipe-sqlite  # Don't use --skip-processing
```

### Large file sizes

Use Parquet format or reduce data size:
```bash
python scripts/run_etl.py --users 50 --days 90
```

## Best Practices

1. **Always archive before wiping** (use `--archive-before-wipe`)
2. **Use Parquet format** for archives (smaller, faster)
3. **Confirm before destructive operations** (wipe, push to production)
4. **Test with emulator first** before pushing to production
5. **Keep archives versioned** in external storage (S3, GCS)
6. **Use SQLite for development** (fast, local, no dependencies)

## Related Documentation

- `docs/DATA_REGENERATION.md` - Legacy data regeneration guide
- `docs/DATA_METHODOLOGY.md` - Data generation methodology
- `src/database/schema.sql` - Database schema definition
- `scripts/run_etl.py` - ETL script source code

## Support

For issues or questions:
1. Check this README
2. Review `docs/TROUBLESHOOTING.md`
3. Check script help: `python scripts/run_etl.py --help`







