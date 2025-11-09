# Chat Agent Capabilities Guide

## Overview

The SpendSense chat agent is an AI-powered financial education assistant that provides personalized insights based on transaction data. This document describes the agent's capabilities, analysis features, safety measures, and configuration options.

## Core Capabilities

### 1. Temporal Spending Analysis

The agent analyzes spending patterns across time to provide insights about when and how users spend money.

**Weekday vs Weekend Patterns**
- Calculates average spending on weekdays vs weekends
- Identifies highest spending days
- Provides transaction counts for each period

**Example Insights:**
- "Your weekend spending averages $85 compared to $62 on weekdays"
- "Tuesday is your highest spending day this month at $125"

**Month-to-Date Progress**
- Tracks spending progress through the current month
- Calculates daily averages
- Projects monthly totals based on current pace

**Example Insights:**
- "You've spent $850 so far this month (15 days), averaging $56.67 per day"
- "At this pace, you're projected to spend $1,700 this month"

**Spending Velocity Trends**
- Analyzes if spending is increasing or decreasing over time
- Compares first half vs second half of transaction window
- Identifies trend direction (increasing, decreasing, stable)

**Example Insights:**
- "Your spending is trending 15% higher in the second half of the month"
- "Spending has decreased 10% compared to the first two weeks"

### 2. Category Intelligence

Detailed breakdown of spending by category with percentages and transaction counts.

**Features:**
- Top 5 spending categories by amount
- Percentage of total spending per category
- Transaction count and average transaction size
- Both primary and detailed category analysis

**Example Insights:**
- "Food and Drink: $325 (32% of spending) across 18 transactions (avg $18.06)"
- "Transportation: $180 (18% of spending) across 4 transactions (avg $45.00)"

### 3. Merchant Pattern Recognition

Identifies frequently visited merchants and spending patterns.

**Features:**
- Detects merchants with 3+ visits
- Calculates total spend and average per visit
- Tracks visit frequency
- Limited to top 5 frequent merchants for focus

**Example Insights:**
- "Starbucks: 12 visits, $156 total (avg $13 per visit)"
- "Amazon: 8 visits, $420 total (avg $52.50 per visit)"

### 4. Payment Channel Analysis

Analyzes online vs in-store spending preferences.

**Features:**
- Breakdown by payment channel (online, in store, other)
- Transaction counts per channel
- Total amounts per channel

**Example Insights:**
- "Online: 45 transactions, $1,250"
- "In Store: 28 transactions, $680"

### 5. Pending Transaction Awareness

Tracks pending transactions that will impact future balances.

**Features:**
- Count of pending transactions
- Total pending charges
- Total pending deposits
- Net pending amount

**Example Insights:**
- "You have 3 pending transactions totaling $150 that will post soon"
- "Net pending: -$120 (charges exceed pending deposits)"

### 6. Account-Specific Activity

Groups transactions by account for account-level insights.

**Features:**
- Transaction count per account
- Total spent per account
- Total deposited per account
- Account type and mask identification

**Example Insights:**
- "Checking ending in 1234: 45 transactions, $2,100 spent, $3,500 deposited"
- "Credit Card ending in 5678: 18 transactions, $680 spent"

### 7. Credit Utilization Monitoring

Analyzes credit card usage and utilization rates.

**Features:**
- Per-card utilization percentages
- Balance and limit information
- Account masking for privacy

**Example Insights:**
- "Your Visa ending in 4523 shows 65% utilization ($3,250 of $5,000 limit)"

### 8. Subscription Tracking

Identifies and tracks recurring subscription payments.

**Features:**
- Monthly recurring totals
- Top 5 subscriptions by amount
- Percentage of income spent on subscriptions

**Example Insights:**
- "You have 5 recurring subscriptions totaling $75/month: Netflix ($15), Spotify ($10), Adobe ($22), Gym ($25), Cloud Storage ($3)"

### 9. Savings Behavior Analysis

Tracks savings patterns and emergency fund coverage.

**Features:**
- Average monthly income and expenses
- Savings rate calculation
- Emergency fund coverage assessment

**Example Insights:**
- "Average monthly income $4,500, expenses $3,200 (savings rate: 28.9%)"

## Safety and Privacy Features

### 1. PII Sanitization

