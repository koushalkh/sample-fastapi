"""
AWS Secrets Manager utility for fetching secrets.

This module provides a simple interface to fetch secrets from AWS Secrets Manager.
"""

import json
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from structlog import get_logger

logger = get_logger(__name__)


class SecretsManager:
    """
    AWS Secrets Manager client for fetching secrets from AWS.

    This class handles fetching secrets from AWS Secrets Manager only.
    Environment variable fallback logic should be handled at the application level.
    """

    def __init__(self, region_name: str = "us-east-1"):
        """
        Initialize the SecretsManager.

        Args:
            region_name: AWS region for Secrets Manager
        """
        self.region_name = region_name
        self._client: Optional[Any] = None
        self.logger = logger.bind(service="secrets_manager")

    @property
    def client(self):
        """Lazy initialization of the Secrets Manager client."""
        if self._client is None:
            try:
                self._client = boto3.client(
                    "secretsmanager", region_name=self.region_name
                )
                self.logger.debug(
                    "AWS Secrets Manager client initialized", region=self.region_name
                )
            except Exception as e:
                self.logger.warning(
                    "Failed to initialize AWS Secrets Manager client",
                    region=self.region_name,
                    error=str(e),
                )
                self._client = False  # Mark as failed to avoid retry
        return self._client if self._client else None

    def get_secret(self, secret_name: str) -> Optional[Dict[str, Any]]:
        """
        Get secret from AWS Secrets Manager.

        Args:
            secret_name: Name of the secret in AWS Secrets Manager

        Returns:
            Dictionary containing the secret values, or None if failed
        """
        if not self.client:
            self.logger.debug(
                "AWS Secrets Manager client not available", secret_name=secret_name
            )
            return None

        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            secret_string = response.get("SecretString")

            if not secret_string:
                self.logger.warning(
                    "Secret exists but has no SecretString", secret_name=secret_name
                )
                return None

            # Parse JSON secret
            try:
                secret_data = json.loads(secret_string)
                self.logger.debug(
                    "Successfully parsed secret JSON",
                    secret_name=secret_name,
                    keys=list(secret_data.keys()),
                )
                return secret_data
            except json.JSONDecodeError as e:
                self.logger.error(
                    "Failed to parse secret JSON", secret_name=secret_name, error=str(e)
                )
                return None

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                self.logger.warning(
                    "Secret not found in AWS Secrets Manager", secret_name=secret_name
                )
            elif error_code == "InvalidRequestException":
                self.logger.error(
                    "Invalid request to AWS Secrets Manager",
                    secret_name=secret_name,
                    error=str(e),
                )
            elif error_code == "InvalidParameterException":
                self.logger.error(
                    "Invalid parameter for AWS Secrets Manager",
                    secret_name=secret_name,
                    error=str(e),
                )
            else:
                self.logger.error(
                    "AWS Secrets Manager client error",
                    secret_name=secret_name,
                    error_code=error_code,
                    error=str(e),
                )
            return None

        except BotoCoreError as e:
            self.logger.error(
                "BotoCore error accessing AWS Secrets Manager",
                secret_name=secret_name,
                error=str(e),
            )
            return None

        except Exception as e:
            self.logger.error(
                "Unexpected error accessing AWS Secrets Manager",
                secret_name=secret_name,
                error=str(e),
            )
            return None


# Global instance for easy import
secrets_manager = SecretsManager()
