# G0-006 Seed Data Check Evidence

Date: 2026-05-26  
Source inputs: `G0-001_current_ui_inventory_evidence.md`, `G0-002_delete_refactor_list.md`, `G0-003_route_plan_confirmation.md`, `G0-004_main_procurement_shell_confirmation.md`, `G0-005_data_api_availability_evidence.md`

## 1) Seed gate decision summary

Decision: **Dependency note submitted (partial).**

- Canonical PP2 planning seed loader/validator paths are identified and documented.
- Required WORKS business codes and checkpoint coverage are mapped per reset surface.
- Existing P3/P4 automated evidence confirms planning seed/test readiness patterns.
- This gate documents dependency confirmation without re-running seed mutation commands in this step.

## 2) Canonical seed loaders and validators (Planning vs Lifecycle)

### Canonical PP2 Planning seed path (for reset Planning UI)

- Loader:
  - `kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master.seed_procurement_planning_works_master`
- Validator:
  - `kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master.validate_procurement_planning_works_master_seed`
- Compatibility shim:
  - `kentender_procurement.procurement_planning.seeds.works_master_planning_seed.upsert_works_master_planning`
  - Delegates to PP2 canonical loader at `RELEASED_TO_TENDER` checkpoint.

### Lifecycle seed path (supplementary, not replacement for planning records)

- Loader:
  - `kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master.load_procurement_lifecycle_works_master`
- Validator:
  - `kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master.validate_procurement_lifecycle_works_master_seed`

Reset interpretation:
- PP2 Planning surfaces require **planning seed records** (plan/package/release/consumption/audit), so lifecycle-only validation is insufficient for G0-006 on its own.

## 3) Command reference for this bench/site

Canonical planning seed commands (site-scoped to this bench’s primary site):

```bash
bench --site kentender.midas.com execute kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master.seed_procurement_planning_works_master --kwargs '{"checkpoint":"CONSUMED_BY_TENDER","force_reset":true}'

bench --site kentender.midas.com execute kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master.validate_procurement_planning_works_master_seed --kwargs '{"checkpoint":"CONSUMED_BY_TENDER"}'
```

Lifecycle commands from reset tracker §13.6 (supplementary cross-module dependency):

```bash
bench --site kentender.midas.com execute kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master.load_procurement_lifecycle_works_master --kwargs '{"reset":true,"checkpoint":"TENDER_PUBLISHED"}'

bench --site kentender.midas.com execute kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master.validate_procurement_lifecycle_works_master_seed --kwargs '{"checkpoint":"TENDER_PUBLISHED"}'
```

## 4) Business code inventory (required by reset flows)

| Domain | Required codes/examples | Status source |
|---|---|---|
| Demand/Budget/Journey | `DEM-MOH-2026-001`, `BUD-MOH-INFRA-2026-001`, `JRN-MOH-2026-001` | Covered by prior PP2 seed/test stacks and upstream prerequisites |
| Plan/Package | `PLAN-MOH-2026`, `PKG-MOH-2026-001`, `PKGLINE-MOH-2026-001-001` | Covered in PP2 planning master seed path |
| Tender linkage | `TND-MOH-2026-001` | Required for release/consumption and released views |
| Handoff/audit records | `PLANINCL-MOH-2026-001`, `PKGREL-MOH-2026-001`, `PKGCONSUME-MOH-2026-001` | Must exist server-side; hidden in default UI unless explicit evidence/technical expansion |

## 5) Surface-to-checkpoint coverage matrix

| Surface | Required seed/state | Preferred checkpoint evidence | Coverage note |
|---|---|---|---|
| Planning Home | Multi-queue business summary (needs planning/review/ready/released/blocked) | Mixed checkpoint or tailored fixture set | Single consumed snapshot can under-populate some queues |
| Approved Demands | Ready-to-plan demand state | `APPROVED_DEMAND_READY` (or equivalent pre-inclusion state) | `CONSUMED_BY_TENDER` can remove demand from awaiting-planning queue |
| Plans | Active plan with counts | `INCLUDED_IN_PLAN` and above | Plan appears in planning seed hierarchy |
| Packages | Workbench rows with package status/action | `PACKAGE_DRAFT` to `CONSUMED_BY_TENDER` | `PKG-MOH-2026-001` proven in prior UI evidence |
| Package Detail | Header + tab data across readiness/review/release | `READY_FOR_RELEASE` to `CONSUMED_BY_TENDER` | Tab APIs present (see G0-005) |
| Released to Tender | Released/consumed package with tender link | `RELEASED_TO_TENDER` or `CONSUMED_BY_TENDER` | Requires release + consumption records |
| Evidence Drawer | Timeline + technical expansion references | `INCLUDED_IN_PLAN` and above | Requires handoff/audit records retained |

## 6) Dependency/gap register

| Gap ID | Gap | Impacted rows |
|---|---|---|
| G0-006-G1 | Reset tracker §13.6 lists lifecycle seed validation only; planning UI surfaces also require PP2 planning seed validation | G0-006 quality of proof, P5C/P5D/P5E/P5F |
| G0-006-G2 | Single `CONSUMED_BY_TENDER` seed state may not populate all Planning Home queues simultaneously | P5C queue acceptance and screenshots |
| G0-006-G3 | Approved Demands ready-to-plan scenarios may need lower checkpoint or controlled reset sequence | P5C-009..P5C-015 |
| G0-006-G4 | UI smoke specs assume seeded `PKG-MOH-2026-001` but do not enforce seed precondition in each run | P5H stability |

## 7) Existing evidence anchors used for this gate

- PP2 seed API entry points:
  - `procurement_planning/seeds/seed_procurement_planning_works_master.py`
  - `procurement_planning/seeds/works_master_planning_seed.py`
- Lifecycle seed API entry points:
  - `procurement_lifecycle/seeds/seed_procurement_lifecycle_works_master.py`
- Previously submitted gate artifacts:
  - G0-001 through G0-005 reset evidence documents.
- Existing planning test inventory references:
  - PP2 planning seed test module family (`test_pp2_planning_works_master_seed_p3_*`)
  - PP2 API validation test module family (`test_pp2_*_p4_*`)

## 8) Tracker-format evidence block

Implementation Evidence:
- Code path(s):
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/seeds/seed_procurement_planning_works_master.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/seeds/works_master_planning_seed.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_lifecycle/seeds/seed_procurement_lifecycle_works_master.py`
- Component/template path(s): N/A (seed data gate).
- Route path(s): Planning reset routes depend on this seed state matrix.
- API/service path(s), if applicable: planning/lifecycle seed load + validate entry points listed above.

Test Evidence:
- Test path(s): Existing P3/P4 seed/API test families documented as evidence anchors.
- Command(s) run: N/A in this documentation gate submission.
- Result: Dependency note submitted with canonical command references and checkpoint matrix.

UI Proof:
- Screenshot(s), if UI row: N/A (seed data gate).
- Route: N/A
- Role: N/A
- Selected queue/item: N/A
- Primary action visible: N/A

Review Notes:
- WORKS seed dependency is confirmed with explicit canonical PP2 planning seed path and checkpoint coverage guidance.
- Lifecycle seed command references are retained as supplementary, not a replacement for planning seed proof.
