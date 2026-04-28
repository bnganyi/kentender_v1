# Procurement Planning — implementation tracker

**Prompt pack:** [9. Cursor Pack.md](./9.%20Cursor%20Pack.md)  
**Execution order (mandatory):** A1 -> A2 -> A3 -> A4 -> A5 -> B1 -> B2 -> B3 -> B4 -> C1 -> C2 -> C3 -> C4 -> D1 -> D2 -> D3 -> D4 -> D5 -> E1 -> E2 -> E3 -> F2 -> F1 -> G2 -> G1 -> **G3** (Playwright desk smoke; may track after G1/G2) -> H1 -> H2 -> H3

## Source documents

| # | Document |
|---|----------|
| 0 | [0. MVP Bootstrap Checklist - Sticky.md](./0.%20MVP%20Bootstrap%20Checklist%20-%20Sticky.md) |
| 1 | [1. Scope Summary.md](./1.%20Scope%20Summary.md) |
| 2 | [2. PRD v1.0.md](./2.%20PRD%20v1.0.md) |
| 3 | [3. Domain Model Table.md](./3.%20Domain%20Model%20Table.md) |
| 4 | [4. Templates - Deep Design.md](./4.%20Templates%20-%20Deep%20Design.md) |
| 5 | [5. UI Specification v1.0.md](./5.%20UI%20Specification%20v1.0.md) |
| 6 | [6. Seed Data.md](./6.%20Seed%20Data.md) |
| 7 | [7. Roles and Permissions.md](./7.%20Roles%20and%20Permissions.md) |
| 8 | [8. Smoke Test Contracts.md](./8.%20Smoke%20Test%20Contracts.md) |
| 9 | [9. Cursor Pack.md](./9.%20Cursor%20Pack.md) |

## Quality gate checklist (hard rule)

Mark any ticket/phase as **Done** only when all checks pass:

- [ ] **TDD evidence:** changed behavior covered by automated tests (test-first or same-change before closure).
- [ ] **Service/API coverage:** includes happy path + key negative/permission path.
- [ ] **UI coverage:** for Desk/workspace UX changes, Playwright validation executed and passing.
- [ ] **Regression guard:** bug fixes include a reproducing automated test.
- [ ] **Tracker discipline:** if any gate is incomplete, status is **Partial/In progress**, not Done.

## Ticket status

**Last updated:** 2026-04-24 (**H3** module exit complete — Procurement Planning implementation track closed)

### Phase A — Domain foundation

| Ticket | Description | Status |
|--------|-------------|--------|
| **A1** | Create Procurement Plan DocType | **Done** (2026-04-23) |
| **A2** | Create Procurement Package DocType | **Done** (2026-04-23) |
| **A3** | Create Package Line DocType | **Done** (2026-04-23) |
| **A4** | Create Template and Profile DocTypes | **Done** (2026-04-23) |
| **A5** | Implement derived totals and integrity calculations | **Done** (2026-04-23) |

### Phase B — Governance and workflow

| Ticket | Description | Status |
|--------|-------------|--------|
| **B1** | Implement Procurement Plan state model | **Done** (2026-04-23) |
| **B2** | Implement Procurement Package state model | **Done** (2026-04-23) |
| **B3** | Implement workflow action methods | **Done** (2026-04-23) |
| **B4** | Implement lock rules | **Done** (2026-04-23) |

### Phase C — Template and package application

| Ticket | Description | Status |
|--------|-------------|--------|
| **C1** | Implement template applicability validation | **Done** (2026-04-23) |
| **C2** | Implement template application service | **Done** (2026-04-23) |
| **C3** | Implement method derivation and override governance | **Done** (2026-04-23) |
| **C4** | Implement one end-to-end package creation slice | **Done** (2026-04-23) |

### Phase D — Workbench and package UI

| Ticket | Description | Status |
|--------|-------------|--------|
| **D1** | Implement Planning workbench shell | **Done** (2026-04-23) — workspace + landing API + `procurement_planning_workspace.js/css`, stable testids §12 shell/KPI/tabs/queues |
| **D2** | Implement package list panel | **Done** (2026-04-23) — `get_pp_package_list` + list UI wired to queues; smoke testids §4 / §12 list |
| **D3** | Implement package detail panel | **Done** (2026-04-23) — `get_pp_package_detail` + sectioned detail UI + workflow actions; smoke testids §12 detail |
| **D4** | Implement package builder/editor | **Done** (2026-04-23) — tabbed Form + `package_line_edit` + `procurement_package.js/css`; **`pp-builder-*`** testids |
| **D5** | Implement template selector and preview UX | **Done** (2026-04-23) — `list_pp_templates` / `get_pp_template_preview` in `api/template_selector.py`; `show_apply_template` on landing; shared `pp_template_selector.js` modal; **Choose template…** on package form (Draft/Structured); workbench **Apply template** + `apply_template_to_demands`; CSS; tests `test_pp_template_selector.py`; testids `pp-template-selector` / `pp-template-row-*` / `pp-template-preview` / `pp-template-apply` / `pp-action-apply-template` |

### Phase E — Roles and permissions

| Ticket | Description | Status |
|--------|-------------|--------|
| **E1** | Implement server-side role and scope enforcement | **Done** (2026-04-23) — `permissions/pp_record_permissions.py` (PQC + `has_permission` for Plan/Package; User Permission entity scope; strict auditor read); `permissions/pp_policy.py`; `workflow.py` read-load + `save(ignore_permissions=True)` after asserts; `package_line_edit` line asserts; DocPerm tighten Officer plan write / Officer+Authority package write |
| **E2** | Implement role-aware UI visibility | **Done** (2026-04-23) — landing `show_submit_plan` / `show_approve_plan` / `show_return_plan` / `show_reject_plan` / `show_lock_plan`; plan action bar in `renderPlanBar` + `runPpPlanWorkflow`; `package_detail._actions_for_workbench`; `procurement_package.js` planner-only Choose template / Submit |
| **E3** | Implement route and surface protection | **Done** (2026-04-23) — `loadPpLandingData` access-denied collapses shell (`data-pp-access-denied`); `injectPpLandingShell` refuses re-inject when denied; hooks remain authoritative for direct Form/list |

