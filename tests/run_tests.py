#!/usr/bin/env python3
"""
Test runner for minipam project

This script runs tests with proper Python path setup when pytest is not available.
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import test functions
from tests.test_integration import test_basic_functionality


async def main():
    """Run basic integration tests"""
    print("Running minipam integration tests...")
    print("=" * 50)

    try:
        await test_basic_functionality()
        print("✅ All integration tests passed!")
        return True
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
