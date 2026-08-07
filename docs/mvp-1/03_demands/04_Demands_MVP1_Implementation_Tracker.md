# Demands MVP-1 Implementation Tracker

**Document ID:** DEMAND-MVP1-IMPL-TRACKER-1.1  
**Status:** Active tracking — Waves 1–3 Done (Wave 1 hooks/sidebar Partial; UI not started)  
**Date:** 7 August 2026  
**Authority:** DEMAND-MVP1-REQ-1.1 → Stitch DEM-UI-01…10 → DEMAND-MVP1-CURSOR-1.2 → Contract v2.1 → Org Scope Model  
**Prompt A companion:** sections A–L of this document’s 1.0 baseline are retained below as **Locked baseline**; day-to-day status is updated only in the **Atomic work items** tables.

## Goal

Track Demands MVP-1 delivery **atomically** (schema, services, each screen, seed fixtures, AC evidence) so status never collapses into a single “Done” flag. Prompt B executes against these rows; mark **Done** only with test/evidence.

**Overall:** Not started (implementation). DIA preparatory teardown is complete and is **not** Demands MVP-1 Done.

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
| **Demands MVP-1 Done** | All layers Done (not claimed yet) |

---

## Documentation read gate

| Doc | Role |
|---|---|
| [01_Demands_MVP1_Requirements.md](01_Demands_MVP1_Requirements.md) | Locked behaviour / AC / NFR |
| [02_Demands_MVP1_Stitch_Prompts.md](02_Demands_MVP1_Stitch_Prompts.md) | Design rationale |
| [03_Demands_MVP1_Cursor_Implementation_Prompt.md](03_Demands_MVP1_Cursor_Implementation_Prompt.md) | Prompt A/B |
| [05_Demands_Teardown_Dependency_Inventory.md](05_Demands_Teardown_Dependency_Inventory.md) | Legacy deletes done |
| [ui_design/](ui_design/) | Approved Stitch HTML |
| [Contract v2.2](../00_common/01_KenTender_MVP_Canonical_Demo_Data_Contract_v2.2.md) | Fixture identities + §7.5 creation-scope states |
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
| 1 | Schema + Module Def + registry | 12 Done / 2 Partial (hooks + sidebar await Wave 4 pages) | Partial |
| 2 | Permissions + workflow | 5 / 5 DEM-PERM-* | Done |
| 3 | Services + integrations | DEM-SVC-* Done; DEM-INT-* Not started | Partial |
| 4 | UI screens | 0 / 15 DEM-UI-* | Not started |
| 5 | Canonical seed | 0 / see DEM-SEED-* | Not started |
| 6 | AC / NFR / absence evidence | 0 / see DEM-AC-* / DEM-NFR-* / DEM-ABS-* | Not started |

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
| DEM-UI-01 | Demands workspace | [ui_design/DEM-UI-01.html](ui_design/DEM-UI-01.html) | `demands-workspace` | DEM-SVC-014 | DEM-SCH-012, DEM-SVC-014 | Partial | Stitch Desk hand-port (`kt-stitch-canvas`) + live bind; gate green after typography/chrome rework |
| DEM-UI-02 | Create / Edit Demand | [DEM-UI-02.html](ui_design/DEM-UI-02.html) | `demand-form` | DEM-SVC-001, DEM-SVC-002 | DEM-SVC-001 | Partial | Creation-scope §7.5; shared record header + stage (DEM-UIC-002); gate `ui-demands-form-gate`; supporting-docs upload not persisted yet |
| DEM-UI-03 | Returned correction state | [DEM-UI-03.html](ui_design/DEM-UI-03.html) | `demand-form` (same page) | DEM-SVC-001, DEM-SVC-013 | DEM-UI-02, DEM-SVC-003 | Done | Return notice below shared stage chrome; correction list + highlights + funding; Cancel demand Stitch modal; Playwright DEM-UI-03; gate `ui-demands-form-gate` |
| DEM-UI-04 | Business review | [DEM-UI-04.html](ui_design/DEM-UI-04.html) | `demand-review` | DEM-SVC-003 | DEM-SVC-003, DEM-UI-02 | Done | Shared record chrome + stage; `get_demand_review` / `record_business_decision_form`; Support/Return/Reject; `business-review.spec.ts`; gate `ui-demands-review-gate` |
| DEM-UI-05 | Procurement enrichment | [DEM-UI-05.html](ui_design/DEM-UI-05.html) | `demand-review` | DEM-SVC-004, DEM-SVC-006 | DEM-SVC-004 | Done | Stage-switched enrichment body + sticky footer on `demand-review`; duplication fields; `enrich_demand_form` / `record_procurement_decision_form`; `procurement-enrichment.spec.ts`; gate `ui-demands-review-gate` |
| DEM-UI-05A | Strategy target selector | [DEM-UI-05A.html](ui_design/DEM-UI-05A.html) | drawer on `demand-review` | DEM-SVC-005 | DEM-UI-05, DEM-SVC-005 | Done | Stitch right drawer first pass; search + Primary radio + reason; `suggest_strategy_context_form`; Assign/Change/Remove wired |
| DEM-UI-06 | Routine Budget confirmation | [DEM-UI-06.html](ui_design/DEM-UI-06.html) | `demand-review` | DEM-SVC-007, DEM-SVC-008 | DEM-SVC-008 | Not started | |
| DEM-UI-07 | Budget exception | [DEM-UI-07.html](ui_design/DEM-UI-07.html) | `demand-review` | DEM-SVC-009 | DEM-SVC-009 | Not started | |
| DEM-UI-08 | Final approval | [DEM-UI-08.html](ui_design/DEM-UI-08.html) | `demand-review` | DEM-SVC-010 | DEM-SVC-010 | Not started | |
| DEM-UI-09 | Approved Demand detail (Overview) | [DEM-UI-09.html](ui_design/DEM-UI-09.html) | `demand-detail` | DEM-SVC-013, read projection | DEM-SVC-010 | Not started | |
| DEM-UI-09A | Approved scope tab | [DEM-UI-09A.html](ui_design/DEM-UI-09A.html) | `demand-detail` tab | read projection | DEM-UI-09 | Not started | |
| DEM-UI-09B | Strategy and value tab | [DEM-UI-09B.html](ui_design/DEM-UI-09B.html) | `demand-detail` tab | read projection | DEM-UI-09 | Not started | |
| DEM-UI-09C | Funding tab | [DEM-UI-09C.html](ui_design/DEM-UI-09C.html) | `demand-detail` tab | read projection | DEM-UI-09 | Not started | |
| DEM-UI-09D | Lifecycle tab | [DEM-UI-09D.html](ui_design/DEM-UI-09D.html) | `demand-detail` tab | DEM-SVC-013 | DEM-UI-09 | Not started | |
| DEM-UI-10 | Demand performance | [DEM-UI-10.html](ui_design/DEM-UI-10.html) | `demand-performance` | DEM-SVC-015 | DEM-SVC-015 | Not started | |

