# Tender Publications — Implementation Tracker

Precedence: v7 workflow + A1–A3 mocks. Civic Ledger for Desk UI. F1 package immutability retained; Send-to-Publication as a primary step removed.

| ID | Item | Status | Evidence |
|---|---|---|---|
| PUB-00 | Pack README + this tracker + CL rollout matrix | Done | `docs/tender-publications/`, rollout matrix |
| PUB-01 | Publication Record statuses/fields (Ready/Scheduled/bidder_visibility/activate/ack) | Done | DocType + migrate |
| PUB-02 | `confirm_tender_package` auto-creates Publication Setup | Done | `test_generate_confirm_auto_opens_publication_setup` |
| PUB-03 | Package review summary API | Done | `test_package_review_summary_after_generate` |
| PUB-04 | list / get / save setup / publish / return APIs | Done | `test_publication_setup_api` (6) + `make pub-domain-gate` |
| PUB-05 | A1 Electronic Tender Package Review Desk page | Done | `a1-package-review.spec.ts` |
| PUB-06 | A2 Publications queue | Done | `a2-publications-queue.spec.ts` + CL queue gate includes A2 |
| PUB-07 | A3 Publication Setup + Publish | Done | `a3-publication-setup.spec.ts` |
| PUB-08 | Workspace nav + seeds + Makefile gates | Done | Sidebar Publications → page; `seed_publications_demo`; `make pub-domain-gate` / `ui-publications-gate` |
| PUB-09 | Remove Send-to-Publication primary UI/tests | Done | WG-03 Continue to Setup; send API thin shim only |

## State model (publication record)

`Awaiting Publication Setup` → `Ready to Publish` | `Scheduled` → `Published`  
Return path → `Returned` (config returned for correction; package invalidated)

## Gates (evidence 2026-07-21)

```bash
make -C apps/kentender_v1 pub-domain-gate   # 18 tests OK
make -C apps/kentender_v1 ui-publications-gate  # 3 passed
```

MCP Desk smoke: `/desk/publications` renders summary cards, tabs, filter bar (Administrator session).

## Out of scope / Partial

Full bidder Bid Submissions UI, evaluation/award, TM2 Works publication path.
Publish sets visibility + workspace activation flags for downstream (bidder portal UI not in this programme).
A1–A3 Desk layouts realigned to mocks (context strips, 8+4 A3 rail, A1 section chrome, A2 tab counts/STD chips/soft CTAs) with CSS pins in `kt_cl_code_layout.css`. Evidence: `make ui-publications-gate` (3/3) + MCP screenshots. Strict pixel-lock vs mock `code.html` remains Partial (CL pageHeader chrome + queueSummaryCard icon layout still diverge slightly from static HTML).
