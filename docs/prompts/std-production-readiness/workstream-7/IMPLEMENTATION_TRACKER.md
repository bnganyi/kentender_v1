# STD Engine — Security, Permissions, and Audit Hardening — Implementation Tracker

Source of truth:

- [`1. std_engine_security_permissions_and_audit_hardening.md`](1.%20std_engine_security_permissions_and_audit_hardening.md)
- [`2. cursor_pack_security_permissions_and_audit_hardening.md`](2.%20cursor_pack_security_permissions_and_audit_hardening.md)

Status legend: `Not Started` | `In Progress` | `Partial` | `Blocked` | `Done`

**Target code layout (Frappe / this bench):** `kentender_procurement/kentender_procurement/tender_management/security/` — subpackages `permissions`, `authorization`, `action_availability`, `audit`, `evidence` (SEC-0001). **Do not** treat Desk menu visibility as authorization; services remain testable without UI.

**API note:** Cursor pack §21 lists REST-style paths (`POST /api/security/action-availability`, etc.). This bench typically exposes **`@frappe.whitelist`** handlers and `frappe.call` (see root `AGENTS.md`). Tracker evidence should name actual module paths and handler names once implemented.

**Prerequisite workstreams:** Publication readiness (`tender_publication`, PUB-*), STD instance authorization patterns (`std_instance/authorization.py`), publication authorization (`PublicationAuthorizationService`), derived output consumption, and existing audit (`Audit Event`) wiring are **inputs** and **integration targets** for `SEC-1000`—this workstream generalizes and centralizes where the pack requires it, without duplicating every existing gate blindly.

---

## 1) Pre-Implementation Acceptance Gate

Do not treat backend implementation as “complete” until product/engineering accepts the structures below (std engine doc §18 — Completion Gate).

| Gate | Status | Notes |
|---|---|---|
| Canonical roles accepted | Pending | Std engine §4 |
| Permission catalogue accepted | Pending | Std engine §5 |
| Role-permission matrix accepted | Pending | Std engine §6 |
| Object-scope rules accepted | Pending | Std engine §7 |
| State-based authorization rules accepted | Pending | Std engine §8 |
| Action availability service contract accepted | Pending | Std engine §9 |
| Negative permissions accepted | Pending | Std engine §10 |
| Denial code catalogue accepted | Pending | Std engine §11 |
| Audit event catalogue accepted | Pending | Std engine §13 |
| Audit metadata standard accepted | Pending | Std engine §14 |
| Evidence exportability controls accepted | Pending | Std engine §15 |
| Seed pack alignment changes accepted | Pending | Std engine §16 |
| Smoke contracts accepted | Pending | Std engine §17 / pack §20 (`SEC-SMOKE-*`) |

---

## 2) Ordered Implementation Tickets (Execution Sequence)

Implement in **this exact order** from the Cursor pack (section 23 — Implementation Order).

