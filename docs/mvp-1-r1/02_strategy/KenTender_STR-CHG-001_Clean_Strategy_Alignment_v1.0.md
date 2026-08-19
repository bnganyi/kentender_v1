**REVISION LEDGER CHANGE UNIT**

Clean Strategy Alignment

Greenfield semantic correction, module decoupling and implementation baseline

| **Control**            | **Value**                                        |
| ---------------------- | ------------------------------------------------ |
| Document ID            | STR-CHG-001                                      |
| Version                | 1.0                                              |
| Date                   | 19 August 2026                                   |
| Status                 | Proposed for product-owner approval              |
| Module                 | Strategy Alignment                               |
| Implementation posture | Clean build; no migration or compatibility layer |

**Controlling decision:** Preserve Strategy Alignment as a distinct upstream governance module, correct its semantics and remove all legacy Demands coupling. Do not redesign the surrounding procurement lifecycle and do not retain incorrect models merely to preserve provisional code or seed data.

# Document map

- Decision, scope and completion standard
- Legal and governance grounding
- Corrected module boundary and canonical concepts
- Governance, permissions and lifecycle
- Screen and interaction corrections
- Integration contracts and seed data
- Implementation plan, acceptance criteria and smoke contract

# 1\. Decision and purpose

STR-CHG-001 is the single implementation authority for cleaning Strategy Alignment. It consolidates requirements, corrected screen intent, data definitions, seed data, implementation controls and acceptance evidence in one Revision Ledger unit.

The module is substantively retained. The work is a controlled semantic and dependency correction, not a complete functional rewrite. The corrected module must install, seed, open and operate without the deleted legacy Demands package and without Procurement Home.

**Release classification:** MVP-blocking stabilization. Strategy Alignment is an upstream dependency for Budget & Funding and Procurement Planning; broken imports, ambiguous value objects or non-deterministic scope resolution would contaminate all downstream records.

## 1.1 Outcomes

- A self-contained Strategy Alignment module with no runtime or seed dependency on legacy Demands.
- Correct domain language: Strategy Value Commitment, Strategic Outcome, Performance Indicator and Performance Target.
- One governed, versioned strategy hierarchy that downstream modules can reference but cannot mutate.
- Explicit Procuring Entity, organisation-unit and effective-period scope with no first-record or Administrator fallback.
- Deterministic, configuration-first seed data for the Ministry of Health and County Government of Kisumu demonstration contexts.
- Neutral read surfaces separated from live workflow task surfaces.

## 1.2 In scope

- Domain-object correction and clean internal naming.
- Removal of obsolete treatment, Public Value Objective and legacy dependency structures.
- Strategy-plan versioning, hierarchy, outcomes, indicators, targets and value commitments.
- Approval, activation, supersession and read-only access controls.
- Static screen corrections and implementation behaviour contracts.
- Logical APIs, seed fixtures, audit requirements and automated acceptance tests.

## 1.3 Explicit exclusions

- No migration, mapping table, alias, redirect, dual read, shadow write, feature flag or compatibility query for legacy Strategy or Demands records.
- No advanced strategy-performance dashboard, corrective-action workflow or generic Public Value Objective rules engine in MVP 1.
- No Budget Line Value Treatment, Demand Value Treatment, planned-treatment field or generic statutory-treatment questionnaire.
- No requester-facing Strategy selection in Departmental Needs.
- No change to the approved Procurement Planning, Tender or Contract lifecycle beyond the stable read contracts defined here.
- No custom Procurement Home dependency or replacement dashboard in this change unit.

## 1.4 Completion standard

The change is complete only when a fresh environment can install, migrate, seed and open Strategy Alignment; all renamed concepts are consistent across schema, services, UI, links, seeds and tests; and downstream consumers receive governed, read-only strategy references through explicit contracts.

# 2\. Problem statement and correction rationale

The previous implementation mixed sound strategic-planning foundations with provisional concepts and cross-module assumptions. The clean-up must preserve versioned strategy data while removing semantic ambiguity and import-time coupling.

