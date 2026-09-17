# STR-CHG-001 — Clean Strategy Alignment

| Control | Value |
|---|---|
| Document ID | STR-CHG-001 |
| Version | 1.8 |
| Date | 13 September 2026 |
| Status | **Consolidated approved requirements** |
| Approval basis | Approved v1.7 baseline and Project Owner approval of STR Usability Amendment v0.1, STR-UX-001–012, on 13 September 2026, with direction to incorporate into the full document. |
| Supersedes | v1.7 and earlier Strategy implementation specifications in full. |
| Change type | Complete successor: approved usability changes integrated across actors, screen contracts, commands, lifecycle presentation, fixtures and verification; 61 acceptance criteria and a 12-row full v1.8 change register. |
| Module | Strategy Alignment |
| Standards | Inspected KT-STD-001 v1.4, AUTH-ADR-001 v1.7 and approved CFG-CHG-002 v0.10; owner boundaries and remaining evidence in §18. |
| Implementation posture | Correction in place; no compatibility layer, extra approval stage or performance-management workflow. |

**Controlling decision:** Strategy Alignment is a small upstream governance module. It maintains approved strategy structures for the one Procuring Entity this site represents, and exposes them through read-only contracts. Strategy responsibilities are **site-wide**: there is no per-plan organisational scope. It does not become a performance-management, treatment, corrective-action or procurement-workflow module.

---

## 1. Governing decision

This document is the single implementation authority for Strategy Alignment. The existing `kentender_strategy` application is corrected in place. Apply the approved usability decisions throughout this complete successor. Earlier removal/migration dispositions remain subject to historical-data protection and existing cutover evidence; do not repeat destructive cleanup merely to change visible labels. Technical identities, event semantics and authorised historical evidence stay intact.

Completion requires one coherent result across schema, services, permissions, screens, seeds and tests. A field, action or screen not defined here is not part of the module.

### 1.1 Conflict and disposition register

Items disposed of in v1.5 and not reopened: Plan Value Commitment and Strategy Value Commitment; Public Value Objectives and the PVO catalogue; treatment, planned treatment and treatment questionnaire; Strategy Corrective Action; Strategy-owned result capture and verification; the Strategy performance dashboard; Strategic Outcome as a layer between Objective and Indicator; the Strategy Reviewer / Strategy Approval Authority split; the Strategy Viewer workflow role; the In Review, Returned, Awaiting Approval, Approved and Archived statuses; downstream direct table reads; and delete-and-recreate cleanup.

Historical v1.6 dispositions, retained for traceability (current owner citations updated below):

| Earlier item | Disposition in v1.6 |
|---|---|
| `procuring_entity_id` on `StrategicPlan` | **Remove.** One site is one Procuring Entity. The field is denormalised data with no choice behind it, and a second copy of the PE is a second source of truth for the permission engine. |
| `owner_org_unit_id` on `StrategicPlan` | **Remove.** Strategy responsibilities are site-wide (§6). With no rule reading the field, KT-STD-001 §7's data-purpose gate requires its omission. A directorate-level framework is expressed as a **Supporting Framework** distinguished by title, not by scope. |
| Frappe Roles plus PE/OU User Permissions as the Strategy authorization mechanism | **Remove.** Replaced by role-bound `User Responsibility Assignment` resolved through registered Frappe permission hooks, per AUTH-ADR-001 v1.7 §5.2–5.3. |
| STR-AC-032 requiring authorisation through native User Permission | **Invert.** The criterion now requires that no User Permission participate in a Strategy authorization path. |
| `financial_year_id` referencing a KenTender `FinancialYear` | Replace with `fiscal_year`, referencing the ERPNext `Fiscal Year` governed by CFG-CHG-002 v0.10 §4.2. |
| §9 resolution step "prefer an exact OU scope over PE-wide scope" | **Remove.** It was a silent precedence rule contradicting STR-BR-017, and it has no meaning once scope is site-wide. Ambiguity is rejected, never resolved by preference. |
| County Government of Kisumu (`PE-CGK`) seed plan, its three fixture actors and every cross-PE isolation test | **Remove entirely.** Creating a second Procuring Entity is structurally impossible under CFG-AC-003, so the seed would fail unconditionally. Cross-PE isolation is now guaranteed by deployment topology, not by an in-product test. |
| Bespoke fixture cast (`str.author.moh@…`, `str.approver.moh@…`, `str.auditor@…`) | Replace with the shared register in KT-STD-001 §8.3, extended by the three Strategy actors named in §14.1. |
| Fixture timeline of 15–16 March 2027 | Realign to 24–25 November 2026, matching KT-STD-001 §8.5 and the seeded Fiscal Years. |
| PE row in the STR-DES-01 context strip and in the STR-DES-02, STR-DES-03 and STR-DES-06 identity cards | **Remove.** KT-STD-001 §2.3 prohibits a PE column or context record on any artboard. STR-DES-01's strip contained only that row, so the strip is deleted. |
| "the existing KenTender PE/FY selector" in §12.1 and §12.12 | **Remove.** The component no longer exists. |
| Restated closed-input rules, common page states, TDD protocol, release evidence and product-wide prohibitions | **Remove.** Cite KT-STD-001. |
| Citation of `CFG-CHG-002_PE_and_Financial_Year_Maintenance_v0.3` | Replace with CFG-CHG-002 v0.10, *Site Configuration and System Setup*. |

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
| Business authority and scope resolution | AUTH-ADR-001 v1.7 | Strategy declares required business roles; it implements no permission mechanism. |
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

### 4.7 Presentation labels and immutable identities

| Stored concept / field | Visible label | Exact interpretation |
|---|---|---|
| plan_role Primary | Main strategic plan | Same overlap and applicable-primary resolution rules. |
| plan_role Supporting Framework | Supporting framework | Same required parent_primary_plan_id, labelled Main plan. |
| status Active | Current | Current version of this plan; consumer date/year applicability is still checked. |
| status Superseded | Previous version | Historical exact version, never silently replaced with latest. |
| status Submitted for approval | Awaiting Strategy Approver review / Awaiting approval on review | Same submitted state; no new queue/state. |
| Draft with current return evidence | Changes requested | Returned Draft with exact reason; no extra Returned status. |
| StrategyNode title, type Strategic Objective | Objective | Same stored type and unique source identity; no Outcome or duplicate objective. |
| PerformanceIndicator name | Indicator | Distinct measure of an Objective. |
| PerformanceIndicator definition | How it is measured | Full required definition; not a new description field. |
| PerformanceTarget comparison/target_value | Target | At least / At most / Equal to and inherited unit. |
| fiscal_year / target_by_date | Financial year / Target date | Exactly one persisted, selected through Set target for. |
| effective_from / effective_to | Use from / Use until (successor Draft) | Same version applicability fields and immediate-approval checks; no scheduled activation. |
| display_order | Move up / Move down | System-managed sibling order via existing change set, no editable numeric position. |

These are UI labels, not migrations of enums, IDs, audit actions or historical submitted wording. Historical evidence remains verbatim; the renderer may explain its context. Source/unit rules remain Strategy-owned; the Configuration UOM catalogue is not assumed to contain the semantic Percentage indicator unit.

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

Two Strategy workflow responsibilities exist. Both are registered in the AUTH-ADR-001 v1.7 §4.4 business-role registry with `scope_type = Site-wide`.

| Business role | Scope type | Permitted actions |
|---|---|---|
| Strategy Author | Site-wide | Create plans and successor versions; edit Draft content; submit for approval. |
| Strategy Approver | Site-wide | Inspect a submitted version; return it with a reason, or approve and activate it. |

Registry properties: neither role is an `exclusive_office`; both are granted by Administrator or System Manager; both carry an `sod_tags` entry sufficient for the no-self-approval rule, which is evaluated against the version's audit history rather than a role comparison.

Read access is not a third Strategy workflow role. It is produced by the registered permission hooks in AUTH-ADR-001 v1.7 §5.3 acting on the actor's assignments. Budget and Procurement Planning users consume only the approved read contracts their modules require. **Auditor** is a registered business role under AUTH-ADR-001 v1.7 §4.4, not a bare Frappe role, and confers no Strategy workflow action.

Administrator and System Manager receive full technical read under AUTH-ADR-001 v1.7 §8 and no Strategy business action. No capability profile, operational scope assignment, plan-role grant, effective-date grant, Frappe User Permission or parallel permission store participates in a Strategy authorization path.

---

### 6.1 Actor journeys and exact access boundary

| Actor | Work / read surface | Authority limit |
|---|---|---|
| Strategy Author | Strategic plans, Draft editor, returned correction, Update plan | Site-wide current assignment; create/edit/submit permitted Draft, not own approval. |
| Strategy Approver | Existing approval tasks and exact submitted review | Return with reason or approve/activate under current guards; cannot approve a version they authored. |
| Dual-role user | Same permitted work together | No role switch and no bypass of audit-based self-approval rule. |
| Budget / Procurement Planning consumer | Existing owner selector and approved read contracts | No general Strategy Draft/task access; Planning owns the Objective selector and snapshot boundary. |
| Auditor | Authorised plan, version, definitions, targets and history | Neutral reading; no Strategy mutation or automatic approval-task access. |
| Administrator / System Manager | Technical detail in every status, including exact task or edit-shaped route | AUTH v1.7 §8 read exception; no business assignment required for read, no mutation without the real assigned responsibility and checks. |
| AO, HoD and other organisational titles | Only work from their actual assigned Strategy responsibility or authorised consumer contract | Title alone grants no Strategy decision. No extra Finance, AO, supplier or bidder workflow. |

