**PLN-GF-001 — Clean Procurement Planning**

Statutory Procedure, Prescribed Form and System-Control Matrix

**Document series:** KenTender Greenfield MVP-1 Revision Ledger

**Version:** 0.1 — Draft for Product Owner review

**Date:** 20 August 2026

**Authority baseline:** Constitution of Kenya, PPADA 2015 and PPAD Regulations 2020, as currently consolidated

**Supersession:** No requirements, models, screens, states or seed records are inherited from pre-greenfield Procurement Planning documents

**Governing decision.** Procurement Planning is a separate statutory module between Departmental Needs and Procurement Requisitions. Its output is an approved, published Annual Procurement Plan containing eligible Plan Items. It neither initiates a procurement proceeding nor creates a Tender.

# 1\. Purpose and decision

This change unit establishes the statutory and control foundation for the greenfield Procurement Planning module. It identifies what the law requires, how the prescribed Annual Procurement Plan is represented, who is authorised to act, and which non-bypassable system controls are necessary. Later change units may refine screens and implementation detail but may not contradict this foundation.

## 1.1 Greenfield completeness rule

Include every field, decision, actor and evidence record required by Kenyan law or necessary to implement a statutory obligation safely.

Use international practice only to improve traceability, budget integration, aggregation discipline, transparency and internal control; it must not introduce a foreign form, additional approval gate or discretionary questionnaire.

Do not ask users to re-enter values that can be derived from Configuration, Strategy Alignment, Budget & Funding or Departmental Needs.

Do not retain compatibility aliases, legacy data models, fallback reads, dual writes, migration code or seed-repair logic.

Do not implement unsupported cases through free text. A legally required case that MVP-1 cannot process must be clearly unavailable and fail closed.

## 1.2 Binding lifecycle

Configuration and Governance establishes the Procuring Entity, financial year, approval authority, role assignments, method catalogue, reservation rules and planning window.

Strategy Alignment and Budget & Funding provide governed references; Planning may read but may not alter them.

Departmental Needs supplies accepted, HoD-owned need records for the relevant financial year.

Procurement Planning forms departmental procurement plans, consolidates them and produces the approved Annual Procurement Plan.

Procurement Requisitions later draw down eligible Approved Plan Items and formally initiate particular procurements.

Tender Preparation begins only from an authorised Procurement Requisition.

# 2\. Authority hierarchy and interpretive rule

| **Priority** | **Authority**                                           | **System treatment**                                                                                                |
| ------------ | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **1**        | Constitution of Kenya, Article 227                      | Controlling principles: fairness, equity, transparency, competition and cost-effectiveness.                         |
| **2**        | Public Procurement and Asset Disposal Act, 2015         | Binding duties, accountability, budgeting, planning and anti-splitting requirements.                                |
| **3**        | Public Procurement and Asset Disposal Regulations, 2020 | Binding procedure, actors, plan content, prescribed form, e-procurement and publication requirements.               |
| **4**        | Applicable binding financing agreement                  | Applies only where legally operative; must be configured against the affected plan or item and may not be presumed. |
| **5**        | National Treasury and PPRA instruments                  | Apply where current, authorised and consistent with higher law.                                                     |
| **6**        | International good practice                             | Non-binding design guidance only; cannot override Kenyan law or create additional business requirements.            |

**Interpretive rule.** Where sources differ, KenTender must follow the higher applicable Kenyan authority. Product convenience, an earlier prototype or an international template is not a lawful basis for changing the statutory process.

# 3\. Statutory module boundary

| **Planning reads**                             | **Planning owns**                                              | **Planning must not own**                                                        |
| ---------------------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| **PE and FY configuration**                    | Annual Plan root and immutable versions                        | Procuring Entity or financial-year master data                                   |
| **Accepted Departmental Needs**                | Departmental procurement plans and submissions                 | Need approval, Need amendment or technical-detail correction                     |
| **Strategy references**                        | Consolidated Plan Items and source allocations                 | Strategy objectives, programmes or approval                                      |
| **Budget lines, ceilings and funding sources** | Planning estimates, schedules, methods and packaging decisions | Budget creation, budget approval or financial ledger entries                     |
| **Configured statutory approval route**        | Plan decisions, evidence, publication and version lineage      | Procurement Requisitions, Tender records, bids, evaluations, awards or contracts |

**Downstream boundary.** An Approved Plan Item becomes eligible for a Procurement Requisition. It must never create a Tender directly. Deficient upstream facts are corrected in their owning module and then re-projected into Planning.

# 4\. Statutory actor and authority matrix

