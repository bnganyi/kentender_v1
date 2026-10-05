# ANL-CHG-001 v0.8: Procurement Analytics, tracker

| Control | Value |
|---|---|
| Version | 0.8-tracker.1 |
| Date | 5 October 2026 |
| Status | Built and verified on the test site, 5 October 2026, including the real-data walk on the two-year seed world (Phase 7). Phases 1, 2, 4, 6 and most of 7 done; Phases 0, 3, 5 and 8 have Partial rows (listed below); most of Phase 9 is `Blocked — owner`. The seed session migrated the dev site; this session ran nothing on dev. Nothing committed. |

**Authority:** `KenTender_ANL-CHG-001_Procurement_Analytics_v0_8.md`, *Approved — 4 October 2026*. Governing standard: KT-STD-001 v1.22.

**Plan:** `ANL-CHG-001_v0_8_Implementation_Plan.md`. It holds owner decisions OD-0 to OD-2, technical decisions D1–D15 and conflicts C1–C14.

**Companions:** `ANL-CHG-001_v0_8_FOLLOW_UPS.md`; Phase 0 `reconciliation/`; later `evidence/v0_8/`.

**Design:** `design/Analytics/Analytics.dc.html` (index) and five board files (22 boards), design system `design/_ds/kentender-industry-82d82607-…`.

**Started:** 5 October 2026. **Built:** 5 October 2026 (same day), by the lead with five delegated builders: Needs and Planning, Requisitions and Budget, Opening/Evaluation/Award facts, Tenders, and the page.

## Tracker rules

1. **Rows are permanent.** Status vocabulary: `Planned` / `In progress` / `Blocked` / `Blocked — owner` / `Partial` / `Done`. Reversed decisions are struck through in place, never deleted.
2. **`Done` needs the row's own evidence:** a command with result counts, a named test, a commit, or a described browser observation with the literal rendered strings. Never record a result that was not observed. A passing narrow test does not close a row whose acceptance criterion is broader.
3. **A UI row closes only after the live check** on the running site, as the named persona, from the sidebar, not by address alone. Record "tested by address" otherwise.
4. **Test site only.** Python and browser tests run on `kentender-test.local` through `scripts/test-site.sh`. Never run Python tests while a Playwright process is active. Check `make ui-queue-check` before reading code on an odd UI failure.
5. **Reads create nothing.** A row is not Done if loading, paging, filtering, retrying or navigating creates a business event, a stored measure, a working-context preference or a notification (ANL §16; FU-ANL-16).
6. **No stored field and no owner workflow change.** An owner projection reshapes existing owner data; it adds no task, decision, DocType or stored business field. Any storage need is a follow-up with owner sign-off before it is built.
7. **Approved documents are not edited.** A defect found in a filed document is a row in the follow-ups file. Document changes (owner amendments, register entries, a seed runbook) follow the kentender-document-change protocol, and the latest version is checked first.
8. **Cross-app callers.** Before reshaping a hook, route, sidebar item or role tuple, grep the whole repository for real callers, not only the owning module (the Analytics sidebar item, `PLANNED_SIDEBAR_LABELS`, `kt_home_providers`, `kt_tender_stage_summaries`, `Home.spec.js`).
9. **Design gates.** No UI row (Phase 5 onward) is Done before Gate ANL-G04. Home's repo-wide design-system adoption (Phase 1B) stays on hold and blocks nothing here.
10. **Measures, counts and labels are server-made.** A row is not Done if the browser computes a count, band, month bucket, median, percentage, amount or label from rows or from a page of rows (ANL §16).
11. **Disclosure is tested end to end** through the real endpoint as the real persona (Charles Mutiso, Amina Hassan, Dr Peter Kimani, Daniel Otieno, Nadia Kamau), with a negative case, including revoked scope. A masked record contributes to no figure.
12. **Narrow then broad.** Red then green on one test, the module tests once, then broaden only at a gate. Other modules' tests are re-run only when a dependency they use changed (Home providers when a shared helper changes).
13. **Fixtures clean up.** Every test module registers a purge cleanup; browser-pass records count as test data. Build worlds once per module, not per test. Reseed the canonical world after a run that persists.
14. **Deferred and owner-gated scope stays that way.** Rows marked `Blocked — owner` (Phase 7, Phase 9, rows 0228 and 0808) count toward no readiness claim.
15. **Report exactly what was and was not run.** Never claim a result that was not observed. Flag any migrate, patch or seed need immediately and state dev's real state at the end of every task.
16. **Commits only when the owner asks, and only Analytics' own files.** The working tree carries other changes (Home, OVS, Budget, Requisitions, Award, Evaluation); do not stage or revert them.
17. **No forecast, trend, savings, utilisation percentage, health or risk score, overdue claim or sum of different kinds of amount** appears in any response or board (ANL-AC-24).

## Decision log

| Date | Decision | Rationale |
|---|---|---|
| 4 Oct 2026 | OD-0: approval. Owner answer, verbatim: "Yes", to "Shall I apply this pass, and then approve KT-STD v1.22, HOME v0.6 and ANL v0.8 together?" (ANL v0.8 §18.0C). | ANL v0.8 §10A is the design input. Approval is not evidence of implementation, owner-read readiness, seed, testing or production readiness. |
| 5 Oct 2026 | Owner instruction, verbatim: "Read the contents in \19_analytics and any related latest docment versions and prepare and implementation plan and tracker". | Produces this plan, tracker and follow-ups (row ANL8-0001). No code in this step. |
| 5 Oct 2026 | OD-1: test data. Owner answer: "Wait for the two-year seed world". | Server tests prove figures on a synthetic world; browser verification on realistic data waits for the seed world's Phase 5. The seed work is on hold (owner, 4 Oct 2026). Phase 7 rows are `Blocked — owner`. |
| 5 Oct 2026 | OD-2: who sees what. Owner answer: "Match the pictures with aggregate-only reads (Recommended)". | Each owner adds an Analytics read for the site-wide audience returning counts, values and instants, never documents. Widens aggregate disclosure; owner documents need amendment (FU-ANL-01 to 08; row ANL8-0901). |
| 5 Oct 2026 | Build interpretation recorded for the owner, not a decision: coverage uses Planning's U14 drawdown basis, not the `ProceedingCoverage` table (plan D6; C1). | ANL-M-07 says "the same facts PLN shows in U14"; PLN v1.29 §5.4.6 and the A1 fixture agree. PLN confirms (FU-ANL-02). |
| 5 Oct 2026 | Build interpretation recorded for the owner, not a decision: the award amount is `submitted_amount` (C6). | `letters.py` uses it and A1 implies it. AWD confirms (FU-ANL-07; row 0904). |
| 5 Oct 2026 | Build interpretation recorded for the owner, not a decision: the board's local data palette is used (C9). | The owner accepted the rendered boards (D-ANL-14); palette approval stays open (FU-ANL-10; row 0902). |
| 5 Oct 2026 | Build interpretation: charts are hand-built SVG/CSS components; no library and no `frappe-ui` (D8; FU-ANL-19). | None exists in the repository and CLAUDE.md requires explicit approval for `frappe-ui`. |
| 5 Oct 2026 | Owner instruction, verbatim: "1. Confirmed 2. HOD has to have budget visibility 3. Yes  Also: Proceed until completion as I will not prompt you again. Once done, send a message to the seed building session to begin - it is waiting with a ready plan". | Item 1 confirms the plan's three build interpretations (coverage basis, `submitted_amount`, the board's palette). Item 2 decides row 0228: the Head of User Department gets the department funding view, built as the Analytics aggregate only (no Budget read added; OVS v0.6 §4.1 BUD approves exactly that read). Item 3 confirms Home's Phase 1B stays on hold. The build ran to completion on the test site; the seed session is told when it ends. |
| 5 Oct 2026 | Build decision: department-limited readers get no Award notice, opinion or deliberation matter (OVS v0.6 §4.1 AWD, OVS-P03), which differs from ANL-DES-30's notice row. | A secure default under an approved OVS boundary; the owner confirms which governs (conflicts C22, FU-ANL-26). |
| 5 Oct 2026 | Build decision: site-wide readers see no Drafts; a Draft appears only to the department that contributes to it. | Analytics counts submitted work (conflicts C21). |
| 5 Oct 2026 | Build decision: the Head of User Department gets department-scoped plan items (ANL-AC-07), a new Planning aggregate read. | OD-2, "match the pictures" (conflicts C18). |
| 5 Oct 2026 | Build decision found on the seed world: an invalid or unpermitted `fy`, `dept` or `state` shows the §8 message and the valid parts of the selection and draws no figure. | The page first drew All-years figures beside the message; ANL-AC-13 says an invalid value "never widens the selection" (conflicts C25, FU-ANL-29). The owner may prefer the looser reading of §9.1 ("never widens silently"). |

