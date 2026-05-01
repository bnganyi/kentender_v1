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
| 2 | [`2. …user_journey_information_architecture.md`](2.%20procurement_officer_tender_configuration_poc_user_journey_information_architecture.md) | IA: journey, navigation tree, screen inventory | Not started | | Desk shape: `Procurement Tender` list + form first; §7 recommended implementation shape. |
| 3 | [`3. …guided_configuration_field_model.md`](3.%20procurement_officer_tender_configuration_poc_guided_configuration_field_model.md) | Field groups, metadata, inventory vs `fields.json` | Not started | | Canonical keys = package `field_code`; `configuration_json` store; §10 inventory. |
| 4 | [`4. …conditional_field_rule_feedback_ux.md`](4.%20procurement_officer_tender_configuration_poc_conditional_field_rule_feedback_ux.md) | Conditional visibility + validation feedback UX | Not started | | §7–11 visibility rules; §10 validation model; preview blocked until safe (§13). |
| 5 | [`5. …required_forms_checklist_ux.md`](5.%20procurement_officer_tender_configuration_poc_required_forms_checklist_ux.md) | Required forms checklist UX | Not started | | Timing §8; stale/blocked checklist §17–19; conditional forms §15. |
| 6 | [`6. …boq_handling_boundary_specification.md`](6.%20procurement_officer_tender_configuration_poc_boq_handling_boundary_specification.md) | POC BoQ panel + readiness vs preview | Not started | | Representative rows only; dayworks/provisional categories; lot linkage §17. |
| 7 | [`7. …preview_audit_ux_specification.md`](7.%20procurement_officer_tender_configuration_poc_preview_audit_ux_specification.md) | Preview + audit summary UX | Not started | | Status model §8; blocked/stale §13–16; hash display rules §20.1. |
| 8 | [`8. …minimal_frappe_implementation_pack.md`](8.%20procurement_officer_tender_configuration_poc_minimal_frappe_implementation_pack.md) | Frappe implementation: server module, form sections, whitelisted methods, officer actions | Not started | | **`OFFICER-IMPL-AC-001`–`015`** (doc 8 §27). Implementation order: follow **Implementation sequence (doc 8 §24)** table below. |
| 9 | [`9. …smoke_test_specification.md`](9.%20procurement_officer_tender_configuration_poc_smoke_test_specification.md) | Smoke path + evidence pack | Not started | | **`OFF-ST-001`–`018`** (doc 9); §28–31 pass/fail + evidence pack §29. Prefer dedicated Playwright spec(s) under `apps/kentender_v1/tests/ui/smoke/procurement/` + API tests under `tender_management/tests/`. |

---

## Implementation sequence (from doc 8 §24)

Use this table for day-to-day sequencing while **Officer step 8** is **In progress**. Update **Status** as substeps complete; roll up summary evidence to the **Officer step 8** row above.

| Impl seq | Task | Status | Evidence | Notes |
|---:|---|:---:|:---:|---|
| 1 | Create officer workflow server module (`tender_management/services/officer_tender_config.py` — **STD-OFFICER-002**) | Done | Same evidence as Officer step **1** row (module stub + state map constants). | Shared module; further methods added Officer steps **3–8**. |
| 2 | Available templates + `initialize_officer_tender_from_template` | Not started | | Doc 8 §9.1. |
| 3 | Guided field groups / `get_officer_guided_field_model` + form fields | Not started | | Doc 3 + doc 8 §8–11. |
| 4 | `sync_officer_configuration` → `configuration_json` | Not started | | Doc 8 §9.2 / §13. |
| 5 | Client conditional visibility + `get_officer_conditional_state` | Not started | | Doc 4; `mark_officer_configuration_changed`. |
| 6 | `validate_officer_configuration` + officer-friendly feedback | Not started | | Doc 8 §9.3; doc 4 §10–11. |
| 7 | Validation panel + **Validate** action | Not started | | Doc 2 screen inventory. |
| 8 | Required forms checklist UX + RPCs | Not started | | Doc 8 §9.4; doc 5. |
| 9 | BoQ status UX + RPCs | Not started | | Doc 8 §9.5; doc 6. |
| 10 | Officer preview + audit summary | Not started | | Doc 8 §9.6; doc 7; block on `can_generate_officer_preview`. |
| 11 | POC state indicators / `mark_officer_tender_ready_for_review` | Not started | | Doc 1 §8.9; doc 8 §9.7. |
| 12 | Remove or hide out-of-scope Desk actions (publish, PDF, bidders, etc.) | Not started | | Doc 8 §10 forbidden buttons. |
| 13 | Run officer smoke (doc 9) and attach evidence | Not started | | Aligns with **Officer step 9**; run after impl seq 1–12 sufficient. |

---

## How to use

1. Read **Officer step 1** (scope) and the spec for the row you are implementing.
2. For coding, follow **doc 8** Cursor Implementation Prompt (§25) and **Implementation sequence** rows in order unless a dependency dictates otherwise.
3. Update **Status** and **Evidence** on this page; log **`STD-OFFICER-NNN`** in [`ISSUES_LOG.md`](ISSUES_LOG.md) for decisions, blockers, path deviations (mirror to [`../ISSUES_LOG.md`](../ISSUES_LOG.md) when programme-visible).
4. Extend this tracker with extra rows if a spec splits deliverables (e.g. separate Playwright spec per major panel) — keep **Officer step** ids stable for audit.
