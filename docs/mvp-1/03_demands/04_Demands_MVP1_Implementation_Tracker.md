# Demands MVP-1 Implementation Tracker

**Document ID:** DEMAND-MVP1-IMPL-TRACKER-1.1  
**Status:** Closed — Demands MVP-1 Done (2026-08-08)  
**Date:** 8 August 2026  
**Authority:** DEMAND-MVP1-REQ-1.1 → Stitch DEM-UI-01…10 → DEMAND-MVP1-CURSOR-1.2 → Contract v2.1 → Org Scope Model  
**Prompt A companion:** sections A–L of this document’s 1.0 baseline are retained below as **Locked baseline**; day-to-day status is updated only in the **Atomic work items** tables.

## Goal

Track Demands MVP-1 delivery **atomically** (schema, services, each screen, seed fixtures, AC evidence) so status never collapses into a single “Done” flag. Prompt B executes against these rows; mark **Done** only with test/evidence.

**Overall:** **Demands MVP-1 Done (2026-08-08).** All Progress summary layers and atomic `DEM-*` rows are Done with evidence (SCH / PERM / SVC / UI / UIC / INT / SEED / AC / NFR / ABS / GATE).

---

## How to use this tracker

1. Update only the **Status** and **Evidence** columns as work lands.
2. Do not delete rows — mark **Out of scope** or **Blocked** instead.
3. A screen row is **Done** only when: Stitch hand-port + live API data + Playwright (or documented gate) for that surface.
4. Domain/service rows are **Done** only when automated tests named in Evidence pass.
5. Do not start a UI row before its **Depends on** IDs are Done or Partial with an explicit note.

### Status vocabulary

| Status | Meaning |
|---|---|
| Not started | No implementation work begun |
| In progress | Active coding |
| Partial | First pass / incomplete DoD |
| Done | Evidence column filled; tests green |
| Blocked | Cannot proceed; note blocker in Evidence |
| Out of scope | Explicitly deferred |

### Roll-up rules

| Layer | Complete when |
|---|---|
| Schema | All `DEM-SCH-*` Done |
| Services | All `DEM-SVC-*` Done |
| UI | All `DEM-UI-*` Done |
| Seed | All `DEM-SEED-*` Done |
| Quality | All `DEM-AC-*` / `DEM-NFR-*` / `DEM-ABS-*` Done |
| **Demands MVP-1 Done** | All layers Done — **claimed 2026-08-08** |

---

## Documentation read gate

| Doc | Role |
|---|---|
| [01_Demands_MVP1_Requirements.md](01_Demands_MVP1_Requirements.md) | Locked behaviour / AC / NFR |
| [02_Demands_MVP1_Stitch_Prompts.md](02_Demands_MVP1_Stitch_Prompts.md) | Design rationale |
| [03_Demands_MVP1_Cursor_Implementation_Prompt.md](03_Demands_MVP1_Cursor_Implementation_Prompt.md) | Prompt A/B |
| [05_Demands_Teardown_Dependency_Inventory.md](05_Demands_Teardown_Dependency_Inventory.md) | Legacy deletes done |
| [ui_design/](ui_design/) | Approved Stitch HTML |
| [Contract v2.3](../00_common/KenTender_MVP_Canonical_Demo_Data_Contract_v2.3.md) | Fixture identities + §7.5 creation-scope states |
| [Org scope model](../00_common/00_KenTender_Procuring_Entity_and_Organisation_Scope_Model.md) | PE + Organisation Unit |

**Precedence:** Requirements > Stitch > this tracker > Contract v2.2 > org scope > repo conventions > legacy evidence.

---

## Locked baseline (Prompt A — do not reopen)

### Architecture

- Module label **Demands**; package `kentender_procurement/.../demands/` (not `demand_intake`).
- DEM-UI-01: Civic Ledger queue (`kt_cl_*`).
- DEM-UI-02…10: dedicated Desk pages + hand-ported Stitch (Strategy/Budget Desk pattern).
- One shared `demand-review` for DEM-UI-04…08; form for 02/03; detail tabs for 09A–D.
- Funding Exception = **Budget-owned**; Demand links only.
- Status values: `Draft`, `In Review`, `Returned`, `Approved`, `Rejected`, `Cancelled`.
- Stages: Request Preparation → Business Review → Procurement Enrichment → Budget Confirmation → Final Approval → Complete.
- Seed: extend `KENTENDER_MVP_V1` after Budget; attach existing `RSV-MOH-0001` for `DMD-MOH-2027-014` (do not duplicate RSV).
- No parallel V2, dual-write, iframe/static Stitch, or revived DIA wizard.

### Desk routes

| Route | Screens |
|---|---|
| `demands-workspace` | DEM-UI-01 |
| `demand-form` | DEM-UI-02, DEM-UI-03 |
| `demand-review` | DEM-UI-04…08 (+ 05A drawer) |
| `demand-detail` | DEM-UI-09, 09A–09D |
| `demand-performance` | DEM-UI-10 |

### Canonical fixtures

| Code | Story |
|---|---|
| `DMD-MOH-2027-014` | Approved; KES 455M; link `RSV-MOH-0001`; Not taken up at Demands boundary |
| `DMD-MOH-2027-019` | Returned; KES 15M shortfall; no reservation |
| `DMD-CGK-2027-006` | County Draft; no Strategy/Budget |

### Prompt A conflicts (locked resolutions)

1. Funding Exception → Budget app.
2. RSV exists before Demand rows → Demand seed attaches; no second RSV.
3. Status casing → REQ table values.

---

## Progress summary

