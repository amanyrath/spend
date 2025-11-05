# SpendSense - Complete Task List

**Timeline:** 2-3 weeks  
**Estimated Hours:** 80-100 hours total

---

## Week 1: Data Foundation & Feature Detection (Days 1-7)

### Phase 1.1: Project Setup (Day 1 - 4 hours)

- [ ] **Task 1.1.1:** Create GitHub repository
  - Initialize with README, .gitignore (Python)
  - Create project structure (see below)
  - First commit
  - **Output:** Clean repo structure

- [ ] **Task 1.1.2:** Set up Python environment
  - Create virtual environment: `python -m venv venv`
  - Create `requirements.txt` with: fastapi, uvicorn, pandas, faker, pytest, pydantic
  - Install dependencies: `pip install -r requirements.txt`
  - **Output:** Working Python environment

- [ ] **Task 1.1.3:** Create project directory structure
  ```
  spendsense/
  ├── data/
  ├── src/
  │   ├── ingest/
  │   ├── features/
  │   ├── personas/
  │   ├── recommend/
  │   ├── guardrails/
  │   └── api/
  ├── operator_ui/
  ├── eval/
  ├── tests/
  ├── docs/
  └── results/
  ```
  - **Output:** Complete folder structure

- [ ] **Task 1.1.4:** Create SQLite database schema
  - Create `src/database/schema.sql`
  - Define tables: users, accounts, transactions, computed_features, persona_assignments, recommendations
  - Create `src/database/db.py` with connection helper
  - **Output:** SQLite database initialized

---

### Phase 1.2: Synthetic Data Generation (Days 2-3 - 12 hours)

- [ ] **Task 1.2.1:** Create user generator
  - File: `src/ingest/data_generator.py`
  - Function: `generate_users(count=75)`
  - Use faker library for names (no real PII)
  - Assign varied income levels ($30K-$150K)
  - **Output:** 75 synthetic user profiles

- [ ] **Task 1.2.2:** Create account generator
  - Function: `generate_accounts(user_id)`
  - Per user: 1 checking (always), 0-1 savings (70%), 0-2 credit cards (60%)
  - Realistic balances and credit limits
  - Account masks (last 4 digits)
  - **Output:** Accounts for all users

- [ ] **Task 1.2.3:** Create transaction generator
  - Function: `generate_transactions(account_id, days=180)`
  - 150-250 transactions per user over 180 days
  - Categories: groceries, restaurants, bills, shopping, entertainment
  - Recurring patterns for subscriptions (Netflix, Spotify, etc.)
  - Payroll deposits (ACH, biweekly/monthly)
  - **Output:** Realistic transaction history

- [ ] **Task 1.2.4:** Create liability data generator
  - Function: `generate_liabilities(credit_accounts)`
  - APRs, minimum payments, last payment amounts
  - Interest charges as transactions
  - Overdue status (10% of users)
  - **Output:** Credit card liability data

- [ ] **Task 1.2.5:** Create diversity in financial situations
  - 30% low utilization (<30%)
  - 30% medium utilization (30-50%)
  - 40% high utilization (≥50%)
  - 25% active savers, 50% minimal savers, 25% no savings
  - Vary subscription counts: 0-2, 3-5, 6+ subscriptions
  - **Output:** Diverse user profiles

- [ ] **Task 1.2.6:** Export data to files
  - Save to: `data/users.json`, `data/accounts.csv`, `data/transactions.csv`, `data/liabilities.csv`
  - Validate Plaid-style schema
  - Add deterministic seed for reproducibility
  - **Output:** Data files ready to load

- [ ] **Task 1.2.7:** Create data loader script
  - File: `src/ingest/data_loader.py`
  - Function: `load_data_to_db()`
  - Read CSV/JSON files
  - Insert into SQLite database
  - Handle duplicates (idempotent)
  - **Output:** Data loaded into database

---

### Phase 1.3: Signal Detection Implementation (Days 3-5 - 16 hours)

