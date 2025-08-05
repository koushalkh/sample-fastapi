"""
Security Headers Middleware for FastAPI application.

Adds essential security headers to all responses for production security.
"""

import os
from typing import Any, Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from structlog import get_logger

from .constants import CSP_POLICY, HTTPS_SECURITY_HEADERS, SECURITY_HEADERS

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Adds standard security headers and conditionally adds HTTPS-specific headers
    based on the environment and request scheme.
    """

    def __init__(self, app: Any, add_csp: bool = True, add_hsts: Optional[bool] = None):
        """
        Initialize security headers middleware.

        Args:
            app: FastAPI application instance
            add_csp: Whether to add Content Security Policy header
            add_hsts: Whether to add HTTPS Strict Transport Security header.
                     If None, will be determined based on environment and request scheme.
        """
        super().__init__(app)
        self.add_csp = add_csp
        self.add_hsts = add_hsts
        self.environment = os.getenv("ENVIRONMENT", "development").lower()

        logger.info(
            "Security headers middleware initialized",
            add_csp=add_csp,
            add_hsts=add_hsts,
            environment=self.environment,
        )

    async def dispatch(
        self, request: Request, call_next: Callable[..., Any]
    ) -> Response:
        """
        Add security headers to the response.

        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler

        Returns:
            Response with security headers added
        """
        # Call the next middleware or route handler
        response = await call_next(request)

        # Add standard security headers
        for header_name, header_value in SECURITY_HEADERS.items():
            response.headers[header_name] = header_value

        # Add Content Security Policy if enabled
        if self.add_csp:
            response.headers["Content-Security-Policy"] = CSP_POLICY

        # Add HTTPS security headers conditionally
        should_add_hsts = self._should_add_hsts(request)
        if should_add_hsts:
            for header_name, header_value in HTTPS_SECURITY_HEADERS.items():
                response.headers[header_name] = header_value

        # Add server header (optional, for branding)
        response.headers["Server"] = "ADR-Service"

        return response

    def _should_add_hsts(self, request: Request) -> bool:
        """
        Determine whether to add HTTPS Strict Transport Security header.

        Args:
            request: FastAPI request object

        Returns:
            True if HSTS header should be added
        """
        # If explicitly set, use that value
        if self.add_hsts is not None:
            return self.add_hsts

        # In production environments, add HSTS for HTTPS requests
        if self.environment in ("production", "prod", "staging"):
            return request.url.scheme == "https"

        # In development, don't add HSTS by default
        return False


def setup_security_headers_middleware(app: Any, **kwargs: Any) -> None:
    """
    Set up security headers middleware for the FastAPI application.

    Args:
        app: FastAPI application instance
        **kwargs: Additional arguments to pass to SecurityHeadersMiddleware
    """
    app.add_middleware(SecurityHeadersMiddleware, **kwargs)
    logger.info("Security headers middleware configured")
