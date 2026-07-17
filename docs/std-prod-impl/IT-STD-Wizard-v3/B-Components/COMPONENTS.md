# Civic Ledger Desk Chrome — Component Contract

Source mock: [code.html](./code.html) · Tokens: [DESIGN.md](./DESIGN.md)

The mock is ported to Frappe Desk faithfully across all three regions (left nav,
top bar, full content area) using a **one-time compiled, scoped Tailwind
stylesheet** and a **reusable component library** so subsequent pages compose
instead of rebuild.

## Namespace

- `kentender_core.cl_code_spec` — canonical Tailwind class strings copied from `code.html` (single source of truth for every block; consumed by components and the Python parity guard).
- `kentender_core.cl_components` (aliased as `kentender_core.cl.components`) — the component library.
- `kentender_core.cl_sidebar` (aliased as `kentender_core.cl.sidenav`) — curated, config-driven sidenav.
- `kentender_core.cl_shell` (aliased as `kentender_core.cl.shell`) — lifecycle (`enter`, `leave`, `mountPageChrome`).

## Opt-in shell

```js
kentender_core.cl_shell.enter({
  workspaceKey: "Procurement",
  sidebar: { portalTitle, portalSubtitle, items: [...curated IA] },
});
kentender_core.cl_shell.mountPageChrome(page.main, { toolbar, pageHeader, mainHtml });
```

`body.kt-cl-shell` is added; Frappe `.navbar`, `.page-head`, and
`.body-sidebar-container` are hidden. A **custom sidenav** (`#kt-cl-sidenav`)
replaces the native Workspace Sidebar.

## Component library

Stateless data-in / HTML-out renderers under `kentender_core.cl_components`. Each
maps to a `code.html` block and pulls its class strings from `cl_code_spec`.

| Component | API | testid |
|-----------|-----|--------|
| Sidenav (config-driven) | `cl_sidebar.mount(workspaceKey, { portalTitle, portalSubtitle, avatarUrl?, items, footerItems? })` | `kt-cl-sidenav`, `kt-cl-sidebar-brand`, `kt-cl-sidebar-footer`, `kt-cl-nav-item`, `kt-cl-nav-group`, `kt-cl-nav-child` |
| Top bar | `topBar({ title, showSearch?, searchPlaceholder?, avatarUrl? })` | `kt-cl-toolbar`, `kt-cl-toolbar-title`, `kt-cl-toolbar-search` |
| Breadcrumbs | `breadcrumbs({ items: [{ label, route? }], current })` | `kt-cl-breadcrumbs`, `kt-cl-breadcrumb-current` |
| Page header | `pageHeader({ breadcrumbs, current, subtitle, actions?, actionsHtml? })` | `kt-cl-page-header`, `kt-cl-page-header-actions` |
| Button | `button({ label, icon, variant: 'primary'|'outline', testid?, key? })` | per `testid` |
| KPI card | `kpiCard({ variant: 'metric'|'progress', tone, label, value, icon, delta?, progress?, progressLabel? })` | `kt-cl-kpi-card` |
| Bento helpers | `metricsGrid(cardsHtml)`, `bentoGrid({ metricsHtml, asideHtml })` | `kt-cl-metrics-grid`, `kt-cl-bento` |
| Calendar widget | `calendarWidget({ title, viewAllLabel?, items: [{ day, month, title, subtitle, tone }] })` | `kt-cl-calendar`, `kt-cl-calendar-item` |
| Data table | `dataTable({ title, filter?, columns, rows, footerText })` | `kt-cl-data-table`, `kt-cl-table-row`, `kt-cl-table-filter`, `kt-cl-table-footer` |
| Status chip | `statusChip({ tone: 'approved'|'review'|'draft'|'rejected', label? })` | `kt-cl-status-chip` (`data-tone`) |

Sidenav item schema: `link` = `{ kind:'link', label, icon, route|url, active? }`;
`group` = `{ kind:'group', label, icon, keepClosed?, children:[{ label, route|url }] }`.
Groups collapse/expand with persistence (`localStorage`, keyed by `workspaceKey`).

## CSS pipeline

The Tailwind stylesheet is compiled **once, offline** (not `bench build`) and
committed. See [tools/civic-ledger-css/README.md](../../../../tools/civic-ledger-css/README.md).

- `important: '.kt-cl-shell'` scopes every utility under the shell.
- `corePlugins.preflight = false`, `container = false` — never resets Frappe, no
  leaked `.container`.
- Bootstrap ships `!important` base-color utilities (`.text-primary`,
  `.bg-primary`, `.border-primary`, `.text-secondary`, `.bg-secondary`) and
  `.hidden {display:none!important}` that differ from / beat Tailwind's
  selector-scoped (non-important) utilities. `kt_cl_code_layout.css` re-asserts
  those + the responsive `sm:`/`md:` display classes scoped to `.kt-cl-shell`.

## Assets

| File | Role |
|------|------|
| `kt_cl_code_spec.js` | Canonical Tailwind class strings from `code.html` |
| `kt_cl_components.js` | Component library |
| `kt_cl_sidebar.js` | Curated, config-driven sidenav |
| `kt_cl_shell.js` | Shell lifecycle |
| `civic_ledger.css` | Compiled, scoped Tailwind utilities (source: `tools/civic-ledger-css`) |
| `kt_cl_code_layout.css` | Hide Frappe chrome; canvas offset; Bootstrap collision overrides; list/collapse helpers |
| `kt_cl_fonts.css` | Self-hosted Public Sans, JetBrains Mono, Material Symbols |
| `kt_cl_routes.js` (procurement) | Permanent redirect: Procurement Home workspace → POC page |
| `kt_cl_components_gallery_page.js` (core) | Component gallery page script |

## Routes

- `/desk/kt-cl-shell-poc` — the faithful port of `code.html` (sidenav + top bar +
  full content: KPI bento, calendar, data table). The **Procurement Home** menu
  redirects here permanently (`kt_cl_routes.js`).
- `/desk/kt-cl-components` — component gallery: every component rendered in
  isolation (proof of reuse).

## Tests

- `kentender_core.tests.test_kt_cl_shell_layout_guard` — compiled-CSS scoping/tokens, all-block `code.html` parity markers, library exports, desk wiring for both pages, redirect wiring.
- `kentender_procurement.tender_management.tests.test_kt_cl_shell_poc_desk_wiring` — POC page composes from the library.
- `tests/ui/smoke/kt-cl-shell/kt-cl-shell-poc.spec.ts` — full chrome, curated IA, collapse, content parity, computed tokens.
- `tests/ui/smoke/kt-cl-shell/kt-cl-menu-wiring.spec.ts` — Procurement Home → POC redirect.
- `tests/ui/smoke/kt-cl-shell/kt-cl-components-gallery.spec.ts` — gallery renders every component.
