# IT Tender Wizard — Screen Ownership Implementation Tracker

**Governing contract:** [`99 IT_Tender_Wizard_Screen_Ownership_Matrix.md`](99%20IT_Tender_Wizard_Screen_Ownership_Matrix.md)  
**Correction plan:** [`98 IT_Tender_Wizard_Screen_Ownership_Correction_Plan.md`](98%20IT_Tender_Wizard_Screen_Ownership_Correction_Plan.md)  
**UI wiring tracker:** [`UI_IMPLEMENTATION_TRACKER.md`](UI_IMPLEMENTATION_TRACKER.md)

## Goal

Enforce one primary object per screen, source-backed references, and no magical values across ITW-01–15. Close residual defects on wired screens and hard-gate future wiring.

Done looks like: every `ITW-OWN-*` row below has status Done with automated test evidence; `make it-wizard-ownership-gate` is green; ITW-08+ wiring cannot start without a Ready ownership precondition row.

**Deep ownership pass (2026-07-15):** purged magical fixtures from all 15 design+deploy HTML pairs; inventory Security summary uses real inventory fields only; Profile TDS-owned fields are static RO + Edit-in-TDS; hydration errors no longer reveal fixture `main`; cross-screen forbidden patterns enforced in ownership unit tests.

## Precedence decision log

| Date | Decision | Evidence |
|---|---|---|
| 2026-07-15 | Matrix `99` is the correction layer for field ownership / editability / source presentation over PRD, Domain, API, Governance, Pack, Sprint backlog, and design HTML | Pack §2.1 updated; Cursor rule `kentender-it-wizard-screen-ownership.mdc`; this tracker |

## Status legend

| Status | Meaning |
|---|---|
| Pending | Not started |
| In progress | Active work |
| Partial | Implemented without full DoD / gate evidence |
| Ready | Precondition checklist filled; waiting on wiring stage |
| Done | Tests + UX evidence recorded |

## Phase A — Contract freeze and prevention

| ID | Work | Status | Evidence |
|---|---|---|---|
| ITW-OWN-000 | Adopt Matrix precedence; plan + tracker + Pack §2.1 + Cursor rule | Done | `98` plan; this tracker; Pack §2.1; `.cursor/rules/kentender-it-wizard-screen-ownership.mdc` — 2026-07-15 |
| ITW-OWN-GATE-01 | Shared ownership contract helpers (Python + TS) | Done | Cross-screen forbidden patterns + inventory honest-field hooks; TS helper — 2026-07-15 deep pass |
| ITW-OWN-GATE-02 | `make it-wizard-ownership-gate` | Done | Ownership unit (8) + all 15 LGs + PW ownership contract green — 2026-07-15 deep pass |

## Phase B — Correct already-wired screens

| ID | Screen | Owns (Matrix) | Must not own | Residual work | Status | Evidence |
|---|---|---|---|---|---|---|
| ITW-OWN-007 | System Inventory | Inventory item, category, scope, required action, bidder context, disclosure | Full pricing, evaluated-price, scoring | Honest category cards (no Access Logic/Data Residency fake KPIs); Edit opens item drawer | Done | Security shows title/classification/required_action/bidder_consideration only; Edit creates when empty — 2026-07-15 deep pass |
| ITW-OWN-003 | Tender Profile | Title/summary, lots, participation | TDS security/contact detail, requirements, pricing | Static RO + Source + Edit-in-TDS; collect skips all TDS-owned keys | Done | HTML baked owned-elsewhere; language/currency skipped on save — 2026-07-15 deep pass |
| ITW-OWN-006 | Implementation Schedule | Phases/milestones, duration, triggers, deliverables, acceptance, evidence | Live execution, payment certification | Turnkey Source + Edit + Reset parity; hide unwired Standard Template apply | Done | Turnkey reset actions in HTML/JS; template button hidden with title — 2026-07-15 |
| ITW-OWN-005 | IT Requirements | Requirement text, treatment, bidder evidence instruction, acceptance criteria | Score marks, %, evaluation results | Never surface raw `SCORED` | Done | `requirements_treatment_display_label` maps SCORED→Evaluation-linked — 2026-07-15 deep pass |
| ITW-OWN-001 | Dashboard | Queue / KPI navigation only | Configuration editing | Empty KPI/table hosts; hydrate-only; error path withholds fixtures | Done | Fixture KPIs purged; hydration error keeps main hidden — 2026-07-15 deep pass |
| ITW-OWN-002 | Overview | Step navigation / summary | Configuration editing | Empty context hosts; hydrate-only | Done | Fixture title/%/last-run purged — 2026-07-15 deep pass |
| ITW-OWN-004 | TDS | Tender-specific TDS values | Requirements, price lines, scoring | Empty inputs; no invented `ELECTRONIC_ONLY` | Done | Hydrate uses blank envelope_marking when unset — 2026-07-15 deep pass |

