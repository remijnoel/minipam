"""
API Key authentication backend

Authenticates users using API keys stored in environment variables.
Each API key is mapped to a username and role.
"""

import os
import hashlib
from typing import Optional, Dict, Any
from ..base import AuthBackend, AuthenticationError
from ..models import UserInfo, AuthRequest, ApiKeyAuthRequest, AuthConfig


class ApiKeyBackend(AuthBackend):
    """Authentication backend using API keys"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize API key backend
        
        Args:
            config: Backend configuration dictionary
        """
        super().__init__(config)
        self.api_keys = self._load_api_keys()
    
    def _load_api_keys(self) -> Dict[str, Dict[str, str]]:
        """Load API keys from environment variables
        
        Expected format:
        MINIPAM_API_KEY_<USERNAME>=<key>:<role>
        
        Returns:
            Dictionary mapping API keys to user info
        """
        api_keys = {}
        
        for key, value in os.environ.items():
            if key.startswith("MINIPAM_API_KEY_"):
                username = key[16:].lower()  # Remove MINIPAM_API_KEY_ prefix
                
                if ":" in value:
                    api_key, role = value.split(":", 1)
                else:
                    api_key = value
                    role = "readonly"  # Default role
                
                # Hash the API key for secure comparison
                key_hash = hashlib.sha256(api_key.encode()).hexdigest()
                
                api_keys[key_hash] = {
                    "username": username,
                    "role": role
                }
        
        return api_keys
    
    async def authenticate(self, request: AuthRequest) -> Optional[UserInfo]:
        """Authenticate using API key
        
        Args:
            request: Authentication request containing API key
            
        Returns:
            UserInfo if authentication successful, None otherwise
            
        Raises:
            AuthenticationError: If request format is invalid
        """
        if not isinstance(request, ApiKeyAuthRequest):
            raise AuthenticationError("Invalid request type for API key backend")
        
        # Hash the provided API key
        key_hash = hashlib.sha256(request.api_key.encode()).hexdigest()
        
        # Look up the API key
        if key_hash not in self.api_keys:
            return None
        
        user_data = self.api_keys[key_hash]
        
        return UserInfo(
            username=user_data["username"],
            email=None,
            roles=[user_data["role"]],
            is_authenticated=True
        )
    
    def get_config(self) -> AuthConfig:
        """Get authentication configuration
        
        Returns:
            AuthConfig for API key authentication
        """
        return AuthConfig(
            enabled=True,
            backend="apikey",
            login_url=None,
            supports_browser_flow=False
        )
    
    def is_enabled(self) -> bool:
        """Check if API key backend is enabled
        
        Returns:
            True if MINIPAM_AUTH_BACKEND is 'apikey' and keys are configured
        """
        auth_backend = os.getenv("MINIPAM_AUTH_BACKEND", "").lower()
        return auth_backend == "apikey" and len(self.api_keys) > 0
    
    def validate_config(self) -> bool:
        """Validate API key configuration
        
        Returns:
            True if at least one API key is configured
        """
        return len(self.api_keys) > 0
    
    def supports_browser_flow(self) -> bool:
        """API key backend doesn't support browser flow
        
        Returns:
            False - API keys are used directly
        """
        return False
    
    def get_configured_users(self) -> list[str]:
        """Get list of configured usernames
        
        Returns:
            List of usernames with API keys
        """
        return [user_data["username"] for user_data in self.api_keys.values()]
