# CLAUDE.md - AI Assistant Guide for SpendSense

## Project Overview

SpendSense is a financial education platform that analyzes transaction data to deliver personalized, explainable financial guidance. This document provides essential context for AI assistants working on this codebase.

**Core Concept**: Generate synthetic transaction data → Detect behavioral signals → Assign personas → Generate personalized recommendations → Display in consumer/operator UIs

## Technology Stack

### Backend
- **Language**: Python 3.11-3.12 (avoid 3.14 due to pandas compatibility)
- **Framework**: FastAPI (REST API)
- **Server**: Uvicorn (ASGI server)
- **Database**:
  - SQLite (local development, default)
  - Firebase Firestore (production/Vercel deployment)
  - Firebase Emulator (local testing)
- **Data Processing**: Pandas 2.2.0+ (vectorized operations)
- **AI/Chat**: OpenAI GPT-4o-mini
- **Guardrails**: Guardrails AI (response validation, optional in production)
- **Testing**: pytest

### Frontend
- **Consumer UI**: React 19 + TypeScript + Vite + Tailwind CSS 4.1 + shadcn/ui
- **Operator UI**: Vanilla HTML/JavaScript with Firebase SDK
- **Router**: React Router 7
- **Charts**: Recharts
- **Icons**: Lucide React

### Deployment
- **Platform**: Vercel (serverless functions + static hosting)
- **Backend**: Vercel Serverless Functions (`api/index.py` entry point)
- **Frontend**: Vercel static site deployment
- **Production DB**: Firebase Firestore

## Repository Structure

```
spend/
├── api/                        # Vercel serverless function entry point
│   └── index.py               # Wraps FastAPI app for Vercel
├── consumer_ui/               # React consumer-facing dashboard
│   ├── src/
│   │   ├── components/       # Reusable React components
│   │   ├── pages/            # Page-level components
│   │   ├── lib/              # API client, utilities
│   │   └── App.tsx           # Main React app
│   ├── dist/                 # Build output (gitignored)
│   ├── package.json
│   └── vercel.json           # Frontend deployment config
├── operator_ui/              # Operator oversight interface
│   ├── templates/            # HTML templates
│   └── analytics_app/        # Analytics dashboard (React)
├── src/                      # Python backend source
│   ├── api/                  # FastAPI application
│   │   ├── main.py           # Main FastAPI app (500+ lines)
│   │   ├── auth.py           # JWT authentication
│   │   ├── exceptions.py     # Custom exceptions
│   │   ├── validators.py     # Input validation
│   │   └── rate_limit.py     # Rate limiting logic
│   ├── database/             # Database abstraction layer
│   │   ├── db.py             # SQLite operations (excluded from Vercel)
│   │   └── firestore.py      # Firestore operations (auto-detects emulator)
│   ├── features/             # Behavioral signal detection
│   │   ├── signal_detection.py  # Core signal algorithms
│   │   ├── compute_all.py       # Parallel processing
│   │   └── compute_all_vectorized.py  # Pandas vectorized (faster)
│   ├── personas/             # Persona assignment logic
│   │   ├── assignment.py     # Hierarchical persona matching
│   │   └── assign_all.py     # Batch persona assignment
│   ├── recommend/            # Recommendation engine
│   │   ├── engine.py         # Core recommendation logic
│   │   ├── content_catalog.py  # Education content definitions
│   │   ├── credit_offers.py    # Partner offer definitions
│   │   └── rationale_generator.py  # Rationale generation
│   ├── chat/                 # AI chat service
│   │   ├── service.py        # OpenAI integration
│   │   ├── prompts.py        # System prompts
│   │   └── transaction_analysis.py  # Transaction context building
│   ├── guardrails/           # Safety & validation
│   │   ├── guardrails_ai.py  # Guardrails AI integration (optional)
│   │   ├── tone_validator.py # Tone validation
│   │   └── data_sanitizer.py # PII detection & sanitization
│   ├── ingest/               # Data generation & ETL
│   │   ├── data_generator.py      # Synthetic data generation
│   │   ├── data_loader.py         # Load CSV/JSON to SQLite
│   │   ├── regenerate_data.py     # One-command data refresh
│   │   ├── push_from_sqlite.py    # Push SQLite → Firestore
│   │   └── load_from_firebase.py  # Pull Firestore → SQLite
│   ├── utils/                # Utility functions
│   │   ├── category_utils.py # Transaction category normalization
│   │   ├── calculators.py    # Financial calculations
│   │   └── plaid_categories.py  # Plaid category schema
│   ├── traces/               # Decision tracing (auditability)
│   └── analytics/            # Operator analytics
├── data/                     # Data files (gitignored, generated locally)
│   ├── users.json            # Synthetic user profiles
│   ├── accounts.csv          # Bank accounts
│   ├── transactions.csv      # Transaction history
│   ├── liabilities.csv       # Credit card liabilities
│   └── spendsense.db         # SQLite database
├── tests/                    # Test suite (pytest)
├── docs/                     # Comprehensive documentation
├── eval/                     # Evaluation metrics
├── scripts/                  # Utility scripts
├── requirements.txt          # Minimal deps (Vercel production)
├── requirements-full.txt     # Full deps (local development)
├── vercel.json               # Backend deployment config
└── .vercelignore             # Deployment exclusion list
```

