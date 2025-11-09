"""Tests for API validation utilities."""

import pytest
from src.api.validators import (
    validate_user_id,
    validate_time_window,
    validate_recommendation_id,
    validate_account_id,
    validate_limit,
    validate_offset,
    sanitize_string
)


class TestValidateUserID:
    """Tests for user_id validation."""
    
    def test_valid_user_id(self):
        """Test valid user_id formats."""
        assert validate_user_id("user_001")[0] == True
        assert validate_user_id("user_123")[0] == True
        assert validate_user_id("user_999")[0] == True
    
    def test_invalid_user_id_empty(self):
        """Test empty user_id."""
        is_valid, error_msg = validate_user_id("")
        assert is_valid == False
        assert "required" in error_msg.lower()
    
    def test_invalid_user_id_format(self):
        """Test invalid user_id formats."""
        invalid_ids = [
            "user_12",      # Too short
            "user_1234",    # Too long
            "user_abc",     # Non-numeric
            "usr_123",      # Wrong prefix
            "123",          # No prefix
            "user123",      # Missing underscore
        ]
        
        for invalid_id in invalid_ids:
            is_valid, error_msg = validate_user_id(invalid_id)
            assert is_valid == False, f"Should reject: {invalid_id}"
            assert "format" in error_msg.lower() or "required" in error_msg.lower()
    
    def test_invalid_user_id_type(self):
        """Test non-string user_id."""
        is_valid, error_msg = validate_user_id(123)
        assert is_valid == False
        assert "string" in error_msg.lower()


class TestValidateTimeWindow:
    """Tests for time_window validation."""
    
    def test_valid_time_windows(self):
        """Test valid time_window values."""
        assert validate_time_window("30d")[0] == True
        assert validate_time_window("180d")[0] == True
        assert validate_time_window("30D")[0] == True  # Case insensitive
        assert validate_time_window("180D")[0] == True
    
    def test_default_time_window(self):
        """Test None time_window defaults to 30d."""
        is_valid, error_msg, normalized = validate_time_window(None)
        assert is_valid == True
        assert normalized == "30d"
    
    def test_invalid_time_window(self):
        """Test invalid time_window values."""
        invalid_windows = ["7d", "90d", "365d", "30days", "30", ""]
        
        for invalid_window in invalid_windows:
            is_valid, error_msg, normalized = validate_time_window(invalid_window)
            assert is_valid == False, f"Should reject: {invalid_window}"
            assert "invalid" in error_msg.lower()
    
    def test_invalid_time_window_type(self):
        """Test non-string time_window."""
        is_valid, error_msg, normalized = validate_time_window(30)
        assert is_valid == False


class TestValidateRecommendationID:
    """Tests for recommendation_id validation."""
    
    def test_valid_recommendation_id(self):
        """Test valid recommendation_id formats."""
        assert validate_recommendation_id("rec_123456789abc")[0] == True
        assert validate_recommendation_id("rec_abcdef123456")[0] == True
    
    def test_invalid_recommendation_id_format(self):
        """Test invalid recommendation_id formats."""
        invalid_ids = [
            "rec_123",              # Too short
            "rec_123456789abcdef",  # Too long
            "rec_123456789AB",      # Invalid chars
            "rec123456789abc",      # Missing underscore
            "123456789abc",         # Missing prefix
        ]
        
        for invalid_id in invalid_ids:
            is_valid, error_msg = validate_recommendation_id(invalid_id)
            assert is_valid == False, f"Should reject: {invalid_id}"


class TestValidateLimit:
    """Tests for pagination limit validation."""
    
    def test_valid_limits(self):
        """Test valid limit values."""
        assert validate_limit(1)[0] == True
        assert validate_limit(50)[0] == True
        assert validate_limit(100)[0] == True
    
    def test_default_limit(self):
        """Test None limit defaults."""
        is_valid, error_msg, normalized = validate_limit(None, default=50)
        assert is_valid == True
        assert normalized == 50
    
    def test_invalid_limits(self):
        """Test invalid limit values."""
        # Too small
        is_valid, error_msg, normalized = validate_limit(0)
        assert is_valid == False
        
        # Too large
        is_valid, error_msg, normalized = validate_limit(101, max_limit=100)
        assert is_valid == False
        
        # Wrong type
        is_valid, error_msg, normalized = validate_limit("50")
        assert is_valid == False


class TestValidateOffset:
    """Tests for pagination offset validation."""
    
    def test_valid_offsets(self):
        """Test valid offset values."""
        assert validate_offset(0)[0] == True
        assert validate_offset(50)[0] == True
        assert validate_offset(100)[0] == True
    
    def test_default_offset(self):
        """Test None offset defaults."""
        is_valid, error_msg, normalized = validate_offset(None, default=0)
        assert is_valid == True
        assert normalized == 0
    
    def test_invalid_offsets(self):
        """Test invalid offset values."""
        # Negative
        is_valid, error_msg, normalized = validate_offset(-1)
        assert is_valid == False
        
        # Wrong type
        is_valid, error_msg, normalized = validate_offset("0")
        assert is_valid == False


class TestSanitizeString:
    """Tests for string sanitization."""
    
    def test_basic_sanitization(self):
        """Test basic string sanitization."""
        assert sanitize_string("  test  ") == "test"
        assert sanitize_string("test") == "test"
    
    def test_max_length(self):
        """Test max length enforcement."""
        long_string = "a" * 200
        sanitized = sanitize_string(long_string, max_length=100)
        assert len(sanitized) == 100
    
    def test_non_string_input(self):
        """Test non-string input."""
        assert sanitize_string(123) == ""
        assert sanitize_string(None) == ""







