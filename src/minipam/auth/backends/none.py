"""
None authentication backend

Disables authentication - all requests are considered authenticated with default permissions.
Used for development or when authentication is handled externally.
"""

import os
from typing import Optional, Dict, Any
from ..base import AuthBackend
from ..models import UserInfo, AuthRequest, AuthConfig


class NoneBackend(AuthBackend):
    """Authentication backend that disables authentication"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize none backend
        
        Args:
            config: Backend configuration (unused for none backend)
        """
        super().__init__(config)
        self.default_username = os.getenv("MINIPAM_DEFAULT_USERNAME", "admin")
        self.default_role = os.getenv("MINIPAM_DEFAULT_ROLE", "readwrite")
    
    async def authenticate(self, request: AuthRequest) -> Optional[UserInfo]:
        """Always return default user info (no authentication required)
        
        Args:
            request: Authentication request (ignored)
            
        Returns:
            Default UserInfo object
        """
        return UserInfo(
            username=self.default_username,
            email=None,
            roles=[self.default_role],
            is_authenticated=True
        )
    
    def get_config(self) -> AuthConfig:
        """Get authentication configuration
        
        Returns:
            AuthConfig indicating authentication is disabled
        """
        return AuthConfig(
            enabled=False,
            backend="none",
            login_url=None,
            supports_browser_flow=False
        )
    
    def is_enabled(self) -> bool:
        """Check if none backend is enabled
        
        Returns:
            True if MINIPAM_AUTH_BACKEND is set to 'none' or empty
        """
        auth_backend = os.getenv("MINIPAM_AUTH_BACKEND", "").lower()
        return auth_backend in ["", "none", "disabled"]
    
    def supports_browser_flow(self) -> bool:
        """None backend doesn't require browser flow
        
        Returns:
            False - no browser interaction needed
        """
        return False
