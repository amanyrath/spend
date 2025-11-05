# SpendSense Workflow Overview

## Your Current System Architecture

You have a **dual-environment** system that works both locally (SQLite) and in production (Firebase Firestore):

```
┌─────────────────────────────────────────────────────────┐
│                    DATA PIPELINE                        │
└─────────────────────────────────────────────────────────┘

1. Generate Synthetic Data
   ↓
2. Load into Database (SQLite or Firestore)
   ↓
3. Compute Features/Signals
   ↓
4. Assign Personas
   ↓
5. Generate Recommendations
   ↓
6. Serve via API
   ↓
7. Display in UI (Consumer or Operator)
```

## Complete Workflow Breakdown

### Phase 1: Data Preparation (One-time or when refreshing data)

**Step 1: Generate Synthetic Data**
```bash
source venv/bin/activate
python3 src/ingest/data_generator.py
```
**Output:** Creates `data/users.json`, `data/accounts.csv`, `data/transactions.csv`, `data/liabilities.csv`

**Step 2: Load Data into Database**
```bash
python3 src/ingest/data_loader.py
```
**Output:** Creates `data/spendsense.db` (SQLite) or loads to Firestore

**What happens:**
- Reads CSV/JSON files
- Inserts into database tables
- Verifies data integrity

### Phase 2: Feature Computation

**Step 3: Compute Behavioral Signals**
```bash
python src/features/compute_all.py
```
**What happens:**
- Analyzes transactions for each user
- Detects: subscriptions, credit utilization, savings patterns, income stability
- Stores computed features in database

**Output:** Features stored in `computed_features` table

### Phase 3: Persona Assignment

**Step 4: Assign Personas**
```bash
python src/personas/assign_all.py
```
**What happens:**
- Matches users to personas based on behavioral signals
- Personas: high_utilization, subscription_heavy, savings_builder, variable_income, general_wellness
- Stores assignments in `persona_assignments` table

**Output:** Each user gets a persona assignment

### Phase 4: Recommendation Generation

**Step 5: Generate Recommendations**
```bash
python src/recommend/generate_all.py
```
**What happens:**
- Matches personas to education content and offers
- Generates rationales explaining why content is shown
- Creates decision traces for auditability
- Stores in `recommendations` table

**Output:** Recommendations with rationales and traces

### Phase 5: Serve via API

**Step 6: Start Backend API**
```bash
python -m uvicorn src.api.main:app --reload --port 8000
```
**Available at:** `http://localhost:8000`

**Endpoints:**
- `GET /api/health` - Health check
- `GET /api/users` - List all users (operator view)
- `GET /api/users/{user_id}` - User details
- `GET /api/users/{user_id}/signals` - Behavioral signals
- `GET /api/users/{user_id}/recommendations` - Recommendations
- `GET /api/users/{user_id}/transactions` - Transaction history

### Phase 6: Frontend Applications

**Option A: Consumer Dashboard (NEW)**
```bash
cd consumer_ui
npm install  # First time only
npm run dev
```
**Available at:** `http://localhost:5173`

**Features:**
- Education page (personalized content)
- Insights page (behavioral signals)
- Transactions page (spending history)
- Offers page (partner offers)

**Option B: Operator UI (EXISTING)**
```bash
cd operator_ui/templates
python3 -m http.server 8080
```
**Available at:** `http://localhost:8080/user_list.html`

**Features:**
- User list with filtering
- User detail view
- Decision trace viewer
- Signals and recommendations audit

## Your Typical Development Workflow

### Initial Setup (One Time)
1. Activate venv: `source venv/bin/activate`
2. Generate data: `python3 src/ingest/data_generator.py`
3. Load data: `python3 src/ingest/data_loader.py`
4. Compute features: `python src/features/compute_all.py`
5. Assign personas: `python src/personas/assign_all.py`
6. Generate recommendations: `python src/recommend/generate_all.py`

### Daily Development

**Terminal 1 - Backend:**
```bash
source venv/bin/activate
python -m uvicorn src.api.main:app --reload --port 8000
```

**Terminal 2 - Consumer UI:**
```bash
cd consumer_ui
npm run dev
```

**Terminal 3 - Operator UI (if needed):**
```bash
cd operator_ui/templates
python3 -m http.server 8080
```

### Testing Changes

**After modifying code:**
1. Backend auto-reloads (with `--reload` flag)
2. Frontend hot-reloads (Vite dev server)
3. Test in browser: `http://localhost:5173`

**Run tests:**
```bash
pytest tests/ -v
```

### Evaluation

**Generate metrics:**
```bash
python eval/evaluate.py
```
**Output:** `results/evaluation_report.json` and `results/summary.txt`

## Database Environment Detection

Your system automatically detects which database to use:

**Local (SQLite):**
- Uses `data/spendsense.db`
- No Firebase config needed
- Good for development

**Production (Firestore):**
- Detects `firebase-service-account.json` file
- Uses Firebase Firestore
- Configured for Vercel deployment

**Detection Logic:**
```python
USE_FIRESTORE = os.getenv('FIREBASE_SERVICE_ACCOUNT') is not None or \
                os.path.exists('firebase-service-account.json')
```

## Deployment Workflow

### Vercel Deployment

**Backend API:**
- Configured in `vercel.json` at root
- Uses `api/index.py` as entry point
- Serverless functions

**Consumer UI:**
- Configured in `consumer_ui/vercel.json`
- Static site generation
- Set `VITE_API_URL` environment variable

**Operator UI:**
- Simple HTML files
- Can be deployed to Vercel or any static host

## Key Files & Their Roles

**Backend:**
- `src/api/main.py` - FastAPI application
- `src/database/db.py` - SQLite utilities
- `src/database/firestore.py` - Firestore utilities
- `src/features/signal_detection.py` - Signal computation
- `src/personas/assignment.py` - Persona logic
- `src/recommend/engine.py` - Recommendation engine

**Frontend:**
- `consumer_ui/src/App.tsx` - Main React app
- `consumer_ui/src/pages/` - Page components
- `consumer_ui/src/components/` - Reusable components
- `consumer_ui/src/lib/api.ts` - API client

**Data:**
- `data/users.json` - User profiles
- `data/accounts.csv` - Bank accounts
- `data/transactions.csv` - Transaction history
- `data/spendsense.db` - SQLite database

## Common Workflows

### Adding New Features
1. Modify backend code in `src/`
2. Backend auto-reloads
3. Update frontend if needed
4. Test locally

### Refreshing Data
1. Re-run data generator: `python3 src/ingest/data_generator.py`
2. Re-run data loader: `python3 src/ingest/data_loader.py`
3. Re-compute features: `python src/features/compute_all.py`
4. Re-assign personas: `python src/personas/assign_all.py`
5. Re-generate recommendations: `python src/recommend/generate_all.py`

### Debugging
1. Check API logs in terminal running uvicorn
2. Check browser console for frontend errors
3. Check network tab for API calls
4. Use `pytest tests/ -v` for backend tests

## Quick Reference Commands

```bash
# Backend
source venv/bin/activate
python -m uvicorn src.api.main:app --reload --port 8000

# Consumer UI
cd consumer_ui && npm run dev

# Operator UI
cd operator_ui/templates && python3 -m http.server 8080

# Full pipeline (when refreshing data)
python3 src/ingest/data_generator.py
python3 src/ingest/data_loader.py
python src/features/compute_all.py
python src/personas/assign_all.py
python src/recommend/generate_all.py
```