| **Observed or inherited problem** | **Required correction**                                                                                                                                  | **Why it matters**                                                      |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Legacy module imports             | Remove every Strategy runtime, hook, test and seed import of the deleted demands package.                                                                | Strategy must remain available while Departmental Needs is rebuilt.     |
| Plan Value Commitment label       | Rename the model and all user-facing references to Strategy Value Commitment.                                                                            | The commitment originates in Strategy, not in a Procurement Plan.       |
| Objective used as indicator       | Model Strategic Objective and Performance Indicator as separate concepts; introduce Strategic Outcome between them where the plan structure requires it. | Objectives describe intended direction; indicators measure achievement. |
| Manual technical codes            | Generate stable references and display titles plus hierarchy paths.                                                                                      | Prevents duplicate, malformed and user-maintained identifiers.          |
| Silent PE/OU selection            | Require zero/one/multiple scope resolution with no first-record fallback.                                                                                | Prevents cross-entity leakage and incorrect plan activation.            |
| Administrator role inflation      | Provide neutral read access, but no operational authorship or approval unless separately assigned.                                                       | Separates technical administration from accountable decisions.          |
| Generic treatment engines         | Remove treatment fields, records, services, screens, seeds and tests.                                                                                    | They have no validated actor, decision or downstream consequence.       |
| Overlapping active plans          | Enforce the active-plan uniqueness rule at write time.                                                                                                   | Downstream modules must resolve one authoritative primary plan.         |

# 3\. Legal and governance grounding

Strategy Alignment is a governance-enabling module. The procurement legislation does not prescribe KenTender's internal object names or require a standalone strategy application. It does require procurement planning to be realistic, budget-integrated, properly authorised and traceable. The system therefore retains approved strategic lineage as governed context without inventing additional procurement approvals.

| **Authority**                                                                                        | **Relevant requirement**                                                                                                                   | **System consequence**                                                                                                              |
| ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| Constitution of Kenya, Article 227                                                                   | Public procurement must be fair, equitable, transparent, competitive and cost-effective.                                                   | Strategy references must not create hidden eligibility rules or bypass procurement controls.                                        |
| PPADA 2015, sections 44 and 45                                                                       | The accounting officer is responsible for compliance, approved-budget alignment, systematic decisions and segregation of responsibilities. | Strategy authorship, approval and downstream procurement actions remain separately authorised and auditable.                        |
| PPADA 2015, section 53                                                                               | Annual procurement plans must be realistic, budget-linked and integrated with applicable budget processes.                                 | Approved Strategy context supports traceability but does not replace Budget confirmation or Plan approval.                          |
| PPAD Regulations 2020, regulations 40–42                                                             | Departmental and consolidated annual procurement plans follow the annual budget process and prescribed format.                             | Planning consumes approved Strategy references; Strategy does not become a parallel procurement-plan editor.                        |
| Public Service Commission (Performance Management) Regulations 2021, regulation 14, where applicable | Objectives should relate to mandate, national development, outputs, budgets, beneficiaries, achievements and timeframes.                   | Separate objectives, outcomes, indicators and targets; retain measurable lineage.                                                   |
| Public Finance Management Act 2012, section 126, for county development plans                        | County development plans connect priorities, programmes, services, indicators and allocated budgets.                                       | County seed data and hierarchy must support programme, indicator and budget linkage without assuming a national-ministry structure. |

**Interpretation boundary:** The legal provisions justify traceable strategy-to-plan alignment and accountable approvals. They do not justify generic treatment questionnaires, duplicate HoD approval, requester-authored Strategy mappings or a universal performance-management engine.

# 4\. Corrected module boundary

## 4.1 Strategy Alignment owns

- Strategic plans and their versions, types, ownership scope and effective periods.
- Typed hierarchy nodes, including pillars, programmes, sub-programmes, strategic objectives, strategic outcomes and initiatives or activities where applicable.
- Performance indicators and time-bound performance targets.
- Strategy Value Commitments approved for downstream use.
- Approval, activation, supersession, archive and immutable audit history.
- Resolution of the applicable active strategy context for a PE, OU and date or financial year.

## 4.2 Strategy Alignment does not own