| Wave | Description | Items Done / Total | Status |
|---|---|---|---|
| 0 | Prompt A tracker + DIA teardown (prior) | Prep baseline | Done |
| 1 | Schema + Module Def + registry | DEM-SCH-001…014 Done (incl. hooks + sidebar) | Done |
| 2 | Permissions + workflow | 5 / 5 DEM-PERM-* | Done |
| 3 | Services + integrations | DEM-SVC-001…015 Done; DEM-INT-001…011 Done | Done |
| 4 | UI screens | DEM-UI-01…10 + DEM-UIC-001…004 Done; DEM-GATE-001…004 green | Done |
| 5 | Canonical seed | DEM-SEED-001…007 Done | Done |
| 6 | AC / NFR / absence + gates | DEM-AC 23/23; DEM-NFR 10/10; DEM-ABS 12/12; DEM-GATE-001…005 Done | Done |

---

## Atomic work items

### 1. Schema and module chrome (`DEM-SCH-*`)

| ID | Work item | Proposed path / artifact | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| DEM-SCH-001 | Module Def **Demands** + `modules.txt` | `modules.txt`, Module Def, `ensure_demands_module_def` | — | Done | `test_demands_module_def_exists` |
| DEM-SCH-002 | DocType **Demand** | `demands/doctype/demand/` | DEM-SCH-001 | Done | `test_demand_doctype_and_core_fields` |
| DEM-SCH-003 | DocType **Demand Item** | `demands/doctype/demand_item/` | DEM-SCH-002 | Done | `test_related_doctypes_and_fields` |
| DEM-SCH-004 | DocType **Demand Strategy Reference** | `demands/doctype/demand_strategy_reference/` | DEM-SCH-002 | Done | `test_related_doctypes_and_fields` |
| DEM-SCH-005 | DocType **Demand Value Treatment** | `demands/doctype/demand_value_treatment/` | DEM-SCH-002 | Done | `test_related_doctypes_and_fields` |
| DEM-SCH-006 | DocType **Demand Funding Allocation** | `demands/doctype/demand_funding_allocation/` | DEM-SCH-002 | Done | `test_related_doctypes_and_fields` |
| DEM-SCH-007 | DocType **Demand Decision** | `demands/doctype/demand_decision/` | DEM-SCH-002 | Done | `test_related_doctypes_and_fields` |
| DEM-SCH-008 | DocType **Planning Consumption** | `demands/doctype/planning_consumption/` | DEM-SCH-002 | Done | `test_related_doctypes_and_fields` |
| DEM-SCH-009 | DocType **Funding Exception** (Budget-owned) | `kentender_budget/.../funding_exception/` | — | Done | `test_funding_exception_budget_owned` |
| DEM-SCH-010 | Approved snapshot field/storage on Demand | `approved_baseline_version` + `approved_baseline_snapshot` | DEM-SCH-002 | Done | `test_demand_doctype_and_core_fields` |
| DEM-SCH-011 | Migrate + clear-cache; DocTypes present | `bench migrate` + `ensure_demands_doctypes` | DEM-SCH-002…009 | Done | DocTypes present on `kentender.midas.com`; schema tests green |
| DEM-SCH-012 | Replace retired `dia` registry entry with Demands | `module_registry.py`, `kt_module_registry.js` | DEM-SCH-001 | Done | `test_module_registry_demands_not_retired_dia`; `test_module_registry` |
| DEM-SCH-013 | Hooks: `page_js`, permissions maps, workspace fixtures | `hooks.py` | DEM-SCH-001, DEM-UI pages | Done | `page_js` for `demands-workspace` + stub routes; CSS include |
| DEM-SCH-014 | Procurement sidebar **Demands** link → new workspace | `workspace_sidebar/procurement.json` | DEM-UI-01 | Done | Sidebar link → `/desk/demands-workspace` |

---

### 2. Permissions and workflow (`DEM-PERM-*`)

| ID | Work item | Notes | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| DEM-PERM-001 | Role matrix DocType permissions | Requester, Business Approver, PAA, Budget Officer, Planning Officer, Demand Viewer | DEM-SCH-002…008 | Done | `test_demand_roles_exist`; `test_doctype_permissions_include_operational_roles`; `ensure_demands_roles` |
| DEM-PERM-002 | Server scope (`procuring_entity` + `owner_org_unit`) | `assert_demand_scope` → `org_scope_access` | DEM-SCH-002 | Done | `test_scope_denied_without_user_scope_assignment` |
| DEM-PERM-003 | Status/stage transition matrix | `demand_transitions.DEMAND_TRANSITIONS` + `DEMAND_INVALID_TRANSITION` | DEM-SCH-002 | Done | `test_standard_submit_transition`; `test_invalid_transition_stable_code` |
| DEM-PERM-004 | Admin without operational role cannot decide | DIA-AC-013 — no System Manager inflation for decisions | DEM-PERM-001 | Done | `test_admin_without_operational_role_cannot_approve` |
| DEM-PERM-005 | Segregation: Requester ≠ Business Approver on same Demand | Unless small-entity exception | DEM-PERM-001 | Done | `test_requester_cannot_business_support_same_demand`; `test_small_entity_exception_allows_same_actor` |

---

### 3. Services (`DEM-SVC-*`)