| Order | Ticket | Deliverable | Status | Evidence (tests / notes) |
|---|---|---|---|---|
| 1 | `SEC-0001` | **Package structure** — folders, stubs, import guard test | Done | [`security/`](../../../../kentender_procurement/kentender_procurement/tender_management/security/) — `permissions` (catalog, role_permission, service), `authorization` (denial_codes, decision_engine, object_scope, state_authorization, negative_permissions), `action_availability` (service, catalog, api), `audit` (event_catalog, metadata, event_service, denied_action), `evidence` (export_authorization). Tests: [`test_sec_models_package_structure_0001.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_models_package_structure_0001.py) (1/1). `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_sec_models_package_structure_0001` OK |
| 2 | `SEC-0100` | **Canonical permission catalogue** — idempotent seed / DocType rows; `risk_level`, `audit_required` | Done | DocType [`Security Permission`](../../../../kentender_procurement/kentender_procurement/kentender_procurement/doctype/security_permission/security_permission.json); catalogue [`permissions/catalog.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/permissions/catalog.py); seed [`permissions/seed_catalog.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/permissions/seed_catalog.py); service [`permissions/service.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/permissions/service.py). Tests: [`test_sec_permission_catalog_0100.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_permission_catalog_0100.py) (2/2). `bench --site kentender.midas.com migrate` then `run-tests --module …test_sec_permission_catalog_0100` OK. Seed: `bench --site kentender.midas.com execute kentender_procurement.tender_management.security.permissions.seed_catalog.run` |
| 3 | `SEC-0110` | **Role–permission alignment** — idempotent seed; explicit **non-grants** per role | Done | DocTypes [`Security Role`](../../../../kentender_procurement/kentender_procurement/kentender_procurement/doctype/security_role/security_role.json) + [`Security Role Permission`](../../../../kentender_procurement/kentender_procurement/kentender_procurement/doctype/security_role_permission/security_role_permission.json) (child `assigned_permissions` → `Security Permission`). Matrix [`permissions/role_matrix.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/permissions/role_matrix.py); seed [`permissions/seed_role_matrix.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/permissions/seed_role_matrix.py); service [`permissions/role_permission.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/permissions/role_permission.py) (`RolePermissionService`). Tests: [`test_sec_role_permission_matrix_0110.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_role_permission_matrix_0110.py) (2/2). `bench --site kentender.midas.com migrate` then `run-tests --module …test_sec_role_permission_matrix_0110` OK. Seed: `bench --site kentender.midas.com execute kentender_procurement.tender_management.security.permissions.seed_role_matrix.run` (runs SEC-0100 catalogue seed first) |
| 4 | `SEC-0200` | **Central denial code catalogue** — constants; stable denial object shape; no ad hoc strings in core | Done | [`authorization/denial_codes.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/authorization/denial_codes.py) — `DenialCode` (`StrEnum`), `PACK_SEC_0200_CODES` (35), `EXTENSION_DENIAL_CODES` (`PUBLISH_CONFIGURATION_SNAPSHOT_MISSING`), `build_denial` / `StandardDenialPayload`, `is_known_denial_code`. Wired: [`publication/precondition.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tender_publication/publication/precondition.py), [`authorization/publication_authorization.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tender_publication/authorization/publication_authorization.py) (`TITLE_PUBLISH_PERMISSION_DENIED`), [`audit/codes.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tender_publication/audit/codes.py) (`DENIAL_POST_PUBLICATION_EDIT_ADDENDUM_REQUIRED`), [`derived_models/dem/schema.py`](../../../../kentender_procurement/kentender_procurement/tender_management/derived_models/dem/schema.py), [`derived_models/events/codes.py`](../../../../kentender_procurement/kentender_procurement/tender_management/derived_models/events/codes.py), [`derived_models/consumption/manual_rule_denial.py`](../../../../kentender_procurement/kentender_procurement/tender_management/derived_models/consumption/manual_rule_denial.py). Tests: [`test_sec_denial_codes_0200.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_denial_codes_0200.py) (5/5). `bench --site kentender.midas.com run-tests --module …test_sec_denial_codes_0200` OK; `test_sec_models_package_structure_0001`, `test_pub_authorization_0800` OK. Heavy pub/derived modules may hit unrelated ``TimestampMismatchError`` on shared STD Template when run in parallel with other suites |
| 5 | `SEC-0300` | **`AuthorizationDecisionEngine`** — `evaluate(...)` ordered steps; stable allow/deny JSON | Done | [`authorization/decision_engine.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/authorization/decision_engine.py) (`evaluate`, `AuthorizationEvaluationAllowed` / `AuthorizationEvaluationDenied`); action→PERM registry [`authorization/action_authorization_registry.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/authorization/action_authorization_registry.py) (std engine §9.5 minimum set). Steps 3–8 honor ``context`` hooks for SEC-0310–0330; permission via ``granted_permissions`` or ``security_role_codes`` + `RolePermissionService`. Tests: [`test_sec_authorization_decision_engine_0300.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_authorization_decision_engine_0300.py) (8/8). `bench --site kentender.midas.com run-tests --module …test_sec_authorization_decision_engine_0300` + `test_sec_models_package_structure_0001` OK |
| 6 | `SEC-0310` | **`ObjectScopeService`** — package/tender/instance/template/committee/audit scope asserts | Done | [`authorization/object_scope.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/authorization/object_scope.py) — `check_*` / `assert_*` for package (owner/created_by/approved_by), tender (owner), STD template (governance `*_by` trail), STD instance (instance + tender owner), committee (`register_committee_members` registry + opening/evaluation), audit (`frappe.has_permission` read). `AuthorizationDecisionEngine` step 3: `context["enforce_object_scope"]` + `object_scope_kind` + `object_code` (+ `committee_type` / `object_type` for audit). Tests: [`test_sec_object_scope_service_0310.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_object_scope_service_0310.py) (6/6). `bench --site kentender.midas.com run-tests --module …test_sec_object_scope_service_0310` + `test_sec_authorization_decision_engine_0300` (8/8) OK |
| 7 | `SEC-0320` | **`StateAuthorizationService`** — template/instance/output/snapshot/tender state vs action | Done | [`authorization/state_authorization.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/authorization/state_authorization.py) — `check_*` / `assert_*` + `check(..., kind=, status=)`; engine step 5: `context["state_authorization"]` (`kind`, `status`) before legacy `state_allows`. Tests: [`test_sec_state_authorization_0320.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_state_authorization_0320.py) (13/13). `bench --site kentender.midas.com run-tests --module …test_sec_state_authorization_0320` + `test_sec_authorization_decision_engine_0300` + `test_sec_models_package_structure_0001` OK |
| 8 | `SEC-0330` | **`NegativePermissionService`** — `NEG_*` rules override broad access | Done | [`authorization/negative_permissions.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/authorization/negative_permissions.py) — `evaluate_negative_rules` / `evaluateNegativeRules`, stable `NEG_*` rule ids + :class:`NegativePermissionOutcome`; engine step 7 when ``context["enforce_negative_permission_rules"]`` is true. Extended [`action_authorization_registry.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/authorization/action_authorization_registry.py) with fixture actions (`CONFIGURE_STD_TEMPLATE_MAPPINGS`, `EDIT_WORKS_BOQ_DURING_APPROVAL`, `PERFORM_BOQ_ARITHMETIC_CORRECTION`, `ADD_MANUAL_EVALUATION_CRITERIA`, `SILENT_DCM_CONTRACT_OVERRIDE`). Tests: [`test_sec_negative_permission_rules_0330.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_negative_permission_rules_0330.py) (15/15). `bench --site kentender.midas.com run-tests --module …test_sec_negative_permission_rules_0330` + `test_sec_authorization_decision_engine_0300` + `test_sec_state_authorization_0320` + `test_sec_models_package_structure_0001` OK |
| 9 | `SEC-0400` | **`ActionAvailabilityService`** — `getActionAvailability`; uses engine; no mutation | Done | [`action_availability/service.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/action_availability/service.py) — `get_action_availability` + `getActionAvailability` alias; delegates to `AuthorizationDecisionEngine.evaluate` and returns pack §9/§12 response (`allowed`, `denial_code?`, `required_permission`, `risk_level`, `requires_confirmation`, `audit_on_attempt`, optional `object_state`). [`action_availability/catalog.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/action_availability/catalog.py) defines required action set and startup assertion against registry coverage. Tests: [`test_sec_action_availability_service_0400.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_action_availability_service_0400.py) (5/5). `bench --site kentender.midas.com run-tests --module …test_sec_action_availability_service_0400` + `test_sec_authorization_decision_engine_0300` + `test_sec_negative_permission_rules_0330` + `test_sec_state_authorization_0320` + `test_sec_models_package_structure_0001` OK |
| 10 | `SEC-0410` | **Action availability API** — single + batch; stable error envelope | Done | [`action_availability/api.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/action_availability/api.py) — `sec_api_action_availability` + `sec_api_action_availability_batch` (`@frappe.whitelist`) with session-actor resolution (optional explicit actor), stable error envelope (`success/error_code/message/details`), JSON payload parsing, and internal-error stack-trace suppression. Tests: [`test_sec_action_availability_api_0410.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_action_availability_api_0410.py) (8/8). Regressions: [`test_sec_action_availability_service_0400.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_action_availability_service_0400.py) (5/5), [`test_sec_models_package_structure_0001.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_models_package_structure_0001.py) (1/1). |
| 11 | `SEC-0500` | **Common audit metadata schema** — document / validate shape for emitters | Done | [`security/audit/metadata.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/audit/metadata.py) — canonical `AuditEventMetadata` TypedDict + enums (`AuditEventResult`, `AuditRiskLevel`), `build_audit_metadata`, `normalize_audit_metadata` (legacy alias mapping), and `validate_audit_metadata` (required schema fields, result/risk validation, hash/evidence fields, High/Critical actor reference rule). Exports wired in [`security/audit/__init__.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/audit/__init__.py). Tests: [`test_sec_audit_metadata_schema_0500.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_audit_metadata_schema_0500.py) (5/5). Regressions: `test_sec_models_package_structure_0001` (1/1), `test_sec_action_availability_api_0410` (8/8). |
| 12 | `SEC-0510` | **Audit event catalogue constants** — align with std engine §13 groups | Done | [`security/audit/event_catalog.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/audit/event_catalog.py) — centralized `AuditEventCode` enum + required group sets (`STD_LIBRARY_TEMPLATE_EVENTS`, `RELEASE_EVENTS`, `STD_INSTANCE_COMPLETION_EVENTS`, `DERIVED_MODEL_EVENTS`, `APPROVAL_PUBLICATION_EVENTS`, `EVIDENCE_AUDIT_EVENTS`) + `ALL_AUDIT_EVENT_CODES` / `is_known_audit_event_code`. Wired exports in [`security/audit/__init__.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/audit/__init__.py). Core hardening alignment: derived and publication code tables now import shared constants (`derived_models/events/codes.py`, `tender_publication/audit/codes.py`). Tests: [`test_sec_audit_event_catalog_0510.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_audit_event_catalog_0510.py) (5/5). Regressions: `test_sec_audit_metadata_schema_0500` (5/5), `test_sec_models_package_structure_0001` (1/1). |
| 13 | `SEC-0520` | **`AuditEventService`** (or facade) — append-only record success/denied/failed; query by object/tender | Done | [`security/audit/event_service.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/audit/event_service.py) — `record_success/denied/failed` (+ pack camelCase aliases), metadata validation via SEC-0500 schema, append-only guard (`assert_append_only_operation`), and query methods `get_audit_events_for_object` / `get_audit_events_for_tender` with filter support. Exported via [`security/audit/__init__.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/audit/__init__.py). Tests: [`test_sec_audit_event_service_0520.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_audit_event_service_0520.py) (4/4). Regressions: `test_sec_audit_event_catalog_0510` (5/5), `test_sec_audit_metadata_schema_0500` (5/5), `test_sec_models_package_structure_0001` (1/1). |
| 14 | `SEC-0530` | **`DeniedActionAuditService`** — uniform denied-attempt rows for high/critical | Done | [`security/audit/denied_action.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/audit/denied_action.py) — `record_denied_action` + `recordDeniedAction` alias; enforces high/critical denied attempts are audited (or lower risk when `audit_on_attempt`), persists actor/action/object/denial via `AuditEventService.record_denied`, and maps canonical denied event types (`RELEASE_PERMISSION_DENIED`, `STD_TEMPLATE_EDIT_DENIED`, `MANUAL_RULE_INJECTION_DENIED`, `PUBLICATION_DENIED`, `POST_PUBLICATION_EDIT_DENIED`). Compatibility hardening: `AuditEventService` now falls back `performed_by` to session user when supplied actor does not exist as a `User` link. Tests: [`test_sec_denied_action_audit_service_0530.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_denied_action_audit_service_0530.py) (4/4). Regressions: `test_sec_audit_event_service_0520` (4/4), `test_sec_models_package_structure_0001` (1/1). |
| 15 | `SEC-0600` | **`EvidenceExportAuthorizationService`** — assert + record export; `AUDIT_EXPORT_DENIED` | Done | [`security/evidence/export_authorization.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/evidence/export_authorization.py) — `check/assert_can_export_evidence` (+ pack aliases), role/policy gates (Auditor allowed, Procurement Officer allowed only for assigned tender when policy allows, Approving Authority policy-controlled), denial code `AUDIT_EXPORT_DENIED`, and `record_evidence_export` auditing format + `evidence_package_hash` via `AuditEventService`. Added denial code extension `AUDIT_EXPORT_DENIED` in [`authorization/denial_codes.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/authorization/denial_codes.py). Tests: [`test_sec_evidence_export_authorization_0600.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_evidence_export_authorization_0600.py) (4/4). Regressions: `test_sec_denial_codes_0200` (5/5), `test_sec_denied_action_audit_service_0530` (4/4), `test_sec_models_package_structure_0001` (1/1). |
| 16 | `SEC-0700` | **Security seed fixtures** — `USER-*` users; `NEG-SEC-*` negative cases data | Done | [`security/permissions/seed_security_fixtures_0700.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/permissions/seed_security_fixtures_0700.py) — idempotent fixture user seed (`USER-STD-ADMIN-001`…`USER-SYSADMIN-001`) + canonical `NEG-SEC-001`…`NEG-SEC-008` data for tests (`negative_access_cases`). Exported via [`security/permissions/__init__.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/permissions/__init__.py). Tests: [`test_sec_security_seed_fixtures_0700.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_security_seed_fixtures_0700.py) (3/3). Regressions: `test_sec_role_permission_matrix_0110` (2/2), `test_sec_negative_permission_rules_0330` (15/15), `test_sec_models_package_structure_0001` (1/1). |
| 17 | `SEC-1000` | **Integrate authorization** into critical services (import, release, instance, parameters, works, BOQ, outputs, readiness, submit, approve, publish, consumption, evidence export) | Done | Added SEC-1000 integration shim [`security/authorization/integration.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/authorization/integration.py) and wired it into critical mutation services (`std_template_loader`, release handoff, instance create/parameter/works/BOQ edits, derived output generation, readiness run, submit/approve/publish, output consumption, evidence export). |
| 18 | `SEC-0900` | **Security & audit APIs** — whitelist handlers mirroring pack §21 (action availability, audit query, export-availability) | Done | Added [`security/api.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/api.py) with whitelisted handlers for object/tender audit queries and evidence export-availability, reusing SEC-0410 stable error envelope pattern and session-actor enforcement. |
| 19 | `SEC-0800` | **Smoke: role permissions** — `SEC-SMOKE-ROLE-001` … `009` | Done | Added smoke suite [`test_sec_smoke_role_permissions_0800.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_smoke_role_permissions_0800.py) using seeded users (`SEC-0700`) and backend action availability/authorization outcomes with exact denial codes. |
| 20 | `SEC-0810` | **Smoke: state locks** — `SEC-SMOKE-STATE-001` … `006` | Done | Added smoke suite [`test_sec_smoke_state_locks_0810.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_smoke_state_locks_0810.py) asserting backend state-authorization outcomes for draft/locked/published instance, active template, published output, and final snapshot. |
| 21 | `SEC-0820` | **Smoke: downstream controls** — `SEC-SMOKE-DOWN-001` … `008` | Done | [`test_sec_smoke_downstream_controls_0820.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_smoke_downstream_controls_0820.py) (8/8). `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_sec_smoke_downstream_controls_0820` OK |
| 22 | `SEC-0830` | **Smoke: audit completeness** — `SEC-SMOKE-AUDIT-001` … `006` | Done | [`test_sec_smoke_audit_completeness_0830.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_sec_smoke_audit_completeness_0830.py) (6/6). `enforce_sec_authorization` corrected to call `DeniedActionAuditService.record_denied_action` with the real positional API ([`integration.py`](../../../../kentender_procurement/kentender_procurement/tender_management/security/authorization/integration.py)). `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_sec_smoke_audit_completeness_0830` OK |

