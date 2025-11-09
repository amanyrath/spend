"""Tests for authentication functionality."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
import jwt
import os

from src.api.auth import (
    create_access_token,
    decode_token,
    User,
    JWT_SECRET,
    JWT_ALGORITHM
)


class TestUser:
    """Tests for User class."""
    
    def test_user_creation(self):
        """Test user creation."""
        user = User("user_123", "consumer")
        assert user.user_id == "user_123"
        assert user.role == "consumer"
        assert user.email is None
    
    def test_user_with_email(self):
        """Test user creation with email."""
        user = User("user_123", "operator", email="test@example.com")
        assert user.user_id == "user_123"
        assert user.role == "operator"
        assert user.email == "test@example.com"
    
    def test_is_operator(self):
        """Test is_operator method."""
        operator = User("op_123", "operator")
        consumer = User("user_123", "consumer")
        
        assert operator.is_operator() == True
        assert consumer.is_operator() == False
    
    def test_is_consumer(self):
        """Test is_consumer method."""
        operator = User("op_123", "operator")
        consumer = User("user_123", "consumer")
        
        assert operator.is_consumer() == False
        assert consumer.is_consumer() == True


class TestCreateAccessToken:
    """Tests for create_access_token function."""
    
    def test_token_creation(self):
        """Test basic token creation."""
        token = create_access_token("user_123", "consumer")
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_token_contains_user_id(self):
        """Test token contains user_id."""
        token = create_access_token("user_123", "consumer")
        payload = decode_token(token)
        assert payload["sub"] == "user_123"
    
    def test_token_contains_role(self):
        """Test token contains role."""
        token = create_access_token("user_123", "operator")
        payload = decode_token(token)
        assert payload["role"] == "operator"
    
    def test_token_contains_email(self):
        """Test token contains email when provided."""
        token = create_access_token("user_123", "consumer", email="test@example.com")
        payload = decode_token(token)
        assert payload["email"] == "test@example.com"
    
    def test_token_has_expiration(self):
        """Test token has expiration claim."""
        token = create_access_token("user_123", "consumer")
        payload = decode_token(token)
        assert "exp" in payload
        assert isinstance(payload["exp"], (int, float))
    
    def test_token_has_issued_at(self):
        """Test token has issued_at claim."""
        token = create_access_token("user_123", "consumer")
        payload = decode_token(token)
        assert "iat" in payload


class TestDecodeToken:
    """Tests for decode_token function."""
    
    def test_decode_valid_token(self):
        """Test decoding valid token."""
        token = create_access_token("user_123", "consumer")
        payload = decode_token(token)
        
        assert payload["sub"] == "user_123"
        assert payload["role"] == "consumer"
    
    def test_decode_expired_token(self):
        """Test decoding expired token."""
        # Create expired token manually
        expiration = datetime.utcnow() - timedelta(hours=1)
        payload = {
            "sub": "user_123",
            "role": "consumer",
            "exp": expiration,
            "iat": datetime.utcnow() - timedelta(hours=2)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        with pytest.raises(Exception):  # Should raise UnauthorizedError
            decode_token(token)
    
    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        invalid_tokens = [
            "invalid.token.here",
            "not.a.valid.token",
            "",
            "Bearer invalid",
        ]
        
        for invalid_token in invalid_tokens:
            with pytest.raises(Exception):  # Should raise UnauthorizedError
                decode_token(invalid_token)
    
    def test_decode_token_wrong_secret(self):
        """Test decoding token with wrong secret."""
        token = create_access_token("user_123", "consumer")
        
        # Try to decode with wrong secret
        with pytest.raises(Exception):  # Should raise UnauthorizedError
            jwt.decode(token, "wrong_secret", algorithms=[JWT_ALGORITHM])







