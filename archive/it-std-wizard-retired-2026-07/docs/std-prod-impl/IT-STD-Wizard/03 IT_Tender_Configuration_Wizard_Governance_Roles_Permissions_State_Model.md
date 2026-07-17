# IT Tender Configuration Wizard — Governance, Roles, Permissions, and State Model

**Project:** KenTender e-Procurement System  
**Module:** Standard Tender Document Engine / IT Tender Configuration Wizard  
**STD Family:** Procurement of Information Technology  
**Package Baseline:** `KE-PPRA-IT-2022-04`  
**Document Type:** Governance, Roles, Permissions, and State Model  
**Version:** 1.0 Draft  
**Status:** Implementation Design Draft  

---

## 1. Purpose

This document defines the governance model for the IT Tender Configuration Wizard. It converts the IT Tender Configuration Wizard PRD and Domain Model into an enforceable operational model covering:

1. Tender configuration lifecycle states.
2. State-transition rules.
3. Approval gates.
4. Role definitions.
5. Permission matrix.
6. Segregation-of-duty controls.
7. Immutable publication rules.
8. Addendum and supersession governance.
9. Validation gates.
10. Audit-event requirements.
11. Exception handling.
12. Smoke contracts and acceptance criteria.

This document is intentionally written so that the governance model can be reused by other STD-specific wizards. IT-specific details are included where the IT STD requires special handling, but the governing pattern is general.

---

## 2. Governance Principle

The wizard must not become a free-form tender-document editor.

The wizard is a controlled configuration interface over an approved STD template version. It allows authorized users to supply tender-specific values, technical requirements, implementation schedules, price schedule structures, evaluation settings, and contract parameters only within the mutability limits defined by the active STD package.

The controlling rule is:

> **The STD template version is the legal source of structure. The tender wizard only creates a tender-specific instance of that approved structure.**

Therefore:

1. Locked STD text is never editable from the wizard.
2. Controlled parameters are editable only through typed fields.
3. Requirements are authored only through controlled requirement-composer objects.
4. Evaluation criteria may only be configured where the STD package permits.
5. Published generated tender artifacts are immutable.
6. Any post-publication change must follow addendum governance.
7. Every generated artifact must be traceable to the STD version, tender configuration values, render profile, validation run, approval chain, and package hash.

---

## 3. Relationship to STD Engine Core Governance

The IT Tender Configuration Wizard is subordinate to the STD Engine Core.

The STD Engine Core controls:

1. STD family registration.
2. STD version import.
3. Source document traceability.
4. Clause and section mutability.
5. Master rules.
6. Master forms.
7. Master render blocks.
8. STD version lifecycle.
9. Activation and supersession of master template versions.

The IT Tender Configuration Wizard controls:

1. Tender-specific configuration values.
2. IT requirement authoring.
3. Implementation schedule authoring.
4. System inventory authoring.
5. Price schedule configuration.
6. Evaluation configuration within STD limits.
7. SCC parameter completion.
8. Tender-specific validation.
9. Tender package review.
10. Generation of tender publication bundle.
11. Addendum impact handling after publication.

The wizard cannot override STD Engine Core governance.

---

## 4. Generalized Wizard Governance Pattern

The following model should apply to all STD-specific configuration wizards.

| Layer | Scope | Example for IT STD |
|---|---|---|
| STD Master Layer | Defines approved structure and legal rules | IT STD package `KE-PPRA-IT-2022-04` |
| Tender Instance Layer | Holds one tender's configuration values | NSSF-style ERP tender configuration |
| Validation Layer | Tests completeness, consistency, and rule compliance | Tender security, dates, scoring totals, price schedule linkage |
| Review Layer | Performs internal procurement, technical, finance, legal, and approval review | IT requirements, SCC values, evaluation criteria |
| Render Layer | Generates draft and publication artifacts | Tender document, submission forms, evaluation matrix, contract drafts |
| Publication Layer | Freezes tender artifacts and exposes them to suppliers | Published tender bundle |
| Addendum Layer | Manages post-publication changes | Revised deadline, corrected requirement, amended price schedule |
| Audit Layer | Records evidence for every configuration, validation, review, render, publication, and addendum event | Full immutable audit trail |

---

## 5. Primary Actors

### 5.1 System Actors

| Actor | Description |
|---|---|
| STD Engine Core | Provides active STD template version, mutability map, parameter definitions, rules, forms, render blocks, and validation contracts. |
| IT Tender Configuration Wizard | Allows authorized tender users to configure one IT tender instance. |
| Validation Engine | Executes mandatory, warning, cross-field, and publication-blocking validations. |
| Render Engine | Generates preview and publication-ready tender artifacts. |
| Audit Service | Captures immutable event records. |
| Notification Service | Sends workflow and review notifications. |
| Tender Management Module | Consumes the approved tender configuration and published tender bundle. |
| Supplier Portal | Consumes published forms, price schedules, requirements, and submission schemas. |
| Evaluation Module | Consumes generated evaluation matrix and supplier responses. |
| Contract Management Module | Consumes award and contract carry-forward data. |

### 5.2 Human Actors

| Role | Description |
|---|---|
| Procurement Preparer | Creates and edits tender configuration before submission for review. |
| Procurement Reviewer | Reviews tender configuration for procurement compliance. |
| Technical Owner | Owns IT requirements, system inventory, implementation schedule, technical compliance matrix, and acceptance criteria. |
| Technical Reviewer | Reviews IT technical content for completeness, neutrality, feasibility, and evaluability. |
| Finance Reviewer | Reviews price schedule structure, budget alignment, payment milestones, taxes, guarantees, retention, and recurrent-cost handling. |
| Legal Reviewer | Reviews SCC parameters, contract carry-forward, IP, confidentiality, limitation of liability, dispute resolution, securities, and change-order terms. |
| Procurement Approver | Approves configuration for publication on behalf of the procuring entity. |
| Accounting Officer / Authorized Officer | Final accountable authority for publication where required by organization policy. |
| Internal Auditor | Read-only reviewer of configuration, validation, approval, and publication records. |
| System Administrator | Manages technical access but cannot approve procurement content by system-admin privilege alone. |
| STD Administrator | Manages STD packages, but cannot alter a tender instance after publication except through governed addendum paths. |

---

## 6. Role Definitions

### 6.1 Procurement Preparer

The Procurement Preparer initiates and maintains the tender configuration draft.

Responsibilities:

1. Create tender instance from active STD version.
2. Complete tender identity fields.
3. Configure procurement method and participation settings.
4. Complete TDS values.
5. Coordinate input from technical, finance, and legal users.
6. Run validations.
7. Resolve validation warnings and blockers.
8. Submit the tender configuration for review.

Restrictions:

1. Cannot activate an STD version.
2. Cannot modify locked STD text.
3. Cannot approve own tender configuration.
4. Cannot publish without required approvals.
5. Cannot modify published tender bundle directly.

### 6.2 Technical Owner

The Technical Owner owns the substance of the information system requirements.

Responsibilities:

1. Define functional requirements.
2. Define architectural and integration requirements.
3. Define performance, security, availability, and service requirements.
4. Define implementation schedule and acceptance milestones.
5. Define system inventory items.
6. Define supplier conformance response requirements.
7. Provide technical review responses.

Restrictions:

1. Cannot approve procurement compliance.
2. Cannot approve legal/SCC terms unless separately assigned legal authority.
3. Cannot publish tender bundle by technical-owner role alone.

### 6.3 Technical Reviewer

The Technical Reviewer checks technical requirements for quality and governance compliance.

Responsibilities:

1. Confirm requirements are clear, measurable, supplier-facing, and evaluable.
2. Confirm requirements avoid unjustified brand restriction unless properly justified and allowed.
3. Confirm implementation schedule is feasible.
4. Confirm system inventory and price schedule linkage.
5. Confirm acceptance tests and conformance matrix are complete.