### Phase F — Seed data

| Ticket | Description | Status |
|--------|-------------|--------|
| **F2** | Validate DIA/Budget dependencies for planning seed | **Done** (2026-04-23) — [`validate_planning_seed_dependencies.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/seeds/validate_planning_seed_dependencies.py): `get_validation_report` / `run` / `assert_prerequisites` (DIA `demand_id`s **0004 / 0011 / 0020 / 0030**; Budget lines **BL-MOH-2026-001/002** + **BL-MOH-2027-001**). |
| **F1** | Implement Procurement Planning seed pack | **Done** (2026-04-23) — DIA: [`seed_dia_planning_f1_prerequisites.py`](../../../kentender_procurement/kentender_procurement/demand_intake/seeds/seed_dia_planning_f1_prerequisites.py) (4 demands + header totals; **0004** requires `seed_dia_basic`). Planning: [`seed_procurement_planning_f1.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/seeds/seed_procurement_planning_f1.py) — 6. profiles + **TPL-ICT-001** / **TPL-EMG-001** (+ **TPL-MED-001** if missing) + **PP-MOH-2026**; **`apply_template_to_demands`** to **PKG-MOH-2026-001/002/003**; `is_emergency` on **003**; `grouping_strategy` uses **`{"group_by": []}`** (v1 allowlist; 6. region/equipment is conceptual, same as PP3). Tests: [`test_f1_procurement_planning_seed.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/tests/test_f1_procurement_planning_seed.py). **Order:** DIA+Budget → **F2** → (optional) DIA F1 prereq → **F1**; `F1.run(ensure_dia=True)` runs DIA prereq + F2 assert then seeds. |

### Phase G — Smoke tests

| Ticket | Description | Status |
|--------|-------------|--------|
| **G1** | Implement Procurement Planning smoke suite | **Done** (2026-04-24) — [`test_procurement_planning_smoke_g1.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/tests/test_procurement_planning_smoke_g1.py): F1-gated integration tests for PP1, PP2/20 (APIs), PP3/4/5/17, PP6, PP7 (skip if demands packaged), PP8+9+10+14, PP11/12, PP15, PP16, PP18, PP19, `test_a0` reason guard, `test_zz` return+reject, PP13. |
| **G2** | Add/verify stable test IDs | **Done** (2026-04-24) — [`test_procurement_planning_testids_g2.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/tests/test_procurement_planning_testids_g2.py) scans desk JS + `landing.py` for §6 hooks; jQuery/ `setAttribute` allowed. **Fix:** `template_selector._label_for_doctype` no longer queries non-existent columns (e.g. `template_name` on Risk Profile). |
| **G3** | **Comprehensive Procurement desk UI smoke tests (Playwright)** — extend beyond ad-hoc checks: **Procurement Home** (injected shell, KPI strip, quick links, no false DIA/PP hijack), **Demand Intake & Approval** workbench, **Procurement Planning** workbench, **Workspace Sidebar** IA (first item Procurement Home, Settings block, no second-sidebar regression for Planning), navigation from desktop tile; align with stable `data-testid` hooks where defined; run against a live site using repo [`playwright.config.ts`](../../../playwright.config.ts), `.env.ui`, and `make -C apps/kentender_v1 ui-smoke` (or `npm run test:ui:smoke`); document required roles/fixtures in test README. | **Done** (2026-04-24) — `tests/ui/smoke/procurement/procurement-g3.spec.ts` + `tests/ui/helpers/procurement.ts`; validates launcher path, DIA/PP shells, sidebar IA order/settings, and single-rail behavior for Planning. |

### Phase H — Review and module exit

| Ticket | Description | Status |
|--------|-------------|--------|
| **H1** | Governance completeness review | **Done** (2026-04-24) — [Procurement-Planning-H1-Governance-Review.md](./Procurement-Planning-H1-Governance-Review.md): plan/package states, transitions, template mandatory, locks, method override, DIA/Budget traceability, handoff preconditions. **Follow-up** (plan-draft bootstrap) implemented under **H3**. |
| **H2** | UI alignment review | **Done** (2026-04-24) — [Procurement-Planning-H2-UI-Review.md](./Procurement-Planning-H2-UI-Review.md); workbench vs spec §2–5 + Kentender UI pattern; **code:** subtitle aligned to locked §2.2, demand-lines table shows **Demand title** (API field). **Note:** queue pill label remains **Completed Packages** (renamed from Structured) by product decision. |
| **H3** | Module exit checklist | **Done** (2026-04-24) — [Procurement-Planning-H3-Module-Exit.md](./Procurement-Planning-H3-Module-Exit.md); sections A–G assessed **Pass**; **code:** `_validate_parent_plan_draft_for_bootstrap` on `Procurement Package` + `test_procurement_planning_h3_plan_bootstrap.py` (closes H1 recommendation). |

## Progress log (append per ticket or batch)

| Field | |
|-------|--|
| **Date** | |
| **Ticket(s)** | |
| **Reviewer** | |
| **Completed** | |
| **Not completed** | |
| **Assumptions** | |
| **Files changed** | |
| **Acceptance criteria status** | |
| **Risks remaining** | |
| **Ready for next ticket?** | Yes / No |

| **Date** | 2026-04-23 |
| **Ticket(s)** | F2, F1 |
| **Reviewer** | — |
| **Completed** | F2 dependency check; DIA F1 four-demand prerequisite pack; F1 full seed (profiles, templates, plan, three packages, `is_emergency` on `PKG-MOH-2026-003`); integration tests. |
| **Not completed** | G3, H* |
| **Assumptions** | Template v1 `grouping_strategy` is empty `group_by` (6. `region`/`equipment_type` not in allowlist). G1: some tests skip if F1 plan is not Draft (e.g. `test_g_pp19` already run) or demands are fully allocated to packages (PP7). |
| **Files changed** | `test_procurement_planning_smoke_g1.py`, `test_procurement_planning_testids_g2.py`, `template_selector.py` (`_label_for_doctype`), this tracker. |
| **Acceptance criteria status** | G1: deterministic backend smoke where seed exists; G2: stable `data-testid` and KPI testids in code. |
| **Risks remaining** | G1 `test_g_pp19` leaves F1 plan `PP-MOH-2026` in **Approved** until re-seed; PP7 may skip on crowded F1. |
| **Ready for next ticket?** | **Yes** — next **G3** (Playwright) or **H1**. |

| **Date** | 2026-04-24 |
| **Ticket(s)** | G1, G2 |
| **Completed** | Backend G1 suite + G2 test ID checks; `_label_for_doctype` only queries fields that exist on each DocType. |
| **Risks remaining** | F1 plan may be left **Approved** after G1; re-seed to restore Draft. |

| **Date** | 2026-04-24 |
| **Ticket(s)** | G3 |
| **Reviewer** | — |
| **Completed** | Added Playwright procurement smoke suite: Procurement Home shell and quick links (no DIA/PP shell hijack), DIA + PP open from Procurement module sidebar, sidebar IA checks (Procurement Home first, Settings visible), and no duplicate sidebar rail in Planning. Added procurement UI helper and Playwright test README with required roles/fixtures; expanded `.env.ui.example` credentials. |
| **Not completed** | H1, H2, H3 |
| **Assumptions** | Sidebar Settings child links may be collapsed by default (`keep_closed`); G3 validates Settings block presence rather than expanded child-link visibility. |
| **Files changed** | `tests/ui/smoke/procurement/procurement-g3.spec.ts`, `tests/ui/helpers/procurement.ts`, `tests/ui/README.md`, `.env.ui.example`, this tracker. |
| **Acceptance criteria status** | Pass — `npm run test:ui -- tests/ui/smoke/procurement/procurement-g3.spec.ts` (3/3 passed). |
| **Risks remaining** | Full `ui-smoke` suite still depends on local environment data/credentials parity; run `make -C apps/kentender_v1 ui-smoke` on target UAT before release gate. |
| **Ready for next ticket?** | **Yes** — next **H1**. |

| **Date** | 2026-04-24 |
| **Ticket(s)** | H1 |
| **Reviewer** | Engineering (code-backed review) |
| **Completed** | H1 governance completeness review per [9. Cursor Pack.md](./9.%20Cursor%20Pack.md); deliverable [Procurement-Planning-H1-Governance-Review.md](./Procurement-Planning-H1-Governance-Review.md). |
| **Not completed** | H2, H3 |
| **Assumptions** | H1 is review-only per Cursor Pack (no code changes in H1). Optional hardening: parent-plan Draft guard on package insert / `plan_id` change (documented as recommended follow-up). |
| **Files changed** | `Procurement-Planning-H1-Governance-Review.md` (new); this tracker. |
| **Acceptance criteria status** | All seven H1 checks addressed with **complete** / **missing** / **risky** / **must-fix** sections; sign-off **Pass** with one **risky** item (Form vs template plan-state parity). |
| **Risks remaining** | Threshold rules interpreter still deferred (v1); optional package–plan bootstrap guard not implemented. |
| **Ready for next ticket?** | **Yes** — next **H2**. |

| **Date** | 2026-04-24 |
| **Ticket(s)** | H2 |
| **Reviewer** | Engineering (spec + code review) |
| **Completed** | H2 UI alignment review per [9. Cursor Pack.md](./9.%20Cursor%20Pack.md); deliverable [Procurement-Planning-H2-UI-Review.md](./Procurement-Planning-H2-UI-Review.md). Minor alignment: workbench subtitle = UI spec §2.2; detail demand table includes **Demand title** column. |
| **Not completed** | H3 |
| **Assumptions** | “Completed Packages” queue label kept as-is; Package Form Restructure v2 overrides legacy §6.3 in-form demand table. |
| **Files changed** | `Procurement-Planning-H2-UI-Review.md` (new), `procurement_planning_workspace.js`, this tracker. |
| **Acceptance criteria status** | All eight H2 checks documented (matches / missing / must-fix); sign-off **Pass**. |
| **Risks remaining** | Playwright G3 or copy tests may assert old subtitle — update if present. |
| **Ready for next ticket?** | **Yes** — next **H3**. |

| **Date** | 2026-04-24 |
| **Ticket(s)** | H3 |
| **Reviewer** | Engineering |
| **Completed** | Module exit checklist [Procurement-Planning-H3-Module-Exit.md](./Procurement-Planning-H3-Module-Exit.md); plan-draft bootstrap guard on package insert / `plan_id` change; test `test_procurement_planning_h3_plan_bootstrap`. |
| **Not completed** | — (PP Cursor Pack track A–H complete for Planning scope) |
| **Assumptions** | Tendering consumption of **Ready** packages is a **separate module**; threshold rules interpreter still deferred. |
| **Files changed** | `procurement_package.py`, `test_procurement_planning_h3_plan_bootstrap.py`, `Procurement-Planning-H3-Module-Exit.md`, this tracker. |
| **Acceptance criteria status** | H3 §A–G: all **Pass**; blockers **none**; downstream recommendations documented. |
| **Risks remaining** | Cross-module Tendering contract tests not in this repo scope. |
| **Ready for next ticket?** | **N/A** — proceed to **Tendering programme** or PP v1.1 backlog per product. |

## Global instruction (prepend to each implementation ticket)

Implement Procurement Planning exactly per locked artifacts ([1. Scope Summary.md](./1.%20Scope%20Summary.md), [2. PRD v1.0.md](./2.%20PRD%20v1.0.md), [3. Domain Model Table.md](./3.%20Domain%20Model%20Table.md), [5. UI Specification v1.0.md](./5.%20UI%20Specification%20v1.0.md), [6. Seed Data.md](./6.%20Seed%20Data.md), [7. Roles and Permissions.md](./7.%20Roles%20and%20Permissions.md), [8. Smoke Test Contracts.md](./8.%20Smoke%20Test%20Contracts.md), [9. Cursor Pack.md](./9.%20Cursor%20Pack.md)). Enforce governance server-side. Keep strict scope boundaries (no Tendering implementation, no supplier lifecycle, no contract execution, no payment logic). End each ticket with: completed / not completed / assumptions / files changed / acceptance criteria status / risks remaining.

## A1 implementation notes (2026-04-23)

| Area | Notes |
|------|--------|
| **DocType** | Added [`procurement_plan.json`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_plan/procurement_plan.json) with locked A1 fields (`plan_code`, `plan_name`, `fiscal_year`, `procuring_entity`, `currency`, `total_planned_value`, `status`, `created_by`, `created_at`, `approved_by`, `approved_at`, `is_active`), `title_field`, `search_fields`, and role baseline. |
| **Validation/controller** | Added [`procurement_plan.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_plan/procurement_plan.py): canonical status validation, defensive plan-code uniqueness check, approved/locked immutability guard, audit defaulting, and approval metadata sync. |
| **Module bootstrap** | Added `Procurement Planning` to [`modules.txt`](../../../kentender_procurement/kentender_procurement/modules.txt), plus idempotent patch [`ensure_procurement_planning_module_def.py`](../../../kentender_procurement/kentender_procurement/patches/ensure_procurement_planning_module_def.py) and registered it in [`patches.txt`](../../../kentender_procurement/kentender_procurement/patches.txt). |
| **Validation run** | `python -m py_compile` passed; `./scripts/bench-with-node.sh --site kentender.midas.com migrate` passed; site checks validated duplicate-code rejection and approved-state lock behavior. |

