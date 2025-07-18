"""
Storage backends for MiniPAM.

This module provides different storage backends for persisting CIDR blocks.
"""

import fcntl
import json
import os
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import CIDRBlock, CIDRBlockCreate, CIDRBlockUpdate


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def create(self, block_data: CIDRBlockCreate) -> CIDRBlock:
        """Create a new CIDR block."""
        pass

    @abstractmethod
    async def get(self, cidr: str) -> Optional[CIDRBlock]:
        """Get a CIDR block by its CIDR notation."""
        pass

    @abstractmethod
    async def list(
        self, offset: int = 0, limit: int = 100, tags: Optional[List[str]] = None
    ) -> List[CIDRBlock]:
        """List CIDR blocks with optional filtering."""
        pass

    @abstractmethod
    async def update(self, cidr: str, updates: CIDRBlockUpdate) -> Optional[CIDRBlock]:
        """Update a CIDR block."""
        pass

    @abstractmethod
    async def delete(self, cidr: str) -> bool:
        """Delete a CIDR block."""
        pass

    @abstractmethod
    async def count(self, tags: Optional[List[str]] = None) -> int:
        """Count total number of CIDR blocks."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on storage backend."""
        pass


class MemoryStorage(StorageBackend):
    """In-memory storage backend for development and testing."""

    def __init__(self):
        self._blocks: Dict[str, CIDRBlock] = {}

    async def create(self, block_data: CIDRBlockCreate) -> CIDRBlock:
        """Create a new CIDR block."""
        if block_data.cidr in self._blocks:
            raise ValueError(f"CIDR block {block_data.cidr} already exists")

        block = CIDRBlock(
            cidr=block_data.cidr,
            name=block_data.name,
            description=block_data.description,
            parent=block_data.parent,
            tags=block_data.tags,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
        )

        self._blocks[block.cidr] = block
        return block

    async def get(self, cidr: str) -> Optional[CIDRBlock]:
        """Get a CIDR block by its CIDR notation."""
        return self._blocks.get(cidr)

    async def list(
        self, offset: int = 0, limit: int = 100, tags: Optional[List[str]] = None
    ) -> List[CIDRBlock]:
        """List CIDR blocks with optional filtering."""
        blocks = list(self._blocks.values())

        # Filter by tags if provided
        if tags:
            filtered_blocks = []
            for block in blocks:
                if any(tag in block.tags for tag in tags):
                    filtered_blocks.append(block)
            blocks = filtered_blocks

        # Apply pagination
        return blocks[offset : offset + limit]

    async def update(self, cidr: str, updates: CIDRBlockUpdate) -> Optional[CIDRBlock]:
        """Update a CIDR block."""
        if cidr not in self._blocks:
            return None

        block = self._blocks[cidr]
        update_data = updates.model_dump(exclude_unset=True)

        # Update fields
        for field, value in update_data.items():
            setattr(block, field, value)

        block.updated_at = datetime.now(timezone.utc)
        return block

    async def delete(self, cidr: str) -> bool:
        """Delete a CIDR block."""
        if cidr in self._blocks:
            del self._blocks[cidr]
            return True
        return False

    async def count(self, tags: Optional[List[str]] = None) -> int:
        """Count total number of CIDR blocks."""
        if not tags:
            return len(self._blocks)

        count = 0
        for block in self._blocks.values():
            if any(tag in block.tags for tag in tags):
                count += 1
        return count

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on storage backend."""
        return {
            "type": "memory",
            "status": "healthy",
            "total_blocks": len(self._blocks),
        }


class FileStorage(StorageBackend):
    """File-based storage backend with atomic writes and locking."""

    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.data_file = self.storage_path / "cidr_blocks.json"
        self.lock_file = self.storage_path / "cidr_blocks.lock"

        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize data file if it doesn't exist
        if not self.data_file.exists():
            self._write_data({})

    def _acquire_lock(self):
        """Acquire file lock for atomic operations."""
        self.lock_file.touch()
        self._lock_fd = open(self.lock_file, "w")
        fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_EX)

    def _release_lock(self):
        """Release file lock."""
        if hasattr(self, "_lock_fd"):
            fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_UN)
            self._lock_fd.close()
            delattr(self, "_lock_fd")

    def _read_data(self) -> Dict[str, Dict[str, Any]]:
        """Read data from file with error handling."""
        try:
            with open(self.data_file, "r") as f:
                data = json.load(f)
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_data(self, data: Dict[str, Dict[str, Any]]) -> None:
        """Write data to file atomically."""
        # Write to temporary file first
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=self.storage_path,
            prefix="cidr_blocks_",
            suffix=".tmp",
            delete=False,
        ) as tmp_file:
            json.dump(data, tmp_file, indent=2, default=str)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
            tmp_path = tmp_file.name

        # Atomic move
        os.rename(tmp_path, self.data_file)

    def _serialize_block(self, block: CIDRBlock) -> Dict[str, Any]:
        """Serialize CIDR block for JSON storage."""
        return block.model_dump()

    def _deserialize_block(self, data: Dict[str, Any]) -> CIDRBlock:
        """Deserialize CIDR block from JSON data."""
        return CIDRBlock(**data)

    async def create(self, block_data: CIDRBlockCreate) -> CIDRBlock:
        """Create a new CIDR block."""
        self._acquire_lock()
        try:
            data = self._read_data()

            if block_data.cidr in data:
                raise ValueError(f"CIDR block {block_data.cidr} already exists")

            block = CIDRBlock(
                cidr=block_data.cidr,
                name=block_data.name,
                description=block_data.description,
                parent=block_data.parent,
                tags=block_data.tags,
                created_at=datetime.now(timezone.utc),
                updated_at=None,
            )

            data[block.cidr] = self._serialize_block(block)
            self._write_data(data)

            return block
        finally:
            self._release_lock()

    async def get(self, cidr: str) -> Optional[CIDRBlock]:
        """Get a CIDR block by its CIDR notation."""
        data = self._read_data()
        block_data = data.get(cidr)

        if block_data:
            return self._deserialize_block(block_data)
        return None

    async def list(
        self, offset: int = 0, limit: int = 100, tags: Optional[List[str]] = None
    ) -> List[CIDRBlock]:
        """List CIDR blocks with optional filtering."""
        data = self._read_data()
        blocks = []

        for block_data in data.values():
            block = self._deserialize_block(block_data)

            # Filter by tags if provided
            if tags and not any(tag in block.tags for tag in tags):
                continue

            blocks.append(block)

        # Sort by creation time (newest first)
        blocks.sort(key=lambda x: x.created_at, reverse=True)

        # Apply pagination
        return blocks[offset : offset + limit]

    async def update(self, cidr: str, updates: CIDRBlockUpdate) -> Optional[CIDRBlock]:
        """Update a CIDR block."""
        self._acquire_lock()
        try:
            data = self._read_data()

            if cidr not in data:
                return None

            block = self._deserialize_block(data[cidr])
            update_data = updates.model_dump(exclude_unset=True)

            # Update fields
            for field, value in update_data.items():
                setattr(block, field, value)

            block.updated_at = datetime.now(timezone.utc)

            data[cidr] = self._serialize_block(block)
            self._write_data(data)

            return block
        finally:
            self._release_lock()

    async def delete(self, cidr: str) -> bool:
        """Delete a CIDR block."""
        self._acquire_lock()
        try:
            data = self._read_data()

            if cidr in data:
                del data[cidr]
                self._write_data(data)
                return True
            return False
        finally:
            self._release_lock()

    async def count(self, tags: Optional[List[str]] = None) -> int:
        """Count total number of CIDR blocks."""
        data = self._read_data()

        if not tags:
            return len(data)

        count = 0
        for block_data in data.values():
            block = self._deserialize_block(block_data)
            if any(tag in block.tags for tag in tags):
                count += 1
        return count

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on storage backend."""
        try:
            # Test read access
            data = self._read_data()

            # Test write access
            test_file = self.storage_path / "health_check.tmp"
            test_file.write_text("test")
            test_file.unlink()

            return {
                "type": "file",
                "status": "healthy",
                "path": str(self.storage_path),
                "total_blocks": len(data),
                "readable": True,
                "writable": True,
            }
        except Exception as e:
            return {
                "type": "file",
                "status": "unhealthy",
                "path": str(self.storage_path),
                "error": str(e),
                "readable": False,
                "writable": False,
            }


def create_storage_backend(storage_type: str, **kwargs) -> StorageBackend:
    """Factory function to create storage backends."""
    if storage_type == "memory":
        return MemoryStorage()
    elif storage_type == "file":
        storage_path = kwargs.get("path")
        if not storage_path:
            raise ValueError("File storage requires 'path' parameter")
        return FileStorage(storage_path)
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")