Restrictions:

1. Cannot edit requirements during review unless explicitly assigned editor permissions.
2. Cannot approve procurement or legal sufficiency.

### 6.4 Procurement Reviewer

The Procurement Reviewer checks the tender configuration for procurement-law and STD compliance.

Responsibilities:

1. Review TDS values.
2. Review eligibility and qualification criteria.
3. Review evaluation criteria.
4. Review participation restrictions, reservations, alternatives, lots, tender security, clarifications, and submission rules.
5. Confirm validation findings are resolved or accepted according to policy.
6. Recommend approval or return for correction.

Restrictions:

1. Cannot approve final publication if also acting as preparer for the same tender, unless policy explicitly permits and the system records an override.
2. Cannot edit locked STD text.

### 6.5 Finance Reviewer

The Finance Reviewer checks financial structure.

Responsibilities:

1. Confirm price schedule configuration.
2. Confirm recurrent cost treatment.
3. Confirm VAT/tax handling.
4. Confirm payment milestones.
5. Confirm performance security, advance payment security, retention, warranty, and budget alignment.
6. Confirm abnormally low/high tender benchmark data exists where required.

Restrictions:

1. Cannot approve technical requirements by finance role alone.
2. Cannot publish tender bundle.

### 6.6 Legal Reviewer

The Legal Reviewer checks legal and contract configuration.

Responsibilities:

1. Review SCC parameter values.
2. Review IP, licensing, confidentiality, limitation of liability, warranty, acceptance, termination, dispute resolution, and change-order controls.
3. Confirm contract carry-forward fields.
4. Confirm addendum legal sufficiency where applicable.

Restrictions:

1. Cannot alter locked GCC text.
2. Cannot publish tender bundle unless separately assigned authorized officer role.

### 6.7 Procurement Approver

The Procurement Approver makes the formal approval decision for the tender configuration before publication.

Responsibilities:

1. Review completed configuration summary.
2. Confirm required reviews are completed.
3. Confirm blockers are resolved.
4. Approve or reject publication readiness.

Restrictions:

1. Cannot approve a configuration with unresolved hard blockers.
2. Cannot bypass locked-template controls.
3. Cannot approve if segregation-of-duty rules prohibit approval.

### 6.8 Accounting Officer / Authorized Officer

The Accounting Officer or Authorized Officer gives final authorization where organizational policy requires it.

Responsibilities:

1. Final publication authorization.
2. High-impact addendum authorization.
3. Cancellation or withdrawal authorization where applicable.

Restrictions:

1. Cannot publish an invalid bundle.
2. Cannot alter active STD structure.

### 6.9 Internal Auditor

The Internal Auditor reviews evidence and governance compliance.

Responsibilities:

1. View tender configuration history.
2. View validation runs.
3. View approvals and rejections.
4. View render hashes and publication evidence.
5. Export audit reports.

Restrictions:

1. Read-only access.
2. No content editing.
3. No approval actions unless separately assigned operational role outside audit role.

### 6.10 System Administrator

The System Administrator manages user access, system configuration, and technical operations.

Responsibilities:

1. Manage access assignments subject to policy.
2. Maintain system health.
3. Support technical troubleshooting.
4. View logs needed for support.

Restrictions:

1. Cannot use administrator privilege to approve procurement content.
2. Cannot modify published artifacts.
3. Cannot bypass audit logging.
4. Cannot impersonate approvers without explicit audited break-glass process.

---

## 7. Tender Configuration State Model

### 7.1 Primary State Machine

The IT Tender Configuration Wizard uses the following primary lifecycle:

```text
NOT_STARTED
  -> DRAFT
  -> CONFIGURATION_IN_PROGRESS
  -> VALIDATION_IN_PROGRESS
  -> VALIDATION_FAILED
  -> READY_FOR_REVIEW
  -> PROCUREMENT_REVIEW
  -> TECHNICAL_REVIEW
  -> FINANCE_REVIEW
  -> LEGAL_REVIEW
  -> REVIEW_RETURNED
  -> APPROVAL_PENDING
  -> APPROVED_FOR_PUBLICATION
  -> RENDERING_FOR_PUBLICATION
  -> PUBLICATION_READY
  -> PUBLISHED
  -> ADDENDUM_DRAFT
  -> ADDENDUM_REVIEW
  -> ADDENDUM_APPROVED
  -> ADDENDUM_PUBLISHED
  -> CLOSED
```

A tender instance may also enter terminal or exception states:

```text
CANCELLED
WITHDRAWN_BEFORE_PUBLICATION
SUPERSEDED_BY_NEW_TENDER
ARCHIVED
LOCKED_FOR_INVESTIGATION
```

### 7.2 State Definitions

| State | Meaning | Editable? | Supplier Visible? |
|---|---|---:|---:|
| `NOT_STARTED` | No tender instance has been created. | No | No |
| `DRAFT` | Tender instance exists but minimal data only. | Yes | No |
| `CONFIGURATION_IN_PROGRESS` | Tender-specific data is being entered. | Yes | No |
| `VALIDATION_IN_PROGRESS` | System is executing validation checks. | Temporarily locked | No |
| `VALIDATION_FAILED` | One or more blocking validation findings exist. | Yes, only to resolve findings | No |
| `READY_FOR_REVIEW` | Required fields complete and no blocking validation failures. | Limited | No |
| `PROCUREMENT_REVIEW` | Procurement review is active. | No, except returned changes | No |
| `TECHNICAL_REVIEW` | Technical review is active. | No, except returned changes | No |
| `FINANCE_REVIEW` | Finance review is active. | No, except returned changes | No |
| `LEGAL_REVIEW` | Legal review is active. | No, except returned changes | No |
| `REVIEW_RETURNED` | Review has returned the configuration for correction. | Yes, scoped to returned issues | No |
| `APPROVAL_PENDING` | All required reviews are complete; final approval is pending. | No | No |
| `APPROVED_FOR_PUBLICATION` | Final approval granted; ready to render. | No | No |
| `RENDERING_FOR_PUBLICATION` | Publication bundle is being generated and hashed. | No | No |
| `PUBLICATION_READY` | Rendered bundle exists and awaits publication action. | No | No |
| `PUBLISHED` | Tender is published; artifacts are immutable. | No direct editing | Yes |
| `ADDENDUM_DRAFT` | Post-publication change is being prepared. | Only addendum draft | Published base remains visible |
| `ADDENDUM_REVIEW` | Addendum is under review. | No, except return cycle | Published base remains visible |
| `ADDENDUM_APPROVED` | Addendum approved and ready for rendering/publication. | No | Published base remains visible |
| `ADDENDUM_PUBLISHED` | Addendum has been published and linked to base bundle. | No direct editing | Yes |
| `CLOSED` | Tender configuration lifecycle is complete. | No | As per procurement record rules |
| `CANCELLED` | Tender stopped before completion. | No, except cancellation notes | Depends on publication status |
| `WITHDRAWN_BEFORE_PUBLICATION` | Tender abandoned before publication. | No | No |
| `SUPERSEDED_BY_NEW_TENDER` | Replaced by a new tender instance. | No | Depends on publication status |
| `ARCHIVED` | Retained as historical/audit record. | No | As per archive policy |
| `LOCKED_FOR_INVESTIGATION` | Locked due to audit/legal/integrity issue. | No | Depends on publication status |

---

## 8. Transition Rules

### 8.1 Core Transition Table

