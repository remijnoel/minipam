# MiniPAM - Minimalistic IPAM Solution

A FastAPI-based CIDR block management service with pluggable storage backends, modern Vue.js UI, and a comprehensive CLI interface.

## Features

- 🚀 **FastAPI-based REST API** - High-performance web API with automatic OpenAPI documentation
- 🌐 **Modern Vue.js UI** - Clean, responsive UI built with Vue 3 and Tailwind CSS
- 💾 **Pluggable Storage Backends** - Support for both in-memory and file-based storage
- 🛠️ **Validation Rules Engine** - Enforce CIDR hierarchy and prevent data inconsistency
- 🔒 **Thread-safe Operations** - Concurrent access protection with file locking
- 🛠️ **Comprehensive CLI** - Full command-line interface for all operations
- 🐞 **Advanced Debugging** - Detailed request/response logging and storage operation tracking
- ✅ **Full Test Coverage** - Comprehensive test suite with 48+ tests
- 📝 **Pydantic Models** - Strong data validation and serialization
- 🐍 **Modern Python** - Built with Python 3.9+ and modern dependencies

## Quick Start

### 🐳 Docker (Recommended)

Get MiniPAM running in seconds with Docker:

```bash
# Clone the repository
git clone <repository-url>
cd minipam

# Start with Docker Compose (includes persistent storage)
docker-compose up -d

# Or run directly with Docker
docker build -t minipam .
docker run -p 8000:8000 -v minipam-data:/app/data minipam
```

**That's it!** MiniPAM is now running at:

- **Web UI**: <http://localhost:8000/ui>
- **API**: <http://localhost:8000/api>
- **API Docs**: <http://localhost:8000/docs>
- **Health Check**: <http://localhost:8000/api/health>

### 🔧 Development Installation

```bash
# Clone the repository
git clone <repository-url>
cd minipam

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode (enables CLI)
pip install -e .
```

### Start the API Server

```bash
# Start the server (with web UI)
./dev-server.sh

# Enable debug mode for detailed logging
./dev-server.sh --debug

# Or using uvicorn directly
uvicorn minipam.main:app --reload
```

The API will be available at `http://localhost:8000/api` with automatic documentation at `http://localhost:8000/docs`.
The web UI will be available at `http://localhost:3000` in development mode.

### Using the CLI

```bash
# Check API health
minipam health

# Create a CIDR block
minipam create 192.168.1.0/24 --name "Development Network" --description "Dev environment"

# List all CIDR blocks
minipam list

# Get specific CIDR details
minipam get 192.168.1.0/24

# Update a CIDR block
minipam update 192.168.1.0/24 --description "Updated description"

# Delete a CIDR block
minipam delete 192.168.1.0/24 --force
```

## API Endpoints

- `GET /health` - Health check
- `GET /cidrs/` - List all CIDR blocks
- `POST /cidrs/` - Create a CIDR block
- `PUT /cidrs/{cidr}` - Update a specific CIDR block
- `GET /cidrs/{cidr}` - Get a specific CIDR block
- `DELETE /cidrs/{cidr}` - Delete a CIDR block

## Configuration

MiniPAM supports configuration through multiple methods:

### 1. Configuration Files (Recommended)

Create a configuration file in YAML or JSON format:

```bash
# Generate an example configuration file
python -m minipam.main --generate-config config.yaml

# Start with a configuration file
python -m minipam.main --config config.yaml

# Or use the dev server with config
./dev-server.sh --config config.yaml
```

#### Example YAML Configuration

```yaml
# Server configuration
server:
  host: "0.0.0.0"
  port: 8000
  log_level: "info"  # debug, info, warning, error, critical

# Storage configuration
storage:
  type: "file"  # "memory" or "file"
  
  # File storage configuration
  file:
    path: "cidrs.json"  # Path to the data file

# Debug mode
debug: false

# CORS configuration
cors:
  enabled: true
  origins:
    - "*"
    # For production, specify allowed origins:
    # - "https://yourdomain.com"

# Web UI configuration
ui:
  enabled: true
  path: "webui/dist"
```

#### Example JSON Configuration

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "log_level": "info"
  },
  "storage": {
    "type": "file",
    "file": {
      "path": "cidrs.json"
    }
  },
  "debug": false,
  "cors": {
    "enabled": true,
    "origins": ["*"]
  },
  "ui": {
    "enabled": true,
    "path": "webui/dist"
  }
}
```

### 2. Environment Variables

Environment variables override configuration file settings:

```bash
# Storage backend
export MINIPAM_STORAGE_TYPE=file           # "memory" or "file"
export MINIPAM_STORAGE_FILE_PATH=cidrs.json  # File path for storage

