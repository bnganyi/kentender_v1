# Progress — INT-C second integration gate (core, budget, strategy, suppliers)

Site: kentender-test.local only, every run under `flock /tmp/kt-test-site.lock`, one module per call, 7 Oct 2026, HEAD afdeac99. The site was rebuilt clean from dev and migrated before the gate; INT-D ran the procurement modules concurrently, so the lock queue made this slow. The machine restarted at 19:32 and killed the first run (scratchpad logs lost); every module was therefore run again from a fresh driver (all 156, complete logs). Wave 4R commits under test: `git log --oneline 759685f6..HEAD` (41 commits).

## Summary

| App | Modules | Modules with no tests | Tests run | Modules failing | Failing tests (first full pass) | Failing after rerun |
|---|---|---|---|---|---|---|
| kentender_core | 101 | 9 (doctype stubs and `services.test_clock`) | 916 | 21 | 37 | 37 |
| kentender_budget | 23 | 0 | 246 | 0 | 0 | 0 |
| kentender_strategy | 18 | 0 | 182 in the first pass (the 8 failing modules errored in setUp) | 8 | 92 | 0 (8 modules re-run: 22+9+17+10+11+18+5+7 = 99 tests pass) |
| kentender_suppliers | 14 | 0 | 100 | 0 | 0 | 0 |
| Total | 156 | 9 | about 1,444 | 29 | 129 | 37 |

Modules NOT run: none. All 156 `test_*.py` files were run. (Nine core doctype stubs contain no tests and print no result.)

Classes: R = 0, E = 129 first-pass failures (all of the above), D = 0 decisions newly needed (follow-ups restate earlier ones), unclassified = 0. No commit of code was needed; no guard, test or seed was changed. The only commits are this file (and its first-draft version).

## Regressions (R)

None. Every failing test is the same set INT-A recorded before Wave 4R, each is explained below, and none fails inside a file changed by the Wave 4R commits (checked by comparing the files named in each traceback with `git diff --name-only 759685f6..HEAD`). The only hit was `seeds/kentender_mvp_v1/clear.py` (the User Scope Assignment delete, line 177, changed by 2f1d8df0), which is not where `test_kentender_mvp_v1_seed_contract` fails (line 396, see below). Where a changed file is the subject of the test, the pre-change version was read with `git show` (see test_kt_cl_shell_layout_guard).

## Failing tests (all E)

Core, 21 modules:

- test_backfill_pe_fy_context_links (4 errors) E: setUp does `get_all("Organisation Unit", ...)[0]` for an OU with a procuring entity and gets `IndexError`. Test file and the backfill service untouched since the first gate.
- test_business_action, test_exception_record, test_master_data, test_typed_attachment, test_wave0_smoke, test_workflow_guard (1 error each) E: each inserts a Procuring Entity without `reporting_currency`, `reqd` since 9f1f5cf8 (15 Aug). `procuring_entity.py` was changed in the window (7fe149af, an HTTP-only single-entity check that returns when `frappe.local.request` is None), but the failure is `MandatoryError ... reporting_currency` raised before and independent of it; the fixtures run in-process. See Follow-up 1.
- test_canonical_seed (3 errors: reservation namespace stray, second full run changes nothing, procurement rules fixture-verified; the 3 ladder tests that INT-A fixed pass; 33 of 36 pass) E: `canonical.validate()` fails on residue, not on seed logic (residue list below).
- test_dem_seed_004_orchestrator_demands (1) E: legacy pack expects Budget Line `MOH-BL-DHI-2027`, which the two-year canonical world does not seed.
- test_industry_design_gate (1), test_industry_design_scope (1) E: the Supplier Website shell `templates/kt_portal/base.html` has no `kt-industry` body class and still uses `kt-btn` classes. Neither template nor tests are in the diff.
- test_kentender_mvp_v1_seed_contract (setUpClass error) E: the legacy orchestrator's `_clear_requisitions_playwright_rows_canonical` (clear.py line 396, not the line changed by 2f1d8df0) refuses to reset a requisition whose handoff is consumed and whose Budget reservation is Active (guard from cfda5b8f). The canonical award-stage world has that state by design.
- test_kt_cl_shell_layout_guard (3: `test_code_html_parity_markers_in_implementation`, `test_planning_surfaces_are_registered`, `test_procurement_page_controllers_are_page_scoped`) E: (a) the class string lives in `public/js/kt_cl_code_spec.js` and the `planning_item_editor_page.js` page_js wiring, neither in the diff; (b) `planning-workspace` is not in `kt_cl_surface_registry.js` at 759685f6 either (`git show 759685f6:...kt_cl_surface_registry.js | grep -c planning-workspace` is 0; last present in 66440949/bf96c913, weeks ago). The test file was edited in 9756d5f4 only to replace `test_surface_registry_exports_ui00`, and that replacement test passes.
- test_module_registry (2), test_stitch_desk_chrome_gate (2) E: stale checks of retired routes/files (`form/demand`, `demands`, `planning_ui_fixtures/workspace.js`, `procurement-plan-update`). Untouched.
- test_portal_runtime (1) E: asserts a one-line `<a href="/tenders" data-kt-portal-nav="tenders" aria-current="page">`; the template renders the attributes over several lines (same cause as INT-B R-1's second half). Untouched; also uses `set_request`, see Follow-up 4.
- test_procurement_settings (1: `test_a_schedule_nobody_uses_and_that_has_not_started_is_corrected_in_place`) E: probe shows Annual Plan Items APIR-309131 (namespace KENTENDER_REQ_PLAYWRIGHT, 19:57 today) and APIR-308582 (KENTENDER_TEST, 19:25) with `schedule_profile_version = SPR-OPEN-TENDER-GOODS-V2`, the exact name the test creates, so the new version reads as already used. Residue from Requisitions/Planning tests (INT-D), not from these commits.
- test_reference_data_seed_mvp1 (3 errors), E: "This Procuring Entity is not active": the legacy multi-PE seed enables PE-NSSF/PE-CGKIS, which do not exist on a one-entity site.
- test_seed_v1 (1) E: queries column `strategic_plan_name`, which no longer exists.
- test_stable_platform_seed (3 errors) E: `tabDemand` does not exist (no Demand doctype in the repo). The sibling `test_demo_platform_seed` file was deleted by the retirement commit 9756d5f4 together with the demo seed, so that module no longer exists.
- test_technical_read_conformance (3 errors + 1 failure) E: Bid Opening resolver declares `route` as a string (`TypeError: 'str' object is not callable`), and Administrator (System Manager) makes `tenders.get_tender_publication.can_configure` true. Not in the diff for these two causes.
- test_artboard_provenance_gate (module-level error on re-run, passed the first time) E: the test loads ERPNext test records, which re-insert `_Test Fiscal Year 2040..2050`; it errors with "overlapping with Fiscal Year 2040-2041". Fiscal Year `2040-2041` (created 20:16:55) is the year the Strategy test fixture `ensure_fiscal_year(2040)` creates, left behind by the Strategy re-run after I deleted the ERPNext `_Test Fiscal Year 2040..2050` rows (below). Same collision in the other direction as the Strategy one; no code in the diff is involved. It passed in the first pass while the ERPNext rows were still present.

Strategy, 8 modules, 92 errors in the first pass (test_str_aud_remediation 22, phase2_lifecycle 9, phase4_contracts 17, phase7_ui_contracts 10, v1_7_correction 11 (+6 in a sibling class), v1_8_usability 18, discard_draft 5, idempotency_envelope 7; test_str_technical_read and the rest pass) E: all one error, `Year start date or end date is overlapping with Fiscal Year _Test Fiscal Year 2040` from `tests/fixtures.py::ensure_fiscal_year(2040)` (ERPNext Fiscal Year overlap validation). The ERPNext `_Test Fiscal Year` rows (created 18:24:50 by an ERPNext test-record load, during the core modules) are fixtures of ERPNext, and `kentender_strategy/tests/fixtures.py` is not in the diff. As in INT-A I deleted `_Test Fiscal Year 2040`..`2050` (11 throw-away rows, test site only) and re-ran the 8 modules: all pass (99 tests), which verifies the Strategy command-journal change (cdd4f8cc) and the new `test_str_rg_residue` (passes in the first pass).

Budget (23 modules, 246 tests) and Suppliers (14 modules, 100 tests): all pass, including the new Budget modules (`test_budget_locking_races`, `test_database_guards_install`, v19 usability) and the rewritten Suppliers authorization/workbench/smoke tests (7bb5e983).

## Residue observed (test site)

`canonical.validate()` after the full run reports (so the next canonical-dependent run needs a rebuild, as the coordinator expects):

- 15 Organisation Units where 4 are expected;
- non-canonical Fiscal Year `2040-2041` (Strategy fixture) plus 2101-2102 / 2103-2104 seen mid-run;
- fixture-domain users outside the register: `nds.test.*`, `bud.*.4e3409@test.local` (Budget tests), `plnt.*`, `evlt.*`, `bopt.*`, `bdst.*`, `tndt.*`, `reqt.*`, `test*@example.com`;
- extra Budgets named `MOH-BUD-3393-001`, `3296`, `3199`, `3102`, `3005`, `2908`, ... (Budget test modules leave one Budget per test year behind), plus `BUD-PLNT-0001` earlier;
- Funding Reservations outside the REQ namespace (`gmmg18henq`, `gmme0ohstf`, `ucqtqjv3bg`) and 6 Procurement Commitments outside it.

Probe: `bench --site kentender-test.local execute kentender_core.seeds.canonical.validate` mid-run (after 8 modules, after test_canonical_seed) and at the end. The Budget budgets/users and `_Test Fiscal Year` interactions are from this app group; the `plnt`/`evlt`/`bopt`/`bdst`/`tndt`/`reqt` users and reservations come from INT-D's procurement modules.

Test-site data change made by me: deleted ERPNext `_Test Fiscal Year 2040`..`2050` (11 rows). Nothing else, and nothing on dev.

## Follow-ups

1. (D, carried from INT-A D-1) seven core tests create a Procuring Entity without `reporting_currency`. Recommended: set `reporting_currency="KES"` in those fixtures (separate `test(core)` commit). Not done: pre-existing, outside the Wave regressions.
2. (D, carried) Strategy tests need a fiscal-year window that cannot collide with ERPNext test years (and Strategy's `ensure_fiscal_year(2040)` leaves `2040-2041` behind, which in turn breaks `test_artboard_provenance_gate`). Recommended: move it to the >= 2100 window used by the other modules and delete the year in tearDown.
3. (D, carried) Budget test modules leave a Budget per test year and `bud.*@test.local` users behind; add a purge cleanup per memory rule "always remove test data".
4. (D) `test_portal_runtime` uses `frappe.utils.set_request` without restoring `frappe.local.request` (INT-B follow-up 3); with the new maintenance-write guard it can refuse later fixtures in the same process. Not hit here only because it is the last test in its module.
5. (D, carried) legacy seed/shell/registry tests listed above should be retired or repaired; they hide signal.
6. (D, carried) Bid Opening technical-read resolver `route` string, and the Administrator `can_configure` probe.

## Needs browser check

None.

## Dev site actions needed

None (no schema, patch or seed change committed).

## Document follow-ups

None.

## Commands run

- Driver (one module at a time, 156 modules in two passes): `cd /home/midasuser/frappe-bench && flock /tmp/kt-test-site.lock timeout 1500 bench --site kentender-test.local run-tests --app <app> --module <module>`, plus `canonical.validate` every 8 or 10 modules.
- Re-run of the 8 Strategy modules after deleting the 11 ERPNext `_Test Fiscal Year 2040..2050` rows (a throw-away script under `bench execute`, removed afterwards): all OK.
- Read-only probes under the lock: Annual Plan Item schedule-profile pins, Organisation Unit and Fiscal Year listings, `canonical.validate()`.
- `git diff --name-only 759685f6..HEAD` compared with the files in each failing traceback; `git show 759685f6:kentender_core/kentender_core/public/js/kt_cl_surface_registry.js` for the registry.
- Not run: Playwright, migrate, site rebuild, anything on dev, any baseline run with files swapped back.
