# Proposal: a two-year canonical seed world

| Control | Value |
|---|---|
| Date | 4 October 2026 |
| Status | Decisions accepted — 4 October 2026. Project Owner, verbatim: "Decisions for the owner: recommendations accepted", answering §9 D1–D7. Phase 1 (documents) started. (Proposed status read: Proposal for the Project Owner. Not approved. No code or controlled document has been changed.) |
| Asked for by | Project Owner, 4 October 2026: one active procurement year executing against an accepted, locked Annual Procurement Plan; one future year whose cycle is being prepared; a make command that moves each year's journey separately; an expanded data set for Home and Analytics. "Evaluate the above and create a proposal if sound." |
| Read for this proposal | KT-STD-001 v1.22 §8 (in full); HOME-CHG-001 v0.6 implementation plan (in full); HOME-CHG-001 v0.6 §10B.2, §13 and §13.1; HOME `reconciliation/seed_scenario_map.md` (in full); ANL-CHG-001 v0.8 §§4–5.5, §10A.1–10A.4 and §13–13.1. Seed code read in part: `kentender_core/seeds/{canonical,site_setup,clock}.py`, the Strategy, Budget, Planning, Requisitions, Tenders, Bid Submission and Award seed modules (dates and fiscal-year constants only). |
| Not read | The Home and Analytics `.dc.html` boards (their fixture text is in the specs); SEED-001 v1.4; the module specs' own fixture sections other than through the documents above. |

## 1. Verdict

The request is sound. It fixes the cause of the strain we keep hitting, and it fits what Home and Analytics need. Three things need settling before building, set out as decisions in §9:

1. **Where "now" sits in the story.** Every Home and Analytics design is read on 16–18 June 2027, and the existing chain's dates already sit in March–July 2027. Fixing the story's "now" at **18 June 2027, 10:00** keeps all of that and makes both years natural. On a server without the test clock, the real date (October 2026) still sits before the story; §9 D2 covers that.
2. **Stopping a year early leaves records stopped.** With independent controls, stopping the current year at `tenders` leaves tenders whose deadlines have passed with no bids, as today. That is acceptable for a testing control, but it must be stated.
3. **The governing fixture register has to change.** KT-STD-001 §8.4 (fiscal years) and §8.4A (fixture instants) describe a single year. They are the owner's document; this proposal names the correction, it does not make it.

## 2. What the seed does today, and why it strains

Every stage tells one story about the **FY 2027/28** plan, carried out before that year begins:

| Stage | Fiscal year | Seeded dates |
|---|---|---|
| Departmental needs | 2027/28 | from 24 Nov 2026 |
| Departmental plans and Annual Plan | 2027/28 | 25 Nov – 10 Dec 2026 (Plan published 10 Dec 2026) |
| Budget | 2027/28 | 1 Oct 2026 – 16 Mar 2027 |
| Requisition | 2027/28 | March 2027 |
| Tender, bids, opening | 2027/28 | 20 Mar – 12 Jun 2027 |
| Evaluation, award | 2027/28 | 12 Jun – 2 Jul 2027 |

So the real current year (FY 2026/27) has no plan, no budget in use and no procurement. The plan for 2027/28 is bought before 1 July 2027. Analytics' own design dataset carries the same mismatch and says so: ANL-CHG-001 v0.8 §13 "Existing source-pack FY/date mismatches are not repaired by this Analytics fixture."

A real Ministry carries out this year's plan while preparing next year's. Those are two journeys running side by side, and the seed squeezes them into one.

## 3. The proposed world

One moment, the **as-at instant**, is the story's "now": **18 June 2027, 10:00 EAT**. It is the read time of HOME-CHG-001 v0.6 H10–H12 and of ANL-CHG-001 v0.8 dataset A1. Everything recorded is at or before it; every live deadline is after it. Test and dev sites set the site test clock to it, as the demo profiles do today.

At that moment the Ministry is twelve days from the end of FY 2026/27:

### 3.1 Year 1 — FY 2026/27, the year being carried out

