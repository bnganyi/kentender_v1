<!--
  Evidence for Rectification Tracker §13 — R8-014 / LV-R8-REG-03
-->

## Goal

Prove **Planning → Tender** **package release governance** survives PLC usability work: **`create_planning_release_package` (PKGREL)**, **`release_procurement_package_to_tender`** (B3/B10), **handoff configuration / audit / duplicate** guards (**B7–B9**) stay green—matching the Cursor pack (**§1688**) “Planning release remains governed” bar and Tender Management tracker **R07** module inventory.

## What was implemented

| Area | Deliverable |
|------|-------------|
| R8 aggregator | **`test_r8_014_planning_release_governance_smoke_regression`** — `unittest` **`load_tests`** over **R3-005** + **B3** + **B7–B10** modules (see aggregator docstring inventory). |
| WORKS prerequisite | **`works_master_budget_seed._ensure_works_sub_program`** — idempotent Sub Program under **PROG-MOH-INFRA**, linked on **`BUD-MOH-INFRA-2026-001`** (new inserts + DB backfill path) so DIA derivation fields (`Demand.sub_program`) are populated for integration fixtures. |
| Handoff fixtures | **`handoff_integration_test_budget_line_name`** in **`test_release_procurement_package_to_tender_b3`** — prefers active **`BL-MOH-2026-001`**, else active **`BUD-MOH-INFRA-2026-001`** once `sub_program` is set (**R2-005** aligned). **`test_planning_tender_handoff_xmv_b5`** restores Budget Line IDs using the same resolver. |
| Regression tests | **`test_release_package_to_tender_fails_if_no_tender_after_handoff`** — accepts either historic or current ``ValidationError`` copy (“TM2 Tender” vs generic “tender”). **`test_r2_005_works_master_budget_seed.test_001`** — `_clean_budget` before fresh insert for shared benches; asserts **`Budget Line.sub_program`** after seed. |

## Evidence submitted (automated)

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_lifecycle.tests.test_r8_014_planning_release_governance_smoke_regression
```

**Last run:** **OK** — **34** integration tests, ~176 s (kentender.midas.com, agent session).

**Related (seed contract):**

```bash
bench --site kentender.midas.com run-tests --app kentender_budget \
  --module kentender_budget.tests.test_r2_005_works_master_budget_seed
```

**Last run:** **OK** — **5** tests (includes **Sub Program** / **Budget Line.sub_program** checks).

### Underlying modules (inventory)

Runs are equivalent (for governance scope) to executing each module separately:

- `kentender_procurement.procurement_lifecycle.tests.test_r3_005_planning_release_handoff`
- `kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3`
- `kentender_procurement.tender_management.tests.test_planning_tender_handoff_configuration_b7`
- `kentender_procurement.tender_management.tests.test_planning_tender_handoff_audit_b8`
- `kentender_procurement.tender_management.tests.test_planning_tender_handoff_duplicate_b9`
- `kentender_procurement.tender_management.tests.test_planning_tender_handoff_release_integration_b10`

## Operational note

Bench sites that load **PLC-SMOKE-BE-001** / **`upsert_works_master_budget`** after this change will refresh **`BUD-MOH-INFRA-2026-001`** `sub_program` on the existing-row path. **Planning release handoff** UI flows (**R5-006** / **PLC-SMOKE-UI-003**) are unchanged visually; behavioural alignment is Demand/strategy derivation for **integration tests**—not UX copy.

## Related references

- Rectification Cursor pack §1688 — planning release governed.
- [`docs/prompts/tender management/IMPLEMENTATION_TRACKER.md`](../../tender%20management/IMPLEMENTATION_TRACKER.md) — **R07** (B3 + B7–B10 + B10 citations).
- **R3-005** / **LV-R3-005-01** — PKGREL service.
