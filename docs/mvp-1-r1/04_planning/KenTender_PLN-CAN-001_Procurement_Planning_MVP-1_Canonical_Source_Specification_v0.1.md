**KENTENDER PROCUREMENT PLANNING**

**PLN-CAN-001**

**Procurement Planning MVP-1 Canonical Source Specification**

Single source of product truth

**Document series:** KenTender Procurement Planning Re-baseline

**Version:** 0.1 - Approved

**Date:** 21 August 2026

**Canonical fingerprint:** sha256:2e8e8790309b4d738ab80934f609111753f94766aab8e4bf2d3313146289e879

**Applies to:** Procurement Planning MVP-1

**Authority:** Sole Planning product-truth baseline after approval

**Derivative set:** Functional Requirements; Stitch Contract; Seed Data Contract; Implementation Pack

**Visual posture:** Reuse existing Planning UI composition; apply only canonical semantic corrections

**Build posture:** Greenfield schema and services; no legacy compatibility

**Legal posture:** Primary-law duties retained; 2020 Regulations-dependent claims explicitly bounded

**Controlling decision.** This document alone owns Procurement Planning product truth. Every derivative shall cite this exact version and fingerprint and shall introduce no new requirement.

# **1\. Canonical decision, status and use**

This document is the sole product-truth specification for KenTender Procurement Planning MVP-1. It consolidates the accepted statutory, product, governance, domain, interaction, seed, implementation and acceptance decisions into one self-contained baseline. No earlier Procurement Planning document is required to determine current behaviour.

**Canonical decision.** Procurement Planning consumes current accepted Departmental Needs, forms and validates Departmental Procurement Plans, consolidates accepted departmental submissions into one Annual Procurement Plan for each Procuring Entity and financial year, reconciles funding, obtains professional validation, Accounting Officer certification and the configured statutory approval, publishes the approved Annual Plan through the governed external channel, and exposes active Plan Items for Procurement Requisitions. It does not create a Tender.

## **1.1 Document control**

| **Item**                      | **Canonical value**                                                                                            |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Document ID                   | PLN-CAN-001                                                                                                    |
| Title                         | KenTender Procurement Planning MVP-1 Canonical Source Specification                                            |
| Version                       | 0.1                                                                                                            |
| Date                          | 21 August 2026                                                                                                 |
| Status                        | Approved                                                                                                       |
| Canonical content fingerprint | sha256:2e8e8790309b4d738ab80934f609111753f94766aab8e4bf2d3313146289e879                                        |
| Scope                         | Procurement Planning MVP-1, from accepted Departmental Need intake through active-plan Requisition eligibility |
| Product authority             | Sole Procurement Planning source after approval                                                                |
| Implementation authority      | None until this version and all release-blocking authority assumptions are approved                            |
| Visual baseline               | Existing KenTender Planning UI composition, corrected only where this document requires                        |
| Build posture                 | Greenfield schema and services; UI composition reuse; no legacy compatibility                                  |

The fingerprint is SHA-256 over the UTF-8 canonical Markdown source with the fingerprint field represented by a fixed placeholder during hashing. Every derivative shall name this document ID, version and fingerprint exactly.

## **1.2 Derivative architecture**

This canonical source is followed by four separate controlled derivatives:

| **Derivative**          | **Purpose**                                                                                           | **Binding rule**                                                                                                                                                 |
| ----------------------- | ----------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Functional Requirements | Complete actor, task, record, validation, state, command and acceptance requirements                  | May restate and organise canonical functional truth; may not add product behaviour.                                                                              |
| Stitch Contract         | Exact visible composition for every admitted screen and state                                         | May specify layout from the canonical screen registry and approved UI assets; may not infer fields, actors, commands, states or outcomes.                        |
| Seed Data Contract      | Deterministic integrated story, isolated state profiles, reset rules and expected projections         | May instantiate only canonical records and values; may not repair or reinterpret upstream truth.                                                                 |
| Implementation Pack     | Standalone schema, service, route, authorization, transaction, event, observability and test contract | May choose technical implementation detail only where the canonical source expressly leaves it open; may not consult historical Planning documents to fill gaps. |

Each derivative cover shall state the exact canonical ID, version and fingerprint; its own version and approval status; the approved Stitch output version where applicable; and this instruction: **If this derivative conflicts with or omits a required canonical rule, stop and return the issue to PLN-CAN-001. Do not infer a resolution.**

## **1.3 Normative language and priority**

**Shall**, **must**, **required** and **prohibited** are binding. **May** identifies an allowed choice. **Derived** means calculated from authoritative records and never directly written by a client. **Snapshot** means immutable evidence captured at a decision boundary.

If provisions within this document appear to conflict, apply this order:

1. verified current Constitution and primary legislation;
2. expressly stated legal-status limitation in section 2;
3. fixed product decisions and module boundaries;
4. domain ownership and invariants;
5. state, command and authorization contracts;
6. screen registry and visible interaction requirements;
7. fixture values and implementation guidance.

No screen copy, seed value or implementation convenience may override a higher control.

# **2\. Authority status and bounded legal treatment**

## **2.1 Verified primary-law baseline**

The following product controls are grounded directly in the Constitution of Kenya and the Public Procurement and Asset Disposal Act, 2015, subject to final legal review of the latest consolidation:

| **Authority**             | **Verified duty used by KenTender**                                                                                                                                                   | **Canonical product consequence**                                                                                               |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Constitution, Article 227 | Public procurement must operate through a fair, equitable, transparent, competitive and cost-effective system.                                                                        | Decisions, authority, sources, reasons, versions and publication evidence are explicit, reviewable and non-bypassable.          |
| PPADA section 44          | The Accounting Officer is primarily responsible for compliance, budget conformity, planning, records and segregation.                                                                 | AO accountability, budget evidence, immutable records and maker-checker controls are mandatory.                                 |
| PPADA sections 45 and 47  | Procurement decisions are structured and the Procurement Function performs professional procurement work, including planning.                                                         | Planning uses named commands and professional validation; no generic approval or hidden correction.                             |
| PPADA section 53          | An annual procurement plan must be realistic, integrated with indicative or approved budgets, prepared before the financial year and approved through the applicable authority route. | One annual Plan root per PE/FY, budget reconciliation, explicit certification and approval, and fail-closed readiness controls. |
| PPADA section 54          | Contract splitting and procurement-structure abuse are prohibited.                                                                                                                    | Consolidation preserves sources and applies anti-fragmentation checks before certification.                                     |

Official primary sources are listed in Appendix C.

## **2.2 Status of the 2020 Regulations**

The earlier Planning specifications relied on the Public Procurement and Asset Disposal Regulations, 2020 and their Third Schedule as settled current subsidiary legislation. The High Court judgment in **Roads and Civil Engineering Contractors Association & another v Attorney General & another; Public Procurement Administrative Review Board & another, Petition E226 of 2020, \[2025\] KEHC 19224 (KLR), delivered 4 December 2025**, declared those Regulations unconstitutional, null and void ab initio and issued quashing and prohibition orders.

The official sources reviewed for this version did not establish a conclusive Court of Appeal stay or reversal, a replacement general procurement regulation, or a current official direction resolving the judgment's effect. A later 2026 High Court judgment referred to parts of the Regulations, which confirms practical uncertainty but does not resolve it.

Accordingly:

| **Authority class**                                                                            | **Canonical treatment**                                                                                                                                                                      |
| ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Primary-law duty                                                                               | Label as statutory where supported directly by the Constitution or Act.                                                                                                                      |
| Workflow historically derived from regulations 33, 34 and 40-42                                | Adopt as KenTender MVP-1 product policy because it creates a coherent, segregated and auditable planning process; do not claim the exact route is settled current law until validated.       |
| Third Schedule data and milestone content                                                      | Retain as the canonical Annual Plan output profile and historical prescribed-form model; label it **Annual Procurement Plan output** rather than **current statutory form** until validated. |
| Electronic preparation, external submission and publication historically tied to regulation 50 | Retain the integrity and acknowledgement controls as product policy; hold the exact destination, protocol and legal wording for current official confirmation.                               |
| Electronic Procurement Requisition boundary historically tied to regulation 52                 | Retain the Planning-to-Requisition boundary as a fixed KenTender product control independent of the regulation's status.                                                                     |

**Release hold LEG-AUTH-001.** This document may be approved as the Procurement Planning product baseline with the above bounded treatment. No derivative or implementation may describe a regulation-dependent rule as settled current law, label the output a current prescribed statutory form, or enable the external publication integration in production until the legal/policy owner records the operative authority and current publication instrument.

## **2.3 Product-policy assumptions requiring closure**

| **Assumption ID** | **Bounded decision used in this version**                                                                                                 | **Closure required before production release**                                                       |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| ASMP-001          | Departmental Plans are prepared from accepted Departmental Needs, certified by the HoD and validated by Procurement before consolidation. | Legal/policy confirmation of the current formal departmental-planning route.                         |
| ASMP-002          | The configured statutory approving authority depends on PE type; the AO does not automatically become final approver.                     | Approved PE-type authority catalogue and effective-assignment source.                                |
| ASMP-003          | The external publication adapter transmits the exact approved payload and activation waits for authoritative acknowledgement.             | Current e-GPS/State Portal direction, endpoint/protocol, acknowledgement semantics and retry policy. |
| ASMP-004          | The Planning input contract uses Departmental Needs identifiers, accepted state and fields defined in section 6.                          | Approval and exact version reconciliation of the upstream NDS contract.                              |

# **3\. Product scope, lifecycle and module boundary**

## **3.1 End-to-end lifecycle**

The binding lifecycle is:

1. Configuration & Governance declares a PE/FY context, departments, planning window, method catalogue, reservation rules, publication destination, approval route and effective assignments.
2. Strategy Alignment and Budget & Funding provide governed references; Procurement Planning may read and snapshot them but may not alter them.
3. Departmental Needs produces a current Need version in **Accepted for planning** for one PE, FY and department.
4. Procurement Planning projects each eligible accepted Need into the department's Departmental Procurement Plan exactly once and at full accepted quantity.
5. The Head of User Department certifies and submits an immutable Departmental Plan submission addressed to the Accounting Officer.
6. Procurement Function classifies each departmental entry and either returns the submission with structured issues or accepts it for consolidation.
7. **Begin consolidation** atomically creates or opens the single Annual Procurement Plan root and its Draft Version using eligible accepted departmental submissions.
8. Procurement Function forms Plan Items, preserves exact source allocations, records professional procurement treatment and completes the Annual Plan output fields.
9. Finance reconciles every included source allocation and confirms the full required funding atomically or returns the item.
10. Head of Procurement Function performs professional Plan validation and submits the immutable version for AO certification.
11. Accounting Officer certifies the exact version and submits it to the configured statutory approving authority.
12. The configured authority approves or returns the certified version.
13. Procurement Function transmits the exact approved Annual Plan payload through the configured publication adapter. Authoritative acknowledgement activates the version.
14. The active version becomes the sole operational baseline. Eligible Plan Items are exposed to Procurement Requisitions with remaining quantity/value and immutable lineage.
15. Monitoring records actual milestones and variance without rewriting the approved baseline.
16. Amendments use new immutable departmental change submissions and a Draft successor Annual Plan Version. The active predecessor remains operational until an approved and acknowledged successor activates atomically.

## **3.2 Planning reads, owns and excludes**

| **Planning reads**                                       | **Planning owns**                                                                            | **Planning must not own or create**                                          |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Declared PE/FY contexts, PE type, FY dates and timezone  | Planning Cycle and workspace projection                                                      | Duplicate PE, FY, department, user or assignment masters                     |
| Effective assignments and delegations                    | Departmental Procurement Plan roots, entries, submissions, validations, issues and decisions | Need approval, Need amendment or technical source correction                 |
| Current accepted Departmental Need versions              | Annual Procurement Plan root and immutable Plan Versions                                     | Budget creation, budget approval or ledger mutation                          |
| Strategy, programme and project references               | Plan Items, source allocations, professional treatment and planned schedule                  | Procurement Requisition, Tender, bid, evaluation, award or contract records  |
| Budget lines, funding sources, ceilings and availability | Finance reconciliation task references and Planning-side decision evidence                   | Generic approval, questionnaire, treatment, score or compliance objects      |
| Method, reservation and approval-route configuration     | Publication requests/acknowledgements, Requisition eligibility and monitoring evidence       | Legacy Demand, contribution, release-package or direct Tender-handoff models |

## **3.3 MVP-1 supported profile**

MVP-1 supports:

- one declared Procuring Entity and financial year per Planning Cycle;
- one stable Departmental Procurement Plan per department/cycle;
- single-year Plan Items only;
- **No lots expected** only;
- Open Tender as the required configured supported method unless another method is later admitted through a governed canonical update;
- separate or combined Plan Item formation from same-PE/FY accepted departmental entries, including cross-department combination under section 10.4;
- full-value, all-source Finance confirmation;
- professional validation, AO certification, configured statutory approval, publication acknowledgement and activation;
- one active Plan Version and at most one open Draft successor;
- additions, whole-item removals and changed-source amendment submissions; and
- Requisition eligibility and drawdown projection.

Multi-year treatment, lots, unsupported methods, partial source inclusion, partial Finance confirmation and direct Plan-to-Tender initiation are unavailable and fail closed.

# **4\. Canonical terminology and identifiers**

