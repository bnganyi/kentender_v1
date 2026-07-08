# STD Template Governance and Lifecycle — ISSUES_LOG

**Canonical log** for Workstream 1 issues prefixed **`STD-GOV-*`**. Cross-post to [`../planning-to-tender-handoff/ISSUES_LOG.md`](../../planning-to-tender-handoff/ISSUES_LOG.md) as **`STD-INT-*`** only when a item is shared with planning→tender handoff or integrated seed (resolution, eligibility, or seed contract).

**Tracker:** [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md)

**Specs (source of truth):** docs [`1`](1.%20std_template_governance_lifecycle_scope_document.md)–[`8`](8.%20std_template_governance_lifecycle_smoke_test_specification.md) in this folder.

---

## Open

| ID | Type | Summary | Status |
|----|------|---------|--------|
| STD-GOV-101 | policy | **`Procurement Planner`** (core `BUSINESS_ROLES`) vs **`Procurement Planning Officer`** (governance pack doc 7 §6 / doc 3 §4): both may coexist. STD-GOV-001 seeds the pack-exact `Procurement Planning Officer` role; DocPerms and `Has Role` mapping for planning users are deferred to STD-GOV-002+ / product decision — do not silently merge names. | Open |
| STD-GOV-102 | meta | **STD-GOV-002 field reconciliation (doc 7 §7):** (1) Pack `package_payload_json` / `package_manifest_json` are **not** added — use **`package_json`** / **`manifest_json`** as the governed payload + manifest. (2) **`procurement_category`** remains **Select** (WORKS/GOODS/…) vs pack **Data** — intentional deviation. (3) **`status`** (POC manifest mapping) coexists with **`lifecycle_status`** (governance model) until STD-GOV-006/007 unify writers. (4) **`authority`** coexists with **`source_authority`** (same semantics; loader sets both; migrate backfill). (5) **`template_family`** converted to pack **Select**; manifest code `BUILDING_AND_ASSOCIATED_CIVIL_ENGINEERING_WORKS` maps to **`Works`**. (6) **`template_version`** is stored explicitly (not `fetch_from`); patch **`std_gov_002b`** + loader + `validate` backfill from `version_label` / `package_version`. | Open |

---

## Closed

| ID | Type | Summary | Status |
|----|------|---------|--------|
| STD-GOV-001 | meta | STD-GOV-001 roles delivered: `ensure_std_template_governance_roles` + `after_migrate` hook + `test_std_template_governance_roles` (3 tests). | Closed |
| STD-GOV-103 | test | **Doc 8 §32 required evidence pack:** automated §C gate uses **bench + Playwright +** [`STD-GOV-doc8_smoke_environment_and_results.md`](STD-GOV-doc8_smoke_environment_and_results.md) instead of populating `evidence/std_template_governance_lifecycle_smoke/` with screenshots; optional UAT may still fill that folder. | Closed |
| STD-GOV-104 | test | **Doc 8 §33 smoke issue log:** nil issues for doc 8 automated gate tied to STD-GOV-doc8 evidence. | Closed |

---

## How to log

1. Add a row under **Open** (or a dated subsection for bursts of related items).
2. Use **`STD-GOV-NNN`** for new issues (next free integer after scanning **Open** and **Closed**).
3. Reference the id from **Notes** in [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md).
4. When resolved, move the row to **Closed** with a short evidence pointer (PR, test module, commit).

**Types (examples):** `policy` | `migration` | `permission` | `audit` | `ui` | `seed` | `test` | `cross-handoff` | `meta`
