# 4. Procurement Planning

## Goal

Document **Procurement Planning**: translating approved demand into **Procurement Plan** and **Procurement Package** structures, driven by **Procurement Template** metadata and planning profiles (KPI, risk, vendor, decision criteria).

## Frappe app and module

- **App:** `kentender_procurement`
- **Frappe module:** *Procurement Planning*

## DocTypes

| DocType | Purpose (summary) |
|---------|-------------------|
| Procurement Plan | Planning cycle / authority record |
| Procurement Package | Package of procurement lines for tender release |
| Procurement Package Line | Monetary and scope lines under a package |
| Procurement Template | Template definition (methods, default STD template linkage, etc.) |
| KPI Profile | Planning-side KPI profile |
| Risk Profile | Planning-side risk profile |
| Vendor Management Profile | Vendor strategy profile |
| Decision Criteria Profile | Evaluation / decision criteria profile |

*Authoritative list:* [`doctypes_inventory.csv`](doctypes_inventory.csv) — filter `frappe_module=Procurement Planning`.

## Desk and hooks

- **Workspace:** *Procurement Planning* — roles include Procurement Planner, Procurement Officer, Planning Authority, Auditor, System Manager (`workspace/procurement_planning/`).
- **Workspace assets:** `public/js/procurement_planning_workspace.js`, `public/css/procurement_planning_workspace.css`
- **Package form script:** `doctype_js` → `Procurement Package` → `public/js/procurement_package.js`
- **Template selector helper:** `public/js/pp_template_selector.js`
- **Permission hooks** (`hooks.py`):
  - `Procurement Plan` and `Procurement Package` — `procurement_planning.permissions.pp_record_permissions` (query conditions + `has_permission`)

## Seed data (`procurement_planning/seeds/`)

| Module | Role |
|--------|------|
| `seed_procurement_planning_f1.py` | F1 planning / handoff scenario |
| `seed_planning_pp3_slice.py` | PP3 slice fixture |
| `seed_works_stdint_s01.py` | WORKS STDINT-S01 integrated planning + tender seed chain |
| `works_std_seed_requirements.py` | Preconditions for works STD seed |
| `works_stdint_s01_verification.py` | Doc 3 §28 structural checks; §29 TM2 smoke stub (legacy PT path removed) |
| `validate_planning_seed_dependencies.py` | Dependency validation for seeds |

## Release to tender (integration hook)

- `hooks.py` → `release_procurement_package_to_tender` → `tender_management.services.release_procurement_package_to_tender.hook_release_procurement_package_to_tender`  
  This is the **contractual handoff** from planning package status to **TM2 Tender** creation (see `06_tender_management.md`).

## Code layout

- `kentender_procurement/kentender_procurement/procurement_planning/` — services, permissions, seeds, tests.
