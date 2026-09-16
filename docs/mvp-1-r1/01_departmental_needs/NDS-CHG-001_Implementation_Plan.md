# NDS-CHG-001 v1.13 — Departmental Needs usability correction — implementation plan

## Context

The Project Owner approved the Departmental Needs Usability Amendment v0.1 (NDS-UX-001..010) on 13 September 2026 and had it consolidated into **NDS-CHG-001 v1.13** (`docs/mvp-1-r1/01_departmental_needs/KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1_13.md`, approved 15 September 2026; a companion `KenTender_NDS_Usability_Amendment_v0_1.html` is background only — v1.13 is the single authority). A full Claude Design pass has already produced the artboards (`design/Departmental Needs - Design Board.dc.html`, 15 `NDS-DES-` screens plus their declared state variants, on the `_ds/kentender-industry-…` bundle).

v1.13's own change register (§18.2) shows its delta over v1.12 is almost entirely §11 (the screen-composition rewrite) and §12.10 (the new action map): 105 of 115 acceptance criteria and the whole domain model/lifecycle/business-rule set are unchanged carryover from v1.10/v1.11. The live app (`kentender_procurement`, `departmental_needs` module) was rebuilt through NDS-CHG-001 v1.10 (closed 4 Sep 2026: schema retarget, the AUTH-ADR-001 v1.6 authorization cutover, 249 Python tests, 23 Playwright tests — see `IMPLEMENTATION_TRACKER.md`, superseded-in-tracking by this document) and has had scattered corrections since (context-strip harmonisation, "Review tasks" menu retirement, the Revision/Submission/Version counter rename). **Every §8.1/§8.2 contract v1.13 names already exists in `api.py` today** — verified directly, not assumed. The gap is presentation: the screens were never rebuilt against the explicit v1.13 §11 composition, several DES-14/DES-15 state variants have no screen coverage at all, and the module is missing the `design-fidelity` Playwright gate every sibling module (Budget/Planning/Requisitions/System-setup/Tender-prep) already has.

**Owner decisions taken during planning (15 Sep 2026):**
- **Scope = the §11/§12.10 screen rewrite plus only the server deltas the screens actually need.** The backend command/read surface is complete; Phase 2 is a small, targeted audit (fixture correction, AUTH v1.7 delta check against the v1.6 cutover already done), not a rebuild.
- **AUTH-ADR-001 v1.7's §16.3 13-step correction slice is compared against work already done**, not re-executed from scratch: the v1.10 cycle's Phase 2 (NDS-201..220, Gate NDS-G02) already replaced every `User Permission` read with the shared resolver, removed FY/PE dimensions, and implemented `selectable_financial_years()`/`list_need_create_targets()`. §16.3 v1.7's 13 steps are near-verbatim the same checklist. Phase 2 here re-verifies live, fixes only a genuine v1.6→v1.7 delta if one exists, and does not repeat completed work.
- Implementation started 15 Sep 2026 on the owner's instruction to run every phase without stopping.

## Baseline facts the plan relies on

