# System setup: plan to bring the module up to CFG-CHG-002 v0.14

## Context

The Project Owner approved CFG-CHG-002 v0.14 on 24 September 2026. The live System setup page implements v0.11 and has been passed by two later approved versions:

- **v0.12:** read-only Tender formats; AUTH v1.9, where a Scheduled responsibility can be edited.
- **v0.13:** the corrected 30% reservation measure. The plan is measured against the current Annual Plan, never the unused Budget.
- **v0.14:** the Tender-format reservation scope.

The shared standard is now KT-STD-001 v1.7, which asks for task-led screens. The standard also says it does not make CFG's older screens conformant; each module needs its own presentation rewrite and browser evidence. The design boards were refreshed after the last commit (7 files changed, plus a new `Tender-Formats.dc.html`).

What the research found:

1. **The UI assurance is weak.**
   - System setup is checked only by the text-order fidelity spec, which cannot see containers.
   - It is not in `make ui-structure-gate`, has no `departures/system-setup.js`, and never calls `expectStructure` or `expectLayoutSanity`.
   - The spec header claims geometry checks that nobody runs.
   - `COVERED` lists in every departures file are imported by nothing.
2. **The routing breaks the shared runtime rules.**
   - `SystemSetup.vue` has its own `hashchange` listener and never uses `useRouteState`.
   - It has no screen cache, no sequence guard, and no revalidation on return.
   - Tabs are swapped with `v-if`.
   - The root `load()` replaces the content with a skeleton.
   - `ProcuringEntityTab.vue:160` navigates to a view kind that doesn't exist.
   - This is the known cause of flashes, stale screens and "field lost on save".
3. **Domain drift against v0.13/v0.14.**
   - The reservation payload still uses `denominator_basis = AnnualProcurementBudget | AnnualProcurementValue` and has no `measure_stage`. The places are `regulatory_reference.py:271`, `RuleEditor.vue:60,352` and `site_setup.py:791`.
   - Tracker row CFG10-AC-047 marks the old wording Done.
   - Idempotency does not hash the payload, so a reused key with different content silently replays the old result instead of returning `CFG_IDEMPOTENCY_CONFLICT`.
   - There is no general rule preview service.
   - There is no `ResolveProcurementConfiguration` result envelope.
   - CFG registers nothing with Technical record search (`kt_technical_reference_resolvers` / `kt_technical_read_probes` are absent from `kentender_core/hooks.py`).
4. **Tracker and fixtures are stale.** The tracker covers v0.11 only. The fixture worlds CONFIG-FIRST, CONFIG-SWAP and CONFIG-EMPTY were never built. The first-run screen has never been driven in a browser (FU-14).

**Owner decisions for this cycle (24 Sep 2026):**

- **D11 — Tender formats is deferred.** The Tender-template owner's read projection does not exist, and STD-TPL-001 v0.7 is not in the repo. Nothing Tender-format related is built this cycle. This covers the `/tender-formats` route, the §4.11 projection and the reservation-category constant used by Requisitions. It is recorded as a follow-up with its exact prerequisites.
- **D12 — Routing uses a hash-aware shared adapter.** Keep the spec's exact `#tab/section/id[/versions/id]` links, but read them through a `useRouteState` adapter built on `kentender_core.desk_page.useRoute`. Delete the hand-written listener.
- **D13 — Re-port every CFG screen from its current board**, class-for-class. No existing component is kept because it "works". Each one is re-derived from the board and gated structurally. Keeping a component unchanged needs an explicit, recorded departure.

## Rules that govern the work

### Project rules (CLAUDE.md, AGENTS.md, KT-STD-001 v1.7)

**Business logic and authority**
- Business rules live in Python services under `kentender_core/services/`. Controllers stay thin. Nothing is authoritative in the browser.
- Every command checks authority, `expected_version`, idempotency and audit on the server. Failures leave nothing half-written.

**Dependencies**
- `kentender_core` is the base app and never imports another app.
- Consumers call CFG's published services.
- After any contract change, grep the whole repo for real callers:
  - Planning: `readiness.py`, `profiles.py`, `plan_*`
  - Tenders: `configuration_gateway.py`
  - Requisitions: `compatibility.py`
  - Budget: `budget_contracts.py`

