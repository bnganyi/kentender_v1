<!--
  Evidence for Rectification Tracker §13 — R8-001 / LV-R8-BE-01
-->
# Goal

Automate **PLC-SMOKE-BE-001**: prove the canonical **`bench execute`** path — **`load_procurement_lifecycle_works_master(reset=True, checkpoint="TENDER_PUBLISHED")`** — materializes **`JRN-MOH-2026-001`** and the **seven base handoff cards**, and does **not** create **CLOSECERT** / **OPENREADY** opening handoffs (pack §15.1, tracker NG-007A).

# What was verified

| Step | Check |
|------|--------|
| Upstream WORKS seeds | Strategy → Tender fixtures (same prerequisite chain as **R3-011** integration tests). |
| PLC load | `reset=True`, `checkpoint="TENDER_PUBLISHED"` → `ok`; **`Procurement Journey`** **`JRN-MOH-2026-001`** exists. |
| Base handoffs | Every code in **`BASE_HANDOFF_CODES`** exists as **`Procurement Handoff Card`**. |
| Opening hygiene | **`CLOSECERT-TND-MOH-2026-001`** and **`OPENREADY-TND-MOH-2026-001`** **absent** after base load. |
| Validator | **`validate_procurement_lifecycle_works_master_seed(TENDER_PUBLISHED)`** — **VAL-SEED-001**, **016–019** **PASS**. Full **`ok`** may remain false until TM2 satisfies **VAL-SEED-014/015/020/022**. |

# Evidence submitted (automated)

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_lifecycle.tests.test_r8_001_plc_smoke_be_001_master_seed_load
```

# Related references

- **§16.1–16.2** acceptance commands (`load_procurement_lifecycle_works_master`, `validate_procurement_lifecycle_works_master_seed`).
- **`seed_procurement_lifecycle_works_master.py`** — public entrypoints.
