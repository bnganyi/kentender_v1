# STR-CHG-001 v1.8 — Strategy Alignment usability correction — tracker

**Authority:** `KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1_8.md` (consolidated approved requirements, 13 September 2026; supersedes v1.7 in full). KT-STD-001 v1.5 governs by owner direction (plan D4).
**Companions:** `STR-CHG-001_Implementation_Plan.md` (decision register D1–D12, conflicts C1–C8, phases), `FOLLOW_UPS.md`, design `strategy_design/*.dc.html` (12 artboards on the v1.8 `_ds`).
**Supersedes-in-tracking:** the v1.7 correction pass (`IMPLEMENTATION_TRACKER.md`, closed 6 September 2026; 86 Python test functions, 7 Playwright tests, STR-AC-001..037 evidenced except the fidelity half of STR-AC-025). That build is the baseline this cycle corrects.
**Status:** Phases 0–4 Done 14 September 2026 (uncommitted at time of writing). Every §16.2 (12) journey was driven in a real browser by the §14 actors on the v1.8 compositions; the Strategy Python suite, the browser gate, the new fidelity gate and both halves of the industry design gate that can run on this site are green.
**Started:** 14 September 2026.

## Tracker rules

1. Rows are permanent. Vocabulary: `Planned` / `In progress` / `Blocked` / `Partial` / `Done`. Reversed decisions are struck through in place.
2. `Done` requires the row's own evidence: a command with result counts, a named test, a diff, or a described browser observation with literal rendered strings. Never record a result that was not observed.
3. §11 governs visual/content fidelity only; §12 governs behaviour. A row implementing behaviour from §11 prose is a defect.
4. No alias, redirect, dual-write, compatibility shim or parallel surface. Old labels are replaced, not kept as fallbacks.
5. Every visible action maps to one existing §8.1 command; no new command, status, role or approval stage.
6. Never run the Python suite while a Strategy Playwright process is active on the site.

## Decision log

| Date | Decision | Rationale |
|---|---|---|
| 2026-09-14 | Owner Q1 — design system: follow the v1.8 `_ds` faithfully; re-tune the shared `kt_industry_tokens.css` (plan D2). | The tokens file is the one product design system and has always been re-tuned from the newest bundle. |
| 2026-09-14 | Owner Q2 — neutral labels: tab is **Actions** (FU-07), not "My work" (plan D3). | One neutral convention across module landing pages. |
| 2026-09-14 | Owner Q3 — KT-STD-001 v1.5 governs; technical read is §3A.6 (plan D4). | FU-08. |
| 2026-09-14 | D5 comparison by structural key, no `copied_from` field. | Data-purpose gate. |
| 2026-09-14 | D6 idempotency via the existing `Strategy Command Journal` on all write commands. | §8.2; helper exists. |
| 2026-09-14 | D7 one pending change set; Submit saves then submits with separate keys. | §8.2/§12.3. |
| 2026-09-14 | D8 server refuses future-effective approval; predecessor `effective_to` closes to the day before the successor start when later than its own start. | §5.1/§11.6/STR18-XD-002. |

## Risks

| # | Risk | Handling |
|---|---|---|
| R1 | D2 changes table padding, hover and header band for every Industry page; other modules' fidelity gates measure geometry from older `_ds` renders. | Run `ui-budget-fidelity-gate` and `ui-system-setup-fidelity-gate` once at Phase 4; record truthfully; drift is those modules' follow-up. |
| R2 | `industry-design-gate.spec.ts` compares `--kt-color-accent` across pages; all read one file so parity holds, but the Python half aborts on the site's Fiscal Year overlap (PLN C18). | Run; record the abort if it recurs. |
| R3 | Sibling-uniqueness guard on `display_order` trips mid-batch on a swap. | 2d applies temporary negative orders first. |

## Gate register

