# Authentication System Feature Specification

**Document Version:** 1.1\
**Date:** July 13, 2025\
**Author:** Development Team\
**Status:** Updated Draft

---

## 1. Executive Summary

This specification defines the implementation of a modular authentication system for MiniPAM, enabling secure, configurable, and stateless user authentication while minimizing server footprint. Multiple authentication backends are supported with a unified JWT-based approach, and all secrets/API keys are sourced securely via environment variables by default.

---

## 2. Business Requirements

### 2.1 Primary Objectives

- **Modularity**: Pluggable authentication backends with zero code changes.
- **Enterprise Ready**: OIDC/SAML/corporate identity support.
- **Lightweight**: Auth system can be completely disabled with zero runtime overhead.
- **Developer Friendly**: Simple API token option for CLI/automation.
- **Security**: JWTs with strong signing, short expiry, secure config and secret management.

### 2.2 Success Criteria

-

---

## 3. Functional Requirements

### 3.1 Authentication Backends

#### 3.1.1 None (`none`)

- All requests are allowed.
- Returns default user with configurable role/permissions.
- No login UI shown.
- Zero runtime cost.

**Configuration:**

```yaml
auth:
  enabled: false
```

#### 3.1.2 API Key (`apikey`)

- Supports multiple keys with role/permission mapping.
- Keys are loaded from environment variables at startup (never hardcoded).
- Static config for admin and readonly roles.

**Configuration:**

```yaml
auth:
  enabled: true
  backend: apikey
  apikey:
    admin_key: ${ADMIN_API_KEY}
    readonly_key: ${READONLY_API_KEY}
```

- At startup, load `ADMIN_API_KEY` and `READONLY_API_KEY` from ENV. If missing, fail securely.

**Authentication Flow:**

1. Client sends `Authorization: Bearer <api-key>`
2. Backend validates against keys from ENV.
3. On success, issue JWT for subsequent use.

#### 3.1.3 OIDC (`oidc`)

- Integrates with OIDC identity providers (Azure, Google, Keycloak, etc).
- All OIDC secrets and client credentials loaded from ENV.
- Role/group mapping is configurable.
- Follows standard OAuth 2.0 flow.

**Configuration:**

```yaml
auth:
  enabled: true
  backend: oidc
  oidc:
    issuer: https://login.microsoftonline.com/tenant-id/v2.0
    client_id: ${OIDC_CLIENT_ID}
    client_secret: ${OIDC_CLIENT_SECRET}
    scopes: [openid, profile, email, groups]
  authorization:
    admin_groups: [minipam-admins, network-admins]
    readonly_groups: [minipam-users, network-team]
    default_role: readonly
```

- All `${...}` are loaded from environment variables at runtime.

---

### 3.2 Permission Model

- **readonly**: View-only access to IP/CIDR info.
- **readwrite**: Full CRUD on IP/CIDR blocks.
- Role mapping is configurable and loaded at startup.

---

### 3.3 JWT Token Management

- **Issued after successful login**
- **Payload** (example):

  ```json
  {
    "sub": "username",
    "email": "user@example.com",
    "roles": ["readonly"],
    "iat": 1642780800,
    "exp": 1642809600,
    "iss": "minipam"
  }
  ```

- **Validation**: On every API call.
- **Algorithm**: Default RS256 (asymmetric); fallback to HS256 if configured.
- **Secret/Private Key**: Always loaded from environment variables.
- **Expiration**: Default 8 hours; configurable.
- **No persistent storage** required for JWTs or sessions.
- **No refresh tokens** by default; clients must re-authenticate.

---

### 3.4 API Endpoints

#### Auth Endpoints

- `POST   /api/auth/login`
- `GET    /api/auth/config`
- `GET    /api/auth/me`
- `POST   /api/auth/logout`
- `GET    /auth/login` (OIDC browser redirect)
- `GET    /auth/callback` (OIDC callback)

#### Protected (example)

- `GET    /api/cidrs`      (readonly)
- `POST   /api/cidrs`      (readwrite)
- `PUT    /api/cidrs/{id}` (readwrite)
- `DELETE /api/cidrs/{id}` (readwrite)

---

## 4. Technical Requirements

### 4.1 Architecture

```
src/minipam/auth/
├── __init__.py
├── base.py              # Abstract base classes (use Python stdlib 'abc')
├── models.py            # Pydantic/BaseModel user/auth models
├── middleware.py        # FastAPI middleware (stdlib if possible)
├── dependencies.py      # FastAPI dependencies (avoid 3rd party unless necessary)
├── backends/
│   ├── __init__.py
│   ├── none.py
│   ├── apikey.py
│   └── oidc.py
└── utils.py             # JWT and crypto (prefer stdlib)
```

#### Backend Interface

