# Strategy Alignment — MVP 1 Requirements

**Document ID:** STRATEGY-MVP1-REQ-1.1  
**Status:** Locked  
**Date:** 3 August 2026  
**Approved:** 3 August 2026  
**Change control:** Functional changes require a new document version  
**Module:** Strategy Alignment  
**Application:** KenTender  
**Primary entity fixture:** Ministry of Health  

### Source baseline

- KenTender Statutory and Public-Value Obligations Matrix, version 1.1
- Current Strategy Alignment implementation summary supplied for this redesign
- Constitution of Kenya, Public Procurement and Asset Disposal Act, Public Procurement and Asset Disposal Regulations, and National Public Procurement and Asset Disposal Policy

## 1. Purpose

Strategy Alignment shall provide the controlled strategic foundation for public procurement. It shall define what the procuring entity intends to achieve, how achievement is measured, which cross-cutting public-value objectives apply, and which approved strategic references downstream modules may use.

The module shall not be a document archive or a cosmetic classification tree. It shall support traceability from strategy to budget, demand, planning, tender treatment, contract performance, assets and disposal outcomes.

## 2. MVP outcomes

MVP 1 shall enable a procuring entity to:

1. Create and govern versioned strategic plans.
2. Define a clean hierarchy of programmes, optional sub-programmes, strategic outcomes, performance indicators and performance targets.
3. Maintain an approved Public Value Objective Catalogue.
4. Adopt selected public-value objectives into a strategic plan through Plan Value Commitments.
5. Expose valid Active strategy references and applicable value commitments to downstream modules.
6. Record periodic target measurements separately from target definitions.
7. Verify measurements and require corrective action for material underperformance.
8. Show where strategic targets and value commitments are used downstream.
9. Preserve historical references when a plan or objective is superseded.
10. Provide a complete approval and audit record.
11. Provide managers and senior stakeholders with a read-only, value-driven view of strategic performance, procurement contribution, public-value treatment and exceptions requiring intervention.

## 3. Design principles

1. **Legal compliance is the operating floor.** It is not a score or optional objective.
2. **Objectives, indicators, targets and measurements are separate concepts and records.**
3. **Strategy defines available outcomes and objectives; downstream modules decide procurement-specific treatment through their own approvals.**
4. **Only relevant public-value objectives are selected.** The system shall not present every objective to every procurement.
5. **Approved and Active records are immutable.** Material change creates a new version.
6. **Historical references must remain resolvable.** Supersession shall not rewrite prior decisions.
7. **Actual performance is time-series evidence.** A new result shall not overwrite an earlier result.
8. **System intelligence should be derived.** Users shall not manually recreate cycle-time, usage or coverage reports that the system can calculate.
9. **Simple structured rules take precedence over configurable scripting.** MVP 1 shall not include an arbitrary formula or rules engine.
10. **The user interface shall optimise for comprehension and completion, not expose the underlying tables.**
11. **Management reporting shall distinguish evidence from inference.** The system shall show verified outcomes and authoritative procurement references without claiming that procurement caused an outcome or summing overlapping lifecycle values.

## 4. Scope

### 4.1 Included

- Entity-scoped strategic-plan portfolio
- Strategic-plan creation, versioning, approval, activation, supersession and archiving
- Programme and optional sub-programme structure
- Strategic outcomes
- Performance indicators
- Performance targets
- Public Value Objective Catalogue
- Plan Value Commitments
- Simple objective-applicability rules
- Target measurement submission and verification
- Strategy corrective actions
- Downstream strategy-reference APIs
- Applicable-value-commitment APIs
- Downstream usage and alignment-coverage views
- Strategy Performance management view and controlled report export
- Readiness validation
- Role and permission controls
- Audit history
- Ministry of Health seed fixture
- Replacement of the current MVP strategy data structures and obsolete compatibility behaviour

### 4.2 Excluded

- National or county planning-system API import
- AI-generated strategy, targets or measurements
- Arbitrary formula builders
- Predictive performance forecasting
- Full enterprise performance-management functionality
- Employee performance appraisal
- Project or programme delivery management
- Tender criteria, specifications or contract clause authoring
- Procurement Value Case authoring, which belongs to Demand Intake
- Contract KPI administration, which belongs to Contract Management
- Public disclosure of strategy records
- Complex weighted strategy scoring
- Automatic adverse action based on target underperformance
- Predictive management analytics or automated management recommendations
- Causal attribution of strategic outcomes to procurement without verified supporting evidence
- Unverified savings, benefits or cost-avoidance claims

## 5. Terminology

| Term | Definition |
|---|---|
| Strategic Plan | An approved, time-bound plan belonging to a procuring entity |
| Programme | A major area of strategic intervention within a plan |
| Sub-programme | An optional subdivision of a programme |
| Strategic Outcome | The intended change or result |
| Performance Indicator | The defined measure used to assess an outcome |
| Performance Target | The expected indicator value, direction and period |
| Performance Measurement | A dated actual result submitted against a target |
| Public Value Objective | A reusable, approved objective covering effectiveness, economy, efficiency, competition, inclusion, sustainability, integrity or resilience |
| Plan Value Commitment | Adoption of a Public Value Objective within a specific strategic-plan version |
| Strategy Reference | A versioned reference selected by a downstream module to an Active strategy node |
| Primary Alignment | The principal target to which a demand or other downstream record contributes |
| Supporting Alignment | An additional material strategic contribution |
| Enforcement Guidance | The approved suggested downstream treatment; it is not itself a tender rule |

## 6. Controlled value pillars

MVP 1 shall use the following controlled pillars:

1. Strategic and service outcomes
2. Economy and whole-life value
3. Process efficiency
4. Fair competition and market access
5. Inclusion and economic development
6. Sustainability and asset stewardship
7. Integrity and accountability
8. Contract performance and resilience

Changing this list is an administrative configuration change. A pillar does not determine a score or enforcement route.

## 7. Functional requirements

### 7.1 Strategic-plan portfolio and identity

