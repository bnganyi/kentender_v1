# Procurement Officer Tender Configuration POC — implementation tracker

**Purpose:** Single place to record officer-workstream status, evidence (Python tests, Playwright), acceptance criteria, and exit-condition fulfilment for the **Procurement Officer Tender Configuration POC** (guided `Procurement Tender` configuration from imported STD template — no package authoring, no publication/bidder/evaluation scope).

**Parent workstreams:** [STD-WORKS-POC tracker](../IMPLEMENTATION_TRACKER.md) (package + engine + DocTypes) · [STD Administration Console POC tracker](../admin%20console/IMPLEMENTATION_TRACKER.md) (internal observability). **Depends on:** STD-WORKS-POC through tender/preview path and Admin Console through smoke **minimum** — officer flow reuses `STD Template`, `Procurement Tender`, `std_template_engine`, child tables, and existing whitelisted patterns.

**Issues (this stream):** [`ISSUES_LOG.md`](ISSUES_LOG.md) — use ids **`STD-OFFICER-NNN`**. Optional cross-links to shared [`../ISSUES_LOG.md`](../ISSUES_LOG.md) for programme-wide decisions.

**Agent rules (existing):** [`.cursor/rules/kentender-std-poc-implementation.mdc`](../../../../../.cursor/rules/kentender-std-poc-implementation.mdc) · [`.cursor/rules/kentender-std-admin-console-implementation.mdc`](../../../../../.cursor/rules/kentender-std-admin-console-implementation.mdc) · workspace TDD/Playwright quality gate. Add a dedicated officer rule file later if prompts outgrow these.

**Specs (this folder):** [`1. procurement_officer_tender_configuration_poc_scope_document.md`](1.%20procurement_officer_tender_configuration_poc_scope_document.md) … [`9. procurement_officer_tender_configuration_poc_smoke_test_specification.md`](9.%20procurement_officer_tender_configuration_poc_smoke_test_specification.md)

---

## Rules of engagement

1. **Scope document is law for boundaries** — Read doc **1** before coding; honour **non-publication**, **no raw JSON editing**, **no bidder/evaluation/award** prompts in every spec.
2. **Server-side validation is authoritative** — Client may drive conditional visibility; engine + `validate_*` paths own truth (doc 3–4).
3. **TDD; Playwright for Desk** — Any new officer-visible Desk behaviour requires automated tests + **Playwright** where doc 9 defines UI smoke; cite commands in **Evidence**. Do not mark **Done** without evidence or a logged environment **blocker** per repo guidance.
4. **Reuse engine and DocTypes** — Prefer `officer_tender_config` helpers calling existing `Procurement Tender` whitelists + `std_template_engine`; avoid duplicating rule evaluation in client scripts (doc 8).
5. **Exit conditions** — Mark **`Done`** only when that row’s acceptance/exit items are met **and** evidenced. Use **`Partial`** / **`Blocked`** when work is incomplete or **`STD-OFFICER-NNN`** applies.

### Per-row completion (before Done)

- Relevant spec sections read (note § refs in **Notes**)  
- Deliverable implemented and bounded (no out-of-scope actions)  
- `OFFICER-*` / `OFF-ST-*` acceptance exercised (reference in **Notes**)  
- TDD + Playwright evidence in **Evidence**  

---

**Status values:** `Not started` | `In progress` | `Partial` | `Blocked` | `Done`

**Evidence column:** `bench run-tests …`, test modules, Playwright spec paths, PR links. **Notes column:** `STD-OFFICER-NNN`, acceptance ids (`OFFICER-IMPL-AC-*`, `OFF-ST-*`, group-level AC from docs 4–7).

---

## Specification and delivery steps (docs 1–9)

