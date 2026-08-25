# STR-CHG-001 — Clean Strategy Alignment

| Control | Value |
|---|---|
| Document ID | STR-CHG-001 |
| Version | 1.4 |
| Date | 25 August 2026 |
| Status | Proposed for product-owner approval |
| Module | Strategy Alignment |
| Implementation posture | Correction in place; no compatibility layer |

**Controlling decision:** Retain Strategy Alignment as a small upstream governance module. It maintains approved strategy structures and exposes them through read-only contracts. It does not become a performance-management, treatment, corrective-action or procurement-workflow module.

## 1. Governing decision

This document is the single implementation authority for the Strategy Alignment cleanup. It replaces the earlier Strategy MVP requirements wherever those requirements conflict with this document.

The existing `kentender_strategy` application is corrected in place. Existing usable code and the successfully proven Strategy Portfolio UI pattern are reused. Removed concepts are deleted rather than aliased, redirected, dual-read or retained behind feature flags.

Completion requires one coherent result across schema, services, permissions, screens, seeds and tests. A field, action or screen not defined here is not part of the module.

### 1.1 Conflict and disposition register

| Earlier item | Disposition in v1.4 |
|---|---|
| Plan Value Commitment / Strategy Value Commitment | Remove completely. It duplicates the Strategic Objective and creates no separate decision. A Procurement Plan Item links one approved Strategic Objective directly. |
| Public Value Objective and PVO catalogue | Remove completely. No replacement object or screen. |
| Strategy treatment, planned treatment and treatment questionnaire | Remove completely. |
| Strategy Corrective Action | Remove completely. |
| Strategy-owned result capture, verification and remediation | Exclude. Contract Management owns delivery and verified results. |
| Strategy performance dashboard | Replace with the neutral, permission-gated Strategy Portfolio read surface. |
| Strategic Outcome between Objective and Indicator | Remove. It duplicates outcome-oriented Objective wording and is not used by Procurement Planning. A Performance Indicator measures one Strategic Objective directly. |
| Objective represented as a measure or PVO | Correct to an explicit **Strategic Objective** distinct from a Performance Indicator. |
| Administrator or first-record fallback authority | Remove. Use explicit, scoped Strategy assignments and fail closed. |
| Downstream direct Strategy table reads | Remove. Downstream modules use the contracts in section 10. |
| Delete-and-recreate cleanup | Reject. Correct the retained application in place. |

## 2. Purpose and outcomes

Strategy Alignment shall provide:

- one governed portfolio of strategic plans for each authorised Procuring Entity scope;
- immutable approved plan versions;
- a typed lineage from plan through objective, indicator and target;
- direct selection of approved Strategic Objectives by downstream Procurement Planning;
- explicit author, reviewer and approval authority responsibilities;
- deterministic resolution of the applicable active primary plan;
- immutable strategy snapshots at downstream approval boundaries; and
- neutral read access without granting workflow authority.

### 2.1 Scope exclusions

The module shall not contain:

- Public Value Objectives;
- Strategic Outcomes or an equivalent intermediate layer between Strategic Objective and Performance Indicator;
- treatment, remediation or corrective-action records;
- performance-result entry, verification or performance scoring;
- an advanced performance dashboard;
- requester-facing Strategy selection in Departmental Needs;
- budget creation or confirmation;
- procurement method, schedule, lot or tender configuration;
- delivery, acceptance or contract-performance records;
- editable technical identifiers;
- source-reference, evidence, attachment or contact fields;
- generic notes, rationale or description fields that have no defined consumer;
- baseline or tolerance fields in MVP 1;
- Plan Value Commitment, Strategy Value Commitment or any equivalent duplicate objective record; or
- a new Frappe shell, page header, breadcrumb, global selector or navigation system.

### 2.2 Data-purpose gate

No new stored field is permitted unless all three conditions are documented before implementation:

1. a current operational decision or output uses the field;
2. the screen, rule or service consuming it is named; and
3. its validation and system effect are defined.

“Useful later”, “common in similar systems” and “helpful context” are not sufficient reasons. Undocumented fields shall be omitted, not added as optional fields.

## 3. Fixed external constraints

- Procuring Entity, organisation-unit and Financial Year records come from Configuration and Governance. Strategy shall not create or infer them.
- Strategy lineage supports procurement traceability but does not approve a budget, procurement plan, tender or contract.
- New Procurement Plan Items may select only Strategic Objectives from the applicable Active plan version.
- Existing downstream snapshots remain historically valid after a plan is superseded or archived.
- Strategy owns definitions and targets. Contract Management owns delivery evidence and verified results.

## 4. Ownership and domain boundary

| Information or decision | Owner | Strategy relationship |
|---|---|---|
| Procuring Entity, organisation unit and Financial Year | Configuration and Governance | Read explicit configured identifiers. No fallback. |
| Strategic plan, version, hierarchy, indicator and target | Strategy Alignment | Create, govern, approve and expose read-only. |
| Departmental need | Departmental Needs | No requester-facing Strategy dependency. |
| Budget allocation and availability | Budget and Funding | May reference approved Strategy nodes or targets through contracts. |
| Procurement Plan Item and Plan Version | Procurement Planning | Select one approved Strategic Objective and retain its immutable strategy-lineage snapshot. |
| Tender and award | Tender Management | May inherit the approved snapshot; no direct Strategy edit. Consumer work is outside this change unit. |
| Delivery, acceptance, actual result and evidence | Contract Management | May later record results against inherited Strategy identifiers. |

Dependency direction is:

**Configuration and Governance → Strategy Alignment → Budget and Funding / Procurement Planning → Tender Management → Contract Management**

Strategy Alignment shall not import a downstream transactional module.

## 5. Canonical domain model

All references are generated by the server. System audit fields such as owner, creation time and modified time remain framework-managed and are not repeated below.

### 5.1 StrategicPlan

The stable identity of one strategic framework.

| Field | Operational purpose and system effect |
|---|---|
| `plan_id` | Immutable generated reference used by routes, contracts, audit and downstream snapshots. Not editable. |
| `procuring_entity_id` | Defines the owning PE and is used in permission and context resolution. Required. |
| `owner_org_unit_id` | Narrows applicability to one configured organisation unit when the plan is not PE-wide. Empty means PE-wide. |
| `title` | Human-readable plan identity used in lists, selectors and snapshots. Required. |
| `plan_role` | `Primary` or `Supporting Framework`; controls overlap and downstream resolution. Required. |
| `parent_primary_plan_id` | Links a Supporting Framework to its governing Primary plan. Required only when `plan_role` is `Supporting Framework` and forbidden when it is `Primary`. |
| `period_start` | Defines plan coverage and participates in active-plan resolution. Required. |
| `period_end` | Defines plan coverage and participates in active-plan resolution. Required and later than `period_start`. |

No separate plan-type taxonomy is stored. Plan role supplies the only classification required by current resolution rules; the PE and title identify the institution and plan.

### 5.2 StrategicPlanVersion

The approval boundary for the contents of one Strategic Plan.

| Field | Operational purpose and system effect |
|---|---|
| `plan_version_id` | Immutable generated reference used by hierarchy children, services and snapshots. |
| `plan_id` | Links the version to its stable Strategic Plan. |
| `version_number` | Establishes ordered version history and is generated per plan. |
| `based_on_plan_version_id` | Identifies the approved or Active version copied to create a successor and supplies the fixed comparison baseline for review. Empty only for the first version. |
| `status` | Controls editability, workflow actions and downstream eligibility. |
| `effective_from` | Determines when this version may become the resolved Active version. Required before approval. |
| `effective_to` | Ends version applicability and supports successor resolution. May be empty only while it is the current Active version within the plan period. |
| `return_reason` | Records why an In Review or Awaiting Approval version was returned. Required only for the Return action; otherwise absent from ordinary forms. |

Submitted, reviewed, approved, activated, superseded and archived actors and timestamps are audit events. They are not editable business fields.