| Gate | Exit condition | Status | Evidence / gap |
|---|---|---|---|
| STR18-G00 | Plan, tracker, follow-ups, memory | Done 2026-09-14 | This document, `STR-CHG-001_Implementation_Plan.md`, FOLLOW_UPS FU-07/08/09 rows. |
| STR18-G01 | Design system re-tuned; industry gate green; Strategy renders indigo live | Done 2026-09-14 | `kt_industry_tokens.css` re-tuned (711 → 733 lines); live `getComputedStyle` on `/desk/strategy`: `--kt-color-accent #2b46b0`, `--kt-color-bg #f0f2f7`, 0 visible `.kt-corner`, `th` band `#f5f6f9` on a 2px accent rule; `industry-design-gate.spec.ts` 2 passed (computed-style parity + shared rail). Static half `kentender_core.tests.test_industry_design_gate` aborts in the framework's test-record preload on the site's pre-existing Fiscal Year overlap (R2, PLN C18) — unrelated to this change and recorded truthfully. |
| STR18-G02 | Server contracts 2a–2e green in the Python suite | Done 2026-09-14 | `test_str_chg_001_v1_8_usability` 17 OK; full `--app kentender_strategy` suite `Ran 59 … OK` + `Ran 44 … OK` (103 tests) after this cycle's changes. |
| STR18-G03 | Screens 3A–3E ported; `make ui-strategy-gate` green; live click-through by every actor | Done 2026-09-14 | `make ui-strategy-gate` 8 passed (3.5m); live click-through as Esther (register → Current overview → Update plan → inline target 80→85 → Save changes → Add objective under Programme → Move up → unsaved guard → Submit) and Alfred (Actions → Review → decision overview → Return dialog → Approve → Current/Previous version); screenshots `evidence/v1_8/`. |
| STR18-G04 | Release evidence §16.3; AC map complete; C8 gates recorded | Done 2026-09-14 (C8 row below) | `make ui-strategy-fidelity-gate` 4 passed (FU-01 closed); production bundle `strategy.bundle.*.js` built through `bench-with-node.sh`; repository scan `TestStaticScan` green inside the suite; C8 sibling gates: see STR18-404. |

## Phase rows

### Phase 1 — design system `[core]`

| ID | Item | Status | Evidence |
|---|---|---|---|
| STR18-101 | Re-tune tokens: bg, accent, accent-2, divider, neutral ramp, accent ramps 100–900, accent-2 ramp | Done | `kt_industry_tokens.css` token block: `--kt-color-accent: #2b46b0`, `--kt-color-accent-2: #d9691a`, `--kt-color-bg: #f0f2f7`, `--kt-color-divider: #d4d8e3`, neutral 100–900, accent 100–900, accent-2 100–900, chart 1–6, `--kt-shadow-md`. |
| STR18-102 | Corner marks hidden (`.kt-corner`), removed from Strategy markup; status/figure dots removed | Done | `.kt-industry .kt-corner { display: none !important }`; `grep kt-corner kentender_strategy/…/public/js` = 0; `.kt-status::before { display: none }`, `.kt-figure::after { content: none }`. Other apps' dead markup: FU-09. |
| STR18-103 | Table header band + accent rule, accent-100 hover, cell padding, focus ring 1px accent-700, type floor, links rust | Done | `.kt-table th` band/rule, `tbody tr:hover` accent-100, `td` 10px/space-4, `:focus-visible` 1px accent-700, `.kt-label` 13px/600, `a` accent-2-700; tabs re-styled to the v1.8 `.kt-tab`. |
| STR18-104 | New components `.kt-notice`, `.kt-timeline`, `.kt-kpi-card`, `.kt-disclosure`, `.kt-checkbox`, `.kt-tag`, `.kt-move-btn` | Done | Appended under "v1.8 components"; plus `.kt-field-hint`, `.kt-field-error`, responsive `.kt-grid-2/-3`, `.kt-editor-grid`, `.kt-objective-grid` (stack ≤ 900px). |
| STR18-105 | `ui-industry-design-gate` (Python half) and bundle rebuild + cache clear; live screenshot | Done (Python half blocked by R2) | Runtime half 2 passed; static half aborts on the site's FY overlap before any assertion (R2). Live screenshot `evidence/v1_8/str18-phase1-register.png`. |

### Phase 2 — server contracts `[strategy]`