| From State | To State | Trigger | Required Role | Blocking Conditions |
|---|---|---|---|---|
| `NOT_STARTED` | `DRAFT` | Create tender from active STD | Procurement Preparer | No active STD version; user lacks permission |
| `DRAFT` | `CONFIGURATION_IN_PROGRESS` | Begin configuration | Procurement Preparer | STD version inactive/superseded before use |
| `CONFIGURATION_IN_PROGRESS` | `VALIDATION_IN_PROGRESS` | Run validation | Procurement Preparer / Technical Owner | Required minimum data absent |
| `VALIDATION_IN_PROGRESS` | `VALIDATION_FAILED` | Blocking findings detected | System | None |
| `VALIDATION_IN_PROGRESS` | `READY_FOR_REVIEW` | No blocking findings | System | None |
| `VALIDATION_FAILED` | `CONFIGURATION_IN_PROGRESS` | Correct findings | Procurement Preparer / assigned owner | Instance locked or returned scope exceeded |
| `READY_FOR_REVIEW` | `PROCUREMENT_REVIEW` | Submit for procurement review | Procurement Preparer | Required technical/finance/legal prechecks incomplete if configured as mandatory |
| `PROCUREMENT_REVIEW` | `TECHNICAL_REVIEW` | Route to technical review | Procurement Reviewer | Procurement reviewer rejects before technical review |
| `TECHNICAL_REVIEW` | `FINANCE_REVIEW` | Technical review complete | Technical Reviewer | Technical review rejects or requires correction |
| `FINANCE_REVIEW` | `LEGAL_REVIEW` | Finance review complete | Finance Reviewer | Finance review rejects or requires correction |
| `LEGAL_REVIEW` | `APPROVAL_PENDING` | Legal review complete | Legal Reviewer | Legal review rejects or requires correction |
| Any Review State | `REVIEW_RETURNED` | Return for correction | Active Reviewer | Return reason missing |
| `REVIEW_RETURNED` | `CONFIGURATION_IN_PROGRESS` | Reopen for correction | Procurement Preparer | Returned scope missing; locked published state |
| `APPROVAL_PENDING` | `APPROVED_FOR_PUBLICATION` | Final approval | Procurement Approver / Authorized Officer | Hard blockers; SoD violation; expired validation run |
| `APPROVED_FOR_PUBLICATION` | `RENDERING_FOR_PUBLICATION` | Generate publication bundle | Procurement Preparer / System | Approval missing; render profile invalid |
| `RENDERING_FOR_PUBLICATION` | `PUBLICATION_READY` | Render and hash complete | System | Render error; hash error; missing required artifact |
| `PUBLICATION_READY` | `PUBLISHED` | Publish tender | Authorized Publisher | Publication authorization missing; bundle hash mismatch |
| `PUBLISHED` | `ADDENDUM_DRAFT` | Initiate addendum | Procurement Preparer / Authorized Officer | Tender closed; addendum prohibited by tender state |
| `ADDENDUM_DRAFT` | `ADDENDUM_REVIEW` | Submit addendum for review | Procurement Preparer | Addendum impact analysis incomplete |
| `ADDENDUM_REVIEW` | `ADDENDUM_APPROVED` | Approve addendum | Required Reviewers / Approver | Hard blockers; missing addendum reason |
| `ADDENDUM_APPROVED` | `ADDENDUM_PUBLISHED` | Publish addendum | Authorized Publisher | Addendum render/hash failure |
| `PUBLISHED` or `ADDENDUM_PUBLISHED` | `CLOSED` | Close tender configuration lifecycle | Procurement Approver / System | Active addendum draft exists |

### 8.2 Parallel Review Support

The system may support sequential or parallel reviews.

Default implementation should support both, but configuration should determine workflow behavior.

| Review Mode | Behavior |
|---|---|
| Sequential | Procurement → Technical → Finance → Legal → Approval |
| Parallel | Procurement, Technical, Finance, and Legal reviews run simultaneously after `READY_FOR_REVIEW` |
| Conditional | Only required review tracks are activated based on tender characteristics |

For IT tenders, the recommended default is:

```text
READY_FOR_REVIEW
  -> PROCUREMENT_REVIEW
  -> TECHNICAL_REVIEW
  -> FINANCE_REVIEW
  -> LEGAL_REVIEW
  -> APPROVAL_PENDING
```

Reason: IT tenders usually require deep dependency between technical requirements, pricing, implementation milestones, acceptance criteria, IP treatment, and SCC values.

### 8.3 Review Return Rules

When a review returns a configuration:

1. The reviewer must select a return category.
2. The reviewer must enter a return reason.
3. The reviewer must identify affected wizard sections.
4. The system must reopen only the affected sections unless the return category requires broader reopening.
5. Previously approved sections remain approved unless the change impacts them.
6. Any edited returned section must trigger validation again.
7. Any material change after review must invalidate affected downstream approvals.

Return categories:

| Category | Meaning | Approval Impact |
|---|---|---|
| Procurement correction | TDS/evaluation/eligibility/procurement method issue | Procurement approval invalidated |
| Technical correction | Requirements, inventory, implementation, acceptance issue | Technical approval invalidated |
| Financial correction | Price schedule, milestones, security, retention, tax issue | Finance approval invalidated |
| Legal correction | SCC, contract, IP, liability, dispute, change order issue | Legal approval invalidated |
| Cross-cutting correction | Affects multiple review domains | All affected approvals invalidated |
| Editorial correction | Non-substantive correction | Reviewer may mark no reapproval required if policy allows |

---

## 9. Wizard Section State Model

Each major wizard section has its own subsection state. This avoids making the entire tender configuration appear complete when critical sections are still unfinished.

### 9.1 Section States

```text
NOT_STARTED
IN_PROGRESS
COMPLETE
VALIDATED
RETURNED_FOR_CORRECTION
APPROVED
LOCKED
SUPERSEDED_BY_ADDENDUM
```

### 9.2 Section State Table

| Wizard Section | Required Owner | Required Review Track | Locking Point |
|---|---|---|---|
| Tender Identity | Procurement Preparer | Procurement | Publication |
| Procurement Method and Participation | Procurement Preparer | Procurement | Approval for publication |
| Dates, Clarifications, and Submission | Procurement Preparer | Procurement | Publication; addendum after publication |
| Tender Security / Professional Indemnity | Procurement Preparer / Finance Reviewer | Procurement + Finance | Approval for publication |
| Lots, Alternatives, Reservations | Procurement Preparer | Procurement | Approval for publication |
| IT Requirements | Technical Owner | Technical + Procurement | Approval for publication |
| Technical Requirements | Technical Owner | Technical | Approval for publication |
| Implementation Schedule | Technical Owner | Technical + Finance | Approval for publication |
| System Inventory | Technical Owner | Technical + Finance | Approval for publication |
| Price Schedule Setup | Procurement Preparer / Finance Reviewer | Finance + Procurement | Approval for publication |
| Evaluation Criteria | Procurement Preparer / Technical Owner | Procurement + Technical | Approval for publication |
| Qualification Requirements | Procurement Preparer | Procurement | Approval for publication |
| Contract / SCC Parameters | Procurement Preparer / Legal Reviewer | Legal + Finance where financial | Approval for publication |
| Forms and Evidence | Procurement Preparer | Procurement + Technical where technical forms | Approval for publication |
| Validation and Preview | System / Procurement Preparer | All | Publication |
| Publication Bundle | System | Authorized Publisher | Immutable on publication |

---

## 10. Approval Gates

### 10.1 Gate 1 — Creation Gate

A tender configuration may be created only when:

1. The selected STD template version is active.
2. The STD version is not archived.
3. The user has create permission.
4. The tender is linked to a valid procurement plan item or approved procurement initiation record, where required by the platform.
5. No conflicting tender instance already exists for the same procurement plan item unless multiple tender instances are allowed.

### 10.2 Gate 2 — Configuration Completeness Gate

Before review, the configuration must have:

