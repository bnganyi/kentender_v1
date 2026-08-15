# Procurement Planning Revision Implementation Report

**Revision:** PLN-CHG-001 through PLN-CHG-014
**Implementation review cut:** 2026-08-15 18:00 +03
**Status:** Implemented and focused-validation complete; full MVP and cross-module regression gates are deliberately deferred for end-of-module validation.

## 1. Executive summary

The approved Procurement Planning revision has been implemented as a coherent server-governed slice spanning the Planning workspace, annual Plan registration, empty and populated initial/successor Draft builders, approved-Demand selection, Plan Item formation and editing, task-backed Finance confirmation, professional review, the current Approved Plan, schema constraints, permissions, deterministic seeds, client navigation, and lifecycle behavior.

The implementation replaces client-authored Plan identity and aggregate Demand arithmetic with governed PE/FY context, per-Need-Item availability, transaction-scoped active holds, immutable allocation lineage, database-backed uniqueness, and idempotent formation. UI-02 through UI-05 were rebuilt around the approved HTML compositions instead of extending the obsolete markup. UI-01 retains its working fixture but now renders the revised deterministic projection and exact queue/action vocabulary.

No new DocType, role, workflow state, queue/counter model, or permanent design-only record was introduced. Governed Finance and professional task evidence is stored on the existing Version records and `Plan Decision`, as required by PLN-CHG-009 through PLN-CHG-012.

## 2. Source precedence and presentation decisions

- Business state, authorization, copy, fields, actions, and prohibited behavior come from `01_Procurement_Planning_Revision_Ledger.md` and `02_Procurement_Planning_Workspace_State_Specifications.md`.
- Visual hierarchy, component composition, columns, spacing, typography, iconography, and responsive intent come from the matching `PLN-UI-*.html` file.
- Ledger content overrides contradictory static sample content in HTML.
- The static HTML top bar, sidebar, footer, fake records, Tailwind CDN, and navigation handlers were not shipped.
- No breadcrumb was added inside the Planning canvas. The existing shared Desk toolbar remains the sole navigation-chrome owner.
- The shared chrome test accepts the workspace CTA's exact HTML `rounded` value (4px) through its existing per-surface radius option; production CSS was not changed away from the approved HTML to satisfy a generic 6px default.

## 3. Requirement traceability

| Change | Implemented behavior | Principal code | Focused evidence |
|---|---|---|---|
| `PLN-CHG-001` | Deterministic UI-01 states, explicit PE/FY scope, approved/draft summaries, Finance and validation projections, server-derived primary action, prioritized/deduplicated action and waiting queues, server search/filter, viewer/support isolation, non-flashing partial refresh | `services/get_planning_workspace.py`, `public/js/planning_workspace_page.js`, `public/js/planning_live_bind.js`, `public/js/planning_ui_fixtures/workspace.js`, `public/css/planning_workspace.css` | Workspace API 10/10; query-growth assertion included; focused chrome 1/1 |
| `PLN-CHG-002` | Explicit PE/FY registration scope, five governed read-only values, derived identity, atomic/idempotent Plan + Draft V1 + audit decision, no downstream side effects | Core `services/financial_context.py`; Planning `services/get_planning_create_scope.py`, `services/create_procurement_plan.py`, `api.py` | Registration API 6/6; permission and invariant suites |
| `PLN-CHG-003` | Static fixture composition separated from executable behavior; split shared utilities, registration, builder, dialog and workspace binders; lifecycle teardown and stale-request protection | `planning_client_utils.js`, `planning_register_bind.js`, `planning_builder_bind.js`, `planning_demand_dialog.js`, page controllers and hooks | Static layout guard 17/17; JS syntax checks clean |
| `PLN-CHG-004` | Exact empty Draft builder, governed summary, eligible-count driven Add action, no premature filters/validation/submission controls | `services/get_plan_builder.py`, `planning_ui_fixtures/builder.js`, `planning_builder_bind.js` | Builder revision 3/3; registration routing covered |
| `PLN-CHG-005` | Per-Need-Item eligibility, Budget adapter validation, partial availability, single/separate/combined formation, mixed-OU PE ownership, immutable source/funding lineage, active holds, concurrency/idempotency/rollback behavior | `services/list_eligible_demands.py`, `services/add_demand_to_plan.py`, allocation/item schemas, Budget public adapter | Eligibility 3/3; formation 7/7; update/remove/Finance/scenario suites |
| `PLN-CHG-006` | Exact populated builder metrics, outstanding-work summary, server OU/status/search filters, seven-column rows, item-specific actions, return to empty state after removal | `services/get_plan_builder.py`, builder fixture/binder/CSS | Builder revision 3/3; removal 12/12; scenario removal 5/5 |

## 4. Schema, migration, and backfill

### Core

- Added required `Procuring Entity.reporting_currency` Link to Currency.
- Added the public governed financial-context service using enabled ERPNext Fiscal Years and PE reporting currency.
- Added an explicit reporting-currency backfill patch and canonical KES seed configuration.

