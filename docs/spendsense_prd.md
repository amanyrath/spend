# SpendSense MVP - Product Requirements Document

**Version:** 1.0  
**Date:** November 3, 2025  
**Project:** SpendSense - Financial Education Platform  
**Contact:** Bryce Harris - bharris@peak6.com

---

## Executive Summary

SpendSense is a web-based financial education platform that analyzes user transaction data to deliver personalized, explainable financial guidance without crossing into regulated financial advice. The MVP demonstrates the complete user journey for both consumers and bank operators with production-grade authentication, deployment, and data privacy controls.

**Core Value Proposition:**
- Consumers receive personalized financial education based on their actual spending patterns
- Operators gain full auditability and oversight of all recommendations
- Every recommendation includes clear rationales citing specific data points
- System respects user consent and maintains strict ethical guardrails

---

## Goals & Success Metrics

### Primary Goals
1. Demonstrate explainable AI for financial education
2. Showcase production-ready auth and deployment
3. Prove end-to-end traceability for operator oversight
4. Validate ethical AI principles (consent, transparency, no shaming)

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Coverage | 100% of users with persona + ≥3 behaviors | Automated |
| Explainability | 100% of recommendations with rationales | Automated |
| Latency | <5s to generate recommendations | Performance test |
| Auditability | 100% of recommendations with decision traces | Code review |
| User Consent | 100% consent before data access | Auth flow test |

---

## User Personas

### Primary Users

**1. Consumer (End User)**
- **Who:** Banking customer who connects their accounts
- **Goal:** Understand their financial habits and learn how to improve
- **Pain Points:** Overwhelmed by generic financial advice, unclear why they're seeing certain content
- **Needs:** Personalized, non-judgmental guidance that explains the "why"

**2. Operator (Bank Employee)**
- **Who:** Compliance officer or customer success manager
- **Goal:** Ensure recommendations are accurate, appropriate, and auditable
- **Pain Points:** Black-box AI systems, inability to trace decisions
- **Needs:** Full visibility into behavioral signals, decision logic, and override capability

---

## Core Features

### 1. Authentication & Authorization

**Requirements:**
- Real authentication via Supabase Auth
- Role-based access control (consumer vs operator)
- Pre-seeded demo accounts for testing
- Session management and token refresh

**User Flows:**

**Consumer Login:**
1. User navigates to app
2. Enters email/password
3. If first login → consent modal appears
4. User must grant consent before accessing dashboard
5. Redirects to consumer dashboard

**Operator Login:**
1. User navigates to app
2. Enters email/password with operator role
3. Redirects to operator user list
4. No consent required (viewing aggregated data)

**Demo Accounts:**
- `hannah@demo.com` / `demo123` (Consumer - High Utilization persona)
- `sam@demo.com` / `demo123` (Consumer - Subscription-Heavy persona)
- `operator@demo.com` / `demo123` (Operator access)

**Technical Details:**
- Supabase Auth with JWT tokens
- Row-Level Security (RLS) policies enforce data access
- Consent tracked in `consent_records` table with timestamps
- IP address logging for consent audit trail

---

### 2. Consumer Dashboard

**Layout:**
4-tab navigation with persistent chat widget

#### Tab 1: Transactions

**Purpose:** Allow users to review their spending history

**Features:**
- Table view with columns:
  - Date
  - Merchant Name
  - Amount (color-coded: red for debit, green for credit)
  - Category (with icon)
  - Account (last 4 digits)
- Filters:
  - Date range (30/90 days)
  - Category dropdown
  - Search by merchant name
- Sort by date (default: newest first) or amount
- Pagination (50 transactions per page)

**Edge Cases:**
- Empty state: "No transactions found for this filter"
- Pending transactions marked with badge
- Large amounts (>$1000) highlighted

---

#### Tab 2: Insights 🌟 *Showcase Feature*

**Purpose:** Visualize spending patterns and key financial metrics

**Features:**

**Chart 1: Monthly Spending by Category**
- Type: Horizontal bar chart
- X-axis: Amount ($)
- Y-axis: Categories (Food & Drink, Shopping, Bills, etc.)
- Time period toggle: 30d / 90d
- Hover: Show exact amount + % of total

