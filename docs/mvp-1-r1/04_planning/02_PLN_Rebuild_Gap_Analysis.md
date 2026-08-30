# PLN-CHG-001 v1.2 — Procurement Planning Rebuild Gap Analysis

| Control | Value |
|---|---|
| Authority | `KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1.2.md` (approved 30 August 2026) |
| Companions | `03_PLN_Rebuild_Implementation_Plan.md`, `IMPLEMENTATION_TRACKER.md` |
| Prepared | 30 August 2026 |
| Status | Research artifact. Rows marked **[confirm in Phase 0]** rest on exploration inference, not a direct read of the named function body; do not act on them without that read (Budget cleanup tracker rule-5 pattern). |

## 1. Executive summary

The existing Procurement Planning module (`kentender_procurement/kentender_procurement/procurement_planning/`, ~142 files, ~29,600 lines) implements a **different product** from PLN-CHG-001 v1.2. It was built against the retired **Demands** source model, renders through the prohibited **Stitch/Civic Ledger** design system, and enforces permissions through the prohibited **capability store / Operational Scope Assignment** layer. The Departmental Procurement Plan aggregate — roughly half of the v1.2 domain model (§4.1–§4.6) — does not exist in any form. The module's navigation entry is currently decommissioned to `coming-soon` because its Demand-coupled workspace is known broken.

**Verdict: rebuild in place** (per the §1.1 register test — it removes concepts wholesale, which cannot be patched toward), while deliberately retaining the predecessor's proven transactional mechanics: submission/approve/return flow shape, immutable decision records, idempotency keys, concurrency tokens, `fixture_namespace` isolation, and the seed orchestration entry point.

What is genuinely reusable, what must be corrected, and what must be demolished is catalogued below and finalised file-by-file in Phase 0.

## 2. Which spec the code actually implements

Git history: the module's last substantive feature commits target "Demo v2.7" waves and "Section 9.1 workspace revision" — pre-v1.x Planning documents now superseded by §18. Since then it has only received survival fixes:

- `010ce0d6` (CTX-CHG-001 Phase E) restored the import-dead `api.py` and stubbed two formation endpoints to throw `PLN_DEMANDS_RETIRED`.
- `remove_planning_ui10_and_publication.py` retired the publication UI at runtime while leaving the `Publication Event` DocType directory on disk.
- `setup/sidebar_availability.py:29-32` parks "Procurement Plans" in `PLANNED_SIDEBAR_LABELS` with the comment "Temporary decommission: Planning Home is broken against the deleted Demands doctypes".

CTX-FU-03 (in `KenTender_CTX-CHG-001_Working_Context_v1.0.md`) already records that the Planning Playwright suite and `test_planning_mvp_seed_contract.py` still import retired Demand modules. This rebuild closes CTX-FU-03.

## 3. Domain model diff (§4)

### 3.1 Spec objects with no existing counterpart (net-new)

| §4 object | Nearest existing thing | Gap |
|---|---|---|
| §4.1 DPPSubmissionWindow | none | Net-new. Window states derived from clock, no manual status. |
| §4.2 DepartmentalProcurementPlan (root) | none | Net-new. One root per PE/FY/OU (DB uniqueness, invariant 2). |
| §4.3 DPPVersion | none | Net-new. |
| §4.4 DPPEntry | `Plan Need Allocation` holds Need lineage, but at the wrong layer (plan-side allocation, not departmental entry) | Net-new. `source_line_id` = Need ID or `dpp_entry_id`. |
| §4.5 DPPSubmission (immutable snapshot + attestation) | none | Net-new. Fixed server-supplied certification text. |
| §4.6 DPPValidationTask / DPPValidationDecision | `Plan Validation Result` (rule-check rows, different concept) | Net-new. Classification lives on the decision, not on entry/allocation (§8.1 `ListAcceptedDPPSources`). |
| §4.10 PlanSourceAllocation | `Plan Need Allocation` (Demand/Need hybrid, `allocated_quantity` permits partial) | Replace. v1.2 forbids partial allocation; carries full funding specification + origin. |
| §4.12 PlanGovernanceTask / PlanDecision (AO adoption + one statutory approval) | `Plan Decision` + review-task fields on `Procurement Plan Version` (professional-review era: `Planning Reviewer`, `Planning Authority`, `Designated Approver`) | Replace. The AO-adoption → single-statutory-approval chain does not exist; the old review chain is prohibited (§1.1). |
| §4.14 RequisitionEligibilityProjection | `Planning Handoff Snapshot` + `tender_takeup_projection` (Tender-era handoff) | Replace with `GetRequisitionEligiblePlanItem.v2` (remaining-balance model, sequential partial drawdowns). |

