#!/usr/bin/env python3
"""
Simple test of MiniPAM authentication components
"""

import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_auth_models():
    """Test authentication models"""
    print("=== Testing Auth Models ===")
    
    from minipam.auth.models import UserInfo, JWTPayload, AuthConfig
    
    # Test UserInfo
    user = UserInfo(
        username="testuser",
        email="test@example.com",
        roles=["readwrite"],
        is_authenticated=True
    )
    
    print(f"User: {user.username}")
    print(f"Permissions: {user.permissions}")
    print(f"Can read: {user.has_permission('read')}")
    print(f"Can write: {user.has_permission('write')}")
    
    # Test JWT payload conversion
    payload = JWTPayload.from_user_info(user, 1234567890, 1234567890 + 3600)
    print(f"JWT payload: {payload.dict()}")
    
    # Convert back to user
    user2 = payload.to_user_info()
    print(f"Converted back: {user2.username}, roles: {user2.roles}")
    
    print()


def test_jwt_utils():
    """Test JWT utilities"""
    print("=== Testing JWT Utils ===")
    
    # Set required environment
    os.environ["MINIPAM_JWT_SECRET"] = "test-secret-key"
    
    from minipam.auth.utils import JWTHandler
    from minipam.auth.models import UserInfo
    
    # Create JWT handler
    handler = JWTHandler()
    print(f"JWT Algorithm: {handler.algorithm}")
    print(f"JWT Issuer: {handler.issuer}")
    
    # Create user
    user = UserInfo(
        username="alice",
        email="alice@example.com",
        roles=["readwrite"],
        is_authenticated=True
    )
    
    # Create token
    token = handler.create_token(user)
    print(f"Created token: {token[:50]}...")
    
    # Validate token
    validated_user = handler.validate_token(token)
    print(f"Validated user: {validated_user.username}")
    print(f"Validated roles: {validated_user.roles}")
    
    print()


def test_none_backend():
    """Test none backend"""
    print("=== Testing None Backend ===")
    
    os.environ["MINIPAM_AUTH_BACKEND"] = "none"
    os.environ["MINIPAM_DEFAULT_USERNAME"] = "admin"
    os.environ["MINIPAM_DEFAULT_ROLE"] = "readwrite"
    
    from minipam.auth.backends.none import NoneBackend
    from minipam.auth.models import AuthRequest
    
    backend = NoneBackend({})
    print(f"Backend name: {backend.name}")
    print(f"Is enabled: {backend.is_enabled()}")
    
    # Test authentication
    import asyncio
    async def test_auth():
        request = AuthRequest(backend="none")
        user = await backend.authenticate(request)
        return user
    
    user = asyncio.run(test_auth())
    print(f"Authenticated user: {user.username}")
    print(f"User roles: {user.roles}")
    
    print()


def test_apikey_backend():
    """Test API key backend"""
    print("=== Testing API Key Backend ===")
    
    os.environ["MINIPAM_AUTH_BACKEND"] = "apikey"
    os.environ["MINIPAM_API_KEY_ALICE"] = "secret123:readwrite"
    os.environ["MINIPAM_API_KEY_BOB"] = "secret456:readonly"
    
    from minipam.auth.backends.apikey import ApiKeyBackend
    from minipam.auth.models import ApiKeyAuthRequest
    
    backend = ApiKeyBackend({})
    print(f"Backend name: {backend.name}")
    print(f"Is enabled: {backend.is_enabled()}")
    print(f"Configured users: {backend.get_configured_users()}")
    
    # Test authentication
    import asyncio
    async def test_auth():
        # Valid key
        request = ApiKeyAuthRequest(backend="apikey", api_key="secret123")
        user = await backend.authenticate(request)
        print(f"Valid key - User: {user.username if user else 'None'}")
        
        # Invalid key
        request = ApiKeyAuthRequest(backend="apikey", api_key="invalid")
        user = await backend.authenticate(request)
        print(f"Invalid key - User: {user}")
    
    asyncio.run(test_auth())
    
    print()


def main():
    """Run all tests"""
    print("MiniPAM Authentication System Tests")
    print("=" * 50)
    
    try:
        test_auth_models()
        test_jwt_utils()
        test_none_backend()
        test_apikey_backend()
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