**No approval stages in setup**
- Setup saves directly. Versions are immutable. Source checks are appended.
- Never add Draft, Submitted or Approved states, a PE selector, or anything else KT-STD §2.3 or §10 prohibits.

**Errors**
- Use the exact `CFG_*` codes and the one-sentence messages from spec §8.
- Return `{"ok":false,"errors":{field:msg}}` with `frappeCall({silent:true})`.
- Never let Frappe's default "Message" popup appear (AGENTS §6.10).

**Seeds and data**
- Seeds call the real commands and are idempotent (KT-STD §8.6).
- The canonical seed must stay valid: `make seed-canonical-validate`.
- Every test module registers a purge for its own data. `bench run-tests` does not roll back on this bench.
- Clear `_Test Fiscal Year` residue after Python runs.

**Assets and the environment**
- Build one app at a time: `./scripts/bench-with-node.sh build --app kentender_core`. Never use a plain `bench build`.
- After any static CSS/JS edit, `touch hooks.py`, clear the cache, and confirm the bundle hash (or the CSS `?v=`) actually changed.
- Before any UI run: `make ui-queue-check`, with a worker running.
- Never run `bench run-tests` and Playwright at the same time.

**Replies** are in plain English. Section numbers and tracker IDs stay in docs and commits.

### Test-driven development (the loop for every change)

1. **Red.** Write the smallest test that proves the rule, at the lowest layer that owns it:
   - Python service test for domain behaviour;
   - vitest component test for rendering and state;
   - Playwright only for navigation, integration and real-browser behaviour.

   Run just that test and confirm it fails for the expected reason.
2. **Green.** Make the smallest change that passes it.
3. **Refactor**, keeping the focused test green.
4. **Run the containing module once.** One `--module` per `bench run-tests` call; two in one call runs only the last.
5. **Broaden only at checkpoints:** module suite, then affected cross-app callers, then the named `make` gate, then the full suite at release.

Other rules:
- Every bug found in the browser gets a regression test before its fix.
- Never weaken an assertion or add an arbitrary wait to go green.
- Classify each failure as product, fixture, selector, environment or unrelated before changing code. Keep the first traceback, response and console error.

### UI construction rules (the strengthened approach)

1. **The board is the build source.**
   - Before writing or touching any component, open its `.dc.html` board and port its DOM class-for-class and element-for-element beneath the shared rail. Keep the single `.blueprint` card, underline tabs, `h6.kt-card-title` subsections and `.kt-notice` with its icon.
   - Never build from the prose spec or from memory of other screens.
   - Never swap a drawn control for a native one.
   - Format dates as `24 Nov 2026, 09:15 EAT`.
2. **The spec supplies the words, the board supplies the structure.** Copy comes verbatim from spec §10 and §8.1. If the spec contradicts the board, the spec wins, and the difference is recorded as a departure entry with its reason. It is never a silent divergence.
3. **Diff the boards before porting.** Each refreshed board is compared with HEAD, because a design-tool export can silently drop hand-authored states. Missing §10.13 states are authored into the boards before code, not invented in Vue.
4. **One shared runtime, never per-screen fixes.**
   - `desk_page.register` + `useRouteState` + `createScreenCache` + `createSequenceGuard` + `createCommandRunner`.
   - The skeleton appears only when a screen has nothing to show yet. After that, refresh in place with `data-refreshing`.
   - Controlled inputs bind to the user's own selection, never to the server echo.
   - Editors re-hydrate only when the identity or `record_version` changes.
   - The post-save reload is awaited inside the command runner.
5. **Status dimensions stay separate.** "Saved", "Sources verified", "Details complete" and "Available in this release" are shown separately. There is never a combined "Ready" badge.
6. **Styling.**
   - `kt_industry_tokens.css` is the only design system.
   - Chain the base class when overriding (`.kt-card.kt-x`).
   - Editable controls go in `.kt-field`. `.kt-meta-row` is for read-only facts only.
   - No bare `import "*.css"`, and no `*/` inside a CSS comment.
