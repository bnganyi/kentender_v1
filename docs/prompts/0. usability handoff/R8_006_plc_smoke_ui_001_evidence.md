<!--
  Evidence for Rectification Tracker §13 — R8-006 / LV-R8-UI-01
-->
## Goal

Close **PLC-SMOKE-UI-001 / R8-006**: **Procurement Home** shows **`JRN-MOH-2026-001`** (“District Hospital Renovation Works”) in **Active Procurement Journeys** with **current stage**, **next action**, and **`Open Journey`** routing to **`plc-procurement-journey/{code}`**, using pack selectors **`plc-procurement-home-active-journeys`** and **`plc-home-open-journey`** (implemented as **`data-testid`** on panel + primary button).

Implementation reuses **R4-001** (`procurement_home_workspace.js`, `procurement_home_active_journeys.spec.ts`); R8 adds explicit testids aligned with §15.2 and regression-proof locators.

## What was implemented

| Layer | Change |
|-------|--------|
| Desk JS | **`data-testid="plc-procurement-home-active-journeys"`** on active panel root; **`data-testid="plc-home-open-journey"`** on **Open Journey** button (`procurement_home_workspace.js`). |
| Playwright helpers | **`expectProcurementHomeActiveJourneysPanel`** / **`activeJourneyCard`** use **`getByTestId('plc-procurement-home-active-journeys')`** (`tests/ui/helpers/procurement.ts`). |
| Spec | **`procurement_home_active_journeys.spec.ts`** — tags **R8-006**, **`card.getByTestId('plc-home-open-journey')`**, assertions for stage **Tender Published**, next action / blockers copy. |
| Assets | **`./scripts/bench-with-node.sh build --app kentender_procurement`** (required after JS edit). |

## Preconditions

- Site reachable at **`UI_BASE_URL`** (default **`http://127.0.0.1:8000`** per `playwright.config.ts`).
- **Administrator** credentials (`.env.ui` / env used by **`loginAsAdministrator`**).
- WORKS journey **`JRN-MOH-2026-001`** seeded (PLC load / upstream seeds).

## Evidence submitted (Playwright)

From **`apps/kentender_v1/`**:

```bash
npx playwright install chromium   # agent / CI shells without browsers
npx playwright test tests/ui/smoke/procurement/procurement_home_active_journeys.spec.ts
```

**Last run (2026-05-16, local bench + `apps/kentender_v1`):** `2 passed (11.0s)` — full file `procurement_home_active_journeys.spec.ts` (PLC-SMOKE-UI-001 + View Evidence).

## Related references

- **PLC-SMOKE-UI-001** — cursor pack §15.2.
- **R4-001 / LV-R4-001-01** — original feature acceptance.
- **R4-005 / R4-006** — journey Desk page shell navigated after **Open Journey**.