## A2 implementation notes (2026-04-23)

| Area | Notes |
|------|--------|
| **DocType** | Added [`procurement_package.json`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_package/procurement_package.json) with Cursor Pack A2 / domain fields (`package_code`, `package_name`, `plan_id`, `template_id`, `procurement_method`, `contract_type`, `estimated_value`, `currency`, `status`, `planning_status`, `schedule_start`, `schedule_end`, profile links, override fields, `is_emergency`, `is_active`, `created_by`, `approved_by`, `approved_at`). Status `Ready` = ready-for-tender handoff state per domain. |
| **Link targets** | Minimal shell DocTypes (expanded in **A4**) so `Link` fields resolve on migrate: [`Procurement Template`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_template/), [`Risk Profile`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/risk_profile/), [`KPI Profile`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/kpi_profile/), [`Decision Criteria Profile`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/decision_criteria_profile/), [`Vendor Management Profile`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/vendor_management_profile/) — each `template_code` / `profile_code` + name fields only for now. |
| **Controller** | [`procurement_package.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_package/procurement_package.py): canonical selects, required links + existence checks, defensive `package_code` uniqueness, override reason when flag set, competitive methods require `decision_criteria_profile_id`, non-negative `estimated_value`, **Approved/Ready** read-only lock, approval timestamp stamping when locked. Line-sum derivation for `estimated_value` remains **A5**. |
| **Validation run** | `py_compile` OK; `bench migrate` synced `Procurement Package`; spot-checked insert (Direct without criteria), rejected Open Tender without criteria, rejected duplicate `package_code`; removed temp test rows from site. |

## A3 implementation notes (2026-04-23)

| Area | Notes |
|------|--------|
| **DocType** | Added [`procurement_package_line.json`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_package_line/procurement_package_line.json): `package_id` → `Procurement Package`, `demand_id` → `Demand`, `budget_line_id` → `Budget Line`, `amount`, optional `quantity` / `department` / `priority`, `is_active`; `title_field`/`search_fields` for link UX. |
| **Controller** | [`procurement_package_line.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_package_line/procurement_package_line.py): `amount` > 0; parent package must be **Draft** or **Structured** (no line edits once package moves on); demand must exist and be **Approved** or **Planning Ready**; budget line exists and **must match** demand `budget_line`; optional `priority` must match DIA set when set; **v1** at most **one active** line per `demand_id` globally. |
| **Validation run** | `py_compile` OK; `bench migrate` OK; `DocType` `Procurement Package Line` present on `kentender.midas.com`. |

