# MiniPAM Testing Guide

This document describes the testing strategy and procedures for MiniPAM.

## Testing Philosophy

MiniPAM follows **Test-Driven Development (TDD)** as mandated by CLAUDE.md:

1. **Write tests first** - Tests are written before implementation
2. **Test at multiple levels** - Unit, integration, and end-to-end tests
3. **Comprehensive coverage** - Every function must have tests
4. **Fail fast** - Tests must fail initially to prove they work

## Test Structure

### Test Categories

Tests are organized into categories using pytest markers:

- `@pytest.mark.unit` - Unit tests for individual functions/classes
- `@pytest.mark.integration` - Integration tests for complete workflows
- `@pytest.mark.slow` - Tests that take longer to run

### Test Files

```
tests/
├── conftest.py                 # Pytest configuration and fixtures
├── run_tests.py               # Test runner script
├── test_models.py             # Data model tests
├── test_config.py             # Configuration tests
├── test_validation_engine.py  # Validation engine tests
├── test_storage_backends.py   # Storage backend tests
├── test_auth_backends.py      # Authentication backend tests
├── test_api_routes.py         # API endpoint tests
├── test_integration.py        # End-to-end integration tests
└── test_cli.py               # CLI interface tests
```

## Running Tests

### Test Runner Script

Use the provided test runner for comprehensive testing:

```bash
# Run all tests with coverage
python tests/run_tests.py --verbose --coverage

# Run specific test categories
python tests/run_tests.py --unit
python tests/run_tests.py --integration
python tests/run_tests.py --core-only

# Run with verbose output
python tests/run_tests.py --verbose
```

### Direct Pytest Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/minipam --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_models.py -v

# Run specific test function
pytest tests/test_models.py::TestCIDRBlock::test_valid_cidr_creation -v

# Run tests matching pattern
pytest -k "test_auth" -v

# Run tests by marker
pytest -m unit -v
pytest -m integration -v
pytest -m "not slow" -v
```

### Test Configuration

Tests can be configured via environment variables:

```bash
# Skip integration tests
export SKIP_INTEGRATION_TESTS=true

# Use specific test database
export TEST_STORAGE_PATH=/tmp/test_data

# Enable debug logging in tests
export TEST_DEBUG=true
```

## Test Types

### Unit Tests

Unit tests verify individual functions and classes in isolation.

**Characteristics:**
- Fast execution (< 1 second each)
- No external dependencies
- Use mocks for external services
- Test single responsibility

**Example:**
```python
def test_cidr_validation_success():
    """Test CIDR validation with valid input."""
    engine = CIDRValidationEngine()
    
    # Mock storage
    mock_storage = Mock()
    mock_storage.get.return_value = None
    mock_storage.list.return_value = []
    
    block = CIDRBlock(cidr="10.0.0.0/24", name="Test")
    result = engine.validate(block, mock_storage)
    
    assert result.is_valid
    assert len(result.errors) == 0
```

### Integration Tests

Integration tests verify complete workflows and component interactions.

**Characteristics:**
- Test real HTTP requests/responses
- Use FastAPI TestClient
- Test complete user scenarios
- May involve multiple components

**Example:**
```python
def test_create_cidr_workflow():
    """Test complete CIDR creation workflow."""
    app = create_app()
    client = TestClient(app)
    
    # Create CIDR via API
    response = client.post("/api/v1/cidrs", json={
        "cidr": "10.0.0.0/24",
        "name": "Test Network"
    })
    
    assert response.status_code == 201
    assert response.json()["cidr"] == "10.0.0.0/24"
    
    # Verify in list
    list_response = client.get("/api/v1/cidrs")
    assert len(list_response.json()) == 1
```

### End-to-End Tests

End-to-end tests verify complete user scenarios across the entire system.

**Characteristics:**
- Test real server instances
- Include UI interactions (when applicable)
- Test authentication flows
- Test data persistence

## Test Data and Fixtures

### Common Fixtures

Defined in `conftest.py`:

```python
@pytest.fixture
def sample_cidrs():
    """Sample CIDR blocks for testing."""
    return [
        CIDRBlock(cidr="10.0.0.0/16", name="Corporate", tags=["corp"]),
        CIDRBlock(cidr="10.0.1.0/24", name="DMZ", parent="10.0.0.0/16", tags=["dmz"]),
    ]

