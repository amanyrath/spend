# SpendSense Project Summary

## Overview

SpendSense is a financial education platform that analyzes transaction data to deliver personalized, explainable financial guidance. The system uses synthetic transaction data (Plaid-compatible schema) to detect behavioral signals, assign personas, and generate personalized recommendations with clear rationales.

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11-3.12)
- **API Server**: Uvicorn
- **Database**: 
  - SQLite (local development, default)
  - Firebase Firestore (production deployment)
  - Firebase Emulator (local testing)
- **Data Processing**: Pandas 2.2.0+ (for vectorized operations)
- **Testing**: Pytest

### Frontend
- **Consumer UI**: 
  - React 19 + TypeScript
  - Vite (build tool)
  - Tailwind CSS 4.1
  - shadcn/ui components (Radix UI primitives)
  - React Router 7
  - Recharts (data visualization)
- **Operator UI**: HTML/JavaScript with Firebase SDK

### AI/ML Integrations
- **OpenAI API**: GPT-4o-mini for chat responses
- **Guardrails AI**: Response validation and safety checks
  - Toxic language detection
  - Custom prohibited phrases validator
  - Tone validation for financial education

### Deployment
- **Backend**: Vercel (serverless functions)
- **Frontend**: Vercel (static site)
- **Database**: Firebase Firestore (production)

## Key Integrations

### 1. OpenAI Integration
- **Purpose**: AI-powered chat interface for financial questions
- **Model**: GPT-4o-mini (configurable via `OPENAI_MODEL` env var)
- **Features**:
  - Personalized responses based on user's financial data
  - Automatic citation extraction
  - PII sanitization before sending to API
  - Rate limiting (10 messages per minute per user)
- **Location**: `src/chat/service.py`

### 2. Guardrails AI Integration
- **Purpose**: Ensure safe, appropriate responses in financial education context
- **Features**:
  - Toxic language detection (optional, requires hub validators)
  - Custom prohibited phrases validation (judgmental language prevention)
  - Response retry mechanism if validation fails
- **Location**: `src/guardrails/guardrails_ai.py`

### 3. Firebase Integration
- **Purpose**: Production database and local emulator support
- **Features**:
  - Auto-detection of Firebase emulator (checks port 8080)
  - Support for service account JSON (file or environment variable)
  - Firestore collections: users, accounts, transactions, computed_features, persona_assignments, recommendations, chat_logs
- **Database Priority**:
  1. Firebase Emulator (if `FIRESTORE_EMULATOR_HOST` set or port 8080 detected)
  2. Firebase Production (if credentials available)
  3. SQLite (fallback)
- **Location**: `src/database/firestore.py`

### 4. Vercel Integration
- **Purpose**: Serverless deployment
- **Backend**: `api/index.py` wraps FastAPI app for Vercel serverless functions
- **Frontend**: Static site deployment with environment variable configuration
- **Config**: `vercel.json` for routing

## Architecture

### Data Flow
```
Synthetic Data Generation → SQLite → Feature Computation → Persona Assignment → Recommendations → Firebase (optional)
```

### Key Components

1. **Data Ingestion** (`src/ingest/`)
   - `generate_demo_data.py`: Synthetic data generation (200 users, 200 days)
   - `data_loader.py`: Load CSV/JSON into SQLite
   - `push_from_sqlite.py`: Push all data to Firebase
   - `load_from_firebase.py`: Load Firebase data back to SQLite

2. **Feature Computation** (`src/features/`)
   - `signal_detection.py`: Core behavioral signal detection
   - `compute_all.py`: Parallel processing (standard)
   - `compute_all_vectorized.py`: Pandas-based vectorized processing (faster)

3. **Persona Assignment** (`src/personas/`)
   - Hierarchical persona matching (High Utilization, Variable Income, Subscription Heavy, Savings Builder, General Wellness)
   - Match percentage calculations

4. **Recommendations** (`src/recommend/`)
   - Content catalog matching
   - Rationale generation
   - Eligibility checking for partner offers

5. **Guardrails** (`src/guardrails/`)
   - PII detection and sanitization (`data_sanitizer.py`)
   - Tone validation (`guardrails_ai.py`, `tone_validator.py`)

6. **Chat Service** (`src/chat/`)
   - OpenAI integration
   - Citation extraction
   - Context building from user data

7. **API Layer** (`src/api/main.py`)
   - REST endpoints for users, signals, recommendations, transactions, insights, overview, chat
   - Automatic database backend selection (SQLite/Firestore)
   - CORS configured for local and Vercel deployments

8. **Consumer UI** (`consumer_ui/`)
   - React SPA with pages: Overview, Education, Insights, Transactions, Offers
   - API client (`src/lib/api.ts`) with TypeScript types

9. **Operator UI** (`operator_ui/`)
   - HTML-based oversight interface
   - User list and detail views
   - Recommendation audit trail

## Data Schema

