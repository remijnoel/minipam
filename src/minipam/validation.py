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

    async def validate(
        self, block: CIDRBlock, storage: StorageBackend
    ) -> ValidationResult:
        """Validate a CIDR block against all rules."""
        result = ValidationResult(is_valid=True)

        # Run all validation rules
        for rule in self.validation_rules:
            try:
                await rule(block, storage, result)
            except Exception as e:
                result.add_error(f"Validation error: {str(e)}")

        return result

    async def validate_create(
        self, block: CIDRBlock, storage: StorageBackend
    ) -> ValidationResult:
        """Validate a CIDR block for creation."""
        return await self.validate(block, storage)

    async def validate_update(
        self, original_cidr: str, updated_block: CIDRBlock, storage: StorageBackend
    ) -> ValidationResult:
        """Validate a CIDR block for update."""
        # For updates, we need to exclude the original block from duplicate/overlap checks
        result = ValidationResult(is_valid=True)

        # Get all existing blocks except the one being updated
        all_blocks = await storage.list(limit=1000)  # TODO: Handle pagination properly
        other_blocks = [b for b in all_blocks if b.cidr != original_cidr]

        # Run validation against other blocks
        for rule in self.validation_rules:
            if rule.__name__ in ["_validate_no_duplicates", "_validate_no_overlaps"]:
                # Use modified storage that excludes the original block
                mock_storage = MockStorageForUpdate(other_blocks)
                await rule(updated_block, mock_storage, result)
            else:
                await rule(updated_block, storage, result)

        return result

    async def _validate_cidr_format(
        self, block: CIDRBlock, storage: StorageBackend, result: ValidationResult
    ) -> None:
        """Validate CIDR format is correct - IPv4 only."""
        try:
            IPv4Network(block.cidr, strict=False)
        except AddressValueError as e:
            result.add_error(f"Invalid CIDR format: {str(e)}")

    async def _validate_parent_exists(
        self, block: CIDRBlock, storage: StorageBackend, result: ValidationResult
    ) -> None:
        """Validate that parent CIDR exists if specified."""
        if not block.parent:
            return

        parent_block = await storage.get(block.parent)
        if not parent_block:
            result.add_error(f"Parent CIDR {block.parent} does not exist")

    async def _validate_parent_relationship(
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
                result.add_error(
                    f"CIDR {block.cidr} is not a subnet of parent {block.parent}"
                )
        except (AddressValueError, AttributeError) as e:
            result.add_error(f"Cannot validate parent relationship: {str(e)}")

    async def _validate_no_duplicates(
        self, block: CIDRBlock, storage: StorageBackend, result: ValidationResult
    ) -> None:
        """Validate that CIDR doesn't already exist."""
        existing_block = await storage.get(block.cidr)
        if existing_block:
            result.add_error(f"CIDR {block.cidr} already exists")

    async def _validate_no_overlaps(
        self, block: CIDRBlock, storage: StorageBackend, result: ValidationResult
    ) -> None:
        """Validate that CIDR doesn't overlap with existing blocks."""
        try:
            # Get the network object for the new block (IPv4 only)
            new_net = IPv4Network(block.cidr, strict=False)

            # Check against all existing blocks
            all_blocks = await storage.list(
                limit=1000
            )  # TODO: Handle pagination properly

            for existing_block in all_blocks:
                if existing_block.cidr == block.cidr:
                    continue  # Skip self

                try:
                    # Get network for existing block (IPv4 only)
                    existing_net = IPv4Network(existing_block.cidr, strict=False)

                    # Check for overlaps
                    if new_net.overlaps(existing_net):
                        # Allow if one is a subnet of the other (hierarchy)
                        if not (
                            new_net.subnet_of(existing_net)
                            or existing_net.subnet_of(new_net)
                        ):
                            result.add_error(
                                f"CIDR {block.cidr} overlaps with existing CIDR {existing_block.cidr}"
                            )

                except AddressValueError:
                    # Skip invalid existing blocks
                    continue

        except AddressValueError as e:
            result.add_error(f"Cannot validate overlaps: {str(e)}")

    async def _validate_hierarchy_consistency(
        self, block: CIDRBlock, storage: StorageBackend, result: ValidationResult
    ) -> None:
        """Validate that the CIDR hierarchy remains consistent."""
        if not block.parent:
            return

        try:
            # Get all blocks to check hierarchy
            all_blocks = await storage.list(
                limit=1000
            )  # TODO: Handle pagination properly

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


class MockStorageForUpdate:
    """Mock storage that excludes specific blocks for update validation."""

    def __init__(self, blocks: List[CIDRBlock]):
        self.blocks = blocks

    async def get(self, cidr: str) -> Optional[CIDRBlock]:
        """Get a CIDR block by its CIDR notation."""
        for block in self.blocks:
            if block.cidr == cidr:
                return block
        return None

    async def list(
        self, offset: int = 0, limit: int = 100, tags: Optional[List[str]] = None
    ) -> List[CIDRBlock]:
        """List CIDR blocks with optional filtering."""
        blocks = self.blocks

        # Filter by tags if provided
        if tags:
            filtered_blocks = []
            for block in blocks:
                if any(tag in block.tags for tag in tags):
                    filtered_blocks.append(block)
            blocks = filtered_blocks

        # Apply pagination
        return blocks[offset : offset + limit]
