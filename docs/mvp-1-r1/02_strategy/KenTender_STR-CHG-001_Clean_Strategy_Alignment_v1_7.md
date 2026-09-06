# STR-CHG-001 — Clean Strategy Alignment

| Control | Value |
|---|---|
| Document ID | STR-CHG-001 |
| Version | 1.7 |
| Change type | **Amendment to the approved v1.6.** Adopts KT-STD-001 v1.2 §3A: the authorisation verdict resolves before any content renders, a page-load denial is an inline state and never a modal, navigation is gated rather than hidden, and the Forbidden panel names the responsibilities that open the surface. No domain decision changes. |
| Date | 3 September 2026 |
| Status | **Approved** |
| Approved on | 3 September 2026 |
| Supersedes | v1.5 and all earlier versions, in full |
| Module | Strategy Alignment |
| Change type | Complete successor to v1.5. Realigns authorization, scope, fiscal year, fixtures and artboards to the one-site-one-PE model. |
| Standards | Governed by KT-STD-001 v1.2. Sections not restated here are inherited from it. |
| Implementation posture | Correction in place; no compatibility layer |

**Controlling decision:** Strategy Alignment is a small upstream governance module. It maintains approved strategy structures for the one Procuring Entity this site represents, and exposes them through read-only contracts. Strategy responsibilities are **site-wide**: there is no per-plan organisational scope. It does not become a performance-management, treatment, corrective-action or procurement-workflow module.

---

## 1. Governing decision

This document is the single implementation authority for Strategy Alignment. The existing `kentender_strategy` application is corrected in place. Removed concepts are deleted rather than aliased, redirected, dual-read or retained behind feature flags.

Completion requires one coherent result across schema, services, permissions, screens, seeds and tests. A field, action or screen not defined here is not part of the module.

### 1.1 Conflict and disposition register

Items disposed of in v1.5 and not reopened: Plan Value Commitment and Strategy Value Commitment; Public Value Objectives and the PVO catalogue; treatment, planned treatment and treatment questionnaire; Strategy Corrective Action; Strategy-owned result capture and verification; the Strategy performance dashboard; Strategic Outcome as a layer between Objective and Indicator; the Strategy Reviewer / Strategy Approval Authority split; the Strategy Viewer workflow role; the In Review, Returned, Awaiting Approval, Approved and Archived statuses; downstream direct table reads; and delete-and-recreate cleanup.

New in v1.6:

| Earlier item | Disposition in v1.6 |
|---|---|
| `procuring_entity_id` on `StrategicPlan` | **Remove.** One site is one Procuring Entity. The field is denormalised data with no choice behind it, and a second copy of the PE is a second source of truth for the permission engine. |
| `owner_org_unit_id` on `StrategicPlan` | **Remove.** Strategy responsibilities are site-wide (§6). With no rule reading the field, KT-STD-001 §7's data-purpose gate requires its omission. A directorate-level framework is expressed as a **Supporting Framework** distinguished by title, not by scope. |
| Frappe Roles plus PE/OU User Permissions as the Strategy authorization mechanism | **Remove.** Replaced by role-bound `User Responsibility Assignment` resolved through registered Frappe permission hooks, per AUTH-ADR-001 v1.6 §5.2–5.3. |
| STR-AC-032 requiring authorisation through native User Permission | **Invert.** The criterion now requires that no User Permission participate in a Strategy authorization path. |
| `financial_year_id` referencing a KenTender `FinancialYear` | Replace with `fiscal_year`, referencing the ERPNext `Fiscal Year` governed by CFG-CHG-002 v0.6 §4.2. |
| §9 resolution step "prefer an exact OU scope over PE-wide scope" | **Remove.** It was a silent precedence rule contradicting STR-BR-017, and it has no meaning once scope is site-wide. Ambiguity is rejected, never resolved by preference. |
| County Government of Kisumu (`PE-CGK`) seed plan, its three fixture actors and every cross-PE isolation test | **Remove entirely.** Creating a second Procuring Entity is structurally impossible under CFG-AC-003, so the seed would fail unconditionally. Cross-PE isolation is now guaranteed by deployment topology, not by an in-product test. |
| Bespoke fixture cast (`str.author.moh@…`, `str.approver.moh@…`, `str.auditor@…`) | Replace with the shared register in KT-STD-001 §8.3, extended by the three Strategy actors named in §14.1. |
| Fixture timeline of 15–16 March 2027 | Realign to 24–25 November 2026, matching KT-STD-001 §8.5 and the seeded Fiscal Years. |
| PE row in the STR-DES-01 context strip and in the STR-DES-02, STR-DES-03 and STR-DES-06 identity cards | **Remove.** KT-STD-001 §2.3 prohibits a PE column or context record on any artboard. STR-DES-01's strip contained only that row, so the strip is deleted. |
| "the existing KenTender PE/FY selector" in §12.1 and §12.12 | **Remove.** The component no longer exists. |
| Restated closed-input rules, common page states, TDD protocol, release evidence and product-wide prohibitions | **Remove.** Cite KT-STD-001. |
| Citation of `CFG-CHG-002_PE_and_Financial_Year_Maintenance_v0.3` | Replace with CFG-CHG-002 v0.6, *Site Configuration and System Setup*. |

---

## 2. Purpose and exclusions

Strategy Alignment shall provide: one governed portfolio of strategic plans for this entity; immutable Active plan versions; a typed lineage from plan through objective, indicator and target; direct selection of Strategic Objectives from the Active version by Procurement Planning; explicit Strategy Author and Strategy Approver responsibilities; deterministic resolution of the applicable Active Primary plan; immutable strategy snapshots at downstream approval boundaries; and neutral read access without workflow authority.

The module shall not contain: Public Value Objectives; Strategic Outcomes or an equivalent intermediate layer; treatment, remediation or corrective-action records; performance-result entry, verification or scoring; an advanced performance dashboard; requester-facing Strategy selection in Departmental Needs; budget creation or confirmation; procurement method, schedule, lot or tender configuration; delivery, acceptance or contract-performance records; editable technical identifiers; source-reference, evidence, attachment or contact fields; generic notes, rationale or description fields with no defined consumer; baseline or tolerance fields in MVP 1; any duplicate of the Strategic Objective under another label; or a new Frappe shell, page header, breadcrumb, global selector or navigation system.

The data-purpose gate and the omission default are in KT-STD-001 §7.

---

## 3. Fixed external constraints and ownership

- The Fiscal Year catalogue comes from ERPNext through Configuration and Governance. Strategy shall not create or infer a year.
- Strategy lineage supports procurement traceability but approves no budget, procurement plan, tender or contract.
- New Procurement Plan Items may select only Strategic Objectives from the applicable Active plan version.
- Existing downstream snapshots remain historically valid after a plan is superseded.
- Strategy owns definitions and targets. Contract Management owns delivery evidence and verified results.

