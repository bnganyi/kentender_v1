# Part xc-core — concurrency, SoD residual, audit, money, Frappe hazards (AUD-XC-101 …)

All findings are static (source read, `grep -n`, `sed -n`); nothing was run on a site, DB or bench. Lines were re-opened by the author of this part. Where a number was computed it was done with plain Python float/Decimal arithmetic outside the site (no bench). The lead queried the site: MariaDB 10.6.23 with `@@tx_isolation = REPEATABLE-READ`; Frappe v16 sets no isolation level (`apps/frappe/frappe/database/mariadb/database.py` only treats snapshot conflicts as deadlock, lines 26-29). Every "stale snapshot" finding below depends on that fact: a plain `SELECT` after a `SELECT … FOR UPDATE` in the same transaction reads the snapshot taken at the transaction's first consistent read, not the rows committed while it waited for the lock.

| ID | Severity | Title |
|---|---|---|
| AUD-XC-101 | High | `reserve_funding` can oversubscribe a Budget Line: lock is taken, availability is then read from a pre-lock snapshot |
| AUD-XC-102 | High | `adjust_commitment` increase is not serialised against the Budget Line or against reservations |
| AUD-XC-103 | High | Budget approval/closure and reservation take disjoint lock sets, so successor approval or closure can race a reservation |
| AUD-XC-104 | High | Finance decision "serialised basis" is validated with stale reads after the lock |
| AUD-XC-105 | High | Budget no-self-approval reads the FIRST submission event, and fails open when the event was never written |
| AUD-XC-106 | High | An approved Annual Plan is never dispatched for publication: nothing transmits it, so it never becomes Active |
| AUD-XC-107 | Medium | Requisition drawdown rechecks (correction hold, Plan Item state, record version) read a pre-lock snapshot |
| AUD-XC-108 | Medium | Award cancellation guard reads `notification_status` from a stale snapshot after taking the Award Case lock |
| AUD-XC-109 | Medium | Requisition revocation and handoff consumption take row locks in opposite order (AB-BA) |
| AUD-XC-110 | Medium | Budget funding-ledger events (20 sites) and Award audit are best-effort: a failed audit write is swallowed after the material action |
| AUD-XC-111 | Medium | Funding-ledger events omit before/after positions, business role, assignment ID and fiscal year |
| AUD-XC-112 | Medium | Denial events required by STR §13 / BUD §14 are never written, or are written and rolled back |
| AUD-XC-113 | Medium | Reads of sealed/confidential bid pages and opening exports create no audit event |
| AUD-XC-114 | Medium | Opening-register download delivery record and audit event are written inside a GET and rolled back |
| AUD-XC-115 | Medium | Plan affordability and method-limit tests compare float sums with a 1e-9 epsilon |
| AUD-XC-116 | Medium | Budget position, floor and `Needs Attention` tests use float arithmetic |
| AUD-XC-117 | Medium | Money inputs are not validated as exact decimals: NaN/Inf, excess scale, 0.01 and 0.0001 tolerances |
| AUD-XC-118 | Medium | Need quantity is a 3-decimal Float with no unit-of-measure precision or whole-number rule |
| AUD-XC-119 | Medium | Budget optimistic-lock stamp is optional on every command, and a line save never moves it |
| AUD-XC-120 | Medium | Strategy idempotency journal is keyed without payload, replays before authorisation, and its race leaves duplicate effects |
| AUD-XC-121 | Medium | `PublishAnnualPlan` re-sends after an Indeterminate result; `PLN_PUBLICATION_FAILED`/`UNKNOWN` are never produced |
| AUD-XC-122 | Medium | Strategy §13 audit list is incomplete (consumer reads, context resolution) and two events omit attribution |
| AUD-XC-123 | Medium | Planning and Requisition command journals do not record the exercised authority, role or request id |
| AUD-XC-124 | Medium | Departmental Need Decision stores a bare assignment ID, not the snapshot NDS §4.5 requires |
| AUD-XC-125 | Medium | A post-model-sync patch deletes the DocType records of two doctypes the app still ships, and the next patch wipes the table |
| AUD-XC-126 | Medium | Dropped-doctype crash class still present: post-sync patches and a whitelisted TM2 export touch dropped tables |
| AUD-XC-127 | Medium | One-shot destructive patches have no environment or non-empty guard |
| AUD-XC-128 | Low | Organisation Unit commands and Award Settings changes write no audit event |
| AUD-XC-129 | Low | Frappe `Currency` storage (decimal 21,9) cannot hold the 18 integral digits the documents require |
| AUD-XC-130 | Low | Typed stale-version / idempotency errors are unreachable under real concurrency; reference generators read stale data |
| AUD-XC-131 | Low | Idempotent replay is answered before authorisation and from a user-blind key lookup |
| AUD-XC-132 | Low | Reservation "required" amount is rounded half-up to the cent |
| AUD-XC-133 | Low | Currency and precision are hard-coded in Planning and Budget reads |
| AUD-XC-134 | Low | Planner segregation chain omits `SavePlanVersionDetails` and other Planner commands |
| AUD-XC-135 | Low | "Independent of direct processing" for the opening committee covers only Tender Version actors and the publishing AO |
| AUD-XC-136 | Low | Nothing stops an assignment administrator granting business roles to themselves or Administrator; registry `sod_tags` unused |
| AUD-XC-137 | Low | Open segregation questions in approved documents (Finance vs Budget Officer, BDS signatory, Contract) |
| AUD-XC-138 | Low | A patch records success although its unique indexes may not exist |
| AUD-XC-139 | Low | Patches that rewrite data by heuristic |
| AUD-XC-140 | Low | `**kwargs` Needs endpoints and journey/search endpoints turn unknown or malformed input into HTTP 500 |
| AUD-XC-141 | Low | Departmental-plan autostart failure is swallowed and never retried |
| AUD-XC-142 | Low | Scheduler sweeps without per-item isolation |
| AUD-XC-143 | Low | Legacy Tender Configuration services commit mid-request and a "get" writes and commits |

### AUD-XC-101 — `reserve_funding` can oversubscribe a Budget Line: lock is taken, availability is then read from a pre-lock snapshot
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** BUD v1.12 §8.3, BUD-BR-013, BUD18-AC-019; REQ v1.14 §9.1A step 2 · **Module(s):** Budget, Requisitions · **Sources:** sweep-money F1; trace-budget F-05(a); trace-requisition F-03 (Budget half)
**Evidence**
- `kentender_budget/kentender_budget/services/budget_check_reserve_contracts.py:314` — `existing = _existing_reservations_for_correlation(correlation_id)`: a plain read, which opens the snapshot (`_resolve_line` per row at :337 also reads before the lock).
- `…/budget_check_reserve_contracts.py:340-343` — `select name from \`tabProcurement Budget Line\` where name in %s order by name for update`: only Budget Line rows are locked; they are never updated.
- `…/budget_check_reserve_contracts.py:372-375` — `totals, _budget = _line_totals(rows, line_docs)` then `if entry["available"] < entry["required"]` → `BUDGET_INSUFFICIENT_FUNDS`. `_line_totals` → `_line_active_version_and_position` (:139-157) → `_line_position` (`budget_contracts.py:196-215`) sums `Funding Reservation.remaining_amount` and `Procurement Commitment.current_amount` with plain `select coalesce(sum(...))`.
- `kentender_procurement/.../procurement_requisitions/services/authorise.py:111-118` — `check_funding` and `reserve_funding` run in one `envelope.atomic("authorise")` transaction, so the snapshot is older than any lock wait.
- `Funding Reservation.drawdown_line_id` is unique per drawdown line, not per Budget Line, so no index stops a second reservation on the same line.
**Rule:** BUD §8.3 "`reserve_funding` … locks Budget root/affected lines in stable order, rechecks aggregate availability"; BUD-BR-013 "Concurrent commands cannot oversubscribe a line."; BUD18-AC-019 "Concurrent authorisations cannot oversubscribe a line, and no position becomes negative." Framework: under REPEATABLE READ, rows another transaction inserted and committed during the lock wait are invisible to later consistent reads.
**Reproduction / failing test sketch:** (static; not run) On `kentender-test.local`, Budget Line L approved 100,000,000.00, nothing reserved. Two requisitions on different Plan Items (so REQ `open_slot_key` does not serialise them) each need 80,000,000.00 from L. Two threads, each `frappe.init/connect`, `check_funding` then `threading.Barrier.wait()` then `reserve_funding` then `frappe.db.commit()`. Thread B blocks at line 341 until A commits, then sums with its old snapshot (reserved 0) and inserts. Expected: second call raises `BUDGET_INSUFFICIENT_FUNDS`. Actual by reading: both succeed; `select sum(remaining_amount) from \`tabFunding Reservation\` where budget_line = L` = 160,000,000.00 and available = −60,000,000.00. First run `select @@tx_isolation`.
**Impact:** Two concurrently authorised Requisitions can reserve more than the approved Budget Line; BUD-BR-013 fails exactly under the concurrency it names. Existing "concurrent" test (`test_bud_chg_001_phase3_check_reserve.py:140`) is sequential on one connection.
**Verification:** CONFIRMED — budget_check_reserve_contracts.py:314 (plain read opens the snapshot), :341 (`for update` on Budget Line rows only) and :372-375 via budget_contracts.py:187-215 (plain sums) read availability after the lock; with MariaDB REPEATABLE-READ (confirmed by lead) a waiter's later plain SELECT does not see rows the lock holder committed, and the only unique key is drawdown_line_id (funding_reservation.json:108-112).

### AUD-XC-102 — `adjust_commitment` increase is not serialised against the Budget Line or against reservations
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** BUD v1.12 §9.1 (`adjust_commitment`: "no unfunded increase"), BUD-BR-013 · **Module(s):** Budget · **Sources:** sweep-money F2
**Evidence**
- `kentender_budget/kentender_budget/services/budget_commitment_contracts.py:266` — `select name from \`tabProcurement Commitment\` where name=%s for update`: only the one commitment row is locked.
- `…/budget_commitment_contracts.py:273-276` — `pos = _line_position(reservation.budget_line, _current_line_version(...))` then `if delta > pos["available"] + 0.0001` (plain snapshot sums, `budget_contracts.py:196-215`).
- `reserve_funding` locks `Procurement Budget Line` rows (`budget_check_reserve_contracts.py:341`); `adjust_commitment` locks a commitment row. The two lock sets never intersect.
**Rule:** BUD §9.1 table: `adjust_commitment` — "Locked adjustment and effective ledger event; no unfunded increase." BUD-BR-013 "Concurrent commands cannot oversubscribe a line."
**Reproduction / failing test sketch:** (static; not run) Line approved 100,000,000.00 with commitments C1 = 40,000,000.00 and C2 = 40,000,000.00 (available 20,000,000.00). Thread A raises C1 to 60,000,000.00, thread B raises C2 to 60,000,000.00, barrier before `_line_position`. Different commitment rows are locked, so neither waits and neither sees the other. Both pass `delta 20,000,000 <= available 20,000,000`. After commit committed = 120,000,000.00, available = −20,000,000.00. Same gap between `adjust_commitment` and a concurrent `reserve_funding` on the same line.
**Impact:** Commitment increases can push a line negative, breaching "positions never negative" without any refusal.
**Verification:** CONFIRMED — budget_commitment_contracts.py:266 locks only the one Procurement Commitment row and :275 reads `_line_position` with plain sums, while reserve_funding locks Budget Line rows (budget_check_reserve_contracts.py:341), so two increases on different commitments, or an increase and a reservation, share no lock.

