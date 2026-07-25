# Lean Statutory Declarations — Review and Certify Report

| Item | Value |
|---|---|
| Status | Complete (Review-and-Certify redesign) |
| Binding pack | `05_Statutory/Stitch Statutory Declarations Prompts.md` + Stitch `01`–`04` HTML |
| Precedence | `05_Statutory` prompt + Stitch **wins** over lean `route_only` stub |
| UI shell | A2 bidder nav + sidebar; Website Review-and-Certify (FoT/CBQ family) |
| Date | 2026-07-25 |

## Goal

Statutory Declarations is a **single declaration-bundle screen**: bidders review four fixed IT STD legal records, answer the independent-tender question (with optional competitor disclosures), and certify once. Certification produces four separate legal-record snapshots. Draft save does not Complete the checklist. Source changes withdraw the whole bundle.

## Checklist order

| Change | Detail |
|---|---|
| Registry | Unchanged — CBQ → `statutory_declarations` → … → FoT |
| Template | `ppra_it_std_v1.json` section `slice_status: statutory_implemented` + `legal_records[]` |
| Approval hash | `ppra_it_std_v1.approval.json` → `625610a0c9c98891da8182842fe9bcb88f3c4b573c5e1ea2396094b3aae00d17` |
| Complete rule | Checklist Complete **only when certified** (not on save) |

## CBQ declarant source gaps

| Field | Role |
|---|---|
| `authorized_signatory_name` / `title` / `authority_to_bind_confirmed` | Declarant identity (allowlisted) |
| `declarant_postal_address` | Postal address for legal records |
| `declarant_place_of_residence` | Place of residence |
| `declarant_country_of_residence` | Country of residence |
| SOE keys | Retained for FoT; not owned by Statutory |

Missing declarant address fields block certify; UI links Edit in CBQ. Affirmation copy states authority to certify bid forms and bind the Tenderer.

## Service / API

| Artifact | Path |
|---|---|
| Service | `services/statutory_declarations.py` — readiness, save, certify (4 records), invalidate |
| APIs | `get_statutory_declarations`, `save_statutory_declarations`, `certify_statutory_declarations` |
| Audit events | `statutory_certified`, `statutory_certification_invalidated` on `Electronic Bid Audit Event` |
| Invalidation | CBQ `_store_response` (declarant/material fields) + statutory owned-input save after certify |
| FoT readiness | `_statutory_complete` / `is_statutory_certified` — certified bundle required |
| Checklist | `derive_statutory_section_status` + `portal_statutory_url` |

Owned persist only: `independent_tender_choice` (`independent` \| `disclosed`, no default) + disclosure rows (`competitor_name`, `nature_of_interaction`, `reason`, `complete_details`).

## Website UI (Stitch 01–04)

| Surface | Path |
|---|---|
| Route | `/tenders/<publication_ref>/sections/statutory_declarations` (dedicated; before catch-all) |
| Template | `www/tenders/statutory_declarations.html` |
| CSS | `public/css/statutory_declarations_web.css` (+ FoT footer/dialog patterns) |

Markers (`kt-stat-*`): Authorized Declarant card; Independent Tender radios (no default); conditional disclosure table + discard confirm; SD1/SD2/Ethics statements; legal text drawer; certify dialog; certified panel; fixed footer. No per-form certify, signatures, stamps, PDFs, hashes, witness fields, or NSSF hard-coding.

## Unresolved — witness workflow

**Witness invitation / signature workflow is not implemented** (explicit non-scope). Recorded here as unresolved for a later slice. No witness UI fields shipped.

## Explicit non-scope

- Witness invitation/signature workflow (**unresolved**)
- Final Declaration / Submit & Seal
- Other checklist sections (security, technical, price)
- Generic legal-document engine, digests, BWMF pipelines
- Field-level invalidation graphs
- Production migration complexity

## Deviations

None material vs `05_Statutory` Stitch contract. Fraud & Corruption appendix text is attached to the Code of Ethics record (not a fifth legal record), per pack.

## Test evidence

```bash
cd apps/kentender_v1 && make bw-statutory-domain-gate SITE=kentender.midas.com
cd apps/kentender_v1 && make ui-bidder-statutory-gate
```

| Suite | Result | Wall |
|---|---|---|
| `test_lean_statutory_declarations` | **9 passed** | ~18s |
| `test_lean_fot_review_certify` (regression) | **9 passed** | ~46s |
| `test_lean_it_std_template_fot_slice` (regression) | **12 passed** | ~51s |
| `test_lean_f0_foundation` (regression) | **12 passed** | ~44s |
| `test_submission_checklist_api` (Needs Attention/Resume on `tender_security`) | **9 passed, 1 skipped** | ~32s |
| `ui-bidder-statutory-gate` (`statutory-declarations.spec.ts`) | **1 passed** | ~22s |

Gates: `bw-statutory-domain-gate`, `ui-bidder-statutory-gate`.