- [ ] **Task 1.3.1:** Create signal detection module structure
  - File: `src/features/signal_detection.py`
  - Base class or shared utilities
  - Helper functions for date math
  - **Output:** Module skeleton

- [ ] **Task 1.3.2:** Implement subscription detection
  - Function: `detect_subscriptions(user_id, window_days=90)`
  - Logic:
    - Group transactions by merchant
    - Find merchants with ≥3 occurrences
    - Check for regular cadence (monthly ±3 days, weekly ±1 day)
    - Calculate monthly recurring total
    - Calculate subscription share of total spend
  - **Output:** Subscription signals for each user

- [ ] **Task 1.3.3:** Implement credit utilization detection
  - Function: `detect_credit_utilization(user_id, window_days=30)`
  - Logic:
    - For each credit account: utilization = balance / limit
    - Flag: high (≥50%), medium (30-50%), low (<30%)
    - Detect minimum payment only (last_payment ≈ minimum_payment within $5)
    - Sum interest charges from transactions
    - Check overdue status from liabilities
  - **Output:** Credit signals for each user

- [ ] **Task 1.3.4:** Implement savings behavior detection
  - Function: `detect_savings_behavior(user_id, window_days=180)`
  - Logic:
    - Identify savings accounts (type = savings, money market, HSA)
    - Calculate net inflow (deposits - withdrawals)
    - Calculate growth rate: (current - 180d_ago) / 180d_ago
    - Calculate emergency fund coverage: savings / avg_monthly_expenses
    - Assign coverage flag: excellent/good/building/low
  - **Output:** Savings signals for each user

- [ ] **Task 1.3.5:** Implement income stability detection
  - Function: `detect_income_stability(user_id, window_days=180)`
  - Logic:
    - Find payroll deposits (ACH with "PAYROLL" or employer names)
    - Identify frequency (weekly, biweekly, monthly)
    - Calculate variability (coefficient of variation)
    - Calculate cash-flow buffer: checking_balance / avg_monthly_expenses
  - **Output:** Income signals for each user

- [ ] **Task 1.3.6:** Create compute features pipeline
  - Function: `compute_all_features(user_id)`
  - Call all detection functions
  - Store results in `computed_features` table
  - Compute for both 30d and 180d windows
  - **Output:** All signals computed and stored

- [ ] **Task 1.3.7:** Write tests for signal detection
  - File: `tests/test_signal_detection.py`
  - Test: `test_subscription_detection()` - Detects Netflix recurring monthly
  - Test: `test_credit_utilization()` - Calculates 68% correctly
  - Test: `test_savings_behavior()` - Computes growth rate
  - Test: `test_income_stability()` - Identifies biweekly payroll
  - **Output:** 4 passing tests

---

### Phase 1.4: Database Integration (Days 6-7 - 8 hours)

- [ ] **Task 1.4.1:** Create database helpers
  - File: `src/database/db.py`
  - Functions: `get_connection()`, `execute_query()`, `fetch_one()`, `fetch_all()`
  - Context manager for connections
  - **Output:** Reusable DB utilities

- [ ] **Task 1.4.2:** Create feature storage functions
  - Function: `store_feature(user_id, signal_type, signal_data, time_window)`
  - Insert into `computed_features` table
  - Handle JSON serialization
  - **Output:** Features persisted

- [ ] **Task 1.4.3:** Create feature retrieval functions
  - Function: `get_user_features(user_id, time_window)`
  - Query `computed_features` table
  - Parse JSON data
  - **Output:** Features retrieved for use

- [ ] **Task 1.4.4:** Run feature computation for all users
  - Script: `python src/features/compute_all.py`
  - Loop through all users
  - Compute and store features
  - Log progress
  - **Output:** Database populated with signals

---

## Week 2: Personas & Recommendations (Days 8-14)

### Phase 2.1: Persona Assignment (Days 8-9 - 10 hours)

