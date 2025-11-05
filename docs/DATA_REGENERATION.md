# Data Regeneration Guide

This guide explains how to regenerate your synthetic data with the new Plaid-compatible schema.

## Quick Start

### Option 1: Regenerate Everything (Recommended)

```bash
# Generate 200 days of data, skip Firestore to reduce Firebase touches
python -m src.ingest.regenerate_data --skip-firestore

# Or with Parquet export (recommended for better storage)
python -m src.ingest.regenerate_data --skip-firestore --parquet
```

### Option 2: Custom Options

```bash
# Generate 100 users, 200 days, with Parquet export, skip Firestore
python -m src.ingest.regenerate_data --users 100 --days 200 --parquet --skip-firestore

# Generate and load to both SQLite and Firestore
python -m src.ingest.regenerate_data --parquet
```

## CSV vs Parquet

### CSV (Default)
- **Pros**: Human-readable, works everywhere, easy to inspect
- **Cons**: Larger file size, slower reads
- **Use when**: You need to inspect data manually, or don't have pandas/pyarrow installed

### Parquet (Recommended)
- **Pros**: 
  - **50-70% smaller file size** (compressed)
  - **3-10x faster reads**
  - Better type preservation (arrays stored as arrays, not JSON strings)
  - Standard format for data pipelines
- **Cons**: Requires pandas/pyarrow (`pip install pandas pyarrow`)
- **Use when**: You want efficient storage and fast loading

**For default 200 users with 200 days of history:**
- CSV: ~20-30 MB
- Parquet: ~8-12 MB (with snappy compression)

## Firebase Optimization

### Reducing Firebase Touches

Firestore batch writes are limited to 500 operations per batch. Our optimized loader:
- Batches transactions in groups of 500
- For ~15,000 transactions = ~30 batch writes (instead of 15,000 individual writes)

**To minimize Firebase usage:**
1. Use `--skip-firestore` flag to only load to SQLite
2. Load to Firestore only when needed for API/testing
3. Use Parquet format for faster re-loading if needed

### Loading to Firestore (when needed)

```bash
# Load everything to Firestore
python -m src.ingest.regenerate_data

# Or load separately (if you already have CSV files)
python -c "from src.ingest.data_loader import *; load_users_to_firestore(); load_accounts_to_firestore(); load_transactions_to_firestore()"
```

## Storage Recommendations

### For Development/Testing
- **SQLite**: Fast, local, no dependencies
- **CSV files**: Keep in `data/` directory
- **Skip Firestore**: Use `--skip-firestore` flag

### For Production/Staging
- **Parquet files**: Store in S3/GCS for efficient loading
- **SQLite**: Use for local development
- **Firestore**: Load only when needed for API access

### Safe Storage

1. **Version control**: Add `data/*.csv` and `data/*.parquet` to `.gitignore`
2. **Backup**: Keep data files in versioned storage (S3, GCS)
3. **Database**: SQLite file is in `data/spendsense.db` (backup regularly)

## What Gets Generated

With default 200 users and 200 days:

- **Users**: 200 user profiles (100 constructed: 20 per persona, 100 unconstructed)
- **Accounts**: ~200-250 accounts (checking, savings, credit cards, loans)
- **Transactions**: ~15,000-20,000 transactions
- **Liabilities**: Credit card and loan liability data

## Data Structure

All data follows Plaid-compatible schema:

- **Transactions**: Category arrays, location data, payment channels
- **Accounts**: Depository, credit, and loan accounts with proper subtypes
- **Liabilities**: Credit card and loan liability details

## Troubleshooting

### "pandas/pyarrow not installed"
```bash
pip install pandas pyarrow
```

### "Database locked" error
- Close any other connections to the SQLite database
- Or delete `data/spendsense.db` and regenerate

### "Firebase not initialized"
- Set `FIRESTORE_EMULATOR_HOST` for local emulator
- Or configure `FIREBASE_SERVICE_ACCOUNT` environment variable
- Or use `--skip-firestore` flag

### Large file sizes
- Use `--parquet` flag for compression
- Or reduce `--users` count
- Or reduce `--days` count

## Next Steps

After regeneration:

1. **Verify data**: Check `data/transactions.csv` has new fields
2. **Test API**: Start your FastAPI server and test endpoints
3. **Check database**: Verify SQLite has all new columns
4. **Run migrations**: If using existing database, migrations run automatically

