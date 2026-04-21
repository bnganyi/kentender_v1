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

**Last updated:** 2026-04-21

### Phase A — Foundations and schema

| Ticket | Description | Status |
|--------|-------------|--------|
| **A1** | Demand DocType (header): full PRD schema, enums, defaults, read-only system fields, deterministic `demand_id` | Not started |
| **A2** | Demand Item child DocType: fields, link to Demand, `line_total` derived | Not started |
| **A3** | Derived totals: item `line_total`, header `total_amount`, recalc on row/qty/cost changes | Not started |
| **A4** | Canonical enums and defaults verified (priority, demand type, requisition type, status, planning_status, reservation_status) | Not started |

### Phase B — Governance and lifecycle

| Ticket | Description | Status |
|--------|-------------|--------|
| **B1** | Status model and allowed transitions; block invalid transitions server-side | Not started |
| **B2** | Lifecycle action whitelisted methods: submit, HoD approve/return/reject, finance approve/return/reject, cancel, mark_planning_ready | Not started |
| **B3** | Edit locking by state (draft/rejected editable; approval/finance/approved/planning/cancelled locked per PRD) | Not started |
| **B4** | Rejection / return / cancel metadata (reasons, actors, timestamps) | Not started |

### Phase C — Strategy and budget integration

| Ticket | Description | Status |
|--------|-------------|--------|
| **C1** | Budget-line-first strategy derivation; derived fields; block inconsistent mapping | Not started |
| **C2** | Core PRD validation (title, entity, dept, requester, dates, ≥1 line, total > 0, linkage, entity match) | Not started |
| **C3** | Demand-type validation (Planned / Unplanned / Emergency conditional fields, `is_exception`) | Not started |
| **C4** | Finance-stage budget sufficiency check; snapshot `available_budget_at_check`, `budget_check_datetime` | Not started |
| **C5** | Reservation on finance approval; atomic failure if reservation fails | Not started |
| **C6** | Reservation release on reject/cancel after reservation | Not started |
| **C7** | Planning Ready handoff (`planning_status`, lock, no Procurement Plan objects in DIA) | Not started |

### Phase D — Workspace / landing page

| Ticket | Description | Status |
|--------|-------------|--------|
| **D1** | DIA landing shell: header, subtitle, New Demand, KPI area, 4 tabs, queue selector, filters, master–detail | Not started |
| **D2** | KPI strip by role (Requisitioner / HoD / Finance / Procurement sets per UI spec) | Not started |
| **D3** | Top tabs (My Work / All / Approved / Rejected) + role-aware queue selector driving list | Not started |
| **D4** | Filters + search (refine active queue) | Not started |
| **D5** | Master list rows (badges, amounts, dates; selection highlight) | Not started |
| **D6** | Detail panel sections A–F (summary, budget/strategy, financial, items, workflow/audit, actions) | Not started |
| **D7** | Role- and state-aware action buttons on landing detail panel | Not started |

### Phase E — Builder / record editor

| Ticket | Description | Status |
|--------|-------------|--------|
| **E1** | Builder shell: routes new/edit, back to DIA, status badge, state-aware header actions | Not started |
| **E2** | Sectioned layout (order per UI spec); two-column short fields; no grey slabs | Not started |
| **E3** | Basic Request + Items sections (full field set, editable only in allowed states) | Not started |
| **E4** | Justification + Strategy + Budget sections (budget-line-first, derived strategy visible) | Not started |
| **E5** | Delivery + Exceptions + Workflow + Closure sections | Not started |
| **E6** | Inline validation; read-only when locked | Not started |

### Phase F — Roles, permissions, route protection

| Ticket | Description | Status |
|--------|-------------|--------|
| **F1** | Backend permissions for PRD action matrix | Not started |
| **F2** | UI visibility aligned with backend | Not started |
| **F3** | Route / API protection (no bypass via direct URL) | Not started |

### Phase G — Seed data

| Ticket | Description | Status |
|--------|-------------|--------|
| **G2** | Prerequisite budget lines / upstream seed (BL-MOH-2026-001, -002, BL-MOH-2027-001, mappings) | Not started |
| **G1** | DIA seed packs: `seed_dia_empty`, `seed_dia_basic`, `seed_dia_extended`, `seed_dia_exceptions`; IDs DIA-MOH-2026-0001–0009 per spec | Not started |

### Phase H — Smoke tests

| Ticket | Description | Status |
|--------|-------------|--------|
| **H2** | Stable `data-testid` / selectors per UI spec + smoke contract | Not started |
| **H1** | Playwright smoke suite (scenarios in smoke contract; helpers; deterministic seeds) | Not started |

### Phase I — Review and module exit

| Ticket | Description | Status |
|--------|-------------|--------|
| **I1** | Governance completeness review (no code — checklist pass/fail) | Not started |
| **I2** | UI/UX alignment review vs UI spec (no code) | Not started |
| **I3** | Module exit checklist ([8. DIA Master Checklist.md](./8.%20DIA%20Master%20Checklist.md)) | Not started |

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

## Deferred / follow-up

*Track ad-hoc polish, tech debt, and out-of-scope items here as they arise.*

| Area | Notes |
|------|--------|
| — | — |
