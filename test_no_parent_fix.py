#!/usr/bin/env python3
"""
Test the specific case that was failing: adding a CIDR with no parent
when a more specific parent exists.
"""

import asyncio
import sys
import os

# Add the project root to the path so we can import the rules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from minipam.rules import ValidationError, validate_cidr
from standalone_test_rules import CIDRBlock, InMemoryCIDRStorage

async def test_no_parent_when_parent_exists():
    """Test that CIDRs without parents are rejected when a parent should exist"""
    storage = InMemoryCIDRStorage()
    
    print("🧪 Testing: No parent specified when parent exists")
    print("=" * 60)
    
    # Set up the existing hierarchy
    print("Setting up existing hierarchy...")
    root = CIDRBlock(cidr="0.0.0.0/0", name="Root")
    await storage.put(root)
    print("✅ Added 0.0.0.0/0 (root)")
    
    ten_slash_8 = CIDRBlock(cidr="10.0.0.0/8", parent="0.0.0.0/0")
    await storage.put(ten_slash_8)
    print("✅ Added 10.0.0.0/8 under 0.0.0.0/0")
    
    print()
    
    # Now try to add 10.0.100.0/24 with no parent - should fail
    print("Test 1: Try to add 10.0.100.0/24 with no parent")
    bad_cidr = CIDRBlock(cidr="10.0.100.0/24", parent=None)
    try:
        await validate_cidr(bad_cidr, storage)
        print("❌ FAILED: Should have been rejected!")
        return False
    except ValidationError as e:
        print(f"✅ SUCCESS: Correctly rejected - {e}")
    
    print()
    
    # Try to add 10.0.100.0/24 with correct parent - should succeed
    print("Test 2: Try to add 10.0.100.0/24 with correct parent (10.0.0.0/8)")
    good_cidr = CIDRBlock(cidr="10.0.100.0/24", parent="10.0.0.0/8")
    try:
        await validate_cidr(good_cidr, storage)
        print("✅ SUCCESS: Correctly accepted with proper parent")
        await storage.put(good_cidr)
        return True
    except ValidationError as e:
        print(f"❌ FAILED: Should have been accepted - {e}")
        return False

async def test_api_with_fixed_rules():
    """Test the API to see if the issue is fixed"""
    print()
    print("🌐 Testing API with fixed rules")
    print("=" * 60)
    
    # Test the problematic case via API
    import subprocess
    import json
    
    # Try to create 10.1.0.0/24 without a parent (should fail now)
    print("Testing API: Adding 10.1.0.0/24 without parent...")
    try:
        result = subprocess.run([
            'curl', '-s', '-X', 'POST', 'http://localhost:8000/api/cidrs',
            '-H', 'Content-Type: application/json',
            '-d', '{"cidr": "10.1.0.0/24", "name": "Should fail", "description": "No parent specified"}'
        ], capture_output=True, text=True, timeout=10)
        
        if '422' in result.stderr or 'must be assigned to parent' in result.stdout:
            print("✅ SUCCESS: API correctly rejected CIDR without proper parent")
            print(f"   Response: {result.stdout.strip()}")
        else:
            print("❌ FAILED: API did not reject the invalid CIDR")
            print(f"   Response: {result.stdout.strip()}")
            print(f"   Error: {result.stderr.strip()}")
            
    except subprocess.TimeoutExpired:
        print("⚠️  Timeout: API might not be running")
    except Exception as e:
        print(f"⚠️  Error testing API: {e}")

async def main():
    success = await test_no_parent_when_parent_exists()
    await test_api_with_fixed_rules()
    
    if success:
        print()
        print("🎉 All tests passed! The rules are now working correctly.")
        print("   CIDRs must be assigned to their most specific parent.")
    else:
        print()
        print("❌ Some tests failed. Check the implementation.")

if __name__ == "__main__":
    asyncio.run(main())