### 5.3 StrategyNode

A typed structural node inside one plan version.

| Field | Operational purpose and system effect |
|---|---|
| `strategy_node_id` | Immutable generated reference used by parent links, lineage and downstream snapshots. |
| `plan_version_id` | Prevents content from leaking between plan versions. Required. |
| `node_type` | Selects the hierarchy rule and downstream lineage label. Required. |
| `parent_node_id` | Establishes the node's position. Empty only for a root Pillar. |
| `title` | Carries the approved strategic statement displayed in the hierarchy and snapshot. Required. |
| `display_order` | Produces deterministic sibling ordering. Required and unique among siblings. |

Allowed `node_type` values are:

- **Pillar**
- **Programme**
- **Sub-programme**
- **Strategic Objective**

An inapplicable optional layer is omitted. Blank placeholder nodes are forbidden.

### 5.4 PerformanceIndicator

A measure attached directly to one Strategic Objective.

| Field | Operational purpose and system effect |
|---|---|
| `indicator_id` | Immutable generated reference used by targets, lineage and snapshots. |
| `plan_version_id` | Binds the indicator to one immutable version. |
| `measures_node_id` | Identifies the Strategic Objective being measured. Required. |
| `name` | Provides the human-readable measure used in plan review and downstream snapshots. Required. |
| `definition` | Removes ambiguity about what the measure counts or calculates. Required and shown during review. |
| `unit` | Defines the target value's unit and prevents incompatible target entry. Required. |

No source, frequency, owner, result, evidence or score is stored in Strategy Alignment.

### 5.5 PerformanceTarget

A time-bound expected value for one Performance Indicator.

| Field | Operational purpose and system effect |
|---|---|
| `target_id` | Immutable generated reference used by lineage and snapshots. |
| `indicator_id` | Identifies the measure to which the target applies. Required. |
| `financial_year_id` | Anchors an annual target to a configured Financial Year. Required for annual targets. |
| `target_by_date` | Anchors a plan-period target when no annual Financial Year is used. Required only when `financial_year_id` is empty. |
| `comparison` | Defines how the value is interpreted: `At least`, `At most` or `Equal to`. Required. |
| `target_value` | Supplies the expected value in the indicator's inherited unit. Required. |

Exactly one of `financial_year_id` and `target_by_date` shall be present. Unit is inherited and is not duplicated on the target.

### 5.6 StrategyAuditEvent

An append-only system event containing event ID, record type and ID, action, actor, timestamp, before/after status, reason where required, and correlation ID. It is produced by commands and protected reads; users do not edit it.

## 6. Lifecycle and governance

### 6.1 Plan version lifecycle

| Current status | Command | Next status | Authorised actor |
|---|---|---|---|
| Draft | Submit for review | In Review | Strategy Author |
| In Review | Return | Returned | Strategy Reviewer |
| In Review | Recommend for approval | Awaiting Approval | Strategy Reviewer |
| Returned | Revise | Draft | Original or reassigned Strategy Author |
| Awaiting Approval | Return | Returned | Strategy Approval Authority |
| Awaiting Approval | Approve | Approved | Strategy Approval Authority |
| Approved | Activate | Active | Strategy Approval Authority |
| Active | Activate successor | Superseded | System, as part of the successor activation transaction |
| Superseded | Archive | Archived | Strategy Approval Authority |

There is no separate lifecycle for hierarchy, indicator or target records. They inherit the plan version status.

### 6.2 Governance rules

- Draft and Returned versions are editable only by an assigned Strategy Author.
- In Review, Awaiting Approval, Approved, Active, Superseded and Archived versions are read-only.
- The submitter cannot perform the reviewer recommendation on the same version.
- The author cannot approve or activate the same version.
- Return requires a reason of 10–500 characters.
- Approve and Activate are separate audited decisions.
- Activation revalidates scope, period, completeness and overlap inside one transaction.
- Activating a successor version supersedes the previous Active version of the same plan atomically.
- Records are never deleted after submission.

## 7. Roles and permissions

| Role | Permitted capability |
|---|---|
| Strategy Viewer | View approved, Active, Superseded and Archived Strategy records within assigned scope. |
| Strategy Author | Create plans and draft versions; edit Draft or Returned content; submit for review within assigned scope. |
| Strategy Reviewer | View live review tasks; return or recommend them within assigned scope. |
| Strategy Approval Authority | Return, approve, activate and archive live tasks within assigned scope. |
| Budget/Finance Officer | Read the applicable Active context and lineage through contracts; no Strategy workflow access. |
| Procurement Planner | List applicable Active Strategic Objectives and create approved downstream snapshots through contracts; no Strategy workflow access. |
| Auditor | Read scoped records, version history and audit evidence; no workflow action. |
| System Administrator | Inspect all records and technical metadata read-only unless separately assigned a Strategy role. |

Assignments are scoped by PE, optional organisation unit, plan role and effective dates. The same server-side scope filter applies to registers, counts, direct URLs, service calls, exports and task queues.

## 8. Business rules

| ID | Rule and enforcement |
|---|---|
| STR-BR-001 | Every Strategy record shall resolve to one explicit configured PE. Missing or unauthorised scope is rejected server-side. |
| STR-BR-002 | A Primary plan shall be PE-wide or scoped to one organisation unit and shall not have a parent plan. |
| STR-BR-003 | A Supporting Framework shall name one Active or governed Primary plan in the same PE and compatible OU scope. |
| STR-BR-004 | Two Primary plans for the same PE/OU shall not be Active for overlapping dates. The database transaction shall serialize the activation check. |
| STR-BR-005 | A plan period shall have `period_start < period_end`; every version effective date shall fall within that period. |
| STR-BR-006 | Approved or Active content is immutable. A correction requires a successor version whose `based_on_plan_version_id` identifies an Approved or Active version of the same plan. |
| STR-BR-007 | Allowed structural hierarchy is Pillar → Programme → optional Sub-programme → Strategic Objective. A Programme may parent an Objective when Sub-programme is omitted. |
| STR-BR-008 | A Performance Indicator shall measure one Strategic Objective from the same version and shall appear as its direct child in the authoring and review tree. |
| STR-BR-009 | An indicator name shall be unique under its measured node within one version. |
| STR-BR-010 | A target shall use exactly one configured Financial Year or one target-by date, and shall fall within the plan period. |
| STR-BR-011 | `target_value` shall be compatible with the indicator unit; Percentage values shall be between 0 and 100 inclusive. |
| STR-BR-012 | Submission requires complete plan identity, a valid hierarchy, at least one Strategic Objective, one Indicator and one Target. |
| STR-BR-013 | Only Strategic Objectives in an Active plan version are available for new Procurement Plan Item selection. |
| STR-BR-014 | The selected Strategic Objective shall belong to the resolved Active plan version and the same authorised PE/OU scope as the Procurement Plan Item. |
| STR-BR-015 | Approval and activation repeat all readiness checks; a stale client result cannot bypass server validation. |
| STR-BR-016 | Ordinary users never enter or modify generated identifiers. |
| STR-BR-017 | Zero matching Active primary plans returns `STRATEGY_CONTEXT_NOT_FOUND`; more than one returns `STRATEGY_CONTEXT_AMBIGUOUS`. Neither case chooses the first record. |
| STR-BR-018 | Downstream services return only authorised, Active data and never expose Draft or live workflow content. |
| STR-BR-019 | Downstream modules cannot update a Strategy record through a read or snapshot contract. |
| STR-BR-020 | Direct reads of Strategy database tables by downstream applications are prohibited. |

## 9. Downstream context and lineage

Resolution input is:

- `procuring_entity_id` — required;
- `owner_org_unit_id` — optional;
- exactly one of `as_of_date` or `financial_year_id`; and
- `include_supporting` — optional, default `false`.

Resolution order is:

1. validate PE, OU and Financial Year through Configuration and Governance;
2. identify Active Primary plan versions whose plan and version periods cover the requested date;
3. prefer an exact OU scope over PE-wide scope;
4. reject zero or multiple equally applicable Primary results;
5. return the Primary version; and
6. when requested, return explicitly linked Supporting Frameworks in deterministic title order.

The resolved result contains only IDs, titles, role, period, version, status and hierarchy summary required by a consumer. It contains no authoring or audit internals.

For a Procurement Plan Item, Strategy Alignment supplies one direct selection path:

1. Procurement Planning resolves the applicable Active plan version;
2. it lists Strategic Objectives from that version;
3. the planner selects exactly one Strategic Objective;
4. the Draft Plan Item stores the selected Objective ID; and
5. approval of the Procurement Plan Version creates an immutable snapshot of the plan, version, ancestor path and selected Objective.

Indicators and Targets remain visible below the Objective but are not alternative Procurement Plan Item selection objects.

## 10. Service contracts

All services are server-authorised, typed and versioned. They do not mutate Strategy content. `create_strategy_snapshot` returns an approval-bound snapshot payload for the calling module to store on its own approved record.

| Contract | Required input | Output and effect |
|---|---|---|
| `resolve_strategy_context` | PE, optional OU, date or FY, include-supporting flag | One applicable Active Primary version and optional Supporting Framework summaries; typed zero/ambiguous errors. |
| `list_strategy_objectives` | Resolved plan version ID, optional Programme/Sub-programme filter, search text and paging | Active Strategic Objectives with generated ID, title and full ancestor path; no Draft records. |
| `get_strategy_lineage` | One authorised Strategic Objective, Indicator or Target ID | Ordered path with stable IDs, types and titles from plan to the requested record. |
| `create_strategy_snapshot` | Consumer module, record ID/version, Strategic Objective ID, expected consumer status and approval correlation ID | Validates eligibility and returns a deterministic snapshot containing plan/version identity and period plus the ordered Pillar, Programme, optional Sub-programme and Strategic Objective IDs and titles. It records the snapshot audit event but does not write the consumer's record. Repeating the same approval correlation returns the same payload. |

`record_verified_result` is reserved for a later Contract Management change unit. Strategy Alignment v1.4 provides no result-entry fields, screen or production write endpoint.

### 10.1 Command contracts

| Command | Purpose |
|---|---|
| `save_strategy_plan_draft` | Create or update plan identity and Draft version metadata with optimistic concurrency. |
| `create_strategy_successor_version` | Copy one Approved or Active version into a new Draft of the same plan and set the immutable comparison baseline. |
| `save_strategy_structure_draft` | Create, update, reorder or remove Draft nodes, indicators and targets as one validated draft change set. |
| `submit_strategy_version` | Validate readiness and move Draft to In Review. |
| `review_strategy_version` | Return or recommend an In Review version. |
| `approve_strategy_version` | Return or approve an Awaiting Approval version. |
| `activate_strategy_version` | Revalidate and atomically activate an Approved version. |
| `archive_strategy_version` | Archive a Superseded version. |

Every write command requires the expected record version. A conflict returns `STRATEGY_STALE_WRITE`; the command shall not silently overwrite newer work.

## 11. UI architecture and routes

Strategy Alignment remains a top-level KenTender module named **Strategy Alignment**. The module menu contains only:

- **Strategy Portfolio**; and
- **Review tasks**, visible only to an assigned Strategy Reviewer or Strategy Approval Authority.

Do not retain navigation for PVOs, treatments, corrective actions or Strategy performance management.

| Screen | Canonical route | Purpose |
|---|---|---|
| STR-UI-01 Strategy Portfolio | `/app/strategy` | Scoped plan register and entry point for authoring or neutral viewing. |
| STR-UI-02 Plan workspace | `/app/strategy/plan/{plan_id}` | Plan identity, version summary and version navigation. |
| STR-UI-03 Structure editor | `/app/strategy/plan/{plan_id}/version/{version_number}/structure` | Draft hierarchy, indicators and targets. |
| STR-UI-04 Review task | `/app/strategy/review/{plan_version_id}` | Live reviewer, approver or activation decision surface. |

The plan workspace uses these persistent tabs:

- **Overview**
- **Structure**
- **History**

The active tab is represented by the URL. The existing proven Strategy Portfolio visual language and Vue-in-Frappe page pattern shall be reused. This document does not authorise a second dashboard, a separate application shell or a replacement Frappe header.

## 12. Static Claude Design contract

This section is the complete input to Claude Design. It defines static visual compositions only. Runtime behaviour belongs to section 13 and shall not be pasted into a design prompt.

### 12.1 Closed-input rules

- Produce desktop artboards at **1440 × 1024 px**.
- Reuse the approved KenTender Strategy Portfolio visual system, spacing, type scale, tokens, cards, tags, tables, fields, buttons, tabs, empty states and dialogs.
- The artboard starts below the Frappe Desk header. Do not draw Frappe navigation, the Desk header, breadcrumb, user menu, notifications, Help, global search or the PE/FY workspace selector.
- Breadcrumb text is fixture data outside the artboard. It is supplied to confirm location only.
- Use only the visible labels, values, badges, controls, sections and states stated for that artboard.
- Do not add summary cards, charts, KPIs, trend arrows, illustrations, side panels, steppers, tooltips, helper text, timestamps, metadata, action menus or table columns unless explicitly stated.
- Do not invent data. If a value or state is not stated, omit it.
- Do not encode behaviour, validation, permissions, API rules, routing, transitions or implementation instructions in the visual output.
- Do not show source references, evidence, attachments, contacts, descriptions, notes, baselines, tolerances, treatment, corrective actions, actual results or performance scores.
- Generated identifiers may be shown on saved records but never as editable fields.

The approved desktop shell inside every artboard is:

- full-width warm-white page background;
- a 1200 px maximum-width content column centred in the available page area;
- 32 px top and bottom page padding;
- page header followed by 24 px vertical spacing;
- 16 px gaps between cards or table sections; and
- no custom sidebar.

### 12.2 STR-DES-01 — Strategy Portfolio

**Fixture context — outside the artboard:** MOH Strategy Author · `str.author.moh@example.test` · Ministry of Health · 15 Mar 2027, 11:30 EAT · Frappe header breadcrumb: **Home > Strategy Alignment**

**Page content header**

- Eyebrow: **STRATEGY ALIGNMENT**
- Title: **Strategy Portfolio**
- Description: **Maintain the approved strategy structure used by Budget and Procurement Planning.**
- Right-aligned primary button: **New strategic plan**

**Context strip**

| Label | Value |
|---|---|
| Procuring Entity | PE-MOH — Ministry of Health |

**Tabs**

- **Plans 1** — selected
- **My work 0**

**Filter row, left to right**

- empty search field with placeholder **Search plan or reference**
- select showing **All plan roles**
- select showing **All statuses**

**Plans table**

| Strategic plan | Role | Period | Current version | Status | Action |
|---|---|---|---|---|---|
| Ministry of Health Strategic Plan (Demo) · STR-MOH-2023-001 | Primary | 2023/24–2027/28 | Version 1 | Active | View |

Footer text: **Showing 1 of 1 plan**

Do not show performance figures, targets achieved, risk, corrective actions, approval counts or charts.

### 12.3 STR-DES-02 — New strategic plan draft

**Fixture context — outside the artboard:** MOH Strategy Author · `str.author.moh@example.test` · Ministry of Health · 15 Mar 2027, 11:30 EAT · Frappe header breadcrumb: **Home > Strategy Alignment > New strategic plan**

**Page content header**

- Title: **New strategic plan**
- Status: **Draft**

**Plan identity card**

| Field label | Displayed value |
|---|---|
| Plan reference | Not assigned |
| Procuring Entity | PE-MOH — Ministry of Health |
| Organisation scope | PE-wide |
| Plan title | Ministry of Health Strategic Plan 2028–2032 (Demo) |
| Plan role | Primary |
| Plan period start | 1 Jul 2028 |
| Plan period end | 30 Jun 2033 |

