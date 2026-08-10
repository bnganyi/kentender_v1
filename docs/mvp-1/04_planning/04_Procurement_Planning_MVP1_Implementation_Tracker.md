# Procurement Planning MVP-1 Implementation Tracker

**Document ID:** PLANNING-MVP1-IMPL-TRACKER-1.0  
**Status:** Active — Gate 00–04 Done; next Gate 05 (approval)  
**Date:** 10 August 2026  
**Authority:** `PLANNING-MVP1-REQ-1.4` → approved Stitch `PLN-UI-01`…`10` → `PLANNING-MVP1-CURSOR-1.2` → Canonical Demo Data Contract v2.4 → Org Scope Model  

## Goal

Track Procurement Planning MVP-1 delivery **atomically** (schema, services, each screen, seed fixtures, AC evidence) so status never collapses into a single “Done” flag. Execute against Cursor Gates 00–08; mark **Done** only with automated test evidence.

**User mandate:** Zero PP2 Planning code. Full retirement (`PLN-RET-*` / [GATE_PP2_RETIREMENT.md](GATE_PP2_RETIREMENT.md) v1.2) completed before Gate 01. No temporary preserve. No coexistence.

**Overall:** Gate 00 Done. RET-001…005 Done. Gate 01 Done. Gate 02 Done. Gate 03 Done ([GATE_03_WORKSPACE_AND_REGISTER.md](GATE_03_WORKSPACE_AND_REGISTER.md)). Gate 04 Done ([GATE_04_DEMAND_AND_PLAN_ITEM_EDITOR.md](GATE_04_DEMAND_AND_PLAN_ITEM_EDITOR.md)). **Next:** Gate 05 — `PLN-UI-07`…`08` / approval.

---

## How to use this tracker

1. Update only the **Status** and **Evidence** columns as work lands.
2. Do not delete rows — mark **Out of scope** or **Blocked** instead.
3. A screen row is **Done** only when: Stitch hand-port + live API data + Playwright (or named Makefile gate) for that surface.
4. Domain/service rows are **Done** only when automated tests named in Evidence pass.
5. Do not start a UI row before its **Depends on** IDs are Done or Partial with an explicit note.
6. Do not claim MVP-1 Done from domain tests or title-only layout guards alone.

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
| Gate 00 | Replacement boundary approved |
| Schema | All `PLN-SCH-*` Done |
| Permissions | All `PLN-PERM-*` Done |
| Services | All `PLN-SVC-*` Done |
| UI | All `PLN-UI-*` + `PLN-UIC-*` Done |
| Seed | All `PLN-SEED-*` Done |
| Quality | All `PLN-AC-*` / `PLN-NFR-*` / `PLN-GATE-08` Done |
| PP2 retirement | All `PLN-RET-*` Done; `PLN-ABS-*` via RET-005 |
| **Planning MVP-1 Done** | Build layers Done **and** RET-001…005 Done with evidence |

---

## Documentation read gate

| Doc | Role |
|---|---|
| [Procurement_Planning_MVP1_Requirements_v1.4.md](Procurement_Planning_MVP1_Requirements_v1.4.md) | Locked behaviour / FR / AC / NFR |
| [Procurement_Planning_MVP1_Stitch_Prompts_v1.4.md](Procurement_Planning_MVP1_Stitch_Prompts_v1.4.md) | Approved design prompts |
| [Procurement_Planning_MVP1_Cursor_Implementation_Pack_v1.2.md](Procurement_Planning_MVP1_Cursor_Implementation_Pack_v1.2.md) | Ordered Gates 00–08 |
| [GATE_00_REPLACEMENT_BOUNDARY.md](GATE_00_REPLACEMENT_BOUNDARY.md) | Approved keep/replace/retire inventory |
| [GATE_PP2_RETIREMENT.md](GATE_PP2_RETIREMENT.md) | Separate PP2 retirement programme (`PLN-RET-*`) |
| [ui_design/](ui_design/) | Approved Stitch HTML `PLN-UI-01`…`10` |
| [Contract v2.4](../00_common/KenTender_MVP_Canonical_Demo_Data_Contract_v2.4.md) | Fixture identities + `SCN-PLN-ADD-001` |
| [Org scope model](../00_common/00_KenTender_Procuring_Entity_and_Organisation_Scope_Model.md) | PE + Organisation Unit |

**Precedence on conflict:** Requirements v1.4 > Cursor pack v1.2 > Canonical Demo Data Contract v2.4 > approved Stitch outputs and Stitch prompts v1.4 > repo conventions that do not conflict.

**Pack authority:** `apps/kentender_v1/docs/mvp-1/04_planning/` is authoritative for Procurement Planning MVP-1. Historical `docs/prompts/procurement planning v2/` is **reference only** — do not treat PP2 tracker Done rows as MVP-1 Done; do not preserve Inclusion / Package / Release workbenches.

