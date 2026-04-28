# STD Engine Works v2 - Decision Log (Phase 0)

Date: 2026-04-28  
Status: Draft baseline for planning only.

## Decision 001 - Scope guard

- Decision: Limit current execution to Phase 0 planning artifacts only.
- Rationale: User requested plan/background work only.
- Impact: Phase 1+ remains reference roadmap in tracker; no implementation starts.

## Decision 002 - Source-of-truth ownership

- Decision: STD Engine will own tender content/rules generation in future execution; downstream modules consume outputs only.
- Rationale: Defined across docs 1-10 and smoke contract invariants.
- Impact: Future refactors must remove manual downstream rule ownership.

## Decision 003 - Existing baseline

- Decision: Treat current planning release hook payload as temporary compatibility surface.
- Evidence:
  - `kentender_procurement/procurement_planning/services/tendering_handoff.py`
  - `kentender_procurement/hooks.py` (`release_procurement_package_to_tender = []`)
- Impact: Replace in later phases with STD output references.

## Decision 004 - Feature-flag requirement

- Decision: Introduce `std_engine_v2_enabled` as transition gate before runtime refactors.
- Rationale: Cursor pack phase 0 requirement and safe rollout.
- Current state: Flag not yet implemented.
- Impact: Include in planning, test matrix, and rollout controls.

## Decision 005 - Data source policy (DOC1)

- Decision: DOC1 PDF is legal source evidence; runtime source of truth must be structured seed entities, not file uploads.
- Rationale: Seed specification and anti-pattern lockouts.
- Impact: Seed ingestion must enforce source trace and non-invention rules.

## Decision 006 - Testing policy definition

- Decision: Keep TDD/API/Playwright gates in tracker even during planning phase.
- Rationale: Required by workspace quality rules and pack acceptance gates.
- Impact: Future phase completion requires explicit evidence logging in tracker.

## Open decisions to resolve before Phase 1+

1. Exact location/shape of feature flag storage and access pattern in Frappe settings.
2. API contract versioning strategy for TM/downstream consumption (method names and payload versions).
3. Migration sequencing policy for environments with mixed legacy/new tender flows.
4. Evidence export format boundaries (JSON payload bundle only vs packaged export artifacts).

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

