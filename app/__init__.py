"""
ADR (Abnormal End Records) FastAPI Microservice

A production-ready FastAPI microservice for managing ABEND (Abnormal End) records
and SOPs (Standard Operating Procedures) with modular architecture, structured logging,
and flexible deployment options.
"""

# Health Check Endpoints
HEALTH_CHECK_PATH = "/healthz"
READINESS_CHECK_PATH = "/readyz"

__all__ = [
    "HEALTH_CHECK_PATH",
    "READINESS_CHECK_PATH",
]
