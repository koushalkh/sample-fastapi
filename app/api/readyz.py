from fastapi import APIRouter
from pydantic import BaseModel
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

router = APIRouter()


class ReadyzResult(BaseModel):
    message: str  # contains the reason for failure


@router.get(
    "",  # endpoint set in router addition prefix
    summary="Readiness probe to verify service readiness.",
    description="Readiness probe to verify service readiness.",
    response_model=ReadyzResult,
    responses={
        HTTP_500_INTERNAL_SERVER_ERROR: {"model": ReadyzResult},
    },
    tags=["service-health"],
)
def get_readyz() -> ReadyzResult:
    #  TODO: Add more detailed readiness check
    # Check for all dependent services health, database connections, etc.

    ready_probe = ReadyzResult(message="OK")
    return ready_probe
