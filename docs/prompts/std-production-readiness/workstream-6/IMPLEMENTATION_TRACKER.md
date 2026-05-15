# STD Engine — Review, Approval, and Publication Readiness — Implementation Tracker

Source of truth:

- `1. std_engine_review_approval_and_publication_readiness.md`
- `2. cursor_pack_review_approval_and_publication_readiness.md`

Status legend: `Not Started` | `In Progress` | `Partial` | `Blocked` | `Done`

**Target code layout (Frappe / this bench):** implement under `kentender_procurement/kentender_procurement/tender_management/` in a dedicated package (suggested: `publication/` or `tender_publication/`) with submodules aligned to the Cursor pack §4 tree: `readiness/`, `approval/`, `snapshot/` (configuration vs publication), `publication/`, `evidence/`, `authorization/`, `audit/`, `api/`, `seeds/`, `tests/`. **Do not** hide legal gates in Desk-only controllers; services must be unit/integration-testable without UI.

**API note:** Cursor pack §17 lists REST-style paths; this bench typically exposes **`@frappe.whitelist`** handlers and `frappe.call` (see `AGENTS.md`, workstream-4 `WORKS-COMP-1000`). Tracker evidence should name actual module paths and handler names once implemented.

**Prerequisite workstreams:** Workstream-5 derived models (`DERIVED-*`), `StdInstanceGeneratedOutputService`, `OutputConsumptionService`, and STD instance publication snapshot patterns (`StdInstanceSnapshotService.create_publication_snapshot`, `test_derived_smoke_x_001_publication_snapshot_all_refs`) are **inputs** to this workstream; this tracker covers **tender-level** readiness, **configuration snapshot before approval**, **approval decisions**, **atomic publish transaction**, **evidence package**, and **PUB-1000** audit codes — not a duplicate of STDINST-only readiness.

---

## 1) Pre-Implementation Acceptance Gate

Do not treat backend implementation as “complete” until product/engineering accepts the structures below (std engine doc §22 — Completion Gate).

| Gate | Status | Notes |
|---|---|---|
| Publication readiness gate model accepted | Pending | Std engine §6 |
| Configuration snapshot before approval accepted | Pending | Std engine §7 |
| Approval review package model accepted | Pending | Std engine §8 |
| Return-to-preparation rules accepted | Pending | Std engine §9 |
| Publication preconditions accepted | Pending | Std engine §10 |
| Publication snapshot model accepted | Pending | Std engine §11 |
| Publication lock / immutability rules accepted | Pending | Std engine §12 |
| Evidence package requirements accepted | Pending | Std engine §14 |
| Post-publication change rules accepted | Pending | Std engine §15 |
| Authorization rules accepted | Pending | Std engine §16 |
| Smoke contracts accepted | Pending | Std engine §20 / pack §20 (`PUB-SMOKE-*`) |

---

## 2) Ordered Implementation Tickets (Execution Sequence)

Implement in **this exact order** from the Cursor pack (section 21 — Implementation Order).

