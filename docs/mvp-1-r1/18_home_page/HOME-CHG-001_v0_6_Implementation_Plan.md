# HOME-CHG-001 v0.6: Home, implementation plan

| Control | Value |
|---|---|
| Version | 0.6-plan.1 |
| Date | 4 October 2026 |
| Authority | `KenTender_HOME-CHG-001_Home_v0_6.md`, **"Approved — 4 October 2026"** (HOME v0.6 control table). Approval record: Project Owner, verbatim "Yes", answering "Shall I apply this pass, and then approve KT-STD v1.22, HOME v0.6 and ANL v0.8 together?". Approval does not establish implementation, owner-feed readiness, seed execution, testing or production readiness. |
| Governing standard | KT-STD-001 v1.22, approved 4 October 2026 (`../00_common/KenTender_KT-STD-001_Document_Design_and_Verification_Standards_v1_22.md`). |
| Version set | HOME 0.6; KT-STD 1.22; OVS 0.6; AUTH 1.11; CTX 1.1; TPR 0.17; BOP 0.11; EVL 0.5; AWD 0.5; REQ 1.14; NDS 1.16; PLN 1.29; BUD 1.12; STR 1.9; SEED 1.4; SEED-OPS 1.24 (latest; no v1_25). ANL 0.6 is cited by HOME; ANL 0.8 exists only outside the repository (FU-HOME-05). |
| Design | `design/Home/Home.dc.html` (16 boards: HOME-DES-21, 21N, 22–25, 26, 26B, 27, 28A–28F, 29), `design/Home/DS additions.dc.html`, `design/Home/ds-additions.css` (headed "not approved" and stale against the accepted render), `design/_ds/kentender-industry-82d82607-…` (design system DS-REV-002). The `.dc.html` markup is the build source. |
| Companions | `HOME-CHG-001_v0_6_IMPLEMENTATION_TRACKER.md`; `HOME-CHG-001_v0_6_FOLLOW_UPS.md`. Phase 0 adds `reconciliation/`. Later: `evidence/v0_6/`. |
| Predecessor | None. The existing `my-work` page and the legacy `kt-procurement-home` dashboard are different things (see Current state) and are not predecessors of this design. |
| Prepared | 4 October 2026 (current-state reading done the same day, source read-only; dev site queried read-only) |
| Status | Phases 0, 1A, 2, 3, 4 and 6 done (Gates HOME-G00, G01A, G02, G03A, G03B on 4 October 2026; G04 and G06 on 5 October 2026). Phase 7 is retired from this change by the owner. Phase 1B (the rest of the repository) is on hold. Home is live on the test and dev sites; Phases 5, 8 and 9 remain. |

## Context

**Why this change.** Home is the internal landing page that answers what needs my action, what blocks it, who I am waiting for, what remains outstanding in records I oversee and where my completed action is. Today the closest thing is a three-tab My Work page that lists tasks only, and a sidebar item "Home" that opens the Coming soon page.

**What HOME v0.6 requires, in one paragraph.** A read-only, server-composed page at `/app/home` in `kentender_core`. Header (greeting by site time, every active responsibility with scope, Updated instant, **Technical record search** for technical readers). Summary row of up to three counts (actions, waiting, oversight), each complete or **Count unavailable**. Main column: My work then Coming up (14 calendar days). Rail: Waiting on others, Records you oversee, Recently completed actions. Five rows per region with in-place **Show more**, relative labels computed server-side with the exact time always shown, and five failure/empty/loading/denied states. It creates, clears and marks read nothing.

**What is not in the request.** No new task, decision, approval, permission or stored business field. No charts or aggregates (those are Analytics). No browser-computed counts, labels or deadlines (HOME §16).

### What slowed earlier modules, and the rule here

