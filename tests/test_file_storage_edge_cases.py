import json
import os
from pathlib import Path

import pytest

from minipam.models import CIDRBlock
from minipam.storage import FileCIDRStorage


@pytest.fixture
def temp_file(tmp_path):
    file = tmp_path / "cidr.json"
    yield str(file)
    lock = str(file) + ".lock"
    if os.path.exists(file):
        os.unlink(file)
    if os.path.exists(lock):
        os.unlink(lock)


def make_block(cidr, **kwargs):
    data = {
        "cidr": cidr,
        "name": "n",
        "description": "d",
        "tags": {},
        "parent": None,
        "children": [],
    }
    data.update(kwargs)
    return CIDRBlock(**data)


@pytest.mark.asyncio
async def test_file_does_not_exist(temp_file):
    storage = FileCIDRStorage(temp_file)
    blocks = await storage.list()
    assert blocks == []


@pytest.mark.asyncio
async def test_empty_file(temp_file):
    Path(temp_file).touch()
    storage = FileCIDRStorage(temp_file)
    blocks = await storage.list()
    assert blocks == []


@pytest.mark.asyncio
async def test_invalid_json(temp_file):
    Path(temp_file).write_text("not a json")
    storage = FileCIDRStorage(temp_file)
    blocks = await storage.list()
    assert blocks == []


@pytest.mark.asyncio
async def test_partial_corrupt_data(temp_file):
    # One valid, one invalid
    data = {
        "1.1.1.0/24": {
            "cidr": "1.1.1.0/24",
            "name": "ok",
            "description": "",
            "tags": {},
            "parent": None,
            "children": [],
            "created_at": "2020-01-01T00:00:00",
        },
        "bad": {"foo": "bar"},
    }
    Path(temp_file).write_text(json.dumps(data))
    storage = FileCIDRStorage(temp_file)
    blocks = await storage.list()
    assert len(blocks) == 1
    assert blocks[0].cidr == "1.1.1.0/24"


@pytest.mark.asyncio
async def test_unicode_and_special_characters(temp_file):
    block = make_block("2.2.2.0/24", name="n✓", description="d€", tags={"k": "v♥"})
    storage = FileCIDRStorage(temp_file)
    await storage.put(block)
    got = await storage.get("2.2.2.0/24")
    assert got is not None
    assert got.name == "n✓"
    assert got.description == "d€"
    assert got.tags["k"] == "v♥"


@pytest.mark.asyncio
async def test_concurrent_access(temp_file):
    s1 = FileCIDRStorage(temp_file)
    s2 = FileCIDRStorage(temp_file)
    b1 = make_block("3.3.3.0/24")
    b2 = make_block("4.4.4.0/24")
    await s1.put(b1)
    await s2.put(b2)
    blocks = await s1.list()
    cidrs = {b.cidr for b in blocks}
    assert "3.3.3.0/24" in cidrs and "4.4.4.0/24" in cidrs


@pytest.mark.asyncio
async def test_persistence_across_instances(temp_file):
    block = make_block("5.5.5.0/24")
    s1 = FileCIDRStorage(temp_file)
    await s1.put(block)
    s2 = FileCIDRStorage(temp_file)
    got = await s2.get("5.5.5.0/24")
    assert got is not None
    assert got.cidr == "5.5.5.0/24"


@pytest.mark.asyncio
async def test_delete_nonexistent_block(temp_file):
    storage = FileCIDRStorage(temp_file)
    await storage.delete("nope/24")  # Should not raise


@pytest.mark.asyncio
async def test_overwrite_existing_block(temp_file):
    block = make_block("6.6.6.0/24", name="first")
    storage = FileCIDRStorage(temp_file)
    await storage.put(block)
    block2 = make_block("6.6.6.0/24", name="second")
    await storage.put(block2)
    got = await storage.get("6.6.6.0/24")
    assert got is not None
    assert got.name == "second"


@pytest.mark.asyncio
async def test_large_number_of_blocks(temp_file):
    storage = FileCIDRStorage(temp_file)
    for i in range(100):
        await storage.put(make_block(f"10.0.{i}.0/24"))
    blocks = await storage.list()
    assert len(blocks) == 100


@pytest.mark.asyncio
async def test_directory_does_not_exist(tmp_path):
    dir_path = tmp_path / "subdir"
    file_path = dir_path / "cidr.json"
    storage = FileCIDRStorage(str(file_path))
    block = make_block("7.7.7.0/24")
    await storage.put(block)
    got = await storage.get("7.7.7.0/24")
    assert got is not None
    assert got.cidr == "7.7.7.0/24"


