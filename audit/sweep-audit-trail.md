# Sweep: audit-trail (completeness of the audit trail)

Status: static read only. Nothing was executed against a site or database. Every behavioural claim about Frappe is tied to the installed framework source at `/home/midasuser/frappe-bench/apps/frappe/frappe/` or is marked "needs live confirmation".

## 1. Header

**Scope.** AGENTS.md and the module docs require actor, time, reason and evidence for every material action: state transition, decision (approve, reject, return), override, cancellation, reassignment, configuration change, release or unseal of sealed content, access to sealed or confidential bid content, delegation, export and publication. This sweep checks four things:

1. every material command writes an audit record;
2. the record carries the fields the governing document requires;
3. the record is written in the same transaction and cannot be skipped;
4. the records are append-only.

**Docs read (latest versions confirmed with `ls | sort -V`).**
- KT-STD-001 v1_25: §2.9, §3B and §6; the "Audit and historical integrity" release-evidence row (§6, row 12); the AGENTS.md instants override.
- AGENTS.md §4.3–§4.5.
- AUTH-ADR-001 v1_11: §9.2, §15 and the §371 line on Setup writes being "validated and audited".
- TRUST-ADR-001 v0_2.
- STR v1_9: §4.6 and §13.
- BUD v1_12: §4.7, §4.10 and §14.
- NDS v1_16: §4.5 and §13.
- PLN v1_29: §12.
- REQ v1_14: §15.
- TPR v0_17: §12.1–§12.3.
- BOP v0_11: §12.
- BDS v0_11, searched for audit and immutability rules.
- EVL v0_5, searched for audit and immutability rules.
- AWD v0_5: §12.
- OVS v0_6: lines 66, 102 and 154, the sealed-content and access-logging statements.

**Docs not read.** The prompt names "BDS/BOP/EVL v0_5". BDS and BOP are at v0_11 in `12_bid_submission` and `14_bid_opening`; only EVL is v0_5. I used the latest of each.

**Method (reproducible).**
- Doctype inventory: a Python script (`glob` + `json`) over `kentender_*/**/doctype/*/*.json`. It prints name, `track_changes`, `istable`, DocPerm rows with create/write/delete, and whether the `.py` controller defines `validate`, `before_save` or `on_trash`.
  - Filtered by regex `audit|event|history|decision|log|access|incident|verification|release|trail|ledger|snapshot|usage|signature|custody|seal|unseal|reveal` for the first pass.
  - Run unfiltered per module for Strategy, Budget, NDS, Planning, Requisitions, Tenders, BDS, BOP, PRC, EVL, AWD, Core and STD Templates.
- Shared writers: `grep -rn "log_audit_event(" --include=*.py kentender_*` excluding tests and seeds, and `grep -rn "def .*audit\|record_event\|emit"`.
- Command enumeration: `ast` walks of each module's `services/*.py` for public functions taking `idempotency_key`, tested for a journal, event, decision or audit call. This is a heuristic; misses were then read by hand.
- Transaction and commit checks:
  - `grep -rn "frappe.db.commit()"` excluding tests, seeds and patches;
  - `grep -rn "update_modified=False"`, filtered by `status|state`;
  - `grep -rn "flags.commit"`, which found nothing;
  - Frappe `app.py` `sync_database` (lines 417-428) and the exception path (lines 138-141).
- Swallowed audit writes: `grep -rn "except Exception" -B6` around audit calls; `safe_record_event`.
- Append-only checks: the DocPerm table above, controller guards, `grep -rn "delete_doc(\"Audit Event\|set_value(\"Audit Event"`, and `has_permission` / `permission_query_conditions` hooks in each app's `hooks.py`.
- Read and export checks: `grep -rn "make_access_log\|Access Log\|access_log"`, which found nothing in app code; `@frappe.whitelist(methods=["GET"])` endpoints that download or export.

**Calibration items.** None of the ten known past defects sits in this audit-trail domain: the `**kwargs` transport fields, intake scope, handoff v1.4 names, reservation denominator, 7-day period, late-accepted need, catalogue digest, editor race, dropped doctype, Strategy universal read. I did not examine them. The closest analogue the method should rediscover is "an idempotent outbox event written in the same transaction". That is present and sound in NDS (`departmental_need_event.py:6-9`) and Tenders (`tenders/services/events.py:1-13`).

## 2. Coverage

### 2.1 Shared audit mechanisms found

| Mechanism | Used by | Append-only enforcement |
|---|---|---|
| Core `Audit Event` via `log_audit_event` (`kentender_core/services/audit_event_service.py:19`) | Strategy, core configuration and AUTH, workflow tasks, Supplier Accounts, Award, BOP, EVL (refusals), STD Templates, Opening register download | None: controller is `pass`; DocPerm cwd for System Manager and Administrator (Finding 1) |
| `Budget Audit Event` (Funding Ledger) | Budget | `on_trash` guard bypassable by flag; no write permission for any role; no `validate` guard |
| Module journals (`Planning`, `Requisition`, `Tender`, `Strategy` Command Journal) | Planning, REQ, Tenders, Strategy | Planning and REQ journals: none; DocPerm cw for System Manager |
| Decision doctypes with a controller guard (NDS Decision, Tender Decision/Event, Award Decision/Event, Proceeding Event, Bid Submission Event, Opening Access Incident, EVL Source Event, Supplier Account Access Decision) | NDS, TPR, AWD, PRC, BDS, BOP, EVL, Suppliers | Yes; see section 4 |
| Decision doctypes without a guard (Planning decisions, signatures, Treasury evidence, Late Activation, Requisition Decision/Event/Version, KTSM Status History) | Planning, REQ, KTSM | No (Finding 7) |
| Legacy TM2/BWMF audit events | `tender_management`, `tender_configurations` | TM2: `validate` plus `on_trash`; BWMF: `enforce_doctype_immutability`; not traced further |

