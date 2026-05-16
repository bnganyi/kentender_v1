# 3. Demand Intake and Approval

## Goal

Document **Demand Intake and Approval**: capture of requisitions (`Demand`), line items, workflow toward planning, and **record-level permissions** integrated with Frappe roles (Requisitioner, Department Approver, Finance Reviewer, etc.).

## Frappe app and module

- **App:** `kentender_procurement`
- **Frappe module:** *Demand Intake* (see DocType JSON `module` field)

## DocTypes

| DocType | Purpose (summary) |
|---------|-------------------|
| Demand | Header requisition; links to budget line, procuring context, attachments |
| Demand Item | Child line items |

*Authoritative list:* [`doctypes_inventory.csv`](doctypes_inventory.csv) — filter `frappe_module=Demand Intake`.

## Desk and hooks

- **Desk workspace:** *Demand Intake and Approval* (`kentender_procurement/.../workspace/demand_intake_and_approval/`) — roles include Requisitioner, Department Approver, Finance Reviewer, Procurement Planner, System Manager.
- **Form script:** `doctype_js` → `Demand` → `public/js/demand_form.js`
- **Workspace assets:** `public/js/demand_intake_workspace.js`, `public/css/demand_intake_workspace.css` (`app_include_*` in `hooks.py`).
- **Permission hooks** (`hooks.py`):
  - `permission_query_conditions["Demand"]` → `demand_intake.permissions.demand_permissions.get_permission_query_conditions_for_demand`
  - `has_permission["Demand"]` → `demand_intake.permissions.demand_permissions.demand_has_permission`

## Seed data (`demand_intake/seeds/`)

| Module | Role |
|--------|------|
| `dia_seed_common.py` | Shared constants/helpers |
| `seed_dia_basic.py` | Default DIA slice for dev |
| `seed_dia_extended.py` | Larger scenario |
| `seed_dia_empty.py` | Minimal / empty |
| `seed_dia_exceptions.py` | Edge-case rows (rejections, corrections) |
| `seed_dia_planning_f1_prerequisites.py` | Preconditions for planning F1 handoff tests |

## Cross-links

- **Budget line:** Demand records reference **Budget Line** (in `kentender_budget`) for fiscal control.
- **Procurement Planning:** Approved demands feed **Procurement Plan** / **Procurement Package** flows (`procurement_planning/`).

## Code layout

- `kentender_procurement/kentender_procurement/demand_intake/` — controllers, services, permissions, tests.
