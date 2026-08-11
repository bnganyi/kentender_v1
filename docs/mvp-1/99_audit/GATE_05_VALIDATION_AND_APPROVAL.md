# Procurement Planning — Gate 05 Validation and approval

**Document ID:** PLANNING-MVP1-GATE-05-1.0  
**Status:** Done (2026-08-11)  
**Authority:** Cursor Prompt 05; Stitch `PLN-UI-07`…`08`; REQ v1.5 §8.1 steps 5–6 / PLN-FR-090…098 / AC-006…008 / AC-015 / NFR-002  
**Prerequisite:** `GATE_04_DEMAND_AND_PLAN_ITEM_EDITOR.md` Done; contribution slice (`PLN-UI-07` / `PLN-SVC-008`) Done  

---

## 1. Goal

Ship Gate 05 so after HoD departmental sign-off, a Planner can submit a Ready Draft for review, a Planning Reviewer can recommend or return it, and a Designated Approver / Accounting Officer / Planning Authority can approve or return — with atomic Effective-once lock on approve — on a Desk screen that **matches Stitch PLN-UI-08**.

**Exit phrase:** *A recommended In-review plan can be approved atomically with role segregation; Reviewer/Approver act on the same Stitch canvas.*

---

## 2. Delivered

### Workflow

```
Draft (Ready + contributions) → submit_plan_for_review → In review
  → record_plan_decision Recommend → trail row (status stays In review)
  → record_plan_decision Return → Returned
  → approve_plan_version (Approver) → Approved + Effective allocations + consumption
```

### Routes / surfaces

| Stitch | Desk surface | Implementation |
|---|---|---|
| PLN-UI-07 | Builder contribution drawer | Already Done (`contribution_drawer.js` + bind) |
| PLN-UI-08 | `procurement-plan-review` | `planning_ui_fixtures/plan_review.js` + `planning_review_page.js` + `bindPlanningReview` |

Shell: `kt_cl_shell.enterNative` + `kt-stitch-canvas` (no iframe, no Tailwind CDN, no Dialog stack). In-canvas fake breadcrumb dropped (Desk chrome owns crumbs). Approver variant swaps primary CTA via DTO `rail_mode`.

### Services / whitelist

- `submit_plan_for_review` — Planner; Ready + contributions; Draft → In review
- `record_plan_decision` — Recommend / Return; `{ok:false, errors:{decision_comment}}` for missing return comment
- `approve_plan_version` (hardened) — In review + Ready + prior Recommend; atomic Effective / supersede / consumption / Decision trail
- `get_plan_review` — UI-08 DTO (`rail_mode`, statutory rows, trail, `can_*`, concurrency)
- Builder: `can_submit_for_review` + Submit for review CTA → review route
- `prepare_planning_gate05_approval_ui` — isolated In-review + recommended fixture (SEED-004 style; does not mutate permanent V1 seed)

### Chrome + gates

- Registry: `procurement-plan-review` (+ chrome Playwright surface)
- Layout guard: `test_plan_review_fixture_markers` (summary, statutory, issues, rail CTAs, trail, no matrix)
- `make ui-planning-approval-gate` = chrome gate + SVC-009…011 + layout guard + `planning-plan-review.spec.ts`
- Contribution remains `make ui-planning-contribution-gate`

**Out of Gate 05:** PLN-UI-09…10, publish, tender take-up, revision overview.

---

## 3. Evidence commands

```bash
bench --site kentender.midas.com clear-cache

bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_submit_plan_for_review
bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_record_plan_decision
bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_approve_plan_version_gate05
bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_planning_ui_stitch_layout_guard

cd apps/kentender_v1 && make ui-planning-approval-gate
```

**Recorded 2026-08-11:**

- `make ui-planning-approval-gate` **green** (chrome 24/24 including `procurement-plan-review`; SVC-009…011; layout guard 11/11; Playwright review **2/2**)
- SVC-009 `test_submit_plan_for_review` **4/4**
- SVC-010 `test_record_plan_decision` **4/4**
- SVC-011 `test_approve_plan_version_gate05` **4/4**
- MCP browser: Reviewer canvas shows title, summary, statutory, rail (**Recommend approval**), trail on `procurement-plan-review?plan=…`

### Visual / fidelity pass (2026-08-11)

Hard rule: Stitch HTML is the contract — literal `<main>` port of `ui_design/PLN-UI-08.html` with Stitch utility classes retained; no approval matrix; identity/money columns wrap (no truncate).

---

## 4. Tracker rows closed by this gate

`PLN-UI-08`, `PLN-SVC-009`…`011`, `PLN-AC-006`…`008`, `PLN-AC-015` (approve requires Ready), `PLN-NFR-002` (idempotent approve path covered in Gate 05 happy path / Gate 01 Effective-once), `PLN-UIC-001` (review route), `PLN-UIC-002` (return comment), `PLN-GATE-05`, `PLN-INT-001` consumption on approve (via `approve_plan_version`).

**Next:** Gate 06 — approved plan / implementation + Draft revision (`PLN-UI-09`…`10`).
