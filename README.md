# SpendSense

Financial Education Platform - Behavioral Signal Detection & Personalized Recommendations

## Overview

SpendSense is a local-first financial education system that analyzes synthetic transaction data to deliver personalized, explainable financial guidance. This demonstration project focuses on core algorithms and explainability.

## Features

- **Synthetic Data Generation**: Generate realistic transaction data for 50-200 users with Plaid-compatible schema
- **Behavioral Signal Detection**: Detect subscriptions, credit utilization, savings patterns, and income stability
- **Persona-Based Personalization**: Assign users to personas with clear rationales
- **Personalized Recommendations**: Generate educational content and partner offers with explainable rationales
- **Chat Interface**: AI-powered chat for financial questions with PII protection and guardrails
- **Consumer UI**: Modern React-based dashboard for end users
- **Operator Interface**: HTML-based oversight and auditability interface
- **Evaluation Metrics**: Automated coverage, explainability, latency, and auditability metrics
- **Multi-Database Support**: Works with SQLite (local), Firebase Firestore (production), or Firebase Emulator

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
spend/
├── data/                  # Data files (CSV, JSON, Parquet) and database
├── src/                   # Source code
│   ├── ingest/           # Data generation and loading
│   ├── features/         # Signal detection
│   ├── personas/         # Persona assignment
│   ├── recommend/        # Recommendation engine
│   ├── guardrails/       # Tone, eligibility validation, and PII protection
│   ├── chat/             # Chat service and prompts
│   ├── api/              # FastAPI endpoints
│   ├── database/         # Database schema and utilities (SQLite/Firestore)
│   └── utils/            # Utility functions (category normalization, etc.)
├── consumer_ui/          # Consumer-facing React dashboard
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   └── lib/          # API client and utilities
│   └── dist/             # Build output
├── operator_ui/          # Operator interface (HTML/JavaScript)
│   └── templates/        # HTML templates
├── eval/                 # Evaluation metrics
├── tests/                # Test suite
├── docs/                 # Documentation
└── results/              # Evaluation reports
```

## Quick Start

**Make sure your virtual environment is activated:**
```bash
source venv/bin/activate  # macOS/Linux
```

### Phase 1.2: Synthetic Data Generation (SQLite-First Workflow)

**The project follows a SQLite-first workflow:**
1. Generate data → Load to SQLite only
2. Process everything in SQLite (features, personas, recommendations)
3. Push all data to Firebase when ready

**Option 1: Regenerate Everything (Recommended)**

Regenerate all synthetic data and load it into SQLite:
```bash
# Generate 200 days of data and load to SQLite only
python -m src.ingest.regenerate_data

# Or with Parquet export (recommended for better storage)
python -m src.ingest.regenerate_data --parquet
```

**Option 2: Generate and Push to Firebase in One Step**

If you want to push raw data immediately after generation:
```bash
# Generate and push to Firebase (only raw data - no processed data yet)
python -m src.ingest.regenerate_data --push-to-firebase
```

**Note:** Make sure you're in the project root directory when running these commands. The scripts will automatically add the project root to the Python path.

Expected output:
- `data/users.json` - User profiles (default: 200 users)
- `data/accounts.csv` - Bank accounts (and `.parquet` if using `--parquet`)
- `data/transactions.csv` - Transaction history (and `.parquet` if using `--parquet`)
- `data/liabilities.csv` - Credit card liabilities (and `.parquet` if using `--parquet`)
- `data/spendsense.db` - SQLite database with all data loaded

**Option 2: Manual Steps (if you need more control)**

1. Generate synthetic data (creates CSV/JSON files in `data/` directory):
```bash
python3 src/ingest/data_generator.py
```

2. Load data into SQLite database:
```bash
python3 src/ingest/data_loader.py
```

**Verify it worked:**
```bash
# Check that files were created
ls -lh data/

# Check database exists
ls -lh data/spendsense.db
```

**See `docs/DATA_REGENERATION.md` for detailed regeneration options, custom parameters, and troubleshooting.**

### Pushing Data to Firebase Production

**Note:** The `push_to_production.py` script is kept for backward compatibility. For new workflows, use `push_from_sqlite.py` instead.

To push existing data (from SQLite or CSV files) to Firebase production:

```bash
# Push from SQLite database
python -m src.ingest.push_to_production --from-sqlite

# Push from CSV/JSON files
python -m src.ingest.push_to_production --from-csv

