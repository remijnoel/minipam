"""
MiniPAM - A minimalistic IPAM solution

This package provides a FastAPI-based CIDR block management service
with pluggable storage backends.
"""

__version__ = "1.0.0"

from .main import create_app
from .models import CIDRBlock
from .storage import CIDRStorage, FileCIDRStorage, InMemoryCIDRStorage

__all__ = [
    "CIDRBlock",
    "CIDRStorage",
    "InMemoryCIDRStorage",
    "FileCIDRStorage",
    "create_app",
]
