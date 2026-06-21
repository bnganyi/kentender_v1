# G0-005 Data/API Availability Evidence

Date: 2026-05-26  
Source inputs: `G0-001_current_ui_inventory_evidence.md`, `G0-002_delete_refactor_list.md`, `G0-003_route_plan_confirmation.md`, `G0-004_main_procurement_shell_confirmation.md`

## 1) Surface-to-route-to-view-model contract matrix

| Surface | Route | Required reset contract shape | Status |
|---|---|---|---|
| Planning Home | `/desk/procurement-planning` | Summary + five business queues (needs planning/review/release/recently released/blocked) | Partial |
| Approved Demands | `/desk/procurement-planning/approved-demands` | Queue/list + selected summary + Include in Plan flow | Ready/Partial (API ready, UI unwired) |
| Plans | `/desk/procurement-planning/plans` | Plan queues + plan list + selected summary | Gap |
| Packages | `/desk/procurement-planning/packages` | Workbench list + selected summary + compact filters | Ready/Partial (API ready, active UI not using canonical endpoint) |
| Package Detail | `/desk/procurement-planning/packages/<package_code>` | Five-tab contextual workbench | Ready/Partial (API available, route/UI contract gap) |
| Released to Tender | `/desk/procurement-planning/releases` | Released list + selected release summary/actions | Ready/Partial (API ready, UI unwired) |
| Evidence (contextual only) | Via `View Evidence` action/drawer | Timeline + records + permissioned technical expansion | Ready (API), relocation still needed in UI |

## 2) API/service mapping (endpoint, purpose, consumer, reset fit)

| Endpoint | Purpose | Current consumer | Reset fit |
|---|---|---|---|
| `landing.get_pp_landing_shell_data` | Role, plan context, KPIs, queue tabs | Legacy workspace file, procurement home bridge; not active reset router | Partial (useful primitives, queue model mismatches reset home/plans needs) |
| `approved_demands.get_pp_approved_demands_awaiting_planning` | Approved demand queue list | No active reset consumer | Ready |
| `approved_demands.get_pp_approved_demand_planning_drawer` | Selected demand planning drawer/eligibility | No active reset consumer | Ready |
| `approved_demands.include_pp_demand_in_procurement_plan` | Include demand in plan (write) | No active reset consumer | Ready |
| `planning_inclusion.create_pp_package_from_planning_inclusion` | Create package from inclusion | No active reset consumer | Ready |
| `package_workbench.get_pp_package_workbench` | Canonical package workbench rows/filters/next action | No active reset consumer | Ready |
| `package_list.get_pp_package_list` | Legacy package list by queue_id/plan | Legacy workspace only | Partial/Legacy |
| `package_workspace.get_pp_package_workspace` | Tab-oriented package workspace context | No active reset consumer | Partial (includes evidence/advanced tab payloads; UI contract must constrain defaults) |
| `package_detail.get_pp_package_detail` | Monolithic package detail with handoff summaries | Active router uses for handoff stack | Partial (useful data, but not reset-default presentation model) |
| `planning_journey.get_pp_planning_journey_handoffs` | Journey/handoff references + package_status | Active router (status strip, journey components) | Partial (contextual evidence/technical usage, not default primary workbench content) |
| `released_to_tender.get_pp_released_to_tender` | Released package list + consumption/handoff states | No active reset consumer | Ready |
| `released_to_tender.get_pp_planning_release_package` | Release detail view | No active reset consumer | Partial (detailed technical context; keep contextual) |
| `planning_evidence.get_pp_planning_evidence_timeline` | Evidence timeline + record list | No active reset consumer | Ready |
| `package_readiness.get_pp_package_readiness` + `run_pp_package_readiness_checks` | Readiness tab read/run | No active reset consumer | Ready |
| `package_review.get_pp_package_review` + `record_pp_package_review_decision` | Review tab read/write | No active reset consumer | Ready |
| `package_release.get_pp_package_release` + `mark_pp_package_ready_for_release` + `release_pp_package_to_tender` | Release tab read/write | No active reset consumer | Ready |
| `package_method.get_pp_package_method` + `record_pp_package_method_decision` | Method/governance read/write | No active reset consumer | Ready |
| `package_lines.get_pp_package_line_traceability` | Lines traceability read | No active reset consumer | Ready |
| `package_line_edit.get_pp_package_lines` + line mutation methods | Package line edit/read | Used by Desk package form flow | Ready |

