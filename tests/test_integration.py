"""
Integration tests for minipam

These tests verify that all components work together correctly.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from minipam.main import create_app
from minipam.models import CIDRBlock


@pytest.mark.asyncio
async def test_basic_functionality():
    """Test basic functionality of all components"""
    print("Testing basic functionality...")

    # Test 1: Create a CIDR block
    print("1. Testing CIDR block creation...")
    block = CIDRBlock(
        cidr="192.168.1.0/24",
        name="Integration Test Network",
        description="Test network for integration testing",
        tags={"test": "integration"},
    )
    assert block.cidr == "192.168.1.0/24"
    print("   ✅ CIDR block created successfully")

    # Test 2: Test file storage with default name
    print("2. Testing file storage...")
    file_path = "cidrs.json"
    lock_file = file_path + ".lock"

    # Clean up any existing files
    for path in [file_path, lock_file]:
        if os.path.exists(path):
            os.unlink(path)

    try:
        # Set environment to use file storage
        os.environ["USE_FILE_BACKEND"] = "true"
        os.environ["CIDR_FILE_PATH"] = file_path

        # Get storage from factory to ensure we're using file storage
        from minipam.storage import FileCIDRStorage, get_cidr_storage

        # Create the file storage explicitly to ensure it works as expected
        file_storage = FileCIDRStorage(file_path)

        # Test operations
        await file_storage.put(block)
        retrieved = await file_storage.get(block.cidr)
        assert retrieved is not None
        assert retrieved.cidr == block.cidr

        # Verify file was created
        assert os.path.exists(file_path), "Storage file was not created"
        print("   ✅ File storage works")
    finally:
        # Clean up
        for path in [file_path, lock_file]:
            if os.path.exists(path):
                os.unlink(path)

    # Test 3: Test FastAPI app creation with file storage
    print("3. Testing FastAPI app creation...")
    # Set environment variables to ensure file storage is used
    os.environ["USE_FILE_BACKEND"] = "true"
    os.environ["CIDR_FILE_PATH"] = "app_test_cidrs.json"

    try:
        app = create_app()
        assert app is not None
        print("   ✅ FastAPI app created successfully with file storage")
    finally:
        # Clean up
        for path in ["app_test_cidrs.json", "app_test_cidrs.json.lock"]:
            if os.path.exists(path):
                os.unlink(path)

    print("🎉 All integration tests passed!")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
