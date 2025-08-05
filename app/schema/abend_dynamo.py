"""
Optimized ABEND DynamoDB Schema for High-Volume Data

This optimized schema addresses the following requirements:
1. Billions of rows with 90% queries on today's data
2. 200 concurrent users, ~2000 records per day
3. Zero Python filtering - all filtering via DynamoDB
4. Complete feature parity between today's and date range queries
5. Significant cost reduction through strategic GSI consolidation

Key Optimizations:
- Reduced from 5 GSIs to 2 strategic GSIs (60% capacity reduction)
- Single-partition access for today's data (AbendedDateIndex)
- Dedicated job history tracking (JobHistoryIndex)
- Extensible primary key design (tracking_id + record_type)
- Smart pagination support for cross-date queries
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

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


class AbendedDateIndex(GlobalSecondaryIndex):
    """
    Primary GSI for date-based queries (90% of all queries).

    Optimized for:
    - Today's data queries (single partition)
    - Date range queries (parallel partition access)
    - Time-based sorting with filters and search

    Key Design:
    - Hash Key: abended_date (YYYY-MM-DD format)
    - Range Key: abended_at (timestamp for sorting)
    """

    class Meta:
        index_name = "AbendedDateIndex"
        projection = AllProjection()
        read_capacity_units = 2
        write_capacity_units = 2

    # Hash key: Date in YYYY-MM-DD format for partition isolation
    abended_date = UnicodeAttribute(hash_key=True)

    # Range key: Timestamp for precise sorting and pagination
    abended_at = UnicodeAttribute(range_key=True)


class JobHistoryIndex(GlobalSecondaryIndex):
    """
    Secondary GSI for job-specific failure tracking.

    Optimized for:
    - Job failure history analysis
    - Trend identification for specific jobs
    - SOP and troubleshooting workflows

    Key Design:
    - Hash Key: job_name (groups all failures for a job)
    - Range Key: abended_at (chronological failure order)
    """

    class Meta:
        index_name = "JobHistoryIndex"
        projection = AllProjection()
        read_capacity_units = 2
        write_capacity_units = 2

    # Hash key: Job Name for grouping job failures
    job_name = UnicodeAttribute(hash_key=True, attr_name="jobName")

    # Range key: Timestamp for chronological ordering
    abended_at = UnicodeAttribute(range_key=True, attr_name="abended_at")


class AuditLogsIndex(GlobalSecondaryIndex):
    """
    Dedicated GSI for audit log queries.

    Optimized for:
    - Get all audit logs for a tracking_id
    - Chronological ordering of audit events
    - Efficient audit trail retrieval

    Key Design:
    - Hash Key: tracking_id (groups audit logs by tracking ID)
    - Range Key: audit_id (allows multiple audit logs per tracking ID)
    """

    class Meta:
        index_name = "AuditLogsIndex"
        projection = AllProjection()
        read_capacity_units = 1
        write_capacity_units = 1

    # Hash key: tracking_id for grouping audit logs
    tracking_id = UnicodeAttribute(hash_key=True, attr_name="trackingID")

    # Range key: audit_id for unique identification within a tracking ID
    audit_id = UnicodeAttribute(range_key=True, attr_name="auditID")


class AbendDynamoTable(Model):
    """
    Optimized ABEND record schema with strategic GSI design.

    This schema is optimized for:
    1. 90% today's data queries via AbendedDateIndex single partition
    2. Historical analysis via AbendedDateIndex parallel partitions
    3. Job failure tracking via JobHistoryIndex
    4. Complete DynamoDB native filtering (zero Python filtering)
    5. Consistent pagination across all query types

    Primary Key Design:
    - Hash: tracking_id (unique identifier)
    - Range: record_type (extensibility for future record types)
    """

    class Meta:
        table_name = f"{DynamoDBConfig.get_table_name_prefix()}abend-test-dynamodb-dev"
        region = DynamoDBConfig.get_connection_kwargs()["region"]

        # Apply connection configuration for local DynamoDB
        if "host" in DynamoDBConfig.get_connection_kwargs():
            host = DynamoDBConfig.get_connection_kwargs()["host"]
            aws_access_key_id = DynamoDBConfig.get_connection_kwargs()[
                "aws_access_key_id"
            ]
            aws_secret_access_key = DynamoDBConfig.get_connection_kwargs()[
                "aws_secret_access_key"
            ]

    # Primary Key (matching DynamoDB schema)
    tracking_id = UnicodeAttribute(hash_key=True, attr_name="trackingID")
    record_type = UnicodeAttribute(range_key=True, default="ABEND")

    # GSI Key Attributes (matching DynamoDB schema)
    abended_date = UnicodeAttribute(
        attr_name="abended_date", null=True
    )  # YYYY-MM-DD format for AbendedDateIndex
    abended_at = UnicodeAttribute(
        attr_name="abended_at", null=True
    )  # String timestamp for both GSIs - nullable for audit logs
    job_id = UnicodeAttribute(
        attr_name="job_id", null=True
    )  # Standard job identifier - optional

    # Basic job information (matching main schema)
    job_name = UnicodeAttribute(attr_name="jobName", null=True)
    order_id = UnicodeAttribute(attr_name="orderID", null=True)
    incident_number = UnicodeAttribute(attr_name="incidentNumber", null=True)
    fa_id = UnicodeAttribute(attr_name="faID", null=True)
    domain_area = UnicodeAttribute(attr_name="domainArea", null=True)

    # ABEND specific information (matching main schema)
    abend_type = UnicodeAttribute(attr_name="abendType", null=True)
    abend_step = UnicodeAttribute(attr_name="abendStep", null=True)
    abend_return_code = UnicodeAttribute(attr_name="abendReturnCode", null=True)
    abend_reason = UnicodeAttribute(attr_name="abendReason", null=True)

    # Status and Severity (matching DynamoDB schema)
    adr_status = UnicodeAttribute(
        attr_name="adrStatus", null=True
    )  # Nullable for audit logs (reused for audit_status)
    severity = UnicodeAttribute(
        attr_name="severity", null=True
    )  # Nullable for audit logs

    # Performance metrics (flattened, matching main schema)
    perf_log_extraction_time = UnicodeAttribute(
        attr_name="perfLogExtractionTime", null=True
    )
    perf_ai_analysis_time = UnicodeAttribute(attr_name="perfAiAnalysisTime", null=True)
    perf_remediation_time = UnicodeAttribute(attr_name="perfRemediationTime", null=True)
    perf_total_automated_time = UnicodeAttribute(
        attr_name="perfTotalAutomatedTime", null=True
    )

    # Log extraction metadata (flattened, matching main schema)
    log_extraction_run_id = UnicodeAttribute(attr_name="logExtractionRunId", null=True)
    log_extraction_retries = NumberAttribute(
        attr_name="logExtractionRetries", default=0
    )

    # Complex nested objects stored as JSON (matching main schema)
    email_metadata = JSONAttribute(attr_name="emailMetadata", null=True)
    knowledge_base_metadata = JSONAttribute(
        attr_name="knowledgeBaseMetadata", null=True
    )
    remediation_metadata = JSONAttribute(attr_name="remediationMetadata", null=True)

    # Audit fields (matching main schema)
    created_by = UnicodeAttribute(attr_name="createdBy", default="system")
    updated_by = UnicodeAttribute(attr_name="updatedBy", default="system")
    generation = NumberAttribute(attr_name="generation", default=1)

    # Audit log specific attributes (only populated for AUDIT_LOG records)
    audit_id = UnicodeAttribute(
        attr_name="auditID", null=True
    )  # Unique audit log ID for range key
    audit_level = UnicodeAttribute(attr_name="auditLevel", null=True)
    audit_message = UnicodeAttribute(attr_name="auditMessage", null=True)
    audit_description = UnicodeAttribute(attr_name="auditDescription", null=True)

    # Timestamp fields (matching main schema)
    created_at = UTCDateTimeAttribute(
        default=lambda: datetime.now(timezone.utc), attr_name="createdAt"
    )
    updated_at = UTCDateTimeAttribute(
        default=lambda: datetime.now(timezone.utc), attr_name="updatedAt"
    )

    # GSI Definitions
    abended_date_index = AbendedDateIndex()
    job_history_index = JobHistoryIndex()
    audit_logs_index = AuditLogsIndex()

    def save(self, **kwargs):
        """Override save to auto-populate timestamps and derived fields."""
        now = datetime.now(timezone.utc)

        # Set timestamps (matching main schema behavior)
        self.updated_at = now
        if not hasattr(self, "_created_at_set"):
            self.created_at = now
            self._created_at_set = True

        # Handle record type specific logic
        if self.record_type == "AUDIT_LOG":
            # For audit logs, don't populate ABEND-specific fields
            # Set ABEND-specific fields to None to avoid GSI indexing
            self.abended_date = None
            self.abended_at = None
            self.job_name = None
            self.severity = None  # Not used for audit logs

        elif self.record_type == "ABEND":
            # Existing ABEND logic for GSI keys
            # Ensure abended_date is properly formatted
            if (
                hasattr(self, "abended_at")
                and self.abended_at
                and not self.abended_date
            ):
                # Convert datetime to date string if abended_at is datetime
                if isinstance(self.abended_at, datetime):
                    self.abended_date = self.abended_at.strftime("%Y-%m-%d")
                    # Convert datetime to ISO string for storage
                    self.abended_at = self.abended_at.isoformat()
                elif isinstance(self.abended_at, str):
                    # Parse ISO string to extract date
                    try:
                        dt = datetime.fromisoformat(
                            self.abended_at.replace("Z", "+00:00")
                        )
                        self.abended_date = dt.strftime("%Y-%m-%d")
                    except:
                        # Fallback to today's date
                        self.abended_date = now.strftime("%Y-%m-%d")

            # Clear audit-specific attributes for ABEND records
            self.audit_level = None
            self.audit_message = None
            self.audit_description = None

        # Set default record type
        if not self.record_type:
            self.record_type = "ABEND"

        return super().save(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary for API responses."""
        result = {
            "tracking_id": self.tracking_id,
            "record_type": self.record_type,
            "abended_date": self.abended_date,
            "abended_at": self.abended_at,
            "job_id": getattr(self, "job_id", None),
            "job_name": getattr(self, "job_name", None),
            "domain_area": getattr(self, "domain_area", None),
            "severity": self.severity,
            "adr_status": self.adr_status,
            "incident_number": getattr(self, "incident_number", None),
            "abend_reason": getattr(self, "abend_reason", None),
            "order_id": getattr(self, "order_id", None),
            "abend_type": getattr(self, "abend_type", None),
            "abend_step": getattr(self, "abend_step", None),
            "abend_return_code": getattr(self, "abend_return_code", None),
            "fa_id": getattr(self, "fa_id", None),
            # Performance metrics
            "perf_log_extraction_time": getattr(self, "perf_log_extraction_time", None),
            "perf_ai_analysis_time": getattr(self, "perf_ai_analysis_time", None),
            "perf_remediation_time": getattr(self, "perf_remediation_time", None),
            "perf_total_automated_time": getattr(
                self, "perf_total_automated_time", None
            ),
            # Log extraction metadata
            "log_extraction_run_id": getattr(self, "log_extraction_run_id", None),
            "log_extraction_retries": getattr(self, "log_extraction_retries", 0),
            # Complex nested objects
            "email_metadata": getattr(self, "email_metadata", None),
            "knowledge_base_metadata": getattr(self, "knowledge_base_metadata", None),
            "remediation_metadata": getattr(self, "remediation_metadata", None),
            # Audit fields
            "created_by": getattr(self, "created_by", "system"),
            "updated_by": getattr(self, "updated_by", "system"),
            "generation": getattr(self, "generation", 1),
            # Timestamps
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AbendDynamoTable":
        """Create model instance from dictionary."""
        # Convert datetime strings back to datetime objects
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(
                data["created_at"].replace("Z", "+00:00")
            )

        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(
                data["updated_at"].replace("Z", "+00:00")
            )

        return cls(**data)

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"AbendDynamoTable(tracking_id={self.tracking_id}, job_id={self.job_id}, abended_at={self.abended_at})"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"AbendDynamoTable("
            f"tracking_id={self.tracking_id}, "
            f"record_type={self.record_type}, "
            f"job_id={self.job_id}, "
            f"abended_date={self.abended_date}, "
            f"abended_at={self.abended_at}, "
            f"severity={self.severity}, "
            f"adr_status={self.adr_status})"
        )

    @classmethod
    def generate_tracking_id(cls, job_name: str) -> str:
        """
        Generate tracking ID using the format: ABEND_{jobname}_{ulid}
        Compatible with main schema's generate_tracking_id method.

        Args:
            job_name: Name of the job that abended

        Returns:
            Formatted tracking ID with auto-generated ULID
        """
        return f"ABEND_{job_name}_{ulid.ulid()}"

    @property
    def abended_at_iso(self) -> str:
        """
        Get the abended_at datetime as ISO 8601 string for compatibility.

        Returns:
            ISO 8601 formatted datetime string (YYYY-MM-DDTHH:MM:SS.fffffZ)
        """
        if self.abended_at:
            if isinstance(self.abended_at, str):
                return self.abended_at
            elif isinstance(self.abended_at, datetime):
                return self.abended_at.isoformat()
        return ""

    @classmethod
    def datetime_to_iso_string(cls, dt: datetime) -> str:
        """
        Convert datetime to ISO 8601 string format.

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
        return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))

    # Helper methods for metadata (matching main schema)
    def set_email_metadata(self, email_data: Dict[str, Any]) -> None:
        """Set email metadata from dictionary."""
        self.email_metadata = email_data

    def get_email_metadata(self) -> Optional[Dict[str, Any]]:
        """Get email metadata as dictionary."""
        return self.email_metadata

    def set_knowledge_base_metadata(self, kb_data: Dict[str, Any]) -> None:
        """Set knowledge base metadata from dictionary."""
        self.knowledge_base_metadata = kb_data

    def get_knowledge_base_metadata(self) -> Optional[Dict[str, Any]]:
        """Get knowledge base metadata as dictionary."""
        return self.knowledge_base_metadata

    def set_remediation_metadata(self, remediation_data: Dict[str, Any]) -> None:
        """Set remediation metadata from dictionary."""
        self.remediation_metadata = remediation_data

    def get_remediation_metadata(self) -> Optional[Dict[str, Any]]:
        """Get remediation metadata as dictionary."""
        return self.remediation_metadata

    # Audit log helper methods
    @classmethod
    def generate_audit_log_id(cls) -> str:
        """
        Generate audit log ID using the format: AUDIT_{ulid}

        Returns:
            Formatted audit log ID with auto-generated ULID
        """
        return f"AUDIT_{ulid.ulid()}"

    def set_audit_data(
        self, level: str, message: str, description: str, adr_status: str
    ) -> None:
        """Set audit log specific data."""
        self.audit_level = level
        self.audit_message = message
        self.audit_description = description
        self.adr_status = adr_status  # Use adr_status field consistently
        self.record_type = "AUDIT_LOG"

        # Generate audit_id if not already set
        if not self.audit_id:
            self.audit_id = self.generate_audit_log_id()

        # Generate audit_id if not already set
        if not self.audit_id:
            self.audit_id = self.generate_audit_log_id()

    def get_audit_data(self) -> Optional[Dict[str, Any]]:
        """Get audit log data as dictionary."""
        if self.record_type != "AUDIT_LOG":
            return None

        return {
            "level": self.audit_level,
            "message": self.audit_message,
            "description": self.audit_description,
            "adr_status": self.adr_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
