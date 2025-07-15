# Configuration Management

## Objective
Provide Viper-style configuration management where environment variables
override configuration file values using dot-notation mapping.

---

## Background / Context
- Following Go Viper pattern for configuration precedence and mapping.
- Environment variables use `MINIPAM_` prefix with underscores for nesting.
- Configuration files support both YAML and JSON formats.

---

## Requirements

### Functional Requirements
- Configuration sources in precedence order:
  1. Environment variables (`MINIPAM_*`)
  2. Configuration file (YAML/JSON)
  3. Default values
- Dot-notation mapping: `MINIPAM_STORAGE_TYPE` overrides `storage.type`
- Nested configuration: `MINIPAM_AUTH_OIDC_CLIENT_ID` overrides `auth.oidc.client_id`
- Support for arrays via comma-separated values: `MINIPAM_TAGS=dev,prod`
- Configuration validation with clear error messages

### Configuration Schema
```yaml
# Example configuration file
server:
  host: "0.0.0.0"
  port: 8000
  debug: false

storage:
  type: "file"  # file, memory
  path: "./data"

auth:
  backend: "none"  # none, apikey, oidc
  apikey:
    keys: []
  oidc:
    issuer_url: ""
    client_id: ""
    client_secret: ""

ui:
  enabled: true
  path: "/ui"
```

### Environment Variable Examples
```bash
# Server configuration
MINIPAM_SERVER_HOST=127.0.0.1
MINIPAM_SERVER_PORT=9000
MINIPAM_SERVER_DEBUG=true

# Storage configuration  
MINIPAM_STORAGE_TYPE=file
MINIPAM_STORAGE_PATH=/app/data

# Authentication configuration
MINIPAM_AUTH_BACKEND=oidc
MINIPAM_AUTH_OIDC_ISSUER_URL=https://auth.example.com
MINIPAM_AUTH_OIDC_CLIENT_ID=minipam-client
MINIPAM_AUTH_OIDC_CLIENT_SECRET=secret-from-vault
```

### Non-Functional Requirements
- Configuration loading must complete in < 100ms
- Clear validation errors with specific field paths
- Support hot-reload for non-critical settings (debug level, etc.)
- No secrets logged during configuration loading

### Out of Scope
- Configuration encryption at rest
- Dynamic configuration updates via API

---

## Inputs & Outputs
- **Input:** Config file path, environment variables
- **Output:** Validated configuration object with resolved values

---

## Dependencies / Constraints
- Use Python's built-in `os.environ` for environment variable access
- YAML parsing via `PyYAML` or similar
- JSON parsing via standard library `json`

---

## Edge Cases / Gotchas
- Boolean environment variables: `true/false`, `1/0`, `yes/no` all supported
- Empty environment variables override config file (not ignored)
- Invalid YAML/JSON files should fail fast with clear error message
- Missing config file is acceptable (use defaults + env vars)

---

## Testing & Acceptance Criteria
- Test all precedence combinations (env > file > default)
- Test nested configuration mapping
- Test boolean, string, integer, and array value types
- Test configuration validation with invalid values
- Test missing file scenarios

---

## Security / Privacy Notes
- Never log configuration values that might contain secrets
- Environment variables containing "SECRET", "PASSWORD", "KEY" should be masked in logs
- Configuration file permissions should be 600 or more restrictive

---

## Future Considerations / TODO
- Configuration watching for hot-reload
- Remote configuration sources (Consul, etcd)