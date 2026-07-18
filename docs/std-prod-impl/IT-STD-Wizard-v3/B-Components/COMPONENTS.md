# Civic Ledger Desk Chrome — Component Contract

Source mock: [code.html](./code.html) · Tokens: [DESIGN.md](./DESIGN.md)

The mock is ported to Frappe Desk faithfully across reusable chrome and content
regions using a **one-time compiled, scoped Tailwind stylesheet** and a
**reusable component library** so subsequent pages compose instead of rebuild.

## Namespace

- `kentender_core.cl_code_spec` — canonical Tailwind class strings copied from `code.html` (single source of truth for every block; consumed by components and the Python parity guard).
- `kentender_core.cl_components` (aliased as `kentender_core.cl.components`) — the component library.
- `kentender_core.cl_sidebar` (aliased as `kentender_core.cl.sidenav`) — curated, config-driven sidenav (**POC / full-replacement mode only**).
- `kentender_core.cl_shell` (aliased as `kentender_core.cl.shell`) — lifecycle (`enter`, `leave`, `enterNative`, `leaveNative`, `mountPageChrome`, `mountContent`, `updateChrome`).
- `kentender_core.cl_surface_registry` — route → chrome metadata for registered Civic Ledger surfaces (IT STD Wizard A2 IDs first).
- `kentender_core.cl_shell_router` — global `frappe.router` bootstrap that activates native-sidebar mode on registered routes only.

## Shell modes (Step 1 + Step 2)

### Native-sidebar mode (default for production surfaces) — Step 2

```js
kentender_core.cl_shell.enterNative({
  sidebarWorkspaceKey: "procurement",
  toolbar: {
    breadcrumbs: [
      { label: "Dashboard", route: ["Workspaces", "Procurement Home"] },
      { label: "Tender Management", route: ["tender-management-v2"] },
    ],
  },
});
kentender_core.cl_shell.mountContent(page.main, {
  pageHeader: { title, subtitle, actions, hideBreadcrumbs: true },
  mainHtml: /* page body */,
});
```

### Top toolbar standard (C1-M1 — going forward)

Source: `C1-M1/code-in-progress.html` TopAppBar.

| Slot | Contract |
|------|----------|
| Left | **Context trail only** (`toolbar.breadcrumbs`) — ancestors with chevrons; **last crumb bold** (module/parent). Leaf page name is **not** in the strip. |
| Right | Notifications · Help · **name + role** · Avatar. **No search** (`showSearch` defaults `false`) |
| Icons | Borderless Material icon buttons (Desk chrome stripped in `kt_cl_code_layout.css`) |
| User meta | Name from session; role from first non-system boot role; avatar from `frappe.user_info().image` / initials |

### Page header standard

- **H1** = leaf page title (`pageHeader.title`) + subtitle + primary actions.
- **No duplicate breadcrumb row** under the strip (`hideBreadcrumbs: true` by default).

### Breadcrumb / trail wiring

- Trail items are `{ label, route? }` on `toolbar.breadcrumbs` (last item may still carry a `route`).
- Workspace crumbs use `["Workspaces", "<Workspace Title>"]`.
- Page crumbs use Desk slugs, e.g. `["tender-management-v2"]`.
- `updateChrome` / `mountContent` / `mountPageChrome` call `bindBreadcrumbRoutes`.


- Adds `body.kt-cl-shell` **and** `body.kt-cl-shell-native`.
- **Keeps** Frappe `.body-sidebar-container` (Step 1 Civic Ledger restyle via `kt_native_sidebar_civic.css`).
- **Hides** Frappe `.navbar` and `.page-head`.
- Injects persistent `#kt-cl-chrome-host` (toolbar) outside `page.main`.
- Activated automatically by `kt_cl_shell_router.js` when `frappe.get_route()` matches `cl_surface_registry`.
- Teardown via `leaveNative()` when navigating off registered routes.

