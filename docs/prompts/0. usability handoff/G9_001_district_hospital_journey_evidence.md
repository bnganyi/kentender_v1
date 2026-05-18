<!--
  Evidence for Rectification Tracker §14 — G9-001 / LV-G9-001-01
-->
## Goal

Close **§14 G9-001**: **District Hospital Renovation Works** (**`JRN-MOH-2026-001`**) is visible as **one coherent journey from Strategy through Tender** — entered from **Procurement Home** via **Open Journey**, with the Journey Desk page showing the master header and lifecycle spine through **`tender_publication`** (base seed checkpoint **`TENDER_PUBLISHED`**).

## What was implemented

| Layer | Change |
|-------|--------|
| Playwright | **`g9_001_district_hospital_journey_visible.spec.ts`** — Administrator → **Procurement Home** → active card → **`plc-home-open-journey`** → asserts **`plc-journey-page`**, **`expectWorksMasterJourneyHeader`**, **`expectPlcSmokeUi002JourneyFullSpine`** (same spine contract as **PLC-SMOKE-UI-002 / R8-007**). |
| Helpers | Reuses **`tests/ui/helpers/procurement.ts`** (`activeJourneyCard`, spine helpers); **no** new Desk JS required for this gate. |

## Preconditions

- Site reachable at **`UI_BASE_URL`** (default **`http://127.0.0.1:8000`** per `playwright.config.ts`).
- **Administrator** credentials (`.env.ui` / **`loginAsAdministrator`**).
- WORKS journey **`JRN-MOH-2026-001`** seeded (`load_procurement_lifecycle_works_master` / upstream PLC seeds).

## Evidence submitted (Playwright)

From **`apps/kentender_v1/`**:

```bash
npx playwright install chromium   # agent / CI shells without browsers
npx playwright test tests/ui/smoke/procurement/g9_001_district_hospital_journey_visible.spec.ts
```

**Last run (2026-05-16, local bench + `apps/kentender_v1`):** `1 passed (~12s)` — `g9_001_district_hospital_journey_visible.spec.ts`.

Record output in reviewer bundle when promoting gate status to **Accepted**.

## Related references

- **R8-006 / PLC-SMOKE-UI-001** — Procurement Home active journey card + routing.
- **R8-007 / PLC-SMOKE-UI-002** — Journey page spine pillars and step statuses.
- Pack §14 **G9-001** — “One coherent journey from Strategy through Tender appears.”
