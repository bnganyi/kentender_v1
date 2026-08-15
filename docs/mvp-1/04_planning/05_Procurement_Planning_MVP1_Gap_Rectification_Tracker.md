# Procurement Planning MVP-1 — Gap Rectification Tracker

**Document ID:** PLANNING-MVP1-GAP-TRACKER-1.0  
**Status:** Active — first-pass audit after C00–C07 / NFR-001–005 close  
**Date:** 13 August 2026  
**Supersedes:** none (does not replace [`04_Procurement_Planning_MVP1_Implementation_Tracker.md`](04_Procurement_Planning_MVP1_Implementation_Tracker.md))

## Goal

Close **real deviations** between the approved Planning pack and what shipped, so the module matches:

- REQ v1.9 functional rules (especially source-once, Finance-after-Plan-Item, Tender Initiator take-up);
- Stitch `PLN-UI-01`…`10` / `05A` / `07A` composition (literal port, not title-only);
- Demo Contract v2.7 identities, personas, and reservation timing;
- Cross-Module Authorization Surface (record vs task vs mutation; actions from server projection).

**Done looks like:** every row below is **Done** with automated test IDs; wrongly-Done claims in the implementation tracker are corrected; no new canvases invented to paper over gaps.

---

## Documentation read gate (mandatory before any GAP ticket)

| Doc | Role |
|---|---|
| [KenTender_MVP_Cross_Module_Operating_Model_v1.1.md](../00_common/KenTender_MVP_Cross_Module_Operating_Model_v1.1.md) | Controlling journey: Demand → Plan Item → Finance → HoP → Tender handoff |
| [Procurement_Planning_MVP1_Requirements_v1.9.md](Procurement_Planning_MVP1_Requirements_v1.9.md) | FR / AC / actors / take-up §10.4 |
| [ui_design/](ui_design/) + [DESIGN.md](ui_design/DESIGN.md) | Visual contract (`PLN-UI-01`…`10`, `05A_*`, `07A`) |
| [Procurement_Planning_MVP1_Stitch_Prompts_v2.0.md](Procurement_Planning_MVP1_Stitch_Prompts_v2.0.md) | Screen contracts |
| [KenTender_MVP_Canonical_Demo_Data_Contract_v2.7.md](../00_common/KenTender_MVP_Canonical_Demo_Data_Contract_v2.7.md) | Seed identities, SCN-*, personas, fixture clock |
| [KenTender_Cross_Module_Authorization_Surface_Design_and_Cursor_Pack_v1.0.md](../00_common/KenTender_Cross_Module_Authorization_Surface_Design_and_Cursor_Pack_v1.0.md) | Neutral vs task; `available_actions`; no disabled-for-missing-role |
| [04_Procurement_Planning_MVP1_Implementation_Tracker.md](04_Procurement_Planning_MVP1_Implementation_Tracker.md) | Current Done claims to correct when this tracker proves a gap |

**Precedence:** CMOM v1.1 → REQ v1.9 → Stitch HTML → Cursor pack v1.8 → Demo v2.7 → Auth surface → Org scope.

**Audit method (13 Aug 2026):** full pack read + service/fixture/seed/page-role comparison. Static; targeted suites from the NFR close remain the last runtime evidence. Do not treat implementation-tracker Done as proof against a GAP row.

---

## Requirements digest (gaps only)

