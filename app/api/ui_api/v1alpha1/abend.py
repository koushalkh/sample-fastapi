from fastapi import APIRouter, HTTPException, Path
from starlette import status

from app.api import tags
from app.models.abend import AbendDetail
from app.models.generic_responses import Message

# Create the router
router = APIRouter()


@router.get(
    "/{abend_id}",
    summary="Get ABEND details for UI",
    description="Get detailed information about a specific ABEND record for UI display.",
    response_model=AbendDetail,
    responses={status.HTTP_404_NOT_FOUND: {"model": Message}},
    tags=[tags.UI_ABEND_V1ALPHA1.display_name],
)
async def get_abend(
    abend_id: str = Path(
        ..., description="The unique identifier of the ABEND record to retrieve"
    )
) -> AbendDetail:
    """
    Get detailed ABEND information for UI display
    """
    # This is just example data
    if abend_id == "1":
        return AbendDetail(
            abendId="1",
            name="ABEND-001",
            severity="HIGH",
            description="Example ABEND record 1",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ABEND record with ID {abend_id} not found",
        )