**Chart 2: Credit Utilization Trend**
- Type: Line chart
- X-axis: Date (weekly buckets)
- Y-axis: Utilization % (0-100%)
- Reference lines: 30% (green), 50% (yellow), 80% (red)
- Tooltip: "Week of [date]: 65% utilization ($3,400 / $5,000)"
- Only shown if user has credit accounts

**Chart 3: Subscription Breakdown**
- Type: Donut chart
- Inner: Total monthly recurring ($)
- Segments: Individual subscriptions by merchant
- Legend: Merchant name + amount
- Click segment → filter transactions to that merchant

**Summary Cards (above charts):**
- Total Spending (period)
- Average Daily Spend
- Top Category
- Savings Rate (if applicable)

**Explanation Boxes:**
Each chart has a "What this means" expandable section with plain-language explanation.

---

#### Tab 3: Education

**Purpose:** Deliver personalized financial education content

**Features:**

**Content Cards (3-5 per user):**
Each card displays:
- Icon (matched to category: credit, savings, budgeting, etc.)
- Title (e.g., "Understanding Credit Utilization")
- Brief description (2-3 sentences)
- **Rationale box** (highlighted background):
  - "We're showing you this because [specific data point]"
  - Example: "...your Visa ending in 4523 is at 65% utilization ($3,400 of $5,000 limit)"
- "Learn More" button (expands full content in modal)
- Tags: #Credit #DebtManagement

**Content Mapping:**
- High Utilization persona → Credit utilization explainer, debt paydown strategies, minimum payment dangers
- Subscription-Heavy persona → Subscription audit checklist, negotiation tips, cancellation workflows
- Savings Builder persona → Goal-setting frameworks, HYSA explainers, CD basics

**Card Sorting:**
- Priority order based on persona match and signal strength
- Most urgent/relevant at top
- Color-coded by topic area

**Disclaimer:**
At bottom of tab: "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."

---

#### Tab 4: Offers

**Purpose:** Present relevant partner products with eligibility transparency

**Features:**

**Offer Cards (2-3 per user):**
Each card displays:
- Partner logo
- Product name (e.g., "Balance Transfer Credit Card")
- Brief description
- Eligibility status:
  - ✅ "You may be eligible" (green badge)
  - ⚠️ "Requirements not met" (yellow badge) + explanation
- **Rationale:**
  - "This might help because [data-driven reason]"
  - Example: "...you're currently paying $87/month in interest on your Visa"
- "Learn More" external link
- **Disclosure:** "SpendSense may receive compensation. This is not a recommendation."

**Eligibility Logic:**
- Balance transfer card: High utilization (>50%) + no recent late payments
- HYSA: Building savings + current savings APY < 2%
- Budgeting app: Variable income detected OR subscription-heavy
- Subscription manager: ≥5 active subscriptions

**Filtering:**
- Don't show products user already has
- Don't show products with income requirements not met
- Never show predatory products (payday loans, high-fee accounts)

---

#### Chat Widget

**Purpose:** Answer user questions about their financial data

**Features:**
- Fixed position: bottom-right corner
- Expandable/collapsible
- Chat history (session-based)
- Typing indicator when processing

**Example Queries:**
- "What's my credit utilization?"
- "How much do I spend on subscriptions?"
- "Why am I seeing this education content?"
- "What can I do to improve my credit score?"

**Response Format:**
- Cites specific data points
- Includes numbers from actual transactions
- Links back to relevant tabs ("See Insights tab for more")
- Always includes disclaimer at end

**Guardrails:**
- No financial advice (only education)
- No shaming language
- PII scrubbing in logs
- Error handling for unclear questions
- Rate limiting (10 messages per minute)

**Technical Implementation:**
- OpenAI GPT-4 or Claude API
- System prompt with strict guidelines
- Retrieval of user's computed features + recent transactions
- Response validation before displaying

---

### 3. Operator Dashboard

**Layout:**
2-page application

#### Page 1: User List

**Purpose:** Overview of all users for monitoring and selection

**Features:**