### 3.2 Existing objects that survive as concepts but need rework

| Existing DocType | v1.2 counterpart | Required change |
|---|---|---|
| `Procurement Plan` | §4.7 AnnualProcurementPlan | Keep shape (root + `active_version`/`open_successor` pointers, `record_version`). Add generated title rule, `PLN-{PE}-{FY}-{NNN}` reference, DB uniqueness per PE/FY (invariant 24). Drop `plan_type`, `lifecycle_state` (single-value fields fail the §2.2 data-purpose gate). |
| `Procurement Plan Version` | §4.8 PlanVersion | Keep versioning + concurrency shape. Replace status vocabulary with the nine §4.8 states; add `correction_of_plan_version_id`; remove embedded review-task fields (tasks become their own doctypes). |
| `Procurement Plan Item` + `Procurement Plan Item Version` | §4.9 PlanItem (single doctype; version identity comes from `plan_version_id`) | Major reduction. The Item Version doctype carries six spec-removed field families (see §4 below). v1.2 items live inside one Plan Version and are copied forward by successor creation, so the separate item-version aggregate collapses. **[confirm in Phase 0]** that no retained mechanic (removal-in-successor bookkeeping) still needs a second doctype. |
| Finance fields on `Procurement Plan Item Version` (`finance_*`) | §4.11 FinanceTask / FinanceDecision + reservation references | Extract into task/decision doctypes with per-allocation reservation reference rows; derive `finance_state`, never store Budget positions. |
| `Plan Decision` | §4.12 PlanDecision | Keep the immutable-decision-record shape (actor, capacity, task token, idempotency); re-key to the new task doctypes and two-stage chain. |
| `Publication Event` | §4.13 PlanPublication | Replace: attempt-numbered, destination-configured, `Pending/Acknowledged/Failed/Indeterminate`, activation only on acknowledgement. Old DocType dir is runtime-retired but still ships — delete with its replacement. |

### 3.3 Removed field families present in code today (§1.1 demolition targets)

All on `Procurement Plan Item Version` unless noted; every consumer listed must lose the field in the same phase the replacement lands:

| Removed concept | Fields | Known consumers |
|---|---|---|
| Value Commitment | `pvc_snapshot` | `services/open_or_create_plan_revision.py`, `services/create_planning_handoff_snapshot.py`, `seeds/kentender_mvp_v1.py` |
| Recommended vs planned method | `recommended_method`, `method_basis`, `method_override_*`, `governing_regime` | `services/validate_plan.py`, `services/open_or_create_plan_revision.py` |
| Lotting | `lotting_decision`, `expected_lot_count`, `lot_basis` | 12 files incl. `get_plan_item_editor.py`, `update_plan_item.py`, `get_plan_builder.py`, item-editor UI fixture, 4 tests, 1 Playwright spec |
| Contract period / multi-year | `arrangement`, `multi_year_justification`, `annual_funding_schedule` | editor + validation services |
| Preference/reservation scheme | `preference_reservation_scheme`, `reservation_scope`, `eligible_groups`, `planned_reserved_value` | `services/preference_reservation.py` (157 lines, whole service goes) |
| Actual-milestone monitoring | `ms_*` ×7 + `schedule_change_reason` | `get_plan_implementation.py` (whole service goes), `plan_builder_successor.py`, editor/builder services. Note: v1.2 keeps **seven planned dates** as first-class PlanItem fields — the demolition is of the monitoring/actuals treatment, not the planned schedule. |
| Removal bookkeeping via draft labels | `draft_change_label`, `proposed_removal`, `removal_reason`, `removed_in_version` | `remove_plan_item.py` (968 lines — mechanics partially reusable for `RemovePlanItemInSuccessor`) **[confirm in Phase 0]** |

Concepts the spec removes that are **already absent** (nothing to delete): Begin consolidation command, `Not started` plan state, readiness score, Monitoring Officer role, AO recipient on DPP submission, capability *profiles* (the capability *store* usage is real and listed in §6 below).

## 4. Lifecycle and command gaps (§5, §8)