Plan reference and Procuring Entity use the approved read-only field component. Organisation scope and Plan role use the approved select component. Plan title and the two Plan period rows use the approved input or date component appropriate to their displayed value.

**Fixed footer, left to right:** **Cancel**, **Save draft**. **Save draft** is the primary button.

Do not show structure fields, approval history, readiness checks or a submit action on this artboard.

### 12.4 STR-DES-03 — Active plan overview

**Fixture context — outside the artboard:** MOH Strategy Viewer · `str.viewer.moh@example.test` · Ministry of Health · 15 Mar 2027, 11:30 EAT · Frappe header breadcrumb: **Home > Strategy Alignment > STR-MOH-2023-001**

**Page content header**

- Eyebrow: **STR-MOH-2023-001**
- Title: **Ministry of Health Strategic Plan (Demo)**
- Status: **Active**
- No header action button

**Tabs:** **Overview** selected, **Structure**, **History**

**Plan identity card**

| Label | Value |
|---|---|
| Procuring Entity | PE-MOH — Ministry of Health |
| Organisation scope | PE-wide |
| Plan role | Primary |
| Plan period | 1 Jul 2023–30 Jun 2028 |
| Active version | Version 1 |
| Version effective period | 1 Jul 2023–30 Jun 2028 |

**Structure summary card**

| Item | Count |
|---|---|
| Pillars | 1 |
| Programmes | 1 |
| Sub-programmes | 1 |
| Strategic objectives | 1 |
| Performance indicators | 1 |
| Performance targets | 1 |

**Current authority card**

| Label | Value |
|---|---|
| Approved by | MOH Strategy Approval Authority |
| Approved | 30 Jun 2023, 15:40 EAT |
| Activated | 1 Jul 2023, 00:00 EAT |

Do not show edit controls, performance results, evidence, corrective action or downstream transaction counts.

### 12.5 STR-DES-04 — Draft structure editor

**Fixture context — outside the artboard:** MOH Strategy Author · `str.author.moh@example.test` · Ministry of Health · 15 Mar 2027, 11:30 EAT · Frappe header breadcrumb: **Home > Strategy Alignment > STR-MOH-2023-001 > Version 2 > Structure**

**Page content header**

- Eyebrow: **STR-MOH-2023-001 · VERSION 2**
- Title: **Strategy structure**
- Status: **Draft**
- Right-aligned secondary button: **Save draft**
- Right-aligned primary button: **Submit for review**

**Tabs:** **Overview**, **Structure** selected, **History**

Below the tabs, create a two-column working surface: 42% width for the hierarchy tree and 58% width for the selected-record card.

**Hierarchy tree header**

- Heading: **Plan hierarchy**
- Compact secondary button: **Add pillar**

**Expanded hierarchy tree — exact order and indentation**

1. **Digital health systems** · Pillar
   1. **Health policy, standards and regulation** · Programme
      1. **Digital health governance** · Sub-programme
         1. **Strengthen interoperable national digital health services** · Strategic Objective — selected
            1. **Percentage of priority facilities using interoperable digital health services** · Performance Indicator
               1. **At least 85% · FY 2027/28** · Performance Target

Use these exact compact trailing actions:

| Selected or displayed row type | Trailing action |
|---|---|
| Pillar | Add programme |
| Programme | Add sub-programme |
| Sub-programme | Add objective |
| Strategic Objective | Add indicator |
| Performance Indicator | Add target |
| Performance Target | None |

Do not show **Add outcome** or the generic label **Add child**. The selected row has the approved selected background and border.

**Selected record card**

- Heading: **Strategic Objective**
- Subtext: **Pillar / Programme / Sub-programme / Strategic Objective**

| Field label | Displayed value |
|---|---|
| Title | Strengthen interoperable national digital health services |
| Display order | 1 |

Card footer buttons, left to right: **Delete node**, **Save changes**. **Delete node** uses the danger-outline style; **Save changes** is primary.

Do not show an editable node code, description, owner, evidence, status or approval field.

### 12.6 STR-DES-05 — Indicator and target editor

**Fixture context — outside the artboard:** MOH Strategy Author · `str.author.moh@example.test` · Ministry of Health · 15 Mar 2027, 11:30 EAT · Frappe header breadcrumb: **Home > Strategy Alignment > STR-MOH-2023-001 > Version 2 > Structure**

Duplicate the completed STR-DES-04 artboard. Keep the hierarchy tree unchanged except select the Performance Indicator row. Replace the selected-record card with the following content.

**Selected record card**

- Heading: **Performance Indicator**
- Subtext: **Measures: Strengthen interoperable national digital health services**

| Field label | Displayed value |
|---|---|
| Indicator name | Percentage of priority facilities using interoperable digital health services |
| Definition | Priority facilities operating an approved interoperable digital health service divided by all priority facilities, expressed as a percentage. |
| Unit | Percentage |

**Targets subsection**

| Period | Expected result | Action |
|---|---|---|
| FY 2027/28 | At least 85% | Edit |

Below the table, right-aligned secondary button: **Add target**

Card footer buttons, left to right: **Delete indicator**, **Save changes**. **Delete indicator** uses the danger-outline style; **Save changes** is primary.

Do not show source, frequency, responsible owner, baseline, actual result, evidence, variance, score or status.

**Add target dialog artboard**

Create one additional static artboard over the dimmed Indicator editor.

- Title: **Add performance target**
- Intro text: **Set the expected value and period for this indicator.**
- Field label: **Period**
- Displayed choice: **FY 2027/28**
- Field label: **Expected result**
- Two controls on one row: comparison choice **At least** and numeric value **85**
- Read-only suffix beside the numeric value: **Percentage**
- Footer buttons: **Cancel** and **Add target**

Do not show target name, description, owner, baseline, tolerance, actual result, evidence, status or another unit control.

### 12.7 STR-DES-06 — Reviewer task · Overview

**Fixture context — outside the artboard:** MOH Strategy Reviewer · `str.reviewer.moh@example.test` · Ministry of Health · 16 Mar 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Strategy Alignment > Review tasks > STR-MOH-2023-001-V2**

**Page content header**

- Eyebrow: **STR-MOH-2023-001 · VERSION 2**
- Title: **Review strategic plan version**
- Status: **In Review**
- No header action button

**Tabs:** **Overview** selected, **Structure**, **Changes**, **History**

**Plan identity card**

| Label | Value |
|---|---|
| Strategic plan | Ministry of Health Strategic Plan (Demo) |
| Procuring Entity | PE-MOH — Ministry of Health |
| Organisation scope | PE-wide |
| Plan role | Primary |
| Plan period | 1 Jul 2023–30 Jun 2028 |
| Submitted version | Version 2 |
| Version effective period | 1 Jul 2027–30 Jun 2028 |

**Submission authority card**

| Label | Value |
|---|---|
| Submitted by | MOH Strategy Author |
| Submitted | 15 Mar 2027, 16:20 EAT |

**Readiness card**

| Check | Result |
|---|---|
| Plan identity complete | Ready |
| Hierarchy valid | Ready |
| Indicators and targets complete | Ready |
| Active-plan overlap | Ready |

**Structure summary card**

| Item | Count |
|---|---|
| Pillars | 1 |
| Programmes | 1 |
| Sub-programmes | 1 |
| Strategic objectives | 1 |
| Performance indicators | 1 |
| Performance targets | 1 |

**Fixed footer, left to right:** **Return**, **Recommend for approval**. **Return** uses the danger-outline style; **Recommend for approval** is primary.

Do not show editable fields, comments, attachments, evidence, performance results or Active Version 1 data on this artboard.

### 12.8 STR-DES-07 — Reviewer task · Structure

**Fixture context — outside the artboard:** MOH Strategy Reviewer · `str.reviewer.moh@example.test` · Ministry of Health · 16 Mar 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Strategy Alignment > Review tasks > STR-MOH-2023-001-V2**