| **Excluded ownership**                                               | **Owning module**            | **Permitted Strategy relationship**                                                                                                              |
| -------------------------------------------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Plain-language departmental need and HoD approval                    | Departmental Needs           | None required from the requester; no Strategy selection on Needs intake.                                                                         |
| Budget structures, availability and Finance confirmation             | Budget & Funding             | Budget Lines may reference approved Strategy nodes or targets.                                                                                   |
| Procurement method, aggregation, schedule, lotting and Plan approval | Procurement Planning         | Plan Items select or inherit approved Strategy Value Commitments and retain an immutable lineage snapshot when the Plan Version is approved.     |
| Tender configuration and solicitation controls                       | Tender Management            | Tender receives the approved Plan Item's strategy snapshot; it does not edit Strategy.                                                           |
| Delivery, acceptance and actual performance                          | Contract Management          | Contract records verified results against inherited indicators or commitments and returns measurement evidence through a controlled integration. |
| Technical users, PE/FY configuration and assignments                 | Configuration and Governance | Strategy consumes explicit configuration; it does not create fallback entities, years or assignments.                                            |

## 4.3 Dependency direction

**Allowed direction:** Configuration → Strategy Alignment → Budget & Funding / Procurement Planning → Tender → Contract. Departmental Needs remains independently operable and does not import Strategy. Strategy never imports a downstream transactional module.

# 5\. Canonical terminology and rename register

| **Previous or ambiguous term**                  | **Canonical term**                                                  | **Disposition**                                                                                    |
| ----------------------------------------------- | ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Plan Value Commitment                           | Strategy Value Commitment                                           | Clean rename in DocType/model, fields, services, labels, links, seeds and tests. No alias.         |
| Strategy Objective used to store a measure      | Performance Indicator                                               | Replace the misclassified object. Retain Strategic Objective only for a genuine objective.         |
| Target/Outcome combined value                   | Strategic Outcome + Performance Target                              | Separate intended result from measurable threshold and period.                                     |
| User-entered strategy code                      | System-generated reference                                          | Reference is immutable; ordinary forms show title and hierarchy path.                              |
| Public Value Objective / PVO treatment          | No MVP replacement                                                  | Remove generic engine and ordinary navigation. Re-admit only through a later approved change unit. |
| Strategy treatment / planned treatment          | No canonical term                                                   | Remove record, field, service, UI, seed and test.                                                  |
| Strategy Administrator as operational authority | Explicit Strategy Author / Reviewer / Approval Authority assignment | Administrator has neutral read access only unless explicitly assigned.                             |

# 6\. Canonical domain model

All identifiers are generated. Every owned record carries one procuring_entity and, where applicable, an owner_org_unit. Approved and active records are never silently edited; corrections create a new version.

| **Object**                | **Purpose**                                                                              | **Required controls**                                                                                                  |
| ------------------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Strategic Plan            | Stable identity for a national, ministerial/county, corporate or departmental framework. | PE, optional OU, plan type, title, period, primary/supporting flag, generated reference.                               |
| Strategic Plan Version    | Immutable approval boundary for the plan content.                                        | Version number, status, effective dates, submitted/approved/activated actors and timestamps.                           |
| Strategy Node             | Typed hierarchical node within one version.                                              | Node type, title, parent, order, optional description; no manually maintained code.                                    |
| Performance Indicator     | Defines how achievement of an objective or outcome is measured.                          | Name, definition, unit, direction, data source, frequency, responsible owner.                                          |
| Performance Target        | Time-bound expected indicator value.                                                     | Indicator, period/FY, baseline where relevant, target value, unit inherited from indicator.                            |
| Strategy Value Commitment | Approved statement of strategic value available to downstream procurement records.       | Plan version, linked objective/outcome/indicator/target, title, commitment statement, scope, effective period, status. |
| Strategy Plan Scope       | Defines explicit PE and optional OU applicability for the plan.                          | No wildcard or first-PE inference; overlap validation is server-side.                                                  |
| Strategy Audit Event      | Append-only evidence of lifecycle and controlled changes.                                | Actor, capability, timestamp, before/after state, reason and correlation reference.                                    |

## 6.1 Strategy hierarchy

The hierarchy is typed rather than hard-coded to a single institutional structure. The canonical lineage supports, where applicable: National Development Plan → Ministerial or County Strategic Plan → Corporate Plan → Department Work Plan → Pillar → Programme → Sub-programme → Strategic Objective → Strategic Outcome → Performance Indicator → Performance Target.