Technical access includes all per-record details, not only Active records. A technical search/filter must locate them. A workflow-shaped URL is not a reason to deny technical read; return full read-only detail. Ordinary consumer/neutral-reader authority is not widened by this exception. Permission resolves before protected content renders, per KT-STD §3A.

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

### 8.1 User actions mapped to existing commands

| Visible action | Existing command | Preserved effect |
|---|---|---|
| Create plan and add objectives | save_strategy_plan_draft | Save identity and first Draft, then open its structure. |
| Update plan | create_strategy_successor_version | Copy exact Active version to a Draft with fixed comparison baseline. |
| Save changes (structure) | save_strategy_structure_draft | Atomic validated pending structure set; exact generated IDs and resulting token. |
| Submit for approval | submit_strategy_version | Submit the confirmed saved version; readiness and authority are server checks. |
| Return for correction | return_strategy_version | 10–500 character reason; Submitted to Draft, full history retained. |
| Approve and use plan / Approve changes and use plan | approve_strategy_version | Immediate activation and applicable atomic predecessor supersession. |

Identity/version-metadata edits still use save_strategy_plan_draft, only where existing lifecycle rules allow. The screen must identify the save scope. No generic approval wrapper, autosave record, third business responsibility or new rejection command is introduced.

### 8.2 Save, submission and unknown-outcome execution

| Case | Required result |
|---|---|
| Begin attempt | Capture immutable attempt payload, expected token and a stable command idempotency identity under KT-STD §11. Different commands have distinct identities; retries of one command reuse its identity and payload. |
| New plan | Save identity first; confirmed result retains exact plan/version/token and opens the structure. A failed route transition does not undo successful creation. |
| Pending structure Submit | Validate visible completeness; save the complete change set if changed; receive exact generated IDs/resulting token; then submit that exact confirmed Draft with a separate submission identity. An unchanged saved Draft submits directly. |
| Separately edited identity | Use its existing permitted save command first, then refetch/reconcile dependent tree tokens before structure save/submit. A stale tree cannot be silently replayed as an overwrite. |
| Save known rejected | No submit. Explain Your changes were not saved; preserve authorised pending work and exact row/field errors. |
| Save confirmed, Submit rejected | Retain the saved Draft and route. Explain Your changes were saved, but the plan was not submitted; show actual failure and permitted retry. |
| Save/submit/approval outcome unknown | Resolve or replay the original command request using unchanged identity/payload. Do not create a second plan/version, task or decision; do not label the attempt failed or approved merely from a lost response. |
| Concurrent edit or authority change | Re-read authoritative state; preserve only still-authorised edits for explicit reconciliation. Do not automatically resubmit changed content or retain protected data after access revocation. |
| Submission confirmed | Display exact submitted details and Awaiting Strategy Approver review; no further edits until an authorised Return. |
| Approval confirmed | Read exact committed Active and predecessor state; no duplicate decision/event on response replay. |

Each existing command has its own transaction. Save plus submit is not asserted to be one transaction. Pending client rows are not persistent requirement fields; generated IDs remain server-owned. Map actual RPC responses, token granularity and authorised result lookup/replay in implementation before claiming these guarantees are present. Browser reload must recover an unresolved attempt instead of inventing a new idempotency identity. Required failure/concurrency evidence is in §§15–18.

### 8.3 Review facts and guard presentation

Compare the exact submitted version against immutable based_on_plan_version_id on the server. Include added/removed/reordered structure, titles, definitions, units, targets and effective-date differences, with exact IDs for evidence and readable paths for review. Failed comparison is not No changes. For the decision page, readiness and overlap show real failures; current permission, record state, date and transactional validation remain authoritative at approval.

The plain Primary/Current labels never change the resolver or permit future activation. No first-match fallback, new approval stage or automatic date correction is introduced. Consistent closure of the predecessor applicability interval must use the owner’s documented date-boundary semantics and reject overlapping authority; inspect and verify the actual implementation rather than inventing time offsets to make a test pass. Historical consumer snapshots remain unchanged.

## 9. Error contract

| Code | Required service effect | User-facing explanation |
|---|---|---|
| `STRATEGY_RESPONSIBILITY_REQUIRED` | You are not assigned the responsibility required for this action. No record is created or changed. | You are not assigned the responsibility required for this action. Ask your KenTender administrator to check your assignment. |
| `STRATEGY_CONFIG_MISSING` | A referenced financial year is missing or unavailable. The operation fails closed. | This financial year is unavailable. Ask your KenTender administrator to check System setup. |
| `STRATEGY_INVALID_STATE` | The command is not valid for the current server status. Current status is returned. | This plan has changed. Refresh to see the available actions. |
| `STRATEGY_NOT_READY` | Submission or approval readiness failed. Structured failing rule IDs are returned. | Complete the highlighted items before submitting or approving. Identify the actual missing/invalid value; a future-effective blocker uses §11.6. |
| `STRATEGY_INVALID_HIERARCHY` | A node type, parent relationship, duplicate sibling or cross-version link is invalid. | This item cannot be placed here. Show its permitted parent/type or duplicate-name issue and the affected item. |
| `STRATEGY_INVALID_TARGET` | Target period, comparison or value is invalid for the indicator and plan. | This target is not valid. Show the actual period, duplicate, comparison, unit or value error beside the target. |
| `STRATEGY_OVERLAP` | Approval would create overlapping Active Primary authority. No status changes occur. | Another main strategic plan already covers these dates. This plan cannot be approved. Show conflicting details only when authorised. |
| `STRATEGY_CONTEXT_NOT_FOUND` | No applicable Active Primary plan exists for the requested date or financial year. | No current strategic plan covers the selected date or financial year. |
| `STRATEGY_CONTEXT_AMBIGUOUS` | More than one equally applicable Active Primary plan exists. No record is selected. | More than one strategic plan applies. Selection is unavailable until this is resolved. |
| `STRATEGY_OBJECTIVE_NOT_ELIGIBLE` | The selected objective is missing, outside the resolved version, or not in an Active plan version. No link or snapshot is produced. | This objective is no longer available for this selection. Refresh the eligible objectives. |
| `STRATEGY_STALE_WRITE` | The expected record version is stale. No newer changes are overwritten. | This plan has changed since you opened it. Refresh to see the current details. |
| `STRATEGY_DOWNSTREAM_FORBIDDEN` | A downstream caller attempted an unsupported read, Draft access or mutation. | This Strategy information is not available through this action. Do not disclose protected content. |

`STRATEGY_SCOPE_REQUIRED` and `STRATEGY_PERMISSION_DENIED` are removed: the first named a scope that no longer exists, the second named User Permission. Message conventions are in KT-STD-001 §11.

---


## 10. UI architecture and routes

**Strategy Alignment** remains a top-level module. Its existing menu entries are **Strategic plans** (formerly Strategy Portfolio) and **Approval tasks**. There is no new dashboard, role switch or approval queue. Approval tasks remains the existing Approver entry; technical readers can reach exact task detail through their authorised technical search. The top-level module remains visible when entry is denied, following KT-STD §3A.

| Screen | Canonical route | Purpose |
|---|---|---|
| STR-UI-01 Strategic plans | `/app/strategy` | Plan register and My work projection of existing actionable records. |
| STR-UI-02 Plan workspace | `/app/strategy/plan/{plan_id}` | Plan identity, exact version selection, readable content and history. |
| STR-UI-03 Structure editor | `/app/strategy/plan/{plan_id}/version/{version_number}/structure` | Draft hierarchy, Indicators and Targets; technical read on the same route when required. |
| STR-UI-04 Approval task | `/app/strategy/approval/{plan_version_id}` | Exact submitted-version review and decisions; authorised technical read without decisions. |

Plan workspace retains **Overview**, **Structure** and **History**. Approval retains **Overview**, **Structure**, **Changes** and **History**. Selected tab and exact version are in the URL using the existing supported query/route convention. The default approval Overview now includes a successor's change comparison and complete relevant proposed facts; it does not require switching to Changes to discover the decision. All four existing route families remain; the existing create entry must be mapped in the repository, not invented as a fifth application.

Budget/Planning users use only the consumer contracts their modules authorise. A consumer contract does not grant arbitrary Draft, portfolio, task or history access. Auditor reads and technical detail are governed separately from business decisions. Reuse the Frappe shell and KenTender components; no PE, Organisation Unit or global Fiscal Year selector appears.

---

## 11. Complete screen and static design contract

Supply KT-STD-001 v1.4 §2 and this section to the design workflow. These are complete compositions for STR-DES-01–10 with the existing identifiers retained. Runtime behaviour belongs to §12. Artboards are static evidence, not proof that transactions or user testing have passed.

Use names before references, short labelled facts, tables and restrained contrast. Full titles, Indicator definitions, reasons and targets must remain readable. Optional disclosures are allowed for supporting detail, never for a material approval blocker. No mandatory download, opened-tab checklist, review score or compulsory tour. Show dates in Africa/Nairobi, retain audit instants in UTC. Fixture context stays outside the product screen.