| Order | Ticket | Deliverable | Status | Evidence (tests / notes) |
|---|---|---|---|---|
| 1 | `PUB-0001` | Publication readiness **package structure** (folders, service stubs, test harness) | Done | `kentender_procurement/tender_management/tender_publication/` — subpackages `readiness`, `approval`, `snapshot`, `publication`, `evidence`, `authorization`, `audit`, `api`, `seeds`; stub service classes / `audit/codes.py` docstring reference; no runtime wiring. Tests: `test_pub_models_package_structure_0001.py`. `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_pub_models_package_structure_0001` OK; regression `test_std_inst_readiness_0700` OK. |
| 2 | `PUB-0100` | **Readiness blocker / finding** model — stable codes, severity, `blocks_approval` / `blocks_publication`, resolution text | Done | `tender_publication/readiness/schema.py` — `PUBLICATION_CRITICAL_BLOCKER_CODES` (19), `PUBLICATION_WARNING_CODES` (4), default messages/resolutions/affected areas, `PUBLICATION_READINESS_FINDING_INVALID`, `PUBLICATION_READINESS_BRIDGE_UNKNOWN`; `readiness/validator.py` — `validate_publication_readiness_finding`; `readiness/readiness_finding.py` — `publication_finding_from_code`, `publication_finding_from_std_blocker` + minimal `STD_READINESS_CODE_TO_PUBLICATION_CODE` (no `STALE_OUTPUTS_PRESENT` — caller maps to `*_NOT_CURRENT` in PUB-0110). Tests: `test_pub_readiness_finding_0100.py`. `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_pub_readiness_finding_0100` OK (9/9); `test_pub_models_package_structure_0001` OK. |
| 3 | `PUB-0110` | **`PublicationReadinessService`** — `runReadiness`, `getLatestReadiness`, `assertReadyForApproval`, `assertReadyForPublication`; statuses `Not Run` … `Invalidated`; categories per pack §6 | Done | `tender_publication/readiness/publication_readiness.py` — planning gate (`source_package_code` or linked `Procurement Package` `Released to Tender`), STD binding + `StdInstanceReadinessService.evaluate` (non-persist), stale → `*_NOT_CURRENT`, trace validation, `EvidencePackageService.validate_for_readiness_gate`; in-process latest cache + `clear_publication_readiness_cache`; asserts throw `PUBLICATION_READINESS_GATE_FAILED` (`schema.py`). Tests: `test_pub_readiness_service_0110.py` (7). `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_pub_readiness_service_0110` OK (7/7). Follow-up: wire submit-for-approval (`PUB-CURSOR-RULE-001`); `Incomplete` / `Invalidated` reserved for later tickets |
| 4 | `PUB-0200` | **`ConfigurationSnapshotService`** — `createConfigurationSnapshot`, `getCurrentConfigurationSnapshot`, `invalidateConfigurationSnapshot`; denial `CONFIG_SNAPSHOT_READINESS_REQUIRED`; lock STD/tender for approval | Done | `tender_publication/snapshot/configuration_snapshot.py` — `PublicationReadinessService.runReadiness` must be **Ready** (else ``CONFIG_SNAPSHOT_READINESS_REQUIRED``); advances instance Draft/Validation Blocked → In Configuration → **Ready for Publication** (STDINST-0120, same as WORKS-COMP-0700) then `StdInstanceSnapshotService.create_configuration_snapshot` + `readiness_evidence` in hash + **`readiness_summary_json`** on `Tender STD Instance Snapshot` (PUB-0300 section 4); `StdPublicationLockService.lock_for_approval`. `getCurrentConfigurationSnapshot` / `invalidateConfigurationSnapshot` (Final→Superseded). Tests: `test_pub_configuration_snapshot_0200.py` (5). `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_pub_configuration_snapshot_0200` OK (5/5). **Partial rule-002:** desk submit-for-approval wiring + `Procurement Tender.tender_status` (“Ready for Approval”) deferred |
| 5 | `PUB-0300` | **`ApprovalReviewPackageService.getApprovalReviewPackage`** — read-only sections 1–14 per pack §8 | Done | `tender_publication/approval/approval_review_package.py` — requires current **Final** Configuration snapshot (else ``APPROVAL_REVIEW_CONFIGURATION_SNAPSHOT_REQUIRED``); sections from snapshot **output refs** (5–9), `readiness_summary_json` (4 / 12), hash integrity checks (10–11), `Audit Event` tail (13), action stubs (14). DocType: `Tender STD Instance Snapshot.readiness_summary_json`. Tests: `test_pub_approval_review_package_0300.py` (3). `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_pub_approval_review_package_0300` OK (3/3). **Gap:** PUB-0310 / API must gate **available** actions from review package §14 using same role matrix as PUB-0800 |
| 6 | `PUB-0310` | **`ApprovalDecisionService`** — `approveForPublication`, `returnForCorrection`, `rejectPublication`, `requestClarification`; decision record; **no silent edit** of TDS/SCC/BOQ/outputs | Done | DocType **`Tender Publication Approval Decision`** (append-only); preconditions: current Final configuration snapshot + STD **Locked for Approval** + no critical codes in snapshot `readiness_summary_json` + **PUB-0800** ``assertCanApproveForPublication`` (`{System Manager, Purchase Manager}` or **Administrator**); **approve** records row + `TENDER_PUBLICATION_APPROVAL_GRANTED` `Audit Event` (STD stays locked); **`returnForCorrection`** delegates to **PUB-0320** ``ReturnToPreparationService``; **reject** invalidate snapshot + unlock + `invalidate_readiness_for_tender`; **clarification** record only. Tests: `test_pub_approval_decision_0310.py` (7). Audits use PUB-1000 metadata (`event_code` pack §18) via ``emit_publication_audit_event`` |
| 7 | `PUB-0320` | **`ReturnToPreparationService.returnToPreparation`** — invalidate/supersede configuration snapshot, readiness **Invalidated**, tender/instance state per pack §10 | Done | `tender_publication/approval/return_to_preparation.py` — required payload ``return_reason_code``, ``return_comment``, ``affected_area``, ``criticality`` (``Low``/``Medium``/``High``/``Critical``); optional ``target_instance_status`` → **Validation Blocked** (two-step unlock); decision row + ``TENDER_PUBLICATION_APPROVAL_RETURNED`` + ``TENDER_PUBLICATION_RETURN_TO_PREPARATION`` audits; ``Procurement Tender.tender_status`` → **Configured** (POC vocabulary). ``normalize_return_payload_from_decision_service`` for PUB-0310 legacy callers. Tests: `test_pub_return_to_preparation_0320.py` (4). `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_pub_return_to_preparation_0320` OK (4/4, isolated) |
| 8 | `PUB-0400` | **`PublicationPreconditionService.assertCanPublish`** — pack §11 table + denial codes | Done | ``EvidencePackageService.validateEvidencePackage`` (PUB-0700 publication phase) after readiness **Ready**; output/stale denial titles precede ``EVIDENCE_PACKAGE_FAILED`` in readiness priority. Tests: `test_pub_precondition_0400.py` (9). |
| 9 | `PUB-0500` | **`PublicationSnapshotService`** — `createPublicationSnapshot`, `getPublicationSnapshot`; Final immutability; binds exact output codes | Done | ``insert_publication_snapshots_after_precheck`` uses ``EvidencePackageService.validateEvidencePackage`` + ``evidence_package_code_from_validation`` for ``EVIDENCE|…`` binding. Tests: `test_pub_publication_snapshot_0500.py` (5). |
| 10 | `PUB-0600` | **`PublicationTransactionService.publishTender`** — atomic sequence pack §13 | Done | ``tender_publication/publication/transaction.py`` — explicit **savepoint** + ``rollback`` + **re-raise**. Order: ``_assert_no_final`` → ``assertCanPublish`` → ``insert_publication_snapshots_after_precheck`` → idempotent ``publish_output`` for Bundle–DCM → **``PublicationLockService.markPublishedLocked``** (Final ``Tender Publication Snapshot`` bound to instance) → ``Procurement Tender.tender_status`` = **Published**; ``log_audit_event`` ``TENDER_PUBLICATION_TENDER_PUBLISHED``. **PUB-0400** DB-fresh instance gate; **Auth (PUB-0800):** publish roles `{Procurement Officer, Procurement Manager, Purchase Manager, System Manager}` + **Administrator**. Tests: `test_pub_publication_transaction_0600.py` (3); rollback also asserted in ``PUB-SMOKE-PUBLISH-005`` (`test_pub_smoke_1200`) |
| 11 | `PUB-0610` | **`PublicationLockService`** — pack §14 methods; stable denial audit | Done | ``tender_publication/publication/lock_service.py`` — ``assertNotPublishedLocked``, ``assertCanEditPrePublication``, ``assertAddendumRequired``, ``markPublishedLocked`` (delegates to ``StdPublicationLockService.lock_for_publication`` after snapshot binding check). ``audit/post_publication_denial.py`` + ``TENDER_PUBLICATION_POST_PUBLICATION_EDIT_DENIED`` with metadata ``denial_code`` = ``POST_PUBLICATION_EDIT_DENIED_ADDENDUM_REQUIRED``. ``StdAuthorizationService.assert_can_mutate_published`` emits audit + clearer addendum **ValidationError** title. Mutation paths pass **``attempted_change``** into ``assert_can_edit_draft_instance`` (parameter, BOQ, drawing, works requirements, attachments). Tests: `test_pub_publication_lock_0610.py` (6). Regress: `test_pub_publication_transaction_0600`, `test_std_inst_publication_lock_0600`, `test_std_inst_authorization_1000` |
| 12 | `PUB-0700` | **`EvidencePackageService`** — `assembleEvidencePackage`, `validateEvidencePackage`, `exportEvidencePackage` | Done | ``tender_publication/evidence/evidence_package.py`` — phased validation: **readiness** (artifact checks only; defers planning/output currency to PUB-0110), **publication/export** (full pack §15 checklist incl. planning, lineage, Final configuration snapshot, approval alignment, **Published** outputs + hashes, WORKS ``boq``/``works_requirements`` hashes on snapshot, audit tail, optional Final tender publication snapshot when tender **Published**). Export: ``JSON_MANIFEST``, ``AUDIT_LOG_EXPORT``, ``GENERATED_MODEL_JSON_ARCHIVE``; ``PDF_BUNDLE`` / ``DOCUMENT_ATTACHMENTS_ARCHIVE`` **partial** (stub). **Export auth (PUB-0800):** `{Auditor, Procurement Officer, System Manager, Purchase Manager}` + **Administrator**. Tests: `test_pub_evidence_package_0700.py` (6). Regress: `test_pub_readiness_service_0110`, `test_pub_precondition_0400`, `test_pub_publication_snapshot_0500`, `test_pub_publication_transaction_0600` |
| 13 | `PUB-0800` | **`PublicationAuthorizationService`** — permission mapping + role rules pack §16 | Done | ``tender_publication/authorization/publication_authorization.py`` — role matrix: readiness run (Officer, SM, PM; Assistant excluded); submit snapshot (Officer, SM only); approve/return (SM, PM); publish (Officer, Procurement Manager, PM, SM); evidence export (Auditor, Officer, SM, PM); denial audit ``TENDER_PUBLICATION_AUTHORIZATION_DENIED``. Wired: readiness, configuration snapshot submit, approval decisions, publish precondition, evidence export. Tests: `test_pub_authorization_0800.py` (5). Regress: `test_pub_precondition_0400`, `test_pub_readiness_service_0110`, `test_pub_configuration_snapshot_0200`, `test_pub_approval_decision_0310`, `test_pub_return_to_preparation_0320`, `test_pub_evidence_package_0700`, `test_pub_publication_transaction_0600` — all pass |
| 14 | `PUB-0900` | **Publication API** — whitelist handlers for pack §17 endpoints | Done | `tender_publication/api/handlers.py` — ``pub_api_*`` methods map to pack §17 (readiness run/latest, submit-for-approval → configuration snapshot, review package, approve/return/reject, publish, publication snapshot, evidence validate/export); DERIVED-style ``success`` / ``error_code`` / ``message`` / ``details`` envelope; ``tender_code`` = ``Procurement Tender`` name or unique ``tender_reference`` (``PUB_API_TENDER_AMBIGUOUS`` when duplicate refs); internal errors logged, not returned. Tests: `test_pub_api_0900.py` (9). `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_pub_api_0900` OK |
| 15 | `PUB-1000` | **Publication **audit** events** — codes pack §18 | Done | `audit/codes.py` — `TENDER_PUBLICATION_*` ``event_type`` constants + ``EVENT_TYPE_TO_PACK_EVENT_CODE``; `audit/publication_audit.py` — ``emit_publication_audit_event`` (metadata: pack ``event_code``, ``tender_code``, ``instance_code``, configuration/publication snapshot codes, ``actor``, ``details``). Wired: readiness (Passed/Blocked/Run), configuration snapshot + submit-for-approval, approval review opened, approval decisions (existing types), publish attempted/denied/snapshot/outputs locked/tender published, evidence assembled/exported, post-publication edit + addendum notice, authorization denied metadata. Tests: `test_pub_audit_events_1000.py` (3). Regress: `test_pub_publication_transaction_0600`, `test_pub_approval_decision_0310`, `test_pub_return_to_preparation_0320`, `test_pub_evidence_package_0700`, `test_pub_publication_lock_0610`, `test_pub_readiness_service_0110`, `test_pub_configuration_snapshot_0200`, `test_pub_api_0900`, `test_pub_approval_review_package_0300` |
| 16 | `PUB-1100` | **Seed fixture** — deterministic codes pack §19 + state variants | Done | [`seed_pub_moh_1100.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tender_publication/seeds/seed_pub_moh_1100.py) — `run` / `run_fixture` / `fixture_codes`; variants `ready`, `no_bundle`, `stale_dem`, `no_std_binding`, `approved`, `published`; `PKG-MOH-2026-001` row ensured but tenders omit `procurement_package` (B9 handoff uniqueness; release via `source_package_code`). Tests: [`test_pub_seed_1100.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_pub_seed_1100.py) (8). `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_pub_seed_1100` OK (2026-05-09) |
| 17 | `PUB-1200` | **Smoke tests** — `PUB-SMOKE-*` pack §20 | Done | [`test_pub_smoke_1200.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_pub_smoke_1200.py) — 22 tests named `test_PUB_SMOKE_*`; readiness (001–006) uses PUB-1100 seed + local fixtures; approval/publication/post-publication assert stable titles (`CONFIG_SNAPSHOT_READINESS_REQUIRED`, `PUBLISH_APPROVAL_REQUIRED`, `PUBLISH_OUTPUT_STALE`, …) and rollback (`PUB-SMOKE-PUBLISH-003` / `005`); consumption + evidence export. `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_pub_smoke_1200` OK (22/22, 2026-05-10) |

**Regression anchor (while building PUB-*):** keep green: `test_derived_smoke_1300`, `test_derived_consumption_0800`, `test_std_inst_readiness_0700`, `test_works_comp_snapshot_lock_0700`, `test_std_inst_generated_output_0400`.

**Existing primitives (integration points — not substitutes for full PUB layer):**

| Area | Location | Relevance to PUB-* |
|---|---|---|
| STD instance readiness | `std_instance/readiness.py` — `StdInstanceReadinessService` | Overlaps **check categories**; PUB-0110 should compose or wrap and emit **pack-normalized** findings |
| Approval / publication locks | `std_instance/publication_lock.py` — `StdPublicationLockService` | PUB-0200 / PUB-0610 alignment |
| Publication snapshot (STD + tender) | `std_instance/snapshot.py` — `create_publication_snapshot`; **PUB-0500** — `PublicationSnapshotService` + ``Tender Publication Snapshot`` | PUB-0600 composes STD Publication row + tender publication envelope |
| Output publish + consumption | `std_instance/generated_output.py`, `derived_models/consumption/output_consumption.py` | PUB-0600 step “mark outputs Published” |
| Seed choreography | `derived_models/seeds/seed_derived_moh_1200.py` | Demonstrates publish path for **derived outputs**; PUB-1100 should add **approval + configuration snapshot** states |

---

## 3) Non-Negotiable Rule Compliance Checklist

Map to Cursor pack §3 (`PUB-CURSOR-RULE-*`) and std engine §5 (`PUB-RULE-*`).  
**Status legend:** **Done** = implemented + automated test evidence. **Partial** = building block exists but tender-level gate / audit / API incomplete. **Pending** = not implemented.

| Rule ID | Pack intent (short) | Status | Evidence / notes |
|---|---|---|---|
| `PUB-CURSOR-RULE-001` | No submit for approval unless readiness **Ready**. | Pending | PUB-0110 + submit handler |
| `PUB-CURSOR-RULE-002` | Configuration snapshot required before approval review. | Partial | `ConfigurationSnapshotService` + tests (PUB-0200); **gap:** submit-for-approval / review package must call service and refuse without current snapshot (PUB-0300 / wiring) |
| `PUB-CURSOR-RULE-003` | Approver sees **snapshot**, not mutable draft. | Pending | PUB-0300 + snapshot binding |
| `PUB-CURSOR-RULE-004` | Approver cannot silently edit tender/STD content. | Partial | PUB-0310 decision service performs **no** TDS/SCC/BOQ/output writes; PUB-0800 enforces decider vs submitter roles on services; desk/API must call services only |
| `PUB-CURSOR-RULE-005` | Return invalidates / supersedes approval snapshot. | Pending | PUB-0320 |
| `PUB-CURSOR-RULE-006` | No publish unless approval **Approved**. | Partial | PUB-0400 + **PUB-0600** ``publishTender``; desk/API wiring still pending |
| `PUB-CURSOR-RULE-007` | No publish without Bundle, DSM, DOM, DEM, DCM **current**. | Partial | PUB-0400 + PUB-0600 output publish idempotency |
| `PUB-CURSOR-RULE-008` | No publish with **stale** generated outputs. | Partial | PUB-0400; PUB-0600 inherits same gate |
| `PUB-CURSOR-RULE-009` | Publication snapshot required **before or atomically during** publish. | Partial | PUB-0500 + PUB-0600 savepoint-bound insert before lock/tender status |
| `PUB-CURSOR-RULE-010` | Published STD Instance immutable. | **Done** | PUB-0600/0610: **Published Locked** + ``PublicationLockService`` gates; denials audited |
| `PUB-CURSOR-RULE-011` | Published outputs immutable. | Partial | `generated_output` doc validate; TDS/BOQ/drawing denials + audit — PUB-0610 |
| `PUB-CURSOR-RULE-012` | Publication transaction atomic — no partial published state. | **Done** | PUB-0600 savepoint + `test_pub_publication_transaction_0600`; **PUB-SMOKE-PUBLISH-003** / **005** in `test_pub_smoke_1200` |
| `PUB-CURSOR-RULE-013` | Post-publication direct edits denied; addendum/reissue. | **Done** | ``POST_PUBLICATION_EDIT_DENIED_ADDENDUM_REQUIRED`` + ``TENDER_PUBLICATION_POST_PUBLICATION_EDIT_DENIED`` audit; TDS/BOQ/drawing paths — `test_pub_publication_lock_0610` |
| `PUB-CURSOR-RULE-014` | Evidence package assembleable for published tender. | **Partial** | ``assembleEvidencePackage`` / ``exportEvidencePackage`` — `test_pub_evidence_package_0700`; export permissions PUB-0800; PDF/attachments export stubs remain |
| `PUB-CURSOR-RULE-015` | Denials and transitions audited. | **Done** | PUB-1000 emitters across readiness, submit, review, approval, publish transaction, evidence, post-pub denial + addendum notice; PUB-0610 — `test_pub_audit_events_1000`, `test_pub_publication_lock_0610`; pack §20 smoke — `test_pub_smoke_1200` (`PUB-SMOKE-POST-002` asserts ``POST_PUBLICATION_EDIT_DENIED_ADDENDUM_REQUIRED`` metadata) |

---

## 4) Blocker, Denial, and Audit Code Coverage

Track implementation and test coverage for codes from std engine §6.4–§6.5, pack §5–§11, §18.

### 4.1 Critical readiness blockers (representative)

| Code | Implemented | Test | Notes |
|---|---|---|---|
| `RELEASE_RECORD_MISSING` | ☑ | ☑ | Constants + factory in `readiness/schema.py` / `readiness_finding.py`; `test_pub_readiness_finding_0100` |
| `STD_BINDING_MISSING` | ☑ | ☑ | Same |
| `STD_INSTANCE_MISSING` / `STD_INSTANCE_NOT_READY` | ☑ | ☑ | Same; PUB-0110 bridges from STD readiness |
| `TEMPLATE_LINEAGE_INVALID` | ☑ | ☑ | Same |
| `TDS_INCOMPLETE` / `SCC_INCOMPLETE` / … | ☑ | ☑ | Pack §5 critical set covered by `PUBLICATION_CRITICAL_BLOCKER_CODES` |
| `BUNDLE_NOT_CURRENT` … `DCM_NOT_CURRENT` | ☑ | ☑ | Same; STD `*_MISSING` → `*_NOT_CURRENT` via `STD_READINESS_CODE_TO_PUBLICATION_CODE` |
| `OUTPUT_TRACE_MISSING` | ☑ | ☑ | Same |
| `SNAPSHOT_CREATION_FAILED` | ☑ | ☑ | Same |
| `APPROVAL_REQUIRED` | ☑ | ☑ | Same |
| `EVIDENCE_PACKAGE_FAILED` | ☑ | ☑ | Same; `PUB-SMOKE-READY-006` — `test_PUB_SMOKE_READY_006_evidence_gate_failure_blocked` |
| Pack §5 warning codes (`AUDIT_*`, `SOURCE_HASH_*`, …) | ☑ | ☑ | `PUBLICATION_WARNING_CODES`; default non-blocking in factory |
| `PUBLICATION_READINESS_BRIDGE_UNKNOWN` | ☑ | ☑ | `test_pub_0100_std_bridge_unknown_raises` |

### 4.2 Publication denial codes (pack §11)

| Code | Implemented | Test |
|---|---|---|
| `PUBLISH_PERMISSION_DENIED` | ☑ | ☑ `test_pub_precondition_0400` |
| `PUBLISH_APPROVAL_REQUIRED` | ☑ | ☑ `test_pub_precondition_0400`; `PUB-SMOKE-PUBLISH-002` — `test_PUB_SMOKE_PUBLISH_002_publish_without_approval_denied` |
| `PUBLISH_READINESS_NOT_READY` | ☑ | ☑ `test_pub_precondition_0400` (`test_pub_0400_readiness_not_ready_generic`) |
| `PUBLISH_OUTPUT_STALE` | ☑ | ☑ `test_pub_precondition_0400` |
| `PUBLISH_OUTPUT_MISSING` | ☑ | ☑ `test_pub_precondition_0400` |
| `PUBLISH_EVIDENCE_PACKAGE_FAILED` | ☑ | ☑ `test_pub_precondition_0400` |
| `PUBLISH_CONFIGURATION_SNAPSHOT_MISSING` | ☑ | ☑ `test_pub_precondition_0400` |

### 4.3 Other stable codes

| Code | Implemented | Test |
|---|---|---|
| `PUBLICATION_READINESS_FINDING_INVALID` | ☑ | `test_pub_readiness_finding_0100` |
| `PUBLICATION_READINESS_BRIDGE_UNKNOWN` | ☑ | `test_pub_0100_std_bridge_unknown_raises` |
| `CONFIG_SNAPSHOT_READINESS_REQUIRED` | ☑ | `test_pub_0200_create_denied_when_readiness_not_ready` |
| `APPROVAL_REVIEW_CONFIGURATION_SNAPSHOT_REQUIRED` | ☑ | `test_pub_0300_requires_configuration_snapshot` |
| `APPROVAL_DECISION_PRECONDITION_FAILED` / `APPROVAL_DECISION_READINESS_BLOCKERS_PRESENT` / `APPROVAL_DECISION_PERMISSION_DENIED` / `APPROVAL_DECISION_ALREADY_APPROVED` / `APPROVAL_DECISION_STATE_CONFLICT` / `APPROVAL_DECISION_PAYLOAD_INVALID` | ☑ | `test_pub_approval_decision_0310` |
| `RETURN_TO_PREPARATION_PAYLOAD_INVALID` | ☑ | `test_pub_return_to_preparation_0320` |
| `PUBLICATION_SNAPSHOT_ALREADY_FINAL` | ☑ | `test_pub_publication_snapshot_0500` |
| `PUBLICATION_SNAPSHOT_CONFIGURATION_INVALID` | ☑ | (implicit in service; no isolated test) |
| `PUBLICATION_SNAPSHOT_OUTPUT_STALE` / `PUBLICATION_SNAPSHOT_OUTPUT_MISSING` / `PUBLICATION_SNAPSHOT_OUTPUT_INVALID` | ☑ | Service enforcement after precondition; no isolated unit test (``PUBLISH_OUTPUT_STALE`` covers stale path first) |
| `TENDER_PUBLICATION_TENDER_PUBLISHED` (audit ``event_type``) | ☑ | `test_pub_publication_transaction_0600`; metadata ``event_code`` = ``TENDER_PUBLISHED`` (PUB-1000) |
| `POST_PUBLICATION_EDIT_DENIED_ADDENDUM_REQUIRED` (metadata ``denial_code``) | ☑ | `test_pub_publication_lock_0610`; `PUB-SMOKE-POST-002` — `test_PUB_SMOKE_POST_002_edit_boq_denied` |
| `TENDER_PUBLICATION_POST_PUBLICATION_EDIT_DENIED` (audit ``event_type``) | ☑ | `test_pub_publication_lock_0610` |
| `TENDER_PUBLICATION_AUTHORIZATION_DENIED` (audit ``event_type``) | ☑ | `test_pub_authorization_0800` |
| Pack §18 publication audit catalogue (via ``metadata.event_code`` + ``event_type``) | ☑ | `test_pub_audit_events_1000`; smoke transitions + post-pub denial — `test_pub_smoke_1200` |

_Add rows for any new stable codes introduced during implementation._

---

## 5) Smoke Test Tracker (`PUB-1200`)

Pack section 20 — map each `PUB-SMOKE-*` to a test function under `kentender_procurement/.../tender_management/tests/`.

### Readiness (`PUB-SMOKE-READY-*`)

| Test code | Status | Evidence (test function name) |
|---|---|---|
| `PUB-SMOKE-READY-001` | Done | `test_PUB_SMOKE_READY_001_complete_tender_readiness_ready` |
| `PUB-SMOKE-READY-002` | Done | `test_PUB_SMOKE_READY_002_missing_bundle_blocked` |
| `PUB-SMOKE-READY-003` | Done | `test_PUB_SMOKE_READY_003_stale_dem_blocked` |
| `PUB-SMOKE-READY-004` | Done | `test_PUB_SMOKE_READY_004_missing_std_binding_blocked` |
| `PUB-SMOKE-READY-005` | Done | `test_PUB_SMOKE_READY_005_missing_release_record_blocked` |
| `PUB-SMOKE-READY-006` | Done | `test_PUB_SMOKE_READY_006_evidence_gate_failure_blocked` |

### Approval (`PUB-SMOKE-APP-*`)

| Test code | Status | Evidence |
|---|---|---|
| `PUB-SMOKE-APP-001` | Done | `test_PUB_SMOKE_APP_001_submit_ready_tender_configuration_snapshot` |
| `PUB-SMOKE-APP-002` | Done | `test_PUB_SMOKE_APP_002_submit_blocked_tender_denied` |
| `PUB-SMOKE-APP-003` | Done | `test_PUB_SMOKE_APP_003_approver_boq_edit_denied` |
| `PUB-SMOKE-APP-004` | Done | `test_PUB_SMOKE_APP_004_return_invalidates_snapshot` |
| `PUB-SMOKE-APP-005` | Done | `test_PUB_SMOKE_APP_005_approver_approves` |

### Publication (`PUB-SMOKE-PUBLISH-*`)

| Test code | Status | Evidence |
|---|---|---|
| `PUB-SMOKE-PUBLISH-001` | Done | `test_PUB_SMOKE_PUBLISH_001_publish_approved_tender` |
| `PUB-SMOKE-PUBLISH-002` | Done | `test_PUB_SMOKE_PUBLISH_002_publish_without_approval_denied` |
| `PUB-SMOKE-PUBLISH-003` | Done | `test_PUB_SMOKE_PUBLISH_003_snapshot_insert_failure_rollback` |
| `PUB-SMOKE-PUBLISH-004` | Done | `test_PUB_SMOKE_PUBLISH_004_publish_stale_dsm_denied` |
| `PUB-SMOKE-PUBLISH-005` | Done | `test_PUB_SMOKE_PUBLISH_005_partial_failure_rollback` |

### Post-publication (`PUB-SMOKE-POST-*`)

| Test code | Status | Evidence |
|---|---|---|
| `PUB-SMOKE-POST-001` | Done | `test_PUB_SMOKE_POST_001_edit_tds_denied` |
| `PUB-SMOKE-POST-002` | Done | `test_PUB_SMOKE_POST_002_edit_boq_denied` |
| `PUB-SMOKE-POST-003` | Done | `test_PUB_SMOKE_POST_003_replace_drawing_denied` |
| `PUB-SMOKE-POST-004` | Done | `test_PUB_SMOKE_POST_004_consume_published_dsm_submission_allowed` |
| `PUB-SMOKE-POST-005` | Done | `test_PUB_SMOKE_POST_005_consume_published_dem_evaluation_allowed` |
| `PUB-SMOKE-POST-006` | Done | `test_PUB_SMOKE_POST_006_export_evidence_allowed` |

---

## 6) Definition of Done Checklist

From Cursor pack §22. Mark `[x]` only with automated test evidence (and Playwright **only** if Desk submit/approve/publish flows are in scope for the ticket).

- [ ] Readiness blocks incomplete tender.
- [ ] Configuration snapshot required before approval.
- [ ] Approval package is read-only.
- [ ] Approver cannot silently edit content.
- [ ] Return invalidates snapshot/readiness.
- [ ] Publication requires approval.
- [ ] Publication requires current Bundle/DSM/DOM/DEM/DCM.
- [ ] Publication snapshot created and immutable when Final.
- [ ] Publication transaction atomic.
- [ ] Outputs marked Published; STD Instance Published Locked.
- [ ] Direct post-publication edits denied.
- [ ] Evidence assemble/export works.
- [ ] Authorization enforced.
- [x] Audit events (`PUB-1000` codes) implemented.
- [x] Seed fixtures load idempotently (`PUB-1100` — `test_pub_seed_1100`).
- [x] Smoke tests (`PUB-SMOKE-*`) pass (`test_pub_smoke_1200` — pack §20).

---

## 7) Phase Log

| Date | Ticket / milestone | Change summary | Tests run | Result | Risks / follow-up |
|---|---|---|---|---|---|
| 2026-05-10 | — | Tracker created from std engine + Cursor pack; execution order = pack §21 | — | N/A | Resolve §1 gates; decide tender-level snapshot DocType vs extending STD snapshot; align blocker codes with existing `readiness.py` |
| 2026-05-10 | `PUB-0001` | Scaffolded `tender_publication` package + `test_pub_models_package_structure_0001` import guard | `test_pub_models_package_structure_0001`; `test_std_inst_readiness_0700` | Pass | Next: `PUB-0100` readiness finding model |
| 2026-05-10 | `PUB-0100` | Readiness finding schema, validator, factory, STD→pack bridge subset | `test_pub_readiness_finding_0100`; `test_pub_models_package_structure_0001` | Pass (9/9) | Next: `PUB-0110` `PublicationReadinessService` |
| 2026-05-10 | `PUB-0110` | `PublicationReadinessService` (planning + STD readiness + traces + evidence hook); `EvidencePackageService.validate_for_readiness_gate` stub | `test_pub_readiness_service_0110` | Pass (7/7) | Next: `PUB-0200` configuration snapshot; integrate asserts into approval submit when ready |
| 2026-05-10 | `PUB-0200` | `ConfigurationSnapshotService` (readiness gate, STD Configuration snapshot, lock for approval, get current, invalidate supersede) | `test_pub_configuration_snapshot_0200`; `test_pub_models_package_structure_0001` | Pass (5/5) | Next: `PUB-0300` review package from snapshot; wire submit-for-approval; optional `Procurement Tender` status for “Ready for Approval” |
| 2026-05-10 | `PUB-0300` | `ApprovalReviewPackageService.getApprovalReviewPackage`; `readiness_summary_json` on `Tender STD Instance Snapshot`; fingerprint extended | `test_pub_approval_review_package_0300`; `test_pub_configuration_snapshot_0200`; `test_works_comp_snapshot_lock_0700`; `test_std_inst_snapshot_0500` | Pass | Next: `PUB-0310` decisions + gate section 14 actions; migrate other sites for new snapshot field |
| 2026-05-10 | `PUB-0310` | `ApprovalDecisionService` + `Tender Publication Approval Decision`; audit events; return/reject unlock + snapshot supersede; `invalidate_readiness_for_tender`; review package §14 action flags | `test_pub_approval_decision_0310`; `test_pub_approval_review_package_0300` | Pass (7/7) | Next: `PUB-0320` dedicated return orchestration vs current inline; migrate sites for new DocType |
| 2026-05-10 | `PUB-0320` | `ReturnToPreparationService.returnToPreparation` + strict pack payload; `returnForCorrection` delegates; dual audit codes | `test_pub_return_to_preparation_0320`; `test_pub_approval_decision_0310` | Pass | Next: `PUB-0400` publication preconditions |
| 2026-05-10 | `PUB-0400` | `PublicationPreconditionService.assertCanPublish` + pack §11 denial titles | `test_pub_precondition_0400` (9/9) | Pass | Next: `PUB-0500` tender-level publication snapshot; wire `PUB-0600` to call preconditions |
| 2026-05-10 | `PUB-0500` | DocType ``Tender Publication Snapshot`` + ``PublicationSnapshotService`` (STD Publication row + tender envelope, Final immutability) | `test_pub_publication_snapshot_0500` (5/5); `test_pub_precondition_0400`; migrate | Pass | Next: `PUB-0600` atomic `publishTender` calling preconditions + this service; PUB-0700 evidence codes |
| 2026-05-10 | `PUB-0600` | ``PublicationTransactionService.publishTender`` + savepoint rollback/re-raise; tender **Published**; audit ``TENDER_PUBLICATION_TENDER_PUBLISHED``; PUB-0400 DB-fresh instance gate; ``Purchase Manager`` in ``PUBLISH_ROLES`` | `test_pub_publication_transaction_0600` (3/3); `test_pub_0500`; `test_pub_0400`; `test_std_inst_readiness_0700` | Pass | Next: PUB-0610 post-publish denials; PUB-1000 catalogue alignment; PUB-1200 smoke |
| 2026-05-10 | `PUB-0610` | ``PublicationLockService`` (pack §14); ``markPublishedLocked`` in PUB-0600; ``emit_post_publication_edit_denied_audit``; ``attempted_change`` on draft-edit asserts for TDS/BOQ/drawing/works/attachments | `test_pub_publication_lock_0610` (6/6); `test_pub_publication_transaction_0600`; `test_std_inst_publication_lock_0600`; `test_std_inst_authorization_1000`; `test_pub_models_package_structure_0001` | Pass | Next: PUB-0700 evidence; PUB-1000 catalogue; PUB-1200 smoke (`PUB-SMOKE-POST-*`) |
| 2026-05-10 | `PUB-0700` | ``EvidencePackageService`` — phased validate, assemble, export; PUB-0400/0500 wire ``validateEvidencePackage``; readiness finding priority tweak | `test_pub_evidence_package_0700` (6/6); `test_pub_readiness_service_0110`; `test_pub_precondition_0400`; `test_pub_publication_snapshot_0500`; `test_pub_publication_transaction_0600` | Pass | Next: PUB-0800 export permissions; real PDF/attachment archives; PUB-1200 smoke |
| 2026-05-10 | `PUB-0800` | ``PublicationAuthorizationService`` — pack §16 role matrix; denial audit ``TENDER_PUBLICATION_AUTHORIZATION_DENIED``; wired readiness, snapshot submit, decisions, publish precondition, evidence export | `test_pub_authorization_0800` (5/5); regress: `test_pub_precondition_0400`, `test_pub_readiness_service_0110`, `test_pub_configuration_snapshot_0200`, `test_pub_approval_decision_0310`, `test_pub_return_to_preparation_0320`, `test_pub_evidence_package_0700`, `test_pub_publication_transaction_0600` | Pass | Purchase Manager no longer submits configuration snapshot (Officer/SM only); PUB-0900 API must mirror same asserts |
| 2026-05-10 | `PUB-0900` | Whitelist ``pub_api_*`` publication endpoints (pack §17) + stable error envelope; tender resolution by name or ``tender_reference`` | `test_pub_api_0900` (9/9) | Pass | Next: PUB-1000 audit catalogue; PUB-1200 smoke; optional REST router if product needs non-``frappe.call`` URLs |
| 2026-05-10 | `PUB-1000` | ``emit_publication_audit_event`` + pack §18 ``event_code`` metadata; wired readiness, snapshot/submit, review opened, publish sequence (attempted/denied/snapshots/outputs/lock/published), evidence assemble/export, addendum notice, auth denial enrichment | `test_pub_audit_events_1000` (3/3); regress pub modules (0600, 0310, 0320, 0700, 0610, 0800, 0200, 0110, 0900, 0300) | Pass | PUB-1200 smoke still maps ``PUB-SMOKE-*`` to row-level assertions |
| 2026-05-09 | `PUB-1100` | `seed_pub_moh_1100`: six publication-readiness variants + idempotent `run`/`run_fixture`; deterministic `TND-MOH-PUB1100-*` / `STDINST-*` / `GB-…` names (coexistence with STDINST-1400); no `procurement_package` on fixture tenders | `test_pub_seed_1100` (8/8) | Pass | Next: `PUB-1200` pack §20 smoke matrix |
| 2026-05-10 | `PUB-1200` | `test_pub_smoke_1200`: 22 integration tests mapping pack §20 `PUB-SMOKE-*` (readiness via PUB-1100 seed + local fixtures; approval/publication/post-publication; rollback 003/005; `OutputConsumptionService` Submission/Evaluation; evidence JSON export) | `test_pub_smoke_1200` (22/22) | Pass | Desk/UI Playwright for submit/approve/publish still out of scope |

---

## 8) Explicit Out of Scope (reminder)

From Cursor pack §2.2: full Tender module v2 UI, full Procurement Officer UI, supplier portal publication display, submission/opening/evaluation/contract **operational UIs**, full addendum workflow UI, external portal integrations unless already present. **In scope:** backend gates, snapshots, locks, evidence, authorization, audits, seeds, automated tests — **not** the publish button UI until pack §21 dependencies are stable.