## 3) Active vs canonical API usage

Current active planning router is still wired to older/superseded composition:
- Uses `get_pp_planning_journey_handoffs` and `get_pp_package_detail` to render context strip + handoff cards.
- Does not call canonical reset-oriented APIs like:
  - `get_pp_package_workbench`
  - `get_pp_package_workspace`
  - `get_pp_released_to_tender`
  - `get_pp_planning_evidence_timeline`
  - `get_pp_approved_demands_awaiting_planning`

Conclusion:
- Backend APIs exist for most reset surfaces.
- Main gap is availability of surface-level aggregators (especially Home and Plans) plus UI wiring to canonical APIs.

## 4) Gap register (IDs, impact, downstream dependencies)

| Gap ID | Gap | Impact | Downstream rows |
|---|---|---|---|
| G0-005-G1 | No dedicated Planning Home aggregate API for reset five-queue view model | Home summary and queue contract cannot be met cleanly by active UI | P5C-001..P5C-008 |
| G0-005-G2 | No dedicated Plans workbench aggregate API (queues + plan counts/blockers) | Plans route contract cannot be completed with current minimal plan selector data | P5D-001..P5D-005 |
| G0-005-G3 | Active planning UI not wired to canonical APIs (`package_workbench`, `package_workspace`, approved demands, released, evidence) | Existing backend capabilities are not realized in reset UI | P5C/P5D/P5E/P5F |
| G0-005-G4 | Legacy queue vocabulary from landing/package_list mismatches reset queue contract | Risk of reintroducing superseded queue model in reset screens | P5D-007, P5B-002 |
| G0-005-G5 | `package_workspace` payload exposes evidence/advanced tab data directly | UI must enforce five default tabs and contextual evidence access | P5E-003..P5E-005, P5F |
| G0-005-G6 | Journey/package-detail APIs include technical/handoff-heavy fields | Must remain contextual (Evidence/Technical), not default primary UI blocks | P5F, P5G-007/008 |

## 5) Backend preservation checklist (must remain intact)

Confirmed requirements to preserve (no UI-driven weakening):
- Readiness checks remain server-backed.
- Review and release state gates remain server-enforced.
- Planning inclusion/release/consumption records persist for audit.
- Permission gates remain in PP API policy/gates; supplier confidentiality preserved.
- UI simplification does not replace backend authorization/state validation.

## 6) Downstream implementation ownership notes

Likely implementation touchpoints for closing G0-005 gaps (not part of this gate):
- New/extended aggregators for Planning Home and Plans workbench under `procurement_planning/api/` + services.
- `public/js/pp2_planning_router.js` and new reset workbench modules to consume canonical endpoints.
- Route and shell alignment already tracked in G0-003/G0-004; API wiring to follow in P5C/P5D/P5E/P5F.

## 7) Tracker-format evidence block

Implementation Evidence:
- Code path(s):
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/public/js/pp2_planning_router.js`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/public/js/procurement_planning_workspace.js`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/api/landing.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/api/approved_demands.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/api/package_workbench.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/api/package_workspace.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/api/package_detail.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/api/package_list.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/api/planning_journey.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/api/planning_evidence.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/api/released_to_tender.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/api/package_readiness.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/api/package_review.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/api/package_release.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/api/package_method.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/api/package_lines.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/api/package_line_edit.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/api/planning_inclusion.py`
- Component/template path(s): planning router and legacy workspace consumer inventory recorded above.
- Route path(s): Home, Approved Demands, Plans, Packages, Package Detail, Releases, contextual Evidence.
- API/service path(s), if applicable: listed above per surface mapping.

Test Evidence:
- Test path(s): N/A for this G0 documentation gate.
- Command(s) run: N/A for this G0 documentation gate.
- Result: N/A for this G0 documentation gate.

UI Proof:
- Screenshot(s), if UI row: N/A (API availability gate).
- Route: N/A
- Role: N/A
- Selected queue/item: N/A
- Primary action visible: N/A

Review Notes:
- API availability is largely present for reset surfaces, with explicit aggregate-model gaps for Planning Home and Plans.
- Backend rigor constraints remain intact and are marked as preserve-only.
