"""
Unit tests for minipam.models module
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from minipam.models import CIDRBlock


class TestCIDRBlock:
    """Test cases for CIDRBlock model"""

    def test_cidr_block_creation_minimal(self):
        """Test creating a CIDR block with minimal required fields"""
        block = CIDRBlock(cidr="192.168.1.0/24")

        assert block.cidr == "192.168.1.0/24"
        assert block.name is None
        assert block.description is None
        assert block.tags == {}
        assert block.parent is None
        assert isinstance(block.created_at, datetime)

    def test_cidr_block_creation_full(self):
        """Test creating a CIDR block with all fields"""
        created_at = datetime.utcnow()
        block = CIDRBlock(
            cidr="10.0.0.0/8",
            name="Corporate Network",
            description="Main corporate network",
            tags={"environment": "production", "priority": "high"},
            parent="172.16.0.0/12",
            created_at=created_at,
        )

        assert block.cidr == "10.0.0.0/8"
        assert block.name == "Corporate Network"
        assert block.description == "Main corporate network"
        assert block.tags == {"environment": "production", "priority": "high"}
        assert block.parent == "172.16.0.0/12"
        assert block.created_at == created_at

    def test_cidr_block_validation_empty_cidr(self):
        """Test that empty CIDR raises validation error"""
        with pytest.raises((ValueError, ValidationError)):
            CIDRBlock(cidr="")

    def test_cidr_block_validation_invalid_cidr(self):
        """Test that invalid CIDR format raises validation error"""
        with pytest.raises((ValueError, ValidationError)):
            CIDRBlock(cidr="not-a-cidr")

        with pytest.raises((ValueError, ValidationError)):
            CIDRBlock(cidr="192.168.1.0/33")  # Invalid subnet mask

        with pytest.raises((ValueError, ValidationError)):
            CIDRBlock(cidr="256.256.256.256/24")  # Invalid IP address

    def test_cidr_block_validation_no_cidr(self):
        """Test that missing CIDR raises validation error"""
        with pytest.raises((TypeError, ValidationError)):
            CIDRBlock()

    def test_cidr_block_tags_default(self):
        """Test that tags default to empty dict"""
        block = CIDRBlock(cidr="192.168.1.0/24")
        assert block.tags == {}

        # Test that we can modify tags
        block.tags["test"] = "value"
        assert block.tags == {"test": "value"}

    def test_cidr_block_serialization(self):
        """Test CIDR block serialization to dict"""
        block = CIDRBlock(
            cidr="192.168.1.0/24", name="Test Network", tags={"env": "test"}
        )

        data = block.dict()
        assert data["cidr"] == "192.168.1.0/24"
        assert data["name"] == "Test Network"
        assert data["tags"] == {"env": "test"}
        assert "created_at" in data

    def test_cidr_block_json_serialization(self):
        """Test CIDR block JSON serialization"""
        block = CIDRBlock(cidr="192.168.1.0/24")

        json_str = block.json()
        assert "192.168.1.0/24" in json_str
        assert "created_at" in json_str

    def test_cidr_block_from_dict(self):
        """Test creating CIDR block from dictionary"""
        data = {
            "cidr": "192.168.1.0/24",
            "name": "Test Network",
            "description": "Test description",
            "tags": {"env": "test"},
            "parent": None,
            "created_at": "2023-01-01T00:00:00",
        }

        block = CIDRBlock(**data)
        assert block.cidr == "192.168.1.0/24"
        assert block.name == "Test Network"
        assert block.description == "Test description"
        assert block.tags == {"env": "test"}

    def test_cidr_block_equality(self):
        """Test CIDR block equality comparison"""
        block1 = CIDRBlock(cidr="192.168.1.0/24", name="Test")
        block2 = CIDRBlock(cidr="192.168.1.0/24", name="Test")

        # Note: Pydantic models compare by value, but created_at will be different
        # so we need to set the same created_at for true equality
        created_at = datetime.utcnow()
        block1.created_at = created_at
        block2.created_at = created_at

        assert block1 == block2

    def test_cidr_block_inequality(self):
        """Test CIDR block inequality comparison"""
        block1 = CIDRBlock(cidr="192.168.1.0/24")
        block2 = CIDRBlock(cidr="192.168.2.0/24")

        assert block1 != block2