| Officer step | Document | Deliverable | Status | Evidence | Notes |
|---:|---|---|:---:|:---:|---|
| 1 | [`1. …scope_document.md`](1.%20procurement_officer_tender_configuration_poc_scope_document.md) | Scope, hypothesis, in/out scope, POC state model | Done | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_officer_poc_step1_scope_baseline` (4/4 OK, 2026-05-01) · [`officer_tender_config.py`](../../../../kentender_procurement/kentender_procurement/tender_management/services/officer_tender_config.py) · [`test_officer_poc_step1_scope_baseline.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_officer_poc_step1_scope_baseline.py) | **§19 / §21 / §22** anchors + boundary phrases. **Planning §1:** `tender_status_to_officer_ux_label` / `officer_ux_label_to_tender_status` (no migrate). **STD-OFFICER-002** path note in issues log. |
| 2 | [`2. …user_journey_information_architecture.md`](2.%20procurement_officer_tender_configuration_poc_user_journey_information_architecture.md) | IA: journey, navigation tree, screen inventory | Done | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_officer_poc_step2_information_architecture_baseline` (2/2 OK, 2026-05-01) · [`test_officer_poc_step2_information_architecture_baseline.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_officer_poc_step2_information_architecture_baseline.py) | **§29 `OFFICER-IA-AC-001`–`015`** anchors; **§7** list+form first (asserted). |
| 3 | [`3. …guided_configuration_field_model.md`](3.%20procurement_officer_tender_configuration_poc_guided_configuration_field_model.md) | Field groups, metadata, inventory vs `fields.json` | Done | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_officer_poc_step3_guided_field_model` (3/3 OK, 2026-05-01) · [`officer_tender_config.py`](../../../../kentender_procurement/kentender_procurement/tender_management/services/officer_tender_config.py) (`get_officer_guided_field_model`) · [`test_officer_poc_step3_guided_field_model.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_officer_poc_step3_guided_field_model.py) | **9 groups / 75 fields** from bundled `fields.json`; **OFFICER-FIELD-AC-001–012** anchors in spec. |
| 4 | [`4. …conditional_field_rule_feedback_ux.md`](4.%20procurement_officer_tender_configuration_poc_conditional_field_rule_feedback_ux.md) | Conditional visibility + validation feedback UX | Done | Officer step **3–4** evidence + step **8** Desk `get_officer_conditional_state_for_tender` + `html_officer_guided_notices` (`procurement_tender.js`). | Server hints: `get_officer_conditional_state` (steps 3–4). |
| 5 | [`5. …required_forms_checklist_ux.md`](5.%20procurement_officer_tender_configuration_poc_required_forms_checklist_ux.md) | Required forms checklist UX | Done | Steps **5** + **8**: `shape_officer_required_forms_checklist`, `generate_officer_required_forms`, `get_officer_required_forms_checklist`; tests `test_officer_poc_step5_*`, `test_officer_poc_step8_*`. | |
| 6 | [`6. …boq_handling_boundary_specification.md`](6.%20procurement_officer_tender_configuration_poc_boq_handling_boundary_specification.md) | POC BoQ panel + readiness vs preview | Done | Steps **6** + **8**: `get_officer_boq_readiness_summary`, `generate_officer_representative_boq`, `get_officer_boq_status`; tests `test_officer_poc_step6_*`, step **8** module. | |
| 7 | [`7. …preview_audit_ux_specification.md`](7.%20procurement_officer_tender_configuration_poc_preview_audit_ux_specification.md) | Preview + audit summary UX | Done | `get_officer_preview_audit_summary_enriched`, `get_officer_preview_audit_summary`, `apply_officer_preview_audit_labels`; tests `test_officer_poc_step7_*`. | |
| 8 | [`8. …minimal_frappe_implementation_pack.md`](8.%20procurement_officer_tender_configuration_poc_minimal_frappe_implementation_pack.md) | Frappe implementation: server module, form sections, whitelisted methods, officer actions | Done | `bench --site kentender.midas.com migrate` · `test_officer_poc_step8_sync_and_whitelists` · [`procurement_tender.py`](../../../../kentender_procurement/kentender_procurement/kentender_procurement/doctype/procurement_tender/procurement_tender.py) officer whitelists · [`procurement_tender.js`](../../../../kentender_procurement/kentender_procurement/kentender_procurement/doctype/procurement_tender/procurement_tender.js) · role + seed: `constants.py`, `ensure_procurement_officer_role` patch · DocType HTML sections + `Procurement Officer` DocPerm. | **`OFFICER-IMPL-AC`**: subset via officer RPCs + STD engine wrappers; admin-only STD POC / STD Demo (doc 8 §10). |
| 9 | [`9. …smoke_test_specification.md`](9.%20procurement_officer_tender_configuration_poc_smoke_test_specification.md) | Smoke path + evidence pack | Partial (extended) | **Desk:** `npm run test:ui:smoke:procurement-officer` · `npm run test:ui:smoke:procurement-officer-doc9` (`officer-tender-poc-off-st-desk.spec.ts` — OFF-ST-001–009,016–018). **API:** `bench … test_officer_poc_step9_doc9_off_st_contracts` (OFF-ST-010–015). | Full OFF-ST-005 branch matrix / OFF-ST-004 save-edit still partial (officer form save vs server actions). **STD-OFFICER-003** `/desk/` routes. |