No PVO, Outcome layer, performance result, score, risk, treatment, corrective action, attachment, source reference, owner, baseline, generic note or extra approval is added. Required Indicator definition is permitted and must not be accidentally removed by the old blanket prohibition on descriptions. This is definition authoring, not performance-result capture.

### 11.1 STR-DES-01 — Strategic plans

Fixture: Esther Muthoni, Strategy Author, 24 Nov 2026 11:30 EAT. Existing Frappe breadcrumb Home > Strategy Alignment. Page title **Strategic plans**; description **Create and maintain the strategy used for budget and procurement planning.** Primary **Create strategic plan** only with current Author authority. No context strip.

Tabs **Plans 1** and **My work 0**. Search **Search plan or reference**; filters **All plan types**, **All statuses**; **Clear filters** when narrowed. Status options map to the existing enums under §4.7. Counts and records come from the same permission predicate.

| Strategic plan | Plan type | Period | Version | Status | Action |
|---|---|---|---|---|---|
| Ministry of Health Strategic Plan (Demo); secondary STR-MOH-2023-001 | Main strategic plan | 2023/24–2027/28 | 1 | Current | View |

Footer **Showing 1 of 1 plan**. My work contains the same underlying permitted tasks/drafts; it is not a second queue. Row actions are **Continue draft**, **Correct and resubmit**, **Review**, or **View**, according to server authority. A review row opens a task; it never approves. No authority-derived action is guessed from the displayed status.

Approver variant: retain the register and My work, omit Create unless separately Author. Existing Approval tasks view lists Plan, Review (New plan/Plan changes), Submitted by, Submitted, Status and Review; no approval counters or decision checklist. Exact proposed V2 example: Ministry of Health Strategic Plan (Demo), Plan changes, Esther, 24 Nov 16:20 EAT, Awaiting review, Review. A dual-role user sees authorised work together, with no role switch. Auditor and technical-reader variants omit business actions; technical search/filter remains available for records in every status.

### 11.2 STR-DES-02 — Create strategic plan

Fixture: Esther, 24 Nov 2026 11:30 EAT; isolated new plan, not the default seed. Heading **Create strategic plan**. Introduction **Enter the plan details, then add its objectives and targets.**

| Label | Exact example | Rule |
|---|---|---|
| Plan title | Ministry of Health Strategic Plan 2028–2033 (Demo) | Required title; consistent with actual end date. |
| Plan type | Main strategic plan | Maps to Primary. Other option Supporting framework. |
| Start date | 1 Jul 2028 | Plan period start. |
| End date | 30 Jun 2033 | Later than start. |

For **Supporting framework**, reveal required **Main plan**, using eligible server-returned Primary choices. Guidance **A supporting framework sits under a main strategic plan.** Primary hides and clears the inapplicable parent in the permitted Draft command. No generated-reference input before creation, even a read-only Not assigned field. No PE/OU field, attachment, description or duplicate first-version dates.

Footer **Cancel** / **Create plan and add objectives**. Creation saves plan identity and the first Draft, then opens structure authoring. No submit before the required structure exists. A future-period Draft may be prepared; no scheduled approval or activation is implied. Confirmed save followed by failed navigation offers **Open saved draft** for that exact identity. Unconfirmed creation resolves the original request; do not create again blindly.

### 11.3 STR-DES-03 — Current plan overview and readers

Fixture: Naomi Chebet, Auditor, 24 Nov 2026 11:30 EAT. Title **Ministry of Health Strategic Plan (Demo)**; badge **Current**; secondary reference STR-MOH-2023-001 · Version 1. Tabs Overview, Structure, History. No business action for Naomi.

| Plan details | Value |
|---|---|
| Plan type | Main strategic plan |
| Plan period | 1 Jul 2023 – 30 Jun 2028 |
| This version applies | 1 Jul 2023 – 30 Jun 2028 |

Lead with **Objectives and targets**: Objective **Strengthen interoperable national digital health services**; Indicator **Percentage of priority facilities using interoperable digital health services**; Target **At least 80% · FY 2027/28**. Show full **How it is measured**: **Priority facilities operating an approved interoperable digital health service divided by all priority facilities, expressed as a percentage.** Unit Percentage. Full hierarchy is in Structure with the same exact facts; the opening page must not substitute six counts for the strategy's meaning.

**Approval details**: Dr Alfred Ochieng; 1 Jul 2023 09:15 EAT; approved and activated Version 1. **Structure summary** may show 1 Pillar, 1 Programme, 1 Sub-programme, 1 Objective, 1 Indicator and 1 Target as secondary detail. No achieved-result chart or procurement transaction count.

Author variant offers **Update plan** when the existing server command is permitted. Explanation **Start a draft from the current plan. The current plan remains in use until the changes are approved.** Existing pending Draft shows **Update in progress** with a permitted Continue draft link; submitted successor shows **Update awaiting Strategy Approver review. The current plan remains in use.** These notices never replace the Current badge or historical source.

Historical variant uses **Previous version · Version [actual number]** and exact recorded content, with a separate permitted **View current plan** link. No redirect to the latest version. Technical readers can read Draft, Submitted, Active and Superseded records, including edit-shaped routes, without mutation controls. Ordinary consumers remain limited to the data their own contracts allow.

### 11.3A Draft Overview — plan details and version dates

This is a state variant of the existing STR-UI-02 Overview, not another route or artboard family. Heading **Plan details**; Draft or Draft update badge; exact generated reference/version secondary. For the first Draft, show the same Plan title, Plan type, conditional Main plan, Start date and End date controls from §11.2, only while §12.2 permits identity editing. First-version applicability derives from the plan period; do not request it twice.

For a successor Draft, show plan identity read-only and the existing version fields labelled **Use from** and **Use until**. Guidance **These dates must fall within the plan period. Approval makes this version current immediately; a future start date prevents approval until that date.** These controls map to effective_from/effective_to without new fields or scheduling. Retain §4.2 requiredness and the applicable date validation. Positive V2 example: Use from 25 Nov 2026, Use until 30 Jun 2028. Future-profile example: Use from 1 Jul 2027, Use until 30 Jun 2028.

Action **Save plan details** commits only the permitted identity/version metadata through save_strategy_plan_draft. **Edit structure** navigates to the same version's structure after resolving any unsaved detail edits. Save plan details is deliberately distinct from structure Save changes: neither button claims to persist another surface's unconfirmed edits. If Submit is invoked with pending metadata, follow the explicit command sequencing in §§8.2 and 12.3. Technical readers see the same full values read-only, including Draft dates; they cannot save or submit.

### 11.4 STR-DES-04 — Draft structure editor

Fixture: Esther, 24 Nov 2026 15:55 EAT, isolated V2 Draft created at 13:10; effective-date profile is explicit under §14.4. Heading **Edit plan**, followed by full plan title, badge **Draft update**, secondary reference/version. Tabs Overview, Structure selected, History. Notice **The current plan remains in use until these changes are approved.**

One page action area **Save changes** / **Submit for approval**. No competing Save draft at the page top and Save changes inside the selected-record card. Save changes commits the pending validated structure change set; it does not silently save separately edited identity metadata.

On wide screens retain tree and selected-item editor; on narrow screens stack with accessible navigation back to the selected item. Tree heading **Plan structure**, action **Add pillar**. Full expanded fixture:

| Parent / level | Type | Title / value | Actions allowed by structure |
|---|---|---|---|
| Root | Pillar | Digital health systems | Add programme |
| Digital health systems | Programme | Health policy, standards and regulation | Add objective; Add sub-programme |
| Health policy, standards and regulation | Sub-programme | Digital health governance | Add objective |
| Digital health governance | Strategic Objective | Strengthen interoperable national digital health services | Add indicator |
| Strategic Objective | Performance Indicator | Percentage of priority facilities using interoperable digital health services | Add target |
| Performance Indicator | Performance Target | At least 85% · FY 2027/28 | Edit |

Selected Objective card: heading **Objective**; read-only path Digital health systems / Health policy, standards and regulation / Digital health governance. Field **Objective** populated with the full title. Guidance **State what the plan aims to achieve.** Only the existing title is edited; no new description or Outcome. Provide **Move up**, **Move down** for valid sibling moves instead of an editable Display order. First/last positions disable the corresponding move. Keyboard actions produce the same validated sibling change set.

Deletion label is **Delete objective** (or actual type). Confirmation names the item; descendants block removal unless explicitly moved/removed in one valid change set, and nothing may be deleted after first submission. Do not offer cascade delete or imply Draft after Return restores deletion rights. No generic Delete node, Add child, editable generated code or arbitrary drag reparenting.

A Programme without Sub-programme exposes Add objective directly. Do not insert placeholder layers. Adding a Sub-programme is optional; Pillar and Programme are retained under the current hierarchy rule. New-plan empty tree says **Add a pillar to start the plan structure.** Directly explain a missing prerequisite beside the corresponding action.

### 11.5 STR-DES-05 — Indicator and target editor

Same V2 Draft and clock as §11.4. Select the Indicator. Heading **Indicator**; context **Measures: Strengthen interoperable national digital health services**.

| Label | Exact value / guidance |
|---|---|
| Indicator | Percentage of priority facilities using interoperable digital health services |
| Guidance | What will show progress towards this objective? |
| How it is measured | Priority facilities operating an approved interoperable digital health service divided by all priority facilities, expressed as a percentage. |
| Definition guidance | Explain exactly what this indicator counts or calculates. |
| Unit | Percentage |