| Information or decision | Owner | Strategy relationship |
|---|---|---|
| Site Procuring Entity, Organisation Units, Fiscal Year | Configuration and Governance | Read the Fiscal Year catalogue only. Strategy references no PE or Organisation Unit. |
| Business authority and scope resolution | AUTH-ADR-001 v1.6 | Strategy declares required business roles; it implements no permission mechanism. |
| Strategic plan, version, hierarchy, indicator, target | Strategy Alignment | Create, govern, approve and expose read-only. |
| Departmental need | Departmental Needs | No requester-facing Strategy dependency. |
| Budget allocation and availability | Budget and Funding | May reference approved Strategy nodes or targets through contracts. |
| Procurement Plan Item and Plan Version | Procurement Planning | Select one approved Strategic Objective and retain its immutable lineage snapshot. |
| Tender, award, delivery, acceptance, actual result | Tender and Contract Management | May inherit the approved snapshot; no direct Strategy edit. |

Dependency direction is **Configuration and Governance → Strategy Alignment → Budget and Funding / Procurement Planning → Tender Management → Contract Management**. Strategy Alignment shall not import a downstream transactional module.

---

## 4. Canonical domain model

All references are server-generated. Framework audit fields remain framework-managed and are not repeated.

### 4.1 StrategicPlan

| Field | Operational purpose and system effect |
|---|---|
| `plan_id` | Immutable generated reference used by routes, contracts, audit and downstream snapshots. Not editable. |
| `title` | Human-readable plan identity used in lists, selectors and snapshots. Required. |
| `plan_role` | `Primary` or `Supporting Framework`; controls overlap and downstream resolution. Required. |
| `parent_primary_plan_id` | Links a Supporting Framework to its governing Primary plan. Required when `plan_role` is `Supporting Framework`; forbidden when `Primary`. |
| `period_start` | Defines plan coverage and participates in Active-plan resolution. Required. |
| `period_end` | Defines plan coverage and participates in Active-plan resolution. Required and later than `period_start`. |

There is no `procuring_entity_id` and no `owner_org_unit_id`. Every plan belongs to the site entity by construction, and Strategy responsibilities are site-wide. No separate plan-type taxonomy is stored: plan role supplies the only classification current resolution rules require, and the title identifies the plan.

### 4.2 StrategicPlanVersion

| Field | Operational purpose and system effect |
|---|---|
| `plan_version_id` | Immutable generated reference used by hierarchy children, services and snapshots. |
| `plan_id` | Links the version to its stable Strategic Plan. |
| `version_number` | Establishes ordered version history; generated per plan. |
| `based_on_plan_version_id` | Identifies the Active version copied to create a successor and supplies the fixed comparison baseline for approval. Empty only for the first version. |
| `status` | Controls editability, workflow actions and downstream eligibility. |
| `effective_from` | Determines when this version may become the resolved Active version. Required before approval. |
| `effective_to` | Ends version applicability and supports successor resolution. May be empty only while it is the current Active version within the plan period. |
| `return_reason` | Records why a Submitted for approval version was returned to Draft. Required only for the Return action. |

Submitted, returned, approved, activated and superseded actors and timestamps are audit events, not editable business fields.

### 4.3 StrategyNode

| Field | Operational purpose and system effect |
|---|---|
| `strategy_node_id` | Immutable generated reference used by parent links, lineage and snapshots. |
| `plan_version_id` | Prevents content leaking between plan versions. Required. |
| `node_type` | Selects the hierarchy rule and downstream lineage label. Required. |
| `parent_node_id` | Establishes position. Empty only for a root Pillar. |
| `title` | Carries the approved strategic statement shown in the hierarchy and snapshot. Required. |
| `display_order` | Produces deterministic sibling ordering. Required and unique among siblings. |

Allowed `node_type` values: **Pillar**, **Programme**, **Sub-programme**, **Strategic Objective**. An inapplicable optional layer is omitted; blank placeholder nodes are forbidden.

### 4.4 PerformanceIndicator

| Field | Operational purpose and system effect |
|---|---|
| `indicator_id` | Immutable generated reference used by targets, lineage and snapshots. |
| `plan_version_id` | Binds the indicator to one immutable version. |
| `measures_node_id` | Identifies the Strategic Objective being measured. Required. |
| `name` | Human-readable measure used in review and snapshots. Required. |
| `definition` | Removes ambiguity about what the measure counts. Required and shown during review. |
| `unit` | Defines the target value's unit and prevents incompatible target entry. Required. |

No source, frequency, owner, result, evidence or score is stored in Strategy Alignment.

### 4.5 PerformanceTarget

| Field | Operational purpose and system effect |
|---|---|
| `target_id` | Immutable generated reference used by lineage and snapshots. |
| `indicator_id` | Identifies the measure to which the target applies. Required. |
| `fiscal_year` | Anchors an annual target to an ERPNext `Fiscal Year`. Required for annual targets. |
| `target_by_date` | Anchors a plan-period target when no annual year is used. Required only when `fiscal_year` is empty. |
| `comparison` | `At least`, `At most` or `Equal to`. Required. |
| `target_value` | Expected value in the indicator's inherited unit. Required. |

Exactly one of `fiscal_year` and `target_by_date` shall be present. Unit is inherited and never duplicated on the target.

### 4.6 StrategyAuditEvent

An append-only system event containing event ID, record type and ID, action, actor, the exercised responsibility assignment ID, timestamp, before and after status, reason where required, and correlation ID. Produced by commands and protected reads; users do not edit it.

---

## 5. Lifecycle and business rules

### 5.1 Plan version lifecycle

| Current status | Command | Next status | Authorised actor |
|---|---|---|---|
| Draft | Submit for approval | Submitted for approval | Strategy Author |
| Submitted for approval | Return | Draft | Strategy Approver |
| Submitted for approval | Approve | Active | Strategy Approver |
| Active | Approve successor | Superseded | System, within the successor approval transaction |

Hierarchy, indicator and target records have no separate lifecycle; they inherit the plan version status. The only allowed statuses are **Draft**, **Submitted for approval**, **Active** and **Superseded**. Old role labels and statuses are removed from metadata, services, screens, seeds and tests. They are not aliases.

Governance rules:

- Draft versions are editable only by a Strategy Author.
- Submitted for approval, Active and Superseded versions are read-only.
- Return requires a reason of 10–500 characters and sends the version directly back to Draft.
- The author of a version cannot approve it, even when that user also holds Strategy Approver.
- Approval revalidates readiness, period, completeness and overlap, and activates within one transaction.
- Approving a successor activates it and supersedes the previous Active version of the same plan atomically.
- Approval is permitted only when the version can become effective immediately. MVP 1 has no scheduled-activation state.
- Records are never deleted after first submission.

### 5.2 Business rules

