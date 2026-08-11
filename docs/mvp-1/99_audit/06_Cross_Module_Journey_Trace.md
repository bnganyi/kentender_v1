# Cross-Module Journey Trace (A–F)

**Document ID:** KENTENDER-ROIDA-06-1.0  
**Date:** 11 August 2026  
**Mode:** Read-only — traces are from code paths, not live DB mutation

---

## Journey A — Normal path

**Intended (CMOM §4):** Requester → HoD Demand approve → Planner Plan Item → Finance funding → Head of Procurement review/approve → Tender from Plan Item.

| Step | Actor | Code path | Records / state | Capability check | Screen |
|---|---|---|---|---|---|
| 1 Create/submit Demand | Requester | `demands/services/demand_lifecycle.py` create/submit; `demand_creation_scope.resolve_demand_creation_scope` | Demand Draft→awaiting; Demand Items; generated `demand_code` | Requester + USA PE/OU | Demand form / workspace |
| 2 HoD approve/return | Business Approver / HoD | lifecycle approve/return; `Demand Decision` | Demand Approved or Returned | Business Approver + scope | DEM review |
| 3a Finance BO confirm | Budget Officer | lifecycle Budget Confirmation (~L1078+); `Demand Funding Allocation.bo_confirmation_*`; may `reserve_funding` | Confirmed allocations; Funding Reservation | Budget Officer | DEM-UI-06 |
| 3b Enrichment / strategy refs | Procurement roles | enrichment APIs; `Demand Strategy Reference`; **may write Demand Value Treatment** | Treatments (prohibited questionnaire) | Enrichment roles | DEM-UI-05 |
| 4 Add to Plan | Planner | `add_demand_to_plan.py` → optional `open_or_create_plan_revision`; Plan Item + Draft allocations | One Item default; empty `aggregation_decision` | Procurement Planner + scope | PLN-UI-04 dialog → UI-06 editor |
| 5 Complete Plan Item | Planner | `update_plan_item.py`; `validate_plan` | Method/schedule/lotting/preference | Planner | PLN-UI-06 / builder UI-05 |
| 6 **Contribution (current)** | HoD / Contributor | `submit_departmental_contribution.py` | **Departmental Submission** Submitted | Contrib roles | **PLN-UI-07** |
| 7 Submit for review | Planner | `submit_plan_for_review.py` | Version → In review; **requires contributions Submitted** | Planner | Builder CTA |
| 8 Recommend/return | Planning Reviewer | `record_plan_decision.py` | Plan Decision; Return→Returned | Reviewer | PLN-UI-08 |
| 9 Approve | Designated Approver / AO / Planning Authority | `approve_plan_version.py` | Approved; Effective allocations; Planning Consumption; Decision | Approver roles | PLN-UI-08 |
| 10 Tender | Tender Initiator | Handoff services **partial / later gates** | Planning Handoff Snapshot (schema exists) | Tender Initiator | Not fully Journey-green |

**Disposition conflicts on Journey A:** Steps 6–7 (contribution) contradict CMOM §5.2. Step 3a Finance is **before** Plan Item completion, while CMOM lists Finance after planning proposal — **open decision** (`08`). Step 10 incomplete.

---

## Journey B — Add to Approved Plan

| Check | Code evidence | Result |
|---|---|---|
| Opens/reuses Draft successor | `add_demand_to_plan` → `open_or_create_plan_revision` when no open Draft | **Aligned** |
| Approved V1 remains | Revision creates successor; approve replaces later | **Aligned** (Gate 01/05 Effective-once) |
| No second Demand selection in editor | `plan_item_editor.js` / `get_plan_item_editor` — source read-only; layout guard | **Aligned** |
| No default aggregation | `aggregation_decision` empty on single add | **Aligned** |
| No routine second HoD | **Still required** via contribution before submit_for_review | **Conflict** with CMOM |
| Tender handoffs stay on Approved version | Handoff snapshot DocType; take-up service later | **Investigate** completeness |

---

## Journey C — Explicit aggregation

| Check | Code evidence | Result |
|---|---|---|
| Aggregation only when adding another Demand | `aggregate_plan_allocations` + UI-04 aggregate mode | **Aligned** |
| Combine stores decision | `aggregation_decision="Combine"` | **Aligned** |
| Separate creates real Items | `formation_mode=separate_per_need_item` creates N Items; Keep separate **removed** from editor | **Aligned** for Need-Item split; multi-Demand “separate” = do not call aggregate / add as new Item | **Keep** |
| Cosmetic Keep separate | Layout/tests forbid string | **Absent** (good) |

---

## Journey D — Material change → HoD reapproval

| Check | Evidence | Result |
|---|---|---|
| Planning changes owning OU / scope / material value | No Planning service found for targeted HoD reapproval | **Gap** |
| Demand material funding change | `_invalidate_bo_signoff_*` / `apply_material_funding_change` → Budget Confirmation | **BO reconfirm only**, not HoD |
| CMOM §5.3 | Required for HoD-owned facts | **Record gap** — do not invent universal reapproval |

---

## Journey E — Unauthorised task form

| Surface | Record view | Task action | API | Notes |
|---|---|---|---|---|
| Demand review/approve | Scoped list/detail | `allowed_actions` omit | Stage APIs throw | Stronger pattern |
| Budget activate | Overview | `can_activate` | activate throws | Admin inflated roles weaken test |
| Plan review PLN-UI-08 | Page loads with plan id if scoped | `rail_mode=readonly`; `can_*` false | decision/approve PermissionError | **Investigate** whether page shell should 403 vs readonly |
| Contribution drawer | Builder | Action gated | submit throws | Prohibited feature anyway |

---

## Journey F — Multiple scopes

| Module | Behaviour | Evidence |
|---|---|---|
| Demand create | multi → deliberate PE then OU; zero blocks | `demand_creation_scope.py` |
| Plan create | multi → deliberate PE; Admin alone blocked | `resolve_pe_for_create` |
| Budget | multi → **sorted first** or User Permission default; Admin → PE-MOH | `entity_for_user` |
| Strategy list | PE may be unset → unfiltered list | `list_strategy_plans` |

**Silent fallbacks to Correct:** Budget + Home + Strategy list weakness.

---

## Journey disposition map

| Journey | Overall | Primary Correct/Remove |
|---|---|---|
| A | Partial — contribution + Finance timing + Tender | Remove contrib; decide Finance position; finish handoff |
| B | Mostly Keep; contrib conflict | Remove contrib gate |
| C | Keep | — |
| D | Gap | Targeted HoD reapproval if CMOM accepted |
| E | Partial | Harden route denial; fix Admin inflation |
| F | Mixed | Fix Budget/Strategy/Home |
