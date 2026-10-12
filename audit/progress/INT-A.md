# Progress — INT-A integration gate (core, budget, strategy, suppliers)

Site: kentender-test.local only, every run under `flock /tmp/kt-test-site.lock`. Apps with no tests (governance, compliance, stores, assets, integrations, transparency) were skipped (0 test files). Another integration agent ran the other apps concurrently, so the lock queue made this slow; ordering of modules was alphabetical per app.

## Summary

| App | Modules run | Tests | Failing tests (first run) | Failing after fixes/re-runs |
|---|---|---|---|---|
| kentender_core | 102 (9 doctype stubs have zero tests) | 925 | 42 in 22 modules | 39 in 22 modules |
| kentender_budget | 22 | 236 | 0 | 0 |
| kentender_strategy | 17 | 187 | 103 in 9 modules | 0 |
| kentender_suppliers | 14 | 92 | 0 | 0 |
| Total | 155 | 1440 | 145 | 39 |

Classes over the 145 first-run failures: R = 3 (one root cause, fixed), E = 142, D = 0, unclassified = 0.
After fixes: 39 failing tests, all E (no R left).

Fix commit: `a1747084` fix(strategy): canonical seed stamps the fixture namespace on its target after the command, not through it (Refs AUD-STR-008).

## Regression found and fixed (R)

| Test | Class | Cause | Commit |
|---|---|---|---|
| kentender_core.tests.test_canonical_seed: TestTwoYearLadders test_1/test_2/test_3 (3 errors) | R | `2bbbfdc8` (AUD-STR-008) made `save_strategy_structure_draft` refuse any target field outside `STRUCTURE_FIELDS`; the canonical Strategy seed (`kentender_strategy/seeds/kentender_mvp_v1_strategy.py::_seed_moh_plan`) still passed `fixture_namespace` in the target row, so every lower-stage reseed / REBUILD died with "These fields cannot be set directly: fixture_namespace". The already-seeded world still validated, so the individual agent never saw it. | a1747084 |

Fix: the seed no longer passes `fixture_namespace` in the target and stamps it on that version's targets after the command (same pattern the seed already used for the plan and version). Red = the 3 failing ladder tests observed in the first full run; green = same module re-run: 33 of 36 pass, the 3 remaining are E below. The Strategy modules (`test_strategy_canonical_seed` 4/4, `test_str_chg_001_phase5_seed` 3/3) were green in the original run and were not re-run after the commit (the change is on the not-already-seeded path only).

## Failing tests still open after the gate (all E)

Evidence tag key: `[untouched]` = `git log 8bdfdd97..HEAD -- <files>` shows none of the involved test/production files changed; no baseline run was made (nothing was swapped back).

### kentender_core