| ID | Rule and enforcement |
|---|---|
| STR-BR-001 | Every Strategy write requires an Active site-wide `User Responsibility Assignment` for the required business role, resolved server-side. There is no PE or organisation-unit scope check, because none exists. |
| STR-BR-002 | A Primary plan shall not have a parent plan. |
| STR-BR-003 | A Supporting Framework shall name one Active or governed Primary plan. |
| STR-BR-004 | Two Primary plans shall not be Active for overlapping dates. Enforced by a database-level partial unique index or equivalent guard **and** in the approval transaction. A read-then-write check alone is insufficient. |
| STR-BR-005 | A plan period shall have `period_start < period_end`; every version effective date shall fall within that period. |
| STR-BR-006 | Active content is immutable. A correction requires a successor version whose `based_on_plan_version_id` identifies the Active version of the same plan. |
| STR-BR-007 | Allowed hierarchy is Pillar → Programme → optional Sub-programme → Strategic Objective. A Programme may parent an Objective when Sub-programme is omitted. |
| STR-BR-008 | A Performance Indicator shall measure one Strategic Objective from the same version and appear as its direct child in the authoring and review tree. |
| STR-BR-009 | An indicator name shall be unique under its measured node within one version. |
| STR-BR-010 | A target shall use exactly one ERPNext Fiscal Year or one target-by date, falling within the plan period. |
| STR-BR-011 | `target_value` shall be compatible with the indicator unit; Percentage values shall be between 0 and 100 inclusive. |
| STR-BR-012 | Submission requires complete plan identity, a valid hierarchy, at least one Strategic Objective, one Indicator and one Target. |
| STR-BR-013 | Only Strategic Objectives in an Active plan version are available for new Procurement Plan Item selection. |
| STR-BR-014 | The selected Strategic Objective shall belong to the resolved Active plan version. |
| STR-BR-015 | Approval repeats all readiness and overlap checks and activates atomically; a stale client result cannot bypass server validation. |
| STR-BR-016 | Ordinary users never enter or modify generated identifiers. |
| STR-BR-017 | Zero matching Active Primary plans returns `STRATEGY_CONTEXT_NOT_FOUND`; more than one returns `STRATEGY_CONTEXT_AMBIGUOUS`. Neither case chooses a record by preference or order. |
| STR-BR-018 | Downstream services return only authorised, Active data and never expose Draft or live workflow content. |
| STR-BR-019 | Downstream modules cannot update a Strategy record through a read or snapshot contract. |
| STR-BR-020 | Direct reads of Strategy database tables by downstream applications are prohibited. |

---

## 6. Roles and permissions

Two Strategy workflow responsibilities exist. Both are registered in the AUTH-ADR-001 v1.6 §4.4 business-role registry with `scope_type = Site-wide`.

| Business role | Scope type | Permitted actions |
|---|---|---|
| Strategy Author | Site-wide | Create plans and successor versions; edit Draft content; submit for approval. |
| Strategy Approver | Site-wide | Inspect a submitted version; return it with a reason, or approve and activate it. |

Registry properties: neither role is an `exclusive_office`; both are granted by Administrator or System Manager; both carry an `sod_tags` entry sufficient for the no-self-approval rule, which is evaluated against the version's audit history rather than a role comparison.

Read access is not a third Strategy workflow role. It is produced by the registered permission hooks in AUTH-ADR-001 v1.6 §5.3 acting on the actor's assignments. Budget and Procurement Planning users consume only the approved read contracts their modules require. **Auditor** is a registered business role under AUTH-ADR-001 v1.6 §4.4, not a bare Frappe role, and confers no Strategy workflow action.

Administrator and System Manager receive full technical read under AUTH-ADR-001 v1.6 §8 and no Strategy business action. No capability profile, operational scope assignment, plan-role grant, effective-date grant, Frappe User Permission or parallel permission store participates in a Strategy authorization path.

---

## 7. Downstream context and lineage

Resolution input is:

- exactly one of `as_of_date` or `fiscal_year`; and
- `include_supporting` — optional, default `false`.

Resolution order is:

1. identify Active Primary plan versions whose plan and version periods cover the requested date;
2. reject zero or multiple applicable Primary results per STR-BR-017;
3. return the Primary version; and
4. when requested, return explicitly linked Supporting Frameworks in deterministic title order.

There is no scope validation step and no preference rule. The resolved result contains only IDs, titles, role, period, version, status and the hierarchy summary a consumer requires. It contains no authoring or audit internals.

For a Procurement Plan Item, Strategy Alignment supplies one direct selection path: Procurement Planning resolves the applicable Active plan version; lists Strategic Objectives from that version; the planner selects exactly one Objective; the Draft Plan Item stores the Objective ID; and approval of the Procurement Plan Version creates an immutable snapshot of the plan, version, ancestor path and selected Objective. Indicators and Targets remain visible below the Objective but are not alternative selection objects.

---

## 8. Service and command contracts

All services are server-authorised, typed and versioned. They do not mutate Strategy content.

| Contract | Required input | Output and effect |
|---|---|---|
| `resolve_strategy_context` | Date or Fiscal Year; include-supporting flag | One applicable Active Primary version and optional Supporting Framework summaries; typed zero and ambiguous errors. |
| `list_strategy_objectives` | Resolved plan version ID; optional Programme or Sub-programme filter, search text and paging | Active Strategic Objectives with generated ID, title and full ancestor path; no Draft records. |
| `get_strategy_lineage` | One authorised Strategic Objective, Indicator or Target ID | Ordered path with stable IDs, types and titles from plan to the requested record. |
| `create_strategy_snapshot` | Consumer module, record ID and version, Strategic Objective ID, expected consumer status, approval correlation ID | Validates eligibility and returns a deterministic snapshot containing plan and version identity and period plus the ordered Pillar, Programme, optional Sub-programme and Strategic Objective IDs and titles. Records the snapshot audit event; does not write the consumer's record. Repeating the same correlation returns the same payload. |

| Command | Purpose |
|---|---|
| `save_strategy_plan_draft` | Create or update plan identity and Draft version metadata with optimistic concurrency. |
| `create_strategy_successor_version` | Copy one Active version into a new Draft of the same plan and set the immutable comparison baseline. |
| `save_strategy_structure_draft` | Create, update, reorder or remove Draft nodes, indicators and targets as one validated change set. |
| `submit_strategy_version` | Validate readiness and move Draft to Submitted for approval. |
| `return_strategy_version` | Require a correction reason and return Submitted for approval to Draft. |
| `approve_strategy_version` | Revalidate responsibility, readiness, effective date and overlap; activate the submitted version and atomically supersede the previous Active version where applicable. |

`record_verified_result` is reserved for a later Contract Management change unit. Strategy Alignment provides no result-entry field, screen or production write endpoint.

Every write command requires the expected record version. Concurrency and idempotency rules are in KT-STD-001 §11.

---

## 9. Error contract

| Code | Message intent and effect |
|---|---|
| `STRATEGY_RESPONSIBILITY_REQUIRED` | You are not assigned the responsibility required for this action. No record is created or changed. |
| `STRATEGY_CONFIG_MISSING` | A referenced financial year is missing or unavailable. The operation fails closed. |
| `STRATEGY_INVALID_STATE` | The command is not valid for the current server status. Current status is returned. |
| `STRATEGY_NOT_READY` | Submission or approval readiness failed. Structured failing rule IDs are returned. |
| `STRATEGY_INVALID_HIERARCHY` | A node type, parent relationship, duplicate sibling or cross-version link is invalid. |
| `STRATEGY_INVALID_TARGET` | Target period, comparison or value is invalid for the indicator and plan. |
| `STRATEGY_OVERLAP` | Approval would create overlapping Active Primary authority. No status changes occur. |
| `STRATEGY_CONTEXT_NOT_FOUND` | No applicable Active Primary plan exists for the requested date or financial year. |
| `STRATEGY_CONTEXT_AMBIGUOUS` | More than one equally applicable Active Primary plan exists. No record is selected. |
| `STRATEGY_OBJECTIVE_NOT_ELIGIBLE` | The selected objective is missing, outside the resolved version, or not in an Active plan version. No link or snapshot is produced. |
| `STRATEGY_STALE_WRITE` | The expected record version is stale. No newer changes are overwritten. |
| `STRATEGY_DOWNSTREAM_FORBIDDEN` | A downstream caller attempted an unsupported read, Draft access or mutation. |