1. Tender identity.
2. Procuring entity details.
3. Tender name and number.
4. Procurement method.
5. Participation settings.
6. Dates and submission rules.
7. TDS values.
8. Required IT requirement groups.
9. Required implementation milestones.
10. Required system inventory and/or price schedule configuration.
11. Evaluation configuration.
12. SCC values.
13. Required forms and evidence selections.

### 10.3 Gate 3 — Validation Gate

Before `READY_FOR_REVIEW`, validation must confirm:

1. No unresolved `BLOCKER` findings.
2. No unresolved `ERROR` findings.
3. All mandatory fields are complete.
4. Date rules pass.
5. Price schedule rules pass.
6. Evaluation scoring totals pass.
7. Mandatory requirement groups are present.
8. Technical requirement identifiers are unique.
9. Implementation milestones are coherent.
10. System inventory items link to price schedules where required.
11. SCC values are complete.
12. Render blocks can be resolved.

### 10.4 Gate 4 — Review Gate

Before `APPROVAL_PENDING`, required review tracks must be complete.

Default IT review tracks:

| Review Track | Mandatory? | Reason |
|---|---:|---|
| Procurement Review | Yes | Confirms procurement procedure and STD compliance |
| Technical Review | Yes | Confirms IT requirements and acceptance are complete/evaluable |
| Finance Review | Yes | Confirms price schedule, budget, payment, security, retention, recurrent cost treatment |
| Legal Review | Yes | Confirms SCC, IP, liability, confidentiality, acceptance, change-order and dispute terms |

### 10.5 Gate 5 — Final Approval Gate

Before `APPROVED_FOR_PUBLICATION`, the system must confirm:

1. All required reviews are approved.
2. No review return remains unresolved.
3. No validation blocker exists.
4. Validation run is current.
5. The STD version is still valid for the tender instance.
6. Segregation-of-duty checks pass.
7. Required approval authority is present.
8. Publication checklist is complete.

### 10.6 Gate 6 — Render Gate

Before `PUBLICATION_READY`, the system must confirm:

1. All render blocks resolve.
2. No locked clause is missing.
3. All configured values render into expected locations.
4. All required forms are generated.
5. All required price schedules are generated.
6. All required requirement tables are generated.
7. Contract carry-forward fields are preserved.
8. Generated bundle hash is computed.
9. Render manifest is stored.

### 10.7 Gate 7 — Publication Gate

Before `PUBLISHED`, the system must confirm:

1. Publication-ready bundle exists.
2. Bundle hash matches render manifest.
3. Publication actor is authorized.
4. Publication timestamp is captured.
5. Supplier-visible artifact list is complete.
6. Internal-only materials are excluded.
7. Public notice and tender document references are consistent.
8. Audit event is written before external visibility is enabled.

### 10.8 Gate 8 — Addendum Gate

Before an addendum is published, the system must confirm:

1. Base tender is already published.
2. Addendum reason is recorded.
3. Affected sections are identified.
4. Impacted render blocks are identified.
5. Affected supplier submission schemas are identified.
6. Whether deadline extension is required has been assessed.
7. Required reviews are complete.
8. Addendum bundle hash is computed.
9. Addendum is linked to base publication bundle.
10. Supplier notification event is recorded.

---

## 11. Permission Matrix

### 11.1 Permission Categories

| Permission Code | Description |
|---|---|
| `it_tender.create` | Create IT tender configuration instance |
| `it_tender.view` | View tender configuration |
| `it_tender.edit.identity` | Edit tender identity fields |
| `it_tender.edit.tds` | Edit TDS fields |
| `it_tender.edit.requirements` | Edit IT requirements |
| `it_tender.edit.schedule` | Edit implementation schedule |
| `it_tender.edit.inventory` | Edit system inventory |
| `it_tender.edit.price_schedule` | Edit price schedule setup |
| `it_tender.edit.evaluation` | Edit evaluation settings |
| `it_tender.edit.scc` | Edit SCC/contract parameters |
| `it_tender.edit.forms` | Edit form/evidence configuration |
| `it_tender.validate` | Run validation |
| `it_tender.preview` | Generate preview |
| `it_tender.submit_review` | Submit configuration for review |
| `it_tender.review.procurement` | Perform procurement review |
| `it_tender.review.technical` | Perform technical review |
| `it_tender.review.finance` | Perform finance review |
| `it_tender.review.legal` | Perform legal review |
| `it_tender.return_review` | Return configuration for correction |
| `it_tender.approve_publication` | Approve for publication |
| `it_tender.render_publication` | Generate publication bundle |
| `it_tender.publish` | Publish tender bundle |
| `it_tender.create_addendum` | Create addendum draft |
| `it_tender.review_addendum` | Review addendum |
| `it_tender.approve_addendum` | Approve addendum |
| `it_tender.publish_addendum` | Publish addendum |
| `it_tender.cancel` | Cancel tender configuration |
| `it_tender.archive` | Archive tender configuration |
| `it_tender.audit_view` | View full audit history |
| `it_tender.audit_export` | Export audit package |
| `it_tender.break_glass` | Emergency controlled access |

### 11.2 Role-Permission Matrix

| Permission | Preparer | Technical Owner | Technical Reviewer | Procurement Reviewer | Finance Reviewer | Legal Reviewer | Approver | Authorized Officer | Auditor | System Admin | STD Admin |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `it_tender.create` | Yes | No | No | Yes | No | No | No | No | No | No | No |
| `it_tender.view` | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Limited | Yes |
| `it_tender.edit.identity` | Yes | No | No | Conditional | No | No | No | No | No | No | No |
| `it_tender.edit.tds` | Yes | No | No | Conditional | No | No | No | No | No | No | No |
| `it_tender.edit.requirements` | Conditional | Yes | No | No | No | No | No | No | No | No | No |
| `it_tender.edit.schedule` | Conditional | Yes | No | No | Conditional | No | No | No | No | No | No |
| `it_tender.edit.inventory` | Conditional | Yes | No | No | Conditional | No | No | No | No | No | No |
| `it_tender.edit.price_schedule` | Yes | Conditional | No | Conditional | Yes | No | No | No | No | No | No |
| `it_tender.edit.evaluation` | Yes | Conditional | No | Conditional | Conditional | No | No | No | No | No | No |
| `it_tender.edit.scc` | Conditional | No | No | Conditional | Conditional | Yes | No | No | No | No | No |
| `it_tender.edit.forms` | Yes | Conditional | No | Conditional | No | Conditional | No | No | No | No | No |
| `it_tender.validate` | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Read Only | No | Yes |
| `it_tender.preview` | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | No | Yes |
| `it_tender.submit_review` | Yes | No | No | Conditional | No | No | No | No | No | No | No |
| `it_tender.review.procurement` | No | No | No | Yes | No | No | No | No | Read Only | No | No |
| `it_tender.review.technical` | No | No | Yes | No | No | No | No | No | Read Only | No | No |
| `it_tender.review.finance` | No | No | No | No | Yes | No | No | No | Read Only | No | No |
| `it_tender.review.legal` | No | No | No | No | No | Yes | No | No | Read Only | No | No |
| `it_tender.return_review` | No | No | Yes | Yes | Yes | Yes | Yes | Yes | No | No | No |
| `it_tender.approve_publication` | No | No | No | No | No | No | Yes | Yes | No | No | No |
| `it_tender.render_publication` | Yes | No | No | Conditional | No | No | Conditional | Conditional | No | No | No |
| `it_tender.publish` | No | No | No | No | No | No | Conditional | Yes | No | No | No |
| `it_tender.create_addendum` | Yes | Conditional | No | Yes | No | Conditional | Conditional | Yes | No | No | No |
| `it_tender.review_addendum` | No | No | Yes | Yes | Yes | Yes | Yes | Yes | Read Only | No | No |
| `it_tender.approve_addendum` | No | No | No | No | No | No | Yes | Yes | No | No | No |
| `it_tender.publish_addendum` | No | No | No | No | No | No | Conditional | Yes | No | No | No |
| `it_tender.cancel` | No | No | No | Conditional | No | Conditional | Yes | Yes | Read Only | No | No |
| `it_tender.archive` | No | No | No | No | No | No | Conditional | Yes | Read Only | No | Conditional |
| `it_tender.audit_view` | No | No | No | Conditional | Conditional | Conditional | Conditional | Conditional | Yes | Limited | Yes |
| `it_tender.audit_export` | No | No | No | No | No | No | Conditional | Conditional | Yes | No | Conditional |
| `it_tender.break_glass` | No | No | No | No | No | No | No | Conditional | No | Conditional | No |

