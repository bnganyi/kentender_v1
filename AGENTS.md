# KenTender Repository Instructions

KenTender is a modular public-procurement platform built on Frappe/ERPNext v16. Treat this repository as production-oriented, governance-sensitive software: preserve legal/process meaning, app boundaries, permissions, auditability, and test evidence.

## Instruction precedence and conflicts

Apply guidance in this order:

1. The user's current explicit request and acceptance criteria.
2. The task-specific implementation pack or specification explicitly named by the user.
3. The closest applicable nested `AGENTS.md` or `AGENTS.override.md`.
4. This repository-level file.
5. Current, non-archived architecture and module documentation.

Do not infer that the words “never” or “do not” in an older document automatically override a newer explicit instruction. If two applicable sources materially conflict, stop before editing, identify the exact conflict and affected files, and ask for direction.

Archived documents and retired code are historical reference only unless the task explicitly targets them.

## Repository boundary

- The repository root is `frappe-bench/apps/kentender_v1/`; it is a container repository, not a Frappe app named `kentender_v1`.
- Frappe apps are the top-level `kentender_*` directories in this repository. Bench exposes them through symlinks under the repository's `apps/` directory; see `docs/architecture/mono-repo-v2.md` and the root `Makefile`.
- Work only inside this repository unless the task explicitly requires inspection elsewhere.
- Treat sibling bench apps (`frappe`, `erpnext`, `hrms`, and third-party apps) as read-only references. Do not modify them unless the user explicitly authorizes a framework or upstream-app change.
- Do not inspect or expose secrets, site configuration, private files, environment directories, database dumps, or logs unless the task specifically requires them. Never print credentials or tokens.
- Generated or transient directories such as `node_modules/`, `playwright-report/`, `test-results/`, caches, and built assets are not source files. Do not hand-edit or commit generated output unless the repository intentionally tracks it.

## App set and dependency direction

The allowed v3 apps are:

- `kentender_core`
- `kentender_strategy`
- `kentender_budget`
- `kentender_procurement`
- `kentender_suppliers`
- `kentender_governance`
- `kentender_compliance`
- `kentender_stores`
- `kentender_assets`
- `kentender_integrations`
- `kentender_transparency`

Do not create another app or parallel replacement module unless explicitly approved.

The primary dependency direction is:

`core -> strategy -> budget -> procurement -> stores -> assets`

Side apps (`suppliers`, `governance`, `compliance`, `integrations`, and `transparency`) consume published interfaces. Respect ownership and the detailed map in `docs/architecture/dependency-map-v3.md`.

- Do not add reverse dependencies or deep imports into another app's internals.
- Put shared primitives and cross-app contracts in the owning public interface, normally `kentender_core` when genuinely cross-cutting.
- Do not move behavior between apps merely to make an implementation easier.
- Before a cross-app change, identify the owning app, consumers, public contract, and dependency impact.

## Read only the context the task needs

Start with repository inspection and the files or implementation pack named in the task. Do not load every architecture document by default.

Read `docs/architecture/README.md` for routing when the relevant source is unclear. Read these documents when the change is architecture-sensitive, cross-app, or introduces a domain/workflow boundary:

- `docs/architecture/kentender_architecture_rules_v3.md`
- `docs/architecture/global-architecture-v3.md`
- `docs/architecture/dependency-map-v3.md`

Read `docs/prompts/architecture/architecture-restructure-cursor-prompt-pack.md` only for an explicitly requested architecture restructure or phased ticket from that pack. Despite its filename, treat it as a task specification, not as automatically loaded Cursor behaviour.

For module work, prefer the current PRD, domain/state model, role-permission matrix, UI specification, seed specification, and tests for that module. Ignore superseded drafts in `archive/` directories unless asked to compare or recover them.

If documentation, tests, and current code disagree materially, do not silently select one. Report the mismatch and use the user's stated task as the controlling scope.

## Working method

### Before editing

1. Inspect the relevant repository area and `git status`; preserve all existing user changes.
2. Confirm the task mode:
   - For review, explanation, planning, or diagnosis, do not implement unless explicitly asked.
   - For a requested change or build, implement it and validate it.