| **Actor**                         | **Statutory or control responsibility**                                                                                                  | **KenTender authority**                                                                                                                    |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **User Department**               | Prepare departmental procurement requirements and the departmental plan; provide the requirement description, unit, quantity and timing. | May prepare only its assigned department's Draft departmental plan from eligible Needs.                                                    |
| **Head of User Department**       | Submit the annual departmental procurement plan before the financial year and own the truth of the departmental requirement.             | Certify and submit; return to preparers; withdraw only before consolidation acceptance.                                                    |
| **Procurement Planner**           | Perform professional planning work within the Procurement Function.                                                                      | Validate, consolidate, schedule and propose packaging and method; cannot approve the statutory plan.                                       |
| **Head of Procurement Function**  | Prepare the consolidated procurement plan through the Procurement Function; advise on aggregation, method and compliance.                | Professionally validate the consolidated version and submit it for Accounting Officer preparation/certification.                           |
| **Finance/Budget Officer**        | Support integration with the approved budget and confirm the referenced budget/funding evidence.                                         | Confirm or reject the financial reconciliation; cannot approve the procurement plan unless separately assigned as the statutory authority. |
| **Accounting Officer**            | Primarily accountable; prepare a realistic annual plan within budget and ensure sufficient funds before procurement begins.              | Certify the consolidated version and submit it to the configured statutory approving authority.                                            |
| **Statutory Approving Authority** | Approve the consolidated annual plan according to PE type: Cabinet Secretary, relevant CEC member, board or similar body.                | Approve or return; authority must be configured and effective for the PE/FY.                                                               |
| **System Administrator**          | Technical administration only.                                                                                                           | Audited read-only access to planning data plus configuration administration; no planning or approval decision authority.                   |
| **Auditor/Oversight**             | Examine compliance and evidence.                                                                                                         | Read-only access within lawful scope; no workflow actions.                                                                                 |

## 4.1 Segregation rules

A user must possess an effective PE/FY-scoped assignment for every business action.

Selecting a PE or FY filters authorised data; it does not create authority or ownership.

No person may approve a plan version they prepared or professionally validated where the configured route requires segregation.

Delegation is recognised only when the enabling authority, delegate, scope and effective dates are recorded; there is no generic role fallback.

Administrative privilege never implies procurement, financial or statutory approval authority.

# 5\. Statutory procedure and system-control matrix

| **Stage**                           | **Responsible actor**                          | **Required result**                                                                                   | **Non-bypassable system control**                                                                                           |
| ----------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| 1\. Open annual cycle               | Configuration authority / Procurement Function | One governed planning cycle for the authorised PE/FY.                                                 | PE, FY, planning window, approval route, reservation rules and role assignments must be active.                             |
| 2\. Form departmental plan          | User Department                                | Eligible accepted Needs are assembled into the department's annual plan.                              | Only accepted Needs mapped to the PE, department and governed FY may be selected; source facts remain read-only.            |
| 3\. Departmental submission         | Head of User Department                        | Departmental plan is certified and submitted before the financial year.                               | Completeness, ownership and timing are validated; the submission is immutable and timestamped.                              |
| 4\. Professional validation         | Procurement Function                           | Submissions are checked and accepted or returned with actionable reasons.                             | No silent editing of HoD-owned facts; returned issues identify the owning record and required correction.                   |
| 5\. Consolidate and package         | Procurement Function                           | Compatible requirements are aggregated into Plan Items and incompatible requirements remain separate. | Source allocation totals reconcile; anti-splitting and duplicate-source checks run before submission.                       |
| 6\. Method and schedule             | Procurement Function                           | Each Plan Item has an authorised procurement method and coherent statutory milestone schedule.        | Only configured methods with represented legal conditions are selectable; unsupported cases fail closed.                    |
| 7\. Financial reconciliation        | Finance/Budget Officer                         | Estimated cost, budget line, available ceiling and funding source reconcile.                          | No version proceeds where an item is unfunded, exceeds the available ceiling or refers to inactive funding evidence.        |
| 8\. Statutory allocation validation | Procurement Function / Finance                 | Plan-level reservation obligations are met and evidenced.                                             | The applicable national and county reservation rules are calculated from governed configuration; no manual status override. |
| 9\. AO preparation/certification    | Accounting Officer                             | The realistic consolidated plan is certified as prepared within budget.                               | All departmental submissions, professional validation and finance evidence must be complete.                                |
| 10\. Statutory approval             | Configured approving authority                 | The plan is approved or returned with reasons.                                                        | Authority is derived from PE type and effective assignment; approval creates an immutable decision record.                  |
| 11\. Publication                    | Procurement Function under AO accountability   | Approved plan is uploaded/published through the State Portal integration.                             | Publication success requires external acknowledgement; it cannot be self-declared and is not tender advertisement.          |
| 12\. Activation                     | System                                         | The published approved version becomes the sole active annual plan for its PE/FY.                     | Only one active version is permitted; approved values are immutable.                                                        |
| 13\. Monitor implementation         | Procurement Function / Accounting Officer      | Actual milestones and quarterly implementation reporting are maintained.                              | Monitoring updates actuals only; they do not rewrite the approved baseline.                                                 |
| 14\. Amend                          | Authorised Planning actors                     | A Draft successor is prepared and follows the applicable validation, approval and publication route.  | The active version remains operative until the successor becomes active; no in-place amendment.                             |
| 15\. Requisition eligibility        | System / Requisitions module                   | Eligible Plan Items are exposed for formal Procurement Requisition.                                   | Read-only projection includes active version, remaining quantity/value and legal eligibility; no direct Tender action.      |

