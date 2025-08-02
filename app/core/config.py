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

        # S3 Configuration
        self.s3_endpoint = os.getenv("S3_ENDPOINT")  # For LocalStack
        self.s3_abend_log_inbound_bucket = os.getenv("S3_ABEND_LOG_INBOUND_BUCKET", "abend-logs-inbound")
        self.s3_abend_log_inbound_path = os.getenv("S3_ABEND_LOG_INBOUND_PATH", "raw-logs")
        self.s3_abend_log_processed_bucket = os.getenv("S3_ABEND_LOG_PROCESSED_BUCKET", "abend-logs-processed")
        self.s3_abend_log_processed_path = os.getenv("S3_ABEND_LOG_PROCESSED_PATH", "processed-logs")

        # Initialize boto3 clients as None (lazy initialization)
        self._dynamodb_client: Optional[Any] = None
        self._dynamodb_resource: Optional[Any] = None
        self._s3_client: Optional[Any] = None

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

    @property
    def s3_client(self) -> Any:
        """Get or create S3 client instance"""
        if self._s3_client is not None:
            return self._s3_client

        client_config = Config(retries={"max_attempts": 3, "mode": "adaptive"})

        if self.s3_endpoint:
            # Local S3 setup (LocalStack)
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=self.s3_endpoint,
                region_name=self.aws_region,
                config=client_config,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
            )
            return self._s3_client

        # AWS S3 setup
        self._s3_client = boto3.client("s3", config=client_config)
        return self._s3_client


try:
    settings = Settings()

except Exception:
    logger.exception(
        "Failed to load application configuration with exception. Exiting."
    )
    sys.exit(1)