A downstream procurement line must reference the complete applicable lineage required by its PE configuration. Inapplicable layers are omitted explicitly; they are not populated with blank placeholders.

## 6.2 Core invariants

- A Strategy Node belongs to exactly one Strategic Plan Version.
- A Performance Indicator measures one Strategic Objective or Strategic Outcome; it is not itself an objective.
- A Performance Target belongs to one Performance Indicator and one time period or financial year.
- A Strategy Value Commitment belongs to one approved or active Strategic Plan Version and references at least one outcome or target.
- At most one primary Strategic Plan may be Active for the same PE and overlapping effective period; supporting frameworks may coexist only when their type and relationship are explicit.
- A Strategic Plan Version cannot become Active until hierarchy validation, indicator/target validation and approval are complete.
- Downstream records store references and approved snapshots; they never update Strategy master data.
- Deletion is prohibited after approval or downstream reference. Supersession is used instead.

# 7\. Lifecycle and governance

| **Current state** | **Action**         | **Next state** | **Authority and guard**                                                                              |
| ----------------- | ------------------ | -------------- | ---------------------------------------------------------------------------------------------------- |
| Draft             | Submit for review  | In Review      | Strategy Author; completeness and overlap pre-validation required.                                   |
| In Review         | Return             | Returned       | Strategy Reviewer or Approval Authority; reason required.                                            |
| Returned          | Resume editing     | Draft          | Assigned Strategy Author; prior review evidence retained.                                            |
| In Review         | Approve            | Approved       | Strategy Approval Authority; cannot be the same actor as author where segregation is configured.     |
| Approved          | Activate           | Active         | Strategy Approval Authority; effective-period and active-plan uniqueness checks required.            |
| Active            | Activate successor | Superseded     | System transition when a valid successor becomes Active; existing downstream snapshots remain valid. |
| Superseded        | Archive            | Archived       | Strategy records authority; no deletion and no new downstream selection.                             |

## 7.1 Approval and audit rules

- Every submit, return, approve, activate, supersede and archive action is server-authorised and audited.
- A user may see a neutral record without being able to open its workflow task form.
- Unauthorised task routes and APIs return a controlled denial; they do not render a disabled form.
- The System Administrator may inspect records and technical metadata read-only, but gains no author, review, approval or activation capability by virtue of being Administrator.
- Capability assignments are scoped by PE, optional OU, plan type and effective dates.
- The UI may not be the sole enforcement point for status or permission rules.

# 8\. Roles and permissions

| **Actor**                   | **Neutral view**          | **Draft authoring**            | **Review/return**              | **Approve/activate**           | **Config**     |
| --------------------------- | ------------------------- | ------------------------------ | ------------------------------ | ------------------------------ | -------------- |
| Strategy Viewer             | Scoped                    | No                             | No                             | No                             | No             |
| Strategy Author             | Scoped                    | Scoped                         | No                             | No                             | No             |
| Strategy Reviewer           | Scoped                    | No                             | Scoped live tasks              | No                             | No             |
| Strategy Approval Authority | Scoped                    | No                             | Scoped live tasks              | Scoped                         | No             |
| Procurement Planner         | Applicable active context | No                             | No                             | No                             | No             |
| Budget/Finance Officer      | Applicable active context | No                             | No                             | No                             | No             |
| Head of Procurement         | Applicable active context | No                             | No                             | No                             | No             |
| System Administrator        | All records read-only     | No, unless separately assigned | No, unless separately assigned | No, unless separately assigned | Technical only |

**Scope rule:** List results, counters, direct routes, APIs, exports, notifications and task queues must use the same server-side PE/OU capability filter. Workspace selectors filter visibility; they never grant authority.

# 9\. Functional requirements

