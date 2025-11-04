"""Tests for recommendation engine functionality."""

import pytest
from unittest.mock import patch, MagicMock

from src.recommend import engine
from src.recommend import rationale_generator
from src.guardrails import tone_validator


@pytest.fixture
def sample_user_id():
    """Fixture providing a sample user ID."""
    return "user_test_rec"


@pytest.fixture
def mock_signals():
    """Fixture providing mock signal data."""
    return {
        "credit_utilization": {
            "total_utilization": 68.0,
            "utilization_level": "high",
            "accounts": [
                {
                    "account_id": "acc_123",
                    "balance": 6800.0,
                    "limit": 10000.0,
                    "utilization": 68.0,
                    "mask": "4523",
                    "subtype": "Visa"
                }
            ],
            "interest_charged": 87.0,
            "minimum_payment_only": False,
            "is_overdue": False
        },
        "subscriptions": {
            "recurring_merchants": ["Netflix", "Spotify", "Hulu"],
            "monthly_recurring": 62.97,
            "subscription_share": 8.5
        },
        "savings_behavior": {
            "total_savings": 1200.0,
            "growth_rate": 2.5,
            "net_inflow": 200.0
        },
        "income_stability": {
            "frequency": "biweekly",
            "cash_flow_buffer": 0.8,
            "median_pay_gap": 14
        }
    }


@pytest.fixture
def mock_persona_assignment():
    """Fixture providing mock persona assignment."""
    return {
        "persona": "high_utilization",
        "criteria_met": ["credit_utilization >= 0.50"],
        "assigned_at": "2025-01-01T00:00:00"
    }


def test_recommendation_count(sample_user_id, mock_signals, mock_persona_assignment):
    """Test that recommendation generation produces 3-5 education + 1-3 offers."""
    with patch('src.recommend.engine.get_persona_assignment', return_value=mock_persona_assignment), \
         patch('src.recommend.engine.get_user_features', return_value=mock_signals), \
         patch('src.recommend.engine.store_recommendation'):
        
        recommendations = engine.generate_recommendations(sample_user_id, "30d")
        
        # Should generate recommendations
        assert len(recommendations) > 0
        
        # Count education vs offers
        education_count = sum(1 for r in recommendations if r["type"] == "education")
        offer_count = sum(1 for r in recommendations if r["type"] == "partner_offer")
        
        # Should have 3-5 education items
        assert 3 <= education_count <= 5
        
        # Should have 1-3 offers
        assert 1 <= offer_count <= 3


def test_rationale_substitution(mock_signals):
    """Test that rationale generator substitutes variables with actual data."""
    template = "Your {card_name} is at {utilization}% utilization ({balance} of {limit} limit). Bringing this below 30% could improve your credit score."
    
    rationale = rationale_generator.generate_rationale(template, mock_signals)
    
    # Check that variables were substituted
    assert "{card_name}" not in rationale
    assert "{utilization}" not in rationale
    assert "{balance}" not in rationale
    assert "{limit}" not in rationale
    
    # Check that actual values appear
    assert "68" in rationale or "68.0" in rationale  # Utilization
    assert "$" in rationale  # Currency formatting
    assert "4523" in rationale  # Card mask


def test_rationale_subscription_variables(mock_signals):
    """Test rationale substitution for subscription variables."""
    template = "You have {subscription_count} active subscriptions totaling ${monthly_recurring} per month."
    
    rationale = rationale_generator.generate_rationale(template, mock_signals)
    
    assert "{subscription_count}" not in rationale
    assert "{monthly_recurring}" not in rationale
    assert "3" in rationale  # Subscription count
    assert "$" in rationale  # Currency formatting


def test_tone_validation():
    """Test that tone validator catches prohibited phrases."""
    # Test prohibited phrase
    bad_text = "You're overspending on subscriptions."
    assert tone_validator.validate_tone(bad_text) == False
    
    # Test another prohibited phrase
    bad_text2 = "This shows bad habits in your spending."
    assert tone_validator.validate_tone(bad_text2) == False
    
    # Test acceptable text
    good_text = "Your data shows you have several active subscriptions. Reviewing these could help you optimize your spending."
    assert tone_validator.validate_tone(good_text) == True
    
    # Test text with no prohibited phrases
    neutral_text = "You might consider reviewing your subscription services."
    assert tone_validator.validate_tone(neutral_text) == True