# Server configuration
export MINIPAM_SERVER_HOST=0.0.0.0         # Server host
export MINIPAM_SERVER_PORT=8000            # Server port
export MINIPAM_SERVER_LOG_LEVEL=info       # Log level

# Debug mode
export MINIPAM_DEBUG=true                  # Enable debug mode

# Legacy environment variables (still supported)
export USE_FILE_BACKEND=true               # Use file-based storage
export CIDR_FILE_PATH=cidrs.json          # File path for storage
export HOST=0.0.0.0                       # Server host
export PORT=8000                          # Server port
export LOG_LEVEL=info                     # Log level
```

### 3. Command Line Arguments

Command line arguments override both config files and environment variables:

```bash
# Start server with CLI overrides
python -m minipam.main --config config.yaml --host 127.0.0.1 --port 8080 --debug

# Generate example config file
python -m minipam.main --generate-config my-config.yaml
```

### Configuration Priority

Settings are applied in the following order (highest priority last):

1. Configuration file defaults
2. Configuration file values
3. Environment variables
4. Command line arguments

## CLI Usage

The CLI supports all CRUD operations on CIDR blocks:

### Global Options

- `--api-url TEXT` - API server URL (default: <http://localhost:8000>)
- `--format [table|json]` - Output format (default: table)

### Commands

- `health` - Check API server health
- `list` - List all CIDR blocks
- `get <cidr>` - Get details of specific CIDR block
- `create <cidr>` - Create new CIDR block with optional metadata
- `update <cidr>` - Update existing CIDR block
- `delete <cidr>` - Delete CIDR block

### Examples

```bash
# Create networks with metadata
minipam create 10.0.0.0/16 --name "Corporate Network" --tag env=production
minipam create 10.0.1.0/24 --parent 10.0.0.0/16 --tag zone=dmz

# JSON output for scripting
minipam --format json list | jq '.[] | select(.tags.env == "production")'

# Different API endpoint
minipam --api-url https://ipam.company.com list
```

## Web UI

MiniPAM now includes a modern web interface built with Vue 3 and Tailwind CSS:

- **CIDR Block Management** - Create, view, update and delete CIDR blocks
- **Parent/Child Relationships** - Create child CIDR blocks with parent relationship
- **Tagging System** - Add key-value tags to CIDR blocks
- **Responsive Design** - Works on desktop and mobile devices

### Web UI Development

```bash
# Start the development server (backend + frontend)
./dev-server.sh

# Build the web UI for production
./build-ui.sh
```

## Debug Mode

MiniPAM includes comprehensive debugging capabilities that can be enabled with:

```bash
# Start server with debug mode
./dev-server.sh --debug

# Or set environment variable
export MINIPAM_DEBUG=1
```

Debug mode provides:

- **HTTP Request/Response Logging** - Full details of all API calls
- **Storage Operation Tracing** - Track all database/storage operations
- **Enhanced Error Information** - Detailed error messages with context
- **CLI Debug Output** - Verbose logging for CLI operations
- **Application Startup Details** - Configuration and environment information

## Development

### Project Structure

```text
src/minipam/
├── __init__.py      # Package initialization
├── main.py          # FastAPI application
├── api.py           # API routes
├── models.py        # Pydantic models
├── storage.py       # Storage backends
├── config.py        # Configuration
├── debug.py         # Debugging utilities
└── cli.py           # Command-line interface

webui/
├── src/             # Vue.js source code
│   ├── api/         # API client
│   ├── components/  # Vue components
│   └── App.vue      # Root application component
└── public/          # Static assets

tests/
├── conftest.py      # Test fixtures
├── test_api.py      # API tests
├── test_models.py   # Model tests
├── test_storage.py  # Storage tests
├── test_ui_api_integration.py  # UI integration tests
└── test_integration_full.py    # Full integration tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/minipam --cov-report=html

