"""Synthetic data generator for SpendSense.

This module generates realistic synthetic financial data for N users including:
- User profiles with names and income levels
- Bank accounts (checking, savings, credit cards)
- Transaction history over specified number of days
- Credit card liabilities

All data follows Plaid-style schema and includes realistic patterns like
recurring subscriptions, payroll deposits, and varied credit utilization.
"""

import json
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from faker import Faker
from src.utils.plaid_categories import get_category_for_merchant

# Initialize Faker with deterministic seed
fake = Faker()
Faker.seed(42)
random.seed(42)

# Financial ratios and constants
CHECKING_BALANCE_MULTIPLIER_MIN = 0.5
CHECKING_BALANCE_MULTIPLIER_MAX = 2.0
SAVINGS_BALANCE_MULTIPLIER_MIN = 0.0
SAVINGS_BALANCE_MULTIPLIER_MAX = 6.0
CREDIT_LIMIT_INCOME_MIN = 0.10
CREDIT_LIMIT_INCOME_MAX = 0.30
DISPOSABLE_INCOME_RATIO = 0.70
MORTGAGE_PAYMENT_RATIO = 0.059
RENT_INCOME_MIN = 0.25
RENT_INCOME_MAX = 0.30
MONTHS_PER_YEAR = 12
BIWEEKLY_PAY_PERIODS = 26
CURRENCY_DECIMAL_PLACES = 2

# US Metro areas for location coherence (top 20 by population)
METRO_AREAS = [
    {"name": "New York", "lat": 40.7128, "lon": -74.0060, "weight": 0.15},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437, "weight": 0.12},
    {"name": "Chicago", "lat": 41.8781, "lon": -87.6298, "weight": 0.08},
    {"name": "Dallas", "lat": 32.7767, "lon": -96.7970, "weight": 0.06},
    {"name": "Houston", "lat": 29.7604, "lon": -95.3698, "weight": 0.06},
    {"name": "Washington DC", "lat": 38.9072, "lon": -77.0369, "weight": 0.05},
    {"name": "Philadelphia", "lat": 39.9526, "lon": -75.1652, "weight": 0.05},
    {"name": "Miami", "lat": 25.7617, "lon": -80.1918, "weight": 0.05},
    {"name": "Atlanta", "lat": 33.7490, "lon": -84.3880, "weight": 0.05},
    {"name": "Boston", "lat": 42.3601, "lon": -71.0589, "weight": 0.04},
    {"name": "Phoenix", "lat": 33.4484, "lon": -112.0740, "weight": 0.04},
    {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194, "weight": 0.04},
    {"name": "Detroit", "lat": 42.3314, "lon": -83.0458, "weight": 0.03},
    {"name": "Seattle", "lat": 47.6062, "lon": -122.3321, "weight": 0.03},
    {"name": "Minneapolis", "lat": 44.9778, "lon": -93.2650, "weight": 0.03},
    {"name": "San Diego", "lat": 32.7157, "lon": -117.1611, "weight": 0.03},
    {"name": "Tampa", "lat": 27.9506, "lon": -82.4572, "weight": 0.03},
    {"name": "Denver", "lat": 39.7392, "lon": -104.9903, "weight": 0.03},
    {"name": "St. Louis", "lat": 38.6270, "lon": -90.1994, "weight": 0.02},
    {"name": "Portland", "lat": 45.5152, "lon": -122.6784, "weight": 0.02},
]

# Seasonal spending multipliers (month -> category -> multiplier)
SEASONAL_MULTIPLIERS = {
    1: {"utilities": 1.3},  # January - winter heating
    2: {"utilities": 1.3, "restaurants": 1.2},  # February - heating, Valentine's Day
    7: {"utilities": 1.2},  # July - summer cooling
    8: {"utilities": 1.2},  # August - summer cooling
    11: {"groceries": 1.3, "shopping": 1.5},  # November - Thanksgiving, Black Friday
    12: {"groceries": 1.4, "restaurants": 1.3, "shopping": 1.8},  # December - holidays
}


def get_day_of_week_multiplier(date: datetime, category: str) -> float:
    """Get spending multiplier based on day of week.
    
    Args:
        date: Transaction date
        category: Category type (e.g., "groceries", "restaurants")
        
    Returns:
        Multiplier to apply to transaction amount
    """
    weekday = date.weekday()  # 0=Monday, 6=Sunday
    
    if category in ["groceries", "shopping"]:
        # More shopping on weekends
        return 1.3 if weekday in [5, 6] else 0.9
    elif category == "restaurants":
        # More restaurants on Friday-Sunday
        return 1.4 if weekday in [4, 5, 6] else 0.85
    
    return 1.0


def generate_users(count: int = 200) -> List[Dict[str, Any]]:
    """Generate synthetic user profiles.
    
    Args:
        count: Number of users to generate (default: 200)
        
    Returns:
        List of user dictionaries with user_id, name, income, created_at
    """
    if count <= 0:
        raise ValueError("count must be positive")
    
    users = []
    base_date = datetime(2024, 1, 1)
    
    for i in range(1, count + 1):
        # Generate user ID
        user_id = f"user_{i:03d}"
        
        # Generate name using Faker (no real PII)
        name = fake.name()
        
        # Assign varied income levels ($30K-$150K)
        # Use weighted distribution: more users in middle range
        income_choice = random.choices(
            ["low", "medium", "high"],
            weights=[0.3, 0.5, 0.2]
        )[0]
        
        if income_choice == "low":
            income = random.randint(30000, 50000)
        elif income_choice == "medium":
            income = random.randint(50000, 100000)
        else:  # high
            income = random.randint(100000, 150000)
        
        # Assign user to a metro area for location coherence
        metro_area = random.choices(
            METRO_AREAS,
            weights=[m["weight"] for m in METRO_AREAS]
        )[0]
        
        # Create user
        user = {
            "user_id": user_id,
            "name": name,
            "income": income,
            "created_at": (base_date + timedelta(days=random.randint(0, 30))).isoformat(),
            # Generate employer name for payroll transactions
            "employer_name": fake.company() + " Payroll",
            "metro_area": metro_area
        }
        users.append(user)
    
    return users