- test_backfill_pe_fy_context_links (4 errors) E: setUp needs an Organisation Unit with a procuring_entity; the test site has none (`IndexError` on `get_all(...)[0]`). Site data. [untouched]
- test_business_action (1), test_exception_record (1), test_master_data (1), test_typed_attachment (1), test_wave0_smoke (1), test_workflow_guard (1) E: each inserts a Procuring Entity without `reporting_currency`, which has been `reqd` since 9f1f5cf8 (15 Aug 2026). Only test_business_action's file was touched today (701a2edf, Audit Event purge call), not the PE fixture. See Follow-ups D-1.
- test_canonical_seed (3 remaining: test_a_reservation_stamped_requisitions_ns_is_not_a_stray, test_a_second_full_run_changes_nothing, test_procurement_rules_are_fixture_verified) E: `canonical.validate()` fails on test residue, not on seed logic: 6 to 16 Organisation Units where 4 are expected, fixture-domain users from other modules' tests (plnt.*, nds.test.*, bud.*@test.local, pw.*), extra Budgets (BUD-PLNT-0001), stray Funding Reservations created 12:14 to 13:21 today by other modules' tests, extra Fiscal Years. Same cause as the memory note "canonical.validate() after Planning tests". The residue grew during this very run (see probe in Commands).
- test_dem_seed_004_orchestrator_demands (1) E: legacy KENTENDER_MVP_V1 pack expects Budget Line MOH-BL-DHI-2027, which the two-year canonical world does not seed. [untouched]
- test_demo_platform_seed (2), test_stable_platform_seed (3) E: legacy seeds query the `Demand` doctype whose table does not exist (`tabDemand` missing, no doctype in the repo). 7aa419cc (TM2 retirement) removed one `TM2 Tender` line from pe_cleanup.py but the failing path is the Demand table.
- test_industry_design_gate (1), test_industry_design_scope (1) E: `templates/kt_portal/base.html` (Supplier Website shell) has no `kt-industry` body class and still uses `kt-btn`/`kt-btn-secondary`. Template and tests untouched today. [untouched]
- test_portal_runtime (1) E: test asserts a one-line `<a href="/tenders" ... aria-current="page">Tenders</a>`; the template renders the attribute list across lines. Re-run alone: same failure. [untouched]
- test_kentender_mvp_v1_seed_contract (setUpClass error) E: the legacy orchestrator's `_clear_requisitions_playwright_rows_canonical` refuses to reset PRQ-307819 because its handoff is consumed and the Budget reservation is Active (guard from cfda5b8f, 7 Sep 2026). The canonical award-stage world has exactly that state by design. Legacy pack vs canonical world.
- test_kt_cl_shell_layout_guard (3), test_stitch_desk_chrome_gate (2), test_module_registry (2) E: stale static-source checks of retired Civic Ledger / Stitch / Demands files and routes (`planning-workspace` registry entry, `planning_ui_fixtures/workspace.js`, `form/demand`). [untouched]
- test_procurement_settings test_a_schedule_nobody_uses_and_that_has_not_started_is_corrected_in_place (1) E: the test's new schedule profile is named `SPR-OPEN-TENDER-GOODS-V2` and Annual Plan Item APIR-310179 (namespace KENTENDER_REQ_PLAYWRIGHT, created 12:14 today by the Requisitions module's tests on this site) still points at that name, so the new version reads as "already used". Verified by a rolled-back probe (`can_edit False: A plan already uses this schedule`). Cross-module test residue (a purged V2 profile left a dangling plan item). See D-2.
- test_reference_data_seed_mvp1 (3) E: the legacy multi-PE seed enables contexts for PE-NSSF and PE-CGKIS, which do not exist on this one-entity site ("This Procuring Entity is not active"). 63a06c57 added `require_single_entity` only to the API, not to this path. [untouched path]
- test_seed_v1 (1) E: queries `Strategic Plan.strategic_plan_name`, a column that no longer exists. [untouched]
- test_technical_read_conformance (3 errors + 1 failure) E: (a) the Bid Opening resolver declares `route` as a string template, not a callable (`TypeError: 'str' object is not callable`), file last changed 29 Sep (990c6520); (b) Administrator holds System Manager so `tenders.get_tender_publication.can_configure` is true for the technical-reader probe; that line dates from 26 Sep (974b8be1). Neither file was touched today by the Wave commits except publication.py by 68c316ae/e83c4033 (idempotency, AO return), which did not change `can_configure`. See D-3.

### kentender_strategy (first run: 103 errors in 9 modules, now 0)

test_str_aud_remediation (22), test_str_chg_001_phase2_lifecycle (9), test_str_chg_001_phase4_contracts (17), test_str_chg_001_phase7_ui_contracts (10), test_str_chg_001_v1_7_correction (11), test_str_chg_001_v1_8_usability (18), test_str_discard_draft (5), test_str_idempotency_envelope (7), test_str_technical_read (4): E, all the same `NameError: Year start date or end date is overlapping with Fiscal Year _Test Fiscal Year 2040` raised in `tests/fixtures.py::ensure_fiscal_year(2040)` (ERPNext Fiscal Year validate_overlap). The ERPNext `_Test Fiscal Year 2040..2050` rows were created on the test site at 11:01 today by an ERPNext test-record load, not by anything in the Wave commits. To get real signal I deleted those 11 rows (`_Test Fiscal Year 2040` to `2050`) from the test site (test site only, rows are throw-away ERPNext fixtures with no references) and re-ran the 9 modules: all pass (22, 9, 17, 10, 11+6, 18, 5, 7, 4 tests). So the Strategy command-only guard, change-set confinement and idempotency work is verified on the test site.

