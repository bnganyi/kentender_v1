# IT Tender Configuration Wizard — Seed Data and Smoke Contracts

**Project:** KenTender e-Procurement System  
**Module:** IT Tender Configuration Wizard  
**Artifact Type:** Seed Data and Smoke Contracts  
**STD Family:** Standard Tender Document for Procurement of Information Technology  
**Target STD Package:** `KE-PPRA-IT-2022-04`  
**Status:** Draft for implementation planning  
**Activation Status:** Not activatable until imported into a tested environment and reviewed by procurement/legal authorities  
**Prepared For:** KenTender STD Engine and Tender Management implementation  

---

## 1. Purpose

This document defines the initial seed data and smoke contracts required to implement the IT Tender Configuration Wizard as a controlled consumer of the generalized STD Engine.

The wizard must allow a Procuring Entity to configure a tender under the Standard Tender Document for Procurement of Information Technology without directly editing the master STD text, locked clauses, legal structure, or rendered tender document manually.

The seed data in this document establishes the initial roles, permissions, states, transitions, wizard steps, enumerations, validation severities, review gates, and controlled options needed by the wizard.

The smoke contracts in this document define the minimum testable behaviors that must pass before the wizard is considered usable for controlled pilot implementation.

This document is deliberately generalized where possible so the same wizard framework can later support other STD families, including Works, Goods, Services, Consultancy, Small Works, Framework Agreements, and sector-specific templates.

---

## 2. Design Position

The IT Tender Configuration Wizard is not the legal master. It is a governed tender-instance configuration layer.

The legal master remains the active STD template version held in the STD Engine.

The wizard must therefore operate under the following principles:

1. It must bind a tender to a single active STD version.
2. It must expose only configurable parameters, requirement-composer areas, schedules, forms, and SCC values permitted by the STD package.
3. It must not allow editing of locked ITT, GCC, or other non-configurable legal text.
4. It must validate tender configuration before review, approval, publication, and addendum generation.
5. It must generate structured outputs for publication, supplier response, evaluation, award, and contract formation.
6. It must preserve a full audit trail of configuration, validation, review, approval, rendering, publication, and addendum events.
7. It must be extensible to multiple STD families without hard-coding IT-specific rules into the platform core.

---

## 3. Scope of Seed Data

This artifact seeds the following categories:

| Category | Purpose |
|---|---|
| Wizard roles | Define who can draft, review, approve, validate, and publish IT tender configurations |
| Wizard permissions | Define granular allowed actions |
| Wizard states | Define lifecycle stages for a tender STD configuration instance |
| Transition actions | Define allowed state changes and required gates |
| Wizard step registry | Define ordered configuration steps |
| Mutability handling | Define how locked, configurable, generated, and derived content behaves |
| Parameter groups | Define common configuration groups for IT tenders |
| Requirement types | Define functional, technical, service, performance, implementation, and inventory areas |
| Evaluation seed structures | Define pass/fail, scored, and financial evaluation setup |
| Price schedule types | Define supply/install and recurrent cost schedule categories |
| Evidence types | Define standard supplier evidence/document categories |
| Validation severities | Define blocker, warning, advisory, and informational outcomes |
| Review tracks | Define procurement, legal, technical, finance, and ICT/security review tracks |
| Audit event types | Define events to be logged |
| Smoke contracts | Define the minimum implementation tests that must pass |

---

## 4. Out of Scope

This document does not contain the full official STD clause text.

This document does not activate the IT STD package.

This document does not replace the STD Engine Core seed data.

This document does not define the full frontend UI component library.

This document does not define every procurement-law interpretation or policy exception.

This document does not authorize live use without institutional review and environment testing.

---

## 5. Dependency Baseline

The wizard seed data depends on the following previously defined modules and artifacts:

1. STD Engine Core Module Pre-PRD.
2. STD Engine Core Module PRD.
3. STD Engine Core Domain Model.
4. STD Engine Core Governance, Roles, Permissions, and State Model.
5. STD Engine Core Seed Data and Smoke Contracts.
6. STD Engine Core API, UI, and Service Contract.
7. STD Engine Core Cursor Implementation Pack.
8. IT STD Extraction Matrix.
9. IT STD Seed Package Specification.
10. `KE-PPRA-IT-2022-04` Seed Package Skeleton.
11. IT STD Full Source Extraction Passes 1 to 5.
12. IT STD Package Reconciliation and Import-Ready Update Plan.
13. `KE-PPRA-IT-2022-04_Seed_Package_v0_2.zip`.
14. IT STD Package Validation Report v0.2.
15. NSSF ERP Calibration Mapping.
16. IT Tender Configuration Wizard PRD.
17. IT Tender Configuration Wizard Domain Model.
18. IT Tender Configuration Wizard Governance, Roles, Permissions, and State Model.

---

## 6. Core Seed Data Principles

### 6.1 Principle 1 — STD Version Binding Is Mandatory

Every wizard configuration instance must bind to one active STD version before tender configuration begins.

A wizard instance must not exist in a legally meaningful state without the following:

| Required item | Description |
|---|---|
| STD family ID | Example: `KE-PPRA-IT` |
| STD version ID | Example: `KE-PPRA-IT-2022-04` |
| STD package hash | Hash of the active package used at binding time |
| Binding timestamp | Date/time of binding |
| Binding actor | User/service that created the binding |
| Binding reason | Usually `NEW_TENDER_CONFIGURATION` |

### 6.2 Principle 2 — Locked Text Is Not Editable

The wizard must never expose a free-text editor for locked legal text.

Locked clauses may be displayed for preview and traceability, but modification must be prevented at the data model, API, and UI layers.

### 6.3 Principle 3 — Configurable Areas Are Schema-Driven

Tender-specific configuration must be driven by the active STD package schema.

The wizard must not rely on hard-coded frontend field definitions. Every step should be generated from registered parameter groups, requirement schemas, form schemas, evaluation schemas, and render block metadata.

### 6.4 Principle 4 — Publication Creates an Immutable Bundle

When a tender is approved and published, the generated tender document bundle must be immutable.

Post-publication changes must create a controlled addendum or supersession flow.

### 6.5 Principle 5 — Evaluation and Contract Formation Must Carry Forward

Configured requirements, price schedules, evaluation criteria, SCC values, implementation schedules, system inventory items, and contract-specific fields must be carried forward into supplier response, evaluation, award, and contract formation.

---

## 7. Seed: Wizard Role Registry

The following roles should be seeded for the IT Tender Configuration Wizard. These roles should be implemented as role records that can be mapped to institutional users and organizational units.

| Role Code | Role Name | Purpose | Typical User |
|---|---|---|---|
| `IT_TENDER_DRAFTER` | IT Tender Drafter | Creates and edits tender configuration before review | Procurement officer, ICT officer |
| `IT_REQUIREMENTS_AUTHOR` | IT Requirements Author | Authors IT functional/technical/service requirements | ICT technical team, business analyst |
| `IT_TECHNICAL_REVIEWER` | IT Technical Reviewer | Reviews technical requirements, architecture, implementation schedule, inventory, and acceptance criteria | ICT manager, enterprise architect |
| `PROCUREMENT_REVIEWER` | Procurement Reviewer | Reviews procurement method, TDS, eligibility, qualification, tender security, evaluation structure, and compliance | Procurement manager |
| `LEGAL_REVIEWER` | Legal Reviewer | Reviews SCC, contract carry-forward, IP clauses, warranties, liabilities, securities, and change orders | Legal officer |
| `FINANCE_REVIEWER` | Finance Reviewer | Reviews price schedule setup, payment milestones, budget linkage, security amounts, taxes, retention, and recurrent costs | Finance officer |
| `APPROVING_AUTHORITY` | Approving Authority | Grants final approval for publication or addendum | Head of procurement, accounting officer delegate |
| `TENDER_PUBLISHER` | Tender Publisher | Publishes approved generated bundle | Procurement publication officer |
| `ADDENDUM_MANAGER` | Addendum Manager | Initiates and manages addendum configuration after publication | Procurement officer |
| `AUDIT_VIEWER` | Audit Viewer | Views audit history and generated artifacts without editing rights | Internal auditor, external reviewer |
| `STD_ENGINE_ADMIN` | STD Engine Administrator | Maintains system-level STD package references and bindings; does not override legal governance | System administrator |
| `SUPPLIER_RESPONSE_SCHEMA_VIEWER` | Supplier Response Schema Viewer | Reviews generated bidder response schema for operational readiness | Supplier portal administrator |

### 7.1 Role Separation Requirements

| Requirement | Rule |
|---|---|
| Drafter cannot final-approve own configuration | Required |
| Requirements author cannot bypass procurement review | Required |
| Technical reviewer cannot approve legal/SCC issues alone | Required |
| Publisher cannot publish unless final approval is recorded | Required |
| System administrator cannot activate a tender configuration without business approval | Required |
| Audit viewer is read-only | Required |

---

## 8. Seed: Permission Registry

Permissions should be granular and auditable. They should be assigned to roles through a role-permission mapping table.

### 8.1 Configuration Permissions

