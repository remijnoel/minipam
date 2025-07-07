"""
Integration tests for minipam.api module
"""

import os

import pytest
from fastapi.testclient import TestClient

from minipam.main import create_app
from minipam.models import CIDRBlock


@pytest.fixture
def client():
    """Create a test client for the FastAPI app with file storage enabled"""
    # Set environment variable to use file storage
    os.environ["USE_FILE_BACKEND"] = "true"
    os.environ["CIDR_FILE_PATH"] = "test_cidrs.json"
    app = create_app()
    return TestClient(app)


@pytest.fixture
def clean_storage():
    """Clear storage before each test"""
    # Reset the singleton storage instance
    import os
    from pathlib import Path

    import minipam.api

    minipam.api._storage_instance = None

    # Define test file path
    test_file_path = "test_cidrs.json"
    lock_file = test_file_path + ".lock"

    # Clean up any existing files
    for file_path in [test_file_path, lock_file]:
        if os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except Exception as e:
                print(f"Error removing file {file_path}: {e}")

    # Get a fresh storage instance
    from minipam.storage import get_cidr_storage

    storage = get_cidr_storage()

    # Clear any existing data
    import asyncio

    async def clear_storage():
        all_blocks = await storage.list()
        for block in all_blocks:
            await storage.delete(block.cidr)

    asyncio.run(clear_storage())

    yield storage

    # Clean up after test
    for file_path in [test_file_path, lock_file]:
        if os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except Exception as e:
                print(f"Error removing file {file_path}: {e}")


@pytest.fixture
def sample_cidr_data():
    """Sample CIDR data for testing"""
    return {
        "cidr": "192.168.1.0/24",
        "name": "Test Network",
        "description": "Test network for API testing",
        "tags": {"environment": "test", "priority": "high"},
        "parent": None,
    }