| ID | Requirement |
|---|---|
| STR-FR-001 | The system shall list plans scoped to the current procuring entity. |
| STR-FR-002 | Users with cross-entity authority may switch entity context; other users shall not access another entity's plan records. |
| STR-FR-003 | Each logical plan shall have a stable `plan_code` and one or more immutable versions. |
| STR-FR-003a | The system shall automatically assign an immutable, human-readable reference when the record is first saved. Users shall not be required to create or maintain reference codes. Relationships between records and downstream modules shall use immutable internal identifiers rather than reference strings. |
| STR-FR-004 | Each plan version shall have its own internal identifier, version number, status, effective period and audit history. |
| STR-FR-005 | The system shall prevent activation of a plan version when another Active plan for the same procuring entity, plan type and organisational scope has an overlapping effective period. Only one Active Entity Strategic Plan may cover any given date for an entity (the entity is the scope). Programme Strategy, Thematic Plan and Annual Implementation Plan versions may be Active concurrently only when they have a distinct scope and a recorded `parent_plan` relationship to an Entity Strategic Plan of the same entity. Only one version of the same `plan_code` may be Active; activating a successor shall supersede the prior Active version of that `plan_code`. |
| STR-FR-006 | Plan search shall support code, title, type, period, status and entity. |
| STR-FR-007 | Portfolio counts shall be derived for Draft, Submitted, Active, expiring and measurement-attention plans. |

### 7.2 Strategic hierarchy

| ID | Requirement |
|---|---|
| STR-FR-010 | A plan shall contain one or more Programmes. |
| STR-FR-011 | A Programme may contain zero or more Sub-programmes. |
| STR-FR-012 | A Strategic Outcome shall belong to a Programme and may additionally belong to a Sub-programme within that Programme. |
| STR-FR-013 | A Performance Indicator shall belong to exactly one Strategic Outcome. |
| STR-FR-014 | A Performance Target shall belong to exactly one Performance Indicator. |
| STR-FR-015 | A parent and child shall belong to the same plan version. |
| STR-FR-016 | Business codes shall be unique within the entity and logical plan version as defined in section 12. |
| STR-FR-017 | The Structure view shall render the hierarchy in business order and allow authorised editing only while the plan is editable. |
| STR-FR-018 | Nodes referenced downstream shall not be deleted; an editable successor version may omit or replace them. |
| STR-FR-019 | Reordering shall change display order only and shall be audited. |
| STR-FR-020 | The system shall not create placeholder Sub-programmes where the plan does not use them. |

### 7.3 Strategic outcomes

| ID | Requirement |
|---|---|
| STR-FR-025 | Each outcome shall state the intended change or result, not a measure or target value. |
| STR-FR-026 | Each outcome shall have a responsible function and may have an executive owner. |
| STR-FR-027 | An outcome may link to one or more active Plan Value Commitments. |
| STR-FR-028 | Outcome descriptions shall support plain text only in MVP 1. |

### 7.4 Performance indicators and targets

| ID | Requirement |
|---|---|
| STR-FR-030 | Each indicator shall define its name, measurement method, unit, frequency, data source and responsible function. |
| STR-FR-031 | Supported measurement types shall be Numeric, Percentage, Currency, Duration, Count, Milestone and Boolean. |
| STR-FR-032 | Supported comparison directions shall be At least, At most, Equal to, Increase to, Reduce to and Achieve by date, constrained by measurement type. |
| STR-FR-033 | A target shall define a baseline status, target value, period and tolerance where applicable. |
| STR-FR-034 | Baseline status shall be Known, To be established or Not applicable. |
| STR-FR-035 | A Known baseline requires value, as-of date and source. |
| STR-FR-036 | A target shall define the responsible benefit owner and measurement verifier. |
| STR-FR-037 | Target values and units shall conform to the parent indicator's measurement definition. |
| STR-FR-038 | A target may be annual, quarterly, monthly, due-date or plan-end. |
| STR-FR-039 | A plan may not be submitted with an incomplete target. |

### 7.5 Public Value Objective Catalogue

| ID | Requirement |
|---|---|
| STR-FR-045 | The catalogue shall be entity-scoped, with optional system-level objectives made available to authorised entities. |
| STR-FR-046 | Each objective shall have a stable code, title, pillar, description, source, applicability, measure guidance, evidence guidance, owner and effective period. |
| STR-FR-047 | Source type shall be Constitution, Act, Regulation, Policy, Entity Strategy or Management Objective. |
| STR-FR-048 | Statutory-source references shall be informational and auditable; the catalogue shall not attempt to replace the legal source. |
| STR-FR-049 | Objective applicability shall be Universal consideration, Category-triggered, Procurement-type-triggered, Asset-triggered or Demand-selected. |
| STR-FR-050 | Category triggers shall use the platform's controlled procurement category master. |
| STR-FR-051 | MVP 1 shall support simple inclusion triggers only; compound scripted rules are excluded. |
| STR-FR-052 | Each objective shall identify default enforcement guidance from the controlled routes in section 8. |
| STR-FR-053 | Enforcement guidance shall not create a bidder requirement, evaluation criterion or contract obligation without downstream approval. |
| STR-FR-054 | Only Active objectives may be added to new Plan Value Commitments. |
| STR-FR-055 | Retired and Superseded objectives shall remain visible on historical records. |

### 7.6 Plan Value Commitments

| ID | Requirement |
|---|---|
| STR-FR-060 | A plan shall adopt a Public Value Objective through a Plan Value Commitment rather than copying its definition. |
| STR-FR-061 | The commitment shall identify its plan-specific rationale, consideration level, responsible owner and linked outcomes or targets. |
| STR-FR-062 | Consideration level shall be Required consideration, Recommended consideration or Available. |
| STR-FR-063 | Required consideration means that a downstream Value Case must include the objective or record an approved not-applicable reason. |
| STR-FR-064 | A Plan Value Commitment may narrow but shall not silently expand the approved objective's applicability. |
| STR-FR-065 | Plan Value Commitments shall lock with the approved plan version. |
| STR-FR-066 | A plan-readiness check shall identify commitments with no linked outcome or target. |

### 7.7 Performance measurements

