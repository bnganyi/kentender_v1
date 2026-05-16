# 2. Budget

## Goal

Document the **Budget** vertical: fiscal envelopes, **Budget Line** as the join between strategy and operational demand/procurement, reservations, and funding splits.

## Frappe app

- **`kentender_budget`** (`apps/kentender_v1/kentender_budget/`)

## DocTypes (Frappe module: *Kentender Budget*)

| DocType | Purpose (summary) |
|---------|-------------------|
| Budget | Annual / cycle budget header |
| Budget Line | Line-level envelope; links to strategy hierarchy and later to Demand / procurement |
| Budget Allocation | Split of budget across programmes or lines |
| Budget Reservation | Holds / commitments against a line |
| Funding Source | Source-of-funds metadata |
| Budget Navigation | Desk navigation scaffolding |

*Authoritative list:* [`doctypes_inventory.csv`](doctypes_inventory.csv) (`app=kentender_budget`).

## Desk and assets

- **Workspace:** `public/js/budget_workspace.js`, `public/css/budget_workspace.css`
- **Budget Builder page:** `page_js` → `budget-builder` → `public/js/budget_builder_page.js`, `public/css/budget_builder_page.css`
- **Budget DocType form:** `public/js/budget.js`

## Seed data

| Seed module (`kentender_core/seeds/`) | Role |
|----------------------------------------|------|
| `seed_budget_basic.py` | Minimal budget + lines for DIA/planning tests |
| `seed_budget_extended.py` | Richer allocations / reservations |
| `seed_budget_empty.py` | Empty baseline |
| `seed_budget_line_dia.py` | Lines shaped for Demand Intake ↔ planning flows |
| `_budget_seed_common.py` | Shared helpers |
| `dev_full_reseed.py` | Full bench reseed orchestration |

Historical / audit seed packs: `apps/kentender_v1/docs/audit/planning_tender_handoff_2026-05-03/seeds/seed_budget_*.py`.

## Dependencies

- **`kentender_core`**, **`kentender_strategy`** (`required_apps` in `kentender_budget/hooks.py`).
- **Upstream for procurement:** `kentender_procurement` requires `kentender_budget` so Demand and packages can resolve budget lines.

## Related implementation

- Budget business rules and roll-ups: `kentender_budget/kentender_budget/` (DocType controllers, `api/`).
