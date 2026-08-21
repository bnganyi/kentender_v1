# Audit reproducibility appendix

**Parent:** KenTender Cursor Read-Only Implementation Disposition Audit Prompt v1.0  
**Completed:** 11 August 2026

## Files created (analysis only)

1. `apps/kentender_v1/docs/mvp-1/99_audit/00_Implementation_Disposition_Executive_Summary.md`
2. `…/01_Shared_Scope_and_Authorisation_Inventory.md`
3. `…/02_Strategy_Disposition_Matrix.md`
4. `…/03_Budget_and_Funding_Disposition_Matrix.md`
5. `…/04_Demands_Disposition_Matrix.md`
6. `…/05_Procurement_Planning_Disposition_Matrix.md`
7. `…/06_Cross_Module_Journey_Trace.md`
8. `…/07_Seed_and_Test_Consistency_Audit.md`
9. `…/08_Open_Decisions_and_Evidence_Gaps.md`
10. `…/09_Audit_Reproducibility_Appendix.md` (this file)

## Controlling documents inspected

- `KenTender_Cursor_Read_Only_Implementation_Disposition_Audit_Prompt_v1.0.md`
- `KenTender_MVP_Cross_Module_Operating_Model_v1.0.md`
- `KenTender_MVP_Semantic_and_Workflow_Assurance_Audit_v1.1.md`
- `docs/mvp-1/00_common/00_KenTender_Procuring_Entity_and_Organisation_Scope_Model.md` (referenced)
- `docs/mvp-1/00_common/KenTender_MVP_Canonical_Demo_Data_Contract_v2.5.md` (referenced via seed/validate)
- Module trackers/packs under `docs/mvp-1/01_strategy`, `02_budget`, `03_demands`, `04_planning` (as cited)

## Representative implementation paths inspected

- `kentender_core/services/org_scope_access.py`, USA/PE/OU DocTypes, `seeds/kentender_mvp_v1/*`
- `kentender_budget/services/budget_permissions.py`, budget DocTypes, `budget_reference.py`, seeds
- `kentender_strategy` DocTypes (PVC), `strategy_reference.py`, `strategy_api.py`, seeds
- `kentender_procurement/demands` DocTypes, `demand_lifecycle.py`, `demand_creation_scope.py`, seeds
- `kentender_procurement/procurement_planning` DocTypes (incl. `departmental_submission`), services (`submit_departmental_contribution`, `submit_plan_for_review`, `add_demand_to_plan`, `aggregate_plan_allocations`, `approve_plan_version`, `get_plan_review`, …), fixtures UI-07/08, tests, Makefile gates

## Commands run (non-mutating)

```text
git rev-parse / git status -sb   # observed: no commits on main; dirty untracked tree
ls / readlink apps/kentender_*
cat sites/apps.txt ; common_site_config.json keys
grep / ripgrep across apps/kentender_v1 for mandatory semantic terms
read of __version__ files (Frappe 16.12.0, ERPNext 16.10.1)
```

**Not run:** migrate, seed execute, clear-cache, bench build, DB writes, fixture mutation.

## Mandatory semantic search — outcome summary

| Term / concept | Runtime presence |
|---|---|
| Departmental Submission / submit_departmental_contribution / contribution UI-07 | **Present** — Remove |
| Organisation Unit Planning Contributor / OU_SIGNOFF / record_ou_plan_signoff | Contributor role **present**; OU_SIGNOFF / record_ou_plan_signoff **absent** |
| Statutory / planned_treatment / value_treatment_note | Retired fields + derived UI-08 coverage |
| Budget/Demand Value Treatment | **Present** — Remove |
| Plan Value Commitment | **Present** (name Correct → Strategy Value Commitment) |
| aggregation_decision / Keep separate | Combine only; Keep separate removed |
| PE-MOH / first USA / Admin fallback | Budget/Home **present**; Demand/Plan create **blocked** |
| Free-text Budget context on Plan | Not found as Plan header field in this pass |
| User-maintained codes | Runtime generators Keep; seeds plant stable IDs |

## Completion gate checklist

- [x] Four modules + shared foundations inventoried  
- [x] Artifacts dispositioned or listed as Investigate/open  
- [x] Journeys A–F traced  
- [x] Prohibited concepts searched repo-wide  
- [x] Seed/tests reconciled to same story  
- [x] No application/schema/seed/test **implementation** files modified (analysis docs only under `99_audit/`)