**Automatic Removal:**
- Location data (addresses, cities, coordinates)
- Authorized dates
- Email patterns in merchant names
- Phone numbers in transaction data
- Account numbers (except last 4 digits)
- SSN patterns
- Routing numbers

**Validation:**
- All merchant names validated for PII patterns
- User messages sanitized before processing
- Guardrails AI validation on responses

### 2. Token Management

**Context Optimization:**
- Automatic token estimation (1 token ≈ 4 characters)
- Maximum context tokens: 2,000 (configurable)
- Intelligent transaction sampling if limits exceeded
- Prioritizes recent + high-value + random sample

**Transaction Limits:**
- Maximum 100 transactions per request (configurable)
- ~3 transactions per day in window, capped at max
- Representative sampling maintains data diversity

### 3. Merchant Name Sanitization

**Enhanced Patterns Removed:**
- Email addresses (`@` symbol)
- Phone numbers (`555-123-4567`)
- ATM identifiers (`ATM 12345`)
- Check numbers (`CHECK 1234`)
- Wire transfer IDs (`WIRE 5678`)

### 4. Guardrails Validation

**Response Validation:**
- Toxic language detection (if available)
- Prohibited phrase checking
- Tone validation for educational context
- Retry mechanism with stricter prompts

**Prohibited Phrases:**
- "overspending"
- "bad habits"
- "poor choices"
- "irresponsible"
- "wasteful"
- (and variations)

### 5. Optional Privacy Enhancements

**Amount Bucketing:**
- Can be enabled via `CHAT_ENABLE_AMOUNT_BUCKETING=true`
- Groups amounts into ranges ($0-$5, $5-$10, etc.)
- Provides additional privacy layer
- Disabled by default

## Configuration Options

### Environment Variables

```bash
# Transaction Window
CHAT_MAX_TRANSACTION_WINDOW=180  # Maximum days (default: 180)

# Transaction Limits
CHAT_MAX_TRANSACTIONS=100  # Maximum per request (default: 100)

# Token Management
CHAT_MAX_CONTEXT_TOKENS=2000  # Maximum context tokens (default: 2000)

# Privacy Features
CHAT_ENABLE_AMOUNT_BUCKETING=false  # Enable amount bucketing (default: false)

# OpenAI Configuration
OPENAI_API_KEY=your_key_here  # Required
OPENAI_MODEL=gpt-4o-mini  # Model to use (default: gpt-4o-mini)
```

### Request Parameters

**`transaction_window_days`** (optional, default: 30)
- Minimum: 7 days
- Maximum: 180 days (or `CHAT_MAX_TRANSACTION_WINDOW`)
- Controls how far back in transaction history to analyze

**Example Requests:**

```json
{
  "user_id": "user_001",
  "message": "How is my spending this month?",
  "transaction_window_days": 30
}
```

```json
{
  "user_id": "user_001",
  "message": "Show me my spending trends over the last quarter",
  "transaction_window_days": 90
}
```

## Response Format

### Standard Response

```json
{
  "data": {
    "response": "Based on your recent transactions over the last 30 days (87 transactions), here's what I'm seeing:...",
    "citations": [
      {
        "data_point": "Account ending in 4523",
        "value": "65.0% utilization"
      },
      {
        "data_point": "Recurring subscriptions",
        "value": "$75.00/month"
      }
    ]
  },
  "meta": {
    "user_id": "user_001",
    "timestamp": "2025-01-15T10:00:00Z"
  }
}
```

### Context Provided to Agent

The agent receives comprehensive context including:

```
Transaction Window: Last 30 days (87 transactions)

User Persona: high_utilization

Spending Patterns:
  - Weekday: 62 transactions, $1,850.00 total (avg $29.84)
  - Weekend: 25 transactions, $730.00 total (avg $29.20)
  - Highest spending day: Saturday ($280.50)

Month-to-Date (January 2025):
  - Spent so far: $1,450.00 (48 transactions)
  - Daily average: $96.67 (15 days elapsed, 16 remaining)
  - Projected monthly: $2,996.67

Spending by Category:
  - Food and Drink: $425.00 (32.3%) - 28 transactions (avg $15.18)
  - Shopping: $380.00 (28.9%) - 12 transactions (avg $31.67)
  - Transportation: $180.00 (13.7%) - 6 transactions (avg $30.00)

Payment Channels:
  - Online: 45 transactions, $750.00
  - In Store: 42 transactions, $830.00

Frequent Merchants (3+ visits):
  - Starbucks: 12 visits, $156.00 total (avg $13.00 per visit)
  - Amazon: 8 visits, $420.00 total (avg $52.50 per visit)

Pending Transactions:
  - Count: 3
  - Pending charges: $150.00
  - Net pending: -$150.00
```

