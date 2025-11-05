# SpendSense - Product Requirements Document (Assignment-Focused)

**Version:** 1.0 (Simplified)  
**Date:** November 4, 2025  
**Project:** SpendSense - Financial Education Platform (Platinum Project Submission)  
**Timeline:** 2-3 weeks  
**Team Size:** Individual or small team

---

## Executive Summary

SpendSense is a **local-first financial education system** that analyzes synthetic transaction data to deliver personalized, explainable financial guidance. This is a **demonstration project** focused on the core algorithms and explainability, not a production-ready application.

**Core Value Proposition:**
- Demonstrates behavioral signal detection from transaction data
- Shows persona-based personalization with clear rationales
- Provides operator oversight and auditability
- Validates ethical AI principles (consent, transparency, no shaming)

**Key Simplifications from Production MVP:**
- ❌ No real authentication (pre-loaded demo users)
- ❌ No deployment (runs locally)
- ❌ No background jobs (compute on-demand)
- ❌ No chat widget (focus on core algorithms)
- ✅ Focus: Data → Features → Personas → Recommendations → Evaluation

---

## Project Goals

### Primary Goals
1. **Generate synthetic data** for 50-100 users matching Plaid schema
2. **Detect behavioral signals** (subscriptions, credit, savings, income)
3. **Assign personas** based on hierarchical criteria
4. **Generate recommendations** with plain-language rationales
5. **Build operator view** for oversight and decision traces
6. **Evaluate system** with metrics (coverage, explainability, latency)

### Success Metrics (From Assignment)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Coverage | 100% of users with persona + ≥3 behaviors | Automated |
| Explainability | 100% of recommendations with rationales | Automated |
| Latency | <5s to generate recommendations | Performance test |
| Auditability | 100% of recommendations with decision traces | Code review |
| Code Quality | ≥10 unit/integration tests | Test suite |

---

## User Personas

### Primary User: Operator (Bank Employee)
- **Who:** Compliance officer or customer success manager reviewing the system
- **Goal:** Understand how recommendations are generated and verify appropriateness
- **Needs:** 
  - View all users and their detected signals
  - See persona assignments with explanations
  - Review recommendations with rationales
  - Access decision traces for auditability
  - Override recommendations if needed

### Secondary User: End Consumer (Simulated)
- **Who:** Synthetic banking customer (data only, no UI needed)
- **Representation:** JSON profiles with transaction history
- **Purpose:** Demonstrate system capabilities across diverse financial situations

---

## Core Features

### 1. Synthetic Data Generation

**Purpose:** Create realistic financial data for 50-100 users without real PII

**Requirements:**

**Accounts (per user):**
```json
{
  "account_id": "acc_abc123",
  "type": "depository",
  "subtype": "checking",
  "balances": {
    "available": 1250.00,
    "current": 1250.00,
    "limit": null
  },
  "mask": "4523"
}
```

**Account Types to Generate:**
- Checking accounts (all users)
- Savings accounts (70% of users)
- Credit cards (60% of users)
- High-yield savings (20% of users)
- Money market accounts (10% of users)

**Transactions (per user):**
```json
{
  "transaction_id": "tx_xyz789",
  "account_id": "acc_abc123",
  "date": "2025-10-15",
  "amount": -45.67,
  "merchant_name": "Whole Foods",
  "category": ["Food and Drink", "Groceries"],
  "pending": false
}
```

**Transaction Volume:**
- 150-250 transactions per user over 180 days
- Mix of categories: groceries, restaurants, bills, shopping, subscriptions, payroll

**Liabilities (for credit cards):**
```json
{
  "account_id": "acc_credit123",
  "aprs": [{"apr_percentage": 18.99, "apr_type": "purchase_apr"}],
  "minimum_payment_amount": 50.00,
  "last_payment_amount": 50.00,
  "is_overdue": false,
  "last_statement_balance": 3400.00
}
```

