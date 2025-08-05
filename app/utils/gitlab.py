"""
GitLab API client for triggering pipelines with retry logic and jitter
"""

import asyncio
import random
from typing import Any, Dict, Optional
import aiohttp
from structlog import get_logger
from fastapi import status

from app.utils.constants import (
    GITLAB_API_VERSION,
    DEFAULT_RETRY_DELAY,
    MAX_RETRY_DELAY,
    NUM_GITLAB_RETRIES,
    GITLAB_JITTER
)

logger = get_logger(__name__)


class GitLabClient:
    """
    Async GitLab API client for pipeline operations with retry logic and jitter
    """

    def __init__(self, config: Dict[str, Any], ssl_verify: bool = True):
        """
        Initialize GitLab client
        
        Args:
            config: GitLab configuration containing URL, token, and branch
            ssl_verify: Whether to verify SSL certificates
        """
        self.base_url = config.get("ADR-GitlabUrl", "").rstrip("/")
        self.token = config.get("ADR-GitlabToken", "")
        self.branch_name = config.get("ADR-GitlabBranchName", "main")
        self.ssl_verify = ssl_verify
        
        if not self.base_url or not self.token:
            raise ValueError("GitLab URL and token are required")
        
        self.api_url = f"{self.base_url}/api/{GITLAB_API_VERSION}"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        logger.info(
            "GitLab client initialized",
            base_url=self.base_url,
            branch=self.branch_name,
            ssl_verify=ssl_verify
        )

    async def trigger_pipeline(
        self,
        project_id: str,
        variables: Optional[Dict[str, str]] = None,
        ref: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trigger a GitLab pipeline with retry logic and jitter
        
        Args:
            project_id: GitLab project ID
            variables: Pipeline variables
            ref: Git reference (branch/tag), defaults to configured branch
            
        Returns:
            Pipeline information
            
        Raises:
            aiohttp.ClientError: If all retries are exhausted
        """
        ref = ref or self.branch_name
        variables = variables or {}
        
        logger.info(
            "Triggering GitLab pipeline",
            project_id=project_id,
            ref=ref,
            variables_count=len(variables)
        )
        
        url = f"{self.api_url}/projects/{project_id}/pipeline"
        payload = {
            "ref": ref,
            "variables": [
                {"key": key, "value": value}
                for key, value in variables.items()
            ]
        }
        
        return await self._make_request_with_retry("POST", url, json=payload)

    async def _make_request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and jitter
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Response JSON data
            
        Raises:
            aiohttp.ClientError: If all retries are exhausted
        """
        last_exception = None
        
        for attempt in range(NUM_GITLAB_RETRIES + 1):  # +1 for initial attempt
            try:
                if attempt > 0:
                    # Apply jitter to retry delay
                    jitter_ms = random.uniform(0, GITLAB_JITTER)
                    base_delay = min(DEFAULT_RETRY_DELAY * (2 ** (attempt - 1)), MAX_RETRY_DELAY)
                    delay = base_delay + (jitter_ms / 1000)
                    
                    logger.info(
                        "Retrying GitLab request",
                        attempt=attempt,
                        max_retries=NUM_GITLAB_RETRIES,
                        delay_seconds=round(delay, 2),
                        url=url
                    )
                    
                    await asyncio.sleep(delay)
                
                connector = aiohttp.TCPConnector(ssl=self.ssl_verify)
                timeout = aiohttp.ClientTimeout(total=30)
                
                async with aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers=self.headers
                ) as session:
                    async with session.request(method, url, **kwargs) as response:
                        if response.status in [status.HTTP_200_OK, status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED]:
                            data = await response.json()
                            
                            if attempt > 0:
                                logger.info(
                                    "GitLab request succeeded after retry",
                                    attempt=attempt,
                                    status=response.status
                                )
                            
                            return data
                        else:
                            response_text = await response.text()
                            error_msg = f"GitLab API error: {response.status} - {response_text}"
                            
                            if response.status >= 500:  # Server errors are retryable
                                logger.warning(
                                    "GitLab server error, will retry",
                                    status=response.status,
                                    attempt=attempt,
                                    max_retries=NUM_GITLAB_RETRIES
                                )
                                last_exception = aiohttp.ClientResponseError(
                                    request_info=response.request_info,
                                    history=response.history,
                                    status=response.status,
                                    message=error_msg
                                )
                                continue
                            else:  # Client errors are not retryable
                                logger.error(
                                    "GitLab client error, not retrying",
                                    status=response.status,
                                    error=response_text
                                )
                                raise aiohttp.ClientResponseError(
                                    request_info=response.request_info,
                                    history=response.history,
                                    status=response.status,
                                    message=error_msg
                                )
                                
            except aiohttp.ClientError as e:
                last_exception = e
                logger.warning(
                    "GitLab request failed",
                    attempt=attempt,
                    max_retries=NUM_GITLAB_RETRIES,
                    error=str(e),
                    error_type=type(e).__name__
                )
                
                if attempt == NUM_GITLAB_RETRIES:
                    break
                    
            except Exception as e:
                logger.error(
                    "Unexpected error in GitLab request",
                    attempt=attempt,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
        
        # All retries exhausted
        logger.error(
            "GitLab request failed after all retries",
            max_retries=NUM_GITLAB_RETRIES,
            url=url
        )
        raise last_exception or aiohttp.ClientError("All retries exhausted")

    async def close(self):
        """
        Clean up resources (placeholder for future cleanup needs)
        """
        logger.debug("GitLab client cleanup completed")


async def create_gitlab_client(config: Dict[str, Any], ssl_verify: bool = True) -> GitLabClient:
    """
    Factory function to create GitLab client
    
    Args:
        config: GitLab configuration
        ssl_verify: Whether to verify SSL certificates
        
    Returns:
        GitLab client instance
    """
    return GitLabClient(config, ssl_verify)
