"""
Data models for CIDR Management Service
"""

import ipaddress
from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field, field_validator


class CIDRBlock(BaseModel):
    """Model for CIDR block with metadata"""

    cidr: str = Field(..., description="CIDR block notation (e.g., 192.168.1.0/24)")
    name: Optional[str] = Field(
        None, description="Human-readable name for the CIDR block"
    )
    description: Optional[str] = Field(
        None, description="Description of the CIDR block"
    )
    tags: Dict[str, str] = Field(default_factory=dict, description="Key-value tags")
    parent: Optional[str] = Field(None, description="Parent CIDR block")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )

    @field_validator("cidr")
    @classmethod
    def validate_cidr(cls, v):
        """Validate CIDR notation"""
        if not v or not v.strip():
            raise ValueError("CIDR cannot be empty")

        # Try to parse as IPv4 or IPv6 network
        try:
            ipaddress.ip_network(v, strict=False)
        except ValueError as e:
            raise ValueError(f"Invalid CIDR format: {e}") from e

        return v

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