- [ ] **Task 2.1.1:** Create persona assignment module
  - File: `src/personas/assignment.py`
  - Define persona criteria as constants
  - **Output:** Module structure

- [ ] **Task 2.1.2:** Implement High Utilization persona check
  - Function: `check_high_utilization(signals) -> bool`
  - Criteria: credit_utilization ≥ 0.50 OR interest_charged > 0 OR minimum_payment_only OR is_overdue
  - **Output:** Boolean check

- [ ] **Task 2.1.3:** Implement Variable Income persona check
  - Function: `check_variable_income(signals) -> bool`
  - Criteria: (median_pay_gap > 45 days OR irregular_frequency) AND cash_flow_buffer < 1.0
  - **Output:** Boolean check

- [ ] **Task 2.1.4:** Implement Subscription-Heavy persona check
  - Function: `check_subscription_heavy(signals) -> bool`
  - Criteria: recurring_merchants ≥ 3 AND (monthly_recurring ≥ 50 OR subscription_share ≥ 0.10)
  - **Output:** Boolean check

- [ ] **Task 2.1.5:** Implement Savings Builder persona check
  - Function: `check_savings_builder(signals) -> bool`
  - Criteria: (savings_growth_rate ≥ 0.02 OR net_savings_inflow ≥ 200) AND all_credit_utilization < 0.30
  - **Output:** Boolean check

- [ ] **Task 2.1.6:** Implement hierarchical persona assignment
  - Function: `assign_persona(user_id, time_window) -> persona_name`
  - Check personas in priority order (1-4)
  - First match wins
  - Default: "general_wellness"
  - Store in `persona_assignments` table
  - **Output:** Persona assigned

- [ ] **Task 2.1.7:** Assign personas to all users
  - Script: `python src/personas/assign_all.py`
  - Loop through all users
  - Assign for both 30d and 180d windows
  - **Output:** All users have personas

- [ ] **Task 2.1.8:** Write tests for persona assignment
  - File: `tests/test_persona_assignment.py`
  - Test: `test_high_utilization_assignment()` - User with 68% utilization gets correct persona
  - Test: `test_persona_priority()` - High utilization takes precedence over subscription-heavy
  - Test: `test_default_persona()` - User with no criteria gets general_wellness
  - **Output:** 3 passing tests

---

### Phase 2.2: Content Catalog (Days 10-11 - 10 hours)

- [ ] **Task 2.2.1:** Create content catalog structure
  - File: `src/recommend/content_catalog.py`
  - Data structure: List of dicts or JSON file
  - **Output:** Catalog structure defined

- [ ] **Task 2.2.2:** Create education content items
  - 5 items for High Utilization:
    - "Understanding Credit Utilization"
    - "The Real Cost of Minimum Payments"
    - "Debt Avalanche vs. Debt Snowball"
    - "How to Set Up Autopay"
    - "Building a Debt Paydown Plan"
  - 3 items for Variable Income:
    - "Budgeting with Irregular Income"
    - "Building a Cash-Flow Buffer"
    - "The 50/30/20 Rule (Adapted)"
  - 4 items for Subscription-Heavy:
    - "The $200 Question: Are You Using All Your Subscriptions?"
    - "How to Negotiate Lower Bills"
    - "Subscription Cancellation Made Easy"
    - "Setting Up Bill Alerts"
  - 3 items for Savings Builder:
    - "From Savings to Investing: When Are You Ready?"
    - "High-Yield Savings Accounts Explained"
    - "Setting SMART Financial Goals"
  - Each item includes: id, title, category, personas, trigger_signals, summary, full_content, rationale_template
  - **Output:** 15 education items

- [ ] **Task 2.2.3:** Create partner offer items
  - 8 offers:
    - Balance Transfer Credit Card (0% APR)
    - High-Yield Savings Account (4.5% APY)
    - Budgeting App (Mint alternative)
    - Subscription Management Tool
    - Credit Monitoring Service
    - Financial Planning Consultation
    - Debt Consolidation Loan
    - Cashback Credit Card
  - Each offer includes: id, title, partner, summary, eligibility_criteria, rationale_template
  - **Output:** 8 partner offers