Reuse the STR-DES-06 page content header and fixed footer without changing their content or placement.

**Tabs:** **Overview**, **Structure** selected, **Changes**, **History**

**Submitted plan structure card**

- Heading: **Submitted Version 2 structure**
- Subtext: **Read-only plan hierarchy**

Display this fully expanded hierarchy in the exact order and indentation shown:

1. **Digital health systems** · Pillar
   1. **Health policy, standards and regulation** · Programme
      1. **Digital health governance** · Sub-programme
         1. **Strengthen interoperable national digital health services** · Strategic Objective
            1. **Percentage of priority facilities using interoperable digital health services** · Performance Indicator
               1. **At least 85% · FY 2027/28** · Performance Target

No hierarchy row is selected. Do not show Add, Edit, Delete, drag, overflow-menu, checkbox or inline-action controls.

### 12.9 STR-DES-08 — Reviewer task · Changes

**Fixture context — outside the artboard:** MOH Strategy Reviewer · `str.reviewer.moh@example.test` · Ministry of Health · 16 Mar 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Strategy Alignment > Review tasks > STR-MOH-2023-001-V2**

Reuse the STR-DES-06 page content header and fixed footer without changing their content or placement.

**Tabs:** **Overview**, **Structure**, **Changes** selected, **History**

**Change comparison card**

- Heading: **Changes from Active Version 1**

| Changed item | Active Version 1 | Submitted Version 2 |
|---|---|---|
| FY 2027/28 performance target | At least 80% | At least 85% |

Text below the table: **No other plan identity or structure items changed.**

Do not show unchanged rows, inline editing, accept/reject controls, comments or a side-by-side document viewer.

### 12.10 STR-DES-09 — Reviewer task · History

**Fixture context — outside the artboard:** MOH Strategy Reviewer · `str.reviewer.moh@example.test` · Ministry of Health · 16 Mar 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Strategy Alignment > Review tasks > STR-MOH-2023-001-V2**

Reuse the STR-DES-06 page content header and fixed footer without changing their content or placement.

**Tabs:** **Overview**, **Structure**, **Changes**, **History** selected

**Version history card**

| Date and time | Event | Actor |
|---|---|---|
| 15 Mar 2027, 16:20 EAT | Submitted for review | MOH Strategy Author |
| 15 Mar 2027, 15:55 EAT | Draft saved | MOH Strategy Author |
| 15 Mar 2027, 13:10 EAT | Successor Version 2 created | MOH Strategy Author |

Do not show comments, attachments, evidence, technical request logs or events from another plan version.

### 12.11 STR-DES-10 — Approval task · four tab variants

Create four Approval Authority artboards by duplicating STR-DES-06, STR-DES-07, STR-DES-08 and STR-DES-09 respectively.

**Fixture context for all four approval artboards — outside the artboard:** MOH Strategy Approval Authority · `str.approver.moh@example.test` · Ministry of Health · 17 Mar 2027, 09:40 EAT · Frappe header breadcrumb: **Home > Strategy Alignment > Review tasks > STR-MOH-2023-001-V2**

Make exactly these changes on all four duplicates:

- title: **Approve strategic plan version**;
- status: **Awaiting Approval**;
- fixed-footer buttons: **Return**, **Approve**; **Return** uses the danger-outline style and **Approve** is primary; and
- retain the selected tab and all submitted Version 2 content from the corresponding Reviewer artboard.

On the **Overview** duplicate, replace the Submission authority card with this exact resulting card:

| Label | Value |
|---|---|
| Submitted by | MOH Strategy Author |
| Submitted | 15 Mar 2027, 16:20 EAT |
| Reviewed by | MOH Strategy Reviewer |
| Recommended | 16 Mar 2027, 10:22 EAT |

On the **History** duplicate, replace the Version history table with this exact resulting table:

| Date and time | Event | Actor |
|---|---|---|
| 16 Mar 2027, 10:22 EAT | Recommended for approval | MOH Strategy Reviewer |
| 15 Mar 2027, 16:20 EAT | Submitted for review | MOH Strategy Author |
| 15 Mar 2027, 15:55 EAT | Draft saved | MOH Strategy Author |
| 15 Mar 2027, 13:10 EAT | Successor Version 2 created | MOH Strategy Author |

Do not change the Structure or Changes content. Do not add an activation action, editable control, comment box, attachment or evidence panel to any Approval artboard.

### 12.12 STR-DES-11 — Approved version awaiting activation

**Fixture context — outside the artboard:** MOH Strategy Approval Authority · `str.approver.moh@example.test` · Ministry of Health · 17 Mar 2027, 10:05 EAT · Frappe header breadcrumb: **Home > Strategy Alignment > STR-MOH-2023-001 > Version 2**

**Page content header**

- Eyebrow: **STR-MOH-2023-001 · VERSION 2**
- Title: **Ministry of Health Strategic Plan (Demo)**
- Status: **Approved**
- Right-aligned primary button: **Activate version**

**Tabs:** **Overview** selected, **Structure**, **History**

**Version authority card**

| Label | Value |
|---|---|
| Plan period | 1 Jul 2023–30 Jun 2028 |
| Version effective period | 1 Jul 2027–30 Jun 2028 |
| Approved by | MOH Strategy Approval Authority |
| Approved | 17 Mar 2027, 09:47 EAT |
| Current Active version | Version 1 |

**Activation readiness card**

| Check | Result |
|---|---|
| Plan identity complete | Ready |
| Hierarchy valid | Ready |
| Indicators and targets complete | Ready |
| Active-plan overlap | Ready |

Do not show editable fields, an approval stepper, scheduling fields, a reason field or a second action button.

### 12.13 STR-DES-12 — Portfolio state variants

Create four static variants. Every variant contains the STR-DES-01 page content header, context strip, tabs and standard filter row. Do not show summary cards or plan rows.

Fixture context for Loading, No matches and Server error — outside the artboard: **MOH Strategy Author · `str.author.moh@example.test` · Ministry of Health · 15 Mar 2027, 11:30 EAT**. Fixture context for Forbidden — outside the artboard: **Kisumu Strategy Viewer · `str.viewer.kisumu@example.test` · Ministry of Health · 15 Mar 2027, 11:30 EAT**. Frappe header breadcrumb for all variants: **Home > Strategy Alignment**.

| Variant | Filter row | Main content | Buttons |
|---|---|---|---|
| Loading | Search, plan-role and status controls disabled | Five full-width skeleton table rows | None |
| No matches | Search value **County strategy**; selects show **All plan roles** and **All statuses** | Heading **No plans match these filters.** Body **Change or clear the filters to see other strategic plans.** | **Clear filters** |
| Forbidden | No filter row | Heading **You do not have access to Strategy Alignment.** Body **Ask your KenTender administrator to review your Strategy assignment.** | None |
| Server error | Standard empty filter row | Heading **Strategy plans could not be loaded.** Body **Try again. If the problem continues, contact KenTender support.** | **Try again** |

### 12.14 STR-DES-13 — Existing Frappe and KenTender controls

No design artboard is authorised for the Frappe header, breadcrumb, module menu, global page chrome, notifications, user menu or the existing KenTender PE/FY selector. Reuse those components without visual modification. The Procurement Planning Strategic Objective selector belongs to the Procurement Planning UI contract and is not designed in this Strategy change unit.

## 13. Functional interaction requirements — excluded from design prompts

This section defines behaviour for requirements, implementation and testing. It shall not be copied into Claude Design.

### 13.1 STR-UI-01 — Strategy Portfolio

- The server returns only plans within the actor's Strategy assignment.
- The selected PE context comes from the existing KenTender context control and is never inferred from the first available record.
- **Plans** shows all scoped records the actor may view. **My work** shows only live records on which the actor may perform the next command.
- Search matches plan reference and title. Plan role and status filters are server-side.
- Counts use the same permission query as rows.
- **New strategic plan** appears only for a scoped Strategy Author.
- Selecting **View**, **Continue draft**, **Review**, **Approve** or **Activate** follows the server-returned `available_action`; the browser does not derive authority from status alone.
- Browser back/forward restores filters, tab and selected record.

