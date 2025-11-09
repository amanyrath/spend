"""Input validation utilities for SpendSense API.

This module provides validation functions for API endpoints including
user_id format validation, time_window validation, and query parameter validation.
"""

import re
from typing import Optional, Tuple
from fastapi import HTTPException


# User ID format: user_XXX where XXX is 3 digits
USER_ID_PATTERN = re.compile(r'^user_\d{3}$')

# Valid time windows
VALID_TIME_WINDOWS = {'30d', '180d'}

# Valid recommendation ID format: rec_XXXXXXXXXXXX (12 hex chars)
RECOMMENDATION_ID_PATTERN = re.compile(r'^rec_[a-f0-9]{12}$')

# Valid account ID format: acc_XXX
ACCOUNT_ID_PATTERN = re.compile(r'^acc_[a-z0-9]+$')


def validate_user_id(user_id: str) -> Tuple[bool, str]:
    """Validate user_id format.
    
    Args:
        user_id: User ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not user_id:
        return False, "user_id is required"
    
    if not isinstance(user_id, str):
        return False, "user_id must be a string"
    
    if not USER_ID_PATTERN.match(user_id):
        return False, f"Invalid user_id format: {user_id}. Expected format: user_XXX (where XXX is 3 digits)"
    
    return True, ""


def validate_time_window(time_window: Optional[str]) -> Tuple[bool, str, Optional[str]]:
    """Validate time_window parameter.
    
    Args:
        time_window: Time window string to validate
        
    Returns:
        Tuple of (is_valid, error_message, normalized_time_window)
    """
    if time_window is None:
        return True, "", "30d"  # Default to 30d
    
    if not isinstance(time_window, str):
        return False, "time_window must be a string", None
    
    time_window_lower = time_window.lower()
    
    if time_window_lower not in VALID_TIME_WINDOWS:
        return False, f"Invalid time_window: {time_window}. Must be one of: {', '.join(VALID_TIME_WINDOWS)}", None
    
    return True, "", time_window_lower


def validate_recommendation_id(recommendation_id: str) -> Tuple[bool, str]:
    """Validate recommendation_id format.
    
    Args:
        recommendation_id: Recommendation ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not recommendation_id:
        return False, "recommendation_id is required"
    
    if not isinstance(recommendation_id, str):
        return False, "recommendation_id must be a string"
    
    if not RECOMMENDATION_ID_PATTERN.match(recommendation_id):
        return False, f"Invalid recommendation_id format: {recommendation_id}. Expected format: rec_XXXXXXXXXXXX"
    
    return True, ""


def validate_account_id(account_id: str) -> Tuple[bool, str]:
    """Validate account_id format.
    
    Args:
        account_id: Account ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not account_id:
        return False, "account_id is required"
    
    if not isinstance(account_id, str):
        return False, "account_id must be a string"
    
    if not ACCOUNT_ID_PATTERN.match(account_id):
        return False, f"Invalid account_id format: {account_id}"
    
    return True, ""


def validate_limit(limit: Optional[int], default: int = 50, max_limit: int = 100) -> Tuple[bool, str, int]:
    """Validate pagination limit parameter.
    
    Args:
        limit: Limit value to validate
        default: Default limit if None
        max_limit: Maximum allowed limit
        
    Returns:
        Tuple of (is_valid, error_message, normalized_limit)
    """
    if limit is None:
        return True, "", default
    
    if not isinstance(limit, int):
        return False, "limit must be an integer", 0
    
    if limit < 1:
        return False, "limit must be >= 1", 0
    
    if limit > max_limit:
        return False, f"limit must be <= {max_limit}", 0
    
    return True, "", limit


def validate_offset(offset: Optional[int], default: int = 0) -> Tuple[bool, str, int]:
    """Validate pagination offset parameter.
    
    Args:
        offset: Offset value to validate
        default: Default offset if None
        
    Returns:
        Tuple of (is_valid, error_message, normalized_offset)
    """
    if offset is None:
        return True, "", default
    
    if not isinstance(offset, int):
        return False, "offset must be an integer", 0
    
    if offset < 0:
        return False, "offset must be >= 0", 0
    
    return True, "", offset


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """Sanitize string input (strip whitespace, prevent injection).
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length (None for no limit)
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return ""
    
    # Strip whitespace
    sanitized = value.strip()
    
    # Limit length if specified
    if max_length is not None and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized







