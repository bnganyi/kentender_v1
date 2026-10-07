# Sweep: authorization (AUTH-ADR-001 conformance) — Phase 2, read-only

Sweep name: **authorization**
Scope: every `@frappe.whitelist()` endpoint in all `kentender_*` apps; the AUTH hook registration (`permission_query_conditions` / `has_permission` / `kentender_scope_map`) for business doctypes; DocPerm JSON on business doctypes; Frappe User Permission use; `ignore_permissions` / `set_user` bypasses reachable from endpoints; OVS v0.6 §4.1/§4.2 read visibility.
Method: static reading only. Nothing was executed (no bench, no DB, no tests). Every runtime-behaviour claim below is marked "static" and carries a reproduction sketch for Phase 3 to run on the test site.

## 1. Method (reproducible)

```
cd /home/midasuser/frappe-bench/apps/kentender_v1
# endpoints
grep -rn "@frappe.whitelist\|@whitelist\|frappe.whitelist(" --include=*.py kentender_* | grep -v /tests/      # 668 lines
python3 <ast walker>  # (scratchpad wl_ast.py) parses 1,967 .py files / 9,267 functions; 648 decorated + 20 aliases
                      # `x = frappe.whitelist()(fn)` in departmental_needs/api.py:45-103 = 668 endpoints
grep -n allow_guest                                  # 5 guest endpoints, 2 explicit allow_guest=False
# User Permission use
grep -rnE "User Permission|add_user_permission|get_user_permissions" --include=*.py kentender_*
# bypasses
grep -rn "ignore_permissions=True\|flags.ignore_permissions\|frappe.set_user(" --include=*.py kentender_*   # 413 ignore_permissions, ~40 set_user (all tender_management)
# hooks
grep -n "kentender_scope_map\|permission_query_conditions\|has_permission" kentender_*/kentender_*/hooks.py
# DocPerm
python3 <json walker> over kentender_*/**/doctype/*/*.json  (338 doctypes, 298 non-child): role/perm matrix
grep -n "flags" in each doctype controller (lifecycle-guard presence)
# technical-read registration
grep -rn "kt_technical" kentender_*/kentender_*/hooks.py
# Frappe facts used (frappe v16.12.0, bench apps/frappe)
frappe/__init__.py:1384  get_all() forces kwargs["ignore_permissions"] = True
frappe/permissions.py:107 has_permission(): user == "Administrator" is allowed before any hook
frappe/permissions.py:558 get_roles(): every non-Guest user receives "All" and "Guest"
```
Classification of endpoints used a name-based call-graph (depth 4-6) only as a *hint*; every bucket below was then confirmed by reading the thin API layer of every file and the service gate of the endpoints named in the findings (sampled for the large, uniformly-patterned modules; see Coverage "A*").

Docs read (latest versions confirmed with `ls | sort -V`): AUTH-ADR-001 v1_11 (§1, §5, §8, §9, §10, §19), `AUTH-ADR-001-capability-mapping.md` (whole), OVS-CHG-001 v0_6 (§4, §4.1, §4.2, §11, §18.1), NDS v1_16 (§6 table, NDS-BR-019, §16.1, §8.2), BUD v1_12 (§9/§17.1, contract-service-principal paragraph), TPR v0_17 (§6 table line 713), BDS v0_11 (BDS01-AC-080), BOP v0_11 (lines 9, 146), TRUST-ADR-001 v0_2, AGENTS.md §4.3. Note: the task brief listed BDS/BOP/EVL v0_5 and AWD v0_5; the repository's latest are BDS v0_11, BOP v0_11, PRC v0_11, EVL v0_5, AWD v0_5, STR v1_9, PLN v1_29, REQ v1_14.

## 2. Coverage

### 2.1 Endpoints

668 whitelisted endpoints (648 decorated + 20 `frappe.whitelist()(fn)` aliases at `departmental_needs/api.py:45-103`). Buckets:

- **A**  = AUTH resolver reached on the read of the endpoint/service (authorise_record / permitted_ou_scopes / is_technical / registry `may_administer`), gate located and read.
- **A\*** = same pattern (service-level `guards`/`authz` on the thin-API-to-service call), gate read for the endpoints named in findings or sampled per module, remainder inferred from the uniform thin-API pattern and the call-graph hint (NOT individually read).
- **B**  = Frappe DocPerm / bare Frappe Role only (no AUTH assignment, no scope hook). Includes setup-administrator gates (System Manager/Administrator, legitimate under CFG §6/AUTH §8 for setup) and legacy-role gates.
- **C**  = `allow_guest=True`.
- **D**  = none/unchecked, or "any logged-in user".

