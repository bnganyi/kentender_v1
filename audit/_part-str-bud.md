# Part str-bud — Strategy Alignment and Budget & Funding (Phase 3 findings)

Oracles: STR-CHG-001 v1.9 (`docs/mvp-1-r1/02_strategy/KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1_9.md`, Approved 3 Oct 2026), BUD-CHG-001 v1.12 (`docs/mvp-1-r1/03_budget/KenTender_BUD-CHG-001_Clean_Budget_and_Funding_v1_12.md`, Approved 3 Oct 2026), AUTH-ADR-001 v1.9. All findings are from static reading; nothing was run ("static; not run"). Every cited line was re-opened in this pass. Path shorthand: `STR/` = `kentender_strategy/kentender_strategy/`, `BUD/` = `kentender_budget/kentender_budget/`, `PROC/` = `kentender_procurement/kentender_procurement/` (all under the repo root `/home/midasuser/frappe-bench/apps/kentender_v1/`).

| ID | Severity | Title |
|---|---|---|
| AUD-STR-001 | High | `save_strategy_structure_draft` deletes any record of any DocType (permissions bypassed) |
| AUD-STR-002 | High | Structure change set accepts record names from other versions: Active content can be deleted or moved |
| AUD-STR-003 | High | `save_strategy_plan_draft` edits any version and any plan identity regardless of status |
| AUD-STR-004 | High | Open-ended (null `effective_to`) version never resolves and escapes the overlap guard |
| AUD-STR-005 | Medium | Strategy consumer endpoints open to every signed-in account; lineage ignores version status |
| AUD-STR-006 | Medium | "Author cannot approve" is implemented as "submitter cannot approve" |
| AUD-STR-007 | Medium | §13 audit obligations for downstream contract calls and snapshots are not met |
| AUD-STR-008 | Medium | Generated Strategy identifiers can be supplied by the caller and are not unique |
| AUD-STR-009 | Medium | Snapshot and lineage payloads carry Frappe docnames, not the generated references, and omit §8 fields |
| AUD-STR-010 | Medium | Planning and Requisitions read Strategy tables directly; objective reference column does not exist |
| AUD-STR-011 | Medium | Approval does not refuse expired applicability |
| AUD-STR-012 | Low | Submitter blocked from Return, contrary to §12.4 |
| AUD-STR-013 | Low | `effective_to` not bounded by the plan period on the server |
| AUD-STR-014 | Low | Plan type cannot be changed in the first Draft although §11.3A shows the control |
| AUD-STR-015 | Low | Existence of a plan is distinguishable from refusal |
| AUD-STR-016 | Low | Hierarchy and target validation raise untyped errors where §9 requires typed codes |
| AUD-STR-017 | Low | §9 error vocabulary contradicts the AUTH-ADR-001 §10 closed vocabulary Strategy is bound to |
| AUD-STR-018 | Low | Predecessor closure can lengthen the predecessor's applicability |
| AUD-STR-019 | Low | Seed plan title lacks "(Demo)"; §14.3 identifiers cannot be produced under STR-BR-016 |
| AUD-STR-020 | Low | Extra `fixture_namespace` field on every Strategy DocType |
| AUD-STR-021 | Low | Workspace shortcut still labelled "Strategy Portfolio" |
| AUD-BUD-001 | High | Owner-scope and source-OU eligibility not enforced where money moves |
| AUD-BUD-002 | High | Return/resubmit keeps no immutable submission-attempt snapshot |
| AUD-BUD-003 | Medium | A Closed Budget can be re-activated by an already-open successor |
| AUD-BUD-004 | Medium | `Procurement Commitment.contract` is unique table-wide |
| AUD-BUD-005 | Medium | `check_funding` writes a ledger-table event on every call |
| AUD-BUD-006 | Medium | `save_budget_lines_draft` is not one validated change set |
| AUD-BUD-007 | Medium | Editor lost-on-save race and line-scope stamp that never changes |
| AUD-BUD-008 | Medium | Approval document removed from the evidence gate against approved BUD-BR-004 |
| AUD-BUD-009 | Medium | No historical funding position, no CurrencyBasis, no `get_budget_currency_contract` |
| AUD-BUD-010 | Medium | Disabled or inactive Organisation Unit / Funding Source never rechecked on line save or approval |
| AUD-BUD-011 | Medium | Procurement lifecycle and Requisitions read Budget tables directly; Budget reads Planning tables |
| AUD-BUD-012 | Medium | SPEC GAP: how an in-process caller proves it is the REQ / Contract Management service principal |
| AUD-BUD-013 | Low | Check token not bound to actor or Budget revisions |
| AUD-BUD-014 | Low | Mixed release/convert hold ends as `Released`; Close blocked for the version's submitter |
| AUD-BUD-015 | Low | Seed diverges from §15.3/§15.5/§15.6 (generated line references, BUD-SC-FIN-* names, relative dates) |
| AUD-BUD-016 | Low | SPEC DEFECT: canonical route `/app/budget` cannot be served (collides with ERPNext Budget) |
| AUD-BUD-017 | Low | SPEC DEFECT: BUD-BR-027 "no ledger event" vs §14 request events in the same ledger |

