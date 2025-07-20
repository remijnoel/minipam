"""
Test UI functionality with real data scenarios.
"""

import pytest
from fastapi.testclient import TestClient

from minipam.api import create_app, reset_dependencies
from minipam.models import CIDRBlock
from minipam.config_loader import get_config, reset_configuration


class TestUIWithData:
    """Test UI endpoints with realistic data scenarios."""

    @pytest.fixture(autouse=True)
    def setup_test(self):
        """Set up test environment."""
        reset_configuration()
        reset_dependencies()
        yield
        reset_configuration()
        reset_dependencies()

    @pytest.fixture
    def test_app(self):
        """Create test app with memory storage."""
        config = get_config()
        config.storage.type = "memory"
        config.ui.enabled = True
        app = create_app(config)
        return app

    @pytest.fixture
    def client(self, test_app):
        """Create test client."""
        return TestClient(test_app)

    def test_ui_tree_with_hierarchical_data(self, client):
        """Test that UI tree endpoint returns hierarchical structure."""
        # Create parent CIDR
        parent_data = {
            "cidr": "10.0.0.0/16",
            "name": "Corporate Network",
            "description": "Main corporate network",
            "parent": None,
            "tags": ["production"]
        }
        response = client.post("/api/v1/cidrs", json=parent_data)
        assert response.status_code == 201

        # Create child CIDR
        child_data = {
            "cidr": "10.0.1.0/24",
            "name": "Development Network",
            "description": "Development subnet",
            "parent": "10.0.0.0/16",
            "tags": ["development"]
        }
        response = client.post("/api/v1/cidrs", json=child_data)
        assert response.status_code == 201

        # Create grandchild CIDR
        grandchild_data = {
            "cidr": "10.0.1.128/25",
            "name": "Dev Team A",
            "description": "Team A development subnet",
            "parent": "10.0.1.0/24",
            "tags": ["development", "team-a"]
        }
        response = client.post("/api/v1/cidrs", json=grandchild_data)
        assert response.status_code == 201

        # Test tree endpoint
        response = client.get("/api/v1/cidrs/tree")
        assert response.status_code == 200
        tree = response.json()
        
        # Verify tree structure
        assert len(tree) == 1  # One root node
        root = tree[0]
        assert root["cidr"] == "10.0.0.0/16"
        assert root["name"] == "Corporate Network"
        assert len(root["children"]) == 1  # One child
        
        child = root["children"][0]
        assert child["cidr"] == "10.0.1.0/24"
        assert child["name"] == "Development Network"
        assert len(child["children"]) == 1  # One grandchild
        
        grandchild = child["children"][0]
        assert grandchild["cidr"] == "10.0.1.128/25"
        assert grandchild["name"] == "Dev Team A"
        assert len(grandchild["children"]) == 0  # No children

    def test_ui_index_serves_with_tree_data(self, client):
        """Test that UI index page is accessible and includes tree functionality."""
        # Create test data first
        parent_data = {
            "cidr": "192.168.0.0/16",
            "name": "Home Network",
            "description": "Home network range",
            "parent": None,
            "tags": ["home"]
        }
        client.post("/api/v1/cidrs", json=parent_data)

        child_data = {
            "cidr": "192.168.1.0/24",
            "name": "IoT Network",
            "description": "IoT devices subnet",
            "parent": "192.168.0.0/16",
            "tags": ["home", "iot"]
        }
        client.post("/api/v1/cidrs", json=child_data)

        # Test UI endpoint
        response = client.get("/ui/")
        assert response.status_code == 200
        content = response.text
        
        # Verify UI contains expected elements
        assert "MiniPAM" in content
        assert "vue.global.prod.js" in content  # Vue.js is loaded
        assert "app.js" in content  # App script is loaded
        assert "id=\"app\"" in content  # Vue mount point

    def test_ui_tree_api_integration(self, client):
        """Test that the tree API correctly builds hierarchical data."""
        # Create multiple root networks
        networks = [
            {"cidr": "10.0.0.0/8", "name": "Private Class A", "parent": None, "tags": ["rfc1918"]},
            {"cidr": "172.16.0.0/12", "name": "Private Class B", "parent": None, "tags": ["rfc1918"]},
            {"cidr": "192.168.0.0/16", "name": "Private Class C", "parent": None, "tags": ["rfc1918"]},
        ]
        
        for network in networks:
            response = client.post("/api/v1/cidrs", json=network)
            assert response.status_code == 201

        # Add children to first network
        children = [
            {"cidr": "10.1.0.0/16", "name": "Region 1", "parent": "10.0.0.0/8", "tags": ["region1"]},
            {"cidr": "10.2.0.0/16", "name": "Region 2", "parent": "10.0.0.0/8", "tags": ["region2"]},
        ]
        
        for child in children:
            response = client.post("/api/v1/cidrs", json=child)
            assert response.status_code == 201

        # Add grandchildren
        grandchildren = [
            {"cidr": "10.1.1.0/24", "name": "DC1", "parent": "10.1.0.0/16", "tags": ["datacenter"]},
            {"cidr": "10.1.2.0/24", "name": "DC2", "parent": "10.1.0.0/16", "tags": ["datacenter"]},
        ]
        
        for grandchild in grandchildren:
            response = client.post("/api/v1/cidrs", json=grandchild)
            assert response.status_code == 201

        # Test tree structure
        response = client.get("/api/v1/cidrs/tree")
        assert response.status_code == 200
        tree = response.json()
        
        # Should have 3 root nodes
        assert len(tree) == 3
        
        # Find the 10.0.0.0/8 network
        class_a = None
        for node in tree:
            if node["cidr"] == "10.0.0.0/8":
                class_a = node
                break
        
        assert class_a is not None
        assert len(class_a["children"]) == 2  # Two regions
        
        # Check region 1 has datacenters
        region1 = None
        for child in class_a["children"]:
            if child["cidr"] == "10.1.0.0/16":
                region1 = child
                break
                
        assert region1 is not None
        assert len(region1["children"]) == 2  # Two datacenters

    def test_ui_add_child_workflow(self, client):
        """Test the add child CIDR workflow through API calls."""
        # Create parent
        parent_data = {
            "cidr": "203.0.113.0/24",
            "name": "Test Network",
            "description": "Test documentation network",
            "parent": None,
            "tags": ["test"]
        }
        response = client.post("/api/v1/cidrs", json=parent_data)
        assert response.status_code == 201

        # Simulate adding a child (what the UI would do when clicking "Add Child")
        child_data = {
            "cidr": "203.0.113.128/25",
            "name": "Test Subnet A",
            "description": "First test subnet",
            "parent": "203.0.113.0/24",  # This would be pre-filled by UI
            "tags": ["test", "subnet-a"]
        }
        response = client.post("/api/v1/cidrs", json=child_data)
        assert response.status_code == 201

        # Add another child
        child_b_data = {
            "cidr": "203.0.113.0/25",
            "name": "Test Subnet B", 
            "description": "Second test subnet",
            "parent": "203.0.113.0/24",
            "tags": ["test", "subnet-b"]
        }
        response = client.post("/api/v1/cidrs", json=child_b_data)
        assert response.status_code == 201

        # Verify tree structure
        response = client.get("/api/v1/cidrs/tree")
        assert response.status_code == 200
        tree = response.json()
        
        assert len(tree) == 1
        parent_node = tree[0]
        assert parent_node["cidr"] == "203.0.113.0/24"
        assert len(parent_node["children"]) == 2
        
        # Children should be sorted
        child_cidrs = [child["cidr"] for child in parent_node["children"]]
        assert "203.0.113.0/25" in child_cidrs
        assert "203.0.113.128/25" in child_cidrs