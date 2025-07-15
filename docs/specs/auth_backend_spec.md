# Authentication Backend Plugin Interface

## Objective
Provide a pluggable auth layer so deployments can choose anything from
“NoAuth (dev)” to OIDC, Cognito, or SAML, all via a uniform interface.

---

## Background / Context
- POC supports NoAuth & hard-coded API key.
- Production will need enterprise SSO.

---

## Requirements

### Functional Requirements
- Abstract class `AuthBackend` with methods:  
  - `authenticate(request:AuthRequest) -> UserInfo`  
  - `refresh(token:str) -> UserInfo` *(optional)*  
  - `revoke(token:str) -> None` *(optional)*  
- Must set `UserInfo.roles` although RBAC enforcement is out of scope.
- Configurable via dict (issuer URL, JWKS, client_id…).

### Non-Functional Requirements
- Latency budget: ≤ 100 ms added per request.  
- Must cache public keys/JWKS for ≥ 10 min.  
- Library choice must support FIPS 140-2 compliant crypto if host OS requires.

### Out of Scope
- MFA flows.  
- Fine-grained permission mapping.

---

## Inputs & Outputs
- **Input:** `AuthRequest` (headers, cookies, query params).  
- **Output:** `UserInfo {id, username, roles, scopes}`.

---

## Dependencies / Constraints
- JWT libraries must support RS256 & ES256.  
- No root-level secret exposure in debug logs.

---

## Edge Cases / Gotchas
- Expired tokens → 401, *never* 500.  
- Clock-skew handling ± 120 s for `exp`/`nbf`.

---

## Testing & Acceptance Criteria
- Positive & negative token samples for each backend.  
- Static analysis: no high CVE in crypto deps.

---

## Security / Privacy Notes
- Default backend: NoAuth (DEV ONLY) guarded by `ENABLE_NOAUTH=false`.

---

## Future Considerations / TODO
- Pluggable authorization (RBAC/ABAC) layer atop UserInfo.
