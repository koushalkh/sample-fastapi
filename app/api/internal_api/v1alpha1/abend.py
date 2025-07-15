from fastapi import APIRouter, HTTPException
from app.models.generic_responses import Message
from models.abend import AbendItem
from api import tags
from starlette import status

# Create the router
router = APIRouter()



@router.get(
    "/{abend_id}",
    summary="Get ABEND record by ID",
    description="Get a specific Abnormal End record by its ID.",
    response_model=AbendItem,
    responses={status.HTTP_404_NOT_FOUND: {"model": Message}},
    tags=[tags.INTERNAL_ABEND_V1ALPHA1.display_name]
)
async def get_abend(abend_id: str):
    """
    Get a specific ABEND record by ID
    """
    # This is just example data
    if abend_id == "1":
        return AbendItem(
            abendId="1", 
            name="ABEND-001"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ABEND record with ID {abend_id} not found",
        )