**Table View:**
- Columns:
  - Full Name
  - Email
  - Primary Persona (30-day)
  - Risk Flags (badges: 🔴 High Utilization, ⚠️ Overdue, etc.)
  - Last Active
  - Actions (View Details button)
- Sort by any column
- Search by name or email
- Filter by persona type
- Filter by risk flags

**Summary Stats (top of page):**
- Total Users
- Users by Persona (bar chart)
- Active Users (last 7 days)
- Flagged Users Requiring Review

---

#### Page 2: User Detail

**Purpose:** Deep dive into individual user's data and recommendations

**Layout:**

**Section 1: User Overview**
- Name, email, member since
- Consent status + timestamp
- Connected accounts (number + types)
- Persona assignments:
  - 30-day: [Persona Name]
  - 90-day: [Persona Name]
  - 180-day: [Persona Name] (if different, shows evolution)

**Section 2: Behavioral Signals**
Display all detected signals with time windows:

**Credit Signals:**
- Visa ****4523: 65% utilization ($3,400 / $5,000)
- Last payment: $50 (minimum only)
- Interest charged: $87 last statement
- Status: Current (no overdues)

**Subscription Signals:**
- 8 active recurring merchants
- Monthly total: $203
- Top subscriptions: Netflix ($15), Spotify ($10), ...
- Subscription share: 15% of total spend

**Savings Signals:**
- Emergency fund: $1,200
- Monthly net inflow: $150
- Growth rate: 3.2% over 90 days
- Coverage: 1.2 months expenses

**Income Signals:**
- Payroll frequency: Biweekly
- Average paycheck: $1,750
- Last deposit: Oct 28, 2025
- Cash-flow buffer: 0.8 months

**Section 3: Recommendations Review**
Table of all education items + offers shown to user:
- Columns:
  - Type (Education / Offer)
  - Title
  - Shown At (timestamp)
  - Clicked? (boolean)
  - Decision Trace (button)
- Click "Decision Trace" → Opens modal with JSON view

**Decision Trace Format:**
```json
{
  "recommendation_id": "rec_123",
  "type": "education",
  "title": "Understanding Credit Utilization",
  "rationale": "User's Visa ****4523 is at 65% utilization",
  "decision_logic": {
    "persona_match": "high_utilization",
    "signals_used": [
      "credit_utilization_visa_4523: 0.65",
      "minimum_payment_only: true",
      "interest_charged: 87.00"
    ],
    "eligibility_checks_passed": true,
    "tone_validation_passed": true,
    "timestamp": "2025-11-03T10:30:00Z"
  }
}
```

**Section 4: Operator Actions**
- Button: "Override Recommendation" (logs action)
- Button: "Flag for Review" (adds to queue)
- Audit log of past operator actions on this user

---

### 4. Behavioral Signal Detection

**Purpose:** Compute features from transaction data to drive personalization

**Implementation:** Background job runs on user data update

**Signals to Detect:**

#### Subscription Detection
- Logic: Recurring merchant (≥3 occurrences in 90 days with monthly/weekly cadence)
- Cadence detection: ±3 days tolerance for monthly, ±1 day for weekly
- Outputs:
  - List of recurring merchants
  - Monthly recurring spend total
  - Subscription share of total spend

#### Credit Utilization
- For each credit card account:
  - Utilization % = balance / limit
  - Flag: High (≥50%), Medium (30-50%), Low (<30%)
- Minimum payment detection:
  - Compare last_payment_amount to minimum_payment_amount
  - Flag if equal within $5
- Interest detection:
  - Check for interest charges in transaction categories
- Overdue status from liability data

#### Savings Behavior
- Net inflow = deposits to savings-like accounts - withdrawals
- Growth rate = (current_balance - balance_90d_ago) / balance_90d_ago
- Emergency fund coverage:
  - Average monthly expenses from transactions
  - Coverage = savings_balance / avg_monthly_expenses
  - Flag: Excellent (≥6mo), Good (3-6mo), Building (1-3mo), Low (<1mo)

#### Income Stability
- Payroll detection:
  - Look for ACH deposits with "PAYROLL" or employer names
  - Identify recurring pattern
