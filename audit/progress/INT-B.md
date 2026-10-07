# Progress — INT-B integration gate, kentender_procurement Python tests

Site: kentender-test.local (flock /tmp/kt-test-site.lock, one module per call). Run 7 Oct 2026, HEAD at start ~e015391a + this worker's commits.
Scope: all 302 `test_*.py` modules under kentender_procurement (find kentender_procurement -name 'test_*.py').

## Summary

| Result | Modules | Tests |
|---|---|---|
| Pass (OK, incl. 8 with skips) | 258 | about 2,900 (2,976 counted over the 283 modules that ran, less the failing ones) |
| Fail (FAILED) | 25 -> 24 after fix | 21 failures + 27 errors -> 20 failures + 24 errors after fix |
| Not run, no tests collected | 19 | 0 (3 are doctype controllers named `test_*` with no tests; 16 `tender_configurations` modules fail at ERPNext test-record loading, see E-4) |
| Total | 302 | 2,976 counted by "Ran N" over the 283 modules that ran |

Class counts of the 48 failing/erroring tests before fixes: R = 4 (all one cause, fixed), E = 43, unclassified = 1 module (transient, passes on rerun). D = 0 (follow-ups listed below are suggestions, not blockers).

After fixes: 0 regressions open. 44 failing tests remain, all E (pre-existing / site data / ERPNext fixtures), plus 1 transient.

## Per-module table (failing, not-run, and the one fixed module)

| Module | Tests | Fail+Err | Class |
|---|---|---|---|
| bid_submission.tests.test_available_tenders | 7 | 1F+3E -> 0 after fix | R (fixed, 759685f6) |
| bid_evaluation.tests.test_evl_canonical_seed | 1 | 2E (one run) | unclassified, transient; passes on rerun (39.8 s) |
| bid_evaluation.tests.test_evl_intake | 6 | 1F | E-1 |
| bid_submission.tests.test_acceptance_gaps | 27 | 1F | E-2 |
| departmental_needs.tests.test_departmental_needs_architecture | 8 | 2F | E-3 |
| departmental_needs.tests.test_departmental_needs_lifecycle | 86 | 1E | E-4 |
| departmental_needs.tests.test_departmental_needs_seed | 28 | 1F | E-5 |
| departmental_needs.tests.test_home_provider | 29 | 3F | E-6 |
| procurement_lifecycle.tests.test_r3_014_current_stage_calculator | 12 | 2E | E-7 |
| procurement_lifecycle.tests.test_r3_019_permission_filtering | 27 | 1F+2E | E-7 |
| procurement_lifecycle.tests.test_r4_013_technical_evidence_drawer | 1 | 1E | E-7 |
| procurement_lifecycle.tests.test_r5_002_procurement_journeys_for_strategy_node | 5 | 3E | E-7 |
| procurement_planning.tests.test_dead_end_matrix | 1 | 1F | E-8 |
| procurement_requisitions.tests.test_draft_commands | 18 | 1F | E-9 |
| procurement_requisitions.tests.test_read | 11 | 1F | E-9 |
| procurement_requisitions.tests.test_ovs_requisition_reads | 5 | 1F | E-9 |
| setup.tests.test_g0_015_cross_app_workspace_boot | 3 | 1F | E-10 |
| setup.tests.test_procurement_home_page_roles | 6 | 1F | E-10 |
| setup.tests.test_procurement_sidebar_g0_012_contract | 8 | 2F | E-10 |
| tenders.tests.test_read | 10 | 3F | E-11 |
| tender_configurations.tests.test_bidder_stitch_contract_gate | 3 | 1E | E-12 |
| tender_configurations.tests.test_f1_bidder_submission_schema_on_confirm | 1 | 1E | E-12 |
| tender_configurations.tests.test_publication_setup_api | 8 | 8E | E-12 |
| tender_configurations.tests.test_published_tender_overview_web | 2 | 2E | E-12 |
| tender_configurations.tests.test_tender_configuration_dashboard_api | 0 | 1E (setUpClass) | E-12 |
| 16 tender_configurations modules (cfg09_ensure_std_rows, cfg09_no_invented_hydrate, configuration_*_api x12, step_progress, ui01_mockup_seed) | not run | import-time error | E-4b |
| bid_submission.doctype.test_trust_certificate / test_trust_signature, departmental_needs.doctype.departmental_need.test_departmental_need | not applicable | no tests | doctype controllers/stubs named test_*; nothing to run |

All other modules passed (OK). Full per-module list with counts and times: scratchpad `intb/summary.tsv` (not in repo); every log kept in the same folder.

