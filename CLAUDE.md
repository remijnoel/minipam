# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MiniPAM is a minimalistic IPAM (IP Address Management) solution built with FastAPI and Vue.js. It manages CIDR blocks with features like validation rules, authentication, pluggable storage backends, and a modern web interface.

## Development Commands

### Starting the Development Environment

```bash
# Start both backend (port 8000) and frontend (port 3000) with hot reloading
./dev-server.sh

# Start with debug mode (verbose logging, detailed error traces)
./dev-server.sh --debug

# Start with custom configuration
./dev-server.sh --config config.yaml
```

### Building and Installing

```bash
# Install in development mode (enables CLI)
pip install -e .

# Install dependencies
pip install -r requirements.txt

# Build web UI for production
./build-ui.sh

# Clean build (for distribution)
make clean-build
```

### Testing

Make sure to run tests after making changes.

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/minipam --cov-report=html

# Run specific test categories
pytest tests/test_api.py -v
pytest tests/test_storage.py -v
pytest tests/test_ui_api_integration.py -v

# Run tests with markers
pytest -m "not slow"  # Skip slow tests
pytest -m integration  # Only integration tests
```

### Docker

```bash
# Quick start with Docker Compose
docker-compose up -d

# Build and run manually
docker build -t minipam .
docker run -p 8000:8000 -v minipam-data:/app/data minipam

# Test Docker setup
./scripts/test-docker.sh
```

## Architecture Overview

MiniPAM follows a modular, layered architecture with clear separation of concerns:

### System Architecture

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vue.js UI     │    │   REST API      │    │   Storage       │
│   (webui/)      │◄──►│   (api.py)      │◄──►│   (storage.py)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              ▲                        ▲
                              │                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Auth Middleware │    │ Rules Engine    │
                       │ (auth/)         │    │ (rules.py)      │
                       └─────────────────┘    └─────────────────┘
```

### Core Components

**FastAPI Backend** (`src/minipam/`):

- `main.py` - Application factory, middleware stack, and configuration loading
- `api.py` - REST API endpoints with OpenAPI documentation and validation
- `storage.py` - Pluggable storage abstraction (InMemory, File, extensible to DB)
- `models.py` - Pydantic models for request/response validation and serialization
- `config_loader.py` - Multi-source configuration system (YAML/JSON/env/CLI)
- `rules.py` - CIDR validation rules engine with custom rule support
- `auth/` - Modular authentication system with multiple backend support

**Vue.js Frontend** (`webui/`):

- Modern Vue 3 + Composition API + Tailwind CSS
- Component-based architecture in `src/components/`
- Centralized API client with auth integration (`src/api/client.js`)
- Built for production and served by FastAPI at `/ui`

### Storage Architecture

The application uses dependency injection for storage backends:

- **InMemoryStorage**: Fast, temporary storage (default)
- **FileStorage**: JSON file with atomic writes and file locking
- Storage factory in `storage.py:get_cidr_storage()` chooses backend based on config

### Authentication System


### Configuration System

Multi-layer configuration (highest priority last):

1. Configuration file defaults
2. Configuration file values (YAML/JSON)
3. Environment variables (`MINIPAM_*`)
4. Command line arguments

Generate example config: `python -m minipam.main --generate-config config.yaml`

### Validation Rules Engine

CIDR blocks are validated using a pluggable rules system:

- Default rules: no duplicates, smallest parent assignment
- Custom rules can be added by extending `CIDRValidationRule`
- Rules in `rules.py` and examples in `custom_rules.py`

## Key Files for Development

### Backend Entry Points

- **`src/minipam/main.py`**:
  - `create_app()` - FastAPI application factory with middleware setup
  - `main()` - CLI entry point with argument parsing and server startup
  - Configuration loading and validation

- **`src/minipam/api.py`**:
  - `get_storage()` - Storage dependency injection for endpoints
  - REST API routes with OpenAPI documentation
  - Request/response validation and error handling

- **`src/minipam/storage.py`**:
  - `get_cidr_storage()` - Storage backend factory based on configuration
  - Abstract `CIDRStorage` interface for pluggable backends
  - `FileCIDRStorage` and `InMemoryCIDRStorage` implementations

### Authentication System

Pluggable authentication with multiple backends:

- **none**: No authentication (development)
- **apikey**: API key-based authentication
- **oidc**: OpenID Connect integration
- Middleware in `auth/middleware.py` handles user context and permissions

Main components:

- **`src/minipam/auth/middleware.py`**:
  - `AuthMiddleware` - FastAPI middleware for request authentication
  - Path exemption logic for public endpoints
  - User context injection and token validation

- **`src/minipam/auth/dependencies.py`**:
  - `AuthManager` - Central authentication backend management
  - Lazy initialization and backend selection logic
  - `get_auth_manager()` - Global auth manager singleton

- **`src/minipam/auth/backends/`**:
  - `oidc.py` - OpenID Connect authentication implementation
  - `apikey.py` - API key-based authentication
  - `none.py` - No-auth backend for development

### Configuration and Deployment

- **`src/minipam/config_loader.py`**:
  - Multi-source configuration management (YAML/JSON/env/CLI)
  - `load_configuration()` - Main config loading function
  - Configuration validation and type checking

- **`pyproject.toml`**:
  - Python package metadata and dependencies
  - CLI entry point configuration (`minipam` command)
  - Build system configuration

- **`docker-compose.yml`**:
  - Complete development and production environment
  - Volume mounts for persistent data and configuration
  - Environment variable configuration

- **`dev-server.sh`**:
  - Development environment launcher with hot reloading
  - Backend and frontend concurrent startup
  - Debug mode activation

### Frontend Integration

