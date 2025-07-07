"""
Test the API endpoints with UI-specific request formats
"""

import json
import os
from pathlib import Path

import pytest
import requests
from fastapi.testclient import TestClient

from minipam.main import create_app
from minipam.models import CIDRBlock

# Set environment variables to use file storage
os.environ["USE_FILE_BACKEND"] = "true"
os.environ["CIDR_FILE_PATH"] = "ui_test_cidrs.json"

# Create a test client using FastAPI's TestClient
app = create_app()
client = TestClient(app)


@pytest.fixture
def clear_storage():
    """Fixture to clear storage before each test"""
    # Define test file paths
    test_file_path = "ui_test_cidrs.json"
    lock_file = test_file_path + ".lock"

    # Clean up any existing files before test
    for file_path in [test_file_path, lock_file]:
        if os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except Exception as e:
                print(f"Error removing file {file_path}: {e}")

    # Reset the API server's storage singleton to force reinitialization
    import minipam.api

    minipam.api._storage_instance = None

    yield

    # Clean up after test
    for file_path in [test_file_path, lock_file]:
        if os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except Exception as e:
                print(f"Error removing file {file_path}: {e}")

    # Reset the API server's storage singleton again to clean up
    minipam.api._storage_instance = None


def test_ui_create_cidr_format(clear_storage):
    """Test creating a CIDR block with UI-formatted data"""
    # This is what the UI would send when creating a CIDR block
    ui_cidr_data = {
        "cidr": "192.168.1.0/24",
        "name": "UI Test Network",
        "description": "Created from UI integration test",
        "tags": {"source": "ui", "environment": "test"},
        "parent": None,
    }

    # Make the request
    response = client.post("/cidrs/", json=ui_cidr_data)

    # Check the response
    assert (
        response.status_code == 201
    ), f"Expected 201 but got {response.status_code}: {response.text}"
    data = response.json()

    assert data["cidr"] == ui_cidr_data["cidr"]
    assert data["name"] == ui_cidr_data["name"]
    assert data["description"] == ui_cidr_data["description"]
    assert data["tags"] == ui_cidr_data["tags"]
    assert data["parent"] == ui_cidr_data["parent"]
    assert "created_at" in data


def test_ui_create_cidr_with_empty_fields(clear_storage):
    """Test creating a CIDR with empty string values from UI"""
    # The UI might send empty strings for optional fields
    ui_cidr_data = {
        "cidr": "192.168.2.0/24",
        "name": "",  # Empty string
        "description": "",  # Empty string
        "tags": {},  # Empty object
        "parent": "",  # Empty string
    }

    # Make the request
    response = client.post("/cidrs/", json=ui_cidr_data)

    # Check the response - this may be failing in the UI
    assert (
        response.status_code == 201
    ), f"Expected 201 but got {response.status_code}: {response.text}"

    data = response.json()
    assert data["cidr"] == ui_cidr_data["cidr"]

    # Check that empty strings are handled correctly
    assert data["name"] is None or data["name"] == ""
    assert data["description"] is None or data["description"] == ""
    assert data["parent"] is None or data["parent"] == ""


def test_ui_create_cidr_with_parent(clear_storage):
    """Test creating a CIDR with a parent - simulating the 'Create Child' feature"""
    # First create a parent CIDR
    parent_data = {"cidr": "10.0.0.0/8", "name": "Parent Network"}
    client.post("/cidrs/", json=parent_data)

    # Now create a child CIDR as the UI would
    child_data = {
        "cidr": "10.1.0.0/16",
        "name": "Child Network",
        "description": "Child network created from UI",
        "tags": {"type": "child"},
        "parent": "10.0.0.0/8",  # Reference parent by CIDR
    }

    response = client.post("/cidrs/", json=child_data)
    assert (
        response.status_code == 201
    ), f"Expected 201 but got {response.status_code}: {response.text}"

    data = response.json()
    assert data["parent"] == "10.0.0.0/8"


def test_ui_update_cidr(clear_storage):
    """Test updating a CIDR as the UI would"""
    # First create a CIDR
    cidr_data = {
        "cidr": "172.16.0.0/16",
        "name": "Original Name",
        "tags": {"original": "tag"},
    }
    client.post("/cidrs/", json=cidr_data)

    # Now update it using PUT as the UI would
    updated_data = {
        "cidr": "172.16.0.0/16",  # Same CIDR (can't be changed)
        "name": "Updated Name",
        "description": "Updated description",
        "tags": {"original": "tag", "new": "tag"},
        "parent": None,
    }

    response = client.put(f"/cidrs/{updated_data['cidr']}", json=updated_data)
    assert (
        response.status_code == 200
    ), f"Expected 200 but got {response.status_code}: {response.text}"

    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["tags"] == {"original": "tag", "new": "tag"}