### Full-replacement mode (POC / gallery demos)

```js
kentender_core.cl_shell.enter({
  workspaceKey: "Procurement",
  sidebar: { portalTitle, portalSubtitle, items: [...curated IA] },
});
kentender_core.cl_shell.mountPageChrome(page.main, { toolbar, pageHeader, mainHtml });
```

- Adds `body.kt-cl-shell` only (no `kt-cl-shell-native`).
- Hides native sidebar + top chrome; mounts custom `#kt-cl-sidenav`.
- Used by `/desk/kt-cl-shell-poc` and the component gallery. **Not** primary navigation.

## Component library

Stateless data-in / HTML-out renderers under `kentender_core.cl_components`. Each
maps to a `code.html` block and pulls its class strings from `cl_code_spec`.

| Component | API | testid |
|-----------|-----|--------|
| Sidenav (config-driven, POC only) | `cl_sidebar.mount(workspaceKey, { portalTitle, portalSubtitle, avatarUrl?, items, footerItems? })` | `kt-cl-sidenav`, `kt-cl-sidebar-brand`, `kt-cl-sidebar-footer`, `kt-cl-nav-item`, `kt-cl-nav-group`, `kt-cl-nav-child` |
| Top bar | `topBar({ breadcrumbs?: [{label,route?}], title?, showSearch?: false, showUserMeta?: true, userName?, userRole?, avatarUrl? })` | `kt-cl-toolbar`, `kt-cl-breadcrumbs` (in toolbar), `kt-cl-breadcrumb-current`, `kt-cl-toolbar-notifications`, `kt-cl-toolbar-help`, `kt-cl-toolbar-user-name`, `kt-cl-toolbar-user-role`, `kt-cl-toolbar-avatar` |
| Breadcrumbs | `breadcrumbs({ items, current, currentRoute?, variant?: 'page'\|'toolbar' })` | `kt-cl-breadcrumbs`, `kt-cl-breadcrumb-current` |
| Page title | `pageTitle({ title })` (leaf H1) | `kt-cl-page-title` |
| Page header | `pageHeader({ title?, subtitle, actions?, hideBreadcrumbs?: true })` | `kt-cl-page-header`, `kt-cl-page-header-actions` |
| Button | `button({ label, icon, variant: 'primary'|'outline', testid?, key? })` | per `testid` |
| KPI card | `kpiCard({ variant: 'metric'|'progress', tone, label, value, icon, delta?, progress?, progressLabel? })` | `kt-cl-kpi-card` |
| Bento helpers | `metricsGrid(cardsHtml)`, `bentoGrid({ metricsHtml, asideHtml })` | `kt-cl-metrics-grid`, `kt-cl-bento` |
| Calendar widget | `calendarWidget({ title, viewAllLabel?, items: [{ day, month, title, subtitle, tone }] })` | `kt-cl-calendar`, `kt-cl-calendar-item` |
| Data table | `dataTable({ title, filter?, columns, rows, footerText })` | `kt-cl-data-table`, `kt-cl-table-row`, `kt-cl-table-filter`, `kt-cl-table-footer` |
| Status chip | `statusChip({ tone: 'approved'|'review'|'draft'|'rejected', label? })` | `kt-cl-status-chip` (`data-tone`) |
| Queue summary card | `queueSummaryCard({ key, label, value, icon, accentClass? })` | `kt-cl-queue-summary-card` |
| Queue summary grid | `queueSummaryGrid(cardsHtml)` | `kt-cl-queue-summary-grid` |
| Tab bar | `tabBar({ tabs:[{key,label}], active })` | `kt-cl-tab-bar`, `kt-cl-ui00-tab-*` |
| Filter bar | `filterBar({ filters:[{key,label,type,options?,value?,hidden?}] })` | `kt-cl-filter-bar`, `kt-cl-filter-search`, `kt-cl-filter-sep`, `kt-cl-filter-fields`, `kt-cl-ui00-filter-*` |
| Filter wiring | `bindFilterBar($root, { onChange(key,value), namespace?, debounceMs? })` | standard search debounce + select change for all queue tables |
| Queue table | `queueTable({ columns, rows:[{id,cells}], footerText, pagination?, pageSize?, pageSizeOptions?, showPageSize? })` — footer right: Rows per page (left of pager) | `kt-cl-ui00-table`, `kt-cl-ui00-page-size`, `kt-cl-ui00-pager`, `kt-cl-ui00-row-*` |
| Create config modal | `createTenderConfigurationModal({ hasSelection, selectedLabel, preview, canCreate })` | `kt-cl-uim01-*` |
| **Configuration context strip (wizard chrome)** | `configurationContextStrip(context)` — **required on UI-01 + every CFG/WF page** (including **CFG-01**); **8 cells** from home/profile `context` DTO (C1-M3 §4). Do not add a 9th “Tender Configuration Ref” cell without a CL lock amendment. | `kt-cl-config-context-strip`, `kt-cl-config-context-*` |
| Next best action | `nextBestActionPanel({ label, reason, buttonLabel, route, tone? })` | `kt-cl-ui01-next-action` |
| Configuration steps grid | `configurationStepsGrid({ steps })` | `kt-cl-ui01-steps`, `kt-cl-ui01-step-CFG-*` |
| Completion & Handoff | `handoffPanel({ handoff })` | `kt-cl-ui01-handoff` |
| Overall Progress | `overallProgressPanel({ complete, total, progressPct })` — `%` is **average of per-step exit-condition progress**; meta is “X of Y steps complete” | `kt-cl-ui01-progress` |
| Step progress | Computed in `step_progress.py` (register builders in `STEP_CONDITION_BUILDERS`); CFG-01 live; other CFGs status-fallback until their screen ships | `progress_pct`, `show_progress_bar` on step rows |
| Resources | `resourcesPanel({ items })` | `kt-cl-ui01-resources` |
| Step details drawer | `stepDetailsDrawer({ step })` | `kt-cl-ui01-drawer` |
| Wizard step footer | `wizardStepFooter({ backLabel, saveLabel, continueLabel, … })` — **Back left**, Save + high-contrast Continue right (white on navy) | `kt-cl-wizard-footer`, `kt-cl-wizard-btn--*` |

