# Two-year seed world: implementation plan

| Control | Value |
|---|---|
| Version | plan.1 |
| Date | 4 October 2026 |
| Authority | `KenTender_Two_Year_Seed_World_Proposal_2026-10-04.md`. Its decisions D1–D7 were accepted by the Project Owner on 4 October 2026, verbatim: "Decisions for the owner: recommendations accepted". |
| Companions | `KenTender_Two_Year_Seed_World_Fixture_Corrections_2026-10-04.md` (Phase 1 output); `Two_Year_Seed_World_IMPLEMENTATION_TRACKER.md` |
| Folder | `docs/mvp-1-r1/20_seed_data/` collects this work's documents (owner instruction, 4 October 2026: "Create a dedicated seed_data folder to collect the documentation and implementation work"). |
| Status | **In progress.** The hold (owner, 4 October 2026: "Let's hold on the implementation for now to avoid interfering with other work.") was released on 5 October 2026 when the Analytics session, at the owner's instruction, said "You can start the seed world" and the owner had said "Run to completion as I will not prompt you again". Phases 2–4 built and committed (bedf8a5b); regression, the state check, the documentation revamp and roll-out follow. |

## Context

The canonical seed tells one story: the FY 2027/28 plan, carried out before that year begins. The real current year (FY 2026/27) has no plan in use and no procurement. Home and Analytics also need many records in different states at the same moment, but the seed has one chain, and its demo profiles cannot be stacked.

The target world is read **as at 18 June 2027, 10:00 EAT**:
- **Year 1, FY 2026/27, being carried out.** Its budget, needs, departmental plans and Annual Plan (Active and locked) are always built. Requisitions, Tenders and later stages run against that Plan. A portfolio of 11 Tenders sits at different states.
- **Year 2, FY 2027/28, being prepared.** Budget, needs, departmental plans and Annual Plan only.
- **Controls.** `make seed-canonical CURRENT=<annual_plan…award> NEXT=<none|budget|needs|departmental_plans|annual_plan>`.

## Decisions on record

| Ref | Decision | Source |
|---|---|---|
| D1 | As-at instant fixed at 18 Jun 2027, 10:00 EAT; test sites use the test clock | Proposal §9, accepted 4 Oct 2026 |
| D2 | A server without the test clock stays future-dated for now; instants are written as offsets from the as-at constant, so a later whole-year shift is cheap | same |
| D3 | A configured, closed FY 2025/26 only if a command needs it | same |
| D4 | Portfolio T1–T11; no negative cases in the canonical world | same |
| D5 | A capped year's records stop where the cap leaves them | same |
| D6 | The default is the full world: `CURRENT=award NEXT=annual_plan` | same |
| D7 | The owner amends KT-STD-001 §8.4/§8.4A and SEED-001 in their own library | same |
| D8 | Planned dates fit their own year. Year 1 Required by is 30 Jun 2027; the laptop baseline invitation is 1 Feb 2027; actual dates are kept. Year 1's history is dated 364 days before Year 2's. | Corrections §1–§2; owner "1. Accepted", 4 Oct 2026 |
| D9 | T6 title "Supply of medical-grade tablets" | Owner "2. Accepted", 4 Oct 2026 |
| D10 | Year 2 Need titles: Health information exchange platform upgrade; Training centre audio-visual equipment; Clinical decision-support software licences | Owner "3. Accepted", 4 Oct 2026 |
| D11 | The documentation revamp is one task; the current seed documents may be retired and replaced by a clean successor | Owner, 4 Oct 2026: "include documentation revamp as one task. If it is easier, the current document can be retired completely so the next version can start on a clean slate without the previous baggage." |
| D12 | **One** new document replaces both SEED-001 (fixture, v1.4) and SEED-OPS-001 (runbook, v1.25 proposed). It has three parts: the world, how to seed it, and how a module adds to it. KT-STD-001 §8.4/§8.4A shrinks to a pointer to it. | Owner, 4 Oct 2026: "one new document to replace both the fixture document and the runbook" (answering OQ-1) |

(OQ-1 answered; recorded as D12 above.)

## Rules for working alongside other sessions

These come from the check made on 4 October 2026. At that point the Home session was writing core service files and a Budget provider, and running tests on `kentender-test.local`.

