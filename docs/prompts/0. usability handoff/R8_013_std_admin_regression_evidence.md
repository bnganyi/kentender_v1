<!--
  Evidence for Rectification Tracker §13 — R8-013 / LV-R8-REG-02
-->
## Goal

After PLC usability rectification (**R8**, **§15** usability smoke), prove **Official STD Template Governance** invariants—the server-side lifecycle, permissions, package validation gates, eligibility, supersession/retirement, auditing, seed governance (**STD-GOV-ST-001 … ST-020 Doc 8 §C**)—still pass. This gate matches the rectification pack rule: usability work must **not** weaken STD Admin governance controls.

## What was verified

| Step | Check |
|------|--------|
| Inventory | Tender management automated Doc 8 gate — **`test_std_template_governance_smoke_doc8`** (maps *STD Governance* **§8 Smoke Test Specification**, API/service acceptance). |
| R8 aggregator | **`test_r8_013_std_governance_smoke_regression`** loads the Doc 8 module via `unittest` **`load_tests`** (same pattern as **R8-012**). |
| Scope | Roles/boundaries (**ST-001**), POC import + validate (**ST-002–003**), invalid package blocks submit (**ST-004**), full lifecycle chain (**ST-005–015**), permission negatives (**ST-016**), replace + re-validation (**ST-017**), governed POC seed (**ST-020**), C3 mutation guards (**C3** tests). |

**Desk UI scenarios (ST-018 / ST-019)** remain covered by Playwright **`std-template-governance-smoke-doc8.spec.ts`** (see Doc 8 module header); **R8-013 evidence** records the **bench** regression command only (tracker **kentender_procurement** / CI log).

## Evidence submitted (automated)

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_lifecycle.tests.test_r8_013_std_governance_smoke_regression
```

**Last run:** **OK** — **12** integration tests in ~34s (single slow spots: POC import ~14s; POC seed governance ~15s).

## Canonical underlying module

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.tender_management.tests.test_std_template_governance_smoke_doc8
```

Equivalent test count and outcome to the aggregator (aggregator exists for tracker naming parity with **R8-012**).

## Related references

- **`8. std_template_governance_lifecycle_smoke_test_specification.md`** (production-readiness §8).
- **`test_std_template_governance_smoke_doc8`** module docstring (Doc 8 §C mapping).
- Rectification preamble — STD governance stays role-controlled (**Cursor pack**, **plc rectification pack**).