---

## Locked baseline (do not reopen without REQ revision)

### Architecture

- Module label **Procurement Planning**.
- Clean replacement of disposable legacy Planning structures; **no dual-write**.
- Plan Item is the working unit; no user-facing Inclusion, Package, Package Line, Release Package or Consumption.
- Logical Plan lifecycle: `Open` / `Closed` / `Cancelled`.
- Plan Version: `Draft` / `In review` / `Returned` / `Approved` / `Superseded` / `Cancelled`.
- Plan Item baseline: `Proposed` / `Active` / `Removed`.
- Separate projections: validation, departmental contribution, publication, Tender take-up.
- One logical Plan per PE + FY; at most one current Approved version; at most one open Draft successor.
- UI: native Desk shell + hand-ported Stitch main content; **no iframe / static Stitch runtime / second nav shell**.
- Plan registration: PE, financial year, title, currency, coordinating procurement unit — **no Budget context**.
- Service and business-record names follow Requirements v1.4 exactly (Cursor pack v1.2).

### Canonical fixtures

| Code | Story |
|---|---|
| `PLN-MOH-2027-001` | Open logical Plan; PE-MOH; FY 2027/28 |
| `PLN-MOH-2027-001-V1` | Current Approved Version 1; KES 455,000,000 |
| `PPI-MOH-2027-021` | Active; digital health infrastructure; `RSV-MOH-0001`; Tender `TND-MOH-2027-008` |
| `SCN-PLN-ADD-001` | Correct/approve `DMD-MOH-2027-019` → Draft V2 → Proposed `PPI-MOH-2027-022` (KES 80M) → total KES 535M |

### Desk pattern (target)

Hand-port Stitch into Desk pages under the Procurement shell (exact route names confirmed in Gate 00 audit). Reuse shared Stitch Desk chrome (`kt-stitch-canvas`) for portfolio surfaces.

### Prompt / pack conflicts (locked resolutions)

1. Service and business-record names → Requirements v1.4 (Cursor pack v1.2).
2. Plan-header Budget context → prohibited (`PLN-FR-014B`).
3. Stitch HTML `PLN-UI-01`…`10` → approved visual contract; hand-port main content only.
4. Historical PP2 pack → reference only.
5. Gate 00 boundary → [GATE_00_REPLACEMENT_BOUNDARY.md](GATE_00_REPLACEMENT_BOUNDARY.md): greenfield MVP Plan/Item model; no Plan Item↔Package dual-write; Package + WORKS seed temporarily preserved for TM/PLC only.
6. PP2 retirement → [GATE_PP2_RETIREMENT.md](GATE_PP2_RETIREMENT.md) v1.1: **full removal before Gate 01**; no Package/WORKS preserve; zero legacy Planning code.

---

## Progress summary

| Wave | Description | Items Done / Total | Status |
|---|---|---|---|
| 0 | Pack baselines (REQ / Stitch / Cursor / seed) | Prep baseline | Done |
| 1 | Gate 00 — repo audit + replacement boundary | 1 / 1 | Done |
| R | PP2 full removal before Gate 01 (`PLN-RET-*`) | 5 / 5 | Done |
| 2 | Schema + permissions | 12 / 13 SCH + 5 / 5 PERM | PERM Done; SCH-013 deferred |
| 3 | Services + integrations | 0 / 16 SVC + 6 INT | Partial (Gate 01 thin SVCs + Gate 02 scope) |
| 4 | UI screens + chrome | 0 / 10 UI + 2 UIC | Not started |
| 5 | Canonical seed + SCN-PLN-ADD-001 | 3 / 4 | SEED-001…003 Done; SEED-004 deferred |
| 6 | AC / NFR / ABS + final gate | 0 / 34 AC + 12 NFR + ABS + gates | Not started |

---

## Atomic work items

### 0. Gate 00 — audit and replacement (`PLN-GATE-*`)

| ID | Work item | Notes | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-GATE-00 | Read-only Planning inventory; keep/replace/retire table; approved clean replacement boundary | Cursor Prompt 00; no domain/UI code in this gate | Pack baselines | Done | [GATE_00_REPLACEMENT_BOUNDARY.md](GATE_00_REPLACEMENT_BOUNDARY.md) (Approved 2026-08-09); audit: live stack is PP2 Inclusion/Package/Release; MVP-1 schema absent; Package+WORKS seed temporary preserve for TM/PLC only |

---

### 1. Schema and module chrome (`PLN-SCH-*`)