### 11.3 Conditional Permission Meaning

`Conditional` means the action is allowed only if:

1. The user is explicitly assigned to that tender instance.
2. The tender instance is in a state where the action is permitted.
3. The relevant wizard section is not locked.
4. The action does not violate segregation-of-duty policy.
5. The action is within the user's review or ownership scope.

---

## 12. Segregation of Duties

### 12.1 Mandatory SoD Rules

| Rule ID | Rule | Severity |
|---|---|---|
| `SOD-001` | A user who created the tender configuration cannot be the sole final approver. | Blocker |
| `SOD-002` | A user who edited a section after review cannot approve that same section unless override policy allows. | Blocker by default |
| `SOD-003` | System Administrator privilege does not grant procurement approval authority. | Blocker |
| `SOD-004` | STD Administrator privilege does not grant tender publication authority. | Blocker |
| `SOD-005` | Auditor role is read-only and cannot approve or edit. | Blocker |
| `SOD-006` | Addendum author cannot be the sole addendum approver. | Blocker |
| `SOD-007` | Legal reviewer cannot alter locked GCC text. | Blocker |
| `SOD-008` | Technical owner cannot approve final procurement publication by technical ownership alone. | Blocker |

### 12.2 Optional Configurable SoD Rules

| Rule ID | Rule | Recommended Default |
|---|---|---|
| `SOD-101` | Procurement reviewer must differ from procurement preparer. | Enabled |
| `SOD-102` | Technical reviewer must differ from technical owner. | Enabled for high-value tenders |
| `SOD-103` | Finance reviewer must differ from payment milestone author. | Enabled |
| `SOD-104` | Legal reviewer must differ from SCC parameter author. | Enabled where legal user authored SCC |
| `SOD-105` | Final publisher must differ from final approver. | Optional |

---

## 13. Mutability Enforcement

### 13.1 Mutability Types

The wizard must enforce the mutability model inherited from the STD package.

| Mutability Type | Meaning | Wizard Behavior |
|---|---|---|
| `LOCKED` | Legal text or structure cannot be changed. | Display only; no edit control. |
| `PARAMETERIZED` | Tender-specific value can be supplied through defined field. | Typed form field only. |
| `CONTROLLED_TEXT` | User may enter text subject to rules. | Rich/plain text with validation and review. |
| `STRUCTURED_REQUIREMENTS` | Requirements are entered as structured objects. | Requirement composer only. |
| `STRUCTURED_TABLE` | Tables are entered using defined row/column schema. | Grid/table editor only. |
| `SELECTABLE_OPTION` | Choice from approved values. | Select control only. |
| `CALCULATED` | Value is system-computed. | Read-only computed field. |
| `GENERATED` | Rendered from rules and configuration. | No direct editing. |
| `REFERENCE_ONLY` | Informational source material. | Attach/link/view only. |

### 13.2 Locked Content Rules

1. Locked ITT and GCC clauses are never edited by the wizard.
2. Locked clause text must render from the active STD package.
3. If a locked clause is missing from the package, publication must fail.
4. User-entered values may render into TDS/SCC or permitted placeholders only.
5. The system must prevent hidden mutation of locked text during rendering.
6. Rendered locked text hashes must be traceable to source clause hashes when available.

### 13.3 Controlled Text Rules

Controlled text fields require:

1. Field-level ownership.
2. Maximum length where configured.
3. Prohibited-content checks where configured.
4. Review track assignment.
5. Change history.
6. Render location.
7. Optional source/evidence attachment.

---

## 14. IT-Specific Governance Rules

### 14.1 Requirements Composer Rules

> **Ownership Matrix override (`99` / ITW-OWN-DOC-04):** Interpret “scored requirement” as Evaluation-linked treatment with a criterion link. Score marks/weights are validated on Evaluation Setup (`ITEVAL-*`), not entered on the Requirements screen.

| Rule ID | Rule | Severity |
|---|---|---|
| `ITREQ-001` | Every requirement must have a unique requirement ID. | Blocker |
| `ITREQ-002` | Every mandatory requirement must have a compliance response mode. | Blocker |
| `ITREQ-003` | Every scored requirement must link to an evaluation criterion. | Blocker |
| `ITREQ-004` | Requirement text must be supplier-facing and obligation-oriented. | Warning/Blocker depending policy |
| `ITREQ-005` | Brand-specific requirements require justification and review. | Blocker unless justified |
| `ITREQ-006` | Requirement groups must map to render sections. | Blocker |
| `ITREQ-007` | Each requirement must identify whether evidence is required. | Blocker for mandatory requirements |

### 14.2 Implementation Schedule Rules

| Rule ID | Rule | Severity |
|---|---|---|
| `ITSCH-001` | Implementation schedule must contain at least one milestone. | Blocker |
| `ITSCH-002` | Milestone dates or durations must be coherent. | Blocker |
| `ITSCH-003` | Acceptance milestones must link to acceptance criteria. | Blocker |
| `ITSCH-004` | Payment milestones must not conflict with implementation milestones. | Blocker |
| `ITSCH-005` | Multi-phase implementation must define phase dependencies. | Blocker |
| `ITSCH-006` | Warranty commencement must link to acceptance or phase acceptance. | Blocker |

### 14.3 System Inventory Rules

> **Ownership Matrix override (`99` / ITW-OWN-DOC-04):** ITINV-002/003/004 commercial quantity, recurrence, and price-line validity are enforced on Price Schedule (`ITPRICE-*`). System Inventory enforces unique codes, technical category/scope completeness, disclosure/review, and Price Schedule Link policy only.

| Rule ID | Rule | Severity |
|---|---|---|
| `ITINV-001` | Inventory item IDs must be unique. | Blocker |
| `ITINV-002` | Supply/install inventory items must link to price schedule where pricing is required. | Blocker |
| `ITINV-003` | Recurrent cost items must identify recurrence period. | Blocker |
| `ITINV-004` | Quantity and unit fields must be valid where required. | Blocker |
| `ITINV-005` | Inventory items must map to a requirement group, service, component, or contract deliverable. | Warning/Blocker depending policy |

### 14.4 Price Schedule Rules

| Rule ID | Rule | Severity |
|---|---|---|
| `ITPRICE-001` | Price schedule structure must match selected STD price schedule schema. | Blocker |
| `ITPRICE-002` | Supply/install and recurrent costs must be separated where STD requires separation. | Blocker |
| `ITPRICE-003` | VAT handling must be explicit. | Blocker |
| `ITPRICE-004` | Price adjustment setting must be consistent with TDS/SCC. | Blocker |
| `ITPRICE-005` | Recurrent cost evaluation period must be specified if recurrent costs are evaluated. | Blocker |
| `ITPRICE-006` | Payment milestones must not exceed 100 percent of contract price. | Blocker |

### 14.5 Evaluation Rules

