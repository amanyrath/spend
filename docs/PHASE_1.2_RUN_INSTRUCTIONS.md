# Phase 1.2: Complete Run Instructions

## Step-by-Step Setup and Execution

### 1. Setup (One-time)

```bash
# Navigate to project directory
cd /Users/alexismanyrath/Code/spend

# Create virtual environment (if not already created)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Verify setup:**
```bash
# Check Python version (should be 3.11+)
python3 --version

# Check packages installed
pip list | grep -E "faker|pandas|fastapi"
```

### 2. Generate Synthetic Data

```bash
# Make sure venv is activated
source venv/bin/activate

# Generate data (this creates CSV/JSON files)
python3 src/ingest/data_generator.py
```

**Expected output:**
```
Generating synthetic data for 200 users...
Generated 200 users
Generated XXX accounts
Generated XXX transactions
Applying diversity strategy...
Generated XX liabilities
Exporting data to files...
Exported 200 users to data/users.json
Exported XXX accounts to data/accounts.csv
Exported XXX transactions to data/transactions.csv
Exported XX liabilities to data/liabilities.csv
Data generation complete!
```

### 3. Load Data into Database

```bash
# Still in venv
python3 src/ingest/data_loader.py
```

**Expected output:**
```
Initializing database schema...
Schema initialized
Loading users from data/users.json...
Inserted 200 users
Loading accounts from data/accounts.csv...
Inserted XXX accounts
Loading transactions from data/transactions.csv...
Inserted XXX transactions

Verifying data integrity...
Users in database: 75
Accounts in database: XXX
Transactions in database: XXX
No orphaned transactions found
No orphaned accounts found

Data loading complete!
```

### 4. Verify Everything Works

```bash
# Check files exist
ls -lh data/

# Expected files:
# - users.json
# - accounts.csv
# - transactions.csv
# - liabilities.csv
# - spendsense.db

# Optional: Inspect database
python3 -c "
from src.database.db import fetch_all
users = fetch_all('SELECT COUNT(*) as count FROM users')
print(f'Users in DB: {users[0][\"count\"]}')
"
```

## Troubleshooting

### "python3: command not found"
- Use `python` instead of `python3`
- Or install Python 3.11+ via Homebrew: `brew install python3`

### "ModuleNotFoundError: No module named 'src'"
- Make sure you're in the project root directory (`/Users/alexismanyrath/Code/spend`)
- Make sure venv is activated
- Run from project root, not from `src/` directory

### "Permission denied" errors
- Make sure `data/` directory exists and is writable
- Run: `mkdir -p data && chmod 755 data`

### Virtual environment not activating
- Make sure you're using the correct path: `source venv/bin/activate`
- Check venv exists: `ls -la venv/`
- If it doesn't exist, create it: `python3 -m venv venv`

## Next Steps

After Phase 1.2 is complete:
- Phase 1.3: Signal Detection (compute features from transactions)
- Phase 1.4: Database Integration (complete feature storage)
- Phase 2.1: Persona Assignment