### 13.2 STR-UI-02 — Plan workspace

- A saved new-plan draft receives its generated plan and version references from the server.
- The first version effective period is set equal to the plan period; the user does not enter the same dates twice.
- Plan identity can be edited only while its first version is Draft or Returned and before downstream use exists.
- A Primary plan hides `parent_primary_plan_id`; a Supporting Framework requires selection of an eligible Primary plan.
- Active, Superseded and Archived versions always open read-only.
- **Create successor version** is offered only to an authorised Strategy Author on an approved or Active plan and creates a server-side copy of the current version.
- History is chronological and append-only; it shows lifecycle events, actor, timestamp and required return reason.

### 13.3 STR-UI-03 — Structure editor

- The server returns the full Draft tree with stable IDs and one expected version token.
- Add-child choices are limited by STR-BR-007 and returned by the server.
- Reorder updates only sibling `display_order` values and is saved as one atomic command.
- A node with descendants cannot be removed until its descendants are removed or explicitly moved in the same validated command.
- An indicator can be attached only to a Strategic Objective and is displayed directly beneath that Objective.
- **Add indicator** is available only on a Strategic Objective. **Add target** is available only on a Performance Indicator. No Outcome command or record is permitted.
- A target copies no unit field; its displayed unit is resolved from the indicator.
- **Add target** opens the exact dialog in STR-DES-05. **Edit** opens the same dialog with the current Period, comparison and value.
- Period offers only configured Financial Years overlapping the plan period and one plan-period date option when applicable.
- The unit is inherited from the Indicator, displayed read-only and never submitted as an independent Target value.
- One Indicator cannot contain two Targets for the same Financial Year or the same target-by date.
- Financial Year choices come from Configuration and Governance and are limited to years overlapping the plan period.
- Saving a stale tree returns `STRATEGY_STALE_WRITE` and preserves the user's unsaved values for deliberate reload or reconciliation.
- **Submit for review** calls readiness validation. If validation fails, the page shows an error summary and focuses the first failing record without changing status.

### 13.4 STR-UI-04 — Review task

- Direct task routes require the exact live capability. A neutral viewer is denied rather than shown a disabled workflow form.
- The route is bound to one `plan_version_id`. Overview, Structure, Changes and History always read that submitted version; they never fall back to the current Active version.
- The selected review tab is represented by the URL. Browser back/forward restores the prior tab without changing the submitted version or mounting a second page application.
- Overview returns plan identity, submission authority, readiness and structure counts from the submitted version.
- Structure returns the complete read-only submitted hierarchy, including Indicators and Targets.
- Changes is calculated server-side between `based_on_plan_version_id` and the submitted version. The client does not construct or infer the comparison.
- History returns only lifecycle and draft-save events for the submitted version in reverse chronological order.
- The role-appropriate decision footer remains available on every tab and every command carries the submitted version ID, expected status and expected record version.
- A Reviewer may Return or Recommend only while status is In Review.
- An Approval Authority may Return or Approve only while status is Awaiting Approval.
- Return opens a dialog containing only **Return reason**, **Cancel** and **Return**. The reason is validated server-side.
- Approve does not activate. The Approved plan workspace exposes **Activate version** only to the scoped Approval Authority.
- Activate reruns readiness and overlap guards under a transaction lock. A failed guard leaves the version Approved.
- Successful successor activation changes the new version to Active and the previous Active version of the same plan to Superseded in one transaction.

### 13.5 Common page states

- Loading never presents a false zero count.
- Empty filtered results provide **Clear filters**.
- A scope with no plans presents **No strategic plans exist for this scope.** and shows **New strategic plan** only to an authorised Author.
- Forbidden states disclose no plan names, counts or task details.
- A server failure retains any already displayed stable data and offers **Try again**.
- Focus order, keyboard operation, labels, contrast and live status messages shall meet the established KenTender accessibility standard.

### 13.6 Downstream Strategic Objective selection boundary

- Procurement Planning owns the Plan Item selector and its interaction design.
- Strategy Alignment returns eligible Objective rows only through `list_strategy_objectives`.
- Each row contains Objective ID, Objective title and the ordered Pillar → Programme → optional Sub-programme path so the planner can distinguish similar objectives.
- A Plan Item selects exactly one Strategic Objective. Indicator and Target are read-only associated measures, not alternative selector values.
- The Draft Plan Item stores the Objective ID. Procurement Plan Version approval calls `create_strategy_snapshot` and stores the returned immutable lineage.
- No Value Commitment field, model, service, label or compatibility mapping is permitted in Strategy Alignment or Procurement Planning.

## 14. Error contract

Errors return a stable code, plain-language message, correlation ID and field or record reference when applicable. Messages do not disclose records outside the actor's scope.

| Code | Message intent and effect |
|---|---|
| `STRATEGY_SCOPE_REQUIRED` | A valid PE and, where required, organisation-unit scope was not supplied. No record is created or changed. |
| `STRATEGY_PERMISSION_DENIED` | The actor lacks the required scoped capability. No protected data is returned. |
| `STRATEGY_CONFIG_MISSING` | A referenced PE, OU or Financial Year is missing or unavailable. The operation fails closed. |
| `STRATEGY_INVALID_STATE` | The command is not valid for the current server status. Current status is returned. |
| `STRATEGY_NOT_READY` | Submission, approval or activation readiness failed. Structured failing rule IDs are returned. |
| `STRATEGY_INVALID_HIERARCHY` | A node type, parent relationship, duplicate sibling or cross-version link is invalid. |
| `STRATEGY_INVALID_TARGET` | Target period, comparison or value is invalid for the indicator and plan. |
| `STRATEGY_OVERLAP` | Activation would create overlapping Active Primary authority. No status changes occur. |
| `STRATEGY_CONTEXT_NOT_FOUND` | No applicable Active Primary plan exists for the requested scope and date/FY. |
| `STRATEGY_CONTEXT_AMBIGUOUS` | More than one equally applicable Active Primary plan exists. No record is selected. |
| `STRATEGY_OBJECTIVE_NOT_ELIGIBLE` | The selected Objective is missing, outside the resolved version or scope, or not in an Active plan version. No link or snapshot is produced. |
| `STRATEGY_STALE_WRITE` | The expected record version is stale. No newer changes are overwritten. |
| `STRATEGY_DOWNSTREAM_FORBIDDEN` | A downstream caller attempted an unsupported read, Draft access or mutation. |

Validation errors identify the exact record and field without exposing internal tracebacks. Unexpected failures are logged server-side and return the standard KenTender support message plus correlation ID.

## 15. Audit and historical integrity

The following events are append-only:

- plan and successor-version creation;
- Draft structural change sets;
- submit, return, recommend, approve, activate, supersede and archive;
- permission or segregation denial;
- successful and failed context resolution;
- Strategic Objective listing and lineage reads by a downstream module; and
- snapshot creation or idempotent snapshot reuse.

Each event records actor, scoped capability, PE/OU, record and version IDs, action, timestamp, before/after status, required reason and correlation ID. A downstream contract event also records the calling module.

Approved, Active, Superseded and Archived versions are immutable. A Strategy snapshot is copied into the downstream approval record and does not change when the source plan later changes status. Deleting lifecycle events, renumbering versions and reusing generated references are prohibited.

## 16. Seed contract

Seed data is deterministic, synthetic and required for integration, permission and cross-PE-isolation tests. It is not policy or production master data.

### 16.1 Configuration prerequisites

Strategy seed shall resolve these existing Configuration and Governance records and fail with `STRATEGY_CONFIG_MISSING` if any is absent:

| Record | Required identifier |
|---|---|
| Ministry of Health | `PE-MOH` |
| County Government of Kisumu | `PE-CGK` |
| Financial Year 2027/28 | `FY-2027-2028` |

The Strategy seed shall not create a PE, OU, Financial Year or PE/FY Context and shall not select the first available record.

### 16.2 Test actors and assignments

| User ID | Display name | Assignment and test purpose |
|---|---|---|
| `str.author.moh@example.test` | MOH Strategy Author | Strategy Author for PE-MOH; authoring and submit tests. |
| `str.reviewer.moh@example.test` | MOH Strategy Reviewer | Strategy Reviewer for PE-MOH; review and segregation tests. |
| `str.approver.moh@example.test` | MOH Strategy Approval Authority | Strategy Approval Authority for PE-MOH; approval and activation tests. |
| `str.viewer.moh@example.test` | MOH Strategy Viewer | Strategy Viewer for PE-MOH; neutral-read tests. |
| `str.author.kisumu@example.test` | Kisumu Strategy Author | Strategy Author for PE-CGK; cross-PE authoring tests and deterministic seed authority. |
| `str.reviewer.kisumu@example.test` | Kisumu Strategy Reviewer | Strategy Reviewer for PE-CGK; cross-PE review tests and deterministic seed authority. |
| `str.approver.kisumu@example.test` | Kisumu Strategy Approval Authority | Strategy Approval Authority for PE-CGK; cross-PE approval tests and deterministic seed authority. |
| `str.viewer.kisumu@example.test` | Kisumu Strategy Viewer | Strategy Viewer for PE-CGK; cross-PE isolation tests. |
| `str.auditor@example.test` | Strategy Auditor | Auditor for PE-MOH and PE-CGK; audit-read tests. |

No actor receives Strategy authority from Administrator or System Manager alone.

### 16.3 Ministry of Health plan

| Field | Seed value |
|---|---|
| Plan ID | `STR-MOH-2023-001` |
| Title | Ministry of Health Strategic Plan (Demo) |
| Procuring Entity | `PE-MOH` |
| Organisation scope | PE-wide |
| Plan role | Primary |
| Period | 1 Jul 2023–30 Jun 2028 |
| Version | 1 |
| Version ID | `STR-MOH-2023-001-V1` |
| Version effective period | 1 Jul 2023–30 Jun 2028 |
| Status | Active |

Exact lifecycle authority:

| Event | Actor | Date and time |
|---|---|---|
| Submitted for review | MOH Strategy Author | 28 Jun 2023, 09:10 EAT |
| Recommended for approval | MOH Strategy Reviewer | 29 Jun 2023, 10:25 EAT |
| Approved | MOH Strategy Approval Authority | 30 Jun 2023, 15:40 EAT |
| Activated | MOH Strategy Approval Authority | 1 Jul 2023, 00:00 EAT |

Exact hierarchy:

| Order | Stable ID | Type | Title or value |
|---|---|---|---|
| 1 | `PIL-MOH-2023-001` | Pillar | Digital health systems |
| 2 | `PRG-MOH-2023-001` | Programme | Health policy, standards and regulation |
| 3 | `SPR-MOH-2023-001` | Sub-programme | Digital health governance |
| 4 | `OBJ-MOH-2023-001` | Strategic Objective | Strengthen interoperable national digital health services |
| 5 | `IND-MOH-2023-001` | Performance Indicator | Percentage of priority facilities using interoperable digital health services |
| 6 | — | Indicator definition | Priority facilities operating an approved interoperable digital health service divided by all priority facilities, expressed as a percentage. |
| 7 | — | Indicator unit | Percentage |
| 8 | `TGT-MOH-2027-001` | Performance Target | FY 2027/28 · At least 80% |

### 16.4 County Government of Kisumu isolation plan

| Field | Seed value |
|---|---|
| Plan ID | `STR-KSM-2023-001` |
| Title | Kisumu County Development Strategy (Demo) |
| Procuring Entity | `PE-CGK` |
| Organisation scope | PE-wide |
| Plan role | Primary |
| Period | 1 Jan 2023–31 Dec 2027 |
| Version | 1 |
| Version ID | `STR-KSM-2023-001-V1` |
| Version effective period | 1 Jan 2023–31 Dec 2027 |
| Status | Active |

Exact lifecycle authority:

| Event | Actor | Date and time |
|---|---|---|
| Submitted for review | Kisumu Strategy Author | 28 Dec 2022, 09:00 EAT |
| Recommended for approval | Kisumu Strategy Reviewer | 29 Dec 2022, 11:10 EAT |
| Approved | Kisumu Strategy Approval Authority | 30 Dec 2022, 14:15 EAT |
| Activated | Kisumu Strategy Approval Authority | 1 Jan 2023, 00:00 EAT |

Exact minimal hierarchy:

| Order | Stable ID | Type | Title or value |
|---|---|---|---|
| 1 | `PIL-KSM-2023-001` | Pillar | Digital county services |
| 2 | `PRG-KSM-2023-001` | Programme | County administration and digital services |
| 3 | `OBJ-KSM-2023-001` | Strategic Objective | Improve reliable access to priority county digital services |
| 4 | `IND-KSM-2023-001` | Performance Indicator | Percentage of priority county services available through approved digital channels |
| 5 | — | Indicator definition | Priority county services available through an approved digital channel divided by all priority county services, expressed as a percentage. |
| 6 | — | Indicator unit | Percentage |
| 7 | `TGT-KSM-2027-001` | Performance Target | By 31 Dec 2027 · At least 70% |

### 16.5 Isolated design and workflow fixture

The Version 2 data shown in STR-DES-04 through STR-DES-11 is an isolated test fixture, not part of the default Active seed.

| Fixture item | Exact value |
|---|---|
| Submitted version ID | `STR-MOH-2023-001-V2` |
| Based on version ID | `STR-MOH-2023-001-V1` |
| Effective period | 1 Jul 2027–30 Jun 2028 |
| Only content change | FY 2027/28 target: At least 80% → At least 85% |
| Successor created | 15 Mar 2027, 13:10 EAT · MOH Strategy Author |
| Draft saved | 15 Mar 2027, 15:55 EAT · MOH Strategy Author |
| Submitted for review | 15 Mar 2027, 16:20 EAT · MOH Strategy Author |
| Recommended for approval | 16 Mar 2027, 10:22 EAT · MOH Strategy Reviewer |

Test setup may place the version in Draft, In Review, Awaiting Approval or Approved status for the named artboard or test and must remove or roll it back after the test.

### 16.6 Seed execution rules

- Upsert by the exact stable seed identifiers; do not create duplicates.
- A second seed run shall produce no semantic change, new version or duplicate audit authority.
- Validate each plan through the same domain rules used by commands.
- Seed lifecycle events use the named role actors, never Administrator.
- Fail loudly on missing configuration, invalid hierarchy, invalid target or conflicting Active plan.
- Mark all synthetic records visibly as **(Demo)** in plan titles; do not add a generic disclaimer field.

## 17. Acceptance contract

