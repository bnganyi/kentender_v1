# UI Smoke Tests

Playwright smoke tests live under `tests/ui/smoke`.

## Run

- `make -C apps/kentender_v1 ui-smoke`
- or `cd apps/kentender_v1 && npm run test:ui:smoke`

## Environment

Copy `apps/kentender_v1/.env.ui.example` to `apps/kentender_v1/.env.ui` and set credentials that exist on the target site.

**Seed alignment (KenTender v1):** After `bench --site <site> execute kentender_core.seeds.seed_core_minimal.run` (or any full reseed that includes core minimal), business users and their password are defined in `kentender_core/seeds/constants.py` — `SEED_USERS` (emails such as `strategy.manager@moh.test`) and `TEST_PASSWORD` (default `Test@123`). Set `UI_STRATEGY_*`, `UI_PLANNING_*`, `UI_REQUISITIONER_*`, `UI_PLANNER_*`, `UI_HOD_*`, `UI_FINANCE_*` to those values unless you maintain a custom site. **`UI_ADMIN_*` is not in seeds**; it must match the Frappe Administrator on that site.

**Auditor:** `SEED_USERS` does not include an Auditor login yet. `dia-auditor-readonly.spec.ts` skips unless `UI_AUDITOR_USER` is set; add `UI_AUDITOR_USER` / `UI_AUDITOR_PASSWORD` only after a matching Desk user exists (see `.env.ui.example` for the usual pattern).

Required variables used by smoke helpers:

- `UI_BASE_URL`
- `UI_ADMIN_USER`, `UI_ADMIN_PASSWORD`
- `UI_REQUISITIONER_USER`, `UI_REQUISITIONER_PASSWORD` (DIA suites)
- `UI_PLANNER_USER`, `UI_PLANNER_PASSWORD` (PP role-aware suites)
- `UI_PLANNING_USER`, `UI_PLANNING_PASSWORD`
- `UI_AUDITOR_USER`, `UI_AUDITOR_PASSWORD`
- `UI_HOD_USER`, `UI_HOD_PASSWORD`
- `UI_FINANCE_USER`, `UI_FINANCE_PASSWORD`

## Fixtures for Procurement G3

`tests/ui/smoke/procurement/procurement-g3.spec.ts` expects:

- Procurement module Desktop Icon is present and clickable.
- Procurement sidebar contains:
  - `Procurement Home`
  - `Demand Intake & Approval`
  - `Procurement Planning`
  - `Settings` section (with links such as `Procurement Templates`).
- DIA shell exposes `dia-landing-page` and `dia-page-title`.
- Procurement Planning shell exposes `pp-page-title`, `pp-current-plan-bar`, `pp-control-bar`.
- Procurement Home shell exposes `ph-landing-page` and quick-link buttons for DIA and Planning.

Seed baseline:

- Run PP/DIA seed flows from tracker (`F1`, with DIA prerequisites + budget deps) before UI smoke so queues and list/detail regions are populated.
