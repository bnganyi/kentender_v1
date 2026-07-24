# Bidder Workspace — Implementation Tracker

Precedence: A0 website landing + A1 **Website** overview + A2 **Website** checklist + A3 **Website** documents/addenda + A4 **Website** requirement matrix for bidders; Desk A1 for officers/admin. Civic Ledger for Desk overview only. E1 PoC electronic bid APIs reused for draft/seal; non-matrix section editing still bridges to Desk PoC until other Screen D renderers ship.

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
| BW-A4-01 | Requirement Matrix DTO + merge-save + status helpers | Done | `services/requirement_matrix.py` + `test_requirement_matrix_api` |
| BW-A4-02 | Website `/tenders/<ref>/sections/<section_key>` | Done | `www/tenders/section.*` + CSS/JS |
| BW-A4-03 | Checklist matrix `action_url` + status roll-up | Done | `submission_checklist.py` portal section URLs |
| BW-A4-04 | A4 Playwright + Makefile gates | Done | `ui-bidder-a4-gate` / `bw-a4-domain-gate` |
| BW-A0-01 | Available Tenders list service + public status mapping | Done | `test_available_tenders_api` |
| BW-A0-02 | Website `/tenders` Jinja landing (not Desk) | Done | `www/tenders/` |
| BW-A0-03 | Desk Desktop Icon **Tenders** → `/tenders` | Done | `desktop_icon/tenders.json` + after_migrate sync |
| BW-A0-04 | Officer Bid Submissions unlinked from A1 | Done | `bid-submissions` stub page |
| BW-A0-05 | A0 Playwright + Makefile gates | Done | `ui-bidder-a0-gate` (includes View Tender → portal) |

## A0 rules (landing)

| Source | Requirement |
|---|---|
| A0 arch | Website/Portal page, not Desk Page |
| A0 CTA | Primary: View Tender (or View Submitted / View Notice) — never Start Bid; Continue Bid is secondary when a draft exists so overview stays the default notice path |
| A0 data | Published + bidder-visible only; default list excludes Closed/Cancelled |
| Desk icon | Launch shortcut to `/tenders` |

## A2 notes

- Checklist rows are schema-driven (compiled bidder submission schema).
- Section Open/Continue/Resolve: **requirement_matrix** → A4 portal section URL; **document_acknowledgement** → A3 `/documents`; other sections still bridge to Desk E1 PoC until their Screen D hosts ship.
- Status logic: unstarted → **Not Started / Start**; partial → **In Progress / Resume** (matrix uses **Continue**); validation failures only → **Needs Attention / Resolve**; final declaration **Locked** until other required sections complete.
- Display label: `contract_terms_acknowledgement` → **Contract Conditions Acknowledgement**.
- Review & Validate / Submit & Seal sidebar items remain placeholders.

## A4 notes

- Matrix detection is structural (`requirements` + `response_fields_per_requirement`) or `section_type=requirement_matrix` — not hardcoded to `technical_compliance_matrix` / ordinal 6 / NSSF group names.
- Groups are derived at read time from `category_label` (fallback `requirement_family` / General).
- Persistence remains `Electronic Bid Submission.responses[section_key][requirement_id]` via merge-save over `save_section_responses`.
- Portal drawer suppresses `reference_pages` (electronic-only). Evidence upload uses mock-compatible payload until §22.5 real upload.
- Other checklist section renderers (declarations, price schedule, etc.) remain out of scope.

## A3 notes

- Official documents are package-driven (confirmed tender PDF + package artifacts). No invented BoQ/DOCX rows.
- Official Addenda renders `addenda: []` empty state unless the published package already carries real addenda. No seeded fake addenda; no IT addendum DocType this slice.
- **Acknowledge Tender Documents** completes the schema `document_acknowledgement` / `tender_document_acknowledgement` section via electronic bid responses.
- Empty addenda must not block submission (`addenda_block_submission=false`). Future required addenda will block until each is acknowledged (helper ready; per-addendum API later).

## Gates (evidence 2026-07-24)

```bash
make -C apps/kentender_v1 bw-a0-domain-gate
make -C apps/kentender_v1 ui-bidder-a0-gate
make -C apps/kentender_v1 bw-a2-domain-gate
make -C apps/kentender_v1 ui-bidder-a2-gate
make -C apps/kentender_v1 bw-a3-domain-gate
make -C apps/kentender_v1 ui-bidder-a3-gate
make -C apps/kentender_v1 bw-a4-domain-gate
make -C apps/kentender_v1 ui-bidder-a4-gate
make -C apps/kentender_v1 bw-domain-gate
make -C apps/kentender_v1 ui-bidder-a1-gate
```

## Out of scope / later

My Bids / Clarifications / Account website pages; other Screen D section renderers (declarations, price schedule, etc.); IT addendum DocTypes / publication / per-addendum ack API; full Review & Validate / Submit & Seal portal UIs; removing Desk A1 / E1 PoC entirely; Company Profile.