| Source ID | Requirement | Repo deviation | Plan impact |
|---|---|---|---|
| REQ §2.3 / PLN-FR-028 / PLN-AC-003 | Source selection happens once; UI-06 must not reselect/reallocate Demands | `aggregate_plan_allocations` still whitelisted + live-bind aggregate mode | Remove/hard-deny post-formation aggregate |
| REQ §6 / §10.4 / PLN-FR-072 | Tender take-up requires **Tender Initiator** scope | Handoff uses `CAP_PLAN_ITEM_EDIT` (Planner/HoD/Contributor) | New handoff capability; Planner cannot take up unless also Initiator |
| PLN-FR-074 / PLN-AC-018 | Handoff preserves Finance/reservation + Strategy lineage | Snapshot JSON omits strategy/PVC/reservation ids | Enrich snapshot; tests |
| PLN-FR-050 | Validation: Not run / Ready / Needs attention / Blocked / **Stale** | `VALIDATION_STALE` never emitted | Implement stale projection |
| PLN-FR-075 / 076 | Implementation milestones/variance from **downstream** | UI-09 `progress` / `variance` hardcoded `"—"` | Wire derived fields or omit (prefer omission) |
| Auth pack §6.1 / §7.1 | Queues render `available_actions`; do not invent Review from status | Workspace `_finance_work_queue` emits “Review return” without planner capability | Gate actions; Viewer must not see planner CTAs |
| Auth pack §4.3 | Task surface = capability **and** current step | `get_plan_review` `surface: task` from role only | Tighten to In-review + current step |
| Demo §7.1 / §7.4 / §9 | `RSV-MOH-0001` only after post-Planning Finance; Demand approval creates no reservation | Budget+Demands seed attach RSV + BO-confirmed before Planning | Split Demands-only vs full-bundle; move RSV to Planning Finance |
| Demo §7.2 / §7.6 | `DMD-MOH-2027-019` is HoD **scope** return; no BO shortfall at base | Still “Returned shortfall” + Funding Exception 15m | Rewrite returned Demand story |
| Demo §4.6 | Named personas: Grace `moh.procurement.authority@`, Peter `moh.budget.officer@`, HoD `moh.business.approver@` | Those emails missing; finance/approve use dual/approver aliases | Seed contract personas or update contract + validate |
| Stitch PLN-UI-06 | Lotting: “Indicative lots expected” first / details visible | Fixture defaults “No lots expected”, details hidden | Align default fixture + bind |
| Stitch PLN-UI-08 / 10 | Subtitle = full plan title + Draft Version N | Generic “Version 1” / “Annual Procurement Plan” until bind | Bind + assert live title |

---

## Executive summary

Implementation tracker C00–C07 and NFR-001–005 are **domain-complete for the happy path** (formation, Finance, approve, remove, PE isolation, a11y smoke). The remaining work is **correction**, not a new module.

Three clusters matter most:

1. **Permissions / take-up** — Planner can create a Tender handoff; Tender Initiator cannot. Viewer can see a planner Finance “Review return” queue action. Auth pack `available_actions` is not the queue source.
2. **Functional leftovers** — post-formation `aggregate_plan_allocations` contradicts “source selection once”; handoff snapshot is thin; validation Stale and UI-09 downstream variance are unimplemented (omit is allowed if we stop claiming Done).
3. **Seed / demo story** — reservation timing and `DMD-019` still follow the pre-v2.7 Demands-stage Finance/shortfall narrative. Named HoP/BO/HoD emails are not the login personas.

**UI designs:** no screen replaced Stitch `<main>` with invented BEM. Breadcrumbs omitted on purpose (Desk chrome). Highest visual gaps are lotting default (UI-06) and verifying live-bound titles (UI-08/09/10). UI-09 `h1` placeholder is overwritten by `dto.title` in `planning_live_bind.js` — confirm with Playwright, do not re-port the canvas.

---

## Status legend

| Status | Meaning |
|---|---|
| Not started | Confirmed gap; no fix landed |
| In progress | Active coding |
| Partial | First pass; DoD incomplete |
| Done | Automated test IDs in Evidence |
| Out of scope | Tracker §8 / TM2 / WCAG AA |

**Severity:** Blocker (wrong actor or seed story that breaks the demo) · High (REQ contradiction with a Done claim) · Medium · Low.

---

## Wave 0 — Blockers (do first)