# Run specific test categories
pytest tests/test_api.py -v
pytest tests/test_storage.py -v
pytest tests/test_ui_api_integration.py -v
```

### Storage Backends

#### In-Memory Storage (Default)

- Fast, lightweight
- Data is lost when application restarts
- Suitable for development and testing

#### File-Based Storage

- Persistent across restarts
- Thread-safe with file locking
- Suitable for production use in single-instance deployments

```bash
# Enable file backend
export USE_FILE_BACKEND=true
export CIDR_FILE_PATH=/data/cidrs.json
```

## Architecture

The application follows a modular architecture with clear separation of concerns:

- **Models** - Data validation and serialization using Pydantic
- **Storage** - Abstract storage interface with multiple implementations
- **API** - FastAPI routes with dependency injection
- **UI** - Vue.js frontend with Tailwind CSS
- **CLI** - Click-based command-line interface
- **Configuration** - Environment-based configuration management
- **Debug** - Comprehensive logging and debugging utilities

## CIDR Block Model

Each CIDR block supports the following fields:

```json
{
  "cidr": "192.168.1.0/24",           // Required: CIDR notation
  "name": "Development Network",       // Optional: Human-readable name
  "description": "Dev environment",    // Optional: Description
  "tags": {                           // Optional: Key-value tags
    "env": "development",
    "owner": "devops-team"
  },
  "parent": "192.168.0.0/16",        // Optional: Parent CIDR
  "created_at": "2025-07-06T04:52:51.141686"  // Auto-generated
}
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Documentation

- [Architecture Documentation](ARCHITECTURE.md)
- [Test Summary](TEST_SUMMARY.md)
- [CLI Documentation](CLI_README.md)
- [VS Code Testing Guide](VSCODE_TESTING.md)

## 📦 Files Added for Docker Support

The following files have been added to support Docker deployment:

- **`Dockerfile`** - Multi-stage build with Node.js frontend and Python backend
- **`docker-compose.yml`** - Complete Docker Compose setup with persistent storage
- **`docker-entrypoint.sh`** - Container startup script with health checks
- **`config.docker.yaml`** - Docker-optimized configuration
- **`test-docker.sh`** - Comprehensive Docker setup validation
- **`.dockerignore`** - Optimized Docker build exclusions
- **`DOCKER.md`** - Complete Docker deployment guide

## 🎯 Docker Quick Reference

```bash
# Quick start
docker-compose up -d

# Build and run manually
docker build -t minipam .
docker run -p 8000:8000 -v minipam-data:/app/data minipam

# Test setup
./test-docker.sh

# Check health
curl http://localhost:8000/api/health

# Access Web UI
open http://localhost:8000/ui

# Access API
curl http://localhost:8000/api/cidrs/
```

For detailed Docker deployment instructions, see [DOCKER.md](DOCKER.md).

## 🐳 Docker Deployment

### Quick Start with Docker Compose

The easiest way to deploy MiniPAM is using Docker Compose:

```bash
# Clone and start
git clone <repository-url>
cd minipam
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop
docker-compose down
```

### Manual Docker Build

```bash
# Build the image
docker build -t minipam .

# Run with persistent storage
docker run -d \
  --name minipam \
  -p 8000:8000 \
  -v minipam-data:/app/data \
  minipam

# Run with custom configuration
docker run -d \
  --name minipam \
  -p 8000:8000 \
  -v minipam-data:/app/data \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  minipam
```

### Docker Environment Variables

Configure MiniPAM using environment variables:

```bash
docker run -d \
  --name minipam \
  -p 8000:8000 \
  -v minipam-data:/app/data \
  -e MINIPAM_STORAGE_TYPE=file \
  -e MINIPAM_STORAGE_FILE_PATH=/app/data/cidrs.json \
  -e MINIPAM_SERVER_LOG_LEVEL=debug \
  -e MINIPAM_DEBUG=true \
  minipam
```

### Docker Compose with Custom Configuration

Create a custom `docker-compose.override.yml`:

```yaml
services:
  minipam:
    volumes:
      - ./my-config.yaml:/app/config.yaml:ro
    environment:
      - MINIPAM_DEBUG=true
    ports:
      - "8080:8000"  # Use different port
```

Then run:

```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

### Production Deployment

For production, use the provided `config.docker.yaml`:

```bash
# Copy and customize the Docker config
cp config.docker.yaml config.prod.yaml
# Edit config.prod.yaml with your settings

# Deploy
docker run -d \
  --name minipam-prod \
  -p 80:8000 \
  -v minipam-prod-data:/app/data \
  -v $(pwd)/config.prod.yaml:/app/config.yaml:ro \
  --restart unless-stopped \
  minipam
```

### Health Checks

The Docker image includes built-in health checks:

```bash
# Check container health
docker ps
docker inspect minipam | grep -A 10 "Health"

