# Bid Submissions — Delivery Report (docs/bids §25)

| Item | Value |
|---|---|
| Date | 2026-07-31 |
| Status | Implemented (officer Desk module) |

## Goal delivered

Officer Desk **Bid Submissions** replaces Coming Soon: list tenders by submission stage, keep bids sealed until authorised opening, open under server gates, show immutable register, review sealed snapshots read-only. No evaluation/scoring.

## Files changed (primary)

| Area | Path |
|---|---|
| Bid fields | `tender_configurations/doctype/electronic_bid_submission/` |
| Opening model | `tender_configurations/doctype/it_bid_opening_record/` |
| Service | `tender_configurations/services/bid_submissions.py` |
| Seal stamp | `tender_configurations/services/electronic_bid.py` (`submit_and_seal`) |
| API / package | `tender_configurations/api.py`, `__init__.py` |
| Desk UI | `public/js/bid_submissions_page.js`, `public/css/bid_submissions_page.css` |
| Sidebar | `workspace_sidebar/procurement.json`, `setup/sidebar_availability.py` |
| Fixtures | `seed/bid_submissions_officer_fixtures.py` |
| Tests | `tests/test_bid_submissions_api.py`, `tests/ui/smoke/bid-submissions/` |
| Gates | `Makefile` → `bid-submissions-domain-gate`, `ui-bid-submissions-gate` |

## Models reused

- `Electronic Bid Submission` (sealed snapshot, responses, evidence seal, receipt)
- `IT Tender Publication Record` (deadlines, electronic template snapshot)
- `Electronic Bid Audit Event` (bid-side); opening audit on `IT Bid Opening Record.audit_json`

## Opening model added

`IT Bid Opening Record` — refs only (`active_submission_ids` JSON), statuses Draft / In Progress / Completed, immutable when Completed.

## Active version selection

Latest `Sealed` bid per `(owner, offer_type)` with `sealed_at` ≤ submission deadline, `superseded_by` empty, not withdrawn.

## Sealed protections

- List/sealed DTOs omit names, counts, receipts, bid ids before Completed opening
- Register / overview / section / evidence APIs require Completed opening
- Administrator does not bypass sealing
- Open dialog is UI only; server enforces deadline, scheduled opening, permission, duplicate lock

## Permissions

| Capability | Roles (demo) |
|---|---|
| View metadata / register / bid | System Manager, Purchase Manager, Procurement Manager, Tender Manager, Purchase User, Auditor |
| Open bids / evidence download | Opening roles + Administrator |
| Version history | Opening roles + Auditor |

## Routes and methods

- Desk: `/desk/bid-submissions`, `…/<publication_id>`, `…/bid/<bid_id>`, `…/section/<key>`, receipt & opening-record segments
- Whitelisted: `list_bid_submission_tenders`, `get_bid_submission_sealed_status`, `open_submitted_bids`, `get_opening_register`, `get_submitted_bid_overview`, `get_submitted_section_response`, `get_submission_receipt_view`, `get_opening_record_view`, `download_submitted_evidence`, `get_submission_version_history`, `seed_bid_submissions_officer_fixtures`

## Read-only renderer

Section review renders sealed JSON payload (pretty-printed). Bidder Workspace interactive editors are not reused yet; content is snapshot-only with no save/edit chrome.

## Fixtures (§23)

`seed_bid_submissions_officer_fixtures`: receiving, closed sealed, opened×3, supersession, withdrawn, multi-lot, alternative, opened empty; role notes for metadata-only vs opener.

## Tests

| Suite | Command / result |
|---|---|
| Domain | `make bid-submissions-domain-gate` |
| UI | `make ui-bid-submissions-gate` |
| Sidebar | G0-012 contract updated for `bid-submissions` link |

## Remaining gaps (genuine)

1. Rich FoT/price HTML renderers (reuse bidder section widgets) — JSON read-only for v1
2. Full PE-scoped filtering beyond role gates
3. “Released to evaluation” action intentionally not fabricated (§21)
4. Withdraw/resubmit product UX for bidders still thin (officer tooling helpers exist for fixtures)
5. Seed multi-scenario currently recreates UI00 each `ensure_pub` call (heavy; acceptable for demo/test)