- [ ] **Task 2.2.4:** Create rationale templates
  - Templates with variables: {card_name}, {utilization}, {balance}, {limit}, {interest_charged}
  - Example: "Your {card_name} is at {utilization}% utilization ({balance} of {limit} limit)..."
  - **Output:** Templates for all content

- [ ] **Task 2.2.5:** Save content catalog
  - Save to: `src/recommend/catalog.json` or hardcode in Python
  - Validate structure
  - **Output:** Complete content catalog

---

### Phase 2.3: Recommendation Engine (Days 12-13 - 12 hours)

- [ ] **Task 2.3.1:** Create recommendation engine module
  - File: `src/recommend/engine.py`
  - Load content catalog
  - **Output:** Engine skeleton

- [ ] **Task 2.3.2:** Implement content matching
  - Function: `match_education_content(persona, signals) -> [content_ids]`
  - Filter catalog by persona match
  - Filter by trigger signals
  - Return 3-5 items
  - **Output:** Matched content list

- [ ] **Task 2.3.3:** Implement offer matching with eligibility
  - Function: `match_offers(signals) -> [offer_ids]`
  - Check eligibility criteria (credit_utilization, overdue status, etc.)
  - Filter out ineligible offers
  - Return 1-3 offers
  - **Output:** Eligible offers list

- [ ] **Task 2.3.4:** Create rationale generator
  - File: `src/recommend/rationale_generator.py`
  - Function: `generate_rationale(template, signals) -> rationale_text`
  - Extract relevant signal values
  - Substitute variables in template
  - Format numbers (currency, percentages)
  - **Output:** Personalized rationale

- [ ] **Task 2.3.5:** Implement tone guardrails
  - File: `src/guardrails/tone_validator.py`
  - Function: `validate_tone(text) -> bool`
  - Prohibited phrases list: ["overspending", "bad habits", "poor choices", "irresponsible", "wasteful"]
  - Check if any prohibited phrase in text
  - **Output:** Tone validation

- [ ] **Task 2.3.6:** Create decision trace generator
  - Function: `create_decision_trace(recommendation, signals, persona) -> trace_json`
  - Include: persona_match, signals_used, guardrails_passed, timestamp
  - Format as JSON
  - **Output:** Decision trace object

- [ ] **Task 2.3.7:** Implement main recommendation function
  - Function: `generate_recommendations(user_id) -> [recommendations]`
  - Load user persona and signals
  - Match education content
  - Match partner offers
  - Generate rationales for each
  - Validate tone
  - Create decision traces
  - Store in `recommendations` table
  - **Output:** Complete recommendations

- [ ] **Task 2.3.8:** Generate recommendations for all users
  - Script: `python src/recommend/generate_all.py`
  - Loop through all users
  - Generate and store recommendations
  - **Output:** All users have recommendations

- [ ] **Task 2.3.9:** Write tests for recommendations
  - File: `tests/test_recommendations.py`
  - Test: `test_recommendation_count()` - Generates 3-5 education + 1-3 offers
  - Test: `test_rationale_substitution()` - Variables replaced with actual data
  - Test: `test_tone_validation()` - Catches prohibited phrase "overspending"
  - Test: `test_decision_trace_structure()` - Trace has all required fields
  - **Output:** 4 passing tests

---

### Phase 2.4: Testing & Validation (Day 14 - 6 hours)

- [ ] **Task 2.4.1:** Run full test suite
  - Command: `pytest tests/ -v`
  - Fix any failing tests
  - Aim for ≥10 tests passing
  - **Output:** All tests green

- [ ] **Task 2.4.2:** Manual validation
  - Check 5 random users in database
  - Verify signals detected correctly
  - Verify persona assignment makes sense
  - Verify recommendations are relevant
  - Verify rationales cite actual data
  - **Output:** Spot-checked users look good