- Frequency: Weekly, biweekly, semi-monthly, monthly
- Variability: Coefficient of variation of paycheck amounts
- Cash-flow buffer = checking_balance / avg_monthly_expenses

**Time Windows:**
Compute signals for:
- 30-day (short-term, reactionary)
- 90-day (medium-term, trend detection)
- 180-day (long-term, stability assessment)

---

### 5. Persona Assignment

**Purpose:** Categorize users based on behavioral signals for targeted education

**Assignment Logic:** Hierarchical (higher priority first)

**Persona 1: High Utilization**
- **Priority:** 1 (highest)
- **Criteria:**
  - ANY card utilization ≥50% OR
  - Interest charges > $0 OR
  - Minimum payment only detected OR
  - Overdue status = true
- **Primary Focus:**
  - Reduce credit utilization
  - Understand interest impact
  - Payment planning strategies
  - Autopay setup education

**Persona 2: Subscription-Heavy**
- **Priority:** 2
- **Criteria:**
  - Recurring merchants ≥3 AND
  - (Monthly recurring spend ≥$50 in 30d OR subscription share ≥10%)
- **Primary Focus:**
  - Subscription audit checklist
  - Negotiation tactics
  - Cancellation workflows
  - Bill alerts setup

**Persona 3: Variable Income Budgeter**
- **Priority:** 3
- **Criteria:**
  - Median pay gap >45 days OR irregular frequency AND
  - Cash-flow buffer <1 month
- **Primary Focus:**
  - Percentage-based budgeting
  - Emergency fund basics
  - Income smoothing strategies
  - Expense forecasting

**Persona 4: Savings Builder**
- **Priority:** 4
- **Criteria:**
  - Savings growth rate ≥2% over 90-day window OR
  - Net savings inflow ≥$200/month AND
  - All card utilizations <30%
- **Primary Focus:**
  - Goal-setting frameworks
  - Savings automation
  - HYSA/CD education
  - Investment readiness quiz

**Assignment Rules:**
- One primary persona per time window
- User can have different personas across windows (30d vs 90d)
- If multiple criteria met, highest priority wins
- If no criteria met → "General Financial Wellness" default

---

### 6. Recommendation Engine

**Purpose:** Generate personalized education content and partner offers

**Process Flow:**
1. Retrieve user's persona and behavioral signals
2. Select 3-5 education items from content catalog
3. Select 2-3 partner offers with eligibility filtering
4. Generate rationales for each recommendation
5. Apply tone guardrails
6. Store recommendations with decision traces
7. Return to frontend

**Education Content Catalog:**

Structured as:
```json
{
  "id": "edu_credit_util_101",
  "title": "Understanding Credit Utilization",
  "category": "credit",
  "personas": ["high_utilization"],
  "trigger_signals": ["credit_utilization_high"],
  "content": "...",
  "rationale_template": "Your {card_name} is at {utilization}% utilization ({balance} of {limit} limit). Bringing this below 30% could improve your credit score."
}
```

**Rationale Generation:**
- Template-based with variable substitution
- Always cite specific data (account numbers, amounts, dates)
- Use plain language, no jargon
- Format: "We're showing you this because [concrete observation]"

**Tone Guardrails:**
- **No shaming:** Avoid "you're overspending", "bad habits", "poor choices"
- **Empowering:** Use "opportunity to", "you might consider", "here's what you can do"
- **Neutral observations:** "We noticed", "your data shows", "based on your activity"
- Validation: Check generated text against prohibited phrase list

**Partner Offer Filtering:**
```python
def filter_offers(user_signals, offers):
    eligible = []
    for offer in offers:
        # Check eligibility criteria
        if offer.type == "balance_transfer_card":
            if user_signals.credit_utilization >= 0.5:
                if not user_signals.has_late_payments:
                    eligible.append(offer)
        
        # Check doesn't already have product
        if offer.product_id in user_signals.existing_products:
            continue
        
        # Check minimum requirements
        if offer.min_income and user_signals.income < offer.min_income:
            continue
        
        eligible.append(offer)
    
    return eligible[:3]  # Top 3 most relevant
```