Targets table: Period FY 2027/28; Target At least 85%; Edit. **Add target** opens an inline target editor in this selected-Indicator surface; Edit uses the same editor. This replaces the old target dialog's unclear second persistence step. The page's Save changes remains the only structure persistence action.

Target fields: **Set target for** with **Financial year** / **Target date**; show exactly one applicable input; **Target**, containing At least / At most / Equal to and numeric value; inherited read-only unit suffix **%** for Percentage. Guidance **Set the expected value and period for this indicator.** No target name, description, independent unit, baseline or actual-result field.

Annual example: Financial year, FY 2027/28, At least, 85, %. Date example is a separate fixture: Target date, 30 Jun 2028, At least, 85, %. Exactly one of fiscal_year and target_by_date is submitted; switching modes removes the inactive draft value before validation. Keep the Indicator's current unsaved values when changing selection only through §12.3's explicit pending-change handling. No new default unit, precision, range or duplicate-period exception.

**Discard new target** removes only a never-persisted pending row. Persisted-target removal follows deletion/history rules and the validated change set. Add target locally creates an editable pending target, not a second server save; a subsequent page Save or Submit commits it once. Failed validation identifies the target and preserves permitted pending values.

### 11.6 STR-DES-06 — Approval task · Decision overview

Positive fixture: Alfred, 25 Nov 2026 **11:15 EAT**, exact submitted STR-MOH-2023-001-V2, based on V1, positive immediate-effective profile in §14.4. This clock aligns the shared 11:00–17:00 Strategy window; the amendment's illustrative 10:15 is corrected here. Title **Review plan changes**. Plan name prominent; Submitted by Esther, 24 Nov 16:20 EAT; secondary exact reference/version; badge **Awaiting approval**. Tabs Overview selected, Structure, Changes, History.

**What changed** appears first, calculated by the server:

| Item | Previous accepted baseline · V1 | Proposed · V2 |
|---|---|---|
| Target for FY 2027/28 | At least 80% | At least 85% |
| Version effective from | 1 Jul 2023 | 25 Nov 2026 |

Text **No other submitted identity, effective-date or structure values changed in this isolated fixture.** Predecessor closure on approval is a lifecycle effect, not an omitted proposed edit. General comparisons must include additions, removals, moves, definitions, units and applicability dates when actually changed.

**Proposed plan** shows Main strategic plan; plan period 1 Jul 2023–30 Jun 2028; proposed version applicability 25 Nov 2026–30 Jun 2028; full Pillar/Programme/Sub-programme path, Objective, Indicator, definition, Percentage unit and 85% FY2027/28 target from §11.5. Use labelled facts and structured detail. The full tree remains on Structure. Do not substitute only a target comparison for full proposed content or display the current version as the proposed one.

Footer visible on every tab: **Return for correction** / **Approve changes and use plan**. Consequence beside it: **Approval replaces the current strategy version for new planning selections. Existing approved records keep their saved strategy details.** Approval also checks period applicability for the consumer; a Current badge does not establish eligibility for every year.

First-version variant: title **Review strategic plan**; no empty comparison or predecessor notice; complete proposed structure/identity first. Primary **Approve and use plan**. Consequence **Approval makes this plan available for new budget and procurement planning. It does not approve a budget or procurement.**

Show only real actionable readiness failures prominently, with the affected value and useful next action. Do not lead with a green checklist or counts. Do not require every tab opened, a checkbox, score, reason for approval, generic confirmation or download. The server repeats all guards at commit; page readiness is not authority.

Future-effective variant: retain the complete original fixture with effective start **1 Jul 2027**, reviewed in Nov 2026. Show the effective-start comparison 1 Jul 2023 → 1 Jul 2027 as well as the target change. Banner **This version cannot be approved yet. It starts on 1 Jul 2027. Approval makes the version current immediately, so it cannot be approved before that date.** Follow with **Return it if the date needs correction. If the date is intentional, it can remain awaiting approval. An authorised Approver must approve it when it is applicable. It will not activate automatically.** Approval disabled, permitted Return available. No date rewrite, scheduler or extra status.

### 11.7 STR-DES-07 — Approval task · Proposed structure

Reuse exact submitted-version header and fixed decision area from §11.6, Structure selected. Heading **Proposed plan**. Show all hierarchy rows from §11.4, with full Indicator definition and inherited-unit Target from §11.5 available on the same page. Names and typed parent relationships remain distinct; no generic record tree alone.

Select/search a row to read its complete facts; selection does not edit, acknowledge or approve anything. Display full paths for similar names. All additions/removals in comparison are understandable, while this tab shows the complete submitted result. No Add, Edit, Delete, drag, checkbox, row acceptance or performance result. Material date/overlap blockers remain visible on every tab. All read results bind to the exact submitted version.

### 11.8 STR-DES-08 — Approval task · Complete comparison

Changes selected; same submitted identity/footer. Heading **Changes from Version 1**. Use the positive comparison in §11.6 or the future-effective version comparison, never mix profiles. Server compares the fixed based_on_plan_version_id with the submitted version, not whichever Active version later exists. Show only changed values but include all material changed fields; Added/Removed/Moved rows identify full item type and path. Long definitions remain readable without clipping.

No unchanged table flood, inline edits, row accept/reject or misleading “Only the target changed” where applicability differs. A first version shows **This is the first version of this plan.** and the proposed plan link. An unavailable baseline yields **The changes could not be loaded. Try again.** Never represent a failed comparison as No changes; a missing review-critical comparison prevents presenting a ready successor approval.

### 11.9 STR-DES-09 — Approval task · Submission and history

History selected; same header/footer. Heading **Submission and history**. Exact V2 evidence:

| Date and time | Event | Actor |
|---|---|---|
| 24 Nov 2026, 16:20 EAT | Submitted for approval | Esther Muthoni |
| 24 Nov 2026, 15:55 EAT | Draft saved | Esther Muthoni |
| 24 Nov 2026, 13:10 EAT | Draft update created from Version 1 | Esther Muthoni |

Return/resubmission variants preserve exact actual comments and events. No fabricated return on the default profile. Event labels can be readable while stored actions/IDs stay stable. This tab remains limited to this version; opening an earlier version is a separate authorised navigation. Do not add editable comments, attachments or raw technical request logs to the business review.

Return dialog: heading **What needs to change?**; field **Correction required**, required 10–500 characters; example **Explain how the revised target will be measured and confirm the date these changes should take effect.** Footer Cancel / Return for correction. Record the user's exact text. No Reject or Decline command. The return reason is not an approval opinion form.

### 11.10 STR-DES-10 — Shared states and actor variants

Resolve the permission verdict before any protected page header, filter, count, content or empty state. During that wait show the approved neutral loading state. A denied page never paints an otherwise usable screen behind the refusal. Reuse global shell/navigation without disclosing protected content.

| Condition | Exact copy / controls |
|---|---|
| Permitted data loading | Loading strategic plans…; structure-appropriate skeleton, no false zero. |
| No plans, Author | No strategic plans exist yet. Create strategic plan. |
| No plans, reader | No strategic plans to display. No create button. |
| No filter matches | No plans match these filters. Change or clear the filters to see other strategic plans. Clear filters. |
| General entry denied | You do not have access to Strategy Alignment. This area needs Strategy Author, Strategy Approver or Auditor responsibility, or Administrator/System Manager technical access. Ask your KenTender administrator to check your access in System setup. |
| Approval entry denied | You do not have access to this Strategy approval page. Decision access requires Strategy Approver responsibility. Administrator and System Manager can inspect the record read-only. Ask your KenTender administrator to check your access in System setup. |
| Server read failure | Strategy information could not be loaded. Try again. If the problem continues, contact KenTender support. |
| Returned Draft | Changes requested. Show full actual reason; Correct and resubmit opens that Draft. |
| Known save failure | Your changes were not saved. Retain permitted edits; focus actual error. |
| Save succeeded, submit rejected | Your changes were saved, but the plan was not submitted. Retain the saved Draft and show cause. |
| Unknown command outcome | We could not confirm the result. Checking the existing request… |
| Stale edit/review | This plan has changed since you opened it. Refresh to see the current details. |
| Own-version approval | Another Strategy Approver must review this version. |
| Missing/unauthorised record whose existence is protected | This plan record is not available to you. Do not distinguish missing from unauthorised existence. |

Forbidden fixture: Samuel Otieno, expired unrelated assignment. Technical reader is a separate positive read fixture, never a denial example. Missing data and permission denial are not interchangeable. Ordinary consumer eligibility does not turn a Budget/Planning user into a Strategy Author/Approver/Auditor. Zero/ambiguous Strategy resolution is explained in the consumer's own surface, without granting a new role or showing a Draft.

### 11.11 Existing controls and coverage

Reuse Frappe header, breadcrumb, navigation, fields, dialogs, notifications and tokens. No business title grants Strategy authority. Finance/Budget and Procurement Planning own their selection journeys; Strategy returns eligible definitions and lineage. AO, HoD, suppliers and bidders gain no extra Strategy task.