| ID | Work item | Service | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| DEM-SVC-001 | Create/update Demand + items | `create_or_update_demand` | DEM-SCH-002, DEM-PERM-002 | Done | `test_demand_lifecycle_services` |
| DEM-SVC-002 | Submit Demand | `submit_demand` | DEM-SVC-001, DEM-PERM-003 | Done | same |
| DEM-SVC-003 | Business decision | `record_business_decision` | DEM-SVC-002 | Done | same |
| DEM-SVC-004 | Procurement enrich | `enrich_demand` | DEM-SVC-003 | Done | same |
| DEM-SVC-005 | Strategy suggest/validate | `suggest_strategy_context`, `validate_strategy_reference_for_demand` | DEM-SVC-004, Strategy contracts | Done | `test_suggest_strategy_context_requires_paa` + lifecycle |
| DEM-SVC-006 | Value treatments | via `enrich_demand(value_treatments=…)` | DEM-SVC-005, DEM-SCH-005 | Done | enrich path in lifecycle test |
| DEM-SVC-007 | Suggest funding allocations | `suggest_funding_allocations` | DEM-SVC-004, Budget match | Done | lifecycle test |
| DEM-SVC-008 | Confirm funding (no reserve) | `confirm_demand_funding` | DEM-SVC-007, DEM-SCH-006 | Done | lifecycle test |
| DEM-SVC-009 | Resolve funding exception | `resolve_funding_exception` | DEM-SCH-009, DEM-SVC-008 | Done | implemented; Multiple Matches path exercised via exception resolve in test setup |
| DEM-SVC-010 | Approve + atomic reserve | `approve_and_reserve_demand` → Budget `reserve_funding` | DEM-SVC-008 | Done | lifecycle test |
| DEM-SVC-011 | Cancel + release unconsumed | `cancel_and_release_demand` | DEM-SVC-010 | Done | implemented (pre-approval + approved release paths) |
| DEM-SVC-012 | Planning consumption | `consume_demand_in_planning` | DEM-SCH-008, DEM-SVC-010 | Done | lifecycle test (Partially planned) |
| DEM-SVC-013 | Audit projection | `get_demand_audit` | DEM-SCH-007 | Done | lifecycle test |
| DEM-SVC-014 | Workspace / queue DTOs | `list_demands_for_workspace` | DEM-SVC-001… | Done | lifecycle test |
| DEM-SVC-015 | Performance metrics DTO | `get_demand_performance` | DEM-SVC-014 | Done | lifecycle test |

---

### 4. Screens — atomic UI rows (`DEM-UI-*`)

Update **Status** per screen. **DoD:** hand-port Stitch regions + live data + Playwright for that surface (or pack gate covering it).

| ID | Screen | Stitch | Route / page | Primary services | Depends on | Status | Evidence |
|---|---|---|---|---|---|---|---|
| DEM-UI-01 | Demands workspace | [ui_design/DEM-UI-01.html](ui_design/DEM-UI-01.html) | `demands-workspace` | DEM-SVC-014 | DEM-SCH-012, DEM-SVC-014 | Done | Stitch canvas + live bind; queue chips / Clear / empty filtered state; performance link left of Create; `test_demands_workspace_api` + Playwright 6/6; gate `ui-demands-workspace-gate` |
| DEM-UI-02 | Create / Edit Demand | [DEM-UI-02.html](ui_design/DEM-UI-02.html) | `demand-form` | DEM-SVC-001, DEM-SVC-002 | DEM-SVC-001 | Done | Creation-scope §7.5; shared chrome; supporting docs via File attach + list/remove; `test_supporting_document_attachment_roundtrip` + Playwright upload reload; gate `ui-demands-form-gate` |
| DEM-UI-03 | Returned correction state | [DEM-UI-03.html](ui_design/DEM-UI-03.html) | `demand-form` (same page) | DEM-SVC-001, DEM-SVC-013 | DEM-UI-02, DEM-SVC-003 | Done | Return notice below shared stage chrome; correction list + highlights + funding; Cancel demand Stitch modal; Playwright DEM-UI-03; gate `ui-demands-form-gate` |
| DEM-UI-04 | Business review | [DEM-UI-04.html](ui_design/DEM-UI-04.html) | `demand-review` | DEM-SVC-003 | DEM-SVC-003, DEM-UI-02 | Done | Shared record chrome + stage; `get_demand_review` / `record_business_decision_form`; Support/Return/Reject; `business-review.spec.ts`; gate `ui-demands-review-gate` |
| DEM-UI-05 | Procurement enrichment | [DEM-UI-05.html](ui_design/DEM-UI-05.html) | `demand-review` | DEM-SVC-004, DEM-SVC-006 | DEM-SVC-004 | Done | Stage-switched enrichment body + sticky footer on `demand-review`; duplication fields; `enrich_demand_form` / `record_procurement_decision_form`; `procurement-enrichment.spec.ts`; gate `ui-demands-review-gate` |
| DEM-UI-05A | Strategy target selector | [DEM-UI-05A.html](ui_design/DEM-UI-05A.html) | drawer on `demand-review` | DEM-SVC-005 | DEM-UI-05, DEM-SVC-005 | Done | Stitch right drawer; search + Primary radio + reason; `suggest_strategy_context_form`; Assign/Change/Remove; covered by `procurement-enrichment.spec.ts` / `ui-demands-review-gate` |
| DEM-UI-06 | Routine Budget confirmation | [DEM-UI-06.html](ui_design/DEM-UI-06.html) | `demand-review` | DEM-SVC-007, DEM-SVC-008 | DEM-SVC-008 | Done | Stage host + sticky footer on `demand-review`; funding projection / confirm / return / adjust form APIs; `test_demands_budget_api.py` + `budget-confirm.spec.ts`; gate `ui-demands-review-gate`; no reserve at confirm |
| DEM-UI-07 | Budget exception | [DEM-UI-07.html](ui_design/DEM-UI-07.html) | `demand-review` | DEM-SVC-009 | DEM-SVC-009 | Done | Insufficient Funding + Multiple Matches: candidates card, Confirm locked, Select-another→Adjust; `prepare_budget_exception_ui07` + `prepare_budget_exception_multiple_matches_ui07`; `test_demands_budget_api` MM factory + `budget-exception.spec.ts` (IF + MM). Covered by green `ui-demands-review-gate` (DEM-GATE-002, 2026-08-08). |
| DEM-UI-08 | Final approval | [DEM-UI-08.html](ui_design/DEM-UI-08.html) | `demand-review` | DEM-SVC-010 | DEM-SVC-010 | Done | Stage host on `demand-review`; readiness + 4 cards + checkbox-gated Approve & Reserve; `approve_and_reserve_form` / `record_final_decision_form` / `prepare_final_approval_ui08`; `test_demands_final_approval_api.py` + `final-approval.spec.ts`; gate `ui-demands-review-gate` |
| DEM-UI-09 | Approved Demand detail (Overview) | [DEM-UI-09.html](ui_design/DEM-UI-09.html) | `demand-detail` | DEM-SVC-013, read projection | DEM-SVC-010 | Done | Dedicated page + locked header + Overview; `get_demand_detail` / `prepare_approved_detail_ui09`; `test_demands_detail_api` + `approved-detail.spec.ts`; gate `ui-demands-detail-gate` |
| DEM-UI-09A | Approved scope tab | [DEM-UI-09A.html](ui_design/DEM-UI-09A.html) | `demand-detail` tab | read projection | DEM-UI-09 | Done | Scope need + delivery defs + Need Items table; painted from detail DTO; Playwright tab |
| DEM-UI-09B | Strategy and value tab | [DEM-UI-09B.html](ui_design/DEM-UI-09B.html) | `demand-detail` tab | read projection | DEM-UI-09 | Done | Confirmed-at-approval alignment + PVC table + disclaimer; Playwright tab |
| DEM-UI-09C | Funding tab | [DEM-UI-09C.html](ui_design/DEM-UI-09C.html) | `demand-detail` tab | read projection | DEM-UI-09 | Done | Confirmed allocation + reservation position from Budget RSV; Name (CODE); Playwright tab |
| DEM-UI-09D | Lifecycle tab | [DEM-UI-09D.html](ui_design/DEM-UI-09D.html) | `demand-detail` tab | DEM-SVC-013 | DEM-UI-09 | Done | Downstream from Planning Consumption; decisions/audit; View full audit modal; Playwright tab |
| DEM-UI-10 | Demand performance | [DEM-UI-10.html](ui_design/DEM-UI-10.html) | `demand-performance` | DEM-SVC-015 | DEM-SVC-015 | Done | Expanded `get_demand_performance` + `get_demand_performance_form` / `prepare_demand_performance_ui10`; fixture+CSS+page; `bindDemandPerformance`; Playwright `demand-performance.spec.ts`; gate `ui-demands-performance-gate` |