## Phase C — Pack/doc realignment

| ID | Work | Status | Evidence |
|---|---|---|---|
| ITW-OWN-DOC-01 | PRD §13.8 / §13.11 cite Matrix | Done | Ownership Matrix override callouts in PRD — 2026-07-15 |
| ITW-OWN-DOC-02 | Domain note: qty/unit/evaluated-price → Price Schedule; marks → Evaluation | Done | Domain §8.23 override callout — 2026-07-15 |
| ITW-OWN-DOC-03 | API §10.6 realigned | Done | API §10.6 override callout — 2026-07-15 |
| ITW-OWN-DOC-04 | Governance ITINV/ITREQ rules realigned | Done | Governance §14.1 / §14.3 override callouts — 2026-07-15 |
| ITW-OWN-DOC-05 | Sprint backlog S5 inventory AC footnotes Matrix override | Done | S5-006 / S5-007 footnotes — 2026-07-15 |

## Phase D — Downstream screens (ITW-08–15)

Historical gate note: **Blocks ITW-08 wiring** until Ready + ownership gate green. As of 2026-07-16 Desk wiring is complete; keep ownership gate green for regressions.

| ID | Screen | Owns | Must not own | Design audit | Gate | Status | Evidence |
|---|---|---|---|---|---|---|---|
| ITW-OWN-008 | Price Schedule | Pricing basis, qty/unit, tax, evaluated-price inclusion | Requirement wording, inventory context, scoring | Fixture purge done | Downstream | Done | DocTypes/service/API/desk/`it_wizard_downstream.js`; PW downstream 9/9; `make it-wizard-downstream-gate` — 2026-07-16 |
| ITW-OWN-009 | Evaluation Setup | Stages, scored criteria, weights, pass marks, financial basis | Requirement text, bidder submissions, award | Fixture purge done | Downstream | Done | Wired via evaluation setup service + hydrator — 2026-07-16 |
| ITW-OWN-010 | Forms & Evidence | Submission items, formats, mandatory rules | Actual uploads, verification, scores | Fixture purge done | Downstream | Done | Wired via forms evidence service + hydrator — 2026-07-16 |
| ITW-OWN-011 | SCC / Carry-Forward | SCC values, carry-forward, obligation text | Signing, payment certification, inspection | Fixture purge done | Downstream | Done | Wired via SCC service + hydrator — 2026-07-16 |
| ITW-OWN-012 | Validation Report | Findings only | Fixing configuration fields | Findings host emptied | Downstream | Done | Findings deep-link to owner screens; run validation save — 2026-07-16 |
| ITW-OWN-013 | Review & Approval | Review decisions/comments/returns | Configuration edit, publication | Fixture purge done | Downstream | Done | Review decisions hydrate/save — 2026-07-16 |
| ITW-OWN-014 | Final Tender Preview | Preview confirmation only | Content edit, publication | Fixture purge done | Downstream | Done | Checklist confirmation only — 2026-07-16 |
| ITW-OWN-015 | Publication Readiness | Readiness confirmation / handoff | Publish Tender, bidder notification | Fixture purge done | Downstream | Done | Mark as Publication Ready (no Publish Tender) — 2026-07-16 |

### Precondition checklist (met)

- [x] Owns / Must-not-own filled from Matrix
- [x] Design `code.html` audited (no magical values; no cross-owned editors)
- [x] Static ownership assertions added to ownership gate
- [x] Field-source metadata planned for DTO/UI
- [x] Edit-in-owner links planned for references

## Gate commands

```bash
make it-wizard-ownership-gate SITE=kentender.midas.com
make it-wizard-downstream-gate SITE=kentender.midas.com
```
