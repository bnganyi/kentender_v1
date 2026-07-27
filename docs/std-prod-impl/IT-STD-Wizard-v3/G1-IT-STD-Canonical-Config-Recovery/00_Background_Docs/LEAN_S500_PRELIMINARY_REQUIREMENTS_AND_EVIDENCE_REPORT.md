# LEAN S500 — Preliminary Requirements and Evidence Report

## Goal

Bidder Preliminary Requirements and Evidence is a dynamic criteria checklist driven by published Preliminary-stage evaluation criteria (not NSSF hard-coding), with a right-hand response drawer, X100 evidence wiring, and linked FoT / Statutory / Tender Security status projection.

## Files changed

| Area | Path |
|---|---|
| Template | `tender_configurations/electronic_std_templates/ppra_it_std_v1.json` (`eligibility_checklist`, `preliminary_implemented`) |
| Approval hash | `electronic_std_templates/ppra_it_std_v1.approval.json` |
| Renderer allowlist | `electronic_std_templates/__init__.py` |
| Instantiation | `services/electronic_std_template.py` → `materialize_preliminary_criteria` |
| Lean criteria seed | `seed/lean_preliminary_criteria.py` (+ `preview_fixtures.py`, `ui00_seed.py`, `lean_synthetic_it_seed.py`) |
| Service | **new** `services/preliminary_requirements.py` |
| API | `tender_configurations/api.py` (`get_preliminary_requirements`, `save_preliminary_response`) |
| Checklist | `services/submission_checklist.py` (specialize + guinea pig → `qualification_and_capability`) |
| Website | **new** `www/tenders/preliminary_requirements.{py,html}`, `public/css/preliminary_requirements_web.css` |
| Routes | `hooks.py`, `www/tenders/section.py` |
| Domain tests | **new** `tests/test_lean_preliminary_requirements.py` |
| Playwright | **new** `tests/ui/smoke/bidder-workspace/preliminary-requirements.spec.ts` |
| Makefile | `bw-preliminary-domain-gate`, `ui-bidder-preliminary-gate` |

## Criterion mapping (lean PE-neutral seed)

| criterion_id | Title | Method | Notes |
|---|---|---|---|
| prelim-business-registration | Business registration certificate | upload | always |
| prelim-tax-compliance | Tax compliance certificate | select_or_upload | `valid_on_submission_deadline` |
| prelim-product-authorisation | Product authorisation letter | upload | always |
| prelim-jv-agreement | Joint Venture agreement | upload | `jv_only` → N/A for single bidder |
| prelim-form-of-tender | Form of Tender | linked_section | → FoT |
| prelim-statutory-declarations | Statutory Declarations | linked_section | → Statutory |
| prelim-tender-security | Tender Security | linked_section | → Tender Security (N/A when mode none) |

NSSF / other PE tenders keep their own Preliminary CFG rows; runtime materializes whatever is published.

## TDS / CFG sources

- Criteria: `Tender Configuration.evaluation_setup.criteria` where `stage == Preliminary`, enriched with optional `response_method`, `linked_section_key`, `validity_rule`, file limits, applicability.
- Validity dates: publication overview / TDS submission deadline and opening datetime.
- JV applicability: CBQ bidder entity type / `jv_mode`.
- Evidence pool: X100 bid evidence register (`upload_evidence` / `link_evidence` with `target_kind=preliminary_criterion`).

## Gates

```bash
make bw-preliminary-domain-gate SITE=kentender.midas.com
make ui-bidder-preliminary-gate
```

## Unresolved (explicit non-scope)

1. PE preliminary evaluation / Passed–Failed decisions (completeness only).
2. Template-authoring UI for preliminary criteria.
3. Org-wide reusable evidence library beyond the bid’s X100 register.

## Anti-patterns avoided

- No NSSF titles hard-coded in service logic.
- No Passed / Failed / Approved / Compliant bidder statuses.
- Main footer uses **Continue** (not Save & Continue); drawer uses **Save response**.
- Expired tax evidence → Needs attention; not preselected; completion banner hidden.
