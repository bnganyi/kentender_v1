# KenTender MVP-1 — Role & user cleanup audit

**Status:** Cleanup executed on site (2026-08-06) — 58 users disabled, 26 roles disabled; keep packs re-seeded  
**Date:** 2026-08-06  
**Site:** `kentender.midas.com`  
**Companion canvas:** `kentender-mvp1-role-user-cleanup-audit.canvas.tsx` (Cursor canvases)

## Goal

Keep only MVP-1 roles and deterministic test users. Disable wave leftovers (TM / BWMF / unit-test ephemerals) while retaining STD library and supplier portal cohorts.

## Binding decisions (2026-08-06)

| # | Decision | Outcome |
|---|---|---|
| 1 | Keep Performance Officer / Verifier Role definitions with 0 users? | **No.** Retire Role docs. Map measurement **submit** → Strategy Officer; **verify** → Strategy Manager. |
| 2 | Is STD library still in-scope on this site? | **Yes.** Keep STD Template roles + `stdinst*` users. |
| 3 | Keep supplier portal Website Users? | **Yes.** Keep smoke/supplier/`KenTender External Supplier` cohort. |
| 4 | Operator `bnganyi@yahoo.com` | **Keep** (outside seed packs). |

## Keep registries (source of truth)

| Pack | Path |
|---|---|
| Core SEED_USERS (9) | `kentender_core/seeds/constants.py` |
| Strategy role matrix | `kentender_strategy/seeds/strategy_role_users.py` |
| Budget role matrix | `kentender_budget/seeds/budget_role_users.py` |
| Cleanup runner | `kentender_core/seeds/mvp1_role_user_cleanup.py` |
| UI passwords / emails | `apps/kentender_v1/.env.ui` (gitignored) |

### Keep users

- Platform: `Administrator`, operator `bnganyi@yahoo.com`, PP2 actor `system@moh.test`
- Core: `strategy.manager@moh.test`, `planning.authority@moh.test`, `planning.reviewer@moh.test`, `requisitioner@moh.test`, `planner@moh.test`, `procurement.officer@moh.test`, `finance.reviewer@moh.test`, `hod.approver@moh.test`, `auditor@moh.test`
- **MOH_MVP_V1 §4.4:** `moh.medicalservices.officer@example.test`, `moh.publichealth.officer@example.test`, `moh.strategy.reviewer@example.test`, `moh.budget.reviewer@example.test`, `moh.budget.authority@example.test`, `moh.viewer@example.test`, `other.entity.officer@example.test` (+ thin SoD dual `moh.budget.officer.authority@example.test`)
- STD / supplier: `stdinst*`, `smoke.*`, `supplier.*`, lean/s100/x100 bidder*, `@kentender.test`, any User with `KenTender External Supplier`
- **Retired from keep (disabled by seed):** prior `strategy.*@moh.test` / `budget.*@moh.test` matrix (except core `strategy.manager@moh.test`)

### Keep roles

Strategy REQ §12 (MVP-1 remap) + Budget REQ + `BUSINESS_ROLES`: Strategy Viewer/Officer/Manager/Reviewer, Planning Authority, Auditor, Budget Viewer/Officer/Reviewer/Authority, Planning Reviewer, Requisitioner, Procurement Planner/Officer, Finance Reviewer, Department Approver, STD Template roles, KenTender External Supplier (portal).

**Capability remap (decision 1):** measurement submit/save = Strategy Officer; measurement verify/return/reject = Strategy Manager. Transitional aliases `ROLE_PERF_OFFICER` / `ROLE_PERF_VERIFIER` point at Officer / Manager.

## Live inventory snapshot (pre-cleanup)

- **96** users (excl. Guest)
- **~21** keep (MVP-1 + ops) + STD/supplier cohorts
- Remove candidates: unit-test `@example.com`, DIA orphans, TM/phase seeds, extra `@moh.test` not in packs
- Roles to disable: Performance Officer/Verifier, BWMF*, TM leftovers, `_Test Role*`, etc. (see `ROLES_TO_DISABLE` in cleanup script)

## Cleanup sequence

1. Dry-run then apply `mvp1_role_user_cleanup` (prefer disable over hard delete).
2. Re-seed keep packs (`upsert_strategy_role_users`, `upsert_budget_role_users`, core seeds as usual).
3. Run measurement/verify/notification tests + `make ui-strategy-role-gate` / `make ui-budget-role-gate`.
4. Optional follow-up: harden test `tearDown` so `@example.com` users are deleted after tests.

## Evidence (executed 2026-08-06)

| Check | Result |
|---|---|
| Cleanup apply | 58 users disabled, 26 roles disabled; 38 kept |
| Kept samples | `bnganyi@yahoo.com`, `stdinst1000-officer@example.test`, `supplier.p7-010@moh.test`, `smoke.a@kentender.test`, `strategy.reviewer@moh.test` enabled |
| Performance Officer/Verifier | Role `disabled=1` |
| `test_strategy_measurement_verify` | 6/6 OK |
| `test_strategy_notifications` | 6/6 OK |
| `test_strategy_mvp1_ac_matrix` | 12/12 OK |
| `test_budget_role_matrix` | 7/7 OK |
| `make ui-strategy-role-gate` | Playwright 5/5 passed |
| `make ui-budget-role-gate` | Playwright 6/6 passed |

```bash
# Re-run
bench --site kentender.midas.com execute \
  kentender_core.seeds.mvp1_role_user_cleanup.upsert_mvp1_role_user_cleanup
bench --site kentender.midas.com execute kentender_strategy.seeds.strategy_role_users.upsert_strategy_role_users
bench --site kentender.midas.com execute kentender_budget.seeds.budget_role_users.upsert_budget_role_users
cd apps/kentender_v1 && make ui-strategy-role-gate
cd apps/kentender_v1 && make ui-budget-role-gate
```