| ID | Work item | Proposed path / artifact | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-SCH-001 | Module / registry / sidebar entry for **Procurement Planning** | `module_registry`, Procurement sidebar | PLN-GATE-00 | Done | `form_doctype=Procurement Plan`; `test_planning_mvp1_schema.test_module_registry_points_at_plan` |
| PLN-SCH-002 | DocType **Procurement Plan** | logical PE/FY container | PLN-SCH-001 | Done | Reshaped MVP lifecycle; [GATE_01_DOMAIN_FOUNDATION.md](GATE_01_DOMAIN_FOUNDATION.md) |
| PLN-SCH-003 | DocType **Procurement Plan Version** | Draft/review/approved versions | PLN-SCH-002 | Done | `test_planning_mvp1_schema` |
| PLN-SCH-004 | DocType **Procurement Plan Item** | stable operational identity | PLN-SCH-002 | Done | `test_planning_mvp1_schema` |
| PLN-SCH-005 | DocType **Procurement Plan Item Version** | version-specific planning values | PLN-SCH-004 | Done | `test_planning_mvp1_schema` |
| PLN-SCH-006 | DocType **Plan Demand Allocation** | Draft / Effective / Reversed | PLN-SCH-004 | Done | `test_planning_mvp1_schema` |
| PLN-SCH-007 | DocType **Departmental Submission** | OU sign-off per Plan Version | PLN-SCH-003 | Done | Schema present (services later) |
| PLN-SCH-008 | DocType **Plan Decision** | review / return / approval evidence | PLN-SCH-003 | Done | Written on `approve_plan_version` |
| PLN-SCH-009 | DocType **Plan Validation Result** | issue-led validation runs | PLN-SCH-003 | Done | Schema present |
| PLN-SCH-010 | DocType **Publication Event** | publication/export evidence | PLN-SCH-003 | Done | Schema present |
| PLN-SCH-011 | DocType **Planning Handoff Snapshot** | immutable Tender take-up input | PLN-SCH-004 | Done | Schema present |
| PLN-SCH-012 | Migrate + clear-cache; MVP DocTypes present | `bench migrate` | PLN-SCH-002…011 | Done | migrate 2026-08-09; schema 5/5 OK |
| PLN-SCH-013 | Hooks: `page_js`, permissions maps, workspace fixtures | `hooks.py` | PLN-SCH-001, PLN-UI pages | Done | Gate 03: `page_js` + `app_include_*` for planning fixtures/CSS; layout guard |

---

### 1A. PP2 full removal (`PLN-RET-*`) — before Gate 01

Authority: [GATE_PP2_RETIREMENT.md](GATE_PP2_RETIREMENT.md) v1.2. **RET-005 Done — Gate 01 unblocked (and completed).**

| ID | Work item | Prerequisite | Status | Evidence |
|---|---|---|---|---|
| PLN-RET-001 | Freeze: no new PP2 Planning features | PLN-GATE-00 | Done | [GATE_PP2_RETIREMENT.md](GATE_PP2_RETIREMENT.md) |
| PLN-RET-002 | Remove all PP2 Planning UX, pages, router, APIs | PLN-RET-001 | Done | Deleted `pp2_*`/`pp3_*` assets, planning-hub / package wizard / package-detail pages; stripped hooks `app_include_*` / `page_js` |
| PLN-RET-003 | Remove/replace Package callers in Home, TM, PLC, TCFG, seeds | PLN-RET-002 | Done | Home/TCFG/PLC/stable seeds cut; Package Link→Data; create-from-package / eligible-package APIs closed or empty |
| PLN-RET-004 | Delete Package/Inclusion/Release DocTypes, pp2_constants, WORKS/F1/PP3 Planning seeds, PP2 tests/Playwright | PLN-RET-003 | Done | Tree delete under `procurement_planning/` (shell Plan kept); migrate orphan drop; patch `mvp1_drop_pp2_planning_doctypes` |
| PLN-RET-005 | `PLN-ABS-*` + legacy-reference search green | PLN-RET-004 | Done | `test_pp2_full_removal_abs` 4/4 OK (2026-08-09); Gate 01 unblocked |

---

### 2. Permissions and scope (`PLN-PERM-*`)

| ID | Work item | Notes | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-PERM-001 | Planning operational roles + DocType permissions | Contributor, HoD, Planner, Reviewer, AO, Designated Approver, Tender Initiator, Viewer | PLN-SCH-002…011 | Done | `test_planning_roles_exist` 3/3; `ensure_planning_roles` patch |
| PLN-PERM-002 | Server PE + OU scope on every read/mutation | No role without scope; no Admin fallback | PLN-PERM-001 | Done | `planning_permissions.assert_planning_scope`; matrix + isolation tests |
| PLN-PERM-003 | Zero- / single- / multi-PE selection pattern | Matches Demands scope pattern | PLN-PERM-002 | Done | `test_planning_pe_scope_selection` 3/3 |
| PLN-PERM-004 | Admin without operational role cannot prepare/review/approve | PLN-AC-019 | PLN-PERM-001 | Done | `test_planning_permissions_matrix` admin deny |
| PLN-PERM-005 | Cross-entity isolation (MOH vs County) | UI + API | PLN-PERM-002 | Done | `test_planning_cross_entity_isolation` 3/3; helpers `planningRoles.ts` |