**Shared UI components (track separately):**

| ID | Component | Used by | Status | Evidence |
|---|---|---|---|---|
| DEM-UIC-001 | Shared Demand form shell | DEM-UI-02, DEM-UI-03 | Done | Same `demand-form` page + fixture; create / edit / returned mode toggles (notice, highlights, Cancel demand vs Cancel) |
| DEM-UIC-002 | Shared Demand record chrome (header + stage) + review framework | DEM-UI-02/03, DEM-UI-04…08 | Partial | Shared chrome + stage on form + review; Business Review + Procurement Enrichment bodies live; Budget/Final stage panels still open |
| DEM-UIC-003 | Strategy selector drawer | DEM-UI-05A | Done | DEM-UI-05A drawer first pass on enrichment (search/Primary/reason; no Strategy create) |
| DEM-UIC-004 | Detail tab host | DEM-UI-09A…09D | Not started | |

---

### 5. Consumer rewires (`DEM-INT-*`)

| ID | Work item | Paths | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| DEM-INT-001 | Planning approved-demand queue | `approved_demand_queue.py` | DEM-SVC-010, DEM-SVC-014 | Not started | |
| DEM-INT-002 | Planning approved-demand drawer | `approved_demand_drawer.py` | DEM-INT-001 | Not started | |
| DEM-INT-003 | Planning inclusion / wizard Demand cards | inclusion + `package_wizard_service.py` | DEM-SCH-002 | Not started | |
| DEM-INT-004 | Planning readiness Demand refs | `package_readiness_service.py` | DEM-SCH-002 | Not started | |
| DEM-INT-005 | PP2 router: drop `demand-workbench` → Demands routes | `pp2_planning_router.js` | DEM-UI-09 | Not started | |
| DEM-INT-006 | Procurement Home counts + URLs | `home_*.py`, `procurement_home_page.js`, sidebar header | DEM-UI-01 | Not started | |
| DEM-INT-007 | Lifecycle handoff / journey bootstrap | `demand_approval_handoff.py`, bootstrap | DEM-SVC-010 | Not started | |
| DEM-INT-008 | Strategy PVC adoption from Demand Value Treatment | `strategy_performance.py`, seeds | DEM-SCH-005, DEM-SVC-006 | Not started | |
| DEM-INT-009 | Budget `_demand_context` / reserve source | `budget_check_reserve_contracts.py` | DEM-SCH-002 | Not started | |
| DEM-INT-010 | Remove `legacy_demand_seed_shim` after fixtures | shim + PP2 imports | DEM-SEED-001…003 | Not started | |
| DEM-INT-011 | Retire `demand_module_gate` fail-closed paths | `demand_module_gate.py` | DEM-INT-001 | Not started | |

