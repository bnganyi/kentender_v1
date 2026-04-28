# STD Engine Works v2 - Existing State Inventory

Date: 2026-04-28  
Scope: `apps/kentender_v1` reconnaissance for `STD-CURSOR-0001` (planning artifact only).

## Objective

Identify current code and architecture points that will be impacted when STD Engine Works v2 is implemented, especially where tender behavior is currently defined, handed off, or missing.

## Key findings (high level)

1. Tendering v1 has been retired from `kentender_procurement`; no active in-tree tendering implementation remains.
2. Procurement has a current handoff surface from planning to downstream tendering via hook payload, but no concrete STD-derived model contract yet.
3. Downstream slices (`bid_submission_opening`, `evaluation_award`, `contract_management`) currently expose minimal placeholders and do not yet consume DSM/DOM/DEM/DCM.
4. No `std_engine_v2_enabled` feature flag exists yet in code.
5. No existing canonical STD Engine domain objects (template family/version/profile/instance/mappings/derived outputs) are currently implemented in `kentender_procurement`.

## Evidence map

### Existing domain and architecture anchors

- `apps/kentender_v1/kentender_procurement/PROCUREMENT_INTERNAL_STRUCTURE.md`
  - Confirms tendering v1 retired and split lifecycle slices.
- `apps/kentender_v1/kentender_procurement/kentender_procurement/hooks.py`
  - Includes planning/workspace assets and fixtures.
  - Defines optional downstream hook `release_procurement_package_to_tender = []`.
- `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/services/tendering_handoff.py`
  - Provides current package-release payload + best-effort hook dispatch.

### Current service/API surfaces

- Procurement planning APIs are active:
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/api/__init__.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/api/workflow.py`
- Downstream APIs are currently skeletal:
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/bid_submission_opening/api/__init__.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/evaluation_award/api/__init__.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/contract_management/api/__init__.py`

## Inventory by required lens (Cursor pack requirement)

### 1) Existing models/DocTypes touching tender flow

- `Procurement Plan`, `Procurement Package`, `Procurement Package Line`, `Procurement Template` in planning slice.
- No active STD Engine Works model set detected (no `std_template_*`, `std_instance`, `derived_*` models).

### 2) Existing services/controllers

- Planning workflow controller/service in `procurement_planning/api/workflow.py`.
- Release hook adapter in `procurement_planning/services/tendering_handoff.py`.
- No implemented services for:
  - generated submission model
  - generated opening model
  - generated evaluation model
  - generated contract carry-forward model

### 3) Existing UI routes/components

- Active planning and procurement workbench assets in:
  - `kentender_procurement/public/js/*workspace*.js`
  - `kentender_procurement/public/css/*workspace*.css`
- No dedicated STD Engine workbench route/shell yet.

### 4) Existing attachment/upload behavior

- No canonical STD source engine exists yet; therefore no governed structured seed-loader path is present.
- Current recon shows no active implementation where DOC1 structured seed is loaded into normalized STD entities.

### 5) Existing publication/readiness logic

- Procurement planning has workflow and status transitions for plan/package.
- No STD readiness run that gates Tender Management publication against bundle + DSM/DOM/DEM/DCM availability.

### 6) Existing supplier submission checklist logic

- No active STD-driven DSM requirement model service found in current procurement slices.

### 7) Existing evaluation criteria logic

- No active DEM service/contract found in downstream `evaluation_award` slice at present.

### 8) Existing opening register logic

- No active DOM service/contract found in downstream `bid_submission_opening` slice at present.

### 9) Existing contract handoff logic

- Current planning release payload (`tendering_handoff.py`) includes package-level payload only.
- No DCM binding contract currently present.

## Refactor targets (phase planning)

1. Introduce STD Engine core + Works plug-in domain model and services without breaking current planning workflows.
2. Replace package-only handoff with structured STD output references for TM and downstream consumers.
3. Build explicit downstream consumption contracts for DSM/DOM/DEM/DCM.
4. Add `std_engine_v2_enabled` transition strategy before runtime refactors.
5. Add governance/auth/audit enforcement before enabling downstream mutations.

## STD-CURSOR-0001 validation checklist

| Required lens | Covered in this document |
|---|---|
| Existing models/DocTypes touching tender flow | Yes (`Inventory by required lens` section 1) |
| Existing services/controllers | Yes (section 2) |
| Existing UI routes/components | Yes (section 3) |
| Existing attachment/upload behavior | Yes (section 4) |
| Existing publication/readiness logic | Yes (section 5) |
| Existing supplier submission checklist logic | Yes (section 6) |
| Existing evaluation criteria logic | Yes (section 7) |
| Existing opening register logic | Yes (section 8) |
| Existing contract handoff logic | Yes (section 9) |
| Explicit refactor targets/gaps | Yes (`Refactor targets`) |

## Out of scope for this artifact

- No runtime code changes.
- No migration execution.
- No service contract implementation.

## Phase 0 closeout record template

Use this template whenever this artifact is revised:

| Field | Value |
|---|---|
| Date | |
| Completed | |
| Not completed | |
| Assumptions | |
| Files changed | |
| Evidence | |
| Residual risks | |

