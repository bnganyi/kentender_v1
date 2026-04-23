# Demand Intake and Approval (DIA) — implementation tracker

**Prompt pack:** [7. Cursor Pack.md](./7.%20Cursor%20Pack.md)  
**Execution order (mandatory):** A1 → A2 → A3 → A4 → B1 → B2 → B3 → B4 → C1 → C2 → C3 → C4 → C5 → C6 → C7 → D1 → D2 → D3 → D4 → D5 → D6 → D7 → E1 → E2 → E3 → E4 → E5 → E6 → F1 → F2 → F3 → **G2 → G1** → **H2 → H1** → I1 → I2 → I3

**Master checklist / exit gate:** [8. DIA Master Checklist.md](./8.%20DIA%20Master%20Checklist.md)

## Source documents

| # | Document |
|---|----------|
| 1 | [1. Scope Summary.md](./1.%20Scope%20Summary.md) |
| 2 | [2. PRD.md](./2.%20PRD.md) |
| 3 | [3. DIA Build Strategy.md](./3.%20DIA%20Build%20Strategy.md) |
| 4 | [4. DIA UI Spec.md](./4.%20DIA%20UI%20Spec.md) |
| — | *Seed Data Specification (referenced by PRD/UI pack; add as `5.` when available)* |
| 6 | [6. DIA Smoke Test Contract.md](./6.%20DIA%20Smoke%20Test%20Contract.md) |
| 7 | [7. Cursor Pack.md](./7.%20Cursor%20Pack.md) |
| 8 | [8. DIA Master Checklist.md](./8.%20DIA%20Master%20Checklist.md) |

## Ticket status

**Last updated:** 2026-04-23 (Phase I module exit review — I1/I2/I3)

### Phase A — Foundations and schema

| Ticket | Description | Status |
|--------|-------------|--------|
| **A1** | Demand DocType (header): full PRD schema, enums, defaults, read-only system fields, deterministic `demand_id` | **Done** (2026-04-21) |
| **A2** | Demand Item child DocType: fields, link to Demand, `line_total` derived | **Done** (2026-04-21) |
| **A3** | Derived totals: item `line_total`, header `total_amount`, recalc on row/qty/cost changes | **Done** (2026-04-21) |
| **A4** | Canonical enums and defaults verified (priority, demand type, requisition type, status, planning_status, reservation_status) | **Done** (2026-04-21) |

### Phase B — Governance and lifecycle

| Ticket | Description | Status |
|--------|-------------|--------|
| **B1** | Status model and allowed transitions; block invalid transitions server-side | **Done** (2026-04-21) |
| **B2** | Lifecycle action whitelisted methods: submit, HoD approve/return/reject, finance approve/return/reject, cancel, mark_planning_ready | **Done** (2026-04-21) |
| **B3** | Edit locking by state (draft/rejected editable; approval/finance/approved/planning/cancelled locked per PRD) | **Done** (2026-04-21) |
| **B4** | Rejection / return / cancel metadata (reasons, actors, timestamps) | **Done** (2026-04-21) |

### Budget control extension (DIA prerequisite)

| Ticket | Description | Status |
|--------|-------------|--------|
| **BX1** | Extend Budget Line (mini-PRD §6); BL-001–BL-007 validation | **Done** (2026-04-21) |
| **BX2** | Budget Reservation DocType; BR-001–BR-007 validation | **Done** (2026-04-21) |
| **BX3** | Service APIs: `get_budget_line_context`, `check_available_budget`, `create_reservation`, `release_reservation`, `get_available_budget` | **Done** (2026-04-21) |
| **BX4** | Seed budget lines BL-MOH-2026-001/002, BL-MOH-2027-001 (`kentender_core.seeds.seed_budget_line_dia`) | **Done** (2026-04-21) |
| **BX5** | Reservation smoke tests (`kentender_budget.tests.test_dia_budget_control_bx5`) | **Done** (2026-04-21) |

### Phase C — Strategy and budget integration