1. **Own site for seed work.** Every reseed in Phases 2–5 runs on a separate copy, `kentender-seed.local` on port 8002, via `TEST_SITE=… TEST_PORT=… scripts/test-site.sh`. The script already reads both variables. `kentender-test.local` is left to the module sessions.
2. **The dev site is reseeded once**, in Phase 7, after the world is proven, and the owner is told first.
3. **Shared files.**
   - `Makefile` carries other sessions' uncommitted hunks. Commit only this work's hunks, using a private index.
   - `bid_evaluation/seeds/kentender_mvp_v1.py` and `kentender_core/seeds/README.md` carry other sessions' uncommitted edits. Build on them; never revert them.
4. **Home's seed phase.** HOME-CHG-001 plan Phase 7 (a Home fixture module of named worlds) overlaps this work. Before Phase 4, the owner or the Home session is told that the portfolio supplies those states. Until then, Home tests should not depend on the FY 2027/28 label or on there being one Tender.
5. **Approved seed documents stay in `00_common/` until Phase 6.** SEED-001 and SEED-OPS-001 are linked from `CLAUDE.md`, the `Makefile`, `kentender_core/seeds/README.md`, the register and OVS and Strategy documents, several of which other sessions are editing. They move or retire in the revamp, with every link updated in one step.

## Current state (verified 4 October 2026 by reading source; nothing run)

- `kentender_core/seeds/canonical.py`:
  - `STAGES = ("site", "strategy", "budget", "needs", "planning", "requisitions", "tenders", "bid_submission", "bid_opening", "bid_evaluation", "award")`;
  - `OPEN_TENDER_STAGES` for `OPEN=True`;
  - rebuild-on-mismatch through `CanonicalTenderNeedsRebuild`.
- `site_setup.py`:
  - `FISCAL_START_YEARS = (2026, 2027)`;
  - Needs, DPP and disposal intakes for start year 2027;
  - rule effective dates from `f"{FISCAL_START_YEARS[0]}-07-01"`;
  - responsibility starts from 1 Sep 2026, 1 Oct 2026, 1 Dec 2026 and 1 Jan 2026 (Strategy people from 1 Jul 2023).
- Each module seed holds one fiscal year constant (Budget `FY = "2027-2028"`; Planning and Requisitions read the 2027/28 plan) and fixed instants:

| Stage | Seeded instants |
|---|---|
| Needs | from 24 Nov 2026 |
| Planning (`CLOCK`) | 25 Nov – 10 Dec 2026 |
| Requisitions | from 1 Mar 2027 |
| Tenders | 20 Mar – 12 Jun 2027 |
| Award | 17 Jun – 2 Jul 2027 |

- Strategy V1 was approved 1 Jul 2023 for 1 Jul 2023 – 30 Jun 2028, which covers both years.
- Owner checks that bind dates to a year:
  - `departmental_needs/services/lifecycle.py:474` (Required by inside the FY);
  - `procurement_planning/services/dpp_lifecycle.py:521` (same);
  - `procurement_planning/services/readiness.py:437` (`PLN_DELIVERY_BOUNDARY_INSUFFICIENT`).
- An hourly scheduler job closes due submission periods on real time (`tenders.services.submission_close.close_due_submission_periods`).

## Phases

Every phase follows the AGENTS.md loop: smallest failing check first, smallest change, focused tests, then one reseed and validation on `kentender-seed.local`, then the tracker row updated with evidence.

**Phase 0 — Preparation (documents only).** Create the folder, move this work's documents into it, and write this plan and the tracker. **Gate SW-G00:** the files exist, decisions are recorded verbatim, and no code has changed.

**Phase 1 — Decisions and correction text (documents only).** The proposal, the owner's decisions, and the replacement text for KT-STD-001 §8.4/§8.4A and SEED-001. **Gate SW-G01:** done 4 Oct 2026, committed fec5ebba.

