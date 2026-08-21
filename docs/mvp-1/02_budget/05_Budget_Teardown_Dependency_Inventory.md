# Budget Teardown — Dependency Inventory

**Document ID:** BUDGET-MVP1-TEARDOWN-INV-1.0  
**Branch:** `mvp1/strategy-teardown`  
**Date:** 4 August 2026  
**Scope:** Preparatory teardown only (delete legacy Budget & Funding; no new domain yet)  
**Authority:** BUDGET-MVP1-REQ-1.1 §16  
**Current status:** §§1–5 are historical preparatory teardown records. Delivery truth for the MVP-1 rebuild and remaining gaps is [`04_Budget_Cross_Module_Lifecycle_Tracker.md`](04_Budget_Cross_Module_Lifecycle_Tracker.md) (see also §6).

App boundary: `apps/kentender_v1/kentender_budget/` (bench symlink `apps/kentender_budget`).

---

## 1. Files to delete

### 1.1 DocTypes (legacy funding domain)

| Path | DocType |
|---|---|
| `kentender_budget/.../doctype/budget/` | Budget |
| `kentender_budget/.../doctype/budget_line/` | Budget Line |
| `kentender_budget/.../doctype/budget_allocation/` | Budget Allocation |
| `kentender_budget/.../doctype/budget_reservation/` | Budget Reservation |
| `kentender_budget/.../doctype/funding_source/` | Funding Source |
| `kentender_budget/.../doctype/budget_navigation/` | Budget Navigation |

### 1.2 APIs and services

- `kentender_budget/kentender_budget/api/approval.py`
- `kentender_budget/kentender_budget/api/artefacts.py`
- `kentender_budget/kentender_budget/api/audit.py`
- `kentender_budget/kentender_budget/api/builder.py`
- `kentender_budget/kentender_budget/api/dia_budget_control.py`
- `kentender_budget/kentender_budget/api/funding_check.py`
- `kentender_budget/kentender_budget/api/funding_sources.py`
- `kentender_budget/kentender_budget/api/guardrails.py`
- `kentender_budget/kentender_budget/api/landing.py`
- `kentender_budget/kentender_budget/api/movements.py`
- `kentender_budget/kentender_budget/api/review.py`
- `kentender_budget/kentender_budget/api/revision.py`
- `kentender_budget/kentender_budget/api/velocity.py`
- `kentender_budget/kentender_budget/services/budget_guards.py`
- `kentender_budget/kentender_budget/services/budget_permissions.py`
- `kentender_budget/kentender_budget/services/budget_service.py`
- `kentender_budget/kentender_budget/permissions.py`

### 1.3 Desk UI / pages / chrome

- `.../page/budget_hub/budget_hub.json`
- `.../page/budget_workbench/budget_workbench.json`
- `.../workspace/budget_management/budget_management.json`
- `public/js/budget_hub_page.js`, `budget_workbench_page.js`, `budget_workspace.js`
- `public/css/budget_hub_page.css`, `budget_workbench_page.css`
- `desktop_icon/budget.json`, `workspace_sidebar/budget.json`
- `public/icons/desktop_icons/**/budget.svg`

### 1.4 Patches, seeds, tests (Budget-owned)

- `patches.txt` entries under `patches/v1_0/*` (legacy schema migrations)
- `seeds/works_master_budget_seed.py`, `seed_works_master_budget.py`, `seed_budget_hub_demo.py`
- `seed/fix_dangling_strategy_refs.py`, `reconcile_budget_totals.py`, `reconcile_available_amounts.py`, `seed_strategy_program_descriptions.py`
- `tests/test_budget_*.py`, `tests/test_dia_budget_control_*.py`, `tests/test_demand_lifecycle_budget.py`, `tests/test_r2_005_*.py`, …
- Fat `install.py` / `hooks.py` `page_js`, `app_include_*`, fixtures, `has_permission` for deleted DocTypes

### 1.5 Playwright / UI helpers (legacy Budget UX)

- `tests/ui/smoke/budget/**`
- `tests/ui/smoke/budget-hub/**`
- `tests/ui/smoke/budget-landing/**`
- `tests/ui/smoke/budget-workspace/**`
- `tests/ui/helpers/budgetLanding.ts`
- Related budget pattern-lock specs referenced from Makefile `ui-workspace-pattern-gate`

---

## 2. Files to replace (later rebuild — not built in this pass)

