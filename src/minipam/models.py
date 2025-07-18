"""
Data models for MiniPAM.

This module defines the core data structures used throughout the application.
"""

from datetime import datetime, timezone
from ipaddress import AddressValueError, IPv4Network
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class CIDRBlock(BaseModel):
    """CIDR block model with validation and metadata."""

    cidr: str = Field(..., description="CIDR notation (e.g., 10.0.0.0/24)")
    name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(None, description="Optional description")
    parent: Optional[str] = Field(None, description="Parent CIDR block")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp",
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="Last update timestamp"
    )

    @field_validator("cidr")
    @classmethod
    def validate_cidr(cls, v: str) -> str:
        """Validate CIDR notation - IPv4 only."""
        try:
            net = IPv4Network(v, strict=False)
            # Don't allow /0 networks
            if net.prefixlen == 0:
                raise ValueError("CIDR /0 networks are not allowed")
            return v
        except AddressValueError:
            raise ValueError(f"Invalid IPv4 CIDR notation: {v}")

    @field_validator("parent")
    @classmethod
    def validate_parent(cls, v: Optional[str]) -> Optional[str]:
        """Validate parent CIDR notation if provided - IPv4 only."""
        if v is None:
            return v
        try:
            net = IPv4Network(v, strict=False)
            # Don't allow /0 networks as parent
            if net.prefixlen == 0:
                raise ValueError("CIDR /0 networks are not allowed as parent")
            return v
        except AddressValueError:
            raise ValueError(f"Invalid parent IPv4 CIDR notation: {v}")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate tags - remove duplicates and empty strings, convert to lowercase."""
        seen = set()
        result = []
        for tag in v:
            normalized = tag.strip().lower()
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(normalized)
        return result

    @model_validator(mode="after")
    def validate_parent_relationship(self) -> "CIDRBlock":
        """Validate that parent relationship is logical."""
        if not self.cidr or not self.parent:
            return self

        try:
            # Parse networks (IPv4 only)
            cidr_net = IPv4Network(self.cidr, strict=False)
            parent_net = IPv4Network(self.parent, strict=False)

            # Check if cidr is a subnet of parent
            if not cidr_net.subnet_of(parent_net):
                raise ValueError(
                    f"CIDR {self.cidr} is not a subnet of parent {self.parent}"
                )

        except (AddressValueError, AttributeError):
            raise ValueError(
                f"Cannot validate parent relationship between {self.cidr} and {self.parent}"
            )

        return self

    def get_network(self) -> IPv4Network:
        """Get the network object for this CIDR block."""
        return IPv4Network(self.cidr, strict=False)

    def get_parent_network(self) -> Optional[IPv4Network]:
        """Get the parent network object if parent is set."""
        if not self.parent:
            return None
        return IPv4Network(self.parent, strict=False)

    def overlaps_with(self, other: "CIDRBlock") -> bool:
        """Check if this CIDR block overlaps with another."""
        try:
            self_net = self.get_network()
            other_net = other.get_network()
            return self_net.overlaps(other_net)
        except Exception:
            return False

    def contains(self, other: "CIDRBlock") -> bool:
        """Check if this CIDR block contains another."""
        try:
            self_net = self.get_network()
            other_net = other.get_network()
            return other_net.subnet_of(self_net)
        except Exception:
            return False

    def is_contained_by(self, other: "CIDRBlock") -> bool:
        """Check if this CIDR block is contained by another."""
        try:
            self_net = self.get_network()
            other_net = other.get_network()
            return self_net.subnet_of(other_net)
        except Exception:
            return False

    def is_child_of(self, other: "CIDRBlock") -> bool:
        """Check if this CIDR block is a child of another (based on containment)."""
        return self.is_contained_by(other) and self.cidr != other.cidr

    def is_parent_of(self, other: "CIDRBlock") -> bool:
        """Check if this CIDR block is a direct parent of another."""
        return other.parent == self.cidr and other.is_contained_by(self)

    def is_sibling_of(self, other: "CIDRBlock") -> bool:
        """Check if this CIDR block is a sibling of another."""
        return (
            self.parent is not None
            and self.parent == other.parent
            and self.cidr != other.cidr
        )

    def __str__(self) -> str:
        return f"{self.name} ({self.cidr})"

    def __repr__(self) -> str:
        return f"CIDRBlock(cidr='{self.cidr}', name='{self.name}')"


class ValidationError(BaseModel):
    """Validation error model."""

    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")


class ValidationResult(BaseModel):
    """Validation result model."""

    is_valid: bool = Field(..., description="Whether validation passed")
    errors: List[str] = Field(
        default_factory=list, description="List of validation errors"
    )
    warnings: List[str] = Field(
        default_factory=list, description="List of validation warnings"
    )

    def add_error(self, error: str) -> None:
        """Add a validation error."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a validation warning."""
        self.warnings.append(warning)

    @classmethod
    def success(cls) -> "ValidationResult":
        """Create a successful validation result."""
        return cls(is_valid=True, errors=[], warnings=[])

    @classmethod
    def failure(cls, errors: List[str]) -> "ValidationResult":
        """Create a failed validation result from error strings."""
        return cls(is_valid=False, errors=errors, warnings=[])