`STRATEGY_SCOPE_REQUIRED` and `STRATEGY_PERMISSION_DENIED` are removed: the first named a scope that no longer exists, the second named User Permission. Message conventions are in KT-STD-001 §11.

---

## 10. UI architecture and routes

Strategy Alignment remains a top-level KenTender module named **Strategy Alignment**. The module menu contains only **Strategy Portfolio** and **Approval tasks**, the latter visible only to a Strategy Approver. Do not retain navigation for PVOs, treatments, corrective actions or performance management.

| Screen | Canonical route | Purpose |
|---|---|---|
| STR-UI-01 Strategy Portfolio | `/app/strategy` | Plan register and entry point for authoring or neutral viewing. |
| STR-UI-02 Plan workspace | `/app/strategy/plan/{plan_id}` | Plan identity, version summary and version navigation. |
| STR-UI-03 Structure editor | `/app/strategy/plan/{plan_id}/version/{version_number}/structure` | Draft hierarchy, indicators and targets. |
| STR-UI-04 Approval task | `/app/strategy/approval/{plan_version_id}` | Read-only submitted-version review and decision surface. |

The plan workspace uses persistent **Overview**, **Structure** and **History** tabs, with the active tab represented in the URL. The proven Strategy Portfolio visual language and Vue-in-Frappe page pattern are reused. This document authorises no second dashboard, application shell or replacement Frappe header.

---

## 11. Static Claude Design contract

Supply **KT-STD-001 §2 plus this section** to Claude Design. Nothing else. The closed-input rules, product-wide prohibitions, approved desktop shell, page-header pattern and division of supply are in KT-STD-001 §2.2–2.5 and are not repeated here. Fixture actors and financial years come from KT-STD-001 §8, extended by §14.1 below.

**Additional prohibitions for this document:** do not show performance figures, targets achieved, risk, corrective actions, approval counts, charts, source references, evidence, attachments, contacts, descriptions, notes, baselines, tolerances, treatments, actual results or performance scores. Do not show an Organisation scope control, a PE row or any scope selector — Strategy is site-wide and there is nothing to choose.

### 11.1 STR-DES-01 — Strategy Portfolio

**Fixture context — outside the artboard:** Esther Muthoni · `esther.muthoni@moh.example.test` · Strategy Author · 24 Nov 2026, 11:30 EAT · Frappe header breadcrumb: **Home > Strategy Alignment**

**Page content header**

- Eyebrow: **STRATEGY ALIGNMENT**
- Title: **Strategy Portfolio**
- Description: **Maintain the approved strategy structure used by Budget and Procurement Planning.**
- Right-aligned primary button: **New strategic plan**

There is no context strip on this artboard.

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

### 11.2 STR-DES-02 — New strategic plan draft

**Fixture context — outside the artboard:** Esther Muthoni · `esther.muthoni@moh.example.test` · Strategy Author · 24 Nov 2026, 11:30 EAT · Frappe header breadcrumb: **Home > Strategy Alignment > New strategic plan**

**Page content header**

- Title: **New strategic plan**
- Status: **Draft**

**Plan identity card**

| Field label | Displayed value |
|---|---|
| Plan reference | Not assigned |
| Plan title | Ministry of Health Strategic Plan 2028–2032 (Demo) |
| Plan role | Primary |
| Plan period start | 1 Jul 2028 |
| Plan period end | 30 Jun 2033 |

Plan reference uses the approved read-only field component. Plan role uses the approved select component. Plan title and the two Plan period rows use the approved input or date component appropriate to their displayed value.

**Fixed footer, left to right:** **Cancel**, **Save draft**. **Save draft** is the primary button.

Do not show structure fields, approval history, readiness checks or a submit action on this artboard.

### 11.3 STR-DES-03 — Active plan overview

**Fixture context — outside the artboard:** Naomi Chebet · `naomi.chebet@moh.example.test` · Auditor · 24 Nov 2026, 11:30 EAT · Frappe header breadcrumb: **Home > Strategy Alignment > STR-MOH-2023-001**

**Page content header**

- Eyebrow: **STR-MOH-2023-001**
- Title: **Ministry of Health Strategic Plan (Demo)**
- Status: **Active**
- No header action button

**Tabs:** **Overview** selected, **Structure**, **History**

**Plan identity card**

| Label | Value |
|---|---|
| Plan role | Primary |
| Plan period | 1 Jul 2023 – 30 Jun 2028 |
| Active version | Version 1 |
| Version effective period | 1 Jul 2023 – 30 Jun 2028 |

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
| Approved and activated by | Dr Alfred Ochieng |
| Approved and activated | 1 Jul 2023, 09:15 EAT |

Do not show edit controls, performance results, evidence, corrective action or downstream transaction counts.

### 11.4 STR-DES-04 — Draft structure editor

**Fixture context — outside the artboard:** Esther Muthoni · `esther.muthoni@moh.example.test` · Strategy Author · 24 Nov 2026, 11:30 EAT · Frappe header breadcrumb: **Home > Strategy Alignment > STR-MOH-2023-001 > Version 2 > Structure**

**Page content header**

- Eyebrow: **STR-MOH-2023-001 · VERSION 2**
- Title: **Strategy structure**
- Status: **Draft**
- Right-aligned secondary button: **Save draft**
- Right-aligned primary button: **Submit for approval**

**Tabs:** **Overview**, **Structure** selected, **History**

Below the tabs, a two-column working surface: 42% width for the hierarchy tree, 58% for the selected-record card.

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

Exact compact trailing actions:

| Displayed row type | Trailing action |
|---|---|
| Pillar | Add programme |
| Programme | Add sub-programme |
| Sub-programme | Add objective |
| Strategic Objective | Add indicator |
| Performance Indicator | Add target |
| Performance Target | None |

Do not show **Add outcome** or the generic label **Add child**. The selected row uses the approved selected background and border.

**Selected record card**

- Heading: **Strategic Objective**
- Subtext: **Pillar / Programme / Sub-programme / Strategic Objective**

| Field label | Displayed value |
|---|---|
| Title | Strengthen interoperable national digital health services |
| Display order | 1 |

Card footer buttons, left to right: **Delete node**, **Save changes**. **Delete node** uses the danger-outline style; **Save changes** is primary.

Do not show an editable node code, description, owner, evidence, status or approval field.

### 11.5 STR-DES-05 — Indicator and target editor

**Fixture context — outside the artboard:** Esther Muthoni · `esther.muthoni@moh.example.test` · Strategy Author · 24 Nov 2026, 11:30 EAT · Frappe header breadcrumb: **Home > Strategy Alignment > STR-MOH-2023-001 > Version 2 > Structure**