# 6\. Prescribed Annual Procurement Plan form crosswalk

Regulation 42 adopts the Third Schedule Annual Procurement Plan. Regulation 41 adds mandatory plan content that the prescribed schedule must operationalise. KenTender shall capture the following without adding narrative fields that are not needed for a legal or control purpose.

## 6.1 Plan header

| **Required value**              | **Source / entry rule**                                                 | **Storage rule**                                                    |
| ------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------- |
| **Ministry/Parastatal**         | Derived from the configured PE hierarchy; never free typed on the plan. | Immutable snapshot on each submitted version.                       |
| **Procuring Entity name**       | Derived from the selected authorised PE.                                | PE reference plus immutable display snapshot.                       |
| **Project name, if applicable** | Shown only where an applicable governed project reference exists.       | Nullable project reference and snapshot; no compulsory placeholder. |
| **Financial year**              | Derived from the governed PE/FY context.                                | Immutable FY reference and start/end dates on submitted version.    |

## 6.2 Plan Item and implementation schedule

| **Prescribed / statutory value**                  | **KenTender treatment**                                                                                                    | **Authoritative source**                                                    |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **Item number**                                   | System-generated sequence within the submitted Plan Version.                                                               | Planning                                                                    |
| **Requirement description**                       | Comprehensive planning description but not technical specifications.                                                       | Accepted Need; editable only through upstream correction where source-owned |
| **Requirement type**                              | Goods, works, non-consulting services or consulting services; required to apply the correct legal controls.                | Accepted Need / Procurement validation                                      |
| **Unit**                                          | Universally accepted unit of purchase or issue.                                                                            | Accepted Need                                                               |
| **Quantity**                                      | Total planned quantity, reconciled to all contributing Need allocations.                                                   | Accepted Need allocations                                                   |
| **Procurement method**                            | Configured legal method; Open Tender is available by default. Alternative methods require configured statutory conditions. | Procurement Function / governance catalogue                                 |
| **Source of funds**                               | Reference to the governed funding source; display such as Government of Kenya or donor.                                    | Budget & Funding                                                            |
| **Estimated cost**                                | Stored in KES at full precision; rendered in the prescribed Kshs '000 format. Must include applicable incidental costs.    | Planning estimate reconciled to Budget & Funding                            |
| **Single- or multi-year treatment**               | Single-year is supported in MVP-1. A multi-year requirement is identified and blocked pending its governed feature.        | Planning                                                                    |
| **Aggregation / common-user decision**            | Recorded once per source grouping with concise professional rationale.                                                     | Procurement Function                                                        |
| **Lotting decision**                              | MVP-1 records that no lots are used. A requirement needing lots is blocked rather than flattened into free text.           | Procurement Function                                                        |
| **Transfer responsibility period, if applicable** | Shown only where legally relevant; otherwise absent.                                                                       | Procurement Function                                                        |
| **Invite/advertise date**                         | Planned procurement milestone.                                                                                             | Planning                                                                    |
| **Bid opening date**                              | Planned procurement milestone.                                                                                             | Planning                                                                    |
| **Bid evaluation date / duration**                | Planned milestone subject to statutory limits.                                                                             | Planning                                                                    |
| **Tender award approval date**                    | Planned milestone, not an award decision.                                                                                  | Planning                                                                    |
| **Notification of award date**                    | Planned milestone.                                                                                                         | Planning                                                                    |
| **Contract signing date**                         | Planned milestone.                                                                                                         | Planning                                                                    |
| **Total time to contract signature**              | Derived from planned dates; never manually duplicated.                                                                     | System-derived                                                              |
| **Delivery / implementation / completion date**   | Planned result date; must align with the Need's required-by period.                                                        | Accepted Need and Planning                                                  |
| **Actual dates and variance**                     | Captured only during implementation monitoring; never overwrite planned dates.                                             | Monitoring                                                                  |

## 6.3 Minimal system metadata

Plan, version and Plan Item identifiers;

source Departmental Plan, Need and source-allocation identifiers;

record state, version number and predecessor/successor linkage;

actor, authority, timestamp, decision, reason and evidence references;

publication request, acknowledgement, timestamp and failure evidence; and

created/modified audit metadata generated by the platform.

**No duplicate entry.** Identifiers, names, PE/FY dates, organisation units, budget labels, funding-source labels, totals, durations and percentages are derived or referenced. They are not additional user-entered form fields.

