# STD Engine Production UI — Implementation Tracker

**Phase:** 2 — Minimal Desk wiring (STD Library)  
**Module pack:** `apps/kentender_v1/docs/std-prod-impl/ui/`

## Goal

Phase 1: deploy three design `code.html` files as verbatim static assets. Phase 2: Desk iframe pages and minimal navigation between library and family detail — no backend APIs yet.

## Tracker

| ID | Screen | Design source | Deployed asset | Layout guard | Playwright | Status | Evidence |
|---|---|---|---|---|---|---|---|
| UI-01 | STD Library | `ui/1. std-lib/code.html` | `std_library.html` | `test_std_prod_ui_std_library_layout_guard` | `static-screens.spec.ts` (library) | Done | Design refresh 2026-07-08; 3/3 unit; Playwright OK |
| UI-02 | STD Family Detail | `ui/2. std-family-detail/code.html` | `std_family_detail.html` | `test_std_prod_ui_std_family_detail_layout_guard` | `static-screens.spec.ts` (family) | Done | Design refresh 2026-07-08; 3/3 unit; Playwright OK |
| UI-03 | STD Version Detail | `ui/3. std-version-detail/code.html` | `std_version_detail.html` | `test_std_prod_ui_std_version_detail_layout_guard` | `static-screens.spec.ts` (version) | Done | Design refresh 2026-07-08; 3/3 unit; Playwright OK |
| UI-00 | Preview index | — | `index.html` | — | `static-screens.spec.ts` (index) | Done | Playwright index smoke OK |
| UI-04 | STD Library Desk wiring | — | Frappe Page `std-library` + iframe shell | `test_std_prod_std_library_desk_wiring` | `std-library-desk-wiring.spec.ts` | Done | 6/6 unit+integration; Playwright 4/4 OK |
| UI-05 | Library Open → Family Detail | — | Frappe Page `std-family-detail` + iframe wiring | `test_std_prod_std_family_detail_desk_wiring` | `std-library-open-family-detail.spec.ts` | Done | 5/5 unit+integration; Playwright 1/1 OK |
| UI-06 | Family version actions → Version Detail | — | Frappe Page `std-version-detail` + iframe wiring | `test_std_prod_std_version_detail_desk_wiring` | `std-family-open-version-detail.spec.ts` | Done | 5/5 unit+integration; Playwright 2/2 OK |

## Exit criteria (Phase 1)

1. Deployed HTML byte-identical to design `code.html` (EOF newline normalization only)
2. All three layout guard modules pass on `kentender.midas.com`
3. Playwright `static-screens.spec.ts` passes (index + 3 screens via asset URLs)
4. No `hooks.py`, Frappe Pages, APIs, or breadcrumb routing added

## Exit criteria (Phase 2 — minimal wiring)

1. Frappe Page `std-library` exists; Procurement sidebar **Official STD Library** links to it
2. Page loads static `std_library.html` in iframe (no backend calls)
3. `test_std_prod_std_library_desk_wiring` passes; Playwright `std-library-desk-wiring.spec.ts` passes
4. `std-module-retired` placeholder route remains for governance shortcuts
5. Library table **Open** navigates to `std-family-detail` (static family design; no per-row family code yet)
6. Family versions table **open_in_new**, **edit**, and **visibility** actions navigate to `std-version-detail`

## Desk routes

- **Official STD Library:** `http://127.0.0.1:8000/app/std-library`
- **STD Family Detail:** `http://127.0.0.1:8000/app/std-family-detail`
- **STD Version Detail:** `http://127.0.0.1:8000/app/std-version-detail`

## Preview URLs

- Index: `http://127.0.0.1:8000/assets/kentender_procurement/std_prod_impl/index.html`
- Library: `.../std_library.html`
- Family detail: `.../std_family_detail.html`
- Version detail: `.../std_version_detail.html`
