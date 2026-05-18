<!--
  Evidence for Rectification Tracker §13 — R8-004 / LV-R8-BE-04
-->
## Goal

Automate **PLC-SMOKE-BE-004**: after the canonical WORKS PLC load (**`TENDER_PUBLISHED`**), **`get_business_readiness_summary("TM2 Tender", "TND-MOH-2026-001")`** exposes **five user-facing business labels**, maps **Bundle / DSM / DOM / DEM / DCM** technical rows in order, preserves the **golden technical ref codes** from **`PUBCERT`** handoff data, and returns the **publication snapshot** line — matching cursor pack §15.1 and **R3-016** contracts.

## What was verified

| Step | Check |
|------|--------|
| PLC load | Upstream WORKS seeds + **`load_procurement_lifecycle_works_master(reset=True, checkpoint="TENDER_PUBLISHED")`**. |
| Status | **`status="Ready"`**, all five **`checks[].result=="PASS"`**. |
| Business copy | **`business_label`** list equals pack §13 (**R3-016 BRS-003**). |
| Technical spine | **`technical_label`** order **Bundle → DSM → DOM → DEM → DCM**; each **`technical_ref`** equals **GB-/DSM-/DOM-/DEM-/DCM-…-V2** (**R3-016 BRS-004 / BRS-006**). |
| Snapshot | **`snapshot_ref`** = **`PUBSNAP-TND-MOH-2026-001-V2`** (**R3-016 BRS-005**). |
| UX flag | **`technical_details_available`** is **True** when all checks PASS. |

## Evidence submitted (automated)

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_lifecycle.tests.test_r8_004_plc_smoke_be_004_business_readiness_mapping
```

**Last run (2026-05-16, local bench):** `Ran 1 test … OK` — `test_plc_smoke_be_004_readiness_maps_five_technical_and_snapshot` in ~7.8s.

## Related references

- **PLC-SMOKE-BE-004** — cursor pack §15.1.
- **R3-016** / `business_readiness_summary.py`.
- **R6** technical-ref display — Desk consumes the same summary fields.
