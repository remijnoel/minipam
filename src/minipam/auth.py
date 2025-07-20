"""
Authentication backends and utilities for MiniPAM.

This module provides pluggable authentication backends following the specification
in docs/specs/auth_backend_spec.md.
"""

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Dict

import httpx
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError as JWTInvalidTokenError
from fastapi import HTTPException, Request, status

from .config_loader import get_config
from .models import AuthRequest, UserInfo

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Authentication error exception."""
    
    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class InvalidCredentialsError(AuthenticationError):
    """Invalid credentials error - subclass of AuthenticationError."""
    pass


class InvalidTokenError(AuthenticationError):
    """Invalid token error - subclass of AuthenticationError.""" 
    pass


class AuthBackend(ABC):
    """Abstract authentication backend interface."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    @abstractmethod
    async def authenticate(self, request: AuthRequest) -> UserInfo:
        """Authenticate a user from request data."""
        pass
    
    async def refresh(self, token: str) -> UserInfo:
        """Refresh a user token (optional)."""
        raise NotImplementedError("Refresh not supported by this backend")
        
    async def revoke(self, token: str) -> None:
        """Revoke a user token (optional)."""
        raise NotImplementedError("Revoke not supported by this backend")


class NoAuthBackend(AuthBackend):
    """No authentication backend for development."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Check if NoAuth is explicitly enabled via environment variable
        enable_noauth = os.environ.get("ENABLE_NOAUTH", "").lower()
        if enable_noauth not in ["true", "1", "yes"]:
            raise AuthenticationError("NoAuth backend is disabled")
    
    async def authenticate(self, request: AuthRequest) -> UserInfo:
        """Always return a default user."""
        return UserInfo(
            id="dev-user",
            username="developer",
            roles=["admin"],
            scopes=["cidr:read", "cidr:write", "cidr:delete"]
        )


class APIKeyBackend(AuthBackend):
    """API key authentication backend."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.valid_keys = config.get("keys", [])
    
    async def authenticate(self, request: AuthRequest) -> UserInfo:
        """Authenticate using API key from Authorization header."""
        # Try Authorization header first (case-insensitive)
        auth_header = ""
        api_key = None
        
        # Check for Authorization header (case-insensitive)
        for key, value in request.headers.items():
            if key.lower() == "authorization":
                auth_header = value
                break
        
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]  # Remove "Bearer " prefix
        else:
            # Try X-API-Key header (case-insensitive)
            for key, value in request.headers.items():
                if key.lower() == "x-api-key":
                    api_key = value
                    break
        
        if not api_key:
            raise InvalidCredentialsError("No API key provided")
        
        # Check if API key is valid
        if api_key not in self.valid_keys:
            raise InvalidCredentialsError("Invalid API key")
            
        return UserInfo(
            id="api-user",
            username="api-user", 
            roles=["user"],
            scopes=["cidr:read", "cidr:write"]
        )


