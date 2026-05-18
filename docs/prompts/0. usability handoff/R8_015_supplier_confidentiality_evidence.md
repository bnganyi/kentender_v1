<!--
  Evidence for Rectification Tracker §13 — R8-015 / LV-R8-REG-04
-->

## Goal

Ensure PLC usability and journey presentation work **does not regress supplier confidentiality**:
supplier portal actors remain **denied by default** on Procurement Lifecycle APIs—especially
**internal evidence timeline** (**`get_journey_evidence`**)—encoding **NEG-SUP-EVIDENCE-ACCESS-001**
and **G0-006** in repeatable CI.

## What was verified

| Step | Check |
|------|--------|
| Inventory | **R3-020** / **LV-R3-020-01** — ``kentender_procurement/procurement_lifecycle/tests/test_r3_020_supplier_confidentiality.py``. |
| Named threat | **NEG-SUP-EVIDENCE-ACCESS-001** — Guest + supplier user cannot call **`get_journey_evidence`**; related **NEG-SUP-*** and **NEG-SUP-DOCPERM-*** paths in the same module. |
| R8 wrapper | **`test_r8_015_supplier_confidentiality_smoke_regression`** — aggregates R3-020 via `unittest` **`load_tests`** (same pattern as **R8-012**/**R8-013**/**R8-014**). |

**Depends:** **LV-R8-BE-01**-class site data (WORKS journey/handoff cards; **`smoke.b@kentender.test`** for named supplier tests). **LV-R7-007-01** (Playwright mirror for any client-side fetches) is **out of scope** for this evidence row and remains on the tracker separately.

## Evidence submitted (automated)

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_lifecycle.tests.test_r8_015_supplier_confidentiality_smoke_regression
```

**Last run (2026-05-16, local bench, kentender.midas.com):** **OK** — **22** integration tests in ~1.65s.

## Canonical underlying module

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_lifecycle.tests.test_r3_020_supplier_confidentiality
```

## Related references

- **G0-006** — supplier confidentiality threat model; **LV-R8-REG-04** cross-walk.
- Rectification pack **§10.4** — supplier cannot access internal journey evidence by default.
- **R3-020** tracker row — acceptance baseline for this module.
