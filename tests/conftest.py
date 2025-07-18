"""Pytest configuration and fixtures."""

import shutil
import tempfile
from pathlib import Path

import pytest

from src.minipam.api import reset_dependencies
from src.minipam.config import reset_configuration
from src.minipam.models import CIDRBlock
from src.minipam.storage import MemoryStorage


@pytest.fixture(autouse=True)
def reset_state():
    """Reset global state before each test."""
    reset_configuration()
    reset_dependencies()
    yield
    reset_configuration()
    reset_dependencies()


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def memory_storage():
    """Create memory storage instance."""
    return MemoryStorage()


@pytest.fixture
def sample_cidrs():
    """Sample CIDR blocks for testing."""
    return [
        CIDRBlock(
            cidr="10.0.0.0/16",
            name="Corporate Network",
            parent=None,
            tags=["corp", "main"],
        ),
        CIDRBlock(
            cidr="10.0.1.0/24",
            name="DMZ Network",
            parent="10.0.0.0/16",
            tags=["dmz", "public"],
        ),
        CIDRBlock(
            cidr="10.0.2.0/24",
            name="Internal Network",
            parent="10.0.0.0/16",
            tags=["internal", "private"],
        ),
        CIDRBlock(
            cidr="192.168.1.0/24", name="Lab Network", parent=None, tags=["lab", "test"]
        ),
    ]


@pytest.fixture
async def populated_storage(memory_storage, sample_cidrs):
    """Memory storage populated with sample data."""
    for cidr in sample_cidrs:
        from src.minipam.models import CIDRBlockCreate

        cidr_data = CIDRBlockCreate(
            cidr=cidr.cidr,
            name=cidr.name,
            description=cidr.description,
            parent=cidr.parent,
            tags=cidr.tags,
        )
        await memory_storage.create(cidr_data)
    return memory_storage


@pytest.fixture
def config_file(temp_storage_dir):
    """Create temporary config file."""
    config_content = f"""
server:
  host: "127.0.0.1"
  port: 8001
  debug: true

storage:
  type: "file"
  path: "{temp_storage_dir}"

auth:
  backend: "none"

ui:
  enabled: true
  path: "/ui"
"""
    config_file = Path(temp_storage_dir) / "test_config.yaml"
    config_file.write_text(config_content)
    return str(config_file)
