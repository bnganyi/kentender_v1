# Final Submission — Implementation Report

## Goal

Ship the bidder Final Submission workflow (Review & Validate → Final Bid Review → Submit Bid → Receipt) so a completed checklist can become a formally submitted, immutable electronic bid — with server-authoritative readiness, plain-language Submit Bid UX, and a human-readable receipt (no checklist rows for Final Review / Declaration / Submission).

## Scope delivered

| Area | Status |
|---|---|
| Readiness aggregator (`final_submission.py`) composing checklist + module statuses | Done |
| Checklist CTA **Review & Validate Bid** + sidebar Review/Submit enablement | Done |
| Website Stitch 01–05 (R&V, Final Bid Review, Submit + dialog, Receipt) | Done |
| Portal `submit_bid` seal on `Electronic Bid Submission` (owner submit; no hashes in receipt DTO) | Done |
| Layout guard + Makefile gates + Playwright happy path | Done |
| Test seed `seed_ready_lean_bid_for_final_submission_tests` | Done |

## Architecture

- Domain: [`tender_configurations/services/final_submission.py`](../../kentender_procurement/kentender_procurement/tender_configurations/services/final_submission.py)
- Checklist unlock: [`submission_checklist.py`](../../kentender_procurement/kentender_procurement/tender_configurations/services/submission_checklist.py)
- Website: `www/tenders/review_and_validate.*`, `final_bid_review.*`, `submit_bid.*`, `submission_receipt.*` + `public/css/final_submission_web.css` + `public/js/final_submission_web.js`
- Routes (before section catch-all in `hooks.py`):
  - `/tenders/<ref>/review-and-validate`
  - `/tenders/<ref>/final-bid-review`
  - `/tenders/<ref>/submit-bid`
  - `/tenders/<ref>/submission-receipt`
- APIs: `get_bid_submission_readiness`, `get_final_bid_review`, `get_submit_bid_page`, `submit_electronic_bid`, `get_submission_receipt`, `seed_ready_lean_bid_for_final_submission_tests`

## Validation rules aggregated

- Applicable required section Completes from the same checklist derive path (docs, CBQ, statutory, PS, FoT, …)
- Configuration-excluded / N/A sections do not block
- Deadline open (server time); closed deadline blocks submit
- FoT/PS totals kept separated by currency; FoT display uses PS projection
- Declaration confirmation required at submit; client cannot set sealed time/status/totals

## Permission rules enforced

- Bid **owner** (and Administrator for tests/PoC) may submit
- Non-owners: review remains available; Submit disabled with “You do not have permission to submit this bid.”
- Multi-user bidder-team roles: **follow-on** (not in repo today)

## Submission state changes

- Draft → Sealed on successful `submit_bid`
- Evidence frozen via `freeze_evidence_for_seal`
- Internal `seal_hash` retained on DocType; **omitted** from bidder-facing receipt DTO
- Sealed bids reject section saves (immutable)

## Receipt implementation

- User-facing: receipt reference, submitted datetime + timezone, tender/bidder/lots/totals, submitter name, status Submitted
- Print + HTML download actions; Return to My Bids

## Evidence commands

```bash
bench --site kentender.midas.com clear-cache
cd apps/kentender_v1 && make bw-final-submission-domain-gate
cd apps/kentender_v1 && make ui-bidder-final-submission-gate

## UX rectification (2026-07-30)

1. **Leaked internals** — Technical Proposal supporting-evidence list no longer renders `evidence_type` slugs; Final Bid Review no longer shows the FoT “not a separate stored total” implementation note.
2. **Continue CTA contrast** — Footer rule `.kt-fs-footer > a { color: #515f74 }` overrode primary button text; removed that descendant rule and locked `.kt-fs-btn--primary` to white (`!important`).
3. **Stitch fidelity** — Final Bid Review rebuilt to context card grid + Bid Section Summaries (price card highlight); Submit Bid rebuilt to Submission Summary | Authenticated Submitter two-column layout.
```

**Gate evidence (this delivery):**

- `test_final_submission_readiness` — 11 passed
- `test_final_submission_stitch_layout_guard` — 7 passed
- `final-submission.spec.ts` — 1 passed (~1.6m)

## Explicitly deferred / follow-on

- Multi-user bidder-team submit permission matrix
- Withdrawal / revision UI when tender policy allows
- BWMF `create_or_get_sealed_submission` bridge
- Evaluator / opening / PDF full bid package / new cryptography

## Aliases

Also covers lean pack prompts **G100** (Review & Validate) and **G200** (Submit, Seal & Receipt).
