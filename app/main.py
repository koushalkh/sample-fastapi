import argparse
import os

import uvicorn
from fastapi import FastAPI
from structlog import get_logger

from app.api import route_management, tags
from app.core.logger import struct_logger
from app.core.config import settings

struct_logger.setup_logging()
logger = get_logger()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI()
    # TODO: Add Middlewares

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
