"""
Rule engine for CIDR validation.

This module provides a pluggable rule engine for validating CIDR blocks
before they are added or updated in the system.
"""

import ipaddress
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from .models import CIDRBlock
from .storage import CIDRStorage

# Setup logger
logger = logging.getLogger("minipam.rules")


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


class ValidationError(Exception):
    """Exception raised when a validation rule fails"""

    def __init__(self, message: str, rule_name: Optional[str] = None):
        self.message = message
        self.rule_name = rule_name
        super().__init__(message)


class CIDRValidationRule(ABC):
    """Base class for CIDR validation rules"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the rule for identification"""

    @abstractmethod
    async def validate(
        self, block: CIDRBlock, storage: CIDRStorage
    ) -> ValidationResult:
        """
        Validate a CIDR block against the rule.

        Args:
            block: The CIDR block to validate
            storage: Storage backend to query existing data

        Returns:
            ValidationResult: Result of the validation check
        """


class NoDuplicateCIDRRule(CIDRValidationRule):
    """Rule that validates that a CIDR block doesn't already exist"""

    @property
    def name(self) -> str:
        return "no_duplicate_cidr"

    async def validate(
        self, block: CIDRBlock, storage: CIDRStorage
    ) -> ValidationResult:
        # Check if the CIDR already exists
        existing = await storage.get(block.cidr)
        if existing is not None:
            return ValidationResult.failure(f"CIDR block '{block.cidr}' already exists")

        return ValidationResult.success()


class SmallestParentRule(CIDRValidationRule):
    """
    Rule that validates a CIDR block is assigned to the smallest possible parent.

    For example, if 10.0.0.0/8 exists (under 0.0.0.0/0) and you try to add
    10.0.0.0/16 directly to 0.0.0.0/0, it should fail because 10.0.0.0/16
    should be a child of 10.0.0.0/8 instead.
    """

    @property
    def name(self) -> str:
        return "smallest_parent"

    async def validate(
        self, block: CIDRBlock, storage: CIDRStorage
    ) -> ValidationResult:
        # Skip validation if no parent is specified
        if block.parent is None:
            return ValidationResult.success()

        # Parse the CIDR block
        try:
            cidr_network = ipaddress.ip_network(block.cidr)
        except ValueError as e:
            # This should be caught by the model validation already
            # but we'll check again to be safe
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


class RuleEngine:
    """
    Rule engine for validating CIDR blocks.

    This class maintains a registry of validation rules and applies them
    to CIDR blocks before they are added or updated in the system.
    """

    def __init__(self):
        self._rules: Dict[str, CIDRValidationRule] = {}

    def register_rule(self, rule: CIDRValidationRule) -> None:
        """Register a new validation rule"""
        self._rules[rule.name] = rule
        logger.debug(f"Registered validation rule: {rule.name}")

    def register_rules(self, rules: List[CIDRValidationRule]) -> None:
        """Register multiple validation rules at once"""
        for rule in rules:
            self.register_rule(rule)

    def get_rule(self, name: str) -> Optional[CIDRValidationRule]:
        """Get a rule by name"""
        return self._rules.get(name)

    def list_rules(self) -> List[str]:
        """List all registered rule names"""
        return list(self._rules.keys())

    async def validate(
        self, block: CIDRBlock, storage: CIDRStorage
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a CIDR block against all registered rules.

        Args:
            block: The CIDR block to validate
            storage: Storage backend to query existing data

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
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


# Create global rule engine instance
rule_engine = RuleEngine()

# Register default rules
rule_engine.register_rules(
    [
        NoDuplicateCIDRRule(),
        SmallestParentRule(),
    ]
)


async def validate_cidr(block: CIDRBlock, storage: CIDRStorage) -> None:
    """
    Validate a CIDR block against all registered rules.
    Raises ValidationError if any rule fails.

    Args:
        block: The CIDR block to validate
        storage: Storage backend to query existing data

    Raises:
        ValidationError: If any validation rule fails
    """
    valid, message = await rule_engine.validate(block, storage)

    if not valid:
        raise ValidationError(message or "Validation failed")