Stores, Assets, Governance, Compliance, Integrations and Transparency contain only `hooks.py` (252 lines each, no services, doctypes or APIs). There is nothing to audit; I record them as not applicable.

### 2.2 Per-module command coverage (state-changing or material commands vs a persisted audit record)

"Audited" means the command writes an actor/time record in the same transaction (the exact record is named). Counts come from the AST scan plus hand reading of the misses.

| Module | Commands enumerated | With audit record | Without / defective | Notes |
|---|---|---|---|---|
| Strategy | 8 write endpoints (save draft, successor, structure save, discard, submit, return, approve, snapshot); approve also writes the supersede event | 8 of 8 write an `Audit Event` | 0 missing; 3 consumer reads, resolve-context denials and denial paths are not logged (Finding 8) | `strategy_writes.py` and `strategy_transitions.py` call `record_event` after the write in the same transaction |
| Budget | 16 (save approval details, save lines, successor, submit, return, approve, close, check, reserve, revalidate, release, convert, adjust commitment, decline request, receive request, withdraw request) | 16 of 16 call `safe_record_event` | all 16 are best-effort (Finding 3); positions, role and assignment absent (Finding 4); denial events never written (Finding 5) | Revalidate writes an event only when the status changes |
| NDS | 9 (create, update, submit, review, withdraw, create successor, cancel successor, request withdrawal, decide withdrawal) | 9 of 9 write `Departmental Need Decision` | 0 | Immutable; outbox events in the same transaction |
| Planning | 48 command functions | 47 of 48 journal or write a decision | `budget_revision.withdraw_budget_revision_request` journals nothing on the Planning side; Budget side logs it | Journal records no assignment or role (Finding 9) |
| Requisitions | 40 candidates (20 flagged by the heuristic, all delegating through `_journal` or `_return`, hand-verified) | All Draft writes journal via `_journal`; decisions via `record_decision` | journal lacks assignment, role, request id and old/new values | Authorise and revoke write both decision and event |
| Tenders | 36 | 29 direct plus 7 delegating (`confirm_*_channel`, evidence requirement add/update/remove, handoff consume/release, which are internal) | 0 uncovered | Events carry assignment snapshot except the four system events (clarification received, candidate notice, planning gateway, submission close) |
| Bid Submission | 16 | Every command goes through `records.idempotent` plus `records.emit` (event with assignment, command, key hash, UTC and EAT) | 0 uncovered (not every command traced to its `emit` call; `submit_bid` emits in a helper) | `Bid Command Journal` and `Bid Submission Event` guarded |
| Bid Opening | 30 | All route through `records.command` (journal) and Proceedings events | refusals audited at API layer | Sealed-content reads and export create no event (Finding 13) |
| Evaluation | 52 (12 flagged by the heuristic: delegating or internal) | Journal plus events; 40 direct | internal helpers not traced one by one | Doctypes guarded, no write permission |
| Award | 14 | 13 through `records.command`, plus `records.audit` for the shared log | `records.audit` swallows write failure (Finding 16) | Guarded doctypes |
| Supplier Accounts | 8 account commands | 8 of 8 call `audit.record` | evidence file view not logged (Finding 16) | |
| Core configuration and AUTH | 35 write functions (AST heuristic) | 29 call `log_audit_event`; URA grant and revoke rely on record fields; 3 OU commands have no event; 4 purge helpers | OU add/rename/deactivate (Finding 14) | |
| Legacy KTSM (suppliers) | 16 governance functions | 15 write history (all transitions with reasons) | `KTSM Status History` is mutable | |
| Tender Configurations (legacy) | review commands | decisions stored in a JSON blob on the document | Finding 15 | |

### 2.3 Append-only classification of the event, decision, journal and snapshot doctypes inspected (approximate counts)

- **Guarded, with no write permission for any role (immutable):** about 55 doctypes in BDS, BOP, PRC, EVL, AWD, NDS (Decision, Event, Review Task) and Installed STD Release.
- **Guarded by controller but System Manager keeps cwd permission:** Tender Event, Tender Decision, Tender Version, Tender Publication and the rest of the Tenders family. The guard requires `flags.kt_lifecycle`; a REST write by System Manager is refused.
- **Unguarded and mutable:**
  - Audit Event;
  - Planning Command Journal, Plan Governance Decision, Plan Finance Decision, Departmental Plan Validation Decision, Plan Preparation Signature, Treasury Submission Evidence, Late Activation Explanation, Approved Plan Snapshot;
  - Requisition Decision, Requisition Event, Requisition Version, Requisition Command Journal;
  - Strategy Command Journal;
  - KTSM Status History;
  - Funding Reservation, Procurement Commitment;
  - the Tender root and Tender Task.

## 3. Candidate findings (most severe first)

### F1. The shared `Audit Event` is mutable and deletable by System Manager and Administrator; Strategy's own segregation-of-duties check reads it