**Diversity Requirements:**
- Income levels: $30K-$150K/year (inferred from deposits)
- Credit behaviors: Low utilization (30%), medium (30%), high (40%)
- Savings patterns: Active savers (25%), minimal savers (50%), no savings (25%)
- Subscription counts: 0-2 (30%), 3-5 (40%), 6+ (30%)

**Implementation:**
- Python script: `generate_synthetic_data.py`
- Use `faker` library for names, no real PII
- Output: `data/users.json`, `data/accounts.csv`, `data/transactions.csv`, `data/liabilities.csv`
- Deterministic with seed for reproducibility

---

### 2. Behavioral Signal Detection

**Purpose:** Extract meaningful patterns from transaction data

**Time Windows:**
- 30-day (short-term, reactive signals)
- 180-day (long-term, trend signals)

#### Signal 1: Subscription Detection

**Logic:**
- Identify recurring merchants: ≥3 occurrences in 90 days
- Cadence detection: Monthly (±3 days) or Weekly (±1 day)
- Amount consistency: Within 10% variance

**Outputs:**
```json
{
  "signal_type": "subscriptions",
  "time_window": "30d",
  "recurring_merchants": [
    {"merchant": "Netflix", "frequency": "monthly", "amount": 15.99},
    {"merchant": "Spotify", "frequency": "monthly", "amount": 10.99}
  ],
  "monthly_recurring_total": 203.00,
  "subscription_share": 0.15
}
```

**Detection Algorithm:**
```python
def detect_subscriptions(transactions, window_days=90):
    # Group by merchant
    # Find merchants with ≥3 occurrences
    # Check if dates form regular pattern (monthly/weekly)
    # Return list of recurring merchants
```

#### Signal 2: Credit Utilization

**Logic:**
- For each credit card: utilization = balance / limit
- Flags: High (≥50%), Medium (30-50%), Low (<30%)
- Minimum payment detection: last_payment ≈ minimum_payment (within $5)
- Interest detection: Check for "Interest Charge" transactions

**Outputs:**
```json
{
  "signal_type": "credit_utilization",
  "time_window": "30d",
  "accounts": [
    {
      "account_id": "acc_credit123",
      "mask": "4523",
      "utilization": 0.68,
      "utilization_flag": "high",
      "minimum_payment_only": true,
      "interest_charged": 87.00,
      "is_overdue": false
    }
  ]
}
```

#### Signal 3: Savings Behavior

**Logic:**
- Identify savings-like accounts (savings, money market, HSA, CDs)
- Net inflow = deposits - withdrawals
- Growth rate = (current_balance - balance_180d_ago) / balance_180d_ago
- Emergency fund coverage = savings_balance / avg_monthly_expenses

**Outputs:**
```json
{
  "signal_type": "savings_behavior",
  "time_window": "180d",
  "total_savings_balance": 8500.00,
  "net_inflow": 200.00,
  "growth_rate": 0.032,
  "emergency_fund_coverage": 3.2,
  "coverage_flag": "good"
}
```

**Coverage Flags:**
- Excellent: ≥6 months
- Good: 3-6 months
- Building: 1-3 months
- Low: <1 month

#### Signal 4: Income Stability

**Logic:**
- Detect payroll deposits: ACH deposits with "PAYROLL" or employer names
- Identify frequency: Weekly, biweekly, semi-monthly, monthly
- Calculate variability: Coefficient of variation of paycheck amounts
- Cash-flow buffer = checking_balance / avg_monthly_expenses

**Outputs:**
```json
{
  "signal_type": "income_stability",
  "time_window": "180d",
  "payroll_frequency": "biweekly",
  "average_paycheck": 1750.00,
  "variability": 0.05,
  "cash_flow_buffer": 0.8,
  "irregular_income": false
}
```