### Planning

- `Procurement Plan`: identity fields are derived/read-only snapshots; obsolete `coordinating_org_unit` was removed; PE/FY uniqueness is database-enforced.
- `Procurement Plan Version`: hidden open-version slot and unique Plan/version number enforcement.
- `Procurement Plan Item`: optional owner OU for mixed-OU PE-owned combinations; formation idempotency/batch fields and lookup constraints.
- `Plan Demand Allocation`: immutable source OU and funding lineage, active-hold key, approved quantity/value snapshots and supporting indexes.
- Transition services consistently set or clear open-version/active-hold keys.

The migration is split into preflight, schema/backfill, and formation-batch/index patches. Preflight reports duplicates and conflicting open records instead of selecting or deleting a winner. `bench --site kentender.midas.com migrate` completed successfully on 2026-08-15.

## 5. Public API changes

| API | Before | After |
|---|---|---|
| `get_planning_workspace` | Mixed projection and client inference | Explicit selected scope, deterministic state, approved/draft/Finance/validation summaries, server primary action, two queues, stable identifiers, counts/options, search/filter, temporary `work_queue` alias |
| `get_planning_create_scope` | Client-fillable registration metadata | Explicit authorized PE/FY and five governed read-only identity values plus existence/capability/destination |
| `create_procurement_plan` | Accepted client-authored identity metadata | Accepts PE/FY only; derives all identity; atomically creates Plan, Draft V1 and registration decision; idempotently returns existing Plan |
| `get_plan_builder` | Mixed client filtering/completeness | Server OU/status/search filters; exact UI-03/UI-05 state or approved/update redirect |
| `list_eligible_demands` | Aggregate Demand availability | Scoped per-Need-Item availability, source breakdown, filter options, and structured requested-source exclusion reasons |
| `add_demand_to_plan` | Client-influenced formation details | Plan, Demand IDs, expected token, required multi-selection mode/reason and idempotency key only; atomic server formation |

## 6. HTML fidelity

| Surface | Visual source | Production fixture/controller | Sanctioned exclusions or corrections |
|---|---|---|---|
| UI-01 | `PLN-UI-01.html` | `planning_ui_fixtures/workspace.js`, workspace binder/CSS | No HTML fake shell or in-canvas breadcrumb; deterministic ledger copy/states; one empty-state line removed where required |
| UI-02 | `PLN-UI-02.html` | `planning_ui_fixtures/register.js`, `planning_register_bind.js` | Governed FY/context replaces stale static sample; exactly five read-only values and two actions |
| UI-03 | `PLN-UI-03.html` | shared builder fixture and `planning_builder_bind.js` | Duplicate Add action and premature controls removed per ledger |
| UI-04 | `PLN-UI-04.html` | `planning_ui_fixtures/add_demand_dialog.js`, `planning_demand_dialog.js` | Live scoped data and fresh server eligibility replace fake rows |
| UI-04A | `PLN-UI-04A.html` | same reusable dialog controller | Server-controlled separate formation and result routing |
| UI-04B | `PLN-UI-04B.html` | same reusable dialog controller | Full approved combined label/reason and mixed-OU ownership rules retained |
| UI-05 | `PLN-UI-05.html` | shared builder fixture and `planning_builder_bind.js` | Removed obsolete method/schedule columns and sticky submission footer |

Manrope remains the heading family, Inter the interface/body family, JetBrains Mono the reference/FY/currency/numeric family, and Material Symbols use the HTML glyph/fill choices.

## 7. Files added, replaced, and materially changed

### Added

- `kentender_core/kentender_core/services/financial_context.py`
- `kentender_core/kentender_core/patches/v1_0/backfill_procuring_entity_reporting_currency.py`
- `kentender_procurement/kentender_procurement/patches/pln_revision_preflight.py`
- `kentender_procurement/kentender_procurement/patches/pln_revision_schema_backfill.py`
- `kentender_procurement/kentender_procurement/patches/scope_pln_formation_batch_key.py`
- `kentender_procurement/kentender_procurement/public/js/planning_client_utils.js`
- `kentender_procurement/kentender_procurement/public/js/planning_register_bind.js`
- `kentender_procurement/kentender_procurement/public/js/planning_builder_bind.js`
- `kentender_procurement/kentender_procurement/public/js/planning_demand_dialog.js`
- `kentender_procurement/kentender_procurement/procurement_planning/tests/test_plan_builder_revision.py`
- This report.

### Replaced or substantially rewritten

- Planning registration, eligibility, formation, workspace and builder service internals.
- UI-02, UI-03/UI-05 and UI-04 fixture markup and bind behavior.
- The UI-01 projection/binding contract and scoped visual refinements.
- Planning public API adapters and relevant canonical/scenario seed behavior.
- Planning schema JSON/controllers and cross-workflow hold/open-version maintenance.

### Consequentially changed

