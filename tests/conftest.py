"""Pytest configuration for SpendSense tests.

This file adds the project root to sys.path so that imports like
`from src.features import signal_detection` work correctly.
"""

import sys
from pathlib import Path
import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def realistic_signals():
    """Fixture providing realistic signal data matching actual API responses."""
    return {
        "subscriptions": {
            "monthly_recurring": 0,
            "recurring_merchants": [],
            "merchant_details": [],
            "subscription_share": 0
        },
        "credit_utilization": {
            "is_overdue": False,
            "total_utilization": 31.3,
            "minimum_payment_only": False,
            "accounts": [
                {
                    "balance": 3099.46,
                    "account_id": "acc_TEST_USER_general_wellness_1_02",
                    "limit": 9903.53,
                    "utilization": 31.3
                }
            ],
            "interest_charged": 0,
            "online_spending_share": 26.29,
            "utilization_level": "medium"
        },
        "savings_behavior": {
            "total_savings": 0,
            "growth_rate": 0,
            "net_inflow": 0,
            "travel_filtered_transactions": 0,
            "coverage_level": "low",
            "accounts": [],
            "emergency_fund_coverage": 0,
            "avg_monthly_expenses": 1764.76
        },
        "income_stability": {
            "cash_flow_buffer": 0,
            "median_pay_gap": 0,
            "avg_monthly_expenses": 1764.76,
            "irregular_frequency": False,
            "frequency": "unknown",
            "coefficient_of_variation": 0.0,
            "avg_monthly_income": 0.0
        }
    }