| ID | Severity | Work | Source | Wrongly Done in impl tracker? | Status | Evidence |
|---|---|---|---|---|---|---|
| PLN-GAP-PERM-001 | Blocker | Tender take-up must require **Tender Initiator** + PE/OU write scope. Add `CAP_PLAN_HANDOFF` (or equivalent). Planner/HoD/Contributor must **not** create handoff unless they also hold Initiator. Tests: Initiator happy path; Planner deny; Viewer deny. | REQ §6, §10.4, PLN-FR-072/073, PLN-AC-019 | **Yes** — PLN-SVC-014 / PLN-AC-019 | Done | `test_create_planning_handoff_snapshot` 4/4 (`test_creates_immutable_snapshot_and_blocks_propose_removal`, `test_planner_cannot_create_handoff`, `test_viewer_cannot_create_handoff`, `test_rejects_draft_item`); `test_planning_task_capability.test_tender_initiator_can_handoff_planner_cannot`. Service uses `CAP_PLAN_HANDOFF` + PE/OU write. UI-09 has no take-up CTA (export remains publish). |
| PLN-GAP-SEED-001 | Blocker | `RSV-MOH-0001` must exist **only after** post-Planning Finance on completed `PPI-MOH-2027-021`. Demands-only / Budget-only seed must not attach BO-confirmed reservation. Planning seed must call `confirm_plan_item_funding` (or equivalent live service), not `_ensure_v1_finance_and_handoff` status write. | Demo §7.1, §7.4, §8.2, §9; CMOM Finance-after-item | **Yes** — PLN-SEED-001 | Done | Option C: `test_planning_mvp_seed_contract` 7/7 (`test_finance_after_plan_item_and_no_contribution`, `test_idempotent_second_run`); `validate.py` `planning.rsv_0001_after_plan_item` + `planning.rsv_0001_finance_provenance` (`finance_confirmed_by` = BO); Demands-only `demands.principal.no_rsv_link` + `budget.canonical.no_rsv_0001` (`test_kentender_mvp_v1_demands_seed`, `test_dem_seed_004_orchestrator_demands`). Budget tests use `RSV-MOH-TEST-ACT-0001` (`test_budget_funding_activity`). Live `confirm_plan_item_funding` as `USER_BUD_OFFICER` (Peter; Wave 1 SEED-003); no silent adopt of leftover `RSV-MOH-0001`. Dual alias kept. |
| PLN-GAP-SEED-002 | Blocker | Rewrite `DMD-MOH-2027-019` to HoD **scope** return (KES 95m → correct 80m). Remove base-boundary Budget Officer “Insufficient Funding”, Funding Exception 15m, and `validate.py` `demands.returned.shortfall_exception`. | Demo §7.2, §7.6, §9 | Cross-module (Demands seed + validate) | Done | `test_dem_seed_002_returned_shortfall.test_returned_scope_demand_is_canonical_and_idempotent`; `validate.py` `demands.returned.hod_scope_return` + `demands.returned.no_funding_exception` + `demands.returned.no_rsv`. Reason = Demo §7.2 scope quote. FUND-SHORT (`PPI-022`) unchanged. |

---

## Wave 1 — High (permissions + source-once + personas)

