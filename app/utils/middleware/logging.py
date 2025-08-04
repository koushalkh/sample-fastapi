"""
Request Logging Middleware for FastAPI application.

Provides structured logging with correlation IDs and request/response tracking.
"""

import uuid
import time
from typing import Any, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from structlog import get_logger

from .constants import (
    CORRELATION_ID_HEADER,
    REQUEST_ID_HEADER,
    SKIP_LOGGING_PATHS,
    SENSITIVE_HEADERS
)

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add structured logging with correlation IDs for all requests.
    
    Features:
    - Generates unique correlation ID for each request
    - Logs request and response details with structured data
    - Excludes sensitive headers from logs
    - Skips logging for health check and static endpoints
    """
    
    def __init__(self, app: Any, skip_paths: set = None):
        """
        Initialize request logging middleware.
        
        Args:
            app: FastAPI application instance
            skip_paths: Set of paths to skip logging for
        """
        super().__init__(app)
        self.skip_paths = skip_paths or SKIP_LOGGING_PATHS
        
        logger.info("Request logging middleware initialized", 
                   skip_paths=list(self.skip_paths))
    
    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        """
        Log request and response with correlation tracking.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler
            
        Returns:
            Response with correlation headers added
        """
        # Skip logging for specified paths
        if request.url.path in self.skip_paths:
            return await call_next(request)
        
        # Generate correlation ID
        correlation_id = self._get_or_generate_correlation_id(request)
        request_id = str(uuid.uuid4())
        
        # Start timing
        start_time = time.time()
        
        # Add correlation context to the request state
        request.state.correlation_id = correlation_id
        request.state.request_id = request_id
        request.state.start_time = start_time
        
        # Log incoming request
        self._log_request(request, correlation_id, request_id)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Add correlation headers to response
            response.headers[CORRELATION_ID_HEADER] = correlation_id
            response.headers[REQUEST_ID_HEADER] = request_id
            
            # Log response
            self._log_response(request, response, correlation_id, request_id, response_time)
            
            return response
            
        except Exception as exc:
            # Calculate response time for errors
            response_time = time.time() - start_time
            
            # Log exception
            self._log_exception(request, exc, correlation_id, request_id, response_time)
            
            # Re-raise the exception
            raise
    
    def _get_or_generate_correlation_id(self, request: Request) -> str:
        """
        Get correlation ID from request headers or generate a new one.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Correlation ID string
        """
        # Check if correlation ID is provided in headers
        correlation_id = request.headers.get(CORRELATION_ID_HEADER.lower())
        
        if not correlation_id:
            # Generate new correlation ID
            correlation_id = str(uuid.uuid4())
        
        return correlation_id
    
    def _log_request(self, request: Request, correlation_id: str, request_id: str) -> None:
        """
        Log incoming request details.
        
        Args:
            request: FastAPI request object
            correlation_id: Request correlation ID
            request_id: Unique request ID
        """
        # Filter sensitive headers
        headers = self._filter_sensitive_headers(dict(request.headers))
        
        logger.info(
            "Incoming request",
            correlation_id=correlation_id,
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params) if request.query_params else None,
            client_ip=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            headers=headers
        )
    
    def _log_response(
        self, 
        request: Request, 
        response: Response, 
        correlation_id: str, 
        request_id: str, 
        response_time: float
    ) -> None:
        """
        Log response details.
        
        Args:
            request: FastAPI request object
            response: FastAPI response object
            correlation_id: Request correlation ID
            request_id: Unique request ID
            response_time: Request processing time in seconds
        """
        logger.info(
            "Request completed",
            correlation_id=correlation_id,
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            response_time_ms=round(response_time * 1000, 3),
            content_length=response.headers.get("content-length"),
        )
    
    def _log_exception(
        self, 
        request: Request, 
        exception: Exception, 
        correlation_id: str, 
        request_id: str, 
        response_time: float
    ) -> None:
        """
        Log exception details.
        
        Args:
            request: FastAPI request object
            exception: Exception that occurred
            correlation_id: Request correlation ID
            request_id: Unique request ID
            response_time: Request processing time in seconds
        """
        logger.error(
            "Request failed with exception",
            correlation_id=correlation_id,
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            response_time_ms=round(response_time * 1000, 3),
            exc_info=True
        )
    
    def _filter_sensitive_headers(self, headers: dict) -> dict:
        """
        Remove sensitive headers from logging.
        
        Args:
            headers: Dictionary of request headers
            
        Returns:
            Filtered headers dictionary
        """
        return {
            key: value for key, value in headers.items()
            if key.lower() not in SENSITIVE_HEADERS
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address, handling proxies.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Client IP address
        """
        # Check for forwarded headers first (common in load balancer setups)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in case of multiple proxies
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"


def setup_request_logging_middleware(app: Any, **kwargs: Any) -> None:
    """
    Set up request logging middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
        **kwargs: Additional arguments to pass to RequestLoggingMiddleware
    """
    app.add_middleware(RequestLoggingMiddleware, **kwargs)
    logger.info("Request logging middleware configured")
