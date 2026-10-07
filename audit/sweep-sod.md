# Sweep: segregation-of-duties (SoD) enforced server-side

READ-ONLY static audit. Written 6 Oct 2026. Repo root `/home/midasuser/frappe-bench/apps/kentender_v1`. No test, migrate, seed or database command was run.

## 1. Header

**Scope.** SoD / maker-checker / conflict-of-interest rules across Strategy -> Budget -> Needs -> Planning -> Requisition -> Tenders -> Bid Opening -> Evaluation -> Award -> Contract. For each rule: where it is enforced, whether it compares actor identity (user, and responsibility where the doc says), whether it holds on every path (API, background, direct DocType save), and whether it can be bypassed by role stacking, reassignment, delegation or a client-supplied identity.

**Docs read (latest versions, confirmed by `ls | sort -V`).** STR v1_9 (02_strategy), BUD v1_12 (03_budget), NDS v1_16 (01_departmental_needs), PLN v1_29 (04_planning), REQ v1_14 (06_requisitions), TPR v0_17 (11_tenders), BOP v0_11 (14_bid_opening), BDS v0_11 (12_bid_submission), EVL v0_5 (15_bid_evaluation), AWD v0_5 (16_award), AUTH-ADR-001 v1_11, TRUST-ADR-001 v0_2 (all `docs/mvp-1-r1/...`). Note: the task named BDS/BOP/EVL "v0_5"; the latest BOP is v0_11 and BDS v0_11, EVL v0_5 is latest. TPR `TPR-CHG-001_FOLLOW_UPS.md` FU-08 read for the legacy Tender Management status.

**Method (reproducible).**
```
# 1. rule discovery in the 10 docs
grep -nEi 'segregat|same person|same user|cannot be the same|must not be the same|maker.?checker|conflict of interest|different from|not the same|self-approv|separation of dut|four.eyes|must not (approve|be)|cannot approve|did not (author|prepare|create)|SoD|sod_tag|AUTH_SEGREGATION|incompatible|distinct (user|person|member)|another (user|person|member)|no-self|cannot (certify|accept|authoris|confirm|adopt|sign|decide|approve|issue|act|be)|independent (of|member|from)|recus|appointed|roster|declar' <doc>
# 2. enforcement discovery
grep -rnE 'AUTH_SEGREGATION_BLOCKED|NDS_MAKER_CHECKER|PLN_SEGREGATION_CONFLICT|REQ_SOD_BLOCKED|TND_SOD_BLOCKED|is_owner|require_segregation|require_not_segregated|_blocked_by_self_approval|is_excluded_from_evaluation|processing_actors' --include=*.py kentender_*
# 3. identity-as-parameter: AST scan (scratchpad wl.py) of every @frappe.whitelist function and every `x = frappe.whitelist()(fn)` alias in core/strategy/budget/procurement/suppliers/governance for parameters named user/actor/principal/performed_by/by/... or **kwargs
# 4. direct-DocType-write surface: parse every doctype JSON in needs/planning/requisitions/tenders/opening/evaluation/award for DocPerm rows with write/create/delete, then read each controller for a status/command guard (flags.kt_*_command / kt_lifecycle)
# 5. Frappe facts checked in apps/frappe: frappe/__init__.py:1150 get_newargs (forwards every declared param incl. `user`); frappe/handler.py:86 execute_cmd (frappe.call(method, **frappe.form_dict)); no field-level read_only enforcement in frappe/model/document.py
```

## 2. Coverage

Rules enumerated: 27. Classification of every rule:

| # | Rule (doc §) | Classification | Evidence |
|---|---|---|---|
| 1 | Strategy: author of a version cannot approve it (STR §6/L203, L245, L258, STR-AC-010) | Partial (submitter only) - F10 | strategy_authorization.py:102-127 |
| 2 | Budget: submitting Officer cannot approve (BUD §6/L329, L368, BUD-AC-025; current attempt: BUD18-AC-062 L1431, BUD19-AC-014 L1465) | Partial, bypassable - F2, F4 | budget_authorization.py:112-131 |
| 3 | Needs: submitter cannot decide revision (NDS-BR-006 L425, NDS-AC-010 L1631) | Enforced on owner==principal, but principal is client-supplied - F1 | lifecycle.py:725-733 |
| 4 | Needs: withdrawal requester cannot decide (NDS L1414) | Enforced, same F1 hole | lifecycle.py:1092-1106 |
| 5 | Planning: certifier of DPP cannot accept/return as Planner (PLN L392, §6.4 row 1) | Enforced | planning_authorization.py:410-413; dpp_validation.py:87,174 |
| 6 | Planning: Planner-chain actor cannot confirm Finance / adopt as AO / approve as statutory (§6.4 rows 2-4) | Enforced (one gap: F12) | planning_authorization.py:357-421; plan_finance.py:282,333; plan_governance.py:479,532,637 |
| 7 | Planning: HOPF preparation signature joins the chain (§6.2, §6.4) | Enforced | planning_authorization.py:375-376 |
| 8 | Planning: correction chain never resets history (§6.4 last para, PLN-RI-013) | Enforced | planning_authorization.py:326-354 |
| 9 | Requisition: Author cannot complete HoD decision unless HoD and prepared in that capacity (REQ §7.3 b1, REQ-AC-045) | Partial - F9 | lifecycle.py:255-262 |
| 10 | Requisition: authoriser cannot be the departmental submitting authority (REQ §7.3 b4) | Enforced | authorise.py:103-105 |
| 11 | Requisition: HOPF cannot edit departmental content / HOPF alone cannot prepare (REQ §7.3 b3, REQ19-AC-045) | Enforced (role gate) | requisition_authorization.py:175-191 |
| 12 | Tender: preparer/submitter cannot approve as HOPF (TPR §6/L719, TPR09-AC-035) | Partial - F5 | tenders/services/lifecycle.py:205-225 |
| 13 | Tender: preparer/submitter/HOPF-approver cannot authorise publication as AO (L719, TPR09-AC-039) | Partial - F5 | publication.py:62 |
| 14 | Tender: AO return of approved package has the same segregation (TPR16-AC-016) | Enforced | publication.py:252 |
| 15 | Opening: committee >= 3 incl. independent member, independent of processing (BOP-A02, L158) | Partial - F13 | bid_opening/services/appointment.py:81-93 |
| 16 | Opening: independent member excluded from same-tender evaluation (BOP-A17, EVL-A01) | Partial, order-dependent - F6 | evaluation/appointment.py:49; bid_opening appointment.py:55-61 |
| 17 | Opening: chair cannot open alone, roster all present, two distinct custody confirmations incl. independent (BOP-A02, BOP-A13, TRUST §2) | Enforced | guards.py:30-80; custody_participation.py:62-67 |
| 18 | Evaluation: declared conflict stops that member's bid access, AO resolves (EVL L67) | Partial, self-clearable - F7 | declaration.py:50-56; reads.py:62 |
| 19 | Evaluation: each member declares personally; signs personally (EVL L67, L162) | Enforced (session actor, no identity param) | declaration.py:28-57; bid_evaluation/api.py:57-59 |
| 20 | Evaluation: AO alone appoints/replaces committee (EVL §7.2) | Enforced | appointment.py:36-38, 76-77 |
| 21 | Award: HOP signs opinion, AO decides; evaluators acquire no award power (AWD §6 L275) | SPEC GAP: no actor-identity rule at all - F8 | award decision.py:107-110; opinion.py:41 |
| 22 | Budget: Finance Confirmation Officer vs Budget Officer for same line (BUD21-XD-002 L1673, open question) | Missing (spec open) - F16 | none |
| 23 | AUTH registry `sod_tags` "consumed by domain segregation checks" (AUTH §4.4 L173, §5.8 L322) | Not consumed anywhere - F14 | business_role_registry.py:29,67 |
| 24 | AUTH §8 L373: setup authority is not business authority | Missing guard on self-grant and technical-user target - F14 | responsibility_administration.py:84-111, 382-388 |
| 25 | BDS01-IMP-008: separate preparer/signatory "where the approved policy requires" | SPEC GAP (no policy stated); not examined further - F16 | BDS v0_11 L2349 |
| 26 | Contract (chain end) | No code (`contract_management/doctype`, `services`, `api` empty) and no approved doc | - |
| 27 | Legacy Tender Management v2 publication approval | Missing SoD + client `actor` - F11 | handlers.py:252; approval_decision.py:248-270 |

Whitelisted-function sweep (identity-as-parameter): 668 `@frappe.whitelist` functions and aliases scanned in core, strategy, budget, procurement, suppliers, governance. 37 had a `user`/`actor`/`principal`/`**kwargs` surface. Classified: 20 Needs read/command endpoints with `user` forwarded (F1); 3 `save_need_draft`/accept/return/decline `**kwargs` (F1); 8 legacy TM2 publication endpoints with `actor` (F11) plus 3 TM2 read endpoints; 3 core `responsibility_api` endpoints where `user` is the grantee, not the actor (clean). Strategy, Budget, Planning, Requisition, Tender, Opening, Evaluation and Award endpoints take identity from `frappe.session.user` only (clean, see section 4).

