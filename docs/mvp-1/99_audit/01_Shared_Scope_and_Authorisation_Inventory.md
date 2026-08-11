# Shared Scope and Authorisation Inventory

**Document ID:** KENTENDER-ROIDA-01-1.0  
**Date:** 11 August 2026  
**Mode:** Read-only  
**Controls:** CMOM §10–§11; SWA §4.3, §9; `docs/mvp-1/00_common/00_KenTender_Procuring_Entity_and_Organisation_Scope_Model.md`

---

## 1. Repository baseline (prompt §3)

| Item | Evidence |
|---|---|
| Bench root | `/home/midasuser/frappe-bench` |
| KenTender monorepo | `apps/kentender_v1/` with app packages symlinked into `apps/kentender_*` |
| Git | Bench root: **no commits yet on `main`**; large dirty/untracked worktree — **no reliable commit SHA** |
| Frappe | `apps/frappe/frappe/__version__.py` → **16.12.0** |
| ERPNext | `apps/erpnext/erpnext/__init__.py` → **16.10.1** |
| Default site | `sites/common_site_config.json`: `default_site=kentender.midas.com`, `serve_default_site=true` |
| Installed apps (`sites/apps.txt`) | frappe, erpnext, kentender_core, kentender_strategy, kentender_budget, kentender_procurement, kentender_governance, kentender_integrations, kentender_compliance, kentender_stores, kentender_suppliers, kentender_transparency, kentender_assets, hrms, lending, chama, … |
| Migrations | Per-app `patches.txt` under each `kentender_*` package (visible in repo; DB state not mutated this pass) |
| Seed entry | `kentender_core.seeds.kentender_mvp_v1.orchestrator.run_kentender_mvp_v1` |
| UI test gates | `apps/kentender_v1/Makefile` — `ui-strategy-*`, `ui-budget-funding-*`, `ui-demands-*`, `ui-planning-*`, `ui-stitch-desk-chrome-gate` |
| Playwright | `apps/kentender_v1/tests/ui/smoke/{strategy-alignment,budget-funding,demands,planning,stitch-desk}/` |
| Missing controlling docs | CMOM/SWA still **Draft** (not PO-approved). Module REQ/Stitch/Cursor packs remain provisional per SWA §13. |

**Commands run (read-only):** `git status` / `rev-parse`; `ls`/`readlink`; file reads; ripgrep. **Not run:** migrate, seed, clear-cache, writes.

---

## 2. Organisation and scope DocTypes

| Artifact | Location | Notes |
|---|---|---|
| Procuring Entity | `kentender_core/.../doctype/procuring_entity/` | autoname `field:entity_code` |
| Organisation Unit | `kentender_core/.../doctype/organisation_unit/` | requires PE + unit type |
| Organisation Unit Type | `kentender_core/.../doctype/organisation_unit_type/` | |
| User Scope Assignment | `kentender_core/.../doctype/user_scope_assignment/` | user + role + PE + optional OU |
| Canonical PE-MOH | `kentender_core/procuring_entity_canonical.py` | `CANONICAL_MOH_ENTITY = "PE-MOH"` |
| Shared access | `kentender_core/services/org_scope_access.py` | `user_scope_rows`, `permitted_procuring_entities`, `permitted_org_units`, `can_access_owned_record` |

**Symbols not found:** `ensure_user_scope`, `get_user_scope`. Stub `utils/entity_scope.py` (`get_user_entity` → `None`) is non-enforcing.

---

## 3. Explicit fallback inventory

| Pattern | Location | Consequence | Disposition lean |
|---|---|---|---|
| Admin/Guest → PE-MOH | `budget_permissions.entity_for_user` | Invents operational PE | **Remove/Correct** |
| Unrestricted USA (`pes is None`) → PE-MOH | same | Admin/bypass PE | **Remove/Correct** |
| Multi-PE → `sorted(pes)[0]` | same | Silent first PE | **Correct** |
| Home prefer PE-MOH/PE-MOE | `home_context.resolve_home_context` / `list_available_entities` | Preferred catalogue / fallback | **Correct** |
| Strategy list without PE filter | `list_strategy_plans` when `entity_for_user()` empty | May list all plans | **Investigate/Correct** |
| Demand/Plan create 0/1/multi | `demand_creation_scope.py`, `resolve_pe_for_create` | Blocks inventing PE | **Keep** |
| Planning Admin-alone deny | `planning_permissions.require_operational_roles` | No operational invent | **Keep** |
| Demand Admin-alone deny on decisions | `demand_permissions.require_operational_roles` | No decision invent | **Keep** |
| Strategy/Budget Admin role inflation | `strategy_permissions.user_roles`, `budget_permissions.user_roles` | Admin gains all module roles | **Correct** vs CMOM §10 |
| Playwright factory default PE-MOH | `demands/api.py` prepare factories | Test-only defaults | **Keep** as fixture (not runtime ownership) |

