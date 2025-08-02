from fastapi import APIRouter

from app.api import tags
from app.models.sop import SOPItem

# Create the router
router = APIRouter()


@router.get(
    "",
    summary="List all SOPs",
    description="List all Standard Operating Procedures available in the system.",
    response_model=list[SOPItem],
    tags=[tags.INTERNAL_SOP_V1ALPHA1.display_name],
)
async def list_sops() -> list[SOPItem]:
    """
    List all SOPs
    """
    # This is just example data
    return [
        SOPItem(id="1", name="SOP-001", description="Example SOP 1"),
        SOPItem(id="2", name="SOP-002", description="Example SOP 2"),
    ]