## Regression found and fixed

- R-1 `bid_submission.tests.test_available_tenders` (3 errors + 1 failure). Cause: `test_a_guest_receives_the_portal_page_with_the_first_payload` calls `frappe.utils.set_request`, which leaves `frappe.local.request` set. Commit 701a2edf (command-write guard, AUD-XC-010) makes `maintenance_write` refuse while a request is present, so every later test's Tender fixture wipe in the same process raised `CommandWriteError: Maintenance writes are not available here` (setUp errors in 3 tests). The same test also asserted `data-kt-portal-nav="tenders" aria-current="page"` on one line, but the portal template (UI rework d7b8de9b, not an audit commit) renders those attributes across lines; that is the 1 failure. Fix (test only, no guard weakened): restore `frappe.local.request` in a cleanup and match the attributes with `\s+`. Commit `759685f6` "test(bid-submission): the portal-page test restores frappe.local.request so later fixture wipes are not refused (Refs AUD-XC-010)". Rerun: 7 tests OK.
  - Same `set_request` pattern exists in `tender_configurations/tests/test_published_tender_overview_web.py` and `kentender_core/tests/test_portal_runtime.py`; the first could not be exercised (E-12) and would leak the request the same way once its fixture works; the second belongs to the core worker. See Follow-ups.

## Environmental / pre-existing (E) with evidence

- E-1 `test_evl_intake::test_a_final_no_bids_opening_closes_the_preparation`: `titles(AO)` is not scoped to the test's tender; the canonical world's seeded case EVL-MOH-2026-010 (Preparing, no committee, created by the seed) gives the AO "Appoint evaluation committee for TND-MOH-2026-010". Assertion dates from 1abddfbe (Sep); no today commit touches that task code.
- E-2 `test_acceptance_gaps::test_every_action_a_read_emits_has_exactly_one_mapping`: 7 unmapped labels ("Company and declarations", "Tender documents", "Requirements", "Review", ...) are task-flow labels introduced in beed7f36 (2 Oct); test last changed 28 Sep. No today commit touches `task_flow`/`bid_context`.
- E-3 `departmental_needs_architecture` (2): `procurement_planning/seeds/kentender_mvp_v1.py` imports `departmental_needs.seeds.kentender_mvp_r1` (line 348) and does `get_all("Departmental Need")` (line 1214); both lines blamed to bedf8a5b (5 Oct), not today.
- E-4 `departmental_needs_lifecycle::test_selectable_years_and_workspace_filtering_span_two_fiscal_years`: ERPNext `_Test Fiscal Year 2028` overlaps the test's 2028-07-01..2029-06-30 year. E-4b: the 16 `tender_configurations` modules die at load with "Year start date or end date is overlapping with Fiscal Year 2040-2041" (ERPNext test-record Fiscal Year fixture vs a seeded year).
- E-5 `departmental_needs_seed::test_the_cleared_variant_supplies_no_plan_references`: `test_departmental_needs_contracts` (runs earlier, alphabetical) leaves a Planning usage projection for NDS-MOH-2027-0001 dated now+1 year (its own `later()` helper); the profile's AS_AT (18 Jun 2027) event is then an older event and correctly ignored, so usage stays "Fully included". Verified by applying the profile and reading the projection (source_event_time 2027-10-07). Test-order residue, test code untouched by the guard commits.
- E-6 `departmental_needs.test_home_provider` (3): all three are julia.njeri (acting Head, assignment URA-17470 effective_to 2025-12-01, expired at the real clock). Seed row last modified 5 Oct; not changed today.
- E-7 `procurement_lifecycle` (8 tests across 4 modules): `Procurement Journey JRN-MOH-2026-001` / `Procurement Handoff Card PKGREL-MOH-2026-001` do not exist (legacy demo rows, deliberately cleared by `canonical.py` `_LEGACY_DEMO_DOCTYPES`; `tabProcurement Journey` count 0), user `tender.seed.auditor@test.local` does not exist, and `tabStrategy Objective`/`tabStrategy Target` tables were dropped by the Strategy v1.7 correction. Today's lifecycle commits (7aa419cc TM2 removal) do not create these conditions.
- E-8 `procurement_planning.test_dead_end_matrix`: `plnt.hopf@example.test` holds a stray "Head of User Department" grant on OU-MOH-02527 (URA-17654, namespace KENTENDER_TEST). The Requisitions fixture `procurement_requisitions/tests/fixtures.py:85` (git blame cfda5b8f, 7 Sep) grants that to the shared Planning HOPF user and does not revoke it, so the Planning guidance names the HOPF among the people to wait for. The failing line is the matrix's "told to wait for themselves" rule. Pre-existing cross-module fixture residue.
- E-9 `procurement_requisitions` (3): 16 Funding Reservations from the canonical seed (namespace KENTENDER_MVP_1_R1_REQ, dated up to 2027-06-10) make `count("Funding Reservation", calling_module=Requisitions)` 16 not 0; the OVS list's first page of 10 is full of seeded 2027-dated requisitions, so the new one is not on it.
- E-10 `setup` (4): `test_procurement_sidebar_g0_012_contract` x2 is the documented pre-existing drift (memory note procurement-sidebar-g0012; sidebar now has "Procurement meetings"); `test_g0_015...strategy_workspace_shell` is the documented open FU-03 in the test's own docstring; `test_procurement_home_page_roles` lists legacy users (requisitioner@moh.test, hod.approver@moh.test, esther.njeri, nadia.kamau) whose roles are not in LANDING_ROLES. `setup/` files changed today only by 7aa419cc (two lines of `tender-management-v2`).
- E-11 `tenders.test_read` (3): the Officer's workspace counts include the canonical world's Tenders (read live: TND-MOH-2026-014 "Returned to you", 11 other canonical Tenders), so "returned", "ready" and "awaiting approval" counts are one higher than the single record each test creates. `wipe_all` is scoped to test years >= 2100 (by design) so the seeded rows stay.
- E-12 `tender_configurations` (13 tests): `DocType Procurement Package not found` (doctype removed 10 Aug, 12ab75e2) and `www/tenders/review_and_validate.html` missing (removed 26 Sep, d55ef1bf). Neither is touched by today's commits.

