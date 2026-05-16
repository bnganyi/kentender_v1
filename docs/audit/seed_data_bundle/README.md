# KenTender seed data bundle (audit + extension)

## Goal

Provide **concrete seed artefacts**—not only Python entry points—so auditors and engineers can **review, diff, and extend** deterministic data without spelunking the codebase. This bundle contains:

1. **Frozen JSON** — values extracted from canonical seed modules (`frozen/`).
2. **On-disk payloads** — full copies of structured files already in-repo (`packages/`, `fixtures/`).
3. **This README** — how to load data on a site and how to keep the bundle in sync with code.

## Layout

| Path | Description |
|------|-------------|
| [`frozen/core_constants.json`](frozen/core_constants.json) | MOH entity, departments, seed users, plan titles (`constants.py`) |
| [`frozen/budget_seed_names.json`](frozen/budget_seed_names.json) | Budget / plan name keys used by budget line seed |
| [`frozen/strategy_moh_basic_plan.json`](frozen/strategy_moh_basic_plan.json) | Full tree for `seed_strategy_basic` (programmes, objectives, targets) |
| [`frozen/dia_g2_budget_lines.json`](frozen/dia_g2_budget_lines.json) | DIA budget line codes and amounts (`seed_budget_line_dia`) |
| [`frozen/dia_g1_demands_scenarios.json`](frozen/dia_g1_demands_scenarios.json) | DIA business IDs and workflow scenarios (`dia_seed_common`) |
| [`frozen/works_stdint_s01_stable_ids.json`](frozen/works_stdint_s01_stable_ids.json) | Stable plan/package/demand codes for WORKS S01 |
| [`frozen/stdinst_1400_stable_ids.json`](frozen/stdinst_1400_stable_ids.json) | STDINST-1400 fixture identifiers |
| [`frozen/bench_execute_catalog.json`](frozen/bench_execute_catalog.json) | Dotted `bench execute` paths by app area |
| [`packages/ke-ppra-works-building-2022-04-poc/`](packages/ke-ppra-works-building-2022-04-poc/) | **Copy** of official STD WORKS POC package (manifest, forms, rules, `sample_tender.json`, …) |
| [`fixtures/tm2_seed_works_open_tender.json`](fixtures/tm2_seed_works_open_tender.json) | **Copy** of TM2 tender JSON fixture used in tests / tooling |

> **Canonical sources:** The `packages/` tree is a byte copy of  
> `kentender_procurement/.../tender_management/std_templates/ke_ppra_works_building_2022_04_poc/`.  
> When the upstream package changes, re-copy into this bundle (or automate in CI).

## Loading seed data on a site

Typical **DIA + planning** order (from in-code docstrings):

```bash
bench --site kentender.midas.com execute kentender_core.seeds.seed_strategy_basic.run
bench --site kentender.midas.com execute kentender_core.seeds.seed_budget_extended.run
bench --site kentender.midas.com execute kentender_core.seeds.seed_budget_line_dia.run
bench --site kentender.midas.com execute kentender_procurement.demand_intake.seeds.seed_dia_basic.run
```

**WORKS STDINT-S01** (planning through release-to-tender):

```bash
bench --site kentender.midas.com execute kentender_procurement.procurement_planning.seeds.seed_works_stdint_s01.run
```

**Full orchestrated reseed** (destructive — dev/UAT only):

```bash
bench --site kentender.midas.com execute kentender_core.seeds.dev_full_reseed.run
```

See [`frozen/bench_execute_catalog.json`](frozen/bench_execute_catalog.json) for additional callables.

## What is *not* duplicated here

- **Large programme seeds** (`seed_strategy_extended`, full `seed_pub_moh_1100` document graphs) — still only in Python; extend this bundle with new `frozen/*.json` files when you need auditors to see those literals.
- **Database-only after_migrate** STD governance rows — created by hooks listed in `bench_execute_catalog.json` under `frappe_after_migrate_hooks`.
- **Historical audit copies** under `docs/audit/planning_tender_handoff_2026-05-03/seeds/` — separate tree; merge into this bundle if you want one folder of truth.

## Maintenance checklist

When changing seed **constants** or **scenario tables**:

1. Update the Python source of truth.
2. Update the matching file under `frozen/` (or add a CI check that diffs them).
3. If STD POC files change, re-run:

```bash
cp -a apps/kentender_v1/kentender_procurement/kentender_procurement/tender_management/std_templates/ke_ppra_works_building_2022_04_poc \
      apps/kentender_v1/docs/audit/seed_data_bundle/packages/ke-ppra-works-building-2022-04-poc
```

## Related documentation

- Module overview: [`../module_implementation_catalog/README.md`](../module_implementation_catalog/README.md)
- DocType flat list: [`../module_implementation_catalog/doctypes_inventory.csv`](../module_implementation_catalog/doctypes_inventory.csv)