7. **A rule and the check that fails when it is broken land in the same change.** No rule without enforcement, and no claim of enforcement that isn't wired in.

### UI testing rules (definition of done per screen)

A screen is done only when **all** of the following are green and recorded in the tracker:

- **(a) Component tests** (vitest `system-setup`) cover every state variant the board and §10 name: loading, empty, error, blocked, stale, and each variant ID.
- **(b) Structural fidelity:**
  - the screen is listed in `departures/system-setup.js` `COVERED`;
  - the component-level `system-setup.fidelity.spec.js` compares its skeleton against the resolved board artboard;
  - `make ui-structure-gate` includes it.
- **(c) Browser journey** (Playwright, one fixture world per spec file, instants pinned rather than set relative to now) proves:
  - first paint plus one interactive re-render after a real mutation;
  - direct load, reload and back/forward, with a MutationObserver count showing no skeleton flash on return;
  - the forced-500 error state through `page.route`;
  - the **absence** of things that must not appear: no Frappe "Message" modal, no approval controls, no combined Ready badge;
  - at least one actor whose authority does not cover everything (System Manager, or a denied business user);
  - `expectLayoutSanity` whenever an editor opens in an incomplete state.
- **(d) Browser fidelity:** `expectStructure` plus `expectLandmarkSubsequence` against the board.
- **(e) Accessibility:** keyboard-only completion, focus returns to the trigger on Cancel, focus moves to the first error on failure, 200% zoom and narrow width (year cards keep all three activities), and a footer that never covers the last field.
- **(f) Live click-through** using the Playwright browser tools as Administrator and System Manager, with zero console errors and zero failed own requests. Screenshots are compared against the board rendered next to them, not just checked for a successful render.
- **(g) Fast iteration:** use `npx playwright test <file> -g "<name>" --retries=0` while building. Whole gates run only at the end of a phase.

## Phases

The first four phases work across the whole module (docs, enforcement, runtime, domain). From Phase 5 the work goes screen by screen: API, then screen, then browser proof, then gate, before the next screen starts.

