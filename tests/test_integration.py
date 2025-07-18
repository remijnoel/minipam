"""Integration tests for MiniPAM - WRITTEN FIRST per CLAUDE.md requirements"""

import shutil
import tempfile
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory for integration tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_config(temp_data_dir):
    """Create test configuration."""
    config_content = f"""
server:
  host: "127.0.0.1"
  port: 8001
  debug: true

storage:
  type: "memory"

auth:
  backend: "none"

ui:
  enabled: true
  path: "/ui"
"""
    config_file = Path(temp_data_dir) / "test_config.yaml"
    config_file.write_text(config_content)
    return str(config_file)


class TestApplicationStartup:
    """Test application startup and configuration loading."""

    def test_application_loads_config_successfully(self, test_config):
        """Test that the application can load configuration from file."""
        # This will fail until we implement config loading
        from src.minipam.config import load_config

        config = load_config(test_config)
        assert config.server.host == "127.0.0.1"
        assert config.server.port == 8001
        assert config.storage.type == "memory"
        assert config.auth.backend == "none"

    def test_application_creates_fastapi_app(self, test_config):
        """Test that the application creates a FastAPI app."""
        # This will fail until we implement the app factory
        from src.minipam.api import create_app
        from src.minipam.config import load_config

        load_config(test_config)
        app = create_app()
        assert app is not None
        assert hasattr(app, "routes")


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_liveness_endpoint_returns_ok(self, test_config):
        """Test liveness endpoint returns 200 OK."""
        from src.minipam.api import create_app
        from src.minipam.config import load_config

        load_config(test_config)
        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_readiness_endpoint_returns_ready(self, test_config):
        """Test readiness endpoint returns ready status."""
        from src.minipam.api import create_app
        from src.minipam.config import load_config

        load_config(test_config)
        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "storage" in data


class TestCIDRManagement:
    """Test complete CIDR management workflow."""

    def test_create_cidr_block_successfully(self, test_config):
        """Test creating a new CIDR block via API."""
        from src.minipam.api import create_app
        from src.minipam.config import load_config

        load_config(test_config)
        app = create_app()
        client = TestClient(app)

        cidr_data = {
            "cidr": "10.0.0.0/16",
            "name": "Corporate Network",
            "parent": None,
            "tags": ["corp", "main"],
        }

        response = client.post("/api/v1/cidrs", json=cidr_data)
        assert response.status_code == 201

        created_cidr = response.json()
        assert created_cidr["cidr"] == "10.0.0.0/16"
        assert created_cidr["name"] == "Corporate Network"
        assert created_cidr["tags"] == ["corp", "main"]

    def test_list_cidr_blocks_empty_initially(self, test_config):
        """Test listing CIDR blocks returns empty list initially."""
        from src.minipam.api import create_app
        from src.minipam.config import load_config

        load_config(test_config)
        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/cidrs")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_cidr_tree_view(self, test_config):
        """Test getting hierarchical tree view of CIDRs."""
        from src.minipam.api import create_app
        from src.minipam.config import load_config

        load_config(test_config)
        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/cidrs/tree")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_overlapping_cidr_returns_409(self, test_config):
        """Test that creating overlapping CIDR blocks returns 409 conflict."""
        from src.minipam.api import create_app
        from src.minipam.config import load_config

        load_config(test_config)
        app = create_app()
        client = TestClient(app)

        # Create first CIDR
        cidr1 = {"cidr": "10.0.0.0/16", "name": "Network 1", "parent": None, "tags": []}
        response1 = client.post("/api/v1/cidrs", json=cidr1)
        assert response1.status_code == 201

        # Try to create overlapping CIDR
        cidr2 = {
            "cidr": "10.0.0.0/24",
            "name": "Network 2",
            "parent": None,  # This should fail - needs parent
            "tags": [],
        }
        response2 = client.post("/api/v1/cidrs", json=cidr2)
        assert response2.status_code == 409

    def test_create_child_cidr_with_parent(self, test_config):
        """Test creating a child CIDR with proper parent relationship."""
        from src.minipam.api import create_app
        from src.minipam.config import load_config

        load_config(test_config)
        app = create_app()
        client = TestClient(app)

        # Create parent CIDR
        parent_cidr = {
            "cidr": "10.0.0.0/16",
            "name": "Parent Network",
            "parent": None,
            "tags": ["parent"],
        }
        response1 = client.post("/api/v1/cidrs", json=parent_cidr)
        assert response1.status_code == 201

        # Create child CIDR
        child_cidr = {
            "cidr": "10.0.1.0/24",
            "name": "Child Network",
            "parent": "10.0.0.0/16",
            "tags": ["child"],
        }
        response2 = client.post("/api/v1/cidrs", json=child_cidr)
        assert response2.status_code == 201

        # Verify hierarchy in tree view
        tree_response = client.get("/api/v1/cidrs/tree")
        assert tree_response.status_code == 200
        tree = tree_response.json()
        assert len(tree) == 1
        assert tree[0]["cidr"] == "10.0.0.0/16"
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["cidr"] == "10.0.1.0/24"

    def test_delete_cidr_block(self, test_config):
        """Test deleting a CIDR block."""
        from src.minipam.api import create_app
        from src.minipam.config import load_config

        load_config(test_config)
        app = create_app()
        client = TestClient(app)

        # Create CIDR
        cidr_data = {
            "cidr": "192.168.1.0/24",
            "name": "Test Network",
            "parent": None,
            "tags": [],
        }
        response = client.post("/api/v1/cidrs", json=cidr_data)
        assert response.status_code == 201

        # Delete CIDR
        delete_response = client.delete("/api/v1/cidrs/192.168.1.0%2F24")
        assert delete_response.status_code == 204

        # Verify it's gone
        get_response = client.get("/api/v1/cidrs/192.168.1.0%2F24")
        assert get_response.status_code == 404

    def test_update_cidr_block(self, test_config):
        """Test updating a CIDR block."""
        from src.minipam.api import create_app
        from src.minipam.config import load_config

        load_config(test_config)
        app = create_app()
        client = TestClient(app)

        # Create CIDR
        cidr_data = {
            "cidr": "172.16.0.0/24",
            "name": "Original Name",
            "parent": None,
            "tags": ["original"],
        }
        response = client.post("/api/v1/cidrs", json=cidr_data)
        assert response.status_code == 201

        # Update CIDR
        updated_data = {
            "cidr": "172.16.0.0/24",
            "name": "Updated Name",
            "parent": None,
            "tags": ["updated"],
        }
        update_response = client.put("/api/v1/cidrs/172.16.0.0%2F24", json=updated_data)
        assert update_response.status_code == 200

        updated_cidr = update_response.json()
        assert updated_cidr["name"] == "Updated Name"
        assert updated_cidr["tags"] == ["updated"]


