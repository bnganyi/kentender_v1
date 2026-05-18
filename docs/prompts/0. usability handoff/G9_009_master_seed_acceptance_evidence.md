<!--
  Evidence for Rectification Tracker §14 — G9-009
-->
## Goal

Close **§14 G9-009**: **WORKS master seed accepted** — the loader and validator behave per the **WORKS Master Seed Data Specification** on the **base** checkpoint **`TENDER_PUBLISHED`**; **`OPENING_READY`** stays optional (see tracker §16.5).

## What was implemented

| Layer | Change |
|-------|--------|
| Regression bundle | **`procurement_lifecycle/tests/test_g9_009_master_seed_acceptance.py`** — aggregates **R8-001** + **R2-003** via ``load_tests``. |
| Underlying tests | **PLC-SMOKE-BE-001** (reset load, seven base handoffs, no opening cards, VAL-SEED-001 + 016–019 PASS); **R2-003** (22-row validator shape, unsupported checkpoint, PLC load → subset PASS). |
| Cross-reference | **R8-001** module docstring cites **G9-009**. |

### Caveat (aligned with **R8-001**)

Full validator aggregate **`ok`** may still be **false** until TM2 publication fixtures satisfy **VAL-SEED-014/015/020/022** on the site. G9-009 still passes via **explicit PASS** assertions on PLC-critical checks and validator contracts documented under **R2-003**.

## Preconditions

- Same upstream WORKS seed chain as **R8-001** (strategy → … → TM2).

## Evidence submitted (Python)

From **bench root**:

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_lifecycle.tests.test_g9_009_master_seed_acceptance
```

**Manual specification hooks** (§16.1–16.2), optional:

```bash
bench --site kentender.midas.com execute \
  kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master.load_procurement_lifecycle_works_master \
  --kwargs '{"reset": true, "checkpoint": "TENDER_PUBLISHED"}'

bench --site kentender.midas.com execute \
  kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master.validate_procurement_lifecycle_works_master_seed \
  --kwargs '{"checkpoint": "TENDER_PUBLISHED"}'
```

**Last run (local bench, site `kentender.midas.com`):** **5 tests OK** (~17s wall time): **R8-001** ×1 + **R2-003** ×4 (`test_g9_009_master_seed_acceptance`).

## Related references

- [`R8_001_plc_smoke_be_001_evidence.md`](./R8_001_plc_smoke_be_001_evidence.md)
- [`G0-009_works_master_seed_specification_acceptance.md`](./G0-009_works_master_seed_specification_acceptance.md)
