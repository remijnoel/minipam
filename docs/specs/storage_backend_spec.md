# Storage Backend Plugin Interface

## Objective
Define a stable interface that lets contributors add new persistence
backends (file, PostgreSQL, DynamoDB, S3-object, etc.) without touching
core logic.

---

## Background / Context
- POC ships File & In-Memory backends.
- Need prod-ready alternatives (SQL, object storage).

---

## Requirements

### Functional Requirements
- Interface `CIDRStorage` with methods:  
  - `get(cidr:str) -> CIDRBlock|None`  
  - `put(block:CIDRBlock) -> None`  
  - `delete(cidr:str) -> None`  
  - `list(parent:Optional[str]=None, *, recursive:bool=True) -> List[CIDRBlock]`  
  - `stats() -> Dict[str,Any]` *(count, backend-specific metrics)*  
- **Atomicity:** `put` & `delete` are atomic from API perspective.
- Backends must accept config via typed dict (e.g., connection string).

### Non-Functional Requirements
- Thread-safe or async-safe under FastAPI default workers.  
- 95th-percentile `get` latency < 20 ms at 10 k CIDRs.  
- Must not mutate input objects (defensive copy).

### Out of Scope
- Schema migrations (handled by caller).  
- Cross-backend replication.

---

## Inputs & Outputs
- Inputs = `CIDRBlock` model (see API spec).
- Outputs = same model or iterable list.

---

## Dependencies / Constraints
- Open-source libraries permissible if OSI-approved.  
- No GPL-only deps.

---

## Edge Cases / Gotchas
- Partial write then crash → must not corrupt data.  
- Case-insensitive tags? Backend must store exactly as provided.

---

## Testing & Acceptance Criteria
- Contract test suite runs each backend against ~5 k random CIDRs,
  verifying CRUD, hierarchy invariants, and concurrency (pytest-xdist).

---

## Security / Privacy Notes
- Backend secrets (passwords, keys) retrieved via env vars or secret store;
  **never** stored in config files.

---

## Future Considerations / TODO
- Multi-region replication strategy (event sourcing?).