- [ ] **Task 2.4.3:** Write additional tests if needed
  - Test edge cases
  - Test users with no behaviors
  - Test users with multiple personas matching
  - **Output:** Edge cases covered

---

## Week 3: API, UI & Evaluation (Days 15-21)

### Phase 3.1: API Development (Days 15-16 - 10 hours)

- [ ] **Task 3.1.1:** Set up FastAPI application
  - File: `src/api/main.py`
  - Initialize FastAPI app
  - Add CORS middleware
  - **Output:** Basic API running

- [ ] **Task 3.1.2:** Create health check endpoint
  - Endpoint: `GET /api/health`
  - Return: `{"status": "ok", "timestamp": "..."}`
  - **Output:** Health endpoint working

- [ ] **Task 3.1.3:** Create user list endpoint
  - Endpoint: `GET /api/users`
  - Query all users from database
  - Include: user_id, name, persona_30d, behavior_count
  - **Output:** User list JSON

- [ ] **Task 3.1.4:** Create user detail endpoint
  - Endpoint: `GET /api/users/{user_id}`
  - Return: profile, persona assignments (30d, 180d)
  - **Output:** User detail JSON

- [ ] **Task 3.1.5:** Create signals endpoint
  - Endpoint: `GET /api/users/{user_id}/signals`
  - Query `computed_features` table
  - Parse and format JSON
  - **Output:** All signals for user

- [ ] **Task 3.1.6:** Create recommendations endpoint
  - Endpoint: `GET /api/users/{user_id}/recommendations`
  - Query `recommendations` table
  - Include decision traces
  - **Output:** Recommendations with traces

- [ ] **Task 3.1.7:** Test API with curl or Postman
  - Test all endpoints
  - Verify JSON responses
  - Check error handling (404 for invalid user_id)
  - **Output:** API fully functional

---

### Phase 3.2: Operator UI (Days 17-18 - 12 hours)

**Option A: Simple HTML (Faster)**

- [ ] **Task 3.2.1:** Create HTML templates folder
  - Folder: `operator_ui/templates/`
  - Use Jinja2 or plain HTML + vanilla JS
  - **Output:** Templates folder

- [ ] **Task 3.2.2:** Create user list page
  - File: `operator_ui/templates/user_list.html`
  - Fetch from `/api/users`
  - Display table with columns: Name, Persona, # Behaviors, Actions
  - Add search/filter (basic)
  - **Output:** User list page

- [ ] **Task 3.2.3:** Create user detail page
  - File: `operator_ui/templates/user_detail.html`
  - Fetch from `/api/users/{user_id}`, `/api/users/{user_id}/signals`, `/api/users/{user_id}/recommendations`
  - Display 4 sections: Profile, Signals, Recommendations, Actions
  - **Output:** User detail page

- [ ] **Task 3.2.4:** Create decision trace modal
  - Component: Modal popup with JSON viewer
  - Syntax highlighting (optional: use highlight.js)
  - Copy-to-clipboard button
  - **Output:** Trace viewer

- [ ] **Task 3.2.5:** Add basic styling
  - Use simple CSS or Tailwind CDN
  - Make it readable, doesn't need to be fancy
  - **Output:** Styled pages

**Option B: React (More Polished)**

- [ ] **Task 3.2.1:** Initialize React project
  - Command: `npm create vite@latest operator_ui -- --template react`
  - Install dependencies: react-router-dom, axios
  - **Output:** React project

- [ ] **Task 3.2.2:** Create UserList component
  - File: `operator_ui/src/UserList.jsx`
  - Fetch from `/api/users`
  - Display table with React Table or simple HTML table
  - **Output:** User list component

- [ ] **Task 3.2.3:** Create UserDetail component
  - File: `operator_ui/src/UserDetail.jsx`
  - Fetch user data, signals, recommendations
  - Display 4 sections
  - **Output:** User detail component

