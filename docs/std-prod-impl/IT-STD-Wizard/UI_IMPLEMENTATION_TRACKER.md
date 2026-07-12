# IT Tender Configuration Wizard — UI Implementation Tracker

**Phase:** 1 — Static screen port (verbatim `code.html` assets; no Desk wiring)  
**Module pack:** `apps/kentender_v1/docs/std-prod-impl/IT-STD-Wizard/ui-designs/`  
**Precedent:** [`UI_IMPLEMENTATION_TRACKER.md`](../UI_IMPLEMENTATION_TRACKER.md) (STD prod Phase 1c)

## Goal

Deploy fifteen IT Tender Configuration Wizard design `code.html` files as verbatim static assets under `public/it_tender_wizard_impl/`. Engineers preview every wizard step via asset URLs and a catalog index—without backend services, DocTypes, or Desk API hydration.

Done looks like: 15 HTML files + `index.html`, 45/45 layout-guard unit tests green, Playwright `static-screens.spec.ts` green, every tracker row marked Done with test evidence.

## Tracker

| ID | Screen | Design source | Deployed asset | Layout guard | Playwright | Status | Evidence |
|---|---|---|---|---|---|---|---|
| ITW-01 | Tender Configuration Dashboard | `01 dashboard/code.html` | `it_wizard_dashboard.html` | `test_it_wizard_ui_dashboard_layout_guard` | `static-screens.spec.ts` (dashboard) | Done | ITW-LG-01 (3/3); PW-ITW-01 |
| ITW-02 | Tender STD Configuration Overview | `02 std-config-overview/code.html` | `it_wizard_std_config_overview.html` | `test_it_wizard_ui_std_config_overview_layout_guard` | `static-screens.spec.ts` (overview) | Done | ITW-LG-02 (3/3); PW-ITW-02 |
| ITW-03 | Tender Profile | `03 tender-profile/code.html` | `it_wizard_tender_profile.html` | `test_it_wizard_ui_tender_profile_layout_guard` | `static-screens.spec.ts` (profile) | Done | ITW-LG-03 (3/3); PW-ITW-03 |
| ITW-04 | Tender Data Sheet (TDS) | `04 tds/code.html` | `it_wizard_tds.html` | `test_it_wizard_ui_tds_layout_guard` | `static-screens.spec.ts` (tds) | Done | ITW-LG-04 (3/3); PW-ITW-04 |
| ITW-05 | IT Requirements | `05 it-requirements/code.html` | `it_wizard_it_requirements.html` | `test_it_wizard_ui_it_requirements_layout_guard` | `static-screens.spec.ts` (requirements) | Done | ITW-LG-05 (3/3); PW-ITW-05 |
| ITW-06 | Implementation Schedule | `06 implementation-schedule/code.html` | `it_wizard_implementation_schedule.html` | `test_it_wizard_ui_implementation_schedule_layout_guard` | `static-screens.spec.ts` (schedule) | Done | ITW-LG-06 (3/3); PW-ITW-06 |
| ITW-07 | System Inventory | `07 system-inventory/code.html` | `it_wizard_system_inventory.html` | `test_it_wizard_ui_system_inventory_layout_guard` | `static-screens.spec.ts` (inventory) | Done | ITW-LG-07 (3/3); PW-ITW-07 |
| ITW-08 | Price Schedule | `08 price-schedule/code.html` | `it_wizard_price_schedule.html` | `test_it_wizard_ui_price_schedule_layout_guard` | `static-screens.spec.ts` (price) | Done | ITW-LG-08 (3/3); PW-ITW-08 |
| ITW-09 | Evaluation Setup | `09 evaluation-setup/code.html` | `it_wizard_evaluation_setup.html` | `test_it_wizard_ui_evaluation_setup_layout_guard` | `static-screens.spec.ts` (evaluation) | Done | ITW-LG-09 (3/3); PW-ITW-09 |
| ITW-10 | Forms & Evidence | `10 forms-and-evidence/code.html` | `it_wizard_forms_and_evidence.html` | `test_it_wizard_ui_forms_and_evidence_layout_guard` | `static-screens.spec.ts` (forms) | Done | ITW-LG-10 (3/3); PW-ITW-10 |
| ITW-11 | SCC / Contract Carry-Forward | `11 scc/code.html` | `it_wizard_scc.html` | `test_it_wizard_ui_scc_layout_guard` | `static-screens.spec.ts` (scc) | Done | ITW-LG-11 (3/3); PW-ITW-11 |
| ITW-12 | Validation Report | `12 validation-report/code.html` | `it_wizard_validation_report.html` | `test_it_wizard_ui_validation_report_layout_guard` | `static-screens.spec.ts` (validation) | Done | ITW-LG-12 (3/3); PW-ITW-12 |
| ITW-13 | Review & Approval | `13 review-and-approval/code.html` | `it_wizard_review_and_approval.html` | `test_it_wizard_ui_review_and_approval_layout_guard` | `static-screens.spec.ts` (review) | Done | ITW-LG-13 (3/3); PW-ITW-13 |
| ITW-14 | Final Tender Preview | `14 render-preview/code.html` | `it_wizard_render_preview.html` | `test_it_wizard_ui_render_preview_layout_guard` | `static-screens.spec.ts` (preview) | Done | ITW-LG-14 (3/3); PW-ITW-14 |
| ITW-15 | Publication Readiness | `15 publication-readiness/code.html` | `it_wizard_publication_readiness.html` | `test_it_wizard_ui_publication_readiness_layout_guard` | `static-screens.spec.ts` (publication) | Done | ITW-LG-15 (3/3); PW-ITW-15 |
| ITW-00 | Preview index | — | `index.html` | — | `static-screens.spec.ts` (index) | Done | PW-ITW-00 |

## Deferred (no mockup)

| ID | Screen | Notes |
|---|---|---|
| ITW-16 | Addendum Impact | Implementation Pack §14.2 #19 — design TBD |
| ITW-17 | Audit & Hash Evidence | Implementation Pack §14.2 #20 — design TBD |

## Exit criteria (Phase 1)

1. All 15 `code.html` files deployed verbatim under `public/it_tender_wizard_impl/` — **Done**
2. `make it-wizard-static-gate SITE=kentender.midas.com` passes (45 unit tests) — **Done** (45/45, 2026-07-12)
3. Playwright `tests/ui/smoke/it-std-wizard/static-screens.spec.ts` passes (index + 15 screens) — **Done** (16/16, 2026-07-12)
4. Preview: `http://127.0.0.1:8000/assets/kentender_procurement/it_tender_wizard_impl/index.html`

## Explicitly out of scope (Phase 1)

- Frappe Page fixtures, `hooks.py` `page_js`, Desk iframe hydration
- `it_tender_wizard` DocTypes, services, APIs
- Tailwind CDN → hand-ported CSS refactor
