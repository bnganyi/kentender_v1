# STD-GOV-014 — Implementation review report

**Workstream:** STD Template Governance and Lifecycle (production readiness Workstream 1)  
**Pack:** [7. std_template_governance_lifecycle_complete_cursor_implementation_pack.md](7.%20std_template_governance_lifecycle_complete_cursor_implementation_pack.md) (doc 7 §23 tail)  
**Date:** 2026-05-04  
**Site / evidence:** `bench --site kentender.midas.com run-tests` (see §5)

---

## 1. Completed tickets

| Ticket | Title | Status |
|--------|--------|--------|
| STD-GOV-001 | Roles seed (doc 7 §6) | Done |
| STD-GOV-002 | `STD Template` governance fields (§7) | Done |
| STD-GOV-003 | Child DocTypes + child tables (§§8–10) | Done |
| STD-GOV-004 | Constants + canonical hash helpers (§§11–12) | Done |
| STD-GOV-005 | Lifecycle audit event writer (§13.5 / §12) | Done |
| STD-GOV-006 | Governance validation service (§13.2, §15) | Done |
| STD-GOV-007 | Lifecycle transitions (§13.3, §14) | Done |
| STD-GOV-008 | Eligibility, usage, impact, resolve (§13.4, §16) | Done |
| STD-GOV-009 | Governance snapshot + hash (§13.5 snapshot, §18) | Done |
| STD-GOV-010 | `STD Template` controller guards (§19) | Done |
| STD-GOV-011 | Desk admin UI + whitelisted API (§20) | Done |
| STD-GOV-012 | WORKS POC governance seed / `after_migrate` (§21) | Done |
| STD-GOV-013 | §22 test matrix (`test_std_template_governance*.py`) | Done |
| STD-GOV-014 | This implementation review | Done |

**Not in ticket sequence but required for acceptance:** [8. std_template_governance_lifecycle_smoke_test_specification.md](8.%20std_template_governance_lifecycle_smoke_test_specification.md) (**§C** in [IMPLEMENTATION_TRACKER.md](IMPLEMENTATION_TRACKER.md)) — **not executed** in this pass; remains the minimum post-implementation smoke gate.

---

## 2. Primary deliverables (files / areas)

Implementation lives under app **`kentender_procurement`** unless noted.

### Services (`tender_management/services/`)

- `std_template_governance.py` — constants, lifecycle/validation status literals, event codes, `canonicalize_std_package_payload`, `compute_std_package_hash`, protected field names.
- `std_template_governance_events.py` — `write_std_template_lifecycle_event`.
- `std_template_governance_validation.py` — `run_std_template_validation`, findings helpers, payload validation wrapper.
- `std_template_governance_lifecycle.py` — submit / return / reject / approve / activate / suspend / reinstate / supersede / retire / archive; role gates and SoD.
- `std_template_governance_usage.py` — tender eligibility, `record_std_template_usage`, impact, `resolve_active_std_template_for_context`.
- `std_template_governance_snapshot.py` — baseline snapshot JSON + SHA-256, `EVT_SNAPSHOT_GENERATED`.

### DocTypes (`kentender_procurement/doctype/`)

- `std_template/` — extended JSON, `std_template.py` / `std_template.js` (whitelisted governance methods, guards, desk helpers).
- `std_template_lifecycle_event/`, `std_template_validation_finding/`, `std_template_usage/`.

### Seeds / hooks

- `tender_management/seeds/std_template_governance_roles.py` — `after_migrate`.
- `tender_management/seeds/std_template_governance_seed.py` — `after_migrate` (STD-GOV-012).
- `hooks.py` — `after_migrate` entries for roles + seed.

### Tests (`tender_management/tests/`)

- Per-ticket: `test_std_template_governance_*_gov00X.py` (roles through desk API), `test_std_template_governance_seed_gov012.py`.
- §22 matrix (STD-GOV-013): `test_std_template_governance.py`, `test_std_template_governance_permissions.py`, `test_std_template_governance_audit.py`.
- Regression anchors: `test_std_works_poc_step9_doctypes.py`, `test_std_works_poc_step10_loader.py`, `test_std_works_poc_step11_engine.py`.

### Desk UI / E2E

- `apps/kentender_v1/tests/ui/smoke/procurement/std-template-governance-desk-gov011.spec.ts` (Playwright, STD-GOV-011).

---

## 3. Migrations / patches

Recorded in `kentender_procurement/patches.txt` and executed via `bench migrate`:

| Patch module | Purpose |
|--------------|---------|
| `kentender_procurement.patches.std_gov_002_backfill_std_template_governance_fields` | Backfill new governance columns on existing `STD Template` rows |
| `kentender_procurement.patches.std_gov_002b_backfill_template_version` | Backfill `template_version` from labels / package version |

No additional governance-specific patches beyond these two were required for STD-GOV-003+ (child tables ship with DocType sync).

---

## 4. Tests run (commands)

