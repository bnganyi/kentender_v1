# STD Engine Production UI — Implementation Tracker

**Phase:** 1c — Static screens 13–22 (requirement schema through audit log)  
**Module pack:** `apps/kentender_v1/docs/std-prod-impl/ui/`

## Goal

Deploy twenty-two design `code.html` files as verbatim static assets. Screens 13–22 added in this phase (no Desk wiring). Desk wiring remains on screens 01–03 only.

## Tracker

| ID | Screen | Design source | Deployed asset | Layout guard | Playwright | Status | Evidence |
|---|---|---|---|---|---|---|---|
| UI-01 | STD Library | `ui/01. std-lib/code.html` | `std_library.html` | `test_std_prod_ui_std_library_layout_guard` | `static-screens.spec.ts` (library) | Done | Design refresh 2026-07-08; 3/3 unit; Playwright OK |
| UI-02 | STD Family Detail | `ui/02. std-family-detail/code.html` | `std_family_detail.html` | `test_std_prod_ui_std_family_detail_layout_guard` | `static-screens.spec.ts` (family) | Done | Design refresh 2026-07-08; 3/3 unit; Playwright OK |
| UI-03 | STD Version Detail | `ui/03. std-version-detail/code.html` | `std_version_detail.html` | `test_std_prod_ui_std_version_detail_layout_guard` | `static-screens.spec.ts` (version) | Done | Design refresh 2026-07-08; 3/3 unit; Playwright OK |
| UI-07 | Source Document & Traceability | `ui/04. source-doc/code.html` | `std_source_doc.html` | `test_std_prod_ui_std_source_doc_layout_guard` | `static-screens.spec.ts` (source doc) | Done | 3/3 unit; Playwright OK |
| UI-08 | Section and Clause Map | `ui/05. section-clauses/code.html` | `std_section_clauses.html` | `test_std_prod_ui_std_section_clauses_layout_guard` | `static-screens.spec.ts` (section clauses) | Done | 3/3 unit; Playwright OK |
| UI-09 | Clause Detail | `ui/06. clause-detail/code.html` | `std_clause_detail.html` | `test_std_prod_ui_std_clause_detail_layout_guard` | `static-screens.spec.ts` (clause detail) | Done | 3/3 unit; Playwright OK |
| UI-10 | Parameter Dictionary | `ui/07. parameter-dictionary/code.html` | `std_parameter_dictionary.html` | `test_std_prod_ui_std_parameter_dictionary_layout_guard` | `static-screens.spec.ts` (parameter dictionary) | Done | 3/3 unit; Playwright OK |
| UI-11 | Parameter Detail | `ui/08. parameter-detail/code.html` | `std_parameter_detail.html` | `test_std_prod_ui_std_parameter_detail_layout_guard` | `static-screens.spec.ts` (parameter detail) | Done | 3/3 unit; Playwright OK |
| UI-12 | Rule Dictionary | `ui/09. Rule-Dictionary/code.html` | `std_rule_dictionary.html` | `test_std_prod_ui_std_rule_dictionary_layout_guard` | `static-screens.spec.ts` (rule dictionary) | Done | 3/3 unit; Playwright OK |
| UI-13 | Rule Detail | `ui/10. Rule-Detail/code.html` | `std_rule_detail.html` | `test_std_prod_ui_std_rule_detail_layout_guard` | `static-screens.spec.ts` (rule detail) | Done | 3/3 unit; Playwright OK |
| UI-14 | Form Schema Manager | `ui/11. Form Schema Manager/code.html` | `std_form_schema_manager.html` | `test_std_prod_ui_std_form_schema_manager_layout_guard` | `static-screens.spec.ts` (form schema manager) | Done | 3/3 unit; Playwright OK |
| UI-15 | Form Detail & Field Builder | `ui/12. Form Detail & Field Builder/code.html` | `std_form_detail_field_builder.html` | `test_std_prod_ui_std_form_detail_field_builder_layout_guard` | `static-screens.spec.ts` (form detail) | Done | 3/3 unit; Playwright OK |
| UI-16 | Requirement Schema Manager | `ui/13. Requirement Schema Manager/code.html` | `std_requirement_schema_manager.html` | `test_std_prod_ui_std_requirement_schema_manager_layout_guard` | `static-screens.spec.ts` (requirement schema) | Done | 3/3 unit; Playwright OK |
| UI-17 | Price Schedule Schema | `ui/14. Price Schedule Schema/code.html` | `std_price_schedule_schema.html` | `test_std_prod_ui_std_price_schedule_schema_layout_guard` | `static-screens.spec.ts` (price schedule) | Done | 3/3 unit; Playwright OK |
| UI-18 | Evaluation Schema | `ui/15. Evaluation Schema/code.html` | `std_evaluation_schema.html` | `test_std_prod_ui_std_evaluation_schema_layout_guard` | `static-screens.spec.ts` (evaluation schema) | Done | 3/3 unit; Playwright OK |
| UI-19 | Render Blocks | `ui/16. Render Blocks/code.html` | `std_render_blocks.html` | `test_std_prod_ui_std_render_blocks_layout_guard` | `static-screens.spec.ts` (render blocks) | Done | 3/3 unit; Playwright OK |
| UI-20 | Validation Report | `ui/17. Validation Report/code.html` | `std_validation_report.html` | `test_std_prod_ui_std_validation_report_layout_guard` | `static-screens.spec.ts` (validation report) | Done | 3/3 unit; Playwright OK |
| UI-21 | Review and Approval | `ui/18. Review and Approval/code.html` | `std_review_and_approval.html` | `test_std_prod_ui_std_review_and_approval_layout_guard` | `static-screens.spec.ts` (review and approval) | Done | 3/3 unit; Playwright OK |
| UI-22 | Usage and Tender Bindings | `ui/19. Usage and Tender Bindings/code.html` | `std_usage_and_tender_bindings.html` | `test_std_prod_ui_std_usage_and_tender_bindings_layout_guard` | `static-screens.spec.ts` (usage bindings) | Done | 3/3 unit; Playwright OK |
| UI-23 | Import Package Review | `ui/20. Import Package Review/code.html` | `std_import_package_review.html` | `test_std_prod_ui_std_import_package_review_layout_guard` | `static-screens.spec.ts` (import package) | Done | 3/3 unit; Playwright OK |
| UI-24 | Version Diff and Supersession | `ui/21. Version Diff and Supersession/code.html` | `std_version_diff_and_supersession.html` | `test_std_prod_ui_std_version_diff_and_supersession_layout_guard` | `static-screens.spec.ts` (version diff) | Done | 3/3 unit; Playwright OK |
| UI-25 | Audit Log | `ui/22. Audit Log/code.html` | `std_audit_log.html` | `test_std_prod_ui_std_audit_log_layout_guard` | `static-screens.spec.ts` (audit log) | Done | 3/3 unit; Playwright OK |
| UI-00 | Preview index | — | `index.html` | — | `static-screens.spec.ts` (index) | Done | Playwright index smoke OK |
| UI-04 | STD Library Desk wiring | — | Frappe Page `std-library` + iframe shell | `test_std_prod_std_library_desk_wiring` | `std-library-desk-wiring.spec.ts` | Done | 6/6 unit+integration; Playwright 4/4 OK |
| UI-05 | Library Open → Family Detail | — | Frappe Page `std-family-detail` + iframe wiring | `test_std_prod_std_family_detail_desk_wiring` | `std-library-open-family-detail.spec.ts` | Done | 5/5 unit+integration; Playwright 1/1 OK |
| UI-06 | Family version actions → Version Detail | — | Frappe Page `std-version-detail` + iframe wiring | `test_std_prod_std_version_detail_desk_wiring` | `std-family-open-version-detail.spec.ts` | Done | 5/5 unit+integration; Playwright 2/2 OK |

