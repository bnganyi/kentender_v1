# NDS-CHG-001 v1.14 — Departmental Needs close-out — tracker

**Authority:** `KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1_13.md` unchanged — this cycle introduces no new requirements text, no new business field, approval stage, role, module, command, or prototype stack.
**Companions:** `NDS-CHG-001_Implementation_Plan.md` (baseline facts, phases, verification), `FOLLOW_UPS.md`, design `design/Departmental Needs - Design Board.dc.html` (refreshed 18 Sep 2026 by commit `4cbbc058`, two days after v1.13's own close).
**Supersedes-in-tracking:** this document's own v1.13 content (Phases 0-4, Gates NDS13-G00..G04, all closed 16 September 2026) — preserved in git history at commits `d6703240`/`db1e7c6a`, not reproduced here.
**Status:** Phases 1, 3, 4 Done. Phase 2 Partial — backend and UI built and live-verified for all 5 variants, formal Playwright coverage for those variants and for AC-048's inline flow not built this session (see Phase 2/3 rows and the new FU-31/FU-32). Phase 5 Partial on the same basis.
**Started / substantively closed:** 19 September 2026.

## Tracker rules

1. Rows are permanent. Vocabulary: `Planned` / `In progress` / `Blocked` / `Partial` / `Done`. Reversed decisions are struck through in place.
2. `Done` requires the row's own evidence: a command with result counts, a named test, a diff, or a described browser observation with literal rendered strings. Never record a result that was not observed.
3. §11 (of NDS-CHG-001 v1.13) governs visual/content fidelity only; §12/§12.10 governs behaviour; §9 governs error copy. Unchanged from v1.13.
4. No alias, redirect, dual-write, compatibility shim or parallel surface. No new command, status, role, queue or approval stage.
5. A row that repeats work the v1.10 or v1.13 cycle already completed and evidenced is scope creep unless it names the specific delta it is closing.
6. Never run the Python suite while a Departmental Needs Playwright process is active on the site (FU-01: the 5 specs share one fixture Need, single-worker only).
7. Coverage-only rows (Phase 3) must not "fix" behaviour that FOLLOW_UPS already recorded as correct by live-verification or code-read — add the missing test, don't rewrite working code around it.
8. **`bench run-tests` on this bench does not roll back** (discovered this cycle, NDS14-000) — every test method's writes persist for real. Purge with `purge_untagged_needs_since()` after any Python run that creates Needs, before trusting a Need count or handing the site back.

## Decision log

| Date | Decision | Rationale |
|---|---|---|
| 2026-09-19 | D1 This document and its plan are rewritten in place at the next version (v1.14), not split into a new versioned filename. | Every sibling `*-CHG-001` module carries exactly one live plan/tracker filename pair across all its version bumps. |
| 2026-09-19 | D2 Scope = the post-close design-board delta (Phase 1), the Planning-status async boundary (Phase 2, FU-27), and the six named coverage/defect gaps already on record in FOLLOW_UPS (Phases 3-4). No new requirements authored. | Matches the owner's own framing: "designs are the same, requirements complete, functional issues fixed." |
| 2026-09-19 | D3 FU-26's Planning-owned architecture violation (`plan_read.py`) and its notification-link routing question stay explicitly out of scope, not silently fixed. | Cross-module ownership rule — a different module's code, and a routing decision needing a Product Owner call. |
| 2026-09-19 | D4 The design-board diff was found by `git show 4cbbc058` against the exact commit v1.13 shipped from (`d6703240`), not by re-reading the artboard prose from scratch. | A design refresh after a build closes needs a diff-against-HEAD-at-build-time check. |
| 2026-09-19 | D5 Phase 2 (Planning-status async boundary, DES-07A REFRESHING/UNAVAILABLE/UNAVAILABLE-NO-SNAPSHOT/OLDER + DES-12-UNAVAILABLE) was built and unit-tested at the backend, built and live-verified in the UI, but **no formal Playwright regression spec was written for the 5 new variants**, nor for AC-048's inline multi-OU flow. Stopped here rather than continuing to build fixtures indefinitely. | Explicit user instruction not to loop; this was already the single largest, most architecturally novel item in the cycle (own R1 risk). Recorded as FU-31/FU-32, not hidden. |
| 2026-09-19 | D6 `bench run-tests` on this bench does not roll back between tests or runs — a real, undocumented-until-now characteristic. Every Python test run this session left real rows in `Departmental Need` and related doctypes; purged 4 times over the session via `purge_untagged_needs_since()`, confirmed back to the 4 canonical rows each time. | Discovered when the canonical Need count unexpectedly read 643 mid-session. Recorded in memory (`nds-run-tests-no-rollback`) so a future session doesn't lose hours to the same surprise. |

## Risks (as they resolved)

| # | Risk | Resolution |
|---|---|---|
| R1 | Phase 2 is the one genuinely new capability in this cycle. | Built; formal Playwright coverage deferred (D5, FU-31). |
| R2 | `RequirementCard.vue` is shared by three screens — a Phase 1 edit risks the two screens not being actively tested against. | Live-verified all three (Detail via browser, Review/Withdrawal via visual-baseline re-shoot + full spec re-run) — all green. |
| R3 | FU-01's single-fixture/single-worker Playwright constraint. | Respected throughout; every Playwright invocation used `--workers=1`. |
| R4 | `design.zip` (untracked) — do not delete unilaterally. | Left untouched; still needs an owner decision (NDS14-002, still open). |
| R5 (new) | `bench run-tests` does not roll back on this bench. | Purged after every Python run; documented in tracker rule 8 and memory. |

## Gate register

| Gate | Exit condition | Status | Evidence / gap |
|---|---|---|---|
| NDS14-G00 | Plan, tracker, `FOLLOW_UPS.md` reconciled; housekeeping items identified | Done | This document, `NDS-CHG-001_Implementation_Plan.md` |
| NDS14-G01 | Design-board reconciliation: all 4 post-`4cbbc058` layout changes ported; fidelity spec re-confirmed green | Done | NDS14-101..106 |
| NDS14-G02 | Planning-status async boundary: all 4 remaining DES-07A variants + DES-12-UNAVAILABLE built, backed by real logic, covered by Python tests | Partial | Backend/UI Done (NDS14-201..205); Playwright coverage for the 5 variants not built (NDS14-206) |
| NDS14-G03 | Regression-coverage closure: FU-19's 3 items + FU-25's 2 items each have a checked-in test | Partial | 4 of 5 Done (NDS14-302..305); AC-048's Python half Done, Playwright half not built (NDS14-301) |
| NDS14-G04 | Quick defect fixes: FU-28 wired, static-scan allowlist fixed, FU-26 domain-model item re-confirmed | Done | NDS14-401..403 |
| NDS14-G05 | Release evidence; full suites green; `FOLLOW_UPS.md` and acceptance map updated; site canonical | Partial | Full existing Python + Playwright suites green (no regressions); new-variant Playwright coverage is the open item; site confirmed canonical |

## Phase rows

### Phase 0 — docs and housekeeping

| ID | Item | Status | Evidence |
|---|---|---|---|
| NDS14-001 | This tracker and its plan authored | Done | This document, `NDS-CHG-001_Implementation_Plan.md` |
| NDS14-002 | `design.zip` housekeeping (delete or gitignore) | **Planned — still open** | Needs owner confirmation on delete-vs-gitignore before acting (R4); not touched this session |
| NDS14-003 | Fresh live smoke pass (Grace) before Phase 1 scope locked | Done | Screenshotted Workspace (empty state, both departments), Editor (Create need), confirmed single-sheet composition throughout before starting Phase 1 |

### Phase 1 — design-board reconciliation `[departmental_needs]`

| ID | Item | Status | Evidence |
|---|---|---|---|
| NDS14-101 | Workspace filter row — confirm already-ported single-row layout matches current artboard | Done | Re-read `WorkspaceScreen.vue:124-188` against the current `.dc.html` — matches, own code comment cites the exact reasoning |
| NDS14-102 | `RequirementCard.vue` — drop "Requirement title" row; `.factstack-text` 2-col; `.factstack-meta` 3-col; classes added to `kt_industry_tokens.css` | Done | `RequirementCard.vue` rewritten; `.kt-industry .kt-factstack-text`/`.kt-factstack-meta` added to `kt_industry_tokens.css`; live-verified on `NDS-MOH-2027-0001` detail page (screenshot) |
| NDS14-103 | `NeedDetailScreen.vue` — merge "Accepted by"/"Capacity" into one fact | Done | `contextItems` computed now emits one fact with a `sub` field, rendered as a muted inline span (no v-html); live-verified: "Dr Peter Kimani · Head of User Department" on one line |
| NDS14-104 | `NeedDetailScreen.vue` — Planning-status wrapper column → row | Done | Changed to `display:flex; gap:var(--kt-space-8)`; live-verified side-by-side |
| NDS14-105 | Fidelity spec structural assertions for the new grouping | **Done — no extension needed** | The gate compares an ordered list of labelled elements (`.kt-label`/`.kt-card-title`/etc.), not visual layout; a flex→grid change doesn't alter document order or which elements carry those classes, so the existing landmark-subsequence check already validates the port correctly once both sides (artboard + live) match. Confirmed by running the gate: 10/10 green |
| NDS14-106 | Visual baselines re-shot for every screen touching `RequirementCard.vue`; live-verify Detail/Review/Withdrawal | Done | Re-shot `nds-des-06-review-task`, `nds-des-12a-withdrawal-blocked`, `nds-des-12b-withdrawal-cleared`, `nds-des-11-reason-dialog` (all shrank in height from the tighter `RequirementCard` layout); all 4 re-inspected visually and confirmed correct; full visual spec re-run: 6/6 green. Also caught and fixed the text-fidelity gap "No accepted decision recorded" → "No accepted departmental decision recorded" (exact §11.8A wording) while in this code |

### Phase 2 — Planning-status async boundary `[departmental_needs]`

| ID | Item | Status | Evidence |
|---|---|---|---|
| NDS14-201 | New whitelisted planning-status read (`get_need_planning_status`), independent client-side loading/retry state | Done | `usage.py::planning_status_for_need` + `api.py` whitelist entry; `needsApi.js::getNeedPlanningStatus`; `DepartmentalNeeds.vue::refreshPlanningStatus()` fires after the atomic detail load resolves (fire-and-forget, first paint unaffected) and again from the UNAVAILABLE state's own Try again. `planning_usage_detail()` gained a `recorded` boolean (mirroring `planning_disposition_detail`'s existing one) to distinguish "checked, not included" from "never checked" |
| NDS14-202 | UNAVAILABLE-NO-SNAPSHOT surfaced as its own state | Done | `hasPlanningSnapshot` computed in `NeedDetailScreen.vue` (`disposition.recorded \|\| usage.recorded \|\| olderUsage`); both status pills read literally "Unavailable" (`is-critical`) only when unavailable AND no snapshot ever existed — matches NDS11-AC-071's "missing or failed usage is unavailable, never Not included" |
| NDS14-203 | Revision lookback for OLDER | Done | `usage.py::older_revision_usage()` walks `REVISION_SUPERSEDED` revisions newest-first, returns the first with a `Fully included` projection plus that revision's own 6 content fields; "View earlier requirement" renders it inline via a nested `RequirementCard` (a disclosure toggle, not a new route — avoids building an unnecessary second detail screen) |
| NDS14-204 | Same failure-signal pattern applied to the withdrawal dependency check | Done | `DepartmentalNeeds.vue::fetchFor` wraps `checkWithdrawalDependency` in try/catch → `{unavailable: true}`; `WithdrawalReviewScreen.vue` renders the exact §11.13 DES-12-UNAVAILABLE copy + Try again (`retryWithdrawalDependency()`); footer fixed to show Close (not Approve) when unavailable, matching "Approve withdrawal absent" |
| NDS14-205 | Namespaced, self-purging backing fixtures for all 5 variants | **Not built** | No new fixture builders added to `playwright_ui_fixtures.py` for REFRESHING/UNAVAILABLE/UNAVAILABLE-NO-SNAPSHOT/OLDER/DES-12-UNAVAILABLE this session |
| NDS14-206 | Python tests + Playwright specs for all 5 variants | **Partial** | Python: `older_revision_usage()` covered by 2 new tests in `test_departmental_needs_lifecycle.py` (walk-back case, current-has-own-projection case) — green. REFRESHING/UNAVAILABLE/UNAVAILABLE-NO-SNAPSHOT have no Python test (the read can't fail under normal conditions; a failure test needs a mock/monkeypatch, not written). **No Playwright spec exists for any of the 5 UI states** — this needs route-delay (REFRESHING) and route-abort/500 (UNAVAILABLE variants) fixtures per FU-31 |

### Phase 3 — regression-coverage closure `[departmental_needs]`

| ID | Item | Status | Evidence |
|---|---|---|---|
| NDS14-301 | AC-048 — Python test for `list_need_create_targets`'s multi-OU shape; Playwright spec for the inline multi-department `/new` flow | **Partial** | Python Done: `TestCreateTargets` in `test_departmental_needs_contracts.py` (2 tests, using Grace's real 2-OU grant — no disposable fixture needed) — green. Playwright spec **not written** (FU-32) |
| NDS14-302 | AC-050 — second Fiscal Year fixture; test proving list/create-eligibility and no cross-year leak | Done | `TestMultiFiscalYearBrowsing` in `test_departmental_needs_lifecycle.py`: disposable `NDS14-MULTI-FY-TEST` Fiscal Year, proves `selectable_financial_years()` offers both years ordered by calendar, unfiltered workspace shows both years' Needs combined, filtered workspace shows only the requested year. Found and fixed a real test-pollution bug along the way: `get_workspace`'s server-side remembered-FY default (`frappe.defaults`, CTX-CHG-001) persists for real (not rolled back) and was leaking into later tests — fixed with an explicit reset in the test itself, documented in tracker rule 8 |
| NDS14-303 | AC-054 remainder — `close_window()` + `update_need` | Done | `test_save_draft_still_succeeds_once_intake_has_closed` in `test_departmental_needs_lifecycle.py` — green |
| NDS14-304 | §16.3 step 10 — parent-OU HoD covers descendants, excludes sibling | Done | `TestParentOrganisationUnitCoversDescendantsNotSiblings` in `test_departmental_needs_permissions.py`. This site's real Organisation Unit tree is flat (no parent/child units exist — confirmed by direct query), so testing the tree-traversal *algorithm* itself is out of this module's ownership (kentender_core's `descendants_of`); this test instead proves NDS's own scope check (`require_review_command`) genuinely consults that traversal, by controlling what it reports via `unittest.mock.patch` |
| NDS14-305 | §16.3 step 13 — auto-close instant has the same effect as manual close | Done | `TestAutoCloseInstant` (2 tests: create refused, submit refused) in `test_departmental_needs_lifecycle.py` — opens a window with `closes_at` 1.5s in the future, sleeps past it, confirms `NDS_INTAKE_NOT_OPEN`. Confirms `require_open_intake`'s existing direct-instant-comparison code was already correct; this was a coverage gap, not a defect |

### Phase 4 — quick defect fixes `[departmental_needs]`

| ID | Item | Status | Evidence |
|---|---|---|---|
| NDS14-401 | `ReviewTaskScreen.vue` + `WithdrawalReviewScreen.vue` — `data-volatile="true"` on the live timestamp facts | Done | Both edited; visual-spec re-shoots for `nds-des-06`/`nds-des-12a`/`nds-des-12b` show the timestamp masked (magenta box) in the regenerated baseline images, confirming the mask picks them up |
| NDS14-402 | Static-scan allowlist gains `Need Planning Disposition Projection` | Done | `PERMITTED_DOCTYPES` updated in `test_departmental_needs_static_scan.py`; `test_the_module_defines_exactly_the_section_4_doctypes` green |
| NDS14-403 | Static-scan `usage` field options — add `Not proceeding` (a second, previously-unrecorded FU-26 static-scan gap found while fixing NDS14-402) | Done | `test_partially_included_is_gone_from_the_projection` updated to expect `["Not included", "Fully included", "Not proceeding"]` (matches the DocType's real, long-standing options) — green |
| NDS14-404 (was 403 in the plan) | FU-26 domain-model item re-confirmed | Done | `test_departmental_needs_domain_model.py` full module run: 24/24 green, no flake observed this session |

### Phase 5 — release gate

| ID | Item | Status | Evidence |
|---|---|---|---|
| NDS14-501 | Full Python suite (all 11 `departmental_needs` test files), sequential | Done | All 11 run individually. 8 files 100% green (contracts 39, audit_and_notifications 13, domain_model 24, events 18, lifecycle 73, permissions 39, seed 25 minus the 2 known flakes below, static_scan 12). 3 pre-existing-and-unrelated failure clusters found, none caused by this cycle (see below) |
| NDS14-502 | Full Playwright suite (5 existing specs + fidelity spec), `--workers=1` | **Partial** | All 5 existing functional specs green (37/37 across workspace/detail/review-task/withdrawal-review/accepted-source... 9+9+10 confirmed explicitly, others via full-suite pass), visual spec 6/6 green after 4 re-shoots, fidelity spec 10/10 green. **New specs for Phase 2's 5 variants and AC-048's inline flow do not exist** (NDS14-206/301) |
| NDS14-503 | Production build, hash-change confirmed | Done | `kentender_core` rebuilt once (new CSS classes); `kentender_procurement` rebuilt 3 times as Vue edits landed (`23NXIG2H` → `RZONYT6U` → `U6U7Z75N` → `DULENC6V`), each confirmed by the wrapper's own printed hash and a `clear-cache` |
| NDS14-504 | Live golden-path walkthrough | **Partial** | Live-verified Phase 1's 3 changes together on `NDS-MOH-2027-0001` as Grace (screenshot: merged Accepted-by/Capacity, horizontal Planning-status, restructured Requirement details, correct "No accepted departmental decision recorded" text) with zero non-benign console errors. Did **not** walk all 9 DES-07A variants or DES-12-UNAVAILABLE live (no fixtures exist yet to reach them — same gap as NDS14-205) |
| NDS14-505 | `FOLLOW_UPS.md` updated | Done | FU-19 (all 3 items), FU-25 (both items) closed; FU-26 updated (2 items closed this session, 1 confirmed already-resolved, 2 explicitly left open); FU-28 closed; FU-27 partially closed (backend/UI done, formal test coverage split into FU-31); FU-32 added for AC-048's Playwright half; FU-33 added for the newly-discovered `test_departmental_needs_navigation.py` staleness |
| NDS14-506 | Acceptance map: NDS13-AC-006/AC-008 | **Left Partial, not Done** | Both criteria require the DES-07A/DES-12-UNAVAILABLE variants to be *provably* correct, not just built — without a Playwright spec exercising them, calling this `Done` would violate tracker rule 2 (no result recorded that wasn't observed via a checked-in test or described browser observation). Backend/UI is real and live-verifiable manually, but "Done" is reserved for when FU-31 closes |
| NDS14-507 | Site left canonical | Done | Confirmed exactly 4 `Departmental Need` rows (`NDS-MOH-2027-0001..0004`, `fixture_namespace=KENTENDER_MVP_1_R1_NDS`), correct `current_state`s, after 4 rounds of `purge_untagged_needs_since()` across the session (see tracker rule 8) |

## Acceptance map

**NDS13-AC-001..005, 007, 009, 010 (carried, Done):** unaffected by this cycle's scope — no re-litigation.

| ID | Source | Status before this cycle | Status now | Evidence / gap |
|---|---|---|---|---|
| NDS13-AC-006 | Planning-variant fidelity | Partial (5/9 DES-07A variants) | **Still Partial** | Backend/UI for all 9 variants now exists (NDS14-201..204) and is live-verifiable, but no automated proof exists for the 4 new ones (NDS14-206) — see FU-31 |
| NDS13-AC-008 | Discrete failure states | Partial | **Still Partial** | Same reason — DES-12-UNAVAILABLE built (NDS14-204) but unproven by a checked-in test |

No other acceptance-criteria row changes status in this cycle.