- **Severity:** High
- **Classification:** CODE DEFECT
- **Evidence:**
  - `kentender_core/kentender_core/kentender_core/doctype/audit_event/audit_event.json:84,92` and `:96,104`: `"delete": 1 … "role": "System Manager"`, `"write": 1`; the same block for `"Administrator"`.
  - `audit_event.py:4-5`: `class AuditEvent(Document): pass`.
  - `services/audit_event_service.py:1-5`: docstring "Append-only audit events", with `doc.insert(ignore_permissions=True)` at line 51.
  - `kentender_strategy/services/strategy_authorization.py:102-127`:
    ```python
    for event in list_events("Strategic Plan Version", version_name):
        if event.get("action") == "Submit for approval": return event.get("performed_by")
    ```
    `has_ever_been_submitted` (112) and `_blocked_by_self_approval` (121) make the segregation check and the "submitted-once, never discard" lock depend on those rows.
  - Seed code deletes and back-dates these rows with direct writes (`seeds/kentender_mvp_v1/reference_data.py:167` `frappe.db.set_value("Audit Event", name, "timestamp", …)`; `delete_doc("Audit Event", …)` in `procurement_settings.py:1229,1246,1268` and `regulatory_reference.py:1275`).
- **Rule:** STR §4.6 "append-only system event … users do not edit it" and STR §13; AUTH §15 "Administrative history on an assignment is append-only"; AWD §12 "Retain original and corrected values rather than editing history"; AGENTS.md §4.5 "silent mutation of approved baselines or missing audit evidence" is a stop condition. `Audit Event` is the audit store for Strategy, configuration, AUTH, Supplier Accounts, workflow tasks and the Award/BOP/EVL refusal events.
- **Reproduction:**
  1. Log in as a System Manager.
  2. `PUT /api/resource/Audit Event/<name>` with `{"performed_by": "<other user>"}` or `{"action": "x"}` succeeds; `DELETE /api/resource/Audit Event/<name>` succeeds.
  3. Delete the "Submit for approval" row of a submitted Strategic Plan Version. `strategy_authorization._blocked_by_self_approval` then no longer blocks the submitter from approving, and `discard_strategy_plan_draft` no longer refuses.
  4. Failing test sketch: `frappe.set_user(sm); with pytest.raises(frappe.PermissionError): frappe.delete_doc("Audit Event", name)`.
- **Note:** `Budget Audit Event` is better (no write permission for any role) but its `validate` does not refuse update; see Finding 7.

### F2. State-bearing records can be written directly through the standard document API, bypassing the command layer and its audit

- **Severity:** High
- **Classification:** CODE DEFECT
- **Evidence (DocPerm write for business roles; controller guards do not enforce the transition).** The guards that exist cover only identity fields, never the status.
  - Strategy: `strategic_plan_version.json:150-152` `"role": "Strategy Author" … "write": 1`; `status` has no `read_only` / `set_only_once`. `strategy_domain_guards.py:125-129` protects only `plan_id`, `version_number` and `based_on_plan_version_id` once the version is submitted; the only status check is `:134` `if doc.status == "Active" and prev_status != "Active": assert_no_primary_overlap(doc)` (overlap, not authority). `strategy_transitions.TRANSITIONS` (`:44`) is consulted only by the command function. Strategy's `hooks.py` registers no `has_permission`.
  - Budget: `procurement_budget_version.json` grants `Budget Officer` write (line 250-252) and `Budget Approver` write. The controller `procurement_budget_version.py:13-19` validates revision type and approval date only. `budget_read_scope.has_permission` (`:51-68`) only restricts readers. `Funding Reservation` and `Procurement Commitment` grant System Manager `cw` and have no guard (`funding_reservation.py` is `pass`), so reservation amounts and status change with no ledger event.
  - NDS: `departmental_need.json` grants `Departmental Author` write and `Head of User Department` write; `departmental_need.py:23-30` validates the state value is a legal state and guards only OU and FY (`_guard_immutable_scope`). `current_state`, `current_accepted_revision` and `Departmental Need Revision.revision_status` are not guarded (`REVISION_CONTENT_FIELDS` excludes the status, `constants.py:55-62`).
  - Planning: `annual_plan_version.json:222-225` `"role": "Procurement Planner" … "write": 1, "create": 1`; `annual_plan_version.py` is a 8-line shell. An approved `Annual Plan Version.version_status` is editable. `Departmental Plan Version` grants `Departmental Author` and `Head of User Department` write.
- **Rule:** AGENTS.md §4.3 "Never rely on hidden fields, disabled buttons … Enforce eligible source state, required role and scope, … audit actor, time, and reason"; AGENTS.md §4.5 "Never silently rewrite approved history"; STR §13 "Submitted for approval, Active and Superseded versions are immutable"; BUD §14 "Active, Superseded and Closed versions are immutable"; NDS §13 "Submitted content is immutable. Accepted content is immutable"; PLN §12 "Preserve immutable earlier versions, decisions and files". Frappe: `read_only` form flags are not enforced on server-side document saves; DocPerm write is sufficient for `PUT /api/resource/<doctype>/<name>`.
- **Reproduction (needs live confirmation, not run):**
  1. As a user holding only the Strategy Author responsibility (role projected by `_sync_projection`): `PUT /api/resource/Strategic Plan Version/<draft>` with `{"status":"Active"}`. The version is Active with no Approve decision, no segregation check and no Audit Event.
  2. As Budget Officer: `PUT /api/resource/Procurement Budget Version/<v>` with `{"status":"Active"}`, or edit an Active `Procurement Budget Line Version.approved_amount`.
  3. As Head of User Department: set `Departmental Need.current_state = "Accepted for planning"`.
  4. As Procurement Planner: edit an approved `Annual Plan Version`.
  5. Failing test sketch for each: `frappe.set_user(<role user>); doc = frappe.get_doc(DT, name); doc.status = "Active"; with pytest.raises(...): doc.save()`.
- **Note:** this finding is about audit completeness. Authority bypass is in scope for the permissions sweep, but the missing record is the audit-trail consequence.