DocType direct-write sweep: 145 doctypes in needs/planning/requisitions/tenders/opening/evaluation/award checked. Opening, Evaluation, Award have no business-role write DocPerm (clean). Tenders: only System Manager has write and the controllers enforce `flags.kt_lifecycle` (clean). Strategy, Budget, Needs, Planning and Requisition doctypes: see F3 and F15.

Calibration (known past defects in this domain):
- Whitelisted `**kwargs` transport-field 500: FIXED. `departmental_needs/api.py:70-75` (`_TRANSPORT_FIELDS`, `_command_args`). But the same fix leaves `user` forwarded, producing F1.
- Intake-scope, handoff-rename, reservation denominator, 7-day period, catalogue digest, post-save race, dropped-table crash, Strategy read: not SoD; not examined here.

## 3. Candidate findings (most severe first)

### F1 - CRITICAL - Needs commands take the acting user as a client parameter (identity spoof; defeats NDS maker-checker, role and OU checks)

**Evidence.**
- `kentender_procurement/kentender_procurement/departmental_needs/services/permissions.py:59-60`: `def actor(user: str | None = None) -> str:` / `value = cstr(user or frappe.session.user).strip()` (the supplied value wins; no comparison with the session).
- Every Needs command resolves its principal this way, e.g. `services/lifecycle.py:725` (`review_need`: `principal = actor(user)`), then `:729 require_review_command(doc, principal)`, `:732 if is_owner(doc, principal)`. Same at lines 535, 602, 652, 838, 882, 934, 1014, 1092.
- The services' signatures declare `user`: `lifecycle.py:703-712` (`review_need(..., user: str | None = None)`), `submit_need` 643, `withdraw_need` 824, etc.
- They are whitelisted directly or with `**kwargs` passthrough: `departmental_needs/api.py:92-97` (`submit_need_revision = frappe.whitelist()(lifecycle.submit_need)` ... `decide_accepted_need_withdrawal = frappe.whitelist()(lifecycle.decide_withdrawal)`), `:113-127` (`accept_need_revision(**kwargs)` -> `lifecycle.review_need(decision="accept", **_command_args(kwargs))`). `_command_args` (`api.py:73-74`) strips only `cmd`, `csrf_token`, `_`.
- Framework fact: `frappe/__init__.py:1150-1172` `get_newargs` keeps every kwarg named in the function signature; `frappe/handler.py:86` calls `frappe.call(method, **frappe.form_dict)`. A POST field `user=` therefore reaches `actor()`.
- Reads leak too: `services/workspace.py:217,373,643` (`get_workspace`, `get_review_task`, `get_need` all take `user`) and `context.py:140,216`.

**Governing rule.** AUTH-ADR-001 v1.11 §5.5 L295 "The client never supplies an assignment ID, effective role, permitted scope or available action as authority ... the server ... resolves again" and §5.6 step 1 "authenticate an enabled System User". NDS-BR-006 (L425) "Maker-checker is rechecked on the server". NDS §6 role/OU scope.

**Impact.** Any authenticated user (even with no Needs role) can act as any other user: accept their own Need by passing `user=<another in-scope HoD>`; create Needs for any OU; decide withdrawals; read other users' scoped workspaces. Audit records the spoofed principal as actor.

**Reproduction.** Session as Departmental Author A (owner of Need N, submitted). `POST /api/method/kentender_procurement.departmental_needs.api.accept_need_revision` with `need=N, task=<open task>, expected_version=<n>, decision_token=<tok>, idempotency_key=k, user=<HoD-H2>`. Expected (correct): rejected. Actual (by reading): `principal = H2`, `require_review_command` passes (H2 holds HoD in the OU), `is_owner(doc, H2)` is False, Need becomes Accepted. Test sketch:
```python
frappe.set_user(author)            # holds only Departmental Author in OU
need = submit(...)                 # owner == author
frappe.set_user(author)
r = frappe.call("kentender_procurement.departmental_needs.api.accept_need_revision",
                need=need, task=task, expected_version=v, decision_token=tok,
                idempotency_key="k", user=other_hod)   # other_hod != author
assert r raises NDS_SCOPE_DENIED   # fails today: returns accepted
```
**Classification.** CODE DEFECT.

### F2 - HIGH - Budget no-self-approval reads the FIRST submission, not the current attempt

**Evidence.** `kentender_budget/kentender_budget/services/budget_authorization.py:112-122`:
```
event = frappe.db.get_value("Budget Audit Event", {"budget_version": version_name, "event_type": "Budget version submitted"}, ["actor"], order_by="event_at asc")
```
and `:125-131` `_blocked_by_self_approval` returns `_submitted_by(version_name) == user`. Each re-submit after Return writes a new "Budget version submitted" event (`budget_readiness_contracts.py:572-581`), and the current submitter is stored in `version.submitted_by` (`:572`) but is not used for the check.

