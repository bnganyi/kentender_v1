# Two-year seed world: implementation tracker

| Control | Value |
|---|---|
| Plan | `Two_Year_Seed_World_Implementation_Plan.md` (plan.1) |
| Status | **In progress** (hold released 5 October 2026). Phases 0–5 built and checked; Phase 6 documentation proposed (owner approval pending); Phase 7 roll-out done (5 October 2026); SEED-002 approval and the old documents' retirement wait for the owner. |
| Updated | 5 October 2026 |

## Rules

1. A row is **Done** only with evidence: the commands run, the site, the result, and the commit. Narrow passes don't close broader rows.
2. Statuses: **Planned**, **In progress**, **Done**, **Blocked — owner**, **Blocked — dependency**, **On hold**.
3. Each row is updated in the same step as the work it records.
4. Seed reseeds run on `kentender-seed.local` only, until Phase 7 (plan, "Rules for working alongside other sessions").

## Phase 0 — Preparation

| ID | Work | Status | Evidence |
|---|---|---|---|
| SW-0001 | Create `docs/mvp-1-r1/20_seed_data/` | Done | 4 Oct 2026, owner instruction "Create a dedicated seed_data folder". |
| SW-0002 | Move this work's documents into it | Done | 4 Oct 2026: the proposal and corrections files moved from `98_work_progress/`. SEED-001 and SEED-OPS-001 stay in `00_common/` until SW-0601, because files other sessions are editing link to them. |
| SW-0003 | Plan and tracker | Done | 4 Oct 2026: this file and `Two_Year_Seed_World_Implementation_Plan.md`. |
| SW-0004 | Record owner answers verbatim | Done | Plan "Decisions on record" D1–D11. The corrections file carries the "1. Accepted 2. Accepted 3. Accepted" record. |
| SW-0005 | Gate SW-G00 | Done | Files exist; decisions recorded; no code changed. |

## Phase 1 — Decisions and correction text

| ID | Work | Status | Evidence |
|---|---|---|---|
| SW-0101 | Proposal with D1–D7 | Done | Accepted 4 Oct 2026; committed fec5ebba. |
| SW-0102 | Finding: planned dates must fit their own year | Done | Corrections §1, from the three owner checks cited there (source read, nothing run). |
| SW-0103 | Replacement text for KT-STD-001 §8.4/§8.4A and SEED-001 | Done | Corrections §3–§5; committed fec5ebba. |
| SW-0104 | Owner applies the KT-STD-001 §8.4/§8.4A correction in their library | Blocked — owner | Under D12 this becomes a pointer to the new document (SW-0603). |
| SW-0105 | Gate SW-G01 | Done | 4 Oct 2026. |

## Phase 2 — Seed site, calendar and Year 1 base

