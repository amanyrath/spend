# SpendSense Decision Log

This document records key design decisions made during the development of SpendSense.

## Persona Assignment

### Why Hierarchical Persona Assignment?

We chose a hierarchical (priority-based) approach where personas are checked in order and the first match wins. This decision was made because:

1. **Clear Prioritization**: High Utilization represents the most urgent financial risk, so it should take precedence over other personas
2. **Deterministic Results**: Each user gets exactly one primary persona, making recommendations easier to generate
3. **Simple Logic**: Easier to understand, debug, and explain than multi-persona assignment systems
4. **Real-world Alignment**: Financial advisors typically prioritize debt reduction over other goals

**Priority Order:**
1. High Utilization (debt/credit issues)
2. Variable Income (income instability)
3. Subscription-Heavy (recurring expenses)
4. Savings Builder (positive savings behavior)
5. General Wellness (default)

**Alternative Considered**: Multi-persona assignment where users could have multiple personas. Rejected because it would complicate recommendation logic and reduce explainability.

## Rationale Templates

### How Were Rationale Templates Chosen?

Rationale templates were designed to:

1. **Cite Specific Data**: Every rationale includes actual user data (e.g., "Your Visa ending in 4523 is at 68% utilization")
2. **Be Actionable**: Templates explain why the recommendation is relevant (e.g., "Bringing this below 30% could improve your credit score")
3. **Use Positive Language**: Avoids judgmental terms (no "overspending", "bad habits", etc.)
4. **Be Concise**: Templates are brief enough to be readable but detailed enough to be meaningful

**Template Variables:**
- `{card_name}` - Credit card name/mask
- `{utilization}` - Utilization percentage
- `{balance}` - Current balance
- `{limit}` - Credit limit
- `{interest_charged}` - Monthly interest charges
- `{median_pay_gap}` - Days between paychecks
- `{cash_flow_buffer}` - Months of expenses covered
- `{monthly_recurring}` - Total monthly subscription costs

**Rationale**: Templates allow for personalization while maintaining consistency and ensuring all rationales cite actual user data.

## Signal Detection Algorithms

### Trade-offs in Signal Detection

#### Subscription Detection
- **Algorithm**: Groups transactions by merchant, checks for ≥3 occurrences with regular cadence (±3 days monthly, ±1 day weekly)
- **Trade-off**: Simpler pattern matching vs. ML-based detection
- **Rationale**: Pattern matching is more explainable and deterministic. ML would require training data and be harder to audit.

#### Credit Utilization
- **Algorithm**: Direct calculation: `balance / limit` per account
- **Trade-off**: Real-time calculation vs. cached values
- **Rationale**: Always calculating ensures accuracy. Caching would save compute but risk stale data.

#### Savings Behavior
- **Algorithm**: Net inflow calculation over 180-day window
- **Trade-off**: 180-day window provides stability but may miss recent changes
- **Rationale**: Longer window smooths out volatility and provides more reliable trends for financial planning.

#### Income Stability
- **Algorithm**: Median pay gap calculation with coefficient of variation
- **Trade-off**: Simple statistics vs. complex time-series analysis
- **Rationale**: Median and CV provide sufficient insight without over-engineering. Complex analysis would be harder to explain to users.

## Database Choice

### SQLite (Local) vs. Firestore (Deployment)

**Decision**: Support both databases with automatic detection.

**Rationale**:
- **SQLite**: Perfect for local development - zero setup, fast, file-based
- **Firestore**: Required for Vercel deployment (serverless functions can't use file-based databases)
- **Dual Support**: Allows same codebase to work in both environments

**Implementation**: Use `USE_FIRESTORE` flag based on environment variable detection. All database operations check this flag and route to appropriate backend.

## API Design

### RESTful Endpoints

**Structure**: `/api/users`, `/api/users/{user_id}`, `/api/users/{user_id}/signals`, etc.

**Rationale**:
- Follows REST conventions
- Hierarchical structure matches data model
- Easy to understand and document
- Compatible with frontend routing

**Alternative Considered**: GraphQL. Rejected because REST is simpler for this use case and doesn't require additional infrastructure.

## UI Technology

### HTML + Vanilla JS vs. React

**Decision**: Simple HTML with vanilla JavaScript.

**Rationale**:
- Faster to build (no build process needed)
- Easier to deploy (static files)
- Sufficient for operator interface (not customer-facing)
- No framework dependencies

**Trade-off**: Less reusable components and more code duplication, but acceptable for an internal tool.

## Evaluation Metrics

### Why These Four Metrics?

1. **Coverage**: Ensures all users have personas and behaviors detected
2. **Explainability**: Ensures all recommendations have rationales
3. **Latency**: Performance requirement (must be fast enough for real-time use)
4. **Auditability**: Ensures decision traces exist for compliance/debugging

**Rationale**: These metrics cover the core requirements: completeness, explainability, performance, and auditability. Additional metrics could be added later but these are the minimum viable set.

## Tone Guardrails

### Prohibited Phrases

**Decision**: Block phrases like "overspending", "bad habits", "poor choices", "irresponsible", "wasteful"

**Rationale**: Financial advice should be constructive and non-judgmental. Users are already aware of their financial stress; adding judgment doesn't help.

**Implementation**: Simple string matching (case-insensitive). More sophisticated NLP could be added later but simple filtering catches most issues.

## Decision Traces

### What's Included in Decision Traces?

**Structure**:
```json
{
  "persona_match": "high_utilization",
  "signals_used": [...],
  "guardrails_passed": {...},
  "timestamp": "..."
}
```

**Rationale**: Traces provide complete auditability - anyone can see why a recommendation was made, what data was used, and what checks passed. Essential for compliance and debugging.

**Future Enhancement**: Could include confidence scores or alternative personas considered.