## Educational Tone Guidelines

The agent follows strict guidelines to maintain an educational, non-judgmental tone:

### DO:
- Cite specific data points with exact numbers
- Use neutral, supportive language
- Frame insights constructively
- Reference temporal patterns and trends
- Acknowledge payment channel preferences
- Note pending transactions
- End with educational disclaimer

### DON'T:
- Give specific financial advice
- Use judgmental language
- Shame spending habits
- Make assumptions about user's goals
- Recommend specific products or services

### Example Good Responses:

"Based on your transactions, your spending is trending 15% higher in the second half of this month, with weekend spending averaging $85 compared to $62 on weekdays. Your checking account ending in 1234 shows 45 transactions totaling $2,100."

"You have 5 recurring subscriptions totaling $75/month: Netflix ($15), Spotify ($10), Adobe ($22), Gym ($25), and Cloud Storage ($3). This represents approximately 2.5% of your average monthly income."

### Example Bad Responses:

"You're overspending on weekends. You should cut back on your bad spending habits."

"You have too many wasteful subscriptions. Cancel some immediately."

## Rate Limiting

- **Limit:** 10 messages per minute per user
- **Purpose:** Prevent abuse and manage API costs
- **Response:** HTTP 429 with `Retry-After` header

## Logging and Audit

All chat interactions are logged for:
- Security monitoring (PII detection events)
- Guardrails validation results
- Token usage and context reduction
- Merchant name validation issues

## Best Practices

### For Optimal Results:

1. **Use appropriate transaction windows:**
   - 7-14 days: Recent behavior, quick insights
   - 30 days: Standard monthly analysis
   - 60-90 days: Trend identification
   - 180 days: Long-term pattern analysis

2. **Ask specific questions:**
   - "How is my spending this month compared to last month?"
   - "What are my top spending categories?"
   - "How much do I spend on weekends vs weekdays?"

3. **Monitor token usage:**
   - Longer windows = more transactions = more tokens
   - System automatically samples if needed
   - Check logs for context reduction events

### For Developers:

1. **Environment configuration:**
   - Set appropriate limits based on your needs
   - Monitor token usage in production
   - Adjust sampling ratios if needed

2. **Testing:**
   - Use pytest to run comprehensive tests
   - Test with various transaction window sizes
   - Verify PII sanitization works correctly

3. **Monitoring:**
   - Watch for PII detection events
   - Track guardrails validation failures
   - Monitor context reduction frequency

## Limitations

1. **Transaction Data Only:**
   - Agent only analyzes provided transaction data
   - Cannot access external financial data
   - Cannot make API calls to other services

2. **Educational Content Only:**
   - Cannot provide financial advice
   - Cannot recommend specific investments
   - Cannot prioritize debt payments

3. **Token Constraints:**
   - Maximum 2,000 tokens for context (configurable)
   - Automatic sampling may reduce detail
   - Very large windows may lose some transactions

4. **Time Sensitivity:**
   - Analysis based on transactions in specified window
   - Future projections assume constant rate
   - Does not account for known future expenses

## Support and Troubleshooting

### Common Issues:

**"Response seems generic"**
- Try increasing transaction_window_days for more context
- Ensure user has sufficient transaction history
- Check logs for context reduction events

**"Agent missed important pattern"**
- May be due to transaction sampling
- Increase CHAT_MAX_TRANSACTIONS if needed
- Verify transactions have correct dates

**"PII appears in response"**
- Should not happen due to sanitization
- Check guardrails validation logs
- Report issue for investigation

### Debug Steps:

1. Check logs for token estimation and reduction
2. Verify transaction data has required fields
3. Ensure environment variables are set correctly
4. Test with smaller transaction windows first

## Future Enhancements

Planned improvements:
- Multi-month trend comparison
- Budget tracking integration
- Goal progress monitoring
- Predictive insights for upcoming expenses
- Enhanced visualization data in responses







