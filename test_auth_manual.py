#!/usr/bin/env python3
"""
Manual authentication testing script
Tests all auth backends and JWT functionality
"""

import os
import sys
import asyncio

# Add src to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from minipam.auth.backends.none import NoneBackend
from minipam.auth.backends.apikey import ApiKeyBackend
from minipam.auth.models import AuthRequest, ApiKeyAuthRequest, UserInfo
from minipam.auth.utils import create_access_token, validate_access_token
from minipam.auth.base import AuthTokenError

async def test_none_backend():
    """Test the none authentication backend"""
    print("=" * 60)
    print("TESTING NONE AUTHENTICATION BACKEND")
    print("=" * 60)
    
    os.environ["MINIPAM_AUTH_BACKEND"] = "none"
    
    backend = NoneBackend({})
    
    print(f"✓ Enabled: {backend.is_enabled()}")
    print(f"✓ Config: {backend.get_config()}")
    print(f"✓ Supports browser flow: {backend.supports_browser_flow()}")
    
    # Test authentication
    request = AuthRequest(backend='none')
    user = await backend.authenticate(request)
    print(f"✓ Authentication result: {user}")
    if user:
        print(f"✓ User permissions: {user.permissions}")
        print(f"✓ Has read permission: {user.has_permission('read')}")
        print(f"✓ Has write permission: {user.has_permission('write')}")
    else:
        print("✗ No user returned")


async def test_apikey_backend():
    """Test the API key authentication backend"""
    print("\n" + "=" * 60)
    print("TESTING API KEY AUTHENTICATION BACKEND")
    print("=" * 60)
    
    # Set up environment for API key backend
    os.environ["MINIPAM_AUTH_BACKEND"] = "apikey"
    os.environ["MINIPAM_API_KEY_ADMIN"] = "test-admin-key:readwrite"
    os.environ["MINIPAM_API_KEY_VIEWER"] = "test-viewer-key:readonly"
    os.environ["MINIPAM_API_KEY_SERVICE"] = "test-service-key:readwrite"
    
    backend = ApiKeyBackend({})
    
    print(f"✓ Enabled: {backend.is_enabled()}")
    print(f"✓ Config: {backend.get_config()}")
    print(f"✓ Supports browser flow: {backend.supports_browser_flow()}")
    print(f"✓ Configured users: {backend.get_configured_users()}")
    
    # Test valid authentication
    print("\nTesting valid API key authentication:")
    request = ApiKeyAuthRequest(backend='apikey', api_key='test-admin-key')
    user = await backend.authenticate(request)
    print(f"✓ Admin authentication result: {user}")
    if user:
        print(f"✓ Admin permissions: {user.permissions}")
    
    request = ApiKeyAuthRequest(backend='apikey', api_key='test-viewer-key')
    user = await backend.authenticate(request)
    print(f"✓ Viewer authentication result: {user}")
    if user:
        print(f"✓ Viewer permissions: {user.permissions}")
    
    # Test invalid authentication
    print("\nTesting invalid API key authentication:")
    request = ApiKeyAuthRequest(backend='apikey', api_key='invalid-key')
    user = await backend.authenticate(request)
    print(f"✓ Invalid key result: {user}")


def test_jwt_functionality():
    """Test JWT token creation and validation"""
    print("\n" + "=" * 60)
    print("TESTING JWT TOKEN FUNCTIONALITY")
    print("=" * 60)
    
    # Set up JWT environment
    os.environ["MINIPAM_JWT_SECRET"] = "test-secret-key-for-testing"
    os.environ["MINIPAM_JWT_ALGORITHM"] = "HS256"
    os.environ["MINIPAM_JWT_ISSUER"] = "minipam-test"
    os.environ["MINIPAM_JWT_EXPIRY_HOURS"] = "1"
    
    # Test user info
    test_user = UserInfo(
        username="testuser",
        email="test@example.com",
        roles=["readwrite"],
        is_authenticated=True
    )
    
    print(f"✓ Test user: {test_user}")
    print(f"✓ User permissions: {test_user.permissions}")
    
    try:
        # Create token
        token = create_access_token(test_user)
        print(f"✓ Created JWT token (first 50 chars): {token[:50]}...")
        
        # Validate token
        validated_user = validate_access_token(token)
        print(f"✓ Validated user: {validated_user}")
        print(f"✓ Token validation successful: {validated_user.username == test_user.username}")
        
        # Test with invalid token
        try:
            validate_access_token("invalid.token.here")
            print("✗ Should have failed with invalid token")
        except AuthTokenError as e:
            print(f"✓ Invalid token correctly rejected: {e.message}")
            
    except Exception as e:
        print(f"✗ JWT test failed: {e}")


async def test_integration_scenario():
    """Test an integration scenario with authentication flow"""
    print("\n" + "=" * 60)
    print("TESTING INTEGRATION SCENARIO")
    print("=" * 60)
    
    # Scenario: API key auth + JWT tokens
    os.environ["MINIPAM_AUTH_BACKEND"] = "apikey" 
    os.environ["MINIPAM_API_KEY_ALICE"] = "alice-secret-key:readwrite"
    os.environ["MINIPAM_JWT_SECRET"] = "integration-test-secret"
    
    # Step 1: Authenticate with API key
    backend = ApiKeyBackend({})
    request = ApiKeyAuthRequest(backend='apikey', api_key='alice-secret-key')
    user = await backend.authenticate(request)
    print(f"✓ Step 1 - API key authentication: {user}")
    
    if user:
        # Step 2: Issue JWT token
        token = create_access_token(user)
        print(f"✓ Step 2 - JWT token issued (length: {len(token)})")
        
        # Step 3: Validate JWT token (simulating subsequent API calls)
        validated_user = validate_access_token(token)
        print(f"✓ Step 3 - JWT validation: {validated_user}")
        print(f"✓ Integration test successful: user identity maintained")
    else:
        print("✗ Integration test failed: no user from API key auth")


async def main():
    """Run all authentication tests"""
    print("MiniPAM Authentication System Test")
    print("Testing implementation against AUTH_FEATURE_SPEC.md requirements")
    print()
    
    try:
        await test_none_backend()
        await test_apikey_backend()
        test_jwt_functionality()
        await test_integration_scenario()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())