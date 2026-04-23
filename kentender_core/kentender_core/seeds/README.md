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
