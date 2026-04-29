# STD Engine Works v2 - Implementation Tracker

**Prompt pack:** `apps/kentender_v1/docs/prompts/6.a. STD/1...10`  
**Cursor pack:** `apps/kentender_v1/docs/prompts/6.a. STD/10. std_engine_works_configuration_cursor_implementation_pack.md`  
**Source PDF:** `apps/kentender_v1/docs/prompts/6.a. STD/DOC 1. STD FOR WORKS-BUILDING AND ASSOCIATED CIVIL ENGINEERING WORKS Rev April 2022.pdf`

## Scope guard (current execution)

- Phase 0 planning artifacts are complete and retained as baseline.
- Current approved execution scope: **Phase 1 through Phase 7 STD-CURSOR-0702** (readiness validator + stale output detection; no Desk UI in this phase).
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

**Last updated:** 2026-04-29 (through Phase 7 STD-CURSOR-0701 to STD-CURSOR-0702; Phases 1–6 as previously executed)

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
| STD-CURSOR-0801 | Addendum impact analyzer | Pending |
| STD-CURSOR-0802 | Addendum regeneration service | Pending |

### Phase 9 - Tender Management integration refactor (reference only)

| Ticket | Description | Status |
|---|---|---|
| STD-CURSOR-0901 | STD binding to Tender Management v2 | Pending |
| STD-CURSOR-0902 | Disable manual submission requirements | Pending |
| STD-CURSOR-0903 | Disable manual evaluation criteria | Pending |
| STD-CURSOR-0904 | Disable manual opening fields outside DOM | Pending |
| STD-CURSOR-0905 | Bind Contract Management to DCM | Pending |

### Phase 10 - STD workbench UI (reference only)

| Ticket | Description | Status |
|---|---|---|
| STD-CURSOR-1001 | Workbench route and shell | Pending |
| STD-CURSOR-1002 | KPI/risk strip | Pending |
| STD-CURSOR-1003 | Scope tabs and queue bar | Pending |
| STD-CURSOR-1004 | Search and filters | Pending |
| STD-CURSOR-1005 | Object list panel | Pending |
| STD-CURSOR-1006 | Detail panel and action bar | Pending |
| STD-CURSOR-1007 | Template version detail tabs | Pending |
| STD-CURSOR-1008 | Structure tab | Pending |
| STD-CURSOR-1009 | Parameters tab | Pending |
| STD-CURSOR-1010 | Forms tab | Pending |
| STD-CURSOR-1011 | Works configuration tab | Pending |
| STD-CURSOR-1012 | Mappings tab | Pending |
| STD-CURSOR-1013 | Reviews and approval tab | Pending |
| STD-CURSOR-1014 | Audit and evidence tab | Pending |

### Phase 11 - TM integration UI (reference only)

| Ticket | Description | Status |
|---|---|---|
| STD-CURSOR-1101 | STD instance detail tabs | Pending |
| STD-CURSOR-1102 | Instance parameters UI | Pending |
| STD-CURSOR-1103 | Works requirements UI | Pending |
| STD-CURSOR-1104 | BOQ configuration UI | Pending |
| STD-CURSOR-1105 | Generated outputs preview UI | Pending |
| STD-CURSOR-1106 | Readiness UI | Pending |
| STD-CURSOR-1107 | Addendum impact UI | Pending |
| STD-CURSOR-1108 | TM v2 STD panel integration UI | Pending |

### Phase 12 - Smoke contract automation (reference only)

| Ticket | Description | Status |
|---|---|---|
| STD-CURSOR-1201 | Seed load smoke tests | Pending |
| STD-CURSOR-1202 | Locked section and parameter tests | Pending |
| STD-CURSOR-1203 | DSM/DOM/DEM/DCM/BOQ tests | Pending |
| STD-CURSOR-1204 | Bundle/readiness/addendum tests | Pending |
| STD-CURSOR-1205 | Cross-module and negative regression tests | Pending |
| STD-CURSOR-1206 | UI smoke tests | Pending |

### Phase 13 - Hardening and evidence export (reference only)

| Ticket | Description | Status |
|---|---|---|
| STD-CURSOR-1301 | Evidence export service | Pending |
| STD-CURSOR-1302 | Production safety checks | Pending |

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