| ID | Severity | Work | Source | Files (start) | Status | Evidence |
|---|---|---|---|---|---|---|
| PLN-GAP-FR-001 | High | Remove or hard-deny **`aggregate_plan_allocations`** after initial formation (API, service, live-bind aggregate mode, `test_aggregate_plan_allocations`). UI-06 already hides “Add another Demand”; server must match. | REQ §2.3, PLN-FR-028, PLN-AC-003 | `aggregate_plan_allocations.py`, `api.py`, `planning_live_bind.js` | Done | `test_aggregate_plan_allocations` 2/2 (`test_post_formation_aggregate_is_denied`, `test_parallel_item_aggregate_is_denied`) — `{ok:false, errors:{form:…}}`; whitelist kept; live-bind has no `dialogMode === "aggregate"`; layout guard `assertNotIn("aggregate_plan_allocations", live)`. |
| PLN-GAP-PERM-002 | High | Workspace Finance queue: do **not** emit `Review return` / `Confirm funding` unless the actor has the matching capability. Viewer/Auditor must get View only. Soften **all** operational actions when read-only (today only `add_to_plan` is rewritten). Playwright: Viewer queue has no Confirm/Review return. | Auth pack §6.1–6.3, §8; PLN-FR-081 | `get_planning_workspace.py` `_finance_work_queue` | Done | `test_planning_workspace_api.test_viewer_queue_has_no_finance_task_actions`; read-only rewrites `add_to_plan` / `confirm_funding` / `continue_item`; Playwright `planning-workspace.spec.ts` `Viewer queue has no Confirm funding or Review return` (absent, not disabled). |
| PLN-GAP-PERM-003 | High | Introduce Planning `get_available_actions` (or equivalent) and render workspace/builder/review row CTAs from that projection. Stop constructing Review/Approve from status alone. | Auth pack §6.1, §7.1 | `planning_permissions.py`, workspace/review bind | Done | `get_available_actions` + `primary_queue_action` in `planning_permissions.py`; `test_planning_task_capability.test_available_actions_finance_and_review_from_capability`; workspace `_finance_work_queue` / `_work_queue` consume projection; `get_plan_review` `can_recommend` / `can_return` / `can_approve` derived from the same helper. Wave 2 PERM-004 still owns `surface: task` tightness. |
| PLN-GAP-SEED-003 | High | Seed Demo §4.6 emails: `moh.business.approver@`, `moh.procurement.authority@` (Grace / HoP), `moh.budget.officer@` (Peter). Point SCN-ADD approve/finance at those users **or** formally amend the contract to the implemented aliases and update validate. | Demo §4.6, §7.6 | `users.py`, `scn_pln_add_001.py`, `constants.py` | Done | `test_seed_004_persona_usa` — James `USER_BUSINESS_APPROVER` / Grace `USER_HOP` / Peter `USER_BUD_OFFICER` USA; `test_planning_mvp_seed_contract` 7/7 (`finance_confirmed_by == USER_BUD_OFFICER`); `test_scn_pln_add_001` 7/7 (finance→Peter, V2 approve→Grace). Dual/approver aliases kept. Demo v2.7 not amended. |
| PLN-GAP-SEED-004 | High | `validate.py`: add `include_scn_fund_short` / `include_scn_remove` blocks per Demo §9; orchestrator must be able to run them. | Demo §9 | `validate.py`, `orchestrator.py` | Done | `test_scn_pln_fund_short_001.test_validate_include_scn_fund_short` — one `RSV-MOH-SHORT-001` @ 55m, no `RSV-MOH-0002`, HWD 25m; `test_scn_pln_remove_001.test_validate_include_scn_remove` — no Proposed 022, Draft 455m, 019 eligible, V1 / RSV-0001 / TND-008. Orchestrator `validate_kentender_mvp_v1` accepts flags. Default `run_kentender_mvp_v1` stays V1 (`include_planning=True` only). |
| PLN-GAP-FR-002 | High | Handoff snapshot must include Plan + item/version + allocations + **Finance/reservation** + **Strategy/PVC** lineage (PLN-FR-074). Keep idempotent. | PLN-FR-074, PLN-AC-018 | `create_planning_handoff_snapshot.py` | Done | `test_create_planning_handoff_snapshot` 4/4 — `snapshot_json` has `plan_version_code`, `finance.{status,reservation_id,reservation_code,confirmed_by}`, `strategy_snapshot`, `pvc_snapshot`, alloc `demand_code`; second call idempotent; Initiator-only unchanged. |

---

## Wave 2 — Medium (auth tightness, validation, UI-09 derived fields, seed clock)

