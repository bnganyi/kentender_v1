# 1. Strategy

## Goal

Document the **Strategy** vertical: master data for national/programme planning that **Budget** and **Procurement** consume (e.g. strategic plan, programmes, objectives, KPI targets).

## Frappe app

- **`kentender_strategy`** (`apps/kentender_v1/kentender_strategy/`)

## DocTypes (Frappe module: *Kentender Strategy*)

| DocType | Purpose (summary) |
|---------|-------------------|
| Strategic Plan | Top-level plan document; anchors workspace and builder UX |
| Strategy Program | Programme under a strategic plan |
| Sub Program | Child programme hierarchy |
| Strategy Objective | Objectives linked into the hierarchy |
| Strategy Target | Measurable targets / KPI-style rows |
| Strategy Node | Graph / tree node model for strategy builder |
| Strategy Navigation | Desk navigation / module scaffolding |

*Authoritative list:* see [`doctypes_inventory.csv`](doctypes_inventory.csv) (filter `app=kentender_strategy`).

## Desk and assets

- **Workspace / list UX:** `public/js/strategy_workspace.js`, `public/css/strategy_workspace.css`
- **Strategic Plan form:** `public/js/strategic_plan.js`, `public/css/strategic_plan_form.css`
- **Strategy Builder page:** `page_js` hook `strategy-builder` → `public/js/strategy_builder_page.js`, `public/css/strategy_builder_page.css`
- **Shared list helper:** `public/js/workspace_list_selection_utils.js` (cache-busted from `hooks.py`)

## Seed data

Strategy master data is seeded primarily from **`kentender_core`** (shared programme seeds), not from a dedicated `kentender_strategy/seeds/` tree:

| Seed module (`kentender_core/seeds/`) | Role |
|----------------------------------------|------|
| `seed_strategy_basic.py` | Minimal strategy graph for dev/UAT |
| `seed_strategy_extended.py` | Richer strategy fixture set |
| `seed_strategy_empty.py` | Empty baseline |
| `reset_strategy_seed.py` / `reset_core_seed.py` | Teardown / reset helpers |
| `dev_full_reseed.py` | Orchestrated multi-app reseed (includes strategy) |

Planning handoff audit copies under `apps/kentender_v1/docs/audit/planning_tender_handoff_2026-05-03/seeds/` also contain **strategy seed variants** used in historical UAT packs (not shipped as Frappe fixtures by default).

## Dependencies

- **`kentender_core`**: procuring entity / business unit and audit primitives used across modules.
- **Downstream:** `kentender_budget` declares `required_apps` including `kentender_strategy`; procurement declares both strategy and budget.

## Related implementation (code, not DocTypes)

- Strategy-specific validation and graph logic live under `kentender_strategy/kentender_strategy/` (controllers next to each DocType, plus `api/` if present).
