# Lean F0 — Template and Workspace Foundation Report

| Item | Value |
|---|---|
| Status | Complete (F0 only) |
| Binding pack | `05_Cursor_Section_by_Section_Electronic_IT_STD_Implementation_Pack_v1.md` — Prompt F0 + Common Control Rules §3 |
| Date | 2026-07-24 |

## Goal

Establish the shared lean foundation required by later section prompts: a manually curated PPRA IT STD template kept **Draft** while sections are incomplete, readable validator + lifecycle metadata, tender instantiation to one immutable snapshot/hash on `IT Tender Publication Record`, shared section-response/status/issue interfaces, and A2 checklist authority from that snapshot (development preview or Approved ordinary publication).

## Template path and version

| Artifact | Path |
|---|---|
| Template | `kentender_procurement/tender_configurations/electronic_std_templates/ppra_it_std_v1.json` |
| Approval sidecar | `.../ppra_it_std_v1.approval.json` — **`status: Draft`** |
| Validator | `.../electronic_std_templates/validator.py` |
| Template ID / version | `PPRA-IT-STD` / `1.0` |

## Lifecycle state

- Statuses: `Draft → Reviewed → Approved → Retired`
- Current: **Draft** (preparer recorded; `approved_by` / `approved_at` null)
- Preparer must not be the final approver when F900 Approves
- Template load does **not** require Approved; ordinary publish does

## Preview vs ordinary publish gates

| Path | API | Template status allowed |
|---|---|---|
| Ordinary bidder-visible publish | `publication_setup.publish_tender` → `seal_electronic_template_on_publication` | **Approved only** (`KT_ELECTRONIC_TEMPLATE_UNAPPROVED` otherwise) |
| Development preview | `publish_tender_for_development_preview` / `seal_electronic_template_for_development_preview` | Draft / Reviewed / Approved — **Administrator only** |

Lean/A2/NSSF test seeds use the development-preview path while the curated template remains Draft.

## Canonical registry and applicability

Full registry order (11 keys):

1. `tender_documents_and_addenda`
2. `lot_and_alternative_selection` — when `lots_or_alternatives_configured`
3. `form_of_tender`
4. `confidential_business_questionnaire`
5. `statutory_declarations`
6. `tender_security` — when `tender_security_required`
7. `preliminary_requirements_and_evidence`
8. `qualification_and_capability`
9. `technical_proposal_and_implementation_plan`
10. `requirements_compliance`
11. `price_schedule`

Instantiation includes only applicable sections (no hard “exactly N sections” fail). NSSF calibration count overlay was removed from the foundation path. Lean NSSF publish (`publish_e1_nssf_with_electronic_template`) forces TDS `tender_security_required=Yes` (not in the template file) so the applicable set is registry minus lots only (10 sections). No NSSF constants in the template file.

## Shared interfaces

| Module | Role |
|---|---|
| `services/section_response_envelope.py` | Normalize/read/write `{ section_key, payload, meta }` into bid responses (payload-only storage for FoT/A2 compat) |
| `services/section_status.py` | Canonical snake_case statuses + `derive_generic_section_status` / `issue_result`; A2 Title Case via `to_display_status` |

Wired: `electronic_bid.save_section_responses` through the envelope; checklist generic status via shared helper (FoT-specific derive remains a temporary adapter — **out of F0 claim**).

## Checklist authority

A2 checklist reads `IT Tender Publication Record.electronic_template_snapshot` only (development-preview or Approved seal). Legacy `schema_compiler.SECTION_KEYS` is not authoritative.

## FoT pages exist but out of F0 scope

Website Form of Tender routes/services from the prior lean FoT slice remain in the tree for later section work. **They are not claimed under F0.** F0 does not deepen FoT fields or add other section pages.

## Explicit non-scope (stop confirmation)

Not implemented in this run: S100–S900, X100, G100/G200, A100, F900, new FoT fields/pages, BWMF repair, template-authoring UI.

**Stop after this report.**

## Test evidence

```bash
bench --site kentender.midas.com run-tests \
  --module kentender_procurement.tender_configurations.tests.test_lean_f0_foundation
# Ran 12 tests — OK

# Keep A2 green after seed/preview wiring:
cd apps/kentender_v1 && make bw-a2-domain-gate && make ui-bidder-a2-gate
```

| Suite | Result |
|---|---|
| `test_lean_f0_foundation` | **12 passed** |
| `test_lean_it_std_template_fot_slice` (regression after Draft/preview wiring) | **12 passed** |
| `bw-a2-domain-gate` | **10 + 2 passed** |
| `ui-bidder-a2-gate` | **1 passed** |