**Always built (the base).**
- Budget FY 2026/27 registered and approved before the year began.
- Needs collected, departmental plans accepted and the Annual Plan approved, published and Active, with its baseline locked (`PLN_BASELINE_LOCKED` already exists).

These are today's Needs, Planning and Budget journeys **moved back exactly one year** (needs 24 Nov 2025, Plan published 10 Dec 2025, budget from 1 Oct 2025), and pointed at FY 2026/27.

**Carried out against that plan, up to a chosen stage:** requisitions, tenders, bid submission, bid opening, bid evaluation and award. The existing chain keeps its dates (March–July 2027), which now fall inside the year they spend. Requisitions draw on the FY 2026/27 plan and reserve against the FY 2026/27 budget.

### 3.2 Year 2 — FY 2027/28, the year being prepared

Today's Needs, Planning and Budget journeys stay where they are: needs on 24 Nov 2026, the Plan published 10 Dec 2026 and budget registration from 1 Oct 2026. They become what they always were in substance: next year's preparation. **Year 2 never goes past an approved Annual Plan.** No requisition, tender or reservation is made against it.

### 3.3 What moves to make Year 1's history possible

Year 1's planning happens in late 2025. Everything it relies on must already be in force then:

- **Site configuration history** moves from 29 Jun 2026 to before October 2025.
- **Responsibility start dates** move before the Year 1 history. Today they start on 1 Sep 2026, 1 Oct 2026, 1 Dec 2026 or 1 Jan 2026. The deliberate exceptions stay: Samuel Otieno's expired responsibility and Julia Njeri's acting period.
- **Procurement rule and Regulatory Reference effective dates** currently start on 1 Jul 2026 and must start earlier.
- **Supplier accounts** start before the first Year 1 tender opens. Today they start 18 May – 3 Jun 2027.
- **A closed FY 2025/26** may need to exist as a configured year with no business records. §9 D3 asks the owner; the build confirms whether any command requires it.

Strategy needs nothing: the plan period already runs 1 Jul 2023 – 30 Jun 2028 and covers both years.

## 4. The make command

```bash
make seed-canonical SITE=<site> CURRENT=<stage> NEXT=<stage>
```

| Control | Year | Stages, in order | Meaning |
|---|---|---|---|
| `CURRENT` | FY 2026/27 | `annual_plan`, `requisitions`, `tenders`, `bid_submission`, `bid_opening`, `bid_evaluation`, `award` | `annual_plan` is the always-built base: budget, needs, departmental plans and the Active, locked Plan. Each later stage adds that step for every record in the portfolio (§5) that reaches it. |
| `NEXT` | FY 2027/28 | `none`, `budget`, `needs`, `departmental_plans`, `annual_plan` | `none` leaves the year configured, with nothing done in it. `annual_plan` is the ceiling. |

The site, organisation units, people and Strategy are shared and always built.

Examples:

```bash
make seed-canonical SITE=… CURRENT=award NEXT=annual_plan        # the full world (proposed default)
make seed-canonical SITE=… CURRENT=requisitions NEXT=budget      # requisitions in progress; next year's budget only
make seed-canonical SITE=… CURRENT=annual_plan NEXT=needs        # nothing bought yet; next year's needs coming in
make seed-canonical-validate SITE=… CURRENT=… NEXT=…
```

**Kept.** `REBUILD=True`, `FORCE=True`, the dry run, validation, demo profiles, `release_demo_profiles()` and rebuild-on-mismatch.

**Retired.**
- `THROUGH` stays for one release as an alias. Values up to `planning` map to `NEXT` with `CURRENT=annual_plan`; later values map to `CURRENT` with `NEXT=annual_plan`. It then prints a notice and is removed.
- `OPEN=True` is retired. The portfolio always holds a tender that is open for bids, so anonymous visitors see one without a special switch.

**Stopping early (§9 D5).** A stage cap stops every record at that stage, even where its dates say it would have moved on. For example, `CURRENT=tenders` leaves tenders whose deadlines are before the as-at instant closed with no bids. The as-at instant does not move with the cap, so the two years stay independent.