**Phase 2 — Seed site, calendar and the Year 1 base.**
- Create `kentender-seed.local` (port 8002) as a copy of dev.
- Add one as-at constant and a "Year 1 = Year 2 − 364 days" shift helper in `kentender_core/seeds`.
- Move site history, responsibility starts (keeping Julia Njeri's acting window and Dr Peter Kimani's Digital Health start in the same relation), rule effective dates and intake windows earlier.
- Parameterise the Budget, Needs and Planning seeds by fiscal year, content set and shift, so one journey builds Year 1 (FY 2026/27, the laptop and infrastructure content, Required by 30 Jun 2027, the D8 baselines) and Year 2 (FY 2027/28, the D10 titles, today's instants).
- Replace the single ladder with `CURRENT` and `NEXT` in `canonical.run/seed/validate/prepare_site` and the Makefile, with per-year validation.
- Settle D3 by running the commands.

**Gate SW-G02:** `CURRENT=annual_plan` validates with each `NEXT` value (none, budget, needs, departmental_plans, annual_plan); a rerun is idempotent; `test_canonical_seed` is green on the seed site.

**Phase 3 — Move the laptop chain to Year 1.**
- Requisitions draw on the FY 2026/27 Plan and reserve against the FY 2026/27 Budget (operational required by 20 Jun 2027).
- Tender, bid submission, opening, evaluation and award keep their actual instants.
- Supplier account starts move before the first Year 1 publication.
- Count and fix every test and spec that assumes FY 2027/28 or a single canonical record; the count is recorded before fixing.

**Gate SW-G03:** `CURRENT=award NEXT=annual_plan` validates. The affected module test files pass on the seed site. Planning reports the laptop Tender 103 days after its approved invitation date.

**Phase 4 — The Year 1 portfolio.**
- Add T2–T11, the requisition awaiting authorisation, the authorised-not-taken-up requisition, the two-department and partial drawdowns, and the matching Plan items.
- Build in stage order, each through the owners' commands as the named actors, each validated at its own state.
- Measure full-run time and peak memory on the seed site and on a fresh-like site (developer mode off, simulation off).

**Gate SW-G04:** every portfolio record is at its target state at the as-at instant; reruns are idempotent; times are recorded.

**Phase 5 — Home and Analytics state check.** Add a validation step that asserts each state named in proposal §5 at the as-at instant, and a binding table from each HOME H-scenario and ANL A1 record to the generated reference that serves it. **Gate SW-G05:** the check is green; the binding table is filed in this folder.

**Phase 6 — Documentation revamp (one task, D11).**
- Write the clean successor: one document replacing SEED-001 and SEED-OPS-001 (D12).
- Write a carry-over register listing every rule in SEED-001 v1.4 and SEED-OPS-001 v1.25 as carried, superseded or dropped, each with a reason, so nothing approved disappears silently.
- Mark the old documents Retired and move them under `20_seed_data/retired/`.
- Update every link (`CLAUDE.md`, `Makefile`, `kentender_core/seeds/README.md`, the register, cross-references in other folders).
- Supply the KT-STD-001 §8.4/§8.4A pointer text for the owner.
- Remove `OPEN=True`; start the one-release `THROUGH` alias.

**Gate SW-G06:** the owner approves the new document; links resolve; `make help` matches.

**Phase 7 — Roll out.**
- Tell the owner, then reseed `kentender.midas.com` and rebuild `kentender-test.local`.
- Tell the module sessions (Home, Analytics and others) what changed: the new references, the as-at instant and the test clock.
- Update memory.

**Gate SW-G07:** both sites validate; the hand-over note is filed.

## Verification

- Python: `bench --site kentender-seed.local run-tests --app kentender_core --module kentender_core.tests.test_canonical_seed`, then the module seed tests a phase touches. Never on dev; never while a Playwright run is active.
- Seeding:

  ```bash
  make seed-canonical SITE=kentender-seed.local CURRENT=… NEXT=…
  make seed-canonical-validate SITE=kentender-seed.local CURRENT=… NEXT=…
  ```

- Browser (Phase 5): the seed site as Charles Mutiso, Amina Hassan, Brian Wafula, Dr Peter Kimani and an anonymous visitor; record what is shown.

## Risks

- The seed run grows several-fold downstream, and the 1 vCPU / 512 MB server may not cope. `CURRENT` caps keep small runs available; Phase 4 measures it.
- Hidden FY 2027/28 and single-record assumptions in tests and specs. Phase 3 counts them first.
- Moving responsibility and rule dates earlier may change what other modules' tests see on the dev site after roll-out. Phase 7 announces it.
- Other sessions' uncommitted work in shared files: commit by hunk, never revert.
- The owner's library may hold later versions of KT-STD-001 or SEED-001 than the repository.

## Build findings

Appended during the build; the phase text above is not rewritten.

- **BF-01 (5 Oct 2026) — no separate seed site.** No database user here can create a database, and nobody has root access (both site users hold privileges on their own database only), so `kentender-seed.local` cannot be made. Every reseed and Python run uses `kentender-test.local` holding both shared locks (`/tmp/kt-test-site.lock`, `/tmp/home-test-site.lock`). The Analytics session agreed to run nothing there until told; the Home session was idle.
- **BF-02 — accepting a Need starts its department's Draft plan by itself** (`dpp_autostart`), unstamped. The planning build now reuses that Draft and stamps it, so `reset` keeps the year's plans as canonical; at `NEXT=needs` the prepared year's Draft plans exist and are expected.
- **BF-03 — a rebuild's usage reversal outranked the rebuilt plan.** The reset marks each Need "Not included" at the real clock (October 2026); the rebuilt Year 1 activation (December 2025, frozen) is older and was ignored. Planning's usage projections now go with their deleted Needs, like the disposition and intake projections.
- **BF-04 — the executed laptops must be delivered inside FY 2026/27.** A Requisition refuses a latest delivery date after the Plan boundary (30 Jun 2027), and a Tender's bid form refuses an offered date after the latest delivery date, so the canonical laptops (awarded 17 Jun) are due by 30 Jun 2027 and the four bids offer 22–30 Jun 2027 (were 10–25 Sep). Accepted under D8, which keeps the actual chain's dates.
- **BF-05 — only off-the-shelf IT equipment can be bought.** Requisitions take nine IT categories; Tenders takes eight (not "Other IT equipment"). The design titles that are not such equipment have IT substitutes: laboratory desktop computers (for laboratory analysers), document scanners (office desks), desktop computers (hospital beds), clinic desktop computers (clinic equipment), wireless access points (IT peripherals), core network routers (servers).
- **BF-06 — the Year 1 budget is KES 290m on four lines** (Digital Health 120m, workforce 60m entity-wide, ministry-wide ICT 80m, HRMD office equipment 30m) so the executed portfolio fits; the 30% reservation is met by the laptops (Youth, 50m) and the routers (Women, 25m) out of 236.5m planned.
- **BF-07 — Award takes a delivered evaluation report up by itself** (the case appears at Opinion with the delivery instant). The portfolio keeps that case for a report whose opinion is pending, and the "site is ahead" check treats a case at Opinion as the evaluation stage's consequence.
- **BF-08 — the Tenders stage's candidate creates a Draft bid** (Start bid), so only a submitted bid marks the bid stage as reached.
- **BF-09 — a rebuild now removes the canonical supplier accounts** (namespace `KENTENDER_MVP_1_R1_BDS`) and the canonical Tenders' bid, opening, evaluation and award rows; accounts register from 1 Mar 2027 (were 18 May–3 Jun) so the portfolio's April bids are authorised.
- **BF-10 — the canonical award stops at Mary Wanjiku's acceptance** (18 Jun 09:00; the waiting period runs). Delivery to Contracting on 2 Jul is after the as-at instant and stays the AWD-DEMO-DELIVERED profile.
- **BF-11 (5 Oct 2026) — story time is ahead of real time, and Needs usage is ordered on event time.** Planning and Departmental Needs stamp a live event with the site clock (October 2026). The seeded FY 2027/28 Plan's usage events are dated 10 Dec 2026, so until real time passes that date a live event on the same Need (a re-publication, a profile, a test) is "older" and ignored. The Needs demo profiles now date their events at the as-at instant, and the Needs contract tests a year ahead. Live use on dev before 10 Dec 2026 still meets this; changing how Needs orders usage events is a module decision, not this plan's. Only Bid Submission, Supplier Accounts, Bid Opening, Bid Evaluation and Award read the site test clock.
- **BF-12 (5 Oct 2026) — a Requisitions demo profile resets only the laptops Requisition.** It used to clear every canonical Requisition, which revoked or refused on the executed portfolio's authorised ones. Only the canonical rebuild clears the portfolio's. The profiles need `CURRENT=requisitions`, because the canonical Tender consumes the laptops handoff on the full world (one-way, by design); their test skips otherwise.
- **BF-13 (5 Oct 2026) — Julia Njeri is no longer acting head "now".** Her acting term is FY 2026/27's planning history (2 Oct–1 Dec 2025); at 18 Jun 2027 Dr Peter Kimani holds Digital Health. Tests that read her as a current reviewer were changed to her dated term; the Home provider's own Needs test (Home session, uncommitted) still reads her as current and is handed over, not changed here.