**Decision Trace Schema:**
```json
{
  "recommendation_id": "rec_abc123",
  "user_id": "user_xyz",
  "type": "education",
  "title": "Understanding Credit Utilization",
  "selected_reason": "Persona match: high_utilization",
  "signals_used": [
    {"signal": "credit_utilization_visa_4523", "value": 0.65, "threshold": 0.50},
    {"signal": "interest_charged", "value": 87.00, "threshold": 0}
  ],
  "template_id": "edu_credit_util_101",
  "rationale_generated": "Your Visa ending in 4523 is at 65% utilization...",
  "guardrails_passed": {
    "tone_check": true,
    "eligibility_check": true,
    "no_shaming": true
  },
  "timestamp": "2025-11-03T10:30:00Z"
}
```

---

### 7. Consent Management

**Purpose:** Respect user privacy and meet compliance requirements

**Requirements:**
- Explicit opt-in before processing any data
- Clear explanation of what data is used and why
- Easy revocation mechanism
- Audit trail of consent events

**Consent Modal (First Login):**

**Content:**
```
Welcome to SpendSense!

We'll analyze your transaction data to provide personalized financial education.

What we access:
- Your transaction history
- Account balances and types
- Payment patterns and subscriptions

What we don't do:
- Share your data with third parties (except partner offers you click)
- Provide financial advice (only education)
- Access your login credentials

You can revoke consent anytime in Settings.

[Checkbox] I consent to SpendSense analyzing my financial data

[Button: Accept] [Button: Decline]
```

**If Declined:**
- User cannot access dashboard
- Show message: "SpendSense requires consent to provide personalized education. You can grant consent anytime in Settings."

**Revocation Flow:**
- Settings → Privacy → "Revoke Consent" button
- Confirmation modal with consequences
- On revoke: Stop all processing, hide all recommendations, show consent modal again

**Database Tracking:**
```sql
consent_records (
  id uuid,
  user_id uuid,
  granted_at timestamptz,
  revoked_at timestamptz,
  version text,  -- "1.0" for MVP
  ip_address text
)
```

---

## Technical Architecture

### Stack Overview

**Frontend:**
- React 18 with Vite
- Tailwind CSS for styling
- Recharts for data visualization
- Supabase JS client for auth/data
- React Router for navigation

**Backend:**
- FastAPI (Python 3.11+)
- Supabase Python client
- Pandas for feature computation
- OpenAI API for chat (or Claude)
- Pydantic for data validation

**Database:**
- Supabase (PostgreSQL)
- Row-Level Security policies
- Automated backups

**Deployment:**
- Frontend: Vercel
- Backend: Railway or Render
- Database: Supabase (hosted)

**File Storage:**
- Supabase Storage (for any static content)

---

### Database Schema

See detailed schema in "Database Schema" section above. Key tables:
- `profiles` - User roles and metadata
- `consent_records` - Consent audit trail
- `accounts` - Synthetic bank accounts
- `transactions` - Transaction history
- `computed_features` - Cached feature computations
- `persona_assignments` - Persona tracking
- `recommendations` - Generated recommendations
- `decision_traces` - Auditability logs
- `chat_logs` - Chat history with guardrails status
- `operator_actions` - Operator audit log

---

### API Endpoints

**Authentication:**
- Handled by Supabase Auth (signup, login, logout, token refresh)

**Consumer Endpoints:**
```
GET  /api/users/me/profile          # User profile + consent status
GET  /api/users/me/accounts         # List of accounts
GET  /api/users/me/transactions     # Transaction list with filters
GET  /api/users/me/insights         # Computed charts data
GET  /api/users/me/recommendations  # Education + offers
POST /api/users/me/consent          # Grant/revoke consent
POST /api/chat                      # Chat with AI agent
```

**Operator Endpoints:**
```
GET  /api/operator/users                    # User list
GET  /api/operator/users/{user_id}          # User detail
GET  /api/operator/users/{user_id}/signals  # Behavioral signals
GET  /api/operator/users/{user_id}/traces   # Decision traces
POST /api/operator/users/{user_id}/override # Override recommendation
```

**Health Check:**
```
GET  /health  # API health status
```