| Permission Code | Description | Default Roles |
|---|---|---|
| `wizard.create_instance` | Create a new tender configuration instance | `IT_TENDER_DRAFTER` |
| `wizard.bind_std_version` | Bind tender configuration to active STD version | `IT_TENDER_DRAFTER`, `STD_ENGINE_ADMIN` |
| `wizard.edit_identity` | Edit tender identity fields | `IT_TENDER_DRAFTER` |
| `wizard.edit_procurement_setup` | Edit procurement method, participation, lots, alternatives, reservations | `IT_TENDER_DRAFTER`, `PROCUREMENT_REVIEWER` |
| `wizard.edit_tds` | Edit TDS parameters | `IT_TENDER_DRAFTER`, `PROCUREMENT_REVIEWER` |
| `wizard.edit_requirements` | Edit IT requirements | `IT_REQUIREMENTS_AUTHOR`, `IT_TENDER_DRAFTER` |
| `wizard.edit_implementation_schedule` | Edit implementation phases, milestones, acceptance points | `IT_REQUIREMENTS_AUTHOR`, `IT_TECHNICAL_REVIEWER` |
| `wizard.edit_system_inventory` | Edit system inventory and schedule-of-requirements items | `IT_REQUIREMENTS_AUTHOR`, `IT_TECHNICAL_REVIEWER` |
| `wizard.edit_price_schedule_setup` | Configure price schedule structure | `IT_TENDER_DRAFTER`, `FINANCE_REVIEWER` |
| `wizard.edit_evaluation_setup` | Edit permitted evaluation criteria and weights | `PROCUREMENT_REVIEWER`, `IT_TECHNICAL_REVIEWER` |
| `wizard.edit_scc` | Edit SCC parameters | `LEGAL_REVIEWER`, `IT_TENDER_DRAFTER` |
| `wizard.edit_contract_carry_forward` | Edit contract carry-forward fields | `LEGAL_REVIEWER`, `FINANCE_REVIEWER` |
| `wizard.upload_background_material` | Upload or link background/informational material | `IT_REQUIREMENTS_AUTHOR`, `IT_TENDER_DRAFTER` |
| `wizard.delete_draft_item` | Delete draft configuration items not yet approved/published | `IT_TENDER_DRAFTER` |

### 8.2 Validation and Review Permissions

| Permission Code | Description | Default Roles |
|---|---|---|
| `wizard.run_validation` | Run validation on current configuration | All reviewer roles, `IT_TENDER_DRAFTER` |
| `wizard.view_validation_findings` | View validation findings | All roles |
| `wizard.resolve_warning` | Record resolution or justification for warnings | Responsible reviewer roles |
| `wizard.override_warning` | Approve a warning override where policy allows | `PROCUREMENT_REVIEWER`, `LEGAL_REVIEWER`, `APPROVING_AUTHORITY` |
| `wizard.submit_for_review` | Submit configuration for review | `IT_TENDER_DRAFTER` |
| `wizard.review_procurement_track` | Approve/reject procurement review track | `PROCUREMENT_REVIEWER` |
| `wizard.review_technical_track` | Approve/reject technical review track | `IT_TECHNICAL_REVIEWER` |
| `wizard.review_legal_track` | Approve/reject legal review track | `LEGAL_REVIEWER` |
| `wizard.review_finance_track` | Approve/reject finance review track | `FINANCE_REVIEWER` |
| `wizard.final_approve` | Grant final approval for publication | `APPROVING_AUTHORITY` |
| `wizard.reject_to_draft` | Return configuration to draft | Reviewer roles, `APPROVING_AUTHORITY` |

### 8.3 Rendering and Publication Permissions

| Permission Code | Description | Default Roles |
|---|---|---|
| `wizard.preview_render` | Generate non-final preview | `IT_TENDER_DRAFTER`, reviewers |
| `wizard.generate_review_bundle` | Generate review bundle with watermark | `IT_TENDER_DRAFTER`, reviewers |
| `wizard.generate_publication_bundle` | Generate final publication bundle after approval | `TENDER_PUBLISHER`, `APPROVING_AUTHORITY` |
| `wizard.publish_bundle` | Publish final generated bundle | `TENDER_PUBLISHER` |
| `wizard.view_render_hash` | View generated document hashes | Reviewers, audit roles |
| `wizard.verify_render_hash` | Verify published artifact hash | `AUDIT_VIEWER`, `STD_ENGINE_ADMIN` |

### 8.4 Addendum Permissions

| Permission Code | Description | Default Roles |
|---|---|---|
| `wizard.initiate_addendum` | Start addendum flow for published tender | `ADDENDUM_MANAGER`, `PROCUREMENT_REVIEWER` |
| `wizard.edit_addendum_changes` | Edit proposed addendum changes | `ADDENDUM_MANAGER`, responsible domain authors |
| `wizard.run_addendum_impact_analysis` | Identify affected sections/forms/rules/responses | `ADDENDUM_MANAGER`, reviewers |
| `wizard.review_addendum` | Review addendum package | Reviewer roles |
| `wizard.approve_addendum` | Final approval of addendum | `APPROVING_AUTHORITY` |
| `wizard.publish_addendum` | Publish approved addendum | `TENDER_PUBLISHER` |

### 8.5 Audit Permissions

| Permission Code | Description | Default Roles |
|---|---|---|
| `wizard.view_audit_log` | View audit events | `AUDIT_VIEWER`, reviewers, `APPROVING_AUTHORITY` |
| `wizard.export_audit_log` | Export audit trail | `AUDIT_VIEWER`, `APPROVING_AUTHORITY` |
| `wizard.view_source_trace` | View source trace from configured field to STD anchor | All internal roles |
| `wizard.view_change_history` | View field-level change history | Internal roles |

---

## 9. Seed: Role-Permission Mapping

The following mapping should be seeded as the default. Institutions may add local role groups, but they must not weaken the mandatory separation-of-duty rules.

| Role | Core Permissions |
|---|---|
| `IT_TENDER_DRAFTER` | Create instance, bind STD version, edit identity, edit TDS, configure procurement setup, draft price setup, upload background materials, run validation, submit for review, preview render |
| `IT_REQUIREMENTS_AUTHOR` | Edit requirements, implementation schedule, system inventory, background materials, run validation, preview render |
| `IT_TECHNICAL_REVIEWER` | Review technical track, edit/approve technical findings, run validation, preview render, view audit/source trace |
| `PROCUREMENT_REVIEWER` | Review procurement track, edit evaluation setup where allowed, review TDS, override permitted warnings, run validation |
| `LEGAL_REVIEWER` | Review legal track, edit/review SCC, contract carry-forward, IP, securities, warranties, change-order terms |
| `FINANCE_REVIEWER` | Review price schedule setup, payment milestones, securities, taxes, retention, recurrent cost handling |
| `APPROVING_AUTHORITY` | Final approval, warning override where allowed, reject to draft, approve addendum, view/export audit |
| `TENDER_PUBLISHER` | Generate publication bundle and publish after approval |
| `ADDENDUM_MANAGER` | Initiate addendum, edit addendum changes, run impact analysis, submit addendum for review |
| `AUDIT_VIEWER` | Read-only audit, source trace, render hash, generated bundle verification |
| `STD_ENGINE_ADMIN` | Technical binding, environment support, hash verification, seed import support; no unilateral business approval |

---

## 10. Seed: Wizard State Registry

The wizard must use a controlled state machine.

### 10.1 Tender Configuration States

| State Code | State Name | Description | Editable? |
|---|---|---|---|
| `NOT_STARTED` | Not Started | Tender configuration shell exists but no STD binding is complete | Limited |
| `BOUND_TO_STD` | Bound to STD | Active STD version is bound; configuration may begin | Yes |
| `IN_CONFIGURATION` | In Configuration | User is editing tender-specific data | Yes |
| `VALIDATION_FAILED` | Validation Failed | Blocking findings exist | Yes, to resolve blockers |
| `READY_FOR_REVIEW` | Ready for Review | All required fields completed and no unresolved blockers | No, except return to draft |
| `UNDER_REVIEW` | Under Review | Review tracks are active | No, except reviewer comments/actions |
| `REVIEW_REJECTED` | Review Rejected | One or more review tracks rejected and returned for correction | Yes |
| `APPROVED_FOR_PUBLICATION` | Approved for Publication | Final approval granted, awaiting publication bundle generation | No |
| `PUBLISHED` | Published | Final generated tender bundle is published and immutable | No |
| `ADDENDUM_IN_PROGRESS` | Addendum In Progress | Post-publication controlled change is being prepared | Limited to addendum scope |
| `ADDENDUM_UNDER_REVIEW` | Addendum Under Review | Proposed addendum is under review | No, except reviewer actions |
| `ADDENDUM_APPROVED` | Addendum Approved | Addendum approved, awaiting publication | No |
| `ADDENDUM_PUBLISHED` | Addendum Published | Addendum bundle published; original tender linked to addendum | No |
| `CANCELLED` | Cancelled | Configuration/tender cancelled before or after publication as allowed by procurement governance | No |
| `ARCHIVED` | Archived | Closed, historical record retained | No |

### 10.2 State Invariants

| State | Invariant |
|---|---|
| `BOUND_TO_STD` and later | Must have STD version ID, package hash, and binding event |
| `READY_FOR_REVIEW` | Must have zero unresolved blockers |
| `UNDER_REVIEW` | Must have active review tasks |
| `APPROVED_FOR_PUBLICATION` | Must have all mandatory review tracks approved |
| `PUBLISHED` | Must have final render bundle, hash, timestamp, and publication event |
| `ADDENDUM_IN_PROGRESS` | Must reference an existing published tender configuration |
| `ADDENDUM_PUBLISHED` | Must have impact analysis and approved addendum bundle |
| `ARCHIVED` | Must retain immutable artifacts and audit logs |

---

