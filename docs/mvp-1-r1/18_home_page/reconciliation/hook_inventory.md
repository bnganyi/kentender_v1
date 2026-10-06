# Hook, route and workspace inventory (row HOME6-0004)

Date: 4 October 2026. Grep over `apps/kentender_*` (source, tests, JSON, docs; compiled `public/dist` bundles ignored). Dev-site query read-only. Note the repository also appears under `apps/kentender_v1/…`, so a grep from `apps/` shows each file twice.

## 1. `kt_my_work_providers`

Registered in `kentender_procurement/hooks.py` (seven providers: Needs, Planning, Requisitions, Tenders, Bid Opening, Evaluation, Award), `kentender_budget/hooks.py`, `kentender_core/hooks.py` (support issues), `kentender_suppliers/hooks.py` (supplier accounts). Called only by `kentender_core/services/my_work.py` (`_provider_rows`). Tests: `kentender_budget/tests/test_bud_chg_001_v16_my_work_provider.py`, `procurement_requisitions/tests/test_my_work_provider.py`, `departmental_needs/tests/test_departmental_needs_my_work.py`, `tests/ui/smoke/departmental_needs/departmental-needs-review-task.spec.ts`.

**Decision:** Home does not use or change this hook (plan D1). Nothing here is reshaped by Home; no caller breaks. Home's own hook `kt_home_providers` is new. Owners may share row-building helpers with their My Work provider but must not alter that provider's output until My Work is retired (HOME6-0607).

## 2. Landing: `home_page`

- `kentender_core/hooks.py:62`: `boot_session = ["kentender_core.services.my_work.patch_bootinfo_home"]`.
- `kentender_core/services/my_work.py:236-240`: `patch_bootinfo_home` sets `bootinfo.home_page = "my-work"` for users with an active Operational Scope Assignment.
- Test: `kentender_core/tests/test_authorization_gate03.py:88-93` asserts `home_page == "my-work"` for an assigned user and `"desktop"` for Administrator.
- Other `home_page` hits are in the unrelated `frontend` app (`patches/v1_0/create_homepage_v15.py`).

**Decision:** Phase 6 changes the value to the Home route and updates the test above. Administrator and unassigned users keep `desktop` unless the owner decides otherwise (open question for Phase 6, logged as HOME6-0604).

## 3. The `my-work` route

Files that name it as the shared page: `kentender_procurement/…/page/my_work/{my_work.js,my_work.json}`, `public/js/tender_management_v2_workbench_page.js`, `public/js/procurement_journey_page.js`, `procurement_lifecycle/api/journey_api.py` and its two tests, `patches/pln_chg_001_v127_retire_my_work_workspace.py` (an earlier retirement of a `My Work` *workspace*, not the page), `setup/workspace_permissions.py`, `setup/tests/test_workspace_sidebar_fastpath.py`; Playwright specs `planning-guidance.spec.ts` and `departmental-needs-review-task.spec.ts`.

**Not the shared page:** Strategy's `strategy_page.js`, `PortfolioScreen.vue`, `ApprovalTaskScreen.vue`, `workspace/strategy_management/strategy_management.json` and `strategy-approver.spec.ts` use `/app/strategy/my-work`, Strategy's own "Actions" tab (read and confirmed in `PortfolioScreen.vue:4,16`). It is a different route that happens to share the slug and is not removed with My Work. It also means Strategy already has its own task list that a Strategy Home provider can reuse (`strategy_ui_contracts._my_work_versions`).

**Decision:** My Work removal (HOME6-0607) must repoint or remove each shared-page reference above and is blocked until HOME-G08. Each of the two Playwright specs needs checking for whether it walks to `my-work`.

## 4. Legacy Procurement Home

`page/kt_procurement_home/`, hidden Workspace `Procurement Home` (`workspace/procurement_home/procurement_home.json`), `public/js/procurement_home_page.js`, `procurement_home_workspace.js/.css` (included by `hooks.py:61,88`), `procurement_home/` services/api/seed/tests, `setup/procurement_home_page.py`, and "Procurement Home" route references in about 15 Vue screens and bundles (breadcrumb "Home" → `Workspaces/Procurement Home`), `kt_desk_document_title.js`, `kt_cl_components_gallery_page.js`, `SystemSetup.vue`, `ReferenceData.vue`.

**Decision:** Left alone. Many Industry screens use "Home" breadcrumbs that point to the legacy workspace; whether those should point to `/app/home` is an owner question, logged as FU-HOME-21. Uncommitted CTX v1.1 edits to `procurement_home/` belong to another change.

## 5. ERPNext `Home` workspace

Files in `erpnext`: `erpnext/setup/workspace/home/home.json`, `erpnext/desktop_icon/home.json`, `erpnext/workspace_sidebar/home.json`. On `kentender.midas.com` the Workspace `Home` is `public=1, is_hidden=0, app=erpnext`; `Procurement Home` is `public=1, is_hidden=1`. Frappe's `router.js` resolves `frappe.workspaces[route[0]]` at line 171 and falls back to `frappe.workspaces["home"]` at line 489 when picking a default route.

No Kentender code references the ERPNext workspace, so nothing in the repo depends on it. Hiding it does change the default-route fallback and removes the ERPNext desktop icon and sidebar entry for it; Phase 6 (HOME6-0601, 0602) verifies both on the test site before the patch ships. Because ERPNext's JSON is re-imported on migrate, the patch must hide the workspace after import each time (a fixture or `after_migrate` step, not a one-off edit); to be settled in Phase 6.

## 6. Sidebar and sidebar contract tests

- `workspace_sidebar/procurement.json:15` item "Home" → `coming-soon` (route option `{"feature":"Home"}`); "Analytics" likewise.
- `setup/sidebar_availability.py:23` lists "Home" in `PLANNED_SIDEBAR_LABELS`.
- Tests that name it: `setup/tests/test_procurement_sidebar_g0_012_contract.py:40,138`, `setup/tests/test_workspace_sidebar_fastpath.py:51`, `tests/test_home_placeholder_page_access.py`. The memory note on the sidebar notes `bench migrate` rewrites the Procurement sidebar JSON, and the file has uncommitted edits ("Procurement meetings") from OVS, so Phase 6 edits must not clobber them.

**Decision:** Phase 6 edits these three tests with the sidebar change.

## 7. Pages named `home`

No Page directory named `home` exists in the repository (`find` over `*/page/home*` returned nothing, 4 Oct 2026), and the explorer found no DocType named `home` on the test site. The route slug is therefore free once the ERPNext workspace is hidden. `tests/test_home_placeholder_page_access.py` documents that the rail's "Home" entry and the Procurement app tile both route to `/desk/coming-soon?feature=Home`; that test and its premise change when Phase 6 points the entry at the real page.

## Update, 5 Oct 2026 (HOME6-0607)

My Work's Page is retired. The `kt_my_work_providers` hook and `my_work.py` service remain (FU-HOME-47). Home gained `kt_home_technical_providers` (core: Technical Operator's support issues) and the suppliers app's `kt_home_providers` entry (suspended accounts).