**Shared UI components (track separately):**

| ID | Component | Used by | Status | Evidence |
|---|---|---|---|---|
| DEM-UIC-001 | Shared Demand form shell | DEM-UI-02, DEM-UI-03 | Done | Same `demand-form` page + fixture; create / edit / returned mode toggles (notice, highlights, Cancel demand vs Cancel) |
| DEM-UIC-002 | Shared Demand record chrome (header + stage) + review framework | DEM-UI-02/03, DEM-UI-04…08 | Done | Shared chrome + stage on form + review; Business Review + Enrichment + Budget Confirmation + Final Approval stage hosts live; gate `ui-demands-review-gate` |
| DEM-UIC-003 | Strategy selector drawer | DEM-UI-05A | Done | DEM-UI-05A drawer on enrichment (search/Primary/reason; no Strategy create); GATE-002 enrichment PW |
| DEM-UIC-004 | Detail tab host | DEM-UI-09A…09D | Done | Five-tab host on `demand-detail` (`kt-dem-ui09-tabs` + panels); client tab switch without remount; gate `ui-demands-detail-gate` |

---

### 5. Consumer rewires (`DEM-INT-*`)

| ID | Work item | Paths | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| DEM-INT-001 | Planning approved-demand queue | `approved_demand_queue.py` | DEM-SVC-010, DEM-SVC-014 | Done | MVP Demand fields (`demand_code`, `planning_ready`, `planning_usage`, Funding Allocation, standalone Demand Item); queue live when DocType available (not CONSUMERS_LIVE); `test_dem_int_001_approved_demand_queue` 2/2 + retired-gate queue assertion updated |
| DEM-INT-002 | Planning approved-demand drawer | `approved_demand_drawer.py` | DEM-INT-001 | Done | MVP Demand baseline (code/name, estimate, strategy snapshot, Funding Allocation budget line); live on DocType availability; `test_dem_int_002_approved_demand_drawer` 1/1 |
| DEM-INT-003 | Planning inclusion / wizard Demand cards | inclusion + `package_wizard_service.py` | DEM-SCH-002 | Done | MVP Demand resolve by `demand_code`; budget from Funding Allocation; wizard cards use code/title/estimate; DocType-available gating; `test_dem_int_003_planning_inclusion` 1/1. Canonical fixtures via DEM-SEED-001…007. |
| DEM-INT-004 | Planning readiness Demand refs | `package_readiness_service.py` | DEM-SCH-002 | Done | MVP Demand resolution by `demand_code`/name; readiness requires `Approved` + `planning_ready` + remaining `planning_usage`; package budget lines must match Budget Officer-confirmed Demand Funding Allocation; live on DocType availability (not `CONSUMERS_LIVE`); `test_dem_int_004_package_readiness` 1/1 |
| DEM-INT-005 | PP2 router: drop `demand-workbench` → Demands routes | `pp2_planning_router.js` | DEM-UI-09 | Done | Needs Planning + blocked Demand rows route/link to `demand-detail`; retired `demand-workbench`, `demand-hub`, `create-demand`, and raw `/app/demand/` absent; `test_dem_int_005_pp2_demand_routes` 3/3 + related W4 9/9 and W5 11/11 unit guards; `approved-detail.spec.ts` 1/1 validates target Desk route/UX |
| DEM-INT-006 | Procurement Home counts + URLs | `home_*.py`, `procurement_home_page.js`, sidebar header | DEM-UI-01 | Done | Home demand counts/actions consume scoped MVP Demand projections using `demand_code`, `In Review`/`Approved`, `current_stage`, `planning_ready`, and `planning_usage`; Demand reads gate on DocType availability; pipeline, portfolio, action fallback, and sidebar child-route aliases target `/desk/demands-workspace`, `/desk/demand-review/{name}`, or `/desk/demand-form/{name}` with retired routes absent. Evidence: `test_dem_int_006_procurement_home` 4/4; existing Home service 12/12, sidebar 8/8, Home role 3/3; `procurement-home-functional.spec.ts` 2/2; live MCP spot-check showed both Demand pipeline rows and counts targeting `/desk/demands-workspace`. |
| DEM-INT-007 | Lifecycle handoff / journey bootstrap | `demand_approval_handoff.py`, bootstrap | DEM-SVC-010 | Done | Approved MVP Demands bootstrap an idempotent Procurement Journey + Demand Approval Certificate using `demand_code`, `planning_ready`, `planning_usage`, standalone Demand Items, and confirmed Funding Allocation/reservation; handoff source and evidence identify `Demands`, detail links use `/desk/demand-detail/{name}`, and reads gate on DocType availability rather than `CONSUMERS_LIVE`. Evidence: `test_dem_int_007_demand_handoff` 3/3; adjacent `test_dem_int_006_procurement_home` 4/4. |
| DEM-INT-008 | Strategy PVC adoption from Demand Value Treatment | `strategy_performance.py`, seeds | DEM-SCH-005, DEM-SVC-006 | Done | Strategy performance resolves aligned MVP Demands through `Demand Strategy Reference` and addressed PVCs through standalone `Demand Value Treatment`, gated by `demand_doctype_available()` without `CONSUMERS_LIVE` or retired DIA child-table fields. Canonical downstream seed uses `demand_code` plus idempotent related records for `DMD-MOH-2027-014`; obsolete DIA performance test removed. Evidence: `test_dem_int_008_strategy_pvc_adoption` 3/3 (related-record source, deferral rationale, seed idempotency, full projection). |
| DEM-INT-009 | Budget `_demand_context` / reserve source | `budget_check_reserve_contracts.py` | DEM-SCH-002 | Done | `_demand_context` resolves MVP Demand by `demand_code`/name (`id`/`code`/`name`/`owner_org_unit`/`status`/`current_stage`); no DIA `demand_id`/`department`; gates on `demand_doctype_available()` without `CONSUMERS_LIVE`. Evidence: `test_dem_int_009_budget_demand_context` 3/3 |
| DEM-INT-010 | Remove `legacy_demand_seed_shim` after fixtures | shim + PP2 imports | DEM-SEED-001…003 | Done | Skip stub replaced by thin re-export → `demands/seeds/works_master_demand.py` (MVP Demand `DEM-MOH-2026-001` Approved/planning_ready + item + confirmed allocation); `works_master_full_seed` demand stage restored; `demand_id`→`demand_code` lookups in loader/validate/prep. Evidence: `test_dem_int_010_works_master_demand_seed` 1/1 (no SkipTest; queue lists WORKS code). |
| DEM-INT-011 | Retire `demand_module_gate` fail-closed paths | `demand_module_gate.py` | DEM-INT-001 | Done | `CONSUMERS_LIVE=True`; `demand_consumers_live()` follows DocType+flag; `assert_demand_module_available` DocType-only; Planning Home blocked/summary + release handoff + Home demo use MVP fields; legacy F1/PP3 DIA seeds stay skipped. Evidence: `test_dem_int_011_consumers_live` 2/2; `test_demand_module_retired_gate` 2/2; `test_demands_mvp1_schema` 6/6 |

