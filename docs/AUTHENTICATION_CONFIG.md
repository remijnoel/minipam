# MiniPAM Authentication Configuration Guide

This guide explains how to configure MiniPAM's modular authentication system using configuration files.

## Overview

MiniPAM now uses a unified approach with separate configuration files for different authentication methods:

- **`config.apikey.yaml`** - API key authentication
- **`config.azure.yaml`** - Azure Entra ID (OIDC) authentication

You can select which configuration to use via the `MINIPAM_CONFIG_FILE` environment variable.

## Quick Start

### 1. API Key Authentication (Default)

```bash
# Start with API key authentication (default)
docker-compose up -d

# Or explicitly specify the config
MINIPAM_CONFIG_FILE=/app/config.apikey.yaml docker-compose up -d
```

### 2. Azure Entra ID Authentication

```bash
# Start with Azure authentication
MINIPAM_CONFIG_FILE=/app/config.azure.yaml docker-compose up -d

# Or create a .env file
echo "MINIPAM_CONFIG_FILE=/app/config.azure.yaml" > .env
docker-compose up -d
```

## Configuration Files

### API Key Configuration (`config.apikey.yaml`)

```yaml
# Authentication configuration
auth:
  backend: "apikey"
  jwt:
    secret: "your-super-secret-jwt-key-change-in-production"
    algorithm: "HS256"
    expiry_hours: 8
  
  # API key configuration
  api_keys:
    admin: "sk-minipam-admin-12345:readwrite"
    viewer: "sk-minipam-viewer-67890:readonly"
    service: "sk-minipam-service-99999:readwrite"
```

### Azure Entra ID Configuration (`config.azure.yaml`)

```yaml
# Authentication configuration
auth:
  backend: "oidc"
  jwt:
    secret: "your-super-secret-jwt-key-change-in-production"
    algorithm: "HS256"
    expiry_hours: 8
  
  # Azure Entra ID OIDC configuration
  oidc:
    client_id: "your-azure-app-client-id-here"
    client_secret: "your-azure-app-client-secret-here"
    issuer_url: "https://login.microsoftonline.com/your-tenant-id-here/v2.0"
    redirect_uri: "http://localhost:8000/auth/callback/oidc"
    scope: "openid profile email"
    role_claim: "groups"
    role_mapping: "minipam-admins:readwrite,minipam-users:readonly"
    default_role: "readonly"
```

## Environment Variable Overrides

Configuration files can be overridden with environment variables for production deployments:

### API Key Overrides

```bash
# Override JWT secret
MINIPAM_JWT_SECRET=your-production-secret

# Override API keys
MINIPAM_API_KEY_ADMIN=sk-admin-prod-xyz:readwrite
MINIPAM_API_KEY_VIEWER=sk-viewer-prod-abc:readonly
```

### Azure Entra ID Overrides

```bash
# Override Azure credentials
MINIPAM_OIDC_CLIENT_ID=your-client-id
MINIPAM_OIDC_CLIENT_SECRET=your-client-secret
MINIPAM_OIDC_ISSUER_URL=https://login.microsoftonline.com/your-tenant/v2.0
```

## Environment File Examples

### API Key Authentication (`.env.apikey.example`)

```bash
MINIPAM_CONFIG_FILE=/app/config.apikey.yaml
MINIPAM_JWT_SECRET=your-production-jwt-secret
MINIPAM_API_KEY_ADMIN=sk-admin-prod-xyz:readwrite
MINIPAM_API_KEY_VIEWER=sk-viewer-prod-abc:readonly
```

### Azure Authentication (`.env.azure.example`)

```bash
MINIPAM_CONFIG_FILE=/app/config.azure.yaml
MINIPAM_JWT_SECRET=your-production-jwt-secret
MINIPAM_OIDC_CLIENT_ID=12345678-1234-1234-1234-123456789abc
MINIPAM_OIDC_CLIENT_SECRET=your~client~secret
MINIPAM_OIDC_ISSUER_URL=https://login.microsoftonline.com/your-tenant/v2.0
```

## CLI Usage

The CLI also supports the config file option:

```bash
# Start server with specific config
python -m minipam.cli run --config config.apikey.yaml

# Or use environment variable
export MINIPAM_CONFIG_FILE=config.azure.yaml
python -m minipam.cli run
```

## Development Server

The development server script also supports config files:

```bash
# Start with API key config
./dev-server.sh --config config.apikey.yaml

# Start with Azure config
./dev-server.sh --config config.azure.yaml
```

## Authentication Testing

### API Key Authentication

```bash
# Login with API key
curl -X POST "http://localhost:8000/auth/login/apikey?api_key=sk-minipam-admin-12345"

# Use the returned JWT token
TOKEN="your-jwt-token-here"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/cidrs
```

### Azure Entra ID Authentication

```bash
# Check auth config
curl http://localhost:8000/auth/config

# Start OIDC login (will redirect to Microsoft)
curl http://localhost:8000/auth/login/oidc

# Complete login in browser, then use returned JWT token
TOKEN="your-jwt-token-here"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/cidrs
```

## Switching Between Authentication Methods

### Runtime Switching

You can switch authentication methods without rebuilding containers:

```bash
# Switch to Azure authentication
echo "MINIPAM_CONFIG_FILE=/app/config.azure.yaml" > .env
docker-compose restart

# Switch back to API key authentication
echo "MINIPAM_CONFIG_FILE=/app/config.apikey.yaml" > .env
docker-compose restart
```

### Production Deployment

For production, create a `.env` file with your chosen configuration:

```bash
# For API key authentication
cp .env.apikey.example .env
# Edit .env with your production values

# For Azure authentication  
cp .env.azure.example .env
# Edit .env with your Azure tenant details
```

## Security Notes

1. **Change default secrets**: Always change JWT secrets and API keys in production
2. **Use strong API keys**: Generate cryptographically strong API keys
3. **Secure environment files**: Protect `.env` files with proper file permissions
4. **Azure app registration**: Follow least-privilege principles for Azure app permissions
5. **Network security**: Use HTTPS in production and restrict network access

## Troubleshooting

### Enable Debug Mode

```bash
# Add to your .env file
MINIPAM_DEBUG=true

# Or set environment variable
export MINIPAM_DEBUG=true
docker-compose restart
```

### Check Configuration

```bash
# Verify current auth configuration
curl http://localhost:8000/auth/config

# Check health status
curl http://localhost:8000/api/health
```

### View Logs

```bash
# View container logs
docker-compose logs -f minipam

# View authentication-specific logs in debug mode
docker-compose logs -f minipam | grep -i auth
```