**Implementation:**
- Python module: `features/signal_detection.py`
- Functions: `detect_subscriptions()`, `detect_credit()`, `detect_savings()`, `detect_income()`
- Store results: SQLite table `computed_features` or JSON files

---

### 3. Persona Assignment

**Purpose:** Categorize users based on behavioral signals for targeted education

**Assignment Logic:** Hierarchical (check in priority order, first match wins)

#### Persona 1: High Utilization (Priority 1)

**Criteria:**
```python
ANY of:
- credit_utilization >= 0.50 OR
- interest_charged > 0 OR
- minimum_payment_only == True OR
- is_overdue == True
```

**Primary Focus:**
- Reduce credit utilization
- Understand interest impact
- Payment planning strategies
- Autopay setup education

**Education Topics:**
- "Understanding Credit Utilization"
- "The Real Cost of Minimum Payments"
- "Debt Avalanche vs. Debt Snowball"

#### Persona 2: Variable Income Budgeter (Priority 2)

**Criteria:**
```python
ALL of:
- (median_pay_gap > 45 days OR payroll_frequency == "irregular") AND
- cash_flow_buffer < 1.0 month
```

**Primary Focus:**
- Percentage-based budgeting
- Emergency fund basics
- Income smoothing strategies
- Expense forecasting

**Education Topics:**
- "Budgeting with Irregular Income"
- "Building a Cash-Flow Buffer"
- "The 50/30/20 Rule (Adapted)"

#### Persona 3: Subscription-Heavy (Priority 3)

**Criteria:**
```python
ALL of:
- recurring_merchants >= 3 AND
- (monthly_recurring >= 50 OR subscription_share >= 0.10)
```

**Primary Focus:**
- Subscription audit checklist
- Negotiation tactics
- Cancellation workflows
- Bill alerts setup

**Education Topics:**
- "The $200 Question: Are You Using All Your Subscriptions?"
- "How to Negotiate Lower Bills"
- "Subscription Cancellation Made Easy"

#### Persona 4: Savings Builder (Priority 4)

**Criteria:**
```python
ALL of:
- (savings_growth_rate >= 0.02 OR net_savings_inflow >= 200) AND
- ALL credit_utilization < 0.30
```

**Primary Focus:**
- Goal-setting frameworks
- Savings automation
- HYSA/CD education
- Investment readiness

**Education Topics:**
- "From Savings to Investing: When Are You Ready?"
- "High-Yield Savings Accounts Explained"
- "Setting SMART Financial Goals"

#### Persona 5: General Financial Wellness (Default)

**Criteria:**
```python
# If no other persona criteria met
```

**Primary Focus:**
- Financial literacy basics
- Budgeting fundamentals
- Account management

**Assignment Output:**
```json
{
  "user_id": "user_123",
  "time_window": "30d",
  "persona": "high_utilization",
  "criteria_met": [
    "credit_utilization >= 0.50",
    "interest_charged > 0"
  ],
  "assigned_at": "2025-11-04T10:00:00Z"
}
```

**Implementation:**
- Python module: `personas/assignment.py`
- Function: `assign_persona(signals) -> persona`
- Store results: SQLite table `persona_assignments`

---

### 4. Recommendation Engine

**Purpose:** Generate personalized education content with clear rationales

**Process Flow:**
1. Load user's persona and signals
2. Select 3-5 education items from catalog (matched to persona)
3. Select 1-3 partner offers with eligibility checks
4. Generate rationales citing specific data
5. Apply tone guardrails
6. Store recommendations with decision traces

#### Education Content Catalog

**Structure:**
```json
{
  "content_id": "edu_credit_util_101",
  "type": "education",
  "title": "Understanding Credit Utilization",
  "category": "credit",
  "personas": ["high_utilization"],
  "trigger_signals": ["credit_utilization_high"],
  "summary": "Learn why keeping credit card balances low improves your credit score.",
  "full_content": "Credit utilization is the ratio of your current credit card balances to your credit limits...",
  "rationale_template": "Your {card_name} is at {utilization}% utilization ({balance} of {limit} limit). Bringing this below 30% could improve your credit score."
}
```

