"""
Test suite for CIDR validation rules
"""

import pytest

from minipam.models import CIDRBlock
from minipam.rules import ValidationError, validate_cidr


class TestNoDuplicateCIDRRule:
    """Test cases for the no duplicate CIDR rule"""

    @pytest.mark.asyncio
    async def test_no_duplicate_allows_new_cidr(self, memory_storage):
        """Test that new CIDRs are allowed"""
        block = CIDRBlock(cidr="192.168.1.0/24", name="Test Network")
        
        # Should not raise an error
        await validate_cidr(block, memory_storage)
        await memory_storage.put(block)

    @pytest.mark.asyncio
    async def test_no_duplicate_rejects_existing_cidr(self, memory_storage):
        """Test that duplicate CIDRs are rejected"""
        block = CIDRBlock(cidr="192.168.1.0/24", name="Test Network")
        await memory_storage.put(block)
        
        duplicate = CIDRBlock(cidr="192.168.1.0/24", name="Duplicate Network")
        
        with pytest.raises(ValidationError, match="already exists"):
            await validate_cidr(duplicate, memory_storage)


class TestSmallestParentRule:
    """Test cases for the smallest parent rule"""

    @pytest.mark.asyncio
    async def test_root_cidr_allowed(self, memory_storage):
        """Test that root CIDRs with no parent are allowed when no parents exist"""
        root = CIDRBlock(cidr="0.0.0.0/0", name="Root", parent=None)
        
        # Should not raise an error
        await validate_cidr(root, memory_storage)
        await memory_storage.put(root)

    @pytest.mark.asyncio
    async def test_child_requires_parent_when_parent_exists(self, memory_storage):
        """Test that CIDRs must be assigned to existing parents"""
        # Create parent hierarchy
        root = CIDRBlock(cidr="0.0.0.0/0", name="Root", parent=None)
        await memory_storage.put(root)
        
        ten_slash_8 = CIDRBlock(cidr="10.0.0.0/8", parent="0.0.0.0/0")
        await memory_storage.put(ten_slash_8)
        
        # Try to create a child without specifying parent - should fail
        child = CIDRBlock(cidr="10.0.100.0/24", parent=None)
        
        with pytest.raises(ValidationError, match="must be assigned to parent 10.0.0.0/8"):
            await validate_cidr(child, memory_storage)

    @pytest.mark.asyncio
    async def test_child_requires_most_specific_parent(self, memory_storage):
        """Test that CIDRs must be assigned to the most specific parent"""
        # Create hierarchy
        root = CIDRBlock(cidr="0.0.0.0/0", name="Root", parent=None)
        await memory_storage.put(root)
        
        ten_slash_8 = CIDRBlock(cidr="10.0.0.0/8", parent="0.0.0.0/0")
        await memory_storage.put(ten_slash_8)
        
        ten_slash_16 = CIDRBlock(cidr="10.0.0.0/16", parent="10.0.0.0/8")
        await memory_storage.put(ten_slash_16)
        
        # Try to assign to less specific parent - should fail
        child = CIDRBlock(cidr="10.0.100.0/24", parent="10.0.0.0/8")
        
        with pytest.raises(ValidationError, match="should be assigned to the more specific parent 10.0.0.0/16"):
            await validate_cidr(child, memory_storage)

    @pytest.mark.asyncio
    async def test_child_with_correct_parent_succeeds(self, memory_storage):
        """Test that CIDRs with correct parents are accepted"""
        # Create hierarchy
        root = CIDRBlock(cidr="0.0.0.0/0", name="Root", parent=None)
        await memory_storage.put(root)
        
        ten_slash_8 = CIDRBlock(cidr="10.0.0.0/8", parent="0.0.0.0/0")
        await memory_storage.put(ten_slash_8)
        
        ten_slash_16 = CIDRBlock(cidr="10.0.0.0/16", parent="10.0.0.0/8")
        await memory_storage.put(ten_slash_16)
        
        # Assign to correct parent - should succeed
        child = CIDRBlock(cidr="10.0.100.0/24", parent="10.0.0.0/16")
        
        # Should not raise an error
        await validate_cidr(child, memory_storage)
        await memory_storage.put(child)

    @pytest.mark.asyncio
    async def test_invalid_cidr_format_rejected(self, memory_storage):
        """Test that invalid CIDR formats are rejected"""
        invalid_block = CIDRBlock(cidr="172.168.16.126/25", parent=None)
        
        with pytest.raises(ValidationError, match="has host bits set"):
            await validate_cidr(invalid_block, memory_storage)

    @pytest.mark.asyncio
    async def test_parent_must_exist(self, memory_storage):
        """Test that specified parents must exist in storage"""
        child = CIDRBlock(cidr="10.0.1.0/24", name="Test", description="Test", parent="10.0.0.0/8")
        
        with pytest.raises(ValidationError, match="does not exist"):
            await validate_cidr(child, memory_storage)

    @pytest.mark.asyncio
    async def test_cidr_must_be_subnet_of_parent(self, memory_storage):
        """Test that CIDR must be a valid subnet of its parent"""
        parent = CIDRBlock(cidr="10.0.0.0/8", parent=None)
        await memory_storage.put(parent)
        
        # Try to create a child that's not a subnet
        invalid_child = CIDRBlock(cidr="192.168.1.0/24", parent="10.0.0.0/8")
        
        with pytest.raises(ValidationError, match="is not a subnet of parent"):
            await validate_cidr(invalid_child, memory_storage)

    @pytest.mark.asyncio
    async def test_ipv4_ipv6_version_mismatch(self, memory_storage):
        """Test that IPv4 and IPv6 version mismatches are rejected"""
        ipv4_parent = CIDRBlock(cidr="10.0.0.0/8", parent=None)
        await memory_storage.put(ipv4_parent)
        
        # Try to create IPv6 child under IPv4 parent
        ipv6_child = CIDRBlock(cidr="2001:db8::/32", parent="10.0.0.0/8")
        
        with pytest.raises(ValidationError, match="must be the same IP version"):
            await validate_cidr(ipv6_child, memory_storage)