- **`webui/src/api/client.js`**:
  - Centralized HTTP client with authentication
  - Automatic JWT token management
  - Request/response interceptors for error handling

- **`webui/src/components/`**:
  - Vue.js components for CIDR management UI
  - Reusable form components and data tables
  - Authentication-aware navigation

## Debug Mode

Enable comprehensive debugging with `./dev-server.sh --debug`:

- HTTP request/response logging
- Storage operation tracing  
- Enhanced error information with full tracebacks
- Vue.js dev tools integration
- Backend logs to `backend_debug.log`, frontend to `frontend_debug.log`

## Testing Strategy

Tests are organized by component:

All tests should reside in the `tests/` directory. So far, we have the following tests:

- `test_api.py` - FastAPI route testing
- `test_storage.py` - Storage backend testing  
- `test_models.py` - Pydantic model validation
- `test_rules.py` - Validation rules engine
- `test_ui_api_integration.py` - Frontend/backend integration
- `conftest.py` - Shared test fixtures

For future tests, follow these guidelines:

- Use `pytest` fixtures for setup/teardown
- Name unit tests with `test_unit_<feature or module>.py`
- Name integration tests with `test_integration_<feature or module>.py`

Integration tests should cover actual feature usage. For example, if you add a new API endpoint, create a test that:

- Sends valid and invalid requests
- Checks response status codes
- Validates response data structure
- Ensures proper error handling
- Those tests should rely on the actual server running with the docker-compose setup, not mocked responses

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
   - Build documentation MUST go in `docs/build/` directory

3. **Error Handling**:
   - NEVER use bare `except:` - always specify exception types
   - Log errors with appropriate log levels (ERROR, WARNING, INFO, DEBUG)
   - Return meaningful error messages to users via HTTP responses

### Testing Requirements

**MANDATORY testing practices:**

1. **Test Coverage**:
   - EVERY new function/method MUST have unit tests
   - EVERY new API endpoint MUST have integration tests
   - Run `pytest --cov=src/minipam` to ensure coverage doesn't decrease

2. **Test Structure**:
   - Unit tests: `test_unit_<module>.py`
   - Integration tests: `test_integration_<feature>.py`
   - Use pytest fixtures from `conftest.py` for setup/teardown

3. **Test Execution**:
   - Run tests after EVERY change: `pytest`
   - All tests MUST pass before considering work complete
   - Integration tests MUST use real server (docker-compose), not mocks

## Development Workflow (MANDATORY)

**Follow this exact workflow for ALL changes:**

### Phase 1: Planning (REQUIRED)

1. **Create specification document** in `docs/specs/<feature-name>.md`:
2. 
   ```markdown
   # Feature: <Name>
   ## Tasks
   - [ ] Task 1: Description
   - [ ] Task 2: Description
   ## Implementation Details
   ## Testing Strategy
   ```

3. **Break down change into small tasks** (max 2 hours each)
4. **Update specification** as you complete each task

### Phase 2: Test-First Development (REQUIRED)

1. **Write failing tests FIRST** before any implementation:
   - Create integration test in `tests/` that covers the complete feature
   - Test valid inputs, invalid inputs, and edge cases
   - For API endpoints: test all HTTP methods, status codes, response formats

2. **Verify tests fail** with current implementation

### Phase 3: Implementation (REQUIRED)

1. **Implement ONLY enough code** to make the current test pass
2. **Run unit tests after each small change**: `pytest tests/test_unit_*.py`
3. **Add unit tests** for internal functions as you create them
4. **NEVER move to next task** until current tests pass

### Phase 4: Integration (REQUIRED)

1. **Run full test suite**: `pytest`
2. **Run integration tests**: `pytest tests/test_integration_*.py`
3. **Test in Docker environment**: `docker-compose up -d && <test manually>`
4. **Update documentation** in `docs/` to reflect changes

### Phase 5: Completion Criteria (REQUIRED)

**Implementation is NOT complete until ALL of these are true:**

- [ ] All unit tests pass (`pytest tests/test_unit_*.py`)
- [ ] All integration tests pass (`pytest tests/test_integration_*.py`)
- [ ] Full test suite passes (`pytest`)
- [ ] Manual testing in Docker works correctly
- [ ] Specification document is updated with completion status
- [ ] Documentation is updated
- [ ] No PEP 8 violations (run linter if available)

## Critical Rules (NEVER VIOLATE)

**These rules are ABSOLUTE and must ALWAYS be followed:**

1. **Configuration Loading**:
   - ALWAYS use `config_loader.py` functions, NEVER direct environment variable access
   - NEVER hardcode configuration values in the code
   - Use `load_configuration()` before accessing any config values

2. **Authentication System**:
   - ALWAYS use `get_auth_manager()` for auth operations
   - NEVER create AuthManager instances directly
   - Path exemptions MUST be added to middleware for public endpoints

3. **Storage Operations**:
   - ALWAYS use dependency injection with `get_storage()` in API endpoints
   - NEVER import storage classes directly in API code
   - Use atomic operations for file storage (existing file locking)

4. **Testing**:
   - ALWAYS run tests before pushing code
   - NEVER commit code that breaks existing tests
   - ALWAYS test authentication flows end-to-end

5. **Documentation**:
   - UPDATE this CLAUDE.md file when changing architecture
   - CREATE specification documents for non-trivial changes
   - DOCUMENT breaking changes in `docs/`

## Emergency Procedures

**If you encounter these situations:**

- **Tests failing**: STOP all development, fix tests first
- **Configuration not loading**: Check `config_loader.py` and ensure proper initialization order
- **Auth redirects**: Check middleware path exemptions and auth manager initialization
- **Storage errors**: Verify storage backend configuration and file permissions

**When in doubt**: ASK for clarification rather than guessing implementation details.