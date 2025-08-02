from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


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
    ai_remediation_approval_status: Optional[str] = Field(None, alias="aiRemediationApprovalStatus")
    ai_remediation_approval_required: bool = Field(False, alias="aiRemediationApprovalRequired")
    ai_remediation_comments: Optional[str] = Field(None, alias="aiRemediationComments")


class AbendModel(BaseModel):
    """Basic ABEND model for table display and listing."""
    tracking_id: str = Field(..., alias="trackingID")
    job_id: str = Field(..., alias="jobID")
    job_name: str = Field(..., alias="jobName")
    abended_at: datetime = Field(..., alias="abendedAt")
    adr_status: ADRStatusEnum = Field(..., alias="adrStatus")
    severity: SeverityEnum
    domain_area: Optional[str] = Field(None, alias="domainArea")
    incident_number: Optional[str] = Field(None, alias="incidentNumber")
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


# Legacy models for backwards compatibility
class AbendItem(BaseModel):
    abendId: str
    name: str


class AbendDetail(BaseModel):
    abendId: str
    name: str
    severity: str
    description: str
