# MOH_MVP_V1 — Seed Runbook

**Contract:** [KenTender_MVP_Canonical_Demo_Data_Contract.md](./KenTender_MVP_Canonical_Demo_Data_Contract.md)  
**Fixture namespace:** `MOH_MVP_V1`  
**Fixture clock:** `2027-11-03T12:00:00+03:00`  
**Password:** `Test@123` (`kentender_core.seeds.constants.TEST_PASSWORD`)

## Reproduce clean canonical data

From the bench root (`/home/midasuser/frappe-bench`):

```bash
# 1) Apply schema (ownership / department_code / fixture fields)
bench --site kentender.midas.com migrate

# 2) Reset + seed + validate (idempotent; safe to re-run)
cd apps/kentender_v1 && make seed-moh-mvp-v1 SITE=kentender.midas.com

# Equivalent bench execute:
bench --site kentender.midas.com execute \
  kentender_core.seeds.moh_mvp_v1.orchestrator.run_moh_mvp_v1 \
  --kwargs '{"reset": true, "force": true, "validate": true}'

# 3) Validate only
cd apps/kentender_v1 && make seed-moh-mvp-v1-validate SITE=kentender.midas.com
```

Optional: retire leftover non-keep Users/Roles after the pack is loaded:

```bash
bench --site kentender.midas.com execute \
  kentender_core.seeds.mvp1_role_user_cleanup.upsert_mvp1_role_user_cleanup
```

## Demo logins (§4.4)

| Email | Purpose |
|---|---|
| `moh.medicalservices.officer@example.test` | Medical Services / DHP officer |
| `moh.publichealth.officer@example.test` | Public Health / HRMD officer |
| `moh.strategy.reviewer@example.test` | Strategy reviewer |
| `moh.budget.reviewer@example.test` | Budget reviewer |
| `moh.budget.authority@example.test` | Budget authority |
| `moh.viewer@example.test` | Read-only management viewer |
| `other.entity.officer@example.test` | Cross-entity denial (PE-MOE) |

## What the orchestrator does

1. Clears `MOH_MVP_V1` Strategy + Budget records (reverse dependency order)  
2. Upserts PE-MOH/PE-MOE + State Departments + Directorates  
3. Upserts §4.4 users (disables retired `@moh.test` Strategy/Budget matrix)  
4. Seeds Strategy plan `MOH-SP-2026-2030` + hierarchy/PVCs/measurements  
5. Seeds Budgets `MOH-BUD-2027-2028` / `2028-2029` / `2026-2027` + RSV/COM/EXP ledger  
6. Prints a PASS/FAIL §9 verification report  

**Not in the canonical pack:** readiness/role-matrix edges `MOH-BUD-0002` (Submitted) and `MOH-BUD-0004` / `MOH-BL-0006` (incomplete Draft). Those load only when `upsert_moh_mvp_v1_portfolio(include_test_edges=True)` (default for domain tests).

**Freshness note:** RSV/COM/EXP narrative dates follow the fixture clock `2027-11-03`. Line `actual_as_at` for DHI is set relative to wall-clock `today()` so Desk freshness shows **Stale** without freezing server time.

Production sites refuse the seed unless `developer_mode`, `allow_moh_mvp_v1_seed`, or `force=True`.
