# Procurement Planning — Disposition Matrix

**Document ID:** KENTENDER-ROIDA-05-1.0  
**Date:** 11 August 2026  
**Mode:** Read-only  
**App path:** `kentender_procurement/.../procurement_planning/`  
**Controls:** CMOM §5.2–§5.4, §6.4, §7, §12; SWA §2, §7.3, §8.4  
**Note:** Gate 05 (UI-07/08) recently shipped against Planning REQ packs that conflict with CMOM draft.

| Artifact | Exact location | Current purpose/effect | Evidence | Disposition | Required correction | Dependencies | Migration/seed impact | Tests affected |
|---|---|---|---|---|---|---|---|---|
| Procurement Plan / Version / Item / Item Version | `doctype/procurement_plan*` | Plan + approval boundary + execution unit | JSON | **Keep** | — | Demands | Seed V1/V2 | Gate 01–05 |
| Plan Demand Allocation | `doctype/plan_demand_allocation/` | Demand↔Item amounts Draft/Effective | JSON | **Keep** | — | approve | — | add/approve tests |
| Plan Decision | `doctype/plan_decision/` | Recommend/Return/Approve trail | JSON | **Keep** | — | review/approve | — | decision/approve tests |
| Plan Validation Result | `doctype/plan_validation_result/` | Issue-led validation | validate_plan | **Keep** | — | submit/approve | — | `test_validate_plan` |
| **Departmental Submission** | `doctype/departmental_submission/` | OU contribution Preparing/Submitted | JSON + services | **Remove** | Drop DocType + all writers | submit_for_review gate | Purge rows / rebuild | contribution tests, Gate 05 helpers |
| `submit_departmental_contribution` | `services/submit_departmental_contribution.py` | HoD/Contributor submits contribution | Whitelist API | **Remove** | Delete service | UI-07 | — | `test_submit_departmental_contribution` |
| `get_departmental_contribution` | `services/get_departmental_contribution.py` | PLN-UI-07 DTO | API | **Remove** | Delete | UI-07 | — | layout/contrib |
| PLN-UI-07 contribution drawer | `public/js/planning_ui_fixtures/contribution_drawer.js` + bind | “Submit departmental contribution” | Stitch PLN-UI-07 | **Remove** | Remove fixture/bind/Stitch authority after pack reissue | Builder | — | `planning-contribution-drawer.spec.ts`, `ui-planning-contribution-gate` |
| `prepare_planning_gate05_ui` | `procurement_planning/api.py` | Seeds Ready item for contribution UI | API | **Remove/Correct** | Retarget or delete | Playwright | — | contribution gate |
| Role Planning Contributor + HoD contrib assert | `planning_permissions.py` | Authorises contribution | Code | **Remove** (contrib capability) | Keep HoD only if Demand-side needed | Roles seed | USA cleanup | permission tests |
| `submit_plan_for_review` contribution gate | `services/submit_plan_for_review.py` ~L123 | Blocks unless all OU contributions Submitted | Error text | **Correct** | Remove contribution prerequisite; Ready + Finance/professional rules only | SVC-009 | — | `test_submit_plan_for_review` |
| `record_ou_plan_signoff` / `OU_SIGNOFF` | — | **Not implemented** | Grep: audit docs only | **Confirm absent** | Do not introduce | — | — | — |
| `add_demand_to_plan` | `services/add_demand_to_plan.py` | Default one Demand→one Item; empty aggregation; optional separate Need Items | Code + Gate 04 | **Keep** | — | revision | — | `test_add_demand_to_plan_gate04` |
| `aggregate_plan_allocations` | `services/aggregate_plan_allocations.py` | Explicit Combine | Sets `aggregation_decision=Combine` | **Keep** | — | UI-04 aggregate mode | — | `test_aggregate_plan_allocations` |
| `aggregation_decision` field | Plan Item Version JSON | Options `\nCombine` only | Schema | **Keep** | Never store cosmetic Keep separate | — | — | layout guard forbids Keep separate |
| Plan Item editor | `plan_item_editor.js` + `update_plan_item.py` | Method/schedule/lotting/preference; no Demand reselect; no aggregation radios | Layout guard | **Keep** | — | — | — | editor Playwright |
| Retired statutory fields | Plan Item Version + `patches/clear_retired_statutory_questionnaire.py` | Hidden tombstones; update clears | Tests not writable | **Remove** (finish purge) | Drop schema columns when safe | UI-08 DTO | Patch | update_plan_item |
| `get_plan_review.statutory_coverage` | `services/get_plan_review.py` | Derived preference/reservation coverage rows | UI-08 table | **Correct/Keep** | Keep as named obligation projection; not free-text treatment editor | Preference fields | — | review Playwright |
| Preference / reservation on Item | Plan Item Version + `preference_reservation.py` | Named AGPO-style decision | Code | **Keep** | Distinct from generic statutory questionnaire | — | — | update tests |
| `open_or_create_plan_revision` | `services/open_or_create_plan_revision.py` | Quiet Draft successor | Used by add_demand | **Keep** | — | Approved V1 | SCN-ADD seed | revision tests |
| `validate_plan` | `services/validate_plan.py` | Issue-led Ready | Code | **Keep** | — | submit/approve | — | validate tests |
| `record_plan_decision` / `approve_plan_version` | services | Reviewer/Approver professional path | Gate 05 | **Keep** | After contribution removal, approve path must not require Submission rows | Plan Decision | Helpers stop calling contrib | Gate 05 tests |
| PLN-UI-08 review page | `page/procurement_plan_review/`, `plan_review.js` | Consolidated review/approve | Stitch port | **Keep** (Correct copy) | Remove contribution language if any; rail = professional authority | get_plan_review | — | `planning-plan-review.spec.ts` |
| Workspace/register/builder pages | `page/planning_*`, `procurement_plan_*` | PLN-UI-01…06 | Gates 03–04 | **Keep** | — | — | — | workspace/builder gates |
| Code generators | `_invariants.next_plan_*` | Server codes | Code | **Keep** | — | — | — | — |
| Targeted HoD reapproval | — | **Missing** | Grep no Planning material reapproval | **Correct** (add if CMOM accepted) | Route only changed HoD facts | Demand snapshot | New service | New tests |
| Annual departmental-plan certification | — | Not implemented | CMOM §5.4 optional | **Defer** | Requires PO/legal admission | — | — | — |
| Seed planning | `seeds/kentender_mvp_v1.py`, `scn_pln_add_001.py` | Story + clears Departmental Submission | File | **Correct** | Stop creating contribution records | validate | Rebuild | seed validate |
| Gate helpers `complete_plan_item_for_signoff` | `tests/_gate01_helpers.py` | Calls `submit_departmental_contribution` before approve | Code | **Correct** | Remove contrib from happy path | All Gate 05 tests | — | submit/decision/approve modules |
| Tracker PLN-UI-07/08 Done | `04_…Tracker.md` + GATE_05 | Marks contribution Done | Docs | **Investigate** | Provisional vs CMOM — status cannot stay Done after CMOM accept without Remove wave | PO | Doc | — |

### Planning summary

**Keep** Plan/Version/Item, formation defaults, explicit aggregation, revision successor, validation, professional recommend/approve. **Remove** Departmental Submission / UI-07 / contribution gate / contributor capability. **Correct** submit-for-review, test helpers, seed. **Defer** annual certification. **Gap:** targeted HoD reapproval (Journey D).
