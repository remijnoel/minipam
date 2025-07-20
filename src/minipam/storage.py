"""
Storage backends for MiniPAM CIDR blocks.

This module provides pluggable storage backends for persisting CIDR block data.
"""

import fcntl
import json
import logging
import os
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from .models import CIDRBlock

logger = logging.getLogger(__name__)


class CIDRNotFoundError(Exception):
    """Exception raised when a CIDR block is not found."""
    pass


class StorageError(Exception):
    """General storage operation error."""
    pass


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def get(self, cidr: str) -> Optional[CIDRBlock]:
        """Get a CIDR block by its CIDR notation."""
        pass
    
    @abstractmethod
    def put(self, block: CIDRBlock) -> None:
        """Store a CIDR block."""
        pass
    
    @abstractmethod
    def delete(self, cidr: str) -> None:
        """Delete a CIDR block. Raises CIDRNotFoundError if not found."""
        pass
    
    @abstractmethod
    def list(self, **kwargs) -> List[CIDRBlock]:
        """List CIDR blocks with optional filtering."""
        pass
    
    @abstractmethod
    def stats(self) -> Dict[str, int]:
        """Get storage statistics."""
        pass
    
    @abstractmethod
    def update(self, cidr: str, updates) -> Optional[CIDRBlock]:
        """Update a CIDR block. Returns updated block or None if not found."""
        pass


# Alias for backwards compatibility
CIDRStorage = StorageBackend


class MemoryStorage(StorageBackend):
    """In-memory storage backend for development and testing."""
    
    def __init__(self):
        self._data: Dict[str, CIDRBlock] = {}
        self._lock = threading.RLock()
    
    def get(self, cidr: str) -> Optional[CIDRBlock]:
        """Get a CIDR block by its CIDR notation."""
        with self._lock:
            return self._data.get(cidr)
    
    def put(self, block: CIDRBlock) -> None:
        """Store a CIDR block."""
        with self._lock:
            self._data[block.cidr] = block
    
    def delete(self, cidr: str) -> None:
        """Delete a CIDR block. Raises CIDRNotFoundError if not found."""
        with self._lock:
            if cidr in self._data:
                del self._data[cidr]
            else:
                raise CIDRNotFoundError(f"CIDR {cidr} not found")
    
    def list(self, **kwargs) -> List[CIDRBlock]:
        """List CIDR blocks with optional filtering."""
        with self._lock:
            blocks = list(self._data.values())
            
            # Apply parent filtering if specified
            parent = kwargs.get("parent")
            recursive = kwargs.get("recursive", False)
            
            if parent:
                if recursive:
                    # Include all descendants of the parent
                    filtered_blocks = []
                    for block in blocks:
                        if self._is_descendant_of(block, parent, blocks):
                            filtered_blocks.append(block)
                    blocks = filtered_blocks
                else:
                    # Include only direct children
                    blocks = [block for block in blocks if block.parent == parent]
            
            # Sort by CIDR for consistent ordering
            blocks.sort(key=lambda x: x.cidr)
            
            return blocks
    
    def stats(self) -> Dict[str, int]:
        """Get storage statistics."""
        with self._lock:
            return {
                "total_blocks": len(self._data),
                "storage_type": "memory"
            }
    
    def health_check(self) -> Dict[str, str]:
        """Check health of memory storage."""
        return {"status": "healthy", "backend": "memory"}
    
    def clear(self) -> None:
        """Clear all data from storage."""
        with self._lock:
            self._data.clear()
    
    def update(self, cidr: str, updates) -> Optional[CIDRBlock]:
        """Update a CIDR block. Returns updated block or None if not found."""
        with self._lock:
            if cidr not in self._data:
                return None
            
            existing_block = self._data[cidr]
            update_data = updates.model_dump(exclude_unset=True)
            updated_block = existing_block.model_copy(update=update_data)
            self._data[cidr] = updated_block
            return updated_block
    
    def _is_descendant_of(self, block: CIDRBlock, ancestor_cidr: str, all_blocks: List[CIDRBlock]) -> bool:
        """Check if a block is a descendant of another CIDR."""
        if block.cidr == ancestor_cidr:
            return False  # Self is not a descendant
            
        current_parent = block.parent
        while current_parent:
            if current_parent == ancestor_cidr:
                return True
            
            # Find the parent block and continue up the chain
            parent_block = None
            for b in all_blocks:
                if b.cidr == current_parent:
                    parent_block = b
                    break
            
            if parent_block:
                current_parent = parent_block.parent
            else:
                break
                
        return False


