"""
Authentication module for MiniPAM

Provides modular authentication with multiple backends (none, apikey, oidc),
JWT token management, and FastAPI middleware integration.
"""

from .models import UserInfo, AuthRequest, AuthResponse, AuthConfig, AuthError
from .base import AuthBackend, AuthenticationError, AuthConfigurationError, AuthTokenError
from .utils import create_access_token, validate_access_token, get_jwt_handler
from .middleware import AuthMiddleware, get_current_user, require_read_permission, require_write_permission
from .dependencies import get_auth_manager, get_active_auth_backend, get_auth_config
from .api import auth_router
from . import backends

__all__ = [
    # Models
    "UserInfo", "AuthRequest", "AuthResponse", "AuthConfig", "AuthError",
    
    # Base classes and exceptions
    "AuthBackend", "AuthenticationError", "AuthConfigurationError", "AuthTokenError",
    
    # Utilities
    "create_access_token", "validate_access_token", "get_jwt_handler",
    
    # Middleware and decorators
    "AuthMiddleware", "get_current_user", "require_read_permission", "require_write_permission",
    
    # Dependencies
    "get_auth_manager", "get_active_auth_backend", "get_auth_config",
    
    # API router
    "auth_router",
    
    # Backends module
    "backends"
]