## Gate register

| Gate | Condition | Status | Evidence |
|---|---|---|---|
| ANL-G00 | Reconciliation files exist; every follow-up cited exists; route spike answered; no product code written | Partial | Rows 0005, 0009, 0010 Partial (see rows) |
| ANL-G01 | Core measure engine suite green on the test site; reads create nothing | Done | 5 Oct 2026, row 0116: 87 core tests OK |
| ANL-G02A | Needs, Departmental planning, Annual planning projections: tests and persona negatives pass; callers audited | Done | 5 Oct 2026, row 0210: NDS 13, PLN 27 OK. Persona negatives are provider-level |
| ANL-G02B | Requisitions and Budget projections: same | Done | 5 Oct 2026, row 0231: REQ 31, BUD 22 OK |
| ANL-G02C | Tenders, Opening, Evaluation, Award projections: same | Done | 5 Oct 2026, row 0252: TPR 38 + 25, BOP 9, EVL 13, AWD 17 OK |
| ANL-G03 | Endpoint suite green; A1, A2, A3 worlds prove ANL-AC-01 to 08 and 14 to 24; conformance gate registered | Partial | Rows 0305, 0306, 0308, 0309 Partial: fact-level worlds, conformance suite blocked by unrelated failures |
| ANL-G04 | Scoped design system and chart components match the board's computed styles | Done | 5 Oct 2026, row 0412: Chromium computed-style and pixel comparison, 0 differences |
| ANL-G05 | Page shell: component tests, first paint and one interactive re-render verified by address | Partial | 5 Oct 2026: 202 component tests; every tab seen live on the seed world; boards 31A–31G, 29F and 30B by tests only |
| ANL-G06 | `/app/analytics` opens from the sidebar; planned-label guards updated; Home link switched; migrate flagged | Done | 5 Oct 2026, row 0607: opened from the sidebar as Charles, Peter and Amina on the test site; dev not migrated |
| ANL-G07 | Real data through the page for every persona; direct load, refresh, Back, shared link, forced failure, clean console | Partial | 5 Oct 2026, `evidence/v0_8/seed_world_walk.md`: rows 0701–0709 and 0711 Done; per-region failure not forced live (0710) |
| ANL-G08 | Fidelity gate over 22 boards, keyboard and 200% zoom, production build, persona pass, acceptance map closed | Partial | Fidelity gate Done (50 tests); keyboard, zoom, build and persona rows Partial; acceptance map 15 Done, 13 Partial |

## Phase tables

### Phase 0: Reconcile (documents plus one browser spike)

Gate ANL-G00. No product code.

| ID | Deliverable | Done when | Status | Evidence |
|---|---|---|---|---|
| ANL8-0001 | File the plan, tracker and follow-ups in `19_analytics/` | Three files exist; format matches the Home set | Done | 5 Oct 2026: three files filed; spec counts and A1 arithmetic recomputed (follow-ups §5). |
| ANL8-0002 | Route spike: `fy`, `dept`, `state` pushed, then Back, refresh and a shared link, in a real browser on the test site (FU-ANL-14) | `reconciliation/route_spike.md` records the observed behaviour with the literal URLs; adapter design confirmed or simplified | Done | 5 Oct 2026, `reconciliation/route_spike.md`: real Chromium on the test site; `set_route` drops the query; own `history.pushState` under `/desk/` plus `frappe.router.route()` keeps it through Back, Forward and reload; `route_options` keeps stale keys, so the page reads `location.search`. |
| ANL8-0003 | Live-site slug check for `analytics`: Page, Workspace, Desktop Icon and Workspace Sidebar records, read-only (FU-ANL-14) | `route_spike.md` records the query and result; no collision, or a named fix | Done | 5 Oct 2026, `route_spike.md`: read-only queries on the test site, no Page, Workspace, Desktop Icon, Workspace Sidebar, DocType or Module Def named for `analytics`. The dev site itself was not queried. |
| ANL8-0004 | `measure_owner_matrix.md`: ANL-M-01 to M-11 and T1–T5, each with owner, existing read, gap and the field-name mapping (for example `requisition_handoff_id` to `requisition_handoff`) | 16 rows, every cell cites a file and line re-opened for the row | Done | `reconciliation/measure_owner_matrix.md` (16 rows, written after the providers were built). |
| ANL8-0005 | `board_vs_spec.md`: all 22 boards read against ANL §10A text, including the local palette override, the Waiting-n-days badge, the narrow-sheet rule and ANL-DES-21's first-view rule | 22 boards compared; every difference is a registry entry with an authority; markup read, not assumed | Partial | `reconciliation/page_needs.md`, the fidelity gate (50 tests, 22 boards) and the 5 Oct real-data walk record every board difference. A separate line-by-line comparison of board text against ANL §10A text was not run; the page's literal-string tests assert the spec strings. |
| ANL8-0006 | `conflicts.md`: C1–C14 of the plan with evidence and disposition | Each conflict has a quoted source on both sides | Done | `reconciliation/conflicts.md`: C1–C24. |
| ANL8-0007 | `ac_map.md`: ANL-AC-01 to 28 verbatim, each on tracker rows | 28 rows, none missing (script-checked against the spec) | Done | `reconciliation/ac_map.md`: 28 rows copied from ANL §14 by script. |
| ANL8-0008 | `hook_inventory.md`: every caller of the Analytics sidebar item, `PLANNED_SIDEBAR_LABELS`, the Home D7 link, `Home.spec.js` and any `analytics` string (FU-ANL-22) | Repository-wide grep recorded with counts | Done | `reconciliation/hook_inventory.md`: repository-wide search before the sidebar change. |
| ANL8-0009 | Read in full the owner sections ANL §7.1 relies on (PLN v1.29 §§4.4, 4.6, 4.8, 5.4.6, 5.5.1A, 10.13; REQ v1.14 §§5.2–5.13, 7.1; BUD v1.12 §§4.8, 4.9, 5, 7, 9.1; TPR v0.17 §4.1, §4.10; BOP v0.11 §5; EVL v0.5 §5.5, §5.7; AWD v0.5 §4, §5.3; NDS v1.16 §4.5) and OVS v0.6 §4.1 and §4.2 (FU-ANL-09) | Read list recorded (read in full, in part, not read); OVS read-fit answered | Partial | OVS v0.6 §4.1 and §4.2 read in full (C14, C22). The other owner documents were not read in full; their rules were taken from ANL §7.1 and §17.1 and checked against code by the provider agents. |
| ANL8-0010 | `make analytics-preflight`: refuses while a Playwright run is active, like `home-preflight` | Target exists and refuses in a test with Playwright running | Partial | `make analytics-preflight` exists and mirrors `home-preflight`; its refusal was not exercised with a Playwright run active. |
| ANL8-0011 | Gate ANL-G00 | Reconciliation files exist, every follow-up cited exists, spike answered, no product code written | Partial | Rows 0005, 0009 and 0010 are Partial; every other Phase 0 row is Done and no product code was written before the spike. |

### Phase 1: Core measure engine (horizontal, server, fake providers first)

Gate ANL-G01. Red first for every row. All rows in `kentender_core`.

