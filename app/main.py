import argparse
import os

import uvicorn
from fastapi import FastAPI
from pydantic import ValidationError
from pydantic_core import ValidationError as PydanticCoreValidationError
from structlog import get_logger

from app.api import route_management, tags
from app.api.exception_handlers import (
    pydantic_core_validation_exception_handler,
    validation_exception_handler,
)
from app.core.config import settings
from app.core.logger import struct_logger
from app.utils.middleware import (
    setup_cors_middleware,
    setup_request_logging_middleware,
    setup_response_time_middleware,
    setup_security_headers_middleware,
)

struct_logger.setup_logging()
logger = get_logger()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI()

    # Setup middleware in order (important: order matters for middleware stack)
    # 1. Response time tracking (outermost - measures total time)
    setup_response_time_middleware(
        app, slow_threshold_ms=settings.slow_request_threshold_ms
    )

    # 2. Request logging with correlation IDs
    setup_request_logging_middleware(app)

    # 3. Security headers
    if not settings.is_local_env:
        setup_security_headers_middleware(app, add_csp=True)

    # 4. CORS (should be after security headers)
    setup_cors_middleware(app, cors_origins_config=settings.cors_origins)

    logger.info("All middleware configured successfully")

    # Add global exception handlers for Pydantic validation errors
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(
        PydanticCoreValidationError, pydantic_core_validation_exception_handler
    )

    # Initialize routes based on API_MODE environment variable or default to ALL
    api_mode = os.getenv("API_MODE", "ALL")
    logger.info(f"Initializing routes for API mode: {api_mode}")
    route_management.initialize_api_routes(app, api_mode)

    return app


# Create the app instance for direct imports
app = create_app()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--api-mode", default="ALL", choices=tags.ApiType.values())
    args = parser.parse_args()
    # Initialize routers based on the selected visibility
    route_management.initialize_api_routes(app, args.api_mode)

    uvicorn.run(
        app, host="0.0.0.0", port=settings.port, log_level=settings.log_level.lower()
    )

elif __name__ == "main":
    logger.info("Module imported - routes already initialized in create_app()")
    pass
