# KT-ACCESS-REV-001 — implementation record and follow-ups

Date: 7 October 2026. Companion to `audit/ACCESS_REV_001_INVENTORY.md`.
Instruction: the Project Owner accepted every recommendation in the inventory (AR-09, the D1–D5 decisions) and asked for end-to-end implementation, with anything needing a decision logged here.

Nothing is committed. Everything below was run on `kentender-test.local`; the dev site has not been touched (see §1).

## 0. What was done

| ID | Change | Where | Proof |
|---|---|---|---|
| AR-00 | Plan reviewers (Accounting Officer, Head of Procurement Function, statutory approver, Finance Confirmation Officer) read the classification page, departmental plan and source of a plan under their review; the plan-item link is offered only where it opens | `procurement_planning/services/planning_authorization.py` (`plan_source_access`), `dpp_classification.py`, `dpp_read.py`, `plan_read.py`; `PlanItemEditorScreen.vue`, `ProcurementPlanning.vue` | `test_plan_source_reader` 14/14; Vitest 37/37; browser walk as Amina (link → page → refresh → Back). Built to the proposed PLN-R2, ahead of approval |
| AR-03 | A scheduled assignment no longer projects its Frappe Role at grant time; the reconciliation now runs hourly (it ran daily) so the Role appears when the start arrives | `kentender_core/services/responsibility_administration.py` (`_sync_projection`), `hooks.py` | three new tests in `test_responsibility_administration`; one existing test that pinned the old behaviour was corrected |
| AR-04 | One shared "holders in force now" helper (`authorization.active_holders`) replaces the Enabled-only lookups: Support Issues, technical service status, `recover_overdue_close`, Opening-access notices, guidance holders, handoff incidents | `kentender_core/services/authorization.py`, `support_issues.py`, `bid_submission/services/{technical_read,close,guidance,handoffs}.py`, `bid_opening/services/notify.py` | `test_active_holders_lists_only_assignments_in_force`; Bid Submission guidance / handoff / close-recovery modules green |
| AR-01 | The identity and payload records of a bid are closed to a raw Desk/REST read (the six content DocTypes already were): Bidder Arrangement, Bid Organisation Snapshot, Bid Workspace, Bid Submission Attempt, Bid Submission Version, Bid Submission Event, Tender Box Envelope, Bid Opening Handoff | `kentender_procurement/hooks.py` | `test_sealed_bid_desk_read` (16 failures without the hook, passing with it) |
| AR-02 | A Site-wide role (Head of Procurement Function, Planner, Procurement Officer, Auditor) no longer reads an unsent Requisition Draft: list, record, framework check, register, children, `state` is now a required argument of the reader gate | `procurement_requisitions/services/requisition_{roles,authorization}.py`, `read.py`, `draft_commands.py`, `correction.py` | new class in `test_ovs_requisition_reads`; two `test_requisition_authorization` tests re-pointed from a Draft to a submitted record, plus two new Draft denials |
| AR-05 | The Accounting Officer and Head of Procurement Function have a read-only DocPerm row on the Need root and its three projections (the reader hook still limits them to Submitted / Accepted / Not taken forward) | `departmental_needs/doctype/{departmental_need,need_planning_*}.json`, `setup/departmental_needs_doctypes.py` | `test_ovs_needs_reads` (3 new), `test_departmental_needs_permissions` (the "AO appears on no Needs doctype" pin replaced) |
| AR-06 | `get_tender_cancellation` derives the overdue statuses for the screen and writes nothing; the explicit writer stays for a scheduled job | `tenders/services/cancellation.py` (`derived_statuses`), `open_period_read.py` | assertion added to `test_open_period` (record version and `modified` unchanged by the read) |
| AR-07 | A meetings-register row whose record the reader cannot open shows no "View record" link (Head of User Department on an Opening row) | `proceedings/services/register.py`, `bid_opening/services/prc_owner.py`, `ProcurementMeetings.vue` | unit test + component test; bundle rebuilt (`procurement_meetings.bundle.3ZG6C2GX.js`) |
| AR-08 | Analytics names and links a Need or Requisition only where the viewer's own read opens it; the aggregate still counts every one | `departmental_needs/services/analytics_provider.py`, `procurement_requisitions/services/analytics_provider.py` | one new test each; one existing "same figures" test now compares figures, not names |
| AR-09 / AR-10 | A Technical Operator whose assignment is in force is a technical reader (read-only, site-wide), through the assignment and not the System Manager Role; the seeded Daniel Otieno loses System Manager, so a read carries no setup or responsibility-administration power. Release Operator and Evaluation Technical Support are not readers | `kentender_core/services/authorization.py` (`is_technical`), `seeds/site_setup.py`, `seeds/canonical.py`, `tests/test_canonical_seed.py` | `test_technical_operator_reader` (8 tests); canonical-seed validation and test changed to match |
| AR-12 | "Open approval task" is offered only to an Approver or a technical reader | `kentender_strategy/services/strategy_ui_contracts.py` | test red without the fix, green with it |
| AR-13 | Technical search names only a record the technical policy lets a reader open | `kentender_core/services/technical_search.py` (`may_open`) | 3 new tests; `test_bop_api`, `test_cfg_technical_read` green |
| AR-14 | The Strategy and Budget fiscal-year lists refuse a supplier / Website account | `strategy_ui_contracts.py`, `budget_contracts.py` | one new test each |
| AR-15 | Supplier registration documents are stored as private files | `kentender_suppliers/api/smw_public.py` | a source-level guard test (the multipart upload is not exercised) |