### F3. Budget's funding-ledger writes are best-effort: a failed audit insert is swallowed and the financial mutation commits with no ledger event

- **Severity:** High
- **Classification:** CODE DEFECT
- **Evidence:**
  - `kentender_budget/services/budget_audit_contracts.py:176-182`:
    ```python
    def safe_record_event(**kwargs) -> str | None:
        """Best-effort record; never break the calling mutation on a logging failure."""
        try: return record_event(**kwargs)
        except Exception: frappe.log_error(title="Budget audit record_event failed"); return None
    ```
  - All 20 call sites use it (`budget_commitment_contracts.py:95,148,229,292`, `budget_check_reserve_contracts.py:279,419`, `budget_readiness_contracts.py:581,622,690,699,867`, `budget_contracts.py:1006,1055`, `budget_line_contracts.py:216`, `budget_revision_request_contracts.py:156,185,207,274,292`, `budget_idempotency.py:71`). `record_event` itself is never called directly outside `safe_record_event`.
  - `reserve_funding` (`budget_check_reserve_contracts.py:405-430`) inserts the Funding Reservation, then calls `safe_record_event`. If the event insert raises, the reservation row persists and no ledger event exists.
- **Rule:** BUD §14 "Funding Ledger events cannot be edited or deleted", "Append-only events: … reservation creation; revalidation, release, conversion and commitment adjustment"; BUD §4.7 "Append-only". AGENTS.md §4.3 "audit actor, time, and reason". Because the ledger is the sole record of reserved/committed positions, a missing event is a missing financial record, not a lost log line.
- **Reproduction:**
  1. Make the Budget Audit Event insert fail, for example with a `before_insert` hook that raises, or a DB constraint on `calling_module`.
  2. Call `reserve_funding` through a REQ `authorise_requisition`.
  3. The `Funding Reservation` row commits; no `Budget Audit Event` row exists.
  4. Failing test sketch: patch `record_event` to raise, call `reserve_funding`, assert the call raises or the reservation row does not exist.

### F4. Funding-ledger events lack the required before/after positions, business role, assignment ID and fiscal year

- **Severity:** Medium
- **Classification:** CODE DEFECT
- **Evidence:**
  - `budget_audit_event.json` fields are `budget, budget_version, budget_line, event_type, event_at, downstream_reference, reservation, commitment, amount, currency, actor, actor_kind, calling_module, correlation_id, revalidation_failure_code, reason, before_*/after_* (approved, reserved, committed, available), fixture_namespace, idempotency_key, payload_digest, command_result`. There is no business-role, assignment or fiscal-year field.
  - `grep -n "before=\|after=" kentender_budget/kentender_budget/services/*.py` returns no call site: `record_event` accepts `before`/`after` (`budget_audit_contracts.py:111-137`) but no caller passes them. Examples: `reserve_funding` (`budget_check_reserve_contracts.py:419-430`), `release_reservation` (`budget_commitment_contracts.py:148-159`), commitment and adjustment events.
- **Rule:** BUD §4.7 "before and after approved, reserved, committed and available positions; actor or calling service, timestamp and correlation ID"; BUD §14 "Each event records actor or calling service, business role, the exercised responsibility assignment ID, fiscal year, relevant IDs, action, timestamp, before and after status or line position, required decision reason, correlation ID and calling module".
- **Reproduction:** run `reserve_funding`, then read the `Budget Audit Event` row. `before_reserved`, `after_reserved` and the other position fields are NULL; no assignment or role is stored. Failing test sketch: assert `after_reserved - before_reserved == amount`.

### F5. Denial events required by STR §13 and BUD §14 are never written

- **Severity:** Medium
- **Classification:** CODE DEFECT
- **Evidence:**
  - Budget: `budget_audit_contracts.py:38-39` defines `EVENT_PERMISSION_DENIED = "Permission denied"` and `EVENT_CONCURRENCY_CONFLICT = "Concurrency conflict"`; the doctype's `event_type` options list both. No other reference in the app (`grep -rn "EVENT_PERMISSION_DENIED\|EVENT_CONCURRENCY_CONFLICT"` returns only the two definitions). Refusals return `{"ok": False, "code": "BUDGET_STALE_WRITE"…}` (`budget_readiness_contracts.py:540-545`) or `fail(...)` with no event.
  - Strategy: `strategy_authorization.py:132-146` `require_plan_version_capability` calls `fail("AUTH_SEGREGATION_BLOCKED")` / `fail(decision.reason_code …)` with no `record_event`; `grep "record_event" strategy_authorization.py` returns nothing.
  - Even where an event is written before raising (core `require_capability`, Finding 12), the transaction rolls back.
- **Rule:** STR §13 "Append-only events: … responsibility or segregation denial; successful and failed context resolution …"; BUD §14 "responsibility, segregation, floor and concurrency denial".
- **Reproduction:**
  1. As the Strategy submitter, call `approve_strategy_version` on your own submission: `AUTH_SEGREGATION_BLOCKED` is raised.
  2. `frappe.get_all("Audit Event", filters={"document_name": <version>})` shows no denial event. Failing test sketch: assert a `strategy.approve` denial event with `reason_code`, committed after the failed request.
  3. In Budget, call `approve_budget_version` as a user without the capability: no `Permission denied` ledger row.

### F6. The opening-register download audit and delivery record are written inside a GET request and rolled back