Verify keyboard tree navigation, Move up/down, contrast, focus after error/return, readable wrapped definitions/reasons and narrow-screen layouts. A technical reader gets equivalent complete detail for each status, with all mutation controls absent. An ordinary reader's approved-contract access remains limited. Representative-user validation is outstanding; complete artboard instructions do not establish tested usability.

---

## 12. Functional interaction requirements — excluded from design prompts

### 12.1 STR-UI-01 — Strategic plans and existing work

Use the registered scope hooks for rows, counts, options, direct routes and exports. Strategy responsibility is site-wide; no PE, OU, Fiscal Year or role-switch context is required. Plans shows authorised records; My work selects existing records with a live permitted next action. Preserve existing Approval tasks navigation and map its actual implementation without creating a duplicate task model.

Search title/reference; plan-type and status filters are local query choices backed by the server, not grants. Back/forward restores view/filter state. Create is Author-only; Review navigates without deciding; row actions use server available_action. Returned status rendering uses actual return evidence and current Draft state. Technical search reaches all record/task statuses; ordinary consumer access remains constrained by its own contract.

### 12.2 STR-UI-02 — Identity, current plan and version navigation

Create uses save_strategy_plan_draft once for a captured attempt, obtains exact IDs/token, and opens that Draft's structure. Confirmed creation followed by navigation failure reopens the same record; unknown creation resolves/replays the original idempotency identity. No first-record/year/Administrator fallback.

First version inherits plan-period dates without duplicate input. Identity is editable only in its first Draft before downstream use. Supporting Framework requires the eligible parent; Primary forbids it. Version metadata uses the existing fields; do not make immutable plan identity editable through an update.

Update plan invokes create_strategy_successor_version on the exact Active source and preserves based_on_plan_version_id. Its returned Draft opens directly; current source remains Active. Display an existing permitted pending update when returned by the service, without inventing cancellation, exclusive Draft limits or a new lifecycle not defined by the owner. Concurrent creation/replay must not duplicate one user's same attempt; separate permitted attempts follow the actual domain policy documented during implementation.

Explicitly labelled version navigation never silently substitutes latest content. Technical readers get read-only details for all states and route shapes. Historical snapshots stay fixed. No data is made globally accessible merely because a Current label appears.

### 12.3 STR-UI-03 — Editing, pending changes and submission

Read one complete authorised Draft tree with its expected version token. Each row has a stable existing ID or a client-only temporary identity for a pending addition; temporary IDs never become persisted business references or downstream lineage. Server save returns authoritative generated IDs and the new concurrency token. Inspect and map actual RPC shapes under §18.3.

A single pending structure change set contains validated additions, edits, sibling reorders and allowed removals. Same-page tree selection preserves pending work. Attempted navigation away with unsaved edits offers **Save changes**, **Discard unsaved changes**, **Stay here**; discard affects only unsaved work. Do not silently autosave or discard. Field validation identifies the actual row and error; no hidden record-save prerequisite.

Move up/down changes only siblings; no cross-version move. Programme may directly parent Objective. Deletion obeys descendants and first-submission restrictions even after Return; a Draft label is not sufficient clearance. Indicator attaches directly to Objective; no Outcome. Unit derives from Indicator. One target per Indicator/Fiscal Year or target-by date; exactly one period mode. Year options come from CFG's native catalogue and overlap rule, with date/unit validation unchanged.

Add target/Edit uses the inline pending editor in §11.5. No intermediate server add followed by a duplicate save. Pending changes are explicit, not new domain fields. Invalid pending target blocks persistence of the validated structure set rather than silently omitting the invalid item. Saving a valid structure is atomic for that command, including generated references and ordering.

**Submit for approval** executes §8.2: validate visible values, save pending structure if changed, then submit the confirmed exact Draft with a separate command identity. A previously saved unchanged Draft submits directly. If identity metadata was separately edited, save that through its own command and rebase/refetch the valid tree token before continuing; no stale token reuse, covert overwrite or claim that all commands form one atomic operation. Preserve still-authorised input and known successful results on failure. Initial and returned Draft use the same readiness/lifecycle rules; no Needs/DPP intake flag is introduced into Strategy.

### 12.4 STR-UI-04 — Review and decision

Business review requires the current Strategy Approver assignment. AUTH v1.7 technical detail exception allows Administrator/System Manager to read the exact task and version with no business controls; do not reject them because the route is approval-shaped. Other read-only users do not gain task access from consumer eligibility or general read alone.

The route fixes plan_version_id. Every tab resolves that exact version and its fixed comparison baseline. Overview includes material successor changes plus relevant full proposed facts. Structure exposes every statement, Indicator definition/unit and Target. Changes is server-calculated, including applicability and removals; History uses exact version events. Failed/unavailable data is not an empty comparison or readiness success.

Return for correction uses only the existing 10–500 character reason and command. It changes Submitted to Draft and retains history; no new version or rejection state is invented. The current Active plan remains until a successor is approved. Prior submission evidence must remain reviewable under §13; do not repurpose the return reason as generic notes.

The explicit approval label expresses activation. One deliberate click carries expected status/token, exact submitted ID and stable command identity. Revalidate responsibility, audit-based no-self-approval, readiness, effective dates and overlap under the transaction guard. No reason, checklist or confirmation stage is added. Future start, expired applicability, stale source, ambiguity or failed guard leaves approval uncommitted and displays the actual reason. Return remains available where authorised; same-author approval prohibition does not silently add an unapproved prohibition on Return.

Successful successor approval activates the submitted version and supersedes/closes the predecessor applicability atomically. Never edit source content or old downstream snapshots. Unknown response resolves the same command outcome before offering another decision; page refresh alone is not evidence of rollback. A concurrent decision reloads the neutral actual result, with no duplicate decision or notification.

### 12.5 Shared states, accessibility and recovery

Apply KT-STD §3A before rendering. Keep selected route/navigation consistent on denial; no page-load modal. Retain stable displayed data only while still authorised; on access revocation remove protected content and show permitted recovery. Errors preserve still-authorised input without overwriting newer saved work. Keyboard focus moves to the actual invalid field/record or concise summary and is restored after dialogs. Status announcements do not steal focus on routine refresh. Colour never carries status alone.

Plan creation, structure save, submission and approval distinguish known failure, partial success and unknown outcome. Technical diagnostics use support references, not raw payloads/tokens on business cards. Failed reads do not imply zero plans or no applicable strategy. No arbitrary mandatory dwell time, tab-opening requirement or download. Date/overlap/authority checks remain server rules regardless of button state.

### 12.6 Downstream Strategic Objective selection boundary

Procurement Planning owns its Objective selector and consumes list_strategy_objectives with exact generated IDs, titles and ordered ancestor paths. One Plan Item selects one Strategic Objective from the applicable Active version; Indicator/Target are associated read-only facts, never substitute selection objects. Draft stores Objective ID; the owner approval boundary uses create_strategy_snapshot and stores immutable returned lineage.

Budget and later consumers use only their authorised owner contracts. Strategy does not import or update their transactions, create budget/procurement approval or add requester-facing Strategy selection to Departmental Needs. Current label alone does not establish applicability to an arbitrary consumer date/year. Historical consumer snapshots are not rebuilt when Strategy changes. Zero/ambiguous matches and ineligible objectives remain typed errors, never first-match selection or Draft substitution.

---

## 13. Audit and historical integrity

Append-only events: plan and successor-version creation; Draft structural change sets; submit, return, approve, activate and supersede; responsibility or segregation denial; successful and failed context resolution; Strategic Objective listing and lineage reads by a downstream module; and snapshot creation or idempotent reuse.

Each event records actor, business role, the exercised responsibility assignment ID, record and version IDs, action, timestamp, before and after status, required reason and correlation ID. A downstream contract event also records the calling module. No event records a Procuring Entity or organisation-unit scope, because none participates.

Submitted for approval, Active and Superseded versions are immutable. A Strategy snapshot copied into a downstream approval record does not change when the source plan later changes status. Deleting lifecycle events, renumbering versions and reusing generated references are prohibited.

---

## 14. Seed contract

Site configuration, Organisation Units, base actors and Fiscal Years come from KT-STD-001 §8. Execution rules come from KT-STD-001 §8.6.

### 14.1 Shared fixture actors

Inspected KT-STD-001 v1.4 §8.3 already contains these Strategy actors. Reuse their identities and real dated assignments; do not add duplicate users:

| Display name | Login identifier | Responsibility | Scope |
|---|---|---|---|
| Esther Muthoni | `esther.muthoni@moh.example.test` | Strategy Author | Site-wide |
| Dr Alfred Ochieng | `alfred.ochieng@moh.example.test` | Strategy Approver | Site-wide |
| Naomi Chebet | `naomi.chebet@moh.example.test` | Auditor | Site-wide |

KT-STD-001 v1.4 §8.4A already supplies **Strategy journeys — 24–25 Nov 2026, between 11:00 and 17:00 EAT.** The v1.8 approval fixture uses 11:15 EAT to align with that window. Historical baseline activation in 2023 requires explicit dated authority evidence; names alone are not sufficient.

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

### 14.4 Isolated workflow and usability fixtures

Version 2 is isolated, not part of the default Active seed. Never run mutually exclusive profiles simultaneously with the same IDs. Use the test namespace/rollback discipline in KT-STD §8.7. Default Version 1 content, identities, 80% target and historical approval events remain unchanged.