| Ticket | Description | Status |
|--------|-------------|--------|
| **C1** | Budget-line-first strategy derivation; derived fields; block inconsistent mapping | **Done** (2026-04-21) |
| **C2** | Core PRD validation (title, entity, dept, requester, dates, ≥1 line, total > 0, linkage, entity match) | **Done** (2026-04-21) |
| **C3** | Demand-type validation (Planned / Unplanned / Emergency conditional fields, `is_exception`) | **Done** (2026-04-21) |
| **C4** | Finance-stage budget sufficiency check; snapshot `available_budget_at_check`, `budget_check_datetime` | **Done** (2026-04-21) |
| **C5** | Reservation on finance approval; atomic failure if reservation fails | **Done** (2026-04-21) |
| **C6** | Reservation release on reject/cancel after reservation | **Done** (2026-04-21) — cancel from Approved with active reservation releases budget |
| **C7** | Planning Ready handoff (`planning_status`, lock, no Procurement Plan objects in DIA) | **Done** (2026-04-21) — `mark_planning_ready` sets `planning_status` + status Planning Ready |

### Phase D — Workspace / landing page

| Ticket | Description | Status |
|--------|-------------|--------|
| **D1** | DIA landing shell: header, subtitle, New Demand, KPI area, 4 tabs, queue selector, filters, master–detail | **Done** (2026-04-22) — workspace + `demand_intake_workspace.js/css`, `get_dia_landing_shell_data`, list/detail placeholders |
| **D2** | KPI strip by role (Requisitioner / HoD / Finance / Procurement sets per UI spec) | **Done** (2026-04-22) — `get_dia_landing_shell_data` role KPIs + clickable metadata; `test_landing_d2` |
| **D3** | Top tabs (My Work / All / Approved / Rejected) + role-aware queue selector driving list | **Done** (2026-04-23) — `get_dia_queue_list`, tab-scoped queue pills, Desk list + row selection stub; `test_dia_queue_list_d3` |
| **D4** | Filters + search (refine active queue) | **Done** (2026-04-23) — `get_dia_queue_filter_meta`, `get_dia_queue_list` refine + OR search; Desk filters, chips, debounced search; tests |
| **D5** | Master list rows (badges, amounts, dates; selection highlight) | **Done** (2026-04-23) — queue API enrich + card-style list, priority/status/type badges, amount + required-by, emergency/unplanned/exception accents; `test_dia_queue_list_d5` |
| **D6** | Detail panel sections A–F (summary, budget/strategy, financial, items, workflow/audit, actions) | **Done** (2026-04-23) — `get_dia_demand_detail` + Desk sections A–E + F (open form + D7 note); `test_dia_detail_d6` |
| **D7** | Role- and state-aware action buttons on landing detail panel | **Done** (2026-04-23) — `actions` in `get_dia_demand_detail`, Desk prompts + lifecycle calls, admin action union, Rejected cancel for owner; `test_dia_detail_d7` |

### Phase E — Builder / record editor

| Ticket | Description | Status |
|--------|-------------|--------|
| **E1** | Builder shell: routes new/edit, back to DIA, status badge, state-aware header actions | **Done** (2026-04-23) — `doctype_js` Demand + `demand_form.js` shell, `get_dia_demand_form_header` (actions sans open_form); `test_dia_form_header_e1` |
| **E2** | Sectioned layout (order per UI spec); two-column short fields; no grey slabs | Done — `demand.json` field_order + section labels; `section_5_budget_linkage` + `section_delivery`; removed `section_classification` / `section_reservation`; `demand_form.js` + `demand_intake_workspace.css` E2 layout class |
| **E3** | Basic Request + Items sections (full field set, editable only in allowed states) | **Done** (2026-04-23) — `demand_form.js`: Draft/Rejected-only `read_only` on basic fields + `items`, live `line_total`/`total_amount` recalc; `get_dia_demand_form_header` → `basic_items_editable`; `test_dia_builder_e3` |
| **E4** | Justification + Strategy + Budget sections (budget-line-first, derived strategy visible) | **Done** (2026-04-23) — `demand_form.js`: E4 field locks + live `get_budget_line_context` into form on `budget_line` / `procuring_entity`; CSS `.kt-dia-e4-derived-trace`; `test_dia_builder_e4` (BL-MOH-2026-001 derivation) |
| **E5** | Delivery + Exceptions + Workflow + Closure sections | **Done** (2026-04-23) — `demand_form.js`: delivery + exception fields in edit pass; Planned hides **Impact**; non-Emergency hides **Emergency Justification** + clears stale values on type change; `status` / `planning_status` / `reservation_status` read-only in builder; `.kt-dia-e5-workflow-field` CSS |
| **E6** | Inline validation; read-only when locked | **Done** (2026-04-23) — full-form `read_only` when not Draft/Rejected; `disable_save` / `enable_save`; `validate` + `runSaveValidation` (mandatory + Unplanned/Emergency rules + dates); `test_dia_builder_e5_e6` |

