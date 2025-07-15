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
    

try:
    settings = Settings()

except Exception:
    logger.exception(
        "Failed to load application configuration with exception. Exiting."
    )
    sys.exit(1)