---

### Data Flow

**User Login → Dashboard Load:**
1. User logs in via Supabase Auth
2. Frontend retrieves JWT token
3. Check consent status
4. If no consent → show modal → on accept, record in DB
5. If consent granted → fetch pre-computed features
6. Render dashboard with transactions, insights, education, offers

**Recommendation Generation (Background Job):**
1. Trigger: New user signup or daily refresh
2. Fetch user transactions from DB
3. Run feature detection (subscriptions, credit, savings, income)
4. Store computed features in `computed_features` table
5. Run persona assignment logic
6. Store persona in `persona_assignments` table
7. Generate recommendations from content catalog
8. Apply eligibility filters and tone guardrails
9. Store recommendations + decision traces
10. Mark as ready for user

**Operator Audit:**
1. Operator logs in
2. Views user list
3. Clicks user → fetch all data for that user
4. Views behavioral signals (from `computed_features`)
5. Views recommendations (from `recommendations`)
6. Clicks "Decision Trace" → fetch from `decision_traces`
7. Reviews JSON of how recommendation was generated
8. Can override or flag for review (logged in `operator_actions`)

---

## Data Requirements

### Synthetic Data Generation

**Seed 3 Demo Users:**

**User 1: Hannah Martinez (High Utilization)**
- Age: 29, Income: $48,000/year
- Accounts:
  - Checking: $850 balance
  - Savings: $1,200 balance
  - Visa Credit Card: $3,400 balance / $5,000 limit (68% utilization)
- Transactions (90 days):
  - ~200 transactions
  - Categories: 40% necessities, 30% discretionary, 20% bills, 10% subscriptions
  - Recurring: Netflix, Spotify, Planet Fitness, Adobe
  - Credit card interest charges: $87/month
  - Minimum payments only
- Persona: High Utilization
- Key behaviors: High utilization, interest charges, minimum payments

**User 2: Sam Patel (Subscription-Heavy)**
- Age: 34, Income: $65,000/year
- Accounts:
  - Checking: $2,400 balance
  - Savings: $5,000 balance
  - Credit Card: $800 balance / $8,000 limit (10% utilization)
- Transactions (90 days):
  - ~180 transactions
  - 8 active subscriptions totaling $203/month
  - Recurring: Netflix, Hulu, Disney+, Spotify, Apple iCloud, NYT, Peloton, HelloFresh
  - Subscription share: 15% of total spend
- Persona: Subscription-Heavy
- Key behaviors: Multiple subscriptions, good credit habits

**User 3: Sarah Chen (Savings Builder)**
- Age: 26, Income: $55,000/year
- Accounts:
  - Checking: $3,200 balance
  - High-Yield Savings: $8,500 balance (growing)
  - Credit Card: $400 balance / $3,000 limit (13% utilization)
- Transactions (90 days):
  - ~150 transactions
  - Automatic savings transfer: $500/month
  - Low discretionary spending
  - Pays credit card in full monthly
- Persona: Savings Builder
- Key behaviors: Consistent saving, low utilization, automated transfers

**Data Format:**
- CSV files: `accounts.csv`, `transactions.csv`
- JSON structure following Plaid schema
- No real PII - use faker library for names, addresses

---

### Content Catalog

**Education Items (15 total, 3-5 per persona):**

**High Utilization:**
1. Understanding Credit Utilization
2. The Real Cost of Minimum Payments
3. Debt Avalanche vs. Debt Snowball
4. How to Set Up Autopay
5. Building a Debt Paydown Plan

**Subscription-Heavy:**
1. The $200 Question: Are You Using All Your Subscriptions?
2. How to Negotiate Lower Bills
3. Subscription Cancellation Made Easy
4. Setting Up Bill Alerts

**Variable Income:**
1. Budgeting with Irregular Income
2. Building a Cash-Flow Buffer
3. The 50/30/20 Rule (Adapted)

**Savings Builder:**
1. From Savings to Investing: When Are You Ready?
2. High-Yield Savings Accounts Explained
3. Setting SMART Financial Goals
4. CD Laddering Basics

