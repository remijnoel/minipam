# VS Code Test Discovery Troubleshooting

This document helps troubleshoot test discovery issues in VS Code.

## Setup Verification

1. **Check Python Interpreter**:
   - Open VS Code Command Palette (Cmd+Shift+P)
   - Type "Python: Select Interpreter"
   - Select the virtual environment interpreter: `./venv/bin/python`

2. **Verify Virtual Environment**:

   ```bash
   # From project root
   .venv/bin/python --version
   .venv/bin/python -m pytest --version
   ```

3. **Test Discovery**:

   ```bash
   # Run from project root
   .venv/bin/python -m pytest --collect-only tests
   ```

## VS Code Settings

The project is configured with:

- `python.pythonPath`: Points to virtual environment
- `python.defaultInterpreterPath`: Points to virtual environment
- `python.testing.pytestEnabled`: Enabled
- `python.testing.pytestArgs`: Configured for tests directory

## Manual Test Discovery

If VS Code test discovery fails:

1. Use the Command Palette: "Python: Refresh Tests"
2. Or run tests manually: "Python: Run All Tests"
3. Or use the terminal: `.venv/bin/python -m pytest tests/`

## Common Issues

1. **"No module named pytest"**: VS Code is using system Python instead of virtual environment
   - Solution: Select correct interpreter via Command Palette

2. **Tests not discovered**:
   - Verify `tests/__init__.py` exists
   - Check that test files start with `test_`
   - Ensure virtual environment is activated

3. **Import errors in tests**:
   - Check `PYTHONPATH` includes `src` directory
   - Verify `python.analysis.extraPaths` is configured

## Running Tests

### From VS Code

- Use Test Explorer panel
- Click "Run All Tests" or individual test icons
- Use keyboard shortcuts (F5 for debug, Ctrl+F5 for run)

### From Terminal

```bash
# All tests
.venv/bin/python -m pytest tests/

# Specific test file
.venv/bin/python -m pytest tests/test_models.py

# Specific test
.venv/bin/python -m pytest tests/test_models.py::TestCIDRBlock::test_cidr_block_creation_minimal

# Verbose output
.venv/bin/python -m pytest tests/ -v
```

## Test Coverage

```bash
# Run tests with coverage
.venv/bin/python -m pytest tests/ --cov=src/minipam --cov-report=html
```