def test_ui_create_with_null_fields(clear_storage):
    """Test creating a CIDR with explicit null fields from UI"""
    # The UI might send null for optional fields
    ui_cidr_data = {
        "cidr": "192.168.3.0/24",
        "name": None,  # Explicit null
        "description": None,  # Explicit null
        "tags": {},
        "parent": None,  # Explicit null
    }

    # Make the request
    response = client.post("/cidrs/", json=ui_cidr_data)

    assert (
        response.status_code == 201
    ), f"Expected 201 but got {response.status_code}: {response.text}"

    data = response.json()
    assert data["cidr"] == ui_cidr_data["cidr"]
    assert data["name"] is None
    assert data["description"] is None
    assert data["parent"] is None


def test_ui_create_realistic_browser_submission(clear_storage):
    """Test creating a CIDR with a realistic browser form submission pattern"""
    # This test simulates how browsers might actually format the request
    # when submitting from a form - handling of empty values may differ
    # from what the test client does

    # This simulates what the Vue.js frontend is likely sending
    ui_form_data = {
        "cidr": "192.168.5.0/24",
        "name": "Browser Form Test",
        # Note how browsers might handle form fields differently:
        # - Empty fields might be sent as empty strings instead of being omitted
        # - Empty fields might be sent as null
        # - The structure of nested objects might be different than expected
        "description": "",  # Empty string
        "tags": {"key1": "value1"},
        "parent": "",  # Empty string that should be treated as null
    }

    # Make the request with content type that matches what browsers send
    response = client.post(
        "/cidrs/", json=ui_form_data, headers={"Content-Type": "application/json"}
    )

    assert (
        response.status_code == 201
    ), f"Expected 201 but got {response.status_code}: {response.text}"

    # Verify the result
    data = response.json()
    assert data["cidr"] == ui_form_data["cidr"]
    assert data["name"] == ui_form_data["name"]
    assert "tags" in data and data["tags"] == ui_form_data["tags"]

    # Parent should be null/None, not an empty string
    assert data["parent"] is None

    # Also test retrieving the created CIDR to ensure it persisted correctly
    get_response = client.get(f"/cidrs/{ui_form_data['cidr']}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["cidr"] == ui_form_data["cidr"]


@pytest.mark.xfail(
    reason="This test is unstable in CI environments due to shared file storage issues"
)
def test_ui_create_child_cidr_workflow():
    """Test the specific UI workflow for creating child CIDRs that was failing before"""
    # Use a unique file path with timestamp to ensure uniqueness for every test run
    import time

    timestamp = str(int(time.time()))
    unique_file_path = f"test_child_workflow_{timestamp}.json"
    lock_file = unique_file_path + ".lock"

    # Clean up any existing files (should not be necessary with timestamp)
    for file_path in [unique_file_path, lock_file]:
        if os.path.exists(file_path):
            os.unlink(file_path)

    # Save original environment variables
    original_use_file = os.environ.get("USE_FILE_BACKEND")
    original_file_path = os.environ.get("CIDR_FILE_PATH")

    try:
        # Set environment variables to use this specific file
        os.environ["USE_FILE_BACKEND"] = "true"
        os.environ["CIDR_FILE_PATH"] = unique_file_path

        # Reset any existing storage instance
        import minipam.api

        minipam.api._storage_instance = None

        # Create a fresh app instance with our custom file path
        test_app = create_app()
        test_client = TestClient(test_app)

        # First create a parent CIDR - use different CIDRs to avoid conflicts
        parent_data = {"cidr": "192.168.0.0/16", "name": "Test Root Network"}
        response = test_client.post("/cidrs/", json=parent_data)
        assert (
            response.status_code == 201
        ), f"Could not create parent CIDR: {response.text}"

        # Create a child CIDR
        child_data = {
            "cidr": "192.168.1.0/24",
            "name": "test-child",
            "tags": {},
            "parent": "192.168.0.0/16",
        }

        # Make the request
        response = test_client.post("/cidrs/", json=child_data)

        # Check the response
        assert (
            response.status_code == 201
        ), f"Expected 201 but got {response.status_code}: {response.text}"

        data = response.json()
        assert data["cidr"] == child_data["cidr"]
        assert data["parent"] == child_data["parent"]

        # Now try to create a grandchild
        grandchild_data = {
            "cidr": "192.168.1.128/25",
            "name": "test-grandchild",
            "tags": {},
            "parent": "192.168.1.0/24",
        }

        response = test_client.post("/cidrs/", json=grandchild_data)
        assert (
            response.status_code == 201
        ), f"Expected 201 but got {response.status_code}: {response.text}"
    finally:
        # Clean up the test files
        for file_path in [unique_file_path, lock_file]:
            if os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except Exception as e:
                    print(f"Error removing file {file_path}: {e}")

        # Restore original environment variables
        if original_use_file is not None:
            os.environ["USE_FILE_BACKEND"] = original_use_file
        else:
            os.environ.pop("USE_FILE_BACKEND", None)

        if original_file_path is not None:
            os.environ["CIDR_FILE_PATH"] = original_file_path
        else:
            os.environ.pop("CIDR_FILE_PATH", None)

        # Reset the API server's storage singleton
        minipam.api._storage_instance = None
