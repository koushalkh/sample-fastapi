"""
ABEND (Abnormal End Records) DynamoDB table schema using PynamoDB.
Based on Terraform configuration for adr-abend-dynamodb table.
"""

from datetime import datetime, timezone
from typing import Any, Dict
import ulid

from pynamodb.attributes import (
    JSONAttribute,
    NumberAttribute,
    UnicodeAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.indexes import AllProjection, GlobalSecondaryIndex
from pynamodb.models import Model

from app.schema.dynamo_config import DynamoDBConfig


class AbendTypeIndex(GlobalSecondaryIndex):
    """Global Secondary Index for querying by abend type."""

    class Meta:
        index_name = "AbendTypeIndex"
        projection = AllProjection()
        read_capacity_units = 2
        write_capacity_units = 2

    abend_type = UnicodeAttribute(hash_key=True)
    abended_at = UnicodeAttribute(range_key=True)  # Keep as string for GSI sorting


class JobNameIndex(GlobalSecondaryIndex):
    """Global Secondary Index for querying by job name."""

    class Meta:
        index_name = "JobNameIndex"
        projection = AllProjection()
        read_capacity_units = 2
        write_capacity_units = 2

    job_name = UnicodeAttribute(hash_key=True)
    abended_at = UnicodeAttribute(range_key=True)  # Keep as string for GSI sorting


class DomainAreaIndex(GlobalSecondaryIndex):
    """Global Secondary Index for querying by domain area."""

    class Meta:
        index_name = "DomainAreaIndex"
        projection = AllProjection()
        read_capacity_units = 2
        write_capacity_units = 2

    domain_area = UnicodeAttribute(hash_key=True)
    abended_at = UnicodeAttribute(range_key=True)  # Keep as string for GSI sorting


class ADRStatusIndex(GlobalSecondaryIndex):
    """Global Secondary Index for querying by ADR status."""

    class Meta:
        index_name = "ADRStatusIndex"
        projection = AllProjection()
        read_capacity_units = 2
        write_capacity_units = 2

    adr_status = UnicodeAttribute(hash_key=True)
    abended_at = UnicodeAttribute(range_key=True)  # Keep as string for GSI sorting


class SeverityIndex(GlobalSecondaryIndex):
    """Global Secondary Index for querying by severity level."""

    class Meta:
        index_name = "SeverityIndex"
        projection = AllProjection()
        read_capacity_units = 2
        write_capacity_units = 2

    severity = UnicodeAttribute(hash_key=True)
    abended_at = UnicodeAttribute(range_key=True)  # Keep as string for GSI sorting


class AbendDynamoTable(Model):
    """
    ABEND (Abnormal End Records) DynamoDB table model.

    Primary Key:
    - tracking_id (hash key): Unique identifier for the ABEND record
    - abended_at (range key): UTC datetime when the abend occurred

    Global Secondary Indexes:
    - AbendTypeIndex: Query by abend_type + abended_at (as ISO string)
    - JobNameIndex: Query by job_name + abended_at (as ISO string)
    - DomainAreaIndex: Query by domain_area + abended_at (as ISO string)
    - ADRStatusIndex: Query by adr_status + abended_at (as ISO string)
    - SeverityIndex: Query by severity + abended_at (as ISO string)
    
    Note: The abended_at field is stored as UTCDateTimeAttribute in the main table
    but converted to ISO 8601 string format for GSI range key queries.
    Use the helper methods datetime_to_iso_string() and iso_string_to_datetime()
    for conversion between formats when querying GSIs.
    """

    class Meta:
        table_name = f"{DynamoDBConfig.get_table_name_prefix()}abend-records"
        region = DynamoDBConfig.get_connection_kwargs()["region"]
        stream_view_type = "NEW_AND_OLD_IMAGES"

        # Apply connection configuration
        if "host" in DynamoDBConfig.get_connection_kwargs():
            host = DynamoDBConfig.get_connection_kwargs()["host"]
            aws_access_key_id = DynamoDBConfig.get_connection_kwargs()[
                "aws_access_key_id"
            ]
            aws_secret_access_key = DynamoDBConfig.get_connection_kwargs()[
                "aws_secret_access_key"
            ]

    # Primary Key
    tracking_id = UnicodeAttribute(hash_key=True, attr_name="trackingID")
    abended_at = UTCDateTimeAttribute(range_key=True, attr_name="abendedAt")

    # Basic job information
    job_id = UnicodeAttribute(attr_name="jobID")
    job_name = UnicodeAttribute(attr_name="jobName", null=True)
    order_id = UnicodeAttribute(attr_name="orderID", null=True)
    incident_number = UnicodeAttribute(attr_name="incidentNumber", null=True)
    fa_id = UnicodeAttribute(attr_name="faID", null=True)
    domain_area = UnicodeAttribute(attr_name="domainArea", null=True)

    # ABEND specific information
    abend_type = UnicodeAttribute(attr_name="abendType", null=True)
    abend_step = UnicodeAttribute(attr_name="abendStep", null=True)
    abend_return_code = UnicodeAttribute(attr_name="abendReturnCode", null=True)
    abend_reason = UnicodeAttribute(attr_name="abendReason", null=True)
    
    # Status and severity (used for GSI)
    adr_status = UnicodeAttribute(attr_name="adrStatus")
    severity = UnicodeAttribute(attr_name="severity")

    # Performance metrics (flattened)
    perf_log_extraction_time = UnicodeAttribute(attr_name="perfLogExtractionTime", null=True)
    perf_ai_analysis_time = UnicodeAttribute(attr_name="perfAiAnalysisTime", null=True)
    perf_remediation_time = UnicodeAttribute(attr_name="perfRemediationTime", null=True)
    perf_total_automated_time = UnicodeAttribute(attr_name="perfTotalAutomatedTime", null=True)

    # Log extraction metadata (flattened)
    log_extraction_run_id = UnicodeAttribute(attr_name="logExtractionRunId", null=True)
    log_extraction_retries = NumberAttribute(attr_name="logExtractionRetries", default=0)

    # Complex nested objects stored as JSON
    email_metadata = JSONAttribute(attr_name="emailMetadata", null=True)
    knowledge_base_metadata = JSONAttribute(attr_name="knowledgeBaseMetadata", null=True)
    remediation_metadata = JSONAttribute(attr_name="remediationMetadata", null=True)

    # Audit fields
    created_by = UnicodeAttribute(attr_name="createdBy", default="system")
    updated_by = UnicodeAttribute(attr_name="updatedBy", default="system")
    generation = NumberAttribute(attr_name="generation", default=1)

    # Global Secondary Indexes
    abend_type_index = AbendTypeIndex()
    job_name_index = JobNameIndex()
    domain_area_index = DomainAreaIndex()
    adr_status_index = ADRStatusIndex()
    severity_index = SeverityIndex()

    # Timestamp fields
    created_at = UTCDateTimeAttribute(
        default=lambda: datetime.now(timezone.utc), attr_name="createdAt"
    )
    updated_at = UTCDateTimeAttribute(
        default=lambda: datetime.now(timezone.utc), attr_name="updatedAt"
    )

    def save(self, condition: Any = None, **kwargs: Any) -> Dict[str, Any]:
        """Override save to update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)
        return super().save(condition=condition, **kwargs)

    @property
    def abended_at_iso(self) -> str:
        """
        Get the abended_at datetime as ISO 8601 string for GSI queries.
        
        Returns:
            ISO 8601 formatted datetime string (YYYY-MM-DDTHH:MM:SS.fffffZ)
        """
        if self.abended_at:
            return self.abended_at.isoformat()
        return ""
    
    @classmethod
    def datetime_to_iso_string(cls, dt: datetime) -> str:
        """
        Convert datetime to ISO 8601 string format for GSI queries.
        
        Args:
            dt: datetime object to convert
            
        Returns:
            ISO 8601 formatted datetime string
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    
    @classmethod
    def iso_string_to_datetime(cls, iso_string: str) -> datetime:
        """
        Convert ISO 8601 string to datetime object.
        
        Args:
            iso_string: ISO 8601 formatted datetime string
            
        Returns:
            datetime object
        """
        return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    
    @classmethod
    def generate_tracking_id(cls, job_name: str) -> str:
        """
        Generate tracking ID using the format: ABEND_{jobname}_{ulid}
        
        Args:
            job_name: Name of the job that abended
            
        Returns:
            Formatted tracking ID with auto-generated ULID
            
        Example:
            >>> AbendDynamoTable.generate_tracking_id("WGMP110D")
            "ABEND_WGMP110D_01ARZ3NDEKTSV4RRFFQ69G5FAV"
        """
        return f"ABEND_{job_name}_{ulid.ulid()}"
    
    def set_email_metadata(self, email_data: Dict[str, Any]) -> None:
        """
        Set email metadata from dictionary.
        
        Args:
            email_data: Dictionary containing email metadata
        """
        self.email_metadata = email_data
    
    def set_knowledge_base_metadata(self, kb_data: Dict[str, Any]) -> None:
        """
        Set knowledge base metadata from dictionary.
        
        Args:
            kb_data: Dictionary containing knowledge base metadata
        """
        self.knowledge_base_metadata = kb_data
    
    def set_remediation_metadata(self, remediation_data: Dict[str, Any]) -> None:
        """
        Set remediation metadata from dictionary.
        
        Args:
            remediation_data: Dictionary containing remediation metadata
        """
        self.remediation_metadata = remediation_data
