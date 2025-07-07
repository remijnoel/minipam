"""
CIDR Block Management Service

A FastAPI-based service for managing CIDR blocks with pluggable storage backends.
Supports in-memory and file-based storage with concurrent access protection.
"""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

import filelock
import atomicwrites
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field
import uvicorn


# Configuration
USE_FILE_BACKEND = os.getenv("USE_FILE_BACKEND", "false").lower() == "true"
CIDR_FILE_PATH = os.getenv("CIDR_FILE_PATH", "cidrs.json")


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
    children: List[str] = Field(default_factory=list, description="Child CIDR blocks")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


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

    async def get(self, cidr: str) -> Optional[CIDRBlock]:
        """Retrieve a CIDR block by its CIDR string"""
        return self._storage.get(cidr)

    async def put(self, block: CIDRBlock) -> None:
        """Store or update a CIDR block"""
        self._storage[block.cidr] = block

    async def delete(self, cidr: str) -> None:
        """Delete a CIDR block by its CIDR string"""
        if cidr in self._storage:
            del self._storage[cidr]

    async def list(self) -> List[CIDRBlock]:
        """List all CIDR blocks"""
        return list(self._storage.values())


class FileCIDRStorage(CIDRStorage):
    """File-based storage backend for CIDR blocks with concurrent access protection"""

    def __init__(self, file_path: str = CIDR_FILE_PATH):
        self.file_path = Path(file_path)
        self.lock_path = str(self.file_path) + ".lock"
        self.lock = filelock.FileLock(self.lock_path)

    def _load_data(self) -> Dict[str, Dict]:
        """Load data from file, return empty dict if file doesn't exist or is invalid"""
        try:
            if not self.file_path.exists():
                return {}

            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    return {}
                return data
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_data(self, data: Dict[str, Dict]) -> None:
        """Save data to file using atomic writes"""
        # Ensure parent directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Use atomicwrites to safely write the file
        with atomicwrites.atomic_write(
            str(self.file_path), mode="w", encoding="utf-8", overwrite=True
        ) as f:
            json.dump(data, f, indent=2, default=str)

    async def get(self, cidr: str) -> Optional[CIDRBlock]:
        """Retrieve a CIDR block by its CIDR string"""
        with self.lock:
            data = self._load_data()
            if cidr not in data:
                return None

            try:
                return CIDRBlock(**data[cidr])
            except Exception:
                return None

    async def put(self, block: CIDRBlock) -> None:
        """Store or update a CIDR block"""
        with self.lock:
            data = self._load_data()
            data[block.cidr] = block.dict()
            self._save_data(data)

    async def delete(self, cidr: str) -> None:
        """Delete a CIDR block by its CIDR string"""
        with self.lock:
            data = self._load_data()
            if cidr in data:
                del data[cidr]
                self._save_data(data)

    async def list(self) -> List[CIDRBlock]:
        """List all CIDR blocks"""
        with self.lock:
            data = self._load_data()
            blocks = []
            for cidr, block_data in data.items():
                try:
                    blocks.append(CIDRBlock(**block_data))
                except Exception:
                    # Skip invalid blocks
                    continue
            return blocks


# Storage backend factory
def get_cidr_storage() -> CIDRStorage:
    """Factory function to get the appropriate storage backend"""
    if USE_FILE_BACKEND:
        return FileCIDRStorage()
    else:
        return InMemoryCIDRStorage()


# FastAPI app
app = FastAPI(
    title="CIDR Block Management Service",
    description="A service for managing CIDR blocks with pluggable storage backends",
    version="1.0.0",
)

# Global storage instance (singleton pattern for simplicity)
_storage_instance = None


def get_storage() -> CIDRStorage:
    """Dependency injection for storage backend"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = get_cidr_storage()
    return _storage_instance


@app.get("/cidrs/", response_model=List[CIDRBlock])
async def list_cidrs(storage: CIDRStorage = Depends(get_storage)):
    """List all CIDR blocks"""
    return await storage.list()


@app.post("/cidrs/", response_model=CIDRBlock, status_code=status.HTTP_201_CREATED)
async def create_or_update_cidr(
    block: CIDRBlock, storage: CIDRStorage = Depends(get_storage)
):
    """Create or update a CIDR block"""
    await storage.put(block)
    return block


@app.get("/cidrs/{cidr:path}", response_model=CIDRBlock)
async def get_cidr(cidr: str, storage: CIDRStorage = Depends(get_storage)):
    """Retrieve a CIDR block by CIDR string"""
    block = await storage.get(cidr)
    if block is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CIDR block '{cidr}' not found",
        )
    return block


@app.delete("/cidrs/{cidr:path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cidr(cidr: str, storage: CIDRStorage = Depends(get_storage)):
    """Delete a CIDR block by CIDR string"""
    block = await storage.get(cidr)
    if block is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CIDR block '{cidr}' not found",
        )
    await storage.delete(cidr)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "backend": "file" if USE_FILE_BACKEND else "memory"}


if __name__ == "__main__":
    # For development use
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