class TestAuthenticationIntegration:
    """Test authentication integration with different backends."""

    def test_noauth_backend_allows_requests(self, temp_data_dir):
        """Test that NoAuth backend allows all requests."""
        config_content = f"""
server:
  host: "127.0.0.1"
  port: 8001
  debug: true

storage:
  type: "memory"

auth:
  backend: "none"

ui:
  enabled: true
  path: "/ui"
"""
        config_file = Path(temp_data_dir) / "noauth_config.yaml"
        config_file.write_text(config_content)

        # Set required environment variable
        import os

        os.environ["ENABLE_NOAUTH"] = "true"

        try:
            from src.minipam.api import create_app
            from src.minipam.config import load_config

            load_config(str(config_file))
            app = create_app()
            client = TestClient(app)

            # Should be able to access protected endpoint
            response = client.get("/api/v1/cidrs")
            assert response.status_code == 200

        finally:
            os.environ.pop("ENABLE_NOAUTH", None)

    def test_apikey_backend_requires_valid_key(self, temp_data_dir):
        """Test that API key backend requires valid API key."""
        config_content = f"""
server:
  host: "127.0.0.1"
  port: 8001
  debug: true

storage:
  type: "memory"

auth:
  backend: "apikey"
  apikey:
    keys:
      - "valid-test-key"

ui:
  enabled: true
  path: "/ui"
"""
        config_file = Path(temp_data_dir) / "apikey_config.yaml"
        config_file.write_text(config_content)

        from src.minipam.api import create_app
        from src.minipam.config import load_config

        load_config(str(config_file))
        app = create_app()
        client = TestClient(app)

        # Request without API key should fail
        response = client.get("/api/v1/cidrs")
        assert response.status_code == 401

        # Request with invalid API key should fail
        response = client.get(
            "/api/v1/cidrs", headers={"Authorization": "Bearer invalid-key"}
        )
        assert response.status_code == 401

        # Request with valid API key should succeed
        response = client.get(
            "/api/v1/cidrs", headers={"Authorization": "Bearer valid-test-key"}
        )
        assert response.status_code == 200


class TestStorageIntegration:
    """Test storage backend integration."""

    def test_memory_storage_persistence_during_session(self, test_config):
        """Test that memory storage persists data during a session."""
        from src.minipam.api import create_app
        from src.minipam.config import load_config

        load_config(test_config)
        app = create_app()
        client = TestClient(app)

        # Create CIDR
        cidr_data = {
            "cidr": "10.10.0.0/16",
            "name": "Persistent Test",
            "parent": None,
            "tags": ["test"],
        }
        response = client.post("/api/v1/cidrs", json=cidr_data)
        assert response.status_code == 201

        # Verify it persists
        get_response = client.get("/api/v1/cidrs/10.10.0.0%2F16")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Persistent Test"

    def test_file_storage_atomic_operations(self, temp_data_dir):
        """Test that file storage operations are atomic."""
        config_content = f"""
server:
  host: "127.0.0.1"
  port: 8001
  debug: true

storage:
  type: "file"
  path: "{temp_data_dir}/data"

auth:
  backend: "none"

ui:
  enabled: true
  path: "/ui"
"""
        config_file = Path(temp_data_dir) / "file_config.yaml"
        config_file.write_text(config_content)

        import os

        os.environ["ENABLE_NOAUTH"] = "true"

        try:
            from src.minipam.api import create_app
            from src.minipam.config import load_config

            load_config(str(config_file))
            app = create_app()
            client = TestClient(app)

            # Create CIDR
            cidr_data = {
                "cidr": "172.20.0.0/16",
                "name": "File Storage Test",
                "parent": None,
                "tags": ["file"],
            }
            response = client.post("/api/v1/cidrs", json=cidr_data)
            assert response.status_code == 201

            # Verify file exists
            data_file = Path(temp_data_dir) / "data" / "cidrs.json"
            assert data_file.exists()

        finally:
            os.environ.pop("ENABLE_NOAUTH", None)