Duplicate the completed STR-DES-04 artboard. Keep the hierarchy tree unchanged except select the Performance Indicator row. Replace the selected-record card with the following.

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

One additional static artboard over the dimmed Indicator editor.

- Title: **Add performance target**
- Intro text: **Set the expected value and period for this indicator.**
- Field label: **Period** · Displayed choice: **FY 2027/28**
- Field label: **Expected result** · Two controls on one row: comparison choice **At least** and numeric value **85**
- Read-only suffix beside the numeric value: **Percentage**
- Footer buttons: **Cancel** and **Add target**

Do not show target name, description, owner, baseline, tolerance, actual result, evidence, status or another unit control.

### 11.6 STR-DES-06 — Approval task · Overview

**Fixture context — outside the artboard:** Dr Alfred Ochieng · `alfred.ochieng@moh.example.test` · Strategy Approver · 25 Nov 2026, 10:15 EAT · Frappe header breadcrumb: **Home > Strategy Alignment > Approval tasks > STR-MOH-2023-001-V2**

**Page content header**

- Eyebrow: **STR-MOH-2023-001 · VERSION 2**
- Title: **Approve strategic plan version**
- Status: **Submitted for approval**
- No header action button

**Tabs:** **Overview** selected, **Structure**, **Changes**, **History**

**Plan identity card**

| Label | Value |
|---|---|
| Strategic plan | Ministry of Health Strategic Plan (Demo) |
| Plan role | Primary |
| Plan period | 1 Jul 2023 – 30 Jun 2028 |
| Submitted version | Version 2 |
| Version effective period | 1 Jul 2027 – 30 Jun 2028 |

**Submission authority card**

| Label | Value |
|---|---|
| Submitted by | Esther Muthoni |
| Submitted | 24 Nov 2026, 16:20 EAT |

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

**Fixed footer, left to right:** **Return**, **Approve**. **Return** uses the danger-outline style; **Approve** is primary.

Do not show editable fields, comments, attachments, evidence, performance results or Active Version 1 data on this artboard.

### 11.7 STR-DES-07 — Approval task · Structure

**Fixture context — outside the artboard:** Dr Alfred Ochieng · `alfred.ochieng@moh.example.test` · Strategy Approver · 25 Nov 2026, 10:15 EAT · Frappe header breadcrumb: **Home > Strategy Alignment > Approval tasks > STR-MOH-2023-001-V2**

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

### 11.8 STR-DES-08 — Approval task · Changes

**Fixture context — outside the artboard:** Dr Alfred Ochieng · `alfred.ochieng@moh.example.test` · Strategy Approver · 25 Nov 2026, 10:15 EAT · Frappe header breadcrumb: **Home > Strategy Alignment > Approval tasks > STR-MOH-2023-001-V2**

Reuse the STR-DES-06 page content header and fixed footer without changing their content or placement.

**Tabs:** **Overview**, **Structure**, **Changes** selected, **History**

**Change comparison card**

- Heading: **Changes from Active Version 1**

| Changed item | Active Version 1 | Submitted Version 2 |
|---|---|---|
| FY 2027/28 performance target | At least 80% | At least 85% |

Text below the table: **No other plan identity or structure items changed.**

Do not show unchanged rows, inline editing, accept or reject controls, comments or a side-by-side document viewer.

### 11.9 STR-DES-09 — Approval task · History

**Fixture context — outside the artboard:** Dr Alfred Ochieng · `alfred.ochieng@moh.example.test` · Strategy Approver · 25 Nov 2026, 10:15 EAT · Frappe header breadcrumb: **Home > Strategy Alignment > Approval tasks > STR-MOH-2023-001-V2**

Reuse the STR-DES-06 page content header and fixed footer without changing their content or placement.

**Tabs:** **Overview**, **Structure**, **Changes**, **History** selected

**Version history card**

| Date and time | Event | Actor |
|---|---|---|
| 24 Nov 2026, 16:20 EAT | Submitted for approval | Esther Muthoni |
| 24 Nov 2026, 15:55 EAT | Draft saved | Esther Muthoni |
| 24 Nov 2026, 13:10 EAT | Successor Version 2 created | Esther Muthoni |

Do not show comments, attachments, evidence, technical request logs or events from another plan version.

### 11.10 STR-DES-10 — Portfolio state variants

Four static variants. Every variant contains the STR-DES-01 page content header, tabs and standard filter row. Do not show summary cards or plan rows. State treatments follow KT-STD-001 §3.

Fixture context for Loading, No matches and Server error — outside the artboard: **Esther Muthoni · `esther.muthoni@moh.example.test` · Strategy Author · 24 Nov 2026, 11:30 EAT**. Fixture context for Forbidden — outside the artboard: **Samuel Otieno · `samuel.otieno@moh.example.test` · No Strategy responsibility · 24 Nov 2026, 11:30 EAT**. Frappe header breadcrumb for all variants: **Home > Strategy Alignment**.

| Variant | Filter row | Main content | Buttons |
|---|---|---|---|
| Loading | Search, plan-role and status controls disabled | Five full-width skeleton table rows | None |
| No matches | Search value **County strategy**; selects show **All plan roles** and **All statuses** | Heading **No plans match these filters.** Body **Change or clear the filters to see other strategic plans.** | **Clear filters** |
| Forbidden | No filter row | Heading **You do not have access to Strategy Alignment.** Body **This area needs one of these responsibilities: Strategy Author, Strategy Approver or Auditor. Ask your KenTender administrator to assign one in System setup.** | None |
| Server error | Standard empty filter row | Heading **Strategy plans could not be loaded.** Body **Try again. If the problem continues, contact KenTender support.** | **Try again** |

### 11.11 Existing controls

No artboard is authorised for the Frappe header, breadcrumb, module menu, global page chrome, notifications or user menu. Reuse those without visual modification, per KT-STD-001 §2.5. The Procurement Planning Strategic Objective selector belongs to the Procurement Planning UI contract and is not designed here.

---

## 12. Functional interaction requirements — excluded from design prompts

Common page behaviour and accessibility follow KT-STD-001 §3.

### 12.1 STR-UI-01 — Strategy Portfolio

- The server returns plans through the registered permission hooks. No PE context is resolved, selected or inferred.
- **Plans** shows all records the actor may view. **My work** shows only live records on which the actor may perform the next command.
- Search matches plan reference and title. Plan role and status filters are server-side.
- Counts use the same predicate as rows.
- **New strategic plan** appears only for a Strategy Author.
- **View**, **Continue draft** and **Approve** follow the server-returned `available_action`; the browser never derives authority from status alone.
- Browser back and forward restore filters, tab and selected record.

### 12.2 STR-UI-02 — Plan workspace

- A saved new-plan draft receives its generated plan and version references from the server.
- The first version effective period equals the plan period; the user does not enter the same dates twice.
- Plan identity is editable only while its first version is Draft and before downstream use exists.
- A Primary plan hides `parent_primary_plan_id`; a Supporting Framework requires selection of an eligible Primary plan.
- Submitted for approval, Active and Superseded versions always open read-only.
- **Create successor version** is offered only to a Strategy Author on an Active plan and creates a server-side copy of the current version.
- History is chronological and append-only, showing lifecycle events, actor, timestamp and required return reason.

