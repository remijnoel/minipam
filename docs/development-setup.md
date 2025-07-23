# Development Environment Setup

This document explains how to set up your local development environment for MiniPAM.

## Quick Start

1. **Initialize your local environment**:
   ```bash
   make init
   ```

2. **Edit your configuration**:
   ```bash
   # Edit Makefile.local with your settings
   nano Makefile.local
   ```

3. **Verify your configuration**:
   ```bash
   make config
   ```

## Configuration Files

### Makefile.local (Personal Configuration)

The `Makefile.local` file contains your personal development environment configuration. This file is:
- **Ignored by git** (in `.gitignore`)
- **Created from `Makefile.local.example`** when you run `make init`
- **Customizable** for your specific deployment environment

### Standard Open Source Pattern

This project follows the standard open source pattern for handling personal vs public configuration:

- **`Makefile.local.example`** - Template file committed to the repository
- **`Makefile.local`** - Personal file excluded from git (in `.gitignore`)
- **Main `Makefile`** - Includes the local config with `-include Makefile.local`

This pattern allows:
- ✅ **Developers** can have personal configurations without conflicts
- ✅ **Contributors** get working examples to start from
- ✅ **Maintainers** keep personal details out of the public repository
- ✅ **CI/CD** systems can provide their own configuration files

## Common Configuration Examples

### Local Development Only
```makefile
# Makefile.local
API_BASE_URL := http://localhost:8000/api/v1
```

### Docker Compose Development
```makefile
# Makefile.local
API_BASE_URL := http://localhost:8000/api/v1
DOCKER_COMPOSE_FILE := docker-compose.yml
```

### Custom Domain Development
```makefile
# Makefile.local
API_BASE_URL := https://minipam-dev.mydomain.com/api/v1
```

## Available Make Commands

Run `make help` to see all available commands. Key commands include:

- `make init` - Initialize local development environment
- `make config` - Show current configuration
- `make local` - Run locally with Docker
- `make build` - Build Docker image
- `make deploy` - Deploy to your configured environment
- `make test-api` - Test API connectivity
- `make populate` - Populate with sample data

## Deployment (Optional)

For deployment beyond local development:

1. **Update Makefile.local** with your deployment details:
   ```makefile
   API_BASE_URL := https://your-deployment-url/api/v1
   ```

2. **Deploy using your preferred method**:
   - Docker Compose: `docker-compose up -d`
   - Kubernetes: Apply your manifests
   - Cloud platforms: Use platform-specific deployment tools

## Troubleshooting

### "Makefile.local not found" warnings
Run `make init` to create the file from the example.

### Deployment commands fail
- Check your deployment environment configuration
- Verify necessary permissions and access
- Ensure target services/containers are properly configured

### API calls fail
- Check the `API_BASE_URL` in your `Makefile.local`
- Ensure the service is running: `make status`
- Test connectivity: `make test-api`

## Contributing

When contributing to this project:

1. **Never commit `Makefile.local`** - it's personal configuration
2. **Update `Makefile.local.example`** if you add new configuration options
3. **Document new configuration options** in this file
4. **Test with default configuration** to ensure it works for new contributors