# Dry run (preview what would be pushed)
python -m src.ingest.push_to_production --from-sqlite --dry-run
```

**⚠️ Safety Features:**
- Requires Firebase production credentials (not emulator)
- Requires double confirmation before pushing
- Shows data counts before pushing
- Dry-run mode to preview changes

### Loading Data from Firebase to SQLite

To load data from Firebase back into SQLite (useful for syncing production data locally):

```bash
# Load all data from Firebase to SQLite
python -m src.ingest.load_from_firebase

# Load specific collections only
python -m src.ingest.load_from_firebase --collections users,accounts,transactions

# Load with overwrite (replace existing records)
python -m src.ingest.load_from_firebase --overwrite

# Dry run (preview what would be loaded)
python -m src.ingest.load_from_firebase --dry-run
```

### Pushing Data from SQLite to Firebase

To push all data (raw + processed) from SQLite to Firebase:

```bash
# Push all collections
python -m src.ingest.push_from_sqlite

# Push specific collections only
python -m src.ingest.push_from_sqlite --collections users,accounts,transactions,features,personas,recommendations

# Dry run (preview what would be pushed)
python -m src.ingest.push_from_sqlite --dry-run

# Custom batch size for transactions
python -m src.ingest.push_from_sqlite --batch-size 500
```

### Phase 2: Compute Features and Generate Recommendations

1. Compute behavioral signals:

**Option A: Standard (parallel processing)**
```bash
python src/features/compute_all.py
```

**Option B: Vectorized (fastest - uses pandas)**
```bash
python src/features/compute_all_vectorized.py
```

**Performance Options:**
```bash
# Use 4 parallel workers
python src/features/compute_all.py --workers 4

# Quiet mode (less verbose)
python src/features/compute_all.py --quiet

# Vectorized mode (fastest for large datasets)
python src/features/compute_all_vectorized.py --window 30d
```

The vectorized version loads all data into memory and processes all users at once using pandas operations, which is typically 10-50x faster for large datasets.

2. Assign personas (processes in SQLite):
```bash
python src/personas/assign_all.py
```

3. Generate recommendations (processes in SQLite):
```bash
python src/recommend/generate_all.py
```

4. Push everything to Firebase (after processing):
```bash
python -m src.ingest.push_from_sqlite
```

### Phase 3: Start the Application

#### Option 1: Full Stack (Recommended)

**Terminal 1 - Start Backend API:**
```bash
uvicorn src.api.main:app --reload --port 8000
```

**Terminal 2 - Start Consumer UI:**
```bash
cd consumer_ui
npm install  # First time only
npm run dev
```

The Consumer UI will be available at `http://localhost:5173` and will automatically redirect to `http://localhost:5173/user_001` (default user).

The API will be available at `http://localhost:8000`

**See `LOCAL_SETUP.md` for detailed setup instructions.**

#### Option 2: API Only

```bash
uvicorn src.api.main:app --reload
```

The API will be available at `http://localhost:8000`

### Using the Operator UI

The Operator UI is a simple HTML/JavaScript interface for viewing users and recommendations:

1. Make sure the API is running
2. Open `operator_ui/templates/user_list.html` in your browser
3. Or serve it with a simple HTTP server:
```bash
cd operator_ui/templates
python3 -m http.server 8080
```
Then visit `http://localhost:8080/user_list.html`

**Note**: Update the `API_BASE_URL` in the HTML files if your API is running on a different port.

### Running Evaluation

Generate evaluation metrics:
```bash
python eval/evaluate.py
```

This will create:
- `results/evaluation_report.json` - Detailed metrics
- `results/summary.txt` - Human-readable summary

## API Endpoints

### Core Endpoints

- `GET /api/health` - Health check
- `GET /api/users` - List all users
- `GET /api/users/{user_id}` - Get user details
- `GET /api/users/{user_id}/signals` - Get user's behavioral signals
- `GET /api/users/{user_id}/recommendations` - Get user's recommendations

### Chat Endpoint

- `POST /api/chat` - Chat with AI assistant about financial topics
  - Request body: `{ "user_id": "user_001", "message": "How can I improve my credit score?" }`
  - Includes PII detection and guardrails for safe responses

### Operator Endpoints

- `GET /api/operator/users` - List users with summary statistics
- `GET /api/operator/users/{user_id}` - Get detailed user information for operators
- `GET /api/operator/recommendations` - List all recommendations across users

See `docs/schema.md` for detailed API response formats.

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

**Test Coverage**: The project currently has **22 test functions** across 3 test files:
- `tests/test_persona_assignment.py`: 7 tests
- `tests/test_signal_detection.py`: 5 tests  
- `tests/test_recommendations.py`: 10 tests

