"""
Test script for CIDR validation rules
"""

import asyncio
import datetime
import ipaddress
import logging
import sys
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("test_rules")


# Create a simple model for testing
class CIDRBlock:
    """Simple model for CIDR block with metadata for testing"""

    def __init__(
        self,
        cidr: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        parent: Optional[str] = None,
    ):
        self.cidr = cidr
        self.name = name
        self.description = description
        self.tags = tags or {}
        self.parent = parent
        self.created_at = datetime.datetime.utcnow()


# Create a simple memory storage for testing
class InMemoryCIDRStorage:
    """In-memory storage for testing"""

    def __init__(self):
        self._storage = {}

    async def get(self, cidr: str) -> Optional[CIDRBlock]:
        return self._storage.get(cidr)

    async def put(self, block: CIDRBlock) -> None:
        self._storage[block.cidr] = block

    async def delete(self, cidr: str) -> None:
        if cidr in self._storage:
            del self._storage[cidr]

    async def list(self) -> List[CIDRBlock]:
        return list(self._storage.values())


# Validation Result class
class ValidationResult:
    """Result of a validation rule check"""

    def __init__(self, valid: bool, message: Optional[str] = None):
        self.valid = valid
        self.message = message

    @classmethod
    def success(cls) -> "ValidationResult":
        """Return a successful validation result"""
        return cls(True)

    @classmethod
    def failure(cls, message: str) -> "ValidationResult":
        """Return a failed validation result with error message"""
        return cls(False, message)

    def __bool__(self) -> bool:
        """Allow using the result in boolean context"""
        return self.valid


# Validation error exception
class ValidationError(Exception):
    """Exception raised when a validation rule fails"""

    def __init__(self, message: str, rule_name: Optional[str] = None):
        self.message = message
        self.rule_name = rule_name
        super().__init__(message)


# Abstract base class for CIDR validation rules
class CIDRValidationRule:
    """Base class for CIDR validation rules"""

    @property
    def name(self) -> str:
        """Name of the rule for identification"""
        raise NotImplementedError("Subclasses must implement name property")

    async def validate(
        self, block: CIDRBlock, storage: InMemoryCIDRStorage
    ) -> ValidationResult:
        """
        Validate a CIDR block against the rule.

        Args:
            block: The CIDR block to validate
            storage: Storage backend to query existing data

        Returns:
            ValidationResult: Result of the validation check
        """
        raise NotImplementedError("Subclasses must implement validate method")


# No duplicate CIDR rule
class NoDuplicateCIDRRule(CIDRValidationRule):
    """Rule that validates that a CIDR block doesn't already exist"""

    @property
    def name(self) -> str:
        return "no_duplicate_cidr"

    async def validate(
        self, block: CIDRBlock, storage: InMemoryCIDRStorage
    ) -> ValidationResult:
        # Check if the CIDR already exists
        existing = await storage.get(block.cidr)
        if existing is not None:
            return ValidationResult.failure(f"CIDR block '{block.cidr}' already exists")

        return ValidationResult.success()


