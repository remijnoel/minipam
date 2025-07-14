#!/usr/bin/env python3
"""
Example usage of MiniPAM authentication

This script demonstrates how to use the MiniPAM authentication system
with different backends (none, apikey, oidc).
"""

import os
import sys
import asyncio
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from minipam.auth import (
    get_auth_manager,
    create_access_token,
    validate_access_token,
    ApiKeyAuthRequest
)


async def test_none_backend():
    """Test the none authentication backend"""
    print("=== Testing None Backend ===")
    
    # Set environment for none backend
    os.environ["MINIPAM_AUTH_BACKEND"] = "none"
    os.environ["MINIPAM_DEFAULT_USERNAME"] = "testuser"
    os.environ["MINIPAM_DEFAULT_ROLE"] = "readwrite"
    
    # Get auth manager and test
    auth_manager = get_auth_manager()
    backend = auth_manager.get_active_backend()
    
    print(f"Active backend: {backend.name}")
    print(f"Enabled: {backend.is_enabled()}")
    print(f"Config: {backend.get_config().dict()}")
    
    # Test authentication (should always succeed)
    from minipam.auth.models import AuthRequest
    user_info = await backend.authenticate(AuthRequest(backend="none"))
    print(f"User info: {user_info.dict()}")
    
    # Test JWT token creation
    token = create_access_token(user_info)
    print(f"Generated token: {token[:50]}...")
    
    # Test token validation
    validated_user = validate_access_token(token)
    print(f"Validated user: {validated_user.dict()}")
    
    print()


async def test_apikey_backend():
    """Test the API key authentication backend"""
    print("=== Testing API Key Backend ===")
    
    # Set environment for API key backend
    os.environ["MINIPAM_AUTH_BACKEND"] = "apikey"
    os.environ["MINIPAM_API_KEY_ALICE"] = "secret123:readwrite"
    os.environ["MINIPAM_API_KEY_BOB"] = "secret456:readonly"
    os.environ["MINIPAM_JWT_SECRET"] = "supersecretjwtkey"
    
    # Reload backends to pick up new config
    auth_manager = get_auth_manager()
    auth_manager.reload_backends()
    backend = auth_manager.get_active_backend()
    
    print(f"Active backend: {backend.name}")
    print(f"Enabled: {backend.is_enabled()}")
    print(f"Config: {backend.get_config().dict()}")
    
    # Test valid API key authentication
    request = ApiKeyAuthRequest(backend="apikey", api_key="secret123")
    user_info = await backend.authenticate(request)
    if user_info:
        print(f"Valid key - User: {user_info.dict()}")
        
        # Test JWT creation
        token = create_access_token(user_info)
        print(f"Generated token for Alice: {token[:50]}...")
        
        # Test permissions
        print(f"Alice can read: {user_info.has_permission('read')}")
        print(f"Alice can write: {user_info.has_permission('write')}")
    
    # Test readonly user
    request = ApiKeyAuthRequest(backend="apikey", api_key="secret456")
    user_info = await backend.authenticate(request)
    if user_info:
        print(f"Bob permissions - read: {user_info.has_permission('read')}, write: {user_info.has_permission('write')}")
    
    # Test invalid API key
    request = ApiKeyAuthRequest(backend="apikey", api_key="invalid")
    user_info = await backend.authenticate(request)
    print(f"Invalid key result: {user_info}")
    
    print()


async def test_auth_api():
    """Test the authentication API endpoints"""
    print("=== Testing Authentication API ===")
    
    # This would normally be done with a running server
    # For now, just show the expected flow
    
    print("API Endpoints available:")
    print("- GET  /auth/config - Get auth configuration")
    print("- POST /auth/login - Authenticate and get token")
    print("- POST /auth/login/apikey - Login with API key")
    print("- GET  /auth/login/oidc - Start OIDC flow")
    print("- POST /auth/callback/oidc - Handle OIDC callback")
    print("- GET  /auth/user - Get current user info")
    print("- POST /auth/logout - Logout (client-side)")
    print("- GET  /auth/health - Check auth system health")
    
    print("\nExample API usage:")
    print("1. Get auth config: curl http://localhost:8000/auth/config")
    print("2. Login with API key: curl -X POST http://localhost:8000/auth/login/apikey -d 'secret123'")
    print("3. Use token: curl -H 'Authorization: Bearer <token>' http://localhost:8000/api/cidrs")
    
    print()


def main():
    """Main example function"""
    print("MiniPAM Authentication System Examples")
    print("=" * 50)
    
    asyncio.run(test_none_backend())
    asyncio.run(test_apikey_backend())
    asyncio.run(test_auth_api())
    
    print("Environment variables used:")
    auth_vars = {k: v for k, v in os.environ.items() if k.startswith("MINIPAM_")}
    for key, value in sorted(auth_vars.items()):
        # Mask sensitive values
        if "SECRET" in key or "KEY" in key:
            masked_value = f"{value[:6]}..." if len(value) > 6 else "***"
            print(f"  {key}={masked_value}")
        else:
            print(f"  {key}={value}")


if __name__ == "__main__":
    main()
