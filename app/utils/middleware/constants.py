"""
Constants for middleware and application configuration.
"""

# Session Management Constants
SESSION_TIMEOUT_MINUTES = 30
SESSION_COOKIE_NAME = "adr_session"
SESSION_COOKIE_SECURE = True  # Set to True in production
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "lax"

# Security Headers Constants  
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY", 
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

# HTTPS Security Headers (for production)
HTTPS_SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
}

# Content Security Policy
CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "font-src 'self' https:; "
    "connect-src 'self' https:; "
    "frame-ancestors 'none';"
)

# CORS Constants
DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",  # React dev server
    "http://localhost:8080",  # Vue dev server  
    "http://localhost:4200",  # Angular dev server
]

CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
CORS_HEADERS = [
    "accept",
    "accept-encoding", 
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-correlation-id",
]

# Request Logging Constants
CORRELATION_ID_HEADER = "X-Correlation-ID"
REQUEST_ID_HEADER = "X-Request-ID"
RESPONSE_TIME_HEADER = "X-Response-Time"

# Skip logging for these paths
SKIP_LOGGING_PATHS = {
    "/healthz",
    "/readyz", 
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
}

# Sensitive headers to exclude from logs
SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "x-api-key",
    "x-auth-token",
}
