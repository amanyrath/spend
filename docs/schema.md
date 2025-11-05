# SpendSense Schema Documentation

This document describes the database schema, data structures, and API response formats.

## Database Schema

### SQLite Tables

#### `users`
Stores user profiles.

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | TEXT PRIMARY KEY | Unique user identifier |
| `name` | TEXT | User's name (synthetic) |
| `created_at` | TEXT | ISO format timestamp |

#### `accounts`
Stores bank, credit, and loan accounts.

| Column | Type | Description |
|--------|------|-------------|
| `account_id` | TEXT PRIMARY KEY | Unique account identifier |
| `user_id` | TEXT | Foreign key to users |
| `type` | TEXT | Account type: "depository", "credit", or "loan" |
| `subtype` | TEXT | Account subtype: "checking", "savings", "credit card", "auto", "mortgage", "student" |
| `balance` | REAL | Current balance (for loans, this is remaining principal) |
| `limit` | REAL | Credit limit (for credit accounts) or original loan amount (for loans) |
| `mask` | TEXT | Last 4 digits of account |

#### `transactions`
Stores transaction history (Plaid-compatible schema).

| Column | Type | Description |
|--------|------|-------------|
| `transaction_id` | TEXT PRIMARY KEY | Unique transaction identifier |
| `account_id` | TEXT | Foreign key to accounts |
| `user_id` | TEXT | Foreign key to users |
| `date` | TEXT | Transaction date (YYYY-MM-DD) |
| `amount` | REAL | Transaction amount (negative for expenses) |
| `merchant_name` | TEXT | Merchant name |
| `category` | TEXT | Transaction category as JSON array: `["Food and Drink", "Groceries"]` or legacy string |
| `pending` | INTEGER | 1 if pending, 0 if posted |
| `location_address` | TEXT | Street address (optional) |
| `location_city` | TEXT | City name (optional) |
| `location_region` | TEXT | State/region code (optional) |
| `location_postal_code` | TEXT | Postal/ZIP code (optional) |
| `location_country` | TEXT | Country code (e.g., "US") (optional) |
| `location_lat` | REAL | Latitude coordinate (optional) |
| `location_lon` | REAL | Longitude coordinate (optional) |
| `iso_currency_code` | TEXT | Currency code (default: "USD") |
| `payment_channel` | TEXT | Payment channel: "online", "in store", or "other" |
| `authorized_date` | TEXT | Authorization date (YYYY-MM-DD) (optional) |

#### `computed_features`
Stores behavioral signals computed for users.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment ID |
| `user_id` | TEXT | Foreign key to users |
| `time_window` | TEXT | Time window ("30d" or "180d") |
| `signal_type` | TEXT | Signal type ("subscriptions", "credit_utilization", etc.) |
| `signal_data` | TEXT | JSON string with signal data |
| `computed_at` | TEXT | ISO format timestamp |

#### `persona_assignments`
Stores persona assignments for users.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment ID |
| `user_id` | TEXT | Foreign key to users |
| `time_window` | TEXT | Time window ("30d" or "180d") |
| `persona` | TEXT | Persona name |
| `criteria_met` | TEXT | JSON array of criteria strings |
| `assigned_at` | TEXT | ISO format timestamp |

#### `recommendations`
Stores generated recommendations.

| Column | Type | Description |
|--------|------|-------------|
| `recommendation_id` | TEXT PRIMARY KEY | Unique recommendation identifier |
| `user_id` | TEXT | Foreign key to users |
| `type` | TEXT | Recommendation type ("education" or "partner_offer") |
| `content_id` | TEXT | Reference to content catalog |
| `title` | TEXT | Recommendation title |
| `rationale` | TEXT | Personalized rationale text |
| `decision_trace` | TEXT | JSON string with decision trace |
| `shown_at` | TEXT | ISO format timestamp |

### Firestore Structure

When deployed, data is stored in Firestore with this structure:

```
users/
  {user_id}/
    - name: string
    - created_at: timestamp
    accounts/
      {account_id}/
        - type, subtype, balance, limit, mask
        (type: "depository", "credit", or "loan")
        (subtype: "checking", "savings", "credit card", "auto", "mortgage", "student")
    transactions/
      {transaction_id}/
        - date, amount, merchant_name, category (array), pending
        - location_address, location_city, location_region, location_postal_code
        - location_country, location_lat, location_lon
        - iso_currency_code, payment_channel, authorized_date
    computed_features/
      {feature_id}/
        - signal_type, signal_data, time_window, computed_at
    persona_assignments/
      {assignment_id}/
        - persona, criteria_met, time_window, assigned_at
    recommendations/
      {recommendation_id}/
        - type, content_id, title, rationale, decision_trace, shown_at
```

## Plaid-Compatible Data Structures

### Transaction Category Format

Transactions use Plaid's hierarchical category system. Categories are stored as JSON arrays:

**Legacy format (still supported):**
```json
"groceries"
```

**Plaid format (preferred):**
```json
["Food and Drink", "Groceries"]
```

The first element is the primary category, and the second is the detailed category.

### Account Types and Subtypes

- **Depository accounts:**
  - `type`: "depository"
  - `subtype`: "checking" or "savings"

- **Credit accounts:**
  - `type`: "credit"
  - `subtype`: "credit card"
  - Supports 0-6 credit cards per user

- **Loan accounts:**
  - `type`: "loan"
  - `subtype`: "auto", "mortgage", or "student"
  - `balance`: Remaining principal balance
  - `limit`: Original loan amount

### Liability Structure

Liabilities are exported to CSV with different fields depending on account type:

