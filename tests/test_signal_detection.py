"""Tests for signal detection functionality."""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.features import signal_detection
from src.database import db


@pytest.fixture
def sample_user_id():
    """Fixture providing a sample user ID."""
    return "user_test_123"


@pytest.fixture
def mock_transactions():
    """Fixture providing mock transaction data."""
    base_date = datetime.now() - timedelta(days=90)
    
    # Netflix subscription: monthly payments
    netflix_txs = []
    for i in range(4):
        tx_date = base_date + timedelta(days=i * 30)
        netflix_txs.append({
            "merchant_name": "Netflix",
            "date": tx_date.strftime("%Y-%m-%d"),
            "amount": -15.99,
            "category": "entertainment"
        })
    
    # Grocery transactions (non-recurring)
    grocery_txs = []
    for i in range(10):
        tx_date = base_date + timedelta(days=i * 7)
        grocery_txs.append({
            "merchant_name": "Whole Foods",
            "date": tx_date.strftime("%Y-%m-%d"),
            "amount": -85.50 + (i * 5),
            "category": "groceries"
        })
    
    return netflix_txs + grocery_txs


def test_subscription_detection(sample_user_id, mock_transactions):
    """Test that subscription detection correctly identifies Netflix recurring monthly."""
    with patch('src.features.signal_detection.db.fetch_all', return_value=mock_transactions):
        result = signal_detection.detect_subscriptions(sample_user_id, window_days=90)
        
        assert "recurring_merchants" in result
        assert "Netflix" in result["recurring_merchants"]
        assert result["monthly_recurring"] > 0
        assert len(result["merchant_details"]) > 0
        
        # Check Netflix details
        netflix_detail = next(
            (m for m in result["merchant_details"] if m["merchant"] == "Netflix"),
            None
        )
        assert netflix_detail is not None
        assert netflix_detail["frequency"] == "monthly"


def test_credit_utilization():
    """Test credit utilization calculation."""
    user_id = "user_test_credit"
    
    # Mock credit account with 68% utilization
    mock_accounts = [
        {
            "account_id": "acc_123",
            "balance": 6800.0,
            "limit": 10000.0,
            "type": "credit",
            "subtype": "credit card"
        }
    ]
    
    mock_transactions = []
    
    with patch('src.features.signal_detection.db.fetch_all') as mock_fetch:
        def fetch_side_effect(query, params):
            if "accounts" in query.lower() or "FROM accounts" in query:
                return mock_accounts
            elif "FROM transactions" in query:
                return mock_transactions
            return []
        
        mock_fetch.side_effect = fetch_side_effect
        
        result = signal_detection.detect_credit_utilization(user_id, window_days=30)
        
        assert result["total_utilization"] == pytest.approx(68.0, abs=0.1)
        assert result["utilization_level"] == "high"
        assert len(result["accounts"]) == 1
        assert result["accounts"][0]["utilization"] == pytest.approx(68.0, abs=0.1)


def test_savings_behavior():
    """Test savings behavior detection computes growth rate."""
    user_id = "user_test_savings"
    
    # Mock savings account
    mock_accounts = [
        {
            "account_id": "acc_savings_123",
            "balance": 5000.0,
            "type": "depository",
            "subtype": "savings"
        }
    ]
    
    # Mock transactions showing net inflow
    base_date = datetime.now() - timedelta(days=180)
    mock_transactions = []
    
    # Add some deposits
    for i in range(6):
        tx_date = base_date + timedelta(days=i * 30)
        mock_transactions.append({
            "account_id": "acc_savings_123",
            "date": tx_date.strftime("%Y-%m-%d"),
            "amount": 500.0  # Deposits
        })
    
    mock_checking_expenses = [
        {
            "total_spend": 3000.0
        }
    ]
    
    with patch('src.features.signal_detection.db.fetch_all') as mock_fetch_all, \
         patch('src.features.signal_detection.db.fetch_one') as mock_fetch_one:
        
        def fetch_all_side_effect(query, params):
            if "savings" in query.lower() or "subtype IN" in query:
                return mock_accounts
            elif "FROM transactions" in query:
                return mock_transactions
            return []
        
        def fetch_one_side_effect(query, params):
            if "checking" in query.lower():
                return mock_checking_expenses[0]
            return None
        
        mock_fetch_all.side_effect = fetch_all_side_effect
        mock_fetch_one.side_effect = fetch_one_side_effect
        
        result = signal_detection.detect_savings_behavior(user_id, window_days=180)
        
        assert "total_savings" in result
        assert "growth_rate" in result
        assert "emergency_fund_coverage" in result
        assert "coverage_level" in result
        assert result["total_savings"] > 0


def test_income_stability():
    """Test income stability detection identifies biweekly payroll."""
    user_id = "user_test_income"
    
    # Mock checking account
    mock_account = {
        "account_id": "acc_checking_123",
        "balance": 2000.0
    }
    
    # Mock biweekly payroll deposits
    base_date = datetime.now() - timedelta(days=180)
    mock_payroll = []
    
    for i in range(12):  # ~6 months of biweekly pay
        tx_date = base_date + timedelta(days=i * 14)
        mock_payroll.append({
            "date": tx_date.strftime("%Y-%m-%d"),
            "amount": 2500.0,
            "merchant_name": "ACME Corp Payroll",
            "category": "income"
        })
    
    mock_expenses = {
        "total_spend": 4000.0
    }
    
    with patch('src.features.signal_detection.db.fetch_one') as mock_fetch_one, \
         patch('src.features.signal_detection.db.fetch_all') as mock_fetch_all:
        
        def fetch_one_side_effect(query, params):
            if "checking" in query.lower():
                return mock_account
            elif "expense" in query.lower() or "total_spend" in query:
                return mock_expenses
            return None
        
        def fetch_all_side_effect(query, params):
            if "payroll" in query.lower() or "amount > 500" in query:
                return mock_payroll
            return []
        
        mock_fetch_one.side_effect = fetch_one_side_effect
        mock_fetch_all.side_effect = fetch_all_side_effect
        
        result = signal_detection.detect_income_stability(user_id, window_days=180)
        
        assert "frequency" in result
        assert result["frequency"] == "biweekly"
        assert result["median_pay_gap"] == 14
        assert result["irregular_frequency"] == False
        assert "cash_flow_buffer" in result


def test_compute_all_features(sample_user_id):
    """Test that compute_all_features calls all detection functions and stores results."""
    with patch('src.features.signal_detection.detect_subscriptions') as mock_sub, \
         patch('src.features.signal_detection.detect_credit_utilization') as mock_credit, \
         patch('src.features.signal_detection.detect_savings_behavior') as mock_savings, \
         patch('src.features.signal_detection.detect_income_stability') as mock_income, \
         patch('src.features.signal_detection.store_feature') as mock_store:
        
        mock_sub.return_value = {"recurring_merchants": []}
        mock_credit.return_value = {"total_utilization": 0.0}
        mock_savings.return_value = {"total_savings": 0.0}
        mock_income.return_value = {"frequency": "unknown"}
        
        result = signal_detection.compute_all_features(sample_user_id, "30d")
        
        # Verify all detection functions were called
        mock_sub.assert_called_once()
        mock_credit.assert_called_once()
        mock_savings.assert_called_once()
        mock_income.assert_called_once()
        
        # Verify store_feature was called 4 times (once per signal type)
        assert mock_store.call_count == 4
        
        # Verify result structure
        assert "subscriptions" in result
        assert "credit_utilization" in result
        assert "savings_behavior" in result
        assert "income_stability" in result