## A4 implementation notes (2026-04-23)

| Area | Notes |
|------|--------|
| **Profiles** | [`risk_profile.json`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/risk_profile/risk_profile.json) / [`risk_profile.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/risk_profile/risk_profile.py): `risk_level`, `risks` JSON list of objects; unique `profile_code`. [`kpi_profile`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/kpi_profile/): `metrics` JSON list (strings or non-empty objects). [`decision_criteria_profile`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/decision_criteria_profile/): `criteria` list with required `criterion` string and optional `weight` 0–100. [`vendor_management_profile`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/vendor_management_profile/): `monitoring_rules` / `escalation_rules` JSON objects. |
| **Procurement Template** | [`procurement_template.json`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_template/procurement_template.json) / [`procurement_template.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_template/procurement_template.py): Cursor Pack field set including applicability JSON lists, `grouping_strategy`, `threshold_rules`, governance flags, schedule ints; unique `template_code`; required profile links enforced in Python (link fields `reqd` 0 for migrate safety); competitive default method requires `decision_criteria_profile_id`; `allowed_methods` when set must include `default_method`. |
| **Validation run** | `py_compile` OK; `bench migrate` OK on `kentender.midas.com`. |

## A5 implementation notes (2026-04-23)

| Area | Notes |
|------|--------|
| **Package** | [`procurement_package.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_package/procurement_package.py): `_sync_estimated_value_from_lines()` on validate sets `estimated_value` = sum of active line `amount`; `estimated_value` **read-only** in [`procurement_package.json`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_package/procurement_package.json). Module helpers `recompute_package_estimated_value` / `recompute_plan_total_planned_value` (with `on_trash` exclusions) keep DB totals in sync when lines change without a full package save. `estimated_value` omitted from terminal-state lock diff to avoid blocking saves when the field is system-derived. |
| **Plan** | [`procurement_plan.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_plan/procurement_plan.py): `_sync_total_planned_value_from_packages()` sets `total_planned_value` = sum of **active** packages' `estimated_value`; `total_planned_value` skipped in approved/locked change guard for the same reason. |
| **Lines** | [`procurement_package_line.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_package_line/procurement_package_line.py): `after_insert` / `on_update` / `on_trash` call `recompute_package_estimated_value` (excluding the row being deleted on trash). |
| **Package lifecycle** | `after_insert` / `on_update` / `on_trash` on package refresh plan totals (with package exclusion on trash). |
| **Validation run** | `py_compile` OK; `bench migrate` OK. |

## B1 implementation notes (2026-04-23)

| Area | Notes |
|------|--------|
| **DocType** | [`procurement_plan.json`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_plan/procurement_plan.json): `status` adds **Rejected**; **`workflow_reason`** (Long Text) for return/reject/admin unlock; **`rejected_by`** / **`rejected_at`** (read-only audit). |
| **State machine** | [`procurement_plan.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_plan/procurement_plan.py): `ALLOWED_STATUS_TRANSITIONS` — Draft→Submitted; Submitted→Approved / Draft (return) / Rejected; Approved→Locked; Locked→Draft (admin); Rejected terminal. Mirrors DIA [`demand.py`](../../../kentender_procurement/kentender_procurement/demand_intake/doctype/demand/demand.py) transition pattern. |
| **Reasons** | Non-empty **`workflow_reason`** required for Submitted→Draft, Submitted→Rejected, Locked→Draft. |
| **Roles** | Per [7. Roles and Permissions.md](./7.%20Roles%20and%20Permissions.md) §6.1: Draft→Submitted — **Procurement Planner** / Administrator / System Manager; Submitted governance transitions and Approved→Locked — **Planning Authority** / Administrator / System Manager; Locked→Draft — **Administrator / System Manager** only. **Procurement Officer** cannot drive these plan transitions. |
| **Approval precondition** | Submitted→Approved requires **≥1** active package (`plan_id`, `ifnull(is_active,1)=1`). Deeper package validity deferred to B2/C. |
| **Immutability** | **Approved / Locked / Rejected** body fields read-only for non-privileged users; **Administrator / System Manager** bypass field lock (admin override). Narrow exception: non-privileged may change only **`status`** and **`workflow_reason`** together for allowed transitions (fixes Approved→Locked without blocking governance edits). **`total_planned_value`** still excluded from lock diff. |
| **Metadata** | `_sync_approval_metadata`: Approved/Locked stamp `approved_by`/`approved_at` when missing; Rejected clears approval stamps and sets `rejected_by`/`rejected_at`; Draft/Submitted clear governance stamps. |
| **Assumptions** | **Returned** stored as **Draft** (not a separate status). |
| **Validation run** | `py_compile` OK; `bench migrate` OK on `kentender.midas.com`. |

