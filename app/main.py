from fastapi import FastAPI
from app.api import route_management
import uvicorn
from core.config import settings
import argparse
from app.api import tags
from app.core.logger import struct_logger
from structlog import get_logger


struct_logger.setup_logging()
logger = get_logger()

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI()
    # TODO: Add Middlewares
    return app

# Create the app instance for direct imports
app = create_app()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--api-mode", default="ALL", choices=tags.ApiType.values())
    args = parser.parse_args()
    # Initialize routers based on the selected visibility
    route_management.initialize_api_routes(app, args.api_mode)

    uvicorn.run(app, host="0.0.0.0", port=settings.port, log_level=settings.log_level.lower())

elif __name__ == "main":
    logger.info("Initializing ALL routes")
    route_management.initialize_api_routes(app, tags.ApiType.ALL.value)