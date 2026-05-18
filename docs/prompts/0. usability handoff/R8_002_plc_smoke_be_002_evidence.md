<!--
  Evidence for Rectification Tracker §13 — R8-002 / LV-R8-BE-02
-->
# Goal

Automate **PLC-SMOKE-BE-002**: after the WORKS master PLC load (**`TENDER_PUBLISHED`**), **`get_procurement_journey("JRN-MOH-2026-001")`** must expose the **full §15 step spine** in contract order — covering the pack’s **Strategy → Budget → Demand → Planning → STD Readiness → Tender** material path (first seven `step_key` values through **`tender_publication`**) and the remaining **Opening / closing / award / contract** steps through key **`opening_readiness`**, **`bid_opening`**, etc. (12 rows total, per **R3-013** / **`WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER`**).

# What was verified

| Step | Check |
|------|--------|
| Upstream + PLC | Same prerequisite seed chain as **PLC-SMOKE-BE-001**; **`load_procurement_lifecycle_works_master(reset=True, checkpoint="TENDER_PUBLISHED")`** succeeds. |
| `get_procurement_journey` | **`steps`** length **12**; **`step_key`** sequence **equals** **`WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER`**. |
| Strategy→Tender | First **7** keys match **`WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER[:7]`** (ends at **`tender_publication`**). |
| Opening-related steps | Keys include **`opening_readiness`** and **`bid_opening`** (pack “Opening” wording; positions 9–10 in §15 table). |

# Evidence submitted (automated)

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_lifecycle.tests.test_r8_002_plc_smoke_be_002_journey_aggregation
```

**Last run (2026-05-16, local bench):** `Ran 1 test … OK` — `test_plc_smoke_be_002_get_procurement_journey_step_spine` in ~7s.

# Related references

- **PLC-SMOKE-BE-002** — cursor pack §15.1.
- **R3-011 / R3-013** — `get_procurement_journey` / step aggregation contracts.
