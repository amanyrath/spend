"""Tests for error handlers."""

import pytest
from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from unittest.mock import MagicMock, PropertyMock, patch

from src.api.error_handlers import (
    get_request_id,
    create_error_response,
    spendsense_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from src.api.exceptions import (
    UserNotFoundError,
    InvalidInputError,
    RateLimitError
)


class TestGetRequestID:
    """Tests for get_request_id function."""
    
    def test_get_request_id_from_state(self):
        """Test getting request ID from request state."""
        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-id"
        
        request_id = get_request_id(request)
        assert request_id == "test-request-id"
    
    def test_get_request_id_from_header(self):
        """Test getting request ID from header."""
        request = MagicMock(spec=Request)
        request.state.request_id = None
        request.headers.get.return_value = "header-request-id"
        
        request_id = get_request_id(request)
        assert request_id == "header-request-id"
    
    def test_get_request_id_fallback(self):
        """Test fallback when no request ID available."""
        request = MagicMock()
        request.state = MagicMock()
        # Set request_id to None explicitly
        request.state.request_id = None
        # Mock headers.get to return None (key doesn't exist), which should use default "unknown"
        request.headers.get = MagicMock(return_value=None)
        # But we need to make it return "unknown" when called with default
        def mock_get(key, default=None):
            return default if default is not None else None
        request.headers.get = mock_get
        
        request_id = get_request_id(request)
        assert request_id == "unknown"


class TestCreateErrorResponse:
    """Tests for create_error_response function."""
    
    def test_create_error_response(self):
        """Test creating error response."""
        response = create_error_response(
            status_code=404,
            error_code="USER_NOT_FOUND",
            message="User not found",
            request_id="test-123"
        )
        
        assert response.status_code == 404
        content = response.body.decode()
        assert "USER_NOT_FOUND" in content
        assert "User not found" in content
        assert "test-123" in content
    
    def test_create_error_response_with_details(self):
        """Test creating error response with details."""
        details = {"field": "user_id", "reason": "Invalid format"}
        response = create_error_response(
            status_code=400,
            error_code="VALIDATION_ERROR",
            message="Validation failed",
            request_id="test-123",
            details=details
        )
        
        content = response.body.decode()
        assert "VALIDATION_ERROR" in content
        assert "details" in content


class TestSpendSenseExceptionHandler:
    """Tests for SpendSense exception handler."""
    
    @pytest.mark.asyncio
    async def test_handle_user_not_found(self):
        """Test handling UserNotFoundError."""
        request = MagicMock(spec=Request)
        type(request.state).request_id = PropertyMock(return_value="test-123")
        request.headers.get.return_value = None
        
        exc = UserNotFoundError("user_123")
        response = await spendsense_exception_handler(request, exc)
        
        assert response.status_code == 404
        content = response.body.decode()
        assert "USER_NOT_FOUND" in content
        assert "User not found" in content
    
    @pytest.mark.asyncio
    async def test_handle_invalid_input(self):
        """Test handling InvalidInputError."""
        request = MagicMock(spec=Request)
        type(request.state).request_id = PropertyMock(return_value="test-123")
        request.headers.get.return_value = None
        
        exc = InvalidInputError("Invalid user_id format", field="user_id")
        response = await spendsense_exception_handler(request, exc)
        
        assert response.status_code == 400
        content = response.body.decode()
        assert "INVALID_INPUT_USER_ID" in content
    
    @pytest.mark.asyncio
    async def test_handle_rate_limit(self):
        """Test handling RateLimitError."""
        request = MagicMock(spec=Request)
        type(request.state).request_id = PropertyMock(return_value="test-123")
        request.headers.get.return_value = None
        
        exc = RateLimitError("Rate limit exceeded", retry_after=60)
        response = await spendsense_exception_handler(request, exc)
        
        assert response.status_code == 429
        content = response.body.decode()
        assert "RATE_LIMIT_EXCEEDED" in content


class TestValidationExceptionHandler:
    """Tests for validation exception handler."""
    
    @pytest.mark.asyncio
    async def test_handle_validation_error(self):
        """Test handling RequestValidationError."""
        request = MagicMock(spec=Request)
        type(request.state).request_id = PropertyMock(return_value="test-123")
        request.headers.get.return_value = None
        
        # Create a mock validation error
        errors = [
            {
                "loc": ("body", "user_id"),
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
        exc = RequestValidationError(errors)
        
        response = await validation_exception_handler(request, exc)
        
        assert response.status_code == 422
        content = response.body.decode()
        assert "VALIDATION_ERROR" in content
        assert "validation_errors" in content


class TestGeneralExceptionHandler:
    """Tests for general exception handler."""
    
    @pytest.mark.asyncio
    async def test_handle_general_exception(self):
        """Test handling general exception."""
        request = MagicMock(spec=Request)
        type(request.state).request_id = PropertyMock(return_value="test-123")
        request.headers.get.return_value = None
        
        exc = Exception("Unexpected error")
        
        # Patch logging.getLogger directly since error_handlers imports logging
        with patch('logging.getLogger') as mock_logger:
            mock_log = MagicMock()
            mock_logger.return_value = mock_log
            
            response = await general_exception_handler(request, exc)
            
            assert response.status_code == 500
            content = response.body.decode()
            assert "INTERNAL_SERVER_ERROR" in content
            mock_log.error.assert_called_once()

