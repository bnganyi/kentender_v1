# IT Tender Wizard — Native Frappe Desk Architecture

**Status:** Binding for all production IT Wizard screens  
**Version:** 1.0  
**Effective:** 2026-07-17

## Goal

Production IT Tender Configuration Wizard screens run as **native Frappe Desk pages** — single DOM, plain JS render modules, `frappe.call` API adapters, and shared CSS tokens. Stitch / `code.html` mockups under `public/it_tender_wizard_impl/` are **design reference only**, not runtime assets.

## Decision table

| Question | Decision |
|---|---|
| Production architecture | Native Desk page, single DOM, no iframe |
| Stitch HTML role | Design reference only, not runtime asset |
| Tailwind CDN | Forbidden in production |
| Existing iframe screens (S03–S15) | Transitional; migrate screen-by-screen |
| Screen 01 pattern | Architectural precedent — componentize, do not copy 15 times |
| Migration priority | S01 componentize → S02 → S03 → sequential |

## Why native (not iframe + hydrator)

| Requirement | Native Desk | Iframe + hydrator |
|---|---|---|
| Reliable in Frappe Desk | Strong | Fragile |
| Works without CDN | Yes | No |
| Easier Playwright testing | Yes | More brittle |
| Modals / session handling | Simpler | Cross-document complexity |
| Performance | Better | Extra document + hydration |
| Long-term maintainability | Better when componentized | Worse as screens grow |

## Target stack

```
Frappe Desk Page
  └── Thin *_page.js registrar (page_js hook only)
        └── it_wizard_shell.js (lifecycle, body class, sidebar)
              └── screens/*.js (per-screen _state + render)
                    ├── it_wizard_components.js
                    ├── it_wizard_routes.js
                    └── it_wizard_api.js
                          └── Frappe whitelisted APIs
```

## File layout

```
kentender_procurement/public/
  css/
    kt_fonts.css           # Self-hosted fonts only
    kt_it_wizard.css       # Shared tokens + shell + components
    it_wizard_*_page.css   # Screen-specific overrides (shrinking over time)
  js/
    it_wizard/
      it_wizard_shell.js
      it_wizard_components.js
      it_wizard_routes.js
      it_wizard_api.js
      screens/
        dashboard.js
        configuration_home.js
        …
    it_wizard_*_page.js    # Thin registrars only
  it_tender_wizard_impl/   # Design-reference HTML (no runtime mount for native screens)
```

## Per-screen workflow

1. **Stitch design** — visual source in `ui-designs/` and `it_tender_wizard_impl/`
2. **UX refactor markdown** — ownership / field rules per Matrix 99
3. **Native component mapping** — map blocks to shared `it_wizard_components`
4. **Frappe page implementation** — `screens/<name>.js` + thin `*_page.js`
5. **API hydration** — `it_wizard_api.js` wrappers only
6. **Playwright smoke test** — plain DOM assertions (no iframe wait)

**Do not** mount Stitch HTML in an iframe for new or migrated production screens.

## Shared components (Phase 2 library)

- IT Wizard page shell (app bar, canvas, footer offset for sidebar)
- Context strip
- Step card + step grid
- Status chip
- Table / pager patterns
- Drawer + modal
- Footer action bar
- Validation summary (as screens require)

## Migration phases

### Phase 1 — Freeze (this document + Cursor rule)

Declare native-only for new work; iframe path deprecated.

### Phase 2 — Shared native shell

Extract library from Screen 01; refactor dashboard to consume it.

### Phase 3 — Migrate screens

| Order | Screen | Route |
|---|---|---|
| 1 | Dashboard | `it-tender-configuration-dashboard` — componentize |
| 2 | Configuration Home | `it-tender-configuration-overview` |
| 3 | IT Requirements | `it-tender-configuration-it-requirements` |
| 4+ | Remaining steps | Sequential |

### Phase 4 — Remove iframe engine (after S02–S05 stable)

- Remove iframe hydration path from `it_wizard_engine.js`
- Remove static HTML runtime dependency for migrated screens
- Remove Tailwind CDN from design-reference HTML (or archive to docs only)

## Disallowed patterns

- `mount_page()` for new or re-migrated production screens
- Tailwind CDN in any shipped production asset
- Runtime Stitch HTML mount for native screens
- Per-screen duplicated shell / app-bar markup (use shared components)
- Copy-paste of Screen 01 monolith into each screen

## Static HTML layout guards

Byte-guards on `it_tender_wizard_impl/*.html` remain as **design-reference drift detection** only. A green layout guard does **not** imply the HTML is deployed at runtime for native screens.

## Test gates

- Per-screen Makefile gates only (`it-wizard-test-gate.mdc`)
- `make it-wizard-native-architecture-gate` — structural guards for native wiring
- Playwright: plain DOM, `data-itw-*` contract hooks, sidebar visible

## Precedence

Native architecture rule applies alongside Matrix 99 and API contract 05. On conflict with iframe transitional code for a screen marked **native** in the UI tracker, **native wins** — remove iframe wiring for that screen.