---

## 3) Non-Negotiable Rules (Pack §3)

| Rule ID | Pack intent (short) |
|---|---|
| `SEC-RULE-001` | Frontend visibility is not authorization. |
| `SEC-RULE-002` | High-risk/critical mutations backend-authorized. |
| `SEC-RULE-003` | Endpoints enforce even if UI hides. |
| `SEC-RULE-004` | Action availability from backend service. |
| `SEC-RULE-005` | Object state part of authorization. |
| `SEC-RULE-006` | Object scope part of authorization. |
| `SEC-RULE-007` | Negative permissions override broad access. |
| `SEC-RULE-008`–`009` | Published instance / outputs / Final snapshots immutable (addendum path). |
| `SEC-RULE-010` | Manual downstream rule injection denied. |
| `SEC-RULE-011` | Denied legal actions audited. |
| `SEC-RULE-012` | Evidence exports authorized and audited. |
| `SEC-RULE-013` | System Administrator not operational approver/publisher by default. |
| `SEC-RULE-014` | Audit append-only. |

---

## 4) Smoke Test Tracker (`SEC-SMOKE-*`)

Pack section 20 — map each code to a test function under `kentender_procurement/.../tender_management/tests/` (or `security/tests/` if colocated).

### Role (`SEC-SMOKE-ROLE-*`)

