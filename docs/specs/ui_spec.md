# Modern Web UI

## Objective
Deliver a single-page application (SPA) that consumes the REST API and
visualises CIDR blocks in a collapsible tree with create/update/delete
flows.

---

## Background / Context
- POC had a minimal React front; this spec formalises UX for prod.

---

## Requirements

### Functional Requirements
- Login screen (auth backend-agnostic).  
- Dashboard showing: total CIDRs, v4/v6 split, recent activity.  
- **CIDR Tree View:**  
  - Collapsible hierarchy, lazy-load children, search/filter by tag.  
  - Right-click or kebab menu for CRUD actions.  
- Form wizard for creating/updating CIDR with inline validation.  
- Toast notifications for successes/errors.

### Non-Functional Requirements
- Responsive (≥ 320px wide).  
- WCAG 2.1 AA contrast & keyboard nav.  
- First contentful paint < 2 s on 3G network.  
- Use API only; no direct DB calls.

### Out of Scope
- Dark mode (nice-to-have).  
- Drag-and-drop CIDR re-parenting.

---

## Inputs & Outputs
- Inputs = user actions => HTTP calls (see API spec).  
- Outputs = rendered DOM & dispatch events.

---

## Dependencies / Constraints
- Any modern JS framework (React, Vue, Svelte) acceptable; must ship compiled static assets.  
- No CSS frameworks requiring runtime JS (e.g., no jQuery UI).

---

## Edge Cases / Gotchas
- Large trees (> 1 k nodes) → ensure virtualization.  
- Losing auth token mid-session → prompt re-login, don’t silently fail.

---

## Testing & Acceptance Criteria
- E2E tests via Playwright/Cypress covering CRUD & tree collapse/expand.  
- Lighthouse score ≥ 90 perf / 100 a11y.

---

## Security / Privacy Notes
- Store tokens in `httpOnly` cookies when possible; fall back to
  `localStorage` with XSS hardening if backend constraints.

---

## Future Considerations / TODO
- Offline PWAsync with service workers.
