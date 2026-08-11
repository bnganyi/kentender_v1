# Budget & Funding — Disposition Matrix

**Document ID:** KENTENDER-ROIDA-03-1.0  
**Date:** 11 August 2026  
**Mode:** Read-only  
**App:** `kentender_budget` → `apps/kentender_v1/kentender_budget`  
**Controls:** CMOM §6.2, §8; SWA §7.1–7.3, §8.2

| Artifact | Exact location | Current purpose/effect | Evidence | Disposition | Required correction | Dependencies | Migration/seed impact | Tests affected |
|---|---|---|---|---|---|---|---|---|
| Budget DocType | `doctype/budget/budget.json` | Register procurement funding; status Draft→Active | JSON + register/activate APIs | **Keep** | — | Lines | Seed portfolio | `test_budget_register`, readiness |
| Budget Line | `doctype/budget_line/budget_line.json` | Approved amounts + reserved/committed/actual | JSON | **Keep** | Soften forced primary-target if unsupported | Strategy targets | Seed 480m line | line + strategy validate tests |
| Budget Line Value Treatment | `doctype/budget_line_value_treatment/` | Generic treatment questionnaire (Dedicated/Embedded/N/A + rationale) | JSON + line save validation | **Remove** | Drop child + UI; keep PVC/target snapshots if needed elsewhere | PVC naming | Data loss risk — migrate snapshots first | `test_budget_line_strategy_validate`, lines UI |
| Budget Line Supporting Target | `doctype/budget_line_supporting_target/` | Secondary Strategy links | JSON | **Keep/Correct** | Only where approved budget structure supports | Strategy | — | line tests |
| Funding Reservation | `doctype/funding_reservation/` | Hold through Demand/Planning | `reserve_funding` | **Keep** | One reservation lineage (CMOM §8.3) | Demand funding | Seed 455→145 remaining | check-reserve tests |
| Procurement Commitment | `doctype/procurement_commitment/` | Commitment amounts | Seeded/read; convert API **Not started** (XMOD-BUD-007) | **Keep** schema; **Investigate** convert | Implement or document read-only until convert | Reservation | Seed 310m | lifecycle tests |
| Budget Revision (+ Line) | `doctype/budget_revision*` | Controlled change | revision contracts | **Keep** | — | Active Budget | — | revision gates |
| Funding Exception | `doctype/funding_exception/` | Demand-scoped exception | JSON | **Keep/Investigate** | Confirm consumer | Demands UI-07 | — | exception API tests |
| Expenditure Snapshot | `doctype/expenditure_snapshot/` | Read-only expenditure | Seed fixtures | **Defer** ops | No simulated expenditure outside fixtures | Integration | — | performance export |
| Reference allocators | `services/budget_reference.py` | RO generated refs | Client refs ignored | **Keep** | — | — | — | register tests |
| `entity_for_user` PE-MOH / sorted-first | `services/budget_permissions.py` | Silent PE invent / first pick | Lines 97–118 | **Correct** | Match Demand/Plan 0/1/multi | Shared scope | Seed USA | role matrix, portfolio |
| Admin role inflation | same `user_roles` | Admin = all budget roles | Lines 37–41 | **Correct** | Operational USA required | CMOM §10 | — | role gate |
| Portfolio/register/lines/review pages | `page/budget_*`, hooks | Desk funding workspace | `hooks.py` | **Keep** operational | **Defer** funding-performance dashboard if no validated consumer | Chrome | — | `ui-budget-funding-*-gate` |
| `reserve_funding` / check | `budget_check_reserve_contracts.py`, API | Mandatory finance control | Whitelist | **Keep** | Cannot skip for auto-match (CMOM §8.1) | Demand | — | check-reserve specs |
| DIA adapter APIs | `api/dia_budget_control.py` | Legacy pickers/adapters | File present | **Investigate** | Thin shim only; no dual semantics | Demands | — | DEM-INT-009 |
| Works-master budget seed | `seeds/works_master_budget_seed.py` | Skip stub (`mvp1-budget-teardown`) | File | **Keep** as no-op / **Remove** later | — | — | — | — |
| Canonical portfolio seed | `seeds/kentender_mvp_v1_portfolio.py` | 480m story | Orchestrator | **Keep** arithmetic; **Correct** strip treatments | Remove treatment rows on next contract | validate.py | Rebuild | seed validate |
| Live-bind default budget code | `public/js/budget_live_bind.js` default `MOH-BUD-…` | Demo fallback | JS | **Correct** | No silent default | UI | — | Playwright |

### Budget summary

Preserve register → activate → reserve → revise. **Remove** generic value-treatment questionnaire. **Correct** PE resolution and Admin inflation. Commitment convert remains an evidence gap for full Journey A finance closure.
