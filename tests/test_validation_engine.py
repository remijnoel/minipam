"""Unit tests for CIDR validation engine - WRITTEN FIRST per CLAUDE.md"""

from unittest.mock import Mock

import pytest

from src.minipam.models import CIDRBlock, ValidationResult
from src.minipam.validation import CIDRValidationEngine

# Mark as unit tests
pytestmark = pytest.mark.unit


class TestCIDRValidationEngine:
    """Unit tests for CIDR validation engine."""

    def test_validate_unique_cidr_succeeds(self):
        """Test validating a unique CIDR block succeeds."""
        engine = CIDRValidationEngine()

        # Mock storage that returns no existing CIDR
        mock_storage = Mock()
        mock_storage.get.return_value = None
        mock_storage.list.return_value = []

        block = CIDRBlock(cidr="10.0.0.0/24", name="Test Network", parent=None, tags=[])

        result = engine.validate(block, mock_storage)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_duplicate_cidr_fails(self):
        """Test validating a duplicate CIDR block fails."""
        engine = CIDRValidationEngine()

        # Mock storage that returns existing CIDR
        existing_block = CIDRBlock(
            cidr="10.0.0.0/24", name="Existing Network", parent=None, tags=[]
        )
        mock_storage = Mock()
        mock_storage.get.return_value = existing_block
        mock_storage.list.return_value = [existing_block]

        block = CIDRBlock(cidr="10.0.0.0/24", name="Test Network", parent=None, tags=[])

        result = engine.validate(block, mock_storage)
        assert not result.is_valid
        assert any("already exists" in error for error in result.errors)

    def test_validate_parent_relationship_succeeds(self):
        """Test validating valid parent-child relationship."""
        engine = CIDRValidationEngine()

        # Mock storage with parent block
        parent_block = CIDRBlock(
            cidr="10.0.0.0/16", name="Parent Network", parent=None, tags=[]
        )
        mock_storage = Mock()
        mock_storage.get.side_effect = lambda cidr: (
            parent_block if cidr == "10.0.0.0/16" else None
        )
        mock_storage.list.return_value = [parent_block]

        child_block = CIDRBlock(
            cidr="10.0.1.0/24", name="Child Network", parent="10.0.0.0/16", tags=[]
        )

        result = engine.validate(child_block, mock_storage)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_parent_relationship_fails_nonexistent_parent(self):
        """Test validating fails when parent doesn't exist."""
        engine = CIDRValidationEngine()

        # Mock storage with no parent
        mock_storage = Mock()
        mock_storage.get.return_value = None
        mock_storage.list.return_value = []

        child_block = CIDRBlock(
            cidr="10.0.1.0/24", name="Child Network", parent="10.0.0.0/16", tags=[]
        )

        result = engine.validate(child_block, mock_storage)
        assert not result.is_valid
        assert any("does not exist" in error for error in result.errors)

    def test_validate_parent_relationship_fails_not_subnet(self):
        """Test validating fails when child is not a subnet of parent."""
        engine = CIDRValidationEngine()

        # Mock storage with parent block
        parent_block = CIDRBlock(
            cidr="10.0.0.0/24", name="Parent Network", parent=None, tags=[]
        )
        mock_storage = Mock()
        mock_storage.get.side_effect = lambda cidr: (
            parent_block if cidr == "10.0.0.0/24" else None
        )
        mock_storage.list.return_value = [parent_block]

        # Child is not a subnet of parent
        child_block = CIDRBlock(
            cidr="192.168.1.0/24", name="Child Network", parent="10.0.0.0/24", tags=[]
        )

        result = engine.validate(child_block, mock_storage)
        assert not result.is_valid
        assert any("not a subnet" in error for error in result.errors)

    def test_validate_parent_relationship_fails_child_broader_than_parent(self):
        """Test validating fails when child is broader than parent."""
        engine = CIDRValidationEngine()

        # Mock storage with parent block
        parent_block = CIDRBlock(
            cidr="10.0.0.0/24", name="Parent Network", parent=None, tags=[]
        )
        mock_storage = Mock()
        mock_storage.get.side_effect = lambda cidr: (
            parent_block if cidr == "10.0.0.0/24" else None
        )
        mock_storage.list.return_value = [parent_block]

        # Child is broader than parent
        child_block = CIDRBlock(
            cidr="10.0.0.0/16", name="Child Network", parent="10.0.0.0/24", tags=[]
        )

        result = engine.validate(child_block, mock_storage)
        assert not result.is_valid
        assert any("cannot be broader" in error for error in result.errors)

    def test_validate_no_overlaps_succeeds(self):
        """Test validating non-overlapping CIDRs succeeds."""
        engine = CIDRValidationEngine()

        # Mock storage with non-overlapping blocks
        existing_blocks = [
            CIDRBlock(cidr="10.0.0.0/24", name="Network 1", parent=None, tags=[]),
            CIDRBlock(cidr="192.168.1.0/24", name="Network 2", parent=None, tags=[]),
        ]
        mock_storage = Mock()
        mock_storage.get.return_value = None
        mock_storage.list.return_value = existing_blocks

        new_block = CIDRBlock(
            cidr="172.16.0.0/24", name="New Network", parent=None, tags=[]
        )

        result = engine.validate(new_block, mock_storage)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_overlaps_fails(self):
        """Test validating overlapping CIDRs fails."""
        engine = CIDRValidationEngine()

        # Mock storage with overlapping block
        existing_blocks = [
            CIDRBlock(cidr="10.0.0.0/24", name="Existing Network", parent=None, tags=[])
        ]
        mock_storage = Mock()
        mock_storage.get.return_value = None
        mock_storage.list.return_value = existing_blocks

        # New block overlaps with existing
        new_block = CIDRBlock(
            cidr="10.0.0.0/25", name="New Network", parent=None, tags=[]  # Wrong parent
        )

        result = engine.validate(new_block, mock_storage)
        assert not result.is_valid
        assert any("overlaps" in error for error in result.errors)

    def test_validate_hierarchy_consistency_succeeds(self):
        """Test validating hierarchy consistency succeeds."""
        engine = CIDRValidationEngine()

        # Mock storage with consistent hierarchy
        existing_blocks = [
            CIDRBlock(cidr="10.0.0.0/16", name="Parent", parent=None, tags=[]),
            CIDRBlock(
                cidr="10.0.1.0/24", name="Child 1", parent="10.0.0.0/16", tags=[]
            ),
            CIDRBlock(
                cidr="10.0.2.0/24", name="Child 2", parent="10.0.0.0/16", tags=[]
            ),
        ]
        mock_storage = Mock()
        mock_storage.get.side_effect = lambda cidr: next(
            (block for block in existing_blocks if block.cidr == cidr), None
        )
        mock_storage.list.return_value = existing_blocks

        new_block = CIDRBlock(
            cidr="10.0.3.0/24", name="New Child", parent="10.0.0.0/16", tags=[]
        )

        result = engine.validate(new_block, mock_storage)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_hierarchy_consistency_fails_sibling_overlap(self):
        """Test validating fails when siblings overlap."""
        engine = CIDRValidationEngine()

        # Mock storage with sibling blocks
        existing_blocks = [
            CIDRBlock(cidr="10.0.0.0/16", name="Parent", parent=None, tags=[]),
            CIDRBlock(
                cidr="10.0.1.0/24", name="Sibling", parent="10.0.0.0/16", tags=[]
            ),
        ]
        mock_storage = Mock()
        mock_storage.get.side_effect = lambda cidr: next(
            (block for block in existing_blocks if block.cidr == cidr), None
        )
        mock_storage.list.return_value = existing_blocks

        # New block overlaps with sibling
        new_block = CIDRBlock(
            cidr="10.0.1.0/25",
            name="Overlapping Sibling",
            parent="10.0.0.0/16",
            tags=[],
        )

        result = engine.validate(new_block, mock_storage)
        assert not result.is_valid
        assert any("overlaps with sibling" in error for error in result.errors)

    def test_list_children_returns_direct_children(self):
        """Test listing direct children of a CIDR."""
        engine = CIDRValidationEngine()

        # Mock storage with parent-child relationships
        all_blocks = [
            CIDRBlock(cidr="10.0.0.0/16", name="Parent", parent=None, tags=[]),
            CIDRBlock(
                cidr="10.0.1.0/24", name="Child 1", parent="10.0.0.0/16", tags=[]
            ),
            CIDRBlock(
                cidr="10.0.2.0/24", name="Child 2", parent="10.0.0.0/16", tags=[]
            ),
            CIDRBlock(
                cidr="10.0.1.0/25", name="Grandchild", parent="10.0.1.0/24", tags=[]
            ),
        ]
        mock_storage = Mock()
        mock_storage.list.return_value = all_blocks

        children = engine.list_children("10.0.0.0/16", mock_storage, depth=2)

        # Should return direct children and grandchildren
        assert len(children) == 3
        child_cidrs = [child.cidr for child in children]
        assert "10.0.1.0/24" in child_cidrs
        assert "10.0.2.0/24" in child_cidrs
        assert "10.0.1.0/25" in child_cidrs

    def test_list_children_with_depth_limit(self):
        """Test listing children with depth limit."""
        engine = CIDRValidationEngine()

        # Mock storage with deep hierarchy
        all_blocks = [
            CIDRBlock(cidr="10.0.0.0/16", name="Parent", parent=None, tags=[]),
            CIDRBlock(cidr="10.0.1.0/24", name="Child", parent="10.0.0.0/16", tags=[]),
            CIDRBlock(
                cidr="10.0.1.0/25", name="Grandchild", parent="10.0.1.0/24", tags=[]
            ),
            CIDRBlock(
                cidr="10.0.1.0/26",
                name="Great-grandchild",
                parent="10.0.1.0/25",
                tags=[],
            ),
        ]
        mock_storage = Mock()
        mock_storage.list.return_value = all_blocks

        # Test with depth limit of 1
        children = engine.list_children("10.0.0.0/16", mock_storage, depth=1)

        # Should return child and grandchild, but not great-grandchild
        child_cidrs = [child.cidr for child in children]
        assert "10.0.1.0/24" in child_cidrs
        assert "10.0.1.0/25" in child_cidrs
        assert "10.0.1.0/26" not in child_cidrs

    def test_get_tree_returns_hierarchical_structure(self):
        """Test getting hierarchical tree structure."""
        engine = CIDRValidationEngine()

        # Mock storage with hierarchy
        all_blocks = [
            CIDRBlock(cidr="10.0.0.0/16", name="Root", parent=None, tags=["root"]),
            CIDRBlock(
                cidr="10.0.1.0/24", name="Child 1", parent="10.0.0.0/16", tags=["child"]
            ),
            CIDRBlock(
                cidr="10.0.2.0/24", name="Child 2", parent="10.0.0.0/16", tags=["child"]
            ),
            CIDRBlock(
                cidr="192.168.1.0/24", name="Separate Root", parent=None, tags=["root"]
            ),
        ]
        mock_storage = Mock()
        mock_storage.list.return_value = all_blocks

        tree = engine.get_tree(mock_storage)

        # Should return 2 root nodes
        assert len(tree) == 2

        # Find the 10.0.0.0/16 root
        root_10 = next(node for node in tree if node["cidr"] == "10.0.0.0/16")
        assert root_10["name"] == "Root"
        assert root_10["tags"] == ["root"]
        assert len(root_10["children"]) == 2

        # Verify children
        child_cidrs = [child["cidr"] for child in root_10["children"]]
        assert "10.0.1.0/24" in child_cidrs
        assert "10.0.2.0/24" in child_cidrs

    def test_get_tree_with_specific_root(self):
        """Test getting tree with specific root CIDR."""
        engine = CIDRValidationEngine()

        # Mock storage with hierarchy
        all_blocks = [
            CIDRBlock(cidr="10.0.0.0/16", name="Root", parent=None, tags=[]),
            CIDRBlock(cidr="10.0.1.0/24", name="Child", parent="10.0.0.0/16", tags=[]),
            CIDRBlock(cidr="192.168.1.0/24", name="Other Root", parent=None, tags=[]),
        ]
        mock_storage = Mock()
        mock_storage.list.return_value = all_blocks
        mock_storage.get.side_effect = lambda cidr: next(
            (block for block in all_blocks if block.cidr == cidr), None
        )

        tree = engine.get_tree(mock_storage, root="10.0.0.0/16")

        # Should return only the specified root
        assert len(tree) == 1
        assert tree[0]["cidr"] == "10.0.0.0/16"
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["cidr"] == "10.0.1.0/24"

    def test_validation_handles_exceptions_gracefully(self):
        """Test that validation handles exceptions gracefully."""
        engine = CIDRValidationEngine()

        # Mock storage that raises exception
        mock_storage = Mock()
        mock_storage.get.side_effect = Exception("Storage error")

        block = CIDRBlock(cidr="10.0.0.0/24", name="Test Network", parent=None, tags=[])

        result = engine.validate(block, mock_storage)
        assert not result.is_valid
        assert any("Validation failed" in error for error in result.errors)

    def test_would_be_child_method(self):
        """Test the _would_be_child helper method."""
        engine = CIDRValidationEngine()

        parent_block = CIDRBlock(
            cidr="10.0.0.0/16", name="Parent", parent=None, tags=[]
        )
        child_block = CIDRBlock(
            cidr="10.0.1.0/24", name="Child", parent="10.0.0.0/16", tags=[]
        )
        unrelated_block = CIDRBlock(
            cidr="192.168.1.0/24", name="Unrelated", parent=None, tags=[]
        )

        # Child should be child of parent
        assert engine._would_be_child(child_block, parent_block)

        # Unrelated should not be child of parent
        assert not engine._would_be_child(unrelated_block, parent_block)

        # Parent should not be child of child
        assert not engine._would_be_child(parent_block, child_block)
