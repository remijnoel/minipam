# Tests Directory

This directory contains all tests for the minipam project, organized according to Python testing best practices.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Pytest configuration and shared fixtures
├── test_rules.py            # Unit tests for CIDR validation rules
├── test_models.py           # Unit tests for data models
├── test_storage.py          # Unit tests for storage backends
├── test_api.py              # Integration tests for API endpoints
├── test_config.py           # Unit tests for configuration
├── test_cli.py              # Unit tests for CLI commands
├── test_file_storage_edge_cases.py  # Edge case tests for file storage
├── test_ui_api_integration.py       # UI/API integration tests
├── test_integration.py      # Full integration tests
├── run_tests.py             # Enhanced test runner with multiple options
└── README.md               # This file
```

## Running Tests

### Quick Start

```bash
# Run all core tests (recommended for development)
python tests/run_tests.py --core-only --verbose

# Run specific test files
python tests/run_tests.py tests/test_rules.py tests/test_models.py

# Run tests with coverage
python tests/run_tests.py --core-only --coverage

# Run tests matching a pattern
python tests/run_tests.py --pattern "test_rules"
```

### Using pytest directly

```bash
# From project root with virtual environment activated
.venv/bin/python -m pytest tests/ -v

# Run specific test categories
.venv/bin/python -m pytest tests/test_rules.py -v
.venv/bin/python -m pytest tests/test_models.py tests/test_storage.py -v

# Run with coverage
.venv/bin/python -m pytest tests/ --cov=src/minipam --cov-report=html
```

## Test Categories

### Unit Tests

- **test_models.py**: Tests for `CIDRBlock` Pydantic model
- **test_storage.py**: Tests for storage backends (`InMemoryCIDRStorage`, `FileCIDRStorage`)
- **test_config.py**: Tests for configuration module

### Integration Tests

- **test_api.py**: Tests for FastAPI endpoints and HTTP API
- **test_integration.py**: End-to-end tests verifying all components work together

## Legacy Test Runner

### Using pytest (Alternative Method)

If you prefer to use pytest directly, first install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run all tests:

```bash
pytest
```

Run specific test categories:

```bash
# Unit tests only
pytest tests/test_models.py tests/test_storage.py tests/test_config.py

# Integration tests only
pytest tests/test_api.py tests/test_integration.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=minipam --cov-report=html
```

### Using the Simple Test Runner

If pytest is not available, you can use the simple test runner:

```bash
python tests/run_tests.py
```

Or run integration tests directly:

```bash
python tests/test_integration.py
```

## Test Configuration

The `conftest.py` file provides shared fixtures and configuration:

- **sample_cidr_block**: A sample CIDR block for testing
- **another_cidr_block**: Another sample CIDR block for testing
- **memory_storage**: In-memory storage fixture
- **file_storage**: File storage fixture with automatic cleanup
- **temp_file_path**: Temporary file path fixture

## Test Data

Tests use realistic but safe test data:

- **IPv4 CIDR blocks**: `192.168.1.0/24`, `10.0.0.0/8`, `172.16.0.0/12`
- **Test networks**: Named consistently as "Test Network", "Corporate Network", etc.
- **Test tags**: Environment-specific tags like `{"environment": "test"}`

## Test Coverage

The test suite covers:

✅ **Model Validation**: Pydantic model creation, validation, and serialization  
✅ **Storage Operations**: CRUD operations for both storage backends  
✅ **File Safety**: Concurrent access, atomic writes, and error handling  
✅ **API Endpoints**: All HTTP endpoints with various scenarios  
✅ **Configuration**: Environment variable handling  
✅ **Integration**: End-to-end workflow testing  
✅ **Error Handling**: Edge cases and error conditions  

## Writing New Tests

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Using Fixtures

```python
import pytest

class TestYourFeature:
    @pytest.mark.asyncio
    async def test_your_feature(self, memory_storage, sample_cidr_block):
        # Use the fixtures
        await memory_storage.put(sample_cidr_block)
        retrieved = await memory_storage.get(sample_cidr_block.cidr)
        assert retrieved is not None
```

### Testing Async Code

Use `@pytest.mark.asyncio` decorator for async tests:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Testing API Endpoints

```python
def test_api_endpoint(client):
    response = client.get("/cidrs/")
    assert response.status_code == 200
    assert response.json() == []
```

## Best Practices

1. **Isolation**: Each test should be independent and not depend on others
2. **Cleanup**: Use fixtures for automatic cleanup of resources
3. **Descriptive Names**: Test names should clearly describe what they test
4. **Edge Cases**: Test both happy path and error conditions
5. **Realistic Data**: Use data that resembles real-world usage
6. **Fast Tests**: Keep tests fast by using in-memory storage when possible

## Continuous Integration

The test suite is designed to run in CI/CD environments:

- No external dependencies required
- Automatic cleanup of temporary files
- Clear pass/fail indicators
- Detailed error reporting

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root directory
2. **Missing Dependencies**: Run `pip install -r requirements-dev.txt`
3. **Path Issues**: The test runner automatically sets up Python paths
4. **File Permissions**: Ensure tests have permission to create temporary files

### Debug Mode

Run tests with more verbose output:

```bash
pytest -v -s
```

Or use the debug flag:

```bash
pytest --pdb
```