# Smallest parent rule
class SmallestParentRule(CIDRValidationRule):
    """
    Rule that validates a CIDR block is assigned to the smallest possible parent.
    """

    @property
    def name(self) -> str:
        return "smallest_parent"

    async def validate(
        self, block: CIDRBlock, storage: InMemoryCIDRStorage
    ) -> ValidationResult:
        # Skip validation if no parent is specified
        if block.parent is None:
            return ValidationResult.success()

        # Parse the CIDR block
        try:
            cidr_network = ipaddress.ip_network(block.cidr)
        except ValueError as e:
            return ValidationResult.failure(f"Invalid CIDR format: {e}")

        # Parse the parent CIDR
        try:
            parent_network = ipaddress.ip_network(block.parent)
        except ValueError as e:
            return ValidationResult.failure(f"Invalid parent CIDR format: {e}")

        # Check if the CIDR is a subnet of the parent
        if not cidr_network.subnet_of(parent_network):
            return ValidationResult.failure(
                f"CIDR {block.cidr} is not a subnet of parent {block.parent}"
            )

        # Find all possible parent CIDRs that contain this CIDR
        all_cidrs = await storage.list()
        potential_parents = []

        for existing_block in all_cidrs:
            if existing_block.cidr == block.cidr or existing_block.cidr == block.parent:
                continue  # Skip self and specified parent

            try:
                existing_network = ipaddress.ip_network(existing_block.cidr)

                # Check if this existing block contains our CIDR
                if (
                    cidr_network.subnet_of(existing_network)
                    and existing_network.subnet_of(parent_network)
                    and existing_network != parent_network
                ):
                    # This is a more specific parent than the one specified
                    potential_parents.append(existing_block.cidr)
            except ValueError:
                continue  # Skip invalid CIDRs

        if potential_parents:
            # Find the smallest (most specific) potential parent
            smallest_parent = None
            smallest_prefix_len = -1

            for parent_cidr in potential_parents:
                parent_net = ipaddress.ip_network(parent_cidr)
                if parent_net.prefixlen > smallest_prefix_len:
                    smallest_prefix_len = parent_net.prefixlen
                    smallest_parent = parent_cidr

            if smallest_parent:
                return ValidationResult.failure(
                    f"CIDR {block.cidr} should be assigned to the more specific parent {smallest_parent} "
                    f"instead of {block.parent}"
                )

        return ValidationResult.success()