| ID | Severity | Work | Source | Status | Evidence |
|---|---|---|---|---|---|
| PLN-GAP-PERM-004 | Medium | `get_plan_review` `surface: "task"` only when capability **and** version is In review (current step). Role alone must not open the professional rail. | Auth pack §4.3, §5; PLN-FR-080–082 | Done | `test_planning_task_capability.test_reviewer_draft_plan_is_neutral_surface`; In-review Reviewer/Approver remain `surface: task` (`test_reviewer_and_approver_task_surface`). |
| PLN-GAP-PERM-005 | Medium | Audit role on `record_plan_decision` / `approve_plan_version` must use USA-backed `actor_planning_roles()`, not raw `frappe.get_roles`. | Auth pack §5.3; PLN-FR-084 | Done | `test_record_plan_decision.test_recommend_stamps_usa_role_not_desk_approver`; `_actor_role` / `_primary_planning_role` use `actor_planning_roles()`. |
| PLN-GAP-PERM-006 | Medium | Playwright: Budget Officer on review route sees **no** Recommend/Approve; Reviewer `approve_plan_version` API deny already exists — add BO review-route case. | Auth pack §7.2; PLN-PERM-006 | Done | `planning-plan-review.spec.ts` — Budget Officer: `kt-pln-ui08-primary` / `kt-pln-ui08-return` hidden; Recommend/Approve buttons absent (`getByRole`). |
| PLN-GAP-FR-003 | Medium | Validation must emit **Stale** when inputs change after a Ready run (PLN-FR-050). Today only Not run / Ready / Needs attention / Blocked. | PLN-FR-050; PLN-SVC-006 Keep/Correct | Done | `test_validate_plan.test_ready_then_input_change_is_stale`; `effective_validation_status` + Ready fingerprint; builder/review/update/workspace DTOs; save no longer auto-revalidates. |
| PLN-GAP-FR-004 | Medium | UI-09 implementation: derive actual milestones / schedule variance from downstream Tender/contract **or omit the columns/KPI** (REQ §2.10 prefer omission). Stop claiming PLN-SVC-015 Done while `progress_label` / `variance_label` / `on_schedule_label` are `"—"`. | PLN-FR-075/076 | Done | `test_get_plan_implementation.test_approved_dto_without_handoff_or_publication` omits those keys; `has_downstream_actuals=False`; Playwright hides On schedule KPI + progress/variance columns. |
| PLN-GAP-SEED-005 | Medium | Fixture clock `2027-11-05T12:00:00+03:00` (constants still `2027-11-03`). Principal Demand `required_by` **31 March 2028** (seed still `2027-09-30`). | Demo §3, §7.1, changelog 2.4 | Done | `FIXTURE_NOW` / `FIXTURE_DATE` = 2027-11-05; `test_kentender_mvp_v1_demands_seed` `required_by_date == 2028-03-31`. |
| PLN-GAP-SEED-006 | Medium | SCN-ADD HoD approval must be a real Business Approver step, not `db.set_value` to Approved. | Demo §7.6; PP2-legacy-removal (no bypass) | Done | `scn_pln_add_001._approve_returned_demand_for_scn`: Anne `create_or_update_demand` + `submit_demand`; James `record_business_decision(Support, release_to_planning=True)`; `test_scn_pln_add_001.test_demand_ready_without_reservation` asserts Support decision + no Demand RSV. |
| PLN-GAP-SEED-007 | Medium | Grant `kisumu.viewer@` Planning Viewer + county USA so read-only county Planning is demonstrable. | Demo §4.6; Auth pack Viewer | Done | `users.py` `USER_KISUMU_VIEWER` + `ROLE_VIEWER` / PE-CGKIS; `test_seed_004_persona_usa`. |
| PLN-GAP-UI-001 | Medium | PLN-UI-06 lotting: Stitch default is **Indicative lots expected** with count/basis visible; fixture defaults **No lots expected** and hides details. Align fixture + live default without inventing BEM. | Stitch `PLN-UI-06.html` | Done | Fixture Multiple lots checked + details visible; `add_demand_to_plan` / editor default `Multiple lots`; layout guard regex; Playwright `kt-pln-ui06-lotting-multiple` checked. |
| PLN-GAP-UI-002 | Medium | PLN-UI-08 / UI-10: assert live subtitle is **full plan title** + Draft/In-review version label (Stitch), not generic “Version 1” / “Annual Procurement Plan”. UI-09 title already binds `dto.title` — Playwright must prove the bound string is the plan name. | Stitch `PLN-UI-08.html`, `09.html`, `10.html` | Done | `get_plan_review.secondary_line` = `{title} · {status} Version {n}`; Playwright UI-08/09/10 assert bound title ≠ fixture “Annual Procurement Plan”. |

---

## Wave 3 — Low (copy, notifications, amend affordance)

