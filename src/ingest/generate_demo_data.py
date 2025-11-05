"""Demo data generator for SpendSense.

This script generates a demo dataset optimized for proof of concept:
- 50 users total (10 per persona × 5 personas)
- For each persona:
  - 2 TEST users with full transaction history
  - 8 regular users with minimal transactions (10 each over 200 days)

TEST users are named: TEST_USER_{persona}_1 and TEST_USER_{persona}_2
Regular users are named: user_{persona}_{001-008}
"""

import json
import random
import argparse
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from faker import Faker

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import functions from data_generator
from src.ingest.data_generator import (
    generate_accounts,
    generate_transactions,
    generate_liabilities,
    apply_diversity_strategy,
    export_data,
    determine_homeownership_by_quintile,
    MONTHS_PER_YEAR,
    CURRENCY_DECIMAL_PLACES
)
from src.utils.plaid_categories import get_category_for_merchant
from src.ingest.data_loader import (
    load_data_to_db,
    load_users_to_firestore,
    load_accounts_to_firestore,
    load_transactions_to_firestore
)
from src.database.firestore import get_db
from src.features.compute_all_vectorized import compute_all_features_vectorized
import src.features.compute_all_vectorized as compute_all_module
from src.personas.assign_all_vectorized import assign_all_users_vectorized
from src.recommend.generate_all_vectorized import generate_all_recommendations_vectorized
from src.ingest.push_from_sqlite import push_all_from_sqlite

# Initialize Faker with deterministic seed
fake = Faker()
Faker.seed(42)
random.seed(42)

# Persona names
PERSONAS = [
    "high_utilization",
    "variable_income",
    "subscription_heavy",
    "savings_builder",
    "general_wellness"
]

# Simple merchants for minimal transactions
SIMPLE_MERCHANTS = {
    "groceries": ["Whole Foods", "Kroger", "Safeway", "Trader Joe's", "Walmart"],
    "gas": ["Shell", "Exxon", "Chevron", "BP"],
    "shopping": ["Amazon", "Target", "Best Buy"],
    "bills": ["Electric Company", "Water Utility", "Internet Provider"]
}


def generate_demo_users() -> List[Dict[str, Any]]:
    """Generate 50 demo users (10 per persona).
    
    For each persona:
    - 2 TEST users: TEST_USER_{persona}_1 and TEST_USER_{persona}_2
    - 8 regular users: user_{persona}_{001-008}
    
    Returns:
        List of user dictionaries with user_id, name, income, created_at, persona_group
    """
    users = []
    base_date = datetime(2024, 1, 1)
    
    # Income levels appropriate for each persona
    persona_income_ranges = {
        "high_utilization": (30000, 70000),  # Lower income, more likely to have credit issues
        "variable_income": (40000, 80000),  # Moderate income, variable patterns
        "subscription_heavy": (50000, 100000),  # Higher income, can afford subscriptions
        "savings_builder": (60000, 120000),  # Higher income, can save
        "general_wellness": (50000, 100000)  # Moderate income, balanced
    }
    
    for persona in PERSONAS:
        income_min, income_max = persona_income_ranges[persona]
        
        # Generate 2 TEST users
        for i in range(1, 3):
            user_id = f"TEST_USER_{persona}_{i}"
            user = {
                "user_id": user_id,
                "name": fake.name(),
                "income": random.randint(income_min, income_max),
                "created_at": (base_date + timedelta(days=random.randint(0, 30))).isoformat(),
                "persona_group": persona,
                "is_constructed": True,
                "is_test_user": True
            }
            users.append(user)
        
        # Generate 8 regular users
        for i in range(1, 9):
            user_id = f"user_{persona}_{i:03d}"
            user = {
                "user_id": user_id,
                "name": fake.name(),
                "income": random.randint(income_min, income_max),
                "created_at": (base_date + timedelta(days=random.randint(0, 30))).isoformat(),
                "persona_group": persona,
                "is_constructed": True,
                "is_test_user": False
            }
            users.append(user)
    
    return users