- Core module registry, client module registry, patch list, seed common/orchestrator and shared chrome registry.
- Budget's published read-only Planning context adapter.
- Planning hooks, page controllers, navigation/sidebar destinations, approval/review/Finance/removal/publication services and their focused tests.
- Shared Stitch Desk Playwright surface metadata for the revised workspace CTA.

Obsolete UI-10 route/page/fixture/binder/projection/tests and the Planning-owned publication service/tests were intentionally deleted. The final scoped diff is recorded by the commit itself; unrelated dirty-worktree files are excluded from it.

## 8. Seeds and fixture isolation

- Canonical seed uses the governed Plan identity invariant and explicitly configures PE currency.
- Permanent FY2027/28 Approved V1 and downstream records remain canonical.
- `SCN-PLN-ADD-001` supports deterministic ready, incomplete, awaiting-Finance and submitted-review stops using idempotent formation.
- `SCN-PLN-REMOVE-001` proves Draft hold release and restored eligibility.
- Gate UI fixture creation is isolated/resettable and does not introduce permanent design-only Plans, Demands, users, task rows, or counters.
- The focused-test helper no longer commits during pre-case graph cleanup. New high-year test Fiscal Years therefore remain inside Frappe's normal test/request transaction instead of leaking when a later case reuses the helper.
- The canonical reset/validation completed with 129/129 checks and removed fixture-owned Planning, Demand, Budget, Strategy and `@test.local` records shown in its cleanup result.

## 9. Validation evidence

All commands below were run on 2026-08-15 in WSL/bash against `kentender.midas.com`. The test runner did not print a wall-clock timestamp per module; the review cut above records the verified session completion time.

### Passed

- `git diff --check` — pass.
- `python3 -m compileall -q kentender_core/kentender_core kentender_procurement/kentender_procurement` — pass.
- `node --check` for all five revised Planning bind/utility files — pass.
- `bench --site kentender.midas.com migrate` — pass.
- `make seed-kentender-mvp-v1 SITE=kentender.midas.com` — 129 passed, 0 failed.
- `./scripts/bench-with-node.sh build --app kentender_core` — asset and translation build pass.
- `./scripts/bench-with-node.sh build --app kentender_procurement` — asset and translation build pass.
- Focused Planning service tests — 169 passed across invariants, permissions, PE selection, cross-PE isolation, task capability, registration, workspace, builder, eligibility, formation, update, remove, validation, Finance, approval/review, decisions, publication, implementation/handoff and governed scenarios.
- `bench --site kentender.midas.com run-tests --module kentender_core.tests.test_stitch_desk_chrome_gate` — 3/3 pass after CTA registry reconciliation.
- `npx playwright test tests/ui/smoke/stitch-desk/stitch-desk-chrome.spec.ts --project=chromium --workers=1 --grep "planning-workspace resists"` with Node 24 — 1/1 pass.
- After the final test-helper-only removal of an internal commit: targeted `py_compile` and `git diff --check` pass. Service/browser suites were not rerun, following the instruction to stop at focused validation and defer broad regression.

The build host's Python 3.14 default `forkserver` cannot create its Unix socket in this execution environment (`Errno 95`). Asset bundling passed on the first attempt; the successful complete build used a temporary `/tmp` `sitecustomize.py` to select `fork`. No framework or repository source was changed for this environment workaround.

### Deferred at user direction

The following full MVP/cross-module gates were not run to completion and are intentionally deferred until the end of module development:

- `ui-planning-workspace-gate`
- `ui-planning-builder-gate`
- `ui-planning-scope-auth-gate`
- `ui-planning-a11y-gate`
- `ui-planning-finance-gate`
- `ui-planning-approval-gate`
- `ui-planning-mvp1-gate`
- the complete Planning navigation-lifecycle Playwright spec

Before that direction, one cross-module chrome attempt ran 18 checks, then stopped on the workspace's HTML-defined 4px radius versus the generic 6px default; seven later checks did not run. The surface-specific expectation was corrected from the approved HTML and its focused browser assertion now passes. The broad suite was not rerun.

## 10. Manual verification and remaining acceptance work

Still required at the end-of-module checkpoint:

- full desktop and mobile visual comparison for UI-01 through UI-05;
- keyboard/focus-trap/focus-return and reduced-motion pass across all dialog and filter paths;
- complete no-flash search/filter interaction under throttled responses;
- repeated Desk client-navigation/remount exercise across Planning and non-Planning pages;
- all deferred gates above followed by a final canonical reseed/validation.
- review and explicitly approve removal of the already-persisted untagged Fiscal Years dated 2100 or later. A read-only audit confirmed such records exist. They were not deleted because their historical ownership cannot be proven from a date boundary alone; linked records must be resolved from an explicit verified list.

The implementation must remain in review status—not final acceptance—until those deferred gates pass.

## 11. Known boundaries and worktree preservation

