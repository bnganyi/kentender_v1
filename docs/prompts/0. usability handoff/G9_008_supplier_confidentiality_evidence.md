<!--
  Evidence for Rectification Tracker §14 — G9-008
-->
## Goal

Close **§14 G9-008**: **Supplier confidentiality preserved** — supplier / portal actors cannot obtain **internal** procurement lifecycle evidence (journey evidence APIs and related gates); aligns with **NG-006**.

## What was implemented

| Layer | Change |
|-------|--------|
| Automated regression | **Existing** **`test_r8_015_supplier_confidentiality_smoke_regression`** — bundles **R3-020** (`test_r3_020_supplier_confidentiality`). Wrapper docstring updated to cite **G9-008**. |
| New logic | **None** — gate is **R8-015 / NEG-SUP-EVIDENCE-ACCESS-001** / **G0-006**. |
| Detailed evidence | [`R8_015_supplier_confidentiality_evidence.md`](./R8_015_supplier_confidentiality_evidence.md). |

## Preconditions

- Site with WORKS PLC journey/handoff seeds (**LV-R8-BE-01** profile) and **`smoke.b@kentender.test`** where named-user tests apply (see **R8-015** evidence).

## Evidence submitted (Python)

From **bench root**:

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_lifecycle.tests.test_r8_015_supplier_confidentiality_smoke_regression
```

**Underlying module (same tests):**

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_lifecycle.tests.test_r3_020_supplier_confidentiality
```

**Last run (local bench, site `kentender.midas.com`):** **22 tests OK** in ~2.6s — `test_r8_015_supplier_confidentiality_smoke_regression`.

## Related references

- **R8-015 / LV-R8-REG-04** — regression wrapper for PLC tracker §13.
- **R3-020 / LV-R3-020-01** — canonical supplier confidentiality suite.
