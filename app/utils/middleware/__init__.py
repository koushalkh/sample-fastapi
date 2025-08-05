"""
Middleware module for FastAPI application.

This module contains all middleware components for production-ready features:
- CORS configuration
- Security headers
- Request logging and correlation
- Response time tracking
"""

from .cors import setup_cors_middleware
from .logging import RequestLoggingMiddleware, setup_request_logging_middleware
from .monitoring import ResponseTimeMiddleware, setup_response_time_middleware
from .security import SecurityHeadersMiddleware, setup_security_headers_middleware

__all__ = [
    "setup_cors_middleware",
    "SecurityHeadersMiddleware",
    "setup_security_headers_middleware",
    "RequestLoggingMiddleware",
    "setup_request_logging_middleware",
    "ResponseTimeMiddleware",
    "setup_response_time_middleware",
]
