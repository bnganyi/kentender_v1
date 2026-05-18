<!--
  Evidence for Rectification Tracker §14 — G9-003
-->
## Goal

Close **§14 G9-003**: **Procurement Home** is usable for lifecycle entry — **Active Procurement Journeys** shows at least one journey card with **Current stage**, a substantive **Next action** (not an empty/em-dash placeholder), **Blockers**, and **Open Journey** (`plc-home-open-journey`).

## What was implemented

| Layer | Change |
|-------|--------|
| Playwright helper | **`expectG9ProcurementHomeUsable`** in **`tests/ui/helpers/procurement.ts`** — shell + **`plc-procurement-home-active-journeys`** + **`#kt-ph-active-journeys-host`** cards + WORKS card meta/actions. |
| Playwright spec | **`g9_003_procurement_home_usable.spec.ts`**. |
| Desk JS | **None** (uses existing **`procurement_home_workspace.js`**). |

## Preconditions

- Site reachable at **`UI_BASE_URL`** (default **`http://127.0.0.1:8000`**).
- **Administrator** login (`.env.ui`).
- **`list_journeys`** returns **`JRN-MOH-2026-001`** as active (WORKS seed).

## Evidence submitted (Playwright)

From **`apps/kentender_v1/`**:

```bash
npx playwright install chromium   # agent / CI shells without browsers
npx playwright test tests/ui/smoke/procurement/g9_003_procurement_home_usable.spec.ts
```

**Last run (2026-05-16, local bench + `apps/kentender_v1`):** `1 passed (~5s)` — `g9_003_procurement_home_usable.spec.ts`.

## Related references

- **R4-001 / R8-006 / PLC-SMOKE-UI-001** — Procurement Home active journeys (`procurement_home_active_journeys.spec.ts`).
- **`renderHomeJourneyCard`** — **`procurement_home_workspace.js`** (stage / next action / blockers markup).
