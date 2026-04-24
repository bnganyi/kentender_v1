# DIA MVP Closeout — Sticky Lessons For Procurement Planning

Status: DIA MVP successfully closed.

## What Worked Best (Keep)

- Role-first workspace UX: queue-driven landing pages reduced clicks and confusion.
- Contract-first APIs: explicit `ok/error_code/message/data` envelopes made UI behavior predictable.
- Permission-aware data access: `frappe.get_list` for counts/sums/lists avoided KPI/list mismatches.
- Progressive hardening with smoke tests: each workflow scenario moved from `fixme` to runnable test.
- Strong UI guardrails: hidden/derived fields, strict validation, and workflow-locked edit behavior.
- Fast feedback loop: user screenshots + targeted patches resolved UX regressions quickly.

## Production Patterns To Reuse In Procurement Planning

- One canonical entry point: keep users inside module workbench; avoid native-list escape paths.
- Queue semantics before UI polish: define role queues, defaults, and empty captions first.
- “Discoverability first” defaults: ensure newly created records are visible in default queues.
- Display contract for references: store IDs, always show `Name (Code)`, never raw DB IDs.
- Sticky primary actions: put high-frequency actions at top and keep them visible on scroll.
- Non-breaking permissions UX: show blocked states with actionable hints, not hard crashes.

## Testing Strategy To Carry Forward

- Add one smoke test per critical business scenario (submit, approve, return, reject, exception paths).
- Add one cross-role permission test for each module role (read/write boundaries).
- Add list/filter contract tests for queue resolver logic (tab + queue + refine + search).
- Add migration/seed tests for legacy-data cleanup and display backfills.

## Data + Migration Lessons

- Treat legacy hash-like names as technical debt: backfill display fields and rename where needed.
- Ship idempotent patches only; safe reruns are mandatory.
- Include workspace/sidebar fixtures and module-def sync in migrations, not manual setup.

## UX Lessons

- Optional fields must be optional in both DocType and client validation.
- Auto-fill hidden required audit fields before save.
- Keep contextual navigation stable across form/list/workspace transitions.
- Reduce vertical noise in sticky bars; buttons first, explanatory text optional.

## Delivery Process Lessons

- Small, reversible patches beat large rewrites.
- Verify after every substantive change (lint/tests/migrate).
- Use screenshot-driven bug triage with precise issue-to-patch mapping.
- Keep a living tracker of “done / risky / pending” to avoid blind spots.

## Procurement Planning Kickoff Checklist (Sticky)

- Confirm module entry route and sidebar behavior (no native-list drift).
- Define role queues, defaults, and visibility rules before implementation.
- Define reference-display contract (`Name (Code)`) for all linked masters.
- Define API response envelope and error taxonomy before frontend wiring.
- Write initial smoke test matrix and required seed data before feature expansion.
- Add first migration patch skeleton (module defs, sidebars, backfills) early.