From bench root, site **`kentender.midas.com`**:

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement --module <MODULE>
```

Modules exercised in the **rollup pass** (2026-05-04):

1. `kentender_procurement.tender_management.tests.test_std_template_governance_roles`
2. `…test_std_template_governance_doctype_gov002`
3. `…test_std_template_governance_doctype_gov003`
4. `…test_std_template_governance_hash_gov004`
5. `…test_std_template_governance_events_gov005`
6. `…test_std_template_governance_validation_gov006`
7. `…test_std_template_governance_lifecycle_gov007`
8. `…test_std_template_governance_usage_gov008`
9. `…test_std_template_governance_snapshot_gov009`
10. `…test_std_template_governance_controller_gov010`
11. `…test_std_template_governance_desk_api_gov011`
12. `…test_std_template_governance_seed_gov012`
13. `…test_std_template_governance`
14. `…test_std_template_governance_permissions`
15. `…test_std_template_governance_audit`
16. `…test_std_works_poc_step9_doctypes`
17. `…test_std_works_poc_step10_loader`
18. `…test_std_works_poc_step11_engine`

**§22.1–§22.3 note:** run modules 13–15 **sequentially** (or isolated from other DB-heavy suites) to reduce the risk of MariaDB deadlocks on `tabSTD Template Lifecycle Event` seen when multiple `bench run-tests` processes hit the same site concurrently.

---

## 5. Tests passed / failed

| Scope | Result |
|-------|--------|
| Rollup above (18 modules) | **159 tests, 0 failures** (2026-05-04) |

**Follow-up fix in this review cycle:** `test_std_template_governance_usage_gov008.py` — `tearDown` now clears `STD Template Usage` child rows and resets `tender_usage_count` / lock flags before `delete_doc`, matching the pattern used in STD-GOV-013 permission/audit tests. Without this, `on_trash` blocked cleanup after `record_std_template_usage`.

---

## 6. Assumptions

- **Site:** Automated evidence uses **`kentender.midas.com`** with migrations applied and governance roles present (`after_migrate` or equivalent).
- **Administrator / test users:** Integration tests rely on `Administrator` or short-lived users created in-test (e.g. §22.2); not a substitute for full doc 8 **role-matrix UAT** on a clean tenant.
- **WORKS POC:** Primary governed template code remains **`KE-PPRA-WORKS-BLDG-2022-04-POC`**; loader file-hash and governance canonical hash remain distinct concepts (Step 10 vs doc 7 §12).
- **Developer seed:** STD-GOV-012 **active** mode is tied to `frappe.conf.developer_mode` unless `force_mode` is used in code/tests.

---

## 7. Deviations from pack / open items

| Item | Where tracked | Summary |
|------|----------------|---------|
| Field / column naming & schema choices | [ISSUES_LOG.md](ISSUES_LOG.md) **STD-GOV-102** | e.g. `package_json` / `manifest_json` instead of `package_payload_json` / `package_manifest_json`; `procurement_category` Select; `status` vs `lifecycle_status` coexistence; `template_family` Select mapping; explicit `template_version`. |
| Role naming product policy | [ISSUES_LOG.md](ISSUES_LOG.md) **STD-GOV-101** | `Procurement Planner` vs `Procurement Planning Officer` — governance seeds pack-exact names; DocPerm mapping deferred. |
| **`std_template_governance_audit.py`** service file | Pack §24 bullet list | Not implemented as a separate module; behaviour is covered by **`std_template_governance_events.py`** + lifecycle/validation writers. |
| **`std_template_governance_mapping.py`** | Pack §24 optional | Not present; **planning → tender** resolution / mapping depth deferred per **`STD-INT-*`** (see STD-GOV-008 notes in tracker). |
| **Doc 8 smoke gate** | [IMPLEMENTATION_TRACKER.md](IMPLEMENTATION_TRACKER.md) §C | Scenarios in doc 8 not executed in this review; C1–C3 remain **Not started**. |

---

## 8. Blockers

- **None** for declaring STD-GOV-001–013 and **ticket-level** STD-GOV-014 (this document) complete on the evidence site.

**Residual programme risk (not a code blocker):**

- **Doc 8 end-to-end smoke** (import → … → archive, SoD negatives, migration narrative) is still outstanding for a **programme-complete** declaration of Workstream 1 operational readiness.
- **Concurrent CI / agents:** avoid parallel `bench run-tests` against the same site for governance modules that append lifecycle rows, or accept occasional MariaDB **1213 deadlock** retries.

---

## 9. Pack acceptance criteria (§25 rollup)

All **STD-GOV-IMPL-AC-001** … **017** are marked **Yes** in [IMPLEMENTATION_TRACKER.md](IMPLEMENTATION_TRACKER.md) with evidence pointers, subject to the deviations in §7 and the open smoke gate in §1 / §8.

---

## 10. Sign-off

This report satisfies **doc 7 — Ticket STD-GOV-014** (“Cursor shall report” items §1–§8). Further work is **product QA** (doc 8 §C) and resolution of **ISSUES_LOG** items **STD-GOV-101** / **STD-GOV-102** as needed for production policy.
