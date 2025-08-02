from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class SeverityEnum(str, Enum):
    """Severity levels for ABEND incidents."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ADRStatusEnum(str, Enum):
    """ADR (Automated Detection & Remediation) status values - Complete state machine."""
    ABEND_REGISTERED = "ABEND_REGISTERED"
    LOG_EXTRACTION_INITIATED = "LOG_EXTRACTION_INITIATED"
    MANUAL_INTERVENTION_REQUIRED = "MANUAL_INTERVENTION_REQUIRED"
    LOG_UPLOAD_TO_S3 = "LOG_UPLOAD_TO_S3"
    PREPROCESSING_LOG_FILE = "PREPROCESSING_LOG_FILE"
    AI_ANALYSIS_INITIATED = "AI_ANALYSIS_INITIATED"
    MANUAL_ANALYSIS_REQUIRED = "MANUAL_ANALYSIS_REQUIRED"
    REMEDIATION_SUGGESTIONS_GENERATED = "REMEDIATION_SUGGESTIONS_GENERATED"
    AUTOMATED_REMEDIATION_IN_PROGRESS = "AUTOMATED_REMEDIATION_IN_PROGRESS"
    PENDING_MANUAL_APPROVAL = "PENDING_MANUAL_APPROVAL"
    VERIFICATION_IN_PROGRESS = "VERIFICATION_IN_PROGRESS"
    RESOLVED = "RESOLVED"


class AIRemediationApprovalStatusEnum(str, Enum):
    """AI Remediation approval status values."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class EmailMetadata(BaseModel):
    """Email metadata for ABEND notifications."""
    subject: Optional[str] = None
    from_address: Optional[str] = Field(None, alias="from")
    to: Optional[str] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None
    sent_date_time: Optional[datetime] = Field(None, alias="sentDateTime")
    received_date_time: Optional[datetime] = Field(None, alias="receivedDateTime")
    has_attachments: bool = Field(False, alias="hasAttachments")
    conversation_id: Optional[str] = Field(None, alias="conversationID")
    message_id: Optional[str] = Field(None, alias="messageID")


class KnowledgeBaseFile(BaseModel):
    """File metadata in knowledge base."""
    file_name: str = Field(..., alias="fileName")
    file_type: str = Field(..., alias="fileType")
    file_size: int = Field(..., alias="fileSize")
    file_url: str = Field(..., alias="fileUrl")


class KnowledgeBaseMetadata(BaseModel):
    """Knowledge base metadata for ABEND remediation."""
    relevant_sop_id: Optional[str] = Field(None, alias="relevantSOPId")
    files: List[KnowledgeBaseFile] = Field(default_factory=list)


class RemediationMetadata(BaseModel):
    """AI remediation metadata and recommendations."""
    expandability: Optional[str] = None
    confidence_score: Optional[float] = Field(None, alias="confidenceScore", ge=0.0, le=1.0)
    remediation_recommendations: Optional[str] = Field(None, alias="remediationRecommendations")
    ai_remediation_approval_status: Optional[AIRemediationApprovalStatusEnum] = Field(None, alias="aiRemediationApprovalStatus")
    ai_remediation_approval_required: bool = Field(False, alias="aiRemediationApprovalRequired")
    ai_remediation_comments: Optional[str] = Field(None, alias="aiRemediationComments")
    ai_remediation_approved_at: Optional[datetime] = Field(None, alias="aiRemediationApprovedAt")


class AbendModel(BaseModel):
    """Simplified ABEND model for UI table display and listing."""
    tracking_id: str = Field(..., alias="trackingID")
    job_id: str = Field(..., alias="jobID")
    job_name: str = Field(..., alias="jobName")
    adr_status: ADRStatusEnum = Field(..., alias="adrStatus")
    severity: SeverityEnum
    abended_at: datetime = Field(..., alias="abendedAt")
    domain_area: Optional[str] = Field(None, alias="domainArea")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


class AbendDetailsModel(BaseModel):
    """Complete ABEND model with all details."""
    # Basic fields (from AbendModel)
    tracking_id: str = Field(..., alias="trackingID")
    job_id: str = Field(..., alias="jobID")
    job_name: str = Field(..., alias="jobName")
    abended_at: datetime = Field(..., alias="abendedAt")
    adr_status: ADRStatusEnum = Field(..., alias="adrStatus")
    severity: SeverityEnum
    domain_area: Optional[str] = Field(None, alias="domainArea")
    incident_number: Optional[str] = Field(None, alias="incidentNumber")
    
    # Additional basic fields
    order_id: Optional[str] = Field(None, alias="orderID")
    fa_id: Optional[str] = Field(None, alias="faID")
    abend_step: Optional[str] = Field(None, alias="abendStep")
    abend_return_code: Optional[str] = Field(None, alias="abendReturnCode")
    abend_reason: Optional[str] = Field(None, alias="abendReason")
    abend_type: Optional[str] = Field(None, alias="abendType")
    
    # Performance metrics (flattened)
    perf_log_extraction_time: Optional[str] = Field(None, alias="perfLogExtractionTime")
    perf_ai_analysis_time: Optional[str] = Field(None, alias="perfAiAnalysisTime")
    perf_remediation_time: Optional[str] = Field(None, alias="perfRemediationTime")
    perf_total_automated_time: Optional[str] = Field(None, alias="perfTotalAutomatedTime")
    
    # Log extraction metadata (flattened)
    log_extraction_run_id: Optional[str] = Field(None, alias="logExtractionRunId")
    log_extraction_retries: int = Field(0, alias="logExtractionRetries")
    
    # Complex nested objects
    email_metadata: Optional[EmailMetadata] = Field(None, alias="emailMetadata")
    knowledge_base_metadata: Optional[KnowledgeBaseMetadata] = Field(None, alias="knowledgeBaseMetadata")
    remediation_metadata: Optional[RemediationMetadata] = Field(None, alias="remediationMetadata")
    
    # Audit fields
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")
    created_by: str = Field(default="system", alias="createdBy")
    updated_by: str = Field(default="system", alias="updatedBy")
    generation: int = Field(default=1)