| **Canonical term**                  | **Meaning**                                                                                      | **Prohibited substitute**                               |
| ----------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------- |
| Procurement Planning workspace      | The one role-sensitive Planning landing surface                                                  | PLN-GF-002 workspace; separate role dashboard           |
| Accepted Departmental Need          | Current NDS source in Accepted for planning                                                      | Approved Demand; DMD record                             |
| Departmental Procurement Plan (DPP) | Planning-owned departmental container for current accepted Needs                                 | Departmental contribution; OU workbench                 |
| Departmental Plan Submission        | Immutable HoD-certified DPP snapshot                                                             | Mutable submission flag; routine HoD approval           |
| Accept for consolidation            | Professional intake decision over a DPP submission                                               | Departmental Plan approval; Annual Plan approval        |
| Begin consolidation                 | Guarded creation/opening of the one Annual Plan Draft                                            | Create annual plan; blank plan registration             |
| Annual Procurement Plan             | Stable plan identity for one Planning Cycle                                                      | Separate plan per version; Open Plan as editable status |
| Plan Version                        | Immutable decision boundary under one Annual Plan                                                | Manual revision record; in-place approved edit          |
| Plan Item                           | Consolidated procurement-planning requirement in one Plan Version                                | Tender; Requisition; source Need                        |
| Plan Source Allocation              | Exact quantity/value lineage from a departmental submission entry to a Plan Item                 | Demand Allocation; untraceable merge                    |
| Professional validation             | Head of Procurement Function decision that the Plan is professionally ready for AO certification | Final plan approval                                     |
| AO certification                    | Accounting Officer certification and onward submission                                           | Universal final approval                                |
| Statutory approval                  | Approval by the configured effective authority for that PE/FY                                    | Head-of-Procurement approval; generic review            |
| Approved - publication pending      | Approved immutable version awaiting exact-payload publication acknowledgement                    | Active; Published Tender                                |
| Active                              | Acknowledged published version that is the operational baseline                                  | Approved before acknowledgement                         |
| Ready for requisitioning            | Active item satisfies Requisition eligibility controls                                           | Ready for tendering                                     |
| Publish Annual Procurement Plan     | Transparency transmission of the approved Plan                                                   | Publish Tender; open bidding                            |

Identifier formats are stable and case-sensitive. The canonical examples are CTX-MOH-2027-2028, PLNW-MOH-2027-01, NDS-MOH-2027-0001, DPP-MOH-DIGITAL-2027-001, DPPE-MOH-DIGITAL-2027-001, DPPS-MOH-DIGITAL-2027-001-V1, DPPV-MOH-DIGITAL-2027-001-V1, PLN-MOH-2027-001, PLN-MOH-2027-001-V1, PPI-MOH-2027-021, PSA-MOH-2027-021-001, RSV-MOH-2027-021-001 and downstream PRQ-MOH-2027-001.

# **5\. Roles, capabilities and segregation**

## **5.1 Capability matrix**

| **Actor / capability**             | **Minimum scope**                                                   | **Permitted Planning responsibility**                                                                            | **Explicit prohibition**                                                                  |
| ---------------------------------- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Departmental Plan Preparer         | PE + FY + department                                                | View projected accepted Needs, review coverage and follow upstream correction links                              | Submit as HoD; edit source facts; classify; validate; consolidate                         |
| Head of User Department            | PE + FY + department                                                | Certify and submit initial or amendment DPP; withdraw only an unaccepted Draft/Returned plan                     | Validate own submission; edit source facts in Planning; approve Annual Plan               |
| Valid HoD Delegate                 | Exact delegated capability, PE, FY, department and effective period | Perform only the recorded HoD command                                                                            | Generic fallback or authority outside delegation                                          |
| Procurement DPP Validator          | PE + FY + explicit DPP validation capability                        | Classify requirement type, raise structured issues, return, accept, or reopen before consumption                 | Change Need-owned facts; validate own submission; approve Annual Plan                     |
| Procurement Planner / Consolidator | PE + FY                                                             | Begin consolidation; form items; allocate sources; complete professional item treatment; prepare Draft successor | Approve/certify own Plan; mutate upstream or downstream records                           |
| Head of Procurement Function       | PE + FY + professional-validation capability                        | Professionally validate and submit the complete Plan Version for AO certification; return to planner             | Act as automatic final approver; edit submitted snapshot                                  |
| Budget Officer                     | PE + FY + funding scope + Finance capability                        | Confirm full funding or return the Plan Item                                                                     | Approve Plan; edit Plan fields or Budget Line inline; partial confirmation                |
| Accounting Officer                 | PE + effective AO capability                                        | Review exact professionally validated version; certify and submit onward; return for correction                  | Replace configured final approval unless route expressly says so; edit submitted snapshot |
| Statutory Approving Authority      | PE + FY + configured approval capability                            | Approve or return the exact AO-certified version                                                                 | Edit certified content; publish as part of approval                                       |
| Publication Operator               | PE + FY + publication capability                                    | Transmit the exact approved payload; retry failed transmission; view acknowledgement evidence                    | Change approved payload; self-declare success; advertise a Tender                         |
| Monitoring Officer                 | PE + FY + monitoring capability                                     | Record actual milestone/progress evidence                                                                        | Rewrite planned baseline or downstream records                                            |
| Auditor / Oversight                | Lawful oversight scope                                              | Read immutable evidence                                                                                          | Any Planning command                                                                      |
| System Administrator               | Audited support scope                                               | Labelled read-only projection and technical diagnostics                                                          | Any business decision, impersonation or authority substitution                            |

## **5.2 Normative authorization predicate**

The server shall allow a command only when all of the following are true at execution time:

1. an effective assignment grants the exact capability;
2. assignment PE and FY match the record;
3. department scope matches when the command is departmental;
4. any delegation is valid for capability, scope and timestamp;
5. record state permits the command;
6. maker-checker and route-specific segregation rules pass;
7. the expected record version, task iteration and source-set hash are current; and
8. no lower-level invariant or downstream constraint blocks the effect.

Counts, queues, workspace rows, detail access, export where later admitted, notifications and direct command endpoints shall apply the same predicate. Selecting a context, knowing an identifier, holding a broad role name or being System Administrator grants no authority.

## **5.3 Segregation rules**

- A HoD/delegate who submits a DPP may not validate or accept the same submission.
- A Procurement Planner who materially prepared a Plan Version may not professionally validate it.
- The professional validator may not AO-certify or finally approve the same version unless an expressly approved route documents why separation is impossible and how compensating control operates; no such exception is admitted in the canonical MVP-1 seed.
- The AO certifier may not perform the configured final approval unless the approved PE-type route makes the AO that authority.
- A Budget Officer confirms only funding evidence and gains no Planning approval authority from that decision.
- Administrative or database privilege cannot create a valid business decision or immutable evidence record.
- Unauthorized task forms and action controls are omitted, not rendered disabled. Direct access is denied before protected task data is serialized.

# **6\. Authoritative inputs and ownership contract**

## **6.1 Configuration and governance inputs**

| **Input**                           | **Authoritative owner**    | **Required Planning use**                                                                                                                 |
| ----------------------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| PEFiscalYearContext                 | Configuration & Governance | Declares one allowed PE/FY combination; Planning never generates a Cartesian set.                                                         |
| Procuring Entity and PE type        | Configuration & Governance | Identity, hierarchy, approval route and display snapshots.                                                                                |
| Financial Year                      | Configuration & Governance | Start/end dates and Africa/Nairobi timezone; no Planning extension fields.                                                                |
| Organisation Unit                   | Configuration & Governance | Department ownership and scope.                                                                                                           |
| Departmental Plan Submission Window | Configuration & Governance | Distinct from the Needs intake window; derived Scheduled/Open/Closed behaviour; no manual status.                                         |
| Effective Assignment and Delegation | IAM / Access Governance    | Live authority at read and command time; immutable assignment snapshot at decisions.                                                      |
| Method Catalogue                    | Configuration & Governance | Server allow-list and method basis; Open Tender must be configured for MVP-1.                                                             |
| Reservation Rules                   | Configuration & Governance | Applicable plan-level calculation and validation; no manual pass flag.                                                                    |
| Approval Route                      | Configuration & Governance | Ordered professional, AO and final-authority capabilities for the PE type.                                                                |
| Publication Destination             | Integration Configuration  | Current destination, authentication reference, payload profile and acknowledgement semantics; held from production until ASMP-003 closes. |

## **6.2 Departmental Needs input contract**

Planning accepts a Need only through a trusted versioned event or equivalent authoritative pull contract. The minimum source contract is:

| **Field**                                       | **Required rule**                                           | **Planning treatment**                                          |
| ----------------------------------------------- | ----------------------------------------------------------- | --------------------------------------------------------------- |
| Need identifier                                 | Stable four-digit NDS format, for example NDS-MOH-2027-0001 | Reference and immutable snapshot; no DMD alias.                 |
| Need version identifier and source hash         | Exact current accepted version                              | Used for idempotency, staleness and evidence.                   |
| State                                           | Exactly **Accepted for planning** at evaluation time        | Any other state is ineligible.                                  |
| PE, FY and department                           | Exact declared context and department                       | Cross-context source is excluded without disclosure.            |
| Requirement title and planning description      | Current accepted source value                               | Read-only in Planning.                                          |
| Unit and accepted quantity                      | Present, governed and positive                              | Full quantity projected in P3; no Planning override.            |
| Required-by date                                | Within the governed single financial year for MVP-1         | Outside-FY case fails closed.                                   |
| Strategy/programme/project reference            | Current where required by upstream policy                   | Read-only lineage and snapshot.                                 |
| Budget line, funding source and governed amount | Current same-PE/FY reference when required                  | Read-only context in P3; reconciled by Finance later.           |
| Source owner and approval evidence              | Department and HoD-owned upstream history                   | Visible as evidence; not repeated as another Planning approval. |

The intake projection is idempotent and transactionally creates or reuses one DPP root for the cycle/department and one current entry for the Need. Replayed or concurrent source events cannot duplicate either record. Reads never perform projection.

## **6.3 Source-change contract**

| **Current Planning condition**                                         | **Required response to a new accepted Need version**                                                                                                   |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| DPP Draft or Returned, not previously consumed                         | Refresh the current projection, show the changed-source summary and require a new HoD certification.                                                   |
| DPP Submitted                                                          | Keep the submitted snapshot immutable, flag the source stale, block acceptance and require an authorised return.                                       |
| DPP Accepted, not consumed by consolidation                            | Preserve accepted evidence, set current eligibility false and permit validator-controlled reopen to Returned.                                          |
| Accepted submission consumed by an Annual Plan Draft or active version | Never reopen or rewrite that submission. Create a new DPP amendment projection under the same DPP root, with predecessor submission and change reason. |
| Withdrawn DPP                                                          | Preserve history; do not reactivate through event replay. A separately authorised new cycle or amendment path is required.                             |

The amendment projection uses the same coverage, HoD certification, structured validation and acceptance controls as the initial DPP. Its accepted submission is eligible only for an Annual Plan Draft successor. The prior active Plan and prior DPP evidence remain unchanged.

## **6.4 Budget and funding input contract**

Planning reads Budget & Funding values from the authoritative service at the decision timestamp. For every Plan Source Allocation it requires budget line identity, funding source, approved ceiling, reserved amount, committed amount, live available amount, currency, allocation version and **As at** timestamp. The client may not submit these values as authority.

A Finance decision is current only while its source allocation, planned value, funding lineage, budget-line version and governed freshness rule remain unchanged. A material change makes the decision **Stale** and requires a new linked Finance task; historical evidence remains immutable.

# **7\. Canonical domain model**

## **7.1 Context and departmental-plan records**

| **Record**                        | **Purpose and minimum attributes**                                                                                                       | **Non-negotiable invariants**                                                                    |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Planning Cycle                    | cycle_id; context_id; created actor/time; audit metadata                                                                                 | Exactly one per declared PE/FY context; derived availability; may exist without Annual Plan.     |
| Departmental Procurement Plan     | dpp_id; reference; cycle; context; department; current projection; current accepted submission; optimistic version                       | Unique cycle + department; stable root; no hard delete after first submission.                   |
| Departmental Plan Entry           | entry_id; DPP; source Need/version/hash; projection status; professional requirement type                                                | Unique DPP + source Need; source-owned facts read-only; exactly one current projection.          |
| Departmental Plan Submission      | submission_id; number; purpose initial/amendment; predecessor; payload/source-set hashes; HoD/recipient/window snapshots; submitted time | Immutable; monotonic number; exact actor, authority, recipient and source set.                   |
| Departmental Submission Entry     | Submission; source Need/version; description/unit/quantity/required-by/strategy/budget/funding snapshots; source hash                    | Exactly one per included current Need; values equal authoritative accepted version used.         |
| Departmental Plan Validation      | Submission; validator/assignment; start/end; outcome; validation hash                                                                    | At most one terminal outcome per submission; terminal outcome immutable.                         |
| Departmental Entry Classification | Validation; submission entry; Goods/Works/Non-consulting services/Consulting services; actor/time                                        | Governed four-value classification; no free text.                                                |
| DPP Validation Issue              | Submission; optional entry; code; owner module/record; explanation; required action; actor/time; resolution source version               | Actionable structure required; no generic reason alone and no self-declared upstream resolution. |
| DPP Decision                      | DPP/submission; command; from/to; actor/assignment/delegation; reason; timestamp; idempotency key                                        | Append-only; authority effective at decision time; reason mandatory where specified.             |
| Accepted DPP Projection           | Current accepted submission, source-set hash, eligibility and blocker codes                                                              | Computed output, not a mutable master; consumption identifies exact submission/hash.             |

## **7.2 Annual-plan records**

| **Record**                         | **Purpose and minimum attributes**                                                                                                   | **Non-negotiable invariants**                                                                                                 |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| Annual Procurement Plan            | plan_id; cycle; reference; current active version                                                                                    | Exactly one root per Planning Cycle; read never creates it; stable identity across amendments.                                |
| Plan Version                       | version_id; plan; number; predecessor; purpose; state; source-set hash; submitted/decision snapshots; totals; optimistic version     | Monotonic number; at most one active and one open Draft successor; immutable after submission except through named decisions. |
| Plan Item                          | Stable item identity and immutable content as carried by one Plan Version; reference; title; owner scope; treatment; schedule; value | Belongs to one version snapshot; no blank item; source allocations reconcile exactly.                                         |
| Plan Source Allocation             | Plan Item; DPP submission entry; Need/version; quantity; value; budget/funding lineage; allocation state                             | Total allocated quantity/value cannot exceed source; duplicate or conflicting consumption blocked transactionally.            |
| Draft Source Hold                  | Open Draft/Plan Item/allocation identity and source quantity/value held against concurrent formation                                 | Draft only; released on removal/cancellation; does not alter source approval.                                                 |
| Finance Task Iteration             | Plan Version/Item; source funding allocations; assigned capability; prior iteration; state; concurrency token                        | At most one actionable iteration per item; protected data; linked history.                                                    |
| Finance Decision                   | Task; item; every funding allocation/version; amount; actor/assignment; outcome; note/reason; timestamp                              | Full-value, all-source, immutable and idempotent; no partial success.                                                         |
| Funding Reservation Reference      | Authoritative Budget reservation identity linked to source allocation and Finance decision                                           | Created/released through Budget service; never duplicated or locally forged.                                                  |
| Professional Review Task           | Exact submitted Plan Version; assigned capability; iteration; state; prior return                                                    | One actionable current iteration; immutable submitted snapshot.                                                               |
| Planning Decision                  | Named decision type; version/item; actor/authority; from/to; reason/note; timestamp; input hash; idempotency key                     | No generic mutable approval flag; returns preserve prior evidence.                                                            |
| Plan Publication                   | Approved version; payload hash; destination/config version; request; acknowledgement/failure; attempt/time                           | Exact approved payload; success only with authoritative acknowledgement; immutable evidence.                                  |
| Requisition Eligibility Projection | Active Plan Item; source/allocation lineage; remaining quantity/value; blockers; As at                                               | Read-only computed output; no Requisition or Tender created by Planning.                                                      |
| Requisition Drawdown Reference     | Authoritative Requisition identity and amount/quantity consumed from eligibility                                                     | Prevents overdraw; owned by Requisitions and projected into Planning.                                                         |
| Plan Monitoring Entry              | Version/item; milestone; planned baseline ref; actual date/status; evidence; actor/time; correction link                             | Append-only; actuals never overwrite approved planned values.                                                                 |
| Workspace Projection               | Authorised context; cycle/plan summary; action queue; waiting queue; exact commands                                                  | Computed per request; not stored counters or task duplicates.                                                                 |

