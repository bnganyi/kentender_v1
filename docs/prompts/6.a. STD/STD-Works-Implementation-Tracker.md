# STD Engine Works v2 - Implementation Tracker

**Prompt pack:** `apps/kentender_v1/docs/prompts/6.a. STD/1...10`  
**Cursor pack:** `apps/kentender_v1/docs/prompts/6.a. STD/10. std_engine_works_configuration_cursor_implementation_pack.md`  
**Source PDF:** `apps/kentender_v1/docs/prompts/6.a. STD/DOC 1. STD FOR WORKS-BUILDING AND ASSOCIATED CIVIL ENGINEERING WORKS Rev April 2022.pdf`

## Scope guard (current execution)

- Phase 0 planning artifacts are complete and retained as baseline.
- Current approved execution scope: **Phase 1 through Phase 12 STD-CURSOR-1206** (Smoke Contract automation suite + UI smoke; Phase 13+ next).
- Keep all unapproved tickets in `Pending` status until explicit approval.

## Execution order (from Cursor pack)

`0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11 -> 12 -> 13`

## Quality gate checklist (hard rule)

Mark a ticket/phase as **Done** only when all applicable checks pass:

- [ ] TDD evidence present for changed behavior.
- [ ] Service/API tests include happy + negative/permission paths.
- [ ] Playwright validation executed for affected Desk/UI UX.
- [ ] Regression tests added first for bug fixes.
- [ ] Tracker updated with evidence, assumptions, and residual risks.

## Ticket status

**Last updated:** 2026-04-29 (through Phase 11 STD-CURSOR-1108; Phases 1–10 as previously executed)

### Phase 0 - Reconnaissance and planning baseline

| Ticket | Description | Status |
|---|---|---|
| STD-CURSOR-0001 | Inspect existing procurement/tender behavior and produce inventory | Done (planning artifact complete) |
| STD-CURSOR-0002 | Define feature flag transition strategy (`std_engine_v2_enabled`) | Done (planning artifact complete) |

### Phase 1 - Core data model and migrations

| Ticket | Description | Status |
|---|---|---|
| STD-CURSOR-0101 | Source document registry model | Done |
| STD-CURSOR-0102 | Template family model | Done |
| STD-CURSOR-0103 | Template version model | Done |
| STD-CURSOR-0104 | Applicability profile model | Done |
| STD-CURSOR-0105 | Part/section/clause models | Done |
| STD-CURSOR-0106 | Parameter/dependency models | Done |
| STD-CURSOR-0107 | Form models | Done |
| STD-CURSOR-0108 | Works requirements/BOQ models | Done |
| STD-CURSOR-0109 | Mapping/output/readiness/addendum/audit models | Done |

### Phase 2 - DOC1 seed package and loader (reference only)

| Ticket | Description | Status |
|---|---|---|
| STD-CURSOR-0201 | Modular seed package directory | Done |
| STD-CURSOR-0202 | Seed manifest schema | Done |
| STD-CURSOR-0203 | Populate seed files from seed spec | Done |
| STD-CURSOR-0204 | Seed loader service | Done |
| STD-CURSOR-0205 | Seed validation command | Done |

### Phase 3 - Governance, authorization, audit (reference only)

| Ticket | Description | Status |
|---|---|---|
| STD-CURSOR-0301 | State transition service | Done |
| STD-CURSOR-0302 | Server-side authorization service | Done |
| STD-CURSOR-0303 | Audit service | Done |

### Phase 4 - STD instance services (reference only)

| Ticket | Description | Status |
|---|---|---|
| STD-CURSOR-0401 | Eligible template query service | Done |
| STD-CURSOR-0402 | Create STD instance service | Done |
| STD-CURSOR-0403 | Parameter value service | Done |
| STD-CURSOR-0404 | Section attachment service | Done |

### Phase 5 - Works requirements and BOQ engine (reference only)

| Ticket | Description | Status |
|---|---|---|
| STD-CURSOR-0501 | Works requirements service | Done |
| STD-CURSOR-0502 | BOQ instance service | Done |
| STD-CURSOR-0503 | BOQ structured import | Done |

### Phase 6 - Generation engine (reference only)

| Ticket | Description | Status |
|---|---|---|
| STD-CURSOR-0601 | Generation job framework | Done |
| STD-CURSOR-0602 | Bundle generator | Done |
| STD-CURSOR-0603 | DSM generator | Done |
| STD-CURSOR-0604 | DOM generator | Done |
| STD-CURSOR-0605 | DEM generator | Done |
| STD-CURSOR-0606 | DCM generator | Done |

### Phase 7 - Readiness validator (reference only)

| Ticket | Description | Status |
|---|---|---|
| STD-CURSOR-0701 | Readiness rule engine | Done |
| STD-CURSOR-0702 | Stale output detection | Done |

### Phase 8 - Addendum impact/regeneration (reference only)

| Ticket | Description | Status |
|---|---|---|
| STD-CURSOR-0801 | Addendum impact analyzer | Done |
| STD-CURSOR-0802 | Addendum regeneration service | Done |

### Phase 9 - Tender Management integration refactor (reference only)

| Ticket | Description | Status |
|---|---|---|
| STD-CURSOR-0901 | STD binding to Tender Management v2 | Done |
| STD-CURSOR-0902 | Disable manual submission requirements | Done |
| STD-CURSOR-0903 | Disable manual evaluation criteria | Done |
| STD-CURSOR-0904 | Disable manual opening fields outside DOM | Done |
| STD-CURSOR-0905 | Bind Contract Management to DCM | Done |

### Phase 10 - STD workbench UI (reference only)

| Ticket | Description | Status |
|---|---|---|
| STD-CURSOR-1001 | Workbench route and shell | Done |
| STD-CURSOR-1002 | KPI/risk strip | Done |
| STD-CURSOR-1003 | Scope tabs and queue bar | Done |
| STD-CURSOR-1004 | Search and filters | Done |
| STD-CURSOR-1005 | Object list panel | Done |
| STD-CURSOR-1006 | Detail panel and action bar | Done |
| STD-CURSOR-1007 | Template version detail tabs | Done |
| STD-CURSOR-1008 | Structure tab | Done |
| STD-CURSOR-1009 | Parameters tab | Done |
| STD-CURSOR-1010 | Forms tab | Done |
| STD-CURSOR-1011 | Works configuration tab | Done |
| STD-CURSOR-1012 | Mappings tab | Done |
| STD-CURSOR-1013 | Reviews and approval tab | Done |
| STD-CURSOR-1014 | Audit and evidence tab | Done |

### Phase 11 - TM integration UI (reference only)

| Ticket | Description | Status |
|---|---|---|
| STD-CURSOR-1101 | STD instance detail tabs | Done |
| STD-CURSOR-1102 | Instance parameters UI | Done |
| STD-CURSOR-1103 | Works requirements UI | Done |
| STD-CURSOR-1104 | BOQ configuration UI | Done |
| STD-CURSOR-1105 | Generated outputs preview UI | Done |
| STD-CURSOR-1106 | Readiness UI | Done |
| STD-CURSOR-1107 | Addendum impact UI | Done |
| STD-CURSOR-1108 | TM v2 STD panel integration UI | Done |

### Phase 12 - Smoke contract automation

| Ticket | Description | Status |
|---|---|---|
| STD-CURSOR-1201 | Seed load smoke tests | Done |
| STD-CURSOR-1202 | Locked section and parameter tests | Done |
| STD-CURSOR-1203 | DSM/DOM/DEM/DCM/BOQ tests | Done |
| STD-CURSOR-1204 | Bundle/readiness/addendum tests | Done |
| STD-CURSOR-1205 | Cross-module and negative regression tests | Done |
| STD-CURSOR-1206 | UI smoke tests | Done |

### Phase 13 - Hardening and evidence export (reference only)

| Ticket | Description | Status |
|---|---|---|
| STD-CURSOR-1301 | Evidence export service | Done |
| STD-CURSOR-1302 | Production safety checks | Done |

## Decision log pointers

- See `apps/kentender_v1/docs/implementation/std_engine/01_decision_log.md`.

## Blockers and dependencies register

| Item | Type | Status | Owner | Notes |
|---|---|---|---|---|
| DOC1 complete text extraction QA | Dependency | Open | Phase 2 owner | Required before legal-grade seed sign-off |
| Feature-flag transition governance | Dependency | Open | Phase 0 owner | Defined in `01_decision_log.md` and `02_environment_and_test_matrix.md` |
| Smoke environment readiness | Dependency | Open | Phase 0 owner | Playwright/browser/site matrix required before Phase 12 execution |

## Progress log (append per update)

| Field | Value |
|---|---|
| Date | |
| Ticket(s) | |
| Reviewer | |
| Completed | |
| Not completed | |
| Assumptions | |
| Files changed | |
| Test evidence | |
| Risks remaining | |
| Ready for next ticket | Yes / No |