| ID | Requirement |
|---|---|
| STR-FR-070 | Actual performance shall be stored as separate Performance Measurement records. |
| STR-FR-071 | A measurement shall specify target, period, actual value, measurement date, evidence, source and submitter. |
| STR-FR-072 | The system shall prevent duplicate measurements for the same target and measurement period unless the earlier record is formally superseded. |
| STR-FR-073 | The system shall calculate variance and measurement result status using the target definition. |
| STR-FR-074 | Measurement result status shall be On track, At risk or Off track. Target-period roll-up status may additionally be Not due or No data when no measurement exists. |
| STR-FR-075 | Workflow status shall remain separate: Draft, Submitted, Returned, Verified or Rejected. |
| STR-FR-076 | A measurement submitter shall not verify the same measurement. |
| STR-FR-077 | Verification shall record verifier, date, decision and comments. |
| STR-FR-078 | Evidence shall be viewable from the verification screen without duplicating the document. |
| STR-FR-079 | A verified Off track measurement requires a corrective action unless the verifier records an authorised exception. |
| STR-FR-080 | A later result shall not overwrite or conceal an earlier result. |

### 7.8 Corrective actions

| ID | Requirement |
|---|---|
| STR-FR-085 | A corrective action shall identify the affected target and measurement, action, owner, due date and expected resolution. |
| STR-FR-086 | Corrective-action statuses shall be Open, In progress, Submitted for verification, Verified complete and Cancelled. |
| STR-FR-087 | The action owner shall not verify their own action. |
| STR-FR-088 | Cancellation requires an authorised reason and approver. |
| STR-FR-089 | Overdue corrective actions shall appear on the portfolio and responsible user's work queue. |

### 7.9 Downstream strategy references

| ID | Requirement |
|---|---|
| STR-FR-095 | New downstream selections shall use only effective Active plan versions. Budget Lines shall link primarily to Performance Targets on the Active Entity Strategic Plan for the entity; targets on Active Programme Strategy, Thematic Plan or Annual Implementation Plan versions may be used only as supporting links. |
| STR-FR-096 | A reference shall identify the plan version, selected node and complete resolved path. |
| STR-FR-097 | The Strategy service shall validate that the selected node belongs to the stated plan version and path. |
| STR-FR-098 | Historical references shall remain resolvable after supersession or archival. |
| STR-FR-099 | Strategy Alignment shall expose, but not own, primary and supporting alignment records created by downstream modules. |
| STR-FR-100 | Demand Intake shall require one primary Performance Target alignment for its Procurement Value Case. |
| STR-FR-101 | Supporting target alignments shall require a reason. |
| STR-FR-102 | Downstream modules shall store internal identifiers and a human-readable reference snapshot for audit readability. |
| STR-FR-103 | Strategy node renaming in a successor version shall not alter an earlier snapshot. |

### 7.10 Applicability and downstream value commitments

| ID | Requirement |
|---|---|
| STR-FR-110 | Strategy shall expose Active Plan Value Commitments applicable to a downstream category, procurement type or asset condition. |
| STR-FR-111 | The response shall identify whether consideration is Required, Recommended or Available. |
| STR-FR-112 | Downstream treatment decisions and exclusions shall be owned and approved by the consuming module. |
| STR-FR-113 | Strategy shall receive read-only usage references to the resulting Value Cases, tenders, contracts and outcome records. |

### 7.11 Usage and coverage intelligence

| ID | Requirement |
|---|---|
| STR-FR-120 | The Plan workspace shall show downstream use by Budget, Demand, Planning, Tender, Contract, Asset and Disposal where data exists. |
| STR-FR-121 | Usage counts shall be derived from authoritative references and shall not be manually editable. |
| STR-FR-122 | The portfolio shall identify Active targets with no linked budget or demand. |
| STR-FR-123 | The portfolio shall identify downstream records with invalid or superseded references only where remediation is required; valid historical references shall not be flagged. |
| STR-FR-124 | No spend or benefit shall be attributed to a target without a valid alignment reference. |

### 7.12 Management monitoring and reporting

| ID | Requirement |
|---|---|
| STR-FR-130 | Strategy Alignment shall provide a read-only Strategy Performance view for managers and senior stakeholders, separate from the plan-maintenance workspace. |
| STR-FR-131 | Strategy Viewer shall act as the read-only management/stakeholder profile and shall open Strategy Performance by default; authorised operational roles may switch between Strategy Performance and the Strategy Portfolio. |
| STR-FR-132 | The view shall be scoped by the user's entity or cross-entity authority and shall support filters for Active plan, reporting period, Programme and Sub-programme where used. |
| STR-FR-133 | The view shall show target-result distributions derived from the latest applicable Verified measurements: On track, At risk, Off track, Not due and No data. |
| STR-FR-134 | An Outcome summary shall show its target-status distribution and use `Needs attention` when any current target is At risk, Off track or overdue without required data; it shall not conceal the underlying distribution behind a score. |
| STR-FR-135 | The view shall identify missing, overdue, Returned and Rejected measurements separately from verified performance results. |
| STR-FR-136 | The view shall show open and overdue Strategy Corrective Actions, their owners, due dates and direct review links. |
| STR-FR-137 | Procurement contribution shall be derived only from valid alignment references and shall show Budget, Demand, Planning, Tender and Contract counts and values by outcome or target where authoritative data exists. |
| STR-FR-138 | Values from different procurement lifecycle stages shall be labelled separately and shall not be summed as if they were additive. |
| STR-FR-139 | A funding gap may be shown only where approved budget and aligned approved demand or plan values are comparable by period, currency and scope; the calculation basis shall be visible. |
| STR-FR-140 | The view shall not claim savings, cost avoidance, benefits or causal outcome contribution unless an authoritative downstream record provides an approved baseline, method and verified value. |
| STR-FR-141 | Public-value reporting shall distinguish consideration from achievement: downstream Value Case treatment shows whether a commitment was addressed, while achievement requires a linked Verified target measurement or another authoritative verified outcome record. |
| STR-FR-142 | The view shall show Required Plan Value Commitments with missing downstream treatment or approved exclusions as exceptions requiring review, without treating them as automatic tender criteria. |
| STR-FR-143 | Every management metric shall support drill-down to the contributing targets, measurements, corrective actions or authorised downstream references. |
| STR-FR-144 | The view shall display an `As at` timestamp and source-coverage note so users can identify unavailable or stale contributing modules. |
| STR-FR-145 | Authorised users may export the current filtered Strategy Performance view as a controlled management report containing filter context, generation time, source coverage and traceable record references. |
| STR-FR-146 | Performance data, procurement contribution and management reports shall be system-derived and shall not be editable from Strategy Performance. |
| STR-FR-147 | Strategy Performance shall not duplicate generic platform Analytics; it shall remain limited to strategy outcomes, targets, public-value commitments, procurement alignment and required management intervention. |