# Rule engine
class RuleEngine:
    """Rule engine for validating CIDR blocks"""

    def __init__(self):
        self._rules = {}

    def register_rule(self, rule: CIDRValidationRule) -> None:
        """Register a new validation rule"""
        self._rules[rule.name] = rule
        logger.debug(f"Registered validation rule: {rule.name}")

    def register_rules(self, rules: List[CIDRValidationRule]) -> None:
        """Register multiple validation rules at once"""
        for rule in rules:
            self.register_rule(rule)

    async def validate(
        self, block: CIDRBlock, storage: InMemoryCIDRStorage
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a CIDR block against all registered rules.
        """
        for rule_name, rule in self._rules.items():
            logger.debug(f"Applying rule '{rule_name}' to CIDR {block.cidr}")
            result = await rule.validate(block, storage)

            if not result:
                logger.info(
                    f"Rule '{rule_name}' failed for CIDR {block.cidr}: {result.message}"
                )
                return False, result.message

        logger.debug(f"All rules passed for CIDR {block.cidr}")
        return True, None


async def validate_cidr(block: CIDRBlock, storage: InMemoryCIDRStorage) -> None:
    """Validate a CIDR block against all registered rules"""
    engine = RuleEngine()
    engine.register_rules(
        [
            NoDuplicateCIDRRule(),
            SmallestParentRule(),
        ]
    )

    valid, message = await engine.validate(block, storage)

    if not valid:
        raise ValidationError(message or "Validation failed")


async def test_rules():
    """Test the CIDR validation rules"""
    # Create a storage backend
    storage = InMemoryCIDRStorage()

    print("\n===== Testing CIDR Validation Rules =====\n")

    # Test 1: Create a root CIDR
    print("Test 1: Create a root CIDR (0.0.0.0/0)")
    root = CIDRBlock(cidr="0.0.0.0/0", name="Root", description="Root CIDR")
    try:
        await validate_cidr(root, storage)
        await storage.put(root)
        print("✅ Success: Root CIDR created")
    except ValidationError as e:
        print(f"❌ Error: {e}")

    # Test 2: Create a duplicate CIDR (should fail)
    print("\nTest 2: Create a duplicate CIDR (0.0.0.0/0)")
    duplicate = CIDRBlock(
        cidr="0.0.0.0/0", name="Duplicate Root", description="Should fail"
    )
    try:
        await validate_cidr(duplicate, storage)
        await storage.put(duplicate)
        print("❌ Failed: Duplicate CIDR was allowed")
    except ValidationError as e:
        print(f"✅ Success: Caught error - {e}")

    # Test 3: Create a proper hierarchy
    print("\nTest 3: Create a proper hierarchy (10.0.0.0/8 under 0.0.0.0/0)")
    block1 = CIDRBlock(
        cidr="10.0.0.0/8",
        name="RFC1918 - Class A",
        description="Private Address Space",
        parent="0.0.0.0/0",
    )
    try:
        await validate_cidr(block1, storage)
        await storage.put(block1)
        print("✅ Success: Created 10.0.0.0/8 under 0.0.0.0/0")
    except ValidationError as e:
        print(f"❌ Error: {e}")

    # Test 4: Create a proper sub-hierarchy
    print("\nTest 4: Create a proper sub-hierarchy (10.0.0.0/16 under 10.0.0.0/8)")
    block2 = CIDRBlock(
        cidr="10.0.0.0/16",
        name="Class B in 10/8",
        description="Network subdivision",
        parent="10.0.0.0/8",
    )
    try:
        await validate_cidr(block2, storage)
        await storage.put(block2)
        print("✅ Success: Created 10.0.0.0/16 under 10.0.0.0/8")
    except ValidationError as e:
        print(f"❌ Error: {e}")

    # Test 5: Create with wrong parent - should fail smallest parent rule
    print("\nTest 5: Create with wrong parent (10.0.1.0/24 directly under 0.0.0.0/0)")
    block3 = CIDRBlock(
        cidr="10.0.1.0/24",
        name="Invalid Parent",
        description="Should fail - wrong parent",
        parent="0.0.0.0/0",
    )
    try:
        await validate_cidr(block3, storage)
        await storage.put(block3)
        print("❌ Failed: Allowed incorrect parent hierarchy")
    except ValidationError as e:
        print(f"✅ Success: Caught error - {e}")

    # Test 6: Create with correct parent after previous failure
    print("\nTest 6: Create with correct parent (10.0.1.0/24 under 10.0.0.0/8)")
    block4 = CIDRBlock(
        cidr="10.0.1.0/24",
        name="Proper Parent",
        description="Correct parent assignment",
        parent="10.0.0.0/8",
    )
    try:
        await validate_cidr(block4, storage)
        await storage.put(block4)
        print("✅ Success: Created 10.0.1.0/24 under 10.0.0.0/8")
    except ValidationError as e:
        print(f"❌ Error: {e}")

    # Test 7: Create with most specific parent
    print("\nTest 7: Create with most specific parent (10.0.0.0/24 under 10.0.0.0/16)")
    block5 = CIDRBlock(
        cidr="10.0.0.0/24",
        name="Specific Parent",
        description="Child of /16",
        parent="10.0.0.0/16",
    )
    try:
        await validate_cidr(block5, storage)
        await storage.put(block5)
        print("✅ Success: Created 10.0.0.0/24 under 10.0.0.0/16")
    except ValidationError as e:
        print(f"❌ Error: {e}")

    # Test 8: Another test with incorrect parent - should fail smallest parent rule
    print("\nTest 8: Create with wrong parent (10.0.0.1/32 under 10.0.0.0/8)")
    block6 = CIDRBlock(
        cidr="10.0.0.1/32",
        name="Wrong Grandparent",
        description="Should use /24 or /16 as parent",
        parent="10.0.0.0/8",
    )
    try:
        await validate_cidr(block6, storage)
        await storage.put(block6)
        print("❌ Failed: Allowed incorrect parent hierarchy")
    except ValidationError as e:
        print(f"✅ Success: Caught error - {e}")

    print("\n===== Test Results =====")
    all_cidrs = await storage.list()
    print(f"\nTotal CIDRs in storage: {len(all_cidrs)}")
    for cidr in all_cidrs:
        print(f"- {cidr.cidr} (parent: {cidr.parent or 'None'})")


if __name__ == "__main__":
    asyncio.run(test_rules())