## 11. Seed: Transition Action Registry

### 11.1 Normal Tender Configuration Transitions

| Transition Code | From State | To State | Required Permission | Required Gate |
|---|---|---|---|---|
| `create_configuration` | None | `NOT_STARTED` | `wizard.create_instance` | User has tender creation authority |
| `bind_active_std` | `NOT_STARTED` | `BOUND_TO_STD` | `wizard.bind_std_version` | STD version is active and not superseded |
| `start_configuration` | `BOUND_TO_STD` | `IN_CONFIGURATION` | `wizard.edit_identity` | Binding complete |
| `run_validation_failed` | `IN_CONFIGURATION` | `VALIDATION_FAILED` | `wizard.run_validation` | One or more blockers exist |
| `run_validation_passed` | `IN_CONFIGURATION` | `READY_FOR_REVIEW` | `wizard.run_validation` | Mandatory fields complete; zero blockers |
| `resolve_blockers` | `VALIDATION_FAILED` | `IN_CONFIGURATION` | Relevant edit permission | User changes configuration |
| `submit_review` | `READY_FOR_REVIEW` | `UNDER_REVIEW` | `wizard.submit_for_review` | Review tracks generated |
| `reject_review` | `UNDER_REVIEW` | `REVIEW_REJECTED` | Review permission | At least one track rejected with reason |
| `return_to_configuration` | `REVIEW_REJECTED` | `IN_CONFIGURATION` | `wizard.edit_identity` or relevant edit permission | Rejection acknowledged |
| `approve_all_tracks` | `UNDER_REVIEW` | `APPROVED_FOR_PUBLICATION` | `wizard.final_approve` | All tracks approved; final approval recorded |
| `publish_tender` | `APPROVED_FOR_PUBLICATION` | `PUBLISHED` | `wizard.publish_bundle` | Final bundle generated and hashed |
| `cancel_before_publication` | `NOT_STARTED`, `BOUND_TO_STD`, `IN_CONFIGURATION`, `VALIDATION_FAILED`, `READY_FOR_REVIEW`, `UNDER_REVIEW`, `REVIEW_REJECTED`, `APPROVED_FOR_PUBLICATION` | `CANCELLED` | `wizard.reject_to_draft` or equivalent cancellation authority | Cancellation reason recorded |
| `archive_closed` | `PUBLISHED`, `CANCELLED`, `ADDENDUM_PUBLISHED` | `ARCHIVED` | Administrative archival permission | Retention policy satisfied |

### 11.2 Addendum Transitions

| Transition Code | From State | To State | Required Permission | Required Gate |
|---|---|---|---|---|
| `initiate_addendum` | `PUBLISHED` | `ADDENDUM_IN_PROGRESS` | `wizard.initiate_addendum` | Addendum reason recorded |
| `run_addendum_impact` | `ADDENDUM_IN_PROGRESS` | `ADDENDUM_IN_PROGRESS` | `wizard.run_addendum_impact_analysis` | Impact report generated |
| `submit_addendum_review` | `ADDENDUM_IN_PROGRESS` | `ADDENDUM_UNDER_REVIEW` | `wizard.submit_for_review` | Impact report complete; no addendum blockers |
| `reject_addendum` | `ADDENDUM_UNDER_REVIEW` | `ADDENDUM_IN_PROGRESS` | Review permission | Rejection reason recorded |
| `approve_addendum` | `ADDENDUM_UNDER_REVIEW` | `ADDENDUM_APPROVED` | `wizard.approve_addendum` | All required tracks approved |
| `publish_addendum` | `ADDENDUM_APPROVED` | `ADDENDUM_PUBLISHED` | `wizard.publish_addendum` | Addendum bundle generated and hashed |

### 11.3 Forbidden Transitions

| From | To | Reason |
|---|---|---|
| `IN_CONFIGURATION` | `PUBLISHED` | Review and approval are mandatory |
| `VALIDATION_FAILED` | `READY_FOR_REVIEW` without revalidation | Blockers must be resolved and validation rerun |
| `UNDER_REVIEW` | `PUBLISHED` | Final approval state is mandatory |
| `PUBLISHED` | `IN_CONFIGURATION` | Published bundle is immutable |
| `PUBLISHED` | direct edit of tender fields | Addendum is required |
| `ADDENDUM_IN_PROGRESS` | direct edit of original published bundle | Original bundle remains immutable |

---

## 12. Seed: Wizard Step Registry

The wizard must be step-driven. Steps should be registered with codes, names, sequence, required roles, data groups, validation blocks, render outputs, and review tracks.

| Step Code | Step Name | Sequence | Required Before Review? | Primary Role | Review Track |
|---|---:|---:|---|---|---|
| `identity` | Tender Identity | 10 | Yes | `IT_TENDER_DRAFTER` | Procurement |
| `std_binding` | STD Binding | 20 | Yes | `IT_TENDER_DRAFTER` / `STD_ENGINE_ADMIN` | Procurement |
| `procurement_setup` | Procurement Setup | 30 | Yes | `IT_TENDER_DRAFTER` | Procurement |
| `participation_rules` | Participation, Reservations, JV, Alternatives | 40 | Yes | `IT_TENDER_DRAFTER` | Procurement |
| `dates_and_clarifications` | Dates, Clarifications, Pre-Tender Meeting | 50 | Yes | `IT_TENDER_DRAFTER` | Procurement |
| `security_and_validity` | Tender Security / Professional Indemnity / Validity | 60 | Yes | `IT_TENDER_DRAFTER` | Procurement / Finance |
| `requirements_overview` | Requirements Overview | 70 | Yes | `IT_REQUIREMENTS_AUTHOR` | Technical |
| `functional_requirements` | Functional Requirements | 80 | Yes | `IT_REQUIREMENTS_AUTHOR` | Technical |
| `technical_architecture` | Architecture and Technology Requirements | 90 | Yes | `IT_REQUIREMENTS_AUTHOR` | Technical |
| `performance_security` | Performance, Availability, Security and Compliance Requirements | 100 | Yes | `IT_REQUIREMENTS_AUTHOR` | Technical / Legal |
| `service_specifications` | Services, Support, Training, Documentation | 110 | Yes | `IT_REQUIREMENTS_AUTHOR` | Technical |
| `implementation_schedule` | Implementation Schedule | 120 | Yes | `IT_REQUIREMENTS_AUTHOR` | Technical / Finance |
| `system_inventory` | System Inventory and Schedule of Requirements | 130 | Yes | `IT_REQUIREMENTS_AUTHOR` | Technical / Finance |
| `price_schedule_setup` | Price Schedule Setup | 140 | Yes | `IT_TENDER_DRAFTER` / `FINANCE_REVIEWER` | Finance / Procurement |
| `evaluation_setup` | Evaluation and Qualification Setup | 150 | Yes | `PROCUREMENT_REVIEWER` | Procurement / Technical |
| `forms_and_evidence` | Forms and Evidence Requirements | 160 | Yes | `IT_TENDER_DRAFTER` | Procurement |
| `scc_contract_terms` | SCC and Contract Terms | 170 | Yes | `LEGAL_REVIEWER` / `IT_TENDER_DRAFTER` | Legal / Finance |
| `contract_carry_forward` | Contract Carry-Forward Preview | 180 | Yes | `LEGAL_REVIEWER` | Legal |
| `validation` | Validation | 190 | Yes | All internal roles | All tracks |
| `review_bundle_preview` | Review Bundle Preview | 200 | Yes | `IT_TENDER_DRAFTER` | All tracks |
| `approval` | Approval | 210 | Yes | `APPROVING_AUTHORITY` | Final |
| `publication` | Publication | 220 | Yes | `TENDER_PUBLISHER` | Publication |

### 12.1 Step Display Rules

| Rule | Behavior |
|---|---|
| Step must be hidden if active STD package does not expose the relevant schema | Applies across multiple STD families |
| Step must be read-only after submission for review | Unless returned to configuration |
| Step must be read-only after publication | Addendum flow only |
| Step must show source trace where a field maps to STD source | Required |
| Step must show validation status | Required |
| Step must show completion percentage only as advisory | Completion percentage must not replace validation |

---

## 13. Seed: Parameter Group Registry

Parameter groups are reusable across STD families. IT-specific groups should extend general procurement groups.

| Group Code | Group Name | Generalizable? | Purpose |
|---|---|---|---|
| `tender_identity` | Tender Identity | Yes | Name, number, procuring entity, description |
| `procurement_method` | Procurement Method | Yes | Open, restricted, national/international, prequalification |
| `participation_controls` | Participation Controls | Yes | Eligible tenderers, JV limits, reservations, foreign participation |
| `submission_controls` | Submission Controls | Yes | Submission method, address, deadline, copies, serialization |
| `clarification_controls` | Clarification Controls | Yes | Clarification deadline, contact, pre-tender meeting |
| `tender_validity` | Tender Validity | Yes | Validity period and extension handling |
| `security_controls` | Tender Security / Professional Indemnity | Yes | Security type, amount, validity, forfeiture rules |
| `currency_tax` | Currency and Tax | Yes | Currency, taxes, VAT treatment |
| `alternative_tenders` | Alternative Tenders | Yes | Whether alternatives are permitted |
| `lots_contracts` | Lots and Multiple Contracts | Yes | Lot configuration and award model |
| `margin_preference` | Margin of Preference | Yes | Preference enablement and rule gating |
| `qualification_requirements` | Qualification Requirements | Yes | Experience, financial, personnel, certification |
| `evaluation_setup` | Evaluation Setup | Yes | Mandatory criteria, scoring, pass mark, financial evaluation |
| `it_functional_requirements` | IT Functional Requirements | Partly | Business and functional requirements |
| `it_architecture_requirements` | IT Architecture Requirements | Partly | Hosting, integration, deployment, scalability |
| `it_service_requirements` | IT Service Requirements | Partly | Installation, testing, training, maintenance |
| `it_system_inventory` | IT System Inventory | IT-specific but reusable for systems procurement | Components, quantities, recurrent items |
| `it_implementation_schedule` | IT Implementation Schedule | IT-specific but reusable for implementation contracts | Phases, milestones, deliverables, acceptance points |
| `price_schedule` | Price Schedule | Yes | Supply/install and recurrent price structures |
| `scc_terms` | SCC Terms | Yes | Contract-specific terms |
| `contract_carry_forward` | Contract Carry-Forward | Yes | Fields carried into contract forms and appendices |