| ID | Item | Status | Evidence |
|---|---|---|---|
| STR18-201 | Portfolio: `plan_type_label`, `status_label`, `available_action` vocabulary, Actions rows with review type / submitted by / submitted | Done | `strategy_ui_contracts.py` (`plan_type_label`, `version_status_label`, `_row_action`, `_my_work_versions`, `period_fy_label`); `TestVocabulary` 3 OK. |
| STR18-202 | Workspace: `objectives` lead, `pending_update`, `capabilities.update_plan`, Draft identity/version-date save, historical version read with Previous version label | Done | `get_plan_workspace(plan_id, version_number)`; `TestWorkspaceComposition` 3 OK; `has_been_submitted` on the version DTO. |
| STR18-203 | Review overview: `review_type`, `comparison`, `proposed`, `readiness.failures`, `blockers`, `self_approval_blocked` | Done | `get_version_review_overview`; `TestReviewOverviewAndComparison` 6 OK. |
| STR18-204 | `diff_strategy_versions` D5 (dates, title/period, nodes, order, definitions, units, targets; first-version; unavailable baseline) | Done | Rewritten on structural keys; rows carry kind/tag/item/path/previous/proposed/ids; `test_comparison_reports_definitions_units_order_additions_and_removals`, `test_first_version_comparison_says_so`; phase-7 diff test updated to the new shape. |
| STR18-205 | Approval refuses future `effective_from`; predecessor closure semantics; readiness rule ids | Done | `strategy_readiness.get_version_approval_blockers` / `assert_version_ready_for_approval`; `_activate` closes the predecessor's `effective_to` to D-1 when the successor starts later; `TestImmediateEffectApproval` 2 OK. Existing suites pin the review date (`tests/fixtures.pin_review_date`); the Works Master demo seed approves its 2031 plan under its own frozen clock. |
| STR18-206 | `idempotency_key` on the five write commands via `run_idempotent` | Done | `strategy_consumer_api.py`; `TestIdempotentReplay` 2 OK (same plan on replay; one Approve event on replay). |
| STR18-207 | Sibling reorder in one change set without tripping uniqueness | Done | `save_strategy_structure_draft` parks changed orders on temporary negatives; covered in the comparison test's objective swap. |
| STR18-208 | Fixture profiles FUTURE / IMMEDIATE / RETURN / DATE-TARGET / NEW-PLAN with §14.4 clocks; Draft saved 15:55 | Done | `seed_str_des_v2_draft/_fixture/_returned_fixture(profile=…)`; `playwright_ui_fixtures.reset_{submitted,future,returned,date_target,draft}_fixture`; `TestFixtureProfiles` OK on the canonical plan (13:10 / 15:55 / 16:20 / 11:20). Browser IMMEDIATE uses the site date while it is earlier than 25 Nov 2026 (documented in `_immediate_effective_from`). |
| STR18-209 | Forbidden copy per §11.10; technical read §3A.6 test retained | Done | Exact §11.10 copy in all three screens; `test_str_technical_read` 4 OK; `strategy-access.spec.ts` asserts the copy and the empty Actions queue for Administrator. |

### Phase 3 — screens

| ID | Item | Status | Evidence |
|---|---|---|---|
| STR18-301 | STR-UI-01 Strategic plans + Actions (STR-DES-01, 10) | Done | `PortfolioScreen.vue` rewritten; live snapshot: h1 "Strategic plans", tabs Plans/Actions, columns Plan type/Period (`2023/24–2027/28`)/Version/Status "Current"/View; Actions columns Plan/Review/Submitted by/Submitted/Status/Action. Fidelity STR-DES-01 passed. |
| STR18-302 | STR-UI-02 Create plan (STR-DES-02), Draft Overview (§11.3A), Current Overview (STR-DES-03), Previous version | Done | `PlanWorkspaceScreen.vue` rewritten; create lands on `/version/1/structure`; §11.3A card with Save plan details / Edit structure and Use from / Use until; Current overview leads with `ObjectivesAndTargets.vue`; `/version/1` shows "Previous version" + View current plan. Fidelity STR-DES-02/03 passed. |
| STR18-303 | STR-UI-03 Structure editor pending set, Move up/down, typed adds, inline target editor (STR-DES-04/05/05-AddTarget) | Done | `StructureEditor.vue` (pending change set, `$n` client ids, save-then-submit with separate attempt keys, three-way unsaved guard + `beforeunload`, Move up/down, typed deletes, inline target editor, validation summary); `AddTargetDialog.vue` deleted. Fidelity STR-DES-04/05-AddTarget passed (the pending editor is inline per §11.5; asserted as two sequences). |
| STR18-304 | STR-UI-04 Approval decision overview, proposed structure, comparison, history, return dialog, future-effective banner (STR-DES-06..09, 06-Return) | Done | `ApprovalTaskScreen.vue` rewritten; `ReturnDialog.vue`; one-click approve (no confirmation stage); `str-future-effective` banner disables approval on the FUTURE profile with Return enabled (approver spec test 2). Fidelity STR-DES-06/07/08/09/06-Return passed. |
| STR18-305 | Shared states, unknown-outcome recovery, stale, own-version, keyboard, narrow | Done (unknown-outcome replay not browser-proven) | `attempts.js` (`runAttempt`: replay once on a lost response, key kept in `sessionStorage` across reload); `frappeCall.js` classifies 0/502/503/504 as unknown; copy per §11.10 for loading/denied/error/stale/own-version; tree rows `tabindex=0` + Enter/Space; responsive grid classes verified at 420px (no horizontal scroll). The lost-response replay is covered server-side (`TestIdempotentReplay`) and by code review; no browser test injects a dropped response yet — see FU-11. |
| STR18-306 | Playwright specs updated (author, approver, access) + `strategy-fidelity.spec.ts` | Done | `make ui-strategy-gate` 8 passed; `make ui-strategy-fidelity-gate` 4 passed; stale `tests/ui/helpers/strategyWorkbench.ts` removed. |