### 12.3 STR-UI-03 — Structure editor

- The server returns the full Draft tree with stable IDs and one expected version token.
- Add-child choices are limited by STR-BR-007 and returned by the server.
- Reorder updates only sibling `display_order` values and saves as one atomic command.
- A node with descendants cannot be removed until its descendants are removed or explicitly moved in the same validated command.
- An indicator attaches only to a Strategic Objective and displays directly beneath it.
- **Add indicator** is available only on a Strategic Objective; **Add target** only on a Performance Indicator. No Outcome command or record is permitted.
- A target copies no unit field; its displayed unit resolves from the indicator and is never submitted as an independent value.
- **Add target** opens the exact dialog in STR-DES-05. **Edit** opens the same dialog with the current period, comparison and value.
- Period offers only ERPNext Fiscal Years overlapping the plan period, obtained through `GetSiteConfiguration()` or the equivalent projection, plus one plan-period date option when applicable.
- One Indicator cannot contain two Targets for the same Fiscal Year or the same target-by date.
- Saving a stale tree returns `STRATEGY_STALE_WRITE` and preserves unsaved values for deliberate reload or reconciliation.
- **Submit for approval** calls readiness validation. On failure the page shows an error summary and focuses the first failing record without changing status.

### 12.4 STR-UI-04 — Approval task

- Direct task routes require an Active Strategy Approver assignment. A read-only user is denied rather than shown a disabled workflow form.
- The route binds to one `plan_version_id`. Overview, Structure, Changes and History always read that submitted version and never fall back to the current Active version.
- The selected tab is represented in the URL. Browser back and forward restore the prior tab without changing the version or mounting a second page application.
- Overview returns plan identity, submission authority, readiness and structure counts from the submitted version.
- Structure returns the complete read-only submitted hierarchy including Indicators and Targets.
- Changes is calculated server-side between `based_on_plan_version_id` and the submitted version. The client never constructs or infers the comparison.
- History returns only lifecycle and draft-save events for the submitted version, in reverse chronological order.
- The decision footer remains available on every tab; every command carries the submitted version ID, expected status and expected record version.
- Return and Approve are available only while status is Submitted for approval.
- Return opens a dialog containing only **Return reason**, **Cancel** and **Return**. The reason is validated server-side.
- Approve reruns readiness, effective-date and overlap guards under a transaction lock. A failed guard leaves the version Submitted for approval.
- Successful approval changes the submitted version to Active and the previous Active version of the same plan to Superseded in one transaction.
- The author of the submitted version cannot approve it, even when that user also holds Strategy Approver.

### 12.5 Additional page states

- Loading never presents a false zero count.
- Empty filtered results provide **Clear filters**.
- No plans at all presents **No strategic plans exist yet.** and shows **New strategic plan** only to a Strategy Author.
- Forbidden states disclose no plan names, counts or task details.
- A server failure retains already displayed stable data and offers **Try again**.

### 12.6 Downstream Strategic Objective selection boundary

- Procurement Planning owns the Plan Item selector and its interaction design.
- Strategy Alignment returns eligible Objective rows only through `list_strategy_objectives`.
- Each row contains Objective ID, title and the ordered Pillar → Programme → optional Sub-programme path so the planner can distinguish similar objectives.
- A Plan Item selects exactly one Strategic Objective. Indicator and Target are read-only associated measures, not alternative selector values.
- The Draft Plan Item stores the Objective ID. Procurement Plan Version approval calls `create_strategy_snapshot` and stores the returned immutable lineage.
- No Value Commitment field, model, service, label or compatibility mapping is permitted in Strategy Alignment or Procurement Planning.

---

## 13. Audit and historical integrity

Append-only events: plan and successor-version creation; Draft structural change sets; submit, return, approve, activate and supersede; responsibility or segregation denial; successful and failed context resolution; Strategic Objective listing and lineage reads by a downstream module; and snapshot creation or idempotent reuse.

Each event records actor, business role, the exercised responsibility assignment ID, record and version IDs, action, timestamp, before and after status, required reason and correlation ID. A downstream contract event also records the calling module. No event records a Procuring Entity or organisation-unit scope, because none participates.

Submitted for approval, Active and Superseded versions are immutable. A Strategy snapshot copied into a downstream approval record does not change when the source plan later changes status. Deleting lifecycle events, renumbering versions and reusing generated references are prohibited.

---

## 14. Seed contract

Site configuration, Organisation Units, base actors and Fiscal Years come from KT-STD-001 §8. Execution rules come from KT-STD-001 §8.6.

### 14.1 Required additions to the shared fixture register

KT-STD-001 §8.3 does not yet contain Strategy actors. These three shall be added there and are used throughout this document:

| Display name | Login identifier | Responsibility | Scope |
|---|---|---|---|
| Esther Muthoni | `esther.muthoni@moh.example.test` | Strategy Author | Site-wide |
| Dr Alfred Ochieng | `alfred.ochieng@moh.example.test` | Strategy Approver | Site-wide |
| Naomi Chebet | `naomi.chebet@moh.example.test` | Auditor | Site-wide |

KT-STD-001 §8.5 shall also gain a Strategy row: **Strategy journeys — 24–25 Nov 2026, between 11:00 and 17:00 EAT.**

Samuel Otieno, already in the register with an expired assignment, serves as the Forbidden fixture actor. No separate unassigned user is created.

### 14.2 Configuration prerequisite

The seed resolves the ERPNext Fiscal Year **2027-2028** and fails with `STRATEGY_CONFIG_MISSING` if it is absent. The Strategy seed creates no Fiscal Year, Organisation Unit or configuration record, and never selects the first available record.

### 14.3 Ministry of Health plan

| Field | Seed value |
|---|---|
| Plan ID | `STR-MOH-2023-001` |
| Title | Ministry of Health Strategic Plan (Demo) |
| Plan role | Primary |
| Period | 1 Jul 2023 – 30 Jun 2028 |
| Version | 1 |
| Version ID | `STR-MOH-2023-001-V1` |
| Version effective period | 1 Jul 2023 – 30 Jun 2028 |
| Status | Active |

Exact lifecycle authority:

| Event | Actor | Date and time |
|---|---|---|
| Submitted for approval | Esther Muthoni | 1 Jul 2023, 08:30 EAT |
| Approved and activated | Dr Alfred Ochieng | 1 Jul 2023, 09:15 EAT |

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

There is no second seeded plan. The v1.5 County Government of Kisumu plan and its actors are removed with the multi-PE model.

### 14.4 Artboard-only workflow fixture

The Version 2 data shown in STR-DES-04 through STR-DES-10 is an isolated test fixture, not part of the default Active seed. Under KT-STD-001 §8.7 it is declared here so a seed-versus-artboard comparison reports no false mismatch.