**Required Content (15 items minimum):**
- High Utilization: 5 items
- Variable Income: 3 items
- Subscription-Heavy: 4 items
- Savings Builder: 3 items

#### Partner Offers Catalog

**Structure:**
```json
{
  "offer_id": "offer_balance_transfer",
  "type": "partner_offer",
  "title": "0% APR Balance Transfer Card",
  "partner": "Example Bank",
  "summary": "Transfer high-interest balances and save on interest for 18 months.",
  "eligibility_criteria": {
    "credit_utilization": {"min": 0.5},
    "is_overdue": {"equals": false},
    "min_credit_score": 670
  },
  "rationale_template": "You're currently paying ${interest_charged}/month in interest. This card could help you save."
}
```

**Required Offers (8 minimum):**
- Balance Transfer Card
- High-Yield Savings Account
- Budgeting App
- Subscription Management Tool
- Credit Monitoring Service
- Debt Consolidation Loan
- Cashback Credit Card
- Financial Planning Consultation

#### Rationale Generation

**Requirements:**
- Always cite specific data (account numbers, amounts, dates)
- Use plain language, no jargon
- Format: "We're showing you this because [concrete observation]"
- Include actual numbers from user's data

**Example Rationales:**

✅ Good:
> "Your Visa ending in 4523 is at 68% utilization ($3,400 of $5,000 limit). Bringing this below 30% could improve your credit score and reduce interest charges of $87/month."

✅ Good:
> "You have 8 active subscriptions totaling $203/month (15% of your spending). Reviewing these could free up money for your savings goals."

❌ Bad (too generic):
> "High credit utilization can impact your credit score."

❌ Bad (shaming):
> "You're overspending on subscriptions."

**Implementation:**
```python
def generate_rationale(template, user_signals):
    # Extract relevant signals
    # Substitute variables in template
    # Validate tone (no shaming)
    # Return rationale string
```

#### Tone Guardrails

**Prohibited Phrases:**
- "you're overspending"
- "bad habits"
- "poor choices"
- "irresponsible"
- "wasteful"

**Validation:**
```python
def validate_tone(text):
    prohibited = ["overspending", "bad habits", "poor choices"]
    for phrase in prohibited:
        if phrase in text.lower():
            return False
    return True
```

**Preferred Language:**
- "You might consider..."
- "Here's an opportunity to..."
- "Your data shows..."
- "We noticed..."
- "Based on your activity..."

#### Recommendation Output

```json
{
  "recommendation_id": "rec_abc123",
  "user_id": "user_123",
  "type": "education",
  "content_id": "edu_credit_util_101",
  "title": "Understanding Credit Utilization",
  "rationale": "Your Visa ending in 4523 is at 68% utilization ($3,400 of $5,000 limit)...",
  "shown_at": "2025-11-04T10:00:00Z",
  "decision_trace": {
    "persona_match": "high_utilization",
    "signals_used": [
      {"signal": "credit_utilization_visa_4523", "value": 0.68, "threshold": 0.50}
    ],
    "guardrails_passed": {
      "tone_check": true,
      "eligibility_check": true
    }
  }
}
```

**Implementation:**
- Python module: `recommend/engine.py`
- Function: `generate_recommendations(user_id) -> [recommendations]`
- Store results: SQLite table `recommendations`

---

### 5. Operator View

**Purpose:** Human oversight and auditability interface

**Pages:**

#### Page 1: User List

**Layout:**
Simple table with columns:
- User ID
- Name (synthetic)
- Persona (30d)
- # Behaviors Detected
- # Recommendations
- Actions (View Details button)

**Features:**
- Sort by any column
- Search by name or ID
- Filter by persona
- Summary stats at top:
  - Total Users
  - Coverage % (users with persona + ≥3 behaviors)
  - Avg Recommendations per User

