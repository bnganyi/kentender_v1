# Price Schedule — Implementation Report

## Goal

Ship a complete electronic Price Schedule so bidders price published lines in-system (no spreadsheet/PDF), with server-authoritative Decimal totals flowing read-only into Form of Tender and checklist readiness. Done means: Stitch 01–04 Website UI matches the approved designs, pack validations/calculations/status rules pass automated tests, FoT consumes current PS totals without re-entry, and Playwright proves the happy path end-to-end.

## Scope delivered

| Area | Status |
|---|---|
| Lean fixtures (single_lot / multi_lot / multi_currency) + materialize/hydrate | Done |
| Server Decimal calc, validation, section status, blockers | Done |
| Bidder service + thin API whitelist (`price_schedule_bidder.py`) | Done |
| Website overview / schedule editor / review (Stitch 01–04) | Done |
| Checklist special-case + FoT projection/complete without PS discounts | Done |
| Layout guard + Makefile gates + Playwright smoke | Done |

## Architecture

- Domain: `kentender_procurement/tender_configurations/services/price_schedule_bidder.py` (separate from CFG-06 Desk `price_schedule.py`)
- Seed: `tender_configurations/seed/lean_price_schedule.py`
- Persistence: `Electronic Bid Submission.responses["price_schedule"]`
- Website: FoT/RC shell + `price_schedule_web.css` / `price_schedule_web.js`
- Routes (before catch-all section):
  - `/tenders/<ref>/sections/price_schedule`
  - `/tenders/<ref>/sections/price_schedule/schedules/<schedule_key>`
  - `/tenders/<ref>/sections/price_schedule/review`

## Fixtures

| Fixture | Behaviour |
|---|---|
| single_lot | Supply-only; no lot selector; CoO required on supply lines |
| multi_lot | Supply + recurrent; lot selector; period columns on recurrent |
| multi_currency | KES/USD permitted; alternative offers flag when configured |

## Evidence commands

```bash
bench --site kentender.midas.com clear-cache
cd apps/kentender_v1 && make bw-price-schedule-domain-gate
cd apps/kentender_v1 && make ui-bidder-price-schedule-gate
```

**Gate evidence (this delivery):** `bw-price-schedule-domain-gate` OK (17 domain + 5 layout-guard tests); `ui-bidder-price-schedule-gate` OK (1 Playwright smoke).

Manual spot-check: `http://127.0.0.1:8000/tenders/<ref>/sections/price_schedule` (seed via `publish_lean_price_schedule_for_tests`).

## Reused components

- TP multi-surface Website pattern + RC fixed footer / Complete → checklist
- Bidder portal nav + workspace sidebar
- FoT `is_price_schedule_complete` / `price_schedule_projection` / invalidate certifications
- Lean ui00 publish path for Playwright

## Explicitly deferred

- Evaluator analysis / bid comparison
- FX conversion
- Spreadsheet import / PDF generation
- New DocTypes
- CFG-06 Desk redesign
- NSSF-hardcoded UI
