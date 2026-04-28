# STD Engine Works v2 - Feature Flag Transition Strategy

Date: 2026-04-28  
Flag: `std_engine_v2_enabled`  
Status: Planning definition only (no runtime implementation in Phase 0).

## Objective

Define a safe transition path from current procurement handoff behavior to STD Engine v2-owned outputs.

## Flag behavior contract

### When `std_engine_v2_enabled = false`

- Existing planning release/handoff behavior remains active.
- Legacy/manual downstream rule surfaces may remain available for compatibility.
- New STD Engine v2 contracts are not mandatory blockers.

### When `std_engine_v2_enabled = true`

- Tender Management must require STD-derived artifacts for progression.
- Downstream modules must consume generated models (DSM/DOM/DEM/DCM) and reject manual rule injection.
- Publication/readiness flow must enforce generated-output prerequisites.

## Transition stages

1. **Preparation stage**
   - Introduce flag definition and config surface.
   - Add compatibility instrumentation/audit logs to identify legacy path usage.
2. **Dual-readiness stage**
   - Keep legacy behavior available but start validating STD contracts in parallel (non-blocking).
3. **Enforcement stage**
   - Enable strict blocking on missing STD outputs for scoped tenders/workspaces.
4. **Legacy lockout stage**
   - Disable manual downstream rule ownership paths for in-scope tenders.

## Guardrails

- No direct switch to strict mode without smoke-contract readiness in target environment.
- Maintain explicit rollback path to `false` until Phase 12 evidence is stable.
- All flag state changes must be auditable.
- Enablement should support controlled scope (site/environment/tenant/role-based rollout policy).

## Required evidence before enablement by default

- Seed/load invariants validated.
- Governance/authorization/audit checks validated.
- End-to-end generation/readiness/addendum checks validated.
- Cross-module enforcement checks validated.
- UI and API smoke checks validated.

## STD-CURSOR-0002 planning completeness check

| Requirement | Coverage |
|---|---|
| Explicit `false` behavior | Defined in `When std_engine_v2_enabled = false` |
| Explicit `true` behavior | Defined in `When std_engine_v2_enabled = true` |
| Staged rollout path | Defined in `Transition stages` (Preparation -> Dual-readiness -> Enforcement -> Legacy lockout) |
| Safety guardrails and rollback posture | Defined in `Guardrails` |
| Evidence gate before default enablement | Defined in `Required evidence before enablement by default` |
| Unresolved design decisions captured | Defined in `Open implementation decisions` |

## Open implementation decisions (for Phase 1+)

1. Storage location for flag (site config vs singleton DocType vs feature management service).
2. Per-tenant/per-site rollout granularity.
3. Exact blocking/error codes surfaced to TM and downstream UIs.
4. Migration policy for in-flight tenders created before flag enablement.

## Phase 0 closeout record template

| Field | Value |
|---|---|
| Date | |
| Completed | |
| Not completed | |
| Assumptions | |
| Files changed | |
| Evidence | |
| Residual risks | |

