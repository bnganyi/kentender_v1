# Progress — INT-D second integration gate, kentender_procurement Python tests

Site: kentender-test.local only (flock /tmp/kt-test-site.lock, one module per call). 7 Oct 2026, HEAD afdeac99 at start. INT-C ran core/budget/strategy/suppliers on the same site concurrently.
Scope: 273 `test_*.py` modules under kentender_procurement (the Tender Configurations modules no longer exist). Method: one module per call, canonical validate after each module from module 38 on.

STATUS: BLOCKED after module 55 of 273 by one orphan row on the test site (see Blocker). The machine restarted at 19:32 and killed the first session; the scratchpad logs were lost. The table below is what had been observed before the kill; the sweep resumes after `bid_evaluation.tests.test_evl_preparation` (module 43 of 273). Counts for modules 1 to 37 were seen as OK without per-module counts being kept.

## Observed before the restart

| Range | Modules | Result |
|---|---|---|
| award.tests.* (first 20 modules, test_analytics_facts to test_awd_opinion) and following alphabetically through bid_evaluation.tests.test_evl_errors | 37 | all OK (no non-OK row in the driver summary) |
| bid_evaluation.tests.test_evl_funding | 4 tests | OK |
| bid_evaluation.tests.test_evl_intake | 6 tests | FAILED (failures=1) - not yet triaged here; same module and symptom as INT-B E-1 (to be confirmed against its traceback on re-run) |
| bid_evaluation.tests.test_evl_manifest | 11 | OK |
| bid_evaluation.tests.test_evl_meetings | 8 | OK |
| bid_evaluation.tests.test_evl_oversight | 19 | OK |
| bid_evaluation.tests.test_evl_preparation | 4 | OK |

## Canonical validate / residue
Valid (`ok: true`) before the run began. After award module 20 and on every check after that, validate failed with the same set: 6 Organisation Units where 4 expected, Fiscal Years 2101-2102 and 2103-2104, fixture-domain users (plnt.*, reqt.*, testpassword@example.com...), Budget BUD-PLNT-0001, one stray Funding Reservation (a different name each check), and the site test clock unset. The set was already complete at the first check, so it cannot be attributed to a single procurement module; plnt.*/reqt.* users and BUD-PLNT-0001 point to planning/requisitions fixtures that the award/evaluation test worlds build on, and INT-C's core modules ran in the same window. To be attributed by a single-module before/after check at the end.

## Blocker (needs the coordinator or owner)
One orphan row, `Annual Plan Version PLN-MOH-2101-001-V1` (namespace KENTENDER_TEST, created 19:25, no parent Annual Plan; cause: a test process killed mid-run by the 19:32 restart, before its fixture wipe could run). Every module whose fixture calls `ensure_annual_plan(fiscal_year='2101-2102')` now errors at setUp with `DuplicateEntryError ... 'PLN-MOH-2101-001-V1'`. Verified by a read: it is the only Annual Plan Version without a plan. I tried to delete it with one SQL statement on the test site and the permission classifier denied the action, so I left it. Needs: `delete from "tabAnnual Plan Version" where name='PLN-MOH-2101-001-V1'` on kentender-test.local (test site, throw-away fixture row), then the sweep resumes from bid_evaluation.tests.test_evl_intake.

Modules run after the restart that hit this blocker (all setUp errors, class E: residue of the killed run, not a regression): test_evl_intake (6), test_evl_reads (5), test_evl_report (14), test_evl_seams (6), test_evl_separation (8), test_evl_stage_summary (14), test_evl_tables_end_to_end (2), bid_evaluation.tests.test_home_provider (35), bid_opening.tests.test_analytics_facts (1), bid_opening.tests.test_bop_api (5). test_evl_rules (20) and test_evl_schema (7) pass. These ten must be re-run after the row is removed; the earlier INT-D observation that test_evl_intake FAILED (failures=1) before the restart still needs its traceback.

## Failures triaged
(none classified as R/E/D on merit yet; the sweep is incomplete)

## Follow-ups
## Commands run
- Driver: `flock /tmp/kt-test-site.lock timeout 540 bench --site kentender-test.local run-tests --app kentender_procurement --module <m>` then `flock ... bench --site kentender-test.local execute kentender_core.seeds.canonical.validate`.