| Rule ID | Rule | Severity |
|---|---|---|
| `ITEVAL-001` | Technical scoring total must equal configured total, normally 100. | Blocker |
| `ITEVAL-002` | Minimum pass mark must be defined where technical scoring is used. | Blocker |
| `ITEVAL-003` | Mandatory pass/fail requirements must be separately identified from scored criteria. | Blocker |
| `ITEVAL-004` | Financial evaluation method must be defined. | Blocker |
| `ITEVAL-005` | Criteria must not be introduced outside STD-permitted structure unless authorized. | Blocker |
| `ITEVAL-006` | Each scored criterion must have max points greater than zero. | Blocker |
| `ITEVAL-007` | Evaluation criteria must be visible in the rendered tender document. | Blocker |

### 14.6 Contract Carry-Forward Rules

| Rule ID | Rule | Severity |
|---|---|---|
| `ITCON-001` | SCC parameters must carry forward to draft contract forms. | Blocker |
| `ITCON-002` | Payment milestones must carry forward to contract terms. | Blocker |
| `ITCON-003` | Acceptance criteria must carry forward to acceptance certificates. | Blocker |
| `ITCON-004` | Software category and IP information must carry forward to contract appendices where required. | Blocker |
| `ITCON-005` | Approved subcontractors must carry forward after award if applicable. | Blocker at contract formation |
| `ITCON-006` | Change-order procedure must be included where STD package requires it. | Blocker |

---

## 15. Review Track Requirements

### 15.1 Procurement Review Checklist

Procurement review must confirm:

1. Correct active STD version selected.
2. Tender identity complete.
3. Procurement method configured correctly.
4. Eligibility and participation settings are valid.
5. JV settings are valid.
6. Clarification and submission deadlines are valid.
7. Alternative tender setting is valid.
8. Reservation or preference settings are valid where used.
9. Tender security or professional indemnity setting is valid.
10. Qualification criteria are allowed and clear.
11. Evaluation criteria are clear and disclosed.
12. Supplier forms and evidence requirements are complete.
13. Published render preview aligns with configuration.

### 15.2 Technical Review Checklist

Technical review must confirm:

1. Functional requirements are complete.
2. Architectural requirements are complete.
3. Performance and security requirements are complete.
4. Service requirements are complete.
5. Technology specifications are complete.
6. Requirements are measurable and testable.
7. Requirements avoid unjustified vendor lock-in.
8. Implementation schedule is feasible.
9. Acceptance criteria are clear.
10. System inventory is coherent.
11. Supplier conformance matrix is usable.
12. Technical scoring criteria align with requirements.

### 15.3 Finance Review Checklist

Finance review must confirm:

1. Budget and procurement plan values align.
2. Price schedule structure is appropriate.
3. Supply/install and recurrent costs are handled correctly.
4. Taxes and VAT handling are clear.
5. Payment milestones are coherent.
6. Performance security is defined.
7. Advance payment security is defined where applicable.
8. Retention is defined where applicable.
9. Warranty and support periods are financially reflected.
10. Abnormally low/high tender benchmark data exists where required.
11. Financial evaluation method is clear.

### 15.4 Legal Review Checklist

Legal review must confirm:

1. SCC parameters are complete.
2. GCC has not been altered.
3. IP and software licensing provisions are coherent.
4. Confidentiality provisions are included.
5. Limitation of liability settings are lawful and appropriate.
6. Warranty and defect liability provisions are coherent.
7. Acceptance and operational acceptance terms are clear.
8. Termination terms are complete.
9. Dispute resolution settings are complete.
10. Change-order procedure is included.
11. Contract forms and appendices are complete.
12. Beneficial ownership disclosure requirements are included where required.

---

## 16. Addendum Governance

### 16.1 Addendum Types

| Addendum Type | Description | Typical Review Tracks |
|---|---|---|
| Clarification only | Clarifies without changing tender obligations. | Procurement |
| Deadline extension | Extends submission or clarification deadline. | Procurement |
| Requirement correction | Changes technical or functional requirements. | Procurement + Technical |
| Price schedule correction | Changes pricing structure or submission table. | Procurement + Finance |
| Evaluation correction | Changes evaluation criteria or scoring. | Procurement + Technical + Legal |
| SCC/contract correction | Changes contract terms or SCC values. | Procurement + Legal + Finance if financial |
| Material scope amendment | Changes project scope or deliverables. | All tracks + Authorized Officer |
| Cancellation/withdrawal | Cancels or withdraws tender. | Procurement + Legal + Authorized Officer |

### 16.2 Addendum State Machine

```text
ADDENDUM_DRAFT
  -> ADDENDUM_VALIDATION_IN_PROGRESS
  -> ADDENDUM_VALIDATION_FAILED
  -> ADDENDUM_READY_FOR_REVIEW
  -> ADDENDUM_REVIEW
  -> ADDENDUM_RETURNED
  -> ADDENDUM_APPROVED
  -> ADDENDUM_RENDERING
  -> ADDENDUM_PUBLICATION_READY
  -> ADDENDUM_PUBLISHED
```

### 16.3 Addendum Impact Assessment

Every addendum must include an impact assessment.

Required impact fields:

1. Addendum reason.
2. Affected tender sections.
3. Affected requirement IDs.
4. Affected price schedule tables.
5. Affected evaluation criteria.
6. Affected forms and evidence requirements.
7. Affected deadlines.
8. Supplier response impact.
9. Whether resubmission is required.
10. Whether tender opening date changes.
11. Whether generated contract carry-forward fields change.
12. Review tracks required.
13. Render blocks affected.
14. Publication notification requirements.

### 16.4 Addendum Immutability Rules

1. Base publication bundle remains immutable.
2. Addendum creates a linked addendum bundle.
3. Addendum does not overwrite original artifacts.
4. Consolidated view may be generated, but must identify base version and addendum references.
5. Supplier-visible materials must show addendum sequence.
6. Audit must link addendum to initiator, review, approval, render hash, and publication event.

---

## 17. Audit Model

### 17.1 Required Audit Event Categories

| Event Category | Examples |
|---|---|
| Lifecycle | Created, submitted, reviewed, approved, published, closed |
| Configuration | Field changed, requirement added, price table changed, SCC value changed |
| Validation | Validation run started/completed, finding created/resolved/waived |
| Review | Review assigned, review approved, review returned, comment added |
| Render | Preview generated, publication bundle generated, render failed |
| Publication | Tender published, addendum published, supplier notification sent |
| Security | Permission denied, role assigned, break-glass access invoked |
| Integrity | Hash generated, hash verified, hash mismatch detected |
| Exception | Cancellation, investigation lock, emergency override |

### 17.2 Audit Fields

Every audit event must capture:

1. Event ID.
2. Event type.
3. Tender instance ID.
4. STD family ID.
5. STD version ID.
6. Actor user ID.
7. Actor role at time of event.
8. Timestamp.
9. Previous state where applicable.
10. New state where applicable.
11. Object type.
12. Object ID.
13. Before value hash where applicable.
14. After value hash where applicable.
15. Reason or comment where required.
16. Source IP/device/session metadata where available.
17. Correlation ID.
18. Validation run ID where applicable.
19. Render bundle ID where applicable.
20. Addendum ID where applicable.

### 17.3 Audit Non-Repudiation Requirements

1. Audit events must be append-only.
2. Audit events must not be deleted through normal UI.
3. Corrections must be recorded as new events.
4. Publication events must be linked to bundle hashes.
5. Addendum events must be linked to base publication bundle.
6. Role assignments used in approvals must be preserved historically.

---

## 18. Validation Finding Governance

### 18.1 Finding Severities

| Severity | Meaning | Can Publish? |
|---|---|---:|
| `INFO` | Informational notice. | Yes |
| `WARNING` | Non-blocking issue requiring awareness. | Yes, if acknowledged where required |
| `ERROR` | Must be corrected before review or approval. | No |
| `BLOCKER` | Legally or structurally impossible to proceed. | No |

### 18.2 Finding Statuses

