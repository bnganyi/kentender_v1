<!--
  Evidence for Rectification Tracker §13 — R8-011 / LV-R8-UI-06
-->
## Goal

Close **PLC-SMOKE-UI-006 / R8-011**: the **TM2 Tender** Desk form for **`TND-MOH-2026-001`** must show **`plc-module-journey-context-header`** (mounted under **`tm2-tender-module-journey-context`**) so users see **District Hospital Renovation Works** journey context (**`JRN-MOH-2026-001`**), aligned with pack §15.2 — building on **R5-010**.

## What was verified

| Check | Detail |
|--------|--------|
| Host | **`data-testid="tm2-tender-module-journey-context"`** visible. |
| Selector | **`data-testid="plc-module-journey-context-header`** card visible (**pack §15.2**). |
| Title | **`plc-module-journey-context-title`** — **District Hospital Renovation Works**. |
| Codes | **`plc-module-journey-context-code`** — **JRN-MOH-2026-001**; **`plc-module-journey-context-entity`** — **PE-MOH**. |
| Stage | **`plc-module-journey-context-stage`** includes **Tender Published** (**TENDER_PUBLISHED** baseline). |
| Action | **Open journey** control (**`plc-module-journey-context-open`**) visible. |

## Evidence (Playwright)

```bash
npx playwright test tests/ui/smoke/procurement/tm2_module_journey_plc_smoke_ui_006_r8_011.spec.ts
```

**Last run (2026-05-16, local):** `1 passed (3.5s)` — `tm2_module_journey_plc_smoke_ui_006_r8_011.spec.ts`.

## Related references

- **PLC-SMOKE-UI-006** — cursor pack §15.2.
- **R5-001**, **R5-010**, **`tm2_tender_journey_context_r5_010.spec.ts`**, **`module_journey_context_header.js`**.
