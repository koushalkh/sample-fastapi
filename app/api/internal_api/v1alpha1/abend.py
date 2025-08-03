from fastapi import APIRouter, HTTPException, status
from structlog import get_logger

from app.api import tags
from app.models.generic_responses import GenericResponse
from app.models.abend import CreateAbendRequest, CreateAbendResponse
from app.core.abend_service import AbendService

# Create the router
router = APIRouter()
logger = get_logger(__name__)

# Initialize service
abend_service = AbendService()


@router.post(
    "/",
    summary="Create new ABEND record",
    description="Create a new Abnormal End record via internal API.",
    response_model=CreateAbendResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": GenericResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": GenericResponse}
    },
    tags=[tags.INTERNAL_ABEND_V1ALPHA1.display_name],
)
async def create_abend(request: CreateAbendRequest) -> CreateAbendResponse:
    """
    Create a new ABEND record.
    
    This endpoint is used by internal systems to register new ABEND incidents.
    The record will be created with ABEND_REGISTERED status and can be processed
    through the automated detection and remediation workflow.
    
    Args:
        request: ABEND creation request with required fields
        
    Returns:
        CreateAbendResponse with tracking ID and record details
        
    Raises:
        HTTPException: For validation errors or creation failures
    """
    try:
        logger.info("Received create ABEND request",
                   job_name=request.job_name,
                   severity=request.severity,
                   incident_id=request.incident_id)
        
        # Create ABEND via service layer
        response = await abend_service.create_abend(request)
        
        logger.info("Successfully created ABEND record",
                   tracking_id=response.tracking_id,
                   job_name=response.job_name,
                   adr_status=response.adr_status)
        
        return response
        
    except ValueError as e:
        logger.error("Validation error creating ABEND", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error("Error creating ABEND record", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error creating ABEND record"
        )


# @router.get(
#     "/{abend_id}",
#     summary="Get ABEND record by ID",
#     description="Get a specific Abnormal End record by its ID.",
#     response_model=AbendItem,
#     responses={status.HTTP_404_NOT_FOUND: {"model": GenericResponse}},
#     tags=[tags.INTERNAL_ABEND_V1ALPHA1.display_name],
# )
# async def get_abend(abend_id: str) -> AbendItem:
#     """
#     Get a specific ABEND record by ID
#     """
#     # This is just example data
#     if abend_id == "1":
#         return AbendItem(abendId="1", name="ABEND-001")
#     else:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"ABEND record with ID {abend_id} not found",
#         )