## 1. The dev site

**Done on 8 October 2026, at the Project Owner's instruction:** `make migrate`, `make clear`, and `make seed-canonical` on `kentender.midas.com` (dry run first: nothing to remove; seed and validation ended `CANONICAL_SEED_OK`). Checked afterwards on dev: Daniel Otieno holds no System Manager and is a technical reader; the sealed-bid denial and the hourly reconciliation are registered; the Accounting Officer and Head of Procurement Function rows exist on Departmental Need; Amina reads a consumed submission's classification (9 rows, no correction offered). **Not done:** `make restart` fails here (it needs supervisor, which this dev setup does not use), so the long-running background worker (started 7 Oct 22:46) still holds the old code until someone restarts it; the web server's reloader has already picked up the changes. A hard refresh of Desk is still needed in each browser. The list below is what was asked for; items 1, 2 and 4 are done.

### Original list

1. `bench --site kentender.midas.com migrate` — AR-05's DocPerm rows are in the JSON; they take effect on migrate. (Done on the test site.)
2. `bench --site kentender.midas.com clear-cache` and restart the web/worker/scheduler processes — new `has_permission` / `permission_query_conditions` hooks (AR-01) and the hourly scheduler entry (AR-03) are read from hooks.
3. Hard-refresh Desk: the procurement bundle hashes changed (planning `JU6APKWJ`, meetings `3ZG6C2GX`).
4. Daniel Otieno still holds System Manager on a site seeded before this change. Reseeding removes it (`seed-canonical`); or remove the Role by hand. Until then he can still change setup.
5. `kentender_core` hooks changed: run `make doctor` afterwards.

## 2. Decisions and documents owed (nothing here is implemented)

| # | Item | Recommendation |
|---|---|---|
| FU-1 | **OVS v0.6 §11 and the technical text** now disagree with the code on the Technical Operator (read-only, site-wide, KT-STD §8.3). The BDS / BOP / PRC role tables name only Administrator / System Manager | Amend OVS §11 and the owner role tables in a successor version; the code already follows the 4 October instruction |
| FU-2 | **AR-11, post-delivery technical read** of Evaluation / Award content follows OVS §4.2, while EVL and AWD module text still says "no bids / no decision" for a technical reader | Keep OVS §4.2; correct the EVL and AWD text (document change; no code change made) |
| FU-3 | **AR-16**, conflict-of-interest free text reaches the Accounting Officer before delivery and is System Manager-readable on the raw Evaluation Declaration DocType | Decide whether the text can name a bidder; if so, withhold it from both before delivery. Not changed |
| FU-4 | **Tender Security Intake** (issuer, instrument reference, amount) is still System Manager-readable; AR-01's hook list does not include it because the receipts page may rely on it | Confirm it is not sealed bid content; if it is, add it to the hook and check the `/desk/tender-security-receipts` page |
| FU-5 | **Awaiting Department Approval** Requisitions are still readable by the four Site-wide roles; only the unsent Draft is closed. REQ v1.14 §8 gives the Head of Procurement Function the *submitted* Requisition | Confirm whether a version awaiting the department's certification is "submitted" for these roles |
| FU-6 | **Auditor** can no longer read a Requisition Draft (REQ §8: immutable versions). NDS v1.16 still lets the Auditor read unsent Need Drafts by design | Confirm both |
| FU-7 | A **pure Technical Operator holds no Frappe DocPerm**, so raw Desk/REST list routes stay closed for them; the service-based surfaces (search, registers, STD Templates, Home, Analytics) work. KT-STD §8.3 says "every business surface" | Decide whether the Operator needs a read-only DocPerm role of its own (AR-10 removed System Manager, which was supplying it) |
| FU-8 | **PLN-R2 is built ahead of approval** (AR-00). The PLN v1.30 file is not in the repository | Register PLN v1.30 (or reverse the grant) |
| FU-9 | A scheduled assignment's Role is projected within the hour of its start, not at the instant: a record read by DocPerm alone opens up to an hour late (service-layer reads are exact) | Accept, or add a start-time trigger |
| FU-10 | `is_technical` now makes one extra indexed query for a user who holds the projected Technical Operator Role | Measure under load; cache per request if it shows |
| FU-11 | Other "holder list" lookups keep an Enabled-only filter but are re-checked by `holds` / `authorise_record` before any authority (`bid_evaluation`, `award`, `bid_opening` `people.py`, tender `handoffs.py`, Home providers) | Switch to `active_holders` for consistency (low risk) |
| FU-12 | Administrator bypasses Frappe's permission hooks, so AR-01's denial does not bind the Administrator account (the recorded production-gate residual) | Production custody control (TRUST), not code |

