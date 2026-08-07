# Demands Teardown — Dependency Inventory (legacy DIA)

**Document ID:** DEMAND-MVP1-TEARDOWN-INV-1.0  
**Branch:** `mvp1/strategy-teardown`  
**Date:** 7 August 2026  
**Scope:** Preparatory teardown only (delete legacy Demand Intake and Approval; no Demands MVP-1 domain yet)  
**Authority:** DEMAND-MVP1-REQ-1.1 §5.1 / §17; Cursor Implementation Prompt (clean rebuild, no dual-write)

App boundary: `apps/kentender_v1/kentender_procurement/kentender_procurement/demand_intake/` (bench symlink `apps/kentender_procurement`).

---

## 1. Files to delete

### 1.1 DocTypes (legacy DIA domain)

| Path | DocType |
|---|---|
| `demand_intake/doctype/demand/` | Demand |
| `demand_intake/doctype/demand_item/` | Demand Item |
| `demand_intake/doctype/demand_value_treatment/` | Demand Value Treatment |

### 1.2 APIs, services, permissions, utils

- `demand_intake/api/{landing,queue_list,dia_detail,create_demand,demand_strategy,lifecycle,review,audit,chart,dia_access,dia_context,__init__}.py`
- `demand_intake/services/{readiness,demand_strategy_value,__init__}.py`
- `demand_intake/permissions/{demand_permissions,__init__}.py`
- `demand_intake/utils/__init__.py`
- `demand_intake/{__init__,README}.md` / package root after empty

### 1.3 Desk UI / pages / chrome

- `kentender_procurement/page/demand_hub/`
- `kentender_procurement/page/demand_workbench/`
- `kentender_procurement/page/create_demand/`
- `workspace/demand_intake_and_approval/`
- `workspace_sidebar/demand_intake.json`
- `public/js/demand_hub_page.js`, `demand_workbench_page.js`, `create_demand_page.js`, `demand_workspace.js`
- `public/css/demand_hub_page.css`, `demand_workbench_page.css`, `create_demand_page.css`

### 1.4 Seeds and DIA-owned tests

- `demand_intake/seeds/**` (works_master, dia_basic/extended/exceptions/empty/realistic, planning_f1, dia_seed_common)
- `demand_intake/tests/**` (all DIA domain / Playwright-backing modules)

### 1.5 Patches

- `patches/ensure_demand_intake_module_def.py`
- `patches/grant_page_read_for_demand_intake_roles.py`
- Matching `patches.txt` entries

### 1.6 Playwright / UI helpers

- `tests/ui/smoke/dia-landing/`
- `tests/ui/smoke/dia-hub/`
- `tests/ui/smoke/dia-workbench/`
- `tests/ui/smoke/create-demand/`
- `tests/ui/helpers/diaHub.ts`

---

## 2. Files to replace (later rebuild — not built in this pass)

| Planned MVP-1 artifact (DEMAND-MVP1-REQ / Stitch) | Replaces |
|---|---|
| Demands workspace (DEM-UI-01) | demand-hub / Demand Intake workspace |
| Demand capture / review surfaces (DEM-UI-02…10) | create-demand wizard + demand-workbench |
| Demand + Strategy Reference / Funding Allocation / Decision DocTypes | Demand + Demand Item + Demand Value Treatment |
| Organisation-scoped ownership (`owner_org_unit`) | requesting_department / SD-DIR fields |
| Atomic approve + reserve | HoD → Finance multi-step + manual Planning Ready |
| `KENTENDER_MVP_V1` Contract v2.1 Demand fixtures | works_master / seed_dia_* packs |

---

## 3. Downstream files to update (surgical unlink this pass)

### 3.1 Planning

| Path | Action |
|---|---|
| `procurement_planning/services/approved_demand_queue.py` | Empty queue when Demand DocType absent |
| `procurement_planning/services/approved_demand_drawer.py` | Fail-closed / empty detail |
| `procurement_planning/services/package_wizard_service.py` | Tolerate missing Demand; keep Budget check via `dia_budget_control` |
| `procurement_planning/services/package_readiness_service.py` | Skip Demand-sourced readiness rows when DocType absent |
| `procurement_planning/services/planning_release_consumption_service.py` | Guard Demand lookups |
| PP2 / planning tests that seed Demand | `skipTest` when Demand DocType absent |

