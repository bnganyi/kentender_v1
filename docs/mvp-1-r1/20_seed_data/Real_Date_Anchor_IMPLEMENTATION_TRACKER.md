# Real-date anchor: implementation tracker

| Control | Value |
|---|---|
| Document ID | RA-TRK-001 (new; the identifier is proposed for the owner's confirmation) |
| Version | tracker.1 |
| Plan | `Real_Date_Anchor_Implementation_Plan.md` (plan.1) |
| Proposal | `KenTender_Seed_World_Real_Date_Anchor_Proposal_2026-10-15.md` |
| Status | **Built and run on the test site; two things open.** Phases 1 to 7 done or partial as the rows say; Phase 8 is partial: the development site is not reseeded (refused by the permission classifier on 16 October 2026; the owner decides) and the clock policy `never_ahead` is not adopted. SEED-002 v0.9 is proposed. Nothing is committed. |
| Updated | 16 October 2026 |

## Rules

1. A row is **Done** only with evidence: the commands run, the site, the result. Narrow passes don't close broader rows.
2. Statuses: **Planned**, **In progress**, **Done**, **Blocked — owner**, **Blocked — dependency**, **On hold**.
3. Each row is updated in the same step as the work it records.
4. Python runs and reseeds use `kentender-test.local` under its lock, never while another run is active (plan, "Rules for working alongside other sessions").

## Phase 0 — Documents and the clock guard

| ID | Work | Status | Evidence |
|---|---|---|---|
| RA-0001 | The review: what the fixed date costs and what needs it | Done | RA-PROP-001 §2; read-only commands on the development site on 15 October 2026 (rows dated after the real clock, the stored clock, the assignments). |
| RA-0002 | The owner's decisions recorded verbatim | Done | RA-PROP-001 §3; plan "Decisions on record". |
| RA-0003 | Proposal, plan and tracker written | Done | The three files in this folder; `consistency_check.py` on the three files with the register: 0 errors, 7 warnings (no Approval-effect section in a proposal, plan or tracker; SEED-002 v0.7 and its proposed successor v0.8 cited on purpose; two section numbers inside a verbatim quotation of CM-CHG-001 v0.8). Preservation and register checks do not apply: the files are new and no register entry changed. Uncommitted. |
| RA-0004 | The dated-literal inventory | Done | `working/real_date_anchor_literal_dates_2026-10-15.tsv`: 1,269 files; seed code 44 files (680 ISO, 189 written), Python tests 259 (1,153; 351), browser tests and specs 73 (81; 139). Upper bounds: comment dates are counted (classified in RA-0106). |
| RA-0005 | The test-clock policy (`free`, `never_ahead`, `off`) and the validation hook | Done | `kentender_core/services/test_clock.py` (`policy`, `stored_instant`, `ahead_of_real`, `current_instant`, `set_instant`, `describe`, `problem`); `canonical._clock_problem` used by `validate()`. `kentender_core.tests.test_test_clock`: 20 tests, red first (16 errors, the seam did not exist), then green on `kentender-test.local`, 15 October 2026. Existing consumers, default policy, unchanged: `bid_submission.tests.test_simulation` 8 OK; `kentender_core.tests.test_home_time` 24 OK. The Contract Management, Bid Opening and Award consumers were not re-run (the default policy changes nothing for them). |
| RA-0006 | The development site: policy `off`, stale clock cleared | Done | 15 October 2026, owner-approved. `bench --site kentender.midas.com set-config kt_test_clock_policy off` (the site configuration differs from before by that one key, compared file to file); `set_instant` with `None` cleared `2026-11-06 11:00:01`; `describe` then read `{"policy": "off", "stored": null, …, "ahead": false}`. Build finding BF-RA-01. |
| RA-0007 | Gate RA-G00 | Done | The files exist; the owner's words are verbatim; the policy tests and the existing consumers pass; the development site reads the real clock. |
| RA-0008 | RA-PROP-001 approved | Done | Owner, 15 October 2026: "The new document is approved"; control table marked; preservation check PASS against the pre-approval copy. The reading (the proposal and its companions) is flagged for the owner to correct. |
| RA-0009 | The fiscal-year check the owner asked for | Done | Plan BF-RA-03: ERPNext source read and rolled-back probes on the test site (0 rows left); KenTender's CFG10-EC-001, CFG10-AC-009, `CFG_FY_DATES_INVALID` and two code places found. Conflict put to the owner as RA-OD5; decided 15 October 2026: keep 1 July to 30 June (plan RA-10). |
| RA-0010 | SEED-002 v0.8 | Done — approved 15 October 2026 (RA-0013) | `KenTender_SEED-002_Canonical_Seed_World_v0_8.md`, 24 anchored edits to v0.7: preservation PASS (0 changed or deleted apart from the control-table Version row), consistency 82 errors both v0.7 and v0.8 (all in the retired-document carry-over register Appendix A), none introduced. |
| RA-0011 | KT-STD-001 v1.30 | Done — approved 15 October 2026 (RA-0013) | `KenTender_KT-STD-001_Document_Design_and_Verification_Standards_v1_30.md`, 12 anchored edits to v1.29 (KT-STD-001 §8.4, KT-STD-001 §8.4A, KT-STD-001 §8.6, the control table and KT-STD-001 §12): preservation PASS (two control-table rows changed, allowed), consistency 1 error in both (a KT-STD-001 §4.1 reference, pre-existing), none introduced. |
| RA-0012 | The register (KT-DOC-CTRL-001), first update | Done | Entry RA-PROP-001; SEED-002 and KT-STD-001 carry their proposed successors; DEC-057 to DEC-060; delivery item RDA-001; finding AUD-032 (RA-OD5). `register_check.py` with the approved baselines (SEED-002 v0.7, KT-STD-001 v1.29) and RA-PROP-001 v1: 0 errors; 231 warnings and 8 notes before and after, one warning replaced by one (RA-PROP-001 cites CM-CHG-001, which the register does not list). Proposed successors are cited as "(proposed vX)" so the version check does not read them as the current version. A leaf-by-leaf comparison with the register before the edit found every string kept (only `as_of` changed, and three fields extended). HOME, ANL and CFG-CHG-002 entries unchanged (plan BF-RA-04). |
| RA-0013 | Approvals recorded | Done | Owner, 15 October 2026, on the harmonization report: "3. Approved" (SEED-002 v0.8 and KT-STD-001 v1.30), "2. Yes" ("the new document" is RA-PROP-001 v1 and its companions), "1. Keep 1 Jul to 30 Jun" (RA-OD5), "4. Yes" (CM-CHG-001 v0.8 added to the register). SEED-002 v0.8 was patched before approval to write the RA-OD5 answer into §A1.1, §A1.2 and Appendix D question 5, each change keeping the earlier text beside it as "Proposed read"; preservation PASS against v0.7 and against the proposed v0.8. KT-STD-001 v1.30: control table, approval paragraph and §12 effect only, preservation PASS. RA-PROP-001 approval record extended with the confirmation, preservation PASS. |
| RA-0014 | The register, second update: approvals, CM-CHG-001 v0.8, DEC-061, AUD-032 closed | Done | SEED-002 now v0.8 and KT-STD-001 v1.30 (approved 15 October 2026; the v0.7 and v1.29 files, hashes kept as `prior_approved_baseline.source_sha256`, are unchanged); CM-CHG-001 v0.8 added (Approved 14 October 2026, as its control table states; implementation In progress, verification Pending, release Not approved, which follow the repository and are not a new decision); SEED-002 implementation set to In progress because v0.8 adds requirements that are not built (the Phase 0 clock policy only), not because of the approval; DEC-061 added; AUD-032 closed; DEC-057 to DEC-060 and RDA-001 read as approved. `register_check.py` with the four approved files: 0 errors, `source_sha256` of each matches its file, 237 warnings (231 before; the rise is older citations of SEED-002 v0.7 and KT-STD-001 versions that now trail by one more version, and the new CM-CHG-001 entry). Leaf-by-leaf comparison with the register at the start of the harmonization: every string kept except `as_of`, two replaced hashes (now in `prior_approved_baseline`) and one dependency sentence (kept as "v0.7 read"). FW-008 and DEC-016 still describe Contract Management as future work: not changed (the owner has not stated the release-slice scope). |

## Phase 1 — Inventory and spikes (no behaviour change)

| ID | Work | Status | Evidence |
|---|---|---|---|
| RA-0101 | Spike A: the shortest honest Year 1 history; Requisitions and reservations before the year starts | Done | Answered on `kentender-test.local`, 16 Oct 2026: the Requisitions and Tenders services accept a requisition and an invitation date before the financial year starts. At the 9 Oct anchor the executed chain begins on 25 May and 22 Jun 2026 and Year 0's on 24 Jun 2025; `SEASON_MIN_ELAPSED_DAYS` stays 100. |
| RA-0102 | Spike B: Year 2 at the anchor; what each `NEXT` stage needs from the calendar | Done | Year 2 at an anchor of 9 Oct 2026 goes to Departmental Needs (`default_next_stage` = needs): its journey is pulled 49 days so its Needs have happened; its intake window (closes 25 Nov 2026) is never pulled. A `NEXT` beyond that is refused with a message. |
| RA-0103 | Spike C: what Analytics' months need; the proposal for RA-OD2 | Partial | Not made as a separate spike. Read on 16 Oct 2026 with `analytics_workspace.get_workspace`: the monthly series show activity in 10 of the twelve months before the anchor; February and May 2026 hold none (RA-0403). |
| RA-0104 | Spike D: where the anchor is stored | Done | A site-wide default, `kt_seed_world_state` (JSON: mode, anchor, started, season notice), read with `frappe.db.get_default`: no DocType, no migrate, readable by validation, tests and specs, written only by `calendar.prepare`. It is resolved once per process when the seed modules are imported, so `make seed-canonical` stores it in a process of its own first and the seed runs in the next one; a change in the same process raises `AnchorChangedError`. |
| RA-0105 | Spike E: native documents in FY 2025/26 for the Contract Management block | Done | The ERPNext Fiscal Year 2025-2026 exists (Year 0). Native purchase orders, receipts, invoices and payment entries take the trusted clock's date (`native/adapter.py`), so they post between July 2025 and July 2026 (RA-0604). |
| RA-0106 | Classify the inventory: story instant, comment, unrelated | Done (seed code); tests Planned | 15–16 Oct 2026. Seed code: 506 quoted story literals in 26 files are routed through `calendar.world` (`W`); 18 are fiscal-calendar dates routed through `calendar.fiscal` (`F`: Required by dates, Year 2 plan baselines, intake closes, rule effective dates, a supplier's licence expiry); the journey instants of Budget, Needs and Planning keep going through the Year objects (`Year.at`, `Year.window`, never mapped twice); the Strategy period and the retired assignment rows stay as they are. The mapping is the identity until an anchor is stored, so the v0.7 world is unchanged. The tests are classified in Phase 5, after the anchored seed passes. |
| RA-0107 | Put RA-OD2 (Year 0's depth) and RA-OD5 (the fiscal year) to the owner with the Phase 1 numbers | Planned | RA-OD2 was agreed in principle ("2. Agreed"); RA-OD1 is replaced by RA-OD5 (plan RA-6). |
| RA-0108 | Gate RA-G01 | Met | Spikes A, B, D and E answered; C partial (RA-0103). |

## Phase 2 — Calendar and the anchor

| ID | Work | Status | Evidence |
|---|---|---|---|
| RA-0201 | `calendar`: the anchor, the three years, the two kinds of offset | Done (offline) | `kentender_core/seeds/calendar.py`: `prepare`, `choose_anchor`, `world`/`W`, `fiscal`/`F`, `Year` (Year 0, 1, 2; `at`, `window`, `fiscal`), `prepared_pull_days`, `default_next_stage`, `block_shift_days`. `kentender_core.tests.test_calendar`: 20 tests, pure arithmetic, run with no site (`env/bin/python -m unittest`), green. |
| RA-0202 | `canonical`: store and read the anchor; refuse without one; the age; the season; the default `NEXT` | Done | Run on the test site, 16 Oct 2026: the default `NEXT` from the anchor, the refusal of a later cap, `anchor_status`, the `clock.at` guard and the Makefile `ANCHOR=real|story` path (a plain `make seed-canonical ANCHOR=real FORCE=True` kept the stored anchor and changed nothing else). |
| RA-0203 | `site_setup`: responsibility terms, rule windows, supplier registrations, the configured years (2025, 2026, 2027) | Done | Run: the configured years are Year 0 to 2, the rule window starts on 1 Jan 2025, intake closes follow the fiscal calendar; the site stage validates. |
| RA-0204 | Validation: the anchor, the clock policy, nothing later than the anchor | Done | Run: `validate` reports the anchor, its age, the clock and any recorded event later than the anchor; on 16 Oct it failed, correctly, on test residue left by other sessions' Budget tests and by a cleared clock, and passed after a rebuild and `set_as_at`. |
| RA-0205 | Gate RA-G02 | Met | `CURRENT=award` with the default `NEXT` validates on the test site at an anchor of 9 Oct 2026 10:00; `test_calendar` (37) and `test_canonical_seed` (40) pass. |

## Phase 3 — Year 1 and Year 2 re-timed

| ID | Work | Status | Evidence |
|---|---|---|---|
| RA-0301 | Budget | Done | Year 0, 1, 2 budgets from `calendar.Year`; approval references and document names derived from the year (`kentender_budget/seeds/kentender_mvp_v1_portfolio.py`). Run on the test site, 16 Oct 2026: the module's seed builds inside the full world and the world validates (RA-0205, RA-0312); its Python tests are in RA-0501. |
| RA-0302 | Departmental Needs (Year 2 stops at `needs` in October, RA-2) | Done | Needs journeys through `Year.at`/`Year.window`, required-by dates through `F`; Year 0's one Need; Year 2 stops where the anchor allows. Run on the test site, 16 Oct 2026: the module's seed builds inside the full world and the world validates (RA-0205, RA-0312); its Python tests are in RA-0501. |
| RA-0303 | Planning | Done | Plan spec per year (`plan_spec`, Year 0 added); baseline invitations through `W`/`W0`; intake close through `Year.window`; Treasury references and URLs derived from the year. Run on the test site, 16 Oct 2026: the module's seed builds inside the full world and the world validates (RA-0205, RA-0312); its Python tests are in RA-0501. |
| RA-0304 | Requisitions | Done | `fiscal_year` threaded through `build_requisition`/`_plan_item_id`; canonical Plan Items of every Annual Plan up to Year 1; latest delivery held to the year's last day (`calendar.delivery`). Run on the test site, 16 Oct 2026: the module's seed builds inside the full world and the world validates (RA-0205, RA-0312); its Python tests are in RA-0501. |
| RA-0305 | Tenders | Done | Tender story instants through `W`. Run on the test site, 16 Oct 2026: the module's seed builds inside the full world and the world validates (RA-0205, RA-0312); its Python tests are in RA-0501. |
| RA-0306 | Bid Submission and Supplier Accounts | Done | Bid and supplier-account instants through `W`/`W0` (accounts register before Year 0's bids); signing certificate valid from before Year 0's bids; offered delivery dates held to the boundary. Run on the test site, 16 Oct 2026: the module's seed builds inside the full world and the world validates (RA-0205, RA-0312); its Python tests are in RA-0501. |
| RA-0307 | Bid Opening | Done | Opening instants through `W`. Run on the test site, 16 Oct 2026: the module's seed builds inside the full world and the world validates (RA-0205, RA-0312); its Python tests are in RA-0501. |
| RA-0308 | Bid Evaluation | Done | Evaluation instants through `W`. Run on the test site, 16 Oct 2026: the module's seed builds inside the full world and the world validates (RA-0205, RA-0312); its Python tests are in RA-0501. |
| RA-0309 | Award | Done | Award instants through `W`; `award_portfolio_tender` takes `accepted`; DELIVERED profile refuses a moment later than the real clock. Run on the test site, 16 Oct 2026: the module's seed builds inside the full world and the world validates (RA-0205, RA-0312); its Python tests are in RA-0501. |
| RA-0310 | The portfolio (`portfolio.py`) | Done | `portfolio.py`: Year 1 items wrapped; `PORTFOLIO0` (three Year 0 tenders, one per slot) and `portfolio_specs()`. Run on the test site, 16 Oct 2026: the module's seed builds inside the full world and the world validates (RA-0205, RA-0312); its Python tests are in RA-0501. |
| RA-0311 | The test site: policy `never_ahead`, clock pinned to the anchor | Not done | The test-site policy stays `free` and the clock is pinned to the anchor by `set_as_at`. A run under `never_ahead` would repeat the Python suite (about 3½ hours); not made. Proposed to the owner in the change report. |
| RA-0312 | Gate RA-G03 | Met, except RA-0311 | The world validates with the default `NEXT`; a plain rerun changes nothing; the portfolio states equal the v0.8 table (Appendix B), plus Year 0's three Tenders. |

## Phase 4 — Year 0

| ID | Work | Status | Evidence |
|---|---|---|---|
| RA-0401 | The closed FY 2025/26 to the depth RA-OD2 settles | Done | Built and validated on the test site: Budget MOH-FIN-BUD-2025-01, Need NDS-MOH-2025-0001, three Plan Items, three Tenders each with two bids to an accepted award (stage Waiting to proceed), the three chains 0, 18 and 36 weeks apart. `binding_rows()` lists TND-MOH-2025-001 to 003. |
| RA-0402 | Budget closed after the year's end | Not possible as stated | A Budget closes only when no reservation remains held; Year 0's requisitions hold theirs (`budget_readiness_contracts`: "cannot be closed yet … remains reserved"). Year 0's Budget stays Active; to be recorded in SEED-002 v0.9 §A7. |
| RA-0403 | Analytics' twelve months checked | Partial | Read on 16 Oct 2026: needs accepted Nov 2025 and Oct 2026; requisitions submitted Mar, Jun to Oct 2026 and authorised Nov 2025, Mar, Jul, Aug, Oct 2026; Tenders published Dec 2025, Apr, Jul to Sep 2026; decisions Jan, Jun, Oct 2026. February and May 2026 hold nothing. |
| RA-0404 | Full-run time recorded | Done | A rebuild takes 6 to 8 minutes alone (362 s on 16 Oct at 03:30; 7 min 48 s at 14:49); 17 minutes when other sessions' tests run on the site at the same time; a plain rerun about 5 seconds. |
| RA-0405 | Gate RA-G04 | Met, with RA-0402 and RA-0403 recorded | The world validates with Year 0; the run time is recorded; Year 0's Budget cannot be closed and two months of Analytics hold nothing. |

## Phase 5 — Tests and specs

| ID | Work | Status | Evidence |
|---|---|---|---|
| RA-0501 | Python tests read the anchor (batches by module, counted first) | Done, with named exceptions | 213 Python test modules run on the test site (the 144 that name a date, re-run after the fixes they showed, and Contract Management's 64): 204 pass (2,671 tests); 9 fail, none for a reason that depends on the anchor: three legacy seed-pack tests, `test_acceptance_gaps` (labels of 2 Oct), `test_departmental_needs_architecture` (same on the unmodified Planning seed), `_navigation`, `test_procurement_sidebar_g0_012_contract`, `departmental_needs.test_home_provider` (a grant that ended in Dec 2025; direct writes the guard refuses) and one lifecycle test on a disposable Fiscal Year with no Budget. |
| RA-0502 | Browser specs compute their expected strings from the anchor | Partial | `tests/ui/helpers/anchor.ts` (mirror of the calendar) and the Home, Strategy, Needs, Award, Evaluation, Bid Submission, Bid Opening and Contract Management specs that name a seeded date are converted. Run on the test site: Home 40 of 40; Award, Evaluation, Oversight and Contracts-shell sample 21 of 22 (the one failure is a stale expectation of the Award stage). Not converted or not run: about 35 further dated specs, the Planning specs that read the Year 2 Annual Plan (it does not exist at an October anchor), and the Contract Management browser gates. |
| RA-0503 | Gate RA-G05 | Partial | Python: 204 of 213 modules pass, the 9 others are not anchor-dependent; Home browser specs 40 of 40; the other dated browser specs are not all run. |

## Phase 6 — Contract Management

| ID | Work | Status | Evidence |
|---|---|---|---|
| RA-0601 | The Contract Management session releases its seed and tests | Done | The Contract Management session released the site on 16 Oct 03:08 and handed over its files; it is running its own release-evidence gate from 15:30 on 16 Oct. |
| RA-0602 | The demonstration block re-timed as a whole | Done | `kentender_contracts.simulation.timeline.D` = `calendar.years_block`: the story moves back by whole years (2 years at this anchor: 2 Jul 2025 to 28 Jul 2026); whole weeks were tried first and refused by the monthly reports. |
| RA-0603 | History under the shared frozen clock; `kt_cm_clock` retired from the seed | Done | `seeds/demo.py` runs each step under the frozen seed clock (`_at`/`_end`); `kt_cm_clock` is still the tests' injection point. |
| RA-0604 | Supplier and responsibility terms; the ERPNext Fiscal Year; Finance and Budget accept the earlier postings | Done | `native/adapter.py` dates the purchase order, receipt, invoice and payment entry by `services/clock.now()`; the ERPNext Fiscal Year 2025-2026 exists. `test_cm_native`, `_readiness`, `_receipt_reconciliation` and `_claim_race` pass. |
| RA-0605 | FU-CM-61 closed in the Contract Management follow-ups, with a pointer to the proposal | Built; closure is the Contract Management owner's | FU-CM-61 option 1 (the adapter passing the trusted date) is built. The follow-up row is the Contract Management session's to close once its evidence gate has run. |
| RA-0606 | Gate RA-G06 | Partial | All 64 service-gate modules pass (644 tests); the nine demonstration profiles load at 2 Jul 2025 to 28 Jul 2026, validate and clean up. Not run by this work: `cm-ui-gate`, `cm-demo-gate`, `cm-persona-gate` and the release-evidence script. |

## Phase 7 — Documents

| ID | Work | Status | Evidence |
|---|---|---|---|
| RA-0701 | SEED-002 v0.8 (Proposed) under the document-change protocol | Done (model) | RA-0010. SEED-002 v0.9, which records the offsets as built, is owed after Phase 3. |
| RA-0702 | The replacement text for KT-STD-001 §8.4 and KT-STD-001 §8.4A | Done — approved | RA-0011: KT-STD-001 v1.30, approved 15 October 2026. At the owner's request it was written here, not left for the owner to apply (two-year decision D7, SW-0104). |
| RA-0703 | Notes for HOME-CHG-001 v0.6, ANL-CHG-001 v0.8 and CM-CHG-001 v0.8 §10.1B | Done — none needed for HOME and ANL | Plan BF-RA-04. CM-CHG-001 v0.8 §10.1B: SEED-002 v0.8 §A8 states the rule (RA-8); the specification is not in the register and its follow-up FU-CM-61 is closed by the Contract Management owner (RA-0605). |
| RA-0704 | Runbooks, `CLAUDE.md`, the Makefile help, `kentender_core/seeds/README.md` | Done, except the default | Makefile help line and comment, `CLAUDE.md` command card and `kentender_core/seeds/README.md` describe the anchor model; `scripts/test-site.sh` no longer passes `next_year`. `ANCHOR` stays `story` by default until the development site is reseeded (RA-0801). |
| RA-0705 | The register entry for SEED-002 v0.8 | Done | RA-0012. |
| RA-0706 | Gate RA-G07 | Blocked — owner | Awaiting the owner's approval of SEED-002 v0.9 (proposed 16 Oct 2026; preservation PASS, no new consistency error, register check 0 errors). |
| RA-0707 | RA-OD5: keep the fiscal year at 1 July to 30 June, or amend CFG-CHG-002 v0.19 CFG10-EC-001 and CFG10-AC-009 | Done — kept | Owner, 15 October 2026: "1. Keep 1 Jul to 30 Jun" (plan RA-10); written into SEED-002 v0.8 §A1.1, §A1.2 and Appendix D question 5; register finding AUD-032 closed, DEC-061. |

## Phase 8 — Roll out

| ID | Work | Status | Evidence |
|---|---|---|---|
| RA-0801 | Tell the owner; reseed `kentender.midas.com` (policy `off`) and rebuild `kentender-test.local` (policy `never_ahead`) | Partial | Test site rebuilt (anchor 9 Oct 2026) and validated. The development site is NOT reseeded: the reseed was refused by the permission classifier on 16 Oct 2026 and is left for the owner's decision; its policy stays `off`. |
| RA-0802 | Hand-over note to the module sessions | Done | `Real_Date_Anchor_HANDOVER_NOTE_2026-10-16.md`; the Contract Management and Budget sessions were told by message. |
| RA-0803 | Propose `never_ahead` as the default policy | Proposed | `never_ahead` as the test-site default is proposed in the change report; not adopted. |
| RA-0804 | Memory updated | Done | Memory `real-date-anchor-build-progress-2026-10-16` updated. |
| RA-0805 | Gate RA-G08 | Not met | The development site is not reseeded. |