## 8. Controlled enforcement-guidance routes

| Route | Meaning in Strategy Alignment |
|---|---|
| Strategic outcome | Measure the result at entity or programme level |
| Demand gate | Require consideration before a demand proceeds |
| Planning decision | Inform aggregation, method, market or delivery strategy |
| Mandatory specification | Candidate for a tender minimum requirement, subject to tender approval |
| Preliminary criterion | Candidate for an authorised eligibility or mandatory criterion, subject to legal and tender approval |
| Evaluated criterion | Candidate for disclosed evaluation treatment, subject to legal and tender approval |
| Contract obligation or KPI | Candidate for contract measurement after award |
| Asset or disposal control | Candidate for asset custody, reuse, valuation or lawful disposal control |
| Reporting only | Measure or disclose without affecting bidder eligibility or award |

## 9. Clean domain model

### 9.1 Strategic Plan

| Field | Requirement |
|---|---|
| internal_id | System-generated immutable identifier |
| plan_code | System-assigned immutable reference (`{PE}-SP-####`) on first save; same value across versions of the logical plan |
| version_number | Required positive integer, unique within plan_code and entity |
| title | Required display title |
| procuring_entity | Required entity reference |
| plan_type | Entity Strategic Plan, Programme Strategy, Thematic Plan or Annual Implementation Plan |
| scope_type | Required organisational scope kind (Procuring Entity, Programme or Entity Unit). For Entity Strategic Plan the scope is always Procuring Entity. |
| scope_id | Required identifier of the organisational scope (for Entity Strategic Plan, the procuring entity). Distinct from other Active plans of the same type. |
| parent_plan | Required for Programme Strategy, Thematic Plan and Annual Implementation Plan; Link to an Entity Strategic Plan of the same procuring entity (Active or Approved). Null for Entity Strategic Plan. |
| start_date / end_date | Required valid effective period |
| description | Optional plain text |
| supersedes_plan_version | Required for successor versions after the first |
| status | Workflow-controlled |
| submitted_by / submitted_at | System-controlled |
| approved_by / approved_at | System-controlled |
| activated_by / activated_at | System-controlled |
| return_reason | Required when returned |

### 9.2 Programme

| Field | Requirement |
|---|---|
| internal_id | Immutable identifier |
| plan_version | Required parent |
| programme_code | System-assigned immutable reference (`{PE}-PROG-####`) on first save |
| title | Required |
| description | Optional |
| responsible_function | Required |
| order_index | Required non-negative integer |

### 9.3 Sub-programme

| Field | Requirement |
|---|---|
| internal_id | Immutable identifier |
| plan_version | Required |
| programme | Required parent in the same version |
| sub_programme_code | System-assigned immutable reference (`{PE}-SUB-####`) on first save |
| title | Required |
| description | Optional |
| responsible_function | Required |
| order_index | Required non-negative integer |

### 9.4 Strategic Outcome

| Field | Requirement |
|---|---|
| internal_id | Immutable identifier |
| plan_version | Required |
| programme | Required |
| sub_programme | Optional; if supplied, must belong to programme and plan version |
| outcome_code | System-assigned immutable reference (`{PE}-OUT-####`) on first save; retained across successor plan versions |
| title | Required result statement |
| description | Optional |
| responsible_function | Required |
| executive_owner | Optional user/office reference |
| order_index | Required non-negative integer |

### 9.5 Performance Indicator

| Field | Requirement |
|---|---|
| internal_id | Immutable identifier |
| strategic_outcome | Required |
| indicator_code | System-assigned immutable reference (`{PE}-IND-####`) on first save |
| title | Required measure name |
| definition | Required calculation or assessment definition |
| measurement_type | Required controlled value |
| unit | Required except where Milestone or Boolean makes it unnecessary |
| measurement_frequency | Monthly, Quarterly, Annual, Due date or Plan end |
| data_source | Required |
| responsible_function | Required |
| order_index | Required non-negative integer |

### 9.6 Performance Target

| Field | Requirement |
|---|---|
| internal_id | Immutable identifier |
| performance_indicator | Required |
| target_code | System-assigned immutable reference (`{PE}-TGT-####`) on first save; retained across successor plan versions |
| title | Required concise target statement |
| comparison_direction | Required and type-compatible |
| target_numeric / target_text / target_date | Exactly the applicable value required |
| baseline_status | Known, To be established or Not applicable |
| baseline_numeric / baseline_text | Required where baseline is Known |
| baseline_as_of | Required where baseline is Known |
| baseline_source | Required where baseline is Known |
| tolerance_value | Optional, type-compatible |
| period_start / period_end | Required |
| benefit_owner | Required |
| measurement_verifier | Required and different from default submitter where assigned |
| status | Active within an Active plan; historical otherwise |

### 9.7 Public Value Objective

| Field | Requirement |
|---|---|
| internal_id | Immutable identifier |
| objective_code | System-assigned immutable reference (`{PE}-OBJ-####`) on first save for entity-authored objectives; catalogue codes (`PVO-*`) retained for controlled obligation catalogue entries |
| version_number | Required positive integer |
| title | Required desired result |
| pillar | Required controlled pillar |
| description | Required |
| source_type / source_reference | Required |
| scope | System or Procuring entity |
| procuring_entity | Required for entity-scoped objectives |
| applicability_mode | Required controlled value |
| measure_guidance | Required concise guidance |
| evidence_guidance | Required concise guidance |
| responsible_function | Required |
| default_enforcement_guidance | Required controlled route |
| effective_from / effective_to | Required validity |
| supersedes_objective_version | Required for successor versions |
| status | Workflow-controlled |

### 9.8 Objective Applicability Trigger

| Field | Requirement |
|---|---|
| public_value_objective | Required parent |
| trigger_type | Procurement Category, Procurement Type or Asset Condition |
| trigger_value | Required controlled reference/value |
| include | Boolean; MVP 1 uses inclusion rules only and shall default true |

### 9.9 Plan Value Commitment

| Field | Requirement |
|---|---|
| internal_id | Immutable identifier |
| plan_version | Required |
| public_value_objective_version | Required Active objective at time of selection |
| rationale | Required |
| consideration_level | Required, Recommended or Available |
| responsible_owner | Required |
| plan_measure_note | Optional plan-specific guidance |
| status | Locked with plan version |