**Implementation:**
- Simple HTML table or React DataTable
- Load from SQLite: `SELECT * FROM users JOIN persona_assignments`

#### Page 2: User Detail

**Layout:**
Single-page view with sections:

**Section 1: User Profile**
```
Name: Hannah Martinez
User ID: user_001
Persona (30d): High Utilization
Persona (180d): High Utilization
Behaviors Detected: 5
```

**Section 2: Behavioral Signals**
```
Credit Utilization:
- Visa ****4523: 68% ($3,400 / $5,000)
- Minimum payment only: Yes
- Interest charged: $87/month
- Status: Current

Subscriptions:
- 4 active recurring merchants
- Monthly total: $62
- Share of spend: 8%

Savings:
- Balance: $1,200
- Growth rate: 1.5%
- Coverage: 1.2 months

Income:
- Frequency: Biweekly
- Avg paycheck: $1,750
- Buffer: 0.8 months
```

**Section 3: Recommendations**
Table of recommendations:
- Type | Title | Rationale (truncated) | View Trace

Click "View Trace" → Modal with JSON:
```json
{
  "recommendation_id": "rec_abc123",
  "content_id": "edu_credit_util_101",
  "title": "Understanding Credit Utilization",
  "persona_match": "high_utilization",
  "signals_used": [
    {"signal": "credit_utilization", "value": 0.68}
  ],
  "rationale_generated": "Your Visa ending in 4523...",
  "guardrails": {
    "tone_check": "passed",
    "eligibility": "passed"
  },
  "timestamp": "2025-11-04T10:00:00Z"
}
```

**Section 4: Actions**
- Button: "Override Recommendation" (marks as overridden)
- Button: "Flag for Review" (adds to queue)
- Simple form for operator notes

**Implementation:**
- FastAPI backend: `GET /api/operator/users/{user_id}`
- React frontend or simple HTML template
- Load signals, persona, recommendations from SQLite

---

### 6. Evaluation & Metrics

**Purpose:** Quantify system performance against success criteria

**Metrics to Compute:**

#### Coverage
```python
coverage = (users_with_persona_and_3plus_behaviors / total_users) * 100
# Target: 100%
```

#### Explainability
```python
explainability = (recommendations_with_rationales / total_recommendations) * 100
# Target: 100%
```

#### Latency
```python
# Measure time to generate recommendations per user
import time
start = time.time()
recommendations = generate_recommendations(user_id)
latency = time.time() - start
# Target: <5 seconds per user
```

#### Auditability
```python
auditability = (recommendations_with_decision_traces / total_recommendations) * 100
# Target: 100%
```

**Output Format:**
```json
{
  "evaluation_timestamp": "2025-11-04T12:00:00Z",
  "total_users": 75,
  "metrics": {
    "coverage": {
      "users_with_persona": 75,
      "users_with_3plus_behaviors": 73,
      "percentage": 97.3
    },
    "explainability": {
      "total_recommendations": 285,
      "recommendations_with_rationales": 285,
      "percentage": 100.0
    },
    "latency": {
      "avg_seconds": 2.3,
      "max_seconds": 4.8,
      "p95_seconds": 3.9
    },
    "auditability": {
      "total_recommendations": 285,
      "with_decision_traces": 285,
      "percentage": 100.0
    }
  },
  "persona_distribution": {
    "high_utilization": 32,
    "subscription_heavy": 18,
    "savings_builder": 15,
    "variable_income": 8,
    "general_wellness": 2
  }
}
```

**Implementation:**
- Python script: `eval/evaluate.py`
- Runs on entire dataset
- Outputs: `results/evaluation_report.json`
- Generates: `results/summary.txt` (human-readable)

---

## Technical Architecture

### Stack

**Backend:**
- Python 3.11+
- FastAPI (simple REST API)
- SQLite (local database)
- Pandas (data processing)
- Pytest (testing)