| ID | Deliverable | Done when | Status | Evidence |
|---|---|---|---|---|
| ANL8-0101 | Envelope: per-measure value or series, unit, owner read time, completeness (complete, incomplete, unavailable), window bounds; a failed provider is never zero | Fake-provider tests for each verdict and for partial provider sets (ANL-AC-23) | Done | `test_analytics_workspace`: all-fail, one-area, measure-unavailable, incomplete and identity-incomplete branches (50 tests, OK). |
| ANL8-0102 | Twelve-month window ending with the read month in site time; current month labelled `to date`; unaffected by Financial year and Department | Tests at a month boundary and across years (ANL-AC-16) | Done | `test_analytics_measures` window tests (month boundary, year crossing, inclusive ends); `test_filtering_to_the_year_keeps_every_count_and_the_window`. |
| ANL8-0103 | Waiting bands 0–7, 8–30, 31–90, Over 90 from the owner's `since`; never called late, overdue or at risk | Boundary tests at 7, 8, 30, 31, 90, 91 days (ANL-AC-17) | Done | `test_band_boundaries` at 0, 7, 8, 30, 31, 90, 91; A1 waiting rows reproduced. |
| ANL8-0104 | Month buckets with twelve slots and zero months kept | Tests for empty and partly filled series | Done | `test_month_counts_and_empty_months`; A1 monthly series (Published Apr 4, May 1). |
| ANL8-0105 | Shared non-negative calendar-day helper (site-timezone dates; not `home_time._days`, which is signed and private) | Tests across midnight, DST-free site zone and equal dates (FU-ANL-17) | Done | `calendar_days` tests: midnight, same day, refusal of an end before the start. |
| ANL8-0106 | Median, shortest and longest; one decimal only when it ends in .5; the no-completed-steps case | A1 T1 gives 8.5; even and odd counts; empty set (ANL-AC-15) | Done | `test_median_odd_even_and_half`: 8.5, 3.5, 26, 32.5 and a whole mean without a decimal. |
| ANL8-0107 | Coverage percentage: Covered ÷ Planned × 100, half up, whole number; no percentage when planned is zero, unavailable, or either figure is incomplete | A1 gives 81, Digital Health 74, HRMD 96; each no-percentage case (ANL-AC-18) | Done | 81, 74 and 96; half-up cases; zero planned; incomplete read withholds the percentage. |
| ANL8-0108 | Core KES formatter per ANL §5.5 rule 1 (cents only when non-zero; axis ticks may abbreviate millions, labels never) | `KES 55,500,000`, `KES 7,185,000.50`, `KES 20 m` tick; no float anywhere (FU-ANL-17) | Done | `test_kes_shows_cents_only_when_not_zero`; `KES 20 m` tick; owner amounts parsed with `Decimal`. |
| ANL8-0109 | Department attribution: share values and the "share of" secondary text; no department total of award amounts | Tests for IT peripherals 4,000,000 and 2,500,000 splits | Done | A2 tests: `HRMD share of KES 6,500,000`, contributes line, no department total of award amounts. |
| ANL8-0110 | Route-state validation: invalid or unpermitted `fy`, `dept`, `state` give the §8 message, keep valid parts, never widen | One test per invalid value (ANL-AC-13) | Done | `test_invalid_filters_keep_the_valid_parts_and_never_widen`: fy, dept, state, tab. |
| ANL8-0111 | Opaque paging cursor over a bounded owner revision set; counts independent of page size; ten rows | Test with 23 synthetic rows; list changing between pages neither repeats nor skips (ANL-AC-09) | Done | `test_paging_beyond_ten_rows_is_stable`: 23 rows, 10/10/3, stable cursor. |
| ANL8-0112 | Funding-position audience rule: one Financial year selected, whole-Budget or department view, technical readers, no region and no message outside the audience | Matrix test over every role and filter combination (ANL-AC-21, 25) | Done | Core: whole-budget, department and no-region cases; owners decide the audience: BUD provider tests (22) cover every role. |
| ANL8-0113 | Award-amount rule: current committed decision only; superseded adds nothing; no amount from a summary without one | Tests for superseded, return-for-correction, no-award and HoD summary (ANL-AC-20) | Done | Core outcome cell and note; AWD facts tests (17): current committed only, superseded none, Head of User Department no amount. |
| ANL8-0114 | Analytics technical-reader helper: Administrator, System Manager, Technical Operator read every tab site-wide, no action (FU-ANL-18) | Test for each of the three; existing `is_technical` functions unchanged (ANL-AC-27) | Done | Providers use `home_viewer.is_technical_reader`; persona pass: Daniel Otieno's strip equals Charles's. |
| ANL8-0115 | Reads create nothing: no row, no context preference, no notification (FU-ANL-16) | Row-count test before and after a full read | Done | `test_analytics_reads_create_nothing` (2 tests): seven people, every tab, search and filter; 16 tables unchanged, no working-context preference. |
| ANL8-0116 | Gate ANL-G01 | Core suite green on `kentender-test.local`; reads create nothing | Done | 5 Oct 2026: `test_analytics_measures` 18, `test_analytics_workspace` 50, `test_analytics_design_scope` 17, `test_analytics_reads_create_nothing` 2, all OK. |

### Phase 2A: Owner projections — Needs, Departmental planning, Annual planning

Gate ANL-G02A. Each row: owner-guard tests first, then provider, then hook registration. Owner files change additively only.

| ID | Deliverable | Done when | Status | Evidence |
|---|---|---|---|---|
| ANL8-0201 | NDS: first-acceptance instant per permitted Need (FU-ANL-01) | Provider returns the `Accept for planning` instant once per Need; successor acceptance not counted as first | Done | NDS provider test (13 OK): first acceptance only; `Accept successor` not counted. |
| ANL8-0202 | PLN: departmental plan acceptance instants (FU-ANL-02) | Provider returns `decided_at` of each Accept decision; no write to the plan | Done | PLN provider test (27 OK): latest Accept decision instant. |
| ANL8-0203 | PLN: Active Version stable item values and allocation amounts by source department | Planned value 68,500,000 on the A1 world; candidate Version disclosed separately (ANL-AC-03) | Done | PLN: Active Version items only, Decimal allocations, combined two-department item, candidate Version excluded, no Active Version gives no records. |
| ANL8-0204 | PLN: coverage on the U14 basis (authorised Requisition drawdown by allocation), fully, partly and not covered per item (FU-ANL-02a) | A1: covered 55,500,000, items 5/1/1 (ANL-AC-18) | Done | PLN: coverage from authorised drawdown, reversed drawdown covers nothing; the `ProceedingCoverage` table is not used (C1, owner confirmed). |
| ANL8-0205 | PLN: invitation baseline lateness per proceeding in bulk; missing actual is `No date recorded`, never zero | A1: 25, 7, 7, 0, −3 and a blank (ANL-AC-22) | Done | PLN: invitation days from the baseline of the Plan Version the actual was recorded against; none gives `No date recorded`; `has_proceeding` means an authorised drawdown exists. |
| ANL8-0206 | PLN: aggregate-only audience for the site-wide readers (OD-2) | Charles and Amina get counts and values, never a document; a department reader still sees only the department | Done | PLN: Head of Procurement Function, Accounting Officer, Auditor and technical readers get the aggregate; Finance and Statutory Approver plan items only. |
| ANL8-0207 | NDS: current disposition, pending-successor flag and aggregate audience (FU-ANL-01) | Accepted baseline and pending successor count once; AO and HoPF reach the aggregate | Done | NDS: disposition, guarded `pending_successor`; Draft and Withdrawn excluded; AO and HoPF aggregate. |
| ANL8-0208 | Persona negative cases for 2A through the real endpoint, including revoked scope | Each negative returns nothing it should not | Done | Provider-level persona negatives with real users (author, HoD, planner, unrelated, Guest, revoked scope). Not driven through the HTTP endpoint. |
| ANL8-0209 | Repository-wide caller grep for every hook or function touched in 2A | Counts recorded | Done | Additive only: no existing function changed; the module architecture, static-scan, contract and permission suites still pass. |
| ANL8-0210 | Gate ANL-G02A | Rows 0201–0209 Done; owner module tests green once | Done | 5 Oct 2026: NDS 13, PLN 27 OK on the test site. |

### Phase 2B: Owner projections — Requisitions, Budget

Gate ANL-G02B.

