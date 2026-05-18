<!--
  Evidence for Rectification Tracker §13 — R8-012 / LV-R8-REG-01
-->
## Goal

Prove **TM2 legal controls** enforced by **P11-04** (no `Procurement Tender` document API on curated TM2 surfaces) and **P11-05** (no quoted **`Procurement Tender`** literal on those surfaces) remain **green** after PLC rectification work, per **G0-004** inventory and tracker **R8-012** dependency on **LV-R8-BE-01** (master seed path may run first; these tests are static scans and do not require the WORKS load).

## What was verified

| Step | Check |
|------|--------|
| Inventory | **G0-004** §Test Evidence — [`G0-004_tm2_legal_control_confirmation.md`](./G0-004_tm2_legal_control_confirmation.md). |
| P11-04 | `test_p11_04_tm2_surface_has_no_procurement_tender_doc_api` |
| P11-05 | `test_p11_05_tm2_surface_has_no_procurement_tender_doctype_literal` |

## Evidence submitted (automated)

Single module aggregates both G0-004 tests (see `procurement_lifecycle/tests/test_r8_012_tm2_legal_smoke_regression.py`).

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_lifecycle.tests.test_r8_012_tm2_legal_smoke_regression
```

**Last run (2026-05-16, local bench):** both slices **OK** — P11-04 ~0.004s, P11-05 ~0.004s; 2 tests total.

## Individual modules (same inventory as G0-004)

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.tender_management.tests.test_p11_04_tm2_surface_no_procurement_tender

bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.tender_management.tests.test_p11_05_tm2_surface_no_procurement_tender_literal
```

## Related references

- **G0-004** — TM2 legal control confirmation; scanner modules `p11_04_*` / `p11_05_*`.
- **TM2 v2 IMPLEMENTATION_TRACKER** — P11-04 / P11-05 acceptance.
- **Rectification tracker preamble** — TM2 legal behaviour remains canonical.
