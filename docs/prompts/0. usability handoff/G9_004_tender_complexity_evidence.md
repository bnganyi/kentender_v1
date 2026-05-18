<!--
  Evidence for Rectification Tracker §14 — G9-004
-->
## Goal

Close **§14 G9-004**: **Tender complexity reduced** — on the **TM2 Tender** Desk form, **business readiness** labels are visible **before** technical STD/output codes; technical detail stays behind **`plc-br-technical-collapsed`** until the user expands it (**PLC-SMOKE-UI-004** behaviour).

## What was implemented

| Layer | Change |
|-------|--------|
| Playwright | **`g9_004_tender_business_readiness_before_technical.spec.ts`** — Administrator → **`/app/tm2-tender/TND-MOH-2026-001`** → **`expectPlcSmokeUi004Tm2TenderFormBusinessReadiness`** (same assertions as **R8-009**). |
| Helpers | **Reuse** **`expectPlcSmokeUi004Tm2TenderFormBusinessReadiness`** in **`tests/ui/helpers/procurement.ts`** — no duplicate locator logic. |

## Preconditions

- Site reachable at **`UI_BASE_URL`**.
- **Administrator** (`.env.ui`).
- **`TND-MOH-2026-001`** seeded (WORKS TM2).

## Evidence submitted (Playwright)

From **`apps/kentender_v1/`**:

```bash
npx playwright install chromium
npx playwright test tests/ui/smoke/procurement/g9_004_tender_business_readiness_before_technical.spec.ts
```

**Last run (2026-05-18, local bench + `apps/kentender_v1`):** `1 passed (~38s)` — `g9_004_tender_business_readiness_before_technical.spec.ts`.

## Related references

- **R8-009 / PLC-SMOKE-UI-004** — `tm2_tender_business_readiness_plc_smoke_ui_004_r8_009.spec.ts`.
- **R3-016 BRS-003** — five business label strings enforced in helper.
