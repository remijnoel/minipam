# Public REST API

## Objective
Provide a versioned HTTP/JSON API that exposes full CRUD and tree-view
operations for CIDR blocks, plus health and metadata endpoints.

---

## Background / Context
- POC uses FastAPI; spec is implementation-agnostic.
- Consumers: internal UI SPA, future CLI, third-party integrators.
- Must support seamless blue/green deployment (backward-compatible
  as long as `v1` is alive).

---

## Requirements

### Functional Requirements
- `GET  /api/v1/cidrs` — list (flat) with pagination & filtering.  
- `GET  /api/v1/cidrs/tree` — hierarchical view (nested JSON).  
- `GET  /api/v1/cidrs/{cidr}` — fetch single block.  
- `POST /api/v1/cidrs` — create block *(body: CIDRBlock)*.  
- `PUT  /api/v1/cidrs/{cidr}` — full update.  
- `DELETE /api/v1/cidrs/{cidr}` — delete.  
- `GET  /api/v1/health/live|ready` — k8s-style liveness / readiness.  
- All write endpoints **MUST** validate against CIDR hierarchy rules (see separate spec).

Acceptance examples (Gherkin-style):  
- *Given* no block exists, *when* POST `10.0.0.0/24`, *then* status 201 and body.id == `10.0.0.0/24`.  
- *Given* block `10.0.0.0/24` exists, *when* POST `10.0.0.0/16`, *then* status 409 (parent/child incoherence).

### Non-Functional Requirements
- JSON only, UTF-8.  
- Version via URL (`/v1/...`) not headers.  
- Max payload ≤ 1 MiB.  
- 99th-percentile latency < 200 ms for list endpoints at 1k CIDRs.  
- No sensitive info in logs.

### Out of Scope
- Bulk import/export (CSV, etc.)  
- GraphQL.

---

## Inputs & Outputs

**CIDRBlock (JSON)**
```json
{
  "cidr": "10.0.0.0/24",
  "name": "corp-lab-net",
  "parent": "10.0.0.0/16",
  "tags": ["lab", "vlan12"]
}
```

Errors follow RFC 7807 (`application/problem+json`).

---

## Dependencies / Constraints
- Relies on Auth middleware to inject `UserInfo`.  
- Storage backend abstracted via internal service layer.

---

## Edge Cases / Gotchas
- IPv6 support (e.g., `/48` blocks) must behave same as IPv4.  
- Concurrent create/delete on overlapping CIDRs → deterministic conflict (409).  
- Query params must reject invalid CIDR filters early (400).

---

## Testing & Acceptance Criteria
- Swagger/OpenAPI must validate.  
- Contract tests using `pytest` & generated test data up to 10 k CIDRs.  
- Postman collection covering happy path & error path.

---

## Security / Privacy Notes
- All endpoints require auth except `/health/*`.  
- Rate limit header optional but recommend `429` handling.

---

## Future Considerations / TODO
- WebSockets for real-time updates.