---

### 3. Services (`PLN-SVC-*`)

Exact names from Requirements v1.4 / Cursor pack v1.2.

| ID | Work item | Service | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-SVC-001 | Workspace projection | `get_planning_workspace` | PLN-SCH-012, PLN-PERM-002 | Done | `test_planning_workspace_api` + whitelist; Gate 03 |
| PLN-SVC-002 | Register annual plan | `create_procurement_plan` | PLN-SCH-012, PLN-PERM-003 | Done | Whitelist + create-scope DTO + register UI; `test_planning_register_api` |
| PLN-SVC-003 | Eligible Demands queue | `list_eligible_demands` | PLN-SVC-001 | Done | `test_list_eligible_demands` |
| PLN-SVC-004 | Add Demand → Plan Item + Draft allocation | `add_demand_to_plan` | PLN-SVC-003 | Done | Pack v1.3: one Demand→one item default; `formation_mode` separate; no cosmetic Keep separate; `test_add_demand_to_plan_gate04` |
| PLN-SVC-005 | Update Plan Item decisions | `update_plan_item` | PLN-SVC-004 | Done | `test_update_plan_item` (AC-012 / AC-016) |
| PLN-SVC-006 | Aggregation of compatible allocations | `aggregate_plan_allocations` | PLN-SVC-005 | Done | `test_aggregate_plan_allocations` (AC-013 / AC-014) |
| PLN-SVC-007 | Issue-led validation | `validate_plan` | PLN-SVC-005 | Done | `test_validate_plan` (Draft issue-led; Ready not user-settable) |
| PLN-SVC-008 | Departmental contribution submit | `submit_departmental_contribution` | PLN-SVC-007, PLN-SCH-007 | Not started | |
| PLN-SVC-009 | Submit for review | `submit_plan_for_review` | PLN-SVC-008 | Not started | |
| PLN-SVC-010 | Record plan decision | `record_plan_decision` | PLN-SVC-009 | Not started | |
| PLN-SVC-011 | Approve plan version (atomic) | `approve_plan_version` | PLN-SVC-010 | Partial | Gate 01 atomic approve + Effective once; full review chain later |
| PLN-SVC-012 | Open/create Draft revision | `open_or_create_plan_revision` | PLN-SVC-011 | Partial | Gate 01 single-Draft successor + carry-forward |
| PLN-SVC-013 | Cancel Draft revision | `cancel_plan_revision` | PLN-SVC-012 | Not started | |
| PLN-SVC-014 | Publish approved plan | `publish_approved_plan` | PLN-SVC-011 | Not started | |
| PLN-SVC-015 | Tender take-up handoff | `create_tender_from_plan_item` | PLN-SCH-011, PLN-SVC-011 | Not started | |
| PLN-SVC-016 | Implementation / audit projections | `get_plan_implementation`, `get_plan_audit` | PLN-SVC-011 | Not started | |

---

### 4. Integrations (`PLN-INT-*`)

| ID | Work item | Notes | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-INT-001 | Demands: eligibility + effective Planning Consumption on approval | No Demand mutation of scope/ownership | PLN-SVC-004, PLN-SVC-011 | Partial | Eligibility + add without Demand mutation Done; consumption on approve remains Gate 05 |
| PLN-INT-002 | Budget: revalidate reservation / funding; no balance mutation | Read-only funding context | PLN-SVC-007, PLN-SVC-015 | Not started | |
| PLN-INT-003 | Strategy / Plan Value Commitments: immutable snapshots via Demand | No Strategy reassignment in Planning | PLN-SVC-005 | Not started | |
| PLN-INT-004 | Core scope: PE / OU / authority resolution | — | PLN-PERM-002 | Not started | |
| PLN-INT-005 | Tender: immutable handoff; no Release Package | — | PLN-SVC-015 | Not started | |
| PLN-INT-006 | Notifications + audit reuse | Shared infra where compliant | PLN-SVC-008…015 | Not started | |

---

### 5. UI screens (`PLN-UI-*` / `PLN-UIC-*`)

