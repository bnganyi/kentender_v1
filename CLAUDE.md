# CLAUDE.md

This is the operating entry point for Claude Code in the KenTender repository. Read [AGENTS.md](AGENTS.md) before editing — it is the source of truth for engineering rules, app ownership, and the test ladder. This file is the short task loop, environment facts, and command card; where the two overlap, AGENTS.md wins.

## Start every task this way

1. Read the user's request, the named implementation pack, and the closest applicable `AGENTS.md` or `AGENTS.override.md`.
2. Inspect `git status` and the target code, callers, and tests (AGENTS.md §3). Preserve existing user changes.
3. Classify the task before acting:
   - review, explanation, or diagnosis: inspect and report; do not implement;
   - change or build: implement the smallest complete change and validate it.
4. Identify the owning app (AGENTS.md §2), affected public contracts, and acceptance criteria. Do not load unrelated architecture or archived documents.
5. If applicable instructions conflict materially, stop and state the exact conflict (AGENTS.md §1) instead of guessing.

Use TDD for behaviour changes and bug fixes — red/green/refactor, AGENTS.md §7 — and the 5-level test ladder in AGENTS.md §8 to decide how broad to run checks afterward. Do not rerun the full suite after each small edit; reduce a broad failure to a focused reproducer first.

## Non-negotiable implementation rules

Highest-severity rules only; see the referenced AGENTS.md section for full detail and rationale.

- Business orchestration lives in Python services; DocType controllers stay thin; business rules never live only in browser code (§4.2).
- Every material server action enforces source state, role/organizational scope, validation, and audit effects (§4.3).
- Respect app ownership and dependency direction; cross-app access only through the owner's published service or API — never a deep import or direct write into another app's records (§2).
- Use Frappe's own document, permission, migration, background-job, and transaction mechanisms — no parallel substitutes (§4.1, §4.4).
- Complex screens: Vue 3 mounted in a real Frappe Desk Page (§6). Do not add `frappe-ui` without explicit approval.
- Route identifiers via URL path segments; register any native route in `kentender_core.cl_surface_registry.js`. `frappe.router.off()` is a confirmed no-op — use an active-flag guard instead (§6.4).
- After server-side state changes, refetch and re-render from the fresh response; never optimistically mutate local state (§6.2).
- Never mark work complete from a passing narrow test alone (§9).

## Repository map and environment

Bench root: `/home/midasuser/frappe-bench`. Repository root: `apps/kentender_v1/` inside it — a container repository whose `kentender_*` top-level directories are the actual Frappe apps. Default site: `kentender.midas.com`. For app ownership, dependency direction, and the business traceability chain, see AGENTS.md §2.

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

Report completion per AGENTS.md §9: behaviour and files changed; checks run and results; checks not run and why; remaining risks, exclusions, or unresolved decisions. Never claim a result that was not actually observed.
