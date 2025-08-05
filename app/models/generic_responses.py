from pydantic import BaseModel, Field

"""
Generic response models and error handling for API endpoints.
"""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Error detail model."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field name if validation error")


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Error details")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Error timestamp",
    )


class SuccessResponse(BaseModel):
    """Generic success response model."""

    message: str = Field(..., description="Success message")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response timestamp",
    )


# Keep existing legacy models for backwards compatibility
class GenericResponse(BaseModel):
    message: str
