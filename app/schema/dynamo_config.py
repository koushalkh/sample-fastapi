"""
DynamoDB configuration for PynamoDB models.
Centralizes connection settings for all DynamoDB tables.
"""

from typing import Any, Dict

from pynamodb.connection import Connection

from app.core.config import settings


class DynamoDBConfig:
    """Centralized DynamoDB configuration for all PynamoDB models."""

    @staticmethod
    def get_connection_kwargs() -> Dict[str, Any]:
        """Get connection configuration for PynamoDB models."""
        kwargs = {
            "region": settings.aws_region,
        }

        # Use local DynamoDB if endpoint is configured
        if settings.dynamodb_endpoint_url:
            kwargs.update(
                {
                    "host": settings.dynamodb_endpoint_url,
                    "aws_access_key_id": "dummy",
                    "aws_secret_access_key": "dummy",
                }
            )

        return kwargs

    @staticmethod
    def get_table_name_prefix() -> str:
        """Get table name prefix based on environment."""
        app_name = settings.APP_NAME
        # Remove dev-specific naming, use consistent naming
        return f"{app_name}-"

    @staticmethod
    def create_connection() -> Connection:
        """Create a PynamoDB connection with proper configuration."""
        return Connection(**DynamoDBConfig.get_connection_kwargs())


# Global connection instance
dynamo_connection = DynamoDBConfig.create_connection()