## Critical Files for AI Assistants

### Backend Entry Points
- **`src/api/main.py`**: Main FastAPI application (~500 lines)
  - All REST endpoints
  - Database backend selection (SQLite/Firestore auto-detection)
  - CORS, error handling, rate limiting

- **`api/index.py`**: Vercel serverless wrapper (imports FastAPI app)

### Database Layer
- **`src/database/firestore.py`**: Firebase/Firestore operations
  - Auto-detects Firebase emulator on port 8080
  - Handles both production and emulator modes
  - **IMPORTANT**: Used in Vercel production (SQLite excluded)

- **`src/database/db.py`**: SQLite operations (local only)
  - **EXCLUDED from Vercel** via `.vercelignore`
  - Imports made optional in `src/api/main.py`

### Frontend Entry Points
- **`consumer_ui/src/App.tsx`**: Main React application
- **`consumer_ui/src/lib/api.ts`**: TypeScript API client
- **`consumer_ui/src/pages/`**: Page components (Overview, Education, Insights, Transactions, Offers)

## Database Architecture & Environment Detection

### Automatic Database Selection

The system **automatically detects** which database to use based on environment:

```python
# Priority order (from src/database/firestore.py and src/api/main.py):
1. If USE_SQLITE=true → Force SQLite (highest priority)
2. If FIRESTORE_EMULATOR_HOST set → Use Firebase Emulator
3. If emulator detected on port 8080 → Use Firebase Emulator (auto-detect)
4. If FIREBASE_SERVICE_ACCOUNT or firebase-service-account.json exists → Use Firestore Production
5. Otherwise → Use SQLite (default fallback)
```

### Environment Variables

**Production (Vercel):**
- `FIREBASE_SERVICE_ACCOUNT`: JSON string of service account credentials
- `OPENAI_API_KEY`: OpenAI API key for chat

**Local Development:**
- `USE_SQLITE=true`: Force SQLite even if emulator running
- `FIRESTORE_EMULATOR_HOST`: Firebase emulator host (default: `localhost:8080`)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account file

**Optional Configuration:**
- `OPENAI_MODEL`: Model name (default: `gpt-4o-mini`)
- `VITE_API_URL`: Frontend API base URL (default: `http://localhost:8000`)

### Database Collections/Tables

