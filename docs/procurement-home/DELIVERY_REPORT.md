# Procurement Home — delivery report (§18)

## Files changed

**Services / API**

- `kentender_procurement/procurement_home/SOURCE_MAP.md`
- `kentender_procurement/procurement_home/services/{home_context,home_actions,home_pipeline,home_deadlines,home_portfolio,home_service,pe_aliases}.py`
- `kentender_procurement/procurement_home/api/{home.py,landing.py}`
- `kentender_procurement/procurement_home/tests/test_home_service_contract.py`
- `kentender_procurement/procurement_home/seed/seed_home_demo.py`

**Desk UI**

- `kentender_procurement/page/kt_procurement_home/kt_procurement_home.json`
- `public/js/procurement_home_page.js`
- `public/css/procurement_home_page.css`
- `public/js/procurement_home_workspace.js` (Workspace → Page redirect)
- `www/procurement/home.html` (canonical `/procurement/home` → Desk)

**Navigation**

- `workspace_sidebar/procurement.json` — Home → Page `kt-procurement-home`
- `setup/sidebar_availability.py` — Home removed from Planned
- `setup/after_migrate_navigation.py` — sync Page; hide legacy Workspace
- `setup/workspace_permissions.py` — route key `kt-procurement-home`
- `public/js/procurement_sidebar_header.js` — Home active-state alias
- `hooks.py` — `page_js` / CSS / website route

**Tests / docs**

- `tests/ui/smoke/procurement/procurement-home-functional.spec.ts`
- `tests/ui/smoke/kt-cl-shell/native-sidebar-restyle.spec.ts`
- `setup/tests/test_procurement_sidebar_g0_012_contract.py`
- Workspace `procurement_home.json` — `is_hidden: 1`

## Stitch design used

- Populated: `docs/procurement-home/01_code.html` (main column only)
- Empty actions: `docs/procurement-home/02_code.html`
- Discarded: Stitch topnav, fake aside, FAB, illustrative search

## Source query map

See `procurement_home/SOURCE_MAP.md`.

## Pipeline state mapping

| Stage | Mapping |
|---|---|
| Demands under review | Demand Pending HoD / Pending Finance |
| Approved awaiting planning | Approved + not fully planned |
| Plan awaiting tender | Package Approved / Ready for Release |
| Tenders in preparation | TM2 pre-Published statuses |
| Published and open | Published + submission deadline future (or no deadline) |
| Closed awaiting next | Closed / Opening Ready |

## Financial metric definitions

- Approved budget / allocated / available — `get_budget_landing_data` portfolio sums
- Unfunded approved demand — approved demands without budget line or shortfall vs availability
- Active / open tenders — TM2 status + timeline deadline

## Permission rules

- Actions: role-gated DIA / PP / TM queues only
- Portfolio finance: Budget Officer, Finance Reviewer, HoP, PO, Planning Authority, System Manager, Accounts Manager (+ Administrator)
- Portfolio tenders: Tender Manager, PO, Planning Authority, Auditor, System Manager (+ Administrator)
- Unauthorized PE/FY rejected by `resolve_home_context`
- Section soft-fail: unavailable message; no silent zeros on hard errors

## Routes and deep links

| Intent | URL |
|---|---|
| Desk Home | `/desk/kt-procurement-home` |
| Prompt alias | `/procurement/home` → Desk |
| Legacy Workspace | hidden; redirects to Page |
| View all work | `/desk/demand-hub` |
| Lifecycle | `/desk/plc-procurement-journey` |

> Note: Page slug is `kt-procurement-home` because Workspace title **Procurement Home** already owns Desk slug `procurement-home`.

## Fixtures

- `seed_procurement_home_demo()` — idempotent summary over existing module rows (does not invent Home totals)

## Tests executed

| Suite | Result |
|---|---|
| `kentender_procurement.procurement_home.tests.test_home_service_contract` | OK (5) |
| `kentender_procurement.setup.tests.test_procurement_sidebar_g0_012_contract` | OK (7) |
| Playwright `procurement-home-functional.spec.ts` + `native-sidebar-restyle.spec.ts` | OK (11) |

## Genuine remaining gaps

1. Full §16 multi-persona seed (assigned approval, returned item, tender blocker, publication action, unfunded demand, no-finance user) still relies largely on existing site data; demo seed is a thin orchestrator.
2. Demand/plan **approval deadline** fields are not modeled — deadlines currently come from TM2 Timeline explicit dates only.
3. “Allocated to procurement plans” uses Budget Line allocated sums (Budget landing), not a dedicated approved-plan-item funding rollup.
4. Administrator entity list is capped to operational PEs (preferred + Demands/Budgets) rather than every demo Procuring Entity.

## Post-implementation UI results

**Setup:** Administrator on `kentender.midas.com`; Home Page synced via after_migrate; Procurement sidebar reconciled.

**On load:** `/desk/kt-procurement-home` shows Procurement rail with **Home** active (no Planned badge), title “Procurement Home”, subtitle, PE/FY context, Requires Your Action, Procurement Pipeline, Upcoming Deadlines | Portfolio Snapshot.

**After context change:** select PE/FY refreshes sections in place (hosts not remounted).

**Must NOT appear:** Stitch fake sidebar/topnav, charts, Approve/Reject on Home, Planned badge on Home, raw primary-key-only labels as primary display.

**Selectors:** `kt-ph-root`, `kt-ph-title`, `kt-ph-entity`, `kt-ph-fy`, `kt-ph-actions`, `kt-ph-actions-empty`, `kt-ph-pipeline`, `kt-ph-deadlines`, `kt-ph-portfolio`.