def generate_minimal_transactions(
    account_id: str,
    user_id: str,
    account_type: str,
    account_subtype: str,
    days: int = 200,
    target_count: int = 10
) -> List[Dict[str, Any]]:
    """Generate minimal transactions for a user.
    
    Generates exactly target_count transactions distributed evenly across days.
    Uses simple transaction types: groceries, gas, shopping, bills.
    No complex patterns (subscriptions, payroll, recurring bills).
    
    Args:
        account_id: Account identifier
        user_id: User identifier
        account_type: "depository" or "credit"
        account_subtype: "checking", "savings", or "credit card"
        days: Number of days of history
        target_count: Number of transactions to generate (default: 10)
        
    Returns:
        List of transaction dictionaries
    """
    transactions = []
    start_date = datetime.now() - timedelta(days=days)
    
    # Calculate spacing between transactions
    if target_count > 0:
        spacing = days / target_count
    else:
        spacing = days
    
    # Generate transaction dates evenly distributed
    transaction_dates = []
    for i in range(target_count):
        days_offset = int(i * spacing + random.uniform(0, spacing * 0.8))
        transaction_date = start_date + timedelta(days=days_offset)
        transaction_dates.append(transaction_date)
    
    # Sort dates to ensure chronological order
    transaction_dates.sort()
    
    # Simple transaction amounts based on account type
    transaction_counter = 1
    
    for date in transaction_dates:
        # Choose a simple merchant category
        category_type = random.choice(["groceries", "gas", "shopping", "bills"])
        merchant = random.choice(SIMPLE_MERCHANTS[category_type])
        
        # Determine amount based on category and account type
        if category_type == "groceries":
            amount = -round(random.uniform(30.0, 120.0), 2)
        elif category_type == "gas":
            amount = -round(random.uniform(25.0, 60.0), 2)
        elif category_type == "shopping":
            amount = -round(random.uniform(15.0, 150.0), 2)
        else:  # bills
            amount = -round(random.uniform(50.0, 200.0), 2)
        
        # For credit cards, amounts are negative
        if account_type == "credit":
            amount = abs(amount) * -1
        
        # Generate transaction
        transaction_id = f"tx_{user_id}_{account_id}_{transaction_counter:04d}"
        transaction = {
            "transaction_id": transaction_id,
            "account_id": account_id,
            "user_id": user_id,
            "date": date.strftime("%Y-%m-%d"),
            "amount": amount,
            "merchant_name": merchant,
            "category": json.dumps(get_category_for_merchant(merchant)),
            "pending": 0,
            "location_address": None,
            "location_city": None,
            "location_region": None,
            "location_postal_code": None,
            "location_country": None,
            "location_lat": None,
            "location_lon": None,
            "iso_currency_code": "USD",
            "payment_channel": random.choice(["online", "in store", "other"]),
            "authorized_date": date.strftime("%Y-%m-%d")
        }
        
        transactions.append(transaction)
        transaction_counter += 1
    
    return transactions


