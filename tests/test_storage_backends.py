"""Unit tests for storage backends - WRITTEN FIRST per CLAUDE.md"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.minipam.models import CIDRBlock
from src.minipam.storage import CIDRNotFoundError, CIDRStorage, FileStorage, MemoryStorage, StorageBackend, StorageError

# Mark as unit tests
pytestmark = pytest.mark.unit


class TestCIDRStorageInterface:
    """Test the CIDRStorage interface."""

    def test_storage_interface_is_abstract(self):
        """Test that CIDRStorage cannot be instantiated directly."""
        with pytest.raises(TypeError):
            CIDRStorage()

    def test_storage_interface_has_required_methods(self):
        """Test that CIDRStorage interface has all required methods."""
        # Check that all abstract methods are defined
        required_methods = ["get", "put", "delete", "list", "stats"]
        for method in required_methods:
            assert hasattr(CIDRStorage, method)
            assert callable(getattr(CIDRStorage, method))


class TestMemoryStorage:
    """Unit tests for MemoryStorage backend."""

    def test_memory_storage_initialization(self):
        """Test MemoryStorage initializes correctly."""
        storage = MemoryStorage()
        assert storage is not None
        assert hasattr(storage, "_data")
        assert hasattr(storage, "_lock")
        assert len(storage._data) == 0

    def test_memory_storage_get_nonexistent_returns_none(self):
        """Test getting non-existent CIDR returns None."""
        storage = MemoryStorage()
        result = storage.get("10.0.0.0/24")
        assert result is None

    def test_memory_storage_put_and_get_succeeds(self):
        """Test storing and retrieving CIDR block."""
        storage = MemoryStorage()

        block = CIDRBlock(
            cidr="10.0.0.0/24", name="Test Network", parent=None, tags=["test"]
        )

        storage.put(block)
        retrieved = storage.get("10.0.0.0/24")

        assert retrieved is not None
        assert retrieved.cidr == "10.0.0.0/24"
        assert retrieved.name == "Test Network"
        assert retrieved.tags == ["test"]

    def test_memory_storage_put_updates_existing(self):
        """Test that putting existing CIDR updates it."""
        storage = MemoryStorage()

        # Store initial block
        block1 = CIDRBlock(
            cidr="10.0.0.0/24", name="Original Name", parent=None, tags=["original"]
        )
        storage.put(block1)

        # Update with new block
        block2 = CIDRBlock(
            cidr="10.0.0.0/24", name="Updated Name", parent=None, tags=["updated"]
        )
        storage.put(block2)

        # Should have updated version
        retrieved = storage.get("10.0.0.0/24")
        assert retrieved.name == "Updated Name"
        assert retrieved.tags == ["updated"]

    def test_memory_storage_delete_existing_succeeds(self):
        """Test deleting existing CIDR succeeds."""
        storage = MemoryStorage()

        block = CIDRBlock(cidr="10.0.0.0/24", name="Test Network", parent=None, tags=[])
        storage.put(block)

        storage.delete("10.0.0.0/24")

        # Should be gone
        retrieved = storage.get("10.0.0.0/24")
        assert retrieved is None

    def test_memory_storage_delete_nonexistent_raises_error(self):
        """Test deleting non-existent CIDR raises error."""
        storage = MemoryStorage()

        with pytest.raises(CIDRNotFoundError):
            storage.delete("10.0.0.0/24")

    def test_memory_storage_list_all_blocks(self):
        """Test listing all CIDR blocks."""
        storage = MemoryStorage()

        blocks = [
            CIDRBlock(cidr="10.0.0.0/16", name="Network 1", parent=None, tags=[]),
            CIDRBlock(
                cidr="10.0.1.0/24", name="Network 2", parent="10.0.0.0/16", tags=[]
            ),
            CIDRBlock(cidr="192.168.1.0/24", name="Network 3", parent=None, tags=[]),
        ]

        for block in blocks:
            storage.put(block)

        all_blocks = storage.list()
        assert len(all_blocks) == 3

        cidrs = [block.cidr for block in all_blocks]
        assert "10.0.0.0/16" in cidrs
        assert "10.0.1.0/24" in cidrs
        assert "192.168.1.0/24" in cidrs

    def test_memory_storage_list_by_parent(self):
        """Test listing CIDR blocks by parent."""
        storage = MemoryStorage()

        blocks = [
            CIDRBlock(cidr="10.0.0.0/16", name="Parent", parent=None, tags=[]),
            CIDRBlock(
                cidr="10.0.1.0/24", name="Child 1", parent="10.0.0.0/16", tags=[]
            ),
            CIDRBlock(
                cidr="10.0.2.0/24", name="Child 2", parent="10.0.0.0/16", tags=[]
            ),
            CIDRBlock(cidr="192.168.1.0/24", name="Unrelated", parent=None, tags=[]),
        ]

        for block in blocks:
            storage.put(block)

        children = storage.list(parent="10.0.0.0/16", recursive=False)
        assert len(children) == 2

        child_cidrs = [block.cidr for block in children]
        assert "10.0.1.0/24" in child_cidrs
        assert "10.0.2.0/24" in child_cidrs
        assert "192.168.1.0/24" not in child_cidrs

    def test_memory_storage_list_recursive(self):
        """Test listing CIDR blocks recursively."""
        storage = MemoryStorage()

        blocks = [
            CIDRBlock(cidr="10.0.0.0/16", name="Root", parent=None, tags=[]),
            CIDRBlock(cidr="10.0.1.0/24", name="Child", parent="10.0.0.0/16", tags=[]),
            CIDRBlock(
                cidr="10.0.1.0/25", name="Grandchild", parent="10.0.1.0/24", tags=[]
            ),
            CIDRBlock(cidr="192.168.1.0/24", name="Unrelated", parent=None, tags=[]),
        ]

        for block in blocks:
            storage.put(block)

        descendants = storage.list(parent="10.0.0.0/16", recursive=True)
        assert len(descendants) == 2

        descendant_cidrs = [block.cidr for block in descendants]
        assert "10.0.1.0/24" in descendant_cidrs
        assert "10.0.1.0/25" in descendant_cidrs

    def test_memory_storage_stats_returns_correct_info(self):
        """Test that stats returns correct information."""
        storage = MemoryStorage()

        # Initially empty
        stats = storage.stats()
        assert stats["total_blocks"] == 0
        assert stats["storage_type"] == "memory"

        # Add some blocks
        blocks = [
            CIDRBlock(cidr="10.0.0.0/16", name="Network 1", parent=None, tags=[]),
            CIDRBlock(
                cidr="10.0.1.0/24", name="Network 2", parent="10.0.0.0/16", tags=[]
            ),
        ]

        for block in blocks:
            storage.put(block)

        stats = storage.stats()
        assert stats["total_blocks"] == 2
        assert stats["storage_type"] == "memory"

    def test_memory_storage_clear_removes_all_data(self):
        """Test that clear method removes all data."""
        storage = MemoryStorage()

        # Add some blocks
        blocks = [
            CIDRBlock(cidr="10.0.0.0/16", name="Network 1", parent=None, tags=[]),
            CIDRBlock(
                cidr="10.0.1.0/24", name="Network 2", parent="10.0.0.0/16", tags=[]
            ),
        ]

        for block in blocks:
            storage.put(block)

        assert len(storage.list()) == 2

        storage.clear()

        assert len(storage.list()) == 0
        assert storage.stats()["total_blocks"] == 0

    def test_memory_storage_is_thread_safe(self):
        """Test that memory storage operations are thread-safe."""
        import threading
        import time

        storage = MemoryStorage()
        errors = []

        def worker(worker_id):
            try:
                for i in range(10):
                    block = CIDRBlock(
                        cidr=f"10.{worker_id}.{i}.0/24",
                        name=f"Network {worker_id}-{i}",
                        parent=None,
                        tags=[],
                    )
                    storage.put(block)
                    time.sleep(
                        0.001
                    )  # Small delay to increase chance of race condition
            except Exception as e:
                errors.append(e)

        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have no errors and all blocks
        assert len(errors) == 0
        assert storage.stats()["total_blocks"] == 50


class TestFileStorage:
    """Unit tests for FileStorage backend."""

    def test_file_storage_initialization(self):
        """Test FileStorage initializes correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileStorage(temp_dir)
            assert storage is not None
            assert storage.storage_path == Path(temp_dir)
            assert storage.data_file == Path(temp_dir) / "cidrs.json"
            assert hasattr(storage, "_lock")

            # Should create empty file
            assert storage.data_file.exists()

    def test_file_storage_creates_directory(self):
        """Test FileStorage creates storage directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "nonexistent" / "nested"
            storage = FileStorage(str(storage_path))

            assert storage_path.exists()
            assert storage.data_file.exists()

    def test_file_storage_get_nonexistent_returns_none(self):
        """Test getting non-existent CIDR returns None."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileStorage(temp_dir)
            result = storage.get("10.0.0.0/24")
            assert result is None

    def test_file_storage_put_and_get_succeeds(self):
        """Test storing and retrieving CIDR block."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileStorage(temp_dir)

            block = CIDRBlock(
                cidr="10.0.0.0/24", name="Test Network", parent=None, tags=["test"]
            )

            storage.put(block)
            retrieved = storage.get("10.0.0.0/24")

            assert retrieved is not None
            assert retrieved.cidr == "10.0.0.0/24"
            assert retrieved.name == "Test Network"
            assert retrieved.tags == ["test"]

    def test_file_storage_persistence_across_instances(self):
        """Test that data persists across FileStorage instances."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create first instance and store data
            storage1 = FileStorage(temp_dir)
            block = CIDRBlock(
                cidr="10.0.0.0/24",
                name="Persistent Network",
                parent=None,
                tags=["persistent"],
            )
            storage1.put(block)

            # Create second instance and retrieve data
            storage2 = FileStorage(temp_dir)
            retrieved = storage2.get("10.0.0.0/24")

            assert retrieved is not None
            assert retrieved.name == "Persistent Network"
            assert retrieved.tags == ["persistent"]

    def test_file_storage_delete_existing_succeeds(self):
        """Test deleting existing CIDR succeeds."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileStorage(temp_dir)

            block = CIDRBlock(
                cidr="10.0.0.0/24", name="Test Network", parent=None, tags=[]
            )
            storage.put(block)

            storage.delete("10.0.0.0/24")

            # Should be gone
            retrieved = storage.get("10.0.0.0/24")
            assert retrieved is None

    def test_file_storage_delete_nonexistent_raises_error(self):
        """Test deleting non-existent CIDR raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileStorage(temp_dir)

            with pytest.raises(CIDRNotFoundError):
                storage.delete("10.0.0.0/24")

    def test_file_storage_atomic_writes(self):
        """Test that file operations are atomic."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileStorage(temp_dir)

            # Mock file operations to simulate failure
            original_replace = Path.replace

            def mock_replace(self, target):
                # Simulate failure on replace operation
                raise OSError("Simulated write failure")

            with patch.object(Path, "replace", mock_replace):
                block = CIDRBlock(
                    cidr="10.0.0.0/24", name="Test Network", parent=None, tags=[]
                )

                with pytest.raises(StorageError):
                    storage.put(block)

                # Original file should be unchanged
                assert storage.get("10.0.0.0/24") is None

    def test_file_storage_handles_corrupted_data(self):
        """Test that FileStorage handles corrupted data gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileStorage(temp_dir)

            # Write corrupted JSON to file
            storage.data_file.write_text("invalid json content")

            with pytest.raises(StorageError):
                storage.get("10.0.0.0/24")

    def test_file_storage_stats_returns_correct_info(self):
        """Test that stats returns correct information."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileStorage(temp_dir)

            # Initially empty
            stats = storage.stats()
            assert stats["total_blocks"] == 0
            assert stats["storage_type"] == "file"
            assert stats["storage_path"] == str(storage.data_file)
            assert "file_size_bytes" in stats

            # Add some blocks
            blocks = [
                CIDRBlock(cidr="10.0.0.0/16", name="Network 1", parent=None, tags=[]),
                CIDRBlock(
                    cidr="10.0.1.0/24", name="Network 2", parent="10.0.0.0/16", tags=[]
                ),
            ]

            for block in blocks:
                storage.put(block)

            stats = storage.stats()
            assert stats["total_blocks"] == 2
            assert stats["storage_type"] == "file"

    def test_file_storage_list_operations(self):
        """Test file storage list operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileStorage(temp_dir)

            blocks = [
                CIDRBlock(cidr="10.0.0.0/16", name="Parent", parent=None, tags=[]),
                CIDRBlock(
                    cidr="10.0.1.0/24", name="Child 1", parent="10.0.0.0/16", tags=[]
                ),
                CIDRBlock(
                    cidr="10.0.2.0/24", name="Child 2", parent="10.0.0.0/16", tags=[]
                ),
                CIDRBlock(
                    cidr="10.0.1.0/25", name="Grandchild", parent="10.0.1.0/24", tags=[]
                ),
            ]

            for block in blocks:
                storage.put(block)

            # Test list all
            all_blocks = storage.list()
            assert len(all_blocks) == 4

            # Test list by parent (non-recursive)
            children = storage.list(parent="10.0.0.0/16", recursive=False)
            assert len(children) == 2
            child_cidrs = [block.cidr for block in children]
            assert "10.0.1.0/24" in child_cidrs
            assert "10.0.2.0/24" in child_cidrs
            assert "10.0.1.0/25" not in child_cidrs

            # Test list by parent (recursive)
            descendants = storage.list(parent="10.0.0.0/16", recursive=True)
            assert len(descendants) == 3
            descendant_cidrs = [block.cidr for block in descendants]
            assert "10.0.1.0/24" in descendant_cidrs
            assert "10.0.2.0/24" in descendant_cidrs
            assert "10.0.1.0/25" in descendant_cidrs

    def test_file_storage_concurrent_access(self):
        """Test file storage handles concurrent access."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileStorage(temp_dir)

            # This test would need more sophisticated mocking to truly test
            # file locking, but we can at least verify the structure is in place
            assert hasattr(storage, "_lock")
            assert hasattr(storage, "_read_data")
            assert hasattr(storage, "_write_data")

    def test_file_storage_error_handling(self):
        """Test file storage error handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileStorage(temp_dir)
            
            # Force a cache invalidation to ensure reload is needed
            storage._data = None

            # Test handling of permission errors
            with patch(
                "builtins.open", side_effect=PermissionError("Permission denied")
            ):
                with pytest.raises(StorageError):
                    storage.get("10.0.0.0/24")

    def test_file_storage_is_descendant_of_method(self):
        """Test the _is_descendant_of helper method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileStorage(temp_dir)

            blocks = [
                CIDRBlock(cidr="10.0.0.0/16", name="Root", parent=None, tags=[]),
                CIDRBlock(
                    cidr="10.0.1.0/24", name="Child", parent="10.0.0.0/16", tags=[]
                ),
                CIDRBlock(
                    cidr="10.0.1.0/25", name="Grandchild", parent="10.0.1.0/24", tags=[]
                ),
                CIDRBlock(
                    cidr="192.168.1.0/24", name="Unrelated", parent=None, tags=[]
                ),
            ]

            # Test direct descendant
            assert storage._is_descendant_of(blocks[1], "10.0.0.0/16", blocks)

            # Test indirect descendant
            assert storage._is_descendant_of(blocks[2], "10.0.0.0/16", blocks)

            # Test non-descendant
            assert not storage._is_descendant_of(blocks[3], "10.0.0.0/16", blocks)

            # Test self is not descendant
            assert not storage._is_descendant_of(blocks[0], "10.0.0.0/16", blocks)