## **7.3 Global invariants**

- Reads, context changes, counts, list queries and detail opens create no business record.
- Submitted, returned, professionally validated, certified, approved, active, superseded and cancelled snapshots are never edited in place.
- Each accepted Need is projected once per DPP and fully represented before HoD submission.
- Each consumed departmental submission entry retains exact lineage through every Plan Source Allocation and Requisition drawdown.
- No allocation total may exceed its authoritative source quantity or value; no Draft hold or effective allocation may conflict with another open/current use.
- The one active Annual Plan Version remains operational while a Draft successor is prepared, returned, certified, approved or awaiting publication.
- Approval alone does not activate a version. Publication acknowledgement activates it and atomically supersedes the predecessor.
- Monitoring and downstream projections cannot rewrite the approved Plan baseline.
- No Planning command creates a Requisition, Tender, bid window, tender notice or supplier-facing record.

# **8\. Canonical field registers**

## **8.1 Departmental Plan header and entries**

| **Value**                                       | **Owner / presentation**                    | **Required rule**                                                                         |
| ----------------------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------------------------- |
| DPP reference                                   | Planning, read-only                         | System-generated and immutable.                                                           |
| Procuring Entity, department and financial year | Configuration, read-only                    | Derived from exact context and scope; snapshotted at submission.                          |
| Submission window                               | Configuration, read-only                    | Identifier/open/close/evaluated instant captured at submission.                           |
| HoD/delegate                                    | IAM, resolved at command                    | Actor, assignment/delegation and effective dates captured.                                |
| Accounting Officer recipient                    | Approval configuration, resolved at command | Exact assignment reference and display snapshot; no generic mailbox.                      |
| Need reference/title/description                | Departmental Needs, read-only               | Current accepted version; no Planning edit.                                               |
| Unit, quantity and required-by                  | Departmental Needs, read-only               | Full quantity; required-by within FY; no partial inclusion.                               |
| Strategy/programme/project                      | Strategy through Need, read-only            | Shown only when present/required; no placeholder.                                         |
| Budget line, funding source and governed amount | Budget/Need, read-only                      | Same PE/FY; P3 does not confirm funding.                                                  |
| Requirement type                                | Procurement validator, governed select      | Goods, Works, Non-consulting services or Consulting services; required before acceptance. |
| Source and issue state                          | Derived, read-only                          | Exact current/stale/blocker copy; no percentage or manual checklist.                      |

## **8.2 Annual Plan header**

| **Value**                          | **Source / entry rule**                                       | **Evidence rule**                                                             |
| ---------------------------------- | ------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Ministry/parent institution        | Derived from PE hierarchy                                     | Snapshot on submitted version.                                                |
| Procuring Entity                   | Derived from selected authorised PE                           | Reference plus immutable display snapshot.                                    |
| Project name                       | Derived from governed project reference only where applicable | Nullable reference/snapshot; no compulsory free text.                         |
| Financial year                     | Derived from context                                          | FY reference, label, dates and timezone snapshot.                             |
| Plan reference and version         | Planning-generated                                            | Stable root plus monotonic version.                                           |
| Plan purpose and change reason     | Planning; required for successor                              | Initial plan, addition, removal or source amendment; concise business reason. |
| Current decision owner and state   | Derived                                                       | Exact capability/state, never generic **In review**.                          |
| Total planned value and item count | Derived                                                       | Reconcile to included Plan Items and allocations.                             |

## **8.3 Plan Item and Annual Plan output**

| **Field**                               | **Presentation and owner**                          | **Operational rule**                                                                                        |
| --------------------------------------- | --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Item number                             | System-generated in submitted version               | Deterministic sequence; not business identity.                                                              |
| Source breakdown                        | Read-only DPP submission entries and allocations    | Show every department, Need, quantity, value, budget and source version.                                    |
| Procurement-facing description          | Required multiline; Procurement Planner             | Comprehensive planning description; not technical tender specification and may not contradict source scope. |
| Requirement type/category               | DPP classification plus governed catalogue          | Drives validation and output; no free text.                                                                 |
| Unit and quantity                       | Derived from allocations                            | Reconcile exactly; combined sources must use a compatible unit/treatment.                                   |
| Planned value                           | Read-only allocation total in KES at full precision | Must reconcile to governed source amounts and include applicable incidental procurement costs.              |
| Recommended method and basis            | Read-only governed result                           | Explain configured basis; no opaque automated decision.                                                     |
| Planned procurement method              | Required governed select                            | MVP-1 admits Open Tender only; unsupported payload rejected.                                                |
| Contract period                         | Required governed value                             | MVP-1 value is **Single year** only.                                                                        |
| Indicative lotting                      | Required governed value                             | MVP-1 value is **No lots expected** only.                                                                   |
| Aggregation decision                    | Required when more than one source is combined      | Concise professional reason and compatibility evidence; no source loss.                                     |
| Source of funds                         | Derived from each funding allocation                | Show all sources; no inline substitution.                                                                   |
| Invitation/advertisement date           | Planner-entered planned milestone                   | Required, ordered and within the supported plan period.                                                     |
| Bid opening date                        | Planner-entered planned milestone                   | Required and after invitation.                                                                              |
| Evaluation completion date              | Planner-entered planned milestone                   | Required and after bid opening.                                                                             |
| Tender award approval date              | Planner-entered planned milestone                   | Planned date only; not an award decision.                                                                   |
| Notification of award date              | Planner-entered planned milestone                   | Required and after award approval.                                                                          |
| Contract signing date                   | Planner-entered planned milestone                   | Required and after notification.                                                                            |
| Delivery/implementation/completion date | Planner-entered planned milestone                   | Required; at or before source required-by date for single-year case.                                        |
| Planned days to contract signature      | Derived                                             | Contract-signing date minus invitation date; never manually duplicated.                                     |
| Finance state                           | Derived from current Finance decision               | Not requested, Awaiting confirmation, Returned by Finance, Confirmed or Stale.                              |
| Actual dates and variance               | Monitoring, read-only on baseline                   | Append-only actual evidence; no baseline rewrite.                                                           |

## **8.4 Mutation allow-list**

The Plan Item edit command accepts only procurement-facing description, permitted governed category where not fixed by DPP classification, planned method identifier, contract period, lotting decision, permitted aggregation reason and the seven planned milestone dates. Any client attempt to write PE, FY, department, Need/version, source description, unit, quantity, required-by, Strategy, Budget line, funding source, allocation value, state, completeness, decision, reservation or version ownership returns a stable validation error. Unknown fields are rejected, not silently ignored.

# **9\. State models**

## **9.1 Derived Planning Cycle states**

| **Derived state**                    | **Condition**                                         | **Business effect**                                                 |
| ------------------------------------ | ----------------------------------------------------- | ------------------------------------------------------------------- |
| No authorised context                | Actor has no effective Planning visibility assignment | Show PLN-UI-00; disclose no selector, counts or Plan existence.     |
| Scheduled                            | Valid context but DPP submission window not open      | Read-only timing; no submission action.                             |
| Open for departmental planning       | Window open and initial DPP work permitted            | Capability-specific DPP tasks appear.                               |
| Consolidation / approval in progress | Accepted DPP source or Annual Plan workflow exists    | Exact current decision owner appears.                               |
| Active plan                          | One approved, acknowledged version is active          | Operational baseline and Requisition eligibility available.         |
| Active plan with Draft successor     | Active version coexists with one open successor       | Active baseline remains operational; Draft actions remain separate. |
| Closed / historical                  | No current action and cycle outside active operations | Authorised read-only evidence only.                                 |

No user-maintained cycle status or open-cycle approval exists.

## **9.2 Departmental Procurement Plan states and transitions**

| **From**                     | **Command**                      | **To**                     | **Actor**                           | **Mandatory guards and effects**                                                                                             |
| ---------------------------- | -------------------------------- | -------------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Draft                        | Submit departmental plan         | Submitted                  | HoD or valid delegate               | Window open; exact scope; complete current source coverage; no blocker; immutable submission/recipient/attestation snapshot. |
| Returned                     | Resubmit departmental plan       | Submitted                  | HoD or valid delegate               | Corrected accepted sources projected; new immutable submission number and predecessor.                                       |
| Submitted                    | Return to department             | Returned                   | Assigned DPP validator              | At least one structured issue; immutable decision; submitted payload unchanged.                                              |
| Submitted                    | Accept for consolidation         | Accepted for consolidation | Assigned DPP validator              | Current sources; all entries classified; no blocker; submitter segregation; terminal validation and P4 projection.           |
| Draft / Returned             | Withdraw departmental plan       | Withdrawn                  | HoD or valid delegate               | Reason; no accepted downstream consumption.                                                                                  |
| Accepted for consolidation   | Reopen for source correction     | Returned                   | Assigned DPP validator              | Source changed; no consolidation consumption; reason and changed source; accepted evidence preserved.                        |
| Consumed accepted submission | Prepare departmental plan update | Amendment Draft projection | System projection plus HoD workflow | New accepted Need version/change; predecessor retained; active Annual Plan unchanged.                                        |

The exact HoD attestation is:

**I certify that this Departmental Procurement Plan contains the current accepted procurement needs of {department} for {financial_year}, and that the descriptions, units, quantities and required-by dates shown are the authoritative departmental records submitted for consolidation. I understand that source corrections must be made in the owning module and resubmitted.**

A failed deterministic validation creates blocker evidence only. It does not automatically return, accept, withdraw or reopen a DPP.

## **9.3 Annual Plan Version states**

| **State**                         | **Meaning**                                                             | **Editable content**                                                                  | **Next decision owner**                      |
| --------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | -------------------------------------------- |
| Draft                             | Initial or successor version is being prepared                          | Planner-owned fields only; source facts read-only                                     | Procurement Planner                          |
| Awaiting Finance reconciliation   | One or more complete items have current Finance tasks                   | None for awaiting items; other Draft work may continue where safe                     | Budget Officer                               |
| Returned by Finance               | Finance returned at least one item                                      | Planner-owned fields on affected item                                                 | Procurement Planner                          |
| Ready for professional validation | All items complete, current Finance evidence present and no blocker     | None after submission command                                                         | Head of Procurement Function                 |
| Awaiting AO certification         | Professional validation passed and exact version submitted to AO        | None                                                                                  | Accounting Officer                           |
| Awaiting statutory approval       | AO certified and submitted the exact immutable version                  | None                                                                                  | Configured statutory approving authority     |
| Returned                          | Named authority returned an immutable submitted/certified version       | No edit to returned snapshot; corrected successor or governed reopened Draft required | Procurement Planner / prior workflow owner   |
| Approved - publication pending    | Configured authority approved exact version                             | None                                                                                  | Publication Operator                         |
| Publication failed                | Latest transmission attempt failed; approval remains valid              | None; exact payload cannot change                                                     | Publication Operator retry                   |
| Active                            | Exact approved payload acknowledged and version is operational baseline | None                                                                                  | Monitoring / Requisitions / amendment actors |
| Superseded                        | A successor activated                                                   | None                                                                                  | Historical readers only                      |
| Cancelled                         | Draft/returned version cancelled with reason                            | None                                                                                  | Historical readers only                      |

Finance confirmation, professional validation, AO certification, statutory approval and publication acknowledgement are immutable decisions or evidence, not editable status fields. UI projections may use exact derived waiting labels but shall not persist a generic **In review** value.

## **9.4 Annual Plan transition contract**

