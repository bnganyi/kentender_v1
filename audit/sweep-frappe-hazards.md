# Sweep: frappe-hazards (Phase 2 cross-cutting, READ-ONLY)

Scope: production code of all `kentender_*` apps (tests excluded), four hazard classes: (1) SQL, (2) background jobs and transaction control, (3) patches, (4) fixtures / seeds / hooks / whitelisted-method transport fields.
Static reading only. No bench command, DB access or site access was used. Python `ast` was used only to parse source text.

## 1. Method (reproducible)

Working directory `/home/midasuser/frappe-bench/apps/kentender_v1`. File universe (1,955 production `.py` files, tests excluded):

```
find kentender_* -name "*.py" | grep -vE "/tests?/|/test_[^/]*\.py$|_test\.py$|__pycache__|node_modules"   # -> fh_files.txt
```

| Step | Command / pattern |
|---|---|
| SQL call sites | `grep -nE "frappe\.db\.(sql\|sql_list\|multisql)\(" <files>` (237 hits); then read every multi-line call (`sed -n "L,L+14p"`), classed by string-building style |
| f-string / format / % / concat in SQL | `grep -nE 'f"\|f'"'"'\|\.format\(\| % \|\+ '` over the 237 hits; plus `grep -rnE 'sql\(.*\.format\(\|\.sql\(.*\+ '` |
| LIKE | `grep -nE '"like"\|\bLIKE\b\|like %s' <files>` |
| Raw write SQL in services | `grep -nEi 'sql.*(update\|delete from\|insert into) *.?tab'` excluding patches/seeds/tests; `grep "frappe.db.delete("` excluding patches/seeds/tests/setup |
| Whitelisted functions | AST scan of every `FunctionDef` whose decorator text contains `whitelist` (script `fh_wl_ast.py`): captures `**kwargs`, `allow_guest`, `methods=`, argument names. Separately `grep -nE "whitelist\([^)]*\)\("` for the `frappe.whitelist()(fn)` call form (AST decorator scan misses it) |
| Client-controlled parameters | filtered the AST arg-name list for `user\|actor\|as_user\|owner\|email\|filters\|fields\|order_by\|doctype\|query\|limit` |
| Transaction control | `grep -nE "db\.commit\(\|db\.rollback\(\|\.savepoint\|db\.begin"` (303 hits outside patches) |
| Background jobs | `grep -rn "enqueue" --include=*.py` (no `frappe.enqueue` / `enqueue_doc` call exists in any production file; only comments); read every `scheduler_events` in all 11 `hooks.py` |
| Swallowed exceptions | AST scan of every `except Exception/BaseException/bare` (script `fh_swallow.py`): 253 handlers, 138 with no `log_error` / `logger` / `raise` / `rollback` / `throw` in body; all non-patch, non-seed, non-legacy ones read |
| Patches | `patches.txt` of the 11 apps vs. `patches/` files (script comparing both directions); read every patch body that deletes, drops, alters, calls `has_column`/`get_table_columns`/`get_all`/`get_doc`, or imports live service/seed code; checked Frappe sources (`database.py:1348-1357`, `mariadb/database.py:438-453`, `model/delete_doc.py`, `scheduled_job_type.py:143-161`) for framework behaviour |
| Hooks | `grep` of every `fixtures`, `after_install`, `after_migrate`, `boot_session`, `doc_events`, `scheduler_events`, `override_whitelisted_methods`, `before_request` entry in the 11 `hooks.py`; script `fh_hooks_paths.py` resolved every dotted string `kentender_*.x.y` in hooks (non-comment lines) to a file and an `ast`-confirmed `def/class/assign/import` |

Docs read (latest versions confirmed with `ls | sort -V`): AGENTS.md §4.3; NDS-CHG-001 v1_16 §8.2, NDS-BR-006; BUD-CHG-001 v1_12 §14 (audit) and BUD-BR-025; PLN-CHG-001 v1_29 lines 454, 989 (publication worker); AUTH-ADR-001 v1_11 line 829 ("Timestamps and actors are system-generated. A client cannot supply or amend them").

## 2. Coverage