```python
from abc import ABC, abstractmethod

class AuthBackend(ABC):
    @abstractmethod
    async def authenticate_credentials(self, request) -> "Optional[UserInfo]":
        """Authenticate credentials, return user info or None"""
        pass

    @abstractmethod
    async def get_login_url(self, redirect_uri: str) -> str:
        """Return browser login URL (if supported)"""
        pass

    @property
    @abstractmethod
    def supports_browser_flow(self) -> bool:
        pass
```

---

### 4.2 Security Requirements

- **All secrets/keys/credentials are loaded from environment variables only.**
- Never hardcode secrets or keys in code or config.
- Use strong JWT algorithms (RS256 preferred).
- Key rotation supported via ENV reload/redeploy.
- Validate all JWT claims (`iat`, `exp`, `iss`, `sub`).
- HTTPS enforced in production.
- Use secure cookie settings (if cookies are used): `HttpOnly`, `Secure`, `SameSite=Strict`.
- All authentication-related input is strictly validated (std lib, no unsafe parsing).
- Authentication endpoints rate-limited (use std lib tools or external reverse proxy).
- Comprehensive logging for failed auth attempts.

---

### 4.3 Configuration

- YAML config can reference `${ENV_VAR}`; load these at startup, error if missing.
- ENV takes precedence over config file values.
- All required secrets must be present in ENV or app startup fails securely.
- Only standard libraries for configuration and ENV handling (`os.environ`, `configparser`, `yaml` if needed).

---

## 5. User Experience

- **No Auth:** Loads instantly, no auth UI, all features enabled.
- **API Key:** Minimal login UI; API key never stored in browser cookies.
- **OIDC:** Redirects to identity provider, then returns to app.

**Error Handling:**

- Standard HTTP codes: `401` (unauthenticated), `403` (forbidden).
- Never leak sensitive info in error responses.
- Always log auth failures (username/IP/timestamp).

---

## 6. Non-Functional Requirements

- **Performance:** Auth check <5ms per request, JWT verification done in-memory.
- **Stateless:** No persistent server-side session or auth state.
- **Reliability:** Degrade gracefully if an auth backend is unavailable (OIDC, etc).
- **Maintainability:** Clear interfaces, well-documented, unit tests >90% coverage.
- **Security:** No hardcoded secrets, full environment separation.

---

## 7. Implementation Plan

(As per original, but explicitly: All secrets/API keys loaded from ENV, standard library usage only.)

---

## 8. Testing Strategy

- Mock ENV for all secrets/keys in tests.
- No test secrets in codebase—always via ENV.
- Security tests include missing/misconfigured ENV cases.

---

## 9. Deployment Considerations

- Docker: Use ENV for all keys/secrets, never bind-mount secrets.yaml or similar.
- Kubernetes: Mount secrets via `envFrom`/`Secret`, never as file.
- Reverse proxy: Forward `Authorization` headers; apply rate limits.

---

## 10. Migration Strategy

- Defaults to `auth.enabled: false` unless explicitly configured.
- ENV-first migration supported, with auto-detection of old config formats.

---

## 11. Risk Assessment

- **Secret compromise:** Rotate via ENV update/redeploy.
- **Token replay:** Use short JWT expiry.
- **ENV leakage:** Never log secrets/ENV values.

---

## 12. Success Metrics

- All auth backends work with secrets from ENV only.
- No regressions in auth flow or security with ENV-first config.
- All config/secrets validated at startup—never “fail open”.

---

## Appendix: Configuration Examples

### API Key Auth (ENV-first)

```yaml
auth:
  enabled: true
  backend: apikey
  apikey:
    admin_key: ${ADMIN_API_KEY}
    readonly_key: ${READONLY_API_KEY}
jwt:
  secret: ${JWT_SECRET}
  expiry: 8h
```

**.env example:**

```
ADMIN_API_KEY=verystrongadminkey
READONLY_API_KEY=readonlyaccesskey
JWT_SECRET=superlongrandomsecret
```

### OIDC Auth (ENV-first)

```yaml
auth:
  enabled: true
  backend: oidc
  oidc:
    issuer: https://login.microsoftonline.com/tenant-id/v2.0
    client_id: ${OIDC_CLIENT_ID}
    client_secret: ${OIDC_CLIENT_SECRET}
    scopes: [openid, profile, email, groups]
jwt:
  secret: ${JWT_SECRET}
  expiry: 8h
```

**.env example:**

```
OIDC_CLIENT_ID=myclientid
OIDC_CLIENT_SECRET=supersecret
JWT_SECRET=anotherlongrandomsecret
```

---

## API Reference

### Auth Request

```json
// POST /api/auth/login (API Key)
{ "api_key": "string" }

// POST /api/auth/login (OIDC)
{ "code": "string", "state": "string" }

// Response
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 28800,
  "user": { "username": "string", "email": "string", "roles": ["string"] }
}
```

### Error

```json
{
  "error": "string",
  "error_description": "string",
  "error_code": "string"
}
```

---

**End of Spec**
