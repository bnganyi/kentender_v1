# ANL-CHG-001 v0.8: hook and caller inventory (row ANL8-0008)

Repository-wide search for `analytics` (case-insensitive) in `.py`, `.js`, `.json`, `.vue`, `.ts`, `Makefile` and `.md` outside `docs/`, `node_modules` and the new Analytics files, taken 5 October 2026 before the Page was added.

| Where | What it says | Action |
|---|---|---|
| `kentender_procurement/.../workspace_sidebar/procurement.json:28-31` | Sidebar item "Analytics", `link_to: "coming-soon"`, `route_options {"feature":"Analytics"}` | Point at the Page `analytics`; drop the route option (row 0601) |
| `kentender_procurement/.../setup/sidebar_availability.py:23` | "Analytics" in `PLANNED_SIDEBAR_LABELS` | Remove (row 0602) |
| `kentender_procurement/.../setup/tests/test_procurement_sidebar_g0_012_contract.py:41,150` | Guards "Analytics" as planned and unlinked | Update (row 0603) |
| `kentender_procurement/.../setup/tests/test_procurement_home_page_roles.py:46` | "Analytics" in the stock-role list (an ERPNext role, not a Page) | No change |
| `kentender_core/.../public/js/home/Home.spec.js:170-173` | Asserts Home never shows a "Procurement Analytics" link | Home reads the verdict; the assertion changes when the link is switched on (row 0604) |
| `kentender_core/.../tests/test_home_design_scope.py:145` | Names Analytics among Home's module icons | No change |
| `kentender_procurement/.../public/js/kt_cl_shell_poc_page.js:15` | A proof-of-concept shell with an "Analytics" link to `#` | Legacy shell; not a caller. No change |
| `kentender_procurement/.../public/js/it_tender_configuration_it_requirements_page.js:492` | Material-icon markup containing the word | Not a caller. No change |
| Home plan D7 and Home spec §9 | "See all in Procurement Analytics" is absent until an Analytics verdict exists | `get_analytics_access` is the verdict; Home wiring is row 0604 |

Added by this work: hook `kt_analytics_providers` in `kentender_procurement/hooks.py` (four modules) and `kentender_budget/hooks.py` (one); `kt_technical_read_probes` gains `kentender_core.services.analytics_probes.read_probes`; page_js entry `analytics` (Phase 5).

No other file in `kentender_*` names Analytics. No existing hook, route or role tuple was changed.