- §5.1 DPP lifecycle: entirely net-new (no departmental submission path exists — the old model consolidated Demands directly).
- §5.2 Annual Plan lifecycle: partially covered. Exists in some form: draft save, submit-for-review, approve/return, successor open, empty-update cancel, item removal, finance confirm/return. Missing entirely: automatic Draft-plan creation on first DPP acceptance (invariant 2/24 + concurrency), formation from accepted DPP sources (`FormPlanItems` one-each/combined + compatibility rules), `DissolvePlanItem`, correction chain restarting at AO adoption, statutory-approval stage, publication-on-acknowledgement activation, pending-addition holding, source-correction-required marking.
- §8 command envelope: the predecessor already uses idempotency keys and task/concurrency tokens (`plan_decision.command_idempotency_key`, `*_token` fields; `services/planning_tasks.py`) — port the pattern, not the code, since the task engine itself is being replaced (see §6).
- §8.2 requires **expected record version on every mutating command**; present on some paths today, not uniform. **[confirm in Phase 0]**
- §9 error contract: old codes (`PLN_PERMISSION_DENIED`, `PLN_SCOPE_DENIED`, `PLN_PE_SELECTION_REQUIRED`, …) partially overlap the 21 v1.2 codes; the vocabulary is replaced wholesale, no aliases.

## 5. Cross-module contract state (§7) — name deltas to carry

| Spec name | Reality today | Work |
|---|---|---|
| `DepartmentalNeedAccepted.v2` (§7.1) | **Exists at exactly v2** — `departmental_needs/services/events.py` transactional outbox (`Departmental Need Event`: unique `event_id`, per-Need `sequence`, Pending/Delivered per `consumer`). Payload is exactly the §7.1 six-facts set; the Need model carries no Budget Line, amount, Strategy or classification (already removed by NDS-CHG-001 v1.1). There was never a `.v1`. | Consume it. Planning currently uses only the replay reads (`current_accepted_events`, `get_current_accepted_need`) via `services/need_allocations.py`. |
| Superseded / Withdrawn events | Published (`DepartmentalNeedSuperseded.v1`, `DepartmentalNeedWithdrawn.v1`); **no production consumer anywhere** — `consume_events`/`acknowledge` are only called by Needs' own tests. | Net-new: Planning outbox drain + the §7.1 reactions (stale unsubmitted source refresh, **Source correction required** on allocated Draft items, blocked decision when in governance, waiting successor when Active). |
| `NeedPlanningUsageChanged.v1` | **Receiver only**: `departmental_needs.api.project_need_planning_usage` (idempotent on `source_event_id`, requires Procurement Planner role, projects `Not included`/`Fully included`). No publisher exists anywhere. | Net-new Planning publisher, fired only when an Active Plan begins/ceases representing the accepted Need version. |
| `ListEligibleStrategicObjectives` (§7.2) | Real contract: `kentender_strategy.api.strategy_consumer_api.list_strategy_objectives(plan_version_id, …)` → rows with `{id, title, path}`; PE→version resolution is separate (`resolve_strategy_context(procuring_entity, …)`, fails loudly on 0/2+ Active plans); lineage freeze via `create_strategy_snapshot(plan_version_id, objective_id, correlation_key)` (idempotent). | Planning-side adapter named after the spec verb; store Objective/Plan/Version lineage per §7.2. Planning imports **nothing** from `kentender_strategy` today. |
| `ListEligibleBudgetLines` (§7.3) | Real contract exists: `kentender_budget.api.budget_api.list_eligible_budget_lines(procuring_entity, financial_year, source_org_unit=…)` — Active version only, OU-owned lines scoped (BUD-BR-007). **Zero callers outside Budget.** Planning instead reads `Budget Line`/`Budget Line Version` tables directly (`get_plan_item_editor.py:36-48`, `plan_item_finance.py:180-190`) — a boundary violation to close. | Route all Budget-line reads through the published API. |
| `CheckAndReserveFunding` (§7.3) | Two-step contract: `check_funding(...)` → non-mutating result + **check token cached 300 s**, then `reserve_funding(token, …, idempotency_key)` — locks lines in stable order, creates **all reservations or none**, idempotent replay returns `{"reused": True}`. Planning's `plan_item_finance.py` already calls both, but by deep import of the service module and persisting reservation refs onto the nonexistent `Demand Funding Allocation` DocType (guarded by `frappe.db.exists`). | Keep the two-step protocol (the Finance command must fit the 300 s TTL); persist refs on the new §4.11 reservation-reference rows; call through the published API surface. |
| `ReleasePlanningReservations` (§7.3) | Planning releases through the **legacy adapter** `kentender_budget.api.dia_budget_control.release_reservation(reservation_id, reason)` — hardcoded synthetic idempotency key, full-remainder only. The real contract `budget_api.release_reservation(reservation, amount, downstream_event_id, downstream_event_type, idempotency_key)` supports unconverted-remainder release and caller-owned correlation. | Migrate off the adapter; one Planning correlation + idempotency key per release batch; release failure rolls back the Planning transition (§7.3). |
| `RevalidatePlanningReservations` (§7.3) | `budget_api.revalidate_reservations(reservations, downstream_event_id, …)` exists (returns Active / Partially Converted / Needs Attention). **No Planning caller.** | Net-new caller on corrected-Plan submission and pre-downstream checks. |
| Reservation states (§4.11) | `Funding Reservation.status` = `Active / Partially Converted / Converted / Released / Needs Attention` — **matches the spec exactly**, including `remaining_amount` and `plan_source_allocation` link field already present. | None on the Budget side. |

