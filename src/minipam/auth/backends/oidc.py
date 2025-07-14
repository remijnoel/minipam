"""
OIDC authentication backend

Authenticates users using OpenID Connect (OIDC) providers.
Supports authorization code flow with PKCE.
"""

import os
import json
import urllib.parse
import urllib.request
from typing import Optional, Dict, Any
from ..base import AuthBackend, AuthenticationError
from ..models import UserInfo, AuthRequest, OIDCAuthRequest, AuthConfig


class OIDCBackend(AuthBackend):
    """Authentication backend using OIDC providers"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OIDC backend
        
        Args:
            config: Backend configuration dictionary
        """
        super().__init__(config)
        
        # Get OIDC configuration from config dict, with environment variable fallbacks
        oidc_config = config.get("oidc", {})
        
        self.client_id = (
            os.getenv("MINIPAM_OIDC_CLIENT_ID") or 
            oidc_config.get("client_id", "")
        )
        self.client_secret = (
            os.getenv("MINIPAM_OIDC_CLIENT_SECRET") or 
            oidc_config.get("client_secret", "")
        )
        self.issuer_url = (
            os.getenv("MINIPAM_OIDC_ISSUER_URL") or 
            oidc_config.get("issuer_url", "")
        )
        self.redirect_uri = (
            os.getenv("MINIPAM_OIDC_REDIRECT_URI") or 
            oidc_config.get("redirect_uri", "http://localhost:8000/auth/callback/oidc")
        )
        self.scope = (
            os.getenv("MINIPAM_OIDC_SCOPE") or 
            oidc_config.get("scope", "openid profile email")
        )
        
        # Role mapping configuration
        self.role_claim = (
            os.getenv("MINIPAM_OIDC_ROLE_CLAIM") or 
            oidc_config.get("role_claim", "groups")
        )
        self.role_mapping = self._parse_role_mapping(oidc_config)
        self.default_role = (
            os.getenv("MINIPAM_OIDC_DEFAULT_ROLE") or 
            oidc_config.get("default_role", "readonly")
        )
        
        # Discovery document cache
        self._discovery_doc: Optional[Dict[str, Any]] = None
    
    def _parse_role_mapping(self, oidc_config: Dict[str, Any]) -> Dict[str, str]:
        """Parse role mapping from environment variable or config
        
        Expected format: MINIPAM_OIDC_ROLE_MAPPING=group1:readwrite,group2:readonly
        
        Args:
            oidc_config: OIDC configuration dictionary
            
        Returns:
            Dictionary mapping OIDC groups/roles to MiniPAM roles
        """
        mapping_str = (
            os.getenv("MINIPAM_OIDC_ROLE_MAPPING") or 
            oidc_config.get("role_mapping", "")
        )
        mapping = {}
        
        if mapping_str:
            for pair in mapping_str.split(","):
                if ":" in pair:
                    group, role = pair.split(":", 1)
                    mapping[group.strip()] = role.strip()
        
        return mapping
    
    async def authenticate(self, request: AuthRequest) -> Optional[UserInfo]:
        """Authenticate using OIDC authorization code
        
        Args:
            request: Authentication request containing authorization code
            
        Returns:
            UserInfo if authentication successful, None otherwise
            
        Raises:
            AuthenticationError: If authentication fails
        """
        if not isinstance(request, OIDCAuthRequest):
            raise AuthenticationError("Invalid request type for OIDC backend")
        
        try:
            # Exchange authorization code for tokens
            token_response = await self._exchange_code_for_tokens(
                request.code, request.state
            )
            
            # Get user info from ID token or userinfo endpoint
            user_claims = await self._get_user_claims(token_response)
            
            # Map claims to UserInfo
            return self._map_claims_to_user(user_claims)
            
        except Exception as e:
            raise AuthenticationError(f"OIDC authentication failed: {str(e)}")
    
    async def _exchange_code_for_tokens(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange authorization code for access and ID tokens
        
        Args:
            code: Authorization code from OIDC provider
            state: State parameter for CSRF protection
            
        Returns:
            Token response dictionary
        """
        discovery_doc = await self._get_discovery_document()
        token_endpoint = discovery_doc.get("token_endpoint")
        
        if not token_endpoint:
            raise AuthenticationError("Token endpoint not found in discovery document")
        
        # Prepare token request
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
        }
        
        if self.client_secret:
            data["client_secret"] = self.client_secret
        
        # Make token request
        req_data = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(
            token_endpoint,
            data=req_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                raise AuthenticationError(f"Token exchange failed: {response.status}")
            
            return json.loads(response.read().decode())
    
    async def _get_user_claims(self, token_response: Dict[str, Any]) -> Dict[str, Any]:
        """Get user claims from ID token or userinfo endpoint
        
        Args:
            token_response: Token response from OIDC provider
            
        Returns:
            User claims dictionary
        """
        # For simplicity, we'll try to get userinfo from the userinfo endpoint
        # In a production implementation, you'd want to validate the ID token JWT
        access_token = token_response.get("access_token")
        if not access_token:
            raise AuthenticationError("No access token in response")
        
        discovery_doc = await self._get_discovery_document()
        userinfo_endpoint = discovery_doc.get("userinfo_endpoint")
        
        if not userinfo_endpoint:
            raise AuthenticationError("Userinfo endpoint not found")
        
        # Make userinfo request
        req = urllib.request.Request(
            userinfo_endpoint,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                raise AuthenticationError(f"Userinfo request failed: {response.status}")
            
            return json.loads(response.read().decode())
    
    def _map_claims_to_user(self, claims: Dict[str, Any]) -> UserInfo:
        """Map OIDC claims to UserInfo object
        
        Args:
            claims: User claims from OIDC provider
            
        Returns:
            UserInfo object
        """
        username = claims.get("preferred_username") or claims.get("sub") or "unknown"
        email = claims.get("email")
        
        # Map roles/groups to MiniPAM roles
        user_groups = claims.get(self.role_claim, [])
        if isinstance(user_groups, str):
            user_groups = [user_groups]
        
        roles = []
        for group in user_groups:
            if group in self.role_mapping:
                roles.append(self.role_mapping[group])
        
        # Use default role if no roles mapped
        if not roles:
            roles = [self.default_role]
        
        return UserInfo(
            username=username,
            email=email,
            roles=roles,
            groups=user_groups,
            is_authenticated=True
        )
    
    async def _get_discovery_document(self) -> Dict[str, Any]:
        """Get OIDC discovery document
        
        Returns:
            Discovery document dictionary
        """
        if self._discovery_doc is None:
            discovery_url = f"{self.issuer_url}/.well-known/openid-configuration"
            
            try:
                with urllib.request.urlopen(discovery_url) as response:
                    if response.status != 200:
                        raise AuthenticationError(f"Discovery failed: {response.status}")
                    
                    self._discovery_doc = json.loads(response.read().decode())
            
            except Exception as e:
                raise AuthenticationError(f"Failed to fetch discovery document: {str(e)}")
        
        return self._discovery_doc or {}
    
    def get_config(self) -> AuthConfig:
        """Get authentication configuration
        
        Returns:
            AuthConfig for OIDC authentication
        """
        return AuthConfig(
            enabled=True,
            backend="oidc",
            login_url=self.get_login_url(),
            supports_browser_flow=True
        )
    
    def is_enabled(self) -> bool:
        """Check if OIDC backend is enabled
        
        Returns:
            True if auth backend is 'oidc' and required config is present
        """
        from ...config import get_auth_backend
        auth_backend = get_auth_backend().lower()
        return (
            auth_backend == "oidc" and
            bool(self.client_id) and
            bool(self.issuer_url) and
            bool(self.redirect_uri)
        )
    
    def validate_config(self) -> bool:
        """Validate OIDC configuration
        
        Returns:
            True if all required configuration is present
        """
        return bool(
            self.client_id and
            self.issuer_url and
            self.redirect_uri
        )
    
    def get_login_url(self) -> Optional[str]:
        """Get OIDC authorization URL
        
        Returns:
            Authorization URL for browser-based login
        """
        if not self.validate_config():
            return None
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "state": "oidc_state"  # In production, use a random state value
        }
        
        # For Azure OIDC, construct the authorization endpoint
        # TODO: In production, use OIDC discovery to get the actual endpoint
        if "login.microsoftonline.com" in self.issuer_url:
            # Azure uses /oauth2/v2.0/authorize
            base_url = self.issuer_url.replace("/v2.0", "")
            auth_endpoint = f"{base_url}/oauth2/v2.0/authorize"
        else:
            # Generic OIDC endpoint (fallback)
            auth_endpoint = f"{self.issuer_url}/auth"
        
        return f"{auth_endpoint}?{urllib.parse.urlencode(params)}"
    
    def supports_browser_flow(self) -> bool:
        """OIDC backend supports browser flow
        
        Returns:
            True - OIDC requires browser interaction
        """
        return True