# Manual health check
docker exec minipam python -c "import requests; print(requests.get('http://localhost:8000/api/health').json())"
```

### Backup and Restore

When using file-based storage:

```bash
# Backup data
docker cp minipam:/app/data/cidrs.json backup-$(date +%Y%m%d).json

# Restore data
docker cp backup-20231201.json minipam:/app/data/cidrs.json
docker restart minipam
```

# Using the CLI

```bash
# Check API health
minipam health

# Create a CIDR block
minipam create 192.168.1.0/24 --name "Development Network" --description "Dev environment"

# List all CIDR blocks
minipam list

# Get specific CIDR details
minipam get 192.168.1.0/24

# Update a CIDR block
minipam update 192.168.1.0/24 --description "Updated description"

# Delete a CIDR block
minipam delete 192.168.1.0/24 --force
```

## API Endpoints

- `GET /health` - Health check
- `GET /cidrs/` - List all CIDR blocks
- `POST /cidrs/` - Create a CIDR block
- `PUT /cidrs/{cidr}` - Update a specific CIDR block
- `GET /cidrs/{cidr}` - Get a specific CIDR block
- `DELETE /cidrs/{cidr}` - Delete a CIDR block

## Configuration

MiniPAM supports configuration through multiple methods:

### 1. Configuration Files (Recommended)

Create a configuration file in YAML or JSON format:

```bash
# Generate an example configuration file
python -m minipam.main --generate-config config.yaml

# Start with a configuration file
python -m minipam.main --config config.yaml

# Or use the dev server with config
./dev-server.sh --config config.yaml
```

#### Example YAML Configuration

```yaml
# Server configuration
server:
  host: "0.0.0.0"
  port: 8000
  log_level: "info"  # debug, info, warning, error, critical

# Storage configuration
storage:
  type: "file"  # "memory" or "file"
  
  # File storage configuration
  file:
    path: "cidrs.json"  # Path to the data file

# Debug mode
debug: false

# CORS configuration
cors:
  enabled: true
  origins:
    - "*"
    # For production, specify allowed origins:
    # - "https://yourdomain.com"

# Web UI configuration
ui:
  enabled: true
  path: "webui/dist"
```

#### Example JSON Configuration

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "log_level": "info"
  },
  "storage": {
    "type": "file",
    "file": {
      "path": "cidrs.json"
    }
  },
  "debug": false,
  "cors": {
    "enabled": true,
    "origins": ["*"]
  },
  "ui": {
    "enabled": true,
    "path": "webui/dist"
  }
}
```

### 2. Environment Variables

Environment variables override configuration file settings:

```bash
# Storage backend
export MINIPAM_STORAGE_TYPE=file           # "memory" or "file"
export MINIPAM_STORAGE_FILE_PATH=cidrs.json  # File path for storage

# Server configuration
export MINIPAM_SERVER_HOST=0.0.0.0         # Server host
export MINIPAM_SERVER_PORT=8000            # Server port
export MINIPAM_SERVER_LOG_LEVEL=info       # Log level

# Debug mode
export MINIPAM_DEBUG=true                  # Enable debug mode

# Legacy environment variables (still supported)
export USE_FILE_BACKEND=true               # Use file-based storage
export CIDR_FILE_PATH=cidrs.json          # File path for storage
export HOST=0.0.0.0                       # Server host
export PORT=8000                          # Server port
export LOG_LEVEL=info                     # Log level
```

### 3. Command Line Arguments

Command line arguments override both config files and environment variables:

```bash
# Start server with CLI overrides
python -m minipam.main --config config.yaml --host 127.0.0.1 --port 8080 --debug

# Generate example config file
python -m minipam.main --generate-config my-config.yaml
```

### Configuration Priority

Settings are applied in the following order (highest priority last):

1. Configuration file defaults
2. Configuration file values
3. Environment variables
4. Command line arguments

## CLI Usage

The CLI supports all CRUD operations on CIDR blocks:

### Global Options