- App/module: `kentender_procurement/kentender_procurement/departmental_needs/` (backend); `kentender_procurement/kentender_procurement/public/js/departmental_needs/` (frontend, root `DepartmentalNeeds.vue`). Desk page controller `public/js/departmental_needs_page.js` — already one `kentender_core.desk_page.register("departmental-needs", {...})` call (confirmed by direct read; no shared-runtime fix needed, unlike the pre-`desk_page` era other modules once had).
- Backend is complete against §8: `api.py` (113 lines) whitelists all 9 §8.1 reads (`resolve_needs_scope`, `list_needs_financial_years`, `list_need_create_targets`, `get_needs_workspace`, `get_departmental_need`, `get_departmental_review_task`, `get_needs_submission_state`, `get_current_accepted_need`, `check_accepted_need_withdrawal_dependency`) and all 12 §8.2 commands (`save_need_draft`, `submit_need_revision`, `return_need_revision`, `accept_need_revision`, `decline_need_revision`, `withdraw_unaccepted_need`, `create_accepted_need_successor`, `cancel_accepted_need_successor`, `request_accepted_need_withdrawal`, `decide_accepted_need_withdrawal`, `project_need_planning_usage`, `project_need_planning_disposition`). The one contract v1.13 names that does not exist yet, `validate_accepted_need_withdrawal_for_decision` (§8.3), is explicitly a **Planning-owned** "logical new contract" (NDS11-XD-003) — not this module's to build.
- Services: `services/permissions.py` (AUTH-ADR-001 resolver, rewritten in the v1.10 cycle), `services/context.py` (`selectable_financial_years`, `list_need_create_targets`, `get_needs_submission_state`, `resolve_creation_context`), `services/lifecycle.py` (all command logic + `check_withdrawal_dependency`), `services/usage.py` (`project_planning_usage`, `project_planning_disposition`), `services/workspace.py` (`get_workspace`, `get_need`, `get_review_task`, `get_current_accepted_need`), `services/events.py`, `services/my_work_provider.py`, `services/notifications.py`, `services/technical_read.py`.
- Frontend: 13 Vue components under `public/js/departmental_needs/components/` — `WorkspaceScreen.vue`, `NeedEditorScreen.vue`, `NeedDetailScreen.vue`, `ReviewTaskScreen.vue`, `WithdrawalReviewScreen.vue`, `NeedsTable.vue`, `ContextCard.vue`, `ContextPicker.vue`, `CreateTargetDialog.vue`, `RequirementCard.vue`, `ReasonDialog.vue`, `ConfirmDialog.vue`, `ReadonlyRow.vue`, `StatusPill.vue`. Data layer `data/needsApi.js`, `data/format.js` (+ `data/format.spec.js` vitest).
- Design system: `kentender_core/kentender_core/public/css/kt_industry_tokens.css` (`.kt-industry` scope) already has `.kt-notice`/`-icon`/`-body` plus `.is-warning`/`.is-critical`/`.is-live` modifiers, `.kt-disclosure*`, `.kt-timeline*`, `.card*`, `.dialog*`, `.table`, `.btn*`. Missing vs. the NDS design board: **`.is-info`** (used 4× in the board; confirmed absent by direct grep of the tokens file).
- Tests: 11 Python files (~254 tests) under `departmental_needs/tests/`; 5 Playwright specs (~27 tests) under `tests/ui/smoke/departmental_needs/`; 1 vitest spec. **Missing, unlike every sibling module**: `tests/ui/smoke/design-fidelity/departmental-needs-fidelity.spec.ts` (Budget/Planning/Requisitions/System-setup/Tender-prep all have one).
- Docs precedent: `docs/mvp-1-r1/03_budget/BUD-CHG-001_Implementation_Plan.md` + `BUD-CHG-001_IMPLEMENTATION_TRACKER.md` (phase table, gate register, phase rows, acceptance map — this plan mirrors that structure).
- Canonical seed: `make seed-canonical SITE=kentender.midas.com THROUGH=<stage>` (`kentender_core/seeds/canonical.py`). Dev site is disposable (memory: dev-site-teardown-allowed).
- `FOLLOW_UPS.md` (FU-01..24, plus a Planning-cross-reference FU-07 opened 2026-09-12) carries several items this pass will naturally touch: FU-23 (no FY filter on the workspace — DES-01 specifies one), FU-08/FU-12/FU-21 (menu/label items, confirm still correct), FU-19 (missing automated regression for the multi-OU create dialog, multi-FY browsing, save-draft-while-closed, and the missing fidelity gate).

## Phase sequence

Work phases in order; each phase's exit condition is its gate. Phases 1–2 are horizontal; Phase 3 is vertical per route (screen → browser), per the rebuild-sequencing lesson from Strategy/Budget.

| Phase | Name | Exit condition |
|---|---|---|
| 0 | Docs and tracker | This plan + `NDS-CHG-001_IMPLEMENTATION_TRACKER.md` in repo, mirroring the Budget/Strategy tracker structure; `FOLLOW_UPS.md` reviewed for items this cycle closes. No product code. |
| 1 | `[core]` design-system addition | `kt_industry_tokens.css` gains `.kt-industry .kt-notice.is-info` (mirroring the existing `.is-warning`/`.is-critical`/`.is-live` rules). |
| 2 | `[departmental_needs]` server deltas | NDS12-CHG-011 seed-fixture correction applied; §16.3 AUTH-ADR-001 v1.7 delta audited against the v1.10 cycle's already-completed cutover, genuine gaps (if any) fixed; §8.4/§8.5 presentation contracts confirmed. |
| 3A | Workspace route | DES-01/02 + DES-14 workspace variants + reader supplements ported into `WorkspaceScreen.vue`/`NeedsTable.vue`; FY filter added (closes FU-23). |
| 3B | Editor route | DES-03/04/08/15 + DES-14 editor variants ported into `NeedEditorScreen.vue`; canonical inline department selector (NDS13-CHG-003). |
| 3C | Detail route | DES-05/07/07A (9 Planning-status variants) + reader/technical supplements + DES-14 detail variants ported into `NeedDetailScreen.vue`/`RequirementCard.vue`. |
| 3D | Review task route | DES-06/09 + DES-13 return/decline dialogs + DES-14 review variants ported into `ReviewTaskScreen.vue`/`ReasonDialog.vue`. |
| 3E | Withdrawal route | DES-11/12 + DES-13 withdrawal dialogs ported into `WithdrawalReviewScreen.vue`/`ReasonDialog.vue`/`ConfirmDialog.vue`. |
| 4 | Release gate | New `departmental-needs-fidelity.spec.ts`; full Python module suite; full Playwright smoke suite; production build; `FOLLOW_UPS.md` + acceptance map updated. |