| Fixture item | Exact value |
|---|---|
| Submitted version ID | `STR-MOH-2023-001-V2` |
| Based on version ID | `STR-MOH-2023-001-V1` |
| Effective period | 1 Jul 2027 – 30 Jun 2028 |
| Only content change | FY 2027/28 target: At least 80% → At least 85% |
| Successor created | 24 Nov 2026, 13:10 EAT · Esther Muthoni |
| Draft saved | 24 Nov 2026, 15:55 EAT · Esther Muthoni |
| Submitted for approval | 24 Nov 2026, 16:20 EAT · Esther Muthoni |

Test setup may place the version in Draft or Submitted for approval for a named artboard or test, and must remove or roll it back afterwards. Approval changes it directly to Active.

### 14.5 Additional seed rules

- Upsert by the exact stable identifiers above; create no duplicates.
- Validate each plan through the same domain rules used by commands.
- Seed lifecycle events use the named responsibility holders, never Administrator.
- Fail loudly on a missing Fiscal Year, invalid hierarchy, invalid target or conflicting Active plan.
- Mark synthetic records visibly as **(Demo)** in plan titles; add no generic disclaimer field.

---

## 15. Acceptance contract

| ID | Acceptance result |
|---|---|
| STR-AC-001 | The module installs and imports without the legacy Demands package or Procurement Home. |
| STR-AC-002 | No executable metadata, route, service, field, label, seed or active test refers to Plan Value Commitment, Strategy Value Commitment, PVO, Strategic Outcome, treatment or Strategy Corrective Action. |
| STR-AC-003 | A Strategy Author can create a Draft plan and receives generated plan and version references. |
| STR-AC-004 | A user without an Active Strategy assignment — including Administrator and System Manager — cannot create, submit, return or approve. |
| STR-AC-005 | A Draft can represent Pillar → Programme → optional Sub-programme → Objective, with Indicator directly beneath Objective and Target directly beneath Indicator. |
| STR-AC-006 | Strategic Objective and Performance Indicator are distinct types and cannot be substituted for one another; no Strategic Outcome type exists. |
| STR-AC-007 | Target validation enforces period choice, comparison, unit-compatible value and percentage range. |
| STR-AC-008 | Readiness blocks submission when plan identity or hierarchy is invalid, or when the version has no Strategic Objective, Indicator or Target. |
| STR-AC-009 | A Procurement Plan Item can select exactly one Strategic Objective from its resolved Active plan version and cannot select an Indicator or Target instead. |
| STR-AC-010 | Only Strategy Author and Strategy Approver are Strategy workflow responsibilities; the author of a version cannot approve that version. |
| STR-AC-011 | Return requires a reason and preserves the complete workflow history. |
| STR-AC-012 | Submitted for approval, Active and Superseded content cannot be edited; an Active correction requires a successor version. |
| STR-AC-013 | Concurrent approval cannot create overlapping Active Primary authority, and the guard holds when the command layer is bypassed. |
| STR-AC-014 | Approving a successor atomically activates it and supersedes the previous Active version of the same plan. |
| STR-AC-015 | Zero and multiple context matches return typed errors and never select a record by preference or order. |
| STR-AC-016 | `resolve_strategy_context` returns the correct Active Primary version for a supplied date or Fiscal Year, and requires no Procuring Entity or organisation-unit input. |
| STR-AC-017 | `list_strategy_objectives` returns only Active Strategic Objectives with exact generated IDs and ordered ancestor paths. |
| STR-AC-018 | `get_strategy_lineage` returns exact stable IDs, types and titles in plan-to-record order. |
| STR-AC-019 | `create_strategy_snapshot` captures the selected Strategic Objective and its exact plan-to-objective lineage, and is immutable and idempotent for one downstream approval correlation ID. |
| STR-AC-020 | Downstream direct-table mutation and Draft reads are rejected. |
| STR-AC-021 | A user with read access can open an Active plan but cannot open an approval task without an Active Strategy Approver assignment. |
| STR-AC-022 | Portfolio counts, rows, routes, exports, reports and APIs apply the same server-side predicate, and a plan hidden from the register is unreachable by direct route. |
| STR-AC-023 | The default seed is deterministic and an immediate second run produces no change. |
| STR-AC-024 | A missing ERPNext Fiscal Year fails seed execution without creating a fallback record. |
| STR-AC-025 | The four primary screen routes render without console error and match their approved static designs. |
| STR-AC-026 | Loading, no-match, forbidden and server-error states disclose no false or unauthorised data. |
| STR-AC-027 | The Frappe header and breadcrumb are reused and not duplicated inside the Vue page; no PE, scope or context selector appears on any Strategy screen. |
| STR-AC-028 | No Strategy page or API accepts Value Commitment, source-reference, evidence, attachment, contact, baseline, treatment, actual-result or corrective-action data. |
| STR-AC-029 | Strategy Approver can inspect Overview, Structure, Changes and History for the exact submitted version, and no tab substitutes current Active-version content. |
| STR-AC-030 | Return and Approve remain available on every approval tab and reject a stale version or status. |
| STR-AC-031 | No executable Strategy metadata, permission, route, service, seed or active test refers to Strategy Reviewer, Strategy Approval Authority, Strategy Viewer as a workflow role, or the removed lifecycle statuses. |
| STR-AC-032 | Every Strategy write is authorised through an Active `User Responsibility Assignment` resolved by the registered permission hooks. No Frappe User Permission, capability profile, operational scope assignment or parallel permission lookup participates in any Strategy authorization path. |
| STR-AC-033 | No `procuring_entity`, `procuring_entity_id`, `owner_org_unit_id` or KenTender `FinancialYear` reference exists in Strategy schema, services, seeds, fixtures or tests. |
| STR-AC-034 | Strategy Author and Strategy Approver appear in the business-role registry with `scope_type = Site-wide`, and no Strategy command performs an organisation-unit scope check. |

### 15.1 Minimum rule coverage

| Rule group | Required automated coverage |
|---|---|
| Responsibility and access | STR-BR-001, STR-AC-003–004, STR-AC-010, STR-AC-021–022, STR-AC-031–034 |
| Domain structure | STR-BR-005–012, STR-AC-005–009, STR-AC-012 |
| Lifecycle and approval | STR-BR-004, STR-BR-006, STR-BR-015–017, STR-AC-010–015 |
| Downstream Objective and contracts | STR-BR-013–014, STR-BR-018–020, STR-AC-009, STR-AC-016–020 |
| Seeds | STR-AC-023–024 |
| UI | STR-AC-025–030 |
| STR-AC-035 | Every page resolves its authorisation verdict before rendering; a denied actor sees the inline Forbidden panel with no header, filter, content or empty state painted, and no permission modal appears on page load. |
| STR-AC-036 | The Forbidden panel names the responsibilities that open the surface and directs the user to a KenTender administrator; it names no line manager or supervisor. |
| STR-AC-037 | Selecting this module without access pushes its own route, highlights it in navigation, and lands on its Forbidden state; the module is never hidden and route and view never diverge. |

---

## 16. Implementation and test constraints

The implementation baseline is KT-STD-001 §4; the verification protocol is KT-STD-001 §5; release evidence is KT-STD-001 §6.

### 16.1 Additional implementation rules