| Shared V2 item | Exact value |
|---|---|
| Version ID | STR-MOH-2023-001-V2 |
| Comparison baseline | STR-MOH-2023-001-V1 |
| Successor created | 24 Nov 2026 13:10 EAT · Esther Muthoni |
| Draft saved / editor clock | 24 Nov 2026 15:55 EAT · Esther Muthoni; editor no longer predates creation. |
| Submitted | 24 Nov 2026 16:20 EAT · Esther Muthoni |
| Content change | FY2027/28 target At least 80% → At least 85%; all structure, Indicator definition and other content retained. |
| Applicability comparison | A separate required comparison row; the start changes in both profiles below. Never claim the target is the only changed field. |

| Profile | Proposed effective dates / clock | Expected behaviour |
|---|---|---|
| STR18-FX-FUTURE | 1 Jul 2027–30 Jun 2028; review 25 Nov 2026 11:15 EAT | Preserve the original future-date proposal as a negative approval example. Approval blocked; state stays Submitted; authorised Return permitted. No scheduled activation. |
| STR18-FX-IMMEDIATE | 25 Nov 2026–30 Jun 2028; review 25 Nov 2026 11:15 EAT | All other guards and dated assignments verified; approval activates V2 and supersedes V1 atomically. Compare start 1 Jul 2023 → 25 Nov 2026 and target 80% → 85%. |
| STR18-FX-RETURN | Branch of a submitted profile, Return 25 Nov 2026 11:20 EAT | Alfred returns with exact §11.9 example reason. Same version becomes Draft; current V1 stays Active. Esther opens correction after that instant. No fabricated return event in other profiles. |
| STR18-FX-DATE-TARGET | Separate Draft of the immediate profile, 24 Nov 2026 15:55 EAT | Demonstrate target-by-date 30 Jun 2028, At least 85%, without silently adding it to the default annual fixture. Exactly one period mode per target. |
| STR18-FX-NEW-PLAN | New-plan form, 24 Nov 2026 11:30 EAT; title Ministry of Health Strategic Plan 2028–2033 (Demo), period 1 Jul 2028–30 Jun 2033 | Illustrates creation only; no default extra Active Primary plan or future approval. First version inherits period dates. |

Additional parameterised profiles cover direct Programme → Objective without Sub-programme; Supporting Framework parent selection; no/expired/dual-role assignments; all-state technical reads; invalid/duplicate target; missing year; overlap; concurrent approvals; lost save/submit/approval response and stale edits. Use existing actors with explicit temporary test assignments and rollback; never grant Administrator a business role just to make a fixture pass. Declare exact supporting plan IDs and eligible parent data in the executable test namespace before using that profile, not as fabricated defaults in this document.

Seed facts may not be mutated to satisfy a screenshot. No July 2027 version becomes Active in November 2026. The illustrative amendment's 10:15 approval time is normalised to 11:15 here solely for shared-window consistency; the governing date remains unchanged.

### 14.5 Additional seed rules

- Upsert by the exact stable identifiers above; create no duplicates.
- Validate each plan through the same domain rules used by commands.
- Seed lifecycle events use the named responsibility holders, never Administrator.
- Fail loudly on a missing Fiscal Year, invalid hierarchy, invalid target or conflicting Active plan.
- Mark synthetic records visibly as **(Demo)** in plan titles; add no generic disclaimer field.

---

## 15. Acceptance contract

All 37 existing STR-AC identifiers are retained and reconciled below; §15.2 adds 24 criteria, for **61** total. These are required results, not claims of executed tests.

| ID | Acceptance result |
|---|---|
| STR-AC-001 | The module installs and imports without the legacy Demands package or Procurement Home. |
| STR-AC-002 | No executable metadata, route, service, field, label, seed or active test refers to Plan Value Commitment, Strategy Value Commitment, PVO, Strategic Outcome, treatment or Strategy Corrective Action. |
| STR-AC-003 | A Strategy Author creates a Draft through Create plan and add objectives, receives generated IDs/token and resumes the same record after a lost navigation response; no empty generated-reference input. |
| STR-AC-004 | A user without an Active Strategy assignment, including Administrator/System Manager acting only technically, cannot create, submit, return or approve. Technical read succeeds separately for all record/task statuses. |
| STR-AC-005 | A Draft can represent Pillar → Programme → optional Sub-programme → Objective, with Indicator directly beneath Objective and Target directly beneath Indicator. |
| STR-AC-006 | Strategic Objective and Performance Indicator are distinct types and cannot be substituted for one another; no Strategic Outcome type exists. |
| STR-AC-007 | Target validation enforces period choice, comparison, unit-compatible value and percentage range. |
| STR-AC-008 | Readiness blocks submission when plan identity or hierarchy is invalid, or when the version has no Strategic Objective, Indicator or Target. |
| STR-AC-009 | A Procurement Plan Item can select exactly one Strategic Objective from its resolved Active plan version and cannot select an Indicator or Target instead. |
| STR-AC-010 | Only Strategy Author and Strategy Approver are Strategy workflow responsibilities; the author of a version cannot approve that version. |
| STR-AC-011 | Return requires a reason and preserves the complete workflow history. |
| STR-AC-012 | Submitted, Active and Superseded content is read-only; Active correction uses Update plan to copy a successor. Return edits the existing Draft while retaining history; deletion remains prohibited after first submission. |
| STR-AC-013 | Concurrent approval cannot create overlapping Active Primary authority, and the guard holds when the command layer is bypassed. |
| STR-AC-014 | Approving a successor atomically activates it and supersedes the previous Active version of the same plan. |
| STR-AC-015 | Zero and multiple context matches return typed errors and never select a record by preference or order. |
| STR-AC-016 | `resolve_strategy_context` returns the correct Active Primary version for a supplied date or Fiscal Year, and requires no Procuring Entity or organisation-unit input. |
| STR-AC-017 | `list_strategy_objectives` returns only Active Strategic Objectives with exact generated IDs and ordered ancestor paths. |
| STR-AC-018 | `get_strategy_lineage` returns exact stable IDs, types and titles in plan-to-record order. |
| STR-AC-019 | `create_strategy_snapshot` captures the selected Strategic Objective and its exact plan-to-objective lineage, and is immutable and idempotent for one downstream approval correlation ID. |
| STR-AC-020 | Downstream direct-table mutation and Draft reads are rejected. |
| STR-AC-021 | An ordinary approved-contract/neutral reader gains no approval-task access. Administrator/System Manager can inspect the exact task and all per-record detail read-only under AUTH v1.7 §8, with no decision authority. |
| STR-AC-022 | Portfolio counts, rows, routes, exports, reports and APIs apply the same server-side predicate, and a plan hidden from the register is unreachable by direct route. |
| STR-AC-023 | The default seed is deterministic and an immediate second run produces no change. |
| STR-AC-024 | A missing ERPNext Fiscal Year fails seed execution without creating a fallback record. |
| STR-AC-025 | The four primary route families render the complete revised STR-DES-01–10 compositions and actor variants without console errors; no second shell or approval queue. |
| STR-AC-026 | Loading, no-match, forbidden and server-error states disclose no false or unauthorised data. |
| STR-AC-027 | The Frappe header and breadcrumb are reused and not duplicated inside the Vue page; no PE, scope or context selector appears on any Strategy screen. |
| STR-AC-028 | No Strategy page or API accepts Value Commitment, source-reference, evidence, attachment, contact, baseline, treatment, actual-result or corrective-action data. |
| STR-AC-029 | Approver can inspect full exact submitted identity, hierarchy, Indicator definitions/units, targets, comparison including applicability dates and history. Overview leads with successor changes; no tab substitutes latest Active content. |
| STR-AC-030 | The decision area remains on every approval tab. Return and otherwise eligible approval revalidate state/token; a future-effective, expired, stale or failed-guard submission cannot be approved. No mandatory tab tour or added confirmation stage. |
| STR-AC-031 | No executable Strategy metadata, permission, route, service, seed or active test refers to Strategy Reviewer, Strategy Approval Authority, Strategy Viewer as a workflow role, or the removed lifecycle statuses. |
| STR-AC-032 | Every Strategy write is authorised through an Active `User Responsibility Assignment` resolved by the registered permission hooks. No Frappe User Permission, capability profile, operational scope assignment or parallel permission lookup participates in any Strategy authorization path. |
| STR-AC-033 | No `procuring_entity`, `procuring_entity_id`, `owner_org_unit_id` or KenTender `FinancialYear` reference exists in Strategy schema, services, seeds, fixtures or tests. |
| STR-AC-034 | Strategy Author and Strategy Approver appear in the business-role registry with `scope_type = Site-wide`, and no Strategy command performs an organisation-unit scope check. |
| STR-AC-035 | Every page resolves its authorisation verdict before rendering; a denied actor sees the inline Forbidden panel with no header, filter, content or empty state painted, and no permission modal appears on page load. |
| STR-AC-036 | The Forbidden panel names the responsibilities appropriate to that surface and recognises technical read where applicable; it directs the user to a KenTender administrator, never a supervisor or invented approver. |
| STR-AC-037 | Selecting this module without access pushes its own route, highlights it in navigation, and lands on its Forbidden state; the module is never hidden and route and view never diverge. |

### 15.1 Minimum rule coverage