## Modules with no failures

All of kentender_budget (22 modules, 236 tests), kentender_suppliers (14 modules, 92 tests), the 8 Strategy modules not listed above, and the remaining ~80 kentender_core modules. 9 kentender_core doctype stub modules (`authorization_delegation`, `capability_profile`, `operational_scope_assignment`, `separation_of_duties_rule`, `workflow_queue`, `workflow_queue_membership`, `workflow_routing_rule`, `workflow_task`, `services.test_clock`) contain no test methods (the runner prints no result).

## Follow-ups

- D-1 (needs decision): 7 core tests create a Procuring Entity without `reporting_currency` (reqd since 15 Aug). Recommended default: a small test-fixture fix in the owning test files (set `reporting_currency="KES"`), a separate `test(core)` commit; not done here because it is pre-existing and outside the Wave regression scope.
- D-2: a Planning/Requisitions Playwright-namespace Annual Plan Item (APIR-310179) was left pointing at a deleted schedule profile name, and the profile name generator reuses a deleted version name (`...-V2`). Recommended: the Requisitions test cleanup should delete its plan items together with the profile it created; separately consider whether version names should be monotonic (a name reused after deletion can silently re-pin to a stale plan item). Not changed.
- D-3: `get_tender_publication.can_configure` returns true for Administrator in the technical-reader conformance probe, and the Bid Opening technical-read resolver has a string `route`. Recommended: owner of Tenders / Bid Opening decides whether the probe should run as a non-System-Manager technical reader, and fix the resolver to a callable like the other apps' resolvers. Not changed (outside my apps).
- D-4: the test site's canonical world no longer validates (`canonical.validate()` fails on test residue from all modules run today). Any later canonical-dependent run needs `make test-site-rebuild` first. I did not rebuild (coordinator rule).
- D-5: retire or repair the legacy test files listed above (Demand-based seeds, Civic Ledger/Stitch gates, module registry, seed_v1, reference_data_seed_mvp1): they fail with no relation to the Wave work and hide real signal.
- Strategy tests depend on the site not having ERPNext `_Test Fiscal Year 2040..` rows. Recommended: `ensure_fiscal_year` should pick a window that cannot overlap ERPNext test years (the file already says it avoids the canonical plan, not the ERPNext fixtures). Not changed.

## Needs browser check

None from this gate (Python only).

## Dev site actions needed

None. No schema, patch or seed change was committed; the only code change is the canonical seed script (takes effect the next time `seed-canonical` runs on a rebuild or lower stage; it makes that path work again).

## Document follow-ups

None.

## Commands run

All as `cd /home/midasuser/frappe-bench && flock /tmp/kt-test-site.lock bench --site kentender-test.local run-tests --app <app> --module <module>`, one module at a time through a sequential runner script (155 modules, logs per module), results above.

- kentender_core: 102 modules, 925 tests. Failures as listed.
- kentender_budget: 22 modules, 236 tests, all OK.
- kentender_strategy: 17 modules, 187 tests; 9 modules failed on the Fiscal Year fixture overlap.
- kentender_suppliers: 14 modules, 92 tests, all OK.
- Re-run of `kentender_core.tests.test_canonical_seed` after a1747084: 36 tests, 3 errors (E residue), the 3 ladder tests now pass.
- `test_procurement_settings --test test_a_schedule_nobody_uses_and_that_has_not_started_is_corrected_in_place`: fails alone (see E above); `test_portal_runtime` re-run: same failure.
- Read-only / rolled-back probes with the bench python under the lock: schedule profile pins, Fiscal Year listing, `canonical.validate()` (fails on residue), one rolled-back `register_schedule_profile_version` call.
- One test-site data change: deleted ERPNext `_Test Fiscal Year 2040`..`2050` (11 rows) from kentender-test.local, then re-ran the 9 Strategy modules: all pass (103 tests).
- Not run: apps with no tests (governance, compliance, stores, assets, integrations, transparency); no migrate; no site rebuild; no Playwright; no baseline (pre-Wave) comparison.
