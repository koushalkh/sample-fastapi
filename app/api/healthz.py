from fastapi import APIRouter
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from app.models import generic_responses

router = APIRouter()


@router.get(
    "",
    summary="Health check to verify service is running.",
    description="Health check to verify service is running.",
    response_model=generic_responses.GenericResponse,
    responses={HTTP_500_INTERNAL_SERVER_ERROR: {"model": generic_responses.GenericResponse}},
)
def healthz() -> generic_responses.GenericResponse:
    """
    API endpoint for kubelet to verify service liveness
    :return:
    """
    return generic_responses.GenericResponse(message="OK")
