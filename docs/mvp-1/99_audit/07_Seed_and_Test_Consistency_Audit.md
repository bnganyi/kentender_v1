# Seed and Test Consistency Audit

**Document ID:** KENTENDER-ROIDA-07-1.0  
**Date:** 11 August 2026  
**Mode:** Read-only  
**Controls:** CMOM §13; SWA §10–§12; `docs/mvp-1/00_common/KenTender_MVP_Canonical_Demo_Data_Contract_v2.5.md` (provisional per SWA §13)

---

## 1. Canonical seed entry points

| Step | Location | Role |
|---|---|---|
| Orchestrator | `kentender_core/seeds/kentender_mvp_v1/orchestrator.py` | `run_kentender_mvp_v1` |
| Constants | `.../constants.py` | PE-MOH, amounts (`PLAN_AMOUNT_V1=455e6`, `V2=535e6`, SCN 80e6) |
| Users / USA | `.../users.py` | Personas + `ensure_*_roles` |
| Strategy | `kentender_strategy/seeds/kentender_mvp_v1_strategy.py` | Upsert hierarchy + PVC |
| Budget | `kentender_budget/seeds/kentender_mvp_v1_portfolio.py` | Portfolio / lines / reservations |
| Demands | `kentender_procurement/.../demands/seeds/kentender_mvp_v1.py` | Principal / returned / treatments |
| Planning | `.../procurement_planning/seeds/kentender_mvp_v1.py` | Plans; clears Departmental Submission on reset |
| Validate | `kentender_core/seeds/kentender_mvp_v1/validate.py` | Arithmetic + identity checks |
| Runbook | `docs/mvp-1/00_common/MOH_MVP_V1_Seed_Runbook.md` | Operator instructions |

**Idempotency:** Upsert/clear helpers per module; validate.py asserts story. Exact DB repeatability not re-executed this pass (read-only).

---

## 2. Canonical arithmetic (contract vs validate)

| Invariant (CMOM §13 / SWA §10) | Seed/validate evidence | Status |
|---|---|---|
| Budget Line KES 480,000,000 | Portfolio seed + validate budget checks | Present in validate suite |
| Approved Demand / Active Plan Item 455,000,000 | `validate.py` principal + allocation checks; `PLAN_AMOUNT_V1` | **Aligned** |
| Commitment 310,000,000 | `budget.committed_310m` | **Aligned** |
| Remaining reservation 145,000,000 | `budget.reserved_145m` / RSV remaining | **Aligned** |
| Returned Demand 95→80m | validate returned + `PLAN_ITEM_SCN_AMOUNT` 80m | Returned check still cites 95m confirmed in one assert — **Investigate** correction-to-80 story completeness |
| Draft Revision 2 = 535,000,000 | `PLAN_AMOUNT_V2` | Constant present; planning seed must keep V1 operational |
| Kisumu second entity | Scope model / isolation tests | Present as isolation story in Planning/Demands tests |

---

## 3. Personas and scope

| Persona (demo) | Seed wiring | Notes |
|---|---|---|
| MoH Strategy / Budget / Demand / Planning users | `users.py` + module `*_role_users.py` | Explicit USA for PE-MOH / OUs |
| Planning Reviewer / Approver (Gate 05 UI) | `prepare_planning_gate05_approval_ui` + `moh.planning.reviewer@…` | Fixture users for Playwright |
| Administrator | Inflated in Strategy/Budget; blocked alone in Demand/Plan decisions | Inconsistent with CMOM §10 |

---

## 4. Prohibited seed content (CMOM §13)

| Concept | Seed/code presence | Disposition |
|---|---|---|
| Departmental Submission / contribution | Planning seed clears on reset; Gate helpers **create** via `submit_departmental_contribution`; Gate 05 UI prep | **Remove** from next canonical version |
| Generic Budget Line Value Treatment rows | Budget line contracts + portfolio may plant | **Remove** |
| Demand Value Treatment | Demands seed | **Remove** |
| Routine planning-stage HoD sign-off | Contribution path | **Remove** |
| Strategy Value Commitments (PVC) | Strategy seed (named Plan Value Commitment) | **Keep** with rename |

---

## 5. Test inventory vs business behaviour

### Behavioural (state / permission / arithmetic)

| Area | Examples | Notes |
|---|---|---|
| Strategy | `test_strategy_mvp1_*`, reference, activation concurrency | Strong domain |
| Budget | register, lines, readiness, check-reserve, revisions, role matrix | Strong; PE fallback under-tested as defect |
| Demands | creation scope (Admin no PE-MOH), funding AC-019, schema | Strong create-scope |
| Planning | add_demand, aggregate, validate, submit_for_review, decision, approve Gate05, PE selection, invariants Admin fallback | Strong — **but contribution tests encode prohibited workflow** |

### Smoke / render / chrome

| Area | Examples |
|---|---|
| Stitch chrome | `stitch-desk-chrome.spec.ts` |
| Layout guards | `test_*_ui_stitch_layout_guard.py` |
| Playwright smoke | strategy-alignment-nav, budget-funding-*, demands-*, planning-* |

### Tests that will turn red if Remove waves land (expected)

- `test_submit_departmental_contribution.py`
- `planning-contribution-drawer.spec.ts` / `make ui-planning-contribution-gate`
- Gate helpers calling contribution before approve
- Budget/Demand treatment validation tests
- Any REQ pack acceptance tests that assert UI-07 as Done

### Coverage gaps vs SWA §12 acceptance list

| Required proof | Current status |
|---|---|
| No Admin / first-assignment fallback | Demand/Plan **yes**; Budget/Home **no** |
| No user-maintained codes | Mostly yes at runtime |
| HoD once on normal path | **Violated** by contribution |
| Mandatory Finance cannot bypass | Demand BO path yes; Plan-level unclear |
| Unauthorised workflow forms inaccessible | Partial (readonly vs 403) |
| Removed treatment/contribution absent | **Present** in schema/services/UI/tests |
| Canonical seed deterministic + isolation | validate + cross-entity tests exist; contribution pollution risk |

---

## 6. Makefile gates (relevant)

| Gate | Implication under CMOM |
|---|---|
| `ui-planning-contribution-gate` | Encodes **Remove** surface — must not remain a Done criterion after CMOM accept |
| `ui-planning-approval-gate` | Keep after rewiring without contribution |
| `ui-budget-funding-*-gate` | Keep; strip treatment assertions when Remove lands |
| `ui-demands-*-gate` | Keep; strip value-treatment when Remove lands |
| `ui-strategy-alignment-ui-gate` | Keep; rename PVC labels |

---

## 7. Consistency verdict

Seed **arithmetic story** is largely coherent and validated. Seed/tests **still institutionalise contribution and generic treatments**, which CMOM/SWA mark for removal. Playwright/Makefile gates for PLN-UI-07 are high-quality tests of the **wrong** workflow relative to the draft operating model.
