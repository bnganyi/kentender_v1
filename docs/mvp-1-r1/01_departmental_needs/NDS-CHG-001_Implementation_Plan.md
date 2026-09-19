# NDS-CHG-001 v1.14 — Departmental Needs close-out: design-refresh reconciliation, Planning-status async boundary, regression-coverage closure — implementation plan

## Context

NDS-CHG-001 v1.13 (the §11/§12.10 screen-composition rewrite) closed 16 September 2026 — all phases and gates (NDS13-G00..G04) Done, committed as `d6703240` (build) and `db1e7c6a` (three canonical-seed bugs found exercising the closed build). **v1.13 remains the current requirements authority; no requirements text changes in this cycle.** This is a correction/closure cycle on top of it, in the same spirit v1.13 itself was on top of v1.10 — the v1.13 tracker's own content is preserved in git history at those two commits; this document and `NDS-CHG-001_IMPLEMENTATION_TRACKER.md` are rewritten in place to carry the next slice of work forward, per the module's own full-replacement convention for these two files.

Two things happened after the 16 September close that this cycle exists to close out:

1. **The design board moved after the build closed.** Commit `4cbbc058` ("docs(needs): refresh the Departmental Needs design board", 18 September 2026, owner-authored) edited `design/Departmental Needs - Design Board.dc.html` two days after Phase 4's gate — nobody has reconciled the screens against it since. Diffing `4cbbc058` against its parent (`d6703240`, the exact commit the v1.13 build was ported from) shows a single-file, 86-line change, four concrete layout edits. One is already ported (apparently done ahead of this plan, evidenced below); three are not. This is exactly the "design-tool regen after close" trap recorded for Budget (`budget-v19-kickoff` memory) — caught here by diffing the artboard file against the commit the build actually shipped from, not by re-reading prose.
2. **v1.13's own tracker recorded five follow-ups it did not close** (`FOLLOW_UPS.md` FU-19 residue, FU-25, FU-26, FU-27, FU-28) because they were genuine new capability or pre-existing debt outside a usability-only cycle's scope. Two gate rows stayed `Partial` for the same reason (NDS13-303, NDS13-305) and two acceptance-criteria rows stayed `Partial` (NDS13-AC-006, NDS13-AC-008). None of these are speculative — each has a named, dated FOLLOW_UPS entry with a concrete fix already sketched.

**Owner instruction (this session):** "Done means the designs are the same, requirements are complete, and any functional issues are fixed." Read literally against what's actually open, that maps onto three bodies of work — Phase 1 (designs), Phase 2 (the one requirement still Partial), Phase 3/4 (the recorded functional/coverage gaps) — not a rebuild. The domain model, lifecycle, permissions and the 12 §8.2 commands are untouched and stay untouched.

## Baseline facts the plan relies on

- App/module: `kentender_procurement/kentender_procurement/departmental_needs/` (backend); `kentender_procurement/kentender_procurement/public/js/departmental_needs/` (frontend). Nothing about the desk-page registration, backend contract surface, or design-token set changed since v1.13's own baseline facts (`git log`, re-confirmed) — this section only records what's different now.
- **Design-board delta, confirmed by `git show 4cbbc058 -- ".../Departmental Needs - Design Board.dc.html"`** (the only file in that commit with markup changes):
  1. Workspace filter row: two rows (search/status/FY, then department/Clear filters) merged into one row. **Already ported** — `WorkspaceScreen.vue:124-188` carries this exact layout with its own explanatory comment ("splitting this across two rows made the department select's long label read as if the row had wrapped"). Re-confirm only in Phase 1; no code change.
  2. Requirement-details fact block: the "Requirement title" row (redundant — the screen heading already shows the title) removed; Description + Expected result placed in a 2-column grid (`.factstack-text`); Quantity + Unit + Required by placed in a 3-column grid (`.factstack-meta`). **Not ported** — `RequirementCard.vue:8-33` (confirmed by direct read) still renders the pre-refresh single-column stack including a "Requirement title" fact row. `RequirementCard.vue` is shared by `NeedDetailScreen.vue`, `ReviewTaskScreen.vue` and `WithdrawalReviewScreen.vue` — one component fix reconciles all three screens.
  3. DES-07 "Accepted by" / "Capacity" facts merged into one line (`"Julia Njeri · Acting Head of User Department"`). **Not ported** — `NeedDetailScreen.vue:327,331` (confirmed by direct read) still emits two separate facts.
  4. Planning-status section: vertical stack (`flex-direction:column`) changed to a horizontal row (`display:flex;gap:var(--space-8)`). **Not ported** — `NeedDetailScreen.vue:90` (confirmed by direct read, comment at line 86-87 still says "two rows") is still `flex-direction: column`.
