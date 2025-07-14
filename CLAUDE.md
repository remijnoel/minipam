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

### Core Components

**FastAPI Backend** (`src/minipam/`):
- `main.py` - Application entry point with FastAPI setup, middleware, and configuration loading
- `api.py` - REST API routes with CRUD operations for CIDR blocks
- `storage.py` - Abstract storage interface with InMemory and File backends
- `models.py` - Pydantic models for data validation
- `config.py` & `config_loader.py` - Configuration management (YAML/JSON/env vars)
- `rules.py` - Validation rules engine for CIDR hierarchy enforcement
- `auth/` - Authentication system with pluggable backends (API key, OIDC, none)

**Vue.js Frontend** (`webui/`):
- Modern Vue 3 + Tailwind CSS interface
- Components in `src/components/` for CIDR management
- API client in `src/api/client.js`
- Built assets served by FastAPI at `/ui` endpoint

### Storage Architecture

The application uses dependency injection for storage backends:
- **InMemoryStorage**: Fast, temporary storage (default)
- **FileStorage**: JSON file with atomic writes and file locking
- Storage factory in `storage.py:get_cidr_storage()` chooses backend based on config

### Authentication System

Pluggable authentication with multiple backends:
- **none**: No authentication (development)
- **apikey**: API key-based authentication
- **oidc**: OpenID Connect integration
- Middleware in `auth/middleware.py` handles user context and permissions

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

- `src/minipam/main.py:create_app()` - Application factory and configuration
- `src/minipam/api.py:get_storage()` - Storage dependency injection 
- `src/minipam/storage.py:get_cidr_storage()` - Storage backend factory
- `src/minipam/auth/middleware.py` - Authentication middleware
- `pyproject.toml` - Python package configuration and CLI entry point
- `docker-compose.yml` - Complete development/production setup
- `dev-server.sh` - Development environment launcher

## Debug Mode

Enable comprehensive debugging with `./dev-server.sh --debug`:
- HTTP request/response logging
- Storage operation tracing  
- Enhanced error information with full tracebacks
- Vue.js dev tools integration
- Backend logs to `backend_debug.log`, frontend to `frontend_debug.log`

## Testing Strategy

Tests are organized by component:
- `test_api.py` - FastAPI route testing
- `test_storage.py` - Storage backend testing  
- `test_models.py` - Pydantic model validation
- `test_rules.py` - Validation rules engine
- `test_ui_api_integration.py` - Frontend/backend integration
- `conftest.py` - Shared test fixtures

## Development Standards

- Follow PEP 8 for Python code
- Use type hints for function signatures
- Import statements at top of files (except in tests)
- Document changes in changelog
- Write unit tests for new functionality
- Place build docs in `docs/build` directory (by build doc I mean specifications, results of tests, summary of features implementation)
- Test files in `tests/`, standalone scripts in `scripts/`