| Test code | Status | Evidence (test function name) |
|---|---|---|
| `SEC-SMOKE-ROLE-001` | Done | `test_sec_smoke_role_001_std_admin_import_allowed` |
| `SEC-SMOKE-ROLE-002` | Done | `test_sec_smoke_role_002_std_admin_create_instance_denied` |
| `SEC-SMOKE-ROLE-003` | Done | `test_sec_smoke_role_003_procurement_officer_release_allowed` |
| `SEC-SMOKE-ROLE-004` | Done | `test_sec_smoke_role_004_procurement_officer_template_mapping_denied` |
| `SEC-SMOKE-ROLE-005` | Done | `test_sec_smoke_role_005_procurement_assistant_mark_ready_denied_by_default` |
| `SEC-SMOKE-ROLE-006` | Done | `test_sec_smoke_role_006_approving_authority_approves_allowed` |
| `SEC-SMOKE-ROLE-007` | Done | `test_sec_smoke_role_007_approving_authority_edits_boq_denied` |
| `SEC-SMOKE-ROLE-008` | Done | `test_sec_smoke_role_008_auditor_exports_evidence_allowed` |
| `SEC-SMOKE-ROLE-009` | Done | `test_sec_smoke_role_009_auditor_mutates_instance_denied` |

### State (`SEC-SMOKE-STATE-*`)