class TestRuleEngineIntegration:
    """Integration tests for the complete rule engine"""

    @pytest.mark.asyncio
    async def test_complex_hierarchy_validation(self, memory_storage):
        """Test validation with a complex CIDR hierarchy"""
        # Build a complex hierarchy step by step
        cidrs = [
            CIDRBlock(cidr="0.0.0.0/0", name="Root", parent=None),
            CIDRBlock(cidr="10.0.0.0/8", parent="0.0.0.0/0"),
            CIDRBlock(cidr="192.168.0.0/16", parent="0.0.0.0/0"),
            CIDRBlock(cidr="10.0.0.0/16", parent="10.0.0.0/8"),
            CIDRBlock(cidr="10.1.0.0/16", parent="10.0.0.0/8"),
            CIDRBlock(cidr="192.168.1.0/24", parent="192.168.0.0/16"),
            CIDRBlock(cidr="10.0.1.0/24", parent="10.0.0.0/16"),
        ]
        
        # All should validate and be created successfully
        for cidr in cidrs:
            await validate_cidr(cidr, memory_storage)
            await memory_storage.put(cidr)

    @pytest.mark.asyncio
    async def test_rule_order_independence(self, memory_storage):
        """Test that rule validation works regardless of rule order"""
        # Create a scenario that tests both duplicate and parent rules
        root = CIDRBlock(cidr="0.0.0.0/0", name="Root", parent=None)
        await memory_storage.put(root)
        
        # This should fail on duplicate rule first
        duplicate_root = CIDRBlock(cidr="0.0.0.0/0", name="Duplicate", parent=None)
        
        with pytest.raises(ValidationError, match="already exists"):
            await validate_cidr(duplicate_root, memory_storage)
