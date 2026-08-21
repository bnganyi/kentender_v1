# Procurement Planning — Gate 01 Domain Foundation

**Document ID:** PLANNING-MVP1-GATE-01-1.0  
**Status:** Done (2026-08-09)  
**Authority:** Cursor Prompt 01; REQ v1.4 §9 / §13; tracker `PLN-GATE-01`  
**Prerequisite:** `GATE_PP2_RETIREMENT.md` RET-005 Done  

---

## 1. Goal

Clean MVP-1 persistence under `procurement_planning/`: logical Plan → Plan Version → Plan Item (+ allocations and evidence DocTypes), with ten Prompt 01 invariants enforced in thin services. No Stitch UI, roles matrix, or canonical seed (Gate 02+).

---

## 2. Delivered DocTypes (REQ names)

| DocType | Notes |
|---|---|
| Procurement Plan | Reshaped: `lifecycle_state` Open/Closed/Cancelled; PE + `financial_year`; version pointers |
| Procurement Plan Version | Draft → Approved / Superseded / …; concurrency token |
| Procurement Plan Item | Stable `plan_item_code`; Proposed / Active / Removed |
| Procurement Plan Item Version | Values per Plan Version; carry-forward marker |
| Plan Demand Allocation | Draft / Effective / Reversed |
| Departmental Submission | Schema ready |
| Plan Decision | Written on approve |
| Plan Validation Result | Schema ready |
| Publication Event | Schema ready |
| Planning Handoff Snapshot | Schema ready |

---

## 3. Services (thin)

- `create_procurement_plan`
- `open_or_create_plan_revision`
- `add_demand_to_plan` (minimal Draft path)
- `approve_plan_version` (atomic; Effective once; Planning Consumption write)

Shared guards: `services/_invariants.py` (PE/FY uniqueness, operational roles, concurrency, FY dates).

---

## 4. Evidence

```bash
bench --site kentender.midas.com migrate
bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_planning_mvp1_schema
# 5/5 OK

bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_planning_mvp1_invariants
# 10/10 OK

bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_planning_mvp1_no_package_dual_write
# 2/2 OK (PLN-ABS-018)

bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_pp2_full_removal_abs
# 4/4 OK (still green; MVP services/ allowed)
```

---

## 5. Explicitly not in Gate 01

- `PLN-PERM-*`, `PLN-SEED-*`, Stitch `PLN-UI-*`, `PLN-SCH-013` page_js  
- Full workspace / validation / publication / tender take-up product services  

**Next:** Gate 02 — scope, roles, canonical seed.