- UI-05A and UI-06 are implemented in the focused PLN-CHG-007/008 addendum below. Later Planning revision sections remain out of scope.
- UI-09 was rebuilt as the current Approved Plan projection. UI-10 was removed completely with no redirect or alias.
- Existing changes to `AGENTS.md`, deleted P5 evidence images, `.playwright-mcp/`, legal/reference PDFs, STD documents and archives were not staged, restored, deleted, or otherwise altered by this implementation.
- Existing untagged high-year Fiscal Year records remain a known database-cleanliness issue. The source leak is fixed, but deleting those historical rows requires an explicitly approved, verified target list rather than an unsafe wildcard/date-range cleanup.
- Commit and push were requested after this review cut; the resulting commit identifier is reported in the handoff response.

## 12. Focused PLN-CHG-007 / PLN-CHG-008 addendum

### Final status at review cut

PLN-UI-05 item-specific actions and removal entry, all four data-driven PLN-UI-05A presentations, and the revised PLN-UI-06 editor contract have been implemented. The static HTML controls hierarchy, spacing, typography, Material Symbols, fields and column order; the approved ledger controls business copy, capabilities and command behavior. Fake HTML chrome, footers and in-canvas breadcrumbs were omitted.

The implementation is ready for code review, but browser acceptance remains open because the execution environment did not permit a completed post-fix Chromium rerun. No full MVP or cross-module suite was run.

### Requirement traceability

| Change | Implementation | Focused evidence |
|---|---|---|
| `PLN-CHG-007` / UI-05 capabilities | `get_plan_builder.py` bulk-projects item-specific action/removal capabilities and bounded source/downstream evidence; `planning_builder_bind.js` exposes removal only through the row overflow menu and refreshes in place | `test_plan_builder_revision` (3/3), `test_remove_plan_item` (12/12) |
| `PLN-CHG-007` / UI-05A projection | `get_plan_item_removal` returns the authoritative mode, four presentation variants, identity, token, Finance/reservation effect, source totals, exact copy and destination without mutation | `test_planning_ui_05a_06_revision_services` and `test_planning_ui_05a_06_revision_layout` |
| `PLN-CHG-007` / removal command | `remove_plan_item_from_plan` requires Draft identity, expected token, reason and idempotency key; Draft removal reverses lineage/holds/Finance effects, while Active removal creates/reuses a successor only after confirmation and remains proposed until approval | `test_remove_plan_item` (including combined, replay, stale token, Active removal, concurrent handoff and cancel-update); `test_scn_pln_remove_001` (5/5) |
| `PLN-CHG-007` / shared UI-09/UI-10 entry | Existing entry handlers invoke `planning_removal_dialog.js`; no adjacent screen redesign | Static layout guard and scoped diff review |
| `PLN-CHG-008` / editor projection | `get_plan_item_editor.py` returns immutable source rows, exact approved fields/options/status, return context, completeness, token, duration and initial/successor back route | `test_planning_ui_05a_06_revision_services`; `test_update_plan_item` (12/12) |
| `PLN-CHG-008` / mutation boundary | `update_plan_item.py` enforces the strict allow-list, Open tender only, category options, conditional fields, governed dates, chronology, source revalidation, concurrency and idempotency | `test_update_plan_item` (12/12) |
| `PLN-CHG-008` / Finance command | Request Finance saves and validates under one savepoint, creates one Finance transition/audit on success and rolls back failed Finance submissions | `test_plan_item_finance` (14/14) and revision service tests |
| `PLN-CHG-008` / seven-date schedule | `ms_notification_of_award` is included in schema, projection, completeness, validation, fingerprinting, successor copy and scenario data | schema reload, layout/service tests, update/Finance modules |

### Files added for this slice

- `kentender_procurement/kentender_procurement/public/js/planning_removal_dialog.js`
- `kentender_procurement/kentender_procurement/public/js/planning_item_editor_bind.js`
- `kentender_procurement/kentender_procurement/procurement_planning/tests/test_planning_ui_05a_06_revision_layout.py`
- `kentender_procurement/kentender_procurement/procurement_planning/tests/test_planning_ui_05a_06_revision_services.py`

The directly affected API, builder/removal/editor/Finance/validation services, Plan Item Version schema, UI fixtures/binders/pages, scenario helpers and focused tests were materially changed. No new DocType, role, workflow state, permanent queue/counter or design-only canonical record was added.

### Focused validation performed on 15 August 2026

- Targeted reload: `bench --site kentender.midas.com reload-doc procurement_planning doctype procurement_plan_item_version` — pass.
- Static UI-05A/UI-06 layout guard — 3/3 pass.
- Focused revision service module — 5/5 pass.
- Builder revision module — 3/3 pass after warming framework metadata/permission caches before the constant-query comparison.
- Removal service module — 12/12 pass.
- Governed removal scenario module — 5/5 pass.
- Editor update/validation module — 12/12 pass.
- Finance request/return module — 14/14 pass.
- JavaScript syntax checks for the revised builder, editor and removal assets — pass.
- Procurement asset bundling completed successfully. Translation compilation then failed because Python 3.14 `forkserver` cannot bind its multiprocessing socket in this host (`Errno 95`); the repository source was not changed to bypass the host restriction.
- Focused Chromium UI-05A test was attempted. Browser launch required escalation; the first permitted run reached the application but timed out before the revised root became live, leading to a direct-entry live-marker correction and Frappe cache clear. The post-fix rerun could not start because the environment's automatic approval review timed out twice. Browser status is therefore **not verified**, not passed.
- `git diff --check` is blocked by pre-existing trailing whitespace in the user-owned updated revision ledger at lines 1138–1140 and 1397–1399. The implementation files themselves introduced no reported whitespace error.