- [ ] **Task 3.2.4:** Create DecisionTrace component
  - File: `operator_ui/src/DecisionTrace.jsx`
  - Modal with JSON display
  - Use react-json-view or similar
  - **Output:** Trace viewer component

- [ ] **Task 3.2.5:** Set up routing
  - Routes: `/` (user list), `/users/:userId` (user detail)
  - **Output:** Navigation working

- [ ] **Task 3.2.6:** Add basic styling
  - Use Tailwind CSS or plain CSS
  - **Output:** Styled UI

---

### Phase 3.3: Evaluation & Metrics (Days 19-20 - 10 hours)

- [ ] **Task 3.3.1:** Create evaluation module
  - File: `eval/evaluate.py`
  - Load all users from database
  - **Output:** Evaluation skeleton

- [ ] **Task 3.3.2:** Implement coverage metric
  - Function: `calculate_coverage()`
  - Count users with persona
  - Count users with ≥3 behaviors
  - Calculate percentage
  - **Output:** Coverage metric

- [ ] **Task 3.3.3:** Implement explainability metric
  - Function: `calculate_explainability()`
  - Count total recommendations
  - Count recommendations with rationales
  - Calculate percentage
  - **Output:** Explainability metric

- [ ] **Task 3.3.4:** Implement latency metric
  - Function: `measure_latency()`
  - Time `generate_recommendations()` for each user
  - Calculate avg, max, p95
  - **Output:** Latency metrics

- [ ] **Task 3.3.5:** Implement auditability metric
  - Function: `calculate_auditability()`
  - Count recommendations with decision traces
  - Calculate percentage
  - **Output:** Auditability metric

- [ ] **Task 3.3.6:** Calculate persona distribution
  - Count users per persona
  - **Output:** Distribution stats

- [ ] **Task 3.3.7:** Generate evaluation report
  - Output: `results/evaluation_report.json`
  - Include all metrics
  - Timestamp
  - **Output:** JSON report

- [ ] **Task 3.3.8:** Generate human-readable summary
  - Output: `results/summary.txt`
  - 1-2 pages with key findings
  - Formatted nicely
  - **Output:** Text summary

- [ ] **Task 3.3.9:** Run evaluation on full dataset
  - Command: `python eval/evaluate.py`
  - Verify metrics meet targets
  - **Output:** Evaluation complete

---

### Phase 3.4: Documentation & Polish (Day 21 - 8 hours)

- [ ] **Task 3.4.1:** Write comprehensive README
  - File: `README.md`
  - Sections: Overview, Setup, Usage, Architecture, Metrics
  - One-command setup instructions
  - One-command run instructions
  - **Output:** Clear README

- [ ] **Task 3.4.2:** Write decision log
  - File: `docs/decision_log.md`
  - Document key design choices:
    - Why hierarchical persona assignment?
    - How were rationale templates chosen?
    - Trade-offs in signal detection algorithms
  - **Output:** Decision log

- [ ] **Task 3.4.3:** Write schema documentation
  - File: `docs/schema.md`
  - Document all database tables
  - Document data structures
  - Document API response formats
  - **Output:** Schema docs

- [ ] **Task 3.4.4:** Write limitations document
  - File: `docs/limitations.md`
  - Known edge cases
  - Simplifications made
  - Future improvements
  - **Output:** Limitations doc

- [ ] **Task 3.4.5:** Create demo video or screenshots
  - Screen recording or screenshots showing:
    - Operator viewing user list
    - Drilling into user detail
    - Viewing signals
    - Reviewing recommendations
    - Examining decision trace
  - 3-5 minutes max
  - **Output:** Demo video/screenshots

- [ ] **Task 3.4.6:** Final code cleanup
  - Remove debug print statements
  - Add docstrings to key functions
  - Format code (black, autopep8)
  - **Output:** Clean codebase

- [ ] **Task 3.4.7:** Run final tests
  - Command: `pytest tests/ -v`
  - All tests passing
  - **Output:** Test report

