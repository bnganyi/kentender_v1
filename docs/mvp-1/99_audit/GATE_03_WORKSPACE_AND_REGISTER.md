# Procurement Planning — Gate 03 Workspace and Register

**Document ID:** PLANNING-MVP1-GATE-03-1.0  
**Status:** Done (2026-08-09)  
**Authority:** Cursor Prompt 03; Stitch `PLN-UI-01`…`03`; REQ v1.4 registration / PE scope  
**Prerequisite:** `GATE_02_ROLES_AND_SEED.md` Done  

---

## 1. Goal

Ship the first three Planning Desk surfaces so a Procurement Planner can open the workspace under PE/FY context, register an annual plan (zero / single / multi PE), and land on an empty Draft builder — Stitch hand-ports in the real Desk shell with live APIs and browser tests.

**Exit phrase:** *Registration and workspace browser tests pass for every PE-scope state.*

---

## 2. Delivered

### Routes

| Stitch | Desk route | Page JS |
|---|---|---|
| PLN-UI-01 | `planning-workspace` | `planning_workspace_page.js` |
| PLN-UI-02 | `procurement-plan-register` | `planning_register_page.js` |
| PLN-UI-03 | `procurement-plan-builder` | `planning_builder_page.js` |

Note: Workspace slug `/desk/procurement-planning` collides with a Page of the same name — UI-01 uses `planning-workspace`; `planning_workspace_redirect.js` sends `Workspaces / Procurement Planning` → that Page.

Shell: `kt_cl_shell.enterNative` + fixtures with `kt-stitch-canvas` (no iframe, no Tailwind CDN).

### Services / whitelist

- `get_planning_workspace` — PE/FY filters, current plan panel, compact work queue
- `get_planning_create_scope` — zero/single/multi; period dates; no Budget fields
- `create_procurement_plan` — structured `{ok:false, errors:{…}}` + redirect to builder
- `get_plan_builder` — empty Draft empty-state DTO (`add_demand_pending_gate`)
- `prepare_planning_gate03_ui` — Playwright fixture (empty Draft + multi planner + free FY)

### UI seed

- `PLN-SEED-004` helper `pln_seed_004_empty_draft.py` — `PLN-MOH-UI-DRAFT-001` / FY `2029/30` (does not touch Approved V1)

### Chrome + gates

- Registry: `planning-workspace`, `procurement-plan-register`, `procurement-plan-builder`
- `make ui-planning-workspace-gate` (depends on `ui-stitch-desk-chrome-gate`)

**Out of Gate 03:** PLN-UI-04…10 Demand modal, package/release revival.

---

## 3. Evidence commands

```bash
bench --site kentender.midas.com clear-cache

bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_planning_workspace_api

bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_planning_register_api

bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_planning_ui_stitch_layout_guard

cd apps/kentender_v1 && make ui-planning-workspace-gate
```

---

## 4. Tracker rows closed by this gate

`PLN-UI-01`…`03`, `PLN-UIC-001` (three surfaces), `PLN-UIC-002` (register), `PLN-SVC-001`, `PLN-SVC-002` (UI wired), `PLN-SCH-013`, `PLN-GATE-03`, `PLN-SEED-004`, `PLN-AC-001` (Partial→Done via UI+API).

**Next:** Gate 04 — eligible Demand modal (`PLN-UI-04`).