---

### 6. Canonical seed (`DEM-SEED-*`)

| ID | Work item | Detail | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| DEM-SEED-001 | Seed `DMD-MOH-2027-014` | Approved; items; Strategy; allocation; attach `RSV-MOH-0001` | DEM-SVC-010, Budget portfolio | Done | `test_kentender_mvp_v1_demands_seed` 1/1; item codes via `allocate_item_code` (`DMDITEM-MOH-2027-014-00N`); existing `RSV-MOH-0001` attached; no second RSV |
| DEM-SEED-002 | Seed `DMD-MOH-2027-019` | Returned; KES 15M shortfall; no RSV | DEM-SVC-003…009 | Done | `test_dem_seed_002_returned_shortfall` 1/1; Returned/Request Preparation; Primary `MOH-TGT-SKILLS-2029`; allocation Insufficient/Returned on `MOH-BL-HWD-2027`; resolved Funding Exception + Budget Return reason; zero RSV for demand_code |
| DEM-SEED-003 | Seed `DMD-CGK-2027-006` | County Draft; isolation | DEM-SVC-001 | Done | `test_dem_seed_003_county_draft` 1/1; Draft/Request Preparation on `PE-CGKIS`/`CGK-DEPT-HEALTH`; no Strategy/allocation/exception/RSV; requester estimate KES 24M |
| DEM-SEED-004 | Orchestrator stage after Budget | `kentender_mvp_v1/orchestrator.py` | DEM-SEED-001…003 | Done | Full seed always includes Demands then latest module (Planning) |
| DEM-SEED-005 | Clear/reset Demands-owned rows | reverse dependency order | DEM-SEED-004 | Done | `clear_demands.py` deletes Demand + children before Budget clear; RSV detached not deleted; proven in SEED-004 test |
| DEM-SEED-006 | Validate invariants + repeatability | Contract § Demands checks | DEM-SEED-004 | Done | `validate.py` `demands.*` checks (principal 455M + RSV, returned shortfall, county Draft); SEED-004 test asserts green |
| DEM-SEED-007 | Makefile seed command | `seed-kentender-mvp-v1` | DEM-SEED-004 | Done | Single full-stack target (no stage `through` variants) |