---

## 14. Seed: Mutability Type Registry

| Mutability Code | Name | Description | Editable in Wizard? |
|---|---|---|---|
| `LOCKED` | Locked | Official STD text cannot be altered | No |
| `PARAMETERIZED` | Parameterized | Text contains placeholders filled from approved parameters | Yes, only through parameter fields |
| `CONTROLLED_CONFIG` | Controlled Configuration | User may choose among permitted options or structured rows | Yes |
| `PE_AUTHORED_STRUCTURED` | PE-Authored Structured Content | Procuring Entity writes structured requirements under schema constraints | Yes |
| `DERIVED` | Derived | Value computed from other fields | No direct edit |
| `GENERATED` | Generated | Output created by render engine | No direct edit |
| `ATTACHMENT_REFERENCE` | Attachment Reference | References external/background material | Controlled upload/link only |
| `POST_AWARD_COMPLETED` | Post-Award Completed | Completed after award by successful supplier or contract team | No during tender configuration |

---

## 15. Seed: Validation Severity Registry

| Severity Code | Name | Blocks Progress? | Typical Use |
|---|---|---|---|
| `BLOCKER` | Blocker | Yes | Missing mandatory field, invalid date order, locked text edit attempt, incomplete review |
| `WARNING` | Warning | No, unless policy escalates | Unusual but permitted configuration, e.g. high security amount near threshold |
| `ADVISORY` | Advisory | No | Best-practice suggestion |
| `INFO` | Informational | No | Trace or non-actionable information |

### 15.1 Severity Handling Rules

| Severity | Handling |
|---|---|
| `BLOCKER` | Must be resolved before review, approval, or publication |
| `WARNING` | Must be acknowledged or justified before approval if flagged as review-required |
| `ADVISORY` | May be ignored but remains logged |
| `INFO` | Display only; no action required |

---

## 16. Seed: Review Track Registry

| Review Track Code | Name | Required For IT Tender? | Primary Reviewer Role | Scope |
|---|---|---|---|---|
| `PROCUREMENT` | Procurement Review | Yes | `PROCUREMENT_REVIEWER` | TDS, eligibility, method, submission, evaluation, forms |
| `TECHNICAL` | Technical Review | Yes | `IT_TECHNICAL_REVIEWER` | Requirements, architecture, implementation, inventory, acceptance |
| `LEGAL` | Legal Review | Yes | `LEGAL_REVIEWER` | SCC, contract terms, IP, warranties, liabilities, addenda |
| `FINANCE` | Finance Review | Yes | `FINANCE_REVIEWER` | Price schedule, payment milestones, budget, securities, taxes |
| `ICT_SECURITY` | ICT/Security Review | Conditional | `IT_TECHNICAL_REVIEWER` or security officer | Security, data protection, hosting, integration, access control |
| `FINAL_APPROVAL` | Final Approval | Yes | `APPROVING_AUTHORITY` | Final decision before publication |

### 16.1 Review Track State Registry

| State Code | Description |
|---|---|
| `NOT_REQUIRED` | Track not required for this configuration |
| `PENDING` | Track generated but not started |
| `IN_REVIEW` | Reviewer is reviewing |
| `APPROVED` | Track approved |
| `REJECTED` | Track rejected with required corrections |
| `WAIVED` | Track waived by authorized authority with reason |

Waivers must be rare, permission-controlled, and always audited.

---

## 17. Seed: IT Requirement Type Registry

| Requirement Type Code | Name | Description | Typical Conformance Response |
|---|---|---|---|
| `FUNCTIONAL` | Functional Requirement | Business function the system must perform | Comply / Partially Comply / Not Comply + narrative |
| `ARCHITECTURAL` | Architectural Requirement | Hosting, architecture, integration, platform, scalability | Comply / Partially Comply / Not Comply + reference |
| `PERFORMANCE` | Performance Requirement | Availability, throughput, response times, capacity | Numeric value / SLA commitment / evidence |
| `SECURITY` | Security Requirement | Access control, encryption, audit logs, compliance | Compliance evidence + architecture reference |
| `SERVICE` | Service Specification | Installation, configuration, migration, training, support | Methodology + deliverables |
| `TECHNOLOGY` | Technology Specification | Hardware/software/cloud/network requirements | Product/service details + compliance reference |
| `IMPLEMENTATION` | Implementation Requirement | Milestones, phases, deliverables, acceptance gates | Project plan and schedule |
| `INVENTORY` | Inventory Requirement | Items to be supplied, installed, licensed, supported | Price schedule and item response |
| `DOCUMENTATION` | Documentation Requirement | Manuals, technical docs, user guides | Document list and delivery method |
| `TESTING_ACCEPTANCE` | Testing and Acceptance Requirement | UAT, operational acceptance, commissioning | Test plan + acceptance criteria |
| `SUPPORT_MAINTENANCE` | Support and Maintenance Requirement | Warranty, SLA, support hours, escalation | SLA matrix + support plan |
| `DATA_MIGRATION` | Data Migration Requirement | Migration scope, cleansing, validation, reconciliation | Migration approach + risk controls |
| `INTEGRATION` | Integration Requirement | Interfaces/APIs with external systems | Interface design + standards |
| `TRAINING` | Training Requirement | User/technical/admin training | Training plan, audience, materials |

---

## 18. Seed: Compliance Response Registry

| Response Code | Name | Description | Requires Explanation? | Requires Evidence? |
|---|---|---|---|---|
| `COMPLY` | Comply | Supplier confirms full compliance | Optional | Optional/conditional |
| `PARTIAL_COMPLY` | Partially Comply | Supplier partially meets requirement | Yes | Yes |
| `NOT_COMPLY` | Not Comply | Supplier does not meet requirement | Yes | Optional |
| `ALTERNATIVE_PROPOSED` | Alternative Proposed | Supplier proposes alternative approach where alternatives are permitted | Yes | Yes |
| `NOT_APPLICABLE` | Not Applicable | Requirement not applicable where allowed by tender schema | Yes | Optional |

### 18.1 Compliance Validation Rules

| Rule Code | Rule |
|---|---|
| `compliance_response_required` | Every mandatory requirement must have a supplier compliance response |
| `partial_requires_narrative` | Partial compliance requires explanation |
| `not_comply_requires_risk_flag` | Non-compliance on mandatory requirement creates evaluation finding |
| `alternative_allowed_only_if_enabled` | Alternative response allowed only if alternative tenders or equivalent alternatives are permitted |
| `reference_page_required_if_configured` | If tender requires reference pages, supplier must provide reference location |

---

## 19. Seed: Requirement Priority Registry

| Priority Code | Name | Evaluation Meaning |
|---|---|---|
| `M` | Mandatory | Failure or non-compliance may result in disqualification or technical non-responsiveness |
| `D` | Desirable | Scored or considered but not automatically disqualifying |
| `I` | Informational | Provided for context; not evaluated directly |
| `C` | Contractual | Must carry forward into contract obligations |

---

## 20. Seed: Evaluation Component Registry

| Component Code | Name | Type | Typical Use |
|---|---|---|---|
| `PRELIMINARY_RESPONSIVENESS` | Preliminary Responsiveness | Pass/Fail | Mandatory documents, eligibility, signatures, security, declarations |
| `TECHNICAL_PASS_FAIL` | Technical Pass/Fail | Pass/Fail | Mandatory technical requirements |
| `TECHNICAL_SCORED` | Technical Scored | Weighted score | Methodology, team, experience, solution quality, support |
| `FINANCIAL_EVALUATION` | Financial Evaluation | Calculated | Price comparison, recurrent costs, corrections |
| `POST_QUALIFICATION` | Post-Qualification | Pass/Fail | Verification of capacity and qualifications |
| `PREFERENCE_RESERVATION` | Preference/Reservation | Rule-driven | Margin of preference or reserved participation where enabled |
| `ABNORMAL_PRICE_REVIEW` | Abnormally Low/High Review | Risk workflow | Compares price to estimate and triggers review |

---

## 21. Seed: Default Technical Scoring Template

This default template is a starter archetype. It must remain configurable within limits permitted by the active STD package.

| Criteria Code | Criterion | Default Maximum Points | Generalizable? |
|---|---|---:|---|
| `company_experience` | Company profile, experience, and past performance | 20 | Yes |
| `solution_compliance` | Technical solution proposal and compliance with requirements | 25 | Yes |
| `implementation_methodology` | Implementation methodology, project management, risk management | 15 | Yes |
| `key_personnel` | Key personnel qualifications and experience | 15 | Yes |
| `support_maintenance` | Post-implementation support and maintenance plan | 10 | Yes |
| `data_migration_integration` | Data migration and integration approach | 10 | IT/common systems procurement |
| `training_plan` | Training plan | 5 | Yes |

