# B5.8 — Budget governance review (post–approval flow)

**Prompt:** [8.Budget-Approval-Flow.md — B5.8](./8.Budget-Approval-Flow.md)  
**Date:** 2026-04-20  
**Scope:** Read-only assessment after B5.1–B5.7. No code changes in this ticket. **Update:** subsection below reflects post–8.a rejection (B5.16-style review).

## Checklist

### 1. Required states

**Implemented:** `Draft`, `Submitted`, `Approved`, `Rejected` on `Budget` ([`budget.json`](../../../kentender_budget/kentender_budget/kentender_budget/doctype/budget/budget.json)), with optional rejection metadata fields. Legacy `Archived` was migrated to `Approved` via patch.

### 2. Valid / invalid transitions

**Enforced in** [`budget.py`](../../../kentender_budget/kentender_budget/kentender_budget/doctype/budget/budget.py) and [`budget_permissions.py`](../../../kentender_budget/kentender_budget/services/budget_permissions.py): `Draft → Submitted`, `Submitted → Approved`, `Submitted → Rejected`, `Rejected → Submitted`; other paths throw. Role checks on transitions in `assert_allowed_transition_roles`.

### 3. Edit locks (backend + UI)

**Backend:** `enforce_budget_submitted_approved_immutability`, allocation guard in [`budget_guards.py`](../../../kentender_budget/kentender_budget/services/budget_guards.py), `has_permission` hook in [`permissions.py`](../../../kentender_budget/kentender_budget/permissions.py).

**UI:** Landing actions and builder read-only state driven by status + roles ([`budget_workspace.js`](../../../kentender_budget/kentender_budget/public/js/budget_workspace.js), [`budget_builder_page.js`](../../../kentender_budget/kentender_budget/public/js/budget_builder_page.js)). UI is not authoritative; API/validate enforce locks.

### 4. Role permissions

**Aligned with spec:** Strategy Manager submits and edits Draft; Planning Authority approves Submitted and cannot create budgets or edit Draft content; Administrator / System Manager retain broad access per DocPerm + bypass helpers. Documented in tests ([`test_budget_b52.py`](../../../kentender_budget/kentender_budget/tests/test_budget_b52.py), [`test_budget_b53.py`](../../../kentender_budget/kentender_budget/tests/test_budget_b53.py)).

### 5. Procurement trust for Approved budgets

**Ready for downstream use:** Only `Approved` should be treated as the frozen financial baseline. Code paths should consume `Budget` where `status === "Approved"` (and `is_current_version` as needed). Procurement integration is **out of scope** for this module ticket; consumers must not rely on Draft/Submitted as committed spend.

### 6. Gaps before leaving Budget / moving to Procurement

| Area | Risk / gap | Mitigation |
|------|------------|------------|
| **Direct SQL / import** | Bypasses DocType validate | Restrict to trusted ops; use Data Import with same rules or server scripts. |
| **System Manager edits** | `budget_superuser_bypass` allows locked-budget fixes | Acceptable break-glass; audit via version / activity if required later. |
| **Rejection / return-to-Draft** | Addressed in 8.a (minimal rejection: `Submitted → Rejected → Submitted`) | No literal return to Draft; Strategy Manager revises while status stays `Rejected`. |
| **Procurement coupling** | Not implemented here | Procurement app should filter `Budget` by `Approved` and entity/plan. |

## B5.16 — Post-rejection checklist (8.a)

1. **Lifecycle:** `Draft → Submitted → Approved` and `Submitted → Rejected → Submitted` cover approver send-back and manager revision without dead ends.
2. **Dead ends:** None for the intended roles if users use landing actions; `Approved` remains terminal.
3. **Visibility:** Rejected budgets show status, optional row cue (“Needs revision”), and a detail summary with reason and actor/time.
4. **Locks:** `Submitted` / `Approved` content remains locked; `Rejected` allows edits and allocation changes (same as revision-needed working state).
5. **Procurement:** Still trust only **`Approved`** for committed baseline; `Rejected` is explicitly not approved spend.

## Summary

| | |
|--|--|
| **Complete** | States, transitions, role rules, locks, submit/approve/reject APIs, landing/builder UX, seeds, Playwright B5.7; rejection loop (8.a) with `Rejected` status and metadata. |
| **Missing (by design)** | Multi-step approval chains, accounting hooks, threaded rejection history. |
| **Risky** | Superuser bypass; manual DB changes. |
| **Must fix before Procurement** | None blocking in Budget module itself; Procurement must **only** trust **Approved** budgets and enforce entity alignment in its own layer. |
