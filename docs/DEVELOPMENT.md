# MiniPAM Development Guide

This document provides detailed instructions for setting up and developing MiniPAM according to the CLAUDE.md workflow.

## Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose (for containerized development)
- Git

## Development Workflow

MiniPAM follows a strict Test-Driven Development (TDD) workflow as defined in CLAUDE.md:

### Phase 1: Planning (REQUIRED)
- Create specification document in `docs/specs/` using the template
- Break down changes into small tasks
- Update specification as you complete each task

### Phase 2: Test-First Development (REQUIRED)
- **Write failing tests FIRST** before any implementation
- Create integration tests in `tests/` that cover the complete feature
- Verify tests fail with current implementation

### Phase 3: Implementation (REQUIRED)
- Implement ONLY enough code to make current tests pass
- Run tests after each small change
- Add unit tests for internal functions as you create them

### Phase 4: Integration (REQUIRED)
- Run full test suite: `python tests/run_tests.py`
- Run integration tests: `python tests/run_tests.py --integration`
- Test Docker builds: `./scripts/test-docker.sh`
- Update documentation in `docs/` to reflect changes

### Phase 5: Completion Criteria (REQUIRED)
Implementation is NOT complete until ALL of these are true:
- [ ] All unit tests pass
- [ ] All integration tests pass  
- [ ] Full test suite passes
- [ ] Docker build succeeds
- [ ] Documentation is updated
- [ ] No linting violations

## Environment Setup

### 1. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install package in development mode
pip install -e .
```

### 2. Verify Setup

```bash
# Check Python environment
./check_python_setup.sh

# Verify minipam command works
minipam --help
```

## Running Tests

### Test Runner Script

Use the provided test runner script:

```bash
# Run all tests with coverage
python tests/run_tests.py --verbose --coverage

# Run only unit tests
python tests/run_tests.py --unit

# Run only integration tests
python tests/run_tests.py --integration

# Run core tests only (no server required)
python tests/run_tests.py --core-only
```

### Individual Test Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/minipam --cov-report=html --cov-report=term

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Run specific test file
pytest tests/test_models.py -v
```

## Code Quality

### Linting and Formatting

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/minipam
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Docker Development

### Building Images

```bash
# Build production image
docker build -t minipam .

# Build development image
docker build -t minipam-dev . --target development

# Test Docker builds
./scripts/test-docker.sh
```

### Running with Docker Compose

```bash
# Start with default configuration
docker-compose up -d

# Start with Azure OIDC
docker-compose -f docker-compose.azure.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Development Server

### Quick Start

```bash
# Start development server
./dev-server.sh
```

This will:
- Activate virtual environment
- Install dependencies if needed
- Set development environment variables
- Start server in debug mode

### Manual Start

```bash
# Set environment variables
export ENABLE_NOAUTH=true
export MINIPAM_AUTH_BACKEND=none
export MINIPAM_STORAGE_TYPE=memory
export MINIPAM_SERVER_DEBUG=true

# Start server
minipam serve
```

## Configuration

### Environment Variables

All configuration can be overridden with environment variables using the `MINIPAM_` prefix:

```bash
# Server configuration
export MINIPAM_SERVER_HOST=127.0.0.1
export MINIPAM_SERVER_PORT=9000
export MINIPAM_SERVER_DEBUG=true

# Storage configuration
export MINIPAM_STORAGE_TYPE=file
export MINIPAM_STORAGE_PATH=/app/data

# Authentication configuration
export MINIPAM_AUTH_BACKEND=apikey
export MINIPAM_AUTH_APIKEY_KEYS=key1,key2,key3
```

### Configuration Files

```bash
# Initialize default configuration
minipam init

# Use custom configuration
minipam serve --config custom-config.yaml
```

## Testing Strategy

### Unit Tests

- Test individual functions/classes in isolation
- Use mocks for external dependencies
- Located in `tests/test_*.py`
- Marked with `@pytest.mark.unit`

### Integration Tests

- Test complete workflows end-to-end
- Use real FastAPI TestClient
- Test actual HTTP requests/responses
- Located in `tests/test_integration.py`
- Marked with `@pytest.mark.integration`

### Test Data

- Use fixtures for common test data
- Create temporary directories for file storage tests
- Reset configuration state between tests

## Project Structure

```
minipam/
├── src/minipam/           # Source code
│   ├── models/            # Data models
│   ├── config/            # Configuration management
│   ├── storage/           # Storage backends
│   ├── auth/              # Authentication backends
│   ├── validation/        # CIDR validation engine
│   ├── api/               # FastAPI routes and middleware
│   ├── ui/                # Embedded web UI
│   ├── main.py            # Application entry point
│   └── cli.py             # Command-line interface
├── tests/                 # Test suite
│   ├── conftest.py        # Pytest configuration
│   ├── run_tests.py       # Test runner script
│   └── test_*.py          # Test files
├── docs/                  # Documentation
│   ├── specs/             # Technical specifications
│   └── *.md               # Documentation files
├── scripts/               # Development scripts
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── pyproject.toml         # Package configuration
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
└── README.md              # Main documentation
```

## Common Issues

### Import Errors

If you encounter import errors, ensure:
- Virtual environment is activated
- Package is installed in development mode: `pip install -e .`
- Python path includes src directory

### Test Failures

If tests fail:
- Check that all dependencies are installed
- Verify configuration is reset between tests
- Check that test data is properly cleaned up

### Docker Issues

If Docker builds fail:
- Ensure Docker daemon is running
- Check that requirements.txt is up to date
- Verify file permissions for scripts

## Contributing

1. Follow the CLAUDE.md workflow exactly
2. Write tests first, then implementation
3. Ensure all tests pass before submitting
4. Update documentation for any changes
5. Run full test suite and Docker builds

## AWS Fargate Development

### Quick Start Commands

For AWS Fargate deployment during development:

```bash
# First time setup
make first-deploy

# Get your API URL
make status

# Quick redeploy with latest code
make redeploy

# View logs
make logs

# Run tests against deployed service
make test

# Destroy the deployment
make destroy
```

### Available Makefile Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make deploy` | Full deployment (first time) |
| `make redeploy` | Quick redeploy with latest code |
| `make status` | Show deployment status and URLs |
| `make logs` | Show recent application logs |
| `make test` | Run tests against deployed service |
| `make local` | Run locally with Docker |
| `make clean` | Clean up local Docker images |
| `make destroy` | Destroy the deployment |

### Cost Optimization

Development environment costs approximately:
- **Fargate**: ~$10-15/month (1 task, 0.25 vCPU, 0.5 GB)
- **ALB**: ~$20/month
- **Total**: ~$30-35/month

To minimize costs:
- Use `make destroy` when not actively developing
- The stack can be redeployed quickly with `make deploy`

### Frontend Integration Example

Update your frontend to use the deployed API:

```javascript
// Get your API URL from 'make status'
const API_BASE_URL = 'http://minipam-dev-alb-123456789.us-east-1.elb.amazonaws.com/api/v1';

// Test connection
fetch(`${API_BASE_URL}/health/ready`)
  .then(response => response.json())
  .then(data => console.log('Backend healthy:', data));

// Get CIDR tree
fetch(`${API_BASE_URL}/cidrs/tree`)
  .then(response => response.json())
  .then(data => console.log('CIDR tree:', data));
```

## Resources

- [CLAUDE.md](../CLAUDE.md) - Development workflow requirements
- [Technical Specifications](specs/) - Detailed requirements
- [API Documentation](http://localhost:8000/api/docs) - Interactive API docs
- [Test Coverage Report](htmlcov/index.html) - Generated after running tests with coverage