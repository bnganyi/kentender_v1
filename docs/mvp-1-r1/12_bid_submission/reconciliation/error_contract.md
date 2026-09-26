# BDS-CHG-001 v0.8: error contract (BDS-CHG-001 §8, verbatim)

| Control | Value |
|---|---|
| Version | 0.8-phase0.1 |
| Status | Phase 0 working document (plan BDS-CHG-001 v0.8) |
| Source | `KenTender_BDS-CHG-001_Supplier_and_Electronic_Bid_Submission_v0_8.md` BDS-CHG-001 §8, lines 765–798; extracted by script on 26 Sep 2026. |
| Count | 34 codes. A whole-document scan for `` `BDS_…` `` finds no code outside this table. |
| Supersedes | The 27-code table in `BDS-CHG-001_IMPLEMENTATION_TRACKER.md` (v0.4, 21 Sep 2026), which is retained unchanged as history. |
| Rule | `bid_submission/services/errors.py` holds exactly this closed set; `test_bds_schema.py` asserts equality with this table. Messages are copied, never reworded (BDS03-IMP-004, BDS03-AC-004). |

## Table (verbatim)

| Code | User-visible message and treatment |
|---|---|
| `BDS_TENDER_NOT_FOUND` | **Tender not found.** Return to Tenders. |
| `BDS_TENDER_NOT_OPEN` | **This Tender is not accepting bids.** Show the truthful published/cancelled/closed status. |
| `BDS_SIGN_IN_REQUIRED` | **Sign in to start or continue a bid.** Preserve the safe return destination. |
| `BDS_ACCOUNT_REQUIRED` | **Set up your supplier account before starting a bid.** Link Account. |
| `BDS_ACCOUNT_SUSPENDED` | **This supplier account cannot submit bids.** Show the configured support route. |
| `BDS_ARRANGEMENT_INVALID` | **Check the supplier or joint-venture information.** Link exact field/member. |
| `BDS_NOTICE_CONTACT_REQUIRED` | **Choose a verified email for Tender notices.** Link the Tender contact control; create no arrangement or workspace. |
| `BDS_RESPONSIBILITY_REQUIRED` | **An Authorised Signatory must complete this action.** |
| `BDS_DEFINITION_UNSUPPORTED` | **This bid format is not available.** Do not create a partial workspace; keep any existing Draft unchanged and show the approved support route. |
| `BDS_ADDENDUM_REVIEW_REQUIRED` | **Review the latest addendum and the affected bid responses.** Link each affected task. |
| `BDS_CLARIFICATION_DEADLINE_PASSED` | **The clarification deadline has passed.** Preserve entered text locally for copy only; create no question record. |
| `BDS_CLARIFICATION_NOT_REGISTERED` | **Start a bid before asking a question about this Tender.** Return to the Tender overview. |
| `BDS_PORTAL_INFORMATION_UNAVAILABLE` | **Supplier support information is temporarily unavailable.** Keep public Tender reading, an existing Draft and existing receipts available. Block new Start and production Submit or replacement acceptance until required support and legal links resolve; show **Continue saved bid** or **View receipts** to an authorised existing supplier, and **Try again** for a new visitor. |
| `BDS_FIELD_INVALID` | **Check the highlighted value.** Bind each exact field error. |
| `BDS_UNKNOWN_RESPONSE` | **This response is not part of the published Tender.** Reject without saving. |
| `BDS_EVIDENCE_REQUIRED` | **Add the required supporting evidence.** Link the published requirement. |
| `BDS_EVIDENCE_REJECTED` | **This file could not be accepted.** Show type/size/scan reason without internal details. |
| `BDS_SECURITY_PROOF_REQUIRED` | **Add the required tender-security proof.** |
| `BDS_SECURITY_ORIGINAL_OUTSTANDING` | **The physical tender-security original has not been recorded as received.** This warns but does not falsely block electronic receipt. |
| `BDS_MUST_FIX` | **Fix the listed items before submitting.** Link every issue. |
| `BDS_STALE_VERSION` | **Another person changed this bid. Reload before continuing.** |
| `BDS_SIGNATORY_REQUIRED` | **Only an active Authorised Signatory can submit this bid.** |
| `BDS_SIGNATORY_CERTIFICATE_REQUIRED` | **A valid digital signature certificate is required before you can submit.** Keep the Draft; show **Check certificate** for the signatory after obtaining one from an approved licensed certifying agency. |
| `BDS_SIGNATURE_UNAVAILABLE` | **Digital signing is temporarily unavailable. Your bid remains saved and has not been submitted.** This is an enabled trust-service failure, not a missing bidder certificate. Show deadline and approved support route. |
| `BDS_SIGNATURE_INVALID` | **The digital signature could not be verified for this bid.** Nothing is submitted. |
| `BDS_PRODUCTION_SUBMISSION_NOT_ENABLED` | **Electronic bid submission is not available yet. Your bid remains saved and has not been submitted.** Show the exact deadline and configured supplier support contact; do not promise an enablement time or offer a retry. |
| `BDS_SUBMISSION_SERVICE_UNAVAILABLE` | **Electronic submission is temporarily unavailable. Your bid remains saved.** Never imply receipt. |
| `BDS_CUSTODY_REJECTED` | **The tender box rejected this attempt. Your bid remains saved and was not submitted.** Show the safe rejection reference; offer **Try confirmation again** only when the server has definitively established no acceptance, permits another attempt and the deadline remains open. |
| `BDS_SUBMISSION_UNCERTAIN` | **Submission confirmation is still pending. Do not submit again.** Show correlation/support route; no receipt or success claim. |
| `BDS_DEADLINE_PASSED` | **The submission deadline has passed. This bid was not submitted.** Show authoritative deadline/time. |
| `BDS_ALREADY_SUBMITTED` | **This bid Version has already been submitted.** Show its receipt. |
| `BDS_REPLACEMENT_CONFLICT` | **A newer submitted bid already exists.** Show current receipt; do not change either Version. |
| `BDS_WITHDRAWAL_BLOCKED` | **This bid can no longer be withdrawn because the deadline has passed.** |
| `BDS_IDEMPOTENCY_CONFLICT` | **This request was already used with different information. Stop and refresh.** |