### Intentionally skipped

Per instruction, no full Planning MVP suite, MVP gate, whole accessibility gate, Finance/approval cross-module gate, navigation lifecycle suite or cross-module regression suite was run. UI-09's mislabeled export/publication action, workspace seed presentation and unrelated routes/fixtures were not repaired.

### Manual review still required

- Re-run the two focused Chromium specs for the populated builder/removal happy path and canonical UI-06 Save/Request-Finance path.
- Compare UI-05A variants and UI-06 at desktop/mobile sizes against the supplied HTML.
- Verify keyboard focus trap/return and Awaiting-Finance read-only behavior in a browser.

Unrelated dirty-worktree changes, deleted evidence images, legal/reference files and prior revision work were preserved and were not staged, committed or pushed.

## 13. PLN-CHG-009 through PLN-CHG-014 completion addendum

### Corrected journey and screen ownership

The implemented journey is:

`PLN-UI-09 → PLN-UI-04 → PLN-UI-06 → PLN-UI-05 → PLN-UI-07/07A → PLN-UI-05 → PLN-UI-08 → PLN-UI-09`

- PLN-UI-05 is now the sole populated Draft builder for initial Drafts and successors. Successors include Approved-predecessor context, Draft totals/net change, update reason, effective changes, Finance/validation readiness, and compact unchanged operational context.
- PLN-UI-03 remains the zero-item initial-Draft state only.
- PLN-UI-04 routes single/combined formation to PLN-UI-06 and multiple separately formed items to PLN-UI-05.
- PLN-UI-05A removal returns to PLN-UI-03 or PLN-UI-05 according to the recalculated Draft state.
- PLN-UI-06 Save/Back returns populated Draft work to PLN-UI-05.
- PLN-UI-07/07A and PLN-UI-08 are protected, task-identity-based Finance and professional-review surfaces.
- PLN-UI-09 resolves and displays the current Approved Version without creating a Draft or other workflow evidence on open.
- PLN-UI-10 was deleted completely. Its old route returns the ordinary Frappe not-found result.

### Requirement-to-code traceability

| Change | Implemented behavior | Principal code/evidence |
|---|---|---|
| `PLN-CHG-009` | Assigned Finance task projection, exact sufficient/shortfall arithmetic, full-source reservation, return/re-request, stale token and idempotency controls | `services/plan_item_finance.py`, `services/planning_tasks.py`, Finance fixture/binder, `test_plan_item_finance.py`, focused Finance browser spec |
| `PLN-CHG-010` | PLN-UI-07A shortfall state with no confirmation capability and governed return/resolution navigation | Finance projection/controller and `scn_pln_fund_short_001.py`; focused shortfall browser path |
| `PLN-CHG-011` | Atomic Draft submission, assigned professional task, task-only projection, approve/return race and replay controls | `services/submit_plan_for_review.py`, `services/get_plan_review.py`, `services/approve_plan_version.py`, review fixture/binder and focused tests |
| `PLN-CHG-012` | Current Approved Version projection, independently derived action capabilities, two-item summary/history, removal/handoff restrictions, mutation-free open | `services/get_plan_implementation.py`, Approved fixture/binder, `test_get_plan_implementation.py`, focused Approved browser spec |
| `PLN-CHG-013` | Superseded design retained only as ledger history | No active UI-10 implementation remains |
| `PLN-CHG-014` | Successor projection consolidated into the ordinary builder; UI-10 route, page, fixture, binder, service and tests removed | `services/plan_builder_successor.py`, builder service/fixture/binder, retirement patch, layout/absence tests |

### Schema, API, and lifecycle changes

- Hidden Finance task identity, iteration, assignee, state, predecessor and token fields are stored on `Procurement Plan Item Version`.
- Equivalent professional-review task and submission evidence is stored on `Procurement Plan Version`.
- `Plan Decision` carries task identity, iteration and command-idempotency evidence with uniqueness protection.
- Finance APIs accept stable task identity rather than a client-selected Plan Item.
- Professional review APIs accept stable task identity and deny unassigned direct access before returning protected data.
- `save_plan_draft` replaces the UI-10-owned update save command; `get_plan_update` was removed.
- Planning publication APIs, DTO fields, presentation, seed writes and tests were removed. Tender Management publication remains untouched.
- The split controllers use native Promises, namespaced lifecycle handlers, stale-response suppression, focus management, in-flight disabling, accessible announcements and context-preserving Frappe navigation.