### Phase 4 — release gate

| ID | Item | Status | Evidence |
|---|---|---|---|
| STR18-401 | Strategy Python suite | Done | `bench --site kentender.midas.com run-tests --app kentender_strategy`: `Ran 59 tests … OK`, `Ran 44 tests … OK` (2026-09-14 23:0x EAT). |
| STR18-402 | `make ui-strategy-gate`, `make ui-strategy-fidelity-gate`, `make ui-industry-design-gate` | Done (static half blocked by R2) | 8 passed / 4 passed / runtime spec 2 passed; static Python half aborts in test-record preload (FY overlap) as in every module since PLN C18. |
| STR18-403 | Production asset build; repository scan (§16.2 item 11) | Done | `./scripts/bench-with-node.sh build --app kentender_strategy` → `strategy.bundle.K6SFRTOO.js` (and later hashes on each rebuild); `TestStaticScan` green in the suite. |
| STR18-404 | C8 sibling fidelity gates recorded | Done 2026-09-14 | After the re-tune: `make ui-budget-fidelity-gate` **23 passed (1.9m)**; `make ui-system-setup-fidelity-gate` **17 passed (1.5m)**. No landmark or geometry drift from D2 on either module; R1 did not materialise; FU-10 closed. |
| STR18-405 | AC map, FOLLOW_UPS, memory | Done | This document; FOLLOW_UPS FU-01 closed, FU-07/08 notes, FU-09/10/11 opened; memory `strategy-v18-kickoff` updated. |

## Acceptance map

All 37 prior STR-AC rows remain evidenced by the v1.7 tracker unless a row below reopens them. New rows:

| ID | Status | Evidence |
|---|---|---|
| STR-AC-025 (revised compositions, both halves) | Done | `ui-strategy-gate` 8 passed (behaviour, zero console errors) + `ui-strategy-fidelity-gate` 4 passed (STR-DES-01–09 incl. the two dialogs). |
| STR-AC-029 / 030 | Done | Approver spec: overview leads with "What changed"; footer present on every tab; FUTURE profile cannot be approved; no confirmation stage. |
| STR18-AC-001, 002 | Done | `TestVocabulary`; author/approver specs (Current, Changes requested, Correct and resubmit, Review). |
| STR18-AC-003, 004 | Done | Author spec test 2 (create lands on structure; no reference input); `TestIdempotentReplay.test_plan_creation_replays_from_the_journal`; `runAttempt` on create. |
| STR18-AC-005, 006 | Done | Author spec (Add objective under Programme, Move up/down); `test_comparison_reports…` (swap in one change set); deletion refused after submission (server + `str-target-delete` absent in the approver spec). |
| STR18-AC-007, 008 | Done | Author spec (one Save changes; Submit saves then submits — two journal rows observed live); `TestIdempotentReplay`; unknown-outcome browser injection outstanding (FU-11). |
| STR18-AC-009, 010 | Done | Inline editor with Financial year / Target date modes (author spec, `reset_date_target_fixture`); definition/unit distinct in author and review; percentage/duplicate rules unchanged (server tests). |
| STR18-AC-011, 012 | Done | `test_successor_review_leads_with_server_comparison`, `test_comparison_reports…`, `test_first_version_*`; approver spec (Target + Date rows). |
| STR18-AC-013, 014 | Done | Labels Approve and use plan / Approve changes and use plan / Return for correction (server `decision`); one click; `TestImmediateEffectApproval`; replay test. |
| STR18-AC-015, 016 | Done | `test_overview_leads_with_objectives_and_targets`, `test_current_version_leads_and_pending_update_is_separate`; approver spec Previous version at `/version/1`. |
| STR18-AC-017, 018 | Done (partial for 018) | `test_readiness_failures_name_the_missing_item`; author spec inline "Add a pillar"; stale/permission copy present; access-revocation and lost-response recovery not browser-driven (FU-11). |
| STR18-AC-019, 020 | Done (representative-user review outstanding) | Access spec (Auditor, no-assignment, Administrator); keyboard rows; narrow layout at 420px; fidelity gate. Representative-user findings remain STR18-XD-008, outside this build. |
| STR18-AC-021, 022 | Done | `test_future_effective_version_cannot_be_approved_and_stays_submitted`, `test_immediate_version_activates_and_closes_the_predecessor`, `test_profiles_carry_the_section_14_4_clocks_and_isolate`; approver spec FUTURE test. |
| STR18-AC-023, 024 | Done | This tracker maps every prior STR-AC and the 24 new criteria; plan D1–D12 and C1–C8 record authority and owner dependencies. |
