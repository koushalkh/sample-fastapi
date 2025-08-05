"""
Utility constants for utils module
"""

# GitLab API Constants
GITLAB_API_VERSION = "v4"

# Retry Configuration
DEFAULT_RETRY_DELAY = 1.0
MAX_RETRY_DELAY = 30.0

# GitLab Pipeline Configuration
NUM_GITLAB_RETRIES = 3
GITLAB_JITTER = 1000