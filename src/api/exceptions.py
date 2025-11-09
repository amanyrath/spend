"""Custom exception classes for SpendSense API.

This module defines custom exception classes for consistent error handling
across the API. All exceptions inherit from SpendSenseException which provides
a base error code and message structure.
"""

from typing import Optional


class SpendSenseException(Exception):
    """Base exception class for SpendSense errors.
    
    All custom exceptions should inherit from this class.
    Provides error code and message structure.
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        """Initialize exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)


class UserNotFoundError(SpendSenseException):
    """Exception raised when a user is not found."""
    
    def __init__(self, user_id: str):
        super().__init__(
            message=f"User not found: {user_id}",
            error_code="USER_NOT_FOUND"
        )
        self.user_id = user_id


class InvalidInputError(SpendSenseException):
    """Exception raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        error_code = f"INVALID_INPUT_{field.upper()}" if field else "INVALID_INPUT"
        super().__init__(message=message, error_code=error_code)
        self.field = field


class UnauthorizedError(SpendSenseException):
    """Exception raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message=message, error_code="UNAUTHORIZED")


class ForbiddenError(SpendSenseException):
    """Exception raised when user lacks required permissions."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, error_code="FORBIDDEN")


class RateLimitError(SpendSenseException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(message=message, error_code="RATE_LIMIT_EXCEEDED")
        self.retry_after = retry_after


class RecommendationNotFoundError(SpendSenseException):
    """Exception raised when a recommendation is not found."""
    
    def __init__(self, recommendation_id: str):
        super().__init__(
            message=f"Recommendation not found: {recommendation_id}",
            error_code="RECOMMENDATION_NOT_FOUND"
        )
        self.recommendation_id = recommendation_id


class ConsentNotGrantedError(SpendSenseException):
    """Exception raised when user consent is required but not granted."""
    
    def __init__(self, message: str = "User consent required"):
        super().__init__(message=message, error_code="CONSENT_NOT_GRANTED")