- **Severity:** Medium
- **Classification:** CODE DEFECT (needs live confirmation)
- **Evidence:**
  - `bid_opening/api.py:333-337`: `@frappe.whitelist(methods=["GET"]) def download_opening_register(...): _download(_call("GetOpeningRegisterCopy", …, register_copy.get_register_copy))`.
  - `register_copy.py:127-134`: `row.update({"status": "Delivered", "delivered_at": clock.now()}); records.save(row)` then `log_audit_event(event_type="Opening register downloaded", … action="download" …)`. Nothing commits.
  - Frappe `app.py:417-428` `sync_database`: `if frappe.local.request.method in UNSAFE_HTTP_METHODS or frappe.local.flags.commit: db.commit(…) else: db.rollback(…)`. `grep -rn "flags.commit"` finds no setter anywhere in `kentender_v1` or in Frappe, so a GET rolls back.
  - `_audit()` in the same API (`:42-52`) commits explicitly, but only for the refusal path.
- **Rule:** BOP register copy: the function's own docstring (`register_copy.py:121-123`) "the first download is recorded as the delivery, and every download is audited"; BOP §12 "register/copy request/fulfillment".
- **Reproduction:**
  1. A requester whose copy is Ready calls `GET /api/method/kentender_procurement.bid_opening.api.download_opening_register?tender_reference=…`.
  2. After the response, the request row is still `Ready`, `delivered_at` is empty and no `Opening register downloaded` Audit Event exists.
  3. Failing test sketch: issue the call through `frappe.handler` as GET and assert the audit row after the request commits or rolls back.
  4. Fix direction (not a style change): make the delivery a POST command, or commit explicitly under a documented exception.

### F7. System Manager retains create/write/delete on immutable evidence records that have no controller guard

- **Severity:** Medium
- **Classification:** CODE DEFECT
- **Evidence (DocPerm, then missing guard):**
  - Planning: `Plan Governance Decision`, `Plan Finance Decision`, `Departmental Plan Validation Decision`, `Plan Preparation Signature`, `Treasury Submission Evidence`, `Late Activation Explanation`, `Approved Plan Snapshot`, `Planning Command Journal`: System Manager and Administrator `cw` (`plan_governance_decision.json`, same pattern for the others). Controllers are 8-line shells (`plan_governance_decision.py:8`: `class PlanGovernanceDecision(Document): pass`). The doctype's own docstring says "shape only; every rule lives in services". Technical users pass the scope `has_permission` veto (`authorization.py:483` `if is_technical(principal): return True`), so nothing restricts a System Manager write.
  - Requisitions: `Requisition Decision` and `Requisition Version` grant System Manager `cwd` (`requisition_decision.json:137-138`); controllers `pass`. `Requisition Event`, `Requisition Command Journal` grant `cw`.
  - Tenders root: `Tender` grants System Manager `cwd` and the controller is `pass`; `Tender Task` the same. `overall_status` and delete are unguarded, unlike `Tender Version`, `Tender Event` and `Tender Decision`, which have guards.
  - Budget and Strategy: `Funding Reservation` and `Procurement Commitment` (System Manager `cw`, no guard); `Strategy Command Journal` (System Manager `cwd`).
  - AUTH: `User Responsibility Assignment` grants System Manager `delete: 1` (`user_responsibility_assignment.json`, System Manager block) and its controller has no `on_trash` (`user_responsibility_assignment.py` defines `validate`, `_validate_immutable_once_in_force`, `is_effective` only; `status` is not in `IDENTITY_FIELDS` at `:41-49`, so a Revoked assignment can be set back to Enabled).
  - `KTSM Status History`: System Manager `write: 1`, no immutability guard (`ktsm_status_history.py:10-14` only sets defaults).
  - Guarded siblings for contrast: `Departmental Need Decision` (`validate` refuses update, `on_trash` refuses delete), `Tender Event`/`Tender Decision`, `Award Decision(Event)`.
- **Rule:** PLN §12 "Preserve immutable earlier versions, decisions and files. Reversal is a linked record, never erasure."; REQ §15 "Submitted, returned, authorised, withdrawn, revoked, superseded and stopped Version content cannot be edited or deleted"; TPR §12.3 "Submitted, approved, publication-authorised, published, issued-addendum and cancelled facts are append-only"; AUTH §15 "Assignment records are never physically deleted"; AUTH §371 / KT-STD §3A.6: technical access is read access, not a business write.
- **Reproduction:**
  1. As System Manager, `PUT /api/resource/Plan Governance Decision/<n>` `{"decision":"Returned"}`; or `DELETE /api/resource/Requisition Decision/<n>`; or `DELETE /api/resource/User Responsibility Assignment/<n>` for an Active assignment.
  2. Each succeeds (Version is recorded where `track_changes=1`; Frappe Version rows are themselves deletable by System Manager).
  3. Failing test sketch: `frappe.set_user(sm); with pytest.raises(frappe.ValidationError): frappe.delete_doc("Requisition Decision", n)`.

### F8. Strategy's §13 event list is incomplete and two events omit required attribution

- **Severity:** Medium
- **Classification:** CODE DEFECT
- **Evidence:**
  - `strategy_consumer.py:76-130` `resolve_strategy_context`, `:176` `list_strategy_objectives` and `:225` `get_strategy_lineage` contain no audit call; the only consumer audit is `create_strategy_snapshot` at `:327`.
  - Snapshot event `:327-334`: `record_event(entity_type="Strategy Node", … event_type="Strategy Snapshot Created", …)` passes no calling module, business role or assignment, and `create_strategy_snapshot(plan_version_id, objective_id, correlation_key)` (`:275`) has no caller identity parameter.
  - Supersede event `strategy_transitions.py:136-144`: `record_event(… event_type="Approve successor", prior_state="Active", new_state="Superseded", …)` omits `business_role`, `assignment`, `capability` and `correlation_id`, while the Approve event at `:200-212` carries them.