---

## 4. Authorisation surfaces (record vs task)

CMOM §11 / SWA §4.10 require: record visibility ≠ task visibility ≠ mutation authority; unauthorised task forms absent (not merely disabled).

| Module | Record visibility | Task action projection | Mutation / API | Direct task route |
|---|---|---|---|---|
| Demands | Scoped `list_demands_for_workspace` | `allowed_actions` on review/enrich/budget loaders | Stage services throw `PermissionError` / demand errors | Review/form loaders deny unauthorised |
| Budget | `resolve_scoped_entity` + role status filters | `capabilities.can_activate` etc. | Role gates; Admin inflated | Pages load broadly for Admin |
| Strategy | Portfolio/list (PE filter weak if unset) | Readiness `allowed_actions` | Transition services | Review pages exist; capability-gated in bind |
| Planning | Workspace PE-scoped | DTO `can_*` / `rail_mode` on review | Submit/decision/approve asserts | Review page reachable if PE scoped; rail_mode `readonly` for viewers |

**Known gap:** Design pack names shared `evaluate_capability` / `get_available_actions` — **not** implemented as a single core service; each module projects locally. Whether an unauthorised user can **open** review chrome (empty actions) vs hard route denial needs Journey E verification per surface (see `06` / `08`).

---

## 5. Role / capability matrix (MVP four modules)

| Capability (business) | Role constant(s) | Primary module file |
|---|---|---|
| Strategy view/manage/approve/activate | Strategy Viewer/Officer/Manager/Reviewer; Planning Authority | `strategy_permissions.py` |
| Budget register/activate/reserve | Budget Officer/Reviewer/Authority/Viewer/Auditor | `budget_permissions.py` |
| Demand create/approve/BO confirm | Requester; Business Approver; Budget Officer; … | `demand_permissions.py` |
| Plan create/edit | Procurement Planner | `planning_permissions.py` |
| **OU contribution (prohibited)** | Planning Contributor; Head of User Department | `assert_can_submit_departmental_contribution` |
| Plan recommend | Planning Reviewer | `record_plan_decision` |
| Plan approve | Designated Approver; Accounting Officer; Planning Authority | `approve_plan_version` |
| Tender initiate | Tender Initiator | planning roles (handoff later) |

---

## 6. Reference generation

| Domain | Allocator | User-editable codes? |
|---|---|---|
| Strategy | `strategy_reference.allocate_reference` | Create ignores client `plan_code`; hierarchy codes allocated on insert; PVO catalogue codes author-controlled |
| Budget | `budget_reference.allocate_*` | `generated_reference` RO |
| Demand | `demand_codes.allocate_demand_code` | Server-generated |
| Plan / Plan Item | `_invariants.next_plan_code` / `next_plan_item_code` | Server-generated |

Seeds still plant **stable business identities** (e.g. `MOH-SP-2026-2030`, PE-MOH) — appropriate for fixtures, not for runtime silent defaults.

---

## 7. Shared disposition summary

| Artifact | Disposition | Required correction |
|---|---|---|
| PE/OU/USA DocTypes + `org_scope_access` | **Keep** | — |
| Demand/Plan strict create scope | **Keep** | — |
| Budget `entity_for_user` PE-MOH + sorted-first | **Correct** | Zero/multi deliberate selection; no Admin invent |
| Strategy/Budget Admin role inflation | **Correct** | Align with CMOM §10 |
| Home PE-MOH preference | **Correct** | Explicit selection / no invent |
| Shared capability evaluator | **Investigate** | Design pack vs local projections |
| Contribution roles/services | **Remove** (Planning wave) | See `05_…` |

See module matrices `02`–`05` for per-artifact rows.