class OIDCBackend(AuthBackend):
    """OIDC/OAuth2 authentication backend."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.issuer_url = config.get("issuer_url", "")
        self.client_id = config.get("client_id", "")
        self.client_secret = config.get("client_secret", "")
        self.jwks_cache_ttl = config.get("jwks_cache_ttl", 600)
        self._jwks_cache = {}
        self._jwks_cache_time = 0
        
        # Validate required configuration
        if not self.issuer_url or not self.client_id:
            raise AuthenticationError("OIDC backend requires issuer_url and client_id")
        
    async def authenticate(self, request: AuthRequest) -> UserInfo:
        """Authenticate using OIDC JWT token."""
        # Validate configuration
        if not self.issuer_url or not self.client_id:
            raise AuthenticationError("OIDC backend requires issuer_url and client_id")
            
        # Extract token from Authorization header
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            raise InvalidTokenError("No Bearer token provided")
            
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            # Get JWKS and validate token
            jwks = await self._get_jwks(self.issuer_url)
            decoded_token = self._validate_jwt(token, jwks, self.issuer_url, self.client_id)
            
            # Extract user info from token
            user_id = decoded_token.get("sub", "unknown")
            username = decoded_token.get("preferred_username") or decoded_token.get("email") or user_id
            roles = decoded_token.get("groups", decoded_token.get("roles", ["user"]))
            
            # Map roles to scopes
            scopes = self._map_roles_to_scopes(roles)
            
            return UserInfo(
                id=user_id,
                username=username,
                roles=roles,
                scopes=scopes
            )
            
        except ExpiredSignatureError:
            raise InvalidTokenError("Token has expired")
        except JWTInvalidTokenError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"OIDC authentication error: {str(e)}")
            raise InvalidTokenError("Invalid token header")
    
    async def _get_jwks(self, issuer_url: str) -> Dict[str, Any]:
        """Get JWKS from OIDC provider with caching."""
        current_time = time.time()
        
        # Check cache
        if (current_time - self._jwks_cache_time) < self.jwks_cache_ttl and self._jwks_cache:
            return self._jwks_cache
            
        # Fetch JWKS
        try:
            jwks_url = f"{issuer_url.rstrip('/')}/.well-known/jwks.json"
            with httpx.Client() as client:
                response = client.get(jwks_url, timeout=10.0)
                response.raise_for_status()
                
                jwks = response.json()
                self._jwks_cache = jwks
                self._jwks_cache_time = current_time
                
                return jwks
            
        except Exception as e:
            logger.error(f"Failed to fetch JWKS from {jwks_url}: {str(e)}")
            raise AuthenticationError("Failed to fetch JWKS")
    
    def _validate_jwt(self, token: str, jwks: Dict[str, Any], issuer_url: str, client_id: str) -> Dict[str, Any]:
        """Validate JWT token using JWKS."""
        # Decode header to get key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        if not kid:
            raise JWTInvalidTokenError("Token missing key ID")
            
        # Find matching key in JWKS
        signing_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                signing_key = jwt.PyJWK(key).key
                break
                
        if not signing_key:
            raise JWTInvalidTokenError("No matching key found in JWKS")
            
        # Verify and decode token
        decoded_token = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=client_id,
            issuer=issuer_url
        )
        
        return decoded_token
    
    def _map_roles_to_scopes(self, roles: list) -> list:
        """Map roles to scopes."""
        scopes = ["cidr:read"]  # All roles get read access
        
        # Admin roles get full access
        admin_roles = ["admin", "editor", "ipam-admin"]
        if any(role in admin_roles for role in roles):
            scopes.extend(["cidr:write", "cidr:delete"])
        
        return scopes


async def get_current_user(request: Request) -> UserInfo:
    """FastAPI dependency to get current authenticated user."""
    config = get_config()
    auth_config = config.auth
    
    # Get auth backend
    backend_type = auth_config.backend
    
    if backend_type == "none":
        # Temporarily set ENABLE_NOAUTH for NoAuthBackend initialization
        old_enable_noauth = os.environ.get("ENABLE_NOAUTH")
        os.environ["ENABLE_NOAUTH"] = "true"
        try:
            backend = NoAuthBackend({"enabled": True})
        finally:
            # Restore original ENABLE_NOAUTH value
            if old_enable_noauth is None:
                os.environ.pop("ENABLE_NOAUTH", None)
            else:
                os.environ["ENABLE_NOAUTH"] = old_enable_noauth
    elif backend_type == "apikey":
        apikey_config = auth_config.apikey
        if apikey_config:
            backend = APIKeyBackend({"keys": apikey_config.keys})
        else:
            backend = APIKeyBackend({})
    elif backend_type == "oidc":
        oidc_config = auth_config.oidc
        if oidc_config:
            backend = OIDCBackend({
                "issuer_url": oidc_config.issuer_url,
                "client_id": oidc_config.client_id,
                "client_secret": oidc_config.client_secret,
                "jwks_cache_ttl": oidc_config.jwks_cache_ttl,
            })
        else:
            backend = OIDCBackend({})
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unknown auth backend: {backend_type}"
        )
    
    # Create auth request from FastAPI request
    auth_request = AuthRequest(
        headers=dict(request.headers),
        cookies=dict(request.cookies),
        query_params=dict(request.query_params)
    )
    
    try:
        user = await backend.authenticate(auth_request)
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )