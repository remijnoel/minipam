# CIDR Hierarchy & Validation Engine

## Objective
Guarantee CIDR uniqueness, non-overlap, and a navigable parent/child
hierarchy for IPv4 networks.

---

## Background / Context
- Bugs often stem from overlapping subnets; spec formalises rules
  currently embedded in POC rule engine.

---

## Requirements

### Functional Requirements
1. **Uniqueness:** Exact CIDR may appear only once.  
2. **Parent/Child Coherence:**  
   - A CIDR is a *child* of another if it is fully contained (e.g.,
     `10.0.0.0/24` child of `10.0.0.0/16`).  
   - No child may be broader (`/16` cannot live under `/24`).  
3. **No Overlap Among Siblings:** Children of the same parent must not overlap.  
4. **Validation API:** `validate(block:CIDRBlock, storage:CIDRStorage) -> ValidationResult`.  
5. **Traversal API:** `list_children(cidr, depth)` returns tree slice.

### Non-Functional Requirements
- No artificial limit on hierarchy depth (supports hundreds of nested levels).  
- Worst-case validation time: O(n log n) where n = #CIDRs.

### Out of Scope
- Address allocation (IPAM), only CIDR registry.

---

## Inputs & Outputs
- **Input:** Candidate `CIDRBlock`.  
- **Output:** `ValidationResult {is_valid:bool, errors:list[str]}`.

---

## Dependencies / Constraints
- Relies on storage backend for existing set lookup.  
- Must use standard library `ipaddress` (or equivalent in other language).

---

## Edge Cases / Gotchas
- `/0` (default route) is **disallowed** to avoid root-level ambiguity.  
- Inserting `/31` (point-to-point) valid but child rules still apply.
- Deep nesting (100+ levels) should not cause performance degradation.

---

## Testing & Acceptance Criteria
- Exhaustive unit tests for: duplicate, nested, sibling-overlap,
  boundary prefixes (`/0`, `/32`), and deep nesting scenarios.

---

## Security / Privacy Notes
- None beyond normal API auth.

---

## Future Considerations / TODO
- Lease/allocation engine on top of CIDR hierarchy.