- Drop `procuring_entity_id` and `owner_org_unit_id` from `StrategicPlan`, together with every service parameter, filter, index, fixture, label and test that references them.
- Rename `financial_year_id` to `fiscal_year` and repoint it at the ERPNext `Fiscal Year`. Remove every reference to a KenTender `FinancialYear` DocType.
- Register Strategy Author and Strategy Approver in the AUTH-ADR-001 v1.6 business-role registry with `scope_type = Site-wide`. Remove Strategy capability strings, custom assignment lookups and every User Permission read from Strategy writes. The no-self-approval check reads the version's audit history.
- Register Strategy DocTypes in `kentender_scope_map` per AUTH-ADR-001 v1.6 §5.3. Because both roles are site-wide, the registered predicate reduces to an assignment existence check; it is still registered through both hooks so direct-route access is covered.
- Enforce STR-BR-004 with a database-level partial unique index or equivalent guard in addition to the approval-transaction check.
- Normalize legacy statuses once: Draft and Returned → Draft; In Review, Awaiting Approval and Approved → Submitted for approval; Active → Active; Superseded and Archived → Superseded. Do not activate an old Approved version automatically.
- Existing Strategy Approval Authority holders may receive a Strategy Approver assignment during the controlled migration. Strategy Reviewer holders are not promoted automatically. Remove old roles once all permissions, fixtures and tests use the two-role model.
- Delete the Plan and Strategy Value Commitment DocTypes, child-link table, services, routes, page fixtures, seeds and tests. Preserve no alias or compatibility response field.
- Remove `Strategic Outcome` from node metadata, services, commands, fixtures, screens and tests. During cleanup an Indicator attached to an Outcome is reattached to that Outcome's direct parent Strategic Objective, then the Outcome is removed. Cleanup fails loudly if the parent is not exactly one Strategic Objective or if the link crosses a plan version; it never guesses.
- Replace downstream Strategy-contract imports and Budget and Planning test fixtures with `list_strategy_objectives`, `get_strategy_lineage` and the Objective-based `create_strategy_snapshot` shape in §8.
- Reuse the proven Vue 3 single-file-component pattern mounted into one `frappe.ui.make_app_page()` Desk page. Reuse the approved Strategy design tokens and scoped component styles.

### 16.2 Additional minimum coverage

1. Strategy write attempted with no assignment, with an expired assignment and with a Scheduled assignment.
2. Administrator and System Manager technical read succeeds; business mutation is denied.
3. Direct-route access to a plan excluded from the actor's register.
4. Report and export scoping proving the shared match conditions are applied.
5. Concurrent approval of two overlapping Primary plans, including a command-layer bypass to prove the database guard holds.
6. Successor approval atomicity: activate and supersede in one transaction, with rollback on failure.
7. No-self-approval enforced from audit history when the same user holds both responsibilities.
8. Context resolution at period boundaries, for zero matches and for multiple matches.
9. Target period restricted to Fiscal Years overlapping the plan period.
10. Snapshot idempotency for one downstream approval correlation ID.
11. Repository scan proving `procuring_entity`, `owner_org_unit_id`, `FinancialYear`, `STRATEGY_SCOPE_REQUIRED` and `STRATEGY_PERMISSION_DENIED` are absent.
12. Browser journeys: Strategy Author opens Portfolio → creates and saves a Draft → edits structure → submits; Strategy Approver inspects Overview, Structure, Changes and History → returns once → approves the corrected submission; a read-only user opens an Active plan and sees no workflow action; an actor with no Strategy assignment sees the Forbidden state with no data disclosure.

### 16.3 Additional release evidence

- Static scan showing no removed concept and no legacy Demands import in executable Strategy code.
- Schema and metadata migration succeeds; deterministic seed succeeds twice.
- Budget and Procurement Planning contract consumer tests pass.
- AUTH contract suite passes, proving no Strategy path reintroduces a User Permission read.

---

## 17. Prohibited shortcuts

The universal list is KT-STD-001 §2.3 and §10. Additionally, for this document:

- No PVO, treatment, corrective-action or performance-result concept under a new label.
- No alias DocType, compatibility service, dual read, shadow write or silent fallback for a removed record.
- No reintroduction of `procuring_entity_id` or `owner_org_unit_id`, including "for reporting" or "for a future county deployment".
- No organisation-unit scope check, scope selector or scope column in any Strategy command, service or screen.
- No first-plan, first-year or Administrator fallback.
- No preference rule that resolves an ambiguous context instead of rejecting it.
- No downstream raw SQL or ORM read of Strategy tables.
- No mutation of Submitted for approval, Active or Superseded content.
- No duplicate of the Strategic Objective under another label.
- No arbitrary JSON field used to avoid the canonical hierarchy or the direct Strategic Objective reference.
- No optional source, evidence, attachment, contact, description, note, baseline or owner field "for future use".
- No editable generated reference.

---

## 18. Traceability and precedence

1. **KT-STD-001 v1.2** for document structure, design closed-input rules, the artboard shell, the shared fixture register, common page behaviour, the verification protocol, release evidence, seed conventions, universal prohibitions and error-contract conventions.
2. **AUTH-ADR-001 v1.6** for business authority, the role registry, responsibility assignment, the shared resolver and the registered permission hooks.
3. **CFG-CHG-002 v0.6** for the site Procuring Entity, the ERPNext Fiscal Year surface and Organisation Unit records.
4. **This document** for strategic plans, versions, hierarchy, indicators, targets, their lifecycle and their read contracts.
5. **Procurement Planning** for the Plan Item selector and its interaction design.

This document reconciles and supersedes conflicting Strategy requirements in `04_Strategy_Alignment_MVP1_Requirements.md`, `02_Strategy_Cleanup_Plan.md`, and STR-CHG-001 v1.0 through v1.5. Where an earlier item is not retained here, it is outside Strategy Alignment scope.

Documents requiring a matching correction:

| Document | Required correction |
|---|---|
| KT-STD-001 | Add the three Strategy actors in §14.1 to §8.3, and the Strategy fixture instant to §8.5. |
| PLN-CHG-001 | Strategic Objective selection consumes `list_strategy_objectives` and `create_strategy_snapshot` with no PE or organisation-unit argument. |
| BUD-CHG-001 | Strategy node and target references carry no PE or organisation-unit scope. |

---

## 19. Approval effect

Approved 3 September 2026. STR-CHG-001 v1.6 supersedes v1.5 and all earlier versions in full and is the only Strategy Alignment document to consult.

This approval authorises: removal of `procuring_entity_id` and `owner_org_unit_id`; registration of Strategy Author and Strategy Approver as site-wide business roles resolved through the AUTH-ADR-001 v1.6 permission hooks; adoption of the ERPNext `Fiscal Year`; removal of the County Government of Kisumu seed plan, its three fixture actors and every cross-PE isolation test; adoption of the KT-STD-001 shared fixture register and its 2026 timeline; the corrected artboards in §11; and the acceptance contract in §15.

Implementers shall not retain v1.5's PE or organisation-unit scope fields, its User Permission authorization path, its `STRATEGY_SCOPE_REQUIRED` or `STRATEGY_PERMISSION_DENIED` error codes, its second Procuring Entity seed, or any PE row or scope control on a Strategy screen.