**Frontend (Optional):**
- React + Vite (operator view)
- OR Simple HTML + CSS (faster for demo)
- Recharts (optional, for visualizations)

**Storage:**
- SQLite database: `data/spendsense.db`
- CSV files: `data/*.csv` (for synthetic data)
- JSON files: `results/*.json` (for evaluation)

**No External Services:**
- No authentication
- No deployment
- No cloud services
- No LLM APIs (unless optional for content generation)

### Project Structure

```
spendsense/
├── data/
│   ├── users.json
│   ├── accounts.csv
│   ├── transactions.csv
│   ├── liabilities.csv
│   └── spendsense.db
├── src/
│   ├── ingest/
│   │   ├── __init__.py
│   │   ├── data_generator.py
│   │   └── data_loader.py
│   ├── features/
│   │   ├── __init__.py
│   │   └── signal_detection.py
│   ├── personas/
│   │   ├── __init__.py
│   │   └── assignment.py
│   ├── recommend/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── content_catalog.py
│   │   └── rationale_generator.py
│   ├── guardrails/
│   │   ├── __init__.py
│   │   ├── tone_validator.py
│   │   └── eligibility_checker.py
│   └── api/
│       ├── __init__.py
│       └── main.py
├── operator_ui/
│   ├── src/
│   │   ├── UserList.jsx
│   │   ├── UserDetail.jsx
│   │   └── DecisionTrace.jsx
│   ├── package.json
│   └── vite.config.js
├── eval/
│   ├── evaluate.py
│   └── metrics.py
├── tests/
│   ├── test_signal_detection.py
│   ├── test_persona_assignment.py
│   ├── test_recommendations.py
│   └── test_guardrails.py
├── docs/
│   ├── decision_log.md
│   ├── schema.md
│   └── limitations.md
├── results/
│   ├── evaluation_report.json
│   └── summary.txt
├── requirements.txt
├── README.md
└── run.sh
```

### Database Schema (SQLite)