| **ID**     | **Requirement**                                                                                      |
| ---------- | ---------------------------------------------------------------------------------------------------- |
| STR-FR-001 | Create a Strategic Plan only within one explicit authorised PE and optional OU scope.                |
| STR-FR-002 | Generate the plan reference; do not expose it as an editable field.                                  |
| STR-FR-003 | Maintain plan type, title, ownership scope, effective period and primary/supporting classification.  |
| STR-FR-004 | Create versioned plan content; approved and active versions are immutable.                           |
| STR-FR-005 | Maintain typed Strategy Nodes with validated parent-child relationships.                             |
| STR-FR-006 | Maintain Strategic Objectives separately from Strategic Outcomes.                                    |
| STR-FR-007 | Maintain Performance Indicators with definition, unit, direction, source, frequency and owner.       |
| STR-FR-008 | Maintain Performance Targets by indicator and period/FY.                                             |
| STR-FR-009 | Maintain Strategy Value Commitments against approved hierarchy and measurable targets.               |
| STR-FR-010 | Resolve one applicable primary active strategy context for a PE and date/FY.                         |
| STR-FR-011 | Reject overlapping primary Active plans for the same PE and effective period.                        |
| STR-FR-012 | Allow supporting frameworks only with explicit type, scope and relationship.                         |
| STR-FR-013 | Validate completeness before submission and again before activation.                                 |
| STR-FR-014 | Record return reasons and preserve all review history.                                               |
| STR-FR-015 | Expose neutral read surfaces independently of workflow-task authority.                               |
| STR-FR-016 | Provide downstream read contracts without direct database coupling.                                  |
| STR-FR-017 | Prevent downstream modules from mutating Strategy records.                                           |
| STR-FR-018 | Create an immutable strategy lineage snapshot when a downstream approval boundary requires it.       |
| STR-FR-019 | Remove legacy Plan Value Commitment and treatment concepts from executable code and active metadata. |
| STR-FR-020 | Operate without Departmental Needs, Procurement Home or any legacy demands package being importable. |
| STR-FR-021 | Seed deterministically from configuration-owned PE/FY records without silent creation or fallback.   |
| STR-FR-022 | Audit all lifecycle, permission-sensitive read and downstream-resolution actions.                    |

# 10\. Screen and interaction corrections

The existing Strategy Alignment navigation position is retained. This change corrects the screens necessary to operate the canonical domain; it does not introduce an advanced performance-management suite.

| **Screen**                           | **Static design contract**                                                                                                                         | **Implementation behaviour**                                                                                                             |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| STR-UI-01 Strategy Workspace         | Show explicit PE context, applicable active plan, plan period, status and role-appropriate next work. Do not show advanced performance dashboards. | Zero scopes block with explanation; one resolves automatically; multiple require deliberate selection. Counts use the same server scope. |
| STR-UI-02 Strategic Plans            | Compact list with plan title, type, scope, period, current version and status.                                                                     | Create appears only for authorised authors. Neutral viewers open read-only detail.                                                       |
| STR-UI-03 Plan Version Detail        | Show metadata, hierarchy summary, validation state, approval evidence and version history.                                                         | Approved/Active versions are read-only. Editing creates or resumes a Draft version.                                                      |
| STR-UI-04 Hierarchy Editor           | Tree plus focused node editor; show meaningful titles and paths, not editable codes.                                                               | Parent-child rules, duplicate siblings and completeness are validated server-side.                                                       |
| STR-UI-05 Indicators and Targets     | Compact records grouped under objective/outcome with unit, period and target.                                                                      | Indicator and target semantics are validated; no combined Target/Outcome field.                                                          |
| STR-UI-06 Strategy Value Commitments | List commitment, linked outcome/indicator/target, effective period and status.                                                                     | Only Strategy roles author commitments. Downstream users select/read approved commitments.                                               |
| STR-UI-07 Review and Approval        | Show submitted version, validation summary, changes and approval actions.                                                                          | Accessible only for a live assigned task. Return reason required; activation rechecks overlap.                                           |
| STR-UI-08 Neutral Strategy Record    | Read-only hierarchy, indicators, targets, commitments and approval evidence.                                                                       | Available to authorised viewers, including System Administrator, without exposing workflow actions.                                      |

**Design-tool boundary:** Stitch prompts may specify only the visible static composition and example states. Saving, permissions, validation, transitions, concurrent updates, API failures and loading behaviour belong to this implementation contract and its tests.

# 11\. Validation rules

