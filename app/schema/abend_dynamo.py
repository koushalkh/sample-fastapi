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
    abended_at = UnicodeAttribute(range_key=True)


class JobNameIndex(GlobalSecondaryIndex):
    """Global Secondary Index for querying by job name."""

    class Meta:
        index_name = "JobNameIndex"
        projection = AllProjection()

    job_name = UnicodeAttribute(hash_key=True)
    abended_at = UnicodeAttribute(range_key=True)


class DomainAreaIndex(GlobalSecondaryIndex):
    """Global Secondary Index for querying by domain area."""

    class Meta:
        index_name = "DomainAreaIndex"
        projection = AllProjection()

    domain_area = UnicodeAttribute(hash_key=True)
    abended_at = UnicodeAttribute(range_key=True)


class AbendActionStatusIndex(GlobalSecondaryIndex):
    """Global Secondary Index for querying by abend action status."""

    class Meta:
        index_name = "AbendActionStatusIndex"
        projection = AllProjection()

    abend_action_status = UnicodeAttribute(hash_key=True)
    abended_at = UnicodeAttribute(range_key=True)


class AbendDynamoTable(Model):
    """
    ABEND (Abnormal End Records) DynamoDB table model.

    Primary Key:
    - tracking_id (hash key): Unique identifier for the ABEND record
    - abended_at (range key): Timestamp when the abend occurred

    Global Secondary Indexes:
    - AbendTypeIndex: Query by abend_type + abended_at
    - JobNameIndex: Query by job_name + abended_at
    - DomainAreaIndex: Query by domain_area + abended_at
    - AbendActionStatusIndex: Query by abend_action_status + abended_at
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
    abended_at = UnicodeAttribute(range_key=True, attr_name="abendedAt")

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
