# Budget module — implementation tracker

**Prompt pack:** [7.Budget Module-Cursor-Prompt-Pack.md](./7.Budget%20Module-Cursor-Prompt-Pack.md)  
**Execution order:** B0.1 → B0.2 → B1.1 → B1.2 → B2.1 → B3.1 → B3.2 → B3.3 → B4.1 → B4.2 → B4.3

**Approval workflow:** [8.Budget-Approval-Flow.md](./8.Budget-Approval-Flow.md) — **B5.1 → B5.8**

## Source documents

| # | Document |
|---|----------|
| 1 | [1.Budget-Module-Scope Summary-MVP-v1.md](./1.Budget-Module-Scope%20Summary-MVP-v1.md) |
| 2 | [2.KenTender-Budget-Module-PRD-v1.md](./2.KenTender-Budget-Module-PRD-v1.md) |
| 3 | [3.Budget-Module-UX-Wireframe-MVP-v1.md](./3.Budget-Module-UX-Wireframe-MVP-v1.md) |
| 4 | [4.KenTender-Budget-Minimal-Domain-Model-v1.md](./4.KenTender-Budget-Minimal-Domain-Model-v1.md) |
| 5 | [5.KenTender-Budget-Seed-Data-Specification-v1.md](./5.KenTender-Budget-Seed-Data-Specification-v1.md) |
| 6 | [6.Budget-Module-Playwright-Smoke-Contract-v1.md](./6.Budget-Module-Playwright-Smoke-Contract-v1.md) |
| 7 | [7.Budget Module-Cursor-Prompt-Pack.md](./7.Budget%20Module-Cursor-Prompt-Pack.md) |
| 8 | [8.Budget-Approval-Flow.md](./8.Budget-Approval-Flow.md) |

## Ticket status

**Last updated:** 2026-04-21

| Ticket | Description | Status |
|--------|-------------|--------|
| **B0.1** | Budget + Budget Allocation DocTypes, validation | **Done** |
| **B0.2** | Workspace, Desk icon, routes, roles | **Done** |
| **B1.1** | Landing (empty + list) | **Done** |
| **B1.2** | Selected budget panel | **Done** |
| **B2.1** | Budget create form (enriched model, save → builder redirect) | **Done** |
| **B3.1** | Builder shell + program list | **Done** |
| **B3.2** | Allocation editor (`upsert_budget_allocation`, read-only guard) | **Done** |
| **B3.3** | Totals computation (landing + builder, non-negative remaining) | **Done** |
| **B4.1** | Seed data (idempotent scripts + docs) | **Done** |
| **B4.2** | Roles & permissions + role smoke (credential-aware skip) | **Done** |
| **B4.3** | Playwright smoke (landing, builder, totals, role visibility) | **Done** |

### Approval workflow (B5)

| Ticket | Description | Status |
|--------|-------------|--------|
| **B5.1** | Status model (Draft / Submitted / Approved), transitions, invalid transition errors | **Done** |
| **B5.2** | Role-based approval permissions | **Done** |
| **B5.3** | Lock Budget + Budget Allocation after submission | **Done** |
| **B5.4** | Landing + builder approval UI | **Done** |
| **B5.5** | `submit_budget` / `approve_budget` APIs | **Done** |
| **B5.6** | Seed: submitted/approved scenarios | **Done** |
| **B5.7** | Playwright approval smoke | **Done** |
| **B5.8** | Governance review (no code) | **Done** ([Budget-B5.8-Governance-Review.md](./Budget-B5.8-Governance-Review.md)) |

## Post-ticket polish (tracked here)

| Area | What shipped |
|------|----------------|
| **Fiscal year** | Server validation `2000–2099` on `Budget` (`budget.py`); tests in `test_budget_b01.py`. |
| **Landing UX** | Dashboard layout, KPIs, `displayBudgetLabel`, FY display, list scroll, asset cache-bust in `hooks.py`. |
| **Landing work surface (fix-3)** | Work tabs (All / My Work / status filters) with client-side filtering; role default tab; portfolio KPIs `pending_approval_count` / `my_drafts_count`; list row action cues + optional PA emphasis; approver detail banner; `get_budget_landing_data` includes `owner` / `created_by` and counts ([budget-landing-page-fix-3.md](./budget-landing-page-fix-3.md)). |
| **Rejection flow (8.a)** | `Rejected` status; `rejection_reason` / `rejected_by` / `rejected_at`; `reject_budget` + re-submit from `Rejected`; landing Rejected tab + modal; builder editable when Rejected; tests ([8.a.Budget-Approval-Flow - 2.md](./8.a.Budget-Approval-Flow%20-%202.md)). |
| **Budget Builder** | Aligns with landing via `.kt-budget-builder-shell` + shared `budget_workspace.css` tokens; desk-style `page-head` strip + breadcrumbs; `frappe.utils.set_title` for tab; “Back to Budgets” in header CTA. |
| **Budget form** | Two-column DocType layout: section/column breaks in `budget.json` (details, status, metadata); Notes full-width. |

## Global instruction (prepend to each ticket)

Use Budget module docs as source of truth. Do not introduce GL/cost centers/accounts, reuse ERPNext Budget, redesign Strategy, or over-engineer MVP. For B5, follow [8.Budget-Approval-Flow.md](./8.Budget-Approval-Flow.md) (no multi-step workflow engines). End each ticket with: completed / not completed / assumptions / files changed.

## Deferred / follow-up

- `services/budget_service.py`, `api/budget.py` (post–B0.1 as needed)
- DB composite unique indexes (validate-only in B0.1)
- Remove or migrate placeholder `Budget Navigation` Single DocType (optional cleanup)
