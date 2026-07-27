# Lean Tender Security — completion report

## Goal

Bidder checklist task for published TDS mode: **instrument**, **Tender-Securing Declaration**, or **none** (omit). Never both.

## Mode mapping (TDS)

| TDS `tender_security_type` | `tender_security_required` | Mode | Checklist |
|---|---|---|---|
| `Tender Security` | Yes (typical) | `instrument` | Row titled Tender Security |
| `Tender-Securing Declaration` | Yes (typical) | `securing_declaration` | Row titled Tender-Securing Declaration |
| `Not Required` / required No | — | `none` | Section omitted |
| Legacy: required Yes, type empty | Yes | `instrument` | Compatibility |

Resolver: `resolve_tender_security_mode` in `electronic_std_template.py` (also used by `services/tender_security.py`).

## Files changed

| Area | Path |
|---|---|
| Template | `electronic_std_templates/ppra_it_std_v1.json` + `ppra_it_std_v1.approval.json` |
| Applicability | `services/electronic_std_template.py` (`tender_security_applicable`) |
| Service | **new** `services/tender_security.py` |
| API | `api.py` — `get_tender_security`, `save_tender_security`, `certify_tender_securing_declaration` |
| Audit | `electronic_bid_audit_event.json` — certify/invalidate events |
| Checklist | `submission_checklist.py` — specialized status + URL |
| CBQ invalidate | `confidential_business_questionnaire.py` |
| Website | **new** `www/tenders/tender_security.{py,html}`, `public/css/tender_security_web.css` |
| Routes | `hooks.py`, `www/tenders/section.py` |
| Seeds | `preview_fixtures.py`, `ui00_seed.py`, `lean_synthetic_it_seed.py` — set `tender_security_type` |
| Tests | **new** `test_lean_tender_security.py`, `tests/ui/smoke/bidder-workspace/tender-security.spec.ts` |
| Guinea pig | `test_submission_checklist_api.py` → `preliminary_requirements_and_evidence` |
| Makefile | `bw-tender-security-domain-gate`, `ui-bidder-tender-security-gate` |

## Data model

No new DocType. Bidder payload under Electronic Bid `responses.tender_security`:

- Instrument: `{ mode, instrument{…}, section_status, validation_errors, complete }`
- Declaration: `{ mode, certified*, legal_text_snapshot, material_fingerprint, requires_recertification, … }`

Upload reuses Desk `upload_file` attach to the bid; URL stored on instrument fields (no new evidence engine).

## Gates (evidence)

```bash
make bw-tender-security-domain-gate SITE=kentender.midas.com
# → 13 tests OK (modes, instrument save/validate, declaration certify/invalidate, none omits)

make ui-bidder-tender-security-gate
# → Playwright tender-security.spec.ts passed (instrument shell on seeded tender)

bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.tender_configurations.tests.test_submission_checklist_api
# → OK (guinea pig moved to preliminary_requirements_and_evidence)
```

## UX rectification (2026-07-26)

First UI pass used CBQ grid classes without loading CBQ CSS and a flat requirements list — not Stitch. Rectified to:

- Requirements **bento** (amount / validity / types / beneficiary / applicant / issuer conditions)
- Dedicated `.kt-sec-form-grid` (2-col, full-width issuer fields, nested date pair)
- Electronic **submission method cards** with in-card upload dropzone / hosted fields
- Footer **Save draft** + **Save and continue**; PE responsiveness note
- Declaration summary/signatory cards + center certify CTA
- DTO enrichments: TDS currency fallback (`tender_currency`), overview `dates.submission_deadline`, formatted amount/validity displays

## Unresolved (explicit)

1. **PE pre-opening confidentiality** — no PE Desk gate in this slice; evaluator/approval out of scope.
2. **28 vs 30-day instrument / declaration expiry wording** — left to published template `declaration.legal_text_template` and TDS validity slots; runtime does not guess which calendar rule applies beyond configured periods.
3. **Issuer route metadata beyond defaults** — template defaults supply upload + issuer-hosted; PE-specific registry URLs need future TDS/slot extension when authoring UI exists.

## Non-scope (confirmed)

PE evaluator review; BWMF digest pipelines; performance security / PI as tender security; NSSF hard-coding.
