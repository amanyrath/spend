"""Authentication infrastructure for SpendSense API.

This module provides Firebase-based authentication with role-based access control
for operator and consumer roles.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth as firebase_auth

from src.api.exceptions import UnauthorizedError, ForbiddenError
from src.utils.logging import get_logger

logger = get_logger("auth")

# Security scheme
security = HTTPBearer()


class User:
    """User model for authentication."""
    
    def __init__(self, user_id: str, role: str, email: Optional[str] = None):
        self.user_id = user_id
        self.role = role  # 'operator' or 'consumer'
        self.email = email
    
    def is_operator(self) -> bool:
        """Check if user is an operator."""
        return self.role == "operator"
    
    def is_consumer(self) -> bool:
        """Check if user is a consumer."""
        return self.role == "consumer"


def verify_firebase_token(token: str) -> Dict[str, Any]:
    """Verify Firebase ID token and return decoded claims.
    
    Args:
        token: Firebase ID token string
        
    Returns:
        Decoded token payload with user information
        
    Raises:
        UnauthorizedError: If token is invalid or expired
    """
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except firebase_auth.ExpiredIdTokenError:
        raise UnauthorizedError("Token has expired")
    except firebase_auth.RevokedIdTokenError:
        raise UnauthorizedError("Token has been revoked")
    except firebase_auth.InvalidIdTokenError as e:
        raise UnauthorizedError(f"Invalid Firebase token: {str(e)}")
    except Exception as e:
        logger.error(f"Firebase token verification error: {str(e)}")
        raise UnauthorizedError(f"Authentication failed: {str(e)}")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> User:
    """Get current authenticated user from Firebase token.
    
    Args:
        credentials: HTTP authorization credentials from request header
        
    Returns:
        User object
        
    Raises:
        UnauthorizedError: If token is missing or invalid
    """
    if not credentials:
        raise UnauthorizedError("Authentication required")
    
    token = credentials.credentials
    decoded = verify_firebase_token(token)
    
    user_id = decoded.get("uid")
    email = decoded.get("email")
    
    # Get role from custom claims or default to consumer
    role = decoded.get("role", "consumer")
    
    if not user_id:
        raise UnauthorizedError("Invalid token: missing user ID")
    
    return User(user_id=user_id, role=role, email=email)


def require_operator(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require operator role.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object (guaranteed to be operator)
        
    Raises:
        ForbiddenError: If user is not an operator
    """
    if not current_user.is_operator():
        raise ForbiddenError("Operator role required")
    return current_user


def require_consumer(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require consumer role.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object (guaranteed to be consumer)
        
    Raises:
        ForbiddenError: If user is not a consumer
    """
    if not current_user.is_consumer():
        raise ForbiddenError("Consumer role required")
    return current_user


def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """Optional authentication - returns User if authenticated, None otherwise.
    
    Args:
        credentials: HTTP authorization credentials (optional)
        
    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        decoded = verify_firebase_token(token)
        
        user_id = decoded.get("uid")
        role = decoded.get("role", "consumer")
        email = decoded.get("email")
        
        if not user_id:
            return None
        
        return User(user_id=user_id, role=role, email=email)
    except Exception:
        return None


# Legacy function for backward compatibility - now returns Firebase UID
def create_access_token(user_id: str, role: str, email: Optional[str] = None) -> str:
    """Legacy function for creating access tokens.
    
    Note: With Firebase Auth, tokens are created by Firebase SDK on the client side.
    This function is kept for backward compatibility but should not be used for new code.
    
    Args:
        user_id: User identifier
        role: User role ('operator' or 'consumer')
        email: User email (optional)
        
    Returns:
        User ID (Firebase tokens are created client-side)
    """
    logger.warning("create_access_token called but Firebase Auth handles token creation client-side")
    return user_id



