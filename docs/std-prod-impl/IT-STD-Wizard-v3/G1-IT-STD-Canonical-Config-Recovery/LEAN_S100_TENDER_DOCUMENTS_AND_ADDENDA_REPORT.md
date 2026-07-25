# Lean S100 — Tender Documents & Addenda Report

| Item | Value |
|---|---|
| Status | Complete (S100 only) |
| Binding pack | `05_Cursor_Section_by_Section_Electronic_IT_STD_Implementation_Pack_v1.md` — Prompt S100 + Common Control Rules §3 |
| Blueprint | `02. Canonical_PPRA_IT_STD_Bidder_Submission_Section_Blueprint_v1.md` §11 |
| Design preserved | `docs/bidder-workspace/A3-documents-and-addenda/code.html` (A3 Screen C) |
| Date | 2026-07-24 |

## Goal

Bidder-facing **Tender Documents & Addenda** (`tender_documents_and_addenda`) with current package display, addenda register, and **version-bound** acknowledgements. Material package/addendum changes invalidate affected acknowledgements without deleting history; A2 checklist status is server-derived.

## Template path and section metadata

| Artifact | Path |
|---|---|
| Template | `electronic_std_templates/ppra_it_std_v1.json` — task_groups + acknowledgement_policy; `slice_status: s100_implemented` |
| Approval | `ppra_it_std_v1.approval.json` — remains **Draft**; hash updated |
| Section key / renderer | `tender_documents_and_addenda` / `document_acknowledgement` |

Task groups: `current_tender_package`, `addenda_register`, `required_acknowledgements`.

## Binding model

Stored under `Electronic Bid Submission.responses[tender_documents_and_addenda]`:

- Effective: `acknowledged`, `acknowledged_at/by`, `publication_ref`, `package_id`, `package_document_hash`, `configuration_version`, `addenda_set_digest`, `addenda_acknowledged[{id, version_or_hash}]`
- History: `acknowledgement_history[]` (prior effective snapshots with `superseded_at` + `reason`)

Acknowledgements bind **bidder + publication + package digest + addenda-set digest**.

## Invalidation

Triggers (S100): `package_document_hash` change, `addenda_set_digest` change, `publication_ref` mismatch.

On read, stale effective acks are superseded into history and treated as unacknowledged until re-ack. Cross-section impact (A100 / FoT) is **out of scope**.

## Addenda register

Append-only `IT Tender Publication Record.issued_addenda_json`. Helper/API: `append_issued_addendum` (Administrator). Empty list remains the default for ui00/NSSF.

## Routes and services

| Surface | Path |
|---|---|
| Website | `/tenders/<publication_ref>/documents` — A3 chrome + human package label / publication date / New / stale badges (digests stay server-side only) |
| Service | `services/tender_documents_addenda.py` — DTO, ack, derive, append |
| Checklist | `submission_checklist.py` uses `derive_docs_section_status` for this section |
| Instantiate | Snapshot attaches tender-owned package slots for this section |

## Explicit non-scope (stop confirmation)

Not implemented: X100, S150–S900, S200 FoT deepening, G100/G200, A100, F900, BWMF, template-authoring UI, second document library.

**Stop after this report.**

## Test evidence

```bash
bench --site kentender.midas.com run-tests \
  --module kentender_procurement.tender_configurations.tests.test_lean_s100_tender_documents_addenda
cd apps/kentender_v1 && make bw-a3-domain-gate && make ui-bidder-a3-gate
```

| Suite | Result |
|---|---|
| `test_lean_s100_tender_documents_addenda` | **5 passed** |
| `bw-a3-domain-gate` | **OK** |
| `ui-bidder-a3-gate` | **1 passed** |