# 7\. Minimum domain model

| **Record**                        | **Purpose**                                                                           | **Non-negotiable invariants**                                                                |
| --------------------------------- | ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **Planning Cycle**                | Governs planning for one PE/FY.                                                       | Unique PE/FY; configuration-owned dates and authority route; cannot grant user access.       |
| **Departmental Procurement Plan** | Statutory departmental submission container.                                          | One current submission per department/cycle; submitted version immutable; owned by HoD.      |
| **Departmental Plan Entry**       | Projects an accepted Need into the departmental plan.                                 | Exactly one source Need; source facts read-only; no requisition or tender state.             |
| **Annual Procurement Plan**       | Stable plan identity for one PE/FY.                                                   | Unique PE/FY; never hard-deleted after submission.                                           |
| **Plan Version**                  | Immutable snapshot submitted for certification, approval and publication.             | Monotonic version; one active version; approved values immutable.                            |
| **Plan Item**                     | Consolidated statutory procurement requirement and execution unit.                    | Belongs to one version; complete Third Schedule projection; no blank item.                   |
| **Plan Source Allocation**        | Reconciles one or more departmental entries to a Plan Item.                           | Allocated quantity/value cannot exceed source; totals reconcile exactly.                     |
| **Planning Decision**             | Captures submission, validation, finance confirmation, AO certification and approval. | Actor authority effective at decision time; immutable; reason required for return/rejection. |
| **Plan Publication**              | Captures State Portal transmission and acknowledgement.                               | No success without acknowledgement; payload hash and version reference immutable.            |
| **Plan Monitoring Entry**         | Records actual milestone or quarterly progress without changing baseline.             | References active/superseded version and item; append-only corrections.                      |

## 7.1 Deliberately excluded records

A second Demand, Need or Requisition model inside Planning;

generic Approval, Treatment, Score, Questionnaire or Compliance-result objects;

duplicate PE, FY, Strategy, Budget, Organisation Unit or User masters;

Tender shell, Tender release or bid-submission records;

mutable 'approved' flags without an immutable decision; and

legacy compatibility, migration, repair or alias records.

# 8\. State and transition foundation

## 8.1 Departmental Procurement Plan

| **From**         | **Action**               | **To**                     | **Guard**                                                                         |
| ---------------- | ------------------------ | -------------------------- | --------------------------------------------------------------------------------- |
| Draft            | Submit                   | Submitted                  | HoD authority; eligible entries; complete statutory fields; planning window open. |
| Submitted        | Return                   | Returned                   | Procurement authority; actionable reason required.                                |
| Returned         | Resubmit                 | Submitted                  | HoD authority; source corrections completed; new immutable submission snapshot.   |
| Submitted        | Accept for consolidation | Accepted for consolidation | Procurement validation complete; no unresolved blocking issue.                    |
| Draft / Returned | Withdraw                 | Withdrawn                  | HoD authority; not accepted for consolidation; reason required.                   |

## 8.2 Consolidated Plan Version

| **From**                               | **Action**                  | **To**                         | **Guard**                                                                                       |
| -------------------------------------- | --------------------------- | ------------------------------ | ----------------------------------------------------------------------------------------------- |
| Draft                                  | Begin consolidation         | Under consolidation            | Accepted departmental submissions exist.                                                        |
| Under consolidation                    | Submit for AO certification | Ready for AO                   | Professional validation, reconciliation, schedule, method and statutory allocation checks pass. |
| Ready for AO                           | Certify and submit          | Awaiting statutory approval    | AO authority; Finance evidence current; immutable submission snapshot created.                  |
| Awaiting statutory approval            | Return                      | Returned                       | Configured approver; actionable reason required.                                                |
| Returned                               | Create corrected successor  | Draft                          | No editing of returned submission snapshot; lineage retained.                                   |
| Awaiting statutory approval            | Approve                     | Approved — publication pending | Configured statutory authority; valid effective assignment; immutable approval.                 |
| Approved — publication pending         | Publish                     | Active                         | State Portal acknowledgement for the exact approved payload/version.                            |
| Active                                 | Activate approved successor | Superseded                     | Successor has been approved and published atomically; only one active version remains.          |
| Draft / Under consolidation / Returned | Cancel                      | Cancelled                      | Authorised actor; reason; no effect on an existing Active version.                              |

**Status discipline.** Finance confirmation, professional validation, AO certification and statutory approval are immutable decisions and gates. They are not user-editable status fields.

# 9\. Core system-control matrix