| ID | Severity | Work | Source | Status | Evidence |
|---|---|---|---|---|---|
| PLN-GAP-UI-003 | Low | PLN-UI-01 work filter includes “Awaiting Finance confirmation” (not in Stitch option list). Keep if REQ queue needs it; otherwise drop to Stitch set. Document the choice in evidence. | Stitch `PLN-UI-01.html`; PLN-FR-005 queues | Done | **Kept** (REQ queue, not Stitch miss). PLN-FR-040 Finance-after-item. Layout-guard `test_workspace_fixture_markers`; Playwright `planning-workspace.spec.ts` (`kt-pln-ui01-work-filter`). |
| PLN-GAP-UI-004 | Low | PLN-UI-02 currency: Stitch shows USD option; fixture is KES-only. Confirm KES-only is intentional (Kenya MVP) and layout-guard it. | Stitch `PLN-UI-02.html` | Done | Kenya MVP KES-only. `test_register_fixture_markers` `assertNotIn value="USD"`; `test_create_rejects_non_kes_currency`; Playwright `planning-register.spec.ts` (`kt-pln-ui02-currency`). |
| PLN-GAP-UI-005 | Low | PLN-UI-05 static fixture defaults to empty (UI-03) chrome; populated header is bind-toggled. Add a layout-guard or Playwright assert that populated bind shows UI-05 header (`Open Plan · Draft Version N`, `Add approved demands`). | Stitch `PLN-UI-05.html` | Done | Layout-guard `kt-pln-ui05-header` block; Playwright populated builder asserts Open Plan · Draft Version + Add approved demands. |
| PLN-GAP-FR-005 | Low | PLN-AC-005: UI-06 “View Approved Demand” is not an amend path. Add copy/route into Demands correction if pack still requires “directed to Demand amendment”. | PLN-AC-005, REQ §2.9 | Done | Copy + `/desk/demand-detail/` (Approved) or `/desk/demand-form/` (Returned). `demand_desk_route`; `test_copies_demand_strategy_and_pvc_snapshots`; Playwright `kt-pln-ui06-view-demand`. |
| PLN-GAP-FR-006 | Low | Notifications for Finance / professional task owners (PLN-FR-005). No Planning emitters today. | PLN-FR-005 | Done | `emit_notification_log` PE-scoped USA. `test_finance_request_emits_pe_scoped_notification`; `test_submit_notifies_pe_reviewer_not_kisumu`; `test_return_sets_returned` planner log. |
| PLN-GAP-SEED-008 | Low | Planning seed header still cites Contract v2.4; `moh.publichealth.officer@` display name vs “Anne Achieng”; extra personas (`moh.accounting.officer@`) are fine if documented. | Demo §4.6 / §7.2 | Done | Demo v2.7 headers; Anne Achieng (`test_seed_004_persona_usa`); AO extra SoD comment. |

---

## UI fidelity notes (not tickets unless listed above)

| Screen | Verdict | Notes |
|---|---|---|
| PLN-UI-01 | Literal + policy extras | Pagination footer required by desk-table-footer rule. Extra work-filter = GAP-UI-003. |
| PLN-UI-02 | Literal | Breadcrumbs omitted (Desk). Currency = GAP-UI-004. |
| PLN-UI-03 / 05 | Literal after bind | Empty vs populated toggle; GAP-UI-005. |
| PLN-UI-04 | Literal | Formation hidden until selection (bind). |
| PLN-UI-05A ×3 | Literal | Error slots added (NFR-005). |
| PLN-UI-06 | Literal + lotting default drift | GAP-UI-001. |
| PLN-UI-07 / 07A | Literal | Anti-truncate on identity (correct vs Stitch ellipsis). |
| PLN-UI-08 | Literal | Trail empty until bind; subtitle = GAP-UI-002. |
| PLN-UI-09 | Literal shell | Title live-bound; Stitch `truncate` on requirement **must not** be copied. Downstream `"—"` = GAP-FR-004. |
| PLN-UI-05 | Literal | Subtitle = GAP-UI-002. |

