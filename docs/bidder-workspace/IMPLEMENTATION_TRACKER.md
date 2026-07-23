# Bidder Workspace — Implementation Tracker

Precedence: A0 website landing + A1 **Website** overview + A2 **Website** checklist + A3 **Website** documents/addenda for bidders; Desk A1 for officers/admin. Civic Ledger for Desk overview only. E1 PoC electronic bid APIs reused for draft/seal; section editing bridges to Desk PoC until Screen D.

| ID | Item | Status | Evidence |
|---|---|---|---|
| BW-00 | Pack README + tracker + A1 rules digest | Done | `docs/bidder-workspace/` |
| BW-A1-01…04 | Published Tender Overview API + Desk page + gates | Done | `bw-domain-gate` / `ui-bidder-a1-gate` |
| BW-A1-WEB-01 | Website overview `/tenders/<publication_ref>` + portal nav | Done | `www/tenders/overview.py` + route rule |
| BW-A1-WEB-02 | View Tender retarget + Start Bid guest login | Done | `_overview_url` → `/tenders/…`; `published_tender_overview_web.js` |
| BW-A2-01 | Submission Checklist DTO + primary-action/status helpers | Done | `services/submission_checklist.py` + `test_submission_checklist_api` |
| BW-A2-02 | Website `/tenders/<ref>/workspace` + contextual sidebar | Done | `www/tenders/workspace.*` + `kt_bidder_workspace_sidebar.html` |
| BW-A2-03 | Start/Continue Bid retarget to Website workspace | Done | `bidder_workspace_route` → `/tenders/…/workspace` |
| BW-A2-04 | A2 Playwright + Makefile gates | Done | `ui-bidder-a2-gate` / `bw-a2-domain-gate` |
| BW-A3-01 | Documents & Addenda DTO + schema ack helpers | Done | `services/tender_documents_addenda.py` + `test_tender_documents_addenda_api` |
| BW-A3-02 | Website `/tenders/<ref>/documents` + Prepare Bid sidebar | Done | `www/tenders/documents.*` |
| BW-A3-03 | Acknowledge Tender Documents → electronic bid section | Done | `acknowledge_tender_documents` whitelist |
| BW-A3-04 | A3 Playwright + Makefile gates | Done | `ui-bidder-a3-gate` / `bw-a3-domain-gate` |
| BW-A0-01 | Available Tenders list service + public status mapping | Done | `test_available_tenders_api` |
| BW-A0-02 | Website `/tenders` Jinja landing (not Desk) | Done | `www/tenders/` |
| BW-A0-03 | Desk Desktop Icon **Tenders** → `/tenders` | Done | `desktop_icon/tenders.json` + after_migrate sync |
| BW-A0-04 | Officer Bid Submissions unlinked from A1 | Done | `bid-submissions` stub page |
| BW-A0-05 | A0 Playwright + Makefile gates | Done | `ui-bidder-a0-gate` (includes View Tender → portal) |

## A0 rules (landing)

| Source | Requirement |
|---|---|
| A0 arch | Website/Portal page, not Desk Page |
| A0 CTA | View Tender / Continue Bid / View Submitted Bid / View Notice — never Start Bid |
| A0 data | Published + bidder-visible only; default list excludes Closed/Cancelled |
| Desk icon | Launch shortcut to `/tenders` |

## A2 notes

- Checklist rows are schema-driven (compiled bidder submission schema).
- Section Open/Continue/Resolve temporarily bridges to Desk E1 PoC until Screen D (portal section editor), except **document_acknowledgement** → A3 `/documents`.
- Status logic: unstarted → **Not Started / Start**; partial → **In Progress / Resume**; validation failures only → **Needs Attention / Resolve**; final declaration **Locked** until other required sections complete.
- Display label: `contract_terms_acknowledgement` → **Contract Conditions Acknowledgement**.
- Review & Validate / Submit & Seal sidebar items remain placeholders.

## A3 notes

- Official documents are package-driven (confirmed tender PDF + package artifacts). No invented BoQ/DOCX rows.
- Official Addenda renders `addenda: []` empty state unless the published package already carries real addenda. No seeded fake addenda; no IT addendum DocType this slice.
- **Acknowledge Tender Documents** completes the schema `document_acknowledgement` / `tender_document_acknowledgement` section via electronic bid responses.
- Empty addenda must not block submission (`addenda_block_submission=false`). Future required addenda will block until each is acknowledged (helper ready; per-addendum API later).

## Gates (evidence 2026-07-23)

```bash
make -C apps/kentender_v1 bw-a0-domain-gate
make -C apps/kentender_v1 ui-bidder-a0-gate
make -C apps/kentender_v1 bw-a2-domain-gate
make -C apps/kentender_v1 ui-bidder-a2-gate
make -C apps/kentender_v1 bw-a3-domain-gate
make -C apps/kentender_v1 ui-bidder-a3-gate
make -C apps/kentender_v1 bw-domain-gate
make -C apps/kentender_v1 ui-bidder-a1-gate
```

## Out of scope / later

My Bids / Clarifications / Account website pages; Screen D portal section editor; IT addendum DocTypes / publication / per-addendum ack API; full Review & Validate / Submit & Seal portal UIs; removing Desk A1 / E1 PoC entirely; Company Profile.