def generate_accounts(user_id: str, user_profile: Dict[str, Any], homeownership_status: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Generate accounts for a user.
    
    Per user:
    - 1 checking account (always)
    - 0-1 savings account (70% probability)
    - 0-6 credit cards (weighted distribution)
    - 0-1 auto loan (40-50% probability)
    - 0-1 student loan (20-30% probability)
    - 0-1 mortgage (based on homeownership status)
    
    Args:
        user_id: User identifier
        user_profile: User profile dict with income
        homeownership_status: Dict with 'is_homeowner' boolean and 'income_quintile' (optional)
        
    Returns:
        List of account dictionaries matching schema
    """
    accounts = []
    account_counter = 1
    
    # Always create checking account
    checking_balance = user_profile["income"] / MONTHS_PER_YEAR * random.uniform(
        CHECKING_BALANCE_MULTIPLIER_MIN, CHECKING_BALANCE_MULTIPLIER_MAX
    )
    accounts.append({
        "account_id": f"acc_{user_id}_{account_counter:02d}",
        "user_id": user_id,
        "type": "depository",
        "subtype": "checking",
        "balance": round(checking_balance, 2),
        "limit": None,
        "mask": f"{random.randint(1000, 9999):04d}"
    })
    account_counter += 1
    
    # 70% probability of savings account
    if random.random() < 0.7:
        savings_balance = user_profile["income"] / MONTHS_PER_YEAR * random.uniform(
            SAVINGS_BALANCE_MULTIPLIER_MIN, SAVINGS_BALANCE_MULTIPLIER_MAX
        )
        accounts.append({
            "account_id": f"acc_{user_id}_{account_counter:02d}",
            "user_id": user_id,
            "type": "depository",
            "subtype": "savings",
            "balance": round(savings_balance, 2),
            "limit": None,
            "mask": f"{random.randint(1000, 9999):04d}"
        })
        account_counter += 1
    
    # Credit cards: 0-6 cards per user with weighted distribution
    # Distribution: 0 cards (15%), 1 card (25%), 2 cards (25%), 3 cards (20%), 4 cards (10%), 5 cards (3%), 6 cards (2%)
    if random.random() < 0.85:  # 85% have at least one card
        num_cards = random.choices(
            [1, 2, 3, 4, 5, 6],
            weights=[0.25, 0.25, 0.20, 0.10, 0.03, 0.02]
        )[0]
        for _ in range(num_cards):
            # Credit limit based on income (typically 10-30% of annual income)
            credit_limit = user_profile["income"] * random.uniform(
                CREDIT_LIMIT_INCOME_MIN, CREDIT_LIMIT_INCOME_MAX
            )
            # Balance will be set later based on utilization strategy
            balance = 0  # Will be adjusted in diversity strategy
            
            accounts.append({
                "account_id": f"acc_{user_id}_{account_counter:02d}",
                "user_id": user_id,
                "type": "credit",
                "subtype": "credit card",
                "balance": round(balance, 2),
                "limit": round(credit_limit, 2),
                "mask": f"{random.randint(1000, 9999):04d}"
            })
            account_counter += 1
    
    # Auto loan: 40-50% of users
    if random.random() < 0.45:  # 45% average
        # Auto loan amount: typically $15K-$40K, balance reduces over time
        # For simplicity, use remaining balance (simulate some payments made)
        original_loan_amount = random.uniform(15000, 40000)
        # Assume loan is 20-80% paid off
        remaining_balance = original_loan_amount * random.uniform(0.20, 0.80)
        loan_limit = original_loan_amount  # Original loan amount
        
        accounts.append({
            "account_id": f"acc_{user_id}_{account_counter:02d}",
            "user_id": user_id,
            "type": "loan",
            "subtype": "auto",
            "balance": round(remaining_balance, 2),
            "limit": round(loan_limit, 2),
            "mask": f"{random.randint(1000, 9999):04d}"
        })
        account_counter += 1
    
    # Student loan: 20-30% of users
    if random.random() < 0.25:  # 25% average
        # Student loan amount: typically $10K-$60K
        original_loan_amount = random.uniform(10000, 60000)
        # Assume loan is 10-70% paid off
        remaining_balance = original_loan_amount * random.uniform(0.10, 0.70)
        loan_limit = original_loan_amount
        
        accounts.append({
            "account_id": f"acc_{user_id}_{account_counter:02d}",
            "user_id": user_id,
            "type": "loan",
            "subtype": "student",
            "balance": round(remaining_balance, 2),
            "limit": round(loan_limit, 2),
            "mask": f"{random.randint(1000, 9999):04d}"
        })
        account_counter += 1
    
    # Mortgage: Only if homeowner (determined by income quintile)
    if homeownership_status and homeownership_status.get("is_homeowner", False):
        # Mortgage amount: typically 3-5x annual income, balance reduces over time
        original_mortgage_amount = user_profile["income"] * random.uniform(3.0, 5.0)
        # Assume mortgage is 5-30% paid off (homeowner for a while)
        remaining_balance = original_mortgage_amount * random.uniform(0.70, 0.95)
        loan_limit = original_mortgage_amount
        
        accounts.append({
            "account_id": f"acc_{user_id}_{account_counter:02d}",
            "user_id": user_id,
            "type": "loan",
            "subtype": "mortgage",
            "balance": round(remaining_balance, 2),
            "limit": round(loan_limit, 2),
            "mask": f"{random.randint(1000, 9999):04d}"
        })
        account_counter += 1
    
    return accounts


def _get_transaction_amount_for_category(category_type: str, user_income: float = 50000) -> float:
    """Get transaction amount based on category type and user income.
    
    Args:
        category_type: Category string (e.g., "groceries", "restaurants")
        user_income: User's annual income for scaling amounts
        
    Returns:
        Negative transaction amount (expense)
    """
    # Base amounts for median income ($50K)
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
    
    # Calculate income scaling factor (0.7x to 1.8x based on income)
    # $30K income -> 0.7x, $50K -> 1.0x, $150K -> 1.8x
    income_scale = 0.7 + (user_income - 30000) / (150000 - 30000) * 1.1
    income_scale = max(0.7, min(1.8, income_scale))
    
    min_amount, max_amount = category_amounts.get(category_type, (10.0, 200.0))
    scaled_min = min_amount * income_scale
    scaled_max = max_amount * income_scale
    
    return -round(random.uniform(scaled_min, scaled_max), CURRENCY_DECIMAL_PLACES)


def _calculate_recurring_dates(
    start_date: datetime,
    end_date: datetime,
    initial_date: datetime,
    frequency_days: int,
    window_days: int = 0
) -> set:
    """Calculate recurring transaction dates efficiently.
    
    Args:
        start_date: Start of transaction period
        end_date: End of transaction period
        initial_date: First occurrence date
        frequency_days: Days between occurrences
        window_days: Window around date (for subscriptions, default 0)
        
    Returns:
        Set of dates (as date objects) when transactions should occur
    """
    dates = set()
    current = initial_date
    
    # Find first occurrence within range
    while current < start_date:
        current += timedelta(days=frequency_days)
    
    # Add all occurrences within range
    while current <= end_date:
        if window_days > 0:
            # Add dates within window
            for offset in range(-window_days, window_days + 1):
                window_date = current + timedelta(days=offset)
                if start_date <= window_date <= end_date:
                    dates.add(window_date.date())
        else:
            dates.add(current.date())
        current += timedelta(days=frequency_days)
    
    return dates


def generate_transactions(
    account_id: str,
    account_type: str,
    account_subtype: str,
    user_profile: Dict[str, Any],
    account_info: Dict[str, Any],
    days: int = 180,
    homeownership_status: Dict[str, Any] = None,
    persona_group: str = None
) -> List[Dict[str, Any]]:
    """Generate transactions for an account.
    
    Args:
        account_id: Account identifier
        account_type: "depository" or "credit"
        account_subtype: "checking", "savings", or "credit card"
        user_profile: User profile dict with income
        account_info: Account dict with balance, limit
        days: Number of days of history to generate
        homeownership_status: Dict with homeownership information
        persona_group: Persona group assigned to user (optional)
        
    Returns:
        List of transaction dictionaries
    """
    transactions = []
    start_date = datetime.now() - timedelta(days=days)
    transaction_counter = 1
    
    # Common merchant categories
    categories = {
        "groceries": ["Whole Foods", "Kroger", "Safeway", "Trader Joe's", "Walmart"],
        "restaurants": ["Starbucks", "McDonald's", "Chipotle", "Olive Garden", "Pizza Hut"],
        "bills": ["Electric Company", "Water Utility", "Internet Provider", "Phone Company"],
        "shopping": ["Amazon", "Target", "Best Buy", "Macy's", "Home Depot"],
        "entertainment": ["Netflix", "Spotify", "Disney+", "Hulu", "YouTube Premium"],
        "gas": ["Shell", "Exxon", "Chevron", "BP"],
        "subscriptions": ["Netflix", "Spotify", "Disney+", "Hulu", "YouTube Premium", 
                          "Adobe Creative Cloud", "Microsoft 365", "Gym Membership"],
        "healthcare": ["CVS Pharmacy", "Walgreens", "Doctor's Office", "Dental Care", "Hospital"],
        "insurance": ["Health Insurance", "Auto Insurance", "Home Insurance", "Life Insurance"],
        "utilities": ["Electric Company", "Water Utility", "Gas Utility", "Sewer Service"]
    }
    
    # Subscription merchants (for recurring patterns)
    subscription_merchants = categories["subscriptions"]
    
    # Generate recurring subscriptions (monthly) - needed before date generation
    subscriptions = {}
    if account_type == "depository" and account_subtype == "checking":
        if persona_group == "subscription_heavy":
            # Priority 3: >= 3 subscriptions AND monthly_recurring >= 50
            num_subscriptions = random.randint(3, 8)
            min_per_sub = max(5.99, 50.0 / num_subscriptions)  # Ensure total >= 50
            
            # Use unique merchant selection
            available_merchants = subscription_merchants.copy()
            for _ in range(num_subscriptions):
                if not available_merchants:
                    break
                merchant = random.choice(available_merchants)
                available_merchants.remove(merchant)
                amount = round(random.uniform(min_per_sub, 29.99), 2)
                subscriptions[merchant] = {
                    "amount": amount,
                    "frequency": "monthly",
                    "next_date": start_date + timedelta(days=random.randint(0, 30))
                }
        else:
            # Other personas: random distribution
            num_subscriptions = random.randint(0, 8)
            
            # Use unique merchant selection
            available_merchants = subscription_merchants.copy()
            for _ in range(num_subscriptions):
                if not available_merchants:
                    break
                merchant = random.choice(available_merchants)
                available_merchants.remove(merchant)
                amount = round(random.uniform(5.99, 29.99), 2)
                subscriptions[merchant] = {
                    "amount": amount,
                    "frequency": "monthly",
                    "next_date": start_date + timedelta(days=random.randint(0, 30))
                }
    
    # Generate payroll deposits (for checking accounts) - needed before date generation
    payroll_amount = None
    payroll_frequency = None
    payroll_start = None
    employer_name = user_profile.get("employer_name", "PAYROLL DEPOSIT")
    if account_type == "depository" and account_subtype == "checking":
        if persona_group == "variable_income":
            # Priority 2: Irregular frequency OR gaps > 45 days
            payroll_frequency = "irregular"
            base_payroll = user_profile["income"] / MONTHS_PER_YEAR
            # Add small variation (±1-2%) for realism
            variation = random.uniform(0.98, 1.02)
            payroll_amount = base_payroll * variation
            payroll_start = start_date + timedelta(days=random.randint(0, 29))
        else:
            # Regular payroll
            payroll_frequency = random.choice(["biweekly", "monthly"])
            if payroll_frequency == "biweekly":
                base_payroll = user_profile["income"] / BIWEEKLY_PAY_PERIODS
            else:
                base_payroll = user_profile["income"] / MONTHS_PER_YEAR
            # Add small variation (±1-2%) for realism
            variation = random.uniform(0.98, 1.02)
            payroll_amount = base_payroll * variation
            payroll_amount = round(payroll_amount, CURRENCY_DECIMAL_PLACES)
            # Ensure payroll lands on weekdays (Monday-Friday)
            start_offset = random.randint(0, 13 if payroll_frequency == "biweekly" else 29)
            payroll_start = start_date + timedelta(days=start_offset)
            # Adjust to nearest weekday if needed
            while payroll_start.weekday() >= 5:  # Saturday = 5, Sunday = 6
                payroll_start += timedelta(days=1)
    
    # Generate mortgage/rent payments (for checking accounts) - needed before date generation
    mortgage_payment = None
    rent_payment = None
    mortgage_start = None
    rent_start = None
    
    if account_type == "depository" and account_subtype == "checking" and homeownership_status:
        if homeownership_status.get("is_homeowner", False):
            # Mortgage payment: 5.9% of disposable income (monthly)
            # Disposable income ≈ 70% of gross income (after taxes)
            disposable_income = user_profile["income"] * DISPOSABLE_INCOME_RATIO
            monthly_disposable = disposable_income / MONTHS_PER_YEAR
            mortgage_payment = round(monthly_disposable * MORTGAGE_PAYMENT_RATIO, CURRENCY_DECIMAL_PLACES)
            mortgage_start = start_date + timedelta(days=random.randint(0, 29))
        else:
            # Rent payment: 25-30% of gross income (monthly)
            monthly_income = user_profile["income"] / MONTHS_PER_YEAR
            rent_payment = round(monthly_income * random.uniform(RENT_INCOME_MIN, RENT_INCOME_MAX), CURRENCY_DECIMAL_PLACES)
            rent_start = start_date + timedelta(days=random.randint(0, 29))
    
    # Generate transaction dates: up to 2 transactions per day for most accounts
    # For loan accounts, generate monthly payments only
    if account_type == "loan":
        # Loan accounts get monthly payment transactions only
        payment_start = start_date + timedelta(days=random.randint(0, 29))
        current_payment_date = payment_start
        transaction_dates = []
        while current_payment_date <= datetime.now():
            transaction_dates.append(current_payment_date)
            current_payment_date += timedelta(days=30)
    else:
        # For other accounts, generate dates based on daily transaction limits
        transaction_dates = []
        current_date = start_date
        
        # Pre-calculate special transaction dates that must have at least 1 transaction
        special_transaction_dates = set()
        payroll_dates_set = set()  # Track payroll dates separately for payroll check
        if account_type == "depository" and account_subtype == "checking":
            # Calculate payroll dates efficiently
            if payroll_amount and payroll_frequency:
                if payroll_frequency == "irregular":
                    # Generate irregular payroll dates (30-60 day gaps > 45)
                    payroll_dates = set()
                    current_pay_date = payroll_start
                    previous_pay_date = None
                    while current_pay_date <= datetime.now():
                        # Ensure payroll lands on weekdays (Monday-Friday)
                        while current_pay_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                            current_pay_date += timedelta(days=1)
                        
                        # Ensure minimum gap of 28 days from previous payroll date
                        if previous_pay_date is None or (current_pay_date.date() - previous_pay_date).days >= 28:
                            payroll_dates.add(current_pay_date.date())
                            previous_pay_date = current_pay_date.date()
                        
                        gap_days = random.randint(30, 60)  # Irregular gaps
                        current_pay_date += timedelta(days=gap_days)
                    special_transaction_dates.update(payroll_dates)
                    payroll_dates_set.update(payroll_dates)  # Track separately
                else:
                    frequency_days = 14 if payroll_frequency == "biweekly" else 30
                    payroll_dates = _calculate_recurring_dates(
                        start_date, datetime.now(), payroll_start, frequency_days
                    )
                    # Adjust payroll dates to weekdays (Monday-Friday)
                    # and ensure minimum gap between adjusted dates
                    adjusted_payroll_dates = []
                    previous_adjusted_date = None
                    for pay_date in sorted(list(payroll_dates)):
                        # Convert date back to datetime for weekday check
                        pay_datetime = datetime.combine(pay_date, datetime.min.time())
                        # Adjust to nearest weekday if needed
                        while pay_datetime.weekday() >= 5:  # Saturday = 5, Sunday = 6
                            pay_datetime += timedelta(days=1)
                        
                        # Ensure minimum gap of 13 days from previous adjusted payroll date
                        # (biweekly is 14 days, so 13-day minimum prevents consecutive/nearby days)
                        if previous_adjusted_date is None or (pay_datetime.date() - previous_adjusted_date).days >= 13:
                            adjusted_payroll_dates.append(pay_datetime.date())
                            previous_adjusted_date = pay_datetime.date()
                    
                    special_transaction_dates.update(adjusted_payroll_dates)
                    payroll_dates_set.update(adjusted_payroll_dates)  # Track separately
            
            # Calculate mortgage/rent dates efficiently
            mortgage_dates_set = set()  # Track mortgage dates separately
            rent_dates_set = set()  # Track rent dates separately
            
            if mortgage_payment and mortgage_start:
                mortgage_dates = _calculate_recurring_dates(
                    start_date, datetime.now(), mortgage_start, 30
                )
                special_transaction_dates.update(mortgage_dates)
                mortgage_dates_set.update(mortgage_dates)
            
            if rent_payment and rent_start:
                rent_dates = _calculate_recurring_dates(
                    start_date, datetime.now(), rent_start, 30
                )
                special_transaction_dates.update(rent_dates)
                rent_dates_set.update(rent_dates)
            
            # Calculate subscription dates efficiently
            for merchant, sub_info in subscriptions.items():
                subscription_dates = _calculate_recurring_dates(
                    start_date, datetime.now(), sub_info["next_date"], 30, window_days=3
                )
                special_transaction_dates.update(subscription_dates)
        
        # Generate transaction dates day by day
        while current_date <= datetime.now():
            current_date_only = current_date.date()
            is_special_day = current_date_only in special_transaction_dates
            
            # Determine how many transactions this account gets on this day (0-2)
            # Special transaction days get at least 1 transaction
            if account_type == "depository" and account_subtype == "checking":
                # Checking accounts: realistic transaction frequency (avg 0-1 per day)
                # Ensure special days get at least 1 transaction
                if is_special_day:
                    daily_tx_count = random.choices(
                        [1, 2],
                        weights=[0.70, 0.30]
                    )[0]
                else:
                    daily_tx_count = random.choices(
                        [0, 1, 2],
                        weights=[0.50, 0.35, 0.15]
                    )[0]
            elif account_type == "depository" and account_subtype == "savings":
                # Savings accounts: rare transactions (maybe once every few days)
                daily_tx_count = random.choices(
                    [0, 1],
                    weights=[0.95, 0.05]
                )[0]
            elif account_type == "credit":
                # Credit cards: moderate transactions (avg 0-2 per day)
                daily_tx_count = random.choices(
                    [0, 1, 2],
                    weights=[0.70, 0.25, 0.05]
                )[0]
            else:
                daily_tx_count = 0
            
            # Add this date multiple times if multiple transactions
            for _ in range(daily_tx_count):
                # Add some randomness to the time of day (for variety)
                day_fraction = random.uniform(0, 0.99)  # Fraction of day (0.0 to 0.99)
                transaction_date = current_date + timedelta(days=day_fraction)
                transaction_dates.append(transaction_date)
            
            current_date += timedelta(days=1)
        
        # Sort by date
        transaction_dates.sort()
    
    # BLS Consumer Expenditure Survey distribution (as % of total spending)
    # Note: Housing (32.9%) includes mortgage/rent which we handle separately
    # These weights are for non-housing expenses
    BLS_CATEGORY_WEIGHTS = {
        # Food: 12.9% of total spending
        "groceries": 0.08,  # ~8% groceries
        "restaurants": 0.05,  # ~5% restaurants (total food ~12.9%)
        
        # Transportation: 17.0% (gas, auto payments already handled separately)
        "gas": 0.04,  # Gas stations (~4% of total, rest is auto payments/insurance)
        
        # Housing-related (utilities, home maintenance): ~8% of total (rest is mortgage/rent)
        "utilities": 0.04,  # Utilities (~4% of total)
        "bills": 0.02,  # Other bills (phone, internet)
        
        # Healthcare: 8.0%
        "healthcare": 0.08,
        
        # Insurance/Pensions: 12.4% (we'll include insurance payments)
        "insurance": 0.06,  # Insurance payments
        
        # Entertainment: 4.7%
        "entertainment": 0.05,
        
        # Shopping/General Merchandise: ~12.1% other
        "shopping": 0.12,
    }
    
    # Normalize weights to sum to 1.0 for non-housing expenses
    total_weight = sum(BLS_CATEGORY_WEIGHTS.values())
    normalized_weights = {k: v / total_weight for k, v in BLS_CATEGORY_WEIGHTS.items()}
    
    # Create weighted category list for random selection
    category_list = []
    weights_list = []
    for cat, weight in normalized_weights.items():
        category_list.append(cat)
        weights_list.append(weight)
    
    # Generate transactions
    # Track which payroll/mortgage/rent dates have been processed to prevent duplicates
    processed_payroll_dates = set()
    processed_mortgage_dates = set()
    processed_rent_dates = set()
    
    for tx_date in transaction_dates:
        transaction_id = f"tx_{account_id}_{transaction_counter:06d}"
        transaction_counter += 1
        
        # Initialize variables for this transaction
        category_type = None  # Track category for clustering logic
        
        # Determine transaction type
        if account_type == "loan":
            # Loan account: monthly payment transactions
            # Calculate monthly payment based on loan balance and original amount
            original_amount = account_info.get("limit", account_info.get("balance", 0))
            current_balance = account_info.get("balance", 0)
            
            if account_subtype == "mortgage":
                # Mortgage payment already handled in checking account transactions
                # Skip generating here (mortgage payments come from checking account)
                continue
            elif account_subtype == "auto":
                # Auto loan payment: typically $200-$600/month
                monthly_payment = round(random.uniform(200, 600), CURRENCY_DECIMAL_PLACES)
                merchant_name = "Auto Loan Payment"
                category = ["Loan Payments", "Auto Loan Payment"]
            elif account_subtype == "student":
                # Student loan payment: typically $100-$400/month
                monthly_payment = round(random.uniform(100, 400), CURRENCY_DECIMAL_PLACES)
                merchant_name = "Student Loan Payment"
                category = ["Loan Payments", "Student Loan Payment"]
            else:
                continue  # Unknown loan type
            
            amount = -monthly_payment
            pending = 0
            payment_channel = "other"
            
        elif account_type == "credit":
            # Credit card transactions (negative amounts)
            # Use BLS-weighted category selection
            category_type = random.choices(category_list, weights=weights_list)[0]
            user_income = user_profile.get("income", 50000)
            amount = _get_transaction_amount_for_category(category_type, user_income)
            
            # Apply seasonal multiplier
            tx_month = tx_date.month
            if tx_month in SEASONAL_MULTIPLIERS:
                if category_type in SEASONAL_MULTIPLIERS[tx_month]:
                    amount *= SEASONAL_MULTIPLIERS[tx_month][category_type]
                    amount = round(amount, CURRENCY_DECIMAL_PLACES)
            
            # Apply day-of-week multiplier
            day_multiplier = get_day_of_week_multiplier(tx_date, category_type)
            amount *= day_multiplier
            amount = round(amount, CURRENCY_DECIMAL_PLACES)
            
            merchant_name = random.choice(categories.get(category_type, categories["shopping"]))
            category = get_category_for_merchant(merchant_name, category_type)
            pending = random.choice([0, 1]) if tx_date > datetime.now() - timedelta(days=2) else 0
            payment_channel = random.choice(["online", "in store", "other"])
        
        elif account_subtype == "checking":
            # Checking account transactions - use priority-based approach
            # Priority: Payroll > Mortgage/Rent > Subscriptions > Regular Expenses
            tx_date_only = tx_date.date()
            amount = None
            merchant_name = None
            category = None
            pending = None
            payment_channel = None
            
            # Check payroll (highest priority)
            if payroll_amount and payroll_frequency:
                # Check if this date is in pre-calculated payroll dates
                # (applies to both irregular and regular payroll)
                if tx_date_only in payroll_dates_set and tx_date_only not in processed_payroll_dates:
                    # Add small variation to amount for realism (±1-2%)
                    variation = random.uniform(0.98, 1.02)
                    amount = round(payroll_amount * variation, CURRENCY_DECIMAL_PLACES)
                    merchant_name = employer_name
                    category = ["Transfer", "Deposit"]
                    pending = 0
                    payment_channel = "other"
                    # Mark this payroll date as processed
                    processed_payroll_dates.add(tx_date_only)
            
            # Check mortgage/rent (second priority)
            if amount is None:
                if mortgage_payment and mortgage_start:
                    # Check if this date is in pre-calculated mortgage dates and hasn't been processed
                    if tx_date_only in mortgage_dates_set and tx_date_only not in processed_mortgage_dates:
                        amount = -mortgage_payment
                        merchant_name = "Mortgage Payment"
                        category = ["Rent And Utilities", "Mortgage"]
                        pending = 0
                        payment_channel = "other"
                        processed_mortgage_dates.add(tx_date_only)
                elif rent_payment and rent_start:
                    # Check if this date is in pre-calculated rent dates and hasn't been processed
                    if tx_date_only in rent_dates_set and tx_date_only not in processed_rent_dates:
                        amount = -rent_payment
                        merchant_name = "Rent Payment"
                        category = ["Rent And Utilities", "Rent"]
                        pending = 0
                        payment_channel = "other"
                        processed_rent_dates.add(tx_date_only)
            
            # Check subscriptions (third priority)
            if amount is None:
                for merchant, sub_info in subscriptions.items():
                    days_since_sub = (tx_date - sub_info["next_date"]).days
                    if 0 <= days_since_sub <= 3:  # Monthly subscription ±3 days
                        amount = -sub_info["amount"]
                        merchant_name = merchant
                        category = ["Entertainment", "Streaming Services"]
                        pending = 0
                        payment_channel = "online"
                        # Update next subscription date
                        sub_info["next_date"] += timedelta(days=30)
                        break
            
            # Check credit card payments (85% of users have credit cards)
            # Generate monthly credit card payment transactions
            if amount is None and random.random() < 0.85:
                # Check if this is around the credit card payment date (20th of month ±3 days)
                day_of_month = tx_date.day
                if 17 <= day_of_month <= 23:  # 20th ±3 days
                    # Generate payment based on income (credit card users pay 1-5% of monthly income)
                    monthly_income = user_profile.get("income", 50000) / MONTHS_PER_YEAR
                    payment_amount = round(monthly_income * random.uniform(0.01, 0.05), CURRENCY_DECIMAL_PLACES)
                    amount = -payment_amount
                    merchant_name = "Credit Card Payment"
                    category = ["Transfer", "Credit Card Payment"]
                    pending = 0
                    payment_channel = "other"
            
            # Default to regular expense (lowest priority)
            if amount is None:
                category_type = random.choices(category_list, weights=weights_list)[0]
                user_income = user_profile.get("income", 50000)
                amount = _get_transaction_amount_for_category(category_type, user_income)
                
                # Apply seasonal multiplier
                tx_month = tx_date.month
                if tx_month in SEASONAL_MULTIPLIERS:
                    if category_type in SEASONAL_MULTIPLIERS[tx_month]:
                        amount *= SEASONAL_MULTIPLIERS[tx_month][category_type]
                        amount = round(amount, CURRENCY_DECIMAL_PLACES)
                
                # Apply day-of-week multiplier
                day_multiplier = get_day_of_week_multiplier(tx_date, category_type)
                amount *= day_multiplier
                amount = round(amount, CURRENCY_DECIMAL_PLACES)
                
                merchant_name = random.choice(categories.get(category_type, categories["shopping"]))
                category = get_category_for_merchant(merchant_name, category_type)
                pending = random.choice([0, 1]) if tx_date > datetime.now() - timedelta(days=2) else 0
                payment_channel = random.choice(["online", "in store", "other"])
        
        else:  # savings account
            if persona_group == "savings_builder":
                # Priority 4: Generate positive net inflow
                # Use automatic transfers (70%) and manual deposits (30%)
                if random.random() < 0.70:  # 70% automatic transfers
                    amount = round(random.uniform(200.0, 500.0), CURRENCY_DECIMAL_PLACES)
                    merchant_name = "Automatic Transfer from Checking"
                    category = ["Transfer", "Transfer"]
                    pending = 0
                    payment_channel = "other"
                else:  # 30% manual deposits
                    amount = round(random.uniform(100.0, 300.0), CURRENCY_DECIMAL_PLACES)
                    merchant_name = "Savings Deposit"
                    category = ["Transfer", "Deposit"]
                    pending = 0
                    payment_channel = "other"
            else:
                # Other personas: mix of transfers and deposits/withdrawals
                if random.random() < 0.50:  # 50% automatic transfers
                    amount = round(random.uniform(100.0, 400.0), CURRENCY_DECIMAL_PLACES)
                    merchant_name = "Automatic Transfer from Checking"
                    category = ["Transfer", "Transfer"]
                    pending = 0
                    payment_channel = "other"
                elif random.random() < 0.3:  # 30% chance of withdrawal
                    amount = -round(random.uniform(50.0, 500.0), CURRENCY_DECIMAL_PLACES)
                    merchant_name = "Savings Withdrawal"
                    category = ["Transfer", "Withdrawal"]
                    pending = 0
                    payment_channel = "other"
                else:  # 20% manual deposits
                    amount = round(random.uniform(100.0, 1000.0), CURRENCY_DECIMAL_PLACES)
                    merchant_name = "Savings Deposit"
                    category = ["Transfer", "Deposit"]
                    pending = 0
                    payment_channel = "other"
        
        # Generate location data (for non-transfer transactions)
        if category[0] != "Transfer":
            location_address = fake.street_address()
            location_city = fake.city()
            location_region = fake.state_abbr()
            location_postal_code = fake.zipcode()
            location_country = "US"
            # Use user's metro area with small variance for coordinates
            metro_area = user_profile.get("metro_area", METRO_AREAS[0])
            base_lat = metro_area["lat"]
            base_lon = metro_area["lon"]
            # Add variance of ±0.5 degrees (roughly 35 miles)
            location_lat = round(base_lat + random.uniform(-0.5, 0.5), 6)
            location_lon = round(base_lon + random.uniform(-0.5, 0.5), 6)
        else:
            location_address = None
            location_city = None
            location_region = None
            location_postal_code = None
            location_country = None
            location_lat = None
            location_lon = None
        
        # Generate authorized_date (same as date for most transactions, or 1-2 days before for pending)
        if pending:
            authorized_date = (tx_date - timedelta(days=random.randint(1, 2))).strftime("%Y-%m-%d")
        else:
            authorized_date = tx_date.strftime("%Y-%m-%d")
        
        transactions.append({
            "transaction_id": transaction_id,
            "account_id": account_id,
            "user_id": user_profile["user_id"],
            "date": tx_date.strftime("%Y-%m-%d"),
            "amount": amount,
            "merchant_name": merchant_name,
            "category": json.dumps(category),  # Store as JSON string for CSV compatibility
            "pending": pending,
            "location_address": location_address,
            "location_city": location_city,
            "location_region": location_region,
            "location_postal_code": location_postal_code,
            "location_country": location_country,
            "location_lat": location_lat,
            "location_lon": location_lon,
            "iso_currency_code": "USD",
            "payment_channel": payment_channel,
            "authorized_date": authorized_date,
        })
        
        # Transaction clustering: 30% chance of related transaction for shopping categories
        # This creates realistic shopping patterns (multiple stores in one trip)
        if category[0] != "Transfer" and category_type in ["groceries", "shopping", "restaurants"]:
            if random.random() < 0.30:  # 30% chance of cluster transaction
                transaction_counter += 1
                cluster_transaction_id = f"tx_{account_id}_{transaction_counter:06d}"
                
                # Generate within 1 hour (same day)
                cluster_time_offset = random.uniform(0, 1/24)  # Up to 1 hour
                cluster_tx_date = tx_date + timedelta(days=cluster_time_offset)
                
                # Smaller amount (50-80% of original)
                cluster_amount_factor = random.uniform(0.5, 0.8)
                cluster_amount = round(amount * cluster_amount_factor, CURRENCY_DECIMAL_PLACES)
                
                # Different merchant, same category
                cluster_merchant = random.choice(categories.get(category_type, categories["shopping"]))
                # Make sure it's different from the original merchant
                attempts = 0
                while cluster_merchant == merchant_name and attempts < 5:
                    cluster_merchant = random.choice(categories.get(category_type, categories["shopping"]))
                    attempts += 1
                
                # Same location area but slight variance
                if location_lat and location_lon:
                    cluster_location_lat = round(location_lat + random.uniform(-0.01, 0.01), 6)
                    cluster_location_lon = round(location_lon + random.uniform(-0.01, 0.01), 6)
                else:
                    cluster_location_lat = location_lat
                    cluster_location_lon = location_lon
                
                transactions.append({
                    "transaction_id": cluster_transaction_id,
                    "account_id": account_id,
                    "user_id": user_profile["user_id"],
                    "date": cluster_tx_date.strftime("%Y-%m-%d"),
                    "amount": cluster_amount,
                    "merchant_name": cluster_merchant,
                    "category": json.dumps(category),
                    "pending": pending,
                    "location_address": location_address,
                    "location_city": location_city,
                    "location_region": location_region,
                    "location_postal_code": location_postal_code,
                    "location_country": location_country,
                    "location_lat": cluster_location_lat,
                    "location_lon": cluster_location_lon,
                    "iso_currency_code": "USD",
                    "payment_channel": payment_channel,
                    "authorized_date": authorized_date if not pending else (cluster_tx_date - timedelta(days=random.randint(1, 2))).strftime("%Y-%m-%d"),
                })
    
    return transactions


def generate_liabilities(
    credit_accounts: List[Dict[str, Any]], 
    loan_accounts: List[Dict[str, Any]],
    overdue_users: set,
    payment_behavior_groups: Dict[str, str] = None
) -> List[Dict[str, Any]]:
    """Generate liability data for credit card and loan accounts.
    
    Args:
        credit_accounts: List of credit card account dictionaries
        loan_accounts: List of loan account dictionaries (auto, mortgage, student)
        overdue_users: Set of user_ids that should be overdue
        payment_behavior_groups: Dict mapping user_id to payment behavior
        
    Returns:
        List of liability dictionaries
    """
    liabilities = []
    
    # Generate credit card liabilities
    for account in credit_accounts:
        account_id = account["account_id"]
        user_id = account["user_id"]
        balance = account["balance"]
        limit = account["limit"]
        
        # Generate APR (15-25%)
        apr = round(random.uniform(15.0, 25.0), 2)
        
        # Calculate minimum payment (typically 1-3% of balance or $25-50)
        min_payment_pct = random.uniform(0.01, 0.03)
        min_payment_amount = max(25.0, balance * min_payment_pct)
        minimum_payment_amount = round(min_payment_amount, CURRENCY_DECIMAL_PLACES)
        
        # Last payment amount based on payment behavior
        payment_behavior = payment_behavior_groups.get(user_id, "partial") if payment_behavior_groups else "partial"
        
        if payment_behavior == "min_only":
            last_payment_amount = minimum_payment_amount
        elif payment_behavior == "full":
            # Pay balance in full (or close to it)
            last_payment_amount = round(balance * random.uniform(0.95, 1.0), CURRENCY_DECIMAL_PLACES)
        else:  # partial
            # Pay between minimum and full (varies)
            if minimum_payment_amount > 0:
                max_multiplier = balance / minimum_payment_amount
            else:
                max_multiplier = 5.0
            last_payment_amount = round(minimum_payment_amount * random.uniform(1.5, max_multiplier), CURRENCY_DECIMAL_PLACES)
            # Cap at balance
            last_payment_amount = min(last_payment_amount, balance)
        
        # Overdue status (10% of users)
        is_overdue = user_id in overdue_users
        
        liability = {
            "account_id": account_id,
            "account_type": "credit",
            "account_subtype": "credit card",
            "aprs": json.dumps([{
                "apr_percentage": apr,
                "apr_type": "purchase_apr"
            }]),
            "minimum_payment_amount": minimum_payment_amount,
            "last_payment_amount": last_payment_amount,
            "is_overdue": is_overdue,
            "last_statement_balance": round(balance, 2)
        }
        
        liabilities.append(liability)
    
    # Generate loan liabilities
    for account in loan_accounts:
        account_id = account["account_id"]
        user_id = account["user_id"]
        balance = account["balance"]
        original_amount = account.get("limit", balance)
        subtype = account["subtype"]
        
        # Calculate loan age (for origination date)
        # Assume loan originated 1-10 years ago
        loan_age_years = random.uniform(1, 10)
        origination_date = (datetime.now() - timedelta(days=int(loan_age_years * 365))).strftime("%Y-%m-%d")
        
        # Calculate next payment due date (1-30 days from now)
        days_until_payment = random.randint(1, 30)
        next_payment_due_date = (datetime.now() + timedelta(days=days_until_payment)).strftime("%Y-%m-%d")
        
        if subtype == "mortgage":
            # Mortgage liability fields
            interest_rate = round(random.uniform(3.0, 7.0), 3)  # Mortgage rates typically 3-7%
            escrow_balance = round(random.uniform(1000, 5000), 2)  # Escrow for taxes/insurance
            property_address = f"{fake.street_address()}, {fake.city()}, {fake.state_abbr()} {fake.zipcode()}"
            
            liability = {
                "account_id": account_id,
                "account_type": "loan",
                "account_subtype": "mortgage",
                "origination_date": origination_date,
                "original_principal_balance": round(original_amount, 2),
                "interest_rate": interest_rate,
                "next_payment_due_date": next_payment_due_date,
                "escrow_balance": escrow_balance,
                "property_address": property_address,
                "principal_balance": round(balance, 2)
            }
            
        elif subtype == "auto":
            # Auto loan liability fields
            interest_rate = round(random.uniform(3.0, 12.0), 3)  # Auto loan rates typically 3-12%
            
            liability = {
                "account_id": account_id,
                "account_type": "loan",
                "account_subtype": "auto",
                "origination_date": origination_date,
                "original_principal_balance": round(original_amount, 2),
                "interest_rate": interest_rate,
                "next_payment_due_date": next_payment_due_date,
                "principal_balance": round(balance, 2)
            }
            
        elif subtype == "student":
            # Student loan liability fields
            interest_rate = round(random.uniform(3.0, 8.0), 3)  # Student loan rates typically 3-8%
            guarantor = random.choice(["FEDERAL", "PRIVATE", "STATE"])
            
            liability = {
                "account_id": account_id,
                "account_type": "loan",
                "account_subtype": "student",
                "origination_date": origination_date,
                "original_principal_balance": round(original_amount, 2),
                "interest_rate": interest_rate,
                "next_payment_due_date": next_payment_due_date,
                "guarantor": guarantor,
                "principal_balance": round(balance, 2)
            }
        else:
            continue  # Unknown loan type
        
        liabilities.append(liability)
    
    return liabilities


def assign_persona_groups_to_users(users: List[Dict[str, Any]], users_per_persona: int = 20) -> Dict[str, str]:
    """Assign persona groups to users before data generation.
    
    Assigns users as constructed (users_per_persona per persona), then marks remaining
    users as unconstructed. If fewer than users_per_persona * 5 total users, assigns proportionally.
    
    Args:
        users: List of user dictionaries
        users_per_persona: Number of users per persona (default: 20)
    
    Returns:
        Dict mapping user_id to persona_group
    """
    from collections import Counter
    users_shuffled = users.copy()
    random.shuffle(users_shuffled)
    num_users = len(users_shuffled)
    
    persona_groups = {}
    
    # Target: users_per_persona * 5 personas constructed users, remainder unconstructed
    constructed_target = users_per_persona * 5
    users_per_persona_target = users_per_persona
    
    # Calculate how many constructed users we can actually assign
    constructed_count = min(constructed_target, num_users)
    
    # Calculate users per persona (proportional if fewer than constructed_target total)
    if num_users >= constructed_target:
        # We have enough users: assign exactly users_per_persona per persona
        users_per_persona_actual = users_per_persona_target
    else:
        # Fewer than constructed_target users: assign proportionally
        users_per_persona_actual = max(1, constructed_count // 5)  # Divide by 5 personas
    
    high_util_count = users_per_persona_actual
    variable_income_count = users_per_persona_actual
    subscription_heavy_count = users_per_persona_actual
    savings_builder_count = users_per_persona_actual
    general_wellness_count = users_per_persona_actual
    
    # Adjust to not exceed constructed_count
    total_assigned = high_util_count + variable_income_count + subscription_heavy_count + savings_builder_count + general_wellness_count
    if total_assigned > constructed_count:
        # Reduce equally from each persona
        excess = total_assigned - constructed_count
        reduce_per_persona = excess // 5
        high_util_count -= reduce_per_persona
        variable_income_count -= reduce_per_persona
        subscription_heavy_count -= reduce_per_persona
        savings_builder_count -= reduce_per_persona
        general_wellness_count -= reduce_per_persona
        # Handle remainder
        remainder = excess % 5
        if remainder > 0:
            general_wellness_count -= remainder
    
    idx = 0
    
    # Assign constructed users
    for i in range(high_util_count):
        if idx < constructed_count:
            persona_groups[users_shuffled[idx]["user_id"]] = "high_utilization"
            users_shuffled[idx]["is_constructed"] = True
            idx += 1
    
    for i in range(variable_income_count):
        if idx < constructed_count:
            persona_groups[users_shuffled[idx]["user_id"]] = "variable_income"
            users_shuffled[idx]["is_constructed"] = True
            idx += 1
    
    for i in range(subscription_heavy_count):
        if idx < constructed_count:
            persona_groups[users_shuffled[idx]["user_id"]] = "subscription_heavy"
            users_shuffled[idx]["is_constructed"] = True
            idx += 1
    
    for i in range(savings_builder_count):
        if idx < constructed_count:
            persona_groups[users_shuffled[idx]["user_id"]] = "savings_builder"
            users_shuffled[idx]["is_constructed"] = True
            idx += 1
    
    for i in range(general_wellness_count):
        if idx < constructed_count:
            persona_groups[users_shuffled[idx]["user_id"]] = "general_wellness"
            users_shuffled[idx]["is_constructed"] = True
            idx += 1
    
    # Remaining users: unconstructed (no persona assignment)
    while idx < num_users:
        users_shuffled[idx]["is_constructed"] = False
        # Don't assign persona_group - will be None
        idx += 1
    
    # Store persona in user dicts for constructed users
    for user in users:
        user["persona_group"] = persona_groups.get(user["user_id"])
        # Set is_constructed flag (default to False if not set)
        if "is_constructed" not in user:
            user["is_constructed"] = False
    
    return persona_groups


def apply_diversity_strategy(
    users: List[Dict[str, Any]],
    accounts: List[Dict[str, Any]],
    transactions: List[Dict[str, Any]],
    liabilities: List[Dict[str, Any]]
) -> tuple:
    """Apply diversity strategy to ensure varied financial situations.
    
    Target distributions:
    - Credit utilization: 30% low (<30%), 30% medium (30-50%), 40% high (≥50%)
    - Savings: 25% active savers, 50% minimal savers, 25% no savings
    - Subscriptions: 0-2 (30%), 3-5 (40%), 6+ (30%)
    
    Args:
        users: List of user dictionaries
        accounts: List of account dictionaries
        transactions: List of transaction dictionaries
        liabilities: List of liability dictionaries
        
    Returns:
        Tuple of (users, accounts, transactions, liabilities) with diversity applied
    """
    # Shuffle users for random assignment
    users_shuffled = users.copy()
    random.shuffle(users_shuffled)
    num_users = len(users_shuffled)
    
    # Assign users to credit card payment behavior groups
    # Distribution: 11% min only, 42% full (average of 40-44%), 47% partial (average of 45-49%)
    # Prioritize high_utilization users for min_only payments
    min_only_count = max(1, int(num_users * 0.11))
    full_payment_count = max(1, int(num_users * 0.42))
    partial_payment_count = num_users - min_only_count - full_payment_count
    
    payment_behavior_groups = {}
    
    # First, assign min_only to high_utilization users (50% of them)
    high_util_users = [u for u in users_shuffled if u.get("persona_group") == "high_utilization"]
    high_util_min_only_count = min(min_only_count, len(high_util_users) // 2) if high_util_users else 0
    
    high_util_assigned = 0
    for user in users_shuffled:
        user_id = user["user_id"]
        persona = user.get("persona_group")  # Can be None for unconstructed users
        
        if persona == "high_utilization" and high_util_assigned < high_util_min_only_count:
            payment_behavior_groups[user_id] = "min_only"
            high_util_assigned += 1
        elif len(payment_behavior_groups) < min_only_count:
            payment_behavior_groups[user_id] = "min_only"
        elif len([v for v in payment_behavior_groups.values() if v == "full"]) < full_payment_count:
            payment_behavior_groups[user_id] = "full"
        else:
            payment_behavior_groups[user_id] = "partial"
    
    # Assign users to credit utilization groups
    low_util_count = int(num_users * 0.30)
    medium_util_count = int(num_users * 0.30)
    high_util_count = num_users - low_util_count - medium_util_count
    
    utilization_groups = {}
    for i, user in enumerate(users_shuffled):
        if i < low_util_count:
            utilization_groups[user["user_id"]] = "low"
        elif i < low_util_count + medium_util_count:
            utilization_groups[user["user_id"]] = "medium"
        else:
            utilization_groups[user["user_id"]] = "high"
    
    # Assign users to savings groups
    active_saver_count = int(num_users * 0.25)
    minimal_saver_count = int(num_users * 0.50)
    no_saver_count = num_users - active_saver_count - minimal_saver_count
    
    savings_groups = {}
    for i, user in enumerate(users_shuffled):
        if i < active_saver_count:
            savings_groups[user["user_id"]] = "active"
        elif i < active_saver_count + minimal_saver_count:
            savings_groups[user["user_id"]] = "minimal"
        else:
            savings_groups[user["user_id"]] = "none"
    
    # Assign users to subscription groups
    low_sub_count = int(num_users * 0.30)
    medium_sub_count = int(num_users * 0.40)
    high_sub_count = num_users - low_sub_count - medium_sub_count
    
    subscription_groups = {}
    for i, user in enumerate(users_shuffled):
        if i < low_sub_count:
            subscription_groups[user["user_id"]] = "low"
        elif i < low_sub_count + medium_sub_count:
            subscription_groups[user["user_id"]] = "medium"
        else:
            subscription_groups[user["user_id"]] = "high"
    
    # Create user lookup dictionary for efficient access (must be before use)
    user_lookup = {u["user_id"]: u for u in users}
    
    # Apply credit utilization to credit card accounts
    user_credit_accounts = {}
    for account in accounts:
        if account["type"] == "credit":
            user_id = account["user_id"]
            if user_id not in user_credit_accounts:
                user_credit_accounts[user_id] = []
            user_credit_accounts[user_id].append(account)
    
    for user_id, credit_accounts_list in user_credit_accounts.items():
        # Get persona from user dict (stored in Step 1)
        persona = None
        user_data = user_lookup.get(user_id)
        if user_data:
            persona = user_data.get("persona_group")
        
        # Handle None persona (unconstructed users) - use general_wellness as default
        if persona is None:
            persona = "general_wellness"
        
        if persona == "high_utilization":
            utilization = random.uniform(0.50, 0.95)
        elif persona == "variable_income":
            utilization = random.uniform(0.05, 0.49)  # Not high enough for Priority 1
        elif persona == "subscription_heavy":
            utilization = random.uniform(0.05, 0.49)  # < 50% to avoid Priority 1
        elif persona == "savings_builder":
            utilization = random.uniform(0.05, 0.29)  # < 30% required
        else:  # general_wellness or None
            utilization = random.uniform(0.05, 0.49)
        
        for account in credit_accounts_list:
            limit = account["limit"]
            account["balance"] = round(limit * utilization, 2)
    
    # Adjust checking balances based on persona (for cash_flow_buffer)
    for account in accounts:
        if account["type"] == "depository" and account["subtype"] == "checking":
            user_id = account["user_id"]
            user_data = user_lookup.get(user_id)
            persona = user_data.get("persona_group") if user_data else None
            
            # Handle None persona (unconstructed users)
            if persona is None:
                persona = "general_wellness"
                
            user_income = user_lookup.get(user_id, {}).get("income", 50000)
            monthly_expenses = user_income / MONTHS_PER_YEAR * DISPOSABLE_INCOME_RATIO
            
            if persona == "variable_income":
                # Priority 2: cash_flow_buffer < 1.0 (checking balance < 1 month expenses)
                account["balance"] = round(monthly_expenses * random.uniform(0.1, 0.9), 2)
            else:
                # Other personas: reasonable checking balance
                account["balance"] = round(monthly_expenses * random.uniform(0.5, 2.0), 2)
    
    # Apply savings strategy to savings accounts
    for account in accounts:
        if account["type"] == "depository" and account["subtype"] == "savings":
            user_id = account["user_id"]
            user_data = user_lookup.get(user_id)
            persona = user_data.get("persona_group") if user_data else None
            
            # Handle None persona (unconstructed users)
            if persona is None:
                persona = "general_wellness"
                
            user_income = user_lookup.get(user_id, {}).get("income", 50000)
            monthly_expenses = user_income / MONTHS_PER_YEAR * DISPOSABLE_INCOME_RATIO
            
            if persona == "savings_builder":
                # Priority 4: Need positive net_inflow >= 200/month
                # Set balance high enough to show growth (3-6 months expenses)
                account["balance"] = round(monthly_expenses * random.uniform(3.0, 6.0), CURRENCY_DECIMAL_PLACES)
            else:
                # Other personas: use existing savings group logic
                savings_group = savings_groups.get(user_id, "minimal")
                if savings_group == "active":
                    account["balance"] = round(monthly_expenses * random.uniform(3.0, 12.0), CURRENCY_DECIMAL_PLACES)
                elif savings_group == "minimal":
                    account["balance"] = round(monthly_expenses * random.uniform(0.5, 3.0), CURRENCY_DECIMAL_PLACES)
                else:
                    account["balance"] = round(random.uniform(0, 100), CURRENCY_DECIMAL_PLACES)
    
    # Mark users for overdue status (10% of users with credit cards)
    overdue_users = set()
    credit_card_users = set(user_credit_accounts.keys())
    if credit_card_users:
        num_overdue = max(1, int(len(credit_card_users) * 0.10))
        overdue_user_ids = random.sample(list(credit_card_users), min(num_overdue, len(credit_card_users)))
        overdue_users.update(overdue_user_ids)
    
    # Re-generate liabilities with overdue status and payment behaviors
    credit_accounts_for_liabilities = [acc for acc in accounts if acc["type"] == "credit"]
    loan_accounts_for_liabilities = [acc for acc in accounts if acc["type"] == "loan"]
    liabilities = generate_liabilities(credit_accounts_for_liabilities, loan_accounts_for_liabilities, overdue_users, payment_behavior_groups)
    
    return users, accounts, transactions, liabilities


def export_data(
    users: List[Dict[str, Any]],
    accounts: List[Dict[str, Any]],
    transactions: List[Dict[str, Any]],
    liabilities: List[Dict[str, Any]],
    output_dir: str = "data"
) -> None:
    """Export generated data to files.
    
    Args:
        users: List of user dictionaries
        accounts: List of account dictionaries
        transactions: List of transaction dictionaries
        liabilities: List of liability dictionaries
        output_dir: Output directory path (default: "data")
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Export users to JSON
    users_file = output_path / "users.json"
    try:
        with open(users_file, "w") as f:
            json.dump(users, f, indent=2)
        print(f"Exported {len(users)} users to {users_file}")
    except IOError as e:
        print(f"Error exporting users to {users_file}: {e}")
        raise
    
    # Export accounts to CSV
    accounts_file = output_path / "accounts.csv"
    if accounts:
        try:
            fieldnames = ["account_id", "user_id", "type", "subtype", "balance", "limit", "mask"]
            with open(accounts_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for account in accounts:
                    row = account.copy()
                    row["limit"] = account["limit"] if account["limit"] is not None else ""
                    writer.writerow(row)
            print(f"Exported {len(accounts)} accounts to {accounts_file}")
        except IOError as e:
            print(f"Error exporting accounts to {accounts_file}: {e}")
            raise
    
    # Export transactions to CSV
    transactions_file = output_path / "transactions.csv"
    if transactions:
        try:
            fieldnames = ["transaction_id", "account_id", "user_id", "date", "amount", 
                         "merchant_name", "category", "pending",
                         "location_address", "location_city", "location_region", "location_postal_code",
                         "location_country", "location_lat", "location_lon",
                         "iso_currency_code", "payment_channel", "authorized_date"]
            with open(transactions_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for transaction in transactions:
                    row = transaction.copy()
                    # Handle None values for location fields
                    for field in ["location_address", "location_city", "location_region", 
                                 "location_postal_code", "location_country", 
                                 "location_lat", "location_lon", "authorized_date"]:
                        if row.get(field) is None:
                            row[field] = ""
                    writer.writerow(row)
            print(f"Exported {len(transactions)} transactions to {transactions_file}")
        except IOError as e:
            print(f"Error exporting transactions to {transactions_file}: {e}")
            raise
    
    # Export liabilities to CSV
    liabilities_file = output_path / "liabilities.csv"
    if liabilities:
        try:
            # Collect all possible fieldnames from liabilities
            all_fieldnames = set()
            for liability in liabilities:
                all_fieldnames.update(liability.keys())
            
            # Order fields logically: common fields first, then account-specific
            common_fields = ["account_id", "account_type", "account_subtype"]
            credit_fields = ["aprs", "minimum_payment_amount", "last_payment_amount", "is_overdue", "last_statement_balance"]
            loan_fields = ["origination_date", "original_principal_balance", "interest_rate", "next_payment_due_date", "principal_balance"]
            mortgage_fields = ["escrow_balance", "property_address"]
            student_fields = ["guarantor"]
            
            fieldnames = []
            for field_list in [common_fields, credit_fields, loan_fields, mortgage_fields, student_fields]:
                for field in field_list:
                    if field in all_fieldnames:
                        fieldnames.append(field)
            
            # Add any remaining fields
            for field in sorted(all_fieldnames):
                if field not in fieldnames:
                    fieldnames.append(field)
            
            with open(liabilities_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for liability in liabilities:
                    row = liability.copy()
                    # Handle None values
                    for field in fieldnames:
                        if field not in row or row[field] is None:
                            row[field] = ""
                    writer.writerow(row)
            print(f"Exported {len(liabilities)} liabilities to {liabilities_file}")
        except IOError as e:
            print(f"Error exporting liabilities to {liabilities_file}: {e}")
            raise


def determine_homeownership_by_quintile(user_income: float, all_incomes: List[float]) -> Dict[str, Any]:
    """Determine homeownership status based on income quintile.
    
    Homeownership rates by income quintile:
    - 20th percentile (bottom 20%): 44%
    - 40th percentile: 58%
    - 60th percentile: 62%
    - 80th percentile: 75%
    - 100th percentile (top 20%): 87%
    
    Args:
        user_income: User's income
        all_incomes: List of all user incomes to determine quintiles
        
    Returns:
        Dict with 'is_homeowner' boolean and 'income_quintile' string
    """
    # Sort incomes to determine quintiles
    sorted_incomes = sorted(all_incomes)
    num_users = len(sorted_incomes)
    
    # Determine quintile thresholds
    quintile_20 = sorted_incomes[int(num_users * 0.20)] if num_users > 0 else user_income
    quintile_40 = sorted_incomes[int(num_users * 0.40)] if num_users > 0 else user_income
    quintile_60 = sorted_incomes[int(num_users * 0.60)] if num_users > 0 else user_income
    quintile_80 = sorted_incomes[int(num_users * 0.80)] if num_users > 0 else user_income
    
    # Determine which quintile the user is in
    if user_income <= quintile_20:
        quintile = "20th"
        homeownership_rate = 0.44
    elif user_income <= quintile_40:
        quintile = "40th"
        homeownership_rate = 0.58
    elif user_income <= quintile_60:
        quintile = "60th"
        homeownership_rate = 0.62
    elif user_income <= quintile_80:
        quintile = "80th"
        homeownership_rate = 0.75
    else:
        quintile = "100th"
        homeownership_rate = 0.87
    
    # Determine if user is homeowner based on rate
    is_homeowner = random.random() < homeownership_rate
    
    return {
        "is_homeowner": is_homeowner,
        "income_quintile": quintile
    }


def generate_all_data(count: int = 200, output_dir: str = "data", days: int = 180, users_per_persona: int = 20) -> None:
    """Generate all synthetic data and export to files.
    
    This is the main entry point for data generation.
    Generates users with constructed personas and unconstructed users.
    
    Args:
        count: Number of users to generate (default: 200)
        output_dir: Output directory path (default: "data")
        days: Number of days of transaction history to generate (default: 180)
        users_per_persona: Number of users per persona (default: 20)
    """
    print(f"Generating synthetic data for {count} users over {days} days...")
    constructed_count = min(users_per_persona * 5, count)
    unconstructed_count = max(0, count - constructed_count)
    print(f"  - Up to {constructed_count} users will be constructed ({users_per_persona} per persona)")
    if unconstructed_count > 0:
        print(f"  - Remaining {unconstructed_count} users will be unconstructed")
    
    # Generate users
    users = generate_users(count)
    print(f"Generated {len(users)} users")
    
    # Assign persona groups BEFORE generating transactions
    from collections import Counter
    persona_groups = assign_persona_groups_to_users(users, users_per_persona=users_per_persona)
    print(f"Assigned persona groups: {dict(Counter(persona_groups.values()))}")
    
    # Collect all incomes for quintile calculation
    all_incomes = [user["income"] for user in users]
    
    # Generate accounts for all users (with homeownership logic)
    accounts = []
    homeownership_map = {}  # Track homeownership status for mortgage/rent generation
    for user in users:
        homeownership_status = determine_homeownership_by_quintile(user["income"], all_incomes)
        homeownership_map[user["user_id"]] = homeownership_status
        user_accounts = generate_accounts(user["user_id"], user, homeownership_status)
        accounts.extend(user_accounts)
    print(f"Generated {len(accounts)} accounts")
    
    # Generate transactions for all accounts
    transactions = []
    # Create user lookup dictionary for efficient access
    user_lookup = {u["user_id"]: u for u in users}
    
    for account in accounts:
        user_id_for_account = account["user_id"]
        user_profile_for_account = user_lookup.get(user_id_for_account, {})
        homeownership_status_for_account = homeownership_map.get(user_id_for_account)
        persona_group_for_account = user_profile_for_account.get("persona_group")
        
        account_transactions = generate_transactions(
            account["account_id"],
            account["type"],
            account["subtype"],
            user_profile_for_account,
            account,
            days=days,
            homeownership_status=homeownership_status_for_account,
            persona_group=persona_group_for_account
        )
        transactions.extend(account_transactions)
    print(f"Generated {len(transactions)} transactions")
    
    # Apply diversity strategy (this also generates liabilities)
    print("Applying diversity strategy...")
    users, accounts, transactions, liabilities = apply_diversity_strategy(
        users, accounts, transactions, []
    )
    print(f"Generated {len(liabilities)} liabilities")
    
    # Export to files
    print("Exporting data to files...")
    export_data(users, accounts, transactions, liabilities, output_dir)
    
    print("Data generation complete!")


if __name__ == "__main__":
    generate_all_data()