**Schema (same structure for SQLite and Firestore):**
- `users`: User profiles (user_id, name, email, created_at)
- `accounts`: Bank accounts (account_id, user_id, type, balance)
- `transactions`: Transaction history (Plaid-compatible schema)
- `liabilities`: Credit card liabilities
- `computed_features`: Behavioral signals (subscriptions, credit_util, savings, income)
- `persona_assignments`: Persona assignments with match percentages
- `recommendations`: Education content and partner offers with rationales
- `chat_logs`: Chat interaction history with citations
- `operator_actions`: Audit trail for operator actions
- `user_consents`: User consent records

## Development Workflows

### Initial Setup (First Time)

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install full dependencies (local dev)
pip install -r requirements-full.txt

# 3. Generate synthetic data and load to SQLite
python -m src.ingest.regenerate_data --parquet

# 4. Compute features, assign personas, generate recommendations
python src/features/compute_all_vectorized.py
python src/personas/assign_all.py
python src/recommend/generate_all.py

# 5. Install frontend dependencies
cd consumer_ui
npm install
cd ..
```

### Daily Development Workflow

**Terminal 1 - Backend API:**
```bash
source venv/bin/activate
uvicorn src.api.main:app --reload --port 8000
```

**Terminal 2 - Consumer UI:**
```bash
cd consumer_ui
npm run dev
# Available at http://localhost:5173
```

**Terminal 3 (Optional) - Operator UI:**
```bash
cd operator_ui/templates
python3 -m http.server 8080
# Available at http://localhost:8080/user_list.html
```

### Refreshing Data

```bash
# One command to regenerate all data
python -m src.ingest.regenerate_data --parquet

# Or step by step:
python src/ingest/data_generator.py          # Generate CSV/JSON
python src/ingest/data_loader.py             # Load to SQLite
python src/features/compute_all_vectorized.py # Compute features
python src/personas/assign_all.py            # Assign personas
python src/recommend/generate_all.py         # Generate recommendations
```

### Firebase Emulator Workflow

```bash
# Terminal 1: Start emulator
firebase emulators:start --only firestore
# Auto-detected on port 8080 (no env vars needed!)

# Terminal 2: Push data from SQLite to emulator
python -m src.ingest.push_from_sqlite

# Terminal 3: Start API (automatically uses emulator)
uvicorn src.api.main:app --reload --port 8000
```

### Testing

```bash
# Run test suite
pytest tests/ -v

# Run specific test file
pytest tests/test_persona_assignment.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Vercel Deployment Considerations

### Critical Size Optimization

**Problem**: Vercel serverless functions have a 250 MB unzipped size limit.

**Solution**: The project uses different requirements files:
- `requirements.txt` (minimal, ~80-100 MB) - Used by Vercel
- `requirements-full.txt` (full, ~250+ MB) - Used for local development

### Excluded from Vercel (via `.vercelignore`)

**Heavy modules excluded:**
- `src/database/db.py` (SQLite, not needed - Vercel uses Firestore)
- `src/ingest/data_generator.py` (data generation scripts)
- `src/features/compute_all*.py` (batch computation - run locally)
- `src/personas/assign_all*.py` (batch assignment - run locally)
- `src/recommend/generate_all*.py` (batch generation - run locally)
- All data files, tests, docs, node_modules

**Dependencies excluded from Vercel:**
- `pandas` (~100 MB) - Only needed for batch operations, not API endpoints
- `guardrails-ai` (~40 MB) - Made optional, falls back to basic validation
- `faker` - Only needed for data generation
- `pytest` - Testing only

### What Works on Vercel vs Locally

**✅ Works on Vercel (via API):**
- All GET endpoints (users, signals, recommendations, transactions, insights)
- Chat endpoint (with basic guardrails)
- Single-user persona assignment
- Single-user feature computation
- Authentication & authorization

**❌ Must Run Locally:**
- Batch feature computation (all users)
- Batch persona assignment (all users)
- Batch recommendation generation (all users)
- Data generation and ETL operations
- Vectorized processing with pandas

### Making Code Vercel-Compatible