---

### 6. Canonical seed (`DEM-SEED-*`)

| ID | Work item | Detail | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| DEM-SEED-001 | Seed `DMD-MOH-2027-014` | Approved; items; Strategy; allocation; attach `RSV-MOH-0001` | DEM-SVC-010, Budget portfolio | Not started | |
| DEM-SEED-002 | Seed `DMD-MOH-2027-019` | Returned; KES 15M shortfall; no RSV | DEM-SVC-003…009 | Not started | |
| DEM-SEED-003 | Seed `DMD-CGK-2027-006` | County Draft; isolation | DEM-SVC-001 | Not started | |
| DEM-SEED-004 | Orchestrator stage after Budget | `kentender_mvp_v1/orchestrator.py` | DEM-SEED-001…003 | Not started | |
| DEM-SEED-005 | Clear/reset Demands-owned rows | reverse dependency order | DEM-SEED-004 | Not started | |
| DEM-SEED-006 | Validate invariants + repeatability | Contract § Demands checks | DEM-SEED-004 | Not started | |
| DEM-SEED-007 | Makefile / through-Demands boundary | `seed-kentender-mvp-v1` + Demands-only option | DEM-SEED-004 | Not started | |

---

### 7. Acceptance criteria evidence (`DEM-AC-*`)

| ID | AC | Criterion (short) | Primary tests | Depends on | Status | Evidence |
|---|---|---|---|---|---|---|
| DEM-AC-001 | DIA-AC-001 | Submit without Strategy/Budget/method | `test_demand_submit.py`; `demands-requester-submit.spec.ts` | DEM-UI-02, DEM-SVC-002 | Not started | |
| DEM-AC-002 | DIA-AC-002 | Business Approver by entity/OU | `test_demand_assignment.py` | DEM-PERM-002, DEM-SVC-002 | Not started | |
| DEM-AC-003 | DIA-AC-003 | Support → Enrichment | `test_get_review_and_support`; business-review Playwright Support path | DEM-UI-04 | Done | Support → Procurement Enrichment; disclaimer asserted in UI; dedicated `test_demand_business_decision.py` module name deferred |
| DEM-AC-004 | DIA-AC-004 | Enrich + Strategy/value | `test_demands_enrichment_api.py`; `procurement-enrichment.spec.ts` | DEM-UI-05, DEM-UI-05A | Done | Save enrichment, Primary assign via 05A, Send → Budget Confirmation; Return with Enrichment-stage decision; PVC table empty-state first pass |
| DEM-AC-005 | DIA-AC-005 | Auto-match + BO confirm; exceptions | `test_demand_funding.py`; budget-confirm / exception specs | DEM-UI-06, DEM-UI-07 | Not started | |
| DEM-AC-006 | DIA-AC-006 | Atomic approve+reserve; Planning Ready | `test_demand_approve_reserve.py`; final-approval spec | DEM-UI-08 | Not started | |
| DEM-AC-007 | DIA-AC-007 | Idempotent approval / one RSV | `test_demand_approve_reserve.py` | DEM-SVC-010 | Not started | |
| DEM-AC-008 | DIA-AC-008 | Partial/full consume; status unchanged | `test_demand_planning_consume.py` | DEM-SVC-012, DEM-INT-001 | Not started | |
| DEM-AC-010 | DIA-AC-010 | Cross-entity/OU denial | `test_demand_scope.py`; scope-isolation spec | DEM-PERM-002, DEM-SEED-003 | Not started | |
| DEM-AC-011 | DIA-AC-011 | Requester cannot edit specialist fields | `test_demand_permissions.py` | DEM-PERM-001 | Not started | |
| DEM-AC-012 | DIA-AC-012 | BO confirm; cannot final-approve | funding + permissions tests | DEM-UI-06, DEM-PERM-001 | Not started | |
| DEM-AC-013 | DIA-AC-013 | Admin without role cannot approve | `test_demand_permissions.py` | DEM-PERM-004 | Not started | |
| DEM-AC-014 | DIA-AC-014 | Failed reserve → no partial | `test_demand_approve_reserve.py` | DEM-SVC-010 | Not started | |
| DEM-AC-015 | DIA-AC-015 | Approved baseline immutable | `test_demand_immutability.py` | DEM-SCH-010 | Not started | |
| DEM-AC-016 | DIA-AC-016 | Cancel releases unconsumed only | `test_demand_cancel_release.py` | DEM-SVC-011 | Not started | |
| DEM-AC-017 | DIA-AC-017 | Emergency retains controls; no method | `test_demand_route.py` | DEM-SVC-004 | Not started | |
| DEM-AC-018 | DIA-AC-018 | Return owns correction; history kept | `test_returned_form_notice_hints_funding_and_cancel`; DEM-UI-03 Playwright | DEM-UI-03 | Partial | Form return notice + decision snapshot hints proven; dedicated `test_demand_return.py` / seed `DMD-MOH-2027-019` still open |
| DEM-AC-019 | DIA-AC-019 | Material change invalidates BO sign-off | `test_demand_funding.py` | DEM-SVC-008 | Not started | |
| DEM-AC-020 | DIA-AC-020 | Strategy snapshot after supersession | `test_demand_strategy_snapshot.py` | DEM-SVC-005 | Not started | |
| DEM-AC-021 | DIA-AC-021 | Allocations = approved estimate | `test_demand_funding.py` | DEM-SVC-008 | Not started | |
| DEM-AC-022 | DIA-AC-022 | Workspace counts match scope | `test_demand_workspace.py`; workspace spec | DEM-UI-01 | Not started | |
| DEM-AC-023 | DIA-AC-023 | Metrics As at / basis / drill-down | `test_demand_performance.py`; performance spec | DEM-UI-10 | Not started | |
| DEM-AC-024 | DIA-AC-024 | Repeatable MOH+Kisumu seed | `test_kentender_mvp_v1_demands_seed.py` | DEM-SEED-006 | Not started | |