| Planned MVP-1 artifact (BUDGET-MVP1-REQ / Stitch pack) | Replaces |
|---|---|
| Approved Budget baseline + Budget Lines | Old Budget / Budget Line / Allocation |
| Funding activity / reservation identity | Budget Reservation + duplicate holds |
| Strategy Reference + PVC treatments on lines | Old Strategy cascade Links |
| Finance expenditure snapshots | Manual Actual Spend |
| Controlled Revision application | Direct Active-budget editing |
| Budget Desk surfaces (Stitch `ui_design/**`) | budget-hub / budget-workbench |
| MOH fixture per REQ seed section | `BUDGET-MOH-2026` / `BUD-MOH-*-2026-*` |

---

## 3. Downstream files to update (surgical unlink this pass)

### 3.1 Demand / DIA

| Path | Action |
|---|---|
| `demand_intake/doctype/demand/demand.json` | Remove Links `budget_line`, `budget`, `funding_source` (clear values first) |
| `demand.py`, `api/lifecycle.py`, `services/readiness.py` | Stop Budget Line / reservation APIs |
| `api/dia_detail.py`, `queue_list.py`, landing | Stop budget labels |
| `public/js/demand_workbench_page.js` | Remove budget picker / `dia_budget_control` calls |

### 3.2 Planning / Home / lifecycle

| Path | Action |
|---|---|
| `procurement_planning/services/package_wizard_service.py`, `approved_demand_drawer.py`, package creation | Stop `check_available_budget` / Budget Line context |
| Package / Package Line DocTypes | Clear/remove `budget_line_id` Links |
| `procurement_home/services/home_portfolio.py` | Stop budget landing / availability |
| `procurement_lifecycle` seeds/purge/handoff | Skip Budget Line currency/code |

### 3.3 Strategy (downstream usage only)

| Path | Action |
|---|---|
| `kentender_strategy/.../seeds/moh_downstream_usage.py` | Stop linking Budget Lines |
| `strategy_contracts.py` / `strategy_performance.py` Budget rows | Tolerate empty Budget until rebuild |

### 3.4 Core seeds / demo / Makefile

| Path | Action |
|---|---|
| `kentender_core/seeds/stable_platform_seed/{load,it_budget,validate,clear,purge}.py` | Skip Budget load (`mvp1-budget-teardown`) |
| `seed_budget_*.py`, `seed_budget_line_dia.py` | Neutralize |
| `docs/data/DEMO_PLATFORM_SEED.md` | Banner: Budget gate removed pending rebuild |
| `Makefile` `ui-workspace-pattern-gate` | Drop budget-pattern-lock until rebuild |
| `module_registry` / `kt_module_registry.js` | Point budget module to retired/placeholder |

---

## 4. Shared infrastructure to retain

- `kentender_budget` app shell: `pyproject.toml`, `modules.txt`, `license.txt`, `__init__.py`, slim `hooks.py`
- Makefile install/symlink entry for `kentender_budget`
- `kentender_procurement` `required_apps` including `kentender_budget`
- Procurement Home rail label **Budget & Funding** → placeholder Workspace **Budget Management**
- Unrelated modules (Strategy Alignment MVP-1, Tender CFG, bidder, STD packs, DIA non-budget surfaces)
- MVP-1 docs under `docs/mvp-1/02_budget/`
- Historical `docs/prompts/budget/` and `docs/prompts/budget management v2/` (reference only; not delete)

---

## 5. Destructive targets (data)

Before DocType deletion on `kentender.midas.com`:

1. Clear Link values on Demand, Procurement Package, Procurement Package Line pointing at Budget / Budget Line / Funding Source.
2. Delete all rows of: Budget Reservation → Budget Allocation → Budget Line → Budget → Funding Source → Budget Navigation.
3. Known stable codes: `BUDGET-MOH-2026`, `BUD-MOH-IT-2026-001`, `BUD-MOH-INFRA-2026-001`, `BUDGET-DOE-2026`, `BUDGET-SDT-2026`.
4. Do **not** delete Procuring Entity, User, Demand non-budget fields, Strategy Alignment MVP-1 DocTypes, Tender CFG, or unrelated masters.

---

## 6. Status after preparatory teardown

**Preparatory teardown completed** — legacy Budget & Funding domain removed.

**MVP-1 Budget core rebuild is in place** — DocTypes, services, Desk portfolio screens, and the working fixture `KENTENDER_MVP_V1` / `MOH-BUD-2027-2028` (Contract v2.0) have been restored under the implementation pack.

**Completion level:** approaching **Budget Core Complete**. This is **not** Integration Ready or End-to-End Complete.

Remaining funding lifecycle provider work, consumer wiring, and support gaps are tracked only in [`04_Budget_Cross_Module_Lifecycle_Tracker.md`](04_Budget_Cross_Module_Lifecycle_Tracker.md) (`XMOD-BUD-*`, `BUD-SUP-*`). Do not treat this inventory as a live Done claim for those rows.
