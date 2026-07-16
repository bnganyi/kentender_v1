# IT Tender Configuration Wizard — UI Implementation Tracker

**Phase:** 1 — Static screen port (verbatim `code.html` assets; no Desk wiring)  
**Module pack:** `apps/kentender_v1/docs/std-prod-impl/IT-STD-Wizard/ui-designs/`  
**Precedent:** [`UI_IMPLEMENTATION_TRACKER.md`](../UI_IMPLEMENTATION_TRACKER.md) (STD prod Phase 1c)

## Ownership correction (binding)

Field ownership, editability, and source presentation are governed by:

- [`99 IT_Tender_Wizard_Screen_Ownership_Matrix.md`](99%20IT_Tender_Wizard_Screen_Ownership_Matrix.md)
- [`98 IT_Tender_Wizard_Screen_Ownership_Correction_Plan.md`](98%20IT_Tender_Wizard_Screen_Ownership_Correction_Plan.md)
- [`Screen_Ownership_Implementation_Tracker.md`](Screen_Ownership_Implementation_Tracker.md)

**Hard rule:** Keep `make it-wizard-ownership-gate` green. ITW-08–15 Desk wiring also requires `make it-wizard-downstream-gate` green.

## Goal

Deploy fifteen IT Tender Configuration Wizard design `code.html` files as verbatim static assets under `public/it_tender_wizard_impl/`. Engineers preview every wizard step via asset URLs and a catalog index—without backend services, DocTypes, or Desk API hydration.

Done looks like: 15 HTML files + `index.html`, 45/45 layout-guard unit tests green, Playwright `static-screens.spec.ts` green, every tracker row marked Done with test evidence.

## Tracker

| ID | Screen | Design source | Deployed asset | Layout guard | Playwright | Status | Evidence |
|---|---|---|---|---|---|---|---|
| ITW-01 | Tender Configuration Dashboard | `01 dashboard/code.html` | `it_wizard_dashboard.html` | `test_it_wizard_ui_dashboard_layout_guard` | `dashboard-desk-wiring.spec.ts` | Done | ITW-LG-01 (3/3); ITW-BE-DASH-001..004; ITW-DESK-DASH-001/002; ITW-NAV-001/002; PW-ITW-DASH-01 |
| ITW-02 | Tender STD Configuration Overview | `02 std-config-overview/code.html` | `it_wizard_std_config_overview.html` | `test_it_wizard_ui_std_config_overview_layout_guard` | `overview-desk-wiring.spec.ts` | Done | ITW-LG-02 (3/3); ITW-BE-OVERVIEW-001; ITW-DESK-OVERVIEW-001/002; PW-ITW-OVERVIEW-01 |
| ITW-03 | Tender Profile | `03 tender-profile/code.html` | `it_wizard_tender_profile.html` | `test_it_wizard_ui_tender_profile_layout_guard` | `tender-profile-desk-wiring.spec.ts` | Done | ITW-LG-03 (3/3); ITW-BE-PROFILE-001; ITW-DESK-PROFILE-001/002; PW-ITW-PROFILE-01 |
| ITW-04 | Tender Data Sheet (TDS) | `04 tds/code.html` | `it_wizard_tds.html` | `test_it_wizard_ui_tds_layout_guard` | `tds-desk-wiring.spec.ts` | Done | ITW-LG-04 (3/3); ITW-BE-TDS-001; ITW-DESK-TDS-001/002; PW-ITW-TDS-01 |
| ITW-05 | IT Requirements | `05 it-requirements/code.html` | `it_wizard_it_requirements.html` | `test_it_wizard_ui_it_requirements_layout_guard` | `it-requirements-desk-wiring.spec.ts` | Done | ITW-LG-05 (4/4); ITW-BE-REQ-001; ITW-DESK-REQ-001/002; PW-ITW-REQ-01; **ITW-05-R1** composer UX (2026-07-14) |
| ITW-06 | Implementation Schedule | `06 implementation-schedule/code.html` | `it_wizard_implementation_schedule.html` | `test_it_wizard_ui_implementation_schedule_layout_guard` | `implementation-schedule-desk-wiring.spec.ts` | Done | ITW-LG-06 (3/3); ITW-BE-SCHED-001; ITW-DESK-SCHED-001/002; PW-ITW-SCHED-01; desk wiring (2026-07-15) |
| ITW-07 | System Inventory | `07 system-inventory/code.html` | `it_wizard_system_inventory.html` | `test_it_wizard_ui_system_inventory_layout_guard` | `system-inventory-desk-wiring.spec.ts` | Done | ITW-LG-07 (3/3); ITW-BE-INV-001 (12/12); ITW-DESK-INV-001/002 (5/5); PW-ITW-INV-01 (5/5); live MCP validation (2026-07-15) |
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

