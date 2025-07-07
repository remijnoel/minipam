#!/usr/bin/env bash

# Script to help VS Code find the correct Python interpreter
# This can be used if VS Code is having trouble with interpreter selection

echo "Available Python interpreters:"
echo "System Python: $(which python3)"
echo "Virtual Environment Python: $(pwd)/.venv/bin/python"
echo ""
echo "Virtual Environment Python version:"
.venv/bin/python --version
echo ""
echo "Pytest availability:"
.venv/bin/python -m pytest --version
echo ""
echo "Test discovery:"
.venv/bin/python -m pytest --collect-only tests -q