### Phase F — Roles, permissions, route protection

| Ticket | Description | Status |
|--------|-------------|--------|
| **F1** | Backend permissions for PRD action matrix: Demand `permission_query_conditions` + `has_permission` (`demand_intake/permissions/demand_permissions.py`, `hooks.py`) | Done |
| **F2** | UI visibility aligned with backend: New Demand button respects `can_create`; landing hint for `DIA_ACCESS_DENIED` (`demand_intake_workspace.js`) | Done |
| **F3** | Route / API protection: `dia_access.py` workspace gate + demand read/write checks on landing, queue, detail, lifecycle APIs | Done |

### Phase G — Seed data

| Ticket | Description | Status |
|--------|-------------|--------|
| **G2** | Prerequisite budget lines: `seed_budget_line_dia` (BX4) + `verify_prerequisites_for_dia()` read-only check | Done |
| **G1** | DIA seed packs under `demand_intake/seeds/`: `seed_dia_empty`, `seed_dia_basic`, `seed_dia_extended`, `seed_dia_exceptions`; business IDs DIA-MOH-2026-0001–0009; `test_dia_seed_phase_g` | Done |

### Phase H — Smoke tests

| Ticket | Description | Status |
|--------|-------------|--------|
| **H2** | Stable `data-testid` / selectors per smoke contract §5: KPI slots (`dia-kpi-*`), `dia-queue-selector`, `dia-filter-date-range`, list `dia-row-*` / row facets, detail panel + `dia-action-*`, builder `dia-builder-page` + field testids | Done |
| **H1** | Playwright under `tests/ui/smoke/dia/` (11 files per contract): live tests (empty shell, landing testids, New Demand, HoD queue row, procurement planning-ready) + `test.fixme` scaffolds for remaining scenarios; helpers `tests/ui/helpers/dia.ts` + auth roles | Done (extend fixme flows as needed) |

### Phase I — Review and module exit

| Ticket | Description | Status |
|--------|-------------|--------|
| **I1** | Governance completeness review (no code — checklist pass/fail) | **Done** (2026-04-23) — [DIA-Phase-I-Module-Exit-Review.md](./DIA-Phase-I-Module-Exit-Review.md) §I1 |
| **I2** | UI/UX alignment review vs UI spec (no code) | **Done** (2026-04-23) — same doc §I2 |
| **I3** | Module exit checklist ([8. DIA Master Checklist.md](./8.%20DIA%20Master%20Checklist.md)) | **Done** (2026-04-23) — same doc §I3 (F **Partial**: Playwright `test.fixme` backlog) |

## Progress log (append per batch)

Use after each ticket or batch (template from Master Checklist §19):

| Field | |
|-------|--|
| **Date** | |
| **Ticket(s)** | |
| **Reviewer** | |
| **Completed** | |
| **Not completed** | |
| **Assumptions** | |
| **Files changed** | |
| **Risks / concerns** | |
| **Ready for next ticket?** | Yes / No |

## Global instruction (prepend to each implementation ticket)

Implement DIA per locked artifacts ([2. PRD.md](./2.%20PRD.md), [4. DIA UI Spec.md](./4.%20DIA%20UI%20Spec.md), [6. DIA Smoke Test Contract.md](./6.%20DIA%20Smoke%20Test%20Contract.md)). Enforce governance **server-side**. Do not implement Procurement Planning, tendering, suppliers, or contracts in this module. End each ticket with: completed / not completed / assumptions / files changed / acceptance criteria status.

## A1 implementation notes (2026-04-21)

| Area | Notes |
|------|--------|
| **Demand** | [`kentender_procurement/.../doctype/demand/`](../../../kentender_procurement/kentender_procurement/doctype/demand/) — PRD §13.1 fields; `autoname` hash; `demand_id` format `DIA-{procuring_entity}-{YYYY}-{seq}` in `validate()`; audit defaults (`request_date`, `requested_by`, `created_by`); `is_exception` synced from `demand_type`. |
| **Link stubs** | Minimal **Budget Line**, **Funding Source** ([`kentender_budget`](../../../kentender_budget/kentender_budget/kentender_budget/doctype/)); **Sub Program** ([`kentender_strategy`](../../../kentender_strategy/kentender_strategy/kentender_strategy/doctype/sub_program/)). `output_indicator` → DocType **Strategy Objective** (label “Output Indicator”). |
| **Hooks** | [`hooks.py`](../../../kentender_procurement/kentender_procurement/hooks.py) `required_apps`: `kentender_core`, `kentender_strategy`, `kentender_budget`. |
| **Module** | `Demand Intake` in [`modules.txt`](../../../kentender_procurement/kentender_procurement/modules.txt). |
| **Migrate** | `bench --site kentender.midas.com migrate` succeeded. (`bench --site all migrate` may fail on sites referencing missing apps such as `kentender`.) |

