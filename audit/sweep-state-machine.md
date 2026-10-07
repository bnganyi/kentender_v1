# Sweep: state-machine-immutability (Phase 2, read-only static audit)

Scope: every business doctype with a status / workflow_state / lifecycle field in `kentender_*` apps (Strategy, Budget, Departmental Needs, Planning, Requisitions, Tenders, Bid Submission/Opening, Evaluation, Award; Contract Management has no doctypes at all). (1) allowed transitions and the single service that performs each, bypasses of that service, preconditions, idempotency; (2) immutability of approved / submitted / published / frozen records against edits and deletion through every write path.

## Method (reproducible)

Static reading only. No bench/db/site contact. Commands used:

```
# doctypes carrying a state-ish field (python over */doctype/*/*.json): fieldname contains status|state|lifecycle, excluding istable  -> 186 doctypes
# DocPerm write/create/delete matrix per doctype (python over the same JSON), split into technical (System Manager, Administrator) vs business/"All" roles
# controller guard presence: for each doctype .py -> validate / on_trash / before_save / on_update / flags.kt_*  (bare "pass" controllers listed)
grep -rn --include=*.py -E "db\.set_value\(|\.db_set\(|UPDATE `tab|ignore_validate|db_update\(\)" kentender_*   # direct-write bypasses
grep -rn --include=*.py -E "flags\.(kt_lifecycle|kt_awd_command|kt_evl_command|kt_bop_command|kt_prc_command|ignore_validate)" kentender_*
python3 scan_wl.py   # AST scan of ALL 668 @frappe.whitelist functions and whitelist() aliases for parameters named user|actor|performed_by|principal|... and **kwargs forwarding
grep -n "doc_events|has_permission|permission_query_conditions|before_request|override_whitelisted" kentender_*/kentender_*/hooks.py
read frappe/__init__.py get_newargs + frappe/client.py set_value + frappe/handler.py (framework facts: read_only is NOT enforced server-side; whitelisted args are filtered only by signature)
```

Framework facts relied on (verified in `/home/midasuser/frappe-bench/apps/frappe/frappe`):
- `client.py:167-198` `set_value` and `/api/resource` PUT run `doc.update(values); doc.save()`: permission check = DocPerm role (+ the app's `has_permission` hook) and the controller's `validate`. `read_only: 1` on a field is a UI attribute only; `document.py` has no server-side read_only enforcement (only `set_only_once` and permlevel are server-enforced).
- `__init__.py:1150-1172` `get_newargs`: request parameters are passed to a whitelisted function if their name is in its signature (all of them if it has `**kwargs`). Only `ignore_permissions` and `flags` are stripped. A `user` parameter is therefore attacker-controlled.
- `kentender_core/services/authorization.py:461-501` / `planning_authorization.py:484-494` / `budget_read_scope.py:57-68` / `requisition_authorization.py:351-377`: every `has_permission` hook in the repo only restricts READ scope (organisation unit) and returns True for every other ptype, so it never blocks a `write`.
- No `doc_events` for any business doctype (procurement hooks.py:457-469 registers only `File.on_trash` and `Departmental Need Event.after_insert`; core registers authorization-record validators only).

Docs read (latest approved): STR v1_9 (§6.1, STR-BR-004/005/006/015, STR-AC-010, line 636), BUD v1_12 (BUD-BR-005/021/022/025/028, BUD18-AC-062, line 329/1175), NDS v1_16 (§4.3, §4.11, §5.1-5.4, §7.5, NDS-BR-006/010/016/017/018), PLN v1_29 (§4.5 field table, §5.1.5, §5.2.3), REQ v1_14 (§7.1, §7.5 inv. 11-13), TPR v0_17 (§5.1, §5.8, §12.3), AUTH-ADR-001 v1_11 (§8 technical roles hold no business action, lines 182/361/831), KT-STD-001 v1_25 §11, AGENTS.md §4.3-4.5. BDS/BOP/EVL/AWD docs consulted only for their command/guard model through the code docstrings (see "sampled").

## Coverage

| Bucket | Enumerated | Classification |
|---|---|---|
| Doctypes with a state field | 186 | all classified by DocPerm write set x controller guard (below) |
| Business-role-writable doctypes (non-technical role holds create/write) | 53 | 44 unguarded or guard-bypassable by status/field (findings F2-F5, F8, F10); 9 TM2/legacy handled in F6/F7 and "Checked" |
| Doctypes writable by technical roles only (System Manager / Administrator) | ~95 incl. Requisition family, Tender root, Tender Task, Approved Plan Snapshot, Audit Event | guard absent on Requisition*, Tender, Tender Task, Authorised Requisition Handoff, Approved Plan Snapshot, Funding Reservation, Procurement Commitment, Audit Event (F11) |
| Doctypes with NO write DocPerm for anyone and a command-flag controller guard | Award (16), Bid Evaluation (22), Bid Opening (13), Bid Submission (21), Proceedings (8), Tender family except Tender/Tender Task (13) | clean at the REST/desk layer ("Checked and clean" C1-C3) |
| Whitelisted functions scanned for caller-supplied identity | 668 | 1 module exposes `user`/`actor` to the caller on 20+ endpoints (NDS, F1); TM2 publication API (7 endpoints, F6); core responsibility API `user` is a target user, not the actor (clean) |
| Direct DB writes outside the owning service (`db.set_value`, `db_set`, raw UPDATE) | procurement_planning 40+ calls, NDS 6, requisitions 3, budget 4, strategy 1, core/suppliers other | all inside the owning module's own service (see C7); no cross-app direct write of another app's status found |
| `flags.ignore_validate` outside seeds/tests | 0 in business modules (only seeds and `File` CAS) | clean |
| Contract (Contract Management) | module folder has no doctypes, api or services | not implemented; nothing to audit |

### Transition inventory and the single owning service

| Doc | Transitions (doc rule) | Owning service (file) |
|---|---|---|
| Strategic Plan Version | Draft -> Submitted for approval (Author); Submitted -> Draft (Return, Approver); Submitted -> Active (Approve, supersedes prior Active) (STR §6.1, STR-BR-015) | `kentender_strategy/services/strategy_transitions.py:41-45 TRANSITIONS`, `transition_plan_version:150` |
| Procurement Budget Version | Draft -> Submitted -> Draft/Active -> Superseded/Closed (BUD §6, BUD-BR-005/021/022) | `kentender_budget/services/budget_readiness_contracts.py` `_submit_budget_version:558`, `_return_budget_version:598`, `_approve_budget_version:643`, `_close_budget:824` |
| Departmental Need / Revision | Draft -> Submitted -> Accepted/Returned/Not taken forward; Accepted -> successor / withdrawal (NDS §5.1-5.3) | `departmental_needs/services/lifecycle.py` (`submit_need:643`, `review_need:703`, `withdraw_need:824`, `request_withdrawal:1000`, `decide_withdrawal:1069`) |
| Departmental Plan Version | Draft -> Submitted -> Accepted/Returned/Withdrawn (PLN §5.1.5) | `procurement_planning/services/dpp_lifecycle.py`, `dpp_validation.py` |
| Annual Plan Version | Draft -> Awaiting AO -> Awaiting statutory -> Approved-pending -> Active; returns/withdrawals (PLN §5.2.3) | `procurement_planning/services/plan_governance.py:368,464,517,624`, `plan_publication.py`, `publication_pipeline.py` |
| Requisition / Version | Draft -> Awaiting Dept -> Submitted to Procurement -> Authorised / Revoked / Withdrawn (REQ §7.1) | `procurement_requisitions/services/lifecycle.py`, `authorise.py:81-163` (revoke `:165`) |
| Tender / Tender Version | Draft -> Submitted -> Approved -> Publication authorised -> Published -> Cancelled/closed (TPR §5.1) | `tenders/services/lifecycle.py`, `publication.py`, `cancellation.py`; single writer `envelope.bump` (`tenders/services/envelope.py:103-115`) |
| Bid Opening / Evaluation / Award / BDS / Proceedings | per their command contracts | `*/services/records.py` command envelopes (flags `kt_bop_command`, `kt_evl_command`, `kt_awd_command`, `kt_prc_command`, `kt_bds_command` context) |

## Candidate findings

Sorted most severe first. Severity: Critical / High / Medium / Low. Classification: CODE DEFECT / SPEC DEFECT / SPEC GAP.

### F1. Critical - Departmental Needs API trusts a caller-supplied `user`: any logged-in user can act as any other user (Head of Department accept, maker-checker defeated). CODE DEFECT

Evidence:
- `departmental_needs/api.py:78-90` `save_need_draft(**kwargs)`, `:113-127` `return_need_revision/accept_need_revision/decline_need_revision(**kwargs)` forward every request field except `cmd/csrf_token/_` (`api.py:73-74 _command_args`) into the service.
- `api.py:92-103` `submit_need_revision = frappe.whitelist()(lifecycle.submit_need)` (and withdraw, successor create/cancel, request/decide withdrawal, `project_need_planning_*`) expose services whose signature contains `user: str | None = None` (`lifecycle.py:643-646`, `:703-713`).
- Read endpoints `api.py:45-51` (`get_departmental_need`, `get_departmental_review_task`, `resolve_needs_scope`, `list_needs_financial_years`) also take `user` (`workspace.py:643`, `:373`, `context.py:140,216`).
- `departmental_needs/services/permissions.py:59-66`:
  ```python
  def actor(user: str | None = None) -> str:
      value = cstr(user or frappe.session.user).strip()
  ```
  and every command uses `principal = actor(user)` (e.g. `lifecycle.py:725`, then `require_review_command(doc, principal)` `:729` and `if is_owner(doc, principal): fail("NDS_MAKER_CHECKER")` `:732`). Nothing compares `user` to the session.
- Framework: `frappe/__init__.py:1150-1172` passes any request parameter whose name is in the signature.
- Contrast (correct pattern): `award/api.py:38` `fn(user=frappe.session.user, **kwargs)`, `bid_opening/api.py:55`. Tenders, Requisitions, Planning, Budget, Strategy APIs expose no `user` parameter (scan of 668 whitelisted callables).
- The reviewer's task id and token are handed to the caller by `get_departmental_need` as soon as it believes the viewer is a department decider (`workspace.py:118-137`, `_open_review_task` `:63-74`).

Rule: NDS-BR-006 and NDS-AC-010 (maker never decides own version, "rechecked on the server"); NDS-BR-018 (every write checks decision token under one transaction as the authenticated actor); AGENTS.md §4.3 ("Never rely on ... client checks for authorization ... re-check permissions inside whitelisted methods"); AUTH-ADR-001 §15 audit identity (the recorded decision actor/assignment is the forged principal).

Reproduction (Departmental Author A, no HoD role; N is A's own submitted Need, H the HoD's email):
1. `GET /api/method/kentender_procurement.departmental_needs.api.get_departmental_need?need=N&user=H` -> response contains the open review action `{"code":"review","task":"NDT-<uuid>","decision_token":"<token>"}` (expected: A's own session view, no decision controls; actual: HoD's view).
2. `POST /api/method/kentender_procurement.departmental_needs.api.accept_need_revision` body `need=N&task=NDT-<uuid>&decision_token=<token>&expected_version=<record_version>&idempotency_key=k1&user=H` (expected: NDS_MAKER_CHECKER / NDS_SCOPE_DENIED; actual: Need becomes "Accepted for planning", decision row records H as actor with H's assignment, outbox event published to Planning).
3. Same with `decline_need_revision` / `return_need_revision`, and `decide_accepted_need_withdrawal` to approve withdrawal as the reviewer.
Also `save_need_draft` with `user=<other author>` creates/edits needs as another user; `project_need_planning_usage/disposition/intake` with `user=<planner>` lets any user falsify Planning projections (see F9).

Test sketch: with two session users, call each NDS endpoint with `user=<other>`; assert the effective actor in the Decision row equals the session user (or the call is refused).

### F2. High - Direct REST write on Departmental Need / Revision / Review Task / Withdrawal Request bypasses every lifecycle rule. CODE DEFECT

Evidence:
- DocPerm: `departmental_need.json:120-128` Departmental Author create+write, Head of User Department write; same for `departmental_need_revision.json:150-160`, `need_withdrawal_request.json`; `departmental_need_review_task.json` Head of User Department write. `read_only: 1` on `current_state`, `current_accepted_revision`, `revision_status`, review task `status`/`decision_token` is not enforced server-side (framework fact above). `has_permission` hook (`authorization.py:461-501`) restricts only the OU read scope.
- `departmental_need.py:23-26`: `validate` only checks `current_state in NEED_STATES` and OU/FY immutability (`:28-37`); no transition table, no pointer guard.
- `departmental_need_revision.py:37-47`:
  ```python
  if self.is_new() or self.revision_status in MUTABLE_REVISION_STATUSES: return
  before = self.get_doc_before_save()
  changed = [f for f in REVISION_CONTENT_FIELDS if self.get(f) != before.get(f)]
  ```
  It tests the NEW `revision_status`, so a single save that flips an Accepted/Submitted revision to `Draft` and edits content is exempt; the status itself is not in `REVISION_CONTENT_FIELDS` (`constants.py:60-67`).
Rule: NDS-BR-017 (statuses never client-editable), NDS §4.3 ("Submitted content is immutable"), NDS-BR-006, NDS-BR-010 (submit creates immutable hash + task atomically), NDS-BR-015.

Reproduction (Departmental Author in scope):
1. `PUT /api/resource/Departmental Need Revision/<accepted revision>` `{"revision_status":"Draft","title":"Changed after acceptance","indicative_quantity":9999}` -> expected 417 NDS_STATE_CONFLICT; actual 200, accepted content rewritten (Planning consumes it as the accepted revision).
2. `PUT /api/resource/Departmental Need/<n>` `{"current_state":"Accepted for planning","current_accepted_revision":"<own draft revision>","current_revision":"<same>"}` and `PUT .../Departmental Need Revision/<draft>` `{"revision_status":"Accepted"}` -> accepted without HoD, no Decision row, no event; DPP/Plan intake treats it as accepted.
3. `POST /api/resource/Departmental Need` with `current_state:"Accepted for planning"` creates a pre-accepted Need (validate only checks the enum).
4. HoD (`write` on Review Task): `PUT /api/resource/Departmental Need Review Task/<t>` `{"status":"Completed"}` closes a task with no decision.
Test sketch: `frappe.set_user(author); doc=frappe.get_doc("Departmental Need Revision", accepted); doc.revision_status="Draft"; doc.title="x"; doc.save()` must raise; today it succeeds.

### F3. High - Annual Plan / Departmental Plan families are writable by Procurement Planner / Departmental Author / Head of User Department with no controller guard: statutory approval chain and frozen snapshot bypass. CODE DEFECT

Evidence:
- DocPerm create+write for Procurement Planner on `Annual Plan` (`annual_plan.json:104-109`), `Annual Plan Version` (`annual_plan_version.json:222-226`), `Annual Plan Item` (`annual_plan_item.json:427`), `Plan Source Allocation` (`plan_source_allocation.json:217`); Departmental Author create+write and Head of User Department write on `Departmental Plan`, `Departmental Plan Version` (`departmental_plan_version.json:120-130`), `Departmental Plan Entry` (`departmental_plan_entry.json:174-184`).
- Controllers: `annual_plan.py`, `annual_plan_version.py:8` and `departmental_plan*.py` are `pass` (8 lines). `annual_plan_item.py` and `departmental_plan_entry.py` validate only field lengths/shape (`annual_plan_item.py` validate; `departmental_plan_entry.py` validate).
- `annual_plan_version.json:83-91` `version_status` is `read_only: 1` (UI only); the same doctype stores `submitted_snapshot`, `snapshot_hash`, `preparation_signature`, `funding_state`. `annual_plan.json:12-13` `active_version`, `open_successor_version`.
Rule: PLN §4.5 field table: `version_status` "Governed only", `active_version_id` "Activation transaction only", `submitted_snapshot_id` "Immutable", Plan Item `title` etc. "Planner Draft only"; PLN §5.2.3 (HOPF signature -> AO adoption -> statutory approval -> publication before Active); §5.1.5 (certified DPP snapshot immutable); AGENTS.md §4.5 ("Never silently rewrite approved history").

Reproduction (user holding the Procurement Planner role):
1. `PUT /api/resource/Annual Plan Version/<v>` `{"version_status":"Active"}` then `PUT /api/resource/Annual Plan/<p>` `{"active_version":"<v>"}` -> expected 403/417; actual 200: plan Active with no HOPF signature, AO adoption, statutory decision, Treasury evidence or publication. Requisitions then authorise against it (draws Planning allowance, reserves Budget funds).
2. `PUT /api/resource/Annual Plan Item/<i>` `{"estimated_total":..., "procurement_method":...}` on an Awaiting-AO or Active version -> frozen content rewritten while `snapshot_hash` still matches the old snapshot.
3. Departmental Author: `PUT /api/resource/Departmental Plan Version/<v>` `{"version_status":"Accepted"}` and edits to `Departmental Plan Entry` of a Submitted/Accepted version.
Note the Planning services themselves are correct (they use `envelope.locked`, `check_record_version`, SoD `require_not_segregated` - C5); the hole is only the parallel REST path.

### F4. High - Budget Version / Line Version / Budget are writable by Budget Officer and Budget Approver with no status guard: approved amounts and Active status editable. CODE DEFECT

Evidence:
- DocPerm: `procurement_budget_version.json:250-266` Budget Officer create+write, Budget Approver write; `procurement_budget_line_version.json:133-145` Budget Officer create+write; `procurement_budget_line.json:71`; `procurement_budget.json:95`.
- `procurement_budget_version.py` validate checks only revision_type pairing and a future approval date; `procurement_budget_line_version.py`, `procurement_budget_line.py` are `pass`. `procurement_budget_version.json:76-81` `status` select Draft/Submitted for approval/Active/Superseded/Closed (UI read-only only). `procurement_budget_line_version.json` `approved_amount` currency.
- The service layer keeps its own guards (`budget_line_contracts.py:_save_budget_lines_draft` requires Draft) but REST bypasses them.
- The only database guard is the Active-per-budget unique marker (`patches/bud_chg_001_v1_3_phase4_active_version_unique_index.py`), which does not stop two successive writes (`Superseded` then `Active`).
Rule: BUD-BR-005 (only Draft versions editable), BUD-BR-021/022 (approval rechecks and activates atomically), BUD-BR-025 and BUD-BR-028 ("statuses ... never client-editable", "Only a successor Version ... changes an approved amount"), BUD §4 line 1245 ("Active, Superseded and Closed versions are immutable"), BUD-BR-015.

Reproduction (Budget Officer):
1. `PUT /api/resource/Procurement Budget Line Version/<lv of the Active version>` `{"approved_amount": 1000000000}` -> expected 417 (immutable); actual 200 (affordability headroom for every downstream check_funding changes, no successor, no approval).
2. `PUT /api/resource/Procurement Budget Version/<draft>` `{"status":"Active"}` after `PUT .../<old active>` `{"status":"Superseded"}` -> self-activation without Budget Approver, without readiness (`_evaluate_readiness`), without the separation-of-duties check (`budget_authorization.py:125-131`), without ledger events.
3. Budget Approver: any field of a Submitted/Active version (`approval_reference`, `authorised_total`).

### F5. High - Strategic Plan Version: approval can be skipped, and Active content is mutable, by a Strategy Author over REST. CODE DEFECT

Evidence:
- DocPerm `strategic_plan_version.json:143-153` Strategy Author create+write (same on Strategic Plan, Strategy Node, Performance Indicator/Target). No `has_permission` hook in strategy.
- `strategy_domain_guards.py:125-129`:
  ```python
  prev_status = None if doc.is_new() else frappe.db.get_value("Strategic Plan Version", doc.name, "status")
  if prev_status in VERSION_IMMUTABLE:
      for f in ("plan_id", "version_number", "based_on_plan_version_id"):
          if doc.has_value_changed(f): frappe.throw("Approved/Active plan versions are immutable")
  ```
  Only three identity fields are protected; `status`, `effective_from`, `effective_to`, `return_reason` are free. The only status check is the overlap lock when a save makes a version Active (`:134-135`).
- Strategy Node edits are gated by `_assert_version_editable` (`:179-184`, checks the new `plan_version_id` only).
Rule: STR §6.1 / line 636 ("Submitted for approval, Active and Superseded versions are immutable"), STR-BR-006 ("Active content is immutable"), STR-BR-012 (submission readiness), STR-BR-015 (approval repeats readiness and activates atomically), STR-AC-010 (author cannot approve).

Reproduction (Strategy Author):
1. `PUT /api/resource/Strategic Plan Version/<draft>` `{"status":"Active"}` (or POST a new version with `status:"Active"`) -> expected 417; actual 200: version Active with no Submit, no Approver, no readiness, no audit event; Planning's "Active Primary plan" resolution (STR-BR-017) now serves it.
2. `PUT /api/resource/Strategic Plan Version/<active>` `{"effective_to":"2030-01-01"}` -> accepted (applicability window of an Active version rewritten).
3. `PUT /api/resource/Strategy Node/<node of Draft v2>` `{"plan_version_id":"<Active v1 node's version moved to Draft>"}`: a node whose own version is Active cannot be edited, but a Pillar (no parent) can be re-parented onto a Draft version (guard reads the NEW `plan_version_id` only).

### F6. High (legacy) - TM2 publication API accepts a caller-supplied `actor`: approve/publish a tender as any user. CODE DEFECT (retired-pending code still routable)

Evidence: `tender_management/tender_publication/api/handlers.py:192,222,237,252,272,292,312` each endpoint takes `actor: str | None = None` and passes it to the service; `approval_decision.py:64-65`, `snapshot/tender_publication_snapshot.py:83-84`, `publication/transaction.py:28-29`: `return _strip(actor) or _strip(frappe.session.user) or "Administrator"`; `enforce_sec_authorization(actor=act, ...)` (`approval_decision.py:263-270`) then authorises the forged identity. Also falls back to `"Administrator"` when neither is present.
Rule: AGENTS.md §4.3; TRUST/AUTH "technical access grants no business action"; BDS legacy_inventory §4 (this workbench is "kept live until OD-F clean-up", so it is still reachable).
Reproduction: any authenticated user `POST /api/method/kentender_procurement.tender_management.tender_publication.api.handlers.pub_api_approve_for_publication` `tender_code=<TM2 code>&actor=<publication approver>` -> decision recorded for the approver.

### F7. High (legacy) - `All` role has create+write on Confirmed Tender Document Package and IT Tender Publication Record; status fields editable. CODE DEFECT

Evidence: `confirmed_tender_document_package.json:219-224` and `it_tender_publication_record.json:317-319` grant role `All` read+write+create. Controllers: `confirmed_tender_document_package.py:21-45` locks artifact fields by the DB `package_status` and exempts when the status itself is moved; `it_tender_publication_record.py:46,73-79` only blocks edits once the DB status is terminal (`Cancelled/Returned/Published`) - the status itself is a freely writable select (`it_tender_publication_record.json:96-102`), `published_at/published_by` are `read_only` only in the UI.
Rule: TPR §12.3 (published facts append-only), TPR §5.8 inv. 7/9; AUTH-ADR §4 (writes require a responsibility).
Reproduction: any logged-in user `PUT /api/resource/IT Tender Publication Record/<n>` `{"status":"Published"}` (marks a publication Published with no publication transaction; record then locks as terminal); `PUT /api/resource/Confirmed Tender Document Package/<n>` `{"package_status":"Invalidated"}` invalidates a confirmed package (then `tender_html` is editable because the Invalidated branch only protects status/hash, `:21-27`). Legacy module owner-sanctioned until clean-up (`legacy_inventory.md` §1/§4); classify accordingly.

### F8. Medium - Need Planning Intake Projection grants create/write/delete to Departmental Author, HoD, Planner and Auditor although NDS declares it read-only. CODE DEFECT

Evidence: `need_planning_intake_projection.json:99-171` (all six roles `create/delete/write`), controller `need_planning_intake_projection.py` validate only checks revision ownership. The two sibling projections (`need_planning_usage_projection.json`, `need_planning_disposition_projection.json`) correctly give business roles no write. NDS §4.11: "stores a read-only projection ... users cannot edit it" and the controller docstring says the same.
Reproduction: Auditor `DELETE /api/resource/Need Planning Intake Projection/<need>` (or PUT `{"position":"No update needed"}`) -> expected 403; actual 200; the Need page then hides "Create update" / shows a false position (re-creates the late-accepted dead end the projection was built to fix).

### F9. Medium - Planning projection endpoints are callable by a human with caller-chosen values, including `actor`. SPEC GAP / CODE DEFECT
`api.py:98-103` whitelists `project_planning_usage/disposition/intake` directly; gate is `in_scope(Procurement Planner) or is_administrative` (`usage.py:181, 326, 453`). NDS §7.5 line 573 ("Registered Planning producer only") and §7.4 line 562 `actor` "Trusted actor identity ... Browser-supplied author identity is not trusted", yet `project_planning_disposition(... actor: str = "", ...)` takes it from the request. `is_actively_included` (`usage.py:239-243`) reads `usage` to decide the withdrawal block (NDS-BR-016, `lifecycle.py:966-998`). A Procurement Planner (or anyone via F1) can `POST ...project_need_planning_usage` `usage=Not included` for a Need an Active Plan depends on and then withdraw it, or assert `Fully included`. Classify: CODE DEFECT against §7.5 (human principals should not be accepted).

### F10. Medium - Budget separation of duties uses the FIRST submission event, not the current attempt. CODE DEFECT
`budget_authorization.py:112-122` `_submitted_by` reads the Budget Audit Event `Budget version submitted` with `order_by="event_at asc"` (earliest); `:125-131` blocks only that user. BUD18-AC-062: "approval checks the current attempt's submitter for segregation"; BUD §6 line 329. The current submitter is already stored on the version (`budget_readiness_contracts.py:572 version.submitted_by = frappe.session.user`) but unused. Scenario: Officer A submits, Approver returns (`_return` `:599`), Officer B (who also holds Budget Approver) re-edits and resubmits; A is blocked, B is not -> B approves their own submission. Compounded by `safe_record_event` (`budget_audit_contracts.py:176-182`) swallowing audit-write failures: if the submit event row failed to write, `_submitted_by` returns None and nobody is blocked. (Contrast Strategy: `strategy_authorization.py:102-109` iterates newest-first, correct.)
Reproduction: users A (Officer), B (Officer+Approver); A `submit_budget_version`; B-less approver `return_budget_version`; B `save` and `submit_budget_version`; B `approve_budget_version` -> expected AUTH_SEGREGATION_BLOCKED, actual ok.

### F11. Medium - Technical roles (System Manager / Administrator) hold write/delete DocPerm and no controller guard on immutable approved records; audit store is editable. CODE DEFECT (against AUTH §8 "technical roles hold no business action")
Evidence (DocPerm create/write/delete = `cwd`): `Procurement Requisition`, `Requisition Version`, `Requisition Decision`, `Authorised Requisition Handoff`, `Requisition Task` (requisitions/doctype/*.json, controllers `pass`, `requisition_version.py:9-10`); `Tender` and `Tender Task` (`tenders/doctype/tender/tender.py:9-10`, `tender_task.py:9-10`, SM `cwd`); `Approved Plan Snapshot` (SM/Administrator `cw`, `pass`), `Plan Governance Decision`, `Plan Publication` etc.; `Funding Reservation` / `Procurement Commitment` (SM `cw`, status and `remaining_amount` editable); `Strategic Plan Version` and `Procurement Budget Version` (SM `cwd`, no `on_trash`); core `Audit Event` (`audit_event.json` SM/Administrator `cwd`, `audit_event.py` is `pass` although `audit_event_service.py` documents "Append-only audit events"). Requisition services still set `flags.kt_lifecycle` (`authorise.py:134-135,196-197`, `lifecycle.py:92`) but no requisition controller reads it - the guard that Tenders has (`tender_version.py:16-23`) was never ported.
Rule: REQ §7.5 inv. 12 ("Submitted and authorised Versions, rows, files and digests are immutable"), TPR §12.3 rule 1, STR line 636 ("Deleting lifecycle events ... prohibited"), AUTH-ADR-001 lines 182/361/831; also the Strategy SoD check (`strategy_authorization.py:102-109`) reads the editable Audit Event rows, so editing `performed_by` or deleting the `Submit for approval` event defeats STR-AC-010 and re-enables `discard_strategy_plan_draft` (`strategy_writes.py:265`) for a submitted draft.
Reproduction (System Manager): `PUT /api/resource/Requisition Version/<authorised>` `{"version_status":"Draft"}`; `DELETE /api/resource/Authorised Requisition Handoff/<h>` (expected refusal, handoff referenced by reserved Budget lines); `DELETE /api/resource/Audit Event/<id>`; `DELETE /api/resource/Strategic Plan Version/<active>`.
Severity Medium because the actor is a technical administrator, but the doc says even they hold no business action and approved records must never be edited or deleted.

### F12. Low - Optional idempotency keys and optional `expected_version` on Strategy and Budget state commands; key matched without payload. CODE DEFECT vs KT-STD-001 §11
KT-STD-001 §11: "Every state command carries expected_version ... Every retriable command carries an idempotency key and returns the original committed result on replay." Strategy: `strategy_consumer_api.py:134-190` pass `idempotency_key or None` and `expected_version or None`; `strategy_idempotency.py:21-31` runs without a key and, when a key exists, returns the journalled result by key alone (no payload digest, no document/action comparison): reusing key K for approve on version B returns the result of version A with no effect on B and no conflict error. `_check_expected_version` (`strategy_transitions.py:83-91`) returns when None. Budget: `budget_idempotency.py:49-51` "Commands without a key run as before", `_is_stale` (`budget_readiness_contracts.py:546-548`) ignores a missing token. No duplicate decision/event was found (state guards hold), so Low. NDS/Tenders/Planning/Requisition/Award/Evaluation require the key and compare a payload fingerprint (C4).

### F13. Low - Replay lookups run before authorisation (NDS) or before the row lock (Tenders, Award, Evaluation, Planning). CODE DEFECT (low)
NDS `_existing(idempotency_key, payload)` is called first (`lifecycle.py:533,600,650,723,836,880,932,1012,1090`) and returns the stored result (need name/state/revision ids) to any caller who knows the key and repeats the payload: `fingerprint` excludes `user` (`lifecycle.py:124-135`). Tenders/Award/Evaluation `replay_or_none`/`command` look up the journal before `load`/`lock` (e.g. `lifecycle.py:approve_tender_package`, `award/services/records.py:command`), so a concurrent double-click whose twin has not committed gets `TND_STALE_VERSION`/`AWD_RECORD_CHANGED` instead of the original result (no duplicate effect: the row lock + state/record_version check holds). Journal rows are not unique on `idempotency_key` in Tenders/Award/Evaluation (`tender_command_journal.json` no `unique`).

### F14. Low - Audit writes swallowed on failure after the state change committed. CODE DEFECT (low) vs AGENTS.md §4.3 (audit actor/time/reason)
`budget_audit_contracts.py:176-182 safe_record_event` and `award/services/records.py:audit` (`except Exception: frappe.log_error`) let an approve/decision commit with no ledger/audit row; for Budget this also removes the data the SoD check reads (F10).

## Checked and clean

C1. Award (16), Bid Evaluation (22), Bid Opening (13), Bid Submission (21), Proceedings (8): no role (including System Manager) has create/write/delete DocPerm, so `/api/resource` and `frappe.client.*` writes are refused except for Administrator; every controller `validate` throws unless the module command flag is set (`award/doctype/award_decision/award_decision.py` `kt_awd_command`; `evaluation_report_version.py` `kt_evl_command`) and `on_trash` throws unless `kt_fixture_wipe`. Flags are only set in `*/services/records.py` (`award/services/records.py:43,53`, `bid_evaluation/services/records.py:39,45`, `bid_opening/services/records.py:40,46`, `proceedings/services/records.py:41,47`); no whitelisted function sets a flag from request data.
C2. Tender family except `Tender`/`Tender Task` (Tender Version, Addendum, Publication, Channel Confirmation, Clarification, Cancellation, Bid Definition, Decision, Document, Event, Submission Handoff, Command Journal): `validate` rejects any non-new save without `flags.kt_lifecycle` (`tender_version.py:16-23`) and `on_trash` rejects deletion; child tables are covered because a child save goes through the parent `save()`. Single writer `envelope.bump` (`tenders/services/envelope.py:103-115`).
C3. Needs: `Departmental Need Decision`, `Departmental Need Event` (immutable payload fields), `Need Planning Usage/Disposition Projection` have no business write DocPerm; Decision/Event/Review Task/Withdrawal `on_trash` refuse (`departmental_need_decision.py`, `departmental_need_event.py`, `departmental_need_review_task.py`, `need_withdrawal_request.py`); Need and Revision `on_trash` refuse (`departmental_need.py:39-40`, `departmental_need_revision.py:on_trash`). Budget Audit Event: SM create only, `on_trash` refuses (`budget_audit_event.py`).
C4. Idempotency and concurrency of the command services I read in full: NDS (`lifecycle.py:138-165` key required, fingerprint conflict, `_locked_need` FOR UPDATE `:243-251`, `_check_version`, task token); Tenders (`envelope.py:50-76` replay + `locked` + `check_record_version`, `lifecycle.py` approve/return/reopen with SoD `require_segregation`); Requisitions `authorise.py:81-163` (revoke `:165`) (root locked `records.py:95-98 require_root(lock=True)`, task, version and package locked, Budget reservation + Planning drawdown + decision + handoff + outbox in one `envelope.atomic`; revoke re-checks `handoff.consumed_at` under the handoff lock); Planning `plan_governance.py:368-583` (`replay_or_none`, `envelope.locked`, `assert_task_token`, `require_not_segregated`, status gate, `record_command`); Award `decision.py:107-138` (lock, state guard, `committed_decision` single-commit guard); Evaluation `signing.py:130-158` (lock, exact report version, replay-safe sign). Second concurrent same-key request fails closed (stale/record-changed), no second decision/event/reservation was constructible from the code.
C5. Budget `release_reservation`/`convert` are state-idempotent (`budget_commitment_contracts.py:117-151`); Budget Version Active uniqueness is enforced in the database (`patches/bud_chg_001_v1_3_phase4_active_version_unique_index.py`, generated column + unique key, registered at `patches.txt:22`).
C6. Strategy services: `transition_plan_version` (`strategy_transitions.py:150-213`) enforces the 3-row table, capability and SoD (newest submit event first, `strategy_authorization.py:102-109`), readiness, atomic supersession, audit; `discard_strategy_plan_draft` refuses submitted drafts (`strategy_writes.py:259-270`); Strategy Node/Indicator/Target validators gate on the version being Draft (`strategy_domain_guards.py:179-184`); no `db.set_value` of a status in Strategy services (grep: only `display_order` parking `strategy_writes.py:391`).
C7. Direct DB writes found in Planning (`dpp_validation.py:68,113,208-210`, `plan_publication.py:72-82`, `publication_pipeline.py:153-206,287-291`, `plan_workbench.py:229-233,332`, `schedule.py:205`, `treasury.py`, `departmental_update.py:179`), NDS (`lifecycle.py:301,677,1121,1212`, `events.py:244`), Requisitions (`records.py:184,196` slot key, `events.py:62` outbox delivered), Budget revision requests/events (`budget_revision_request_contracts.py:251,359,365`) all run inside the owning module's own transition/outbox service under a row lock and, in Planning, with the `record_version` token for concurrency; none writes another app's record. They skip controller `validate` (pattern against AGENTS.md §4.4 but not a bypass of a stated rule); Planning/Requisition controllers carry no validation to skip, which is why F3/F11 matter.
C8. `flags.ignore_validate` / `ignore_mandatory` appear only in seeds, install, `File` CAS and the legacy Tender Configuration services (`tender_configurations/services/*` `ignore_mandatory`); none in Strategy/Budget/NDS/Planning/Requisition/Tender/Award code paths.
C9. Calibration items in this domain: (a) kwargs transport fields: fixed pattern present at `departmental_needs/api.py:66-75` (`_TRANSPORT_FIELDS`, `_command_args`); `bid_evaluation/api.py:8` and `award/api.py:6` document the same; the fix forwards the remaining request fields verbatim, which is the root of F1 (the `user` field is not filtered). Only NDS uses `**kwargs` among the 668 whitelisted callables. (b) Editor post-save race / optimistic lock: `record_version` tokens are checked under row locks in NDS, Tenders, Requisitions, Planning, Award; Strategy/Budget use `modified` and accept an omitted token (F12). (c) Late-accepted Need dead end: `Need Planning Intake Projection` exists (`usage.py:436-488`) but its DocPerm lets any listed role rewrite it (F8). (d) Intake scope, reservation denominator, 7-day preparation period, catalogue-control digest, universal Strategy read, dropped-doctype crash: not state-machine items; not examined here.

## Sampled, not exhaustively verified

- Bid Submission / Bid Opening / Evaluation (other than signing) / Proceedings command bodies: only the shared `records.command` envelope and guard model were read (`award/services/records.py:128-161`, `bid_evaluation/services/records.py:106-136`, `bid_opening/services/records.py`, `bid_submission/services/records.py:51-150`); the individual 100+ commands were not each traced for preconditions.
- TM2 (legacy) doctype guards (`tender_management/immutability_guards.py`, 23 `tm2_*` doctypes with Procurement Officer create+write): shared guard module exists and several controllers call it; not traced per doctype; excluded as retired-pending (OD-F).
- Core configuration doctypes with status fields (Financial Year, Procurement Entity/Version, Organisation Unit, URA, Regulatory Reference etc.) belong to the CFG/AUTH sweeps; only `regulatory_reference.py` and `organisation_unit.py` were glanced at.
- Contract Management: no doctype exists (`contract_management/doctype/` empty), so no contract state machine to audit.