| **Rule**                                             | **When enforced**                      | **Failure result**                                                       |
| ---------------------------------------------------- | -------------------------------------- | ------------------------------------------------------------------------ |
| Explicit authorised PE/OU scope                      | Create, list, read, submit and approve | Controlled denial or required scope selection; never first-row fallback. |
| Effective start precedes effective end               | Save and submit                        | Field-level validation; no state change.                                 |
| No overlapping primary Active plan                   | Approve/activate                       | Activation blocked with conflicting plan reference.                      |
| Hierarchy node parent is permitted                   | Save/import/seed                       | Row rejected; transaction rolled back.                                   |
| Indicator has definition, unit, direction and source | Submit                                 | Version remains Draft with actionable error.                             |
| Target uses indicator unit and valid period          | Save and submit                        | Target rejected or version blocked.                                      |
| Commitment references approved lineage               | Submit and activate                    | Commitment cannot become available downstream.                           |
| No mutation of Approved/Active version               | Every write                            | Write denied; author must create a Draft successor.                      |
| Optimistic concurrency/version guard                 | Save and transition                    | Stale update rejected; user reloads current version.                     |
| Downstream read-only contract                        | API and database permission            | Mutation denied and audited.                                             |

# 12\. Integration contracts

These are logical service contracts. Their package paths may follow the application structure, but their inputs, outputs and authority boundaries are mandatory. Downstream modules must not import Strategy DocType controllers or query Strategy tables directly.

| **Contract**              | **Input**                                                    | **Output and control**                                                                                                    |
| ------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------- |
| resolve_strategy_context  | PE, optional OU, effective date or FY                        | Exactly one primary active plan context or a typed zero/multiple-result error; supporting frameworks returned explicitly. |
| list_strategy_commitments | Resolved context plus optional node/target filters           | Approved, effective commitments only; server-side scope enforced.                                                         |
| get_strategy_lineage      | Strategy node, indicator, target or commitment reference     | Canonical titles, hierarchy path, version and effective period; no editable code.                                         |
| create_strategy_snapshot  | Approved downstream record boundary plus selected references | Immutable lineage payload and source version; idempotent by correlation key.                                              |
| record_verified_result    | Contract evidence reference and measured result              | Deferred until Contract scope activates it; no direct Strategy master-data mutation.                                      |

## 12.1 Minimum returned lineage

- Procuring Entity and optional organisation-unit scope.
- Strategic Plan reference, type, title, version and effective period.
- Applicable node path, including objective, programme and sub-programme where configured.
- Strategic Outcome, Performance Indicator and Performance Target references and labels.
- Strategy Value Commitment reference, title and approved statement.
- Resolution timestamp and source version for audit and snapshot creation.

# 13\. Seed data contract

Strategy seed data is deterministic and independently runnable. It consumes PE, OU and FY records established by Configuration and Governance; it must fail loudly when those prerequisites are absent and must never create a first-PE fallback.

| **Seed set**        | **Required records**                                                                                                   | **Downstream purpose**                                                     |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| CFG dependency      | Ministry of Health and County Government of Kisumu; FY 2027/28; explicit organisational units and assignments.         | Provides stable entity, year and role scope used by all modules.           |
| MoH primary plan    | STR-MOH-2023-001; Ministry of Health Strategic Plan (Demo); 2023/24–2027/28; Active primary.                           | Primary strategy context for the canonical MoH planning story.             |
| MoH hierarchy       | Digital health pillar; programme and sub-programme; objective; strategic outcome; indicator; FY 2027/28 target.        | Complete lineage for the digital-health Plan Item without requester entry. |
| MoH commitment      | SVC-MOH-2027-001; approved Strategy Value Commitment linked to the outcome, indicator and target.                      | Selectable/inheritable strategy value for Procurement Planning.            |
| Kisumu primary plan | STR-KSM-2023-001; Kisumu County development strategy (Demo); 2023–2027; Active primary.                                | Second-entity isolation and county-plan hierarchy.                         |
| Negative fixtures   | Overlapping Draft plan, unauthorised actor, stale version and missing prerequisite fixtures created only inside tests. | Proves guards without contaminating canonical demo data.                   |

## 13.1 Illustrative MoH lineage

| **Level**                 | **Illustrative seed value**                                                    |
| ------------------------- | ------------------------------------------------------------------------------ |
| Plan                      | Ministry of Health Strategic Plan (Demo)                                       |
| Pillar                    | Digital health systems                                                         |
| Programme                 | Health policy, standards and regulation                                        |
| Sub-programme             | Digital health governance                                                      |
| Strategic Objective       | Strengthen interoperable national digital health services                      |
| Strategic Outcome         | Improved availability and reliability of interoperable digital health services |
| Performance Indicator     | Percentage of priority facilities using interoperable digital health services  |
| FY 2027/28 Target         | 80 percent                                                                     |
| Strategy Value Commitment | Enable secure, interoperable access to priority digital health services        |