| ID | Deliverable | Done when | Status | Evidence |
|---|---|---|---|---|
| ANL8-0221 | REQ: drawdown values by current Version state and contributing department, parsed from Data strings to Decimal (FU-ANL-03) | A1: 12,000,000 requested; 55,500,000 authorised; draft, withdrawn, revoked, returned contribute no value (ANL-AC-19) | Done | REQ provider test (31 OK): values by state and department, `Returned` successor reading, A1 two-line drawdown. |
| ANL8-0222 | REQ: submission, authorisation and handoff-consumption instants of the authorised Version | T1 and T2 inputs for the six authorised A1 Requisitions; returned earlier Versions not added | Done | REQ: submission, authorisation, consumption instants and event lists. |
| ANL8-0223 | REQ: aggregate-only audience for the site-wide readers (OD-2) | Amina sees all 7 on the A1 world; disclosure test for a department reader | Done | REQ: aggregate for HoPF, Planner, Procurement Officer, Auditor, AO and technical readers across non-Draft states; AO sees 7 states through Analytics. |
| ANL8-0224 | REQ: register rows with exact current owner destination and Tender relationship | Row set equals the count; destinations come from the owner route (ANL-AC-10) | Done | REQ: exact owner routes (`/authorised` for Authorised and Revoked) and the Tender reference. |
| ANL8-0225 | BUD: Fiscal Year Active Version totals as Decimal with `as_at`, taking `user=` (FU-ANL-04) | 150,000,000 = 55,500,000 + 0 + 94,500,000 (ANL-AC-21) | Done | BUD provider test (22 OK): exact Decimal totals (4,000,000 + 0.10 + 0.20), reserved + committed + available = registered. |
| ANL8-0226 | BUD: line "Available to" and reserved and committed amounts by reservation source department | HRMD view: 30,000,000; 13,500,000; 0; 16,500,000 and 8,000,000 reserved on the shared line; shared allocation never divided (ANL-AC-26) | Done | BUD: line owner and reservations by source department; shared allocation never divided; Active Version only. |
| ANL8-0227 | BUD: audience for Budget Officer, Budget Approver, Finance Confirmation Officer, Head of Procurement Function, Accounting Officer, Auditor and technical readers | Matrix test; approved-version-only reads for AO and HoPF confirmed | Done | BUD: audience matrix; AO and HoPF approved-only; no role gets `PermissionError`. |
| ANL8-0228 | BUD: Head of User Department department view (needs a Budget read grant that does not exist; FU-OVS-30) | Owner grants or declines the read | Done | Owner, 5 Oct 2026: "HOD has to have budget visibility". Built as the Analytics department view only (BUD test: Head of User Department still gets `PermissionError` listing Budget Versions). BUD and OVS amendment owed (FU-ANL-04). |
| ANL8-0229 | Persona negative cases for 2B through the real endpoint | Each negative returns nothing it should not | Done | Provider-level persona negatives with real users. Not driven through the HTTP endpoint. |
| ANL8-0230 | Repository-wide caller grep for every function touched in 2B, including Home providers | Counts recorded; Home provider tests re-run if a shared helper changed | Done | No existing function changed; Home workspace tests (72) and Home components (35) rerun after the `home_workspace` change. |
| ANL8-0231 | Gate ANL-G02B | Rows 0221–0230 Done except 0228; owner module tests green once | Done | 5 Oct 2026: REQ 31, BUD 22 OK. |

### Phase 2C: Owner projections — Tenders, Opening, Evaluation, Award

Gate ANL-G02C.

| ID | Deliverable | Done when | Status | Evidence |
|---|---|---|---|---|
| ANL8-0241 | TPR: `published_at` and cancellation `decided_at` per permitted Tender (FU-ANL-05) | A1: published 042–046, cancelled 046; unpublished 041 has no instant | Done | TPR provider test (25 OK): `published_at`, cancellation instants. |
| ANL8-0242 | TPR: one-bucket classifier for the §5.2 buckets using `overall_status`, deadline against the read instant, BOP, EVL and AWD stage; failed read gives Status unavailable (FU-ANL-05, 15) | A1: 1/1/1/2/1; a past-deadline Tender not yet closed by the hourly job reads Opening; every Tender classified once (ANL-AC-04, 06, 08) | Done | `test_analytics_buckets` (38 OK): every bucket, deadline-versus-clock, cancellation precedence, empty opening closed, unavailable. |
| ANL8-0243 | TPR: department and Financial year filters and register rows (title, reference, authorised requisition value, recorded AO outcome, destination) | Contributor counted once with its lead named; filter changes inclusion not the window | Done | TPR: authorised value by department from the consumed handoff; contributors; core applies the filters. |
| ANL8-0244 | BOP: Opening complete instant for nonempty openings only (FU-ANL-06) | Empty opening gives no transition; no bid count or sealed content leaves the owner | Done | BOP facts test (9 OK): nonempty openings only; no bid counts. |
| ANL8-0245 | EVL: first Report sent instant per case (FU-ANL-06) | Earliest delivered report; later versions not added; a case existing before the opening is not Evaluation by itself | Done | EVL facts test (13 OK): earliest delivered report; raw `since`; `position` phrases. |
| ANL8-0246 | AWD: case received, first committed decision instant and outcome of cycle 1 as one read (FU-ANL-07) | Return for correction is not an end event; latest decision is not mistaken for the first | Done | AWD facts test (17 OK): first committed cycle-1 decision, Return for correction not counted, `position` phrases. |
| ANL8-0247 | AWD: current committed award amount; field confirmed with the owner (C6) | A1: 7,185,000 on Tender 045 only; no department total; HoD gets no amount (ANL-AC-20) | Done | AWD: `submitted_amount` of the current committed Award decision (owner confirmed the interpretation); Head of User Department none. |
| ANL8-0248 | Outstanding matters with a raw `since` from every owner that has them (Tenders, Evaluation, Award, Requisitions) | A1: five matters, bands 0–7 days 4 and 8–30 days 1; each counts once in its record's area (ANL-M-02) | Done | Raw `since` from Requisitions, Tenders, Evaluation and Award; core bands them; Needs, Planning and Budget have no outstanding concept. |
| ANL8-0249 | Full facts for technical readers across every owner projection (D12; FU-ANL-18) | Daniel Otieno's read equals Charles's on A1 (ANL-AC-27) | Done | Facts reads return full facts to technical readers, Technical Operator included; Daniel equals Charles in the persona pass. |
| ANL8-0250 | Persona negative cases for 2C through the real endpoint | Each negative returns nothing it should not; no Tender the actor may not know | Done | Provider-level persona negatives (Head of User Department no Award notice or opinion matter and no amount, department reader limits). Not driven through the HTTP endpoint. |
| ANL8-0251 | Repository-wide caller grep for every hook or function touched in 2C, including Home providers and `kt_tender_stage_summaries` callers | Counts recorded; Home provider tests re-run if a shared helper changed | Done | No existing function changed; Home provider paths untouched. |
| ANL8-0252 | Gate ANL-G02C | Rows 0241–0251 Done; owner module tests green once | Done | 5 Oct 2026: TPR 38 + 25, BOP 9, EVL 13, AWD 17 OK. |

### Phase 3: Endpoint, verdict and server proof

Gate ANL-G03.

| ID | Deliverable | Done when | Status | Evidence |
|---|---|---|---|---|
| ANL8-0301 | `get_procurement_analytics` for Overview; thin API plus `analytics_workspace.py` composing providers by hook | Overview payload carries the five unit headlines, bands, coverage, five transitions and the funding line | Done | Overview payload tested on A1 (ANL-DES-21, 28, 31J figures). |
| ANL8-0302 | Area tab reads: Needs, Departmental planning, Annual planning, Requisitions, Tender proceedings, with registers, search and state filter | Each tab's measures and register on the A1 world; search and state change rows only (ANL-AC-09) | Done | Every area tab tested on A1 and A2 (22–27, 29–30B). |
| ANL8-0303 | Verdict states in the same call: permitted, no permitted area, invalid filter; the same call answers Home's link verdict | Nadia gets the §8 no-area copy; the menu item stays visible (ANL-AC-13) | Done | `denied`, `no_area`, invalid filters; `get_analytics_access` is cheap (no provider scan). |
| ANL8-0304 | Failure branches: area unavailable, measure unavailable, identity incomplete, state incomplete | Each branch shows its §8 text and no zero or partial total (ANL-AC-08, 23) | Done | One area, all areas, one measure, incomplete, identity-incomplete, one Tender's stage, a start event missing. |
| ANL8-0305 | Synthetic A1 test world: 2 Needs, 2 plans, 7 Plan items, 7 Requisitions, 6 Tenders, Budget, outstanding matters; isolated years from 2100; purge cleanup; built once per module (FU-ANL-13) | World builds, reconciles to ANL §10A.2 and is removed by cleanup | Partial | A1 is proved as owner facts through fake owners (`analytics_a1.py`, 50 tests), not as a world built through every owner's commands (FU-ANL-27). |
| ANL8-0306 | Synthetic A2 world (Peter, HRMD) as a view of A1 | 1 Need, 1 plan, 4 Plan items, 4 Requisitions, 4 Tenders; 041 counted once; no 044 or 046 (ANL-AC-07) | Partial | A2 likewise, as the HRMD view of the A1 facts. |
| ANL8-0307 | Synthetic A3 world (no records in any included area) | The §8 empty state, no zero claims | Done | `test_empty_selection_is_not_an_error`. |
| ANL8-0308 | Server proof of the acceptance rows that need no browser: ANL-AC-01 to 08 and 14 to 24 | Each row passes on the A1/A2 worlds with the figures in the ANL text; no forecast or derived money measure in any response (ANL-AC-24) | Partial | ANL-AC-01 to 08 and 14 to 24 pass at fact level; end-to-end on realistic data waits for the seed world (Phase 7). |
| ANL8-0309 | Register the read entry point with the technical-read conformance gate | Conformance gate passes for Analytics | Partial | Three probes registered through `kt_technical_read_probes`; the conformance table lists them OK for Administrator. The suite itself fails in earlier, unrelated checks (FU-ANL-25), so the other persona was not reached. |
| ANL8-0310 | Gate ANL-G03 | Rows 0301–0309 Done; endpoint suite green on `kentender-test.local` | Partial | Rows 0305, 0306, 0308 and 0309 are Partial. |

