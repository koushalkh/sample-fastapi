import os
import sys

from structlog import get_logger

logger = get_logger()

class Settings:
    APP_NAME: str = "adr"
    APP_SERVICE_NAME: str = "adr-svc"

    def __init__(self):
        pass
    
    @property
    def is_dev_env(self):
        pod_namespace = os.environ.get("POD_NAMESPACE")
        
        return bool(pod_namespace)
    
    @property
    def log_level(self):
        if self.is_dev_env:
            return "DEBUG"
        return "INFO"

    @property
    def port(self):
        return 8000
    
    # Graph API Configuration
    @property
    def graph_api_endpoint(self):
        return os.environ.get("GRAPH_API_ENDPOINT", "https://graph.microsoft.com/v1.0")
    
    @property
    def tenant_id(self):
        return os.environ.get("GRAPH_API_TENANT_ID")
    
    @property
    def client_id(self):
        return os.environ.get("GRAPH_API_CLIENT_ID")
    
    @property
    def client_secret(self):
        return os.environ.get("GRAPH_API_CLIENT_SECRET")
    
    @property
    def graph_api_scopes(self):
        default_scopes = ["https://graph.microsoft.com/.default"]
        scopes_env = os.environ.get("GRAPH_API_GRAPH_API_SCOPES")
        if scopes_env:
            return scopes_env.split(",")
        return default_scopes


try:
    settings = Settings()

except Exception:
    logger.exception(
        "Failed to load application configuration with exception. Exiting."
    )
    sys.exit(1)
