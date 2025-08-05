"""
CORS Middleware for FastAPI application.

Handles Cross-Origin Resource Sharing configuration based on environment variables.
"""

from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
from structlog import get_logger

from .constants import CORS_HEADERS, CORS_METHODS, DEFAULT_CORS_ORIGINS

logger = get_logger(__name__)


def get_cors_origins(cors_origins_config: str = "") -> List[str]:
    """
    Get CORS origins from configuration or use defaults.

    Args:
        cors_origins_config: Comma-separated list of origins from settings
        Example: "https://app.company.com,https://staging.company.com"

    Returns:
        List of allowed CORS origins
    """
    if cors_origins_config:
        # Parse comma-separated origins and strip whitespace
        origins = [
            origin.strip()
            for origin in cors_origins_config.split(",")
            if origin.strip()
        ]
        logger.info("Using CORS origins from configuration", origins=origins)
        return origins
    else:
        logger.info("Using default CORS origins", origins=DEFAULT_CORS_ORIGINS)
        return DEFAULT_CORS_ORIGINS


def setup_cors_middleware(app: FastAPI, cors_origins_config: str = "") -> None:
    """
    Set up CORS middleware for the FastAPI application.

    Args:
        app: FastAPI application instance
        cors_origins_config: CORS origins configuration from settings
    """
    origins = get_cors_origins(cors_origins_config)

    app.add_middleware(
        FastAPICORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,  # Allow cookies and authorization headers
        allow_methods=CORS_METHODS,
        allow_headers=CORS_HEADERS,
        expose_headers=[
            "X-Correlation-ID",
            "X-Request-ID",
            "X-Response-Time",
            "X-Total-Count",  # For pagination
        ],
    )

    logger.info(
        "CORS middleware configured",
        origins=origins,
        methods=CORS_METHODS,
        allow_credentials=True,
    )


# For backward compatibility, export the setup function as CORSMiddleware
def CORSMiddleware(app: FastAPI, cors_origins_config: str = "") -> None:
    """Backward compatibility wrapper for setup_cors_middleware"""
    setup_cors_middleware(app, cors_origins_config)