### Phase 4: Scoped design system and charts (may run beside Phase 2)

Gate ANL-G04. No page yet.

| ID | Deliverable | Done when | Status | Evidence |
|---|---|---|---|---|
| ANL8-0401 | Parameterise `scripts/home_design_css.py` (class list, scope class, source board) without changing Home's output (FU-ANL-20) | Home's generated CSS is byte-identical before and after; `test_home_design_scope.py` green | Done | Home's `kt_home_ds.bundle.css` md5 `87f4819ef0729329901bb978691488d7` before and after; `test_home_design_scope` 10 OK. |
| ANL8-0402 | Generate the Analytics scoped CSS under `.kt-industry.kt-analytics` from the board's classes (`kt-tab*`, `kt-disclosure*`, `kt-result-value`, `kt-range-line`, `is-cat-*`, `is-seq-*`, `kt-kpi-*`, `kt-icon-chip`) | Computed styles equal the board for every class, with and without `kt_industry_tokens.css` loaded | Done | Chromium on the 22 boards: 6,683 elements, 548 properties each, 0 differences scoped, 0 with the apps' stylesheets after resets; 32 hover/focus states, 0 differences (`reconciliation/design_scope_check.md`). `test_analytics_design_scope` 17 OK. |
| ANL8-0403 | Data palette from the board's local override (FU-ANL-10); status red, amber and green never used for a category or band | Test pins the palette tokens; colour-role test per chart (ANL-AC-28) | Done | Palette pinned to the board's values and tested (mutation check: 6 guard tests fail on a stray rule or a status red). Owner confirmed the interpretation; formal approval in the design system is not recorded (FU-ANL-10). |
| ANL8-0404 | Icons: five area icons (Needs, Departmental planning, Annual planning, Requisitions, Tender proceedings) plus any the boards use; one icon per area on tab, strip column and region titles | Icon map test; no icon in table rows | Done | `analytics_icons.js` with the five area icons; `AnalyticsIcon` spec (3 OK). |
| ANL8-0405 | Horizontal bar chart with value column | Component tests: value text on every bar, selected state mirrors the stage select | Done | `HorizontalBar` spec (10 OK). |
| ANL8-0406 | Horizontal segmented bar with legend in stated order; zero segment and legend entry omitted unless a brief says otherwise | Component tests incl. the Committed 0 exception on the funding bar | Done | `SegmentedBar` and `SegmentedBarRows` specs (10 + 10 OK), Committed 0 kept via `keepZero`. |
| ANL8-0407 | Vertical grouped bar by month: twelve slots `Jul 2026` to `Jun 2027 (to date)`, zero month shows no bar and no label | Component tests for empty and sparse series | Done | `MonthlyGroupedBars` spec (10 OK). |
| ANL8-0408 | Range strip: line from shortest to longest, median marker, shared axis 0 to 60 days ticks every 10, value columns | Component tests with A1 values | Done | `RangeStrip` spec (7 OK). |
| ANL8-0409 | From-zero horizontal bars for invitation timing (later right, earlier left; `On the approved date`; `No date recorded` has no bar) | Component tests for positive, zero, negative and blank | Done | `FromZeroBars` spec (6 OK). |
| ANL8-0410 | Every chart exposes its values as a visually hidden table in visual order, no visible toggle | Test reads the table text against the visual order | Done | Every chart renders a `table.sr-only` in visual order; asserted in each chart spec. |
| ANL8-0411 | Vitest project for chart components | Project runs green in isolation | Done | `npx vitest run --project analytics`: 200 passed, 1 skipped. |
| ANL8-0412 | Gate ANL-G04 | Computed-style comparison green; chart tests green | Done | 5 Oct 2026: computed-style comparison and chart pixel comparison (11 charts, 0 differing pixels) in Chromium. |

### Phase 5: Page shell and tabs

Gate ANL-G05. Each board row closes after the board is ported class-for-class and compared (Phase 8 repeats it as the gate).

| ID | Deliverable | Done when | Status | Evidence |
|---|---|---|---|---|
| ANL8-0501 | Page JSON `analytics` (`roles: []`, module Kentender Core), `page_js` hook entry, one `desk_page.register`, bundle, `Analytics.vue` root with `.kt-industry kt-analytics`; no `cl_surface_registry` entry | Page opens by address once migrated on the test site; AGENTS.md §6 checklist ticked | Done | Page `analytics` opens at `/desk/analytics` on the test site; one `desk_page.register`; no `cl_surface_registry` entry. |
| ANL8-0502 | Own route adapter: `/app/analytics`, `/app/analytics/{tab}`, pushed `fy`, `dept`, `state`; tab change keeps `fy` and `dept`, drops `state`; search and cursor never in the URL | Component and browser tests for push, Back, refresh and shared link (ANL-AC-12) | Done | Vitest URL contract tests and Chromium: push, Back, Forward, reload on `/desk/analytics/tender-proceedings?state=award`; `route_options` ignored; search never in the URL. |
| ANL8-0503 | Header, six tabs, filter row (Financial year, Department, Apply filters, Clear filters), Refresh, updated and scope text | Strings equal ANL §10A.1 character for character | Done | Header, tabs and filters render the spec strings (94 page tests); selects bind to a draft until Apply. |
| ANL8-0504 | Area summary strip with the five columns, segmented bars, outstanding line and link; the Home summary-column treatment (neutral left rule, area icon) | Strings and counts from the payload only; the browser computes none | Done | Strip rendered from the payload; observed live as Charles, Amina and Peter. |
| ANL8-0505 | Overview regions and boards ANL-DES-21, 21X, 28 (Amina, funding position), 31J (Daniel): waiting bands, Plan coverage, Time between key steps, funding line or region | Boards ported; first view meets the v0.8 first-view rule | Done | 21 and 28 and 31J on the seed world: Charles, Amina, Peter and Daniel opened the Overview from the sidebar; 21X opened in the test (`evidence/v0_8/seed_world_walk.md`; fidelity gate). |
| ANL8-0506 | Tender proceedings tab and boards ANL-DES-22, 23, 31A, 31F: outstanding rows with badge, stage chart, monthly chart, time strip, register, Clear stage filter | Boards ported; stage bar and select agree | Partial | 22 and 23 live as Charles (11 Tenders, Award filter 3 of 3, outstanding rows, charts); 31A (no match) and 31F (stage unavailable) by tests only. |
| ANL8-0507 | Requisitions tab and board ANL-DES-24 | Board ported | Done | 24: Requisitions tab loaded for Charles, Amina, Peter and Daniel ("Showing 10 of 13 Requisitions"), screenshot in evidence. |
| ANL8-0508 | Annual planning tab and board ANL-DES-25: coverage by item and by department, invitation timing, register | Board ported | Done | 25: Annual planning tab live (17 Plan items, laptops "103 days after approved date"), screenshot in evidence. |
| ANL8-0509 | Needs and Departmental planning tabs and boards ANL-DES-26, 27 | Boards ported | Done | 26 and 27 live ("Showing 7 of 7 Needs", "4 of 4 departmental plans"), screenshot in evidence. |
| ANL8-0510 | Department views and boards ANL-DES-29, 29F (department funding view), 30, 30B (Peter) | Boards ported; no award amount and no site-wide total | Partial | 29 and 30 live for Peter (Tender note without an amount); 29F (department funding view) and 30B by endpoint and tests only. |
| ANL8-0511 | State boards ANL-DES-31B, 31C, 31D, 31E, 31G, 31H | Boards ported; spot illustrations only on 31B, 31D and 31H | Partial | 31H live (Nadia); the forced-500 state seen live; 31B, 31C, 31D, 31E, 31G by tests only. |
| ANL8-0512 | How these figures are counted disclosure, collapsed by default; 200 ms or less transition | Expanded text equals ANL §10A.1; no transition on charts | Done | Disclosure collapsed by default, `aria-expanded`; 21X opened in the test; a registered departure for `<details>` versus a button. |
| ANL8-0513 | Narrow sheet: strip columns wrap to three then two; side-by-side regions stack; range strip keeps value columns | Component test at 960 px and below | Done | Chromium: strip 5 columns at 1172 px, 3 at 882 px, 2 at 632 px and 524 px; regions stack below 960 px; no horizontal scroll. |
| ANL8-0514 | Vitest project `analytics`; added to the structure-gate list | Project runs; `make ui-structure-gate` includes it | Done | Vitest project `analytics` exists and is in `make ui-structure-gate` (run: Analytics 200 passed). |
| ANL8-0515 | First paint and one interactive re-render verified; skeleton only when nothing to show; selects bind to the caller's own selection | Observed in a browser by address, literal strings recorded (AGENTS.md §6.4) | Done | First paint and an interactive re-render (apply a filter, switch tab) observed on the test site; no skeleton on revalidation (test). |
| ANL8-0516 | Registers shared behaviour: search on Enter, state select, Clear search, footer counts, paging beyond ten rows, owner destination links | Tests for each; whole-area summary unchanged by search and state (ANL-AC-09, 10) | Done | Live: "Showing 10 of 11 Tenders", Next gives "11 of 11"; search "printers" gives "1 of 1 matching Tenders" with the URL unchanged; Clear stage filter. |
| ANL8-0517 | Gate ANL-G05 | Rows 0501–0516 Done; component tests green; checked by address on the test site | Partial | Component tests 202 green; live on the seed world for every tab; boards 31A, 31B, 31C, 31D, 31E, 31F, 31G, 29F and 30B are covered by tests only. |

