# LEAN S600 — Qualification and Capability Implementation Report

## Goal

Bidder-facing **Qualification and Capability** section with overview + five Stitch-faithful category screens, server-derived status/issues, A2 checklist roll-up, EXP-1 nine-month qualifying years, baseline tender/lot/JV-member scope, and three PE-neutral fixtures — without NSSF hard-coding or evaluator scores.

## UI fidelity (binding)

Pattern: **CBQ-style** Website shell + hand-port of Stitch main canvas from `08_Qualifications/01_code.html`–`06_code.html` (no Tailwind CDN, no form-stack approximations).

| Screen | Stitch | Shipped |
|---|---|---|
| Overview | `01_code.html` | Category table + required-categories KPI |
| Contract performance | `02_code.html` | Reporting entity + 3 Yes/No disclosure tables |
| Financial capability | `03_code.html` | Configured requirements + FY / turnover / resources tables |
| Experience | `04_code.html` | General + Specific project tables + project drawer |
| Key personnel | `05_code.html` | Personnel Matrix + Assign person drawer |
| Delivery partners | `06_code.html` | Item/provider matrix + Partner Record drawer |

Anti-regression:

- Static layout guard: `test_qualification_stitch_layout_guard.py` (wired into `bw-qualification-domain-gate`)
- Playwright asserts Stitch structure across all five categories + financial Complete path
- Workspace rule: `.cursor/rules/kentender-bidder-stitch-fidelity.mdc`

## Existing components reused

- Electronic bid section JSON persistence (`Electronic Bid Submission.responses`)
- Published electronic template snapshot + `materialize_*` pattern from Preliminary
- X100 / evidence register patterns (evidence references; tender-specific auth scoped to publication)
- Bidder portal shell (nav, workspace sidebar, FoT CSS tokens)
- A2 `submission_checklist` specialization pattern
- Website route hooks before `<section_key>` catch-all

## Files changed / added

| Area | Path |
|---|---|
| Template | `electronic_std_templates/ppra_it_std_v1.json`, `__init__.py` (`qualification_response`), approval hash |
| Materialize | `services/electronic_std_template.py` → `materialize_qualification_categories` |
| Fixtures | `seed/lean_qualification_criteria.py` (full / reduced / conditional) |
| Service | `services/qualification_and_capability.py` |
| Website | `www/tenders/qualification_and_capability.{py,html}`, `qualification_category.{py,html}` |
| Stitch includes | `templates/includes/qualification/kt_s600_{contract,financial,experience,personnel,partners}.html` |
| Assets | `public/css/qualification_and_capability_web.css`, `public/js/qualification_and_capability_web.js` |
| Tests | domain + `test_qualification_stitch_layout_guard.py` + Playwright structure smoke |
| Gates | `make bw-qualification-domain-gate`, `make ui-bidder-qualification-gate` |

## Applicability / EXP-1 / validation

Unchanged from domain slice: required / optional / conditional / excluded; EXP-1 nine-month qualifying years; checklist roll-up; three fixtures (full / reduced / conditional). See prior domain section tests.

## Evidence

```text
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.tender_configurations.tests.test_lean_qualification_and_capability
→ OK (13)

bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.tender_configurations.tests.test_qualification_stitch_layout_guard
→ OK (7)

npx playwright test --workers=1 --retries=0 \
  tests/ui/smoke/bidder-workspace/qualification-and-capability.spec.ts
→ OK (overview + five category structure + financial Complete)
```

## Deferred (explicit — not Stitch tables/drawers)

| Deferred case | Reason |
|---|---|
| Complex multi-lot combination matrices | Baseline lot filter only |
| Unusual JV authority graphs | Baseline member selector |
| Exhaustive §14 combinatorial matrix | Principal transitions + three fixtures |
| Pack Preference Information as sixth screen | Not in approved Stitch set |
| Evaluator scores / pass-fail | Forbidden |
| Full X100 upload drawer parity in every evidence cell | References + checkboxes; upload can deepen via Preliminary/X100 |
| Cross-tender org certificate library UX | Tender-specific auth blocked across tenders |

## Status

**Partial → Stitch UI redo complete for structure + primary wiring.** Domain gates green; Playwright structure smoke green. Further field-level polish (rich EXP-2 similarity dimensions UI, CV workspace) remains optional depth beyond the approved Stitch screens’ core tables/drawers.
