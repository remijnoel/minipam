"""
MiniPAM - A minimalistic IPAM solution

This package provides a FastAPI-based CIDR block management service
with pluggable storage backends.
"""

__version__ = "1.0.0"

# Lazy imports to avoid circular dependencies and import issues
def create_app(*args, **kwargs):
    """Create FastAPI application (lazy import)"""
    from .main import create_app as _create_app
    return _create_app(*args, **kwargs)

from .models import CIDRBlock
from .storage import CIDRStorage, FileCIDRStorage, InMemoryCIDRStorage

__all__ = [
    "CIDRBlock",
    "CIDRStorage",
    "InMemoryCIDRStorage",
    "FileCIDRStorage",
    "create_app",
]