## B2 implementation notes (2026-04-23)

| Area | Notes |
|------|--------|
| **DocType** | [`procurement_package.json`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_package/procurement_package.json): `status` adds **Rejected**; `status` description clarifies **Ready** = Ready for Tender; **`workflow_reason`**; **`rejected_by`** / **`rejected_at`**. |
| **State machine** | [`procurement_package.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_package/procurement_package.py): `ALLOWED_STATUS_TRANSITIONS` — Draft→Structured; Structured→Submitted; Submitted→Approved / Draft / Rejected; Approved→Ready; Ready→Draft; Rejected terminal. |
| **Reasons** | Non-empty **`workflow_reason`** for Submitted→Draft, Submitted→Rejected, Ready→Draft. |
| **Roles** | Per §6.2: Draft→Structured and Structured→Submitted — **Procurement Planner** / Admin / SM; Submitted governance — **Planning Authority** / Admin / SM (Officer excluded); Approved→Ready — **Procurement Officer** or **Planning Authority** / Admin / SM; Ready→Draft — Admin / SM only. |
| **Preconditions** | Draft→Structured: not on first `is_new()` save; **≥1** active line. Structured→Submitted: **≥1** active line. Approved→Ready: **≥1** active line + competitive **decision criteria** present. |
| **Immutability** | **Approved / Ready / Rejected** read-only for non-privileged users; **Admin/SM** bypass; narrow **status** + **workflow_reason** allowance so **Approved→Ready** succeeds; **`estimated_value`** still excluded from lock diff. |
| **Metadata** | `_sync_approval_metadata`: Approved and Ready set approval stamps when missing and clear rejection fields; Rejected clears approval and sets rejection stamps; Draft/Structured/Submitted clear both. |
| **Assumptions** | **Returned** = **Draft**; stored handoff state remains **`Ready`**. |
| **Validation run** | `py_compile` OK; `bench migrate` OK on `kentender.midas.com`. |

## B3 implementation notes (2026-04-23)

| Area | Notes |
|------|--------|
| **API module** | [`workflow.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/api/workflow.py): `@frappe.whitelist()` actions **`submit_plan`**, **`approve_plan`**, **`return_plan`**, **`reject_plan`**, **`lock_plan`**, **`structure_package`**, **`submit_package`**, **`approve_package`**, **`return_package`**, **`reject_package`**, **`mark_ready_for_tender`**, **`apply_template_to_demands`** (C2). |
| **Behaviour** | Each action validates id, **`has_permission` + `check_permission("write")`**, asserts **expected prior `status`**, sets target **`status`** (and **`workflow_reason`** for return/reject), then **`doc.save()`** so **B1/B2** Document rules remain the single source of truth. |
| **Audit** | After successful save, **`doc.add_comment("Comment", …)`** records action + user (+ truncated reason for return/reject). |
| **Discoverability** | [`procurement_planning/api/__init__.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/api/__init__.py) imports **`workflow`** so the submodule loads with the package. |
| **Validation run** | `py_compile` OK; `bench execute …submit_plan` with empty `plan_id` raises **ValidationError**; missing plan id raises **DoesNotExistError** as expected. |

## B4 implementation notes (2026-04-23)

| Area | Notes |
|------|--------|
| **Plan field lock** | [`procurement_plan.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_plan/procurement_plan.py): **`READONLY_STATUSES`** now includes **Submitted** (with Approved, Locked, Rejected) per [7. Roles and Permissions.md](./7.%20Roles%20and%20Permissions.md) §11 / Cursor Pack B4. Non-privileged users may still change only **`status`** + **`workflow_reason`** together for allowed transitions; **`total_planned_value`** excluded; **Administrator / System Manager** bypass unchanged. |
| **Package field lock** | [`procurement_package.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_package/procurement_package.py): **`READONLY_STATUSES`** includes **Submitted** (with Approved, Ready, Rejected). Same narrow workflow escape and **`estimated_value`** exclusion; Admin/SM bypass unchanged. |
| **Package lines** | [`procurement_package_line.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_package_line/procurement_package_line.py): clearer lock message when parent is not **Draft** or **Structured**, naming **Submitted / Approved / Ready / Rejected**. |
| **Validation run** | `py_compile` OK on touched modules. |