| **Control**             | **Failure condition**                                                                                          | **Required system response**                                                       | **Evidence**                                           |
| ----------------------- | -------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------ |
| PE/FY authority         | Actor lacks an effective scoped assignment.                                                                    | Deny access/action server-side; do not reveal unauthorised data.                   | Assignment and denial audit event.                     |
| Need eligibility        | Need is not accepted, belongs to another PE/FY/department, is withdrawn or has incompatible required-by dates. | Exclude or block with owning-record explanation.                                   | Source ID, state and eligibility evaluation.           |
| Source reconciliation   | Allocated quantity/value differs from source totals or a source is reused inconsistently.                      | Block submission.                                                                  | Allocation ledger and validation result.               |
| Budget reconciliation   | Missing/inactive budget line, insufficient ceiling, inconsistent funding source or stale confirmation.         | Block AO submission.                                                               | Budget reference, checked amount, actor and timestamp. |
| Excess consumption      | Quantity materially exceeds accepted departmental requirements without lawful basis.                           | Block or require upstream correction; no Planning-only quantity inflation.         | Comparison result and resolution.                      |
| Anti-splitting          | Similar requirements are separated in a way that could avoid the proper method or threshold.                   | Block submission pending professional resolution.                                  | Potential grouping, values and recorded decision.      |
| Method legality         | Method is unconfigured or its statutory conditions are not represented.                                        | Method unavailable; Open Tender remains default.                                   | Catalogue version and selected basis.                  |
| Estimate reasonableness | Estimate lacks market basis or omits applicable incidental costs.                                              | Block professional validation.                                                     | Estimate components and source evidence.               |
| Schedule coherence      | Milestones are out of order, exceed statutory constraints or miss the required completion date.                | Block submission and identify conflicting dates.                                   | Baseline milestone set and validation output.          |
| Reservation allocation  | Applicable national/county reservation totals are below configured statutory minimums.                         | Block AO submission unless a legally authorised exception exists in configuration. | Computed totals, rule version and item treatment.      |
| Approval authority      | Approver is not the configured legal authority for the PE/FY or assignment is expired.                         | Deny decision.                                                                     | Authority route and assignment snapshot.               |
| Segregation             | Actor attempts an incompatible preparation/validation/approval combination.                                    | Deny decision.                                                                     | Decision-role history.                                 |
| Immutability            | Attempt to edit submitted, approved, active or superseded content.                                             | Reject; require a new version or upstream amendment.                               | Rejected mutation audit event.                         |
| Publication integrity   | Payload differs from approved version or State Portal has not acknowledged it.                                 | Do not activate; remain publication pending or failed.                             | Payload hash, response and timestamps.                 |
| Requisition handoff     | Plan/version/item is not active, item is blocked or remaining quantity/value is insufficient.                  | Do not expose as eligible and deny direct API initiation.                          | Eligibility projection and drawdown ledger.            |

# 10\. Screen and interaction boundary

| **Screen**                         | **Purpose**                                                                                        | **Explicit exclusions**                                                                                |
| ---------------------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **Procurement Planning workspace** | Role-aware work requiring action, waiting work and read-only plan access for the authorised PE/FY. | No global operational authority; no Tender action; no advanced performance dashboard.                  |
| **Departmental Plan**              | Review projected Needs, completeness and submission status; HoD certifies and submits.             | No technical-specification editor; no budget or method approval questionnaire.                         |
| **Consolidated Plan workbench**    | Professional consolidation, source allocation, packaging, method and schedule preparation.         | No free-text methods, duplicate data entry or direct source edits.                                     |
| **Finance reconciliation**         | Confirm budget references, ceilings, funding sources and plan totals.                              | No procurement-plan approval unless the same user separately holds the configured statutory authority. |
| **AO review and certification**    | Review the complete consolidated version and certify it for statutory approval.                    | No editing of submitted values; return with reasons instead.                                           |
| **Statutory approval**             | Approve or return the exact certified Plan Version.                                                | No self-declared approval, silent correction or publication action disguised as approval.              |
| **Approved Annual Plan**           | Read-only prescribed Plan, evidence, version and publication status.                               | No bid-submission affordance; publication wording must say Annual Plan, not Tender.                    |
| **Implementation monitoring**      | Record actual milestones and quarterly implementation progress.                                    | No rewriting of the approved baseline.                                                                 |

## 10.1 Workspace action rule

The primary action is derived from the actor's current assignment and the record's state.

Read-only users may view authorised plans even when they have no pending action.

System Administrators receive audited support visibility but no business action.

A role queue must be computed from effective PE/FY assignments and pending decision ownership, not from saved UI context.

Empty states must distinguish 'no authorised PE/FY context' from 'no work requiring action'.

# 11\. Configuration dependencies

