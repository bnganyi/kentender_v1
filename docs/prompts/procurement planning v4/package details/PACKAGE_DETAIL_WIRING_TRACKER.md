# Procurement Package Detail — Wiring Tracker (PD1–PD14)

## Goal

Ship a real, pixel-accurate **Package Detail** page for the Procurement
Planning Workbench that replaces the currently-orphaned, plain-Bootstrap
"PP3" contextual surface. Today, clicking a package title anywhere in the
Workbench (In Creation / Awaiting Review / Ready for Release / Blocked /
Released queues) opens the raw Frappe desk form for `Procurement Package` —
a generic, technical form never designed for planners or reviewers. Done
looks like: every package title link opens one consistent, pixel-ported
detail page (Overview / Lines & Funding / Readiness / Review / Release
tabs) whose content and right-hand action panel adapt per package status
using the five new mockups, a working three-way review decision (Approve /
Return for Correction / **Request Clarification**, newly built) for the
Awaiting Review queue, and the existing PP2 backend services doing almost
all of the data/action work already — this is primarily a UI build + wiring
pass, not a new backend, following the same "port the real design onto
already-solid services" pattern used for the Package Creation Wizard
(`../package wizard/PACKAGE_WIZARD_WIRING_TRACKER.md`).

## Documentation read gate (mandatory before implementation)