### 9.10 Plan Value Commitment Link

| Field | Requirement |
|---|---|
| plan_value_commitment | Required parent |
| link_type | Strategic Outcome or Performance Target |
| linked_record | Required record from the same plan version |

### 9.11 Performance Measurement

| Field | Requirement |
|---|---|
| internal_id | Immutable identifier |
| performance_target | Required |
| measurement_period_start / end | Required |
| actual_numeric / actual_text / actual_date | Exactly the type-compatible value required |
| measurement_date | Required |
| evidence_reference | Required |
| evidence_source | Required |
| commentary | Optional |
| variance | System-calculated where quantitative |
| result_status | System-calculated |
| workflow_status | Workflow-controlled |
| submitted_by / submitted_at | System-controlled |
| verified_by / verified_at | System-controlled |
| verification_comment | Required for Return or Reject; optional for Verify |
| supersedes_measurement | Optional; required for a formal corrected version |

### 9.12 Strategy Corrective Action

| Field | Requirement |
|---|---|
| internal_id | Immutable identifier |
| performance_measurement | Required |
| performance_target | Derived and locked |
| action | Required |
| owner | Required |
| due_date | Required |
| expected_result | Required |
| status | Workflow-controlled |
| completion_evidence | Required before verification |
| verified_by / verified_at | System-controlled |
| cancellation_reason / cancelled_by | Required only when cancelled |

## 10. Core constraints

1. Internal identifiers shall never be reused.
2. Business codes shall use uppercase letters, numbers and hyphens.
3. System-assigned references are immutable after first save. Only a Strategy Administrator may correct a reference before the plan is activated, with an audited reason. Users shall not create or maintain reference codes.
4. A child shall never reference a parent from a different plan version.
5. An Active or Approved plan version shall not be edited.
6. An Active Public Value Objective version shall not be edited.
7. Deleting referenced or approved records is prohibited.
8. One logical plan version may supersede only one immediate predecessor.
9. A superseded plan version shall not return to Active.
10. A measurement period shall fall within the target period unless an authorised final measurement is explicitly marked.
11. Measurement values, target values and indicator types shall be compatible.
12. Workflow and result status shall never be stored in the same field.
13. For quantitative `At least` targets: actual at or above target is On track; actual below target but at or above tolerance is At risk; actual below tolerance is Off track. `At most` targets apply the inverse comparison.
14. A quantitative target without an explicit tolerance shall treat a missed target as Off track.
15. Milestone and Boolean targets shall use due date and achieved/not-achieved state to derive the target-period status.

## 11. Governance and state transitions

### 11.1 Strategic Plan

| Current state | Action | Next state | Actor | Guards |
|---|---|---|---|---|
| Draft | Submit | Submitted | Strategy Manager | Readiness passes |
| Returned | Resubmit | Submitted | Strategy Manager | Return issues resolved; readiness passes |
| Submitted | Return for correction | Returned | Strategy Reviewer or Planning Authority | Reason required |
| Submitted | Approve | Approved | Planning Authority | Reviewer checks complete; approver is not submitter |
| Approved | Activate | Active | Planning Authority | Effective period valid; no Active version conflict for the same `plan_code`; no Active overlap for the same entity + plan type + scope; if Entity Strategic Plan, no overlapping Active Entity Strategic Plan for the entity; if subordinate type, `parent_plan` is set to an Entity Strategic Plan of the same entity |
| Active | Supersede | Superseded | Planning Authority | Approved successor is activated atomically |
| Active | Archive | Archived | Planning Authority | Only if no successor is required; reason required |
| Approved | Withdraw approval | Draft | Planning Authority | Not yet Active; reason required |

### 11.2 Public Value Objective

| Current state | Action | Next state | Actor | Guards |
|---|---|---|---|---|
| Draft | Submit | Submitted | Strategy Manager | Required fields and triggers valid |
| Submitted | Return | Returned | Strategy Reviewer | Reason required |
| Submitted | Approve | Approved | Planning Authority | Approver is not submitter |
| Approved | Activate | Active | Planning Authority | Effective dates valid; version conflict absent |
| Active | Supersede | Superseded | Planning Authority | Approved successor activated atomically |
| Active | Retire | Retired | Planning Authority | Reason required; historical use preserved |

### 11.3 Performance Measurement

| Current state | Action | Next state | Actor | Guards |
|---|---|---|---|---|
| Draft | Submit | Submitted | Performance Officer | Value and evidence complete |
| Returned | Resubmit | Submitted | Performance Officer | Return issues addressed |
| Submitted | Return | Returned | Performance Verifier | Reason required |
| Submitted | Verify | Verified | Performance Verifier | Verifier is not submitter |
| Submitted | Reject | Rejected | Performance Verifier | Reason required |

Result status is calculated independently after submission and confirmed at verification.

### 11.4 Corrective Action

| Current state | Action | Next state | Actor | Guards |
|---|---|---|---|---|
| Open | Start | In progress | Action Owner | None |
| In progress | Submit completion | Submitted for verification | Action Owner | Completion evidence required |
| Submitted for verification | Return | In progress | Performance Verifier | Reason required |
| Submitted for verification | Verify | Verified complete | Performance Verifier | Verifier is not action owner |
| Open / In progress | Cancel | Cancelled | Planning Authority | Reason required |

## 12. Roles and permissions

| Capability | Strategy Viewer | Strategy Officer | Strategy Manager | Strategy Reviewer | Planning Authority | Performance Officer | Performance Verifier | Auditor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| View Active strategy | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| View all strategy versions | No | Assigned entity | Assigned entity | Assigned entity | Assigned authority | Assigned entity | Assigned entity | Yes |
| Create/edit Draft plans | No | Yes | Yes | No | No | No | No | No |
| Submit plan | No | No | Yes | No | No | No | No | No |
| Review/return plan | No | No | No | Yes | Yes | No | No | No |
| Approve/activate/supersede plan | No | No | No | No | Yes | No | No | No |
| Create/edit Draft objectives | No | Yes | Yes | No | No | No | No | No |
| Approve/activate/retire objectives | No | No | No | No | Yes | No | No | No |
| Submit measurements | No | No | No | No | No | Yes | No | No |
| Verify measurements/actions | No | No | No | No | No | No | Yes | No |
| View audit history | No | Own actions | Assigned entity | Assigned entity | Assigned authority | Own submissions | Assigned entity | Yes |
| Export authorised data | No | No | Yes | Yes | Yes | No | Yes | Yes |
| View Strategy Performance | Yes | Assigned entity | Assigned entity | Assigned entity | Assigned authority | Assigned entity | Assigned entity | Yes |
| Export Strategy Performance report | Assigned entity | No | Assigned entity | Assigned entity | Assigned authority | No | No | Yes |

