"""
Unit tests for minipam.storage module
"""

import pytest

from minipam.models import CIDRBlock
from minipam.storage import FileCIDRStorage, InMemoryCIDRStorage


class TestInMemoryCIDRStorage:
    """Test cases for InMemoryCIDRStorage"""

    @pytest.mark.asyncio
    async def test_empty_storage(self, memory_storage):
        """Test that empty storage returns empty list"""
        blocks = await memory_storage.list()
        assert blocks == []

    @pytest.mark.asyncio
    async def test_get_nonexistent_block(self, memory_storage):
        """Test getting a non-existent CIDR block"""
        block = await memory_storage.get("192.168.1.0/24")
        assert block is None

    @pytest.mark.asyncio
    async def test_put_and_get_block(self, memory_storage, sample_cidr_block):
        """Test storing and retrieving a CIDR block"""
        await memory_storage.put(sample_cidr_block)

        retrieved = await memory_storage.get(sample_cidr_block.cidr)
        assert retrieved is not None
        assert retrieved.cidr == sample_cidr_block.cidr
        assert retrieved.name == sample_cidr_block.name

    @pytest.mark.asyncio
    async def test_put_multiple_blocks(
        self, memory_storage, sample_cidr_block, another_cidr_block
    ):
        """Test storing multiple CIDR blocks"""
        await memory_storage.put(sample_cidr_block)
        await memory_storage.put(another_cidr_block)

        blocks = await memory_storage.list()
        assert len(blocks) == 2

        cidrs = [block.cidr for block in blocks]
        assert sample_cidr_block.cidr in cidrs
        assert another_cidr_block.cidr in cidrs

    @pytest.mark.asyncio
    async def test_update_block(self, memory_storage, sample_cidr_block):
        """Test updating an existing CIDR block"""
        await memory_storage.put(sample_cidr_block)

        # Update the block
        updated_block = sample_cidr_block.copy()
        updated_block.name = "Updated Network"
        updated_block.description = "Updated description"

        await memory_storage.put(updated_block)

        retrieved = await memory_storage.get(sample_cidr_block.cidr)
        assert retrieved.name == "Updated Network"
        assert retrieved.description == "Updated description"

        # Should still have only one block
        blocks = await memory_storage.list()
        assert len(blocks) == 1

    @pytest.mark.asyncio
    async def test_delete_block(self, memory_storage, sample_cidr_block):
        """Test deleting a CIDR block"""
        await memory_storage.put(sample_cidr_block)

        # Verify it exists
        retrieved = await memory_storage.get(sample_cidr_block.cidr)
        assert retrieved is not None

        # Delete it
        await memory_storage.delete(sample_cidr_block.cidr)

        # Verify it's gone
        retrieved = await memory_storage.get(sample_cidr_block.cidr)
        assert retrieved is None

        blocks = await memory_storage.list()
        assert len(blocks) == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_block(self, memory_storage):
        """Test deleting a non-existent CIDR block (should not raise error)"""
        await memory_storage.delete("192.168.1.0/24")
        # Should not raise any exception


class TestFileCIDRStorage:
    """Test cases for FileCIDRStorage"""

    @pytest.mark.asyncio
    async def test_empty_storage(self, file_storage):
        """Test that empty storage returns empty list"""
        blocks = await file_storage.list()
        assert blocks == []

    @pytest.mark.asyncio
    async def test_get_nonexistent_block(self, file_storage):
        """Test getting a non-existent CIDR block"""
        block = await file_storage.get("192.168.1.0/24")
        assert block is None

    @pytest.mark.asyncio
    async def test_put_and_get_block(self, file_storage, sample_cidr_block):
        """Test storing and retrieving a CIDR block"""
        await file_storage.put(sample_cidr_block)

        retrieved = await file_storage.get(sample_cidr_block.cidr)
        assert retrieved is not None
        assert retrieved.cidr == sample_cidr_block.cidr
        assert retrieved.name == sample_cidr_block.name

    @pytest.mark.asyncio
    async def test_put_multiple_blocks(
        self, file_storage, sample_cidr_block, another_cidr_block
    ):
        """Test storing multiple CIDR blocks"""
        await file_storage.put(sample_cidr_block)
        await file_storage.put(another_cidr_block)

        blocks = await file_storage.list()
        assert len(blocks) == 2

        cidrs = [block.cidr for block in blocks]
        assert sample_cidr_block.cidr in cidrs
        assert another_cidr_block.cidr in cidrs

    @pytest.mark.asyncio
    async def test_persistence(self, temp_file_path, sample_cidr_block):
        """Test that data persists between storage instances"""
        # Create first storage instance and save data
        storage1 = FileCIDRStorage(temp_file_path)
        await storage1.put(sample_cidr_block)

        # Create second storage instance and verify data is there
        storage2 = FileCIDRStorage(temp_file_path)
        retrieved = await storage2.get(sample_cidr_block.cidr)
        assert retrieved is not None
        assert retrieved.cidr == sample_cidr_block.cidr

    @pytest.mark.asyncio
    async def test_update_block(self, file_storage, sample_cidr_block):
        """Test updating an existing CIDR block"""
        await file_storage.put(sample_cidr_block)

        # Update the block
        updated_block = sample_cidr_block.copy()
        updated_block.name = "Updated Network"
        updated_block.description = "Updated description"

        await file_storage.put(updated_block)

        retrieved = await file_storage.get(sample_cidr_block.cidr)
        assert retrieved.name == "Updated Network"
        assert retrieved.description == "Updated description"

        # Should still have only one block
        blocks = await file_storage.list()
        assert len(blocks) == 1

    @pytest.mark.asyncio
    async def test_delete_block(self, file_storage, sample_cidr_block):
        """Test deleting a CIDR block"""
        await file_storage.put(sample_cidr_block)

        # Verify it exists
        retrieved = await file_storage.get(sample_cidr_block.cidr)
        assert retrieved is not None

        # Delete it
        await file_storage.delete(sample_cidr_block.cidr)

        # Verify it's gone
        retrieved = await file_storage.get(sample_cidr_block.cidr)
        assert retrieved is None

        blocks = await file_storage.list()
        assert len(blocks) == 0

    @pytest.mark.asyncio
    async def test_concurrent_access(
        self, temp_file_path, sample_cidr_block, another_cidr_block
    ):
        """Test concurrent access to file storage"""
        storage1 = FileCIDRStorage(temp_file_path)
        storage2 = FileCIDRStorage(temp_file_path)

        # Both storages should be able to operate safely
        await storage1.put(sample_cidr_block)
        await storage2.put(another_cidr_block)

        # Both blocks should be accessible from both storage instances
        blocks1 = await storage1.list()
        blocks2 = await storage2.list()

        assert len(blocks1) == 2
        assert len(blocks2) == 2

        cidrs1 = [block.cidr for block in blocks1]
        cidrs2 = [block.cidr for block in blocks2]

        assert sample_cidr_block.cidr in cidrs1
        assert another_cidr_block.cidr in cidrs1
        assert sample_cidr_block.cidr in cidrs2
        assert another_cidr_block.cidr in cidrs2
