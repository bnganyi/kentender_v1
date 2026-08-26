# KenTender Engineering Rules

KenTender is a modular public-procurement platform on Frappe/ERPNext v16. Its purpose is to manage the traceable lifecycle from public strategy and budget through procurement, contracting, delivery, assets, disclosure, and audit. Treat workflow meaning, permissions, evidence, and audit history as product behaviour—not administrative detail.

## 1. Authority and scope

Apply instructions in this order:

1. the user's current request and acceptance criteria;
2. the task-specific specification or implementation pack named by the user;
3. the closest applicable `AGENTS.md` or `AGENTS.override.md`;
4. this repository-level file;
5. current, non-archived architecture and module documentation.

If two applicable sources materially disagree, identify the exact conflict and stop before implementing the disputed part. Archived documents and code are historical reference only unless the task explicitly targets them.

The root `CLAUDE.md` is the command card and execution loop. It does not override this file.

## 2. Project structure and ownership

The repository root is `frappe-bench/apps/kentender_v1/`. It is a container repository, not a Frappe app. The product apps are the top-level `kentender_*` directories:

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

Do not create another app or parallel replacement module without explicit approval.

Primary dependency direction:

`core -> strategy -> budget -> procurement -> stores -> assets`

`suppliers`, `governance`, `compliance`, `integrations`, and `transparency` are side applications that consume published interfaces. `transparency` is read-only/publication-oriented; `integrations` adapts external systems and does not own business rules.

Rules:

- The app that owns a record owns its invariants and write operations.
- No upstream or reverse dependency, deep import into another app's internals, or cross-app direct database write.
- Cross-app interaction uses an explicit public service or API owned by the relevant app.
- Put genuinely shared primitives and contracts in `kentender_core`; do not move domain behaviour there merely for convenience.
- Before changing a cross-app contract, identify the owner, consumers, compatibility impact, and contract tests.
- Treat sibling bench apps such as Frappe and ERPNext as read-only unless an explicit task authorizes an upstream change or tracked core patch.

The canonical traceability chain is:

`Strategy -> Budget -> Demand/Requisition -> Plan -> Tender -> Bid -> Evaluation -> Award -> Contract -> Inspection -> Stores/Assets -> Reporting/Audit`

Preserve identifiers, record lineage, approvals, actor/time/reason evidence, and organizational scope across that chain.

## 3. Change discipline

Before editing:

1. Inspect `git status` and preserve existing user changes.
2. Read the named implementation pack, target code, callers, public contracts, and focused tests. Do not read every project document by default.
3. Confirm the owning app and the smallest coherent change.
4. State a short plan for multi-app, migration, permission, workflow, or substantial UI work.

While editing:

- Implement only the requested scope. Avoid speculative refactors, broad formatting, unrelated cleanup, duplicate modules, shadow workflows, and temporary bypasses.
- Reuse existing services, components, helpers, registries, fixtures, and patterns before introducing another abstraction.
- Preserve existing public contracts unless the controlling task explicitly approves a clean break or migration.
- Do not invent roles, states, approvals, identifiers, legal outcomes, or business rules. Surface the missing decision.
- Do not modify secrets, private site configuration, generated assets, test reports, framework code, or unrelated files.
- Do not add or upgrade production dependencies without approval.
- Do not commit, push, merge, rebase, or use destructive Git commands unless explicitly requested.

## 4. Frappe application rules

### 4.1 Use Frappe, do not imitate it

- Create apps, sites, and DocType scaffolds through supported Frappe commands and export flows. Do not hand-create fake framework scaffolding.
- Use DocTypes, permissions, hooks, patches, background jobs, caching, and Desk lifecycle conventions before inventing parallel mechanisms.
- Persistent schema and data changes require explicit DocType changes and patches/migrations. Do not hide migrations in runtime side effects.
- Use the repository's build wrapper and current `make` targets; do not guess commands or bypass the required Node version.

### 4.2 Keep layers clear

- **DocType controllers:** persistence lifecycle and thin, local invariants.
- **Services:** business orchestration, cross-record consistency, transitions, and reusable domain operations.
- **API:** small explicit endpoints that validate input, authorize the actor, and call services.
- **Client code:** interaction and presentation only; never the sole enforcement point for business rules.
- **Utilities:** lightweight helpers, not hidden service layers.