## 5. The expanded Year 1 portfolio for Home and Analytics

Home and Analytics need many records in different states at the same moment. Today there is one chain, and the demo profiles are mutually exclusive: loading one rebuilds Planning (`seed_scenario_map.md` §2). The proposal replaces the single chain with a **portfolio**: several plan items, requisitions and tenders, each built through the owners' commands by the named actors, each stopping at its own state at the as-at instant.

The seed provides **states**, not the designs' exact numbers. Both specs say their datasets are illustrative:
- ANL-CHG-001 v0.8 §13: "A1/A2/A3 are **illustrative design datasets**, not installed records."
- HOME-CHG-001 v0.6 §13: "All H scenarios are **illustrative artboard fixtures**". It also says "Before runtime comparison create through owner commands and bind generated identities to each scenario".

References stay generated (DEC-027), so a seed cannot promise "TND-MOH-2027-042".

### 5.1 Tenders (one consumed requisition each)

| # | State at 18 Jun 2027, 10:00 | Holder of the next step | Serves |
|---|---|---|---|
| T1 | Award decided, required notices not all confirmed. This is today's canonical laptops tender, with four bids, report sent 16 Jun 14:07 and award 17 Jun 10:00. | Charles Mutiso (notice delivery) | ANL Award bucket and award amount; HOME H10 and H12 rows of the 045 kind; HOME "recently completed" for Amina |
| T2 | Report delivered; professional opinion not yet signed | Charles Mutiso | HOME H2, H10; ANL 044 kind |
| T3 | Opinion signed; award decision pending | Amina Hassan | HOME H12 ("Decide award") |
| T4 | Evaluation in committee review; statutory deadline after the as-at instant | Committee chaired by Grace Wambui | HOME H10 Coming up, H11 and H12 oversight; ANL 043 kind |
| T5 | Opening complete; evaluation committee not yet appointed | Amina Hassan | HOME H12 ("Appoint the evaluation committee") |
| T6 | Published and open for bids, deadline after the as-at instant. The opening is scheduled, and the opening chair has an Upcoming "Start opening". It carries clarifications: one answerable; one whose answer needs an addendum; six in all, for paging. | Brian Wafula; opening chair | Anonymous `/tenders` list; HOME H1 (clarification), H3 (blocked), H8 (paging), H10 Coming up; ANL Open bucket |
| T7 | Submitted by Brian, approved by Charles, awaiting publication decision | Amina Hassan | HOME H1 (completed submission), H10 (waiting), H12 ("Authorise publication") |
| T8 | Returned to Brian for correction (warranty period) | Brian Wafula | ANL preparation bucket and outstanding matter (041 kind) |
| T9 | Cancellation requested, under the Accounting Officer's consideration | Amina Hassan | HOME H1 (waiting), H12 ("Consider cancellation") |
| T10 | Cancelled; compliance evidence pending, due after the as-at instant | Brian Wafula | HOME H1, H12 waiting (034 kind) |
| T11 | Cancelled; compliance evidence complete | — | ANL Closed bucket (046 kind) |

Optional negatives, still to be decided (§9 D4): an empty opening (closed, no bids), and a No award decision.

### 5.2 Requisitions

- One authorised and consumed requisition per tender above.
- One **submitted to Procurement, awaiting Charles's authorisation**: HOME H10, ANL R-A.
- One **authorised, not yet taken up by a tender**. ANL T2 "authorised to Tender started" needs a not-yet-consumed case to be meaningful.
- At least one with **two departments' drawdown lines**: Digital Health and HRMD (ANL R-B).
- At least one that **draws less than its plan allowance** (ANL R-C).
- Every drawdown reserves against the FY 2026/27 budget. That gives Analytics a real funding position: the Digital Health line, the HRMD line and the line available to all departments, as in ANL A1.

### 5.3 Plan, needs and departmental plans (Year 1)

