"""
ABEND business logic service.
Contains all business operations for ABEND records management.
Delegates data access to the DAL layer.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Optional

from structlog import get_logger

from app.dal import abend_repository
from app.models.abend import (
    AbendDetailsModel,
    AbendDetailsResponse,
    ADRStatusEnum,
    AIRecommendationApprovalRequest,
    AIRecommendationApprovalResponse,
    AuditLevelEnum,
    AvailableFiltersResponse,
    CreateAbendRequest,
    CreateAbendResponse,
    CreateAuditLogRequest,
    CreateAuditLogResponse,
    GetAbendsFilter,
    GetAbendsResponse,
    GetAuditLogsResponse,
    JobLogsResponse,
    PaginationMeta,
    SeverityEnum,
    TodayStatsResponse,
)
from app.utils.pagination import encode_cursor

logger = get_logger(__name__)


class AbendService:
    """Business logic service for ABEND operations."""

    def __init__(self):
        self.logger = get_logger(__name__)

    async def get_abends(self, filters: GetAbendsFilter) -> GetAbendsResponse:
        """
        Get ABEND records with filtering, searching, and cursor-based pagination.
        Delegates to DAL layer for optimized database queries.
        Uses cursor-based pagination for optimal DynamoDB performance.
        """
        try:
            # Call unified DAL function with all parameters
            records, next_page_key = abend_repository.get_abends_unified(
                start_date=filters.parsed_start_date,
                end_date=filters.parsed_end_date,
                domain_area=filters.domain_area,
                adr_status=filters.adr_status,
                severity=filters.parsed_severity,
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

            return GetAbendsResponse(data=records, meta=meta)

        except Exception as e:
            self.logger.error("Error getting abends", error=str(e))
            raise

    async def get_abend_details(
        self, tracking_id: str
    ) -> Optional[AbendDetailsResponse]:
        """
        Get detailed ABEND information by tracking ID.
        Delegates to DAL layer for optimized PK query.
        """
        try:
            # Use DAL direct PK query (most efficient)
            abend_details = abend_repository.get_abend_by_tracking_id(tracking_id)

            if not abend_details:
                return None

            return AbendDetailsResponse(data=abend_details)

        except Exception as e:
            self.logger.error(
                "Error getting abend details", tracking_id=tracking_id, error=str(e)
            )
            raise

    async def create_abend(self, request: CreateAbendRequest) -> CreateAbendResponse:
        """
        Create a new ABEND record via internal API.
        Generates unique tracking ID and initializes with ABEND_REGISTERED status.
        Creates an audit log entry for tracking the ABEND creation.
        """
        try:

            self.logger.info(
                "Creating new ABEND record",
                job_name=request.job_name,
                severity=request.severity,
                incident_id=request.incident_id,
            )

            # Create ABEND record via DAL
            abend_details = abend_repository.create_abend(
                job_name=request.job_name,
                abended_at=request.abended_at,
                severity=request.severity,
                service_now_group=request.service_now_group,
                incident_id=request.incident_id,
                order_id=request.order_id,
            )

            # Create audit log entry for ABEND creation (Option A: Synchronous)
            try:
                audit_request = CreateAuditLogRequest(
                    trackingID=abend_details.tracking_id,
                    level=AuditLevelEnum.INFO,
                    adrStatus=ADRStatusEnum.ABEND_REGISTERED,
                    message=f"ABEND record created for job '{abend_details.job_name}'",
                    description=f"New ABEND record created with severity '{abend_details.severity}', incident ID '{request.incident_id}', and initial status '{abend_details.adr_status}'",
                    createdBy="system",
                )

                await self.create_audit_log(audit_request)

                self.logger.info(
                    "Audit log created for ABEND creation",
                    tracking_id=abend_details.tracking_id,
                    job_name=abend_details.job_name,
                )

            except Exception as audit_error:
                # Log audit failure but don't fail the main ABEND creation
                self.logger.warning(
                    "Failed to create audit log for ABEND creation",
                    tracking_id=abend_details.tracking_id,
                    job_name=abend_details.job_name,
                    audit_error=str(audit_error),
                )

            # Return success response
            return CreateAbendResponse(
                trackingID=abend_details.tracking_id,
                jobName=abend_details.job_name,
                adrStatus=abend_details.adr_status,
                severity=abend_details.severity,
                abendedAt=abend_details.abended_at,
                createdAt=abend_details.created_at,
                message=f"ABEND record created successfully with tracking ID: {abend_details.tracking_id}",
            )

        except Exception as e:
            self.logger.error(
                "Error creating ABEND record", job_name=request.job_name, error=str(e)
            )
            raise

    async def update_ai_remediation_approval(
        self, tracking_id: str, approval_request: AIRecommendationApprovalRequest
    ) -> Optional[AIRecommendationApprovalResponse]:
        """
        Update AI remediation approval status and comments.
        Updates the RemediationMetadata structure in the database.
        """
        try:
            # First check if record exists
            existing_record = abend_repository.get_abend_by_tracking_id(tracking_id)
            if not existing_record:
                return None

            # Get existing remediation metadata or create new one
            existing_metadata = existing_record.remediation_metadata
            approval_time = datetime.now(timezone.utc)

            # Create updated remediation metadata dict
            remediation_metadata = {
                # Preserve existing fields
                "expandability": (
                    existing_metadata.expandability if existing_metadata else None
                ),
                "confidenceScore": (
                    existing_metadata.confidence_score if existing_metadata else None
                ),
                "remediationRecommendations": (
                    existing_metadata.remediation_recommendations
                    if existing_metadata
                    else None
                ),
                "aiRemediationApprovalRequired": (
                    existing_metadata.ai_remediation_approval_required
                    if existing_metadata
                    else False
                ),
                # Update approval-specific fields
                "aiRemediationApprovalStatus": approval_request.approval_status.value,
                "aiRemediationComments": approval_request.comments,
                "aiRemediationApprovedAt": approval_time.isoformat(),
            }

            # Prepare database update
            updates: Dict[str, Any] = {
                "remediation_metadata": remediation_metadata,
                "updated_at": approval_time,
                "updated_by": "system",  # In production, get from auth context
            }

            # Use DAL layer for efficient field update
            success = abend_repository.update_abend_fields(tracking_id, updates)

            if not success:
                return None

            return AIRecommendationApprovalResponse(
                trackingID=tracking_id,
                approvalStatus=approval_request.approval_status,
                approvedAt=approval_time,
                message="AI remediation approval updated successfully",
            )

        except Exception as e:
            self.logger.error(
                "Error updating AI remediation approval",
                tracking_id=tracking_id,
                error=str(e),
            )
            raise

    async def get_available_filters(self) -> AvailableFiltersResponse:
        """
        Get available filter options for the UI.
        Returns hardcoded values for dropdown population.
        """
        return AvailableFiltersResponse(
            domainAreas=[],
            adrStatuses=[status.value for status in ADRStatusEnum],
            severities=[severity.value for severity in SeverityEnum],
        )

    async def get_job_logs(self, tracking_id: str) -> Optional[JobLogsResponse]:
        """
        Get job logs from S3 using tracking ID.
        Uses DAL layer to get ABEND details, then fetches logs from S3.
        """
        try:
            # Get ABEND details to find S3 path
            abend_details = abend_repository.get_abend_by_tracking_id(tracking_id)
            if not abend_details:
                return None

            # Extract S3 path from knowledge base metadata
            s3_file_url = self._extract_s3_log_path(abend_details, tracking_id)

            # Download from S3 (simplified implementation)
            log_content = await self._download_s3_logs(
                s3_file_url, abend_details.job_name, tracking_id
            )

            return JobLogsResponse(
                trackingID=tracking_id,
                jobName=abend_details.job_name,
                logContent=log_content,
                fileSize=len(log_content.encode("utf-8")),
                lastModified=abend_details.abended_at,
            )

        except Exception as e:
            self.logger.error(
                "Error getting job logs", tracking_id=tracking_id, error=str(e)
            )
            raise

    async def get_today_stats(self) -> TodayStatsResponse:
        """
        Get today's ABEND statistics.
        Uses DAL layer optimized stats query.
        """
        try:
            today = date.today()

            # Use DAL layer optimized stats function
            stats = abend_repository.get_stats_for_date(today)

            return TodayStatsResponse(
                activeAbends=stats.get("active_abends", 0),
                manualInterventionRequired=stats.get("manual_intervention_required", 0),
                resolvedAbends=stats.get("resolved_abends", 0),
                totalAbends=stats.get("total_abends", 0),
            )

        except Exception as e:
            self.logger.error("Error getting today stats", error=str(e))
            raise

    async def get_job_history_trends(self, job_name: str) -> Dict[str, Any]:
        """
        Get job history trends for a specific job.
        Uses DAL layer optimized job history query.
        """
        try:
            # Get last 30 days of data using DAL
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=30)

            # Use DAL job history index for efficient query
            job_history = abend_repository.get_job_history(
                job_name=job_name,
                start_date=start_date,
                end_date=end_date,
                limit=1000,  # Get all records for last 30 days
            )

            # Build trend data by aggregating by date
            trend_data: Dict[str, Dict[str, Any]] = {}
            for record in job_history:
                record_date = record.abended_at.date().isoformat()
                if record_date not in trend_data:
                    trend_data[record_date] = {
                        "date": record_date,
                        "abend_count": 0,
                        "resolved_count": 0,
                    }

                trend_data[record_date]["abend_count"] += 1
                if record.adr_status == "RESOLVED":
                    trend_data[record_date]["resolved_count"] += 1

            # Fill in missing dates with zero counts
            all_dates: list[str] = []
            for i in range(30):
                check_date = (end_date - timedelta(days=i)).date()
                date_str = check_date.isoformat()
                if date_str not in trend_data:
                    trend_data[date_str] = {
                        "date": date_str,
                        "abend_count": 0,
                        "resolved_count": 0,
                    }
                all_dates.append(date_str)

            # Sort and prepare final data
            sorted_trends: list[Dict[str, Any]] = [
                trend_data[date_str] for date_str in sorted(all_dates)
            ]

            total_abends = sum(int(day["abend_count"]) for day in sorted_trends)
            total_resolved = sum(int(day["resolved_count"]) for day in sorted_trends)

            return {
                "job_name": job_name,
                "trends": sorted_trends,  # Oldest to newest
                "total_abends_last_30_days": total_abends,
                "total_resolved_last_30_days": total_resolved,
            }

        except Exception as e:
            self.logger.error(
                "Error getting job history trends", job_name=job_name, error=str(e)
            )
            raise

    def _extract_s3_log_path(
        self, abend_details: AbendDetailsModel, tracking_id: str
    ) -> str:
        """
        Extract S3 log file path from ABEND knowledge base metadata.
        """
        # In real implementation, extract from abend_details.knowledge_base_metadata.files
        # For now, construct standard path
        return f"s3://abend-logs/{tracking_id}/job.log"

    async def _download_s3_logs(
        self, s3_path: str, job_name: str, tracking_id: str
    ) -> str:
        """
        Download log content from S3.
        Simplified implementation - in production, use boto3 S3 client.
        """
        # Simulated log content for demonstration
        return f"""
