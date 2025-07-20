"""Unit tests for authentication backends - WRITTEN FIRST per CLAUDE.md"""

import json
import os
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.minipam.auth import (
    APIKeyBackend,
    AuthBackend,
    AuthenticationError,
    InvalidCredentialsError,
    InvalidTokenError,
    NoAuthBackend,
    OIDCBackend,
)
from src.minipam.models import AuthRequest, UserInfo

# Mark as unit tests
pytestmark = pytest.mark.unit


class TestAuthBackendInterface:
    """Test the AuthBackend interface."""

    def test_auth_backend_is_abstract(self):
        """Test that AuthBackend cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AuthBackend({})

    def test_auth_backend_has_required_methods(self):
        """Test that AuthBackend interface has all required methods."""
        required_methods = ["authenticate", "refresh", "revoke"]
        for method in required_methods:
            assert hasattr(AuthBackend, method)
            assert callable(getattr(AuthBackend, method))


class TestNoAuthBackend:
    """Unit tests for NoAuthBackend."""

    def test_noauth_backend_requires_enable_flag(self):
        """Test that NoAuthBackend requires ENABLE_NOAUTH environment variable."""
        # Ensure the env var is not set
        os.environ.pop("ENABLE_NOAUTH", None)

        with pytest.raises(AuthenticationError, match="NoAuth backend is disabled"):
            NoAuthBackend({})

    def test_noauth_backend_accepts_enable_flag_true(self):
        """Test that NoAuthBackend accepts ENABLE_NOAUTH=true."""
        os.environ["ENABLE_NOAUTH"] = "true"

        try:
            backend = NoAuthBackend({})
            assert backend is not None
        finally:
            os.environ.pop("ENABLE_NOAUTH", None)

    def test_noauth_backend_accepts_enable_flag_variations(self):
        """Test that NoAuthBackend accepts various true values."""
        true_values = ["true", "1", "yes", "TRUE", "True", "YES", "Yes"]

        for value in true_values:
            os.environ["ENABLE_NOAUTH"] = value

            try:
                backend = NoAuthBackend({})
                assert backend is not None
            finally:
                os.environ.pop("ENABLE_NOAUTH", None)

    def test_noauth_backend_rejects_false_values(self):
        """Test that NoAuthBackend rejects false values."""
        false_values = ["false", "0", "no", "FALSE", "False", "NO", "No"]

        for value in false_values:
            os.environ["ENABLE_NOAUTH"] = value

            try:
                with pytest.raises(
                    AuthenticationError, match="NoAuth backend is disabled"
                ):
                    NoAuthBackend({})
            finally:
                os.environ.pop("ENABLE_NOAUTH", None)

    @pytest.mark.asyncio
    async def test_noauth_backend_authenticate_returns_default_user(self):
        """Test that NoAuthBackend always returns default user."""
        os.environ["ENABLE_NOAUTH"] = "true"

        try:
            backend = NoAuthBackend({})

            # Any request should return the same user
            requests = [
                AuthRequest(),
                AuthRequest(headers={"Authorization": "Bearer token"}),
                AuthRequest(cookies={"session": "abc123"}),
            ]

            for request in requests:
                user = await backend.authenticate(request)
                assert isinstance(user, UserInfo)
                assert user.id == "dev-user"
                assert user.username == "developer"
                assert user.roles == ["admin"]
                assert "cidr:read" in user.scopes
                assert "cidr:write" in user.scopes
                assert "cidr:delete" in user.scopes

        finally:
            os.environ.pop("ENABLE_NOAUTH", None)


class TestAPIKeyBackend:
    """Unit tests for APIKeyBackend."""

    def test_apikey_backend_initialization(self):
        """Test APIKeyBackend initializes correctly."""
        config = {"keys": ["key1", "key2", "key3"]}

        backend = APIKeyBackend(config)
        assert backend.valid_keys == ["key1", "key2", "key3"]

    def test_apikey_backend_initialization_empty_keys(self):
        """Test APIKeyBackend handles empty keys configuration."""
        config = {"keys": []}

        backend = APIKeyBackend(config)
        assert backend.valid_keys == []

    def test_apikey_backend_initialization_no_keys_config(self):
        """Test APIKeyBackend handles missing keys configuration."""
        config = {}

        backend = APIKeyBackend(config)
        assert backend.valid_keys == []

    @pytest.mark.asyncio
    async def test_apikey_backend_authenticate_bearer_token_success(self):
        """Test APIKeyBackend authenticates valid Bearer token."""
        config = {"keys": ["valid-key-123"]}
        backend = APIKeyBackend(config)

        request = AuthRequest(headers={"authorization": "Bearer valid-key-123"})
        user = await backend.authenticate(request)

        assert isinstance(user, UserInfo)
        assert user.id == "api-user"
        assert user.username == "api-user"
        assert user.roles == ["user"]
        assert "cidr:read" in user.scopes
        assert "cidr:write" in user.scopes

    @pytest.mark.asyncio
    async def test_apikey_backend_authenticate_x_api_key_success(self):
        """Test APIKeyBackend authenticates valid X-API-Key header."""
        config = {"keys": ["valid-key-456"]}
        backend = APIKeyBackend(config)

        request = AuthRequest(headers={"x-api-key": "valid-key-456"})
        user = await backend.authenticate(request)

        assert isinstance(user, UserInfo)
        assert user.id == "api-user"
        assert user.username == "api-user"
        assert user.roles == ["user"]
        assert "cidr:read" in user.scopes
        assert "cidr:write" in user.scopes

    @pytest.mark.asyncio
    async def test_apikey_backend_authenticate_no_key_fails(self):
        """Test APIKeyBackend fails when no API key provided."""
        config = {"keys": ["valid-key-789"]}
        backend = APIKeyBackend(config)

        request = AuthRequest()

        with pytest.raises(InvalidCredentialsError, match="No API key provided"):
            await backend.authenticate(request)

    @pytest.mark.asyncio
    async def test_apikey_backend_authenticate_invalid_key_fails(self):
        """Test APIKeyBackend fails with invalid API key."""
        config = {"keys": ["valid-key-abc"]}
        backend = APIKeyBackend(config)

        request = AuthRequest(headers={"authorization": "Bearer invalid-key"})

        with pytest.raises(InvalidCredentialsError, match="Invalid API key"):
            await backend.authenticate(request)

    @pytest.mark.asyncio
    async def test_apikey_backend_authenticate_malformed_bearer_fails(self):
        """Test APIKeyBackend fails with malformed Bearer token."""
        config = {"keys": ["valid-key-def"]}
        backend = APIKeyBackend(config)

        request = AuthRequest(headers={"authorization": "InvalidFormat valid-key-def"})

        with pytest.raises(InvalidCredentialsError, match="No API key provided"):
            await backend.authenticate(request)

    @pytest.mark.asyncio
    async def test_apikey_backend_authenticate_case_insensitive_headers(self):
        """Test APIKeyBackend handles case-insensitive headers."""
        config = {"keys": ["valid-key-ghi"]}
        backend = APIKeyBackend(config)

        # Test Authorization header
        request1 = AuthRequest(headers={"Authorization": "Bearer valid-key-ghi"})
        user1 = await backend.authenticate(request1)
        assert isinstance(user1, UserInfo)

        # Test X-API-Key header
        request2 = AuthRequest(headers={"X-API-Key": "valid-key-ghi"})
        user2 = await backend.authenticate(request2)
        assert isinstance(user2, UserInfo)

    @pytest.mark.asyncio
    async def test_apikey_backend_user_info_generation(self):
        """Test that APIKeyBackend generates consistent user info."""
        config = {"keys": ["test-key-123"]}
        backend = APIKeyBackend(config)

        request = AuthRequest(headers={"authorization": "Bearer test-key-123"})
        user1 = await backend.authenticate(request)
        user2 = await backend.authenticate(request)

        # Should generate same user info for same key
        assert user1.id == user2.id
        assert user1.username == user2.username
        assert user1.roles == user2.roles
        assert user1.scopes == user2.scopes


class TestOIDCBackend:
    """Unit tests for OIDCBackend."""

    def test_oidc_backend_initialization_success(self):
        """Test OIDCBackend initializes with required config."""
        config = {
            "issuer_url": "https://auth.example.com",
            "client_id": "test-client",
            "client_secret": "test-secret",
            "jwks_cache_ttl": 300,
        }

        backend = OIDCBackend(config)
        assert backend.issuer_url == "https://auth.example.com"
        assert backend.client_id == "test-client"
        assert backend.client_secret == "test-secret"
        assert backend.jwks_cache_ttl == 300

    def test_oidc_backend_initialization_missing_required_config(self):
        """Test OIDCBackend fails without required configuration."""
        # Missing issuer_url
        config1 = {"client_id": "test-client"}
        with pytest.raises(
            AuthenticationError, match="requires issuer_url and client_id"
        ):
            OIDCBackend(config1)

        # Missing client_id
        config2 = {"issuer_url": "https://auth.example.com"}
        with pytest.raises(
            AuthenticationError, match="requires issuer_url and client_id"
        ):
            OIDCBackend(config2)

    def test_oidc_backend_initialization_defaults(self):
        """Test OIDCBackend uses default values."""
        config = {"issuer_url": "https://auth.example.com", "client_id": "test-client"}

        backend = OIDCBackend(config)
        assert backend.client_secret == ""
        assert backend.jwks_cache_ttl == 600

    @pytest.mark.asyncio
    async def test_oidc_backend_authenticate_no_bearer_token_fails(self):
        """Test OIDCBackend fails when no Bearer token provided."""
        config = {"issuer_url": "https://auth.example.com", "client_id": "test-client"}
        backend = OIDCBackend(config)

        request = AuthRequest()

        with pytest.raises(InvalidTokenError, match="No Bearer token provided"):
            await backend.authenticate(request)

    @pytest.mark.asyncio
    async def test_oidc_backend_authenticate_malformed_bearer_fails(self):
        """Test OIDCBackend fails with malformed Bearer token."""
        config = {"issuer_url": "https://auth.example.com", "client_id": "test-client"}
        backend = OIDCBackend(config)

        request = AuthRequest(headers={"authorization": "InvalidFormat token"})

        with pytest.raises(InvalidTokenError, match="No Bearer token provided"):
            await backend.authenticate(request)

    @patch("src.minipam.auth.httpx")
    @patch("src.minipam.auth.jwt")
    @pytest.mark.asyncio
    async def test_oidc_backend_authenticate_jwt_expired_fails(self, mock_jwt, mock_httpx):
        """Test OIDCBackend fails with expired JWT token."""
        from jwt import ExpiredSignatureError

        config = {"issuer_url": "https://auth.example.com", "client_id": "test-client"}
        backend = OIDCBackend(config)

        # Mock JWKS response
        jwks_data = {
            "keys": [{"kid": "test-key-id", "kty": "RSA", "n": "mock-n", "e": "AQAB"}]
        }
        mock_response = MagicMock()
        mock_response.json.return_value = jwks_data
        mock_response.raise_for_status.return_value = None
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx.Client.return_value.__enter__.return_value = mock_client

        # Mock JWT to raise ExpiredSignatureError
        mock_jwt.get_unverified_header.return_value = {"kid": "test-key-id"}
        mock_jwt.PyJWK.return_value.key = MagicMock()
        mock_jwt.decode.side_effect = ExpiredSignatureError("Token expired")

        request = AuthRequest(headers={"authorization": "Bearer expired-token"})

        with pytest.raises(InvalidTokenError, match="Token has expired"):
            await backend.authenticate(request)

    @patch("src.minipam.auth.httpx")
    @patch("src.minipam.auth.jwt")
    @pytest.mark.asyncio
    async def test_oidc_backend_authenticate_invalid_token_fails(self, mock_jwt, mock_httpx):
        """Test OIDCBackend fails with invalid JWT token."""
        from jwt import InvalidTokenError as JWTInvalidTokenError

        config = {"issuer_url": "https://auth.example.com", "client_id": "test-client"}
        backend = OIDCBackend(config)

        # Mock JWKS response
        jwks_data = {
            "keys": [{"kid": "test-key-id", "kty": "RSA", "n": "mock-n", "e": "AQAB"}]
        }
        mock_response = MagicMock()
        mock_response.json.return_value = jwks_data
        mock_response.raise_for_status.return_value = None
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx.Client.return_value.__enter__.return_value = mock_client

        # Mock JWT to raise InvalidTokenError
        mock_jwt.get_unverified_header.return_value = {"kid": "test-key-id"}
        mock_jwt.PyJWK.return_value.key = MagicMock()
        mock_jwt.decode.side_effect = JWTInvalidTokenError("Invalid token")

        request = AuthRequest(headers={"authorization": "Bearer invalid-token"})

        with pytest.raises(InvalidTokenError, match="Invalid token"):
            await backend.authenticate(request)

    @patch("src.minipam.auth.httpx")
    @patch("src.minipam.auth.jwt")
    @pytest.mark.asyncio
    async def test_oidc_backend_authenticate_success(self, mock_jwt, mock_httpx):
        """Test OIDCBackend successful authentication."""
        config = {"issuer_url": "https://auth.example.com", "client_id": "test-client"}
        backend = OIDCBackend(config)

        # Mock JWKS response
        jwks_data = {
            "keys": [{"kid": "test-key-id", "kty": "RSA", "n": "mock-n", "e": "AQAB"}]
        }
        mock_response = MagicMock()
        mock_response.json.return_value = jwks_data
        mock_response.raise_for_status.return_value = None
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx.Client.return_value.__enter__.return_value = mock_client

        # Mock JWT operations
        mock_jwt.get_unverified_header.return_value = {"kid": "test-key-id"}
        mock_jwt.PyJWK.return_value.key = MagicMock()
        mock_jwt.decode.return_value = {
            "sub": "user-123",
            "preferred_username": "testuser",
            "email": "test@example.com",
            "groups": ["admin", "user"],
            "iss": "https://auth.example.com",
            "aud": "test-client",
        }

        request = AuthRequest(headers={"authorization": "Bearer valid-token"})
        user = await backend.authenticate(request)

        assert isinstance(user, UserInfo)
        assert user.id == "user-123"
        assert user.username == "testuser"
        assert user.roles == ["admin", "user"]
        assert "cidr:read" in user.scopes
        assert "cidr:write" in user.scopes
        assert "cidr:delete" in user.scopes

    @patch("src.minipam.auth.jwt")
    @pytest.mark.asyncio
    async def test_oidc_backend_validate_jwt_invalid_header_fails(self, mock_jwt):
        """Test OIDCBackend fails with invalid JWT header."""
        config = {"issuer_url": "https://auth.example.com", "client_id": "test-client"}
        backend = OIDCBackend(config)

        # Mock JWT to raise exception on header parsing
        mock_jwt.get_unverified_header.side_effect = Exception("Invalid header")

        request = AuthRequest(headers={"authorization": "Bearer invalid-header-token"})

        with pytest.raises(InvalidTokenError, match="Invalid token header"):
            await backend.authenticate(request)

    @patch("src.minipam.auth.httpx")
    @pytest.mark.asyncio
    async def test_oidc_backend_get_jwks_success(self, mock_httpx):
        """Test OIDCBackend successfully fetches JWKS."""
        config = {"issuer_url": "https://auth.example.com", "client_id": "test-client"}
        backend = OIDCBackend(config)

        # Mock JWKS response
        jwks_data = {
            "keys": [{"kid": "test-key-id", "kty": "RSA", "n": "mock-n", "e": "AQAB"}]
        }
        mock_response = MagicMock()
        mock_response.json.return_value = jwks_data
        mock_response.raise_for_status.return_value = None
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx.Client.return_value.__enter__.return_value = mock_client

        jwks = await backend._get_jwks("https://auth.example.com")

        assert jwks == jwks_data
        assert backend._jwks_cache == jwks_data

    @patch("src.minipam.auth.httpx")
    @pytest.mark.asyncio
    async def test_oidc_backend_get_jwks_caching(self, mock_httpx):
        """Test OIDCBackend caches JWKS for configured TTL."""
        config = {
            "issuer_url": "https://auth.example.com",
            "client_id": "test-client",
            "jwks_cache_ttl": 300,
        }
        backend = OIDCBackend(config)

        # Mock JWKS response
        jwks_data = {
            "keys": [{"kid": "test-key-id", "kty": "RSA", "n": "mock-n", "e": "AQAB"}]
        }
        mock_response = MagicMock()
        mock_response.json.return_value = jwks_data
        mock_response.raise_for_status.return_value = None
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx.Client.return_value.__enter__.return_value = mock_client

        # First call should fetch from server
        jwks1 = await backend._get_jwks("https://auth.example.com")
        assert mock_client.get.call_count == 1

        # Second call should use cache
        jwks2 = await backend._get_jwks("https://auth.example.com")
        assert mock_client.get.call_count == 1  # No additional call
        assert jwks1 == jwks2

    @patch("src.minipam.auth.httpx")
    @pytest.mark.asyncio
    async def test_oidc_backend_get_jwks_fetch_failure(self, mock_httpx):
        """Test OIDCBackend handles JWKS fetch failure."""
        config = {"issuer_url": "https://auth.example.com", "client_id": "test-client"}
        backend = OIDCBackend(config)

        # Mock network failure
        mock_httpx.Client.return_value.__enter__.side_effect = Exception("Network error")

        with pytest.raises(AuthenticationError, match="Failed to fetch JWKS"):
            await backend._get_jwks("https://auth.example.com")

    def test_oidc_backend_map_roles_to_scopes(self):
        """Test OIDCBackend maps roles to scopes correctly."""
        config = {"issuer_url": "https://auth.example.com", "client_id": "test-client"}
        backend = OIDCBackend(config)

        # Test admin role
        admin_scopes = backend._map_roles_to_scopes(["admin"])
        assert "cidr:read" in admin_scopes
        assert "cidr:write" in admin_scopes
        assert "cidr:delete" in admin_scopes

        # Test editor role
        editor_scopes = backend._map_roles_to_scopes(["editor"])
        assert "cidr:read" in editor_scopes
        assert "cidr:write" in editor_scopes
        assert "cidr:delete" in editor_scopes

        # Test ipam-admin role
        ipam_admin_scopes = backend._map_roles_to_scopes(["ipam-admin"])
        assert "cidr:read" in ipam_admin_scopes
        assert "cidr:write" in ipam_admin_scopes
        assert "cidr:delete" in ipam_admin_scopes

        # Test user role (basic)
        user_scopes = backend._map_roles_to_scopes(["user"])
        assert "cidr:read" in user_scopes
        assert "cidr:write" not in user_scopes
        assert "cidr:delete" not in user_scopes

        # Test unknown role
        unknown_scopes = backend._map_roles_to_scopes(["unknown"])
        assert "cidr:read" in unknown_scopes
        assert "cidr:write" not in unknown_scopes
        assert "cidr:delete" not in unknown_scopes

    @patch("src.minipam.auth.httpx")
    @patch("src.minipam.auth.jwt")
    @pytest.mark.asyncio
    async def test_oidc_backend_authenticate_missing_user_info_uses_defaults(
        self, mock_jwt, mock_httpx
    ):
        """Test OIDCBackend handles missing user info gracefully."""
        config = {"issuer_url": "https://auth.example.com", "client_id": "test-client"}
        backend = OIDCBackend(config)

        # Mock JWKS response
        jwks_data = {
            "keys": [{"kid": "test-key-id", "kty": "RSA", "n": "mock-n", "e": "AQAB"}]
        }
        mock_response = MagicMock()
        mock_response.json.return_value = jwks_data
        mock_response.raise_for_status.return_value = None
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_httpx.Client.return_value.__enter__.return_value = mock_client

        # Mock JWT operations with minimal payload
        mock_jwt.get_unverified_header.return_value = {"kid": "test-key-id"}
        mock_jwt.PyJWK.return_value.key = MagicMock()
        mock_jwt.decode.return_value = {
            "sub": "user-456",
            "iss": "https://auth.example.com",
            "aud": "test-client",
        }

        request = AuthRequest(headers={"authorization": "Bearer minimal-token"})
        user = await backend.authenticate(request)

        assert isinstance(user, UserInfo)
        assert user.id == "user-456"
        assert user.username == "user-456"  # Falls back to user ID
        assert user.roles == ["user"]  # Default role
        assert "cidr:read" in user.scopes
