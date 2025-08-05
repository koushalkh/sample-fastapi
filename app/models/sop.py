from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SOPModel(BaseModel):
    """Simplified SOP model for UI table display and listing."""
    sop_id: str = Field(..., alias="sopID", description="Unique SOP identifier")
    sop_name: str = Field(..., alias="sopName", description="Name of the SOP")
    job_name: str = Field(..., alias="jobName", description="Associated job name")
    abend_type: str = Field(..., alias="abendType", description="Type of abend this SOP addresses")
    created_at: datetime = Field(..., alias="createdAt", description="SOP creation timestamp")
    updated_at: datetime = Field(..., alias="updatedAt", description="SOP last update timestamp")
    created_by: str = Field(..., alias="createdBy", description="Who created this SOP")


class SOPDetailsModel(BaseModel):
    """Complete SOP model with all details."""
    # Basic fields (from SOPModel)
    sop_id: str = Field(..., alias="sopID", description="Unique SOP identifier")
    sop_name: str = Field(..., alias="sopName", description="Name of the SOP")
    job_name: str = Field(..., alias="jobName", description="Associated job name")
    abend_type: str = Field(..., alias="abendType", description="Type of abend this SOP addresses")
    
    # Document URLs (S3 references)
    source_document_url: str = Field(..., alias="sourceDocumentUrl", description="S3 URL of the original SOP document")
    processed_document_urls: List[str] = Field(default=[], alias="processedDocumentUrls", description="S3 URLs of processed document versions")
    
    # Audit fields
    created_at: datetime = Field(..., alias="createdAt", description="SOP creation timestamp")
    updated_at: datetime = Field(..., alias="updatedAt", description="SOP last update timestamp")
    created_by: str = Field(default="system", alias="createdBy", description="Who created this SOP")
    updated_by: str = Field(default="system", alias="updatedBy", description="Who last updated this SOP")
    generation: int = Field(default=1, description="Version number for optimistic locking")


# Request Models
class CreateSOPRequest(BaseModel):
    """Request model for creating a new SOP record via internal API."""
    sop_name: str = Field(..., alias="sopName", description="Name of the SOP", min_length=1, max_length=255)
    job_name: str = Field(..., alias="jobName", description="Associated job name", min_length=1, max_length=255)
    abend_type: str = Field(..., alias="abendType", description="Type of abend this SOP addresses", min_length=1, max_length=100)
    source_document_url: str = Field(..., alias="sourceDocumentUrl", description="S3 URL of the original SOP document")
    processed_document_urls: Optional[List[str]] = Field(None, alias="processedDocumentUrls", description="S3 URLs of processed document versions")
    created_by: Optional[str] = Field(None, alias="createdBy", description="Who is creating this SOP", max_length=255)


class UpdateSOPRequest(BaseModel):
    """Request model for updating an existing SOP record."""
    sop_name: Optional[str] = Field(None, alias="sopName", description="Name of the SOP", min_length=1, max_length=255)
    job_name: Optional[str] = Field(None, alias="jobName", description="Associated job name", min_length=1, max_length=255)
    abend_type: Optional[str] = Field(None, alias="abendType", description="Type of abend this SOP addresses", min_length=1, max_length=100)
    source_document_url: Optional[str] = Field(None, alias="sourceDocumentUrl", description="S3 URL of the original SOP document")
    processed_document_urls: Optional[List[str]] = Field(None, alias="processedDocumentUrls", description="S3 URLs of processed document versions")
    updated_by: Optional[str] = Field(None, alias="updatedBy", description="Who is updating this SOP", max_length=255)


class GetSOPsFilter(BaseModel):
    """Filter model for getting SOP records with pagination."""
    job_name: Optional[str] = Field(None, alias="jobName", description="Filter by job name")
    abend_type: Optional[str] = Field(None, alias="abendType", description="Filter by abend type")
    search: Optional[str] = Field(None, description="Search term for SOP name")
    limit: int = Field(default=20, description="Number of records to return (max 100)", le=100, ge=1)
    cursor: Optional[str] = Field(None, description="Pagination cursor for next page")
    
    # Computed properties (set by validator)
    _decoded_cursor: Optional[dict[str, str]] = None
    
    @property
    def decoded_cursor(self) -> Optional[dict[str, str]]:
        """Get the decoded cursor for DynamoDB pagination."""
        return self._decoded_cursor


# Response Models
class PaginationMeta(BaseModel):
    """Pagination metadata for cursor-based pagination."""
    total: int = Field(..., description="Estimated total number of records")
    limit: int = Field(..., description="Number of records requested")
    has_next: bool = Field(..., alias="hasNext", description="Whether there are more records")
    has_previous: bool = Field(..., alias="hasPrevious", description="Whether there are previous records")
    next_cursor: Optional[str] = Field(None, alias="nextCursor", description="Cursor for next page")
    prev_cursor: Optional[str] = Field(None, alias="prevCursor", description="Cursor for previous page")


class GetSOPsResponse(BaseModel):
    """Response model for getting SOP records."""
    data: List[SOPModel] = Field(..., description="List of SOP records")
    meta: PaginationMeta = Field(..., description="Pagination metadata")


class SOPDetailsResponse(BaseModel):
    """Response model for SOP details."""
    data: SOPDetailsModel = Field(..., description="Complete SOP details")


class CreateSOPResponse(BaseModel):
    """Response model for SOP creation."""
    sop_id: str = Field(..., alias="sopID", description="Generated SOP ID")
    sop_name: str = Field(..., alias="sopName", description="SOP name")
    job_name: str = Field(..., alias="jobName", description="Associated job name")
    abend_type: str = Field(..., alias="abendType", description="Abend type")
    created_at: datetime = Field(..., alias="createdAt", description="Record creation timestamp")
    message: str = Field(..., description="Success message")


class UpdateSOPResponse(BaseModel):
    """Response model for SOP update."""
    sop_id: str = Field(..., alias="sopID", description="SOP ID")
    updated_at: datetime = Field(..., alias="updatedAt", description="Record update timestamp")
    generation: int = Field(..., description="New version number")
    message: str = Field(..., description="Success message")


# Legacy models for backward compatibility
class SOPItem(BaseModel):
    """Legacy SOP item model - kept for backward compatibility."""
    id: str
    name: str
    description: str


class SOPDetail(BaseModel):
    """Legacy SOP detail model - kept for backward compatibility."""
    id: str
    name: str
    description: str
    version: str
    content: str
    last_updated: str