Job Log for {job_name}
Tracking ID: {tracking_id}
Generated at: {datetime.now(timezone.utc).isoformat()}

[INFO] Job execution started
[INFO] Processing batch records
[ERROR] Database connection timeout after 30 seconds
[ERROR] Failed to process record batch #245
[ERROR] Job execution failed at step: DATA_VALIDATION
[ERROR] Rolling back transaction
[ERROR] Job abended with return code: 8
""".strip()

    # Audit Log Methods
    async def create_audit_log(
        self, request: CreateAuditLogRequest
    ) -> CreateAuditLogResponse:
        """
        Create an audit log entry for tracking state changes and operations.

        Args:
            request: CreateAuditLogRequest with audit log details

        Returns:
            CreateAuditLogResponse with created audit log information

        Raises:
            Exception if creation fails
        """
        try:
            self.logger.info(
                "Creating audit log",
                tracking_id=request.tracking_id,
                level=request.level,
                adr_status=request.adr_status,
                message=request.message,
            )

            # Create audit log via DAL
            audit_log = abend_repository.create_audit_log(
                tracking_id=request.tracking_id,
                level=request.level,
                adr_status=request.adr_status,  # Use adr_status parameter
                message=request.message,
                description=request.description,
                created_by=request.created_by or "system",
            )

            return CreateAuditLogResponse(
                auditID=audit_log.audit_id,
                trackingID=audit_log.tracking_id,
                level=audit_log.level,
                adrStatus=audit_log.adr_status,
                createdAt=audit_log.created_at,
                message="Audit log created successfully",
            )

        except Exception as e:
            self.logger.error(
                "Error creating audit log",
                tracking_id=request.tracking_id,
                error=str(e),
            )
            raise

    async def get_audit_logs(self, tracking_id: str) -> GetAuditLogsResponse:
        """
        Get all audit logs for a specific tracking ID.

        Args:
            tracking_id: The tracking ID to get audit logs for

        Returns:
            GetAuditLogsResponse with list of audit logs

        Raises:
            Exception if retrieval fails
        """
        try:
            self.logger.info("Getting audit logs", tracking_id=tracking_id)

            # Get audit logs via DAL
            audit_logs = abend_repository.get_audit_logs_by_tracking_id(tracking_id)

            return GetAuditLogsResponse(
                trackingID=tracking_id, auditLogs=audit_logs, totalCount=len(audit_logs)
            )

        except Exception as e:
            self.logger.error(
                "Error getting audit logs", tracking_id=tracking_id, error=str(e)
            )
            raise


# Global service instance
abend_service = AbendService()
