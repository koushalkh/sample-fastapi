"""
SOP business logic service.
Contains all business operations for SOP records management.
Delegates data access to the DAL layer.
"""

from datetime import datetime, timezone
from typing import Optional

from structlog import get_logger

from app.dal import sop_repository
from app.models.sop import (
    CreateSOPRequest,
    CreateSOPResponse,
    GetSOPsFilter,
    GetSOPsResponse,
    PaginationMeta,
    SOPDetailsResponse,
    UpdateSOPRequest,
    UpdateSOPResponse,
)
from app.utils.pagination import encode_cursor

logger = get_logger(__name__)


class SOPService:
    """Business logic service for SOP operations."""

    def __init__(self):
        self.logger = get_logger(__name__)

    async def get_sops(self, filters: GetSOPsFilter) -> GetSOPsResponse:
        """
        Get SOP records with filtering, searching, and cursor-based pagination.
        Delegates to DAL layer for optimized database queries.
        Uses cursor-based pagination for optimal DynamoDB performance.
        """
        try:
            # Call unified DAL function with all parameters
            records, next_page_key = sop_repository.get_sops_unified(
                job_name=filters.job_name,
                abend_type=filters.abend_type,
                search_term=filters.search,
                limit=filters.limit,
                last_evaluated_key=filters.decoded_cursor,
            )

            # Build pagination metadata with cursor support
            has_next = next_page_key is not None
            has_previous = filters.cursor is not None

            # Generate cursors for next/previous pages
            next_cursor = encode_cursor(next_page_key) if next_page_key else None
            prev_cursor = (
                None  # For simplicity, not implementing reverse pagination cursors
            )

            # Estimate total - in production, implement count queries or caching
            estimated_total = len(records) + (filters.limit if has_next else 0)

            meta = PaginationMeta(
                total=estimated_total,
                limit=filters.limit,
                hasNext=has_next,
                hasPrevious=has_previous,
                nextCursor=next_cursor,
                prevCursor=prev_cursor,
            )

            return GetSOPsResponse(data=records, meta=meta)

        except Exception as e:
            self.logger.error("Error getting SOPs", error=str(e))
            raise

    async def get_sop_details(self, sop_id: str) -> Optional[SOPDetailsResponse]:
        """
        Get detailed SOP information by ID.
        Delegates to DAL layer for optimized PK query.
        """
        try:
            # Use DAL direct PK query (most efficient)
            sop_details = sop_repository.get_sop_by_id(sop_id)

            if not sop_details:
                return None

            return SOPDetailsResponse(data=sop_details)

        except Exception as e:
            self.logger.error("Error getting SOP details", sop_id=sop_id, error=str(e))
            raise

    async def create_sop(self, request: CreateSOPRequest) -> CreateSOPResponse:
        """
        Create a new SOP record via internal API.
        Generates unique SOP ID and initializes with proper audit fields.
        """
        try:
            self.logger.info(
                "Creating new SOP record",
                sop_name=request.sop_name,
                job_name=request.job_name,
                abend_type=request.abend_type,
            )

            # Create SOP record via DAL
            sop_details = sop_repository.create_sop(
                sop_name=request.sop_name,
                job_name=request.job_name,
                abend_type=request.abend_type,
                source_document_url=request.source_document_url,
                processed_document_urls=request.processed_document_urls,
                created_by=request.created_by or "system",
            )

            # Return success response
            return CreateSOPResponse(
                sopID=sop_details.sop_id,
                sopName=sop_details.sop_name,
                jobName=sop_details.job_name,
                abendType=sop_details.abend_type,
                createdAt=sop_details.created_at,
                message=f"SOP record created successfully with ID: {sop_details.sop_id}",
            )

        except Exception as e:
            self.logger.error(
                "Error creating SOP record", sop_name=request.sop_name, error=str(e)
            )
            raise

    async def update_sop(
        self, sop_id: str, request: UpdateSOPRequest
    ) -> Optional[UpdateSOPResponse]:
        """
        Update an existing SOP record.
        Updates only provided fields and maintains audit trail.
        """
        try:
            self.logger.info("Updating SOP record", sop_id=sop_id)

            # First check if record exists
            existing_sop = sop_repository.get_sop_by_id(sop_id)
            if not existing_sop:
                return None

            # Build updates dictionary from request
            updates = {}
            if request.sop_name is not None:
                updates["sop_name"] = request.sop_name
            if request.job_name is not None:
                updates["job_name"] = request.job_name
            if request.abend_type is not None:
                updates["abend_type"] = request.abend_type
            if request.source_document_url is not None:
                updates["source_document_url"] = request.source_document_url
            if request.processed_document_urls is not None:
                updates["processed_document_urls"] = request.processed_document_urls
            if request.updated_by is not None:
                updates["updated_by"] = request.updated_by

            # Only proceed if there are actual updates
            if not updates:
                # No updates provided, return success anyway
                return UpdateSOPResponse(
                    sopID=sop_id,
                    updatedAt=existing_sop.updated_at,
                    generation=existing_sop.generation,
                    message="No changes provided - SOP record unchanged",
                )

            # Perform update via DAL
            update_time = datetime.now(timezone.utc)
            updates["updated_at"] = update_time

            success = sop_repository.update_sop_fields(sop_id, updates)

            if not success:
                return None

            # Return success response
            return UpdateSOPResponse(
                sopID=sop_id,
                updatedAt=update_time,
                generation=existing_sop.generation + 1,  # Incremented by DAL
                message="SOP record updated successfully",
            )

        except Exception as e:
            self.logger.error("Error updating SOP record", sop_id=sop_id, error=str(e))
            raise

    async def delete_sop(self, sop_id: str) -> bool:
        """
        Delete a SOP record (placeholder for future implementation).

        Args:
            sop_id: The SOP ID to delete

        Returns:
            True if deleted successfully, False if not found

        Note:
            This could be implemented as a soft delete by adding an 'active' field,
            or as a hard delete by removing the record entirely.
        """
        try:
            self.logger.info("Deleting SOP record", sop_id=sop_id)

            # TODO: Implement SOP deletion
            # For now, this is a placeholder

            self.logger.warning("SOP deletion not yet implemented", sop_id=sop_id)
            return False

        except Exception as e:
            self.logger.error("Error deleting SOP record", sop_id=sop_id, error=str(e))
            raise


# Global service instance
sop_service = SOPService()
