# CLAUDE.md

This is the operating entry point for Claude Code in the KenTender repository. Read [AGENTS.md](AGENTS.md) before editing. `AGENTS.md` contains the stable engineering rules; this file is only the short task loop, repository map, and command card.

## Start every task this way

1. Read the user's request, the named implementation pack, and the closest applicable `AGENTS.md` or `AGENTS.override.md`.
2. Inspect `git status`, the target files, their callers, and their focused tests. Preserve existing user changes.
3. Classify the task before acting:
   - review, explanation, or diagnosis: inspect and report; do not implement;
   - change or build: implement the smallest complete change and validate it.
4. Identify the owning app, affected public contracts, and acceptance criteria. Do not load unrelated architecture or archived documents.
5. If applicable instructions conflict materially, stop and state the exact conflict instead of guessing.

## Default development loop

Use test-driven development for behaviour changes and bug fixes:

1. **Red:** add or identify the smallest test that reproduces the requirement or defect; run only that test and confirm the expected failure.
2. **Green:** make the smallest maintainable change that passes it.
3. **Refactor:** improve structure without changing behaviour; keep the focused test green.
4. Run the containing module tests once.
5. Broaden to affected contract, app, UI gate, or full-suite checks only when the change reaches the corresponding checkpoint defined in `AGENTS.md`.

Do **not** rerun hundreds of tests after each small edit. When a broad run fails, reduce each failure to a focused reproducer, fix and rerun that subset, then perform one appropriate broad verification at the end.

## Non-negotiable implementation rules

- Put business orchestration in Python services. Keep DocType controllers thin and keep business rules out of browser code.
- Enforce permissions, organizational scope, allowed state transitions, validation, and audit effects on the server for every material action.
- Respect app ownership and dependency direction. Cross-app access uses the owner's published service or API; never deep-import internals or write another app's records directly.
- Use Frappe's normal document, permission, migration, background-job, and transaction mechanisms. Do not build parallel framework substitutes.
- For complex screens, build Vue 3 mounted inside a real Frappe Desk Page (validated standard — see `AGENTS.md` §6). Routine CRUD/administration uses standard Frappe Form/List/Report/Workflow APIs; module landing uses a standard Workspace. Do not add `frappe-ui` without explicit approval.
- Route record identifiers in URL path segments, preserve context across direct load, forward navigation, refresh, and browser back/forward. Register any route using `kentender_core.cl_shell.enterNative()` in `kentender_core.cl_surface_registry.js`. Note: `frappe.router.off()` is a confirmed no-op (see `AGENTS.md` §6.4) — use an active-flag guard, not `.off()`, to neutralize a listener on unmount.
- After server-side state changes, refresh or reconcile the visible page state. Verify both first paint and at least one interactive re-render.
- Never mark work complete from a passing narrow test alone. Match the full acceptance criteria and report exactly what was and was not run.

## Repository and application map

The repository root is `frappe-bench/apps/kentender_v1/`. It is a container repository; the actual Frappe applications are its top-level `kentender_*` directories. The bench is `/home/midasuser/frappe-bench`, and the default site is `kentender.midas.com`.

Primary dependency direction:

`kentender_core -> kentender_strategy -> kentender_budget -> kentender_procurement -> kentender_stores -> kentender_assets`

Side applications consume published interfaces:

- `kentender_suppliers`: supplier identity and qualification;
- `kentender_governance`: approvals and delegation;
- `kentender_compliance`: regulatory and audit-rule overlays;
- `kentender_integrations`: external-system adapters, not business-rule ownership;
- `kentender_transparency`: read-only or publication views, never transactional authority.

Business traceability must remain intact:

`Strategy -> Budget -> Demand -> Procurement Plan -> Tender -> Bid -> Evaluation -> Award -> Contract -> Inspection -> Stores/Assets -> Reporting/Audit`

Within each app, use `doctype/` for persistence and thin lifecycle validation, `services/` for business operations, `api/` for explicit endpoints, and `utils/` only for lightweight helpers.

## Command card

Run root `make` targets from `apps/kentender_v1/`. Run `bench` commands from `/home/midasuser/frappe-bench`.

### Discover before guessing

```bash
make help
```

Use the current target shown there; feature-gate names change.

### Focused Python test

```bash
cd /home/midasuser/frappe-bench
bench --site kentender.midas.com run-tests \
  --app <app> --module <python.test.module>
```

If the runner supports a narrower test selector in the current repository, use it during the red/green loop.

### Focused frontend and UI tests

```bash
npx vitest run path/to/file.spec.tsx
npx playwright test path/to/spec.ts -g "test name"
```

Use `npm run test:ui:smoke` for the UI smoke checkpoint and `npm run test:ui` only when a full UI run is justified.

### Assets

Never use plain `bench build` or an app-level Yarn build. Use the repository's Node wrapper:

```bash
./scripts/bench-with-node.sh build --app <app>
```

After CSS or JavaScript changes, clear the target site's cache and hard-refresh Desk. Do not mistake stale assets for a code defect.

### Bench lifecycle and seed data

```bash
make validate-links
make migrate SITE=<site>
make clear SITE=<site>
make doctor
make seed-kentender-mvp-v1 SITE=<site>
make seed-kentender-mvp-v1-validate SITE=<site>
make purge-kentender-playwright-data SITE=<site>
```

Use destructive or fixture-reset targets only when the task authorizes their scope and the target site is confirmed.

## Finish every implementation task with evidence

Report:

- behaviour and files changed;
- focused tests run and results;
- broader checks or manual flows run and results;
- checks not run and why;
- remaining risks, exclusions, or unresolved decisions.

Never claim a result that was not actually observed.