| Evidence | Rule here |
|---|---|
| Verification left to the end produced late rework (`feedback-rebuild-phase-sequencing`). | Phases 0–2 are horizontal; from Phase 3 each phase is a vertical slice ending in a live check as a named persona. |
| A green E2E missed a scope bug because fixtures mirrored the code's own persona assumptions (`playwright-fixture-realism-gaps`). | Disclosure and clearing are tested through the real endpoint as the real persona (Charles, Brian, Amina, Peter, Daniel, Jane, Naomi), and one spec per slice is driven from the menu, not by address (`feedback-walk-from-the-menu`). |
| Tests write real rows with no rollback and have wiped site data. | Test site only; shared test worlds per module (`feedback-shared-test-worlds`); never run Python while Playwright is active; reseed after runs that persist. |
| A rewritten published contract broke callers. | Before reshaping any hook, grep the whole repository for callers (`kt_my_work_providers`, `home_page`, `kt-procurement-home`). |
| Design-tool regeneration and "port class-for-class" drifted (`feedback-use-artboards-literally`). | The board is ported literally; every departure is a registry entry with a reason and an authority. |
| Edits to CSS/JS looked like code defects when assets were stale (`frappe-css-cache-bust-hooks-import`). | Verify the `?v=` hash changed and `getComputedStyle` before screenshotting. |

## Current state (verified 4 October 2026 by reading source; dev site queried read-only)

Paths are relative to the repository root unless stated.

**Nothing named Home exists in the new sense.** No `GetHomeWorkspace`, no `/app/home` page, no `kt_home_providers` hook, no `coming_up` or `recently_completed` symbol anywhere.

**My Work (the nearest existing thing).**
- `kentender_core/kentender_core/services/my_work.py`: `get_my_work()` merges provider results through the `kt_my_work_providers` hook into `{assigned, claimable, waiting}`. It skips every provider for technical readers, **catches and logs each provider failure** (so partial is indistinguishable from empty), counts rows (so counts equal returned rows), and has no cursor. `patch_bootinfo_home` (`kentender_core/hooks.py:62`) sets `bootinfo.home_page = "my-work"` for users with an active Operational Scope Assignment.
- Provider hooks: Needs, Planning, Requisitions, Tenders, Bid Opening, Evaluation, Award (`kentender_procurement/hooks.py:630-640`), Budget (`kentender_budget/hooks.py:48`), core support issues, supplier accounts. **Strategy has none.**
- Row keys: `task_id, task_type, title, reference, module, stage, organisation_unit, status, received_at, due_at, action_label, route[], route_options{}, comment`, with optional `holder`/`since` objects. `due_at` is `""` in every module provider. Titles are composites ("Prepare professional opinion for TND-…"). Waiting is hard-coded empty for Requisitions and Award. Award builds a `holder` and drops it. There is no structured blocker reason. Module labels are inconsistent ("Procurement Planning", "Bid Opening", "Budget & Funding").
- Page `my-work` is vanilla jQuery in `kentender_procurement` (`page/my_work/`), not Vue and not `desk_page.register`.

**Legacy "Procurement Home"** (`kt-procurement-home`, `procurement_home/` services, `public/js/procurement_home_page.js`, hidden Workspace `Procurement Home`) is a PE/FY portfolio dashboard. It has nothing to do with HOME-CHG-001. It carries uncommitted CTX v1.1 edits (single site entity, selector removed) that belong to another change.

**Sidebar.** `workspace_sidebar/procurement.json` item "Home" points at `coming-soon`; `setup/sidebar_availability.py` lists it in `PLANNED_SIDEBAR_LABELS`; `test_procurement_sidebar_g0_012_contract.py` guards both.

**Route collision, confirmed.** On `kentender.midas.com` (apps: frappe 16.12.0, erpnext 16.10.1, all kentender apps) the public, non-hidden Workspace `Home` (app `erpnext`) exists. `frappe/public/js/frappe/router.js` resolves `frappe.workspaces[route[0]]` first (line 171) and also falls back to `frappe.workspaces["home"]` when choosing a default route (line 489). A Page named `home` would never load.

**Shared contract available.** `kentender_core/services/next_step.py` defines answer kinds `your_turn`, `your_turn_blocked`, `waiting`, `timed` (Scheduled), `done`, `not_involved`, with `holder()`, `since()`, blockers and fixes. It is per record, not a cross-record feed. Per-Tender oversight summaries exist behind the `kt_tender_stage_summaries` hook (`tenders/services/stage_summary.py`; Opening, Evaluation and Award providers) with an `outstanding` field. No cross-record "Records you oversee" read exists, and OVS is itself not yet "implemented" (its tracker).

