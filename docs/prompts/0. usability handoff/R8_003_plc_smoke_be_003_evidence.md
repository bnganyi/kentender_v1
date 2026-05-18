<!--
  Evidence for Rectification Tracker §13 — R8-003 / LV-R8-BE-03
-->
## Goal

Automate **PLC-SMOKE-BE-003**: when **source** planning truth (`Procurement Package`) changes after a **Planning Release** handoff exists, **`validate_handoff_card_freshness`** marks **`PKGREL-MOH-2026-001`** **Stale** while **the package keeps the updated value** — the handoff layer does **not** overwrite the source module (ADR-PLC-002 / **R1-010**; **R3-010** freshness contract).

## What was verified

| Step | Check |
|------|--------|
| PLC load | Same WORKS upstream seeds + **`load_procurement_lifecycle_works_master(reset=True, checkpoint="TENDER_PUBLISHED")`**. |
| Source change | **`procurement_method`** on **`PKG-MOH-2026-001`** set from **Open Tender** → **Restricted Tender** via **`frappe.db.set_value`** (source-module field change only). |
| Handoff | **`validate_handoff_card_freshness("PKGREL-MOH-2026-001")`** returns **`fresh: false`**, status **Stale**, nonempty **stale_reason**; DB handoff status **Stale**. |
| Authority | **`Procurement Package.procurement_method`** remains **Restricted Tender** after validation — no rollback from the handoff path. |
| Cleanup | Test restores original method and handoff **Consumed** / cleared **stale_reason** so the site is left consistent. |

## Evidence submitted (automated)

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_lifecycle.tests.test_r8_003_plc_smoke_be_003_handoff_source_authority
```

**Last run (2026-05-16, local bench):** `Ran 1 test … OK` — `test_plc_smoke_be_003_pkgrel_stale_when_package_changes_source_kept` in ~7.6s.

## Related references

- **PLC-SMOKE-BE-003** — cursor pack §15.1.
- **ADR-PLC-002** — non-authoritative journey/handoff; source wins.
- **R1-010** / **R3-010** — `handoff_freshness.py` mutates only `Procurement Handoff Card`.
