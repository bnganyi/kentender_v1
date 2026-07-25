# Bidder Workspace (electronic bid submission)

## Goal

Bidders discover published tenders on a **public Website** landing page, open the Published Tender Overview, then prepare and submit bids electronically via a **Website Submission Checklist** workspace. Officers keep Tender Management / Publications / Bid Submissions on Desk Procurement.

## Binding sources

| Artifact | Role |
|---|---|
| [`Bidder_Workspace_Electronic_Bid_Submission_v1.md`](Bidder_Workspace_Electronic_Bid_Submission_v1.md) | Product + API contract |
| [`A0-bidder-landing-page/`](A0-bidder-landing-page/) | Available Tenders public landing |
| [`A1-published-tender-overview/`](A1-published-tender-overview/) | Published Tender Overview |
| [`A2-submission-checklist/`](A2-submission-checklist/) | Submission Checklist (workspace home) |
| [`A3-documents-and-addenda/`](A3-documents-and-addenda/) | Tender Documents & Addenda (Screen C) |
| [`A4-requirements/`](A4-requirements/) | Requirement Matrix (Screen D for `requirement_matrix`) |
| [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md) | Implementation status |

## Presentation boundary (permanent)

Bidder-facing screens and APIs must expose only information needed to understand or complete a bidder task. Internal hashes, digests, schema names, manifest identifiers, configuration references, database IDs, artifact types and audit metadata must never appear in bidder-visible HTML, API DTOs, accessibility text, tooltips, filenames or error messages.

Implementation: explicit allowlist projections in `kentender_procurement.tender_configurations.services.bidder_presentation` (and callers such as A3 `tender_documents_addenda`). Integrity hashes remain on the server for acknowledgement binding, audit and addendum invalidation.

## Architecture split

| Surface | Host | Route |
|---|---|---|
| **A0 Available Tenders** | Website (not Desk) | `/tenders` |
| Desk **Tenders** icon | Desktop Icon → External `/tenders` | Desk home launch shortcut |
| **A1 Published Tender Overview (bidder)** | Website portal | `/tenders/<publication_ref>` |
| **A1 Desk overview (officer/admin)** | Desk CL page | `/desk/published-tender-overview/<publication_ref>` |
| **A2 Submission Checklist (bidder)** | Website portal | `/tenders/<publication_ref>/workspace` |
| **A3 Tender Documents & Addenda (bidder)** | Website portal | `/tenders/<publication_ref>/documents` |
| **A4 Requirement Matrix (bidder)** | Website portal | `/tenders/<publication_ref>/sections/<section_key>` |
| Section editor bridge (temporary, non-matrix) | Desk E1 PoC | `/desk/it-electronic-bidder-workspace/<configuration_id>` |
| Officer Bid Submissions | Desk stub | `/desk/bid-submissions` |

Public top nav on A0–A4 Website: KenTender · Tenders · My Bids · Clarifications · Account  
A2–A4 share a **contextual left bid sidebar** (Checklist; Prepare Bid → documents; Review / Submit placeholders). No permanent “Requirement Matrix” nav item — matrix opens from checklist.  
Do **not** show officer modules on the bidder portal. Do **not** show Start Bid on A0 (Start Bid is on A1 Website overview only).  
**A0 primary** is always **View Tender** → overview (even when a draft exists), so addenda/Q&A stay reachable. **Continue Bid** on A0 is secondary only.  
**Start/Continue Bid** on A1 → Website `/tenders/<ref>/workspace`. **Prepare Bid** → Website `/tenders/<ref>/documents`. Matrix checklist rows → `/tenders/<ref>/sections/<section_key>`.

## Gates

```bash
make -C apps/kentender_v1 bw-a0-domain-gate
make -C apps/kentender_v1 ui-bidder-a0-gate
make -C apps/kentender_v1 bw-domain-gate
make -C apps/kentender_v1 ui-bidder-a1-gate
make -C apps/kentender_v1 bw-a2-domain-gate
make -C apps/kentender_v1 ui-bidder-a2-gate
make -C apps/kentender_v1 bw-a3-domain-gate
make -C apps/kentender_v1 ui-bidder-a3-gate
make -C apps/kentender_v1 bw-a4-domain-gate
make -C apps/kentender_v1 ui-bidder-a4-gate
```
