"""Test core data models."""

import ipaddress

import pytest
from pydantic import ValidationError

from src.minipam.models import AuthRequest, CIDRBlock, UserInfo, ValidationResult


class TestCIDRBlock:
    """Test CIDRBlock model."""

    def test_valid_cidr_creation(self):
        """Test creating valid CIDR blocks."""
        cidr = CIDRBlock(
            cidr="10.0.0.0/24",
            name="Test Network",
            parent="10.0.0.0/16",
            tags=["test", "lab"],
        )

        assert cidr.cidr == "10.0.0.0/24"
        assert cidr.name == "Test Network"
        assert cidr.parent == "10.0.0.0/16"
        assert cidr.tags == ["test", "lab"]

    def test_cidr_validation(self):
        """Test CIDR notation validation."""
        # Valid CIDR
        cidr = CIDRBlock(cidr="192.168.1.0/24", name="Test")
        assert cidr.cidr == "192.168.1.0/24"

        # Invalid CIDR
        with pytest.raises(ValidationError):
            CIDRBlock(cidr="invalid", name="Test")

        # IPv6 not allowed
        with pytest.raises(ValidationError):
            CIDRBlock(cidr="2001:db8::/64", name="Test")

        # /0 not allowed
        with pytest.raises(ValidationError):
            CIDRBlock(cidr="0.0.0.0/0", name="Test")

    def test_parent_validation(self):
        """Test parent CIDR validation."""
        # Valid parent
        cidr = CIDRBlock(cidr="10.0.0.0/24", name="Test", parent="10.0.0.0/16")
        assert cidr.parent == "10.0.0.0/16"

        # Invalid parent
        with pytest.raises(ValidationError):
            CIDRBlock(cidr="10.0.0.0/24", name="Test", parent="invalid")

        # IPv6 parent not allowed
        with pytest.raises(ValidationError):
            CIDRBlock(cidr="10.0.0.0/24", name="Test", parent="2001:db8::/64")

    def test_tags_normalization(self):
        """Test tag normalization."""
        cidr = CIDRBlock(
            cidr="10.0.0.0/24", name="Test", tags=["  TEST  ", "Lab", "  ", "PROD"]
        )

        assert cidr.tags == ["test", "lab", "prod"]

    def test_network_methods(self):
        """Test network utility methods."""
        cidr = CIDRBlock(cidr="10.0.0.0/24", name="Test", parent="10.0.0.0/16")

        # Test get_network
        network = cidr.get_network()
        assert isinstance(network, ipaddress.IPv4Network)
        assert str(network) == "10.0.0.0/24"

        # Test get_parent_network
        parent_network = cidr.get_parent_network()
        assert isinstance(parent_network, ipaddress.IPv4Network)
        assert str(parent_network) == "10.0.0.0/16"

    def test_relationship_methods(self):
        """Test CIDR relationship methods."""
        parent = CIDRBlock(cidr="10.0.0.0/16", name="Parent")
        child = CIDRBlock(cidr="10.0.0.0/24", name="Child")
        sibling = CIDRBlock(cidr="10.0.1.0/24", name="Sibling")
        unrelated = CIDRBlock(cidr="192.168.1.0/24", name="Unrelated")

        # Test is_child_of
        assert child.is_child_of(parent)
        assert not parent.is_child_of(child)
        assert not sibling.is_child_of(child)
        assert not unrelated.is_child_of(parent)

        # Test overlaps_with
        assert child.overlaps_with(parent)
        assert parent.overlaps_with(child)
        assert not sibling.overlaps_with(child)
        assert not unrelated.overlaps_with(parent)


class TestUserInfo:
    """Test UserInfo model."""

    def test_user_info_creation(self):
        """Test creating user info."""
        user = UserInfo(
            id="user123",
            username="testuser",
            roles=["admin", "user"],
            scopes=["cidr:read", "cidr:write"],
        )

        assert user.id == "user123"
        assert user.username == "testuser"
        assert user.roles == ["admin", "user"]
        assert user.scopes == ["cidr:read", "cidr:write"]

    def test_user_info_defaults(self):
        """Test default values."""
        user = UserInfo(id="user123", username="testuser")

        assert user.roles == []
        assert user.scopes == []


class TestAuthRequest:
    """Test AuthRequest model."""

    def test_auth_request_creation(self):
        """Test creating auth request."""
        request = AuthRequest(
            headers={"Authorization": "Bearer token"},
            cookies={"session": "abc123"},
            query_params={"token": "xyz789"},
        )

        assert request.headers == {"Authorization": "Bearer token"}
        assert request.cookies == {"session": "abc123"}
        assert request.query_params == {"token": "xyz789"}

    def test_auth_request_defaults(self):
        """Test default values."""
        request = AuthRequest()

        assert request.headers == {}
        assert request.cookies == {}
        assert request.query_params == {}


class TestValidationResult:
    """Test ValidationResult model."""

    def test_validation_result_creation(self):
        """Test creating validation result."""
        result = ValidationResult(is_valid=False, errors=["Error 1", "Error 2"])

        assert not result.is_valid
        assert result.errors == ["Error 1", "Error 2"]

    def test_success_factory(self):
        """Test success factory method."""
        result = ValidationResult.success()

        assert result.is_valid
        assert result.errors == []

    def test_failure_factory(self):
        """Test failure factory method."""
        errors = ["Error 1", "Error 2"]
        result = ValidationResult.failure(errors)

        assert not result.is_valid
        assert result.errors == errors

    def test_add_error(self):
        """Test adding errors."""
        result = ValidationResult.success()
        assert result.is_valid

        result.add_error("Test error")
        assert not result.is_valid
        assert result.errors == ["Test error"]

        result.add_error("Another error")
        assert result.errors == ["Test error", "Another error"]
