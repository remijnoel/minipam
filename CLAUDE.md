# MiniPAM Coding Instructions

This file provides guidance to coding agents on how to work with the MiniPAM project - a minimalistic IPAM (IP Address Management) solution.

## Development Commands

### Starting the Development Environment

```bash
# Activate virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install package in development mode
pip install -e .

# Start development server
python -m minipam.main --config config.yaml.example
# OR use the dev script
./dev-server.sh
```

### Building and Installing

```bash
# Build the package
make build

# Install from wheel
make install-build

# OR install in development mode
make install-dev
```

### Running the Application using Docker

```bash
# Build and run with Docker Compose (recommended)
docker-compose up -d

# Build Docker image manually
docker build -t minipam .

# Run with Docker (persistent storage)
docker run -p 8000:8000 -v minipam-data:/app/data minipam

# Run with Azure OIDC authentication
docker-compose -f docker-compose.azure.yml up -d
```

### Building the Web UI

```bash
# Build the UI assets from remote repository
./scripts/build-ui.sh

# OR build from local development directory
LOCAL_UI_DIR=../ipam-visual-nexus ./scripts/build-ui-local.sh
```

The Web UI is built from a separate repository (https://github.com/remijnoel/ipam-visual-nexus) and packaged into the MiniPAM distribution:
- Built UI assets are placed in `src/minipam/ui/dist/`
- UI is served at the root path `/` by default
- Build scripts automatically pull, build, and package the latest UI

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/minipam --cov-report=html --cov-report=term

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests

# Run tests using the test runner
python tests/run_tests.py --verbose --coverage

# Run core tests only (no server required)
python tests/run_tests.py --core-only
```

## Architecture Overview

**MiniPAM** is a FastAPI-based CIDR block management service with:

- **Backend**: FastAPI REST API with async support
- **Frontend**: React frontend (in another repository)
- **Storage**: Pluggable backends (memory, file-based with atomic writes)
- **Authentication**: Multiple backends (none, API keys, Azure OIDC)
- **CLI**: Click-based command-line interface
- **Configuration**: YAML/JSON with environment variable overrides

Refer to the documentation in `docs/` for detailed architecture information.

## Development Standards

### Code Quality Requirements

**ALWAYS follow these coding standards:**

1. **Python Code Style**:
   - Follow PEP 8 formatting (use `black` formatter if available)
   - Use type hints for ALL function signatures: `def func(param: str) -> bool:`
   - Import statements MUST be at top of files (exceptions only in test files)
   - Docstrings required for public functions using Google style format

2. **File Organization**:
   - Test files MUST go in `tests/` directory only
   - Standalone scripts MUST go in `scripts/` directory only
   - Documentation files MUST go in `docs/` directory only
   - DO NOT create test files, scripts or documentation at the root level

3. **Error Handling**:
   - NEVER use bare `except:` - always specify exception types
   - Log errors with appropriate log levels (ERROR, WARNING, INFO, DEBUG)
   - Return meaningful error messages to users via HTTP responses
  
4. **Logging**:
   - Use Python's built-in `logging` module
   - Log at appropriate levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   - Log messages should be clear and informative
   - Use lazy evaluation for log messages (e.g., `logger.debug("Value: %d", value)`)
   - Setup logging configuration in a single place and allow it to be overridden by environment variables

5. **Virtual Environments**:
   - Use `.venv` for all development (already configured)
   - Activate virtual environment and install dependencies from `requirements.txt` before running any commands

6. **Configuration**:
   - Use `src/minipam/config_loader.py` for all configuration management
   - Support both YAML and JSON configuration files
   - ALWAYS support environment variable overrides using `MINIPAM_*` prefix
   - Test configuration changes with both file and environment variable inputs

### Testing Requirements

**MANDATORY testing practices:**

1. **Test Coverage**:
   - EVERY new function/method MUST have unit tests
   - EVERY new feature MUST have integration tests
   - Run `pytest --cov=src/minipam` to ensure coverage doesn't decrease
   - Current test files: `test_api.py`, `test_auth.py`, `test_cli.py`, `test_config.py`, `test_models.py`, `test_rules.py`, `test_storage.py`, `test_integration.py`

2. **Test Structure**:
   - Unit tests: Test individual functions/classes in isolation
   - Integration tests: Test complete workflows including OIDC authentication
   - Use pytest fixtures from `conftest.py` for setup/teardown
   - Use `reset_configuration()` in tests that modify configuration state

3. **Test Execution**:
   - Run tests after EVERY change: `pytest`
   - All tests MUST pass before considering work complete
   - Integration tests MUST use real server, not mocks
   - OIDC tests require actual Azure configuration or proper mocking

4. **Authentication Testing**:
   - Test all auth backends: `none`, `apikey`, `oidc`
   - Test environment variable configuration: `MINIPAM_AUTH_BACKEND`, `MINIPAM_OIDC_*`
   - Test configuration loading order and precedence
   - Test JWT token generation and validation

## Development Workflow (MANDATORY)

**Follow this exact workflow for ALL changes:**

### Phase 1: Planning (REQUIRED)

- **Create specification document** in `docs/specs/<feature-name>.md` based on the template available in `docs/specs/specs_template.md`
- **Break down change into small tasks**
- **Update specification** as you complete each task
- **Ask all the questions** you need to fill out the spec
- **Do NOT start coding** until the spec is complete and approved

### Phase 2: Test-First Development (REQUIRED)

- **Write failing tests FIRST** before any implementation:
  - Create integration test in `tests/` that covers the complete feature
  - Test valid inputs, invalid inputs, and edge cases
  - For API endpoints: test all HTTP methods, status codes, response formats
  - For authentication: test all backends and configuration scenarios
- **Verify tests fail** with current implementation

### Phase 3: Implementation (REQUIRED)

- **Implement ONLY enough code** to make the current test pass
- **Run unit tests after each small change**: `pytest tests/test_*.py`
- **Add unit tests** for internal functions as you create them
- **NEVER move to next task** until current tests pass

### Phase 4: Integration (REQUIRED)

1. **Run full test suite**: `pytest`
2. **Run integration tests**: `pytest -m integration`
3. **Test Docker builds**: `docker build -t minipam-test .`
4. **Test authentication flows** (if applicable)
5. **Update documentation** in `docs/` to reflect changes

### Phase 5: Completion Criteria (REQUIRED)

**Implementation is NOT complete until ALL of these are true:**

- [ ] All unit tests pass (`pytest tests/test_*.py`)
- [ ] All integration tests pass (`pytest -m integration`)
- [ ] Full test suite passes (`pytest`)
- [ ] Configuration system works with both files and environment variables
- [ ] Docker build succeeds (`docker build -t minipam .`)
- [ ] Specification document is updated with completion status
- [ ] Documentation is updated
- [ ] No PEP 8 violations (run linter if available)

## Authentication Development Notes

**Special considerations for authentication features:**

- **Configuration Priority**: Environment variables > Config file > Defaults
- **Auth Backends**: Located in `src/minipam/auth/backends/`
- **Dependencies**: Authentication logic in `src/minipam/auth/dependencies.py`
- **Middleware**: Authentication middleware in `src/minipam/auth/middleware.py`
- **OIDC Flow**: Complete implementation with state validation and JWT tokens
- **Testing**: Use `reset_configuration()` before each test to avoid state pollution

## Critical Rules (NEVER VIOLATE)

**These rules are ABSOLUTE and must ALWAYS be followed:**

- **NEVER commit code that does not pass ALL tests** - this includes unit and integration tests
- **NEVER skip writing tests** - every new feature MUST have tests
- **NEVER modify existing tests** to make them pass - always fix the implementation
- **NEVER break configuration loading order** - environment variables must override config files
- **NEVER hardcode secrets** - always use environment variables or configuration files

**When in doubt**: ASK for clarification rather than guessing implementation details.

## Project-Specific Notes

- **Vue.js UI**: Built from remote repository and packaged in `src/minipam/ui/dist/`
- **Docker**: Multi-stage build with development and production configurations
- **CLI**: Available as `minipam` command after installation
- **Storage**: File-based storage uses atomic writes with file locking
- **Debugging**: Enable with `MINIPAM_DEBUG=true` or `debug: true` in config
- **CORS**: Enabled by default for development, configurable for production