**Pattern: Optional imports with graceful fallbacks**

```python
# Example from src/api/main.py
try:
    from src.database import db
    from src.database.db import get_db_connection
    HAS_SQLITE = True
except ImportError:
    # SQLite not available - use Firestore only (production deployment)
    HAS_SQLITE = False
    db = None
    get_db_connection = None
```

**Pattern: Conditional execution**

```python
# Check if running on Vercel/serverless
if os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
    # Skip auto-detection to prevent hanging
    return
```

## Code Conventions & Patterns

### Python Backend

**Style:**
- Follow PEP 8
- Use type hints where helpful
- Docstrings for public functions/classes
- Error handling with custom exceptions (`src/api/exceptions.py`)

**Database Abstraction:**
```python
# Good: Use database-agnostic functions
from src.database.firestore import get_user, get_recommendations

# Avoid: Direct database queries in API endpoints
# Instead, use helper functions in database layer
```

**API Endpoint Pattern:**
```python
@app.get("/api/users/{user_id}")
async def get_user_endpoint(user_id: str):
    validate_user_id(user_id)  # Input validation
    user = firestore_get_user(user_id)  # Database call
    if not user:
        raise UserNotFoundError(f"User {user_id} not found")
    return user
```

### React Frontend

**Style:**
- TypeScript for type safety
- Functional components with hooks
- shadcn/ui components for consistency
- Tailwind CSS for styling

**API Client Pattern:**
```typescript
// From consumer_ui/src/lib/api.ts
export async function fetchUserRecommendations(userId: string) {
  const response = await fetch(`${API_BASE_URL}/api/users/${userId}/recommendations`);
  if (!response.ok) throw new Error('Failed to fetch recommendations');
  return response.json();
}
```

**Component Structure:**
```typescript
// Page component example
export function EducationPage() {
  const { userId } = useParams();
  const [recommendations, setRecommendations] = useState([]);

  useEffect(() => {
    // Fetch data
  }, [userId]);

  return (
    // JSX
  );
}
```

### Transaction Schema (Plaid-Compatible)

**Important conventions:**
- Categories: JSON array format `["Food and Drink", "Groceries"]`
- Legacy string format also supported: `"Food and Drink, Groceries"`
- Payment channels: `"online"`, `"in store"`, `"other"`
- Amounts: Positive for debits, negative for credits
- Dates: ISO format `YYYY-MM-DD`

**Example:**
```json
{
  "transaction_id": "txn_001",
  "account_id": "acc_001",
  "amount": 42.50,
  "date": "2024-01-15",
  "name": "WHOLE FOODS",
  "category": ["Food and Drink", "Groceries"],
  "payment_channel": "in store",
  "location": {
    "city": "San Francisco",
    "region": "CA",
    "country": "US"
  }
}
```

## API Endpoints Reference

### Core Endpoints
- `GET /api/health` - Health check with database status
- `GET /api/users` - List users (pagination, search, filtering)
- `GET /api/users/{user_id}` - User details
- `GET /api/users/{user_id}/overview` - Financial overview
- `GET /api/users/{user_id}/signals` - Behavioral signals
- `GET /api/users/{user_id}/recommendations` - Personalized recommendations
- `GET /api/users/{user_id}/transactions` - Transaction history
- `GET /api/users/{user_id}/insights` - Spending insights

### Chat Endpoint
- `POST /api/chat` - AI chat with financial questions
  - Request: `{"user_id": "user_001", "message": "How can I save more?"}`
  - Includes PII sanitization, guardrails, citations
  - Rate limited: 10 messages/minute per user

### Operator Endpoints
- `POST /api/users/{user_id}/override` - Override recommendation
- `POST /api/users/{user_id}/flag` - Flag user for review
- `GET /api/users/{user_id}/actions` - Audit log

## Common Tasks for AI Assistants

### Adding a New API Endpoint