- **Module pack**: `apps/kentender_v1/docs/prompts/procurement planning v4/package details/` — `DESIGN.md` (tokens/brand) + `1. in_creation/code.html` + `2. awaiting_review/code.html` + `3. ready_for_release/code.html` + `4. blocked/code.html` + `5. released/code.html` (all read end-to-end, `screen.png` reviewed for each) — this pass.
- **Cross-cutting docs also read this pass**: `../Procurement Planning — Operational Flow, States, and UX Rules.md` (§5, §9.7–§9.10, §10 data-model tables, state-map table ~L1083–L1091), `../workbench/WORKBENCH_WIRING_TRACKER.md` (full file — W1–W13, the "package-detail surface... needs its own explicit decision" gap at L314–L320, and the Title/Ref link-style pass), `../package wizard/PACKAGE_WIZARD_WIRING_TRACKER.md` (architecture precedent: dedicated Page, one shared shell, canonical-path legacy removal).
- **Tracker row**: none pre-existing for this surface as a first-class tracker (a "Phase D3"/"P6" package detail effort existed historically inside `WORKBENCH_WIRING_TRACKER.md`'s design-gaps section and its own `P6-*`/`P8-*` Playwright specs, but was never given a persistent tracker file and is now confirmed **superseded**, not resumed — see Scope decisions below). This file is the new canonical tracker for the package-detail surface, sibling to `../workbench/WORKBENCH_WIRING_TRACKER.md` and `../package wizard/PACKAGE_WIZARD_WIRING_TRACKER.md`.
- **Section map**:

  | Doc | Sections read |
  | --- | --- |
  | `DESIGN.md` | Full (tokens, brand, component rules) |
  | `1. in_creation/code.html` + `screen.png` | Full markup + screenshot |
  | `2. awaiting_review/code.html` + `screen.png` | Full markup + screenshot |
  | `3. ready_for_release/code.html` + `screen.png` | Full markup + screenshot |
  | `4. blocked/code.html` + `screen.png` | Full markup + screenshot |
  | `5. released/code.html` + `screen.png` | Full markup + screenshot |
  | Operational Flow doc | §5 (state list), §9.7–§9.10 (readiness/submit/review/release steps + decisions), §10.3/§10.4 data-model tables (Review Status, Decision, Comments, Release Status) |
  | `WORKBENCH_WIRING_TRACKER.md` | Full — queue→API mapping (Resumption checklist), W6–W8 title-link pattern, the unresolved package-detail-surface note |

- **Requirements digest**:

  | Source | Requirement | Plan impact |
  | --- | --- | --- |
  | 5 mockups, consistent 4/5 | Overview / Lines & Funding / Readiness / Review / Release tab set | PD3 canonical tab set (Released's 6-tab outlier reconciled to this set, see Design mapping below) |
  | `4. blocked/code.html` | Full-width blocker alert banner, per-blocker copy (design shows funding shortfall) | PD6 must generalize banner to all real blocker types (funding, readiness-failed, returned-for-correction), not just funding |
  | `2. awaiting_review/code.html` | Approve / Return for Correction / **Request Clarification** actions + reviewer comments + Assigned Reviewers panel | PD7 (3-way decision, net-new Request Clarification), PD8 (Assigned Reviewers simplified to real approver/rejecter history per user decision) |
  | `3. ready_for_release/code.html` | Release Checklist (6/6), Release to Tender, Download Release Certificate | PD5 reuses existing readiness + release services; certificate download is net-new (flagged, may defer per W11 precedent) |
  | `5. released/code.html` | Tender Link, Release Evidence, Recent Activity, decorative "Project Impact Area" card | PD5; Project Impact Area has no backing data model — flagged to omit (no fabricated content) |
  | Operational Flow §9.9 | Canonical review decisions are Approve / Return for Correction / Reject-Cancel — **no** "Request Clarification" | PD7 explicitly extends the canonical decision set; must add a real `Package Review Decision.decision_type` option + audit event type, not just a UI button |
  | `WORKBENCH_WIRING_TRACKER.md` W6–W8 | Title links today route to `/desk/procurement-package/<id>` (Frappe desk form) — a prior intentional decision | PD1/PD9 supersede this: all 5 queues' title links now route to the new detail page (user-confirmed) |
  | `pp2-legacy-removal` rule | One canonical path; remove/replace legacy | PD1 retires `pp3_planning_package_detail.js` + its route + its now-broken `P6-*`/`P8-*` Playwright specs, replacing them with PD-numbered equivalents against the new page |

- **Precedence**: PP2 canonical-loader rule applies — the new detail page is
  the **one canonical package-detail surface** going forward. The orphaned
  `pp3_planning_package_detail.js` / `get_pp3_package_detail` **JS delivery
  layer** is retired (not run in parallel); its **backend service layer**
  (`package_detail_view_model.py`, `package_review_api.py`,
  `package_readiness_api.py`, `package_release_api.py`,
  `package_review_service.py`, `package_readiness_service.py`,
  `package_release_service.py`) is sound and is reused/extended, the same
  way the wizard reused `package_wizard_service.py` rather than rewriting
  proven services.
- **Repo inventory (existing, to extend)**:
  - **Reused as-is (data/actions)**: `procurement_planning/services/package_detail_view_model.py` (`get_pp3_package_detail_view_model` — 5-tab payload shape), `procurement_planning/api/package_detail.py` (`get_pp3_package_detail`), `procurement_planning/api/package_readiness.py` + `services/package_readiness_service.py` (`run_pp_package_readiness_checks`, `evaluate_pp2_readiness_checks`), `procurement_planning/api/package_release.py` + `services/package_release_service.py` (`release_pp_package_to_tender`), `procurement_planning/api/workflow.py` (`submit_package`, `approve_package`, `return_package`).
  - **Extended (net-new)**: `procurement_planning/doctype/package_review_decision/package_review_decision.json` (+`Clarification Requested` to `decision_type` options), `procurement_planning/services/package_review_service.py` (+`request_clarification_on_package`), `procurement_planning/api/workflow.py` (+`request_clarification`), `procurement_planning/services/planning_audit_constants.py` (+`PACKAGE_CLARIFICATION_REQUESTED` event type).
  - **Retired**: `public/js/pp3_planning_package_detail.js` (delete once superseded), its mount path (confirmed unreachable already), `tests/ui/smoke/procurement/procurement-planning-package-detail-route-p6-001.spec.ts`, `...-package-detail-tabs-p6-003-015.spec.ts` (currently failing — confirmed via `npx playwright test ...p6-001...` this pass — reason: route never navigates, stays on `?package_code=` query string), `...-permissions-regression-p8-001-010.spec.ts` (verify scope before deleting — may cover permission checks worth porting rather than dropping outright).
  - **New**: dedicated Frappe Page (architecture below), its JS controller + CSS, `public/js/pp2_planning_router.js` title-link rewiring in `buildWorkbenchPackageQueueRow` / `buildWorkbenchReviewReleaseRow` / `buildWorkbenchBlockedRow` / `buildWorkbenchReleasedRow`.

## Scope decisions confirmed with user (2026-07-05)

1. **Rebuild fresh, don't re-skin PP3**: build a brand-new dedicated page
   (see Architecture below) rather than re-skinning
   `pp3_planning_package_detail.js` in place. The old surface's **backend**
   is still reused; only its JS/route delivery layer is retired.
2. **Rewire all "Open Package" links**: this tracker supersedes the
   previous session's "leave as-is" answer — all 5 Workbench queues'
   package title links (In Creation, Awaiting Review, Ready for Release,
   Blocked, Released) now navigate to the new detail page instead of the
   raw Frappe desk form.
3. **Request Clarification — build for real**: a genuine 3rd reviewer
   decision alongside Approve / Return for Correction. Requires a new
   `Package Review Decision.decision_type` value, a new whitelisted API, a
   new `Planning Audit Event` type, and a way for the planner to see the
   clarification question on the package (package stays in `In Review`,
   does not transition state — clarification is informational, not a
   blocking transition, pending confirmation in PD7).
4. **Assigned Reviewers — simplified**: do **not** build a multi-reviewer
   assignment data model. The Review tab / sidebar instead shows the
   package's **real** approver/rejecter/decision history (already captured
   in `Package Review Decision` rows: `decided_by`, `decision_type`,
   `decided_at`, `decision_reason`) — no fabricated named avatars, no
   "Principal/Assigned" role concept.
5. **One consistent tab set, but status-specific content/actions/sidebar
   preserved**: all 5 statuses share the same 5 tabs (Overview / Lines &
   Funding / Readiness / Review / Release) and the same page chrome
   (matching the already-shipped Workbench's own header/sidebar — not 5
   different navs). Within that shared shell, the **content** of each tab,
   the **blocker/alert banners**, and the **right-hand contextual action
   panel** (Workflow Actions / Reviewer Actions / Status Information /
   Tender Link, etc.) are genuinely status-specific and must be ported
   per-status as designed, not homogenized into one generic sidebar. See
   "Design → content mapping" below for the exact per-status breakdown.

## Architecture

- **Dedicated Frappe Page**, analogous to `create-package-wizard`
  (`../package wizard/PACKAGE_WIZARD_WIRING_TRACKER.md`), not a client-side
  sub-route embedded in the iframe-based Workbench SPA. Proposed route
  name: `package-detail` (query param `?package=<package_code>`), reached
  via `frappe.set_route("package-detail", { package: code })` from every
  Workbench queue row and from the package wizard's success screen "View
  Package" link (if one exists/gets added later).
  - Rationale: the five mockups have materially different, rich per-status
    layouts (blocker banners, review decision cards, release checklists,
    tender-link cards) that don't fit the Workbench's existing
    iframe/static-HTML row-cloning model; a dedicated Page mirrors the
    proven wizard pattern (own JSON/JS/CSS, `hooks.py` `page_js`/
    `app_include_css` entries, no `?v=` cache-busting per
    `frappe-bench-node.mdc`).
  - This is a **proposed** architecture consistent with the wizard
    precedent and the user's "rebuild fresh" decision; flag for a quick
    go/no-go confirmation at implementation kickoff if a different routing
    approach is preferred.
- One shared shell renders the Workbench-matching top nav + left sidebar +
  footer, the 5-tab bar, and a header block (title, status pill, ref code) —
  built once, not per status.
- Per status, the shell swaps in: (a) an optional top-of-canvas alert
  banner (Blocked only, today; extensible), (b) the active tab's body
  content, and (c) the right-hand contextual action panel — driven by
  backend-provided `status` + tab payload, not hardcoded per-status JS
  branches where avoidable.

## Design → content mapping (status-specific parts to port, per PD5/PD6)

| Status (backend `status` value) | Mockup source | Canvas content (beyond generic tab body) | Right sidebar panel |
| --- | --- | --- | --- |
| Draft (**In Creation**) | `1. in_creation/` | Package Identity (editable — pencil icon), Included Demands cards, Package Lines table | Package Summary (value/funding/lines), Workflow Actions (Run Readiness Checks / Modify Package), Evidence & History (View Evidence + activity timeline) |
| In Review (**Awaiting Review**) | `2. awaiting_review/` | Review tab pre-selected: Reviewer Comments, Approval Decision cards (Approve / Return), Final Review Summary textarea, Package Summary card | Reviewer Actions (Approve / Return for Correction / **Request Clarification**, net-new), "Package Locked" notice, Assigned Reviewers → **simplified** to real decision history (PD8) |
| Approved *(transient, no dedicated mockup)* | none — closest neighbor `3. ready_for_release/` | Reuses Ready for Release canvas with a status pill override + "awaiting readiness pass" framing; flagged gap, see Open questions | Workflow Actions scoped to "Run Readiness Checks" (mirrors In Creation's action, not full Release actions) |
| Ready for Release | `3. ready_for_release/` | Release tab pre-selected: Final Package Value / Method summary, Release Checklist (real readiness check list, not hardcoded 6/6), Tender Management Integration visual (decorative "AUTO-GENERATE SHELL"/"SECURE HANDOFF" copy — descriptive only, no separate actions) | Workflow Actions (Release to Tender / Download Release Certificate — certificate flagged, see Open questions), Package Readiness timeline |
| Returned for Correction / readiness Failed (**Blocked**) | `4. blocked/` | Overview tab pre-selected: **generalized** Blocker Alert banner (funding shortfall is the design's example; must also render for readiness-check failures and returned-for-correction reasons, sourced from the same `blocker_message`/`status_detail` values `planning_home_queues.py` already computes), Package Identity, Included Demands table w/ per-item status | Status Information (Locked for Editing + blocker severity), Workflow Actions (Resolve Blockers / View Funding Analysis / View Block History — funding-analysis and block-history flagged as new/needs scoping), Assigned Contacts → **simplified** to real package owner + last reviewer/decider (no fabricated stock-photo avatars) |
| Released to Tender / Consumed (**Released**) | `5. released/` | Release tab pre-selected: Success banner, Financial Handoff + Asset Package bento, "Project Impact Area" card (**decorative, no backing data model — omit**, flagged) | Tender Link (Open in Tender Management), Release Evidence (View Release Certificate — flagged), Recent Activity timeline |

## Status legend

Same as the other two trackers in this pack: ✅ Done (implemented, tested,
live-validated) · 🟡 Partial/in progress · ⬜ Not started · 🛑 Deferred
(explicit user decision) · ❓ Open question (needs a decision before this
item can start).

## Tracker

| # | Item | Scope | Status | Notes |
|---|------|-------|--------|-------|
| PD1 | Retire orphaned PP3 surface | Delete `pp3_planning_package_detail.js`; confirm no other reachable caller exists; delete/replace `P6-001`, `P6-003-015` specs (currently failing — confirmed this pass); triage `P8-001-010` (permissions) for content worth porting into the new page's regression suite before deleting | ✅ Done | `pp3_planning_package_detail.js` removed from `hooks.py` + disk; P6 Playwright specs replaced by `procurement-planning-package-detail-journey-pd11.spec.ts`; PP6/PP8 source tests retargeted to `package_detail_page.js` |
| PD2 | Dedicated Page scaffold | New `package-detail` Frappe Page (json/js/css/hooks), following the `create-package-wizard` pattern exactly (own module dir, `page_js`/`app_include_css` in `hooks.py`, no `?v=` cache-busting) | ✅ Done | Page `package-detail` migrated on `kentender.midas.com`; `package_detail_page.js` + `package_detail_page.css` + hooks wired |
| PD3 | Shared shell + tab bar | Port Workbench-matching top nav/sidebar/footer once; port the 5-tab bar (Overview/Lines & Funding/Readiness/Review/Release) shared across all statuses; header block (title, status pill, ref code, breadcrumb) | ✅ Done | In-content shell ported (`kt-pd-canvas`, inline title+pill, breadcrumb, 5-tab bar, 8/4 layout, institutional footer); Desk top nav/sidebar intentionally omitted (wizard pattern); tab switch updates `kt-pd-tab-host` only; evidence: `test_pd3_package_detail_shell.py` + P6-001 testids |
| PD4 | Overview + Lines & Funding tabs | Port Package Identity, Included Demands, Package Lines table content (from `1. in_creation/` as the base content reference, since it's the fullest Overview example); wire to `get_pp3_package_detail_view_model`'s `overview`/`lines_funding` tab payloads | ✅ Done | Mockup-level identity card (edit affordance, estimated value), included demands/lines table styling, draft sidebar Modify Package + activity timeline; evidence: PD11 direct route + `test_pp6_package_overview_p6_006` |
| PD5 | Readiness + Release tabs | Port Readiness tab (checklist from real `run_pp_package_readiness_checks` results, not the mockup's hardcoded "Passed (6/6)"); port Release tab (Final Value/Method summary, checklist, Release to Tender action) from `3. ready_for_release/` and `5. released/` (post-release state); wire to existing readiness/release services | ✅ Done | Release summary bento + readiness checklist on release tab; Approved state reuses release layout (`kt-pd-approved-note`); released handoff bento (no Project Impact Area); certificate buttons **deferred** per decision #1 |
| PD6 | Overview blocker banner (generalized) | Build one blocker-banner component driven by real blocker data (`blocker_message`/`status_detail` from `planning_home_queues.py`, readiness failure reasons, return reason from `Package Review Decision.decision_reason`) — not hardcoded to the funding-shortfall example in `4. blocked/` | ✅ Done | `blocker_banner` + blocked sidebar (`kt-pd-status-info`, funding notification stub, filtered block-history evidence drawer); `test_pd6_blocker_banner.py` + PD11b Playwright (returned + readiness variants) |
| PD7 | Review tab 3-way decision (Approve / Return / **Request Clarification**) | New `Clarification Requested` `decision_type` on `Package Review Decision`; new `request_clarification_on_package` service function + `request_clarification` whitelisted API; new `PACKAGE_CLARIFICATION_REQUESTED` audit event; package stays `In Review` (no state transition); planner-visible surfacing of the clarification note (Overview or Review tab); notify package owner (reuse existing notification pattern from DIA/PP2 if one exists, else a `frappe.sendmail`/Notification Log entry) | ✅ Done | `test_pd12_package_detail_clarification.py` (validation + audit + API); UI `kt-pd-clarify` + review clarifications list |
| PD8 | Review tab — real decision history (Assigned Reviewers simplification) | Replace mockup's fabricated named-avatar panel with a real read-only list of `Package Review Decision` rows for this package (decided_by, decision_type, decided_at, reason) | ✅ Done | `list_package_review_decisions()` + `kt-pd-decision-history-row` panel |
| PD9 | Rewire all 5 Workbench queue title links | `pp2_planning_router.js`: `buildWorkbenchPackageQueueRow`, `buildWorkbenchReviewReleaseRow`, `buildWorkbenchBlockedRow`, `buildWorkbenchReleasedRow` — title `<a>` now routes to `package-detail?package=<code>` instead of `/desk/procurement-package/<id>` (packages only; Blocked's demand-branch rows keep routing to `demand-workbench` as today — out of scope) | ✅ Done | `navigateToPackageDetailPage` + `buildPackageDetailUrl`; `test_pp4_workbench_package_queues_w6` / `test_pp4_workbench_remaining_queues_w7_w8` updated; wizard success link updated |
| PD10 | Role/permission gate audit | Confirm the reviewer-vs-authority action mismatch flagged in backend inventory (`package_detail.py`'s `_actions_for_workbench` restricts approve/return to `role_key == "authority"`, while the DocType controller and `resolve_pp_role_key` allow Planning Reviewer) is/isn't inherited by `package_detail_view_model.py`'s own action gating for the new page; fix if it is | ✅ Done | `_actions_for_workbench` now grants approve/return/clarify to `reviewer` role; `may_clarify` gated via actions map |
| PD11 | Playwright — one continuous journey per status transition | Following the "optimize for speed" testing decision established for the wizard: **one** journey spec that walks a package through Draft → In Review → (Approve / Return / Request Clarification branches) → Ready for Release → Released, asserting tab content + right-sidebar actions inline at each stage, rather than one spec per tab/status; a second spec for the Blocked banner (funding + readiness-failure variants) | ✅ Done | `procurement-planning-package-detail-journey-pd11.spec.ts` **6/6 green** — PD11a full lifecycle (submit→approve→readiness→ready→released) + PD11b banners + PD11c reviewer actions + shell/workbench tests |
| PD12 | Backend regression tests | New: `Clarification Requested` decision-type validation, `request_clarification_on_package` service test, audit event assertion, role-gate test (PD10 outcome), blocker-banner-source test (PD6) | ✅ Done | `test_pd12_package_detail_clarification.py`; `test_pd6_blocker_banner.py`; Planning Reviewer DocPerm read on `Procurement Package` + `Procurement Plan` (P2-014 gap fixed) |
| PD13 | Harmonize `WORKBENCH_WIRING_TRACKER.md` | Update W6/W7/W8 rows (or add a dated addendum, consistent with how PW7/PW11 additions were handled) to note title links now route to the new `package-detail` page, not the desk form; resolve the "package-detail surface... needs its own explicit decision" gap note (L314–L320) as **Rebuilt fresh, see `PACKAGE_DETAIL_WIRING_TRACKER.md`**; leave W9 (Selected Work Summary panel), W11 (Export/Evidence), W13 (Strategic Alignment/Insights) untouched — genuinely separate, still pending/deferred | ✅ Done | Resolution block L322–329 documents PD9 routing superseding W6/W7/W8 desk-form links |
| PD14 | Agent efficiency playbook compliance | Apply `.cursor/rules/kentender-agent-efficiency-playbook.mdc` throughout implementation (Playwright DNS/browser workaround, asset build/cache steps, architecture-confirmation checklist before writing UI code) | ✅ Done | Used `127.0.0.1:8000`, `./scripts/bench-with-node.sh` not needed (symlinked assets), no `?v=` on `page_js` |

## Open questions (flagged for confirmation before/at implementation start of the relevant item)

**Decisions confirmed (2026-07-05):**

| # | Topic | Decision |
|---|--------|----------|
| 1 | PD5 certificate buttons | **Defer** — no certificate backend in this tracker |
| 2 | PD6 funding actions | **Notification stub** |
| 3 | PD6 View Block History | **Filtered evidence drawer** |
| 5 | Approved state UI | **Reuse Ready-for-Release layout** |
| 6 | Released Project Impact Area | **Omit** |

Remaining open: **PD7 item 4** — clarification stays informational (`In Review` unchanged).

## Test plan summary (per the established "optimize for journeys" testing strategy)

- **PD11a** — one Playwright spec walking a single seeded package through
  every status transition, asserting the shared shell/tabs stay mounted
  (no full remount, no chrome flash — per
  `kentender-workspace-pattern-lock.mdc`), and that the right-sidebar panel
  and canvas content swap correctly at each status per the Design → content
  mapping table.
- **PD11b** — one Playwright spec dedicated to the Blocked banner's two
  variants (insufficient funding vs readiness-check failure), since that
  content is generalized in PD6 and is the highest-risk regression surface.
- **PD12** — backend `bench run-tests` coverage for the new
  `Clarification Requested` decision type, its service function, its audit
  event, and the PD9 title-link routing (can be asserted at the JS
  signature-string level the same way `test_pp4_workbench_package_queues_w6.py`
  does for the existing row-builders).
- No per-tab, per-button micro-specs — consistent with the user's explicit
  "the journey test is enough because we want to optimize" testing
  direction from the wizard work.

## Explicitly out of scope for this tracker

- W9 (Selected Work Summary panel), W11 (Export/Evidence UX at the
  Workbench-list level), W13 (Strategic Alignment/Workbench Insights data
  wiring) — all remain independently pending/deferred per
  `WORKBENCH_WIRING_TRACKER.md`, untouched by this tracker.
- Any change to the Package Creation Wizard (`PACKAGE_WIZARD_WIRING_TRACKER.md`)
  — separate, already-shipped surface.
- Multi-reviewer assignment data model (explicitly declined by the user —
  Scope decision 4).
