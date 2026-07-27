# Lean S300 — Confidential Business Questionnaire Report

| Item | Value |
|---|---|
| Status | Complete (S300 + pixel UI wiring) |
| Binding pack | `05_Cursor_Section_by_Section_Electronic_IT_STD_Implementation_Pack_v1.md` — Prompt S300 + Common Control Rules §3 |
| Blueprint | `02. Canonical_PPRA_IT_STD_Bidder_Submission_Section_Blueprint_v1.md` §14 |
| Design | `CBQ/Stitch_Confidential_Business_Questionnaire_Screen_Prompts_v1.md` + `step_1_code.html` … `step_5_code.html` |
| Obligations | `IT-BSO-CBQ-001` … `IT-BSO-CBQ-012` |
| UI shell | FoT/A2 bidder nav + sidebar; Stitch main canvas (5-step wizard) |
| Date | 2026-07-25 |

## Goal

Bidder-facing **Confidential Business Questionnaire** matching Stitch pixel fidelity for the main canvas (stepper, forms, 9-row conflict matrix, certify), wired to get/save/JV/certify whitelist APIs so drafts and certifications persist. No verified-profile panel; tender PE / publication ref / opening prefilled only.

## Related: S150 deferred

Lots & Alternatives remain deferred — see [`LEAN_S150_LOTS_AND_ALTERNATIVES_DEFERRED.md`](LEAN_S150_LOTS_AND_ALTERNATIVES_DEFERRED.md). Single-lot / alternatives-prohibited tenders (including NSSF) continue to omit `lot_and_alternative_selection` from checklist and progress.

## Template + schema

| Artifact | Path |
|---|---|
| Template | `electronic_std_templates/ppra_it_std_v1.json` — CBQ `renderer: questionnaire`, 9 `conflict_rows`, `slice_status: s300_implemented` |
| Approval | `ppra_it_std_v1.approval.json` — remains **Draft**; hash updated |
| Allowlist | Expanded `ALLOWED_ANSWER_KEYS` + `CONFLICT_ROW_KEYS` (`q1_…` … `q9_…`) in `services/confidential_business_questionnaire.py` |

Task groups: `entity_selection`, `general_particulars`, `business_registration`, `entity_type_details`, `relationship_disclosures`, `conflict_matrix`, `questionnaire_certification`.

## Binding model

Stored under `Electronic Bid Submission.responses[confidential_business_questionnaire]`:

- `entities[]` — `entity_id`, `role` (`bidder` / `jv_member`), `entity_type`, design answer keys, `conflict_rows` (9), certifier fields
- `tender_info` — PE name, publication_ref, opening (read-only UI bar)
- `history[]` — certification invalidation events

Completion requires every entity valid and certified. Material identity/disclosure changes clear certification. Certify requires `certifier_name`, `certifier_title`, and `authority_affirmed`.

## Routes and UI

| Surface | Path |
|---|---|
| Website | `/tenders/<publication_ref>/sections/confidential_business_questionnaire` |
| CSS | `public/css/confidential_business_questionnaire_web.css` (no Tailwind CDN) |
| Service | `services/confidential_business_questionnaire.py` |
| APIs | `get_confidential_business_questionnaire`, `save_confidential_business_questionnaire`, `add_cbq_jv_entity`, `certify_cbq_entity` |
| Checklist | `submission_checklist.py` special-case `derive_cbq_section_status` + `portal_cbq_url` |

Pixel UI: single page, client steps 1–5; entity switcher for JV; `data-testid="kt-s300-*"`; init under `frappe.ready` so `frappe.call` is available on website.

## Explicit non-scope (stop confirmation)

Not implemented: S150 domain/UI, S400+, S200 FoT deepening, G100/G200, A100, F900, org-profile editor product, NSSF vendor quals in CBQ, iframe Stitch, Tailwind CDN.

**Stop after this report.**

## Test evidence

```bash
bench --site kentender.midas.com clear-cache
bench --site kentender.midas.com run-tests \
  --module kentender_procurement.tender_configurations.tests.test_lean_s300_confidential_business_questionnaire
cd apps/kentender_v1 && make bw-s300-domain-gate
cd apps/kentender_v1 && make ui-bidder-s300-cbq-gate
```

| Suite | Result | Wall |
|---|---|---|
| `test_lean_s300_confidential_business_questionnaire` | **9 passed** (1 web + 8 domain) | ~22s (`DOMAIN_sec=21.84`) |
| `bw-s300-domain-gate` | **OK** (same module) | — |
| `ui-bidder-s300-cbq-gate` (`s300-cbq.spec.ts`) | **1 passed** | ~24s (`PW_sec=24.49`) |
| `bench clear-cache` | OK | ~2.7s |

Web asserts: root + stepper + Save draft; no verified-profile panel; no Tailwind CDN. Playwright: login → CBQ → stepper → Save draft toast → Continue → step 2.

## Session wall times (pixel wiring)

| Step | Wall |
|---|---|
| Tests + service schema + template + www/CSS/JS | prior session + this session |
| Fix `_tender_info` (`procuring_entity_name`) | ~1 min |
| Domain retest (green) | ~22s |
| Fix `frappe.ready` race on website `frappe.call` | ~5 min |
| Playwright gate (green) | ~24s |
| Full `bench migrate` | **not required** (no DocType schema change) |