Default total: 100 points.

Default minimum technical pass mark: 75 points.

### 21.1 Scoring Guardrails

| Rule | Behavior |
|---|---|
| Total scored technical criteria must equal configured total | Blocker |
| Minimum pass mark must be within allowed range | Blocker |
| Mandatory pass/fail checks cannot be converted into scored optional checks without permission | Blocker |
| Evaluation criteria must be published before tender submission | Blocker |
| Post-publication evaluation changes require addendum | Blocker |

---

## 22. Seed: Mandatory Requirement Archetype Registry

| Requirement Code | Requirement Name | Evidence Type |
|---|---|---|
| `incorporation_registration` | Certificate of incorporation/registration | Registration document |
| `tax_compliance` | Tax compliance certificate or exemption | Tax certificate |
| `business_questionnaire` | Confidential business questionnaire | Completed form |
| `independent_tender_determination` | Certificate of independent tender determination | Completed declaration |
| `self_declaration_fraud_corruption` | Self-declaration on fraud and corruption/debarment | Completed declaration |
| `authorized_signatory` | Authorization of tender signatory | Authorization letter/resolution |
| `tender_security_or_indemnity` | Tender security, tender securing declaration, or professional indemnity as configured | Security instrument |
| `technical_proposal` | Technical proposal addressing requirements | Proposal document / structured responses |
| `price_schedule` | Completed price schedules | Structured price table |
| `ip_software_category_disclosure` | Intellectual property and software category disclosure | Completed form/list |
| `project_plan` | Preliminary project plan | Project plan document / structured schedule |
| `subcontractor_list` | Subcontractor list where applicable | Completed list |

---

## 23. Seed: Price Schedule Type Registry

| Schedule Type Code | Name | Description |
|---|---|---|
| `GRAND_SUMMARY` | Grand Summary Cost Table | Summary of all evaluated price components |
| `SUPPLY_INSTALL_SUMMARY` | Supply and Installation Cost Summary | Summary of supply, installation, configuration, testing, commissioning costs |
| `SUPPLY_INSTALL_SUBTABLE` | Supply and Installation Cost Sub-Table | Line-level cost items |
| `RECURRENT_SUMMARY` | Recurrent Cost Summary | Maintenance, licenses, support, hosting, subscription, warranty extension |
| `RECURRENT_SUBTABLE` | Recurrent Cost Sub-Table | Line-level recurrent costs by year or period |
| `COUNTRY_OF_ORIGIN` | Country of Origin Code Table | Country origin disclosure for goods/software/components where required |
| `OPTIONAL_ITEMS` | Optional Items | Optional items where permitted by tender configuration |
| `ALTERNATIVE_PRICE` | Alternative Price Schedule | Used only when alternatives are allowed |

### 23.1 Price Schedule Validation Rules

| Rule Code | Rule |
|---|---|
| `price_schedule_required` | Required price schedules must exist before review |
| `line_totals_match_summary` | Line totals must reconcile to summary totals |
| `vat_disclosure_required_if_configured` | VAT treatment must follow tender configuration |
| `recurrent_cost_period_required` | Recurrent cost items must specify period/year |
| `currency_must_match_tds` | Currency must match TDS unless multi-currency is enabled |
| `evaluated_price_formula_locked_after_publication` | Published evaluated-price formula cannot be changed without addendum |

---

## 24. Seed: Implementation Schedule Registry

### 24.1 Implementation Milestone Types

| Milestone Type Code | Name | Description |
|---|---|---|
| `CONTRACT_SIGNING` | Contract Signing | Contract commencement event |
| `KICKOFF` | Project Kickoff | Formal project initiation |
| `SCOPING_REQUIREMENTS` | Scoping and Requirements Confirmation | Detailed requirements confirmation |
| `DESIGN_CONFIGURATION` | Design and Configuration | System design, configuration, customization |
| `DATA_MIGRATION` | Data Migration | Extraction, transformation, migration, validation |
| `INTEGRATION` | Integration | External systems integration |
| `TESTING` | Testing | SIT, UAT, security testing, performance testing |
| `TRAINING` | Training | User, technical, administrator training |
| `GO_LIVE` | Go-Live | Production deployment |
| `OPERATIONAL_ACCEPTANCE` | Operational Acceptance | Acceptance certificate event |
| `POST_IMPLEMENTATION_SUPPORT` | Post-Implementation Support | Hypercare/support period |
| `WARRANTY_END` | Warranty End | Warranty period closure |

### 24.2 Schedule Validation Rules

| Rule Code | Rule |
|---|---|
| `milestone_dates_required` | Each milestone must have planned date or duration |
| `acceptance_requires_tests` | Operational acceptance must have linked test/acceptance criteria |
| `go_live_after_testing` | Go-live cannot precede required testing milestones |
| `payment_milestone_requires_acceptance_link` | Payment milestones should link to deliverables or acceptance events |
| `phase_dependencies_required` | Multi-phase implementation must define dependencies across phases |

---

## 25. Seed: System Inventory Type Registry

| Inventory Type Code | Name | Description |
|---|---|---|
| `SOFTWARE_LICENSE` | Software License | Commercial off-the-shelf or subscription software |
| `CUSTOM_SOFTWARE` | Custom Software | Custom-developed components or customizations |
| `CLOUD_SERVICE` | Cloud Service | Cloud hosting, storage, compute, managed service |
| `HARDWARE` | Hardware | Physical equipment where applicable |
| `NETWORK_COMPONENT` | Network Component | Network equipment/services |
| `IMPLEMENTATION_SERVICE` | Implementation Service | Configuration, installation, customization, migration |
| `TRAINING_SERVICE` | Training Service | Training delivery and materials |
| `SUPPORT_SERVICE` | Support Service | Support, maintenance, helpdesk, SLA |
| `INTEGRATION_SERVICE` | Integration Service | API/interface development and integration |
| `DOCUMENTATION` | Documentation | Manuals, guides, technical documentation |

---

## 26. Seed: Evidence Type Registry

| Evidence Type Code | Name | File Required? | Structured Fields Required? |
|---|---|---|---|
| `REGISTRATION_CERTIFICATE` | Registration/Incorporation Certificate | Yes | Issuer, number, date |
| `TAX_COMPLIANCE_CERTIFICATE` | Tax Compliance Certificate | Yes | Issuer, expiry date |
| `NSSF_COMPLIANCE_CERTIFICATE` | NSSF Compliance Certificate | Conditional | Issuer, expiry date |
| `CR12_OR_EQUIVALENT` | CR12 or Equivalent Ownership Disclosure | Conditional | Issue date, owners/directors |
| `SECURITY_INSTRUMENT` | Tender Security / Indemnity / Declaration | Yes | Type, issuer, amount, validity |
| `AUTHORIZATION_LETTER` | Authorized Signatory Evidence | Yes | Signatory, authority basis |
| `CERTIFICATION` | Vendor/Product Certification | Yes | Issuer, credential, expiry |
| `REFERENCE_LETTER` | Client Reference Letter | Yes | Client, project, date, signatory |
| `COMPLETION_CERTIFICATE` | Project Completion Certificate | Yes | Project, value, completion date |
| `AUDITED_FINANCIALS` | Audited Financial Statements | Yes | Year, turnover, auditor |
| `CV` | Curriculum Vitae | Yes | Person, role, years experience |
| `PROJECT_PLAN` | Project Plan | Yes or structured | Milestones, dates, resources |
| `METHODOLOGY` | Methodology Document | Yes or structured | Approach, risk controls |
| `SLA` | Service Level Agreement / Support Plan | Yes or structured | Response times, escalation, hours |
| `IP_DISCLOSURE` | IP/Software Category Disclosure | Yes or structured | License category, owner, restrictions |
| `DATA_PROTECTION_EVIDENCE` | Data Protection/Security Evidence | Conditional | Policy, certification, controls |

---

## 27. Seed: Contract Carry-Forward Field Registry

These fields must carry forward from tender configuration and supplier response into award and contract formation.

| Field Code | Source | Target Contract Area |
|---|---|---|
| `contract_name` | Tender identity | Contract Agreement |
| `tender_number` | Tender identity | Contract Agreement, award notices |
| `supplier_name` | Award result | Contract Agreement |
| `contract_price` | Evaluated/awarded price | Contract Agreement, payment schedule |
| `payment_milestones` | SCC / finance setup | SCC, contract appendices |
| `performance_security_amount` | SCC / contract terms | Performance Security form |
| `advance_payment_security_amount` | SCC, if applicable | Advance Payment Security form |
| `implementation_schedule` | Requirements/supplier response | Contract appendix, project plan |
| `system_inventory` | Requirements/supplier response | Contract appendix, schedule of requirements |
| `software_categories` | Supplier IP disclosure | Software categories appendix |
| `custom_materials` | Supplier IP disclosure | Custom materials appendix |
| `approved_subcontractors` | Supplier response / approval | Approved subcontractors appendix |
| `acceptance_tests` | Tender requirements / supplier response | Acceptance certificates |
| `support_sla` | Supplier response / SCC | Support and maintenance appendix |
| `warranty_period` | SCC | SCC, acceptance certificates |
| `change_order_procedure` | STD/SCC | Change order forms |
| `beneficial_ownership` | Supplier disclosure | Beneficial ownership record |