- **Rule:** STR §13 "Strategic Objective listing and lineage reads by a downstream module; successful and failed context resolution … A downstream contract event also records the calling module … Each event records actor, business role, the exercised responsibility assignment ID …".
- **Reproduction:** call `resolve_strategy_context` (success and `STRATEGY_CONTEXT_NOT_FOUND`), `list_strategy_objectives`, `get_strategy_lineage`; query `Audit Event` filtered by the action: zero rows. Approve a successor and read the "Approve successor" event metadata: no `business_role` or `assignment`.

### F9. Planning and Requisition command journals do not record the exercised authority, business role or request id for non-decision commands

- **Severity:** Medium
- **Classification:** CODE DEFECT against PLN §12 and REQ §15
- **Evidence:**
  - `Planning Command Journal` fields: `idempotency_key, command, document_type, document_name, request_fingerprint, actor, result, occurred_at, fixture_namespace` (`planning_command_journal.json`). `envelope.record_command` (`procurement_planning/services/envelope.py:63-86`) writes exactly these.
  - `Requisition Command Journal`: the same fields (`requisition_command_journal.json`; `procurement_requisitions/services/envelope.py:63-86`).
  - `fingerprint()` stores a SHA-256 of the payload (`envelope.py:29-35`), so decision-less commands (for example `withdraw_departmental_submission` `dpp_lifecycle.py:675-711`, `hold_plan_publication` `publication_pipeline.py:325-368`, all REQ Draft writes) retain actor, time, command and result, but not assignment, role, request id or old/new values (REQ §15).
  - Contrast: NDS stores `effective_assignment`, `request_id`, `source_ip`, `before_state_hash` and `after_state_hash` (`departmental_need_decision.json`; `lifecycle.py:205-241`); Planning and REQ decision doctypes carry `authority_snapshot`.
- **Rule:** PLN §12 "Every command records its exact input/output identities, expected/resulting token, actor or authenticated producer, exercised authority, prior/resulting states, idempotency correlation …"; REQ §15 "Audit records contain actor, business role, the exercised responsibility assignment ID, server time, request ID and idempotency key" and "old and new values for each Draft change".
- **Reproduction:** run `save_requisition_summary` or `withdraw_departmental_submission`; read the journal row; the assignment and old/new values are absent. The old/new values exist only in Frappe `Version` (REQ `track_changes=1`; Planning `Departmental Plan Version` `track_changes=1`), which is not an audit contract and is deletable.

### F10. NDS, Strategy and Budget decisions do not store the authority snapshot AUTH §15 requires

- **Severity:** Medium
- **Classification:** CODE DEFECT (NDS) / SPEC GAP (Strategy and Budget, whose own docs only demand the ID)
- **Evidence:**
  - NDS: `departmental_need_decision.json` has `effective_assignment` (a bare ID) and no snapshot field; `lifecycle.py:220` `"effective_assignment": cstr(assignment)`. NDS §4.5 and §13 require "exact User Responsibility Assignment ID and snapshot".
  - `authorization.assignment_snapshot()` (`authorization.py:517-530`) exists but has no caller (`grep -rn "assignment_snapshot(" kentender_*` returns only its definition; Tenders/REQ/Planning use `authz.authority_snapshot`, a different function).
  - Strategy stores the ID in event metadata (`strategy_audit.py:56-61`); Budget stores nothing (F4).
- **Rule:** AUTH §15 "Every protected decision retains: assignment ID; user; business role; Organisation Unit scope; appointment type and authority reference where applicable; effective period evaluated …"; "Later changes to an assignment never rewrite historical decision evidence". NDS §13.
- **Reproduction:** accept a Need, read the decision: the `effective_assignment` string only. If the assignment later changes (revoked with its reason, or an in-force row edited by System Manager under F7), the decision no longer shows the period or scope it was exercised under.

### F11. `Need Planning Intake Projection` grants every role, including Auditor, create/write/delete

- **Severity:** Medium
- **Classification:** CODE DEFECT
- **Evidence:** `need_planning_intake_projection.json` DocPerm rows for `System Manager`, `Administrator`, `Departmental Author`, `Head of User Department`, `Procurement Planner` and `Auditor`, each with create 1, delete 1, write 1 (read from lines 288-289 and surrounding rows). The controller docstring (`need_planning_intake_projection.py:1-13`) says "a read-only projection supplied by Planning … users cannot edit it. It is written only by `project_need_planning_intake`".
- **Rule:** NDS §13 "Projection updates never change Need content, state, accepted pointer, quantity or review decision history"; NDS §4.7 "read-only projection".
- **Reproduction:** as Auditor, `PUT /api/resource/Need Planning Intake Projection/<n>` changes `position`; `DELETE` removes it. Failing test sketch: assert a non-service write raises.

### F12. Core `require_capability` writes an `authorization.denied` event and then throws, so the denial is rolled back

- **Severity:** Medium
- **Classification:** CODE DEFECT
- **Evidence:**
  - `kentender_core/services/authorization_policy.py:188-215`: `log_audit_event(event_type="authorization.denied", … performed_by=…, metadata={"reason_code": decision.reason_code, …})` followed by `frappe.throw(…, frappe.PermissionError, …)`; no commit.
  - Frappe `app.py:138-141`: `except Exception as e: response = … handle_exception(e); if db := …: db.rollback(chain=True)`. So in a POST request the denial row is rolled back with everything else. Callers: `workflow_tasks.py:139,154,177,198` (get task, claim, reassign, transition).