def validate_demo_data(
    users: List[Dict[str, Any]],
    transactions: List[Dict[str, Any]],
    minimal_transaction_count: int = 10
) -> None:
    """Validate demo dataset meets requirements.
    
    Args:
        users: List of user dictionaries
        transactions: List of transaction dictionaries
        minimal_transaction_count: Expected transaction count for regular users
    """
    print("\n" + "=" * 60)
    print("Validating Demo Dataset")
    print("=" * 60)
    
    # Check user counts
    test_users = [u for u in users if u.get("is_test_user")]
    regular_users = [u for u in users if not u.get("is_test_user")]
    
    print(f"Total users: {len(users)}")
    print(f"  TEST users: {len(test_users)}")
    print(f"  Regular users: {len(regular_users)}")
    
    # Check personas
    persona_counts = {}
    for persona in PERSONAS:
        persona_users = [u for u in users if u.get("persona_group") == persona]
        persona_counts[persona] = len(persona_users)
        print(f"  {persona}: {persona_counts[persona]} users")
    
    # Verify all personas have 10 users
    for persona in PERSONAS:
        if persona_counts[persona] != 10:
            print(f"  WARNING: {persona} has {persona_counts[persona]} users (expected 10)")
    
    # Check transactions
    transaction_counts = {}
    for user in users:
        user_id = user["user_id"]
        user_transactions = [t for t in transactions if t["user_id"] == user_id]
        transaction_counts[user_id] = len(user_transactions)
    
    # Check TEST users have full transaction history (should have many transactions)
    test_user_transactions = {uid: transaction_counts.get(uid, 0) for uid in [u["user_id"] for u in test_users]}
    min_test_transactions = min(test_user_transactions.values()) if test_user_transactions else 0
    max_test_transactions = max(test_user_transactions.values()) if test_user_transactions else 0
    
    print(f"\nTEST users transaction counts:")
    print(f"  Minimum: {min_test_transactions}")
    print(f"  Maximum: {max_test_transactions}")
    print(f"  Average: {sum(test_user_transactions.values()) / len(test_user_transactions) if test_user_transactions else 0:.1f}")
    
    if min_test_transactions < 50:
        print(f"  WARNING: Some TEST users have fewer than 50 transactions")
    
    # Check regular users have minimal transactions
    regular_user_transactions = {uid: transaction_counts.get(uid, 0) for uid in [u["user_id"] for u in regular_users]}
    regular_counts = list(regular_user_transactions.values())
    
    print(f"\nRegular users transaction counts:")
    print(f"  Expected: {minimal_transaction_count} per user")
    print(f"  Actual: {regular_counts}")
    
    incorrect_counts = [uid for uid, count in regular_user_transactions.items() if count != minimal_transaction_count]
    if incorrect_counts:
        print(f"  WARNING: {len(incorrect_counts)} regular users have incorrect transaction counts")
        for uid in incorrect_counts[:5]:  # Show first 5
            print(f"    {uid}: {regular_user_transactions[uid]} transactions")
    else:
        print(f"  ✓ All regular users have {minimal_transaction_count} transactions")
    
    print("=" * 60)