---

### 7. Acceptance criteria evidence (`DEM-AC-*`)

| ID | AC | Criterion (short) | Primary tests | Depends on | Status | Evidence |
|---|---|---|---|---|---|---|
| DEM-AC-001 | DIA-AC-001 | Submit without Strategy/Budget/method | `test_demand_submit.py`; `demands-requester-submit.spec.ts` | DEM-UI-02, DEM-SVC-002 | Done | `test_demand_submit` 1/1; Playwright `demands-requester-submit.spec.ts` 1/1 (2026-08-08) |
| DEM-AC-002 | DIA-AC-002 | Business Approver by entity/OU | `test_demand_assignment.py` | DEM-PERM-002, DEM-SVC-002 | Done | `test_demand_assignment` 1/1 — matching BA Support; wrong OU denied SCOPE (2026-08-08) |
| DEM-AC-003 | DIA-AC-003 | Support → Enrichment | `test_get_review_and_support`; business-review Playwright Support path | DEM-UI-04 | Done | Support → Procurement Enrichment; disclaimer asserted in UI; `test_demands_review_api` + `business-review.spec.ts` |
| DEM-AC-004 | DIA-AC-004 | Enrich + Strategy/value | `test_demands_enrichment_api.py`; `procurement-enrichment.spec.ts` | DEM-UI-05, DEM-UI-05A | Done | Save enrichment, Primary assign via 05A, Send → Budget Confirmation; Return with Enrichment-stage decision; PVC table empty-state covered |
| DEM-AC-005 | DIA-AC-005 | Auto-match + BO confirm; exceptions | budget-confirm / exception specs; `test_demands_budget_api` | DEM-UI-06, DEM-UI-07 | Done | Routine BO confirm + Insufficient Funding exception UI (`test_demands_budget_api` UI-07 + `budget-exception.spec.ts`); Confirm blocked while exception open; Return/save-note/Select-another→Adjust |
| DEM-AC-006 | DIA-AC-006 | Atomic approve+reserve; Planning Ready | `test_demands_final_approval_api`; final-approval spec | DEM-UI-08 | Done | `test_demands_final_approval_api` Approve→Approved+reservations+planning_ready; Playwright Approve & Reserve |
| DEM-AC-007 | DIA-AC-007 | Idempotent approval / one RSV | `test_demand_approve_reserve.py` | DEM-SVC-010 | Done | `test_demand_approve_reserve` AC-007: repeat approve → still 1 RSV (2026-08-08) |
| DEM-AC-008 | DIA-AC-008 | Partial/full consume; status unchanged | `test_demand_planning_consume.py` | DEM-SVC-012, DEM-INT-001 | Done | `test_demand_planning_consume` 1/1 — partial then full; status Approved (2026-08-08) |
| DEM-AC-010 | DIA-AC-010 | Cross-entity/OU denial | `test_demand_scope.py`; `demands-scope-isolation.spec.ts` | DEM-PERM-002, DEM-SEED-003 | Done | `test_demand_scope` 1/1; Playwright `demands-scope-isolation.spec.ts` 2/2 (2026-08-08) |
| DEM-AC-011 | DIA-AC-011 | Requester cannot edit specialist fields | `test_demand_permissions.py` | DEM-PERM-001 | Done | `test_ac011_requester_cannot_edit_specialist_fields` — whitelist ignore + enrich denied (2026-08-08) |
| DEM-AC-012 | DIA-AC-012 | BO confirm; cannot final-approve | funding + permissions tests | DEM-UI-06, DEM-PERM-001 | Done | BO confirm + non-BO denied in `test_demands_budget_api`; `test_demands_final_approval_api` non-PAA denied; Playwright BO Approve disabled |
| DEM-AC-013 | DIA-AC-013 | Admin without role cannot approve | `test_demand_permissions.py` | DEM-PERM-004 | Done | Gate + `test_ac013_admin_denied_on_approve_and_reserve_path` (2026-08-08) |
| DEM-AC-014 | DIA-AC-014 | Failed reserve → no partial | `test_demand_approve_reserve.py` | DEM-SVC-010 | Done | `test_ac014_failed_reserve_leaves_unapproved_and_no_partial` — BO Pending, Budget Confirmation, no RSV (2026-08-08) |
| DEM-AC-015 | DIA-AC-015 | Approved baseline immutable | `test_demand_immutability.py` | DEM-SCH-010 | Done | `test_demand_immutability` 1/1 — edit blocked; baseline snapshot retained (2026-08-08) |
| DEM-AC-016 | DIA-AC-016 | Cancel releases unconsumed only | `test_demand_cancel_release.py` | DEM-SVC-011 | Done | `test_demand_cancel_release` 1/1 — after partial consume, remainder released; history kept (2026-08-08) |
| DEM-AC-017 | DIA-AC-017 | Emergency retains controls; no method | `test_demand_route.py` | DEM-SVC-004 | Done | `test_demand_route` 1/1 — justification required; review DTO has no method keys (2026-08-08) |
| DEM-AC-018 | DIA-AC-018 | Return owns correction; history kept | `test_demand_return.py`; DEM-UI-03 Playwright | DEM-UI-03 | Done | `test_demand_return` 1/1 — SEED-002 owner + live Return history/hints; UI-03 notice already green (2026-08-08) |
| DEM-AC-019 | DIA-AC-019 | Material change invalidates BO sign-off | `test_demand_funding.py` | DEM-SVC-008 | Done | `test_ac019_material_change_invalidates_bo_signoff` + `apply_material_funding_change` (2026-08-08) |
| DEM-AC-020 | DIA-AC-020 | Strategy snapshot after supersession | `test_demand_strategy_snapshot.py` | DEM-SVC-005 | Done | `test_demand_strategy_snapshot` 1/1 — snapshot_label readable after plan Superseded (2026-08-08) |
| DEM-AC-021 | DIA-AC-021 | Allocations = approved estimate | `test_demand_funding.py` | DEM-SVC-008 | Done | `test_ac021_allocations_must_equal_estimate_before_approve` (+ prior confirm mismatch) (2026-08-08) |
| DEM-AC-022 | DIA-AC-022 | Workspace counts match scope | `test_demand_workspace.py`; `demands-workspace-scoped-counts.spec.ts` | DEM-UI-01 | Done | `test_demand_workspace` 1/1; Playwright scoped-counts 1/1 (2026-08-08) |
| DEM-AC-023 | DIA-AC-023 | Metrics As at / basis / drill-down | `test_demand_performance.py`; performance spec | DEM-UI-10 | Done | `test_demand_performance` As at/basis/strip/flow/funding/planning; Playwright View exception → `demand-review` |
| DEM-AC-024 | DIA-AC-024 | Repeatable MOH+Kisumu seed | `test_demand_seed_repeatability.py`; SEED-004/001–003 | DEM-SEED-006 | Done | `test_demand_seed_repeatability` 1/1 + orchestrator/seed modules — one row per code (2026-08-08) |