- **Rule:** AUTH §15 "Every protected decision retains … segregation result"; the function's own intent (a denial audit).
- **Reproduction:** as a user without the capability, `POST` claim or transition a workflow task, then query `Audit Event` where `event_type = 'authorization.denied'`: none persist. Failing test sketch: call through the request handler (not a direct Python call, which does not roll back) and assert the row exists after the call.
- **Note:** the BOP, Award and EVL APIs avoid this by catching the exception, auditing and committing (`bid_opening/api.py:42-52`); the core service does not.

### F13. Reads of sealed or confidential content, and opening exports, create no audit event; the docs lean on "existing security/access logging" that the code does not implement

- **Severity:** Medium
- **Classification:** SPEC GAP (the sweep brief requires access logging; BOP §12 lists no read events and OVS defers to "existing security/access logging")
- **Evidence:**
  - `bid_opening/services/pages.py:1-13` docstring "Reading records no event."; `bid_pages` (`:28-38`) returns the rendered bid pages with no log.
  - `bid_opening/services/export.py:41-58` `export_opening` returns the whole opening bundle (entries, register, handoff, proceedings) with no audit event.
  - `grep -rn "make_access_log\|Access Log\|access_log" kentender_*` returns nothing outside Frappe.
  - Supplier evidence view: `supplier_accounts/services/evidence.py:78-90` `get_account_evidence_file` returns the stored file with no event. Upload is audited (`:72`).
  - OVS v0.6 line 154: "Existing security/access logging continues; viewing creates no business approval"; BOP §12 lists attendance, register request, minutes and handoff but no page reads.
- **Rule:** OVS v0.6 line 102/154 (sealed content stays excluded; access logging "continues"); TRUST-ADR-001 §5 audit exports. The sweep brief names "access to sealed or confidential bid content" and "export". The docs do not say what an access record contains.
- **Reproduction:** open bid pages after reveal as a committee member and read `Audit Event` for the tender: no row. Decision needed: define whether Frappe `Access Log` or a module event is the record, and whether it is the business audit trail.

### F14. Configuration changes with no event: Award Settings and Organisation Unit commands

- **Severity:** Low (OU) / Medium (Award Settings)
- **Classification:** SPEC GAP (Award Settings), CODE DEFECT (OU against AUTH line 371)
- **Evidence:**
  - Award Settings holds the legal profile: `profile_id, profile_version, verified, simulation_only, reviewer, reviewed_on, reply_days, minimum_wait_days, earliest_time, giving_rule, audience_rule, debrief_rule, …` (`award_settings.json`). DocPerm: System Manager `cw`; controller is `pass`; `award/services/profile.py` only reads it and has `install_test_profile`. A System Manager edit, including setting `verified`, produces only a Frappe Version row (`track_changes=1`) with no reason, no Audit Event. AWD §12 expects statutory evidence retained.
  - OU: `organisation_structure.py:261,308,328` `add_organisation_unit`, `rename_organisation_unit`, `set_organisation_unit_active` call no `log_audit_event` (the AST scan lists them as writes with `audit=False`); `Organisation Unit` has `track_changes=1` (Version only). AUTH-ADR-001 line 371: "These writes … are validated and audited."; §9.2 commands. Responsibility grant and revoke keep their actor, time and reason on the record (`assigned_by`, `assigned_at`, `revoked_by`, `revoked_at`, `revocation_reason`, `responsibility_administration.py:154-160,197-203`), which meets the actor/time/reason rule; they write no Audit Event but are not a gap against §9.2's "write audit" because the record fields are the audit.
- **Reproduction:** rename an OU; `Audit Event` has no row; `Version` has one (deletable). Edit Award Settings as System Manager; same.

### F15. Legacy Tender Configuration keeps its review decisions in a mutable JSON blob and mutates status inside a read endpoint

- **Severity:** Low
- **Classification:** SPEC GAP (no approved doc in the oracle governs this legacy module; it remains in `modules.txt`)
- **Evidence:** `tender_configurations/services/review_workspace.py:462-487` appends the "approve_for_preview" decision to `blob["decisions"]` on the document's own JSON field and sets the status; `:405-424` the return decision is the same. `get_review_workspace` (`:374-399`) is a read function that does `frappe.db.set_value("Tender Configuration", …, update_modified=False)` and `frappe.db.commit()`. There are 26 explicit commits in `tender_configurations/services` (for example `:257,398,434,484,554,604`).
- **Rule:** AGENTS.md §4.4 "Do not call `frappe.db.commit()` from ordinary request services … Do not use direct database writes to bypass validation or manufacture workflow state."
- **Reproduction:** open the review workspace for a configuration in "Ready for Review" as a reviewer: the status changes to "Under review" with no event and the `modified` timestamp is unchanged.

### F16. Smaller defects

- **Severity:** Low
- **Classification:** CODE DEFECT unless stated.
  1. **`records.audit` swallows write failure in Award:** `award/services/records.py:160-169`: `except Exception: frappe.log_error(title="Award audit write failed")`. The Award records themselves carry the primary evidence, so the effect is limited to the shared log.
  2. **`check_funding` writes a ledger event though BUD §14 says check calls create none:** `budget_check_reserve_contracts.py:277-285` writes `EVENT_CHECK_PERFORMED`. BUD §14: "Read/check calls do not create business or funding-ledger events." The event is in neither the lifecycle nor the funding partition (`budget_audit_contracts.py:57-76`), so it pollutes the stream. Classification: CODE DEFECT against the doc, or SPEC DEFECT if the event is wanted.
  3. **`Budget Audit Event.on_trash` is bypassable by a flag:** `budget_audit_event.py:12-18` returns early when `frappe.flags.allow_budget_audit_purge` is set or during migrate/install, and there is no `validate` refusing update.
  4. **`TM2 Tender Audit Event.on_trash` returns early under `frappe.in_test`** (`tm2_tender_audit_event.py:68-74`); this is test-only in production but a guard that depends on a test flag.
  5. **Refusal commit in BOP/Award/EVL API wrappers:** `_audit()` calls `frappe.db.commit()` after a caught refusal (`bid_opening/api.py:42-52`; `award/api.py:25-35`; `bid_evaluation/api.py:43-52`). Where the command ran inside `atomic()` (`records.command`) the failed body has already rolled back to its savepoint, so the commit is safe. A refusal raised outside `records.command` (a read or a guard before the command) commits whatever the request had already written; I did not find a case, so this is unproven.
  6. **`Strategy Command Journal` and `Planning/Requisition Command Journal` are idempotency stores that double as audit evidence but are mutable** (covered by F7).

