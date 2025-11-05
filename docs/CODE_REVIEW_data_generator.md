# Code Review: `src/ingest/data_generator.py`

## Executive Summary
This file contains a synthetic data generator for financial data. The code is generally well-structured but has several areas for improvement including code duplication, potential bugs, performance issues, and missing error handling.

## Critical Issues

### 1. **Code Duplication - Transaction Amount Logic**
**Severity:** High  
**Location:** Lines 482-497, 518-540, 554-577, 585-607

The logic for determining transaction amounts based on category is duplicated 4 times throughout the `generate_transactions` function. This violates DRY principles and makes maintenance difficult.

**Issue:**
- Same if/elif chain repeated for biweekly payroll, monthly payroll, and no payroll cases
- Any changes to amount ranges require updates in 4 places

**Recommendation:**
Extract to a helper function:
```python
def get_transaction_amount_for_category(category_legacy: str) -> float:
    """Get transaction amount range based on category."""
    category_amounts = {
        "groceries": (20.0, 150.0),
        "restaurants": (8.0, 80.0),
        "gas": (30.0, 80.0),
        "healthcare": (15.0, 200.0),
        "insurance": (50.0, 300.0),
        "utilities": (50.0, 250.0),
        "bills": (30.0, 150.0),
        "shopping": (10.0, 300.0),
        "entertainment": (5.0, 50.0),
    }
    min_amount, max_amount = category_amounts.get(category_legacy, (10.0, 200.0))
    return -round(random.uniform(min_amount, max_amount), 2)
```

### 2. **Bug: Subscription Date Calculation Logic**
**Severity:** Medium  
**Location:** Lines 349-355

The subscription date calculation iterates through every day, which is inefficient. More importantly, the logic for determining subscription dates is flawed.

**Issue:**
- The loop checks `days_since_sub` but `sub_info["next_date"]` is being updated later (line 644), so initial calculation may be incorrect
- The ±3 day window logic doesn't align with how subscriptions are actually processed later (line 637)

**Recommendation:**
Calculate subscription dates more efficiently and ensure consistency with processing logic.

### 3. **Potential Overflow: Transaction Dates Generation**
**Severity:** Medium  
**Location:** Lines 307-309, 321-355

The loop `while current_payment_date <= datetime.now()` and similar loops could theoretically run indefinitely if `start_date` is incorrectly set, though in practice this is unlikely.

**Recommendation:**
Add maximum iteration limits or validate date ranges.

### 4. **Inefficient Date Calculation**
**Severity:** Medium  
**Location:** Lines 319-355

The code iterates through every single day to find special transaction dates. For 200 days, this creates 200+ iterations per special date type.

**Issue:**
```python
temp_date = start_date
while temp_date <= datetime.now():
    # Check if this date matches criteria
    temp_date += timedelta(days=1)
```

**Recommendation:**
Calculate dates mathematically instead of iterating:
```python
# For biweekly payroll
if payroll_frequency == "biweekly":
    current = payroll_start
    while current <= datetime.now():
        if current >= start_date:
            special_transaction_dates.add(current.date())
        current += timedelta(days=14)
```

## Major Issues

### 5. **Missing Error Handling**
**Severity:** Medium  
**Location:** Throughout

The code lacks error handling for:
- File I/O operations (export functions)
- Dictionary key access (e.g., `user_profile["income"]`)
- Empty lists (e.g., `random.sample()` on empty list)
- Division by zero (e.g., `minimum_payment_amount` calculation)

**Recommendation:**
Add try/except blocks for critical operations and validate inputs.

### 6. **Magic Numbers**
**Severity:** Low-Medium  
**Location:** Throughout

Many magic numbers scattered throughout code:
- Line 96: `0.5, 2.0` (checking balance multipliers)
- Line 110: `0, 6.0` (savings balance multipliers)
- Line 131: `0.10, 0.30` (credit limit percentages)
- Line 290: `0.70` (disposable income percentage)
- Line 292: `0.059` (mortgage payment percentage)

**Recommendation:**
Extract to named constants at module level:
```python
# Financial ratios
CHECKING_BALANCE_MULTIPLIER_MIN = 0.5
CHECKING_BALANCE_MULTIPLIER_MAX = 2.0
SAVINGS_BALANCE_MULTIPLIER_MIN = 0.0
SAVINGS_BALANCE_MULTIPLIER_MAX = 6.0
CREDIT_LIMIT_INCOME_MIN = 0.10
CREDIT_LIMIT_INCOME_MAX = 0.30
DISPOSABLE_INCOME_RATIO = 0.70
MORTGAGE_PAYMENT_RATIO = 0.059
```

### 7. **Complex Conditional Logic**
**Severity:** Medium  
**Location:** Lines 504-645

The transaction generation logic for checking accounts has deeply nested conditionals that are hard to follow:
- Payroll checks (biweekly vs monthly)
- Mortgage/rent checks
- Subscription checks
- Regular expense generation

**Issue:**
The logic processes transactions sequentially, but later checks (mortgage, rent, subscriptions) can overwrite previous amounts, making the final transaction unpredictable.

**Recommendation:**
Refactor to use a priority-based approach or separate the transaction generation into distinct phases.

### 8. **Transaction Overwriting Bug**
**Severity:** Medium  
**Location:** Lines 615-645

When checking for mortgage, rent, or subscription payments, the code overwrites the `amount` variable that was already set for regular expenses. This means:
- A transaction date might have a regular expense amount calculated
- Then mortgage/rent/subscription check overwrites it
- The transaction ends up with the last matched payment type

