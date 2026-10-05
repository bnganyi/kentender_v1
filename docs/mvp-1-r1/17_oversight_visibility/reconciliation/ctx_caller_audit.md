# OVS-CHG-001 v0.6: working-context caller audit (Phase 12, OVS6-1201 and OVS6-1202)

**Made 4 October 2026 by a read-only audit** of `.py`, `.js`, `.vue`, `.ts`, `hooks.py` and tests (excluding `node_modules`, archive, docs and built `public/dist`). "No caller" means none found in those. The Python tests were not run by the audit. Paths: `KC` = `kentender_core/kentender_core`, `KP` = `kentender_procurement/kentender_procurement`, `KB` = `kentender_budget/kentender_budget`.

**What CTX-CHG-001 v1.1 asks.** §2: "Remove CTX v1.0's multi-entity chooser, global PE preference and cross-PE picker"; "Display the site identity where useful; do not ask a user to choose the only entity." §3: "Do not use Frappe User Permission, User Scope Assignment or browser preference as business authority." §4: "Do not add a global FY, PE Fiscal Year Context gate." §5: obsolete `select_working_pe` / `pe_options` flows are retired, module-local filters are kept only where they satisfy the contract. AUTH-ADR-001 v1.11: "One KenTender site represents exactly one Procuring Entity … configured once and never selected."

**Headline.** The Procuring Entity selector was wired end to end, but no production page turned it on: `showPeSwitcher` was only ever false or omitted. The live dependencies were Procurement Home and the Procuring-Entity-offer code in `kentender_core`. Planning, Needs and Budget were already free of a Procuring Entity and keep FY/OU as local filters.

## What was done (4 October 2026)

| Item | Before | After |
|---|---|---|
| PageRail entity switcher (`KC/public/js/kt_industry/components/PageRail.vue`, `kt_industry_page_rail.bundle.js`) | calls `get_working_context` / `select_working_pe`, fires `kt:working-pe-changed`; dormant | removed |
| `KC/api/working_context_api.py` (`get_working_context`, `select_working_pe`, `select_module_financial_year`) and `KC/tests/test_working_context_api.py` | only PageRail called it | removed |
| Procurement Home (`KP/procurement_home/services/home_context.py`, `public/js/procurement_home_page.js`) | threw "No Procuring Entity is available" for a user with no User Scope Assignment / User Permission row; read and wrote the global working-entity preference; entity `<select>` | the site's own entity (`Site Procuring Entity`), shown as text, for every user; an explicit request for any other is refused; no preference read or written; the select and the `kt:working-pe-changed` listener removed |

## What is kept, and why

| Item | Anchor | Live callers | Disposition |
|---|---|---|---|
| `pe_options`, `get_working_pe`, `select_working_pe`, `GLOBAL_PE_KEY` | `KC/services/working_context.py:45-181` | `KC/services/reference_data_resolver.py:176,210`; tests; two migration patches (`migrate_kt_procuring_entity_to_working_pe`, KB `migrate_budget_working_context_defaults`) | retire with the reference-data shim (FU-OVS-56) |
| `resolve_working_context`, `select_working_context`, `_persist_context_pair` and two endpoints (`reference_data_api.py:234,239`) | `KC/services/reference_data_resolver.py:143,199,221` | none in production (no JS caller); `test_working_context_service.py:248-266` | safe to remove with their tests |
| `resolve_authorized_contexts`, `validate_context_for_command` and endpoints | resolver :49, :80; api :224, :229 | none in production; `test_reference_data_context_lifecycle.py` | safe to remove with their tests |
| `default_fy_options` | `working_context.py:190` | reached only through the dead paths above | remove with them |
| `get_module_fy`, `select_module_fy`, `clear_module_fy`, `get_module_ou`, `select_module_ou`, `clear_module_ou` | `working_context.py:275-367` | Needs (`workspace.py`), Planning (`planning_context.py`), Home (`home_context.py`, key `kt_home_financial_year`) | **keep**: reversible module-local filters that satisfy §5 (revalidated on each read, a stale value dropped) |
| `PE Fiscal Year Context` lifecycle and queries | `KC/services/reference_data_transitions.py:327-535`, `reference_data_queries.py:293-392` | Configuration maintenance (`ReferenceData.vue`), seeds, patches | **keep**: §3 "Configuration maintenance remains separately authorised" |
| `permitted_procuring_entities` | `KC/services/org_scope_access.py:87` (falls back to `User Permission` at :98-102) | `working_context.py:117`, `reference_data_resolver.py:118` (Home no longer calls it) | the real blocker; retire in a later authority phase |
| `authorization_native.py` (User Permission as scope authority) | `KC/services/authorization_native.py:34-54` | test-only importer | safe to remove with its test |
| `permitted_org_units`, `can_access_owned_record`, `user_scope_rows` | `KC/services/org_scope_access.py` | seed validators and the seed-contract test only; no business route | remove with the seed checks |
| Budget fiscal-year filter | `KB/public/js/budget_shared/composables/useFiscalYearFilter.js` (browser localStorage) | `BudgetWorkspaceScreen.vue`, `RegisterAllocationScreen.vue` | acceptable as a filter; optionally move to `get_module_fy("budget")` |

## Routes that take a visible year or filter

- **Procurement Home**: a stale saved entity or year falls back silently; an unlisted year throws. After this change it does not touch entity authority.
- **Budget workspace**: a link with no year and no valid saved one shows a "no year selected" picker; a year named in the link overrides the saved one (`useFiscalYearFilter.js:56-61`). Not a Procuring Entity gate.
- **Planning workspace**: an explicit year outside `selectable_years` throws `PLN_FY_NOT_SELECTABLE` (`planning_context.py:115-116`); record routes are fetched by reference and do not read the saved year.
- **Needs**: no blocking outcome; a stale unit or year is healed; the detail route fetches by reference.
- No route in Strategy, Requisitions, Tenders, Award, Evaluation or Configuration requires a Procuring Entity or year.

## Not verified by the audit

Whether Strategy and Requisitions have any year filter (none found); Playwright specs against the running site; the built `public/dist` bundles.