### Phase 6: Routing and menu

Gate ANL-G06. Flag the migrate need at once (FU-ANL-21).

| ID | Deliverable | Done when | Status | Evidence |
|---|---|---|---|---|
| ANL8-0601 | Sidebar item "Analytics" to the Page | `procurement.json` points at `analytics`; no `coming-soon` route option | Done | `procurement.json` Analytics item points at Page `analytics` with `url /desk/analytics`. |
| ANL8-0602 | Remove "Analytics" from `PLANNED_SIDEBAR_LABELS` | Set no longer holds it | Done | Removed from `PLANNED_SIDEBAR_LABELS`. |
| ANL8-0603 | Update `test_procurement_sidebar_g0_012_contract.py` (lines 41, 150) and any role-list guard | Contract tests green; menu item visible to every Desk user (ANL-AC-13) | Partial | New test `test_procurement_sidebar_analytics_opens_the_analytics_page` passes. Two other tests in that module fail on "Procurement meetings" and "Tender-security receipts", unrelated (FU-ANL-25). |
| ANL8-0604 | Switch on Home's gated Analytics link when the verdict permits; update `Home.spec.js:170` (D14) | Caller grep first; Home component tests green once | Done | Server field `analytics` in Home's payload from `get_analytics_access`; link after the oversight rows and, for technical readers, in the header. Home components 35 and Home workspace 72 OK. |
| ANL8-0605 | `bench migrate` flagged; state of the dev site stated | Statement recorded at the end of the task | Done | Dev: the seed session ran `bench migrate` (5 Oct 2026), restoring the sidebar export. Read-only check on dev: Page `analytics` exists, sidebar item links to it, the endpoint returns the seed world's figures, bundle `analytics.bundle.BIRTBODL.js`. This session ran nothing on dev. |
| ANL8-0606 | Menu-driven check on the test site as Charles | Page opens from the sidebar; otherwise recorded "tested by address" | Done | Test site, sidebar link, 5 Oct 2026: Charles, Amina, Peter, Daniel and Nadia each opened Analytics at `/desk/analytics` and saw their own view (`evidence/v0_8/seed_world_walk.md`). |
| ANL8-0607 | Gate ANL-G06 | Rows 0601–0606 Done | Done | Rows 0601–0606 Done except 0603 (two unrelated failing sidebar tests). |

### Phase 7: Real data and browser walk (Blocked — owner: seed hold, OD-1)

Gate ANL-G07. All rows `Blocked — owner` until the owner releases the two-year seed world and its Phase 5 state check exists. They count toward no readiness claim.

| ID | Deliverable | Done when | Status | Evidence |
|---|---|---|---|---|
| ANL8-0701 | Owner releases the seed hold; seed-world Phase 5 gate closed | Owner instruction recorded in the decision log | Done | Owner instruction 5 Oct 2026: "send a message to the seed building session to begin"; seed session reported the world ready the same day (commits 505be8dc, 92f62e7d). The owner's own record of the release is still to be made, per the seed session. |
| ANL8-0702 | Binding table SW-0502 binds each ANL A1 record kind to a generated reference (FU-ANL-13) | Table filed in the seed folder | Done | SEED-002 Appendix B (`kentender_core.seeds.portfolio.binding_rows`): T1–T11, the clinic and monitors Requisitions. |
| ANL8-0703 | Expected figures derived independently from owner data on the seeded site, not from the A1 table | Derivation recorded with the commands used | Done | `kentender_core/tests/analytics_seed_world_expected.py` (plain SQL) against the endpoint: 13 figure groups match, including the T5 judgement (`evidence/v0_8/seed_world_walk.md`). |
| ANL8-0704 | Walk every tab as Charles Mutiso from the menu | Literal rendered strings recorded for each tab | Done | Charles from the sidebar: Needs 7, Departmental planning 4, Annual planning 17, Requisitions 13, Tender proceedings 11; FY 2026/27, Tender tab, Award filter, Back, Forward, shared link, paging, search. |
| ANL8-0705 | Walk Overview with FY selected as Amina Hassan (funding position) | Literal strings recorded | Done | Amina: figures equal Charles's; shared FY link shows the funding position (registered 290,000,000, reserved 143,000,000, available 147,000,000). |
| ANL8-0706 | Walk Overview, Tender proceedings and Annual planning as Dr Peter Kimani with HRMD, with and without FY | Literal strings recorded; no award amount; no site-wide total | Done | Peter heads all three departments in this world, so his figures equal the site-wide ones; no award amount in his Tender note. A narrower department scope (Grace Wanjiku) was checked through the endpoint against the HRMD SQL slice. |
| ANL8-0707 | Walk every tab as Daniel Otieno (Technical Operator) | Equals Charles's read; no business action (ANL-AC-27) | Done | Daniel from the sidebar: identical to Charles on every tab. |
| ANL8-0708 | Direct entry as Nadia Kamau | No-area copy; menu item was visible (ANL-AC-13) | Done | Nadia from the sidebar: menu item visible; lock illustration and the no-area sentence, no tabs, totals or rows. |
| ANL8-0709 | Direct load, refresh, Back, forward and a shared link on every tab with `fy`, `dept` and `state` | Same view each time after a fresh verdict (ANL-AC-12) | Done | As Charles: Apply writes `?fy=2026-2027`, tab keeps it, stage adds `&state=award`, Back, Back, Forward walk the entries, a direct load of the shared link reproduces the view. |
| ANL8-0710 | Forced failure of one area, one measure and all reads | The §8 text appears; other regions keep their values | Partial | A forced 500 shows the all-failed state live; one-area and one-measure failures by tests; invalid filters live (message, no figures). |
| ANL8-0711 | Console clean except Frappe's known dev noise | Observed | Done | Console on every walk: only Frappe's socket.io 404 and xhr-poll noise. |
| ANL8-0712 | Gate ANL-G07 | Rows 0701–0711 Done | Partial | Rows 0701–0709 and 0711 Done; 0710 Partial (per-region failure not forced live). |

