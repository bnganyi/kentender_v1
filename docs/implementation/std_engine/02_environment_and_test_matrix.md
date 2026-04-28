# STD Engine Works v2 - Environment and Test Matrix (Phase 0)

Date: 2026-04-28  
Status: Planning baseline (no execution yet).

## Environment assumptions

| Item | Value / Constraint |
|---|---|
| Workspace root | `/home/midasuser/frappe-bench` |
| App tree in scope | `apps/kentender_v1` |
| Primary procurement app | `apps/kentender_v1/kentender_procurement` |
| Source PDF | `apps/kentender_v1/docs/prompts/6.a. STD/DOC 1. STD FOR WORKS-BUILDING AND ASSOCIATED CIVIL ENGINEERING WORKS Rev April 2022.pdf` |
| Node/bench build rule | Use `./scripts/bench-with-node.sh` only for asset builds |
| UI test framework | Playwright in `apps/kentender_v1/tests/ui` |

## Planned validation matrix (for future execution)

| Phase band | Validation expectation | Evidence location |
|---|---|---|
| Phase 1-5 | Unit/service + integration tests | Tracker progress log + test output refs |
| Phase 6-8 | Generation/readiness/addendum contract tests | Tracker progress log |
| Phase 9-11 | Cross-module integration + UI behavioral checks | Tracker progress log + Playwright refs |
| Phase 12 | Full smoke contract automation | Tracker + smoke suite output |
| Phase 13 | Hardening and evidence export validation | Tracker + artifact references |

## Command matrix (planning reference)

These are reference commands for future execution phases:

- Python tests (app-level):
  - `bench --site <site> run-tests --app kentender_procurement`
- Targeted tests:
  - `bench --site <site> run-tests --app kentender_procurement --module <module_path>`
- Asset build after desk JS/CSS changes:
  - `./scripts/bench-with-node.sh build --app kentender_procurement`
  - `./scripts/bench-with-node.sh build --app kentender_core` (if shared UI assets touched)
- Cache reset (as needed):
  - `bench --site <site> clear-cache`
- Playwright (from `apps/kentender_v1`):
  - `npx playwright install chromium`
  - `npm run test:ui:smoke`

## Playwright prerequisites (planning checklist)

- [ ] Reachable site base URL
- [ ] Role accounts and credentials seeded
- [ ] Browser binaries available in current runner context
- [ ] Stable test IDs present for affected workbench surfaces
- [ ] Environment variables aligned with `playwright.config.ts`

## Risk notes

1. Mixed legacy/new tender behavior can produce false positives in integration tests without explicit flag gating.
2. UI smoke stability depends on deterministic seed data and role setup.
3. Generation/readiness tests need deterministic identifiers and source hash policy from seed package.

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