---

## 28. Seed: Audit Event Type Registry

| Event Code | Description |
|---|---|
| `wizard_instance_created` | Tender configuration instance created |
| `std_version_bound` | Active STD version bound to configuration |
| `field_value_changed` | Configurable field changed |
| `requirement_added` | Requirement row added |
| `requirement_updated` | Requirement row updated |
| `requirement_deleted` | Draft requirement row deleted |
| `price_schedule_configured` | Price schedule setup changed |
| `evaluation_setup_changed` | Evaluation setup changed |
| `scc_parameter_changed` | SCC parameter changed |
| `validation_run` | Validation executed |
| `validation_blocker_raised` | Blocking finding created |
| `validation_warning_acknowledged` | Warning acknowledged |
| `review_submitted` | Configuration submitted for review |
| `review_track_approved` | Review track approved |
| `review_track_rejected` | Review track rejected |
| `final_approval_granted` | Final approval recorded |
| `review_bundle_generated` | Review bundle rendered |
| `publication_bundle_generated` | Final bundle rendered |
| `tender_published` | Tender bundle published |
| `addendum_initiated` | Addendum initiated |
| `addendum_impact_analysis_generated` | Addendum impact analysis generated |
| `addendum_approved` | Addendum approved |
| `addendum_published` | Addendum bundle published |
| `render_hash_verified` | Render hash verified |
| `configuration_archived` | Configuration archived |

---

## 29. Seed: Standard Validation Rule Registry

### 29.1 General Validation Rules

| Rule Code | Severity | Description |
|---|---|---|
| `active_std_required` | Blocker | Tender configuration must bind to an active STD version |
| `std_version_not_superseded_at_binding` | Blocker | New tender cannot bind to superseded STD version |
| `mandatory_parameters_complete` | Blocker | Mandatory TDS/SCC/identity parameters must be completed |
| `locked_text_not_modified` | Blocker | Locked sections cannot be changed through wizard |
| `publication_requires_final_approval` | Blocker | Publication cannot occur before final approval |
| `published_bundle_immutable` | Blocker | Published bundle cannot be edited |
| `post_publication_change_requires_addendum` | Blocker | Any post-publication change requires addendum flow |
| `source_trace_required_for_rendered_blocks` | Blocker | Rendered output must trace to source fields/blocks |
| `audit_required_for_state_transition` | Blocker | All state transitions must create audit events |

### 29.2 Tender Data Validation Rules

| Rule Code | Severity | Description |
|---|---|---|
| `submission_deadline_required` | Blocker | Tender submission deadline is mandatory |
| `opening_not_before_deadline` | Blocker | Tender opening cannot occur before submission deadline |
| `clarification_deadline_before_submission` | Blocker | Clarification deadline must be before submission deadline |
| `validity_period_positive` | Blocker | Tender validity period must be positive |
| `currency_required` | Blocker | Tender currency must be configured |
| `alternative_tender_policy_required` | Blocker | Alternatives must be explicitly permitted or not permitted |
| `jv_limit_required_if_jv_allowed` | Blocker | JV maximum members must be set if JVs are allowed |
| `security_amount_required_if_security_enabled` | Blocker | Tender security/indemnity amount must be set where required |

### 29.3 IT Requirement Validation Rules

| Rule Code | Severity | Description |
|---|---|---|
| `requirements_must_have_type` | Blocker | Every requirement must have a requirement type |
| `mandatory_requirement_must_have_text` | Blocker | Requirement statement cannot be empty |
| `requirement_priority_required` | Blocker | Every requirement must have priority or evaluation status |
| `mandatory_requirements_in_response_schema` | Blocker | Mandatory requirements must generate bidder response fields |
| `implementation_schedule_required` | Blocker | Implementation schedule must exist for IT design/supply/install tenders |
| `system_inventory_required` | Blocker | System inventory/schedule of requirements must exist |
| `acceptance_criteria_required_for_milestones` | Warning/Blocker | Key milestones should have acceptance criteria |
| `security_requirements_review_required` | Warning | Security/data protection requirements should trigger technical/legal review |

### 29.4 Evaluation Validation Rules

| Rule Code | Severity | Description |
|---|---|---|
| `evaluation_stages_required` | Blocker | Evaluation stages must be defined |
| `technical_total_points_match` | Blocker | Technical scoring points must sum to configured total |
| `technical_passmark_in_range` | Blocker | Technical pass mark must be valid |
| `mandatory_documents_mapped_to_forms` | Blocker | Mandatory documents must map to forms/evidence |
| `financial_evaluation_formula_required` | Blocker | Financial evaluation method must be defined |
| `lowest_evaluated_responsive_rule_present` | Blocker | Award rule must be present |

### 29.5 Contract Carry-Forward Validation Rules

| Rule Code | Severity | Description |
|---|---|---|
| `scc_required_fields_complete` | Blocker | Mandatory SCC fields must be completed |
| `payment_milestones_reconcile` | Blocker | Payment milestone percentages must reconcile if percentage-based |
| `performance_security_required` | Blocker | Performance security terms must exist where required |
| `warranty_period_required` | Blocker | Warranty period must be configured for IT implementation |
| `ip_terms_review_required` | Warning/Blocker | IP/software ownership terms must be reviewed |
| `acceptance_certificate_schema_required` | Blocker | Acceptance certificate schema must exist for implementation tenders |

---

## 30. Smoke Contracts

Smoke contracts define the minimum end-to-end tests required before the wizard may be piloted.

Each smoke contract should be implemented as an automated or semi-automated test case with clear preconditions, actions, expected results, audit events, and failure conditions.

---

## 31. Smoke Contract 001 — Create Tender Configuration Instance

**Code:** `IT_WIZ_SMOKE_001_CREATE_INSTANCE`

**Purpose:** Verify that an authorized user can create a tender configuration shell.

**Preconditions:**

1. User has role `IT_TENDER_DRAFTER`.
2. At least one active IT STD version exists in the STD Engine.

**Steps:**

1. User opens the IT Tender Configuration Wizard.
2. User selects “Create New IT Tender Configuration”.
3. System creates configuration in `NOT_STARTED` state.

**Expected Result:**

1. Configuration record exists.
2. State is `NOT_STARTED`.
3. Audit event `wizard_instance_created` is recorded.
4. No publication or review actions are available.

**Failure Conditions:**

1. Unauthorized user can create configuration.
2. Configuration is created without audit event.
3. Configuration starts in an advanced state.

---

## 32. Smoke Contract 002 — Bind Active STD Version

**Code:** `IT_WIZ_SMOKE_002_BIND_STD`

**Purpose:** Verify that the wizard binds a tender to one active STD version.

**Preconditions:**

1. Configuration exists in `NOT_STARTED` state.
2. Active STD package `KE-PPRA-IT-2022-04` or equivalent active version exists.
3. User has `wizard.bind_std_version` permission.

**Steps:**

1. User selects active IT STD version.
2. System records family ID, version ID, package hash, timestamp, and actor.
3. System transitions to `BOUND_TO_STD`.

**Expected Result:**

1. Configuration is bound to the selected active STD version.
2. State is `BOUND_TO_STD`.
3. Audit event `std_version_bound` is recorded.
4. Bound package hash is immutable.

**Failure Conditions:**

1. Superseded STD can be bound for a new tender.
2. Binding lacks package hash.
3. Binding can be edited after publication.

---

## 33. Smoke Contract 003 — Prevent Locked Clause Editing

**Code:** `IT_WIZ_SMOKE_003_LOCKED_TEXT`

**Purpose:** Verify that locked ITT/GCC text cannot be edited through the wizard.

**Preconditions:**

1. Configuration is bound to active STD.
2. Active STD has at least one locked clause.
3. User has drafting permissions.

**Steps:**

1. User opens preview of locked ITT clause.
2. User attempts to edit clause text through UI or API.

**Expected Result:**

1. UI does not expose editable control for locked text.
2. API rejects modification attempt.
3. Validation rule `locked_text_not_modified` blocks any attempted change.
4. Security/audit event is recorded if API tampering is attempted.

**Failure Conditions:**

1. Locked legal text can be edited.
2. API accepts mutation.
3. No audit event is recorded for tampering attempt.

---

## 34. Smoke Contract 004 — Complete Tender Identity and TDS Parameters

**Code:** `IT_WIZ_SMOKE_004_TDS_COMPLETION`

**Purpose:** Verify that mandatory identity and TDS parameters can be completed and validated.

**Preconditions:**

1. Configuration is in `IN_CONFIGURATION` state.
2. User has permissions to edit identity and TDS.

**Steps:**

1. User enters tender name, tender number, procuring entity, address, deadline, opening venue, validity period, currency, alternatives policy, and security/indemnity configuration.
2. User saves each step.
3. System runs validation.

**Expected Result:**

1. Mandatory fields are saved.
2. Date-order validations pass.
3. Currency and validity validations pass.
4. Audit events are recorded for field changes.

**Failure Conditions:**

1. Missing mandatory fields pass validation.
2. Opening date before submission deadline passes validation.
3. Changes are not audited.

---

## 35. Smoke Contract 005 — Configure IT Requirements

**Code:** `IT_WIZ_SMOKE_005_REQUIREMENTS`

**Purpose:** Verify that IT requirements can be created as structured records rather than free-form attachment only.

**Preconditions:**

1. Configuration is in `IN_CONFIGURATION`.
2. User has `wizard.edit_requirements` permission.