### Phase 8: Release evidence

Gate ANL-G08.

| ID | Deliverable | Done when | Status | Evidence |
|---|---|---|---|---|
| ANL8-0801 | Fidelity departures file `tests/ui/fidelity/departures/analytics.js` with a reason and authority per departure | Every departure listed; none unexplained | Done | `tests/ui/fidelity/departures/analytics.js`: 18 disclosure pairs (`<details>` and `<summary>` versus a button) and one text departure on 31F, each with reason and authority; stale entries fail. |
| ANL8-0802 | Fidelity spec comparing all 22 boards | 22 boards compared; results recorded | Done | `analytics.fidelity.spec.js`: 50 tests, 22 boards, container skeleton, element tags and ordered landmark text; four negative controls prove it can fail; it found a real missing-space defect. |
| ANL8-0803 | `make` fidelity target and `fidelity-affected` rule; artboard provenance header | Target runs; rule fires for Analytics files | Partial | `make ui-analytics-fidelity-gate` and the `fidelity-affected.sh` rule exist and parse. No artboard-provenance header check was added. |
| ANL8-0804 | Keyboard pass: tabs, selects, filter buttons, stage bar, disclosure, links, Try again | Every control reachable with visible focus (ANL-AC-11) | Partial | Chromium Tab order: tabs, filters, Apply, Clear, six links, disclosure; every Analytics control shows a ring. Tests cover reachability and `aria-expanded`. |
| ANL8-0805 | 200% zoom and narrow sheet | Material reasons and the read-only purpose stay visible (ANL-AC-11) | Partial | Narrow sheet measured; at a 720 px viewport (200% equivalent) no horizontal scroll and the title, Refresh and read-only note remain. A real browser zoom was not used. |
| ANL8-0806 | Assistive-technology tables for every chart | Text equals the visual values | Partial | Every chart's `table.sr-only` is asserted in its spec. Not read with a screen reader. |
| ANL8-0807 | Production-mode build; bundle hash confirmed changed | Build succeeds; hash recorded | Partial | `./scripts/bench-with-node.sh build --app kentender_core` was run twice and the page loaded from it; the bundle hash was not recorded. |
| ANL8-0808 | Persona pass as every persona of Phase 7 | Needs rows 0704–0708 (blocked); otherwise recorded as not run | Blocked — owner | Depends on Phase 7 |
| ANL8-0809 | Acceptance map closed with evidence for ANL-AC-01 to 28 | Each row Done or named Partial or Blocked with the reason | Partial | See the acceptance status table below: 15 Done, 13 Partial. |
| ANL8-0810 | Gate ANL-G08 | Rows 0801–0809 Done | Partial | Rows 0803–0809 Partial or blocked. |

### Phase 9: Owner-gated and deferred (all Blocked — owner)

Counts toward no readiness claim.

| ID | Deliverable | Done when | Status | Evidence |
|---|---|---|---|---|
| ANL8-0901 | Owner-document amendments through the document-change protocol: NDS, PLN, REQ, BUD, TPR, BOP, EVL, AWD, OVS (FU-ANL-01 to 09) | Each amendment filed as a new version and approved by the owner | Blocked — owner | Owner decision |
| ANL8-0902 | Approval of the palette and icon set; design system records them (FU-ANL-10) | Owner approval quoted | Partial | Owner confirmed the interpretation ("1. Confirmed"); the palette's approval in the design system is not recorded. |
| ANL8-0903 | Register entries for ANL v0.8, HOME v0.6 and KT-STD v1.22 under the register's own rule (FU-ANL-12) | `register_check.py` passes | Blocked — owner | Owner decision |
| ANL8-0904 | Award-amount field confirmed (`submitted_amount` recommended; C6) | AWD owner answer recorded | Blocked — owner | Owner decision |
| ANL8-0905 | HoD "award notices awaiting delivery" question answered (C7; FU-HOME-06) | AWD owner answer recorded | Blocked — owner | Owner decision |
| ANL8-0906 | Contract Management, delivery, inspection, performance and Accounts measures | Separate change unit; not scheduled | Blocked — owner | Deferred by ANL §2 |
| ANL8-0907 | Head of User Department Budget read grant for the department funding view (FU-OVS-30) | Same decision as row 0228 | Done | Decision made 5 Oct 2026 (row 0228); the general Budget read for the role (FU-OVS-30) is unchanged. |
| ANL8-0908 | KT-STD §4 versus AGENTS.md §6.5 wording on `cl_surface_registry` (FU-HOME-11) | Shared with Home; no Analytics action | Blocked — owner | Owner decision |

## Acceptance map (ANL-AC-01 to 28)

Each row's text is in the spec §14 and is copied verbatim into `reconciliation/ac_map.md` in Phase 0 (row ANL8-0007). A row is Done only when every tracker row named here is Done with its own evidence and the criterion is met end to end; "Partial" says what was proved and what was not.

| Acceptance row | Status (5 Oct 2026) | Basis | Tracker rows |
|---|---|---|---|
| ANL-AC-01 | Done | real data: 7 Needs, 4 departmental plans, 17 Plan items, 13 Requisitions, 11 Tenders, each on its own unit, none summed (walk) | ANL8-0305, ANL8-0308 |
| ANL-AC-02 | Done | FY filter matches the SQL derivation for 2026/27, 2027/28 and All years; All years needs no current-year prerequisite | ANL8-0243, ANL8-0308 |
| ANL-AC-03 | Done | Plan items count once with contributors; department selections match the HRMD and Digital Health SQL slices; Active Version only | ANL8-0203, ANL8-0308 |
| ANL-AC-04 | Partial | A1 stage reconciliation 1+1+1+2+1=6 at fact level; classifier tests for the real chain | ANL8-0242, ANL8-0308, ANL8-0704 |
| ANL-AC-05 | Partial | classifier: nonempty opening to Evaluation, empty opening closed | ANL8-0242, ANL8-0308 |
| ANL-AC-06 | Partial | classifier and failure tests; no real end-to-end chain | ANL8-0242, ANL8-0308 |
| ANL-AC-07 | Partial | A2 at fact level | ANL8-0306, ANL8-0308, ANL8-0706 |
| ANL-AC-08 | Partial | Status unavailable and identity-incomplete branches tested | ANL8-0304, ANL8-0308 |
| ANL-AC-09 | Done | live paging 10 of 11 then 11 of 11, search and state filters, counts independent of page size | ANL8-0111, ANL8-0302, ANL8-0516 |
| ANL-AC-10 | Partial | owner routes only, read-only; links not all walked live | ANL8-0224, ANL8-0516, ANL8-0709 |
| ANL-AC-11 | Partial | literal-string tests and fidelity gate; not representative-user tested | ANL8-0801, ANL8-0804, ANL8-0805 |
| ANL-AC-12 | Done | live: Apply, tab, state, Back, Forward, reload and shared link reproduce the view; search and cursor never in the URL | ANL8-0502, ANL8-0709 |
| ANL-AC-13 | Done | live: invalid fy, dept and state show the §8 message, keep the valid parts and draw no figure; Nadia's menu item visible | ANL8-0110, ANL8-0303, ANL8-0502, ANL8-0603, ANL8-0708 |
| ANL-AC-14 | Partial | every ANL-DES-21 figure reproduced from owner facts | ANL8-0301, ANL8-0308, ANL8-0505 |
| ANL-AC-15 | Done | unit tests: 8.5 for T1, site-time dates, window only | ANL8-0106, ANL8-0308 |
| ANL-AC-16 | Done | test: a year filter changes inclusion, not the window | ANL8-0102, ANL8-0308 |
| ANL-AC-17 | Done | band tests; no late/overdue/at-risk wording in any payload (test) | ANL8-0103, ANL8-0308 |
| ANL-AC-18 | Done | real data: covered 143,000,000 equals the SQL sum of authorised drawdowns; 11 + 1 + 5 items reconcile to 17; HRMD 57,000,000 of 70,500,000 | ANL8-0204, ANL8-0107, ANL8-0308 |
| ANL-AC-19 | Partial | A1 values at fact level; REQ provider tests | ANL8-0221, ANL8-0308 |
| ANL-AC-20 | Done | award amount 46,400,000 equals the committed Award Decision; Peter sees none; no department total | ANL8-0113, ANL8-0247, ANL8-0308 |
| ANL-AC-21 | Done | funding 290,000,000 with reserved 143,000,000, committed 0, available 147,000,000 equals Budget; sums to registered; no region outside the audience | ANL8-0112, ANL8-0227, ANL8-0225, ANL8-0308 |
| ANL-AC-22 | Done | laptops read "103 days after approved date", the seed's own stated figure; a missing actual reads No date recorded (tests) | ANL8-0205, ANL8-0308 |
| ANL-AC-23 | Done | failure-branch tests: no zero, no partial total, no percentage | ANL8-0101, ANL8-0304, ANL8-0308 |
| ANL-AC-24 | Partial | no forbidden word in payloads (test); boards not each inspected | ANL8-0308, ANL8-0801 |
| ANL-AC-25 | Partial | funding audience via owner and core tests | ANL8-0112, ANL8-0308 |
| ANL-AC-26 | Partial | A2 funding at fact level; BUD department view test | ANL8-0226, ANL8-0308 |
| ANL-AC-27 | Done | Daniel equals Charles on every tab in the browser, no business action | ANL8-0114, ANL8-0249, ANL8-0707 |
| ANL-AC-28 | Partial | palette and colour-role guards; rendered boards compared structurally, not by colour | ANL8-0403, ANL8-0404, ANL8-0801 |