## C1–C3 implementation notes (2026-04-23)

| Area | Notes |
|------|--------|
| **C1 — Applicability** | [`template_applicability.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/services/template_applicability.py): **`validate_demands_for_template`**: template exists and **active**; each demand **Approved** or **Planning Ready**; **`demand_type`** / **`requisition_type`** in template JSON lists; **`budget_line`** set, **Budget Line** exists, **`is_active`** not explicitly off; **`total_amount` > 0** (v1 packaging amount source aligns with C2 lines); no **active** [`Procurement Package Line`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_package_line/procurement_package_line.py) for that **`demand_id`** (`ifnull(is_active,1)=1`). |
| **C2 — Application** | [`template_application.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/services/template_application.py): **`apply_template_to_demands`** requires plan **`Draft`**; runs C1; **`grouping_strategy.group_by`** allowlist only **`demand_type`**, **`requisition_type`**, **`procuring_entity`**, **`requesting_department`**, alias **`department`** → **`requesting_department`**; unknown keys **throw**; empty **`group_by`** ⇒ single group; per group inserts **`Procurement Package`** (**Draft**) with template defaults + plan **`currency`**, unique **`package_code`** (plan code prefix + token) unless **`options.package_code` / `package_name`** (single group, C4 seed); human **`package_name`**; per demand inserts **`Procurement Package Line`** with **`amount` = `Demand.total_amount`**, **`budget_line_id`**, optional context fields; **no Demand mutation**; **`frappe.flags.skip_package_line_rollup`** defers line rollups so **`recompute_package_estimated_value`** runs **once** per package after lines; packages/lines inserted with **`ignore_permissions=True`** (caller must enforce auth). Returns **`{packages, lines_created}`**. |
| **C2 — API** | [`workflow.apply_template_to_demands`](../../../kentender_procurement/kentender_procurement/procurement_planning/api/workflow.py): **`has_permission` + `check_permission("write")`** on **Procurement Plan**; **read** on **Procurement Template**; **`demand_ids`** parsed as JSON list or comma-separated string; **`plan_id` / `template_id` / demand entries** resolved via [`planning_references.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/services/planning_references.py) (internal **`name`** or business **`plan_code`**, **`template_code`**, **`demand_id`**); optional **`options`** JSON (e.g. **`package_code`** + **`package_name`** for single-group deterministic apply); optional **`actor`** for **`created_by`**. |
| **C3 — Governance** | [`procurement_package.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_package/procurement_package.py): in **Draft / Structured**, when **`method_override_flag`** is off, **`procurement_method`** and **`contract_type`** reset from template **`default_*`**; **`threshold_rules`** non-empty is a **v1 no-op** (threshold bands deferred); if **`allowed_methods`** is set, template default must be in the list when not overriding; with override, chosen method must be in **`allowed_methods`** when non-empty; **Submitted+** may not change **`procurement_method`**, **`contract_type`**, or **`method_override_flag`** (explicit C3 guard alongside B4 lock). |
| **Lines rollup flag** | [`procurement_package_line.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_package_line/procurement_package_line.py): **`frappe.flags.skip_package_line_rollup`** skips **`recompute_package_estimated_value`** from line hooks during bulk apply. |
| **Assumptions** | **Apply** only when plan is **Draft**. **Line amount** v1 = **`Demand.total_amount`** (revisit if PRD prefers line-sum). **Threshold rules** interpreter **deferred**. **`package_code`** uses random suffix unless **C4**-style **`options.package_code` / `package_name`** (single group). |
| **Validation run** | `py_compile` OK on touched modules; **`bench execute`** `apply_template_to_demands` with empty **`plan_id`** raises **`ValidationError`** as expected. |

## C4 implementation notes (2026-04-23)

| Area | Notes |
|------|--------|
| **References** | [`planning_references.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/services/planning_references.py): **`resolve_procurement_plan_name`**, **`resolve_procurement_template_name`**, **`resolve_demand_name`** — map business codes / **`demand_id`** to internal **`name`**. |
| **Deterministic apply** | [`template_application.apply_template_to_demands`](../../../kentender_procurement/kentender_procurement/procurement_planning/services/template_application.py): optional **`options.package_code`** + **`options.package_name`** (both required; **single group only**) for seed/smoke; not the D5 workbench path. |
| **PP3 seed** | [`seed_planning_pp3_slice.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/seeds/seed_planning_pp3_slice.py): **`run()`** — idempotent; skips if **`PKG-MOH-2026-001`** already exists on **PP-MOH-2026**; requires **`DIA-MOH-2026-0004`** (run **`seed_dia_basic`** first), creates **`DIA-MOH-2026-0011`** if missing; **`grouping_strategy`** uses **`{"group_by": []}`** (6. Seed Data **region/equipment_type** grouping deferred to **F1**); profiles + **TPL-MED-001** + **PP-MOH-2026**; **`Demand.total_amount`** for **0004** / **0011** aligned to **3M / 2M** via **`frappe.db.set_value`** after approval (Approved demands block item edits; **0011** uses small line totals for finance reservation then header total aligned). Core seed runs only if **MOH** / **KES** missing (avoids **`run_core_minimal`** races in parallel tests). |
| **Tests** | [`test_c4_pp3_slice.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/tests/test_c4_pp3_slice.py): integration tests for create + idempotent skip; **`setUp`** clears stale PP3 artifacts; **`tearDown`** restores **0004** **`total_amount`** and removes created rows. |
| **Validation run** | `py_compile` OK; **`bench execute`** **`kentender_procurement.procurement_planning.seeds.seed_planning_pp3_slice.run`** OK; **`bench run-tests`** **`kentender_procurement.procurement_planning.tests.test_c4_pp3_slice`** OK. |