- **Follow-ups this cycle closes** (`FOLLOW_UPS.md`, read in full):
  - FU-19 residue: AC-048 (multi-OU eligibility — note the object of the test has moved: `CreateTargetDialog.vue` was retired by NDS13-CHG-003 in favour of the inline DES-15 selector, so the checked-in coverage this closes is for the inline flow, not the dialog FU-19 originally named), AC-050 (multi-Fiscal-Year browsing), AC-054 half (save-draft while intake closed). Confirmed still open by grep: zero hits for a second-Fiscal-Year fixture or a `close_window`+`update_need` combination anywhere in the test tree.
  - FU-25: AUTH-ADR-001 §16.3 steps 10 (sibling-OU exclusion) and 13 (auto-close instant) still have no checked-in regression, live-verified only.
  - FU-26: five pre-existing failures found running the full suite during v1.13. Three are **not this module's to fix** (Planning's `plan_read.py` reads the Decision table directly — a Planning-owned boundary violation; a Returned-need notification link target — a routing decision needing a Product Owner call, not a code default to guess at) — left exactly as FOLLOW_UPS records them, not touched here. Two are: `test_departmental_needs_static_scan.py`'s allowlist missing `Need Planning Disposition Projection`/`Not proceeding` — this module's own test file, a stale allowlist, in scope. The fifth (`current_accepted_revision` domain-model drift) is **confirmed already resolved** — live query today shows `NDS-MOH-2027-0001.current_accepted_revision == "...-V001"` as the seed expects, fixed as a side effect of `db1e7c6a`'s canonical-seed corrections; only needs a confirming test run, no code change.
  - FU-27: DES-07A's four remaining Planning-status variants (REFRESHING/UNAVAILABLE/UNAVAILABLE-NO-SNAPSHOT/OLDER) and DES-12-UNAVAILABLE need a real capability addition (a distinguishable "the read failed" signal, separate from "read succeeded, not included"; a lookback across prior accepted revisions) — not a template port. This is the one genuine new-capability item in the cycle.
  - FU-28: `nds-des-06-review-task` and `nds-des-12a-withdrawal-blocked` visual baselines drift on every re-run because their live "Submitted at"/"Requested at" facts render as plain spans instead of through `ReadonlyRow.vue`'s existing `volatile` prop. Confirmed by direct read: `ReviewTaskScreen.vue:25` and `WithdrawalReviewScreen.vue:22` are plain `<span>`s; `ReadonlyRow.vue` already has the `volatile`/`data-volatile` convention and `departmental-needs-visual.spec.ts:59` already masks `[data-volatile]` — the fix is wiring existing plumbing through two lines, not building anything new.
- **Site state, confirmed live**: 5 `Departmental Need` rows total — 4 canonical (`NDS-MOH-2027-0001..0004`, `fixture_namespace=KENTENDER_MVP_1_R1_NDS`) plus one `NEED-PLNT-0001` tagged `fixture_namespace=KENTENDER_TEST`. That fifth row is Planning's own test residue (matches the `canonical-validate-planning-test-residue` memory exactly) — not this module's fixture, not swept by this plan; `canonical.clear_non_canonical()` is the documented fix and is Planning's/canonical-owner's call, recorded here only as pre-flight context.
- Untracked `docs/mvp-1-r1/01_departmental_needs/design.zip` (206 KB) has been sitting in the working tree since before `4cbbc058`. That commit's own message already asked for it to be deleted or gitignored (it predates the board edits and nothing reads it) — still there. Housekeeping item, Phase 0.
- Docs precedent: this plan and its tracker are rewritten in place (not new versioned filenames) per the pattern already established by every sibling `*-CHG-001` module (Budget, Strategy, Planning, Tender Preparation, System Setup each carry exactly one live plan/tracker pair; the one-time old-filename-to-`*-CHG-001`-filename split happened only at the pre-CHG-001-to-CHG-001 transition, not at every version bump).

## Scope boundary

**In scope:** Phases 1–4 below — design-board reconciliation, the Planning-status async boundary, the six named regression-coverage gaps (FU-19 ×3, FU-25 ×2), the two quick in-scope defect fixes (FU-28, the static-scan allowlist), release evidence.

