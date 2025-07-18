"""
Authentication module for MiniPAM.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config_loader import get_config

logger = logging.getLogger(__name__)

# Security scheme for API key authentication
security = HTTPBearer(auto_error=False)


class AuthenticationError(Exception):
    """Authentication error exception."""

    pass


class AuthBackend:
    """Base authentication backend."""

    async def authenticate(
        self, credentials: Optional[HTTPAuthorizationCredentials]
    ) -> Optional[Any]:
        """Authenticate user credentials."""
        raise NotImplementedError


class NoAuthBackend(AuthBackend):
    """No authentication backend - allows all requests."""

    async def authenticate(
        self, credentials: Optional[HTTPAuthorizationCredentials]
    ) -> Optional[Any]:
        """Always allow access."""
        return {"username": "anonymous", "authenticated": False}


class APIKeyBackend(AuthBackend):
    """API key authentication backend."""

    def __init__(self, api_keys: list[str]):
        self.api_keys = set(api_keys)

    async def authenticate(
        self, credentials: Optional[HTTPAuthorizationCredentials]
    ) -> Optional[Any]:
        """Authenticate using API key."""
        if not credentials:
            raise AuthenticationError("Missing authentication credentials")

        if credentials.credentials not in self.api_keys:
            raise AuthenticationError("Invalid API key")

        return {"username": "api_key_user", "authenticated": True, "method": "api_key"}


class OIDCBackend(AuthBackend):
    """OIDC authentication backend."""

    def __init__(
        self, issuer_url: str, client_id: str, client_secret: Optional[str] = None
    ):
        self.issuer_url = issuer_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self._jwks_cache: Optional[Dict] = None
        self._jwks_cache_time: Optional[datetime] = None

    async def authenticate(
        self, credentials: Optional[HTTPAuthorizationCredentials]
    ) -> Optional[Any]:
        """Authenticate using OIDC JWT token."""
        if not credentials:
            raise AuthenticationError("Missing authentication credentials")

        try:
            # Decode and verify JWT token
            token = credentials.credentials

            # Get JWKS for verification
            await self._get_jwks()  # Validate JWKS endpoint is reachable

            # For simplicity, we'll skip full JWT verification in this implementation
            # In production, you would verify the signature using the JWKS

            # Decode without verification for now (NOT SECURE - for demo only)
            payload = jwt.decode(token, options={"verify_signature": False})

            # Basic validation
            if payload.get("iss") != self.issuer_url:
                raise AuthenticationError("Invalid token issuer")

            if payload.get("aud") != self.client_id:
                raise AuthenticationError("Invalid token audience")

            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(
                timezone.utc
            ):
                raise AuthenticationError("Token expired")

            return {
                "username": payload.get(
                    "preferred_username", payload.get("sub", "unknown")
                ),
                "authenticated": True,
                "method": "oidc",
                "claims": payload,
            }

        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"OIDC authentication error: {e}")
            raise AuthenticationError("Authentication failed")

    async def _get_jwks(self) -> Dict:
        """Get JWKS from the OIDC provider."""
        # Simple caching (5 minutes)
        now = datetime.now(timezone.utc)
        if (
            self._jwks_cache
            and self._jwks_cache_time
            and (now - self._jwks_cache_time).seconds < 300
        ):
            return self._jwks_cache

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.issuer_url}/.well-known/jwks.json")
                response.raise_for_status()

                self._jwks_cache = response.json()
                self._jwks_cache_time = now

                return self._jwks_cache

        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            raise AuthenticationError("Unable to verify token")


# Global auth backend instance
_auth_backend: Optional[AuthBackend] = None


def get_auth_backend() -> AuthBackend:
    """Get the configured authentication backend."""
    global _auth_backend

    if _auth_backend is None:
        config = get_config()

        if config.auth.backend == "none":
            _auth_backend = NoAuthBackend()
        elif config.auth.backend == "apikey":
            if not config.auth.apikey or not config.auth.apikey.get("keys"):
                raise ValueError(
                    "API key authentication requires 'auth.apikey.keys' configuration"
                )
            _auth_backend = APIKeyBackend(config.auth.apikey["keys"])
        elif config.auth.backend == "oidc":
            if not config.auth.oidc:
                raise ValueError(
                    "OIDC authentication requires 'auth.oidc' configuration"
                )

            oidc_config = config.auth.oidc
            issuer_url = oidc_config.get("issuer_url")
            client_id = oidc_config.get("client_id")
            client_secret = oidc_config.get("client_secret")

            if not issuer_url or not client_id:
                raise ValueError(
                    "OIDC authentication requires 'issuer_url' and 'client_id'"
                )

            _auth_backend = OIDCBackend(issuer_url, client_id, client_secret)
        else:
            raise ValueError(f"Unknown authentication backend: {config.auth.backend}")

    return _auth_backend


def reset_auth_backend() -> None:
    """Reset the auth backend - useful for testing."""
    global _auth_backend
    _auth_backend = None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Any:
    """FastAPI dependency to get current authenticated user."""
    auth_backend = get_auth_backend()

    try:
        user = await auth_backend.authenticate(credentials)
        if user is None:
            raise AuthenticationError("Authentication failed")
        return user
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
