<!--
  Evidence for Rectification Tracker §14 — G9-002
-->
## Goal

Close **§14 G9-002**: On the **Procurement Journey** Desk page (**`/desk/plc-procurement-journey/{code}`**), the seven base checkpoint handoffs (**STRATREF**, **BUDCONF**, **DEMAPP**, **PLANINCL**, **PKGREL**, **STDREADY**, **PUBCERT**) **appear** with **route**, **locked/passed-forward preview** (`plc-handoff-card-preview`), **evidence** (`plc-handoff-card-evidence`), **Technical details**, no **Stale** banner, and the journey shows **Next action** in **Current focus** (`plc-current-focus-next-action`).

## What was implemented

| Layer | Change |
|-------|--------|
| Playwright helper | **`expectG9BaseHandoffCardsDetail`** in **`tests/ui/helpers/procurement.ts`** — builds on **`expectWorksJourneyHandoffPanel`** (R4-010), then asserts per-card preview/evidence/stale + journey next action. |
| Playwright spec | **`g9_002_base_handoff_cards_visible.spec.ts`** — Administrator → **`/desk/plc-procurement-journey/JRN-MOH-2026-001`** → **`expectG9BaseHandoffCardsDetail`**. |
| Desk JS | **None** (uses existing **`procurement_journey_page.js`** handoff rendering). |

## Preconditions

- Site reachable at **`UI_BASE_URL`** (default **`http://127.0.0.1:8000`**).
- **Administrator** login (`.env.ui`).
- WORKS PLC seed with seven base handoff cards (**`BASE_HANDOFF_CODES`**).

## Evidence submitted (Playwright)

From **`apps/kentender_v1/`**:

```bash
npx playwright install chromium   # agent / CI shells without browsers
npx playwright test tests/ui/smoke/procurement/g9_002_base_handoff_cards_visible.spec.ts
```

**Last run (2026-05-16, local bench + `apps/kentender_v1`):** `1 passed (~6s)` — `g9_002_base_handoff_cards_visible.spec.ts`.

## Related references

- **R4-010** — Handoff panel smoke (`expectWorksJourneyHandoffPanel`).
- **R8-008 / PLC-SMOKE-UI-003** — PKGREL card depth (drawer).
- **`works_master_handoff_payloads.BASE_HANDOFF_CODES`** — canonical seven codes.