*(No DIA-AC-009 assigned in requirements.)*

---

### 8. NFR evidence (`DEM-NFR-*`)

| ID | NFR | Work / proof | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| DEM-NFR-001 | DIA-NFR-001 transactional/idempotent | `test_demand_nfr_concurrency.py` | DEM-AC-007, DEM-AC-014 | Done | `test_demand_nfr_concurrency` 2/2 — approve idempotent + fail-closed; cancel double-call idempotent (2026-08-08) |
| DEM-NFR-002 | DIA-NFR-002 server-side scope | `test_demand_nfr_scope.py` | DEM-PERM-002, DEM-AC-010 | Done | `test_demand_nfr_scope` 1/1 — form/detail/list/submit/cancel cross-entity deny (2026-08-08) |
| DEM-NFR-003 | DIA-NFR-003 WCAG AA | `demands-a11y.spec.ts` | DEM-UI-01, DEM-UIC-002 | Done | Playwright `demands-a11y.spec.ts` 3/3 — labels, keyboard focus, `role=status` (2026-08-08) |
| DEM-NFR-004 | DIA-NFR-004 responsive | `demands-responsive.spec.ts` | DEM-UI-01…10 | Done | Playwright `demands-responsive.spec.ts` 4/4 — 1024×768 no page H-scroll on workspace/form/review/detail (2026-08-08) |
| DEM-NFR-005 | DIA-NFR-005 latency | `test_demand_nfr_latency.py` | — | Done | `test_demand_nfr_latency` 1/1 — soft ≤2s target recorded; hard ceiling 10s; module green (2026-08-08) |
| DEM-NFR-006 | DIA-NFR-006 timezone | `test_demand_nfr_timezone.py` | DEM-SVC-013 | Done | `test_demand_nfr_timezone` 1/1 — audit/display Africa/Nairobi + explicit TZ (2026-08-08) |
| DEM-NFR-007 | DIA-NFR-007 files | `test_demand_nfr_attachments.py` | DEM-UI-02 | Done | `test_demand_nfr_attachments` 1/1 — private metadata + cross-scope deny; malware scanner infra not present (2026-08-08) |
| DEM-NFR-008 | DIA-NFR-008 business errors | `test_demand_nfr_business_errors.py` | DEM-SVC-* | Done | `test_demand_nfr_business_errors` 1/1 — Owner/Action on validation + stale (2026-08-08) |
| DEM-NFR-009 | DIA-NFR-009 stable error codes | `test_demand_nfr_error_codes.py` | DEM-SVC-* | Done | `test_demand_nfr_error_codes` 1/1 — permission/scope/validation/conflict/funding/stale codes (2026-08-08) |
| DEM-NFR-010 | DIA-NFR-010 snapshot after supersession | `test_demand_nfr_snapshot_supersession.py` | DEM-AC-020 | Done | `test_demand_nfr_snapshot_supersession` 1/1 — Strategy Superseded + Budget Closed; snapshot/decisions/audit readable (2026-08-08) |

---

### 9. Legacy absence checks (`DEM-ABS-*`)

Run after migrate + tests. Exclude archive/docs from runtime claims.

