# Lean FoT — Review and Certify Report

| Item | Value |
|---|---|
| Status | Complete (Review-and-Certify redesign) |
| Binding pack | `03_FoT/Electronic Form of Tender.md` + Stitch `01`–`04` HTML |
| Precedence | `03_FoT` redesign **wins** over lean FoT slice (early order, Save=Complete, FoT-owned legal fields) |
| UI shell | A2 bidder nav + sidebar; Website Review-and-Certify (CBQ family) |
| Date | 2026-07-25 |

## Goal

Form of Tender is a **derived legal instrument**: bidders review projected material terms after Price Schedule, disclose commissions only, then certify. Certification creates the legal record; draft save does not Complete the checklist. Source changes withdraw certification.

## Checklist order

| Change | Detail |
|---|---|
| Registry | `CANONICAL_SECTION_KEYS` ends `… → price_schedule → form_of_tender` |
| Template | `ppra_it_std_v1.json` section `order` renumbered; `form_of_tender` last |
| Approval hash | `ppra_it_std_v1.approval.json` updated to match file SHA-256 |
| Final Declaration | **Not** added (out of scope) |

## Source gaps (minimal)

| Owner | Fields for FoT projection |
|---|---|
| CBQ | SOE Yes/No + ITT 4.7; authorized signatory name/title; authority-to-bind |
| Price Schedule | `discounts_offered` + discount detail fields on bidder response contract; incomplete price blocks certify |

## Service / API

| Artifact | Path |
|---|---|
| Service | `services/form_of_tender.py` — readiness, commissions-only save, certify, invalidate |
| APIs | `get_form_of_tender`, `save_form_of_tender`, `certify_form_of_tender` |
| Audit events | `fot_certified`, `fot_certification_invalidated` on `Electronic Bid Audit Event` |
| Invalidation | CBQ store + `save_section_responses` for docs / lots / price / statutory |

Complete checklist status only when all required FoT instances are certified.

## Website UI (Stitch 01–04)

| Surface | Path |
|---|---|
| Route | `/tenders/<publication_ref>/sections/form_of_tender` |
| Template | `www/tenders/form_of_tender.html` |
| CSS | `public/css/form_of_tender_web.css` |

Markers: incomplete banner, material offer summary, signatory card, legal terms drawer, commissions Yes/No (no default), certify dialog, certified panel, fixed footer. Removed editable legal name/address, price re-entry, declarations a–s, NSSF hard-coding.

## Seed isolation fix

`seed_ui00_dashboard(clear=True)` now deletes `Electronic Bid Submission` rows for seed configs before deleting configurations (stable config names were reusing polluted drafts).

## Explicit non-scope

Final Declaration / Submit & Seal UI; full Price Schedule / Lots / Statutory portals; field-level invalidation graphs; generic legal-document engine.

## Test evidence

```bash
cd apps/kentender_v1 && make bw-fot-domain-gate
cd apps/kentender_v1 && make ui-bidder-fot-gate
```

| Suite | Result | Wall |
|---|---|---|
| `test_lean_fot_review_certify` | **9 passed** | ~24s |
| `test_lean_it_std_template_fot_slice` | **12 passed** | ~16s |
| `test_lean_f0_foundation` | **12 passed** | ~30s |
| `ui-bidder-fot-gate` (`fot-review-certify.spec.ts`) | **1 passed** | ~15s |

Gates: `bw-fot-domain-gate`, `ui-bidder-fot-gate`.