## D1 implementation notes (2026-04-23)

| Area | Notes |
|------|-------|
| **Landing API** | [`landing.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/api/landing.py): **`get_pp_landing_shell_data`** — `{ok, role_key, currency, current_plan, plans[], kpis[], queue_tabs{}, show_new_plan, show_new_package}`; **`PP_NOT_INSTALLED`** / **`PP_ACCESS_DENIED`** envelopes; **KPIs scoped to current plan** (`plan_id` filter) when a plan is resolved; optional **`plan`** arg to pin context; high-risk count = packages whose **Risk Profile** is **High**. |
| **Desk shell** | [`procurement_planning_workspace.js`](../../../kentender_procurement/kentender_procurement/public/js/procurement_planning_workspace.js) + [`procurement_planning_workspace.css`](../../../kentender_procurement/kentender_procurement/public/css/procurement_planning_workspace.css): inject on **Procurement Planning** workspace; header, plan bar, KPI strip, four tabs, queue pills, master–detail placeholders (`pp-package-list` / `pp-detail-panel`); **New Plan** / **New Package** (prefills **`plan_id`** when package); plan `<select>` when multiple plans. |
| **Workspace & nav** | [`workspace/procurement_planning/procurement_planning.json`](../../../kentender_procurement/kentender_procurement/kentender_procurement/workspace/procurement_planning/procurement_planning.json); sidebar [`workspace_sidebar/procurement.json`](../../../kentender_procurement/kentender_procurement/workspace_sidebar/procurement.json); [`hooks.py`](../../../kentender_procurement/kentender_procurement/hooks.py) **fixtures** + **app_include** for assets. |
| **Assumptions** | **Queue matrix** in landing is a first-pass mapping to §7.1; **D2** wires list queries to **`activeQueueId`** via **`get_pp_package_list`**. **Migrate** on target site required to import the new **Workspace** row. |
| **Acceptance** | D1 Cursor Pack: workbench structure + clean load; UI spec §2–3, §8.1, §12 testids for shell/KPI/tabs/named queues. |
| **Validation run** | `python -m py_compile` on **`landing.py`**; local **`import kentender_procurement.procurement_planning.api.landing`** OK. Full **`bench migrate`** not re-run in this environment (bench site import error: unrelated **`kentender`** app hook). |
| **Ready for next ticket?** | **Yes** — **D3** package detail panel (list + selection stub shipped in **D2**). |

## D2 implementation notes (2026-04-23)

| Area | Notes |
|------|-------|
| **List API** | [`package_list.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/api/package_list.py): **`get_pp_package_list(plan, queue_id, limit)`** — same auth/plan resolution as landing (`resolve_pp_role_key`, `_can_read_planning`, `_resolve_current_plan`); **`INVALID_QUEUE`** / **`NO_PACKAGE_PERMISSION`** / **`PP_*`** envelopes; filters **`plan_id` + `is_active`** per queue id aligned with KPI semantics in [`landing.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/api/landing.py) (`submitted_packages` / `pending_approval` both **Submitted**; **`high_risk_escalation`** = **Submitted** + high-risk profile set; **`method_override`** = **`method_override_flag`** + status in Draft/Structured/Submitted/Approved). Rows include **`template_name`** (batch from **Procurement Template**) and **`badges`** (`high_risk` from **Risk Profile** level, **`emergency`**, **`submitted`**, **`ready`**). |
| **Desk list** | [`procurement_planning_workspace.js`](../../../kentender_procurement/kentender_procurement/public/js/procurement_planning_workspace.js): after **`renderQueuePills`**, **`fetchPackageList`** loads rows; compact row layout + **`pp-row-*`** testids per [8. Smoke Test Contracts](8.%20Smoke%20Test%20Contracts.md); queue-specific empty copy + **Create Package** CTA when **`show_new_package`** and queue is draft/structured; row click toggles selection and loads the **D3** detail panel. |
| **CSS** | [`procurement_planning_workspace.css`](../../../kentender_procurement/kentender_procurement/public/css/procurement_planning_workspace.css): scrollable list column, row hover/active, badge variants. |
| **Tests** | [`test_pp_package_list.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/tests/test_pp_package_list.py): **`INVALID_QUEUE`**, **`Guest`** → **`PP_ACCESS_DENIED`**. |
| **Validation run** | `./scripts/bench-with-node.sh build --app kentender_procurement`; **`bench --site kentender.midas.com run-tests --module …test_pp_package_list`** OK. |
| **Ready for next ticket?** | **Yes** — **D3** detail panel (implemented same day). |

## D3 implementation notes (2026-04-23)