**Authority and instants.** `kentender_core/services/authorization.py::diagnose_user(user, at)` returns active assignments with business role, organisation unit and period, plus `technical_read_all`. `is_technical()` covers Administrator and System Manager; **Technical Operator is a site-scope business role it does not cover**, although HOME §6 treats it as a technical reader. There is no internal-user helper (`user_type == "System User"` is the existing test). `utils/instants.py` and `utils/display.py` hold site-time helpers; there is no relative-label helper. `services/test_clock.py::current_instant()` is the trusted clock.

**Page pattern.** `kentender_core/public/js/kt_desk_page.js` (`desk_page.register`, `useRoute`), the smallest complete core page `technical-search` and the newest `procurement-meetings` give the full file skeleton: page JSON, `page_js` hook, controller, bundle, root `.vue` with `.kt-industry`, `frappeCall` adapter (`silent: true`), API, service, Vitest project, Python tests, Playwright spec.

**Design system.** `kentender_core/public/css/kt_industry_tokens.css` (1,041 lines, scoped under `.kt-industry`) is the **old revision**: Barlow fonts, ground `#f0f2f7`, radii 2/4/7, buttons `.kt-btn*`, rust links, 1 px focus ring, `.kt-kpi-card` as a bordered card with a top bar. It has no `--color-figure`, `.kt-icon-chip`, `.kt-spot`, `data-seq` tokens, Inter or `kt-icons.svg`. The Home pack's `_ds` is DS-REV-002 (Inter, `--color-figure #1b2c68`, 4/8/12 radii, `.btn*`, indigo links, 2 px focus ring), which KT-STD v1.22 §2.4 already requires. The Home pack's `_ds/styles.css` differs by hash from every other module pack, so the Oversight, Award, Evaluation, Opening and Bid Submission boards are on an older revision.

**Board.** All 16 spec artboards are present and their text matches the spec (HOME-DES-21 and 29 checked line by line). `Home.dc.html` has about 1,000 inline `style` attributes and about 15 class names (`kt-icon`, `kt-icon-chip`, `kt-kpi-*`, `btn btn-*`, `kt-status`, `kt-spot`). It links neither `ds-additions.css` nor uses its classes. Its only script is the canvas zoom. Focus moves, Show more, Try again and the 960 px reflow are static pictures.

**Seed.** SEED-OPS-001 v1.24 and SEED-001 v1.4 do not mention Home. The canonical world has one Tender ("Supply and delivery of business laptops"), one Requisition, four Needs (one, `NDS-MOH-2027-0002`, still Submitted for Peter), four bids and one award. Demo profiles are mutually exclusive named states with a site-wide test clock; loading one rebuilds the Planning namespace, so a composite Home world cannot be made from profiles. Evaluation has no profiles. Mapping of the spec's scenarios: H2, H4, H7, H9B from canonical data (H2 with `AWD-DEMO-OPINION` and the clock at 16 Jun 16:00); H11, H10, H12 one row each; H1, H3, H8 and the rest of H10/H12 synthetic, built through owner commands; H5, H6, H9A are injected failures, not seed data. The canonical award week (16–18 June 2027) matches the spec's read times; the real date is 4 October 2026, so all seeded rows are future-dated and Home must read the trusted clock.

