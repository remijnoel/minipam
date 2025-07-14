# MiniPAM Authentication Configuration Examples

This document provides configuration examples for all authentication backends.

## Environment Variables

All authentication configuration is done via environment variables to ensure security.

### Core Authentication Settings

```bash
# Authentication backend selection (none, apikey, oidc)
MINIPAM_AUTH_BACKEND=none

# JWT token configuration
MINIPAM_JWT_SECRET=your-super-secret-jwt-key-here
MINIPAM_JWT_ALGORITHM=HS256
MINIPAM_JWT_ISSUER=minipam
MINIPAM_JWT_EXPIRY_HOURS=8

# Default user settings (when auth is disabled)
MINIPAM_DEFAULT_USERNAME=admin
MINIPAM_DEFAULT_ROLE=readwrite
```

## Backend Configurations

### 1. None Backend (Development)

Disables authentication completely. All requests are treated as authenticated with default permissions.

```bash
# Use none backend (or leave empty)
MINIPAM_AUTH_BACKEND=none

# Default user when auth is disabled
MINIPAM_DEFAULT_USERNAME=admin
MINIPAM_DEFAULT_ROLE=readwrite
```

### 2. API Key Backend

Authenticates using pre-configured API keys stored in environment variables.

```bash
# Use API key backend
MINIPAM_AUTH_BACKEND=apikey

# JWT configuration (required)
MINIPAM_JWT_SECRET=your-super-secret-jwt-key-here

# API key configuration: MINIPAM_API_KEY_<USERNAME>=<key>:<role>
MINIPAM_API_KEY_ALICE=sk-prod-alice-12345:readwrite
MINIPAM_API_KEY_BOB=sk-prod-bob-67890:readonly
MINIPAM_API_KEY_ADMIN=sk-prod-admin-99999:readwrite
MINIPAM_API_KEY_VIEWER=sk-view-only-11111:readonly
```

**API Key Format:**

- Username: Derived from the environment variable suffix (e.g., `ALICE` from `MINIPAM_API_KEY_ALICE`)
- Key: The secret API key string
- Role: Either `readonly` or `readwrite`

**Usage:**

```bash
# Get token using API key
curl -X POST http://localhost:8000/auth/login/apikey \
  -H "Content-Type: application/json" \
  -d '{"api_key": "sk-prod-alice-12345"}'

# Use token to access API
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/cidrs
```

### 3. OIDC Backend

Authenticates using OpenID Connect providers (Azure AD, Google, Okta, etc.).

```bash
# Use OIDC backend
MINIPAM_AUTH_BACKEND=oidc

# JWT configuration (required)
MINIPAM_JWT_SECRET=your-super-secret-jwt-key-here

# OIDC provider configuration
MINIPAM_OIDC_CLIENT_ID=your-oidc-client-id
MINIPAM_OIDC_CLIENT_SECRET=your-oidc-client-secret
MINIPAM_OIDC_ISSUER_URL=https://your-provider.com
MINIPAM_OIDC_REDIRECT_URI=http://localhost:8000/auth/callback/oidc
MINIPAM_OIDC_SCOPE=openid profile email

# Role mapping: OIDC group to MiniPAM role
MINIPAM_OIDC_ROLE_CLAIM=groups
MINIPAM_OIDC_ROLE_MAPPING=minipam-admins:readwrite,minipam-viewers:readonly
MINIPAM_OIDC_DEFAULT_ROLE=readonly
```

**OIDC Configuration Notes:**

- `ISSUER_URL`: Your OIDC provider's issuer URL (e.g., `https://login.microsoftonline.com/<tenant-id>/v2.0`)
- `ROLE_CLAIM`: JWT claim containing user groups/roles (default: `groups`)
- `ROLE_MAPPING`: Maps OIDC groups to MiniPAM roles (comma-separated `group:role` pairs)
- `DEFAULT_ROLE`: Fallback role if no groups match

**Usage:**

```bash
# Start OIDC login flow
curl http://localhost:8000/auth/login/oidc
# User is redirected to OIDC provider, then back to callback URL
```

## Role-Based Access Control

MiniPAM supports two roles:

- **readonly**: Can view CIDR blocks and configurations
- **readwrite**: Can view and modify CIDR blocks

### Permission Mapping

| Role | Read CIDRs | Create CIDRs | Update CIDRs | Delete CIDRs |
|------|------------|--------------|--------------|--------------|
| readonly | ✅ | ❌ | ❌ | ❌ |
| readwrite | ✅ | ✅ | ✅ | ✅ |

## Security Best Practices

### 1. JWT Secret Management

```bash
# Generate a strong JWT secret
openssl rand -base64 32

# Or use a UUID
uuidgen
```

### 2. API Key Management

```bash
# Generate secure API keys
openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
```

### 3. Environment Variable Security

- Use a `.env` file for local development (never commit to git)
- Use your platform's secret management for production:
  - Docker Secrets
  - Kubernetes Secrets
  - Azure Key Vault
  - AWS Secrets Manager
  - HashiCorp Vault

### 4. OIDC Security

- Always use HTTPS in production
- Validate redirect URIs in your OIDC provider
- Use state parameter for CSRF protection
- Consider using PKCE for additional security

## Example Configurations

### Development Environment

```bash
# .env.development
MINIPAM_AUTH_BACKEND=none
MINIPAM_DEFAULT_USERNAME=dev-user
MINIPAM_DEFAULT_ROLE=readwrite
```

### Staging Environment

```bash
# .env.staging
MINIPAM_AUTH_BACKEND=apikey
MINIPAM_JWT_SECRET=staging-jwt-secret-12345
MINIPAM_API_KEY_STAGING_ADMIN=sk-staging-admin-12345:readwrite
MINIPAM_API_KEY_STAGING_USER=sk-staging-user-67890:readonly
```

### Production Environment

```bash
# .env.production (loaded from secure secret store)
MINIPAM_AUTH_BACKEND=oidc
MINIPAM_JWT_SECRET=<from-secret-store>
MINIPAM_OIDC_CLIENT_ID=<from-secret-store>
MINIPAM_OIDC_CLIENT_SECRET=<from-secret-store>
MINIPAM_OIDC_ISSUER_URL=https://login.microsoftonline.com/<tenant>/v2.0
MINIPAM_OIDC_REDIRECT_URI=https://minipam.company.com/auth/callback/oidc
MINIPAM_OIDC_ROLE_MAPPING=minipam-admins:readwrite,minipam-users:readonly
```

## Testing Authentication

### 1. Check Authentication Status

```bash
curl http://localhost:8000/auth/config
```

### 2. Health Check

```bash
curl http://localhost:8000/auth/health
```

### 3. Test API Access

```bash
# Without authentication (should fail if auth is enabled)
curl http://localhost:8000/api/cidrs

# With authentication
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/cidrs
```

## Troubleshooting

### Common Issues

1. **"No authentication backend configured"**
   - Check `MINIPAM_AUTH_BACKEND` environment variable
   - Ensure backend-specific configuration is present

2. **"Invalid token"**
   - Check `MINIPAM_JWT_SECRET` is set correctly
   - Verify token hasn't expired (default: 8 hours)

3. **"Permission denied"**
   - Check user role mapping
   - Verify API endpoint requires correct permission level

4. **OIDC login fails**
   - Check `MINIPAM_OIDC_*` configuration
   - Verify redirect URI is registered with provider
   - Check issuer URL and discovery document

### Debug Mode

Enable debug logging to troubleshoot authentication issues:

```bash
MINIPAM_DEBUG=true
```

This will log detailed authentication flow information.