| File | Endpoints | A | A* | B | C | D |
|---|---|---|---|---|---|---|
| `kb/api/budget_api.py` | 32 | 0 | 27 | 0 | 0 | 5 |
| `kb/api/dia_budget_control.py` | 1 | 0 | 0 | 0 | 0 | 1 |
| `kb/api/landing.py` (inert stub) | 1 | 0 | 0 | 0 | 0 | 1 |
| `kc/api/analytics.py` | 2 | 0 | 2 | 0 | 0 | 0 |
| `kc/api/home.py` | 1 | 0 | 1 | 0 | 0 | 0 |
| `kc/api/organisation_structure_api.py` | 6 | 6 | 0 | 0 | 0 | 0 |
| `kc/api/procurement_settings_api.py` | 24 | 0 | 0 | 21 | 0 | 3 |
| `kc/api/public_portal_api.py` | 2 | 0 | 0 | 2 | 0 | 0 |
| `kc/api/reference_data_api.py` | 22 | 0 | 0 | 18 | 0 | 4 |
| `kc/api/responsibility_api.py` | 10 | 10 | 0 | 0 | 0 | 0 |
| `kc/api/site_configuration_api.py` | 18 | 0 | 0 | 18 | 0 | 0 |
| `kc/api/technical_search.py` | 2 | 2 | 0 | 0 | 0 | 0 |
| `kc/authorization_api.py` (legacy AUTH-G04) | 5 | 0 | 0 | 5 | 0 | 0 |
| `kc/services/my_work.py` (legacy engine) | 2 | 0 | 0 | 2 | 0 | 0 |
| `kp/award/api.py` | 18 | 0 | 18 | 0 | 0 | 0 |
| `kp/bid_evaluation/api.py` | 50 | 0 | 50 | 0 | 0 | 0 |
| `kp/bid_opening/api.py` | 33 | 0 | 32 | 0 | 1 | 0 |
| `kp/bid_submission/api.py` | 42 | 0 | 39 | 0 | 3 | 0 |
| `kp/departmental_needs/api.py` | 24 | 24 | 0 | 0 | 0 | 0 |
| `kp/proceedings/api.py` | 1 | 1 | 0 | 0 | 0 | 0 |
| `kp/procurement_home/api/{home,landing}.py` | 2 | 0 | 0 | 2 | 0 | 0 |
| `kp/procurement_lifecycle/api/*.py` | 12 | 0 | 0 | 12 | 0 | 0 |
| `kp/procurement_planning/api.py` | 67 | 0 | 67 | 0 | 0 | 0 |
| `kp/procurement_requisitions/api.py` | 44 | 44 | 0 | 0 | 0 | 0 |
| `kp/std_templates/api.py` | 9 | 9 | 0 | 0 | 0 | 0 |
| `kp/tender_configurations/__init__.py` (re-wraps api.py) | 56 | 0 | 0 | 56 | 0 | 0 |
| `kp/tender_configurations/api.py` | 47 | 0 | 0 | 47 | 0 | 0 |
| `kp/tender_management/api/tm2_workbench.py` | 12 | 0 | 0 | 12 | 0 | 0 |
| `kp/tender_management/security/action_availability/api.py` | 2 | 0 | 0 | 0 | 0 | 2 |
| `kp/tender_management/security/api.py` | 3 | 0 | 0 | 1 | 0 | 2 |
| `kp/tender_management/tender_publication/api/handlers.py` | 11 | 0 | 0 | 1 | 0 | 10 |
| `kp/tenders/api.py` | 42 | 0 | 42 | 0 | 0 | 0 |
| `ks/api/strategy_consumer_api.py` | 12 | 0 | 7 | 0 | 0 | 5 |
| `ks/api/strategy_ui_api.py` | 8 | 0 | 7 | 0 | 0 | 1 |
| `ksu/api/ktsm_landing.py` | 7 | 0 | 0 | 4 | 0 | 3 |
| `ksu/api/smw_public.py` | 8 | 0 | 0 | 7 | 1 | 0 |
| `ksu/api/smw_workflow.py` | 15 | 0 | 0 | 14 | 0 | 1 |
| `ksu/services/eligibility.py` | 2 | 0 | 0 | 0 | 0 | 2 |
| `ksu/supplier_accounts/api.py` | 13 | 13 | 0 | 0 | 0 | 0 |
| **Total** | **668** | **109** | **292** | **222** | **5** | **40** |

(`kb`=kentender_budget/kentender_budget, `kc`=kentender_core/kentender_core, `kp`=kentender_procurement/kentender_procurement, `ks`=kentender_strategy/kentender_strategy, `ksu`=kentender_suppliers/kentender_suppliers.) The bucket for the 40 D endpoints is itemised in findings F-01, F-02, F-03, F-04, F-12, F-19, F-20, F-22, F-25. Apps with zero whitelisted endpoints: assets, compliance, governance, integrations, stores, transparency.

Caveat on A\*: the 292 are not individually proven. The thin APIs pass `user=frappe.session.user` into service functions that call `guards.require*`/`authz.*`/`people.holds` (read for EVL `reads.py`, AWD `guards.py`/`reads.py`, BOP `reads.py`/`public.py`, BDS `bid_authorization.py`, PLN `planning_authorization.py`, TND `tender_authorization.py`, REQ `requisition_authorization.py`, STD `access.py`, PRC `register.py`). A Phase 3 sweep of "every A\* service function reaches a gate" is still useful for Planning (67) and Evaluation (50).

### 2.2 Guest endpoints (c) — all 5 enumerated

| Endpoint | Justified? |
|---|---|
| `bid_submission/api.py:41 get_available_tenders` | Yes — BDS v0_11 line 725 "`GetAvailableTenders` Public bidder-safe list". |
| `bid_submission/api.py:47 get_tender_overview` | Yes — BDS line 1537/1855 "signed-out/public Tender"; own-bid data only after `authz.acting_assignment` (overview.py:118-126). |
| `bid_submission/api.py:58 download_tender_document` | Yes (public published document); streams via `bidder_projection.stream_public_document`, key-addressed. |
| `bid_opening/api.py:311 get_public_opening` | Yes — BOP v0_10 §10.5 public opening page; `public.py:_tender` refuses unpublished Tenders. |
| `suppliers/api/smw_public.py:23 ktsm_register` | **Not justified by any current module doc** — see F-21. |

### 2.3 Hook coverage (AUTH §5.3 "registered through both hooks")

Registered scoped doctypes: Budget 4 (`kentender_budget/hooks.py:87-106`), Needs 2 + DPP 2 + DPP children 4 (`kentender_procurement/hooks.py:378-412`), Requisition family 5 (`:424-437`), Tender family 14 (`:450-451`), Bid content 6 deny-all (`:737-738`), Support Issue 1 (`kentender_core/hooks.py:298-299`). Doctypes with DocPerm read for business roles but **no hook**: 72 in procurement, 5 in budget, 5 in strategy, 4 in suppliers, 23 in core (the 23 core ones are catalogues; 5 strategy are Site-wide-readers only). The ones that matter are in F-06, F-07, F-08, F-10.

### 2.4 Other enumerations

| Item | Count | Result |
|---|---|---|
| Non-child doctypes with DocPerm JSON | 298 | 26 core/ref catalogues grant `All`/`Desk User` read (F-25); 2 grant `All` rwc (F-05); 201 grant `System Manager`/`Administrator` write/create/delete (F-09). |
| Doctypes with no DocPerm at all (Administrator-only) | 38 | Bid/Opening/Evaluation/Proceeding doctypes: correct sealed-custody posture. |
| `User Permission` reads in production code | 6 sites | `authorization_native.py:34`, `org_scope_access.py:94-102`, `authorization.py:617-619` (count only), plus scripts/seeds. F-16. |
| `ignore_permissions=True` (non-test, non-seed) | 413 | Overwhelmingly post-gate service writes. 2 are `get_all(..., ignore_permissions=True)` reads (Fiscal Year catalogues, benign, F-25). 5 reachable endpoints do it with no prior gate: `ktsm_register`, `ktsm_update_profile`, `ktsm_upload_document` (own-profile), none else proven unguarded beyond F-01/F-21. |
| `frappe.set_user(` | ~40 sites | All in `kentender_procurement/tender_management` (TM2); take the actor from the caller (F-01). |
| Frappe Query/Script Reports | 0 | AUTH §5.4 is vacuously met for reports. `authorization.py:504 report_match_conditions` has zero production callers (tests only). |

---

## 3. Candidate findings (most severe first)

### F-01 — TM2 publication API trusts a client-supplied `actor`; `actor="Administrator"` is a break-glass bypass — CRITICAL — CODE DEFECT (on a retained legacy surface)

