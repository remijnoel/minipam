#!/usr/bin/env python3
"""
Functional tests for OIDC authentication flow

This test suite verifies the complete OIDC authentication flow including:
- Backend configuration and initialization
- Login URL generation and endpoints
- Browser auto-redirect behavior
- Callback processing with mocked Azure responses
- End-to-end authentication workflow
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock, Mock
from urllib.parse import urlparse, parse_qs
from fastapi.testclient import TestClient

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from minipam.main import create_app
from minipam.auth.models import OIDCAuthRequest, UserInfo
from minipam.auth.backends.oidc import OIDCBackend
from minipam.auth.dependencies import get_auth_manager
from minipam.auth.utils import validate_access_token


class TestOIDCAuthenticationFlow:
    """Comprehensive tests for OIDC authentication flow"""

    @pytest.fixture(autouse=True)
    def setup_oidc_environment(self):
        """Set up OIDC test environment"""
        # Set environment for OIDC testing
        os.environ["MINIPAM_AUTH_BACKEND"] = "oidc"
        os.environ["MINIPAM_STORAGE_TYPE"] = "memory"
        os.environ["MINIPAM_JWT_SECRET"] = "test-secret-for-oidc-testing"
        
        # Azure OIDC configuration
        os.environ["MINIPAM_OIDC_CLIENT_ID"] = "test-client-id-12345"
        os.environ["MINIPAM_OIDC_CLIENT_SECRET"] = "test-client-secret-67890"
        os.environ["MINIPAM_OIDC_ISSUER_URL"] = "https://login.microsoftonline.com/test-tenant-id/v2.0"
        os.environ["MINIPAM_OIDC_REDIRECT_URI"] = "http://localhost:8000/auth/callback/oidc"
        os.environ["MINIPAM_OIDC_SCOPE"] = "openid profile email"
        os.environ["MINIPAM_OIDC_ROLE_MAPPING"] = "minipam-admins:readwrite,minipam-users:readonly"
        os.environ["MINIPAM_OIDC_DEFAULT_ROLE"] = "readonly"
        
        # Force config system to reload with environment variables
        import minipam.config
        import minipam.config_loader
        import minipam.auth.dependencies
        minipam.config._config = None  # Reset global config
        minipam.config_loader.config_loader.config = {}  # Reset config loader
        minipam.auth.dependencies._auth_manager = None  # Reset auth manager
        
        # Force config loading with environment overrides
        from minipam.config_loader import config_loader
        config_loader._apply_env_overrides()
        minipam.config._config = config_loader.get_config()
        
        yield
        
        # Clean up environment and reset globals
        oidc_env_vars = [
            "MINIPAM_AUTH_BACKEND", "MINIPAM_STORAGE_TYPE", "MINIPAM_JWT_SECRET",
            "MINIPAM_OIDC_CLIENT_ID", "MINIPAM_OIDC_CLIENT_SECRET", "MINIPAM_OIDC_ISSUER_URL",
            "MINIPAM_OIDC_REDIRECT_URI", "MINIPAM_OIDC_SCOPE", "MINIPAM_OIDC_ROLE_MAPPING",
            "MINIPAM_OIDC_DEFAULT_ROLE"
        ]
        for var in oidc_env_vars:
            os.environ.pop(var, None)
        
        # Reset globals again
        minipam.config._config = None
        minipam.auth.dependencies._auth_manager = None

    @pytest.fixture
    def mock_azure_responses(self):
        """Mock Azure OIDC discovery and API responses"""
        
        # Mock Azure discovery document
        discovery_response = {
            "issuer": "https://login.microsoftonline.com/test-tenant-id/v2.0",
            "authorization_endpoint": "https://login.microsoftonline.com/test-tenant-id/oauth2/v2.0/authorize",
            "token_endpoint": "https://login.microsoftonline.com/test-tenant-id/oauth2/v2.0/token",
            "userinfo_endpoint": "https://graph.microsoft.com/oidc/userinfo",
            "jwks_uri": "https://login.microsoftonline.com/test-tenant-id/discovery/v2.0/keys",
            "response_types_supported": ["code"],
            "subject_types_supported": ["pairwise"],
            "id_token_signing_alg_values_supported": ["RS256"],
            "scopes_supported": ["openid", "profile", "email"]
        }
        
        # Mock token exchange response
        token_response = {
            "access_token": "mock_access_token_12345",
            "token_type": "Bearer",
            "expires_in": 3600,
            "id_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.mock_claims.mock_signature",
            "refresh_token": "mock_refresh_token"
        }
        
        # Mock userinfo response
        userinfo_response = {
            "sub": "00000000-0000-0000-0000-000000000001",
            "name": "Test User",
            "preferred_username": "testuser@company.com",
            "email": "testuser@company.com",
            "groups": ["minipam-admins", "minipam-users"],
            "roles": ["User", "Admin"]
        }
        
        def mock_urlopen(request):
            """Mock urllib.request.urlopen responses based on URL"""
            url = request.full_url if hasattr(request, 'full_url') else str(request)
            
            # Create mock response object
            mock_response = Mock()
            mock_response.status = 200
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=None)
            
            if "/.well-known/openid-configuration" in url:
                mock_response.read.return_value = json.dumps(discovery_response).encode()
            elif "/oauth2/v2.0/token" in url:
                mock_response.read.return_value = json.dumps(token_response).encode()
            elif "/oidc/userinfo" in url:
                mock_response.read.return_value = json.dumps(userinfo_response).encode()
            else:
                # Default response
                mock_response.status = 404
                mock_response.read.return_value = b'{"error": "not_found"}'
            
            return mock_response
        
        with patch('urllib.request.urlopen', side_effect=mock_urlopen):
            yield {
                "discovery": discovery_response,
                "token": token_response,
                "userinfo": userinfo_response
            }

    @pytest.fixture
    def client(self):
        """Create FastAPI test client with OIDC configuration"""
        app = create_app()
        return TestClient(app)

    def test_oidc_backend_configuration(self):
        """Test OIDC backend is properly configured and enabled"""
        # Get the auth config like the auth manager does
        from minipam.config import get_auth_config
        auth_config = get_auth_config()
        
        # Test backend initialization with auth config
        backend = OIDCBackend(auth_config)
        
        # Verify configuration is loaded
        assert backend.client_id == "test-client-id-12345"
        assert backend.client_secret == "test-client-secret-67890"
        assert backend.issuer_url == "https://login.microsoftonline.com/test-tenant-id/v2.0"
        assert backend.redirect_uri == "http://localhost:8000/auth/callback/oidc"
        assert backend.scope == "openid profile email"
        
        # Verify backend reports as enabled
        assert backend.is_enabled() == True
        assert backend.validate_config() == True
        assert backend.supports_browser_flow() == True

    def test_auth_manager_oidc_selection(self):
        """Test auth manager selects OIDC as active backend"""
        auth_manager = get_auth_manager()
        active_backend = auth_manager.get_active_backend()
        
        # Verify OIDC backend is selected
        assert active_backend.name == "oidc"
        assert active_backend.is_enabled() == True
        
        # Verify auth configuration
        auth_config = auth_manager.get_auth_configuration()
        assert auth_config.enabled == True
        assert auth_config.backend == "oidc"
        assert auth_config.supports_browser_flow == True
        assert auth_config.login_url is not None

    def test_oidc_login_url_generation(self, mock_azure_responses):
        """Test OIDC login URL generation"""
        config = {
            "oidc": {
                "client_id": "test-client-id-12345",
                "issuer_url": "https://login.microsoftonline.com/test-tenant-id/v2.0",
                "redirect_uri": "http://localhost:8000/auth/callback/oidc",
                "scope": "openid profile email"
            }
        }
        
        backend = OIDCBackend(config)
        login_url = backend.get_login_url()
        
        # Verify login URL is generated
        assert login_url is not None
        assert "login.microsoftonline.com" in login_url
        
        # Parse and verify URL components
        parsed = urlparse(login_url)
        query_params = parse_qs(parsed.query)
        
        assert query_params["response_type"][0] == "code"
        assert query_params["client_id"][0] == "test-client-id-12345"
        assert query_params["redirect_uri"][0] == "http://localhost:8000/auth/callback/oidc"
        assert query_params["scope"][0] == "openid profile email"
        assert "state" in query_params

    def test_auth_config_endpoint(self, client):
        """Test /auth/config endpoint returns correct OIDC configuration"""
        response = client.get("/auth/config")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify OIDC configuration
        assert data["enabled"] == True
        assert data["backend"] == "oidc"
        assert data["supports_browser_flow"] == True
        assert data["login_url"] is not None
        assert "login.microsoftonline.com" in data["login_url"]

    def test_oidc_login_endpoint_redirect(self, client, mock_azure_responses):
        """Test /auth/login/oidc endpoint redirects to Azure"""
        response = client.get("/auth/login/oidc", follow_redirects=False)
        
        # Should return redirect response
        assert response.status_code in [302, 307]
        assert "location" in response.headers
        
        # Verify redirect URL points to Azure
        redirect_url = response.headers["location"]
        assert "login.microsoftonline.com" in redirect_url
        assert "test-client-id-12345" in redirect_url
        assert "response_type=code" in redirect_url

    def test_browser_auto_redirect_behavior(self, client):
        """Test browser requests automatically redirect to OIDC login"""
        # Test browser request to root
        response = client.get(
            "/",
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            },
            follow_redirects=False
        )
        
        assert response.status_code == 302
        assert response.headers["location"] == "/auth/login/oidc"
        
        # Test browser request to /ui
        response = client.get(
            "/ui",
            headers={
                "Accept": "text/html,application/xhtml+xml",
                "User-Agent": "Mozilla/5.0 Safari/537.36"
            },
            follow_redirects=False
        )
        
        assert response.status_code == 302
        assert response.headers["location"] == "/auth/login/oidc"

    def test_api_requests_get_json_errors(self, client):
        """Test API requests get JSON errors instead of redirects"""
        # Test API request to /api/cidrs
        response = client.get(
            "/api/cidrs/",
            headers={
                "Accept": "application/json",
                "User-Agent": "curl/7.87.0"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "authorization header" in data["detail"].lower()
        
        # Test API request to /ui (without browser headers)
        response = client.get("/ui")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_oidc_callback_processing(self, client, mock_azure_responses):
        """Test OIDC callback processes authorization code correctly"""
        # Simulate Azure callback with query parameters
        response = client.get("/auth/callback/oidc?code=mock_authorization_code_12345&state=oidc_state")
        
        # Verify callback succeeds
        assert response.status_code == 200
        data = response.json()
        
        # Verify JWT token is returned
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"].lower() == "bearer"
        assert "expires_in" in data
        
        # Verify JWT contains correct user information
        jwt_token = data["access_token"]
        user_info = validate_access_token(jwt_token)
        
        assert user_info.username == "testuser@company.com"
        assert user_info.email == "testuser@company.com"
        assert user_info.is_authenticated == True
        assert "readwrite" in user_info.roles  # Based on group mapping

    def test_authenticated_api_access(self, client, mock_azure_responses):
        """Test API access works with valid JWT from OIDC flow"""
        # First, get JWT token through OIDC callback
        auth_response = client.get("/auth/callback/oidc?code=mock_authorization_code_12345&state=oidc_state")
        assert auth_response.status_code == 200
        
        jwt_token = auth_response.json()["access_token"]
        
        # Test authenticated API access
        headers = {"Authorization": f"Bearer {jwt_token}"}
        
        # Test CIDR list endpoint
        response = client.get("/api/cidrs/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Test user info endpoint
        response = client.get("/auth/user", headers=headers)
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["username"] == "testuser@company.com"
        assert "readwrite" in user_data["roles"]

    def test_oidc_callback_error_handling(self, client):
        """Test OIDC callback error handling"""
        # Test missing code parameter
        response = client.get("/auth/callback/oidc?state=test_state")
        assert response.status_code == 422
        
        # Test missing state parameter
        response = client.get("/auth/callback/oidc?code=test_code")
        assert response.status_code == 422
        
        # Test empty request
        response = client.get("/auth/callback/oidc")
        assert response.status_code == 422

    def test_oidc_role_mapping(self, mock_azure_responses):
        """Test OIDC role mapping from Azure groups to MiniPAM roles"""
        config = {
            "oidc": {
                "client_id": "test-client-id",
                "issuer_url": "https://login.microsoftonline.com/test-tenant-id/v2.0",
                "redirect_uri": "http://localhost:8000/auth/callback/oidc",
                "role_claim": "groups",
                "role_mapping": "minipam-admins:readwrite,minipam-users:readonly",
                "default_role": "readonly"
            }
        }
        
        backend = OIDCBackend(config)
        
        # Test admin user mapping
        admin_claims = {
            "sub": "admin_user_id",
            "preferred_username": "admin@company.com",
            "email": "admin@company.com",
            "groups": ["minipam-admins", "other-group"]
        }
        
        admin_user = backend._map_claims_to_user(admin_claims)
        assert admin_user.username == "admin@company.com"
        assert "readwrite" in admin_user.roles
        assert admin_user.groups == ["minipam-admins", "other-group"]
        
        # Test regular user mapping
        user_claims = {
            "sub": "regular_user_id", 
            "preferred_username": "user@company.com",
            "email": "user@company.com",
            "groups": ["minipam-users"]
        }
        
        regular_user = backend._map_claims_to_user(user_claims)
        assert regular_user.username == "user@company.com"
        assert "readonly" in regular_user.roles
        
        # Test user with no mapped groups (should get default role)
        unmapped_claims = {
            "sub": "unmapped_user_id",
            "preferred_username": "unmapped@company.com", 
            "email": "unmapped@company.com",
            "groups": ["some-other-group"]
        }
        
        unmapped_user = backend._map_claims_to_user(unmapped_claims)
        assert unmapped_user.username == "unmapped@company.com"
        assert "readonly" in unmapped_user.roles  # Default role

    def test_auth_health_endpoint(self, client):
        """Test /auth/health endpoint reports OIDC status"""
        response = client.get("/auth/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["backend"] == "oidc"
        assert data["enabled"] == True
        assert data["configured"] == True

    def test_azure_callback_with_real_authorization_code_format(self, client, mock_azure_responses):
        """Test Azure callback with real Azure authorization code format"""
        # Real Azure authorization code format (anonymized)
        real_azure_code = "1.AToAt0LRM840d0OHDT97Ji23y3FhPvPq_GpNqa73S8GNGhbhAAA6AA.AgABBAIAAABVrSpeuWamRam2jAF1XRQEAwDs_wUA9P9nxbv1EvtvWxx85EcLIoJbX1L7A1MOAadkDtsIsxoyTHaTrjtNcoCyvX_7SSu5cTK9Ys1h2whlu-nx2F20XKOFzN7x1VotgUmQ14aBI4HW32hMfwcuVOmYf96VlHVsZ73gYRyHe-Nzk5e1Z_uUlFyRK-ncbws2SHbJxlm6aoNZ2re6loK_7Ls89FZSSPSZzBaLrkqiZa8y7JrAwSWn2QI9G55Dd3qHmEuauBYBrhY8i0nVXjtkDr6qnhtSFRYrVookIVe5QgHKTpw4miBumhXzQizS6ksAM4wvmX-PTA2FXSKCF42RgsmQR4HGlF-EfiMi3N4yjo2DbwFLjXKWkiwbGY8CaWruUa0MYRJhHARWUNHGpyIXvXl0OFrjemgEDOnfMnlJSAvxRTNCW_5CTKdFVrrz5ncYIACwS3ZnWMQggoXB5bE54kHP9ciY0O0kYDVmF1K1JzRm7GjMnsp7nOv9bLDmqyxs9YaRMRd7c_uo0Y4JZVXuYA-Z0ZktYteyMDZHXcIg3jg_ivI9gwtc2W9r8M-hsvUhEI168DaK0bV9uRtMBO7QQycQEhdKA4jYELWXdmCZgXM_AG2dWV2h-C_fqiy4sPld6XMwT_pIWfAHlVpuafEHlEYuzddHLCwNq64nLc7VtCK1IgIqwDNGdmwjH91xTCt-Cz08Y-PErYVF9i0TbiIMXgz-YYeQgUF6VR7n4XEP7iiokXby6DS8"
        azure_state = "oidc_state"
        session_state = "006cfa89-907b-e0fb-ace9-8c12fb31dbe1"
        
        # Test the actual Azure callback format with GET request
        callback_url = f"/auth/callback/oidc?code={real_azure_code}&state={azure_state}&session_state={session_state}"
        response = client.get(callback_url)
        
        # Verify callback succeeds with real Azure code format
        assert response.status_code == 200
        data = response.json()
        
        # Verify JWT token is returned
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"].lower() == "bearer"
        assert "expires_in" in data
        
        # Verify JWT contains correct user information
        jwt_token = data["access_token"]
        user_info = validate_access_token(jwt_token)
        
        assert user_info.username == "testuser@company.com"
        assert user_info.email == "testuser@company.com"
        assert user_info.is_authenticated == True
        assert "readwrite" in user_info.roles  # Based on group mapping
        
        # Verify the token can be used for API access
        headers = {"Authorization": f"Bearer {jwt_token}"}
        api_response = client.get("/api/cidrs/", headers=headers)
        assert api_response.status_code == 200

    def test_azure_callback_edge_cases(self, client, mock_azure_responses):
        """Test Azure callback edge cases and error handling"""
        # Test with very long authorization code (Azure codes can be quite long)
        long_code = "A" * 2000  # Very long code
        response = client.get(f"/auth/callback/oidc?code={long_code}&state=oidc_state")
        assert response.status_code == 200  # Should handle long codes
        
        # Test with special characters in state (URL encoded)
        special_state = "oidc_state%20with%20spaces"
        response = client.get(f"/auth/callback/oidc?code=test_code&state={special_state}")
        assert response.status_code == 200  # Should handle URL encoded state
        
        # Test with additional Azure parameters (session_state, etc.)
        response = client.get("/auth/callback/oidc?code=test_code&state=oidc_state&session_state=test-session&admin_consent=True")
        assert response.status_code == 200  # Should ignore extra parameters


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])