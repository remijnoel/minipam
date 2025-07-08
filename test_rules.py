"""
Test script for CIDR validation rules
"""

import asyncio
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("minipam.test_rules")

# Add the parent directory to the path so we can import the module
sys.path.insert(0, ".")


async def test_rules():
    """Test the CIDR validation rules"""
    from src.minipam.models import CIDRBlock
    from src.minipam.rules import ValidationError, validate_cidr
    from src.minipam.storage import InMemoryCIDRStorage

    # Create a storage backend
    storage = InMemoryCIDRStorage()

    print("\n===== Testing CIDR Validation Rules =====\n")

    # Test 1: Create a root CIDR
    print("Test 1: Create a root CIDR (0.0.0.0/0)")
    root = CIDRBlock(
        cidr="0.0.0.0/0", name="Root", description="Root CIDR", parent=None
    )
    try:
        await validate_cidr(root, storage)
        await storage.put(root)
        print("✅ Success: Root CIDR created")
    except ValidationError as e:
        print(f"❌ Error: {e}")

    # Test 2: Create a duplicate CIDR (should fail)
    print("\nTest 2: Create a duplicate CIDR (0.0.0.0/0)")
    duplicate = CIDRBlock(
        cidr="0.0.0.0/0", name="Duplicate Root", description="Should fail", parent=None
    )
    try:
        await validate_cidr(duplicate, storage)
        await storage.put(duplicate)
        print("❌ Failed: Duplicate CIDR was allowed")
    except ValidationError as e:
        print(f"✅ Success: Caught error - {e}")

    # Test 3: Create a proper hierarchy
    print("\nTest 3: Create a proper hierarchy (10.0.0.0/8 under 0.0.0.0/0)")
    block1 = CIDRBlock(
        cidr="10.0.0.0/8",
        name="RFC1918 - Class A",
        description="Private Address Space",
        parent="0.0.0.0/0",
    )
    try:
        await validate_cidr(block1, storage)
        await storage.put(block1)
        print("✅ Success: Created 10.0.0.0/8 under 0.0.0.0/0")
    except ValidationError as e:
        print(f"❌ Error: {e}")

    # Test 4: Create a proper sub-hierarchy
    print("\nTest 4: Create a proper sub-hierarchy (10.0.0.0/16 under 10.0.0.0/8)")
    block2 = CIDRBlock(
        cidr="10.0.0.0/16",
        name="Class B in 10/8",
        description="Network subdivision",
        parent="10.0.0.0/8",
    )
    try:
        await validate_cidr(block2, storage)
        await storage.put(block2)
        print("✅ Success: Created 10.0.0.0/16 under 10.0.0.0/8")
    except ValidationError as e:
        print(f"❌ Error: {e}")

    # Test 5: Create with wrong parent - should fail smallest parent rule
    print("\nTest 5: Create with wrong parent (10.0.1.0/24 directly under 0.0.0.0/0)")
    block3 = CIDRBlock(
        cidr="10.0.1.0/24",
        name="Invalid Parent",
        description="Should fail - wrong parent",
        parent="0.0.0.0/0",
    )
    try:
        await validate_cidr(block3, storage)
        await storage.put(block3)
        print("❌ Failed: Allowed incorrect parent hierarchy")
    except ValidationError as e:
        print(f"✅ Success: Caught error - {e}")

    # Test 6: Create with correct parent after previous failure
    print("\nTest 6: Create with correct parent (10.0.1.0/24 under 10.0.0.0/8)")
    block4 = CIDRBlock(
        cidr="10.0.1.0/24",
        name="Proper Parent",
        description="Correct parent assignment",
        parent="10.0.0.0/8",
    )
    try:
        await validate_cidr(block4, storage)
        await storage.put(block4)
        print("✅ Success: Created 10.0.1.0/24 under 10.0.0.0/8")
    except ValidationError as e:
        print(f"❌ Error: {e}")

    # Test 7: Create with most specific parent
    print("\nTest 7: Create with most specific parent (10.0.0.0/24 under 10.0.0.0/16)")
    block5 = CIDRBlock(
        cidr="10.0.0.0/24",
        name="Specific Parent",
        description="Child of /16",
        parent="10.0.0.0/16",
    )
    try:
        await validate_cidr(block5, storage)
        await storage.put(block5)
        print("✅ Success: Created 10.0.0.0/24 under 10.0.0.0/16")
    except ValidationError as e:
        print(f"❌ Error: {e}")

    # Test 8: Another test with incorrect parent - should fail smallest parent rule
    print("\nTest 8: Create with wrong parent (10.0.0.1/32 under 10.0.0.0/8)")
    block6 = CIDRBlock(
        cidr="10.0.0.1/32",
        name="Wrong Grandparent",
        description="Should use /24 or /16 as parent",
        parent="10.0.0.0/8",
    )
    try:
        await validate_cidr(block6, storage)
        await storage.put(block6)
        print("❌ Failed: Allowed incorrect parent hierarchy")
    except ValidationError as e:
        print(f"✅ Success: Caught error - {e}")

    print("\n===== Test Results =====")
    all_cidrs = await storage.list()
    print(f"\nTotal CIDRs in storage: {len(all_cidrs)}")
    for cidr in all_cidrs:
        print(f"- {cidr.cidr} (parent: {cidr.parent or 'None'})")


if __name__ == "__main__":
    asyncio.run(test_rules())
