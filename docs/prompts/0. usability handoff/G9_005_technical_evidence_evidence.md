<!--
  Evidence for Rectification Tracker §14 — G9-005
-->
## Goal

Close **§14 G9-005**: **Technical evidence preserved** — an authorized Desk user (**Administrator** smoke) opening **TM2 Tender** **`TND-MOH-2026-001`** can expand **`plc-br-technical-collapsed`** and see **`plc-technical-evidence-body`** containing **Bundle (GB)** / **DSM** / **DOM** / **DEM** / **DCM** tokens and **`PUBSNAP-TND-MOH-2026-001-V2`** (**PLC-SMOKE-UI-005**).

## What was implemented

| Layer | Change |
|-------|--------|
| Playwright | **`g9_005_tm2_technical_evidence_visible.spec.ts`** → **`expectPlcSmokeUi005Tm2ReadinessTechnicalBodyStdout`**. |
| Helpers | **Reuse** **`PLC_SMOKE_UI_005_TECH_AND_SNAPSHOT_EXPECTATIONS`** / **`expectPlcSmokeUi005Tm2ReadinessTechnicalBodyStdout`** in **`tests/ui/helpers/procurement.ts`**. |

## Preconditions

- **`UI_BASE_URL`** reachable; **Administrator** (`.env.ui`).
- **`TND-MOH-2026-001`** seeded with WORKS STD/snapshot refs.

## Evidence submitted (Playwright)

From **`apps/kentender_v1/`**:

```bash
npx playwright install chromium
npx playwright test tests/ui/smoke/procurement/g9_005_tm2_technical_evidence_visible.spec.ts
```

**Last run (2026-05-18, local bench + `apps/kentender_v1`):** `1 passed (~5s)` — `g9_005_tm2_technical_evidence_visible.spec.ts`.

## Related references

- **R8-010 / PLC-SMOKE-UI-005** — `tm2_technical_evidence_plc_smoke_ui_005_r8_010.spec.ts`.
- **R3-016 / PLC-SMOKE-BE-004** — canonical technical refs.
