from fastapi import APIRouter, HTTPException
from models.generic_responses import Message
from models.sop import SOPDetail
from api import tags
from starlette import status

# Create the router
router = APIRouter()



@router.get(
    "/{sop_id}",
    summary="Get SOP details for UI",
    description="Get detailed information about a specific SOP for UI display.",
    response_model=SOPDetail,
    responses={status.HTTP_404_NOT_FOUND: {"model": Message}},
    tags=[tags.UI_SOP_V1ALPHA1.display_name]
)
async def get_sop_for_ui(sop_id: str):
    """
    Get detailed SOP information for UI display
    """
    # This is just example data
    if sop_id == "1":
        return SOPDetail(
            id="1", 
            name="SOP-001", 
            description="Example SOP 1", 
            version="1.0",
            content="This is the detailed content of SOP-001",
            last_updated="2025-07-01T12:00:00Z"
        )
    elif sop_id == "2":
        return SOPDetail(
            id="2", 
            name="SOP-002", 
            description="Example SOP 2", 
            version="1.0",
            content="This is the detailed content of SOP-002",
            last_updated="2025-07-05T14:30:00Z"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SOP with ID {sop_id} not found",
        )