**Steps:**

1. User creates one functional requirement.
2. User creates one architectural requirement.
3. User creates one security requirement.
4. User creates one support/maintenance requirement.
5. User marks all as mandatory.
6. System generates supplier conformance response fields.

**Expected Result:**

1. Requirements are stored as structured records.
2. Each requirement has type, statement, priority, evaluation handling, and source trace.
3. Supplier response schema includes the mandatory requirements.
4. Audit events are recorded.

**Failure Conditions:**

1. Requirement can be saved without type or text.
2. Mandatory requirement fails to appear in supplier response schema.
3. Requirement is stored only as unstructured document text.

---

## 36. Smoke Contract 006 — Configure Implementation Schedule

**Code:** `IT_WIZ_SMOKE_006_IMPLEMENTATION_SCHEDULE`

**Purpose:** Verify that implementation schedule is modeled as milestones and acceptance gates.

**Preconditions:**

1. Configuration is in `IN_CONFIGURATION`.
2. User has schedule edit permission.

**Steps:**

1. User creates kickoff, requirements confirmation, configuration, testing, go-live, operational acceptance, and support milestones.
2. User links operational acceptance to acceptance criteria.
3. User saves schedule.

**Expected Result:**

1. Schedule records are saved.
2. Go-live cannot precede testing.
3. Operational acceptance has linked acceptance criteria.
4. Schedule can be rendered into tender document preview.

**Failure Conditions:**

1. Schedule is accepted without required milestones.
2. Invalid milestone order passes validation.
3. Acceptance criteria are missing but validation passes when required.

---

## 37. Smoke Contract 007 — Configure System Inventory

**Code:** `IT_WIZ_SMOKE_007_SYSTEM_INVENTORY`

**Purpose:** Verify that system inventory items can be defined and linked to price schedules.

**Preconditions:**

1. Configuration is in `IN_CONFIGURATION`.
2. User has inventory edit permission.

**Steps:**

1. User adds software license item.
2. User adds implementation service item.
3. User adds recurrent support item.
4. System links items to price schedule categories.

**Expected Result:**

1. Inventory items have type, description, quantity/unit, cost category, and price schedule mapping.
2. Required price schedules are generated.
3. Inventory appears in preview render.

**Failure Conditions:**

1. Inventory item can be saved without cost category.
2. Recurrent item does not appear in recurrent cost schedule.
3. Price schedule mapping is missing.

---

## 38. Smoke Contract 008 — Configure Evaluation Criteria

**Code:** `IT_WIZ_SMOKE_008_EVALUATION`

**Purpose:** Verify evaluation criteria can be configured within allowed schema.

**Preconditions:**

1. Configuration is in `IN_CONFIGURATION`.
2. User has evaluation setup permission.

**Steps:**

1. User enables preliminary responsiveness stage.
2. User configures technical scored criteria totaling 100 points.
3. User sets pass mark to 75.
4. User enables financial evaluation by lowest evaluated price.
5. User runs validation.

**Expected Result:**

1. Evaluation stages are saved.
2. Scored technical criteria total equals 100.
3. Pass mark is valid.
4. Award rule is present.

**Failure Conditions:**

1. Criteria totaling less or more than 100 pass validation.
2. Financial evaluation method is missing but validation passes.
3. Award rule is absent.

---

## 39. Smoke Contract 009 — Configure Price Schedule

**Code:** `IT_WIZ_SMOKE_009_PRICE_SCHEDULE`

**Purpose:** Verify supply/install and recurrent price schedules are generated from configuration.

**Preconditions:**

1. Inventory and implementation schedule exist.
2. User has price setup permission.

**Steps:**

1. User enables grand summary.
2. User enables supply/install cost table.
3. User enables recurrent cost table.
4. User maps inventory items to price schedule lines.
5. User runs validation.

**Expected Result:**

1. Required price schedule schemas are generated.
2. Line totals reconcile to summaries.
3. Currency follows TDS.
4. VAT treatment is represented as configured.

**Failure Conditions:**

1. Price schedule missing but review can proceed.
2. Totals do not reconcile but validation passes.
3. Recurrent items are excluded from evaluated price where configured as included.

---

## 40. Smoke Contract 010 — Submit for Review

**Code:** `IT_WIZ_SMOKE_010_SUBMIT_REVIEW`

**Purpose:** Verify configuration can move to review only when validation allows.

**Preconditions:**

1. Configuration is complete.
2. No unresolved blockers exist.
3. User has `wizard.submit_for_review` permission.

**Steps:**

1. User runs validation.
2. System reports zero blockers.
3. User submits for review.

**Expected Result:**

1. State changes to `UNDER_REVIEW`.
2. Review tracks are generated.
3. Draft editing is locked.
4. Audit event `review_submitted` is recorded.

**Failure Conditions:**

1. Configuration with blockers can be submitted.
2. Review tracks are not created.
3. Draft remains freely editable during review.

---

## 41. Smoke Contract 011 — Multi-Track Review and Rejection

**Code:** `IT_WIZ_SMOKE_011_REVIEW_REJECTION`

**Purpose:** Verify review tracks can approve or reject independently and rejected items return to configuration.

**Preconditions:**

1. Configuration is `UNDER_REVIEW`.
2. Procurement, technical, legal, and finance review tracks exist.

**Steps:**

1. Technical reviewer rejects technical requirements with reason.
2. System transitions to `REVIEW_REJECTED` or records rejected track per workflow design.
3. Drafter corrects issue.
4. User reruns validation and resubmits.

**Expected Result:**

1. Rejection reason is mandatory.
2. Rejected scope is visible.
3. Corrections are audited.
4. Resubmission is possible only after validation.

**Failure Conditions:**

1. Reviewer can reject without reason.
2. Draft corrections are not audited.
3. Configuration can proceed to final approval despite rejected track.

---

## 42. Smoke Contract 012 — Final Approval and Publication

**Code:** `IT_WIZ_SMOKE_012_PUBLICATION`

**Purpose:** Verify publication requires all reviews and final approval.

**Preconditions:**

1. All required review tracks are approved.
2. User has final approval permission.
3. Publisher has publication permission.

**Steps:**

1. Approving Authority grants final approval.
2. Publisher generates final publication bundle.
3. System computes bundle hash.
4. Publisher publishes tender.

**Expected Result:**

1. State changes to `APPROVED_FOR_PUBLICATION`, then `PUBLISHED`.
2. Published bundle is immutable.
3. Bundle hash is recorded.
4. Audit events are recorded.

**Failure Conditions:**

1. Publication allowed without all approvals.
2. Bundle generated without hash.
3. Published bundle can be edited.

---

## 43. Smoke Contract 013 — Supplier Response Schema Generation

**Code:** `IT_WIZ_SMOKE_013_SUPPLIER_SCHEMA`

**Purpose:** Verify the wizard generates the supplier response schema from the approved tender configuration.

**Preconditions:**

1. Configuration is approved or published.
2. Requirements, forms, evidence, and price schedules exist.

**Steps:**

1. System generates supplier response schema.
2. Schema includes mandatory forms, requirement conformance matrix, evidence uploads, price schedules, and declarations.

**Expected Result:**

1. Supplier response schema is generated from the tender configuration.
2. Mandatory requirements are represented.
3. Price schedules are represented.
4. Evidence requirements are represented.

**Failure Conditions:**

1. Supplier schema omits mandatory requirements.
2. Price schedule does not match tender configuration.
3. Schema can be edited independently in supplier portal without addendum.

---

## 44. Smoke Contract 014 — Evaluation Matrix Generation

**Code:** `IT_WIZ_SMOKE_014_EVALUATION_MATRIX`

**Purpose:** Verify evaluation artifacts are generated from published configuration.

**Preconditions:**

1. Tender is published.
2. Evaluation setup exists.

**Steps:**

1. System generates preliminary checklist.
2. System generates technical scoring matrix.
3. System generates financial evaluation model.
4. System generates post-qualification checklist.

**Expected Result:**

1. Evaluation matrix matches published tender criteria.
2. No unpublished criteria can be added silently.
3. Evaluation artifact carries tender and STD version hash.

**Failure Conditions:**

1. Evaluation criteria differ from published tender.
2. Evaluators can add undisclosed scoring criteria.
3. Evaluation artifact lacks traceability.

---

## 45. Smoke Contract 015 — Contract Carry-Forward

**Code:** `IT_WIZ_SMOKE_015_CONTRACT_CARRY_FORWARD`

**Purpose:** Verify tender configuration fields carry forward to contract formation.

**Preconditions:**

1. Tender is published.
2. Supplier has been awarded.
3. Award result exists.

**Steps:**

1. System generates contract formation data set.
2. System maps tender identity, supplier, price, implementation schedule, inventory, SCC terms, security, warranty, IP disclosures, and acceptance requirements.

**Expected Result:**

1. Contract data set is generated.
2. Carry-forward fields match tender and award data.
3. Contract generation artifacts are traceable.

**Failure Conditions:**

1. Contract terms are manually re-entered without trace.
2. Implementation schedule fails to carry forward.
3. Price or security values diverge without approval.

---

## 46. Smoke Contract 016 — Addendum Initiation and Impact Analysis

**Code:** `IT_WIZ_SMOKE_016_ADDENDUM`

**Purpose:** Verify post-publication changes trigger addendum workflow and impact analysis.

**Preconditions:**

1. Tender is `PUBLISHED`.
2. User has `wizard.initiate_addendum` permission.