**Explicitly out of scope, not silently dropped:**
- Planning's `plan_read.py` reading `Departmental Need Decision` directly (FU-26 item 1) — Planning-owned code, a different module's fix.
- The Returned-need notification link target (FU-26 item 2) — needs a Product Owner decision on the intended route, not a default this session should pick.
- Every non-goal v1.13's own §18.3 table already recorded (Planning-side event producer, the withdrawal-transaction validator, usage-stream wire inspection, cross-module float-precision remediation, shared SEED-module adoption, CFG UOM verification, representative-user usability testing) — none of that changed; not reproduced here in full, see the v1.13 plan's own "Non-goals" section (preserved in git history at `d6703240`).
- No new business field, approval stage, role, module, command, or prototype stack — same constraint v1.13 itself operated under (§20).

## Phase sequence

| Phase | Name | Exit condition |
|---|---|---|
| 0 | Docs and housekeeping | This plan + `NDS-CHG-001_IMPLEMENTATION_TRACKER.md` rewritten in place; `FOLLOW_UPS.md` reviewed (done above); stale `design.zip` removed or gitignored; one fresh live smoke pass across all 5 screens to catch anything that drifted since 16 Sep beyond what's already named. |
| 1 | `[departmental_needs]` design-board reconciliation | The 3 not-yet-ported layout changes (factstack regrouping, Accepted-by/Capacity merge, Planning-status row) ported class-for-class; fidelity spec's structural assertions extended to catch the new grouping mechanically; affected visual baselines re-shot. |
| 2 | `[departmental_needs]` Planning-status async boundary | New whitelisted read for planning status with its own loading/retry state (closes REFRESHING/UNAVAILABLE/UNAVAILABLE-NO-SNAPSHOT); revision lookback for OLDER; the same failure signal reaches the withdrawal-dependency check (closes DES-12-UNAVAILABLE). |
| 3 | `[departmental_needs]` regression-coverage closure | FU-19's 3 remaining items + FU-25's 2 items each get a checked-in Python or Playwright test, not just a live-verified or code-read confirmation. |
| 4 | `[departmental_needs]` quick defect fixes | FU-28 (`data-volatile` wiring) and the static-scan allowlist gap fixed; FU-26's `current_accepted_revision` item re-confirmed green. |
| 5 | Release gate | Full Python suite, full Playwright suite (existing + fidelity + new Phase 2/3 specs) green; production build with hash-change confirmed; live golden-path walkthrough covering all 9 DES-07A variants + DES-12-UNAVAILABLE; `FOLLOW_UPS.md` and the tracker's acceptance map updated; site left canonical. |

## Phase 0 — docs and housekeeping

1. This plan and the tracker, rewritten in place (baseline facts above already gathered by direct git/code/live-query inspection, not assumption).
2. Delete `docs/mvp-1-r1/01_departmental_needs/design.zip` or add it to `.gitignore` — the prior commit's own message already flagged it as a stale, unread duplicate; confirm with the repo owner which of the two before acting, since it's an untracked file outside this session's own working set.
3. One fresh live smoke pass (Grace as Author, Peter as Head of User Department) across Workspace/Editor/Detail/Review/Withdrawal before starting Phase 1 — confirms the 16 September golden path (NDS13-404) still holds and surfaces anything not already named in FOLLOW_UPS before phase scope is locked in.

## Phase 1 — design-board reconciliation

Work against the *current* `.dc.html` (post-`4cbbc058`), not memory of the pre-refresh layout.