| **From**                                            | **Command**                        | **To**                                          | **Required actor**                          | **Core guards and atomic effects**                                                                                       |
| --------------------------------------------------- | ---------------------------------- | ----------------------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| No Annual Plan root                                 | Begin consolidation                | Draft Version 1                                 | Procurement Planner                         | Valid context; eligible accepted DPP source; transaction, unique constraints and idempotency; create/reuse root/version. |
| Active with no successor                            | Begin plan update                  | Draft successor                                 | Procurement Planner                         | Eligible accepted DPP amendment/addition or eligible removal; one successor; predecessor remains Active.                 |
| Draft                                               | Save Plan Item draft               | Draft                                           | Procurement Planner                         | Mutation allow-list; optimistic version; recalculated completeness; no Finance task.                                     |
| Draft / Returned by Finance                         | Request Finance confirmation       | Awaiting Finance reconciliation                 | Procurement Planner                         | Item complete; current sources; save-and-submit atomic; one current task iteration.                                      |
| Awaiting Finance reconciliation                     | Confirm funding                    | Finance-confirmed derived gate                  | Budget Officer                              | Full all-source live availability; reservations/decision/task complete atomically; Plan Version remains Draft.           |
| Awaiting Finance reconciliation                     | Return to planner                  | Returned by Finance                             | Budget Officer                              | Required reason; no reservation; linked evidence; reopen planner fields.                                                 |
| Draft with all gates ready                          | Submit for professional validation | Protected submitted snapshot                    | Procurement Planner                         | Effective change; complete items; current Finance; no blocker; immutable snapshot and one task.                          |
| Submitted for professional validation               | Validate and submit to AO          | Awaiting AO certification                       | Head of Procurement Function                | Revalidate all content/controls; immutable professional decision; no final approval meaning.                             |
| Submitted for professional validation               | Return to planner                  | Returned                                        | Head of Procurement Function                | Required structured reason; active predecessor remains; task iteration complete.                                         |
| Awaiting AO certification                           | Certify and submit                 | Awaiting statutory approval                     | Accounting Officer                          | Revalidate professional decision, funding, sources, form/output and authority; immutable certification.                  |
| Awaiting AO certification                           | Return for correction              | Returned                                        | Accounting Officer                          | Required actionable reason; exact submitted snapshot preserved.                                                          |
| Awaiting statutory approval                         | Approve Annual Procurement Plan    | Approved - publication pending                  | Configured authority                        | Exact route/assignment; maker-checker; immutable approval; no activation or publication side effect.                     |
| Awaiting statutory approval                         | Return for correction              | Returned                                        | Configured authority                        | Required actionable reason; no edit or silent correction.                                                                |
| Approved - publication pending / Publication failed | Publish Annual Procurement Plan    | Active on acknowledgement or Publication failed | Publication Operator                        | Exact approved payload/hash; configured destination; attempt evidence; acknowledge before activation.                    |
| Active predecessor + acknowledged successor         | Activate successor                 | Successor Active; predecessor Superseded        | System in publication transaction           | One active version; effective additions/removals/allocations apply once; predecessor evidence retained.                  |
| Draft / Returned                                    | Cancel plan update                 | Cancelled                                       | Procurement Planner with command capability | Reason; no effect on Active version; reverse Draft holds/eligible reservations through governed services.                |

## **9.5 Publication integrity**

The publication service shall serialize the approved Annual Plan output deterministically, hash it, and persist the payload profile and destination configuration version. The approval input hash and publication payload hash shall reconcile. The adapter may return acknowledged, failed or indeterminate. Only an authoritative acknowledged response activates the version. Failed or indeterminate attempts retain the exact payload and permit idempotent retry; they may not create a second approval or change Plan content.

Publication of the Annual Procurement Plan is a transparency action only. It does not advertise a Tender, open bidding, create a supplier route, or authorize Tender Preparation.

# **10\. Functional requirements by lifecycle stage**

## **10.1 Context, workspace and cycle controls**

| **ID**     | **Canonical requirement**                                                                                                                                                                                                                               |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CAN-FR-001 | The server shall return only active declared PE/FY contexts covered by the actor's effective Planning visibility assignment. Zero contexts shall disclose no PE/FY or Plan information; one shall auto-select; many shall require deliberate selection. |
| CAN-FR-002 | A remembered context is a client convenience only and shall be revalidated on every request. It shall not create authority or fall back to a broad default.                                                                                             |
| CAN-FR-003 | The workspace shall use one common authorization predicate for summary, counts, action queue, waiting queue, links and commands. Counts shall reconcile to visible rows.                                                                                |
| CAN-FR-004 | The Planning Cycle shall be unique per declared context and may be idempotently materialised only after configuration prerequisites pass. Workspace reads shall not create it.                                                                          |
| CAN-FR-005 | The Annual Plan root shall be unique per cycle and shall be created only by Begin consolidation with at least one eligible accepted DPP submission.                                                                                                     |
| CAN-FR-006 | Missing configuration shall produce a safe business unavailable state and a support reference; only authorised support may receive diagnostic detail.                                                                                                   |
| CAN-FR-007 | The context help text shall state: **These controls define the workspace view; they do not change record ownership or grant operational authority.**                                                                                                    |
| CAN-FR-008 | The workspace description shall state: **Turn accepted departmental plans into funded, approved Plan Items ready for requisitioning.**                                                                                                                  |

## **10.2 Departmental Need projection and DPP submission**

| **ID**     | **Canonical requirement**                                                                                                                                                                       |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CAN-FR-010 | A trusted acceptance event shall project one current accepted Need into one DPP entry for the matching cycle/department, idempotently and without creating an Annual Plan.                      |
| CAN-FR-011 | Every current eligible accepted Need shall appear exactly once and at full quantity before DPP submission. Omission, duplication, partial quantity and local inflation shall block submission.  |
| CAN-FR-012 | Departmental users and Procurement validators shall not edit Need-owned description, unit, quantity, required-by, Strategy, Budget or funding facts in Planning.                                |
| CAN-FR-013 | DPP readiness shall be an exact blocker set, not a score or percentage. It shall include source currency, context, coverage, required data, budget reference and window checks.                 |
| CAN-FR-014 | Submit/Resubmit shall record the exact payload, source versions/hashes, window, PE/FY/department, HoD authority, AO recipient, attestation hash, predecessor and idempotency key atomically.    |
| CAN-FR-015 | A DPP return shall identify issue code, affected entry where applicable, owning module, owning record, concise defect and exact required action. The submitted snapshot shall remain unchanged. |
| CAN-FR-016 | The assigned validator may set only the governed professional requirement type and may accept only a current, fully classified, issue-free submission they did not submit.                      |
| CAN-FR-017 | Accept for consolidation shall publish a computed eligible source for P4 and shall explicitly state that it does not approve the Annual Procurement Plan.                                       |
| CAN-FR-018 | A post-consumption source change shall create a new amendment submission path under the DPP root; no prior submission or active Annual Plan evidence shall be rewritten.                        |

## **10.3 Consolidation and Plan Item formation**

| **ID**     | **Canonical requirement**                                                                                                                                                                                                                                |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CAN-FR-020 | Begin consolidation shall create/reuse one Annual Plan root and Draft Version atomically from selected eligible accepted DPP submissions/entries.                                                                                                        |
| CAN-FR-021 | The source-selection surface shall list only current, accepted, unconsumed departmental entries for the selected PE/FY and the actor's consolidation scope.                                                                                              |
| CAN-FR-022 | Selecting one entry shall normally form one Proposed Plan Item and one exact Plan Source Allocation without a second formation question.                                                                                                                 |
| CAN-FR-023 | Selecting multiple entries shall require **One Plan Item for each selected requirement** or **One combined Plan Item for all selected requirements** and shall preview exact item/source counts and total value.                                         |
| CAN-FR-024 | Separate formation shall create one Proposed Plan Item per entry. Combined formation shall create one item with every source allocation and require a concise professional aggregation reason.                                                           |
| CAN-FR-025 | Combined formation may cross departments only within the same PE/FY and only when all compatibility controls in section 10.4 pass. Mixed-department ownership shall be PE-level Procurement Function ownership; every source department remains visible. |
| CAN-FR-026 | Formation shall be atomic, idempotent and concurrency-safe. Draft holds shall prevent duplicate selection but shall not change the source DPP or Need acceptance state.                                                                                  |
| CAN-FR-027 | One result shall open the Plan Item editor. Multiple separate results shall return to the Draft workbench with every result visible. Source selection shall not repeat in the editor.                                                                    |
| CAN-FR-028 | The workbench shall derive item count, total, Finance progress, validation blockers and available actions from authoritative items/allocations/decisions.                                                                                                |

## **10.4 Cross-department aggregation decision**

Cross-department aggregation is admitted for MVP-1 as a controlled professional decision, resolving the former HOLD-004. It is available only when:

1. all sources belong to the same PE and FY;
2. every source submission/entry is current, accepted and unconsumed;
3. the governed requirement type is compatible;
4. units, descriptions and delivery obligations can be represented truthfully as one procurement package;
5. required-by dates permit one coherent single-year schedule;
6. funding sources permit atomic all-source Finance confirmation without prohibited cross-fund substitution;
7. the combined total and selected method do not conceal contract splitting or another separation duty;
8. no financing, legal, donor, security, confidentiality or contractual restriction requires separation; and
9. the planner records a concise common-supply, market, delivery or operational rationale.

Failure of any control blocks combined formation without blocking valid separate formation. The system shall not use department identity alone as an incompatibility rule and shall not make an automated procurement decision.

## **10.5 Plan Item completion**

| **ID**     | **Canonical requirement**                                                                                                                                                                                 |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CAN-FR-030 | The editor shall open one existing Proposed Plan Item and show every source allocation read-only. It shall never create a blank item, select sources or regroup allocations.                              |
| CAN-FR-031 | The server shall enforce the mutation allow-list in section 8.4 and derive planned value, recommendation basis, days-to-signature, completeness and source context.                                       |
| CAN-FR-032 | MVP-1 shall accept only an active configured Open Tender method, Single year and No lots expected. Unavailable values shall be absent from UI and rejected before persistence.                            |
| CAN-FR-033 | The seven milestone dates shall be complete, chronological, coherent with the FY and completion/required-by date, and shall satisfy any configured legal-policy constraints.                              |
| CAN-FR-034 | Save draft shall persist only allowed fields and recalculate completeness without creating a Finance task.                                                                                                |
| CAN-FR-035 | Request Finance confirmation shall atomically save allowed fields, revalidate source/allocation and completeness, and create/reuse one protected Finance task. Failure shall roll back the task boundary. |
| CAN-FR-036 | While Finance action is pending, the planner shall see neutral read-only item detail, not the Budget Officer task form or disabled decision controls.                                                     |

## **10.6 Finance reconciliation**

| **ID**     | **Canonical requirement**                                                                                                                                                                                             |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CAN-FR-040 | Only the assigned Finance-capable actor may list, open or decide a protected task; denial shall occur before protected funding data is returned.                                                                      |
| CAN-FR-041 | The task shall show every source allocation, Budget Line, approved/reserved/committed/available amount, required amount, after-confirmation balance and authoritative As-at time read-only.                           |
| CAN-FR-042 | Confirm funding shall lock and reload every affected source/item/task/allocation, require full live availability, create/resolve all reservations and one Finance decision, and complete the task in one transaction. |
| CAN-FR-043 | If any source is short, no Confirm command shall be exposed and direct confirmation shall fail with the current shortfall projection and no partial reservation.                                                      |
| CAN-FR-044 | Open Budget & Funding shall preserve the same Finance task and independently enforce Budget authority. Navigation alone shall create no Planning or Finance mutation.                                                 |
| CAN-FR-045 | Return to planner shall require a reason, create no reservation and reopen only planner-owned fields. A later valid request shall create one linked task iteration.                                                   |
| CAN-FR-046 | A material funding/source/value change shall make prior Finance evidence Stale and require a new current confirmation before submission.                                                                              |
| CAN-FR-047 | Finance confirmation shall not approve a Plan Version, activate an item, amend a Need, edit a Budget Line or create a Requisition/Tender.                                                                             |

## **10.7 Professional validation, AO certification and approval**

| **ID**     | **Canonical requirement**                                                                                                                                                                                                                  |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| CAN-FR-050 | Submit for professional validation shall require at least one effective change, complete items, current full Finance decisions, complete source allocations, supported method/treatment and no blocking/stale issue.                       |
| CAN-FR-051 | Submission shall create an immutable version snapshot and one protected task for the Head of Procurement Function. Non-task viewers may receive neutral read-only detail only.                                                             |
| CAN-FR-052 | Professional validation shall show exact Plan/version, predecessor, change reason, submitter/time, item/source/funding summaries, validation results and decision history. It shall not edit the snapshot.                                 |
| CAN-FR-053 | **Validate and submit to Accounting Officer** shall revalidate the entire version and create one immutable professional decision; it shall not approve, activate or publish the Plan.                                                      |
| CAN-FR-054 | Professional return shall require an actionable reason, preserve active predecessor and current evidence, and reopen only the governed correction path.                                                                                    |
| CAN-FR-055 | The AO screen shall show the exact professionally validated version, accountability statement, budget/funding evidence, output preview and decision history. **Certify and submit** creates immutable certification and onward submission. |
| CAN-FR-056 | AO return shall require an actionable reason and preserve the submitted snapshot; no silent edit or approval shall occur.                                                                                                                  |
| CAN-FR-057 | The statutory approval screen shall identify the configured authority and show the exact AO-certified version. **Approve Annual Procurement Plan** or **Return for correction** are the only decisions.                                    |
| CAN-FR-058 | Approval shall create an immutable decision and state Approved - publication pending. It shall not make the version active or perform publication.                                                                                         |

## **10.8 Publication, activation and downstream eligibility**

| **ID**     | **Canonical requirement**                                                                                                                                                                                                 |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CAN-FR-060 | Publication shall transmit only the exact approved payload through the configured adapter and record destination, configuration version, request, payload hash, attempt, response and timestamps.                         |
| CAN-FR-061 | No version shall become Active without authoritative acknowledgement for the exact approved payload. Failed/indeterminate attempts remain retryable and create no new approval.                                           |
| CAN-FR-062 | Successor activation shall atomically make the successor sole Active, supersede the predecessor and apply approved additions/removals/allocations once.                                                                   |
| CAN-FR-063 | The Approved/Active Plan detail shall be read-only and show version, approval/publication evidence, item baseline, Finance coverage, Requisition eligibility/drawdown and later downstream status as neutral projections. |
| CAN-FR-064 | Planning shall expose only Active, unblocked items with remaining quantity/value to Requisitions. The projection shall include exact Plan/version/item/source lineage and As-at time.                                     |
| CAN-FR-065 | Requisition drawdown shall be recorded from the authoritative Requisitions contract and shall prevent overdraw. Planning shall never create the Requisition or Tender itself.                                             |

## **10.9 Amendments, removals and monitoring**

| **ID**     | **Canonical requirement**                                                                                                                                                                              |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| CAN-FR-070 | An accepted departmental amendment submission, new accepted DPP source or eligible removal may create/reuse one Draft successor. Merely opening a surface shall not create it.                         |
| CAN-FR-071 | A draft-only item may be removed with a reason, retaining history, cancelling open tasks and reversing Draft-stage reservations/holds through governed services.                                       |
| CAN-FR-072 | An Active item may be proposed for whole-item removal only when no Requisition drawdown, Tender handoff, commitment or downstream execution exists. It remains operational until successor activation. |
| CAN-FR-073 | A combined Plan Item may be removed only as a whole in MVP-1. Source-level detachment is unavailable.                                                                                                  |
| CAN-FR-074 | A removal-only successor requires one item-level reason used as the update reason and does not require a new Finance confirmation.                                                                     |
| CAN-FR-075 | Cancellation of a no-effective-change Draft successor shall release Draft holds/effects and leave the active baseline unchanged.                                                                       |
| CAN-FR-076 | Monitoring shall append actual milestones, progress and variance evidence. Corrections append a replacement/correction link and never overwrite the approved planned dates or downstream source.       |