def generate_demo_data(
    output_dir: str = "data",
    days: int = 200,
    minimal_transaction_count: int = 10,
    push_to_firebase: bool = False,
    skip_transformations: bool = False
) -> None:
    """Generate demo dataset.
    
    Args:
        output_dir: Output directory path (default: "data")
        days: Number of days of transaction history (default: 200)
        minimal_transaction_count: Number of transactions for regular users (default: 10)
        push_to_firebase: Push processed data to Firebase after transformations (default: False)
        skip_transformations: Skip feature computation, persona assignment, and recommendations (default: False)
    """
    print("=" * 60)
    print("Generating Demo Dataset")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print(f"Days: {days}")
    print(f"Minimal transactions per regular user: {minimal_transaction_count}")
    print("=" * 60)
    print()
    
    # Generate demo users
    print("Step 1: Generating demo users...")
    users = generate_demo_users()
    print(f"  Generated {len(users)} users")
    print(f"    - 10 TEST users (2 per persona)")
    print(f"    - 40 regular users (8 per persona)")
    
    # Collect all incomes for quintile calculation
    all_incomes = [user["income"] for user in users]
    
    # Generate accounts for all users
    print("\nStep 2: Generating accounts...")
    accounts = []
    homeownership_map = {}
    for user in users:
        homeownership_status = determine_homeownership_by_quintile(user["income"], all_incomes)
        homeownership_map[user["user_id"]] = homeownership_status
        user_accounts = generate_accounts(user["user_id"], user, homeownership_status)
        accounts.extend(user_accounts)
    print(f"  Generated {len(accounts)} accounts")
    
    # Generate transactions
    print("\nStep 3: Generating transactions...")
    transactions = []
    user_lookup = {u["user_id"]: u for u in users}
    
    for account in accounts:
        user_id = account["user_id"]
        user_profile = user_lookup.get(user_id, {})
        is_test_user = user_profile.get("is_test_user", False)
        homeownership_status = homeownership_map.get(user_id)
        persona_group = user_profile.get("persona_group")
        
        if is_test_user:
            # TEST users: Generate full transaction history
            account_transactions = generate_transactions(
                account["account_id"],
                account["type"],
                account["subtype"],
                user_profile,
                account,
                days=days,
                homeownership_status=homeownership_status,
                persona_group=persona_group
            )
        else:
            # Regular users: Generate minimal transactions
            # Only generate for checking accounts (skip savings/credit for minimal users)
            if account["subtype"] == "checking":
                account_transactions = generate_minimal_transactions(
                    account["account_id"],
                    user_id,
                    account["type"],
                    account["subtype"],
                    days=days,
                    target_count=minimal_transaction_count
                )
            else:
                # Skip transactions for non-checking accounts for minimal users
                account_transactions = []
        
        transactions.extend(account_transactions)
    
    print(f"  Generated {len(transactions)} transactions")
    
    # Count transactions by user type
    test_user_ids = {u["user_id"] for u in users if u.get("is_test_user")}
    test_transactions = [t for t in transactions if t["user_id"] in test_user_ids]
    regular_transactions = [t for t in transactions if t["user_id"] not in test_user_ids]
    
    print(f"    - TEST users: {len(test_transactions)} transactions")
    print(f"    - Regular users: {len(regular_transactions)} transactions")
    
    # Apply diversity strategy
    print("\nStep 4: Applying diversity strategy...")
    users, accounts, transactions, liabilities = apply_diversity_strategy(
        users, accounts, transactions, []
    )
    print(f"  Generated {len(liabilities)} liabilities")
    
    # Export to files
    print("\nStep 5: Exporting data to files...")
    export_data(users, accounts, transactions, liabilities, output_dir)
    
    # Validate
    validate_demo_data(users, transactions, minimal_transaction_count)
    
    # Load data to SQLite for transformations
    if not skip_transformations:
        print("\n" + "=" * 60)
        print("Loading Data to SQLite")
        print("=" * 60)
        try:
            load_data_to_db(data_dir=output_dir)
            print("  ✓ Data loaded to SQLite successfully")
        except Exception as e:
            print(f"  ✗ Error loading data to SQLite: {e}")
            print("  Skipping transformations...")
            skip_transformations = True
    
    # Perform transformations
    if not skip_transformations:
        print("\n" + "=" * 60)
        print("Computing Features")
        print("=" * 60)
        try:
            # Temporarily disable USE_FIRESTORE to force SQLite usage
            # (compute_all_features_vectorized doesn't accept use_sqlite parameter)
            original_use_firestore = compute_all_module.USE_FIRESTORE
            compute_all_module.USE_FIRESTORE = False
            
            try:
                # Compute features for 30d window
                print("  Computing features for 30d window...")
                compute_all_features_vectorized(window_days=30, time_window="30d", verbose=True)
                
                # Compute features for 180d window
                print("\n  Computing features for 180d window...")
                compute_all_features_vectorized(window_days=180, time_window="180d", verbose=True)
                
                print("\n  ✓ Features computed successfully")
            finally:
                # Restore USE_FIRESTORE
                compute_all_module.USE_FIRESTORE = original_use_firestore
            
        except Exception as e:
            print(f"  ✗ Error computing features: {e}")
            raise
        
        print("\n" + "=" * 60)
        print("Assigning Personas")
        print("=" * 60)
        try:
            assign_all_users_vectorized(time_windows=['30d', '180d'], use_sqlite=True, verbose=True)
            print("\n  ✓ Personas assigned successfully")
        except Exception as e:
            print(f"  ✗ Error assigning personas: {e}")
            raise
        
        print("\n" + "=" * 60)
        print("Generating Recommendations")
        print("=" * 60)
        try:
            generate_all_recommendations_vectorized(time_windows=['30d', '180d'], use_sqlite=True, verbose=True)
            print("\n  ✓ Recommendations generated successfully")
        except Exception as e:
            print(f"  ✗ Error generating recommendations: {e}")
            raise
    
    # Push to Firebase if requested
    if push_to_firebase:
        print("\n" + "=" * 60)
        print("Pushing Data to Firebase")
        print("=" * 60)
        
        # Check if Firebase is available
        db = get_db()
        if db is None:
            print("\nWARNING: Firebase not initialized!")
            print("  Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists")
            print("  Or set FIRESTORE_EMULATOR_HOST for emulator")
            print("  Skipping Firebase push...")
        else:
            # Check if using emulator or production
            if os.getenv('FIRESTORE_EMULATOR_HOST'):
                print(f"  Using Firebase emulator at {os.getenv('FIRESTORE_EMULATOR_HOST')}")
            else:
                print("  Using production Firebase")
            
            try:
                if skip_transformations:
                    # If transformations were skipped, only push raw data
                    print("\n  Pushing raw data only (transformations skipped)...")
                    load_users_to_firestore(data_dir=output_dir)
                    load_accounts_to_firestore(data_dir=output_dir)
                    load_transactions_to_firestore(data_dir=output_dir, batch_size=500)
                    print("\n  ✓ Raw data successfully pushed to Firebase!")
                else:
                    # Push all data (raw + processed) from SQLite
                    print("\n  Pushing all data from SQLite (raw + processed)...")
                    push_all_from_sqlite(
                        collections=['users', 'accounts', 'transactions', 'features', 'personas', 'recommendations'],
                        dry_run=False,
                        batch_size=500,
                        delay=0.5,
                        max_retries=3
                    )
                    print("\n  ✓ All data successfully pushed to Firebase!")
            except Exception as e:
                print(f"\n  ERROR: Failed to push to Firebase: {e}")
                print("  Data files were still generated successfully.")
    
    print("\n" + "=" * 60)
    print("Demo Dataset Generation Complete!")
    print("=" * 60)
    print(f"\nTEST users (with full transaction history):")
    for persona in PERSONAS:
        print(f"  - TEST_USER_{persona}_1")
        print(f"  - TEST_USER_{persona}_2")
    print(f"\nRegular users (with {minimal_transaction_count} transactions each):")
    for persona in PERSONAS:
        print(f"  - user_{persona}_001 through user_{persona}_008")
    print()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate demo dataset for SpendSense proof of concept",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate demo dataset with defaults (10 transactions per regular user, 200 days)
  python3 src/ingest/generate_demo_data.py

  # Generate with custom minimal transaction count
  python3 src/ingest/generate_demo_data.py --minimal-transactions 10

  # Generate with custom output directory
  python3 src/ingest/generate_demo_data.py --output-dir demo_data

  # Generate with custom days
  python3 src/ingest/generate_demo_data.py --days 200

  # Generate and push to Firebase (includes all transformations)
  python3 src/ingest/generate_demo_data.py --push-to-firebase

  # Generate raw data only (skip transformations)
  python3 src/ingest/generate_demo_data.py --skip-transformations

  # Generate and push to Firebase emulator
  export FIRESTORE_EMULATOR_HOST=localhost:8080
  python3 src/ingest/generate_demo_data.py --push-to-firebase
        """
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Output directory for generated files (default: data)"
    )
    
    parser.add_argument(
        "--minimal-transactions",
        type=int,
        default=10,
        help="Number of transactions for regular users (default: 10)"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=200,
        help="Number of days of transaction history (default: 200)"
    )
    
    parser.add_argument(
        "--push-to-firebase",
        action="store_true",
        help="Push processed data to Firebase Firestore after transformations (includes features, personas, recommendations)"
    )
    
    parser.add_argument(
        "--skip-transformations",
        action="store_true",
        help="Skip feature computation, persona assignment, and recommendation generation (raw data only)"
    )
    
    args = parser.parse_args()
    
    generate_demo_data(
        output_dir=args.output_dir,
        days=args.days,
        minimal_transaction_count=args.minimal_transactions,
        push_to_firebase=args.push_to_firebase,
        skip_transformations=args.skip_transformations
    )


if __name__ == "__main__":
    main()