```sql
-- Users
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    created_at TEXT
);

-- Accounts
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,
    user_id TEXT,
    type TEXT,
    subtype TEXT,
    balance REAL,
    limit REAL,
    mask TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Transactions
CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT,
    user_id TEXT,
    date TEXT,
    amount REAL,
    merchant_name TEXT,
    category TEXT,
    pending INTEGER,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- Computed Features
CREATE TABLE computed_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    time_window TEXT,
    signal_type TEXT,
    signal_data TEXT,  -- JSON
    computed_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Persona Assignments
CREATE TABLE persona_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    time_window TEXT,
    persona TEXT,
    criteria_met TEXT,  -- JSON array
    assigned_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Recommendations
CREATE TABLE recommendations (
    recommendation_id TEXT PRIMARY KEY,
    user_id TEXT,
    type TEXT,
    content_id TEXT,
    title TEXT,
    rationale TEXT,
    decision_trace TEXT,  -- JSON
    shown_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

### API Endpoints (Minimal)

```
GET  /api/health                           # Health check
GET  /api/users                            # List all users
GET  /api/users/{user_id}                  # User profile
GET  /api/users/{user_id}/signals          # Behavioral signals
GET  /api/users/{user_id}/persona          # Persona assignment
GET  /api/users/{user_id}/recommendations  # Generated recommendations
POST /api/evaluate                         # Run evaluation metrics
```

---

## Implementation Timeline (2-3 Weeks)

### Week 1: Data & Features
- **Days 1-2:** Generate synthetic data (50-100 users)
  - Create `data_generator.py`
  - Generate accounts, transactions, liabilities
  - Validate against Plaid schema
  - Output CSV/JSON files
- **Days 3-5:** Build signal detection
  - Implement subscription detection
  - Implement credit utilization
  - Implement savings behavior
  - Implement income stability
  - Write tests for each signal
- **Days 6-7:** Database setup
  - Create SQLite schema
  - Load synthetic data
  - Write data loader scripts

### Week 2: Personas & Recommendations
- **Days 8-9:** Persona assignment
  - Implement hierarchical assignment logic
  - Test on all users
  - Verify coverage
- **Days 10-11:** Content catalog
  - Create 15 education items
  - Create 8 partner offers
  - Write rationale templates
- **Days 12-13:** Recommendation engine
  - Match content to personas
  - Generate rationales with data substitution
  - Implement tone guardrails
  - Create decision traces
- **Day 14:** Testing
  - Write unit tests (aim for 10+)
  - Test edge cases
  - Validate outputs

### Week 3: Operator View & Evaluation
- **Days 15-16:** API
  - Build FastAPI endpoints
  - Test with Postman or curl
- **Days 17-18:** Operator UI
  - User list page
  - User detail page
  - Decision trace viewer
  - (Can be simple HTML if pressed for time)
- **Days 19-20:** Evaluation
  - Implement metrics calculations
  - Run on full dataset
  - Generate report
  - Document limitations
- **Day 21:** Documentation & Polish
  - Write README
  - Decision log
  - Demo video/screenshots
  - Final testing

---

## Testing Requirements

**Minimum 10 Tests:**

1. `test_subscription_detection()` - Detects recurring merchants
2. `test_credit_utilization()` - Calculates utilization correctly
3. `test_savings_behavior()` - Computes growth rate
4. `test_income_stability()` - Identifies payroll pattern
5. `test_persona_high_utilization()` - Assigns correct persona
6. `test_persona_priority()` - Respects hierarchical logic
7. `test_recommendation_generation()` - Generates correct count
8. `test_rationale_substitution()` - Variables replaced correctly
9. `test_tone_validation()` - Catches prohibited phrases
10. `test_decision_trace()` - Trace includes all required fields

**Run tests:**
```bash
pytest tests/ -v
```

---

## Deliverables

### Code Repository
- GitHub repo with clear README
- One-command setup: `pip install -r requirements.txt`
- One-command run: `python src/ingest/data_generator.py && python src/api/main.py`

### Documentation
1. **README.md** - Setup and usage instructions
2. **docs/decision_log.md** - Key design choices and rationale
3. **docs/schema.md** - Database schema documentation
4. **docs/limitations.md** - Known limitations and edge cases

### Evaluation Report
1. **results/evaluation_report.json** - Full metrics
2. **results/summary.txt** - Human-readable summary (1-2 pages)

### Demo
- **Video/Screenshots** showing:
  - Operator viewing user list
  - Drilling into user detail
  - Reviewing behavioral signals
  - Examining recommendations with rationales
  - Viewing decision trace JSON
- OR **Live demo** running locally

---

## Non-Functional Requirements

### Performance
- Recommendation generation: <5 seconds per user
- Evaluation run: <2 minutes for 100 users
- Reasonable on laptop (no GPU needed)

### Code Quality
- Modular structure (clear separation of concerns)
- Type hints in Python functions
- Docstrings for key functions
- ≥10 passing tests
- No hardcoded paths (use relative paths)

### Reproducibility
- Deterministic data generation (use seed)
- Same input → same output
- Document Python version (3.11+)

### Documentation
- Clear README with setup steps
- Decision log explaining key choices
- Comments in complex algorithms
- Schema documentation

---

## Out of Scope

**Not Required for Assignment:**
- ❌ Real Plaid API integration
- ❌ User authentication/login
- ❌ Deployment (Vercel, AWS, etc.)
- ❌ Background jobs/scheduling
- ❌ Chat widget
- ❌ Email notifications
- ❌ Real-time updates
- ❌ Mobile responsiveness (desktop UI is fine)
- ❌ LLM integration (unless optional for content)
- ❌ Complex visualizations (simple charts OK)

---

## Success Checklist