## 6. Permission-layer gap (§6)

Current: `services/planning_permissions.py` (615 lines) implements a 10-role model (`Planning Contributor`, `Planning Reviewer`, `Planning Authority`, `Designated Approver`, `Tender Initiator`, `Planning Viewer`, …) over the capability vocabulary (`plan.view/create/submit/review/approve/recommend/return`, `plan.finance.*`, `plan.handoff`) plus Operational Scope Assignment; tasks are core `Workflow Task` records via `services/planning_tasks.py`. `AUTH-ADR-001-capability-mapping.md` §3 already flags the `plan.*` domain as **BLOCKED on a dual-path conflict** (nine capabilities enforced by two disconnected mechanisms).

v1.2 §6 requires: seven roles/capacities (`Departmental Author`, `Head of User Department`, `Procurement Planner`, `Budget Officer`, `Accounting Officer`, statutory capacity, `Planning Auditor`), **native Frappe Role + Workflow permission + User Permission only**, no second permission store, PE/OU/Budget scope via User Permission (not per-FY), and the §6.1 maker-checker matrix on evidence chains (correction chains included).

Precedent to follow (recorded NDS decisions): **D2** native-only permissions, and **D3** module-local task doctypes rather than core `Workflow Task`, because that engine calls `require_capability()` internally and would rebind the module to the prohibited store. My Work integration moves from core's hardcoded `_PRESENTATION` map (`plan.finance.confirm`, `plan.review`, `plan.approve` rows in `kentender_core/kentender_core/services/my_work.py:16-18`) to a Planning-registered `kt_my_work_providers` hook (NDS pattern).

## 7. Screen, route and navigation gap (§10–§12)

Current UI is entirely **Stitch-era**: 6 Frappe Pages (`planning-workspace`, `procurement-plan-register`, `-builder`, `-item-editor`, `-review`, `-approved`) driven by `public/js/planning_live_bind.js` (1,142 lines) + HTML-string fixtures + `public/css/planning_workspace.css` (2,439 lines), mounted through `cl_shell.mountContent`. There is **no Vue SFC, no bundle, no Industry root** for Planning. The 16 target screens (PLN-DES-01..16) therefore have **zero reusable UI surface**; the spec's §10.1 "reuse the proven Planning UI" claims are satisfied by the *sibling-module* Industry pattern (Needs/Budget page shell, shared `kt_industry_page_rail`), not by the Stitch code. Demolition targets: the 6 pages, all bind/fixture JS, the CSS file, `test_planning_ui_stitch_layout_guard.py` (624 lines asserting the Stitch contract), and `planning_workspace_redirect.js`.

Known framework constraints for the new routes (§10 table):

1. **Slug collisions.** `/app/procurement-plan-item/{id}` is a §10 route, but DocType `Procurement Plan Item` *already* scrubs to `procurement-plan-item`, and a Page always loses to a same-named readable DocType's list view. Likewise a new DocType named "Departmental Procurement Plan" or "Annual Procurement Plan" would collide with its own §10 route. **Decision D2:** Pages own the §10 slugs; DocType names are chosen so their scrubbed slugs never equal a §10 route slug (exact names fixed in Phase 1; NDS precedent: doctype `Departmental Need` vs page `departmental-needs`).
2. **Workspace ownership of `/app/procurement-planning`.** A Workspace fixture named "Procurement Planning" exists (empty links, stale roles incl. `Procurement Officer`, `Finance Reviewer`). Phase 0 verifies Page-vs-Workspace precedence empirically and retires/renames the fixture — carefully: `workspace_sidebar/*.json` is reverse-synced by migrate, and a dangling Workspace/Page link fails the whole-site migrate.
3. **Module-def sidebar swap.** The Page's module is the real Module Def "Procurement Planning", so 3-segment routes trigger Frappe's auto-doctype-sidebar swap; apply the NDS boot-key/setup-skip mitigation.
4. **No `kt_cl_surface_registry.js` entries** for Industry pages. Seven stale Planning entries exist (lines ~528–612, incl. `procurement-plan-update`, whose Page was already deleted) — remove with the surfaces they described.
5. Sidebar: exactly one "Procurement Planning" entry (§10, PLN-AC-059); the old `planning_module_navigation.json` single-entry file is the right shape, currently pointing at the retired `planning-workspace` Page and parked behind `sidebar_availability.py`.

