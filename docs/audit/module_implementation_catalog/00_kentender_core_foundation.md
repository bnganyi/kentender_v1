# Appendix A — Kentender Core (shared foundation)

## Goal

List **cross-programme** DocTypes and seeds that **Strategy**, **Budget**, and **Procurement** rely on, so audit readers do not assume these live inside a single vertical.

## Frappe app

- **`kentender_core`** (`apps/kentender_v1/kentender_core/`)

## DocTypes

| DocType | Purpose (summary) |
|---------|-------------------|
| Procuring Entity | Organisational anchor for procurement authority |
| Procuring Department | Department under entity |
| Business Unit | Optional business unit split |
| Typed Attachment | Structured attachment typing |
| Audit Event | Generic audit row (used with domain-specific payloads) |
| Exception Record | Controlled exception / waiver logging |
| Business ID Counter | Sequential business identifiers |

*CSV rows:* filter `app=kentender_core` in [`doctypes_inventory.csv`](doctypes_inventory.csv).

## Seeds (`kentender_core/seeds/`)

Shared orchestration and budget/strategy seed entry points (also referenced from `02_budget.md` / `01_strategy.md`):

- `seed_core_minimal.py`, `dev_full_reseed.py`, `reset_core_seed.py`
- Strategy/budget variants: `seed_strategy_*`, `seed_budget_*`, `seed_budget_line_dia.py`

## Desk

- Global desk layout helper: `app_include_css` → `public/css/kentender_desk_builder_layout.css`