## Unclassified

- `bid_evaluation.tests.test_evl_canonical_seed`: first run (during the sweep) errored 2x with `EVL_SOURCE_INCOMPLETE` at "take up the completed opening" after wipe + reseed (9 s). A diagnostic read of the same completion immediately afterwards showed all 4 packages `Accepted/Verified` and `sources.release` fine; the rerun passed in 39.8 s. Cause of the single failure not found; most likely a transient world state from a concurrent writer to the shared database. Not reproduced. Worth one more run in the lead's final sweep.

## Follow-ups

1. (D, small) Requisitions fixture `restore_site` should revoke the HOPF "Head of User Department" grant (E-8), and `test_departmental_needs_contracts` should restore the usage projection it leaves dated in the future (E-5); both make unrelated modules fail depending on run order.
2. (D) Several tests assume an empty site (E-1, E-9, E-11) and fail against the two-year canonical world; decide whether tests should scope to their own records or the suite should run on a site without the canonical world.
3. Test hygiene: `set_request` users should restore `frappe.local.request` (pattern in 759685f6): `tender_configurations/tests/test_published_tender_overview_web.py` and `kentender_core/tests/test_portal_runtime.py` (core worker).
4. 16 `tender_configurations` modules never load on this site because of the Fiscal Year overlap with ERPNext's test records; they are not exercising the Tender configuration guards at all in this sweep. Needs an owner decision on those retired-feature tests (E-4b, E-12 reference removed doctypes).
5. `departmental_needs/doctype/.../test_departmental_need.py` and the two `test_trust_*` doctype folders contain no tests; harmless.
6. The working tree has an uncommitted change to `kentender_procurement/workspace_sidebar/procurement.json` (not mine; relates to E-10 sidebar tests).

## Needs browser check

None.

## Dev site actions needed

None (no migrate, patch or schema change by this worker).

## Document follow-ups

None.

## Commands run

- Driver (one module at a time, 302 modules): `flock /tmp/kt-test-site.lock timeout 540 bench --site kentender-test.local run-tests --app kentender_procurement --module <dotted.module>`; results above (258 OK, 25 FAILED, 19 not run).
- Diagnostics (read-only or fixture-scoped, under flock, test site only): apply/reset of the `withdrawal_cleared` Needs profile and projection read; reads of Evaluation Case, User Responsibility Assignment, Funding Reservation, Procurement Journey; `tenders.services.read.get_tenders_workspace` for the Tenders test Officer after `fx.ensure_world()`.
- After fix: `... --module kentender_procurement.bid_submission.tests.test_available_tenders` -> Ran 7, OK. `... --module kentender_procurement.bid_evaluation.tests.test_evl_canonical_seed` rerun -> Ran 1, OK.
- Commit: `759685f6` (explicit path `test_available_tenders.py` only; no PNG staged).