3. Trace the existing implementation before proposing a new one. Reuse established services, APIs, components, test helpers, and patterns.
4. Define the smallest coherent change. Do not mix unrelated cleanup, speculative refactoring, or future phases into the task.
5. For a substantive change, state briefly before the first edit:
   - goal and acceptance criteria;
   - affected apps and likely files;
   - explicit scope exclusions;
   - validation plan.

Use Plan mode for ambiguous, multi-app, migration, workflow, permission, or architecture-sensitive work. A small localized correction does not require a ceremonial plan.

### While editing

- Make the smallest maintainable change that fully satisfies the requirement.
- Preserve public behaviour and compatibility outside the stated scope.
- Do not create duplicate modules, compatibility scaffolding, shadow workflows, or temporary bypasses unless explicitly required.
- Do not invent missing business rules, roles, approvals, workflow states, identifiers, or legal outcomes. Surface the decision needed.
- Do not add or upgrade production dependencies without explaining the need and receiving approval.
- Do not modify unrelated files, reformat broad areas, or overwrite user changes.
- Do not run destructive Git operations. Do not commit, push, merge, rebase, or amend unless explicitly requested.
- Comments should explain non-obvious business or technical reasons, not restate the code.

### Before completion

1. Review the complete diff for scope creep, permission gaps, architectural violations, and accidental generated-file changes.
2. Run the narrowest relevant checks first, then the appropriate broader tests for affected contracts.
3. Never claim a test or manual flow passed unless it was actually run. Report blocked or skipped validation with the reason.
4. Confirm that the result matches the named requirement or acceptance criteria—not merely that the code compiles.

### Efficiency and iteration discipline

- Verify unfamiliar framework mechanisms empirically before building on them. Before writing a feature against a framework interaction you haven't personally exercised in this codebase (routing, page lifecycle, event wiring, async/transaction boundaries), write a minimal throwaway probe that exercises the real interaction path and confirms your assumption. Do not assume framework behavior from documentation or prior experience with a different version.
- Test the real interaction path, not the shortcut path, before calling a phase done. A page that renders correctly via direct URL navigation is not verified — click-through navigation from the actual entry point (button, menu, workflow transition) must be exercised at least once before a UI phase is marked complete. Framework routing/state can differ across three distinct paths in this codebase — direct load, `frappe.set_route()` programmatic navigation, and browser back/forward (`popstate`) — confirm all three that apply, not just the first one that happens to work. Browser back-navigation in particular resolves Frappe's hide/show/route-change event order differently than a forward `set_route()` call and has silently broken chrome that looked fine on every other path (see the `kt_cl_surface_registry` gotcha above).
- Batch diagnosis before batch fixing. When a broad test run surfaces a failure, review the surrounding code for related issues before fixing the single visible one and re-running everything. Do not run the full suite after every single-line fix; use narrow/targeted test runs during active iteration and reserve full-suite runs for phase boundaries and pre-completion verification.
- Seed/test fixtures must call the real service layer, not duplicate its side effects. Constructing fixtures via direct DB writes that hand-reconstruct what a service function would have done (audit rows, timestamps, task creation, derived fields) creates a second implementation that silently drifts from the first every time the real one changes. Prefer calling the actual service functions to build fixtures. Where a direct write is unavoidable (e.g., backdating), comment why, and treat it as a standing liability to re-check whenever the corresponding service function changes.
- Checkpoint with the user before continuing past a natural demo point in any multi-phase module. For any module split into phases where a UI phase completes, stop and show a live screenshot or short demo before continuing to the next phase — do not run an entire multi-phase module autonomously to completion without a midpoint check-in. This is the cheapest point to catch a design or functional mismatch.

### Hard completion-status rule

