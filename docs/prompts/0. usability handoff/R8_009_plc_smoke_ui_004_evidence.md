<!--
  Evidence for Rectification Tracker §13 — R8-009 / LV-R8-UI-04
-->
## Goal

Close **PLC-SMOKE-UI-004 / R8-009**: on the **TM2 Tender** Desk form for **`TND-MOH-2026-001`**, **`plc-business-readiness-summary`** shows the **five pack business labels** verbatim, and **Bundle/DSM/… technical output codes** stay **out of view** until the user expands **Technical output codes (advanced)** — cursor pack §15.2 + **R6-001 / R6-003**.

## What was verified

| Check | Detail |
|--------|--------|
| Host | **`tm2-tender-business-readiness-host`** + **`plc-business-readiness-summary`** visible after load (no stuck **`plc-br-loading`**). |
| Summary title | **`plc-br-summary-label`** contains **Tender document readiness**. |
| Business labels | Five **`plc-br-business-label`** rows match **BRS-003** strings (pack §15.2). |
| Not restricted | Administrator path: no **`plc-br-technical-restricted`** strip. |
| Collapsed technical | **`plc-br-technical-collapsed`** has no **`open`**; **`plc-technical-evidence-body`** not visible. |
| Expand / codes | After **`plc-br-technical-summary`** click: **`open`**, body visible, first **`.plc-technical-output-code`** contains **GB-TND-MOH-2026-001-V2**; collapse restores hidden state. |

## Evidence (Playwright)

From **`apps/kentender_v1/`**:

```bash
npx playwright test tests/ui/smoke/procurement/tm2_tender_business_readiness_plc_smoke_ui_004_r8_009.spec.ts
```

**Last run (2026-05-16, local):** `1 passed (3.8s)` — `tm2_tender_business_readiness_plc_smoke_ui_004_r8_009.spec.ts`.

## Related references

- **PLC-SMOKE-UI-004** — cursor pack §15.2.
- **R6-001 … R6-003**, **`business_readiness_summary.js`**.
- **R8-004 / PLC-SMOKE-BE-004** — same five labels via API/Python smoke.