### Wizard context strip (reuse contract)

All Tender Configuration wizard surfaces share one strip. Pass the `context` object from `get_tender_configuration_home` (or a future thin context API). Do **not** hand-roll a second strip.

Cells (fixed order): Package Ref · Title · Entity · Procurement Method · STD Family · Standard Tender Document · Configuration Status (+dot) · Issues.

Sidenav item schema (POC): `link` = `{ kind:'link', label, icon, route|url, active? }`;
`group` = `{ kind:'group', label, icon, keepClosed?, children:[{ label, route|url }] }`.

## Pattern lock (agents — do not skip)

Queue/list pages must **compose** the APIs above; do not re-implement table/filter/footer markup.
Wizard pages must **compose** `configurationContextStrip` — never duplicate the strip markup.

- Cursor rule: `.cursor/rules/kentender-civic-ledger-queue-lock.mdc`
- Playwright helpers: `tests/ui/helpers/ktClQueueContract.ts`, `ktClConfigContext.ts`, `ktClUi01LayoutContract.ts`
- Gates: `make -C apps/kentender_v1 ui-civic-ledger-queue-gate`, `ui-civic-ledger-ui01-gate`, and `ui-civic-ledger-cfg01-gate`
- UI-01 mockups: `seed_ui01_mockups_for_tests` → `TCFG-MOCK-SHOWCASE` + `TCFG-MOCK-CFG-01`…`09`
- CFG-01 page: `it_tender_configuration_tender_profile_page.js` + pins `kt-cl-cfg01-*` in `kt_cl_code_layout.css`
- CFG-01 follow-ups (explicitly out of ticket): multi-version STD picker; Run Readiness Check CTA; real CFG-02 TDS page; relational lots child table; strip Config Ref cell (needs CL lock amendment)
- Rollout matrix: [`docs/test-contracts/civic-ledger-queue-rollout-matrix.md`](../../../test-contracts/civic-ledger-queue-rollout-matrix.md)