BDS-CHG-001 §8 closing rule, verbatim: "Record-existence masking prevents cross-organisation disclosure. A public not-found response never confirms whether another supplier has a Draft or submission."

## Where each code is raised (plan proposal, new content)

| Code | Plan phase and service |
|---|---|
| `BDS_TENDER_NOT_FOUND` | 5 (reads), 11.1–11.2 |
| `BDS_TENDER_NOT_OPEN` | 5 (Start bid guard) |
| `BDS_SIGN_IN_REQUIRED` | 2C (portal resolver) |
| `BDS_ACCOUNT_REQUIRED` | 5 (Start bid guard) |
| `BDS_ACCOUNT_SUSPENDED` | 4 (Account), 5 (every bid command) |
| `BDS_ARRANGEMENT_INVALID` | 5 (Start bid) |
| `BDS_NOTICE_CONTACT_REQUIRED` | 5 (Start bid, notice contact) |
| `BDS_RESPONSIBILITY_REQUIRED` | 4, 8, 9 |
| `BDS_DEFINITION_UNSUPPORTED` | 5 (definition runtime) |
| `BDS_ADDENDUM_REVIEW_REQUIRED` | 6 (addendum) |
| `BDS_CLARIFICATION_DEADLINE_PASSED` | 5 (clarification) |
| `BDS_CLARIFICATION_NOT_REGISTERED` | 5 (clarification) |
| `BDS_PORTAL_INFORMATION_UNAVAILABLE` | 2A (projection), 5 (Start bid), 8 (submission) |
| `BDS_FIELD_INVALID` | 4, 6 |
| `BDS_UNKNOWN_RESPONSE` | 6 (save) |
| `BDS_EVIDENCE_REQUIRED` | 6 (validation) |
| `BDS_EVIDENCE_REJECTED` | 6 (evidence) |
| `BDS_SECURITY_PROOF_REQUIRED` | 7 (security) |
| `BDS_SECURITY_ORIGINAL_OUTSTANDING` | 7 (Review note only) |
| `BDS_MUST_FIX` | 6 (validation), 8 |
| `BDS_STALE_VERSION` | 4–9 (envelope) |
| `BDS_SIGNATORY_REQUIRED` | 8, 9 |
| `BDS_SIGNATORY_CERTIFICATE_REQUIRED` | 8 (signature) |
| `BDS_SIGNATURE_UNAVAILABLE` | 8 (availability) |
| `BDS_SIGNATURE_INVALID` | 8 (signature) |
| `BDS_PRODUCTION_SUBMISSION_NOT_ENABLED` | 8 (availability) |
| `BDS_SUBMISSION_SERVICE_UNAVAILABLE` | 8 (availability) |
| `BDS_CUSTODY_REJECTED` | 8 (submission) |
| `BDS_SUBMISSION_UNCERTAIN` | 8 (submission) |
| `BDS_DEADLINE_PASSED` | 5–9 (deadline guard) |
| `BDS_ALREADY_SUBMITTED` | 8 |
| `BDS_REPLACEMENT_CONFLICT` | 9 (replacement) |
| `BDS_WITHDRAWAL_BLOCKED` | 9 (withdrawal) |
| `BDS_IDEMPOTENCY_CONFLICT` | 4–9 (envelope) |
