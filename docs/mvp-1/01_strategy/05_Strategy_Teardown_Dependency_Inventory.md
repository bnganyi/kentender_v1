# Strategy Teardown — Dependency Inventory

**Document ID:** STRATEGY-MVP1-TEARDOWN-INV-1.0  
**Branch:** `mvp1/strategy-teardown` (historical)  
**Date:** 2 August 2026 (inventory); status refreshed 6 August 2026 (STR-SUP-004)  
**Scope:** Historical Steps 1–3 inventory (delete old Strategy). MVP-1 Strategy Alignment is now shipped — see §6.  
**Authority:** STRATEGY-MVP1-REQ-1.0 §20  

App boundary: `apps/kentender_v1/kentender_strategy/` (bench symlink `apps/kentender_strategy`).

---

## 1. Files to delete

### 1.1 DocTypes (old hierarchy)

| Path | DocType |
|---|---|
| `kentender_strategy/.../doctype/strategic_plan/` | Strategic Plan |
| `kentender_strategy/.../doctype/strategy_program/` | Strategy Program |
| `kentender_strategy/.../doctype/sub_program/` | Sub Program |
| `kentender_strategy/.../doctype/strategy_objective/` | Strategy Objective (conflated output indicator) |
| `kentender_strategy/.../doctype/strategy_target/` | Strategy Target (embedded actuals) |
| `kentender_strategy/.../doctype/strategy_node/` | Strategy Node (legacy) |
| `kentender_strategy/.../doctype/strategy_navigation/` | Strategy Navigation |

### 1.2 APIs and services

- `kentender_strategy/kentender_strategy/api/landing.py`
- `kentender_strategy/kentender_strategy/api/workspace.py`
- `kentender_strategy/kentender_strategy/api/strategy_builder.py`
- `kentender_strategy/kentender_strategy/api/strategy_workflow.py`
- `kentender_strategy/kentender_strategy/api/selectors.py` (`get_active_strategy_*`)
- `kentender_strategy/kentender_strategy/services/strategy_builder.py`
- `kentender_strategy/kentender_strategy/services/strategy_hierarchy_guards.py`
- `kentender_strategy/kentender_strategy/services/strategy_readiness.py`
- `kentender_strategy/kentender_strategy/permissions.py` (old DocType permission maps)

### 1.3 Desk UI / pages / chrome

- `.../page/strategy_builder/strategy_builder.json`
- `.../workspace/strategy_management/strategy_management.json`
- `public/js/strategy_workspace.js`, `strategy_builder_page.js`, `strategy_structure_panel.js`, `strategy_review_panel.js`, `strategy_audit_panel.js`, `strategy_plan_drawer.js`, `strategic_plan.js`, `procurement_journey_impact_panel.js`, `workspace_list_selection_utils.js`
- `public/css/strategy_workspace.css`, `strategy_builder_page.css`, `strategic_plan_form.css`, `procurement_journey_impact_panel.css`
- `desktop_icon/strategy.json`, `workspace_sidebar/strategy.json`
- `public/icons/desktop_icons/**/strategy.svg` (if present)

### 1.4 Patches, seeds, tests (Strategy-owned)

- `patches.txt` + `patches/v1/*.py` (all old hierarchy backfills/migrations)
- `seeds/works_master_strategy_hierarchy.py`, `works_master_strategy_purge.py`, `seed_works_master_strategy_*.py`, `seed_portfolio_hub_mockdata.py`
- `tests/test_strategy_*.py`, `tests/test_r2_004_*.py`, `tests/test_g0_016_workspace_route_labels.py`
- Fat `install.py` / `hooks.py` doctype_js, page_js, permission_query, fixtures for deleted DocTypes

### 1.5 Playwright / UI helpers (old Strategy UX)

- `tests/ui/smoke/strategy-builder/**`
- `tests/ui/smoke/strategy-landing/**`
- `tests/ui/smoke/strategy-workbench/**`
- `tests/ui/helpers/strategyBuilder.ts`, `strategyLanding.ts` (if present)
- Related strategy pattern-lock specs referenced from Makefile `ui-workspace-pattern-gate`

---

## 2. Files to replace (planned at teardown; **now implemented**)

| MVP-1 artifact (§9 / STR-UI) | Replaces | Status |
|---|---|---|
| Versioned Strategic Plan (`plan_code`, versions) | Old Strategic Plan | Implemented |
| Programme / Sub-programme | Strategy Program / Sub Program | Implemented |
| Strategic Outcome | *(new; not Strategy Objective)* | Implemented |
| Performance Indicator | Strategy Objective-as-indicator | Implemented |
| Performance Target (definition only) | Strategy Target | Implemented |
| Public Value Objective + Applicability Trigger | *(new catalogue)* | Implemented |
| Plan Value Commitment (+ Link) | *(new)* | Implemented |
| Performance Measurement | Embedded actuals on Target | Implemented |
| Strategy Corrective Action | *(new)* | Implemented |
| Strategy Reference DTO + selector services (§16) | `get_active_strategy_*` + five-field Links | Implemented |
| STR-UI Desk surfaces (Alignment portfolio + plan tabs) | strategy-management / strategy-builder | Implemented |
| MOH fixture `MOH-SP-0001` + PVOs | `STRAT-MOH-2026` / `PROG-MOH-*` / `OBJ-MOH-*` | Implemented (`works_master_strategy_hierarchy`) |

