# H3 — Procurement Planning module exit checklist

**Date:** 2026-04-24  
**Authority:** [9. Cursor Pack.md](./9.%20Cursor%20Pack.md) §H3, prior **H1** / **H2** reviews, Phases A–G tracker.

---

## Pass / fail by section

| Section | Verdict | Notes |
|---------|---------|--------|
| **A. Domain** | **Pass** | Plan, Package, Package Line, Template, Profiles shipped (A1–A4). Derived totals: package `estimated_value` and plan `total_planned_value` (A5). **Orphans:** no automated global orphan purge in-app; rely on workflow + FK usage — **acceptable** for v1; operational DBA hygiene out of scope. |
| **B. Governance** | **Pass** | State machines + workflow APIs + `pp_policy` (H1). **H3 code:** `_validate_parent_plan_draft_for_bootstrap` on `Procurement Package` — new inserts and `plan_id` changes (non-admin) require parent plan **Draft**, matching `apply_template_to_demands`. Template mandatory, locks, approvals, method override — H1. |
| **C. Integration** | **Pass** | Package lines: Demand status gate, Budget Line required, **must match** Demand’s budget line; template apply **does not** mutate Demand (H1). |
| **D. UI** | **Pass** | Workbench, detail panel, builder/tabs, template modal, business IDs (H2 + tracker D*). |
| **E. Permissions** | **Pass** | `pp_record_permissions`, `has_permission` hooks, `pp_policy`, workbench access shell (E1–E3). |
| **F. Seed and tests** | **Pass** | F1/F2 + G1/G2/G3 documented; site run: `test_procurement_planning_h3_plan_bootstrap` added for plan-draft guard. **Operational:** run full `bench run-tests` / `ui-smoke` on release branch before Tendering cut. |
| **G. Downstream trust** | **Pass (conditional)** | **Ready** state reached only via `Approved` + preconditions (≥1 line, competitive → decision criteria) on Document validate and workflow. **Tendering module** must still treat `Procurement Package` in **Ready** as handoff input and re-validate DocPerm scope — **not implemented here** (scope boundary per PRD). |

---

## Blockers

**None** for declaring **Procurement Planning v1 implementation complete** against the locked Cursor Pack scope (Planning only; no Tendering build in this module).

---

## Recommended fixes before moving to Tendering (cross-module)

1. **Tendering intake contract** — Document which fields Tendering reads (`status == Ready`, `package_code`, lines → demands, etc.) and add **Tendering-side** integration tests that consume PP fixtures (or API contract tests).  
2. **Operational gates** — Run full G1 + procurement Playwright G3 on CI/UAT with seeded `F1` data; re-seed after governance smoke that leaves plans **Approved**.  
3. **Threshold rules** — When business enables `threshold_rules` interpretation, extend C3 + UI preview (currently v1 no-op per tracker).  
4. **Monitoring** — Add production alerts for workflow API failures / validation spikes if desired.

---

## Artifacts closed in this H3 pass

| Item | Location |
|------|----------|
| Plan–Draft bootstrap guard | `procurement_planning/doctype/procurement_package/procurement_package.py` — `_validate_parent_plan_draft_for_bootstrap` |
| Regression test | `procurement_planning/tests/test_procurement_planning_h3_plan_bootstrap.py` |

---

## Module exit declaration

**Procurement Planning** is **ready to exit** the implementation track defined in [Procurement-Planning-Implementation-Tracker.md](./Procurement-Planning-Implementation-Tracker.md) (Phases **A–H**), with **Tendering** work explicitly **out of scope** for this exit and tracked as a **downstream programme**.

**Signed off (engineering):** 2026-04-24