- `--api-url TEXT` - API server URL (default: <http://localhost:8000>)
- `--format [table|json]` - Output format (default: table)

### Commands

- `health` - Check API server health
- `list` - List all CIDR blocks
- `get <cidr>` - Get details of specific CIDR block
- `create <cidr>` - Create new CIDR block with optional metadata
- `update <cidr>` - Update existing CIDR block
- `delete <cidr>` - Delete CIDR block

### Examples

```bash
# Create networks with metadata
minipam create 10.0.0.0/16 --name "Corporate Network" --tag env=production
minipam create 10.0.1.0/24 --parent 10.0.0.0/16 --tag zone=dmz

# JSON output for scripting
minipam --format json list | jq '.[] | select(.tags.env == "production")'

# Different API endpoint
minipam --api-url https://ipam.company.com list
```

## Web UI

MiniPAM now includes a modern web interface built with Vue 3 and Tailwind CSS:

- **CIDR Block Management** - Create, view, update and delete CIDR blocks
- **Parent/Child Relationships** - Create child CIDR blocks with parent relationship
- **Tagging System** - Add key-value tags to CIDR blocks
- **Responsive Design** - Works on desktop and mobile devices

### Web UI Development

```bash
# Start the development server (backend + frontend)
./dev-server.sh

# Build the web UI for production
./build-ui.sh
```

## Debug Mode

MiniPAM includes comprehensive debugging capabilities that can be enabled with:

```bash
# Start server with debug mode
./dev-server.sh --debug

# Or set environment variable
export MINIPAM_DEBUG=1
```

Debug mode provides:

- **HTTP Request/Response Logging** - Full details of all API calls
- **Storage Operation Tracing** - Track all database/storage operations
- **Enhanced Error Information** - Detailed error messages with context
- **CLI Debug Output** - Verbose logging for CLI operations
- **Application Startup Details** - Configuration and environment information

## Development

### Project Structure

```text
src/minipam/
├── __init__.py      # Package initialization
├── main.py          # FastAPI application
├── api.py           # API routes
├── models.py        # Pydantic models
├── storage.py       # Storage backends
├── config.py        # Configuration
├── debug.py         # Debugging utilities
└── cli.py           # Command-line interface

webui/
├── src/             # Vue.js source code
│   ├── api/         # API client
│   ├── components/  # Vue components
│   └── App.vue      # Root application component
└── public/          # Static assets

tests/
├── conftest.py      # Test fixtures
├── test_api.py      # API tests
├── test_models.py   # Model tests
├── test_storage.py  # Storage tests
├── test_ui_api_integration.py  # UI integration tests
└── test_integration_full.py    # Full integration tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/minipam --cov-report=html

# Run specific test categories
pytest tests/test_api.py -v
pytest tests/test_storage.py -v
pytest tests/test_ui_api_integration.py -v
```

### Storage Backends

#### In-Memory Storage (Default)

- Fast, lightweight
- Data is lost when application restarts
- Suitable for development and testing

#### File-Based Storage

- Persistent across restarts
- Thread-safe with file locking
- Suitable for production use in single-instance deployments

```bash
# Enable file backend
export USE_FILE_BACKEND=true
export CIDR_FILE_PATH=/data/cidrs.json
```

## Architecture

The application follows a modular architecture with clear separation of concerns:

- **Models** - Data validation and serialization using Pydantic
- **Storage** - Abstract storage interface with multiple implementations
- **API** - FastAPI routes with dependency injection
- **UI** - Vue.js frontend with Tailwind CSS
- **CLI** - Click-based command-line interface
- **Configuration** - Environment-based configuration management
- **Debug** - Comprehensive logging and debugging utilities

## CIDR Block Model

Each CIDR block supports the following fields:

```json
{
  "cidr": "192.168.1.0/24",           // Required: CIDR notation
  "name": "Development Network",       // Optional: Human-readable name
  "description": "Dev environment",    // Optional: Description
  "tags": {                           // Optional: Key-value tags
    "env": "development",
    "owner": "devops-team"
  },
  "parent": "192.168.0.0/16",        // Optional: Parent CIDR
  "created_at": "2025-07-06T04:52:51.141686"  // Auto-generated
}
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Documentation

- [Architecture Documentation](ARCHITECTURE.md)
- [Test Summary](TEST_SUMMARY.md)
- [CLI Documentation](CLI_README.md)
- [VS Code Testing Guide](VSCODE_TESTING.md)

## 📦 Files Added for Docker Support

The following files have been added to support Docker deployment:

- **`Dockerfile`** - Multi-stage build with Node.js frontend and Python backend
- **`docker-compose.yml`** - Complete Docker Compose setup with persistent storage
- **`docker-entrypoint.sh`** - Container startup script with health checks
- **`config.docker.yaml`** - Docker-optimized configuration
- **`test-docker.sh`** - Comprehensive Docker setup validation
- **`.dockerignore`** - Optimized Docker build exclusions
- **`DOCKER.md`** - Complete Docker deployment guide

## 🎯 Docker Quick Reference

```bash
# Quick start
docker-compose up -d

# Build and run manually
docker build -t minipam .
docker run -p 8000:8000 -v minipam-data:/app/data minipam

# Test setup
./test-docker.sh

# Check health
curl http://localhost:8000/api/health

# Access Web UI
open http://localhost:8000/ui

# Access API
curl http://localhost:8000/api/cidrs/
```

For detailed Docker deployment instructions, see [DOCKER.md](DOCKER.md).

## 🐳 Docker Deployment

### Quick Start with Docker Compose

The easiest way to deploy MiniPAM is using Docker Compose:

```bash
# Clone and start
git clone <repository-url>
cd minipam
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop
docker-compose down
```

### Manual Docker Build

```bash
# Build the image
docker build -t minipam .

# Run with persistent storage
docker run -d \
  --name minipam \
  -p 8000:8000 \
  -v minipam-data:/app/data \
  minipam

# Run with custom configuration
docker run -d \
  --name minipam \
  -p 8000:8000 \
  -v minipam-data:/app/data \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  minipam
```

### Docker Environment Variables

Configure MiniPAM using environment variables:

```bash
docker run -d \
  --name minipam \
  -p 8000:8000 \
  -v minipam-data:/app/data \
  -e MINIPAM_STORAGE_TYPE=file \
  -e MINIPAM_STORAGE_FILE_PATH=/app/data/cidrs.json \
  -e MINIPAM_SERVER_LOG_LEVEL=debug \
  -e MINIPAM_DEBUG=true \
  minipam
```

### Docker Compose with Custom Configuration

Create a custom `docker-compose.override.yml`:

```yaml
services:
  minipam:
    volumes:
      - ./my-config.yaml:/app/config.yaml:ro
    environment:
      - MINIPAM_DEBUG=true
    ports:
      - "8080:8000"  # Use different port
```

Then run:

```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

### Production Deployment

For production, use the provided `config.docker.yaml`:

```bash
# Copy and customize the Docker config
cp config.docker.yaml config.prod.yaml
# Edit config.prod.yaml with your settings

# Deploy
docker run -d \
  --name minipam-prod \
  -p 80:8000 \
  -v minipam-prod-data:/app/data \
  -v $(pwd)/config.prod.yaml:/app/config.yaml:ro \
  --restart unless-stopped \
  minipam
```

### Health Checks

The Docker image includes built-in health checks:

```bash
# Check container health
docker ps
docker inspect minipam | grep -A 10 "Health"

# Manual health check
docker exec minipam python -c "import requests; print(requests.get('http://localhost:8000/api/health').json())"
```

### Backup and Restore

When using file-based storage:

```bash
# Backup data
docker cp minipam:/app/data/cidrs.json backup-$(date +%Y%m%d).json

# Restore data
docker cp backup-20231201.json minipam:/app/data/cidrs.json
docker restart minipam
```

## Validation Rules

MiniPAM includes a pluggable rule engine for validating CIDR operations. The following rules are enabled by default:

### Default Rules

1. **No Duplicate CIDRs** - Prevents adding CIDR blocks with the same CIDR notation twice
2. **Smallest Parent Rule** - Ensures CIDR blocks are assigned to the most specific parent
   - Example: If 10.0.0.0/8 exists (under 0.0.0.0/0) and 10.0.0.0/16 exists (under 10.0.0.0/8),
     then 10.0.0.0/24 must be assigned to 10.0.0.0/16, not to 10.0.0.0/8 or 0.0.0.0/0

### Extending the Rule Engine

You can create custom validation rules by extending the `CIDRValidationRule` base class:

```python
from minipam.rules import CIDRValidationRule, ValidationResult, rule_engine

class MyCustomRule(CIDRValidationRule):
    """Custom rule that validates [your criteria]"""
    
    @property
    def name(self) -> str:
        return "my_custom_rule"

    async def validate(self, block: CIDRBlock, storage: CIDRStorage) -> ValidationResult:
        # Your validation logic here
        if [condition]:
            return ValidationResult.failure("Error message explaining the validation failure")
        return ValidationResult.success()

# Register your rule with the engine
rule_engine.register_rule(MyCustomRule())
```

See `src/minipam/custom_rules.py` for examples of custom rules that can be created.

### Error Handling

When a validation rule fails, the API returns a 422 Unprocessable Entity response with a clear error message that can be displayed in the UI or CLI. This helps ensure data consistency and proper CIDR hierarchy.