- Never mark a gate, tracker row, requirement, acceptance criterion, module wave, plan step, or task as `Done`, `Complete`, or equivalent unless its entire stated scope and every applicable acceptance criterion have actually been implemented and the required validation evidence has passed.
- A prerequisite, partial slice, narrow happy path, scaffold, passing subset of tests, or implementation that still requires material integration or verification must remain `Partial`, `In progress`, or `Planned` as appropriate.
- Do not infer completion from progress. Before changing any persistent status to complete, compare the implementation and executed evidence against the full controlling contract item by item.
- If a completion status was recorded prematurely, correct it immediately and explicitly identify the remaining work. Never preserve an inaccurate completion status for presentation, momentum, or convenience.
- A phase cannot be marked Done without one unscripted, live, end-to-end run of its primary user journey. Automated Python/Playwright coverage is necessary but not sufficient — before setting a tracker row or gate to Done, perform a manual-equivalent click-through as a real user would do it (fresh data, no pre-conditioned shortcuts), watching actual network responses for errors, not just green assertions. A green test suite that never exercised the real journey is not evidence of a working journey.
- Test every optional-feature-plus-completion combination, not just each in isolation. If a workflow has an optional step (attachment, cost estimate, delegate assignment, multi-context selection), the test matrix must include "use the optional step, then complete the primary flow" — not only "complete the primary flow" and "use the optional step" as separate, disconnected tests.
- A deferred/stubbed integration that blocks the primary flow is a bug, not a scope boundary. Before deferring an integration point ("no real external service exists yet, wire it up later"), check whether skipping it leaves the primary user journey completable. If completing the primary journey now depends on that integration, deferring it without a safe stopgap (e.g., an explicit override, a default-pass behavior with a visible flag) is a blocking defect and must be flagged as such in the tracker — not filed as acceptable future work.
- For any screen that persists state and is reachable by its own URL (create/edit/detail routes), the live end-to-end run must include a hard page refresh after the state-changing action, not just the action itself. Loading a page via direct URL and loading it via client-side navigation after a save can diverge — the save can appear to fully succeed (success toast, correct-looking transition) while the identifier it navigated to was never actually placed anywhere a refresh can recover it. "I clicked save and it looked right" is not equivalent to "I clicked save, refreshed, and the data was still there."

## Frappe engineering rules

- This is a Frappe application; act as an expert Frappe Framework developer, not a generic web developer bolting features onto an unfamiliar system. When a framework mechanism seems awkward, limiting, or produces an unexpected result, the default hypothesis is that there is an idiomatic Frappe way to do it that hasn't been found yet — not that the framework needs to be worked around. Before building a parallel mechanism (custom state-passing, hand-rolled permission checks, bespoke dialog systems, manual DOM diffing), search for and use the framework's own facility for it, even if the workaround would ship faster. A working-but-wrong-idiom fix has cost more later in this codebase than the time saved building it — see the `frappe.set_route` gotcha below, which shipped as an object-based `route_options` workaround (documented as a "known limitation" at the time) instead of the framework's own path-segment routing, and later broke "refresh loses data" in production across an entire module.
- Keep business logic in explicit Python service modules, not in DocType controllers, page JavaScript, or client-only handlers.
- Keep DocType controllers thin: lifecycle delegation, invariant enforcement, and calls into the owning service layer.
- Expose cross-layer operations through explicit, minimal APIs with stable inputs and outputs.
- Enforce critical validation, authorization, scope, state transitions, and financial/business rules on the server. Client validation may improve UX but is never the sole control.
- Use Frappe's permission and ORM facilities unless a reviewed exception is required. Do not bypass permissions or write directly to the database for convenience.
- Make retriable actions idempotent where duplicate execution could create approvals, reservations, submissions, awards, ledger effects, or audit events.
- Idempotency keys built from a business record's own auto-generated name (e.g. `f"{prefix}:{doc.name}:{step}"`, as `kentender_core.services.workflow_tasks.execute_routed_transition` does) are only safe if that name can never be reused. Several of this codebase's naming schemes are purely sequential ("next number for this scope"), not globally unique (UUID/hash) — so deleting a record and later creating a new one in the same scope can silently reissue its old name. If a stale `Workflow Task` (or any other row keyed by that same idempotency string) still exists from the deleted record, the new record's genuinely-first transition gets silently treated as an idempotent replay of the old one: the calling function returns `ok: true` with the *pre-transition* state, and the real mutation never runs — no error, no log, just a submission that silently doesn't submit. This is exactly why ad hoc data deletion on a sequentially-named doctype must also sweep every other table keyed by that name (not just doctypes with a formal Link field to it) — `grep` for the doctype name as a plain string field (`subject_type`/`document_type`/`reference_doctype`-style generic references), not only `"options": "<Doctype>"` Link fields, before considering a cleanup complete.
- Preserve audit trails and actor/time/reason data for material workflow decisions.
- Do not invent hidden workflow states. User-visible status, server state, permitted actions, and audit history must agree.
- Use explicit patches/migrations for persistent schema or data changes. Do not disguise migrations as runtime side effects.
- Keep APIs and services independent of a particular page where the capability is a domain operation.

