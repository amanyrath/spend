"""Tests for custom exception classes."""

import pytest
from src.api.exceptions import (
    SpendSenseException,
    UserNotFoundError,
    InvalidInputError,
    UnauthorizedError,
    ForbiddenError,
    RateLimitError,
    RecommendationNotFoundError,
    ConsentNotGrantedError
)


class TestSpendSenseException:
    """Tests for base exception class."""
    
    def test_basic_exception(self):
        """Test basic exception creation."""
        exc = SpendSenseException("Test message")
        assert exc.message == "Test message"
        assert exc.error_code == "SpendSenseException"
        assert str(exc) == "Test message"
    
    def test_exception_with_code(self):
        """Test exception with custom error code."""
        exc = SpendSenseException("Test message", "CUSTOM_CODE")
        assert exc.message == "Test message"
        assert exc.error_code == "CUSTOM_CODE"


class TestUserNotFoundError:
    """Tests for UserNotFoundError."""
    
    def test_user_not_found(self):
        """Test UserNotFoundError creation."""
        exc = UserNotFoundError("user_123")
        assert exc.message == "User not found: user_123"
        assert exc.error_code == "USER_NOT_FOUND"
        assert exc.user_id == "user_123"


class TestInvalidInputError:
    """Tests for InvalidInputError."""
    
    def test_invalid_input_without_field(self):
        """Test InvalidInputError without field."""
        exc = InvalidInputError("Invalid input")
        assert exc.message == "Invalid input"
        assert exc.error_code == "INVALID_INPUT"
        assert exc.field is None
    
    def test_invalid_input_with_field(self):
        """Test InvalidInputError with field."""
        exc = InvalidInputError("Invalid user_id", field="user_id")
        assert exc.message == "Invalid user_id"
        assert exc.error_code == "INVALID_INPUT_USER_ID"
        assert exc.field == "user_id"


class TestUnauthorizedError:
    """Tests for UnauthorizedError."""
    
    def test_unauthorized_default_message(self):
        """Test UnauthorizedError with default message."""
        exc = UnauthorizedError()
        assert exc.message == "Authentication required"
        assert exc.error_code == "UNAUTHORIZED"
    
    def test_unauthorized_custom_message(self):
        """Test UnauthorizedError with custom message."""
        exc = UnauthorizedError("Custom auth message")
        assert exc.message == "Custom auth message"
        assert exc.error_code == "UNAUTHORIZED"


class TestForbiddenError:
    """Tests for ForbiddenError."""
    
    def test_forbidden_default_message(self):
        """Test ForbiddenError with default message."""
        exc = ForbiddenError()
        assert exc.message == "Insufficient permissions"
        assert exc.error_code == "FORBIDDEN"


class TestRateLimitError:
    """Tests for RateLimitError."""
    
    def test_rate_limit_default(self):
        """Test RateLimitError with default message."""
        exc = RateLimitError()
        assert exc.message == "Rate limit exceeded"
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.retry_after is None
    
    def test_rate_limit_with_retry(self):
        """Test RateLimitError with retry_after."""
        exc = RateLimitError("Rate limit exceeded", retry_after=60)
        assert exc.message == "Rate limit exceeded"
        assert exc.retry_after == 60


class TestRecommendationNotFoundError:
    """Tests for RecommendationNotFoundError."""
    
    def test_recommendation_not_found(self):
        """Test RecommendationNotFoundError creation."""
        exc = RecommendationNotFoundError("rec_123456789abc")
        assert exc.message == "Recommendation not found: rec_123456789abc"
        assert exc.error_code == "RECOMMENDATION_NOT_FOUND"
        assert exc.recommendation_id == "rec_123456789abc"


class TestConsentNotGrantedError:
    """Tests for ConsentNotGrantedError."""
    
    def test_consent_not_granted(self):
        """Test ConsentNotGrantedError creation."""
        exc = ConsentNotGrantedError()
        assert exc.message == "User consent required"
        assert exc.error_code == "CONSENT_NOT_GRANTED"