#### Credit Card Liabilities
```json
{
  "account_id": "acc_123",
  "account_type": "credit",
  "account_subtype": "credit card",
  "aprs": "[{\"apr_percentage\": 18.5, \"apr_type\": \"purchase_apr\"}]",
  "minimum_payment_amount": 45.00,
  "last_payment_amount": 250.00,
  "is_overdue": false,
  "last_statement_balance": 2250.00
}
```

#### Mortgage Liabilities
```json
{
  "account_id": "acc_456",
  "account_type": "loan",
  "account_subtype": "mortgage",
  "origination_date": "2015-03-15",
  "original_principal_balance": 350000.00,
  "interest_rate": 4.25,
  "next_payment_due_date": "2025-02-01",
  "escrow_balance": 3200.00,
  "property_address": "123 Main St, Anytown, CA 12345",
  "principal_balance": 285000.00
}
```

#### Auto Loan Liabilities
```json
{
  "account_id": "acc_789",
  "account_type": "loan",
  "account_subtype": "auto",
  "origination_date": "2020-06-10",
  "original_principal_balance": 28000.00,
  "interest_rate": 5.75,
  "next_payment_due_date": "2025-02-15",
  "principal_balance": 12500.00
}
```

#### Student Loan Liabilities
```json
{
  "account_id": "acc_101",
  "account_type": "loan",
  "account_subtype": "student",
  "origination_date": "2018-09-01",
  "original_principal_balance": 45000.00,
  "interest_rate": 6.25,
  "next_payment_due_date": "2025-02-20",
  "guarantor": "FEDERAL",
  "principal_balance": 32000.00
}
```

### Homeownership Distribution

Mortgage accounts are assigned based on income quintile with the following homeownership rates:
- 20th percentile: 44%
- 40th percentile: 58%
- 60th percentile: 62%
- 80th percentile: 75%
- 100th percentile: 87%

Non-homeowners receive monthly rent payments instead of mortgage payments.

### Credit Card Payment Behaviors

Credit card payment behaviors are distributed as follows:
- 11% of cardholders: Minimum payment only
- 40-44% of cardholders: Pay balance in full
- 45-49% of cardholders: Pay between minimum and full

## Data Structures

### Signal Data Structures

#### Subscription Signals
```json
{
  "recurring_merchants": [
    {
      "merchant": "Netflix",
      "frequency": "monthly",
      "amount": 15.99,
      "last_occurrence": "2025-01-15"
    }
  ],
  "monthly_recurring": 45.97,
  "subscription_share": 0.08
}
```

#### Credit Utilization Signals
```json
{
  "total_utilization": 68.5,
  "interest_charged": 45.30,
  "minimum_payment_only": true,
  "is_overdue": false,
  "accounts": [
    {
      "account_id": "acc_123",
      "utilization": 68.5,
      "balance": 3425.00,
      "limit": 5000.00
    }
  ]
}
```

#### Savings Behavior Signals
```json
{
  "total_savings": 3500.00,
  "net_inflow": 200.00,
  "growth_rate": 0.06,
  "emergency_fund_coverage": 2.5,
  "coverage_level": "good"
}
```

#### Income Stability Signals
```json
{
  "frequency": "biweekly",
  "median_pay_gap": 14,
  "irregular_frequency": false,
  "coefficient_of_variation": 5.2,
  "cash_flow_buffer": 1.5,
  "avg_monthly_income": 3500.00,
  "avg_monthly_expenses": 2800.00
}
```

### Persona Assignment Structure
```json
{
  "persona": "high_utilization",
  "criteria_met": [
    "credit_utilization >= 0.50",
    "interest_charged > 0"
  ],
  "assigned_at": "2025-01-15T10:00:00Z"
}
```

### Decision Trace Structure
```json
{
  "persona_match": "high_utilization",
  "signals_used": [
    {
      "signal": "credit_utilization",
      "value": 0.685,
      "threshold": 0.50
    }
  ],
  "guardrails_passed": {
    "tone_check": true,
    "eligibility_check": true
  },
  "timestamp": "2025-01-15T10:00:00Z"
}
```

## API Response Formats

### GET /api/health
```json
{
  "status": "ok",
  "timestamp": "2025-01-15T10:00:00Z"
}
```

### GET /api/users
```json
[
  {
    "user_id": "user_001",
    "name": "John Doe",
    "persona_30d": "high_utilization",
    "behavior_count": 4,
    "recommendation_count": 5
  }
]
```

### GET /api/users/{user_id}
```json
{
  "user_id": "user_001",
  "name": "John Doe",
  "created_at": "2025-01-01T00:00:00Z",
  "personas": {
    "30d": {
      "persona": "high_utilization",
      "criteria_met": ["credit_utilization >= 0.50"],
      "assigned_at": "2025-01-15T10:00:00Z"
    },
    "180d": {
      "persona": "high_utilization",
      "criteria_met": ["credit_utilization >= 0.50"],
      "assigned_at": "2025-01-15T10:00:00Z"
    }
  }
}
```

### GET /api/users/{user_id}/signals
```json
{
  "user_id": "user_001",
  "time_window": "30d",
  "signals": {
    "subscriptions": { /* subscription signals */ },
    "credit_utilization": { /* credit signals */ },
    "savings_behavior": { /* savings signals */ },
    "income_stability": { /* income signals */ }
  }
}
```

### GET /api/users/{user_id}/recommendations
```json
{
  "user_id": "user_001",
  "time_window": "30d",
  "recommendations": [
    {
      "recommendation_id": "rec_abc123",
      "user_id": "user_001",
      "type": "education",
      "content_id": "edu_credit_util_101",
      "title": "Understanding Credit Utilization",
      "rationale": "Your Visa ending in 4523 is at 68% utilization...",
      "decision_trace": { /* decision trace object */ },
      "shown_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

## Error Responses

All endpoints return standard HTTP status codes:
- `200`: Success
- `404`: Resource not found
- `500`: Internal server error

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

