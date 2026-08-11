# Demands — Disposition Matrix

**Document ID:** KENTENDER-ROIDA-04-1.0  
**Date:** 11 August 2026  
**Mode:** Read-only  
**App path:** `kentender_procurement/.../demands/`  
**Controls:** CMOM §5.1, §6.3, §8; SWA §6–§8.3

| Artifact | Exact location | Current purpose/effect | Evidence | Disposition | Required correction | Dependencies | Migration/seed impact | Tests affected |
|---|---|---|---|---|---|---|---|---|
| Demand DocType | `demands/doctype/demand/demand.json` | Business need; PE/OU; status/stage; planning_ready/usage | JSON | **Keep** | — | Planning eligibility | Seed principal 455m | schema + lifecycle |
| Demand Item | `doctype/demand_item/` | Need Items | JSON | **Keep** | — | Plan allocations | — | item tests |
| Demand Decision | `doctype/demand_decision/` | Decision trail incl. Budget Confirmation | JSON | **Keep** | — | Audit | — | review/final tests |
| Demand Funding Allocation | `doctype/demand_funding_allocation/` | BO confirmation + reservation link | `bo_confirmation_*` | **Keep** | Align timing with CMOM if Plan-level Finance required (open) | Budget reservation | Seed | `test_demand_funding.py` |
| Demand Strategy Reference | `doctype/demand_strategy_reference/` | Inherited Strategy lineage | JSON | **Keep** | Requester must not maintain (enrichment roles) | Strategy PVC/targets | — | enrichment tests |
| Demand Value Treatment | `doctype/demand_value_treatment/` | Generic treatment + PVC link | JSON + enrichment APIs | **Remove** | Drop questionnaire; retain named Strategy refs | Strategy | Clear seed treatments | enrichment API / schema |
| Demand `aggregation_treatment` / rationale | `demand.json` fields | Demand-side package formation hint | Fields + enrichment | **Correct/Remove** | Demand may flag similarity only; Planning owns package | Planning aggregation | Clear field usage | enrichment tests |
| Planning Consumption | `doctype/planning_consumption/` | Written on plan approve | approve_plan_version path | **Keep** | — | Planning | — | Gate 05 approve |
| Creation scope resolver | `services/demand_creation_scope.py` | 0/1/multi PE/OU; no Admin invent | Tests deny PE-MOH fallback | **Keep** | — | USA | — | `test_demand_creation_scope` |
| Permissions | `services/demand_permissions.py` | Operational roles; Admin alone blocked on decisions | Code | **Keep** | — | Shared | — | role tests |
| Lifecycle: create/submit/HoD approve/return | `services/demand_lifecycle.py` | Normal Demand journey | Stages | **Keep** | — | — | — | review gates |
| Lifecycle: Budget Confirmation | same (`confirm_*` ~1078+) | Mandatory BO funding sign-off | Decisions + allocations | **Keep** | Confirm whether CMOM also needs post-plan Finance | Budget | — | budget-confirm specs |
| Material funding change → invalidate BO | `apply_material_funding_change`, `_invalidate_bo_signoff_*` | Reconfirm funding | DIA-FR-093/087 comments | **Keep** (Finance) | Distinct from HoD material reapproval (gap in Planning) | Budget | — | `test_ac019_material_change_invalidates_bo_signoff` |
| Workspace / form / review pages | Demands pages + `demands_live_bind.js` | DEM-UI surfaces | Tracker Closed Done | **Keep** | Ensure unauthorised cannot open approval chrome | Auth | — | `ui-demands-*-gate` |
| Prepare factories | `demands/api.py` `prepare_*_ui*` | Playwright fixtures; default PE-MOH | Admin-only | **Keep** (test) | Not runtime ownership | — | — | smoke specs |
| Seed | `demands/seeds/kentender_mvp_v1.py` | Principal/returned/story; may plant treatments | File | **Correct** | Strip value-treatment / aggregation packaging | validate.py | Rebuild | seed validate |
| Tracker status | `docs/mvp-1/03_demands/04_…Tracker.md` Closed Done | Pack treated complete | Tracker | **Investigate** | SWA §13 — packs provisional until reconciled | PO acceptance | Doc only | — |

### Demands summary

Preserve Requester capture, explicit PE/OU, HoD approval, BO confirmation, Strategy references, Planning Consumption. **Remove** Demand Value Treatment questionnaire and Demand-owned aggregation packaging. Open decision: whether Finance on Demand alone satisfies CMOM sequence “after planned requirement.”