| Test code | Status | Evidence |
|---|---|---|
| `SEC-SMOKE-STATE-001` | Done | `test_sec_smoke_state_001_edit_draft_std_instance_allowed` |
| `SEC-SMOKE-STATE-002` | Done | `test_sec_smoke_state_002_edit_locked_for_approval_denied` |
| `SEC-SMOKE-STATE-003` | Done | `test_sec_smoke_state_003_edit_published_instance_denied_addendum_required` |
| `SEC-SMOKE-STATE-004` | Done | `test_sec_smoke_state_004_edit_active_std_template_denied` |
| `SEC-SMOKE-STATE-005` | Done | `test_sec_smoke_state_005_overwrite_published_output_denied` |
| `SEC-SMOKE-STATE-006` | Done | `test_sec_smoke_state_006_modify_final_snapshot_denied` |

### Downstream (`SEC-SMOKE-DOWN-*`)

| Test code | Status | Evidence |
|---|---|---|
| `SEC-SMOKE-DOWN-001` | Done | `test_sec_smoke_down_001_submission_consumes_dsm_allowed` |
| `SEC-SMOKE-DOWN-002` | Done | `test_sec_smoke_down_002_submission_manual_requirement_denied` |
| `SEC-SMOKE-DOWN-003` | Done | `test_sec_smoke_down_003_opening_consumes_dom_allowed` |
| `SEC-SMOKE-DOWN-004` | Done | `test_sec_smoke_down_004_opening_arithmetic_correction_denied` |
| `SEC-SMOKE-DOWN-005` | Done | `test_sec_smoke_down_005_evaluation_consumes_dem_allowed` |
| `SEC-SMOKE-DOWN-006` | Done | `test_sec_smoke_down_006_evaluation_manual_criteria_denied` |
| `SEC-SMOKE-DOWN-007` | Done | `test_sec_smoke_down_007_contract_consumes_dcm_allowed` |
| `SEC-SMOKE-DOWN-008` | Done | `test_sec_smoke_down_008_contract_override_dcm_denied` |

