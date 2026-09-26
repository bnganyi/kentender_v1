# BDS-CHG-001 v0.8: hand-off register

| Control | Value |
|---|---|
| Version | 0.8-phase0.1 |
| Status | Phase 0 working document (plan BDS-CHG-001 v0.8) |
| Source | BDS-CHG-001 §5.14, lines 660–676, copied verbatim below (extracted 26 Sep 2026). |
| Rule | KT-STD-001 v1.9 §3B.4: items clear only on the stated state change, never on "mark as read". KT-STD-001 v1.9 §6 requires a create-and-clear test for every row. |
| New content | The "Implementation" table is a plan proposal (implementation plan D15, OD-D). Its doctype names are new. |

## Spec §5.14 (verbatim)

Each row clears from the underlying event, not a notification read. Technical/configuration/release queues are governed operational queues, not Administrator or System Manager business My Work; their `next_step` never gives a supplier business action under KT-STD-001 §3B.6. Support incidents contain a safe correlation and no bid responses, evidence, price or sealed content. The named test holders below are fixture assignments; production resolves the current responsible person.

| Event | Next holder | Their My Work item | Sender waiting item | Notification | Clears when |
|---|---|---|---|---|---|
| Account challenge issued | Registering Account owner | **Verify supplier account email** | None | Yes, Account owner | Challenge verified or superseded/expired. |
| Account access suspended | Supplier Account support officer Amina Yusuf | **Review suspended supplier account access** | Assigned supplier users: **Waiting for Account support** | Yes, Amina | Governed Account access is restored or final decision recorded; no self-activation. |
| Draft becomes Ready to submit | Authorised Signatory Mary Wanjiku | **Review and submit BID-MOH-2027-033-001** | David Ouma: **Waiting for Mary Wanjiku to submit BID-MOH-2027-033-001** | Yes, Mary | Submitted, changed back to Needs attention, withdrawn or deadline closes. |
| Effective addendum makes Draft need review | Supplier preparer David Ouma | **Review ADD-MOH-2027-033-001 for BID-MOH-2027-033-001** | Mary: **Waiting for David Ouma to review the addendum** if a prior ready item existed | Yes, David | Acknowledgement and affected responses complete, or submission deadline closes. |
| Public portal information becomes incomplete | CFG System Manager Daniel Otieno | None in supplier My Work; controlled CFG configuration queue | Affected signatory: **Waiting for supplier portal information** | Governed CFG incident to Daniel; no supplier notice | CFG active projection is complete and validated. |
| Production gate remains disabled when a bid is ready | Release operator Nadia Kamau | None in supplier My Work; controlled deployment release queue | Signatory: **Waiting for production submission availability** | Yes, Nadia | Approved operating profile and healthy dependencies permit enablement, or deadline closes. |
| Enabled submission service fails | Technical operator Daniel Otieno | None in supplier My Work; technical incident queue with non-content reference | Mary: **Waiting for electronic submission recovery** | Yes, Daniel | Service health restored or deadline closes; no success inference. |
| Submission result uncertain | Technical operator Daniel Otieno | None in supplier My Work; technical reconciliation queue for COR-BDS-2027-033-01 | Mary: **Waiting for the result of this submission attempt** | Yes, Daniel | Same correlation resolves accepted or definitively failed. |

No item asks a supplier to obtain a template approval or contact an officer outside the product to progress an internal guard. The public footer remains available for human support, including accessibility and deadline concerns.

## Implementation (plan proposal)

| Event (spec) | Record and surface | Created by | Cleared by | Notification |
|---|---|---|---|---|
| Account challenge issued | `Supplier Account Task` (ACC) | `SendAccountVerification` commit | `VerifyAccountCommunication` success, or a newer challenge / expiry | Supplier transport (hook `kt_supplier_account_message_transports`); portal Account next step |
| Account access suspended | `Supplier Account Task` (ACC) → Desk My Work for Amina Yusuf; waiting rows for assigned supplier users | `SuspendSupplierAccountAccess` (owner decision OD-D) | `RestoreSupplierAccountAccess` or a recorded final decision (OD-D) | Frappe Notification Log to Amina |
| Draft becomes Ready to submit | `Bid Hand-off` (BDS) holder Mary; waiting row for David | Readiness derivation after a Draft mutation | Submitted, back to Needs attention, withdrawn, or close | Supplier transport; portal My bids row action and next step (plan D15) |
| Effective addendum makes Draft need review | `Bid Hand-off` (BDS) holder David; waiting row for Mary when a ready item existed | Consumer of the Tenders addendum-effective event | Acknowledgement plus affected responses complete, or close | Supplier transport |
| Public portal information becomes incomplete | `Bid Submission Incident` (operational CFG queue), holder Daniel Otieno; waiting row for the affected signatory | `get_public_portal_information()` returns Incomplete at a guarded command | Projection Complete again | Notification Log to Daniel; no supplier notice |
| Production gate remains disabled when a bid is ready | `Bid Submission Incident` (deployment release queue), holder Nadia Kamau; waiting row for the signatory | Availability check returns `BDS_PRODUCTION_SUBMISSION_NOT_ENABLED` for a Ready Draft | Availability passes, or close | Notification Log to Nadia |
| Enabled submission service fails | `Bid Submission Incident` (technical incident queue), holder Daniel Otieno; waiting row for Mary | Availability returns `BDS_SIGNATURE_UNAVAILABLE` or `BDS_SUBMISSION_SERVICE_UNAVAILABLE` | Health restored, or close | Notification Log to Daniel |
| Submission result uncertain | `Bid Submission Incident` (reconciliation queue) for the correlation; waiting row for Mary | `SubmitBid` phase 3 records Uncertain | Same correlation resolved Accepted or Rejected | Notification Log to Daniel |

Supplier-side items (Mary, David) cannot appear in Desk My Work: suppliers are Website Users. Plan D15 surfaces them in the portal. This is a spec follow-up (FU-V08-07).