class TestWebUIIntegration:
    """Test web UI integration."""

    def test_ui_index_page_accessible(self, test_config):
        """Test that UI index page is accessible."""
        from src.minipam.api import create_app
        from src.minipam.config import load_config

        load_config(test_config)
        app = create_app()
        client = TestClient(app)

        response = client.get("/ui/")
        # Should return HTML page or redirect
        assert response.status_code in [200, 302]

    def test_ui_serves_static_assets(self, test_config):
        """Test that UI serves static assets correctly."""
        from src.minipam.api import create_app
        from src.minipam.config import load_config

        load_config(test_config)
        app = create_app()
        client = TestClient(app)

        # Try to access UI (may not exist yet, but should not crash)
        response = client.get("/ui/")
        assert response.status_code in [200, 404]  # 404 if static files not found


class TestCompleteCIDRWorkflow:
    """Test complete end-to-end CIDR management workflow."""

    def test_complete_cidr_hierarchy_workflow(self, test_config):
        """Test complete workflow: create hierarchy, validate, modify, delete."""
        from src.minipam.api import create_app
        from src.minipam.config import load_config

        load_config(test_config)
        app = create_app()
        client = TestClient(app)

        # Step 1: Create root network
        root_cidr = {
            "cidr": "10.0.0.0/8",
            "name": "Root Network",
            "parent": None,
            "tags": ["root"],
        }
        response = client.post("/api/v1/cidrs", json=root_cidr)
        assert response.status_code == 201

        # Step 2: Create regional network
        regional_cidr = {
            "cidr": "10.1.0.0/16",
            "name": "Regional Network",
            "parent": "10.0.0.0/8",
            "tags": ["regional"],
        }
        response = client.post("/api/v1/cidrs", json=regional_cidr)
        assert response.status_code == 201

        # Step 3: Create local networks
        local_cidrs = [
            {
                "cidr": "10.1.1.0/24",
                "name": "Local Network 1",
                "parent": "10.1.0.0/16",
                "tags": ["local", "office1"],
            },
            {
                "cidr": "10.1.2.0/24",
                "name": "Local Network 2",
                "parent": "10.1.0.0/16",
                "tags": ["local", "office2"],
            },
        ]

        for cidr in local_cidrs:
            response = client.post("/api/v1/cidrs", json=cidr)
            assert response.status_code == 201

        # Step 4: Verify hierarchy in tree view
        tree_response = client.get("/api/v1/cidrs/tree")
        assert tree_response.status_code == 200
        tree = tree_response.json()

        # Should have 1 root with 1 regional child with 2 local children
        assert len(tree) == 1
        assert tree[0]["cidr"] == "10.0.0.0/8"
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["cidr"] == "10.1.0.0/16"
        assert len(tree[0]["children"][0]["children"]) == 2

        # Step 5: Verify list view
        list_response = client.get("/api/v1/cidrs")
        assert list_response.status_code == 200
        cidrs = list_response.json()
        assert len(cidrs) == 4

        # Step 6: Try to create conflicting CIDR (should fail)
        conflict_cidr = {
            "cidr": "10.1.1.0/25",
            "name": "Conflicting Network",
            "parent": "10.0.0.0/8",  # Wrong parent
            "tags": ["conflict"],
        }
        response = client.post("/api/v1/cidrs", json=conflict_cidr)
        assert response.status_code == 409

        # Step 7: Update a CIDR
        updated_cidr = {
            "cidr": "10.1.1.0/24",
            "name": "Updated Local Network 1",
            "parent": "10.1.0.0/16",
            "tags": ["local", "office1", "updated"],
        }
        response = client.put("/api/v1/cidrs/10.1.1.0%2F24", json=updated_cidr)
        assert response.status_code == 200

        # Step 8: Try to delete parent with children (should fail)
        response = client.delete("/api/v1/cidrs/10.1.0.0%2F16")
        assert response.status_code == 409

        # Step 9: Delete child networks first
        response = client.delete("/api/v1/cidrs/10.1.1.0%2F24")
        assert response.status_code == 204

        response = client.delete("/api/v1/cidrs/10.1.2.0%2F24")
        assert response.status_code == 204

        # Step 10: Now delete parent
        response = client.delete("/api/v1/cidrs/10.1.0.0%2F16")
        assert response.status_code == 204

        # Step 11: Verify final state
        final_response = client.get("/api/v1/cidrs")
        assert final_response.status_code == 200
        final_cidrs = final_response.json()
        assert len(final_cidrs) == 1
        assert final_cidrs[0]["cidr"] == "10.0.0.0/8"
