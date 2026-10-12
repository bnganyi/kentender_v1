# KenTender conformance audit — FINDINGS

Date: 6 October 2026 · Branch: mvp1/dev · Mode: read-only static audit (no code modified, no tests run, no seed/migrate; the only live query was a read-only `SELECT @@tx_isolation` on the dev site).

## 1. Scope, oracle and method

- **Oracle:** the latest version of each module document under `docs/mvp-1-r1/`. All eight were checked and read **Approved — 3 October 2026**: Strategy STR-CHG-001 v1.9, Budget BUD-CHG-001 v1.12, Needs NDS-CHG-001 v1.16, Planning PLN-CHG-001 v1.29, Requisition REQ-CHG-001 v1.14, Tenders TPR-CHG-001 v0.17, Evaluation EVL-CHG-001 v0.5, Award AWD-CHG-001 v0.5. Because none is merely Proposed, no finding is labelled "divergence from proposed spec" except where the approved document itself gates a rule as owner-gated/blocked (the post-close Tender cancellation, TPR14); those are noted in the finding or in the trace file and are not counted as defects.
- **Phase 1** (8 module traces, 2,359 rows) → `audit/trace-<module>.md`. **Phase 2** (7 cross-cutting sweeps) → `audit/sweep-<name>.md`. **Phase 3** consolidated ~190 candidate findings into the findings below, one per root cause; each was re-opened at its cited file:line by a writer, and every Critical and High finding was then attacked by an independent verifier agent (`audit/_verify-A/B/C.md`). Verifiers confirmed 36, corrected 5 (severity/citation/reproduction) and refuted none.
- **Evidence standard:** every finding cites file:line read in this audit, the rule it breaks, and a reproduction or failing-test sketch. **All reproductions are static and unrun** — they are sequences for the test site (`kentender-test.local`), not observed failures. Where a claim rests on Frappe/InnoDB behaviour rather than code alone, the finding says so.
- **Confirmed live:** MariaDB 10.6.23, `tx_isolation = REPEATABLE-READ` (global and session). This removes the caveat the concurrency findings (AUD-XC-101…104) carried.
- **Not covered:** per-command bodies of Bid Submission / Bid Opening / Proceedings (only shared envelopes and the Evaluation/Award seams were read); TM2 doctypes per-doctype; whether this particular site holds TM2 Tender rows (AUD-XC-003 is conditional on it); rendered UI.
- **Not findings:** missing tests alone, style, naming, refactoring. Untested-but-implemented rules are listed in the trace files (status `Untested`).

## 2. Summary

**237 findings: Critical 3 · High 36 · Medium 114 · Low 84.** Classification: CODE DEFECT 186 · SPEC DEFECT 19 · SPEC GAP 32. (1 further entries are retained as duplicates/withdrawn and excluded from counts.)

| Area | Critical | High | Medium | Low | Total |
|---|---|---|---|---|---|
| Cross-cutting (authorization, state/immutability, audit, concurrency, money, Frappe hazards) | 3 | 15 | 33 | 21 | 72 |
| Hand-off contracts | 0 | 2 | 7 | 2 | 11 |
| Strategy | 0 | 4 | 7 | 10 | 21 |
| Budget | 0 | 2 | 10 | 5 | 17 |
| Needs | 0 | 1 | 9 | 8 | 18 |
| Planning | 0 | 3 | 9 | 10 | 22 |
| Requisition | 0 | 2 | 8 | 6 | 16 |
| Tenders | 0 | 2 | 8 | 9 | 19 |
| Evaluation | 0 | 3 | 14 | 6 | 23 |
| Award | 0 | 2 | 9 | 7 | 18 |
| **Total** | **3** | **36** | **114** | **84** | **237** |

### Phase 1 trace coverage (rows by status)

| Module | Rows | Implemented | Partial | Missing | Contradicts | Untested |
|---|---|---|---|---|---|---|
| Strategy | 230 | 117 | 89 | 5 | 7 | 12 |
| Budget | 402 | 190 | 108 | 22 | 38 | 44 |
| Needs | 247 | 145 | 55 | 20 | 19 | 8 |
| Planning | 395 | 264 | 87 | 10 | 17 | 17 |
| Requisition | 293 | 186 | 71 | 5 | 5 | 26 |
| Tenders | 333 | 238 | 61 | 9 | 4 | 21 |
| Evaluation | 229 | 142 | 58 | 4 | 3 | 22 |
| Award | 230 | 137 | 79 | 6 | 1 | 7 |
| **Total** | **2,359** | **1,419** | **608** | **81** | **94** | **157** |

Row-level status counts are the trace agents' own and are not re-verified; the findings below are.

### Top 10 findings

| # | ID | Severity | Why it matters |
|---|---|---|---|
| 1 | AUD-XC-001 | Critical | Every Departmental Needs endpoint takes `user=` from the request. Any signed-in account can accept, submit or read as another user (e.g. a Head of Department), defeating maker-checker (NDS-BR-006). Four independent sweeps found it. |
| 2 | AUD-XC-002 | Critical | `release_reservation`, `convert_reservation`, `adjust_commitment`, `revalidate_reservations` are whitelisted and refuse only Guest; any account can release or alter funding. `idempotency_key` is a label, not a dedupe key. |
| 3 | AUD-XC-003 | Critical (conditional) | Tender Management v2 `pub_api_*` trusts a client `actor`; `actor="Administrator"` skips all role checks, so any user can approve/publish a TM2 tender — if TM2 data exists on the site. |
| 4 | AUD-XC-005 · 006 · 007 · 008 | High | Strategy, Budget, Planning and Needs role-holders can write status/approved-amount/lifecycle fields straight through REST; controllers have no transition guard, so approval chains, snapshots and segregation rules are bypassable. |
| 5 | AUD-XC-101 · 102 · 103 · 104 | High | Budget reserve / adjust / approve / close / Finance decision lock rows but then read availability from the pre-lock snapshot (REPEATABLE READ, confirmed), so concurrent requests can oversubscribe a Budget Line (two 80m reservations on a 100m line). |
| 6 | AUD-XC-105 · AUD-EVL-001 · AUD-AWD-001 | High | Segregation of duties: Budget no-self-approval reads the first-ever submission event (a resubmitter can approve their own); an evaluator can clear their own declared conflict; nothing stops one person being evaluator, opinion-giver and Award decider. |
| 7 | AUD-AWD-002 | High | Award never re-reads Budget; it trusts the Evaluation report’s frozen funding block, and an unavailable funding or validity read is treated as "no restriction", permitting a positive award. |
| 8 | AUD-XC-004 | High | Supplier-registry state changes (`ktsm_suspend`, `ktsm_reinstate`, `ktsm_set_expired`, category qualify/reject) have no role gate and write with `ignore_permissions`. Not in any earlier phase file; found during the writer pass. |
| 9 | AUD-XC-106 | High | An approved Annual Plan is never dispatched for publication (no enqueue, no scheduler); it never becomes Active, so Requisition drawdown stalls until someone calls the technical API by hand. |
| 10 | AUD-NDS-001 | High | Late-accepted-Need dead end re-opened for successor revisions: a Need accepted as a successor drops out of Planning’s source list, Planning deletes its Draft plan entry and never publishes "Update required". (Calibration regression — see §3.) |

Honourable mentions: AUD-STR-001 (a Strategy Author can delete any record of any DocType via the structure change set), AUD-XC-009 (any logged-in user reads any module’s audit trail), AUD-XC-010 (Audit Event is mutable and deletable by System Manager and is the source of truth for Strategy’s own SoD check). Verifier note: AUD-XC-004, -009 and -011 are rated High on the writer’s reasoning (no in-repo consumer / legacy module); under the literal severity scale they could be argued to Critical — owner’s call.

## 3. Calibration — known gaps fixed before

Each previously fixed gap was re-checked in current code. "Present" = the fix exists and was read at the cited line.

| Known gap | State now | Evidence / residue |
|---|---|---|
| Whitelisted `**kwargs` receives `cmd`/`csrf_token`/`_` → 500 | **Fixed**, no other `**kwargs` endpoint repo-wide (AST scan) | `departmental_needs/api.py:63-74`. Residue: the same passthrough forwards `user` (AUD-XC-001) and unknown fields still 500 (AUD-XC-140). |
| Intake scope bug (out-of-scope FY/department offered; `NDS_SCOPE_DENIED` on save) | **Fixed** at service layer | `departmental_needs/services/context.py:140-193`, `permissions.py:276-287`. Same class persists one layer down at DocType/REST level (AUD-XC-015) and via request-supplied `user` (AUD-XC-001). |
| Requisition Handoff v1.4 renamed fields not read by Tenders | **Fixed**, weakly pinned | `tenders/services/snapshot.py:38-61` `_handoff_v14_names`; test pins only a hand-written payload (`test_snapshot_contract.py:42-82`), no end-to-end "Youth + 36-month warranty reaches a published Tender" test. Approved docs still say v1.3 (AUD-HND-009). |
| Reservation (AGPO) denominator was the budget | **Fixed** | `procurement_planning/services/readiness.py:249-321` (eligible value of exact Plan Version, Decimal); `get_annual_procurement_budget_basis` gone with no alias. Residue: an absent rule reports success (AUD-PLN-004). |
| Open Tender 21-day default enforced as legal floor (7-day minimum) | **Present and working**; HOPF-approval re-detection and the patch are untested | `tenders/services/review.py:125-150`, `publication.py:78-82,156-159`; patch `core/patches/v1_28/open_tender_preparation_minimum.py:24-35`. |
| Late-accepted Need dead end | **Fixed for first acceptance; NOT fixed for successor revisions** | AUD-NDS-001, AUD-PLN-015. |
| Adding a catalogue control changes every package digest | **Still present** for approved/unauthorised Versions; published Tenders unaffected | AUD-TND-007 (only `shortened_period_reason` is exempt, `controls.py:41`). |
| Editor post-save reload race / optimistic-lock stamp | **Client partly fixed; server stamp still optional** | AUD-BUD-007, AUD-XC-119. |
| Dropped doctype/table crashes sibling `db.exists` | **Still present** | AUD-XC-126 (patches on dropped tables; whitelisted TM2 export), AUD-XC-125 (patch deletes DocType records the app still ships). |
| Strategy approved plans readable by all internal users; drafts restricted; portal excluded | **Present in Vue read APIs; absent at the five consumer endpoints and DocType level** | `strategy_authorization.py:252-267` vs `strategy_consumer_api.py:39-94` (AUD-STR-005). |
| Departmental correction route (Planner cannot change cost) | **Present at service layer only** | Holds only while Desk/REST writes on Plan Source Allocation are open (AUD-XC-007). |

## 4. Findings

Ordered by severity, then cross-cutting → hand-off → module (chain order). Every finding’s **Verification** line, where present, records the independent re-check.


## 4.1 Critical

### AUD-XC-001 — Every Departmental Needs endpoint takes the acting user from the request (`user=`); any signed-in account acts as anyone
**Severity:** Critical · **Classification:** CODE DEFECT · **Doc:** NDS v1_16 NDS-BR-006 (line 425) and AUTH-ADR-001 v1_11 §5.5 (line 295) and §15 (line 829) · **Module(s):** Departmental Needs (consumed by Planning) · **Sources:** sweep-sod F1; sweep-state F1; sweep-hazards F-1; trace-needs C-01
**Evidence**
- `kentender_procurement/kentender_procurement/departmental_needs/services/permissions.py:59-60` — `def actor(user: str | None = None) -> str:` / `value = cstr(user or frappe.session.user).strip()`; the supplied value wins and is never compared with the session.
- `kentender_procurement/kentender_procurement/departmental_needs/services/lifecycle.py:725` — `principal = actor(user)` in `review_need` (declared `user: str | None = None` at :712); then `:732 if is_owner(doc, principal)`. The same line pattern is at lifecycle.py:535, 602, 652, 838, 882, 934, 1014, 1092; workspace.py:234, 380, 481, 535, 644; context.py:147, 179; usage.py:136, 176, 414, 452.
- `kentender_procurement/kentender_procurement/departmental_needs/api.py:45-54,92-103` — services exposed directly by `frappe.whitelist()(fn)` aliases (`get_departmental_need`, `get_departmental_review_task`, `resolve_needs_scope`, `submit_need_revision`, `decide_accepted_need_withdrawal`, `project_need_planning_*`); `:112-127` `accept_need_revision(**kwargs)` forwards `_command_args(kwargs)`, which strips only `cmd`, `csrf_token`, `_` (api.py:70-74).
- `kentender_procurement/kentender_procurement/departmental_needs/services/workspace.py:133` — `"decision_token": task["decision_token"]` is returned inside the review action whenever the (spoofable) principal is a department reader who is not the owner, so the token needed by the decision call is handed over by the read call.
- AST scan of all decorated whitelisted functions (this review) finds a request-controllable acting-user parameter only here (and the TM2 `actor` parameters, AUD-XC-003). `responsibility_api.py` `user` parameters name the grantee, not the actor.
- Internal Planning callers rely on the same parameter: `kentender_procurement/kentender_procurement/procurement_planning/services/needs_intake.py:85,102,342`, `dpp_validation.py:260`, `plan_publication.py:49,60` pass `user="Administrator"`.
**Rule:** AUTH §5.5 "The client never supplies an assignment ID, effective role, permitted scope or available action as authority"; AUTH §15 "Timestamps and actors are system-generated. A client cannot supply or amend them."; NDS-BR-006 "Maker-checker is rechecked on the server"; AGENTS.md §4.3 (re-check permissions inside whitelisted methods).
**Reproduction / failing test sketch:** static; not run. (1) Seed a Need N submitted by Departmental Author A in OU U with an open review task; H = a Head of User Department of U who is not A. (2) Signed in as A (or any Website User): `GET /api/method/kentender_procurement.departmental_needs.api.get_departmental_need?need=N&user=H` and read `actions[0].task` and `.decision_token`. (3) `POST /api/method/kentender_procurement.departmental_needs.api.accept_need_revision` with `need=N&task=<task>&decision_token=<token>&expected_version=<record_version>&idempotency_key=k1&user=H`. Expected: `NDS_SCOPE_DENIED`/`NDS_MAKER_CHECKER`; read result: Need becomes `Accepted for planning` with H recorded as decider. Pytest: `frappe.set_user(A); api.accept_need_revision(need=N, task=t, decision_token=tok, expected_version=v, idempotency_key="k", user=H)` must raise. Also `save_need_draft?user=<other author>` and `project_need_planning_usage?user=<Planner>`.
**Impact:** Any authenticated account, including a supplier Website User, can create, submit, accept, decline or withdraw Needs as any other user and read any user's scoped workspace; the decision and its audit row carry the forged principal, so NDS maker-checker, role and OU scope all fail. A fix must keep an internal non-HTTP seam, because Planning calls these services with `user="Administrator"`.
**Verification:** CONFIRMED — Re-opened permissions.py:59-60, lifecycle.py:725 (and the other 20 `actor(user)` sites), api.py:45-127 and workspace.py:133; frappe handler.py:86 delivers request fields by signature and no before_request/auth hook strips `user`, so the supplied principal wins end to end.

### AUD-XC-002 — Budget release / convert / adjust / revalidate endpoints are open to every non-Guest account; `idempotency_key` is only a label
**Severity:** Critical · **Classification:** CODE DEFECT (with a SPEC GAP: BUD names a "service account" but gives no mechanism that identifies one) · **Doc:** BUD v1_12 §7 (line 358), BUD-BR-015 (line 297), error `BUDGET_DOWNSTREAM_FORBIDDEN` (line 1224), BUD18-AC-032 (line 1401) · **Module(s):** Budget (callers: Requisitions, Planning, future Contract Management) · **Sources:** sweep-authz F-02; sweep-money F5; trace-budget F-01, F-10; trace-planning F-31 (whitelist exposure only, see Dropped)
**Evidence**
- `kentender_budget/kentender_budget/services/budget_commitment_contracts.py:24-31` — `_require_service_capability()` throws only `if not frappe.session.user or frappe.session.user == "Guest"`; its docstring says "any authenticated user acting for a downstream module, may call these". Called at :75 (`revalidate_reservations`), :128 (`release_reservation`), :174 (`convert_reservation`), :257 (`adjust_commitment`).
- `kentender_budget/kentender_budget/api/budget_api.py:266-267,285-286,304-305,321-322` — the four functions are `@frappe.whitelist()`; `kentender_budget/kentender_budget/api/dia_budget_control.py:25-26` whitelists a second `release_reservation(reservation_id, reason)` that releases the full hold with a caller-chosen reason (`:33-39`).
- Writes use `doc.save(ignore_permissions=True)` (budget_commitment_contracts.py:144, 225, 288) and `com.insert(ignore_permissions=True)` for the new Procurement Commitment (:221, in `convert_reservation`).
- `budget_commitment_contracts.py:137` — `release_amount = min(release_amount, flt(doc.remaining_amount))`; `idempotency_key` is used only as `correlation_id=idempotency_key` (:154, :236, :299). No replay lookup exists in `release_reservation` or `adjust_commitment`; `convert_reservation` dedupes only on `(contract, reservation)` (:183) so a second call with a different `amount` returns the first commitment.
- No in-repo caller needs the HTTP routes: Requisitions call the Python service directly (`procurement_requisitions/services/funding_gateway.py:60-66`); the only other callers are seeds. Nothing calls `dia_budget_control.release_reservation`.
**Rule:** BUD §7 "The contract service principal is an authenticated service account, not a business role… It calls `revalidate_reservations`, `release_reservation`, `convert_reservation` and `adjust_commitment` with a downstream event reference and an idempotency key"; BUD-BR-015 "Release, conversion and commitment adjustment require an authenticated downstream event and are idempotent by correlation ID. No user keys amounts directly in Budget UI."; AGENTS.md §4.3.
**Reproduction / failing test sketch:** static; not run. As a Website User with only role `All`: `POST /api/method/kentender_budget.api.budget_api.release_reservation` `{"reservation":"<RSV reference>","amount":40,"downstream_event_id":"x","downstream_event_type":"x","idempotency_key":"K"}` twice. Expected: refusal `BUDGET_DOWNSTREAM_FORBIDDEN`; read result: remaining 100 to 60 to 20, "Reservation released" ledger rows. `convert_reservation {reservation, contract:"ANY", amount:<remaining>}` creates a commitment; `adjust_commitment {commitment, new_total:0}` cancels it and frees funds; a larger `new_total` consumes line availability. Pytest: `frappe.set_user(<user with no Budget assignment>); commit.release_reservation(...)` must raise `frappe.PermissionError`.
**Impact:** Any logged-in account (supplier portal users included) can free, convert or inflate Active funding reservations and commitments, altering Budget availability that every Requisition and Plan check reads. Reservation references are sequential and guessable.
**Verification:** CONFIRMED — budget_commitment_contracts.py:24-31 rejects only Guest, the four `@frappe.whitelist()` wrappers (budget_api.py:265-337) and dia_budget_control.py:24-26 forward without a role check, writes use ignore_permissions (:94,144,225,288) and idempotency_key is only a label; BUD §7 line 358 and BR-015 line 297 say what the finding quotes.

### AUD-XC-003 — Tender Management v2 publication API trusts a client `actor`; `actor=Administrator` skips every role check
**Severity:** Critical · **Classification:** CODE DEFECT (retained legacy surface) · **Doc:** TPR v0_17 §6 (publication is authorised only by the Accounting Officer; Administrator/System Manager "no business action"), AUTH v1_11 §5.5 (line 295), §8 (line 361) · **Module(s):** Tender Management v2 (TM2) · **Sources:** sweep-authz F-01, F-19 (TM2 `actor`), F-18 (TM2 part); sweep-hazards F-2, F-3 (action-availability part); sweep-state F6; sweep-sod F11
**Evidence**
- `kentender_procurement/kentender_procurement/tender_management/tender_publication/api/handlers.py:192,222,237,255,275,295,312` — seven whitelisted endpoints declare `actor: str | None = None` and forward it (`ApprovalDecisionService.approveForPublication(tn, payload, actor)` :265; `PublicationTransactionService.publishTender(tn, actor)` :320; `ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor)` :230).
- `.../tender_publication/approval/approval_decision.py:64-65` and `.../publication/transaction.py:28-29` and `.../authorization/publication_authorization.py:88-89` — `return _strip(actor) or _strip(frappe.session.user) or "Administrator"` (the supplied value wins).
- `.../authorization/publication_authorization.py:140-141` — `if actor == "Administrator": return` inside `_assert_any_role`; `:60-65` `_ROLES_APPROVE_OR_RETURN = {System Manager, Purchase Manager}`, `:66-73` `_ROLES_PUBLISH_TENDER` includes `Procurement Officer`.
- `.../security/authorization/integration.py:32` (`act = (actor or "").strip() or session.user ...`) then `ctx["granted_permissions"] = [spec.required_permission]` (integration.py near :36-38) self-grants the engine's permission check; `.../security/authorization/object_scope.py:39-40,118-119` `_break_glass` returns True for `Administrator` and short-circuits the TM2 tender scope check.
- `.../services/publish_tender.py:212`, `.../tender_publication/snapshot/configuration_snapshot.py:161` and `.../services/approve_tender_publication.py:201` — `frappe.set_user(actor)` switches the session to the supplied name for the write.
- Same family: `.../security/action_availability/api.py:154-158,162-166,184-188` evaluates availability for a client `actor`; read endpoints `pub_api_get_latest_publication_readiness` (handlers.py:207), `pub_api_get_publication_snapshot` (:327) have no role check.
- Reachability: the 56 `tm2_*` doctype JSONs are tracked (`git ls-files` count), `handlers.py` and its `__init__.py` are tracked and importable, and the TM2 workbench "stays live until the OD-F clean-up" (`docs/mvp-1-r1/12_bid_submission/reconciliation/legacy_inventory.md:42,53`); TPR follow-up FU-08 (`docs/mvp-1-r1/11_tenders/TPR-CHG-001_FOLLOW_UPS.md:16`) records the "inverted Administrator authority in `publication_authorization.py`" as known, deferred debt.
**Rule:** AUTH §5.5 "The client never supplies … effective role… as authority"; AUTH §8 "Setup authority is not business authority"; TPR §6 (AO authorises publication, no technical business action); AGENTS.md §4.3.
**Reproduction / failing test sketch:** static; not run. On kentender-test.local, with a TM2 Tender `T` that has a configuration snapshot (state `Locked for Approval`), signed in as a user holding no TM2 role: `POST /api/method/kentender_procurement.tender_management.tender_publication.api.handlers.pub_api_approve_for_publication` `tender_code=T&decision_payload={"decision":"Approved"}&actor=Administrator`, then `pub_api_publish_tender?tender_code=T&actor=Administrator`. Expected: permission denied; read result: both pass `_assert_any_role` and the decision/audit rows name Administrator. Pytest: call `ApprovalDecisionService.approveForPublication(T, {}, "Administrator")` with `frappe.session.user` set to a no-role user and assert `PermissionError`.
**Impact:** Where the TM2 doctypes are migrated and a TM2 Tender exists in a suitable state (the code and doctypes ship in the app; whether this site holds TM2 rows was not queried), any logged-in account can approve and publish a tender on the Administrator's authority. If TM2 is meant to be dead, the endpoints are still routable and should be removed rather than left live.
**Verification:** CONFIRMED — handlers.py:192-312 forward the client `actor`; approval_decision.py:64-65 lets it win, publication_authorization.py:140-141 returns early for Administrator, and the engine (decision_engine.py:178-260) allows because integration.py:32-38 self-grants the permission and `enforce_object_scope` is absent. Not checked: whether this site holds TM2 Tender rows (no DB access), so impact is conditional as the finding already states.


## 4.2 High

### AUD-XC-004 — Supplier-registry state changes (suspend, reinstate, expire, qualify/reject category) have no role gate and write with `ignore_permissions`
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** AUTH-ADR-001 v1_11 §5.1/§5.6 and AGENTS.md §4.3 (no approved module document governs KTSM; BDS FU-06 records it as a legacy model) · **Module(s):** Suppliers (KTSM registry) · **Sources:** new finding of this review (not in the source files); related to sweep-authz F-17, sweep-hazards F-4
**Evidence**
- `kentender_suppliers/kentender_suppliers/api/smw_workflow.py:88-91` `ktsm_suspend`, `:94-97` `ktsm_reinstate`, `:130-133` `ktsm_set_expired`, `:137-145` `ktsm_qualify_category`, `:148-151` `ktsm_reject_category`, `:154-157` `ktsm_start_category_review` — each is `@frappe.whitelist()` and calls straight into `governance.*` with no `_assert_*` call (contrast `ktsm_approve_supplier` :67-70 with `_assert_approver_or_admin()` and `ktsm_blacklist` :100-105 with `supplier_policy.can_blacklist()`).
- `kentender_suppliers/kentender_suppliers/services/governance.py:118-127,130-141,190-202,205-229,232-255,258-270` — the service functions check status and reason only; `_save` (governance.py:11-19) does `prof.flags.bypass_governance = True; prof.save(ignore_permissions=True)`; category functions use `row.db_set(...)`.
- `kentender_suppliers/kentender_suppliers/api/ktsm_landing.py:424-451` — `perform_action` (also `@frappe.whitelist()`, no gate) routes `suspend`, `reactivate`, `reinstate` to the same ungated functions.
- Consumers: `grep` for KTSM or `check_supplier_eligibility` in `kentender_procurement`, `kentender_budget`, `kentender_core` finds only `module_registry.py` and a workspace permission setup; no procurement code reads KTSM eligibility.
**Rule:** AUTH §5.5/§5.6 (every protected command resolves a registered responsibility before it mutates); AGENTS.md §4.3 "Enforce eligible source state, required role and organisational scope on the server". Severity note: the Critical definition (approve on someone else's authority through a whitelisted entry) would apply on its face; I rate it High because no in-repo business module consumes KTSM status and no approved document governs this legacy registry.
**Reproduction / failing test sketch:** static; not run. As a supplier Website User: `POST /api/method/kentender_suppliers.api.smw_workflow.ktsm_suspend` `{"supplier_profile":"<KTSM Supplier Profile name>","reason":"x"}` then `ktsm_set_expired {supplier_profile, reason}`; for a `KTSM Category Assignment` in `Requested` state: `ktsm_start_category_review {assignment_name}` then `ktsm_qualify_category {assignment_name}`. Expected: permission error; read result: operational status moves, a status-history row is written naming the caller, and the category becomes `Qualified`. Pytest: `frappe.set_user(<no-role user>); smw_workflow.ktsm_suspend(profile, "x")` must raise.
**Impact:** Any logged-in account can suspend or expire any supplier and approve any supplier category qualification in the legacy KTSM registry, changing what `check_supplier_eligibility` answers; history rows record the wrong authority. Blast radius is limited to KTSM data unless a consumer reads it.
**Verification:** CONFIRMED — smw_workflow.py:87-157 shows ktsm_suspend/reinstate/set_expired/qualify/reject/start_category_review with no `_assert_*` (unlike :67-70, :100-105) and governance.py `_save` uses ignore_permissions; ktsm_landing.py:424-451 routes to them; no kentender_procurement/budget/core module reads KTSM eligibility, supporting the High (not Critical) rating.

### AUD-XC-005 — Strategy Author can set a plan version Active (or edit an Active version) over REST; approval, readiness and segregation are skipped
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** STR v1_9 STR-BR-006 (line 218), STR-BR-015 (line 227), line 636, STR-AC-010 (line 748), STR-AC-032 (line 770) · **Module(s):** Strategy · **Sources:** trace-strategy F2; sweep-state F5; sweep-authz F-10 (Strategy part); sweep-sod F3 (Strategy part); sweep-audit F2 (Strategy part)
**Evidence**
- `kentender_strategy/kentender_strategy/kentender_strategy/doctype/strategic_plan_version/strategic_plan_version.json:150` — role `Strategy Author` `read/write/create` (same block shape in `strategic_plan.json:132`, `strategy_node.json:131`); `:68-75` field `status` is a plain Select with no `read_only`.
- `kentender_strategy/kentender_strategy/services/strategy_domain_guards.py:125-129` — `prev_status = None if doc.is_new() else ...` / `if prev_status in VERSION_IMMUTABLE:` / `for f in ("plan_id", "version_number", "based_on_plan_version_id")`: only three identity fields are locked once a version is Submitted/Active/Superseded (`VERSION_IMMUTABLE`, :17). `:134-135` `if doc.status == "Active" and prev_status != "Active": assert_no_primary_overlap(doc)` is the only status rule (overlap only; no readiness, no approver, no segregation).
- `kentender_strategy/kentender_strategy/hooks.py` (75 lines) registers no `has_permission`, `permission_query_conditions` or `kentender_scope_map` for any Strategy doctype.
- `kentender_strategy/kentender_strategy/services/strategy_domain_guards.py:194-199` `_assert_version_editable` guards Strategy Node edits by the node's current `plan_version_id` only.
**Rule:** STR-BR-006 "Active content is immutable"; line 636 "Submitted for approval, Active and Superseded versions are immutable"; STR-BR-015 "Approval repeats all readiness and overlap checks and activates atomically"; STR-AC-010 "the author of a version cannot approve that version"; STR-AC-032 "Every Strategy write is authorised through an Active User Responsibility Assignment resolved by the registered permission hooks".
**Reproduction / failing test sketch:** static; not run. As a user holding only Strategy Author: `PUT /api/resource/Strategic Plan Version/<own Draft>` `{"status":"Active"}` (dates inside the plan period, no overlapping Primary plan). Expected: refusal; read result: saved Active with no Submit/Approve event, so Planning's "Active Primary plan" resolution serves it. Also `PUT … <Active version> {"effective_to":"2030-01-01"}`. (A `DELETE` of a version that has Strategy Nodes is blocked by Frappe's link check; do not use it as the reproduction.) Pytest: `frappe.set_user(author); v = frappe.get_doc("Strategic Plan Version", draft); v.status = "Active"; v.save()` must raise.
**Impact:** One role holder can activate a plan version without the Approver, readiness check or no-self-approval rule, and rewrite the applicability window of an Active version that downstream snapshots depend on.
**Verification:** CONFIRMED — strategic_plan_version.json:150 gives Strategy Author write, `status` is a plain Select, strategy_domain_guards.py:125-135 locks only three identity fields and checks only primary overlap on activation, and no app hooks.py registers a has_permission/doc_events guard for Strategy doctypes.

### AUD-XC-006 — Budget Officer / Budget Approver can write version status and approved amounts over REST
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** BUD v1_12 BUD-BR-005 (line 287), BUD-BR-021/022 (lines 303-304), BUD-BR-025 (line 307), BUD-BR-028 (line 310), line 1245 and §18 (line 1571) · **Module(s):** Budget · **Sources:** sweep-state F4; sweep-authz F-10 (Budget part); sweep-sod F3 (Budget part); sweep-audit F2 (Budget part); trace-budget F-02
**Evidence**
- `kentender_budget/kentender_budget/kentender_budget/doctype/procurement_budget_version/procurement_budget_version.json:250` Budget Officer `rwc`, `:262` Budget Approver `rw`; `procurement_budget_line_version.json:133` Budget Officer `rwc`; `procurement_budget_line.json:71` and `procurement_budget.json:95` Budget Officer `rwc`. Field `status` (version) and `approved_amount` (line version) carry no `read_only`.
- `kentender_budget/kentender_budget/kentender_budget/doctype/procurement_budget_version/procurement_budget_version.py:13-19` validates revision type pairing and a future approval date only; `procurement_budget_line_version.py` is `class ...: pass`.
- `kentender_budget/kentender_budget/hooks.py:87-106` registers `budget_read_scope` hooks; `kentender_budget/kentender_budget/services/budget_read_scope.py:51-68` and `kentender_core/kentender_core/services/authorization.py:461-501` only veto (core docstring: "It only ever *restricts*"); they apply to every ptype, so a writer needs an effective Site-wide assignment, but a holder of one is not stopped from writing status or amounts.
**Rule:** BUD-BR-005 "Only Draft versions are editable"; BUD-BR-021/022 approval rechecks and activates atomically; BUD-BR-025 "statuses… are never client-editable"; BUD-BR-028 "Only a successor Version… changes an approved amount"; BUD §18 "Do not permit direct edits of Active, Superseded or Closed data."
**Reproduction / failing test sketch:** static; not run. As a user holding the Budget Officer role with an Enabled Site-wide Budget Officer assignment (the Frappe Role alone is vetoed by the registered `has_permission` hook, `kentender_budget/hooks.py:101-106` to `kentender_core/services/authorization.py:493-494`, which denies every ptype for a user with no effective assignment; the hook only ever restricts, it never grants): (1) `PUT /api/resource/Procurement Budget Line Version/<line version of the Active version>` `{"approved_amount": 1000000000}`; (2) `PUT /api/resource/Procurement Budget Version/<old Active>` `{"status":"Superseded"}` then `PUT …/<Draft>` `{"status":"Active"}` (two writes, because a DB unique marker allows one Active per budget). Expected: refusal. Read result: availability seen by `check_funding` changes and a Draft is Active with no Approver, readiness check, no-self-approval check or ledger event. Pytest: `frappe.set_user(officer); d = frappe.get_doc("Procurement Budget Line Version", lv); d.approved_amount = 1; d.save()` must raise.
**Impact:** A Budget Officer can change approved amounts of an Active Budget or self-activate a version without a Budget Approver, bypassing the approval, segregation and audit rules that govern every downstream funding check.
**Verification:** CORRECTED — DocPerms (json :250,:262,:133,:71,:95), empty/shape-only controllers and writable `status`/`approved_amount` all verified, but the reproduction was incomplete: kentender_budget hooks.py:101-106 registers `has_permission` and authorization.py:493-494 returns False when the user has no effective assignment, so the REST write works only for a Budget Officer/Approver with an Enabled Site-wide assignment (the Frappe Role alone is vetoed). Reproduction wording fixed; severity unchanged.

### AUD-XC-007 — Procurement Planner and Departmental Author / HoD can write Annual Plan and Departmental Plan lifecycle fields over REST
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** PLN v1_29 field table (lines 218, 225, 237) and "Historical rule" (line 147) · **Module(s):** Planning · **Sources:** sweep-state F3; sweep-authz F-10 (Planning part); trace-planning F-29; sweep-audit F2 (Planning part)
**Evidence**
- `kentender_procurement/kentender_procurement/procurement_planning/doctype/annual_plan_version/annual_plan_version.json:222`, `annual_plan/annual_plan.json:104`, `annual_plan_item/annual_plan_item.json:427`, `plan_source_allocation/plan_source_allocation.json:217` — Procurement Planner `rwc`. `departmental_plan_version.json:120/126`, `departmental_plan_entry.json:174/180`, `departmental_plan.json:118/124` — Departmental Author `rwc`, Head of User Department `rw`.
- Controllers: `annual_plan.py`, `annual_plan_version.py`, `plan_source_allocation.py`, `departmental_plan.py`, `departmental_plan_version.py` are 8-line `pass` classes (`class AnnualPlan(Document): pass`); `annual_plan_item.py` and `departmental_plan_entry.py:12-23` validate shape only. `version_status` (annual_plan_version), `active_version` (annual_plan), `indicative_amount` (plan_source_allocation) and `item_state` (annual_plan_item) are `read_only` in JSON only.
- `kentender_procurement/kentender_procurement/procurement_planning/services/planning_authorization.py:484-494` (DPP family hook) delegates to the core scope predicate, which does not look at `ptype` or record state; the Annual Plan family has no hook (`kentender_procurement/kentender_procurement/hooks.py:382-385` comment: "the Annual Plan family has Site-wide readers only and stays unregistered").
**Rule:** PLN line 225 `version_status` "Governed only"; line 218 `active_version_id` "Activation transaction only"; line 237 item `title`/`description` "Planner Draft only"; line 147 "Draft fields freeze at certification/submission. Decisions, events and published files are append-only."
**Reproduction / failing test sketch:** static; not run. As a Procurement Planner: `PUT /api/resource/Annual Plan Version/<v>` `{"version_status":"Active"}` then `PUT /api/resource/Annual Plan/<p>` `{"active_version":"<v>"}`; or `PUT /api/resource/Plan Source Allocation/<n>` `{"indicative_amount": 1}` on a submitted version. As a Departmental Author in scope: `PUT /api/resource/Departmental Plan Entry/<n>` `{"indicative_amount": 999}` on a Submitted/Accepted version. Expected: refusal. Read result: plan Active without HOPF signature, AO adoption, statutory decision or publication, and frozen snapshot content rewritten. Pytest: `frappe.set_user(planner); v = frappe.get_doc("Annual Plan Version", ver); v.version_status = "Active"; v.save()` must raise.
**Impact:** The statutory approval chain and the certified-snapshot freeze can be bypassed by the roles the service layer trusts; Requisitions then draw against a plan that was never approved.
**Verification:** CONFIRMED — DocPerm lines (annual_plan_version.json:222 etc., departmental_plan_*.json:120/126) verified, controllers are 8-line `pass` or shape-only (annual_plan_item.py, departmental_plan_entry.py), `read_only` is not enforced by frappe api/v1.py:49-63 `doc.update(data); doc.save()`, and the Annual Plan family has no hook (kentender_procurement hooks.py:378-385) while the DPP hook (planning_authorization.py:484-494) only checks OU scope.

### AUD-XC-008 — Departmental Author / HoD can write Need, Revision, Review Task and Withdrawal Request lifecycle fields over REST
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** NDS v1_16 NDS-BR-017 (line 436), §16.1 (line 1798) · **Module(s):** Departmental Needs · **Sources:** sweep-state F2; sweep-authz F-06 (write half), F-10 (Needs part); sweep-sod F3 (Needs part); sweep-audit F2 (Needs part); trace-needs C-06
**Evidence** (role to doctype to field; DocPerm lines in `kentender_procurement/kentender_procurement/departmental_needs/doctype/<dt>/<dt>.json`)
- Departmental Author `rwc` / HoD `rw` on `departmental_need` (:120/:126), field `current_state`, `current_accepted_revision`; on `departmental_need_revision` (:151/:157), field `revision_status`; on `need_withdrawal_request` (:125/:131), field `status`. HoD `rw` on `departmental_need_review_task` (:155), field `status`. All are `read_only: 1` in JSON only; no `permlevel`.
- `kentender_procurement/kentender_procurement/departmental_needs/doctype/departmental_need/departmental_need.py:23-26,28-39` — `validate` checks only that `current_state in NEED_STATES` and that OU/FY do not change; `:41-42` `on_trash` refuses delete.
- `kentender_procurement/kentender_procurement/departmental_needs/doctype/departmental_need_revision/departmental_need_revision.py:37-47` — `if self.is_new() or self.revision_status in MUTABLE_REVISION_STATUSES: return`: the guard tests the NEW status, and `constants.py:48` makes only `Draft` mutable, so one save that sets `revision_status = "Draft"` and edits content passes; `revision_status` itself is not in `REVISION_CONTENT_FIELDS` (`constants.py:55-62`).
- `kentender_core/kentender_core/services/authorization.py:461-501` — the hook vetoes by OU only, for every `ptype`.
**Rule:** NDS-BR-017 "Generated references, revision numbers, statuses, hashes and audit data are never client-editable."; NDS §16.1 "Do not expose writable DocType endpoints that bypass commands."; NDS-BR-006 maker-checker.
**Reproduction / failing test sketch:** static; not run. As Departmental Author of OU A with own Need N (Draft): `PUT /api/resource/Departmental Need/N` `{"current_state":"Accepted for planning"}`; for an Accepted revision R: `PUT /api/resource/Departmental Need Revision/R` `{"revision_status":"Draft","title":"Changed after acceptance"}` (a plain `{"title":…}` is refused by the guard above, so the status flip is required). Expected: `NDS_STATE_CONFLICT`; read result: Need accepted with no HoD decision, no Decision row and no event; accepted content rewritten. Pytest: `frappe.set_user(author); n = frappe.get_doc("Departmental Need", N); n.current_state = "Accepted for planning"; n.save()` must raise.
**Impact:** A Departmental Author can accept their own Need (or rewrite an accepted revision) without a Head of User Department, and Planning consumes the result as the accepted source.
**Verification:** CONFIRMED — DocPerms verified (departmental_need.json:120/126, revision :151/157, withdrawal :125/131, task :155) with `read_only` only; departmental_need.py:23-39 checks only state-in-set and scope immutability, and departmental_need_revision.py:37-47 tests the NEW `revision_status` against constants.py:48 so a Draft-flip plus edit passes; Revision/Withdrawal have no scope hook (hooks.py:378-385).

### AUD-XC-009 — Audit-event read endpoints return any object's audit trail to any logged-in account
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** AGENTS.md §4.3 ("Return only data the caller is allowed to see"), AUTH-ADR-001 v1_11 §5.4 (counts and rows must not disclose what the caller cannot see) and §8 (audit evidence is technical read) · **Module(s):** Tender Management v2 security API over the platform `Audit Event` ledger · **Sources:** sweep-authz F-03; sweep-hazards F-3
**Evidence**
- `kentender_procurement/kentender_procurement/tender_management/security/api.py:114-115,132-133` — `sec_api_audit_events(object_type, object_code, filters)` and `sec_api_audit_tender_events(tender_code, filters)` are `@frappe.whitelist()`; `_run` (:122-129, :139-145) performs no role or scope check.
- `kentender_procurement/kentender_procurement/tender_management/security/audit/event_service.py:85-99,117-` — `frappe.get_all("Audit Event", filters={"document_type": ot, "document_name": oc}, fields=[… "performed_by", "timestamp", "metadata"])`; `frappe.get_all` forces `ignore_permissions` and `object_type`/`object_code` are caller-chosen. `Audit Event` DocPerm is System Manager/Administrator only (`kentender_core/kentender_core/kentender_core/doctype/audit_event/audit_event.json:90,102`).
**Rule:** AGENTS.md §4.3; AUTH §8 "audit evidence" is technical-read; STR v1_9 line 161 (audit events are produced by commands and protected reads).
**Reproduction / failing test sketch:** static; not run. As a Website User: `GET /api/method/kentender_procurement.tender_management.security.api.sec_api_audit_events?object_type=Departmental Need&object_code=<need name>`. Expected: permission error or empty; read result: event type, `performed_by`, timestamp and metadata JSON of that Need's trail. Pytest: same call under `frappe.set_user(<no-role user>)` must raise.
**Impact:** Any logged-in account, including a supplier, can read actors, times and metadata for any audited object in any module; sensitivity depends on what each module writes into `metadata` (not assessed).
**Verification:** CONFIRMED — security/api.py:114-145 are `@frappe.whitelist()` with `_wrap` (no auth) and event_service.py:85-99 uses `frappe.get_all` (ignore_permissions) on caller-chosen object_type/object_code with no redaction of `metadata`; audit_event.json:90,102 grants read only to System Manager/Administrator.

### AUD-XC-010 — `Audit Event` is writable and deletable by System Manager, and Strategy's no-self-approval check reads it
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** STR v1_9 line 161 and line 636; AUTH-ADR-001 v1_11 §8 (line 361) · **Module(s):** Core audit ledger; Strategy · **Sources:** sweep-audit F1, F7; sweep-state F11 (audit part); sweep-authz F-09 (audit part); trace-strategy F22
**Evidence**
- `kentender_core/kentender_core/kentender_core/doctype/audit_event/audit_event.json:84-92` — System Manager `create/delete/write` (role at :90); `:96-104` the same for Administrator; `track_changes: 1` (a Frappe Version row is the only trace, and Version rows are themselves editable by System Manager).
- `kentender_core/kentender_core/kentender_core/doctype/audit_event/audit_event.py` is `class AuditEvent(Document): pass`; `kentender_core/kentender_core/services/audit_event_service.py:1` docstring says "Append-only audit events". No incoming Link field targets `Audit Event` (grep of doctype JSON), so Frappe's link check does not block deletes.
- `kentender_strategy/kentender_strategy/services/strategy_authorization.py:102-109` — `_submitted_by` reads `list_events("Strategic Plan Version", version_name)` for `action == "Submit for approval"`; `:112-118` `has_ever_been_submitted` reuses it; `:121-127` `_blocked_by_self_approval` returns `_submitted_by(...) == user`.
**Rule:** STR §4.6 (line 161) "An append-only system event… users do not edit it"; STR line 636 "Deleting lifecycle events… prohibited"; AUTH §8 "Administrator and System Manager hold technical **read** access".
**Reproduction / failing test sketch:** static; not run. As System Manager: `PUT /api/resource/Audit Event/<name>` `{"performed_by":"<other user>"}`; `DELETE /api/resource/Audit Event/<id of the "Submit for approval" row of a submitted Strategic Plan Version>`. Expected: refusal. Read result: edit and delete succeed; `_blocked_by_self_approval` then returns False for the submitter and `has_ever_been_submitted` is False, re-enabling `discard_strategy_plan_draft`. Pytest: `frappe.set_user(sm); frappe.delete_doc("Audit Event", name)` must raise.
**Impact:** The platform audit ledger can be rewritten by a technical user, and one Strategy segregation control and one "never discard once submitted" lock are only as strong as those editable rows.
**Verification:** CONFIRMED — audit_event.json:84-104 gives System Manager and Administrator create/write/delete, audit_event.py is `pass`, no Link field or hook (`doc_events`) protects the doctype, and strategy_authorization.py:102-127 derives self-approval and 'ever submitted' from `list_events` (strategy_audit.py:69-82).

### AUD-XC-011 — Role `All` has create/write on Confirmed Tender Document Package and IT Tender Publication Record
**Severity:** High · **Classification:** CODE DEFECT (legacy Tender Configurations surface) · **Doc:** TPR v0_17 §12.3 rule 1 (line 1621); AUTH-ADR-001 v1_11 §5.1/§19 · **Module(s):** Tender Configurations (legacy) · **Sources:** sweep-authz F-05; sweep-state F7
**Evidence**
- `kentender_procurement/kentender_procurement/tender_configurations/doctype/confirmed_tender_document_package/confirmed_tender_document_package.json:219` and `.../it_tender_publication_record/it_tender_publication_record.json:317` — `"role": "All"` with `"create": 1, "read": 1, "write": 1` (print 1, no delete). `frappe/permissions.py:558` gives `All` to every non-Guest user.
- `.../it_tender_publication_record.json:96-102` — `status` is an editable Select (`Awaiting Publication Setup … Published … Cancelled`); `.../it_tender_publication_record.py:46` `TERMINAL_STATUSES` blocks edits only when the stored status is already terminal (:75-80) and `PACKAGE_LOCKED_FIELDS` (:29-43) does not include `status`.
- `.../confirmed_tender_document_package.json:78-84` `package_status` editable; `.../confirmed_tender_document_package.py:21-27,32-` locks artifact fields only while the stored status is `Confirmed`/`Awaiting Publication Setup`, and `package_status` is not in the locked list, so `Confirmed` to `Invalidated` is allowed.
- No scope hook is registered for either doctype (`kentender_procurement/kentender_procurement/hooks.py` has no entry).
**Rule:** TPR §12.3 "Submitted, approved, publication-authorised, published… facts are append-only"; AUTH §5.1 (permission by registered responsibility); the same package is described as immutable in its own controller.
**Reproduction / failing test sketch:** static; not run. As a supplier Website User: `PUT /api/resource/IT Tender Publication Record/<name>` `{"status":"Published"}`; `PUT /api/resource/Confirmed Tender Document Package/<name>` `{"package_status":"Invalidated"}`. Expected: refusal; read result: record marked Published with no publication transaction (and then locked as terminal), or a confirmed package invalidated.
**Impact:** Any logged-in account can mark a publication record Published or invalidate a confirmed tender package. The module is legacy and deferred (OD-F), but the doctypes are live.
**Verification:** CONFIRMED — confirmed_tender_document_package.json:219 and it_tender_publication_record.json:317 grant role `All` read/write/create; frappe permissions.py:545-558 adds `All` to every non-Guest user, the controllers (it_tender_publication_record.py:29-95, confirmed_tender_document_package.py:21-80) do not lock `status`/`package_status` transitions, and no scope hook is registered.

### AUD-XC-012 — `check_funding` / `reserve_funding` accept Finance Confirmation Officer, trust a self-declared caller, and validate no Requisition
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** BUD v1_12 §7 (line 354 REQ service principal), §12.6 (line 1183 "`reserve_funding` rejects a Planning caller even when the user also holds Finance Confirmation Officer"), BUD-BR-009 (line 291), BUD18-AC-014 (line 1383) · **Module(s):** Budget, Requisitions · **Sources:** trace-budget F-03
**Evidence**
- `kentender_budget/kentender_budget/services/budget_check_reserve_contracts.py:106-109` — `_CHECK_RESERVE_CALLER_ROLES = ("Finance Confirmation Officer", ROLE_HEAD_OF_PROCUREMENT_FUNCTION)`; `:112-126` `_require_check_reserve_capability` accepts either; its comment cites "REQ-CHG-001 v1.6 D1" (an earlier REQ version; REQ v1_14 names no such caller list).
- `kentender_budget/kentender_budget/api/budget_api.py:219-260` — `check_funding(..., calling_module, caller_reference)` and `reserve_funding(...)` are `@frappe.whitelist()`; `calling_module` defaults to `"Procurement Planning"` and is taken from the request (:227, :241), stored in the token cache (budget_check_reserve_contracts.py:267) and replayed at reserve time (:333).
- `kentender_budget/kentender_budget/services/budget_check_reserve_contracts.py:346-354,356-370` — `drawdown_line_id` is client text; the only check is that no reservation already uses it; no Requisition, drawdown or live REQ authority is looked up.
- `kentender_budget/kentender_budget/tests/test_check_reserve_requisition_caller.py:53-66` — `test_finance_confirmation_officer_still_permitted` asserts the contradicting behaviour (a Finance Confirmation Officer reserves and the reservation records `calling_module == "Procurement Planning"`).
**Rule:** BUD §12.6 "`reserve_funding` rejects a Planning caller even when the user also holds Finance Confirmation Officer"; BUD-BR-009 "Reservation begins only at successful Procurement Requisition authorisation"; BUD §7 "Budget validates it with the immutable REQ/drawdown facts, live initiating authority".
**Reproduction / failing test sketch:** static; not run. As a user holding Finance Confirmation Officer (e.g. the seed finance officer): `check_funding(plan_item="x", plan_version="x", source_set_hash="h", allocations=[{"budget_line":<line>,"amount":"1.00","plan_source_allocation":"x"}], correlation_id="c")`, then `reserve_funding(token=<token>, source_set_hash="h", idempotency_key="k")`. Expected: `BUDGET_FINANCE_TASK_DENIED`; read result: Active reservation with no Requisition. Invert the cited test.
**Impact:** A Finance Confirmation Officer or Head of Procurement Function can place Active funding holds with no Requisition behind them, reducing line availability, and the ledger's caller field is whatever the client typed.
**Verification:** CONFIRMED — budget_check_reserve_contracts.py:106-126 admits Finance Confirmation Officer, budget_api.py:219-260 takes `calling_module`/`caller_reference` from the request and drawdown_line_id is only uniqueness-checked (:346-354), and test_check_reserve_requisition_caller.py:53-66 asserts the contradicting behaviour; BUD line 1183 and BUD18-AC-014 (line 1383) say Planning callers are rejected.

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

### AUD-HND-001 — Tender "requisition correction" route has no producer; a consumed handoff can never be re-authorised and the tests fabricate the missing state
**Severity:** High · **Classification:** SPEC DEFECT · **Doc:** REQ-CHG-001 v1_14 §7.4 (line 608) vs TPR-CHG-001 v0_17 §10.14 / TPR09-AC-010 (line 1712) vs E2E-REQ-001 v0.2 §12 (line 271); also a CODE DEFECT (stub in Tenders). Divergence from owner-tracked open item: REQ FOLLOW_UPS FU-30 (High, Open) · **Module(s):** Requisitions, Tenders, Planning · **Sources:** sweep-handoffs F-1
**Evidence**
- `kentender_procurement/kentender_procurement/tenders/services/handoff_gateway.py:96-101` — `def release(...)`: `fail("TND_HANDOFF_INVALID", "A consumed requisition handoff can no longer be released. The Tender correction route is being revised.", ...)`.
- `kentender_procurement/kentender_procurement/procurement_requisitions/services/authorise.py:184-185` — `if handoff_doc.consumed_at: fail("REQ_HANDOFF_CONSUMED", ...)` (revocation refused after consumption).
- `kentender_procurement/kentender_procurement/procurement_requisitions/services/correction.py:212` — `if root.current_state != "Revoked": fail("REQ_STALE_VERSION")` (`CreateRequisitionCorrectionDraft` needs a Revoked root, which a consumed one can never be).
- `kentender_procurement/kentender_procurement/procurement_planning/services/plan_requisition.py:280-285` — `eligible = (item.item_state == "Active" and funding_confirmed and total_remaining_qty > 0 and total_remaining_value > 0)`; a consumed handoff keeps its drawdown (`handoff.py:109-110` "Consumption frees the item's open slot (§5.1) but releases no drawdown").
- `kentender_procurement/kentender_procurement/tenders/services/correction.py:120` — `start_corrected_tender_version` refuses any consumed handoff (`TND_HANDOFF_CONFLICT`) and only continues from a *different*, unconsumed handoff on the same Plan Item (`correction.py:83`, `handoff_gateway.py:105-108` `successors`).
- `kentender_procurement/kentender_procurement/tenders/tests/test_lifecycle.py:331-333` — "Owner-contract stand-in ... (REQ FOLLOW_UPS FU-30 owns the real route)" then `frappe.db.set_value("Authorised Requisition Handoff", authorised["handoff"], {"consumed_at": None, "tender": None, "tender_version": None}, ...)`. The same un-consume is in `tenders/seeds/playwright_ui_fixtures.py:597`.
- Docs: REQ v1_14 line 608 "after handoff consumption, Requisitions cannot revoke or edit the authorised package; Tender Preparation uses its own upstream-correction route, per TPR-CHG-001 §10.4" but TPR v0_17 line 1067 is `### 10.4 TPR-DES-03 — Draft: Tender details` (the correction route is §10.14); TPR09-AC-010 (line 1712) "can continue only from a newly authorised successor handoff"; E2E-REQ-001 v0.2 line 271 "release the handoff, correct and reauthorise" (REQ v1.11 removed release).
**Rule:** TPR09-AC-010 "Requisition-owned correction stops the current Tender Version and can continue only from a newly authorised successor handoff" requires a REQ command that yields such a successor; REQ §7.4 says no such REQ command exists after consumption and points at the wrong TPR section. AGENTS.md §5 (a stub that blocks completion is a defect).
**Reproduction / failing test sketch:** (static; not run) On the test site: authorise a requisition drawing 100% of a Plan Item's remaining allowance; `StartTender`; `RequestRequisitionCorrection` as HOPF. The Tender is `Requisition correction requested` and a "Correct Requisition" task goes to the Departmental Author. Try every REQ command: `RevokeUnconsumedAuthorisation` -> `REQ_HANDOFF_CONSUMED`; `CreateRequisitionCorrectionDraft` -> `REQ_STALE_VERSION` (root is Authorised); `PrepareITEquipmentRequisition` -> not eligible (remaining qty/value 0). `handoff_gateway.successors(plan_item_id=...)` stays empty, so `StartCorrectedTenderVersion` is unreachable. If allowance remained, a second requisition is possible but it is an additional draw while the stopped Tender's drawdown and Budget reservation stay held (inference from `handoff.py:109-110`). Test sketch: replace the `db.set_value` in `test_correction_stops_the_version...` with real REQ calls; it cannot pass.
**Impact:** Any Tender that needs an upstream requisition correction after Start is permanently stopped with no way to continue, and the three approved documents disagree on which route is meant.
**Verification:** CONFIRMED — `handoff_gateway.py:96-101` (`release` always fails), `authorise.py:184-185` and `correction.py:212-213` refuse every REQ route on a consumed handoff, and the only continuation test un-consumes the handoff by direct DB write (`test_lifecycle.py:333`, `playwright_ui_fixtures.py:597`); REQ v1_14 line 608 and TPR09-AC-010 line 1712 confirmed, and REQ FU-30 (High, Open) records the same break as owner-known.

### AUD-HND-002 — Need withdrawal checks only the named revision's local usage card; Active Plan dependency of an older revision is ignored and Planning activation never revalidates the Need
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** NDS-CHG-001 v1_16 NDS-BR-016 (line 435), §5.3 (line 410), §8.1 (line 617), §8.3 (lines 646-650), test rule line 1581 · **Module(s):** Departmental Needs, Planning · **Sources:** sweep-handoffs F-11 (with F-5 as the trigger)
**Evidence**
- `kentender_procurement/kentender_procurement/departmental_needs/services/lifecycle.py:976` — `detail = planning_usage_detail(cstr(need), cstr(accepted_revision))`; `usage.py:41-49,72` `_projection(accepted_revision)` reads one revision's `Need Planning Usage Projection` row.
- `lifecycle.py:1030` `check_withdrawal_dependency(doc.name, doc.current_accepted_revision)` and `lifecycle.py:1107-1111` `dependency = check_withdrawal_dependency(doc.name, request.accepted_revision)` ... `if dependency["included"]: fail("NDS_ACTIVE_PLAN_DEPENDENCY", ...)`. Only the one revision is consulted.
- `kentender_procurement/kentender_procurement/departmental_needs/services/usage.py:90-123` — `older_revision_usage` already walks superseded revisions for *display* but is not used by the withdrawal check (`grep` shows its only caller is `usage.py:151`).
- `lifecycle.py:967-974` docstring cites "NDS-BR-016 ties the block to the exact accepted version"; the approved rule says the opposite (below).
- `kentender_procurement/kentender_procurement/procurement_planning/services/plan_publication.py:64-82` — `_activate_version` marks items Active and ends in `_publish_usage_events(...)`; no Need eligibility check. `grep` of `needs_intake`/`departmental_needs` in `procurement_planning/services` shows no call from `plan_governance.py` or `plan_publication.py`; `validate_accepted_need_withdrawal_for_decision` exists nowhere in the repo.
**Rule:** NDS-BR-016 "An accepted withdrawal remains pending while any accepted revision of this stable Need has an authoritative Active Plan dependency; a newer accepted pointer or disposition does not clear an older revision's inclusion." §5.3 (line 410) "The decision checks the stable Need **across all accepted revisions**, not just the revision named by the request or the local usage card." Line 1581: "Merely injecting a local Not included projection is not a valid withdrawal test." §8.3 line 647: Planning "validates NDS accepted eligibility through the owner contract ... no Active source may race past committed withdrawal." Note the document itself marks the Planning-side validator as owed (line 650 "matching Planning implementation is required before claiming that race is closed").
**Reproduction / failing test sketch:** (static; not run) On the test site: accept Need N revision V1; accept the departmental plan; activate the Annual Plan (V1 usage = `Fully included`). Raise and accept successor revision V2 (`current_accepted_revision = V2`; `lifecycle.py:780-783`; only `DepartmentalNeedSuperseded.v1` is published, see AUD-NDS part's successor-projection finding, sweep-handoffs F-5). No usage row exists for V2. As the requester call `request_withdrawal(need=N)`; as a second reviewer `decide_withdrawal(..., decision="approve")`. `check_withdrawal_dependency(N, V2)` returns `included=False` and the withdrawal is approved while the Active Plan still carries V1. pytest sketch: build that world, assert `decide_withdrawal(approve)` raises `NDS_ACTIVE_PLAN_DEPENDENCY`; it will not.
**Impact:** A Need whose earlier revision is in an Active Annual Plan can be withdrawn, orphaning the plan item's source lineage; the same missing owner contract lets a Need withdrawn between approval and activation still activate.
**Verification:** CONFIRMED — `lifecycle.py:1030,1107-1111` call `check_withdrawal_dependency` with one pinned revision, `usage.py:41-49,82` reads only that revision's projection row (absent row reads "Not included") and nothing in the successor-accept path (`lifecycle.py:780-811`) copies or consults the older row; `older_revision_usage` is display-only (`usage.py:151`) and `validate_accepted_need_withdrawal_for_decision` exists nowhere in the repo. Overlaps AUD-NDS-002 (same defect, two parts).

### AUD-STR-001 — `save_strategy_structure_draft` deletes any record of any DocType (permissions bypassed)
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** STR-CHG-001 v1.9 §5.1 "Records are never deleted after first submission"; STR-BR-006; §9 `STRATEGY_INVALID_STATE`; AGENTS.md §4.3 · **Module(s):** kentender_strategy (reaches any app's DocType) · **Sources:** trace-strategy F1a (downgraded Critical to High by the lead)
**Evidence**
- `STR/api/strategy_consumer_api.py:128-129` — `@frappe.whitelist()` `def save_strategy_structure_draft(plan_version_id, nodes=None, indicators=None, targets=None, deletes=None, ...)`; `:141-149` passes `deletes=_obj(deletes)` straight to the service.
- `STR/services/strategy_writes.py:354` — `exercised = require_plan_version_capability(frappe.session.user, CAP_AUTHOR, version)` is the only gate. It needs an Enabled Site-wide Strategy Author assignment (`STR/services/strategy_authorization.py:134-150`); it does not test the version's status or who created it, so it is not bypassable by a non-Author but any Author passes.
- `STR/services/strategy_writes.py:372-376` — `doctype, name = item.get("doctype"), item.get("name")` ... `_assert_deletable(doctype, name)` ... `frappe.delete_doc(doctype, name, ignore_permissions=True)`; the doctype string comes from the request.
- `STR/services/strategy_writes.py:320-335` — `_assert_deletable` inspects only `Strategy Node` and `Performance Indicator` children; every other DocType falls through.
- `STR/services/strategy_writes.py:358-368` — the "submitted once" lock reads the audit events of the version named in the request only, so an Author names a never-submitted Draft of their own to pass it.
- Mitigations seen in Frappe (`apps/frappe/frappe/model/delete_doc.py:23-129`): linked records raise `LinkExistsError` unless `force`; standard DocTypes delete only in developer mode. Unlinked business rows, `Audit Event` (no `on_trash`, `kentender_core/.../audit_event/audit_event.py`) and similar are deleted.
**Rule:** STR §5.1 "Records are never deleted after first submission"; §13 "Deleting lifecycle events ... prohibited"; AGENTS.md §4.3 authorise and validate input. A structure change set is limited to this version's nodes, indicators and targets (§12.3).
**Reproduction / failing test sketch:** (static; not run) 1. On kentender-test.local, as a user holding Strategy Author, `save_strategy_plan_draft(payload={"title":"X","plan_role":"Primary","period_start":"2030-07-01","period_end":"2035-06-30","effective_from":"2030-07-01","effective_to":"2035-06-30"})` and note the new version id V. 2. `POST /api/method/kentender_strategy.api.strategy_consumer_api.save_strategy_structure_draft` with `plan_version_id=V`, `deletes=[{"doctype":"Audit Event","name":"<any existing Audit Event name>"}]`. Expected: refused. Actual by reading: deleted, response `deleted:[name]`. Test: author calls with `deletes=[{"doctype":"ToDo","name":<existing>}]`, assert `frappe.ValidationError` and the ToDo still exists.
**Impact:** A Strategy Author can destroy audit rows (including the "Submit for approval" rows the lock and the no-self-approval rule read) or any unlinked record in any app, outside their authority and with no audit event of the deletion itself.
**Verification:** CONFIRMED — `STR/services/strategy_writes.py:372-376` deletes an arbitrary request-supplied doctype/name with `ignore_permissions=True`, `_assert_deletable` (`:320-335`) only knows two doctypes, and no `on_trash`/`doc_events` hook exists in any app's hooks.py or on Audit Event (`audit_event.py` is `pass`).

### AUD-STR-002 — Structure change set accepts record names from other versions: Active content can be deleted or moved
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** STR-BR-006 "Active content is immutable"; §4.3 `plan_version_id` "Prevents content leaking between plan versions"; §12.3 "no cross-version move"; §13 "Submitted for approval, Active and Superseded versions are immutable" · **Module(s):** kentender_strategy · **Sources:** trace-strategy F1b; calibration check 2
**Evidence**
- `STR/services/strategy_writes.py:397-403` — `data["plan_version_id"] = plan_version_id` then `if name and frappe.db.exists("Strategy Node", name): doc = frappe.get_doc("Strategy Node", name); doc.update(data)` — the request's version id overwrites the record's own; same shape for indicators (`:416-422`) and targets (`:431-439`, `indicator_id` re-pointable).
- `STR/services/strategy_domain_guards.py:194-199` — `_assert_version_editable(doc.plan_version_id)` therefore tests the NEW (own Draft) version after `doc.update`, not the version the record belongs to. `validate_strategy_node` (`:202-228`) and `validate_performance_target` (`:274-321`) have no previous-value check on `plan_version_id`/`indicator_id`.
- `STR/services/strategy_writes.py:372-376` — deletes never verify the record belongs to `plan_version_id`.
**Rule:** STR-BR-006; §12.3 "Move up/down changes only siblings; no cross-version move."; §4.3 "Prevents content leaking between plan versions."
**Reproduction / failing test sketch:** (static; not run) 1. Author with an Active V1 and an open successor Draft V2 (via `create_strategy_successor_version`). 2. Read a V1 Performance Target id from `get_strategy_tree`; call `save_strategy_structure_draft(plan_version_id=V2, deletes=[{"doctype":"Performance Target","name":"<V1 target>"}])`. Expected: refused (record not in this version). Actual by reading: the target is deleted from the Active V1 (it passes `_assert_deletable`; only a link to it would stop it). Variant: `targets=[{"name":"<V1 target>","indicator_id":"<V2 indicator>"}]` moves the target into V2. Test: extend `STR/tests/test_str_chg_001_phase4_contracts.py` (immutability test near line 480): Active V1 target T, Draft V2, call with `deletes` naming T, assert T still exists.
**Impact:** An Author can remove or relocate targets, indicators and leaf objectives of an Active (immutable) plan version; an Active plan's content is no longer guaranteed fixed for the Budget and Planning snapshots that reference it.
**Verification:** CONFIRMED — `STR/services/strategy_writes.py:397-402,416-421,438` overwrite `plan_version_id` on an existing record from the request, the guards at `strategy_domain_guards.py:194-206,267-276` test only the new (Draft) version, and no delete/trash hook exists on the Strategy doctypes.

### AUD-STR-003 — `save_strategy_plan_draft` edits any version and any plan identity regardless of status
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** STR §5.1 "Submitted for approval, Active and Superseded versions are read-only"; §12.2 "Identity is editable only in its first Draft before downstream use ... do not make immutable plan identity editable through an update"; STR-BR-006 · **Module(s):** kentender_strategy · **Sources:** trace-strategy F3; calibration check 2
**Evidence**
- `STR/services/strategy_writes.py:56-70` — `version_id = resolve_version_name(payload.get("plan_version_id")) or ...`; no `version.status == "Draft"` test, no `version.plan_id == plan_id` test; the only gate is `require_plan_version_capability(..., CAP_AUTHOR, version)` (`:70`).
- `STR/services/strategy_writes.py:72-79` — `plan.set(field, payload[field])` for `title, plan_role, parent_primary_plan_id, period_start, period_end`, `plan.save(ignore_permissions=True)`, then `version.set(field, ...)` for `effective_from, effective_to`, `version.save(ignore_permissions=True)`.
- `STR/services/strategy_domain_guards.py:89-135` — `validate_strategic_plan_version` locks only `plan_id`, `version_number`, `based_on_plan_version_id` once immutable (`:125-129`); `validate_strategic_plan` (`:48-83`) checks only role/parent/period order. Neither rejects a change to an Active or Submitted version's dates or the plan period.
- `STR/services/strategy_ui_contracts.py:764-766` — `identity_editable` / `is_editable_draft` (`:755`) exist only as capability flags returned to the browser.
**Rule:** STR §5.1 line "Submitted for approval, Active and Superseded versions are read-only"; §12.2; STR-BR-006 "Active content is immutable. A correction requires a successor version".
**Reproduction / failing test sketch:** (static; not run) As Author on the test site: `save_strategy_plan_draft(payload={"plan_id":P,"plan_version_id":"<Active V1>","effective_from":"<a date after today, within the plan period>"})` (an `effective_to` earlier than the version's `effective_from` is refused by `strategy_domain_guards.py:122`, so move the start date past today instead), then `resolve_strategy_context(as_of_date=<today>)` raises STRATEGY_CONTEXT_NOT_FOUND. Second case: `payload={"plan_id":P,"title":"Renamed","period_end":"2030-06-30"}` while a successor Draft exists rewrites the Active plan's title/period. Test: extend `STR/tests/test_str_chg_001_phase4_contracts.py` (draft save test near line 329) with an Active version id and assert `STRATEGY_INVALID_STATE`.
**Impact:** A Strategy Author can silently change the applicability dates or identity of the Active plan, which can make Planning and Budget lose their resolvable plan, with a "Draft saved" audit row and no successor/approval.
**Verification:** CORRECTED — code claim confirmed (`STR/services/strategy_writes.py:56-79` has no status or plan/version match check and `validate_strategic_plan_version` locks only `plan_id`/`version_number`/`based_on`); the first reproduction date was fixed because `effective_to` earlier than the version's `effective_from` is refused (`strategy_domain_guards.py:122`).

### AUD-STR-004 — Open-ended (null `effective_to`) version never resolves and escapes the overlap guard
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** STR §4.2 `effective_to` "May be empty only while it is the current Active version within the plan period"; STR-BR-004; STR-BR-017 · **Module(s):** kentender_strategy, Procurement Planning (consumer) · **Sources:** trace-strategy F5
**Evidence**
- `STR/services/strategy_consumer.py:38-41` — `_overlaps_range` returns `False` when `end` is empty; `:137-139` `_applicable` requires `_overlaps_range(version.effective_from, version.effective_to, range_start, range_end)`, so a version with empty `effective_to` is never returned by `resolve_strategy_context` (both `as_of_date` and `fiscal_year` modes).
- `STR/services/strategy_domain_guards.py:138-141` — `_overlaps` returns `False` when any bound is empty, so `assert_no_primary_overlap` (`:144-185`) never reports STRATEGY_OVERLAP against or for an open-ended Primary version.
- `STR/services/strategy_readiness.py:114-127` — approval requires only `effective_from`; nothing requires `effective_to`.
- `STR/public/js/strategy/screens/PlanWorkspaceScreen.vue:234-236,257` — the form permits a blank "Use until" and sends `effective_to: detailForm.effective_to || null`.
- `PROC/procurement_planning/services/strategy_gateway.py:26-33` — `_active_plan_version()` swallows the resolver error and returns `""`; `list_eligible_strategic_objectives` (`:36-41`) then returns `[]`.
**Rule:** STR §4.2 explicitly allows the empty value for the current Active version; STR-BR-017 requires the Active Primary to resolve; STR-BR-004 forbids overlapping Active Primary plans.
**Reproduction / failing test sketch:** (static; not run) 1. Author saves successor Draft V2 with Use until blank, submits; a different Approver approves (V1 becomes Superseded). 2. `resolve_strategy_context(as_of_date=<today>)` raises STRATEGY_CONTEXT_NOT_FOUND although V2 is the Active Primary; Planning's objective selector is empty. 3. Second case: a second Primary plan with empty `effective_to` and the same dates is approved while another Active Primary covers them: no STRATEGY_OVERLAP. Test: version `status=Active`, `effective_to=None` must resolve; a second null-ended Primary must raise STRATEGY_OVERLAP.
**Impact:** Following the documented optional-field rule, approving a successor with a blank end date leaves the site with no resolvable strategy, blocking Planning's Objective selection until a dated version is created.
**Verification:** CONFIRMED — `STR/services/strategy_consumer.py:38-40,139` and `strategy_domain_guards.py:138-141` treat an empty end as non-overlapping, approval does not require `effective_to` (`strategy_readiness.py:114-127`), and the form sends null (`PlanWorkspaceScreen.vue:257`).

### AUD-BUD-001 — Owner-scope and source-OU eligibility not enforced where money moves
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** BUD-CHG-001 v1.12 BUD-BR-007 "A line is eligible for an allocation only when ... its owner scope is Entity-wide or exactly matches the explicit `source_organisation_unit_id` of that allocation"; §9.1 (eligible-line listing) "Missing/unknown source OU fails even for Entity-wide candidates"; §13 `BUDGET_LINE_NOT_ELIGIBLE`, `BUDGET_SOURCE_OU_REQUIRED`; BUD18-AC-009, BUD18-AC-055 · **Module(s):** kentender_budget, kentender_procurement (callers) · **Sources:** trace-budget F-08
**Evidence**
- `BUD/services/budget_check_reserve_contracts.py:160-170` — `_normalise_rows` carries `source_organisation_unit` and `funding_source` through unchanged.
- `BUD/services/budget_check_reserve_contracts.py:174-203` — `_line_totals` compares only `row["funding_source"]` with the line's, and only when the row carries one (`:196`); there is no comparison of `source_organisation_unit` with the line version's `owner_org_unit` anywhere in `check_funding`/`reserve_funding` (`:206-296`, `:296-433`).
- `BUD/services/budget_line_contracts.py:396-398` — `if r.owner_org_unit and source_org_unit and r.owner_org_unit != source_org_unit: continue`: with no source OU every line is listed; `:671` hard-codes `"eligible": True`.
- `grep -rn SOURCE_OU_REQUIRED` over `kentender_*` returns nothing: the code is not produced.
- `PROC/procurement_requisitions/services/authorise.py:66-72` — the funding rows REQ sends carry `budget_line, plan_source_allocation, drawdown_line_id, source_organisation_unit, amount` and no `funding_source`, so the funding-source test (`:196`) is skipped for REQ calls too.
**Rule:** BUD-BR-007/008 and §9.1 quoted above; BUD18-AC-055 "an isolated HRMD-owned line rejects DHI even when the initiating user has broad authority".
**Reproduction / failing test sketch:** (static; not run) On the test site with a line owned by Digital Health: `check_funding(plan_item, plan_version, source_set_hash, [{"budget_line":<DHI line>,"source_organisation_unit":<HRMD OU>,"amount":"1000000.00","drawdown_line_id":"D1"}], correlation_id)` then `reserve_funding` with the token as a Head of Procurement Function: a reservation is created. Expected `BUDGET_LINE_NOT_ELIGIBLE`. Test: line owned by DHI, reserve with source OU HRMD or empty, expect typed refusal.
**Impact:** Funds ring-fenced to one department can be reserved against another department's requisition when the caller supplies a different or empty source OU (callers currently pass Planning facts, so the defence in depth the document requires is absent).
**Verification:** CONFIRMED — `BUD/services/budget_check_reserve_contracts.py:176-203,298-433` never compare `source_organisation_unit` with the line's `owner_org_unit`, the funding-source test is skipped when the row carries none, and REQ's rows (`authorise.py:64-72`) carry no funding source; reachable by the whitelisted `check_funding`/`reserve_funding` (`budget_api.py:220,247`) for Finance Confirmation Officer or HOPF.

### AUD-BUD-002 — Return/resubmit keeps no immutable submission-attempt snapshot
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** BUD v1.12 §6 "Return ... preserves an immutable submission-attempt snapshot, exact evidence attachment and decision. Re-editing the same Draft Version creates a new submission attempt; no prior submitted content or decision is overwritten."; §9.3; BUD18-AC-062; BUD19-AC-004; BUD19-AC-014 · **Module(s):** kentender_budget · **Sources:** trace-budget F-09
**Evidence**
- `BUD/services/budget_readiness_contracts.py:571-577` — resubmission sets `decided_by = None`, `decided_at = None`, `return_reason = ""` on the same Version row.
- `BUD/services/budget_contracts.py:998-999` — `if payload.get("approval_document"): version.approval_document = payload["approval_document"]` overwrites the attachment link.
- `BUD/services/budget_line_contracts.py:176-182` — Draft line versions are edited in place (`line_version.approved_amount = approved_amount; line_version.save(...)`).
- The only per-attempt record is a `Budget version submitted/returned` event with a `reason` (`budget_readiness_contracts.py:579-588,620-630`); no snapshot field or table exists (`grep -rni attempt BUD/services BUD/kentender_budget/doctype` shows no submission-attempt storage).
**Rule:** §6 and BUD18-AC-062 "Return/re-edit/resubmit preserves each immutable submitted attempt, attachment and decision".
**Reproduction / failing test sketch:** (static; not run) Officer submits V (document D1, line 100m); Approver returns; Officer replaces the document with D2, changes the line to 90m, resubmits. D1 and the 100m line content cannot be recovered from any Budget-owned record (only Frappe's generic `track_changes` Version rows, mutable by an administrator and not surfaced by `get_budget_version_history`, hold the earlier values). Test: after Return, edit, resubmit, `get_budget_version_history` must expose attempt 1 with its document and line values.
**Impact:** Approval evidence an auditor must see (what was first submitted and decided on) is overwritten by the next attempt.
**Verification:** CORRECTED — overwrite confirmed (`BUD/services/budget_readiness_contracts.py:574-576`, `budget_contracts.py:998-999`, `budget_line_contracts.py:181`) and no submission-attempt snapshot exists; but the Version and Line Version doctypes have `track_changes: 1`, so Frappe Version rows hold the earlier values (not an immutable, surfaced attempt snapshot, hence the finding stands at High, but "cannot be recovered from any Budget record" is overstated).

### AUD-NDS-001 — A Need whose accepted revision is a successor drops out of Planning's source list; Planning then deletes its Draft entry and never publishes the "Update required" position
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §7.2, §5.5, NDS-BR-013, NDS15-XD-001; PLN v1.29 §5.1.2 and §7.3 (position published "after every departmental-plan command and every Need acceptance") · **Module(s):** NDS, PLN · **Sources:** trace-needs C-08; sweep-handoffs F-5
**Evidence**
- `NDS/services/lifecycle.py:806-811` — `if superseded: event = publish_superseded(...) else: event = publish_accepted(doc, version)`; a successor acceptance writes only `DepartmentalNeedSuperseded.v1`.
- `NDS/services/events.py:253-290` — `current_accepted_events` returns only the `Departmental Need Event` row with `"event_type": EVENT_ACCEPTED` and `"need_revision": row.current_accepted_revision` (line 281). No such row exists for a successor, so the Need is skipped. Test `NDS/tests/test_departmental_needs_events.py:228` (`..._publishes_supersession_not_a_second_accepted`) pins that no second accepted event exists.
- `PLN/services/needs_intake.py:163-170` — `payload = by_need.pop(cstr(row.need), None); if payload is None: frappe.delete_doc("Departmental Plan Entry", row.name, force=True, ...)`: the Draft entry of the omitted Need is deleted (its funding specification goes with it). `refresh_draft_entries` is called from `PLN/services/dpp_read.py:174,445` and `dpp_lifecycle.py:220-310`.
- `PLN/services/needs_intake.py:279-316` — `need_positions` also builds positions from `current_accepted_sources`, so the same omission means no "Update required" (with carried revision) position can ever be produced for a successor-accepted Need, not merely a delayed one.
- `PLN/services/dpp_autostart.py:57` — `if cstr(doc.get("event_type")) != EVENT_ACCEPTED: return`; the superseded event triggers nothing.
**Rule:** NDS §7.2 "Accepted Need successor: Makes the old source stale for new/current Planning use … successor refreshes six facts"; PLN §5.1.2 position table "Update required (with the earlier revision it carries, if any)", which exists only for successor revisions; NDS15-XD-001 "every Need acceptance".
**Reproduction / failing test sketch:** (static; not run, test site) 1. Accept Need N revision 1 for department D; let the autostarted Draft DPP take N in. 2. Author `create_accepted_need_successor`, edit, submit; HoD `accept_need_revision` (successor). 3. Call `events.current_accepted_events(financial_year=FY, organisation_unit=D)`: N is absent. 4. Open the department's Draft plan (`dpp_read` refresh) or call `needs_intake.refresh_draft_entries(version)`: the Need-origin entry for N is deleted. 5. `get_need_planning_status(N)`: no `planning_intake`. Failing assertion: the payload for N has `accepted_version_id == <successor revision>`.
**Impact:** After any successor acceptance the department's Draft plan silently loses that Need (and any funding already entered), and an already-accepted departmental plan is never told to update, re-opening the late-accepted-Need dead end for revisions.
**Verification:** CONFIRMED — `lifecycle.py:808-811` publishes only `DepartmentalNeedSuperseded.v1` for a successor, `events.py:277-288` selects strictly `EVENT_ACCEPTED` rows keyed on the current revision (so the Need drops out of `needs_intake.current_accepted_sources`), and `needs_intake.py:~160-168` deletes any Draft entry whose Need is absent from that set; no other producer writes an accepted event for a successor.

### AUD-PLN-002 — Hold-then-withdraw-for-correction sequence dead-ends
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §5.2.3 (lines 459-460), §5.7 (line 812: "Material defect held; confirmed unpublished … Accounting Officer: Your turn — Request withdrawal for correction"), U13-UNPUBLISHED-DEFECT (line 1937) · **Module(s):** PLN · **Sources:** trace-planning F-25
**Evidence**
- `PLN/services/publication_pipeline.py:352-353` — `existing = _active_hold(version.name); if existing: return {"ok": True, "idempotent": True, "action": "held", "hold": existing}`: the existing hold is returned unchanged whatever its kind.
- `PLN/services/treasury.py:157-158` — `request_plan_withdrawal` calls `hold_plan_publication(... hold_kind="Withdrawal request" ...)` and then creates the statutory task using the returned hold name.
- `PLN/services/treasury.py:200` — `withdraw_approved_plan_for_correction` requires `hold_kind == "Withdrawal request"`, else `PLN_WITHDRAWAL_NOT_PERMITTED`.
**Rule:** PLN §5.2.3/§5.7: after a hold (system "Detected invalidity" or AO correction request) the AO's next step is to request withdrawal; the statutory authority then withdraws.
**Reproduction / failing test sketch:** (static; not run) AO calls `hold_plan_publication(hold_kind="Accounting Officer correction request")`; AO calls `request_plan_withdrawal` (reuses the existing hold, creates the task); statutory approver calls `withdraw_approved_plan_for_correction`: refused. Tests (`test_plan_publication.py:314,430`) exercise hold and withdrawal separately, never in sequence.
**Impact:** The documented recovery path for a defective, unpublished approved plan cannot be completed once any hold exists; the plan stays locked.
**Verification:** CONFIRMED — `publication_pipeline.py:352-353` returns the existing Active hold unchanged, `treasury.py:157-158` builds the withdrawal task on that hold, `treasury.py:200` demands `hold_kind == "Withdrawal request"`, and the only code that sets `hold_state` to Released is `treasury.py:217` (grep `hold_state`), so a pre-existing "Accounting Officer correction request"/"Detected invalidity" hold has no exit; the AO hold is also the `hold_plan_publication` API default (`api.py:466-469`).

### AUD-PLN-003 — A classification correction does not mark or block an affected Draft Plan Item
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §5.1.6.6, PLN21-AC-004 (line 2650: "an affected mutable Draft item becomes Source correction required and cannot continue until explicitly dissolved and re-formed") · **Module(s):** PLN · **Sources:** trace-planning F-09
**Evidence**
- `PLN/services/dpp_classification.py:307-337` — `source_correction_required(plan_item_id)` implements the classification-aware test; a repository search finds callers only in `PLN/tests/test_dpp_classification_correction.py:278,290,332`.
- `PLN/services/plan_read.py:285-296` — the function actually used by `plan_workbench.py:396`, `plan_governance.py:427`, `publication_pipeline.py:227` and `plan_read.py:378` compares only the DPP entry's source signature (`plan_read.py:196-203`, fields in `ENTRY_SOURCE_FIELDS` carry no requirement type or category), so a classification correction never trips it.
**Rule:** PLN §5.1.6.6 and PLN21-AC-004 as quoted.
**Reproduction / failing test sketch:** (static; not run) Accept a DPP entry typed Works; `form_plan_items`; `correct_accepted_requirement_classification` to Non-consulting services; then save the item, request funding, sign and submit: no `PLN_SOURCE_CORRECTION_REQUIRED`; the approved plan carries Works while the effective classification is Services. Failing test: after the correction, `plan_read.source_correction_required(entry)` or `plan_readiness(...)["blockers"]` must report the item.
**Impact:** A plan can be approved with a procurement category, method, schedule and reservation computed on a superseded classification.
**Verification:** CONFIRMED — `dpp_classification.py:~440-540` writes only the correction row and returns `draft_items` as information (no item flag/state change), `dpp_classification.source_correction_required` is called only from tests, and the production gates use `plan_read.source_correction_required` (`plan_read.py:285-296`) whose source signature (`:196-203`) excludes classification; no readiness check compares the item's requirement type with `effective_classification`.

### AUD-PLN-004 — An absent reservation rule is reported as "Required allocation met" and does not block submission
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §5.5.3.1 (line 755: "Block Sign and submit Annual Plan where a verified mandatory planning allocation is unmet or its calculation basis is missing"; line 761: "absence of verified mandatory configuration cannot be reported as success"), PLN18-AC-069, PLN18-AC-072 · **Module(s):** PLN, core (regulatory reference) · **Sources:** trace-planning F-01
**Evidence**
- `kentender_core/kentender_core/services/regulatory_reference.py:1216-1231` — `_single_in_force` returns `None` unless exactly one in-force Reservation rule exists; `_empty` sets `reservation.target_percent: None` (line 1118).
- `PLN/services/readiness.py:308` — `"mandatory": bool(target)`, so no rule gives `mandatory: False`.
- `PLN/services/plan_read.py:422` — `if stage == "submission" and items and share["mandatory"]:` is the only place the reservation blocker is raised; and `plan_read.py:806-807` — `if not share["mandatory"] or share["met"]: reservation_result = "Required allocation met"`.
**Rule:** PLN §5.5.3.1 and PLN18-AC-072 as quoted ("Missing mandatory method/schedule/reservation configuration or basis blocks the affected submission/action").
**Reproduction / failing test sketch:** (static; not run) Site with no in-force "Reservation rules" version for the FY (or two overlapping ones). Complete a plan, obtain Finance confirmation, `submit_consolidated_plan` as HOPF: no `PLN_RESERVATION_SHORTFALL` or `PLN_REFERENCE_UNAVAILABLE`; U07 shows "Required allocation met". `test_plan_workbench.py:928` covers an in-force but unverified rule only.
**Impact:** The statutory reserved-procurement check is silently skipped when its configuration is missing or ambiguous, and the screen reports success.
**Verification:** CONFIRMED — `regulatory_reference.py:1170,1216-1231` yields no reservation doc unless exactly one in-force rule exists, so `target_percent` is None and `readiness.py:308` gives `mandatory: False`; `plan_read.py:422` raises the blocker only when `mandatory` and `plan_read.py:806-807` renders "Required allocation met" for `not mandatory`; no other blocker covers an absent/ambiguous rule (PLN §5.5.3.1 line 761 and PLN18-AC-072 quoted correctly).

### AUD-REQ-001 — `record_handoff_consumption` endpoint lets a Procurement Officer or HOPF mark any authorised handoff consumed by a Tender that does not exist
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §9.2, §10.2 `RecordHandoffConsumption` · **Module(s):** Requisitions, Tenders · **Sources:** trace-requisition F-04
**Evidence**
- `REQ/api.py:271-280` — `@frappe.whitelist()` `record_handoff_consumption(handoff_name, tender, tender_version, template_key, template_version, idempotency_key)`; gate is only `any(authz.has_site_role(role) for role in TENDER_CALLER_ROLES)`.
- `REQ/services/requisition_roles.py:37` — `TENDER_CALLER_ROLES = (ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION)`.
- `REQ/services/handoff.py:105-137` — forwards `tender` straight into `doc.tender = cstr(tender)`, sets `consumed_at`, calls `records.release_slot(root)`; no lookup that the Tender exists or that the call is inside a Tender transaction.
- `REQ/doctype/authorised_requisition_handoff/authorised_requisition_handoff.json:76-77` — `tender` is a plain `Data` field, not a Link, so Frappe does not validate it either.
- `REQ/services/authorise.py:183-185` — `if handoff_doc.consumed_at: fail("REQ_HANDOFF_CONSUMED", ...)`: once set, revocation is permanently refused.
- `REQ/tests/test_requisitions_api_requests.py:101` — the suite itself consumes a handoff over HTTP with the fabricated id `TND-0001`.
- `TND/services/draft_commands.py:102-103` — a real `start_tender` on that handoff now hits `if handoff_doc.consumed_at: fail("TND_HANDOFF_CONFLICT")`.
**Rule:** REQ §9.2 "Tender Preparation consumes the exact handoff idempotently through REQ's `RecordHandoffConsumption` owner command within the same transaction as Draft Tender creation ... If TPR creation fails, consumption rolls back too." §10.2: "Owner-authorized TPR command ... atomic with Tender creation". HOPF is not a Tender starter (Tenders refuses HOPF at start, `TND/tests/test_lifecycle.py:126-131`).
**Reproduction / failing test sketch:** (static; not run) 1. On the test site authorise a requisition (`fx.authorise`). 2. As a user holding Procurement Officer (or Head of Procurement Function) POST `kentender_procurement.procurement_requisitions.api.record_handoff_consumption` with `handoff_name=<handoff>`, `tender="NOPE"`, `tender_version="x"`, `template_key="IT-EQUIPMENT-OPEN-V1"`, `template_version="1.1"`, a fresh `idempotency_key` -> expect refusal; today returns `action: consumed`. 3. As HOPF call `revoke_unconsumed_authorisation` -> `REQ_HANDOFF_CONSUMED`. 4. As an Officer call Tenders `start_tender(handoff)` -> `TND_HANDOFF_CONFLICT`.
**Impact:** One Procurement Officer can strand any authorised requisition: the Tender can never be started from that handoff, the HOPF can no longer revoke it, and the Budget reservation behind it cannot be released through the governed route. Reachable by any holder of the two roles.
**Verification:** CONFIRMED — `REQ/api.py:271-280` gates only on the two TENDER_CALLER_ROLES and `REQ/services/handoff.py:105-137` sets `doc.tender` from the request with no Tender lookup; no hook, controller or Link field intervenes, and `authorise.py:183-185` then blocks revocation.

### AUD-REQ-002 — HoD maker-checker is enforced only on the Awaiting branch; a Draft can be certified by an Author who later became HoD (and "preparing directly" is never checked)
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §7.3 bullet 1, §7.1 (Draft / Submit to Procurement), REQ19-AC-045 · **Module(s):** Requisitions · **Sources:** trace-requisition F-02; sweep-sod F9
**Evidence**
- `REQ/services/lifecycle.py:261-262` — `if cstr(version.prepared_by) == actor and cstr(version.prepared_capacity) != ROLE_HEAD_OF_USER_DEPARTMENT: fail("REQ_SOD_BLOCKED")`, inside the `if root.current_state == "Awaiting Department Approval":` branch that starts at line 253.
- `REQ/services/lifecycle.py:267-270` — `elif root.current_state == "Draft": ... lock(root, version, package_version, target_status="Submitted to Procurement")`: no check on `prepared_by` or `prepared_capacity`; the only gate is `_lead_hod(root, actor)` at line 247.
- `REQ/services/draft_commands.py:56-65,127,177` — `prepared_capacity` is chosen by trying HoD first across *any* contributing unit, then Author, and is stored; it records the capacity the actor happened to hold, not the capacity exercised in the lead unit.
- `REQ/tests/test_home_provider.py:258-270` — builds exactly the Author-turned-HoD case but only asserts `assertRaises(Exception)` on the Awaiting path.
**Rule:** §7.3 "A Departmental Author cannot complete the Head of User Department decision on the same Version unless the actor is independently assigned the Head of User Department role and prepared the Requisition directly in that capacity." §7.1 row "Draft | Submit to Procurement | Head of User Department preparing directly". REQ19-AC-045 "Dual-role actors exercise exact current capacity with no self-authorisation."
**Reproduction / failing test sketch:** (static; not run) 1. A holds Departmental Author in the lead OU only; A prepares and completes a Draft (`prepared_capacity = "Departmental Author"`). 2. Grant A Head of User Department in the lead OU (`administration.grant(...)`, as `test_home_provider.py:262`). 3. As A call `submit_requisition_to_procurement(requisition, expected_record_version, key)` while the root is still `Draft` -> succeeds, `submitted_by = A`, a Procurement task is created, no departmental-approval task ever existed. 4. The same call after `send_for_department_approval` raises `REQ_SOD_BLOCKED`. Expected: step 3 raises `REQ_SOD_BLOCKED`. Also: a different lead HoD can certify an Author's Draft directly, skipping the departmental task, because "preparing directly" is never tested.
**Impact:** An Author who is also (or becomes) HoD certifies their own work for the whole department, defeating the first maker-checker stage; the HOPF authorisation (a different person, `authorise.py:104`) still stands, which is why this is High rather than Critical.
**Verification:** CORRECTED — core case holds (`REQ/services/lifecycle.py:253-270`: the `prepared_by`/`prepared_capacity` check exists only in the Awaiting branch; the Draft branch only calls `lock`). Secondary claim (a different lead HoD certifying an Author's Draft) is narrower than written: `REQ/services/read.py:473-476` deliberately offers Submit to Procurement on a Draft to any lead HoD who is not a lead Author, so that is a spec-ambiguity (§7.1 "preparing directly") rather than a pure code bug; severity High kept for the Author-turned-HoD case.

### AUD-TND-001 — An addendum can become effective (deadline rewritten, definition activated) after the submission period has closed
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 §4.8, §5.1 (Close submission period), §5.6 · **Module(s):** Tenders, Bid Submission · **Sources:** trace-tenders F-03
**Evidence**
- `TND/services/submission_close.py:57-93` — `close_tender_submission_period` closes a `Published — open` Tender and freezes `effective_submission_deadline` into the handoff; it does not look at addenda in `Awaiting publication confirmation`.
- `TND/services/channel_confirmation.py:160-161` — `confirm_channel` refuses only `if root.overall_status == "Cancelled" and subject_type != SUBJECT_CANCELLATION`; there is no `Published — open` guard on addendum confirmations.
- `TND/services/addenda.py:452-465` — `_all_channels_confirmed` sets the addendum `Issued`, calls `bid_definition.activate(root, doc.successor_bid_definition, at=issued_at)` (line 461) and `envelope.bump(root, submission_deadline=doc.revised_submission_deadline)` (lines 463-465).
**Rule:** §4.8: the addendum, its deadline and successor definition become effective "only when the HOPF confirms every required channel"; §5.1 "Close submission period ... Sets Submission period ended and emits immutable downstream contract"; §5.6 "BDS cannot see an awaiting-confirmation definition as current."
**Reproduction / failing test sketch:** (static; not run) In `TND/tests/test_open_period.py` style: 1. Issue a deadline-extending addendum with channels outstanding. 2. Advance `frappe.flags.kt_tenders_clock` past the original deadline; `submission_close.close_due_submission_periods()` -> Tender `Submission period ended`, handoff frozen. 3. HOPF confirms the last addendum channel -> `Tender.submission_deadline` moves later and a new Effective definition is activated on a closed Tender. Expected: refusal or a defined outcome; today no `TND_*` error.
**Impact:** The closed Tender's deadline and effective definition diverge from the frozen submission handoff that Bid Submission and Bid Opening already consumed, a legally material inconsistency on a live procurement.
**Verification:** CONFIRMED — `TND/services/addenda.py:452-465` activates the definition and rewrites `submission_deadline` with no tender-status guard, `TND/services/channel_confirmation.py:160-161` guards only Cancelled, and `submission_close.py:57-93` never consults awaiting addenda.

### AUD-TND-002 — A late final channel confirmation strands the Tender with no governed exit
**Severity:** High · **Classification:** SPEC GAP · **Doc:** TPR-CHG-001 v0.17 §5.5 item 6, §7 · **Module(s):** Tenders · **Sources:** trace-tenders F-04
**Evidence**
- `TND/services/publication.py:156-159` — `confirm_tender_published` fails `TND_PUBLICATION_PERIOD_INVALID` when `published_at` plus the minimum period is after the deadline.
- `TND/services/publication.py:208-211` — `withdraw_publication_authorisation` refuses once any channel is Confirmed (`TND_PUBLICATION_WITHDRAWAL_BLOCKED`).
- `TND/services/lifecycle.py:290-291` — `reopen_approved_tender` refuses once `root.publication` is set (`TND_PUBLICATION_STARTED`).
- `TND/services/cancellation.py:52-56` — `_require_open` allows cancellation only from `Published — open`.
- `TND/tests/test_publication.py:438-456` — the test's own next step is to re-submit the same final channel with an earlier default `available_at` to get past the refusal.
**Rule:** §5.5(6) "If the applicable minimum period would be breached, the Tender cannot become Published until a lawful revised deadline is issued in the same immutable publication package." No §7 command issues such a revised deadline.
**Decision the owner must make:** name the command that issues a revised deadline inside the same publication package (or a governed withdrawal) for the case where three channels are already confirmed.
**Reproduction / failing test sketch:** (static; not run) Authorise publication; confirm three channels; confirm the fourth with `available_at` later than deadline minus minimum days -> `TND_PUBLICATION_PERIOD_INVALID`; `withdraw_publication_authorisation` -> `TND_PUBLICATION_WITHDRAWAL_BLOCKED`; `reopen_approved_tender` -> `TND_PUBLICATION_STARTED`; `cancel_tender` -> `TND_STALE_VERSION`.
**Impact:** The Tender can only progress if the HOPF attests a different (earlier) availability time than the real one, which invites false attestation; otherwise it is stuck in "Publication authorised".
**Verification:** CONFIRMED — the final confirmation's failure rolls back (test `TND/tests/test_publication.py:438-456` leaves the row Awaiting), and every exit is closed: `publication.py:208-211` withdraw, `lifecycle.py:290-291` reopen, `cancellation.py:52-56` cancel, `correction.py:52-53` request-correction (`root.publication` set) and `publication.py:250` return_approved_tender.

### AUD-EVL-001 — A conflicted evaluator can clear their own declared conflict and regain bid access
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §3 (roster terminology, line 67/69); EVL-A06 · **Module(s):** Evaluation · **Sources:** trace-evaluation F-1 (rows 20, 137, 198, 203); sweep-sod F7
**Evidence**
- `P/bid_evaluation/services/declaration.py:51` — `if current and current.choice == choice and choice == "No conflict to declare":` (early return only when the choice repeats; a conflict followed by "No conflict" does not hit it)
- `P/bid_evaluation/services/declaration.py:55` — `prior.status = "Superseded"` then a new Current declaration row is inserted (lines 58-63)
- `P/bid_evaluation/services/roster.py:69` — `conflict = bool(decl and decl.choice == "Declare a conflict")` is derived only from the Current declaration; `roster.py:78` returns `eligible: member and not reasons`, so the new "No conflict" row makes the member eligible again
- `P/bid_evaluation/services/declaration.py:65` — only the "Declare a conflict" branch calls `lifecycle.roster_changed` and notifies the Accounting Officer; the retraction branch (line 73-74 `member_became_eligible`) involves no AO action
- `P/bid_evaluation/services/my_work_provider.py:67-71` and `next_steps.py:120-124` derive the AO's "Resolve committee appointment" task from the same live status, so the task silently disappears
**Rule:** EVL §3 line 67: "A declared conflict stops that person's bid access immediately and creates the Accounting Officer's task"; line 69: an eligible member has "no unresolved conflict"; line 57: the Accounting Officer "deal[s] with declared conflicts". The AO's reasoned replacement is the only resolution route the document names; it does not provide for self-retraction.
**Reproduction / failing test sketch:** (static; not run) 1. On the test site appoint three members (M1..M3) to an Evaluation Case in Reviewing and have all declare "No conflict". 2. As M1 call `declare_interest(choice="Declare a conflict", conflict_description="x", confidentiality_accepted=True, idempotency_key=k1)`; `roster.status(case, M1)["conflict"]` is True, `reads.bid(..., user=M1)` is Not found, AO has "Resolve committee appointment". 3. As M1 call `declare_interest(choice="No conflict to declare", confidentiality_accepted=True, idempotency_key=k2)`. Expected: refused (AO-only resolution). Predicted: `eligible` True, `reads.bid` returns bid content, AO task gone, no AO action recorded. Also works while the report is Signing (the earlier conflict withdrew signing; the reversal restores M1 as a required signer).
**Impact:** The person whose interest is in question can lift their own recusal and read sealed bids, defeating the Accounting Officer's conflict control without a trace beyond a superseded declaration row.
**Verification:** CONFIRMED — `declaration.py:51-63` only short-circuits a repeated "No conflict" and otherwise supersedes the Current row, `roster.py:69,78` recomputes eligibility from the Current row alone, and no guard, doctype controller or test blocks the retraction (`api.declare_interest` is gated only by roster membership).

### AUD-EVL-002 — A committee-recorded qualified report on an unresolved requirement or price discrepancy can never be frozen for signing
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §4.4 (line 114), §5.5 (lines 160), EVL-A09/A17 · **Module(s):** Evaluation · **Sources:** trace-evaluation F-2 (rows 111, 112, 206, 214)
**Evidence**
- `P/bid_evaluation/services/conclusion.py:104` — `kind = "Qualified report" if result == "Needs review" else "Resolved finding"`
- `P/bid_evaluation/services/aggregate.py:71` — `human_record` feeds `conclusion` only for kinds `("Resolved finding", "Reply disposition", "Verification outcome")`; a "Qualified report" conclusion only sets the `qualified` flag (`aggregate.py:76-78`, `:112`), so the requirement stays Needs review
- `P/bid_evaluation/services/comparison.py:75-76` — a Needs-review bid leaves `pending` non-empty, so no `outcome` is produced (`:78` `if not pending:`)
- `P/bid_evaluation/services/report.py:153` — `return {"outcome": None, ..., "provisional": True}` for that case; the `QUALIFIED` outcome (`report.py:144-145`) is reachable only inside `if table["outcome"] == "Recommendation":` (`:140`), i.e. when nothing is pending
- `P/bid_evaluation/services/signing.py:70-71` — `if built["recommendation"]["provisional"]: issues.append({"item": "The comparison is provisional", ...})` makes `readiness` fail with `EVL_REPORT_INCOMPLETE`; the preceding loop (`signing.py:59`) already exempts `row["qualified"]`, showing the qualified path was intended to freeze
**Rule:** EVL §5.5 (line 160): freeze is allowed "once every required result is either resolved or explicitly included in a committee-recorded qualified outcome … A qualified report is a completed account of the issue, not a successful award recommendation"; §4.4 (line 114): "Without one, record the unresolved discrepancy and deliver an appropriately qualified report with no unsupported recommendation."
**Reproduction / failing test sketch:** (static; not run) 1. Reviewing world with one bid; leave requirement "Service location" at Needs review. 2. Full roster present in a discussion; chair calls `record_conclusion(bid=B, requirement_key=..., result="Needs review", qualified=True, reason="cannot establish the address")` (as `P/bid_evaluation/tests/test_evl_discussion.py:140`). 3. Resolve every other requirement; secretary calls `signing.send_for_signing(...)`. Expected: frozen version with outcome "Qualified report". Predicted: `EVL_REPORT_INCOMPLETE` listing "The comparison is provisional". Same for a price discrepancy (AUD-EVL-003 setup without a member finding). Add to `TestSendAndSign`: assert `report.build(doc)["recommendation"]["outcome"] == "Qualified report"` and case state Signing. Only the case-wide "No agreed recommendation" conclusion (`report.py:137`) reaches signing, which is a different outcome. No test freezes a qualified report (grep "qualified" in `P/bid_evaluation/tests/` finds only `test_evl_discussion.py:53-55,140-141`).
**Impact:** The legally required fallback for an unresolved requirement or arithmetic discrepancy cannot be produced, so the committee can only force a signable report by recording "No agreed recommendation" or by (wrongly) resolving the requirement; the evaluation can dead-end.
**Verification:** CONFIRMED — traced `conclusion.py:104` -> `aggregate.py:71-78,99` (requirement stays Needs review, responsiveness `REVIEW` at `aggregate.py:~143`) -> `comparison.py:75-78` (pending, no outcome) -> `report.py:153` (`provisional: True`) -> `signing.py:70-71` (`EVL_REPORT_INCOMPLETE`); `report.py:144-145` QUALIFIED is reachable only when nothing is pending.

### AUD-EVL-003 — One member's evidence finding resolves a price-arithmetic discrepancy (or a missing rule) and the bid is ranked on the submitted total
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §4.4 (line 114), §4.1 · **Module(s):** Evaluation · **Sources:** trace-evaluation F-6 (rows 33, 54, 206)
**Evidence**
- `P/bid_evaluation/services/rules.py:269` — `"result": REVIEW if problems else MEETS` (a submitted total that differs from the exact-decimal calculation is Needs review for `RR-PRICE-GOODS`, `checks.py:29` / `:118-121`)
- `P/bid_evaluation/services/findings.py:93-104` — `record_evidence_finding` requires only `require_member` and state Reviewing; `contrary` is true only when the automatic result is "Does not meet" (`:104`); a "Meets" finding on a Needs-review requirement creates no discussion item (`:108`)
- `P/bid_evaluation/services/aggregate.py:99` — `elif finding is not None and finding.result in (MEETS, FAILS):` makes the requirement result the member's finding (basis "Member evidence finding")
- `P/bid_evaluation/services/comparison.py:63-64` — `elif res["responsiveness"] == "Responsive" and row["financial"] == aggregate.MEETS: row["evaluated_total"] = cstr(bid.submitted_total)`; the discrepant sum is ranked and `report.build` recommends it
- The same path resolves a requirement whose rule is unavailable (`P/bid_evaluation/services/rules.py:124-126` returns Needs review "unavailable"), because the finding/conclusion overrides it
**Rule:** EVL §4.4 (line 114): "Arithmetic inconsistencies remain visible. Where the issued tender supplies a lawful disposition, apply and explain it without changing the submitted sum. Without one, record the unresolved discrepancy and deliver an appropriately qualified report with no unsupported recommendation. A committee explanation cannot substitute for a missing legal or published basis."
**Reproduction / failing test sketch:** (static; not run) 1. Build the discrepant-total world of `P/bid_evaluation/tests/test_evl_rules.py:113` (package total differs from the calculation). 2. As an eligible member call `record_evidence_finding(bid=B, requirement_key="RR-PRICE-GOODS", result="Meets", reason="ok", idempotency_key=k)`. 3. `comparison.compare(case)` ranks B with `evaluated_total == submitted_total` and `report.build` recommends B with no qualification. Test sketch: assert step 2 is refused or the outcome remains unresolved/qualified.
**Impact:** A single individual member, with no committee conclusion, can make a bid with an arithmetic discrepancy the recommended bidder at the wrong total, contrary to the document's express prohibition.
**Verification:** CONFIRMED — `findings.py:93-108` accepts a "Meets" finding on any requirement (price requirement `RR-PRICE-GOODS` is a normal requirement, `checks.py:29,118`), `aggregate.py:99` adopts it unless the automatic result is "Does not meet", and `comparison.py:63-64` then ranks the submitted total; no guard excludes calculation-type requirements.

### AUD-AWD-001 — No segregation of duties anywhere in the evaluation → opinion → award-decision chain
**Severity:** High · **Classification:** SPEC GAP · **Doc:** AWD-CHG-001 v0_5 §6 (line 275); AUTH-ADR-001 v1_11 §5.8 (line 320); EVL-CHG-001 v0_5 §3 · **Module(s):** Award, Evaluation, Core (registry) · **Sources:** trace-award F1 (row 129, calibration 2); sweep-sod F8; trace-evaluation F-5 (rows 224, 225; D-5)
**Evidence**
- `P/award/services/guards.py:29-42` — `require`/`require_hop`/`require_ao` check only that the user holds the role (`people.holds`)
- `P/award/services/decision.py:110` — `RecordAwardDecision` gates on `guards.require_ao(user)` only; `P/award/services/opinion.py:41,81,141` gate opinion save/sign/return on `guards.require_hop(user)` only; grep `segreg|sod_tags|conflict` in `P/award/services/*.py` finds nothing relevant
- `P/award/services/people.py:37` — `holds` calls `authorise_record(user, business_role, purpose=PURPOSE_COMMAND)` with no record, action or SoD input
- `P/bid_evaluation/services/appointment.py:43-53` — `_ineligibility` excludes only non-internal users, the same-tender opening independent member and declared-conflict persons; the Accounting Officer or Head of Procurement may be appointed chair/member, and Evaluation's signer list is carried to Award (`P/bid_evaluation/services/award_seam.py:111-112`, `signatures.members`) but never compared with the deciding AO
- `kentender_core/kentender_core/services/business_role_registry.py:147,191` — the registry's `sod_tags` for Accounting Officer (`plan_adoption`, `publication_authorisation`, `tender_cancellation`) and Head of Procurement Function (`requisition_authorisation`, `tender_approval`, …) contain no evaluation, opinion or award-decision tag
**Rule:** AUTH §5.8: "Holding two roles is not a violation; performing incompatible decisions in the same evidence chain is. Segregation is evaluated against actual actions using the registry's `sod_tags` and the owning module's rules." AWD §6: "Use AUTH's existing enforcement; add no per-tender permission grants"; "Evaluation members … acquire no Award decision power". Neither Award nor Evaluation states the incompatible-action rule, so the code has nothing to enforce.
**Reproduction / failing test sketch:** (static; not run) 1. Give one user both the Accounting Officer and Head of Procurement Function assignments. 2. As that user appoint self as evaluation chair, sign the report, then `award.api.sign_opinion` (HOP) and `award.api.record_decision(outcome="Award")` (AO): each is accepted under one identity. Failing test: after HOP+AO on one user, `decision.record` should raise `AUTH_SEGREGATION_BLOCKED`; and a user present in `snapshot["signatures"]["members"]` should be refused as deciding AO.
**Impact:** One person can evaluate, recommend, sign the professional opinion and decide the award. **Owner decision needed:** define the incompatible actions (e.g. report signer ≠ opinion signer ≠ deciding AO; AO/HoP not appointable as members) and add the `sod_tags`; the code then needs the check.
**Verification:** CONFIRMED — `guards.py:29-42` + `people.py:37-39` (`authorise_record(..., purpose=PURPOSE_COMMAND)`, no SoD input) are the only gates on `decision.py:110` and `opinion.py:41,81,141`; `authorization_native.py:~85` states segregation "stays a domain rule" and neither Award nor Evaluation (grep segreg/sod) implements one; neither AWD v0_5 nor EVL v0_5 names an incompatible-action rule, hence SPEC GAP.

### AUD-AWD-002 — Funding is never re-read from Budget and an unavailable funding (or validity) read permits a positive award
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §3 (Budget row), §5.1 (line 93), §5.5 (line 141), AWD-IF-07 (line 528) · **Module(s):** Award, Evaluation, Budget · **Sources:** trace-award F2 (rows 31, 43, 90, 222, 223); sweep-money F11
**Evidence**
- `P/award/services/checks.py:77-80` — `f = state.snapshot(state.current_report(doc)).get("funding") or {}` → `restricted = bool(qualification) or short > 0`; Award has no Budget call (grep `funding` in `P/award/services/` finds only snapshot readers)
- `P/bid_evaluation/services/award_seam.py:115` — the snapshot's funding is `recommendation.get("funding") or {}` frozen at report-signing time
- `P/bid_evaluation/services/funding.py:35-52` — `None` when no reservations exist or the Budget read raises, so the report's funding fact is absent and Award's `funding()` returns `restricted: False` (see AUD-EVL-014)
- `P/award/services/decision.py:42-52` — `positive_guards` checks holds, recommendation and `v["expired"]` only; `P/award/services/checks.py:42-47` returns `{"known": False, "expired": False}` for an unreadable validity, so an unknown validity does not block the decision (it blocks only at delivery, `P/award/services/eligibility.py:47-49`)
- Nothing re-checks funding at decision, issue (`P/award/services/notices.py:95-109` `_stop_reasons`) or delivery (`eligibility.py:50-52`)
**Rule:** AWD §5.1: "Read-only checks cover … validity, funding … Distinguish an established restriction from an unavailable check. Neither permits an unsupported positive decision."; §5.5: conditions are rechecked "at decision, actual issue and Contracting delivery"; AWD-IF-07: "read-only current funding response with explicit unknown/failure result".
**Reproduction / failing test sketch:** (static; not run) (a) Make Budget's `get_funding_lineage` raise at evaluation time; deliver the report with empty funding; AO `record_decision(outcome="Award")` succeeds with clean `positive_guards`. (b) Report-time funding sufficient; consume the reservation before the decision days later: Award still passes. Failing test: with `funding == {}` and Budget unavailable assert `decision.positive_guards` returns a funding-unknown reason.
**Impact:** An award can be decided, notified and sent to Contracting on funding that was never verified or has since been withdrawn.
**Verification:** CONFIRMED — `award/services/checks.py:~77-80` reads funding only from the frozen report snapshot and `decision.py:42-52` `positive_guards` has no funding term; `checks.py:42-47` returns `known: False, expired: False` for an unreadable validity (only a separately synced Status-unavailable issue could still block the decision, and `decision.record` does not run sync), and AWD §5.1/§3 Budget row/AWD-IF-07 require the Budget read.


## 4.3 Medium

### AUD-XC-013 — System Manager / Administrator hold write/delete on decision, evidence, handoff, reservation and assignment records that the documents make immutable
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AUTH-ADR-001 v1_11 §8 (line 361) and §15 (line 828); REQ v1_14 invariant 12 (line 650), line 591 and line 1530; PLN v1_29 line 147; TPR v0_17 §12.3 (line 1621); BUD v1_12 lines 335, 360, 1245 · **Module(s):** Requisitions, Planning, Tenders, Budget, Core (assignments) · **Sources:** sweep-audit F7; sweep-authz F-09; sweep-state F11; trace-requisition F-01; trace-planning F-11; sweep-sod F15; (Audit Event itself is AUD-XC-010)
**Evidence**
- DocPerm for System Manager (`rwcd`, Administrator likewise where listed): `kentender_procurement/kentender_procurement/procurement_requisitions/doctype/requisition_decision/requisition_decision.json:144`, `authorised_requisition_handoff.json:136`, `requisition_version.json:244`, `procurement_requisition.json:245`, `requisition_task.json:115`; `.../tenders/doctype/tender/tender.json:295`, `tender_task.json:144`; `kentender_core/kentender_core/kentender_core/doctype/user_responsibility_assignment/user_responsibility_assignment.json:160,168`. `rwc`: `.../procurement_planning/doctype/plan_governance_decision.json:136,142`, `approved_plan_snapshot.json:96,102`, `plan_finance_decision.json:109,115`, `departmental_plan_validation_decision.json:127,133`, `plan_preparation_signature.json:96,102`, `treasury_submission_evidence.json:142,148`; `kentender_budget/kentender_budget/kentender_budget/doctype/funding_reservation/funding_reservation.json:206`, `procurement_commitment.json:103`.
- Controllers are empty: `requisition_decision.py` (`class RequisitionDecision(Document): pass`), `plan_governance_decision.py`, `funding_reservation.py`, `procurement_commitment.py`, `tender.py` (`class Tender(Document): pass`), and `approved_plan_snapshot.py` (docstring only). Requisition services set `flags.kt_lifecycle` but no Requisition controller reads it, whereas the Tender family does (`tenders/doctype/tender_version/tender_version.py:10-24`: `validate` refuses a non-Draft write without `flags.kt_lifecycle`, `on_trash` refuses delete).
- Hooks answer True for technical users on every `ptype`: `kentender_core/kentender_core/services/authorization.py:483-484`; `requisition_authorization.py:353-354`; `tender_authorization.py:288-289`.
- `user_responsibility_assignment.py:54-72` — `_validate_immutable_once_in_force` locks the identity fields but has no `on_trash`, and `status` is not an identity field; Link-field search finds no field that targets the doctype, so a delete is not blocked.
**Rule:** AUTH §15 "Assignment records are never physically deleted. Revocation is a state change"; AUTH §8 "Setup authority is not business authority" and technical **read** only; REQ invariant 12 "Submitted and authorised Versions, rows, files and digests are immutable"; REQ line 591 "Administrator or System Manager access grants no business decision"; PLN line 147 "Decisions, events and published files are append-only"; TPR §12.3 rule 1; BUD line 360 "no Budget business action". Part of this is spec-aligned for setup (AUTH §8 lets System setup create assignments); delete and edit of decided records is not.
**Reproduction / failing test sketch:** static; not run. As System Manager with no assignment: `PUT /api/resource/Plan Governance Decision/<n>` `{"decision":"Returned"}`; `PUT /api/resource/Authorised Requisition Handoff/<n>` with a changed `payload_json` (its stored digest then no longer matches); `PUT /api/resource/Funding Reservation/<n>` `{"remaining_amount": 0}`; `DELETE /api/resource/User Responsibility Assignment/<n>` for an Active assignment. Requisition Decision and Authorised Requisition Handoff deletes are blocked while a Requisition Task or Procurement Requisition links to them. Expected: refusal. Pytest: `frappe.set_user(sm); d = frappe.get_doc("Plan Governance Decision", n); d.decision = "Returned"; d.save()` must raise.
**Impact:** A technical user can rewrite or delete recorded decisions, handoffs, reservations and responsibility assignments with no business assignment and, for money records, with no ledger event. Audit risk rather than an anonymous exploit, because the actor is an administrator.

### AUD-XC-014 — Need Planning Intake Projection is writable and deletable by six roles including Auditor
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1_16 §8.2 (line 637) "written only by `project_need_planning_intake`"; NDS-BR-019 · **Module(s):** Departmental Needs, Planning · **Sources:** sweep-authz F-07; sweep-state F8; sweep-audit F11; trace-needs C-06 (projection part)
**Evidence**
- `kentender_procurement/kentender_procurement/departmental_needs/doctype/need_planning_intake_projection/need_planning_intake_projection.json:108,120,132,144,156,168` — System Manager, Administrator, Departmental Author, Head of User Department, Procurement Planner and Auditor each hold `read/write/create/delete`.
- `.../need_planning_intake_projection.py:1-13` docstring "a read-only projection supplied by Planning… users cannot edit it"; `validate` (:26-38) checks revision ownership only. The two sibling projections `need_planning_usage_projection` and `need_planning_disposition_projection` grant business roles no write.
**Rule:** NDS §8.2 (line 637), NDS-BR-017 (line 436).
**Reproduction / failing test sketch:** static; not run. As an Auditor: `DELETE /api/resource/Need Planning Intake Projection/<n>` or `PUT … {"position":"No update needed"}`. Expected: refusal; read result: the Need detail's Planning position changes or disappears, hiding "Create update" for a late-accepted Need.
**Impact:** An oversight role with no business mutation right can change what Planning position the Need screen shows.

### AUD-XC-015 — Need Revision / Withdrawal Request have no scope hook; Planner and Author reads are wider than NDS section 6
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1_16 §6 table (lines 478-481) and NDS-BR-019 (line 438); AUTH-ADR-001 v1_11 §5.3 (lines 257-266) · **Module(s):** Departmental Needs · **Sources:** sweep-authz F-06 (read half), F-08; trace-needs C-06 (read half), C-07 (hook half)
**Evidence**
- `kentender_procurement/kentender_procurement/hooks.py:370-384` — `kentender_scope_map` registers only `Departmental Need` and `Departmental Need Review Task` for Needs; the comment states Revision, Decision and Withdrawal Request have "no direct route" and rely on the service layer. Their DocPerm still grants read to Departmental Author, Head of User Department, Procurement Planner and Auditor (`departmental_need_revision.json:151-170`, `need_withdrawal_request.json:125-142`), and no `has_permission` or `permission_query_conditions` entry exists for them.
- `kentender_core/kentender_core/services/authorization.py:400-419,445-447` — `_relevant_business_roles` is derived from the doctype's DocPerm read roles, so for `Departmental Need` it includes Procurement Planner (Site-wide); `scope_condition` returns `""` (unrestricted) for a Site-wide row, and `has_permission` returns True at `:495-497`.
- Service predicate for comparison: `departmental_needs/services/permissions.py:100-135` — `can_view` limits the Planner to `current_state == STATE_ACCEPTED` and the Author to own Needs.
**Rule:** NDS §6 "Departmental Author — View own Needs"; "Procurement Planner — Read current accepted Need revisions"; NDS-BR-019 "Counts, rows, direct routes, services and exports use the same server-side scope predicate"; AUTH §5.3 "Registering only the query hook leaves a direct-route hole" and §9.1 one predicate.
**Reproduction / failing test sketch:** static; not run. (1) As a Departmental Author of department A: `GET /api/resource/Departmental Need Revision?fields=["name","title","description","departmental_need"]` returns revisions of department B's Needs. (2) As a Procurement Planner: `GET /api/resource/Departmental Need?filters=[["current_state","in",["Draft","Returned"]]]` returns Draft and Returned Needs of every department. (3) As an Author: `GET /api/resource/Departmental Need` lists colleagues' Needs in the same OU subtree. Pytest: `frappe.get_list("Departmental Need", filters={"current_state":"Draft"}, user=planner)` must be `[]`.
**Impact:** Draft Need content of other departments is readable through the standard REST routes; this is the calibration "intake scope" class reappearing one layer below the fixed workspace.

### AUD-XC-016 — Planning projection endpoints are callable by a human Planner with caller-chosen actor and ordering time
**Severity:** Medium · **Classification:** SPEC DEFECT (NDS §8.2/§7.5 allow an "administrative principal", AUTH §8 says technical roles decide nothing) plus CODE DEFECT (client `actor`) · **Doc:** NDS v1_16 §7.4 (`actor`, line 563), §7.5 (lines 571-573), §8.2 (line 637); AUTH-ADR-001 v1_11 §8 · **Module(s):** Departmental Needs, Planning · **Sources:** sweep-authz F-22; sweep-state F9; trace-needs C-09
**Evidence**
- `kentender_procurement/kentender_procurement/departmental_needs/api.py:98-103` whitelists `project_planning_usage`, `project_planning_disposition`, `project_planning_intake` directly.
- `kentender_procurement/kentender_procurement/departmental_needs/services/usage.py:177-183,325-327,453-454` — gate is `in_scope(principal, business_role=ROLE_PROCUREMENT_PLANNER, organisation_unit="") or is_administrative(principal)`; `permissions.py:83-97` `in_scope` returns True for technical users. `usage.py:361` `"actor": cstr(actor) or principal` with `actor` an endpoint argument (:317).
- `usage.py:206-208` — ordering is `str(occurred) < str(existing["source_event_time"])` with `occurred = source_event_time or now_datetime()` taken from the request, so a far-future time pins the row and discards later genuine events.
- `usage.py:239-243` `is_actively_included` reads `usage` to decide the withdrawal block (NDS-BR-016).
**Rule:** NDS §7.5 line 571 "Registered Planning producer only; validate schema, immutable payload…"; §7.4 line 563 `actor` "Trusted actor identity… Browser-supplied author identity is not trusted"; AUTH §8 "Setup authority is not business authority" (the NDS "administrative principal" wording contradicts it).
**Reproduction / failing test sketch:** static; not run. As a Procurement Planner (no Planning producer identity): `POST /api/method/kentender_procurement.departmental_needs.api.project_need_planning_usage` `departmental_need=<N>&accepted_revision=<R>&usage=Not included&source_event_id=e1&source_event_time=2099-01-01 00:00:00` for a Need an Active Plan includes; then a Head of User Department approves a withdrawal of N. Expected: refusal; read result: `check_withdrawal_dependency` sees "Not included". Same call with `user=Administrator` passes via `is_administrative`.
**Impact:** A human Planner (or, until AUD-XC-001 is fixed, anyone) can falsify what Planning says about a Need, which unblocks a withdrawal of a Need that an Active Plan depends on and can forge the recorded disposition actor.

### AUD-XC-017 — Reference-data API lets a bare Frappe Role create further Procuring Entities and PE/FY contexts
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AUTH-ADR-001 v1_11 §19 (line 949), §5.7 (line 314); CFG-CHG-002 v0_18 CFG10-AC-003 (line 868), CFG10-AC-020 (line 885), line 1062 · **Module(s):** Core reference data · **Sources:** sweep-authz F-11
**Evidence**
- `kentender_core/kentender_core/api/reference_data_api.py:71-77` (`create_or_revise_pe`), `:79-84` (`update_pe_draft`), `:86-105` (`decide_pe_change`), `:121-123` (`create_financial_year`), `:169-` (`enable_pe_fy_context`) — whitelisted, session user passed on.
- `kentender_core/kentender_core/services/reference_data_transitions.py:37-47,61-75` — `create_pe_draft` inserts a `Procuring Entity` and a `Procuring Entity Version` with `ignore_permissions=True` after `perm.require_reference_data_manager(actor)` only; there is no single-entity guard.
- `kentender_core/kentender_core/services/reference_data_permissions.py:19-29,32-` — authority is the bare Frappe Role `Reference Data Manager`; `procuring_entity.json:161` grants that role `rwc`.
**Rule:** AUTH §19 "Do not create a second Procuring Entity record or simulate multi-tenancy inside one site"; CFG10-AC-003 "Creating a second Procuring Entity is impossible through the UI, the API and a fixture"; CFG10-AC-020 "No `Reference Data Manager` role… exists"; AUTH §5.7 "Direct manual addition of a Frappe Role creates no business authority".
**Reproduction / failing test sketch:** static; not run. As a user given the Frappe Role `Reference Data Manager`: `POST /api/method/kentender_core.api.reference_data_api.create_or_revise_pe` `payload={"entity_code":"PE-X","legal_name":"X","pe_type_code":"<active type>"}`. Expected: refusal; read result: a second `Procuring Entity` row. Pytest: after the call, `frappe.db.count("Procuring Entity")` must not exceed the site's single entity.
**Impact:** A role holder can create extra Procuring Entities and PE/FY contexts. I traced no authorisation effect (the single `Site Procuring Entity` is untouched), so this is rated Medium rather than the source's High.

### AUD-XC-018 — Supplier-registry reads and eligibility results are open to every logged-in account
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AUTH-ADR-001 v1_11 §5.1/§5.4; AGENTS.md §4.3; BDS v0_11 (suppliers see only their own organisation) · **Module(s):** Suppliers (KTSM) · **Sources:** sweep-authz F-04, F-20; sweep-hazards F-4
**Evidence**
- `kentender_suppliers/kentender_suppliers/api/ktsm_landing.py:24-25,153-154,304-305` — `get_landing`, `get_suppliers(filters)`, `get_supplier_detail(supplier_code)` are `@frappe.whitelist()` and never call `_assert_registry_access()` (defined :258, called only at :461, :492, :552). They read with `frappe.get_all`/`frappe.get_doc`; `get_supplier_detail` returns approval, operational and compliance status, `risk_level`, `external_user` (login e-mail), document list with `verified_by`, category assignments and status history (:316-422).
- `kentender_suppliers/kentender_suppliers/services/eligibility.py:64-79` — `check_supplier_eligibility`, `check_multiple_suppliers` (`allow_guest=False`, no role check); `_eligibility` returns reason codes (not active, suspended, blacklisted) for any `supplier_code`; `api/smw_workflow.py:122-126` `ktsm_check_eligibility` wraps it.
**Rule:** AGENTS.md §4.3 "Return only data the caller is allowed to see"; AUTH §5.4.
**Reproduction / failing test sketch:** static; not run. As a supplier Website User: `GET /api/method/kentender_suppliers.api.ktsm_landing.get_suppliers?filters={}` lists all profiles with risk level; `get_supplier_detail?supplier_code=SUP-KE-2026-0001` returns documents, verifier names and login e-mail; `check_multiple_suppliers?supplier_codes=["SUP-KE-2026-0001"]` reveals suspension/blacklist reasons. Pytest: same calls under `frappe.set_user(<no-role user>)` must raise.
**Impact:** Competing suppliers can read each other's registry status, risk rating, document verification and login e-mail.

### AUD-XC-019 — Supplier approval/return/reject are authorised by bare Frappe Roles (System Manager, "Approving Authority")
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AUTH-ADR-001 v1_11 §5.7 (line 314), §5.8 (line 326 "Generic labels such as `approving authority`… are prohibited unless an approved source defines that distinct legal capacity"), §8 · **Module(s):** Suppliers (KTSM) · **Sources:** sweep-authz F-17
**Evidence**
- `kentender_suppliers/kentender_suppliers/api/smw_workflow.py:16-23` — `_assert_approver_or_admin` allows `{"System Manager","Administrator","KenTender Approving Authority"}`; used at :67-69, :74-77, :81-84. `:26-34` `_assert_compliance_reviewer` and `:37-46` `_assert_start_review` likewise.
- `kentender_suppliers/kentender_suppliers/api/ktsm_landing.py:258-271` — `_assert_registry_access` accepts bare roles including `Procurement Officer`, `Procurement Planner`, `Planning Authority`. None of `KenTender Approving Authority`, `KenTender Compliance Officer`, `KenTender Supplier Registry Officer`, `KenTender Supplier Blacklist Authority` is a registered business role (`kentender_core/services/business_role_registry.py`, per sweep-authz; not re-opened).
**Rule:** AUTH §8 technical roles decide nothing; §5.7 a Frappe Role grants no business authority; §5.8 generic "approving authority" label prohibited.
**Reproduction / failing test sketch:** static; not run. As System Manager with no responsibility: `POST /api/method/kentender_suppliers.api.smw_workflow.ktsm_approve_supplier` `{"supplier_profile":"<profile Under Review>"}` succeeds (only `sod.assert_not_same_user_submit_and_approve` applies, governance.py:64-69).
**Impact:** A System Manager can approve supplier registrations, and approval authority rests on role names that no approved document defines.

### AUD-XC-020 — Unauthenticated `ktsm_register` creates User, Supplier, profile and API-access rows with `ignore_permissions` (all 5 guest endpoints listed)
**Severity:** Medium · **Classification:** SPEC GAP (no current document justifies a guest write; owner must decide whether public self-registration exists and how an e-mail is verified) · **Doc:** AUTH-ADR-001 v1_11 (silent on guest writes); BDS v0_11 (verified supplier accounts; BDS FU-06); AGENTS.md §4.3 · **Module(s):** Suppliers · **Sources:** sweep-authz F-21 (user asked that `allow_guest` be flagged)
**Evidence** — all `allow_guest=True` endpoints in `kentender_*` (grep `allow_guest`, non-test), each with its justification status:
- `kentender_procurement/kentender_procurement/bid_submission/api.py:41` `get_available_tenders` — justified: BDS v0_11 line 725 "Public bidder-safe list of open Tenders".
- `.../bid_submission/api.py:47` `get_tender_overview` — justified: BDS v0_11 lines 1127, 1537 (signed-out public Tender); own-bid data only after the supplier assignment check.
- `.../bid_submission/api.py:58` `download_tender_document` — justified: BDS v0_11 line 1631 "Opens or streams the exact published document from Tenders by bidder-safe reference"; key-addressed through `tenders_gateway.stream_public_document`.
- `.../bid_opening/api.py:311` `get_public_opening` — justified: BOP v0_11 §10.5 (line 300) public attendance page; data only for published Tenders.
- `kentender_suppliers/kentender_suppliers/api/smw_public.py:23` `ktsm_register` — **not justified by any current approved document**; `:49` `erp.insert(ignore_permissions=True)`, `:58` `prof.insert(ignore_permissions=True)`, `:94` `usr.insert(ignore_permissions=True, ignore_links=True)`, `:114` API-access insert. `_ensure_website_user_for_registration` (:77-95) returns an existing user's e-mail unchanged, so the new profile is bound to that existing login without verification. No throttle, captcha or e-mail verification. The two `allow_guest=False` markers (`services/eligibility.py:64,74`) are explicit denials, not guest endpoints.
- Supported onboarding is `kentender_suppliers/kentender_suppliers/supplier_accounts/` `register_supplier_organisation` (`api.py:38-44`, `methods=["POST"]`, not guest, followed by the `send_account_verification` command at :47-49).
**Rule:** AGENTS.md §4.3; BDS v0_11 supplier accounts are verified before they can act; the guest write has no governing rule.
**Reproduction / failing test sketch:** static; not run. Unauthenticated: `POST /api/method/kentender_suppliers.api.smw_public.ktsm_register` `{"supplier_name":"A","primary_email":"victim@example.test"}` repeated with different names. Expected: refusal or verification step; read result: a Supplier, a KTSM profile bound to `victim@example.test`, and a Website User (when absent) per call.
**Impact:** Anyone on the internet can create unbounded supplier and user records and bind a profile to another person's e-mail. The profile starts `Draft`, so no bid right follows by itself.

### AUD-XC-021 — Frappe User Permission is read in a production path reachable from whitelisted endpoints
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AUTH-ADR-001 v1_11 §19 (lines 946, 952 "Do not treat Frappe User Permission as a KenTender fallback", "Do not store authoritative context in… session defaults"), §11.5 (line 480); NDS v1_16 §6 (User Permission "grant no Departmental Needs authority") · **Module(s):** Core working context / reference data · **Sources:** sweep-authz F-16 (user asked that User Permission use be flagged)
**Evidence**
- `kentender_core/kentender_core/services/org_scope_access.py:87-102` — `permitted_procuring_entities`: "Fall back to User Permission PEs if no scope rows yet" then `frappe.get_all("User Permission", filters={"user": user, "allow": "Procuring Entity"}, pluck="for_value")`.
- Reached from `kentender_core/kentender_core/services/reference_data_resolver.py:116-118` (`_authorized_context_rows`) and `services/working_context.py:114-117` (`pe_options`), exposed by whitelisted `api/reference_data_api.py:229-241` (`get_working_context`, `select_working_context`, `validate_context_for_command`); the choice is persisted through `frappe.defaults` (`working_context.py`, `_set_default`, per sweep-authz).
- `kentender_core/kentender_core/services/authorization_native.py:34-54` also scopes by `User Permission`; the module is imported only by tests in this repo (grep).
- Other production code reads no User Permission (grep of `User Permission|get_user_permissions` over `kentender_*` finds scripts, seeds, tests and one docstring).
**Rule:** AUTH §19 "Do not treat Frappe User Permission as a KenTender fallback"; §19 "Do not store authoritative context in… session defaults"; §11.5 "No fallback mode".
**Reproduction / failing test sketch:** static; not run. Add `User Permission` (allow=`Procuring Entity`, for_value=`<PE>`) for a user with no responsibility and no `User Scope Assignment`; call `get_working_context?module=budget`. Expected: no context rows; read result: contexts for that PE are returned.
**Impact:** A Frappe User Permission row still widens which PE/FY contexts a user is offered. I found no command that authorises from it, so the effect is limited to the legacy context selector.

### AUD-XC-022 — A department reader can fetch unpublished Internal Tender documents by digest
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** TPR v0_17 §6 (line 713) "Read inherited requirements and neutral Tender/publication status… no Tender action"; §7.1 `GetTenderDocument` (line 733) "by digest and authorised audience"; AUTH-ADR-001 v1_11 §10 (masked not-found) · **Module(s):** Tenders · **Sources:** sweep-authz F-13; trace-tenders F-11
**Evidence**
- `kentender_procurement/kentender_procurement/tenders/services/documents.py:104-108` — `mode = authz.reader_mode(...)`; only `audience == "Audit"` (needs `site`/`technical`) and `audience == "Public"` (needs `published_at`) are restricted; `AUDIENCES = ("Internal","Public","Audit")` (:29) and the default is `"Internal"` (:92), so `department` mode falls through to `"html": html_of(row.name)` (:120).
- `kentender_procurement/kentender_procurement/tenders/services/tender_authorization.py:154-165` — `reader_mode` returns `department` for a Head of User Department / Author whose unit contributed.
- `kentender_procurement/kentender_procurement/tenders/services/read.py:674,681` — `get_tender` returns `version_summary(version)` (`invitation_digest`, `issued_tender_digest`, preparer/approver ids; defined :567-579) and `review.summary(version)` (findings text) for every mode including `department`; `:652` shows `reader_mode` is the only gate.
- Contrast `kentender_procurement/kentender_procurement/tenders/api.py:89-91` `preview_tender_documents` refuses `department` mode.
**Rule:** TPR §6 (line 713) "neutral Tender/publication status… no Tender action"; §7.1 "authorised audience".
**Reproduction / failing test sketch:** static; not run. As a Head of User Department of a contributing OU, for a Tender with a Submitted Version: `GET …tenders.api.get_tender?tender=<ref>` and read `version.invitation_digest`; then `GET …tenders.api.get_tender_document?digest=<digest>&audience=Internal`. Expected: not found; read result: the unpublished Invitation HTML. Pytest: `documents.get_tender_document(digest_value=d, audience="Internal", user=<department HoD>)` must raise not-found for an unpublished Tender.
**Impact:** Contributing departments can read the unpublished Invitation and complete Tender text and the review findings, ahead of publication.

### AUD-XC-023 — Tender list predicate (lead unit only) differs from the direct-access predicate (lead plus contributors)
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** OVS-CHG-001 v0_6 §4.1 table row TPR/BOP (line 87) "HoD receives administrative progress… for a Tender with an authorised lead/contributing-OU relationship" and line 94; AUTH-ADR-001 v1_11 §5.3 and §5.4 ("Counts shall not disclose records that rows cannot show") · **Module(s):** Tenders · **Sources:** sweep-authz F-14; trace-tenders F-12
**Evidence**
- `kentender_procurement/kentender_procurement/tenders/services/tender_authorization.py:249-257` — list condition `` `tabTender`.`lead_org_unit` in (...) `` for non-Site-wide readers; `:299-305` `has_permission` and `:154-165` `reader_mode` also match `contributing_org_unit_ids`.
- `kentender_procurement/kentender_procurement/tenders/services/read.py:236` — the Tenders workspace uses `frappe.get_list("Tender", ..., user=actor)`.
**Rule:** OVS §4.1 contributor matching "uses the actual source version consumed by the Tender"; AUTH §5.3 "one predicate".
**Reproduction / failing test sketch:** static; not run. Tender with lead OU-A and contributor OU-B; as HoD of OU-B: `frappe.get_list("Tender", user=hod)` omits it while `frappe.has_permission("Tender", doc=<name>, user=hod)` is True and `get_tender` opens it in `department` mode.
**Impact:** A contributing department's HoD gets no workspace row for a Tender they may open and which OVS says they must see progress for; counts and rows disagree.

### AUD-XC-024 — Evaluation and Proceedings register nothing with the technical-read hooks
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AUTH-ADR-001 v1_11 §8 (line 361) "Every module registers its record types… through the `kt_technical_reference_resolvers` hook and its read entry points… through `kt_technical_read_probes`"; OVS v0_6 §4.2 · **Module(s):** Bid Evaluation, Proceedings, Bid Opening (probes) · **Sources:** sweep-authz F-24 (registration half)
**Evidence**
- `kentender_procurement/kentender_procurement/hooks.py:667-685` — resolvers: Needs, Planning, Requisitions, Tenders, STD, Bid Submission, Bid Opening, Award; probes: the same minus Bid Opening. No `bid_evaluation` or `proceedings` entry in either list.
- `ls kentender_procurement/kentender_procurement/bid_evaluation/services` and `.../proceedings/services` contain no `technical_read.py` (Award, Needs, Planning, etc. do).
**Rule:** AUTH §8 "Every module registers its record types with it… and its read entry points with the technical-read conformance gate".
**Reproduction / failing test sketch:** static; not run. As System Manager at `/app/technical-search`, search an Evaluation reference (e.g. `EVL-MOH-2099-001`) or a Proceeding reference: expected a resolved route; read result: no match. A conformance-gate test that enumerates registered probes would not include these modules.
**Impact:** Administrator/System Manager cannot locate Evaluation or Proceedings records through the one sitewide search, and the technical-read gate cannot test those routes.

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

### AUD-HND-003 — `NeedPlanningDispositionChanged` deviates from the approved wire contract (enum, schema_version, producer_sequence, payload-conflict rule)
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS-CHG-001 v1_16 §7.4 (lines 556-574); PLN-CHG-001 v1_29 §7.6 (line 1037) · **Module(s):** Planning, Departmental Needs · **Sources:** sweep-handoffs F-7
**Evidence**
- `kentender_procurement/kentender_procurement/departmental_needs/services/usage.py:256` — `DISPOSITION_NOT_PROCEEDING = "Not proceeding"`; doctype options `Proceeding\nNot proceeding` (`departmental_needs/doctype/need_planning_disposition_projection/need_planning_disposition_projection.json:18`); producer passes the same constant (`procurement_planning/services/dpp_validation.py:254`).
- `usage.py:329` `if value not in DISPOSITION_VALUES: fail(...)` (rejects the spec's literal) and `usage.py:303-345` has no `schema_version` parameter; `dpp_validation.py:249-259` emits none.
- `dpp_validation.py:244` — `sequence = int(frappe.db.get_value("Departmental Plan Submission", submission, "submission_number") or 0)` used as `producer_sequence` (`:257`).
- `usage.py:348` — `if frappe.db.exists(DISPOSITION_DOCTYPE, {"source_event_id": event_id}): return {... "idempotent": True ...}`; usage consumer `usage.py:205` the same; neither compares payload.
**Rule:** NDS v1_16 §7.4 line 560 "Exact enum `Proceeding` or `Not proceeding this financial year`"; line 556 "`schema_version` Integer 1 ... Unknown versions are rejected/quarantined"; line 557 `producer_sequence` "allocated transactionally ... in this stable Need's disposition stream"; line 574 "Different payload under the same ID/sequence conflicts; preserve evidence and reject." PLN v1_29 line 1037 repeats the enum and sequence rule.
**Reproduction / failing test sketch:** (static; not run) pytest: call `usage.project_planning_disposition(..., disposition="Not proceeding this financial year", reason="x"*25, source_event_id="E1", producer_sequence=1)` -> fails with `NDS_FIELD_REQUIRED` (spec literal rejected). Call it twice with the same `source_event_id` and different `reason`/`need_revision` -> second returns `idempotent: True` instead of a conflict.
**Impact:** Producer and consumer agree with each other but not with the approved contract, so any compliant external producer or consumer breaks, and a replayed event with changed content is silently accepted.

### AUD-HND-004 — Tenders' proceeding-coverage rows never reach Planning (allocation id tested as a document name, silent skip)
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** PLN-CHG-001 v1_29 §4.8 (line 286 ProceedingCoverage), §7.3 (line 1010 "exact proceeding/REQ/Plan/allocation coverage") · **Module(s):** Tenders, Planning · **Sources:** sweep-handoffs F-14
**Evidence**
- `kentender_procurement/kentender_procurement/tenders/services/planning_gateway.py:70-71` — `allocation = cstr(line.get("plan_item_line_id"))` / `if not allocation or not frappe.db.exists("Plan Source Allocation", allocation): continue`.
- `kentender_procurement/kentender_procurement/procurement_planning/services/plan_requisition.py:241` — `"plan_item_line_id": a.allocation_id`; `references.py:112-114` allocation ids look like `PSA-<item>-nnn`.
- `procurement_planning/doctype/plan_source_allocation/plan_source_allocation.json:3` — `"autoname": "format:PSAR-{#####}"`, so `frappe.db.exists("Plan Source Allocation", "PSA-...")` tests the document name and is never true. `allocation_id` is a separate field, preserved across successor copies (json description), and Planning itself resolves it with `{"allocation_id": ..., "plan_item": ...}` (`plan_requisition.py:506`).
- `procurement_planning/services/schedule.py:209` -> `actuals.upsert_coverage(allocation=cstr(row.get("allocation")), ...)` and `proceeding_coverage.json` field `allocation` is a Link to `Plan Source Allocation` (document name); `progress_read.py:176-200` builds the proceedings list only from `Proceeding Coverage`.
- No Tenders test exercises coverage (`grep -n coverage tenders/tests` finds only unrelated home-provider hits); `tenders/tests/test_gateway_contracts.py:66` checks only that the `coverage` parameter exists.
**Rule:** PLN v1_29 line 1010 requires the invitation actual to carry "exact proceeding/REQ/Plan/allocation coverage"; line 286 ProceedingCoverage needs "exact Plan/item/allocation IDs".
**Reproduction / failing test sketch:** (static; not run) On the test site: authorise a requisition, start and publish a Tender (`ConfirmTenderPublished`). Then `frappe.get_all("Proceeding Coverage", filters={"proceeding_id": <tender_reference>})` returns `[]`, while the invitation milestone actual is stored. Test: in `tenders/tests`, call `planning_gateway._coverage(root)` for a published Tender and assert it is non-empty; it returns `[]`.
**Impact:** Every published Tender delivers its date to Planning with an empty coverage list, so Planning's procurement-progress view shows no proceeding, stage or covered quantity for the item (impact inferred from `progress_read.py:176-200`; not run).

### AUD-HND-005 — Planning's budget-revision request omits `expected_line_revision`, so Budget's stale-line check is dead and Budget stores Planning's over-amount
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** BUD-CHG-001 v1_12 §8.5 item 1 (line 446), BUD21-AC-001/002 (lines 1495-1496); PLN-CHG-001 v1_29 §7.3 (line 1013) · **Module(s):** Planning, Budget · **Sources:** sweep-handoffs F-8
**Evidence**
- `kentender_procurement/kentender_procurement/procurement_planning/services/budget_revision.py:110-121` — payload keys `planning_request_id, idempotency_key, fiscal_year, budget_line, planned_amount, over_amount, plan_version_reference, plan_label, requested_by, fixture_namespace`; no line revision.
- `kentender_budget/kentender_budget/services/budget_revision_request_contracts.py:125-126` — `expected = cstr(payload.get("expected_line_revision")); if expected and expected != line_version.name: return _error("BUDGET_DECISION_BASIS_STALE", ...)`; only a Budget test passes the key (`tests/test_bud_chg_001_v111_revision_request.py:162`).
- `budget_revision_request_contracts.py:144` — `"over_amount": flt(payload.get("over_amount")) or (planned - approved)`: Budget stores Planning's over-amount, computed from Planning's own `approved` (`budget_revision.py:90,115`) while Budget's `approved_amount_at_receipt` (`:140`) is its own current value.
- `budget_revision.py:126` maps `BUDGET_DECISION_BASIS_STALE -> PLN_FINANCE_STALE`; unreachable. Planning's display statement carries no line revision (only the decision statement does, `budget_line_contracts.py:657`), which is why none is sent.
**Rule:** BUD v1_12 line 446 Planning calls with "Planning request ID, idempotency key, Fiscal Year, Budget Line and expected line revision, Planning's planned amount, the over amount ..." and Budget "checks the expected revision"; BUD21-AC-002 "a stale line revision fails with `BUDGET_DECISION_BASIS_STALE`". PLN line 1013 lists "exact Budget Line and revision, approved, planned and over Money amounts".
**Reproduction / failing test sketch:** (static; not run) Planner sees line L approved 60m, planned 62m. A Budget Officer changes L's approved amount to 65m (new line version) before the Planner clicks `RequestBudgetRevision`. Budget receives the request with no revision, records `approved_amount_at_receipt=65m` but `over_amount=2m` (Planning's figure); with planned 62m <= 65m the request is refused as not required only because of the separate amount test, otherwise (approved 61m) it is accepted with an over-amount of 2m against a true 1m. Test: send a stale-basis request through `budget_revision.request_budget_revision` and assert `PLN_FINANCE_STALE`.
**Impact:** A Budget Officer can be shown an over-amount that no longer matches the line they will decide on, and the spec's stale-line refusal can never occur through the real caller.

### AUD-HND-006 — Tenders maps the wrong REQ error code, so a concurrent second Tender start gets `TND_HANDOFF_INVALID` instead of `TND_HANDOFF_CONFLICT`
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0_17 error table line 794 (`TND_HANDOFF_CONFLICT`); REQ-CHG-001 v1_14 error table line 856 (`REQ_HANDOFF_CONFLICT`) · **Module(s):** Tenders, Requisitions · **Sources:** sweep-handoffs F-2; trace-requisition F-24
**Evidence**
- `kentender_procurement/kentender_procurement/procurement_requisitions/services/handoff.py:122` — `fail("REQ_HANDOFF_CONFLICT", detail={"tender": cstr(doc.tender)})` (consumed by another Tender) and `:124` the same code for a revoked / non-current handoff.
- `kentender_procurement/kentender_procurement/tenders/services/handoff_gateway.py:88-90` — `if exc.code == "REQ_HANDOFF_CONSUMED": fail("TND_HANDOFF_CONFLICT", ...)` then `fail("TND_HANDOFF_INVALID", detail={"requisition_error": exc.code})`.
- `REQ_HANDOFF_CONSUMED` is raised only by revocation (`procurement_requisitions/services/authorise.py:185`), never by `record_handoff_consumption`, so the conflict branch is unreachable. The non-concurrent pre-check (`tenders/services/draft_commands.py:102-103`) does map correctly.
**Rule:** TPR v0_17 line 794: `TND_HANDOFF_CONFLICT` -> "A Tender has already been started for this requisition." with the Tender reference and **Open Tender** (for a reader of the Tender); TPR12-AC-009 requires this conflict not to expose the Tender to an unauthorised viewer. The code never reaches that branch for the real race.
**Reproduction / failing test sketch:** (static; not run) Two Procurement Officers call `StartTender` for the same handoff concurrently (or call `handoff_gateway.consume` twice with different Tender names after the first committed). The second `record_handoff_consumption` raises `REQ_HANDOFF_CONFLICT`; Tenders turns it into `TND_HANDOFF_INVALID` with `detail.requisition_error="REQ_HANDOFF_CONFLICT"` and no Tender link. Test: assert `exc.code == "TND_HANDOFF_CONFLICT"`.
**Impact:** The loser of a start race sees "no longer available" with no link to the Tender that won; the spec'd error never appears.

### AUD-HND-007 — Tender stores the Annual Plan Version id in `plan_item_version_id`; exact item-content identity is lost
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0_17 §4.1 (line 163); REQ-CHG-001 v1_14 §5.1 (line 157) · **Module(s):** Tenders, Requisitions · **Sources:** sweep-handoffs F-3; trace-requisition F-25
**Evidence**
- `kentender_procurement/kentender_procurement/tenders/services/draft_commands.py:117` — `"plan_item_id": snapshot.get("plan_item_id"), "plan_item_version_id": snapshot.get("plan_version_id")`.
- Producer carries both: `procurement_requisitions/services/handoff.py:59-60` `"plan_version_id": root.plan_version_id`, `"plan_item_id": ..., "plan_item_version_id": root.plan_item_version_id`; Planning defines `plan_version_id = version.name` and `plan_item_version_id = item.name` (`procurement_planning/services/plan_requisition.py:299-300`).
- Field: `tenders/doctype/tender/tender.json:93-96` label "Plan Item version", read-only. No other reader of `Tender.plan_item_version_id` exists (`grep` across the repo outside Planning/Requisitions).
**Rule:** TPR v0_17 line 163 "`plan_item_id`, `plan_item_version_id` | Stable item and exact approved content identities."; REQ line 157 "exact approved content supplying this Requisition, pinned ... immutable."
**Reproduction / failing test sketch:** (static; not run) Start a Tender from any handoff; `frappe.db.get_value("Tender", t, "plan_item_version_id")` equals the Annual Plan Version name, not the Plan Item name in the handoff payload. Test: `assert root.plan_item_version_id == payload["plan_item_version_id"]`.
**Impact:** Every Tender carries a wrong record type in the exact item-content identity field (lineage/evidence defect; no behavioural reader found, static).

### AUD-HND-008 — `TenderPublishedForEvaluation v1` and `ReadEvaluationPreparationSource` do not exist; Evaluation polls on a one-minute sweep
**Severity:** Medium · **Classification:** CODE DEFECT (divergence from a binding the EVL document itself calls "proposed/not yet verified"; EVL tracker row EVL4-1502 shows it as "Blocked - owner") · **Doc:** TPR-CHG-001 v0_17 §5.5.2 (lines 566-584), TPR15-AC-001..006 (line 586); EVL-CHG-001 v0_5 §6 row "Tenders -> Evaluation preparation" (line 191), `EnsureEvaluationPreparation` (line 247) · **Module(s):** Tenders, Bid Evaluation · **Sources:** trace-tenders F-10
**Evidence**
- `kentender_procurement/kentender_procurement/tenders/services/publication.py:169-184` — publication emits only `TenderPublishedOpen` and `TenderOpenForSubmission` (consumer `bidder-service`). `grep -rn "TenderPublishedForEvaluation\|ReadEvaluationPreparationSource" --include=*.py --include=*.json kentender_procurement` returns no match outside docs.
- `kentender_procurement/kentender_procurement/bid_evaluation/services/sweep.py:28-30,40-50` — `ensure_preparation(tender=tender)` runs from the `sweep.run` scheduler job (registered in `hooks.py` near line 503; the sweep docstring `sweep.py:45` says "Scheduler entry (every minute)") over `tenders.evaluation_candidates()`; the docstring states "The sweep is the binding to Tenders and Bid Opening".
- `kentender_procurement/kentender_procurement/tenders/services/evaluation_seam.py:62-85,98-147` — `publication_fact`/`scope_facts` are in-process reads; scope is derived from the release `supported_use` and the Tender row, with no event id/version/schema, no pending/attempt/acknowledgement tracking and no service identity.
**Rule:** TPR v0_17 §5.5.2 line 568 "Tenders durably records `TenderPublishedForEvaluation v1` with the publication transaction or its recoverable outbox"; line 572 stable `event_id`/`event_version`/`schema_version`; line 580 `ReadEvaluationPreparationSource(tender_id, publication_id)` is "an authenticated owner-service read"; line 584 "Tenders records pending delivery, attempts and successful consumer acknowledgement under the same event." TPR15-AC-001: "final channel commit produces one notification." EVL v0_5 line 191 itself says the binding "is a required coordinated binding, not an already verified interface." (Older EVL v0.4 tracker blocked this on the TPR amendment; TPR v0_15 added it and v0_17 is approved with it.)
**Reproduction / failing test sketch:** (static; not run) Publish a Tender on the test site. `frappe.get_all("Tender Event", filters={"tender": t})` has no `TenderPublishedForEvaluation` row and no acknowledgement; Evaluation preparation appears only after the next sweep run. Test for TPR15-AC-001/002: assert exactly one such event row after the final channel confirmation; it will find none.
**Impact:** Evaluation preparation is triggered by polling rather than the specified durable, acknowledged owner event, so missed or delayed delivery has no tracked retry or support evidence.

### AUD-HND-009 — Handoff and outbox event are v1.4 in code; approved REQ v1.14 and TPR v0.17 still specify v1.3, and unconsumed v1.3 handoffs silently become unusable
**Severity:** Medium · **Classification:** SPEC DEFECT · **Doc:** REQ-CHG-001 v1_14 §5.12 (line 361), §5.14 last row (line 404), §9.2 (line 754), §9.1 (line 786); TPR-CHG-001 v0_17 lines 32, 1823, 2024, 2143 · **Module(s):** Requisitions, Tenders · **Sources:** sweep-handoffs F-4; trace-requisition F-18; trace-tenders F-16
**Evidence**
- `kentender_procurement/kentender_procurement/procurement_requisitions/services/handoff.py:31` — `HANDOFF_VERSION = "1.4"`; `procurement_requisitions/services/events.py:19` — `EVENT_AUTHORISED = "ProcurementRequisitionAuthorised.v1.4"`.
- `kentender_procurement/kentender_procurement/tenders/services/handoff_gateway.py:69` — `if cstr(handoff_doc.handoff_version) != req_handoff.HANDOFF_VERSION: fail("TND_HANDOFF_INVALID", ...)`; `procurement_requisitions/services/read.py:897` filters the eligible list by `"handoff_version": handoff_service.HANDOFF_VERSION`. The only handoff patch is `patches/ovs_chg_001_v06_tender_lead_from_certification.py`; no migration of v1.3 handoffs.
- The v1.4 shape is recorded only in code docstrings (`handoff.py:3-12`, "owner D4, 24 Sep 2026") and the REQ implementation plan (`06_requisitions/03_REQ_Implementation_Plan.md` D4), not in an approved REQ/TPR version; REQ v1_14 §5.12 heading is "AuthorisedRequisitionHandoff v1.3".
**Rule:** REQ v1_14 §5.14 line 404 "an incompatible wire change requires an explicit agreed version/cutover, never two undocumented shapes under one name." The approved documents name v1.3; the owner decision to move to v1.4 was never carried into them.
**Reproduction / failing test sketch:** (static; not run) On the test site insert an Authorised requisition whose handoff row has `handoff_version="1.3"` and `consumed_at` unset: `list_eligible_handoffs` omits it and `StartTender` returns `TND_HANDOFF_INVALID` ("version is not supported"). A consumer built to the approved TPR v0_17 text (v1.3) rejects every handoff the code produces.
**Impact:** The approved contract text cannot be implemented as written against the running system, and any in-flight unconsumed v1.3 handoff dies without a cutover (the plan says stored v1.3 handoffs are "history", so the second effect is an accepted owner decision but undocumented in an approved version).

### AUD-STR-005 — Strategy consumer endpoints open to every signed-in account; lineage ignores version status
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** STR-BR-018 "Downstream services return only authorised, Active data and never expose Draft or live workflow content"; STR-AC-020 "Draft reads are rejected"; §9 `STRATEGY_DOWNSTREAM_FORBIDDEN`; §8 `get_strategy_lineage` "One authorised ... ID"; owner ruling 5 Oct 2026 "every internal user reads APPROVED plans; portal/external accounts excluded" (decision recorded in `STR/services/strategy_authorization.py:252-254`) · **Module(s):** kentender_strategy · **Sources:** trace-strategy F4; sweep-authz F-12
**Evidence**
- `STR/api/strategy_consumer_api.py:39,54,71,76,84` — `resolve_strategy_context`, `list_strategy_objectives`, `get_strategy_lineage`, `list_active_targets`, `create_strategy_snapshot` carry only `@frappe.whitelist()` (any signed-in session, including Website Users; not `allow_guest`).
- `STR/services/strategy_consumer.py:225-272` — `get_strategy_lineage(node_id)` resolves any `Strategy Node`, `Performance Indicator` or `Performance Target` by id with no status or read-scope test and returns ancestor titles and the target's `f"{comparison} {target_value}"`. Draft-version ids are visible to Strategy readers.
- `STR/services/strategy_consumer.py:275-336` — `create_strategy_snapshot` (via `run_idempotent`, `strategy_consumer_api.py:84-94`) writes an `Audit Event` and a `Strategy Command Journal` row for whoever calls; the caller has to know an Active objective id (obtainable from `list_strategy_objectives`).
- `STR/services/strategy_authorization.py:262-267` — `read_scope` (the check the Vue read APIs use, `strategy_ui_contracts.py:72-80,340-343,476-481,694-717,873-876`) is not applied here. `STRATEGY_DOWNSTREAM_FORBIDDEN` is defined nowhere in `STR/` (`grep -rn DOWNSTREAM_FORBIDDEN` empty).
**Rule:** STR-BR-018, STR-AC-020; §9 "`STRATEGY_DOWNSTREAM_FORBIDDEN` | A downstream caller attempted an unsupported read, Draft access or mutation"; owner ruling 5 Oct 2026 (portal accounts read nothing here).
**Reproduction / failing test sketch:** (static; not run) 1. Log in as a supplier Website User on kentender-test.local. 2. `GET /api/method/kentender_strategy.api.strategy_consumer_api.resolve_strategy_context?as_of_date=<today>` returns plan and version summary; `...list_strategy_objectives?plan_version_id=<version id>` returns the Active objectives. 3. Given a node id of a Draft version, `...get_strategy_lineage?node_id=<id>` returns Draft titles. Expected: refusal. Test: as the Website User created in `STR/tests/test_ovs_strategy_reads.py:148`, call each endpoint; assert refusal; Draft id to `get_strategy_lineage` also refuses.
**Impact:** External accounts can read Active Strategy content, any signed-in account holding a Draft id can read Draft lineage and target values, and any signed-in account can write Strategy audit and journal rows. No funds or approvals are reachable.

### AUD-STR-006 — "Author cannot approve" is implemented as "submitter cannot approve"
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** STR §5.1 "The author of a version cannot approve it, even when that user also holds Strategy Approver"; §6.1 "cannot approve a version they authored"; STR-AC-010; §16.1 "The no-self-approval check reads the version's audit history" · **Module(s):** kentender_strategy · **Sources:** trace-strategy F7; sweep-sod F10
**Evidence**
- `STR/services/strategy_authorization.py:102-109` — `_submitted_by` returns the performer of the "Submit for approval" event only (events are newest first, `STR/services/strategy_audit.py:73-83`).
- `STR/services/strategy_authorization.py:121-127` — `_blocked_by_self_approval` returns `_submitted_by(version_name) == user` for `CAP_APPROVE`.
- `STR/services/strategy_writes.py:70,257,354` — any Strategy Author may edit a Draft; "Draft saved", "Draft structure saved" and "Successor Version Created" events (`record_event` calls at `strategy_writes.py:81,109,234,276,446`) record the other authors but are ignored.
**Rule:** STR §5.1/§6.1/STR-AC-010 use the word "author" and §16.1 says the check reads the audit history, but the document nowhere defines which events make a user an "author". Decision the owner must make: author = anyone who created or saved Draft content (all Draft events), or only the submitter. BUD v1.12 §6 defines the submitter explicitly ("The submitting Budget Officer cannot approve"), which suggests Strategy's different word is intentional or an omission.
**Reproduction / failing test sketch:** (static; not run) X holds Strategy Author and Strategy Approver; X creates the plan and its structure; Y (Author) clicks Submit; X calls `approve_strategy_version`. Under the code X is allowed (X is not the submitter). Test: `edit_draft_as(X); submit_as(Y); approve_as(X)` expects `AUTH_SEGREGATION_BLOCKED` if the owner rules "author" means any editor; passes (allowed) today.
**Impact:** A dual-role user can author all content and approve it as long as someone else clicks Submit.

### AUD-STR-007 — §13 audit obligations for downstream contract calls and snapshots are not met
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** STR §13 "Append-only events: ... successful and failed context resolution; Strategic Objective listing and lineage reads by a downstream module; and snapshot creation or idempotent reuse ... A downstream contract event also records the calling module." · **Module(s):** kentender_strategy · **Sources:** trace-strategy F10 (the denial-event part is owned by the xc-core cluster "Denial events never written / rolled back on throw")
**Evidence**
- `STR/services/strategy_consumer.py:76-173,176-222,225-272` — `resolve_strategy_context`, `list_strategy_objectives`, `get_strategy_lineage` contain no `record_event`; the only call in the file is `:325-336` (snapshot creation).
- `STR/services/strategy_consumer.py:327-335` — the snapshot event passes `entity_type, entity_name, event_type, plan_version, reason, correlation_id, summary`; `record_event` (`STR/services/strategy_audit.py:18-32`) has no calling-module parameter.
- `STR/services/strategy_idempotency.py:22-24` — an idempotent reuse returns the journal result and writes no event.
**Rule:** STR §13 quoted above.
**Reproduction / failing test sketch:** (static; not run) Call `resolve_strategy_context`, `list_strategy_objectives`, `get_strategy_lineage` and `create_strategy_snapshot` twice with one `correlation_key`; `Audit Event` filtered by `document_type="Strategy Node"` shows exactly one snapshot event with no calling module and none for the reads or the reuse. Test: assert one event per read, one for each reuse, each carrying the calling module.
**Impact:** The required trail of which module read strategy content and froze lineage does not exist; the audit trail cannot show who used the data.

### AUD-STR-008 — Generated Strategy identifiers can be supplied by the caller and are not unique
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** STR-BR-016 "Ordinary users never enter or modify generated identifiers"; §17 "No editable generated reference"; §4.3 `strategy_node_id` "Immutable generated reference" · **Module(s):** kentender_strategy · **Sources:** trace-strategy F11
**Evidence**
- `STR/services/strategy_reference.py:142-148` — `ensure_doc_reference` returns the supplied value when `current` is non-empty (`if current: return current`).
- `STR/services/strategy_reference.py:183-190` — `validate_reference_field` only rejects an empty value; there is no uniqueness or format test (`REF_RE`, `:24`, is unused outside tests).
- `STR/kentender_strategy/doctype/strategy_node/strategy_node.json:28-35` — `strategy_node_id` is `Data`, `reqd`, `search_index` and not `unique`; the other four DocTypes are the same; `autoname` is `hash`.
- `STR/services/strategy_writes.py:405-407,424-426,441-443` — payload keys go straight into `frappe.get_doc(data)`.
**Rule:** STR-BR-016; §4.3.
**Reproduction / failing test sketch:** (static; not run) As Author: `save_strategy_structure_draft(plan_version_id=<own Draft>, nodes=[{"node_type":"Pillar","title":"x","display_order":1,"strategy_node_id":"<an existing reference>"}])` creates a second node with the same reference. Test: assert the call is refused or the reference is regenerated.
**Impact:** The human reference shown in lineage and Requisitions can be set or duplicated by any Author; downstream joins use the hash docname, so integrity of lineage is not affected.

### AUD-STR-009 — Snapshot and lineage payloads carry Frappe docnames, not the generated references, and omit §8 fields
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** STR §4.3 `strategy_node_id` "Immutable generated reference used by parent links, lineage and snapshots"; §8 `create_strategy_snapshot` input "Consumer module, record ID and version, Strategic Objective ID, expected consumer status, approval correlation ID", output "plan and version identity and period plus the ordered Pillar, Programme, optional Sub-programme and Strategic Objective IDs and titles"; `get_strategy_lineage` "stable IDs" · **Module(s):** kentender_strategy, Planning (consumer) · **Sources:** trace-strategy F13; calibration check 3
**Evidence**
- `STR/services/strategy_consumer.py:312-323` — the snapshot returns `plan_id, plan_code, plan_title, plan_version_id (the input docname), effective_from, effective_to, path, objective_id, objective_title, correlation_key`; no plan `period_start/period_end`, no `version_number`, no `consumer module/record/status`.
- `STR/services/strategy_consumer.py:366-385` — `_node_ancestor_path` selects `name, node_type, title, parent_node_id`; path ids in the snapshot and lineage (`:225-272`) are `n["name"]` (hash docname), never `strategy_node_id`.
- `STR/api/strategy_consumer_api.py:84-94` — the endpoint accepts only `plan_version_id`, `objective_id`, `correlation_key`.
**Rule:** STR §4.3 and §8 quoted above. The input-shape difference (how a consumer identifies itself) is a SPEC GAP the owner should settle; the payload omissions and the docname-versus-reference choice are code against §4.3/§8.
**Reproduction / failing test sketch:** (static; not run) `create_strategy_snapshot` for any Active objective; the result has no `period_start`, no `version_number`, and every `path[].id` is a 10-character hash, not `MOH-NODE-0001`. Test: assert `path[].id` equals each node's `strategy_node_id` and the period and version number are present. (The replay-with-different-objective problem is the idempotency root cause owned by the xc-core part.)
**Impact:** Planning freezes opaque hash ids and a partial identity into its own approval snapshot; the "stable generated ID" the document specifies is not what is carried.

### AUD-STR-010 — Planning and Requisitions read Strategy tables directly; objective reference column does not exist
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** STR-BR-020 "Direct reads of Strategy database tables by downstream applications are prohibited"; §17 "No downstream raw SQL or ORM read of Strategy tables" · **Module(s):** kentender_procurement (Requisitions, Planning) · **Sources:** trace-strategy F14
**Evidence**
- `PROC/procurement_requisitions/services/presenters.py:61` — `frappe.db.get_value("Strategy Node", objective, "title")`; `:64-71` `objective_reference` probes columns `node_code`, `reference`, `code` via `frappe.db.has_column("Strategy Node", field)` and falls back to the docname.
- `STR/kentender_strategy/doctype/strategy_node/strategy_node.json` — field names are `strategy_node_id, plan_version_id, col_id, node_type, parent_node_id, title, display_order, fixture_namespace`; none of the three probed columns exist.
- `PROC/procurement_requisitions/services/read.py:438` and `presenters.py:335` — the Requisition shows `objective_reference(root.strategic_objective_id)`.
- `PROC/procurement_planning/services/plan_read.py:1213` and `plan_governance.py:172` — `frappe.db.get_value("Strategy Node", item.strategic_objective, "title")`.
**Rule:** STR-BR-020; §17.
**Reproduction / failing test sketch:** (static; not run) Open any Requisition with a strategic objective: "Strategic objective reference" shows the hash docname, not the generated `…-NODE-####` reference. Test: assert the displayed reference equals the node's `strategy_node_id`; grep gate: no `"Strategy Node"` read outside `kentender_strategy`.
**Impact:** Downstream apps depend on Strategy's table layout (already out of step with it), and the Requisition displays an opaque id as the reference.

### AUD-STR-011 — Approval does not refuse expired applicability
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** STR §12.4 "Future start, expired applicability, stale source, ambiguity or failed guard leaves approval uncommitted"; STR-AC-030 · **Module(s):** kentender_strategy · **Sources:** trace-strategy F17
**Evidence**
- `STR/services/strategy_readiness.py:114-127` — `get_version_approval_blockers` blocks only a missing `effective_from` and `effective_from > today()`; nothing tests `effective_to < today`.
- `STR/services/strategy_readiness.py:62-104` — `get_version_readiness` has no date, plan-period-ended or baseline-still-Active check.
- `STR/services/strategy_transitions.py:177-197` — `Approve` calls `assert_version_ready_for_approval` then `_activate`, which supersedes the predecessor (`:118-137`).
**Rule:** STR §12.4 quoted above.
**Reproduction / failing test sketch:** (static; not run) Successor with `effective_from` yesterday and `effective_to` last week: submit and approve. Expected: STRATEGY_NOT_READY. Actual by reading: version Active, predecessor Superseded, `resolve_strategy_context(as_of_date=<today>)` finds nothing.
**Impact:** An Approver can activate an already-expired version, retiring the working plan and leaving no resolvable strategy.

### AUD-BUD-003 — A Closed Budget can be re-activated by an already-open successor
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** BUD-BR-023 "A Closed Budget admits no new reservations"; §6 "Closed budgets cannot support new holds, conversions or obligation increases"; BUD19-AC-022. Spec is also silent on closing while a Draft/Submitted successor is open (SPEC GAP: owner should decide whether Close is refused, or open successors are declined, when a successor is open) · **Module(s):** kentender_budget · **Sources:** trace-budget F-11 (incl. S-4)
**Evidence**
- `BUD/services/budget_readiness_contracts.py:824-863` — `_close_budget` closes only the Active Version; a Draft/Submitted successor is left.
- `BUD/services/budget_readiness_contracts.py:643-690` — `_approve_budget_version` has no Closed test: `prior_active = _active_version(version.budget)` (`:665`) is `None` after close, `version.status = "Active"` (`:677`).
- `BUD/services/budget_check_reserve_contracts.py:139-154` — `_line_active_version_and_position` then finds the new Active Version and admits reservations.
- `BUD/kentender_budget/doctype/procurement_budget_version/procurement_budget_version.py:11-17` — the DocType validator has no status guard.
**Rule:** BUD-BR-023 and §6.
**Reproduction / failing test sketch:** (static; not run) Active V1 and a Draft V2 (from a revision request); after FY end with no holds, Approver closes V1; Officer submits V2 and a different Approver approves: V2 becomes Active and `check_funding` accepts reservations. Test: `approve_budget_version(V2)` after close expects a typed Closed refusal.
**Impact:** A closed fiscal-year budget can be reopened to new funding holds through a pre-existing draft successor.

### AUD-BUD-004 — `Procurement Commitment.contract` is unique table-wide
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** BUD v1.12 §4.6 "`contract_id` ... Required and unique within the reservation lineage."; §4.6 "One reservation may convert into more than one commitment"; §15.4A two reservations (HWD 20m and 30m) for one Plan Item · **Module(s):** kentender_budget · **Sources:** trace-budget F-07 (downgraded High to Medium: no in-repo caller of `convert_reservation` other than seeds/API, so it is latent until Contract Management integrates, and the document's wording "within the reservation lineage" is not explicit about a contract spanning reservations)
**Evidence**
- `BUD/kentender_budget/doctype/procurement_commitment/procurement_commitment.json:43-52` — field `contract` has `"unique": 1` (a database unique index) while its description says "unique within the reservation lineage".
- `BUD/services/budget_commitment_contracts.py:178-182` — dedupe is on `(contract, reservation)`; `:208-217` inserts the commitment.
- `grep -rn convert_reservation` shows callers only in `budget_api.py:305`, the seeds and `tests`.
**Rule:** §4.6 per-lineage uniqueness; the table-wide index is stricter than the rule.
**Reproduction / failing test sketch:** (static; not run) Two reservations R1 (20m) and R2 (30m) from one REQ authorisation; `convert_reservation(R1, "CTR-1", "20000000")` succeeds; `convert_reservation(R2, "CTR-1", "30000000")` raises a duplicate-entry error on `contract`. Test: reserve two rows on separate lines, convert both under one contract id, expect two commitments.
**Impact:** One contract funded from two reservations (the document's own two-department fixture) cannot be converted in full.

### AUD-BUD-005 — `check_funding` writes a ledger-table event on every call
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** BUD-BR-012 "`check_funding` and `check_plan_affordability` are both non-mutating"; §8.3 "It writes nothing"; §14 "Read/check calls do not create business or funding-ledger events"; BUD18-AC-015 · **Module(s):** kentender_budget · **Sources:** trace-budget F-12
**Evidence**
- `BUD/services/budget_check_reserve_contracts.py:277-286` — `safe_record_event(budget=budget.name, event_type=EVENT_CHECK_PERFORMED, ...)` writes `Check funding performed` (`budget_audit_contracts.py:31`) into `Budget Audit Event`, the append-only ledger table.
- `BUD/services/budget_check_reserve_contracts.py:269-275` — also caches the token.
- The covering test `BUD/tests/test_bud_chg_001_phase3_check_reserve.py:40-57` counts only `Funding Reservation` rows.
**Rule:** BUD-BR-012; §8.3; §14 (note the document also lists "owner decision evidence referencing a funding check" as an event, which is a decision-time event, not a check event; see AUD-BUD-017).
**Reproduction / failing test sketch:** (static; not run) Call `check_funding` ten times with a valid payload; `frappe.db.count("Budget Audit Event", {"event_type": "Check funding performed"})` rises by ten. Test: assert the event count is unchanged by a check.
**Impact:** The ledger fills with non-financial rows on a call the document says must write nothing.

### AUD-BUD-006 — `save_budget_lines_draft` is not one validated change set
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** BUD v1.12 §9.2 "Create, update or remove Draft lines as one validated change set." · **Module(s):** kentender_budget · **Sources:** trace-budget F-15
**Evidence**
- `BUD/services/budget_line_contracts.py:109-210` — rows are written or deleted one by one (`:129,137` `frappe.delete_doc(...)`, `:176-182` update, `:188-205` insert); `:173` `if errors: continue` skips only later rows; `:211-212` `return {"ok": False, "errors": errors}` is a normal return, so the request commits the earlier writes.
- `BUD/services/budget_idempotency.py:44-80` — no rollback on a non-ok result.
**Rule:** §9.2 quoted above.
**Reproduction / failing test sketch:** (static; not run) Payload `lines=[{valid, approved_amount 10}, {title "", ...}]`: row 1 persisted, response `ok:false`. Test: after a failed save, line versions equal the pre-call state.
**Impact:** A rejected save leaves a half-applied Draft the Officer cannot see as a unit.

### AUD-BUD-007 — Editor lost-on-save race and line-scope stamp that never changes
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** BUD v1.12 §9.3 "A stale result cannot silently overwrite newer changes or use the prior token"; §9.2 "Every write requires the expected record version"; AGENTS.md §6.4 (awaited post-mutation reload; editor never re-hydrates from a refresh that carries nothing new) · **Module(s):** kentender_budget · **Sources:** trace-budget F-16; calibration 4
**Evidence**
- `BUD/public/js/budget_funding/components/BudgetVersionEditorScreen.vue:295-311` — `saveDetails` sets `formSignature = signature()` from the form at response time, so values typed during the request become "clean" and `loadDraft` re-hydrates over them (`:159-162`).
- `BUD/public/js/budget_funding/components/BudgetVersionEditorScreen.vue:326-340` — `saveLines` replaces the rows with the server's and sets `linesDirty = false` at response time; the inputs (`:556-582`) are not disabled while `busy` (only the two buttons, `:498-499`).
- `BUD/services/budget_line_contracts.py:92-93` — the stamp compared is `Version.modified`; line saves never save the Version (`:225` only `version.reload()`), so two Officers with the same stamp both pass.
**Rule:** §9.3, §9.2, AGENTS.md §6.4.
**Reproduction / failing test sketch:** (static; not run) UI: click Save changes on Approval details and type into Approval reference before the response arrives; the field reverts. API: two `save_budget_lines_draft` calls carrying the same `expected_modified` both succeed and the second overwrites the first's amounts. Test: Playwright type-during-save spec; Python: a second line save with the pre-first stamp must return `BUDGET_STALE_WRITE`.
**Impact:** Edits typed during a save are silently lost; concurrent line edits overwrite each other.

### AUD-BUD-008 — Approval document removed from the evidence gate against approved BUD-BR-004
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** BUD-BR-004 "Approval reference, approval date, one approval document and a positive authorised total are required before submission"; §9.3 "exactly one successfully uploaded/linked approval document" before Save and add budget lines; §13 `BUDGET_APPROVAL_EVIDENCE_REQUIRED`; BUD19-AC-003. The owner instruction of 19 Sep 2026 is recorded only as FU-23 in `docs/mvp-1-r1/03_budget/FOLLOW_UPS.md:49`; v1.12 (3 Oct) did not fold it in · **Module(s):** kentender_budget · **Sources:** trace-budget F-18; S-6
**Evidence**
- `BUD/services/budget_contracts.py:951-955` — first-save gate comment "the approval document is no longer required to save or submit (owner instruction)"; `:998-999` the document is optional.
- `BUD/services/budget_readiness_contracts.py:91-93` — `_evaluate_readiness` has no `approval_document` test.
- Pinned by tests `test_registering_a_budget_does_not_require_an_approval_document` and `test_submit_succeeds_without_an_approval_document` in `BUD/tests/test_bud_chg_001_phase3_lifecycle.py`.
**Rule:** BUD-BR-004, §9.3 quoted above. The owner must either update the document or restore the gate; the approved document is the oracle until then.
**Reproduction / failing test sketch:** (static; not run) `save_budget_version_draft` without `approval_document` returns `ok:true`; `submit_budget_version` succeeds. Test per BUD19-AC-003: registering and submitting without a document returns `BUDGET_APPROVAL_EVIDENCE_REQUIRED`.
**Impact:** A budget can be activated with no recorded approval document, weakening the evidence trail the approved document requires.

### AUD-BUD-009 — No historical funding position, no CurrencyBasis, no `get_budget_currency_contract`
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** BUD v1.12 §9.1 `get_budget_line_position` "Never silently label today's position as historical"; `get_budget_currency_contract`; §4.8 CurrencyBasis; §13 `BUDGET_HISTORICAL_BASIS_UNAVAILABLE`; BUD18-AC-050/053; BUD19-AC-016. SPEC GAP residue: the native-metadata mapping for CurrencyBasis (§9.1 "Logical provider name to be mapped to the repository in implementation") · **Module(s):** kentender_budget · **Sources:** trace-budget F-14
**Evidence**
- `BUD/services/budget_contracts.py:361-378` — `get_budget_line_position(budget_line, *, as_at_version=None)` takes the approved amount from the named version but `_line_position` (`:187-215`) sums live reservations/commitments: a superseded version's approved amount is shown with today's reserved/committed.
- `BUD/api/budget_api.py:58-60` — the whitelisted wrapper exposes no historical parameter; `grep as_at_version` finds no caller.
- No `CurrencyBasis`, `currency_basis` or `get_budget_currency_contract` in `BUD/` (grep over `*.py`/`*.json` is empty); the only `BUDGET_HISTORICAL_BASIS_UNAVAILABLE` use is the closure check (`budget_readiness_contracts.py:846`).
**Rule:** §9.1 quoted above.
**Reproduction / failing test sketch:** (static; not run) In the bench console on the test site: `get_budget_line_position(line, as_at_version=<superseded V1>)` returns V1 approved with today's reserved/committed. Test: a historical read for V1 after V2 activation must fail typed or replay the ledger at an instant.
**Impact:** Historical reads (and any consumer needing the currency/precision identity) cannot be served as specified; the historical mode, if used, would mislabel current data as historical.

### AUD-BUD-010 — Disabled or inactive Organisation Unit / Funding Source never rechecked on line save or approval
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** BUD18-AC-056 "Disabled source/OU is excluded from new selection and rechecked at decisions while historical read-by-ID/frozen labels remain available"; §13 `BUDGET_LINE_NOT_ELIGIBLE` "missing, inactive or incompatible" · **Module(s):** kentender_budget · **Sources:** trace-budget F-22 (catalogue item)
**Evidence**
- `BUD/services/budget_line_contracts.py:163-169` — `owner_org_unit` is checked only with `frappe.db.exists("Organisation Unit", owner_org_unit)`; `funding_source` only for truthiness (the Link field validates existence on save).
- `kentender_core/.../organisation_unit/organisation_unit.json:61-67` has `status` (`Active\nInactive`); `kentender_core/.../funding_source/funding_source.json:25` has `record_status`. Neither is read: `grep -rniE "inactive|disabled|record_status" BUD/services` finds nothing relevant.
- `BUD/services/budget_readiness_contracts.py:77-119` — `_evaluate_readiness` (used at submit and approve) has no catalogue-state check.
**Rule:** BUD18-AC-056, §13.
**Reproduction / failing test sketch:** (static; not run) Mark a line's Organisation Unit Inactive in CFG; edit and submit a successor Draft that keeps that unit as owner; approval succeeds. Test: approval returns `BUDGET_LINE_NOT_ELIGIBLE` for a new line naming an inactive unit or source.
**Impact:** A budget line can be created or carried into a new Active version on a retired department or funding source.

### AUD-BUD-011 — Procurement lifecycle and Requisitions read Budget tables directly; Budget reads Planning tables
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** BUD-BR-024 "Downstream modules use Budget service contracts and cannot query or mutate Budget tables directly"; BUD18-AC-031; AGENTS.md (dependency direction `kentender_budget -> kentender_procurement`, cross-app access via the owner's published service) · **Module(s):** kentender_procurement, kentender_budget · **Sources:** trace-budget F-20
**Evidence**
- `PROC/procurement_lifecycle/budget_line_procurement_use.py:119-122,139,160-182` — raw reads of `Procurement Budget Line`, `Procurement Budget Line Version`, `Funding Reservation` (`select coalesce(sum(remaining_amount)...) from tabFunding Reservation`) and `Procurement Commitment`; comment ":139 This stays a raw, permission-free read".
- `PROC/procurement_lifecycle/api/journey_api.py:388-406` — the whitelisted `get_procurement_use_for_budget_line` is gated by `_require_journey_read_permission()` (Procurement Journey read), not by Budget read scope, and returns those sums.
- `PROC/procurement_requisitions/services/read.py:745` and `PROC/procurement_planning/services/financial_basis.py:121` — `frappe.db.get_value("Funding Reservation" / "Procurement Budget Line Version", ...)`.
- Reverse direction: `BUD/services/budget_contracts.py:241-254` reads `Annual Plan Item` (owned by `kentender_procurement`, downstream of Budget).
**Rule:** BUD-BR-024 and the AGENTS.md dependency rule.
**Reproduction / failing test sketch:** (static; not run) A user with Procurement Journey read and no Budget assignment calls `kentender_procurement.procurement_lifecycle.api.journey_api.get_procurement_use_for_budget_line?budget_line_name=<id>`: reservation and commitment totals are returned. Test: assert the call is refused without Budget read scope; a grep gate for `tabFunding Reservation` outside Budget.
**Impact:** Funding positions are readable through a path governed by a different DocType's permission, and downstream code is coupled to Budget's table layout.

### AUD-BUD-012 — SPEC GAP: how an in-process caller proves it is the REQ / Contract Management service principal
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** BUD v1.12 §7 (roles) and BUD-BR-015 "Release, conversion and commitment adjustment require an authenticated downstream event"; BUD-BR-027 "registered Planning service principal"; §8.3 · **Module(s):** kentender_budget, kentender_procurement · **Sources:** trace-budget S-3 (the exposure of money-moving endpoints is owned by the xc-authz cluster "Budget money-moving endpoints open to any non-Guest user")
**Evidence**
- `BUD/services/budget_check_reserve_contracts.py:99-125` — the "service" gate is a human responsibility check (Finance Confirmation Officer or Head of Procurement Function).
- `BUD/services/budget_commitment_contracts.py:128-129` — `release_reservation` begins `_require_service_capability()`; the document names "REQ service principal" and "contract service principal" without saying how an in-process call authenticates (no mechanism, flag or error code is specified).
**Rule:** §7/BUD-BR-015 name the principals, not the mechanism. Decision the owner must make: the authentication mechanism for in-process service principals (for example a trusted-caller context object versus a dedicated service user), and which error code a missing principal returns.
**Reproduction / failing test sketch:** (static; not run) Not applicable as a defect; acceptance test needed once decided: a human session without the principal calling `release_reservation` must be refused.
**Impact:** Without a decision the code cannot be conformant; see the xc-authz cluster for the present exposure.

### AUD-NDS-003 — AO, HOPF and Planner receive an author's unsent Draft successor through get_departmental_need
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 header amendment and §6.1 ("Unsent author Draft access remains unchanged"); OVS v0.6 §4.1 NDS row ("unsent author Drafts remain under existing access"); NDS §6 (Planner reads current accepted revisions) · **Module(s):** NDS · **Sources:** trace-needs C-14
**Evidence**
- `NDS/services/permissions.py:126-140` — Accepted Needs are readable by the Planner (`"planning"`, line 134) and, through `_oversight_office`, by AO/HOPF for `OVERSIGHT_READ_STATES` (`NDS/constants.py:159` includes Accepted).
- `NDS/services/workspace.py:749` — `"current_revision": _version_facts(doc.current_revision)` is returned unconditionally to every profile; `_version_facts` (`workspace.py:77-99`) returns title, description, quantity and the rest of `REVISION_CONTENT_FIELDS`. For an Accepted Need with an open update, `current_revision` is the Draft/Returned/Submitted successor.
**Rule:** NDS header amendment: "Unsent author Draft access remains unchanged"; OVS §4.1: "unsent author Drafts remain under existing access".
**Reproduction / failing test sketch:** (static; not run) Accepted Need N; owner `create_accepted_need_successor` then `save_need_draft(need=N, title="Private draft title", ...)`; AO (or HOPF, or Planner) calls `get_departmental_need(need=N)`; `current_revision.title == "Private draft title"`. `test_ovs_needs_reads.py` asserts only the access profile and actions, not content.
**Impact:** Roles that the documents say must not see unsent author drafts can read their content (Needs have no funding data, so sensitivity is limited to requirement text and quantity).

### AUD-NDS-004 — A superseded accepted revision cannot be read at its own route; the page shows the current revision
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §12.4 / NDS-UI-06, §8.1 `get_departmental_need` (optional accepted revision), NDS-DES-07-HISTORICAL, NDS11-AC-069 · **Module(s):** NDS (Vue) · **Sources:** trace-needs C-15
**Evidence**
- `NDS/services/workspace.py:643` — `def get_need(*, need: str, user: str | None = None)`: no revision parameter; usage and disposition are built for `doc.current_accepted_revision` only (lines 758-761).
- `NDS` Vue `public/js/departmental_needs/DepartmentalNeeds.vue:381-388` — `pinnedRevision` returns `accepted` when the number matches and otherwise `return accepted || null;` (line 387), i.e. the CURRENT accepted revision object.
- `components/NeedDetailScreen.vue:421-426` — `isHistoricalRevision` is true only when `pinnedRevision.name !== acceptedRevision.name`; with the fallback above both are the same object, so it is never true and the "has been superseded" notice (line 93) is unreachable.
**Rule:** NDS §12.4: the Planning deep link "fixes the accepted revision in the route. If it is superseded, the page remains historically readable and clearly labels the current accepted revision without redirecting or rewriting the requested revision."
**Reproduction / failing test sketch:** (static; not run) Need with R1 superseded by R2; open `/app/departmental-needs/<ref>/accepted/1`: the Required-by date and title shown are R2's. Test: change R2's required-by, load the R1 route, assert R1's value and the superseded notice. `accepted-source.spec.ts:43` asserts only the URL and `data-reference`.
**Impact:** A Planner following a Plan Item's link to the revision the plan actually used reads different requirement facts than the plan holds, with no warning.

### AUD-NDS-005 — "Awaiting planning clearance" is unreachable from the UI; approve-while-included raises instead of recording the block
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §5.3 table (Evaluate), §8.2 `decide_accepted_need_withdrawal` ("approve, block for clearance or decline atomically"), §12.6 ("the command records/retains Awaiting planning clearance"), §5.5, §7.6 · **Module(s):** NDS · **Sources:** trace-needs C-20
**Evidence**
- `NDS/services/lifecycle.py:1039` — `request_withdrawal` always creates the request with `"status": WITHDRAWAL_AWAITING_REVIEW`.
- `NDS/services/lifecycle.py:1111-1115` — `if decision == "approve": if dependency["included"]: fail("NDS_ACTIVE_PLAN_DEPENDENCY", ...)` raises and rolls back; nothing is recorded.
- `NDS/services/lifecycle.py:1138-1152` — only an explicit `decision == "evaluate"` sets `WITHDRAWAL_AWAITING_CLEARANCE`.
- `public/js/departmental_needs/DepartmentalNeeds.vue:1142,1195` — the app sends only `decideWithdrawal("decline")` and `decideWithdrawal("approve")`; a grep for `evaluate` in the Vue app finds nothing outside specs.
**Rule:** NDS §8.2 (line 634) and §12.6 (line 1410): "If an Active Plan dependency exists, the command records/retains `Awaiting planning clearance`, returns the exact Plan/Plan Item reference …".
**Reproduction / failing test sketch:** (static; not run) Need included in the Active plan; author requests withdrawal; HoD opens the review in the browser: only Decline is offered, status stays "Awaiting review"; calling `decide_accepted_need_withdrawal(decision="approve")` returns `NDS_ACTIVE_PLAN_DEPENDENCY` and no status change. Tests `T-LC:1238` and `T-DE:137` reach the state only by calling `evaluate` directly.
**Impact:** The Planner's "Decide whether the annual plan keeps this need" turn and the author's "Waiting for a Planning change" item (`NDS/services/guidance.py:249-263` for the Planner turn; the author waiting item is in `NDS/services/my_work_provider.py`) are unreachable in a browser-driven flow, so a blocked withdrawal never reaches the Planner.

### AUD-NDS-006 — A Returned correction can be resubmitted after intake closes; the next-step answer says it cannot
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §12.7 (line 1418: "At the close instant, initial creation, initial submission and resubmission of an unaccepted Returned initial Need are blocked"), NDS-BR-003 (line 422: "Submission stays blocked while the flag is closed"), NDS11-AC-054 (line 1675), NDS12-AC-017 (line 1742), NDS11-CHG-015 (line 1894) · **Module(s):** NDS · **Sources:** trace-needs C-03
**Evidence**
- `NDS/services/lifecycle.py:663-669` — `elif prior in {STATE_DRAFT, STATE_RETURNED}: ... if prior == STATE_DRAFT: require_open_intake(doc.financial_year)`; the Returned branch is not gated.
- `NDS/services/guidance.py:168-203` — for Draft and Returned alike, closed intake yields `NDS_INTAKE_NOT_OPEN` / "New submissions are closed"; the code is therefore internally inconsistent.
- Pinned the other way by `NDS/tests/test_departmental_needs_lifecycle.py:478` (`test_a_returned_correction_may_be_resubmitted_after_the_window_closes`) and `NeedEditorScreen.spec.js:65`.
**Rule:** NDS §12.7 and NDS11-CHG-015 ("preserve save/correction while initial submit/resubmit stays blocked"). `FOLLOW_UPS.md` FU-18 (4 Sep 2026) recorded the ambiguity against v1.6; the later amendments settled it as "blocked", and BR-002/BR-003 still use the narrower word "initial", which should be reconciled (SPEC DEFECT note).
**Reproduction / failing test sketch:** (static; not run) Need returned for correction; CFG closes needs submission for the FY; `submit_need_revision(need, expected_version, idempotency_key)` returns `current_state == "Submitted"`; expected `NDS_INTAKE_NOT_OPEN`.
**Impact:** After the legal close instant a department can still push a returned Need into review, and the screen's own guidance contradicts the command.

### AUD-NDS-007 — Acceptance does not recheck the unit or the content hash
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §8.2 `accept_need_revision` ("Recheck exact reviewer task, current unit, content hash and concurrency"), §4.9 ("Current UOM eligibility is rechecked at acceptance through the owner contract"), NDS11-AC-081 · **Module(s):** NDS · **Sources:** trace-needs C-04
**Evidence**
- `NDS/services/lifecycle.py:703-815` — `review_need` rechecks reviewer, maker-checker, task token and record version; it never calls `_validate_submission` (defined at 445, called only at 675 inside `submit_need`) or `_content_hash` (defined at 184).
- `NDS/services/events.py:77` — the accepted payload copies the stored `content_hash` and the unit id unchecked.
**Rule:** NDS §8.2 (line 628) and §4.9 (line 332), NDS11-AC-081 "checked at submission and acceptance".
**Reproduction / failing test sketch:** (static; not run) Submit a Need on unit `Each`; set `UOM.enabled = 0` for `Each`; HoD accepts; acceptance succeeds and `DepartmentalNeedAccepted.v2` carries the now-ineligible unit. Test: same sequence must raise at `accept`.
**Impact:** A Need can be accepted onto a unit that the governed catalogue no longer allows, and Planning receives it.

### AUD-NDS-008 — Unknown save/submit outcome is not resolved; a refresh mints a new key and can create a second root
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §8.4 (resolve or replay the same request with its unchanged key before any other write; persist the attempt correlation across refresh), NDS12-AC-008 · **Module(s):** NDS (Vue) · **Sources:** trace-needs C-16
**Evidence**
- `public/js/departmental_needs/DepartmentalNeeds.vue:734-757` — on an ambiguous failure of `submit`/`save-before-submit` the handler sets `submitUnknown.value = true` (line 756) and stops; nothing replays the request. A plain `save` that fails ambiguously only shows the error summary.
- `public/js/departmental_needs/data/needsApi.js:79` — `newIdempotencyKey(action)` mints a fresh UUID for every attempt; grep finds no `sessionStorage`/`localStorage` use for an attempt key in `DepartmentalNeeds.vue` or `data/`.
**Rule:** NDS §8.4 "Resolve/replay the same creation/save request with its unchanged key/payload before submitting or creating another record"; NDS12-AC-008.
**Reproduction / failing test sketch:** (static; not run) New form; drop the network after the server commits `save_need_draft` (no response); refresh and repeat the save: a second Need with a new reference is created because the key differs. `NeedEditorScreen.spec.js:126` only renders the notice.
**Impact:** Duplicate Need roots after a lost response; the "Checking the existing request…" wording promises a check that does not happen.

### AUD-NDS-009 — Disposition event uses a different enum and sequence than the approved wire contract
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §4.8 (line 311) and §7.4 (line 560: "Exact enum `Proceeding` or `Not proceeding this financial year`"); PLN v1.29 §7.6 (line 1037) · **Module(s):** NDS, PLN · **Sources:** trace-needs C-10; trace-planning F-13 (sweep-handoffs F-7 describes the same enum root cause and is owned by the hnd part)
**Evidence**
- `NDS/services/usage.py:256,329-330` — `DISPOSITION_NOT_PROCEEDING = "Not proceeding"`; any other value raises `NDS_FIELD_REQUIRED`. The doctype Select options are `Proceeding\nNot proceeding` (`NDS/doctype/need_planning_disposition_projection/need_planning_disposition_projection.json:18`).
- `PLN/services/dpp_validation.py:254` — the producer passes the same short constant, so producer and consumer agree with each other, not with the document.
- `PLN/services/dpp_validation.py:244,257` — `producer_sequence` is the DPP `submission_number` shared by every Need of the department; PLN §7.6 (line 1037) says it "is allocated transactionally per stable Need's disposition stream".
**Rule:** NDS §7.4 (line 560) and PLN §7.6 (line 1037), quoted above.
**Reproduction / failing test sketch:** (static; not run) As a Procurement Planner call `project_need_planning_disposition(departmental_need=N, need_revision=R, dpp_submission=S, disposition="Not proceeding this financial year", reason="<20+ chars>", source_event_id="e1", producer_sequence=1)`: returns `NDS_FIELD_REQUIRED`. Test: the in-repo producer's value must equal the approved enum string.
**Impact:** Any producer or consumer built to the approved contract is rejected; the two in-repo sides agree only because both diverge.

### AUD-NDS-010 — The Planning-event consumer lacks the versioning, conflict, ownership and ordering rules of §7.4–7.5
**Severity:** Medium · **Classification:** CODE DEFECT (the document marks the coordinated producer/consumer work as outstanding in NDS11-XD-001/002, which bounds severity) · **Doc:** NDS v1.16 §7.4 (line 556 `schema_version`; line 574 "Different payload under the same ID/sequence conflicts; preserve evidence and reject"), §7.5 · **Module(s):** NDS · **Sources:** trace-needs C-24 (and the authentication aspect of C-09, whose caller-identity part is owned by xc-authz item 12)
**Evidence**
- `NDS/services/usage.py:303-372` — no `schema_version` parameter or field exists for the disposition event.
- `NDS/services/usage.py:348-349` — `if frappe.db.exists(DISPOSITION_DOCTYPE, {"source_event_id": event_id}): return {... "idempotent": True ...}` for ANY payload; usage does the same at line 205; the intake projection never compares the id.
- `NDS/services/usage.py:340-342` — only `Departmental Need` existence is checked; `need_revision` is a plain Link (revision need not belong to the Need) and the disposition controller is an empty class (`need_planning_disposition_projection.py`, `pass`), so a disposition can name a revision of another Need or any submission id.
- `NDS/services/usage.py:350-353` — ordering key is `revision::submission`, not the Need's stream; usage has no sequence and orders on a caller-supplied `source_event_time` string (line 207).
- No retention of pending or gapped events, no replay; error codes `NDS_PLANNING_EVENT_INVALID`, `NDS_PLANNING_SYNC_PENDING`, `NDS_PLANNING_DEPENDENCY_UNAVAILABLE` are absent from `NDS/errors.py` (NDS §9 lists them).
**Rule:** NDS §7.4 (rejected/quarantined unknown schema; exact Need/revision/submission verification) and §7.5 (conflicting duplicates rejected with evidence; gap or out-of-order retained, never guessed; replay).
**Reproduction / failing test sketch:** (static; not run) As Planner: `project_need_planning_disposition(departmental_need=N1, need_revision=<a revision of N2>, dpp_submission="x", disposition="Proceeding", source_event_id="e", producer_sequence=1)` succeeds; repeating `source_event_id="e"` with `disposition="Not proceeding"` returns `idempotent: True` and changes nothing instead of conflicting.
**Impact:** Disposition and usage facts that gate withdrawal (see AUD-NDS-002) can be wrong or silently dropped without evidence.

### AUD-NDS-011 — check_accepted_need_withdrawal_dependency has no permission check
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 NDS-BR-019 ("direct routes … use the same server-side scope predicate"), §9 `NDS_SCOPE_DENIED` ("Disclose no protected record data") · **Module(s):** NDS · **Sources:** trace-needs C-07
**Evidence**
- `NDS/api.py:54` — `check_accepted_need_withdrawal_dependency = frappe.whitelist()(lifecycle.check_withdrawal_dependency)` (not guest; any logged-in account).
- `NDS/services/lifecycle.py:966-997` — the function calls neither `actor(...)` nor `require_view`; it returns `active_plan`, `active_plan_item` and `dependency_version` for any Need/revision names supplied.
**Rule:** NDS-BR-019 and §9 as quoted.
**Reproduction / failing test sketch:** (static; not run) Any signed-in user: `GET /api/method/kentender_procurement.departmental_needs.api.check_accepted_need_withdrawal_dependency?need=<need name>&accepted_revision=<revision name>` returns the Active plan and plan item of a Need the caller cannot read.
**Impact:** Disclosure of Plan/Plan-Item identifiers and inclusion status of any Need to any authenticated account (limited sensitivity; names must be guessed or learned elsewhere).

### AUD-PLN-001 — Active-plan funding is never marked stale when the Budget changes; Requisition authorisation keeps passing
**Severity:** Medium (was High; Budget `check_funding` still gates the money at authorisation) · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §5.3.4 (line 512: "While current funding evidence for an Active Plan is stale, new Requisition authorisation remains blocked."), PLN18-AC-033 · **Module(s):** PLN, REQ · **Sources:** trace-planning F-23
**Evidence**
- `PLN/services/plan_requisition.py:268,282` — eligibility uses `funding_confirmed = version.funding_state == "Confirmed"`, the stored column only; `:486` `authorise_requisition_drawdown` checks `funding_state ... != "Confirmed"` the same way.
- `PLN/services/plan_finance.py:89-104` — `funding_is_current` (digest comparison against the decided basis) exists but has no caller in the Requisition path (callers: `plan_finance.py:154`, `publication_pipeline.py:230`, `next_step.py`, `plan_governance.py:217,433`, `plan_read.py`).
- `PLN/services/plan_finance.py:342` sets `Stale` for an Active Version only inside `return_from_finance`; `plan_read.py:1159-1160` computes staleness for a Draft only and never writes.
**Rule:** PLN §5.3.4 line 512 as quoted; PLN18-AC-033 "its independent current affordability … checks continue to apply".
**Reproduction / failing test sketch:** (static; not run) Active plan with funding Confirmed. Reduce the Budget Line Version `approved_amount` below the planned total. `get_requisition_eligible_plan_item(...)` still returns `eligible: True`; HOPF `authorise_requisition_drawdown` succeeds and locks scope. `test_plan_requisition.py:247` sets `funding_state` by direct DB write, so production staleness is never exercised.
**Impact:** New Requisition authorisations proceed against Plan funding evidence the document says must block them (Budget's own reservation checks at the later gate are separate and were not assessed here).
**Verification:** CORRECTED — severity High -> Medium: the code claim holds (`plan_requisition.py:268,486` read only the stored `funding_state`; `funding_is_current` has no Requisition-path caller), but `authorise.py:112-117` calls Budget `check_funding` (`budget_check_reserve_contracts.py:206-248`, per-line available >= required) and refuses with `REQ_FUNDING_UNAVAILABLE`, so no money can be reserved beyond Budget's own availability; what is lost is the documented evidence-state block, not a funds bypass.

### AUD-PLN-005 — Strategy snapshot is taken at Plan Item save, not at final approval, and ignores the plan's fiscal year
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §7.4 (line 1021: "The snapshot call belongs to final Plan approval, not item formation … must not append duplicate Strategy snapshot evidence on retry"), line 1019 ("At final statutory approval, call STR `create_strategy_snapshot` …"), PLN-RI-033, §7.3 (line 1008 lists "FY/Plan period" as an input) · **Module(s):** PLN, STR · **Sources:** trace-planning F-16; sweep-handoffs F-9
**Evidence**
- `PLN/services/plan_workbench.py:516` — `strategy_gateway.snapshot_objective(objective_id=..., correlation_key=f"{item.plan_item_id}:{idempotency_key}")` inside `save_plan_item`; the key changes with every save.
- `PLN/services/strategy_gateway.py:64-75` — `snapshot_objective` calls `create_strategy_snapshot`; repository search finds no other caller.
- `PLN/services/plan_governance.py:517` (`approve_annual_plan`) and `PLN/services/publication_pipeline.py:48-62` (`commit_approved_plan`) never call STR; `strategy_approval_snapshot` is set to an objective path string (`publication_pipeline.py:62`).
- `PLN/services/strategy_gateway.py:32` — `resolve_strategy_context(as_of_date=frappe.utils.today())`; the plan's fiscal year is not passed, and `:33-34` swallows every exception into "" (shown as "no objectives").
**Rule:** PLN §7.4 lines 1019-1021 as quoted. For the fiscal-year point, line 1021 also says a new selection "must use the current eligible Strategy version", so the date-based choice is arguable; the missing FY input (line 1008) is the stated divergence.
**Reproduction / failing test sketch:** (static; not run) Change one item's objective twice with different idempotency keys: two STR snapshots/audit events are created while the plan is a Draft; approve: no snapshot id is stored and a changed Strategy version with the same objective id passes `_require_positive_predicates`.
**Impact:** Duplicate Strategy evidence on every edit and no deterministic approval-time lineage match.

### AUD-PLN-006 — Successor submission and activation recheck neither scope lock nor consumed value; removal takes no reason
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §5.4.4 (lines 555-556, 560: "Also enforce §5.4.6 at successor submission and activation"), PLN-RI-070, PLN18-AC-035, §7.2 (line 975: `RemovePlanItemInSuccessor` takes "Draft successor item ID; reason") · **Module(s):** PLN · **Sources:** trace-planning F-19
**Evidence**
- `PLN/services/publication_pipeline.py:218-238` — `_activation_blockers` checks only source correction, `funding_is_current` and predecessor change; no consumed-quantity, funding-identity or `scope_lock` test (`scope_lock.guard` is never called from this module).
- `PLN/services/plan_publication.py:137-140` — `_no_downstream_use` is true unless an Active `Plan Drawdown Reference` exists; no Tender hand-off, commitment, contract or permanent scope-lock test.
- `PLN/services/plan_publication.py:143-161` and `PLN/api.py:519` — `remove_plan_item_in_successor(plan_item, expected_record_version, idempotency_key)` has no reason parameter.
**Rule:** PLN §5.4.4 items 4-5 and the sentence at line 560, as quoted; line 975.
**Reproduction / failing test sketch:** (static; not run) Authorise a Requisition on item X (scope lock set), reverse the drawdown fully, `begin_plan_update`, `remove_plan_item_in_successor(X)`: allowed (`_no_downstream_use` true) although X is scope-locked; submit and activate: no recheck. Also: a source added to X in the successor Draft before a Requisition is authorised on the predecessor passes activation after the lock appears.
**Impact:** A successor can drop or enlarge an item that downstream procurement already relies on, because the checks run only at edit time.

### AUD-PLN-007 — Approved removals re-queue the source; removed items stay in the reviewed totals but not in the published plan
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §5.4.4 item 6 (line 557: "Treat an approved removal as an explicit accounted-for exclusion; do not immediately place the same source back in the consolidation queue.") · **Module(s):** PLN · **Sources:** trace-planning F-18
**Evidence**
- `PLN/services/plan_publication.py:74` — at activation the removed item's allocations are set to `allocation_state = "Removed in successor"`.
- `PLN/services/plan_read.py:264-267` — `_allocated_dpp_entries` counts only allocations in ("Draft", "Active"); `PLN/services/plan_governance.py:200-209` (`_validate_ready_to_submit`) then refuses submission of the next successor Draft until every accepted entry is allocated, so the removed source returns to the queue.
- `PLN/services/plan_publication.py:161` — in the successor Draft, removal sets `item_state = "Removed in successor"` while allocations stay "Draft"; `PLN/services/readiness.py:171,276` count items `!= "Dissolved"` (affordability and the reservation denominator) and `PLN/services/plan_governance.py:139,195` freeze them into the reviewed snapshot, whereas `PLN/services/plan_json.py:117` publishes only Draft/Active items.
**Rule:** PLN line 557 as quoted; PLN §5.5.3.1 (reservation share is of "the exact current complete" plan value).
**Reproduction / failing test sketch:** (static; not run) Active V1 with item X; V2 Draft removes X; submit, approve, activate V2; open V3 Draft: X's source shows unallocated and V3 submission is refused until re-allocated. Separately, in V2 Draft X still counts in `line_totals` and in `reservation_allocations` frozen into `submitted_snapshot`, but is absent from the V2 published JSON.
**Impact:** Finance and the Accounting Officer review a larger plan than the one published, and a removal is not durable across the next update.

### AUD-PLN-008 — A correction request can be "Resolved" against the unchanged Active Version
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §5.4.5 (line 572: "Resolve is allowed only after a referenced correcting Plan Version is Active and the correction result identifies the replacement eligible lineage … Close without change requires a reason"), PLN18-UX-23 · **Module(s):** PLN, REQ · **Sources:** trace-planning F-24
**Evidence**
- `PLN/services/plan_requisition.py:760-830` — `resolve_plan_item_correction_request` requires only that `correcting_plan_version` is Active (`:794`) and holds an Active item with the replacement id; it never requires it to differ from, or follow, the request's own plan version.
- `PLN/services/plan_requisition.py:714-724` — the gate is the Procurement Planner role.
**Rule:** line 572 as quoted; releasing the hold "without change" is the separate reasoned outcome.
**Reproduction / failing test sketch:** (static; not run) Correction request recorded against Active V1; Planner calls `resolve_plan_item_correction_request(correction_request, correcting_plan_version=V1, ...)`: status Resolved, hold recomputed, `PlanItemCorrectionOutcome.v1` sent to REQ with replacement lineage equal to the stopped version. Tests cover only a Draft target and a genuine successor (`test_plan_requisition.py:659,707`).
**Impact:** A Planner can release the authorisation hold and tell REQ a correction happened with no change and no recorded reason.

### AUD-PLN-009 — ReturnPlanVersion records no collective resolution and caps the reason at 500
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §7.2 (line 971: "required collective resolution where applicable"), §6.1 (line 855: "Board and Council decisions retain their collective resolution reference"), §4.1 (line 145: other reasons "capped at 1,000") · **Module(s):** PLN · **Sources:** trace-planning F-02 (item-context part dropped, see below)
**Evidence**
- `PLN/services/plan_governance.py:624` — signature `(task, reason, task_token, idempotency_key, user)`; `PLN/api.py:405` exposes the same four parameters; the stored decision is created with `return_reason=reason` and no `resolution_reference` (`plan_governance.py:642` calling `_decision`, which accepts `resolution_reference` at line 395).
- `PLN/services/plan_governance.py:631` — `if not (10 <= len(reason) <= 500)`.
- By contrast `approve_annual_plan` (`:535-536`) and `withdraw_approved_plan_for_correction` (`treasury.py:194-195`) require the reference for collective capacities.
**Rule:** PLN lines 971, 855, 145 as quoted.
**Reproduction / failing test sketch:** (static; not run) Site configured with a Board/Council statutory capacity: the statutory recorder calls `return_plan_version(task, reason="…10+ chars…", task_token, key)`: accepted, decision stored without a resolution reference. A 600-character reason: `PLN_ENTRY_INCOMPLETE`.
**Impact:** A collective statutory return carries no resolution evidence; reasons between 501 and 1,000 characters are refused.

### AUD-PLN-010 — Segregation chain omits SavePlanVersionDetails and the funding-reuse request
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §6.4 (line 892: "Author Annual Plan content, form/dissolve items, request Finance, or sign formal submission" blocks later Finance/AO/statutory decisions) · **Module(s):** PLN · **Sources:** trace-planning F-04
**Evidence**
- `PLN/services/planning_authorization.py:68-78` — `PLANNER_CHAIN_COMMANDS` lists FormPlanItems, DissolvePlanItem, SavePlanItem, ConfirmSplittingAdvisory, RequestPlanFundingConfirmation, SubmitConsolidatedPlan, SubmitCorrectedPlan, RemovePlanItemInSuccessor, BeginPlanUpdate; not `SavePlanVersionDetails` (journaled at `PLN/services/plan_workbench.py:568`).
- `PLN/services/plan_finance.py:189-199` — the reuse path of `RequestPlanFundingConfirmation` is journaled against a `Plan Finance Basis Reuse` document; `planning_authorization.py:380` builds `journal_targets = set(chain) | set(items) | set(tasks)`, which excludes it. A correction Draft's owner is excluded from the Planner set (`planning_authorization.py:373-374`).
**Rule:** PLN §6.4 as quoted.
**Reproduction / failing test sketch:** (static; not run) On a correction Draft, user P (Planner and Finance Confirmation Officer) calls `request_plan_funding_confirmation` and the earlier basis is reused (`action: confirmation_reused`); a different user signs and submits. `is_segregated(P, ACTION_FINANCE_DECIDE, plan_version=...)` is False and P can confirm funding for a plan P requested.
**Impact:** A narrow maker-checker gap on correction chains; other chain commands are covered.

### AUD-PLN-011 — Splitting confirmation is free text with no related-item set, rule Version or stale-finding check
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §7.2 (line 963: "reasoned response … Retain assessment evidence; … stale finding rejected"), PLN18-AC-074 (line 2436: "retains related records, rule Version and justification") · **Module(s):** PLN · **Sources:** trace-planning F-20
**Evidence**
- `PLN/services/plan_workbench.py:575-598` — `confirm_splitting_advisory(plan_version, confirmation, ...)` stores a 10-500 character string in `splitting_confirmation` (`:585,592`); no finding id, related item set or rule Version is accepted or stored; no stale-finding rejection.
**Rule:** lines 963 and 2436 as quoted.
**Reproduction / failing test sketch:** (static; not run) Confirm the advisory with any 10-character text while the related items later change: accepted; the stored value cannot show which items or rule Version it answered.
**Impact:** Legally material splitting accountability is not evidenced as specified (the advisory is advisory; mandatory method rules still block).

### AUD-PLN-012 — "Fixture-verified — not production law" passes every verification gate (spec gap)
**Severity:** Medium · **Classification:** SPEC GAP — decision for the owner: may a rule or profile whose status is `Fixture-verified — not production law` satisfy the production gates, or must a site mode reject it? · **Doc:** PLN v1.29 §10.2 (line 1444: "do not display the profile as a verified legal reference"), §5.5.3.1 line 761 ("absence of verified mandatory configuration cannot be reported as success"); CFG-CHG-002 v0.18 CFG17-AC-002 (line 1031) · **Module(s):** PLN, core · **Sources:** trace-planning F-26
**Evidence**
- `kentender_core/kentender_core/services/procurement_settings.py:42-43` — `VERIFICATION_FIXTURE = "Fixture-verified — not production law"`.
- `PLN/services/profiles.py:38` — `VERIFIED_STATUSES = (settings.VERIFICATION_FIXTURE, settings.VERIFICATION_VERIFIED)`, used at `PLN/services/readiness.py:291`, `PLN/services/profiles.py:98` and `PLN/services/plan_requisition.py:147`.
**Rule:** the documents prohibit displaying fixture rules as verified and forbid reporting missing verified configuration as success, but do not say whether the fixture status satisfies a gate.
**Reproduction / failing test sketch:** (static; not run) Seed the Open Tender profile and reservation rule with the fixture status; every submission and Requisition gate treats them as verified.
**Impact:** A production site carrying fixture-status rules passes all verification gates with no switch to reject them.

### AUD-REQ-003 — Preparer can also be the Procurement authoriser (no "self-authorisation" check beyond `submitted_by`)
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** REQ-CHG-001 v1.14 REQ19-AC-045, §7.3 bullet 4, §5.2 · **Module(s):** Requisitions · **Sources:** trace-requisition F-02 (F-02b part)
**Evidence**
- `REQ/services/authorise.py:103-104` — `if cstr(version.submitted_by) == actor: fail("REQ_SOD_BLOCKED")` is the only actor comparison; `prepared_by` is never compared.
- `REQ/services/lifecycle.py:213-235` — the actor who sends a Draft for department approval is written only to the command journal (`_journal`), not to the Version or a decision.
**Rule:** §7.3 bullet 4 only blocks the authoriser from being "recorded as the departmental submitting authority". REQ19-AC-045 adds "HOPF alone cannot prepare a departmental Draft. Dual-role actors exercise exact current capacity with no self-authorisation." The documents do not say whether the preparer (or sender) of a Draft may later be its Procurement authoriser.
**Decision the owner must make:** may an actor who prepared or sent a Draft authorise it as HOPF (dual-role Author + HOPF)? If not, `authorise_requisition` must also compare `prepared_by` and a recorded "sent by" actor.
**Reproduction / failing test sketch:** (static; not run) 1. User U holds Departmental Author (lead OU) and Head of Procurement Function; U prepares and sends a Draft; a different lead HoD approves and submits. 2. U calls `authorise_requisition` -> succeeds (`submitted_by` is the HoD).
**Impact:** A dual-role actor can carry a requisition from preparation to funded authorisation with only one other person (the HoD) in the chain.

### AUD-REQ-004 — HoD submission from "Awaiting Department Approval" skips the section 7.2 rechecks
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §7.2 · **Module(s):** Requisitions · **Sources:** trace-requisition F-05
**Evidence**
- `REQ/services/lifecycle.py:253-266` — the Awaiting branch only checks the task, the SoD rule and flips the already locked Version/package to "Submitted to Procurement" with `envelope.bump(...)`; it never calls `lock()` (lines 78-96: Planning eligibility, `compatibility.require_compatible`, `validation.validate`, digest) or `validation.validate`.
- `REQ/services/lifecycle.py:267-270` — only the Draft branch calls `lock(...)`.
**Rule:** §7.2 "Before departmental routing **or submission**, the server rechecks: ... current Planning eligibility and open balance; every field and row control ...; zero Blocking findings; supporting-file security and digest; product suitability ...; and canonical content digest."
**Reproduction / failing test sketch:** (static; not run) 1. Send a Draft for department approval. 2. Before the HoD acts, make the item ineligible (record a Planning correction request on it, or switch the template release off). 3. HoD calls `submit_requisition_to_procurement(..., task=<open task>)` -> succeeds and creates a Procurement task. Expected: `PLN_ITEM_AUTHORISATION_HELD`/`REQ_PRODUCT_UNSUPPORTED`/`REQ_PLAN_INELIGIBLE`.
**Impact:** An unauthorisable Version reaches the HOPF queue; the authorise-time recheck (`authorise.py:40-61`) still blocks money movement, so the cost is a dead task and a misleading status.

### AUD-REQ-005 — Category applicability of technical characteristics is not enforced server-side
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §6.3, REQ19-AC-009, §14.3 · **Module(s):** Requisitions · **Sources:** trace-requisition F-06
**Evidence**
- `REQ/services/catalogue.py:89` and `:151` — `Characteristic.applies(equipment_category)` and `characteristics_for(category)` exist; a repo-wide grep over non-test `*.py` in the module finds no caller (only `tests/test_catalogue.py:60-61`).
- `REQ/services/draft_commands.py:507-520` (`_visible_technical`) and `:731-743` (`add_technical_requirement`) look the key up in `CATALOGUE_BY_KEY` and validate the value only; the item category is never consulted.
- `REQ/services/validation.py:234-236` — only checks that the key exists in the catalogue (`CONTROL_INVALID` otherwise).
- `REQ/services/catalogue.py:123` — `print_speed` is declared `frozenset({"Printer"})`.
- `REQ/tests/test_draft_commands.py:159-172` — pins that after changing Laptop to Desktop the Confirmed rows are kept.
**Rule:** §6.3 "Only characteristics applicable to the selected category are offered." REQ19-AC-009 "Only category-applicable characteristics and their released controls are accepted." §14.3 "Changing an equipment category revalidates its characteristics."
**Reproduction / failing test sketch:** (static; not run) 1. Draft with Monitor items. 2. `add_technical_requirement(values={"characteristic_key": "print_speed", "applies_to_scope": "All items", "value": 30, ...})` -> accepted as a Confirmed row; passes `validation._technical_support`; enters the handoff `technical_requirements`. Expected `REQ_CONTROL_INVALID`.
**Impact:** A Printer-only obligation can be imposed on monitors (and Laptop-only rows survive a category change), so the Tender inherits requirements that do not apply to the goods.

### AUD-REQ-006 — Brand/restrictive-term Blocking finding is applied only to technical TEXT rows
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §6.3 rules, §6.5 Blocking findings, REQ19-AC-018 · **Module(s):** Requisitions · **Sources:** trace-requisition F-29 row 75
**Evidence**
- `REQ/services/validation.py:250` — `if ch.control == TEXT and restrictive_terms.is_restrictive(text_value, reason=row.get("reason", "")):` is the only call site of `is_restrictive` in the module (grep over `services/*.py`).
- Free-text fields that reach the Tender and are not scanned: item `item_name`/`intended_use`, acceptance `pass_condition`, related-service `required_result`/`quantity_or_coverage`, supporting-material `title`/`purpose`, and the `other` value of non-TEXT controls (`catalogue.py:210-212,226-229`).
- `REQ/services/restrictive_terms.py:13-24` — the detector exists (brand and platform lists).
**Rule:** §6.3 "A brand, model, proprietary certification or named technology triggers a Blocking finding unless the text includes an approved `or equivalent` treatment and a recorded functional reason." §6.5: "a brand or restrictive term lacks permitted equivalent treatment" is Blocking. REQ19-AC-018 "Brand/restrictive wording without permitted equivalence treatment blocks submission."
**Reproduction / failing test sketch:** (static; not run) 1. Draft; add an acceptance requirement with `pass_condition="Delivered units must be Dell Latitude 5440 devices"` (or an item named "Dell Latitude 5440"). 2. `validate_requisition` -> no `RESTRICTIVE_TERM` finding; submission and authorisation succeed. Expected: Blocking finding.
**Impact:** Brand-restrictive wording, a legally sensitive defect in a tender specification, passes every REQ gate outside the one control type scanned and flows into the handoff.

### AUD-REQ-007 — Draft and in-review requisitions are readable by every site-wide role
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** REQ-CHG-001 v1.14 §8 role table, §7.5 invariant 15 · **Module(s):** Requisitions · **Sources:** trace-requisition F-08
**Evidence**
- `REQ/services/requisition_roles.py:27` — `SITE_WIDE_ROLES = (HOPF, Procurement Planner, Procurement Officer, Auditor)`.
- `REQ/services/requisition_authorization.py:124-142` (`require_requisition_reader`) returns for any of those roles for any state; `:262-271` (`_site_wide_condition`) gives them an unrestricted list condition.
- `REQ/services/read.py:166-195` — the workspace `register` includes Draft roots for readers; `REQ/services/draft_commands.py:924-930` (`validate_requisition`) returns findings and a preview digest to any reader.
- `REQ/tests/test_requisition_authorization.py:65-69` — pins the Auditor reading a prepared requisition as intended.
**Rule:** §8: Procurement Officer "No Draft right in Requisitions by virtue of this role"; Planner "Neutral read of Planning lineage and drawdown projection"; HOPF "View the complete submitted Requisition". §7.5 invariant 15: unauthorised requests reveal no record. The document is silent on whether "no Draft right" and "neutral read" cover reading Draft content.
**Decision the owner must make:** may Planner, Procurement Officer and Auditor (site-wide) read Draft and in-review content, or only Submitted/Authorised/Revoked states (as the Accounting Officer oversight read is restricted by `OVERSIGHT_READ_STATES`)?
**Reproduction / failing test sketch:** (static; not run) As a Procurement Officer, `get_requisition_workspace()` lists every department's Drafts in `register`; `get_requisition_record(<draft>)` returns the editor projection read-only.
**Impact:** Unsubmitted departmental work (requirements, quantities, values) is visible site-wide.

### AUD-REQ-008 — "Purchase ready for requisition" does not clear for an occupied item and the start surfaces carry no hold wording
**Severity:** Medium · **Classification:** CODE DEFECT (tension with doc §13.13; see note) · **Doc:** REQ-CHG-001 v1.14 §9.1C, REQ112-AC-002, REQ112-AC-004 · **Module(s):** Requisitions · **Sources:** trace-requisition F-09; F-29 rows 158-160
**Evidence**
- `REQ/services/read.py:228-246` — when `records.open_root_for(...)` returns a root, the row is still appended with an `existing` link unless that root is in the actor's own `your_work` (line 236, Drafts only); Awaiting, Submitted and Authorised roots therefore leave the item in the Ready list.
- `REQ/services/read.py:238-246` and `:305-356` (`get_start_preview`) — neither the ready row nor the preview contains a hold field; the word "hold" occurs in `read.py` only at 634-663 (authorisation task).
- `kentender_procurement/kentender_procurement/public/js/procurement_requisitions/components/WorkspaceScreen.vue:165-166` (existing rows listed separately) and `StartDialog.vue`: no hold wording (grep `-i hold` over both returns nothing).
**Rule:** §9.1C "Clears when: ... a Requisition root occupies the stable item's open slot"; REQ112-AC-002 "The item clears when a root occupies the open slot"; §9.1C Correction hold "Its row states the existing hold wording from §9.1 beside **Start requisition**"; REQ112-AC-004 "remains listed with the hold wording". Note: §13.13 also defines an "Existing open requisition" state with action "Open existing requisition", so the doc is not fully consistent about whether an occupied item stays in the list as a pointer.
**Reproduction / failing test sketch:** (static; not run) 1. Author sends a Draft for department approval; `get_requisition_workspace()` still lists the Plan Item in `ready_to_start` with `existing`. 2. Record a Planning correction request on a different eligible item; its Ready row carries no hold text and the start preview has no hold state.
**Impact:** Users are told a purchase is ready when a requisition already occupies it, and are not warned that authorisation is on hold until the Authorise step.

### AUD-REQ-009 — `funding_source` is not sent to Budget and is not in the handoff
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §5.12, §9.1A · **Module(s):** Requisitions, Budget, Planning · **Sources:** trace-requisition F-10; F-29 row 154
**Evidence**
- `REQ/services/authorise.py:62-72` (`funding_rows`) — each Budget row has `budget_line, plan_source_allocation, drawdown_line_id, source_organisation_unit, amount` and no `funding_source`.
- `kentender_budget/kentender_budget/services/budget_check_reserve_contracts.py:160-170` normalises a missing `funding_source` to `""`, and `:196` — `if row["funding_source"] and row["funding_source"] != entry["line_version"].funding_source:` (BUD-BR-008) never fires for REQ.
- `REQ/services/handoff.py:49,62-89` — per-line `budget_line` only; no funding source anywhere in the payload.
- `kentender_procurement/kentender_procurement/procurement_planning/services/plan_requisition.py:234-259` — the Planning projection carries `budget_line` but no funding source (grep `funding_source` in `procurement_planning/doctype` also finds nothing).
**Rule:** §5.12 "planned method, schedule, Budget Line and funding source". §9.1A "REQ supplies its exact Version ... funding source/currency/precision with the array."
**Reproduction / failing test sketch:** (static; not run) Authorise any requisition and read `Authorised Requisition Handoff.payload_json`: no `funding_source`; call `check_funding` with a deliberately wrong `funding_source` for the same lines to show Budget would refuse it, whereas REQ never supplies one.
**Impact:** Budget's allocation-versus-line funding-source equality is never exercised for requisitions and the Tender does not see the funding source; the Budget Line itself fixes the source, so the blast radius is limited.

### AUD-REQ-010 — Supporting files: no private/ownership check, "Not scanned" accepted, no download predicate
**Severity:** Medium · **Classification:** SPEC GAP (scan fallback) with CODE DEFECT (private/ownership) · **Doc:** REQ-CHG-001 v1.14 §5.10, §8 final paragraph · **Module(s):** Requisitions, Core · **Sources:** trace-requisition F-15
**Evidence**
- `CORE/services/file_integrity.py:71-74,82` — `scanner_result` returns `NOT_SCANNED` ("Not scanned — no scanner configured", line 27) when no scanner hook answers; `check_file` (lines 89-119) rejects only an `Infected` verdict (line 119-120) and never reads `File.is_private`, `attached_to_*` or owner.
- `REQ/services/files.py:20-30` and `REQ/services/draft_commands.py:889-893` — `add_supporting_material` runs `files.check_file(values.get("file"))` on any File name supplied and stores `file_digest`.
- `kentender_procurement/kentender_procurement/hooks.py:192` — the only `kt_file_scanners` entry is the BDS simulation-only test scanner; `hooks.py:457-459` registers only `File.on_trash`, no read predicate for Files.
**Rule:** §5.10 `file_id` "Required private Frappe File"; `file_digest` "Generated after malware and readability checks." §8 "Every list, count, direct route, file download and command applies the same registered predicate." Decision for the owner: whether a file with "Not scanned" may be attached or must fail closed when no scanner is configured.
**Reproduction / failing test sketch:** (static; not run) 1. As user A upload a public (`is_private = 0`) `.pdf`. 2. As user B (Departmental Author) call `add_supporting_material` naming A's File -> accepted, digest returned, check_result "Not scanned — no scanner configured". 3. Name any other readable private PDF File of another module -> also accepted and its SHA-256 is stored on the requisition (a content oracle).
**Impact:** A requisition can reference a public or someone else's file as a governed obligation document with no malware verdict; reviewers downstream may be unable to read it, and its digest becomes part of the immutable Version.

### AUD-TND-003 — Accounting Officer can still authorise publication after returning the package; the return item is orphaned
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 §5.1, TPR16-AC-015 · **Module(s):** Tenders · **Sources:** trace-tenders F-02
**Evidence**
- `TND/services/read.py:414` — only the read hides the control (`... and not handoffs.open_for(root, handoffs.RETURNED_BY_AO) ...`).
- `TND/services/publication.py:49-77` — `authorise_tender_publication` checks status, segregation, `ao_task` (only if `task` is passed), digest; no test of an open `RETURNED_BY_AO` hand-off. `return_approved_tender` cancels the AO authorisation task (`publication.py:255`) so `ao_task` is `None` afterwards.
- `TND/services/publication.py:108` — on authorisation only `REVIEW_WITHDRAWN` hand-offs are closed; `TND/services/lifecycle.py:290-291,301` — Reopen (which would close `RETURNED_BY_AO`) is refused once `root.publication` is set.
**Rule:** §5.1 "While the return is open the Accounting Officer has neither **Authorise publication** nor **Return**." TPR16-AC-015 "...is offered neither **Authorise publication** nor **Return**. Reopen, or a Requisition correction, clears the hand-off."
**Reproduction / failing test sketch:** (static; not run) 1. AO `return_approved_tender(reason>=20 chars)`. 2. AO `authorise_tender_publication(tender, expected_record_version=<returned record_version>, idempotency_key=<new>)` with no `task` -> commits. 3. HOPF My Work still shows "Review Tender ... returned by the Accounting Officer"; Reopen is refused with `TND_PUBLICATION_STARTED`. Expected: step 2 raises `TND_STALE_VERSION`.
**Impact:** A server call (not the UI) lets the AO bypass the HOPF correction they just requested; the HOPF is left with a task that can never clear.

### AUD-TND-004 — Non-material addendum rows for clarification deadline and others have no effect on the Tender or definition
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 §3, §4.8, §4.9, §5.6 · **Module(s):** Tenders · **Sources:** trace-tenders F-06
**Evidence**
- `TND/services/addenda.py:71-72` — `clarification_deadline` and `submission_deadline` are offered as non-material `affected_reference` rows.
- `TND/services/bid_definition.py:58` (`_ADDENDUM_TARGETS`, otherwise unused) and `:281-301` — `apply_addenda` applies only `delivery_location`, `tender_title`, `inspection_location`, `contract_contact_office`, `pre_tender_meeting`, plus the submission deadline when `deadline_extension_required`.
- `TND/services/addenda.py:462-465` — updates only `submission_deadline`; no code writes `Tender.clarification_deadline` after publication (grep `clarification_deadline` in `TND/services` shows writes only at `lifecycle.py:144` and `publication.py:110`).
- `TND/services/clarifications.py:73-76` — `TND_CLARIFICATION_LATE` is judged against `root.clarification_deadline`.
**Rule:** §4.8/§5.6 the successor definition is built "from the current effective definition plus this exact addendum"; §3/§4.9 a clarification at or after the stated clarification deadline is rejected.
**Reproduction / failing test sketch:** (static; not run) Draft an addendum with `affected_reference_key="clarification_deadline"`, a revised value, reason (20+ chars) and materiality statement; issue and confirm all channels. The issued notice states the new clarification deadline, but `Tender.clarification_deadline` and the Effective definition are unchanged, so `receive_tender_clarification` still rejects questions after the old deadline.
**Impact:** The published addendum says one thing and the system enforces another, so bidders can be told a deadline moved that the system still applies; likewise a corrected `inspection_location` is free text without validation (`addenda.py:190-204`).

### AUD-TND-005 — The conflicting-confirmation audit event is written and then rolled back with the refusal
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 §5.8 item 10, §12.1 · **Module(s):** Tenders · **Sources:** trace-tenders F-07 (the generic denial-event root cause is owned by the xc-core part, "denial events never written / rolled back on throw")
**Evidence**
- `TND/services/channel_confirmation.py:183-190` — `events.emit(... event_type="ConfirmationConflictRejected" ...)` is immediately followed by `fail("TND_PUBLICATION_ALREADY_CONFIRMED", ...)`; the emit is outside `envelope.atomic`, so it lives in the request transaction that the raised error rolls back (Frappe rolls back an uncaught exception in a whitelisted request; static reasoning, not run).
- `TND/tests/test_publication.py:347-354` — passes only because the test catches the exception inside one test transaction before asserting `events.exists(...)`.
**Rule:** §5.8(10) "a conflicting confirmation is rejected and preserved for audit." §12.1 "Rejected commands record a security or operational audit fact where policy requires it."
**Reproduction / failing test sketch:** (static; not run) Via HTTP call `confirm_publication_channel` for a Confirmed channel with a different `available_at`; get the refusal; query `Tender Event` for `ConfirmationConflictRejected` -> expected one row, today none.
**Impact:** The audit trail required for conflicting confirmations is lost in production although the test suite shows it as present.

### AUD-TND-006 — A Planning refusal of the invitation actual is recorded and never retried
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 §5.5 item 7, TPR09-AC-079, TPR-IMP-033 · **Module(s):** Tenders, Planning · **Sources:** trace-tenders F-08
**Evidence**
- `TND/services/planning_gateway.py:50-55` — on `ProcurementPlanningError` the event is `mark_rejected` and the function returns `{"ok": False, ...}`.
- `TND/services/publication.py:142-148,175` — `confirm_tender_published` returns early once `publication_status == Published`, and the only caller of `publish_invitation_actual` is `publication.py:175`; the only other caller is a test (`TND/tests/test_publication.py:381`).
- `kentender_procurement/kentender_procurement/hooks.py:481-500` — the scheduler jobs listed include no Planning-event retry.
**Rule:** TPR09-AC-079 "Owner-contract failure ... supports safe idempotent recovery." §5.5(7) "Planning receives exactly one actual invitation event for `published_at`."
**Reproduction / failing test sketch:** (static; not run) Make `schedule.record_tender_milestone_actual` raise `ProcurementPlanningError` during the final channel confirmation; the Tender becomes Published, the `TenderPublished` event is `Rejected`, nothing later re-sends it and Planning never records the actual date.
**Impact:** Planning's schedule can permanently miss the actual invitation date for a published Tender.

### AUD-TND-007 — Package-digest recomputation makes every unauthorised Tender Version fragile to any new CATALOGUE control
**Severity:** Medium · **Classification:** CODE DEFECT (latent) · **Doc:** TPR-CHG-001 v0.17 §4.2, TPR16-AC-018 · **Module(s):** Tenders · **Sources:** trace-tenders F-05
**Evidence**
- `TND/services/controls.py:247-259` — `normalise` emits a key (None when blank) for every field in `CATALOGUE`; `TND/services/serializer.py:293-300` (`officer_state`) normalises the stored payload through it.
- `TND/services/controls.py:41` — the only exemption is `DIGEST_OMIT_WHEN_EMPTY = ("shortened_period_reason",)`, applied at `TND/services/serializer.py:451-453`.
- `TND/services/lifecycle.py:238` (approval) and `TND/services/publication.py:77` (authorisation) compare the live recomputed `package_digest` with the stored one; `TND/services/review.py:155-160` recomputes the inherited snapshot digest live.
- `TND/services/errors.py:76` — the failure surfaces as the generic `TND_STALE_VERSION` ("Another user changed this Tender. Reload before continuing.").
**Rule:** §4.2 `package_digest` covers "every inherited/officer/generated value"; v0.16 left the shortened-period reason out while empty so earlier Versions "still verify"; TPR16-AC-018.
**Reproduction / failing test sketch:** (static; not run) Monkeypatch one extra optional entry into `controls.CATALOGUE`; recompute `serializer.package_digest` for a stored Submitted or Approved Version; it differs from `version.package_digest`, so `approve_tender_package`/`authorise_tender_publication` fail `TND_STALE_VERSION`. Published Tenders are not affected (nothing recomputes the digest after publication; confirmations compare stored digests, `publication.py:150-151`).
**Impact:** The next control added to the catalogue (or any change to grouping or the v1.4 translation in `snapshot._handoff_v14_names`) silently invalidates every in-flight Tender, with a misleading error, until each is returned or reopened and reworked.

### AUD-TND-008 — "Prepared by" for segregation is only the person who started the Tender
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** TPR-CHG-001 v0.17 §6, TPR09-AC-035/AC-039 · **Module(s):** Tenders · **Sources:** trace-tenders F-13; sweep-sod F5
**Evidence**
- `TND/services/draft_commands.py:128` — `prepared_by` set only at StartTender; `:152-189` (`save_tender_draft`) requires `authz.require_officer` and never records the editor; `TND/services/lifecycle.py:87,185,299` carry `prepared_by` forward unchanged.
- `TND/services/lifecycle.py:205-211` and its callers (`lifecycle.py:225`, `publication.py:62,252`) test only `prepared_by`, `submitted_by`, `approved_by`.
**Rule:** §6 "The person who prepared or submitted a Version cannot approve it as HOPF ... Checks use the immutable Version audit, not role labels alone." The document does not define "prepared" (creator or every editor). Decision for the owner: does "prepared" include every person who saved a value (journalled in `TenderDraftSaved` events, which carry the editor)?
**Reproduction / failing test sketch:** (static; not run) Officer O1 starts the Tender; user H (Procurement Officer + Head of Procurement Function) edits values with `save_tender_draft`; O1 submits; H calls `approve_tender_package` -> allowed (`prepared_by = O1`, `submitted_by = O1`).
**Impact:** A person who substantively authored the package can approve it as HOPF.

### AUD-TND-009 — Cancellation grounds are a code-owned, unverified list
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** TPR-CHG-001 v0.17 §4.10, §5.7, TPR09-AC-066 · **Module(s):** Tenders · **Sources:** trace-tenders F-09
**Evidence**
- `TND/services/cancellation.py:34-45` — `GROUNDS_SOURCE = "... s.63(1) — wording verification pending (FOLLOW_UPS FU-06)"` and a fixed tuple of eight grounds.
- `TND/services/cancellation.py:71,119` — `if ground not in GROUND_LABELS: fail(...)` is the only validation (recommend and cancel); no applicability, verification status or configuration lookup.
**Rule:** §4.10 `ground` "One configured, verified lawful ground from the applicable rule set." §5.7 "A configured verified lawful ground and specific reason are mandatory." The document names no reference kind or configuration surface for the grounds. Decision for the owner: where the verified ground set is configured (and whether the code list stays as a fallback until verified).
**Reproduction / failing test sketch:** (static; not run) AO `cancel_tender(ground="FORCE_MAJEURE", reason=<20+ chars>, ...)` on any `Published — open` Tender -> accepted.
**Impact:** A final, irreversible cancellation can rest on a ground whose wording the code itself marks unverified.

### AUD-TND-010 — Publication/addendum evidence is accepted with "Not scanned"
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** TPR-CHG-001 v0.17 §4.7, TPR09-AC-050 · **Module(s):** Tenders, Core (shared root cause with AUD-REQ-010) · **Sources:** trace-tenders F-21
**Evidence**
- `TND/services/channel_confirmation.py:172` — `file_integrity.check_file(cstr(evidence_file).strip(), fail=...)` is the evidence check for every channel confirmation.
- `CORE/services/file_integrity.py:71-74,82,118-120` — with no scanner answering, `check_result` is "Not scanned — no scanner configured" and only an `Infected` verdict fails.
- `kentender_procurement/kentender_procurement/hooks.py:192` — the only `kt_file_scanners` entry is the simulation-only BDS test scanner.
**Rule:** TPR09-AC-050 "Uploaded evidence is scanned, digested and retained; failed or rejected uploads cannot confirm a channel." The document does not say whether unscanned evidence may confirm publication. Decision for the owner: fail closed when no scanner is configured, or accept and display "Not scanned".
**Reproduction / failing test sketch:** (static; not run) On a site without `kt_bds_simulation_environment`, confirm a publication channel with a valid PDF; the confirmation succeeds with `evidence_check_result = "Not scanned — no scanner configured"`.
**Impact:** The legal publication evidence may be an unscanned file; the first channel confirmation that publishes a Tender does not meet AC-050 as written.

### AUD-EVL-004 — `retry_delivery` completes and hands over a report with no suspension, roster or validity recheck
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §5.5 (line 164), §5.7 (line 180) · **Module(s):** Evaluation, Award · **Sources:** trace-evaluation F-3 (rows 78, 116, 207)
**Evidence**
- `P/bid_evaluation/services/signing.py:177-188` — `_complete_and_deliver` runs `recheck(doc)` (`:180`, roster + `guards.open_case`) and the validity withdrawal (`:182-185`) before `complete_record`/`deliver`; a `Paused` result leaves the case in Signing (`:181`)
- `P/bid_evaluation/services/signing.py:221-235` — `retry_delivery` checks only the secretary and `record_versions.missing_proofs`, then `out = deliver(doc, version, idempotency_key)` (`:235`), which sets `state="Report sent"` and calls `notify_consumers` (Award hand-off, `:215-217`)
**Rule:** EVL line 164: "Before freezing and again before delivery, recheck current source impact, roster, cancellation/suspension and tender validity … If the frozen report still makes that recommendation … return it to Reviewing … A suspension alone preserves the signing state but pauses completion." Line 180: suspension "pauses new committee decisions, requests and report signing".
**Reproduction / failing test sketch:** (static; not run) 1. All members sign with `simulation.set_controls(delivery_outcome="Failed")` (as `P/bid_evaluation/tests/test_evl_report.py:120`). 2. `tender_events.record_simulated_event(kind="Suspension", ...)` (or move the clock past `validity_end` for a positive recommendation). 3. Secretary calls `signing.retry_delivery(...)`. Expected `EVL_SUSPENDED` / return to Reviewing. Predicted: Delivered; Award receives a report that should be paused or withdrawn. Also the `Paused` branch (`:180-181`) leaves signed proofs whose only exit is this unguarded retry.
**Impact:** A report that must be paused (suspension) or withdrawn (expired validity, roster change) can still be delivered to the Head of Procurement and Award.

### AUD-EVL-005 — A pending opening-supplement impact does not block freezing, and a "material" impact triggers no recalculation
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §5.5 (line 164), §5.6 (line 174) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-8 (rows 111, 126, 209)
**Evidence**
- `P/bid_evaluation/services/correction.py:224` — a received supplement is stored with `"impact": "Pending"`
- `P/bid_evaluation/services/signing.py:47-79` — `readiness` has no reference to source-event impact (grep "impact" in `signing.py`/`lifecycle.py`/`checks.py` returns nothing); `recheck` (`signing.py:169-174`) also omits it
- `P/bid_evaluation/services/correction.py:259-262` — `assess_supplement` with "Findings need review" only calls `lifecycle.withdraw_signing(...)`; no `checks.run` or re-evaluation follows
**Rule:** EVL line 174: "Before delivery, a member must record whether they affect any finding; material changes require recalculation and, if already signing, a new report"; line 164: recheck "current source impact" before freezing and before delivery.
**Reproduction / failing test sketch:** (static; not run) 1. In Reviewing, `correction._receive_supplement(tender, "BOP-SUPP:X", supplement)` (or let `consume_supplements` run). 2. Resolve all requirements; secretary `send_for_signing`. Predicted: frozen and deliverable with the supplement impact still Pending. 3. Member `assess_supplement(impact="Findings need review")` before delivery: signing is withdrawn but the check run is not repeated, so findings/ranking are unchanged. No test covers receive/assess/head_review (EVL-A12).
**Impact:** A report can be frozen and delivered ignoring corrected opening facts that the document says must be assessed (and recalculated) first.

### AUD-EVL-006 — A participant who is no longer an eligible member can still sign the verification report
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §5.4 (line 152), EVL-A08 (line 668) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-11 (rows 103, 147, 205)
**Evidence**
- `P/bid_evaluation/services/diligence.py:106-108` — `record_observation` requires `user in participants(plan)` and `findings.require_member(doc, user)`
- `P/bid_evaluation/services/diligence.py:195` — `sign` checks only `if not plan or user not in participants(plan)`; no `require_member`; `my_targets` (`:177-185`) is also membership-by-target only
- `P/bid_evaluation/services/diligence.py:150` — `send_for_signing` (lead) likewise does not re-check eligibility; a roster change/conflict supersedes only the main report (`lifecycle.withdraw_signing`, `lifecycle.py:27-54`), not the verification plan
**Rule:** EVL line 152: due diligence "is carried out by named eligible members of the current evaluation committee"; EVL-A08 line 668: "scope/roster changes … are retained".
**Reproduction / failing test sketch:** (static; not run) 1. Plan with participants Grace and Ruth, observations recorded, lead freezes (`diligence.send_for_signing`). 2. Ruth `declare_interest("Declare a conflict")` or is replaced by the AO. 3. Ruth calls `diligence.sign(...)`. Expected refusal. Predicted: proofs recorded and the verification report completes (`report_state="Signed"`) with a signature from an ineligible person. `P/bid_evaluation/tests/test_evl_diligence.py:79` covers only the happy path.
**Impact:** A conflicted or replaced member's signature can complete the due-diligence record that supports the recommendation.

### AUD-EVL-007 — `return_report` has no check that the delivery is the current, unreturned one
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §5.6 (line 168-172), EVL-A11 · **Module(s):** Evaluation · **Sources:** trace-evaluation F-12 (rows 26, 121, 152, 208)
**Evidence**
- `P/bid_evaluation/services/correction.py:55-57` — `_delivered` returns the latest `status="Delivered"` delivery by `delivered_at`; a returned delivery keeps `status="Delivered"` (only `review_state` changes, `:114-116`)
- `P/bid_evaluation/services/correction.py:94-106` — `return_report` checks recipient, `guards.closed` and downstream status, but not `delivery.review_state` nor `doc.state`
- `P/bid_evaluation/services/correction.py:120` — `records.bump(doc, state="Reviewing", ...)` unconditionally
- `P/bid_evaluation/services/signing.py:89` — `send_for_signing` only requires `doc.state == "Reviewing"`; `lifecycle.signing_report` (`lifecycle.py:23-24`) returns one arbitrary Signing version by `get_value`
**Rule:** EVL §5.6 / EVL-A11: a return "reopens the evaluation as Reviewing and prepare[s] a new numbered report"; delivered report preserved; new version needs fresh signatures. Nothing authorises a return of an already-returned delivery while its successor is being signed.
**Reproduction / failing test sketch:** (static; not run) 1. Deliver v1; Head returns it (case Reviewing); secretary freezes v2 (case Signing, v2 collecting proofs). 2. Head calls `return_report` again with another comment. Predicted: v1 is re-marked Returned with the new comment, case state regresses to Reviewing while v2 is still in state Signing; `send_for_signing` can then freeze a v3 while v2 still holds proofs (two Signing versions; `signing_report` picks one by `get_value`). `P/bid_evaluation/tests/test_evl_oversight.py:276,298` return once only.
**Impact:** A repeated return corrupts the case/report state machine and can leave two versions in Signing.

### AUD-EVL-008 — Opening exceptions, including "Comment for Evaluation", are handed over but never read by Evaluation
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §5.1 (line 126), §6 (line 186) · **Module(s):** Evaluation, Bid Opening · **Sources:** trace-evaluation F-19 (row 63)
**Evidence**
- `P/bid_opening/services/completion.py:35-36,45` — the hand-off carries `"exceptions": [{..., "for_evaluation": x.exception_class == "Comment for Evaluation"}]` and each package's `render_digest`
- `P/bid_evaluation/services/intake.py:51-124` — `receive_opening_package` reads packages, register and `opening_record` only; grep `exceptions|render_digest` in `P/bid_evaluation/services/` matches only a docstring (`intake.py:10`); grep for `for_evaluation` outside Bid Opening and tests finds no consumer
- `P/public/js/bid_opening/screens/OpenBidsScreen.vue:73` — Bid Opening offers a form headed "Comment for Evaluation" whose content therefore reaches no Evaluation screen or report
**Rule:** EVL §5.1 line 126: "Accept one verified nonempty BOP completion, with unchanged packages, the issued definition/mappings, register, minutes, opening exceptions and exact source versions"; line 186: `ReceiveOpeningPackage` carries "register/minutes and exceptions".
**Reproduction / failing test sketch:** (static; not run) 1. In Bid Opening record a "Comment for Evaluation" on an entry and complete the opening. 2. After Evaluation intake, search every `reads.resolve`/`reads.bid`/report output for the comment text: absent. Test sketch: `completion` payload with one exception; after `intake.receive_opening_package` assert the exception is stored/readable by the committee.
**Impact:** Observations the opening committee explicitly directed to Evaluation are silently dropped.

### AUD-EVL-009 — Clarification-reply attachments bypass the shared upload integrity check
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §5.3 (line 142), §10 D06 (line 583) · **Module(s):** Evaluation, Bid Submission · **Sources:** trace-evaluation F-10 (row 92)
**Evidence**
- `P/bid_evaluation/services/clarification.py:302` — `ATTACHMENT_TYPES = ("application/pdf", "image/png", "image/jpeg")` is matched against the client-asserted `media_type` (`:317`)
- `P/bid_evaluation/services/clarification.py:316` — `base64.b64decode(..., validate=False)`; only emptiness and a 5 MB cap are checked; the bytes are stored in `attachments_json`
- `P/bid_submission/services/evidence.py:90` — Bid Submission runs every upload through `kentender_core.services.file_integrity.check_file` (`:84` `file_integrity.unreadable`); Evaluation never calls it
**Rule:** EVL line 142: "Supporting files are restricted to the question and shared upload security limits"; line 583: "configured BDS file limits and security validation".
**Reproduction / failing test sketch:** (static; not run) As an authorised supplier call `submit_clarification_reply(attachments=[{"filename":"x.pdf","media_type":"application/pdf","content_base64": base64(b"MZ\x90 not a pdf")}])`. Predicted: accepted and later exposed to committee members. Bid Submission refuses the same bytes.
**Impact:** A supplier can place an unvalidated file (any bytes labelled PDF/image) before committee members.

### AUD-EVL-010 — A conflicted or unavailable member who is also the secretary keeps bid access
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §3 (lines 59-61, 67) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-4 (row 15)
**Evidence**
- `P/bid_evaluation/services/reads.py:62` — `bids = (v["eligible"] or v["secretary"] or v["auditor"]) and not v["technical"]`
- `P/bid_evaluation/services/next_steps.py:47-56` — `viewer()` sets `secretary` independently of `conflicted`/`unavailable`
- `P/bid_evaluation/services/secretary.py:26-61` — the Head of Procurement may appoint themselves or a procurement officer; the secretary may also be an appointed member (EVL line 67)
**Rule:** EVL line 67: "A declared conflict stops that person's bid access immediately"; line 61: "Specific appointment plus conflict clearance governs committee access".
**Reproduction / failing test sketch:** (static; not run) HoP assigns member M as secretary; M declares a conflict; call `reads.bid(tender_reference, bid, user=M)` and `reads.evidence(...)`. Expected Not found; predicted: returned (`access()["bids"]` true through `secretary`).
**Impact:** The recusal of a member-secretary does not stop access to the bids they declared a conflict about.

### AUD-EVL-011 — Accounting Officer / Head of Procurement see committee free text and a submission version before delivery
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** OVS-CHG-001 v0_6 §4 (line 70); EVL-CHG-001 v0_5 §6 (technical issues) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-13 (rows 173, 177, 211)
**Evidence**
- `P/bid_evaluation/services/issues.py:48` — `safe_detail=f"{requirement['label']}: {cstr(description).strip()}"` stores the chair's free text in the platform Support Issue
- `P/bid_evaluation/services/reads.py:169-170` — `work()` returns every Support Issue of the case including `safe_detail` for `a["secretary"] or a["ao"] or a["hop"] or a["chair"]`; `resolve()` returns `out["work"] = work(doc, a)` (`:141`)
- `P/bid_evaluation/services/reads.py:82,128` — `_source(doc)` returns the first bid's `submitted_version` to AO/HoP before delivery
**Rule:** OVS v0_6 line 70: before delivery oversight sees state, committee, dates, next action, meeting counts; "Do not include bidder identities, bid counts, prices, findings, clarification content or discussion notes."
**Reproduction / failing test sketch:** (static; not run) Chair `report_issue(requirement_key=K, description="Memory rule for Afya defective")`; then `reads.resolve(tender_reference=T, user=AO)["work"]["issues"][0]["safe_detail"]` contains the bidder name and requirement label. The existing disclosure tests (`P/bid_evaluation/tests/test_evl_reads.py:40`, `test_evl_oversight.py:74`) assert absence of bidder name/total only.
**Impact:** Bidder-specific committee commentary reaches officers whom the approved visibility rule restricts to administrative facts.

### AUD-EVL-012 — `ExportEvaluationRecord` / "Download report" is not a server operation
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §5.5 (line 162), §7.2/§10 (lines 269, 599) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-16 (rows 109, 150, 171, 212)
**Evidence**
- `P/public/js/bid_evaluation/BidEvaluation.vue:290-292` — `case "download": go(["report","preview"]); setTimeout(() => window.print(), 800);`
- `P/bid_evaluation/api.py` — no whitelisted export method (grep `export|Export` returns nothing across its 54 functions)
**Rule:** EVL line 599: "Download report — `ExportEvaluationRecord` restricted to selected report/version and permitted annexes; original signatures and correction links preserved"; line 162: "Supporting evidence is linked and exportable".
**Reproduction / failing test sketch:** (static; not run) Open a delivered report and click Download report: the browser print dialog opens over the on-screen preview; no annexes, signature/correction links or per-export permission/log exist server-side.
**Impact:** The documented, scoped export of the signed record does not exist; users can only print what the preview shows.

### AUD-EVL-013 — Independent-opening-member exclusion from evaluation works in one order only
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** EVL-CHG-001 v0_5 §3 (line 65), §5.1 (line 126: "Appointment may exist before intake"); BOP-CHG-001 v0_11 BOP-A17 (line 401) · **Module(s):** Evaluation, Bid Opening · **Sources:** sweep-sod F6
**Evidence**
- `P/bid_evaluation/services/appointment.py:49` — `if opening.is_excluded_from_evaluation(doc.tender, user): return "opening_independent"` (checked only at evaluation-appointment time)
- `P/bid_opening/services/appointment.py:55-61` — `is_excluded_from_evaluation` looks at opening-committee rows with `excluded_from_evaluation`
- `P/bid_opening/services/appointment.py:81` and `:159` — the opening-appointment check compares the independent member only against `opening_seam.processing_actors` (`P/tenders/services/opening_seam.py:91-98`: Tender Version actors and Tender Publication authoriser); it never looks at the Evaluation roster
**Rule:** EVL line 65: "the independent opening member cannot be appointed to evaluate the same tender" (unqualified); BOP-A17: "excluded from later same-Tender Evaluation appointment". The two documents differ on order and neither addresses an Evaluation member later designated independent opening member.
**Reproduction / failing test sketch:** (static; not run) 1. AO appoints an Evaluation committee including U (allowed before intake). 2. AO then appoints U as "Independent member" of the opening committee: `validate` passes (U is not a tender processor). U sits on both. `roster.status`/`reads.py:62` never re-evaluate the exclusion.
**Impact:** The "conservative product policy" separation between opening and evaluation is order-dependent. **Owner decision needed:** state whether the exclusion is symmetric (then Bid Opening must refuse an existing Evaluation member) or only "later evaluation appointments" as BOP-A17 reads.

### AUD-EVL-014 — Evaluation's funding read runs as the session user and swallows every failure
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §4.4 (line 116), D03-FUNDING (line 380) · **Module(s):** Evaluation, Budget · **Sources:** sweep-handoffs F-15
**Evidence**
- `P/bid_evaluation/services/funding.py:35-43` — `get_funding_lineage(reservation=...)` inside `try: ... except Exception: frappe.log_error(title="Bid Evaluation funding read unavailable"); return None`
- `kentender_budget/kentender_budget/services/budget_downstream_contracts.py:61` — `require_budget_version_read_scope(version_at_creation)`; `kentender_budget/kentender_budget/services/budget_authorization.py:170-184` runs `frappe.has_permission(..., user=frappe.session.user, throw=True)`; read roles are Budget governance roles, Auditor, AO and HOPF (`budget_authorization.py:55-71`)
- `P/bid_evaluation/services/funding.py:50-52` — `compare` returns `None` when `available()` is `None`, so `comparison.compare` yields `funding: None` and the frozen report carries no funding fact
**Rule:** EVL line 116: "an authoritative budget comparison can report a shortfall"; a failed or unauthorised read is indistinguishable from "no reservations" (silent absence), and Award later treats absence as "not restricted" (AUD-AWD-002).
**Reproduction / failing test sketch:** (static; not run; permission outcome needs runtime confirmation) 1. Make a procurement-officer secretary (no Budget role) freeze a report whose Tender has reservations. 2. `funding.available(tender)` raises inside the Budget read and returns `None`; the report records no funding block and no shortfall qualification.
**Impact:** A real shortfall can vanish from the signed report depending on who triggered the read, with only an error-log row as trace.

### AUD-EVL-015 — Tenders publishes only cancellation: suspension, resumption, validity-extension, award-decision and dated-rule facts have no production producer
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §6 (line 192), §5.7 (lines 176-180) · **Module(s):** Evaluation, Award, Tenders · **Sources:** trace-evaluation row 77 (§5.7/§6 Partial); trace-award rows 66, 73, 145; related to AUD-EVL-017
**Evidence**
- `P/tenders/services/evaluation_seam.py:171-179` — `status_events` returns only a `Cancellation` event (from `root.cancellation`)
- `P/bid_evaluation/services/tender_events.py:39,119-123` — Evaluation accepts kinds `("Suspension","Resumption","Cancellation","Validity extension","Award decision","Dated rule")`, but `record_simulated_event` throws unless `simulation.enabled()`; `P/bid_evaluation/services/timers.py:40-41` reads a "Validity extension" only from such a stored event
- grep for "validity extension" in `P/tenders` (excluding tests) finds only two docstring mentions (`evaluation_seam.py:25`, `award_seam.py:10`): Tenders owns no extension record
- `P/award/services/restrictions.py:111` — `ReceiveAwardRestriction` (`receive`) has no caller outside tests; Award's only automatic restriction intake is `tenders.status_events` (`P/award/services/tender_events.py`), so Review-order/Suspension events never arrive in production
**Rule:** EVL line 192: "Tenders / downstream owner → Evaluation: Versioned suspension/cancellation/validity-extension and award-decision facts. Evaluate the event's scope and authority; never infer status from an absent consumer."
**Reproduction / failing test sketch:** (static; not run) On a non-test site suspend a tender in Tenders (if a route exists) or extend its validity: no `Evaluation Source Event`/Award issue results; only cancellation is ever consumed. After `validity_end`, `report.outcome` returns "No current recommendation — tender validity expired" with no extension path.
**Impact:** Authoritative pauses and lawful validity extensions never reach Evaluation or Award; the system will report a lawfully extended tender as expired and will not pause for a Board suspension (HOP must key it manually in Award). The producer belongs to Tenders (TPR); this is a missing hand-off.

### AUD-EVL-016 — The secretary reads every bid with no declaration or confidentiality acceptance
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** EVL-CHG-001 v0_5 §3 (lines 61, 63, 67) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-5 (secretary part), rows 15, 225
**Evidence**
- `P/bid_evaluation/services/reads.py:62` — `bids = (v["eligible"] or v["secretary"] or v["auditor"]) and not v["technical"]` (secretary grants bid access without any declaration)
- `P/bid_evaluation/services/secretary.py:26-61` — assignment requires only "Head of Procurement" or a procurement officer and an appointment reference; no declaration or confidentiality sentence
- `P/bid_evaluation/services/declaration.py:35-36` — declarations exist only for members (`user not in roster.member_users(...)` → Not found)
**Rule:** EVL line 67: each *member* personally declares and accepts confidentiality; line 61: "conflict clearance governs committee access". The document says nothing equivalent for the secretary, who reads all bids and prepares the report.
**Reproduction / failing test sketch:** (static; not run) HoP assigns procurement officer P (not a member) as secretary; P calls `reads.bid(...)` before any declaration: returned.
**Impact:** The person who organises the record can read all sealed-then-opened bids without any conflict or confidentiality statement. **Owner decision needed:** require the same declaration/confidentiality acceptance from the secretary (and say whether a conflicted secretary must be replaced).

### AUD-EVL-017 — No authoritative statutory evaluation deadline exists, so overdue highlighting is dead in production
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** EVL-CHG-001 v0_5 §5.7 (line 178) · **Module(s):** Evaluation, Tenders · **Sources:** trace-evaluation F-21 (rows 80, 81, 210)
**Evidence**
- `P/tenders/services/evaluation_seam.py:165-167` — `"evaluation_deadline": None, "evaluation_rule": None, "evaluation_rule_missing": "No authoritative dated rule for the statutory evaluation period is recorded (FU-EVL-18)."`
- `P/bid_evaluation/services/timers.py:35-47` — `overdue` can be true only if a deadline exists, which in production it never does (only the simulated "Dated rule" event sets it, `tender_events.py:119-123`)
**Rule:** EVL line 178: "Display the statutory evaluation deadline … from the authoritative dated rules. The legal computation, source and timezone must be inspectable … Overdue evaluation is highlighted to the chair and Head of Procurement". The document names no counting rule or source for the evaluation period.
**Reproduction / failing test sketch:** (static; not run) `timers.dated(doc)` on any production case: `evaluation_deadline` is None, `overdue` False; chair/HoP highlighting and the date-conflict check (`clarification.py:125-126`) never trigger.
**Impact:** The documented overdue highlight cannot occur. **Owner decision needed:** supply the governing evaluation-period rule (source, counting, timezone) and the Tenders record that carries it.

### AUD-AWD-003 — Heads of Procurement can end an authoritative order or a funding restriction with free-text "evidence"
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.6 (line 151), §5.10 (lines 255-272), AC-030 · **Module(s):** Award, Tenders · **Sources:** trace-award F12 (rows 24, 75, 110, 115, 117, 210)
**Evidence**
- `P/award/services/restrictions.py:153` — evidence is required only as non-blank (`... and not proof`); `:163-167` resolves the issue for `Restriction ended` / `Owner correction confirmed`
- `P/award/services/tender_events.py:49` — release evidence from a Tenders Resumption event is stored in `detail.release_evidence` but never required or compared in `disposition`
- `P/award/services/restrictions.py:166` — `if chosen == OWNER_CONFIRMED: checks.sync(...)`; `P/award/services/checks.py:120` opens the Funding issue with `source_event=f"funding:{rep.name}"` and `P/award/services/issues.py:25-26` returns an existing (even resolved) issue for the same `source_event`, so a funding restriction resolved by the HOP is never reopened for that report
**Rule:** AWD §5.6: an authoritative order "can be marked ended only from the operative release/expiry evidence and checks for continuing restrictions"; §5.10: Restriction ended needs "operative authority evidence"; Owner correction confirmed needs "authoritative owner receipt".
**Reproduction / failing test sketch:** (static; not run) A Tenders `Suspension` event creates an authoritative hold; HOP calls `record_disposition(outcome="Restriction ended", reason="x", evidence="y")` → resolved and the package can proceed. Likewise a Funding issue: `record_disposition(outcome="Owner correction confirmed", reason="x", evidence="y")` resolves it and `sync` cannot reopen it.
**Impact:** A single role holder lifts a statutory suspension, or clears a funding restriction permanently, on unverified text. Verification of "operative evidence" is partly impossible for free text, but system-received orders carry release evidence that is ignored.

### AUD-AWD-004 — Later restrictions and cancellation-after-notice do not reliably reach an already-delivered Contracting case
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.8 (line 185), AC-020 · **Module(s):** Award, Contracting (simulated) · **Sources:** trace-award F3 (rows 73, 84, 100, 200)
**Evidence**
- `P/award/services/restrictions.py:65-68` — `try: receipt = contracting.deliver_update(update)["receipt"]` / `except contracting.ReceiverUnavailable: receipt = ""`, then the update is appended with an empty receipt (`:69-70`)
- `P/award/services/sweep.py:12-24` — the sweep steps (`intake.retry_pending`, `tender_events.sweep`, `eligibility.sweep`, `notices.retry_failed`, `events.retry_pending`, `explanation.retry_pending`) include no update retry; no support issue is opened
- `P/award/services/restrictions.py:78` and `P/award/services/corrections.py:81` are the only callers of `_later_update`; `P/award/services/tender_events.py:68-71` (cancellation after notification) and validity expiry (`checks.py:112-117`) open holds with no update to a delivered package
- `P/award/test_services/contracting_receiver.py` creates no task for an update (`_receive(..., task=False)` per trace; static)
**Rule:** AWD §5.8: "Later orders, corrections or validity changes are delivered as separate immutable updates with required consumer acknowledgement and a task"; AC-020: "A later restriction reaches the existing Contracting case".
**Reproduction / failing test sketch:** (static; not run) Deliver a package; set the receiver down (`contracting_down=1`); `record_restriction(basis="Authoritative order", evidence=...)` → ok, `pkg.updates_json` row has `receipt: ""`; restore the receiver and run `award.services.sweep.run`: no update is delivered. Also cancel the tender after delivery: no Restriction update reaches Contracting.
**Impact:** Contracting may proceed on a package that is under a later order. Latent today because the only receiver is a simulation (no Contracting module exists on this bench), but the sender's retry/incident duty is Award's.

### AUD-AWD-005 — Case `outcome` is never set to "Award", so the HoD decision summary shows no outcome
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 header (OVS-P03, line 5); OVS-CHG-001 v0_6 §4.1 · **Module(s):** Award, Tenders summary · **Sources:** trace-award F4 (rows 226, 229)
**Evidence**
- `P/award/services/decision.py:64` — `records.bump(doc, decision_status="Award recorded", current_decision=decision.name, outcome="")`; `:85` sets "No award" and `tender_events.py:77` "Cancelled"; `eligibility.py:134` sets only the cycle's outcome to "Award"
- `P/award/services/reads.py:186` — `department_record` builds `decided = {"outcome": doc.outcome, ...}`; `P/award/services/stage_summary.py:67-70` — `outcome = {"label": "Outcome", "value": doc.outcome} if doc.outcome else None` and `ss.fact("Outcome", doc.outcome)`
**Rule:** AWD header: HoD "scoped final-decision summary"; OVS v0_6 §4.1: HoD sees "final AO decision/outcome/date and a disclosed decision-reason summary".
**Reproduction / failing test sketch:** (static; not run) As AO record an Award; read `reads.department_record(doc)` (or `stage_summary.for_tender` as a Head of User Department): `decision.outcome == ""`, no Outcome badge; date and reason are present. Test sketch: after `awarded()`, the summary must contain `Outcome: Award`. `P/award/tests/test_awd_home_provider.py` asserts only the absence of notice text.
**Impact:** The approved HoD/Tender summary cannot show that an award was made.

### AUD-AWD-006 — The real Evaluation producer hard-codes every annex as available
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.1 (line 91), AC-002 · **Module(s):** Evaluation, Award · **Sources:** trace-award F8 (rows 28, 182)
**Evidence**
- `P/bid_evaluation/services/award_seam.py:113` — `"annexes": [{"name": s, "available": True} for s in (content.get("sections") or [])]`
- `P/award/services/checks.py:37` — `if any(not a.get("available") for a in snap.get("annexes") or []): return "One required annex is unavailable."`
- `P/bid_evaluation/services/award_seam.py:111` — `signatures.required` is `len(sigs)` (the number of target rows), so it cannot exceed present rows
**Rule:** AWD §5.1: "The incoming package must identify every required report signature and the exact report/annex set. A missing, mismatched or unverifiable artifact creates a source issue automatically."
**Reproduction / failing test sketch:** (static; not run) Withhold or remove an annex artefact in Evaluation: `delivered_report` still returns `available: True`, so Award's "annex unavailable" source issue can fire only through the synthetic provider (`awd_intake test_incomplete_source_opens_the_exact_issue` uses `overrides={"missing_annex": True}`).
**Impact:** The missing-annex detection required by AC-002 is vacuous with real data.

### AUD-AWD-007 — Contracting package "contract terms" are constant strings, not mapped tender data
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.8 (line 179), AC-021 · **Module(s):** Award, Contracting · **Sources:** trace-award F10 (rows 26, 92, 201)
**Evidence**
- `P/award/services/eligibility.py:85-88` — `"delivery_and_warranty": "As issued in the tender and the supplier's response", "reservation_treatment": "As recorded in the tender's reservation lineage", "performance_security": "As published in the tender (Contracting verifies before signature)", "tender_security": "As recorded at submission"`
- `P/award/services/eligibility.py:84-86` — only `quantity` and `warranty` come from the report snapshot; there is no requirement/response mapping, reservation id or security amount (the reservation ids are available via `P/tenders/services/evaluation_seam.py:202`)
**Rule:** AWD §5.8: "The package includes the issued requirement and supplier response mappings needed for the contract, delivery/warranty commitments, applicable reservation treatment, published performance-security terms, tender-security references, and all current restrictions."
**Reproduction / failing test sketch:** (static; not run) Deliver a package; inspect `content_json["contract_terms"]` — literal sentences only; `awd_delivery test_delivered` asserts only amount/warranty/quantity.
**Impact:** Contracting would have to re-key mappings, reservation lineage and security terms, contrary to AC-021.

### AUD-AWD-008 — §88 validity extension and the notice's contracting window are not modelled
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.5 (line 141), §5.8 condition 5 (line 173) · **Module(s):** Award, Tenders · **Sources:** trace-award F11 (rows 66, 89); related to AUD-EVL-015
**Evidence**
- `P/tenders/services/award_seam.py:33-37` → `P/tenders/services/evaluation_seam.py:147-166` — `validity` returns only the published validity date (no extension, prior-extension count, duration or notice evidence)
- `P/award/services/checks.py:42-49` — `validity()` computes expiry from that date only; `P/award/services/tender_events.py:13` says extensions "are read live" but no code does
- `P/award/services/eligibility.py:47-49` — condition 5 tests only `v["known"] and not v["expired"]`; grep `contracting window|extension` in `P/award/services/` matches only that comment
**Rule:** AWD §5.5: "Tenders supplies the extension decision, prior-extension count, duration and notice evidence, checked against the effective legal profile"; §5.8 cond. 5: "Tender validity and the notice's contracting window remain current".
**Reproduction / failing test sketch:** (static; not run) After a lawful extension recorded by Tenders (when that exists) the published validity date is unchanged, so `checks.validity` reports expired and Award holds with `AWD_VALIDITY_EXPIRED` permanently.
**Impact:** A lawfully extended tender is treated as expired; the notice contracting-window condition cannot be enforced.

### AUD-AWD-009 — The "No award" follow-up task can never be completed
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.7 (line 161) · **Module(s):** Award · **Sources:** trace-award row 81
**Evidence**
- `P/award/services/decision.py:80` — `next_action_owner=hop or None, next_action_state="Open"` is the only writer of `next_action_state` (grep across `P/award/` code and `P/public/js/award` finds no other assignment)
- `P/award/services/tasks.py:64`, `P/award/services/next_steps.py:318`, `P/award/services/home_provider.py:317`, `analytics_facts.py:223` — the HOP task and next-step row are shown while `next_action_state == "Open"`
**Rule:** AWD §5.7: Record no award gives "one concrete next task for HOP … Store that task's action, owner and completion evidence".
**Reproduction / failing test sketch:** (static; not run) Record a No award with `next_action="Review whether the tender should be cancelled"`; the HOP item `next:<decision>` appears; no command exists to record completion or evidence, so it never clears (`awd_decision test_no_award_follow_up` asserts only the "Open" state, `:53`).
**Impact:** A permanent open HOP task on every No-award case, with no way to close it or capture completion evidence.

### AUD-AWD-010 — An open debrief request or missing debrief rule never blocks Contracting delivery
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.6 (line 149), AC-015 · **Module(s):** Award · **Sources:** trace-award row 72; divergence from proposed spec (legal profile unverified, production gate owner-held, §15)
**Evidence**
- `P/award/services/profile.py:31` — `"debrief_rule": "Test profile: an explanation request does not extend the waiting period; an open request does not block Contracting delivery."` is the only debrief rule, a string
- `P/award/services/eligibility.py:32-58` — conditions 1-7 include no debrief condition (grep `debrief` in `eligibility.py`, `clocks.py`, `guards.py`, `checks.py` returns nothing); an explanation request is Correspondence, not an Issue, so it never reaches `issues.holding`
**Rule:** AWD §5.6: "A missing applicable rule or unresolved effect on the waiting period prevents Contracting delivery until HOP records the supported disposition."
**Reproduction / failing test sketch:** (static; not run) Supplier `request_explanation` after notice, leave it open; once conditions 1-6 are met the package is delivered.
**Impact:** Latent until a verified legal profile exists (the unverified profile already blocks delivery with `AWD_RULE_UNVERIFIED`); the debrief gate must still be built.

### AUD-AWD-011 — Return to Evaluation dead-ends when the Head of Procurement who received the report is replaced
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.2, §5.9 (expired authority routes work to the current holder), §7 `ReturnEvaluationReport` · **Module(s):** Award, Evaluation · **Sources:** trace-award F20 (row 37)
**Evidence**
- `P/award/services/issues.py:66-74` — `hop_for` routes Award work to the current Head of Procurement when the recipient no longer holds the responsibility
- `P/award/services/opinion.py:141,150` — `return_report` passes only `guards.require_hop(user)` (any current holder) and then calls Evaluation with that `user`
- `P/bid_evaluation/services/correction.py:96-97` — `if not delivery or delivery.recipient_user != user: raise frappe.DoesNotExistError("Not found")`
**Rule:** AWD §5.9 / AUTH: an expired or replaced authority routes the task to the current holder; the replacement HOP is the actor the document expects to Return.
**Reproduction / failing test sketch:** (static; not run) Deliver a report to HOP-1; end HOP-1's assignment and appoint HOP-2; HOP-2 (who gets the "Prepare professional opinion" task) calls `award.api.return_report(...)`: Evaluation answers Not found; Award's opinion stays unreturnable.
**Impact:** After a change of Head of Procurement a report cannot be returned for correction by the current holder; the flow dead-ends until the original recipient is restored.


## 4.4 Low

### AUD-XC-025 — Requisition package, event, journal and outcome doctypes have business-role read DocPerm and no registered hook
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** REQ v1_14 §8 ("Every list, count, direct route, file download and command applies the same registered predicate") and invariant 15 (line 652); AUTH-ADR-001 v1_11 §5.7 (line 316) · **Module(s):** Requisitions · **Sources:** trace-requisition F-07
**Evidence**
- `kentender_procurement/kentender_procurement/hooks.py:424-437` — the hooks cover Procurement Requisition, Requisition Version, Requisition Task, Requisition Decision, Authorised Requisition Handoff only.
- `kentender_procurement/kentender_procurement/procurement_requisitions/doctype/it_equipment_requirement_package_version/it_equipment_requirement_package_version.json:238,250,262`, `it_equipment_requirement_package.json:129,141,153`, `requisition_event.json:150,162`, `requisition_correction_outcome.json:223,235`, `requisition_command_journal.json:121` — Head of Procurement Function, Procurement Planner and Auditor `read` with no hook.
**Rule:** REQ §8 and invariant 15; AUTH §5.7 "A lingering Role grants no business authority on its own — coarse DocType access without a scope match resolves to denial", which holds only where a hook exists.
**Reproduction / failing test sketch:** static; not run. A user whose assignment has lapsed but whose projected role `Auditor` lingers until the daily reconcile: `GET /api/resource/IT Equipment Requirement Package Version?fields=["*"]` lists every Draft version; the five hooked doctypes refuse the same user.
**Impact:** Exposure is limited to a role holder without a live assignment, until the reconcile removes the role.

### AUD-XC-026 — Legacy AUTH-G04 engine (Operational Scope Assignment, Capability Profile) is still writable and still authorises My Work claims
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** AUTH-ADR-001 v1_11 §19 (line 945) "Do not keep `User Scope Assignment` and `User Responsibility Assignment` both active", §11.5 (line 480) "No fallback mode" · **Module(s):** Core · **Sources:** sweep-authz F-15
**Evidence**
- `kentender_core/kentender_core/authorization_api.py:25-28` `add_assignment` (whitelisted) calls `authorization_administration.create_draft_assignment` (`services/authorization_administration.py:63-70`), which inserts an `Operational Scope Assignment` with `ignore_permissions=True`; the gate is `require_access_administrator` (:19-23): `System Manager` or the bare role `System Access Administrator`. `user_access`, `routing_rule`, `revise_routing_rule` (:10-23) call the same gate; `diagnostic` (:30-34) admits the same roles or the legacy capability `authorization.diagnostic.view` (`authorization_diagnostics.py:13-14`).
- `kentender_core/kentender_core/services/my_work.py:226-228` `claim_my_work_task` (whitelisted) calls `workflow_tasks.claim_task`, which calls `require_capability` (`services/workflow_tasks.py:148-160`) over the legacy `authorization_policy`.
- Mitigation found: no production code calls `workflow_tasks.create_routed_task` (grep: only a retirement patch references the module), so only already-existing Workflow Tasks can be claimed.
**Rule:** AUTH §19 and §11.5; `AUTH-ADR-001-capability-mapping.md` (the OSA/Capability Profile path is to be retired).
**Reproduction / failing test sketch:** static; not run. As System Manager: `POST /api/method/kentender_core.authorization_api.add_assignment` `values={"user_id":"<u>","capability_profile_id":"<profile>","procuring_entity_id":"<PE>","effective_from":"2026-10-01"}` creates a second authority record outside `User Responsibility Assignment`.
**Impact:** A parallel, administrator-writable authority store remains, but it authorises only claims on legacy Workflow Tasks.

### AUD-XC-027 — Bid working-copy doctypes are denied by hook, but Administrator reads them by name; Bid Receipt technical route is dead
**Severity:** Low · **Classification:** SPEC GAP (BDS records the Administrator bypass as a production-gate residual; the owner must decide how it is closed, for example by not storing bid content readable through Frappe at all) · **Doc:** BDS v0_11 BDS01-AC-080 (line 2012) "Technical and administrator views expose only authorised service/custody metadata and cannot decrypt, preview, download or search submitted content"; AUTH-ADR-001 v1_11 §8 "never stranded" · **Module(s):** Bid Submission · **Sources:** sweep-authz F-23
**Evidence**
- `kentender_procurement/kentender_procurement/bid_submission/services/bid_authorization.py:66-72` (comment: "Administrator bypasses Frappe's permission checks — a recorded production-gate residual, plan D7"), `:75-84` `CONTENT_DOCTYPES`, `deny_desk_access` returns False and `deny_desk_query` returns `"1=0"`; registered for six content doctypes at `kentender_procurement/kentender_procurement/hooks.py:735-738`.
- `apps/frappe/frappe/permissions.py:107` returns True for Administrator before any controller hook, so `GET /api/resource/Bid Section Response/<name>` by name is allowed for Administrator; list reads are still emptied (`db_query.py:1075` applies the `1=0` query condition to every user).
- `kentender_procurement/kentender_procurement/bid_submission/services/technical_read.py:40` — the `Bid Receipt` resolver routes to `["Form","Bid Receipt",name]`, a form the deny hook refuses to System Manager.
**Rule:** BDS01-AC-080; AUTH §8 (technical reader is never stranded on a record the module says it can resolve).
**Reproduction / failing test sketch:** static; not run. As Administrator: `GET /api/resource/Bid Section Response/<known name>`; as System Manager open the technical-search hit for a Bid Receipt (expected: metadata view; read result: permission error).
**Impact:** Only the Administrator account (not System Manager) can read a bid working-copy record, and only by name; the Bid Receipt link in Technical search is unusable for System Manager.

### AUD-XC-028 — BOP v0_11 and OVS v0_6 section 4.2 disagree on what Administrator/System Manager read in Bid Opening
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** BOP v0_11 §6 table (line 146) vs OVS v0_6 §4.2 (lines 104-106) and OVS-P05 (OVS v0_6 line 362; tracked as FU-OVS-18) · **Module(s):** Bid Opening · **Sources:** sweep-authz F-24 (Bid Opening half)
**Evidence**
- `docs/mvp-1-r1/14_bid_opening/KenTender_BOP-CHG-001_Electronic_Bid_Opening_v0_11.md:146` — "Administrator/System Manager | Non-content health and incident support only"; line 9 notes OVS "qualifies" it.
- `docs/mvp-1-r1/17_oversight_visibility/KenTender_OVS-CHG-001_System_Usability_and_Decision_Visibility_v0_6.md` §4.2 — "After governed release, Administrator/System Manager reads the ordinary owner business record"; OVS-P05 "Approved 3 October 2026".
- `kentender_procurement/kentender_procurement/bid_opening/services/reads.py:112-113,128` — code follows BOP: "Bids, the register and the opening record are not shown to administrators"; `record_view` returns None for technical users.
**Rule:** the two approved documents state different outcomes for the same actor and state.
**Reproduction / failing test sketch:** static; not run. As System Manager open a completed Bid Opening: BOP says status only; OVS §4.2 says the ordinary record. Decision needed from the owner: which text governs after release.
**Impact:** No defect in code against one reading, a defect against the other; implementers cannot satisfy both.

### AUD-XC-029 — `list_organisation_units` serves the unit catalogue to portal accounts the doctype itself refuses
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** AUTH-ADR-001 v1_11 §5.1; AGENTS.md §4.3 · **Module(s):** Core reference data · **Sources:** sweep-authz F-25 (narrowed after checking DocPerm)
**Evidence**
- `kentender_core/kentender_core/api/reference_data_api.py:48-51` — `list_organisation_units` is `@frappe.whitelist()` with no gate; `kentender_core/kentender_core/services/reference_data_queries.py:75-101` returns `frappe.get_all("Organisation Unit", ...)` ids and `unit_name` (permissions ignored).
- `kentender_core/kentender_core/kentender_core/doctype/organisation_unit/organisation_unit.json:176` grants read to `Desk User` only (Website Users lack it). By contrast `pe_type.json:69`, `financial_year.json:128`, `funding_source.json:75` already grant `All` read, so their list endpoints add no exposure.
**Rule:** AGENTS.md §4.3.
**Reproduction / failing test sketch:** static; not run. As a supplier Website User: `GET /api/method/kentender_core.api.reference_data_api.list_organisation_units` returns every Active unit; `GET /api/resource/Organisation Unit` is refused.
**Impact:** Internal department names and ids are visible to portal accounts; low sensitivity.

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

### AUD-HND-010 — NDS accepted-Need contract has two key shapes under one `.v2` tag; quantity is a JSON float
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** NDS-CHG-001 v1_16 §7.1 (lines 325, 521), §8.1 (line 616), NDS11-AC-078 (line 1699); PLN-CHG-001 v1_29 §4.1 Quantity (line 142) · **Module(s):** Departmental Needs, Planning · **Sources:** sweep-handoffs F-10
**Evidence**
- `kentender_procurement/kentender_procurement/departmental_needs/services/events.py:73-77,83` — event keys `need_id`, `accepted_version_id`, `version_number`, `org_unit_id`, `financial_year_id`, `unit_id`, `unit_display_value`, `"indicative_quantity": flt(version.indicative_quantity)`.
- `kentender_procurement/kentender_procurement/departmental_needs/services/workspace.py:503-514` — `get_current_accepted_need` returns `"contract": "DepartmentalNeedAccepted.v2"` with `need`, `accepted_revision`, `revision_number`, `organisation_unit`, `financial_year`, `unit`, `unit_label`, and `"indicative_quantity": flt(...)`.
- Planning reads only `accepted_revision` from the read (`procurement_planning/services/needs_intake.py:89`), so nothing breaks today.
**Rule:** NDS v1_16 line 521 "Wire keys are unchanged ...: the accepted revision travels as `accepted_version_id` and `version_number`, and the contract stays at `.v2`"; line 616 the read returns the "Current accepted payload"; line 325 "no ... hidden dual-read fields"; NDS11-AC-078 "never silent v2 drift". PLN v1_29 line 142 Quantity "Exact positive decimal string ... Need quantities are copied exactly" (the float-quantity part overlaps the float-money root cause owned by the xc-core part; stated here only because it is on this contract).
**Reproduction / failing test sketch:** (static; not run) Accept a Need; compare `list(events.accepted_payload(...).keys())` with `list(workspace.get_current_accepted_need(...).keys())` - the id/revision/org/FY/unit keys differ while both claim `DepartmentalNeedAccepted.v2`; the quantity is `float`, not a decimal string.
**Impact:** Two incompatible shapes carry one contract tag; any consumer written to the spec's wire keys fails on the read, with no effect on the current Planning consumer.

### AUD-HND-011 — REQ v1.14 is internally inconsistent about its own version status and conflicts with E2E-REQ-001 v0.2
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** REQ-CHG-001 v1_14 control table, §23.1 (line 2086), §2.1, §1.1, §5A, §5.1/§5.2; E2E-REQ-001 v0.2 §3, §11, §13/§18.7 · **Module(s):** Requisitions · **Sources:** trace-requisition F-19
**Evidence**
- REQ v1_14 control table: "Version 1.14 ... Status Approved - 3 October 2026"; "Supersession: On approval, supersedes v1.12 ... which remains the controlling approved version until then"; "Change type" row describes the OD5 change of v1.13/v1.12; line 5 "Preserve the v1.13 pending change intact"; line 2086 "REQ-CHG-001 v1.13 is proposed for Project Owner approval; v1.12 remains the approved controlling version until then." No operative v1.14 change description exists.
- E2E-REQ-001 v0.2 (approved 28 Aug 2026): line 45 "excludes ... cross-department Requisition grouping"; line 277 "Use native Frappe Roles, Workflow permissions and User Permissions"; §11 lists eight suitability tests. REQ v1_14: line 45 "Narrowly relaxed" cross-department combine (§2.1/§7.5); line 661 "No Frappe User Permission participates in any authorization decision in this module"; §5A has nine checks. REQ line 1964 acknowledges E2E-REQ-001 "has not been supplied ... re-verified".
- §5A line 415 requirement-type test "Straightforward off-the-shelf IT equipment" names no testable fact; code proxies Planning's `requirement_type == "Goods"` (`procurement_requisitions/services/compatibility.py:121-123`; docstring `:16-17`), so every Goods item passes that check.
- §5.1 line 167 lists `reservation_ids` on the root; line 190 lists `Superseded` with no trigger.
**Rule:** KT-STD document-change protocol: an approved version has one status and no peer approved document contradicts it without a recorded precedence rule.
**Reproduction / failing test sketch:** Static document review; no code run. Read the three REQ locations above side by side; and E2E lines 45/277 against REQ lines 45/661.
**Impact:** Implementers and testers cannot tell which REQ version is controlling or which approved contract wins on cross-department grouping and authorisation model; no code consequence by itself.

### AUD-STR-012 — Submitter blocked from Return, contrary to §12.4
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** STR §12.4 "Return remains available where authorised; same-author approval prohibition does not silently add an unapproved prohibition on Return" · **Module(s):** kentender_strategy · **Sources:** trace-strategy F6
**Evidence**
- `STR/services/strategy_transitions.py:46` — `("Submitted for approval", "Return"): ("Draft", CAP_APPROVE)`.
- `STR/services/strategy_authorization.py:121-127` — `_blocked_by_self_approval` blocks every `CAP_APPROVE` action for the submitter, so Return is blocked too (`require_plan_version_capability`, `:134-150`).
- Older tests pin the old rule: `STR/tests/test_str_chg_001_phase2_lifecycle.py:221-224`; `test_str_chg_001_v1_8_usability.py:326-327`.
**Rule:** STR §12.4 sentence quoted above; §5.1 transition table lists Return for "Strategy Approver" without a self restriction.
**Reproduction / failing test sketch:** (static; not run) Dual-role user submits then `return_strategy_version(plan_version_id, reason="<10+ characters>")` returns `AUTH_SEGREGATION_BLOCKED`. Test: assert it succeeds (still blocked from Approve).
**Impact:** A dual-role submitter cannot withdraw their own submission through Return; another Approver is needed.

### AUD-STR-013 — `effective_to` not bounded by the plan period on the server
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** STR-BR-005 "every version effective date shall fall within that period" · **Module(s):** kentender_strategy · **Sources:** trace-strategy F12
**Evidence**
- `STR/services/strategy_domain_guards.py:118-123` — checks `effective_from < period_start`, `effective_from > period_end`, `effective_from > effective_to`; there is no `effective_to <= period_end` test.
- The bound exists only in the browser: `STR/public/js/strategy/screens/PlanWorkspaceScreen.vue:235`.
**Rule:** STR-BR-005.
**Reproduction / failing test sketch:** (static; not run) `save_strategy_plan_draft({"plan_id":P,"plan_version_id":<Draft>,"effective_to":"2099-01-01"})` is accepted. Test: assert `ValidationError`.
**Impact:** Version end dates can exceed the plan period through the API; the resolver still requires plan-period overlap, so resolution is unaffected.

### AUD-STR-014 — Plan type cannot be changed in the first Draft although §11.3A shows the control
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** STR §11.3A "For the first Draft, show the same Plan title, Plan type, conditional Main plan, Start date and End date controls from §11.2, only while §12.2 permits identity editing" · **Module(s):** kentender_strategy · **Sources:** trace-strategy F15
**Evidence**
- `STR/services/strategy_domain_guards.py:79-82` — `if prev_role != doc.plan_role and _has_versions(doc.name): frappe.throw("Plan role cannot change once the plan has any version")`; every plan has Version 1 from creation (`STR/services/strategy_writes.py:99-107`).
- `STR/public/js/strategy/screens/PlanWorkspaceScreen.vue:495-503` — Plan type and Main plan render as read-only text in the Draft form.
**Rule:** §11.3A / §12.2 quoted above.
**Reproduction / failing test sketch:** (static; not run) Draft plan; `save_strategy_plan_draft({"plan_id":P,"plan_role":"Supporting Framework","parent_primary_plan_id":Q})` returns a validation error. Test: assert it saves while the first version is Draft and never submitted.
**Impact:** A wrongly typed plan must be discarded and recreated.

### AUD-STR-015 — Existence of a plan is distinguishable from refusal
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** STR §11.10 "Missing/unauthorised record whose existence is protected ... Do not distinguish missing from unauthorised existence"; AUTH-ADR-001 v1.9 §10 "Cross-scope reads return Not found where existence itself is protected" · **Module(s):** kentender_strategy · **Sources:** trace-strategy F18
**Evidence**
- `STR/services/strategy_ui_contracts.py:692-696` — `plan_name = resolve_plan_name(plan_id); if not plan_name: return {"not_found": True}` precedes `scope = _read_scope(); if not scope: return {"forbidden": True}`.
**Rule:** §11.10 quoted above.
**Reproduction / failing test sketch:** (static; not run) As a Website User call `get_plan_workspace` (see `STR/api/strategy_ui_api.py`) with a real and a made-up plan reference: `{"forbidden": True}` versus `{"not_found": True}`. Test: assert identical payloads.
**Impact:** Plan reference existence is observable by non-readers; no content leaks.

### AUD-STR-016 — Hierarchy and target validation raise untyped errors where §9 requires typed codes
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** STR §9 `STRATEGY_INVALID_HIERARCHY` ("A node type, parent relationship, duplicate sibling or cross-version link is invalid") and `STRATEGY_INVALID_TARGET` ("Target period, comparison or value is invalid") · **Module(s):** kentender_strategy · **Sources:** trace-strategy F19 (code part)
**Evidence**
- `STR/services/strategy_domain_guards.py:202-228,231-251,254-321` — every validator uses `frappe.throw(_("..."))` with no `title`/code (for example `:211,214,221,237,252,264,280,301`).
- The STRATEGY_INVALID_HIERARCHY / STRATEGY_INVALID_TARGET titles appear only on the delete paths `STR/services/strategy_writes.py:323-334`.
**Rule:** §9 table quoted above.
**Reproduction / failing test sketch:** (static; not run) `save_strategy_structure_draft` with a Pillar given a `parent_node_id`: the response `exc` carries no STRATEGY_INVALID_HIERARCHY. Test: assert the error title equals `STRATEGY_INVALID_HIERARCHY`.
**Impact:** Clients cannot branch on the contract's error codes for the most common validation failures.

### AUD-STR-017 — §9 error vocabulary contradicts the AUTH-ADR-001 §10 closed vocabulary Strategy is bound to
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** STR §9 `STRATEGY_RESPONSIBILITY_REQUIRED`, `STRATEGY_DOWNSTREAM_FORBIDDEN` vs AUTH-ADR-001 v1.9 §10 (closed table: `AUTH_RESPONSIBILITY_REQUIRED`, `AUTH_SEGREGATION_BLOCKED`, `AUTH_ASSIGNMENT_INACTIVE`, ...) and STR §6/§16.1 binding Strategy to AUTH · **Module(s):** kentender_strategy, kentender_core · **Sources:** trace-strategy F19 (spec part)
**Evidence**
- `STR/services/strategy_authorization.py:134-150` — authorisation failures call `fail(decision.reason_code or "AUTH_RESPONSIBILITY_REQUIRED")`.
- `kentender_core/kentender_core/services/responsibility_errors.py:66-71` — `fail()` raises `ValueError` for any code outside the AUTH closed set, so `STRATEGY_RESPONSIBILITY_REQUIRED` cannot be produced by this path.
- `docs/mvp-1-r1/00_common/KenTender_AUTH-ADR-001_...v1_9.md:405-417` — the §10 error contract table lists only `AUTH_*` codes.
**Rule:** STR §9 lists `STRATEGY_RESPONSIBILITY_REQUIRED`; AUTH §10 is the closed contract STR §6 says Strategy uses. Both are approved. Owner decision needed: which code a Strategy denial returns.
**Reproduction / failing test sketch:** (static; not run) a user without an assignment calls `submit_strategy_version`: the response code is `AUTH_RESPONSIBILITY_REQUIRED`, STR §9 expects `STRATEGY_RESPONSIBILITY_REQUIRED`; there is no way to satisfy both documents.
**Impact:** Acceptance tests written from STR §9 cannot pass against an AUTH-conformant implementation.

### AUD-STR-018 — Predecessor closure can lengthen the predecessor's applicability
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** STR §8.3 "Consistent closure of the predecessor applicability interval ... reject overlapping authority"; §18.3 STR18-XD-002 (owner date-boundary semantics is an open evidence dependency, so this is partly "divergence from proposed spec") · **Module(s):** kentender_strategy · **Sources:** trace-strategy F21
**Evidence**
- `STR/services/strategy_transitions.py:129-134` — `other.effective_to = add_days(getdate(doc.effective_from), -1)` whenever the successor starts after the predecessor started, regardless of the predecessor's own earlier `effective_to`.
**Rule:** §8.3 quoted above (closure shortens or keeps, never extends).
**Reproduction / failing test sketch:** (static; not run) Predecessor 2023-07-01 to 2025-06-30, successor Use from 2026-01-01: after approval the predecessor's `effective_to` is 2025-12-31. Test: assert `min(old_end, D-1)`.
**Impact:** The historical record of the superseded version shows applicability it never had; the resolver uses Active status only so resolution is unaffected.

### AUD-STR-019 — Seed plan title lacks "(Demo)"; §14.3 identifiers cannot be produced under STR-BR-016
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** STR §14.3 (title "Ministry of Health Strategic Plan (Demo)", ids `STR-MOH-2023-001`, `STR-MOH-2023-001-V1`); §14.5 "Upsert by the exact stable identifiers above" and "Mark synthetic records visibly as (Demo)"; STR-BR-016 / §4.1 `plan_id` "Immutable generated reference" · **Module(s):** kentender_strategy (seed) · **Sources:** trace-strategy F16
**Evidence**
- `STR/seeds/kentender_mvp_v1_strategy.py:56` — `PLAN_TITLE = "Ministry of Health Strategic Plan"` (no "(Demo)"); the other seeded titles do carry it (`:337`).
- `STR/seeds/kentender_mvp_v1_strategy.py:19-30` — docstring records that identifiers are whatever the `{PE}-{TYPE}-####` generator produces, not the §14.3 literals.
**Rule:** §14.3/§14.5 versus §4/STR-BR-016: a document cannot both require exact literal ids and forbid users entering generated ids; the owner must pick (the "(Demo)" omission alone is a code deviation).
**Reproduction / failing test sketch:** (static; not run) after `make seed-canonical`, the plan title is "Ministry of Health Strategic Plan" and its reference is `MOH-SP-0001`; §14.3 expects "(Demo)" and `STR-MOH-2023-001`.
**Impact:** Seeded plan is not visibly marked synthetic; Playwright/E2E fixtures cannot match the document's literals.

### AUD-STR-020 — Extra `fixture_namespace` field on every Strategy DocType
**Severity:** Low · **Classification:** SPEC GAP · **Doc:** STR §1 "A field, action or screen not defined here is not part of the module"; §17 "No optional ... field 'for future use'"; §14.4 "Use the test namespace/rollback discipline in KT-STD §8.7" · **Module(s):** kentender_strategy · **Sources:** trace-strategy F20
**Evidence**
- `STR/kentender_strategy/doctype/strategy_node/strategy_node.json:86-98` — section "Fixture Ownership" and `fixture_namespace` Data field "Seed/test scoping key for idempotent fixture cleanup. Not a business field."; same in `strategic_plan`, `strategic_plan_version`, `performance_indicator`, `performance_target`.
- `STR/seeds/kentender_mvp_v1_strategy.py:125-135` — used as the seed's ownership test.
**Rule:** §1 and §17 above; the document is silent on a fixture-ownership marker on business DocTypes. Decision the owner must make: permit a documented non-business ownership field, or move seed ownership out of the business tables.
**Reproduction / failing test sketch:** (static; not run) `save_strategy_structure_draft` with `nodes=[{..., "fixture_namespace":"x"}]` stores the value; the field is accepted from any command payload.
**Impact:** Undocumented persisted field, writable by an Author through command payloads.

### AUD-STR-021 — Workspace shortcut still labelled "Strategy Portfolio"
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** STR §10 "existing menu entries are **Strategic plans** (formerly Strategy Portfolio) and **Approval tasks**" · **Module(s):** kentender_strategy · **Sources:** trace-strategy F23
**Evidence**
- `STR/kentender_strategy/workspace/strategy_management/strategy_management.json:47` — `"label": "Strategy Portfolio"` (type Page, `link_to: "strategy"`); the workspace content block `str_s1` (`:3`) names the same shortcut.
**Rule:** §10 quoted above.
**Reproduction / failing test sketch:** (static; not run) Open the Strategy Alignment workspace on kentender-test.local: first shortcut reads "Strategy Portfolio". Test: assert the shortcut label equals "Strategic plans".
**Impact:** Menu label differs from the approved wording; no behaviour effect.

### AUD-BUD-013 — Check token not bound to actor or Budget revisions
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** BUD v1.12 §8.3 "one token binding the full input digest, actor/caller, REQ/Plan/source/line revisions and server expiry"; BUD18-AC-059; §13 `BUDGET_CHECK_STALE` "owner revisions ... changed after Check Funding" · **Module(s):** kentender_budget · **Sources:** trace-budget F-22 (token item)
**Evidence**
- `BUD/services/budget_check_reserve_contracts.py:262-268` — the token context contains `plan_item, plan_version, finance_task, source_set_hash, calling_module, caller_reference`; no user.
- `BUD/services/budget_check_reserve_contracts.py:323-333` — `reserve_funding` compares only `finance_task` and `source_set_hash`; `budget_version_at_check` (`:244,257`) is never read back.
**Rule:** §8.3 and BUD18-AC-059 quoted above.
**Reproduction / failing test sketch:** (static; not run) User A (Head of Procurement Function) runs `check_funding`; user B (Finance Confirmation Officer) calls `reserve_funding` with A's token, hash and a new key: it proceeds. Test: the second actor is refused with `BUDGET_CHECK_STALE`.
**Impact:** A token is a bearer secret across callers; a revision change between check and reserve is detected only through the re-read availability, not as a stale check.

### AUD-BUD-014 — Mixed release/convert hold ends as `Released`; Close blocked for the version's submitter
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** BUD v1.12 §4.6 "A fully consumed hold is `Released` when only released, otherwise `Converted`"; §6 table "Active | Close after FY | Closed | Budget Approver" and the no-self-approval bullet limited to "approve the same version" · **Module(s):** kentender_budget · **Sources:** trace-budget F-22 (release status, close items)
**Evidence**
- `BUD/services/budget_commitment_contracts.py:143` — `doc.status = "Released" if doc.remaining_amount <= 0.0001 else doc.status` regardless of earlier conversions.
- `BUD/services/budget_readiness_contracts.py:833` — `_close_budget` calls `require_budget_version_capability(frappe.session.user, CAP_APPROVE, version)`; `BUD/services/budget_authorization.py:125-131` blocks every `CAP_APPROVE` for the version's first submitter (`_submitted_by`, `:112-122`).
**Rule:** §4.6 and §6 quoted above.
**Reproduction / failing test sketch:** (static; not run) Reserve 80m, convert 60m, release the remaining 20m: status is `Released`, §4.6 expects `Converted`. Dual-role user who submitted V1 calls `close_budget` after year end: `AUTH_SEGREGATION_BLOCKED`. Test: assert both per §4.6/§6.
**Impact:** Wrong status label for mixed outcomes; a dual-role submitter cannot close the year they submitted.

### AUD-BUD-015 — Seed diverges from §15.3/§15.5/§15.6 (generated line references, BUD-SC-FIN-* names, relative dates)
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** BUD v1.12 §1.1 "Identifiers are deliberately unchanged. `MOH-BL-DHI-2027` ... Do not 'tidy' them"; §15.3 line ids; §15.5 line "Legacy `BUD-SC-FIN-*` identifiers are renamed to `BUD-SC-REQ-*`"; §15.6 "approval date 14 Mar 2027" · **Module(s):** kentender_budget (seed) · **Sources:** trace-budget F-19; S-6
**Evidence**
- `BUD/seeds/kentender_mvp_v1_portfolio.py:55-60` — comment: line references are the generated ones "(Project Owner decision, 26 Sep 2026 — until then the seed overwrote them with `MOH-BL-DHI-2027`...)"; the document (3 Oct) still says do not tidy.
- `BUD/seeds/kentender_mvp_v1_portfolio.py:723-752` — profile names still `BUD-SC-FIN-SINGLE` etc.
- `BUD/seeds/kentender_mvp_v1_portfolio.py:557` — the successor profile uses `"approval_date": _offset_date(15)`, not the fixed 14 Mar 2027 of §15.6.
**Rule:** the document and the recorded owner decision conflict; the document was not revised. Owner must reconcile (document should adopt generated references and the two-year world, or the seed should revert). The `BUD-SC-FIN-*` names are a leftover against line 1317 of the document.
**Reproduction / failing test sketch:** (static; not run) After `make seed-canonical` the baseline lines have generated references, not `MOH-BL-DHI-2027`; fixture profile `BUD-SC-FIN-SINGLE` exists; `BUD-SC-REQ-SINGLE` does not.
**Impact:** Playwright and Planning fixtures keyed on the document's literals cannot match; no production effect.

### AUD-BUD-016 — SPEC DEFECT: canonical route `/app/budget` cannot be served (collides with ERPNext Budget)
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** BUD v1.12 §10 routes `/app/budget`, `/app/budget/{budget_id}/version/{version_number}/edit`, `/app/budget/review/{budget_version_id}`, `/app/budget/line/{budget_line_id}` · **Module(s):** kentender_budget · **Sources:** trace-budget S-1
**Evidence**
- `BUD/hooks.py:29-33` — `page_js = {"budget-funding": "public/js/budget_funding_page.js"}` with the comment "Not 'budget' — collides with the existing Budget doctype's own List View route".
- `BUD/public/js/budget_funding_page.js:1-18` — states ERPNext's `Budget` DocType (module Accounts) permanently owns the `/app/budget` slug (`apps/erpnext/erpnext/accounts/doctype/budget` exists); the route prefix stays `budget-funding`.
**Rule:** Frappe resolves a bare `/app/<slug>` against readable DocType slugs before a same-named Page, so the document's route cannot be served; the document should name the implemented prefix.
**Reproduction / failing test sketch:** (static; not run) Open `/app/budget` on the test site: ERPNext's Budget list opens, not Budget & Funding.
**Impact:** Document routes (including Planning's "Open Budget & Funding" target) do not match the live routes.

### AUD-BUD-017 — SPEC DEFECT: BUD-BR-027 "no ledger event" vs §14 request events in the same ledger
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** BUD v1.12 BUD-BR-027 "It changes no amount and creates no reservation, commitment or ledger event"; §14 lists "budget revision request receipt, link to a successor, Revised on activation, decline with reason, withdrawal ..." as append-only events; §4.7 funding ledger; §14 "Read/check calls do not create business or funding-ledger events" yet lists "owner decision evidence referencing a funding check" · **Module(s):** kentender_budget · **Sources:** trace-budget S-2
**Evidence**
- `BUD/services/budget_audit_contracts.py:41-44` — request events are `Budget revision request received/declined/withdrawn/revised`; `BUD/services/budget_revision_request_contracts.py:93,156,171,185` write them with `safe_record_event` into `Budget Audit Event`, the same table as funding events.
**Rule:** The document does not say whether request events and check evidence live in the funding ledger or in a separate audit stream; BUD-BR-027 and §14 cannot both hold for one table. Decision the owner must make: a separate audit stream for request/check events, or amend BUD-BR-027/§14 wording.
**Reproduction / failing test sketch:** (static; not run) `receive_budget_revision_request`; `Budget Audit Event` gains a "Budget revision request received" row, contradicting BUD-BR-027 as written.
**Impact:** Ambiguity makes AUD-BUD-005 and the request-event tests unprovable either way.

### AUD-NDS-012 — Successor / withdrawal mutual exclusion is enforced late, with the wrong code, and without a stale-source check
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §5.2/§5.3 (lines 414: "an accepted successor and a withdrawal request are mutually exclusive open changes; creation of either checks this under the stable Need lock"; "A changed accepted pointer fails approval with a stale-source result"), §9 `NDS_OPEN_SOURCE_CHANGE_EXISTS` (line 700), NDS11-AC-028/076 · **Module(s):** NDS · **Sources:** trace-needs C-05 (with rows 69, 70, 79)
**Evidence**
- `NDS/services/lifecycle.py:889` — `create_accepted_need_successor` checks only `_open_successor(doc)`.
- `NDS/services/lifecycle.py:1025` — `request_withdrawal` checks only `_open_withdrawal_request(doc.name)`.
- `NDS/doctype/departmental_need_review_task/departmental_need_review_task.py:26-42` — the single-open-task rule later raises `NDS_STATE_CONFLICT` (not the specified code, which is absent from `NDS/errors.py`) when the successor is submitted.
- `NDS/services/lifecycle.py:1107` — approval never compares `request.accepted_revision` with `doc.current_accepted_revision`; `NDS_SOURCE_STALE` is used only at `NDS/services/workspace.py:497` for the Planning read.
**Rule:** NDS §5.2/§5.3 as quoted.
**Reproduction / failing test sketch:** (static; not run) Accepted Need: `request_accepted_need_withdrawal` then `create_accepted_need_successor`: both succeed; `submit_need_revision` of the update then fails with "An open review task already exists". Reverse: with a Draft successor open, the withdrawal request succeeds and approval later withdraws the Draft (`lifecycle.py:1120-1127`).
**Impact:** Update tasks can be orphaned and users get the wrong error late; no data corruption path was found because the task rule still blocks submission.

### AUD-NDS-013 — Intake and usage ordering compares timestamps as strings
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §4.11 / NDS15-AC-001 ("an older `source_event_time` never replaces a newer one") · **Module(s):** NDS · **Sources:** trace-needs C-11
**Evidence**
- `NDS/services/usage.py:480` — `if existing.source_event_time and str(occurred) < str(existing.source_event_time):` (usage at line 207 is identical).
- `source_event_time` is an unvalidated string parameter of the whitelisted endpoint (`usage.py:436-445`); the stored value stringifies as `YYYY-MM-DD HH:MM:SS`; an ISO `T` value sorts after it (`T` > space).
**Rule:** NDS15-AC-001 as quoted.
**Reproduction / failing test sketch:** (static; not run) As Planner project position A with `source_event_time="2026-11-28 09:00:00"`, then position B with `"2026-11-28T08:00:00"`: B (older) replaces A. In-process Planning passes `now_datetime()` objects and is unaffected.
**Impact:** An older position can overwrite a newer one when an external caller uses a different timestamp format.

### AUD-NDS-014 — Usage projection keeps a third value "Not proceeding"
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §4.7 (line 296: "Only `Not included` or `Fully included`"), §17 · **Module(s):** NDS · **Sources:** trace-needs C-12
**Evidence**
- `NDS/constants.py:141-143` — `USAGE_NOT_PROCEEDING = "Not proceeding"`; `USAGE_VALUES = frozenset({USAGE_NOT_INCLUDED, USAGE_FULL, USAGE_NOT_PROCEEDING})`.
- `NDS/services/usage.py:186` — the usage endpoint accepts it; the usage doctype Select lists three options (`need_planning_usage_projection.json:49`); pinned by `T-CT:446`.
**Rule:** NDS §4.7 line 296 and §17; accepted exclusions belong to the disposition projection (§4.8).
**Reproduction / failing test sketch:** (static; not run) Planner calls `project_need_planning_usage(..., usage="Not proceeding", not_proceeding_reason="...")`: accepted although §4.7 allows two values.
**Impact:** A legacy v1.12 value can be written into a stream the spec reserves for confirmed Active-inclusion facts.

### AUD-NDS-015 — The Procurement Planner is given a full Needs workspace
**Severity:** Low · **Classification:** CODE DEFECT (the in-repo tests pin the build; owner to confirm which side is intended) · **Doc:** NDS v1.16 §1.1 ("Procurement Planner Departmental Needs landing page: Remove"), §10 (line 715: "it does not create a Planner landing page"), NDS11-AC-084 (line 1705: "no new Needs workspace") · **Module(s):** NDS · **Sources:** trace-needs C-13
**Evidence**
- `NDS/services/permissions.py:130-134` — Planner can view every Accepted Need; `permissions.py:306` resolves every active unit for site-wide roles including Planner.
- `NDS/services/workspace.py:217-370` — `get_workspace` returns a READY register for that principal.
- `public/js/departmental_needs/components/WorkspaceScreen.vue:51-55` — the Forbidden copy lists "Procurement Planner" among the responsibilities that open the page; the doc's DENIED copy names Author, HoD and Auditor.
- Pinned by `T-PM:737`, `T-NV:337`, `WorkspaceScreen.spec.js:52`.
**Rule:** NDS §1.1/§10/NDS11-AC-084 as quoted.
**Reproduction / failing test sketch:** (static; not run) User with only Procurement Planner: `get_needs_workspace()` returns `ok: True` with rows.
**Impact:** A removed landing page persists; no data beyond the Planner's documented accepted-Need read is exposed.

### AUD-NDS-016 — The Vue app reads error meaning from message text
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §9 (line 702: "Errors are stable service results, not inferred from … free-text exception messages") · **Module(s):** NDS (Vue) · **Sources:** trace-needs C-17
**Evidence**
- `public/js/departmental_needs/DepartmentalNeeds.vue:907` — `intake_closed: /submission is not open/i.test(errorSummary.value)`.
- `DepartmentalNeeds.vue:648` and `:757` — `/not found\.?$/i.test(e.message || "")` decides "masked" versus "load-failure" and the authority-changed path.
- Grep for "not saved" in non-spec Vue/JS finds no occurrence, so the specified "Your changes were not saved." sentence is not produced.
**Rule:** NDS §9 line 702 as quoted.
**Reproduction / failing test sketch:** (static; not run) Reword the server message for `NDS_INTAKE_NOT_OPEN`: the "intake closed" branch no longer fires.
**Impact:** UI behaviour silently changes with message wording; no server-side effect.

### AUD-NDS-017 — §7.1 lists a PE id in the accepted payload; §3/§4.2/§1.1 say the PE is implicit
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** NDS v1.16 §7.1 (line 514 "PE, OU and FY IDs") versus line 254 ("The site PE is implicit") and NDS-BR-001 (line 420) · **Module(s):** NDS · **Sources:** trace-needs C-18, trace-needs row 126
**Evidence**
- `NDS/services/events.py:62-87` — `accepted_payload` carries `org_unit_id` and `financial_year_id` only; pinned by `T-EV:149`.
- NDS lines 254 and 420 state the PE is implicit and never selected; line 514 lists a PE id in the same event.
**Rule:** the document contradicts itself.
**Reproduction / failing test sketch:** n/a (document inconsistency; a conformance test written to line 514 would fail, one written to line 254 would pass).
**Impact:** Consumers cannot tell whether a PE id is owed; no runtime consequence today.

### AUD-NDS-018 — Withdrawn Needs cannot be found from the register (owner decision open)
**Severity:** Low · **Classification:** SPEC GAP — decision for the owner: is the register, the technical search, or the route the discovery path for Withdrawn Needs? · **Doc:** NDS v1.16 header amendment ("Keep accepted, declined, withdrawn and superseded records discoverable under current permission"); OVS FOLLOW_UPS FU-OVS-58 (Open) · **Module(s):** NDS · **Sources:** trace-needs C-19
**Evidence**
- `NDS/services/workspace.py:319` — `if not allowed or doc.current_state == STATE_WITHDRAWN: continue`.
- `docs/mvp-1-r1/17_oversight_visibility/…FOLLOW_UPS.md` line 92 — "Needs: should a withdrawn Need be findable? The workspace drops them … Low — decision, Project Owner, Open".
**Rule:** header amendment as quoted; the document does not say where discovery happens.
**Reproduction / failing test sketch:** (static; not run) Withdraw an accepted Need; `get_needs_workspace` no longer lists it and no status filter offers it.
**Impact:** An author or auditor cannot locate a withdrawn Need except by typing its route.

### AUD-NDS-019 — NDS §14 seed fixture differs from the executable two-year seed world
**Severity:** Low · **Classification:** SPEC DEFECT (approved NDS §14 versus the seed runbook's two-year world; SEED-002 is itself proposed) · **Doc:** NDS v1.16 §14.1-§14.3 (design clock 24 Nov 2026, close 25 Nov 2026 23:59 EAT, four Needs with fixed titles) · **Module(s):** NDS, core seeds · **Sources:** trace-needs C-21
**Evidence**
- `kentender_core/kentender_core/seeds/calendar.py:32` — `AS_AT = "2027-06-18 10:00:00"`.
- `NDS/seeds/kentender_mvp_r1.py:106-125` — `YEAR_NEEDS` replays the §14 chronology 364 days earlier in year 1 and uses different titles and quantities in year 2; the file's own comment records the deliberate shift.
**Rule:** NDS §14.1 states the fixed clock and prerequisites; the build does not reproduce them.
**Reproduction / failing test sketch:** n/a (document-versus-fixture divergence; `T-SD` pins the seed, not §14).
**Impact:** None at runtime; the approved fixture description does not describe the data testers see.

### AUD-PLN-013 — Late-activation read labels ordinary successors as late and offers an action that then fails
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §4.7 (line 275: explanation belongs to the initial Plan Version), PLN18-UX-29 (line 2532: "normal in-year successor not mislabelled late") · **Module(s):** PLN · **Sources:** trace-planning F-28
**Evidence**
- `PLN/services/plan_read.py:2357-2359` — `applicable = bool(year_start and activated_at and getdate(activated_at) >= getdate(year_start))` for any Version; `:2381` `"can_explain": applicable and has_site_role(AO)`.
- `PLN/services/plan_governance.py:249-250` — `record_late_activation_explanation` refuses a successor (`based_on_version` set) with `PLN_STALE_WRITE`.
**Rule:** PLN18-UX-29 as quoted.
**Reproduction / failing test sketch:** (static; not run) Activate Version 2 mid-year; `get_publication_task` for it returns `late_activation.applicable: True, can_explain: True` for the AO; submitting an explanation yields `PLN_STALE_WRITE`.
**Impact:** Misleading late label and a dialog that cannot succeed.

### AUD-PLN-014 — Planning raises a Finance notification where the spec says Planning sends none
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §7.7 (line 1044: "Notification: none from Planning in any row"), PLN23-AC-001 (line 2676), PLN27-AC-007 (line 2715: "Planning sends no notification") · **Module(s):** PLN · **Sources:** trace-planning F-08
**Evidence**
- `PLN/services/plan_finance.py:232,236-251` — `_notify_finance_officers` calls `notifications.notify_task(... event_type="planning.finance_requested" ...)` after every `RequestPlanFundingConfirmation` that creates a task.
**Rule:** lines 1044, 2676, 2715 as quoted.
**Reproduction / failing test sketch:** (static; not run) Request funding confirmation on a complete plan: a `planning.finance_requested` notification log is emitted for each Finance Confirmation Officer.
**Impact:** A producer the approved spec excludes is active.

### AUD-PLN-015 — A withdrawn initial departmental plan leaves a stale Need position at NDS
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §5.1.2 position table (line 342: "an initial plan withdrawn before acceptance → No update needed") · **Module(s):** PLN, NDS · **Sources:** trace-planning F-10
**Evidence**
- `PLN/services/dpp_lifecycle.py:699` — `envelope.bump(root, current_state="Withdrawn", current_version="")`; line 704 then calls `publish_need_positions`.
- `PLN/services/needs_intake.py:287` — `if not root or not root.current_version: return "", []`, so no position is sent.
**Rule:** line 342 as quoted.
**Reproduction / failing test sketch:** (static; not run) Need N is "After current submission" against a returned initial Draft; HoD withdraws the Draft; NDS keeps "After current submission" for N.
**Impact:** The Need page can keep telling the Planner to "Finish reviewing" a plan that no longer exists.

### AUD-PLN-016 — Return issue entry ids are not validated
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 PLN19-UX-009 (line 2563: "validated exact entry or whole-submission scope") · **Module(s):** PLN · **Sources:** trace-planning F-12
**Evidence**
- `PLN/services/dpp_validation.py:93-96` — `"entry_id": cstr(row.get("entry_id")).strip() or None` is stored as given; it is never compared with the submission's entry snapshots. The gate is the Procurement Planner role.
**Rule:** line 2563 as quoted.
**Reproduction / failing test sketch:** (static; not run) `return_departmental_plan(task, issues=[{"entry_id": "DPPE-NOPE", "correction_required": "x"}], ...)` is recorded.
**Impact:** A return can point the department at a non-existent entry.

### AUD-PLN-017 — PLN_BASELINE_LOCKED is raised for only two edit shapes
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §8 / PLN18-AC-118 (a locked baseline "cannot be changed by any command once the owning Version has left Draft") · **Module(s):** PLN · **Sources:** trace-planning F-06
**Evidence**
- `PLN/services/plan_workbench.py:386-390` — `if version.version_status != "Draft" and any(k in values for k in ("baseline_invitation_date", *schedule.PERIOD_FIELDS)): fail("PLN_BASELINE_LOCKED")`; every other edit on a non-Draft Version raises `PLN_STALE_WRITE` (line 390).
**Rule:** the cited criterion; the edit is still refused, only the contract code differs.
**Reproduction / failing test sketch:** (static; not run) `save_plan_item` changing `title` on an Active Version returns `PLN_STALE_WRITE`, not `PLN_BASELINE_LOCKED`.
**Impact:** Wrong error code only.

### AUD-PLN-018 — WithdrawDepartmentalSubmission cannot withdraw a Submitted plan; spec is ambiguous (spec gap)
**Severity:** Low · **Classification:** SPEC GAP — decision for the owner: may the HoD withdraw a Submitted (awaiting Procurement review) departmental plan? · **Doc:** PLN v1.29 §5.1.5 (line 389 "Mutable candidate"), §7.2 (line 954 "submitted evidence never reopened"), §7.7 (line 1048: the Procurement review item clears on "Accepted, returned or withdrawn") · **Module(s):** PLN · **Sources:** trace-planning F-14
**Evidence**
- `PLN/services/dpp_lifecycle.py:693` — `if version.version_status not in ("Draft", "Returned") or cstr(root.current_version) != version.name: fail("PLN_DPP_STALE", ...)`.
**Rule:** the document says both that only a mutable candidate is withdrawn and that the review item clears on withdrawal, which presumes a Submitted plan can be withdrawn.
**Reproduction / failing test sketch:** (static; not run) HoD calls `withdraw_departmental_submission` on a Submitted version: `PLN_DPP_STALE`.
**Impact:** A submitted plan awaiting review cannot be recalled; the implementation follows the narrower reading.

### AUD-PLN-019 — Combination rule: PLN §5.6.2 and PLN18-AC-055 disagree; code adds an undocumented origin restriction
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** PLN v1.29 §5.6.2 (line 784: "same FY, Procurement Budget Line and currency"), PLN18-AC-055 (line 2417: "reject different Budgets or currencies") · **Module(s):** PLN · **Sources:** trace-planning F-21
**Evidence**
- `PLN/services/plan_workbench.py:104-109` — `COMBINATION_DIMENSIONS` = budget (the Procurement Budget, not the line), classification, unit, origin (Need versus direct requirement); the comment at lines 98-103 records "the Procurement Budget (not the individual line) carries the currency".
- `PLN/tests/test_plan_workbench.py:250` combines sources across two budget lines.
**Rule:** the two document sentences name different dimensions; no document sentence names "origin".
**Reproduction / failing test sketch:** n/a (document inconsistency; code follows the acceptance criterion, not §5.6.2).
**Impact:** Testers cannot tell which rule is authoritative; the origin restriction blocks combining a Need-origin and a direct source of the same category.

### AUD-PLN-020 — Technical-operator "Your turn" contradicts PLN27-AC-009 (spec defect)
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** PLN v1.29 §5.7 (line 811) and §7.7 (line 1061) versus PLN27-AC-009 (line 2717) · **Module(s):** PLN · **Sources:** trace-planning F-32
**Evidence**
- `PLN/services/next_step.py:476-482` — the authorised technical operator gets `KIND_YOUR_TURN` ("Retry publication" / "Check the publication result").
- PLN lines 811 and 1061 give that operator "Your turn"; PLN27-AC-009 says "Administrator and System Manager never receive Your turn or a fix from any Planning next-step answer."
**Rule:** the document contradicts itself; the code follows §5.7 (the comment at `next_step.py:479-480` calls it the one named exception).
**Reproduction / failing test sketch:** n/a (document inconsistency).
**Impact:** None at runtime; one of the two sentences must be corrected.

### AUD-PLN-021 — Statutory withdrawal for correction skips the segregation check (spec gap)
**Severity:** Low · **Classification:** SPEC GAP — decision for the owner: is "Withdraw for correction" covered by §6.4's "approve/return as statutory authority"? · **Doc:** PLN v1.29 §6.4 (line 892) · **Module(s):** PLN · **Sources:** trace-planning F-33
**Evidence**
- `PLN/services/treasury.py:176-210` — `withdraw_approved_plan_for_correction` calls `require_site_role(ROLE_PLAN_STATUTORY_APPROVER, actor)` and checks the collective reference, but never `require_not_segregated(... ACTION_STATUTORY_DECIDE ...)`; `approve_annual_plan` does (`plan_governance.py:532`).
**Rule:** §6.4 lists approve and return, not withdrawal.
**Reproduction / failing test sketch:** (static; not run) A user who signed the plan as Planner and holds the statutory role calls `withdraw_approved_plan_for_correction` on a held plan: not refused for segregation.
**Impact:** Possible maker-checker gap on the statutory withdrawal decision, depending on the owner's reading.

### AUD-PLN-022 — Departmental plan is auto-created on Need acceptance (spec gap)
**Severity:** Low · **Classification:** SPEC GAP — decision for the owner: may Need acceptance create the department's Draft plan without an Author/HoD "Start departmental plan" command? · **Doc:** PLN v1.29 §5.1.5 (line 383: "No DPP; permitted initial intake | Start departmental plan | Author or HoD"), §4.2 invariant 1 ("no creation from a read") · **Module(s):** PLN · **Sources:** trace-planning F-34
**Evidence**
- `PLN/services/dpp_autostart.py:57-70` — `on_need_event` calls `dpp_lifecycle.ensure_departmental_plan` on every `DepartmentalNeedAccepted.v2`.
- `PLN/services/dpp_lifecycle.py:244-319` — creates the root and Draft Submission 1 with no intake-window check and records the accepting user as actor; the docstring states this is deliberate and says "the intake window still governs every submission".
**Rule:** the document describes only the manual start.
**Reproduction / failing test sketch:** (static; not run) Accept a Need for a department with no plan: a Departmental Plan root and Draft version exist afterwards without any Planning command.
**Impact:** None found beyond an undocumented event-driven creation; pinned by `test_dpp_autostart.py:109-179`.

### AUD-REQ-011 — Item/service dates are validated at write time only
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §5.6, §5.8 · **Module(s):** Requisitions · **Sources:** trace-requisition F-16
**Evidence**
- `REQ/services/draft_commands.py:244-245` — `save_requisition_summary` assigns `version.latest_delivery_date` with no comparison to existing item or service dates.
- `REQ/services/draft_commands.py:295-297` and `:789-791` — the item/service date checks run only when those rows are written.
- `REQ/services/validation.py:158-177` — compares only the Version date to the Plan boundary and required-by date.
**Rule:** §5.6 `latest_delivery_date` "Defaults from Version; may be earlier, never later." §5.8 `completion_date` "not later than the package delivery date."
**Reproduction / failing test sketch:** (static; not run) Items dated 30 Sep, Version date 30 Sep; `save_requisition_summary(values={"latest_delivery_date": "<15 Sep>"})`; `validate_requisition` -> no finding; submit and authorise succeed; the handoff carries items dated after the package date.
**Impact:** The Tender inherits item dates later than the requisition's own latest delivery date.

### AUD-REQ-012 — `GetRequisitionHistory` omits drawdown/reservation/reversal/consumption evidence; outbox is never relayed
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §10.1, §9.2, §15 · **Module(s):** Requisitions · **Sources:** trace-requisition F-17; F-29 row 242
**Evidence**
- `REQ/services/read.py:914-926` — returns versions, decisions, correction outcomes and `Requisition Event` rows only.
- `REQ/services/handoff.py:105-137` — consumption writes no event or history row.
- `REQ/services/events.py:58` — `acknowledge` has no caller anywhere in the app; `EVENT_WITHDRAWN` (events.py:21) has no publisher (publishers: `authorise.py:145` authorised, `authorise.py:201` revoked, `correction.py:143`, `lifecycle.py:435`).
**Rule:** §10.1 `GetRequisitionHistory` "Versions, decisions, drawdown, reservation, reversal, upstream-correction and handoff-consumption evidence." §9.2 "publishes ... through the transactional outbox." §15 audit list includes "outbox publication and retry evidence; Tender handoff consumption".
**Reproduction / failing test sketch:** (static; not run) Authorise then consume; `get_requisition_history` has no consumption or reservation entry; `Requisition Event` rows stay `Pending` indefinitely.
**Impact:** An auditor cannot reconstruct consumption or reservation history from the module's own history read; events are persisted but never delivered or acknowledged.

### AUD-REQ-013 — Closed error codes with no raise site; "internally contradictory" Blocking finding unimplemented
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §11, §6.5 · **Module(s):** Requisitions · **Sources:** trace-requisition F-21; F-29 rows 82, 202, 206
**Evidence**
- `REQ/services/errors.py:25,30` — `REQ_QUANTITY_MISMATCH` and `REQ_REQUIREMENT_RESTRICTIVE` are defined; no `fail("REQ_QUANTITY_MISMATCH"...)`/`REQ_REQUIREMENT_RESTRICTIVE` call exists in the module; the conditions surface as findings `QUANTITY_MISMATCH` (`validation.py:215`) and `RESTRICTIVE_TERM` (`:250`) and are raised as `REQ_BLOCKING_FINDINGS`.
- `REQ/services/validation.py` has no rule for "a requirement is internally contradictory" (grep `contradict` finds nothing).
**Rule:** §11 closed error list incl. `REQ_QUANTITY_MISMATCH` ("Item and drawdown quantities do not reconcile. Show the affected line.") and `REQ_REQUIREMENT_RESTRICTIVE`; §6.5 Blocking: "a requirement is internally contradictory".
**Reproduction / failing test sketch:** (static; not run) Make item quantities not equal a drawdown line; `lifecycle.send_for_department_approval` raises `REQ_BLOCKING_FINDINGS` (detail holds `QUANTITY_MISMATCH`), never `REQ_QUANTITY_MISMATCH`.
**Impact:** A client keyed on the documented codes never receives them; the contradictory-requirement block cannot fire.

### AUD-REQ-014 — Planning outcome sequence gaps are not detected
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §9.1B (dedup/ordering paragraph), REQ19-AC-067 · **Module(s):** Requisitions, Planning · **Sources:** trace-requisition F-22
**Evidence**
- `REQ/services/correction.py:122-127` — only `if last is not None and int(event["producer_sequence"]) <= int(last): return _invalid(...)`; a skipped sequence is accepted silently and no replay/pending path exists.
**Rule:** §9.1B "Gap/out-of-order delivery triggers owner replay or an authoritative versioned snapshot; preserve last-confirmed status with a pending indication."
**Reproduction / failing test sketch:** (static; not run) Record outcome with `producer_sequence=1`, then one with `producer_sequence=5` for the same `correction_request_id` -> accepted with no pending indication.
**Impact:** A lost intermediate outcome is never detected; requesters see a status that may not reflect Planning's.

### AUD-REQ-015 — HOPF lead directive survives only the immediate successor Draft
**Severity:** Low · **Classification:** SPEC GAP · **Doc:** REQ-CHG-001 v1.14 §7.3A · **Module(s):** Requisitions · **Sources:** trace-requisition F-23
**Evidence**
- `REQ/services/lifecycle.py:140` — `"lead_routing_directive": lead_directive or None` on the copied Version; a later Return calls `copy_draft_successor` without a directive, so it is cleared.
- `REQ/services/draft_commands.py:204-212` — `_refresh_lead` returns early only `if version.lead_routing_directive`, otherwise recomputes the default and can change `root.lead_org_unit_id`.
**Rule:** §7.3A "Refresh the derived default after a Draft drawdown change, unless an explicit HOPF return directive fixes the new lead." The doc does not say how long a directive binds. Decision for the owner: does the directive persist across later returns?
**Reproduction / failing test sketch:** (static; not run) HOPF changes lead to OU-B (directive set); OU-B's HoD returns the successor; a drawdown amount save on the new Draft recomputes the lead back to the largest-value OU.
**Impact:** The lead department can silently revert after a second return.

### AUD-REQ-016 — Direct read of Budget's Funding Reservation table and import of a private Planning helper
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §3, §19; AGENTS.md §2 (cross-app via published service/API) · **Module(s):** Requisitions, Budget · **Sources:** trace-requisition F-28; F-29 row 5
**Evidence**
- `REQ/services/read.py:745` — `frappe.db.get_value("Funding Reservation", line.get("reservation_id"), "generated_reference")` reads a Budget table directly (Budget is a different app, `kentender_budget`).
- `REQ/services/funding_gateway.py:76` — `from kentender_procurement.procurement_planning.services.budget_gateway import _system_principal` imports a private (underscore) helper of another module (same app, but not a published surface).
(Reads of `Annual Plan`, `Plan Item`, `Tender` at `read.py:186,188,435,738` are inside the same app `kentender_procurement`, so only the Budget read is cross-app.)
**Rule:** REQ §3/§19 cross-app access through published owner services; AGENTS.md §2 "Cross-app interaction uses an explicit public service or API owned by the relevant app."
**Reproduction / failing test sketch:** static: grep `Funding Reservation` in `procurement_requisitions/services/read.py`.
**Impact:** Display-only coupling to Budget's table layout; no money moves.

---

### AUD-TND-011 — Reopen of an approved Tender skips the compatibility recheck
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 §5.3 · **Module(s):** Tenders · **Sources:** trace-tenders F-01
**Evidence**
- `TND/services/lifecycle.py:296` — `template_binding.require_bound(version, "continue")` is the only guard; `compatibility.require_supported` appears at `lifecycle.py:125` (submit), `:233` (approve) and `publication.py:70` (authorise) but not in `reopen_approved_tender` (`lifecycle.py:278-311`).
- `TND/services/compatibility.py:90-130` — the nine checks run on the stored snapshot plus the bound release (`support`) and the live `_is_county_entity()`, so only release support and the Site county flag can differ at reopen.
**Rule:** §5.3 "Compatibility is rechecked at Draft creation, submission, approval, reopening and publication authorisation against the exact immutable owner facts applicable to that action."
**Reproduction / failing test sketch:** (static; not run) Approve a Tender with a County-residents restriction; change `Site Procuring Entity.entity_is_county` to 0 (or switch the release's county support off); HOPF `reopen_approved_tender` -> succeeds, creating a Draft that will fail only at submit.
**Impact:** Limited: the copied Draft is rechecked at submission, so the rule violation is a missed early refusal.

### AUD-TND-012 — Doc says one publication authorisation per approved Version; code allows several after withdrawal
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** TPR-CHG-001 v0.17 §4.6 vs §5.11 · **Module(s):** Tenders · **Sources:** trace-tenders F-14
**Evidence**
- Doc line 312 (§4.6) "One publication authorisation per approved Version."; doc line 692 (§5.11, Withdraw) "Tender reopened for correction or a new authorisation decision."
- `TND/services/publication.py:222` — withdrawal sets `publication=None` and returns the root to `Approved`; `:56-60` then lets the same approved Version be authorised again, creating a second `Tender Publication` row.
**Rule:** the two doc statements conflict; the owner must state "one active authorisation" or forbid re-authorisation.
**Reproduction / failing test sketch:** (static; not run) Authorise, withdraw before any confirmation, authorise again -> two `Tender Publication` rows reference one `Tender Version`.
**Impact:** Ambiguity about the number of publication records per Version; no money or approval is affected.

### AUD-TND-013 — A true concurrent StartTender returns a conflict error, not the first Tender's identity
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 TPR09-AC-007 · **Module(s):** Tenders, Requisitions · **Sources:** trace-tenders F-15
**Evidence**
- `TND/services/draft_commands.py:96-103,135` — the "already consumed/existing" checks run before any lock; two concurrent starts both build a Tender inside `envelope.atomic("start")` and the loser hits `REQ_HANDOFF_CONFLICT` in consumption, surfaced as `TND_HANDOFF_CONFLICT` (rolled back).
**Rule:** TPR09-AC-007 "Concurrent or repeated `StartTender` requests for one handoff produce one Tender and return its identity."
**Reproduction / failing test sketch:** (static; not run) Two sessions call `start_tender` for one handoff with different idempotency keys at the same time; one returns `TND_HANDOFF_CONFLICT`; sequential repeats return `existing` (`TND/tests/test_lifecycle.py:118-124`).
**Impact:** Exactly one Tender survives; the loser sees an error rather than the identity, a retry resolves it.

### AUD-TND-014 — Back saves a dirty Draft silently; no "Leave without saving?"
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 §11.1 item 10, §11.3 · **Module(s):** Tenders · **Sources:** trace-tenders F-17
**Evidence**
- `kentender_procurement/kentender_procurement/public/js/tenders/Tenders.vue:475-485` — `onEditorBack` calls `api.saveTenderDraft(...)` when `editorRef.value.isDirty()` and then navigates; grep `Leave without saving` over `public/js/tenders` (excluding `dist/`) finds nothing.
**Rule:** §11.1(10) "Cancel and Back close the current transient surface without saving." §11.3 "Closing a page with unsaved ... changes gives **Leave without saving?** with Stay / Leave. No autosave is implied."
**Reproduction / failing test sketch:** (static; not run) Edit a Tender details field and press Back: a `SaveTenderDraft` call and a `TenderDraftSaved` event are produced and no prompt appears.
**Impact:** An unintended edit is persisted and audited without the user's confirmation.

### AUD-TND-015 — "Contact administrator" control is absent
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 §11.2 (Contact administrator), TPR10-IMP-007 · **Module(s):** Tenders · **Sources:** trace-tenders F-18
**Evidence**
- Doc line 1466 "Contact administrator | Opens the configured support instruction; it grants no permission and changes nothing."
- `kentender_procurement/kentender_procurement/public/js/tenders/` contains no "Contact administrator" (case-insensitive grep over `*.vue`/`*.js`, excluding `dist/`).
**Rule:** §11.2 control list; TPR10-IMP-007 "Consume CFG v0.16 public portal support/legal-link projection for bidder-safe Tenders surfaces".
**Reproduction / failing test sketch:** static: grep as above.
**Impact:** Users hitting a blocked or forbidden state have no governed route to the support instruction.

### AUD-TND-016 — Late-amendment window is a hard-coded 7 days, not a configured/verified rule
**Severity:** Low · **Classification:** SPEC GAP · **Doc:** TPR-CHG-001 v0.17 §4.8 (`deadline_extension_required`), §5.6, §21 counsel item · **Module(s):** Tenders · **Sources:** trace-tenders F-22
**Evidence**
- `TND/services/addenda.py:50-54,109-110,221` — `LATE_AMENDMENT_DAYS = 7` with the comment "Statutory figure verification pending"; `required = ... (current - now) < timedelta(days=LATE_AMENDMENT_DAYS)`.
- Doc line 2257 (counsel item): PPADA s.75(5) "requires the deadline to be extended when an addendum is issued with less than one third of the preparation time remaining ... not built or verified here".
**Rule:** §4.8 `deadline_extension_required` "Generated from issue timing and the applicable rule." The doc names no source for the rule. Decision for the owner: fixed days, one-third of the period, or a configured rule row.
**Reproduction / failing test sketch:** (static; not run) Tender with a 30-day period; issue an addendum with 8 days remaining -> no deadline extension required by the code, although one-third of 30 days is 10.
**Impact:** The extension trigger may be wrong for periods other than 21 days.

### AUD-TND-017 — Two TPR section 5.2 / AC rules have no field or server rule behind them
**Severity:** Low · **Classification:** SPEC GAP · **Doc:** TPR-CHG-001 v0.17 §5.2 (tender security row), TPR09-AC-014 · **Module(s):** Tenders · **Sources:** trace-tenders F-23
**Evidence**
- Doc line 474 "Tender security amount | Money, exact 2-decimal KES | Positive and within governed rule." vs `TND/services/controls.py:56` (`min_exclusive: 0` only) and `TND/services/review.py:197-198` (positive check only): no governed rule is named or read.
- Doc line 1721 TPR09-AC-014 "A physical meeting requires date/time, venue and access instructions" vs `TND/services/controls.py:58-61` (date/time, mode, venue link, online joining text) and §5.2 doc lines 476-478, which list no "access instructions" field.
(The issue-date rule "cannot precede publication readiness", doc line 467, is superseded by the v0.16 sentence in the same row that counts the period from the later of issue date and authorisation, so it is not claimed here.)
**Rule:** the two doc statements name rules no §5.2 field or rule source implements. Decision for the owner: name the governed tender-security rule source; add an access-instructions field or amend AC-014.
**Reproduction / failing test sketch:** static: set `tender_security_amount` to any positive amount; it passes. No physical-meeting access field exists.
**Impact:** Spec/implementation mismatch without a defect in existing behaviour.

### AUD-TND-018 — Certified lead and contributing OU identifiers are not on `GetTender`
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 header (OVS owner amendment), OVS-CHG-001 v0.6 §4.1 · **Module(s):** Tenders · **Sources:** trace-tenders F-24
**Evidence**
- Doc line 7: "Expose certified lead and contributing OU identifiers from the exact consumed REQ Version through the read model; do not invent independent editable copies."
- `TND/services/read.py:665-674` — the `tender` object in `get_tender` carries name, reference, titles, status, dates, publication, cancellation, template fields; no `lead_org_unit` or `contributing_org_unit_ids` (they are fetched only for the workspace list at `read.py:49-52`, and `tender_row` at `read.py:111` does not return them).
- `TND/services/draft_commands.py:110-118` and `TND/services/snapshot.py:116-125` — stored once at Start; lead falls back to the first contributor when no certification is carried (`snapshot.py:124-125`) and is stored null if the OU row does not exist (`draft_commands.py:118`).
**Rule:** header quote above.
**Reproduction / failing test sketch:** static: call `get_tender` for a started Tender; the response has no lead or contributor field.
**Impact:** The owner read model for oversight consumers must read the Tender columns directly instead of the published read.

### AUD-TND-019 — "Authorise publication" is offered when no publication rule exists
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 §5.10 (guard reasons), §11.1(1), §10.15 "Publication not configured" · **Module(s):** Tenders · **Sources:** trace-tenders F-27
**Evidence**
- `TND/services/read.py:379-393,414-418` — `period_problem` returns `None` when no minimum resolves, so `allowed_actions` appends `authorise_publication`; it does not consult `configuration_gateway.resolve_publication_rule`.
- `TND/services/publication.py:78` — the command itself raises `TND_PUBLICATION_RULE_UNAVAILABLE` via `resolve_publication_rule` (`configuration_gateway.py:72-79`), and the publication read shows it only as `rule_error`/`can_configure` (`publication.py:298-317`), not as a next-step blocker (`guidance.py` references seven `TND_*` codes, not this one).
**Rule:** §11.1(1) "every control is offered only when the command layer would accept it for this actor in this exact state"; doc line 664 "Authorise publication with no effective rule | `TND_PUBLICATION_RULE_UNAVAILABLE` ...".
**Reproduction / failing test sketch:** (static; not run) With no Open Tender publication rule in force, an Approved Tender's AO sees `allowed_actions` containing `authorise_publication`; pressing it raises `TND_PUBLICATION_RULE_UNAVAILABLE`.
**Impact:** A dead-end control shown to the Accounting Officer; the command refuses safely.

---

### AUD-EVL-018 — Published rounding mode (`ROUND_HALF_UP`) is ignored by the price calculation
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §4.1 (rounding from the rule) · **Module(s):** Evaluation, Bid Submission · **Sources:** trace-evaluation F-9 (row 31, 201)
**Evidence**
- `docs/mvp-1-r1/07_tender_templates/evaluation_rules/IT-EQUIPMENT-OPEN-V1.json:34` — `"rounding": "ROUND_HALF_UP"`
- `P/bid_evaluation/services/rules.py:255-256` — `(quantity * unit_price).quantize(Decimal("0.01"))` and `(before + tax).quantize(Decimal("0.01"))` use the default Decimal context (ROUND_HALF_EVEN); no code reads `numbers.rounding` (grep `ROUND_|getcontext|rounding` in `P/bid_evaluation/services/` finds nothing)
- `P/bid_submission/services/price.py:31,46` — Bid Submission quantizes with `rounding=ROUND_HALF_UP`
**Rule:** EVL §4.1: "Units, rounding, inclusive boundaries … come from the rule".
**Reproduction / failing test sketch:** (static; not run) `rules.calculate_price` with quantity "2.5" and unit price "0.01" (half-cent line): Evaluation computes 0.02, Bid Submission 0.03, so a correct bid reads "differs from calculated" and goes to Needs review. Unreachable with integer quantities and 2-dp prices.
**Impact:** Half-cent rounding disagrees between modules, creating false discrepancies in edge cases.

### AUD-EVL-019 — "Test attestation — not an electronic signature" label absent from Evaluation signing views
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** TRUST-ADR-001 v0_2 §2 (member signature row, line 31) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-17 (row 215)
**Evidence**
- `P/proceedings/test_services/attestation.py:19` and `P/award/services/opinion.py:28` define the label; no Evaluation file does (grep `test attestation|not an electronic signature` outside tests finds only `hooks.py`, `proceedings/`, `award/`, seeds)
- `P/bid_evaluation/services/signing.py:289-290` and `reads.py:263-272` return `member`, `name`, `signed_at`/`signed` only
**Rule:** TRUST §2 line 31: "UI/export labels it **Test attestation — not an electronic signature**. No fake certificate, initials image or 'signed' proof."
**Reproduction / failing test sketch:** (static; not run) Sign a report on a test site; the signing and signed views show "Signed" and a time with no attestation label.
**Impact:** A test attestation is presented as a plain signature in Evaluation (Award shows the label, `award/services/reads.py:69`).

### AUD-EVL-020 — A verification plan never clears the chair's discussion item
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §4.3 (line 104), §7.3 (line 284) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-22 (row 46, 214)
**Evidence**
- `P/bid_evaluation/services/diligence.py:47-84` — `record_plan` takes no bid/requirement and never calls `findings.clear_item` (grep `clear_item|open_item` in `diligence.py` returns nothing); `record_outcome` (`:223-255`) also never clears it
- `P/bid_evaluation/services/clarification.py:92,105-106` and `issues.py:52` do call `clear_item`
**Rule:** EVL line 104: "The discussion item clears only when its attributed resolved/qualified conclusion, specialised clarification authorisation or verification plan, or durable linked support issue is committed."
**Reproduction / failing test sketch:** (static; not run) Needs-review finding creates the chair item; chair records a verification plan and later a verification outcome; the item stays Open ("Resolve evaluation concern" remains in the chair's list, `my_work_provider.py:84-95`). The requirement itself resolves via the outcome conclusion.
**Impact:** A stale chair task persists after the documented clearing event.

### AUD-EVL-021 — A failed second package read after intake rolls everything back without recording an issue
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §5.1 (EVL_SOURCE_INCOMPLETE, line 306) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-24 (row 71)
**Evidence**
- `P/bid_evaluation/services/intake.py:122` — `ran = checks.run(doc, reason="Initial", idempotency_key=key)` runs inside the intake body
- `P/bid_evaluation/services/checks.py:144-148` — `checks.run` re-releases each package and, if it is not `VERIFIED`, calls `fail("EVL_SOURCE_INCOMPLETE", ...)`, which raises through `records.command`'s savepoint (`records.py:69-79`)
- `P/bid_evaluation/services/sweep.py:54-56` — the sweep rolls back, logs an error and opens no Support Issue (the issue is created only on the first load failure, `intake.py:74-89`)
**Rule:** EVL line 306: a failed intake "System creates one support issue automatically".
**Reproduction / failing test sketch:** (static; not run) Make the second release of any package return not-verified after the first succeeded (transient custody flap): the intake rows are rolled back and the sweep retries each minute with only an error-log row.
**Impact:** A transient fault between the two reads yields no support issue or waiting notice; low likelihood.

### AUD-EVL-022 — EVL v0_5 says the Head's item clears on "return" but `ReturnEvaluationReport` carries no source event
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** EVL-CHG-001 v0_5 §5.6 (line 172, 174) vs §7.2/§10 (lines 264, 589) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-23, D-6 (row 125)
**Evidence**
- EVL line 172 and 174: the Head's item "clears only on their recorded review or return/correction action … identify that source event"
- EVL line 264 and 589: `ReturnEvaluationReport` takes comments only, with no source-event argument
- `P/bid_evaluation/services/correction.py:269-284` — only `head_review` clears a Head item; `return_report`/`_apply_return` (`:111-123`) never touch `head_review_state`
**Rule:** The document contradicts itself: the clearing event "return" cannot name the source event it must identify.
**Reproduction / failing test sketch:** (static; not run) After delivery a supplement creates the Head's "Review opening update" item; the Head returns the report; the item stays Open until `record_head_review` is also called.
**Impact:** None beyond a stale Head item; the Head has `RecordHeadReview` as an explicit route. Owner should either add a source-event argument to the return or drop "return" from the clearing events.

### AUD-EVL-023 — EVL v0_5 control table, history and task-title claims are inconsistent
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** EVL-CHG-001 v0_5 control table (lines 11-18), §12.1 (lines 701-710), §5.6/§7.3 vs §12.4 N10 · **Module(s):** Evaluation (document) · **Sources:** trace-evaluation D-1, D-2, D-3
**Evidence**
- `docs/mvp-1-r1/15_bid_evaluation/KenTender_EVL-CHG-001_Bid_Evaluation_v0_5.md:13` — "Version / date | 0.4 · 30 September 2026" in the v0_5 file approved 3 October (line 3); lines 15-17 cite KT-STD-001 v1.12, TPR v0.13, BOP v0.10, TRUST-ADR-001 v0.1 although line 3 states TPR v0.16 changes are incorporated and TRUST-ADR-001 v0_2 exists
- same file `:701-710` — the history table has no v0.5 row and the v0.4 row (line 710) is detached from its table by a blank line
- same file `:295-296` — chair and Head opening-update items both titled "Review opening update for {tender}", while `:751` (N10) claims "distinct titles"
**Rule:** Internal consistency of an approved document used as the oracle for the code; the code follows the doc literally (`P/bid_evaluation/services/my_work_provider.py:197,201,204`).
**Reproduction / failing test sketch:** n/a (document review; static).
**Impact:** Traceability only; the approval header (line 3) remains the authority.

### AUD-AWD-012 — `RecordAwardDecision` does not read live tender status before committing
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.5 (line 141), §7 `RecordAwardDecision`, §8 `AWD_STATUS_UNAVAILABLE` · **Module(s):** Award · **Sources:** trace-award F5 (row 137)
**Evidence**
- `P/award/services/decision.py:107-138` — `record` calls `guards.open_case(doc)` (stored `doc.cancelled`, set only when `tender_events.consume` runs, `P/award/services/tender_events.py:73-77`) and `positive_guards`; it never calls `checks.tender_status` or `tender_events.consume`
- `P/award/services/notices.py:95-101` — `_stop_reasons` reads live status, so the batch is `Stopped` after the decision and the `AwardDecisionRecorded` event are already committed (`decision.py:63-64`)
**Rule:** AWD §5.5: the system "checks conditions again at decision, actual issue and Contracting delivery"; §8: unavailable status fails closed.
**Reproduction / failing test sketch:** (static; not run) Cancel the tender in Tenders (or `set_fact(tender, cancelled=True)`) before the Award sweep consumes the event; AO `record_decision(outcome="Award")` commits the decision, delivers `AwardDecisionRecorded` to Contracting, and the batch is Stopped.
**Impact:** Within the sweep lag a decision and a Contracting event exist for an already-cancelled tender; no notice goes out.

### AUD-AWD-013 — "Issue in progress" is not durable before the first outward effect and an interrupted issue has no recovery
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.4 (line 129-131), AC-010 · **Module(s):** Award · **Sources:** trace-award F6 (rows 53-55, 190)
**Evidence**
- `P/award/services/notices.py:129-130` — `records.update(batch, state="Issuing", status="Issue in progress", ...)` and `records.bump(doc, notification_status="Issue in progress", ...)` happen inside the same command transaction (savepoint, `P/award/services/records.py:142-150`) that then runs `_dispatch` for each notice (`:142-143`)
- `P/award/services/sweep.py:12-24` — no step recovers a case with `notification_status` "Issue in progress"/"Unknown"; `notices.retry_failed` handles only `status="Failed"`
- `P/hooks.py:174` — the only transport is the test mailbox (database-transactional), so the gap is latent
**Rule:** AWD §5.4: "A worker must verify that transition before the first outward effect. In-progress or unknown status cannot be treated as no notification. Recover an interrupted issue before allowing either route to proceed."
**Reproduction / failing test sketch:** (static; not run) Patch the transport to send then raise after the first of two recipients: the whole command rolls back including the "Issue in progress" marker while the first outward send stands. Assert `notification_status != "Not issued"` afterwards.
**Impact:** With a real channel, a crash mid-issue could leave an outward notice with `Not issued` recorded, allowing the pre-notification cancellation route.

### AUD-AWD-014 — Authority-status contract answers "no decision / not issued" from absence of a case
**Severity:** Low · **Classification:** CODE DEFECT (divergence from proposed spec: AWD-IF-02 is a proposed counterpart contract, §17.2) · **Doc:** AWD-CHG-001 v0_5 §7 (line 307), AWD-IF-02 (line 523) · **Module(s):** Award, Tenders, Evaluation · **Sources:** trace-award F9 (rows 149, 152, 214, 217)
**Evidence**
- `P/award/services/authority.py:36-41` — with no case `status()` returns `decision_status "No decision recorded"`, `notification_status "Not issued"` (source "No Award case"); `tender_status` returns `None` (`:54-59`)
- `P/tenders/services/evaluation_seam.py:193-197` — with no hook answer Tenders returns `{"status": "No award decision recorded", ... "source": "Tender status"}`; no durable tender-level status record exists (grep in `P/tenders` finds none)
- `P/hooks.py:171-172` — only `tender_status` (EVL vocabulary) and `cancellation_guard` (a string, no evidence/checked time) are published; `status()` (with notification fact, revision, `checked_at`) is not exposed
**Rule:** AWD §7: "Before an Award case exists, authoritative negative values must come from a durable tender-level record … Absence of a case or a failed lookup is insufficient."
**Reproduction / failing test sketch:** (static; not run) `tenders.evaluation_seam.award_decision_status(<tender with no Award case>)` → "No award decision recorded" with no durable record.
**Impact:** Spec conformance gap with little behavioural effect today: no decision can exist before an Award case does, and no notice can exist before a case.

### AUD-AWD-015 — `retry_operation` authority ignores effective dates
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §6 (line 279) · **Module(s):** Award · **Sources:** trace-award F15 (row 128)
**Evidence**
- `P/award/services/people.py:50-52` — `technical_operators()` selects `User Responsibility Assignment` with `status="Enabled"` only and no effective-period/derived-status check
- `P/award/services/recovery.py:52` and `P/award/services/reads.py:151` — `retry_operation` authority is `user in people.technical_operators()`
**Rule:** AWD §6: "Recheck active responsibility, scope, supplier link and signature authority at every action, not just page load." Contrast `people.holders` (`people.py:40-42`), which re-validates through `holds`.
**Reproduction / failing test sketch:** (static; not run) Give a user a Technical Operator assignment whose end date has passed but whose `status` is still Enabled; call `award.api.retry_operation`: accepted.
**Impact:** An expired technical operator can trigger idempotent retry of failed notice/event deliveries.

### AUD-AWD-016 — Award never checks the product profile or the published award method
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.1 (lines 93-94), §3 · **Module(s):** Award, Tenders · **Sources:** trace-award rows 17, 32
**Evidence**
- `P/tenders/services/award_seam.py:30` — `"award_method": "Lowest evaluated responsive tender"` is a literal; `product_key` is returned (`:29`)
- `P/award/services/sources.py:73` stores `award_method=facts.get("award_method", "")`; grep `product_key|award_method|GOODS-IT` in `P/award/services/` finds no comparison anywhere else
**Rule:** AWD §5.1: read-only checks cover "the recommendation's consistency with the published award method"; "The supported product is template key `IT-EQUIPMENT-OPEN-V1`, product profile `GOODS-IT-SIMPLE-V1`".
**Reproduction / failing test sketch:** (static; not run) Feed Award a delivered report for a tender with a different `product_key`: no check refuses it. Upstream, Evaluation's scope gate (`P/bid_evaluation/services/preparation.py:61-66`) already limits cases to the supported product, which bounds the effect.
**Impact:** The Award-side supported-scope and award-method consistency checks do not exist.

### AUD-AWD-017 — AWD v0_5 still carries "proposed"/"would establish" wording after approval
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** AWD-CHG-001 v0_5 lines 3, 8, 471, 538, 585 · **Module(s):** Award (document) · **Sources:** trace-award S1
**Evidence**
- `docs/mvp-1-r1/16_award/KenTender_AWD-CHG-001_Award_v0_5.md:3` — "Controlling approval — 3 October 2026" with "Earlier proposed/pending wording is drafting history superseded by this record"
- same file `:8` — "The proposed technical-reader rule is OVS v0.6 §4.2" (OVS-P05 is recorded approved, OVS v0_6 line 362); `:471` AC-027 "agree on Proposed status"; `:538` "Approval of this version would establish …"; `:585` "v0.4 is the current proposed successor. Approval … remain outstanding."
**Rule:** Internal consistency of an approved document used as the oracle.
**Reproduction / failing test sketch:** n/a (document review; static).
**Impact:** Implementers cannot tell whether OVS §4.2 (technical reader qualified read) is binding for Award; the code treats every technical user as operations-only (`P/award/services/people.py`, `reads.py:198-199`).

### AUD-AWD-018 — AWD v0_5 §15 says "Persist timestamps in UTC"; the project rule and the code store site time
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** AWD-CHG-001 v0_5 §15 (line 479) vs AGENTS.md §4.4 "Instants (owner decision 26 Sep 2026)" · **Module(s):** Award · **Sources:** trace-award S2 (row 212)
**Evidence**
- `docs/mvp-1-r1/16_award/KenTender_AWD-CHG-001_Award_v0_5.md:479` — "Persist timestamps in UTC and display the site timezone."
- `AGENTS.md:117` — "Store every instant as a naive datetime in the site timezone … Only a serialized message between modules … carries ISO-8601 UTC"
- `P/award/services/clock.py:1-11` and `P/award/services/events.py:34` — site time stored; UTC only in the event payload via `to_utc_iso`
**Rule:** The approved document contradicts the owner's later project rule.
**Reproduction / failing test sketch:** n/a (static).
**Impact:** None in code (it follows the project rule); the document should be corrected at the next version.


## 5. Appendix — duplicates and withdrawn entries

- **AUD-NDS-002** (Duplicate): [DUPLICATE of AUD-HND-002] Withdrawal approval checks one revision's local cache, treats "no projection" as clear, and calls no Planning validator

## 6. Appendix — source findings dropped, merged or downgraded by the writers

Each writer re-opened its sources and dropped or reduced what could not be proved. Full lists (with reasons) follow, unedited.


### _part-evl-awd.md

#### Dropped / downgraded

- trace-evaluation F-5 → merged into AUD-AWD-001 (evaluator/decider segregation) and AUD-EVL-016 (secretary declaration part).
- trace-evaluation F-7 (clarification disposition vs concurrent reply) → DROPPED. The stated interleaving cannot yield a Closed request with a committed reply: `submit_reply` locks the request row (`P/bid_evaluation/services/clarification.py:354`) then bumps the Evaluation Case row (`:370`) while `record_disposition` holds the case lock (`records.lock`, `records.py:85-90`) and later saves the request row held by the reply transaction, so InnoDB deadlocks and one side errors; and a stale-snapshot reply is rejected by Frappe's `check_if_latest` (`apps/frappe/frappe/model/document.py:1012-1038`, which reads `modified` `for_update`) because the disposition bumps the case. Not provable as a data-corrupting race.
- trace-evaluation F-14 (HoD "No responsive bids" reason lists bidder names) → DROPPED: OVS v0_6 §4.1 gives the HoD the outcome and its recorded reasons; bidder names are disclosed at opening; no rule violation provable.
- trace-evaluation F-15 (frozen content immutable only by convention, digest not re-verified on read) → DROPPED: no command path mutates a frozen version's `content_json` (only `signing.py:106` on a draft; `save_narrative` edits drafts only) and the controller blocks Desk saves without the command flag; remaining exposure is the general System Manager/DB write surface owned by the xc-authz part (immutable-records cluster).
- trace-evaluation F-18 (untested paths) → skipped per map; test gaps are not findings.
- trace-evaluation F-20 (EVL_REPLY_OVERDUE / EVL_EVALUATION_OVERDUE sentences re-typed in browser) → DROPPED: the evaluation sentence is also returned by the server (`reads.py:103`), wording is identical, no behavioural consequence.
- trace-evaluation D-4 (OVS §4.2 "proposed" vs P05 approved) and D-7 (tie-break source unnamed) → DROPPED as document-wording notes without a defect (D-4 covered by AUD-AWD-017's note; D-7: code states "The published tender has no tie-break rule", `comparison.py:37`, which the doc does not contradict); D-1, D-2, D-3 → AUD-EVL-023; D-5 → AUD-AWD-001; D-6 → AUD-EVL-022.
- trace-evaluation rows 59/70/78/108/172/193 (issue holder named HoP not Tenders owner; no waiting notice to AO; suspension guard coverage of some commands; report content lacks tender/criteria versions inline; evidence re-linking; unpaged register) → not written: no document rule violated beyond doubt, or the content exists in the evidence manifest (`evidence_manifest.py:94-106`); register paging belongs to AGENTS.md §6.11 UI scope and is not a defect in the audited rule set.
- sweep-sod F6 → AUD-EVL-013 (downgraded from CODE DEFECT to SPEC GAP: BOP-A17 says "later … Evaluation appointment", so the code follows BOP; EVL §3 is unqualified).
- sweep-sod F7 → merged into AUD-EVL-001 (classified CODE DEFECT rather than SPEC GAP because eligibility requires "no unresolved conflict" and the AO is the named resolver).
- sweep-sod F8 → merged into AUD-AWD-001; sweep-money F11 → merged into AUD-AWD-002; sweep-handoffs F-15 → AUD-EVL-014.
- trace-award F7 and F16 → owned by xc-core (concurrency / idempotency); not written. Source ids F17 and F19 do not exist in trace-award.
- trace-award F13 (signed opinion / decision / closed cycle immutable only by convention) → DROPPED: `working_opinion` excludes Signed rows so `opinion.save` cannot update a signed opinion; controllers block Desk writes; same residual as the immutable-records cluster.
- trace-award F14 (`respond()` does not check `n.status == "Given"`) → DROPPED: AWD §5.9 line 202 says "current issued notice", and the notice is issued/published when the batch is Issued; the doc does not require "given" evidence before a response, so a server/read-projection mismatch is not a rule violation.
- trace-award F18 (out-of-date draft text overwritten on re-save) → DROPPED: the draft stays readable while Out of date; AWD §5.3 does not require retaining text after the HOP re-saves.
- trace-award row 126 (technical read: no "after governed release" qualified read) → DROPPED: the code is stricter than OVS §4.2, and the document marks §4.2 proposed (AUD-AWD-017).
- Downgrades by the severity scale: trace-award F3 High → Medium (Contracting receiver is a simulation; latent), F5 Medium → Low (batch is stopped by the live check at issue), F6 Medium → Low (only transport is DB-transactional test mailbox), F9 Medium → Low (no decision/notice can exist without a case); trace-evaluation F-21 recorded as SPEC GAP (Medium); F-13 Low/Medium → Medium; F-17 Low/Medium → Low; trace-award F20 Low → Medium (documented flow dead-end on a responsibility change).
- Added beyond the source candidates, each verified: AUD-EVL-015 (missing Tenders producers; from trace-evaluation row 77 and trace-award rows 66/73/145), AUD-AWD-009 (No-award follow-up cannot be completed; trace-award row 81), AUD-AWD-010 (debrief gate; trace-award row 72), AUD-AWD-016 (trace-award rows 17/32), validity-unknown part of AUD-AWD-002 (trace-award row 65).



### _part-hnd.md

#### Dropped / downgraded

- sweep-handoffs F-5 (successor Need acceptance never projects) — owned by the nds-pln part; only referenced as the trigger in AUD-HND-002.
- sweep-handoffs F-9 (Strategy snapshot timing/FY) — owned by the nds-pln part.
- sweep-handoffs F-12 (Planning-Budget float arithmetic/epsilon) — owned by xc-core item 7; the budget-revision float part is not repeated in AUD-HND-005.
- sweep-handoffs F-15 (Evaluation funding read swallowed) — owned by the evl-awd part.
- sweep-handoffs F-6 (permissive defaults on the REQ handoff) — DROPPED. Verified: a v1.4 handoff always carries `departmental_certification.lead_org_unit_id` because `authorise.py:101` refuses authorisation unless `certified_lead_org_unit_id == root.lead_org_unit_id`, so the `units[0]` fallback (`tenders/services/snapshot.py:116-125`) is unreachable for an authorised handoff; a null `reservation_category` meaning "None" is a legitimate value (REQ writes `"None"` at draft, `procurement_requisitions/services/draft_commands.py:153`); Planning always sends `"award_packages": 1` (`plan_requisition.py:326`) and REQ's own check (`procurement_requisitions/services/compatibility.py:115,129`) runs at authorisation, so Tenders' default is redundant, not wrong. What remains is robustness of the Tenders reader against a renamed key, which is a missing-test concern, not a rule violation.
- sweep-handoffs F-13 (Tenders contract test pins source substrings) — DROPPED: missing/weak tests are not findings by themselves; its calibration facts are in "Calibration notes".
- sweep-handoffs F-16 (Award -> Contracting has no production consumer) — DROPPED: AWD v0_5 §13 specifies "synthetic ... Contracting adapters only" and treats Contracting as a separate module (`award/services/contracting.py:8-14` documents "No Contracting module exists on this bench"); delivery waits with a named technical owner as §5.8 requires. Documented absence, not a defect.
- sweep-handoffs F-17 (capture digest vs current digest disagree for a non-Active Budget line) — DROPPED: verified the digests differ (`financial_basis.py:50,62` vs `:140`), but the divergent state is a Plan with an unknown/ineligible line, which cannot be Confirmed, so `funding_is_current` (`plan_finance.py:104`) is never decisive there; only the display flag `basis_current` (`plan_read.py:1771`) is affected. No document rule broken, no reachable consequence beyond a stale flag.
- sweep-handoffs F-18 (events produced with no consumer / unread payload) — DROPPED: no approved document requires Planning to consume `DepartmentalNeedSuperseded/Withdrawn` (PLN v1_29 does not mention them) or BDS to read the Tender submission handoff payload (BDS reads the Tender root); REQ §9.2 specifies publication via outbox, not a named consumer or event body.
- sweep-handoffs F-19 (inconsistent "published surface" for cross-app imports; `_call` catches only ValidationError) — DROPPED: AGENTS.md §2 allows "published service or API" and the imported modules are the owners' `*_contracts` services (also exposed via `budget_api`); no document names a narrower list. The `PermissionError` mapping only differs when `authorise_requisition(user=...)` is called with a user other than the session user, a programmatic-only path; for the normal path the actor equals the session user and is a Head of Procurement Function, which the Budget gate accepts.
- sweep-handoffs F-20 (EVL/BOP comment contradicts producer; first-package definition used) — DROPPED: informational comment drift; whether bids made against different definition versions can coexist is an Evaluation question owned by the evl-awd part.
- sweep-handoffs F-21 (supplier-provider failure -> silent empty audience in Award gateway) — DROPPED: the notice itself is still dispatched by email and portal (`award/services/notices.py:131-146`); only the supplementary in-app notification would be empty. No document rule.
- sweep-handoffs F-22 (REQ hard-coded KES; Tenders sums money via float) — DROPPED: REQ §5.14 specifies "KES scale 2 from BUD CurrencyBasis" and the product is single-currency; the Tenders float sums (`tenders/services/snapshot.py:104-113`) feed a display string and `authorised_value` that no Evaluation or Award code reads numerically (`grep authorised_value` in `bid_evaluation`/`award` is empty). Float-money arithmetic as a root cause is owned by xc-core item 7.
- trace-requisition F-18 -> merged into AUD-HND-009; F-19 -> AUD-HND-011 (subitem (b) kept as a document conflict, subitem (c) kept as a spec gap observation); F-24 -> merged into AUD-HND-006; F-25 -> merged into AUD-HND-007.
- trace-tenders F-16 -> merged into AUD-HND-009; F-4 (late final confirmation strands Tender) is not in this part's scope per the map; F-10 -> AUD-HND-008.
- Downgraded: sweep-handoffs F-14 from "Medium-High" to Medium (read-only projection; the invitation date itself still reaches Planning); sweep-handoffs F-10 from Medium to Low (no consumer reads the divergent keys); trace-requisition F-24/F-25 from Low to Medium (as merged, the error semantics and lineage field fall under the Medium definition).



### _part-nds-pln.md

#### Dropped / downgraded

- trace-needs C-01 (client `user` parameter) — owned by xc-authz item 1; C-06 (DocPerm write/create) — xc-authz item 4; C-09 (projection endpoints open to any human Planner, caller-chosen values) — xc-authz item 12 (the consumer-machinery half is in AUD-NDS-010); C-22 (float quantity, no UOM precision) — xc-core item 7; C-23 (replay answered before authorisation) — xc-core item 11. Not written here.
- trace-needs P-01..P-06 (grouped Partial/Untested rows: CFG verdict re-implementation and `NDS_CONTEXT_REQUIRED` for a disabled FY, hash omits UOM basis, decision keeps assignment id but no snapshot, `Need Withdrawal Request` not registered with technical search, workspace paging, untested transitions) — not promoted: each is either a missing test or a Low partial with no defect shown against a quoted rule; not re-verified individually.
- trace-needs C-05's stale-source sub-claim (row 79) is folded into AUD-NDS-012 rather than written separately.
- trace-planning F-02 — downgraded High to Medium (AUD-PLN-009). The "affected_item_version_id" part was DROPPED: PLN §7.2 line 971 calls it "optional" and PLN19-UX-010 keeps whole-Plan return valid, so its absence is not a defect. The missing collective resolution on return and the 500-character cap were re-verified.
- trace-planning F-05 (segregation pairs untested) — missing tests are not findings.
- trace-planning F-13 — merged into AUD-NDS-009; sweep-handoffs F-9 — merged with F-16 into AUD-PLN-005 (its fiscal-year argument is kept but noted as arguable, because PLN line 1021 asks for the "current eligible Strategy version").
- trace-planning F-22 (Open Tender pre-selected on item formation) — DROPPED: the pre-selection is only an initial value; `PLN/services/readiness.py:399-428` still blocks submission with `PLN_METHOD_NOT_ADMISSIBLE` / `PLN_REFERENCE_UNAVAILABLE` when no complete profile permits it, so PLN18-AC-101 is met at the gate.
- trace-planning F-32 second half ("technical operator has no My Work item") — DROPPED: no rule in PLN §7.7 requires one and the claim was not provable from a quoted sentence.
- trace-planning F-16, F-19 — severity lowered from "Medium-High" to Medium after re-reading (checks exist at edit time; the gaps are at submission/activation).
- trace-planning F-11, F-17, F-27, F-29, F-30, F-31, F-03, F-07, F-15 — owned by xc-authz / xc-core per the ownership map; not written here.
- sweep-handoffs F-7 (disposition event contract) — owned by hnd; AUD-NDS-009 states the same enum root cause from the Needs/Planning side and cross-references it.



### _part-req-tnd.md

#### Dropped / downgraded

- trace-requisition F-27 (no migration for section 20 cutover) -> DROPPED: §20 asks for inspection and controlled migration of live records and says existing Versions "remain immutable and are rendered through the new result-first disclosure"; it names no mandatory patch, and validation computes the three tasks dynamically. No provable rule violation; the TPR rejection of legacy v1.3 handoffs (`TND/services/handoff_gateway.py:77-78`) is the handoff-version issue owned by the hnd part.
- trace-requisition F-29 residual rows: row 5 -> folded into AUD-REQ-016 (and narrowed: `Annual Plan`/`Plan Item`/`Tender` reads are same-app); row 17, 24, 44, 58, 62 (root field `reservation_ids`, `Superseded` no trigger, task display field, requirement-type proxy, Planning hard-coded KES/1) -> DROPPED, doc-silent or by-design with no rule violated; row 30/60 (county id equals base id; overlap treatment never checked on the REQ side) -> DROPPED, `compatibility.py:97-105` does check county support and rule availability, and the duplicate id is how Planning publishes one regulatory reference (see Calibration notes 2); row 41 (subjectivity heuristic) -> DROPPED, SPEC GAP below the Low floor; rows 49, 56 -> owned elsewhere (hnd / xc-core money); row 75 -> promoted to AUD-REQ-006; rows 82, 202, 206 -> AUD-REQ-013; row 134 -> folded into AUD-REQ-007; rows 148, 150, 249 -> test/evidence gaps; row 158-160 -> AUD-REQ-008; row 165, 175 -> API naming only; row 168 -> display read, owned by xc-core item 7; row 236, 238, 240, 283, 284, 286-292 -> UI/usability/evidence rows not assessable by static reading; row 242 -> AUD-REQ-012; row 248 -> same as F-27.
- trace-requisition F-02b -> kept separately as AUD-REQ-003 and classified SPEC GAP (the doc's AC-045 phrase "no self-authorisation" is not defined for preparer-as-authoriser).
- trace-requisition F-17 outbox part -> kept in AUD-REQ-012 at Low (no consumer reads the events; Tenders pulls the handoff).
- trace-tenders F-20 (clarification `received_at` supplied by caller) -> DROPPED: `receive_tender_clarification` is gated to the registered producer identity (`candidate_gateway.require_producer(user)`, `TND/services/clarifications.py:57`), and doc line 381 describes `received_at` as the inbound receipt instant supplied with the question.
- trace-tenders F-25 (post-close cancellation absent) -> DROPPED as a finding: the doc itself marks the v0.14 post-close route proposed and owner-gated ("until then v0.13 is the operational baseline", doc line 1965); code matches the gate (`TND/services/cancellation.py:52-56`). Recorded in Calibration notes as "divergence from proposed spec".
- trace-tenders F-26 (`Tender Event` payload rewritten on rejection) -> DROPPED: the row is an outbox record with a mutable `status`; `mark_rejected` (`TND/services/events.py:116-121`) adds `rejection_reason` to the payload of a delivery record, not to a business audit event.
- trace-tenders F-28 (representative-user, accessibility, property tests absent) -> DROPPED: process/test gap, not a code or doc defect.
- trace-tenders F-01 -> DOWNGRADED Medium to Low and reproduction corrected (compatibility runs on the stored snapshot, so changing the live handoff, as the source suggested, does not affect reopen; only release support and the Site county flag can differ), see AUD-TND-011.
- trace-tenders F-02, F-06 -> kept at Medium; F-03 kept at High (legally material: closed Tender's deadline rewritten); F-04 re-classified from CODE DEFECT to SPEC GAP (no governed command named by the doc) but held at High under the "documented flow dead-ends" rule.
- Not mine, not written: trace-tenders F-10, F-16 (hnd), F-11, F-12 (xc-authz 13), F-19 (xc-core 6); trace-requisition F-01, F-07 (xc-authz 5), F-03, F-12 (xc-core 1), F-11, F-20 (xc-core 7), F-14 (xc-core 11), F-18, F-19, F-24, F-25 (hnd), F-26 (skip). AUD-TND-005 is the Tenders instance of the xc-core cluster "denial events never written / rolled back on throw"; AUD-REQ-010 and AUD-TND-010 share `CORE/services/file_integrity.py:71-82` and are kept as two findings because the governing rules and owners differ.



### _part-str-bud.md

#### Dropped / downgraded

- trace-strategy F1a → written as AUD-STR-001 at High (lead downgrade from Critical; the Strategy Author capability gate on the named version was verified and is not bypassable by a non-Author).
- trace-strategy F2 → owned by xc-authz item 4 (business-role DocPerm write on state-bearing doctypes); not written here. Related Strategy-specific evidence (validators let `status` be set directly, `STR/services/strategy_domain_guards.py:125-135`) belongs there.
- trace-strategy F22 → owned by xc-authz item 5 (Audit Event mutable); only mentioned in AUD-STR-001 evidence.
- trace-strategy F8, F9 → owned by xc-core item 11 (idempotency journal/optional tokens); only referenced in AUD-STR-009.
- trace-strategy F24 → test gap, skipped as instructed.
- trace-strategy F4 → written as AUD-STR-005 at Medium (trace said High): reachable by signed-in, non-Guest sessions only, no money or approval reachable, Draft ids needed for Draft lineage.
- trace-strategy F12 → written as AUD-STR-013 at Low (trace said Medium): the resolver still requires plan-period overlap so no downstream effect.
- trace-strategy F6 → written as AUD-STR-012 at Low (trace said Medium): a withdrawal path is blocked but another Approver can act.
- trace-strategy F7 (+ sweep-sod F10) → written as AUD-STR-006 reclassified SPEC GAP (trace/sweep said code defect with a spec gap): the document does not define "author", and the code's reading (submitter) is one defensible choice; owner decision stated.
- trace-strategy F10 → AUD-STR-007 keeps only the downstream-contract and snapshot event gaps; the "denial event never written" half is owned by xc-core item 4 and not duplicated.
- trace-strategy F19 → split into AUD-STR-016 (code: untyped validation errors) and AUD-STR-017 (spec: §9 versus AUTH §10).
- sweep-authz F-12 → merged into AUD-STR-005 (stated at Medium; sweep's CODE DEFECT confirmed).
- trace-budget F-07 → written as AUD-BUD-004 at Medium (trace said High): latent, no in-repo caller beyond seeds, and the document's "within the reservation lineage" is not explicit about multi-reservation contracts.
- trace-budget F-22 (grouped) → split into AUD-BUD-010 (inactive catalogue), AUD-BUD-013 (token), AUD-BUD-014 (release status, close). Dropped as not provable against a specific rule in this pass: "`link_successor` can modify closed requests" (`budget_revision_request_contracts.py:246-251`), "`View Plan Item` route built by naming rule" (`budget_contracts.py:251-255`), "read contracts raise PermissionError instead of inline verdict", "`submit_budget_version` takes no row lock on the Draft" (the Draft is re-read and status-tested `budget_readiness_contracts.py:558-566`; §12.2 lock wording not tied to a failure), and "return reason stored on Version / funding-source label read live".
- trace-budget F-01, F-10, F-03 → owned by xc-authz item 3 (money-moving endpoints). F-02 → xc-authz item 4. F-05, F-13 → xc-core item 1. F-04, F-17 → xc-core items 2 and 3. F-06 → xc-core item 7 (and its spec side S-5, the 18-digit storage question, is mentioned only here). F-21 → xc-core item 11. F-23 → skipped (test gap).
- trace-budget S-3 → written as AUD-BUD-012; S-4 → merged into AUD-BUD-003; S-6 → merged into AUD-BUD-008 and AUD-BUD-015; S-5 → left to xc-core item 7.
- trace-budget F-19 → AUD-BUD-015 limited to what was re-opened: generated line references, `BUD-SC-FIN-*` names and the relative approval date. The trace's further claims (V2 profile without the 80m hold, `_offset_date(15)` for event dates beyond line 557) were not re-opened in full and are not asserted.



### _part-xc-authz.md

#### Dropped / downgraded

- sweep-authz F-26 (AO/HOPF have no Frappe-level read on Departmental Need): dropped. The hooks only restrict, AO/HOPF reads work through `can_view` (`permissions.py:136-139` region), and no document requires Desk form access for them.
- sweep-authz F-27 (`report_match_conditions` has no production caller): dropped, informational; there is no Query/Script Report, so AUTH §5.4 is met vacuously.
- trace-planning F-31 (Budget decision-time contract whitelisted): downgraded out of this list. `validate_plan_affordability_for_decision` takes `FOR UPDATE` locks that release when the HTTP request ends, is gated by `require_budget_version_read_scope` (budget_line_contracts.py near :617), and writes nothing. Only the whitelist exposure is folded into AUD-XC-002 as "no in-repo HTTP caller needs it".
- sweep-authz F-18, non-TM2 parts (Tender Configurations 103 endpoints, Procurement Lifecycle journeys, Procurement Home client-chosen PE): not assigned to any part in the ownership map, not independently re-verified here, and part of the OD-F legacy deferral. Not written; the TM2 part is in AUD-XC-003.
- sweep-authz F-06 repro as written ("`PUT` an accepted revision `{"title":"changed"}` alters the baseline"): corrected. `departmental_need_revision.py:37-47` refuses that plain edit; the bypass needs `revision_status` set to `Draft` in the same save (AUD-XC-008).
- trace-strategy F2 (Critical): downgraded to High. It needs the Strategy Author role (a registered responsibility, not any account), and the `DELETE` repro is blocked by Frappe link checks when nodes exist.
- sweep-authz F-09 (technical hooks return True on every ptype) and sweep-sod F15 (Requisition controllers have no immutability guard): merged into AUD-XC-013; the hook behaviour is quoted there.
- sweep-sod F14 (`sod_tags` unused, no self-grant guard): not in this part's map (xc-core "SoD residuals").
- sweep-authz F-12 (Strategy consumer endpoints open to every login): owned by the str-bud part.
- sweep-authz F-22 SPEC DEFECT half and F-24: kept as AUD-XC-016 and AUD-XC-028 respectively, with the NDS and BOP/OVS conflicts quoted.
- sweep-hazards F-3 second half (`action_availability` actor): folded into AUD-XC-003.



### _part-xc-core.md

#### Dropped / downgraded

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



## 7. Appendix — observations outside the findings

- **Concurrent Playwright session.** While the audit ran, `git status` went from clean to ~75 modified files, all PNG screenshots under `docs/mvp-1-r1/*/evidence/` and `tests/ui/**/*-snapshots/`, with mtimes up to 20:53 and Playwright/Chromium processes running. The audit agents were read-only and ran no tests; this is another session’s visual run. It was left untouched.
- **Document defects found while tracing** (also listed as SPEC DEFECT findings where material): REQ v1.14 §7.4 cites TPR §10.4 where the correction route is §10.14; REQ v1.14 and TPR v0.17 still specify handoff v1.3 while code and E2E run v1.4; EVL v0_5’s control table reads "0.4 · 30 September 2026"; NDS §7.1 lists a PE id while §3 says the PE is implicit.
- **Supporting files:** `audit/trace-*.md` (8) hold the row-by-row status tables; `audit/sweep-*.md` (7) hold the grep patterns, coverage tables and "checked and clean" lists; `audit/_part-*.md` are the writer slices that this file concatenates; `audit/_verify-*.md` are the verifier notes.