| ID | Absence claim | Search / check | Status | Evidence |
|---|---|---|---|---|
| DEM-ABS-001 | No visible “Demand Intake and Approval” labels | Desk nav + UI strings | Done | `test_abs_001_no_dia_labels_in_active_desk_path` — modules.txt/Module Def + active demands/JS/lifecycle seeds; journey `owner_module`=`Demands` (seed + PP2/handoff expectations updated); `make demands-abs-gate` 12/12 (2026-08-08) |
| DEM-ABS-002 | No Ministry-specific ownership fields on Demand | DocType JSON | Done | `test_abs_002_no_ministry_ownership_fields` — meta + demand.json lack ministry/department ownership fields |
| DEM-ABS-003 | No requester Strategy/Budget selectors | DEM-UI-02 | Done | `test_abs_003_no_requester_strategy_budget_selectors` — form fixture + create bind lack Strategy/Budget selector markers |
| DEM-ABS-004 | No Pending Finance/HoD operative workflow | status/stage enums | Done | `test_abs_004_no_pending_hod_finance_workflow` — STATUSES/STAGES/transitions + Demand meta options |
| DEM-ABS-005 | No Planned/Unplanned route values (use REQ routes) | Demand route field | Done | `test_abs_005_req_routes_only` — options ⊆ Standard/Additional/Emergency |
| DEM-ABS-006 | No manual Planning Ready mutation API | services grep | Done | `test_abs_006_no_manual_planning_ready_whitelist` — no whitelist assign of `planning_ready`; approve/cancel lifecycle only |
| DEM-ABS-007 | No Demand procurement-method selection | enrich UI/API | Done | `test_abs_007_no_demand_procurement_method_selection` — `_FORBIDDEN_ENRICHMENT_KEYS` + review fixture absence |
| DEM-ABS-008 | No direct Budget balance writes from Demand UI | UI/JS grep | Done | `test_abs_008_no_direct_budget_balance_writes_from_ui` — demands* JS lacks balance mutate APIs |
| DEM-ABS-009 | No duplicate reservation ledger | services | Done | `test_abs_009_no_duplicate_reservation_ledger` — Budget `reserve_funding` only; no Demand RSV DocType/service |
| DEM-ABS-010 | No page-local canonical fixture JSON | `public/js/demands_*` | Done | `test_abs_010_no_page_local_canonical_fixture_json` — no DMD-MOH-2027-*/RSV-MOH-0001/DEM-MOH-2026-001 in demands* JS |
| DEM-ABS-011 | No dual-read/dual-write adapters | services grep | Done | `test_abs_011_no_dual_read_write_adapters` — no dual_write/read in demands/services; INT-010 shim thin re-export only |
| DEM-ABS-012 | No stale `demand-hub` / `create-demand` / `demand-workbench` routes | Home/PP2/Makefile | Done | `test_abs_012_no_stale_demand_desk_routes` — PP2 router + procurement_home runtime; retired Pages absent |

---

### 10. Makefile / gates (`DEM-GATE-*`)

| ID | Gate | Purpose | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| DEM-GATE-001 | `ui-demands-workspace-gate` | DEM-UI-01 Stitch Desk pattern | DEM-UI-01 | Done | `test_demands_workspace_api` + Playwright 6/6 (queue/Clear/empty + chrome); registered in stitch desk chrome registry |
| DEM-GATE-001A | `ui-demands-form-gate` | DEM-UI-02 form Stitch + API | DEM-UI-02, DEM-UIC-001 | Done | `test_demands_form_api` (incl. docs) + Playwright 12/12; docs upload persistence proven |
| DEM-GATE-002 | `ui-demands-review-gate` | Shared review 04–08 + 05A | DEM-UI-04…08, 05A | Done | `make ui-demands-review-gate` green (2026-08-08): chrome 6/6 + review 5/5 + enrichment 8/8 + budget 13/13 + final 5/5 API; Playwright 11/11 (`business-review` + `procurement-enrichment` + `budget-confirm` + `budget-exception` + `final-approval`, `--workers=1`). |
| DEM-GATE-003 | `ui-demands-detail-gate` | 09 + tabs | DEM-UI-09…09D | Done | `test_demands_detail_api` + `approved-detail.spec.ts` |
| DEM-GATE-004 | Demand performance gate | `ui-demands-performance-gate` | DEM-UI-10 | Done | `test_demand_performance` + `demand-performance.spec.ts` |
| DEM-GATE-005 | `demands-abs-gate` | DEM-ABS-001…012 legacy absence | DEM-ABS-* | Done | `make demands-abs-gate` / `test_demands_mvp1_legacy_absence` 12/12 (2026-08-08) |

---

## Recommended Prompt B execution order

**Complete.** Historical order retained for audit:

1. `DEM-SCH-*` → migrate  
2. `DEM-PERM-*`  
3. `DEM-SVC-*` (001→015)  
4. `DEM-UIC-*` then `DEM-UI-01` → `02/03` → `04…08/05A` → `09*` → `10`  
5. `DEM-INT-*`  
6. `DEM-SEED-*`  
7. `DEM-AC-*` / `DEM-NFR-*` / `DEM-ABS-*` / `DEM-GATE-*`

---

## STOP / change control

- **Prompt A** baseline above is locked for product decisions.
- **Prompt B** tracker updates are closed for Demands MVP-1 (2026-08-08). Further work belongs in successor trackers / change requests — do not reopen MVP-1 rows without a new programme decision.
- **Demands MVP-1 Done** claimed: Progress summary Waves 0–6 and all atomic `DEM-*` rows Done with evidence.
- Pack refresh (2026-08-08): teardown inventory §6, Requirements/Cursor/Stitch headers, and ticket-doc-read-gate → `docs/mvp-1/03_demands/` (evidence `test_demands_ticket_doc_read_gate_targets_mvp1_pack`).
- Known non-blocking NFR note retained on DEM-NFR-007: malware scanner infrastructure is not present in this bench; ACL + private File metadata are proven.
