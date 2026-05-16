# KenTender module implementation catalog

**Repository path:** `docs/audit/module_implementation_catalog/` (inside **`kentender_v1`**).

## Goal

Provide a **single audit-facing index** of what is implemented across the six programme modules (Strategy through Tender Management): **Frappe DocTypes by app/module**, **seed and fixture entry points**, **Desk and web surfaces**, and **cross-cutting dependencies** (notably `kentender_core`). This folder is intended for compliance, onboarding, and gap analysis—not runtime behaviour.

## Scope and sources

| Module | Primary Frappe app(s) | Main code roots (`apps/kentender_v1/`) |
|--------|------------------------|----------------------------------------|
| 1. Strategy | `kentender_strategy` | `kentender_strategy/` |
| 2. Budget | `kentender_budget` | `kentender_budget/` |
| 3. Demand Intake and Approval | `kentender_procurement` (Frappe module *Demand Intake*) | `kentender_procurement/demand_intake/` |
| 4. Procurement Planning | `kentender_procurement` (Frappe module *Procurement Planning*) | `kentender_procurement/procurement_planning/` |
| 5. STD Admin | `kentender_procurement` (Desk *Governance & Configuration* + `std-engine` page) | `kentender_procurement/tender_management/` (STD governance, library APIs, templates) |
| 6. Tender Management | `kentender_procurement` (TM2, STD instances, publication, supplier portal) | `kentender_procurement/tender_management/` |

**Shared foundation:** `kentender_core` (organisations, audit primitives, shared seeds). Procurement declares `required_apps = ["kentender_core", "kentender_strategy", "kentender_budget"]` in `kentender_procurement/hooks.py`.

## Artifacts in this folder

| File | Contents |
|------|----------|
| [`01_strategy.md`](01_strategy.md) | Strategy DocTypes, desk assets, seeds |
| [`02_budget.md`](02_budget.md) | Budget DocTypes, desk assets, seeds |
| [`03_demand_intake_and_approval.md`](03_demand_intake_and_approval.md) | Demand DocTypes, permissions hooks, seeds |
| [`04_procurement_planning.md`](04_procurement_planning.md) | Planning DocTypes, permissions hooks, seeds |
| [`05_std_admin.md`](05_std_admin.md) | STD Template governance DocTypes, `std-engine` page, after_migrate seeds |
| [`06_tender_management.md`](06_tender_management.md) | TM2, Tender STD Instance, publication, security, web routes |
| [`doctypes_inventory.csv`](doctypes_inventory.csv) | Flat list: `app,frappe_module,doctype_name` |
| [`00_kentender_core_foundation.md`](00_kentender_core_foundation.md) | Shared **kentender_core** DocTypes and seeds (appendix) |

**Seed literals (JSON + STD package copy):** [`../seed_data_bundle/README.md`](../seed_data_bundle/README.md)

## How this inventory was produced

DocType names and Frappe `module` values were derived from `**/doctype/*/<name>.json` under each app (automatable; re-run a small script if DocTypes change). Seed lists are **indicative** (Python modules under `seeds/` and documented `bench execute` / `after_migrate` hooks)—see each module file for paths. For **auditable seed payloads** (constants, DIA scenarios, STD POC files), use the **seed data bundle** linked above.

## Maintenance

When adding DocTypes or seeds:

1. Update the relevant `0x_*.md` file.
2. Regenerate `doctypes_inventory.csv` (or append rows) so audit diffs stay reviewable.
3. When seed **literals** or the STD POC package change, update `docs/audit/seed_data_bundle/` per that folder’s README.

*Generated as part of the KenTender v1 bench documentation set.*
