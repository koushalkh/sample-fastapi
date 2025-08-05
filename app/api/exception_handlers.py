"""
Global exception handlers for API errors.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from pydantic_core import ValidationError as PydanticCoreValidationError
from structlog import get_logger

logger = get_logger(__name__)


async def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors and return 400 instead of 422."""
    logger.warning("Validation error", path=str(request.url), errors=exc.errors())

    # Extract the first error for a cleaner message
    first_error = exc.errors()[0] if exc.errors() else {}
    field = first_error.get("loc", ["unknown"])[
        -1
    ]  # Get the last part of the field path
    msg = first_error.get("msg", "Validation error")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": f"Validation error for field '{field}': {msg}",
            "field": field,
            "type": "validation_error",
        },
    )


async def pydantic_core_validation_exception_handler(
    request: Request, exc: PydanticCoreValidationError
) -> JSONResponse:
    """Handle Pydantic Core validation errors and return 400 instead of 422."""
    logger.warning(
        "Pydantic core validation error", path=str(request.url), error=str(exc)
    )

    # Parse the error message to extract useful information
    error_msg = str(exc)

    # Try to extract field name and message from the error
    if "validation error for" in error_msg:
        parts = error_msg.split("validation error for ")
        if len(parts) > 1:
            model_and_field = parts[1].split("\n")[0]
            field = (
                model_and_field.split(".")[-1] if "." in model_and_field else "unknown"
            )
        else:
            field = "unknown"
    else:
        field = "unknown"

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": f"Validation error: {error_msg}",
            "field": field,
            "type": "validation_error",
        },
    )
