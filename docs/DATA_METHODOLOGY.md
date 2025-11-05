# Synthetic Data Generation

This document describes the rationale, methodology, and design decisions behind the SpendSense synthetic data generation system.

## Table of Contents

1. [Rationale](#rationale)
2. [Methodology Overview](#methodology-overview)
3. [Data Schema](#data-schema)
4. [User Generation](#user-generation)
5. [Account Generation](#account-generation)
6. [Transaction Generation](#transaction-generation)
7. [Liability Generation](#liability-generation)
8. [Demographic Distributions](#demographic-distributions)
9. [Data Sources](#data-sources)

## Rationale

SpendSense generates synthetic financial data to enable development, testing, and demonstration of financial wellness features without requiring real user data or production Plaid integrations. This approach provides several benefits:

- **Privacy**: No real user data or PII is required
- **Consistency**: Reproducible data sets for testing and development
- **Realism**: Data follows real-world patterns and distributions
- **Compliance**: No privacy or security concerns during development
- **Cost**: No API costs during development and testing
- **Control**: Ability to create diverse scenarios and edge cases

The generated data is designed to be Plaid-compatible, enabling seamless integration with real Plaid data when moving to production.

## Methodology Overview

The synthetic data generation system creates realistic financial profiles for a specified number of users (default: 75) over a configurable time period (default: 200 days). The system follows these principles:

1. **Realistic Distributions**: Uses actual demographic and financial statistics from government and industry sources
2. **Plaid Compatibility**: Structures data to match Plaid's API schema exactly
3. **Behavioral Patterns**: Simulates realistic spending, saving, and payment behaviors
4. **Demographic Diversity**: Ensures representation across income levels and financial situations
5. **Temporal Realism**: Generates transactions with realistic timing and frequency patterns

## Data Schema

The generated data follows Plaid's transaction and account schema as documented in:
- [Plaid Transactions API](https://plaid.com/docs/api/products/transactions/)
- [Plaid Transactions Overview](https://plaid.com/docs/transactions/)

### Transaction Schema

Transactions include all Plaid-compatible fields:

- **Category**: Array format `["Food and Drink", "Groceries"]` (matches Plaid's hierarchical category system)
- **Location**: Full location data including address, city, region, postal code, country, and coordinates
- **Payment Channel**: `online`, `in store`, or `other`
- **Currency**: ISO currency code (default: USD)
- **Authorization**: Authorized date for pending transactions

### Account Types

- **Depository**: Checking and savings accounts
- **Credit**: Credit cards (0-6 per user with weighted distribution)
- **Loan**: Auto loans, mortgages, and student loans

## User Generation

Users are generated with realistic income distributions:

- **Income Range**: $30,000 - $150,000 annually
- **Distribution**: Weighted toward middle-income ranges
- **Deterministic**: Uses seeded random number generator for reproducibility

## Account Generation

### Depository Accounts

- **Checking**: Always created (1 per user)
- **Savings**: 70% probability per user
- **Balances**: Based on income levels and savings behavior patterns

### Credit Cards

- **Count**: 0-6 cards per user with weighted distribution
  - 0 cards: 15%
  - 1 card: 25%
  - 2 cards: 25%
  - 3 cards: 20%
  - 4 cards: 10%
  - 5 cards: 3%
  - 6 cards: 2%
- **Credit Limits**: 10-30% of annual income per card
- **Payment Behaviors**:
  - 11% make only minimum payments
  - 42% pay balance in full each month
  - 47% pay between minimum and full

Source: [Federal Reserve Survey of Consumer Finances](https://www.federalreserve.gov/econres/scfindex.htm)

### Loan Accounts

- **Auto Loans**: 45% of users (40-50% range)
- **Student Loans**: 25% of users (20-30% range)
- **Mortgages**: Based on homeownership rates by income quintile

Loan balances reflect realistic payment progress (typically 10-95% of original loan amount remaining).

## Transaction Generation

### Daily Transaction Limits

Transactions are generated with realistic daily frequency:

- **Per Day Maximum**: Up to 6 transactions per day per account
- **Distribution**:
  - Checking accounts: Average 2-4 transactions per day
  - Credit cards: Average 0-2 transactions per day
  - Savings accounts: Rare transactions (approximately once per week)

### Spending Categories

Transaction categories follow the BLS Consumer Expenditure Survey distribution:

- **Housing**: 32.9% (includes mortgage/rent payments handled separately)
- **Transportation**: 17.0% (gas, auto payments, insurance)
- **Food**: 12.9% (groceries and restaurants)
- **Insurance/Pensions**: 12.4%
- **Healthcare**: 8.0%
- **Entertainment**: 4.7%
- **Other**: 12.1%

Source: [BLS Consumer Expenditure Surveys](https://www.bls.gov/cex/)

### Category Implementation

Categories use Plaid's hierarchical taxonomy:
- Primary category: e.g., "Food and Drink"
- Detailed category: e.g., "Groceries"
- Format: `["Food and Drink", "Groceries"]`

### Recurring Transactions

- **Payroll Deposits**: Biweekly or monthly based on income
- **Subscriptions**: 0-8 per user, monthly recurring
- **Mortgage Payments**: Monthly, 5.9% of disposable income
- **Rent Payments**: Monthly, 25-30% of gross income
- **Loan Payments**: Monthly payments for auto and student loans

### Transaction Amounts

Amount ranges vary by category to reflect realistic spending:

- Groceries: $20-$150
- Restaurants: $8-$80
- Gas: $30-$80
- Healthcare: $15-$200
- Insurance: $50-$300
- Shopping: $10-$500
- Entertainment: $5-$50
- Utilities: $50-$250

## Liability Generation

### Credit Card Liabilities

- **APR**: 15-25% (typical range)
- **Minimum Payment**: 1-3% of balance or $25-50 minimum
- **Payment Behavior**: Based on user's assigned payment behavior group
- **Overdue Status**: 10% of users flagged as overdue

### Mortgage Liabilities

Includes all Plaid-compatible fields:
- Origination date
- Original principal balance (3-5x annual income)
- Interest rate (3-7%)
- Next payment due date
- Escrow balance
- Property address

### Auto Loan Liabilities

- Original principal balance: $15,000-$40,000
- Interest rate: 3-12%
- Remaining balance: 20-80% of original (reflects payment progress)

### Student Loan Liabilities

- Original principal balance: $10,000-$60,000
- Interest rate: 3-8%
- Remaining balance: 10-70% of original
- Guarantor: FEDERAL, PRIVATE, or STATE

## Demographic Distributions

### Homeownership Rates by Income Quintile

Mortgage accounts are assigned based on income quintile with the following homeownership rates:

- 20th percentile (bottom 20%): 44%
- 40th percentile: 58%
- 60th percentile: 62%
- 80th percentile: 75%
- 100th percentile (top 20%): 87%

Non-homeowners receive monthly rent payments instead of mortgage payments.

Source: [U.S. Census Bureau Housing Statistics](https://www.census.gov/topics/housing.html)

### Mortgage Payment Calculation

- **Rate**: 5.9% of disposable income (monthly)
- **Disposable Income**: Assumed to be 70% of gross income (after taxes)

Source: [Federal Reserve Economic Data](https://fred.stlouisfed.org/)

### Rent Payment Calculation

- **Rate**: 25-30% of gross monthly income
- **Frequency**: Monthly

This aligns with the common "30% rule" for housing affordability.

### Credit Card Payment Behaviors

Based on industry research:

- **11%**: Make only minimum payments
- **40-44%**: Pay balance in full each month
- **45-49%**: Pay between minimum and full (varies)

Sources:
- [Federal Reserve Consumer Credit Report](https://www.federalreserve.gov/releases/g19/)
- [Credit Card Payment Behavior Studies](https://www.consumerfinance.gov/data-research/research-reports/)

## Persona Distribution

The data generation system ensures balanced distribution across all 5 persona types used by the recommendation engine. This is critical because personas are assigned hierarchically (highest priority first), so data must be structured to allow users to match each persona tier.

### Persona Assignment Strategy

Users are assigned to persona groups **before** transaction generation to ensure their financial data matches the persona's criteria:

1. **High Utilization (Priority 1) - 20% of users**
   - Credit utilization >= 50% OR interest_charged > 0 OR minimum_payment_only OR is_overdue
   - Credit card balances set to 50-95% of limit
   - Payment behavior: 50% make only minimum payments (others partial/full)
   - Ensures this persona matches first in hierarchical assignment

2. **Variable Income (Priority 2) - 20% of users**
   - Criteria: (median_pay_gap > 45 days OR irregular_frequency) AND cash_flow_buffer < 1.0
   - Payroll frequency: Irregular (30-60 day gaps instead of regular biweekly/monthly)
   - Checking balance: 0.1-0.9 months of expenses (low cash flow buffer)
   - Credit utilization: < 50% (to avoid matching Priority 1)

3. **Subscription-Heavy (Priority 3) - 20% of users**
   - Criteria: recurring_merchants >= 3 AND (monthly_recurring >= 50 OR subscription_share >= 0.10)
   - Subscription count: 3-8 subscriptions per user
   - Subscription amounts: Minimum $50/month total (ensures monthly_recurring >= 50)
   - Credit utilization: < 50% (to avoid matching Priority 1)

4. **Savings Builder (Priority 4) - 20% of users**
   - Criteria: (savings_growth_rate >= 0.02 OR net_savings_inflow >= 200) AND all_credit_utilization < 0.30
   - Savings balance: 3-6 months of expenses
   - Savings transactions: Positive net inflow (70% deposits, 30% withdrawals, ensuring >= $200/month)
   - Credit utilization: < 30% (required to match this persona)

5. **General Wellness (Default) - 20% of users**
   - Users who don't match any other persona criteria
   - Reasonable financial patterns: moderate credit utilization, regular income, balanced savings

### Implementation Details

The persona assignment happens in two phases:

1. **Pre-Transaction Assignment**: `assign_persona_groups_to_users()` assigns persona groups to users before transactions are generated
2. **Transaction Generation**: `generate_transactions()` uses the persona group to:
   - Generate appropriate subscription counts and amounts
   - Create irregular payroll patterns for Variable Income users
   - Generate positive savings inflow for Savings Builder users
3. **Post-Transaction Adjustment**: `apply_diversity_strategy()` uses persona groups to:
   - Set credit utilization levels
   - Adjust checking balances for cash flow buffer
   - Set savings balances and ensure positive growth

### Validation

After data generation, persona assignment is validated by running:
```bash
python src/personas/assign_all.py
```

Expected distribution (for default 200 users: 100 constructed + 100 unconstructed):
- Constructed users (100 total, 20 per persona):
  - High Utilization: 20 users
  - Variable Income: 20 users
  - Subscription-Heavy: 20 users
  - Savings Builder: 20 users
  - General Wellness: 20 users
- Unconstructed users: 100 users (randomly generated, no persona assignment)

### Why This Matters

The hierarchical persona assignment means Priority 1 (High Utilization) and Priority 2 (Variable Income) will match users first. Without controlled distribution, these personas would match too many users, leaving no users for Priority 3-4 or the default persona. By explicitly assigning users to persona groups and generating data that matches each persona's criteria, we ensure:

- Balanced distribution across all personas
- Each persona has sufficient users for testing recommendations
- Realistic financial patterns that match persona definitions
- Proper validation of the recommendation engine's persona matching logic

## Data Sources

### Plaid Documentation

- [Plaid Transactions API Documentation](https://plaid.com/docs/api/products/transactions/)
- [Plaid Transactions Overview](https://plaid.com/docs/transactions/)
- [Plaid Categories API](https://plaid.com/docs/api/products/transactions/#categoriesget)

### Government and Economic Data

- [BLS Consumer Expenditure Surveys](https://www.bls.gov/cex/)
- [Federal Reserve Survey of Consumer Finances](https://www.federalreserve.gov/econres/scfindex.htm)
- [U.S. Census Bureau Housing Statistics](https://www.census.gov/topics/housing.html)
- [Federal Reserve Economic Data (FRED)](https://fred.stlouisfed.org/)

### Financial Industry Research

- [Federal Reserve Consumer Credit Report](https://www.federalreserve.gov/releases/g19/)
- [Consumer Financial Protection Bureau Research](https://www.consumerfinance.gov/data-research/research-reports/)

## Data Generation Process

### Step 1: User Generation

1. Generate user profiles with income levels
2. Calculate income quintiles for demographic distribution
3. Assign homeownership status based on income quintile

### Step 2: Account Generation

1. Create checking account (always)
2. Create savings account (70% probability)
3. Generate 0-6 credit cards with weighted distribution
4. Generate auto loans (45% of users)
5. Generate student loans (25% of users)
6. Generate mortgages (based on homeownership status)

### Step 3: Transaction Generation

1. For each account, iterate day-by-day over the time period
2. Determine daily transaction count (0-6 per account)
3. Ensure special transaction days (payroll, subscriptions, mortgage/rent) get at least 1 transaction
4. Assign categories using BLS-weighted distribution
5. Generate location data for non-transfer transactions
6. Add Plaid-compatible fields (payment channel, currency, etc.)

### Step 4: Liability Generation

1. Generate credit card liabilities with payment behaviors
2. Generate mortgage liabilities with property details
3. Generate auto loan liabilities
4. Generate student loan liabilities with guarantor information

### Step 5: Persona Assignment

Before transaction generation, users are assigned to persona groups to ensure balanced distribution:

1. Assign users to persona groups (20% each)
2. Store persona_group in user profile for use during transaction generation

### Step 6: Diversity Strategy Application

Apply diversity patterns to ensure realistic variation:

- **Credit Utilization**: Controlled by persona assignment
  - High Utilization: 50-95%
  - Variable Income: 5-49%
  - Subscription-Heavy: 5-49%
  - Savings Builder: 5-29%
  - General Wellness: 5-49%
- **Savings Behavior**: 
  - Savings Builder: 3-6 months expenses with positive net inflow
  - Others: 25% active savers, 50% minimal savers, 25% no savings
- **Subscription Counts**: 
  - Subscription-Heavy: 3-8 subscriptions (minimum $50/month total)
  - Others: Varies 0-8 per user
- **Income Patterns**:
  - Variable Income: Irregular payroll (30-60 day gaps)
  - Others: Regular biweekly or monthly payroll
- **Cash Flow Buffer**:
  - Variable Income: 0.1-0.9 months expenses (low buffer)
  - Others: 0.5-2.0 months expenses (reasonable buffer)

## Data Files

Generated data is exported to the following files:

- **users.json**: User profiles with names and income
- **accounts.csv**: All account data (depository, credit, loan)
- **transactions.csv**: Transaction history with Plaid-compatible fields
- **liabilities.csv**: Liability data for credit cards and loans

Optional Parquet export available for efficient storage and faster loading.

## Usage

Generate data using the regeneration script:

```bash
# Generate 200 days of data, skip Firestore
python -m src.ingest.regenerate_data --skip-firestore --parquet

# Custom options
python -m src.ingest.regenerate_data --users 100 --days 200 --skip-firestore --parquet
```

See `docs/DATA_REGENERATION.md` for detailed usage instructions.

## Reproducibility

The data generation uses seeded random number generators (seed: 42) to ensure reproducibility. Running the generator multiple times with the same parameters will produce identical data.

## Limitations

- **No Real-Time Updates**: Data is static and does not update automatically
- **Simplified Loan Calculations**: Loan balances don't reflect exact amortization schedules
- **Fixed Distributions**: Uses average distributions rather than individual variations
- **Synthetic Merchants**: Merchant names are generated rather than real businesses

## Future Enhancements

Potential improvements to the data generation system:

- More sophisticated loan amortization calculations
- Seasonal spending patterns
- Regional variations in spending
- More detailed merchant categorization
- Integration with real Plaid data for validation

## See Also

- [Schema Documentation](docs/schema.md)
- [Data Regeneration Guide](docs/DATA_REGENERATION.md)
- [Database Schema](src/database/schema.sql)

