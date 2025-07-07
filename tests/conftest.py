"""
Pytest configuration and shared fixtures for minipam tests
"""

import asyncio
import os

# Add src to Python path for testing
import sys
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from minipam.models import CIDRBlock
from minipam.storage import FileCIDRStorage, InMemoryCIDRStorage


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_cidr_block() -> CIDRBlock:
    """Create a sample CIDR block for testing."""
    return CIDRBlock(
        cidr="192.168.1.0/24",
        name="Test Network",
        description="Test network for unit testing",
        tags={"environment": "test", "priority": "high"},
    )


@pytest.fixture
def another_cidr_block() -> CIDRBlock:
    """Create another sample CIDR block for testing."""
    return CIDRBlock(
        cidr="10.0.0.0/8",
        name="Corporate Network",
        description="Enterprise network range",
        tags={"environment": "corporate", "priority": "medium"},
        children=["10.1.0.0/16", "10.2.0.0/16"],
    )


@pytest.fixture
def memory_storage() -> InMemoryCIDRStorage:
    """Create an in-memory storage instance for testing."""
    return InMemoryCIDRStorage()


@pytest.fixture
def file_storage() -> Generator[FileCIDRStorage, None, None]:
    """Create a file-based storage instance for testing."""
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_file = f.name

    storage = FileCIDRStorage(temp_file)
    yield storage

    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)
    lock_file = temp_file + ".lock"
    if os.path.exists(lock_file):
        os.unlink(lock_file)


@pytest.fixture
def temp_file_path() -> Generator[str, None, None]:
    """Create a temporary file path for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_file = f.name

    yield temp_file

    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)
    lock_file = temp_file + ".lock"
    if os.path.exists(lock_file):
        os.unlink(lock_file)
