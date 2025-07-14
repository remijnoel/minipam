"""
Base authentication backend interface

Defines the abstract base class that all authentication backends must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from .models import UserInfo, AuthRequest, AuthConfig


class AuthBackend(ABC):
    """Abstract base class for authentication backends"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the backend with configuration
        
        Args:
            config: Backend-specific configuration dictionary
        """
        self.config = config
        self.name = self.__class__.__name__.lower().replace('backend', '')
    
    @abstractmethod
    async def authenticate(self, request: AuthRequest) -> Optional[UserInfo]:
        """Authenticate a user based on the request
        
        Args:
            request: Authentication request containing credentials
            
        Returns:
            UserInfo object if authentication successful, None otherwise
            
        Raises:
            AuthenticationError: If authentication fails with specific error
        """
        raise NotImplementedError("Subclasses must implement authenticate method")
    
    @abstractmethod
    def get_config(self) -> AuthConfig:
        """Get authentication configuration for this backend
        
        Returns:
            AuthConfig object with backend configuration
        """
        raise NotImplementedError("Subclasses must implement get_config method")
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if this backend is enabled and properly configured
        
        Returns:
            True if backend is enabled, False otherwise
        """
        raise NotImplementedError("Subclasses must implement is_enabled method")
    
    def validate_config(self) -> bool:
        """Validate backend configuration
        
        Returns:
            True if configuration is valid, False otherwise
        """
        return True
    
    def get_login_url(self) -> Optional[str]:
        """Get login URL for browser-based authentication flows
        
        Returns:
            Login URL if supported, None otherwise
        """
        return None
    
    def supports_browser_flow(self) -> bool:
        """Check if backend supports browser-based authentication flows
        
        Returns:
            True if browser flow is supported, False otherwise
        """
        return False


class AuthenticationError(Exception):
    """Base exception for authentication errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class AuthConfigurationError(Exception):
    """Exception for authentication configuration errors"""
    
    def __init__(self, message: str, backend: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.backend = backend


class AuthTokenError(Exception):
    """Exception for JWT token errors"""
    
    def __init__(self, message: str, token_type: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.token_type = token_type
