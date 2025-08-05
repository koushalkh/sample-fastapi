import os
import sys
from typing import Any, Dict, Optional

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
        self.debug = os.getenv("DEBUG", "false").lower() == "true"

        # ADR Environment Configuration
        self.adr_env = os.getenv("ENV", "Local")

        # AWS Configuration
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.aws_account_id = os.getenv("AWS_ACCOUNT_ID")
        self.secrets_manager_region = os.getenv(
            "SECRETS_MANAGER_REGION", self.aws_region
        )

        # DynamoDB Configuration
        self.dynamodb_endpoint = os.getenv("DYNAMODB_ENDPOINT")

        # S3 Configuration
        self.s3_endpoint = os.getenv("S3_ENDPOINT")  # For LocalStack
        self.s3_abend_log_inbound_bucket = os.getenv(
            "S3_ABEND_LOG_INBOUND_BUCKET", "abend-logs-inbound"
        )
        self.s3_abend_log_inbound_path = os.getenv(
            "S3_ABEND_LOG_INBOUND_PATH", "raw-logs"
        )
        self.s3_abend_log_processed_bucket = os.getenv(
            "S3_ABEND_LOG_PROCESSED_BUCKET", "abend-logs-processed"
        )
        self.s3_abend_log_processed_path = os.getenv(
            "S3_ABEND_LOG_PROCESSED_PATH", "processed-logs"
        )

        # Middleware Configuration
        self.cors_origins = os.getenv("CORS_ORIGINS", "")
        self.slow_request_threshold_ms = float(
            os.getenv("SLOW_REQUEST_THRESHOLD_MS", "1000")
        )

        # Initialize boto3 clients as None (lazy initialization)
        self._dynamodb_client: Optional[Any] = None
        self._dynamodb_resource: Optional[Any] = None
        self._s3_client: Optional[Any] = None

        # Initialize secret configurations
        self._horizon_config: Optional[Dict[str, Any]] = None
        self._gitlab_config: Optional[Dict[str, Any]] = None
        self._dynamodb_secrets: Optional[Dict[str, Any]] = None
        self._graphapi_config: Optional[Dict[str, Any]] = None

    @property
    def is_local_env(self) -> bool:
        """
        Check if the application is running in local development environment.
        """
        return self.adr_env.lower() == "local"

    @property
    def is_dev_env(self) -> bool:
        """
        Check if the application is running in a development environment (deprecated - use is_local_env).
        """
        return self.is_local_env

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

    # Secret Management Properties

    @property
    def horizon_api_secret_name(self) -> str:
        """Get the Horizon API secret name based on ADR_ENV."""
        return f"adr-{self.adr_env.lower()}-horizonapi-secret"

    @property
    def gitlab_secret_name(self) -> str:
        """Get the GitLab secret name based on ADR_ENV."""
        return f"adr-{self.adr_env.lower()}-gitlab-secrets"

    @property
    def dynamodb_secret_name(self) -> str:
        """Get the DynamoDB secret name based on ADR_ENV."""
        return f"adr-{self.adr_env.lower()}-dynamodb-secrets"

    @property
    def graphapi_secret_name(self) -> str:
        """Get the Graph API secret name based on ADR_ENV."""
        return f"adr-{self.adr_env.lower()}-graphapi-secret"

    @property
    def horizon_config(self) -> Dict[str, Any]:
        """Get Horizon API configuration from secrets or environment variables."""
        if self._horizon_config is None:
            self._horizon_config = {}
        return self._horizon_config

    def set_horizon_config(self, config: Dict[str, Any]) -> None:
        """Set Horizon API configuration."""
        self._horizon_config = config

    @property
    def gitlab_config(self) -> Dict[str, Any]:
        """Get GitLab configuration from secrets or environment variables."""
        if self._gitlab_config is None:
            self._gitlab_config = {}
        return self._gitlab_config

    @property
    def gitlab_ssl_verify(self) -> bool:
        """Get GitLab SSL verification setting. False for local env, True for others."""
        return not self.is_local_env

    @property
    def gitlab_url(self) -> str:
        """Get GitLab URL."""
        return self.gitlab_config.get("ADR-GitlabUrl", "")

    @property
    def gitlab_token(self) -> str:
        """Get GitLab token."""
        return self.gitlab_config.get("ADR-GitlabToken", "")

    @property
    def gitlab_branch_name(self) -> str:
        """Get GitLab branch name."""
        return self.gitlab_config.get("ADR-GitlabBranchName", "main")

    @property
    def gitlab_project_id(self) -> str:
        """Get GitLab project ID."""
        return self.gitlab_config.get("ADR-GitlabProjectId", "")

    @property
    def trigger_log_extractor(self) -> bool:
        """Get trigger log extractor setting. Controls whether GitLab pipeline should be triggered."""
        return not self.is_local_env

    def set_gitlab_config(self, config: Dict[str, Any]) -> None:
        """Set GitLab configuration."""
        self._gitlab_config = config

    @property
    def dynamodb_secrets(self) -> Dict[str, Any]:
        """Get DynamoDB secrets from AWS Secrets Manager or environment variables."""
        if self._dynamodb_secrets is None:
            self._dynamodb_secrets = {}
        return self._dynamodb_secrets

    def set_dynamodb_secrets(self, config: Dict[str, Any]) -> None:
        """Set DynamoDB secrets."""
        self._dynamodb_secrets = config

    @property
    def graphapi_config(self) -> Dict[str, Any]:
        """Get Graph API configuration from secrets or environment variables."""
        if self._graphapi_config is None:
            self._graphapi_config = {}
        return self._graphapi_config

    def set_graphapi_config(self, config: Dict[str, Any]) -> None:
        """Set Graph API configuration."""
        self._graphapi_config = config