| ID | Work item | Stitch | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-UI-01 | Procurement Planning workspace | `PLN-UI-01.html` | PLN-SVC-001 | Done | `planning-workspace` + Workspace redirect; Playwright workspace spec |
| PLN-UI-02 | Register annual plan (multi-PE) | `PLN-UI-02.html` | PLN-SVC-002, PLN-PERM-003 | Done | zero/single/multi + create → builder; inline errors |
| PLN-UI-03 | Empty Draft plan builder | `PLN-UI-03.html` | PLN-SVC-001 | Done | empty-state CTA; Add Demand opens UI-04 |
| PLN-UI-04 | Add approved Demand dialog | `PLN-UI-04.html` | PLN-SVC-003, PLN-SVC-004 | Done | Pack v1.3 single-select source; Plan Need Items separately secondary; `planning-add-demand.spec.ts` |
| PLN-UI-05 | Plan builder with Plan Item | `PLN-UI-05.html` | PLN-UI-04, PLN-SVC-005 | Done | Populated builder + Run validation; `planning-builder.spec.ts` |
| PLN-UI-06 | Plan Item editor | `PLN-UI-06.html` | PLN-SVC-005, PLN-SVC-007 | Done | Completes existing item; Add another Demand CTA; no aggregation radios; editor Playwright |
| PLN-UI-07 | Departmental contribution drawer | `PLN-UI-07.html` | PLN-SVC-008 | Not started | |
| PLN-UI-08 | Consolidated review and approval | `PLN-UI-08.html` | PLN-SVC-009…011 | Not started | |
| PLN-UI-09 | Approved plan and implementation | `PLN-UI-09.html` | PLN-SVC-016, PLN-SVC-014 | Not started | |
| PLN-UI-10 | Draft revision overview | `PLN-UI-10.html` | PLN-SVC-012, PLN-UI-06 | Not started | |
| PLN-UIC-001 | Stitch Desk chrome registry + `kt-stitch-canvas` + `assertStitchDeskChrome` | Shared chrome gate | PLN-UI-01…10 | Partial | Gate 03–04: workspace/register/builder/editor registered; UI-04 dialog chrome in add-demand Playwright; UI-07…10 later |
| PLN-UIC-002 | Inline form errors (`kt_form_errors`); no Message dialog for field validation | Form error rule | PLN-UI-02, PLN-UI-06 | Done | Register + Plan Item editor (`planning-plan-item-editor.spec.ts`) |

---

### 6. Canonical seed (`PLN-SEED-*`)

| ID | Work item | Notes | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-SEED-001 | Extend `KENTENDER_MVP_V1` Planning baseline (Contract v2.4) | Idempotent reset | PLN-SCH-012, PLN-PERM-001 | Done | Full seed always through Planning; `test_planning_mvp_seed_contract` 4/4 |
| PLN-SEED-002 | `SCN-PLN-ADD-001` setup / run / reset | No duplicate on second run | PLN-SEED-001, PLN-SVC-012 | Done | `test_scn_pln_add_001` 4/4 (SVC-012 not required for seed runner) |
| PLN-SEED-003 | Seed validation: arithmetic, ownership, reservation lineage, current version | Contract verification | PLN-SEED-001 | Done | `validate.py` planning checks; seed contract tests |
| PLN-SEED-004 | Isolated pre-approval UI fixtures (do not contradict permanent Approved V1 seed) | Stitch journey states | PLN-SEED-001 | Done | `pln_seed_004_empty_draft.py` (`PLN-MOH-UI-DRAFT-001` / FY 2029/30) |

---

### 7. Acceptance criteria (`PLN-AC-*`)

Trace every Requirements §18 criterion. Evidence may be service, Playwright, or seed tests.

#### 7.1 Core journey

| ID | Criterion (summary) | Primary proof | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-AC-001 | Register annual plan; no technical codes | `create_procurement_plan` + PLN-UI-02 | PLN-UI-02, PLN-SVC-002 | Done | API + register Playwright happy path → builder |
| PLN-AC-002 | Queue: Approved, Planning Ready, not fully planned | `list_eligible_demands` | PLN-SVC-003, PLN-UI-04 | Done | Service negatives + UI-04 dialog |
| PLN-AC-003 | Add Demand → Plan Item + Draft allocation; no Demand/RSV mutation | `add_demand_to_plan` | PLN-SVC-004, PLN-INT-001 | Done | `test_add_demand_to_plan_gate04` + add-demand Playwright |
| PLN-AC-004 | Complete method/schedule/lotting/statutory in editor (source selected at UI-04) | PLN-UI-06 | PLN-UI-06, PLN-SVC-005 | Done | `test_update_plan_item` + editor surface; formation at UI-04 |
| PLN-AC-005 | HoD submits unit contribution (drawer, not separate workspace) | PLN-UI-07 | PLN-UI-07, PLN-SVC-008 | Not started | |
| PLN-AC-006 | Consolidate contributions; resolve aggregation candidates | PLN-SVC-006 + review | PLN-SVC-006, PLN-UI-08 | Not started | |
| PLN-AC-007 | Review / AO / Designated Approver per configured route | `record_plan_decision` | PLN-SVC-010, PLN-UI-08 | Not started | |
| PLN-AC-008 | Approval locks version; Draft allocations effective once | `approve_plan_version` | PLN-SVC-011 | Not started | |
| PLN-AC-009 | Tender from Active item via one handoff snapshot | `create_tender_from_plan_item` | PLN-SVC-015, PLN-INT-005 | Not started | |
| PLN-AC-010 | Implementation derives Tender/actuals; baseline immutable | `get_plan_implementation` | PLN-SVC-016, PLN-UI-09 | Not started | |

