"""Tests for rate limiting functionality."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import os

from src.api.rate_limit import (
    check_rate_limit,
    RATE_LIMIT_MESSAGES,
    RATE_LIMIT_WINDOW,
    RATE_LIMITS,
    InMemoryRateLimitStorage,
    DatabaseRateLimitStorage,
    cleanup_rate_limits
)


class TestInMemoryRateLimitStorage:
    """Tests for in-memory rate limit storage."""
    
    def test_get_count_empty(self):
        """Test getting count for new user/endpoint."""
        storage = InMemoryRateLimitStorage()
        window_start = datetime.now()
        count = storage.get_count("user_123", "chat", window_start)
        assert count == 0
    
    def test_increment_and_get_count(self):
        """Test incrementing and getting count."""
        storage = InMemoryRateLimitStorage()
        window_start = datetime.now()
        
        storage.increment("user_123", "chat", window_start)
        count = storage.get_count("user_123", "chat", window_start)
        assert count == 1
        
        storage.increment("user_123", "chat", window_start)
        count = storage.get_count("user_123", "chat", window_start)
        assert count == 2
    
    def test_cleanup_old_entries(self):
        """Test cleanup removes old entries."""
        storage = InMemoryRateLimitStorage()
        old_time = datetime.now() - timedelta(seconds=RATE_LIMIT_WINDOW + 10)
        
        # Add old entry
        storage.store["user_123:chat"].append(old_time)
        
        # Get count should clean up old entries
        window_start = datetime.now()
        count = storage.get_count("user_123", "chat", window_start)
        assert count == 0
    
    def test_separate_users(self):
        """Test that different users have separate counts."""
        storage = InMemoryRateLimitStorage()
        window_start = datetime.now()
        
        storage.increment("user_123", "chat", window_start)
        storage.increment("user_456", "chat", window_start)
        
        assert storage.get_count("user_123", "chat", window_start) == 1
        assert storage.get_count("user_456", "chat", window_start) == 1
    
    def test_separate_endpoints(self):
        """Test that different endpoints have separate counts."""
        storage = InMemoryRateLimitStorage()
        window_start = datetime.now()
        
        storage.increment("user_123", "chat", window_start)
        storage.increment("user_123", "compute_features", window_start)
        
        assert storage.get_count("user_123", "chat", window_start) == 1
        assert storage.get_count("user_123", "compute_features", window_start) == 1


class TestCheckRateLimit:
    """Tests for check_rate_limit function."""
    
    @patch('src.api.rate_limit.rate_limit_storage')
    def test_rate_limit_allowed(self, mock_storage):
        """Test rate limit check when under limit."""
        mock_storage.get_count.return_value = 5  # Under limit
        mock_storage.increment.return_value = None
        
        is_allowed, retry_after = check_rate_limit("user_123", "chat")
        
        assert is_allowed == True
        assert retry_after is None
        mock_storage.get_count.assert_called_once()
        mock_storage.increment.assert_called_once()
    
    @patch('src.api.rate_limit.rate_limit_storage')
    def test_rate_limit_exceeded(self, mock_storage):
        """Test rate limit check when limit exceeded."""
        # Set limit to 10
        limit = RATE_LIMITS["chat"]["limit"]
        mock_storage.get_count.return_value = limit  # At limit
        
        is_allowed, retry_after = check_rate_limit("user_123", "chat")
        
        assert is_allowed == False
        assert retry_after is not None
        assert retry_after > 0
        mock_storage.increment.assert_not_called()  # Should not increment when limit exceeded
    
    @patch('src.api.rate_limit.rate_limit_storage')
    def test_different_endpoints_different_limits(self, mock_storage):
        """Test that different endpoints have different limits."""
        # Chat limit
        chat_limit = RATE_LIMITS["chat"]["limit"]
        mock_storage.get_count.return_value = chat_limit - 1
        
        is_allowed, _ = check_rate_limit("user_123", "chat")
        assert is_allowed == True
        
        # Compute features limit
        compute_limit = RATE_LIMITS["compute_features"]["limit"]
        mock_storage.get_count.return_value = compute_limit - 1
        
        is_allowed, _ = check_rate_limit("user_123", "compute_features")
        assert is_allowed == True


class TestRateLimitConfiguration:
    """Tests for rate limit configuration."""
    
    def test_rate_limit_config_exists(self):
        """Test that rate limit config exists for all endpoints."""
        assert "chat" in RATE_LIMITS
        assert "compute_features" in RATE_LIMITS
        assert "override" in RATE_LIMITS
        assert "flag" in RATE_LIMITS
    
    def test_rate_limit_config_structure(self):
        """Test that rate limit config has required fields."""
        for endpoint, config in RATE_LIMITS.items():
            assert "limit" in config
            assert "window" in config
            assert isinstance(config["limit"], int)
            assert isinstance(config["window"], int)
            assert config["limit"] > 0
            assert config["window"] > 0