def test_decision_trace_structure(mock_signals, mock_persona_assignment):
    """Test that decision trace includes all required fields."""
    recommendation = {
        "recommendation_id": "rec_test123",
        "user_id": "user_test",
        "type": "education",
        "content_id": "edu_credit_util_101",
        "title": "Understanding Credit Utilization",
        "rationale": "Your Visa ending in 4523 is at 68% utilization...",
        "tone_valid": True,
        "eligible": True
    }
    
    trace = engine.create_decision_trace(recommendation, mock_signals, "high_utilization")
    
    # Check required fields
    assert "persona_match" in trace
    assert "content_id" in trace
    assert "signals_used" in trace
    assert "guardrails_passed" in trace
    assert "timestamp" in trace
    
    # Check values
    assert trace["persona_match"] == "high_utilization"
    assert trace["content_id"] == "edu_credit_util_101"
    assert isinstance(trace["signals_used"], list)
    assert isinstance(trace["guardrails_passed"], dict)
    assert "tone_check" in trace["guardrails_passed"]
    assert "eligibility_check" in trace["guardrails_passed"]


def test_offer_eligibility():
    """Test offer eligibility checking."""
    # Test offer with credit utilization requirement
    offer = {
        "offer_id": "offer_test",
        "eligibility_criteria": {
            "credit_utilization": {"min": 0.5},
            "is_overdue": {"equals": False}
        }
    }
    
    # User with high utilization, not overdue
    signals1 = {
        "credit_utilization": {
            "total_utilization": 68.0,
            "is_overdue": False
        }
    }
    assert engine.check_offer_eligibility(offer, signals1) == True
    
    # User with low utilization
    signals2 = {
        "credit_utilization": {
            "total_utilization": 30.0,
            "is_overdue": False
        }
    }
    assert engine.check_offer_eligibility(offer, signals2) == False
    
    # User with overdue account
    signals3 = {
        "credit_utilization": {
            "total_utilization": 68.0,
            "is_overdue": True
        }
    }
    assert engine.check_offer_eligibility(offer, signals3) == False


def test_education_content_matching(mock_signals):
    """Test that education content is matched to persona correctly."""
    persona = "high_utilization"
    
    matched = engine.match_education_content(persona, mock_signals)
    
    # Should return content items
    assert len(matched) > 0
    
    # All items should be for high_utilization persona
    for item in matched:
        assert "high_utilization" in item.get("personas", [])


def test_format_currency():
    """Test currency formatting."""
    assert rationale_generator.format_currency(1234.56) == "$1,234.56"
    assert rationale_generator.format_currency(100.0) == "$100.00"
    assert rationale_generator.format_currency(0) == "$0.00"
    assert rationale_generator.format_currency(-50.0) == "-$50.00"


def test_format_percentage():
    """Test percentage formatting."""
    # Test as decimal
    assert rationale_generator.format_percentage(0.68, decimal=True) == "68.0%"
    assert rationale_generator.format_percentage(0.255, decimal=True) == "25.5%"
    
    # Test as percentage
    assert rationale_generator.format_percentage(68.0, decimal=False) == "68.0%"
    assert rationale_generator.format_percentage(25.5, decimal=False) == "25.5%"


def test_generate_recommendations_full_flow(sample_user_id, mock_signals, mock_persona_assignment):
    """Test full recommendation generation flow."""
    with patch('src.recommend.engine.get_persona_assignment', return_value=mock_persona_assignment), \
         patch('src.recommend.engine.get_user_features', return_value=mock_signals), \
         patch('src.recommend.engine.store_recommendation') as mock_store:
        
        recommendations = engine.generate_recommendations(sample_user_id, "30d")
        
        # Should generate recommendations
        assert len(recommendations) > 0
        
        # Verify all recommendations have required fields
        for rec in recommendations:
            assert "recommendation_id" in rec
            assert "user_id" in rec
            assert "type" in rec
            assert "title" in rec
            assert "rationale" in rec
            assert "decision_trace" in rec
            assert rec["tone_valid"] == True
            assert rec["eligible"] == True
        
        # Verify store_recommendation was called for each recommendation
        assert mock_store.call_count == len(recommendations)