# Request Models
class GetAbendsRequest(BaseModel):
    """Request model for getting ABEND records with filters and pagination."""
    # Filters
    domain_area: Optional[str] = Field(None, alias="domainArea")
    adr_status: Optional[ADRStatusEnum] = Field(None, alias="adrStatus")
    severity: Optional[SeverityEnum] = None
    
    # Date filters - either single date or range
    abended_at: Optional[date] = Field(None, alias="abendedAt", description="Filter by specific date")
    abended_at_start_date: Optional[date] = Field(None, alias="abendedAtStartDate", description="Start date for range filter")
    abended_at_end_date: Optional[date] = Field(None, alias="abendedAtEndDate", description="End date for range filter")
    
    # Search
    search: Optional[str] = Field(None, description="Search by job name")
    
    # Pagination
    limit: int = Field(default=5, ge=1, le=10, description="Number of records per page (max 10)")
    offset: int = Field(default=0, ge=0, description="Number of records to skip")

    @field_validator('abended_at_end_date')
    @classmethod
    def validate_date_range(cls, v: Optional[date], info) -> Optional[date]:
        """Ensure end date is not before start date."""
        if v and info.data.get('abended_at_start_date') and v < info.data['abended_at_start_date']:
            raise ValueError('End date cannot be before start date')
        return v

    @field_validator('abended_at')
    @classmethod
    def validate_single_date_vs_range(cls, v: Optional[date], info) -> Optional[date]:
        """Ensure single date and range filters are not used together."""
        if v and (info.data.get('abended_at_start_date') or info.data.get('abended_at_end_date')):
            raise ValueError('Cannot use both single date and date range filters')
        return v


class AIRecommendationApprovalRequest(BaseModel):
    """Request model for AI recommendation approval."""
    approval_status: AIRemediationApprovalStatusEnum = Field(..., alias="approvalStatus")
    comments: Optional[str] = Field(None, description="Approval comments")


# Response Models
class PaginationMeta(BaseModel):
    """Pagination metadata."""
    total: int = Field(..., description="Total number of records")
    limit: int = Field(..., description="Records per page")
    offset: int = Field(..., description="Records skipped")
    has_next: bool = Field(..., alias="hasNext", description="Whether there are more records")
    has_previous: bool = Field(..., alias="hasPrevious", description="Whether there are previous records")


class GetAbendsResponse(BaseModel):
    """Response model for getting ABEND records."""
    data: List[AbendModel] = Field(..., description="List of ABEND records")
    meta: PaginationMeta = Field(..., description="Pagination metadata")


class AbendDetailsResponse(BaseModel):
    """Response model for ABEND details."""
    data: AbendDetailsModel = Field(..., description="Complete ABEND details")


class AvailableFiltersResponse(BaseModel):
    """Response model for available filter values."""
    domain_areas: List[str] = Field(..., alias="domainAreas", description="Available domain areas")
    adr_statuses: List[str] = Field(..., alias="adrStatuses", description="Available ADR statuses")
    severities: List[str] = Field(..., description="Available severity levels")


class TodayStatsResponse(BaseModel):
    """Response model for today's statistics."""
    active_abends: int = Field(..., alias="activeAbends", description="Number of active ABENDs (not resolved)")
    manual_intervention_required: int = Field(..., alias="manualInterventionRequired", 
                                            description="Number of ABENDs requiring manual intervention")
    resolved_abends: int = Field(..., alias="resolvedAbends", description="Number of resolved ABENDs")
    total_abends: int = Field(..., alias="totalAbends", description="Total ABENDs for today")


class JobLogsResponse(BaseModel):
    """Response model for job logs from S3."""
    tracking_id: str = Field(..., alias="trackingID", description="ABEND tracking ID")
    job_name: str = Field(..., alias="jobName", description="Job name")
    log_content: str = Field(..., alias="logContent", description="Log file content from S3")
    file_size: Optional[int] = Field(None, alias="fileSize", description="File size in bytes")
    last_modified: Optional[datetime] = Field(None, alias="lastModified", description="Last modified timestamp")


class AIRecommendationApprovalResponse(BaseModel):
    """Response model for AI recommendation approval."""
    tracking_id: str = Field(..., alias="trackingID", description="ABEND tracking ID")
    approval_status: AIRemediationApprovalStatusEnum = Field(..., alias="approvalStatus")
    approved_at: datetime = Field(..., alias="approvedAt", description="Approval timestamp")
    message: str = Field(..., description="Success message")