| ID | Work | Status | Evidence |
|---|---|---|---|
| SW-0201 | Create `kentender-seed.local` (port 8002) as a copy of dev; check whether database permission is needed | Done — not possible | 5 Oct 2026: no database user can create a database and nobody has root (plan BF-01). Seed work runs on `kentender-test.local` under both shared locks; the Analytics session holds off; the Home session was idle. |
| SW-0202 | As-at constant and 364-day shift helper in `kentender_core/seeds` | Done | `kentender_core/seeds/calendar.py`: `AS_AT = 2027-06-18 10:00:00`, `YEAR1` (FY 2026/27, −364 days) and `YEAR2` (FY 2027/28). Committed bedf8a5b. |
| SW-0203 | Site history, responsibility starts (Julia/Peter relation kept), rule effective dates and intakes moved earlier | Done | `site_setup.ASSIGNMENTS`: Julia Njeri acting 2 Oct–1 Dec 2025, Peter Kimani Digital Health from 2 Dec 2025, Directorate from 2 Sep 2025, Samuel Otieno 2 Jan–1 Sep 2025; open-ended grants unchanged; rule windows unchanged (Year 1 resolves by planned invitation and FY start, inside them). Year 1 intakes opened by the Needs and Planning seeds at their own instants. bedf8a5b. |
| SW-0204 | Budget seed parameterised by year; Year 1 (FY 2026/27) and Year 2 (FY 2027/28) | Done | `BUDGETS` per year: Year 1 MOH-FIN-BUD-2026-01, KES 290m on four lines (plan BF-06); Year 2 unchanged. Both validated on the test site. bedf8a5b. |
| SW-0205 | Needs seed parameterised by year and content set; Year 1 laptop/infrastructure content (Required by 30 Jun 2027); Year 2 D10 titles plus the pending workforce-certification Need | Done | `YEAR_NEEDS`: Year 1 NDS-MOH-2026-0001..0003 (infrastructure, HRMD laptops returned and corrected, DHI laptops; required by 30 Jun 2027); Year 2 NDS-MOH-2027-0001..0004 with the D10 titles, 0002 still Submitted for Peter. Validated. bedf8a5b. |
| SW-0206 | Planning seed parameterised; Year 1 baselines per D8; Year 2 at today's instants; Treasury references MOH/APP/2026/001 and MOH/APP/2027/001 | Done | `plan_spec(year)` and `upsert_year_plan`: Year 1 PLN-MOH-2026-001 Active 11 Dec 2025 with 14 items (laptops, infrastructure, 12 portfolio items), Treasury MOH/APP/2026/001; Year 2 PLN-MOH-2027-001 Active 10 Dec 2026, 3 items. Every governance step under the frozen clock. Validated. bedf8a5b. |
| SW-0207 | `CURRENT`/`NEXT` in `canonical.run/seed/validate/prepare_site` and the Makefile; per-year validation | Done | `canonical.resolve_years`, `CURRENT_STAGES`/`NEXT_STAGES`, per-year validation, `THROUGH` alias, `world_ahead` → automatic rebuild; Makefile `CURRENT=`/`NEXT=`. bedf8a5b. |
| SW-0208 | Decide D3 (FY 2025/26) by running the commands | Done — not needed | Every Year 1 command ran with FY 2025/26 absent; no configured closed year is added (D3). |
| SW-0209 | `test_canonical_seed` cases: two ladders, independence, `NEXT` ceiling | Done | `test_canonical_seed`: ladder, alias, calendar, idempotent full world, executed-vs-prepared year, `TestTwoYearLadders` (lower stage rebuilds; higher builds on), all green on the test site except the open-tender case (re-running). |
| SW-0210 | Gate SW-G02: `CURRENT=annual_plan` × each `NEXT` validates; rerun idempotent | Done | 5 Oct 2026: `CURRENT=annual_plan NEXT=annual_plan` (WIPE) validated in 1 min 40 s; `CURRENT=annual_plan NEXT=budget` and `CURRENT=requisitions NEXT=departmental_plans` validated in the ladder test; reruns idempotent. |

## Phase 3 — Laptop chain to Year 1