## 3. Failures found that were already there (not caused by this work)

Each was run with the relevant change reverted, or sits in code this work did not touch.

| Test | Symptom | Likely cause |
|---|---|---|
| `procurement_requisitions.tests.test_ovs_requisition_reads` · `test_the_accounting_officer_lists_and_opens_an_authorised_requisition` | the Accounting Officer's register lacks the requisition just authorised | unknown; fails with AR-02 reverted. The list itself works for the Accounting Officer |
| `procurement_requisitions.tests.test_read` · `test_the_procurement_task_leads_with_the_decision_and_its_financial_consequence`; `test_draft_commands` · `test_creates_one_draft_with_exact_default_amounts_and_no_budget_or_planning_effect` | `16 != 0` | test-site residue (12 Authorised requisitions from earlier runs survive the wipe) |
| `procurement_planning.tests.test_dead_end_matrix` | the Head of Procurement Function is told to wait for themselves in a Draft plan state | guidance text, not authorisation |
| `procurement_planning.tests.test_analytics_provider` · `test_a_departmental_author_gets_departmental_plans_only_and_no_plan_items` | the "outsider" fixture gets plan items | the fixture user also holds Head of User Department and Departmental Author in Beta, which the department view of plan items admits |
| `kentender_core.tests.test_technical_read_conformance` | Bid Opening resolvers give a `route` that is a string, not callable; `tenders.get_tender_publication.can_configure` is true for a technical reader | resolver / probe definitions in Bid Opening and Tenders |

### 3.1 The `kentender_core` sweep

All 93 test modules of `kentender_core` were run on the test site: 72 passed outright and 18 failed. The same 18 modules fail identically with every file this work changed stashed, so none is caused by it: `backfill_pe_fy_context_links`, `business_action`, `dem_seed_004_orchestrator_demands`, `exception_record`, `industry_design_gate`, `industry_design_scope`, `kentender_mvp_v1_seed_contract`, `kt_cl_shell_layout_guard`, `master_data`, `module_registry`, `portal_runtime`, `reference_data_seed_mvp1`, `seed_v1`, `stable_platform_seed`, `stitch_desk_chrome_gate`, `typed_attachment`, `wave0_smoke`, `workflow_guard` (several are legacy master-data / design-gate tests). `technical_read_conformance` (above) is a nineteenth. `artboard_provenance_gate` is not a unit test and printed nothing. `canonical_seed` timed out at 400 s inside the sweep and was run again alone with a longer limit; its result is the last line of this file.

## 4. Not run

- Playwright and the UI gates (none were run); the browser check was Amina, on the Planning pages only. Head of Procurement Function and statutory approver were covered by Python tests, not a browser.
- The full Python suites of Strategy, Budget, Procurement and Suppliers; only the modules named in §0 and the modules that mention the Technical Operator were run. The Bid Submission directory was started and stopped, not completed.
- Any change on the dev site (§1).
- The proposed owner successors (AUTH 1.12 … ANL 0.9) and CM, as agreed.

## 5. Last result: the canonical-seed test

`kentender_core.tests.test_canonical_seed` did not finish: it rebuilds the whole seeded world several times and was stopped at its time limit twice (400 s inside the sweep, then 28 minutes alone), so it counts as **not run to completion**, not as passed or failed. What was checked instead: the actor-seeding step this work changed (`site_setup._seed_users`) was run directly on the test site, and Daniel Otieno ends with no System Manager Role, is still a technical reader (`is_technical`), and holds his enabled Technical Operator assignment. The edited assertions in that test file (no System Manager; `is_technical` true) and the seed validation in `seeds/canonical.py` therefore match what the seed produces, but they have not been run as part of a complete class.