def load_config(settings: Settings) -> None:
    """
    Load external service configurations from AWS Secrets Manager or environment variables.

    This function is called after the Settings object is initialized to load secrets
    and external service configurations based on the ADR_ENV setting.

    Args:
        settings: The Settings instance to populate with configurations
    """
    logger.info("Loading external service configurations", adr_env=settings.adr_env)

    if settings.is_local_env:
        # Load from environment variables for local development
        _load_from_environment(settings)
    else:
        # Load from AWS Secrets Manager with environment variable fallback
        _load_from_secrets_manager(settings)

    logger.info("External service configurations loaded successfully")


def _load_from_environment(settings: Settings) -> None:
    """Load configurations from environment variables for local development."""
    logger.debug("Loading configurations from environment variables")

    # Horizon API Configuration
    settings.set_horizon_config(
        {
            "HORIZON_GATEWAY": os.getenv("HORIZON_GATEWAY", ""),
            "HORIZON_CLIENT_ID": os.getenv("HORIZON_CLIENT_ID", ""),
            "HORIZON_CLIENT_SECRET": os.getenv("HORIZON_CLIENT_SECRET", ""),
            "HORIZON_API_SECURE": os.getenv("HORIZON_API_SECURE", "true").lower()
            == "true",
        }
    )

    # GitLab Configuration
    settings.set_gitlab_config(
        {
            "ADR-GitlabUrl": os.getenv("ADR_GITLAB_URL", ""),
            "ADR-GitlabToken": os.getenv("ADR_GITLAB_TOKEN", ""),
            "ADR-GitlabBranchName": os.getenv("ADR_GITLAB_BRANCH_NAME", "main"),
            "ADR-GitlabProjectId": os.getenv("ADR_GITLAB_PROJECT_ID", ""),
        }
    )

    # DynamoDB Secrets
    settings.set_dynamodb_secrets(
        {
            "ADR-DynamoNamespace": os.getenv(
                "ADR_DYNAMO_NAMESPACE", f"{settings.app_name.lower()}-dynamodb-local"
            ),
            "ADR-RegionName": os.getenv("ADR_REGION_NAME", settings.aws_region),
        }
    )

    # Graph API Configuration
    settings.set_graphapi_config(
        {
            "ADR-ClientId": os.getenv("ADR_CLIENT_ID", ""),
            "ADR-ClientSecret": os.getenv("ADR_CLIENT_SECRET", ""),
            "ADR-TenantId": os.getenv("ADR_TENANT_ID", ""),
            "ADR-UserEmail": os.getenv("ADR_USER_EMAIL", ""),
        }
    )


