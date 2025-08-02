import os
import sys
from typing import Any, Optional

import boto3
from botocore.config import Config
from structlog import get_logger

logger = get_logger()


class Settings:
    APP_NAME: str = "adr"
    APP_SERVICE_NAME: str = "adr-svc"

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.app_name = os.getenv("APP_NAME", "BAM")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"

        # AWS Configuration
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.aws_account_id = os.getenv("AWS_ACCOUNT_ID")

        # DynamoDB Configuration
        self.dynamodb_endpoint = os.getenv("DYNAMODB_ENDPOINT")

        # Initialize boto3 clients as None (lazy initialization)
        self._dynamodb_client: Optional[Any] = None
        self._dynamodb_resource: Optional[Any] = None

    @property
    def is_dev_env(self) -> bool:
        """
        Check if the application is running in a development environment locally or in Container.
        """
        pod_namespace = os.environ.get("POD_NAMESPACE")
        return bool(pod_namespace)

    @property
    def log_level(self) -> str:
        if self.is_dev_env:
            return "DEBUG"
        return "INFO"

    @property
    def port(self) -> int:
        return 8000

    # DynamoDB Configuration
    @property
    def dynamodb_endpoint_url(self) -> Optional[str]:
        """DynamoDB endpoint URL. Uses local endpoint if DYNAMODB_ENDPOINT is set."""
        return os.environ.get("DYNAMODB_ENDPOINT")

    @property
    def dynamodb_client(self) -> Any:
        """Get or create DynamoDB client instance"""
        if self._dynamodb_client is not None:
            return self._dynamodb_client

        client_config = Config(retries={"max_attempts": 3, "mode": "adaptive"})

        if self.dynamodb_endpoint:
            # Local DynamoDB setup
            self._dynamodb_client = boto3.client(
                "dynamodb",
                endpoint_url=self.dynamodb_endpoint,
                region_name=self.aws_region,
                config=client_config,
            )
            return self._dynamodb_client

        # AWS DynamoDB setup
        self._dynamodb_client = boto3.client("dynamodb", config=client_config)
        return self._dynamodb_client

    @property
    def dynamodb_resource(self) -> Any:
        """Get or create DynamoDB resource instance"""
        if self._dynamodb_resource is not None:
            return self._dynamodb_resource

        if self.dynamodb_endpoint:
            # Local DynamoDB setup
            self._dynamodb_resource = boto3.resource(
                "dynamodb",
                endpoint_url=self.dynamodb_endpoint,
                region_name=self.aws_region,
            )
            return self._dynamodb_resource

        # AWS DynamoDB setup
        self._dynamodb_resource = boto3.resource(
            "dynamodb", region_name=self.aws_region
        )
        return self._dynamodb_resource


try:
    settings = Settings()

except Exception:
    logger.exception(
        "Failed to load application configuration with exception. Exiting."
    )
    sys.exit(1)
