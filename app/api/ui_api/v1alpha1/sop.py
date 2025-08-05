from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from structlog import get_logger

from app.api import tags
from app.core.sop_service import sop_service
from app.models.generic_responses import GenericResponse
from app.models.sop import GetSOPsFilter, GetSOPsResponse, SOPDetailsResponse

# Create the router
router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/",
    summary="Get SOP records for UI",
    description="Retrieve SOP records with pagination, filtering, and search capabilities for UI display.",
    response_model=GetSOPsResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": GenericResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": GenericResponse},
    },
    tags=[tags.UI_SOP_V1ALPHA1.display_name],
)
async def get_sops_for_ui(filters: GetSOPsFilter = Depends()) -> GetSOPsResponse:
    """
    Get SOP records with filtering and pagination for UI display
    """
    try:
        return await sop_service.get_sops(filters)
    except Exception as e:
        logger.error("Failed to get SOPs for UI", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SOP records",
        )


@router.get(
    "/{sop_id}",
    summary="Get SOP details for UI",
    description="Get detailed information about a specific SOP for UI display.",
    response_model=SOPDetailsResponse,
    responses={status.HTTP_404_NOT_FOUND: {"model": GenericResponse}},
    tags=[tags.UI_SOP_V1ALPHA1.display_name],
)
async def get_sop_for_ui(sop_id: str) -> SOPDetailsResponse:
    """
    Get detailed SOP information for UI display
    """
    try:
        sop_details = await sop_service.get_sop_details(sop_id)
        if not sop_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SOP record with ID '{sop_id}' not found",
            )
        return sop_details
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get SOP details for UI", sop_id=sop_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SOP details",
        )