## 4. Checked and clean

- **Audit write in the same transaction, no commit gap, for the main modules.**
  - NDS: `_record_decision` and `publish_*` inside the command (`departmental_needs/services/lifecycle.py:190-241,789-815`).
  - Strategy: `record_event` after the write, in one request.
  - Tenders: `events.emit` inside `envelope.atomic` (`tenders/services/events.py:1-13`, `submission_close.py:79-91`).
  - BOP, Award, EVL, BDS: `records.command` / `atomic()` savepoints (`bid_opening/services/records.py:75-84,134-197`; `award/services/records.py:142-150`).
  - REQ authorise and revoke: `envelope.atomic("authorise")` writes decision, handoff and event together (`authorise.py:112-160`).
  - `log_audit_event` itself does not commit (`audit_event_service.py:32-34`).
- **Explicit commits are documented and per design:** `bid_submission/services/submission.py:140` ("the attempt is durable before the deposit leaves"), and the scheduler per-record commits in `tenders/services/submission_close.py:99-104`, `bid_submission/services/close.py:233-247`, `candidate_notices.py:159`, `award/services/sweep.py:20,27`. No Planning, NDS, REQ or Strategy service commits.
- **Append-only doctypes, controller guard plus no write permission:**
  - NDS: `Departmental Need Decision` (`validate` refuses non-new at `:25-27`, `on_trash` refuses at `:42-43`); `Departmental Need Event` (immutable field set, `on_trash` refuses).
  - Tenders: `Tender Event`, `Tender Decision`, `Tender Version` (non-new requires `flags.kt_lifecycle`; delete requires `kt_fixture_wipe`).
  - BDS, BOP, PRC, EVL, AWD, Supplier Accounts: `Bid Submission Event`, `Proceeding Event`, `Opening Access Incident`, `Evaluation Source Event`, `Award Decision`, `Award Decision Event`, `Supplier Account Access Decision` and their families (about 55 doctypes, DocPerm lists empty).
  - `Installed STD Release` (immutable fields, never deleted).
  - `Reference Verification Event` (append-only validate and `on_trash`).
  - The guards use a service flag; a REST write by a user is refused. I did not look for code that sets those flags outside the module commands.
- **Decision records carry actor, time, reason and authority where the docs require them.**
  - NDS: reason required for return/decline/withdraw (`departmental_need_decision.py:34-41`), correlation id, content hash and before/after hashes.
  - REQ: `Requisition Decision` (`authority_snapshot`, `legal_capacity`, `reason`).
  - Planning: decision doctypes with `authority_snapshot`.
  - Tenders: events carry `assignment_snapshot`, UTC and EAT times, previous and resulting status, reason, digest.
  - Budget: reason on return (`budget_readiness_contracts.py:620-634`) and decline.
  - Strategy: Return reason length enforced (`strategy_transitions.py:176-184`).
  - Supplier Accounts: suspend and restore with a 10-500 character reason, decision row and event (`supplier_accounts/services/access.py:30-62`).
  - Core: revoke reason 10-500 characters (`responsibility_administration.py:176-203`).
  - KTSM: every governance transition has a reason where required and writes history.
- **Instants are site time.** `now_datetime()` in `audit_event_service.py:36`, Budget `event_at`, Planning journal `occurred_at`; UTC appears only in serialized event payloads (`tenders/services/events.py:62-64`, `bid_submission/services/records.py:157`, `supplier_accounts/services/audit.py:60-65`). The shared test clock answers only when `kt_bds_simulation_environment` is set in site config (`bid_submission/services/simulation.py:1-23`), so production reads the site clock.
- **Config audit coverage is broad.** Procurement settings, regulatory reference, site configuration (PE, fiscal year, intake windows) and public portal settings call `log_audit_event` in every write function (29 of 35); the 4 without are purge helpers and the OU commands in F14. Purge helpers are called only from fixtures (`seeds/playwright_ui_fixtures.py:83-84` and the module Playwright seeds); none is whitelisted.
- **Workflow task audit.** claim, release, reassign (with reason), transition and invalidate each write an event (`workflow_tasks.py:148-218`).
- **Idempotent replay does not duplicate effects.** Strategy `run_idempotent`, Budget `run_idempotent` (replay returns the first result), Planning and REQ `replay_or_none`, BOP and Award `command` return the journalled result.
- **Opening-register request and copy fulfilment** are journalled commands; only the download itself is defective (F6).
- **Strategy `discard_strategy_plan_draft`** records the discard event before deleting, and refuses once the audit trail shows a submission (`strategy_writes.py:246-310`).
- **No dead-ends found for refusal logging where the docs are silent.** TPR §12.1 says "Rejected commands … never create a business event"; NDS, PLN and REQ list no denial events; the code writes none. Strategy and Budget require denial events and fail them (F5).