## Measure map

| Measure or transition | Name | Tracker rows |
|---|---|---|
| ANL-M-01 | Area count and state distribution | ANL8-0207, ANL8-0203, ANL8-0221, ANL8-0242, ANL8-0302 |
| ANL-M-02 | Outstanding matters by waiting time | ANL8-0103, ANL8-0248 |
| ANL-M-03 | Recorded each month | ANL8-0104, ANL8-0201, ANL8-0202, ANL8-0222, ANL8-0241 |
| ANL-M-04 | Time between key steps | ANL8-0106, ANL8-0222, ANL8-0241, ANL8-0244, ANL8-0245, ANL8-0246 |
| ANL-M-05 | Tender invitation timing | ANL8-0205, ANL8-0409 |
| ANL-M-06 | Planned value | ANL8-0203 |
| ANL-M-07 | Plan coverage | ANL8-0204, ANL8-0107 |
| ANL-M-08 | Requisition value | ANL8-0221 |
| ANL-M-09 | Authorised requisition value by Tender stage | ANL8-0221, ANL8-0242 |
| ANL-M-10 | Recorded award amount | ANL8-0247, ANL8-0113 |
| ANL-M-11 | Funding position | ANL8-0225, ANL8-0226, ANL8-0112 |
| T1 | Requisition submitted to authorised | ANL8-0222 |
| T2 | Requisition authorised to Tender started | ANL8-0222, ANL8-0241 |
| T3 | Tender started to published | ANL8-0241 |
| T4 | Bid opening complete to evaluation report sent | ANL8-0244, ANL8-0245 |
| T5 | Evaluation report sent to AO decision recorded | ANL8-0245, ANL8-0246 |

## Board map (22 boards)

| Boards | Content | Port row | Fidelity rows |
|---|---|---|---|
| ANL-DES-21, 21X, 28, 31J | Overview (Charles; definitions expanded; Amina with FY; Daniel) | ANL8-0505 | ANL8-0801, 0802 |
| ANL-DES-22, 23, 31A, 31F | Tender proceedings (Charles; Award selected; no search match; one stage unavailable) | ANL8-0506 | ANL8-0801, 0802 |
| ANL-DES-24 | Requisitions | ANL8-0507 | ANL8-0801, 0802 |
| ANL-DES-25 | Annual planning | ANL8-0508 | ANL8-0801, 0802 |
| ANL-DES-26, 27 | Needs; Departmental planning | ANL8-0509 | ANL8-0801, 0802 |
| ANL-DES-29, 29F, 30, 30B | Peter's department views | ANL8-0510 | ANL8-0801, 0802 |
| ANL-DES-31B, 31C, 31D, 31E, 31G, 31H | No records; area unavailable; all failed; measure unavailable; loading; no permitted area | ANL8-0511 | ANL8-0801, 0802 |

## Build findings

**5 October 2026: the build.** Decisions made while building; the phase text above is not rewritten.

- **What exists.** Core: `analytics_contract.py` (provider contract and validators), `analytics_measures.py`, `analytics_viewer.py`, `analytics_workspace.py`, `analytics_probes.py`, `api/analytics.py` (`get_procurement_analytics`, `get_analytics_access`). Owners (each `services/analytics_provider.py` unless stated): Departmental Needs; Procurement Planning (two kinds); Procurement Requisitions; Tenders (plus `analytics_buckets.py`); Budget; and `analytics_facts.py` in Bid Opening, Bid Evaluation and Award. Page: `page/analytics`, `analytics_page.js`, `public/js/analytics/` (page, 18 components, 7 chart components, scoped CSS, icons, 20 golden payloads, 3 spec files). Hooks: `kt_analytics_providers` (procurement, budget) and the technical-read probes. Home: a server `analytics` field and two links. Make targets `analytics-preflight`, `analytics-services-gate`, `ui-analytics-fidelity-gate`; `fidelity-affected.sh` rule.
- **Tests run (test site, 5 Oct 2026).** Python 282 across 13 modules, all OK: core 87 (18 + 50 + 17 + 2), NDS 13, PLN 27, REQ 31, TPR 38 + 25, BOP 9, EVL 13, AWD 17, BUD 22. Components: `analytics` 200 passed (1 skipped), `home` 35, `design-fidelity` 46, and one at a time `award` 52, `tenders` 101, `bid-evaluation` 113, `procurement-planning` 401. Home workspace Python 72. When `make ui-structure-gate` ran every project at once the machine's load average reached 41 to 64 on 12 cores and many unrelated tests timed out at about 250 s; the same projects pass one at a time, so that is load, not a regression.
- **Not run.** Playwright specs (none written; no menu-driven spec against the seed world), the dev site (no migrate), a screen reader, a real browser zoom, Firefox and WebKit, dark theme, the seed world (on hold), the persona walks of Daniel and Nadia in a browser, paging beyond ten rows live.
- **Red first was not followed for the owner providers.** Each builder wrote provider and tests together and showed the tests bite by breaking the code (for example three deliberate breaks in Planning, two real Award bugs caught by the tests). The core engine and the page were written with their tests in the same pass.
- **Route spike changed the design.** The URL prefix is `/desk/`, `set_route` drops the query, and `frappe.route_options` keeps stale keys across Back and Forward; the page therefore writes its own history entries and reads only `location.search` (reconciliation/route_spike.md).
- **The tests found real defects.** In Award a failed notice issue was treated as a hold and `state.committed_decision` without a cycle returned the whole case's latest decision (a latent risk in the owner's own Home and eligibility code, not changed); in the page a missing space ran a bold title into its sentence; in core the first colour mapping repeated a category colour and a plural read "1 Plan items".
- **Owner data differs from the pictures in places.** Recorded as conflicts C1–C24 and follow-ups FU-ANL-01 to 28; the largest are the coverage basis (C1, confirmed), the widened aggregate audience (OD-2), Award notices for the Head of User Department (C22, owner to confirm) and A1 not being seed data (C8).
- **Real-data walk (5 Oct 2026).** Run on the two-year seed world after the seed session's release; 13 figure groups derived independently with plain SQL all matched, the T5 network switches Tender is Opening (Evaluation has not received the package), and the invalid-filter behaviour was changed because the live page widened the selection (`evidence/v0_8/seed_world_walk.md`). Component tests 202 (analytics), 46 (design-fidelity), 35 (home); Python 282 unchanged.
- **Dev state (updated).** The seed session ran `bench migrate` on the dev site and restored the sidebar export; a read-only check shows the Page, the sidebar item and the seed world's figures there. Earlier text follows. Code is live on the dev site at once: the owner providers, the hooks, the endpoints and the Home change take effect after a cache clear. The Page record and the sidebar item need `bench migrate` there (FU-ANL-21); until then the dev menu still reads "Analytics — Planned" and `/desk/analytics` is not installed. No dev data was touched.
- **Seed session.** Row 0701 waits for the owner's release of the seed hold; the owner's 5 Oct instruction asks that the seed session be told when this build ends. The expected figures for the browser walk (row 0703) are derived from owner data after the seed world's Phase 5 binding table.