## Phase 0 — docs (no product code)

1. This plan and `NDS-CHG-001_IMPLEMENTATION_TRACKER.md`, mirroring `docs/mvp-1-r1/03_budget/BUD-CHG-001_*` structure (tracker rules, decision log, risks, gate register, phase rows, acceptance map — NDS11/NDS12-AC carried in aggregate per §15/§15.2, NDS13-AC-001..010 detailed per §15.3).
2. `IMPLEMENTATION_TRACKER.md` (titled "NDS-CHG-001 v1.10") and `03_NDS_Rebuild_Implementation_Plan.md` marked superseded-in-tracking — not deleted; they remain the evidence trail for the v1.10 authorization/schema cutover this cycle builds on.
3. `FOLLOW_UPS.md` reviewed; no new rows opened at Phase 0 (candidates for closure are handled at Phase 4 once the screens that would close them are actually built and verified, not marked closed speculatively).

## Phase 1 — `[core]` `kt_industry_tokens.css`

Add under `.kt-industry`, immediately after the existing `.kt-notice.is-live` rule:

```css
.kt-industry .kt-notice.is-info { border-left-color: var(--kt-color-accent-700); background: var(--kt-color-accent-100); }
.kt-industry .kt-notice.is-info .kt-notice-icon { color: var(--kt-color-accent-700); }
```

(The base `.kt-notice` rule already uses the accent palette — this modifier makes the class name the board uses resolve to the same visual result the base rule already gives, rather than substituting `.is-warning`/leaving the class unstyled.) `touch kentender_procurement/hooks.py` and every other app's `hooks.py` that imports this shared file is unaffected by an additive rule. Verify: `./scripts/bench-with-node.sh build --app kentender_core`, confirm hash changed, hard-refresh, visually confirm one `.is-info` notice (e.g. DES-11 request-withdrawal dialog) renders with a visible left border and icon tint, not the unstyled default.

## Phase 2 — `[departmental_needs]` server contracts (TDD; one `--module` per run)

**2a — NDS12-CHG-011 seed-fixture correction.** §11.8A/§14.6A's `NDS-SC-DISPOSITION-EXCLUDED` profile must use a *distinct* DHI Submission 2 (accepted by Mercy Kilonzo, 4 Jan 2027 14:00 EAT) rather than reusing the canonical 27 Nov Proceeding event's identity. Locate the profile in `seeds/profiles.py`/`seeds/kentender_mvp_r1.py` (§14.6A), give it its own submission/event identity separate from both the 27 Nov Proceeding event and the 5 Jan still-Active event. Test: extend `test_departmental_needs_seed.py` with an assertion that the EXCLUDED profile's disposition-event identity differs from the canonical Proceeding event's. No domain/lifecycle change — this is a fixture-only correction.

**2b — §16.3 AUTH-ADR-001 v1.7 delta audit.** Read the 13 steps above against `services/permissions.py`/`services/context.py` line by line. The v1.10 cycle's Gate NDS-G02 already closed steps 1–7, 11 as code, and live-verified (not yet checked-in-test) steps 8, 9, 10, 12, 13. Confirm each step still holds against the current code (nothing regressed since 4 Sep 2026); if steps 8/9/10/12/13 still lack a checked-in automated regression, add one (this closes part of FU-19). Do not re-implement anything already done — a row here that repeats completed v1.10 work is scope creep per this tracker's own rule.

**2c — §8.4/§8.5 presentation confirmation.** Confirm `save_need_draft`/`submit_need_revision` already support Submit without a forced prior Save (read `api.py::save_need_draft` — it already branches on Need presence, one call covers both create and update), and that `accept_need_revision`/`decline_need_revision` responses carry enough information for the client to choose "Accept for planning" vs. "Accept proposed changes" copy (kind: initial vs. successor). If either assumption is wrong, fix in `services/lifecycle.py`; otherwise this row closes with no code change, evidenced by the read.

Tests: new or extended cases in `test_departmental_needs_seed.py` (2a) and `test_departmental_needs_permissions.py`/`test_departmental_needs_lifecycle.py` (2b, if a genuine gap is found). Register purge cleanup per memory (always remove test data).