| ID | Work | Status | Evidence |
|---|---|---|---|
| SW-0301 | Count tests and specs assuming FY 2027/28 or a single canonical record (recorded before fixing) | Done | 5 Oct 2026: 72 candidate files by grep (`working/sw0301_candidate_files_2026-10-05.txt`); 32 seed-adjacent Python files run on the test site (`run_modules`, one at a time under both test-site locks): 21 green, 11 failing. Of the 11: 9 assumed the old world (one year, Julia acting now, Year 2 plan dates, single-item Requisitions reset, profile clocks), 1 was another session's uncommitted Home test (handed over) and 1 predates this work (Bid Submission action register: bid-portal labels added without a register row). |
| SW-0302 | Requisitions against the FY 2026/27 Plan and Budget; operational required by 20 Jun 2027 | Done | The laptops Requisition draws on PLN-MOH-2026-001 and reserves against MOH-BUD-2026-001; latest delivery 30 Jun 2027 (plan BF-04). bedf8a5b. |
| SW-0303 | Tender through Award re-pointed, actual instants unchanged | Done | Tender, bids, opening and evaluation keep their instants; the award stops at the acceptance (plan BF-10). `CURRENT=award` validated. bedf8a5b. |
| SW-0304 | Supplier account starts before the first Year 1 publication | Done | Afya registers 1 Mar 2027, Jirani 2 Mar, Pwani 3 Mar, Mlima 4 Mar (plan BF-09). |
| SW-0305 | Fix the tests and specs counted in SW-0301 | Done (Python) | 5 Oct 2026: fixed and re-run green on the test site — Budget canonical seed (per year), Bid Opening profiles (clock back on the as-at instant), Needs seed (both years), notifications and permissions (Julia's dated term), contracts (events after the story's instants), lifecycle (two seeded years), Planning seed (both Plans' signing instants), Requisitions profiles (skip unless `CURRENT=requisitions`). Seed fixes found on the way: plan BF-11, BF-12, and the portfolio's own opening/evaluation tags (a profile reset no longer removes them). Not run: Vitest/Playwright specs among the 72 candidates (UI-level; left to each module's next UI checkpoint). |
| SW-0306 | Gate SW-G03: full world validates; Planning shows the laptop Tender 103 days late | Done | 5 Oct 2026: `CURRENT=award NEXT=annual_plan` validated on the test site (REBUILD, 1 min 17 s before the portfolio). |

## Phase 4 — Year 1 portfolio

| ID | Work | Status | Evidence |
|---|---|---|---|
| SW-0401 | Plan items and requisitions: awaiting authorisation (Clinic equipment); authorised but not taken up; two-department drawdown; partial drawdown | Done | Twelve portfolio Requisitions through `build_requisition`: Clinic desktop computers Submitted to Procurement; Monitors Authorised and not taken up; Wireless access points across both departments; Network switches a partial draw (25 of 30). 14 reservations, KES 143m, all stamped. bedf8a5b. |
| SW-0402 | T7 (UPS units), T8 (IT peripherals), T9 (field laptops), T10 (hospital beds), T11 (servers): preparation and cancellation states | Done | `build_tender`: T7 UPS units Approved; T8 Wireless access points returned (warranty); T9 Field laptops cancellation recommended; T10 Desktop computers cancelled, evidence pending; T11 Core network routers cancelled, all six obligations evidenced. bedf8a5b. |
| SW-0403 | T6 (medical-grade tablets): open, clarifications, opening upcoming | Done | T6 Medical-grade tablets published 24 May, deadline 25 Jun; four candidate Drafts; six unanswered clarifications; opening committee appointed 15 Jun (Start opening upcoming). bedf8a5b. |
| SW-0404 | T5 (network switches): opening complete, no committee | Done | T5 Network switches: two bids, opening complete 14 Jun, evaluation prepared, committee not appointed. bedf8a5b. |
| SW-0405 | T4 (office desks): committee review | Done | T4 Document scanners: two bids, opening 3 Jun, taken up — committee review outstanding. bedf8a5b. |
| SW-0406 | T2 (printers), T3 (hospital laboratory analysers): award stage | Done | T2 Printers: report delivered 16 Jun 11:30, opinion pending; T3 Laboratory desktop computers: report 4 Jun 15:00, opinion signed 17 Jun 16:00, decision pending. bedf8a5b. |
| SW-0407 | Run time and peak memory, seed site and fresh-like site | Done (test site) | 5 Oct 2026 on kentender-test.local: stage by stage — requisitions 45 s (with rebuild), tenders 1 min 42 s (rebuild), bids 2 min 52 s (rebuild), openings 21 s, evaluations 16 s, awards 5 s; the ladder test's rebuild to the base 31 s; a full REBUILD under 8 min 25 s (that figure includes waiting for the shared lock). Peak memory not measured; the small 1 vCPU / 512 MB server not tried (owner-gated roll-out). |
| SW-0408 | Tell the owner or Home session that the portfolio replaces HOME plan Phase 7's fixture worlds | Done | 5 Oct 2026: in the closing report to the owner (the Home session is paused until the seed is done, owner 5 Oct). Hand-over includes the Home session's own Needs Home test, which still reads Julia Njeri as acting head (plan BF-13). |
| SW-0409 | Gate SW-G04 | Done | Every portfolio record at its target state at the as-at instant (`portfolio.validate_portfolio`); a second full run idempotent (`test_a_second_full_run_changes_nothing`). |

## Phase 5 — Home and Analytics state check

| ID | Work | Status | Evidence |
|---|---|---|---|
| SW-0501 | Validation step asserting every proposal §5 state at the as-at instant | Done | `portfolio.validate_portfolio(current=…)` runs inside `canonical.validate`: Requisition state, Tender status, bids, candidates and clarifications, opening, evaluation and award stage per record. |
| SW-0502 | Binding table: HOME H-scenarios and ANL A1 records to generated references | Done | 5 Oct 2026: generated by `portfolio.binding_rows()` on the test site into SEED-002 Appendix B, with the T9 note (no AO cancellation task, a Tenders gap). |
| SW-0503 | Browser check as Charles, Amina, Brian, Peter and an anonymous visitor | Done (service level) | 5 Oct 2026: My Work read for each person on the test site — Charles 11 items (authorise REQ-MOH-2026-008-001, six T6 clarifications, T6 opening, T5 secretary, T2 opinion), Amina 3 (authorise T7 publication, appoint T5 committee, decide T3 award), Brian 9, Peter 1 (the Year 2 certification Need), Grace waiting 1, Mercy none; anonymous `/tenders` lists T6 and T9. Not seen: Amina's T9 "Consider cancellation" (Tenders gap, SEED-002 Appendix B). Page-level browser walk left to the Home and Analytics sessions on their pages. |
| SW-0504 | Gate SW-G05 | Done | 5 Oct 2026: full world validates on the test site; every portfolio state at the as-at instant (`validate_portfolio`); binding table generated; work lists read per person. Open: the Tenders AO cancellation-task gap (reported to the owner). |

## Phase 6 — Documentation revamp

| ID | Work | Status | Evidence |
|---|---|---|---|
| SW-0600 | OQ-1: one document replacing SEED-001 and SEED-OPS-001? | Done | Owner, 4 Oct 2026: "one new document to replace both the fixture document and the runbook". Plan D12. |
| SW-0601 | One clean successor document in this folder, replacing SEED-001 and SEED-OPS-001 (D12) | Done — proposed | `KenTender_SEED-002_Canonical_Seed_World_v0_1.md`: Part A the world, Part B how to seed it, Part C how a module adds to it; Appendix B binding table; Appendix D new content and questions. Owner approval pending. |
| SW-0602 | Carry-over register: every SEED-001 v1.4 and SEED-OPS-001 v1.25 rule carried, superseded or dropped, each with a reason | Done | SEED-002 Appendix A: every SEED-001 v1.4 and SEED-OPS-001 v1.25 rule carried, superseded or dropped, each with a reason. |
| SW-0603 | KT-STD-001 §8.4/§8.4A pointer text for the owner | Done | SEED-002 Appendix C: the replacement text for KT-STD-001 §8.4/§8.4A and the dated §8.3 terms. |
| SW-0604 | Retire the old documents to `20_seed_data/retired/`; update every link and the register | On hold | — |
| SW-0605 | Remove `OPEN=True`; one-release `THROUGH` alias | Done | 5 Oct 2026: `OPEN=True` removed from `canonical.py`, the Tenders and Bid Submission seeds, the Makefile and the tests (the portfolio's tablets Tender is open past the as-at instant; `test_the_open_portfolio_tender_is_listed_for_anyone`). `THROUGH` maps onto CURRENT/NEXT with a notice (`resolve_years`). |
| SW-0606 | Gate SW-G06: owner approval; links resolve | On hold | — |

## Phase 7 — Roll out

| ID | Work | Status | Evidence |
|---|---|---|---|
| SW-0701 | Tell the owner; reseed `kentender.midas.com`; rebuild `kentender-test.local` | Done | 5 Oct 2026: dev migrated (Analytics page installed; sidebar exports backed up, the one timestamp-only rewrite of `procurement.json` restored) and rebuilt — `REBUILD=True`, validates, 3 min 38 s, clock 18 Jun 2027 10:00; test site reseeded and validated, same clock; both sites carry identical generated references. Owner told in the closing report. |
| SW-0702 | Hand-over note to module sessions (references, as-at instant, test clock) | Done | 5 Oct 2026: sent to the Analytics session (ANL8-0701–0712 runnable; binding table location; usage-ordering, T9 task gap, portfolio tags, Julia's term). Home is paused: its notes go through the owner (SW-0408). |
| SW-0703 | Memory updated | Done | 5 Oct 2026. |
| SW-0704 | Gate SW-G07 | Done (owner items open) | Rolled out to dev and the test site. Owner-gated and still open: SEED-002 approval (SW-0606), retiring the old documents (SW-0604), the KT-STD-001 correction (SW-0104). |