### HTML sources and sanctioned exclusions

The production content was hand-ported from `PLN-UI-05-1.html`, `PLN-UI-07.html`, `PLN-UI-07A-1.html`, `PLN-UI-07A-2.html`, `PLN-UI-08-1.html`, `PLN-UI-08-2.html`, and `PLN-UI-09.html`. Fake top bars, sidebars, profile images, external assets, HTML-only footers and in-canvas breadcrumbs were excluded. The revision ledger overrides stale generated sample data and prohibited publication/UI-10 content.

### Final focused validation

The final directly affected service/layout rerun passed 54 tests:

- `test_plan_item_finance` — 14/14;
- `test_planning_task_capability` — 6/6;
- `test_submit_plan_for_review` — 5/5;
- `test_approve_plan_version_gate05` — 5/5;
- `test_get_plan_implementation` — 4/4;
- `test_plan_builder_revision` — 3/3;
- `test_planning_ui_stitch_layout_guard` — 17/17.

An earlier focused Planning slice run passed 95 tests before the final lifecycle/fixture corrections. Focused Chromium reruns verified seven affected paths across individual/batched executions: sufficient Finance confirmation, exact shortfall, professional approval, professional return, current Approved projection, successor routing to PLN-UI-05, and stale UI-10 route absence.

`./scripts/bench-with-node.sh build --app kentender_procurement` completed asset linking/bundling. Its translation tail remains environmentally blocked by Python 3.14 multiprocessing `forkserver` socket creation (`OSError: [Errno 95] Operation not supported`); no translation source changed. Full MVP, module-wide accessibility, Finance/approval cross-module, and cross-module regression suites were intentionally not run under the requested validation boundary.

### Unrelated findings and exclusions

- Unrelated PDFs, `.playwright-mcp/`, deleted historical evidence screenshots, STD documentation, and `AGENTS.md` changes are excluded from the commit.
- The historical portions of the approved revision ledger retain superseded UI-10 discussion as audit context. Active requirements, inventory, routes and implementation no longer depend on UI-10.
- No unrelated route, fixture, screen, or regression failure was repaired.

## 14. PLN-CHG-014 focused correction review cut

The ordinary Plan builder now projects the two deterministic successor states from the same bulk-loaded item set used by the table. The awaiting-Finance state shows two Draft items, KES 535,000,000, KES 80,000,000 added, Planning 2 of 2, Finance 1 of 2 and validation **Needs attention**. The Finance-confirmed state shows Finance 2 of 2 and validation **Ready**, with the single professional submission action enabled only when the update reason and every shared readiness predicate pass.

Additional focused corrections made in this review cut:

- successor validation uses the bulk fingerprint helper, avoiding per-row validation queries;
- the Approved predecessor and its Tender handoff are represented as one compact operational-context line rather than duplicated editable rows;
- Draft save and empty-update cancellation require concurrency and idempotency evidence, resolve replay before stale-token rejection, and rotate the Draft token on first success;
- submission no longer commits inside the service, preserving the request transaction across task, decision and notification evidence;
- `SCN-PLN-ADD-001` now has resettable `awaiting_finance` and `finance_confirmed` boundaries and removes only its own replay markers when rebuilding deterministic records;
- the successor banner, six metrics, update reason, changed-item table, readiness message and action bar are rendered in the ordinary PLN-UI-05 fixture. No UI-10 route or compatibility canvas was restored.

Focused validation on 15 August 2026:

- directly affected Frappe modules: 65/65 tests passed (`test_plan_builder_revision`, `test_remove_plan_item`, `test_scn_pln_add_001`, `test_submit_plan_for_review`, `test_plan_item_finance`, `test_get_plan_implementation`, and `test_planning_ui_stitch_layout_guard`);
- Python compilation and JavaScript syntax checks passed for the changed service, seed and builder assets;
- `./scripts/bench-with-node.sh build --app kentender_procurement` completed assets and translations with the documented temporary WSL `fork` setting; the first unadjusted translation attempt reproduced host `forkserver` error 95 after assets had already bundled;
- focused Chromium: 6/6 clean checks passed for stale UI-10 absence, exact awaiting-Finance and Ready successor states, Finance confirmation returning to UI-05, professional approval opening UI-09, and professional return resuming UI-05;
- an initial combined Chromium attempt exposed stale fixture-owned command markers after canonical reset. The scenario reset was corrected and both exact successor tests then passed without retries.
- the final focused scenario cleanup restored Approved Version 1 and PPI-MOH-2027-021 and removed the Draft successor/browser evidence.

The full MVP suite, module gates as a whole, accessibility suite as a whole and cross-module regression suites were not run, as explicitly requested. Unrelated worktree changes remain excluded.

## 15. PLN-CHG-015 workspace state variants

### Implemented contract

The Planning workspace now derives exactly one unfiltered `workspace_state` from authoritative PE/FY, Plan, Version, item, Finance-task, professional-task, validation and Demand evidence:

