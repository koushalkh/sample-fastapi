from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from structlog import get_logger

from app.api import tags
from app.core.abend_service import abend_service
from app.models.abend import (
    ADRStatusEnum,
    AuditLevelEnum,
    CreateAuditLogRequest,
    CreateAuditLogResponse,
    GetAuditLogsResponse,
)
from app.models.generic_responses import GenericResponse

# Create the router
router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/",
    summary="Create audit log entry",
    description="Create a new audit log entry for tracking state changes and operations.",
    response_model=CreateAuditLogResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": GenericResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": GenericResponse},
    },
    tags=[tags.INTERNAL_ABEND_V1ALPHA1.display_name],
)
async def create_audit_log(request: CreateAuditLogRequest) -> CreateAuditLogResponse:
    """
    Create a new audit log entry.

    This endpoint is used by internal systems to create audit trail entries
    for tracking state changes, operations, and other significant events
    in the ABEND workflow.

    Args:
        request: Audit log creation request with required fields

    Returns:
        CreateAuditLogResponse with created audit log information

    Raises:
        HTTPException: For validation errors or creation failures
    """
    try:
        logger.info(
            "Received create audit log request",
            tracking_id=request.tracking_id,
            level=request.level,
            adr_status=request.adr_status,
            message=request.message,
        )

        # Create audit log via service layer
        response = await abend_service.create_audit_log(request)

        logger.info(
            "Successfully created audit log entry",
            audit_id=response.audit_id,
            tracking_id=response.tracking_id,
            level=response.level,
            adr_status=response.adr_status,
        )

        return response

    except ValueError as e:
        logger.error(
            "Validation error creating audit log",
            tracking_id=getattr(request, "tracking_id", "unknown"),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}",
        )
    except Exception as e:
        logger.error(
            "Error creating audit log",
            tracking_id=getattr(request, "tracking_id", "unknown"),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error creating audit log",
        )


@router.get(
    "/{tracking_id}",
    summary="Get audit logs by tracking ID",
    description="Get all audit log entries for a specific tracking ID.",
    response_model=GetAuditLogsResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": GenericResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": GenericResponse},
    },
    tags=[tags.INTERNAL_ABEND_V1ALPHA1.display_name],
)
async def get_audit_logs(
    tracking_id: str,
    level: Optional[AuditLevelEnum] = Query(
        None, description="Filter by audit log level"
    ),
    adr_status: Optional[ADRStatusEnum] = Query(
        None, description="Filter by ADR status", alias="adrStatus"
    ),
    limit: Optional[int] = Query(
        None, description="Maximum number of audit logs to return", ge=1, le=100
    ),
) -> GetAuditLogsResponse:
    """
    Get audit logs for a specific tracking ID.

    This endpoint is used by internal systems to retrieve audit trail entries
    for a specific ABEND record or workflow instance.

    Args:
        tracking_id: The tracking ID to get audit logs for
        level: Optional filter by audit log level (INFO, WARN, ERROR, DEBUG)
        adr_status: Optional filter by ADR status
        limit: Optional limit on number of results (1-100)

    Returns:
        GetAuditLogsResponse with list of audit logs

    Raises:
        HTTPException: For not found or retrieval failures
    """
    try:
        logger.info(
            "Getting audit logs via internal API",
            tracking_id=tracking_id,
            level=level,
            adr_status=adr_status,
            limit=limit,
        )

        # Get audit logs via service layer
        response = await abend_service.get_audit_logs(tracking_id)

        # Apply optional filters
        filtered_logs = response.audit_logs

        if level:
            filtered_logs = [log for log in filtered_logs if log.level == level]

        if adr_status:
            filtered_logs = [
                log for log in filtered_logs if log.adr_status == adr_status
            ]

        if limit:
            filtered_logs = filtered_logs[:limit]

        # Create filtered response
        filtered_response = GetAuditLogsResponse(
            trackingID=tracking_id,
            auditLogs=filtered_logs,
            totalCount=len(filtered_logs),
        )

        logger.info(
            "Successfully retrieved audit logs via internal API",
            tracking_id=tracking_id,
            total_count=len(filtered_logs),
            original_count=len(response.audit_logs),
        )

        if len(filtered_logs) == 0:
            logger.warning(
                "No audit logs found for tracking ID", tracking_id=tracking_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No audit logs found for tracking ID: {tracking_id}",
            )

        return filtered_response

    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(
            "Error retrieving audit logs via internal API",
            tracking_id=tracking_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving audit logs",
        )
