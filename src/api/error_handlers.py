"""Error handlers for SpendSense API.

This module provides standardized error handling for FastAPI endpoints,
converting exceptions to appropriate HTTP responses with consistent formats.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from src.api.exceptions import SpendSenseException, UserNotFoundError, InvalidInputError, UnauthorizedError, ForbiddenError, RateLimitError


def get_request_id(request: Request) -> str:
    """Extract request ID from request headers or generate one.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Request ID string
    """
    # Check if request ID was set by middleware
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        return request_id
    
    # Fallback: use correlation ID from headers if available
    return request.headers.get("X-Request-ID", "unknown")


def create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    request_id: str,
    details: dict = None
) -> JSONResponse:
    """Create standardized error response.
    
    Args:
        status_code: HTTP status code
        error_code: Machine-readable error code
        message: Human-readable error message
        request_id: Request ID for tracing
        details: Additional error details
        
    Returns:
        JSONResponse with error structure
    """
    error_response = {
        "error": {
            "code": error_code,
            "message": message,
            "request_id": request_id
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


async def spendsense_exception_handler(request: Request, exc: SpendSenseException) -> JSONResponse:
    """Handle SpendSense custom exceptions.
    
    Args:
        request: FastAPI request object
        exc: SpendSenseException instance
        
    Returns:
        JSONResponse with error details
    """
    # Map exception types to HTTP status codes
    status_map = {
        UserNotFoundError: status.HTTP_404_NOT_FOUND,
        InvalidInputError: status.HTTP_400_BAD_REQUEST,
        UnauthorizedError: status.HTTP_401_UNAUTHORIZED,
        ForbiddenError: status.HTTP_403_FORBIDDEN,
        RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
    }
    
    status_code = status_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    request_id = get_request_id(request)
    
    return create_error_response(
        status_code=status_code,
        error_code=exc.error_code,
        message=exc.message,
        request_id=request_id
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors.
    
    Args:
        request: FastAPI request object
        exc: RequestValidationError instance
        
    Returns:
        JSONResponse with validation error details
    """
    request_id = get_request_id(request)
    
    # Extract validation errors
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        message="Input validation failed",
        request_id=request_id,
        details={"validation_errors": errors}
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions.
    
    Args:
        request: FastAPI request object
        exc: Exception instance
        
    Returns:
        JSONResponse with generic error details
    """
    request_id = get_request_id(request)
    
    # Log the exception (will be done by logging middleware if configured)
    import logging
    logger = logging.getLogger("spendsense.api")
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        request_id=request_id
    )