Services must be callable independently of a particular page. Avoid duplicating a business operation in a controller, API method, fixture, and browser handler.

### 4.3 Server authority and security

Every material server action must define and enforce:

- eligible source state;
- required role and organizational scope;
- input and business validation;
- resulting state and related-record effects;
- audit actor, time, and reason where applicable;
- predictable failure behaviour.

Never rely on hidden fields, disabled buttons, or client checks for authorization. Use Frappe permission APIs and re-check permissions inside whitelisted methods and services. Return only data the caller is allowed to see. Use translatable user messages and do not expose internal exceptions, SQL, secrets, or stack traces.

### 4.4 Documents, database, and transactions

- Prefer document APIs for writes so validation, permissions, hooks, and audit behaviour run.
- Lightweight `frappe.db` reads are acceptable when document behaviour is not required. Avoid raw SQL; when unavoidable, justify it, parameterize it, and cover it with tests.
- Do not use direct database writes to bypass validation or manufacture workflow state.
- Let the Frappe request lifecycle manage commits and rollbacks. Do not call `frappe.db.commit()` from ordinary request services.
- Long work belongs in a background job. Jobs must be idempotent, scoped, observable, safe to retry, and explicit about transaction boundaries.
- Cache only derived/read data. Invalidate it on authoritative writes and never use cache as the system of record.

### 4.5 Idempotency, audit, and identity

- Retriable commands, seeds, patches, and integrations must be idempotent.
- Build idempotency on an immutable business key or explicit request key—not an auto-incremented document name, timestamp, or display label.
- Do not infer chronology or uniqueness from sequential names. Deletion and name reuse can leave stale generic references that are not formal Link fields.
- Material changes to approved value, funding, timing, method, evaluation, award, or contract baselines must use the applicable amendment/reapproval flow. Never silently rewrite approved history.
- User-visible status, server state, permitted actions, tasks, and audit history must agree.

### 4.6 Fixtures and seed data

- Fixtures and seeds must be deterministic, idempotent, tenant/site scoped, and safe to validate repeatedly.
- Build records through the real service layer. Do not reproduce service side effects with direct writes.
- A direct write is acceptable only for a test property the service cannot produce, such as controlled backdating; isolate it and explain why.
- Test data cleanup must target only owned fixtures. Confirm references before deletion, including generic reference fields.

## 5. Workflow and product rules

- A screen is not a workflow. Implement and test states, transitions, guards, responsibilities, exceptions, notifications/tasks, amendment paths, and audit effects.
- Do not remove governance, reservations, role queues, exception handling, reapproval, or evidence merely to make the happy path work.
- A deferred integration is acceptable only if the primary journey still has an explicit, safe, truthful outcome. A stub that blocks completion is a defect.
- For optional features, test the combination “use the option, then complete the primary flow”; separate isolated tests are insufficient.
- The primary action shown for a record must reflect what that actor can and should do next in the current state. Server-computed action order is part of the contract.

## 6. Frappe UI construction standard