### Audit (`SEC-SMOKE-AUDIT-*`)

| Test code | Status | Evidence |
|---|---|---|
| `SEC-SMOKE-AUDIT-001` | Done | `test_sec_smoke_audit_001_denied_action_creates_audit_event` |
| `SEC-SMOKE-AUDIT-002` | Done | `test_sec_smoke_audit_002_publication_creates_snapshot_and_tender_published_audits` |
| `SEC-SMOKE-AUDIT-003` | Done | `test_sec_smoke_audit_003_evidence_export_audited_with_hash` |
| `SEC-SMOKE-AUDIT-004` | Done | `test_sec_smoke_audit_004_output_generation_audited` |
| `SEC-SMOKE-AUDIT-005` | Done | `test_sec_smoke_audit_005_return_to_preparation_audited` |
| `SEC-SMOKE-AUDIT-006` | Done | `test_sec_smoke_audit_006_addendum_required_denial_audited` |

---

## 5) Definition of Done Checklist (Pack §24)

Mark `[x]` only with automated test evidence (and Playwright **only** if Desk flows are explicitly in scope for a ticket).

- [x] Permission catalogue complete (`SEC-0100`)
- [x] Role-permission seeds aligned (`SEC-0110`)
- [x] Action availability backend implemented (`SEC-0400`)
- [x] Authorization decision engine implemented (`SEC-0300`)
- [x] Object-scope checks implemented (`SEC-0310`)
- [x] State-based authorization implemented (`SEC-0320`)
- [x] Negative permission rules enforced (`SEC-0330`)
- [x] Published immutability enforced (integrates with existing publication lock)
- [x] Manual downstream rule injection denied (`SEC-0820`: manual submission requirement, opening arithmetic correction, manual evaluation criteria, contract DCM override — all denied with stable titles)
- [x] Denied high/critical actions audited (`SEC-0530` + wiring) — `enforce_sec_authorization` records denied attempts via `DeniedActionAuditService` (fix in `integration.py`); smoke `SEC-SMOKE-AUDIT-001` |
- [x] Audit event catalogue implemented (`SEC-0510`)
- [x] Audit metadata standardized (`SEC-0500`)
- [x] Evidence export authorization enforced (`SEC-0600`)
- [ ] Critical services call authorization (`SEC-1000`)
- [x] Security seed fixtures updated (`SEC-0700`)
- [x] `SEC-SMOKE-ROLE-*` pass (`SEC-0800`)
- [x] `SEC-SMOKE-STATE-*` pass (`SEC-0810`)
- [x] `SEC-SMOKE-DOWN-*` pass (`SEC-0820`)
- [x] `SEC-SMOKE-AUDIT-*` pass (`SEC-0830`)

---

## 6) Phase Log