@pytest.mark.asyncio
async def test_atomicity_on_write(temp_file, monkeypatch):
    # Simulate crash during write by raising in atomic_write
    storage = FileCIDRStorage(temp_file)
    block = make_block("8.8.8.0/24")
    orig = storage._save_data

    def fail_once(data):
        if not hasattr(fail_once, "called"):
            fail_once.called = True
            raise IOError("Simulated crash")
        return orig(data)

    monkeypatch.setattr(storage, "_save_data", fail_once)
    with pytest.raises(IOError):
        await storage.put(block)
    # Should still be empty
    blocks = await storage.list()
    assert blocks == []


@pytest.mark.asyncio
async def test_json_non_dict_root(temp_file):
    """Test when JSON file contains non-dict at root level"""
    Path(temp_file).write_text(json.dumps(["not", "a", "dict"]))
    storage = FileCIDRStorage(temp_file)
    blocks = await storage.list()
    assert blocks == []


@pytest.mark.asyncio
async def test_very_long_file_path(tmp_path):
    """Test with extremely long file path"""
    # Create a very nested directory structure
    deep_path = tmp_path
    for i in range(10):
        deep_path = deep_path / f"very_long_directory_name_{i}"
    file_path = deep_path / "cidr.json"

    storage = FileCIDRStorage(str(file_path))
    block = make_block("9.9.9.0/24")
    await storage.put(block)

    got = await storage.get("9.9.9.0/24")
    assert got is not None
    assert got.cidr == "9.9.9.0/24"


@pytest.mark.asyncio
async def test_file_permissions_readable_only(temp_file):
    """Test behavior when file is read-only"""
    storage = FileCIDRStorage(temp_file)
    block = make_block("10.10.10.0/24")

    # Create the file first
    await storage.put(block)

    # Make file read-only
    os.chmod(temp_file, 0o444)

    try:
        # Should be able to read
        got = await storage.get("10.10.10.0/24")
        assert got is not None
        assert got.cidr == "10.10.10.0/24"

        # Note: atomicwrites creates temp files, so this might not fail
        # Let's just test that we can still read from read-only files
        blocks = await storage.list()
        assert len(blocks) == 1
        assert blocks[0].cidr == "10.10.10.0/24"
    finally:
        # Restore permissions for cleanup
        os.chmod(temp_file, 0o644)


@pytest.mark.asyncio
async def test_empty_cidr_string(temp_file):
    """Test handling of empty CIDR strings"""
    storage = FileCIDRStorage(temp_file)

    # This should be handled gracefully by the storage layer
    # even though it's invalid
    await storage.delete("")  # Should not raise

    got = await storage.get("")
    assert got is None


@pytest.mark.asyncio
async def test_stress_concurrent_operations(temp_file):
    """Test many concurrent operations"""
    import asyncio

    storage = FileCIDRStorage(temp_file)

    # Create multiple tasks that read/write concurrently
    async def worker(worker_id):
        for i in range(10):
            block = make_block(
                f"172.16.{worker_id}.{i}/24", name=f"worker_{worker_id}_block_{i}"
            )
            await storage.put(block)

            # Verify it was stored
            got = await storage.get(f"172.16.{worker_id}.{i}/24")
            assert got is not None
            assert got.name == f"worker_{worker_id}_block_{i}"

    # Run 5 workers concurrently
    tasks = [worker(i) for i in range(5)]
    await asyncio.gather(*tasks)

    # Verify all blocks are present
    blocks = await storage.list()
    assert len(blocks) == 50  # 5 workers * 10 blocks each


@pytest.mark.asyncio
async def test_json_with_null_values(temp_file):
    """Test JSON file with null values"""
    data = {
        "192.168.100.0/24": {
            "cidr": "192.168.100.0/24",
            "name": None,
            "description": None,
            "tags": {},
            "parent": None,
            "children": [],
            "created_at": "2020-01-01T00:00:00",
        }
    }
    Path(temp_file).write_text(json.dumps(data))
    storage = FileCIDRStorage(temp_file)
    blocks = await storage.list()
    assert len(blocks) == 1
    assert blocks[0].cidr == "192.168.100.0/24"
    assert blocks[0].name is None
    assert blocks[0].description is None


@pytest.mark.asyncio
async def test_malformed_datetime_in_json(temp_file):
    """Test JSON with malformed datetime"""
    data = {
        "192.168.200.0/24": {
            "cidr": "192.168.200.0/24",
            "name": "test",
            "description": "test",
            "tags": {},
            "parent": None,
            "children": [],
            "created_at": "not-a-datetime",
        }
    }
    Path(temp_file).write_text(json.dumps(data))
    storage = FileCIDRStorage(temp_file)
    blocks = await storage.list()
    # Should skip invalid blocks
    assert len(blocks) == 0
