# MiniPAM

**Minimalistic IP Address Management** - A production-grade CIDR block management system with pluggable storage and authentication backends.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **API-First Design**: Complete REST API with OpenAPI documentation
- **Embedded Web UI**: Modern Vue.js interface served at `/ui`
- **Pluggable Backends**: Swappable storage (file/memory) and auth (none/API key/OIDC) backends
- **CIDR Hierarchy**: Validates parent-child relationships and prevents overlaps
- **Viper-Style Config**: Environment variables override config files with dot-notation mapping
- **Production Ready**: Atomic file operations, comprehensive validation, error handling

## Quick Start

### Installation

```bash
pip install minipam
```

### Initialize and Run

```bash
# Initialize configuration
minipam init

# Start the server
minipam serve

# Open web UI at http://localhost:8000/ui
```

### Using the CLI

```bash
# Add a CIDR block
minipam add-cidr 10.0.0.0/16 "Corporate Network" --tags "corp,main"

# List CIDR blocks
minipam list-cidrs

# Check server health
minipam health
```

### Using the API

```bash
# List all CIDRs
curl http://localhost:8000/api/v1/cidrs

# Get hierarchical tree view
curl http://localhost:8000/api/v1/cidrs/tree

# Create a new CIDR
curl -X POST http://localhost:8000/api/v1/cidrs \
     -H "Content-Type: application/json" \
     -d '{"cidr": "10.0.1.0/24", "name": "DMZ Network", "parent": "10.0.0.0/16", "tags": ["dmz"]}'
```

## Configuration

MiniPAM uses Viper-style configuration where environment variables override config file values:

### Basic Configuration

Create `config.yaml`:

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  debug: false

storage:
  type: "file"
  path: "./data"

auth:
  backend: "none"

ui:
  enabled: true
  path: "/ui"
```

### Environment Variable Overrides

```bash
# Override any config value using MINIPAM_ prefix
export MINIPAM_SERVER_PORT=9000
export MINIPAM_STORAGE_TYPE=memory
export MINIPAM_AUTH_BACKEND=apikey
export MINIPAM_AUTH_APIKEY_KEYS=key1,key2,key3
```

The mapping follows dot-notation: `MINIPAM_AUTH_OIDC_CLIENT_ID` overrides `auth.oidc.client_id`.

## Authentication Backends

### No Authentication (Development)

```yaml
auth:
  backend: "none"
```

Requires `ENABLE_NOAUTH=true` environment variable for safety.

### API Key Authentication

```yaml
auth:
  backend: "apikey"
  apikey:
    keys:
      - "your-secret-api-key"
```

Use with `Authorization: Bearer <key>` or `X-API-Key: <key>` headers.

### OIDC Authentication

```yaml
auth:
  backend: "oidc"
  oidc:
    issuer_url: "https://auth.example.com"
    client_id: "minipam-client"
    # Use env var: MINIPAM_AUTH_OIDC_CLIENT_SECRET=secret
```

Supports any OIDC provider (Azure AD, Auth0, Keycloak, etc.).

## Storage Backends

### File Storage (Production)

```yaml
storage:
  type: "file"
  path: "./data"
```

Uses atomic writes with file locking for concurrent access.

### Memory Storage (Development/Testing)

```yaml
storage:
  type: "memory"
```

Data is lost when the application stops.

## Web UI

The embedded Vue.js UI provides:

- **Dashboard**: Overview with statistics
- **Tree View**: Hierarchical CIDR visualization 
- **List View**: Tabular display with search/filter
- **CRUD Operations**: Create, edit, delete CIDR blocks
- **Real-time Validation**: Client-side and server-side validation

Access at `http://localhost:8000/ui` (configurable via `ui.path`).

## API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

### Core Endpoints

- `GET /api/v1/cidrs` - List CIDR blocks
- `GET /api/v1/cidrs/tree` - Hierarchical tree view
- `GET /api/v1/cidrs/{cidr}` - Get specific CIDR
- `POST /api/v1/cidrs` - Create CIDR block
- `PUT /api/v1/cidrs/{cidr}` - Update CIDR block
- `DELETE /api/v1/cidrs/{cidr}` - Delete CIDR block
- `GET /api/v1/health/live` - Liveness check
- `GET /api/v1/health/ready` - Readiness check

## CLI Reference

```bash
minipam [OPTIONS] COMMAND [ARGS]...

Commands:
  serve         Start the MiniPAM server
  init          Initialize configuration and data directory
  config-show   Show current configuration
  health        Check server health status
  list-cidrs    List CIDR blocks
  add-cidr      Add a new CIDR block
  delete-cidr   Delete a CIDR block

Options:
  -c, --config PATH  Configuration file path
  --debug           Enable debug mode
  --help            Show help message
```

## CIDR Validation Rules

MiniPAM enforces strict hierarchy rules:

1. **Uniqueness**: Each CIDR can only exist once
2. **Parent Containment**: Children must be subnets of their parent
3. **No Overlaps**: Sibling CIDRs cannot overlap
4. **IPv4 Only**: IPv6 support planned for future versions
5. **No /0 Networks**: Default routes are prohibited

Example hierarchy:
```
10.0.0.0/16 (Corporate Network)
├── 10.0.1.0/24 (DMZ)
├── 10.0.2.0/24 (Internal)
└── 10.0.10.0/24 (Guest)
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/remijnoel/minipam.git
cd minipam

python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/minipam --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
```

### Code Quality

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

## Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install .

EXPOSE 8000
CMD ["minipam", "serve"]
```

## Production Deployment

### Systemd Service

```ini
[Unit]
Description=MiniPAM IPAM Service
After=network.target

[Service]
Type=simple
User=minipam
WorkingDirectory=/opt/minipam
Environment=MINIPAM_STORAGE_PATH=/var/lib/minipam
ExecStart=/usr/local/bin/minipam serve -c /etc/minipam/config.yaml
Restart=always

[Install]
WantedBy=multi-user.target
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minipam
spec:
  replicas: 2
  selector:
    matchLabels:
      app: minipam
  template:
    metadata:
      labels:
        app: minipam
    spec:
      containers:
      - name: minipam
        image: minipam:latest
        ports:
        - containerPort: 8000
        env:
        - name: MINIPAM_STORAGE_PATH
          value: "/data"
        livenessProbe:
          httpGet:
            path: /api/v1/health/live
            port: 8000
        readinessProbe:
          httpGet:
            path: /api/v1/health/ready
            port: 8000
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: minipam-data
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [GitHub Wiki](https://github.com/remijnoel/minipam/wiki)
- **Issues**: [GitHub Issues](https://github.com/remijnoel/minipam/issues)
- **Discussions**: [GitHub Discussions](https://github.com/remijnoel/minipam/discussions)

## Roadmap

- [ ] IPv6 support
- [ ] Role-based access control (RBAC)
- [ ] Bulk import/export functionality
- [ ] Additional storage backends (PostgreSQL, MongoDB)
- [ ] WebSocket support for real-time updates
- [ ] Grafana dashboard integration
- [ ] IPAM allocation engine