| Date | Ticket / milestone | Change summary | Tests run | Result | Risks / follow-up |
|---|---|---|---|---|---|
| 2026-05-10 | — | Tracker created from std engine §18 + Cursor pack §§4–24 | — | N/A | Resolve §1 gates; align with existing `PublicationAuthorizationService` / `StdAuthorizationService` to avoid duplicate matrices |
| 2026-05-10 | `SEC-0001` | `tender_management/security/` package scaffold + import guard | `test_sec_models_package_structure_0001` (1/1) | Pass | Next: `SEC-0100` permission catalogue |
| 2026-05-09 | `SEC-0100` | `Security Permission` DocType + 45-row canonical seed (`PermissionService.ensure_catalog_seeded` / `seed_catalog.run`) | `test_sec_permission_catalog_0100` (2/2); `test_sec_models_package_structure_0001` (1/1) | Pass | Next: `SEC-0110` role–permission matrix |
| 2026-05-09 | `SEC-0110` | Nine `ROLE_*` rows + child grants from pack §6 / std §6.2; tests assert exact grant sets + explicit non-grants absent | `test_sec_role_permission_matrix_0110` (2/2); `test_sec_models_package_structure_0001` (1/1) | Pass | Next: `SEC-0200` denial codes; optional link Frappe `Role` names to `Security Role.role_code` when wiring `SEC-1000` |
| 2026-05-11 | `SEC-0200` | Central `DenialCode` StrEnum (35 pack §7 + PUB snapshot extension), `build_denial` TypedDict shape; core publication/derived call sites import catalogue | `test_sec_denial_codes_0200` (5/5); `test_sec_models_package_structure_0001` (1/1); `test_pub_authorization_0800` (5/5) | Pass | Remaining ad-hoc titles (e.g. `APPROVAL_DECISION_PERMISSION_DENIED`) out of pack §7 — map in `SEC-0300`/`SEC-1000`; parallel integration runs can hit `TimestampMismatchError` on shared `STD Template` |
| 2026-05-11 | `SEC-0300` | `AuthorizationDecisionEngine.evaluate` + §9.5 action registry; ordered gates with ``context`` for scope/state/negative/policy | `test_sec_authorization_decision_engine_0300` (8/8); `test_sec_models_package_structure_0001` (1/1) | Pass | Next: `SEC-0310` wire `ObjectScopeService` into engine; `SEC-0400` action availability should delegate here |
| 2026-05-11 | `SEC-0310` | `ObjectScopeService` + engine `enforce_object_scope` dispatch; committee in-process registry | `test_sec_object_scope_service_0310` (6/6); `test_sec_authorization_decision_engine_0300` (8/8) | Pass | Next: persist committee assignments; procuring-entity / approval-authority scoping; `SEC-0320` state service |
| 2026-05-09 | `SEC-0320` | `StateAuthorizationService` (template/instance/output/snapshot/tender gates vs §9.5 actions); engine `state_authorization` context | `test_sec_state_authorization_0320` (13/13); `test_sec_authorization_decision_engine_0300` (8/8); `test_sec_models_package_structure_0001` (1/1) | Pass | Next: `SEC-0330` negative rules; wire `state_authorization` from callers in `SEC-1000` |
| 2026-05-09 | `SEC-0330` | `NegativePermissionService` + engine `enforce_negative_permission_rules`; fixture-aligned action codes in registry; `ROLE_CONTRACT_OFFICER` gate for DCM | `test_sec_negative_permission_rules_0330` (15/15); `test_sec_authorization_decision_engine_0300` (8/8); `test_sec_state_authorization_0320` (13/13); `test_sec_models_package_structure_0001` (1/1) | Pass | Next: `SEC-0400` action availability; wire `enforce_negative_permission_rules` from `SEC-1000` |
| 2026-05-11 | `SEC-0400` | `ActionAvailabilityService` implemented as read-only engine facade; response contract includes risk/audit/confirmation + optional object_state; required action catalogue assertion | `test_sec_action_availability_service_0400` (5/5); `test_sec_authorization_decision_engine_0300` (8/8); `test_sec_negative_permission_rules_0330` (15/15); `test_sec_state_authorization_0320` (13/13); `test_sec_models_package_structure_0001` (1/1) | Pass | Next: `SEC-0410` action availability API (single + batch) |
| 2026-05-11 | `SEC-0410` | Action availability API handlers (single + batch) with stable error envelope, session actor resolution, JSON payload parsing, and safe internal-error handling | `test_sec_action_availability_api_0410` (8/8); `test_sec_action_availability_service_0400` (5/5); `test_sec_models_package_structure_0001` (1/1) | Pass | Next: `SEC-0500` common audit metadata schema |
| 2026-05-11 | `SEC-0500` | Common audit metadata schema module with builder/normalizer/validator to map existing emitters to a single contract (including hash/evidence fields and High/Critical actor rule) | `test_sec_audit_metadata_schema_0500` (5/5); `test_sec_models_package_structure_0001` (1/1); `test_sec_action_availability_api_0410` (8/8) | Pass | Next: `SEC-0510` audit event catalogue constants |
| 2026-05-11 | `SEC-0510` | Centralized audit event code catalogue (std §13 groups) and aligned derived/publication pack-code constants to shared source | `test_sec_audit_event_catalog_0510` (5/5); `test_sec_audit_metadata_schema_0500` (5/5); `test_sec_models_package_structure_0001` (1/1) | Pass | Next: `SEC-0520` append-only audit event service |
| 2026-05-11 | `SEC-0520` | Append-only `AuditEventService` for Success/Denied/Failed recording and object/tender queries; SEC-0500 metadata validated before persistence | `test_sec_audit_event_service_0520` (4/4); `test_sec_audit_event_catalog_0510` (5/5); `test_sec_audit_metadata_schema_0500` (5/5); `test_sec_models_package_structure_0001` (1/1) | Pass | Next: `SEC-0530` denied-action audit service |
| 2026-05-11 | `SEC-0530` | `DeniedActionAuditService` records uniform denied-attempt audit rows for high/critical decisions (and lower risk when explicitly audited), including actor/action/object/denial code | `test_sec_denied_action_audit_service_0530` (4/4); `test_sec_audit_event_service_0520` (4/4); `test_sec_models_package_structure_0001` (1/1) | Pass | Next: wire denied-audit calls from engine/service integration (`SEC-1000`) |
| 2026-05-11 | `SEC-0600` | `EvidenceExportAuthorizationService` implemented with role/policy checks, enforced `AUDIT_EXPORT_DENIED`, and export audit recording of format/hash | `test_sec_evidence_export_authorization_0600` (4/4); `test_sec_denial_codes_0200` (5/5); `test_sec_denied_action_audit_service_0530` (4/4); `test_sec_models_package_structure_0001` (1/1) | Pass | Next: `SEC-0700` fixture seeds and/or SEC-1000 integration wiring |
| 2026-05-11 | `SEC-0700` | Security fixture seed for required `USER-*` identities and canonical `NEG-SEC-*` case table; idempotent run for test environments | `test_sec_security_seed_fixtures_0700` (3/3); `test_sec_role_permission_matrix_0110` (2/2); `test_sec_negative_permission_rules_0330` (15/15); `test_sec_models_package_structure_0001` (1/1) | Pass | Next: `SEC-0800`/`SEC-0810` smoke suites and/or `SEC-1000` integration wiring |
| 2026-05-11 | `SEC-1000` | Added centralized `enforce_sec_authorization` integration helper and wired authorization+denied-audit enforcement into critical service entry points across import/release/instance edit/output/readiness/approval/publication/consumption/export paths | `test_sec_integration_authorization_1000` (3/3) | Pass | Next: `SEC-0900` security/audit APIs and smoke suites (`SEC-0800`..`SEC-0830`) |
| 2026-05-11 | `SEC-0900` | Implemented API handlers for audit object/tender queries and evidence export-availability with stable envelope (`success`, `error_code`, `message`, `details`) and no raw exception leakage; action-availability APIs from `SEC-0410` retained as required endpoints | `test_sec_security_audit_apis_0900` (8/8); `test_sec_action_availability_api_0410` (8/8); `test_sec_models_package_structure_0001` (1/1) | Pass | Next: smoke suites `SEC-0800`..`SEC-0830` |
| 2026-05-11 | `SEC-0800` | Implemented role permission smoke suite `SEC-SMOKE-ROLE-001`…`009` against backend authorization outcomes using seeded SEC-0700 fixture users and role contexts; includes exact denial code assertions on denied scenarios | `test_sec_smoke_role_permissions_0800` (9/9); `test_sec_action_availability_service_0400` (5/5); `test_sec_security_seed_fixtures_0700` (3/3) | Pass | Next: `SEC-0810` state lock smoke tests |
| 2026-05-11 | `SEC-0810` | Implemented state lock smoke suite `SEC-SMOKE-STATE-001`…`006` through backend state authorization checks (draft allow; locked/published instance deny; active template deny; published output overwrite deny; final snapshot mutation deny) | `test_sec_smoke_state_locks_0810` (6/6); `test_sec_state_authorization_0320` (13/13); `test_sec_action_availability_service_0400` (5/5) | Pass | Next: `SEC-0820` downstream control smoke tests |
| 2026-05-11 | `SEC-0820` | Downstream control smoke `SEC-SMOKE-DOWN-001`…`008`: published DSM/DOM/DEM/DCM consumption allowed per stage consumer; manual submission requirement, opening BOQ arithmetic correction, manual evaluation criteria, and silent DCM contract override denied with expected denial titles | `test_sec_smoke_downstream_controls_0820` (8/8, ~35s with class-scoped STD seed) | Pass | Next: `SEC-0830` audit completeness smoke tests |
| 2026-05-11 | `SEC-0830` | Audit completeness smoke `SEC-SMOKE-AUDIT-001`…`006`: denied `enforce_sec_authorization` audited; publication snapshot + tender published; evidence export hash; DSM generation audit; return-to-preparation; post-publish denial + addendum notice. Fixed `DeniedActionAuditService.record_denied_action` invocation in `enforce_sec_authorization` (was invalid kwargs, swallowed) | `test_sec_smoke_audit_completeness_0830` (6/6); `test_sec_integration_authorization_1000` (3/3) | Pass | Security smoke sequence complete (`SEC-0800`–`SEC-0830`) |

---

## 7) Explicit Out of Scope (reminder)

From Cursor pack §2.2: IdP, password policy, MFA, network security, encryption key management, backup policy, full SOC/security operations, UI redesign beyond API contracts needed by UI.