Reference surface: UI-00 (`it-tender-configuration-dashboard`).

## Surface registry

`kt_cl_surface_registry.js` maps A2 screen IDs (`UI-00`, `UI-01`, `CFG-01`…`CFG-09`, `WF-01`…`WF-04`, `UI-M01`) to:

- `routePrefixes` — Desk page slugs (or empty for modal-only `UI-M01`)
- `sidebarWorkspaceKey` — native sidebar fast-path key (`procurement`)
- `chrome.toolbar` / `chrome.pageHeader` — default Civic Ledger chrome for the surface

**UI-00** (dashboard) and **UI-01** (configuration home) ship live page scripts; CFG/WF entries remain chrome stubs until those screens are implemented (they must adopt `configurationContextStrip`).

## CSS pipeline

The Tailwind stylesheet is compiled **once, offline** (not `bench build`) and
committed. See [tools/civic-ledger-css/README.md](../../../../tools/civic-ledger-css/README.md).

- `important: '.kt-cl-shell'` scopes every utility under the shell (native mode keeps this class).
- `corePlugins.preflight = false`, `container = false` — never resets Frappe, no leaked `.container`.
- Bootstrap `!important` collision overrides live in `kt_cl_code_layout.css` under `.kt-cl-shell`.
- Native Workspace Sidebar visual language: `kt_native_sidebar_civic.css` (Step 1).

## Assets

| File | Role |
|------|------|
| `kt_cl_code_spec.js` | Canonical Tailwind class strings from `code.html` |
| `kt_cl_components.js` | Component library |
| `kt_cl_sidebar.js` | Curated sidenav (POC full-replacement only) |
| `kt_cl_shell.js` | Shell lifecycle (full-replacement + native) |
| `kt_cl_surface_registry.js` | Route → chrome metadata |
| `kt_cl_shell_router.js` | Global router bootstrap |
| `civic_ledger.css` | Compiled, scoped Tailwind utilities |
| `kt_cl_code_layout.css` | Shell layout; mode split; Bootstrap overrides |
| `kt_cl_fonts.css` | Self-hosted Public Sans, JetBrains Mono, Material Symbols |
| `kt_native_sidebar_civic.css` | Restyle of native `.body-sidebar` |

## Routes

- `/desk/it-tender-configuration-dashboard` — **UI-00** Tender Configurations Dashboard (native shell + live queue).
- `/desk/it-tender-configuration-overview` — **UI-01** thin landing stub after create / Continue.
- `/desk/kt-cl-shell-poc` — full-replacement POC of `code.html` (demo only; not primary nav).
- `/desk/kt-cl-components` — component gallery.

Procurement Home **does not** redirect to the POC page (Step 1 retired `kt_cl_routes.js`).

## Tests

- `kentender_core.tests.test_kt_cl_shell_layout_guard` — CSS modes, library exports, desk wiring, native/router assets.
- `kentender_core.tests.test_kt_cl_surface_registry_contract` — A2 IDs + UI-00 page wiring.
- `tests/ui/smoke/kt-cl-shell/kt-cl-shell-poc.spec.ts` — full-replacement POC chrome.
- `tests/ui/smoke/kt-cl-shell/native-sidebar-restyle.spec.ts` — Step 1 native rail restyle.
- `tests/ui/smoke/it-std-wizard/it-wizard-shell.spec.ts` — Step 2 native shell persistence / teardown on UI-00.
- `tests/ui/smoke/kt-cl-shell/kt-cl-components-gallery.spec.ts` — gallery renders every component.