| Rule group | Required automated coverage |
|---|---|
| Responsibility and access | STR-BR-001, STR-AC-003–004, STR-AC-010, STR-AC-021–022, STR-AC-031–034 |
| Domain structure | STR-BR-005–012, STR-AC-005–009, STR-AC-012 |
| Lifecycle and approval | STR-BR-004, STR-BR-006, STR-BR-015–017, STR-AC-010–015 |
| Downstream Objective and contracts | STR-BR-013–014, STR-BR-018–020, STR-AC-009, STR-AC-016–020 |
| Seeds | STR-AC-023–024 |
| UI | STR-AC-025–030 |

---


### 15.2 Approved usability coverage

| ID | Approved decision | Required result |
|---|---|---|
| STR18-AC-001 | STR-UX-001 | Strategic plans and My work show name-first scoped rows and actual actions; Review opens without deciding; no extra queue or role switch. |
| STR18-AC-002 | STR-UX-001 | Current, Previous version, Changes requested and awaiting-review text map to exact existing states/evidence without hiding pending updates or granting consumer eligibility. |
| STR18-AC-003 | STR-UX-002 | Main strategic plan and Supporting framework use the same enums/parent contract. First version inherits dates; no duplicate date entry or extra source field. |
| STR18-AC-004 | STR-UX-002 | Create and Update plan use original command identities; confirmed creation resumes exact Draft after navigation failure and unresolved responses cannot duplicate an attempt. |
| STR18-AC-005 | STR-UX-003 | Programme offers Add objective directly and optional Add sub-programme. Valid hierarchy and same-version links are enforced without placeholders. |
| STR18-AC-006 | STR-UX-003 | Keyboard Move up/down reorders siblings atomically; named deletion obeys descendants and first-submission prohibition, including returned Drafts. |
| STR18-AC-007 | STR-UX-004 | One structure Save changes persists one validated pending set; Submit saves valid pending content then submits exact resulting version/token, with no forced manual Save step. |
| STR18-AC-008 | STR-UX-004 | Save rejected, saved-but-submit-rejected, unknown outcome and stale/permission-changed cases preserve permitted work, resolve original requests and produce no duplicate plan/version/task/event. |
| STR18-AC-009 | STR-UX-005 | Indicator name and full How it is measured definition remain distinct required facts in authoring and review. Target has comparison/value/inherited unit and no actual-result input. |
| STR18-AC-010 | STR-UX-005 | Annual and target-date modes both work, persist exactly one period, reject invalid or duplicate periods and preserve unit/percentage rules; pending target edits save once with the structure. |
| STR18-AC-011 | STR-UX-006 | Successor Overview leads with server comparison of fixed baseline and complete relevant proposed facts; initial plan shows full proposal without empty predecessor machinery. |
| STR18-AC-012 | STR-UX-006 | Date, target, unit, definition, addition, removal and move changes cannot be omitted; failed comparison is not No changes, and complete exact-version Structure/History remain reachable. |
| STR18-AC-013 | STR-UX-007 | First/successor approval labels state immediate use and preserved historical snapshots. One deliberate decision; no Reject, new approval, reason/score/checkbox or mandatory tab tour. |
| STR18-AC-014 | STR-UX-007 | Return keeps the existing reason length and Submitted→Draft lifecycle; approval keeps authorship/date/readiness/overlap guards and atomic activation/supersession, with original-result replay. |
| STR18-AC-015 | STR-UX-008 | Current view shows meaningful objectives/targets and full measure definitions, with approval metadata/counts secondary; proposed update never replaces current facts before approval. |
| STR18-AC-016 | STR-UX-008 | Historical version and consumer snapshot remain exact and immutable; latest/current links are separate authorised choices; no achieved-result or procurement-progress badge is inferred. |
| STR18-AC-017 | STR-UX-009 | Failures name actual actionable missing/invalid values instead of technical green checklists; no false ready, saved, submitted, approved or empty result. |
| STR18-AC-018 | STR-UX-009 | Stale edits, unknown writes and access revocation have distinct safe recovery, accessible focus/status announcements and no protected-data retention or silent overwrite. |
| STR18-AC-019 | STR-UX-010 | All actors in §6.1 have the specified entry/read/action boundary; technical readers inspect every status and exact task without business controls. AO/HoD titles alone grant nothing. |
| STR18-AC-020 | STR-UX-010 | Permission resolves before protected render; route remains selected on denial. Full definitions/reasons, keyboard tree/move controls, narrow-screen layout and readable supporting detail pass implementation checks and representative-user review. |
| STR18-AC-021 | STR-UX-011 | Future profile blocks November approval of July-effective V2; separate immediate profile activates only on applicable date after all guards. Default V1 seed remains unchanged and profiles reset independently. |
| STR18-AC-022 | STR-UX-011 | Draft clock follows creation; review clock uses shared window; plan title/end date agree; comparison includes effective date. Dated actor authority is verified, not inferred from names. |
| STR18-AC-023 | STR-UX-012 | All 37 prior STR-AC IDs sit in the acceptance table and remain mapped; 24 additional criteria and all twelve approved UX decisions are traceable in this successor. |
| STR18-AC-024 | STR-UX-012 | One header/authority statement and current inspected owner citations govern. Completed standard actor additions are not falsely pending; remaining implementation, date-boundary, seed and usability evidence is explicit. |

---

## 16. Implementation and test constraints

The implementation baseline is KT-STD-001 §4; the verification protocol is KT-STD-001 §5; release evidence is KT-STD-001 §6.

### 16.1 Additional implementation rules

- Drop `procuring_entity_id` and `owner_org_unit_id` from `StrategicPlan`, together with every service parameter, filter, index, fixture, label and test that references them.
- Rename `financial_year_id` to `fiscal_year` and repoint it at the ERPNext `Fiscal Year`. Remove every reference to a KenTender `FinancialYear` DocType.
- Register Strategy Author and Strategy Approver in the AUTH-ADR-001 v1.7 business-role registry with `scope_type = Site-wide`. Remove Strategy capability strings, custom assignment lookups and every User Permission read from Strategy writes. The no-self-approval check reads the version's audit history.
- Register Strategy DocTypes in `kentender_scope_map` per AUTH-ADR-001 v1.7 §5.3. Because both roles are site-wide, the registered predicate reduces to an assignment existence check; it is still registered through both hooks so direct-route access is covered.
- Enforce STR-BR-004 with a database-level partial unique index or equivalent guard in addition to the approval-transaction check.
- Where the original controlled migration is still outstanding, normalize legacy statuses once: Draft and Returned → Draft; In Review, Awaiting Approval and Approved → Submitted for approval; Active → Active; Superseded and Archived → Superseded. Do not activate an old Approved version automatically.
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
12. Browser journeys: Strategy Author opens Portfolio → creates and saves a Draft → edits structure → submits; Strategy Approver reviews changes and complete submitted evidence without a mandatory tab tour → returns once → approves the corrected eligible submission; an ordinary read-only user opens permitted Active data without workflow actions; a technical reader opens every status and the exact task read-only; an actor with no Strategy assignment sees the Forbidden state with no data disclosure.

### 16.3 Additional release evidence

In addition to baseline evidence, retain failure/concurrency proofs for the actual save/submit RPC mapping, complete server comparisons, future-date refusal, immediate activation and historical snapshot preservation. Technical all-state/task-read tests, shared-window fixtures, keyboard/narrow-screen checks and representative-user findings are required before claiming usable implemented behaviour. An amendment approval is not a test result.


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

## 18. Traceability, complete changes and remaining dependencies

### 18.1 Governing inputs and precedence

| Inspected source | Controlling use / limit |
|---|---|
| Approved STR v1.7, 3 September 2026 | Full domain, lifecycle, 20 business rules, six commands, four consumer contracts, 37 acceptance criteria and default seed retained. Conflicting UI/fixture/editorial wording is reconciled here. |
| STR Usability Amendment v0.1, approved 13 September 2026 | All twelve STR-UX decisions folded into operative sections; no separate amendment-to-baseline reconciliation required by implementers. |
| KT-STD-001 v1.4, supplied in attachment bundle | Existing shell, permission-first entry, all-responsibility chrome, request concurrency/idempotency, shared actor register, §8.4A Strategy clock and verification discipline. |
| AUTH-ADR-001 v1.7, supplied in attachment bundle | Site-wide assigned Strategy roles, audit-based no-self-approval and §8 all-state technical detail, including edit/task-shaped routes. |
| Approved CFG v0.10 | Native FY/configuration owner contract, preserved native records and actual-adapter mapping; no Strategy FY catalogue, intake workflow or inferred native fields. |
| Approved NDS v1.12 | No requester-facing Strategy selection; approved usability reading principles. NDS acceptance and revision rules do not replace Strategy lifecycle. |
| Procurement Planning and Budget owner contracts | Their eligibility/selection/snapshot boundaries remain owned there. This file does not approve or rewrite proposed Planning v1.19 or Requisitions v1.8. |

Strategy owns definitions, hierarchy, targets, approval/activation and read contracts. Configuration/AUTH own setup and authority. Consumer modules own their transactions and snapshots. This document makes no current-law verification claim or new legal interpretation. Legacy migration directions apply only to verified outstanding cutover, not repeated cleanup or historical-data rewriting.

### 18.2 Full v1.8 change register for re-implementation

The twelve rows are the complete approved amendment-to-baseline change set. The historical removal/scope dispositions in §1.1 remain separately traceable; they are not newly reopened decisions. Each row identifies the complete implementation change, operative sections and verification IDs.