| Phase | Work | Exit condition |
|---|---|---|
| **0 Docs and boards** | 1. v0.14 plan and tracker, replacing the v0.11 tracker: an acceptance map for every current criterion, excluding the deferred Tender-format set CFG12-AC-001–012 and CFG14-AC-001–006; CFG10-AC-047 reopened; old Done rows re-audited rather than carried forward. 2. Record D11–D13. 3. `FOLLOW_UPS.md`: Tender formats (D11) with prerequisites (template standard v0.7, owner projection hook, a `TENDER_RENDERABLE_RESERVATION_CATEGORIES` correction that currently includes "Other disadvantaged group", sc-for board resolver); note that the legal register v1.2 is still "Proposed" while CFG v0.14 adopts its measure. 4. Diff every modified board against HEAD for dropped states. Audit each board against the §10.13 inventory and author any missing CFG state into the board. Commit the boards. | Docs and boards committed; no product code. |
| **1 Enforcement first** (red list) | 1. `tests/ui/fidelity/departures/system-setup.js` (`DEPARTURES`, `COVERED`). 2. A `setupScope` function in `tests/ui/fidelity/board.js` for id'd `div` artboards, plus a switcher resolver where boards use `sc-if`. 3. `kentender_core/public/js/system_setup/system-setup.fidelity.spec.js`, one case per artboard. 4. Add `--project system-setup` to `ui-structure-gate`. 5. A small test that fails when a board-backed component in a module is not in that module's `COVERED` list, which finally enforces the rule for every module. 6. Add `expectStructure` and `expectLayoutSanity` to `system-setup-fidelity.spec.ts` and remove its false geometry claim. 7. Put `system-setup-pe-stale-save.spec.ts` into a gate. 8. Port the `.kt-meta-row` grid fix and `.is-tight` into `kt_industry_tokens.css`, then check Planning's local overrides and other modules' gates for regressions. | The new specs run and **fail** on the current screens. That failing list is the Phase 5 work queue, recorded in the tracker. `make ui-industry-design-gate` and the other modules' structure gates stay green. |
| **2 Shared runtime** | A hash-aware `system_setup/composables/useRouteState.js` over `desk_page.useRoute`, modelled on `reference_data/composables/useRouteState.js`. It parses `#tab[/section[/id[/versions/vid \| /calendars/id]]]` and provides `go()`, `epoch` and `isShown`. Rewire `SystemSetup.vue`: remove the `hashchange` listener, use `KeepAlive` tabs, `createScreenCache`, `createSequenceGuard`, `createCommandRunner`, and show the skeleton only on a cold load. Replace the old ad hoc sub-paths (`rule/`, `new-rule-version/`, …) with the §9 section keys: funding-sources, procurement-rules, schedule-profiles, reminders. Default to the first incomplete setup tab (§9). Fix the dead `navigate("procurement-rules")` call. | Route vitest tests; a Playwright route spec proving direct load, reload, back/forward across all five tabs and a rule-version deep link, with a MutationObserver showing zero skeleton insertions on return. |
| **3 Domain deltas** (Python, test first) | **3a Reservation measure:** add `measure_stage` (PlanningAllocation or ImplementationAchievement) and `denominator_basis` (EligibleCurrentAPPValue or ApplicableActualProcurementValue); refuse the old values; the AGPO planning rule is fixed to EligibleCurrentAPPValue; reseed through commands; grep and verify Planning `readiness.reservation_allocations` still agrees (it already uses eligible planned value). **3b Idempotency:** hash the canonical payload in `reference_data_idempotency.run_idempotent`; same key with a different payload returns `CFG_IDEMPOTENCY_CONFLICT`; make the key required on CFG commands; audit replay has no duplicate event. **3c** A `preview_configuration_version` service for §7.3 (schema, completeness, overlaps and gaps, supersession impact, known usage or an explicit "usage unavailable"); no writes. **3d** A resolver result envelope: `resolve_procurement_configuration` wraps `resolve_reference`, `resolve_method_profile` and `resolve_schedule_profile`, returning §4.10 statuses (Resolved/Missing/Ambiguous/Unverified/Incomplete/Unsupported/MissingBasis/NotPublished) plus a resolution hash. Existing callers stay unchanged; migrating them goes to follow-ups. **3e** Check that intake history carries every IntakeChange fact (module, target and previous year, before/after flags and close instants, reason, command identity) and add what is missing. **3f** Technical-read registration: `kentender_core/services/technical_read.py`, modelled on `kentender_procurement/.../std_configuration/services/technical_read.py`, plus both hooks for the CFG record types. `test_technical_read_conformance` green. | Each item red then green. `kentender_core` module tests pass. Cross-app callers (Planning, Tenders) pass their focused tests. `make seed-canonical-validate` passes. |
| **4 Fixture worlds** | `kentender_core/seeds/playwright_ui_fixtures.py`: `reset_config`, `reset_config_first`, `reset_config_swap`, `reset_config_rules`, `reset_config_empty` per §10.1, with instants pinned at 24 Nov 2026, 09:15 EAT; one world per spec file; a purge registered for each. | Each builder is idempotent and purges clean; the canonical seed still validates afterwards. |
| **5 Screen by screen** | Order: **5A** Procuring entity (configured, first run, conflict, missing authority, the separate source-check group). **5B** Financial years (list, detail, add dialog, duplicate, missing Company, disable blocked/eligible, re-enable, narrow cards) with the six open/close forms, the deadline edit, the cross-year swap notice, expiry and stale form. **5C** Funding sources (list, empty, add, the new Edit dialog, disabled, duplicate). **5D** Procurement rules (list, empty, set-only, saved detail, rename, the one-form add rule for all seven kinds with the updated reservation measure, partial save with "Rule created; version not saved", new version with replacement impact, gap, overlap, stale form). **5E** Source checks (pending, verified-but-incomplete, rejected, version, check and usage history, decision-time vs current evidence). **5F** Schedules and calendars (list, detail, seven milestones, 10-column interval table, the selected-interval editor, missing support, endpoint and default, working-day calendar add, detail, successor and history as separate states). **5G** Reminders (unchanged, edited, zero, invalid). **5H** Common states (loading, denied without painting any content first, load error, stale, read-only version) plus the AUTH-owned tabs checked against the AUTH v1.9 boards, including Edit scheduled assignment and the two missing-root role variants. | Per screen: the whole UI definition of done above, then the screen's `make` gate. Gates are extended in place: `ui-system-setup-fidelity-gate`, `-procurement-settings-gate`, `-fiscal-years-gate`, `-access-gate`, plus new `ui-system-setup-rules-gate` and `ui-system-setup-schedules-gate`. |
| **6 Release** | Full `kentender_core` Python suite compared against the recorded baseline; all System setup gates; `ui-structure-gate`, `ui-industry-design-gate`, technical-read conformance; production asset build of `kentender_core`; a scan proving the old denominator values and the old sub-path routes are gone; representative-user walkthrough scripts (§11.4) prepared and recorded as owed unless actually run; tracker acceptance map complete with evidence or an explicit gap; FOLLOW_UPS and memory updated; site left canonical. | Evidence report: files changed, tests run with results, what was not run and why, remaining risks. |

