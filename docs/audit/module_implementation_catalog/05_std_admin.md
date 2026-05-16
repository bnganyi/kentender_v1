# 5. STD Admin (Official STD Library)

## Goal

Document **STD (Standard Tender Document) administration**: governed **STD Template** lifecycle (import → validate → approve → activate), **usage** tracking, **validation findings**, and **separation-of-duties** roles enforced via DocPerm + desk surfaces—not ad-hoc file drops.

## Frappe app and module

- **App:** `kentender_procurement`
- **Frappe module:** *Kentender Procurement* (STD DocTypes share this module with tender runtime DocTypes; desk separation is by **Workspace** and page routes.)

## DocTypes (STD / governance focus)

| DocType | Purpose (summary) |
|---------|-------------------|
| STD Template | Canonical structured tender template package (governance fields, lifecycle status) |
| STD Template Lifecycle Event | Immutable audit trail of lifecycle transitions |
| STD Template Usage | Records template usage against tenders / instances (read-heavy admin view) |
| STD Template Validation Finding | Structured validation outcomes (blockers/warnings) |
| Security Role | Custom security role registry (SEC pack) |
| Security Permission | Atomic permission codes |
| Security Role Permission | Join of role ↔ permission |

**Also shipped under the same Frappe module but primarily “tender runtime”:** TM2*, Tender STD*, publication, etc. Those are catalogued under [`06_tender_management.md`](06_tender_management.md) to avoid duplicate prose; the **CSV** lists every DocType once.

## Desk: Governance & Configuration workspace

- **Workspace JSON:** `kentender_procurement/kentender_procurement/kentender_procurement/workspace/governance_and_configuration/governance_and_configuration.json`
- **Roles:** STD Template Administrator, Importer, Reviewer, Approver, Activator, Auditor, STD Technical Inspector, plus System/Administrator.
- **Shortcuts:** catalogue, import wizard entry, filtered lists (Pending Validation, Pending Approval, Active, Superseded/Retired), usage, audit, package inspector (see workspace `shortcuts` / `links`).

## STD Engine page (`std-engine`)

- **`page_js`** in `hooks.py` loads the **Official STD Library** shell: `public/js/std_engine_page.js` plus modular `public/js/std_library/*.js` (import wizard, catalogue, API bridge, shell renderers).
- **Styles:** `public/css/std_library_shell.css`, `app_include_css` entry.

## Server entry points (representative)

- **Package / validation:** `tender_management/services/std_package_validation.py`, `std_template_engine.py`, `std_admin_console.py` (facade to `std_template` whitelisted methods).
- **Library HTTP API:** `tender_management/api/std_library_templates.py` (and related `api/` modules).
- **Governance usage checks:** `tender_management/services/std_template_governance_usage.py`

## Seed data and migrations

| Mechanism | Location / behaviour |
|-----------|----------------------|
| `after_migrate` | `hooks.py` → `tender_management.seeds.std_template_governance_roles.run_after_migrate` |
| | `tender_management.seeds.std_template_governance_seed.run_after_migrate` |
| Python seeds | `tender_management/seeds/std_template_governance_seed.py`, `std_template_governance_roles.py` |
| Loader / fixture template | `tender_management/services/std_template_loader.py` (controlled import of packaged STD, e.g. WORKS POC code) |

## Patches (governance / schema)

See `kentender_procurement/patches.txt` — STD-related examples:

- `std_gov_002_backfill_std_template_governance_fields`
- `std_gov_002b_backfill_template_version`
- `retire_std_engine_cleanup`

## Tests

- Broad coverage under `kentender_procurement/.../tender_management/tests/test_std_*`, library governance, and integration tests for governance APIs.
