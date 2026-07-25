# Lean X100 — Evidence and Issues Foundations Report

| Item | Value |
|---|---|
| Status | Complete (X100 only) |
| Binding pack | `05_Cursor_Section_by_Section_Electronic_IT_STD_Implementation_Pack_v1.md` — Prompt X100 + Common Control Rules §3 |
| Blueprint | `02. Canonical_PPRA_IT_STD_Bidder_Submission_Section_Blueprint_v1.md` §22–23 |
| UI shell | Reused A2/A3 bidder workspace (no Stitch A* Evidence/Issues mockups) |
| Date | 2026-07-24 |

## Goal

Cross-cutting **Evidence Register** and server-derived **Issues** for electronic bid submission. Evidence is upload-once / link-many with versioning and seal freeze. Issues aggregate blockers (docs acknowledgement + missing evidence metadata) with correction routes. Neither view is a checklist progress row.

## Evidence

| Artifact | Path |
|---|---|
| Persistence | `Electronic Bid Submission.evidence_register_json` + `evidence_seal_snapshot_json` |
| Service | `services/bid_evidence.py` — upload / replace / link / unlink / register / seal freeze |
| APIs | `get_evidence_register`, `upload_evidence`, `replace_evidence`, `link_evidence`, `unlink_evidence` |
| Website | `/tenders/<publication_ref>/evidence` — `www/tenders/evidence.py` + `.html` |
| Audit events | `evidence_uploaded`, `evidence_replaced`, `evidence_linked`, `evidence_unlinked` on `Electronic Bid Audit Event` |

Rules enforced: allowlisted file types; certificate-type metadata required (issuer, reference, issue date, validity); superseded versions retained; presentation DTO strips `file_id` / internal keys; seal snapshot freezes current evidence versions into the seal hash path.

## Issues

| Artifact | Path |
|---|---|
| Shape | `section_status.issue_item` — severity `blocker` / `warning` / `information` |
| Service | `services/bid_issues.py` — `get_issue_register`, `clear_issue_blockers_denied` |
| Website | `/tenders/<publication_ref>/issues` — `www/tenders/issues.py` + `.html` |

Aggregates: documents acknowledgement / stale ack / required addenda blockers; evidence missing-metadata blockers with correction route to Evidence. Clients cannot dismiss authoritative blockers.

## UI placement

Sidebar foot links (`kt-a2-nav-evidence`, `kt-a2-nav-issues`) on the A2 workspace shell — outside checklist progress. Routes registered in `hooks.py` `website_route_rules`.

## Explicit non-scope (stop confirmation)

Not implemented: S150–S900, S200 FoT deepening, G100/G200, A100, F900, BWMF repair, checklist progress rows for Evidence/Issues, redesign of A0–A4, full upload UI controls beyond register shell.

**Stop after this report.**

## Test evidence

```bash
bench --site kentender.midas.com run-tests \
  --module kentender_procurement.tender_configurations.tests.test_lean_x100_evidence_and_issues
cd apps/kentender_v1 && make bw-x100-domain-gate
```

| Suite | Result | Wall time (this session) |
|---|---|---|
| `test_lean_x100_evidence_and_issues` (web + domain) | **8 passed** (1 web + 7 domain) | ~16s tests; ~19s migrate when schema changed |
| `bw-x100-domain-gate` | **OK** (same module) | — |

## Session timing notes (why “15+ minutes”)

Measured wall times for this continuation (not agent think-time):

| Step | Wall |
|---|---|
| UI templates + hooks + sidebar | ~1–2 min edit |
| `bench migrate` (full apps) | ~20s each |
| Domain+web test module | ~14–16s |
| Fix loops (invalid PDF fixture → pypdf; Jinja `r.items` vs `dict.items`; missing `SEVERITY_INFORMATION` import; audit Select options) | ~3–4 min total CPU |

Dominant non-code cost historically: session summarization / re-discovery and re-planning after interrupts, not Frappe itself. Local FS ops are sub-second; migrate+tests are the multi-second gate.
