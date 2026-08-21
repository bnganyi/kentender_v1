# Departmental Needs MVP 1 rev 1 implementation plan

**Authority:** `NDS-CHG-001 v0.2`, approved 18 August 2026  
**Deployment model:** Clean build only; no Demand migration or compatibility behavior  
**Canonical Desk route:** `/desk/departmental-needs`

## Delivery sequence

1. Establish the four greenfield records and shared-authorization capability contract.
2. Implement scoped, idempotent lifecycle commands and immutable decision evidence.
3. Port NDS-UI-01 as a live Departmental Needs workspace.
4. Replace Planning's Demand allocation boundary with line-level `Plan Need Allocation`.
5. Remove operational Demands code, routes, schemas, roles, fixtures and consumers.
6. Install the exact MOH acceptance fixture and close only criteria backed by passing evidence.

## Locked behavior

- Departmental Need is a non-statutory planning input. It creates no reservation, requisition, tender, procurement classification or method decision.
- State is one of Draft, Submitted, Returned, Accepted for planning, Not taken forward or Withdrawn. Planning usage is derived separately from effective Plan allocations.
- Requesters may withdraw Draft or Returned records. An accepted Need requires a reasoned withdrawal request and departmental-authority approval after every downstream reference is cleared.
- Runtime authority is assignment-, scope-, state- and task-based. Role labels alone grant no operational command.
- Current enabled fiscal years are admitted. Future-year intake remains fail-closed until an intake-window contract is approved.
- NDS-CHG-002 owns the detailed create, edit, view and review screen designs; NDS-UI-01 alone does not close those screens.

## Validation

Focused schema, lifecycle, authorization, allocation, seed and route tests precede affected Core, Strategy, Budget and Planning contracts. UI work requires direct-route, responsive, accessibility and live-projection evidence. The Procurement app asset build must use `./scripts/bench-with-node.sh build --app kentender_procurement`.

The module remains **Partial** while NDS-AC-003 and NDS-CHG-002 interaction screens are outstanding.