# **11\. Canonical user-interface source contract**

## **11.1 Preservation rule**

The constructed Planning UI is reused by default. Preserve the existing KenTender Procurement shell, navigation, top bar, typography, page-width rhythm, compact tables, filter row, summary strip, task/waiting sections, focused Finance drawer, focused confirmation modal, wide Plan workbench, single-page Plan Item editor, review page with decision rail, and Approved Plan operational-detail composition.

Reuse applies to composition and component geometry, not obsolete semantics. The derivative Stitch Contract shall use approved screenshots and implemented selectors as visual reference and shall record **Keep**, **Correct** or **Retire** for every existing component. Redesign requires a documented incompatibility with this canonical model, not a preference for a different style.

The following corrections are mandatory:

- replace Approved Demand/DMD language and source rows with accepted DPP submission entry/Need lineage;
- replace **Create annual plan** with **Begin consolidation**;
- replace **ready for tendering** with **ready for requisitioning**;
- separate professional validation, AO certification, statutory approval and publication into exact actor/state variants;
- show Approved - publication pending separately from Active;
- replace direct Tender take-up with Requisition eligibility/drawdown as the immediate downstream status;
- remove Multi-year, Lots expected and unsupported method controls from MVP-1;
- render source-owned facts as readable text, not disabled editable inputs; and
- omit unauthorized task controls instead of showing them disabled.

## **11.2 Shared visible contract**

Every screen shall specify one actor, one signed-in fixture, one PE/FY context, one point-in-time state and one authoritative projection. Common anatomy is:

1. existing Procurement navigation and KenTender top bar;
2. breadcrumb and business title, with system reference as quiet secondary text;
3. exact PE/FY context and state owner;
4. restrained status chips only where they communicate workflow truth;
5. compact summary strip where totals or stage matter;
6. task content, source evidence or item table;
7. secondary **View evidence** access when lawful;
8. one obvious primary action, plus only necessary secondary actions; and
9. responsive stacking without hiding source identity, status, amount or action outcome.

No screen may introduce a decorative KPI dashboard, score, generic compliance questionnaire, administrator action panel, manual version control, technical schema field, placeholder text such as **short description**, or conditional phrase whose visible variants are not enumerated.

## **11.3 Workspace registry**

| **Screen ID** | **Exact state and primary actor**                       | **Required visible composition**                                                                                                      | **Actions and outcomes**                                                                                                                   | **Reuse disposition**                                                 |
| ------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------- |
| PLN-UI-00     | Authenticated actor with no authorised Planning context | Title **Procurement Planning**; clear no-access state; support guidance; no selector, PE/FY, counts or Plan existence                 | None                                                                                                                                       | Keep blocked composition; correct copy if needed.                     |
| PLN-UI-01A    | Authorised context, no Annual Plan root                 | Context line/help; cycle timing; DPP preparation/validation queues; eligible accepted DPP source summary; no blank-plan metadata form | **Begin consolidation** only for capable planner with eligible source; opens confirmation or workbench and atomically creates/reuses Draft | Preserve workspace structure; retire Create annual plan semantics.    |
| PLN-UI-01B    | Initial Draft exists                                    | Draft summary, stage, Plan Items/source work, Work requiring action and Waiting on others                                             | **View plan update** and exact current task                                                                                                | Keep with corrected sources/stage labels.                             |
| PLN-UI-01C    | Active version and Draft successor coexist              | Visually distinct Active baseline and Draft update; exact values and change reason                                                    | **View approved plan**; **View plan update**                                                                                               | Keep.                                                                 |
| PLN-UI-01D    | Finance reconciliation currently owns work              | Budget Officer sees one actionable task row; other authorised viewers see waiting owner/status                                        | **Review financial reconciliation** only for assigned Finance actor                                                                        | Keep shell/queue; protected task rules corrected.                     |
| PLN-UI-01E    | Professional validation or AO certification owns work   | Separate exact variant names the current owner and version; no generic In review                                                      | **Review plan version** for Head of Procurement Function or **Review certification** for AO                                                | Preserve shell; split ambiguous prior variant.                        |
| PLN-UI-01F    | Statutory approval or publication owns work             | Separate exact variant names configured approver or publication operator, approval/publication state and waiting context              | **Review for approval** or **Publish Annual Procurement Plan** for exact actor                                                             | Extend existing shell; do not infer combined state.                   |
| PLN-UI-01G    | Active plan and no actionable/waiting work              | Read-only active Plan summary and exact no-work messages                                                                              | **View approved plan**                                                                                                                     | Reuse prior PLN-UI-01F composition under corrected ID/state registry. |
| PLN-UI-SUP-01 | System Administrator support projection                 | Persistent **Support view - read only** label; selected support context; diagnostic reference; no business action                     | **View evidence** where policy permits                                                                                                     | Reuse P3 support composition; no impersonation.                       |

Exact empty copy is **No planning work currently needs your action.** and **Nothing is currently waiting on another reviewer.**

## **11.4 Departmental Plan registry**

| **Screen ID** | **Exact state / actor**                      | **Required visible regions**                                                                                                                                                                                                   | **Exact commands or result**                                                            |
| ------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| P3-UI-DPP-01  | Draft; Departmental Plan Preparer            | Header/context; source coverage and readiness notice; accepted Needs table; selected source detail; source correction links; no editable procurement treatment                                                                 | No terminal command; HoD readiness visible.                                             |
| P3-UI-DPP-02  | Draft ready; HoD                             | Same plan/source composition; exact recipient and window; readiness Ready                                                                                                                                                      | **Submit departmental plan** opens P3-UI-DPP-02A.                                       |
| P3-UI-DPP-02A | Submit confirmation; HoD/delegate            | Plan reference; department/FY; source count/hash summary; AO recipient; exact attestation in section 9.2                                                                                                                       | **Cancel** is mutation-free; **Submit departmental plan** creates immutable submission. |
| P3-UI-DPP-03A | Submitted; validator; classification missing | Immutable submission header/source table; governed Requirement type control only; current blockers; decision area                                                                                                              | Save/classify permitted entry values; Acceptance absent until complete.                 |
| P3-UI-DPP-03B | Submitted; validator; ready                  | Immutable submission, complete classifications, no blockers, source/amount summary, evidence link                                                                                                                              | **Return to department** opens 03C; **Accept for consolidation** opens 03D.             |
| P3-UI-DPP-03C | Return confirmation; validator               | Immutable submission identity; structured issue fields: code, affected source, owner, explanation, required action; warning that snapshot remains unchanged                                                                    | **Cancel**; **Return to department**.                                                   |
| P3-UI-DPP-03D | Acceptance confirmation; validator           | Submission ID; source count; total indicative amount when available; statement **This action accepts the departmental submission as a source for Annual Plan consolidation. It does not approve the Annual Procurement Plan.** | **Cancel**; **Accept for consolidation**.                                               |
| P3-UI-DPP-04  | Submitted; department neutral view           | Immutable submitted source rows; recipient/time; exact **Waiting on Procurement Function** message                                                                                                                             | No validator controls, disabled or otherwise.                                           |
| P3-UI-DPP-05A | Returned; correction outstanding             | Return notice, issue owner/source, required action, prior submission evidence, authoritative upstream link                                                                                                                     | **Open Departmental Need** or other owning record; no local source edit.                |
| P3-UI-DPP-05B | Returned; corrected source projected         | Changed-source comparison, current readiness and prior immutable return evidence                                                                                                                                               | **Resubmit departmental plan** opens the submission confirmation with predecessor.      |
| P3-UI-DPP-06  | Accepted; current and unconsumed             | Read-only accepted submission, classifications, source count/hash, P4 eligibility and decision evidence                                                                                                                        | No Begin consolidation on DPP detail; workspace owns consolidation entry.               |
| P3-UI-DPP-06A | Accepted source changed before consumption   | Accepted evidence plus stale-source notice, changed source and current eligibility false                                                                                                                                       | Assigned validator sees **Reopen for source correction**; others read-only.             |
| P3-UI-DPP-06B | Source changed after consumption             | Accepted evidence, consumed Annual Plan reference and statement that later Plan change control owns impact                                                                                                                     | No P3 reopen action.                                                                    |
| P3-UI-DPP-07  | Withdrawn                                    | Withdrawal reason/actor/time and preserved source/evidence                                                                                                                                                                     | No reactivation.                                                                        |
| P3-UI-DPP-09  | Amendment Draft/Submitted/Accepted family    | Reuse the applicable Draft, submission, validation and accepted compositions; show predecessor submission and **Departmental plan update** purpose prominently                                                                 | Commands use update labels but the same authority, snapshot and validation rules.       |

## **11.5 Consolidation, workbench and item registry**

| **Screen ID** | **Purpose and exact state**                          | **Required visible composition**                                                                                                                                                                           | **Actions / corrections to reused UI**                                                                                                                  |
| ------------- | ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PLN-UI-02     | Begin consolidation confirmation                     | PE/FY and plan title derived read-only; eligible accepted DPP submission/entry count and total; effect statement; no editable PE/FY/title/currency/coordinating unit                                       | **Cancel**; **Begin consolidation**. Reuse compact old registration form only as a confirmation summary.                                                |
| PLN-UI-03     | Initial Draft workbench before Plan Items are formed | Plan header; accepted departmental source availability; zero-item state; issue strip; no user-created empty root message                                                                                   | **Add accepted departmental requirements** opens PLN-UI-04.                                                                                             |
| PLN-UI-04     | Select accepted departmental requirements            | Search; department filter; available-only filter; compact table with selection, requirement/source ref, department, type, quantity/unit, value, required-by, funding and status; selected-source summary   | One selection forms one item. Multiple selections show the exact separate/combined choice and result preview.                                           |
| PLN-UI-05     | Populated initial or successor Draft workbench       | Summary strip; change context for successor; issue strip; filters; compact Plan Items table with change, item, owner, value, Planning, Finance, validation and action; active predecessor remains distinct | Exact item action; add source; eligible removal; submit only when ready; **Cancel update** only when no effective change. Retire standalone PLN-UI-10.  |
| PLN-UI-05A    | Whole-item removal confirmation family               | Item/source/value/Finance/downstream effect read-only; required reason; exact immediate Draft or future successor effect                                                                                   | **Keep item**; **Remove from draft** or **Add removal to plan update**. No source checkboxes or hard delete.                                            |
| PLN-UI-05B    | No-effective-change successor confirmation           | Draft successor identity; active predecessor; exact statement that cancellation leaves active plan unchanged                                                                                               | **Keep update**; **Cancel plan update**.                                                                                                                |
| PLN-UI-06     | Focused Plan Item editor                             | Single page, no tabs/stepper; read-only accepted departmental sources; procurement approach; supported method/period/lotting controls; seven-date schedule; derived days/value                             | **Back to plan update**; **Save draft**; **Request Finance confirmation**. Remove legacy Demand, Multi-year, Lots expected and direct Tender semantics. |

The source-selection table and Plan Item editor shall use business titles as primary text and stable NDS/DPP/Plan identifiers as quiet secondary text. A combined item shall show every source department and funding allocation without a separate editor or per-source procurement treatment.

## **11.6 Finance registry**

| **Screen ID** | **Exact state**                             | **Required visible composition**                                                                                                                                                                                                   | **Commands**                                                                      |
| ------------- | ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| PLN-UI-07     | Sufficient funding; assigned Budget Officer | Focused right drawer over dimmed Finance queue; Plan/item context; all source rows; funding position per Budget Line; totals; As-at; after-confirmation balances; exact notice that funding confirmation does not approve the Plan | **Cancel**; **Return to planner**; **Confirm funding**; optional note on confirm. |
| PLN-UI-07A-1  | Insufficient funding                        | Same drawer geometry; exact affected lines, required/available/shortfall and warning; no Finance note and no Confirm control                                                                                                       | **Close**; **Return to planner**; **Open Budget & Funding**.                      |
| PLN-UI-07A-2  | Return confirmation                         | Compact modal over drawer; item and total shortfall; required **Reason for return**; exact statement that no funding will be reserved                                                                                              | **Cancel**; **Return to planner**.                                                |
| PLN-UI-07B    | Planner neutral view while Finance pending  | Item detail and waiting owner/status; immutable submission/funding-request context                                                                                                                                                 | No Budget Officer form or disabled decisions.                                     |

## **11.7 Validation, certification, approval and publication registry**

| **Screen ID** | **Exact task actor/state**                                     | **Reused composition and required corrections**                                                                                                                                                                                       | **Commands**                                                                                      |
| ------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| PLN-UI-08     | Head of Procurement Function; ready professional validation    | Reuse prior wide review page, summary strip, Plan Item table, validation notice, decision history and right decision rail. Title **Validate procurement plan**; label decision **Professional validation**; no final-approval meaning | **Return to planner**; **Validate and submit to Accounting Officer**.                             |
| PLN-UI-08R    | Professional return confirmation                               | Reuse prior return modal; exact Plan Version/value and required reason; state that current Active predecessor remains                                                                                                                 | **Cancel**; **Return to planner**.                                                                |
| PLN-UI-08A    | Accounting Officer; awaiting certification                     | Reuse read-only review composition; title **Certify annual procurement plan**; show professional validator/time, complete funding, source coverage, output preview and AO accountability statement                                    | **Return for correction**; **Certify and submit**.                                                |
| PLN-UI-08AR   | AO return confirmation                                         | Exact version, value, certification stage and required actionable reason                                                                                                                                                              | **Cancel**; **Return for correction**.                                                            |
| PLN-UI-08B    | Configured statutory authority; awaiting approval              | Reuse review composition; prominently identify authority route and AO certification; title **Approve annual procurement plan**; exact immutable version and no editable content                                                       | **Return for correction**; **Approve Annual Procurement Plan**.                                   |
| PLN-UI-08BR   | Statutory return confirmation                                  | Exact certified version/value; required reason; no editing or publication                                                                                                                                                             | **Cancel**; **Return for correction**.                                                            |
| PLN-UI-08C    | Publication Operator; Approved - publication pending or failed | Focused publication task; approved version/value; destination/config version; payload hash; latest attempt/result; legal-status support note where applicable                                                                         | **Publish Annual Procurement Plan** or **Retry publication**; **View evidence**. No payload edit. |
| PLN-UI-08CA   | Publication acknowledged                                       | Read-only acknowledgement result, exact destination/reference/time/hash and activation result                                                                                                                                         | **View active plan**.                                                                             |