- `NO_PLAN`;
- `INITIAL_DRAFT_EMPTY`;
- `APPROVED_WITH_ACTIONABLE_WORK`;
- `DRAFT_WITH_PLANNER_ACTION`;
- `DRAFT_AWAITING_FINANCE`;
- `VERSION_AWAITING_PROFESSIONAL_REVIEW`;
- `APPROVED_NO_WORK`.

The historical `PLN-UI-01C-NC` state is no longer emitted. No-effective-change Drafts are planner-action state with the protected Cancel-update route. Search and work filters operate only after state selection and cannot change the state. The response includes ordered state metrics, unfiltered/filtered counts, exact empty copy, `as_at`, and a non-persisted opaque `projection_token`. `work_queue` remains only as the temporary compatibility alias of `work_requiring_action`.

The shared Demand eligibility projection is used both before Plan registration and after a Plan exists. The no-Plan response exposes only the eligible count; registered Plans may expose authorised Demand rows. Finance and review waiting rows contain neutral work identity, stage, status and responsible role only—no task identity, route, token, comment, allocation arithmetic or decision action.

### UI and direct-entry changes

One state-aware PLN-UI-01 controller renders the approved A–F compositions; no variant route or client-authored state exists. State-specific metric order, seven-column actionable tables, four-column waiting tables, exact empty panels, Manrope/Inter/JetBrains Mono typography and Material Symbols are retained from the approved HTML. Mock chrome, external assets, footers and in-canvas breadcrumbs remain excluded.

Context changes use shared KenTender state and partial `aria-busy` refresh. Initial loading is not restored for search/filter requests, stale responses are ignored, and handlers are namespaced and torn down on page departure. Waiting rows do not synthesize View controls when the server provides no action.

The Approved-plan direct entry now consumes the workspace's `add_demand` context, opens the existing PLN-UI-04 controller on PLN-UI-09, performs fresh server eligibility validation and preselects the requested Demand. The ordinary Add Plan Item action uses the same dialog without first creating a successor.

### Deterministic fixtures and evidence

The Administrator-only `prepare_planning_workspace_ui` test entry prepares BASE and A–F through production Plan/scenario services. A/B reuse the exact FY2028/29 Demand pair and registration boundary. C–F reuse `SCN-PLN-ADD-001` at incomplete, awaiting-Finance, submitted-review and approved boundaries, with scenario evidence stamped to the approved 09:05, 10:00, 10:30 and 11:05 times. Fixture preparation is idempotent and deletes only fixture-owned evidence.

The active workspace-state specification was revised to the PLN-CHG-015 seven-state model. No schema, DocType, role, workflow state, task type, queue/counter model or persistent workspace flag was added.

### Focused validation on 15 August 2026

- `test_planning_workspace_api` — 10/10 passed, covering selection, permission isolation, filters, state priority, projection reconciliation and query growth.
- `test_planning_workspace_states` — 5/5 passed, covering exact A–F/base boundaries, mutation-free repeated loads, informational task payloads and filtered-state stability.
- `test_planning_ui_stitch_layout_guard` — 17/17 passed.
- `test_scn_pln_add_001` — 8/8 passed after replacing superseded waiting-row actions and old awaiting-Finance primary copy with the PLN-CHG-015 contract.
- `test_scn_pln_remove_001` — 5/5 passed, including no-effective-change projection as `DRAFT_WITH_PLANNER_ACTION`.
- JavaScript syntax and Python compilation checks passed for the changed assets/services.
- `./scripts/bench-with-node.sh build --app kentender_procurement` completed assets and translations with the documented temporary `/tmp` WSL `fork` setting. The first unadjusted attempt completed asset bundling but reproduced Python 3.14 `forkserver` error 95 during translation merge.
- Focused Chromium A–F state checks — 6/6 passed.
- Focused Chromium base workspace/Add-to-plan preselection — 1/1 passed.
- Focused Chromium no-flash search/filter refresh — 1/1 passed.
- Focused Chromium Planning navigation lifecycle — 1/1 passed after aligning the test with the approved Change-context interaction and live builder-state action vocabulary.
- Focused Chromium keyboard-focus/mobile reflow checks for the empty, actionable-table and informational-waiting families — 3/3 passed at 390 × 844.

An initial removal-scenario setup hit a transient row lock while another reseed-heavy process was closing; the isolated rerun passed 5/5. Initial Chromium attempts were blocked while port 8000 was not running; only the local Frappe web process was started for the successful focused runs and was stopped afterward.

### Skipped and unrelated findings

Per instruction, the full MVP suite, whole-module gates, whole accessibility gate, Finance/approval cross-module gates and all cross-module regression suites were not run.

Browser server logs still show pre-existing requests to `/undefined` and `/desk/undefined` during adjacent editor/builder navigation. The focused lifecycle flow still passed, and this unrelated route-generation defect was not repaired in the PLN-CHG-015 slice. Unrelated dirty-worktree documentation, PDFs, deleted evidence images and prior Planning changes were preserved and not staged, committed or pushed.