```text
OPEN
ACKNOWLEDGED
RESOLVED
WAIVED
SUPERSEDED
```

### 18.3 Waiver Rules

Only warnings may normally be waived.

Errors and blockers may not be waived unless an explicitly configured legal exception allows it. Any such exception must require:

1. Legal reviewer approval.
2. Procurement approver approval.
3. Reason.
4. Supporting document.
5. Audit event.
6. Expiry or scope limitation.

Default rule:

> `ERROR` and `BLOCKER` findings cannot be waived.

---

## 19. Publication Immutability

### 19.1 Immutable Objects After Publication

After `PUBLISHED`, the following are immutable:

1. Tender identity as published.
2. Published tender document bundle.
3. Rendered sections.
4. Supplier forms.
5. Price schedule forms.
6. Requirement tables.
7. Evaluation criteria.
8. Submission deadline unless changed by addendum.
9. TDS/SCC values as published.
10. Publication hash.
11. Publication audit event.

### 19.2 Permitted Post-Publication Actions

After publication, users may:

1. View published tender bundle.
2. Export published bundle.
3. Create addendum draft.
4. Publish addendum after approval.
5. Record clarifications where governed.
6. Close tender configuration lifecycle.
7. Archive after retention policy allows.

Users may not:

1. Directly edit published tender values.
2. Replace published PDF/HTML silently.
3. Delete publication audit events.
4. Change evaluation criteria without addendum.
5. Change supplier submission schemas without addendum impact assessment.

---

## 20. Break-Glass Governance

Break-glass access is an emergency support pathway. It must not be used for normal procurement decisions.

### 20.1 Permitted Break-Glass Use Cases

1. System outage preventing lawful publication or addendum action.
2. Corrupted workflow state requiring technical repair.
3. Security incident investigation.
4. Court, regulator, or audit-directed record preservation.

### 20.2 Break-Glass Controls

1. Requires explicit authorization.
2. Requires reason.
3. Requires time-bound access.
4. Requires automatic audit event.
5. Requires post-event review.
6. Cannot approve procurement content unless the actor separately has procurement authority and the action is recorded as business approval.
7. Cannot alter published artifact content without creating a new governed correction/addendum record.

---

## 21. Notifications

### 21.1 Notification Events

| Event | Recipients |
|---|---|
| Tender instance created | Assigned preparer, procurement supervisor |
| Configuration submitted for review | Required reviewers |
| Review returned | Preparer and affected section owners |
| Review approved | Preparer and next reviewers/approver |
| Approval pending | Approver / authorized officer |
| Approved for publication | Preparer, publisher |
| Render failed | Preparer, system support, workflow owner |
| Publication ready | Authorized publisher |
| Tender published | Procurement team, audit, supplier portal integration |
| Addendum draft created | Procurement reviewer, affected owners |
| Addendum published | Suppliers, procurement team, audit |
| Deadline changed | Suppliers and internal stakeholders |
| Investigation lock | Authorized officers, audit, system support |

### 21.2 Notification Evidence

Supplier-impacting notifications must be auditable.

Required evidence:

1. Notification type.
2. Recipient group.
3. Timestamp.
4. Delivery channel.
5. Message template ID.
6. Related publication or addendum ID.
7. Delivery result where available.

---

## 22. Data Access Rules

### 22.1 Draft Access

Draft tender configurations are visible only to:

1. Assigned preparers.
2. Assigned technical owners.
3. Assigned reviewers.
4. Approvers for oversight.
5. Auditors where policy allows.
6. System support only as needed.

### 22.2 Review Access

During review:

1. Reviewers may view all relevant sections.
2. Reviewers may comment on relevant sections.
3. Reviewers may approve or return within assigned review track.
4. Editing is disabled unless configuration is returned.

### 22.3 Published Access

Published tender artifacts are visible according to tender publication policy.

Internal configuration metadata remains restricted even where public tender artifacts are visible.

### 22.4 Supplier Access

Suppliers may access only:

1. Published tender document.
2. Published addenda.
3. Supplier forms.
4. Supplier submission schemas.
5. Public clarifications.
6. Submission portal fields relevant to their response.

Suppliers may not access:

1. Internal validation findings.
2. Internal review comments.
3. Internal approval notes.
4. Draft configurations.
5. Internal audit trails.
6. Unpublished addenda.

---

## 23. State-Specific Edit Rules

| State | Edit Policy |
|---|---|
| `DRAFT` | Broad edit permissions for assigned preparer and section owners. |
| `CONFIGURATION_IN_PROGRESS` | Normal editing according to role and section ownership. |
| `VALIDATION_IN_PROGRESS` | Editing temporarily locked. |
| `VALIDATION_FAILED` | Editing allowed only to resolve findings. |
| `READY_FOR_REVIEW` | Editing locked except explicit recall action. |
| Review states | Editing locked; comments and review actions allowed. |
| `REVIEW_RETURNED` | Editing allowed only for returned scope unless reopened by authorized user. |
| `APPROVAL_PENDING` | Editing locked. |
| `APPROVED_FOR_PUBLICATION` | Editing locked. |
| `RENDERING_FOR_PUBLICATION` | Editing locked. |
| `PUBLICATION_READY` | Editing locked; publish or reject render only. |
| `PUBLISHED` | No direct editing; addendum only. |
| Addendum states | Editing limited to addendum scope. |
| Terminal states | No editing except audit/admin metadata allowed by policy. |

---

## 24. Recall and Reopen Rules

### 24.1 Recall Before Review Starts

A preparer may recall a submission from `READY_FOR_REVIEW` if no reviewer has acted.

### 24.2 Recall During Review

Recall during review requires procurement reviewer or workflow owner permission and must:

1. Record reason.
2. Invalidate pending review assignments.
3. Return state to `CONFIGURATION_IN_PROGRESS` or `REVIEW_RETURNED`.
4. Require revalidation before resubmission.

### 24.3 Reopen After Approval but Before Publication

Reopening after `APPROVED_FOR_PUBLICATION` requires:

1. Approver or authorized officer action.
2. Reopen reason.
3. Invalidation of final approval.
4. Revalidation.
5. Re-review of affected sections.

### 24.4 Reopen After Publication

Direct reopen is prohibited.

Post-publication changes must use addendum governance.

---

## 25. Cancellation and Withdrawal Governance

### 25.1 Before Publication

A tender configuration may be withdrawn before publication by authorized procurement users.

Required fields:

1. Withdrawal reason.
2. Authorized actor.
3. Timestamp.
4. Whether procurement plan item remains available for new tender.

### 25.2 After Publication

Cancellation after publication requires:

1. Formal cancellation reason.
2. Legal/procurement review.
3. Authorized officer approval.
4. Supplier notification.
5. Public cancellation artifact where required.
6. Audit event.

### 25.3 Cancellation State Rules

1. Cancelled records remain immutable except cancellation metadata.
2. Published bundle remains preserved.
3. Supplier notifications remain linked.
4. A new tender instance must reference the cancelled tender where retendering occurs.

---

## 26. Governance Data Objects

The following governance objects must exist in the implementation.

| Object | Purpose |
|---|---|
| `Tender Configuration Workflow State` | Stores primary state. |
| `Tender Configuration Section State` | Stores per-section completion/review/lock status. |
| `Tender Review Assignment` | Stores reviewer assignment and due status. |
| `Tender Review Decision` | Stores approval/return decisions. |
| `Tender Approval Decision` | Stores final approval decision. |
| `Tender Validation Run` | Stores validation execution. |
| `Tender Validation Finding` | Stores validation findings. |
| `Tender Render Run` | Stores preview/publication render execution. |
| `Tender Publication Bundle` | Stores immutable generated artifacts and hashes. |
| `Tender Addendum` | Stores addendum lifecycle and impact. |
| `Tender Addendum Impact` | Stores affected objects and sections. |
| `Tender Governance Audit Event` | Stores append-only governance events. |
| `Tender Workflow Lock` | Stores lock reason and owner. |
| `Tender Role Assignment` | Stores tender-specific role assignments. |
| `Tender Permission Override` | Stores explicit authorized exceptions. |