**Partner Offers (8 total):**
1. Balance Transfer Credit Card (0% APR for 18 months)
2. High-Yield Savings Account (4.5% APY)
3. Budgeting App (Mint alternative)
4. Subscription Management Tool (Truebill)
5. Credit Monitoring Service
6. Financial Planning Consultation
7. Debt Consolidation Loan
8. Cashback Credit Card

---

## Non-Functional Requirements

### Performance
- Page load time: <2s on 4G connection
- API response time: <500ms for 95th percentile
- Feature computation: <5s per user
- Chat response: <3s

### Security
- All data encrypted in transit (HTTPS)
- All data encrypted at rest
- JWT tokens for authentication
- RLS policies on all tables
- No PII in logs or decision traces
- Rate limiting on all endpoints
- CORS configured for frontend domain only

### Scalability
- MVP targets 100 concurrent users
- Database can handle 1000 users with current schema
- Background jobs isolated from request path
- Horizontal scaling possible (stateless API)

### Reliability
- 99% uptime target for MVP demo period
- Automated health checks
- Error logging to Sentry or similar
- Database automated backups daily

### Accessibility
- WCAG 2.1 AA compliance target
- Keyboard navigation support
- Screen reader friendly
- Color contrast ratios meet standards

---

## User Flows

### Consumer: First-Time Login to Education

1. User navigates to app URL
2. Clicks "Login" (or "Sign Up")
3. Enters credentials → submits
4. **Consent Modal appears**
   - Reads explanation
   - Checks "I consent" checkbox
   - Clicks "Accept"
5. **Dashboard loads** (Transactions tab default)
   - Sees list of recent transactions
6. **Clicks "Insights" tab**
   - Views spending by category chart
   - Sees credit utilization trend (68% - in red zone)
   - Notices subscription breakdown
7. **Clicks "Education" tab**
   - Sees 4 education cards
   - First card: "Understanding Credit Utilization"
   - Reads rationale: "Your Visa ending in 4523 is at 68% utilization..."
   - Clicks "Learn More"
   - Reads full educational content
8. **Scrolls down to chat widget**
   - Clicks chat icon
   - Types: "Why is high credit utilization bad?"
   - Receives response citing their specific card data
9. **Clicks "Offers" tab**
   - Sees balance transfer card offer
   - Reads rationale about saving on interest
   - Sees eligibility: "You may be eligible"
   - Clicks "Learn More" (external link)

### Operator: Auditing a Recommendation

1. Operator logs in
2. **Lands on User List page**
   - Sees table of 3 users
   - Hannah Martinez has 🔴 High Utilization flag
3. **Clicks "View Details" for Hannah**
4. **User Detail page loads**
   - Section 1: Sees Hannah's profile, consent granted
   - Section 2: Reviews behavioral signals
     - Credit: 68% utilization, minimum payments
     - Subscriptions: 4 active, $62/month
     - Savings: $1,200, 1.2 months coverage
     - Income: Biweekly, $1,750/paycheck
5. **Scrolls to Section 3: Recommendations**
   - Sees list of 5 education items + 2 offers
   - First item: "Understanding Credit Utilization"
6. **Clicks "Decision Trace" button**
   - Modal opens with JSON
   - Reviews:
     - Persona match: high_utilization
     - Signals used: credit_utilization_visa_4523 = 0.68
     - Template ID: edu_credit_util_101
     - Guardrails passed: tone_check = true
7. **Closes modal**
8. **Clicks "Override Recommendation"**
   - Enters reason: "User already completed this module"
   - Confirms override
   - Action logged in operator_actions table

---

## Out of Scope (Future Enhancements)

The following features are **NOT** included in the MVP:

❌ Real Plaid integration (using synthetic data only)
❌ Full 50-100 user dataset (only 3 demo users)
❌ Email notifications
❌ Mobile apps (iOS/Android)
❌ SMS alerts
❌ Document upload (tax forms, pay stubs)
❌ Multi-language support
❌ Social sharing features
❌ Gamification (points, badges, challenges)
❌ Investment tracking
❌ Bill pay functionality
❌ Custom persona creation by operators
❌ A/B testing framework
❌ Advanced analytics dashboard for operators