---

## 3. Downstream files to update (surgical unlink this pass)

### 3.1 Budget

| Path | Action |
|---|---|
| `kentender_budget/.../doctype/budget/budget.json` | Remove Link `strategic_plan` |
| `.../budget_line/budget_line.json` | Remove Links `strategic_plan`, `program`, `sub_program`, `output_indicator`, `performance_target` |
| `.../budget_allocation/budget_allocation.json` | Remove strategy Links |
| `public/js/budget_hub_page.js`, `budget_workbench_page.js` | Remove Strategy `get_list` cascades / fields |
| `api/builder.py`, `landing.py`, `revision.py`, `artefacts.py`, `dia_budget_control.py` | Stop resolving Strategy titles/codes |
| `seeds/works_master_budget_seed.py`, `seed_budget_hub_demo.py` | Stop creating/linking Strategy nodes |
| `seed/fix_dangling_strategy_refs.py`, `seed_strategy_program_descriptions.py` | Delete or neutralize |

### 3.2 Demand / DIA

| Path | Action |
|---|---|
| `demand_intake/doctype/demand/demand.json` | Remove five strategy Links |
| `demand.py`, `api/dia_detail.py`, `api/landing.py` | Stop reading/writing strategy Links |
| `public/js/demand_workbench_page.js` | Remove strategy labels/selectors |

### 3.3 Planning / lifecycle / demo

| Path | Action |
|---|---|
| `procurement_planning/services/package_wizard_service.py`, `approved_demand_drawer.py` | Stop Strategy title/code lookups |
| `procurement_lifecycle/seeds/works_master_full_seed.py`, `purge_non_works_master_seed.py` | Skip strategy upsert/purge |
| `kentender_core/seeds/stable_platform_seed/{load,it_strategy,validate,clear,purge}.py` | Skip/remove Strategy load |
| `kentender_core/seeds/seed_strategy_*.py`, `reset_strategy_seed.py` | Delete or neutralize |
| `docs/data/DEMO_PLATFORM_SEED.md` | Note Strategy gate removed in teardown; MVP-1 seed is `works_master_strategy_hierarchy` / `MOH-SP-0001` |

### 3.4 Registry / nav / Makefile

| Path | Action (teardown intent) | Current status |
|---|---|---|
| `kentender_core/.../module_registry.py`, `kt_module_registry.js` | Hollow strategy routes during teardown | Restored — all Strategy `page_js` slugs (STR-SUP-003) |
| Procurement sidebar / shell routes | Keep nav label; route must not 500 | Live Alignment routes (`strategy-alignment`, plan tabs, …) |
| `Makefile` `ui-workspace-pattern-gate` | Drop strategy-pattern-lock until rebuild | Strategy Alignment UI gate: `make ui-strategy-alignment-ui-gate` |

---

## 4. Shared infrastructure to retain

- `kentender_strategy` app shell: `pyproject.toml`, `modules.txt`, `license.txt`, `__init__.py`, slim `hooks.py`
- Makefile install/symlink entry for `kentender_strategy`
- `kentender_core` PE masters / entity scoping
- Procurement Home rail (Strategy Alignment label may show retired placeholder)
- Unrelated modules (Tender CFG, bidder workspace, STD packs, Budget/DIA non-strategy surfaces)
- MVP-1 docs under `docs/mvp-1/01_strategy/`
- Historical `docs/prompts/strategy/` (reference only; not delete)

---

## 5. Destructive targets (data)

Before DocType deletion on `kentender.midas.com`:

1. Clear Link values on Budget, Budget Line, Budget Allocation, Demand pointing at Strategy DocTypes.
2. Delete all rows of: Strategic Plan, Strategy Program, Sub Program, Strategy Objective, Strategy Target, Strategy Node, Strategy Navigation.
3. Do **not** delete Procuring Entity, User, Budget headers (non-strategy fields), Demand non-strategy fields, Tender CFG, or unrelated masters.

---

## 6. Status (post-rebuild refresh — STR-SUP-004)

**Teardown complete + MVP-1 Alignment shipped.**

- Steps 1–3 destructive inventory above remains the historical record of what was removed.
- Strategy Alignment DocTypes, services (`strategy_reference`, usage, performance), Desk pages, and MOH seed `MOH-SP-0001` are live under `kentender_strategy`.
- Downstream Budget / Demand / Planning Strategy Reference wiring is tracked in `08_Strategy_Cross_Module_Lifecycle_Tracker.md` (multiple XMOD-STR items end-to-end complete).
- Remaining gaps (notifications, Tender/Award carry, full AC evidence matrix, etc.) live in that tracker — not “downstream non-functional until rebuild.”