**Steps:**

1. User initiates addendum to modify one requirement and one deadline.
2. System creates addendum configuration scope.
3. System runs impact analysis.
4. System identifies affected rendered sections, supplier response schema, and evaluation artifacts.

**Expected Result:**

1. Original published bundle remains immutable.
2. Addendum scope is tracked.
3. Impact analysis is generated.
4. Addendum requires review and approval before publication.

**Failure Conditions:**

1. Original tender can be edited directly.
2. Impact analysis is missing.
3. Addendum can be published without approval.

---

## 47. Smoke Contract 017 — Unauthorized Access Rejection

**Code:** `IT_WIZ_SMOKE_017_UNAUTHORIZED_ACCESS`

**Purpose:** Verify unauthorized users cannot edit, approve, or publish tender configurations.

**Preconditions:**

1. User has only `AUDIT_VIEWER` role.
2. Tender configuration exists.

**Steps:**

1. User attempts to edit TDS.
2. User attempts to approve review.
3. User attempts to publish.

**Expected Result:**

1. All write actions are rejected.
2. User may view permitted read-only audit data.
3. Unauthorized attempts are logged.

**Failure Conditions:**

1. Read-only user can edit or approve.
2. Unauthorized attempt is not logged.

---

## 48. Smoke Contract 018 — Hash Verification

**Code:** `IT_WIZ_SMOKE_018_HASH_VERIFICATION`

**Purpose:** Verify generated artifacts can be hash-verified after publication.

**Preconditions:**

1. Tender is published.
2. Publication bundle hash exists.

**Steps:**

1. Audit viewer requests hash verification.
2. System recalculates or verifies stored artifact hash.
3. System returns match result.

**Expected Result:**

1. Hash verification succeeds for unchanged artifact.
2. Any altered artifact fails verification.
3. Verification event is audited.

**Failure Conditions:**

1. Published artifact lacks hash.
2. Altered artifact passes verification.
3. Verification is not audited.

---

## 49. Smoke Contract 019 — NSSF ERP Calibration Fixture

**Code:** `IT_WIZ_SMOKE_019_NSSF_CALIBRATION`

**Purpose:** Verify the real NSSF ERP tender can be represented as a tender instance without modifying the master STD.

**Preconditions:**

1. NSSF ERP calibration fixture is loaded into a non-production test environment.
2. IT STD package exists in draft or active test state.

**Steps:**

1. Create tender configuration for ERP procurement.
2. Map NSSF-style identity, TDS, professional indemnity, technical requirements, implementation phases, scoring criteria, price schedule, SCC terms, and contract forms.
3. Run validation.
4. Generate preview bundle and evaluation matrix.

**Expected Result:**

1. Fixture maps into tender instance records.
2. Master STD package remains unchanged.
3. Deviations or simplifications are flagged as calibration warnings.
4. Requirements and evaluation artifacts are generated structurally.

**Failure Conditions:**

1. Fixture requires modifying master STD legal text.
2. Calibration data is imported as master STD seed data.
3. Significant requirements cannot be represented by the wizard model.

---

## 50. Smoke Contract 020 — Multi-STD Generalization Check

**Code:** `IT_WIZ_SMOKE_020_MULTI_STD_GENERALIZATION`

**Purpose:** Verify that the wizard framework does not hard-code IT-only assumptions into the STD Engine core.

**Preconditions:**

1. At least one non-IT STD family exists in test registry or mock package.
2. Wizard step registry supports conditional step rendering.

**Steps:**

1. Bind a mock non-IT STD family.
2. System hides IT-only steps.
3. System shows only steps exposed by the bound STD package.

**Expected Result:**

1. General wizard framework works with conditional schemas.
2. IT-specific steps do not appear for non-IT STD unless schema exposes them.
3. Core validation still applies.

**Failure Conditions:**

1. IT requirements composer appears for every STD family.
2. Non-IT package cannot use core identity/TDS/review/render lifecycle.
3. Engine has hard-coded IT-only assumptions.

---

## 51. Import Seed Order

The recommended import order is:

1. Wizard role registry.
2. Permission registry.
3. Role-permission mapping.
4. State registry.
5. Transition action registry.
6. Review track registry.
7. Wizard step registry.
8. Parameter group registry.
9. Mutability type registry.
10. Validation severity registry.
11. Requirement type registry.
12. Compliance response registry.
13. Requirement priority registry.
14. Evaluation component registry.
15. Scoring templates.
16. Mandatory requirement archetypes.
17. Price schedule type registry.
18. Implementation milestone type registry.
19. System inventory type registry.
20. Evidence type registry.
21. Contract carry-forward field registry.
22. Audit event type registry.
23. Validation rule registry.
24. Smoke contract registry.
25. NSSF ERP calibration fixture metadata, if environment is non-production.

---

## 52. Minimum Acceptance Criteria

The seed data is acceptable for implementation if:

1. All role codes are unique.
2. All permission codes are unique.
3. Every default role has at least one permission.
4. No final approval or publication permission is assigned to ordinary drafting roles by default.
5. Every wizard state has a defined description and editability rule.
6. Every transition has a source state, target state, permission gate, and validation gate.
7. Every wizard step has sequence, role ownership, and review track mapping.
8. Every validation severity has deterministic behavior.
9. Every smoke contract has preconditions, steps, expected results, and failure conditions.
10. Published tender immutability and addendum-only post-publication changes are enforced.
11. The NSSF ERP calibration fixture is clearly marked as test data and not master STD data.
12. Generalized seed categories remain reusable across STD families.

---

## 53. Activation Blockers

The wizard must not be used for live publication until all of the following are complete:

1. Active IT STD package is legally/procurement reviewed and activated.
2. Full source anchors and clause hashes exist in the STD package.
3. Render templates have been tested against the active STD package.
4. Supplier response schema generation has passed smoke testing.
5. Evaluation matrix generation has passed smoke testing.
6. Contract carry-forward generation has passed smoke testing.
7. User roles have been mapped to real institutional users.
8. Separation-of-duty checks have been tested.
9. Addendum impact analysis has been tested.
10. Published artifact immutability and hash verification have been tested.
11. Audit export has been tested.
12. NSSF ERP calibration has been run successfully in a non-production environment.

---

## 54. Implementation Notes for Cursor Pack

The next Cursor implementation pack should create or update the following:

### 54.1 Backend Models

1. `TenderSTDConfiguration`
2. `TenderSTDConfigurationStateEvent`
3. `TenderSTDConfigurationValue`
4. `TenderRequirement`
5. `TenderRequirementResponseSchema`
6. `TenderImplementationSchedule`
7. `TenderSystemInventoryItem`
8. `TenderPriceScheduleSetup`
9. `TenderEvaluationSetup`
10. `TenderEvidenceRequirement`
11. `TenderSCCValue`
12. `TenderContractCarryForward`
13. `TenderValidationFinding`
14. `TenderReviewTrack`
15. `TenderGeneratedBundle`
16. `TenderAddendum`
17. `TenderAddendumImpact`

### 54.2 Seed Loaders

1. Role seed loader.
2. Permission seed loader.
3. Role-permission mapping seed loader.
4. State and transition seed loader.
5. Wizard step seed loader.
6. Requirement type seed loader.
7. Validation rule seed loader.
8. Evidence type seed loader.
9. Smoke contract seed loader.

### 54.3 Services

1. `TenderSTDConfigurationService`
2. `WizardStepService`
3. `TenderValidationService`
4. `RequirementComposerService`
5. `PriceScheduleSetupService`
6. `EvaluationSetupService`
7. `RenderPreviewService`
8. `SupplierResponseSchemaService`
9. `EvaluationMatrixGenerationService`
10. `ContractCarryForwardService`
11. `AddendumImpactService`
12. `TenderPublicationService`
13. `AuditHashVerificationService`

### 54.4 Test Suites

1. State transition tests.
2. Permission tests.
3. Locked clause tests.
4. TDS validation tests.
5. Requirement composer tests.
6. Price schedule tests.
7. Evaluation setup tests.
8. Review approval tests.
9. Publication immutability tests.
10. Addendum tests.
11. NSSF ERP calibration fixture tests.
12. Multi-STD generalization tests.

---

## 55. Recommended Next Artifact

The next artifact should be:

**IT Tender Configuration Wizard — API, UI, and Service Contract**

That document should define:

1. Backend service contracts.
2. API endpoints.
3. Request/response payloads.
4. Wizard UI screens.
5. Validation execution flow.
6. Review and approval screens.
7. Render preview behavior.
8. Publication behavior.
9. Addendum screens.
10. Supplier response schema generation.
11. Evaluation matrix generation.
12. Contract carry-forward generation.
13. Audit and hash verification behavior.

Only after that should the Cursor implementation pack be produced for the IT Wizard.

---

## 56. Final Position

The seed data and smoke contracts in this document establish the minimum safe implementation baseline for the IT Tender Configuration Wizard.

The most important enforcement points are:

1. Bind every tender configuration to one active STD version.
2. Prevent direct editing of locked legal text.
3. Treat IT requirements, schedules, inventory, pricing, evaluation, and SCC values as structured data.
4. Require validation before review.
5. Require multi-track review before approval.
6. Require final approval before publication.
7. Make published bundles immutable.
8. Use addenda for post-publication changes.
9. Carry forward tender data into supplier response, evaluation, award, and contract formation.
10. Preserve auditability, source traceability, and hash verification throughout.

This is the correct next foundation for implementation.

