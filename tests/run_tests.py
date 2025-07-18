#!/usr/bin/env python3
"""Test runner script for MiniPAM as referenced in CLAUDE.md"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print(f"❌ FAILED: {description}")
        return False
    else:
        print(f"✅ PASSED: {description}")
        return True


def main():
    parser = argparse.ArgumentParser(description="Run MiniPAM tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--coverage", "-c", action="store_true", help="Run with coverage"
    )
    parser.add_argument(
        "--core-only",
        action="store_true",
        help="Run core tests only (no server required)",
    )
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument(
        "--integration", action="store_true", help="Run integration tests only"
    )

    args = parser.parse_args()

    # Change to project root
    project_root = Path(__file__).parent.parent
    subprocess.run(["cd", str(project_root)], shell=True)

    success = True

    # Base pytest command
    pytest_cmd = ["python", "-m", "pytest"]

    if args.verbose:
        pytest_cmd.append("-v")

    if args.coverage:
        pytest_cmd.extend(
            ["--cov=src/minipam", "--cov-report=html", "--cov-report=term"]
        )

    # Test selection
    if args.unit:
        pytest_cmd.extend(["-m", "unit"])
    elif args.integration:
        pytest_cmd.extend(["-m", "integration"])
    elif args.core_only:
        pytest_cmd.extend(["-m", "not slow"])

    # Add test directory
    pytest_cmd.append("tests/")

    # Run tests
    if not run_command(pytest_cmd, "Running pytest"):
        success = False

    # Run additional checks if not core-only
    if not args.core_only:
        # Type checking
        if not run_command(
            ["python", "-m", "mypy", "src/minipam"], "Type checking with mypy"
        ):
            success = False

        # Code formatting check
        if not run_command(
            ["python", "-m", "black", "--check", "src/", "tests/"],
            "Code formatting check",
        ):
            success = False

        # Import sorting check
        if not run_command(
            ["python", "-m", "isort", "--check-only", "src/", "tests/"],
            "Import sorting check",
        ):
            success = False

        # Linting
        if not run_command(
            ["python", "-m", "flake8", "src/", "tests/"], "Linting with flake8"
        ):
            success = False

    # Summary
    print(f"\n{'='*60}")
    if success:
        print("🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()
