<!--
  Evidence for Rectification Tracker §14 — G9-007
-->
## Goal

Close **§14 G9-007**: **TM2 controls preserved** — representative regressions for **legacy Procurement Tender surface lockout** (**P11-04 / P11-05**), **publication** gated via action availability (**EX-15**), **WORKS TM2 STD readiness summary** (**R3-016 BRS-001**), and **sealed bid** confidentiality before opening (**TM2-SMOKE-SEAL-001**).

## What was implemented

| Layer | Change |
|-------|--------|
| Regression bundle | **`procurement_lifecycle/tests/test_g9_007_tm2_controls_regression.py`** — loads five **named** tests via ``load_tests`` (see module docstring table). |
| Underlying suites | **P11-04 / P11-05**, **EX-15**, **R3-016 BRS-001**, **TM2-SMOKE-SEAL-001** — unchanged behaviour. |

## Evidence submitted (Python)

From **bench root**:

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_lifecycle.tests.test_g9_007_tm2_controls_regression
```

**Last run (local bench, site `kentender.midas.com`):** **5 tests OK** (~26s wall time): P11-04 + EX-15 + R3-016 BRS-001 + O-09 + P11-05 (`test_g9_007_tm2_controls_regression`).

## Related references

- **R8-012 / G0-004** — full P11-04/P11-05 aggregation (`test_r8_012_tm2_legal_smoke_regression`).
- **Doc 9 §7** — action availability vs legal services (**EX-15**).
- **R3-016 / PLC-SMOKE-BE-004** — five PASS readiness checks on WORKS **`TND-MOH-2026-001`**.
- **Doc 8 TM2-SMOKE-SEAL-001** — sealed bid denial pre-opening (**O-09**).