## 8. Context handling (§10, CTX-CHG-001)

Already adopted: `services/planning_context.py` delegates to `kentender_core.services.working_context` (`PLANNING_MODULE = "planning"`, `kt_planning_financial_year`), with tests (`test_planning_context_ctx_chg_001.py`). Keep and extend: PE/FY selectors in the page header per PLN-DES-01, server-side preference only, record routes derive context from the record and reauthorise (§12.1). Playwright fixtures must clear actor context prefs on reset (`_clear_context_preferences` pattern from NDS).

## 9. API surface hygiene

`procurement_planning/api.py` is 1,463 lines of which ~900 are Playwright fixture endpoints (`prepare_planning_gate03_ui` … `prepare_planning_empty_update`) living in production code. **Decision D8:** fixture endpoints live in seed/fixture modules, never `api.py`. The v1.2 API is rebuilt around the §8 commands with request-shaped tests through `frappe.handler` from the start (the NDS-914 `**kwargs`/`form_dict` defect class: four endpoints returned 500 over HTTP while 242 direct-service tests passed).

## 10. Seeds and tests state

- Seeds: `seeds/kentender_mvp_v1.py` (789 lines) plus 4 scenario seeds are Demand-coupled (`scn_pln_add_001.py:90` imports the deleted `demand_lifecycle`; the base seed reads deleted `Demand` doctypes at lines 479/659/751). The core orchestrator's planning stage (`kentender_core/.../seeds/kentender_mvp_v1/planning.py`) is a thin delegator guarded on `frappe.db.exists("DocType", "Procurement Plan")` — the wiring survives; the content is rewritten to the §14 contract (integrated baseline, isolated direct/combined profiles, KEBS ×2, failure profiles, frozen clocks, named actors, never Administrator).
- Python tests: 42 modules / ~7,600 lines. Most assert the old model (Stitch layout guard, gate-era capability tests, Demand seed contract — `test_planning_mvp_seed_contract.py:110` imports a deleted module). Salvage candidates: cross-entity isolation, PE-scope selection, context tests. **[confirm in Phase 0 file-by-file]**
- Playwright: 11 specs / 1,804 lines against the Stitch screens — all replaced per-slice. `Makefile` planning gates (`ui-planning-*-gate`) partially reference deleted spec files and tests; re-pointed per-slice, swept in the release phase.
- Vitest: no Planning project; the repo has **no Vue SFC test toolchain** anywhere. **Decision D9 (user, 30 Aug 2026):** add one (`@vitejs/plugin-vue` + jsdom project) so §15.1(5) is met literally; it lands with the first component in Slice A.

## 11. Documentation hygiene

- `design/` carries **two** design-system bundles: `_ds/kentender-industry-82d82607-…/` (referenced by the PLN artboards) and an older `industry-f4215206-…` **[confirm in Phase 0 which artboards, if any, reference the older one; remove the orphan]**.
- `design/uploads/` holds v1.1 and v1.2 spec copies; the v1.1 upload is stale-by-design (canvas input) — leave, per NDS FU-05 precedent, or clean in the release phase.
- `docs/audit/module_implementation_catalog/04_procurement_planning.md` describes the pre-rebuild model; mark superseded at close.

## 12. Open questions carried into the implementation plan

1. Exact DocType names avoiding §10 slug collisions (Phase 1, D2).
2. Page-vs-Workspace precedence for `/app/procurement-planning` (Phase 0, D3).
3. Whether PlanItem needs a companion item-version doctype for successor bookkeeping or collapses into PlanVersion-scoped rows (Phase 1; §3.2 above).
4. Publication destination adapter shape for `MOH-APP-SANDBOX-v1` (§14.1) — nothing exists for the acknowledged-payload protocol; design in Slice G.
5. Which of the 42 existing test modules survive as-is vs are rewritten (Phase 0 catalogue).
