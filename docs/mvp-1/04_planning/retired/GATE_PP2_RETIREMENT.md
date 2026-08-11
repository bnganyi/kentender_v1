# Procurement Planning — PP2 Retirement Programme

**Document ID:** PLANNING-MVP1-PP2-RET-1.2  
**Status:** Complete — RET-001…005 Done (2026-08-09)  
**Date:** 9 August 2026  
**Authority:** User mandate (zero legacy Planning code); REQ §6.1 / §19; Cursor pack §3.1  
**Tracker:** `PLN-RET-001`…`005`  

---

## 1. Goal

**No PP2 Planning code remains.** Inclusion, Package, Package Line, Release, readiness/review package UX, PP2 Planning APIs, workbench, wizard, PP2 Planning seeds/tests, and PP2-only Plan header fields are removed from the product — not frozen beside MVP-1, not shimed as a parallel demo chain.

**Done:** Repository and Desk contain zero operational PP2 Planning path; callers (Home, TM, PLC, TCFG) are cut over or closed; `PLN-ABS-*` structural checks green via `test_pp2_full_removal_abs`; Gate 01 may start.

---

## 2. Sequence status

| ID | Work | Status |
|---|---|---|
| `PLN-RET-001` | Freeze: no new PP2 Planning work | Done |
| `PLN-RET-002` | Remove PP2 Planning UX + APIs + pages + router | Done |
| `PLN-RET-003` | Remove/replace Package imports in Home, TM, PLC, TCFG, seeds | Done |
| `PLN-RET-004` | Delete Package/Inclusion/Release DocTypes, PP2 constants/seeds/tests | Done |
| `PLN-RET-005` | `PLN-ABS-*` + legacy grep green | Done |

---

## 3. Evidence (RET-005)

```bash
bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_pp2_full_removal_abs
# 4/4 OK — DocTypes gone, Desk pages gone, assets gone, no live PP2 module imports
```

Also: `bench --site kentender.midas.com migrate` dropped orphan PP2 pages/DocTypes (`planning-hub`, `create-package-wizard`, `package-detail`, Package/Release orphan DocTypes).

---

## 4. Downstream notes (not reasons to keep PP2)

- **TM / TCFG:** create-from-package and eligible-package queues are **closed** (throw / empty). MVP-1 Plan Item take-up restores entry later.
- **Stable platform / WORKS planning seeds:** skipped with `PP2_PLANNING_RETIRED`.
- **Procurement Plan** DocType shell retained for Gate 01 rebuild (controller stripped of PP2 workflow).
- Closed TM stubs (`create_tender_from_package`, `release_procurement_package_to_tender`, package picker) refuse Package path; they do not restore PP2 Planning.

---

## 5. Next

**Gate 01** — MVP-1 Plan Version / Plan Item domain DocTypes and invariants under `procurement_planning/`.
