<!--
  Evidence for Rectification Tracker §13 — R8-007 / LV-R8-UI-02
-->
## Goal

Close **PLC-SMOKE-UI-002 / R8-007**: the **Procurement Journey** Desk page (**`plc-procurement-journey`**) exposes **`plc-journey-page`** and the pack **spine pillar** hooks (**`plc-journey-step-strategy`** … **`plc-journey-step-opening`**) such that **all §15 lifecycle rows render with visible status categories** at the WORKS **`TENDER_PUBLISHED`** baseline.

Functional coverage builds on **R4-007** (`expectWorksJourneyTimelineSpine`); R8 adds an explicit **PLC-SMOKE-UI-002** Playwright gate and tracker evidence.

## What was verified

| Check | Detail |
|--------|--------|
| Page shell | **`data-testid="plc-journey-page"`** visible; journey route + header load (**`expectProcurementJourneyPageShell`**). |
| Timeline | Twelve nodes, **`step_key`** order §15 (**R4-007**). |
| Pillars §15.2 | At least one **`.plc-journey-step-pill`** with each of **strategy / budget / demand / planning / std-readiness / tender / opening** pillar classes (**`PLC_SMOKE_UI_002_SPINE_PILLAR_CLASSES`**). |
| Status copy | Each pack pillar pill has non-empty **`.plc-journey-step-status`**; first seven rows **done-like** class, remainder **not-started** (**R4-007**). |

## Evidence (Playwright)

From **`apps/kentender_v1/`**:

```bash
npx playwright test tests/ui/smoke/procurement/procurement_journey_spine_plc_smoke_ui_002_r8_007.spec.ts
```

**Last run (2026-05-16, local):** `1 passed (5.3s)` — `procurement_journey_spine_plc_smoke_ui_002_r8_007.spec.ts`.

## Related references

- **PLC-SMOKE-UI-002** — cursor pack §15.2.
- **R4-007 / LV-R4-007-01** — timeline implementation + **`procurement_journey_timeline_r4_007.spec.ts`**.