Users may hold multiple roles, but same-record segregation guards remain applicable.

Strategy Viewer is the read-only management and senior-stakeholder profile. It does not grant access to Draft plan definitions, restricted evidence or another entity's data.

## 13. Readiness rules

Plan submission shall be blocked when any of the following exists:

- No Programme
- Programme without an Outcome, directly or through a Sub-programme
- Outcome without an Indicator
- Indicator without a Target
- Invalid or duplicate code
- Cross-version parent reference
- Missing responsible function
- Incomplete indicator definition
- Incomplete target, baseline or period
- Missing benefit owner or verifier
- Plan Value Commitment without rationale, owner or linked outcome/target
- Referenced Public Value Objective not Active at time of selection
- Invalid effective period

The readiness screen shall group issues by Structure, Targets, Value Commitments and Governance and link each issue to its edit location.

## 14. Screen inventory

| Screen ID | Screen | Core purpose |
|---|---|---|
| STR-UI-01 | Strategy Portfolio | Find plans, see approval work, measurement attention and create a plan |
| STR-UI-02 | Plan Overview | View/edit plan identity, period, status, ownership and summary |
| STR-UI-03 | Plan Structure | Build and review Programme → optional Sub-programme → Outcome → Indicator → Target hierarchy |
| STR-UI-04 | Structure Item Editor | Create/edit the selected hierarchy item in a focused drawer |
| STR-UI-05 | Public Value Objective Catalogue | Find, filter, review and create reusable objectives |
| STR-UI-06 | Public Value Objective Editor | Define source, pillar, applicability, guidance, owner and version |
| STR-UI-07 | Plan Value Commitments | Select applicable objectives for the plan and link them to outcomes/targets |
| STR-UI-08 | Measurement Register | Show due, submitted, verified and attention measurements by plan/target/period |
| STR-UI-09 | Submit Measurement | Enter the actual result, source, evidence and commentary |
| STR-UI-10 | Verify Measurement | Compare target, baseline, actual and evidence and decide Verify, Return or Reject |
| STR-UI-11 | Corrective Actions | Track required actions and verification |
| STR-UI-12 | Downstream Usage | Show Budget, Demand, Planning, Tender, Contract, Asset and Disposal references |
| STR-UI-13 | Readiness and Review | Resolve grouped blockers and submit, return, approve or activate according to authority |
| STR-UI-14 | Audit History | Show version, workflow, edit and usage events |
| STR-UI-15 | Strategy Performance | Give managers and senior stakeholders a read-only view of verified performance, procurement contribution, public-value treatment and exceptions |

## 15. UX requirements

1. Use a portfolio plus focused plan workspace; do not expose raw DocType lists as the primary experience.
2. Keep the Plan workspace tabs limited to Overview, Structure, Value Commitments, Measurement, Downstream Usage, Review and Audit.
3. Use a tree for hierarchy and a single adjacent detail area or drawer; do not nest multiple accordions.
4. Always show Outcome, Indicator and Target as distinct labels.
5. Display human-readable code and title together.
6. Show status, effective period and version without large decorative cards.
7. Use compact tables for catalogues, measurements, actions and usage.
8. Use Start, Continue, Review, Resolve and View actions consistently.
9. Display readiness blockers at their point of correction and in the consolidated Review screen.
10. Do not show weights or scores in MVP 1.
11. Do not show every Public Value Objective while editing a plan; filters and applicability should reduce the selection list.
12. Empty states shall explain the next valid action and provide one primary action.
13. Returned records shall show the return reason next to the work requiring correction.
14. Verified values shall be read-only; correction creates a superseding measurement.
15. Off-track performance shall use `Needs attention`, not `Failed`.
16. The UI shall not imply that Strategy automatically imposes tender evaluation criteria.
17. Keyboard navigation, visible focus, accessible labels and non-colour status cues are required.
18. Navigation and top toolbars are outside the Stitch design scope unless explicitly requested.
19. Strategy Performance shall be a separate management entry view and shall not become an eighth Plan workspace tab.
20. Strategy Performance shall lead with outcome and exception information, followed by procurement contribution, public-value treatment and drill-down evidence.
21. Management summaries shall use compact count strips, concise trend indicators and tables; they shall not use a decorative card wall or an opaque composite score.
22. Procurement lifecycle values shall remain visibly separated by Budget, Demand, Plan, Tender and Contract stage to prevent double counting.
23. `Considered`, `Treated` or `Excluded with approval` shall not be presented as proof that a public-value outcome was achieved.
24. Every derived management value shall expose its reporting period, `As at` time and drill-down path.

## 16. API and downstream contracts

### 16.1 Strategy Reference DTO

```json
{
  "plan_version_id": "SPV-...",
  "plan_code": "MOH-SP-0001",
  "plan_version": 1,
  "node_type": "PerformanceTarget",
  "node_id": "PT-...",
  "node_code": "MOH-TGT-0001",
  "node_name": "At least 99.9% availability by 30 June 2028",
  "path": [
    {"type": "Programme", "id": "...", "code": "MOH-PROG-0001", "name": "Digital Health Services"},
    {"type": "SubProgramme", "id": "...", "code": "MOH-SUB-0001", "name": "Health Information Systems"},
    {"type": "StrategicOutcome", "id": "...", "code": "MOH-OUT-0001", "name": "Reliable and accessible digital clinical services"},
    {"type": "PerformanceIndicator", "id": "...", "code": "MOH-IND-0001", "name": "Availability of core clinical information systems"},
    {"type": "PerformanceTarget", "id": "...", "code": "MOH-TGT-0001", "name": "At least 99.9% availability by 30 June 2028"}
  ],
  "snapshot_label": "Digital Health Services / Health Information Systems / 99.9% availability by 30 June 2028"
}
```

