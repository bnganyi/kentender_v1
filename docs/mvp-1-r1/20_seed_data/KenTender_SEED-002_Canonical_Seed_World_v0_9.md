# SEED-002 — Canonical Seed World

| Control | Value |
|---|---|
| Document ID | SEED-002 (new; the identifier is proposed for the Project Owner's confirmation) |
| Version | 0.9 (v0.8: approved 15 October 2026; v0.7: approved 11 October 2026; v0.6: proposed 10 October 2026, superseded as the proposal by v0.7; v0.5: proposed 10 October 2026, superseded as the proposal by v0.6; v0.4: proposed 9 October 2026, superseded as the proposal by v0.5; v0.3: approved 8 October 2026; v0.2: proposed 8 October 2026 and superseded before approval; v0.1: proposed 5 October 2026) |
| Date | 16 October 2026 (v0.8: 15 October 2026; v0.7: 9 October 2026; v0.3: 8 October 2026; v0.1: 5 October 2026) |
| Status | **Approved — 17 October 2026** (v0.9 was put forward on 16 October 2026; v0.8 read: **Approved — 15 October 2026**; v0.7 read: **Approved — 11 October 2026**; v0.3 read: **Approved — 8 October 2026**) |
| v0.8 proposed status (retained) | Proposed — 15 October 2026; v0.7 is the approved baseline |
| Approved on | 17 October 2026 (v0.8: 15 October 2026; v0.7: 11 October 2026; v0.3: 8 October 2026) |
| Approval record | Project Owner, 17 October 2026, verbatim: “SEED-002 v0.9 is approved”, in a message that also answered “Test-site repair: repair it” and “Reseed dev site”. (v0.8 record, retained: Project Owner, 15 October 2026, verbatim: “3. Approved”, answering the third of the four questions of the report of that day, which asked the owner to approve SEED-002 v0.8 and KT-STD-001 v1.30. The same message answered “1. Keep 1 Jul to 30 Jun” (RA-OD5), “2. Yes” (“the new document” is the proposal RA-PROP-001 v1 and its companion plan and tracker) and “4. Yes” (add CM-CHG-001 v0.8 to the register). v0.8 is approved with the RA-OD5 answer written into §A1.1, §A1.2 and Appendix D question 5; the text first proposed on 15 October 2026 left it open (kept beside each change as “Proposed read”). Approval does not establish implementation, test coverage or production readiness: only Phase 0 of `Real_Date_Anchor_Implementation_Plan.md` is built. (Proposed read: None for v0.8.) v0.7 record, retained: Project Owner, 11 October 2026: “Mark the documents as approved”, answering the report of the proposed set BDS-CHG-001 v0.16, TPR-CHG-001 v0.20, STD-TPL-001 v0.17, BOP-CHG-001 v0.15, TRUST-ADR-001 v0.6, AUTH-ADR-001 v1.15, SEED-002 v0.7 and TRUST-OPS-001 v0.1. The proposals each carries in full are approved with it. (v0.3 record, retained: Project Owner, 8 October 2026, verbatim: “SEED-002 v0.3 is approved.”, answering the report that EVL-CHG-001 v0.8, KT-STD-001 v1.27 and PRC-CHG-001 v0.12 were approved and SEED-002 v0.3 remained Proposed because its approval also retires SEED-001 and SEED-OPS-001.)) |
| v0.4 approval record | Approved with the current version: Project Owner, 11 October 2026: “Mark the documents as approved”, answering the report of the proposed set BDS-CHG-001 v0.16, TPR-CHG-001 v0.20, STD-TPL-001 v0.17, BOP-CHG-001 v0.15, TRUST-ADR-001 v0.6, AUTH-ADR-001 v1.15, SEED-002 v0.7 and TRUST-OPS-001 v0.1. The proposals each carries in full are approved with it. |
| v0.5 change | The tender-security intake duty. Charles Mutiso (Head of Procurement Function) assigns the duty for each Tender to **Mercy Kilonzo**, an existing Procurement Planner who sits on no opening or evaluation, and Mercy records each physical original; Charles records none (v0.4 read: Charles Mutiso recorded them). The seed assigns the duty before the first intake, validates the assignment and the absence of conflicts, and matches no intake to a bid until the opening has started. Basis: the Project Owner's decisions of 10 October 2026 (quoted in BDS-CHG-001 v0.14, AUTH-ADR-001 v1.13). |
| v0.5 owner instruction | The Project Owner instructed on 10 October 2026, verbatim: “Correct the tender-security intake and sealed-bid confidentiality gap across requirements, implementation and fixtures.”; on the intake duty: “Remove tender-security intake permission from the default HOPF permission bundle. Allow the HOPF to assign the intake duty explicitly to an existing eligible officer, using KenTender’s existing assignment mechanism and scoped to the relevant tender. The assignment grants only the access necessary to record security receipt and issuer confirmation. HOPF status, opening membership and evaluation membership must not independently grant that access.” “For the demonstration, assign an existing officer with no opening or evaluation appointment. Do not create a new staff persona solely for this duty.”; on separation: “Enforce separation between security intake and opening/evaluation duties on the same tender. Record this as an approved product policy, without presenting it as a statutory prohibition.” “Check assignments in both directions: assigning intake must reject an opening/evaluation participant, and appointing an opening/evaluation participant must reject an intake officer.” “Ending intake access must not erase prior exposure. An officer who has already accessed supplier-identifying security information or recorded intake for that tender must remain ineligible for its opening/evaluation duties. An unused assignment may be revoked before appointment.”; on administrator access: “Administrator and System Manager status must not grant pre-opening access to sealed-bid existence, counts, identities, contents, submission receipts or supplier-identifying security intake.” “The limited incident operator may access only the operational information necessary under TRUST controls.”; and on the demonstration verification service: “Preserve DEC-044’s removal of general test banners and strips. Store the verification source as “Test Issuer Service (simulation)” and show it in the normal verification details alongside the result and response time.” |
| v0.6 change | Every canonical Tender states how its tender security may be submitted (**Electronic**) and that an original is delivered (**Required**), the two statements the Tender now carries (TPR-CHG-001 v0.19 §23.1); the supplier-facing security status reads **Original received** / **Original receipt not yet recorded** (BDS-CHG-001 v0.15 §4.8) and the validation checks them. New content for owner review: the choice of Electronic with a required original for every canonical Tender, which keeps the behaviour of v0.5. |
| v0.6 owner instruction | The Project Owner instructed on 10 October 2026, answering five open decisions (quoted in part, verbatim): on the supplier status wording: “exposes internal processing and suggests something is wrong” (of “Not yet matched”), replaced by the statuses “Original received”, “Original receipt not yet recorded” and “Issuer verification pending”, with the explanation “Security will be checked against your bid after opening.” and the rule “Deferred matching must not make a complete bid appear incomplete.”; on the template and published Tender data: “Security required” must not automatically mean “physical original required”, so the Tender states the permitted submission method and the original-delivery requirement; on incident records: “System Manager status alone must not grant access”; on emergency access to sealed bids: no unrestricted break-glass access, and “Its absence does not justify an administrator bypass.”; and on scope: “Implement 2–4 now, update their requirements and tests, and record 5 as an explicit production-readiness item, distinguishing operational recovery from access to sealed contents.” |
| v0.9 change | The anchor model of v0.8 is built and its offsets are stated as built (§A3.1): the stored anchor and how a run chooses it (§A1.1 R2, the season rules), the mapping of the story's instants into the world, Year 0's content (§A7), the command and its options (§B1, §B4), the validation of the anchor and of the recorded events (§B5), the troubleshooting rows (§B7) and the new content for review (Appendix D). Nothing about the story's people, money or states changes. The figures in the tables are those of an anchor on 9 October 2026 10:00 EAT. What the build and its validation showed on `kentender-test.local` is recorded under Evidence. |
| v0.9 owner instruction | The Project Owner instructed on 16 October 2026, verbatim: “Complete all the phases without stopping, then list the CM documentation update as follow ups”, answering the plan `Real_Date_Anchor_Implementation_Plan.md` that v0.8 approved. The Contract Management documentation updates are listed in the change report as follow-ups; none is made here. |
| v0.8 change | The canonical world is read as at the **anchor**, the instant a seed run starts, and no simulated instant is later than the real clock (§A1.1, §A6). Three financial years: Year 1 (carried out) is the one that contains the anchor, Year 2 (prepared) the next and Year 0 (closed) the previous; the prepared year goes as far as the anchor allows, which at 15 October 2026 is Departmental Needs. Every instant in §A2 to §A5 is read as illustrative: the instant a row stands for is an offset, recorded in v0.9 when the build fixes it (**Awaiting fixture**). A site's test clock follows a policy: the development site `off`, a test site `never_ahead` and pinned to the anchor (§B2, §B5). A closed FY 2025/26 is seeded (§A7) and Contract Management's demonstrations are placed as one block not later than the anchor (§A8). The fiscal year stays 1 July to 30 June because CFG-CHG-002 v0.19 requires it; the owner's wish to be able to shift it conflicts with that requirement, and the owner decided on 15 October 2026 to keep 1 July to 30 June (§A1.2, Appendix D question 5). (Proposed read: the owner's wish to be able to shift it conflicts with that requirement and is an open question.) v0.7's 18 June 2027 world is retained as the story's shape and is what the seed still builds until Phase 3 of `Real_Date_Anchor_Implementation_Plan.md`. Basis: RA-PROP-001 v1, approved by the Project Owner on 15 October 2026; CM-CHG-001 v0.8 follow-up FU-CM-61. |
| v0.8 owner instruction | The Project Owner instructed on 15 October 2026, verbatim: “The side effects are significant, and at the same time I do not see any scenarios in the reasons given that cannot be overcome by careful preparation of the seed data that revolves around the real today. Revisit the seed data documentation and implementation and let me know”; “I accept all recommendations.”; “The new document is approved, but I also need you to harmonize the rest of the affected documents including the register.”; and on the open decisions: “Decisions: 1. Nothing mandates a fiscal year to start on July 1. You can always shift it to simplify the seeding if necessary. Check how the shift works with ERPNext. 2. Agreed 3. Accepted 4. Accepted”. The fiscal-year check is recorded in §A1.2. On the questions of the report that followed, verbatim: “1. Keep 1 Jul to 30 Jun”, “2. Yes”, “3. Approved” and “4. Yes”. |
| v0.7 change | Every canonical Tender states its tender-security method as **Bidder uploads an electronic instrument** with the original **Required** (v0.6 read: Electronic), and the world is bound to template release 1.5 (STD-TPL-001 v0.17). No other canonical fact changes. |
| v0.7 owner instruction | The Project Owner instructed on 10 October 2026, answering the follow-up decisions (quoted in part, verbatim): on the addendum process: “Use the existing addendum process. Do not introduce a separate kind of addendum or republish the tender as a new procurement. Extend the existing addendum mechanism to amend the structured security submission method and original-delivery requirement.” “Missing system data, requirement already explicit in the published tender: populate the structured data through an auditable correction that preserves the published requirement.”; “Requirement genuinely changing: issue a formal addendum before closing, communicate it to bidders and apply the applicable deadline-extension rules.”; “Closed tenders must retain their issued requirements.”; on the template release: “Make proof upload conditional in the next template release, now.” with the behaviour table (Bidder uploads an electronic instrument: require the instrument attachment; Issuer supplies the instrument directly: use the issuer-supplied instrument and avoid a duplicate bidder upload; Paper instrument requiring an original: require the prescribed electronic copy and show the original-delivery instructions; No security required: hide the security inputs and proof upload), and “Apply the new release to new tenders and unpublished drafts through an explicit update. Published tenders retain their release unless formally amended. A pending issuer response must not automatically become a new submission blocker.”; on incident-detail auditing: “Yes—build incident-detail read auditing now.” … “Record the actor, time, incident, action, access purpose and outcome for detail reads and exports. Keep sensitive contents out of the audit event and restrict access to the audit trail itself. Background refreshes should not generate misleading duplicate “user read” events.”; and on PR-001 and closure: “Have Claude Code draft PR-001’s recovery procedure. It should cover incident declaration, authorised support access, permitted diagnostics, recovery without exposing sealed contents, evidence preservation, escalation when opening cannot proceed, and closure review. Test the procedure before production. Any exceptional access to sealed contents remains a separately reviewed design.” and “The outstanding closure work also needs completing: update the Documentation Control workbook to match the register” |
| v0.5 approval record | Approved with the current version: Project Owner, 11 October 2026: “Mark the documents as approved”, answering the report of the proposed set BDS-CHG-001 v0.16, TPR-CHG-001 v0.20, STD-TPL-001 v0.17, BOP-CHG-001 v0.15, TRUST-ADR-001 v0.6, AUTH-ADR-001 v1.15, SEED-002 v0.7 and TRUST-OPS-001 v0.1. The proposals each carries in full are approved with it. |
| Replaces | On approval (8 October 2026): **SEED-001** Harmonized End-to-End Fixture (approved v1.4) and **SEED-OPS-001** Canonical Site Seed Runbook (approved v1.24; v1.25 proposed, never approved). Both are retired as history from 8 October 2026, not amended (Appendix A records what each rule became). |
| Basis | Two-year seed world proposal, decisions D1–D7 (Project Owner, 4 October 2026: "Decisions for the owner: recommendations accepted"); fixture answers D8–D10 ("1. Accepted 2. Accepted 3. Accepted"); D11 ("include documentation revamp as one task. If it is easier, the current document can be retired completely so the next version can start on a clean slate without the previous baggage."); D12 ("one new document to replace both the fixture document and the runbook"). Plan and tracker: `Two_Year_Seed_World_Implementation_Plan.md`, `Two_Year_Seed_World_IMPLEMENTATION_TRACKER.md`. (v0.8) The real-date anchor proposal RA-PROP-001 v1 (`KenTender_Seed_World_Real_Date_Anchor_Proposal_2026-10-15.md`, approved 15 October 2026), its plan `Real_Date_Anchor_Implementation_Plan.md` and its tracker `Real_Date_Anchor_IMPLEMENTATION_TRACKER.md`. |
| Owner | `kentender_core` (`kentender_core/kentender_core/seeds/canonical.py`, `calendar.py`, `portfolio.py`) |
| v0.4 change | Annual Plan publication. For MVP 1 the Procurement Planner (Mercy Kilonzo) records the Treasury submission and the entity-website publication in one **Confirm plan publication**, and the system activates the plan through its existing checks. The seed no longer has the Accounting Officer record Treasury evidence and no longer publishes through the sandbox adapter, so it creates no publication attempt, acknowledgement or intent. Basis: the Project Owner's instruction of 9 October 2026 (quoted in PLN-CHG-001 v1.31, change scope); PLN-CHG-001 v1.31 §§5.5.2.2, 5.5.2.4, 13.3 and PLN31-AC-017. Required PLN-CHG-001 v1.31 approval first. The two Treasury reference values and the two publication dates are unchanged; the public plan URLs are new content for review (below). |
| v0.3 change | The evaluation secretary. The Head of Procurement Function (Charles Mutiso) is recorded as secretary by office when the Accounting Officer appoints each committee, and delegates to Brian Wafula at the earlier assignment instant; the seed no longer assigns a secretary through a task. Basis: the Project Owner's instruction of 8 October 2026 (quoted in EVL-CHG-001 v0.8); EVL-CHG-001 v0.8 §3; KT-STD-001 v1.27 §8.3. v0.2 is superseded by this version, so the register names one proposal. No other rule changes. |
| v0.2 change | Staff home organisation units. The shared register now has five units (KT-STD-001 §8.2, v1.26 approved 8 October 2026) and records each Evaluation fixture person's home unit (KT-STD-001 §8.3A). The site stage records them through CFG-CHG-002 v0.19 `SetStaffHomeOrganisationUnit`; the Evaluation commands read a committee member's department from the home unit and generate the appointment reference, so the seed passes neither (EVL-CHG-001 v0.7 §3). No other rule changes. Basis: the Project Owner's approval of 8 October 2026, “Approved. Proceed”, of AUTH-ADR-001 v1.12, CFG-CHG-002 v0.19, KT-STD-001 v1.26 and EVL-CHG-001 v0.7. |
| Shared register | KT-STD-001 §8.1–§8.3 (site, units, people) stays the shared fixture register. Its §8.4 (Fiscal years) and §8.4A (Fixture instants) are replaced by this document's Part A §A3 when the Project Owner applies the pointer in Appendix C. (v0.8: the pointer is KT-STD-001 v1.30, approved 15 October 2026; Appendix C records the v0.8 text. Proposed read: the pointer is proposed as KT-STD-001 v1.30, 15 October 2026.) |
| Evidence | Built and validated on `kentender-test.local` on 5 October 2026 (commits bedf8a5b and later; Appendix B lists the generated references). Approval of this document does not establish implementation, test coverage or production readiness. (v0.8: only Phase 0 of `Real_Date_Anchor_Implementation_Plan.md` is built, the site clock policy in `kentender_core/services/test_clock.py` (20 tests on `kentender-test.local`, 15 October 2026); the anchor model is a requirement not yet built.) (v0.9: the anchor model is built and was run on `kentender-test.local` on 16 October 2026 at an anchor of 9 October 2026 10:00 EAT (`CURRENT=award`, `NEXT` by default Departmental Needs). A rebuild takes 6 to 8 minutes (362 s on its own at the first run, 7 min 48 s on the last) and validates; a plain rerun through `make seed-canonical ANCHOR=real` removes the strays and changes nothing else. Tests: `kentender_core.tests.test_calendar` (37 pure tests) and `test_canonical_seed` (40, with `TestAnchoredWorld`) pass. Of 213 Python test modules run on the site (the 144 that name a date, re-run after the fixes they showed, and Contract Management's 64 service modules) 204 pass (2,671 tests) and 9 fail, none for a reason that depends on the anchor (see the change report). Contract Management: all 64 service modules pass; the nine demonstration profiles load at instants from 2 July 2025 to 28 July 2026, validate and clean up. Home's browser specs: 40 of 40 pass. **Not run:** the Contract Management, Planning and Tender browser specs and the other dated browser specs; the clock policy `never_ahead` (the test site stays `free`); the development site is not yet reseeded.) |

**Controlling decision.** A KenTender site has exactly one canonical world: two financial years read as at **18 June 2027, 10:00 EAT**. **FY 2026/27** is the year being carried out: its plan is Active and locked, and requisitions, Tenders, bids, openings, evaluations and awards run against it. **FY 2027/28** is the year being prepared: its budget, Needs, departmental plans and, at most, its approved Annual Plan. Everything else on a site (browser-test worlds, isolated profiles, hand-made drafts) is disposable. One command removes the disposable rows, reseeds the canonical ones through the same commands the screens use, and refuses to report success unless the result validates.

**Controlling decision (v0.8).** The world is read as at the **anchor**, the instant a seed run starts, never as at a date ahead of the real clock. It carries three financial years: the one that contains the anchor is carried out (Year 1), the next is being prepared (Year 2) and the previous is closed (Year 0). (v0.7 read: two financial years read as at 18 June 2027, 10:00 EAT.) The v0.7 paragraph above is retained as the story's shape; §A1.1 states the rules that replace its date.

---

# Part A — The world

## A1. One moment, two years

| | Value |
|---|---|
| The as-at instant | **18 June 2027, 10:00 EAT** (`calendar.AS_AT`) — the read time of HOME-CHG-001 v0.6 H10–H12 and ANL-CHG-001 v0.8 dataset A1. Every recorded fixture event is at or before it; every live deadline is after it. |
| Year 1 | **FY 2026/27** (1 Jul 2026 – 30 Jun 2027), carried out. |
| Year 2 | **FY 2027/28** (1 Jul 2027 – 30 Jun 2028), being prepared. Nothing is bought against it. |
| The clock a test site reads | A test site (site_config `kt_bds_simulation_environment`) runs its live pages on the as-at instant through the site test clock; the seed sets it at the end of every run. A site that is not a test environment reads the real clock (decision D2: until the story is moved, such a site shows a story dated ahead of the real calendar). |
| How the dates are made | Every seeded command runs **at** its fixture instant under the frozen seed clock (`kentender_core.seeds.clock`); nothing is back-stamped. Year 2 keeps the module seeds' instants; Year 1's planning history is the same journey **364 days (52 weeks) earlier**, so each event keeps its weekday and spacing. Year 1's execution keeps its own March–July 2027 instants. |

**v0.8 reading of this table.** The first row (the as-at instant) and the fourth (the clock a test site reads) are replaced by §A1.1; the other rows keep their v0.7 wording as the story's shape. (v0.7 read: the as-at instant is 18 June 2027, 10:00 EAT, and a site that is not a test environment reads the real clock, so it shows a story dated ahead of the real calendar, decision D2.) Until Phase 3 of `Real_Date_Anchor_Implementation_Plan.md` the seed still builds the v0.7 world.

**v0.9 reading.** Phase 3 is built: `make seed-canonical` stores the anchor and builds the anchored world (`ANCHOR=real`, the default once the cut-over is made); `ANCHOR=story` builds the v0.7 world unchanged, read as at 18 June 2027. The sentence above is retained as v0.8's reading.

### A1.1 The anchor model (v0.8)

| Rule | Statement |
|---|---|
| R1 Never ahead | No simulated instant is later than the real clock: not the anchor, not a pinned test clock, not a demonstration profile's moment. A native ERPNext document carries the real date and refuses a later one (CM-CHG-001 v0.8 follow-up FU-CM-61; ERPNext `purchase_receipt.py`: "Posting Date cannot be future date"). |
| R2 The anchor | The instant a seed run starts, stored on the site by the seed and read by validation, tests and browser specs. Where it is stored is **Awaiting decision** (Phase 1, spike D of `Real_Date_Anchor_Implementation_Plan.md`). (v0.9: decided. It is the site default `kt_seed_world_state`, a JSON object with `mode` (`anchored`), `anchor`, `started` (the run's start) and `season_notice`. `kentender_core.seeds.calendar.prepare` stores it in a process of its own, because the seed modules read it once, when they are imported; a process that finds it changed raises `AnchorChangedError`. The anchor is the latest Friday 10:00 not later than the run's start, since the story's own instant, 18 June 2027 10:00, was a Friday: every shift is a whole number of weeks and every event keeps its weekday.) |
| R3 Years | Year 1 is the financial year that contains the anchor (carried out); Year 2 is the next (prepared); Year 0 is the previous (closed). Financial years run 1 July to 30 June (CFG-CHG-002 v0.19 CFG10-EC-001). The clear of §B3 keeps the three years the anchor derives. |
| R4 Two kinds of instant | Planning journeys (budget, Needs, departmental plans, Annual Plan) keep a fixed relation to the fiscal calendar, as in v0.7; portfolio states (requisitions to award) are offsets from the anchor, so a Tender is open for bids or waiting for the Accounting Officer on whatever day the seed runs. |
| R5 Ladders capped by the anchor | A stage whose dated work would fall after the anchor is not built. The default `NEXT` is the furthest stage the anchor allows, up to `annual_plan`; at 15 October 2026 that is `needs` (owner decision RA-2). An explicit cap beyond the anchor is refused with a message. |
| R6 Seeding is unchanged | Every command runs at its fixture instant under the frozen seed clock (`kentender_core.seeds.clock`); nothing is back-stamped. Contract Management's seed joins it (§A8). |
| R7 The clock per site | A site's `kt_test_clock_policy`: `free` (no key; v0.7's behaviour, until the cut-over), `never_ahead` (an instant later than the real clock is refused when set and ignored when read; a test site, pinned to the anchor) or `off` (no pinned clock; the development site). An unrecognised value reads as `off`. |

**The world ages.** A world anchored to a real day ages in real time: its open Tender closes and its Coming-up items pass. Validation reports the anchor's age in days and, on a test site, where a browser run must be repeatable, fails the world at 60 days (owner decision RA-OD4: "4. Accepted", of the recommendation to report only at first and fail at 60 days on a test site). The remedy is a reseed.

**The season (open until the owner decided it on 15 October 2026).** At 15 October 2026 Year 1 has run 106 days (1 July to 15 October); the v0.7 history of the executed year runs 109 days (1 March to 18 June 2027), so on a day early in the year the history does not fit. The owner decided RA-OD5 on 15 October 2026 (“1. Keep 1 Jul to 30 Jun”; §A1.2, Appendix D question 5): the financial year stays 1 July to 30 June, and a run on such a day anchors on the end of the season (the previous June) with a notice, as the report of that day put the choice. The start of the season is measured in Phase 1 (spike A). (v0.9: a run anchors on the end of a season, with a notice, in two cases. **Early:** fewer than `calendar.SEASON_MIN_ELAPSED_DAYS` = 100 days of the financial year have elapsed at the anchor, so the run anchors on the latest anchor-day (the Friday on or before 18 June) of the previous year. **Late:** the run falls after its own season's end, in the last days of June, so it is held to the Friday on or before 18 June, because a Plan Item's invitation, its schedule and its delivery must fit by 30 June. The value 100 is kept: spike A (do the services accept an invitation date before the year begins?) was answered on 16 October 2026, and they do. At an anchor 100 days into the year the executed chain begins before the year does: the first invitation is on 25 May and the first requisition on 22 June, and the rules in force reach back to 1 January of the first seeded year for that reason (§B2).) (Proposed read: Two ways to meet that are put to the owner as RA-OD5 (§A1.2, Appendix D question 5): keep 1 July to 30 June and anchor on the end of the season (the previous June) with a notice, or shift the fiscal year. **Awaiting owner decision.** The start of the season is measured in Phase 1 (spike A).)

### A1.2 The fiscal-year check (v0.8)

Project Owner, 15 October 2026: "Nothing mandates a fiscal year to start on July 1. You can always shift it to simplify the seeding if necessary. Check how the shift works with ERPNext." Checked on 15 October 2026 by reading ERPNext (`accounts/doctype/fiscal_year/fiscal_year.py`) and by probes on `kentender-test.local` that were rolled back (no row left):

- **ERPNext** accepts a Fiscal Year that starts on any date: 1 June 2052 to 31 May 2053 was accepted. The end date must be exactly one year after the start, less a day, otherwise it raises `InvalidDates` ("Fiscal Year End Date should be one year after Fiscal Year Start Date"), unless the year is flagged short. The name is free text. A year that overlaps another year of the same company is refused: 1 June 2026 to 31 May 2027 against the site's 2026-2027 was refused, so a shifted year could replace the site's years only by changing or removing them first.
- **KenTender** is stricter than ERPNext. CFG-CHG-002 v0.19 CFG10-EC-001 reads: "Retain the existing project fiscal-year contract: 1 July–30 June, generated from a start year. The display FY 2027/28 means 1 July 2027–30 June 2028. This is not overridden to fit a seed." CFG10-AC-009 reads: "Fiscal year dates cannot be overridden through the UI or a direct API call." The error `CFG_FY_DATES_INVALID` reads: "Financial-year dates must run from 1 July to 30 June." The add-year command (`kentender_core/services/site_configuration.py` `add_fiscal_year`) writes 1 July to 30 June, and the Strategy register's plan-period label reads financial years as July to June (`kentender_strategy/services/strategy_ui_contracts.py` `_period_fy_label`).

So the shift works in ERPNext but conflicts with an approved KenTender requirement, and a shifted year needs CFG-CHG-002 amended first. This version therefore keeps 1 July to 30 June. **Decided 15 October 2026 (RA-OD5): the financial year stays 1 July to 30 June** (Project Owner: “1. Keep 1 Jul to 30 Jun”); CFG-CHG-002 v0.19 CFG10-EC-001 and CFG10-AC-009 are unchanged. (Proposed read: **Awaiting owner decision RA-OD5.**)

**Each year's planned dates fit inside that year** (decision D8). Needs and departmental-plan requirements refuse a Required by outside their year, and Planning blocks an item whose baseline signing plus delivery ends after its completion boundary (`PLN_DELIVERY_BOUNDARY_INSUFFICIENT`). So every Year 1 Required by is 30 June 2027 at the latest, and each Year 1 item's approved invitation date (February–March 2027) leaves room to finish by then. Year 1's Tenders publish in April–May 2027, later than those approved dates, which Planning reads as Baseline lateness (ANL-M-05).

**Only off-the-shelf IT equipment can be bought.** The one installed Tender format is `IT-EQUIPMENT-OPEN-V1`; Requisitions admit nine equipment categories, Tenders eight (Laptop, Desktop computer, Tablet, Monitor, Printer, Scanner, Network equipment, Power-protection equipment). Every executed item is one of these.

## A2. Site and people

KT-STD-001 §8.1–§8.3 is the register: Procuring Entity `PE-MOH` (Ministry of Health, Africa/Nairobi), the three units (Directorate of Digital Health and Policy, Digital Health under it, Human Resources Management and Development), and every named person. This world adds no person. (v0.2: five units — the three above and ICT and Finance, each directly under the root — by KT-STD-001 §8.2 (v1.26).)

**Tender-security intake duty (v0.5).** The duty is a Tender-scoped responsibility (AUTH-ADR-001 v1.13 §4.4) that the Head of Procurement Function, Charles Mutiso, assigns for each Tender to an existing officer; the world adds no person for it. “For the demonstration, assign an existing officer with no opening or evaluation appointment. Do not create a new staff persona solely for this duty.” **Mercy Kilonzo** (Procurement Planner; she records the plan publication in §A4.3) is that officer: she is on no opening committee and no evaluation, is not the Head's office holder, and holds no technical account. For every Tender with a security requirement the bid stage assigns her the duty before her first intake; the assignment records Charles as assigner, the Tender and an open period. The earlier fixtures' original intake records, made by Charles, are not rewritten: where a world still carries them they are flagged as conflicts for the Accounting Officer to resolve, and the disposable canonical world is rebuilt with Mercy as recorder.

Dated responsibilities (all others are open-ended; `site_setup.ASSIGNMENTS`):

**Home organisation units (v0.2).** The site stage records where each person works through `SetStaffHomeOrganisationUnit` (CFG-CHG-002 v0.19), after the units and the people exist and before any appointment; it never writes the field and grants no authority (AUTH-ADR-001 v1.12 §4.8). KT-STD-001 §8.3A lists them: Grace Wambui in Human Resources Management and Development, Peter Mugo and Samuel Otieno in ICT, Ruth Achieng in Finance (`site_setup.HOME_UNITS`). Everyone else, Esther Muthoni included, has none: **Not recorded** is a valid state and the world's fixture for it. Samuel Otieno's expired Head of User Department term below is a separate fact and is unchanged.

| Person | Responsibility | Term | Why |
|---|---|---|---|
| Esther Muthoni, Dr Alfred Ochieng | Strategy Author, Strategy Approver | from 1 Jul 2023 | the 2023 Strategy baseline (owner, 26 Sep 2026: "Backdate") |
| Samuel Otieno | Head of User Department, Directorate | 2 Jan – 1 Sep 2025 (expired) | the register's expired appointment, before Year 1's history |
| Dr Peter Kimani | Head of User Department, Directorate | from 2 Sep 2025 | covers Digital Health through the parent unit (owner, 26 Sep 2026, D4) |
| Julia Njeri | Head of User Department, Digital Health, **Acting** (`MOH/HR/ACT/2025/041`) | 2 Oct – 1 Dec 2025 | accepts Year 1's Digital Health Needs and certifies its departmental plan (26 Nov 2025) |
| Dr Peter Kimani | Head of User Department, Digital Health | from 2 Dec 2025 | takes Digital Health over; decides Year 2's Digital Health Needs |

The supplier companies (KT-STD-001 v1.14 §8.3) register their accounts through Supplier Accounts' own commands before the first executed bid: Afya Digital Supplies Limited 1 Mar 2027 09:00, Jirani Office Supplies Limited 2 Mar 09:00, Pwani Tech Distributors Limited 3 Mar 10:00, Mlima Computer Solutions Limited 4 Mar 14:00. Every seeded person signs in with the shared fixture password (`kentender_core.seeds.constants.TEST_PASSWORD`, also in `.env.ui`).

## A3. Fiscal years and fixture instants

(Replaces KT-STD-001 §8.4 and §8.4A — Appendix C.)

**(v0.8) Instants are offsets.** Every date and time in §A2 to §A5 (the responsibility terms, the supplier registrations, the tables below, each Tender's dates and Year 2's dates) is the v0.7 story's shape, read as illustrative. The instant a row stands for is an offset from the anchor (portfolio states) or from the fiscal calendar (planning journeys), never later than the anchor (R1, R4). The offsets are **Awaiting fixture**: Phase 1 measures the shortest honest history and v0.9 records the offsets as built. Until then the seed builds the v0.7 dates.

| Year | Period | Role | Needs submission at the as-at instant |
|---|---|---|---|
| FY 2026/27 | 1 Jul 2026 – 30 Jun 2027 | Year 1, carried out | Closed (its intake closed 26 Nov 2025, 23:59) |
| FY 2027/28 | 1 Jul 2027 – 30 Jun 2028 | Year 2, being prepared | Closed (closed 25 Nov 2026, 23:59; on the real calendar before then it reads Open) |

| Purpose | Instants (EAT) |
|---|---|
| Strategy baseline | 1 Jul 2023, 08:00–09:15 (the Version 2 profiles keep 24–25 Nov 2026) |
| Year 1 Budget | created 2 Oct 2025 09:20, lines 15:55, submitted 16:20, approved 4 Oct 2025 11:15; external approval dated 1 Oct 2025 |
| Year 1 Needs | 25 Nov 2025, 09:00–14:00; decisions 25–26 Nov 2025 |
| Year 1 departmental plans | opened 26 Nov 2025; certified 10:30 (Digital Health) and 11:00 (HRMD); accepted 28 Nov 2025 14:00 and 14:05 |
| Year 1 Annual Plan | items formed 2 Dec 2025; funding requested 4 Dec, confirmed 5 Dec 10:00; signed 8 Dec 10:00; adopted 9 Dec 10:00; approved 10 Dec 11:00; publication confirmed by the Planner and Active 11 Dec 2025 15:00 (Treasury submission date 11 Dec 2025; website publication date 11 Dec 2025) |
| Year 1 execution | Requisitions 1 Mar – 16 Jun 2027; Tenders 16 Mar – 16 Jun 2027; bids, openings, evaluations and awards to 18 Jun 2027 09:00 |
| Year 2 Budget | created 1 Oct 2026 09:20 … approved 3 Oct 2026 11:15; external approval dated 30 Sep 2026 |
| Year 2 Needs | 24 Nov 2026, 09:00–14:00; decisions 24–25 Nov 2026 |
| Year 2 departmental plans | certified 25 Nov 2026 10:30 and 11:00; accepted 27 Nov 2026 14:00 and 14:05 |
| Year 2 Annual Plan | confirmed 4 Dec, signed 7 Dec, adopted 8 Dec, approved 9 Dec; publication confirmed by the Planner and Active 10 Dec 2026 15:00 (Treasury submission date 10 Dec 2026; website publication date 10 Dec 2026) |
**Publication fixture values (v0.4, new content for review).** Each plan's confirmation is recorded by **Mercy Kilonzo** (Procurement Planner) with the Treasury reference already named in §A4 and §A5 (Year 1 `MOH/APP/2026/001`; Year 2 `MOH/APP/2027/001`), the synthetic evidence file `Treasury-dispatch-evidence-example.pdf` (labelled illustrative) and a labelled illustrative public plan URL: Year 1 `https://www.moh.example.test/procurement/annual-procurement-plan-2026-27`; Year 2 `https://www.moh.example.test/procurement/annual-procurement-plan-2027-28`. The two dates are those in the rows above and the recorded instant is the plan's activation instant.


### A3.1 Offsets as built (v0.9)

A fixture instant written anywhere in this document is the story's (18 June 2027 10:00 EAT is its "now"). The seed moves it into the world by one of these functions of `kentender_core.seeds.calendar`; in a v0.7 world each is the identity.

| Kind of instant | Function | Rule | At the anchor of 9 October 2026 |
|---|---|---|---|
| Before 1 January 2025 | `W` | Unchanged (the Strategy baseline, expired terms) | Unchanged |
| 1 January to 31 December 2025 (Year 1's planning history, the 2025 responsibility terms) | `W` | Moved by whole weeks with the years | 0 days |
| 1 January to 31 December 2026 (Year 2's journey: budget, Needs, departmental plans, Annual Plan) | `W`, `Year.at` | Moved with the years, then pulled whole weeks earlier so that its Needs have happened by the anchor | 49 days earlier (Needs on 6 to 7 October) |
| 1 January 2027 to 18 June 2027 10:00 (the executed year) | `W` | Moved by E, whole weeks, so that 18 June 2027 10:00 is the anchor | E = 252 days earlier (36 weeks) |
| After 18 June 2027 10:00 (a live deadline: the tablets Tender's close, a clarification deadline) | `W` | As the executed year, and 7 days later, so a deadline survives the days between the anchor and the run | E + 7 days |
| A delivery date of the executed year | `calendar.delivery` | `W`, held to the year's last day | 22 October for 24 June 2027; 28 October for 30 June 2027 |
| A fiscal-calendar date (a year's end, a Required by, a rule's start) | `F` | Moved by whole years | 0 years |
| An intake window's close | `Year.window` | The year's base shift, never pulled | 25 November 2026 for Year 2 |
| The closed year's execution (Year 0) | `W0(value, slot)` | `W` and 364 days (52 weeks) earlier; the Tender in slot 1 and 2 later by `closed_year_offset_days` | Slots 0, 1, 2: 0, 18 and 36 weeks later |
| A block of events that runs past the story's "now" (browser-test worlds, demonstration profiles) | `calendar.block(last)` | E, and the block's own whole weeks earlier so that its last instant is not later than the anchor; no live-deadline week | Award's browser worlds (last instant 11 October 2027): E and 17 weeks earlier |
| A story told in calendar months and quarters (Contract Management's demonstration profiles, browser world and tests) | `calendar.years_block(last)`, `kentender_contracts.simulation.timeline.D` | Whole years back, the fewest that put the story's last instant (28 July 2028 11:00) at or before the anchor; a calendar date keeps its day and month | 2 years at this anchor: 2 July 2027 becomes 2 July 2025, 28 July 2028 becomes 28 July 2026 |

The seed also holds a step of a profile that sits after the prepared year's Needs in the story to the anchor (`calendar.not_after_anchor`). The browser specs mirror these rules in `tests/ui/helpers/anchor.ts` from the numbers `calendar.describe()` returns.

**Year 0's three Tenders are spread over the year** (`calendar.closed_year_offset_days`). Slot 0 is where the executed year's story, one year earlier, puts the chain (at 9 October 2026: requisitions from 24 June 2025, awards accepted on 30 September 2025); slots 1 and 2 are later by a whole number of weeks, the last so that its chain ends at least 14 days before the year's end. The Analytics monthly series read on 16 October 2026 show activity in 10 of the twelve months before the anchor; February and May 2026 hold none (the chains' steps are weeks apart and the series count only submissions, authorisations, publications and decisions). A run late in the year, when the year has no room, spreads nothing.

## A4. Year 1 — FY 2026/27, carried out

### A4.1 Budget

`MOH-FIN-BUD-2026-01 (Demo)`, KES 290,000,000, approval document `MOH Approved Procurement Budget 2026-27 (Demo).pdf`, registered by Josphat Mwangi and approved by Beatrice Kamau.

| Line (generated reference) | Available to | Approved |
|---|---|---|
| Digital health infrastructure programme | Digital Health | KES 120,000,000 |
| Digital health workforce development | All departments | KES 60,000,000 |
| Ministry-wide ICT infrastructure | All departments | KES 80,000,000 |
| Office equipment for Human Resources Management and Development | HRMD | KES 30,000,000 |

### A4.2 Needs

| Reference | Title | Department | Quantity | Required by | State |
|---|---|---|---|---|---|
| NDS-MOH-2026-0001 | National digital health infrastructure upgrade | Digital Health | 1 Programme | 30 Jun 2027 | Accepted by Julia Njeri |
| NDS-MOH-2026-0002 | Clinical training laptops for digital health rollout | HRMD | 200 → 100 Each (Revision 1 returned by Dr Peter Kimani, Revision 2 accepted) | 30 Jun 2027 | Accepted |
| NDS-MOH-2026-0003 | Clinical deployment laptops for digital health rollout | Digital Health | 150 Each | 30 Jun 2027 | Accepted by Julia Njeri |

### A4.3 Departmental plans and the Annual Plan

The Digital Health plan funds Needs 0001 and 0003 and carries the Digital Health portfolio requirements; the HRMD plan funds Need 0002 and carries HRMD's. The **Annual Procurement Plan 2026/27** (`PLN-MOH-2026-001`, Treasury reference `MOH/APP/2026/001`) has 14 items, KES 236,500,000:

| Plan Item | Department(s) | Budget line | KES | Designation | Approved invitation | Delivery |
|---|---|---|---|---|---|---|
| Clinical training and deployment laptops for digital health rollout | HRMD 100 + Digital Health 150 Each | Workforce | 50,000,000 | Youth | 1 Feb 2027 | 60 days |
| National digital health infrastructure upgrade | Digital Health | Digital Health | 80,000,000 | None | 1 Mar 2027 | 30 days |
| Printers | Digital Health | Digital Health | 5,000,000 | None | 15 Feb 2027 | 30 days |
| Laboratory desktop computers | Digital Health | ICT | 9,000,000 | None | 22 Feb 2027 | 30 days |
| Medical-grade tablets | Digital Health | Digital Health | 6,000,000 | None | 15 Mar 2027 | 21 days |
| Field laptops | Digital Health | Digital Health | 7,000,000 | None | 1 Mar 2027 | 30 days |
| Core network routers | Digital Health | ICT | 25,000,000 | Women | 1 Feb 2027 | 60 days |
| Clinic desktop computers | Digital Health | Digital Health | 12,000,000 | None | 15 Mar 2027 | 21 days |
| Document scanners | HRMD | HRMD | 3,500,000 | None | 1 Mar 2027 | 21 days |
| Network switches | HRMD | ICT | 9,000,000 | None | 8 Feb 2027 | 45 days |
| UPS units | HRMD | ICT | 4,000,000 | None | 8 Mar 2027 | 21 days |
| Desktop computers | HRMD | HRMD | 12,000,000 | None | 22 Feb 2027 | 30 days |
| Monitors | HRMD | HRMD | 7,500,000 | None | 1 Mar 2027 | 21 days |
| Wireless access points | Digital Health 4,000,000 + HRMD 2,500,000 | ICT | 6,500,000 | None | 15 Feb 2027 | 30 days |

The 30% planning reservation (of what the plan procures, CFG-CHG-002 v0.13 §4.7) needs KES 70,950,000; the laptops (Youth, 50m) and the routers (Women, 25m) give 75m. Every line stays within its budget (Digital Health 110m of 120m, ICT 53.5m of 80m, HRMD 23m of 30m, workforce 50m of 60m).

### A4.4 What is carried out, and where each record stands at the as-at instant

Every record below is built through the owning module's real commands by the named people. Afya Digital Supplies Limited and Jirani Office Supplies Limited bid on T2–T5 (each bid started, filled, its physical security original recorded by Mercy Kilonzo, the intake officer Charles Mutiso assigns for each Tender (v0.4 read: “recorded by Charles Mutiso”; v0.5 matches it to its bid only after the opening starts), priced and signed); all four suppliers bid on T1.

| Ref | Requisition (state) | Tender | State at 18 Jun 2027, 10:00 | Next step and holder |
|---|---|---|---|---|
| T1 | Laptops — Authorised 15 Mar 2027 | Supply and delivery of business laptops (published 15 May; deadline 12 Jun 11:00) | Four bids; opening complete 12 Jun; report delivered 16 Jun 14:07; opinion signed 17 Jun 09:10; Award for Afya (KES 46,400,000) 17 Jun 10:00; Mary Wanjiku accepted 18 Jun 09:00 | The waiting period runs (delivery to Contracting 2 Jul is the AWD-DEMO-DELIVERED profile) |
| T2 | Printers — Authorised 12 Mar | Supply of printers (9 Apr – 10 May 12:00) | Two bids; opening complete 10 May; report delivered 16 Jun 11:30; Award case received | Prepare professional opinion — Charles Mutiso |
| T3 | Laboratory desktop computers — Authorised 11 Mar | Supply of laboratory desktop computers (6 Apr – 7 May 12:00) | Two bids; report delivered 4 Jun 15:00; opinion signed 17 Jun 16:00 | Decide award — Amina Hassan |
| T4 | Document scanners — Authorised 15 Mar | Supply of document scanners (16 Apr – 3 Jun 10:00) | Two bids; opening complete 3 Jun; committee appointed, members declared, opening taken up | Committee review — Grace Wambui's committee |
| T5 | Network switches — Authorised 15 Mar (25 of 30, KES 7,500,000) | Supply of network switches (14 May – 14 Jun 11:00) | Two bids; opening complete 14 Jun; evaluation prepared | Appoint the evaluation committee — Amina Hassan |
| T6 | Medical-grade tablets — Authorised 20 Apr | Supply of medical-grade tablets (24 May – **25 Jun 2027 11:00**) | Open for bids; four candidate Draft bids; six supplier clarifications received 2–17 Jun, unanswered; opening committee appointed 15 Jun | Answer the clarifications — Brian Wafula; Start opening on 25 Jun — Charles Mutiso |
| T7 | UPS units — Authorised 10 May | Supply of UPS units | Submitted 8 Jun; approved by Charles Mutiso 16 Jun 15:30 | Authorise publication — Amina Hassan |
| T8 | Wireless access points (both departments) — Authorised 15 Mar | Supply of wireless access points | Submitted 14 Jun; returned 16 Jun 09:00: "State the warranty period required from suppliers." | Correct and resubmit — Brian Wafula |
| T9 | Field laptops — Authorised 12 Apr | Supply of field laptops (10 May – 21 Jun) | Brian Wafula drafts an addendum adding 20 laptops on 16 Jun 11:00 — a quantity change no addendum may issue — and asks Amina Hassan to consider cancellation at 14:00 (TPR-CHG-001 v0.17 §5.11; earlier draft of this row read: "Cancellation recommended by Charles Mutiso 16 Jun 14:00", which gives no work item) | Consider cancellation — Amina Hassan; Brian waits |
| T10 | Desktop computers — Authorised 22 Mar | Supply of desktop computers (26 Apr – 28 Jun) | Recommended 14 Jun; cancelled by Amina Hassan 15 Jun 12:00 | Record the cancellation compliance evidence (notices, PPRA report, candidate notice; due within 14 days) — Brian Wafula |
| T11 | Core network routers — Authorised 15 Mar | Supply of core network routers (12 Apr – 30 Jun) | Recommended 14 Jun; cancelled 16 Jun 12:00; all six obligations evidenced 16 Jun 14:00–15:30 | None |
| — | Clinic desktop computers — **Submitted to Procurement** 16 Jun 11:00 | — | Awaiting authorisation | Authorise requisition — Charles Mutiso |
| — | Monitors — **Authorised** 10 Jun 11:00 | — | Not yet taken up by a Tender | Start a Tender — Brian Wafula |

Every authorised Requisition reserves its drawdown against the FY 2026/27 budget (14 reservations, KES 143,000,000, each stamped `KENTENDER_MVP_1_R1_REQ`). The laptops' latest delivery date is the plan boundary, 30 Jun 2027, and the four bids offer 22–30 Jun 2027: a Requisition refuses a later date and a Tender's bid form refuses a later offer (plan BF-04).

The laptops' opening, evaluation and award keep their own story: opening committee Charles Mutiso (chair and recorder), Brian Wafula and Beatrice Kamau (independent member); David Ouma's request to repeat the total answered; Pwani Tech Distributors Limited fails the 16 GB memory requirement automatically and Mlima Computer Solutions Limited's expired tax compliance certificate fails eligibility in the committee's evidence review; Afya is recommended at KES 46,400,000 and Jirani ranked second. The portfolio's evaluations use the same committee (Grace Wambui chair, Peter Mugo, Ruth Achieng; Charles Mutiso recorded as secretary by office on each appointment and Brian Wafula appointed secretary by Charles's written delegation at the earlier assignment instant (v0.3; v0.2 read: “Brian Wafula secretary”)), find every bid responsive and recommend Afya. (v0.2: each member's department on the appointment is the home unit §A2 records, and each appointment reference is generated by the Evaluation commands from the Tender's own reference; the seed passes neither a department nor a reference, and nothing validates a reference by its exact text.)

## A5. Year 2 — FY 2027/28, being prepared

| | |
|---|---|
| Budget | `MOH-FIN-BUD-2027-01 (Demo)`, KES 160,000,000: Digital health infrastructure programme (Digital Health, 100m) and Digital health workforce development (all departments, 60m). |
| Needs | NDS-MOH-2027-0001 Health information exchange platform upgrade (Digital Health, 1 Programme, by 31 Aug 2027, accepted by Dr Peter Kimani); **NDS-MOH-2027-0002 Digital health workforce certification programme (HRMD, 1 Programme, Submitted 24 Nov 2026 — Dr Peter Kimani's review is open)**; NDS-MOH-2027-0003 Training centre audio-visual equipment (HRMD, 20 → 12 Each, returned then accepted); NDS-MOH-2027-0004 Clinical decision-support software licences (Digital Health, 150 Each, accepted). |
| Departmental plans | Digital Health (Needs 0001 and 0004) and HRMD (Need 0003), certified by Dr Peter Kimani, accepted by Mercy Kilonzo. |
| Annual Plan | `PLN-MOH-2027-001`, Treasury reference `MOH/APP/2027/001`, Active from 10 Dec 2026: Health information exchange platform upgrade (Digital Health line, 70m, invitation 3 May 2027, 30 days), Training centre audio-visual equipment (workforce line, 12m, Women, 2 Aug 2027, 45 days), Clinical decision-support software licences (workforce line, 20m, Youth, 15 Jul 2027, 60 days). KES 102m; the reservation needs 30.6m and has 32m. |
| Not there | No Requisition, Tender or reservation on FY 2027/28, ever. |

(v0.8) **How far the prepared year goes.** The prepared year goes as far as the anchor allows (R5). At 15 October 2026 that is Departmental Needs (Project Owner, 15 October 2026: "2. Departmental needs"; "1. Correct", answering the reading that Year 2 stops at the needs stage, before departmental plans): its budget is registered and its Needs are collected, and its Needs window reads Open (KT-STD-001 v1.29 §8.4 states: "Open, closing 25 Nov 2026, 23:59 EAT"; the instant is an offset, **Awaiting fixture**). Its departmental plans and Annual Plan are built only when the anchor is late enough that their dated work does not fall after it.

## A6. Identities and rules the world keeps

- **One site, one Procuring Entity.** `PE-MOH` is a fixture reference, not a selector or a per-record field. Nothing creates a second entity.
- **Generated references** (owner, 26 Sep 2026 and 1 Oct 2026: "Keep generated codes"). References are the ones the system generates, so a document's `TND-MOH-2027-033` is an example of the form; the seed finds records by content (a budget by its approval reference, a line by its title, an item by its title). Appendix B lists them on the test site. (v0.2: the Evaluation appointment references are generated too, so the reference strings pictured in EVL-CHG-001 are illustrative and the seed asserts content, not those strings.)
- **The same commands as the screens, as the named people**, never Administrator for a business decision, each at its fixture instant. No direct write to a governed record, except the namespace stamps that let `reset` recognise canonical rows.
- **Exact money and quantities.** Amounts cross module boundaries as exact decimals; quantities are whole Each where the unit is Each.
- **Lineage.** Each Plan Item's sources are the exact accepted Need revisions or direct departmental requirements; each Requisition draws on one Plan Item; each Tender consumes one authorised hand-off; each bid, opening, evaluation and award belongs to its Tender. Inclusion in the plan, authorised coverage, publication and award are separate facts.
- **Idempotent and deterministic.** A second run with the same controls creates nothing and changes nothing.
- **Fixture rules are fixture rules.** Procurement Rules are stamped `Fixture-verified — not production law`; no legal proposition is certified by the seed.
- **Never ahead (v0.8).** No seeded instant, pinned test clock or demonstration profile's moment is later than the real clock (R1).

## A7. Year 0 — FY 2025/26, closed (v0.8)

Project Owner, 15 October 2026: "3. Yes, seed a closed FY" and, on its depth, "2. Agreed", of the recommendation: its configuration, its closed Budget and plan, and a small completed portfolio of three to four Tenders through to award, sized after Phase 1 measures what Analytics' months need.

| | Value |
|---|---|
| Purpose | Analytics' trailing twelve months (the window reaches back before Year 1 began), and an ERPNext Fiscal Year (2025-2026) in which native documents dated within it can post. |
| How it is built | By the machinery of Year 1, one year earlier, through the owners' commands as the named people at fixture instants (R6). |
| Its records | **Awaiting fixture**: the plan items, requisitions and Tenders, their amounts and instants are set in Phase 4 of `Real_Date_Anchor_Implementation_Plan.md`. |
| State at the anchor | Closed: its Budget is closed after the year's end; nothing in it is open. |

**v0.9: what Year 0 holds, as built.** Every record is built through the owning module's real commands as the named people, at fixture instants (R6).

| | Value |
|---|---|
| Budget | `MOH-FIN-BUD-2025-01 (Demo)`, KES 100,000,000, approval document `MOH Approved Procurement Budget 2025-26 (Demo).pdf`: Ministry-wide ICT infrastructure (all departments, KES 60,000,000) and Office equipment for Human Resources Management and Development (HRMD, KES 40,000,000). Registered by Josphat Mwangi, approved by Beatrice Kamau. |
| Need | NDS-MOH-2025-0001 Staff workstation replacement (HRMD, 120 Each, KES 24,000,000, by 30 June 2026), accepted by Dr Peter Kimani. |
| Departmental plan | HRMD only, certified by Dr Peter Kimani, accepted by Mercy Kilonzo. Its direct requirements: Multifunction office printers (30 Each, KES 6,000,000, HRMD line) and Replacement staff laptops (60 Each, KES 12,000,000, ICT line). |
| Annual Plan | Treasury reference `MOH/APP/2025/001`, Active from December 2024: Staff workstation computers (KES 24,000,000, HRMD line, Youth, 30 days), Multifunction office printers (KES 6,000,000, none, 21 days) and Replacement staff laptops (KES 12,000,000, Women, 30 days). KES 42,000,000; the 30% reservation needs KES 12,600,000 and has KES 36,000,000. |
| Tenders Y0-1, Y0-2, Y0-3 | One per Plan Item, each with two bids (Afya Digital Supplies Limited the lowest, Jirani Office Supplies Limited second: KES 165,000 and 170,000 for the workstations, 165,000 and 172,000 for the printers and the laptops, per Each), the committee's report, the professional opinion, Amina Hassan's award, and Mary Wanjiku's acceptance. Security KES 480,000, 120,000 and 240,000. (The second Tender is for printers, not display monitors: the installed IT-equipment template has no comparison rule for a monitor's display resolution, so a committee cannot find a monitor bid responsive; only Desktop computer, Printer and Laptop reach a finished evaluation.) |
| Where the awards stop | At the supplier's acceptance, in the stage **Waiting to proceed**. No package reaches Contracting, so Contract Management holds no Year 0 case. |
| Its supplier accounts | The four accounts register on 23 to 26 June 2025 (the executed year's registrations one year earlier), before Year 0's bids; the signing certificate is valid from before them. |

**v0.9: two things Year 0 does not do.** (1) **Its Budget is not closed.** The Budget closes only when no reservation remains held (`BUDGET_INVALID_STATE`: "This budget cannot be closed yet. … remains reserved for requisitions."), and the three authorised Requisitions hold theirs. (v0.8 read: "its Budget is closed after the year's end".) (2) **Its three awards are not delivered.** Award's own sweep, which the scheduler runs on a site that has it on (the scheduler is off on the development and test sites), would open "Tender validity has expired. No award can proceed." on each, because a Tender's validity (120 days) has long ended; whether a validity that ended after the supplier accepted should open an issue is a question for Award's owner, not for the seed (change report, follow-up).

## A8. Contract Management's demonstrations (v0.8)

Contract Management is not part of the canonical world. Its nine demonstration profiles (`RECEIVED`, `SIGNING`, `ACTIVE`, `ACCEPTED`, `PAID`, `CHANGE`, `WARRANTY`, `TERMINATION`, `CLOSED`, `kentender_contracts/seeds/demo.py`) are isolated, one contract at a time. Decision RA-4: the calendar dates of CM-CHG-001 v0.8 §10.1B are illustrative and its durations are authoritative (recommended 15 October 2026; Project Owner, 15 October 2026: "3. Accepted"). The authoritative durations include "12-month warranty from each unit’s acceptance event" (CM-CHG-001 v0.8 §10.1B).

- The demonstrations use a synthetic source package (CM-CHG-001 v0.8 implementation plan D17: "use a separate synthetic source package (`CM-DEMO-AWD-01`, `CM-DEMO-TERMS-01`) and **never overwrite the canonical chain**"), so they need no Year 0 award chain.
- They move back as one block so that the last instant, `CLOSED`, is not later than the anchor. The block spans 392 days (2 July 2027 to 28 July 2028); at 15 October 2026 it moves back at least 651 days (arithmetic only, new content).
- Their history runs under the frozen seed clock (R6), so native ERPNext documents take the fixture date, and no instant is later than the anchor (R1). This closes the decision FU-CM-61 asks for; the follow-up itself is closed by the Contract Management owner.
- The warranty stays 12 months. A 6-month warranty is the fallback only if the block cannot move (Project Owner, 15 October 2026: "2. Yes", answering whether a 6-month warranty on the closed-year contract is acceptable).
- A canonical `contracts` stage after `award` (CM-CHG-001 v0.8 implementation plan D17; follow-up FU-CM-12) is not built. If it is built it is subject to R1 like every stage: Award's delivery to Contracting, which v0.7 places on 2 July 2027 (the `AWD-DEMO-DELIVERED` profile, §B6), would then fall before the anchor.
- The block's offsets are **Awaiting fixture**; the work waits for the Contract Management session to release its seed and tests (Phase 6 of `Real_Date_Anchor_Implementation_Plan.md`).
- (v0.9) **As built.** The block moves by **whole years**, not whole weeks (v0.8 read: "moves back at least 651 days"): Contract Management reports by calendar month and quarter (`CM-R-14`, `CM-R-15`), and a move that is not a whole number of years leaves a month starting on a day that is not its first, which the report refuses. `calendar.years_block` (the fewest whole years that put the last instant at or before the anchor) is `kentender_contracts.simulation.timeline.D`; at an anchor of 9 October 2026 it is 2 years, so the story runs from 2 July 2025 to 28 July 2026 (within FY 2025/26 and the first weeks of FY 2026/27). Weekdays are not kept, and nothing in Contract Management depends on them; a duration across a 29 February differs by a day. Native ERPNext documents take the trusted clock's date: the adapter (`native/adapter.py`) dates a purchase order, receipt, invoice and payment entry by `services/clock.now()` (the site clock in production), and a demonstration profile runs each step under the frozen seed clock; this is FU-CM-61's first option, built here and closed by the Contract Management owner. The profile loaders still refuse a moment later than the real clock.

---

# Part B — How to seed it

## B1. The command

Run from the repository root (`apps/kentender_v1/`), where the `Makefile` is:

```bash
make seed-canonical SITE=<site>                                       # the full world: CURRENT=award, NEXT as far as the anchor allows (v0.7 read: NEXT=annual_plan)
make seed-canonical SITE=<site> CURRENT=requisitions NEXT=budget      # requisitions in progress; next year's budget only
make seed-canonical SITE=<site> CURRENT=annual_plan NEXT=needs        # nothing bought yet; next year's Needs in
make seed-canonical SITE=<site> REBUILD=True                          # drop and rebuild the canonical module rows
make seed-canonical SITE=<site> WIPE=True FORCE=True RESEED=True      # from nothing: the site stage too
make seed-canonical SITE=<site> WIPE=True FORCE=True                  # wipe only: an empty, unconfigured site
make seed-canonical SITE=<site> ANCHOR=story                          # (v0.9) the v0.7 world, read as at 18 Jun 2027; clears a stored anchor
make seed-canonical-dry-run SITE=<site>                               # what the clear would remove; deletes nothing
make seed-canonical-validate SITE=<site> [CURRENT=…] [NEXT=…]         # validate only; no writes
```

| Control | Year | Stages, in order | Meaning |
|---|---|---|---|
| `CURRENT` | FY 2026/27 | `annual_plan`, `requisitions`, `tenders`, `bid_submission`, `bid_opening`, `bid_evaluation`, `award` | `annual_plan` is the always-built base (budget, Needs, departmental plans, the Active plan). Each later stage takes every executed record as far as that stage (§A4.4); a record whose story stops earlier stops there. |
| `NEXT` | FY 2027/28 | `none`, `budget`, `needs`, `departmental_plans`, `annual_plan` | How far the prepared year goes; `annual_plan` is the ceiling. |

The site, its people and the Strategy are shared and always built. Both controls default to the full world (v0.8: the default `NEXT` is the furthest stage the anchor allows, R5, and an explicit cap beyond the anchor is refused with a message). A lower stage stops each record where it leaves it, even where its dates say it would have moved on (decision D5): at `CURRENT=tenders`, the Tenders whose deadlines are before the as-at instant are closed with no bids.

**Moving a control.** A run that asks for more than the site holds builds on what is there (a prepared year taken from its departmental plans to its Annual Plan carries on from the accepted plans). A run that asks for less — or finds a Tender told without the bids it now asks for, or a world half-built by a failed run — prints `NOTICE: the canonical world is not in the shape this run builds on …` and rebuilds the canonical module records by itself, once.

**The anchor (v0.9).** `make seed-canonical` first runs `kentender_core.seeds.calendar.prepare` in a process of its own. `ANCHOR=real` (the default once the cut-over is made; until then `ANCHOR=story`) keeps a stored anchor on a plain rerun and takes a new one on `REBUILD=True` or `WIPE=True`; `ANCHOR=story` clears it. A site that holds a world refuses to change between the two without `REBUILD=True` (or `WIPE=True`), because the dates and the years kept differ. When the financial year moves on, the dated responsibilities take their new terms only when the site stage is rebuilt (`REBUILD=True WIPE=True FORCE=True RESEED=True`); `prepare` says so.

**`THROUGH` (retired).** The single-year ladder (`site … planning … award`) maps for one release: up to `planning` it moves only the prepared year (`THROUGH=budget` is `CURRENT=annual_plan NEXT=budget`); a later stage moves the executed year with the prepared year complete (`THROUGH=tenders` is `CURRENT=tenders NEXT=annual_plan`). It prints a notice. **`OPEN=True` is retired:** the executed portfolio's Medical-grade tablets Tender is open past the as-at instant, so the public Tenders page always lists a Tender.

Underneath, `make` calls `bench execute`:

```bash
cd /home/midasuser/frappe-bench
bench --site <site> execute kentender_core.seeds.canonical.run --kwargs '{"current": "award", "next_year": "annual_plan", "reset": True, "validate": True}'
bench --site <site> execute kentender_core.seeds.canonical.validate --kwargs '{"current": "award", "next_year": "annual_plan"}'
```

`--kwargs` is a Python literal: `True`/`False`/`None`, never `true`/`false`. Success prints `CANONICAL_SEED_OK current=<stage> next=<stage> removed={…}`. Any failure raises, and the run — clear and reseed — is rolled back as one transaction, with one exception: submitting a bid commits at once, so a run that fails after the bids leaves a half-built Tender, which the next run rebuilds by itself.

## B2. Prerequisites

- The site's apps are migrated (`bench --site <site> migrate`).
- `developer_mode` or `allow_canonical_seed` in `site_config.json`, or `FORCE=True`. One of them is enough for every stage.
- The site is configured as `PE-MOH`, or not configured. A different Procuring Entity fails the run rather than being repaired.
- The stages from `bid_submission` on use the simulated signing, tender-box, attestation, notice-delivery and Contracting services, which answer only on a test site; a run that reaches them switches site_config `kt_bds_simulation_environment` on itself, with a notice. Never on a site that takes real bids.
- Run as `Administrator` (the `bench execute` default).
- **The clock policy (v0.8).** Each site sets `kt_test_clock_policy` in its own site configuration: no key (`free`, until the cut-over), `never_ahead` or `off` (§A1.1, R7). The development site is `off` and a test site `never_ahead` (Project Owner, 15 October 2026: "1. Yes", answering that the development site runs on the real clock with no pin and only the test site pins, to the seed day). The development site was set on 15 October 2026 (`bench --site <site> set-config kt_test_clock_policy off`). Read a site's clock with `bench --site <site> execute kentender_core.services.test_clock.describe`.
- **The rules' window (v0.9).** In an anchored world the seeded procurement rules are in force from 1 January of the first seeded year (v0.8 read: from its 1 July), because the executed chain moves earlier by whole weeks and a Plan Item's planned invitation date can fall up to about six weeks before the financial year it belongs to; the method and schedule rules resolve by that date.
- **Clock policy during the cut-over (v0.9).** The test site's policy stays `free` until Contract Management's tests and demonstrations are re-timed (Phase 6), so that their tests, which set instants of 2027, keep working; the development site is `off`.

**A new server, once:** the Python packages (`bench setup requirements --python`, or `./env/bin/pip install "freezegun~=1.5.5"` — every command runs at its fixture instant under freezegun); wkhtmltopdf **0.12.6.1 (with patched qt)** exactly, for the IT-equipment Tender template; a migrate after every pull (it also re-registers a KenTender module a migrate put under Frappe). The browser-test tooling is not needed: without it the target drains the background queue with a plain bench worker. The seed installs the tender template itself and stops at once, with the reason, if the template cannot be used.

**A site reachable from the internet:** every seeded person shares the fixture password and the simulated services are on. Use such a site for demonstrations only; restrict who can reach it or disable the fixture accounts afterwards.

## B3. What the clear removes, and what it never touches

Selection is by identity, namespace or fixture e-mail domain — never "everything in a table". The dry run shows the exact list first.

**Removed by every run (`reset`):**

| Area | Rule |
|---|---|
| Budget | Every budget other than the two canonical ones (found by their approval references); on them, any version that is not Active and any reservation or commitment not stamped `KENTENDER_MVP_1_R1_REQ`. (v0.9: in an anchored world there are three canonical budgets, one for each of Year 0, Year 1 and Year 2, found by their approval references.) |
| Departmental Needs | Every Need outside `KENTENDER_MVP_1_R1_NDS`, with its revisions, decisions, review tasks, events and projections. |
| Strategy | Every plan outside `str-chg-001-mvp1`, and every version of the canonical plan other than Version 1. |
| Planning | Annual and departmental plans outside `KENTENDER_MVP_1_R1_PLN`. Accepting a Need starts its department's Draft plan unstamped; the planning build stamps the plans it uses. |
| Requisitions | Every Requisition not on a Plan Item of the executed year's canonical plan (the laptops and the portfolio). |
| Tenders | Every Tender not on a canonical Requisition, with its family rows, journal entries and files; the bid, opening, evaluation and award rows hanging off a removed Tender go with it (`kt_tender_removal_consumers`). |
| Loaded demo profiles | Undone first, through each module's own release (§B6); the test clock is cleared, and the run sets it again to the as-at instant at its end. |
| Leftovers | Child rows and files whose record is gone, and Planning's disposition, intake and usage projections whose Need is gone. |
| Regulatory Reference | Versions outside `KT_STD_001_S8`. |
| Legacy demo journeys | Every `Procurement Handoff Card` and `Procurement Journey`. |
| Responsibility assignments | Rows outside the canonical namespaces, or held by a fixture-domain user outside the register, and `KT_STD_001_S8` grants `site_setup.ASSIGNMENTS` no longer declares; the people who stay have their Frappe roles re-synced. |
| Users | Accounts on a fixture e-mail domain (`@moh.example.test`, `@example.test`, `@test.local`, `@moh.test`, `@moe.test`, `@example.com/.org/.net`) not in the register, with their Contact and permission rows. |
| Organisation Units, Fiscal Years | Units no canonical row points at (a home unit that points at one is cleared first); KenTender-created years other than the three the anchor derives (v0.8 read: 2026-2027 and 2027-2028) that nothing references. |

**Also removed by `REBUILD`:** every canonical module row, downstream first — the canonical Tenders' award, evaluation, opening and bid rows; the Tenders; every canonical Requisition (an unconsumed authorisation revoked through the real command first); both years' Planning rows (each Need's usage projection reversed); both years' Needs; both budgets; the Strategy; and the canonical supplier accounts (`KENTENDER_MVP_1_R1_BDS`), so they register again at their own instants.

**Also removed by `WIPE`:** the site stage — the Procuring Entity, units, years, Regulatory Reference, rule profiles and the register's own actors — and every row in Requisitions, Planning and Tenders; then, unless `RESEED=True`, nothing is rebuilt.

**Never touched:** a real person's account (any non-fixture domain); ERPNext-owned records (Company, UOM, ERPNext Budget and Cost Center), except that `wipe` purges `_Test Fiscal Year …` rows; the legacy reference doctypes the AUTH-ADR-001 removal phase owns (`Procuring Entity`, `Financial Year`, `PE Fiscal Year Context`, `Procuring Department`, `PE Type`); Frappe metadata.

## B4. Options

| Switch | Default | Effect |
|---|---|---|
| `current` / `CURRENT` | `award` | How far the executed year goes (§B1). |
| `next_year` / `NEXT` | as far as the anchor allows (v0.7 read: `annual_plan`) | How far the prepared year goes (§B1). A value later than the anchor allows is refused with a message. |
| `through` / `THROUGH` | — | Retired; mapped for one release (§B1). |
| `ANCHOR` (v0.9) | `real` after the cut-over | `real` stores the anchor first; `story` is the v0.7 world (§B1). |
| `anchor`, `fresh` of `calendar.prepare` (v0.9) | `True`, `False` | The Make target passes `fresh` when `REBUILD` or `WIPE` is `True`. |
| `reset` | `True` | Run the §B3 clear first. |
| `rebuild` / `REBUILD` | `False` | Also drop the canonical module rows (§B3) and rebuild. |
| `wipe` / `WIPE` | `False` | Also drop the site stage. Implies `rebuild`. |
| `reseed` / `RESEED` | `not wipe` | Reseed after the clear; `WIPE=True` alone leaves an empty site. |
| `validate` | `True` | Validate after seeding; a failure rolls the run back. |
| `force` / `FORCE` | `False` | Bypass the developer-mode guards for this run. It does not make the site a test site. |
| `commit` | `True` | Commit at the end (tests pass `False`). |

## B5. Validation — what "canonical" means

`validate(current=…, next_year=…)` raises listing every failed check:

- **Site:** `PE-MOH`; one root and the three named units (v0.2: five, with ICT and Finance), each person of KT-STD-001 §8.3A with their home unit and Esther Muthoni with none; both years and no other; the funding sources; every register person with exactly the assignments and terms `site_setup.ASSIGNMENTS` lists; every unit-scoped role held by someone in force today (counting an ancestor's grant); no fixture-domain account outside the register.
- **Strategy:** the one plan, Version 1 Active, its hierarchy, indicator and target, its 2023 history.
- **Budgets:** exactly the year budgets `NEXT` asks for, each with its version, lines, owners, amounts, approval document and four lifecycle events at their instants; no reservation or commitment outside `KENTENDER_MVP_1_R1_REQ`.
- **Needs:** each year's Needs with their references, states, revisions, required-by dates and every decision by its actor at its instant; no FY 2027/28 Needs below `NEXT=needs`.
- **Planning:** each year's departmental certifications and acceptances; for an Active plan its signature, item count, each item's approved invitation, estimate basis and completion inside the year, activation instant, the Planner's publication confirmation (Treasury reference, Treasury and website dates, public plan URL, evidence file), and each funded Need Fully included; at `NEXT=departmental_plans`, a Draft Annual Plan; below it, no FY 2027/28 plan past Draft. At `CURRENT=annual_plan` also the plan's full read (items, value, eligibility, Finance, governance, publication).
- **The laptops' chain** at each stage reached: the Requisition and its hand-off (instants, package, two reservations, 13 Jun 2027 estimated completion, the HRMD Need's Revision 2); the Tender's lifecycle; the four bids at their instants; the four-bid opening; the evaluation's ranking and report delivery; the award to Mary Wanjiku's acceptance, nothing delivered to Contracting.
- **The portfolio:** every record of §A4.4 at its state for the stage reached (Requisition state, Tender status, bids, candidates and clarifications, opening, evaluation and award stage). (v0.9: and, in an anchored world, §A7's three Tenders, each at Award stage Waiting to proceed.)
- **The clock:** on a test site, the test clock reads the as-at instant. (v0.8: the check follows the site's policy, `test_clock.problem`: `free` keeps this rule; `never_ahead` fails a stored instant that is later than the real clock; `off` fails any stored instant. Once the anchor exists the world's age is reported, and on a test site fails at 60 days, RA-OD4.)
- **Tender-security intake (v0.5):** for each executed bid, Mercy Kilonzo holds the intake duty for its Tender, assigned by Charles Mutiso, and recorded its physical original at its instant (the laptops' on 10 Jun 2027, 10:00 EAT); Charles recorded no intake; Mercy sits on no opening or evaluation of the Tender; no duty conflict is flagged; before the opening starts no intake is matched to any bid, and once it has started the laptops' Afya original is matched to its bid.
- **Tender-security statements and status (v0.6):** each canonical Tender's published tender-security rule carries `submission_method` = Electronic and `original_delivery` = Required; once Mercy has recorded an executed bid's original, that bid's supplier reads **Original received** with the receipt reference and time before the opening starts, with no stored intake-to-bid link until the opening starts; a bid whose original is not recorded reads **Original receipt not yet recorded**; no supplier surface reads “Not yet matched”.
- **Tender-security statements (v0.7):** the canonical Tender’s published tender-security rule carries `submission_method` = Bidder uploads an electronic instrument and `original_delivery` = Required, and the world is compiled under template release 1.5; the validation is otherwise unchanged.

(v0.9) In an anchored world `validate` also reports and checks the anchor: the world's age counted from the run that built it and, apart, the anchor's age; an anchor later than the real clock; and, on a `never_ahead` test site, a world built more than 60 days ago. It also fails any recorded event dated after the anchor (the audit events of Budget, the Needs decisions, the departmental plan submissions and decisions, the plan signatures and activations, the bid receipts and the evaluation report deliveries; `canonical.EVENT_FIELDS`).

`kentender_core.tests.test_canonical_seed` covers the selection rules, the two ladders and the `THROUGH` alias, the calendar, an idempotent full run, the executed and prepared years, the two controls moving independently (a lower stage rebuilds; a higher one builds on), the validator failing closed on a stray budget, the public Tenders list, and the automatic rebuild of a half-built Tender.

## B6. Demo profiles

Profiles are named, mutually exclusive states of the canonical laptops story, built through the same commands, for walking a screen as the person named. They are not part of the canonical world. Every profile still works on the laptops chain, now on FY 2026/27 (references such as `TND-MOH-2026-002` and `PPI-MOH-2026-002` on the test site). A plain `make seed-canonical` undoes a loaded profile first and puts the test clock back on the as-at instant; each module's restore does the same.

(v0.8) Every profile's moment is not later than the anchor (R1). On a site whose policy is `off` a profile does not move the clock, so profiles are walked on a test site until they are re-timed. The moments in the table (10–12 June 2027, 17–18 June and 2 July 2027, and Contract Management's July 2027 to July 2028) are v0.7's story shape; they are re-timed in Phases 3 and 6 of `Real_Date_Anchor_Implementation_Plan.md`.

| Module | Commands | Profiles |
|---|---|---|
| Requisitions (REQ-CHG-001 v1.11 §16.4A) | `make seed-req-profiles`, `seed-req-profile PROFILE=…`, `seed-req-profile-restore` | The thirteen `REQ-SC-*` states on the laptops item (hold, multiple requests, correction resolved, closed without change, outcome ordering, shared-line short, scope lock, sequential, lead change, revoke–consume race, precision, compatibility, open slot). A load that finds the item locked, held or changed rebuilds the executed year's Planning world through this orchestrator (`clear_canonical_modules()` then `seed(current="annual_plan")`). Proof: `procurement_requisitions.tests.test_requisitions_profiles`. |
| Bid Opening (BOP-CHG-001 v0.10) | `make seed-bop-profiles`, `seed-bop-profile PROFILE=…`, `seed-bop-profile-restore` | Fifteen `BOP-DEMO-*` moments of the laptops opening, 10–12 Jun 2027, each with the test clock at its moment; the no-bids profile uses the browser-test Tender. Full walk-through: `docs/mvp-1-r1/14_bid_opening/RUNBOOKS.md` §3. Proof: `make bop-profiles-gate`, `bop-demo-walk.spec.ts`. |
| Award (AWD-CHG-001 v0.4) | `make seed-awd-profiles`, `seed-awd-profile PROFILE=…`, `seed-awd-profile-restore` | `AWD-DEMO-OPINION` (17 Jun 09:00), `-DECISION` (10:00), `-NOTICE` (10:10), `-WAIT` (18 Jun 09:05 — the canonical world's own state), `-DELIVERED` (2 Jul 09:00). Proof: `awd-demo-walk.spec.ts`. |
| Procurement meetings (OVS-CHG-001 v0.6) | `make seed-ovs-register-branch`, `seed-ovs-register-branch-restore` | Tender B: a second department's Tender whose opening was recorded Not held, on the Bid Opening browser-test world; the register lists it once and does not count it. |

While a profile is loaded, every live page reads its moment, `seed-canonical-validate` reports the profile's stage as not canonical, and the profile's own limits apply (each module's run book states them).

## B7. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `make: No rule to make target 'seed-canonical'` | Run from `apps/kentender_v1/`. |
| `Canonical seed refused: enable developer_mode…` | Set `developer_mode` or `allow_canonical_seed`, or pass `FORCE=True`. |
| `NameError: name 'true' is not defined` | `--kwargs` takes Python literals: `True`/`False`/`None`. |
| `NameError: name 'kentender_core' is not defined` from `make seed-canonical` | Nearly always the background queue is full or another error is hidden by `bench execute`: read the traceback above it. The target drains the queue before and after; if it recurs, `make ui-queue-check FIX=1` and rerun. |
| `This site is configured as PE-XXX, not PE-MOH` | The seed never overwrites another site identity. |
| Validation fails on an assignment's term ("… a changed term needs WIPE=True") | An existing grant is returned as it is, so a term the seed changes lands only where the seed retires the old row first. The four terms the two-year world moved are retired by a plain reseed (`site_setup.SUPERSEDED_BY_TWO_YEAR_WORLD`, revoked with a reason); any other changed term needs `WIPE=True FORCE=True RESEED=True`. |
| `Set up your supplier account before starting a bid` at the bid stage | A supplier account registered before 5 Oct 2026 (18 May–3 Jun 2027) cannot act for the April 2027 bids. `REBUILD=True` removes and re-registers the canonical accounts. |
| `This idempotency key was already used with a different request` | A journal entry left by an older world; `REBUILD=True` (or `WIPE`). Report it if it recurs on current code. |
| `REQ_PRODUCT_UNSUPPORTED` / `TND_PRODUCT_UNSUPPORTED` | An item is not off-the-shelf IT equipment in a category the module admits (§A1). |
| `The canonical bid evaluation signs with the test attestation service…` | The site is not a test site; the run switches it on itself from `bid_submission` (§B2). |
| Every live page shows 18 June 2027 | Expected on a test site: the world is read as at that instant. A demo profile moves it to the profile's moment; restore or reseed puts it back. |
| `The test clock cannot be set to …: it is later than the real clock` (v0.8) | The site's policy is `never_ahead`: pass an instant that is not later than the real clock, or clear it. |
| Validation: `the site clock policy is off, so no test instant may be stored` (v0.8) | Clear the stored instant: `bench --site <site> execute kentender_core.services.test_clock.set_instant --kwargs '{"instant": None}'`. `--args '[null]'` does nothing. |
| `Changing between the v0.7 world and the real-date world needs REBUILD=True` (v0.9) | The site holds a world and `ANCHOR` names the other one: rerun with `REBUILD=True` (or `WIPE=True`). |
| `NEXT=… is later than the world's anchor allows` (v0.9) | The prepared year's work for that stage would fall after the anchor; use the stage named in the message, or none. |
| Validation: `a recorded event is later than the anchor` (v0.9) | A seed step wrote an instant after the anchor; report it with the doctype and field named. |
| Validation: `the world was built N days ago` (v0.9) | A `never_ahead` test site fails a world built more than 60 days ago: `REBUILD=True`. |
| `Youth is not supported by the installed IT-equipment Tender format` | The tender template is missing or unusable — nearly always the wrong wkhtmltopdf build (§B2). |
| `No module named 'frappe.core.doctype.supplier_business_profile'` | Pull and migrate: the migrate repairs the module registration. |
| `TimestampMismatchError … BDS Test Environment Controls` | Two seed runs at once on one site; wait for the other, then rerun. |
| After `make ui-budget-gate`, validation fails on the budget lines or the reservations | The Budget browser specs work on the canonical budgets; run `REBUILD=True`. |
| `PLN_ITEM_SCOPE_LOCKED` or "already has an authorised Requisition" | An item's scope lock is permanent; `REBUILD=True` once. |

## B8. Other seed entry points

- `make seed-kentender-mvp-v1` (the multi-PE-era pack) still creates a second Procuring Entity and legacy personas; do not run it on a canonical site. `make seed-canonical` removes them again.
- Module browser gates and Python test worlds seed their own isolated fixtures (namespaced or on isolation years); they are disposable and `make seed-canonical` removes them. Tests write real rows with no rollback: run them on the test site and reseed after.
- `bench execute kentender_core.seeds.site_setup.run` is the site stage alone, without a clear.
- `make awd-seams-gate` builds a persistent Evaluation test world; reseed afterwards.

---

# Part C — How a module adds to the world

When a module builds a seeded story (decision D20, 1 Oct 2026: "The seed should exercise all stages as they are built"):

1. **Place it on a ladder.** A preparation module (budget, Needs, planning) belongs to both years: give its seed a per-year spec (`calendar.YEAR1`/`YEAR2`), Year 1 the same journey 364 days earlier unless its dates must differ, every planned date inside its own year. An execution module belongs to the executed year only: add a stage to `canonical.CURRENT_STAGES` after the stage it consumes, and never touch FY 2027/28.
2. **Use the real commands as the named people, at fixture instants** (`kentender_core.seeds.clock.at`, or the module's own trusted-clock flag). No direct governed writes; no actor created inside a module seed — add people to KT-STD-001 §8.3 and `site_setup.ACTORS`/`ASSIGNMENTS`. (v0.8: use the frozen clock, not a module-only clock flag, so native ERPNext documents take the fixture date, R6; and no instant later than the real clock, R1.)
3. **Make it idempotent and recognisable.** Stamp the module's canonical namespace and add it to `canonical.CANONICAL_NAMESPACES`; extend `collect_non_canonical()` with the disposable-row rule and `clear_canonical_modules()` with the canonical clear, downstream first (a module hanging off a Tender registers `kt_tender_removal_consumers`). If a later stage's records consume yours, make `canonical.world_ahead()` recognise them so a lower `CURRENT` rebuilds.
4. **Give the portfolio its states.** For a stage after `tenders`, decide which portfolio records reach it and where they stop at the as-at instant (`portfolio.PORTFOLIO`), so Home and Analytics see the module's work in several states at once; extend `portfolio.validate_portfolio()` and the binding table (`portfolio.binding_rows()`, Appendix B).
5. **Validate it.** Add the stage's facts to `canonical.validate()` (the module's own `validate_…_seed()`), extend `kentender_core.tests.test_canonical_seed`, run it on the test site, then run the full command on a dirtied site and compare the dry run with the removal report.
6. **Demo profiles**, if any: their release in `canonical.release_demo_profiles()`, a restore that puts the test clock back on the as-at instant, and a row in §B6.
7. **Keep this document true:** Part A's tables, §B5 and Appendix B; the `make help` line and the Makefile comment; the module docstring of `canonical.py`; the seeds README and the command card in `CLAUDE.md`.

---

# Appendix A — Carry-over register

Every rule of the two retired documents, and what it became. **Carried**: stated here, changed only as noted. **Superseded**: replaced by a decision this document records. **Dropped**: no longer applies, with the reason. Section numbers are the retired documents'.

## A.1 SEED-001 v1.4 (Harmonized End-to-End Fixture)

| SEED-001 rule | Disposition | Where / why |
|---|---|---|
| Front matter — OVS amendment: SEED-OPS v1.21 decisions D3, D4, D7, D8, D23; Julia's 2026 term expired at June 2027 instants | Carried, dates moved | §A2 (Julia's term is now Oct–Dec 2025, expired at the as-at instant); D3 §A6; D4 §A2; D7 and D8 below; D23 §A4.4 |
| One site = one Procuring Entity `PE-MOH`; KEBS examples are template-curation evidence only | Carried | §A6 |
| §1.1 source documents and §1.1 "actual approval records govern" | Dropped | Version citations of September 2026; this document cites its own basis (control table) |
| §1.2 BASE / READY — visual / READY — integrated; BASE canonical | Superseded | Owner D7 (26 Sep 2026): "Ready one is canonical". The canonical plans are Active with their reservations met (§A4.3, §A5); BASE and the visual variant remain Planning's isolated profiles and screens |
| §1.3 fixture rules labelled `Fixture-verified — not production law`, never `Verified`; production must not accept fixture configuration | Carried | §A6 |
| §1.3 executable manifest (scenario, versions, build, timezone, FY bounds, rule ids, actors, instants, results, hashes) | Carried in part | The validator and the run report record scenario (controls), instants and results; artifact hashes are not recorded — an open item for the owner |
| §1.3 "The source pack labels the period FY 2027/28 while using the dates below … an open CFG/SEED reconciliation issue" | Superseded | Resolved by the two-year world: the executed chain is FY 2026/27 and every planned date fits it (§A1, D8) |
| §2 lineage: two laptop Needs → one combined item (250 Each, KES 50m, HWD line, HRMD 20m + DHI 30m allocations) → one Requisition → one Tender | Carried, year moved | §A4.2–§A4.4 (Year 1; references generated, e.g. NDS-MOH-2026-0002/0003, PLN-MOH-2026-001) |
| §2 infrastructure Need and item in the same plan | Carried | §A4.3 |
| §2 plan inclusion, coverage, publication and fulfilment are separate facts | Carried | §A6 |
| §3.1 actors and their authority (Grace both units; Julia acting DHI; Peter HRMD and DHI from December; Mercy; Josphat both capacities; Charles; Amina; Daniel Rotich; Brian; Naomi) | Carried, dates moved | §A2 (Julia 2 Oct–1 Dec 2025, Peter DHI from 2 Dec 2025) |
| §3.2 the three accepted Needs' facts (titles, quantities, units, departments, acceptance by Julia and Peter) | Carried, dates moved | §A4.2: Required by 30 Jun 2027 (was 31 Aug / 31 Dec 2027 — Needs refuse a date outside their year); acceptances 26 Nov 2025 |
| §3.2 infrastructure acceptance instant left open | Carried as fixed | Accepted 25 Nov 2025 14:00 by Julia Njeri (the seed's instant; before the Digital Health certification) |
| §3.3 certification and acceptance chronology; DPP intake open to 30 Nov 23:59 | Carried, moved 364 days | §A3: 26 Nov 2025 10:30/11:00, accepted 28 Nov 14:00/14:05, intake to 1 Dec 2025 23:59 |
| §3.3 Julia acting from an expired page is refused | Carried | Validation of assignments and the module's own tests |
| §3.4 Strategy objective and approval-time snapshot | Carried | §A3 (Strategy baseline); the Planning approval takes the snapshot |
| §3.5 Budget `MOH-BUD-2027-001`, two lines, KES 160m | Superseded for Year 1, carried for Year 2 | §A4.1 (Year 1: 290m, four lines — the executed portfolio needs the money, plan BF-06); §A5 (Year 2: the 160m budget) |
| §3.5 30% arithmetic on the KES 160m budget | Superseded | Owner D8 (26 Sep 2026): the plan's eligible value is the denominator (§A4.3, §A5) |
| §3.5 exact decimal money and quantities | Carried | §A6 |
| §3.6 item boundaries (laptops 31 Dec 2027, REQ 30 Sep 2027, completion 24 Sep 2027) | Superseded | D8: boundary 30 Jun 2027, approved invitation 1 Feb 2027, completion 13 Jun 2027; the latest delivery is 30 Jun 2027 (a Requisition refuses a date after the boundary, plan BF-04) |
| §3.6 plan title "Annual Procurement Plan 2027/28" | Superseded | Year 1's plan is the Annual Procurement Plan 2026/27 (§A4.3); Year 2 keeps its own (§A5) |
| §3.7 governance chronology and Treasury dispatch `MOH/APP/2027/001` | Carried, moved 364 days for Year 1 (v0.4: the Treasury dispatch is recorded by the Planner's confirmation, not by the Accounting Officer) | §A3; Year 1 Treasury reference `MOH/APP/2026/001`, Year 2 keeps `MOH/APP/2027/001` |
| §3.7 synthetic Treasury evidence bytes, labelled; publication by the sandbox adapter, labelled simulation | Changed in v0.4 | Evidence bytes stay labelled (`Treasury-dispatch-evidence-example.pdf` per plan version); the sandbox adapter and its attempts are retired and the Planner's confirmation replaces them (PLN-CHG-001 v1.31 §5.5.2.2). v0.3 read: Carried |
| §4.1–§4.3 Requisition identity, drawdown lines, two reservations, scope lock, 1/8/15 March 2027 | Carried | §A4.4 (references generated: REQ-MOH-2026-002-001) |
| §5.1–§5.3 Tender identity, one consolidated schedule line, lifecycle (prepare 20 Mar, approve 20 Apr, publish 15 May) | Carried | §A4.4 |
| §5.2 baseline dates (invitation 15 May …) | Superseded | D8: the laptops' approved invitation is 1 Feb 2027; the actual publication (15 May) is 103 days later — Baseline lateness |
| §5.2 "No opening/evaluation/award actual generated by this seed" | Superseded | Owner D20 (1 Oct 2026): "The seed should exercise all stages as they are built" — the opening, evaluation and award are seeded (§A4.4) |
| §5.3 only the supported invitation event writes an actual; duplicates harmless | Carried | Planning records the Tender's invitation actual |
| §6 naming (Head of Procurement Function; PlanPublication; Submission/Version counters; no KEBS identities) | Carried | §A2, §A6 |
| §7.1 deterministic execution through the real commands, isolated worlds, failure on conflicting data | Carried | §A6, Part B |
| §7.2 coordinated owner updates | Dropped | Historical coordination list of September 2026; Appendix C names what remains |
| §7.3 completion claims (specified/approved/implemented/verified) | Carried | Control table: approval does not establish implementation or verification |
| §8 SEED-AC-001 … SEED-AC-030 | Carried in substance, renumbered | §B5 is the acceptance contract; AC-008–010 (BASE blocked) superseded by D7; AC-015/016 dates per D8 |
| §9 change register SEED13-CHG-001…023 | Dropped | History of v1.3; retained in the retired file |
| §10 dispositions | Superseded | Infrastructure acceptance fixed (above); FY bounds resolved (D8); the rest are module follow-ups |

## A.2 SEED-OPS-001 v1.25 (Canonical Site Seed Runbook; v1.24 approved)

| SEED-OPS-001 rule | Disposition | Where / why |
|---|---|---|
| Controlling decision: one canonical world; everything else disposable; one command; validates or fails | Carried | Controlling decision above |
| Approval records and source-status paragraphs v1.19–v1.25 | Dropped | History; retained in the retired files |
| §1 the command, `THROUGH` ladder, examples | Superseded | §B1 (`CURRENT`/`NEXT`; `THROUGH` mapped for one release) |
| §1 one transaction; bid submissions commit at once; a half-built Tender rebuilds itself | Carried | §B1 |
| §1.1 prerequisites (migrate, permission, `PE-MOH`, Administrator, test site from `bid_submission`) | Carried | §B2 |
| §1.1 fixture password for the register, Jane Wanjiku and the supplier people | Carried | §A2 |
| §1.2 a new server (packages, wkhtmltopdf 0.12.6.1, migrate, permission, no test tooling; what the seed does for itself; internet-facing sites) | Carried | §B2 |
| §1.3 `OPEN=True` (v1.25, never approved) | Dropped | Retired 5 Oct 2026: the executed portfolio's Medical-grade tablets Tender is open past the as-at instant (§A4.4, §B1) |
| §2 stage table (what each stage creates) | Superseded | Part A states the world per year and record; §B1 the stages |
| §2 every stage idempotent; never the legacy multi-PE orchestrator | Carried | §A6, §B8 |
| §2 generated references; EVL/AWD "tender 033" as an example of the form (D19) | Carried | §A6 |
| §2 the Evaluation people hold no standing responsibility; Esther Njeri holds Evaluation Technical Support (v1.18) | Carried | KT-STD-001 §8.3; §A2 |
| SEED-OPS-001 §2 the Evaluation people's departments (typed in the committee roster) and the appointment references the seed passed (v0.2) | Superseded | The department is each person's home unit (§A2) and the reference is generated (§A4.4, §A6); EVL-CHG-001 v0.7 §3 |
| SEED-OPS-001 §2 the secretary assigned by the Head of Procurement Function (Brian Wafula assigned by Charles Mutiso) (v0.3) | Superseded | The Head is recorded as secretary by office when the Accounting Officer appoints; Charles delegates to Brian at the same instant as before (EVL-CHG-001 v0.8 §3) |
| §2 four bids (v1.21): suppliers, people, prices, failures, ranking, notices | Carried | §A4.4 (accounts now registered 1–4 Mar 2027; offered deliveries 22–30 Jun 2027) |
| §3.1 what the clear removes | Carried, updated | §B3 (canonical Requisitions are every one on the executed plan; canonical Tenders every one on those; usage projections swept; a rebuild removes the canonical supplier accounts) |
| §3.1 the canonical world has no test clock | Superseded | D1: a test site reads the as-at instant (§A1) |
| §3.2 never touched | Carried | §B3 |
| §4 options | Carried, updated | §B4 |
| §5 validation | Carried, updated | §B5 (two years, the portfolio, the clock; the award stops at the acceptance, plan BF-10) |
| §6 adding the next module stage | Superseded | Part C |
| §7 troubleshooting rows | Carried where they still apply | §B7. Dropped: rows for faults fixed on 4 Oct 2026 or earlier whose cause no longer exists (`esbuild`, `freezegun` message, guard refusals, `lead_org_unit`, the evaluation presence lapse, the `OPEN=True` rows, the v1.3–v1.5 `wipe` rows, the v1.20 preparation-minimum patch) — each is in the retired file's history |
| §8 other seed entry points | Carried | §B8 |
| §9 Requisitions demo profiles | Carried | §B6 |
| §9A Bid Opening demo profiles | Carried | §B6 (restore now puts the as-at clock back) |
| §9B Award demo profiles | Carried | §B6 (`AWD-DEMO-WAIT` is the canonical world's own state; restore sets the as-at clock) |
| §9C Tender B for the Procurement meetings register; the clock for each persona case | Carried in part | §B6. The persona-clock table (Peter's Digital Health assignment from 1 Dec 2026; Julia's term to 30 Nov 2026) is superseded by §A2's dates |
| §10 change log | Dropped | History; retained in the retired files |
| §11 D1 Strategy title without "(Demo)" | Carried | Decided 26 Sep 2026 |
| §11 D2 2023 Strategy authority backdated | Carried | §A2 |
| §11 D3 generated references | Carried | §A6 |
| §11 D4 Peter heads the Directorate | Carried, date moved | §A2 (from 2 Sep 2025) |
| §11 D5 Grace as HRMD Head of User Department in the canonical world | Carried as open | Still granted (KT-STD-001 §8.3 regression fixture); owner decision pending |
| §11 D6 Need 0004 submission time | Carried as open | Year 2's Need 0004 is submitted 10:45 |
| §11 D7 READY canonical | Carried | §A4.3, §A5 |
| §11 D8 130m denominator | Carried, generalised | The plan's own value each year (§A4.3, §A5) |
| §11 D9–D14 (rule verification by direct stamp; rule window; disposal intake; Company; UOMs; schedule content) | Carried as open | Unchanged by this document |
| §11 D15 site configuration and grants at fixture instants | Superseded in part | The dated grants follow §A2; site configuration still happens at seeding time |
| §11 D16–D18 | Carried as open | Unchanged |
| §11 D19–D22 | Carried | Decided 1 Oct 2026 |
| §11 D23–D24 four bids and the suppliers' names | Carried | §A4.4; the names stand in KT-STD-001 v1.14 |
| §11 "not yet done" list (Planning back-stamping …) | Superseded in part | Every canonical Planning step now runs under the frozen clock; the isolated profiles' back-stamping and the two old Requisitions profiles remain open |

---

# Appendix B — Binding table (generated references on the test site)

The executed year's records as `kentender_core.seeds.portfolio.binding_rows()` reads them on `kentender-test.local` after a full seed. References are generated, so another site may number them differently; titles, states and holders are the same everywhere. The Home and Analytics fixtures are illustrative (HOME-CHG-001 v0.6 §13, ANL-CHG-001 v0.8 §13), so a design's own number (for example "Tender 042") maps to the record that carries its state, not to a reference.

Generated 5 October 2026 from a full seed (`CURRENT=award NEXT=annual_plan`), read as at 18 June 2027, 10:00 EAT. (v0.9: regenerated on 16 October 2026 from the anchored world at 9 October 2026 10:00 EAT by `portfolio.binding_rows()`: the references, states and holders of the rows below are unchanged; the world adds Year 0's three Tenders, listed after the notes.)

| Ref | Plan Item | Requisition | Tender | State | Serves |
|---|---|---|---|---|---|
| T1 | Clinical training and deployment laptops for digital health rollout (PPI-MOH-2026-002) | REQ-MOH-2026-002-001 | TND-MOH-2026-002 | Submission period ended; opening Opening complete; evaluation Report sent; award Waiting to proceed | ANL Award bucket and award amount; HOME H12 recently completed (Amina's award decision); AWD-DEMO-* profiles |
| T2 | Printers (PPI-MOH-2026-003) | REQ-MOH-2026-003-001 | TND-MOH-2026-003 | Submission period ended; opening Opening complete; evaluation Report sent; award Opinion | HOME H2/H10 Prepare professional opinion (Charles); ANL 044 shape |
| T3 | Laboratory desktop computers (PPI-MOH-2026-004) | REQ-MOH-2026-004-001 | TND-MOH-2026-004 | Submission period ended; opening Opening complete; evaluation Report sent; award Decision | HOME H12 Decide award (Amina) |
| T4 | Document scanners (PPI-MOH-2026-009) | REQ-MOH-2026-009-001 | TND-MOH-2026-009 | Submission period ended; opening Opening complete; evaluation Reviewing | HOME H10–H12 committee review outstanding and evaluation deadline; ANL 043 shape |
| T5 | Network switches (PPI-MOH-2026-010) | REQ-MOH-2026-010-001 | TND-MOH-2026-010 | Submission period ended; opening Opening complete; evaluation Preparing | HOME H12 Appoint the evaluation committee (Amina) |
| T6 | Medical-grade tablets (PPI-MOH-2026-005) | REQ-MOH-2026-005-001 | TND-MOH-2026-005 | Published — open; opening Awaiting deadline | Anonymous /tenders list; HOME H1 clarification, H3 addendum guard, H8 paging; H10 Start opening (Coming up); ANL Open bucket |
| T7 | UPS units (PPI-MOH-2026-011) | REQ-MOH-2026-011-001 | TND-MOH-2026-011 | Approved | HOME H1 completed submission, H10 waiting on Amina, H12 Authorise publication |
| T8 | Wireless access points (PPI-MOH-2026-014) | REQ-MOH-2026-014-001 | TND-MOH-2026-014 | Draft | ANL preparation bucket and warranty outstanding matter (041 shape); combined Digital Health + HRMD item |
| T9 | Field laptops (PPI-MOH-2026-006) | REQ-MOH-2026-006-001 | TND-MOH-2026-006 | Published — open | HOME H1 waiting on Amina, H12 Consider cancellation |
| T10 | Desktop computers (PPI-MOH-2026-012) | REQ-MOH-2026-012-001 | TND-MOH-2026-012 | Cancelled | HOME H1/H12 cancellation compliance evidence pending (034 shape) |
| T11 | Core network routers (PPI-MOH-2026-007) | REQ-MOH-2026-007-001 | TND-MOH-2026-007 | Cancelled | ANL Closed bucket, cancellation complete (046 shape); Women reservation |
| R-clinic | Clinic desktop computers (PPI-MOH-2026-008) | REQ-MOH-2026-008-001 | — | Submitted to Procurement | HOME H10 Authorise requisition (Charles); ANL R-A |
| R-monitors | Monitors (PPI-MOH-2026-013) | REQ-MOH-2026-013-001 | — | Authorised | ANL requisition authorised but not taken up (T2 transition open) |

Notes:

- T9 is told through the material-addendum route, the only one TPR-CHG-001 v0.17 §5.11 gives a "Consider cancellation" work item; a Head of Procurement recommendation is optional and opens none (the first generation of this table used the recommendation, so the item was missing — corrected 5 October 2026). Amina Hassan holds **Consider cancellation of TND-MOH-2026-006**; Brian Wafula waits on her. New fixture content for review: the 20-laptop increase and its reason.
- FY 2027/28 has no executed records: its budget, needs, departmental plans and Annual Plan (PLN-MOH-2027-001) are listed in Part A.
- (v0.9) At an October anchor the prepared year goes only as far as Departmental Needs (§A5), so FY 2027/28 has no departmental plans submitted and no Annual Plan.
- (v0.9) Year 0's three Tenders (§A7), as `binding_rows()` reads them on 16 October 2026; each award is at the stage *Waiting to proceed*:

| Ref | Plan Item | Requisition | Tender | State | Serves |
|---|---|---|---|---|---|
| Y0-1 | Staff workstation computers (PPI-MOH-2025-001) | REQ-MOH-2025-001-001 | TND-MOH-2025-001 | Submission period ended; opening Opening complete; evaluation Report sent; award Waiting to proceed | The closed year's history; Analytics' earlier months |
| Y0-2 | Multifunction office printers (PPI-MOH-2025-002) | REQ-MOH-2025-002-001 | TND-MOH-2025-002 | Submission period ended; opening Opening complete; evaluation Report sent; award Waiting to proceed | The closed year's history; Analytics' earlier months |
| Y0-3 | Replacement staff laptops (PPI-MOH-2025-003) | REQ-MOH-2025-003-001 | TND-MOH-2025-003 | Submission period ended; opening Opening complete; evaluation Report sent; award Waiting to proceed | The closed year's history; Analytics' earlier months |


# Appendix C — Required correction in KT-STD-001 (the Project Owner's document)

Replace §8.4 (Fiscal years) and §8.4A (Fixture instants) with:

> **8.4 Fiscal years and fixture instants.** The shared fixture is two financial years read as at 18 June 2027, 10:00 EAT: FY 2026/27 (1 Jul 2026 – 30 Jun 2027), the year being carried out, and FY 2027/28 (1 Jul 2027 – 30 Jun 2028), the year being prepared. SEED-002 Part A states each year's records and every fixture instant; a change unit takes its fixture dates from there. (v1.22 read: §8.4 listed FY 2026/27 Closed and FY 2027/28 Open, closing 25 Nov 2026 23:59 EAT; §8.4A listed one window per module composing "one coherent year".)

and in §8.3, the dated terms: Julia Njeri, Head of User Department (Acting), Digital Health, 2 Oct – 1 Dec 2025; Dr Peter Kimani, Head of User Department, Digital Health from 2 Dec 2025 and the Directorate from 2 Sep 2025; Samuel Otieno's expired term 2 Jan – 1 Sep 2025.

**(v0.8 replacement.)** The text above is the v0.7 replacement, retained as history. With the anchor model KT-STD-001 §8.4 and KT-STD-001 §8.4A are replaced by the text proposed in KT-STD-001 v1.30 (15 October 2026): the shared fixture is three financial years read as at the anchor; SEED-002 Part A states each year's records and every fixture instant, as offsets; a document's own fixture dates are illustrative unless SEED-002 states them. The paragraph above that adds dated terms to KT-STD-001 §8.3 is withdrawn: the terms are offsets stated in §A2, not dates in KT-STD-001 §8.3.

# Appendix D — New content for review and open questions

**New content, not from an approved source** (each was accepted in the two-year proposal or its answers, except where marked):

- The document identifier SEED-002 and its title (new here).
- The as-at instant and the 364-day shift (D1, D8).
- Year 1 Required by dates and approved invitation dates (D8); the Year 1 budget of KES 290m on four lines (plan BF-06; new here).
- The Year 2 Need titles (D10) and their descriptions, quantities and amounts (new here); Year 2's item values, designations and approved invitation dates (new here).
- The portfolio's items, quantities, amounts, lines, designations and approved invitation dates; the IT substitutes for the design titles that are not IT equipment (plan BF-05; new here); the Tender titles, security amounts and dates; the bids' models, prices and security references; the six T6 questions; the cancellation reasons and evidence references (new here).
- The laptops' latest delivery date and the four bids' offered dates (plan BF-04; new here).
- The supplier accounts' registration instants (plan BF-09; new here).
- (v0.2) Nothing new in the seed: the units, the home units and Esther Muthoni as the Not recorded fixture are KT-STD-001 v1.26 content, approved on 8 October 2026; the Project Owner's structure question (D4 of EVL-CHG-001 v0.7 §12.6) was accepted with that approval.
- (v0.8) The rules R1 to R7; the clock policy names `free`, `never_ahead` and `off` and the site-configuration key `kt_test_clock_policy`; the 60-day limit (RA-OD4); the statement that Year 0 is built by the machinery of Year 1 one year earlier; the 651-day block shift (arithmetic, 15 October 2026); the season described in §A1.1. The decisions RA-1 to RA-5 and RA-OD1 to RA-OD4 are quoted in RA-PROP-001 v1.
- (v0.9) Year 0's content (§A7): the Budget `MOH-FIN-BUD-2025-01 (Demo)` and its two lines, the Need NDS-MOH-2025-0001, the three Plan Items, the three Tenders with their quantities, prices, security amounts, models and reference numbers, and the supplier accounts' registration instants; the three-slot spread of Year 0's Tenders and its 14-day margin; the numbers 100 (`SEASON_MIN_ELAPSED_DAYS`), 49 (the October pull, arithmetic), 252 (E, arithmetic), the late-season clamp, the 7-day live-deadline week and the hold of delivery dates to the year's last day; the site default `kt_seed_world_state`; the 60 days counted from the run that built the world; the rule window starting on 1 January of the first seeded year (§B2).

**Questions for the Project Owner**, each with a recommendation:

1. *Approve SEED-002 as the replacement of SEED-001 and SEED-OPS-001?* Recommended: yes; the retired files move to `20_seed_data/retired/` and every link changes in the same step.
2. *Apply Appendix C to KT-STD-001?* Recommended: yes, in the next KT-STD-001 version.
3. *Record artifact hashes in a run manifest (SEED-001 §1.3)?* Recommended: not now; the validator's report and the commit identify a run.
4. *D5 — move Grace Wanjiku's HRMD Head of User Department grant to the isolated permissions fixture?* Recommended: yes, in a later change; it does not affect the two-year world.
5. *(v0.8) RA-OD5 — keep the fiscal year at 1 July to 30 June, or amend CFG-CHG-002 v0.19 CFG10-EC-001 and CFG10-AC-009 so the seed may use a shifted year?* (§A1.2.) Recommended: keep 1 July to 30 June and anchor on the end of the season (the previous June), with a notice, when too little of Year 1 has elapsed; a shifted year would change the System setup command, its error, two acceptance criteria and the Strategy display, and CFG10-EC-001 says it is "not overridden to fit a seed". Reconsider only if Phase 1 shows the history cannot fit even when tightened toward the legal minimums. **Decided 15 October 2026:** “1. Keep 1 Jul to 30 Jun”. Whether the history can be tightened to fit without anchoring on the previous June is still measured in Phase 1 (spike A).

## Change record — v0.5 (10 October 2026)

v0.5 corrects the tender-security intake and sealed-bid confidentiality gap on the Project Owner's instruction of 10 October 2026 (quoted in the control table). Every changed place keeps its v0.4 wording; additions are marked v0.5.

| Place | v0.4 wording | v0.5 wording |
|---|---|---|
| Control table | v0.4 change | adds the v0.5 change row |
| §A2 | This world adds no person | adds the intake duty paragraph; no person added |
| §A4.4 | physical security original recorded by Charles Mutiso | recorded by Mercy Kilonzo, assigned by Charles; matched after the opening starts |
| §B5 | The clock | adds the tender-security intake validation |

Source preservation: v0.4, SHA-256 `30e0082a5f70e195e81f38ddec95422c627f6c1219c1291ac092c16385db001d`; the v0.4 file is unchanged. Approval and the existing implementation, legal and interface verification requirements remain outstanding.

## Change record — v0.6 (10 October 2026)

v0.6 carries v0.5 in full and applies the Project Owner's answers of 10 October 2026 to the open decisions on supplier status wording, template and published Tender data, incident-record exposure and emergency access (quoted in the control table). Every changed place keeps its v0.5 wording; additions are marked v0.6.

| Place | v0.5 wording | v0.6 wording |
|---|---|---|
| Control table | v0.5 change | adds the v0.6 change row |
| §B5 | tender-security intake validation | adds the Tender-security statements and the supplier status |

Source preservation: v0.5, SHA-256 `f06344f20459ed5f9e84df3f02f71cd08edad47c707088b35f131bff1f0b28a0`; the v0.5 file is unchanged. Approval and the existing implementation, legal and interface verification requirements remain outstanding.

## Change record — v0.7 (10 October 2026)

v0.7 carries v0.6 in full and applies the Project Owner's answers of 10 October 2026 to the open decisions on supplier status wording, template and published Tender data, incident-record exposure and emergency access (quoted in the control table). Every changed place keeps its v0.6 wording; additions are marked v0.7.

| Place | v0.6 wording | v0.7 wording |
|---|---|---|
| Control table | v0.6 change | adds the v0.7 change row |
| §B5 | Electronic / Required | Bidder uploads an electronic instrument / Required; release 1.5 |

Source preservation: v0.6, SHA-256 `df3057f5bb4c9c87b863262a7352400f6c85fb8039c10a1a0844ae2176c8e8d9`; the v0.6 file is unchanged. Approval and the existing implementation, legal and interface verification requirements remain outstanding.

## Change record — v0.9 (16 October 2026)

v0.9 carries v0.8 in full and states the anchor model as built. Every changed place keeps its v0.8 wording; additions are marked v0.9.

| Place | v0.8 wording | v0.9 wording |
|---|---|---|
| Control table | v0.8 version, date, status, approval rows | v0.9 rows; v0.8 retained beside each; adds the v0.9 change and owner instruction rows; evidence |
| §A1, §A1.1 R2, the season | state not decided; season measured later | adds the v0.9 reading, where the anchor is stored, the two season rules and the unmeasured 100 |
| §A3.1 | — | new: the offsets as built |
| §A7 | Year 0 Awaiting fixture; Budget closed after the year's end | adds Year 0 as built, why its Budget stays Active and its awards wait |
| §A8 | block offsets Awaiting fixture | adds that Contract Management's release is awaited |
| §B1, §B3, §B4, §B5, §B7 | the command, the clear, options, validation, troubleshooting | adds the anchor, three years kept, the options, the anchor checks, four rows |
| Appendix B, Appendix D | the v0.8 binding table; v0.8 new content | marks the table to be regenerated; adds the v0.9 new content |

Source preservation: v0.8, SHA-256 `62342c446ef96a9195b40417fd24ea311bf35c3a2a79ea59b42576d48b20c3a8`; the v0.8 file is unchanged. Approval and the existing implementation, legal and interface verification requirements remain outstanding.

## Change record — v0.8 (15 October 2026)

v0.8 carries v0.7 in full and states the anchor model of RA-PROP-001 v1 (approved 15 October 2026). Every changed place keeps its v0.7 wording; additions are marked v0.8. It states requirements ahead of the build: until Phase 3 of `Real_Date_Anchor_Implementation_Plan.md` the seed still builds the v0.7 world.

| Place | v0.7 wording | v0.8 wording |
|---|---|---|
| Control table | v0.7 version, date, status, approval rows | v0.8 rows; v0.7 retained beside each; adds the v0.8 change and owner instruction rows |
| Controlling decision | two financial years read as at 18 June 2027 | adds the anchor paragraph; three financial years |
| §A1 | the as-at instant 18 June 2027; a non-test site shows a story ahead of the real calendar (D2) | adds the v0.8 reading, §A1.1 (rules R1 to R7, the world's age, the season) and §A1.2 (the fiscal-year check) |
| §A3 | the instants of each year's work | adds that every instant in §A2 to §A5 is illustrative and an offset, Awaiting fixture |
| §A5 | Year 2 goes to an approved Annual Plan | adds that the prepared year goes as far as the anchor allows (Departmental Needs at 15 October 2026) |
| §A6, §A7, §A8 | six rules | adds the never-ahead rule, Year 0 (the closed year) and Contract Management's demonstrations |
| §B1, §B2, §B5, §B6, §B7 | the command, prerequisites, the clock check, demonstration profiles, troubleshooting | adds the default `NEXT`, the clock policy, the check by policy, profile moments not later than the anchor, two troubleshooting rows |
| Part C | step 2 | adds the frozen clock and never-ahead rules |
| Appendix C | the v0.7 replacement for KT-STD-001 §8.4 and KT-STD-001 §8.4A | adds the v0.8 replacement (KT-STD-001 v1.30) and withdraws the dated terms for KT-STD-001 §8.3 |
| Appendix D | new content and four questions | adds the v0.8 new content and question 5 (RA-OD5) |

Source preservation: v0.7, SHA-256 `d5f4fd615acf1a7fdcb545192226f12e9209dd6c0367a89fc690a8e9613c6b63`; the v0.7 file is unchanged. Approval and the existing implementation, legal and interface verification requirements remain outstanding.
