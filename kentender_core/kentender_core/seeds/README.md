# KenTender v1 seed packs

Implements [docs/data/seed-data-spec-v1.md](../../docs/data/seed-data-spec-v1.md) and [docs/data/users-roles-permissions-spec-v1.md](../../docs/data/users-roles-permissions-spec-v1.md).

## Entry points (`bench execute`)

Run as **Administrator** or **System Manager** on the target site.

```bash
bench --site <site> execute kentender_core.seeds.seed_core_minimal.run
bench --site <site> execute kentender_core.seeds.seed_strategy_empty.run
bench --site <site> execute kentender_core.seeds.seed_strategy_basic.run
bench --site <site> execute kentender_core.seeds.seed_strategy_extended.run
bench --site <site> execute kentender_core.seeds.seed_budget_empty.run
bench --site <site> execute kentender_core.seeds.seed_budget_basic.run
bench --site <site> execute kentender_core.seeds.seed_budget_extended.run
bench --site <site> execute kentender_core.seeds.seed_budget_line_dia.run
```

## Reset / purge

```bash
bench --site <site> execute kentender_core.seeds.reset_strategy_seed.run
bench --site <site> execute kentender_core.seeds.reset_core_seed.run
```

## Stable platform seed (Works + IT STD)

Canonical MOH dev/UAT dataset covering **Strategy**, **Budget**, **DIA (Demand)**, **Planning**, and **IT STD v1_1** import.

```bash
# Load (idempotent upsert)
bench --site <site> execute kentender_core.seeds.seed_stable_platform.run

# Delete stable pack rows then regenerate
bench --site <site> execute kentender_core.seeds.seed_stable_platform.run --kwargs '{"reset": true}'

# Clear only (no reload)
bench --site <site> execute kentender_core.seeds.clear_stable_platform.run

# Validate without loading
bench --site <site> execute kentender_core.seeds.seed_stable_platform.validate
```

From `apps/kentender_v1`: `make seed-stable-platform SITE=kentender.midas.com` and `make seed-stable-platform-reset SITE=kentender.midas.com`.

Scenarios:

| Track | Business codes | Module |
|---|---|---|
| Works renovation | `DEM-MOH-2026-001`, `PLAN-MOH-2026`, `PKG-MOH-2026-001` | Strategy → Budget → DIA → PP2 Planning |
| IT HMIS upgrade | `DEM-MOH-2026-002`, `PLANINCL-MOH-2026-002`, `PKG-MOH-2026-002` | Strategy/Budget/DIA/Planning supplement |
| IT STD library | `KE-PPRA-IT-2022-04` (v1_1 zip) | STD Engine import (DRAFT) |

Default PP2 checkpoint: `PACKAGE_DRAFT` (override with `planning_checkpoint` kwarg; higher checkpoints require TM handoff modules).

Optional dry run (strategy reset only lists plans that would be removed):

```bash
bench --site <site> execute kentender_core.seeds.reset_strategy_seed.run --kwargs "{'dry_run': True}"
```

`reset_core_seed` deletes seeded Strategic Plans (same titles as strategy reset), then test users (`*@moh.test`), User Permissions, MOH/MOE departments and procuring entities. **Role** DocTypes are not removed.

## Idempotency

Seeds use stable natural keys: `entity_code` **MOH** / **MOE**, user emails from `constants.SEED_USERS`, strategic plan titles `PLAN_BASIC_NAME` / `PLAN_EXTENDED_NAME`. Re-running a pack updates or replaces content in a deterministic way.

## Permissions

- **Strategy Manager** / **Planning Authority**: entity-scoped via `User.kt_procuring_entity`, `User Permission` on **Procuring Entity**, and hooks in `kentender_strategy.permissions`.
- **Planning Authority**: read-only on Strategy DocTypes; builder and “New Strategic Plan” shortcut respect `frappe.model.can_create` / `can_write`.

## Password

Local test users use **Test@123** (see `constants.TEST_PASSWORD`).