- [ ] **Task 3.4.8:** Verify deliverables checklist
  - [ ] Code repository with clear README
  - [ ] One-command setup works
  - [ ] One-command run works
  - [ ] ≥10 tests passing
  - [ ] Evaluation report generated
  - [ ] Summary document written
  - [ ] Decision log complete
  - [ ] Demo video/screenshots ready
  - **Output:** All deliverables ready

---

## Priority Tasks (Must-Have for Submission)

### Critical Path (Cannot skip):
1. ✅ Synthetic data generation (Tasks 1.2.1-1.2.7)
2. ✅ Signal detection (Tasks 1.3.2-1.3.5)
3. ✅ Persona assignment (Tasks 2.1.2-2.1.6)
4. ✅ Recommendation engine (Tasks 2.3.1-2.3.7)
5. ✅ Evaluation metrics (Tasks 3.3.1-3.3.9)
6. ✅ Basic operator view (Tasks 3.2.1-3.2.4)
7. ✅ Documentation (Tasks 3.4.1-3.4.4)

### Nice-to-Have (Can simplify if time-constrained):
- React UI (use simple HTML instead)
- Extensive testing (aim for 10, not 20)
- Demo video (screenshots are OK)
- Advanced visualizations

---

## Time Estimates by Phase

| Phase | Hours | Days |
|-------|-------|------|
| 1.1 Project Setup | 4 | 0.5 |
| 1.2 Data Generation | 12 | 1.5 |
| 1.3 Signal Detection | 16 | 2 |
| 1.4 Database Integration | 8 | 1 |
| 2.1 Persona Assignment | 10 | 1.25 |
| 2.2 Content Catalog | 10 | 1.25 |
| 2.3 Recommendation Engine | 12 | 1.5 |
| 2.4 Testing | 6 | 0.75 |
| 3.1 API Development | 10 | 1.25 |
| 3.2 Operator UI | 12 | 1.5 |
| 3.3 Evaluation | 10 | 1.25 |
| 3.4 Documentation | 8 | 1 |
| **Total** | **118 hours** | **~15 days** |

**Note:** Assumes ~8 hours/day of focused work. Can be compressed to 2 weeks with longer days or simplified UI.

---

## Quick Start Commands

```bash
# Day 1: Setup
git clone <your-repo>
cd spendsense
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Day 2-3: Generate data
python src/ingest/data_generator.py
python src/ingest/data_loader.py

# Day 4-7: Compute features
python src/features/compute_all.py

# Day 8-9: Assign personas
python src/personas/assign_all.py

# Day 12-13: Generate recommendations
python src/recommend/generate_all.py

# Day 14: Run tests
pytest tests/ -v

# Day 15-16: Start API
uvicorn src.api.main:app --reload

# Day 17-18: Start UI
cd operator_ui
npm run dev

# Day 19-20: Run evaluation
python eval/evaluate.py
```

---

## Success Checklist (Final Submission)

- [ ] Code repository on GitHub
- [ ] README with setup instructions
- [ ] One-command setup: `pip install -r requirements.txt`
- [ ] One-command run: `python run.py` or similar
- [ ] Synthetic data for 50-100 users generated
- [ ] All 4 signal types detected
- [ ] Personas assigned to all users
- [ ] Recommendations generated with rationales
- [ ] Decision traces created for all recommendations
- [ ] ≥10 tests passing
- [ ] Operator UI functional (user list + detail)
- [ ] Evaluation report with metrics
- [ ] Summary document (1-2 pages)
- [ ] Decision log explaining key choices
- [ ] Demo video or screenshots
- [ ] All metrics meet targets:
  - [ ] Coverage: 100%
  - [ ] Explainability: 100%
  - [ ] Latency: <5s per user
  - [ ] Auditability: 100%
  - [ ] Tests: ≥10 passing

---

**Ready to start? Begin with Task 1.1.1!**