class CIDRBlockCreate(BaseModel):
    """CIDR block creation model."""

    cidr: str = Field(..., description="CIDR notation (e.g., 10.0.0.0/24)")
    name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(None, description="Optional description")
    parent: Optional[str] = Field(None, description="Parent CIDR block")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")

    @field_validator("cidr")
    @classmethod
    def validate_cidr(cls, v: str) -> str:
        """Validate CIDR notation - IPv4 only."""
        try:
            net = IPv4Network(v, strict=False)
            # Don't allow /0 networks
            if net.prefixlen == 0:
                raise ValueError("CIDR /0 networks are not allowed")
            return v
        except AddressValueError:
            raise ValueError(f"Invalid IPv4 CIDR notation: {v}")


class CIDRBlockUpdate(BaseModel):
    """CIDR block update model."""

    name: Optional[str] = Field(None, description="Human-readable name")
    description: Optional[str] = Field(None, description="Optional description")
    parent: Optional[str] = Field(None, description="Parent CIDR block")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")

    @field_validator("parent")
    @classmethod
    def validate_parent(cls, v: Optional[str]) -> Optional[str]:
        """Validate parent CIDR notation if provided - IPv4 only."""
        if v is None:
            return v
        try:
            net = IPv4Network(v, strict=False)
            # Don't allow /0 networks as parent
            if net.prefixlen == 0:
                raise ValueError("CIDR /0 networks are not allowed as parent")
            return v
        except AddressValueError:
            raise ValueError(f"Invalid parent IPv4 CIDR notation: {v}")


class CIDRBlockListResponse(BaseModel):
    """CIDR block list response model."""

    blocks: List[CIDRBlock] = Field(..., description="List of CIDR blocks")
    total: int = Field(..., description="Total number of blocks")
    offset: int = Field(0, description="Offset for pagination")
    limit: int = Field(100, description="Limit for pagination")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Health check timestamp",
    )
    storage: Dict[str, Any] = Field(
        default_factory=dict, description="Storage backend health"
    )
    auth: Dict[str, Any] = Field(
        default_factory=dict, description="Authentication backend health"
    )


class APIError(BaseModel):
    """API error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Error timestamp",
    )


class UserInfo(BaseModel):
    """User information model for authentication."""

    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    roles: List[str] = Field(default_factory=list, description="User roles")
    scopes: List[str] = Field(
        default_factory=list, description="User scopes/permissions"
    )


class AuthRequest(BaseModel):
    """Authentication request model."""

    headers: Dict[str, str] = Field(default_factory=dict, description="Request headers")
    cookies: Dict[str, str] = Field(default_factory=dict, description="Request cookies")
    query_params: Dict[str, str] = Field(
        default_factory=dict, description="Query parameters"
    )
