"""
Storage backends for CIDR Management Service
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

import atomicwrites
import filelock
from fastapi.concurrency import run_in_threadpool

from .config_loader import get_storage_config
from .debug import DEBUG_MODE, log_storage_operation
from .models import CIDRBlock

# Setup logger
logger = logging.getLogger("minipam.storage")


class CIDRStorage(ABC):
    """Abstract base class for CIDR block storage backends"""

    @abstractmethod
    async def get(self, cidr: str) -> Optional[CIDRBlock]:
        """Retrieve a CIDR block by its CIDR string"""

    @abstractmethod
    async def put(self, block: CIDRBlock) -> None:
        """Store or update a CIDR block"""

    @abstractmethod
    async def delete(self, cidr: str) -> None:
        """Delete a CIDR block by its CIDR string"""

    @abstractmethod
    async def list(self) -> List[CIDRBlock]:
        """List all CIDR blocks"""


class InMemoryCIDRStorage(CIDRStorage):
    """In-memory storage backend for CIDR blocks"""

    def __init__(self):
        self._storage: Dict[str, CIDRBlock] = {}
        if DEBUG_MODE:
            logger.debug("Initialized InMemoryCIDRStorage")

    async def get(self, cidr: str) -> Optional[CIDRBlock]:
        """Retrieve a CIDR block by its CIDR string"""
        block = self._storage.get(cidr)

        if DEBUG_MODE:
            success = block is not None
            log_storage_operation(
                "get", cidr, data=block.dict() if success else None, success=success
            )

        return block

    async def put(self, block: CIDRBlock) -> None:
        """Store or update a CIDR block"""
        self._storage[block.cidr] = block

        if DEBUG_MODE:
            log_storage_operation("put", block.cidr, data=block.dict(), success=True)

    async def delete(self, cidr: str) -> None:
        """Delete a CIDR block by its CIDR string"""
        success = cidr in self._storage

        if cidr in self._storage:
            del self._storage[cidr]

        if DEBUG_MODE:
            log_storage_operation("delete", cidr, success=success)

    async def list(self) -> List[CIDRBlock]:
        """List all CIDR blocks"""
        blocks = list(self._storage.values())

        if DEBUG_MODE:
            blocks_data = [block.dict() for block in blocks]
            log_storage_operation("list", "all", data=blocks_data, success=True)

        return blocks


class FileCIDRStorage(CIDRStorage):
    """File-based storage backend for CIDR blocks with concurrent access protection"""

    def __init__(self, file_path: Optional[str] = None):
        if file_path is None:
            storage_config = get_storage_config()
            file_path = storage_config.get("file", {}).get("path", "cidrs.json")

        self.file_path = Path(file_path)
        self.lock_path = str(self.file_path) + ".lock"
        self.lock = filelock.FileLock(self.lock_path)

        if DEBUG_MODE:
            logger.debug(f"Initialized FileCIDRStorage with path: {self.file_path}")

    def _load_data_sync(self) -> Dict[str, Dict]:
        """Load data from file, return empty dict if file doesn't exist or is invalid"""
        try:
            if not self.file_path.exists():
                if DEBUG_MODE:
                    logger.debug(f"Storage file does not exist: {self.file_path}")
                return {}

            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    if DEBUG_MODE:
                        logger.warning(
                            f"Storage file contains invalid data type: {type(data)}"
                        )
                    return {}

                if DEBUG_MODE:
                    logger.debug(f"Loaded {len(data)} CIDR blocks from file")
                return data

        except (json.JSONDecodeError, IOError) as e:
            if DEBUG_MODE:
                logger.error(f"Error loading storage file: {e}")
            return {}

    def _save_data_sync(self, data: Dict[str, Dict]) -> None:
        """Save data to file using atomic writes"""
        # Ensure parent directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if DEBUG_MODE:
            logger.debug(f"Saving {len(data)} CIDR blocks to file")

        # Use atomicwrites to safely write the file
        with atomicwrites.atomic_write(
            str(self.file_path), mode="w", encoding="utf-8", overwrite=True
        ) as f:
            json.dump(data, f, indent=2, default=str)

    async def get(self, cidr: str) -> Optional[CIDRBlock]:
        """Retrieve a CIDR block by its CIDR string"""

        def sync_get():
            with self.lock:
                data = self._load_data_sync()
                return data.get(cidr)

        block_data = await run_in_threadpool(sync_get)

        if block_data is None:
            if DEBUG_MODE:
                log_storage_operation("get", cidr, success=False)
            return None

        try:
            block = CIDRBlock(**block_data)
            if DEBUG_MODE:
                log_storage_operation("get", cidr, data=block_data, success=True)
            return block
        except (ValueError, TypeError, KeyError) as e:
            if DEBUG_MODE:
                logger.error(f"Error parsing CIDR block {cidr}: {e}")
                log_storage_operation("get", cidr, success=False)
            return None

    async def put(self, block: CIDRBlock) -> None:
        """Store or update a CIDR block"""

        def sync_put():
            with self.lock:
                data = self._load_data_sync()
                block_dict = block.dict()
                data[block.cidr] = block_dict
                self._save_data_sync(data)
                return block_dict

        block_dict = await run_in_threadpool(sync_put)
        if DEBUG_MODE:
            log_storage_operation("put", block.cidr, data=block_dict, success=True)

    async def delete(self, cidr: str) -> None:
        """Delete a CIDR block by its CIDR string"""

        def sync_delete():
            with self.lock:
                data = self._load_data_sync()
                if cidr in data:
                    del data[cidr]
                    self._save_data_sync(data)
                    return True
                return False

        success = await run_in_threadpool(sync_delete)
        if DEBUG_MODE:
            log_storage_operation("delete", cidr, success=success)

    async def list(self) -> List[CIDRBlock]:
        """List all CIDR blocks"""

        def sync_list():
            with self.lock:
                return self._load_data_sync()

        data = await run_in_threadpool(sync_list)
        blocks = []
        for block_data in data.values():
            try:
                blocks.append(CIDRBlock(**block_data))
            except (ValueError, TypeError, KeyError) as e:
                # Skip invalid blocks
                if DEBUG_MODE:
                    logger.warning(f"Skipping invalid block: {e}")
                continue

        if DEBUG_MODE:
            blocks_data = [block.dict() for block in blocks]
            log_storage_operation("list", "all", data=blocks_data, success=True)

        return blocks


def get_cidr_storage() -> CIDRStorage:
    """Factory function to get the appropriate storage backend"""
    storage_config = get_storage_config()
    storage_type = storage_config.get("type", "memory")

    if storage_type == "file":
        file_path = storage_config.get("file", {}).get("path", "cidrs.json")
        if DEBUG_MODE:
            logger.debug(f"Using file-based storage backend: {file_path}")
        return FileCIDRStorage(file_path)
    else:
        if DEBUG_MODE:
            logger.debug("Using in-memory storage backend")
        return InMemoryCIDRStorage()