For Frappe-managed scaffolding:

- Create apps with `bench new-app`.
- Create sites with `bench new-site`.
- Generate DocType scaffolds through Frappe's standard creation/export flow.
- Do not simulate unavailable generator output by handwriting framework scaffolds.
- If a required generator cannot be run safely, provide the exact command and report the blocker instead of fabricating the result.

## Product and workflow rules

- Preserve the canonical business traceability chain: Strategy -> Budget -> Demand/Requisition -> Plan -> Tender -> Bid -> Evaluation -> Award -> Contract -> Inspection -> Stores/Assets.
- Preserve app ownership, record lineage, approval evidence, and role/organizational scope across that chain.
- Do not simplify away governance, reservations, role queues, exception handling, reapproval, or audit behaviour merely to complete a happy path.
- Material changes to an approved requirement, value, funding, timing, procurement route, evaluation, or award must follow the applicable amendment/reapproval rules; do not mutate an approved baseline silently.
- Every server action must define eligible source state, required role/scope, validation, resulting state, audit effect, and failure behaviour.
- No module is considered implementation-ready solely because screens exist. Follow the applicable PRD, domain/state model, role-permission matrix, UI specification, seed specification, and smoke contracts.

## UI and navigation

- Prefer the approved workspace-first pattern: landing/workspace -> queue -> detail/workspace -> guided builder or form. Do not fall back to raw DocType-first UX where a product workspace is specified.
- Stitch output is approved design input, not production architecture. Hand-port it into maintainable Frappe pages, components, CSS, and APIs. Do not ship static mock shells, iframes, duplicated fake data, or client-side business behaviour copied from a mockup.
- Preserve the repository's design tokens, accessibility behaviour, responsive layout, test IDs, and established shared components.
- Avoid developer-oriented instructions in end-user UI. Copy must describe the user's decision, evidence, consequence, and next action.

### Stitch Desk chrome fidelity