class TestCIDRAPI:
    """Test cases for CIDR API endpoints"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "backend" in data

    def test_list_empty_cidrs(self, client, clean_storage):
        """Test listing CIDRs when storage is empty"""
        response = client.get("/cidrs/")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_create_cidr(self, client, clean_storage, sample_cidr_data):
        """Test creating a new CIDR block"""
        response = client.post("/cidrs/", json=sample_cidr_data)
        assert response.status_code == 201
        data = response.json()
        assert data["cidr"] == sample_cidr_data["cidr"]
        assert data["name"] == sample_cidr_data["name"]
        assert "created_at" in data

    def test_get_cidr(self, client, clean_storage, sample_cidr_data):
        """Test retrieving a specific CIDR block"""
        # First create a CIDR block
        create_response = client.post("/cidrs/", json=sample_cidr_data)
        assert create_response.status_code == 201

        # Then retrieve it
        cidr = sample_cidr_data["cidr"]
        response = client.get(f"/cidrs/{cidr}")
        assert response.status_code == 200
        data = response.json()
        assert data["cidr"] == cidr
        assert data["name"] == sample_cidr_data["name"]

    def test_get_nonexistent_cidr(self, client, clean_storage):
        """Test retrieving a non-existent CIDR block"""
        response = client.get("/cidrs/192.168.99.0/24")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_update_cidr(self, client, clean_storage, sample_cidr_data):
        """Test updating an existing CIDR block"""
        # First create a CIDR block
        create_response = client.post("/cidrs/", json=sample_cidr_data)
        assert create_response.status_code == 201

        # Update it using PUT
        updated_data = sample_cidr_data.copy()
        updated_data["name"] = "Updated Network"
        updated_data["description"] = "Updated description"

        cidr = sample_cidr_data["cidr"]
        response = client.put(f"/cidrs/{cidr}", json=updated_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Network"
        assert data["description"] == "Updated description"

    def test_delete_cidr(self, client, clean_storage, sample_cidr_data):
        """Test deleting a CIDR block"""
        # First create a CIDR block
        create_response = client.post("/cidrs/", json=sample_cidr_data)
        assert create_response.status_code == 201

        # Delete it
        cidr = sample_cidr_data["cidr"]
        response = client.delete(f"/cidrs/{cidr}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/cidrs/{cidr}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_cidr(self, client, clean_storage):
        """Test deleting a non-existent CIDR block"""
        response = client.delete("/cidrs/192.168.99.0/24")
        assert response.status_code == 404

    def test_list_cidrs_with_data(self, client, clean_storage, sample_cidr_data):
        """Test listing CIDRs with data present"""
        # Create a CIDR block
        client.post("/cidrs/", json=sample_cidr_data)

        # Create another CIDR block
        another_data = {
            "cidr": "10.0.0.0/8",
            "name": "Another Network",
            "description": "Another test network",
            "tags": {"environment": "test"},
        }
        client.post("/cidrs/", json=another_data)

        # List all CIDRs
        response = client.get("/cidrs/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        cidrs = [block["cidr"] for block in data]
        assert "192.168.1.0/24" in cidrs
        assert "10.0.0.0/8" in cidrs

    def test_cidr_with_special_characters(self, client, clean_storage):
        """Test CIDR blocks with special characters in path"""
        # Test with IPv6-like notation (though not real IPv6)
        cidr_data = {
            "cidr": "2001:db8::/32",
            "name": "IPv6 Network",
            "description": "Test IPv6 network",
        }

        response = client.post("/cidrs/", json=cidr_data)
        assert response.status_code == 201

        # Retrieve it
        response = client.get("/cidrs/2001:db8::/32")
        assert response.status_code == 200
        data = response.json()
        assert data["cidr"] == "2001:db8::/32"

    def test_invalid_cidr_data(self, client, clean_storage):
        """Test creating CIDR with invalid data"""
        invalid_data = {"name": "Test Network", "description": "Missing CIDR field"}

        response = client.post("/cidrs/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_cidr_with_tags(self, client, clean_storage):
        """Test CIDR creation and retrieval with tags"""
        cidr_data = {
            "cidr": "172.16.0.0/12",
            "name": "Tagged Network",
            "tags": {
                "environment": "production",
                "team": "infrastructure",
                "priority": "high",
                "region": "us-west",
            },
        }

        response = client.post("/cidrs/", json=cidr_data)
        assert response.status_code == 201

        # Retrieve and verify tags
        response = client.get("/cidrs/172.16.0.0/12")
        assert response.status_code == 200
        data = response.json()
        assert data["tags"]["environment"] == "production"
        assert data["tags"]["team"] == "infrastructure"
        assert len(data["tags"]) == 4

    def test_cidr_with_parent_and_children(self, client, clean_storage):
        """Test CIDR creation with parent relationship"""
        cidr_data = {
            "cidr": "192.168.0.0/16",
            "name": "Child Network",
            "parent": "10.0.0.0/8",
        }

        response = client.post("/cidrs/", json=cidr_data)
        assert response.status_code == 201

        # Retrieve and verify parent relationship
        response = client.get("/cidrs/192.168.0.0/16")
        assert response.status_code == 200
        data = response.json()
        assert data["parent"] == "10.0.0.0/8"

    def test_create_duplicate_cidr(self, client, clean_storage, sample_cidr_data):
        """Test creating a duplicate CIDR block should return 409"""
        # First create a CIDR block
        response = client.post("/cidrs/", json=sample_cidr_data)
        assert response.status_code == 201

        # Try to create the same CIDR block again
        response = client.post("/cidrs/", json=sample_cidr_data)
        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"]

    def test_update_nonexistent_cidr(self, client, clean_storage):
        """Test updating a non-existent CIDR block should return 404"""
        update_data = {
            "cidr": "192.168.99.0/24",
            "name": "Updated Network",
            "description": "Updated description",
        }

        response = client.put("/cidrs/192.168.99.0/24", json=update_data)
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
