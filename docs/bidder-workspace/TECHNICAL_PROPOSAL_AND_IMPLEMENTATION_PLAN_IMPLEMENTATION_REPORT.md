# Technical Proposal and Implementation Plan — Implementation Report

## Goal

Ship the tender-stage **Preliminary Project Plan** so bidders can electronically complete configured Technical Proposal subsections, with server-derived status/issues and checklist readiness — without duplicating Qualification, Requirements Compliance, Lots, or Pricing.

## Scope delivered

| Area | Status |
|---|---|
| Config fixtures (Core / Full / Conditional) + template materialization | Done |
| Domain service get/save/confirm + work-plan validation | Done |
| Website overview (Stitch 01), subsection renderers (02–08 + warranty), review (09) | Done |
| Checklist roll-up + deep-link to first incomplete subsection | Done |
| Evidence link hooks (register select by title; ids stored, never hashes) | Done |
| Layout guard + Makefile gates + Playwright smoke | Done |

## Architecture

- Service: `kentender_procurement/tender_configurations/services/technical_proposal_and_implementation_plan.py`
- Persistence: electronic bid `responses.technical_proposal_and_implementation_plan` (no second submission model)
- Status/issues: server-derived on read/save (never bidder-editable)
- Website: CBQ/FoT shell + `technical_proposal_web.css/js` + Jinja includes under `templates/includes/technical_proposal/`
- Routes (before catch-all section):
  - `/tenders/<ref>/sections/technical_proposal_and_implementation_plan`
  - `.../<subsection_key>`
  - `.../review`

## Fixtures

| Fixture | Behaviour |
|---|---|
| Core | Required: org + integration confirmation only |
| Full | All candidate subsections applicable (PE-neutral topics) |
| Conditional | Optional training; excluded transition; conditional alternatives |

Named conditions only (`always`, `technical_alternatives_permitted`, `training_required_by_tds`, `warranty_support_required_by_tds`, `data_migration_in_requirements`, `lot_topic_selected`).

## Evidence commands

```bash
bench --site kentender.midas.com clear-cache
cd apps/kentender_v1 && make bw-technical-proposal-domain-gate
cd apps/kentender_v1 && make ui-bidder-technical-proposal-gate
```

## Explicit non-goals (unchanged)

- Generic document-management / form-builder
- Evaluator scores, pass/fail, PDF-as-primary response
- Final Agreed Project Plan (post-award)
- Duplicating Requirements matrix, CVs, prices, lot selection, seal
- NSSF-hardcoded topics as canonical fixtures

## Stitch fidelity pass (follow-up)

Aligned Website UI to Stitch `01`–`09` structure:

- Overview / review: Subsection Progress card (`%` + bar + N of M)
- Approach: topic guidance, per-topic status, supporting-material links, evidence block
- Work plan: Phase/Activity matrix with Dur/End/Status/Resolve + dependency labels + help cards
- Org: Manage Key Personnel deep-link
- Transition: handover deliverables checklist
- Testing / alternatives: Status column; alternatives Permitted Scope chips
- Review: Consolidated Summary KPI grid + integration confirmation

## Gaps / follow-ups

- Full evidence upload/replace remains on the shared evidence register page; Technical Approach links existing items only.
- Published snapshots created before the Stitch instruction-string update keep the prior `bidder_instructions` until republish.