Evidence
- `kentender_procurement/tender_management/tender_publication/api/handlers.py:192,222,237,252,272,292,312` — seven whitelisted endpoints declare `actor: str | None = None` and forward it: `res = ApprovalDecisionService.approveForPublication(tn, payload, actor)` (:265), `PublicationTransactionService.publishTender(tn, actor)` (:320), `ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor)` (:230), `PublicationReadinessService.runReadiness(tn, actor)` (:200).
- `.../approval/approval_decision.py:64-65`: `def _effective_actor(actor): return _strip(actor) or _strip(frappe.session.user) or "Administrator"` — the supplied value wins over the session.
- `.../authorization/publication_authorization.py:140-141`: `if actor == "Administrator": return` inside `_assert_any_role`, so every role check is skipped for the literal string.
- `enforce_sec_authorization` (`security/authorization/integration.py:32`) does the same `act = (actor or "").strip() or session.user`, and `object_scope.py:_break_glass` passes `Administrator`.
- `.../snapshot/configuration_snapshot.py:161` `frappe.set_user(act)` and `services/publish_tender.py:212` `frappe.set_user(actor)`, `services/approve_tender_publication.py:201` — the session is switched to the supplied user for the write.
- Also unauthenticated-by-role reads in the same file: `pub_api_get_latest_publication_readiness` (:207), `pub_api_get_publication_snapshot` (:327), `pub_api_validate_evidence_package` (:344) (no role check; `getPublicationSnapshot` returns the Final snapshot summary).

Rule: AUTH-ADR-001 §5.5 "The client never supplies an assignment ID, effective role, permitted scope or available action as authority"; §19 "Do not authorise from ... UI"; §8 (technical roles decide nothing); AGENTS.md §4.3 "Never rely on ... client checks for authorization".

Reproduction: as any logged-in user with a Desk session: `POST /api/method/kentender_procurement.tender_management.tender_publication.api.handlers.pub_api_approve_for_publication` with `tender_code=<TM2 tender>`, `decision_payload={"decision":"Approved"}`, `actor=Administrator`. Expected (correct): permission denied; static reading: the role check is bypassed and the write runs as Administrator. Same with `pub_api_publish_tender`. Pytest sketch: call the function as a user with no roles and `actor="Administrator"` on a TM2 Tender at "Locked for Approval"; assert `PermissionError`.

Note: TM2 is explicitly kept live pending the "OD-F TM2 clean-up" (`docs/mvp-1-r1/12_bid_submission/reconciliation/legacy_inventory.md` §4), so this is a known-deferred legacy surface — but the deferral is a delivery decision, not an authorization decision; the endpoints are reachable now.

### F-02 — Budget reservation/commitment lifecycle endpoints accept any authenticated user — CRITICAL — CODE DEFECT (+ SPEC GAP: no way to identify the "service principal")

Evidence
- `kentender_budget/services/budget_commitment_contracts.py:24-31`:
  `def _require_service_capability(): ... if not frappe.session.user or frappe.session.user == "Guest": frappe.throw("Authentication is required" ...)` — the only check. Called at :75 (`revalidate_reservations`), :128 (`release_reservation`), :174 (`convert_reservation`), :257 (`adjust_commitment`).
- Exposed as `@frappe.whitelist()` at `kentender_budget/api/budget_api.py:267,286,305,322` and, a second route to the same release, `kentender_budget/api/dia_budget_control.py:25-26 release_reservation(reservation_id, reason)` calling `_release(reservation=..., amount=None, ...)`.
- Writes use `doc.save(ignore_permissions=True)` (:144).

Rule: BUD v1_12 line 358: "The **contract service principal** is an authenticated service account, not a business role and not a registry entry. It calls `revalidate_reservations`, `release_reservation`, `convert_reservation` and `adjust_commitment`…"; AGENTS.md §4.3 "required role and organisational scope". The spec names a *service account* but gives no mechanism to identify one (SPEC GAP); the code treats every logged-in account (internal user, supplier Website User) as that principal. Compare `tenders/services/candidate_gateway.py:79-85 require_producer` which gates the equivalent bidder-facing producer by a dedicated Frappe Role.

Reproduction: as a supplier/Website User: `POST /api/method/kentender_budget.api.budget_api.release_reservation {reservation:<name or generated_reference>, downstream_event_id:"x", downstream_event_type:"Contract", idempotency_key:"k1"}` → reservation Released, funds returned to availability. `adjust_commitment {commitment, new_total, ...}` and `convert_reservation {reservation, contract:"X", amount}` likewise. Sketch: pytest as `Administrator`-less test user with only the "All" role; assert `PermissionError`.

### F-03 — Audit-trail read endpoints have no authorization; return any module's audit events — HIGH — CODE DEFECT

Evidence
- `tender_management/security/api.py:115-130 sec_api_audit_events(object_type, object_code, filters)` and `:133-146 sec_api_audit_tender_events(tender_code, filters)`; no role/scope check in the endpoint or `_wrap` (:49-62).
- `security/audit/event_service.py:85-102` and `:117`: `frappe.get_all("Audit Event", filters={"document_type": ot, "document_name": oc}, fields=[... "performed_by","timestamp","metadata" ...])`. `frappe.get_all` forces `ignore_permissions=True` (frappe/__init__.py:1384); `Audit Event` DocPerm is System Manager/Administrator only (`audit_event.json:90,102`).
- `Audit Event` is the platform-wide ledger (`kentender_core/services/audit_event_service.py`), so `object_type` may be any doctype (`"Departmental Need"`, `"Tender"`, `"Strategic Plan Version"`…).

Rule: AUTH-ADR-001 §5.1/§5.4 (counts/rows must not disclose what the caller cannot see), §8 (audit evidence is technical-read), AGENTS.md §4.3 "Return only data the caller is allowed to see".

Reproduction: as any logged-in Website User: `GET /api/method/kentender_procurement.tender_management.security.api.sec_api_audit_events?object_type=Departmental Need&object_code=<need name>` → rows incl. `performed_by` and `metadata`. Sketch: same call as a user with no business role; assert `PermissionError`/empty.

### F-04 — KTSM supplier workbench read endpoints have no authorization (supplier registry + PII readable by any logged-in user) — HIGH — CODE DEFECT

Evidence: `kentender_suppliers/api/ktsm_landing.py:24-25 get_landing`, `:153-154 get_suppliers(filters)`, `:304-305 get_supplier_detail(supplier_code)` — no `_assert_registry_access()` (defined :258 and used only by the builder endpoints :455-571). All three read with `frappe.get_all(...)` (ignore_permissions). `get_supplier_detail` returns `approval_status, operational_status, compliance_status, risk_level, external_user` (login e-mail), and the document list with verifier names (:316-372).

Rule: AUTH §5.1, AGENTS.md §4.3; also BDS/Supplier-Accounts boundary (suppliers are Website Users and must read only their own organisation).