The separate variants above are mandatory. Stitch may reuse one layout family, but it shall generate each actor/state frame independently and may not label any of them generically **Review and approve**.

## **11.8 Active Plan, downstream and monitoring registry**

| **Screen ID** | **Exact state**             | **Required visible composition**                                                                                                                                                                                                                     | **Actions**                                                                                                                                                                   |
| ------------- | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PLN-UI-09     | Current Active Plan Version | Wide read-only operational detail; title/context; approval and publication evidence; summary strip; filters; compact item table; Requisition eligibility/drawdown; later downstream status; version history; Draft-successor notice where one exists | **Add accepted departmental requirement** only with eligible accepted change source; eligible **Propose removal**; **View Plan Item**; no direct Tender or editable baseline. |
| PLN-UI-09A    | Plan Item downstream detail | Read-only active item/source/funding/schedule; remaining quantity/value; Requisition references; later Tender/contract references only after they exist downstream                                                                                   | **View Procurement Requisition** when authorised; no Create Requisition/Tender command.                                                                                       |
| PLN-UI-09M    | Monitoring entry/history    | Approved planned milestone beside downstream actual/variance and evidence; append-only history                                                                                                                                                       | **Record actual milestone** only for Monitoring actor and only where Planning owns the evidence; no baseline edit.                                                            |
| PLN-UI-EVD-01 | Evidence viewer             | Immutable submission, validation, Finance, certification, approval, publication and audit references appropriate to viewer scope                                                                                                                     | Read-only; secure evidence links only.                                                                                                                                        |

## **11.9 Stitch anti-invention contract**

Each independent Stitch prompt shall repeat:

1. prompt and screen ID;
2. purpose and exact primary actor;
3. signed-in fixture and exact PE/FY;
4. origin action and logical route;
5. authoritative reads and point-in-time state;
6. page regions in order;
7. every exact label, value, control type, table column and row;
8. read-only versus editable treatment;
9. buttons, drawers, dialogs and the business outcome represented;
10. role/state visibility and inaccessible-control omission;
11. exact empty, waiting, returned, stale, blocked, success and failure composition where the prompt represents one;
12. responsive stacking and scrolling;
13. explicit exclusions;
14. what remains for implementation; and
15. screenshot/selector acceptance evidence.

The phrases **if applicable**, **where present**, **show as needed**, **appropriate control**, **short description**, **sample rows**, **use realistic data** and equivalent discretion are prohibited unless the same prompt enumerates every resulting visible variant and value. Stitch controls presentation only and shall never be instructed to enforce authority, calculate state, call services or simulate a workflow transition.

# **12\. Integration and service-boundary contracts**

## **12.1 Logical services and commands**

| **Contract**                 | **Minimum input**                                                            | **Required result**                                                      | **Non-bypassable control**                                           |
| ---------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| ResolvePlanningContexts      | Authenticated actor; evaluation time                                         | Zero/one/many authorised declared contexts and visibility mode           | Effective assignments; no client role/PE grant.                      |
| GetPlanningWorkspace         | Authorised context ID                                                        | One coherent summary, action queue, waiting queue and commands           | Same predicate for counts, rows, links and actions.                  |
| ProjectAcceptedNeed          | Trusted event ID; Need/version/hash                                          | Existing or one DPP root/entry projection result                         | Source eligibility, unique constraints, idempotency, no Annual Plan. |
| SubmitDepartmentalPlan       | DPP ID; expected version/source-set; idempotency key                         | Immutable submission and decision                                        | HoD/delegation, window, coverage, current sources, AO recipient.     |
| ReturnDepartmentalPlan       | Submission ID; structured issues; expected version; idempotency key          | Returned decision and immutable issue set                                | Assigned validator; actionable issue contract.                       |
| AcceptDepartmentalPlan       | Submission ID; classifications; expected version/source-set; idempotency key | Terminal validation and Accepted DPP Projection                          | Current sources, all classified, segregation, no blocker.            |
| ReopenDepartmentalPlan       | Accepted submission; changed source; reason; expected version                | Returned state and preserved accepted evidence                           | No P4 consumption.                                                   |
| BeginConsolidation           | Context; selected accepted DPP sources; expected source-set; idempotency key | One Plan root and Draft Version, existing or atomically created          | Exact capability, eligibility, unique constraints and lock.          |
| FormPlanItems                | Plan/Draft; source entry IDs; formation mode; reason if combined; token/key  | Proposed item(s), allocations and Draft holds                            | Server reload, compatibility, atomicity and idempotency.             |
| SavePlanItemDraft            | Item/Draft; allow-listed fields; token/key                                   | Updated Draft and completeness result                                    | Mutation allow-list and source immutability.                         |
| RequestFinanceConfirmation   | Item/Draft; allow-listed fields; token/key                                   | One current Finance task iteration                                       | Item/source completeness, atomic save/task.                          |
| GetFinanceTask               | Task ID                                                                      | Protected current funding projection and available commands              | Assignment/PE/funding scope before serialization.                    |
| ConfirmFunding               | Task ID; token; optional note; key                                           | All reservations, one decision, completed task                           | Locked live funding; full all-source atomicity.                      |
| ReturnFromFinance            | Task ID; token; reason; key                                                  | Return decision; completed iteration; reopened planner fields            | No reservation or Budget mutation.                                   |
| SubmitProfessionalValidation | Plan Version; change reason; token/key                                       | Immutable submitted snapshot and task                                    | Complete effective change and current Finance/source controls.       |
| ProfessionallyValidate       | Review task; token; optional note; key                                       | Professional decision and Awaiting AO certification                      | Task authority, segregation and full revalidation.                   |
| CertifyAndSubmit             | AO task; token; optional certification note; key                             | AO certification and Awaiting statutory approval                         | AO authority and exact immutable version.                            |
| ApproveAnnualPlan            | Approval task; token; optional note; key                                     | Approval and publication-pending state                                   | Configured route/assignment and maker-checker.                       |
| PublishAnnualPlan            | Approved Version; destination config; token/key                              | Attempt plus acknowledgement/failure; activation only on acknowledgement | Exact payload hash and held production integration gate.             |
| ProposeOrApplyRemoval        | Plan/item; reason; token/key                                                 | Immediate Draft exclusion or proposed successor removal                  | Whole-item eligibility and downstream recheck.                       |
| CancelPlanUpdate             | Draft successor; reason; token/key                                           | Cancelled successor and released Draft effects                           | No effect on Active predecessor.                                     |
| GetRequisitionEligibility    | Active Plan Item; As-at                                                      | Remaining quantity/value and lineage or blocker                          | No read mutation; active/current/funding/drawdown checks.            |
| RecordMonitoringEvidence     | Active/superseded item; milestone; evidence; token/key                       | Append-only actual/variance entry                                        | Monitoring capability; baseline immutable.                           |

## **12.2 Event contracts**

| **Event**                            | **Producer**                       | **Planning effect**                                                            |
| ------------------------------------ | ---------------------------------- | ------------------------------------------------------------------------------ |
| DepartmentalNeedAccepted.v1          | Departmental Needs                 | Idempotent DPP projection or amendment impact evaluation.                      |
| DepartmentalNeedSuperseded.v1        | Departmental Needs                 | Stale-source blocker; no silent snapshot rewrite or automatic business return. |
| BudgetAllocationChanged.v1           | Budget & Funding                   | Re-evaluate relevant open Finance tasks and freshness; never auto-confirm.     |
| BudgetReservationChanged.v1          | Budget & Funding                   | Refresh availability/freshness and monitoring projection.                      |
| AnnualPlanPublicationAcknowledged.v1 | Publication adapter                | Verify version/payload/attempt, then activate atomically.                      |
| AnnualPlanPublicationFailed.v1       | Publication adapter                | Persist failure evidence against attempt; remain approved-pending/failed.      |
| ProcurementRequisitionAuthorised.v1  | Procurement Requisitions           | Record read-only drawdown reference and recalculate remaining eligibility.     |
| DownstreamMilestoneChanged.v1        | Requisitions/Tender/Contract owner | Refresh neutral actual/variance projection; do not rewrite baseline.           |

Out-of-order, duplicate and replayed events shall be safe. A reconciliation job may re-run the same idempotent services but may not create a different business outcome or repair immutable evidence silently.

## **12.3 Requisition boundary**

The Requisitions module is the first downstream transactional consumer. It receives active Plan identity/version, Plan Item, source allocations, approved quantity/value, current funding evidence, remaining quantity/value and eligibility blockers. It independently authorizes and creates a Procurement Requisition. Planning receives only the resulting drawdown/reference projection.

There is no Planning service named CreateTender, TakeUpToTender, PublishTender or equivalent. Tender Preparation begins from an authorised Requisition and may later project neutral status back to Planning.

# **13\. Deterministic seed source contract**

The separate Seed Data Contract shall instantiate this section exactly. It may add isolated scenario-owned records only when they use canonical types/values, identify fixture ownership and reset without changing the integrated base.

## **13.1 Authoritative contexts and windows**

| **Identifier**     | **Exact value**                                                                             | **Purpose**                                                      |
| ------------------ | ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| CTX-MOH-2027-2028  | PE-MOH - Ministry of Health; FY-2027-2028; 1 July 2027 through 30 June 2028; Africa/Nairobi | Primary integrated story and national-government approval route. |
| CTX-NSSF-2027-2028 | PE-NSSF - National Social Security Fund; FY-2027-2028                                       | Corporate route and tenant isolation.                            |
| CTX-CGK-2027-2028  | PE-CGK - County Government of Kisumu; FY-2027-2028                                          | County route and tenant isolation.                               |
| PLNW-MOH-2027-01   | Opens 1 October 2026 00:00 EAT; closes 30 November 2026 23:59:59 EAT                        | Primary DPP submission window.                                   |
| PLNW-NSSF-2027-01  | Opens 1 October 2026 00:00 EAT; closes 30 November 2026 23:59:59 EAT                        | Corporate fixture.                                               |
| PLNW-CGK-2027-01   | Opens 15 October 2026 00:00 EAT; closes 15 December 2026 23:59:59 EAT                       | County fixture.                                                  |

Instants are stored in UTC, rendered in Africa/Nairobi, and evaluated with an injected clock. Tests shall not mutate authoritative windows or depend on the machine date.

## **13.2 Primary integrated business records**

| **Identifier**               | **Exact canonical value**                                                                                                                                                                                                                                           |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| NDS-MOH-2027-0001            | **National digital health infrastructure upgrade**; Digital Health Department; Accepted for planning; Non-consulting services; unit **programme**; quantity **1**; required by **31 August 2027**; Government of Kenya funding; governed amount **KES 80,000,000**. |
| DPP-MOH-DIGITAL-2027-001     | Digital Health Departmental Procurement Plan; one current entry from NDS-MOH-2027-0001.                                                                                                                                                                             |
| DPPE-MOH-DIGITAL-2027-001    | Current DPP entry for NDS-MOH-2027-0001.                                                                                                                                                                                                                            |
| DPPS-MOH-DIGITAL-2027-001-V1 | HoD-certified immutable submission created 25 November 2026 at 10:00 EAT.                                                                                                                                                                                           |
| DPPV-MOH-DIGITAL-2027-001-V1 | Procurement validation/classification accepted 27 November 2026 at 14:00 EAT.                                                                                                                                                                                       |
| PLN-MOH-2027-001             | Ministry of Health Annual Procurement Plan 2027/28; stable Plan root created by Begin consolidation on 1 December 2026 at 09:00 EAT.                                                                                                                                |
| PLN-MOH-2027-001-V1          | Initial Plan Version; one item; total KES 80,000,000.                                                                                                                                                                                                               |
| PPI-MOH-2027-021             | **National digital health infrastructure upgrade**; one Plan Source Allocation; Open Tender; Single year; No lots expected; KES 80,000,000.                                                                                                                         |
| PSA-MOH-2027-021-001         | Full quantity 1 and value KES 80,000,000 from DPPS/DPPE/NDS source lineage.                                                                                                                                                                                         |
| RSV-MOH-2027-021-001         | Authoritative Budget reservation created by Finance confirmation for KES 80,000,000.                                                                                                                                                                                |
| PUB-MOH-2027-001-A1          | Sandbox publication attempt for the exact approved V1 payload.                                                                                                                                                                                                      |
| ACK-MOH-2027-001-A1          | Deterministic sandbox acknowledgement dated 10 December 2026 at 15:00 EAT; activates V1 for test purposes only.                                                                                                                                                     |

Planned milestones for PPI-MOH-2027-021 are:

| **Milestone**                        | **Exact date** |
| ------------------------------------ | -------------- |
| Invitation or advertisement          | 1 May 2027     |
| Bid opening                          | 23 May 2027    |
| Evaluation completion                | 23 June 2027   |
| Tender award approval                | 10 July 2027   |
| Notification of award                | 14 July 2027   |
| Contract signing                     | 1 August 2027  |
| Delivery / implementation completion | 31 August 2027 |

## **13.3 Deterministic decisions and personas**

