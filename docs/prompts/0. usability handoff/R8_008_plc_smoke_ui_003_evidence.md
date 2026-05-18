<!--
  Evidence for Rectification Tracker §13 — R8-008 / LV-R8-UI-03
-->
## Goal

Close **PLC-SMOKE-UI-003 / R8-008**: on **`/desk/plc-procurement-journey/JRN-MOH-2026-001`**, the **Planning Release Package** handoff (**`PKGREL-MOH-2026-001`**) appears as a **`plc-handoff-card`**, showing **source** and **target** lines, **passed-forward / evidence** preview copy, and a working **Technical details** control that opens the **technical evidence** drawer — per cursor pack §15.2.

## What was verified

| Check | Detail |
|--------|--------|
| Panel | **`plc-handoff-panel`** visible. |
| Card | **`[data-handoff-code="PKGREL-MOH-2026-001"]`** with **`data-testid="plc-handoff-card"`**. |
| Identity | Title **Planning Release Package**, status **Consumed**. |
| Route | **Procurement Planning** → **Tender Management**. |
| Source / target | **Procurement Package · PKG-MOH-2026-001**; **Target: TM2 Tender · TND-MOH-2026-001**. |
| Summaries | Preview contains **Required Std Category** / **Works** / **District Hospital** (passed-forward blurb); locked package context via source line + evidence. |
| Evidence strip | **Evidence** line references **PKG-MOH-2026-001**. |
| Drawer | **`plc-open-evidence`** → **`plc-technical-evidence-drawer`** with JSON body containing **`tm2_tender_code`** / **TND-MOH-2026-001**; dismissed with **Escape**. |

## Evidence (Playwright)

From **`apps/kentender_v1/`**:

```bash
npx playwright test tests/ui/smoke/procurement/procurement_journey_planning_release_plc_smoke_ui_003_r8_008.spec.ts
```

**Last run (2026-05-16, local):** `1 passed (5.1s)` — `procurement_journey_planning_release_plc_smoke_ui_003_r8_008.spec.ts`.

## Related references

- **PLC-SMOKE-UI-003** — cursor pack §15.2.
- **R4-010 / LV-R4-010-01** — full handoff panel (`expectWorksJourneyHandoffPanel`).
- **R3-018 HAC-001** — PKGREL API golden fields.