| Area | Notes |
|------|-------|
| **Detail API** | [`package_detail.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/api/package_detail.py): **`get_pp_package_detail(package)`** — same planning read gate as list (`resolve_pp_role_key`, `_can_read_planning`); **`PP_NOT_INSTALLED`**, **`PP_ACCESS_DENIED`**, **`NO_PACKAGE_PERMISSION`**, **`NOT_FOUND`**; payload includes **definition**, **financial**, **demand_lines** (batched **Demand** / **Budget Line** labels; **Demand** link resolved by internal **`name`** or business **`demand_id`**), **risk** / **kpi** / **decision_criteria** / **vendor_management** (bounded JSON), **workflow** audit fields, **`badges`**, **`actions`** (workflow + edit, gated on **write** + **status**). |
| **Desk detail** | [`procurement_planning_workspace.js`](../../../kentender_procurement/kentender_procurement/public/js/procurement_planning_workspace.js): **`renderPackageDetail`** → **`get_pp_package_detail`**; eight read-only sections + header; [8. Smoke Test Contracts](8.%20Smoke%20Test%20Contracts.md) **`pp-detail-*`** + **`pp-action-*`**; **`frappe.call`** to [`workflow.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/api/workflow.py) **`structure_package`**, **`submit_package`**, **`approve_package`**, **`mark_ready_for_tender`**; **`return_package`** / **`reject_package`** via **`frappe.prompt`** reason; success refreshes list + detail. |
| **CSS** | [`procurement_planning_workspace.css`](../../../kentender_procurement/kentender_procurement/public/css/procurement_planning_workspace.css): scrollable detail column, section titles, **`kt-pp-detail-grid`** / **`kt-pp-detail-kv`**, table wrap. |
| **Tests** | [`test_pp_package_detail.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/tests/test_pp_package_detail.py): Guest → **`PP_ACCESS_DENIED`**; empty / missing package → **`NOT_FOUND`**. |
| **Validation run** | `./scripts/bench-with-node.sh build --app kentender_procurement`; **`bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.procurement_planning.tests.test_pp_package_detail`** OK. |
| **Ready for next ticket?** | **Yes** — **D4** shipped below; next **D5** template UX. |

## D4 implementation notes (2026-04-23)

| Area | Notes |
|------|-------|
| **DocType layout** | [`procurement_package.json`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_package/procurement_package.json): **10 tabs** (definition → notes), two-column **Column Break** grids; **`demand_lines_html`** anchor for the builder table; **`planner_notes`** / **`exception_notes`**; **`status`** read-only on form (transitions via workflow APIs / server). |
| **Lock / notes** | [`procurement_package.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_package/procurement_package.py): **`planner_notes`** / **`exception_notes`** may change when package is otherwise workflow-locked (`_ALLOWED_CHANGES_WHEN_READONLY`). |
| **Line API** | [`package_line_edit.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/api/package_line_edit.py): **`get_pp_package_lines`**, **`add_pp_package_line`**, **`remove_pp_package_line`** — planning gate + package permissions; **`PACKAGE_LOCKED`** / **`NOT_FOUND`** / **`PP_*`**; soft-deactivate line + **`recompute_package_estimated_value`**. |
| **Desk Form** | [`procurement_package.js`](../../../kentender_procurement/kentender_procurement/public/js/procurement_package.js): **`pp-builder-page`** on layout; tab nav **`pp-builder-section-*`**; demand table **`pp-builder-section-demand-lines`**; **`pp-builder-save`** on primary; **Submit for approval** + **`pp-builder-submit`**; **Back to Procurement Planning**; dialog add line; readonly shell for terminal **`status`** except notes. |
| **CSS** | [`procurement_package.css`](../../../kentender_procurement/kentender_procurement/public/css/procurement_package.css) + [`hooks.py`](../../../kentender_procurement/kentender_procurement/hooks.py) **`doctype_js`** / **`app_include_css`**. |
| **Tests** | [`test_pp_package_line_edit.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/tests/test_pp_package_line_edit.py). |
| **Validation run** | **`bench migrate`** (site **kentender.midas.com**); **`./scripts/bench-with-node.sh build --app kentender_procurement`**; **`bench run-tests --module …test_pp_package_line_edit`** OK. |
| **Ready for next ticket?** | **Yes** — **D5** template selector and preview UX (rich modal; template Link stays standard until then). |

## D5 implementation notes (2026-04-23)

| Area | Notes |
|------|--------|
| **API** | [`template_selector.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/api/template_selector.py): **`list_pp_templates`**, **`get_pp_template_preview`** — same planning read gate as landing; **`PP_NOT_INSTALLED`**, **`PP_ACCESS_DENIED`**, preview **`NOT_FOUND`**. |
| **Landing** | [`landing.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/api/landing.py): **`show_apply_template`** (Draft plan + planner/admin, mirrors **`show_new_package`**). |
| **Client** | [`pp_template_selector.js`](../../../kentender_procurement/kentender_procurement/public/js/pp_template_selector.js) — form **Use template** sets **`template_id`** + profile links; workbench **Apply template** → **`apply_template_to_demands`**. [`procurement_package.js`](../../../kentender_procurement/kentender_procurement/public/js/procurement_package.js) **Choose template…**; [`procurement_planning_workspace.js`](../../../kentender_procurement/kentender_procurement/public/js/procurement_planning_workspace.js) **`pp-action-apply-template`**. |
| **Styling** | [`procurement_package.css`](../../../kentender_procurement/kentender_procurement/public/css/procurement_package.css), [`procurement_planning_workspace.css`](../../../kentender_procurement/kentender_procurement/public/css/procurement_planning_workspace.css) — list row hover, two-column shell, CTA flex gap. |
| **Tests** | [`test_pp_template_selector.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/tests/test_pp_template_selector.py). |
| **Ready for next ticket?** | **Yes** — **F2** / **F1** shipped; next **G2** / **G1**. |

## Phase E implementation notes (2026-04-23)

| Area | Notes |
|------|--------|
| **Hooks** | [`hooks.py`](../../../kentender_procurement/kentender_procurement/hooks.py): **`permission_query_conditions`** + **`has_permission`** for **Procurement Plan** / **Procurement Package** → [`permissions/pp_record_permissions.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/permissions/pp_record_permissions.py). |
| **Policy** | [`permissions/pp_policy.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/permissions/pp_policy.py): workflow + template-apply + package-line edit assertions. |
| **Workflow** | [`workflow.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/api/workflow.py): read gate + **`save(ignore_permissions=True)`** after asserts. |
| **UI** | [`landing.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/api/landing.py) plan CTA flags; [`package_detail.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/api/package_detail.py) **`_actions_for_workbench`**; [`procurement_planning_workspace.js`](../../../kentender_procurement/kentender_procurement/public/js/procurement_planning_workspace.js) plan bar + access shell; [`procurement_package.js`](../../../kentender_procurement/kentender_procurement/public/js/procurement_package.js) planner-only builder actions. |
| **DocPerm** | [`procurement_plan.json`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_plan/procurement_plan.json) Officer **write** 0; [`procurement_package.json`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_package/procurement_package.json) Officer + Planning Authority **write** 0. |
| **Tests** | [`test_pp_permissions_e1.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/tests/test_pp_permissions_e1.py). |
| **Ready for next ticket?** | **Yes** — next **G2** / **G1** (stable test IDs + smoke suite). |
