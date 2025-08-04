"""
Authentication Middleware for FastAPI application.

Provides conditional authentication based on environment settings.
In local development (is_local_env=True), authentication is bypassed.
"""

from typing import Any, Callable, Optional, Set, Dict
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from structlog import get_logger

from app.core.config import settings

logger = get_logger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle authentication for UI APIs.
    
    Features:
    - Conditional authentication based on environment
    - Bypasses auth in local development (is_local_env=True)
    - Configurable protected paths
    - Ready for Okta JWT integration
    """
    
    def __init__(
        self, 
        app: Any, 
        protected_paths: Optional[Set[str]] = None,
        bypass_local: bool = True
    ):
        """
        Initialize authentication middleware.
        
        Args:
            app: FastAPI application instance
            protected_paths: Set of path prefixes that require authentication
            bypass_local: Whether to bypass authentication in local environment
        """
        super().__init__(app)
        self.protected_paths = protected_paths or {"/adr/ui/"}
        self.bypass_local = bypass_local
        
        logger.info(
            "Authentication middleware initialized",
            protected_paths=list(self.protected_paths),
            bypass_local=bypass_local,
            is_local_env=settings.is_local_env
        )
    
    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        """
        Check authentication for protected paths.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler
            
        Returns:
            Response or raises HTTPException for unauthorized requests
        """
        # Check if path requires authentication
        if not self._is_protected_path(request.url.path):
            return await call_next(request)
        
        # Bypass authentication in local environment if configured
        if self.bypass_local and settings.is_local_env:
            logger.debug(
                "Bypassing authentication for local environment",
                path=request.url.path,
                is_local_env=settings.is_local_env
            )
            # Add mock user context for development
            request.state.user = self._create_mock_user()
            return await call_next(request)
        
        # Perform authentication
        try:
            user = await self._authenticate_request(request)
            request.state.user = user
            return await call_next(request)
            
        except HTTPException:
            # Re-raise HTTP exceptions (401, 403, etc.)
            raise
        except Exception as exc:
            logger.error(
                "Authentication error",
                path=request.url.path,
                error=str(exc),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error"
            )
    
    def _is_protected_path(self, path: str) -> bool:
        """
        Check if the request path requires authentication.
        
        Args:
            path: Request path
            
        Returns:
            True if path requires authentication
        """
        return any(path.startswith(protected_path) for protected_path in self.protected_paths)
    
    async def _authenticate_request(self, request: Request) -> Dict[str, Any]:
        """
        Authenticate the request and return user information.
        
        This method will be enhanced when Okta integration is implemented.
        
        Args:
            request: FastAPI request object
            
        Returns:
            User information dictionary
            
        Raises:
            HTTPException: If authentication fails
        """
        # TODO: Implement Okta JWT validation when details are available
        
        # Check for Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header:
            logger.warning("Missing authorization header", path=request.url.path)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Basic validation (to be replaced with Okta JWT validation)
        if not auth_header.startswith("Bearer "):
            logger.warning("Invalid authorization header format", path=request.url.path)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = auth_header.split(" ", 1)[1] if " " in auth_header else ""
        if not token:
            logger.warning("Missing bearer token", path=request.url.path)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # TODO: Replace with actual Okta JWT validation
        # For now, accept any non-empty token as valid
        user_info = await self._validate_jwt_token(token)
        
        logger.info("User authenticated successfully", 
                   user_id=user_info.get("user_id"),
                   path=request.url.path)
        
        return user_info
    
    async def _validate_jwt_token(self, token: str) -> dict:
        """
        Validate JWT token with Okta.
        
        This is a placeholder implementation that will be replaced
        with actual Okta JWT validation.
        
        Args:
            token: JWT token to validate
            
        Returns:
            User information from token
            
        Raises:
            HTTPException: If token is invalid
        """
        # TODO: Implement actual Okta JWT validation
        # This would include:
        # 1. Verify token signature with Okta public key
        # 2. Validate token expiration
        # 3. Check token issuer and audience
        # 4. Extract user claims
        
        # Placeholder implementation - accept any token
        if len(token) < 10:  # Basic validation
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Mock user data (replace with actual token claims)
        return {
            "user_id": "mock_user_123",
            "email": "user@company.com",
            "name": "Mock User",
            "roles": ["view", "edit"],  # Based on your roles: view, edit, admin
            "permissions": ["read:abend", "write:abend"]
        }
    
    def _create_mock_user(self) -> dict:
        """
        Create mock user context for local development.
        
        Returns:
            Mock user information
        """
        return {
            "user_id": "local_dev_user",
            "email": "developer@localhost",
            "name": "Local Developer",
            "roles": ["view", "edit", "admin"],  # Full access in development
            "permissions": ["read:abend", "write:abend", "admin:abend"]
        }


def setup_authentication_middleware(
    app: Any, 
    protected_paths: Optional[Set[str]] = None,
    bypass_local: bool = True,
    **kwargs: Any
) -> None:
    """
    Set up authentication middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
        protected_paths: Set of path prefixes that require authentication
        bypass_local: Whether to bypass authentication in local environment
        **kwargs: Additional arguments to pass to AuthenticationMiddleware
    """
    app.add_middleware(
        AuthenticationMiddleware, 
        protected_paths=protected_paths,
        bypass_local=bypass_local,
        **kwargs
    )
    
    logger.info(
        "Authentication middleware configured",
        protected_paths=list(protected_paths or {"/adr/ui/"}),
        bypass_local=bypass_local,
        is_local_env=settings.is_local_env
    )