The standard for complex screens is **Vue 3, mounted inside a real Frappe Desk Page**. This replaced hand-porting Tailwind/Stitch HTML into jQuery pages after a validated pilot (`kentender_strategy`'s `strategy_portfolio_pilot`) showed materially fewer defeat-CSS iterations and equivalent-or-better fit with Frappe's own patterns. Vue 3 is already vendored by Frappe framework's own esbuild pipeline (`esbuild-plugin-vue3`; the framework uses it internally for Form Builder, Workflow Builder, Print Format Builder) — mounting Vue in a Desk page requires no new dependency and no new build tooling.

Use tiered construction by screen type:

- Routine CRUD and administration: standard Frappe Form/List/Report/Workflow/Dialog APIs.
- Module landing/navigation: standard Frappe Workspace.
- Complex queues, workbenches, guided builders, multi-state workflows: Vue 3 (`<script setup>`, Composition API) mounted in a Desk Page, per this section.
- Public supplier/bidder experiences: a dedicated frontend, per existing convention.

Do not add `frappe-ui` as a dependency by default. Hand-authored Vue components styled from a small ported design-token stylesheet are sufficient; add `frappe-ui` only with explicit approval and a specific, named need.

### 6.1 Page and bundle structure

- The Page doctype folder holds only the `.json` record. The controller lives in `public/js/<slug>_page.js`, registered in the owning app's `hooks.py` `page_js` dict — the same convention every Desk page in this repo already follows.
- The Vue app lives under `public/js/<slug>/`: a `<slug>.bundle.js` entry point (auto-discovered by esbuild's `**/*.bundle.js` glob — no manual registration needed), a root `.vue` component, `components/`, `composables/`, `data/` (API adapters), `styles/` (token CSS).
- **Every `<slug>.bundle.js` entry point must bind `app.config.globalProperties.__ = window.__` and `app.config.globalProperties.frappe = window.frappe` between `createApp(...)` and `app.mount(el)`.** Vue's SFC compiler does not treat `__` as a global — any `__("...")` call inside a `<template>` block compiles to `_ctx.__(...)`, a component-instance property lookup, not a call to `window.__`. Without this binding it is `undefined` at runtime and the component's first render throws, producing a blank content area (Desk chrome/breadcrumb still renders since that isn't Vue-owned) — this is invisible to backend/contract tests and only shows up as a real browser console error. Confirmed missing and fixed in all three `kentender_strategy` Phase 7 bundles (2026-08-24); `kentender_core`'s `reference_data.bundle.js` is the reference example that has always had it right.
- Page controller pattern (mirrors Frappe's own `frappe/printing/page/print_format_builder_beta`):
  ```js
  frappe.pages["<slug>"].on_page_load = (wrapper) => frappe.ui.make_app_page({ parent: wrapper, ... });
  frappe.pages["<slug>"].on_page_show = (wrapper) => mount(wrapper); // guard against double-mount
  frappe.pages["<slug>"].on_page_hide = (wrapper) => unmount(wrapper); // calls app.unmount()
  ```
  Load the bundle lazily via `frappe.require("<slug>.bundle.js")`. Guard the async load against `on_page_hide` firing before it resolves (a "still wanted" flag checked inside the `.then()`), or a fast navigate-away-and-back can mount an app nothing ever unmounts.

### 6.2 Data, permissions, actions

- Call existing whitelisted Python endpoints via `frappe.call()`, wrapped in small composables (`useX()` returning reactive state plus a `refresh()`), not a generic data-fetching library.
- Server output is authoritative for both data and permitted actions. Render a record's action buttons only from a server-returned `allowed_actions`-style array — never a client-side status-to-action map. The server re-checks permissions on every mutating call regardless of what the client displayed; the client list is advisory only.
- After any mutating action, refetch from the server and re-render from the fresh response. Never optimistically mutate local state to reflect an action's expected result.

### 6.3 Confirmation dialogs

Do not use `frappe.confirm()`/`frappe.ui.Dialog` on a Vue-owned surface — they render outside the Vue root and inherit neither its state nor its styles. Build a small in-Vue dialog component instead: `v-if` toggle, `nextTick()` + `.focus()` on open, `@keydown.esc` to cancel, a conditional field for actions that need a reason.

### 6.4 Routing and lifecycle

- Put durable record identity in the URL path segment: `frappe.set_route(slug, id)`, read back via `frappe.get_route()[1]`. Never pass identity as an object argument or rely on `frappe.route_options` — in-memory route state is lost on refresh and direct links.
- Subscribe to `frappe.router.on("change", handler)` to react to in-page navigation (for example, opening/closing a route-addressable detail panel). **`frappe.router.off()` does not actually unbind anything** — Frappe's `EventEmitterMixin.off()` (`frappe/public/js/frappe/event_emitter.js`) rebuilds a fresh wrapper closure on every call and unbinds *that* from jQuery, not the wrapper `on()` originally bound, so the removal never matches. This is a confirmed framework bug, not app-specific. Mitigate with an active-flag guard — set `false` in `onUnmounted`, checked as the first line of the handler — rather than relying on `off()` to remove the listener; it stays bound but becomes inert.
- Verify every applicable path before calling routing work done: direct load, `page.reload()`, and browser back/forward (`page.goBack()`/`goForward()`). This repo's UI test suite has essentially no back/forward coverage anywhere — there is no existing precedent to lean on; write it explicitly for new work.
- **A `watch(routeParam, handler)` for a secondary tab/sub-route (e.g. loading a "History" tab's data) fires only on a later CLIENT-SIDE change of that param — never for the value the route already held on initial mount**, unless the watcher is declared with `{ immediate: true }` or the initial fetch explicitly checks the current tab value once its data dependency resolves. Without one of those, a direct load (or reload) landing straight on that tab renders an empty table with zero console errors and zero network requests — nothing about it looks broken except the missing data, so it's easy to ship having only ever tested by clicking through from the default tab. Confirmed 2026-08-24 on `strategy-review-task`'s History tab; fix is to also call the tab's loader once from inside the primary data-load function's success branch, gated on the current tab value at that moment.

### 6.5 Shared shell participation

- `kentender_core.cl_shell` is the shell system real Desk pages use. Call `kentender_core.cl_shell.enterNative({ sidebarWorkspaceKey, ... })` in `on_page_show` for the toolbar/breadcrumb chrome — it only touches a DOM sibling (`#kt-cl-chrome-host`), never the page's content region, so it is safe alongside a Vue-owned mount point.
- **Never call `kentender_core.cl_shell.mountContent()` on or near a Vue mount root.** It does a full innerHTML replace and will destroy Vue's DOM without Vue knowing. Vue's own `createApp().mount(el)` on a dedicated leaf node is the content-region equivalent; the two must never target overlapping DOM.
- Register the route in `kentender_core.cl_surface_registry.js`'s `surfaces` table (`routePrefixes`, `sidebarWorkspaceKey`, `chrome(...)`) the moment `enterNative()` is used at all. `kt_cl_shell_router.js` calls `leaveNative()` on any unregistered route once native chrome has ever been entered, stripping shell classes on back/forward through the page.
- `kentender_core.kt_shell`/`kt_state`/`module_registry.py`/the `back-to-workbench` testid contract are dead code with zero production callers — confirmed by grep, not assumed. Do not build against them.

### 6.6 Styling

- **`kt_industry_tokens.css` (`.kt-industry` scope, owned by `kentender_core`) is the one canonical design system for the entire application — a hard rule, not a suggestion.** No app may define its own competing token file (its own `--*-color-accent`, its own `.kt-btn`/`.kt-input`/`.kt-card`/`.kt-status` component rules, its own button-height/radius/spacing scale). Every Vue-in-Desk page wraps its root in `class="kt-industry"` and consumes `kt_industry_tokens.css` directly, loaded via that app's own `hooks.py` `app_include_css` pointed at `kentender_core`'s published asset URL (`/assets/kentender_core/css/kt_industry_tokens.css`, cache-busted via a local `_asset_version()` helper resolving `kentender_core`'s file path — see `kentender_strategy/hooks.py` for the pattern). Frappe serves every installed app's static assets from one shared `/assets/<app_name>/` namespace, so this cross-app load is the same mechanism as any of an app's own `app_include_css` entries, just pointed at a different app's published path — there is no platform reason to fork a second copy. This applies to vanilla-JS Desk pages too, not just Vue: `.kt-industry`'s classes are plain CSS (see `kentender_core/public/js/authorization_admin_pages.js` for a non-Vue consumer).
  - **Why this is a hard rule, not just a preference:** Strategy's Structure screen was rebuilt against pixel-precise design artboards and still visibly diverged from them through several rounds of fixes, because it had forked its own token file (`strategy_shared_tokens.css`, `.kt-strategy-ui`) that only superficially resembled Industry and had quietly drifted (wrong button radius, wrong secondary-button color, wrong status-badge contrast). The fork was deleted; Strategy now consumes `kt_industry_tokens.css` directly. See `docs/mvp-1-r1/02_strategy/IMPLEMENTATION_TRACKER.md` row STR-706 for the superseded decision record.
  - **A page-level Vue root component cannot be shared as a normal `app.component()`-registered child across a bundle boundary.** This bench's esbuild config does not mark `"vue"` external, so every `*.bundle.js` entry point carries its own separate copy of the Vue runtime. A component object built by one bundle's Vue instance loses its internal wiring — confirmed live: a `<style scoped>` component rendered as a child vnode by a *different* bundle's `createApp()` instance produced an element with zero `data-v-*` scope attribute, even though its extracted CSS (correctly scoped to that same attribute) was present in the page. To share a component across apps (e.g. the top page rail, `kentender_core.industry.mountPageRail`), publish a **mount helper** instead — a function that creates and owns its own isolated `createApp()` instance internally, exposing only an imperative `update()`/`unmount()` handle across the boundary — never a raw component object for `app.component()` registration. See `kentender_core/public/js/kt_industry/kt_industry_page_rail.bundle.js` for the reference implementation and `strategy_shared/composables/usePageRail.js` for a consumer.
  - `make ui-industry-design-gate` (Python gate + Playwright computed-style-parity spec, modeled on `ui-stitch-desk-chrome-gate`) enforces this: every page-level Vue root (found by locating `createApp(<Component>)` calls in `*.bundle.js` files — the actual mount-point convention, not a naming heuristic) must wrap `class="kt-industry"` or be named on `kentender_core.tests.test_industry_design_gate.LEGACY_BUNDLE_ALLOWLIST` (empty as of this writing — every current Vue-in-Desk page is on Industry). Add a module to that allowlist only when it is staged as Vue but deliberately not yet given its Industry pass; remove the entry once that module's Industry rebuild lands.
  - Civic Ledger (`kt_cl_*`, Tailwind-based content system) and Stitch Desk (`kt_stitch_desk_chrome.css`, its own Tailwind vocabulary, enforced internally-consistent by `ui-stitch-desk-chrome-gate`) are explicitly **not** covered by this rule yet — both predate it and are non-Vue (vanilla-JS/Tailwind fixture) systems today, so neither appears on the Industry gate's allowlist at all. They get migrated module-by-module, each rebuilt fully onto Industry the way Strategy was, not in place. The Civic Ledger sidebar shell (`kt_cl_shell.js`'s `enterNative()`, §6.4/6.5 above) is orthogonal to this rule and is never touched by an Industry migration — it is shared native chrome, not a content design system.
- Port design tokens (colors, spacing, radius, shadow, font stacks) as CSS custom properties scoped under one wrapper class on the component root, not `:root`, and load that token stylesheet as a static file via the owning app's `hooks.py` `app_include_css` (`_asset_version()`-cache-busted, same as `kt_industry_tokens.css`) — scoping under a class is what keeps a globally-loaded stylesheet from leaking into Desk chrome or another screen.
- **Never `import "*.css"` as a plain top-level statement inside a `<slug>.bundle.js` entry point.** `frappe.require("<slug>.bundle.js")` (§6.1) only ever loads that one `.js` URL — it does not discover or load a paired CSS output. esbuild still compiles a plain CSS import to a real file on disk, but nothing links to it: it isn't a metafile entry point, so it gets no `assets.json` key and no `<link>` tag ever points at it. The component mounts and no JS error fires, but every rule in that stylesheet silently never applies — a much quieter failure than the blank-page crash in §6.1, easy to miss in an accessibility-tree/DOM check that doesn't compare actual rendered appearance. Confirmed in all 3 `kentender_strategy` Phase 7 bundles on 2026-08-24 (`kentender_strategy/hooks.py`'s own comment claimed this import was "loaded via frappe.require()" — it was not, and the claim itself was never verified against a rendered screenshot). Put shared tokens in a static file loaded via `app_include_css` instead, or keep styling entirely inside each `.vue` file's own `<style scoped>` block, which Vue's runtime does inject correctly regardless of this esbuild limitation.
- Vue's `<style scoped>` (an auto-appended `data-v-*` attribute selector) is sufficient on its own to avoid Desk/Bootstrap style-bleed — confirmed empirically: a first-pass Vue screen rendered with zero button/select/table chrome bleed, no defeat-CSS iteration needed. Still avoid literal global class names Desk's own Bootstrap CSS already claims (`.btn`, `.table`, `.card`, and similar) inside scoped styles, as a matter of hygiene.
- Self-host any custom fonts using the existing `kt_cl_fonts.css` pattern (`kentender_core/public/css/kt_cl_fonts.css`): per-weight `@font-face` blocks split into `latin`/`latin-ext` subsets, one woff2 file each, registered via the owning app's own `hooks.py` `app_include_css`. Never load fonts from a CDN.
- **A CSS comment containing the literal two-character sequence `*/` anywhere inside it — including inside a file path, e.g. `_ds/industry-*/styles.css` — terminates that comment early.** Every character after that point becomes real CSS again until the browser's parser resyncs, which in practice means it silently drops every rule from there to the end of the file: `document.styleSheets[i].cssRules` returns a count far short of what the file actually contains, with no console error and no build-time failure (esbuild happily bundles the malformed file as-is). This is even quieter than the missing-`app_include_css` failure above: the file loads, `<link>` shows the right URL, `fetch()` of that URL returns the complete correct text — only actually counting parsed CSS rules (or comparing rendered appearance against the mockup) reveals it. Found 2026-08-24 in a comment referencing a path with a glob-style `-*-` segment. When writing a CSS comment that names a file path, directory glob, or anything else containing `*` immediately before `/`, rephrase to avoid the adjacency (or verify rule count / rendered appearance afterward) rather than trusting that the comment "looks closed" by eye.
- When editing a CSS or JS file that's loaded via `hooks.py` `app_include_css`/`app_include_js` (`_asset_version()`-cache-busted by that file's own mtime), the served `?v=` query param is computed once when a worker process imports `hooks.py`, not per-request — editing the CSS/JS file alone does not change the URL a running worker serves, so the browser can end up loading a stale cached response under an unchanged URL even after `bench build` and `bench clear-cache`. `touch hooks.py` (forcing the dev server's autoreload to reimport it) before re-testing in a browser, per the existing [[frappe-dev-asset-caching-gotchas]] memory — `bench clear-cache` alone is not enough for this specific case.

### 6.7 Testing

- A Vue-in-Desk screen is not done when its backend/contract tests pass. A whole class of bugs — including the missing-`globalProperties.__` blank-page failure in §6.1 — is invisible to `bench console`/API-level checks and only shows up as a real browser console error. Load the actual route in a browser (or Playwright) and confirm zero console errors before calling the screen done.
- Use `page.goto(..., { waitUntil: "domcontentloaded" })` plus an explicit element wait for Desk pages, not `waitUntil: "networkidle"` — Frappe's persistent long-poll/socket.io connections mean network never truly goes idle, and `networkidle` can hang or silently consume most of a test's timeout.
- Cover, per screen: live data render; loading/empty/error states (force the error case, for example via `page.route()` intercepting the endpoint with a 500 — do not assert only the happy path); a workflow action end-to-end including the confirm dialog and the authoritative refresh after it; direct load, reload, and back/forward on any route-addressable state; and, if the component holds any interval or subscription, an explicit open-close-reopen cycle asserting the call count does not multiply.

### 6.8 Vue-specific notes (this bench's pinned Vue 3.3.9)

- `<script setup>`'s automatic ref-unwrapping in templates applies only to top-level bindings. A ref nested inside a plain returned object (for example `const filters = { q: someRef }`) renders as the raw ref object in the template — a literal `[object Object]` if bound to an `<input>`. Expose each ref as its own top-level `const` instead.
- `defineModel()` is not available (stabilized in Vue 3.4; this bench pins 3.3.9). Use the plain `modelValue` prop plus `update:modelValue` emit pattern it desugars to.

### 6.9 Lazy-load page-specific assets — never dump them in `app_include_js`/`app_include_css`

**A route's own JS/CSS (fixture templates, live-data binders, dialogs, page-specific stylesheets) must be loaded only by that route's own `page_js`-mapped controller, via `frappe.require([...])` — never added to the app's global `app_include_js`/`app_include_css` in `hooks.py`.** Anything in those global lists loads on *every* Desk page, in every app, on every navigation, regardless of which route the user is actually on. Confirmed live 2026-08-26: kentender_procurement's "planning" route family alone (17 fixture/bind/dialog files) was loading globally, meaning the STD Configuration screens — which use none of it — were pulling in ~145 static requests per navigation, most of it dead weight for that page. This is a real, measured performance cost, not a style nitpick.

- `page_js` (route → controller file) is Frappe's own lazy mechanism — it only loads the mapped controller when the user navigates to that exact route. That part already worked correctly everywhere in this repo.
- The bug pattern was every *other* file that controller depends on (fixture template files, `*_bind.js` live-data binders, dialog components, the page's own CSS) getting dumped into the global include lists instead — a shortcut that avoided figuring out multi-file lazy loading, at the cost of loading it for every page forever.
- The fix: inside the controller's `on_page_load`, before calling whatever function actually renders the page, wrap it in `frappe.require([...])`:
  ```js
  frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
  	var page = frappe.ui.make_app_page({ parent: wrapper, ... });
  	wrapper.page = page;
  	frappe.require(
  		[
  			"/assets/<app>/js/<fixture_or_bind_file>.js",
  			// ...every other file this page's own render/bind logic needs...
  		],
  		function () {
  			mount(page); // now safe — every listed file has finished loading
  		}
  	);
  };
  ```
  `frappe.require()`'s callback fires only once every listed asset has finished loading (`Promise.all` under the hood) — safe to list several interdependent files in one call, since none of them should execute cross-file calls at their own top level (only later, when the controller's own render function runs inside the callback). It does **not** guarantee execution order *among* the listed files themselves (dynamically-injected `<script>` tags race by network arrival, not array order) — fine for files that only define functions/attach to a namespace at load time, wrong if any of them calls another listed file's function immediately at top level.
  **`on_page_show` does need its own guard against the same `frappe.require()` — Frappe guarantees `on_page_load` is *called* before any `on_page_show`, not that its async work has *finished*.** On a page's very first navigation Frappe calls `on_page_load` then `on_page_show` back-to-back, synchronously, without waiting for `on_page_load`'s `frappe.require()` promise to resolve. A page whose `on_page_show` has its own "not yet mounted, so mount now" fallback branch (a common pattern for surviving a fast navigate-away-and-back) will find the mounted flag still false at that point and fire a *second*, concurrent `mount()` — confirmed live 2026-08-26 on `budget-check-reserve`: a bare `mount()` in that branch threw "Check/Reserve fixture missing" because it ran before the fixture had loaded, and even where the resulting race doesn't throw (most pages degrade to a "fixture missing" placeholder instead) it still fires the mount's data call twice. The fix: extract a `mountWithDeps(page)` (or fold the guard into an existing `ensureMounted(wrapper)`) that both `on_page_load` and `on_page_show` call, holding a `page._xLoading` flag set `true` before `frappe.require()` and `false` in its callback — a concurrent call while a load is already in flight becomes a no-op instead of a second fetch.
- If a file is genuinely shared by more than one route, add the same `frappe.require()` entry to each of those routes' controllers — `frappe.require()` is safe to call redundantly (already-loaded assets are a no-op).
- **Not everything belongs in a page-specific `frappe.require()`.** Genuine cross-cutting Desk-wide chrome stays in `app_include_js`/`app_include_css` — the shared shell (`kt_cl_shell.js`/`kt_cl_sidebar.js`/`kt_cl_components.js`/`kt_cl_surface_registry.js`/`kt_cl_shell_router.js`), `kt_industry_tokens.css` (§6.6), the Stitch table-footer/pager components reused across many unrelated pages, and small self-triggering route-detection shims that must run globally to catch a legacy route *before* any specific page controller exists for it (for example `procurement_home_workspace.js`'s `Workspaces/Procurement Home` → `kt-procurement-home` redirect). The test is usage breadth, not file size: if grepping the file's exported namespace/function name turns up callers in one route's controller (or a small named family of routes), it is page-specific and belongs behind that route's own `frappe.require()`; if it turns up callers spread across many unrelated route families, it is genuinely global chrome.
- Before assuming a file is dead and deleting it outright, grep for its exported namespace/function name across every app's `public/js` — a hit count of zero across the whole repo is a real finding (flag it, don't silently keep loading it forever "just in case"), but do not guess a consumer that isn't there.

## 7. Test-driven development

TDD is the default for behaviour changes and bug fixes.

1. **Red:** express one observable requirement or reproduce the defect in the smallest appropriate test. Run it and confirm it fails for the expected reason.
2. **Green:** implement the smallest production change that passes the test.
3. **Refactor:** remove duplication and improve names or boundaries while the focused test remains green.
4. Add the next required case and repeat.

Test the lowest stable layer that owns the behaviour:

- service/domain tests for rules, invariants, transitions, and audit effects;
- API tests for input, permission, scope, serialization, and failure contracts;
- contract tests for public cross-app interfaces;
- browser tests for navigation, rendering, interaction, and integration—not for re-proving every service permutation.

For high-risk funding, submission, evaluation, award, contract, permission, amendment, and audit flows, include positive and negative cases. A bug fix requires a regression test unless the controlling task explicitly documents why automation is impractical.

Do not weaken assertions, bypass permissions, add arbitrary waits, or make production behaviour test-only to get green. Mock external system boundaries, not the service under test. Use deterministic data and the real service layer for setup.

## 8. Efficient test and diagnosis ladder

Use the least expensive level that can disprove the current change. Move upward only after the lower level passes.

| Level | Run when | Typical scope |
|---|---|---|
| 1. Focused reproducer | After each relevant edit in red/green | One test method, one Python module, one Vitest case, or one Playwright test |
| 2. Component/module | The focused case passes | Tests for the changed service, controller, page, or module |
| 3. Affected contract/app | A public interface, permission, workflow, or shared helper changed | Direct consumers and relevant app tests |
| 4. Feature/UI gate | A coherent feature slice is ready for review | The named current `make` gate, smoke suite, or build |
| 5. Full suite | Before merge/release when required, or after broad shared infrastructure, migration, permission framework, global shell, or cross-app changes | Full backend/frontend/UI suite appropriate to the risk |

Operational rules:

- During active repair, rerun the last failing focused test—not the full suite.
- Do not rerun an unchanged passing suite after an edit that cannot affect it.
- Discover exact targets with `make help` and repository scripts. Never guess a gate name.
- When a broad run reports several failures, save the results, group them by likely root cause, and reduce them to focused reproducers before editing.
- Batch related fixes, run their focused subsets, then run the broad level once to confirm the batch.
- If a failure is environmental, prove that with a minimal diagnostic; do not repeatedly rerun the same suite hoping it clears.
- Use a build, migration, seed, or browser run only when the changed layer requires it.
- Perform the unscripted primary user journey once at the feature/phase completion checkpoint, not after every small code fix. Check actual network failures and use fresh, valid data.
- A direct URL rendering successfully is not sufficient UI evidence; the real entry path and return path must also work.

Escalate test scope immediately only when the change itself is broad or dangerous—for example a migration, global permission rule, shared shell/router, app contract, framework patch, or release candidate. State why the broader run is justified.

## 9. Completion standard

Before claiming completion:

1. Review the full diff for scope creep, generated files, permission gaps, dependency violations, and accidental changes.
2. Compare implementation and evidence with every applicable acceptance criterion.
3. Run the appropriate level of the test ladder and the primary manual journey when the feature/phase is complete.
4. Confirm no required integration, state, permission, audit effect, or error path remains stubbed or misleading.

Do not mark a requirement, gate, phase, or tracker item complete from a scaffold, happy path, partial test subset, or unverified integration. Use `Partial`, `In progress`, or `Blocked` truthfully.

The completion report must state:

- files and behaviour changed;
- tests/checks run and results;
- manual flow run and result;
- tests or flows not run and why;
- intentional exclusions, assumptions, unresolved questions, and risks.

Never report a test, screen, or journey as passing unless it was actually observed.

## 10. Review priorities

Review behavioural and governance risk before style. Flag, in severity order:

- missing server permission, scope, validation, or transition enforcement;
- silent mutation of approved baselines or missing audit evidence;
- cross-app ownership, dependency, or direct-write violations;
- business logic implemented only in the client or duplicated across layers;
- UI actions that disagree with server state or lose context on navigation/refresh;
- missing negative-path, contract, workflow, audit, or regression tests;
- edits to archived, retired, generated, framework, secret, or unrelated files;
- completion claims unsupported by executed evidence.

If no material defect is found, say so and identify any remaining validation risk.
