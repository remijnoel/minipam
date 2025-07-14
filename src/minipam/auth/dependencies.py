"""
Authentication dependencies and backend management

Provides authentication backend selection and management.
"""

from typing import Dict, Optional
from .base import AuthBackend, AuthConfigurationError
from .backends import NoneBackend, ApiKeyBackend, OIDCBackend
from .models import AuthConfig


class AuthManager:
    """Manages authentication backends and configuration"""
    
    def __init__(self):
        """Initialize authentication manager"""
        self._backends: Dict[str, AuthBackend] = {}
        self._active_backend: Optional[AuthBackend] = None
        self._initialize_backends()
    
    def _initialize_backends(self) -> None:
        """Initialize all available authentication backends"""
        # Get auth configuration from the config loader
        from ..config import get_auth_config
        auth_config = get_auth_config()
        
        self._backends = {
            "none": NoneBackend(auth_config),
            "apikey": ApiKeyBackend(auth_config),
            "oidc": OIDCBackend(auth_config)
        }
        
        # Set active backend
        self._set_active_backend()
    
    def _set_active_backend(self) -> None:
        """Set the active authentication backend based on configuration"""
        from ..config import get_auth_backend
        backend_name = get_auth_backend().lower()
        
        if backend_name not in self._backends:
            raise AuthConfigurationError(
                f"Unknown authentication backend: {backend_name}",
                backend=backend_name
            )
        
        backend = self._backends[backend_name]
        
        # Validate backend configuration
        if not backend.validate_config():
            if backend_name != "none":
                # Fall back to none backend if the configured backend is invalid
                backend = self._backends["none"]
                backend_name = "none"
        
        self._active_backend = backend
    
    def get_active_backend(self) -> AuthBackend:
        """Get the currently active authentication backend
        
        Returns:
            Active AuthBackend instance
            
        Raises:
            AuthConfigurationError: If no backend is configured
        """
        if self._active_backend is None:
            raise AuthConfigurationError("No authentication backend configured")
        
        return self._active_backend
    
    def get_backend(self, name: str) -> Optional[AuthBackend]:
        """Get a specific authentication backend by name
        
        Args:
            name: Backend name
            
        Returns:
            AuthBackend instance or None if not found
        """
        return self._backends.get(name.lower())
    
    def get_available_backends(self) -> Dict[str, AuthBackend]:
        """Get all available authentication backends
        
        Returns:
            Dictionary of backend name to AuthBackend instance
        """
        return self._backends.copy()
    
    def get_auth_configuration(self) -> AuthConfig:
        """Get authentication configuration for the active backend
        
        Returns:
            AuthConfig object
        """
        return self.get_active_backend().get_config()
    
    def is_auth_enabled(self) -> bool:
        """Check if authentication is enabled
        
        Returns:
            True if authentication is enabled
        """
        return self.get_active_backend().is_enabled()
    
    def reload_backends(self) -> None:
        """Reload authentication backends (e.g., after config change)"""
        self._initialize_backends()


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get the global authentication manager instance
    
    Returns:
        AuthManager instance
    """
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


def get_active_auth_backend() -> AuthBackend:
    """Get the currently active authentication backend
    
    Returns:
        Active AuthBackend instance
    """
    return get_auth_manager().get_active_backend()


def get_auth_config() -> AuthConfig:
    """Get authentication configuration
    
    Returns:
        AuthConfig object for the active backend
    """
    return get_auth_manager().get_auth_configuration()
