# STD Engine — Official Library UI — ISSUES_LOG

**Canonical log** for admin-revamp / Official Library UI issues prefixed **`STD-LIBU-*`**.

**Tracker:** [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md)

**Specs:** [`1. std_engine_ui_refactor_official_std_library_model.md`](1.%20std_engine_ui_refactor_official_std_library_model.md) · [`2. cursor_pack_std_engine_official_library_ui.md`](2.%20cursor_pack_std_engine_official_library_ui.md)

**Cross-links:**

- Governance / lifecycle: [`../workstream-1/ISSUES_LOG.md`](../workstream-1/ISSUES_LOG.md) (**STD-GOV-***)
- Planning → tender handoff: [`../../planning-to-tender-handoff/ISSUES_LOG.md`](../../planning-to-tender-handoff/ISSUES_LOG.md) (**STD-INT-***) when eligibility or seed contracts overlap

---

## Open

| ID | Type | Summary | Status |
|----|------|---------|--------|
| | | *No open items.* | |

---

## Closed

| ID | Type | Summary | Status |
|----|------|---------|--------|
| STD-LIBU-001 | meta | **Desk-first delivery:** pack `/api/std-engine/...` routes are conceptual; implementation is `kentender_procurement` whitelist methods + `frappe.call`. Evidence: [`STD-LIB-REST-mapping.md`](STD-LIB-REST-mapping.md), [`STD-LIB-0700_implementation_review_report.md`](STD-LIB-0700_implementation_review_report.md) §4. SPA / `frontend/.../stdLibraryApi.ts` not built — §A6 programme acceptance. | Closed (2026-05-08) |
| STD-LIBU-002 | test | **Bench regression concurrency:** parallel `bench run-tests --module` jobs against the same site can contend on `STD Template` (lock timeout / `TimestampMismatchError`). Mitigation: run C7 modules sequentially; use [`scripts/run-std-library-regression.sh`](../../../../scripts/run-std-library-regression.sh). Documented in [`STD-LIB-section-C_smoke_environment_and_results.md`](STD-LIB-section-C_smoke_environment_and_results.md). | Closed (2026-05-08) |

---

## How to log

1. Add a row under **Open** with the next **`STD-LIBU-NNN`** (scan Open + Closed for max N).
2. Reference the id from **Notes** in [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md).
3. When resolved, move to **Closed** with a short evidence pointer (PR, test, commit).

**Types (examples):** `ux` | `permission` | `api` | `governance` | `desk` | `test` | `a11y` | `meta` | `cross-handoff`
