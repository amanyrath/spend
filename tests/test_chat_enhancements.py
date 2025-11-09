"""Tests for chat enhancements including transaction analysis, safety features, and API integration."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.chat.transaction_analysis import (
    calculate_weekday_spending,
    calculate_monthly_progression,
    calculate_spending_velocity,
    build_detailed_category_analysis,
    analyze_merchant_patterns,
    analyze_payment_channels,
    analyze_by_account,
    analyze_pending_transactions
)
from src.guardrails.data_sanitizer import DataSanitizer
from src.guardrails.guardrails_ai import MerchantNameValidator, ChatGuardrails


# Sample test data
SAMPLE_TRANSACTIONS = [
    {
        'transaction_id': 'txn_001',
        'account_id': 'acc_001',
        'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
        'amount': -50.00,
        'merchant_name': 'Amazon',
        'category': ['Shopping', 'Online'],
        'pending': False,
        'payment_channel': 'online'
    },
    {
        'transaction_id': 'txn_002',
        'account_id': 'acc_001',
        'date': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
        'amount': -25.00,
        'merchant_name': 'Starbucks',
        'category': ['Food and Drink', 'Cafe'],
        'pending': False,
        'payment_channel': 'in store'
    },
    {
        'transaction_id': 'txn_003',
        'account_id': 'acc_002',
        'date': (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
        'amount': -100.00,
        'merchant_name': 'Target',
        'category': ['Shopping', 'General'],
        'pending': True,
        'payment_channel': 'in store'
    },
    {
        'transaction_id': 'txn_004',
        'account_id': 'acc_001',
        'date': (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
        'amount': 1000.00,  # Deposit
        'merchant_name': 'Payroll',
        'category': ['Transfer', 'Deposit'],
        'pending': False,
        'payment_channel': 'other'
    },
]

SAMPLE_ACCOUNTS = [
    {
        'account_id': 'acc_001',
        'type': 'depository',
        'subtype': 'checking',
        'mask': '1234',
        'balance': 2500.00
    },
    {
        'account_id': 'acc_002',
        'type': 'credit',
        'subtype': 'credit card',
        'mask': '5678',
        'balance': 100.00,
        'limit': 5000.00
    }
]


class TestTemporalAnalysis:
    """Tests for temporal transaction analysis functions."""
    
    def test_calculate_weekday_spending(self):
        """Test weekday vs weekend spending calculation."""
        result = calculate_weekday_spending(SAMPLE_TRANSACTIONS)
        
        assert 'weekday_avg' in result
        assert 'weekend_avg' in result
        assert 'weekday_total' in result
        assert 'weekend_total' in result
        assert 'highest_day' in result
        assert result['weekday_count'] >= 0
        assert result['weekend_count'] >= 0
    
    def test_calculate_monthly_progression(self):
        """Test month-to-date spending calculation."""
        result = calculate_monthly_progression(SAMPLE_TRANSACTIONS)
        
        assert 'spent_mtd' in result
        assert 'transaction_count_mtd' in result
        assert 'days_elapsed' in result
        assert 'days_remaining' in result
        assert 'daily_avg' in result
        assert 'projected_monthly' in result
        assert 'current_month' in result
        assert result['days_elapsed'] > 0
    
    def test_calculate_spending_velocity(self):
        """Test spending trend calculation."""
        result = calculate_spending_velocity(SAMPLE_TRANSACTIONS, window_days=30)
        
        assert 'first_half_spending' in result
        assert 'second_half_spending' in result
        assert 'change_pct' in result
        assert 'trend' in result
        assert result['trend'] in ['increasing', 'decreasing', 'stable']


class TestCategoryAnalysis:
    """Tests for category-based analysis."""
    
    def test_build_detailed_category_analysis(self):
        """Test category breakdown analysis."""
        result = build_detailed_category_analysis(SAMPLE_TRANSACTIONS)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check structure of first category
        cat = result[0]
        assert 'category' in cat
        assert 'amount' in cat
        assert 'percentage' in cat
        assert 'transaction_count' in cat
        assert 'avg_transaction' in cat
        
        # Verify amounts are positive
        assert cat['amount'] >= 0
        assert cat['percentage'] >= 0
    
    def test_category_analysis_empty_transactions(self):
        """Test category analysis with empty transaction list."""
        result = build_detailed_category_analysis([])
        assert result == []


class TestMerchantAnalysis:
    """Tests for merchant pattern analysis."""
    
    def test_analyze_merchant_patterns(self):
        """Test frequent merchant identification."""
        # Create transactions with repeated merchant
        transactions = SAMPLE_TRANSACTIONS.copy()
        for i in range(5):
            transactions.append({
                'transaction_id': f'txn_freq_{i}',
                'account_id': 'acc_001',
                'date': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                'amount': -15.00,
                'merchant_name': 'Netflix',
                'category': ['Entertainment', 'Subscription'],
                'pending': False,
                'payment_channel': 'online'
            })
        
        result = analyze_merchant_patterns(transactions)
        
        assert isinstance(result, list)
        # Should find Netflix as frequent merchant (3+ visits)
        merchant_names = [m[0] for m in result]
        assert 'Netflix' in merchant_names
        
        # Check structure
        if result:
            merchant, data = result[0]
            assert 'visit_count' in data
            assert 'total_spent' in data
            assert data['visit_count'] >= 3
    
    def test_merchant_analysis_no_frequent_merchants(self):
        """Test merchant analysis when no merchant has 3+ visits."""
        result = analyze_merchant_patterns(SAMPLE_TRANSACTIONS)
        assert isinstance(result, list)


class TestPaymentChannelAnalysis:
    """Tests for payment channel analysis."""
    
    def test_analyze_payment_channels(self):
        """Test payment channel breakdown."""
        result = analyze_payment_channels(SAMPLE_TRANSACTIONS)
        
        assert isinstance(result, dict)
        # Should have some channels
        assert len(result) > 0
        
        # Check structure
        for channel, data in result.items():
            assert 'count' in data
            assert 'amount' in data
            assert data['count'] >= 0
            assert data['amount'] >= 0


class TestAccountAnalysis:
    """Tests for account-level analysis."""
    
    def test_analyze_by_account(self):
        """Test account-specific transaction grouping."""
        result = analyze_by_account(SAMPLE_TRANSACTIONS, SAMPLE_ACCOUNTS)
        
        assert isinstance(result, dict)
        assert len(result) > 0
        
        # Check structure for first account
        account_id = list(result.keys())[0]
        activity = result[account_id]
        
        assert 'mask' in activity
        assert 'type' in activity
        assert 'subtype' in activity
        assert 'transaction_count' in activity
        assert 'total_spent' in activity
        assert 'total_income' in activity
        assert activity['transaction_count'] > 0
    
    def test_account_analysis_empty_accounts(self):
        """Test account analysis with empty account list."""
        result = analyze_by_account(SAMPLE_TRANSACTIONS, [])
        assert isinstance(result, dict)


class TestPendingTransactions:
    """Tests for pending transaction analysis."""
    
    def test_analyze_pending_transactions(self):
        """Test pending transaction tracking."""
        result = analyze_pending_transactions(SAMPLE_TRANSACTIONS)
        
        assert 'count' in result
        assert 'pending_charges' in result
        assert 'pending_deposits' in result
        assert 'net_pending' in result
        
        # We have one pending transaction in sample data
        assert result['count'] >= 1
        assert result['pending_charges'] > 0
    
    def test_pending_analysis_no_pending(self):
        """Test pending analysis with no pending transactions."""
        non_pending = [t for t in SAMPLE_TRANSACTIONS if not t.get('pending')]
        result = analyze_pending_transactions(non_pending)
        
        assert result['count'] == 0
        assert result['pending_charges'] == 0
        assert result['pending_deposits'] == 0


class TestDataSanitizer:
    """Tests for enhanced data sanitization features."""
    
    def setup_method(self):
        """Initialize sanitizer for each test."""
        self.sanitizer = DataSanitizer()
    
    def test_sanitize_merchant_name(self):
        """Test merchant name sanitization."""
        # Test email in merchant name
        result = self.sanitizer.sanitize_merchant_name("Store@email.com")
        assert "@" not in result or "[REDACTED]" in result
        
        # Test phone in merchant name
        result = self.sanitizer.sanitize_merchant_name("Shop 555-123-4567")
        assert "555-123-4567" not in result
        
        # Test normal merchant name
        result = self.sanitizer.sanitize_merchant_name("Target")
        assert result == "Target"
    
    def test_sample_transactions_representative(self):
        """Test representative transaction sampling."""
        # Create many transactions
        many_transactions = []
        for i in range(200):
            many_transactions.append({
                'transaction_id': f'txn_{i}',
                'account_id': 'acc_001',
                'date': (datetime.now() - timedelta(days=i % 30)).strftime('%Y-%m-%d'),
                'amount': -(10 + i % 50),
                'merchant_name': f'Merchant_{i % 10}',
                'category': ['Shopping'],
                'pending': False
            })
        
        result = self.sanitizer.sample_transactions_representative(many_transactions, max_count=50)
        
        assert len(result) <= 50
        assert len(result) > 0
        # Check uniqueness by transaction_id
        ids = [t['transaction_id'] for t in result]
        assert len(ids) == len(set(ids))
    
    def test_estimate_context_tokens(self):
        """Test token estimation."""
        user_features = {
            'credit_utilization': {'total_utilization': 65.0},
            'subscriptions': {'monthly_recurring': 100.0}
        }
        
        tokens = self.sanitizer.estimate_context_tokens(user_features, SAMPLE_TRANSACTIONS)
        
        assert isinstance(tokens, int)
        assert tokens > 0
        assert tokens < 10000  # Should be reasonable
    
    def test_reduce_transaction_context(self):
        """Test transaction context reduction."""
        # Create many transactions
        many_transactions = [SAMPLE_TRANSACTIONS[0].copy() for _ in range(100)]
        
        result = self.sanitizer.reduce_transaction_context(many_transactions, target_tokens=500)
        
        assert len(result) < len(many_transactions)
        assert len(result) >= 10  # Should keep at least 10
    
    def test_bucket_transaction_amounts(self):
        """Test amount bucketing functionality."""
        # Test with bucketing enabled
        result = self.sanitizer.bucket_transaction_amounts(SAMPLE_TRANSACTIONS, enabled=True)
        
        assert len(result) == len(SAMPLE_TRANSACTIONS)
        # Check that buckets were added
        for txn in result:
            if txn.get('amount', 0) != 0:
                # Income transactions might not have buckets
                if txn['amount'] < 0:
                    assert 'amount_bucket' in txn
        
        # Test with bucketing disabled
        result = self.sanitizer.bucket_transaction_amounts(SAMPLE_TRANSACTIONS, enabled=False)
        assert len(result) == len(SAMPLE_TRANSACTIONS)


class TestMerchantNameValidator:
    """Tests for merchant name validation."""
    
    def test_validate_clean_merchant_name(self):
        """Test validation of clean merchant names."""
        validator = MerchantNameValidator()
        
        # Should pass
        result = validator.validate("Target")
        assert result == "Target"
        
        result = validator.validate("Amazon")
        assert result == "Amazon"
    
    def test_validate_merchant_with_pii(self):
        """Test validation catches PII patterns."""
        validator = MerchantNameValidator()
        
        # Should fail with email
        with pytest.raises(ValueError) as exc_info:
            validator.validate("store@email.com")
        assert "sensitive patterns" in str(exc_info.value).lower()
        
        # Should fail with phone
        with pytest.raises(ValueError):
            validator.validate("Shop 555-123-4567")


class TestChatGuardrails:
    """Tests for chat guardrails integration."""
    
    def setup_method(self):
        """Initialize guardrails for each test."""
        self.guardrails = ChatGuardrails()
    
    def test_validate_merchant_names(self):
        """Test bulk merchant name validation."""
        merchant_names = ["Target", "Amazon", "Starbucks"]
        
        all_valid, invalid = self.guardrails.validate_merchant_names(merchant_names)
        
        assert all_valid is True
        assert len(invalid) == 0
    
    def test_validate_merchant_names_with_pii(self):
        """Test merchant validation catches PII."""
        merchant_names = ["Target", "store@email.com", "Amazon"]
        
        all_valid, invalid = self.guardrails.validate_merchant_names(merchant_names)
        
        assert all_valid is False
        assert len(invalid) > 0
        assert "store@email.com" in invalid


class TestChatAPIIntegration:
    """Integration tests for chat API with new features."""
    
    @pytest.fixture
    def mock_user_features(self):
        """Mock user features for testing."""
        return {
            'credit_utilization': {
                'total_utilization': 65.0,
                'accounts': [{
                    'account_mask': '1234',
                    'utilization': 0.65,
                    'balance': 3250.00,
                    'limit': 5000.00
                }]
            },
            'subscriptions': {
                'monthly_recurring': 75.00,
                'recurring_merchants': [
                    {'merchant': 'Netflix', 'amount': 15.99},
                    {'merchant': 'Spotify', 'amount': 9.99}
                ]
            }
        }
    
    def test_transaction_window_validation(self):
        """Test that transaction window validation works."""
        from pydantic import ValidationError
        from src.api.main import ChatRequest
        
        # Valid window
        request = ChatRequest(user_id="user_001", message="Test", transaction_window_days=30)
        assert request.transaction_window_days == 30
        
        # Window too small
        with pytest.raises(ValidationError):
            ChatRequest(user_id="user_001", message="Test", transaction_window_days=5)
        
        # Window too large
        with pytest.raises(ValidationError):
            ChatRequest(user_id="user_001", message="Test", transaction_window_days=200)
        
        # Default window
        request = ChatRequest(user_id="user_001", message="Test")
        assert request.transaction_window_days == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])