---

## 27. Governance API Requirements

The API layer must expose operations for:

1. Creating tender instance.
2. Updating permitted sections.
3. Running validation.
4. Submitting for review.
5. Assigning reviewers.
6. Recording review decisions.
7. Returning for correction.
8. Approving publication.
9. Rendering preview.
10. Rendering publication bundle.
11. Publishing tender.
12. Creating addendum.
13. Reviewing addendum.
14. Publishing addendum.
15. Cancelling tender.
16. Closing tender.
17. Viewing audit history.
18. Exporting audit package.

Every write API must:

1. Check current state.
2. Check user permission.
3. Check section lock state.
4. Check SoD constraints where relevant.
5. Write audit event.
6. Return updated state.

---

## 28. UI Governance Requirements

The UI must make governance visible and hard to bypass.

### 28.1 Required UI Elements

1. Current tender lifecycle state badge.
2. Active STD version badge.
3. Section completion indicators.
4. Section lock indicators.
5. Review track status panel.
6. Validation findings panel.
7. Approval checklist.
8. Publication readiness checklist.
9. Addendum impact panel.
10. Audit history panel for authorized users.
11. Render preview panel.
12. Warning when STD version is superseded after tender instance creation.

### 28.2 UI Blocking Behavior

The UI must disable actions that are impossible in current state, including:

1. Editing locked sections.
2. Submitting incomplete configuration.
3. Approving with blockers.
4. Publishing without publication-ready bundle.
5. Editing published tender directly.
6. Publishing addendum without impact assessment.

The API must still enforce all restrictions. UI blocking is not sufficient by itself.

---

## 29. Reporting Requirements

### 29.1 Governance Reports

| Report | Audience |
|---|---|
| Tender Configuration Status Report | Procurement team |
| Review Pending Report | Reviewers and supervisors |
| Validation Findings Report | Preparer and reviewers |
| Approval Decision Report | Approvers and audit |
| Publication Evidence Report | Procurement, audit, legal |
| Addendum Impact Report | Procurement, technical, legal, suppliers where public |
| Audit Trail Export | Internal audit and authorized officers |
| SoD Exception Report | Audit and governance administrators |

### 29.2 Report Filters

Reports should support filtering by:

1. Procuring entity.
2. Tender number.
3. STD family.
4. STD version.
5. Tender status.
6. Assigned reviewer.
7. Validation severity.
8. Publication date.
9. Addendum status.
10. Approval decision.

---

## 30. Smoke Contracts

### 30.1 Creation Smoke Contract

**Given** an active IT STD version exists  
**When** a Procurement Preparer creates a tender instance  
**Then** the instance is created in `DRAFT` state  
**And** it is linked to the active STD version  
**And** an audit event is recorded.

### 30.2 Locked Clause Smoke Contract

**Given** a tender instance is in `CONFIGURATION_IN_PROGRESS`  
**When** a user attempts to edit locked ITT or GCC text  
**Then** the system rejects the edit  
**And** records a permission or mutability violation event.

### 30.3 Validation Blocker Smoke Contract

**Given** mandatory IT requirements are missing  
**When** validation is run  
**Then** a blocker finding is created  
**And** the tender cannot move to `READY_FOR_REVIEW`.

### 30.4 Review Return Smoke Contract

**Given** the tender is in `TECHNICAL_REVIEW`  
**When** the Technical Reviewer returns the requirements section for correction  
**Then** the state becomes `REVIEW_RETURNED`  
**And** only affected sections are reopened  
**And** technical approval remains incomplete.

### 30.5 Segregation of Duty Smoke Contract

**Given** a user created the tender instance  
**When** the same user attempts to be the sole final approver  
**Then** the system rejects the approval  
**And** records an SoD violation finding.

### 30.6 Publication Smoke Contract

**Given** all reviews and approvals are complete  
**And** validation has no blockers  
**When** the publication bundle is rendered and published  
**Then** the tender moves to `PUBLISHED`  
**And** the publication bundle becomes immutable  
**And** bundle hash and audit event are stored.

### 30.7 Addendum Smoke Contract

**Given** a tender is published  
**When** a deadline extension is needed  
**Then** an addendum draft must be created  
**And** the base published bundle remains unchanged  
**And** the addendum must be reviewed, approved, rendered, hashed, and published.

### 30.8 Direct Published Edit Smoke Contract

**Given** a tender is published  
**When** any user attempts to directly edit a published requirement  
**Then** the system rejects the edit  
**And** instructs the user to initiate addendum workflow.

### 30.9 Render Integrity Smoke Contract

**Given** a publication bundle has been rendered  
**When** the system verifies the bundle before publication  
**Then** all artifact hashes must match the render manifest  
**And** publication must fail if any hash mismatch exists.

### 30.10 Contract Carry-Forward Smoke Contract

**Given** an IT tender is configured with payment milestones, warranty period, acceptance milestones, and IP settings  
**When** publication preview is generated  
**Then** those values must appear in the tender document and contract carry-forward schema  
**And** missing carry-forward mappings must produce validation findings.

---

## 31. Acceptance Criteria

The governance model is implementation-ready when all of the following are true:

1. Every lifecycle state has a defined meaning.
2. Every state transition has a permitted actor and blocking conditions.
3. Required approval gates are defined.
4. Review tracks are defined.
5. Segregation-of-duty rules are defined.
6. Role-permission matrix is complete.
7. Locked content behavior is defined.
8. Addendum governance is defined.
9. Publication immutability is defined.
10. Audit-event requirements are defined.
11. Validation finding lifecycle is defined.
12. UI governance requirements are defined.
13. API governance requirements are defined.
14. Smoke contracts are testable.
15. No approval/state-transition gaps remain before service contract and implementation pack work proceeds.

---

## 32. Explicit Approval and State-Transition Gap Check

This section records the required governance quality check before moving to seed data, smoke tests, API design, or implementation instructions.

| Check | Status | Notes |
|---|---|---|
| Primary tender lifecycle states defined | Complete | Includes draft through publication and closure. |
| Addendum lifecycle states defined | Complete | Includes draft, review, approval, rendering, publication. |
| Terminal and exception states defined | Complete | Includes cancellation, archive, investigation lock. |
| State-transition actors defined | Complete | Transition table identifies roles. |
| Blocking conditions defined | Complete | Transition table includes blockers. |
| Review tracks defined | Complete | Procurement, technical, finance, legal. |
| Approval gates defined | Complete | Creation through addendum gates. |
| SoD rules defined | Complete | Mandatory and optional rules included. |
| Published immutability defined | Complete | Direct post-publication editing prohibited. |
| Addendum impact model defined | Complete | Affected sections/forms/schemas/deadlines required. |
| Audit requirements defined | Complete | Event categories and required fields included. |
| Permission matrix defined | Complete | Role-permission table included. |
| Smoke contracts defined | Complete | Testable governance scenarios included. |

Conclusion:

> The approval and state-transition design is sufficiently complete to proceed to seed data, smoke contracts, API/UI contract, and implementation pack work for the IT Tender Configuration Wizard.

---

## 33. Recommended Next Artifact

The next artifact should be:

# IT Tender Configuration Wizard — Seed Data and Smoke Contracts

That document should define:

1. Initial workflow states.
2. Initial transition records.
3. Role records.
4. Permission records.
5. Role-permission assignments.
6. Validation severities.
7. Review track seed values.
8. Addendum type seed values.
9. Audit event type seed values.
10. Smoke-test fixtures.
11. Expected pass/fail outcomes.