**Governing rule.** BUD v1.12 L329/L1175 "The submitting Budget Officer cannot approve the same version ... Enforced from the version's own submission audit event"; L329 third bullet "Decision authority is checked against the submission being decided"; BUD18-AC-062 (L1431) "approval checks the current attempt's submitter for segregation"; BUD19-AC-014 (L1465); BUD18-CHG-021 (L1623) "no-self-approval uses current submission authority".

**Bypass.** Officer A submits, Approver returns, user B (holding Budget Officer + Budget Approver) corrects and resubmits as the current attempt; `_submitted_by` returns A, B is not blocked and approves their own submission. (Inverse: A, the earlier submitter, is wrongly blocked on someone else's later attempt.) No test covers resubmission by a different person (`grep AUTH_SEGREGATION_BLOCKED|resubmi` in budget tests finds none).

**Reproduction / test sketch.**
```python
A = officer_only; B = officer_and_approver
v = create_draft_as(A); submit_as(A, v); return_as(approver, v)
submit_as(B, v)                       # B is the current submitter
assert approve_as(B, v) raises AUTH_SEGREGATION_BLOCKED   # fails today
```
**Classification.** CODE DEFECT.

### F3 - HIGH - Business-role holders have direct write on state-bearing DocTypes with no transition guard (command-layer SoD bypassable via /api/resource or frappe.client.set_value)

**Evidence (DocPerm write for business roles + controller with no state guard).**
- Budget: `kentender_budget/.../doctype/procurement_budget_version/procurement_budget_version.json:250-252` (Budget Officer create+write) and `:262-264` (Budget Approver write). Controller `procurement_budget_version.py:11-18` validates only revision type and approval date. Field `status` (json :76) is not read-only. `has_permission` hook (`budget_read_scope.py:51-68`) only narrows reads for approved-only readers.
- Strategy: `strategic_plan_version.json:150-152` (Strategy Author write); controller `strategic_plan_version.py` -> `validate_strategic_plan_version` (`strategy_domain_guards.py:89-135`) checks numbering, period, immutability of three fields and overlap on Active; it does NOT check status transitions or who made them.
- Planning: `annual_plan_version.json:222-225` (Procurement Planner write); controller `annual_plan_version.py` is `pass`. `version_status` is `read_only: 1` in JSON but the framework does not enforce field read_only server-side (no occurrence in `frappe/model/document.py`).
- Needs: `departmental_need.json:120-128` (Departmental Author write, Head of User Department write); controller `departmental_need.py:27-31` only validates that `current_state` is a valid state name. Same for `Departmental Need Revision`, `Departmental Plan Version`, `Departmental Plan`, `Annual Plan`, `Annual Plan Item` (my DocPerm sweep).
- Core hook `kentender_core/services/authorization.py:461-498` states it "only ever *restricts* — granting a business mutation is `require_responsibility`'s job"; it does not veto writes.
- Contrast (clean): Tenders `tender_version.py:15-19` (`kt_lifecycle` guard), Proceedings/Bid Submission/Evaluation/Award `kt_*_command` guards, and Opening/Evaluation/Award expose no business-role write DocPerm.

**Governing rule.** AUTH-ADR-001 §5.6 step 8 (maker-checker applies to every command) and AGENTS.md/CLAUDE.md "Enforce ... allowed state transitions ... on the server for every material action"; STR/BUD/PLN/NDS "no bypass of audit-based self-approval". Setting `status=Active` directly skips submit, approval, SoD, atomic supersession.

**Reproduction.** Session as Budget Officer only: `PUT /api/resource/Procurement Budget Version/<v>` body `{"status":"Active"}` (or `frappe.client.set_value`). By reading, DocPerm permits it and no controller or hook rejects it. Same with Strategy Author -> `Strategic Plan Version.status = "Active"` (only the overlap check fires); Procurement Planner -> `Annual Plan Version.version_status = "Active"`; HoD -> `Departmental Need.current_state = "Accepted for planning"`.
```python
frappe.set_user(budget_officer_only)
doc = frappe.get_doc("Procurement Budget Version", v)   # Draft
doc.status = "Active"; doc.save()                       # expect PermissionError / ValidationError
```
**Classification.** CODE DEFECT (needs a one-run live confirmation on kentender-test.local; static reading shows no guard on any of these paths).

### F4 - MEDIUM - Budget SoD fails open when the submission audit event is missing

**Evidence.** `budget_audit_contracts.py:176-182` `safe_record_event` swallows any exception (`except Exception: frappe.log_error(...); return None`); `budget_readiness_contracts.py:581` submits through it; `budget_authorization.py:112-122,131` returns `None` when no event exists, so `None == user` is False and approval is allowed.

**Governing rule.** BUD L329 "Enforced from the version's own submission audit event" and the segregation denial must be reliable; Strategy by contrast uses a non-swallowing `record_event` (strategy_audit.py:20-70, no try/except) so a failed audit write rolls back.

**Reproduction.** Make `Budget Audit Event` insert fail once (permission/validation) during submit; submitter then approves. Test: patch `record_event` to raise; submit as B (Officer+Approver); `approve_as(B)` succeeds. **Classification.** CODE DEFECT (fix: use the stored `version.submitted_by`, or make the audit write mandatory).

### F5 - MEDIUM - Tender "prepared by" is the Draft's creator only; other officers who edit are not in the SoD chain

**Evidence.** `tenders/services/draft_commands.py:128` sets `"prepared_by": actor` only at StartTender; `:152-161` `save_tender_draft` requires only the site-wide Procurement Officer role (`authz.require_officer`) and never updates `prepared_by`; `lifecycle.py:87,185` copy_draft carries `cstr(version.prepared_by) or actor`. `lifecycle.py:205-211,225` and `publication.py:62,252` test only `prepared_by`, `submitted_by`, `approved_by` columns.

**Governing rule.** TPR §6 L719 / TPR09-AC-035, AC-039: "The person who prepared or submitted a Version cannot approve it as HOPF ... Checks use the immutable Version audit, not role labels alone." TPR IMP-021 (L2082) "Multi-role and reassignment tests".

**Bypass.** Officer O1 starts the Draft; user H (holds Procurement Officer + Head of Procurement Function) edits content via SaveTenderDraft (and the evidence-requirement commands); O1 submits; H approves as HOPF. `prepared_by=O1`, `submitted_by=O1`, so H passes. The spec calls "prepared" ambiguous about co-editing: SPEC GAP on meaning, CODE GAP in that every edit is journalled (`Tender Command Journal` has the editor) but never consulted.

**Test sketch.**
```python
O1 = officer; H = officer + hopf; AO2 = ao
t = start_tender_as(O1); save_draft_as(H, t, values)   # H edits
submit_as(O1, t)
assert approve_as(H, t) raises TND_SOD_BLOCKED          # passes today
```
**Classification.** CODE DEFECT / SPEC GAP (define "prepared").

### F6 - MEDIUM - Independent-opening-member exclusion from evaluation is order-dependent (one-directional check)

**Evidence.** Evaluation asks Opening at evaluation-appointment time only: `bid_evaluation/services/appointment.py:43-49` -> `bid_opening/services/appointment.py:55-61`. The Opening appointment check (`appointment.py:81-93`) compares the independent member only to `opening_seam.processing_actors` (Tender Versions and Tender Publication; `tenders/services/opening_seam.py:91-98`) and never looks at the Evaluation roster. Evaluation committee appointment is allowed before intake/opening (EVL v0_5 L28 "This can happen before opening", L126 "Appointment may exist before intake").

**Governing rule.** BOP-A17 (BOP v0_11 L401) "The designated independent opening member is excluded from later same-Tender Evaluation appointment"; EVL-A01 (L661) "same-tender independent-opening exclusion works through UI and direct API"; BOP L38 conservative policy.

**Bypass.** AO appoints Evaluation committee including U first; then appoints U as the independent opening member (BOP check passes: U not a tender processor). U sits on both. Later checks (`roster.status`, `reads.py:62`) never re-evaluate the exclusion.

**Test sketch.**
```python
appoint_evaluation_committee_as(ao, tender, members=[U, M2, M3])
resp = appoint_opening_committee_as(ao, tender, [..., {"user": U, "committee_role": "Independent member"}])
assert resp["ok"] is False    # passes today (appointment succeeds)
```
**Classification.** CODE DEFECT.

### F7 - MEDIUM - A conflicted evaluator can clear their own declared conflict by re-declaring "No conflict"

**Evidence.** `bid_evaluation/services/declaration.py:50-56`: if the current declaration is a conflict and the new choice is "No conflict to declare", the early return at `:51` does not fire (it requires `current.choice == choice`), the prior declaration is set `Superseded` (`:53-56`) and a new "No conflict" row becomes Current; `roster.status` (`roster.py:67-79`) then reports eligible and `reads.py:62` restores bid access. Only the conflict branch (`:62-66`) creates the AO task and calls `roster_changed`; the retraction path does not involve the AO.

**Governing rule.** EVL L67 "A declared conflict stops that person's bid access immediately and creates the Accounting Officer's task"; L69 eligible member has "no unresolved conflict"; EVL L282/L640 AO resolves via reasoned replacement. The spec does not state that a member may retract; the code lets the conflicted person lift their own block with no third-party decision.

**Test sketch.** Member declares conflict -> `reads.bids` denied -> same member `declare_interest(choice="No conflict to declare", confidentiality_accepted=True)` -> `roster.status(...)["eligible"] is True` and bids readable, with the AO task still open. **Classification.** SPEC GAP (retraction undefined) with a code consequence that fails the stated intent; treat as CODE DEFECT unless owner confirms self-retraction is intended.

### F8 - MEDIUM - No actor-identity SoD anywhere between evaluation, professional opinion and award decision

**Evidence.** `award/services/decision.py:107-110` gates `RecordAwardDecision` on `guards.require_ao(user)` only; `award/services/opinion.py:41,81,141` gate opinion save/sign on `require_hop(user)` only; no code compares the decider/signer with the Evaluation committee, secretary, Tender approver or opinion signer. Evaluation appointment eligibility (`bid_evaluation/services/appointment.py:43-53`) excludes only non-internal users, the independent opening member and declared-conflict users, so the AO, the HOP, and the Tender preparer/approver may be appointed members (people.py docstring: "an office grants no bid access" but does not forbid appointment).

**Governing rule.** AWD v0_5 §6 L275 only says "Evaluation members ... acquire no Award decision power" and "add no ... new committee approval role"; AUTH §5.8 L322 requires segregation "against actual actions ... and the owning module's rules". The owning docs state no rule: SPEC GAP. The task's example "evaluator vs award decider" therefore has no enforced rule and none specified.

**Bypass.** User X holds Accounting Officer + Head of Procurement Function: AO appoints self as Chair; committee signs; X (as HOP, also eligible secretary) signs the opinion; X (as AO) records the Award. Also HOPF who approved the Tender can sit on the committee.

**Test sketch.** `appoint_evaluation_committee_as(ao_x, [X, ...])` ... `sign_opinion_as(X)` ... `record_award_as(X, "Award")`: all succeed. **Classification.** SPEC GAP (needs owner decision), listed as the highest-value gap.

### F9 - MEDIUM - Requisition: HoD self-certification rule is checked on one of two certify paths

**Evidence.** `procurement_requisitions/services/lifecycle.py:255-262` applies `prepared_by == actor and prepared_capacity != HoD -> REQ_SOD_BLOCKED` only in the `Awaiting Department Approval` branch. The `Draft` branch (`:263-266`: `elif root.current_state == "Draft": ... lock(...)`) has no SoD check. `prepared_capacity` is chosen by `draft_commands.py:56-65` which tries HoD first across ANY contributing unit and records it, regardless of which capacity the actor actually exercised or whether it is the lead unit.

**Governing rule.** REQ §7.3 b1 (L586): "A Departmental Author cannot complete the Head of User Department decision on the same Version unless the actor is independently assigned the Head of User Department role and prepared the Requisition directly in that capacity"; REQ19-AC-045 (L1712).

**Bypass.** (a) User A prepares as Departmental Author (capacity recorded Author). A is later given HoD in the lead OU (reassignment). A calls `submit_requisition_to_procurement` on the Draft: `_lead_hod` passes (current HoD), no SoD check in the Draft branch. (b) A user who is Author in lead OU and HoD only in a non-lead contributing OU is recorded capacity HoD and passes the Awaiting-branch exemption if later made lead-HoD.

**Test sketch.** `prepare_as(A)`; grant HoD(lead) to A; `submit_requisition_to_procurement_as(A)` with no task -> expect REQ_SOD_BLOCKED; passes today. **Classification.** CODE DEFECT.

### F10 - MEDIUM - Strategy: "author cannot approve" is implemented as "submitter cannot approve"

**Evidence.** `strategy_authorization.py:102-127`: `_submitted_by` returns the performer of the latest "Submit for approval" audit event; `_blocked_by_self_approval` blocks only that user.

**Governing rule.** STR v1_9 L203 "The author of a version cannot approve it, even when that user also holds Strategy Approver"; L245 "evaluated against the version's audit history"; L258 "cannot approve a version they authored"; STR-AC-010 (L748). Authors can be several users (any Strategy Author may edit a Draft, `strategy_writes.py:70,139,257,354` check the Author capability only).

**Bypass.** Author A (also Strategy Approver) drafts/edits the plan; Author B submits; A approves. A is not the submitter. Also direct-write path of F3.

**Test sketch.** `edit_draft_as(A)`; `submit_as(B)`; `approve_as(A)` -> expect AUTH_SEGREGATION_BLOCKED; passes today. **Classification.** SPEC GAP (author vs submitter undefined; BUD defines the submitter explicitly, STR says author) with a likely CODE DEFECT.

### F11 - MEDIUM (frozen legacy, TPR FU-08) - Tender Management v2 publication approval: client `actor`, role-only authority, no SoD, System Manager may approve

**Evidence.** `tender_management/tender_publication/api/handlers.py:222,252,272,292,312` (`pub_api_submit_for_approval`, `pub_api_approve_for_publication`, `..._return_for_correction`, `..._reject_publication`, `pub_api_publish_tender`) all take `actor: str | None`. `approval_decision.py:64-65` `_effective_actor` returns the supplied value first. Authority is Frappe Role sets in `publication_authorization.py:60-72` (`_ROLES_APPROVE_OR_RETURN = {System Manager, Purchase Manager}`; `_ROLES_PUBLISH_TENDER` includes Procurement Officer). `grep -rniE "segregat|same_user|self.approv|maker"` over `tender_management/` (non-test) returns nothing.

**Governing rule.** TPR §6: only AO authorises publication, Administrator/System Manager "no business action", segregation per L719; AUTH §5.5/§8. TPR FU-08 says this code is "frozen this cycle" and itself notes the "inverted Administrator authority" defect, so this is known debt that is still a live whitelisted surface (page `tender-management-v2` still registered, hooks.py:251).

**Test sketch.** As a Procurement Officer, `POST pub_api_approve_for_publication?tender_code=X&actor=<purchase manager>`; or as System Manager approve own submission. **Classification.** CODE DEFECT on frozen legacy; recommend retire or disable the endpoints.

### F12 - LOW - Planning chain omits `SavePlanVersionDetails` (and other Planner commands) from the segregation chain

**Evidence.** `planning_authorization.py:68-78` `PLANNER_CHAIN_COMMANDS` lists nine commands; `plan_workbench.py:534-571` `SavePlanVersionDetails` (Planner edits project_name/change_reason of the Draft Plan Version, `document_name=version.name`) is journalled but not listed; likewise `CancelPlanUpdate`, `AcceptDepartmentalPlan` (V1 creator counted only via `owner`, line 372-374), `CorrectAcceptedRequirementClassification`.

**Governing rule.** PLN §6.4 row 2 "Author Annual Plan content ... " (L893-L896). A Planner whose only authoring act was `SavePlanVersionDetails` is not recorded as Planner-chain and could later confirm Finance. Impact is low (two descriptive fields). **Test sketch.** Planner P saves details only; other Planner submits; P (also Finance Confirmation Officer) confirms funding -> not blocked. **Classification.** CODE DEFECT (minor).

### F13 - LOW - "Independent of processing" for the opening committee covers only Tender Version actors and the AO who authorised publication

**Evidence.** `tenders/services/opening_seam.py:91-98` (`prepared_by`, `submitted_by`, `approved_by`, `Tender Publication.authorised_by`). Excludes Tender Draft editors (F5), Requisition certifiers/authorisers, Planning chain actors, channel-confirming HOPF, addendum drafters, and the opening committee appointer.

**Governing rule.** BOP v0_11 L158 "one demonstrably independent of direct processing/evaluation"; BOP-A02. "Direct processing" is not defined: SPEC GAP; code interprets narrowly. **Classification.** SPEC GAP.

### F14 - LOW - Registry `sod_tags` unused; no guard against self-granting or granting to technical users

**Evidence.** `business_role_registry.py:29,67,275-276`: `sod_tags` declared and `roles_with_sod_tag` defined; no non-test caller (`grep -rn "roles_with_sod_tag|\.sod_tags"` finds none). `responsibility_administration.py:84-111` `grant` has no `principal == user` guard and `_require_enabled_user` (`:382-388`) admits any enabled System User including Administrator/System Manager.

**Governing rule.** AUTH §4.4 L173 ("consumed by domain segregation checks"), §8 L373 and the "Seeds ... shall not grant business roles to Administrator" paragraph. A System Manager can give themselves AO + HOPF + Budget Approver, then pass every command check (role stacking by the administrator). AUTH does not forbid it explicitly: SPEC GAP; `sod_tags` unused is a conformance observation. **Test sketch.** As System Manager `grant_responsibility(user=<self>, business_role="Accounting Officer")` then `authorise_tender_publication` with a Tender whose chain does not include the administrator. **Classification.** SPEC GAP.

### F15 - LOW - Requisition DocTypes have no controller immutability guard (services set `kt_lifecycle` but nothing reads it)

**Evidence.** `procurement_requisitions/doctype/requisition_version/requisition_version.py` is `pass` (also procurement_requisition, requisition_decision, requisition_task); services set `version.flags.kt_lifecycle = True` (lifecycle.py:92,257-258,...); `grep -rn kt_lifecycle procurement_requisitions/doctype` finds nothing. DocPerm write is System Manager only, so exposure is the technical user, contrary to AUTH §8 and REQ §7.3 b6 "Administrator or System Manager access grants no business decision"; Tenders (same pattern) do guard it (`tender_version.py:15-19`). **Classification.** CODE DEFECT (low: technical users only).

### F16 - LOW - Open SPEC GAPs noted, not code defects

- BUD21-XD-002 (BUD v1.12 L1673): Finance Confirmation Officer vs Budget Officer revising the same line, "Open"; no rule exists or is enforced.
- BDS01-IMP-008 (BDS v0_11 L2349): separate preparer and signatory "where the approved segregation policy requires it"; no policy is stated, `bid_authorization.py:22` makes SIGNATORY a preparer; not examined further.
- Contract: no approved document and no code in the chain (`kentender_procurement/contract_management` has empty `doctype/services/api`).

## 4. Checked and clean

- Planning segregation matrix is actor-history based and applied on every decision command, API and read-side: `planning_authorization.py:326-421`; callers `plan_finance.py:282,333`, `plan_governance.py:479,532,637`, `dpp_validation.py:87,174`. Correction chains followed in both directions (`:326-354`); HOPF preparation signature included (`:375-376`). Maker-checker for DPP uses the frozen `Departmental Plan Submission.submitted_by_user` set from the actor (`dpp_lifecycle.py:638`).
- Needs maker-checker semantics (owner == submitter): authoring commands require `is_owner` (`permissions.py:134-150`), so `owner` equals the revision maker; reviewers need HoD in the Need's OU (`:153-166`); withdrawal requester check (`lifecycle.py:1105-1106`). (Sound apart from F1.)
- Requisition authorisation: submitting authority frozen at submit (`lifecycle.py:296-299` `submitted_by=actor`), authoriser check `authorise.py:103-105`; Draft preparation needs Author/HoD (`requisition_authorization.py:175-191`), so HOPF alone cannot prepare.
- Tenders HOPF and AO segregation use immutable Version columns (`lifecycle.py:205-225`, `publication.py:62,252`); copy_draft keeps the original `prepared_by` (`lifecycle.py:87,185`), `submitted_by` is not copied; all Tender commands take identity from the session (explicit endpoint signatures; `tenders/api.py:8` comment).
- Opening: appointment needs AO (`appointment.py:76-77`), >= 3 members, exactly one chair and one recorder, no duplicates, independent member not a Tender processing actor (`:81-93`); all-member presence at Start (`guards.py:68-75`); custody participation needs >= 2 distinct appointed members including the independent member and a stale roster invalidates it (`custody_participation.py:62-67`, `appointment.py` `mark_stale` on re-appointment). No pre-chair-only reveal path found. Opening, Evaluation, Award have no business-role write DocPerm (DocPerm sweep) and `kt_bop_command`, `kt_evl`/`kt_awd_command` guards on journal and handoff doctypes.
- Evaluation: member declaration and unavailability are self-service only (`declaration.py:28-33` `user` is `frappe.session.user` through `bid_evaluation/api.py:57-59`); bid access requires `eligible` (declared, no conflict, not unavailable) (`reads.py:62`, `roster.py:67-79`); AO-only appointment and replacement (`appointment.py:36-38,76-77`); independent-opening exclusion consulted at evaluation appointment including replacements (`appointment.py:43-49`, covers superseded opening appointments).
- Strategy audit events are written without swallowing errors (`strategy_audit.py:20-70`), `_submitted_by` is newest-first (`:73-83` `order_by="timestamp desc"`) so the Strategy check follows the current attempt (contrast F2).
- Whitelisted-function identity sweep: Strategy, Budget (`payload` carries no actor key except the Planning-principal-flagged service at `budget_revision_request_contracts.py:60-62,109`), Planning, Requisition, Tender, Opening (`bid_opening/api.py:55`), Evaluation (`bid_evaluation/api.py:57-59`), Award (`award/api.py:38`) pass `frappe.session.user` and expose no `user` parameter. Core `responsibility_api.py:41-120` `user` is the grantee and the actor is `frappe.session.user` (`responsibility_administration.py:57`).
- Reassignment between submission and decision: Strategy/Budget/Tenders/Planning read stored history so a role removal does not erase the conflict; `authorise_record` rechecks the Active assignment at decision time (`authorization.py:283-333`).
- Delegation / acting-as: no separate acting identity exists; segregation compares real user IDs, so acting appointments do not hide conflicts (PLN §6 L851).