1. **Confirm, don't re-port**, the workspace filter row (`WorkspaceScreen.vue:124-188`) already matches the single-row layout — re-read against the current artboard once, move on.
2. **`RequirementCard.vue`** (`components/RequirementCard.vue:8-33`): drop the "Requirement title" fact row; wrap Description + Expected result in a `.factstack-text` two-column grid; wrap Quantity + Unit + Required by in a `.factstack-meta` three-column grid, matching the artboard's own inline styles exactly. These are board-authored utility classes scoped to the artboard's own `<style>` block — check whether an equivalent already exists in `kt_industry_tokens.css` under `.kt-industry`; if not, add them there (shared, additive, same treatment `.is-info` got in the v1.13 cycle — never invent a one-off scoped class in the component file itself).
3. **`NeedDetailScreen.vue:327,331`**: merge "Accepted by" and "Capacity" into one fact (`"{name} · {capacity}"`, capacity in the muted/smaller style the artboard shows), matching the artboard's exact markup.
4. **`NeedDetailScreen.vue:90`**: change the Planning-status wrapper from `flex-direction: column` to the artboard's horizontal row with `gap: var(--space-8)`.
5. Since `RequirementCard.vue` is shared, step 2 alone reconciles `NeedDetailScreen.vue`, `ReviewTaskScreen.vue` and `WithdrawalReviewScreen.vue` in one edit — confirm all three render correctly afterward, not just Detail.
6. Extend `tests/ui/smoke/design-fidelity/departmental-needs-fidelity.spec.ts`'s structural landmark assertions for DES-05/06/07/08/09/12 to expect the new two-/three-column grouping (not just presence of the facts) — this is the mechanism that would have caught this drift automatically had it existed before the 18 September refresh; extending it now closes that blind spot going forward.
7. Re-shoot every visual baseline touching `RequirementCard.vue` or the Planning-status block; re-run the fidelity spec.

## Phase 2 — Planning-status async boundary (the one genuine new capability in this cycle)

This is architecture, not a template port — v1.13's own FU-27 already said so; treat it with the same care.