## 16. PLN-CHG-016 financial-year context and lifecycle closure

Status: implementation ready for review; focused browser execution remains blocked by the local bench process failing to start because `logs/worker.log` is not writable.

### Requirement traceability

- The Core financial-context service now validates configured enabled Fiscal Years for invalid ranges and overlap, and projects stable IDs, governed inclusive dates, current/future/past indicators and Planning-open status.
- `planning_context.resolve_planning_context` is the sole workspace PE/FY default resolver. It applies explicit, authorised context first; restores valid Frappe user defaults; never defaults among multiple PEs; and applies current Open Plan, nearest future Open Plan, most recent past Open Plan, then current enabled no-Plan precedence. `select_planning_context` is the only new preference mutation.
- The workspace returns `planning_context` while retaining its temporary top-level selection fields. Browser `kt_state` is no longer treated as an authoritative PE/FY default, and deliberate selector changes call the server selection command.
- Demand FY eligibility derives only from approved `required_by_date` against configured inclusive periods. PLN-UI-03/04/workspace share the projection and formation rechecks it after source locks. Locked missing/outside/mismatch codes and messages are returned without adding a Demand FY field.
- Logical Plans now expose only `Open`; guarded pre/post-model-sync patches reject historical non-Open/close evidence and then remove the obsolete close/cancel columns. Version `Cancelled` remains immutable.
- The old `cancel_plan_update` API, generic confirmation and Comment replay marker were removed. PLN-UI-05B uses a mutation-free projection and a locked `cancel_empty_plan_update` command with task/hold checks, replay-before-token handling, fixed Plan Decision reason and Approved-plan return.
- The supplied `PLN-UI-05B.html` controls the modal hierarchy, summary, message, actions, typography and icon. Mock shell, breadcrumb and footer content were excluded.
- `SCN-PLN-REMOVE-001` stamps the post-removal boundary at 19 August 2027 09:15 EAT and exposes an idempotent cancelled boundary. The canonical `DMD-MOH-2027-019` seed already used 31 December 2027 and required no correction.

### Focused evidence

- `pln_chg_016_preflight.execute`: passed against `kentender.midas.com`.
- Targeted `Procurement Plan` DocType reload and guarded schema cleanup: passed.
- Python/JSON/Node syntax checks: passed.
- `test_planning_chg016_layout`: 2/2 passed.
- `test_planning_context_chg016`: 3/3 passed.
- `test_planning_workspace_states`: 5/5 passed.
- `test_remove_plan_item`: 12/12 passed.
- `test_scn_pln_remove_001`: 5/5 passed.
- Procurement asset build through `./scripts/bench-with-node.sh build --app kentender_procurement`: passed.
- Focused Playwright discovery/TypeScript transform for `planning-empty-update-cancel.spec.ts`: passed (1 Chromium test discovered).
- `test_planning_mvp1_schema`: 5/6 passed; the unrelated pre-existing `uniq_pln_open_version` index is absent on the focused test site. It was not repaired in this slice.
- Focused Chromium PLN-UI-05B test was added but not executed: `bench start` stopped because `/home/midasuser/frappe-bench/logs/worker.log` is not writable. No permission or unrelated bench-runtime repair was made.

Full MVP, whole-module, whole accessibility, Finance/approval cross-module and cross-module regression suites were intentionally not run. Unrelated dirty-worktree files were preserved and no commit or push was performed.

## 17. PLN-CHG-018 revision closure implementation

The six closure items are now represented by production and executable evidence: FY source/mismatch projection (`CL-01`), deterministic empty-successor cancellation invariants (`CL-02`), shared live method allow-list and fallback (`CL-03`), server-owned UI-09 action destinations with no executable export (`CL-04`), a complete HTML-artifact-to-fixture matrix (`CL-05`), and aligned ledger/state/audit pointers (`CL-06`).

Focused evidence files are `test_planning_context_chg016.py`, `test_remove_plan_item.py`, `test_get_plan_item_editor.py`, `test_update_plan_item.py`, `test_get_plan_implementation.py`, `test_planning_ui_05a_06_revision_services.py`, and `test_planning_ui_stitch_layout_guard.py`.

Closure-edit focused results: method resolver 3/3 passed; UI-09 implementation DTO 4/4 passed; empty-successor removal/cancellation 12/12 passed; FY context 3/3 passed; revision layout/artifact matrix 19/19 passed; UI-05A/UI-06 revision services 5/5 passed. The updater module's 13 changed/adjacent cases passed, while its pre-existing in-review funding setup case failed in the full-module sequence because a source lacked a proposed Budget Line; that same case passed 1/1 in isolation. The updater module therefore is not recorded as a clean full-module pass.

No asset build or browser smoke was executed as part of this closure edit. Release sign-off remains conditional on a clean updater module rerun, the build and protected-route smoke; prior historical results above are not claimed as validation of these new changes.
