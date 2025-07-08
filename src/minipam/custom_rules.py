"""
Example of how to create custom rules for the CIDR validation engine.

This demonstrates how to extend the rule engine with custom validation rules.
"""

import ipaddress
import logging
import re

from .models import CIDRBlock
from .rules import CIDRValidationRule, ValidationResult
from .storage import CIDRStorage

# Setup logger
logger = logging.getLogger("minipam.custom_rules")


class CIDRNamePatternRule(CIDRValidationRule):
    """Example rule that validates CIDR names follow a certain pattern"""

    def __init__(self, pattern: str = r"^[a-zA-Z0-9_\- ]+$"):
        """
        Initialize with a regex pattern that names must match.

        Args:
            pattern: Regular expression that valid names must match
        """
        self.pattern = pattern
        self._regex = re.compile(pattern)

    @property
    def name(self) -> str:
        return "cidr_name_pattern"

    async def validate(
        self, block: CIDRBlock, storage: CIDRStorage
    ) -> ValidationResult:
        # Skip validation if name is None/empty
        if not block.name:
            return ValidationResult.success()

        if not self._regex.match(block.name):
            return ValidationResult.failure(
                f"CIDR name '{block.name}' does not match required pattern {self.pattern}"
            )

        return ValidationResult.success()


class ReservedRangeRule(CIDRValidationRule):
    """Example rule that prevents allocation of certain reserved CIDR ranges"""

    def __init__(self, reserved_ranges=None):
        """
        Initialize with a list of reserved CIDR ranges.

        Args:
            reserved_ranges: List of CIDR strings that are reserved
        """
        # Default reserved ranges if none provided
        self.reserved_ranges = reserved_ranges or [
            "127.0.0.0/8",  # Loopback
            "169.254.0.0/16",  # Link local
            "224.0.0.0/4",  # Multicast
            "240.0.0.0/4",  # Future use
        ]
        # Convert to network objects for easier comparison
        self.reserved_networks = [
            ipaddress.ip_network(cidr) for cidr in self.reserved_ranges
        ]

    @property
    def name(self) -> str:
        return "reserved_range"

    async def validate(
        self, block: CIDRBlock, storage: CIDRStorage
    ) -> ValidationResult:
        try:
            cidr_network = ipaddress.ip_network(block.cidr)

            for reserved in self.reserved_networks:
                # Check if this CIDR overlaps with any reserved range
                if cidr_network.overlaps(reserved):
                    return ValidationResult.failure(
                        f"CIDR {block.cidr} overlaps with reserved range {reserved}"
                    )

            return ValidationResult.success()
        except ValueError as e:
            # This should be caught by model validation already
            return ValidationResult.failure(f"Invalid CIDR format: {e}")


def register_custom_rules():
    """Register custom rules with the rule engine"""
    from .rules import rule_engine

    # Register name pattern rule
    rule_engine.register_rule(CIDRNamePatternRule())

    # Register reserved range rule
    rule_engine.register_rule(ReservedRangeRule())

    logger.info("Custom CIDR validation rules registered")