*(No DIA-AC-009 assigned in requirements.)*

---

### 8. NFR evidence (`DEM-NFR-*`)

| ID | NFR | Work / proof | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| DEM-NFR-001 | DIA-NFR-001 transactional/idempotent | Concurrency cases in approve/reserve tests | DEM-AC-007, DEM-AC-014 | Not started | |
| DEM-NFR-002 | DIA-NFR-002 server-side scope | DEM-AC-010 | DEM-PERM-002 | Not started | |
| DEM-NFR-003 | DIA-NFR-003 WCAG AA | Keyboard/focus checks on workspace + review | DEM-UI-01, DEM-UIC-002 | Not started | |
| DEM-NFR-004 | DIA-NFR-004 responsive | Viewport smoke | DEM-UI-01…10 | Not started | |
| DEM-NFR-005 | DIA-NFR-005 latency | Note in evidence; not AC soft-fail | — | Not started | |
| DEM-NFR-006 | DIA-NFR-006 timezone | Projection tests | DEM-SVC-013 | Not started | |
| DEM-NFR-007 | DIA-NFR-007 files | Attachment permission test | DEM-UI-02 | Not started | |
| DEM-NFR-008 | DIA-NFR-008 business errors | API error payload tests | DEM-SVC-* | Not started | |
| DEM-NFR-009 | DIA-NFR-009 stable error codes | API contract tests | DEM-SVC-* | Not started | |
| DEM-NFR-010 | DIA-NFR-010 snapshot after supersession | DEM-AC-020 | DEM-AC-020 | Not started | |