#### 7.2 Legal and control

| ID | Criterion (summary) | Primary proof | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-AC-011 | Cannot exceed approved/funded/unplanned scope | allocation tests | PLN-SVC-004, PLN-SVC-007 | Done | Over-allocation rejected in `test_add_demand_to_plan_gate04` |
| PLN-AC-012 | Open tender default; alternative needs grounds + evidence | method rules | PLN-SVC-005, PLN-UI-06 | Done | `test_update_plan_item` + editor inline errors |
| PLN-AC-013 | Anti-splitting blocked/escalated; no client bypass | server checks | PLN-SVC-006, PLN-SVC-007 | Done | `test_aggregate_plan_allocations` |
| PLN-AC-014 | Aggregated allocations retain Demand/Budget/RSV lineage | aggregation tests | PLN-SVC-006, PLN-INT-002 | Done | Aggregate lineage test (Budget revalidate remains Gate 05+) |
| PLN-AC-015 | Cannot approve while statutory minimums unmet | validation + approve | PLN-SVC-007, PLN-SVC-011 | Partial | Validate may surface Needs attention; approve block stays Gate 05 |
| PLN-AC-016 | Multi-year: justification + annual funding schedule | Plan Item Version fields | PLN-SVC-005 | Done | `test_update_plan_item` multi-year errors |
| PLN-AC-017 | Actual dates derived; do not overwrite planned | implementation projection | PLN-SVC-016 | Not started | |
| PLN-AC-018 | No cross-PE/OU read or mutate via UI or API | scope matrix | PLN-PERM-002, PLN-PERM-005 | Not started | |
| PLN-AC-019 | Admin without Planning role/scope cannot act | permission tests | PLN-PERM-004 | Not started | |
| PLN-AC-020 | Material Approved change requires revision + re-approval | revision path | PLN-SVC-012, PLN-UI-10 | Not started | |
| PLN-AC-021 | Taken-up item: no material change without downstream correction | take-up guards | PLN-SVC-005, PLN-SVC-015 | Not started | |
| PLN-AC-022 | Publication failure visible; Approved status intact | `publish_approved_plan` | PLN-SVC-014 | Not started | |

#### 7.3 Data, performance and revision

| ID | Criterion (summary) | Primary proof | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-AC-023 | Totals / statutory / metrics reconcile to Plan Items | reporting tests | PLN-SVC-001, PLN-SVC-016 | Not started | |
| PLN-AC-024 | Quarterly report: As at, scope, basis, drill-down | PLN-UI-09 | PLN-UI-09, PLN-SVC-016 | Not started | |
| PLN-AC-025 | Aggregation / public-value not shown as realised without evidence | UI + DTO asserts | PLN-UI-06, PLN-UI-09 | Partial | Editor treatment copy present; UI-09 evidence later |
| PLN-AC-026 | MOH + County fixtures rebuild without duplicates | seed twice | PLN-SEED-001, PLN-SEED-003 | Not started | |
| PLN-AC-027 | Principal item retains Demand/Strategy/Budget/RSV/Tender IDs | seed + handoff | PLN-SEED-001, PLN-SVC-015 | Not started | |
| PLN-AC-028 | One current Approved version per PE/FY; superseded readable | version invariants | PLN-SCH-003, PLN-SVC-011 | Not started | |
| PLN-AC-029 | Transfer + incidental-cost complete before approval; no upstream mutation | validation | PLN-SVC-007, PLN-SVC-011 | Not started | |
| PLN-AC-030 | Add Plan Item → create/reuse one Draft successor; Approved stays operational | `open_or_create_plan_revision` | PLN-SVC-012, PLN-UI-09 | Not started | |
| PLN-AC-031 | New item Proposed; no Tender take-up until revision approved | take-up readiness | PLN-SVC-015, PLN-SEED-002 | Not started | |
| PLN-AC-032 | Revision review focuses on changed items / affected plan controls | PLN-UI-10 | PLN-UI-10, PLN-SVC-007 | Not started | |
| PLN-AC-033 | Approve revision: supersede, activate added, preserve unchanged handoffs | SCN-PLN-ADD-001 | PLN-SVC-011, PLN-SEED-002 | Not started | |
| PLN-AC-034 | Unchanged carry-forward reuses Effective allocations; no double consumption | allocation lifecycle | PLN-SVC-011, PLN-INT-001 | Not started | |

---

### 8. NFR evidence (`PLN-NFR-*`)