### 16.2 Required service contracts

| Contract | Requirement |
|---|---|
| list_strategy_plans | Return entity-scoped plans filtered by status, type and effective date |
| get_strategy_tree | Return the typed, ordered hierarchy and counts for one plan version |
| validate_strategy_reference | Validate plan version, node, path and new-selection eligibility |
| list_active_targets | Return selectable Active targets with resolved paths |
| list_applicable_value_commitments | Return Active commitments filtered by plan, category, procurement type and asset condition |
| get_strategy_usage | Return read-only downstream references grouped by module and record type |
| list_measurements | Return period, workflow status, result status and corrective-action summary |
| get_strategy_portfolio | Return derived portfolio counts and assigned work |
| get_strategy_performance | Return entity- and plan-scoped outcome/target distributions, measurement exceptions, corrective actions, procurement contribution, public-value treatment and source freshness for a reporting period |
| export_strategy_performance_report | Export the authorised filtered management view with filters, generation metadata, source coverage and traceable references |

All write services shall enforce document state and permission server-side. UI hiding is not a permission control.

## 17. Notifications and work queues

The system shall notify or queue work for:

- Plan submitted for review
- Plan returned with reasons
- Plan approved and awaiting activation
- Plan activated or superseded
- Public Value Objective submitted, returned, activated, retired or superseded
- Measurement due, overdue, submitted, returned, verified or rejected
- Corrective action assigned, due, overdue, returned or verified

Notifications shall link directly to the affected screen and shall not expose another entity's data.

## 18. Audit, records and security

1. Record creation, edit, submission, review, approval, activation, supersession, retirement, measurement verification and corrective-action decisions.
2. Record actor, timestamp, prior state, new state and reason where required.
3. Preserve immutable snapshots of Approved and Active plan versions.
4. Preserve objective and reference versions used downstream.
5. Restrict evidence to authorised entity, strategy, performance and audit roles.
6. Prevent direct database/API writes from bypassing state and permission guards.
7. Include usage references in the audit view without copying downstream confidential data.
8. Apply the platform's records-retention and legal-hold controls.

## 19. Ministry of Health seed fixture

### 19.1 Strategic hierarchy

| Entity | Code | Name/value |
|---|---|---|
| Plan | MOH-SP-0001 | Ministry of Health Strategic Plan 2026–2030, version 1, Active |
| Programme | MOH-PROG-0001 | Digital Health Services |
| Sub-programme | MOH-SUB-0001 | Health Information Systems |
| Outcome | MOH-OUT-0001 | Reliable and accessible digital clinical services |
| Indicator | MOH-IND-0001 | Availability of core clinical information systems |
| Target | MOH-TGT-0001 | At least 99.9% annual availability by 30 June 2028 |

Target baseline: 97.8% as at 30 June 2026. Measurement frequency: monthly. Evidence source: approved infrastructure-monitoring report.

### 19.2 Public Value Objectives

| Code | Pillar | Objective |
|---|---|---|
| PVO-EFT-01 | Strategic and service outcomes | Improve availability of critical health services |
| PVO-ECO-01 | Economy and whole-life value | Reduce whole-life infrastructure cost |
| PVO-EFY-01 | Process efficiency | Reduce implementation and service-restoration time |
| PVO-RES-01 | Contract performance and resilience | Improve continuity of critical services |
| PVO-LOC-01 | Inclusion and economic development | Develop internal and local technical capability |
| PVO-SUS-01 | Sustainability and asset stewardship | Reduce infrastructure energy consumption |
| PVO-SUS-02 | Sustainability and asset stewardship | Ensure compliant handling of replaced ICT equipment |
| PVO-INT-01 | Integrity and accountability | Minimise uncontrolled contract changes |

### 19.3 Measurements

- September 2027: actual 99.82%, Submitted then Verified, result `At risk`, corrective action opened by the verifier.
- October 2027: actual 99.96%, Submitted then Verified, result `On track`.
- Corrective action: resolve storage-controller instability, completed and verified.

The fixture is illustrative and must not be presented as a legal or policy threshold.

## 20. MVP teardown and rebuild

The user has authorised removal of the current MVP Strategy data structures. There is no production-data migration requirement.

Implementation shall:

1. Remove the conflated `Strategy Objective = Output Indicator` model.
2. Replace it with explicit Strategic Outcome, Performance Indicator and Performance Target records.
3. Remove target-level embedded actual-result fields.
4. Replace them with Performance Measurement records.
5. Remove legacy Objective/Indicator UI aliases.
6. Remove obsolete builder routes, compatibility APIs and redirects unless another implemented module still requires a route during the same atomic change.
7. Replace downstream five-field cascades with versioned Strategy Reference contracts where affected MVP modules are updated in the same implementation.
8. Reset and reseed Strategy, Budget, Demand and Planning demo references as required.
9. Update all affected tests and selectors.
10. Avoid compatibility layers whose only purpose is preserving disposable MVP data.
11. Preserve unrelated user changes and modules.

The implementation plan must identify every destructive target before execution. It must not delete unrelated master data or documents.

## 21. Acceptance criteria