- Enough plan items for one per requisition, plus one with no requisition. That gives fully, partly and not-covered items (ANL M-07).
- Items are split across Digital Health and HRMD, with at least one combined item.
- Year 1 needs and both departmental plans are accepted.
- Year 2 keeps today's four needs. One is still Submitted for Dr Peter Kimani's review, which serves HOME H11's review task.

### 5.4 Monthly and timing measures

Analytics reads the twelve months to the as-at instant: July 2026 – June 2027. Year 1 events fall across that window:
- requisitions submitted and authorised from March;
- tenders published April – May;
- openings in May – June;
- reports and decisions in June.

Year 2's needs and departmental-plan acceptances (Nov–Dec 2026) also fall inside it. That gives ANL M-03 and M-04 real, non-trivial values. Each tender's instants are chosen so its own owner's checks pass at execution: the 7-day legal minimum and 21-day usual bid period, the evaluation statutory period and the standstill.

### 5.5 People

No new person is needed. Grace Wambui, Peter Mugo and Ruth Achieng are appointed to each evaluated tender (T1–T4) by the Accounting Officer, with their own declarations. The four supplier companies bid on T1–T5, which means more bids, each made by the company's own signatory.

## 6. What changes

**Code** (all through the owners' commands; no direct writes):
- `kentender_core/seeds/canonical.py`:
  - the stage ladder becomes two ladders and the `CURRENT`/`NEXT` arguments;
  - validation per year;
  - the rebuild path;
  - the `THROUGH` alias;
  - `OPEN` retired.
- `site_setup.py`:
  - one as-at constant;
  - earlier site history, responsibility starts and rule effective dates;
  - FY 2025/26 if D3 says so.
- Budget, Needs and Planning seeds take the fiscal year and a whole-year shift as parameters, so the same journey runs for Year 1 (shifted back one year) and Year 2 (as today). Each module keeps a single `FY` constant today, so this is the main refactor.
- Requisitions, Tenders, Bid Submission, Bid Opening, Bid Evaluation and Award seeds:
  - re-pointed to FY 2026/27;
  - generalised from one record to the portfolio table;
  - supplier account dates moved earlier.
- Makefile targets, help text and `tests/test_canonical_seed.py` (ladder, caps, independence of the two years, portfolio states present).
- Module tests and Playwright specs that pin "FY 2027/28" or assume the single canonical requisition or tender. The build counts these first; the number is not known yet.

**Documents:**
- KT-STD-001 §8.4 and §8.4A: required correction, the owner's document.
- SEED-001: a new version for the two-year story and portfolio.
- SEED-OPS-001: a new runbook version (v1.25 is proposed and unapproved; this would follow it).
- HOME-CHG-001 v0.6 plan Phase 7 and `seed_scenario_map.md`: most H scenarios come from the one world, not a Home fixture module.
- ANL-CHG-001: a note that the seed attributes executed records to FY 2026/27, not A1's FY 2027/28.

## 7. Phasing

Each phase ends with a full reseed and validation on `kentender-test.local`.

1. **Decisions and documents.** The owner settles §9. The SEED-001 and SEED-OPS-001 versions are drafted under the document-change protocol, with the KT-STD-001 §8 correction written out for the owner to apply.
2. **Calendar and Year 1 base.**
   - Add the as-at constant.
   - Move site history, responsibilities and rules earlier.
   - Parameterise the Budget, Needs and Planning journeys by year, and build Year 1 shifted back one year.
   - Add the `CURRENT`/`NEXT` ladders.
   - Done when `CURRENT=annual_plan` with each value of `NEXT` validates.
3. **Re-point the existing chain to Year 1.** The laptops tender runs against the FY 2026/27 plan and budget with its dates unchanged. Done when `CURRENT=award NEXT=annual_plan` validates and the affected module tests pass on the test site.
4. **Portfolio.** Add T2–T11 and the extra requisitions and plan items, in stage order, each checked by validation at its own state. Measure the full run time on the test site and on a fresh-like site.
5. **Home and Analytics read check.** A validation step asserts every state in §5 exists at the as-at instant, and records each generated reference against the Home and Analytics scenario it serves.
6. **Retire and document.** Remove `OPEN`, start the `THROUGH` alias period, and update the runbook, CLAUDE.md, the README and memory.

## 8. Risks

- **Run time and memory.** Five tenders go through bids and opening, and four go through evaluation, against one today. The seed will be several times longer downstream, and the 1 vCPU / 512 MB server may struggle. The `CURRENT` caps keep smaller runs available. Run time is measured in Phase 4, not estimated here.
- **Hidden date assumptions.** Tests and module code may assume FY 2027/28 or the single canonical record. Phase 3 finds them before the portfolio is added.
- **Weekdays shift.** Moving Year 1 back exactly one year moves each date one weekday earlier. Any owner check that depends on working days will reject an instant that now falls on a weekend; the build checks and adjusts each such instant.
- **Real calendar.** Without the test clock, a server still shows a story set after today (D2).
- **Other sessions' work.** Home and Analytics are being built now, and their Phase 7 seed work overlaps this proposal. The two need to be sequenced, not built twice.

## 9. Decisions for the owner

| # | Question | Recommendation |
|---|---|---|
| D1 | Where is the story's "now"? | **18 June 2027, 10:00 EAT**, fixed. It matches the Home and Analytics designs, keeps the existing chain's dates and is a natural point in the year: Year 1 nearly complete, Year 2's plan approved. Test and dev sites run with the test clock at that instant. |
| D2 | What should a server without the test clock show? (Today's date there is October 2026.) | Accept, for now, that the story is dated ahead of the real calendar. The open tender (T6) still makes the anonymous list work. Write every instant as an offset from the as-at constant, so a later "shift the whole story back N years" option is a one-line change. Decide that option separately. |
| D3 | Should a closed FY 2025/26 exist as a configured year? | Yes, if any command needs a configured year around Year 1's late-2025 history. Configuration only, with no business records. The build confirms whether it is needed. |
| D4 | Approve the portfolio in §5, and decide whether to add the two optional negatives (empty opening, No award). | Approve T1–T11. Leave the negatives out of the canonical world; the modules' isolated negative fixtures already cover them. |
| D5 | When a year is capped, do records stop where the cap leaves them, even if their dates say otherwise? | Yes. The caps are a testing control, and keeping the as-at instant fixed keeps the two years independent. |
| D6 | What does a plain `make seed-canonical` build? | The full world, `CURRENT=award NEXT=annual_plan`, because Home and Analytics need it. Today's default is `THROUGH=requisitions`. |
| D7 | Who amends KT-STD-001 §8.4 and §8.4A? | You, in your own copy, as with earlier KT-STD-001 fixture changes. This proposal supplies the replacement text in Phase 1. |

### 9.0 Phase 1 finding — planned dates must fit their own year (4 October 2026)

Needs and departmental plans refuse a Required by outside their financial year, and Planning blocks an item whose baseline signing plus delivery ends after its boundary. So Year 1 keeps the chain's actual dates (requisition to award), but its Required by dates and Plan baselines move inside FY 2026/27. The laptop Tender is then published 103 days after its approved invitation date. Year 1's history is dated 364 days (52 weeks) before Year 2's, so weekdays are kept. Details and replacement text: `KenTender_Two_Year_Seed_World_Fixture_Corrections_2026-10-04.md`.

### 9.1 Decision record

Project Owner, 4 October 2026: "Decisions for the owner: recommendations accepted". Each of D1–D7 is settled as its Recommendation column states. Nothing outside §9 is decided by this record.

## 10. Not verified

- Whether any owner command refuses a Year 1 action dated in late 2025 for a reason not found here. Examples: a rule effective date, an intake window or a working-day check.
- How many tests and specs assume FY 2027/28 or the single canonical record.
- Run time and memory use of the portfolio seed.
- Whether HOME H11's "Staff training laptops" need, submitted on 17 Jun 2027, can be made honestly. Year 2's intake closed on 25 Nov 2026, so it would need the late-need route. Until checked it stays artboard-only, and H11 uses the existing pending need.
- The Home and Analytics boards themselves (their fixture text was read in the specs).
