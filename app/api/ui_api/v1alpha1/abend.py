"""
ABEND API endpoints for UI operations.
This module provides versioned API endpoints for ABEND management.
All business logic is delegated to the core service layer.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Path, status
from structlog import get_logger

from app.core.abend_service import abend_service
from app.models.abend import (
    AbendDetailsResponse,
    AIRecommendationApprovalRequest,
    AIRecommendationApprovalResponse,
    AvailableFiltersResponse,
    GetAbendsFilter,
    GetAbendsResponse,
    GetAuditLogsResponse,
    JobLogsResponse,
    TodayStatsResponse,
)
from app.models.generic_responses import ErrorResponse

logger = get_logger(__name__)

router = APIRouter(tags=["ABEND UI"])


@router.get(
    "/",
    response_model=GetAbendsResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get ABEND Records",
    description="Retrieve ABEND records with pagination, filtering, and search capabilities.",
)
async def get_abends(filters: GetAbendsFilter = Depends()) -> GetAbendsResponse:
    """
    Get ABEND records with comprehensive filtering and pagination.

    This endpoint uses cursor-based pagination for optimal performance:

    **Cursor-based pagination:**
    - Use `limit` and `cursor` parameters
    - Efficient for large datasets with O(1) performance
    - Optimized for DynamoDB access patterns
    - Get `nextCursor` from response.meta for next page
    - Leave `cursor` empty for first page

    **Other features:**
    - Search by job name (case-insensitive partial matching)
    - Filtering by domain area, severity, and date ranges
    - Default filter to today's records if no date filters specified
    - All validation handled automatically by Pydantic models
    """
    # Delegate to service layer - all validation is handled by Pydantic in GetAbendsFilter
    # Pydantic validation errors are now handled by global exception handlers
    result = await abend_service.get_abends(filters)

    return result


@router.get(
    "/{tracking_id}",
    response_model=AbendDetailsResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get ABEND Details",
    description="Retrieve detailed information for a specific ABEND record by tracking ID.",
)
async def get_abend_details(
    tracking_id: str = Path(..., min_length=1, description="ABEND tracking ID")
) -> AbendDetailsResponse:
    """
    Get detailed ABEND information by tracking ID.

    Returns comprehensive details including:
    - Basic ABEND information
    - Remediation metadata
    - Knowledge base references
    - Status and timing information
    """
    try:
        result = await abend_service.get_abend_details(tracking_id.strip())

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ABEND record with tracking ID '{tracking_id}' not found",
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in get_abend_details API", tracking_id=tracking_id, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving ABEND details",
        )


@router.put(
    "/{tracking_id}/ai-remediation-approval",
    response_model=AIRecommendationApprovalResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Update AI Remediation Approval",
    description="Update the approval status and comments for AI-generated remediation recommendations.",
)
async def update_ai_remediation_approval(
    approval_request: AIRecommendationApprovalRequest,
    tracking_id: str = Path(..., min_length=1, description="ABEND tracking ID"),
) -> AIRecommendationApprovalResponse:
    """
    Update AI remediation approval status and comments.

    This endpoint allows users to:
    - Approve or reject AI-generated remediation recommendations
    - Add comments explaining the approval decision
    - Track approval timestamps
    """
    try:
        result = await abend_service.update_ai_remediation_approval(
            tracking_id.strip(), approval_request
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ABEND record with tracking ID '{tracking_id}' not found",
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in update_ai_remediation_approval API",
            tracking_id=tracking_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while updating AI remediation approval",
        )


@router.get(
    "/filters/available",
    response_model=AvailableFiltersResponse,
    responses={
        500: {"model": ErrorResponse},
    },
    summary="Get Available Filters",
    description="Retrieve all available filter options for the ABEND listing page.",
)
async def get_available_filters() -> AvailableFiltersResponse:
    """
    Get available filter options for the UI.

    Returns:
    - Available domain areas
    - ADR status options
    - Severity levels

    This endpoint is used to populate filter dropdowns in the UI.
    """
    try:
        result = await abend_service.get_available_filters()
        return result

    except Exception as e:
        logger.error("Error in get_available_filters API", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving available filters",
        )


@router.get(
    "/{tracking_id}/logs",
    response_model=JobLogsResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get ABEND Job Logs",
    description="Retrieve job execution logs from S3 for a specific ABEND record.",
)
async def get_abend_logs(
    tracking_id: str = Path(..., min_length=1, description="ABEND tracking ID")
) -> JobLogsResponse:
    """
    Get job logs from S3 using tracking ID.

    This endpoint:
    - Retrieves the S3 path from the ABEND record's knowledge base metadata
    - Downloads and returns the job execution logs
    - Includes file metadata (size, last modified)
    """
    try:
        result = await abend_service.get_job_logs(tracking_id.strip())

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job logs for tracking ID '{tracking_id}' not found",
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in get_abend_logs API", tracking_id=tracking_id, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving job logs",
        )


@router.get(
    "/stats/today",
    response_model=TodayStatsResponse,
    responses={
        500: {"model": ErrorResponse},
    },
    summary="Get Today's ABEND Statistics",
    description="Retrieve summarized statistics for today's ABEND records.",
)
async def get_today_stats() -> TodayStatsResponse:
    """
    Get today's ABEND statistics.

    Returns aggregated counts for:
    - Active abends requiring attention
    - Abends requiring manual intervention
    - Resolved abends
    - Total abends for the day

    This endpoint supports dashboard widgets and summary views.
    """
    try:
        result = await abend_service.get_today_stats()
        return result

    except Exception as e:
        logger.error("Error in get_today_stats API", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving today's statistics",
        )


@router.get(
    "/job/{job_name}/trends",
    responses={
        500: {"model": ErrorResponse},
    },
    summary="Get Job History Trends",
    description="Retrieve historical trend data for a specific job's ABEND occurrences.",
)
async def get_job_history_trends(
    job_name: str = Path(..., min_length=1, description="Job name for trend analysis")
) -> Dict[str, Any]:
    """
    Get job history trends for analytics and trending views.

    Returns:
    - 30-day trend data for ABEND occurrences
    - Resolved vs. active counts over time
    - Aggregated statistics for the time period

    This endpoint supports analytical dashboards and trend visualization.
    """
    try:
        result = await abend_service.get_job_history_trends(job_name.strip())
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in get_job_history_trends API", job_name=job_name, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving job history trends",
        )


@router.get(
    "/{tracking_id}/audit-logs",
    response_model=GetAuditLogsResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get Audit Logs for ABEND",
    description="Retrieve all audit logs for a specific ABEND tracking ID.",
)
async def get_audit_logs_for_tracking_id(
    tracking_id: str = Path(..., description="ABEND tracking ID", min_length=1)
) -> GetAuditLogsResponse:
    """
    Get all audit logs for a specific ABEND tracking ID.

    This endpoint retrieves the complete audit trail for an ABEND record, showing:
    - State transitions and status changes
    - System actions and interventions
    - Error conditions and resolutions
    - Chronological order of events

    Args:
        tracking_id: The ABEND tracking ID (e.g., "ABEND_JOBNAME_01K1T5TP0RX6...")

    Returns:
        GetAuditLogsResponse: Complete audit trail with metadata

    Raises:
        400: Invalid tracking ID format
        404: Tracking ID not found or no audit logs exist
        500: Internal server error

    Example:
        GET /ui-api/v1alpha1/abends/ABEND_CLAIMS_01K1T5TP0RX6.../audit-logs
    """
    try:
        # Validate tracking ID format
        if not tracking_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tracking ID cannot be empty",
            )

        # Clean and validate tracking ID
        tracking_id = tracking_id.strip()
        if len(tracking_id) < 10:  # Basic validation - should be longer
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tracking ID format",
            )

        logger.info("Getting audit logs via UI API", tracking_id=tracking_id)

        # Get audit logs via service layer
        result = await abend_service.get_audit_logs(tracking_id)

        # Check if any audit logs were found
        if not result.audit_logs:
            logger.warning(
                "No audit logs found for tracking ID", tracking_id=tracking_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No audit logs found for tracking ID: {tracking_id}",
            )

        logger.info(
            "Successfully retrieved audit logs via UI API",
            tracking_id=tracking_id,
            count=len(result.audit_logs),
        )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions (400, 404, etc.)
        raise
    except Exception as e:
        logger.error(
            "Error in get_audit_logs_for_tracking_id API",
            tracking_id=tracking_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving audit logs",
        )