Reproduction: as a supplier Website User: `GET …ktsm_landing.get_suppliers?filters={}` → every supplier, risk levels, e-mails. `get_supplier_detail?supplier_code=SUP-KE-2026-0001`.

### F-05 — DocPerm `All` has read/write/create on two Tender-Configuration doctypes — HIGH — CODE DEFECT

Evidence: `tender_configurations/doctype/confirmed_tender_document_package/confirmed_tender_document_package.json:219` and `.../it_tender_publication_record/it_tender_publication_record.json:317`: `"role": "All"` with `"create": 1, "read": 1, "write": 1`. Fields include `tender_html`, `document_hash`, `status`, `publication_datetime`, `submission_deadline`, `published_by`. Frappe gives every non-Guest user the `All` role (frappe/permissions.py:558) including Website/portal users. No scope hook, controller has no immutability guard.

Rule: AUTH §5.1/§19 (permission by registered responsibility), AGENTS.md §4.3; the package is documented as "immutable" (`f1_publication_handoff.py:214`).

Reproduction: as a supplier Website User: `POST /api/resource/IT Tender Publication Record` / `PUT /api/resource/Confirmed Tender Document Package/<name> {"tender_html": "..."}`.

### F-06 — Departmental Need child doctypes carry business-role read/write DocPerm with no scope hook (cross-department read and direct write) — HIGH — CODE DEFECT

Evidence
- `departmental_need_revision.json:139-166`: Departmental Author `rwc`, Head of User Department `rw`, Procurement Planner `r`, Auditor `r`; `need_withdrawal_request.json` same; `departmental_need_decision.json` read for all four. Fields include `title`, `description`, `expected_operational_result`, `indicative_quantity`, `content_hash`, `revision_status`.
- `kentender_procurement/hooks.py:372-380` comment: "`Departmental Need Revision` / `Decision` / `Need Withdrawal Request` have no OU field of their own and no direct route; access … governed by the service layer" — so none is in `kentender_scope_map`, none has a hook (`hooks.py:391-412`). The docs of those doctypes grant DocPerm anyway; Frappe REST/`get_list` ignore the absent "route".
- `departmental_need_revision.py` has no lifecycle-flag guard (not in the `flags` grep list).

Rule: NDS v1_16 NDS-BR-019 (line 438) "Counts, rows, direct routes, services and exports use the same server-side scope predicate"; NDS §16.1 (line 1798) "Do not expose writable DocType endpoints that bypass commands"; AUTH §5.3 "Both are required … Registering only the query hook leaves a direct-route hole" (here neither is registered). This is the intake-scope-bug class (out-of-scope departments) reappearing one layer down.

Reproduction: as a Departmental Author of department A: `GET /api/resource/Departmental Need Revision?fields=["name","title","description","departmental_need"]` → revisions of department B's Needs. `PUT /api/resource/Departmental Need Revision/<accepted revision> {"title":"changed"}` → accepted baseline altered (only `content_hash` is stored, nothing recomputes it). Sketch: `frappe.get_list("Departmental Need Revision", user=author_of_A)` must equal the revisions of A's Needs.

### F-07 — "Read-only" Need projection tables are writable and deletable by business roles — HIGH — CODE DEFECT

Evidence: `need_planning_intake_projection.json:132-170` grants **Departmental Author, Head of User Department, Procurement Planner and Auditor `read/write/create/delete`** (plus share/export); `need_planning_usage_projection.json` / `…disposition_projection.json` grant Departmental Author/HoD `r` only but `System Manager rwc`. The controller docstring (`need_planning_intake_projection.py:3-12`) says "a read-only projection supplied by Planning … users cannot edit it. It is written only by `project_need_planning_intake`". The projection drives withdrawal clearance and the Need detail's Planning status.

Rule: NDS §8.2 (line 637) "written only by project_need_planning_intake"; AGENTS.md §4.3; AUTH §5.1.

Reproduction: as an Auditor: `DELETE /api/resource/Need Planning Intake Projection/<name>`; or `PUT … {"position":"Update required"}`.

### F-08 — Procurement Planner is unrestricted over Departmental Need at the Frappe-hook level; NDS allows only the current accepted revision — HIGH — CODE DEFECT (two predicates, AUTH §9.1 "one predicate")

Evidence
- Service predicate: `departmental_needs/services/permissions.py:130-135` "the Planner reads only the current accepted source, Site-wide" (`cstr(need.current_state) == STATE_ACCEPTED and authorise_record(... ROLE_PROCUREMENT_PLANNER ...)`).
- Hook predicate: `kentender_core/services/authorization.py:440-447 scope_condition`: roles considered = those whose projection intersects the doctype's DocPerm read roles (`_relevant_business_roles`, :400-419); `Departmental Need` DocPerm read includes Procurement Planner (Site-wide), so `site_wide` is non-empty and `scope_condition` returns `""` (unrestricted) for a Planner; `has_permission` (:461-501) likewise returns True (`:495-497`). Draft/Submitted/Returned Needs of every department are therefore readable by any Planner via `/api/resource/Departmental Need` and `Departmental Need Revision` (no hook at all, F-06).

Rule: NDS v1_16 §6 table (line 481) "Procurement Planner | Site-wide | Read current accepted Need revisions …"; NDS-BR-019; AUTH §9.1 ("one semantic implementation and one predicate"); Calibration class "approved-only read" (Strategy universal read).

Reproduction: as a Planner: `GET /api/resource/Departmental Need?filters=[["current_state","in",["Draft","Returned"]]]`; expected empty. Sketch: `frappe.get_list("Departmental Need", filters={"current_state":"Draft"}, user=planner)` → must be `[]`.

### F-09 — System Manager/Administrator hold write/create/delete DocPerm on service-owned business, decision and audit doctypes; the AUTH hooks return True for technical users on every ptype — HIGH — CODE DEFECT (contradicts AUTH §8)