---

## Implementation sequence (from doc 8 §24)

Use this table for day-to-day sequencing while **Officer step 8** is **In progress**. Update **Status** as substeps complete; roll up summary evidence to the **Officer step 8** row above.

| Impl seq | Task | Status | Evidence | Notes |
|---:|---|:---:|:---:|---|
| 1 | Create officer workflow server module (`tender_management/services/officer_tender_config.py` — **STD-OFFICER-002**) | Done | Same evidence as Officer step **1** row (module stub + state map constants). | Shared module; further methods added Officer steps **3–8**. |
| 2 | Available templates + `initialize_officer_tender_from_template` | Done | `get_available_std_templates_for_officer`, `initialize_officer_tender_from_template`; `test_officer_poc_step8_sync_and_whitelists`. | Doc 8 §9.1. |
| 3 | Guided field groups / `get_officer_guided_field_model` + form fields | Done | Officer step **3** evidence row. | Doc 3; Desk notices + officer HTML sections step **8**. |
| 4 | `sync_officer_configuration` → `configuration_json` | Done | `merge_officer_overlay_into_configuration`, `sync_officer_configuration`; step **8** tests. | Doc 8 §9.2 / §13. |
| 5 | Client conditional visibility + `get_officer_conditional_state` | Done | `get_officer_conditional_state_for_tender` + `procurement_tender.js` notices panel; `mark_officer_configuration_changed`. | Doc 4. |
| 6 | `validate_officer_configuration` + officer-friendly feedback | Done | `validate_officer_configuration`, `get_officer_validation_feedback`, `can_generate_officer_preview`. | Doc 8 §9.3. |
| 7 | Validation panel + **Validate** action | Done | Desk **Validate (officer)** + feedback dialog. | Doc 2. |
| 8 | Required forms checklist UX + RPCs | Done | `generate_officer_required_forms`, `get_officer_required_forms_checklist`. | Doc 8 §9.4. |
| 9 | BoQ status UX + RPCs | Done | `generate_officer_representative_boq`, `get_officer_boq_status`. | Doc 8 §9.5. |
| 10 | Officer preview + audit summary | Done | `generate_officer_preview`, `get_officer_preview_audit_summary`. | Doc 8 §9.6. |
| 11 | POC state indicators / `mark_officer_tender_ready_for_review` | Done | Desk actions **Mark ready for review** / **Reset to configuring**. | Doc 8 §9.7. |
| 12 | Remove or hide out-of-scope Desk actions (publish, PDF, bidders, etc.) | Partial | Admin-only **STD POC** / **STD Demo**; officer POC boundary HTML; raw JSON hidden for Procurement Officer-only session. | Full removal of forbidden buttons not applicable until those controls exist on form. |
| 13 | Run officer smoke (doc 9) and attach evidence | Partial | MVP + extended: `npm run test:ui:smoke:procurement-officer-doc9` · `test_officer_poc_step9_doc9_off_st_contracts`. | **Officer step 9** row; matrix gaps in tracker Notes. |

---

## How to use

1. Read **Officer step 1** (scope) and the spec for the row you are implementing.
2. For coding, follow **doc 8** Cursor Implementation Prompt (§25) and **Implementation sequence** rows in order unless a dependency dictates otherwise.
3. Update **Status** and **Evidence** on this page; log **`STD-OFFICER-NNN`** in [`ISSUES_LOG.md`](ISSUES_LOG.md) for decisions, blockers, path deviations (mirror to [`../ISSUES_LOG.md`](../ISSUES_LOG.md) when programme-visible).
4. Extend this tracker with extra rows if a spec splits deliverables (e.g. separate Playwright spec per major panel) — keep **Officer step** ids stable for audit.