| ID / approved source | Prior issue | Complete required change | Locations | Verification |
|---|---|---|---|---|
| STR18-CHG-001 / STR-UX-001 | Portfolio, My work and task entry (§§10, 11.1, 12.1) | Strategic plans; names before references; useful Current/Previous/waiting labels; queue action Review. Keep existing routes and one underlying work set. | §§4.7, 10, 11.1, 12.1 | STR18-AC-001–002; Author and Approver locate the right work; reader counts match scope; clicking Review does not decide. |
| STR18-CHG-002 / STR-UX-002 | Plan identity and successor entry (§§4.1–4.2, 11.2, 12.2) | Plain plan-type labels; conditional Main plan; Create plan and add objectives; Update plan with retained-current explanation. No duplicate first-version dates or empty generated-ID input. | §§4.7, 8.1–8.2, 11.2–11.3, 12.2 | STR18-AC-003–004; Both plan roles work; same keys/enums; confirmed save resumes the same record; Active remains immutable. |
| STR18-CHG-003 / STR-UX-003 | Hierarchy authoring (§§5.2, 11.4, 12.3) | Expose Add objective directly under Programme; optional Add sub-programme; explicit typed add actions, sibling move controls and named deletion. | §§5, 11.4, 12.3 | STR18-AC-005–006; Both permitted tree paths work; no placeholder layer, cross-version move or cascade bypass; keyboard reorder and post-submission deletion guard hold. |
| STR18-CHG-004 / STR-UX-004 | Save, submit and correction (§§8, 11.4–11.5, 12.2–12.3) | One structure Save changes scope; submit saves pending edits then submits; direct returned-Draft editing with exact comment. Specify actual command/token and unknown-outcome recovery. Inline pending target editing shares the one structure save; exact command orchestration is specified. | §§8.2, 11.4–11.5, 12.2–12.3 | STR18-AC-007–008; Partial save/submit failure, stale tree, double click and lost response create no duplicates and preserve permitted work. No claim that separate commands are atomic. |
| STR18-CHG-005 / STR-UX-005 | Indicator and Target form (§§4.4–4.5, 11.5, 12.3) | How it is measured; Target; Financial year or Target date; inherited unit. Render complete definitions in author and reviewer detail. | §§4.4–4.7, 11.5, 12.3 | STR18-AC-009–010; Both period modes are usable; exactly one stored period; duplicate/percentage/unit rules; no actual result or duplicate unit. |
| STR18-CHG-006 / STR-UX-006 | Approval composition (§§11.6–11.9, 12.4) | Changes first for successor; full plan first for initial submission; compare applicability dates and all changed content against server baseline. Full proposed detail and history remain available. | §§8.3, 11.6–11.9, 12.4 | STR18-AC-011–012; No mandatory tab tour; no missing definition, removed item or changed date; route remains bound to the exact submitted version. |
| STR18-CHG-007 / STR-UX-007 | Decision wording and consequences (§§5.1, 11.6, 12.4) | Approve and use plan / Approve changes and use plan; Return for correction with existing 10–500 character reason. Single deliberate decision and visible consequences. | §§5, 8.1, 11.6, 11.9, 12.4 | STR18-AC-013–014; No added approval, Reject, score or checkbox; immediate activation, no-self-approval and atomic supersession remain enforced. |
| STR18-CHG-008 / STR-UX-008 | Current and historical reading (§§3, 7, 11.3, 12.2, 12.6) | Current plan facts first; pending update separately; history and approval metadata structured; consumer ownership and exact saved snapshots explicit. | §§7, 11.3, 12.2, 12.6, 13 | STR18-AC-015–016; Approver/readers understand current versus proposed; historical evidence never silently redirects or changes; no result dashboard. |
| STR18-CHG-009 / STR-UX-009 | Errors, readiness and recovery (§§9, 11.10, 12.3–12.5) | Actual actionable failures instead of a technical green checklist; plain closed/unknown/stale/overlap/permission text, same codes and protections. | §§8.2–8.3, 9, 11.10, 12.5 | STR18-AC-017–018; No false Ready, saved/submitted/approved success or unknown-as-absence; input and access revocation handled safely. |
| STR18-CHG-010 / STR-UX-010 | All actors and shared readability (§§6, 10–12, 15) | Use the full actor matrix, shared readable detail, role-specific actions, technical-read recognition and permission-first rendering; preserve existing shell and accessible supporting detail. Apply the inspected AUTH v1.7 all-status/task technical-read exception. | §§6.1, 10–12, 15–16 | STR18-AC-019–020; Author, Approver, dual-role, consumer, Auditor and technical-reader journeys checked; no title-based AO authority, hidden denied route or disclosure flash. |
| STR18-CHG-011 / STR-UX-011 | Fixture validity and comparison (§§11.2, 11.4–11.9, 14.4) | Keep July-2027-effective November review as blocked; declare separate immediate-effective positive fixture. Move Draft artboard clock after 13:10 creation. Include date changes in comparison. Reconcile new-plan title 2028–2032 with end date 30 Jun 2033: proposed display title 2028–2033. Approval example uses 11:15 EAT to match the inspected shared window. | §§11.2, 11.4–11.9, 14.4 | STR18-AC-021–022; No future activation, pre-creation screen or “only target changed” claim. Verify actor authority at each fixture instant; preserve default Version 1 and isolate each profile. |
| STR18-CHG-012 / STR-UX-012 | Document authority and acceptance layout (§§header, 11.10, 15, 18–19) | Remove duplicate/conflicting change-type rows and v1.6-only approval-effect text in the successor. Put STR-AC-035–037 in the acceptance table. Reconcile forbidden-state composition with permission-first rule; verify current owner citations without rewriting other modules. | §§header, 15, 18–19 | STR18-AC-023–024; All 37 existing AC IDs remain mapped; new usability criteria added; proposed/approved status unambiguous; owner and shared-seed dependencies remain explicit. |

### 18.3 Owner dependencies and release evidence

| ID | Owner / dependency | Required concrete evidence |
|---|---|---|
| STR18-XD-001 | Strategy UI/services | Inspect actual save/create/submit response IDs, token granularity, idempotency storage and authorised request-result replay. Prove partial and unknown outcomes; no asserted existing API is invented here. |
| STR18-XD-002 | Strategy approval/date semantics | Document actual date-versus-instant boundary and predecessor effective-to closure under the transaction lock. Prove immediate applicability, no overlapping current authority, full rollback, historical source integrity and no future scheduler. |
| STR18-XD-003 | Strategy/KT-STD/SEED fixture owner | Reuse existing shared actors; verify effective assignments at 2023 baseline events and 2026 scenarios. Isolate V2 positive/negative profiles and supporting/direct-Objective variants; publish corrected clocks without mutating default source facts. No fabricated approval by Administrator. |
| STR18-XD-004 | AUTH/Strategy | Prove hooks cover all routes, counts and APIs; technical readers access Draft, Submitted, Active, Superseded and exact task details without mutation. No stale three-status allow-list or blanket approval-route denial. |
| STR18-XD-005 | CFG/Strategy adapter | Verify actual native FY IDs, eligibility projection and supported year/date boundary semantics; no first-year fallback or new catalogue. Indicator unit/target rules remain Strategy-owned; do not assume Percentage is a selectable procurement UOM. |
| STR18-XD-006 | Strategy/Planning/Budget | Consumer tests for exact Objective eligibility and immutable/idempotent snapshots at the owner approval boundary, including source changes and stale/ambiguous contexts. No downstream direct-table access or implied adoption by proposed sibling documents. |
| STR18-XD-007 | Strategy data/migration owner | Inspect outstanding legacy cleanup, existing Draft concurrency policy, submitted-history capture, accepted identities and lineage before migration. Preserve evidence; no repeated status migration, silent duplicate successor policy or deletion after first submission. |
| STR18-XD-008 | Product/UI verification | Representative Author/Approver/reader journeys, complete comparisons, full definition readability, keyboard/contrast and narrow-screen evidence. Record hesitation, misunderstanding and recovery; specification completeness is not tested usability. |

No automatic scheduled activation, additional approval stage, performance-result capture, attachments or corrective-action facility is authorised. Those remain outside MVP scope unless separately specified and approved. Current owner citations do not certify deployment, migration or legal compliance.

---

## 19. Approval effect

The Project Owner approved STR Usability Amendment v0.1 (STR-UX-001–012) on **13 September 2026** and directed incorporation into the full document. This **v1.8 consolidated specification** records the approved baseline and those approved changes as one implementation reference, superseding v1.7 and earlier conflicting Strategy specifications. It does not require implementers to merge a separate usability overlay into an older UI contract.

The complete document retains the Strategy domain, four-state lifecycle, six commands, four consumer contracts, 20 business rules and 37 prior acceptance IDs. It adds 24 usability/consistency criteria, producing **61 acceptance criteria**, with a **12-row full change register** and eight explicit implementation/owner evidence dependencies. Plain user labels do not rename stored identities or introduce additional business decisions.

Approval records requirements and design decisions. It does not establish deployed code, completed migration, passing transaction/consumer/browser tests, representative-user acceptance, verified current law or closure of §18.3. Implementers record concrete evidence against this document; other modules retain their own approval status and ownership.
