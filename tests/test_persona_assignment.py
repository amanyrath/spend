"""Tests for persona assignment functionality."""

import pytest
from unittest.mock import patch

from src.personas import assignment


@pytest.fixture
def sample_user_id():
    """Fixture providing a sample user ID."""
    return "user_test_persona"


def test_high_utilization_assignment():
    """Test that user with 68% utilization gets high_utilization persona."""
    # Mock signals showing high utilization
    mock_signals = {
        "credit_utilization": {
            "total_utilization": 68.0,
            "utilization_level": "high",
            "accounts": [
                {
                    "account_id": "acc_123",
                    "balance": 6800.0,
                    "limit": 10000.0,
                    "utilization": 68.0,
                    "utilization_level": "high",
                    "interest_charged": 87.0,
                    "minimum_payment_only": False
                }
            ],
            "interest_charged": 87.0,
            "minimum_payment_only": False,
            "is_overdue": False
        },
        "subscriptions": {
            "recurring_merchants": [],
            "monthly_recurring": 0.0
        },
        "savings_behavior": {
            "total_savings": 1000.0
        },
        "income_stability": {
            "frequency": "biweekly",
            "cash_flow_buffer": 1.5
        }
    }
    
    with patch('src.personas.assignment.get_user_features', return_value=mock_signals), \
         patch('src.personas.assignment.store_persona_assignment') as mock_store:
        
        persona = assignment.assign_persona("user_test", "30d")
        
        assert persona == assignment.PERSONA_HIGH_UTILIZATION
        mock_store.assert_called_once()
        call_args = mock_store.call_args
        assert call_args[0][2] == assignment.PERSONA_HIGH_UTILIZATION


def test_persona_priority():
    """Test that high utilization takes precedence over subscription-heavy."""
    # Mock signals that match both high utilization AND subscription-heavy
    mock_signals = {
        "credit_utilization": {
            "total_utilization": 55.0,  # High utilization
            "utilization_level": "high",
            "accounts": [],
            "interest_charged": 0.0,
            "minimum_payment_only": False,
            "is_overdue": False
        },
        "subscriptions": {
            "recurring_merchants": ["Netflix", "Spotify", "Hulu", "Amazon Prime"],  # 4 merchants
            "monthly_recurring": 75.0,  # High monthly recurring
            "subscription_share": 15.0
        },
        "savings_behavior": {
            "total_savings": 500.0
        },
        "income_stability": {
            "frequency": "biweekly",
            "cash_flow_buffer": 1.2
        }
    }
    
    with patch('src.personas.assignment.get_user_features', return_value=mock_signals), \
         patch('src.personas.assignment.store_persona_assignment') as mock_store:
        
        persona = assignment.assign_persona("user_test", "30d")
        
        # High utilization should win (priority 1) over subscription-heavy (priority 3)
        assert persona == assignment.PERSONA_HIGH_UTILIZATION
        mock_store.assert_called_once()
        call_args = mock_store.call_args
        assert call_args[0][2] == assignment.PERSONA_HIGH_UTILIZATION


def test_default_persona():
    """Test that user with no criteria gets general_wellness persona."""
    # Mock signals that don't match any persona criteria
    mock_signals = {
        "credit_utilization": {
            "total_utilization": 25.0,  # Low utilization
            "utilization_level": "low",
            "accounts": [],
            "interest_charged": 0.0,
            "minimum_payment_only": False,
            "is_overdue": False
        },
        "subscriptions": {
            "recurring_merchants": ["Netflix"],  # Only 1 merchant
            "monthly_recurring": 15.99,
            "subscription_share": 2.0
        },
        "savings_behavior": {
            "total_savings": 500.0,
            "growth_rate": 0.0,
            "net_inflow": 50.0
        },
        "income_stability": {
            "frequency": "biweekly",
            "median_pay_gap": 14,
            "irregular_frequency": False,
            "cash_flow_buffer": 2.0  # Good buffer
        }
    }
    
    with patch('src.personas.assignment.get_user_features', return_value=mock_signals), \
         patch('src.personas.assignment.store_persona_assignment') as mock_store:
        
        persona = assignment.assign_persona("user_test", "30d")
        
        assert persona == assignment.PERSONA_GENERAL_WELLNESS
        mock_store.assert_called_once()
        call_args = mock_store.call_args
        assert call_args[0][2] == assignment.PERSONA_GENERAL_WELLNESS