## Strategy

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

## Budget & Funding

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

## Dropped / downgraded

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

## Calibration notes

**Strategy — approved-only universal read (owner ruling 5 Oct 2026): present for the Vue read APIs, absent at the consumer endpoints and at DocType level.**
- Present: `STR/services/strategy_authorization.py:252-259` `holds_internal_read` (enabled `System User`), `:262-267` `read_scope` returns `"full"` for technical/Auditor/Author/Approver and `"approved"` for every other internal user and for AO/HOPF/HoD; applied in `STR/services/strategy_ui_contracts.py:72-80` (`_version_readable`), `:340-343` (portfolio), `:476-481` (tree), `:694-717` (workspace), `:873-876` (history); approved-only filter at `:714-717`. Pinned by `STR/tests/test_ovs_strategy_reads.py:128` (internal user reads approved, not pending), `:148` (Website User refused), `:155` (disabled user refused), `:123` (task and comparison closed).
- Absent: the five consumer endpoints are not gated (AUD-STR-005); Strategy DocTypes register no `has_permission` / `permission_query_conditions` / `kentender_scope_map` (`STR/hooks.py`, whole file) although STR §16.1 requires it, so the ruling is enforced only inside the Vue APIs (reading by Desk list/form is denied by DocPerm, which is restrictive, not a leak). This registration gap sits with xc-authz item 4 and is not a separate finding here.

**Strategy — approved Active/Submitted/Superseded version immutability: present on the intended route, bypassable.**
- Present: structure edits on a non-Draft version are rejected (`STR/services/strategy_domain_guards.py:194-199,206,243,275`, test `STR/tests/test_str_chg_001_phase4_contracts.py:480`); identity fields locked (`:125-129`); successor route (`STR/services/strategy_writes.py:121-243`).
- Bypass: AUD-STR-002 (cross-version names), AUD-STR-003 (`save_strategy_plan_draft` on an Active id), and DocType-level writes (xc-authz item 4).

**Strategy — strategic_objective producer contract: stable, with identity gaps.**
- Producer: `list_strategy_objectives` returns `id` (docname), `reference` (`strategy_node_id`), `title`, ancestor path (`STR/services/strategy_consumer.py:210-221`); `resolve_strategy_context` supplies the version (`:76-173`); `create_strategy_snapshot` freezes lineage (`:275-336`). Planning stores the docname in `Annual Plan Item.strategic_objective` (Link to Strategy Node) via `PROC/procurement_planning/services/strategy_gateway.py` and consumes `create_strategy_snapshot` directly in-process (`strategy_gateway.py:71-73`, not through the whitelisted idempotent wrapper). Gaps: AUD-STR-004 (open-ended version never resolves), AUD-STR-009 (docnames and missing fields), AUD-STR-010 (direct reads, non-existent reference column).

**Budget — reservation denominator: fixed.** No `get_annual_procurement_budget_basis` / `AnnualProcurementBudgetBasis` in any `*.py`, `*.js`, `*.vue`, `*.json` under `kentender_*` (only the test `BUD/tests/test_bud_chg_001_v18_decision_basis.py` asserts its absence, `:32-43`); Budget publishes only ceiling/affordability evidence (`BUD/services/budget_line_contracts.py:545` comment). Planning computes the denominator from the current plan Version's eligible value: `PROC/procurement_planning/services/readiness.py:250-264` ("never the approved annual budget ... no Budget contract is read here"). Small gap: the absence test inspects only `budget_line_contracts` and `budget_api`, not `budget_contracts` or `budget_downstream_contracts`.

**Budget — revision request successor guard (at most one open successor): present only by an incidental guard.** `BUD/services/budget_contracts.py:1092-1125` (`create_budget_successor_version`) does `_draft_version(doc.name)` then creates (check-then-insert, no lock). The only concurrent guard is the unique `generated_reference` `{budget_reference}-V{n}` (`procurement_budget_version.json:45-54`, `allocate_budget_version_reference` `budget_reference.py:110-114`, `n = based_on.version_number + 1` at `budget_contracts.py:1028-1033`), which makes the second concurrent insert fail with a raw duplicate-entry error instead of the typed `BUDGET_INVALID_STATE`. Sequentially pinned by `test_duplicate_successor_returns_the_existing_route`. Not raised as a finding: the document's rule holds; only the error type under a race differs (static; not run).

**Budget — lost-on-save race: partially fixed, defect remains (AUD-BUD-007).** Fixed: the post-save reload is awaited inside the guarded runner (`BudgetVersionEditorScreen.vue:343-351`), re-hydration is guarded on `modified`/`status` and dirtiness (`:159-162`), `loadLines` does not clobber dirty rows (`:183`), the server returns typed `BUDGET_STALE_WRITE` for a stale details save (`budget_contracts.py:982-989`). Not fixed: the dirty signature is taken at response time (`:309`), rows are replaced after the response (`:335-337`), the token is optional (xc-core item 11) and line saves never advance the stamp (`budget_line_contracts.py:92-93,225`).