**Analytics and report destination.** ANL-CHG-001 is not in the repository (v0.6 approved; v0.6 and v0.8 copies in the owner's Downloads; v0.8 still reads "Proposed"). No analytics page, verdict or code exists. EVL v0.5 has `ReadEvaluationReport` but no version-addressed delivered-report route.

**Working tree.** Heavily modified by other work (OVS, CTX v1.1, Budget, Requisitions, Award, Evaluation). HOME v0.6, KT-STD v1.22, the OVS folder and the approved v1.x documents are untracked. The baseline register has no HOME or ANL entry and still lists KT-STD at v1.15.

## Owner decisions (recorded 4 October 2026)

- **OD-1 Route.** Owner answer: "Keep /app/home, retire ERPNext's Home workspace (Recommended)". A migrate patch hides the ERPNext `Home` workspace.
- **OD-2 Landing.** Owner answer: "Home becomes the landing page; My Work retired once Home covers it (Recommended)". Home replaces the `my-work` boot landing and the sidebar "Home — coming soon"; My Work is removed only after Gate HOME-G08.
- **OD-3 Design system.** Owner answer: "Adopt DS-REV-002 repo-wide first". The shared Industry stylesheet moves to DS-REV-002 before Home is built; every existing Industry page is restyled.

## Key technical decisions

- **D1 Composition by hook.** Core cannot import procurement. New hook `kt_home_providers`; each owner supplies typed entries for the regions it can honestly fill. Owners wrap their existing guards and `next_step`; Home recomputes no guard (HOME §3). `kt_my_work_providers` and `my_work.py` are left unchanged; the swallow of provider errors stays there and is not copied.
- **D2 Entry schema.** Transient, in `kentender_core/services/home_entries.py` (no DocType): region, owner module key, module label, root, action id, business title, action text, reason, holder, since, due, scheduled-at, completed-at, reference, destination, source revision. Identity is owner + root + exact action. The same work is not duplicated between My work and oversight (My work wins).
- **D3 `GetHomeWorkspace`.** `api/home.py` is thin; `services/home_workspace.py` composes. Inputs are per-region cursors. Output: responsibilities, complete counts (or unavailable), five-row pages with opaque cursors, coverage per region and provider (a failed provider is not a missing module), greeting, relative labels, Updated instant. A partial provider set yields usable rows and no total. Retry reads a region, or all regions after total failure. Nothing is cached past a failed permission verdict.
- **D4 Destinations.** Owner-supplied route plus arguments; core validates owner and viewer on the server. A destination that has since cleared opens the current permitted record with the owner's explanation.
- **D5 Gating.** Page JSON `roles: []` with an in-page internal-user gate rendering the denied state; one server call returns verdict and data (no render-then-deny). A new core helper classifies technical readers (Administrator, System Manager, Technical Operator): header link only, no business entries, no counts.
- **D6 Page pattern.** Copy `technical-search` and `procurement-meetings`: one `desk_page.register`, the app's own `useRouteState()`, bundle binding `globalProperties.__`, root `.kt-industry`, `frappeCall` with `silent: true`, no `cl_surface_registry` (AGENTS.md §6.5; it governs over the older KT-STD §4 wording, FU-HOME-11). The route stays mounted across navigations; skeleton only when nothing to show; revalidate in place; controlled inputs bind to the caller's selection.
- **D7 Gated links.** "See all in Procurement Analytics" appears only when an Analytics verdict permits it. No verdict exists, so it is absent until ANL ships; HOME-AC-14 is satisfied by omission and recorded as such. "View report" (HOME-DES-23) is a `Blocked — owner` row until EVL names the delivered-version route; no route is invented.
- **D8 CSS.** One static `public/css` file registered in `hooks.py` (scoped `<style>` is discarded by esbuild); `touch hooks.py` after any CSS edit; verify the `?v=` hash.
- **D9 Design-system adoption has no aliases.** KT-STD §10 forbids compatibility aliases, so Phase 1 migrates every `.kt-btn*` consumer to `.btn*` rather than keeping both.
- **D10 Time.** Site time throughout; relative labels are site-timezone calendar days from `test_clock.current_instant()`; UTC only in serialised messages (`utils/instants.py`). Overdue appears only when an owner deadline has passed.
- **D11 Page name.** `home`, module Kentender Core. The ERPNext workspace is hidden by patch (OD-1), not renamed around.

## Phases

The loop for every phase: red (smallest failing test), green, refactor, module tests once, phase gate, tracker row updated in the same step. A passing narrow test does not close a row whose acceptance criterion is broader.

**Phase 0: Reconcile (documents only).** File the plan, tracker and follow-ups. Write `reconciliation/`: `owner_feed_matrix.md` (per owner: action title, business title, due, holder, reason, completed event, scheduled item, destination, owner-document section, gap); `board_vs_spec.md` (module chip fill, teal `--data-seq` badge versus "tinted badge", Show more drawn as a ghost button versus "text action", 21N padding and untinted chip, 28B label, 27 link order, 26B static outline, rail divider); `conflicts.md` (H10 versus H12 on Tender 042, §10B.2 "held by" versus the brief "from", wording differences with owners); `hook_inventory.md` (every caller of `kt_my_work_providers`, `home_page`, `kt-procurement-home`, the `Home` workspace); `seed_scenario_map.md`; `ac_map.md` (HOME-AC-01–14 verbatim). Add make scaffolding (`home-preflight`, refusing while Playwright runs). **Gate HOME-G00:** reconciliation files exist, every FU cited exists, no code written.

**Phase 1: Adopt DS-REV-002 repo-wide (owner-gated).** Diff `_ds/…/styles.css` and the manifest's 114 tokens against `kt_industry_tokens.css`. Port Inter (self-hosted fonts), ground and surface tokens that read Frappe v16 variables with fallbacks, radii, 2 px focus ring, `--color-figure`, links in accent-700, `.btn*`, `.kt-icon-chip`, `.kt-spot`, `.kt-status`, the new `.kt-kpi-card`, the `data-seq` chart ramps, the icon sprite, and three missing icons (clock, list-checks, calendar-clock). Migrate every consumer of replaced classes (grep count recorded before and after). Add the §2.4 Frappe-variable upgrade test. Capture before and after screenshots of every existing Industry page for owner review. Re-run `make ui-industry-design-gate`, `ui-structure-gate`, `ui-fidelity-gate` and the bundle gates; update fidelity departure registries where an older board now differs, each with a reason. **Gate HOME-G01 (owner):** approves the restyle. Phases 2 and 3 do not depend on it; Phase 4 does.

**Phase 2: Core contract and service (horizontal).** Fake-provider tests first: schema validation; hook runner returning coverage verdicts (applicable, complete, partial, unavailable, module absent); identity and dedupe; §5 ordering (overdue, dated, then oldest undated, stable tie-break; waiting oldest first; oversight outstanding-first); five-row cursors and complete counts independent of page size; relative labels and Overdue-only-from-deadline; greeting by site time; responsibilities line from `diagnose_user`; internal and technical gates and the Technical Operator helper; destination validation; trusted clock; reads create nothing. Then the `GetHomeWorkspace` endpoint and per-region retry. **Gate HOME-G02:** contract suite green on `kentender-test.local`.

**Phase 3: Owner feeds, vertical slices.** Each slice: provider tests against the owner's own guards first, then the provider, then registration in the owner's `hooks.py`, then a negative case as the real persona through the real endpoint, then a repository-wide caller grep.
- **3A Tenders, Bid Opening, Evaluation, Award.** Tender hand-offs, waiting and completed submission/approval events, clarification blocked reason ("Issue an addendum before sending this answer."); Opening's Scheduled "Start opening"; Evaluation's appointment and statutory deadline; Award's opinion, notice and decision (and stop dropping `holder`); Records you oversee from `kt_tender_stage_summaries`. **Gate HOME-G03A.**
- **3B Requisitions, Needs, Planning, Budget, Strategy.** Each owner's existing task rows reshaped into entries; a new Strategy provider. Owners with no scheduled source (Planning, Strategy, Budget) contribute none and that is logged, not invented. **Gate HOME-G03B.**
- Completed-action events have no source today; row HOME6-0307 decides the source (audit or business-action events) before any owner adds one.

**Phase 4: Page shell (needs HOME-G01).** Page JSON, `page_js` hook, `home_page.js`, bundle, `Home.vue` and components in the board's order: header row, summary columns (whole column is the focus target), work row, rail row, relative-date badge, warning callout, Show more (append in place, focus to the first appended row, live region, count unchanged), per-region Try again, 12-column grid, container-query reflow below 960 px, empty-rail and empty-main rules, and states 28A–28F. Vitest project `home` (also added to the structure-gate list). First paint and one interactive re-render verified. **Gate HOME-G04.**

**Phase 5: Wire and browse.** Real data through the page per persona; one Playwright spec per slice from the menu; direct load, refresh, back/forward, forced-500, zero console errors. **Gate HOME-G05.**

**Phase 6: Routing and landing.** Patch hiding the ERPNext `Home` workspace (and check the router's `frappe.workspaces["home"]` default-route fallback still resolves for users without a `home_page`); sidebar item to the page and out of `PLANNED_SIDEBAR_LABELS`; `boot_session` landing switched; contract tests updated; `bench migrate` flagged. My Work removal waits for HOME-G08. **Gate HOME-G06.**

**Phase 7: Seed and fixtures.** A Home fixture module building H1, H3, H8, H10, H11, H12 through owner commands as named actors (never overwriting the canonical Tender), H2 from `AWD-DEMO-OPINION`, injected failures for H5/H6/H9A, per-scenario test-clock instants, release in `canonical.release_demo_profiles()`, Makefile targets, `test_canonical_seed.py`, and SEED-OPS-001 v1.25 under the document-change protocol (check the latest version first). H12's Tender 042 gets its own binding. **Gate HOME-G07.**

**Phase 8: Release evidence.** `tests/ui/fidelity/departures/home.js`, `home-fidelity.spec.ts`, `make ui-home-fidelity-gate`, a `fidelity-affected.sh` rule, artboard-provenance header; all 16 boards compared; keyboard and 200% zoom; production-mode build; persona pass; acceptance map closed with evidence. **Gate HOME-G08.**

**Phase 9: Owner-gated and deferred (all `Blocked — owner`).** EVL delivered-report destination; Analytics verdict and tab; Contract Management provider; owner-document feed amendments (HOME §17.1); ANL v0.8 filing and approval; register entries for HOME, KT-STD v1.22 and ANL.

## Conflicts and follow-ups to log (Phase 0)

| ID | Conflict | Disposition |
|---|---|---|
| C1 | `/app/home` collides with ERPNext's `Home` workspace | OD-1; Phase 6 |
| C2 | Repo CSS is DS-REV-001; KT-STD v1.22 §2.4 and the board are DS-REV-002 | OD-3; Phase 1 |
| C3 | KT-STD §4 says register routes in `cl_surface_registry`; AGENTS.md §6.5 and OVS D10 say not to | AGENTS.md governs; FU-HOME-11 |
| C4 | H10 has Tender 042 as an opening on 25 June; H12 has 042 as an evaluation appointment received 14 May, yet "shares the H10 world" | Separate binding; FU-HOME-08 |
| C5 | Owner action wording differs from HOME (Authorise requisition vs Decide whether to authorise; Appoint the evaluation committee vs Appoint evaluation committee for {tender}; need-review headline vs Review need) | FU-HOME-03 |
| C6 | No owner defines a Home feed except BOP's Scheduled item | FU-HOME-01; build under existing hand-off registers, workflows unchanged |
| C7 | Technical Operator is not covered by `is_technical` | Phase 2 helper; FU-HOME-15 |
| C8 | `ds-additions.css` is stale and unapproved | Superseded by Phase 1 and the board; FU-HOME-10 |

## Risks

- Phase 1 restyles every module and the other modules' boards are on an older revision, so fidelity gates may need departure entries; screenshots go to the owner before the gate closes.
- Owner feeds touch nine modules whose documents lack a Home contract. A feed must not alter a workflow, add an owner task or add a stored field.
- Completed-action events have no source today; audit data may be too thin for the wording HOME requires.
- Hiding the ERPNext `Home` workspace could change the default route for users with no `home_page`; Phase 6 verifies this before the patch ships.
- Test runs persist rows with no rollback; reseed after, and never during a Playwright run.
- The tree is dirty with other work; Home stages only its own files. No commit unless the owner asks.
- Dev code is live at once: any migrate, patch or seed need is flagged the moment it arises, and dev's real state is reported at the end of every task.

## Verification

- Python: `bench --site kentender-test.local run-tests --app kentender_core --module <focused module>`, then the module once; owner provider tests per module; `make home-preflight` first.
- Component: `npx vitest run` on the `home` project.
- Browser: `scripts/test-site.sh run npx playwright test <spec> --workers=1`; check `make ui-queue-check` before reading code on an odd UI failure.
- Gates: `make ui-industry-design-gate`, `make ui-structure-gate`, `make ui-home-fidelity-gate`, bundle translation-binding gate.
- Assets: `./scripts/bench-with-node.sh build --app kentender_core` (never plain `bench build`); `touch hooks.py`; clear cache; confirm the bundle hash changed.
- Live: dev site as each persona from the sidebar; record the exact rendered strings. `bench migrate` is needed for the page and the workspace patch.

## Build findings

**4 October 2026: Phases 2 and 3.** Decisions made while building, each also in the tracker or follow-ups; phase text above is not rewritten.

- **Provider contract (refines D1, D2).** `kt_home_providers` lists dotted paths to `entries(*, user, region)`. A provider returns `None` (region does not apply), a list (applies; possibly empty) or raises (a failed read). Applicability is decided by responsibility, not by having rows. Core reads each region from every provider, merges the full lists and decides coverage, counts, order, window, de-duplication, paging and every phrase. Written down in `reconciliation/provider_conventions.md`.
- **Counts.** `count` is the summary figure and `total` is every row the region can show. For Records you oversee `count` is outstanding records only (the column reads "records with outstanding matters"); both are `None` unless coverage is complete. Paging uses an opaque keyset cursor (the sort position of the last row), so a list that changes between pages neither repeats nor skips a row.
- **Windows.** Coming up is the read date plus 14 calendar days, inclusive. Recently completed actions is the last 30 calendar days (a build interpretation pending the owner, FU-HOME-23).
- **Completed source.** Each owner builds its entries from its own decision rows; Audit Event and Business Action were rejected (FU-HOME-13). Sentences are `home_time.completed_sentence`, with the awaiting clause only while the owner's current answer is a wait on a holder (FU-HOME-24).
- **Oversight.** Only where an owner has a concept: Tenders, Evaluation (status-only before delivery), Award, Needs (derived, not an owner concept), Budget and Strategy (derived, narrow). Opening, Requisitions and Planning return None. Core never lets a provider widen an owner's disclosure rule.
- **Per-read memo.** `home_support.memo` keeps one scan per read; `get_workspace` resets it first, so nothing outlives a read.
- **Destination check.** The first segment must be a real Page the viewer's roles may open (`Has Role` and custom roles); a failing entry is dropped and the region reads partial.
- **Parallel build.** Providers for Award, Requisitions and Needs, Planning, and Budget and Strategy were written in parallel; every test run on the shared test site went through one file lock (`/tmp/home-test-site.lock`) because earlier parallel runs collided on database locks. Procurement hook paths were registered by the lead after the agents finished.
- **Existing owner files edited:** `tenders/services/handoffs.py` (additive wording tables and three helpers), `procurement_planning/services/my_work_provider.py` (a generator `plan_handoff_items`; the old function is a wrapper with the same output), `kentender_core/services/authorization.py` (one public function `active_assignment_rows`), `kentender_core/tests/responsibility_test_cleanup.py` (also deletes Contacts of `kt.test.%` users), `Makefile` (`home-preflight`).

**4 October 2026: Phase 1 split (owner instruction, OD-3a, which supersedes OD-3).** Phase 1A, the design system for the Home page only, is done; Phase 1B, the rest of the repository, is on hold until the owner says otherwise. Phase 1's text above is not rewritten; read it as 1B, except that:

- **1A is a scoped copy, not a restyle.** `scripts/home_design_css.py` builds `kentender_core/public/js/home/kt_home_ds.bundle.css` from the design pack's own stylesheet: only the rules for the classes the Home board uses, in the pack's order, every selector under `.kt-industry.kt-home`. The page root carries both classes (the Industry design gate needs `.kt-industry`; Home adds `.kt-home`), and the doubled class outranks the old repository rules on the same element. The file is loaded lazily by the Home page controller, never app-wide, so no other page can change. `scripts/home_icons_js.py` builds `public/js/home/home_icons.js` (21 named icons from the board, including clock, list-checks and calendar-clock).
- **Verified, not assumed.** In Chromium, the original design stylesheet and the scoped copy give identical computed styles for every class on the board, hover and keyboard focus included, with and without the old `kt_industry_tokens.css` loaded. Loading the old stylesheet exposed two leaks (link colour; a 1px card border), both closed in the generator. Ten guard tests (`test_home_design_scope.py`) keep it that way and pin the Frappe values the design system falls back to.
- **Effect on later phases.** Gate HOME-G01 became HOME-G01A (done) and HOME-G01B (repo-wide, on hold). Phase 4 is no longer blocked by the design system. Rows HOME6-0102, 0106 and 0109 are `Blocked — owner` until 1B resumes. Rule for 1B: expect old-stylesheet leaks and run the same computed-style comparison per component before replacing anything.

**5 October 2026: Phase 4 (the page).**

- **Built:** a Page `home` with one `desk_page.register` call; Vue root `Home.vue` and components ported from the board's markup (header, summary column, work row, rail row, region, state panel, icon); a composable that keeps the state and applies the placement rules (which regions show, oversight promoted into the main column when My work and Coming up are empty, no rail means the main column spans 12); layout in `home_page.bundle.css`; the design system's rules for Home's classes in `kt_home_ds.bundle.css` (Phase 1A). Both CSS files load only from the Home controller.
- **The server owns every phrase.** Core gained `label` (singular or plural), `next_count` ("Show 1 more", "Show 5 more") and `paged` (the footer reads "Showing 6 of 6" after the last page), and Home's greeting reads the full name and skips titles ("Good morning, Peter" for Dr Peter Kimani). The browser computes no count, label or time.
- **Verified in a real browser** as Peter, Charles, Amina, Brian and Daniel on the test site (by address): the design system's colours, sizes and fonts, the empty, oversight-promoted and technical layouts, a two-per-row summary at 1024 px, no skeleton and one quiet re-read when the page is shown again, and no console errors beyond Frappe's known dev noise.
- **Finding that changes Phase 6:** Frappe lists hidden workspaces for anyone who can manage workspaces, so hiding ERPNext's Home leaves `/app/home` pointing at ERPNext's workspace for Administrator and System Manager. Phase 6 must remove the workspace after every migrate (FU-HOME-34).
- **Not done:** the menu-driven walk (the sidebar item still reads Planned; Phase 6), the keyboard and 200% zoom pass and the fidelity gate (Phase 8), seeded worlds that put rows in Coming up, blocked work and the rail (Phase 7), and installing the page on the dev site (it needs the Page record: a migrate, or the targeted import used on the test site).

**5 October 2026: Phase 6 (routing and landing) built; Phase 7 retired from this change.**

- **Phase 7 (seed and fixtures) is retired from this change** (owner instruction: seeding is done holistically in another session). Its rows and Gate HOME-G07 are `Blocked — owner`. What Home needs from that session is `reconciliation/seed_scenario_map.md`.
- **What was built:** `install.retire_erpnext_home_workspace()` (called from `after_migrate`) removes ERPNext's Home workspace, sidebar and desktop icon; `my_work.patch_bootinfo_home` lands every internal user on Home once the Page exists (My Work only before that); the Procurement sidebar's Home item opens the page and loses the Planned badge; the old landing tests were rewritten and new ones added (`test_home_routing`, 14).
- **Confirmed in a browser on both sites:** Administrator, Peter, Charles, Brian and Daniel open Home at `/app/home` and at `/app`; the sidebar item opens it; My Work still opens (it is retired only after Gate HOME-G08).
- **How it was applied:** by targeted steps, not a real `bench migrate` (a migrate rewrites the Procurement sidebar file, which carries other people's uncommitted edits). The first real migrate does the same through the hook.
- **Two incidents** (FU-HOME-38, FU-HOME-39), both caused by Frappe's developer-mode behaviour of deleting a standard record's exported file with the record: three ERPNext files and `procurement.json` were deleted and regenerated. The removal function now switches developer mode off for the delete, and a test asserts the ERPNext files survive. Lesson for any later work on sidebars, workspaces or desktop icons: never `delete_doc` a standard record in developer mode without checking where its file lives, and back the files up first.