def test_check_high_utilization_criteria():
    """Test individual check functions for high utilization."""
    # Test case 1: High utilization percentage
    signals1 = {
        "credit_utilization": {
            "total_utilization": 68.0,
            "accounts": []
        }
    }
    assert assignment.check_high_utilization(signals1) == True
    
    # Test case 2: Interest charged
    signals2 = {
        "credit_utilization": {
            "total_utilization": 30.0,
            "interest_charged": 50.0,
            "accounts": []
        }
    }
    assert assignment.check_high_utilization(signals2) == True
    
    # Test case 3: Minimum payment only
    signals3 = {
        "credit_utilization": {
            "total_utilization": 30.0,
            "interest_charged": 0.0,
            "minimum_payment_only": True,
            "accounts": []
        }
    }
    assert assignment.check_high_utilization(signals3) == True
    
    # Test case 4: Overdue
    signals4 = {
        "credit_utilization": {
            "total_utilization": 30.0,
            "interest_charged": 0.0,
            "minimum_payment_only": False,
            "is_overdue": True,
            "accounts": []
        }
    }
    assert assignment.check_high_utilization(signals4) == True
    
    # Test case 5: Low utilization, no flags
    signals5 = {
        "credit_utilization": {
            "total_utilization": 25.0,
            "interest_charged": 0.0,
            "minimum_payment_only": False,
            "is_overdue": False,
            "accounts": []
        }
    }
    assert assignment.check_high_utilization(signals5) == False


def test_check_variable_income_criteria():
    """Test variable income persona check."""
    # Test case 1: Irregular income with low buffer
    signals1 = {
        "income_stability": {
            "median_pay_gap": 50,  # > 45 days
            "irregular_frequency": False,
            "cash_flow_buffer": 0.8  # < 1.0
        }
    }
    assert assignment.check_variable_income(signals1) == True
    
    # Test case 2: Regular income with low buffer (should not match)
    signals2 = {
        "income_stability": {
            "median_pay_gap": 14,
            "irregular_frequency": False,
            "cash_flow_buffer": 0.8
        }
    }
    assert assignment.check_variable_income(signals2) == False
    
    # Test case 3: Irregular income with good buffer (should not match)
    signals3 = {
        "income_stability": {
            "median_pay_gap": 50,
            "irregular_frequency": False,
            "cash_flow_buffer": 2.0  # >= 1.0
        }
    }
    assert assignment.check_variable_income(signals3) == False


def test_check_subscription_heavy_criteria():
    """Test subscription-heavy persona check."""
    # Test case 1: 4 merchants with high monthly recurring
    signals1 = {
        "subscriptions": {
            "recurring_merchants": ["Netflix", "Spotify", "Hulu", "Amazon"],
            "monthly_recurring": 75.0,
            "subscription_share": 8.0
        }
    }
    assert assignment.check_subscription_heavy(signals1) == True
    
    # Test case 2: 3 merchants with high subscription share
    signals2 = {
        "subscriptions": {
            "recurring_merchants": ["Netflix", "Spotify", "Hulu"],
            "monthly_recurring": 40.0,
            "subscription_share": 12.0  # >= 10%
        }
    }
    assert assignment.check_subscription_heavy(signals2) == True
    
    # Test case 3: Only 2 merchants (should not match)
    signals3 = {
        "subscriptions": {
            "recurring_merchants": ["Netflix", "Spotify"],
            "monthly_recurring": 30.0,
            "subscription_share": 5.0
        }
    }
    assert assignment.check_subscription_heavy(signals3) == False


def test_check_savings_builder_criteria():
    """Test savings builder persona check."""
    # Test case 1: Good savings growth with low credit utilization
    signals1 = {
        "savings_behavior": {
            "growth_rate": 5.0,  # >= 2%
            "net_inflow": 150.0
        },
        "credit_utilization": {
            "total_utilization": 25.0,  # < 30%
            "accounts": []
        }
    }
    assert assignment.check_savings_builder(signals1) == True
    
    # Test case 2: High net inflow with low credit utilization
    signals2 = {
        "savings_behavior": {
            "growth_rate": 1.0,
            "net_inflow": 250.0  # >= 200
        },
        "credit_utilization": {
            "total_utilization": 20.0,
            "accounts": []
        }
    }
    assert assignment.check_savings_builder(signals2) == True
    
    # Test case 3: Good savings but high credit utilization (should not match)
    signals3 = {
        "savings_behavior": {
            "growth_rate": 5.0,
            "net_inflow": 150.0
        },
        "credit_utilization": {
            "total_utilization": 45.0,  # >= 30%
            "accounts": []
        }
    }
    assert assignment.check_savings_builder(signals3) == False

