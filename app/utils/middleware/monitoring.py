"""
Response Time Monitoring Middleware for FastAPI application.

Tracks request processing time and adds response time headers.
"""

import time
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from structlog import get_logger

from .constants import RESPONSE_TIME_HEADER

logger = get_logger(__name__)


class ResponseTimeMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track and report request processing time.

    Features:
    - Measures high-precision request processing time
    - Adds X-Response-Time header to all responses
    - Logs slow requests for monitoring
    """

    def __init__(self, app: Any, slow_threshold_ms: float = 1000.0):
        """
        Initialize response time middleware.

        Args:
            app: FastAPI application instance
            slow_threshold_ms: Threshold in milliseconds to log slow requests
        """
        super().__init__(app)
        self.slow_threshold_ms = slow_threshold_ms

        logger.info(
            "Response time middleware initialized", slow_threshold_ms=slow_threshold_ms
        )

    async def dispatch(
        self, request: Request, call_next: Callable[..., Any]
    ) -> Response:
        """
        Measure request processing time and add response time header.

        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler

        Returns:
            Response with response time header added
        """
        # Record start time with high precision
        start_time = time.perf_counter()

        # Process request
        response = await call_next(request)

        # Calculate processing time
        end_time = time.perf_counter()
        processing_time_ms = (end_time - start_time) * 1000

        # Add response time header (rounded to 3 decimal places)
        response.headers[RESPONSE_TIME_HEADER] = f"{processing_time_ms:.3f}ms"

        # Log slow requests
        if processing_time_ms > self.slow_threshold_ms:
            self._log_slow_request(request, processing_time_ms)

        return response

    def _log_slow_request(self, request: Request, processing_time_ms: float) -> None:
        """
        Log details of slow requests for monitoring.

        Args:
            request: FastAPI request object
            processing_time_ms: Request processing time in milliseconds
        """
        # Get correlation ID if available from request state
        correlation_id = getattr(request.state, "correlation_id", None)
        request_id = getattr(request.state, "request_id", None)

        logger.warning(
            "Slow request detected",
            correlation_id=correlation_id,
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            processing_time_ms=round(processing_time_ms, 3),
            threshold_ms=self.slow_threshold_ms,
            query_params=str(request.query_params) if request.query_params else None,
        )


def setup_response_time_middleware(app: Any, **kwargs: Any) -> None:
    """
    Set up response time middleware for the FastAPI application.

    Args:
        app: FastAPI application instance
        **kwargs: Additional arguments to pass to ResponseTimeMiddleware
    """
    app.add_middleware(ResponseTimeMiddleware, **kwargs)
    logger.info("Response time middleware configured")