| Population | Count | How classified |
|---|---|---|
| Production `.py` files in scope | 1,955 | all grepped |
| `frappe.db.sql*` call sites | 237 (+ `sql_ddl`) | 12 f-string sites (all interpolate a code constant/doctype name or a `%s` placeholder list, never request data), 1 f-string `WHERE` assembled from fixed fragments (journey_api.py:169), 0 `%`-interpolation, 0 `.format`, 0 `+`; `FOR UPDATE` lock-reads ~60; all multi-line calls read |
| LIKE uses fed by a client string | 6 (journey_api.py:153-156, responsibility_api.py:193, technical_search.py:96-98, publication_setup.py:216-218, budget_line_contracts.py:385, strategy_consumer.py:200) | all parameterised; wildcards `%`/`_` in the search text are not escaped (F-15) |
| Raw `UPDATE/DELETE` on business tables outside patches/seeds | 0 | only `tabSeries` counters (budget_reference.py:76, strategy_reference.py:120; canonical-seed use only) and `frappe.db.delete` by fixture namespace (award/records.py:182) / by tender (security_matching.py:88) |
| Whitelisted functions | 648 decorated + 20 `frappe.whitelist()(fn)` wrappers = 668 | 4 decorated declare `**kwargs` (all in departmental_needs/api.py, all strip transport fields); 0 of the 20 wrappers has `**kwargs`; 485 decorated carry no `methods=`; 5 `allow_guest=True` (bid_submission/api.py:42,48,59; bid_opening/api.py:312; smw_public.py:24) |
| Whitelisted functions with a client-settable acting identity (`user` / `actor`) | 20 (NDS wrappers) + 9 (`pub_api_*` 7, `sec_api_action_availability` 2) + 1 (`sec_api_evidence_export_availability`, ignores it) | F-1, F-2, F-4 |
| `scheduler_events` entries | 18 registered jobs (core: 1 cron + 3 hourly + 1 daily; budget: 1 hourly; procurement: 1 hourly + 7 `all`), plus 0 `frappe.enqueue` | every dotted path resolves; per-job isolation reviewed (F-11) |
| `hooks.py` dotted paths | 166 (non-comment) | 166 resolve to an existing def/class/assignment; 0 missing; 0 `override_whitelisted_methods`; 0 `before_request` |
| `doc_events` handlers | 12 doctype entries (core 9 authorization records, procurement 2, suppliers 1) | 1 swallows errors by design (F-13) |
| `patches.txt` entries vs files | 128 listed (budget 7, core 18, procurement 85, strategy 11, suppliers 7; assets/compliance/governance/integrations/stores/transparency 0) = 128 files | 0 listed-but-missing, 0 unlisted file, 0 duplicate entry, all define `execute` |
| Patches that delete/drop business data | 17 | F-6, F-7 |
| Patches calling `has_column`/`get_table_columns` unguarded on a table dropped by another patch | 4 | F-8 |
| `db.commit()`/`rollback()` in services/api/setup (excl. patches) | 303 occurrences | savepoint-based `atomic()`/envelope wrappers (Tenders, Requisitions, Planning, Award, Evaluation, Opening, Proceedings, BDS) = clean; scheduler per-item commit/rollback = clean (F-11 lists exceptions); mid-command commits in `tender_configurations/*` and `std_templates/*` = F-9 |
| Swallowed `except Exception` without log/raise | 138 | ~110 are parse/format fallbacks (`return ""`, `return None` on bad date/JSON) = acceptable; the rest reviewed individually (F-10, F-12, F-13, F-16, Checked-and-clean) |

## 3. Calibration status (known past defects in this sweep's domain)

| Past defect | Status in current code |
|---|---|
| `**kwargs` whitelisted methods receive `cmd`/`csrf_token`/`_` | FIXED for the four endpoints: `_TRANSPORT_FIELDS = frozenset({"cmd","csrf_token","_"})` and `_command_args()` at kentender_procurement/kentender_procurement/departmental_needs/api.py:70-74; applied at :80, :115, :121, :127. No other whitelisted function in any app declares `**kwargs`. BUT the same `**kwargs` pass-through still forwards `user` and any unknown field (F-1, F-14). |
| Dropping a doctype/table makes sibling `frappe.db.exists`/`has_column` calls crash | STILL PRESENT in four patches (F-8) plus dead legacy code (Checked-and-clean list). Frappe fact: `has_column` -> `get_table_columns` raises `TableMissingError` when the table is absent (`frappe/database/database.py:1348-1357`); `db.exists("DocType", x)` is safe, `db.exists(x, name)` is not. Patches `v1_0/backfill_pe_fy_context_links.py:33-36` and `pln_revision_preflight.py` guard correctly and show the right pattern. |
| Other calibration items (intake scope, Handoff v1.4 names, AGPO denominator, 7-day floor, late-need dead end, digest, post-save race, Strategy readable) | Not in this sweep's static domain, except the late-need dead end whose compensating mechanism can still be silently skipped (F-13). |

## 4. Candidate findings (most severe first)

Severity counts: Critical 2, High 4, Medium 6, Low 7 (19 findings).

---

### F-1 CRITICAL — Departmental Needs endpoints accept a client-supplied `user` and treat it as the acting principal (impersonation, maker-checker bypass)

Evidence
- kentender_procurement/kentender_procurement/departmental_needs/api.py:45-54, :58, :92-103 wrap service functions whose signatures contain `user: str | None = None`: `lifecycle.submit_need` (lifecycle.py:643-645 `*, need, expected_version, idempotency_key, user: str | None = None`), `lifecycle.review_need` (:703-713), `withdraw_need`, `request_withdrawal`, `decide_withdrawal`, `create_accepted_need_successor`, `cancel_accepted_need_successor`, `get_workspace`, `get_need`, `get_review_task`, `get_current_accepted_need`, `resolve_creation_context`, `project_planning_usage/disposition/intake`.
- The `**kwargs` endpoints forward every non-transport field: api.py:73-74 `{key: value ... if key not in _TRANSPORT_FIELDS}`, :87 `lifecycle.update_need(need=need, **args)`, :89 `lifecycle.create_need(**args)`, :115/:121/:127 `lifecycle.review_need(decision=..., **_command_args(kwargs))`.
- Every service resolves identity from that argument: services/permissions.py:59-66 `def actor(user=None): value = cstr(user or frappe.session.user).strip()`; used as `principal = actor(user)` at lifecycle.py:535, 602, 652, 725, 838, 882, 934, 1014, 1092; workspace.py:234, 380, 481, 535, 644; context.py:147, 179; usage.py:136, 176, 414, 452. `project_planning_usage` (usage.py:176-184) grants Planner authority to `principal`.
- Frappe filters a request to the callee's declared parameters with `frappe.get_newargs` (`frappe/__init__.py:1150-1172`); keyword-only parameters named `user` are declared parameters, so a request field `user=` is delivered. No `before_request`/`form_dict` stripping hook exists (grepped).

Governing rule: AGENTS.md §4.3 ("enforce required role and organizational scope ... audit actor ... re-check permissions inside whitelisted methods"); NDS-CHG-001 v1_16 NDS-BR-006 ("The actor who submitted the revision cannot decide that revision. Maker-checker is rechecked on the server") and §8.2 (inputs of each command contain no identity); AUTH-ADR-001 v1_11 line 829 (actors are system-generated, a client cannot supply them).

