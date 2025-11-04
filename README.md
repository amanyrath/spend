# SpendSense

Financial Education Platform - Behavioral Signal Detection & Personalized Recommendations

## Overview

SpendSense is a local-first financial education system that analyzes synthetic transaction data to deliver personalized, explainable financial guidance. This demonstration project focuses on core algorithms and explainability.

## Features

- Synthetic data generation for 50-100 users
- Behavioral signal detection (subscriptions, credit utilization, savings, income stability)
- Persona-based personalization with clear rationales
- Operator oversight and auditability interface
- Evaluation metrics (coverage, explainability, latency, auditability)

## Setup

### Prerequisites

- Python 3.11 or 3.12 (Python 3.14 is not yet fully supported by pandas)
- pip

**Important:** If you're using Python 3.14, pandas 2.1.3 won't compile. Either:
- Use Python 3.11 or 3.12 instead (recommended)
- Or update pandas to 2.2.0+ in requirements.txt

### Installation

**Yes, you need a virtual environment.** It's recommended to isolate project dependencies.

1. Clone the repository (if not already done):
```bash
git clone <repository-url>
cd spend
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note:** After creating the venv, always activate it before running any commands:
```bash
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
```

## Project Structure

```
spendsense/
├── data/              # Data files (CSV, JSON) and database
├── src/               # Source code
│   ├── ingest/       # Data generation and loading
│   ├── features/     # Signal detection
│   ├── personas/     # Persona assignment
│   ├── recommend/    # Recommendation engine
│   ├── guardrails/   # Tone and eligibility validation
│   ├── api/          # FastAPI endpoints
│   └── database/     # Database schema and utilities
├── operator_ui/      # Operator interface (future)
├── eval/             # Evaluation metrics
├── tests/            # Test suite
├── docs/             # Documentation
└── results/          # Evaluation reports
```

## Quick Start

**Make sure your virtual environment is activated:**
```bash
source venv/bin/activate  # macOS/Linux
```

### Phase 1.2: Synthetic Data Generation

1. Generate synthetic data (creates CSV/JSON files in `data/` directory):
```bash
python3 src/ingest/data_generator.py
```

Expected output:
- `data/users.json` - 75 user profiles
- `data/accounts.csv` - Bank accounts
- `data/transactions.csv` - Transaction history
- `data/liabilities.csv` - Credit card liabilities

2. Load data into SQLite database:
```bash
python3 src/ingest/data_loader.py
```

**Note:** Make sure you're in the project root directory (`/Users/alexismanyrath/Code/spend`) when running these commands. The scripts will automatically add the project root to the Python path.

Expected output:
- `data/spendsense.db` - SQLite database with all data loaded
- Verification messages showing counts of inserted records

**Verify it worked:**
```bash
# Check that files were created
ls -lh data/

# Check database exists
ls -lh data/spendsense.db
```

2. Compute features:
```bash
python src/features/compute_all.py
```

3. Assign personas:
```bash
python src/personas/assign_all.py
```

4. Generate recommendations:
```bash
python src/recommend/generate_all.py
```

5. Start the API:
```bash
uvicorn src.api.main:app --reload
```

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

## Documentation

See `docs/` directory for:
- Decision log
- Schema documentation
- Limitations

## License

[Your License Here]