| ID | NFR (summary) | Work / proof | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-NFR-001 | Server-side permissions and scope on every read/mutation | scope matrix tests | PLN-PERM-002, PLN-AC-018 | Not started | |
| PLN-NFR-002 | Approval / supersession / effective allocations transactional + idempotent | concurrency / double-submit | PLN-SVC-011, PLN-AC-008 | Not started | |
| PLN-NFR-003 | Approved versions, decisions, handoffs, audit immutable | immutability tests | PLN-SCH-003…011 | Not started | |
| PLN-NFR-004 | WCAG 2.1 AA: keyboard, labels, focus, contrast, status | Playwright a11y | PLN-UI-01…10, PLN-UIC-002 | Not started | |
| PLN-NFR-005 | Ordinary requests target ≤2s at MVP volume | soft latency check | PLN-SVC-* | Not started | |
| PLN-NFR-006 | Validation errors: issue, owner, corrective action | validation DTO tests | PLN-SVC-007 | Done | `test_validate_plan` issue shape |
| PLN-NFR-007 | Stable API error codes (permission, validation, conflict, stale, funding, duplicate take-up) | error-code tests | PLN-SVC-* | Not started | |
| PLN-NFR-008 | Consistent date storage + user display timezone | timezone tests | PLN-SVC-005, PLN-SVC-016 | Not started | |
| PLN-NFR-009 | Seed/reset deterministic, idempotent, fixture-isolated | PLN-SEED-003 | PLN-SEED-001…002 | Not started | |
| PLN-NFR-010 | Totals/reports derived; no conflicting page-level aggregates | reporting reconcile | PLN-AC-023 | Not started | |
| PLN-NFR-011 | Method / statutory / validation rules versioned and effective-dated | config tests | PLN-SVC-005, PLN-SVC-007 | Not started | |
| PLN-NFR-012 | Publication/export respects disclosure policy | publish contract | PLN-SVC-014 | Not started | |

---

### 9. Legacy absence checks (`PLN-ABS-*`)

Owned by **`PLN-RET-005`** after structural retirement — not by Gate 01 schema. Run after RET-004. Exclude archive/docs from runtime claims. Source: Requirements §19.

| ID | Absence claim | Search / check | Status | Evidence |
|---|---|---|---|---|
| PLN-ABS-001 | No user-facing Planning Inclusion records | DocTypes / UI / services | Done | Orphan DocTypes removed on migrate; no PP2 Inclusion services |
| PLN-ABS-002 | No separate Procurement Package / Package Line workflows | DocTypes / routes / UI | Done | `test_pp2_full_removal_abs.test_abs_001_002_003_package_doctypes_gone` |
| PLN-ABS-003 | No user-managed Planning Release Package | DocTypes / UI | Done | Release/consumption DocTypes dropped with RET-004 |
| PLN-ABS-004 | No manual Released / Consumed actions | services / UI | Done | PP2 release APIs/services deleted |
| PLN-ABS-005 | No nine-state package lifecycle | status enums | Done | `pp2_constants` removed; no Package status machine |
| PLN-ABS-006 | No separate plan/package/inclusion/release workbenches | Desk pages / sidebar | Done | `test_abs_006_pp2_desk_pages_gone` + assets abs |
| PLN-ABS-007 | No ten-tab Package Detail | UI | Done | `package-detail` page + JS removed |
| PLN-ABS-008 | No mandatory template / rule-profile / risk / KPI builders inside Planning | UI / DocTypes | Done | Template/profile DocTypes orphan-deleted on migrate |
| PLN-ABS-009 | No manual entry of actual tender milestones in Planning | PLN-UI-06 / 09 | Not started | |
| PLN-ABS-010 | No planner mutation of funding reservations | services | Not started | |
| PLN-ABS-011 | No Strategy re-selection in Planning | PLN-UI-06 | Not started | |
| PLN-ABS-012 | No automatic merging of Demand Items | `add_demand_to_plan` | Done | Default one Plan Item; separate mode creates one Plan Item per Need Item; Combine only via aggregate |
| PLN-ABS-013 | No detailed Tender lots / STD configuration in Planning | UI / services | Not started | |
| PLN-ABS-014 | No page-local canonical fixture JSON in Planning JS | `public/js` grep | Not started | |
| PLN-ABS-015 | No Ministry-specific ownership fields | DocType JSON | Not started | |
| PLN-ABS-016 | No Administrator-as-operational-approver behaviour | PLN-PERM-004 | Not started | |
| PLN-ABS-017 | No user-maintained Plan / Item / Demand / Budget / Strategy codes in forms | PLN-UI-02 / 06 | Not started | |
| PLN-ABS-018 | No dual-read / dual-write / fallback Planning adapters | services grep | Done | `test_planning_mvp1_no_package_dual_write` 2/2 OK |
| PLN-ABS-019 | No Plan-header Budget context | PLN-UI-02 | Not started | |
| PLN-ABS-020 | No user-maintained statutory percentages on Plan Items | PLN-UI-06 | Done | Editor has treatment/value notes; no % fields |
| PLN-ABS-021 | District Hospital Renovation Works seed does not compete with digital-health story | seed inventory | Not started | |