### 3.2 Procurement Home / lifecycle

| Path | Action |
|---|---|
| `procurement_home/services/{home_portfolio,home_pipeline,home_actions,home_context}.py` | Zero Demand counts; retire hub URLs or no-op |
| `procurement_home/seed/seed_home_demo.py` | Skip Demand rows |
| `procurement_lifecycle/demand_approval_handoff.py` | Raise clear retired / DEMAND_MODULE_RETIRED |
| `procurement_lifecycle/demand_journey_bootstrap.py` | Fail-closed |
| `procurement_lifecycle/demand_planning_status.py` | No-op / empty |
| `procurement_lifecycle/planning_release_handoff.py` | Guard Demand.requisition_type |
| `procurement_lifecycle/seeds/purge_non_works_master_seed.py` | Drop Demand seed import |

### 3.3 Budget / Strategy / Core seeds

| Path | Action |
|---|---|
| `kentender_budget/api/dia_budget_control.py` | **Retain** (Planning still uses check/search); DIA lifecycle callers removed with DIA |
| `kentender_strategy/seeds/moh_downstream_usage.py` | Skip Demand strategy-value wiring when DocType absent |
| `kentender_strategy/tests/test_strategy_performance.py` | Skip Demand-dependent cases |
| `kentender_core/seeds/stable_platform_seed/{load,it_demand,purge}.py` | Skip Demand upsert/purge |
| `kentender_core/seeds/demo_platform_seed/{actionable,transitions}.py` | Skip DIA prerequisites / submit_demand |
| `kentender_core/seeds/dev_full_reseed.py` | Skip DIA seed steps |
| `tender_configurations/seed/demand_to_bidder_journey_sample.py` | Fail-closed or skip Demand step |

### 3.4 Registry / nav / Makefile / hooks

| Path | Action |
|---|---|
| `hooks.py` | Remove demand `page_js`, `app_include_*`, Demand permission maps, Workspace fixture name |
| `modules.txt` | Remove `Demand Intake` |
| `workspace_sidebar/procurement.json` | Drop Demand Intake sidebar link if present |
| `module_registry.py` / `kt_module_registry.js` | Mark `dia` retired / placeholder |
| `kt_desk_document_title.js` | Remove DIA titles |
| `Makefile` | Drop `dia-landing` from workspace-pattern-gate; retire `ui-create-demand-strategy-gate` body |

---

## 4. Shared infrastructure to retain

- `kentender_procurement` app shell and Planning / Tender CFG / STD Engine modules
- Procurement Home rail (Demands label may show retired / empty until rebuild)
- `kentender_budget.api.dia_budget_control` for Planning funding checks (rename later)
- MVP-1 docs under `docs/mvp-1/03_demands/`
- Historical `docs/prompts/demand intake and approval/` and `docs/prompts/dia-v2/` (reference only)

---

## 5. Destructive targets (data)

Before DocType deletion on `kentender.midas.com`:

1. Clear Package / Package Line / handoff Links that point at Demand where required for FK safety.
2. Delete all rows of: Demand Value Treatment → Demand Item → Demand.
3. Do **not** delete Procuring Entity, Organisation Unit, Budget / Budget Line, Strategy Alignment DocTypes, Tender CFG, or Planning masters.

---

## 6. Status after preparatory teardown

**Preparatory teardown completed** — legacy Demand Intake and Approval domain removed on `kentender.midas.com`.

Evidence (7 August 2026):

- DocTypes `Demand` / `Demand Item` / `Demand Value Treatment` absent
- Pages `demand-hub` / `demand-workbench` / `create-demand` absent
- Workspace `Demand Intake and Approval` and Module Def `Demand Intake` absent
- `kentender_procurement.procurement_lifecycle.tests.test_demand_module_retired_gate` — 2/2 OK
- `make ui-workspace-pattern-gate` — no-op (DIA pattern lock retired)
- `make ui-create-demand-strategy-gate` — no-op (create-demand Playwright retired)

**This is not Demands MVP-1 Done.** Prompt A/B rebuild, new DocTypes, DEM-UI Stitch ports, and Contract v2.1 Demand fixtures remain follow-on work.