Reproduction
1. Log in as any authenticated user U with no Needs responsibility (e.g. a Website/supplier user).
2. `POST /api/method/kentender_procurement.departmental_needs.api.accept_need_revision` with form fields `need=NDS-...&task=...&decision_token=...&expected_version=N&idempotency_key=k&user=<email of a Head of User Department who is not the submitter>`. `_command_args` leaves `user`; `review_need(decision="accept", ..., user=<HoD>)` computes `principal = <HoD>` and runs all scope and maker-checker checks as that person. The Need is accepted.
3. `POST .../submit_need_revision?need=..&expected_version=..&idempotency_key=..&user=<author>` submits as the author. `GET .../resolve_needs_scope?user=<any>` and `.../get_needs_workspace?user=<any>` disclose another user's scope and Needs.
4. `POST .../project_need_planning_usage` with `user=<a Procurement Planner>` writes Planning projections without holding the role.
Failing-test sketch: `frappe.set_user(unprivileged); frappe.call("kentender_procurement.departmental_needs.api.get_needs_workspace", user=planner)` returns data instead of NDS_SCOPE_DENIED.

Classification: CODE DEFECT.

---

### F-2 CRITICAL — Publication API (`pub_api_*`) trusts a client-supplied `actor`; `actor=Administrator` bypasses every role check

Evidence
- kentender_procurement/kentender_procurement/tender_management/tender_publication/api/handlers.py:192-193 `pub_api_run_publication_readiness(tender_code, actor=None)`, :222 `pub_api_submit_for_approval`, :237 `pub_api_get_approval_review_package`, :252-255 `pub_api_approve_for_publication`, :272-275 `pub_api_return_for_correction`, :292-295 `pub_api_reject_publication`, :312 `pub_api_publish_tender` — all `@frappe.whitelist()` (no `methods=`), all pass `actor` straight to the service.
- approval/approval_decision.py:64-65 `return _strip(actor) or _strip(frappe.session.user) or "Administrator"`; :68-73 `_assert_actor_can_decide(act)`; authorization/publication_authorization.py:88-89 same `_effective_actor`, :130-143 `_assert_any_role`: `if actor == "Administrator": return` otherwise `_user_roles(actor)`. Decision records `decided_by = actor` (approval_decision.py:220).
- Contrast: security/api.py:149-160 `sec_api_evidence_export_availability` ignores `actor` ("session actor is mandatory for SEC-0900 API checks") and the workbench API (api/tm2_workbench.py:141, 177, 192, 218, 306) always uses `frappe.session.user`. The TM2 doctypes still ship (23 `tm2_*` doctype directories) and the handlers are importable whitelisted paths.

Governing rule: AGENTS.md §4.3; AUTH-ADR-001 v1_11 line 829.

Reproduction: as any logged-in user, `POST /api/method/kentender_procurement.tender_management.tender_publication.api.handlers.pub_api_publish_tender` with `tender_code=<TM2 tender>&actor=Administrator` -> `PublicationAuthorizationService.assertCanPublishTender("Administrator")` returns immediately; the tender is published and the audit/decision rows name Administrator. Same for `pub_api_approve_for_publication` (approval by any user, forged `decided_by`).
Severity note: Critical if the TM2 tables exist on the target site (the doctypes ship in the app); if the TM2 module is intended to be dead code, the endpoints should still be removed.

Classification: CODE DEFECT.

---

### F-3 HIGH — Audit-event read endpoints have no authorisation and bypass permissions

