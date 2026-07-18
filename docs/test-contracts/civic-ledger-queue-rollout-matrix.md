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
| CFG-* / WF-* | — | pending (must reuse `configurationContextStrip`) |

## Required pattern gates

```bash
make -C apps/kentender_v1 ui-civic-ledger-queue-gate
make -C apps/kentender_v1 ui-civic-ledger-ui01-gate
```

Run before marking Civic Ledger queue/list or UI-01 home UX work done.

## Adoption steps for a new CL queue page

1. Register the surface in `kt_cl_surface_registry.js`.
2. Compose with `filterBar` / `bindFilterBar` / `queueTable` (no parallel markup).
3. Add or extend a contract spec that calls `ktClQueueContract` helpers.
4. List the spec in `ui-civic-ledger-queue-gate` in `apps/kentender_v1/Makefile`.
5. Update this matrix row to **locked**.
6. Keep module smoke green; after CL CSS/JS edits: touch `kentender_core/hooks.py` + `bench --site kentender.midas.com clear-cache`.