| ID | Acceptance result |
|---|---|
| STR-AC-001 | The module installs and imports without the legacy Demands package or Procurement Home. |
| STR-AC-002 | No executable metadata, route, service, field, label, seed or active test refers to Plan Value Commitment, Strategy Value Commitment, PVO, Strategic Outcome, treatment or Strategy Corrective Action. |
| STR-AC-003 | A scoped Author can create a Draft plan and receives generated plan/version references. |
| STR-AC-004 | An unassigned user and a System Administrator without Strategy assignment cannot create, review, approve or activate. |
| STR-AC-005 | A Draft can represent Pillar → Programme → optional Sub-programme → Objective, with Indicator directly beneath Objective and Target directly beneath Indicator. |
| STR-AC-006 | Strategic Objective and Performance Indicator are distinct types and cannot be substituted for one another; no Strategic Outcome type exists. |
| STR-AC-007 | Target validation enforces period choice, comparison, unit-compatible value and percentage range. |
| STR-AC-008 | Readiness blocks submission when plan identity or hierarchy is invalid, or when the version has no Strategic Objective, Indicator or Target. |
| STR-AC-009 | A Procurement Plan Item can select exactly one Strategic Objective from its resolved Active plan version and cannot select an Indicator or Target instead. |
| STR-AC-010 | Reviewer recommendation and Approval Authority approval use distinct scoped capabilities; the Author cannot perform either on the same version. |
| STR-AC-011 | Return requires a reason and preserves the complete workflow history. |
| STR-AC-012 | Approved and Active content cannot be edited; a successor version is required. |
| STR-AC-013 | Concurrent activation cannot create overlapping Active Primary authority. |
| STR-AC-014 | Activating a successor version atomically supersedes the previous Active version of the same plan. |
| STR-AC-015 | Zero and multiple context matches return typed errors and never use first-record fallback. |
| STR-AC-016 | `resolve_strategy_context` returns the correct MoH or Kisumu Active plan and never leaks the other PE's data. |
| STR-AC-017 | `list_strategy_objectives` returns only Active, scoped Strategic Objectives with exact generated IDs and ordered ancestor paths. |
| STR-AC-018 | `get_strategy_lineage` returns exact stable IDs, types and titles in plan-to-record order. |
| STR-AC-019 | `create_strategy_snapshot` captures the selected Strategic Objective and its exact plan-to-objective lineage and is immutable and idempotent for one downstream approval correlation ID. |
| STR-AC-020 | Downstream direct-table mutation and Draft reads are rejected. |
| STR-AC-021 | A neutral viewer can open an authorised Active plan but cannot open a live workflow task. |
| STR-AC-022 | Portfolio counts, rows, routes, exports and APIs apply the same server-side scope. |
| STR-AC-023 | The default seed is deterministic and an immediate second run produces no change. |
| STR-AC-024 | Missing CFG prerequisites fail seed execution without creating fallback records. |
| STR-AC-025 | The four primary screen routes render without console error and match their approved static designs. |
| STR-AC-026 | Loading, no-match, forbidden and server-error states disclose no false or unauthorised data. |
| STR-AC-027 | Frappe header, breadcrumb and existing PE/FY selector are reused and are not duplicated inside the Vue page. |
| STR-AC-028 | No Strategy page or API accepts Value Commitment, source-reference, evidence, attachment, contact, baseline, treatment, actual-result or corrective-action data. |
| STR-AC-029 | Reviewer and Approval Authority can inspect Overview, Structure, Changes and History for the exact submitted version, and no tab substitutes current Active-version content. |
| STR-AC-030 | Reviewer and Approval Authority decision actions remain available on every review tab and reject a stale version or status. |

### 17.1 Minimum rule coverage

| Rule group | Required automated coverage |
|---|---|
| Scope and permission | STR-BR-001–004, STR-AC-003–004, STR-AC-010, STR-AC-021–022 |
| Domain structure | STR-BR-005–012, STR-AC-005–009, STR-AC-012 |
| Lifecycle and activation | STR-BR-004, STR-BR-006, STR-BR-015–017, STR-AC-010–016 |
| Downstream Objective and contracts | STR-BR-013–014, STR-BR-018–020, STR-AC-009, STR-AC-016–020 |
| Seeds and isolation | STR-AC-023–024 |
| UI | STR-AC-025–030 |

## 18. Implementation and test constraints

### 18.1 Frappe and UI implementation

- Delete the existing Plan/Strategy Value Commitment DocTypes, child-link table, services, routes, page fixtures, seeds and tests. Do not preserve an alias or compatibility response field.
- Remove `Strategic Outcome` from Strategy node metadata, services, commands, fixtures, screens and tests. During cleanup, an Indicator currently attached to an Outcome is reattached to that Outcome's direct parent Strategic Objective, then the Outcome is removed. The cleanup fails loudly if the parent is not exactly one Strategic Objective or if the link crosses a plan version; it never guesses another Objective.
- Replace downstream Strategy-contract imports and Budget/Planning test fixtures with `list_strategy_objectives`, `get_strategy_lineage` and the Objective-based `create_strategy_snapshot` shape defined in section 10.
- Reuse the proven Vue 3 single-file-component pattern mounted into one `frappe.ui.make_app_page()` Desk page.
- Reuse the approved Strategy design tokens and scoped component styles. Do not import Claude Design runtime files into production.
- Keep design exports under `docs/` as visual evidence. Port their semantic composition into repository-owned Vue components.
- Do not add Tailwind, CDN styles, global CSS resets or a second application shell.
- Scope component styles so Frappe Desk chrome does not alter page controls and page styles do not bleed into Desk.
- Mount once per route and unmount on Frappe page teardown. Do not install duplicate route or `popstate` listeners.
- Use stable `data-testid` hooks on primary controls, tabs, tables, status badges, errors and dialogs.
- All permissions, transitions and invariants remain server-side even when the UI disables or hides an action.

### 18.2 TDD and efficient verification

For every behaviour change:

1. add or identify the smallest failing unit, service or component test;
2. run only that test while implementing the fix;
3. run the directly affected test file;
4. run the relevant Strategy test group after the local tests pass; and
5. run the full Strategy application suite once at the completion of the change group, not after every small edit.

Run cross-module contract tests only when a public Strategy contract or snapshot shape changes. Run fresh install/migrate/seed, idempotency and browser smoke once at the release-candidate checkpoint and again only if a later change affects installation, seed or UI wiring.

Browser verification is one focused path per role:

- Author: open Portfolio → create/save Draft → edit structure → submit;
- Reviewer: open task → inspect Overview, Structure, Changes and History → recommend;
- Approval Authority: inspect Overview, Structure, Changes and History → approve → activate;
- Viewer: open Active plan and confirm no workflow actions; and
- forbidden actor: confirm no data disclosure.

Do not wait for `networkidle` on Frappe Desk. Wait for DOM content and an explicit page-ready element because persistent socket connections may remain open.

### 18.3 Required release evidence

- static scan showing no removed concept or legacy Demands import in executable Strategy code;
- schema and metadata migration succeeds;
- deterministic seed succeeds twice;
- targeted domain, permission, lifecycle and contract tests pass;
- full `kentender_strategy` suite passes once after targeted stabilization;
- Budget contract consumer tests pass;
- production build succeeds without global CSS regression; and
- scripted browser smoke passes with no Strategy-page console or request failure.

## 19. Prohibited shortcuts

- No PVO, treatment, corrective-action or performance-result concept under a new label.
- No alias DocType, compatibility service, dual read, shadow write or silent fallback for removed records.
- No first PE, first OU, first Financial Year, first plan or Administrator fallback.
- No downstream raw SQL or ORM read of Strategy tables.
- No client-only permission, readiness, overlap or transition enforcement.
- No editable generated reference.
- No mutation of Approved or Active content.
- No Value Commitment, alignment statement or equivalent duplicate of the Strategic Objective under another label.
- No arbitrary JSON field used to avoid the canonical hierarchy or direct Strategic Objective reference.
- No optional source, evidence, attachment, contact, description, note, baseline or owner field “for future use”.
- No design-system invention of data, states, controls, columns or copy.
- No behaviour or implementation rule inside Claude Design prompts.
- No Frappe header, breadcrumb or PE/FY selector recreated inside the page canvas.
- No full-suite rerun after every local fix when a targeted test can provide the required feedback.

## 20. Traceability sources

This document reconciles and supersedes conflicting Strategy requirements contained in:

- `04_Strategy_Alignment_MVP1_Requirements.md`;
- `02_Strategy_Cleanup_Plan.md`; and
- `KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1.0.md`.

It consumes PE/FY configuration through the approved `KenTender_CFG-CHG-002_PE_and_Financial_Year_Maintenance_v0.3.md` contract. Where an earlier item is not retained in this v1.4 document, it is outside the proposed Strategy Alignment scope.