- Register every new Stitch-ported Desk page in `kentender_core.stitch_desk_chrome_registry.STITCH_DESK_SURFACES` in the same change that adds it, and run `test_stitch_desk_chrome_gate` before considering the page done. This is an existing, enforced cross-module gate that catches Desk-bleed color/typography/chrome regressions — a page left unregistered is silently exempt from the one automated check built for exactly this problem.
- Module CSS must chain color/spacing/typography from `kt_stitch_desk_chrome.css`'s `--kt-stitch-*` custom properties (e.g. `var(--kt-stitch-primary, #003d9b)`), never hardcode independently. New component CSS must chain through the same tokens, not introduce a second source of truth.
- Do not reintroduce these already-fixed Desk-bleed defects (each has a specific, documented fix in `kt_stitch_desk_chrome.css`): Win98 outset buttons, missing Tailwind Forms select chevrons, wrong Espresso font-weight/letter-spacing on body/labels, wrong primary-button hover color (must stay white, never on-primary-container ink), editable inputs rendering as disabled/surface-tinted instead of white, wrong table/section header chrome (must use the muted DS recipe, not primary-fixed/square), wrong card border color (must be outline-variant/border-subtle).
- Follow the established `<module>_ui_fixtures/<screen>.js` file-per-screen convention (see Strategy/Budget/Planning), not flat `<module>_<screen>_page.js` files — this keeps new pages discoverable the same way existing ones are and lines up with the registry's own naming.
- Pixel-fidelity verification must compare actual values, not impressions. Before marking a UI phase done, extract the mockup's real color hex codes, font-family stack, and spacing/radius tokens from its Tailwind config (or computed styles) and diff them line-by-line against the implementation's CSS — do not rely on a screenshot "looks right" pass. Matching fixture text content is not the same as matching visual design; both are required and must be verified separately.
- When hand-porting a Tailwind-based mockup to plain CSS (required — Desk pages cannot load Tailwind CDN), build the token table first. Translate the mockup's custom color/spacing/font tokens into a small set of CSS custom properties in one place (chained from `--kt-stitch-*` per above), then write component rules only in terms of those tokens. Never transcribe a Tailwind utility class's approximate pixel value by eye into a hand-written rule.
- Known Frappe/Desk routing and rendering gotchas — apply these by default, do not rediscover them per module:
  - Any `position: fixed` element must offset from the left by the sidebar width (`var(--sidebar-width, 256px)` or the module's equivalent token) or it renders hidden under Desk's persistent sidebar.
  - `frappe.set_route(name, {key: value})` — an **object** arg — does not put `key` in the URL; Frappe's own `push_state()` never serializes it, and the value only exists in the in-memory `frappe.route_options`, lost on any refresh or direct link. **Do not "fix" this by reading `frappe.route_options` with a URL-query-string fallback** — that pattern shipped in this exact module, was documented as a known limitation, and still broke "refresh loses data" in production across four page controllers. Use Frappe's actual idiom instead: pass the identifier as a plain **string/positional** arg — `frappe.set_route(name, id)` — which Frappe appends as a real URL path segment (`route[1]`, refresh-safe); read it back with `frappe.get_route()[1]`. This is how every other KenTender module's detail/edit routes already work (e.g. `kentender_budget`'s `budget_workspace_shell.js` `budgetCodeFromRoute()`) — match that convention rather than reinventing state-passing.
  - Two page controllers must never share one `page_js` file with a blind `frappe.pages[name] = frappe.pages[name] || {}` for multiple route names — this silently stubs out whichever name isn't currently loading and permanently blanks that page on its real first visit. Only attach handlers when `frappe.pages[name]` already resolves to a real wrapper.
  - Never repaint a component with `$body.html(jQuery(markupString).html())` when the markup's own root element carries the test id / style-scoping class — this silently strips that root element on every re-render. Use `$body.html(markupString)` directly.
  - Custom-styled dialogs must be appended inside the page's own styled root container, never via `frappe.ui.Dialog` (renders outside that scope and won't match the design). `frappe.confirm()` is a thin wrapper around `frappe.ui.Dialog` and has the exact same problem despite not looking like a Dialog call at the use site — grep for `frappe.confirm(` alongside `frappe.ui.Dialog(` when auditing a module for this. The established replacement is a plain-HTML dialog template (backdrop `div` + card with header/title/close, body, footer with Cancel + primary/danger action) appended inside the page's own markup and toggled via a `hidden` attribute — see `departmental_needs_review_page.js`'s `reasonDialogTemplate()`/`openReasonDialog()` (generalized to also cover a reason-less confirm) and `departmental_needs_create_page.js`'s `confirmDialogTemplate()`. Reuse an existing module's dialog CSS classes (e.g. `.kt-nds-reason-dialog*`) across multiple confirm/prompt dialogs in that module rather than inventing a new class family per dialog.
  - `kt_stitch_desk_chrome.css` forces `border-width/border-color/background-color: ... !important` onto every bare `input`/`select`/`textarea` inside `.kt-stitch-canvas` (needed for real form fields). Any screen with a deliberately borderless/transparent control — an inline table-cell edit, an inline currency amount, anything the mockup renders with `border-0`/transparent background — must counter this with its own `!important` on `background`/`border`/`border-radius`, matching the pattern already used by Budget's, Strategy's, and Planning's table-cell inputs. Skipping the `!important` doesn't make the control invisible-and-broken in an obvious way — it silently produces a bordered white box with whatever padding you wrote, which reads as "slightly cramped" rather than "clearly wrong" and is easy to miss on a casual look.
  - `app_include_css` entries are loaded globally on every Desk page, not scoped per-route — a class name is not implicitly scoped to the screen you're styling it for. Before introducing a new component class in a module CSS file, grep the module's *other* CSS files (not just the one you're editing) for the same class name; a second, differently-shaped rule for the same class will silently override or be overridden by the first wherever both screens share the cascade, breaking whichever screen loses.
  - `frappe.request.cleanup()` auto-shows any `_server_messages` on a response via its own `frappe.msgprint()` popup whenever no handler is registered for the response's `exc_type` — **independent of, and in addition to, whatever the caller's own `callback`/`error` function does with that same response.** Passing `error_handlers: {}` does *not* suppress this (it only registers handlers keyed by exact `exc_type`, which a module's own custom exception class will never match, so the fallback still fires). The result of getting this wrong: after fixing a "generic Request failed" bug by switching `raise` to `frappe.throw()` so the real message reaches the client (see the `errors.py::fail()` fix elsewhere in this file), every validation error started showing as a raw, undesigned "Message" popup dialog *on top of* the module's own on-brand toast — the exact vanilla-Frappe-chrome problem this file already warns about, just reached through a different door. The correct, dedicated suppression is `frappe.call({ ..., silent: true })` — it has no effect on the caller's own `callback`/`error` handling, it only stops Frappe's own auto-popup. Any module wrapping `frappe.call()` in a custom `call()` helper that reads `_server_messages` itself (as this codebase's convention does) must set `silent: true`.
  - `document.body`'s `kt-cl-shell`/`kt-cl-shell-native` classes (the ones every Stitch native-chrome CSS selector is scoped under) are managed by **two independent mechanisms that must both be told about a route, or they fight each other**: each page's own `enterShell()`/`on_page_hide → leaveNative()` calls, *and* `kentender_core`'s global `kt_cl_shell_router.js`, which listens to `frappe.router.on("change", ...)` and calls `leaveNative()` on **any** route not found in `kentender_core.cl_surface_registry` — regardless of what the page itself just did. A module whose routes aren't registered there will intermittently lose all native-shell styling (buttons render as unstyled black default `<button>`s, sidebar/breadcrumb chrome disappears) specifically on browser back/forward navigation, because `popstate`-triggered routing resolves the hide/show/route-change order differently than a `frappe.set_route()` forward navigation, and the registry-driven `leaveNative()` can fire *after* the page's own `enterNative()` on that path. Register every native-chrome route's prefix in `kentender_core.cl_surface_registry` in the same change that adds the page — do not rely solely on each page's own manual `enterShell()` call, even though that call alone is sufficient on first load. This is a **different** registry from `kentender_core.stitch_desk_chrome_registry` (Python, CSS/pixel-fidelity gate) — a page needs both, and being registered in one does not imply the other.
- Verify interactive/re-rendered states, not just first paint. Bugs live disproportionately in state after a client-side re-render (add/remove a row, change a dropdown) — a screen that looks correct on load must also be re-checked after triggering at least one such interaction.
- Diff computed styles on *every distinct control variant* on the page, not one representative sample. A top-level text field, an inline table-cell edit, and an inline currency amount can each carry different CSS and different chrome-bleed exposure even on the same screen — verifying one and assuming the others match by similarity is how a boxed-input regression like the one above survives a "pixel fidelity verified" pass.
- A `<select>`'s empty/placeholder option must be visually and textually impossible to mistake for a real selection: mark it `disabled` (most browsers grey it out and it can't be silently re-selected) and never give it the same label as the field's own column header or field label. A placeholder reading "Unit" in a column header "Unit" looked filled-in at a glance, so users left it unselected without noticing, and only found out at submission — with a generic "must have a unit" message that pointed at the whole form, not the one empty select. This is the same failure shape as an unlabeled disabled button: the control *looks* complete but silently isn't, and the cost lands entirely on the user, downstream, with no visible cause.
- The primary action surfaced for a record (e.g., a workspace row's single action button, driven by `actions[0]` from a server-computed list) must be the action the record's owner is actually going to take next, not a generic default. A Draft/Returned need's own owner opening it from the workspace is going to edit it, not read a preview of it first — routing them through a read-only "View" screen that then requires a second click to "Edit" is friction with no purpose, even though "View" a technically-valid, harmless action. When a server endpoint computes an ordered actions list consumed by `actions[0]`, order it by what's actually next for that state/owner combination, not by an incidental/historical order.

For workbench-to-builder/form navigation, use the shared `kentender_core` shell and the canonical specification:

`docs/prompts/strategy/1. ken_tender_frappe_context_preserving_form_navigation_pattern.md`

When applicable:

1. Register the module consistently in `kentender_core/kentender_core/module_registry.py` and `kentender_core/public/js/kt_module_registry.js`.
2. Mount `kentender_core.kt_shell.mountHeader()` on builders and guided forms.
3. Use `kentender_core.kt_state` to save and restore workbench context.
4. Expose `data-testid="back-to-workbench"` through the shared shell.
5. Cover the return path with `tests/ui/helpers/moduleShell.ts` and `expectBackToWorkbench`.
6. Do not use `frappe.set_route("/desk")` or raw `location.assign` as the primary exit path.

Strategy-specific current rule: the primary UX is the Strategy Management workspace (`strategy_workspace.js`) with Plan Info, Structure, Review, and Audit tabs. The legacy `/app/strategy-builder/<plan>` route redirects to the workspace Structure tab and is not the primary editing surface.

For Workbench typography changes, follow:

`docs/prompts/architecture/KenTender Workbench Typography v1.0.md`

Use the established `--kt-wb-*` tokens rather than introducing ad hoc typography values.

## Procurement layout

Procurement subdomains live below `kentender_procurement/kentender_procurement/` (for example, `demand_intake/`). Follow `kentender_procurement/PROCUREMENT_INTERNAL_STRUCTURE.md`; do not flatten subdomains or place procurement-owned logic in another app.

## Testing and validation

Every substantive story or correction must consider:

- service/domain behaviour;
- validation and invariants;
- permissions and organizational scope;
- allowed and forbidden workflow transitions;
- failure and exception paths;
- audit effects;
- critical UI flow where UI behaviour changed;
- cross-app contract tests where a public interface changed.

Add or update focused tests with the implementation. High-risk funding, submission, evaluation, award, contract, permission, amendment, and audit flows require both positive and negative coverage.

Run `bench` from `/home/midasuser/frappe-bench`. Determine exact test commands from the repository's current scripts and documentation rather than inventing commands.

For asset builds, use the repository wrapper only:

```bash
./scripts/bench-with-node.sh build --app <app>
```

Do not run plain `bench build` or app-level Yarn builds; the wrapper supplies the required Node version. Run the wrapper from the repository root unless its own help/documentation states otherwise.

For Frappe core patches, source patches live under `patches/frappe/`. Apply them only when the task explicitly requires a tracked core patch:

```bash
./scripts/apply-frappe-patches.sh
./scripts/bench-with-node.sh build --app frappe
```

Do not edit the bench-local `apps/frappe` copy as an untracked shortcut.

## Current temporary and retired areas

- The IT Tender Configuration Wizard v1/v2 was retired in July 2026. Historical code is under `archive/it-std-wizard-retired-2026-07/`. Do not reactivate or extend it. The STD Engine remains active.
- The August 2026 MVP-1 Budget teardown removed legacy Budget DocTypes and `kentender_budget.seed.*` implementations. The rebuild is complete against `docs/mvp-1-r1/03_budget/KenTender_BUD-CHG-001_Clean_Budget_and_Funding_v1.0.md` (approved 2026-08-20) — `kentender_budget.seeds.kentender_mvp_v1_portfolio.upsert_kentender_mvp_v1_portfolio` is the active, real seed entry point (called via `kentender_core/seeds/kentender_mvp_v1/budget.py::upsert_budget()`). It no longer returns a skipped `mvp1-budget-teardown` result. `docs/mvp-1/02_budget/` is superseded — do not treat it as the live authority for new Budget work.
- `kentender_budget.seeds.works_master_budget_seed.upsert_works_master_budget` remains only as a compatibility skip stub. Do not treat it as an active seeding implementation.

## Completion report

End implementation tasks with a concise, evidence-based report containing:

- files changed;
- behaviour implemented;
- tests/checks run and their results;
- tests not run and why;
- manual verification still required;
- intentional exclusions or future-phase work not implemented;
- assumptions, unresolved questions, or risks.

Do not describe a task as complete while required validation is failing or a material requirement remains unresolved.

## Code review rules

When reviewing changes, prioritize behavioural and governance defects over style. Flag:

- cross-app ownership or dependency violations;
- business logic in controllers or client-only code;
- missing server-side permission, scope, validation, or transition checks;
- silent mutation of approved baselines;
- hidden states or UI/server action mismatches;
- missing negative-path, permission, workflow, or audit tests;
- raw Desk navigation that breaks workspace context;
- edits to retired, archived, generated, framework, or unrelated files;
- claims of validation unsupported by executed checks.

Report findings by severity with file references and concrete consequences. If no material finding exists, say so and identify any residual testing risk.