All tests cover core functionality including persona assignment, signal detection, and recommendation generation.

## Documentation

See `docs/` directory for:
- `schema.md` - Database schema and API documentation
- `DATA_REGENERATION.md` - Detailed guide for regenerating synthetic data
- `DATA_METHODOLOGY.md` - Methodology for synthetic data generation
- `SECURITY_AND_PII_PROTECTION.md` - Security measures and PII handling
- `GUARDRAILS_SETUP.md` - Guardrails configuration and usage
- `decision_log.md` - Key design decisions and rationale
- `limitations.md` - Known limitations and future improvements
- `TROUBLESHOOTING.md` - Common issues and solutions

See root directory for:
- `LOCAL_SETUP.md` - Complete local development setup guide
- `FIREBASE_EMULATOR_SETUP.md` - Firebase emulator setup and usage
- `TESTING_WITH_EMULATORS.md` - Complete guide for testing with emulators using SQL/CSV data
- `deployment-guide.md` - Deployment instructions for Vercel + Firebase
- `WORKFLOW.md` - Complete workflow overview

## Architecture

SpendSense follows a modular architecture:

- **Data Layer**: SQLite (local), Firebase Firestore (production), or Firebase Emulator
- **Feature Layer**: Signal detection algorithms for behavioral analysis
- **Persona Layer**: Persona assignment logic with hierarchical criteria
- **Recommendation Layer**: Content matching and rationale generation
- **Guardrails Layer**: Tone validation, eligibility checks, and PII protection
- **Chat Layer**: AI-powered chat with guardrails and citations
- **API Layer**: FastAPI REST endpoints
- **UI Layer**: 
  - Consumer UI: React + TypeScript + shadcn/ui (modern dashboard)
  - Operator UI: HTML/JavaScript (oversight interface)

The system automatically detects the deployment environment and uses the appropriate database backend:
- **SQLite**: Default for local development (set `USE_SQLITE=true` to force)
- **Firebase Emulator**: Auto-detected when running on `localhost:8080` (or set `FIRESTORE_EMULATOR_HOST=localhost:8080`)
- **Firebase Production**: Set `FIREBASE_SERVICE_ACCOUNT` or provide `firebase-service-account.json`

**Priority Order:**
1. If `USE_SQLITE=true` → **Force SQLite** (takes precedence over everything)
2. If `FIRESTORE_EMULATOR_HOST` is set → Use emulator
3. If emulator detected on port 8080 → Use emulator (auto-detected)
4. If `FIREBASE_SERVICE_ACCOUNT` or `firebase-service-account.json` exists → Use production Firebase
5. Otherwise → Use SQLite (default fallback)

## Database Options

### SQLite (Default - Local Development)
- No setup required
- Data stored in `data/spendsense.db`
- Fast and simple for local development
- **Force SQLite**: Set `USE_SQLITE=true` to use SQLite even if Firebase emulator is running

### Firebase Emulator (Local Testing)
- Test Firebase features locally without credentials
- **Auto-detected** when running on `localhost:8080` - just start the emulator!
- See `FIREBASE_EMULATOR_SETUP.md` for setup instructions
- See `TESTING_WITH_EMULATORS.md` for complete testing guide with SQL/CSV data
- Quick start: `python test_with_emulators.py`
- Manual start: `firebase emulators:start --only firestore`

### Firebase Firestore (Production)
- Requires Firebase service account credentials
- Set `FIREBASE_SERVICE_ACCOUNT` environment variable or provide `firebase-service-account.json`
- See `deployment-guide.md` for production deployment

## Consumer UI

The Consumer UI is a modern React application built with:
- React 19 + TypeScript
- Vite
- Tailwind CSS
- shadcn/ui components
- React Router

**Features:**
- Education page with personalized recommendations and rationale boxes
- Insights page with behavioral signals and analytics
- Transactions page with transaction history
- Offers page with partner recommendations

**Development:**
```bash
cd consumer_ui
npm install
npm run dev
```

**See `consumer_ui/README.md` for more details.**

## Chat Feature

SpendSense includes an AI-powered chat interface for answering financial questions:

- **PII Protection**: Automatically detects and sanitizes PII before sending to LLM
- **Guardrails**: Validates tone and ensures safe, helpful responses
- **Citations**: Provides citations linking back to user's financial data
- **Audit Trail**: All chat interactions are logged for operator review

**Usage:**
```bash
POST /api/chat
{
  "user_id": "user_001",
  "message": "How can I improve my credit score?"
}
```

## License

[Your License Here]

