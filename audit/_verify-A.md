# Verification A — _part-xc-authz.md (AUD-XC-001..012) and _part-xc-core.md (AUD-XC-101..106)

Method: static re-read of every cited path:line, reachability trace through Frappe (handler.py, api/v1.py, permissions.py, database.get_value), hooks.py and controllers, and doc line checks against the latest approved versions. Nothing run; no DB access.

| ID | Verdict | Note |
|---|---|---|
| AUD-XC-001 | CONFIRMED | `actor(user)` lets the request value win at 21 sites; no request hook strips `user`; token handed out by the read call (workspace.py:133). |
| AUD-XC-002 | CONFIRMED | Only a Guest check; four whitelisted wrappers plus dia_budget_control; ignore_permissions writes; idempotency_key is a label. |
| AUD-XC-003 | CONFIRMED | Client `actor` wins; Administrator early-return and self-granted engine permission. Not checked: whether this site has TM2 Tender rows (impact conditional, as the finding states). |
| AUD-XC-004 | CONFIRMED | Six ungated whitelisted KTSM state changes; no in-repo consumer of KTSM eligibility, so High (not Critical) stands. |
| AUD-XC-005 | CONFIRMED | Strategy Author write on `status`; guard locks only 3 identity fields; no permission hook. |
| AUD-XC-006 | CORRECTED | Reproduction needs an Enabled Site-wide Budget Officer/Approver assignment: the registered core `has_permission` hook vetoes every ptype for a user with no assignment. Wording fixed; severity unchanged. |
| AUD-XC-007 | CONFIRMED | Annual Plan family has no hook (Planner role alone suffices); DPP hook only checks OU scope; read_only not enforced server-side. |
| AUD-XC-008 | CONFIRMED | DocPerms and status-flip bypass of the revision guard verified (guard tests the NEW status). |
| AUD-XC-009 | CONFIRMED | Whitelisted audit readers with no gate; `frappe.get_all` bypasses the System Manager-only DocPerm. |
| AUD-XC-010 | CONFIRMED | System Manager/Administrator hold write/delete on Audit Event; Strategy segregation reads it. |
| AUD-XC-011 | CONFIRMED | Role `All` write/create on both legacy doctypes; status fields unlocked. |
| AUD-XC-012 | CONFIRMED | FCO admitted, caller module client-supplied, no Requisition check; contradicting test present. |
| AUD-XC-101 | CONFIRMED | Lock at :341, plain post-lock sums from a snapshot opened at :314; REPEATABLE-READ makes the stale read real. |
| AUD-XC-102 | CONFIRMED | Only the commitment row is locked; disjoint from reserve_funding's Budget Line locks. |
| AUD-XC-103 | CONFIRMED | Approve/close lock Version rows, reserve locks Line rows; no shared lock, plain floor reads. |
| AUD-XC-104 | CONFIRMED | Status and line-version re-reads after the lock are plain snapshot reads. |
| AUD-XC-105 | CONFIRMED | `_submitted_by` reads the earliest event; audit write is best-effort so it can fail open. |
| AUD-XC-106 | CONFIRMED | No automatic caller of publish_annual_plan (no enqueue, no scheduler entry); cited line fixed to plan_publication.py:78. |

Counts: 17 CONFIRMED, 1 CORRECTED, 0 REFUTED. Changed IDs: AUD-XC-006 (reproduction and evidence wording), AUD-XC-106 (one line number). All 18 findings carry a `**Verification:**` line.