**Recommendation:**
Use separate transaction generation for recurring payments, or process them in order of priority.

### 9. **Inefficient User Lookup**
**Severity:** Low-Medium  
**Location:** Line 964, 1177

Code uses `next()` with generator expression to find user by ID:
```python
user_income = next((u["income"] for u in users if u["user_id"] == user_id), 50000)
```

This is O(n) for each lookup. For multiple lookups, this becomes inefficient.

**Recommendation:**
Create a user lookup dictionary:
```python
user_lookup = {u["user_id"]: u for u in users}
```

## Code Quality Issues

### 10. **Inconsistent Variable Naming**
**Severity:** Low  
**Location:** Throughout

- `category_legacy` - unclear why "legacy"
- `tx_date` - abbreviation
- `sub_info` - abbreviation
- `util_group` - abbreviation

**Recommendation:**
Use more descriptive names: `category_type`, `transaction_date`, `subscription_info`, `utilization_group`

### 11. **Long Functions**
**Severity:** Low-Medium  
**Location:** `generate_transactions()` (lines 207-706)

The `generate_transactions` function is ~500 lines long, making it hard to maintain and test.

**Recommendation:**
Break into smaller functions:
- `_calculate_special_transaction_dates()`
- `_generate_transaction_dates()`
- `_generate_transaction_amount()`
- `_create_transaction_record()`

### 12. **Missing Type Hints**
**Severity:** Low  
**Location:** Throughout

Some helper functions and internal variables lack type hints.

**Recommendation:**
Add complete type hints for better IDE support and type checking.

### 13. **Hardcoded Date Logic**
**Severity:** Low  
**Location:** Lines 327, 336, 344, 617, 627

Hardcoded `% 30` for monthly payments doesn't account for months with different day counts.

**Issue:**
```python
if days_since_mortgage_start >= 0 and days_since_mortgage_start % 30 == 0:
```

**Recommendation:**
Use `dateutil.relativedelta` or similar for proper month arithmetic.

### 14. **Potential Division by Zero**
**Severity:** Medium  
**Location:** Line 753

```python
last_payment_amount = round(minimum_payment_amount * random.uniform(1.5, balance / minimum_payment_amount if minimum_payment_amount > 0 else 5.0), 2)
```

While there's a check, the logic is complex and could be clearer.

**Recommendation:**
Extract to clearer conditional logic.

### 15. **Inconsistent Rounding**
**Severity:** Low  
**Location:** Throughout

Some values use `round(..., 2)`, others use `round(..., 3)`. Consider standardizing to 2 decimal places for currency.

## Performance Issues

### 16. **Inefficient Date Iteration**
**Severity:** Medium  
**Location:** Lines 319-355

As mentioned in issue #4, iterating day-by-day for special dates is inefficient.

### 17. **Multiple List Copies**
**Severity:** Low  
**Location:** Line 874

```python
users_shuffled = users.copy()
```

This creates a copy, but for large user lists, consider using `random.sample()` if order doesn't matter elsewhere.

## Best Practices

### 18. **Missing Input Validation**
**Severity:** Medium  
**Location:** Function parameters

Functions don't validate inputs (e.g., negative counts, None values, empty lists).

**Recommendation:**
Add input validation at function entry points.

### 19. **Magic Strings**
**Severity:** Low  
**Location:** Throughout

String literals used for account types, subtypes, etc.:
- `"depository"`, `"credit"`, `"loan"`
- `"checking"`, `"savings"`, `"credit card"`
- `"min_only"`, `"full"`, `"partial"`

**Recommendation:**
Use Enum classes:
```python
from enum import Enum

class AccountType(Enum):
    DEPOSITORY = "depository"
    CREDIT = "credit"
    LOAN = "loan"
```

### 20. **Missing Docstring Examples**
**Severity:** Low  
**Location:** Function docstrings

Docstrings lack usage examples for complex functions.

### 21. **Seeding Issues**
**Severity:** Low  
**Location:** Lines 23-25

Global seeding affects all random operations. If this module is imported elsewhere, it could affect other code.

**Recommendation:**
Consider using a Random instance instead of the global random module, or document the seeding behavior clearly.

## Positive Aspects

1. **Good documentation** - Functions have clear docstrings
2. **Well-structured** - Logical separation of concerns
3. **Realistic data** - Good use of BLS data and realistic financial patterns
4. **Type hints** - Most functions have type hints
5. **Comprehensive** - Handles many edge cases in financial data

## Recommendations Priority

### High Priority
1. Fix code duplication (#1)
2. Fix transaction overwriting bug (#8)
3. Add error handling (#5)
4. Optimize date calculations (#4, #16)

### Medium Priority
5. Extract magic numbers (#6)
6. Refactor complex conditionals (#7)
7. Optimize user lookups (#9)
8. Break down long functions (#11)

### Low Priority
9. Improve naming (#10)
10. Add Enums (#19)
11. Standardize rounding (#15)
12. Add input validation (#18)

## Testing Recommendations

Given the complexity of this code, consider adding:
1. Unit tests for each generator function
2. Integration tests for the full generation pipeline
3. Property-based tests (e.g., verify distributions match expected percentages)
4. Edge case tests (empty lists, zero values, date boundaries)

## Summary

The code is functional and well-documented but needs refactoring to improve maintainability, fix bugs, and optimize performance. The most critical issues are the code duplication and the transaction overwriting bug which could lead to incorrect data generation.