## Backend wiring (ITW-01 dashboard slice)

- DocTypes, services, whitelisted APIs, Desk iframe hydration, Procurement sidebar link (Tender Management cluster)
- Gate: `make it-wizard-dashboard-gate SITE=kentender.midas.com`

## Backend wiring (ITW-02 overview slice)

- Enriched `get_configuration_summary_api` with `wizard_steps`, validation, governance, and reference triplets via `wizard_overview_service`
- Desk route `/desk/it-tender-configuration-overview`; dashboard **Continue** navigates with `configuration_id`
- Overview iframe hydrator rebuilds header, 13-step grid, and governance panel from API (no mock enum residue)
- Gate evidence: `test_wizard_overview_service`, `test_it_wizard_overview_desk_wiring`, `overview-desk-wiring.spec.ts` (3/3) — 2026-07-13

## Backend wiring (ITW-03 tender profile slice)

- Consolidated `Tender STD Profile` DocType (1:1 with instance; interim until S3-001 model split)
- `get_tender_profile_api` / `save_tender_profile_api` via `wizard_tender_profile_service`
- Desk route `/desk/it-tender-configuration-tender-profile`; overview **Tender Profile** step navigates with `configuration_id`
- Profile iframe hydrator: context header, form fields, sidebar completion, STD binding panel; **Save Profile** persists
- Gate evidence: `test_wizard_tender_profile_service` (5/5), `test_it_wizard_tender_profile_desk_wiring`, `tender-profile-desk-wiring.spec.ts` (3/3) — 2026-07-13

## Backend wiring (ITW-04 TDS slice)

- Consolidated `Tender STD TDS` DocType (1:1 with instance; interim until S3-006 STD Core dynamic schema adapter)
- `get_tds_api` / `save_tds_api` via `wizard_tds_service`; 15-field completion, date-order validation (`SMOKE-WIZ-004`)
- Desk route `/desk/it-tender-configuration-tds`; overview **TDS** step + profile **Continue to Tender Data Sheet** navigate with `configuration_id`
- TDS iframe hydrator: context header, 5 form sections, sidebar completion, footer actions; **Save TDS** persists; fixture scripts stripped at runtime
- Gate evidence: `test_wizard_tds_service` (8/8), `test_it_wizard_tds_desk_wiring`, `tds-desk-wiring.spec.ts` (10/10) — 2026-07-14

## Backend wiring (ITW-05 IT Requirements slice)

- Consolidated `Tender STD IT Requirements` + `Tender STD Requirement Item` child table (1:1 with instance; interim until S4-001 domain model split)
- `get_it_requirements_api` / `save_it_requirements_api` via `wizard_it_requirements_service`; completion stats, mandatory validation (`IT_WIZ_SMOKE_005`)
- Desk route `/desk/it-tender-configuration-it-requirements`; overview **IT Requirements** step + TDS **Continue to IT Requirements** navigate with `configuration_id`
- Requirements iframe hydrator: context strip, section tables, **Requirements Guidance** panel, hidden-by-default edit drawer; **Save Requirements** / **Update Requirement** persist; fixture scripts stripped at runtime
- Stub actions remain disabled until ITW-09/11: Import Template, Add Requirement, Run Validation, Edit in Evaluation Setup, Edit in SCC; **Continue to Implementation Schedule** enabled when `validation.blockers === 0`
- Gate evidence: `test_wizard_it_requirements_service` (11/11), `test_it_wizard_it_requirements_desk_wiring`, `it-requirements-desk-wiring.spec.ts` (11/11) — 2026-07-14

## UX refinement (ITW-05-R1 — requirements composer)

- Replaced evaluation-like mock with structured **requirements composer** layout (`05 it-requirements/code.html` → deployed verbatim; ITW-LG-05 forbidden-string negatives)
- Child table fields: `category`, `bidder_instruction`, `evidence_instruction`, `evidence_level`, `acceptance_criteria`, `template_locked`, `field_sources_json`
- Display DTO: plain labels (`Mandatory`, `Evaluation-linked`, `Evidence Required`, `Criteria Defined`, etc.); gaps: missing mandatory, evidence instructions, acceptance criteria, vendor-neutrality warnings
- Engine: 9-column table, guidance hydrator, drawer open/close on Edit/View/Review, source labels on read-only fields, pinned footer; desk harmonizer forces guidance panel visible in iframe
- Evidence: `test_wizard_it_requirements_service` (11/11), `test_it_wizard_ui_it_requirements_layout_guard` (4/4), `test_it_wizard_it_requirements_desk_wiring` (5/5), `it-requirements-desk-wiring.spec.ts` (11/11) — 2026-07-14