1. Add a whitelisted read separated from `get_need()`'s atomic payload (e.g. `get_planning_status(need)` in `services/workspace.py` or `services/usage.py`, following the existing `planning_usage_detail`/`planning_disposition_detail` pattern) that can independently signal: succeeded-with-a-value, succeeded-with-no-projection-yet, or failed. On the client, `NeedDetailScreen.vue` fetches this separately from the rest of the detail payload with its own pending/error/retry state — this is what makes REFRESHING (in flight) and UNAVAILABLE (failed) representable as distinct states from CLEAR/PROCEEDING/etc., which today are impossible because the whole page waits on one atomic call.
2. UNAVAILABLE-NO-SNAPSHOT: the same read distinguishes "no projection exists for this revision at all" from "checked, and it says not included" — likely already latent in whether `planning_usage_detail`/`planning_disposition_detail` return `None` vs. a value; confirm and surface it as its own named state rather than folding it into UNAVAILABLE.
3. OLDER: extend the read (or add a sibling helper) to walk back through a Need's prior *accepted* revisions' own usage/disposition projections when the current accepted revision has none yet — the current code only ever reads the current revision's projection.
4. Apply the same failure-signal pattern to `check_accepted_need_withdrawal_dependency` for `WithdrawalReviewScreen.vue`'s DES-12-UNAVAILABLE variant (FU-27's own update names this as the identical gap on a second screen — one fix pattern, two call sites).
5. Since none of the named `NDS-SC-DISPOSITION-*` profiles exist in seeds today (confirmed by NDS13-201's grep, zero hits), build the backing fixtures these 5 new variants need directly in `playwright_ui_fixtures.py`, namespaced and self-purging from the start — do not attempt the formal, canonical, cross-module §14.6A profile set (that remains NDS11-XD-005, explicitly out of scope).
6. TDD: Python tests for the new read/lookback logic first (red→green), then Playwright specs for all 5 variants (4 DES-07A + 1 DES-12).

## Phase 3 — regression-coverage closure

Each item below already has correct behaviour (per FOLLOW_UPS's own live-verification or code-read) — the gap is a missing checked-in test, not a defect. Do not "fix" what isn't broken; add coverage.

1. **AC-048** — a Python test asserting `list_need_create_targets`'s actual zero/one/several-OU return shape (currently checked only for being whitelisted); a Playwright spec giving one fixture actor two Organisation Units and exercising the inline `/new` multi-select flow (Save draft/Submit for review disabled until a department is chosen, enabled once picked) — the exact scenario NDS13-302 live-verified once as Grace but never captured as a spec.
2. **AC-050** — build a namespaced second Fiscal Year fixture (none exists on this site today, per FU-19/FU-23's own note); a Python or Playwright test proving list/create-eligibility survive a remembered/filtered year and that switching years doesn't leak the other year's rows.
3. **AC-054 (remaining half)** — a lifecycle test combining `close_window()` (`test_departmental_needs_lifecycle.py:95`) with `update_need`, asserting save-draft still succeeds on a Draft/Returned Need while intake is closed.
4. **§16.3 step 10** — a permissions test proving a parent-OU Head-of-User-Department assignment covers named descendants but excludes a sibling outside that subtree, using the real OU tree or a disposable one.
5. **§16.3 step 13** — a lifecycle test setting `kentender_needs_submission_closes_at` to a near-future instant, advancing past it, and asserting create/submit are refused before the hourly `close_due_needs_submissions` job runs — proving a reached auto-close instant has the same effect as a manual close.

## Phase 4 — quick in-scope defect fixes

1. **FU-28**: give `ReviewTaskScreen.vue:25`'s "Submitted at" fact and `WithdrawalReviewScreen.vue:22`'s "Requested at" fact the same `volatile` treatment `ReadonlyRow.vue` already provides elsewhere (render through `ReadonlyRow` or apply `data-volatile="true"` directly) — `departmental-needs-visual.spec.ts` already masks `[data-volatile]`, so this alone stops the recurring false-failure re-shoots.
2. **Static-scan allowlist**: add `Need Planning Disposition Projection` and its `Not proceeding` value to `test_departmental_needs_static_scan.py`'s `PERMITTED_DOCTYPES`/expected-values allowlists — this module's own test file, a stale allowlist for a doctype that predates this cycle.
3. **FU-26 domain-model item**: re-run `test_departmental_needs_domain_model.py` to confirm the `current_accepted_revision` flake is gone now the canonical reseed (`db1e7c6a`) has run — expect green, no code change.

## Phase 5 — release gate

1. `bench --site kentender.midas.com run-tests --app kentender_procurement --module <each departmental_needs test file>` — one module at a time during red/green, one full sequential pass at the end, never concurrent with an active Playwright run (tracker rule 7).
2. `npx playwright test tests/ui/smoke/departmental_needs tests/ui/smoke/design-fidelity/departmental-needs-fidelity.spec.ts --workers=1` (plus any new Phase 2/3 spec files) — FU-01's single-fixture/single-worker constraint still applies.
3. `./scripts/bench-with-node.sh build --app kentender_core` (if `kt_industry_tokens.css` gained a class) then `--app kentender_procurement` — confirm bundle hash changed, `bench clear-cache`, hard-refresh.
4. Live golden-path walkthrough: all 9 DES-07A Planning-status variants + DES-12-UNAVAILABLE as real actors, not console-manufactured state alone.
5. `FOLLOW_UPS.md`: close FU-19 (all 3 remaining items), FU-25 (both items), FU-27, FU-28 in full; FU-26 updated to record its 2 in-scope items closed and its 3 out-of-scope items left exactly as written, naming why.
6. Tracker acceptance map: NDS13-AC-006 and NDS13-AC-008 move `Partial` → `Done`, cross-referenced against their original rows, not renumbered.
7. Site left on `make seed-canonical SITE=kentender.midas.com`; every test/browser record purged; Planning's own `NEED-PLNT-0001` residue noted but not swept (not this module's fixture).

## Verification (end to end)

1. Focused red/green per Phase 2/3 sub-item: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.departmental_needs.tests.<file>`.
2. Per Phase 1 screen edit: live browser check as the applicable seeded actor (`.env.ui` has credentials) — first paint and at least one interactive re-render, direct load, reload — plus a `-g`-filtered Playwright run for that screen's spec.
3. Phase 5: full Python module suite, full Playwright smoke suite, production build with hash-change confirmation, one full manual golden-path walkthrough covering every named variant.
4. Report per CLAUDE.md: behaviour/files changed, tests run with results, checks not run and why, remaining risks.

## Risks

- Phase 2 is the one item in this cycle that is genuinely new capability, not a port — budget real attention, and resist the temptation to fold REFRESHING/UNAVAILABLE/UNAVAILABLE-NO-SNAPSHOT into fewer states than the board specifies (the same caution v1.13's own R1 risk named for the first 5 variants applies to the remaining 4).
- Confirm the `.factstack-text`/`.factstack-meta` classes' presence (or absence) in `kt_industry_tokens.css` before writing them inline in `RequirementCard.vue` — same shared-file-first rule the `.is-info` addition set as precedent.
- FU-01 (shared fixture, single-worker requirement) still applies to every Playwright run in this cycle.
- Do not delete `design.zip` without the owner's confirmation on gitignore-vs-delete, even though the prior commit already recommended removal — it is untracked, outside this session's own working set, and deleting someone else's file without checking is the kind of action CLAUDE.md's own care rules ask to confirm first.