Evidence
- DocPerm: 201 of 298 non-child doctypes grant `System Manager` and/or `Administrator` one of write/create/delete. Examples: `audit_event.json:90-102` (rwcd — the audit ledger), `requisition_decision.json:144` and `tender.json:295` (rwcd), `departmental_need.json` (rwc), `procurement_budget_version.json:238` (rwcd), `annual_plan_version.json:210-216` (rwc), `strategic_plan_version.json:138` (rwcd), `user_responsibility_assignment.json:160-168` (rwcd, bypasses the `grant`/`revoke` commands' preview, overlap check, projection sync and audit).
- Hooks: `authorization.py:482-484` `if is_technical(principal): return True`; `tender_authorization.py:288-289`, `requisition_authorization.py:353-354` identical; none look at `ptype`.
- Controller guards: later modules (Tender family except root/Task, Supplier, Proceedings, Opening, Evaluation, Award) refuse non-lifecycle updates/deletes (`flags.kt_lifecycle`; e.g. `tender_decision.py:12-19`) — but only on `not self.is_new()`, so a technical user can still **create** a forged `Tender Decision`/`Tender Event` row. NDS/PLN/REQ/BUD/Tender root/Tender Task controllers have no guard at all (`tender.py: class Tender(Document): pass`, `procurement_requisition.py`, `annual_plan_version.py`, `requisition_decision.py` all `pass`).

Rule: AUTH-ADR-001 §8 "Administrator and System Manager hold technical **read** access"; "Setup authority is not business authority"; §8 "Seeds, fixtures and test profiles shall not grant business roles to Administrator"; AUTH-AC-018 as cited in `authorization.py:292-295`; §9.2 "Every mutation is authorised and validated server-side"; audit append-only (`event_service.py:157-161`).

Reproduction: as a System Manager with no assignments: `POST /api/resource/Tender {…}`; `PUT /api/resource/Procurement Budget Version/<n> {"status":"Active"}`; `DELETE /api/resource/Audit Event/<n>`; `POST /api/resource/User Responsibility Assignment {…status:"Enabled"…}`. Expected: refusal; static: allowed by DocPerm and by the hook. Part of this is spec-aligned for *setup* doctypes (System setup writes OUs/assignments "on save", §8) — those should go through the commands, not raw DocPerm; the business/decision/audit doctypes have no such exemption.

### F-10 — Business roles can write service-owned lifecycle doctypes directly (state machine, SoD and audit bypass) — HIGH — CODE DEFECT

Evidence (DocPerm + absent/insufficient controller guard):
- `Procurement Budget Version`: Budget Officer `rwc`, Budget Approver `rw` (`procurement_budget_version.json:250-262`); controller `validate()` checks revision/approval-date only (`procurement_budget_version.py:15-21`), so `status` may be set to `Active` by a Budget Officer through REST — bypassing Budget Approver, no-self-approval (read from the submission audit event) and the atomic activate (`BUD v1_12 §17.1`). Same for `Procurement Budget`, `…Line`, `…Line Version` (Budget Officer `rwc`).
- `Annual Plan`, `Annual Plan Item`, `Annual Plan Version`, `Plan Source Allocation`: Procurement Planner `rwc` (`annual_plan_version.json:222`); controller `pass`. State, approvals, finance basis are written by Planning commands.
- `Departmental Need`, `Departmental Plan`, `Departmental Plan Entry/Version`: Departmental Author `rwc`, HoD `rw`; core `has_permission` is scope-only (restricts OU, never ptype/state), controllers guard only immutable OU/FY (`departmental_need.py:19-36`), so `current_state` is writable by the author.
- `Strategic Plan(Version)/Strategy Node`: Strategy Author `rwc`; mitigated in part by `strategy_domain_guards.validate_strategic_plan_version` immutability of approved content (adequacy not assessed).

Rule: NDS §16.1 (line 1798); AUTH §5.5/§5.6 steps 6-8 (state, task, SoD checks live in the command); AGENTS.md §4.3.

Reproduction: as Departmental Author of A: `PUT /api/resource/Departmental Need/<own need> {"current_state":"Accepted for planning"}`. As Budget Officer: `PUT /api/resource/Procurement Budget Version/<draft> {"status":"Active"}`. Pytest sketch: for each doctype with a non-technical write DocPerm, attempt a raw `doc.save()` that changes the status field as that role; assert refusal.

### F-11 — Reference-data API still lets a bare Frappe Role create additional Procuring Entities and PE/FY Contexts — HIGH — CODE DEFECT (retained pre-AUTH v1.6 surface)

Evidence: `kentender_core/api/reference_data_api.py:72-77 create_or_revise_pe`, `:80 update_pe_draft`, `:87 decide_pe_change`, `:122 create_financial_year`, `:170 enable_pe_fy_context`; `services/reference_data_transitions.py:44-61 create_pe_draft` inserts a new `Procuring Entity` after only `perm.require_reference_data_manager(actor)` (:47); `services/reference_data_permissions.py:25-33` grants authority by the Frappe Role `Reference Data Manager` alone (not a registered business responsibility, `business_role_registry.py` has no such entry; `procuring_entity.json:161` grants it `rwc`). No "only one PE" guard.

Rule: AUTH-ADR-001 §19 "Do not create a second Procuring Entity record or simulate multi-tenancy inside one site"; §5.7 "Direct manual addition of a Frappe Role creates no business authority"; §20 (CFG owns the single Site Procuring Entity record).

Reproduction: as a user with the `Reference Data Manager` role: `POST …reference_data_api.create_or_revise_pe {payload:{entity_code:"PE-X",legal_name:"X",pe_type_code:"…"}}` → a second Procuring Entity row.

### F-12 — Strategy consumer endpoints are open to every logged-in account (portal users included); `get_strategy_lineage` ignores version status; `create_strategy_snapshot` writes unguarded — MEDIUM — CODE DEFECT (calibration class)

Evidence: `api/strategy_consumer_api.py:40,55,72,77,85` (no gate); `services/strategy_consumer.py:76-173 resolve_strategy_context`, `:176 list_strategy_objectives` (Active only), `:451 list_active_targets` (Active only), `:225-272 get_strategy_lineage(node_id)` — resolves any `Strategy Node`/`Performance Indicator`/`Performance Target` from a Draft or Submitted version and returns ancestor titles; `:275-336 create_strategy_snapshot` calls `record_event(...)` (audit write) for any caller. Contrast `strategy_ui_contracts.py:72-80,340,476,694,874` which apply `read_scope`.

Rule: Strategy is universally readable by internal (System) users for approved plans only; draft/pending restricted; portal accounts excluded (`strategy_authorization.py:225-246`, owner decision 5 Oct 2026; OVS §4.1 STR "No general Draft or pending review access is added"); AUTH §10.

Reproduction: as a supplier Website User: `GET …strategy_consumer_api.get_strategy_lineage?node_id=<node of a Draft version>` → titles; `…resolve_strategy_context?fiscal_year=…` → plan titles/hierarchy summary. Sketch: assert `read_scope(user)==""` ⇒ empty/not found.

### F-13 — A departmental reader can fetch `Internal` Tender documents — MEDIUM — CODE DEFECT (needs runtime confirmation)

Evidence: `tenders/services/documents.py:104-109` — only `audience == "Audit"` (site/technical) and `audience == "Public"` (published) are restricted; for `mode == "department"` an `Internal` request falls through and returns `html_of(row.name)` / the PDF URL (:111-121). Contrast `tenders/api.py:preview_tender_documents` which refuses department mode (`authz.not_found()` when `mode == "department"`).

Rule: TPR v0_17 line 713 "Departmental Author / Head of User Department | Organisation Unit | Read inherited requirements and neutral Tender/publication status … no Tender action"; AUTH §10 masked not-found. Mitigation: the caller needs the document's 64-char digest (not guessable) — the digests are listed by `documents.list_for_tender`, whose exposure to department mode was not traced.

Reproduction: as HoD of a contributing department: `GET …tenders.api.get_tender_document?digest=<digest>&audience=Internal` for a Tender in preparation.

### F-14 — Tender list predicate (lead unit only) differs from the direct-access predicate (lead + contributors) — MEDIUM — CODE DEFECT

Evidence: `tenders/services/tender_authorization.py:257` list condition `` `tabTender`.`lead_org_unit` in (...) `` versus `has_permission` :305 `departmental_units(principal) & contributing_units_of(root)` (lead plus `contributing_org_unit_ids`). `read.py:236` builds the Tenders workspace with `frappe.get_list("Tender", ..., user=actor)`, so a contributing (non-lead) department's HoD gets no rows although a direct open succeeds.

Rule: OVS v0_6 §4.1 TPR/BOP row (lines 87, 94) "HoD receives administrative progress … for a Tender with an authorised lead/contributing-OU relationship"; AUTH §5.4 "Counts shall not disclose records that rows cannot show" / §5.3 one predicate.

Reproduction: HoD of a contributing-only unit: `frappe.get_list("Tender", user=hod)` omits the Tender, `frappe.has_permission("Tender", doc=<name>, user=hod)` is True.

### F-15 — Legacy AUTH-G04 engine (Operational Scope Assignment / Capability Profile / Workflow Task) is still live, writable by API, and still authorises My Work claims — MEDIUM — CODE DEFECT (§11 cutover not completed)

Evidence: `kentender_core/authorization_api.py:24-34 add_assignment`, `:9-21 user_access/routing_rule/revise_routing_rule`, `:30-34 diagnostic`; `services/authorization_administration.py:63-70 create_draft_assignment` inserts `Operational Scope Assignment` with `ignore_permissions=True` (gate: System Manager role only, `require_access_administrator` :17-21); `services/my_work.py:173,226 get_my_work/claim_my_work_task` → `workflow_tasks.claim_task` → `require_capability` (`workflow_tasks.py:139,154,177`) → `authorization_policy.evaluate_capability` over `Operational Scope Assignment` (`authorization_policy.py:67-73`); `kentender_core/hooks.py:223-262 doc_events` still wire these doctypes; `authorization_diagnostics.py:41` `support.record.view` capability. Doctypes `User Scope Assignment`, `Strategy Scope Assignment`, `Operational Scope Assignment`, `Capability Profile`, `Authorization Delegation` still exist with System Manager/Administrator rwcd and `Desk User` read on `Strategy Scope Assignment`.

Rule: AUTH §19 "Do not keep `User Scope Assignment` and `User Responsibility Assignment` both active"; §11.5 "No fallback mode"; capability-mapping doc §9 ("OSA/Capability Profile path retired … no dual-mode period in production"); `authorization.py` module docstring.

Reproduction: as System Manager: `POST …authorization_api.add_assignment {values:{user_id, capability_profile_id, procuring_entity_id, effective_from}}` creates a second authority record; `get_my_work` for that user lists queue tasks authorised by it.

### F-16 — Frappe User Permission is read in a production path reachable from a whitelisted endpoint — MEDIUM — CODE DEFECT

Evidence: `services/org_scope_access.py:92-102 permitted_procuring_entities`: "Fall back to User Permission PEs if no scope rows yet" → `frappe.get_all("User Permission", filters={"user": user, "allow": "Procuring Entity"} ...)`; called by `reference_data_resolver.py:114-118 _authorized_context_rows` and `working_context.py:114-117`, exposed through `reference_data_api.py:234 get_working_context` and `:239 select_working_context`. `authorization_native.py:34-54` also scopes by User Permission (module only imported by tests/inventory script). The result narrows which PE/FY contexts a user is offered and is persisted via `frappe.defaults` (`working_context._set_default`).

Rule: AUTH §19 "Do not treat Frappe User Permission as a KenTender fallback" and "Do not store authoritative context in … session defaults or a user profile"; §11.5; §7 (User Permission stays only for ERPNext/HRMS). Mitigation: documented as non-authoritative compat shim; yet still an authorization input.

Reproduction: add a `User Permission` (allow=Procuring Entity) for a user with no responsibilities, call `get_working_context(module="budget")` → context rows returned.

### F-17 — KTSM supplier workflow authorised by bare Frappe Roles that include System Manager — MEDIUM — CODE DEFECT

Evidence: `kentender_suppliers/api/smw_workflow.py:16-35` `_assert_approver_or_admin` allows `{"System Manager","Administrator","KenTender Approving Authority"}`; used by `ktsm_approve_supplier` (:67), `ktsm_return_supplier` (:74), `ktsm_reject_supplier`; `ktsm_landing.py:258-271 _assert_registry_access` accepts bare roles incl. `Procurement Officer`, `Procurement Planner`, `Planning Authority`. None of `KenTender Approving Authority`, `KenTender Compliance Officer`, `KenTender Supplier Registry Officer` is in `business_role_registry.py`.

Rule: AUTH §8 (technical roles decide nothing), §5.7 (a Frappe Role grants no business authority), §4.4 (administrators do not define production roles).

Reproduction: as System Manager with no assignment: `POST …smw_workflow.ktsm_approve_supplier {supplier_profile}` succeeds.

### F-18 — Retained pre-AUTH procurement surfaces (Tender Configurations 103 endpoints, TM2 workbench, Procurement Lifecycle, Procurement Home) authorise by bare/legacy Roles with no scope — MEDIUM — CODE DEFECT (deferred legacy)

Evidence: `tender_configurations/api.py:26-28 _require_login` + per-service `frappe.has_permission(doc=…, ptype=…)` (e.g. `services/profile.py:152,215`); `Tender Configuration` DocPerm roles `Tender Manager`, `Planning Authority` (`dtperm`), no hook, no technical resolver; `TM2 *` doctypes grant `Procurement Officer` `rwc` on 24 doctypes; `procurement_lifecycle/api/permission_guard.py:46-60 JOURNEY_READ_ROLES` (Requisitioner, Planning Authority, Finance Reviewer, Department Approver…) and `journey_api.py:103 list_journeys` raw SQL over all journeys, docstring `scope="my-work"` "via User Permission on Procuring Entity" (not implemented, no scope applied); `procurement_home/services/home_portfolio.py:27-60` role sets; `get_procurement_home(procuring_entity, fiscal_year)` trusts a client PE (`procurement_home/api/home.py:16`). None of these roles is in the registry.

Rule: AUTH §19 "Do not add module-specific scope resolvers"; §5.7; §5.3 hooks; OD-F deferral (legacy_inventory §4).

Reproduction: as a user with only the legacy role `Planning Authority`: `get_tender_configurations_dashboard`, `get_tender_configuration` for any package; `list_journeys`.

### F-19 — `sec_api_action_availability*` evaluate for a client-chosen `actor` — MEDIUM — CODE DEFECT

Evidence: `tender_management/security/action_availability/api.py:154-158 _resolve_actor` returns the explicit `actor` over the session; endpoints :162, :184 pass it to `ActionAvailabilityService.get_action_availability(actor_user, …)` and echo `actor_user_code`. Contrast `security/api.py:149-168` which discards `actor` ("session actor is mandatory").

Rule: AUTH §5.5. Impact: any user can probe what another user (e.g. Administrator) may do on a tender; information disclosure only.

### F-20 — Supplier eligibility endpoints reveal blacklist/suspension reasons to any logged-in account — MEDIUM — CODE DEFECT

Evidence: `kentender_suppliers/services/eligibility.py:64-79 check_supplier_eligibility`, `check_multiple_suppliers` (`allow_guest=False`, no role check), `smw_workflow.py:122 ktsm_check_eligibility`; `_eligibility` returns reason codes (`NOT_ACTIVE`, access revoked/suspended …) for any `supplier_code`.

Rule: AUTH §5.4/§10, BDS (supplier sees only own-organisation data).

### F-21 — Unauthenticated `ktsm_register` creates Users, ERPNext Suppliers and API-access rows with `ignore_permissions` — MEDIUM — CODE DEFECT / SPEC GAP

Evidence: `smw_public.py:23-70` (`allow_guest=True`); `:49 erp.insert(ignore_permissions=True)`, `:58 prof.insert(ignore_permissions=True)`, `:80-100 _ensure_website_user_for_registration` (`usr.insert(ignore_permissions=True, ignore_links=True)`, binds an *existing* user e-mail to a new profile without verification), `_ensure_api_access_for_profile` `.insert(ignore_permissions=True)`. No throttle, captcha or e-mail verification before row creation. The supported supplier-onboarding path is `supplier_accounts/api.py:register_supplier_organisation` (signed-in, verified e-mail). `ktsm_register` is referenced only by `tests/test_ktsm_smoke_contract.py` and `BDS-CHG-001_Implementation_Plan.md`.

Rule: AUTH §19 is silent on guest writes; AGENTS.md §4.3; BDS v0_11 requires verified accounts (SPEC GAP: no document justifies this guest write).

Reproduction: unauthenticated `POST /api/method/kentender_suppliers.api.smw_public.ktsm_register {supplier_name:"A", primary_email:"victim@example.com"}` repeatedly.

### F-22 — NDS planning-projection endpoints let a technical principal write projections, and accept a client `actor` — MEDIUM — SPEC DEFECT (NDS vs AUTH §8) + CODE DEFECT

Evidence: `departmental_needs/services/usage.py:178-182,326,453`: `in_scope(principal, ROLE_PROCUREMENT_PLANNER, "") or is_administrative(principal)` → `in_scope` itself returns True for technical users (`permissions.py:in_scope`), and NDS v1_16 line 637 states "Procurement Planner or administrative principal only". `usage.py:361` `"actor": cstr(actor) or principal` — `actor` is an endpoint argument (`project_planning_disposition(..., actor: str = "")`, :317) recorded as the event actor.

Rule: AUTH §8 "Setup authority is not business authority … a technical role … decide[s] nothing"; §5.5. NDS §8.2 contradicts AUTH on technical write (SPEC DEFECT); the client-supplied `actor` is a code defect.

### F-23 — Administrator can read bid working-copy content through Frappe's own bypass; Bid Receipt resolver points at a doctype whose hook denies everyone — MEDIUM — SPEC GAP (recorded residual) + CODE DEFECT

Evidence: `bid_submission/services/bid_authorization.py:78-83` (comment :67-72) — `deny_desk_access` returns False and `deny_desk_query` returns "1=0" for `Bid Section Response`, `Bid Evidence`, `Bid Draft Change`, `Bid Command Journal`, `Bid Receipt`, `Bid Submission Change` (hooks `kentender_procurement/hooks.py:736-738`); the module comment states "Administrator bypasses Frappe's permission checks — a recorded production-gate residual, plan D7"; Frappe returns True for `Administrator` before hooks (frappe/permissions.py:107). `bid_submission/services/technical_read.py:40` registers `Bid Receipt` with a `["Form","Bid Receipt",name]` route although the deny hook makes that form unopenable for a System Manager (only Administrator gets through).

Rule: BDS v0_11 BDS01-AC-080 (line 2012) "Technical and administrator views expose only authorised service/custody metadata and cannot decrypt, preview, download or search submitted content"; OVS v0_6 §4.2 "never bypasses sealed custody"; AUTH §8 "never stranded". 

Reproduction: as `Administrator`: `GET /api/resource/Bid Section Response?fields=["*"]` returns working-copy answers; as System Manager open the Bid Receipt link from Technical search → permission error.

### F-24 — Technical-read registration and OVS §4.2 divergences — MEDIUM — SPEC DEFECT (peer docs disagree) / CODE DEFECT

Evidence: (i) Bid Evaluation, Proceedings and Tender Configurations register nothing in `kt_technical_reference_resolvers`/`kt_technical_read_probes` (`kentender_procurement/hooks.py:667-686` lists Needs, Planning, Requisitions, Tenders, STD, Bid Submission, Bid Opening (resolvers only), Award). (ii) `bid_opening/services/reads.py:112-128` refuses the Opening register/record to technical readers ("Bids, the register and the opening record are not shown to administrators"), following BOP v0_11 line 146 "Non-content health and incident support only", while OVS v0_6 §4.2 (lines 104-106) / OVS-P05 (approved 3 Oct 2026) says that after governed release Administrator/System Manager reads the ordinary owner business record; BOP v0_11 line 9 acknowledges OVS "qualifies" it.

Rule: AUTH §8 ("Every module registers its record types … through `kt_technical_reference_resolvers` and its read entry points … through `kt_technical_read_probes`"); OVS §4.2.

### F-25 — Catalogue endpoints readable by any authenticated account — LOW — CODE DEFECT

Evidence: `reference_data_api.py:44,49,54,111` (`list_pe_types`, `list_organisation_units`, `list_funding_sources`, `list_financial_years`); `procurement_settings_api.py:68,299,306` (`get_method_profile`, `get_regulatory_reference_version`, `list_regulatory_reference_versions`); `budget_contracts.py:66-76` and `strategy_ui_contracts.py:1233-1250` `list_available_fiscal_years` with `get_all(..., ignore_permissions=True)`; all use `frappe.get_all`. DocPerm for these is `Desk User`/`All` read, so a portal user could not read them via REST but can via these endpoints. `kb/api/landing.py` returns a constant. Data is reference/catalogue (OU names, funding sources, FY ranges, rule versions).

Rule: AUTH §5.1; OVS/STR portal-excluded principle.

### F-26 — Frappe-level reads for AO/HOPF on Departmental Need are absent (service-only) — LOW — CODE DEFECT vs OVS wording

Evidence: `departmental_need.json` DocPerm has no Accounting Officer/HOPF; `departmental_needs/services/permissions.py:136-139,_oversight_office` grants them read via `can_view`. OVS v0_6 §4.1 line 94: "STR/BUD/REQ and departmental additions must be explicit in their owner hooks; holding a URL or an office label alone is insufficient." Same pattern for DPP (no AO/HOPF read DocPerm on `Departmental Plan`).

### F-27 — `report_match_conditions` (AUTH §5.4 helper) has no production caller — LOW — informational

Evidence: `authorization.py:504-509`; grep shows only `tests/test_authorization.py`. No Frappe Query/Script Report exists, so no violation today, but the 126 `frappe.db.sql` sites and the Analytics/Home providers implement their own scoping.

---

## 4. Calibration (known past defects in this domain)

| Defect | Status in current code |
|---|---|
| `**kwargs` transport fields (cmd, csrf_token, _) | **Fixed in NDS**: `departmental_needs/api.py:67-73 _TRANSPORT_FIELDS`/`_command_args`, used by the four `**kwargs` endpoints (:78 save_need_draft, :113, :119, :125). An AST scan of all 648 decorated endpoints found no other whitelisted function declaring `**kwargs`. |
| Intake scope bug (offered out-of-scope FY/department) | **Fixed**: `departmental_needs/services/context.py:140-168 selectable_financial_years` (unit-scoped via `viewing_contexts`), `:170-193 list_need_create_targets` (from `creation_contexts` = `permitted_ou_scopes(author)`), `permissions.py:276-287` (technical status no longer widens creation). **Same class still present** one layer down: F-06/F-08. |
| Strategy universal-read of approved only | **Implemented** in UI contracts (`strategy_authorization.py:225-246 read_scope`; `strategy_ui_contracts.py:72-80,340,476,694,874`) but **not** in the consumer endpoints: F-12. |
| Requisition handoff rename, AGPO denominator, 7-day floor, late-accepted need, catalogue digest, editor race, dropped-doctype `db.exists` | Outside this sweep's domain (no authorization aspect examined). |

## 5. Checked and clean (what was verified correct)

- AUTH resolver: `authorization.py:176-246` (expiry evaluated at resolution, `permitted_ou_scopes` returns empty set for no assignment, never "unrestricted by default"); `:283-333 authorise_record` (technical read only with `PURPOSE_READ`, commands never admitted); `:356-376 require_responsibility`; `:421-453 scope_condition` returns `1=0` on no assignment; `:461-501 has_permission` returns False (not None) to veto — consistent with the Frappe `has_controller_permissions` behaviour recorded in its docstring; `business_role_registry.py` has exactly two scope types and no capability strings.
- Needs/Planning/Requisition/Tender/Budget hooks registered through both hooks: `kentender_procurement/hooks.py:378-451`, `kentender_budget/hooks.py:87-106`; DPP children delegate through the parent chain (`planning_authorization.py:456-494`); Requisition family delegates to root with EXISTS over `Requisition Contributing Unit` (`requisition_authorization.py:296-377`).
- Budget approved-only readers (AO/HOPF) for OVS §4.1 BUD: `budget_read_scope.py:34-72` restricts to Active/Superseded/Closed versions in both hooks.
- Strategy approved reads for AO/HOPF/HoD (OVS §4.1 STR): `strategy_authorization.py:196-246`, `strategy_ui_contracts.py:_version_readable` (:76-80).
- Evaluation read model (OVS §4.1 EVL, §4.2): `bid_evaluation/services/reads.py:23-68` — AO/HOPF status-only before delivery then full frozen version; HoD administrative facts then summary; technical = status then delivered report, never bids; `people.py:11-15` technical users never eligible.
- Award (OVS §4.1 AWD): `award/services/reads.py:176-202` department record; `guards.py:17-35` internal readers; `award/api.py:75-87` supplier notice gated by `_authority`.
- Bid Submission supplier authority is assignment-based and organisation-named per request: `bid_authorization.py:25-45`; content doctypes deny-all (`:78-83`, `hooks.py:736-738`); technical read is metadata-only (`bid_submission/services/technical_read.py:1-17`).
- Bid Opening guest endpoint returns data only for published Tenders and states "Before Start nothing here states or implies the bid count" (`public.py:1-12,31-37`).
- STD Templates: every read service calls `access.require_reader` (`read.py:162,248,466,481`, `lifecycle.py:39`, `concerns.py:73`, `documents.py:38,49`); access resolves only through AUTH or technical (`access.py:40-58`).
- Proceedings register: per-row owner adapters before aggregation (`proceedings/services/register.py:151-165`), totals after verdict.
- Responsibility administration and Organisation structure: administrator check inside the service, actor from session (`responsibility_api.py:1-17`, `responsibility_administration.py:55-82`, `organisation_structure.py:48-56`).
- Technical record search: `technical_search.py:42-47 require_technical` masks to not-found for everyone else.
- Supplier Accounts module (13 endpoints): actor from session, assignment/`authz.require_support_officer`; clean on a read of `access.py:32-60` and API head.
- Strategy UI contracts apply `read_scope` and masked not-found (`strategy_ui_contracts.py:471-483`).
- Frappe User Permission: not read by Needs (`permissions.py:1-8` docstring and grep), Budget, Strategy, Planning, Requisitions or Tenders code (only core legacy files in F-15/F-16).
- `ignore_permissions` in read paths: only the two benign Fiscal Year catalogue reads (F-25); all other occurrences are post-gate service writes (sampled in NDS `lifecycle.py`, BUD `budget_commitment_contracts.py` aside, PLN `budget_revision.py:145-169`, REQ `lifecycle.py:325-355`).
- Unguarded-but-benign: `kentender_budget/api/landing.py` and `procurement_home/api/landing.py` are inert/aliases.

## 6. Not examined (explicit)

- Runtime behaviour of any finding (static only; reproduction sketches provided).
- Individual service bodies of the A\* endpoints beyond the sampled ones (Planning 67, Evaluation 50, Award 18, Tenders 42, Budget 27).
- Vue/browser authorization (server is authoritative; no client bypass reviewed).
- File/attachment reachability after parent denial (AUTH §5.4 last sentence): `File` has no AUTH hook; only the CAS delete guard (`hooks.py:457-460`) — flag for Phase 3.
- Scheduler/background-job principal (`reconcile_role_projections`, sweeps) — run as system; not assessed as an authorization surface.
