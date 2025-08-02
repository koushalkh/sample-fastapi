"""
ABEND (Abnormal End Records) DynamoDB table schema using PynamoDB.
Based on Terraform configuration for adr-abend-dynamodb table.
"""

from datetime import datetime, timezone
from typing import Any, Dict

from pynamodb.attributes import (
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

    abend_type = UnicodeAttribute(hash_key=True)
    abended_at = UnicodeAttribute(range_key=True)  # Keep as string for GSI sorting


class JobNameIndex(GlobalSecondaryIndex):
    """Global Secondary Index for querying by job name."""

    class Meta:
        index_name = "JobNameIndex"
        projection = AllProjection()

    job_name = UnicodeAttribute(hash_key=True)
    abended_at = UnicodeAttribute(range_key=True)  # Keep as string for GSI sorting


class DomainAreaIndex(GlobalSecondaryIndex):
    """Global Secondary Index for querying by domain area."""

    class Meta:
        index_name = "DomainAreaIndex"
        projection = AllProjection()

    domain_area = UnicodeAttribute(hash_key=True)
    abended_at = UnicodeAttribute(range_key=True)  # Keep as string for GSI sorting


class AbendActionStatusIndex(GlobalSecondaryIndex):
    """Global Secondary Index for querying by abend action status."""

    class Meta:
        index_name = "AbendActionStatusIndex"
        projection = AllProjection()

    abend_action_status = UnicodeAttribute(hash_key=True)
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
    - AbendActionStatusIndex: Query by abend_action_status + abended_at (as ISO string)
    
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

    # Attributes for Global Secondary Indexes
    abend_type = UnicodeAttribute(attr_name="abendType", null=True)
    job_name = UnicodeAttribute(attr_name="jobName", null=True)
    domain_area = UnicodeAttribute(attr_name="domainArea", null=True)
    abend_action_status = UnicodeAttribute(attr_name="abendActionStatus", null=True)

    # Global Secondary Indexes
    abend_type_index = AbendTypeIndex()
    job_name_index = JobNameIndex()
    domain_area_index = DomainAreaIndex()
    abend_action_status_index = AbendActionStatusIndex()

    # Additional fields (to be expanded later)
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
