# iPAM — Technical Specification Set

> **Purpose**  
> Provide a precise, implementation‑agnostic blueprint that lets a coding agent
> rebuild the iPAM proof‑of‑concept into a production‑grade system.

---

## Document Map

| Doc | Purpose |
|-----|---------|
| `api_spec.md` | Public REST API (CRUD, tree view, health, etc.) |
| `storage_backend_spec.md` | Pluggable storage backend interface & contracts |
| `auth_backend_spec.md` | Pluggable authentication backend interface & contracts |
| `cidr_hierarchy_spec.md` | CIDR model, hierarchy rules, validation engine |
| `ui_spec.md` | Modern SPA consuming the API |

---

## Global Scope & Principles

1. **API‑First:** All functionality is exposed over HTTP/JSON.  
2. **Pluggability:** Storage and Auth layers are late‑bound via well‑defined interfaces.  
3. **Zero State Corruption:** CIDR hierarchy must never contain overlaps or duplicates.  
4. **Test‑Driven Development:** Every requirement has acceptance criteria.  
5. **Security by Default:** No plaintext secrets; least‑privilege access patterns.

---

## Known Limitations (for POC → Prod)

- No RBAC or fine‑grained ACLs yet.  
- File‑based storage lacks concurrency guarantees under heavy write contention.  
- UI lacks offline support and accessibility audit.

---

*See individual spec files for detailed requirements.*