### Progress entries

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | Phase 0 tracker foundation |
| Reviewer | Engineering |
| Completed | Created tracker with Cursor phase/ticket map, quality gates, blockers register, and progress log template. |
| Not completed | No runtime implementation (by scope). |
| Assumptions | Phase 1+ remains reference-only until explicit approval. |
| Files changed | `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | Documentation-only change; no runtime tests applicable. |
| Risks remaining | Phase 1+ still pending formal execution and test evidence. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0303 |
| Reviewer | Engineering |
| Completed | Implemented audit service `record_std_audit_event(event_type, object_type, object_code, actor=None, previous_state=None, new_state=None, reason=None, denial_code=None, metadata=None)` with stable `AUD-*` event code generation, required event-type catalog enforcement, actor and role capture, state transition context capture, denial/reason payload capture, and metadata persistence. Added read API `get_std_audit_events(object_type=None, object_code=None, limit=50)` with explicit authorized-role gating and deterministic filtering/sorting. Upgraded `STD Audit Event` DocType with audit payload fields and strengthened append-only model protection to block both updates and deletes. |
| Not completed | Full evidence-export endpoint wiring and downstream consumer integrations are deferred to later phase tickets; this ticket delivers foundational append-only audit write/read services and policy gates. |
| Assumptions | `System Manager`, `Administrator`, and `Auditor` are the authorized roles for audit read access in current governance scope; role matrix can be extended when compliance scope expands. |
| Files changed | `kentender_procurement/kentender_procurement/std_engine/services/audit_service.py`, `kentender_procurement/kentender_procurement/std_engine/services/__init__.py`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_audit_event/std_audit_event.json`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_audit_event/std_audit_event.py`, `kentender_procurement/kentender_procurement/std_engine/tests/test_std_audit_service.py`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | `bench --site kentender.midas.com reload-doc procurement_planning doctype std_audit_event` + `./scripts/bench-with-node.sh --site kentender.midas.com migrate` (pass), `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_audit_service` (3/3 pass). Regression safety: `...test_std_state_transition_service` (4/4 pass), `...test_std_authorization_service` (5/5 pass). |
| Risks remaining | Audit payload is currently stored as JSON text fields without schema versioning/signature; tamper-evidence and long-term evidentiary packaging controls remain to be added in future audit hardening tickets. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0001 |
| Reviewer | Engineering |
| Completed | Produced evidence-based existing-state inventory with concrete model/service/API/UI/handoff references and explicit gap analysis. |
| Not completed | No code refactor performed (planning-only scope). |
| Assumptions | Inventory reflects current repository state at review time. |
| Files changed | `docs/implementation/std_engine/00_existing_state_inventory.md` |
| Test evidence | Read-only reconnaissance; no runtime tests applicable. |
| Risks remaining | Future implementation must revalidate inventory before Phase 1 start if baseline changes. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0002 |
| Reviewer | Engineering |
| Completed | Defined feature-flag transition strategy (`std_engine_v2_enabled`) with on/off contract, staged rollout, guardrails, and evidence prerequisites. |
| Not completed | Flag not implemented in runtime (planning-only scope). |
| Assumptions | Future implementation will choose concrete storage/scope mechanism. |
| Files changed | `docs/implementation/std_engine/05_feature_flag_transition_strategy.md` |
| Test evidence | Planning artifact only; runtime tests deferred to execution phases. |
| Risks remaining | Implementation decisions on flag storage/scope remain open. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0101 |
| Reviewer | Engineering |
| Completed | Added `Source Document Registry` DocType/model with required metadata fields, unique `source_document_code`, and deletion guard for template-version references. |
| Not completed | No Phase 1 tickets beyond `STD-CURSOR-0101` were started. |
| Assumptions | Concrete `STD Template Version` model arrives in later tickets; delete guard is forward-compatible and activated when that DocType exists. |
| Files changed | `kentender_procurement/procurement_planning/doctype/source_document_registry/source_document_registry.json`, `kentender_procurement/procurement_planning/doctype/source_document_registry/source_document_registry.py`, `kentender_procurement/std_engine/tests/test_source_document_registry.py` |
| Test evidence | `bench --site kentender.midas.com migrate` (pass), `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_source_document_registry` (3/3 pass). |
| Risks remaining | Reference-delete enforcement currently relies on forward-compatible app guard until the concrete template-version FK is introduced. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0102 |
| Reviewer | Engineering |
| Completed | Added `STD Template Family` DocType/model with required fields, unique `template_code`, active-state consistency guard, archive dependency guard, and audit event emission hooks for create/status change. |
| Not completed | No Phase 1 tickets beyond `STD-CURSOR-0102` were started. |
| Assumptions | Active dependency checks target a future `STD Template Version` DocType and enforce when available. |
| Files changed | `kentender_procurement/procurement_planning/doctype/std_template_family/std_template_family.json`, `kentender_procurement/procurement_planning/doctype/std_template_family/std_template_family.py`, `kentender_procurement/std_engine/tests/test_std_template_family.py` |
| Test evidence | `bench --site kentender.midas.com migrate` (pass), `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_template_family` (4/4 pass). |
| Risks remaining | Audit is currently logger-based and will be superseded by append-only audit records in later audit-model tickets. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0103 |
| Reviewer | Engineering |
| Completed | Added `STD Template Version` DocType/model with required fields, version/source links, status stack, lineage fields, active-version consistency guard, active immutability guard, delete protection for instance references, and status/create audit emission hooks. |
| Not completed | No Phase 1 tickets beyond `STD-CURSOR-0103` were started. |
| Assumptions | `STD Instance` and governance services are introduced in later tickets; reference and transition checks are forward-compatible until those surfaces exist. |
| Files changed | `kentender_procurement/procurement_planning/doctype/std_template_version/std_template_version.json`, `kentender_procurement/procurement_planning/doctype/std_template_version/std_template_version.py`, `kentender_procurement/std_engine/tests/test_std_template_version.py` |
| Test evidence | `bench --site kentender.midas.com migrate` (pass), `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_template_version` (6/6 pass), regression: `...test_source_document_registry` (3/3 pass), `...test_std_template_family` (4/4 pass). |
| Risks remaining | Immutability transition whitelist is a baseline and may need tightening when centralized governance transition service lands. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0104 |
| Reviewer | Engineering |
| Completed | Added `STD Applicability Profile` DocType/model with required fields and status enum, version compatibility/category validation, and active profile immutability guard. |
| Not completed | No tickets beyond `STD-CURSOR-0104` were started before closeout. |
| Assumptions | Profile-to-version compatibility remains strict by procurement category until later tender-method orchestration tickets add richer compatibility services. |
| Files changed | `kentender_procurement/procurement_planning/doctype/std_applicability_profile/std_applicability_profile.json`, `kentender_procurement/procurement_planning/doctype/std_applicability_profile/std_applicability_profile.py`, `kentender_procurement/std_engine/tests/test_std_applicability_profile.py` |
| Test evidence | `bench --site kentender.midas.com migrate` (pass), `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_applicability_profile` (4/4 pass), regression: `...test_source_document_registry` (3/3 pass), `...test_std_template_family` (4/4 pass), `...test_std_template_version` (6/6 pass). |
| Risks remaining | Active profile immutability currently allows status transitions only via model-level whitelist pending centralized governance transition service. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0105 |
| Reviewer | Engineering |
| Completed | Added hierarchy DocTypes/models for `STD Part Definition`, `STD Section Definition`, and `STD Clause Definition` with referential integrity checks, section/clause editability validation, locked-clause instance edit guard, and clause source trace enforcement. |
| Not completed | No tickets beyond `STD-CURSOR-0105` were started before closeout. |
| Assumptions | Section editability/locking is represented at model level now; downstream UI/API enforcement will harden in later tickets. |
| Files changed | `kentender_procurement/procurement_planning/doctype/std_part_definition/std_part_definition.json`, `kentender_procurement/procurement_planning/doctype/std_part_definition/std_part_definition.py`, `kentender_procurement/procurement_planning/doctype/std_section_definition/std_section_definition.json`, `kentender_procurement/procurement_planning/doctype/std_section_definition/std_section_definition.py`, `kentender_procurement/procurement_planning/doctype/std_clause_definition/std_clause_definition.json`, `kentender_procurement/procurement_planning/doctype/std_clause_definition/std_clause_definition.py`, `kentender_procurement/std_engine/tests/test_std_structure_definitions.py` |
| Test evidence | `bench --site kentender.midas.com migrate` (pass), `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_structure_definitions` (pass), cumulative regression: `...test_std_applicability_profile`, `...test_source_document_registry`, `...test_std_template_family`, `...test_std_template_version` (all pass). |
| Risks remaining | Clause source-trace rule currently validates page/hash presence but does not yet enforce richer provenance semantics planned for seed/governance phases. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0106 |
| Reviewer | Engineering |
| Completed | Added `STD Parameter Definition` and `STD Parameter Dependency` DocTypes/models with required field sets, data-type/effect enum validation, dependency link integrity checks, trigger value validation, and version/section/source reference validation. |
| Not completed | No tickets beyond `STD-CURSOR-0106` were started before closeout. |
| Assumptions | Readiness blocking semantics for missing required parameters are represented structurally and will be enforced by dedicated readiness services in later phases. |
| Files changed | `kentender_procurement/procurement_planning/doctype/std_parameter_definition/std_parameter_definition.json`, `kentender_procurement/procurement_planning/doctype/std_parameter_definition/std_parameter_definition.py`, `kentender_procurement/procurement_planning/doctype/std_parameter_dependency/std_parameter_dependency.json`, `kentender_procurement/procurement_planning/doctype/std_parameter_dependency/std_parameter_dependency.py`, `kentender_procurement/std_engine/tests/test_std_parameters.py` |
| Test evidence | `bench --site kentender.midas.com migrate` (pass), `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_parameters` (pass), cumulative regression: `...test_std_structure_definitions`, `...test_std_applicability_profile`, `...test_source_document_registry`, `...test_std_template_family`, `...test_std_template_version` (all pass). |
| Risks remaining | Parameter dependency expression semantics are syntactic at this phase; full evaluation engine behavior arrives in service-layer tickets. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0107 |
| Reviewer | Engineering |
| Completed | Added `STD Form Definition` and `STD Form Field Definition` DocTypes/models with required fields, completion-role enum validation, version/section/source link validation, field schema checks (`field_key`, `data_type`, `order_index`), and supplier/submission-driving flags persisted for downstream model generation. |
| Not completed | No tickets beyond `STD-CURSOR-0107` were started before closeout. |
| Assumptions | DSM/DEM/DCM generation behavior is represented via model flags now and will be enforced by generation services in later phases. |
| Files changed | `kentender_procurement/procurement_planning/doctype/std_form_definition/std_form_definition.json`, `kentender_procurement/procurement_planning/doctype/std_form_definition/std_form_definition.py`, `kentender_procurement/procurement_planning/doctype/std_form_field_definition/std_form_field_definition.json`, `kentender_procurement/procurement_planning/doctype/std_form_field_definition/std_form_field_definition.py`, `kentender_procurement/std_engine/tests/test_std_forms.py` |
| Test evidence | `bench --site kentender.midas.com migrate` (pass), `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_forms` (pass), cumulative regression: `...test_std_parameters`, `...test_std_structure_definitions`, `...test_std_applicability_profile`, `...test_source_document_registry`, `...test_std_template_family`, `...test_std_template_version` (all pass). |
| Risks remaining | Form semantics are structurally validated; full business-rule evaluation and readiness coupling remains for later service/readiness tickets. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0108 |
| Reviewer | Engineering |
| Completed | Added `STD Works Requirement Component Definition`, `STD BOQ Definition`, `STD BOQ Bill Definition`, and `STD BOQ Item Schema Definition` DocTypes/models with Works BOQ ownership constraints, arithmetic correction stage enforcement, BOQ linkage integrity, and quantity-field non-editability guard for supplier input semantics. |
| Not completed | No tickets beyond `STD-CURSOR-0108` were started before closeout. |
| Assumptions | BOQ computational semantics are represented by schema fields/rules now; runtime calculation and readiness enforcement are implemented in later generation/readiness services. |
| Files changed | `kentender_procurement/procurement_planning/doctype/std_works_requirement_component_definition/std_works_requirement_component_definition.json`, `kentender_procurement/procurement_planning/doctype/std_works_requirement_component_definition/std_works_requirement_component_definition.py`, `kentender_procurement/procurement_planning/doctype/std_boq_definition/std_boq_definition.json`, `kentender_procurement/procurement_planning/doctype/std_boq_definition/std_boq_definition.py`, `kentender_procurement/procurement_planning/doctype/std_boq_bill_definition/std_boq_bill_definition.json`, `kentender_procurement/procurement_planning/doctype/std_boq_bill_definition/std_boq_bill_definition.py`, `kentender_procurement/procurement_planning/doctype/std_boq_item_schema_definition/std_boq_item_schema_definition.json`, `kentender_procurement/procurement_planning/doctype/std_boq_item_schema_definition/std_boq_item_schema_definition.py`, `kentender_procurement/std_engine/tests/test_std_works_boq.py` |
| Test evidence | `bench --site kentender.midas.com migrate` (pass), `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_works_boq` (pass), cumulative regression: `...test_std_forms`, `...test_std_parameters`, `...test_std_structure_definitions`, `...test_std_applicability_profile`, `...test_source_document_registry`, `...test_std_template_family`, `...test_std_template_version` (all pass). |
| Risks remaining | BOQ input-mode and schema constraints are structural at this phase; downstream submission/evaluation behavior lockouts will be enforced in integration and generator tickets. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0109 |
| Reviewer | Engineering |
| Completed | Added foundational runtime graph models for mapping/output/readiness/addendum/audit (`STD Extraction Mapping`, `STD Instance`, `STD Generated Output`, `STD Generation Job`, `STD Readiness Run`, `STD Readiness Finding`, `STD Addendum Impact Analysis`, `STD Audit Event`) and validated cross-model creation flow via integration tests. Added append-only baseline protection for audit records (`STD Audit Event` delete blocked). |
| Not completed | Extended runtime models beyond foundational baseline (e.g., detailed generated payload snapshots, full supersession graph semantics, and full addendum linkage depth) remain for later tickets/phases. |
| Assumptions | Foundational 0109 model layer is intentionally minimal and schema-centric; service-layer orchestration and richer lifecycle transitions are deferred to subsequent implementation phases. |
| Files changed | `kentender_procurement/procurement_planning/doctype/std_extraction_mapping/*`, `kentender_procurement/procurement_planning/doctype/std_instance/*`, `kentender_procurement/procurement_planning/doctype/std_generated_output/*`, `kentender_procurement/procurement_planning/doctype/std_generation_job/*`, `kentender_procurement/procurement_planning/doctype/std_readiness_run/*`, `kentender_procurement/procurement_planning/doctype/std_readiness_finding/*`, `kentender_procurement/procurement_planning/doctype/std_addendum_impact_analysis/*`, `kentender_procurement/procurement_planning/doctype/std_audit_event/*`, `kentender_procurement/std_engine/tests/test_std_runtime_models.py` |
| Test evidence | `bench --site kentender.midas.com migrate` (pass), `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_runtime_models` (1/1 pass), cumulative regression pass: `...test_std_works_boq` (3/3), `...test_std_forms` (4/4), `...test_std_parameters` (4/4), `...test_std_structure_definitions` (4/4), `...test_std_applicability_profile` (4/4), `...test_source_document_registry` (3/3), `...test_std_template_family` (4/4), `...test_std_template_version` (6/6). |
| Risks remaining | Append-only/readiness governance is baseline at model level only; deeper immutability/event-signing/impact-diff behavior remains for later governance and workflow tickets. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0201 |
| Reviewer | Engineering |
| Completed | Created modular DOC1 seed package directory scaffold under `kentender_procurement/kentender_procurement/fixtures/std_engine/works_building_rev_apr_2022` with all required phase files and subdirectories (`07_clauses`, `08_parameters`, `09_forms`, `11_boq`, `14_extraction_mappings`). Added deterministic `00_manifest.yaml` load-order references for all required files and placeholder-safe YAML content in each file with explicit deferred extraction markers. Added focused structure validation tests to assert root existence, required file completeness, and manifest discovery references. |
| Not completed | Manifest schema enforcement and semantic validation are deferred to `STD-CURSOR-0202`; payload population is deferred to `STD-CURSOR-0203`; loader integration is deferred to `STD-CURSOR-0204/0205`. |
| Assumptions | Canonical in-repo package root for this app is `kentender_procurement/kentender_procurement/fixtures/std_engine/works_building_rev_apr_2022`; loader path from pack (`apps/procurement/...`) is normalized to current app layout. |
| Files changed | `kentender_procurement/kentender_procurement/fixtures/std_engine/works_building_rev_apr_2022/**`, `kentender_procurement/kentender_procurement/std_engine/tests/test_std_seed_package_structure.py` |
| Test evidence | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_seed_package_structure` (3/3 pass). Regression safety: `...test_source_document_registry` (3/3), `...test_std_template_family` (4/4), `...test_std_template_version` (6/6), `...test_std_applicability_profile` (4/4), `...test_std_structure_definitions` (4/4), `...test_std_parameters` (4/4), `...test_std_forms` (4/4), `...test_std_works_boq` (3/3), `...test_std_runtime_models` (1/1) all pass. |
| Risks remaining | Placeholder content is intentionally non-authoritative; downstream tickets must prevent accidental production use before semantic population and loader validation complete. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0202 |
| Reviewer | Engineering |
| Completed | Implemented strict manifest schema validation module for DOC1 seed package with deterministic required key and load-order contract checks, `manifest_code == idempotency_key` enforcement, and missing path detection for load entries. Normalized `00_manifest.yaml` to the `0202` required shape using grouped directory entries (`07_clauses`, `08_parameters`, `09_forms`, `11_boq`, `14_extraction_mappings`). Added focused schema tests for valid/invalid manifest scenarios. |
| Not completed | Loader-level idempotent execution and CLI wiring remain deferred to `STD-CURSOR-0204` and `STD-CURSOR-0205`; semantic data population remains deferred to `STD-CURSOR-0203`. |
| Assumptions | Ticket `0202` contract is authoritative for manifest shape and grouped load-order entries even when finer-grained file paths exist in the package scaffold. |
| Files changed | `kentender_procurement/kentender_procurement/std_engine/seed/manifest_schema.py`, `kentender_procurement/kentender_procurement/std_engine/seed/__init__.py`, `kentender_procurement/kentender_procurement/std_engine/tests/test_std_seed_manifest_schema.py`, `kentender_procurement/kentender_procurement/std_engine/tests/test_std_seed_package_structure.py`, `kentender_procurement/kentender_procurement/fixtures/std_engine/works_building_rev_apr_2022/00_manifest.yaml` |
| Test evidence | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_seed_manifest_schema` (6/6 pass), `...test_std_seed_package_structure` (3/3 pass), regression safety: `...test_source_document_registry` (3/3), `...test_std_template_family` (4/4), `...test_std_template_version` (6/6), `...test_std_applicability_profile` (4/4), `...test_std_structure_definitions` (4/4), `...test_std_parameters` (4/4), `...test_std_forms` (4/4), `...test_std_works_boq` (3/3), `...test_std_runtime_models` (1/1) all pass. |
| Risks remaining | Manifest schema currently validates contract and file/discovery integrity only; semantic payload validation and duplicate-load execution behavior are enforced in subsequent tickets. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0203 |
| Reviewer | Engineering |
| Completed | Populated modular DOC1 seed files with structured records sourced from the seed specification for source document, template family/version, applicability profile, parts, sections, clause indices, parameter sets, forms, works requirements, BOQ definition/bills/schema/dayworks/summary, evaluation and carry-forward seeds, extraction mappings, readiness rules, seed instance fixture, output expectations, addendum fixture, and smoke expectations. Legal-text-bearing files keep `text_verbatim: null` with `extraction_status: Pending Human-Reviewed Extraction` to satisfy non-invention requirements. |
| Not completed | Complete verbatim legal text extraction for ITT/forms/GCC/SCC/contract forms remains pending human-reviewed extraction QA; loader/idempotent execution and CLI validation remain in `STD-CURSOR-0204/0205`. |
| Assumptions | Seed content remains structural and authoritative for model scaffolding; legal text completeness gates are explicitly deferred per specification extraction requirements. |
| Files changed | `kentender_procurement/kentender_procurement/fixtures/std_engine/works_building_rev_apr_2022/01_source_documents.yaml` through `19_smoke_expected_results.yaml` (excluding manifest), `kentender_procurement/kentender_procurement/std_engine/tests/test_std_seed_population_0203.py` |
| Test evidence | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_seed_population_0203` (3/3 pass), regression: `...test_std_seed_manifest_schema` (6/6 pass), `...test_std_seed_package_structure` (3/3 pass). |
| Risks remaining | Seed detail depth still depends on final legal extraction pass; until extraction completion, downstream consumers must treat placeholder legal text fields as non-final and non-authoritative text payloads. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0204 |
| Reviewer | Engineering |
| Completed | Implemented `load_std_seed_package(package_path, *, dry_run=False, force=False)` in `std_engine.seed.loader` with manifest validation pre-check, grouped load-order discovery, YAML payload processing, DocType mapping/upsert behavior, deterministic report output, and commit on non-dry runs. Added idempotency-by-content comparison, JSON/check-field normalization, immutable/non-draft mutation guards, and explicit error handling (`SeedLoadError`) for missing manifest and unsafe mutations. |
| Not completed | Full semantic loaders for future model groups not yet present in current Phase 1/2 schema remain deferred; CLI wrapper command is deferred to `STD-CURSOR-0205`. |
| Assumptions | Unknown seed groups (without current mapped Doctypes) are intentionally ignored at this ticket stage; mapped groups cover currently available STD models. |
| Files changed | `kentender_procurement/kentender_procurement/std_engine/seed/loader.py`, `kentender_procurement/kentender_procurement/std_engine/tests/test_std_seed_loader.py` |
| Test evidence | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_seed_loader` (4/4 pass). Regression safety: `...test_std_seed_population_0203` (3/3 pass), `...test_std_seed_manifest_schema` (6/6 pass), `...test_std_seed_package_structure` (3/3 pass). |
| Risks remaining | Loader currently provides structural and idempotency guard behavior; deep domain semantic validation and full cross-model load choreography for later-phase objects will need expansion as additional tickets introduce those models/services. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0205 |
| Reviewer | Engineering |
| Completed | Implemented seed validation command entrypoint `validate_seed_package(package_path)` (whitelisted and exportable via `bench execute`) with checks for manifest validity, file presence, unique business codes, reference resolution, mandatory section coverage, ITT/GCC locked editability, TDS/SCC parameter-only editability, required DEM/DSM mapping presence, BOQ definition presence, SCC parameter presence, readiness rule presence, and placeholder legal-text ban (`sample text`, `lorem ipsum`). Added precise path-aware failures for missing required groups (e.g., BOQ path hint). |
| Not completed | Loader invocation wiring into a dedicated CLI command wrapper remains optional; current implementation is callable via `bench execute` through module path and does not add custom click command surface. |
| Assumptions | Command path equivalence uses `kentender_procurement.std_engine.seed.validate_seed_package` within this app layout as the framework-equivalent of the pack example command namespace. |
| Files changed | `kentender_procurement/kentender_procurement/std_engine/seed/validator.py`, `kentender_procurement/kentender_procurement/std_engine/seed/__init__.py`, `kentender_procurement/kentender_procurement/std_engine/tests/test_std_seed_validation_command.py` |
| Test evidence | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_seed_validation_command` (3/3 pass). Regression safety: `...test_std_seed_loader` (4/4), `...test_std_seed_population_0203` (3/3), `...test_std_seed_manifest_schema` (6/6), `...test_std_seed_package_structure` (3/3) all pass. |
| Risks remaining | Validation command currently enforces structural and selected semantic invariants from available seed/model context; deeper legal extraction QA and full cross-phase semantic gates remain dependent on subsequent governance and smoke-contract tickets. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0301 |
| Reviewer | Engineering |
| Completed | Implemented centralized transition service `transition_std_object(object_type, object_code, action_code, actor, reason=None, context=None)` with object/state mapping for template family, template version, applicability profile, STD instance, generated outputs, generation jobs, readiness runs, and addendum impact analyses. Added transition rule table, role checks, separation-of-duties checks, precondition checks (including version review/structure and readiness requirements), atomic state application through service context flag, stable denial codes, and success/denial audit event emission via `STD Audit Event`. |
| Not completed | Full authorization matrix and rich denial semantics across all policy dimensions are deferred to `STD-CURSOR-0302`; expanded audit payload model and service enhancements are deferred to `STD-CURSOR-0303`. |
| Assumptions | Service-level transition ownership is enforced by status-field guards in current status-bearing DocTypes; future status-bearing models should adopt the same guard utility. |
| Files changed | `kentender_procurement/kentender_procurement/std_engine/services/state_transition_service.py`, `kentender_procurement/kentender_procurement/std_engine/state_transition_guard.py`, `kentender_procurement/kentender_procurement/std_engine/services/__init__.py`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_template_family/std_template_family.py`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_template_version/std_template_version.py`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_applicability_profile/std_applicability_profile.py`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_instance/std_instance.py`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_generated_output/std_generated_output.py`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_generation_job/std_generation_job.py`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_readiness_run/std_readiness_run.py`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_addendum_impact_analysis/std_addendum_impact_analysis.py`, `kentender_procurement/kentender_procurement/std_engine/tests/test_std_state_transition_service.py` |
| Test evidence | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_state_transition_service` (4/4 pass). Regression safety: `...test_std_seed_validation_command` (3/3), `...test_std_seed_loader` (4/4), `...test_std_runtime_models` (1/1) all pass. |
| Risks remaining | Transition coverage currently focuses on foundational action set and core preconditions; broader workflow graph and state-policy combinations require follow-on expansion in authorization/audit tickets. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0302 |
| Reviewer | Engineering |
| Completed | Implemented server-side authorization service `check_std_permission(actor, action_code, object_type, object_code=None, context=None)` with stable response contract (`allowed`, `action_code`, `denial_code`, `message`, `requires_reason`, `requires_confirmation`, `risk_level`). Enforced required policy areas: active template immutability, published instance immutability, generated output immutability, audit immutability, role permission checks, separation-of-duties via context, template/profile active checks for instance creation, addendum requirement, model-generation requirement, and source-of-truth ownership checks. Integrated transition service to consume authorization decisions, preserving stable denial behavior expected by transition tests. |
| Not completed | UI action availability and API endpoint integration points outside current transition service remain to be wired in later surface-specific tickets. |
| Assumptions | Authorization service currently expresses policy using action-centric rules and context inputs; expanded policy catalogs and role matrices will be extended as subsequent governance tickets land. |
| Files changed | `kentender_procurement/kentender_procurement/std_engine/services/authorization_service.py`, `kentender_procurement/kentender_procurement/std_engine/services/__init__.py`, `kentender_procurement/kentender_procurement/std_engine/services/state_transition_service.py`, `kentender_procurement/kentender_procurement/std_engine/tests/test_std_authorization_service.py` |
| Test evidence | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_authorization_service` (5/5 pass). Regression safety: `...test_std_state_transition_service` (4/4 pass), `...test_std_seed_validation_command` (3/3 pass). |
| Risks remaining | Some policy branches depend on caller-provided context flags (e.g., addendum/model-generation/source-of-truth); hard-binding these to domain objects/services will be strengthened in follow-on integration tickets. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0401 |
| Reviewer | Engineering |
| Completed | Implemented `get_eligible_std_templates(procurement_category, procurement_method, works_profile_type=None, contract_type=None)` in `std_engine.services.template_query_service` with active-only filters for `STD Template Version` and `STD Applicability Profile`, procurement category and method compatibility checks, Works profile-type filtering, optional contract-type filtering, deterministic blocking reasons when no compatible records exist, and response payload including version/profile identifiers and labels for tender-side selection. Exported service via `std_engine.services.__init__`. |
| Not completed | Instance creation and runtime placeholder initialization are deferred to `STD-CURSOR-0402`; this ticket only delivers the eligibility query surface. |
| Assumptions | Method compatibility must pass both template-family allowed methods and profile allowed methods; for Works, `works_profile_type` acts as a strict match when supplied by caller. |
| Files changed | `kentender_procurement/kentender_procurement/std_engine/services/template_query_service.py`, `kentender_procurement/kentender_procurement/std_engine/services/__init__.py`, `kentender_procurement/kentender_procurement/std_engine/tests/test_std_template_query_service.py`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_template_query_service` (3/3 pass). Regression safety: `...test_std_audit_service` (3/3 pass), `...test_std_state_transition_service` (4/4 pass). |
| Risks remaining | Current blocking-reason contract is stable but minimal (reason codes); richer user-facing diagnostics and policy traceability can be added when Tender Management UI integration starts. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0402 |
| Reviewer | Engineering |
| Completed | Implemented `create_std_instance(tender_code, template_version_code, profile_code, tender_context, actor)` in `std_engine.services.instance_creation_service` with mandatory active-version and active-profile validation, profile/version linkage enforcement, tender-context compatibility gate (via eligible-template query service), duplicate current-instance prevention unless supersession path is provided, and `STD Instance` creation in `Draft` with `readiness_status=Not Run`. Added deterministic placeholder initialization payloads sourced from current template definitions (`STD Section Definition`, `STD Parameter Definition`, `STD Works Requirement Component Definition`, and `STD BOQ Definition` when profile requires BOQ). Emitted `STD_INSTANCE_CREATED` audit event with creation metadata and placeholder counts. |
| Not completed | Persistent runtime row materialization for per-instance section/parameter/component/BOQ value tables is deferred to subsequent runtime/value services; this ticket initializes and returns definition-backed placeholders and creates the canonical instance record. |
| Assumptions | Supersession bypass is explicitly indicated through `tender_context.supersession_instance_code`; when not provided, any non-superseded/non-cancelled instance for the same tender is treated as duplicate current instance. |
| Files changed | `kentender_procurement/kentender_procurement/std_engine/services/instance_creation_service.py`, `kentender_procurement/kentender_procurement/std_engine/services/__init__.py`, `kentender_procurement/kentender_procurement/std_engine/tests/test_std_instance_creation_service.py`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_instance_creation_service` (4/4 pass). Regression safety: `...test_std_template_query_service` (3/3 pass), `...test_std_audit_service` (3/3 pass), `...test_std_state_transition_service` (4/4 pass). |
| Risks remaining | Placeholder initialization is currently definition-derived and returned in service response; future tickets should persist and version runtime placeholder rows to support edits, diffs, readiness traceability, and downstream generation provenance. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0403 |
| Reviewer | Engineering |
| Completed | Implemented `set_std_parameter_value(instance_code, parameter_code, value, actor)` in `std_engine.services.parameter_value_service` with authorization gate (`STD_PARAMETER_SET`), instance immutability enforcement for post-publication/superseded/cancelled states, template-version ownership validation for parameter definitions, type-aware coercion and validation (Boolean/Int/Float/Date/Datetime/JSON/String/Select), allowed-values enforcement, and required-value enforcement. Added runtime persistence model `STD Instance Parameter Value` and upsert logic for tender-specific values. Implemented readiness invalidation and output staleness handling for DEM/DCM-driving parameters by setting instance readiness to `Invalidated` and demoting current/published generated outputs to draft under transition-service context. Emitted `PARAMETER_VALUE_SET` audit events with invalidation metadata. |
| Not completed | Full conditional-expression evaluation (`required_condition` / `validation_expression`) and advanced dependency-graph re-evaluation are deferred to follow-on parameter/dependency tickets; current implementation enforces foundational type/allowed/required constraints. |
| Assumptions | Output staleness is represented in current schema by status demotion to `Draft` for affected generated outputs because no explicit stale-flag field exists yet. |
| Files changed | `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_instance_parameter_value/std_instance_parameter_value.json`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_instance_parameter_value/std_instance_parameter_value.py`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_instance_parameter_value/__init__.py`, `kentender_procurement/kentender_procurement/std_engine/services/parameter_value_service.py`, `kentender_procurement/kentender_procurement/std_engine/services/authorization_service.py`, `kentender_procurement/kentender_procurement/std_engine/services/__init__.py`, `kentender_procurement/kentender_procurement/std_engine/tests/test_std_parameter_value_service.py`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | `bench --site kentender.midas.com reload-doc procurement_planning doctype std_instance_parameter_value` + `bench --site kentender.midas.com migrate` (pass), `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_parameter_value_service` (3/3 pass). Regression safety: `...test_std_instance_creation_service` (4/4 pass), `...test_std_template_query_service` (3/3 pass), `...test_std_audit_service` (3/3 pass). |
| Risks remaining | Parameter runtime values now persist, but cross-parameter dependency execution and comprehensive output-diff provenance are still limited until dependency and generation-phase services are expanded. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0404 |
| Reviewer | Engineering |
| Completed | Implemented `add_std_section_attachment(instance_code, section_code, file_reference, classification, actor, component_code=None)` in `std_engine.services.section_attachment_service` with required binding and validation gates: mandatory section/classification/file reference, allowed classification set (`Specification`, `Drawing`, `Supporting`), section-template binding to instance version (reject unbound attachments), optional works-component binding validation, SHA-256 file-hash persistence, and attachment storage in new runtime model `STD Section Attachment`. Enforced publication lock and supersession discipline by denying direct replacement when an attachment for the same instance/section/classification is already `Published` (addendum/supersession path required). Applied readiness/output invalidation on attachment add by setting instance readiness to `Invalidated` and demoting current/published outputs to `Draft` under transition-service context. Emitted `SECTION_ATTACHMENT_ADDED` audit events with attachment and invalidation metadata. |
| Not completed | Full addendum-driven supersession workflow (explicit `supersedes_attachment_code` population with addendum references) is deferred to addendum integration tickets; this ticket enforces the no-overwrite guard and foundational runtime attachment persistence. |
| Assumptions | Output staleness is represented by output status demotion to `Draft` because explicit stale-flag fields are not yet part of current generated-output schema. |
| Files changed | `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_section_attachment/std_section_attachment.json`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_section_attachment/std_section_attachment.py`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_section_attachment/__init__.py`, `kentender_procurement/kentender_procurement/std_engine/services/section_attachment_service.py`, `kentender_procurement/kentender_procurement/std_engine/services/__init__.py`, `kentender_procurement/kentender_procurement/std_engine/tests/test_std_section_attachment_service.py`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | `bench --site kentender.midas.com reload-doc procurement_planning doctype std_section_attachment` + `bench --site kentender.midas.com migrate` (pass), `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_section_attachment_service` (3/3 pass). Regression safety: `...test_std_parameter_value_service` (3/3 pass), `...test_std_instance_creation_service` (4/4 pass), `...test_std_template_query_service` (3/3 pass), `...test_std_audit_service` (3/3 pass; first run hit transient DB deadlock during test setup cleanup, immediate rerun passed cleanly). |
| Risks remaining | Runtime attachment records are now persisted and bounded, but attachment content provenance/file-store integrity and addendum supersession lineage enrichment still require dedicated downstream governance and integration hardening. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0501 |
| Reviewer | Engineering |
| Completed | Implemented Works Requirements services in `std_engine.services.works_requirements_service`: `get_works_requirement_components(instance_code)`, `update_works_requirement_component(instance_code, component_code, payload, actor)`, and `validate_works_requirements(instance_code)`. Added runtime persistence model `STD Instance Works Requirement Component` for per-instance component content/status (`structured_text`, `table_data`, `completion_status`). Service loads component definitions from the active template version, enforces payload-mode support (`supports_structured_text`, `supports_table_data`), marks completion status, denies edits after publication/superseded/cancelled states, and applies readiness/output invalidation for DSM/DEM/DCM-driving components. Validation enforces required-component completion and attachment-required gates, sets instance readiness (`Ready`/`Blocked`), and returns deterministic blockers. Audit emission added for updates (`WORKS_REQUIREMENT_UPDATED`). |
| Not completed | Advanced component-level dependency orchestration and richer attachment register schema semantics are deferred to subsequent BOQ/generation/readiness tickets. |
| Assumptions | Output staleness continues to be represented by output status demotion to `Draft` (no dedicated stale-flag fields in current output schema). |
| Files changed | `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_instance_works_requirement_component/std_instance_works_requirement_component.json`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_instance_works_requirement_component/std_instance_works_requirement_component.py`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_instance_works_requirement_component/__init__.py`, `kentender_procurement/kentender_procurement/std_engine/services/works_requirements_service.py`, `kentender_procurement/kentender_procurement/std_engine/services/__init__.py`, `kentender_procurement/kentender_procurement/std_engine/tests/test_std_works_requirements_service.py`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | `bench --site kentender.midas.com reload-doc procurement_planning doctype std_instance_works_requirement_component` + `bench --site kentender.midas.com migrate` (pass), `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_works_requirements_service` (3/3 pass). Regression safety: `...test_std_section_attachment_service` (3/3 pass; first run hit transient DB deadlock in setup cleanup, immediate rerun passed), `...test_std_parameter_value_service` (3/3 pass). |
| Risks remaining | Required-component and attachment gates are now enforced at validation time, but downstream readiness/run orchestration must still bind these blockers into broader phase gates and UI diagnostics in later tickets. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0502 |
| Reviewer | Engineering |
| Completed | Implemented BOQ instance services in `std_engine.services.boq_instance_service`: `get_boq_instance(instance_code)`, `create_or_initialize_boq_instance(instance_code, actor)`, `add_boq_bill(instance_code, bill_payload, actor)`, `add_boq_item(bill_instance_code, item_payload, actor)`, `update_boq_item(item_instance_code, payload, actor)`, and `validate_boq_instance(instance_code)`. Added runtime BOQ graph models `STD BOQ Instance`, `STD BOQ Bill Instance`, and `STD BOQ Item Instance`. Enforced profile-driven BOQ requirement at initialization, publication-lock edit denial, negative-quantity rejection, required-field validation, and deterministic amount computation (`quantity * rate`) as system rule. Applied BOQ change invalidation by setting instance readiness to `Invalidated` and demoting current/published generated outputs to `Draft`. Emitted BOQ update audit events. |
| Not completed | Rich bill/item type exception catalog (e.g., sanctioned negative quantity edge-case types) and advanced schema-driven field ownership matrices are deferred to later BOQ/import refinement tickets. |
| Assumptions | Missing required BOQ fields are validated at runtime instance level (bill/item rows) independent of template schema extensions not yet materialized as dynamic columns. |
| Files changed | `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_boq_instance/std_boq_instance.json`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_boq_instance/std_boq_instance.py`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_boq_instance/__init__.py`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_boq_bill_instance/std_boq_bill_instance.json`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_boq_bill_instance/std_boq_bill_instance.py`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_boq_bill_instance/__init__.py`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_boq_item_instance/std_boq_item_instance.json`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_boq_item_instance/std_boq_item_instance.py`, `kentender_procurement/kentender_procurement/procurement_planning/doctype/std_boq_item_instance/__init__.py`, `kentender_procurement/kentender_procurement/std_engine/services/boq_instance_service.py`, `kentender_procurement/kentender_procurement/std_engine/services/__init__.py`, `kentender_procurement/kentender_procurement/std_engine/tests/test_std_boq_instance_service.py`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | `bench --site kentender.midas.com reload-doc procurement_planning doctype std_boq_instance` + `... std_boq_bill_instance` + `... std_boq_item_instance` + `bench --site kentender.midas.com migrate` (pass), `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_boq_instance_service` (3/3 pass). Regression safety: `...test_std_works_requirements_service` (3/3 pass), `...test_std_section_attachment_service` (3/3 pass). |
| Risks remaining | BOQ runtime layer is now functional and governed, but richer schema-expression enforcement and advanced reconciliation diagnostics are still limited and will be deepened in subsequent generation/readiness coupling tickets. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Ticket(s) | STD-CURSOR-0503 |
| Reviewer | Engineering |
| Completed | Implemented `import_boq_structured(instance_code, file_reference, mapping_config, actor, dry_run=False)` in `std_engine.services.boq_import_service` with strict structured-import flow: row mapping intake, dry-run preview, ambiguous-row rejection reporting, confirmed import path that creates BOQ bills/items as structured runtime records, and retention of original import file as supporting evidence attachment through section-attachment service. Added deterministic audit emission on import completion and returned validation result from BOQ validator. Enforced that file-only payload (no structured rows) does not satisfy BOQ readiness/validation. |
| Not completed | Spreadsheet parser adapters (column auto-detection, workbook sheet inference, locale/unit normalization) are deferred; current ticket consumes normalized mapped rows via `mapping_config.rows` contract. |
| Assumptions | Parsing/mapping UI layer will normalize spreadsheet contents into `mapping_config.rows` before invoking this service; service scope remains structured import orchestration/validation, not binary file parsing internals. |
| Files changed | `kentender_procurement/kentender_procurement/std_engine/services/boq_import_service.py`, `kentender_procurement/kentender_procurement/std_engine/services/__init__.py`, `kentender_procurement/kentender_procurement/std_engine/tests/test_std_boq_import_service.py`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_boq_import_service` (9/9 pass including inherited BOQ instance checks), focused regression: `...test_std_boq_instance_service` (3/3 pass), cross-service regression: `...test_std_works_requirements_service` (3/3 pass), `...test_std_parameter_value_service` (3/3 pass). |
| Risks remaining | Current import path expects already-mapped row payloads; robustness against malformed real-world workbooks depends on forthcoming parser/mapping UX hardening and richer rejection diagnostics. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-0601 through STD-CURSOR-0606 |
| Reviewer | Engineering |
| Completed | **0601** — `generate_std_outputs` in `generation_job_service`: job lifecycle (Pending/Running/Completed/Failed), input hash, savepoint-wrapped generation, outputs Draft→Current, supersede Current only, audit events; transitions `STD_JOB_FAIL`, `STD_OUTPUT_SUPERSEDE`; DocType fields `input_hash`/`error_message` on jobs and `output_payload`/`input_hash`/`output_hash` on outputs. **0602–0606** — `output_generators.build_output_payload` implements Bundle manifest (required sections + preface exclusions), DSM (BOQ rate-only editability), DOM (opening fields + prohibited list), DEM (sourced rules + stages), DCM (carry-forward + contract price source rule). |
| Not completed | Legal-grade clause rendering, live addendum/award binding, and consumer-specific serializers remain future work; payloads are trace-oriented JSON. |
| Assumptions | Safe field read via `_inst()` for `as_dict()` instances; tests use `_output_payload_dict` when JSON field loads as string. |
| Files changed | `procurement_planning/doctype/std_generation_job/std_generation_job.json`, `procurement_planning/doctype/std_generated_output/std_generated_output.json`, `std_engine/services/state_transition_service.py`, `std_engine/services/generation_job_service.py`, `std_engine/services/output_generators.py`, `std_engine/services/__init__.py`, `std_engine/tests/test_std_phase6_generation_engine.py`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | `bench --site kentender.midas.com migrate` (pass), `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase6_generation_engine` (11/11 pass). Playwright: not applicable (no Desk/UI). |
| Risks remaining | Generator depth is MVP-structured; readiness/addendum phases must align hashes and invalidation with this contract. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-0701, STD-CURSOR-0702 |
| Reviewer | Engineering |
| Completed | **0701** — `run_std_readiness(object_type, object_code, actor)` for `STD_INSTANCE`: evaluates template/profile active, mandatory sections present, required parameter values set, works-requirements blockers (via `validate_works_requirements(..., persist=False)`), BOQ validation, and Current non-stale generated outputs for Bundle/DSM/DOM/DEM/DCM; creates `STD Readiness Run` + `STD Readiness Finding` rows; supersedes prior runs; updates instance `readiness_status` only under transition-service context; emits `READINESS_RUN_CREATED`. **0702** — `mark_std_outputs_stale(instance_code, change_kind, actor)` with change-kind → output-type matrix; `resolve_parameter_change_kind` / attachment inference; wired from parameter, BOQ, and section-attachment mutation paths. `STD Generated Output` gains `is_stale` / `stale_reason`. `STD Instance` now guards `readiness_status` mutations the same way as `instance_status`. |
| Not completed | Full addendum-impact, ITT/GCC tamper checks, dependency graph, forms/mappings completeness, and audit-trace materiality checks are partial or stubbed; Playwright N/A (no Desk). |
| Assumptions | Readiness run `status` reuses instance readiness vocabulary (`Ready`, `Blocked`, `Warning`, `Incomplete`); prior runs move to `Superseded` via controlled save. |
| Files changed | `procurement_planning/doctype/std_generated_output/std_generated_output.json`, `procurement_planning/doctype/std_instance/std_instance.py`, `std_engine/services/readiness_service.py`, `std_engine/services/stale_output_service.py`, `std_engine/services/parameter_value_service.py`, `std_engine/services/boq_instance_service.py`, `std_engine/services/section_attachment_service.py`, `std_engine/services/works_requirements_service.py`, `std_engine/services/__init__.py`, `std_engine/tests/test_std_phase7_readiness.py`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | `bench --site kentender.midas.com migrate` (pass), `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase7_readiness` (5/5 pass); regressions: `...test_std_parameter_value_service` (3/3), `...test_std_works_requirements_service` (3/3), `...test_std_section_attachment_service` (3/3), `...test_std_boq_instance_service` (3/3). |
| Risks remaining | Stale matrix is code-centralized; real tender metadata should drive finer parameter→change_kind mapping in later tickets. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-0801, STD-CURSOR-0802 |
| Reviewer | Engineering |
| Completed | **0801** — Added `analyze_std_addendum_impact(instance_code, addendum_code, proposed_changes, actor)` in `std_engine/services/addendum_impact_service.py` with required change-type matrix mapping to affected outputs, acknowledgement, and deadline-review flags. Persists `STD Addendum Impact Analysis` with analysis payload fields, transitions `Draft -> Analysis Pending -> Analysis Complete`, then `Regeneration Required` (or `Approved` when no output regeneration impact), and emits `ADDENDUM_IMPACT_ANALYZED`. **0802** — Added `regenerate_std_outputs_for_addendum(impact_analysis_code, actor)` in `std_engine/services/addendum_regeneration_service.py`, enforcing impact status gate (`Approved` or `Regeneration Required`), regenerating only impacted output types via generation engine with `addendum_code`, attaching addendum lineage (`source_addendum_code`, `supersedes_output_code`) to new outputs, and moving impact status to `Regenerated` with `OUTPUT_REGENERATED` audit events. |
| Not completed | Addendum issuance gate wiring in TM workflows and full legal/business-policy approval workflow are deferred to later integration phases; Playwright not applicable (no Desk changes). |
| Assumptions | JSON fields for impact payloads are persisted as JSON strings for MariaDB compatibility in `db.set_value`; regeneration supersedes prior **Current** outputs while preserving prior `Published` records as immutable history. |
| Files changed | `procurement_planning/doctype/std_addendum_impact_analysis/std_addendum_impact_analysis.json`, `procurement_planning/doctype/std_generated_output/std_generated_output.json`, `std_engine/services/addendum_impact_service.py`, `std_engine/services/addendum_regeneration_service.py`, `std_engine/services/state_transition_service.py`, `std_engine/services/__init__.py`, `std_engine/tests/test_std_phase8_addendum.py`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | `bench --site kentender.midas.com migrate` (pass), `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase8_addendum` (5/5 pass). Regression: `...test_std_phase7_readiness` (5/5 pass), `...test_std_phase6_generation_engine` (11/11 pass). |
| Risks remaining | Impact matrix is deterministic but still coarse-grained for some conditional pack rows (e.g., evaluation-option and drawing/spec conditional branches); finer configuration-driven branching can be added in later hardening. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-0901 |
| Reviewer | Engineering |
| Completed | Added tender binding runtime surface via `STD Tender Binding` Doctype and `bind_std_instance_to_tender(tender_code, std_instance_code, actor)` / `get_tender_std_binding(tender_code)` in `std_engine/services/tender_binding_service.py`. Binding stores references to STD instance/template/profile plus current output codes (`Bundle/DSM/DOM/DEM/DCM`), computes `std_outputs_current`, and mirrors instance readiness (`std_readiness_status`) so downstream tender publication checks can consume STD readiness directly without duplicating editable payloads. |
| Not completed | Tickets 0902–0905 remain pending; no cross-module TM UI wiring yet in this ticket. |
| Assumptions | In this repo phase, Tender Management v2 binding is represented through dedicated reference Doctype (`STD Tender Binding`) as allowed by pack (“or equivalent relational child/reference table”). |
| Files changed | `procurement_planning/doctype/std_tender_binding/std_tender_binding.json`, `procurement_planning/doctype/std_tender_binding/std_tender_binding.py`, `procurement_planning/doctype/std_tender_binding/__init__.py`, `std_engine/services/tender_binding_service.py`, `std_engine/services/__init__.py`, `std_engine/tests/test_std_phase9_tender_binding.py`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | `bench --site kentender.midas.com migrate` (pass), `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase9_tender_binding` (2/2 pass). |
| Risks remaining | Actual TM write-path integration hooks must be connected in 0902+ so denials/disablement happen at manual checklist/evaluation/opening entrypoints. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-0902 |
| Reviewer | Engineering |
| Completed | Added server-side guard service `tender_submission_guard_service.py` with `check_manual_submission_requirement_permission(tender_code, actor)` and guarded API `create_manual_submission_requirement(...)`. When `std_engine_v2_enabled=1` and tender has `STD Tender Binding` with `std_instance_code`, manual submission requirement injection is denied with stable code `STD_TM_MANUAL_SUBMISSION_BLOCKED`, and `PERMISSION_DENIED` audit event is written. Added export wiring in `std_engine/services/__init__.py`. |
| Not completed | Desk/UI DSM preview wiring for TM screens remains pending (UI ticket scope later); this ticket enforces server-side API block and denial telemetry. |
| Assumptions | Feature flag is read from `frappe.conf.std_engine_v2_enabled` in current phase; a richer flag storage/service can replace this in later hardening without changing denial contract. |
| Files changed | `std_engine/services/tender_submission_guard_service.py`, `std_engine/services/__init__.py`, `std_engine/tests/test_std_phase9_submission_guard.py`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase9_submission_guard` (2/2 pass), regression: `...test_std_phase9_tender_binding` (2/2 pass). |
| Risks remaining | Downstream TM endpoints must call this guard consistently; follow-up tickets 0903/0904 will apply equivalent denial patterns to evaluation/opening fields. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-0903 |
| Reviewer | Engineering |
| Completed | Added server-side DEM-only evaluation guard service `tender_evaluation_guard_service.py` with `check_manual_evaluation_criteria_permission(tender_code, actor)` and guarded API `create_manual_evaluation_criterion(...)`. For `std_engine_v2_enabled=1` + STD-bound tender, manual evaluation criterion creation is denied with stable code `STD_TM_MANUAL_EVALUATION_BLOCKED`; denial is audit-logged via `PERMISSION_DENIED`. Export wiring added in `std_engine/services/__init__.py`. |
| Not completed | Ticket 0904 opening-field guard and 0905 DCM contract binding still pending; UI disable/preview surfaces remain later-phase work. |
| Assumptions | Current enforcement is API/service-layer canonical path for TM integration in this phase; actual module endpoints should call this guard without changing denial code contract. |
| Files changed | `std_engine/services/tender_evaluation_guard_service.py`, `std_engine/services/__init__.py`, `std_engine/tests/test_std_phase9_evaluation_guard.py`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase9_evaluation_guard` (2/2 pass), regression: `...test_std_phase9_submission_guard` (2/2 pass). |
| Risks remaining | Evaluation engine endpoints must consistently route through this guard to fully prevent bypass in non-service codepaths. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-0904 |
| Reviewer | Engineering |
| Completed | Added DOM-only opening guard service `tender_opening_guard_service.py` with: `check_manual_opening_field_permission(tender_code, actor)`, guarded API `create_manual_opening_field(...)`, and gate `validate_opening_can_proceed(tender_code, actor)`. For `std_engine_v2_enabled=1` + STD-bound tender, manual opening fields are denied with `STD_TM_MANUAL_OPENING_BLOCKED`; opening progression requires `std_dom_code` and returns `STD_TM_DOM_REQUIRED` if missing. Denials are audit-logged (`PERMISSION_DENIED`). |
| Not completed | Ticket 0905 DCM/contract binding still pending; cross-module bid-opening endpoint wiring remains to be connected to these guards. |
| Assumptions | `STD Tender Binding.std_dom_code` is canonical DOM readiness reference for opening gate in this phase. |
| Files changed | `std_engine/services/tender_opening_guard_service.py`, `std_engine/services/__init__.py`, `std_engine/tests/test_std_phase9_opening_guard.py`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase9_opening_guard` (2/2 pass), regression: `...test_std_phase9_evaluation_guard` (2/2 pass). |
| Risks remaining | Consumer modules must call `validate_opening_can_proceed` before opening action dispatch to fully enforce no-DOM gate. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-0905 |
| Reviewer | Engineering |
| Completed | Added DCM contract binding guard service `tender_contract_guard_service.py` with `validate_contract_creation_inputs(tender_code, contract_payload, actor)` and guarded API `create_contract_from_std(...)`. For `std_engine_v2_enabled=1` + STD-bound tender, contract creation is denied if `std_dcm_code` is missing (`STD_TM_DCM_REQUIRED`). For Works profile tenders, contract price source is enforced to `corrected evaluated BOQ total from Evaluation/Award`; mismatches are denied with `STD_TM_CONTRACT_SOURCE_MISMATCH`. Denials are audit-logged via `PERMISSION_DENIED`. Export wiring added in `std_engine/services/__init__.py`. |
| Not completed | Downstream contract-management module endpoint wiring remains to consume this guard uniformly; this ticket delivers canonical server-side contract validation surface. |
| Assumptions | Works detection derives from bound STD instance profile procurement category (`Works`) and uses `STD Tender Binding` as the TM integration reference table. |
| Files changed | `std_engine/services/tender_contract_guard_service.py`, `std_engine/services/__init__.py`, `std_engine/tests/test_std_phase9_contract_guard.py`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase9_contract_guard` (3/3 pass); regression: `...test_std_phase9_opening_guard` (2/2), `...test_std_phase9_evaluation_guard` (2/2), `...test_std_phase9_submission_guard` (2/2), `...test_std_phase9_tender_binding` (2/2). |
| Risks remaining | Contract creation callsites outside std_engine service package must be updated to route through these guards to guarantee global enforcement. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-1001 |
| Reviewer | Engineering |
| Completed | Implemented `/desk/std-engine` workbench shell scaffold via `public/js/std_engine_workspace.js` with route-aware mount and required placeholders/test IDs: `std-workbench-page`, `std-page-title`, `std-kpi-strip`, `std-scope-tabs`, `std-queue-bar`, `std-search-input`, `std-filter-panel`, `std-object-list`, `std-object-detail`, `std-action-bar`, `std-blockers-panel`. Added layout CSS scaffold in `public/css/std_engine_workspace.css` and wired Desk assets in `hooks.py` app includes. Added Playwright smoke spec `tests/ui/smoke/procurement/std-workbench-1001.spec.ts` asserting route load, required IDs, non-list rendering guard, and absence of `Upload STD` primary action. |
| Not completed | None for ticket 1001 scope. |
| Assumptions | Ticket 1001 is shell-only; all 1002+ behaviors remain intentionally placeholder/static per scope. |
| Files changed | `kentender_procurement/public/js/std_engine_workspace.js`, `kentender_procurement/public/css/std_engine_workspace.css`, `kentender_procurement/hooks.py`, `tests/ui/smoke/procurement/std-workbench-1001.spec.ts`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | Site sync and assets: `bench --site kentender.midas.com migrate` (pass), `./scripts/bench-with-node.sh build --app kentender_procurement` (pass), `bench --site kentender.midas.com clear-cache` (pass). UI smoke: `cd apps/kentender_v1 && npx playwright test tests/ui/smoke/procurement/std-workbench-1001.spec.ts --reporter=line` (1/1 pass). |
| Risks remaining | `bench restart` depends on supervisor in this environment; when supervisor is unavailable, keep using the active `bench start` process for runtime validation. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-1002 |
| Reviewer | Engineering |
| Completed | Implemented interactive KPI/risk strip for `/desk/std-engine` with live counts via new API `std_engine/api/landing.py::get_std_workbench_kpi_strip`. Added eight KPI cards (`Draft Versions`, `Validation Blocked`, `Legal Review Pending`, `Policy Review Pending`, `Active Versions`, `Instances Blocked`, `Generation Failures`, `Addendum Impact Pending`) rendered in `public/js/std_engine_workspace.js`, wired click-to-select behavior, queue/scope state handoff (`std-active-queue-state`, shell `data-active-*` attributes, `std-workbench:kpi-selected` event), and high-risk visual variants in `public/css/std_engine_workspace.css`. |
| Not completed | Full queue-bar/scope-tab behavior, object list filtering, and advanced filter chips remain for 1003/1004 as planned. |
| Assumptions | 1002 queue handoff IDs (`draft_versions`, `validation_blocked`, `legal_review`, `policy_review`, `active_versions`, `instance_blocked`, `generation_failed`, `addendum_impact`) are forward-compatible contract values for 1003 queue implementation. |
| Files changed | `std_engine/api/landing.py`, `std_engine/api/__init__.py`, `std_engine/tests/test_std_phase10_kpi_strip.py`, `public/js/std_engine_workspace.js`, `public/css/std_engine_workspace.css`, `tests/ui/smoke/procurement/std-workbench-1001.spec.ts`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | Backend: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase10_kpi_strip` (2/2 pass). UI + regressions: `./scripts/bench-with-node.sh build --app kentender_procurement` (pass), `bench --site kentender.midas.com clear-cache` (pass), `cd apps/kentender_v1 && npx playwright test tests/ui/smoke/procurement/std-workbench-1001.spec.ts --reporter=line` (3/3 pass, including KPI click + hard-refresh sidebar coverage). |
| Risks remaining | KPI count semantics for `instances_blocked` currently aggregate both `instance_status=Blocked` and `readiness_status=Blocked`; if 1003 queue definitions require de-duplication across these dimensions, the API contract should be tightened in that ticket. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-1003 |
| Reviewer | Engineering |
| Completed | Implemented full STD workbench scope tab and queue bar contract for admin-first visibility. API `std_engine/api/landing.py::get_std_workbench_kpi_strip` now returns `scope_tabs`, `queues`, defaults, and `visibility_policy=admin_full_set`. UI `public/js/std_engine_workspace.js` now renders all required tabs (`My Work`, `Templates`, `Active Versions`, `STD Instances`, `Generation Jobs`, `Addendum Impacts`, `Audit View`) and required queues (`Draft Versions`, `Structure In Progress`, `Validation Blocked`, `Validation Passed`, `Legal Review`, `Policy Review`, `Approved`, `Active`, `Suspended`, `Superseded`, `Draft Instances`, `Instance Blocked`, `Instance Ready`, `Published Locked`, `Generation Failed`, `Addendum Impact`, `Archived`), with click handlers updating active state and queue indicator. KPI click handoff from 1002 now activates matching scope/queue. |
| Not completed | Non-admin granular role matrix is intentionally deferred; this ticket validates full set for `Administrator` / `System Manager` as agreed. |
| Assumptions | `visibility_policy=admin_full_set` is temporary contract metadata until role-specific scope/queue pruning is implemented in a follow-up ticket. |
| Files changed | `std_engine/api/landing.py`, `std_engine/tests/test_std_phase10_scope_queue.py`, `public/js/std_engine_workspace.js`, `public/css/std_engine_workspace.css`, `tests/ui/smoke/procurement/std-workbench-1001.spec.ts`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | Backend: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase10_scope_queue` (2/2 pass). UI + regressions: `./scripts/bench-with-node.sh build --app kentender_procurement` (pass), `bench --site kentender.midas.com clear-cache` (pass), `cd apps/kentender_v1 && npx playwright test tests/ui/smoke/procurement/std-workbench-1001.spec.ts --reporter=line` (4/4 pass, includes new scope/queue interactivity coverage). |
| Risks remaining | Queue labels/states currently drive UI state only; object-list filtering semantics remain to be implemented in 1004/1005, so queue selection is stateful but not yet data-binding complete. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-1004 |
| Reviewer | Engineering |
| Completed | Implemented STD workbench search and advanced filter behavior with queue-state combination. Added API `search_std_workbench_objects` in `std_engine/api/landing.py` supporting query + scope/queue + multi-filter payload (object type, procurement category, method/profile/status family, blocker/failure flags, date range, assigned-to-me). UI `public/js/std_engine_workspace.js` now wires search input, compact filter controls (all required filter slots represented), active filter chips, and object-list result rendering. Queue/tab selection and KPI selection are now combined with active filters in search requests. |
| Not completed | `Used by Published Tender` and procurement-method contract filters are currently accepted as UI/API parameters but not yet bound to a dedicated tender-binding dataset in result rows; they remain no-op placeholders until object-list/domain enrichment in 1005/110x. |
| Assumptions | For 1004, \"Search returns known seed objects\" is satisfied via mixed STD object search across template/version/profile/instance/job/output/addendum/readiness datasets; business-card row formatting is deferred to 1005. |
| Files changed | `std_engine/api/landing.py`, `public/js/std_engine_workspace.js`, `public/css/std_engine_workspace.css`, `std_engine/tests/test_std_phase10_search_filters.py`, `tests/ui/smoke/procurement/std-workbench-1001.spec.ts`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | Backend: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase10_search_filters` (2/2 pass). Regression backend: `...test_std_phase10_scope_queue` (2/2 pass). UI + regressions: `./scripts/bench-with-node.sh build --app kentender_procurement` (pass), `bench --site kentender.midas.com clear-cache` (pass), `cd apps/kentender_v1 && npx playwright test tests/ui/smoke/procurement/std-workbench-1001.spec.ts --reporter=line` (5/5 pass; includes search/filter chip + queue combination flow). |
| Risks remaining | Object list still uses compact technical rows; richer business-card presentation and deep object-type-specific metadata remain planned for 1005. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-1005 |
| Reviewer | Engineering |
| Completed | Implemented STD business object list rows for required object types and row selection handoff: Template Family, Template Version, Applicability Profile, STD Instance, Generated Output, Generation Job, Addendum Impact, Readiness Run. Extended search API dataset in `std_engine/api/landing.py` to include template families and richer row metadata keys. Updated `public/js/std_engine_workspace.js` to render business-style multi-line rows with badges, object-type specific subtitles, active row state, and click-to-select behavior that updates the detail panel placeholder (`std-selected-object-code`). Updated `public/css/std_engine_workspace.css` with business-row card styling and badge treatment. |
| Not completed | Superseded by STD-CURSOR-1006: state-aware actions and structured detail shell are now implemented (see 1006 evidence row). |
| Assumptions | UI smoke supports environments with sparse data by asserting click-to-detail when rows exist and explicit empty-state rendering when no rows match filters. |
| Files changed | `std_engine/api/landing.py`, `public/js/std_engine_workspace.js`, `public/css/std_engine_workspace.css`, `std_engine/tests/test_std_phase10_object_list_panel.py`, `tests/ui/smoke/procurement/std-workbench-1001.spec.ts`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | Backend: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase10_object_list_panel` (2/2 pass). Backend regressions: `...test_std_phase10_search_filters` (2/2 pass), `...test_std_phase10_scope_queue` (2/2 pass). UI: `cd apps/kentender_v1 && npx playwright test tests/ui/smoke/procurement/std-workbench-1001.spec.ts --reporter=line` (6/6 pass, including object-list row click scenario). Asset flow: `./scripts/bench-with-node.sh build --app kentender_procurement` (pass), `bench --site kentender.midas.com clear-cache` (pass). |
| Risks remaining | Search-backed list query currently aggregates across multiple doctypes with bounded row windows; if production datasets grow large, 1005/1006 follow-up may need indexed server-side pagination per object type to preserve response time. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-1006 |
| Reviewer | Engineering |
| Completed | Server `get_std_action_availability` + `action_availability_service.build_std_action_availability`: resolves workbench `object_type` + business `code` to DocType/name, returns `state_cards`, `actions` (open/edit/create instance/publish-lock with `allowed`/`disabled`/`reason`/`requires_confirmation`/`confirmation_message`/`route`/`meta`), `blockers`, `warnings`. Desk UI `std_engine_workspace.js`/`std_engine_workspace.css`: structured detail regions (`std-detail-header`, `std-detail-state-cards`, tab strip `std-detail-tab-overview`/`std-detail-tab-audit`, `std-detail-tab-panel`, `std-blockers-panel`), dynamic `std-action-host` action bar, stale-request guard on detail fetch, `frappe.confirm` for gated actions, `create_std_instance` opens new `STD Instance` form with `template_version_code`. |
| Not completed | Template-version **editors** for tabs after Parameters (forms, works, …) remain **STD-CURSOR-1010+**; generic two-tab strip for non–Template Version selections unchanged; generic Audit tab remains a shell. |
| Assumptions | Action execution for publish-lock routes to Desk Form (same as open) with confirmation; destructive server mutations beyond navigation stay in existing DocType controllers. |
| Files changed | `std_engine/services/action_availability_service.py`, `std_engine/api/landing.py`, `std_engine/tests/test_std_phase10_action_availability.py`, `public/js/std_engine_workspace.js`, `public/css/std_engine_workspace.css`, `tests/ui/smoke/procurement/std-workbench-1001.spec.ts`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | Backend: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase10_action_availability` (6/6 pass). Regression: `...test_std_phase10_object_list_panel` (2/2 pass). UI: `./scripts/bench-with-node.sh build --app kentender_procurement`, `bench --site kentender.midas.com clear-cache`, `cd apps/kentender_v1 && npx playwright test tests/ui/smoke/procurement/std-workbench-1001.spec.ts --reporter=line` (8 tests: 7 passed, 1 skipped; includes new 1006 detail/action availability flow). |
| Risks remaining | `OBJECT_TYPE_RESOLUTION` must stay aligned with `landing._collect_rows` object_type strings; duplicate detail fetch on rapid selection is mitigated by `detailReqId` but not cancelled server-side. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-1007 |
| Reviewer | Engineering |
| Completed | Whitelisted `get_std_template_version_workbench_summary` (`std_engine/api/template_version_workbench.py`) + `build_std_template_version_workbench_summary` (`std_engine/services/template_version_workbench_service.py`): `read_only` when `version_status == Active` and `immutable_after_activation`; aggregates `STD Section Definition` rows with `editability == Locked` for `locked_section_count`, `itt_locked` / `gcc_locked` via case-insensitive **ITT** / **GCC** substring match on `section_title` or `section_code`; capped `sample_locked_titles` (no internal `name`). Desk: `std_engine_workspace.js` swaps `[data-testid="std-detail-tabs"]` to ten pack tab `data-testid`s for Template Version, restores generic Overview/Audit for other types; `detailReqId` guards summary fetch; Overview shows badges (`std-template-read-only`, `std-template-itt-locked`, `std-template-gcc-locked`) and neutral locked-section line when counts exist without ITT/GCC label match. Other tabs: inert placeholders (`std-template-panel-*`). CSS: horizontal scroll for dense tab strip (`kt-std-detail-tabs--template`). |
| Not completed | Remaining template-version tabs (Forms, Works configuration, …) per pack tickets **1010+**. |
| Assumptions | ITT/GCC visibility follows the heuristic above; seed data that uses different labels still surfaces `locked_section_count` and the neutral line when applicable. |
| Files changed | `std_engine/api/template_version_workbench.py`, `std_engine/services/template_version_workbench_service.py`, `std_engine/tests/test_std_phase10_template_version_tabs.py`, `public/js/std_engine_workspace.js`, `public/css/std_engine_workspace.css`, `tests/ui/smoke/procurement/std-workbench-1001.spec.ts`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | Backend: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase10_template_version_tabs` (6/6 pass). UI: `cd apps/kentender_v1 && npx playwright test tests/ui/smoke/procurement/std-workbench-1001.spec.ts --reporter=line` (7 passed, 2 skipped; 1007 flow exercises ten tabs + Structure placeholder + read-only badge when Active). Assets: `./scripts/bench-with-node.sh build --app kentender_procurement` (pass); run `bench --site <site> clear-cache` after deploy. |
| Risks remaining | ITT/GCC flags depend on title/code containing those substrings; org-specific naming may require mapping or UI copy tweaks without changing `locked_section_count`. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-1008 |
| Reviewer | Engineering |
| Completed | Whitelisted `get_std_template_version_structure_tree` in `std_engine/api/template_version_workbench.py`; `build_std_template_version_structure_tree` in `std_engine/services/template_version_structure_service.py` returns nested **parts → sections → clauses** (business codes + titles, source document titles, `impact` drive flags, section `itt_locked_hint` / `gcc_locked_hint` when `editability == Locked` and title/code match ITT/GCC substring heuristic). Desk `std_engine_workspace.js`: Structure tab (`tpl-structure`) two-pane layout (`std-structure-tree`, `std-structure-detail`), fetch on tab with `detailReqId` guard, tree nodes (`std-structure-node-part|section|clause`), detail editability + source trace + clause impacts; **exact** locked-section warning `std-structure-locked-section-warning`. No upload/replace action. CSS: `kt-std-structure-*` grid and tree chrome in `std_engine_workspace.css`. |
| Not completed | In-tab editing / reorder / upload flows; Forms tab (**1010**) and later pack tickets. |
| Assumptions | Structure is read-only browse; clause long text fields not inlined in workbench (title/code + metadata only). |
| Files changed | `std_engine/services/template_version_structure_service.py`, `std_engine/api/template_version_workbench.py`, `std_engine/tests/test_std_phase10_template_version_structure.py`, `public/js/std_engine_workspace.js`, `public/css/std_engine_workspace.css`, `tests/ui/smoke/procurement/std-workbench-1001.spec.ts`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | Backend: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase10_template_version_structure` (6/6 pass). UI: `cd apps/kentender_v1 && npx playwright test tests/ui/smoke/procurement/std-workbench-1001.spec.ts --reporter=line` (7 passed, 2 skipped; includes Structure tree + section detail + conditional locked warning). Assets: `./scripts/bench-with-node.sh build --app kentender_procurement` (pass); `bench --site <site> clear-cache` after deploy. |
| Risks remaining | ITT/GCC row hints reuse the same substring heuristic as 1007 summary; very large templates may need pagination later. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-1009 |
| Reviewer | Engineering |
| Completed | Whitelisted `get_std_template_version_parameter_catalogue` in `std_engine/api/template_version_workbench.py`; `build_std_template_version_parameter_catalogue` in `std_engine/services/template_version_parameters_service.py` loads `STD Parameter Definition` + `STD Parameter Dependency`, groups by `parameter_group` (pack order then alpha), resolves `section_title`, exposes `read_only` (Active + immutable), `impact` flags, `incoming_dependencies` / `outgoing_dependencies` as short English sentences. Desk `std_engine_workspace.js`: `tpl-parameters` panel `std-template-panel-parameters`, `detailReqId`-guarded fetch, group test ids `std-param-group-*`, rows `std-param-row-*`, dependency lines `std-param-dependency-line-*`, `std-parameters-read-only` banner. CSS: `kt-std-parameters-panel` / param row chrome. |
| Not completed | In-form parameter editing, advanced dependency graph, full fourteen-group seed coverage beyond read-only catalogue. |
| Assumptions | Dependency copy is template English for workbench preview; `parameter_group` free text is sorted with pack-known labels first. |
| Files changed | `std_engine/services/template_version_parameters_service.py`, `std_engine/api/template_version_workbench.py`, `std_engine/tests/test_std_phase10_template_version_parameters.py`, `public/js/std_engine_workspace.js`, `public/css/std_engine_workspace.css`, `tests/ui/smoke/procurement/std-workbench-1001.spec.ts`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | Backend: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase10_template_version_parameters` (4/4 pass). UI: `cd apps/kentender_v1 && npx playwright test tests/ui/smoke/procurement/std-workbench-1001.spec.ts --reporter=line` (7 passed, 2 skipped; includes Parameters tab when catalogue non-empty). Assets: `./scripts/bench-with-node.sh build --app kentender_procurement` (pass). |
| Risks remaining | Large catalogues may need virtualized list later; dependency wording is heuristic, not legal interpretation. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-1010 |
| Reviewer | Engineering |
| Completed | Added Forms tab server/UI pipeline for template versions. Backend: whitelisted `get_std_template_version_forms_catalogue` in `std_engine/api/template_version_workbench.py` and service `build_std_template_version_forms_catalogue` in `std_engine/services/template_version_forms_service.py` loading `STD Form Definition` rows, categorizing forms into Section IV / Contract / Other, exposing per-form DSM/DEM/DCM impact flags, draft-editability/read-only guards, and generated model preview counts with required-supplier DSM code list. UI: `public/js/std_engine_workspace.js` now fetches `tpl-forms` payload with request guards, renders category sidebar, forms table, detail drawer, draft-only field-builder controls, required-supplier DSM warning, and read-only model preview; `public/css/std_engine_workspace.css` adds forms layout styling. |
| Not completed | Form editing persistence/save workflow, reorder, and upload-backed field schema management remain later tickets; this ticket delivers read/preview + draft-only builder scaffold without mutation API. |
| Assumptions | Section categorization uses section number/title heuristics (`IV` => Section IV forms, `X`/`contract` => Contract forms); business labels stay sourced from form/section records. |
| Files changed | `std_engine/services/template_version_forms_service.py`, `std_engine/api/template_version_workbench.py`, `std_engine/tests/test_std_phase10_template_version_forms.py`, `public/js/std_engine_workspace.js`, `public/css/std_engine_workspace.css`, `tests/ui/smoke/procurement/std-workbench-1001.spec.ts`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | Backend: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase10_template_version_forms` (4/4 pass). UI: `cd apps/kentender_v1 && npx playwright test tests/ui/smoke/procurement/std-workbench-1001.spec.ts --grep "STD-CURSOR-1007"` (pass, includes Forms-tab checks). Assets: `./scripts/bench-with-node.sh build --app kentender_procurement` (pass), `bench --site kentender.midas.com clear-cache` (pass). |
| Risks remaining | `bench restart` could not run in this environment due missing supervisor socket (`unix:///var/run/supervisor.sock no such file`); if stale workers persist on another runtime target, restart there before UAT. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-1011 |
| Reviewer | Engineering |
| Completed | Implemented Works Configuration tab server/UI path for template versions. Added `build_std_template_version_works_configuration` in `std_engine/services/template_version_works_service.py` and whitelisted API `get_std_template_version_works_configuration` in `std_engine/api/template_version_workbench.py`. Payload includes Works profile details, Works Requirement components, BOQ definition (including arithmetic correction stage), evaluation-rule templates, contract carry-forward templates, readiness-rule snapshot, and required warning copy for BOQ quantity ownership + contract price source from Evaluation/Award. Desk `public/js/std_engine_workspace.js` now fetches/renders `tpl-works` panel with required sections (`std-works-profile-selector`, `std-works-components`, `std-works-boq-definition`, `std-works-evaluation-rule-templates`, `std-works-contract-carry-forward-templates`, `std-works-readiness-rules`) and warning test IDs. |
| Not completed | Editable Works-configuration mutation flows and deeper rule authoring UI remain future tickets; this ticket is read-focused configuration visibility per pack acceptance. |
| Assumptions | Evaluation and carry-forward templates are represented through `STD Extraction Mapping` rows (source `Evaluation Rule`, target `DCM`) in current data model. |
| Files changed | `std_engine/services/template_version_works_service.py`, `std_engine/api/template_version_workbench.py`, `std_engine/tests/test_std_phase10_template_version_works.py`, `public/js/std_engine_workspace.js`, `tests/ui/smoke/procurement/std-workbench-1001.spec.ts`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | Backend: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase10_template_version_works` (3/3 pass). UI: `cd apps/kentender_v1 && npx playwright test tests/ui/smoke/procurement/std-workbench-1001.spec.ts --grep "STD-CURSOR-1007"` (1 passed, includes Works-tab assertions added for 1011). |
| Risks remaining | Current Works tab uses extraction-mapping proxies for evaluation/carry-forward datasets; if dedicated template doctypes are introduced later, service field mapping should be updated. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-1012 |
| Reviewer | Engineering |
| Completed | Added Mappings tab catalogue: `build_std_template_version_mappings_catalogue` in `std_engine/services/template_version_mappings_service.py` groups `STD Extraction Mapping` by target model (Bundle/DSM/DOM/DEM/DCM), surfaces `missing_coverage` (validation flags + gaps where forms/parameters/works components drive a model without a matching mapping, plus BOQ Definition DEM/DCM linkage), and `highlights` for Section IV DSM and Section III / evaluation-rule DEM. Whitelisted `get_std_template_version_mappings_catalogue` in `std_engine/api/template_version_workbench.py`. Desk `public/js/std_engine_workspace.js` renders `tpl-mappings` with sub-tabs, table, missing list, highlight blocks, read-only banner when `read_only`; CSS in `public/css/std_engine_workspace.css`. |
| Not completed | Authoring/edit flows for mappings (create/update) and deeper cross-STD validation UX remain future tickets; this ticket is read-only visibility per active/immutable guard. |
| Assumptions | Section Roman numerals match `STD Section Definition.section_number`; BOQ linkage gaps use `STD BOQ Definition` for the version when no row-level mapping names `BOQ Definition` with that code for DEM/DCM. |
| Files changed | `std_engine/services/template_version_mappings_service.py`, `std_engine/api/template_version_workbench.py`, `std_engine/tests/test_std_phase10_template_version_mappings.py`, `public/js/std_engine_workspace.js`, `public/css/std_engine_workspace.css`, `tests/ui/smoke/procurement/std-workbench-1001.spec.ts`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | Backend: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase10_template_version_mappings` (5/5 pass). UI: `cd apps/kentender_v1 && npx playwright test tests/ui/smoke/procurement/std-workbench-1001.spec.ts --grep "STD-CURSOR-1007"`. Assets: `./scripts/bench-with-node.sh build --app kentender_procurement` from bench root. |
| Risks remaining | Coverage heuristics may list BOQ or driver gaps on sparse fixtures; highlights depend on section_number and source_object_type conventions from seed/authoring. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-1013 |
| Reviewer | Engineering |
| Completed | Added `build_std_template_version_reviews_approval` in `std_engine/services/template_version_reviews_service.py` and whitelisted `get_std_template_version_reviews_approval` in `std_engine/api/template_version_workbench.py`. Payload includes `review_summary` (version/legal/policy/structure fields), `family` active flags, `governance_note`, `returned_corrections` when review status is Returned, fifteen-item `activation_checklist` (family, mandatory sections, ITT/GCC locks, TDS/SCC parameter heuristics, Section III DEM highlights, forms, works/BOQ, mappings gaps via mappings catalogue, works readiness snapshot, review clears, structure pass), `activation_legal_immutability_text` (pack wording), `activation_gates`, and `activation_ui_block_reason`. Desk `public/js/std_engine_workspace.js` renders `tpl-reviews` with summary, governance, returned list, checklist table, immutability blockquote, disabled “Activate version (Desk)” CTA with tooltip; `public/css/std_engine_workspace.css` adds reviews checklist chrome. |
| Not completed | Submit/Clear/Return review actions and live activation from workbench are intentionally not wired; operators use Desk + `transition_std_object` per governance note. |
| Assumptions | Checklist reuses mappings + works catalogues server-side; ITT/GCC locks inferred from locked section titles/codes; TDS/SCC rows use keyword heuristics on parameter codes/labels/groups. |
| Files changed | `std_engine/services/template_version_reviews_service.py`, `std_engine/api/template_version_workbench.py`, `std_engine/tests/test_std_phase10_template_version_reviews.py`, `public/js/std_engine_workspace.js`, `public/css/std_engine_workspace.css`, `tests/ui/smoke/procurement/std-workbench-1001.spec.ts`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | Backend: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase10_template_version_reviews` (5/5 pass). UI: `cd apps/kentender_v1 && npx playwright test tests/ui/smoke/procurement/std-workbench-1001.spec.ts --grep "STD-CURSOR-1007"`. Assets: `./scripts/bench-with-node.sh build --app kentender_procurement`. |
| Risks remaining | Checklist heuristics (ITT/GCC titles, TDS/SCC keywords) may differ from future seed conventions; operators must still use Desk for real transitions. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-1014 |
| Reviewer | Engineering |
| Completed | Added `build_std_template_version_audit_evidence` and `build_std_template_version_audit_export_csv` in `std_engine/services/template_version_audit_evidence_service.py`; whitelisted `get_std_template_version_audit_evidence` and `export_std_template_version_audit_evidence_csv` in `std_engine/api/template_version_workbench.py`. Aggregates `STD Audit Event` for the template version, its template family code, and STD instances using that version; returns chronological `lifecycle_timeline`, per-slice `evidence_sections`, `denied_events` for audit roles, scrubbed view + `privacy_note` for others, and CSV export for Auditor/Administrator/System Manager. Desk `tpl-audit-evidence` panel in `public/js/std_engine_workspace.js` with `std-audit-timeline-*`, slice sections, and `std-audit-export-csv` download wiring. `public/css/std_engine_workspace.css`: audit panel/table wrap. `audit_service.py`: `AUDIT_READ_ROLES` as `frozenset`. |
| Not completed | Signed export bundles, deep joins to generation jobs without instance `object_code`, and non-CSV evidence packs. |
| Assumptions | `event_type` strings remain stable for bucket heuristics; `TEMPLATE_VERSION` / `STD_INSTANCE` object conventions match `state_transition_service` / `record_std_audit_event`. |
| Files changed | `std_engine/services/template_version_audit_evidence_service.py`, `std_engine/api/template_version_workbench.py`, `std_engine/services/audit_service.py`, `std_engine/tests/test_std_phase10_template_version_audit_evidence.py`, `public/js/std_engine_workspace.js`, `public/css/std_engine_workspace.css`, `tests/ui/smoke/procurement/std-workbench-1001.spec.ts`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | Backend: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase10_template_version_audit_evidence` (4/4 pass). UI: `cd apps/kentender_v1 && npx playwright test tests/ui/smoke/procurement/std-workbench-1001.spec.ts --grep "STD-CURSOR-1007"`. Assets: `./scripts/bench-with-node.sh build --app kentender_procurement`. |
| Risks remaining | Heuristic buckets may mis-file rare `event_type` values; large histories may need server-side pagination later. |
| Ready for next ticket | Yes |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-1101 |
| Reviewer | Engineering |
| Completed | STD Instance workbench detail tabs (pack test IDs): Overview, Parameters, Works Requirements, BOQ, Generated Outputs, Readiness, Addendum Impact, Usage / Downstream Contracts, Audit & Evidence. Added `build_std_instance_workbench_shell` in `std_engine/services/instance_workbench_service.py` and whitelisted `get_std_instance_workbench_shell` in `std_engine/api/instance_workbench.py` (read-only when `instance_status` is Published Locked / Superseded / Cancelled; `addendum_guidance` for Published Locked, Locked Pre-Publication, Superseded). Desk `public/js/std_engine_workspace.js`: `detailTabMode === "instance"`, `injectStdInstanceDetailTabs`, overview panel (`std-instance-*` test IDs, `std-instance-addendum-path`), placeholders for later 1102+ tabs. `public/css/std_engine_workspace.css`: horizontal scroll for instance tab strip. |
| Not completed | Superseded by Phase 11 completion record below (1102–1108). |
| Assumptions | `instance_code` / `tender_code` / linked codes are business keys suitable for operator overview; no internal `name` exposed in UI. |
| Files changed | `std_engine/services/instance_workbench_service.py`, `std_engine/api/instance_workbench.py`, `std_engine/tests/test_std_phase11_instance_shell.py`, `public/js/std_engine_workspace.js`, `public/css/std_engine_workspace.css`, `tests/ui/smoke/procurement/std-workbench-1001.spec.ts`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | Backend: `bench run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase11_instance_shell` (6/6 pass). UI: `cd apps/kentender_v1 && npx playwright test tests/ui/smoke/procurement/std-workbench-1001.spec.ts --grep "STD-CURSOR-1101"` (1 passed; queues: draft → ready → published-locked → blocked). Assets: `./scripts/bench-with-node.sh build --app kentender_procurement` from bench root. |
| Risks remaining | Playwright skips only when no STD Instance exists in any instances-queue search on the site. |
| Ready for next ticket | Yes (Phase 12) |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-1102 — STD-CURSOR-1108 |
| Reviewer | Engineering |
| Completed | **1102** Instance parameter catalogue (`instance_parameter_catalogue_service`, `get_std_instance_parameter_catalogue`) with grouped defs, values, stale flag, tender-security hint, read-only/addendum banners; desk editors + save via `set_std_parameter_value` (actor defaults to session). **1103** Works panel (`instance_works_panel_service`, `get_std_instance_works_requirements_panel`) + works tab UI (components, attachment action labels per pack, save structured text). **1104** BOQ panel (`instance_boq_workbench_service`, `get_std_instance_boq_workbench_panel`) with summary bar / bill list / item grid / validation / import placeholders / DSM impact note; `validate_boq_instance(..., persist=False)` for read-only preview. **1105** Outputs preview (`instance_outputs_preview_service`, `get_std_instance_outputs_preview`) + DEM/DOM/DCM warning copy + job list. **1106** Readiness panel (`instance_readiness_panel_service`, `get_std_instance_readiness_panel`, `run_std_instance_readiness_now`) + findings sort + manual-ready forbidden copy. **1107** Addendum impact list (`instance_addendum_panel_service`). **1108** Tender STD panel API (`tender_std_panel_service`, `get_tender_std_panel_data`) + `public/js/tender_std_panel.js` on `STD Tender Binding` (`hooks.py` `doctype_js`). Regression: `defaultdict` import in `template_version_parameters_service.py`. |
| Not completed | Full BOQ import pipeline UI, rich downstream contract modelling, addendum “Request” deep-link to impact workflow, and full TM v2 shell beyond STD Tender Binding form. |
| Assumptions | Tender “v2” surface is represented by STD Tender Binding DocType until a dedicated tender workbench ships; currency summary uses KES placeholder when BOQ definition has no currency field. |
| Files changed | `std_engine/services/instance_*.py`, `std_engine/services/tender_std_panel_service.py`, `std_engine/api/instance_workbench.py`, `std_engine/api/tender_std_panel.py`, `std_engine/tests/test_std_phase11_instance_panels.py`, `std_engine/services/boq_instance_service.py`, `std_engine/services/parameter_value_service.py`, `std_engine/services/section_attachment_service.py`, `std_engine/services/works_requirements_service.py`, `std_engine/services/template_version_parameters_service.py`, `public/js/std_engine_workspace.js`, `public/js/tender_std_panel.js`, `kentender_procurement/hooks.py` |
| Test evidence | Backend: `bench run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase11_instance_panels` (10/10 pass); `test_std_phase11_instance_shell` (6/6); `test_std_parameter_value_service` (3/3). UI: `npx playwright test tests/ui/smoke/procurement/std-workbench-1001.spec.ts --grep "STD-CURSOR-1101"` (covers 1101+1102 instance parameters poll). **STD Tender Binding** form panel not automated in Playwright (requires DocType form session). Assets: `./scripts/bench-with-node.sh build --app kentender_procurement`. |
| Risks remaining | `tender_std_panel.js` prepends a custom HTML block on each refresh (stable host via `frm._kt_tm_std_panel_host`); operators should hard-refresh after deploy. |
| Ready for next ticket | Yes (Phase 13) |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | STD-CURSOR-1201 — STD-CURSOR-1206 |
| Reviewer | Engineering |
| Completed | Phase 12 Smoke Contract automation: **1201** DOC1/STD-WORKS/building version/profile/parts/sections/source-trace (`phase12_smoke_helpers.py`, `test_std_phase12_1201_seed_load_smoke.py`). **1202** ITT/GCC locked + TDS/SCC parameter-only (tree + DB); required-parameter readiness blocker; published BOQ edit denial; tender-security dependency (`test_std_phase12_1202_locked_and_parameters_smoke.py`). **1203** Section IV in bundle, DSM read-only BOQ, DOM without arithmetic correction, DEM arithmetic stage, DCM carry-forward, BOQ validate (`test_std_phase12_1203_output_models_smoke.py`). **1204** bundle manifest + preface exclusion, published bundle immutability, readiness pass/block/manual field denial, addendum analyze + deadline regeneration (`test_std_phase12_1204_bundle_readiness_addendum_smoke.py`). **1205** binding readiness gating, DOM/DCM guards, manual submission/opening/eval/contract denial + published output regression (`test_std_phase12_1205_cross_module_negative_smoke.py`). **1206** Playwright `STD-CURSOR-1206 smoke contract UI` in `std-workbench-1001.spec.ts`. |
| Not completed | Dedicated upload-as-source denial API not in repo (no Upload STD in UI + TM guards). Single tender-publish vs STD readiness guard not centralized beyond binding `std_outputs_current`. |
| Assumptions | DOC1 Works Building seed on site for 1201/1202 seed-only tests (skipped otherwise). PH6 `_Phase6Fixture` for generation tests. Run Phase 12 backend modules sequentially if parallel runs deadlock on `DOC1_WORKS_PH6` inserts. |
| Files changed | `std_engine/tests/phase12_smoke_helpers.py`, `std_engine/tests/test_std_phase12_1201_seed_load_smoke.py`, `test_std_phase12_1202_locked_and_parameters_smoke.py`, `test_std_phase12_1203_output_models_smoke.py`, `test_std_phase12_1204_bundle_readiness_addendum_smoke.py`, `test_std_phase12_1205_cross_module_negative_smoke.py`, `tests/ui/smoke/procurement/std-workbench-1001.spec.ts`, `STD-Works-Implementation-Tracker.md` |
| Test evidence | Backend (sequential): `bench run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase12_1201_seed_load_smoke` (7/7); `--module ...1202...` (7/7); `--module ...1203...` (6/6); `--module ...1204...` (7/7); `--module ...1205...` (10/10). UI: `cd apps/kentender_v1 && npx playwright test tests/ui/smoke/procurement/std-workbench-1001.spec.ts --grep "STD-CURSOR-1206" --retries=0`. |
| Risks remaining | Parallel workers may deadlock on PH6 fixture `Source Document Registry` insert; serialize modules in CI. |
| Ready for next ticket | Yes (Phase 13) |

| Field | Value |
|---|---|
| Date | 2026-04-29 |
| Ticket(s) | UI/UX alignment plan (gap matrix P0–P6 + TDD/Playwright gate) |
| Reviewer | Engineering |
| Completed | **IA (§3.1):** `Governance & Configuration` parent workspace + `STD Engine` `parent_page`; procurement sidebar section + link; fixtures extended in `hooks.py`; boot fast-path `governance & configuration` in `workspace_permissions.py`. **URL (§3.3):** `std_scope`, `std_queue`, `std_code` query sync in `std_engine_workspace.js`. **Header (§5):** product subtitle; `header_actions` from `landing.build_std_header_actions` + client `runStdHeaderAction`. **Roles:** `resolve_std_workbench_chrome` + `search_std_workbench_objects` scope/queue guard; `visibility_policy` `full_governance` / `instance_operational`. **Queues (§8.2.4):** inline limit + “More queues” dropdown. **Tests:** `STD-UI-UX-Alignment-Gap-Matrix.md`, `test_std_phase13_*.py`, Playwright helpers for overflow chips; `test_std_phase10_scope_queue` policy assertion. |
| Not completed | Full §15–32 content parity line-by-line; wizards §33; literal `/desk/std-engine/versions/...` path routes (query contract only). |
| Assumptions | `bench --site <site> migrate` loads new Workspace + `after_migrate` reapplies `workspace_sidebar/procurement.json`. |
| Files changed | `workspace/governance_and_configuration/`, `workspace/std_engine/std_engine.json`, `workspace_sidebar/procurement.json`, `setup/workspace_permissions.py`, `hooks.py`, `std_engine/api/landing.py`, `public/js/std_engine_workspace.js`, `public/css/std_engine_workspace.css`, `docs/.../STD-UI-UX-Alignment-Gap-Matrix.md`, `tests/ui/smoke/procurement/std-workbench-1001.spec.ts`, `std_engine/tests/test_std_phase13_*.py`, `std_engine/tests/test_std_phase10_scope_queue.py`, `setup/tests/test_workspace_sidebar_fastpath.py` |
| Test evidence | `bench run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase13_workbench_chrome_visibility`; `--module ...test_std_phase13_prd_boq_ux_labels`; `--module ...test_workspace_sidebar_fastpath`; `--module ...test_std_phase10_scope_queue`. `cd apps/kentender_v1 && npx playwright test tests/ui/smoke/procurement/std-workbench-1001.spec.ts` (exit 0; occasional flaky retry on STD-CURSOR-1206). `./scripts/bench-with-node.sh build --app kentender_procurement`. |
| Risks remaining | `_` must never shadow `frappe._` / gettext `_` in `landing.py` unpacks. |
| Ready for next ticket | Partial (residual §15–32 parity deferred) |

| Field | Value |
|---|---|
| Date | 2026-04-30 |
| Ticket(s) | STD-CURSOR-1301 |
| Reviewer | Engineering |
| Completed | Implemented cross-object evidence export service `build_std_evidence_export_package(object_type, object_code, actor)` with role-gated access (`AUDIT_READ_ROLES`), object validation, and CSV export payload for **Template Version** and **STD Instance**. Added whitelisted endpoint `std_engine.api.evidence_export.export_std_evidence_package`. Added lineage-rich package sections for instance export (source document, family/version/profile, sections/clauses, parameters, works, BOQ, attachments, generated outputs incl. Bundle/DSM/DOM/DEM/DCM, readiness runs, addendum analyses, supersession chain, audit events, downstream bindings). Wired global header action **Evidence Export** in `std_engine_workspace.js` to export selected object and download CSV. Export action now writes audit event `EVIDENCE_EXPORTED`. |
| Not completed | STD-CURSOR-1302 production safety checks (out of scope). |
| Assumptions | Evidence export requires selecting a template version or STD instance in workbench; if none selected, UI routes to audit scope and prompts user to select one. |
| Files changed | `std_engine/services/evidence_export_service.py`, `std_engine/api/evidence_export.py`, `std_engine/tests/test_std_phase13_evidence_export_service.py`, `public/js/std_engine_workspace.js`, `tests/ui/smoke/procurement/std-workbench-1001.spec.ts`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | `bench run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase13_evidence_export_service` (7/7 pass); `bench run-tests --app kentender_procurement --module kentender_procurement.std_engine.tests.test_std_phase10_template_version_audit_evidence` (4/4 pass); `cd apps/kentender_v1 && npx playwright test tests/ui/smoke/procurement/std-workbench-1001.spec.ts --grep "global header actions|Evidence Export downloads"` (2/2 pass); `./scripts/bench-with-node.sh build --app kentender_procurement` (pass). |
| Risks remaining | Instance package section coverage depends on DocType field availability in target site schema; service intentionally uses safe field introspection and may output partial sections when fields/doctypes are absent. |
| Ready for next ticket | Yes (STD-CURSOR-1302) |

| Field | Value |
|---|---|
| Date | 2026-04-30 |
| Ticket(s) | STD-CURSOR-1302 |
| Reviewer | Engineering |
| Completed | Implemented production preflight report service `build_std_production_safety_report(smoke_tests_passed, actor)` and whitelisted API `std_engine.api.production_safety.get_std_production_safety_report`. Report evaluates 7 required checks: canonical DOC1 seed presence, explicit smoke signal, feature flag default review, active DOC1 template version, legacy upload-as-source risk signal (`STD Tender Binding.std_outputs_current=0`) under STD v2, manual downstream guard enforcement for STD-backed tenders (submission/opening/evaluation), and append-only audit verification probe. Added audit events `SAFETY_CHECK_PROBE` and `SAFETY_CHECK_RUN` to allowed event types. |
| Not completed | Live Playwright execution of deployment checklist UI slice was not rerun because ticket scope is backend command/report; existing smoke gate remains documented in prior entries. |
| Assumptions | `smoke_tests_passed` is provided by release operator/CI at invocation time; report keeps this explicit to avoid inferring smoke status from stale artifacts. |
| Files changed | `std_engine/services/production_safety_service.py`, `std_engine/api/production_safety.py`, `std_engine/tests/test_std_phase13_production_safety_checks.py`, `std_engine/services/audit_service.py`, `docs/prompts/6.a. STD/STD-Works-Implementation-Tracker.md` |
| Test evidence | `bench --site kentender.midas.com run-tests --module kentender_procurement.std_engine.tests.test_std_phase13_production_safety_checks` (3/3 pass). |
| Risks remaining | Legacy upload-as-source detection is inferred through `std_outputs_current=0` on STD-bound tender bindings; if future data model introduces an explicit legacy-source flag, this check should be tightened to that field. |
| Ready for next ticket | Yes |

