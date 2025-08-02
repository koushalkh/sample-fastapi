from fastapi import APIRouter
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from app.models import generic_responses

router = APIRouter()


@router.get(
    "",
    summary="Health check to verify service is running.",
    description="Health check to verify service is running.",
    response_model=generic_responses.Message,
    responses={HTTP_500_INTERNAL_SERVER_ERROR: {"model": generic_responses.Message}},
)
def healthz() -> generic_responses.Message:
    """
    API endpoint for kubelet to verify service liveness
    :return:
    """
    return generic_responses.Message(message="OK")
