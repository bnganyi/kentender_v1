<!--
  Evidence for Rectification Tracker §13 — R8-016 / LV-R8-BE-06
-->

## Goal

Prove the **base** WORKS PLC checkpoint (**`TENDER_PUBLISHED`**) stays **clean of optional bid-opening artefacts**: master loader must not create **`CLOSECERT-TND-MOH-2026-001`** / **`OPENREADY-TND-MOH-2026-001`** handoff cards, must not drift the **`Procurement Journey`** header into an **opening-ready** profile, and must not prematurely wire **`tender_closing`** / **`opening_readiness`** spine rows to CLS/ORR handoff payloads. Matches Cursor pack **§15.1 / PLC-SMOKE-BE-006**.

## What was verified

| Step | Check |
|------|--------|
| Load | **`load_procurement_lifecycle_works_master(reset=True, checkpoint="TENDER_PUBLISHED")`** after the same prerequisite seed chain as **R8-001**. |
| Handoff cardinality | Loader summary **`handoff_cards`** equals **`len(BASE_HANDOFF_CODES)`** (seven base §16 cards). |
| Opening cards absent | **`OPENING_HANDOFF_CODES`** (`CLOSECERT…`, `OPENREADY…`) have **no** `Procurement Handoff Card`. |
| Journey header | **`opening_readiness_ref`** blank; **`current_stage_key`** remains **`tender_published`** (`JOURNEY_HEADER_STAGE_KEY`). |
| Spine isolation | Rows **`tender_closing`** and **`opening_readiness`** carry **no** optional opening **`handoff_code`** and **no** fabricated **`CLS-TND*`** / **`ORR-TND*`** `source_object_code` values on the PLC child table. |

**Scope note:** independent **`TM2 Tender Closing Record`** / **`TM2 Opening Readiness Record`** rows may exist from **tender lifecycle** seeds or operator actions—these are **outside** PLC master loader responsibility. **PLC-SMOKE-BE-006** asserts **PLC graph** hygiene (handoffs + journey presentation), not global purging of TM2 documents.

## Evidence submitted (automated)

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_lifecycle.tests.test_r8_016_plc_smoke_be_006_optional_opening_seed_hygiene
```

**Last run (2026-05-16, local bench, kentender.midas.com):** **OK** — **1** integration test in ~8.7s (`test_plc_smoke_be_006_base_no_opening_handoffs_or_journey_profile_drift`).

## Related references

- **PLC-SMOKE-BE-006** — Cursor Implementation Pack §15.1.
- **R8-001** / **R8-005** — overlapping base-handoff / timeline invariants.
- **R2-011** — SEED-TEST-R2-011-005 base checkpoint cards.
