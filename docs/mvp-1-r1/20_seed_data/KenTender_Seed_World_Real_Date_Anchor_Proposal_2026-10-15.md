# Proposal: anchor the canonical seed world to the real date

| Control | Value |
|---|---|
| Document ID | RA-PROP-001 (new; the identifier is proposed for the owner's confirmation) |
| Version | 1 (first issue) |
| Date | 15 October 2026 |
| Status | **Approved — 15 October 2026** (decisions-accepted read: **Decisions accepted — 15 October 2026** (RA-1 to RA-3 and RA-5 as the owner stated them; RA-4 as recommended and read as accepted, to be confirmed: §9). Phase 0 (documents and the clock guard) is built; nothing else is. No controlled document has been changed.) |
| Approved on | 15 October 2026 |
| Approval record | Project Owner, 15 October 2026, verbatim: “The new document is approved, but I also need you to harmonize the rest of the affected documents including the register.” The new document is read as this proposal (RA-PROP-001 v1) and its companion plan and tracker; the owner is asked to correct that reading if it is wrong. The same message answered the open decisions of §9, verbatim: “Decisions: 1. Nothing mandates a fiscal year to start on July 1. You can always shift it to simplify the seeding if necessary. Check how the shift works with ERPNext. 2. Agreed 3. Accepted 4. Accepted”, which read as: RA-OD1 answered with a different approach from the recommendation (the fiscal year may be shifted if necessary; the check is recorded in `Real_Date_Anchor_Implementation_Plan.md` as RA-6, and it found a conflict with CFG-CHG-002 v0.19 CFG10-EC-001, put to the owner as RA-OD5, so §4.3 is superseded only to the extent that RA-OD5 settles); RA-OD2 agreed; RA-OD3 accepted; RA-OD4 accepted. Approval establishes the decisions and the model; it does not establish implementation, test coverage or release. Confirmed 15 October 2026, in the answers to the report that followed, verbatim: “2. Yes”, answering whether “the new document” is this proposal and its companion plan and tracker; and “1. Keep 1 Jul to 30 Jun”, answering RA-OD5 (see above): the financial year stays 1 July to 30 June, so §4.3's anchoring on the end of the season (the previous June) stands and nothing in §4.3 is superseded in that respect. |
| Asked for by | Project Owner, 15 October 2026, verbatim: "The side effects are significant, and at the same time I do not see any scenarios in the reasons given that cannot be overcome by careful preparation of the seed data that revolves around the real today. Revisit the seed data documentation and implementation and let me know". |
| Amends | `KenTender_Two_Year_Seed_World_Proposal_2026-10-04.md` decisions D1, D2, D3 and D5 (retained as history; §3). SEED-002 v0.7 (approved 11 October 2026) is amended by a later version, never edited in place (§7). |
| Read for this proposal | In full: SEED-002 v0.7; `KenTender_Two_Year_Seed_World_Proposal_2026-10-04.md`; `Two_Year_Seed_World_Implementation_Plan.md`; `Two_Year_Seed_World_IMPLEMENTATION_TRACKER.md`; `AGENTS.md`. In part: KT-STD-001 v1.29 §8.4 and KT-STD-001 v1.29 §8.4A (lines 843–864); CM-CHG-001 v0.8 §10.1B (lines 658 and 674–704 and the briefs quoted below); CM-CHG-001 v0.8 follow-ups (FU-CM-61, line 95) and implementation tracker (B22); CM-CHG-001 v0.8 implementation plan D17 (line 108); the Baseline Register entry for SEED-002 (KT-DOC-CTRL-001). Code read: `kentender_core/seeds/{calendar,clock,canonical,portfolio}.py`, `site_setup.py` (assignments), `services/{test_clock,home_time,analytics_measures}.py`, the Bid Submission, Supplier Accounts and Contract Management `clock.py`, `bid_submission/services/simulation.py`, `departmental_needs/services/usage.py`, `kentender_contracts/native/adapter.py` and `seeds/demo.py`; ERPNext `purchase_receipt.py` and `accounts_controller.py`. |
| Not read | HOME-CHG-001 v0.6 and ANL-CHG-001 v0.8 themselves (their read time is taken from SEED-002 v0.7 §A1); the Home, Analytics and Contract Management `.dc.html` boards; KT-STD-001 v1.29 outside KT-STD-001 v1.29 §8.4 and KT-STD-001 v1.29 §8.4A. |

## 1. Verdict

The owner is right. No behaviour of the application needs the story's "now" to be 18 June 2027. The fixed date was chosen so the seed would match the Home and Analytics designs and the existing chain's dates, and it has since cost more than it gave (§2). The world is therefore re-anchored to the day the seed runs, under one rule that Contract Management's follow-up FU-CM-61 turned from a preference into a requirement:

> **No simulated moment is later than the real clock.**

Everything else follows from that rule (§4). Two limits are real and are stated in §4.2 to §4.4: fiscal years are fixed July to June, so the world has to be re-timed, not shifted; and a world anchored to a real day ages in real time, so it is refreshed by reseeding.

## 2. What the review found

Each finding says where it was read. Findings are observations; none is a rule.

**2.1 The application does not need the date.** Home reads the real site time unless a site opts in (`services/home_time.py` `now()`, owner decision 5 October 2026 in its docstring). Analytics' twelve-month window is computed from the read instant (`services/analytics_measures.py` `window_months(at)`: "the twelve calendar months ending with the month that contains the read time"). Only test assertions carry the literal date, for example Home's "Updated 18 June 2027, 10:00 EAT" (`tests/ui/smoke/home/home-work.spec.ts` line 22).

**2.2 The offsets promised on 4 October were not built.** Decision D2 of `KenTender_Two_Year_Seed_World_Proposal_2026-10-04.md` §9 reads: "Write every instant as an offset from the as-at constant, so a later 'shift the whole story back N years' option is a one-line change." `calendar.AS_AT` is used in four seed files (`award/seeds/profiles.py`, `bid_opening/seeds/profiles.py`, `departmental_needs/seeds/profiles.py`, `seeds/canonical.py`). Counting ISO and "18 June 2027" style dates in 2025–2028 (`working/real_date_anchor_literal_dates_2026-10-15.tsv`, measured 15 October 2026): seed code 44 files, 680 ISO and 189 written dates; Python tests 259 files, 1,153 and 351; browser tests and specs 73 files, 81 and 139. These are upper bounds, because decision dates in comments are counted; Phase 1 classifies them. A further 223 design-fixture JSON files and 164 client files carry dates; they are UI-only fixtures and are not re-timed.

**2.3 "Every recorded fixture event is at or before it" is not true.** SEED-002 v0.7 §A1 says so of the as-at instant. The Contract Management demonstration profiles run the site clock from 2 July 2027 (`RECEIVED`) to 28 July 2028 (`CLOSED`) (`kentender_contracts/seeds/demo.py`, the `PROFILES` table). Contract Management is not described in SEED-002.

**2.4 The pinned clock drifts.** Measured 15 October 2026 at about 21:14 and 21:45 EAT: the development site's stored test clock read `2026-11-06 11:00:01`, last saved 10 October 2026 18:49, 22 days ahead of the real clock and not the documented 18 June 2027; the test site's stored clock was empty, last saved 20:42 the same day, while its canonical-world validation expects 18 June 2027. The Home browser helper already says why: "Other modules' browser fixtures clear the clock when they finish" (`tests/ui/smoke/home/helpers.ts` lines 28–30).

**2.5 Rows dated after the real clock on the development site** (measured 15 October 2026 at about 21:14 EAT, counted by `creation` or `modified` later than now): 5,101 of 171,755 Version rows, 305 of 658,261 Comments, 251 of 24,539 Files, 56 of 200 Notification Logs, 14 of 15 Funding Reservations, 26 of 36 Budget Audit Events, 30 of 55,742 Audit Events and 2 of 3 Intake Controls. Eight of the 16 Supplier User Assignments take effect between 1 and 4 March 2027.

**2.6 A live action can lose to a seeded one.** `departmental_needs/services/usage.py` (`project_planning_usage`) ignores an event whose time is earlier than the stored one ("Out-of-order delivery: the newer projection stands"). The seeded FY 2027/28 plan's usage events are dated 10 December 2026, so a real action on the same Need before then is ignored. The two-year plan recorded this on 5 October 2026 as BF-11 and left it as "a module decision, not this plan's".

**2.7 ERPNext cannot follow a simulated future.** CM-CHG-001 v0.8 follow-up FU-CM-61, verbatim: "**Native documents carry the real date, Contract Management the simulated one (B22).** ERPNext dates every native document today, so an invoice dated in a simulated July 2027 is refused by the native invoice (its due date, the real today, is earlier than the bill date). Decide how the seed world dates native documents (the adapter passing the trusted date with `set_posting_time`, or the seed world running on the real calendar)." Reading ERPNext shows both halves:

- A Purchase Invoice validates its due date against the supplier's bill date (`controllers/accounts_controller.py` lines 920–942, `validate_due_date`).
- A Purchase Receipt refuses a posting date later than the real today (`stock/doctype/purchase_receipt/purchase_receipt.py` lines 268–269: `if getdate(self.posting_date) > getdate(nowdate()): throw(_("Posting Date cannot be future date"))`).

So the adapter option can fix at most the invoice for a future moment, never the receipt. The real-calendar option fixes both. The Contract Management seed sets its own clock flag (`frappe.flags.kt_cm_clock`) and not the shared frozen clock that every other seed uses (`kentender_core/seeds/clock.py`), which is why native documents take the real date there.

**2.8 KT-STD-001 §8.4 still carries the old text.** KT-STD-001 v1.29 §8.4 lists "FY 2027/28 | 1 Jul 2027 – 30 Jun 2028 | Open, closing 25 Nov 2026, 23:59 EAT" and KT-STD-001 v1.29 §8.4A lists a "Site configuration history | 29 Jun 2026, 10:10 EAT". SEED-002 v0.7 Appendix C (the replacement the owner was to apply) was never applied. That old text describes a world read in October 2026, which is the world this proposal builds.

## 3. Decisions on record

Decisions RA-1 to RA-5 are the Project Owner's answers of 15 October 2026. The questions were put in the preceding report of that day; the answers are quoted verbatim.

| Ref | Decision | Owner's words, 15 October 2026 |
|---|---|---|
| RA-1 | The development site runs on the real clock with no pin; only the test site pins its clock, to the seed day. | "Decisions: 1. Yes" |
| RA-2 | In October the prepared year (FY 2027/28) stops at Departmental Needs. | "2. Departmental needs"; confirmed: "1. Correct", answering "I read decision 2 as Year 2 stopping at the needs stage, before departmental plans. Is that right?" |
| RA-3 | A closed FY 2025/26 is seeded. | "3. Yes, seed a closed FY" |
| RA-4 | Contract Management's literal 2027 and 2028 dates: the owner asked for a recommendation. Recommended: the dates are illustrative and the durations authoritative (§5). | "4. Recommend, and see the attached FU"; then "2. Yes" answering "Is a 6-month warranty on the closed-year contract acceptable?" and "3. Yes" answering "May I write the change proposal, implementation plan and tracker … and start with the dev-clock cleanup and the new guard?" |
| RA-5 | The recommendation set of the report of 15 October 2026: anchor the world to the seed day; store the anchor on the site; write every instant as an offset from it; derive the fiscal years from it; pin the clock to it on test sites only; let the development site run on real time; have the tests read the anchor. Order of work: the dev-clock cleanup and the guard; the seed dates as offsets (the portfolio first, then the test world); the tests and specs; the approved documents last. | "I accept all recommendations." |

Effect on the two-year decisions (kept as history, not rewritten): D1 (the as-at instant is 18 June 2027) is replaced by RA-5; D2 (a server without the test clock stays future-dated) is replaced by the rule in §1; D3 (a closed FY 2025/26 only if a command needs it) is replaced by RA-3; D5 (a capped year's records stop where the cap leaves them) is kept and extended by rule R5 (§4). D4, D6 to D12 are unchanged, except that D6's default world is "the furthest the anchor allows" (§4, R5).

RA-4 is recorded as accepted by the owner's later answers, which are consistent with it; the owner is asked to confirm it when reviewing this document (§9).

## 4. The model

New content, proposed for the owner's review (§10). The rules are stated here; the numbers they need are measured in Phase 1 of the plan.

**R1 Never ahead.** No simulated instant is later than the real clock: not an anchor, not a pinned test clock, not a demonstration profile's moment.

**R2 The anchor.** The anchor is the instant a seed run starts, stored on the site by the seed and read by validation, tests and browser specs. Where it is stored is settled in Phase 1; it is written only by the seed.

**R3 Years derived from the anchor.** Year 1 is the fiscal year that contains the anchor (carried out); Year 2 is the next (prepared); Year 0 is the previous (closed). Fiscal years stay 1 July to 30 June.

**R4 Two kinds of instant.** Planning journeys (budget, Needs, departmental plans, Annual Plan) keep a fixed relation to the fiscal calendar, as the existing seed does: Year 1's history is 364 days before Year 2's. Portfolio states (requisitions to award) are offsets from the anchor, so a Tender is "open for bids" or "awaiting the Accounting Officer" at whatever day the seed runs.

**R5 The ladders are capped by the anchor.** A stage whose dated work would fall after the anchor is not built. The default `NEXT` is the furthest stage the anchor allows, up to `annual_plan`; at 15 October 2026 that is `needs` (RA-2): Year 2's Needs on 24 November 2026 and its plan on 10 December 2026 are 40 and 56 days after the anchor. Explicit `CURRENT` and `NEXT` caps keep working and a cap beyond the anchor is refused with a message.

**R6 Seeding is unchanged.** Every command still runs at its fixture instant under the frozen seed clock (`seeds/clock.at`), because a command checks authority at command time and history is not back-stamped. Contract Management's seed joins it instead of using its own flag.

**R7 One clock policy per site** (built in Phase 0, §6.1). The development site is `off`; a test site is `never_ahead` and pinned to the anchor; a site without the key is `free`, today's behaviour, until the cut-over in Phase 3.

### 4.1 The world at 15 October 2026 (illustrative)

| Year | Period | Role | State at the anchor |
|---|---|---|---|
| Year 0 | FY 2025/26, 1 Jul 2025 – 30 Jun 2026 | closed | A configured, closed year with a small completed portfolio; depth settled in Phase 1 (§9, RA-OD2) |
| Year 1 | FY 2026/27, 1 Jul 2026 – 30 Jun 2027 | carried out | Plan Active since December 2025; 106 days of the year have passed; the portfolio's states are offsets from the anchor |
| Year 2 | FY 2027/28, 1 Jul 2027 – 30 Jun 2028 | prepared | Budget registered; Needs collected. The Needs window reads Open until 25 November 2026, as KT-STD-001 v1.29 §8.4 states |

### 4.2 Why the world cannot simply be shifted

Fiscal years are fixed, so a shift is only possible in whole years. Measured arithmetic (15 October 2026, 21:45 EAT):

- Year 1's authored execution runs 1 March to 18 June 2027, 109 days. At the anchor Year 1 has run 106 days. The history is three days longer than the year so far, before any minimum is applied.
- Year 2's authored Needs (24 November 2026) and plan (10 December 2026) are after the anchor.
- Year 1's authored planning history (needs 25 November 2025; plan approved 10 December 2025 and Active 11 December 2025) is before the year starts (the approval is 203 days before 1 July 2026) and stays as it is (SEED-002 v0.7 §A3).

### 4.3 The season

A reseed in July to mid-October finds too little of Year 1 elapsed to hold the portfolio's history. The world must always be seedable, so a run whose real day is outside the envelope anchors on the end of the envelope that is not later than today (in practice the previous June), prints a notice, and validation reports the world's age. Recommended; decided in §9 (RA-OD1). The start of the envelope is measured in Phase 1: as authored it is 109 days after 1 July, which is 18 October.

### 4.4 The world ages

A world anchored to a real day does not stay current. Its open tender closes and its Coming-up items pass in real time. Validation reports the anchor's age in days; the remedy is a reseed (about 3 to 8 minutes on the test site, plan SW-0407). On a test site the clock is pinned to the anchor, so a browser run is repeatable whatever the real day.

## 5. Contract Management (RA-4 and FU-CM-61)

**Recommendation.** Contract Management's calendar dates are illustrative; its durations are authoritative. FU-CM-61 closes by the real-calendar option (R1), with the adapter passing the trusted date to native documents as a secondary, optional change for moments in the past.

**Why the dates can move.** CM-CHG-001 v0.8 implementation plan D17: the demonstration contracts "use a separate synthetic source package (`CM-DEMO-AWD-01`, `CM-DEMO-TERMS-01`) and **never overwrite the canonical chain**". CM-CHG-001 v0.8 §10.1B states that "All dates without a year in §§10.2–10.5 are in 2027 unless a brief explicitly says 2028" and, of the base contract: "delivery due 20 July 2027; 12-month warranty from each unit’s acceptance event. The two replacement units are accepted on 27 July 2027, so their warranty ends 27 July 2028." The warranty length is a duration and stays; the year is a date and moves.

**How they move.** The demonstration set moves back as one block so that its last instant is not later than the anchor. The set spans 2 July 2027 (`RECEIVED`) to 28 July 2028, 11:00 (`CLOSED`), 392 days. At 15 October 2026 the block moves back at least 651 days: `RECEIVED` falls on about 18 September 2025 and the base warranty ends about 8 October 2026, so the 12-month warranty is kept and `WARRANTY` and `CLOSED` are both in the past. The date arithmetic is the proposal's; the exact offsets are chosen in the Contract Management phase.

**A correction to the report of 15 October 2026.** That report said the closed year needed "plan through contract for at least one contract" to hold Contract Management's long tail. Reading D17 shows the demonstrations use a synthetic package, so they do not need a Year 0 award chain. Year 0 is needed for Analytics' trailing months and, for the block above, for an ERPNext Fiscal Year 2025-2026 in which native documents dated September 2025 can post. The 6-month warranty the owner accepted ("2. Yes") is the fallback if a block shift proves impossible, not the plan.

**What has to be checked.** That the block's earlier dates are inside every authority and registration the contract needs (the supplier's account, the people's responsibilities, the site configuration history), and that the Finance and Budget side of an embedded payment accepts a September 2025 posting. Neither is verified (§10).

**Held.** The Contract Management session committed Phases 11 and 12 on 15 October 2026 (`dbfb213d`, `f5e72d61`) with the literal dates and, at 21:15, started a loop over its Python test modules. Its seed and tests are not touched until that session releases them (owner, "3. Yes", on the hold).

## 6. What changes

### 6.1 Built in Phase 0 (15 October 2026)

- `kentender_core/services/test_clock.py`: the policy (`free`, `never_ahead`, `off`; an unknown value reads as `off`), `stored_instant`, `ahead_of_real`, `describe`, `problem`. Under `never_ahead` setting an instant later than the real clock raises, and a stored one that is ahead is ignored. Under `off` nothing is stored or read, and a stored value can be cleared.
- `kentender_core/seeds/canonical.py`: `validate()` asks the policy what is wrong with the clock (`_clock_problem`); a site on the default policy keeps the rule that a test environment reads the as-at instant.
- `kentender_core/tests/test_test_clock.py`: 20 tests.
- The development site: `kt_test_clock_policy` set to `off` in its site configuration and the stale instant cleared.

### 6.2 Still to build

| Area | Change |
|---|---|
| `kentender_core/seeds/calendar.py` | `AS_AT` becomes the stored anchor; the fiscal years, `Year.at()` and an offset helper are functions of it; Year 0 added |
| Seed code | 44 files re-expressed as fiscal-calendar or anchor offsets, the portfolio first (151 dates in `portfolio.py`); responsibility terms, rule windows, supplier registrations and fiscal years (2025, 2026 and 2027) in `site_setup.py` |
| `canonical.py` | the anchor stored and read; the default `NEXT` from R5; the season notice; the anchor's age in validation; `set_as_at` pins the anchor under `never_ahead` |
| Tests and specs | Python tests and browser specs read the anchor and build their expected strings from it, never from a literal |
| Contract Management | the demonstration block re-timed; history under the shared frozen clock; FU-CM-61 closed; supplier and responsibility terms for the earlier dates |
| Documents | §7 |

## 7. Documents

Written under the document-change protocol after the code is proven, not before.

| Document | Change | Who |
|---|---|---|
| SEED-002 | A successor, v0.8, Proposed: §A1 (the anchor, the three years, the clock policy, the season, the world's age), §A3 (instants as offsets), §B1 (default `NEXT`), §B5 (the clock checks), §B6 (profile moments are not later than the anchor), Appendix C (the pointer text below). v0.7 stays as the approved baseline until the owner approves v0.8 | Claude, for the owner's approval |
| KT-STD-001 §8.4 and KT-STD-001 §8.4A | The pointer to SEED-002 owed since 5 October 2026 (SEED-002 v0.7 Appendix C, tracker SW-0104), now to name the anchor and no fixed date | The Project Owner (two-year decision D7) |
| HOME-CHG-001 v0.6, ANL-CHG-001 v0.8 | A note that their fixtures are illustrative and the seed's world is read at its anchor, not at 16–18 June 2027 (HOME-CHG-001 v0.6 §13 and ANL-CHG-001 v0.8 §13 already call the fixtures illustrative) | The Project Owner |
| CM-CHG-001 v0.8 §10.1B and the Contract Management boards | The dates are illustrative; the durations are authoritative (RA-4) | The Project Owner |
| CM-CHG-001 v0.8 follow-ups, FU-CM-61 | Closed by the real-calendar rule, with a pointer to this proposal | The Contract Management owner |
| KT-DOC-CTRL-001 | An entry for SEED-002 v0.8 when it is written; the earlier proposal files were not registered, so none is added for this proposal | The documentation owner |

## 8. Risks

- **The history does not fit.** At the anchor, three days short as authored; the legal minimums and whether a Requisition may be authorised before the year starts are not yet measured (Phase 1, spike A).
- **Hidden date assumptions.** About 1,150 Python test dates and 220 browser-test dates, plus module code, may assume the old world. Phase 1 classifies them before any is changed.
- **Dev with no pin shows ageing.** After the cut-over the development site shows a world that is real-time current on the day it is seeded and older each day. Reseed to refresh.
- **Demonstration profiles on dev.** With the policy `off`, profiles no longer move the development site's clock; walk them on the test site until the profiles are re-timed, or build the profile's state at the real now.
- **Weekdays.** A re-timed instant may fall on a weekend where an owner's working-day check refuses it; each is checked when moved.
- **Run time.** Year 0 adds a closed year to a build that takes 3 to 8 minutes today (plan SW-0407); measured in Phase 4.
- **Other sessions.** The Contract Management session is active in the same repository; the shared files carry other sessions' uncommitted hunks. Commit by hunk, never revert.

## 9. Decisions still open for the owner

| Ref | Question | Recommendation |
|---|---|---|
| RA-OD1 | A reseed in the season where Year 1 is too young: anchor on the previous June with a notice, or refuse? | Anchor on the previous June with a notice; the world must always be seedable |
| RA-OD2 | How deep is the closed Year 0? | Configuration, its closed budget and plan, and a small completed portfolio of three to four Tenders through to award, sized after Phase 1 measures what Analytics' months need |
| RA-OD3 | Confirm RA-4: Contract Management's dates are illustrative and its durations authoritative; the demonstration block moves back as a whole | Confirm |
| RA-OD4 | The age at which validation fails the world as stale rather than only reporting it | Report only at first; fail at 60 days on a test site, where a browser run must be repeatable |

## 10. New content for review, and what is not verified

**New content, not from an approved source:**
- Rules R1 to R7, the decision numbering RA-1 to RA-5 and RA-OD1 to RA-OD4, and the identifiers RA-PROP-001 (this proposal), RA-PLAN-001 (the plan) and RA-TRK-001 (the tracker).
- The clock policy names `free`, `never_ahead` and `off` and the site-configuration key `kt_test_clock_policy`.
- The statement that Year 0 is built by the same machinery as Year 1, one more year earlier.
- The block shift of 651 days and its dates (arithmetic only).
- The 60-day staleness figure.

**Not verified:**
- Whether a Requisition or a reservation can be dated before its fiscal year starts (Planning requires a late-activation explanation when a plan is adopted after the year starts, `plan_governance.py`; nothing equivalent was found for Requisitions, and none was run).
- The legal minimum for each step of the executed chain, and so the shortest honest Year 1 history.
- Whether Analytics' months need a Year 0 portfolio of the proposed depth.
- Whether a September 2025 posting is accepted by the embedded Finance side of Contract Management, and by Budget.
- How many of the counted dates are story instants and how many are comments or unrelated.
- That a stale value on the test site's clock was left by the Contract Management session; only that it was saved at 20:42 on 15 October 2026 is known.
- HOME-CHG-001 v0.6 and ANL-CHG-001 v0.8 were not read; their read time is quoted from SEED-002 v0.7 §A1.