Evidence: kentender_procurement/kentender_procurement/tender_management/security/api.py:112-130 `sec_api_audit_events(object_type, object_code, filters)` and :132-143 `sec_api_audit_tender_events(tender_code, filters)`: `@frappe.whitelist()`, no role check; they call `AuditEventService.get_audit_events_for_object` / `get_audit_events_for_tender` (security/audit/event_service.py:72-103, 106-146) which run `frappe.get_all("Audit Event", filters={"document_type": ot, "document_name": oc}, fields=[... "performed_by","metadata"])` (get_all ignores permissions) with attacker-chosen `document_type`/`document_name`.
Governing rule: AGENTS.md §4.3 ("Return only data the caller is allowed to see"); AUTH-ADR-001 v1_11 (Auditor/technical read is a registered responsibility).
Reproduction: any logged-in user: `GET /api/method/kentender_procurement.tender_management.security.api.sec_api_audit_events?object_type=Tender&object_code=<any>` returns actors, timestamps and `metadata` JSON of any audited object.
Same module, lower impact: security/action_availability/api.py:154-158 `_resolve_actor` accepts `actor` (:167, :187) and returns action availability for any named user (information disclosure about other users' authority).
Classification: CODE DEFECT.

---

### F-4 HIGH/MEDIUM — Supplier registry workbench reads are open to every authenticated user (permission-bypassing `get_all`/`get_doc`)

Evidence: kentender_suppliers/kentender_suppliers/api/ktsm_landing.py:24-83 `get_landing`, :153-226 `get_suppliers`, :304-422 `get_supplier_detail` — `@frappe.whitelist()` with no call to `_assert_registry_access()` (defined :258; only the builder endpoints at :461, :492, :552 call it). They read `frappe.get_all("KTSM Supplier Profile"...)`, `frappe.get_doc("KTSM Supplier Profile", ...)`, `frappe.get_all("KTSM Supplier Document", ...)` (permissions ignored). `perform_action` (:424) relies on per-action checks in smw_workflow.py, but the three reads do not.
Governing rule: AGENTS.md §4.3.
Reproduction: log in as a supplier portal user; `GET /api/method/kentender_suppliers.api.ktsm_landing.get_suppliers` lists every supplier profile with approval/compliance/risk status; `get_supplier_detail?supplier_code=SUP-KE-2026-0001` returns documents, verification state and `verified_by`.
Classification: CODE DEFECT (authz/org-scope overlap; reported here because the cause is `get_all`/`get_doc` bypassing Frappe permissions without a replacement check).

---

### F-5 HIGH — Approved Annual Plan is never dispatched for publication: no enqueue, no scheduler job consumes `Publication Intent`

Evidence
- plan_governance.py:520-521 docstring "publication is enqueued, never sent synchronously"; :554-556 `publication_pipeline.commit_approved_plan(...)` only writes `Approved Plan Snapshot`, `Plan Publication` and `Publication Intent` (publication_pipeline.py:10-14: "`publish_annual_plan`, a system worker that would run post-commit via `frappe.enqueue` in production; this bench runs no RQ worker, so callers (tests, seeds) invoke it inline").
- There is no `frappe.enqueue`/`enqueue_doc` anywhere in production code (grep), and kentender_procurement/hooks.py:481-505 and the other apps' `scheduler_events` list no job that drains `Publication Intent` rows in state `Committed` or calls `publish_annual_plan`. The only production callers are the technical-user-only whitelisted wrapper (procurement_planning/api.py:420-432, `is_technical` gate) and seeds/tests (grep: seeds/profiles.py:329, kentender_mvp_v1.py:862, playwright fixtures).
Governing rule: PLN-CHG-001 v1_29 line 454 ("Record approval and Strategy snapshot; enqueue publication of exact approved content") and line 989 ("PublishAnnualPlan — system worker | Post-commit only ... record attempt").
Reproduction: on a site with workers/scheduler running, approve an Annual Plan Version (ApproveAnnualPlan) -> status "Approved — publication pending", `Publication Intent.dispatch_state = Committed`; wait any number of scheduler ticks: nothing transmits, the Version never becomes Active; only an operator calling `publish_annual_plan` as System Manager moves it.
Classification: CODE DEFECT against the approved spec (the code states the omission is a bench limitation; the spec makes the worker mandatory).

---

### F-6 HIGH — A post-model-sync patch deletes the DocType records of two doctypes that the current JSON still ships, then the next patch wipes the table

Evidence: kentender_strategy/kentender_strategy/patches/mvp1_teardown_drop_legacy_strategy_doctypes.py:12-20 `LEGACY_DOCTYPES = [..., "Strategy Node", ..., "Strategic Plan"]`, :56-58 `frappe.delete_doc("DocType", name, force=1, ...)`; both doctypes are current (`kentender_strategy/kentender_strategy/doctype/strategic_plan/strategic_plan.json`, `strategy_node/strategy_node.json`). Listed first in `[post_model_sync]` (patches.txt, after the section header), i.e. after model sync created them. Next entries: `str_chg_001_phase1_domain_model_rebuild.py:36-37` `if frappe.db.table_exists("Strategic Plan"): frappe.db.sql("DELETE FROM `tabStrategic Plan`")` (the table survives the DocType delete: `delete_doc` leaves the table, see the patch authors' own comment in pln_chg_001_v12_drop_legacy_planning_doctypes.py "delete_doc does not reliably drop the backing table").
Governing rule: patch idempotency / safe on sites that have not run it (task scope); AGENTS.md §3 (no destructive operations outside the task's scope); STR-CHG-001 §1.1 authorises disposal only "dev site; no production data exists" (the patch's own docstring).
Reproduction (any site whose Patch Log lacks these two entries — a restored older backup, a rebuilt droplet from an earlier dump): `bench --site X migrate` -> model sync creates Strategic Plan/Strategy Node, patch 1 deletes both DocType rows (Strategy pages then fail until the next migrate re-syncs), patch 2 empties `tabStrategic Plan`. On the dev site both are already logged, so no effect is visible there.
Classification: CODE DEFECT (patch deletes current schema and data with no environment/data guard; contrast nds_chg_001_v11_drop_retired_need_doctypes.py:57-72 which refuses to run on non-seed rows).

---

### F-7 MEDIUM — One-shot destructive data patches have no environment/non-empty guard

Patches that delete or truncate business rows or drop whole tables on first migrate of any site: `tpr_chg_001_v08_retire_tender_preparation.py:52-72` (drops nine Tender Preparation doctypes and tables, "no data migration"); `bds_chg_001_v08_retire_bid_slice.py:34-47` (`DELETE FROM` Electronic Bid Submission / IT Bid Opening Record / Electronic Bid Audit Event, unconditional); `tpr_fu25_retire_candidate_stand_in.py:19-22` (`frappe.db.delete("Tender Candidate Registration")`); `p6_clear_procurement_tender_dev.py:53-63` (`delete from tabProcurement Tender`); `str_chg_001_phase1_domain_model_rebuild.py:36-37` (F-6); `c02_drop_departmental_submission.py:15-19`; `pln_chg_001_v12_drop_legacy_planning_doctypes.py:34-50` (nine planning doctypes dropped with rows); `nds_chg_001_v11_drop_retired_need_doctypes.py:42-43` (`frappe.db.delete("Plan Need Allocation")`, `frappe.db.delete("Departmental Need")` after a seed-namespace guard that covers only Departmental Need, not Plan Need Allocation).
Governing rule: patch discipline in the task statement ("destructive deletes without scoping"); the owner authorisations quoted in the docstrings are dated dev-site instructions (18 Sep, 21 Sep 2026) and do not state that a production site may lose these rows.
Reproduction: deploy the app to a site that has live Tender Preparation / bid rows and has not yet recorded these patches -> `bench migrate` drops/deletes them without prompt.
Classification: SPEC GAP (no approved rule says production sites are exempt or must be pre-checked); only the NDS v1.1/v1.6 patches implement a fail-closed guard.

---

### F-8 MEDIUM — Patches crash with `TableMissingError` / 1146 on a site that is behind (dropped-doctype class, still present)

Evidence (all post_model_sync, all after `pln_chg_001_v12_drop_legacy_planning_doctypes` in the pre_model_sync block has dropped these tables):
- patches/pln_revision_schema_backfill.py:20, 28, 37, 46, 70 `frappe.db.has_column("Procurement Plan Version"/"Plan Demand Allocation"/"Procurement Plan", ...)`; :53-66 `_add_index("tabProcurement Plan..."...)` -> `show index from` a missing table.
- patches/pln_chg_016_schema_cleanup.py:10-12 `frappe.db.has_column("Procurement Plan", field)`.
- patches/scope_pln_formation_batch_key.py:13-16 `show index from tabProcurement Plan Item`.
Frappe fact: `Database.has_column` -> `get_table_columns` raises `TableMissingError` for an absent table (`frappe/database/database.py:1348-1357`).
Reproduction: restore a pre-"Planning revision" backup (Patch Log lacks pln_revision_schema_backfill) and run `bench --site X migrate`: pre-sync patch drops the legacy tables, then post-sync `pln_revision_schema_backfill` raises, aborting migrate (patch order is pre_model_sync block, model sync, post_model_sync block).
Classification: CODE DEFECT (the repo's own newer patches, e.g. `v1_0/backfill_pe_fy_context_links.py:33-36`, use `table_exists` first).

---

### F-9 MEDIUM — Mid-service `frappe.db.commit()` in `tender_configurations/*` and a state-changing read reachable by GET

Evidence: 27 explicit commits inside services called from whitelisted APIs: `tender_configurations/services/review_workspace.py:257, 398, 434, 484, 554, 604`; `readiness.py:379, 432`; `price_schedule.py:788`; `tds.py:738`; `it_requirements.py:588`; `profile.py:281`; `forms_and_evidence.py:667`; `document_preview.py:705, 782, 851, 965`; `contract_values.py:613`; `publication_setup.py:549, 638, 713`; `evaluation_setup.py:992`; `implementation_schedule.py:821`; `system_inventory.py:661`; `electronic_std_template.py:1201, 1268`; `tender_configurations/__init__.py:355`. Each commits the caller's transaction after a partial write (e.g. review_workspace.py:255-257 saves the finding resolution and commits, then runs the readiness report, which itself saves and commits).
Concrete read-path write: tender_configurations/api.py:342-349 `get_tender_configuration_review` (`@frappe.whitelist()`, GET and POST allowed) -> review_workspace.py:379-398 `_ensure_review_started` sets `status = Under Review` and `frappe.db.commit()`. A GET is not CSRF-checked and normally rolled back by Frappe (`sync_database`), but the explicit commit persists it. Also electronic_std_template.py:1186-1201 heals and commits inside a "get".
Governing rule: AGENTS.md §4 ("Use Frappe's normal document ... transaction mechanisms"); task rule: commits mid-command defeat rollback of a later failure.
Reproduction: as a user with write on a Tender Configuration in "Ready for Review", open `GET /api/method/kentender_procurement.tender_configurations.api.get_tender_configuration_review?configuration_id=X` (e.g. from an `<img>` or link on another site): status becomes Under Review and is committed with `submitted_by` stamped.
Classification: CODE DEFECT (legacy module; still in modules.txt and registered).

---

### F-10 MEDIUM — Audit-event write failures are swallowed on material actions

Evidence: kentender_budget/kentender_budget/services/budget_audit_contracts.py:176-182 `safe_record_event` ("Best-effort record; never break the calling mutation") used at 12 call sites for submit/return/approve/supersede/close/reserve/check (budget_readiness_contracts.py:579, 620, 688, 699, 865; budget_check_reserve_contracts.py:277, 417; budget_contracts.py:1004, 1053; budget_line_contracts.py:214; budget_commitment_contracts.py:77). Award: award/services/records.py:160-169 `audit()` `except Exception: frappe.log_error("Award audit write failed")`; award/api.py:25-33, bid_evaluation/api.py:44-51, bid_opening/api.py:44-50 the same pattern around `log_audit_event` + `frappe.db.commit()`.
Governing rule: BUD-CHG-001 v1_12 §14 line 1241 ("Append-only events: ... submit, return, approve, activate, supersede and close; ... reservation creation ..."); AGENTS.md §4.3 ("audit actor, time, and reason").
Reproduction: make `Budget Audit Event` insert fail (e.g. a DB error/lock timeout or a schema mismatch): `submit_budget_version` still returns ok and the Version moves to "Submitted for approval" with no submission event; the failure appears only in Error Log.
Classification: CODE DEFECT (spec requires the event; code makes it optional).

---

### F-11 MEDIUM — Scheduler sweeps lack per-item isolation, so one bad record blocks all later ones (or leaks partial writes)

Frappe fact: `ScheduledJobType.execute` commits only on success and rolls back on exception (`scheduled_job_type.py:156-161`).
- kentender_procurement/.../bid_opening/services/sweep.py:34-43 `run()`: `try: sweep_tender(...) except Exception: frappe.log_error(...)` — no `rollback()` and no per-tender commit. A tender whose sweep wrote rows (e.g. `case.prepare_opening_case`) and then raised keeps those writes in the transaction, which commits when a later tender succeeds. Sibling sweeps (bid_evaluation/sweep.py:48-56, award/sweep.py:14-29, close.py:228-247) do `rollback()`.
- bid_submission/services/handoffs.py:231-241 `sweep()`: `sync(name)` for every open bid and `sync_incidents()` in one transaction with no try/except; one failing bid aborts the whole job each tick, so every other bid's hand-offs and incidents stop updating.
- tenders/services/candidate_notices.py:149-159 `dispatch_pending`: no try/except per notice, creation-ascending order; one notice whose `dispatch()` raises blocks every later Queued notice every tick.
- bid_submission/services/submission.py:284-297 `reconcile_uncertain_attempts`: `box.status()` is outside any try; an exception on the oldest uncertain attempt blocks the rest (rows before it were committed, rows after never reached).
- core/services/reference_data_transitions.py:508-536 `close_due_contexts` / `activate_due_contexts` (cron every 5 min, hooks.py:263-270): per-context `ctx.save()` in a loop with no isolation.
- budget_revision_request_contracts.py:371-379 `retry_pending_outcomes`: docstring promises per-request ordering, but a failed event does not stop later events of the same request; the consumer ignores a sequence not newer than the stored one (procurement_planning/services/budget_revision.py:193-194), so a retried earlier outcome delivered after a later one is silently dropped.
Reproduction examples: one Queued candidate notice with a malformed `destination_snapshot` -> `envelope.locked()`/`events.emit()` raises -> job fails every 4 minutes and no later notice is ever sent; two Pending events (seq 1 fails transiently, seq 2 delivers) -> seq 1 retried next tick is discarded.
Classification: CODE DEFECT (idempotent retry and "failures logged rather than swallowed/blocking" in task scope).

---

### F-12 MEDIUM/LOW — Patch records success although its uniqueness constraints may not exist

Evidence: patches/ensure_bwmf_persistence_indexes.py:92-100 `_add_unique` (`except Exception: frappe.log_error(...)`), :103-109 `_add_index`, :54-62 `except Exception: pass` around `drop column amount_sample/state`. Four unique indexes (`uniq_bwmf_manifest_id_version`, `uniq_bwmf_response_id_version`, `uniq_bwmf_evidence_item_version`, `uniq_bwmf_idempotency_org_op_key`) are integrity guarantees; on duplicate rows the CREATE fails, the patch still completes and Patch Log marks it done, so it never retries.
Classification: CODE DEFECT.

---

### F-13 LOW/MEDIUM — Departmental-plan autostart failure is swallowed with no retry (late-need dead end can recur)

Evidence: procurement_planning/services/dpp_autostart.py:66-89 wraps `ensure_departmental_plan` **and** `needs_intake.publish_need_positions` in one savepoint; on any exception it rolls both back, logs, and drops (docstring: "a failure is logged and dropped"). There is no scheduler job that re-runs it (hooks.py:481-505 lists none); only the one-off patches pln_start_plan_from_accepted_needs / pln_nds_late_need_positions backfill.
Governing rule: NDS-CHG-001 v1_16 line 75 (owner decision "Visible": every accepted Need must show its position against the department's plan).
Reproduction: make `ensure_departmental_plan` raise once when a Need is accepted (e.g. lock timeout): the Need is Accepted, no plan opened, no `Need Planning Intake Projection` written; the Need page shows no position until the next unrelated plan change.
Classification: SPEC GAP (spec requires the projection; says nothing about recovery when the reaction fails).

---

### F-14 LOW — `**kwargs` NDS endpoints accept any field; unknown fields yield HTTP 500

Evidence: departmental_needs/api.py:76-89 `save_need_draft(**kwargs)` -> `lifecycle.create_need(**args)` (keyword-only signature, lifecycle.py:512-). Reproduction: `POST .../save_need_draft` with `organisation_unit=..&financial_year=..&title=..&foo=1` -> `TypeError: create_need() got an unexpected keyword argument 'foo'` -> 500. Same for return/accept/decline. The comment at :61-69 says services must keep explicit signatures, which is why the filter only strips three names.
Classification: CODE DEFECT (allow-list the declared parameters instead of deny-listing three transport names; also closes F-1 for these four).

---

### F-15 LOW — Unvalidated numeric casts and unscoped list yield 500s / over-broad results

- journey_api.py:125 `limit_val = min(int(limit or 100), 500)` -> `limit=abc` ValueError 500; `limit=-1` passes `LIMIT -1` (:176-186) -> SQL 1064 (500). responsibility_api.py:200 `limit_page_length=int(limit or 20)` (no upper bound); api/technical_search.py:15, :19 `int(limit or 25)`.
- journey_api.py:153-156 `like = f"%{search_arg}%"` does not escape `%`/`_`; `list_journeys` returns every journey unless `scope=my-work` (:158-163, `_compute_journey_counts` :433-444 counts all journeys regardless of user): no organisational scope filter.
Classification: CODE DEFECT (low impact).

---

### F-16 LOW — Freshness check fails open

Evidence: procurement_lifecycle/api/handoff_api.py:239-251 `_get_freshness`: `except Exception: return {"fresh": True, "stale_reason": None}`. An error while validating a handoff card reports it fresh to the Journey detail view.
Classification: CODE DEFECT.

---

### F-17 LOW — Patches that rewrite data by heuristic or reset site configuration

- kentender_core/patches/backfill_master_display_titles.py:10, :36-45 (`_HASH_LIKE = ^[A-Za-z0-9]{8,}$`): any single-word department/entity name of 8+ alphanumerics ("Treasury", "Education", "Transport") is treated as a hash and renamed to "<entity> Department 001".
- kentender_budget/patches/bud_chg_001_v1_3_phase4_drop_pe_rename_fy.py:67-71: when `Financial Year` is absent, `update tabProcurement Budget set fiscal_year = NULL where fiscal_year is not null` clears every Budget's fiscal year including valid ERPNext Fiscal Year names (the "not in Fiscal Year" guard only applies on the other branch).
- procurement/patches/pln_chg_001_v127_instants_in_site_time.py:24, :61-66 imports the live seed module (`procurement_planning.seeds.kentender_mvp_v1.CLOCK_BEFORE_SITE_TIME`) and shifts any row whose timestamp equals a seed design instant, with no fixture-namespace filter.
- kentender_suppliers/patches/bds_v08_enable_supplier_signup.py:16-17 sets `Website Settings.disable_signup = 0` on every site (opens self-registration site-wide); kentender_core/patches/set_kentender_app_name.py:13-16 overwrites `app_name` in Website/System Settings.
Classification: CODE DEFECT (Low; one-shot, already applied on the dev site).

---

### F-18 LOW — Latent hazards in unused or dormant code paths

- core/services/business_id_service.py:52-57 `generate_business_id` calls `frappe.db.begin()` (MariaDB `START TRANSACTION` implicitly commits the caller's pending work) then `commit()`/`rollback()`; only re-exported in `services/__init__.py`, no production caller (grep). Becomes a mid-command commit if adopted.
- TM2 `planning_tender_handoff_*` code references dropped doctypes (`Procurement Plan`, `Procurement Package Line`) at tender_management/services/planning_tender_handoff_configuration.py:37-39 and planning_tender_handoff_audit.py:47-49; no caller exists, so unreachable today.
- procurement hooks.py:691-715 declares `fixtures` (DocType Procurement Navigation, Workspace Procurement Home, Workspace Sidebar x2, Desktop Icon x2) but no `kentender_procurement/fixtures/` directory exists, so nothing is imported on migrate; a future `bench export-fixtures` would start exporting and re-importing those records on every migrate.
- setup/after_migrate_navigation.py:44-58 `_apply_sidebar_export` deletes and re-inserts Workspace Sidebar "Procurement" on every migrate (loses per-site edits; on a developer-mode site `Workspace Sidebar.on_trash` deletes `workspace_sidebar/procurement.json` and re-export rewrites it with a new `modified` stamp each migrate); the `planning_module_navigation` basename (:77) has no file.
Classification: CODE DEFECT (Low / latent).

---

### F-19 LOW — Scheduler and delete paths rely on an RQ worker that the repo says may be absent

`frappe.delete_doc` enqueues `delete_dynamic_links` post-commit for every deleted document (`frappe/model/delete_doc.py:182-189`); production services that call `delete_doc`/`frappe.delete_doc` in business flows depend on a worker for link cleanup (award/records.py:175-177 and utils/raw_delete.py exist to avoid exactly this on the dev bench). `Email Queue` rows from `frappe.sendmail(delayed=True)` (tenders/services/candidate_notices.py:60-63) also need the scheduler's flush job. No code enforces or checks worker/scheduler health for these. SPEC GAP (no document states the production worker topology).

---

## 5. Checked and clean (so Phase 3 can separate clean from unexamined)

SQL
- No `%`-interpolation, `.format()` or `+` in any `frappe.db.sql` call; all values pass through `%s`/`%(name)s` parameters. f-string sites interpolate only constants or doctype names from code: budget_reference.py:25, strategy_reference.py:48 (`field`/`doctype` from `REF_TYPE_META`), authorization_administration.py:31, procurement_planning/services/envelope.py:92, requisitions/services/envelope.py:90, tenders/services/envelope.py:88, budget_revision.py:191, site_configuration.py:1378, business_id_service.py:68 (all `FOR UPDATE` on a module-defined doctype), bid_opening/services/home_provider.py:119 (`{'and m.is_chair = 1' if chair ...}` fixed fragments; values as `%(user)s`/`%(ended)s`), journey_api.py:169 (conditions list built from fixed strings; user text only in `values`).
- `IN (%s)` handling is by tuple/list parameter (`where name in %s`, analytics_provider.py:116-159 guards the empty list with `or [""]`; budget_contracts.py:197-210 guards `if all_reservations`; journey_api.py:165-168 builds `%s` placeholders from a non-empty list). One unguarded empty case: budget_check_reserve_contracts.py:338-341 `where name in %s` with `tuple(sorted(line_docs))` (empty only if `cached["allocations"]` is empty, which the check step does not produce).
- No client parameter reaches `order_by`, `fields`, `group_by` or a doctype name in any `frappe.get_all/get_list` call (checked: organisation_structure_api.tree_children, responsibility_api.search_users, technical_search, ktsm_landing._profile_filters uses fixed keys, TM2 workbench list uses `_filters` reserved/ignored, security audit `filters` only feed limit/start and post-filters).
- No raw `UPDATE/DELETE/INSERT` on business tables in services/api; `tabSeries` writes only in canonical-seed reset helpers.
- Literal `%` in SQL: only `pln_chg_001_v112_fiscal_year_cutover.py:59` and `pln_chg_001_v12_retire_legacy_planning_workflow_tasks.py:21` (`'FY-%%'`, `'plan.%%'`, called without values so sent verbatim and still match as a LIKE wildcard) — harmless.

Background jobs
- No `frappe.enqueue`/`enqueue_doc`/`enqueue_after_commit` in production code, so the "reads rows the caller just wrote" class does not arise; all asynchrony is scheduler-based.
- All 18 scheduler paths resolve (verified by `fh_hooks_paths.py`): core/hooks.py:263-286, budget/hooks.py:112-114, procurement/hooks.py:481-505. Jobs run as Administrator in the scheduler context; those that pass an explicit actor use "Administrator"/"System" (tenders/services/submission_close.py:100, site_configuration.py:1139-1154).
- Per-item commit/rollback with `log_error` is correct in: bid_evaluation/sweep.py:48-56, award/sweep.py:14-29, bid_submission/services/close.py:228-247, tenders/services/submission_close.py:96-106, site_configuration.py `_close_due` (:1127-1160, takes `_acquire_intake_control` lock, per-year write, audit event; idempotent re-run).
- Savepoint wrappers (`atomic()`/`running()`) roll back to the savepoint and re-raise: award/records.py:90-100, bid_evaluation/records.py:68-77, bid_opening/records.py:63-71, bid_submission/records.py:75-83, proceedings/records.py:68-76, tenders/envelope.py:128-136, requisitions/envelope.py:127-135, award_seam.py:35-42, dpp_autostart.py:66-89, budget_revision_request_contracts.py:351-358.
- bid_submission/services/submission.py:140 `frappe.db.commit()` is the documented "attempt durable before the deposit leaves" step (plan D8), replays are idempotent by `key_hash` (:107-111).
- `api._audit` helpers in award/evaluation/opening commit after writing an audit event for a refused command; the command bodies run inside `atomic()`, so partial writes were already rolled back at the savepoint before the refusal is audited.

Patches
- `patches.txt` and `patches/` agree in every app (128/128, no missing, no unlisted, no duplicates, every file has `execute`). Documented `bench execute`-only code (std_templates/services/lifecycle.py supersede/withdraw/switch, installer) is not in patches and is not whitelisted.
- Correct guard patterns found: `table_exists` before has_column (backfill_pe_fy_context_links.py:33-36, pln_revision_preflight.py, pln_nds_late_need_positions.py:26-27, cu_305_repoint_performance_target_fiscal_year.py:17), `frappe.db.exists("DocType", x)` before get_all/has_column (ovs_chg_001_v06_evaluation_evidence_manifest.py:23, ovs_chg_001_v06_tender_lead_from_certification.py:42-44, nds_chg_001_v19_rename_need_revision_fields.py:56-62, pln_chg_001_v118_publication_attempts.py:19-20), fail-closed teardown (nds_chg_001_v11_drop_retired_need_doctypes.py:46-72, nds_chg_001_v16_drop_needs_intake_window.py:29-35, nds_chg_001_v16_drop_procuring_entity_columns.py, nds_chg_001_v11_decision_review_task.py), index guards via information_schema (pln_chg_001_v12_planning_unique_indexes.py, pln_chg_001_v118_unique_indexes.py, scope_pln_formation_batch_key.py comparison), re-run no-ops (nds_chg_001_v19_rename_need_revision_doctype.py:42-49, pln_chg_001_v112_fiscal_year_cutover.py). `tpr_chg_001_v012_schema.py:36-47` raises on duplicates before adding the unique; `Database.add_unique` itself checks `information_schema` first (`mariadb/database.py:444-453`) so re-run is safe.
- Fresh installs: Frappe marks all patches as run on app install, so the destructive patches in F-6/F-7 affect only sites that upgrade across them.
- Patch ordering inside the shipped lists is consistent with dependencies (renames and drops in pre_model_sync; backfills and indexes in post_model_sync, e.g. v1_18 plan_item_roots before v1_18 unique_indexes; v19 doctype rename before v19 field renames).

Hooks / fixtures / seeds / doc_events
- `override_whitelisted_methods`, `before_request`, `after_request`, `auth_hooks` are not used anywhere (all commented template lines).
- `after_install`/`after_migrate` in core (`install.py:8-30`) are idempotent: `repair_module_defs`, `create_custom_fields(update=True)`, `ensure_roles` (only fills gaps, business_role_registry.py:296-307), `_ensure_default_pe_types` guards on `count()` (:241-243), `retire_erpnext_home_workspace` only removes records whose `app == "erpnext"` and suspends developer_mode to protect ERPNext's files. They do not touch fiscal years, intake windows or working context. Budget's `after_migrate` only calls `ensure_budget_governance_roles`.
- No migrate-time hook or seed creates a Fiscal Year; Fiscal Year creation exists only in seeds (kentender_budget/seeds/kentender_mvp_v1_portfolio.py:638, kentender_core/seeds/kentender_mvp_v1/orchestrator.py:53), which are gated by `developer_mode`/`allow_tests`/`allow_canonical_seed`/`force` (canonical.py:174-181, 1153-1155; kentender_mvp_v1/orchestrator.py:61-68; playwright_ui_fixtures.py:68). Seeds without a gate are `bench execute` utilities (dev_full_reseed.py guards with `frappe.only_for`, mvp1_role_user_cleanup.py, purge_smoke_test_tenders.py, per-module `clear.py` called from gated orchestrators); none is whitelisted.
- `doc_events`: core authorization-record handlers (validate/invalidate cache) raise on invalid data and swallow nothing; `Supplier.validate` (supplier_hooks.py:12-27) raises; `File.on_trash` (cas.py:237-245) raises via `assert_content_not_deletable`; only `Departmental Need Event.after_insert` swallows (F-13).
- `boot_session` hooks: `my_work.patch_bootinfo_home` (my_work.py:240-254) is read-only; `workspace_permissions.patch_bootinfo` catches and logs per sidebar (:259-268), never raising into boot.
- Whitelisted `**kwargs`: 4 endpoints, all stripped; internal `_call(..., **kwargs)` helpers in award/api.py:36, bid_evaluation/api.py:54, bid_opening/api.py:53 are not whitelisted and pass explicit service parameters plus `user=frappe.session.user`. All other whitelisted APIs (procurement_planning/api.py, procurement_requisitions/api.py, tenders/api.py, budget_api.py, strategy, core, suppliers) have explicit signatures; bid_evaluation/award/opening/tenders always pass `user=frappe.session.user`, TM2 workbench uses `frappe.session.user`.
- Mixed legacy swallow handlers reviewed and acceptable (fail closed or parse fallback): authorization.py:410 (`return ()` = no roles = deny), file_integrity.py:56 (`unreadable` returns True on exception), bid_submission/gateways.py:48 (`_healthy` False), award_gateway.py:66-99 (None/[] = not authorised/empty), tenders/evaluation_seam.py:198 ("Unknown", documented never fabricated), requisitions/read.py:802 (marks owner read unavailable).
