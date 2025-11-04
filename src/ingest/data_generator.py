"""Synthetic data generator for SpendSense.

This module generates realistic synthetic financial data for 75 users including:
- User profiles with names and income levels
- Bank accounts (checking, savings, credit cards)
- Transaction history over 180 days
- Credit card liabilities

All data follows Plaid-style schema and includes realistic patterns like
recurring subscriptions, payroll deposits, and varied credit utilization.
"""

import json
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from faker import Faker

# Initialize Faker with deterministic seed
fake = Faker()
Faker.seed(42)
random.seed(42)


def generate_users(count: int = 75) -> List[Dict[str, Any]]:
    """Generate synthetic user profiles.
    
    Args:
        count: Number of users to generate (default: 75)
        
    Returns:
        List of user dictionaries with user_id, name, income, created_at
    """
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
        
        # Create user
        user = {
            "user_id": user_id,
            "name": name,
            "income": income,
            "created_at": (base_date + timedelta(days=random.randint(0, 30))).isoformat()
        }
        users.append(user)
    
    return users


def generate_accounts(user_id: str, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate accounts for a user.
    
    Per user:
    - 1 checking account (always)
    - 0-1 savings account (70% probability)
    - 0-2 credit cards (60% probability)
    
    Args:
        user_id: User identifier
        user_profile: User profile dict with income
        
    Returns:
        List of account dictionaries matching schema
    """
    accounts = []
    account_counter = 1
    
    # Always create checking account
    checking_balance = user_profile["income"] / 12 * random.uniform(0.5, 2.0)  # 0.5-2 months of income
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
        savings_balance = user_profile["income"] / 12 * random.uniform(0, 6.0)  # 0-6 months savings
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
    
    # 60% probability of credit cards (0-2 cards)
    if random.random() < 0.6:
        num_cards = random.choices([1, 2], weights=[0.7, 0.3])[0]
        for _ in range(num_cards):
            # Credit limit based on income (typically 10-30% of annual income)
            credit_limit = user_profile["income"] * random.uniform(0.10, 0.30)
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
    
    return accounts


def generate_transactions(
    account_id: str,
    account_type: str,
    account_subtype: str,
    user_profile: Dict[str, Any],
    account_info: Dict[str, Any],
    days: int = 180
) -> List[Dict[str, Any]]:
    """Generate transactions for an account.
    
    Args:
        account_id: Account identifier
        account_type: "depository" or "credit"
        account_subtype: "checking", "savings", or "credit card"
        user_profile: User profile dict with income
        account_info: Account dict with balance, limit
        days: Number of days of history to generate
        
    Returns:
        List of transaction dictionaries
    """
    transactions = []
    start_date = datetime.now() - timedelta(days=days)
    transaction_counter = 1
    
    # Determine number of transactions per user (150-250 total)
    # This will be distributed across accounts
    if account_type == "depository" and account_subtype == "checking":
        # Checking gets most transactions
        num_transactions = random.randint(100, 180)
    elif account_type == "depository" and account_subtype == "savings":
        # Savings gets fewer transactions
        num_transactions = random.randint(5, 20)
    else:  # credit card
        # Credit cards get moderate transactions
        num_transactions = random.randint(30, 60)
    
    # Common merchant categories
    categories = {
        "groceries": ["Whole Foods", "Kroger", "Safeway", "Trader Joe's", "Walmart"],
        "restaurants": ["Starbucks", "McDonald's", "Chipotle", "Olive Garden", "Pizza Hut"],
        "bills": ["Electric Company", "Water Utility", "Internet Provider", "Phone Company"],
        "shopping": ["Amazon", "Target", "Best Buy", "Macy's", "Home Depot"],
        "entertainment": ["Netflix", "Spotify", "Disney+", "Hulu", "YouTube Premium"],
        "gas": ["Shell", "Exxon", "Chevron", "BP"],
        "subscriptions": ["Netflix", "Spotify", "Disney+", "Hulu", "YouTube Premium", 
                          "Adobe Creative Cloud", "Microsoft 365", "Gym Membership"]
    }
    
    # Subscription merchants (for recurring patterns)
    subscription_merchants = categories["subscriptions"]
    
    # Generate recurring subscriptions (monthly)
    subscriptions = {}
    if account_type == "depository" and account_subtype == "checking":
        # Assign 0-8 subscriptions per user
        num_subscriptions = random.randint(0, 8)
        for _ in range(num_subscriptions):
            merchant = random.choice(subscription_merchants)
            amount = round(random.uniform(5.99, 29.99), 2)
            subscriptions[merchant] = {
                "amount": amount,
                "frequency": "monthly",
                "next_date": start_date + timedelta(days=random.randint(0, 30))
            }
    
    # Generate payroll deposits (for checking accounts)
    payroll_amount = None
    payroll_frequency = None
    if account_type == "depository" and account_subtype == "checking":
        # Determine payroll frequency
        payroll_frequency = random.choice(["biweekly", "monthly"])
        if payroll_frequency == "biweekly":
            payroll_amount = user_profile["income"] / 26  # Annual income / 26 pay periods
        else:  # monthly
            payroll_amount = user_profile["income"] / 12
        
        payroll_amount = round(payroll_amount, 2)
        payroll_start = start_date + timedelta(days=random.randint(0, 13 if payroll_frequency == "biweekly" else 29))
    
    current_date = start_date
    transaction_dates = []
    
    # Generate transaction dates
    for _ in range(num_transactions):
        # Progress through time
        if transaction_dates:
            days_since_last = random.randint(0, 7)  # Transactions every 0-7 days
        else:
            days_since_last = random.randint(0, 5)
        current_date += timedelta(days=days_since_last)
        if current_date > datetime.now():
            break
        transaction_dates.append(current_date)
    
    # Sort dates
    transaction_dates.sort()
    
    # Generate transactions
    for tx_date in transaction_dates:
        transaction_id = f"tx_{account_id}_{transaction_counter:06d}"
        transaction_counter += 1
        
        # Determine transaction type
        if account_type == "credit":
            # Credit card transactions (negative amounts)
            amount = -round(random.uniform(5.0, 500.0), 2)
            category = random.choice(["groceries", "restaurants", "shopping", "entertainment", "gas"])
            merchant_name = random.choice(categories[category])
            pending = random.choice([0, 1]) if tx_date > datetime.now() - timedelta(days=2) else 0
        
        elif account_subtype == "checking":
            # Checking account transactions
            # Check for payroll deposit
            if payroll_amount and payroll_frequency:
                days_since_payroll_start = (tx_date - payroll_start).days
                if payroll_frequency == "biweekly":
                    if days_since_payroll_start >= 0 and days_since_payroll_start % 14 == 0:
                        amount = payroll_amount
                        merchant_name = "PAYROLL DEPOSIT"
                        category = "transfer"
                        pending = 0
                    else:
                        # Regular expense
                        amount = -round(random.uniform(10.0, 300.0), 2)
                        category = random.choice(["groceries", "restaurants", "bills", "shopping", "gas"])
                        merchant_name = random.choice(categories[category])
                        pending = random.choice([0, 1]) if tx_date > datetime.now() - timedelta(days=2) else 0
                else:  # monthly
                    if days_since_payroll_start >= 0 and days_since_payroll_start % 30 == 0:
                        amount = payroll_amount
                        merchant_name = "PAYROLL DEPOSIT"
                        category = "transfer"
                        pending = 0
                    else:
                        amount = -round(random.uniform(10.0, 300.0), 2)
                        category = random.choice(["groceries", "restaurants", "bills", "shopping", "gas"])
                        merchant_name = random.choice(categories[category])
                        pending = random.choice([0, 1]) if tx_date > datetime.now() - timedelta(days=2) else 0
            else:
                amount = -round(random.uniform(10.0, 300.0), 2)
                category = random.choice(["groceries", "restaurants", "bills", "shopping", "gas"])
                merchant_name = random.choice(categories[category])
                pending = random.choice([0, 1]) if tx_date > datetime.now() - timedelta(days=2) else 0
            
            # Check for subscription payment
            for merchant, sub_info in subscriptions.items():
                days_since_sub = (tx_date - sub_info["next_date"]).days
                if 0 <= days_since_sub <= 3:  # Monthly subscription ±3 days
                    amount = -sub_info["amount"]
                    merchant_name = merchant
                    category = "entertainment"
                    pending = 0
                    # Update next subscription date
                    sub_info["next_date"] += timedelta(days=30)
                    break
        
        else:  # savings account
            # Savings account (mostly deposits, occasional withdrawals)
            if random.random() < 0.3:  # 30% chance of withdrawal
                amount = -round(random.uniform(50.0, 500.0), 2)
                merchant_name = "Savings Withdrawal"
                category = "transfer"
            else:  # 70% chance of deposit
                amount = round(random.uniform(100.0, 1000.0), 2)
                merchant_name = "Savings Deposit"
                category = "transfer"
            pending = 0
        
        transactions.append({
            "transaction_id": transaction_id,
            "account_id": account_id,
            "user_id": user_profile["user_id"],
            "date": tx_date.strftime("%Y-%m-%d"),
            "amount": amount,
            "merchant_name": merchant_name,
            "category": category,
            "pending": pending
        })
    
    return transactions


def generate_liabilities(credit_accounts: List[Dict[str, Any]], overdue_users: set) -> List[Dict[str, Any]]:
    """Generate liability data for credit card accounts.
    
    Args:
        credit_accounts: List of credit card account dictionaries
        overdue_users: Set of user_ids that should be overdue
        
    Returns:
        List of liability dictionaries
    """
    liabilities = []
    
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
        minimum_payment_amount = round(min_payment_amount, 2)
        
        # Last payment amount (may be minimum payment only)
        if random.random() < 0.3:  # 30% only pay minimum
            last_payment_amount = minimum_payment_amount
        else:
            last_payment_amount = round(minimum_payment_amount * random.uniform(1.5, 5.0), 2)
        
        # Overdue status (10% of users)
        is_overdue = user_id in overdue_users
        
        liability = {
            "account_id": account_id,
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
    
    return liabilities


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
    
    # Assign users to credit utilization groups
    num_users = len(users_shuffled)
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
    
    # Apply credit utilization to credit card accounts
    user_credit_accounts = {}
    for account in accounts:
        if account["type"] == "credit":
            user_id = account["user_id"]
            if user_id not in user_credit_accounts:
                user_credit_accounts[user_id] = []
            user_credit_accounts[user_id].append(account)
    
    for user_id, credit_accounts_list in user_credit_accounts.items():
        util_group = utilization_groups.get(user_id, "medium")
        
        for account in credit_accounts_list:
            limit = account["limit"]
            
            if util_group == "low":
                utilization = random.uniform(0.05, 0.29)
            elif util_group == "medium":
                utilization = random.uniform(0.30, 0.49)
            else:  # high
                utilization = random.uniform(0.50, 0.95)
            
            account["balance"] = round(limit * utilization, 2)
    
    # Apply savings strategy to savings accounts
    for account in accounts:
        if account["type"] == "depository" and account["subtype"] == "savings":
            user_id = account["user_id"]
            savings_group = savings_groups.get(user_id, "minimal")
            user_income = next((u["income"] for u in users if u["user_id"] == user_id), 50000)
            
            if savings_group == "active":
                # 3-12 months of expenses saved
                monthly_expenses = user_income / 12 * 0.7  # Assume 70% of income is expenses
                account["balance"] = round(monthly_expenses * random.uniform(3.0, 12.0), 2)
            elif savings_group == "minimal":
                # 0.5-3 months
                monthly_expenses = user_income / 12 * 0.7
                account["balance"] = round(monthly_expenses * random.uniform(0.5, 3.0), 2)
            else:  # none
                account["balance"] = round(random.uniform(0, 100), 2)
    
    # Mark users for overdue status (10% of users with credit cards)
    overdue_users = set()
    credit_card_users = set(user_credit_accounts.keys())
    num_overdue = max(1, int(len(credit_card_users) * 0.10))
    overdue_user_ids = random.sample(list(credit_card_users), min(num_overdue, len(credit_card_users)))
    overdue_users.update(overdue_user_ids)
    
    # Re-generate liabilities with overdue status
    credit_accounts_for_liabilities = [acc for acc in accounts if acc["type"] == "credit"]
    liabilities = generate_liabilities(credit_accounts_for_liabilities, overdue_users)
    
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
    with open(users_file, "w") as f:
        json.dump(users, f, indent=2)
    print(f"Exported {len(users)} users to {users_file}")
    
    # Export accounts to CSV
    accounts_file = output_path / "accounts.csv"
    if accounts:
        fieldnames = ["account_id", "user_id", "type", "subtype", "balance", "limit", "mask"]
        with open(accounts_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for account in accounts:
                row = account.copy()
                row["limit"] = account["limit"] if account["limit"] is not None else ""
                writer.writerow(row)
        print(f"Exported {len(accounts)} accounts to {accounts_file}")
    
    # Export transactions to CSV
    transactions_file = output_path / "transactions.csv"
    if transactions:
        fieldnames = ["transaction_id", "account_id", "user_id", "date", "amount", 
                     "merchant_name", "category", "pending"]
        with open(transactions_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(transactions)
        print(f"Exported {len(transactions)} transactions to {transactions_file}")
    
    # Export liabilities to CSV
    liabilities_file = output_path / "liabilities.csv"
    if liabilities:
        fieldnames = ["account_id", "aprs", "minimum_payment_amount", "last_payment_amount",
                     "is_overdue", "last_statement_balance"]
        with open(liabilities_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(liabilities)
        print(f"Exported {len(liabilities)} liabilities to {liabilities_file}")


def generate_all_data(count: int = 75, output_dir: str = "data") -> None:
    """Generate all synthetic data and export to files.
    
    This is the main entry point for data generation.
    
    Args:
        count: Number of users to generate (default: 75)
        output_dir: Output directory path (default: "data")
    """
    print(f"Generating synthetic data for {count} users...")
    
    # Generate users
    users = generate_users(count)
    print(f"Generated {len(users)} users")
    
    # Generate accounts for all users
    accounts = []
    for user in users:
        user_accounts = generate_accounts(user["user_id"], user)
        accounts.extend(user_accounts)
    print(f"Generated {len(accounts)} accounts")
    
    # Generate transactions for all accounts
    transactions = []
    for account in accounts:
        account_transactions = generate_transactions(
            account["account_id"],
            account["type"],
            account["subtype"],
            next((u for u in users if u["user_id"] == account["user_id"]), {}),
            account
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