**Seed disclaimer:** All Strategy titles and target values marked Demo are synthetic fixtures for testing and demonstration. They must not be presented as an approved government strategy or official performance commitment.

# 14\. Implementation work plan

1. Inventory Strategy schema, controllers, hooks, APIs, reports, workspaces, links, tests and seeds; classify each artifact as Keep, Correct, Remove or Defer.
2. Delete every import and reference to the legacy demands package and every dependency on Procurement Home.
3. Implement the canonical greenfield models and generated-reference rules. Do not create migration or compatibility artifacts.
4. Apply terminology changes across schema, Python, JavaScript, route metadata, links, fixtures and tests.
5. Implement lifecycle transitions, immutable versions, active-plan overlap prevention, capability scope and audit events.
6. Implement neutral read surfaces and deny unauthorised workflow task routes before rendering.
7. Implement logical read services and prohibit downstream direct table/controller access.
8. Rebuild deterministic Strategy seeds after CFG PE/FY seed prerequisites.
9. Run clean-install, schema, seed, permission, API, unit and browser smoke tests.
10. Update the Revision Ledger with implementation evidence and product-owner approval status; do not revive retired documentation packs.

## 14.1 Repository removal checklist

- No executable import path containing kentender_procurement.demands.
- No Plan Value Commitment DocType/model/field/service/route/seed/test identifier except historical documentation assertions.
- No Strategy/Budget/statutory treatment model or planned-treatment value.
- No Public Value Objective engine in MVP navigation, hooks or mandatory validations.
- No first-PE, PE-MOH, first-OU or Administrator operational fallback.
- No user-editable generated reference field.
- No downstream mutation endpoint for Strategy records.

# 15\. Acceptance criteria

| **ID**     | **Observable acceptance outcome**                                                                                             |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------- |
| STR-AC-001 | Fresh site installs and migrates with Strategy Alignment enabled and the legacy demands package absent.                       |
| STR-AC-002 | Strategy workspace opens when Departmental Needs and Procurement Home are unavailable.                                        |
| STR-AC-003 | Zero, one and multiple PE/OU scope cases produce the specified outcomes with no silent fallback.                              |
| STR-AC-004 | System Administrator can open the neutral Strategy record read-only but cannot author or approve without explicit assignment. |
| STR-AC-005 | Strategy Author cannot access review/approval actions; unauthorised task routes are denied before form rendering.             |
| STR-AC-006 | A plan version cannot activate when another primary Active plan overlaps for the same PE.                                     |
| STR-AC-007 | A supporting framework can coexist only with an explicit type and relationship.                                               |
| STR-AC-008 | Approved and Active versions reject direct mutation and retain complete audit evidence.                                       |
| STR-AC-009 | Strategic Objective, Strategic Outcome, Performance Indicator and Performance Target remain distinct in schema and UI.        |
| STR-AC-010 | Strategy Value Commitment is the only active commitment term across code, UI, links, seeds and tests.                         |
| STR-AC-011 | Requester-facing Departmental Needs screens contain no Strategy selection or Strategy dependency.                             |
| STR-AC-012 | Budget and Planning retrieve scoped, approved Strategy context only through the service contract.                             |
| STR-AC-013 | Downstream attempts to mutate Strategy data are denied and audited.                                                           |
| STR-AC-014 | Seed rerun is idempotent and preserves MoH/Kisumu entity isolation.                                                           |
| STR-AC-015 | No removed treatment or PVO concept appears in schema, services, UI, navigation, seeds or runtime tests.                      |
| STR-AC-016 | A Plan approval boundary can create an immutable Strategy lineage snapshot from approved source records.                      |
| STR-AC-017 | All state transitions reject stale versions and retain actor, time, reason and correlation evidence.                          |
| STR-AC-018 | Static screen specifications contain no behavioural controls that are absent from implementation requirements and tests.      |

# 16\. Smoke contract

