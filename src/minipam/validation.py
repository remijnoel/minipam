"""
CIDR validation engine for MiniPAM.

This module provides comprehensive validation of CIDR blocks including
overlap detection, hierarchy validation, and business rule enforcement.
"""

from ipaddress import AddressValueError, IPv4Network
from typing import List, Optional

from .models import CIDRBlock, ValidationResult
from .storage import StorageBackend


class CIDRValidationEngine:
    """Engine for validating CIDR blocks and their relationships."""

    def __init__(self):
        self.validation_rules = [
            self._validate_cidr_format,
            self._validate_parent_exists,
            self._validate_parent_relationship,
            self._validate_no_duplicates,
            self._validate_no_overlaps,
            self._validate_hierarchy_consistency,
        ]

    def validate(
        self, block: CIDRBlock, storage: StorageBackend
    ) -> ValidationResult:
        """Validate a CIDR block against all rules."""
        result = ValidationResult(is_valid=True)

        # Run all validation rules
        for rule in self.validation_rules:
            try:
                rule(block, storage, result)
            except Exception as e:
                result.add_error(f"Validation failed: {str(e)}")

        return result

    def validate_create(
        self, block: CIDRBlock, storage: StorageBackend
    ) -> ValidationResult:
        """Validate a CIDR block for creation."""
        return self.validate(block, storage)

    def validate_update(
        self, original_cidr: str, updated_block: CIDRBlock, storage: StorageBackend
    ) -> ValidationResult:
        """Validate a CIDR block for update."""
        # For updates, we need to exclude the original block from duplicate/overlap checks
        result = ValidationResult(is_valid=True)

        # Get all existing blocks except the one being updated
        all_blocks = storage.list()  # Get all blocks
        other_blocks = [b for b in all_blocks if b.cidr != original_cidr]

        # Run validation against other blocks
        for rule in self.validation_rules:
            if rule.__name__ in ["_validate_no_duplicates", "_validate_no_overlaps"]:
                # Use modified storage that excludes the original block
                mock_storage = MockStorageForUpdate(other_blocks)
                rule(updated_block, mock_storage, result)
            else:
                rule(updated_block, storage, result)

        return result

    def _validate_cidr_format(
        self, block: CIDRBlock, storage: StorageBackend, result: ValidationResult
    ) -> None:
        """Validate CIDR format is correct - IPv4 only."""
        try:
            IPv4Network(block.cidr, strict=False)
        except AddressValueError as e:
            result.add_error(f"Invalid CIDR format: {str(e)}")

    def _validate_parent_exists(
        self, block: CIDRBlock, storage: StorageBackend, result: ValidationResult
    ) -> None:
        """Validate that parent CIDR exists if specified."""
        if not block.parent:
            return

        parent_block = storage.get(block.parent)
        if not parent_block:
            result.add_error(f"Parent CIDR {block.parent} does not exist")

    def _validate_parent_relationship(
        self, block: CIDRBlock, storage: StorageBackend, result: ValidationResult
    ) -> None:
        """Validate that CIDR is actually a subnet of its parent."""
        if not block.parent:
            return

        try:
            # Parse networks (IPv4 only)
            cidr_net = IPv4Network(block.cidr, strict=False)
            parent_net = IPv4Network(block.parent, strict=False)

            # Check if cidr is a subnet of parent
            if not cidr_net.subnet_of(parent_net):
                if cidr_net.supernet_of(parent_net):
                    result.add_error(
                        f"CIDR {block.cidr} cannot be broader than its parent {block.parent}"
                    )
                else:
                    result.add_error(
                        f"CIDR {block.cidr} is not a subnet of parent {block.parent}"
                    )
        except (AddressValueError, AttributeError) as e:
            result.add_error(f"Cannot validate parent relationship: {str(e)}")

    def _validate_no_duplicates(
        self, block: CIDRBlock, storage: StorageBackend, result: ValidationResult
    ) -> None:
        """Validate that CIDR doesn't already exist."""
        existing_block = storage.get(block.cidr)
        if existing_block:
            result.add_error(f"CIDR {block.cidr} already exists")

    def _validate_no_overlaps(
        self, block: CIDRBlock, storage: StorageBackend, result: ValidationResult
    ) -> None:
        """Validate that CIDR doesn't overlap with existing blocks."""
        try:
            # Get the network object for the new block (IPv4 only)
            new_net = IPv4Network(block.cidr, strict=False)

            # Check against all existing blocks
            all_blocks = storage.list()  # Get all blocks

            for existing_block in all_blocks:
                if existing_block.cidr == block.cidr:
                    continue  # Skip self

                try:
                    # Get network for existing block (IPv4 only)
                    existing_net = IPv4Network(existing_block.cidr, strict=False)

                    # Check for overlaps
                    if new_net.overlaps(existing_net):
                        # Check if this is a proper parent-child relationship
                        is_valid_hierarchy = False
                        
                        if new_net.subnet_of(existing_net):
                            # New block is child of existing - allow if:
                            # 1. New declares existing as its parent (direct parent-child), OR
                            # 2. New has a valid parent that creates a valid hierarchy path
                            is_valid_hierarchy = (
                                block.parent == existing_block.cidr or 
                                (block.parent is not None and self._is_valid_hierarchy_path(block, existing_block, storage))
                            )
                        elif existing_net.subnet_of(new_net):
                            # Existing block is child of new - allow if:
                            # 1. Existing declares new as parent, OR
                            # 2. Existing has no parent (orphaned child that can be organized under new parent)
                            is_valid_hierarchy = (existing_block.parent == block.cidr or existing_block.parent is None)
                        
                        if not is_valid_hierarchy:
                            # Check if they are siblings (same parent)
                            if block.parent and existing_block.parent and block.parent == existing_block.parent:
                                result.add_error(
                                    f"CIDR {block.cidr} overlaps with sibling CIDR {existing_block.cidr}"
                                )
                            else:
                                result.add_error(
                                    f"CIDR {block.cidr} overlaps with existing CIDR {existing_block.cidr}"
                                )

                except AddressValueError:
                    # Skip invalid existing blocks
                    continue

        except AddressValueError as e:
            result.add_error(f"Cannot validate overlaps: {str(e)}")

    def _validate_hierarchy_consistency(
        self, block: CIDRBlock, storage: StorageBackend, result: ValidationResult
    ) -> None:
        """Validate that the CIDR hierarchy remains consistent."""
        if not block.parent:
            return

        try:
            # Get all blocks to check hierarchy
            all_blocks = storage.list()  # Get all blocks

            # Parse the new block's network (IPv4 only)
            new_net = IPv4Network(block.cidr, strict=False)

            # Check that no existing children would become orphaned
            for existing_block in all_blocks:
                if existing_block.parent == block.cidr:
                    # This block would become a child of the new block
                    try:
                        # IPv4 only
                        existing_net = IPv4Network(existing_block.cidr, strict=False)

                        if not existing_net.subnet_of(new_net):
                            result.add_error(
                                f"Existing block {existing_block.cidr} claims this as parent but is not a subnet"
                            )
                    except AddressValueError:
                        continue

        except Exception as e:
            result.add_warning(f"Could not fully validate hierarchy: {str(e)}")
    
    def list_children(self, parent_cidr: str, storage: StorageBackend, depth: Optional[int] = None) -> List[CIDRBlock]:
        """List children of a CIDR block up to a specified depth."""
        all_blocks = storage.list()
        children = []
        
        def collect_children_recursive(current_parent: str, current_depth: int, max_depth: Optional[int]):
            # Find direct children of current parent
            direct_children = [block for block in all_blocks if block.parent == current_parent]
            
            for child in direct_children:
                children.append(child)
                
                # Recurse if we haven't reached max depth
                # current_depth represents the depth of the children we just added
                # We can recurse if current_depth < max_depth
                if max_depth is None or current_depth < max_depth:
                    collect_children_recursive(child.cidr, current_depth + 1, max_depth)
        
        # Start the recursive collection
        # depth=1 means include children and grandchildren  
        # depth=2 means include children and grandchildren (but limit at 2 generations)
        collect_children_recursive(parent_cidr, 0, depth)
        
        return children
    
    def get_tree(self, storage: StorageBackend, root: Optional[str] = None):
        """Get hierarchical tree structure of CIDR blocks."""
        all_blocks = storage.list()
        
        if root:
            # Find the root block and build tree from there
            root_block = storage.get(root)
            if not root_block:
                return []
            return [self._build_tree_node(root_block, all_blocks)]
        else:
            # Build tree from all root blocks (blocks with no parent)
            root_blocks = [block for block in all_blocks if not block.parent]
            tree = []
            for root_block in root_blocks:
                tree.append(self._build_tree_node(root_block, all_blocks))
            return tree
    
    def _build_tree_node(self, block: CIDRBlock, all_blocks: List[CIDRBlock]) -> dict:
        """Build a tree node for a CIDR block."""
        # Find direct children
        children = [b for b in all_blocks if b.parent == block.cidr]
        
        node = {
            "cidr": block.cidr,
            "name": block.name,
            "tags": block.tags,
            "children": []
        }
        
        # Recursively build children
        for child in children:
            node["children"].append(self._build_tree_node(child, all_blocks))
        
        return node
    
    def _would_be_child(self, child_block: CIDRBlock, parent_block: CIDRBlock) -> bool:
        """Check if a CIDR block would be a valid child of another."""
        try:
            child_net = IPv4Network(child_block.cidr, strict=False)
            parent_net = IPv4Network(parent_block.cidr, strict=False)
            return child_net.subnet_of(parent_net)
        except AddressValueError:
            return False
    
    def _is_valid_hierarchy_path(self, new_block: CIDRBlock, ancestor_block: CIDRBlock, storage: StorageBackend) -> bool:
        """Check if there's a valid hierarchy path from new block to ancestor through parents."""
        if not new_block.parent:
            return False
        
        # Get the declared parent
        parent_block = storage.get(new_block.parent)
        if not parent_block:
            return False
        
        # If the parent is the ancestor, it's valid
        if parent_block.cidr == ancestor_block.cidr:
            return True
        
        # Check if the parent is also contained within the ancestor
        try:
            from ipaddress import IPv4Network, AddressValueError
            parent_net = IPv4Network(parent_block.cidr, strict=False)
            ancestor_net = IPv4Network(ancestor_block.cidr, strict=False)
            
            if parent_net.subnet_of(ancestor_net):
                # Recursively check if the parent has a valid path to the ancestor
                return self._is_valid_hierarchy_path(parent_block, ancestor_block, storage)
        except AddressValueError:
            pass
        
        return False


class MockStorageForUpdate:
    """Mock storage that excludes specific blocks for update validation."""

    def __init__(self, blocks: List[CIDRBlock]):
        self.blocks = blocks

    def get(self, cidr: str) -> Optional[CIDRBlock]:
        """Get a CIDR block by its CIDR notation."""
        for block in self.blocks:
            if block.cidr == cidr:
                return block
        return None

    def list(self, **kwargs) -> List[CIDRBlock]:
        """List CIDR blocks with optional filtering."""
        blocks = self.blocks

        # Filter by tags if provided
        tags = kwargs.get('tags')
        if tags:
            filtered_blocks = []
            for block in blocks:
                if any(tag in block.tags for tag in tags):
                    filtered_blocks.append(block)
            blocks = filtered_blocks

        return blocks