1. Add endpoint to `src/api/main.py`:
```python
@app.get("/api/new-endpoint/{user_id}")
async def new_endpoint(user_id: str):
    validate_user_id(user_id)
    # Implementation
    return {"result": "data"}
```

2. Add validation if needed (`src/api/validators.py`)
3. Add custom exception if needed (`src/api/exceptions.py`)
4. Update frontend API client (`consumer_ui/src/lib/api.ts`)
5. Test locally before deploying

### Adding a New Behavioral Signal

1. Add detection logic in `src/features/signal_detection.py`:
```python
def detect_new_signal(transactions, window_days=30):
    """Detect new behavioral signal."""
    # Implementation
    return {
        'detected': True,
        'confidence': 0.85,
        'details': {...}
    }
```

2. Update `src/features/compute_all.py` to include new signal
3. Update database schema if needed
4. Add tests in `tests/test_signal_detection.py`

### Adding a New Persona

1. Define persona in `src/personas/assignment.py`:
```python
PERSONAS = {
    'new_persona': {
        'name': 'New Persona',
        'criteria': {
            'new_signal_detected': True,
            # More criteria
        }
    }
}
```

2. Add education content in `src/recommend/content_catalog.py`
3. Update persona assignment logic
4. Test with synthetic data

### Modifying Frontend Components

1. Update component in `consumer_ui/src/components/` or `consumer_ui/src/pages/`
2. Use shadcn/ui components for consistency
3. Update TypeScript types if needed
4. Test with hot reload (`npm run dev`)
5. Build before deploying (`npm run build`)

## Security & Privacy Considerations

### PII Protection
- Chat service sanitizes PII before sending to OpenAI (see `src/guardrails/data_sanitizer.py`)
- Detects: names, emails, phone numbers, SSNs, addresses, account numbers
- Replaces with generic placeholders: `[NAME]`, `[EMAIL]`, `[PHONE]`

### Guardrails
- Tone validation for financial education context
- Prohibited phrases detection (judgmental language)
- Response retry mechanism if validation fails
- **Note**: Full guardrails-ai only in local dev; production uses basic validation

### Rate Limiting
- Chat endpoint: 10 messages/minute per user
- Configurable in `src/api/rate_limit.py`
- Returns 429 status code when exceeded

### Authentication
- JWT-based authentication in `src/api/auth.py`
- Operator vs consumer roles
- Not enforced in demo mode (set `DEMO_MODE=true` to skip auth)

## Troubleshooting Common Issues

### "Vercel function too large"
- **Cause**: Dependencies exceed 250 MB
- **Solution**: Already fixed - uses `requirements.txt` (minimal)
- **Verify**: Check `.vercelignore` excludes heavy modules

### "Module not found" on Vercel
- **Cause**: Module excluded from deployment or missing from `requirements.txt`
- **Solution**: Check `.vercelignore` and `requirements.txt`
- **Pattern**: Make imports optional with try/except

### "Database not found" locally
- **Cause**: SQLite database not generated
- **Solution**: Run `python -m src.ingest.regenerate_data`

### Firebase emulator not detected
- **Cause**: Emulator not running or port mismatch
- **Solution**:
  - Start emulator: `firebase emulators:start --only firestore`
  - Verify port 8080 is open
  - Set `FIRESTORE_EMULATOR_HOST=localhost:8080` if auto-detection fails

### Pandas errors on Python 3.14
- **Cause**: Pandas 2.1.3 incompatible with Python 3.14
- **Solution**: Use Python 3.11 or 3.12, or update pandas to 2.2.0+

### Frontend can't connect to API
- **Cause**: CORS or API URL mismatch
- **Solution**:
  - Check `VITE_API_URL` in `consumer_ui/.env`
  - Verify API is running on correct port
  - Check CORS settings in `src/api/main.py`

## Documentation Resources