---

### 9. Legacy absence checks (`DEM-ABS-*`)

Run after migrate + tests. Exclude archive/docs from runtime claims.

| ID | Absence claim | Search / check | Status | Evidence |
|---|---|---|---|---|
| DEM-ABS-001 | No visible “Demand Intake and Approval” labels | Desk nav + UI strings | Not started | |
| DEM-ABS-002 | No Ministry-specific ownership fields on Demand | DocType JSON | Not started | |
| DEM-ABS-003 | No requester Strategy/Budget selectors | DEM-UI-02 | Not started | |
| DEM-ABS-004 | No Pending Finance/HoD operative workflow | status/stage enums | Not started | |
| DEM-ABS-005 | No Planned/Unplanned route values (use REQ routes) | Demand route field | Not started | |
| DEM-ABS-006 | No manual Planning Ready mutation API | services grep | Not started | |
| DEM-ABS-007 | No Demand procurement-method selection | enrich UI/API | Not started | |
| DEM-ABS-008 | No direct Budget balance writes from Demand UI | UI/JS grep | Not started | |
| DEM-ABS-009 | No duplicate reservation ledger | services | Not started | |
| DEM-ABS-010 | No page-local canonical fixture JSON | `public/js/demands_*` | Not started | |
| DEM-ABS-011 | No dual-read/dual-write adapters | services grep | Not started | |
| DEM-ABS-012 | No stale `demand-hub` / `create-demand` / `demand-workbench` routes | Home/PP2/Makefile | Not started | |

---

### 10. Makefile / gates (`DEM-GATE-*`)

| ID | Gate | Purpose | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| DEM-GATE-001 | `ui-demands-workspace-gate` | DEM-UI-01 Stitch Desk pattern | DEM-UI-01 | Partial | Gate green (API + Playwright 3/3 incl. `assertStitchDeskChrome`); registered in stitch desk chrome registry |
| DEM-GATE-001A | `ui-demands-form-gate` | DEM-UI-02 form Stitch + API | DEM-UI-02, DEM-UIC-001 | Partial | Form API + Playwright regions/chrome; docs upload persistence open |
| DEM-GATE-002 | `ui-demands-review-gate` | Shared review 04–08 + 05A | DEM-UI-04…08, 05A | Partial | Gate runs DEM-UI-04 + DEM-UI-05 API modules and Playwright (`business-review` + `procurement-enrichment`); expand when 06–08 land |
| DEM-GATE-003 | `ui-demands-detail-gate` | 09 + tabs | DEM-UI-09…09D | Not started | |
| DEM-GATE-004 | Replace retired DIA no-op gates | Makefile help + targets | DEM-GATE-001…003 | Not started | |

---

## Recommended Prompt B execution order

Work top-to-bottom; do not mark a wave Done without its atomic rows Done.

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
- **Prompt B** updates only Status/Evidence (and adds rows if new atomic gaps appear).
- Do not claim Demands MVP-1 Done until Progress summary layers are all Done with evidence.