| **Actor**                             | **Capability and scope**                                                       | **Integrated-base action**                                                                                                                        |
| ------------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| <grace.wanjiku@moh.example.test>      | Departmental Plan Preparer; MOH Digital Health; FY 2027/28                     | Reviews projection; no terminal decision.                                                                                                         |
| <peter.kimani@moh.example.test>       | Head of User Department; same scope                                            | Submits DPPS V1 on 25 November 2026 at 10:00 EAT.                                                                                                 |
| <julia.njeri@moh.example.test>        | HoD Delegate; explicit effective period                                        | Delegation positive/expiry negative profiles; no base submission.                                                                                 |
| <mercy.kilonzo@moh.example.test>      | Procurement Planner and DPP validator with distinct admitted test capabilities | Classifies/accepts DPP on 27 November 2026 at 14:00 EAT; begins consolidation and prepares Plan; never validates own Plan Version professionally. |
| <moh.budget.officer@example.test>     | Budget Officer; MOH/FY/funding scope                                           | Confirms KES 80,000,000 on 4 December 2026 at 10:00 EAT.                                                                                          |
| <samuel.otieno@moh.example.test>      | Head of Procurement Function                                                   | Professionally validates/submits V1 to AO on 7 December 2026 at 10:00 EAT.                                                                        |
| <amina.hassan@moh.example.test>       | Accounting Officer                                                             | Certifies/submits V1 on 8 December 2026 at 10:00 EAT.                                                                                             |
| <moh.statutory.approver@example.test> | Configured national-government approving authority                             | Approves V1 on 9 December 2026 at 11:00 EAT.                                                                                                      |
| <moh.plan.publisher@example.test>     | Publication Operator                                                           | Transmits V1 sandbox payload on 10 December 2026 at 14:55 EAT.                                                                                    |
| <peter.ouma@audit.example.test>       | Internal Auditor                                                               | Read-only evidence.                                                                                                                               |
| <kentender.system.admin@example.test> | System Administrator                                                           | Labelled audited support read only.                                                                                                               |
| <lydia.mwangi@kentender.example.test> | Platform Configuration Administrator                                           | Configuration administration; no Planning decision.                                                                                               |

The integrated base shall not assign the same person incompatible preparation, professional validation, AO certification or statutory approval actions. Any persona holding multiple test roles shall receive only explicitly scoped commands and shall not violate the object-specific maker-checker predicate.

## **13.4 Required isolated reset profiles**

| **Profile**                                            | **Exact branch to prove**                                                                                        |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| PLN-SC-CTX-00/01/MANY                                  | Zero, one and many authorised contexts; remembered-context revalidation and tenant isolation.                    |
| PLN-SC-DPP-DRAFT/SUBMITTED/RETURNED/ACCEPTED/WITHDRAWN | Every DPP state and command, including structured return and exact HoD evidence.                                 |
| PLN-SC-DPP-STALE-PRE/POST                              | Source change before and after consolidation consumption.                                                        |
| PLN-SC-PLAN-NONE/DRAFT                                 | No Annual Plan and initial Draft; no read-side creation; Begin consolidation concurrency.                        |
| PLN-SC-COMBINE                                         | Same-PE/FY cross-department separate and combined formation using two NDS sources with exact allocation lineage. |
| PLN-SC-FIN-SUFFICIENT/SHORT/RETURN/STALE               | Full atomic confirmation, shortfall rollback, linked return/re-request and freshness.                            |
| PLN-SC-PROF-READY/RETURN                               | Professional validation and correction branch.                                                                   |
| PLN-SC-AO-READY/RETURN                                 | AO certification and return branch.                                                                              |
| PLN-SC-APPROVER-READY/RETURN                           | Configured authority approval and return branch.                                                                 |
| PLN-SC-PUB-PENDING/FAILED/ACK                          | Publication pending, exact-payload failure/retry and acknowledgement activation.                                 |
| PLN-SC-ACTIVE-SUCCESSOR                                | Active V1 plus Draft successor; addition, amendment, eligible removal and no-change cancellation.                |
| PLN-SC-REQ-ELIGIBLE/DRAWN/BLOCKED                      | Requisition eligibility, partial/full drawdown and direct Tender prohibition.                                    |
| PLN-SC-SECURITY                                        | Cross-PE, expired assignment, support command, direct route and protected task disclosure negatives.             |

One reset database/profile represents one coherent state. Mutually incompatible states of the same record shall not coexist in the integrated base. Every loader is dependency-ordered and idempotent; repeated install/reset creates no duplicate decision, task, reservation, publication, allocation or audit evidence.

# **14\. Implementation, security and evidence invariants**

## **14.1 Schema and transaction controls**

- Unique constraints: PlanningCycle(context), DPP(cycle, department), DPPEntry(DPP, source Need), DPPSubmission(DPP, number), AnnualPlan(cycle), PlanVersion(plan, number), at most one active version, at most one open successor, one terminal DPP validation per submission and one current task iteration per task type/object.
- Foreign keys reference authoritative context, organisation, Need/version, Budget/funding, assignment and downstream identities; no editable shadow masters.
- Submit, return, accept, reopen, Begin consolidation, formation, Finance decision, Plan submission, professional validation, AO certification, statutory approval, publication activation, removal and cancellation execute in serializable or equivalently protected transactions.
- Every state-changing command accepts an idempotency key and expected optimistic version/concurrency token. Source-sensitive commands also accept or derive the expected source-set hash.
- Any failed guard rolls back the complete command. No partial item, allocation, reservation, decision, task, version or publication effect is permitted.
- Immutable decisions and snapshots are append-only. Correction uses a successor, linked task iteration, reversal service or correction record; never an in-place edit.

## **14.2 Authorization and non-disclosure**

- One server policy module evaluates effective capability, PE/FY, optional department/funding scope, delegation, object state, maker-checker history and expected version.
- List, count, workspace, search, detail, evidence, notification, route and command surfaces use the same policy inputs.
- Unauthorized requests return the minimum safe result and shall not reveal whether another PE/FY, Plan, task or identifier exists.
- Protected Finance, professional, AO, approval and publication task data is loaded only after task-specific authorization succeeds.
- Support visibility is visibly labelled, read-only, purpose-audited where required and cannot be converted to a business assignment.
- Client route guards, hidden controls, disabled buttons and supplied role/context values are never treated as authorization.

## **14.3 Audit and observability**

Record actor, effective assignment/delegation, capability, context, object, command, state, expected/current version, source-set hash, timestamp, idempotency key, outcome and support/request correlation reference. Record denied privileged attempts without logging sensitive payloads or cross-tenant facts.

Link the Need event, DPP projection/submission/validation, Plan formation/allocation, Finance reservation/decision, professional validation, AO certification, approval, publication, activation, Requisition drawdown and monitoring evidence through stable identifiers. **View evidence** shall expose lawful immutable evidence without cluttering the primary task surface.

## **14.4 Greenfield and static prohibitions**

The build shall contain no:

- retired Demand/DMD model, three-digit primary NDS identifier or direct Demand-to-Plan route;
- legacy Planning Home, Procurement Home, contribution, release-package or direct Plan-to-Tender dependency;
- migration, import, alias, compatibility route, dual read/write, fallback service or repair seed;
- direct client state writes, mutable approval/accepted/published booleans or generic approval engine that obscures named actors;
- hidden unsupported method, Multi-year or Lots expected payload values;
- wildcard System Administrator business authority;
- automatic Plan creation on read or automatic business decision from an event; or
- implementation agent instruction to consult the Revision Ledger, PLN-GF documents or old Stitch prompts for current behaviour.

# **15\. Canonical issue and error catalogue**

| **Code**                               | **User-facing meaning / required response**                                                                                          |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| PLN_NO_AUTHORISED_CONTEXT              | No Procurement Planning context is available for this account. Return no PE/FY or Plan data.                                         |
| PLN_CONTEXT_SCOPE_DENIED               | The selected Planning context is not authorised. Deny and do not disclose existence.                                                 |
| PLN_CONFIGURATION_INCOMPLETE           | Planning configuration is incomplete. Show stable support reference to authorised users.                                             |
| DPP_WINDOW_NOT_OPEN                    | The Departmental Plan submission window is not open. Block Submit.                                                                   |
| DPP_SOURCE_NOT_ACCEPTED                | The source Need is not currently Accepted for planning. Correct in Departmental Needs.                                               |
| DPP_SOURCE_VERSION_STALE               | A newer accepted Need version exists. Preserve snapshot and use governed correction path.                                            |
| DPP_SOURCE_CONTEXT_MISMATCH            | Source PE/FY/department does not match. Fail closed without cross-tenant disclosure.                                                 |
| DPP_SOURCE_COVERAGE_MISMATCH           | An eligible Need is missing, duplicated or not fully represented. Block submission.                                                  |
| DPP_REQUIRED_BY_OUTSIDE_FY             | Required-by is outside the supported FY. Correct upstream or use future multi-year capability.                                       |
| DPP_BUDGET_REFERENCE_STALE             | Required Budget/funding reference is absent or inactive. Correct owning source.                                                      |
| DPP_REQUIREMENT_TYPE_MISSING           | Validator must classify every entry before acceptance.                                                                               |
| DPP_SEGREGATION_DENIED                 | Incompatible actor attempted submission/validation. Deny and audit.                                                                  |
| DPP_ALREADY_CONSUMED                   | Accepted submission was consumed. Use departmental amendment and Annual Plan successor control.                                      |
| PLN_NO_ELIGIBLE_DPP_SOURCE             | No current accepted departmental submission is available for consolidation. Create no Plan.                                          |
| PLN_SOURCE_ALREADY_ALLOCATED           | Source is held or effectively allocated elsewhere. Refresh source selection.                                                         |
| PLN_COMBINATION_INCOMPATIBLE           | Selected entries cannot form one Plan Item under the canonical compatibility controls. Separate them or correct the blocking source. |
| PLN_STALE_COMMAND                      | Expected record version, task iteration or source-set hash is not current. Refresh; do not replay silently.                          |
| PLN_ITEM_INCOMPLETE                    | Required procurement treatment or schedule is incomplete. Return exact field issues.                                                 |
| PROCUREMENT_METHOD_NOT_CONFIGURED      | **The selected procurement method is not enabled in the current catalogue.**                                                         |
| PLANNING_MULTI_YEAR_NOT_AVAILABLE_MVP1 | **Multi-year Plan Items are not available in this release.**                                                                         |
| PLANNING_LOTS_NOT_AVAILABLE_MVP1       | **Plan Items requiring lots are not available in this release.**                                                                     |
| FINANCE_TASK_ACCESS_DENIED             | Finance task is unavailable to this actor. Return no protected funding data.                                                         |
| FINANCE_INSUFFICIENT_FUNDING           | Full funding is not available. Return exact shortfall; create no partial reservation.                                                |
| FINANCE_CONFIRMATION_STALE             | Funding evidence changed. A new current Finance confirmation is required.                                                            |
| PLAN_VALIDATION_BLOCKED                | Plan Version has current blocking issues. Return affected records and remediation owners.                                            |
| PLAN_SEGREGATION_DENIED                | Actor cannot make this decision because of preparation/decision history.                                                             |
| PLAN_APPROVAL_ROUTE_INVALID            | Configured approving authority or assignment is missing/expired. Deny decision.                                                      |
| PLAN_PUBLICATION_CONFIGURATION_HELD    | Current production publication authority/integration is not approved. Do not transmit.                                               |
| PLAN_PUBLICATION_PAYLOAD_MISMATCH      | Payload differs from approved version. Block publication/activation.                                                                 |
| PLAN_PUBLICATION_NOT_ACKNOWLEDGED      | External acknowledgement is absent or indeterminate. Remain publication pending/failed.                                              |
| PLAN_ITEM_REMOVAL_BLOCKED_DOWNSTREAM   | Requisition drawdown, Tender handoff, commitment or execution prevents removal.                                                      |
| PLAN_REQUISITION_NOT_ELIGIBLE          | Item/version/funding/remaining amount is not eligible for a Requisition.                                                             |
| PLN_SUPPORT_READ_ONLY                  | Support user attempted a business command. Deny and audit.                                                                           |

# **16\. Acceptance, smoke and negative-security contract**

## **16.1 Functional acceptance**

| **ID**     | **Scenario**                                                       | **Expected evidence**                                                                        |
| ---------- | ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| CAN-AC-001 | Actor has zero/one/many authorised contexts.                       | PLN-UI-00 or exact authorised selector behaviour; no authority expansion.                    |
| CAN-AC-002 | Workspace opens with no Plan root.                                 | No business record is created; eligible DPP work is shown accurately.                        |
| CAN-AC-003 | Accepted Need event is replayed/concurrent.                        | One DPP root and one entry; stable idempotent result.                                        |
| CAN-AC-004 | DPP submission omits/duplicates/partially includes a Need.         | Exact coverage blocker; no submission snapshot.                                              |
| CAN-AC-005 | HoD submits within window with current source set.                 | Immutable submission, recipient/authority/attestation/source evidence.                       |
| CAN-AC-006 | Wrong HoD, expired delegate or submitter validates own submission. | Server denial and audit; no protected cross-scope data.                                      |
| CAN-AC-007 | Validator returns with valid issue and source later corrects.      | Immutable return, upstream correction, new submission predecessor and unchanged V1 evidence. |
| CAN-AC-008 | Validator accepts current fully classified submission.             | Terminal validation and P4 eligibility; no Annual Plan approval.                             |
| CAN-AC-009 | Source changes before/after consolidation consumption.             | Pre-consumption reopen only; post-consumption amendment path and no evidence rewrite.        |
| CAN-AC-010 | Two planners Begin consolidation concurrently.                     | One Plan root and Draft Version; stable result.                                              |
| CAN-AC-011 | One/many source entries form separate/combined items.              | Exact item/allocation/hold counts, compatibility enforcement and no source loss.             |
| CAN-AC-012 | Planner mutates source-owned or unknown fields.                    | Stable rejection; no silent ignore or source change.                                         |
| CAN-AC-013 | Save draft versus Request Finance.                                 | Save creates no task; request creates one task only after complete validation.               |
| CAN-AC-014 | Sufficient single/multi-source funding.                            | Full atomic reservation(s), one Finance decision/task completion, no Plan approval.          |
| CAN-AC-015 | Any source funding is short or changes concurrently.               | Exact shortfall; no Confirm control/partial reservation/negative availability.               |
| CAN-AC-016 | Finance returns, planner corrects and re-requests.                 | Required reason; no reservation; one linked task iteration and retained history.             |
| CAN-AC-017 | Complete Plan submitted for professional validation.               | Immutable version and one protected task; neutral detail for non-task viewers.               |
| CAN-AC-018 | Head of Procurement validates or returns.                          | Separate professional decision; no final approval/activation; returned correction evidence.  |
| CAN-AC-019 | AO certifies or returns.                                           | Immutable AO decision and onward route; no silent edit or automatic approval.                |
| CAN-AC-020 | Configured authority approves or returns.                          | Immutable decision; Approved - publication pending; no Active state yet.                     |
| CAN-AC-021 | Publication payload mismatch/failure/acknowledgement.              | Mismatch blocked; failure retryable; exact acknowledgement activates once.                   |
| CAN-AC-022 | Successor activates.                                               | One Active successor, predecessor Superseded, additions/removals/allocations applied once.   |
| CAN-AC-023 | Active item has remaining eligibility.                             | Requisition projection exists; Planning creates no Requisition/Tender.                       |
| CAN-AC-024 | Requisition drawdown consumes part/all.                            | Remaining quantity/value reconciles and overdraw is denied.                                  |
| CAN-AC-025 | Active removal is proposed before/after downstream execution.      | Allowed only before downstream use; later direct command blocked without partial effects.    |
| CAN-AC-026 | Monitoring evidence is recorded/corrected.                         | Append-only actuals and variance; planned baseline unchanged.                                |

