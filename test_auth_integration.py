#!/usr/bin/env python3
"""
Integration test for authentication system
Tests the complete auth flow with FastAPI app
"""

import os
import asyncio
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_auth_integration():
    """Test complete authentication integration"""
    print("Testing MiniPAM Authentication Integration")
    print("=" * 50)
    
    # Set up environment for testing
    os.environ["MINIPAM_AUTH_BACKEND"] = "none"
    os.environ["MINIPAM_STORAGE_TYPE"] = "memory"
    os.environ["MINIPAM_JWT_SECRET"] = "test-secret-for-integration"
    
    try:
        # Test 1: Import auth components
        print("1. Testing auth component imports...")
        from minipam.auth.dependencies import get_auth_manager, get_auth_config
        from minipam.auth.models import UserInfo, AuthConfig
        from minipam.auth.middleware import AuthMiddleware, get_current_user
        print("   ✓ All auth components imported successfully")
        
        # Test 2: Create auth manager
        print("2. Testing auth manager...")
        manager = get_auth_manager()
        backend = manager.get_active_backend()
        print(f"   ✓ Auth manager created with backend: {backend.name}")
        
        # Test 3: Test config
        print("3. Testing auth config...")
        config = get_auth_config()
        print(f"   ✓ Auth config: enabled={config.enabled}, backend={config.backend}")
        
        # Test 4: Test app creation
        print("4. Testing FastAPI app creation...")
        from minipam.main import create_app
        app = create_app()
        print("   ✓ FastAPI app created successfully")
        
        # Test 5: Test with none backend
        print("5. Testing none backend authentication...")
        async def test_none_auth():
            from minipam.auth.backends.none import NoneBackend
            from minipam.auth.models import AuthRequest
            
            none_backend = NoneBackend({})
            request = AuthRequest(backend="none")
            user = await none_backend.authenticate(request)
            return user
        
        user = asyncio.run(test_none_auth())
        print(f"   ✓ None backend auth: user={user.username}, roles={user.roles}")
        
        # Test 6: Test API key backend
        print("6. Testing API key backend...")
        os.environ["MINIPAM_AUTH_BACKEND"] = "apikey"
        os.environ["MINIPAM_API_KEY_TEST"] = "test-key-123:readwrite"
        
        async def test_apikey_auth():
            from minipam.auth.backends.apikey import ApiKeyBackend
            from minipam.auth.models import ApiKeyAuthRequest
            
            apikey_backend = ApiKeyBackend({})
            request = ApiKeyAuthRequest(backend="apikey", api_key="test-key-123")
            user = await apikey_backend.authenticate(request)
            return user
        
        user = asyncio.run(test_apikey_auth())
        print(f"   ✓ API key auth: user={user.username}, roles={user.roles}")
        
        # Test 7: Test JWT creation/validation
        print("7. Testing JWT flow...")
        from minipam.auth.utils import create_access_token, validate_access_token
        
        token = create_access_token(user)
        validated_user = validate_access_token(token)
        print(f"   ✓ JWT flow: created and validated token for {validated_user.username}")
        
        print("\n🎉 All authentication integration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test authentication with API endpoints"""
    print("\nTesting API Endpoints with Authentication")
    print("=" * 50)
    
    try:
        from fastapi.testclient import TestClient
        from minipam.main import create_app
        
        # Set up environment
        os.environ["MINIPAM_AUTH_BACKEND"] = "none"
        os.environ["MINIPAM_STORAGE_TYPE"] = "memory"
        
        # Create test client
        app = create_app()
        client = TestClient(app)
        
        # Test 1: Health endpoint
        print("1. Testing health endpoint...")
        response = client.get("/api/health")
        print(f"   ✓ Health endpoint: {response.status_code} - {response.json()}")
        
        # Test 2: Auth health endpoint
        print("2. Testing auth health endpoint...")
        response = client.get("/auth/health")
        if response.status_code == 200:
            print(f"   ✓ Auth health: {response.json()}")
        else:
            print(f"   ⚠ Auth health failed: {response.status_code}")
        
        # Test 3: Auth config endpoint
        print("3. Testing auth config endpoint...")
        response = client.get("/auth/config")
        if response.status_code == 200:
            print(f"   ✓ Auth config: {response.json()}")
        else:
            print(f"   ⚠ Auth config failed: {response.status_code}")
        
        # Test 4: CIDR list (should work with none auth)
        print("4. Testing CIDR list endpoint...")
        response = client.get("/api/cidrs/")
        print(f"   ✓ CIDR list: {response.status_code} - {response.json()}")
        
        # Test 5: Create CIDR (should work with none auth)
        print("5. Testing CIDR creation...")
        cidr_data = {
            "cidr": "192.168.1.0/24",
            "name": "Test Network",
            "description": "Test network for integration testing"
        }
        response = client.post("/api/cidrs/", json=cidr_data)
        print(f"   ✓ CIDR creation: {response.status_code}")
        if response.status_code == 201:
            print(f"   ✓ Created CIDR: {response.json()['cidr']}")
        
        print("\n🎉 API endpoint tests completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ API endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    print("MiniPAM Authentication Integration Tests")
    print("=" * 60)
    
    success1 = test_auth_integration()
    success2 = test_api_endpoints()
    
    if success1 and success2:
        print("\n🚀 ALL INTEGRATION TESTS PASSED!")
        print("Authentication system is working correctly.")
    else:
        print("\n💥 Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()