from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator, model_validator
from app.utils.pagination import is_valid_cursor, decode_cursor


class SeverityEnum(str, Enum):
    """Severity levels for ABEND incidents."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


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
    job_id: Optional[str] = Field(None, alias="jobID")
    job_name: str = Field(..., alias="jobName")
    adr_status: ADRStatusEnum = Field(..., alias="adrStatus")
    severity: Optional[SeverityEnum] = Field(None, description="Severity level of the ABEND incident")
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
class GetAbendsFilter(BaseModel):
    """Filter model for getting ABEND records with filters and cursor-based pagination."""
    # Filters
    domain_area: Optional[str] = Field(None, alias="domainArea")
    adr_status: Optional[ADRStatusEnum] = Field(None, alias="adrStatus")
    severity: Optional[str] = Field(None, description="Severity level (will be converted to enum)")
    
    # Date filters - simplified logic: start_date required, end_date optional
    abended_at_start_date: Optional[str] = Field(None, alias="abendedAtStartDate", description="Start date (YYYY-MM-DD). If end_date not provided, searches single day. Defaults to today if not provided.")
    abended_at_end_date: Optional[str] = Field(None, alias="abendedAtEndDate", description="End date for range filter (YYYY-MM-DD). Optional - if not provided, searches single day using start_date.")
    
    # Search
    search: Optional[str] = Field(None, description="Search by job name")
    
    # Pagination - cursor-based only for optimal performance
    limit: int = Field(default=5, ge=1, le=10, description="Number of records per page (max 100)")
    cursor: Optional[str] = Field(None, description="Pagination cursor for efficient cursor-based pagination")
    
    # Internal converted fields (populated after validation)
    _parsed_severity: Optional[SeverityEnum] = None
    _parsed_start_date: Optional[date] = None
    _parsed_end_date: Optional[date] = None
    _decoded_cursor: Optional[Dict[str, Any]] = None

    @field_validator('cursor')
    @classmethod
    def validate_cursor(cls, v: Optional[str]) -> Optional[str]:
        """Validate cursor format and decodability."""
        if v is None:
            return v
        
        if not is_valid_cursor(v):
            raise ValueError("Invalid cursor format. Cursor must be a valid base64-encoded pagination token.")
        
        return v

    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v: Optional[str]) -> Optional[str]:
        """Validate and return the severity string for later conversion (case-insensitive and handles migration)."""
        if v is None:
            return v
        
        # Handle case-insensitive mapping and migration from old format
        v_upper = v.upper()
        severity_mapping = {
            'HIGH': 'HIGH',
            'MEDIUM': 'MEDIUM', 
            'LOW': 'LOW',
            # Legacy format mapping for database migration
            'High': 'HIGH',
            'Medium': 'MEDIUM',
            'Low': 'LOW'
        }
        
        if v in severity_mapping:
            return severity_mapping[v]
        elif v_upper in severity_mapping:
            return severity_mapping[v_upper]
        
        # If no mapping found, try the original validation
        try:
            SeverityEnum(v)
            return v
        except ValueError:
            print("==========================================")
            raise ValueError(f"Invalid severity value '{v}'. Use one of: {[s.value for s in SeverityEnum]} (case-insensitive)")

    @field_validator('abended_at_start_date')
    @classmethod
    def validate_start_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate start date format."""
        if v is None:
            return v
        try:
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError("Invalid start date format. Use YYYY-MM-DD format.")

    @field_validator('abended_at_end_date')
    @classmethod
    def validate_end_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate end date format."""
        if v is None:
            return v
        try:
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError("Invalid end date format. Use YYYY-MM-DD format.")

    @model_validator(mode='after')
    def validate_and_convert_dates(self) -> 'GetAbendsFilter':
        """Validate date logic, convert strings to date objects, and decode cursor."""
        # Convert start date or default to today
        if self.abended_at_start_date:
            self._parsed_start_date = date.fromisoformat(self.abended_at_start_date)
        else:
            # Default to today if no start date provided
            from datetime import datetime, timezone
            self._parsed_start_date = datetime.now(timezone.utc).date()
        
        # Convert end date if provided
        if self.abended_at_end_date:
            self._parsed_end_date = date.fromisoformat(self.abended_at_end_date)
            
            # Validate date range order
            if self._parsed_end_date < self._parsed_start_date:
                raise ValueError("End date cannot be before start date")
        else:
            # If no end date, single day search using start date
            self._parsed_end_date = self._parsed_start_date
        
        # Convert severity string to enum
        if self.severity:
            self._parsed_severity = SeverityEnum(self.severity)
        
        # Decode cursor for DynamoDB pagination
        if self.cursor:
            self._decoded_cursor = decode_cursor(self.cursor)
            # Note: decode_cursor already handles validation, but if it returns None,
            # the cursor was invalid and we'll proceed without pagination
        
        return self

    # Convenience properties to access converted values
    @property
    def parsed_severity(self) -> Optional[SeverityEnum]:
        """Get the parsed severity enum."""
        return self._parsed_severity
    
    @property
    def parsed_start_date(self) -> Optional[date]:
        """Get the parsed start date (defaults to today if not provided)."""
        return self._parsed_start_date
    
    @property
    def parsed_end_date(self) -> Optional[date]:
        """Get the parsed end date (equals start_date for single day searches)."""
        return self._parsed_end_date
    
    @property
    def is_single_day(self) -> bool:
        """Check if this is a single day search."""
        return self._parsed_start_date == self._parsed_end_date
    
    @property
    def is_date_range(self) -> bool:
        """Check if this is a date range search."""
        return self._parsed_start_date != self._parsed_end_date
    
    @property
    def decoded_cursor(self) -> Optional[Dict[str, Any]]:
        """Get the decoded cursor for DynamoDB pagination."""
        return self._decoded_cursor


class AIRecommendationApprovalRequest(BaseModel):
    """Request model for AI recommendation approval."""
    approval_status: AIRemediationApprovalStatusEnum = Field(..., alias="approvalStatus")
    comments: Optional[str] = Field(None, description="Approval comments")


# Response Models
class PaginationMeta(BaseModel):
    """Pagination metadata for cursor-based pagination."""
    total: int = Field(..., description="Total number of records (estimated for cursor-based pagination)")
    limit: int = Field(..., description="Records per page")
    has_next: bool = Field(..., alias="hasNext", description="Whether there are more records")
    has_previous: bool = Field(..., alias="hasPrevious", description="Whether there are previous records")
    next_cursor: Optional[str] = Field(None, alias="nextCursor", description="Cursor for next page")
    prev_cursor: Optional[str] = Field(None, alias="prevCursor", description="Cursor for previous page")


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