### AUD-XC-103 — Budget approval/closure and reservation take disjoint lock sets, so successor approval or closure can race a reservation
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** BUD v1.12 §8.2A step 2, BUD-BR-017, BUD-BR-021, BUD-BR-023, BUD19-AC-022 · **Module(s):** Budget · **Sources:** sweep-money F3; trace-budget F-05(b)(c)
**Evidence**
- `kentender_budget/.../budget_readiness_contracts.py:656-661` — approval locks `tabProcurement Budget Version` rows of the Budget (`for update`), then `_evaluate_readiness(version)`; the floor test is `:138` `protected = _reserved_plus_committed(budget_line)` and `:171` `if flt(current.approved_amount) < protected` (plain reads; `_reserved_plus_committed` at :221-225).
- `…/budget_readiness_contracts.py:837` — closure locks the same Version rows, then `version.reload()` and `_closure_status_for`.
- `…/budget_check_reserve_contracts.py:341` — reservation locks `tabProcurement Budget Line` rows only, and reads the Active Version with a plain `_active_version` (`budget_contracts.py:164-173`; called at `budget_check_reserve_contracts.py:142`).
- Neither side writes a row the other locks (reserve inserts a reservation; approve saves Version rows), so no wait or timestamp conflict occurs.
**Rule:** BUD §8.2A step 2 "All Budget activation, closure and decision-validation paths use compatible locks."; BUD-BR-021 "Approval rechecks … floors … and concurrency under one transaction lock before activating."; BUD-BR-017 "A successor cannot reduce a line below its current Reserved plus Committed position."; BUD-BR-023 "A Closed Budget admits no new reservations"; BUD19-AC-022 "commit-time race/stale/failure cannot bypass guards."
**Reproduction / failing test sketch:** (static; not run) (a) Line L approved 100,000,000.00, reserved 70,000,000.00; successor V2 sets L = 80,000,000.00. Thread A `approve_budget_version(V2)` (floor check passes: 70 <= 80), thread B concurrently `reserve_funding` 20,000,000.00 (available 30,000,000.00 under V1). Commit both: approved 80,000,000.00, reserved 90,000,000.00. (b) After FY end with no holds, thread A `close_budget`, thread B `reserve_funding` that read the Version as Active before A committed: a Closed budget with a new Active reservation. Assert `approved >= reserved + committed` and "no Active reservation on a Closed Budget".
**Impact:** Activation or closure can commit a state that BUD-BR-017/023 forbid; the test BUD18-AC-047 requires both orderings and none exists.
**Verification:** CONFIRMED — budget_readiness_contracts.py:657 and :837 lock only Budget Version rows, the floor test (:138,:171) uses plain `_line_position` sums, and reserve_funding locks Budget Line rows only (:341 of check_reserve); neither side writes a row the other locks, so no wait or conflict is possible and both commit.