def _load_from_secrets_manager(settings: Settings) -> None:
    """Load configurations from AWS Secrets Manager with environment variable fallback."""
    logger.debug("Loading configurations from AWS Secrets Manager")

    from app.utils.secrets_manager import SecretsManager

    secrets_manager = SecretsManager(region_name=settings.secrets_manager_region)

    # Load Horizon API Configuration
    horizon_config = _get_config_with_fallback(
        secrets_manager=secrets_manager,
        secret_name=settings.horizon_api_secret_name,
        env_fallback={
            "HORIZON_GATEWAY": "HORIZON_GATEWAY",
            "HORIZON_CLIENT_ID": "HORIZON_CLIENT_ID",
            "HORIZON_CLIENT_SECRET": "HORIZON_CLIENT_SECRET",
            "HORIZON_API_SECURE": "HORIZON_API_SECURE",
        },
        config_name="Horizon API",
    )
    # Convert string to boolean for HORIZON_API_SECURE
    if "HORIZON_API_SECURE" in horizon_config:
        horizon_config["HORIZON_API_SECURE"] = (
            str(horizon_config["HORIZON_API_SECURE"]).lower() == "true"
        )
    settings.set_horizon_config(horizon_config)

    # Load GitLab Configuration
    gitlab_config = _get_config_with_fallback(
        secrets_manager=secrets_manager,
        secret_name=settings.gitlab_secret_name,
        env_fallback={
            "ADR-GitlabUrl": "ADR_GITLAB_URL",
            "ADR-GitlabToken": "ADR_GITLAB_TOKEN",
            "ADR-GitlabBranchName": "ADR_GITLAB_BRANCH_NAME",
            "ADR-GitlabProjectId": "ADR_GITLAB_PROJECT_ID",
        },
        config_name="GitLab",
        defaults={"ADR-GitlabBranchName": "main"},
    )
    settings.set_gitlab_config(gitlab_config)

    # Load DynamoDB Secrets
    dynamodb_secrets = _get_config_with_fallback(
        secrets_manager=secrets_manager,
        secret_name=settings.dynamodb_secret_name,
        env_fallback={
            "ADR-DynamoNamespace": "ADR_DYNAMO_NAMESPACE",
            "ADR-RegionName": "ADR_REGION_NAME",
        },
        config_name="DynamoDB",
        defaults={
            "ADR-DynamoNamespace": f"{settings.app_name.lower()}-dynamodb-{settings.adr_env.lower()}",
            "ADR-RegionName": settings.aws_region,
        },
    )
    settings.set_dynamodb_secrets(dynamodb_secrets)

    # Load Graph API Configuration
    graphapi_config = _get_config_with_fallback(
        secrets_manager=secrets_manager,
        secret_name=settings.graphapi_secret_name,
        env_fallback={
            "ADR-ClientId": "ADR_CLIENT_ID",
            "ADR-ClientSecret": "ADR_CLIENT_SECRET",
            "ADR-TenantId": "ADR_TENANT_ID",
            "ADR-UserEmail": "ADR_USER_EMAIL",
        },
        config_name="Graph API",
    )
    settings.set_graphapi_config(graphapi_config)


def _get_config_with_fallback(
    secrets_manager,
    secret_name: str,
    env_fallback: Dict[str, str],
    config_name: str,
    defaults: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Get configuration from AWS Secrets Manager or environment variables.

    Args:
        secrets_manager: SecretsManager instance
        secret_name: Name of the secret in AWS Secrets Manager
        env_fallback: Dictionary mapping secret keys to environment variable names
        config_name: Name of the configuration (for logging)
        defaults: Optional default values for configuration keys

    Returns:
        Dictionary containing the configuration values
    """
    defaults = defaults or {}

    # Try AWS Secrets Manager first
    secret_data = secrets_manager.get_secret(secret_name)
    if secret_data:
        logger.debug(
            f"Successfully loaded {config_name} configuration from AWS Secrets Manager",
            secret_name=secret_name,
        )
        return secret_data

    # Fallback to environment variables
    logger.info(
        f"Falling back to environment variables for {config_name} configuration",
        secret_name=secret_name,
    )

    config_data = {}
    missing_vars = []

    for secret_key, env_var_name in env_fallback.items():
        env_value = os.getenv(env_var_name)
        if env_value is not None:
            config_data[secret_key] = env_value
        elif secret_key in defaults:
            config_data[secret_key] = defaults[secret_key]
            logger.debug(f"Using default value for {secret_key}", default_value="***")
        else:
            missing_vars.append(env_var_name)

    if missing_vars:
        logger.warning(
            f"Missing environment variables for {config_name} configuration",
            missing_vars=missing_vars,
        )
        # Return partial configuration instead of failing
        # Services can handle missing configuration as needed

    return config_data


try:
    settings = Settings()
    # Load external service configurations after settings initialization
    load_config(settings)

except Exception:
    logger.exception(
        "Failed to load application configuration with exception. Exiting."
    )
    sys.exit(1)