## Backend wiring (ITW-06 Implementation Schedule slice)

- Interim DocTypes: `Tender STD Implementation Schedule`, `Tender STD Schedule Phase Item`, `Tender STD Schedule Milestone Item` (1:1 with instance; phase + milestone child tables)
- `get_implementation_schedule_api` / `save_implementation_schedule_api` via `wizard_implementation_schedule_service`; smoke `IT_WIZ_SMOKE_006` (go-live after testing, acceptance criteria required)
- Desk route `/desk/it-tender-configuration-implementation-schedule`; overview **Implementation Schedule** step + IT Requirements **Continue to Implementation Schedule** navigate with `configuration_id`
- Schedule iframe hydrator: context strip, phase table, **Schedule Guidance** panel, hidden-by-default phase drawer, body-level footer; **Save Schedule** / **Save Changes** persist selected phase
- Stub actions remain disabled until their owning steps: Add Phase, Use Standard IT Schedule Template, and Run Validation. Continue to System Inventory is enabled by ITW-07.
- Gate evidence: `test_wizard_implementation_schedule_service` (18/18), `test_it_wizard_implementation_schedule_desk_wiring` (5/5), `implementation-schedule-desk-wiring.spec.ts` (12/12) — 2026-07-15
- **ITW-06-R1** drawer source UX (2026-07-15): template/derived fields prefill but stay editable; source labels + Edit/Override/Reset actions; only phase id/sequence locked
- **ITW-06-R2** Single Turnkey Delivery (2026-07-15): selecting turnkey confirms the mode change, replaces the phase table with one unified delivery form, applies model-specific validation, persists dedicated turnkey fields, and preserves phased rows for restoration when switching back

### ITW-07 System Inventory Desk wiring (2026-07-15)

- Normalized one-to-one `Tender STD System Inventory` aggregate with eight technical-disclosure categories and stable, system-generated item codes
- Grouped API DTO exposes business `id`/`code`/`name` reference options and excludes internal child-row IDs
- System Inventory stores no quantity, unit, rate, pricing-class, evaluated-price, tax, recurrence, or commercial price-structure fields
- Price Schedule Link is a read-only technical policy (`Required`, `Optional`, `Not Priced`); commercial bindings remain owned by ITW-08
- Stable iframe hydration, category filtering, reusable add/edit drawer, requirement/schedule business references, save flow, and ITW-06 continuation are wired; **Continue to Price Schedule** enabled (ITW-08)
- Gate evidence: backend service 12/12; instance API 27/27; Desk wiring 5/5; layout guard 3/3; navigation contract 6/6; Playwright 5/5; live API and drawer MCP validation passed

### ITW-08–15 Downstream Desk wiring (2026-07-16)

- DocTypes + services + whitelisted get/save APIs for Price Schedule, Evaluation Setup, Forms & Evidence, SCC, Validation Report, Review & Approval, Render Preview, Publication Readiness
- Approach C: Price Schedule owns quantity / unit / evaluated-price inclusion; inventory remains technical-disclosure only
- Shared Desk hydration in `public/js/it_wizard_downstream.js` registered via `kentender.it_wizard.register_downstream`
- Overview `STEP_ROUTE_MAP` covers all 13 configuration steps; inventory continues to Price Schedule; Publication Ready does **not** Publish Tender
- Gate: `make it-wizard-downstream-gate SITE=kentender.midas.com` — price schedule service 3/3; desk wiring 4/4; Playwright `downstream-desk-wiring.spec.ts` 9/9

## Exit criteria (Phase 1)

1. All 15 `code.html` files deployed verbatim under `public/it_tender_wizard_impl/` — **Done**
2. `make it-wizard-static-gate SITE=kentender.midas.com` passes (45 unit tests) — **Done** (45/45, 2026-07-12)
3. Playwright `tests/ui/smoke/it-std-wizard/static-screens.spec.ts` passes (index + 15 screens) — **Done** (16/16, 2026-07-12)
4. Preview: `http://127.0.0.1:8000/assets/kentender_procurement/it_tender_wizard_impl/index.html`

## Explicitly out of scope (Phase 1)

- Frappe Page fixtures, `hooks.py` `page_js`, Desk iframe hydration
- `it_tender_wizard` DocTypes, services, APIs
- Tailwind CDN → hand-ported CSS refactor
