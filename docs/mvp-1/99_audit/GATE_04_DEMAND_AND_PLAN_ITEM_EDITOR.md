# Procurement Planning — Gate 04 Demand modal and Plan Item editor

**Document ID:** PLANNING-MVP1-GATE-04-1.0  
**Status:** Done (2026-08-10)  
**Authority:** Cursor Prompt 04; Stitch `PLN-UI-04`…`06`; REQ v1.4 §10.2–10.8 / §18 AC-002…004, AC-011…014, AC-016  
**Prerequisite:** `GATE_03_WORKSPACE_AND_REGISTER.md` Done  

---

## 1. Goal

Ship Gate 04 so a Procurement Planner can select eligible Approved Demands, create one Proposed Plan Item with Draft allocations, and complete method / schedule / aggregation / lotting / statutory decisions in a focused editor — **without mutating Demand, Budget, reservation, or Strategy**.

**Exit phrase:** *A planner can create and complete one valid Proposed Plan Item without upstream mutation.*

---

## 2. Delivered

### Routes / surfaces

| Stitch | Desk surface | Implementation |
|---|---|---|
| PLN-UI-04 | In-page dialog on plan builder | `planning_ui_fixtures/add_demand_dialog.js` + `bindPlanningBuilder` |
| PLN-UI-05 | Populated Draft builder | Shared `builder.js` (issue strip, columns, Run validation) |
| PLN-UI-06 | `procurement-plan-item-editor` | `plan_item_editor.js` + `planning_item_editor_page.js` |

Shell: `kt_cl_shell.enterNative` + fixtures with `kt-stitch-canvas` (no iframe, no Tailwind CDN, no generic `frappe.ui.Dialog` for UI-04).

### Services / whitelist

- `list_eligible_demands` — PE/OU scope; Approved + Planning Ready + not fully planned
- `add_demand_to_plan` — eligibility-complete; multi Need Items; amount caps; Draft allocations; no upstream mutation
- `update_plan_item` — structured `{ok:false, errors:{field:msg}}`
- `aggregate_plan_allocations` — lineage preserve; anti-split
- `validate_plan` — Draft issue-led; `user_may_set_ready: false`
- `get_plan_item_editor` — RO approved source + writable fields + attention
- `get_plan_builder` — `add_demand_pending_gate: false`; UI-05 columns + issue strip
- `prepare_planning_gate04_ui` — empty Draft + eligible Demand; optional `with_plan_item`

### Schema

- Plan Item Version editor fields: arrangement / multi-year, aggregation / lotting, statutory treatment, six milestone dates, method override grounds

### Chrome + gates

- Registry: `procurement-plan-item-editor` (+ builder remains registered)
- UI-04 dialog chrome asserted in Playwright when open (overlay; not a separate Desk route)
- `make ui-planning-builder-gate` (depends on `ui-stitch-desk-chrome-gate`)
- Layout guard covers UI-01…06 fixtures + live bind

**Out of Gate 04:** PLN-UI-07…10, dept sign-off, `approve_plan_version` completeness, packages / release / consumption.

---

## 3. Evidence commands

```bash
bench --site kentender.midas.com clear-cache

bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_list_eligible_demands
bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_add_demand_to_plan_gate04
bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_update_plan_item
bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_aggregate_plan_allocations
bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_validate_plan
bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_planning_ui_stitch_layout_guard

cd apps/kentender_v1 && make ui-planning-builder-gate
make -C apps/kentender_v1 ui-stitch-desk-chrome-gate
```

**Recorded 2026-08-10:** `make ui-planning-builder-gate` green (service modules OK; Playwright `planning-builder` / `planning-add-demand` / `planning-plan-item-editor` **4 passed**).

### Visual / fidelity pass (2026-08-10)

Hard rule: Stitch HTML is the contract — not an approximation.

Fixes after Gate 04 ship review:
- **UI-04:** Re-ported dialog markup from `PLN-UI-04.html`; live-bind rows match Stitch (checkbox `w-4 h-4 mt-1 align-top`, search `pl-10` + inset-y icon, amount inner `font-data-md` divs, funding pill, end-of-list row, selected `bg-primary/5`).
- **CSS:** Desk input padding rule no longer overrides Stitch `pl-10` (search icon alignment); checkbox size restored; modal utilities pinned.
- **UI-05:** Populated builder hides UI-03-only filter row + planning-period meta; item rows use Stitch Continue + `arrow_forward` stack.
- **UI-06:** Select chevrons restored to Stitch `arrow_drop_down`.

Evidence: layout guard + `planning-add-demand` / builder / editor Playwright green after fidelity pass.

### Plan Item formation (Pack v1.3 / Stitch PLN-UI-04–06)

**Authority:** [`Procurement_Planning_MVP1_Cursor_Implementation_Pack_v1.3.md`](Procurement_Planning_MVP1_Cursor_Implementation_Pack_v1.3.md) Prompt 04 + approved Stitch HTML. (Pack cites Stitch Prompts v1.5; if that markdown is absent, use approved `ui_design/PLN-UI-04.html` / `PLN-UI-06.html`.)

**Canonical behaviour:**

- **PLN-UI-04** is single-select **source selection** only (no packaging radios, no method/revision fields).
- Default confirm: one Approved Demand → **one** Proposed Plan Item with one Draft allocation per available Need Item; Draft successor create/reuse is server-side in the same transaction; route to PLN-UI-06.
- Secondary **Plan Need Items separately** (multi–Need Item only): requires division reason + anti-splitting; creates **N** Proposed Plan Items; never stores cosmetic `Keep separate`.
- Aggregation metadata (`aggregation_decision = Combine`) is set only when **Add another approved Demand to this Plan Item** calls `aggregate_plan_allocations`.
- **PLN-UI-06** completes the already-created item (lotting retained); no Combine / Keep separate radios; no Demand reselection.

---

## 4. Tracker rows closed by this gate

`PLN-UI-04`…`06`, `PLN-UIC-001` (editor + dialog chrome), `PLN-UIC-002` (editor), `PLN-SVC-003`…`007`, `PLN-AC-002`…`004`, `PLN-AC-011`…`014`, `PLN-AC-016`, `PLN-NFR-006` (issue shape), `PLN-GATE-04`, related schema for editor fields.

**Next:** Gate 05 — departmental contribution + consolidated review / approval (`PLN-UI-07`…`08`).
