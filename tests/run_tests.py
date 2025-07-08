#!/usr/bin/env python3
"""
Test runner for MiniPAM

This script provides a convenient way to run tests with proper pytest configuration.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Run MiniPAM tests")
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage reporting"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Run tests in verbose mode"
    )
    parser.add_argument(
        "--pattern",
        "-k",
        help="Run tests matching pattern"
    )
    parser.add_argument(
        "--core-only",
        action="store_true",
        help="Run only core tests (exclude API and integration tests that require server)"
    )
    parser.add_argument(
        "test_files",
        nargs="*",
        help="Specific test files to run"
    )
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Build pytest command
    cmd = [str(project_root / ".venv" / "bin" / "python"), "-m", "pytest"]
    
    # Add test files or default test patterns
    if args.test_files:
        cmd.extend(args.test_files)
    elif args.core_only:
        # Core tests that don't require a running server
        core_tests = [
            "tests/test_rules.py",
            "tests/test_models.py",
            "tests/test_storage.py",
            "tests/test_cli.py",
            "tests/test_file_storage_edge_cases.py",
            "tests/test_integration.py"
        ]
        cmd.extend(core_tests)
    else:
        cmd.append("tests/")
    
    # Add options
    if args.verbose:
        cmd.append("-v")
    
    if args.pattern:
        cmd.extend(["-k", args.pattern])
    
    if args.coverage:
        cmd.extend(["--cov=src/minipam", "--cov-report=html", "--cov-report=term"])
    
    # Run tests
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root)
    
    if args.coverage and result.returncode == 0:
        print("\nCoverage report generated in htmlcov/ directory")
    
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