| **Configuration**                       | **Planning use**                                                                     | **Ownership**                                           |
| --------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------- |
| **Procuring Entity and PE type**        | Identity, hierarchy and statutory approving-authority route.                         | Configuration & Governance                              |
| **Financial year and PE/FY activation** | Plan cycle and required-by-date eligibility.                                         | Configuration & Governance                              |
| **Organisation units**                  | Departmental plan ownership and submission routing.                                  | Configuration & Governance                              |
| **Effective user assignments**          | PE/FY-scoped preparation, validation, finance, certification and approval authority. | Configuration & Governance                              |
| **Planning intake window**              | Controls when departmental plans may be formed and submitted.                        | Configuration & Governance                              |
| **Procurement method catalogue**        | Selectable methods, conditions, threshold references and default Open Tender path.   | Configuration & Governance                              |
| **Reservation rules**                   | National and county percentages and applicability.                                   | Configuration & Governance                              |
| **Budget and funding records**          | Ceilings, sources and confirmation evidence.                                         | Budget & Funding                                        |
| **State Portal integration**            | Approved Annual Plan publication and acknowledgement.                                | Configuration & Governance / integration administration |

**Configuration principle.** Planning references effective configuration; it does not copy configuration into editable Planning masters. Version snapshots preserve evidence without creating a second source of truth.

# 12\. Greenfield seed-data contract

Planning seed data must reference the authoritative Configuration, Strategy, Budget and Departmental Needs seeds. It must not recreate users, PE/FY combinations, organisation units, budgets or Needs.

| **Seed**                      | **Required value**                                                                                                                              | **Acceptance purpose**                                                                    |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| **National-government PE/FY** | Ministry of Health — FY 2027/28                                                                                                                 | Exercises Cabinet Secretary approval route and current Planning workflow.                 |
| **Corporate PE/FY**           | NSSF SPS — FY 2025/26                                                                                                                           | Exercises board/similar-body route and read-only historical/closed context as configured. |
| **Annual Plan**               | PLN-MOH-2027-001 — Ministry of Health Annual Procurement Plan 2027/28                                                                           | Stable plan identity for the active test cycle.                                           |
| **Departmental Plan**         | DPP-MOH-DIGITAL-2027-001 — Digital Health                                                                                                       | Exercises HoD certification and Procurement Function acceptance.                          |
| **Source Need**               | DMD-MOH-2027-019; required-by date 31 December 2027                                                                                             | Proves FY mapping, source ownership and read-only projection.                             |
| **Plan Item**                 | PPI-MOH-2027-001 — Digital health technical staff certification programme                                                                       | Exercises single-source Plan Item, prescribed schedule and Requisition eligibility.       |
| **Plan Item classification**  | Non-consulting services; unit: programme; quantity: 1                                                                                           | Exercises requirement classification without specification-level detail.                  |
| **Funding**                   | Government of Kenya; KES 80,000,000; referenced active MOH budget line                                                                          | Exercises budget reconciliation and prescribed Kshs '000 rendering.                       |
| **Method**                    | Open Tender                                                                                                                                     | Exercises the default legally supported MVP-1 method.                                     |
| **Planned milestones**        | Invite 1 Sep 2027; open 23 Sep; evaluation complete 23 Oct; award approval 10 Nov; notification 14 Nov; signature 1 Dec; completion 31 Dec 2027 | Exercises schedule ordering, derived duration and required-by alignment.                  |

## 12.1 Seed states required

No annual plan yet, to validate the authorised empty state;

Draft departmental plan awaiting HoD submission;

Submitted departmental plan awaiting Procurement validation;

Consolidated Draft with a Finance reconciliation issue;

Plan Version awaiting Accounting Officer certification;

Plan Version awaiting statutory approval;

Approved Plan pending State Portal publication; and

Active published Plan with one Plan Item eligible for Procurement Requisition.

**Seed rule.** Seeds are deterministic, idempotent and valid on a fresh installation. No seed may import a retired Demands package, repair old records or depend on execution order outside the declared seed manifest.

# 13\. Implementation controls

## 13.1 Server-side authority

Every query and mutation resolves effective actor assignments, PE and FY on the server.

Client filters, route parameters and saved context are never trusted as authority.

Transition services calculate the permitted action from current state and immutable decisions; clients do not write state directly.

List, count, workspace and detail services apply the same visibility predicate.

## 13.2 Transaction and concurrency

Submission, approval, publication activation and successor activation are atomic transactions.

Optimistic version checks prevent decisions against stale Plan Versions.

A unique database constraint enforces one Annual Plan per PE/FY and one Active version per Plan.

Source allocation, budget confirmation and reservation totals are revalidated immediately before AO certification and approval.

## 13.3 Audit and evidence

Store immutable decision records rather than mutable booleans.

Record the authority route, effective assignment, actor, timestamp, source version, decision and reason.

Hash submitted and published payloads so the approved and State Portal versions can be proven identical.

Expose evidence through a read-only 'View Evidence' surface; do not clutter the primary workflow with audit metadata.

## 13.4 No legacy compatibility

No imports from retired demands or earlier planning packages;

no aliases for old Doctypes, routes, services, roles or statuses;

