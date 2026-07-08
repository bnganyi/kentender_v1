# STD Config UI — Implementation Tracker

> **Programme status (2026-07-08): RETIRED** — entire POC STD stack archived under `apps/kentender_v1/archive/std-module-poc-retired-2026-07/`. Active Desk route: `/desk/std-module-retired`. Pre-archive tag: `archive/std-module-poc-2026-07`. See `docs/STD_MODULE_POC_RETIRED.md`.

**Purpose:** Track the phased replacement of the STD-LIB master-detail shell with the std config pack (Layers 1–2).

**Programme scope:** STD Library catalogue + STD Version Configurator. **Layer 3 (Tender Document Readiness) deferred.**

**Feature flag:** `std_config_ui_v2_enabled` in site config — **enabled** on `kentender.midas.com`.

**Status values:** `Not started` | `In progress` | `Partial` | `Done`

---

## Phase completion (full-fidelity programme — 2026-07-06)

| Phase | Status | Evidence |
|---|---|---|
| 0 Schema + seed | **Done** | `std_config_section_schema.py`, `seed_std_config_ui_fixture.py`, `test_std_configurator_section_contract` (7 tests), `test_std_config_ui_fixture_seed` |
| 1 STD Library (1.lib) | **Partial** | Filter panel + pagination + row icons + status dots; `test_std_config_library_layout_guard` (3 tests); Playwright `std-library-catalogue.spec.ts`, `std-config-data-binding.spec.ts` (library row) |
| 2 Configurator shell | **Partial** | `configurator/tab_registry.js`, `std_config/tokens.css`, shell registry dispatch; `test_std_configurator_layout_guard`; Playwright `std-configurator-tabs.spec.ts` |
| 3 Overview | **Partial** | Description + funding save wiring; identity/progress/applies-to markers; Playwright fixture title assertion |
| 4 Applicability | **Partial** | 2-col scope/financial limits, entity pills, `run_applicability_test` API + UI; section round-trip tests |
| 5 Tender Fields | **Partial** | 7-column grouped matrix (mockup headers), field drawer save; section round-trip |
| 6 Forms | **Partial** | 9-column table, 5 preview pills, supplier forms from data, document drawer save; section round-trip |
| 7 Evaluation | **Partial** | Governing basis + stages save, stage drawer; section round-trip |
| 8 Contract Terms | **Partial** | 10-column matrix, dynamic readiness, term drawer save; section round-trip |
| 9 Unmocked tabs | **Partial** | Rules save, supplier `used_in_evaluation`, preview modes, approval/evidence/technical JSON wired |
| 10 Regression gate | **Partial** | `npm run test:ui:smoke:std-config-gate` **7/7 pass** (2026-07-06); remaining: side-by-side mockup sign-off per screen |

**Remaining for full Done:** literal region-by-region mockup checklist sign-off (Hard Rule) for Phases 1–8; split `tab_renderers.js` into per-tab modules under `configurator/tabs/`; MCP visual pass.

---

## Primary routes

| Route | Page |
|---|---|
| `/app/std-library` | STD Library catalogue |
| `/app/std-library/import` | Import wizard (re-skinned) |
| `/app/std-configurator/{code}/{tab}` | STD Version Configurator |
| `/app/std-engine` | Redirect shim → std-library |

**UI fixture template (Playwright):** `STD-CFG-UI-FIXTURE` — seed via `bench --site kentender.midas.com execute kentender_procurement.tender_management.seeds.seed_std_config_ui_fixture.ensure_std_config_ui_fixture_template`

---

## STD-LIB retirement

Old `std_library_shell.js` master-detail UI removed from `page_js["std-engine"]`. Legacy modules remain on disk for reference; import adapters reused on `std-library` page.
