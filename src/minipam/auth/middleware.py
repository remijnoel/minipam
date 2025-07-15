"""
Authentication middleware for FastAPI

Provides JWT token validation and user context injection.
"""

import os
from typing import Optional, Callable, Any
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from .utils import validate_access_token
from .base import AuthTokenError
from .models import UserInfo


security = HTTPBearer(auto_error=False)


class AuthMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for authentication"""
    
    def __init__(self, app: Any):
        """Initialize authentication middleware
        
        Args:
            app: FastAPI application instance
        """
        super().__init__(app)
        self.auth_enabled = self._is_auth_enabled()
    
    def _is_auth_enabled(self) -> bool:
        """Check if authentication is enabled
        
        Returns:
            True if authentication is enabled
        """
        try:
            from ..config_loader import get_auth_backend
            auth_backend = get_auth_backend().lower()
        except ImportError:
            # Fallback to environment variable if config system not available
            auth_backend = os.getenv("MINIPAM_AUTH_BACKEND", "").lower()
        
        return auth_backend not in ["", "none", "disabled"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        """Process request with authentication
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response from downstream handler
        """
        # Skip authentication for certain paths
        if self._should_skip_auth(request.url.path):
            return await call_next(request)
        
        # Extract and validate token
        user_info = None
        if self.auth_enabled:
            try:
                user_info = await self._authenticate_request(request)
            except HTTPException as e:
                # Check if this is a browser request that should be redirected
                if self._is_browser_request(request) and self._should_redirect_to_login(request):
                    return await self._redirect_to_login(request)
                
                # Return JSON error for API requests
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail}
                )
        else:
            # Default user when auth is disabled
            user_info = UserInfo(
                username=os.getenv("MINIPAM_DEFAULT_USERNAME", "admin"),
                email=None,
                roles=[os.getenv("MINIPAM_DEFAULT_ROLE", "readwrite")],
                is_authenticated=True
            )
        
        # Add user context to request
        request.state.user = user_info
        
        return await call_next(request)
    
    def _should_skip_auth(self, path: str) -> bool:
        """Check if authentication should be skipped for this path
        
        Args:
            path: Request path
            
        Returns:
            True if auth should be skipped
        """
        skip_paths = [
            "/auth/config",
            "/auth/login",
            "/auth/callback",  # Covers all callback endpoints
            "/auth/health",
            "/health",
            "/api/health",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
        
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    def _is_browser_request(self, request: Request) -> bool:
        """Check if the request comes from a browser
        
        Args:
            request: FastAPI request object
            
        Returns:
            True if the request appears to be from a browser
        """
        accept_header = request.headers.get("accept", "")
        user_agent = request.headers.get("user-agent", "")
        
        # Check for typical browser Accept headers
        browser_indicators = [
            "text/html",
            "application/xhtml+xml",
            "text/*"
        ]
        
        # Check for typical API indicators (should NOT redirect)
        api_indicators = [
            "application/json",
            "curl/",
            "postman",
            "insomnia",
            "httpie"
        ]
        
        # If it's clearly an API request, don't redirect
        if any(indicator in accept_header.lower() or indicator in user_agent.lower() 
               for indicator in api_indicators):
            return False
        
        # If it looks like a browser request
        return any(indicator in accept_header.lower() for indicator in browser_indicators)
    
    def _should_redirect_to_login(self, request: Request) -> bool:
        """Check if the request should be redirected to login
        
        Args:
            request: FastAPI request object
            
        Returns:
            True if request should be redirected to login
        """
        path = request.url.path
        
        # Don't redirect API endpoints
        if path.startswith("/api/"):
            return False
        
        # Don't redirect auth endpoints
        if path.startswith("/auth/"):
            return False
            
        # Don't redirect docs/openapi
        if path.startswith(("/docs", "/redoc", "/openapi.json")):
            return False
        
        return True
    
    async def _redirect_to_login(self, request: Request):
        """Redirect to the login URL
        
        Args:
            request: FastAPI request object
            
        Returns:
            Redirect response to login URL
        """
        try:
            from .dependencies import get_auth_manager
            auth_manager = get_auth_manager()
            backend = auth_manager.get_active_backend()
            
            # For OIDC backend, redirect to the OIDC login endpoint
            if backend.name == "oidc" and backend.supports_browser_flow():
                from fastapi.responses import RedirectResponse
                # Redirect to our OIDC login endpoint which will handle the Azure redirect
                login_endpoint = "/auth/login/oidc"
                return RedirectResponse(url=login_endpoint, status_code=302)
            
            # For other backends that support browser flow, try to get login URL directly
            elif hasattr(backend, 'get_login_url') and backend.supports_browser_flow():
                login_url = backend.get_login_url()
                if login_url:
                    from fastapi.responses import RedirectResponse
                    return RedirectResponse(url=login_url, status_code=302)
        except Exception:
            # If we can't determine the backend, fall back to generic redirect
            pass
        
        # Fallback: redirect to auth login endpoint
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/auth/login/oidc", status_code=302)
    
    async def _authenticate_request(self, request: Request) -> UserInfo:
        """Authenticate the request
        
        Args:
            request: FastAPI request object
            
        Returns:
            UserInfo object for authenticated user
            
        Raises:
            HTTPException: If authentication fails
        """
        # Try to get authorization header
        credentials: Optional[HTTPAuthorizationCredentials] = await security(request)
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            # Validate JWT token
            user_info = validate_access_token(credentials.credentials)
            return user_info
            
        except AuthTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {e.message}",
                headers={"WWW-Authenticate": "Bearer"},
            )


def get_current_user(request: Request) -> UserInfo:
    """Get current authenticated user from request
    
    Args:
        request: FastAPI request object
        
    Returns:
        UserInfo object for current user
        
    Raises:
        HTTPException: If user is not authenticated
    """
    if not hasattr(request.state, "user") or request.state.user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    
    return request.state.user


def require_permission(permission: str) -> Callable:
    """Decorator to require specific permission
    
    Args:
        permission: Required permission ('read' or 'write')
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(request: Request, *args, **kwargs):
            user = get_current_user(request)
            
            if not user.has_permission(permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_read_permission(func: Callable) -> Callable:
    """Decorator to require read permission"""
    return require_permission("read")(func)


def require_write_permission(func: Callable) -> Callable:
    """Decorator to require write permission"""
    return require_permission("write")(func)