## A2 implementation notes (2026-04-21)

| Area | Notes |
|------|--------|
| **Demand Item** | [`.../doctype/demand_item/`](../../../kentender_procurement/kentender_procurement/doctype/demand_item/) — PRD §13.2 fields; `istable` + `editable_grid`; `autoname` hash; `line_total` read-only (derivation in **A3**). |
| **Demand link** | Table field `items` (`options`: Demand Item) in [`demand.json`](../../../kentender_procurement/kentender_procurement/doctype/demand/demand.json), section **Items** before **Amount** / `total_amount`. |
| **Permissions** | Child DocType mirrors Budget Allocation (System Manager, Strategy Manager, Planning Authority read-only). |
| **Migrate** | `bench --site kentender.midas.com migrate` succeeded after A2. |

## A3 implementation notes (2026-04-21)

| Area | Notes |
|------|--------|
| **Demand Item** | [`demand_item.py`](../../../kentender_procurement/kentender_procurement/doctype/demand_item/demand_item.py) — `validate()` sets `line_total = flt(quantity) * flt(estimated_unit_cost)` (safe numeric handling via `frappe.utils.flt`). |
| **Demand** | [`demand.py`](../../../kentender_procurement/kentender_procurement/doctype/demand/demand.py) — `_recalculate_totals()` runs at end of `validate()`: for each `items` row, recomputes `line_total` from qty × unit cost and sets `total_amount` to the sum; empty items → `total_amount` 0. |
| **Verify** | `python -m py_compile` on both controllers; `bench --site kentender.midas.com migrate` succeeded. |

## A4 implementation notes (2026-04-21)

| Area | Notes |
|------|--------|
| **PRD / schema** | [PRD §13.3](./2.%20PRD.md) enumerations match [`demand.json`](../../../kentender_procurement/kentender_procurement/doctype/demand/demand.json) `options` and defaults; no JSON changes required. |
| **Server enforcement** | [`demand.py`](../../../kentender_procurement/kentender_procurement/doctype/demand/demand.py) — frozensets for six Select fields; `_validate_canonical_selects()` after `_recalculate_totals()`; `frappe.throw` if value not in allowed set. |
| **Verify** | `python -m py_compile` on `demand.py`; `bench --site kentender.midas.com migrate` succeeded. |

## B1 implementation notes (2026-04-21)

| Area | Notes |
|------|--------|
| **Transition map** | [`demand.py`](../../../kentender_procurement/kentender_procurement/doctype/demand/demand.py) — `ALLOWED_STATUS_TRANSITIONS` (PRD §8 + Cursor Pack B1): includes **Rejected → Pending HoD Approval**; cancel to **Cancelled** from Draft, Pending HoD, Pending Finance, Approved; **Planning Ready** and **Cancelled** terminal (no outgoing transitions). |
| **Validation** | `_validate_status_transitions()` after A4 checks: new docs only skip when status stays **Draft**; otherwise treat insert-from-**Draft**; updates use `has_value_changed("status")` and `get_doc_before_save()` for prior `status`. |
| **Verify** | `python -m py_compile` on `demand.py`; `bench --site kentender.midas.com migrate` succeeded. |

## B2 implementation notes (2026-04-21)

| Area | Notes |
|------|--------|
| **Lifecycle API** | [`demand_intake/api/lifecycle.py`](../../../kentender_procurement/kentender_procurement/demand_intake/api/lifecycle.py) — `@frappe.whitelist()` methods: `submit_demand`, `approve_hod`, `return_from_hod`, `reject_from_hod`, `approve_finance`, `return_from_finance`, `reject_from_finance`, `cancel_demand`, `mark_planning_ready`. State + role checks; HoD/Finance **approve** blocks self-approval vs `requested_by`; return/reject/cancel require reasons; audit timestamps/actors; finance approve TODO for **C5** reservation. |
| **Schema** | [`demand.json`](../../../kentender_procurement/kentender_procurement/doctype/demand/demand.json) — read-only **`return_reason`** for HoD/Finance return-to-draft. |
| **Roles / seed** | [`constants.py`](../../../kentender_core/kentender_core/seeds/constants.py) — **`Department Approver`** in `BUSINESS_ROLES`; seed user `hod.approver@moh.test`. PRD mapping: Finance Approver → **Finance Reviewer**, Procurement Officer → **Procurement Planner**, HoD → **Department Approver**. |
| **Verify** | `python -m py_compile`; `bench --site kentender.midas.com migrate` succeeded. |