## Phase 3 — screens (Industry, artboard-literal, per route)

Shared rules for every screen, matching the existing components' own conventions (confirm by reading each component before editing, since these were already built once and should not be silently redesigned): root `class="kt-industry"`, `kentender_core.desk_page` route/sequence-guard pattern already in place, controlled inputs bound to local refs, `data-loading`/`data-refreshing` attributes for Playwright, `__()` on every string. Copy comes verbatim from v1.13 §11 (memory: labels name outcomes — the copy is already written in the spec, port it, don't rephrase).

For each route below: open the Design Board's artboard block(s) for that route, port class-for-class into the named component (Design wins on markup/classes; §12 governs behavior — a screen that gets its visual composition from §11 but its interaction rules from anywhere else is wrong per this tracker's own rule, mirrored from the v1.10 tracker's rule 5). After the route: live browser check as the applicable seeded actor (Grace/Peter/Julia/Mercy/Naomi — `.env.ui` has credentials) + one `-g`-filtered Playwright run for that route's existing spec file. Broad runs wait for Phase 4.

**3A — Workspace** (`WorkspaceScreen.vue`, `NeedsTable.vue`, `ContextCard.vue`/`ContextPicker.vue`)
DES-01 (Author "My needs"), DES-02 (HoD dual-table "Needs requiring your decision" / "All departmental needs"), DES-14 LOADING/EMPTY-AUTHOR/EMPTY-READER/FILTERED-EMPTY/CLOSED-WORKSPACE/DENIED/NO-OPEN-YEAR, reader supplements 01-SUBMITTED/01-RETURNED/01-PLAN-INCLUDED/01-PLAN-NOT-INCLUDED/01-OPEN-PROPOSAL/02-DUAL-ROLE. Add the Financial Year filter (closes FU-23) — a local, changeable filter per §6, never an authority gate.

