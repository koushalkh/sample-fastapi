"""
ADR (Abnormal End Records) FastAPI Microservice

A production-ready FastAPI microservice for managing ABEND (Abnormal End) records
and SOPs (Standard Operating Procedures) with modular architecture, structured logging,
and flexible deployment options.
"""

__version__ = "1.0.0"
__app_name__ = "adr-service"
__service_name__ = "adr-svc"

# API Configuration
API_VERSION = "v1alpha1"
SUPPORTED_API_MODES = ["UI", "INTERNAL", "ALL"]
DEFAULT_PORT = 8000

# Health Check Endpoints
HEALTH_CHECK_PATH = "/healthz"
READINESS_CHECK_PATH = "/readyz"

__all__ = [
    "__version__",
    "__app_name__",
    "__service_name__",
    "API_VERSION",
    "SUPPORTED_API_MODES",
    "DEFAULT_PORT",
    "HEALTH_CHECK_PATH",
    "READINESS_CHECK_PATH",
]
