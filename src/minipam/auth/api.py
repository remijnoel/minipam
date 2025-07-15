"""
Authentication API endpoints

Provides REST API endpoints for authentication configuration, login, and token
management.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import RedirectResponse, HTMLResponse

from .models import (
    AuthConfig, AuthRequest, ApiKeyAuthRequest, OIDCAuthRequest,
    AuthResponse, UserInfo
)
from .base import AuthenticationError, AuthConfigurationError
from .dependencies import get_auth_manager, get_active_auth_backend
from .utils import create_access_token
from .middleware import get_current_user

# Create authentication router
auth_router = APIRouter(prefix="/auth", tags=["authentication"])


@auth_router.get("/config", response_model=AuthConfig)
async def get_auth_config() -> AuthConfig:
    """Get authentication configuration
    
    Returns:
        Authentication configuration including backend type and login URL
    """
    try:
        auth_manager = get_auth_manager()
        return auth_manager.get_auth_configuration()
    except AuthConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication configuration error: {e.message}"
        )


@auth_router.post("/login", response_model=AuthResponse)
async def login(request: AuthRequest) -> AuthResponse:
    """Authenticate user and return access token
    
    Args:
        request: Authentication request (type depends on backend)
        
    Returns:
        Authentication response with access token
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        backend = get_active_auth_backend()
        
        # Authenticate user
        user_info = await backend.authenticate(request)
        
        if user_info is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
        
        # Create access token
        access_token = create_access_token(user_info)
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=8 * 3600,  # 8 hours
            user=user_info
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@auth_router.post("/login/apikey", response_model=AuthResponse)
async def login_with_apikey(api_key: str) -> AuthResponse:
    """Authenticate using API key
    
    Args:
        api_key: API key for authentication
        
    Returns:
        Authentication response with access token
    """
    request = ApiKeyAuthRequest(backend="apikey", api_key=api_key)
    return await login(request)


@auth_router.get("/login/oidc")
async def login_with_oidc(request: Request):
    """Initiate OIDC login flow
    
    Returns:
        Redirect to OIDC provider authorization URL
    """
    try:
        backend = get_active_auth_backend()
        
        if backend.name != "oidc":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OIDC authentication not configured"
            )
        
        login_url, state_cookie = backend.get_login_url(request)
        if not login_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OIDC login URL not available"
            )
        
        response = RedirectResponse(url=login_url)
        response.set_cookie(**state_cookie)
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OIDC login failed: {str(e)}"
        )


@auth_router.get("/callback/oidc")
async def oidc_callback(request: Request, code: str, state: str):
    """Handle OIDC callback and complete authentication
    
    Args:
        request: FastAPI request object
        code: Authorization code from OIDC provider
        state: State parameter for CSRF protection
        
    Returns:
        Authentication response with access token or browser redirect
    """
    # Validate state to prevent CSRF
    stored_state = request.cookies.get("oidc_state")
    if not stored_state or stored_state != state:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OIDC state"
        )

    # Complete the authentication
    auth_request = OIDCAuthRequest(backend="oidc", code=code, state=state)
    auth_response = await login(auth_request)
    
    # Check if this is a browser request
    user_agent = request.headers.get("user-agent", "").lower()
    accept_header = request.headers.get("accept", "").lower()
    
    is_browser = (
        "mozilla" in user_agent or
        "webkit" in user_agent or 
        "chrome" in user_agent or
        "safari" in user_agent or
        "text/html" in accept_header
    )
    
    if is_browser:
        # For browser requests, return HTML that stores the token and redirects
        jwt_token = auth_response.access_token
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Successful</title>
            <script>
                // Store the JWT token
                localStorage.setItem('minipam_access_token', '{jwt_token}');
                
                // Store token info
                localStorage.setItem('minipam_token_type', 'bearer');
                localStorage.setItem('minipam_token_expires', '{auth_response.expires_in}');
                
                // Redirect to the UI
                window.location.href = '/ui';
            </script>
        </head>
        <body>
            <h2>Authentication Successful</h2>
            <p>Redirecting to MiniPAM UI...</p>
            <script>
                // Fallback redirect after 2 seconds
                setTimeout(function() {{
                    window.location.href = '/ui';
                }}, 2000);
            </script>
        </body>
        </html>
        """
        response = HTMLResponse(content=html_content)
        response.delete_cookie("oidc_state")
        return response
    else:
        # For API requests, return JSON
        return auth_response


@auth_router.get("/user", response_model=UserInfo)
async def get_current_user_info(
    user: UserInfo = Depends(get_current_user)
) -> UserInfo:
    """Get current authenticated user information
    
    Args:
        user: Current user from authentication middleware
        
    Returns:
        Current user information
    """
    return user


@auth_router.post("/logout")
async def logout() -> Dict[str, str]:
    """Logout current user
    
    Note: With JWT tokens, logout is handled client-side by discarding the token.
    This endpoint exists for API consistency.
    
    Returns:
        Success message
    """
    return {"message": "Logged out successfully"}


@auth_router.get("/health")
async def auth_health() -> Dict[str, Any]:
    """Check authentication system health
    
    Returns:
        Health status of authentication system
    """
    try:
        auth_manager = get_auth_manager()
        active_backend = auth_manager.get_active_backend()
        
        return {
            "status": "healthy",
            "backend": active_backend.name,
            "enabled": active_backend.is_enabled(),
            "configured": active_backend.validate_config()
        }
        
    except (AuthConfigurationError, AuthenticationError) as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