---

### 10. Makefile / gates (`PLN-GATE-*`)

| ID | Gate | Purpose | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-GATE-00 | Replacement boundary approval | Cursor Prompt 00 output accepted | Pack baselines | Done | [GATE_00_REPLACEMENT_BOUNDARY.md](GATE_00_REPLACEMENT_BOUNDARY.md) |
| PLN-GATE-01 | Domain / schema gate | Invariants + no dual-write | PLN-SCH-*, PLN-ABS-018 | Done | [GATE_01_DOMAIN_FOUNDATION.md](GATE_01_DOMAIN_FOUNDATION.md); invariants 10/10 + schema 5/5 + ABS-018 2/2 |
| PLN-GATE-03 | `ui-planning-workspace-gate` | PLN-UI-01…03 | PLN-UI-01…03, PLN-UIC-001 | Done | [GATE_03_WORKSPACE_AND_REGISTER.md](GATE_03_WORKSPACE_AND_REGISTER.md) |
| PLN-GATE-04 | `ui-planning-builder-gate` | PLN-UI-04…06 | PLN-UI-04…06 | Done | [GATE_04_DEMAND_AND_PLAN_ITEM_EDITOR.md](GATE_04_DEMAND_AND_PLAN_ITEM_EDITOR.md) |
| PLN-GATE-05 | `ui-planning-approval-gate` (name TBD) | PLN-UI-07…08 + roles | PLN-UI-07…08 | Not started | |
| PLN-GATE-06 | `ui-planning-revision-gate` (name TBD) | PLN-UI-09…10 + SCN-PLN-ADD-001 | PLN-UI-09…10, PLN-SEED-002 | Not started | |
| PLN-GATE-ABS | `planning-abs-gate` (name TBD) | PLN-ABS-001…021 | PLN-RET-005, PLN-ABS-* | Not started | |
| PLN-GATE-08 | Final verification + FR/AC/NFR traceability report | Cursor Prompt 08 | All layers | Not started | |

---

## Cursor gate map

| Cursor Gate | Tracker coverage | Exit |
|---|---|---|
| 00 | PLN-GATE-00 | Replacement boundary approved |
| 01 | PLN-SCH-*, domain invariants | Domain tests green; no dual-write |
| 02 | PLN-PERM-*, PLN-SEED-001…003 | Seed + cross-entity tests |
| 03 | PLN-UI-01…03, PLN-GATE-03 | Registration / workspace browser tests |
| 04 | PLN-UI-04…06, PLN-GATE-04 | Eligible Demand + Plan Item editor |
| 05 | PLN-UI-07…08, PLN-SVC-007…011, PLN-GATE-05 | Atomic approval + role segregation |
| 06 | PLN-UI-09…10, PLN-SEED-002, PLN-AC-030…034, PLN-GATE-06 | SCN-PLN-ADD-001 e2e |
| 07 | PLN-SVC-014…016, PLN-INT-* | Integration contracts |
| 08 | PLN-AC / NFR / ABS / PLN-GATE-08 | Traceability with evidence |

---

## Recommended execution order

1. **PLN-GATE-00** — **Done**  
2. **PLN-RET-001…005** — **Done**  
3. **PLN-GATE-01** / `PLN-SCH-001…012` — **Done**  
4. Gate 02 roles + seed — **Done** ([GATE_02_ROLES_AND_SEED.md](GATE_02_ROLES_AND_SEED.md))  
5. `PLN-UI-*` / Gate 03 Stitch workspace — **next**  
6. Remaining `PLN-SVC-*` + Gates 04–06  
7. Gate 07 integrations / Plan Item handoff  
8. `PLN-AC-*` / `PLN-NFR-*` / `PLN-GATE-08`

---

## Explicit non-goals (MVP-1 build gates)

- Strategy / Budget / Demand creation or approval inside Planning  
- Mutating reservations or Approved Demand baselines  
- Detailed Tender lots / STD configuration  
- User-managed Release Package or Consumed actions  
- Full public transparency portal (export/publication readiness only)  
- Annual Asset Disposal Plan  
- Leaving any PP2 Planning / Package path alive “for TM demos”  

---

## STOP / change control

- Locked baseline above is closed for product decisions without a Requirements revision.
- **Zero PP2 Planning code** is a user mandate — do not reintroduce temporary preserve.
- Mark tracker rows **Done** only with evidence.
- Gate 01 requires `PLN-RET-005` Done (satisfied).
- On doc/repo conflict: stop and report; do not silently reinterpret Requirements v1.4.