**3B — Editor** (`NeedEditorScreen.vue`)
DES-03 (create), DES-04 (returned correction, "What needs to change" + History disclosure), DES-08 (propose changes to accepted, + DRAFT/SUBMITTED/RETURNED sub-cards), DES-15 (department-choice MULTIPLE/SINGLE/PERSISTED/NO-TARGET — canonical inline selector per NDS13-CHG-003; confirm whether `CreateTargetDialog.vue` is retired in favor of this or still has a live call site before assuming it's dead), DES-14 CLOSED-EDITOR/SAVE-FAILED/PARTIAL-SUBMIT/SUBMIT-UNKNOWN/QUANTITY-ERROR.

**3C — Detail** (`NeedDetailScreen.vue`, `RequirementCard.vue`)
DES-05 (submitted, read-only), DES-07 + the 9 DES-07A Planning-status variants (NONE/PROCEEDING/EXCLUDED/STILL-ACTIVE/RESTORED/OLDER/REFRESHING/UNAVAILABLE/UNAVAILABLE-NO-SNAPSHOT — the highest-density single item in this plan; each has genuinely distinct copy and evidence, not just a label swap), 07-PLANNER/07-AUDITOR/07-HISTORICAL and TECHNICAL-REGISTER/TECHNICAL-DETAIL/LONG-CONTENT/TERMINAL reader supplements, DES-14 MASKED-DETAIL/LOAD-FAILURE.

**3D — Review task** (`ReviewTaskScreen.vue`, `ReasonDialog.vue`)
DES-06 (initial review — Return for correction / Do not take forward / Accept for planning), DES-09 (review of proposed changes — "What changed" diff table, Return for correction / Decline proposed changes / Accept proposed changes), DES-13 RETURN-INITIAL/RETURN-UPDATE/DECLINE-INITIAL/DECLINE-UPDATE dialogs, DES-14 REVIEW-CHANGED/AUTHORITY-CHANGED. Apply §8.5's presentation split (distinct Accept/Decline copy for initial vs. successor) and drop any repeated Accept confirmation step per §8.5.

**3E — Withdrawal** (`WithdrawalReviewScreen.vue`, `ReasonDialog.vue`, `ConfirmDialog.vue`)
DES-11 (request dialog + REQUESTED/OPEN-UPDATE), DES-12 (review + CLEAR/UNAVAILABLE — the CLEAR variant enables Approve, the base DES-12 STILL-ACTIVE composition does not), DES-13 DECLINE-WITHDRAWAL/WITHDRAW-DRAFT/CANCEL-UPDATE/APPROVE-WITHDRAWAL dialogs.

## Phase 4 — release gate and evidence

- Add `tests/ui/smoke/design-fidelity/departmental-needs-fidelity.spec.ts`, following the Budget/Planning/Requisitions/System-setup/Tender-prep pattern (per AGENTS.md §6.6): resolve each artboard's state/placeholders, compare structural landmark order against the live route.
- `bench --site kentender.midas.com run-tests --app kentender_procurement --module <each of the 11 departmental_needs test files>` (one `--module` at a time during red/green per file; a full back-to-back pass once at the end, matching the v1.10 tracker's own NDS-901 approach — `bench run-tests` accepts only one `--module` value, no glob).
- `npx playwright test tests/ui/smoke/departmental_needs tests/ui/smoke/design-fidelity/departmental-needs-fidelity.spec.ts --workers=1` (FU-01: the 5 existing specs share one fixture Need, single-worker required).
- `./scripts/bench-with-node.sh build --app kentender_procurement`, confirm bundle hash changed, `bench --site kentender.midas.com clear-cache`, hard-refresh, live golden-path walkthrough (create → submit → HoD accept → propose change → withdrawal) plus 2–3 DES-14 error states.
- Repo scan: zero hits for any label this cycle replaces (confirm against §4.10's old-vs-new table if any pre-v1.13 label survives in source).
- `FOLLOW_UPS.md`: close FU-23 (FY filter now exists) and the multi-OU-dialog/multi-FY-browsing/fidelity-gate strands of FU-19 that Phase 2b/3B/4 close; leave the Planning-owned strand of FU-19 (none — FU-19 is entirely NDS-owned) and FU-07 (Planning disposition producer, cross-module) open.
- Tracker: NDS13-AC-001..010 each `Done` with a spec/test name or explicit gap; NDS11/NDS12-AC carried rows re-confirmed where a Phase 3 screen touches them.
- Site left on `make seed-canonical SITE=kentender.midas.com THROUGH=<appropriate stage>`; every test/browser record purged.

## Verification (end to end)

1. Focused red/green per Phase 2 sub-item: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.departmental_needs.tests.<file>`.
2. Per route after each 3x phase: `npx playwright test tests/ui/smoke/departmental_needs/<spec>.spec.ts --workers=1` plus a live browser click-through as the named actor (credentials in `apps/kentender_v1/.env.ui`), checking first paint and at least one interactive re-render, direct load, reload, back/forward, zero console errors.
3. Phase 4: full Python module suite, full Playwright smoke suite (new fidelity spec included), production build with hash-change confirmation, one full manual golden-path walkthrough.
4. Report per CLAUDE.md: behaviour/files changed, tests run with results, checks not run and why, remaining risks.

## Non-goals (recorded as follow-ups, not built)

Per v1.13 §18.3's own owner-dependency table — all explicitly outside this module's ownership:
- Planning-side `NeedPlanningDispositionChanged.v1` producer and the `validate_accepted_need_withdrawal_for_decision` withdrawal-transaction validator (NDS11-XD-001/003, Planning-owned).
- Usage-stream wire/versioning inspection (NDS11-XD-002, joint PLN/NDS).
- FU-30 cross-module quantity/float precision remediation spanning NDS/PLN/REQ/BUD (NDS11-XD-004).
- Shared SEED-module adoption (NDS11-XD-005).
- BUD v1.8 wording clarification (NDS11-XD-006, Budget's own doc).
- CFG native UOM/intake metadata verification (NDS11-XD-007).
- Existing-data reconciliation of stale hashes/quantities (NDS11-XD-008) — unless Phase 2/3 work surfaces a concrete instance.
- REQ/TPR sibling review (NDS11-XD-011), citation cleanup (NDS11-XD-012).
- Shared technical search/conformance registration gap in AUTH v1.7 itself (NDS13-XD-015) — flag, don't attempt to build AUTH's side.
- Representative-user usability testing (NDS12-XD-002) — explicitly flagged in the spec as unproven by this build phase alone.

## Risks

- DES-07A's 9 Planning-status variants are the highest-density single item — budget real attention, don't compress into a handful of generic states.
- `.is-info` and any other class gap found mid-port goes into `kt_industry_tokens.css` (shared, low-risk) — never substitute a different existing class to avoid a core-CSS touch.
- Confirm `CreateTargetDialog.vue`'s actual call sites before assuming NDS13-CHG-003 retires it outright.
- Keep the Phase 2b AUTH delta audit genuinely scoped to v1.6→v1.7 deltas — re-doing the v1.10 cutover would be exactly the wasted effort this plan exists to avoid.
- FU-01 (shared fixture, single-worker requirement) still applies to every Playwright run in this cycle — never run with default worker count.