## Exit criteria (Phase 1)

1. Deployed HTML byte-identical to design `code.html` (EOF newline normalization only)
2. All three layout guard modules pass on `kentender.midas.com`
3. Playwright `static-screens.spec.ts` passes (index + 22 screens via asset URLs)
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
- Source document: `.../std_source_doc.html`
- Section and clause map: `.../std_section_clauses.html`
- Clause detail: `.../std_clause_detail.html`
- Parameter dictionary: `.../std_parameter_dictionary.html`
- Parameter detail: `.../std_parameter_detail.html`
- Rule dictionary: `.../std_rule_dictionary.html`
- Rule detail: `.../std_rule_detail.html`
- Form schema manager: `.../std_form_schema_manager.html`
- Form detail & field builder: `.../std_form_detail_field_builder.html`
- Requirement schema manager: `.../std_requirement_schema_manager.html`
- Price schedule schema: `.../std_price_schedule_schema.html`
- Evaluation schema: `.../std_evaluation_schema.html`
- Render blocks: `.../std_render_blocks.html`
- Validation report: `.../std_validation_report.html`
- Review and approval: `.../std_review_and_approval.html`
- Usage and tender bindings: `.../std_usage_and_tender_bindings.html`
- Import package review: `.../std_import_package_review.html`
- Version diff and supersession: `.../std_version_diff_and_supersession.html`
- Audit log: `.../std_audit_log.html`