no migration patches, dual-read, dual-write or fallback projections;

no preservation of old Planning Home or direct Plan-to-Tender actions; and

no seeding from legacy fixtures.

# 14\. MVP-1 exclusions and fail-closed treatment

| **Capability**                                               | **MVP-1 disposition** | **Required behaviour**                                                                    |
| ------------------------------------------------------------ | --------------------- | ----------------------------------------------------------------------------------------- |
| **Multi-year Plan Items**                                    | Deferred              | Identify the case and block submission; do not coerce into a single-year record.          |
| **Lots**                                                     | Deferred              | If lots are required, block the Plan Item; do not flatten or free-type lot data.          |
| **Non-open procurement methods lacking governed conditions** | Unavailable           | Do not show the method. Open Tender remains the supported default path.                   |
| **Direct Tender creation**                                   | Prohibited            | Only the Requisitions module may consume an eligible Active Plan Item.                    |
| **Advanced strategy-performance dashboard**                  | Excluded              | Strategy references remain read-only; no Planning analytics product is created.           |
| **Automated method or packaging decision**                   | Excluded              | The system validates professional decisions; it does not make or score them autonomously. |
| **Legacy data migration**                                    | Prohibited            | Fresh install and fresh seed only.                                                        |

# 15\. Acceptance and smoke contract

| **ID**         | **Acceptance criterion**                                                                                                                       |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **PLN-AC-001** | A fresh installation creates the declared PE/FY references, Planning records and assignments without importing any retired module.             |
| **PLN-AC-002** | A departmental preparer sees only eligible accepted Needs for the assigned department and PE/FY.                                               |
| **PLN-AC-003** | A Head of User Department can certify and submit the complete departmental plan; another HoD cannot act on it.                                 |
| **PLN-AC-004** | Procurement can return a departmental submission but cannot silently edit a source-owned description, unit or quantity.                        |
| **PLN-AC-005** | Consolidation maintains exact source allocation and detects duplicate or potentially fragmented requirements.                                  |
| **PLN-AC-006** | An unsupported method, multi-year arrangement or lot requirement fails closed with a precise explanation.                                      |
| **PLN-AC-007** | Finance reconciliation blocks an unfunded or over-ceiling item and records the confirming actor and budget evidence.                           |
| **PLN-AC-008** | Applicable reservation percentages are computed from configured rules and cannot be overridden through the UI or API.                          |
| **PLN-AC-009** | The Accounting Officer can certify but cannot substitute for the configured Cabinet Secretary/CEC/board approval where that authority applies. |
| **PLN-AC-010** | Approval creates an immutable Plan Version and decision; direct updates to approved values fail.                                               |
| **PLN-AC-011** | The plan remains publication pending until the State Portal acknowledges the exact approved payload.                                           |
| **PLN-AC-012** | Publishing the Annual Plan does not create a Tender, bidding window, tender notice or bid-submission route.                                    |
| **PLN-AC-013** | A Draft successor can be prepared while the existing Active version remains operative; activation supersedes the predecessor atomically.       |
| **PLN-AC-014** | Only an eligible item from the Active Plan Version is exposed to Requisitions, with remaining quantity/value and immutable lineage.            |
| **PLN-AC-015** | System Administrators and authorised oversight users can read lawful plan data but cannot perform business decisions.                          |
| **PLN-AC-016** | Workspace counts, queues, detail permissions and direct API access apply the same PE/FY authority rules.                                       |
| **PLN-AC-017** | Rendered Third Schedule output contains every required plan field and derives totals and durations without duplicate manual entry.             |
| **PLN-AC-018** | Automated unit, integration, permission, transition and browser smoke tests pass on a freshly installed and seeded site.                       |

# 16\. Best-practice controls adopted — and limits

| **Practice**                        | **KenTender application**                                                                         | **Limit against scope growth**                                                     |
| ----------------------------------- | ------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| **Public-finance integration**      | Reference governed budgets, prevent commitments above ceilings and monitor plan versus execution. | No duplicate financial ledger, payment or budget-approval workflow.                |
| **Transparency and objectivity**    | Immutable versions, visible reasons, prescribed output and evidence-backed publication.           | No additional public consultation or approval stage unless Kenyan law requires it. |
| **Aggregation and value for money** | Professional grouping, anti-splitting checks, market estimates and coherent packaging.            | No opaque score or automated recommendation.                                       |
| **Risk-based control**              | Focused red flags for fragmentation, funding, method legality, schedule and authority.            | No generic risk register or questionnaire in MVP-1.                                |
| **End-to-end digital traceability** | Stable IDs and immutable lineage from Need to Plan Item and later Requisition.                    | No Planning-owned Tender or contract records.                                      |

**Best-practice filter.** A practice is adopted only when it strengthens a Kenyan statutory obligation or removes duplicate work. It is rejected when it merely adds data, screens, scoring, approvals or process ceremony.