### Core Entities
- **Users**: User profiles with synthetic names
- **Accounts**: Checking, savings, credit cards (Plaid-compatible types)
- **Transactions**: Plaid-compatible schema with categories, locations, payment channels
- **Computed Features**: Behavioral signals (subscriptions, credit utilization, savings behavior, income stability)
- **Persona Assignments**: Persona assignments with match percentages
- **Recommendations**: Education content and partner offers with rationales
- **Chat Logs**: Chat interaction history with citations

### Transaction Schema (Plaid-Compatible)
- Categories: JSON array format `["Food and Drink", "Groceries"]` (legacy string support)
- Location data: Address, city, region, postal code, country, lat/lon
- Payment channels: online, in store, other
- ISO currency codes

## API Endpoints

### Core Endpoints
- `GET /api/health` - Health check with database status
- `GET /api/users` - List users with persona and behavior counts (pagination, search, filtering)
- `GET /api/users/{user_id}` - Detailed user information
- `GET /api/users/{user_id}/signals` - Behavioral signals for time window
- `POST /api/users/{user_id}/compute-features` - Compute features for user
- `GET /api/users/{user_id}/recommendations` - Personalized recommendations
- `GET /api/users/{user_id}/transactions` - Transaction history
- `GET /api/users/{user_id}/insights` - Spending insights and charts data
- `GET /api/users/{user_id}/overview` - Financial overview with accounts and health metrics

### Chat Endpoint
- `POST /api/chat` - AI chat with financial questions
  - PII sanitization
  - Guardrails validation
  - Citation extraction
  - Rate limiting

### Operator Endpoints
- `POST /api/users/{user_id}/override` - Override recommendation
- `POST /api/users/{user_id}/flag` - Flag user for review
- `GET /api/users/{user_id}/actions` - Audit log

## Environment Variables

### Required for Production
- `OPENAI_API_KEY`: OpenAI API key for chat feature
- `FIREBASE_SERVICE_ACCOUNT`: JSON string of Firebase service account (Vercel)

### Optional
- `OPENAI_MODEL`: OpenAI model name (default: `gpt-4o-mini`)
- `FIRESTORE_EMULATOR_HOST`: Firebase emulator host (default: `localhost:8080`)
- `USE_FIREBASE_EMULATOR`: Set to `true` to force emulator mode
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to Firebase service account file (local)
- `VITE_API_URL`: Frontend API base URL (default: `http://localhost:8000`)

### Chat Agent Configuration
- `CHAT_MAX_TRANSACTION_WINDOW`: Maximum days for transaction window (default: `180`)
- `CHAT_MAX_TRANSACTIONS`: Maximum transactions per request (default: `100`)
- `CHAT_MAX_CONTEXT_TOKENS`: Maximum tokens for context (default: `2000`)
- `CHAT_ENABLE_AMOUNT_BUCKETING`: Enable amount bucketing for privacy (default: `false`)

## Development Workflow

### Local Development (SQLite-First)
1. Generate synthetic data: `python -m src.ingest.regenerate_data`
2. Compute features: `python src/features/compute_all_vectorized.py`
3. Assign personas: `python src/personas/assign_all.py`
4. Generate recommendations: `python src/recommend/generate_all.py`
5. Start API: `uvicorn src.api.main:app --reload --port 8000`
6. Start Consumer UI: `cd consumer_ui && npm run dev`

### Firebase Emulator Testing
1. Start emulator: `firebase emulators:start --only firestore`
2. Auto-detected on port 8080
3. Push data: `python -m src.ingest.push_from_sqlite`

### Production Deployment
- Backend: Deploy to Vercel (serverless functions)
- Frontend: Deploy to Vercel (static site)
- Database: Firebase Firestore (production)

## Key Features

1. **Behavioral Signal Detection**
   - Subscription detection (recurring merchants)
   - Credit utilization tracking
   - Savings behavior analysis
   - Income stability assessment

2. **Persona-Based Personalization**
   - 5 personas with hierarchical matching
   - Match percentage calculations
   - Explainable assignment rationales

3. **Personalized Recommendations**
   - Education content matching
   - Partner offer eligibility
   - Decision trace logging

4. **AI Chat Interface**
   - Financial question answering
   - PII protection
   - Guardrails validation
   - Citation extraction

5. **Consumer Dashboard**
   - Financial overview
   - Personalized education content
   - Spending insights and charts
   - Transaction history
   - Partner offers

6. **Operator Oversight**
   - User management
   - Recommendation audit trail
   - Override capabilities
   - Flagging system

## Security & Privacy

- PII detection and sanitization before LLM processing
- Guardrails for safe, educational responses
- Rate limiting on chat endpoint
- Audit logging for operator actions
- Secure Firebase authentication (service account)

## Evaluation & Testing

- Automated evaluation metrics (`eval/evaluate.py`)
- Test suite (`tests/`) with pytest
- Emulator testing support (`test_with_emulators.py`)

## Data Generation

- Synthetic data generation using Faker library
- Plaid-compatible transaction schema
- Realistic behavioral patterns
- Configurable user count and date ranges
- Support for CSV and Parquet export formats

## Documentation

Comprehensive documentation in `docs/` directory:
- Schema documentation
- Setup guides
- Deployment guides
- Testing guides
- Security documentation
- Workflow documentation