| ID | Acceptance criterion |
|---|---|
| STR-AC-001 | An authorised officer can create a complete plan with the clean hierarchy and optional Sub-programme behaviour. |
| STR-AC-002 | The UI never labels a Performance Indicator as a Strategic Objective. |
| STR-AC-003 | Cross-plan and cross-version parent relationships are rejected server-side. |
| STR-AC-004 | Readiness identifies and links every incomplete hierarchy, target, commitment and governance blocker. |
| STR-AC-005 | A submitter cannot approve the same plan or objective. |
| STR-AC-006 | An Approved or Active plan/objective cannot be edited. |
| STR-AC-007 | Activating a successor atomically supersedes the previous Active version. |
| STR-AC-008 | A historical downstream reference remains resolvable after supersession. |
| STR-AC-009 | Only effective Active targets are available for new downstream selection. |
| STR-AC-010 | Applicable Public Value Commitments are filtered by structured triggers. |
| STR-AC-011 | Required consideration is returned as a requirement to include or record an approved exclusion, not as an automatic tender criterion. |
| STR-AC-012 | Performance actuals are separate measurement records and preserve period history. |
| STR-AC-013 | Duplicate period measurement is blocked unless a formal superseding record is created. |
| STR-AC-014 | A measurement submitter cannot verify the same measurement. |
| STR-AC-015 | Variance and result status are calculated correctly for every supported measurement type. |
| STR-AC-016 | A verified Off track measurement requires corrective action or authorised exception. |
| STR-AC-017 | Downstream Usage is derived and read-only. |
| STR-AC-018 | Entity permissions prevent unauthorised cross-entity access through both UI and API. |
| STR-AC-019 | Audit history records state, actor, time and required reason for every governed action. |
| STR-AC-020 | MOH seeds load repeatably and produce the specified Active plan, objectives, measurements and corrective action. |
| STR-AC-021 | Budget, Demand and Planning integrations use the new reference contract and pass regression tests. |
| STR-AC-022 | No obsolete Objective/Indicator alias, embedded actual field or legacy selector remains in an active MVP path. |
| STR-AC-023 | Core screens satisfy the approved Stitch designs without adding unapproved functionality. |
| STR-AC-024 | Strategy Viewer opens the read-only Strategy Performance view and cannot access plan-maintenance actions or restricted Draft definitions. |
| STR-AC-025 | Outcome and target summaries are derived from applicable Verified measurements and expose the underlying result distribution. |
| STR-AC-026 | Missing workflow data, verified underperformance and overdue corrective actions appear as distinct management exceptions with working drill-down links. |
| STR-AC-027 | Procurement contribution is derived only from valid alignment references and lifecycle-stage values are not summed or double counted. |
| STR-AC-028 | Public-value reporting distinguishes downstream consideration/treatment from verified achievement. |
| STR-AC-029 | Every management view and export shows its filters, reporting period, generation or `As at` time and source coverage. |
| STR-AC-030 | Entity permissions prevent unauthorised Strategy Performance access and report export through both UI and API. |

## 22. Required test matrix

### 22.1 Backend and domain

- Creation and uniqueness constraints
- Parent/path integrity
- Measurement type/value compatibility
- Baseline and period validation
- Applicability triggers
- Duplicate measurement prevention
- Supersession and immutability
- Delete protection

### 22.2 Workflow and permissions

- Every valid transition
- Every invalid transition
- Submitter/approver segregation
- Submitter/verifier segregation
- Entity scoping
- Active-only downstream selection
- Historical reference resolution
- API permission bypass attempts

### 22.3 Service contracts

- Plan and target selectors
- Tree ordering and typed paths
- Reference validation
- Applicable-value-commitment filtering
- Usage grouping
- Portfolio counts
- Measurement calculations
- Strategy Performance roll-ups and exception derivation
- Procurement contribution by lifecycle stage without double counting
- Public-value consideration versus achievement derivation
- Management report filter, lineage and source-coverage metadata

### 22.4 Browser tests

- Portfolio search and filters
- Plan creation
- Structure creation and editing
- Readiness correction links
- Submit, return, approve and activate
- Objective creation and activation
- Plan Value Commitment selection
- Measurement submission and verification
- Corrective-action completion
- Downstream Usage
- Empty, returned and attention states
- Keyboard and focus behaviour for core workflows
- Strategy Performance filters, drill-downs, empty/stale-source states and report export
- Strategy Viewer read-only default route and absence of maintenance actions

### 22.5 Regression

- Budget strategy selection
- Demand primary/supporting alignment
- Planning inherited alignment
- Stable seed execution
- Procurement Home references where present

## 23. Non-functional requirements

1. Primary portfolio and plan screens should load within the platform's established performance budget for normal entity-scale fixtures.
2. Tree retrieval shall avoid per-node query loops.
3. All list APIs shall support pagination or bounded results where volume can grow.
4. Server-side permission and validation are mandatory.
5. User-visible dates, currency and numbers shall use configured locale while APIs use stable canonical formats.
6. Status shall never be conveyed by colour alone.
7. Audit records and approved snapshots shall be durable and exportable by authorised users.
8. Errors shall identify the corrective action without exposing stack traces or sensitive identifiers.
9. Strategy Performance queries shall aggregate in bounded server-side operations and shall not issue per-target or per-downstream-record query loops.
10. Management reports shall reproduce the authorised filtered values and lineage shown at generation time.
11. Source freshness and unavailable-module conditions shall degrade explicitly rather than silently presenting incomplete totals as complete.

## 24. Deferred backlog

- External national/county plan import and reconciliation
- Complex plan branching and merge tools
- Advanced weighted portfolio scoring
- Forecasting and scenario modelling
- Automated evidence ingestion from monitoring platforms
- Public strategy-performance portal
- Cross-government consolidated strategy analytics
- Complex applicability expression builder
- AI assistance

## 25. Lock decisions

The following are intentional MVP 1 decisions:

1. Existing MVP strategy structures may be destroyed and reseeded.
2. The hierarchy is fixed and typed; Sub-programme is optional.
3. Public Value Objectives are a separate catalogue, not hierarchy nodes.
4. Plan Value Commitments adopt catalogue objectives without copying them.
5. Demand Intake owns the procurement-specific Value Case.
6. Strategy provides enforcement guidance but does not impose tender treatment.
7. Target actuals are separate, verified time-series measurements.
8. Simple structured applicability triggers replace an arbitrary rules engine.
9. One logical plan may have only one Active version.
10. Multiple different plans may be Active for the same entity.
11. One primary target alignment and optional supporting target alignments are supported downstream.
12. No scores or weighted strategy ratings are included.
13. Strategy Performance is a separate read-only management view, not an additional Plan workspace tab and not a replacement for generic platform Analytics.
14. Procurement contribution is evidence of alignment and activity; it is not automatic proof that procurement caused the strategic result.
15. Public-value consideration and verified public-value achievement remain separate reporting concepts.

## 26. Requirements-lock checklist

This document may be marked `Locked` only after confirming:

- Scope and exclusions
- Clean hierarchy
- Public Value Objective model
- Plan Value Commitment model
- Measurement and corrective-action model
- Governance and segregation of duties
- Screen inventory
- Downstream reference contract
- Teardown authority and affected modules
- MOH fixture
- Acceptance criteria and test matrix
- Management monitoring, reporting, permissions and attribution safeguards

Once locked, any functional change requires a new document version. Stitch prompts and the Cursor implementation prompt shall reference the locked version and screen IDs.
