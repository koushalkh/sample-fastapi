"""
SOP DynamoDB Schema for High-Volume Data

This schema follows the same optimization patterns as the ABEND schema:
1. Strategic GSI design for common query patterns
2. Extensible primary key design (sop_id + record_type)
3. Complete DynamoDB native filtering
4. S3 URL storage for document references
5. Full audit trail support

Key Features:
- Primary key: sop_id (hash) + record_type (range) for extensibility
- JobNameIndex: Query SOPs by job name + creation date
- AbendTypeIndex: Query SOPs by abend type + creation date
- Audit fields for complete change tracking
- S3 URLs for document storage references
"""

from datetime import datetime, timezone
from typing import Any, Dict

import ulid
from pynamodb.attributes import (
    ListAttribute,
    NumberAttribute,
    UnicodeAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.indexes import AllProjection, GlobalSecondaryIndex
from pynamodb.models import Model

from app.schema.dynamo_config import DynamoDBConfig


class JobNameIndex(GlobalSecondaryIndex):
    """
    GSI for querying SOPs by job name with date-based sorting.

    Optimized for:
    - Finding all SOPs for a specific job
    - Date-range queries for job-specific SOPs
    - Time-based sorting within job context

    Key Design:
    - Hash Key: job_name (partition by job)
    - Range Key: created_at (timestamp for sorting)
    """

    class Meta:
        index_name = "JobNameIndex"
        projection = AllProjection()
        read_capacity_units = 2
        write_capacity_units = 2

    # Hash key: Job name for partition isolation
    job_name = UnicodeAttribute(hash_key=True)

    # Range key: Creation timestamp for precise sorting
    created_at = UTCDateTimeAttribute(range_key=True)


class AbendTypeIndex(GlobalSecondaryIndex):
    """
    GSI for querying SOPs by abend type with date-based sorting.

    Optimized for:
    - Finding all SOPs for a specific abend type
    - Date-range queries for abend-type-specific SOPs
    - Time-based sorting within abend type context

    Key Design:
    - Hash Key: abend_type (partition by type)
    - Range Key: created_at (timestamp for sorting)
    """

    class Meta:
        index_name = "AbendTypeIndex"
        projection = AllProjection()
        read_capacity_units = 2
        write_capacity_units = 2

    # Hash key: Abend type for partition isolation
    abend_type = UnicodeAttribute(hash_key=True)

    # Range key: Creation timestamp for precise sorting
    created_at = UTCDateTimeAttribute(range_key=True)


class SOPDynamoTable(Model):
    """
    SOP record schema with strategic GSI design.

    This schema is optimized for:
    1. Job-specific SOP queries via JobNameIndex
    2. Abend-type-specific SOP queries via AbendTypeIndex
    3. Complete DynamoDB native filtering
    4. Extensible design for future record types
    5. Full audit trail support

    Primary Key Design:
    - Hash: sop_id (unique identifier)
    - Range: record_type (extensibility for future record types)
    """

    class Meta:
        table_name = f"{DynamoDBConfig.get_table_name_prefix()}sop-records"
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

    # Primary Key
    sop_id = UnicodeAttribute(hash_key=True, attr_name="sopID")
    record_type = UnicodeAttribute(range_key=True, default="SOP")

    # Basic SOP information
    sop_name = UnicodeAttribute(attr_name="sopName")
    job_name = UnicodeAttribute(attr_name="jobName")
    abend_type = UnicodeAttribute(attr_name="abendType")

    # Document URLs (S3 references)
    source_document_url = UnicodeAttribute(attr_name="sourceDocumentUrl")
    processed_document_urls = ListAttribute(
        of=UnicodeAttribute, attr_name="processedDocumentUrls", default=list
    )

    # Audit fields
    created_at = UTCDateTimeAttribute(
        default=lambda: datetime.now(timezone.utc), attr_name="createdAt"
    )
    updated_at = UTCDateTimeAttribute(
        default=lambda: datetime.now(timezone.utc), attr_name="updatedAt"
    )
    created_by = UnicodeAttribute(attr_name="createdBy", default="system")
    updated_by = UnicodeAttribute(attr_name="updatedBy", default="system")
    generation = NumberAttribute(attr_name="generation", default=1)

    # GSI Definitions
    job_name_index = JobNameIndex()
    abend_type_index = AbendTypeIndex()

    def save(self, **kwargs: Any) -> Any:
        """Override save to auto-populate timestamps and derived fields."""
        now = datetime.now(timezone.utc)

        # Set timestamps
        self.updated_at = now
        if not hasattr(self, "_created_at_set"):
            self.created_at = now
            self._created_at_set = True

        # Set default record type
        if not self.record_type:
            self.record_type = "SOP"

        return super().save(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary for API responses."""
        result = {
            "sop_id": self.sop_id,
            "record_type": self.record_type,
            "sop_name": self.sop_name,
            "job_name": self.job_name,
            "abend_type": self.abend_type,
            "source_document_url": self.source_document_url,
            "processed_document_urls": (
                list(self.processed_document_urls)
                if self.processed_document_urls
                else []
            ),
            # Audit fields
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "generation": self.generation,
            # Timestamps
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SOPDynamoTable":
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
        return f"SOPDynamoTable(sop_id={self.sop_id}, sop_name={self.sop_name}, job_name={self.job_name})"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"SOPDynamoTable("
            f"sop_id={self.sop_id}, "
            f"record_type={self.record_type}, "
            f"sop_name={self.sop_name}, "
            f"job_name={self.job_name}, "
            f"abend_type={self.abend_type})"
        )

    @classmethod
    def generate_sop_id(cls) -> str:
        """
        Generate SOP ID using the format: SOP_{ulid}

        Returns:
            Formatted SOP ID with auto-generated ULID
        """
        return f"SOP_{ulid.ulid()}"

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
            datetime object with UTC timezone
        """
        return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
