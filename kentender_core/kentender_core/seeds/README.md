# KenTender v1 seed packs

Implements [docs/data/seed-data-spec-v1.md](../../docs/data/seed-data-spec-v1.md) and [docs/data/users-roles-permissions-spec-v1.md](../../docs/data/users-roles-permissions-spec-v1.md).

## Canonical world (two years, read as at 18 Jun 2027 10:00) — the current entry point

```bash
bench --site <site> execute kentender_core.seeds.canonical.run --kwargs '{"current": "award", "next_year": "annual_plan"}'
bench --site <site> execute kentender_core.seeds.canonical.dry_run
bench --site <site> execute kentender_core.seeds.canonical.validate --kwargs '{"current": "award", "next_year": "annual_plan"}'
```

`run` first removes every row that is not part of the canonical world
(test/Playwright budgets, needs, plans, requisitions and Tenders, users on
fixture e-mail domains, duplicate organisation units, isolation fiscal years,
legacy demo journeys, and child-table rows and files whose record is gone —
see `canonical.py`'s `collect_non_canonical`), then reseeds two financial
years (`calendar.py`): **FY 2026/27**, carried out — the site, Strategy, its
budget, Needs, departmental plans and Active Annual Plan always, then
`current` (`requisitions` → `tenders` → `bid_submission` → `bid_opening` →
`bid_evaluation` → `award`) for the laptops Tender and the executed portfolio
(`portfolio.py`) — and **FY 2027/28**, being prepared, as far as `next_year`
(`none` → `budget` → `needs` → `departmental_plans` → `annual_plan`). Each step
goes through its owning module's own seed, at its fixture instant (the bid
stages only on a test site, since they use the simulated signing, tender-box
and delivery services). Before the clear, any loaded demo profile
(Requisitions, Departmental Needs, Bid Opening, Award) is undone; at the end a
test site's clock is set to the as-at instant. The world, the commands and how
a module adds to it are in SEED-002
(`docs/mvp-1-r1/20_seed_data/KenTender_SEED-002_Canonical_Seed_World_v0_1.md`,
proposed to replace SEED-001 and SEED-OPS-001). Pass `"rebuild": True` to also drop the canonical
module rows first (downstream first: Tenders — which takes the bid, opening,
evaluation and award with it — Requisitions, Planning, Needs, Budget,
Strategy) and rebuild from scratch. Leaves ERPNext-owned records and the pre-cutover
legacy reference doctypes alone (KT-STD-001 §10).

`make seed-canonical SITE=<site>` wraps `run` for the full world (`CURRENT=award NEXT=annual_plan`; set either lower to stop a year earlier, add `REBUILD=True` for a rebuild; `THROUGH=` still maps for one release). Until SEED-002 is approved, the approved runbook is `docs/mvp-1-r1/00_common/KenTender_SEED-OPS-001_Canonical_Site_Seed_Runbook_v1_24.md` (each version has its own file from v1.16; v1.0–v1.15 were kept in `…_v1_0.md`); its stage ladder is superseded by the two controls.

**Procurement meetings branch (OVS-CHG-001 v0.6, runbook v1.23 §9C).** `make seed-ovs-register-branch SITE=<site>` adds Tender B beside the canonical Tender: a second department's Tender whose opening was recorded Not held, so the register shows four rows and counts three meetings held. `make seed-ovs-register-branch-restore SITE=<site>` removes it. Opt-in, test-site use; the canonical rows are never touched.

## Legacy entry points (`bench execute`)

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

## Demo platform seed (linked IT STD demo)

Preferred **demo / UAT** pack: clean PEs (`PE-MOH`, `PE-MOE`), purge conflicting CFG noise, load stable WORKS+IT chain, then actionable DIA/CFG/publication/bid stages. See [docs/data/DEMO_PLATFORM_SEED.md](../../docs/data/DEMO_PLATFORM_SEED.md).

```bash
bench --site <site> execute kentender_core.seeds.seed_demo_platform.run --kwargs '{"reset": true}'
# or: ./apps/kentender_v1/scripts/seed_demo_platform.sh
make -C apps/kentender_v1 seed-demo-platform-reset SITE=kentender.midas.com
```

## Stable platform seed (Works + IT STD)

Canonical MOH domain pack covering **Strategy**, **Budget**, **DIA (Demand)**, **Planning**, and **IT STD** import (used inside the demo platform loader).

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

Seeds use stable natural keys: `entity_code` **PE-MOH** / **PE-MOE**, user emails from `constants.SEED_USERS`, strategic plan titles `PLAN_BASIC_NAME` / `PLAN_EXTENDED_NAME`. Re-running a pack updates or replaces content in a deterministic way.

## Permissions

- **Strategy Manager** / **Planning Authority**: entity-scoped via `User.kt_procuring_entity`, `User Permission` on **Procuring Entity**, and hooks in `kentender_strategy.permissions`.
- **Planning Authority**: read-only on Strategy DocTypes; builder and “New Strategic Plan” shortcut respect `frappe.model.can_create` / `can_write`.

## Password

Local test users use **Test@123** (see `constants.TEST_PASSWORD`).