## Critical files

- **UI:** `kentender_core/kentender_core/public/js/system_setup/`, which holds `SystemSetup.vue`, `tabs/*`, `components/*` (RuleEditor, MethodVersionEditor, ScheduleVersionEditor, CalendarEditor, SourceCheckScreen, FundingSourceEditor, IntakeDialog, …), `composables/` and `data/*Api.js`. Also `public/js/system_setup_page.js` and `public/css/kt_admin_configuration.css`.
- **Shared runtime and tokens:** `kentender_core/public/js/kt_desk_page.js` (reuse `useRoute`, `createScreenCache`, `createSequenceGuard`, `createCommandRunner`) and `public/css/kt_industry_tokens.css`.
- **Services:** `kentender_core/services/regulatory_reference.py`, `procurement_settings.py`, `site_configuration.py`, `reference_data_idempotency.py`, `configuration_errors.py`, `api/procurement_settings_api.py`, `api/site_configuration_api.py`, `hooks.py`.
- **Seeds:** `kentender_core/seeds/site_setup.py`, `seeds/playwright_ui_fixtures.py`, `seeds/canonical.py`.
- **Tests:** `kentender_core/tests/test_regulatory_reference.py`, `test_procurement_settings.py`, `test_site_configuration.py`, `test_technical_read_conformance.py`; `tests/ui/smoke/system_setup/*.spec.ts`; `tests/ui/smoke/design-fidelity/system-setup-fidelity.spec.ts`; `tests/ui/fidelity/{board.js,skeleton.js,departures/}`; the `Makefile`.
- **Docs:** `docs/mvp-1-r1/09_unified_system_setup/{CFG-CHG-002_Implementation_Plan.md, CFG-CHG-002_IMPLEMENTATION_TRACKER.md, FOLLOW_UPS.md, design/*.dc.html}`.

## Verification (end to end)

1. **While building:**
   - focused `bench --site kentender.midas.com run-tests --app kentender_core --module kentender_core.tests.<module>`;
   - `npx vitest run --project system-setup <file>`;
   - `npx playwright test tests/ui/smoke/system_setup/<spec>.ts -g "<name>" --retries=0`.
2. **Per screen:** `make ui-structure-gate`, the screen's `make ui-system-setup-*-gate SITE=kentender.midas.com`, and a live click-through as Administrator (credentials in `.env.ui`) and System Manager.
3. **Release:**
   - all System setup gates, `make ui-industry-design-gate`, technical-read conformance;
   - Planning and Tenders focused tests for the changed resolver and reservation contracts;
   - `make seed-canonical SITE=kentender.midas.com` then `make seed-canonical-validate`;
   - the targeted asset build with its hash change confirmed.
4. The report states exactly what ran, what did not, and what remains owed. The representative-user evidence and the deferred Tender formats stay explicitly open.
