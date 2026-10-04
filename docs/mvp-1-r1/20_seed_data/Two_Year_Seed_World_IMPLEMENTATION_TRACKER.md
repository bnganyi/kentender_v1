# Two-year seed world: implementation tracker

| Control | Value |
|---|---|
| Plan | `Two_Year_Seed_World_Implementation_Plan.md` (plan.1) |
| Status | **On hold** (owner, 4 October 2026). Phases 0 and 1 are done; Phase 2 waits for the owner to release the hold. |
| Updated | 4 October 2026 |

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
| SW-0201 | Create `kentender-seed.local` (port 8002) as a copy of dev; check whether database permission is needed | On hold | — |
| SW-0202 | As-at constant and 364-day shift helper in `kentender_core/seeds` | On hold | — |
| SW-0203 | Site history, responsibility starts (Julia/Peter relation kept), rule effective dates and intakes moved earlier | On hold | — |
| SW-0204 | Budget seed parameterised by year; Year 1 (FY 2026/27) and Year 2 (FY 2027/28) | On hold | — |
| SW-0205 | Needs seed parameterised by year and content set; Year 1 laptop/infrastructure content (Required by 30 Jun 2027); Year 2 D10 titles plus the pending workforce-certification Need | On hold | — |
| SW-0206 | Planning seed parameterised; Year 1 baselines per D8; Year 2 at today's instants; Treasury references MOH/APP/2026/001 and MOH/APP/2027/001 | On hold | — |
| SW-0207 | `CURRENT`/`NEXT` in `canonical.run/seed/validate/prepare_site` and the Makefile; per-year validation | On hold | — |
| SW-0208 | Decide D3 (FY 2025/26) by running the commands | On hold | — |
| SW-0209 | `test_canonical_seed` cases: two ladders, independence, `NEXT` ceiling | On hold | — |
| SW-0210 | Gate SW-G02: `CURRENT=annual_plan` × each `NEXT` validates; rerun idempotent | On hold | — |

## Phase 3 — Laptop chain to Year 1

| ID | Work | Status | Evidence |
|---|---|---|---|
| SW-0301 | Count tests and specs assuming FY 2027/28 or a single canonical record (recorded before fixing) | On hold | — |
| SW-0302 | Requisitions against the FY 2026/27 Plan and Budget; operational required by 20 Jun 2027 | On hold | — |
| SW-0303 | Tender through Award re-pointed, actual instants unchanged | On hold | — |
| SW-0304 | Supplier account starts before the first Year 1 publication | On hold | — |
| SW-0305 | Fix the tests and specs counted in SW-0301 | On hold | — |
| SW-0306 | Gate SW-G03: full world validates; Planning shows the laptop Tender 103 days late | On hold | — |

## Phase 4 — Year 1 portfolio

| ID | Work | Status | Evidence |
|---|---|---|---|
| SW-0401 | Plan items and requisitions: awaiting authorisation (Clinic equipment); authorised but not taken up; two-department drawdown; partial drawdown | On hold | — |
| SW-0402 | T7 (UPS units), T8 (IT peripherals), T9 (field laptops), T10 (hospital beds), T11 (servers): preparation and cancellation states | On hold | — |
| SW-0403 | T6 (medical-grade tablets): open, clarifications, opening upcoming | On hold | — |
| SW-0404 | T5 (network switches): opening complete, no committee | On hold | — |
| SW-0405 | T4 (office desks): committee review | On hold | — |
| SW-0406 | T2 (printers), T3 (hospital laboratory analysers): award stage | On hold | — |
| SW-0407 | Run time and peak memory, seed site and fresh-like site | On hold | — |
| SW-0408 | Tell the owner or Home session that the portfolio replaces HOME plan Phase 7's fixture worlds | On hold | Due before SW-0401 starts. |
| SW-0409 | Gate SW-G04 | On hold | — |

## Phase 5 — Home and Analytics state check

| ID | Work | Status | Evidence |
|---|---|---|---|
| SW-0501 | Validation step asserting every proposal §5 state at the as-at instant | On hold | — |
| SW-0502 | Binding table: HOME H-scenarios and ANL A1 records to generated references | On hold | — |
| SW-0503 | Browser check as Charles, Amina, Brian, Peter and an anonymous visitor | On hold | — |
| SW-0504 | Gate SW-G05 | On hold | — |

## Phase 6 — Documentation revamp

| ID | Work | Status | Evidence |
|---|---|---|---|
| SW-0600 | OQ-1: one document replacing SEED-001 and SEED-OPS-001? | Done | Owner, 4 Oct 2026: "one new document to replace both the fixture document and the runbook". Plan D12. |
| SW-0601 | One clean successor document in this folder, replacing SEED-001 and SEED-OPS-001 (D12) | On hold | — |
| SW-0602 | Carry-over register: every SEED-001 v1.4 and SEED-OPS-001 v1.25 rule carried, superseded or dropped, each with a reason | On hold | — |
| SW-0603 | KT-STD-001 §8.4/§8.4A pointer text for the owner | On hold | — |
| SW-0604 | Retire the old documents to `20_seed_data/retired/`; update every link and the register | On hold | — |
| SW-0605 | Remove `OPEN=True`; one-release `THROUGH` alias | On hold | — |
| SW-0606 | Gate SW-G06: owner approval; links resolve | On hold | — |

## Phase 7 — Roll out

| ID | Work | Status | Evidence |
|---|---|---|---|
| SW-0701 | Tell the owner; reseed `kentender.midas.com`; rebuild `kentender-test.local` | On hold | — |
| SW-0702 | Hand-over note to module sessions (references, as-at instant, test clock) | On hold | — |
| SW-0703 | Memory updated | On hold | — |
| SW-0704 | Gate SW-G07 | On hold | — |
