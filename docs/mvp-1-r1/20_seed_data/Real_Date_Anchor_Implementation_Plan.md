# Real-date anchor: implementation plan

| Control | Value |
|---|---|
| Document ID | RA-PLAN-001 (new; the identifier is proposed for the owner's confirmation) |
| Version | plan.1 |
| Date | 15 October 2026 |
| Authority | `KenTender_Seed_World_Real_Date_Anchor_Proposal_2026-10-15.md` (RA-PROP-001 v1), **approved by the Project Owner on 15 October 2026**. Its decisions RA-1 to RA-5 are the Project Owner's answers of that day (RA-PROP-001 §3); RA-6 to RA-9 below are the answers to its open decisions. |
| Companions | `Real_Date_Anchor_IMPLEMENTATION_TRACKER.md`; `working/real_date_anchor_literal_dates_2026-10-15.tsv` (the dated-literal inventory, 1,269 files) |
| Builds on | `Two_Year_Seed_World_Implementation_Plan.md` (plan.1) and SEED-002 v0.7. Their phases, gates and findings are history and are not rewritten. |
| Status | **In progress.** Phase 0 built; the documents harmonized and approved on 15 October 2026 (SEED-002 v0.8 and KT-STD-001 v1.30; the register, with CM-CHG-001 v0.8 added); Phase 1 next. Contract Management's phase is held (below). No owner question is open. Nothing is committed: the owner has not asked for a commit. |

## Context

The canonical world is read as at 18 June 2027, 10:00 EAT, about eight months ahead of the real clock. The review of 15 October 2026 found no behaviour of the application that needs it and a growing list of costs: a pinned clock that drifts, rows dated after the real clock, a Needs rule that ignores real-time actions, and ERPNext documents that refuse a simulated future (RA-PROP-001 §2). The owner accepted the recommendation to anchor the world to the day the seed runs.

The target:

- **One rule.** No simulated moment is later than the real clock (RA-PROP-001 §4, R1).
- **The anchor** is the instant a seed run starts, stored on the site (R2). Fiscal years are derived from it: Year 0 closed, Year 1 carried out, Year 2 prepared (R3).
- **Planning journeys** keep their fixed relation to the fiscal calendar; **portfolio states** are offsets from the anchor (R4).
- **The ladders are capped by the anchor** (R5); at 15 October 2026 the prepared year stops at Departmental Needs (RA-2).
- **One clock policy per site** (R7): the development site `off`, a test site `never_ahead` and pinned to the anchor.

## Decisions on record

| Ref | Decision | Source |
|---|---|---|
| RA-1 | The development site runs on the real clock with no pin; only the test site pins, to the seed day | Owner, 15 Oct 2026: "Decisions: 1. Yes" |
| RA-2 | In October the prepared year stops at Departmental Needs | "2. Departmental needs"; "1. Correct" |
| RA-3 | A closed FY 2025/26 is seeded | "3. Yes, seed a closed FY" |
| RA-4 | Contract Management's dates are illustrative; its durations are authoritative (recommended, read as accepted; owner to confirm, RA-OD3) | "4. Recommend, and see the attached FU"; "2. Yes"; "3. Yes" |
| RA-5 | The recommendation set and its order of work | "I accept all recommendations." |
| Held | Contract Management's seed and tests wait until the Contract Management session releases them | "3. Yes" (RA-PROP-001 §5) |
| RA-6 | The fiscal year: the owner says nothing mandates a 1 July start and it may be shifted if necessary. Checked: ERPNext allows it; the approved CFG-CHG-002 v0.19 does not (CFG10-EC-001, CFG10-AC-009). The documents keep 1 July to 30 June and the question is open as RA-OD5. This replaces RA-OD1 | Owner, 15 Oct 2026: "Decisions: 1. Nothing mandates a fiscal year to start on July 1. You can always shift it to simplify the seeding if necessary. Check how the shift works with ERPNext."; SEED-002 v0.8 §A1.2 |
| RA-7 | Year 0 is configuration, its closed Budget and plan, and a small completed portfolio of three to four Tenders through to award, sized after Phase 1 (RA-OD2) | "2. Agreed" |
| RA-8 | Contract Management's dates are illustrative and its durations authoritative; the demonstration block moves back as a whole (RA-OD3, RA-4) | "3. Accepted" |
| RA-9 | Validation reports the anchor's age and, on a test site, fails the world at 60 days (RA-OD4) | "4. Accepted" |
| RA-10 | RA-OD5: the financial year stays 1 July to 30 June; a run when too little of Year 1 has elapsed anchors on the end of the season (the previous June) with a notice. CFG-CHG-002 v0.19 CFG10-EC-001 and CFG10-AC-009 are unchanged | Owner, 15 Oct 2026, on the harmonization report: "1. Keep 1 Jul to 30 Jun"; SEED-002 v0.8 §A1.1, §A1.2 |
| RA-11 | "The new document" is the proposal RA-PROP-001 v1 and its companion plan and tracker | "2. Yes" |
| RA-12 | SEED-002 v0.8 and KT-STD-001 v1.30 are approved | "3. Approved" |
| RA-13 | CM-CHG-001 v0.8 is added to the register | "4. Yes"; its status is the one its own control table states (Approved, Project Owner, 14 October 2026) |

Every open decision of RA-PROP-001 §9 is answered: RA-OD2, RA-OD3 and RA-OD4 (RA-7 to RA-9); RA-OD1 was replaced by RA-OD5 (RA-6), which the owner decided on 15 October 2026 (RA-10): keep 1 July to 30 June.

## Rules for working alongside other sessions

These come from what was seen on 15 October 2026: the Contract Management session had committed Phases 11 and 12 (`dbfb213d`, `f5e72d61`) and, at 21:15, started a shell loop over its Python test modules (`test_cm_import_boundary`, `test_cm_schema`, and others; the process list shows a truncated command, so which site it used and whether it took the lock were not seen).

1. **One test site, and its locks.** Every Python run and reseed uses `kentender-test.local` under `flock /tmp/kt-test-site.lock` (and `/tmp/home-test-site.lock` for a seed or a browser run). Never two `run-tests` at once; never while a Playwright run is active (`ps` for `run-tests`, `playwright`, `test-server` first).
2. **The development site is touched twice only:** the clock cleanup (done, 15 October 2026, owner-approved) and one reseed in Phase 8 after the owner is told. Its clock policy is already `off`.
3. **Contract Management is held.** Phase 6 starts only when that session says its seed and tests are free. Until then a change that touches `kentender_contracts` is limited to what a shared helper forces.
4. **Shared files.** `Makefile` and several seed files carry other sessions' uncommitted hunks. Commit only this work's hunks, using a private index; never revert another session's edit. No commit is made without the owner's request.
5. **Approved documents are not edited.** SEED-002 v0.7 and KT-STD-001 v1.29 stay the approved baselines; v0.8 and v1.30 are new files. On 15 October 2026 the owner asked for the affected documents to be harmonized, including the register ("The new document is approved, but I also need you to harmonize the rest of the affected documents including the register."). Done that day: SEED-002 v0.8 and KT-STD-001 v1.30 (written by anchored edits with the preservation and consistency checks, and approved the same day, RA-12); the register; HOME-CHG-001 v0.6 and ANL-CHG-001 v0.8 checked and left unchanged (build finding BF-RA-04). CFG-CHG-002 is not changed: the owner kept its fiscal-year contract (RA-10).

## Current state (verified 15 October 2026)

- `calendar.AS_AT = "2027-06-18 10:00:00"`; `YEAR1_SHIFT_DAYS = -364`; `YEARS = (YEAR1, YEAR2)`.
- `test_clock.py` now has the policy (Phase 0). The persisted instant lives in the Bid Submission test controls (`BDS Test Environment Controls.current_instant`); each app's `clock.py` reads it through `test_clock.current_instant()`: Bid Submission, Supplier Accounts, Proceedings, Bid Opening, Bid Evaluation, Award, Contract Management. Home reads the real clock unless a site sets `kt_home_follow_test_clock` (the test site does).
- Dated literals (upper bounds; RA-PROP-001 §2.2): seed code 44 files, 680 ISO and 189 written dates; Python tests 259 files, 1,153 and 351; browser tests and specs 73 files, 81 and 139.
- The largest seed files by dated literals: `portfolio.py` 151; `bid_evaluation/seeds/playwright_ui_fixtures.py` 71; `award/seeds/playwright_ui_fixtures.py` 66; `procurement_planning/seeds/kentender_mvp_v1.py` 47; `bid_submission/seeds/kentender_mvp_v1.py` 38; `bid_evaluation/seeds/kentender_mvp_v1.py` 35; `tenders/seeds/kentender_mvp_v1.py` 34; `site_setup.py` 32; `bid_opening/seeds/kentender_mvp_v1.py` 29; `contracts/seeds/demo.py` 25.
- Sites: `kentender.midas.com` policy `off`, no stored instant; `kentender-test.local` no policy key (so `free`), no stored instant (cleared at 20:42 on 15 October 2026 by something other than this work).
- Facts the new model has to meet, as measured: Year 1's authored execution is 109 days (1 March to 18 June 2027); at 15 October 2026 Year 1 has run 106; Year 2's Needs (24 November 2026) and plan (10 December 2026) are 40 and 56 days after the anchor.

## Phases

Every phase follows the AGENTS.md loop: the smallest failing check first, the smallest change, focused tests, then one reseed and validation on the test site, then the tracker row updated with evidence. A row is Done only with evidence.

**Phase 0 — Documents and the clock guard.** The proposal, this plan, the tracker and the inventory; the clock policy with its tests; the development site's cleanup. **Gate RA-G00:** the files exist, the owner's words are recorded verbatim, the policy tests and the existing clock consumers pass, the development site reads the real clock.

**Phase 1 — Inventory and spikes (no behaviour change).**
- **A. The shortest honest Year 1 history.** For each portfolio record, the legal minimums the owners enforce (the 7-day preparation minimum, the bid period, the evaluation period, the standstill) and whether a Requisition, a reservation or a Tender can be dated before the year starts. Output: the number of days the history needs, and so the start of the season.
- **B. Year 2 at the anchor.** What Needs intake looks like with the anchor inside the window (opened and closing dates, the `Open` state in KT-STD-001 v1.29 §8.4) and what each `NEXT` stage needs from the calendar.
- **C. What Analytics' months need.** Which months of the trailing twelve have events once Year 0 exists, and the least Year 0 portfolio that gives each a real value. Output: the proposal for RA-OD2.
- **D. Where the anchor is stored,** so validation, tests and browser specs can read it, and only the seed writes it.
- **E. Native documents in FY 2025/26,** for the Contract Management block: the ERPNext Fiscal Year, Budget and Finance requirements for a September 2025 posting.
- **F. Classify the inventory:** each dated literal as a story instant, a decision date in a comment, or unrelated; the counts recorded before anything is changed.

**Gate RA-G01:** each spike has a written result; the inventory is classified; RA-OD1 and RA-OD2 are put to the owner with numbers.

**Phase 2 — Calendar and the anchor.**
- `calendar` becomes a function of the anchor: the three years, `Year.at()`, a fiscal-calendar offset and an anchor offset; `AS_AT` stops being a constant.
- `canonical` stores and reads the anchor; refuses to run without it; reports its age; applies the season rule; computes the default `NEXT` (R5).
- `site_setup`: responsibility terms, rule windows, supplier registrations and the configured years (2025, 2026, 2027) as offsets.
- Validation checks the anchor, the clock policy and "nothing later than the anchor".

**Gate RA-G02:** `calendar` and `canonical` unit tests green; `CURRENT=annual_plan NEXT=none` validates on the test site at an anchor of the run start.

**Phase 3 — Year 1 and Year 2 re-timed, module by module.** In stage order: Budget, Needs, Planning, Requisitions, Tenders, Bid Submission (and Supplier Accounts), Bid Opening, Bid Evaluation, Award, the portfolio. Each module's seed takes its instants from `calendar`; the executed chain is tightened to the Phase 1 minimum. At the end the test site's clock policy is set to `never_ahead` and the world is pinned to the anchor.

**Gate RA-G03:** `CURRENT=award` with the default `NEXT` validates on the test site; a second run changes nothing; every state of SEED-002 v0.7 §A4.4 is present at the anchor (the portfolio check); each touched module's seed tests are green.

**Phase 4 — Year 0 (RA-3).** The closed year, to the depth RA-OD2 settles; Budget closed after the year's end; the Analytics months checked. **Gate RA-G04:** the world validates with Year 0; the full run's time is recorded; Analytics' twelve months each carry what Phase 1 said they should.

**Phase 5 — Tests and specs.** Python tests and browser specs read the anchor and compute their expected strings from it. Counted first (the Phase 1 classification), fixed in module batches, one broad run at the end. **Gate RA-G05:** the affected Python modules green on the test site; the Home and Analytics browser specs green on the test site; no literal story date remains in a test outside a fixture the test builds itself.

**Phase 6 — Contract Management (held).** The demonstration block re-timed as a whole, its history under the shared frozen clock, `kt_cm_clock` retired from the seed, the supplier and responsibility terms and the ERPNext Fiscal Year it needs; FU-CM-61 closed. **Gate RA-G06:** the nine demonstration profiles load on the test site with every instant not later than the anchor; native invoices and receipts post; the Contract Management tests that name those dates are green. Starts when the Contract Management session releases its files.

**Phase 7 — Documents.** Done early, on 15 October 2026, at the owner's request: SEED-002 v0.8 (the model; every instant Awaiting fixture), KT-STD-001 v1.30 (KT-STD-001 §8.4, KT-STD-001 §8.4A and KT-STD-001 §8.6) and the register. Still to do here: SEED-002 v0.9, which records the offsets as built (after Phase 3, and Phases 4 and 6 for Year 0 and Contract Management), and the owner's approval of v0.9 (v0.8 and v1.30 were approved on 15 October 2026); the runbooks, `CLAUDE.md`, the Makefile help and `kentender_core/seeds/README.md` brought true. **Gate RA-G07:** the owner approves SEED-002 v0.9 (v0.8 and KT-STD-001 v1.30 are approved, 15 October 2026); the links resolve; `make help` matches.

**Phase 8 — Roll out.** The owner is told; the development site is reseeded (policy `off`) and the test site rebuilt (policy `never_ahead`); the module sessions are told what changed (the anchor, the three years, the policy, the world's age); `never_ahead` is proposed as the default policy; memory updated. **Gate RA-G08:** both sites validate; the hand-over note is filed.

## Verification

- Python, always on the test site and never on the development site:

  ```bash
  cd /home/midasuser/frappe-bench
  flock /tmp/kt-test-site.lock bench --site kentender-test.local run-tests --app kentender_core --module kentender_core.tests.test_test_clock
  ```

- Seeding, from `apps/kentender_v1/`:

  ```bash
  make seed-canonical SITE=kentender-test.local CURRENT=… NEXT=…
  make seed-canonical-validate SITE=kentender-test.local CURRENT=… NEXT=…
  ```

- The clock, on any site: `bench --site <site> execute kentender_core.services.test_clock.describe` (policy, stored instant, the real clock, whether it is ahead).
- Passing `None` to `bench execute` is done with `--kwargs '{"instant": None}'`; `--args '[null]'` does nothing (build finding BF-RA-01).
- Browser (Phase 5): Home and Analytics specs through `scripts/test-site.sh run …`.

## Risks

- The history needs more days than the year so far in the first weeks after the season starts (RA-PROP-001 §4.2, RA-PROP-001 §4.3).
- Hidden assumptions of the old world in about 1,150 Python test dates, 220 browser-test dates and module code (Phase 1 classifies them).
- The Contract Management session's uncommitted and committed work uses the literal dates; re-timing it needs that session's agreement.
- Year 0 lengthens the full build.
- The development site shows a real-time world that ages; the remedy is a reseed (RA-PROP-001 §4.4).
- The owner's library may hold later versions of KT-STD-001, HOME, ANL or CM than the repository.

## Build findings

Appended during the build; the phase text above is not rewritten.

- **BF-RA-01 (15 Oct 2026) — `bench execute` with `--args '[null]'` did nothing.** The first attempt to clear the development site's stored instant printed nothing and changed nothing; `--kwargs '{"instant": None}'` cleared it (`True`, then `describe` showed no stored instant).
- **BF-RA-02 (15 Oct 2026) — the stored clock was not the documented one on either site.** Development read `2026-11-06 11:00:01` (saved 10 October 2026 18:49); the test site read nothing (saved 20:42 on 15 October 2026). Neither read 18 June 2027.
- **BF-RA-03 (15 Oct 2026) — a shifted fiscal year: ERPNext allows it, KenTender's approved requirement does not.** ERPNext (`fiscal_year.py`, and probes on `kentender-test.local` that were rolled back with no row left): any start date is accepted (1 June 2052 to 31 May 2053 was); the end must be one year after the start less a day (`InvalidDates` otherwise) unless the year is flagged short; the name is free text; an overlap with another year of the same company is refused (1 June 2026 to 31 May 2027 against the site's 2026-2027 was). KenTender: CFG-CHG-002 v0.19 CFG10-EC-001 ("This is not overridden to fit a seed."), CFG10-AC-009, `CFG_FY_DATES_INVALID`, `add_fiscal_year` and `preview_fiscal_year` in `site_configuration.py` (1 July to 30 June written in code), and the Strategy plan-period label `_period_fy_label` (reads July to June). So a shifted year needs CFG-CHG-002 amended first: RA-OD5. The owner's statement that nothing mandates a 1 July start is contradicted by that approved requirement. **Decided 15 October 2026 (RA-10): keep 1 July to 30 June.**
- **BF-RA-04 (15 Oct 2026) — HOME-CHG-001 v0.6 and ANL-CHG-001 v0.8 need no change.** Their 18 June 2027 dates are artboard fixtures that say so themselves: HOME-CHG-001 v0.6 §13 ("All H scenarios are **illustrative artboard fixtures**, not runtime events or changes to the canonical seed.") and ANL-CHG-001 v0.8 §13 ("A1/A2/A3 are **illustrative design datasets**, not installed records."; ANL-CHG-001 v0.8 §13.1: "illustrative design facts, not installed records or seed values"). RA-PROP-001 §7 had listed a note for each; it is not needed, and KT-STD-001 v1.30 §8.4 now states the rule once. The other module documents that carry the date (AWD-CHG-001, TPR-CHG-001, DSP-CHG-001) are artboard fixtures of the same kind and were not changed.
- **BF-RA-05 (15 Oct 2026) — CM-CHG-001 v0.8 is not in the register.** The register lists Contract Management only as future work. It was added on 15 October 2026 at the owner's request ("4. Yes"), with the status its own control table states (Approved, Project Owner, 14 October 2026). The register's FW-008 and DEC-016 still call Contract Management planned future work; they are not changed here, because the owner has not stated the release-slice scope. Its follow-up FU-CM-61 is closed by the Contract Management owner when Phase 6 is done.
