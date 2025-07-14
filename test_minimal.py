#!/usr/bin/env python3
"""
Ultra-minimal test of MiniPAM auth components
"""

import sys
import os
from pathlib import Path

# Add src directory to path
auth_path = Path(__file__).parent / "src" / "minipam" / "auth"
sys.path.insert(0, str(auth_path))

def test_models():
    print("=== Testing Auth Models (Direct Import) ===")
    
    # Import models directly
    from models import UserInfo, JWTPayload
    
    # Test UserInfo
    user = UserInfo(
        username="testuser",
        email="test@example.com", 
        roles=["readwrite"],
        is_authenticated=True
    )
    
    print(f"✅ User: {user.username}")
    print(f"✅ Permissions: {user.permissions}")
    print(f"✅ Can read: {user.has_permission('read')}")
    print(f"✅ Can write: {user.has_permission('write')}")
    
    # Test JWT payload
    payload = JWTPayload.from_user_info(user, 1234567890, 1234567890 + 3600)
    print(f"✅ JWT payload sub: {payload.sub}")
    
    user2 = payload.to_user_info()
    print(f"✅ Roundtrip user: {user2.username}")
    
    print()

def test_jwt():
    print("=== Testing JWT Utils (Direct Import) ===")
    
    os.environ["MINIPAM_JWT_SECRET"] = "test-secret"
    
    from utils import JWTHandler
    from models import UserInfo
    
    handler = JWTHandler()
    print(f"✅ JWT handler created: {handler.algorithm}")
    
    user = UserInfo(username="alice", roles=["readwrite"], is_authenticated=True)
    token = handler.create_token(user)
    print(f"✅ Token created: {len(token)} chars")
    
    validated = handler.validate_token(token)
    print(f"✅ Token validated: {validated.username}")
    
    print()

def main():
    print("MiniPAM Auth - Minimal Direct Test")
    print("=" * 40)
    
    try:
        test_models()
        test_jwt()
        print("🎉 Basic auth components working!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