class FileStorage(StorageBackend):
    """File-based storage backend with atomic writes and file locking."""
    
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.data_file = self.storage_path / "cidrs.json"
        self._lock = threading.RLock()
        self._data: Optional[Dict[str, CIDRBlock]] = None
        self._file_mtime: Optional[float] = None
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        self._load_data()
        
        # Create empty file if it doesn't exist
        if not self.data_file.exists():
            self._data = {}
            self._save_data()
    
    def _load_data(self) -> None:
        """Load data from file."""
        with self._lock:
            if self.data_file.exists():
                try:
                    # Track file modification time
                    self._file_mtime = self.data_file.stat().st_mtime
                    
                    with open(self.data_file, 'r') as f:
                        # Use file locking to prevent concurrent access
                        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                        try:
                            data = json.load(f)
                            self._data = {
                                cidr: CIDRBlock(**block_data)
                                for cidr, block_data in data.items()
                            }
                        finally:
                            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except json.JSONDecodeError as e:
                    logger.error(f"Corrupted storage file {self.data_file}: {e}")
                    raise StorageError(f"Corrupted storage file: {e}")
                except PermissionError as e:
                    logger.error(f"Permission denied accessing storage file {self.data_file}: {e}")
                    raise StorageError(f"Permission denied: {e}")
                except FileNotFoundError as e:
                    logger.warning(f"Storage file not found {self.data_file}: {e}")
                    self._data = {}
                    self._file_mtime = None
                except OSError as e:
                    logger.warning(f"Could not load storage file {self.data_file}: {e}")
                    self._data = {}
                    self._file_mtime = None
            else:
                self._data = {}
                self._file_mtime = None
    
    def _save_data(self) -> None:
        """Save data to file with atomic writes."""
        with self._lock:
            if self._data is None:
                return
                
            # Create temporary file for atomic write
            temp_path = self.data_file.with_suffix('.tmp')
            
            try:
                with open(temp_path, 'w') as f:
                    # Use file locking to prevent concurrent access
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    try:
                        data = {
                            cidr: block.model_dump()
                            for cidr, block in self._data.items()
                        }
                        json.dump(data, f, indent=2, default=str)
                        f.flush()
                        os.fsync(f.fileno())
                    finally:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                
                # Atomic move
                temp_path.replace(self.data_file)
                
                # Update modification time tracking
                self._file_mtime = self.data_file.stat().st_mtime
                
            except OSError as e:
                logger.error(f"Failed to save storage file {self.data_file}: {e}")
                if temp_path.exists():
                    temp_path.unlink()
                raise StorageError(f"Failed to save storage file: {e}")
    
    def get(self, cidr: str) -> Optional[CIDRBlock]:
        """Get a CIDR block by its CIDR notation."""
        with self._lock:
            try:
                # Check if we need to reload data
                should_reload = (self._data is None or 
                               (self.data_file.exists() and 
                                self._file_mtime is not None and
                                self.data_file.stat().st_mtime != self._file_mtime))
                
                if should_reload:
                    self._load_data()
                    
                if self._data is None:
                    return None
                return self._data.get(cidr)
            except Exception as e:
                if isinstance(e, StorageError):
                    raise
                logger.error(f"Error getting CIDR {cidr}: {e}")
                raise StorageError(f"Failed to get CIDR: {e}")
    
    def put(self, block: CIDRBlock) -> None:
        """Store a CIDR block."""
        with self._lock:
            if self._data is None:
                self._load_data()
            if self._data is None:
                self._data = {}
            
            # Store original value for rollback
            original_value = self._data.get(block.cidr)
            
            # Temporarily store the new block
            self._data[block.cidr] = block
            
            try:
                # Try to save to disk
                self._save_data()
            except Exception:
                # Rollback on failure
                if original_value is None:
                    # Block didn't exist before, remove it
                    self._data.pop(block.cidr, None)
                else:
                    # Restore original value
                    self._data[block.cidr] = original_value
                raise
    
    def delete(self, cidr: str) -> None:
        """Delete a CIDR block. Raises CIDRNotFoundError if not found."""
        with self._lock:
            if self._data is None:
                self._load_data()
            if self._data is None:
                self._data = {}
            
            if cidr in self._data:
                del self._data[cidr]
                self._save_data()
            else:
                raise CIDRNotFoundError(f"CIDR {cidr} not found")
    
    def list(self, **kwargs) -> List[CIDRBlock]:
        """List CIDR blocks with optional filtering."""
        with self._lock:
            if self._data is None:
                self._load_data()
            if self._data is None:
                return []
            
            blocks = list(self._data.values())
            
            # Apply parent filtering if specified
            parent = kwargs.get("parent")
            recursive = kwargs.get("recursive", False)
            
            if parent:
                if recursive:
                    # Include all descendants of the parent
                    filtered_blocks = []
                    for block in blocks:
                        if self._is_descendant_of(block, parent, blocks):
                            filtered_blocks.append(block)
                    blocks = filtered_blocks
                else:
                    # Include only direct children
                    blocks = [block for block in blocks if block.parent == parent]
            
            # Sort by CIDR for consistent ordering
            blocks.sort(key=lambda x: x.cidr)
            
            return blocks
    
    def stats(self) -> Dict[str, int]:
        """Get storage statistics."""
        with self._lock:
            if self._data is None:
                self._load_data()
            if self._data is None:
                return {
                    "total_blocks": 0,
                    "file_size_bytes": 0,
                    "storage_type": "file",
                    "storage_path": str(self.data_file)
                }
            
            file_size = self.data_file.stat().st_size if self.data_file.exists() else 0
            
            return {
                "total_blocks": len(self._data),
                "file_size_bytes": file_size,
                "storage_type": "file",
                "storage_path": str(self.data_file)
            }
    
    def health_check(self) -> Dict[str, str]:
        """Check health of file storage."""
        try:
            # Check if directory exists and is writable
            self.storage_path.mkdir(parents=True, exist_ok=True)
            # Try to read data to verify file access
            with self._lock:
                if self._data is None:
                    self._load_data()
            return {"status": "healthy", "backend": "file", "path": str(self.storage_path)}
        except Exception as e:
            return {"status": "unhealthy", "backend": "file", "error": str(e)}
    
    def _is_descendant_of(self, block: CIDRBlock, ancestor_cidr: str, all_blocks: List[CIDRBlock]) -> bool:
        """Check if a block is a descendant of another CIDR."""
        if block.cidr == ancestor_cidr:
            return False  # Self is not a descendant
            
        current_parent = block.parent
        while current_parent:
            if current_parent == ancestor_cidr:
                return True
            
            # Find the parent block and continue up the chain
            parent_block = None
            for b in all_blocks:
                if b.cidr == current_parent:
                    parent_block = b
                    break
            
            if parent_block:
                current_parent = parent_block.parent
            else:
                break
                
        return False
    
    def _read_data(self) -> None:
        """Read data from file - alias for _load_data."""
        self._load_data()
    
    def _write_data(self) -> None:
        """Write data to file - alias for _save_data."""
        self._save_data()
    
    def clear(self) -> None:
        """Clear all data from storage."""
        with self._lock:
            self._data = {}
            if self.data_file.exists():
                self.data_file.write_text('{}')
    
    def _invalidate_cache(self) -> None:
        """Invalidate the data cache to force reload."""
        self._data = None
    
    def update(self, cidr: str, updates) -> Optional[CIDRBlock]:
        """Update a CIDR block. Returns updated block or None if not found."""
        with self._lock:
            if self._data is None:
                self._load_data()
            if self._data is None:
                self._data = {}
            
            if cidr not in self._data:
                return None
            
            existing_block = self._data[cidr]
            update_data = updates.model_dump(exclude_unset=True)
            updated_block = existing_block.model_copy(update=update_data)
            
            # Store original for rollback
            original_block = self._data[cidr]
            self._data[cidr] = updated_block
            
            try:
                self._save_data()
                return updated_block
            except Exception:
                # Rollback on failure
                self._data[cidr] = original_block
                raise


def create_storage_backend(storage_type: str, **kwargs) -> StorageBackend:
    """Create a storage backend based on configuration."""
    if storage_type == "memory":
        return MemoryStorage()
    elif storage_type == "file":
        path = kwargs.get("path", "./data")
        return FileStorage(path)
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")