## **16.2 Security and isolation acceptance**

| **ID**      | **Negative scenario**                                                                            | **Expected result**                                                              |
| ----------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| CAN-SEC-001 | User supplies another PE/FY context or known Plan/task ID.                                       | Denied before data serialization; no existence signal.                           |
| CAN-SEC-002 | Counts, queues, search, detail and commands are compared for one actor.                          | Identical common-predicate scope and reconciled counts.                          |
| CAN-SEC-003 | Assignment/delegation expires between read and command.                                          | Command denied after server revalidation; current projection returned safely.    |
| CAN-SEC-004 | System Administrator opens support view and calls any business command.                          | Labelled read-only data where authorised; command denied/audited.                |
| CAN-SEC-005 | Planner/HoD/Viewer directly opens Finance, professional, AO, approval or publication task route. | No protected task payload or decision form returned.                             |
| CAN-SEC-006 | Client sends direct state, approval, allocation, funding or source mutation.                     | Payload rejected; no partial state.                                              |
| CAN-SEC-007 | Concurrent confirm/return, approve/return, publication retry or successor creation races.        | One terminal effect; stale loser receives stable outcome; no duplicate evidence. |
| CAN-SEC-008 | MOH, NSSF and CGK isolation suite runs across rows/counts/details/commands.                      | No cross-PE data, action or existence signal.                                    |

## **16.3 Build and evidence gates**

Release evidence shall include:

- requirement, record, state, command, error, screen and test identifier uniqueness/reference resolution;
- entity and field ownership audit with no duplicate master or writable upstream fact;
- complete reachable state/command graphs and explicit terminal/return paths;
- role/capability/PE/FY/department/funding/segregation matrix tests;
- transaction, unique constraint, idempotency, concurrency and stale-version tests;
- Need and Budget event replay/out-of-order reconciliation tests;
- exact fixture identifier/date/amount/hash arithmetic;
- screenshot/selector comparison for every reused or corrected screen;
- accessible headings, table headers, labels, focus containment/return, keyboard actions and status announcements;
- static scan proving absence of retired terms, routes, modules, commands and unsupported values;
- fresh install, migrate, seed, reset and rerun on a clean site; and
- a traceability report with no orphan canonical rule or untested business command.

# **17\. MVP-1 exclusions and governed backlog**

| **Capability**                                       | **MVP-1 treatment**                              | **Admission requirement for later version**                                                    |
| ---------------------------------------------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| Multi-year Plan Item                                 | Unavailable; UI/value absent; submission blocked | Funding-year model, period rules, schedule, approval, UI, seed and tests approved canonically. |
| Lots expected                                        | Unavailable; UI/value absent                     | Lot model, anti-splitting, Tender handoff, UI, seed and tests approved.                        |
| Method other than admitted governed Open Tender      | Unavailable                                      | Current legal/configuration owner, conditions, grounds, exact interaction and tests approved.  |
| Partial Need inclusion or Planning quantity override | Prohibited                                       | Requires upstream product decision; cannot be silently added.                                  |
| Partial Finance confirmation                         | Prohibited                                       | No backlog assumption; requires explicit canonical redesign.                                   |
| Source-level detachment from a combined Plan Item    | Unavailable                                      | Allocation-change model and downstream impact approved.                                        |
| Direct Requisition or Tender creation in Planning    | Prohibited                                       | Module boundary is fixed; no backlog item.                                                     |
| Advanced strategy/performance dashboard              | Excluded                                         | Separate product need and evidence required.                                                   |
| Approved Plan export                                 | Deferred                                         | Output format, scope, redaction, authorization and audit contract approved.                    |
| Historical version interactive detail                | Deferred                                         | Neutral immutable projection and route authorization approved.                                 |
| Production publication integration                   | Held                                             | ASMP-003 and LEG-AUTH-001 closure evidence.                                                    |
| Legacy migration/compatibility                       | Prohibited                                       | Greenfield decision is fixed; no implied backlog.                                              |

# **18\. Canonical change control, supersession and approval**

## **18.1 Change control**

Any gap, conflict or desired behaviour change shall be raised against PLN-CAN-001. The canonical source is versioned before a derivative or code change. A new canonical version shall identify changed requirement IDs, domain/state/command impacts, screen reuse impacts, seed changes, security tests and superseded derivative versions. Derivatives fail closed on fingerprint mismatch.

Implementation agents shall not resolve a gap from historical documents, an existing database shape, constructed UI behaviour or a Stitch frame. Existing code/screens may evidence an intended composition, but product truth comes only from the approved canonical version.

## **18.2 Supersession on approval**

| **Prior document**                                        | **Final authority treatment**                                                                                                    |
| --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| PLN-CDR-001 v0.1                                          | Retained transition/approval evidence; ceases to be normative once every disposition is reflected here.                          |
| PLN-GF-001 v0.2                                           | Historical legal/control evidence only.                                                                                          |
| PLN-GF-002 v0.2                                           | Historical context/governance/workspace evidence only; there is no PLN-GF-002 workspace.                                         |
| PLN-GF-003 v0.2                                           | Historical P3 and UI evidence only.                                                                                              |
| Procurement Planning Revision Ledger / PLN-CHG-001-018    | Historical decision/UI/implementation evidence only.                                                                             |
| Procurement Planning Stitch Prompts v1.9                  | Historical visual composition evidence only; replaced by the new Stitch Contract.                                                |
| Greenfield Planning handoff and superseded semantic audit | Continuity/assurance evidence only.                                                                                              |
| NDS-CHG-002                                               | Remains in the Departmental Needs authority chain; Planning consumes only the exact approved interface reflected in section 6.2. |

No prior file is deleted. After canonical approval, none is consulted to determine current Planning behaviour.

## **18.3 Approval conditions**

Product-owner approval of this exact version fixes the product baseline, including the resolved cross-department aggregation model and departmental amendment intake. It does not certify legal closure of LEG-AUTH-001 or production readiness of the external publication adapter.

Production implementation approval additionally requires:

1. written legal/policy closure of ASMP-001 through ASMP-003 where applicable;
2. exact approved NDS, Configuration, Strategy and Budget input versions;
3. approved Functional Requirements, Stitch Contract, Seed Data Contract and Implementation Pack carrying this exact fingerprint;
4. approved UI Keep/Correct/Retire selector/screenshot inventory; and
5. passing Gate 6 acceptance evidence from section 16.

# **Appendix A. Canonical lifecycle traceability**

| **Lifecycle stage**          | **Records**                                               | **Commands**                                  | **Screens**                     | **Primary acceptance**          |
| ---------------------------- | --------------------------------------------------------- | --------------------------------------------- | ------------------------------- | ------------------------------- |
| Context/cycle                | Context, Assignment, Planning Cycle, Workspace Projection | Resolve contexts, Get workspace               | PLN-UI-00, 01A-01G, SUP-01      | CAN-AC-001-002; CAN-SEC-001-004 |
| Accepted Need intake         | DPP, Entry                                                | ProjectAcceptedNeed                           | P3-UI-DPP-01/02                 | CAN-AC-003-004                  |
| HoD submission               | Submission, Submission Entry, DPP Decision                | Submit/Resubmit/Withdraw                      | P3-UI-DPP-02/02A/04/05/07       | CAN-AC-005-007                  |
| Procurement validation       | Validation, Classification, Issue, Accepted Projection    | Return, Accept, Reopen                        | P3-UI-DPP-03A-D/06A-B           | CAN-AC-006-009                  |
| Consolidation                | Annual Plan, Version, Plan Item, Allocation, Hold         | Begin consolidation, Form items               | PLN-UI-02-05                    | CAN-AC-010-011                  |
| Item completion              | Plan Item treatment/schedule                              | Save, Request Finance                         | PLN-UI-06                       | CAN-AC-012-013                  |
| Finance                      | Task, Decision, Reservation ref                           | Confirm, Return                               | PLN-UI-07/07A/07B               | CAN-AC-014-016                  |
| Professional validation      | Review Task, Decision                                     | Submit, Validate, Return                      | PLN-UI-08/08R                   | CAN-AC-017-018                  |
| AO certification             | Planning Decision                                         | Certify, Return                               | PLN-UI-08A/08AR                 | CAN-AC-019                      |
| Statutory approval           | Planning Decision                                         | Approve, Return                               | PLN-UI-08B/08BR                 | CAN-AC-020                      |
| Publication/activation       | Plan Publication, Version                                 | Publish, Activate                             | PLN-UI-08C/08CA                 | CAN-AC-021-022                  |
| Requisition boundary         | Eligibility, Drawdown reference                           | Get eligibility                               | PLN-UI-09/09A                   | CAN-AC-023-024                  |
| Amendment/removal/monitoring | Successor, DPP amendment, Monitoring Entry                | Prepare update, Remove, Cancel, Record actual | P3-UI-DPP-09; PLN-UI-05A/B; 09M | CAN-AC-009; CAN-AC-025-026      |

# **Appendix B. Mandatory negative acceptance checks**

The canonical derivative or implementation fails review if any of the following appears:

- **PLN-GF-002 workspace** or any workspace named after a source document;
- **Create annual plan** as a manual blank-root flow;
- Approved Demand/DMD or direct accepted Need to Annual Plan Item without the DPP boundary;
- three-digit NDS-MOH-2027-001, KES 455,000,000 or 31 March 2028 silently reused for the primary canonical fixture;
- Head of Procurement Function or Accounting Officer described as universal final approver;
- professional validation, AO certification, statutory approval and publication collapsed into one generic review;
- Approved treated as Active before exact publication acknowledgement;
- Annual Plan publication described as Tender advertising or bid opening;
- direct Plan Item to Tender creation, take-up or supplier route;
- Requisition eligibility omitted as the immediate downstream boundary;
- source-owned Need facts editable in Planning;
- Multi-year, Lots expected, unsupported method or partial funding available as hidden or visible MVP-1 values;
- submitted/approved/active snapshots editable in place;
- client-side-only authorization, disabled unauthorized task forms or administrator wildcard authority;
- legacy models, imports, aliases, routes, dual writes, fallback reads or repair seeds;
- a Stitch prompt requiring another prompt or historical document to determine visible content;
- a derivative adding a product requirement absent from this exact canonical version; or
- a regulation-dependent proposition labelled settled current law without recorded closure evidence.

# **Appendix C. Authority and evidence source register**

| **Source**                                                                                                            | **Canonical use**                                                              | **Official location / treatment**                                         |
| --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| Constitution of Kenya, Article 227                                                                                    | Procurement-system principles                                                  | <https://new.kenyalaw.org/akn/ke/act/2010/constitution/eng@2022-12-31>    |
| Public Procurement and Asset Disposal Act, 2015, especially sections 44, 45, 47, 53 and 54                            | Primary duties, accountability, budget, planning and anti-splitting            | <https://new.kenyalaw.org/akn/ke/act/2015/33/eng@2022-07-26>              |
| Roads and Civil Engineering Contractors Association & another v Attorney General & another, \[2025\] KEHC 19224 (KLR) | Legal-status hold for the 2020 Regulations                                     | <https://new.kenyalaw.org/akn/ke/judgment/kehc/2025/19224/eng@2025-12-04> |
| Republic v Public Procurement Regulatory Authority; Nzai, \[2026\] KEHC 1483 (KLR)                                    | Later practical reference illustrating unresolved regulatory treatment         | <https://new.kenyalaw.org/akn/ke/judgment/kehc/2026/1483/eng@2026-02-13>  |
| Public Procurement and Asset Disposal Regulations, 2020 and Third Schedule                                            | Historical procedure/form evidence only, subject to LEG-AUTH-001               | <https://new.kenyalaw.org/akn/ke/act/ln/2020/69/eng@2022-12-31>           |
| PPRA Circular 05/2023                                                                                                 | Historical/current administrative publication context requiring reconciliation | <https://ppra.go.ke/download/circular-052023/>                            |
| Kenya Electronic Government Procurement System                                                                        | External publication context; exact current contract held                      | <https://egpkenya.go.ke/>                                                 |
| PLN-CDR-001 v0.1                                                                                                      | Approved conflict and disposition baseline                                     | Transitional internal evidence incorporated into this document.           |
| PLN-GF-001/002/003 v0.2                                                                                               | Greenfield lifecycle, context, P3 and control evidence                         | Superseded on approval.                                                   |
| Procurement Planning Revision Ledger and Stitch v1.9                                                                  | Earlier UI composition, task, Finance and successor evidence                   | Historical UI evidence only.                                              |
| NDS-CHG-002 v0.1                                                                                                      | Upstream Need shape and derivative completeness pattern                        | Reconcile exact approved version before release.                          |

# **Appendix D. Approval record**

| **Decision**                                                                                             | **Product-owner response**                                          | **Date**       | **Version** |
| -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | -------------- | ----------- |
| Approve PLN-CAN-001 as the sole Procurement Planning product-truth baseline with bounded legal treatment | Approved by product owner                                           | 21 August 2026 | 0.1         |
| Approve cross-department aggregation under section 10.4                                                  | Approved as part of canonical approval                              | 21 August 2026 | 0.1         |
| Approve post-consumption departmental amendment intake under section 6.3                                 | Approved as part of canonical approval                              | 21 August 2026 | 0.1         |
| Authorise production use of the external publication adapter                                             | Not approved; hold retained pending LEG-AUTH-001 / ASMP-003 closure | 21 August 2026 | 0.1         |