# 17\. Decisions fixed by this change unit

Procurement Planning is a distinct module; Requisitions is its downstream consumer.

The statutory departmental procurement plan exists inside Planning and is submitted by the Head of User Department.

The Procurement Function prepares the consolidated plan under the Accounting Officer's statutory accountability.

The final statutory approving authority is configured by PE type; the Accounting Officer is not assumed to be the universal final approver.

The Third Schedule and Regulation 41 define the minimum Annual Plan content.

Approved Plan publication is State Portal transparency, not Tender publication.

Approved and published Plan Versions are immutable; amendments use governed successors.

An Active Plan Item may feed only a Procurement Requisition, never a Tender directly.

Unsupported cases fail closed, and no legacy compatibility is permitted.

# 18\. Next change unit

After Product Owner approval, the next integrated artifact is **P2 — Plan Cycle and PE/FY Governance**. It will define cycle configuration consumption, planning windows, PE/FY assignment behaviour, authorised context selection, one-plan-per-cycle enforcement and exact workspace entry states.

# Appendix A — Source register

**S1 Constitution of Kenya, 2010, Article 227**

<https://new.kenyalaw.org/akn/ke/act/2010/constitution/eng@2022-12-31>

**S2 Public Procurement and Asset Disposal Act, 2015 (Cap. 412C), especially sections 44, 45, 53 and 54**

<https://new.kenyalaw.org/akn/ke/act/2015/33/eng@2022-07-26>

**S3 Public Procurement and Asset Disposal Regulations, 2020, especially regulations 33, 34, 40–43, 50, 52 and 54; Third Schedule**

<https://new.kenyalaw.org/akn/ke/act/ln/2020/69/eng@2022-12-31>

**S4 Government of Kenya e-GP Portal — Annual Procurement Plan and Procuring Entity capabilities**

<https://egpkenya.go.ke/>

**S5 PPRA Circular 05/2023 — Publication of Annual Procurement Plans**

<https://ppra.go.ke/download/circular-052023/>

**S6 OECD, Government at a Glance 2025 — Integration of public procurement with public financial management**

<https://www.oecd.org/en/publications/2025/06/government-at-a-glance-2025_70e14c6c/full-report/integration-of-public-procurement-with-public-financial-management_4e0333b7.html>

**S7 UNCITRAL Model Law on Public Procurement (2011)**

<https://uncitral.un.org/en/texts/procurement/modellaw/public_procurement>

**S8 World Bank — Procurement for Borrowers and procurement-planning framework**

<https://www.worldbank.org/ext/en/what-we-do/project-procurement/for-borrowers>

# Appendix B — Source-to-control traceability

| **Authority**                    | **Planning obligation**                                                                                              | **Implemented control area**                                                              |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| **PPADA s.44**                   | AO accountability, budget conformity, documentation, segregation and preference reporting.                           | Actor matrix; budget, evidence, segregation and reservation controls.                     |
| **PPADA s.45**                   | Systematic corporate decisions; within budget; annual planning; thresholds; Article 227.                             | Configured routes, immutable decisions and method controls.                               |
| **PPADA s.53**                   | Realistic annual plan, budget integration, reservations, multi-year consistency, sufficient funds and methods.       | Plan lifecycle, budget gate, reservation validation and fail-closed multi-year treatment. |
| **PPADA s.54 / Reg.43**          | No contract splitting; price reasonableness and market references.                                                   | Aggregation, anti-fragmentation and estimate controls.                                    |
| **Reg.33**                       | Procurement Function prepares consolidated plans, advises on aggregation and conducts market surveys.                | Professional consolidation, packaging and estimate evidence.                              |
| **Reg.34**                       | User Department prepares departmental plans and technical requirements.                                              | Departmental plan and upstream source ownership.                                          |
| **Reg.40**                       | Departmental submission, consolidated-plan preparation, approving authority and quarterly reporting.                 | Governance route, monitoring and PE-type approval configuration.                          |
| **Reg.41**                       | Detailed content, schedules, arrangements, packaging, lots, funding, method and incidental costs.                    | Plan Item form crosswalk and completeness validation.                                     |
| **Reg.42 / Third Schedule**      | Prescribed Annual Procurement Plan format and milestones.                                                            | Rendered statutory output and structured schedule fields.                                 |
| **Reg.50**                       | Electronic plan preparation, configured approval and State Portal upload/publication.                                | Publication record, acknowledgement and Active-state gate.                                |
| **Reg.52**                       | Electronic requisition through Procurement Function.                                                                 | Planning ends at Requisition eligibility; no direct Tender creation.                      |
| **OECD / UNCITRAL / World Bank** | Budget integration, objective decisions, transparency, risk controls, digital tracking and fit-for-purpose planning. | Minimal traceability and validation controls only; no foreign form or approval.           |