| **Gate**               | **Required command/test class**                          | **Pass condition**                                                           |
| ---------------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Static dependency scan | Search executable source, hooks and seed manifests       | No legacy demands or removed treatment imports.                              |
| Fresh environment      | Install → migrate → seed                                 | Completes without compatibility scripts or manual data repair.               |
| Module import          | Import Strategy hooks, services and workspace API        | No downstream module required at import time.                                |
| Seed repeatability     | Run CFG then Strategy seed twice                         | Same identities and counts; no duplicates; no fallback records.              |
| Domain tests           | Hierarchy, target, commitment and active-plan invariants | Positive and negative cases pass.                                            |
| Permission tests       | List, read, direct route, API, task and export matrix    | Neutral view and workflow authority remain separate.                         |
| Integration tests      | Budget/Planning context resolution and snapshot          | Scoped approved lineage returned; mutations rejected.                        |
| Browser smoke          | Workspace, list, detail, editor and review routes        | No runtime dialog, broken route, stale label or unauthorised form rendering. |

# 17\. Requirements traceability

| **Control objective**    | **Requirements**          | **Evidence**                                             |
| ------------------------ | ------------------------- | -------------------------------------------------------- |
| Module independence      | STR-FR-016, 017, 020      | Dependency scan, import test, downstream mutation test.  |
| Correct semantics        | STR-FR-006–009, 019       | Schema inspection, UI assertions, seed assertions.       |
| Scope and access         | STR-FR-001, 010, 015, 022 | PE/OU cases, permission matrix and audit events.         |
| Governed lifecycle       | STR-FR-004, 011–014       | Transition, overlap, immutability and concurrency tests. |
| Downstream traceability  | STR-FR-016–018            | Context, lineage and snapshot contract tests.            |
| Greenfield repeatability | STR-FR-002, 019–021       | Fresh install and double-seed smoke.                     |

# 18\. Risks and controls

| **Risk**                                                            | **Control**                                                                                               |
| ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| A rename is applied only to labels while old objects remain active. | Repository removal scan plus schema/metadata assertions; no compatibility aliases.                        |
| Strategy clean-up breaks Planning or Budget.                        | Read contracts replace direct imports; contract tests run before downstream implementation resumes.       |
| Multiple active plans create ambiguous lineage.                     | Database-safe overlap validation at activation plus concurrent activation test.                           |
| System Administrator becomes an operational approver.               | Technical role grants neutral view only; capability assignments are explicit and audited.                 |
| Seed hides missing configuration by creating default PE/FY data.    | CFG runs first; Strategy seed fails with a named missing-prerequisite error.                              |
| Static designs become the only source of behaviour.                 | All behaviour remains in FRs, state tables and acceptance tests; screen prompts contain composition only. |
| Synthetic demo strategy is mistaken for official policy.            | Every synthetic title/target is marked Demo and confined to fixture environments.                         |

# 19\. Approval record

| **Decision**                                        | **Status**       | **Owner/evidence**                                                                              |
| --------------------------------------------------- | ---------------- | ----------------------------------------------------------------------------------------------- |
| Approve STR-CHG-001 as the implementation authority | Pending          | Product owner approval to be recorded in the Revision Ledger.                                   |
| Retire conflicting Strategy instructions            | Pending approval | On approval, conflicting earlier Strategy requirements and implementation notes are superseded. |
| Implementation completion                           | Not started      | Requires all acceptance criteria and smoke gates.                                               |

# Sources

- Constitution of Kenya, Article 227 — Kenya Law: <https://new.kenyalaw.org/akn/ke/act/2010/constitution>
- Public Procurement and Asset Disposal Act, 2015, sections 44, 45 and 53 — Kenya Law: <https://new.kenyalaw.org/akn/ke/act/2015/33>
- Public Procurement and Asset Disposal Regulations, 2020, regulations 40–42 — Kenya Law: <https://new.kenyalaw.org/akn/ke/act/ln/2020/69>
- Public Service Commission (Performance Management) Regulations, 2021, regulation 14 — Kenya Law: <https://new.kenyalaw.org/akn/ke/act/ln/2021/114>
- Public Finance Management Act, 2012, section 126 — Kenya Law: <https://new.kenyalaw.org/akn/ke/act/2012/18>

_Sources reviewed for this change unit on 19 August 2026._