**Essential docs in `/docs` directory:**
- `schema.md` - Database schema and API documentation
- `WORKFLOW.md` - Complete workflow overview
- `deployment-guide.md` - Vercel + Firebase deployment
- `DATA_METHODOLOGY.md` - Synthetic data generation methodology
- `SECURITY_AND_PII_PROTECTION.md` - Security measures
- `TROUBLESHOOTING.md` - Common issues and solutions

**Root directory docs:**
- `README.md` - Project overview and quick start
- `PROJECT_SUMMARY.md` - Tech stack and architecture
- `VERCEL_FIX_SUMMARY.md` - Vercel optimization details
- `LOCAL_SETUP.md` - Local development setup

## Key Design Decisions

### Why SQLite-First Workflow?
- Fast local development
- No network dependency
- Easy to inspect with DB browser
- Push to Firestore only when ready

### Why Separate requirements.txt Files?
- Vercel has 250 MB size limit
- Batch operations (pandas) not needed in production API
- Guardrails-ai can use fallback validation
- Keeps serverless functions lightweight

### Why Auto-Detect Emulator?
- Seamless local testing
- No manual env var configuration
- Works out of the box after `firebase emulators:start`

### Why Plaid-Compatible Schema?
- Industry standard for transaction data
- Realistic demo data structure
- Easy to understand for financial context

## Git Workflow

### Branch Naming Convention
- Feature branches: `claude/claude-md-<session-id>`
- Always develop on designated feature branch
- Push with: `git push -u origin <branch-name>`

### Commit Guidelines
- Use descriptive commit messages
- Prefix with type: `feat:`, `fix:`, `docs:`, `refactor:`, etc.
- Example: `feat: Add new behavioral signal detection`

### Vercel Deployment
- Backend: Automatic deployment on push to main
- Frontend: Separate Vercel project for `consumer_ui/`
- Environment variables configured in Vercel dashboard

## Performance Optimization Tips

### Backend
- Use vectorized processing for batch operations (`compute_all_vectorized.py`)
- Leverage Firestore batch operations for bulk writes
- Use pagination for large result sets
- Cache frequently accessed data (e.g., user personas)

### Frontend
- Use React.memo for expensive components
- Lazy load routes with React Router
- Optimize images and assets
- Use Vite's code splitting

### Database
- **SQLite**: Create indexes on frequently queried columns
- **Firestore**: Use composite indexes for complex queries
- Batch writes when possible (up to 500 operations)

## Testing Strategy

**Current test coverage:** 22 test functions across 3 files

**Test files:**
- `tests/test_persona_assignment.py` - Persona matching logic
- `tests/test_signal_detection.py` - Behavioral signal detection
- `tests/test_recommendations.py` - Recommendation generation

**Run tests:**
```bash
pytest tests/ -v                    # All tests
pytest tests/test_*.py -v          # Specific test file
pytest tests/ --cov=src            # With coverage
```

## AI Assistant Best Practices

### When Making Changes
1. **Understand the context**: Read related code and documentation
2. **Check both databases**: Ensure changes work with SQLite AND Firestore
3. **Test locally first**: Run full pipeline before deploying
4. **Update documentation**: Keep CLAUDE.md and other docs current
5. **Consider Vercel constraints**: Avoid adding heavy dependencies

### When Debugging
1. **Check logs**: API logs, browser console, network tab
2. **Verify database**: Ensure data exists and is correct structure
3. **Test endpoints**: Use curl or Postman to isolate issues
4. **Check environment**: Verify env vars and database connection

### When Adding Features
1. **Start with backend**: Add API endpoint and database operations
2. **Add validation**: Use validators and custom exceptions
3. **Update frontend**: Add API client function and UI components
4. **Write tests**: Add test coverage for new functionality
5. **Update docs**: Document new features in README or CLAUDE.md

---

**Last Updated**: 2025-11-15
**Project Version**: Active development
**Maintainers**: SpendSense Team

For questions or issues, refer to comprehensive documentation in `/docs` directory or README.md.