### AUD-XC-104 — Finance decision "serialised basis" is validated with stale reads after the lock
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** BUD v1.12 §8.2A steps 2-3, BUD-SC-BASIS-RACE, BUD18-AC-047 · **Module(s):** Budget, Planning · **Sources:** sweep-money F4; trace-budget F-13 (race half; the authorisation half is cluster 3 of the xc-authz part)
**Evidence**
- `kentender_budget/.../budget_line_contracts.py:603` — `version = _active_version(budget_name)` (plain read, opens the snapshot); `:609-610` — `select … from \`tabProcurement Budget Version\` … for update` and `…Line Version… for update`; `:611` — `if frappe.db.get_value("Procurement Budget Version", version.name, "status") != "Active"` (plain read of the locked row).
- `:619-626` — line versions re-read with `frappe.get_all` (plain), compared with `expected` revisions.
- `approve_budget_version` holds the Version rows locked for its whole transaction (`budget_readiness_contracts.py:656-657`) and saves the prior Active row (`:672-680`), so a waiting Finance transaction does wait, then resumes with the old snapshot.
- Caller: `kentender_procurement/.../procurement_planning/services/plan_finance.py:273-296` (`confirm_plan_funding`) reads the basis and totals before calling `budget_gateway.validate_plan_affordability_for_decision`.
**Rule:** BUD §8.2A step 2 "Retain protection until the caller commits"; step 3 "Re-read current Active Version … Check expected revisions; stale/missing/ineligible basis fails atomically."; BUD18-AC-047 "A racing Budget activation/closure and positive Finance decision cannot commit a stale basis; test both orderings."
**Reproduction / failing test sketch:** (static; not run) Thread A approves successor V2 (line reduced below the plan's planned total) and holds the Version locks; thread B (`confirm_plan_funding`) already read V1 as Active and blocks at :609. A commits; B resumes, reads V1 status "Active" and V1's line-version rows from its snapshot, passes `expected_revisions`, records the positive Finance decision on a replaced basis. Expected `PLN_FINANCE_STALE`; actual by reading: confirmation succeeds.
**Impact:** A positive Finance decision can be recorded against a Budget basis that was replaced while it waited — the case §8.2A exists to prevent.
**Verification:** CONFIRMED — budget_line_contracts.py:603 reads the Active Version before the `for update` at :609-610 and :611/:619-626 re-read status and line versions with plain reads, so a Finance transaction that waited behind approve_budget_version (which holds the Version locks, budget_readiness_contracts.py:657) resumes with its pre-lock snapshot; BUD §8.2A steps 2-3 (lines 403-412) require the opposite.

### AUD-XC-105 — Budget no-self-approval reads the FIRST submission event, and fails open when the event was never written
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** BUD v1.12 §6, BUD18-AC-028, BUD18-AC-062, BUD19-AC-014 · **Module(s):** Budget · **Sources:** sweep-sod F2, F4; sweep-state F10; trace-budget F-04
**Evidence**
- `kentender_budget/kentender_budget/services/budget_authorization.py:112-122` — `_submitted_by` is `frappe.db.get_value("Budget Audit Event", {"budget_version": …, "event_type": "Budget version submitted"}, ["actor"], order_by="event_at asc")`: the earliest submission.
- `…/budget_authorization.py:125-131` — `_blocked_by_self_approval` returns `_submitted_by(version_name) == user`; used at :141 and :155.
- `…/budget_readiness_contracts.py:572` — the current submitter is stored (`version.submitted_by = frappe.session.user`) but not consulted; each resubmission writes a new event (`:581-588`).
- `…/budget_audit_contracts.py:176-182` — `safe_record_event` swallows any exception; if the submit event is missing `_submitted_by` returns `None`, and `None == user` is False, so nobody is blocked.
- Contrast: Strategy reads newest-first (`strategy_authorization.py:106-109` iterates `list_events`, which orders `timestamp desc`, `strategy_audit.py:73-82`).
**Rule:** BUD §6 "The submitting Budget Officer cannot approve the same version … Enforced from the version's own submission audit event." and "Decision authority is checked against the submission being decided."; BUD18-AC-062 "approval checks the current attempt's submitter for segregation."
**Reproduction / failing test sketch:** (static; not run) Users A (Budget Officer only), E (Budget Approver), B (Budget Officer + Budget Approver). A `submit_budget_version(V)`; E `return_budget_version(V)`; B edits and `submit_budget_version(V)`; B `approve_budget_version(V)`. Expected `AUTH_SEGREGATION_BLOCKED`; actual by reading: `_submitted_by` = A, B is allowed (and A is wrongly blocked on B's attempt). Second path: make the Budget Audit Event insert fail once during submit; the submitter then approves. Extend `LC.TestSelfApprovalSegregation` with the resubmit-by-different-person case (none exists).
**Impact:** A dual-role user can approve their own resubmitted budget version, which activates approved amounts and funding ceilings.
**Verification:** CONFIRMED — budget_authorization.py:112-131 reads the earliest 'Budget version submitted' event (`order_by="event_at asc"`; frappe database.py:574-590 returns the single field as a string), budget_readiness_contracts.py:572 stores the current submitter but it is not consulted, and budget_audit_contracts.py:176-182 swallows a failed event write so `_submitted_by` can be None; BUD lines 329-330 and BUD18-AC-062 (line 1431) require the current attempt.

### AUD-XC-106 — An approved Annual Plan is never dispatched for publication: nothing transmits it, so it never becomes Active
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §5.2.3 table (L457), §5.5.2, §7.2 `PublishAnnualPlan` (L989), PLN18-AC-043 · **Module(s):** Planning, Requisitions · **Sources:** sweep-hazards F-5; trace-planning F-17
**Evidence**
- `procurement_planning/services/plan_governance.py:556` — approval calls `publication_pipeline.commit_approved_plan(...)`, which only writes snapshot, `Plan Publication` and a `Publication Intent` with `dispatch_state: "Committed"` (`publication_pipeline.py:48-95`).
- `publication_pipeline.py:10-14` — docstring: "`publish_annual_plan`, a system worker that would run post-commit via `frappe.enqueue` in production; this bench runs no RQ worker, so callers (tests, seeds) invoke it inline".
- `grep -rn "enqueue" kentender_*` (non-test) finds no `frappe.enqueue`/`enqueue_doc` call in any production file; `kentender_procurement/hooks.py:481-508` lists scheduler jobs (`all` and `hourly`) and none calls `publish_annual_plan` or drains `Publication Intent`.
- Callers of `publish_annual_plan`: `procurement_planning/api.py:422-432` (whitelisted, `is_technical` only, line 430) and `publication_pipeline.py:316` (`retry_publication`, also technical). No automatic path.
- `plan_publication.py:78` — items become `item_state = "Active"` only in `_activate_version`, reached from an acknowledgement (`publication_pipeline.py:208` `activate_plan_version`); `plan_requisition.py:486` refuses a drawdown unless `item.item_state == "Active"`.
**Rule:** PLN §5.2.3 "Approved — publication pending; prerequisites met and no hold | Transmit and reconcile acknowledgement | System"; L454 "Record approval and Strategy snapshot; enqueue publication of exact approved content"; L989 "PublishAnnualPlan — system worker | … Post-commit only; Treasury/hold checks; send exact immutable manifest".
**Reproduction / failing test sketch:** (static; not run) On a site with scheduler running, approve an Annual Plan Version (`ApproveAnnualPlan`) and record Treasury evidence. Version stays "Approved — publication pending", `Publication Intent.dispatch_state = Committed`; wait any number of ticks: no `Publication Attempt` row appears. Only a System Manager calling `…api.publish_annual_plan` moves it. Test: after approval + Treasury evidence, run `frappe.scheduler`'s registered methods once and assert a `Publication Attempt` exists.
**Impact:** The documented approval → publication → Active flow dead-ends at "publication pending"; items never become Active, so Requisition drawdown (`plan_requisition.py:486`) cannot proceed for a real plan unless an operator intervenes by hand.
**Verification:** CONFIRMED — plan_governance.py:556 only calls commit_approved_plan; the sole callers of publish_annual_plan are the technical-only whitelisted api.py:422-432 and retry_publication (publication_pipeline.py:316), hooks.py:481-508 lists no publication job, and the repo has no non-test `frappe.enqueue`; the plan docs (Implementation_Plan.md:35) record only an inline-for-tests workaround, and PLN line 457 assigns transmission to the System. Cited line corrected to plan_publication.py:78 (the `item_state` write).

### AUD-XC-107 — Requisition drawdown rechecks (correction hold, Plan Item state, record version) read a pre-lock snapshot
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** REQ v1.14 §7.2 ("Recheck the hold and allowances at commit under Planning's stable-item guard, not from an earlier UI eligibility result"), REQ19-AC-058, PLN-RI-029 · **Module(s):** Requisitions, Planning · **Sources:** trace-requisition F-03 (hold-bypass half); sweep-money F12 (drawdown bullet)
**Evidence**
- `procurement_requisitions/services/envelope.py:88-98` and `procurement_planning/services/envelope.py:90-99` — `locked()`: `select name … for update` followed by a plain `frappe.get_doc(...)`.
- `procurement_planning/services/scope_lock.py:61` — `guard()` is `envelope.locked("Plan Item", …)`; `:71` — `if root.scope_locked_since: return` (no write, so no timestamp conflict either).
- `procurement_planning/services/plan_requisition.py:484-486` — `item = envelope.locked("Annual Plan Item", …)`; `check_record_version(item, expected_record_version)`; `if item.item_state != "Active" …`; `:492-493` — `root = scope_lock.guard(...)`; `if root.authorisation_hold: fail("PLN_ITEM_AUTHORISATION_HELD")`. The item is never saved here.
- `procurement_requisitions/services/authorise.py:107` (`projection, checks = recheck(...)`) and `:127` (`expected_record_version=projection["record_version"]`): the expected stamp comes from a read in the same transaction, so the comparison is snapshot against snapshot.
- Hold writer: `plan_requisition.py:693` guards, `:704` `scope_lock.recompute_hold(root)` (writes the root).
**Rule:** REQ §7.2 (quoted above); REQ19-AC-058 "Request recording/hold and new authorisation use the same stable-item guard; both race orderings preserve one valid outcome and no acknowledged hold can be bypassed by stale eligibility."
**Reproduction / failing test sketch:** (static; not run) Plan Item whose scope is already locked (`scope_locked_since` set). Thread T1 `receive_plan_item_correction_request` (takes the guard, sets `authorisation_hold`, commits after T2 started). Thread T2 `authorise_requisition` already read the projection, blocks at `scope_lock.guard`, resumes, reads `authorisation_hold = 0` from its snapshot, proceeds and commits an authorisation after the hold was acknowledged. Same shape for a concurrent supersession of the Annual Plan Item. Expected `PLN_ITEM_AUTHORISATION_HELD`; actual by reading: authorised.
**Impact:** A correction hold acknowledged to the Planner can be bypassed by an in-flight authorisation; money moves against a held or superseded item.

### AUD-XC-108 — Award cancellation guard reads `notification_status` from a stale snapshot after taking the Award Case lock
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AWD v0_5 AWD-AC-010, AWD-IF-02, §5.4 · **Module(s):** Award, Tenders · **Sources:** trace-award F7
**Evidence**
- `kentender_procurement/.../award/services/authority.py:83-84` — `frappe.db.sql("select name from \`tabAward Case\` where name=%s for update", name)` then `cstr(frappe.db.get_value(records.CASE, name, "notification_status"))` (plain read).
- `tenders/services/cancellation.py:124` (`draft_commands.load(tender)`) runs before `:130` `award_seam.cancellation_refusals(root.name)`, so Tenders' transaction already has a snapshot when the guard waits.
- Award commands lock the same way: `award/services/records.py:109-113` (`lock`: `for update` then plain `frappe.get_doc`).
**Rule:** AWD AC-010 "Cancel-before-issue and issue-before-cancel interleavings cannot both succeed; in-progress/unknown status never supplies a false no-notification answer."
**Reproduction / failing test sketch:** (static; not run) A (Accounting Officer, Award) records the decision and issues notices, holding the case lock; B (Tenders AO) `cancel_tender` has passed line 124, blocks at the guard's `for update`; A commits `notification_status = "Issued"`; B resumes, reads "Not issued" from its older snapshot and the cancellation proceeds. Expected `TND_MUST_FIX`; actual by reading: no refusal. No test exercises the interleaving.
**Impact:** A Tender can be cancelled in the pre-notification route after award notices were issued.

### AUD-XC-109 — Requisition revocation and handoff consumption take row locks in opposite order (AB-BA)
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** REQ v1.14 REQ19-AC-074, §19 · **Module(s):** Requisitions, Tenders · **Sources:** trace-requisition F-12
**Evidence**
- Revoke: `procurement_requisitions/services/authorise.py:178` `records.require_root(requisition)` (locks the root; `records.py:95-98`) then `:183` `envelope.locked("Authorised Requisition Handoff", root.handoff)`.
- Consume: `procurement_requisitions/services/handoff.py:117` `envelope.locked("Authorised Requisition Handoff", handoff)` then `:118` `envelope.locked("Procurement Requisition", doc.requisition)`.
- Test: `seeds/profiles.py:572` `REQ-SC-REVOKE-CONSUME-RACE` runs the two sequentially ("Consumption wins … the later revocation is refused").
**Rule:** REQ19-AC-074 "RecordHandoffConsumption/TPR creation and REQ revocation share the owner guard; no delayed projection admits revoked consumption or released funds behind a created Tender; failed creation rolls back consumption." §19 asks for a published serialisation order.
**Reproduction / failing test sketch:** (static; not run) Authorised, unconsumed handoff H on requisition R. Thread A `revoke_unconsumed_authorisation(R)` holds R, waits for H; thread B `record_handoff_consumption(H)` holds H, waits for R. InnoDB aborts one with a deadlock error (1213): either revocation or Tender creation fails with a raw exception instead of `REQ_HANDOFF_CONSUMED` / `TND_HANDOFF_CONFLICT`. Fails closed; no corruption found.
**Impact:** Under a race, Tender creation or revocation fails with an untyped deadlock error and no lock-order contract exists.

### AUD-XC-110 — Budget funding-ledger events (20 sites) and Award audit are best-effort: a failed audit write is swallowed after the material action
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** BUD v1.12 §14, §4.7; AGENTS.md §4.3 · **Module(s):** Budget, Award, Bid Opening, Evaluation · **Sources:** sweep-audit F3, F16(1), F16(5); sweep-hazards F-10; sweep-state F14; trace-budget F-17 (swallow half)
**Evidence**
- `kentender_budget/.../budget_audit_contracts.py:176-182` — `safe_record_event`: `try: return record_event(**kwargs) except Exception: frappe.log_error(title="Budget audit record_event failed"); return None`.
- All 20 call sites use it and `record_event` is never called directly elsewhere: `budget_commitment_contracts.py:95,148,229,292`; `budget_check_reserve_contracts.py:279,419`; `budget_readiness_contracts.py:581,622,690,699,867`; `budget_contracts.py:1006,1055`; `budget_line_contracts.py:216`; `budget_revision_request_contracts.py:156,185,207,274,292`; `budget_idempotency.py:71`.
- `budget_check_reserve_contracts.py:405-430` — the `Funding Reservation` is inserted at :418 (`doc.insert`), then `safe_record_event(...)` at :419; if the event insert raises the reservation persists with no ledger row.
- `award/services/records.py:160-169` — `audit()`: `except Exception: frappe.log_error(title="Award audit write failed")`; the same pattern around `log_audit_event` + `frappe.db.commit()` in `bid_opening/api.py:42-50`, and the Award and Evaluation API wrappers.
- Note: `reserved/committed` positions are computed from the reservation/commitment rows, not from ledger events, so money is not altered; what is lost is the audit record, and (AUD-XC-105) the segregation check reads it.
**Rule:** BUD §14 "Append-only events: … reservation creation; revalidation, release, conversion and commitment adjustment"; "Funding Ledger events cannot be edited or deleted"; AGENTS.md §4.3 "audit actor, time, and reason where applicable"; §10 "missing audit evidence".
**Reproduction / failing test sketch:** (static; not run) Patch `record_event` to raise (or add a `before_insert` hook on Budget Audit Event that throws); call `reserve_funding` via REQ authorise. The reservation row commits; no `Budget Audit Event` exists. Assert the call raises or the reservation does not exist.
**Impact:** A funding mutation, a Budget approval or an Award event can commit with no ledger/audit row, leaving silent gaps in an append-only trail.

### AUD-XC-111 — Funding-ledger events omit before/after positions, business role, assignment ID and fiscal year
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** BUD v1.12 §4.7, §14 · **Module(s):** Budget · **Sources:** sweep-audit F4; trace-budget F-17 (content half)
**Evidence**
- `kentender_budget/.../doctype/budget_audit_event/budget_audit_event.json` fields: `budget, budget_version, budget_line, event_type, event_at, reservation, commitment, amount, currency, actor, actor_kind, calling_module, correlation_id, reason, before_*/after_* (approved, reserved, committed, available), idempotency_key, payload_digest, command_result` — no business-role, assignment or fiscal-year field.
- `budget_audit_contracts.py:111-137` — `record_event` accepts `before`/`after`, but `grep -rn "before=\|after=" kentender_budget/kentender_budget/services/*.py` returns no caller passing either, so every `before_*`/`after_*` column is NULL.
**Rule:** BUD §4.7 "before and after approved, reserved, committed and available positions; actor or calling service, timestamp and correlation ID"; §14 "Each event records actor or calling service, business role, the exercised responsibility assignment ID, fiscal year, relevant IDs, action, timestamp, before and after status or line position, required decision reason, correlation ID and calling module."
**Reproduction / failing test sketch:** (static; not run) Run `reserve_funding` for 10,000,000.00, read the `Budget Audit Event`: `before_reserved`, `after_reserved` etc. are NULL; no role or assignment is stored. Assert `after_reserved - before_reserved == amount`.
**Impact:** The ledger cannot reconstruct positions or the authority exercised at the time of each funding movement.

### AUD-XC-112 — Denial events required by STR §13 / BUD §14 are never written, or are written and rolled back
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** STR v1.9 §13; BUD v1.12 §14; AUTH-ADR-001 v1.11 §15 · **Module(s):** Strategy, Budget, Core · **Sources:** sweep-audit F5, F12
**Evidence**
- `kentender_budget/.../budget_audit_contracts.py:38-39` define `EVENT_PERMISSION_DENIED`/`EVENT_CONCURRENCY_CONFLICT`; `grep -rn "EVENT_PERMISSION_DENIED\|EVENT_CONCURRENCY_CONFLICT" --include=*.py` finds only those two definitions. Refusals return `{"ok": False, "code": "BUDGET_STALE_WRITE", …}` (`budget_readiness_contracts.py:540-545`) with no event.
- `kentender_strategy/.../strategy_authorization.py:131-146` — `require_plan_version_capability` calls `fail("AUTH_SEGREGATION_BLOCKED")` / `fail(decision.reason_code …)`; `grep -n record_event strategy_authorization.py` returns nothing.
- `kentender_core/.../authorization_policy.py:188-215` — `require_capability` writes `log_audit_event(event_type="authorization.denied", …)` then `frappe.throw(…, frappe.PermissionError)`. Frappe `app.py:138-141` — `except Exception … db.rollback(chain=True)`: the denial row is rolled back with the request. Production callers: `workflow_tasks.py:139,154,177,198`, reached from the whitelisted My Work claim (`my_work.py:225-227`).
**Rule:** STR §13 "Append-only events: … responsibility or segregation denial; successful and failed context resolution …"; BUD §14 "responsibility, segregation, floor and concurrency denial"; AUTH §15 "Every protected decision retains … segregation result".
**Reproduction / failing test sketch:** (static; not run) As the Strategy submitter call `approve_strategy_version` on your own submission: `AUTH_SEGREGATION_BLOCKED`; `frappe.get_all("Audit Event", filters={"document_name": <version>})` has no denial row. As a user without the capability, POST My Work claim for a task, then query `Audit Event` where `event_type = 'authorization.denied'`: none persists. Assert a committed denial event after the failed request.
**Impact:** The denial trail STR and BUD require does not exist; the one denial write that exists is undone by the same exception that reports it.

### AUD-XC-113 — Reads of sealed/confidential bid pages and opening exports create no audit event
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** OVS v0_6 (L102, L154), BOP v0_11 §12, TRUST-ADR-001 v0_2 · **Module(s):** Bid Opening, Suppliers · **Sources:** sweep-audit F13
**Evidence**
- `kentender_procurement/.../bid_opening/services/pages.py:1-13` — docstring "Reading records no event."; `bid_pages` (:28-38) returns `{"filename": …, "content": content}` with no `log_audit_event`.
- `bid_opening/services/export.py:41-58` — `export_opening` returns the whole opening bundle (entries, register, handoff, proceedings) with no audit call (`grep -n "audit" export.py` hits only the docstring).
- `grep -rn "make_access_log\|Access Log\|access_log" kentender_*` returns nothing outside Frappe. `supplier_accounts/services/evidence.py:78-90` `get_account_evidence_file` returns the file with no event while upload is audited (:72).
- Doc text: OVS L154 "Existing security/access logging continues; viewing creates no business approval, decision or task-completion event."; BOP §12 lists attendance, register request, minutes and handoff but no page read.
**Rule:** OVS v0_6 L102 sealed contents stay excluded; L154 "Existing security/access logging continues". The documents rely on an access log that the code does not produce and do not say what an access record contains.
**Reproduction / failing test sketch:** (static; not run) As a committee member after reveal, open bid pages and call `export_opening`; query `Audit Event` for the Tender: no row. **Owner decision needed:** is the access record Frappe `Access Log` or a module event, what fields it carries, and whether reading sealed content must be a business audit event.
**Impact:** Access to revealed bid content and full opening exports leaves no attributable record.

### AUD-XC-114 — Opening-register download delivery record and audit event are written inside a GET and rolled back
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** BOP v0_11 §12 ("register/copy request/fulfillment"); function docstring · **Module(s):** Bid Opening · **Sources:** sweep-audit F6
**Evidence**
- `kentender_procurement/.../bid_opening/api.py:333-337` — `@frappe.whitelist(methods=["GET"]) def download_opening_register(...)` → `_call("GetOpeningRegisterCopy", …, register_copy.get_register_copy)`.
- `bid_opening/services/register_copy.py:127-134` — `row.update({"status": "Delivered", "delivered_at": clock.now()}); records.save(row)` then `log_audit_event(event_type="Opening register downloaded", …)`; no commit (`grep commit` on `register_copy.py`, `records.py` and `audit_event_service.py:32` shows none).
- Frappe `app.py:417-428` `sync_database`: `if request.method in UNSAFE_HTTP_METHODS or flags.commit: commit else: rollback`; `grep -rn "flags.commit" kentender_v1` finds no setter.
- The docstring (`register_copy.py:121-123`): "the first download is recorded as the delivery, and every download is audited."
**Rule:** BOP §12 register/copy fulfilment is an audited step; Frappe: a GET is rolled back.
**Reproduction / failing test sketch:** (static; not run) Requester with a Ready copy calls `GET /api/method/kentender_procurement.bid_opening.api.download_opening_register?tender_reference=…`. After the response the request row is still `Ready`, `delivered_at` empty, and no `Opening register downloaded` event exists. Drive through `frappe.handler` as GET and assert the rows.
**Impact:** The delivery of the statutory opening register copy is neither recorded nor audited; the copy can be downloaded repeatedly with no trace.

### AUD-XC-115 — Plan affordability and method-limit tests compare float sums with a 1e-9 epsilon
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §4.1 (Money), §5.5.3.3; BUD v1.12 §4.8, BUD-SC-PRECISION · **Module(s):** Planning, Budget · **Sources:** sweep-money F6, F7; sweep-handoffs F-12; trace-planning F-07 (arithmetic half)
**Evidence**
- `procurement_planning/services/readiness.py:164-179` — `line_totals`: `totals[a.budget_line] = totals.get(a.budget_line, 0.0) + flt(a.indicative_amount)`; `plan_finance.py:46-51` passes them to `check_plan_affordability`.
- `kentender_budget/.../budget_line_contracts.py:496` and `:646` — `within_approved = planned <= pos["approved"] + 1e-9`; also `budget_revision_request_contracts.py:130`, `procurement_planning/services/budget_revision.py:72,161`, `departmental_update.py:110`, `plan_read.py:1129`.
- `readiness.py:391` — `value = sum(flt(a.indicative_amount) for a in allocations)` feeds `profiles.method_conditions`; `profiles.py:232` `Decimal(str(flt(planned_value)))` keeps the float noise; `:242` `ok = (minimum <= 0 or value >= minimum) and (maximum <= 0 or value <= maximum)`.
- `readiness.py:498-503` — low-value cap: `totals[key] = totals.get(key, 0.0) + item_value(item.name)`; `if cap and total > cap`.
- 1e-9 is below one float ulp for amounts above about KES 8 million.
- Computed in plain Python: 44,872,648.85 + 28,586,332.99 + 80,884,095.33 + 29,789,404.90 as floats = `184132482.07000002`; `planned <= 184132482.07 + 1e-9` is False. 242,653.82 + 201,170.23 + 56,175.95 = `500000.00000000006`; `value <= 500000.00` is False.
- Also float: Tender totals `tenders/services/snapshot.py:112-115` (`float(sum(float(...)))`), REQ display `procurement_requisitions/services/read.py:606-607`.
**Rule:** PLN §4.1 "Exact decimal currency-unit value, never binary float"; BUD §4.8 "no `flt()`, epsilon equality or silent rounding"; BUD-SC-PRECISION "decimal arithmetic has no epsilon path"; PLN §5.5.3.3 per-method limits are legal thresholds.
**Reproduction / failing test sketch:** (static; not run) One Budget Line approved 184,132,482.07 and four allocations 44,872,648.85, 28,586,332.99, 80,884,095.33, 29,789,404.90 (exactly the approved amount): `check_plan_affordability` gives `PLN_PLAN_NOT_AFFORDABLE` (excess 2.98e-08, shown as "over by KES 0.00") and `RequestBudgetRevision` is accepted. A Plan Item with the three allocations above under a method whose `maximum_amount` is 500,000.00 reports the condition "Not met" and, if mandatory, `PLN_METHOD_NOT_ADMISSIBLE`. Pure-Python pair: `sum(map(float, parts)) <= float(Decimal(total)) + 1e-9`.
**Impact:** A plan that exactly meets its budget line or a legal method limit is refused or sent for budget revision; the fix is to move a cent.

### AUD-XC-116 — Budget position, floor and `Needs Attention` tests use float arithmetic
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** BUD v1.12 BUD-BR-016, BUD-BR-017, §4.8 · **Module(s):** Budget · **Sources:** sweep-money F8
**Evidence**
- `kentender_budget/.../budget_contracts.py:215` — `available = approved - reserved - committed` (floats from `_line_position`, :196-214).
- `budget_commitment_contracts.py:90` — `new_status = "Needs Attention" if pos["available"] < 0 else …`.
- `budget_readiness_contracts.py:171` — `if flt(current.approved_amount) < protected` with `protected = pos["reserved"] + pos["committed"]` (:221-225).
- Computed in plain Python: `843171926.93 - 535955290.08 - 307216636.85 = -5.96e-08`; `47235303.96 + 650184912.59 = 697420216.5500001 > 697420216.55`.
**Rule:** BUD-BR-016 "`Needs Attention` keeps the remaining amount reserved while downstream progression is blocked" (only on a real breach); BUD-BR-017 "cannot reduce a line below its current Reserved plus Committed position"; BUD §4.8 no `flt()`/epsilon.
**Reproduction / failing test sketch:** (static; not run) Approved 843,171,926.93 = reserved 535,955,290.08 + committed 307,216,636.85: `revalidate_reservations` sets every reservation on the fully subscribed line to `Needs Attention` (the exact answer is 0.00). A successor setting a line to exactly 697,420,216.55 against reserved 47,235,303.96 + committed 650,184,912.59 is refused with a floor breach and a "shortfall" of KES 0.0000001.
**Impact:** Exactly-balanced lines are misclassified as breached, blocking downstream progression, or a lawful successor is refused.

### AUD-XC-117 — Money inputs are not validated as exact decimals: NaN/Inf, excess scale, 0.01 and 0.0001 tolerances
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** BUD v1.12 §4.8, BUD18-AC-051; PLN v1.29 §4.1 · **Module(s):** Budget, Planning · **Sources:** sweep-money F9; trace-planning F-07 (input half); trace-budget F-06 (input half)
**Evidence**
- `kentender_budget/.../budget_line_contracts.py:143,165-166` — `approved_amount = flt(row.get("approved_amount"))`; `if approved_amount <= 0`. `budget_contracts.py:905-910` — `total_val = flt(total)`; `if not total or total_val <= 0`.
- `procurement_planning/services/dpp_lifecycle.py:359` `entry.indicative_amount = flt(indicative_amount)` and `:442` `if flt(indicative_amount) <= 0`; the whitelisted `save_need_funding(…, indicative_amount=None)` (`api.py:79-85`) passes the raw value. Only the REQ drawdown boundary uses `money.parse_money` (`plan_requisition.py:512-513`; the strict parser is `money.py:45-64`).
- `frappe.utils.flt("nan")` → `nan`, `flt("inf")` → `inf` (executed in the bench virtualenv, no site): `nan <= 0` is False, so both pass every positivity guard.
- `budget_readiness_contracts.py:71` `"match": abs(diff) < 0.01` and `:197` `difference >= 0.01` (line total vs authorised total; transfer balance).
- `budget_commitment_contracts.py:199` `if amount > remaining + 0.0001`; `release_reservation`, `convert_reservation`, `adjust_commitment` take `float` (`budget_api.py:285-337`).
- Currency field type is `decimal(21,9)` (`frappe/database/mariadb/database.py:172`), so a value such as 1000000.005 is not rejected at storage.
- Not a defect (checked): over-conversion by less than 0.0001 is blocked later by `non_negative` on `Funding Reservation.remaining_amount` (`funding_reservation.json:143-148`; `frappe/model/document.py:816-833`), as an untyped `NonNegativeError`.
**Rule:** BUD §4.8 "Inputs with more fractional digits than supported are rejected"; "no `flt()`, epsilon equality or silent rounding"; BUD18-AC-051 "float JSON, malformed and overflow values fail before effects"; BUD-BR-004 "the version line sum shall equal `authorised_total`"; PLN §4.1 "Reject excess precision rather than rounding".
**Reproduction / failing test sketch:** (static; not run) Authorised total 100,000,000.00 with lines 60,000,000.004 and 40,000,000.004: difference −0.008, `abs(diff) < 0.01`, so the version submits and approves. `save_need_funding(indicative_amount="1000000.005")` is accepted; `indicative_amount="nan"` passes `<= 0` and fails later at the database (HTTP 500). Assert typed `*_MONEY_PRECISION_INVALID` (the Budget `_exact_money` at `budget_check_reserve_contracts.py:66-82` already exists and is not reused here).
**Impact:** Budget approval can activate lines that do not equal the authorised total, and Planning/Budget amounts of any scale or non-finite value enter the funding chain.

### AUD-XC-118 — Need quantity is a 3-decimal Float with no unit-of-measure precision or whole-number rule
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §4.3, §4.9, NDS11-AC-005, NDS11-AC-077, NDS-SC-UOM-PRECISION, `NDS_QUANTITY_PRECISION_INVALID` (L696) · **Module(s):** Departmental Needs, Requisitions · **Sources:** trace-needs C-22; trace-requisition F-20
**Evidence**
- `kentender_procurement/.../departmental_needs/doctype/departmental_need_revision/departmental_need_revision.json:94-97` — `indicative_quantity`, `fieldtype: Float`, `precision: 3`.
- `departmental_needs/services/lifecycle.py:453` `if flt(version.indicative_quantity) <= 0`; `:503` `"indicative_quantity": flt(indicative_quantity) …`; `services/events.py:83` emits `flt(version.indicative_quantity)`. No unit-of-measure precision or whole-number lookup exists (`grep -rn "whole\|QUANTITY_PRECISION" departmental_needs/services` finds none).
- Requisitions: `requisition_item.json:57-60` quantity is `Int` (max 2,147,483,647) although REQ §5.14 asks for 18-integral-digit capacity; whole-number Each is the REQ product rule (L398).
**Rule:** NDS NDS-SC-UOM-PRECISION "Each whole-number fixture rejects 1.5 … No global three-decimal assumption or float tolerance."; NDS11-AC-005 "Quantity is an exact positive decimal string within supported UOM precision/whole-number and storage range."; NDS11-AC-077 "Each fractional quantity/excess precision/overflow fails without rounding."
**Reproduction / failing test sketch:** (static; not run) `save_need_draft(… indicative_quantity=1.5, unit="Each")`, submit, accept: the accepted event carries `1.5` as a JSON number for a whole-number unit; `0.0004` is stored as the 3-decimal rounding. Tests pin the old rule (`T-LC:735`, `T-DM:178` per the trace).
**Impact:** Fractional equipment quantities enter the Need → Plan → Requisition chain, and quantity crosses the wire as a float.

### AUD-XC-119 — Budget optimistic-lock stamp is optional on every command, and a line save never moves it
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** BUD v1.12 §9.2 ("Every write requires the expected record version"), §12.5; STR v1.9 §8; KT-STD-001 v1.25 §4/§11 · **Module(s):** Budget, Strategy · **Sources:** sweep-money F10; trace-budget F-21; trace-strategy F9; sweep-state F12 (stamp half)
**Evidence**
- `kentender_budget/.../budget_readiness_contracts.py:546-548` — `_is_stale`: `return bool(expected) and str(version.modified) != str(expected)`; used by submit, return, approve, close. Same optional test at `budget_contracts.py:982-983` (draft save) and `budget_line_contracts.py:92-94` (lines save).
- `budget_line_contracts.py:176-225` — `_save_budget_lines_draft` edits/inserts `Procurement Budget Line Version` rows and ends with `version.reload()`; the parent Version is never saved, so `Version.modified` (the stamp) does not change after a lines save.
- Strategy: `strategy_transitions.py:61-64` `_check_expected_version`: `if expected_version is None: return`; `strategy_consumer_api.py:105-240` default `expected_version=None`/`idempotency_key=None`; `create_strategy_successor_version` (`:118-125`) has no token at all.
- The Vue editor sends the stamp (`BudgetVersionEditorScreen.vue:303,327`), so the gap is for direct API callers and for the unmoved stamp.
**Rule:** BUD §9.2 L494 "Every write requires the expected record version."; STR §8 L309 same; KT-STD-001 v1.25 §11 (L853) "Every state command carries `expected_version`; a stale command has no partial effect. Every retriable command carries an idempotency key."
**Reproduction / failing test sketch:** (static; not run) Officers A and B open the editor (stamp M0). A saves line X = 50,000,000.00 (stamp stays M0). B saves X = 60,000,000.00 with stamp M0 → accepted, A's saved amount is overwritten (a transaction overlap would raise Frappe's `TimestampMismatchError`; sequential edits are not caught). `approve_strategy_version(plan_version_id)` with no `expected_version` skips `STRATEGY_STALE_WRITE`; `submit_budget_version` with `expected_modified` omitted skips the check.
**Impact:** Budget line edits and Strategy/Budget decisions can overwrite newer saved work or decide on a changed version without refusal.

### AUD-XC-120 — Strategy idempotency journal is keyed without payload, replays before authorisation, and its race leaves duplicate effects
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** STR v1.9 §8.2, STR18-AC-004, STR18-AC-008; KT-STD-001 v1.25 §11 · **Module(s):** Strategy · **Sources:** trace-strategy F8; sweep-state F12 (key half)
**Evidence**
- `kentender_strategy/.../services/strategy_idempotency.py:19-44` — lookup by `idempotency_key` alone (`frappe.db.get_value("Strategy Command Journal", {"idempotency_key": key}, "result")`), returned as soon as found (no document, action or payload comparison); then `result = fn()`; then insert; `except frappe.DuplicateEntryError` returns the winner's journalled result.
- `strategy_command_journal.json:19-23` — `idempotency_key` is `unique: 1`.
- `api/strategy_consumer_api.py:106-115` — `save_strategy_plan_draft` calls `run_idempotent(...)` before any authorisation; the capability check happens inside `fn`.
- (Contrast: Budget's `budget_idempotency.py:49-82` digests the payload and returns `BUDGET_IDEMPOTENCY_CONFLICT` on mismatch.)
**Rule:** STR §8.2 "Retries of one command reuse its identity and payload … no duplicate plan/version/task/event"; STR18-AC-008 "no duplicate plan/version/task/event"; KT-STD-001 §11 "returns the original committed result on replay".
**Reproduction / failing test sketch:** (static; not run) (a) Reuse key K for `approve_strategy_version(B)` after it was used for version A: returns A's result, no effect on B and no conflict error. (b) Two simultaneous `save_strategy_plan_draft` POSTs with the same key and new plan: the second misses the lookup, runs `fn()` (creating a second Strategic Plan row in its transaction), and its journal insert then fails on the unique index; the except-branch returns the winner's result but the second transaction's side effects stay and commit. (c) Any logged-in caller replaying a known key and payload receives the stored result without authorisation.
**Impact:** A repeated or racing command can create duplicate plans/versions while returning the first result, and a key can be reused across documents with no error.

### AUD-XC-121 — `PublishAnnualPlan` re-sends after an Indeterminate result; `PLN_PUBLICATION_FAILED`/`UNKNOWN` are never produced
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §5.5.2.3, §7.2 (L991), L811, L2810 · **Module(s):** Planning · **Sources:** trace-planning F-27, F-30
**Evidence**
- `procurement_planning/services/publication_pipeline.py:129-132` — `publish_annual_plan` only requires `version.version_status in ("Approved — publication pending", "Publication failed")` plus no hold and current Treasury evidence; an `Indeterminate` attempt leaves the status "Approved — publication pending" (the Indeterminate branch sets only `publication_state` and `dispatch_state`, `:154-156`), so a second call reaches `_transmit` again (`:142`). Only `retry_publication` checks state (`:314-315`), and it is a separate entry point.
- `grep -rn "PLN_PUBLICATION_FAILED\|PLN_PUBLICATION_UNKNOWN" --include=*.py` (non-test) returns only `errors.py:83-84,147-148`; `next_step.py:449-482` (`_publication_state`) renders the condition without a reason code.
**Rule:** PLN §7.2 `RetryPublication` "indeterminate must reconcile first" (L991); L2810 "No … blind unknown-outcome retry/withdrawal"; L811 next-step contract names `PLN_PUBLICATION_FAILED` / `PLN_PUBLICATION_UNKNOWN`.
**Reproduction / failing test sketch:** (static; not run) Set the destination's `sandbox_outcome = "Indeterminate"`; call `…api.publish_annual_plan` twice as a technical user: two `Publication Attempt` rows and two transmissions. Assert the second call is refused until `reconcile_publication`. Assert the blocker list for a Failed/Indeterminate publication carries the documented codes.
**Impact:** A plan whose publication outcome is unknown can be transmitted twice (duplicate publication) and the operator is not told the documented reason code.

### AUD-XC-122 — Strategy §13 audit list is incomplete (consumer reads, context resolution) and two events omit attribution
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** STR v1.9 §13 · **Module(s):** Strategy · **Sources:** sweep-audit F8
**Evidence**
- `kentender_strategy/.../services/strategy_consumer.py` — `resolve_strategy_context` (:76), `list_strategy_objectives` (:176) and `get_strategy_lineage` (:225) contain no audit call; the only consumer audit is `create_strategy_snapshot` (:325-335), which passes no calling module, business role or assignment.
- `strategy_transitions.py:136-144` — the supersede event `record_event(entity_type="Strategic Plan Version", …, event_type="Approve successor", prior_state="Active", new_state="Superseded", …, summary=…)` omits `business_role`, `assignment`, `capability` and `correlation_id`, while the Approve event at `:200-212` carries them.
**Rule:** STR §13 "Append-only events: … successful and failed context resolution; Strategic Objective listing and lineage reads by a downstream module; and snapshot creation or idempotent reuse. Each event records actor, business role, the exercised responsibility assignment ID, record and version IDs, action, timestamp, before and after status, required reason and correlation ID. A downstream contract event also records the calling module."
**Reproduction / failing test sketch:** (static; not run) Call `resolve_strategy_context` (success and `STRATEGY_CONTEXT_NOT_FOUND`), `list_strategy_objectives`, `get_strategy_lineage`; query `Audit Event` for those actions: zero rows. Approve a successor and read the "Approve successor" event metadata: no `business_role`, `assignment`, `correlation_id`.
**Impact:** Downstream use of Strategy is untraceable and the supersede event cannot be tied to the authority that caused it.

### AUD-XC-123 — Planning and Requisition command journals do not record the exercised authority, role or request id
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §12 (L2270); REQ v1.14 §15 (L1512, L1528) · **Module(s):** Planning, Requisitions · **Sources:** sweep-audit F9
**Evidence**
- `Planning Command Journal` and `Requisition Command Journal` fields (JSON): `idempotency_key, command, document_type, document_name, request_fingerprint, actor, result, occurred_at, fixture_namespace` — no assignment, role, request id or old/new values.
- `procurement_planning/services/envelope.py:63-86` and `procurement_requisitions/services/envelope.py:61-86` (`record_command`) write exactly these fields; REQ `_journal` (`draft_commands.py:46-48`) passes only the actor. `Requisition Event` fields: `event_id, event_type, requisition, sequence, requisition_version, occurred_at, payload, status, consumer, delivered_at` — no actor or authority.
- The decision doctypes do carry `authority_snapshot` (`requisition_decision.json`), so only decision-less commands (REQ Draft writes, `withdraw_departmental_submission`, `hold_plan_publication`) lack it.
**Rule:** PLN §12 "Every command records its exact input/output identities, expected/resulting token, actor or authenticated producer, exercised authority, prior/resulting states, idempotency correlation …"; REQ §15 "Audit records contain actor, business role, the exercised responsibility assignment ID, server time, request ID and idempotency key" and "old and new values for each Draft change".
**Reproduction / failing test sketch:** (static; not run) Run `save_requisition_summary` or `hold_plan_publication` and read the journal row: actor and fingerprint only. Old/new values exist only in Frappe `Version` rows (deletable), which are not an audit contract.
**Impact:** The authority under which a Draft change or a publication hold was made cannot be reconstructed from the Planning or Requisition trail.

### AUD-XC-124 — Departmental Need Decision stores a bare assignment ID, not the snapshot NDS §4.5 requires
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §4.5 (L262), §13; AUTH-ADR-001 v1.11 §15 · **Module(s):** Departmental Needs · **Sources:** sweep-audit F10
**Evidence**
- `departmental_need_decision.json` fields include `actor, effective_assignment, scope, review_task, …` and no snapshot field; `departmental_needs/services/lifecycle.py:220` `"effective_assignment": cstr(assignment)`.
- `kentender_core/services/authorization.py:517` defines `assignment_snapshot`; the Tenders, Requisitions and Planning authorization modules use it (`tender_authorization.py:189`, `requisition_authorization.py:252`, `planning_authorization.py:316`); `grep -rn "assignment_snapshot(" departmental_needs` finds no caller.
- (Strategy stores the assignment ID in event metadata, `strategy_audit.py:56-61`; Budget stores nothing, see AUD-XC-111; those documents ask for the ID only.)
**Rule:** NDS §4.5 "exact User Responsibility Assignment ID and snapshot"; AUTH §15 "Every protected decision retains: assignment ID; user; business role; Organisation Unit scope; appointment type and authority reference where applicable; effective period evaluated …"; "Later changes to an assignment never rewrite historical decision evidence."
**Reproduction / failing test sketch:** (static; not run) Accept a Need, read the `Departmental Need Decision`: only the `effective_assignment` string. Revoke or edit the assignment later; the decision no longer shows the role, period or scope it was exercised under.
**Impact:** NDS decision evidence is not self-contained against later assignment changes.

### AUD-XC-125 — A post-model-sync patch deletes the DocType records of two doctypes the app still ships, and the next patch wipes the table
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AGENTS.md §4.5 (patches idempotent), §4.4 · **Module(s):** Strategy · **Sources:** sweep-hazards F-6
**Evidence**
- `kentender_strategy/kentender_strategy/patches/mvp1_teardown_drop_legacy_strategy_doctypes.py:12-20` `LEGACY_DOCTYPES` includes `"Strategy Node"` and `"Strategic Plan"`; `:56-58` `frappe.delete_doc("DocType", name, force=1, ignore_permissions=True)`.
- Both doctypes are current: `kentender_strategy/kentender_strategy/kentender_strategy/doctype/strategic_plan/` and `…/strategy_node/` exist.
- `kentender_strategy/kentender_strategy/patches.txt` lists the patch first under `[post_model_sync]` (after model sync created them), followed by `str_chg_001_phase1_domain_model_rebuild`, whose `execute()` does `if frappe.db.table_exists("Strategic Plan"): frappe.db.sql("DELETE FROM \`tabStrategic Plan\`")` (`str_chg_001_phase1_domain_model_rebuild.py:36-37`).
- The patch docstring authorises disposal only for the dev site ("no production data exists", owner 2026-08-23).
**Rule:** AGENTS.md §4.5 "Retriable commands, seeds, patches, and integrations must be idempotent."; §4.4 "Persistent schema and data changes require explicit DocType changes and patches/migrations." A patch that deletes the schema of a doctype the app currently ships is not idempotent across a site that has not logged it.
**Reproduction / failing test sketch:** (static; not run) On `kentender-test.local` restore a pre-patch backup (Patch Log lacks both entries), `bench migrate`: model sync creates Strategic Plan / Strategy Node, patch 1 deletes both DocType rows (Strategy pages fail until the next migrate re-syncs), patch 2 empties `tabStrategic Plan`. On the dev site both are logged, so nothing is visible.
**Impact:** Upgrading any site that has not run these patches (restored backup, rebuilt droplet from an older dump) destroys Strategy plan rows and breaks the Strategy module until a second migrate. Frappe skips controller-file deletion while migrating (`delete_doc.py:128-137`), so source files are not removed.

### AUD-XC-126 — Dropped-doctype crash class still present: post-sync patches and a whitelisted TM2 export touch dropped tables
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AGENTS.md §4.4; project calibration item "dropped doctype" · **Module(s):** Planning (patches), TM2 · **Sources:** sweep-hazards F-8; this part's runtime grep
**Evidence**
- `kentender_procurement/patches.txt:23` — `pln_chg_001_v12_drop_legacy_planning_doctypes` (pre_model_sync) drops `Procurement Plan`, `Procurement Plan Version`, `Procurement Plan Item` and others with `drop table if exists` (`pln_chg_001_v12_drop_legacy_planning_doctypes.py:18-50`).
- Post-sync patches then call `frappe.db.has_column` on those tables with no `table_exists` guard: `patches/pln_revision_schema_backfill.py:20,28,37,46,70` and `_add_index("tabProcurement Plan…")` (`:53-66`); `patches/pln_chg_016_schema_cleanup.py:10-12`; `patches/scope_pln_formation_batch_key.py:13-16` (`show index from tabProcurement Plan Item`). Listed at `patches.txt:67,68,70`.
- Frappe: `Database.has_column` → `get_table_columns` raises `TableMissingError` for an absent table (`frappe/database/database.py:1348-1357`). The repo's own newer patches guard with `table_exists` (`pln_revision_preflight.py`).
- Runtime path (new in this audit): `tender_management/services/export_tender_evidence.py:251` `frappe.db.exists("Procurement Package", pkg_name)` and `:261` `frappe.db.exists("Procurement Plan", plan_name)`; both doctypes are dropped by patches (`mvp1_drop_pp2_planning_doctypes.py:18-19`, `pln_chg_001_v12_…:18-26`) and ship in no app. Reachable through `tender_management/api/tm2_workbench.py:212-239` (`export_workbench_tender_evidence`, `@frappe.whitelist()`) whenever a TM2 Tender has a non-empty `procurement_package` or `procurement_plan` (the latter is a required Link on `tm2_tender.json:135-139` to the non-existent doctype). Also `planning_tender_handoff_configuration.py:37-39` and `planning_tender_handoff_audit.py:47` (no caller found).
**Rule:** AGENTS.md §4.5 patches idempotent; the project's recorded hazard "dropping a doctype's table turns every later `db.exists`/`get_value` against it into a crash".
**Reproduction / failing test sketch:** (static; not run) (a) Restore a backup lacking `pln_revision_schema_backfill` in Patch Log; `bench migrate`: the pre-sync patch drops the tables, `pln_revision_schema_backfill` raises `TableMissingError`, migrate aborts. (b) On the test site create or seed a TM2 Tender with `procurement_package` set and call `export_workbench_tender_evidence` as a permitted user: `frappe.db.exists("Procurement Package", …)` hits a table that does not exist.
**Impact:** Migrating a site that is behind aborts mid-way; the legacy TM2 evidence export can crash for any tender carrying plan/package links.

### AUD-XC-127 — One-shot destructive patches have no environment or non-empty guard
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** AGENTS.md §4.4/§4.5; owner authorisations quoted in the patch docstrings (dev-site, 18 and 21 Sep 2026) · **Module(s):** Tenders, Bid Submission, Planning, Strategy, Needs · **Sources:** sweep-hazards F-7
**Evidence**
- `kentender_procurement/patches/tpr_chg_001_v08_retire_tender_preparation.py:52-72` drops nine Tender Preparation doctypes and tables ("no data migration").
- `bds_chg_001_v08_retire_bid_slice.py:34-47` `DELETE FROM` Electronic Bid Submission / IT Bid Opening Record / Electronic Bid Audit Event, unconditional.
- `tpr_fu25_retire_candidate_stand_in.py:19-22` `frappe.db.delete("Tender Candidate Registration")`.
- `p6_clear_procurement_tender_dev.py:63` `delete from \`tabProcurement Tender\`` (note `table_exists("tabProcurement Tender")` at :62 passes the table name where a doctype name is expected, so that statement may never run).
- `pln_chg_001_v12_drop_legacy_planning_doctypes.py:34-50` drops nine planning doctypes with rows.
- Only the NDS teardown patches fail closed on non-seed rows (`nds_chg_001_v11_drop_retired_need_doctypes.py:46-72`).
**Rule:** No approved document says whether production sites are exempt from, or must be pre-checked for, these removals; the docstrings cite dev-site owner instructions. **Owner decision needed:** state that these patches may run only on sites with no production rows, or require each to refuse non-empty tables.
**Reproduction / failing test sketch:** (static; not run) Deploy the app to a site that has live Tender Preparation or bid rows and has not recorded these patches; `bench migrate` drops/deletes them without prompt.
**Impact:** A production upgrade across these patches silently destroys business rows. Not shown to have happened (fresh installs mark patches run).

### AUD-XC-128 — Organisation Unit commands and Award Settings changes write no audit event
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** AUTH-ADR-001 v1.11 §8 ("validated and audited"), §9.2; AWD v0_5 §12 · **Module(s):** Core, Award · **Sources:** sweep-audit F14
**Evidence**
- `kentender_core/kentender_core/services/organisation_structure.py:261` `add_organisation_unit`, `:308` `rename_organisation_unit`, `:328` `set_organisation_unit_active` — `grep -n "log_audit_event\|audit" organisation_structure.py` returns nothing; `Organisation Unit` has `track_changes` only (Frappe Version).
- `award/doctype/award_settings/award_settings.json:159` System Manager write, `:175` `track_changes: 1`; the controller is `pass`; the document holds the legal profile (`profile_id`, `verified`, `reviewer`, `reply_days`, …).
**Rule:** AUTH §8 "These writes take effect on save … and are validated and audited."; AWD §12 expects statutory evidence to be retained.
**Reproduction / failing test sketch:** (static; not run) Rename an Organisation Unit via the System setup command; `Audit Event` has no row (a deletable Frappe Version row exists). Edit Award Settings `verified` as System Manager; same.
**Impact:** Structure and statutory-profile changes cannot be attributed from the audit store.

### AUD-XC-129 — Frappe `Currency` storage (decimal 21,9) cannot hold the 18 integral digits the documents require
**Severity:** Low · **Classification:** SPEC GAP · **Doc:** BUD v1.12 §4.8 (Storage/calculation), BUD-SC-PRECISION, BUD18-AC-051; PLN v1.29 §4.1; REQ v1.14 §5.14; NDS v1.16 NDS11-AC-077 · **Module(s):** Budget, Planning, Requisitions, Needs · **Sources:** trace-budget F-06 (storage half); trace-requisition F-11
**Evidence**
- `apps/frappe/frappe/database/mariadb/database.py:172` — `"Currency": ("decimal", "21,9")` (12 integral digits); values read back as `float` (`:162` `FIELD_TYPE.NEWDECIMAL: float`).
- Budget/Planning money fields are Frappe `Currency` (e.g. `funding_reservation.json:143-148`); REQ item quantity is `Int` (`requisition_item.json:57-60`).
- The documents name no storage mechanism; BUD18-XD-002 (L1660) "Release prerequisite" for a shared exact-decimal suite and storage scan is open.
**Rule:** BUD §4.8 "At least 18 integral digits plus supported fractional digits. Exact decimal addition/subtraction/comparison throughout persistence … Overflow fails before mutation."
**Reproduction / failing test sketch:** (static; not run) Round-trip `"999999999999999999.99"` through `save_budget_lines_draft` and read back (BUD-SC-PRECISION); expect exact string or a typed precision error. Amounts at or above 1,000,000,000,000 KES overflow `decimal(21,9)`.
**Impact:** Limited today (entity budgets are below 1e12 KES); the documented capacity cannot be met with the chosen field type. **Owner decision needed:** a decimal-string/Data column or a custom DECIMAL(27,9) for money.

### AUD-XC-130 — Typed stale-version / idempotency errors are unreachable under real concurrency; reference generators read stale data
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** TPR v0_17 TPR09-AC-007, TPR09-AC-025; AWD v0_5 §7 · **Module(s):** Planning, Requisitions, Tenders, Evaluation, Award, Opening, Proceedings, Needs · **Sources:** sweep-money F12; trace-award F16
**Evidence**
- Every module's lock helper is `select name … for update` then a separate plain `frappe.get_doc`: `procurement_planning/services/envelope.py:90-99`; `procurement_requisitions/services/envelope.py:88-98`; `tenders/services/envelope.py:84-91`; `bid_evaluation/services/records.py:83-90`; `award/services/records.py:109-113`; `bid_opening/services/records.py:77-84`; `proceedings/services/records.py:86-93`.
- A waiter whose snapshot predates the other commit passes `check_record_version` on stale data and is stopped only at `doc.save()` by Frappe `check_if_latest` (`frappe/model/document.py:1012-1038`, `TimestampMismatchError`), instead of `PLN_STALE_WRITE`, `REQ_STALE_VERSION`, `TND_STALE_VERSION`, `EVL_VERSION_CONFLICT`, `AWD_RECORD_CHANGED`.
- Reference generators take `get_lock` then compute `max+1` from a plain read: `procurement_planning/services/references.py:64-70`; `departmental_needs/services/lifecycle.py:345-354` (and REQ/Tenders equivalents); duplicate numbers are stopped only by unique indexes.
- Award replay: `award/services/records.py:137-141` reads the journal before taking the case lock; two same-key requests both pass, the second fails on the unique journal key or a version guard instead of returning the original result.
**Rule:** TPR09-AC-007 "Concurrent or repeated `StartTender` requests for one handoff produce one Tender and return its identity."; TPR09-AC-025 "a stale save never overwrites another user's change."; AWD §7 "A duplicate accepted command returns its original result".
**Reproduction / failing test sketch:** (static; not run) Two concurrent `StartTender` for one handoff: the second dies on `tender_reference` uniqueness or a timestamp mismatch, not "return its identity". Fails closed; no lost update found for commands that save their locked root.
**Impact:** Users see untyped failures and rolled-back commands instead of the documented typed refusals or original result.

### AUD-XC-131 — Idempotent replay is answered before authorisation and from a user-blind key lookup
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §9 (`NDS_IDEMPOTENCY_CONFLICT`); PLN v1.29 §8 (`PLN_IDEMPOTENCY_CONFLICT`, L1130); REQ v1.14 (`REQ_IDEMPOTENCY_CONFLICT`, L847); AGENTS.md §4.3 · **Module(s):** Needs, Planning, Requisitions, Tenders, Award, Evaluation · **Sources:** trace-needs C-23; trace-requisition F-14; trace-planning F-03; sweep-state F13
**Evidence**
- NDS: `departmental_needs/services/lifecycle.py:723` `if replay := _existing(idempotency_key, payload): return replay` precedes `principal = actor(user)` (:726) and every scope check; `_fingerprint` excludes `user` (:130-135); lookup is by key alone (`_existing`, :148-153).
- Planning: `procurement_planning/services/envelope.py:29-35` fingerprint excludes `user`; `:45-54` global key lookup; a mismatched payload raises `PLN_STALE_WRITE` (`:51-54`) although `PLN_IDEMPOTENCY_CONFLICT` is registered (`errors.py:91`) and never raised.
- Requisitions: `procurement_requisitions/services/envelope.py:33-58` same shape; `authorise.py` and the revoke/withdraw/request-correction commands share the `{requisition, reason}` payload shape with no command name in the fingerprint; replay precedes the role check (`authorise.py:84-88` for authorise, `:174-179` for revoke).
- Tenders/Award/Evaluation: journal rows are not unique on `idempotency_key` (`tender_command_journal.json` no `unique`) and `replay_or_none`/`command` look up before locking.
**Rule:** NDS §9 "same key with a different payload is `NDS_IDEMPOTENCY_CONFLICT`, never a silent replay"; PLN §8 `PLN_IDEMPOTENCY_CONFLICT`; AGENTS.md §4.3 "Return only data the caller is allowed to see."
**Reproduction / failing test sketch:** (static; not run) User A calls `authorise_requisition` with key K; unrelated user B repeats K with the identical payload and receives A's recorded result (reservation and handoff ids) with `idempotent: True`. Reuse K in Planning with a different payload: `PLN_STALE_WRITE`, not `PLN_IDEMPOTENCY_CONFLICT`.
**Impact:** Low (keys are client-generated UUIDs): a holder of another user's key and payload reads the recorded result; one documented error code is never produced.

### AUD-XC-132 — Reservation "required" amount is rounded half-up to the cent
**Severity:** Low · **Classification:** SPEC GAP · **Doc:** PLN v1.29 §5.5.3.1 · **Module(s):** Planning · **Sources:** sweep-money F13(a)
**Evidence**
- `procurement_planning/services/readiness.py:232` — `required = (eligible * Decimal(str(target_percent)) / Decimal(100)).quantize(cent, ROUND_HALF_UP)`; `:237` `remaining = max(Decimal(0), required - qualifying)`; `met` is `required is not None and remaining == 0` (`:307`).
- PLN §5.5.3.1 defines `required_planned_allocation = applicable percentage × eligible_current_app_value` with no rounding statement.
**Rule:** PLN §5.5.3.1 (quoted). The document is silent on cent rounding of the required amount; the code decides.
**Reproduction / failing test sketch:** (static; not run) Eligible 100.01, target 30%: exact 30.003, code 30.00. Qualifying 30.00 reports "met" at a true share of 29.997%.
**Impact:** Bounded below half a cent; the threshold is rounded in the entity's favour. **Owner decision needed:** round up, exact comparison, or accept half-up.

### AUD-XC-133 — Currency and precision are hard-coded in Planning and Budget reads
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §4.1 ("Currency precision comes from the Budget currency contract"); BUD v1.12 §4.8 CurrencyBasis · **Module(s):** Planning, Budget · **Sources:** trace-planning F-15
**Evidence**
- `procurement_planning/services/financial_basis.py:129` `precision = 2`; `:136,140` `"KES"`; `plan_json.py:67,84,153` `"currency": "KES"`; `plan_requisition.py:325` `"currency": "KES"`.
- `kentender_budget/.../budget_line_contracts.py:555` `CURRENCY_PRECISION = 2  # KES; BUD-CHG-001's currency contract carries the precision`; `:560` `money()` returns `round(flt(value), 2)` (silent rounding).
- `grep -rn "CurrencyBasis\|get_budget_currency_contract" kentender_budget --include=*.py` finds nothing.
**Rule:** BUD §4.8 "Missing or unsupported precision blocks monetary writes and positive decisions; it is not defaulted." PLN §4.1 as quoted.
**Reproduction / failing test sketch:** (static; not run) Static grep above; no test exercises a missing or non-KES currency basis.
**Impact:** Single-currency fixture works; any other currency or precision would be defaulted silently. (The Budget contract itself is covered by the str-bud part.)

### AUD-XC-134 — Planner segregation chain omits `SavePlanVersionDetails` and other Planner commands
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §6.4 row 2 · **Module(s):** Planning · **Sources:** sweep-sod F12
**Evidence**
- `procurement_planning/services/planning_authorization.py:68-78` — `PLANNER_CHAIN_COMMANDS` lists nine commands (`FormPlanItems`, `DissolvePlanItem`, `SavePlanItem`, `ConfirmSplittingAdvisory`, `RequestPlanFundingConfirmation`, `SubmitConsolidatedPlan`, `SubmitCorrectedPlan`, `RemovePlanItemInSuccessor`, `BeginPlanUpdate`); `prior_actors` (:357-406) reads the journal only for those.
- `plan_workbench.py:534-571` — `save_plan_version_details` (Planner edits `project_name` and the successor's `change_reason` on the Draft) is journalled as `"SavePlanVersionDetails"` (:568) and is not in the list; likewise `CancelPlanUpdate` (`plan_publication.py:205`).
**Rule:** PLN §6.4 "Author Annual Plan content, form/dissolve items, request Finance, or sign formal submission | … Confirm/return Finance; adopt/return as AO; approve/return as statutory authority".
**Reproduction / failing test sketch:** (static; not run) Planner P (also Finance Confirmation Officer) only calls `save_plan_version_details`; another Planner submits; P `confirm_plan_funding`: `is_segregated(P, finance_decide)` is False.
**Impact:** Low (two descriptive fields): an author of plan content can later confirm Finance.

### AUD-XC-135 — "Independent of direct processing" for the opening committee covers only Tender Version actors and the publishing AO
**Severity:** Low · **Classification:** SPEC GAP · **Doc:** BOP v0_11 §AppointOpeningCommittee (L158), BOP-A02 · **Module(s):** Bid Opening, Tenders · **Sources:** sweep-sod F13
**Evidence**
- `tenders/services/opening_seam.py:91-98` — `processing_actors` = `prepared_by`, `submitted_by`, `approved_by` of Tender Versions plus `Tender Publication.authorised_by`.
- `bid_opening/services/appointment.py:81-93` compares the independent member only to that set.
**Rule:** BOP L158 "AO names at least three members and one demonstrably independent of direct processing/evaluation". "Direct processing" is not defined, so Tender Draft editors, Requisition certifiers/authorisers, Planning chain actors and addendum drafters are not excluded. **Owner decision needed:** define "direct processing".
**Reproduction / failing test sketch:** (static; not run) Appoint a user who authorised the Requisition as the independent opening member: accepted.
**Impact:** Independence is interpreted narrowly; no code defect against a stated rule. (Order-dependent exclusion from Evaluation is owned by the evl-awd part.)

### AUD-XC-136 — Nothing stops an assignment administrator granting business roles to themselves or Administrator; registry `sod_tags` unused
**Severity:** Low · **Classification:** SPEC GAP · **Doc:** AUTH-ADR-001 v1.11 §4.4 (`sod_tags`), §8 · **Module(s):** Core · **Sources:** sweep-sod F14
**Evidence**
- `kentender_core/.../business_role_registry.py:29,67` declare `sod_tags` ("consumed by domain segregation checks"); `roles_with_sod_tag` (:275-276) and `.sod_tags` have no non-test caller (`grep -rn "roles_with_sod_tag\|\.sod_tags" kentender_*`).
- `responsibility_administration.py:84-111` `grant` has no `principal == user` guard; `_require_enabled_user` (:382-388) admits any enabled System User, including Administrator/System Manager.
**Rule:** AUTH §4.4 L173 `sod_tags` "Stable categories consumed by domain segregation checks"; §8 "Seeds, fixtures and test profiles shall not grant business roles to Administrator …" and "Setup authority is not business authority. To … approve … the person must hold the same Active assignment and pass the same state and segregation checks as any other user." The document does not forbid a setup administrator granting themselves an assignment. **Owner decision needed:** forbid self-grant and technical-user grants, or accept them.
**Reproduction / failing test sketch:** (static; not run) As System Manager `grant_responsibility(user=<self>, business_role="Accounting Officer")` then act on a Tender whose chain does not include that user.
**Impact:** Role stacking by the administrator is possible; every downstream check then applies normally.

### AUD-XC-137 — Open segregation questions in approved documents (Finance vs Budget Officer, BDS signatory, Contract)
**Severity:** Low · **Classification:** SPEC GAP · **Doc:** BUD v1.12 BUD21-XD-002 (L1673); BDS v0_11 BDS01-IMP-008 (L2349) · **Module(s):** Budget, Planning, Bid Submission, Contract · **Sources:** sweep-sod F16
**Evidence**
- BUD21-XD-002: "should a Finance Confirmation Officer be barred from confirming funding for a plan whose Budget Line they revised as Budget Officer? … Open. v1.11 adds no such rule." No code enforces any such rule.
- BDS01-IMP-008: "Require separate users for preparation and final signature where the approved segregation policy requires it"; no policy is stated; `bid_authorization.py:22` makes SIGNATORY a preparer.
- Contract (chain end): `kentender_procurement/contract_management/{doctype,services,api}` contain only `__init__.py`/`.gitkeep`; no approved document exists.
**Rule:** Open spec questions; no code defect asserted. **Owner decisions needed:** (1) Finance Confirmation Officer vs Budget Officer on the same line; (2) the BDS segregation policy; (3) a Contract Management document.
**Reproduction / failing test sketch:** (static; not run) The shared fixture gives one user both Budget Officer and Finance Confirmation Officer; they revise a line and confirm funding for a plan using it: allowed (matches the open question).
**Impact:** None until the owner rules; listed so the open items are not mistaken for conformance.

### AUD-XC-138 — A patch records success although its unique indexes may not exist
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** AGENTS.md §4.5 · **Module(s):** Bidder Workspace (legacy) · **Sources:** sweep-hazards F-12
**Evidence**
- `kentender_procurement/patches/ensure_bwmf_persistence_indexes.py:88-92` `_add_unique`: `try: alter table … add unique index … except Exception: frappe.log_error(title=f"BWMF unique index {index_name}")`; `:54-62` `except Exception: pass` around `drop column`. `patches.txt:65` lists it.
- Four unique indexes (`uniq_bwmf_manifest_id_version`, `uniq_bwmf_response_id_version`, `uniq_bwmf_evidence_item_version`, `uniq_bwmf_idempotency_org_op_key`) are integrity guarantees.
**Rule:** AGENTS.md §4.5 patches must be idempotent and (§4.4) explicit about outcomes; a swallowed DDL failure plus a Patch Log "done" never retries.
**Reproduction / failing test sketch:** (static; not run) Duplicate rows for `(manifest_id, version)` before the patch: CREATE fails, error is logged, patch completes, the index never exists.
**Impact:** Legacy module only; integrity constraints can be silently absent.

### AUD-XC-139 — Patches that rewrite data by heuristic
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** AGENTS.md §4.5 · **Module(s):** Core, Budget · **Sources:** sweep-hazards F-17 (verified subset)
**Evidence**
- `kentender_core/patches/backfill_master_display_titles.py:10` `_HASH_LIKE = re.compile(r"^[A-Za-z0-9]{8,}$")`; `:36-45` any Procuring Department whose name matches (any single-word name of 8+ alphanumerics, e.g. "Treasury", "Education") is renamed `"<entity> Department 001"` via `frappe.db.set_value`. Listed `kentender_core/patches.txt:8`.
- `kentender_budget/patches/bud_chg_001_v1_3_phase4_drop_pe_rename_fy.py:67-71` — when the legacy `Financial Year` doctype is absent, `update tabProcurement Budget set fiscal_year = NULL where fiscal_year is not null` clears every Budget's fiscal year, including valid ERPNext Fiscal Year names.
**Rule:** AGENTS.md §4.5 "Retriable … patches … must be idempotent."; §4.4 "Do not use direct database writes to bypass validation".
**Reproduction / failing test sketch:** (static; not run) A Procuring Department named "Treasury" on a site lacking the first patch is renamed; a site with Budgets referencing valid Fiscal Years but no `Financial Year` doctype loses `fiscal_year` on every Budget when the second patch first runs.
**Impact:** Low; one-shot, already logged on the dev site. (Dropped from the source finding: the supplier sign-up patch is a documented owner/BDS-plan decision, not a defect.)

### AUD-XC-140 — `**kwargs` Needs endpoints and journey/search endpoints turn unknown or malformed input into HTTP 500
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** AGENTS.md §4.3 ("predictable failure behaviour") · **Module(s):** Departmental Needs, Procurement Journey, Core · **Sources:** sweep-hazards F-14, F-15
**Evidence**
- `departmental_needs/api.py:76-89` `save_need_draft(**kwargs)` → `lifecycle.create_need(**args)`; `_command_args` (:73-74) strips only `cmd`, `csrf_token`, `_`; `create_need` has a keyword-only signature (`lifecycle.py:511-524`). An unknown field raises `TypeError: create_need() got an unexpected keyword argument` → 500; same for `return_need_revision`/`accept_need_revision`/`decline_need_revision` (:113-127).
- `procurement_lifecycle/api/journey_api.py:125` `limit_val = min(int(limit or 100), 500)` (non-numeric → `ValueError`; `-1` passes to `LIMIT %s` → SQL error); `core/api/responsibility_api.py:200` `limit_page_length=int(limit or 20)` (no upper bound); `core/api/technical_search.py:19` `int(limit or 25)`.
**Rule:** AGENTS.md §4.3 "predictable failure behaviour"; "do not expose internal exceptions".
**Reproduction / failing test sketch:** (static; not run) `POST …save_need_draft` with `organisation_unit=…&financial_year=…&title=…&foo=1` → HTTP 500; `GET …journey_api.list_journeys?limit=abc` → 500. Assert a typed validation error.
**Impact:** Low: malformed input yields a 500 rather than a typed refusal. (Identity forwarding through the same `**kwargs` path is cluster 1 of the xc-authz part.)

### AUD-XC-141 — Departmental-plan autostart failure is swallowed and never retried
**Severity:** Low · **Classification:** SPEC GAP · **Doc:** NDS v1.16 L75 (owner decision "Visible", 26 Sep 2026) · **Module(s):** Planning, Needs · **Sources:** sweep-hazards F-13
**Evidence**
- `procurement_planning/services/dpp_autostart.py:66-89` — `ensure_departmental_plan` and `needs_intake.publish_need_positions` run in one savepoint; `except Exception: frappe.db.rollback(save_point=SAVEPOINT); frappe.log_error(...)`; the failure is dropped. `kentender_procurement/hooks.py:481-508` registers no job that re-runs it; later plan commands call `publish_need_positions` (`dpp_validation.py:140,227`, `dpp_lifecycle.py:235,666,704,734`) and one-off patches backfill (`patches/pln_nds_late_need_positions.py:29`).
**Rule:** NDS L75 "Procurement Planning pushes where each accepted Need stands against its department's plan into a new read-only projection … The Need's page shows it". The document says nothing about recovery when the reaction fails. **Owner decision needed:** retry or compensating job.
**Reproduction / failing test sketch:** (static; not run) Make `ensure_departmental_plan` raise once when a Need is accepted (lock timeout): the Need is Accepted, no plan opened, no `Need Planning Intake Projection` written; the Need page shows no position until an unrelated plan command republishes.
**Impact:** A transient failure re-creates the "late-accepted Need with no visible position" state the owner decision removed.

### AUD-XC-142 — Scheduler sweeps without per-item isolation
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** AGENTS.md §4.4 ("Jobs must be idempotent, scoped, observable, safe to retry, and explicit about transaction boundaries") · **Module(s):** Bid Opening, Bid Submission, Core · **Sources:** sweep-hazards F-11 (verified subset)
**Evidence**
- `bid_opening/services/sweep.py:34-43` `run()`: `try: sweep_tender(tender) … except Exception: frappe.log_error(...)` with no `rollback()`; the job then commits whatever the failed tender wrote when a later tender succeeds (`ScheduledJobType.execute` runs the method then commits, `frappe/core/doctype/scheduled_job_type/scheduled_job_type.py:156-157`). Sibling sweeps roll back: `bid_evaluation/services/sweep.py:54-56`, `award/services/sweep.py`.
- `bid_submission/services/handoffs.py:231-241` `sweep()` loops `sync(name)` for every open bid then `sync_incidents()` in one transaction with no per-item try/except; `bid_submission/services/submission.py:285` `box.status(...)` is outside any try.
- `kentender_core/.../reference_data_transitions.py:503-519` `close_due_contexts`: `ctx.save()` per context in a loop, no isolation (cron every 5 minutes, `kentender_core/hooks.py:263-270`).
**Rule:** AGENTS.md §4.4 as quoted.
**Reproduction / failing test sketch:** (static; not run) No failing input is demonstrated: if one context's `save()` raises, `ScheduledJobType.execute` rolls back the whole job each tick, so later contexts are never closed until it is fixed.
**Impact:** Low, conditional on a persistently failing item. (Dropped from the source finding: candidate-notice dispatch, whose default transport records its own failure at `candidate_notices.py:64-65`, and Budget outcome re-delivery ordering.)

### AUD-XC-143 — Legacy Tender Configuration services commit mid-request and a "get" writes and commits
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** AGENTS.md §4.4 ("Do not call `frappe.db.commit()` from ordinary request services.") · **Module(s):** Tender Configurations (legacy), Tenders · **Sources:** sweep-hazards F-9; trace-tenders F-19
**Evidence**
- 26 `frappe.db.commit()` calls under `kentender_procurement/tender_configurations/services/` (e.g. `review_workspace.py:257,398,434,484,554,604`; `readiness.py:379,432`; `document_preview.py:705,782,851,965`; `publication_setup.py:549,638,713`); `modules.txt:3` still lists the module.
- `tender_configurations/api.py:342-349` `get_tender_configuration_review` (`@frappe.whitelist()`, GET allowed) → `review_workspace.py:379-398` `get_review_workspace`: `_ensure_review_started` sets `status = Under Review` and `frappe.db.set_value(..., update_modified=False)` then `frappe.db.commit()`. The function docstring (:349-354) says this promotion on first access is intended.
- Tenders: `tenders/api.py:202-204` `get_tender_cancellation` → `open_period_read.py:222-226` `cancellation.refresh_obligation_statuses(doc)` → `envelope.bump` (`cancellation.py:220-229`); on a GET the write is rolled back, on a POST (the default `frappe.call` method) it persists and moves `record_version`. TPR §11.1 "Reads create no record, task, decision, render, confirmation or event" does not name status refreshes, so this bullet is an observation.
**Rule:** AGENTS.md §4.4 as quoted; "Do not use direct database writes to bypass validation or manufacture workflow state."
**Reproduction / failing test sketch:** (static; not run) As a user with write on a Tender Configuration in "Ready for Review", `GET /api/method/kentender_procurement.tender_configurations.api.get_tender_configuration_review?configuration_id=X`: status becomes "Under Review" and is committed with no event.
**Impact:** Low: legacy module, state changes on a read and partial commits defeat rollback of a later failure.

## Dropped / downgraded

- sweep-money F9 (part) — "convert_reservation(amount=100.00005) accepted with remaining −0.00005": dropped. `doc.save()` on `Funding Reservation` fails the `non_negative` validation (`funding_reservation.json:148`, `frappe/model/document.py:816-833`) so the over-conversion is refused untyped; kept only the NaN/scale/tolerance parts (AUD-XC-117).
- sweep-money F13(b) (display rounding `reserved_share_percent` / "Reserved share 30%") and F13(c) (Evaluation `ROUND_HALF_EVEN` recompute vs producer `ROUND_HALF_UP`): dropped. (b) is display-only; (c) needs a fractional-quantity bid line, and REQ items are whole numbers (`requisition_item.json` Int) and bid inputs have scale 2 (`bid_submission/services/controls.py:92-98`), so it is unreachable today.
- sweep-audit F11 (Need Planning Intake Projection, every role cwd), F7, F1 (System Manager/Administrator write/delete on immutable records): not written here; owned by the xc-authz part (cluster 4/5).
- sweep-audit F15 (legacy Tender Configuration JSON blob decisions): dropped; no governing approved document and the module is frozen legacy.
- sweep-audit F16(2) (`check_funding` writes `EVENT_CHECK_PERFORMED`): owned by the str-bud part (trace-budget F-12). F16(3)(4)(5): not written; (3) `Budget Audit Event.on_trash` flag bypass and (4) TM2 `in_test` early return are guard-quality notes with no reachable production bypass found, (5) the author found no unsafe case ("unproven").
- sweep-hazards F-11 candidate-notice head-of-line blocking and budget outcome re-delivery ordering: dropped; the default transport returns `Failed` rather than raising (`candidate_notices.py:64-65`), and Budget outcomes are terminal per request so a skipped lower sequence is not shown to matter.
- sweep-hazards F-16 (`_get_freshness` fails open), F-18 (latent hazards: `business_id_service.generate_business_id` with no production caller, unused TM2 planning handoff code, unexported `fixtures`, sidebar re-insert), F-19 (worker/scheduler reliance): dropped; no governing document rule, no live caller or already a known project gotcha. F-17 supplier sign-up patch: dropped as a documented decision (kept the two verified data-rewrite items in AUD-XC-139).
- trace-requisition F-11 and F-20: folded into AUD-XC-115/129/118 as evidence (Low arithmetic and capacity), not separate findings; trace-planning F-15 became AUD-XC-133.
- trace-tenders F-19: downgraded to a note inside AUD-XC-143 (the write is rolled back on a GET; the documented rule does not name status refreshes).
- sweep-sod F11 and sweep-hazards F-2 (TM2 publication `actor`): owned by xc-authz cluster 2; not written here.
- sweep-state F13 (replay before lock) and trace-award F16: merged into AUD-XC-130/131 rather than separate findings. trace-requisition F-03 Budget half merged into AUD-XC-101.
- sweep-audit F2 (Needs/Planning/Budget/Strategy REST direct write): owned by xc-authz cluster 4.

## Calibration notes

- **Dropped-doctype crash class — still present.** Post-sync patches `pln_revision_schema_backfill.py:20-70`, `pln_chg_016_schema_cleanup.py:10-12`, `scope_pln_formation_batch_key.py:13-16` act on tables that `pln_chg_001_v12_drop_legacy_planning_doctypes.py:18-50` (pre_model_sync, `patches.txt:23`) drops; runtime TM2 code still calls `frappe.db.exists("Procurement Package"/"Procurement Plan", …)` at `tender_management/services/export_tender_evidence.py:251,261` (AUD-XC-126). Observation not verified live: `tm2_tender.json:135-139` declares a required Link to `Procurement Plan`, a doctype no app ships; whether Frappe tolerates that on sync/save needs a run on the test site. The newer patches (`backfill_pe_fy_context_links.py`, `pln_revision_preflight.py`, `pln_nds_late_need_positions.py`) use the correct `table_exists` guard.
- **Editor post-save reload race / optimistic-lock stamp.** Client side: absent (fixed) in the Budget editor — `BudgetVersionEditorScreen.vue:345-349` awaits one reload inside the runner (`loadDraft({quiet:true, lines: tab !== "lines"})`) and sends `expected_modified` on save and submit (:303, :327, :379). Server side: Budget stamp is optional and a lines save never moves it (AUD-XC-119). Planning, Requisitions, Tenders, Evaluation, Award, Opening and Proceedings refuse an empty stamp (`procurement_planning/services/envelope.py:102-106`, `procurement_requisitions/services/envelope.py:100-102`, `tenders/services/envelope.py:94-96`, `bid_evaluation/services/records.py:93-99`, `award/services/records.py:116-122`). The Needs editor client was not examined.
- **Reservation-denominator arithmetic (money side) — fixed, exact.** `procurement_planning/services/readiness.py:211-246` (`reservation_measure`) and `:249-310` (`reservation_allocations`) use the eligible value of the exact Plan Version (`Annual Plan Item` rows of `version_name`, `item_state != "Dissolved"`) in `Decimal` (`money.sum_money`, `money.py:97-103`), with the Budget ceiling explicitly absent (docstring :253-262); `plan_read.py`, `plan_governance.py:185` and `workspace.py` call it. Fixture arithmetic matches RES-IMP-001: 130m × 30% = 39m, 50m/130m = 38.46%. Residual: AUD-XC-132 (half-up cent rounding of `required`, a SPEC GAP) and the float affordability tests of AUD-XC-115 (a different measure: ceiling, not denominator).