@pytest.fixture
def temp_storage_dir():
    """Temporary directory for file storage tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def memory_storage():
    """Clean memory storage instance."""
    return MemoryStorage()
```

### Test Data Guidelines

- Use realistic but non-sensitive data
- Create isolated test data for each test
- Clean up test data after tests complete
- Use factories for complex test data

## Mocking Strategy

### When to Mock

- External HTTP requests
- File system operations (in unit tests)
- Database connections
- Time-dependent operations
- Random number generation

### Mock Examples

```python
# Mock external HTTP request
@patch('src.minipam.auth.oidc.urlopen')
def test_oidc_jwks_fetch(mock_urlopen):
    mock_response = Mock()
    mock_response.read.return_value = json.dumps({"keys": []})
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    # Test code here

# Mock file operations
@patch('pathlib.Path.exists')
@patch('pathlib.Path.read_text')
def test_config_file_loading(mock_read, mock_exists):
    mock_exists.return_value = True
    mock_read.return_value = "server:\n  port: 8080"
    
    # Test code here
```

## Test Coverage

### Coverage Requirements

- **Minimum coverage:** 90% for all code
- **Unit test coverage:** 95% for business logic
- **Integration test coverage:** 100% for API endpoints

### Generating Coverage Reports

```bash
# HTML coverage report
pytest --cov=src/minipam --cov-report=html

# Terminal coverage report
pytest --cov=src/minipam --cov-report=term

# XML coverage report (for CI)
pytest --cov=src/minipam --cov-report=xml
```

### Coverage Analysis

```bash
# View HTML report
open htmlcov/index.html

# Missing coverage
coverage report --show-missing

# Coverage by file
coverage report --sort=cover
```

## Performance Testing

### Load Testing

```bash
# Install testing tools
pip install locust

# Run load test
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

### Memory Testing

```bash
# Memory profiling
pip install memory-profiler

# Profile memory usage
mprof run python -m minipam.main
mprof plot
```

## Testing Best Practices

### Test Organization

1. **One test per behavior** - Each test should verify one specific behavior
2. **Descriptive names** - Test names should describe what they test
3. **Arrange, Act, Assert** - Clear structure for test logic
4. **Independent tests** - Tests should not depend on each other

### Test Data

1. **Minimal data** - Use only the data needed for the test
2. **Realistic data** - Test data should represent real scenarios
3. **Edge cases** - Test boundary conditions and error cases
4. **Clean up** - Remove test data after tests complete

### Assertions

1. **Specific assertions** - Assert exact values, not just truthiness
2. **Multiple assertions** - Verify all relevant aspects
3. **Error messages** - Provide clear failure messages
4. **Exception testing** - Test that exceptions are raised correctly

## Continuous Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        pip install -e .
    
    - name: Run tests
      run: |
        python tests/run_tests.py --verbose --coverage
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
  
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

## Debugging Tests

### Debug Mode

```bash
# Run tests with debug output
pytest --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb

# Debug specific test
pytest tests/test_models.py::test_function --pdb

# Run with print statements
pytest -s tests/test_models.py
```

### Test Debugging Tips

1. **Use print statements** - Add debug prints to understand test flow
2. **Check test data** - Verify test data is set up correctly
3. **Isolate failing tests** - Run only the failing test
4. **Check fixtures** - Ensure fixtures are working as expected
5. **Review mocks** - Verify mocks are configured correctly

## Test Documentation

### Test Docstrings

```python
def test_cidr_validation_duplicate_fails():
    """
    Test that CIDR validation fails for duplicate CIDR blocks.
    
    This test verifies that the validation engine correctly identifies
    when a CIDR block already exists in storage and returns appropriate
    error messages.
    """
    # Test implementation
```

### Test Comments

```python
def test_complex_workflow():
    """Test complex multi-step workflow."""
    # Step 1: Set up initial state
    setup_data()
    
    # Step 2: Perform action
    result = perform_action()
    
    # Step 3: Verify outcome
    assert result.is_valid
    assert len(result.errors) == 0
```

## Troubleshooting

### Common Issues

1. **Import errors** - Check PYTHONPATH and package installation
2. **Fixture errors** - Verify fixture scope and dependencies
3. **Mock errors** - Check mock configuration and patches
4. **Async errors** - Use pytest-asyncio for async tests
5. **Database errors** - Ensure test database is clean

### Test Isolation

```python
# Reset global state
@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset global state before each test."""
    reset_configuration()
    reset_dependencies()
    yield
    reset_configuration()
    reset_dependencies()
```

This comprehensive testing strategy ensures that MiniPAM is thoroughly tested at all levels, following the requirements specified in CLAUDE.md.