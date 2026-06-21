# G0-007 UX Reset Reviewer Acceptance

Date: 2026-05-26

## Decision Header

- Reviewer: User
- Reviewer role: Product reviewer
- Decision: Accepted
- Conditions (if any): Proceed with documented G0 dependency notes from G0-003, G0-005, and G0-006.
- Authorization for next phase: P5A may begin

## 1) Controlling Document Confirmation (mandatory)

Reviewer confirmation required:

- For Procurement Planning P5 UI work, the controlling pack is:
  1. `reset/2.procurement_planning_v_2_p_5_ux_reset_implementation_tracker.md`
  2. `reset/3. procurement_planning_v_2_cursor_implementation_pack_ux_reset_addendum.md`
  3. `reset/4.procurement_planning_v_2_ux_reset_wireframe_pack.md`
  4. Backend/domain/governance/seed artifacts remain authoritative for server controls.
- Earlier pre-reset P5 UI directions are superseded where they conflict with this reset pack.

## 2) Supersession Statement (old P5 direction)

The reviewer confirms ordinary default Planning UI must not continue with superseded patterns such as:

- persistent Planning Evidence submenu as ordinary Planning nav
- handoff-card stacks as primary default content for Home/Packages
- implementation-stage stub/deferred copy in product UI
- Evidence/Advanced as default package detail tabs

Those remain contextual (View Evidence, Technical Details, Audit/Journey contexts) only.

## 3) Product Rule Acceptance

Reviewer confirms the following reset product rule is accepted:

- workbench-first, evidence-on-demand
- queue/list + selected summary + blocker + one primary action
- technical details hidden by default and permission-gated
- backend readiness/review/release/permission/audit rigor is preserved

## 4) G0 Evidence Rollup (G0-001..G0-006)

| Gate | Evidence artifact | Reviewer check |
|---|---|---|
| G0-001 | `G0-001_current_ui_inventory_evidence.md` | Reviewed |
| G0-002 | `G0-002_delete_refactor_list.md` | Reviewed |
| G0-003 | `G0-003_route_plan_confirmation.md` | Reviewed |
| G0-004 | `G0-004_main_procurement_shell_confirmation.md` | Reviewed |
| G0-005 | `G0-005_data_api_availability_evidence.md` | Reviewed |
| G0-006 | `G0-006_seed_data_check_evidence.md` | Reviewed |

## 5) Accepted Dependencies / Conditions

Use this section to record accepted pre-implementation dependencies:

- Route gaps tracked for implementation:
  - `/plans` route implementation
  - `/packages/<package_code>` path implementation
  - persistent `/evidence` de-persisting from ordinary nav
- API/data dependencies tracked for implementation:
  - Planning Home aggregate model
  - Plans workbench aggregate model
- Seed dependencies tracked for implementation/testing:
  - canonical PP2 planning seed validation
  - checkpoint strategy where single snapshot does not populate all queue examples

## 6) No-Go Acknowledgement

Reviewer acknowledges implementation must be rejected if no-go categories recur in ordinary default views:

- handoff/evidence-heavy default screens
- persistent evidence route/menu in ordinary planning IA
- technical leakage before explicit expansion
- multiple primary actions
- UI behavior that weakens backend control enforcement

## 7) Authorization

- G0 acceptance decision:
  - [x] Accepted
  - [ ] Rework Required
- If Accepted, authorization:
  - [x] Proceed to `P5A — Shell and Navigation Reset`
  - [x] Proceed with listed conditions

## 8) Tracker Review Notes Payload

Copy into tracker row `G0-007` review notes after human decision:

```text
Reviewer: User
Decision: Accepted
Follow-up: Begin P5A using reset tracker and preserve backend control rigor.
Conditions: Track and resolve known route/API/seed dependency gaps documented in G0-003, G0-005, and G0-006 during P5 phases.
Authorization: P5A may begin.
```
