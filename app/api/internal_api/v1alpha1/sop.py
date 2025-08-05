from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List
from structlog import get_logger

from app.api import tags
from app.models.generic_responses import GenericResponse
from app.models.sop import (
    CreateSOPRequest,
    CreateSOPResponse,
    UpdateSOPRequest,
    UpdateSOPResponse,
    SOPDetailsResponse
)
from app.core.sop_service import sop_service

# Create the router
router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/",
    summary="Create new SOP record",
    description="Create a new Standard Operating Procedure record via internal API.",
    response_model=CreateSOPResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": GenericResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": GenericResponse}
    },
    tags=[tags.INTERNAL_SOP_V1ALPHA1.display_name],
)
async def create_sop(request: CreateSOPRequest) -> CreateSOPResponse:
    """
    Create a new SOP record
    """
    try:
        return await sop_service.create_sop(request)
    except Exception as e:
        logger.error("Failed to create SOP", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create SOP record"
        )


@router.get(
    "/{sop_id}",
    summary="Get SOP record by ID",
    description="Retrieve a specific SOP record by its ID via internal API.",
    response_model=SOPDetailsResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": GenericResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": GenericResponse}
    },
    tags=[tags.INTERNAL_SOP_V1ALPHA1.display_name],
)
async def get_sop(sop_id: str) -> SOPDetailsResponse:
    """
    Get SOP record by ID
    """
    try:
        sop_details = await sop_service.get_sop_details(sop_id)
        if not sop_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SOP record with ID '{sop_id}' not found"
            )
        return sop_details
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get SOP", sop_id=sop_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SOP record"
        )


@router.put(
    "/{sop_id}",
    summary="Update SOP record",
    description="Update an existing SOP record by its ID via internal API.",
    response_model=UpdateSOPResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": GenericResponse},
        status.HTTP_400_BAD_REQUEST: {"model": GenericResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": GenericResponse}
    },
    tags=[tags.INTERNAL_SOP_V1ALPHA1.display_name],
)
async def update_sop(sop_id: str, request: UpdateSOPRequest) -> UpdateSOPResponse:
    """
    Update SOP record
    """
    try:
        update_response = await sop_service.update_sop(sop_id, request)
        if not update_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SOP record with ID '{sop_id}' not found"
            )
        return update_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update SOP", sop_id=sop_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update SOP record"
        )


@router.delete(
    "/{sop_id}",
    summary="Delete SOP record",
    description="Delete an existing SOP record by its ID via internal API.",
    response_model=GenericResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": GenericResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": GenericResponse}
    },
    tags=[tags.INTERNAL_SOP_V1ALPHA1.display_name],
)
async def delete_sop(sop_id: str) -> GenericResponse:
    """
    Delete SOP record (placeholder implementation)
    """
    try:
        success = await sop_service.delete_sop(sop_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SOP record with ID '{sop_id}' not found or deletion not yet implemented"
            )
        return GenericResponse(message=f"SOP record '{sop_id}' deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete SOP", sop_id=sop_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete SOP record"
        )


# Legacy endpoint for backward compatibility
@router.get(
    "",
    summary="List all SOPs (Legacy)",
    description="List all Standard Operating Procedures available in the system (Legacy endpoint).",
    response_model=list[dict[str, str]],
    tags=[tags.INTERNAL_SOP_V1ALPHA1.display_name],
)
async def list_sops() -> list[dict[str, str]]:
    """
    List all SOPs (Legacy endpoint for backward compatibility)
    """
    # This is legacy example data - kept for backward compatibility
    # In the future, this could redirect to the new unified query endpoint
    return [
        {"id": "1", "name": "SOP-001", "description": "Example SOP 1"},
        {"id": "2", "name": "SOP-002", "description": "Example SOP 2"},
    ]