No fixture uses invented BEM in place of Stitch utilities. No fixture truncates legal identity. Business codes (PPI / DMD / TND) are correct; raw hashes must stay hidden.

---

## Permissions that already match (do not re-open)

| Area | Evidence |
|---|---|
| Admin / System Manager without USA denied | `planning_permissions.py`; `test_planning_task_capability` |
| Viewer neutral review; no Approve/Return | `get_plan_review`; `planning-task-route-denial.spec.ts` |
| Reviewer Recommend ≠ Approve | `test_reviewer_cannot_approve_plan`; Playwright |
| Finance task BO-only; planner/viewer cannot open drawer | `test_plan_item_finance`; `planning-finance-confirm.spec.ts` |
| County vs MOH PE isolation | `test_planning_cross_entity_isolation` 5/5 |
| Direct-route denial on review | `planning-task-route-denial.spec.ts` |

---

## Out of scope (unchanged)

From implementation tracker §8 and this audit:

- Annual departmental-plan batch certification
- Cross-OU aggregation (Combine remains rejected)
- Targeted HoD reapproval **inside** Planning
- Contribution replacement / PVO engine
- Live reservation→commitment convert (Tender/Contract)
- Creating TM2 Tenders from handoff
- Full WCAG 2.1 AA / axe-core (NFR-004 is labels/keyboard/focus/association only)
- Copying Stitch in-canvas breadcrumbs or GovProcure/IFMIS chrome
- Copying Stitch `truncate` on legal columns

---

## Suggested implementation order

```text
Wave 0  PERM-001 (handoff actor) + SEED-001/002 (demo story)
Wave 1  FR-001 (kill aggregate) + PERM-002/003 (queue actions) + SEED-003/004 + FR-002
Wave 2  PERM-004…006 + FR-003/004 + SEED-005…007 + UI-001/002
Wave 3  Done (2026-08-14)
```

After each wave: update **this** tracker Evidence; if a GAP proves an implementation-tracker Done row false, change that row to Partial and point here.

## Commands (targeted, after a wave)

```bash
bench --site kentender.midas.com run-tests --module kentender_procurement.procurement_planning.tests.test_create_planning_handoff_snapshot
bench --site kentender.midas.com run-tests --module kentender_procurement.procurement_planning.tests.test_planning_task_capability
bench --site kentender.midas.com run-tests --module kentender_procurement.procurement_planning.tests.test_planning_mvp_seed_contract
cd apps/kentender_v1 && npx playwright test --workers=1 \
  tests/ui/smoke/planning/planning-task-route-denial.spec.ts \
  tests/ui/smoke/planning/planning-workspace.spec.ts \
  tests/ui/smoke/planning/planning-plan-approved.spec.ts
```

Never plain `bench build`. One stack on `:8000`.

---

## Change log

| 2026-08-14 | **Wave 3 Done** — UI-003 keep Awaiting Finance (REQ queue); UI-004 KES-only; UI-005 populated header; FR-005 Demands amend route/copy; FR-006 PE-scoped Notification Log; SEED-008 Demo v2.7 / Anne Achieng. Wave 0–2 unchanged. |
| 2026-08-14 | **Wave 2 Done** — PERM-004 task surface iff In review; PERM-005 USA `actor_role`; PERM-006 BO Playwright no Recommend/Approve; FR-003 Stale; FR-004 omit UI-09 actuals; SEED-005 clock 5 Nov 2027 / required-by 31 Mar 2028; SEED-006 live James Support; SEED-007 kisumu.viewer Planning Viewer; UI-001 Indicative lots default; UI-002 live plan titles. Wave 3 unchanged. |
| 2026-08-13 | **Wave 0 Done** — PERM-001 Initiator-only handoff (`CAP_PLAN_HANDOFF`); SEED-001 Option C (`RSV-MOH-0001` only via live Finance); SEED-002 HoD scope return for 019. See Wave 0 Evidence. Wave 1–3 unchanged. |
| 2026-08-13 | Tracker 1.0 created from REQ v1.9 + Stitch ui_design + Demo v2.7 + Auth surface pack vs shipped Planning services/fixtures/seeds. |
