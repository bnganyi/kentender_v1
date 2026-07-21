# Civic Ledger Queue Pattern Rollout Matrix

## Goal

Prevent repeated UI regressions on IT STD Wizard / Civic Ledger queue and list pages by enforcing a shared contract (chrome, filter bar, queue table footer) without re-specifying it per ticket.

## Contract scope

- Native-sidebar shell via `kt_cl_shell.enterNative` + surface registry
- Toolbar: context trail only; no search; user meta cluster
- Page header: leaf H1 + subtitle + actions; no breadcrumb row under strip
- Filter bar: `|` separator, outline-variant borders, search fills leftover space, `bindFilterBar`
- Queue table via `queueTable` only
- Footer: **Rows per page** left of pager; `page_size` wired

Binding prose: [`docs/std-prod-impl/IT-STD-Wizard-v3/B-Components/COMPONENTS.md`](../std-prod-impl/IT-STD-Wizard-v3/B-Components/COMPONENTS.md)  
Cursor rule: `.cursor/rules/kentender-civic-ledger-queue-lock.mdc`  
Helpers: `tests/ui/helpers/ktClQueueContract.ts`

## Rollout status

| Surface | Spec | Status |
|---------|------|--------|
| UI-00 Tender Configurations Dashboard | `tests/ui/smoke/it-std-wizard/kt-cl-queue-pattern-lock.spec.ts` | locked |
| UI-01 Tender Configuration Home | `ui01-layout-contract.spec.ts` + `ui01-home.spec.ts` + `ui01-mockup-states.spec.ts` (`ktClUi01LayoutContract.ts`, 8-cell strip) | locked (structural gate) |
| CFG-01 Tender Profile | `cfg01-tender-profile.spec.ts` (8-cell strip + `kt-cl-cfg01-*` layout) | locked (first CFG page) |
| CFG-02 Tender Data Sheet | `cfg02-tender-data-sheet.spec.ts` (8-cell strip + `kt-cl-cfg02-*` 8/4 layout) | locked |
| CFG-03 IT Requirements | `cfg03-it-requirements.spec.ts` (strip + table/drawer + sticky guidance; column-clarity: Delivery Confirmation Method + Setup Status) | locked |
| CFG-04 Implementation Schedule | `cfg04-implementation-schedule.spec.ts` (approach toggle + table/drawer/single form; column-clarity: Acceptance Method + Setup Status; drawer persist) | locked |
| CFG-05 System Inventory & Bidder Background | `cfg05-system-inventory.spec.ts` (banner + filters + table/drawer; column-clarity: Setup Status; INV/BG ids; drawer persist) | locked |
| CFG-06 Price Schedule | `cfg06-price-schedule.spec.ts` (tabs + Import + table/drawer; column-clarity: Setup Status; PRI ids; drawer persist) | locked |
| CFG-07 Evaluation Setup | `cfg07-evaluation-setup.spec.ts` (tabs + Import + table/drawer; Status Complete/Needs attention; EVAL ids; scoring summary; drawer persist) | locked |
| CFG-08 Forms & Evidence | `cfg08-forms-and-evidence.spec.ts` (filters + table/drawer + guidance; FE ids; Import Standard Forms; Continue to Contract Values) | locked |
| CFG-09 Contract Values | `cfg09-contract-values.spec.ts` (tabs + table/drawer + guidance; CV ids; Save + Run Check; no Continue) | locked |
| WF-01 Readiness Check & Report | `wg01-readiness.spec.ts` (summary cards + findings + checklist; Submit for Review) | locked |
| WF-02 Review & Approval | `wg02-review.spec.ts` (checklist + decision panel; Approve for Document Preview) | locked |
| WF-03 Tender Document Preview | `wg03-document-preview.spec.ts` (outline + preview; document artifact path under Package Review) | locked (document path) |
| WF-04 Publication Handoff | — | retired (no Send step; Confirm Package auto-opens Publication Setup) |
| PUB-A1 Electronic Tender Package Review | `tests/ui/smoke/publications/a1-package-review.spec.ts` | locked (functional) |
| PUB-A2 Publications Queue | `tests/ui/smoke/publications/a2-publications-queue.spec.ts` (+ queue gate) | locked (functional) |
| PUB-A3 Publication Setup | `tests/ui/smoke/publications/a3-publication-setup.spec.ts` | locked (functional) |

## Required pattern gates

```bash
make -C apps/kentender_v1 ui-civic-ledger-queue-gate
make -C apps/kentender_v1 ui-civic-ledger-ui01-gate
make -C apps/kentender_v1 ui-civic-ledger-cfg01-gate
make -C apps/kentender_v1 ui-civic-ledger-cfg02-gate
make -C apps/kentender_v1 ui-civic-ledger-cfg03-gate
make -C apps/kentender_v1 ui-civic-ledger-cfg04-gate
make -C apps/kentender_v1 ui-civic-ledger-cfg05-gate
make -C apps/kentender_v1 ui-civic-ledger-cfg06-gate
make -C apps/kentender_v1 ui-civic-ledger-cfg07-gate
make -C apps/kentender_v1 ui-civic-ledger-cfg08-gate
make -C apps/kentender_v1 ui-civic-ledger-cfg09-gate
make -C apps/kentender_v1 ui-civic-ledger-wg01-gate
make -C apps/kentender_v1 ui-civic-ledger-wg02-gate
make -C apps/kentender_v1 ui-civic-ledger-wg03-gate
make -C apps/kentender_v1 ui-publications-gate
```

Run before marking Civic Ledger queue/list, UI-01 home, CFG-01…CFG-09, WF-01…WF-03, or Publications A1–A3 UX work done.

## Adoption steps for a new CL queue page

1. Register the surface in `kt_cl_surface_registry.js`.
2. Compose with `filterBar` / `bindFilterBar` / `queueTable` (no parallel markup).
3. Add or extend a contract spec that calls `ktClQueueContract` helpers.
4. List the spec in `ui-civic-ledger-queue-gate` in `apps/kentender_v1/Makefile`.
5. Update this matrix row to **locked**.
6. Keep module smoke green; after CL CSS/JS edits: touch `kentender_core/hooks.py` + `bench --site kentender.midas.com clear-cache`.