## B3 implementation notes (2026-04-21)

| Area | Notes |
|------|--------|
| **Editable states** | [`demand.py`](../../../kentender_procurement/kentender_procurement/doctype/demand/demand.py) — `STATUSES_FULLY_EDITABLE` = **Draft**, **Rejected**; **Pending HoD** treated as fully locked (v1). `_enforce_edit_lock()` runs after audit/demand_id steps, **before** `_recalculate_totals()`; uses `get_doc_before_save()`; blocks scalar field changes and item-row content changes (signature ignores derived `line_total`). |
| **Lifecycle bypass** | [`lifecycle.py`](../../../kentender_procurement/kentender_procurement/demand_intake/api/lifecycle.py) — `_save_doc` sets `frappe.flags.demand_lifecycle_action` around `doc.save()`. |
| **Demand Item** | [`demand_item.py`](../../../kentender_procurement/kentender_procurement/doctype/demand_item/demand_item.py) — extra guard when parent `Demand` is not Draft/Rejected (same flag bypass). |
| **Verify** | `python -m py_compile`; `bench --site kentender.midas.com migrate` succeeded. |

## B4 implementation notes (2026-04-21)

| Area | Notes |
|------|--------|
| **Schema** | [`demand.json`](../../../kentender_procurement/kentender_procurement/doctype/demand/demand.json) — **`returned_by`**, **`returned_at`**, **`cancelled_by`**, **`cancelled_at`** (read-only); **`rejection_reason`** and **`cancellation_reason`** read-only in UI. |
| **Lifecycle** | [`lifecycle.py`](../../../kentender_procurement/kentender_procurement/demand_intake/api/lifecycle.py) — return/cancel set actor + time; **`submit_demand`** from **Rejected** clears **`return_reason`** / **`returned_by`** / **`returned_at`** only (keeps rejection audit). |
| **Validation** | [`demand.py`](../../../kentender_procurement/kentender_procurement/doctype/demand/demand.py) — `_validate_rejection_and_closure_metadata()` after status transitions: **Rejected** / **Cancelled** require reason + actor/time fields. |
| **Backfill** | [`patches/b4_backfill_cancel_return_metadata.py`](../../../kentender_procurement/kentender_procurement/patches/b4_backfill_cancel_return_metadata.py) — post-migrate SQL for legacy rows (skips if **`tabDemand`** missing). |
| **Verify** | `python -m py_compile`; `bench --site kentender.midas.com migrate` succeeded. |

## Deferred / follow-up

*Track ad-hoc polish, tech debt, and out-of-scope items here as they arise.*

| Area | Notes |
|------|--------|
| — | — |

## Phase I module exit review (2026-04-23)

| Field | |
|-------|--|
| **Date** | 2026-04-23 |
| **Ticket(s)** | I1, I2, I3 |
| **Reviewer** | Cursor agent (Phase I pack) |
| **Completed** | Written governance (I1), UI/UX (I2), and master-checklist exit (I3) reviews; artifact [DIA-Phase-I-Module-Exit-Review.md](./DIA-Phase-I-Module-Exit-Review.md). |
| **Not completed** | Full Playwright coverage per smoke contract (six scenarios still `test.fixme`); optional PRD **Auditor** role not implemented in DIA DocPerms. |
| **Assumptions** | Product accepts v1 **Pending HoD** full content lock (B3) vs checklist wording; engineering exit to PP allowed with **Partial** smoke automation if waived in writing. |
| **Files changed** | `DIA-Phase-I-Module-Exit-Review.md` (new); `DIA-Implementation-Tracker.md` (this section + I1–I3 status). |
| **Risks / concerns** | KPI `count` vs row-level list permissions may diverge; confirm HoD-lock + Auditor vs PRD §17. |
| **Ready for next ticket?** | **Yes** for Procurement Planning handoff, subject to product sign-off on Partial smoke and documented risks. |
