"""
Authentication models for MiniPAM

Defines data structures for user information and authentication configuration.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    """User information extracted from authentication"""
    
    username: str = Field(..., description="Unique username")
    email: Optional[str] = Field(None, description="User email address")
    roles: List[str] = Field(default_factory=list, description="User roles (readonly, readwrite)")
    groups: List[str] = Field(default_factory=list, description="User groups from identity provider")
    is_authenticated: bool = Field(True, description="Whether user is authenticated")
    
    @property
    def permissions(self) -> List[str]:
        """Convert roles to permissions"""
        perms = []
        if "readonly" in self.roles or "readwrite" in self.roles:
            perms.append("read")
        if "readwrite" in self.roles:
            perms.append("write")
        return perms
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions


class AuthRequest(BaseModel):
    """Base authentication request"""
    backend: str = Field(..., description="Authentication backend name")


class ApiKeyAuthRequest(AuthRequest):
    """API key authentication request"""
    api_key: str = Field(..., description="API key for authentication")


class OIDCAuthRequest(AuthRequest):
    """OIDC authentication request"""
    code: str = Field(..., description="Authorization code from OIDC provider")
    state: str = Field(..., description="State parameter for CSRF protection")


class AuthResponse(BaseModel):
    """Authentication response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")
    user: UserInfo = Field(..., description="Authenticated user information")


class AuthConfig(BaseModel):
    """Authentication configuration response"""
    enabled: bool = Field(..., description="Whether authentication is enabled")
    backend: Optional[str] = Field(None, description="Active authentication backend")
    login_url: Optional[str] = Field(None, description="Login URL for browser flows")
    supports_browser_flow: bool = Field(True, description="Whether backend supports browser login")


class AuthError(BaseModel):
    """Authentication error response"""
    error: str = Field(..., description="Error code")
    error_description: str = Field(..., description="Human-readable error description")
    error_code: Optional[str] = Field(None, description="Internal error code")


class JWTPayload(BaseModel):
    """JWT token payload structure"""
    sub: str = Field(..., description="Subject (username)")
    email: Optional[str] = Field(None, description="User email")
    roles: List[str] = Field(default_factory=list, description="User roles")
    iat: int = Field(..., description="Issued at timestamp")
    exp: int = Field(..., description="Expiration timestamp")
    iss: str = Field("minipam", description="Issuer")
    
    @classmethod
    def from_user_info(cls, user_info: UserInfo, iat: int, exp: int) -> "JWTPayload":
        """Create JWT payload from user info"""
        return cls(
            sub=user_info.username,
            email=user_info.email,
            roles=user_info.roles,
            iat=iat,
            exp=exp,
            iss="minipam"
        )
    
    def to_user_info(self) -> UserInfo:
        """Convert JWT payload to user info"""
        return UserInfo(
            username=self.sub,
            email=self.email,
            roles=self.roles,
            is_authenticated=True
        )
