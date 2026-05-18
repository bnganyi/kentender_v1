<!--
  Evidence for Rectification Tracker §13 — R8-010 / LV-R8-UI-05
-->
## Goal

Close **PLC-SMOKE-UI-005 / R8-010**: after expanding the TM2 Tender **Technical output codes (advanced)** block (**`plc-br-technical-collapsed` → open**), **`plc-technical-evidence-body`** must surface **all pack STD/ref strings** (**GB**, **DSM**, **DOM**, **DEM**, **DCM**) plus **PUBSNAP-TND-MOH-2026-001-V2**, matching §15.2 and **`read_business_readiness_summary` / `PUBCERT`** technical payload alignment.

Pack lists selector **`plc-technical-evidence-drawer`** (Bootstrap modal for **handoff** JSON on **`plc-procurement-journey`** — **R4-013**). On the **TM2 Tender** Desk form we assert the **`plc-br-technical-collapsed`** / **`plc-technical-evidence-body`** readiness surface (**R6-003**) that **reuses the same `plc-technical-evidence-body` test-id** for the expandable body.

## What was verified

| Check | Detail |
|--------|--------|
| Route | `/app/tm2-tender/TND-MOH-2026-001` with seeded tender. |
| Host | **`tm2-tender-business-readiness-host`** mounts readiness. |
| Expand | **`plc-br-technical-summary`** reveals **`plc-technical-evidence-body`**. |
| Tokens | **`PLC_SMOKE_UI_005_TECH_AND_SNAPSHOT_EXPECTATIONS`** (six strings §15.2): five **`*-V2`** STD codes + **PUBSNAP**. |
| Collapse | Body hidden again (drawer semantics). |

## Evidence (Playwright)

```bash
npx playwright test tests/ui/smoke/procurement/tm2_technical_evidence_plc_smoke_ui_005_r8_010.spec.ts
```

**Last run (2026-05-16, local):** `1 passed (3.7s)` — `tm2_technical_evidence_plc_smoke_ui_005_r8_010.spec.ts`.

## Related references

- **PLC-SMOKE-UI-005** — cursor pack §15.2.
- **R6-003**, **`PLC-SMOKE-UI-004` / R8-009** expansion path.
- **R4-013 / `plc-technical-evidence-drawer`** — handoff-centered modal JSON (same token set from **`PUBCERT`** where applicable).
