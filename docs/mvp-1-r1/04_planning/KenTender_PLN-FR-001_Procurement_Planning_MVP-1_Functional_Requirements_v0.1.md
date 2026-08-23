# PLN-FR-001 — Procurement Planning MVP-1 Functional Requirements

## 1. Document control and binding

| Item | Value |
| --- | --- |
| Document ID | PLN-FR-001 |
| Title | KenTender Procurement Planning MVP-1 Functional Requirements |
| Version | 0.1 |
| Date | 21 August 2026 |
| Status | Approved |
| Derivative type | Functional Requirements |
| Canonical source | PLN-CAN-001 — KenTender Procurement Planning MVP-1 Canonical Source Specification |
| Canonical version | 0.1, approved 21 August 2026 |
| Canonical content fingerprint | `sha256:2e8e8790309b4d738ab80934f609111753f94766aab8e4bf2d3313146289e879` |
| Approved Stitch output version | Not applicable — the new Stitch Contract has not yet been produced or approved |
| Build posture | Greenfield schema and services; reuse the approved Planning UI composition; no legacy compatibility |
| Production holds | LEG-AUTH-001 and ASMP-003 remain open for the external publication integration; ASMP-001 to ASMP-004 require the closures stated in PLN-CAN-001 |

> **Binding instruction.** If this derivative conflicts with or omits a required canonical rule, stop and return the issue to PLN-CAN-001. Do not infer a resolution.

PLN-CAN-001 is the sole product truth. This derivative organises that truth as testable functional requirements. It does not supersede, amend or extend the canonical source. Historical PLN-GF documents, the Procurement Planning Revision Ledger, earlier Stitch prompts and constructed screens are not sources of current product behaviour.

## 2. Purpose, use and derivative boundary

This document specifies the actors, authoritative inputs, Planning records, states, commands, guards, validations, outcomes, errors and acceptance obligations for Procurement Planning MVP-1. It is the functional contract used to prepare the later Stitch Contract, Seed Data Contract and Implementation Pack.

This document intentionally does not specify:

- screen geometry, responsive coordinates, typography, component selectors or screenshot fixtures; those belong to the Stitch Contract;
- concrete personas, identifiers, dates, amounts, hashes or reset profiles; those belong to the Seed Data Contract;
- physical schema, endpoint paths, framework choices, serialization shapes, job topology or deployment configuration; those belong to the Implementation Pack; or
- behaviour absent from PLN-CAN-001.

The fixed module boundary is: Procurement Planning consumes current accepted Departmental Needs, creates and governs Departmental Procurement Plans and the Annual Procurement Plan, reconciles Finance evidence, records named governance decisions, publishes the approved Annual Plan through a governed adapter, and exposes active Plan Item eligibility to Procurement Requisitions. Planning does not create a Procurement Requisition or Tender.

## 3. Normative conventions and priority

**Shall**, **must**, **required** and **prohibited** are binding. **May** identifies an allowed choice. **Derived** means calculated from authoritative records and never written directly by a client. **Snapshot** means immutable evidence captured at a decision boundary.

Each requirement retains its canonical `CAN-FR-*` identifier. This avoids a second numbering system and makes the canonical-to-functional relationship exact. The columns in section 10 add testable actor, guard and outcome detail but do not change the canonical rule.

If any provision appears to conflict, apply the priority order in PLN-CAN-001 section 1.3. A lower-level surface, fixture or implementation choice cannot override authority status, product boundaries, ownership, state, command or authorization controls.

## 4. Functional scope and lifecycle

The supported lifecycle is:

1. Configuration & Governance declares the PE/FY context, departments, departmental-plan window, effective assignments, method catalogue, reservation rules, approval route and publication destination.
2. Strategy Alignment and Budget & Funding provide governed references that Planning reads but does not alter.
3. Departmental Needs supplies a current Need version in **Accepted for planning** for one PE, FY and department.
4. Planning projects every eligible Need exactly once and at full accepted quantity into the department's DPP.
5. The HoD or valid delegate certifies and submits an immutable DPP submission addressed to the Accounting Officer.
6. The assigned Procurement DPP Validator classifies every entry and returns the submission with structured issues or accepts it for consolidation.
7. A Procurement Planner uses **Begin consolidation** to create or reuse the single Annual Plan root and Draft Version from eligible accepted DPP sources.
8. Procurement forms separate or governed combined Plan Items, preserves all source allocations and completes the professional treatment and seven-date schedule.
9. Finance confirms the full required funding for all allocations atomically or returns the item.
10. The Head of Procurement Function professionally validates the exact submitted version and submits it to the Accounting Officer.
11. The Accounting Officer certifies the exact version and submits it to the configured statutory approving authority.
12. The configured authority approves or returns the certified version.
13. A Publication Operator transmits the exact approved payload. Authoritative acknowledgement, not approval alone, activates the version.
14. The sole Active version exposes eligible Plan Items and remaining quantity/value to Procurement Requisitions.
15. Monitoring appends actual milestones and variance without changing the approved baseline.
16. Additions, changed sources and eligible whole-item removals use immutable departmental amendments and one Draft successor; the Active predecessor remains operational until successor activation.

MVP-1 supports one declared PE/FY per Planning Cycle, one DPP per department/cycle, single-year Plan Items, **No lots expected**, configured Open Tender, full-value all-source Finance confirmation, separate or compatible combined formation, one Active Plan Version and at most one open Draft successor.

Multi-year items, lots, unsupported methods, partial Need inclusion, Planning quantity override, partial Finance confirmation, source-level detachment from a combined item, direct Requisition creation and direct Tender initiation are unavailable and fail closed.

## 5. Actors, authority and segregation

| Actor | Minimum effective scope | Permitted responsibility | Prohibited effect |
| --- | --- | --- | --- |
| Departmental Plan Preparer | PE + FY + department | Read projected accepted Needs, coverage and upstream correction links | HoD submission, classification, validation, consolidation or source edit |
| Head of User Department | PE + FY + department | Certify and submit an initial or amendment DPP; withdraw eligible Draft/Returned DPP | Validate own submission, edit source facts or approve Annual Plan |
| Valid HoD Delegate | Exact delegated command, PE, FY, department and time | Perform only the recorded HoD command | Generic fallback or authority outside delegation |
| Procurement DPP Validator | PE + FY + DPP validation capability | Classify entries, create structured issues, return, accept and eligible reopen | Change Need facts, validate own submission or approve Annual Plan |
| Procurement Planner / Consolidator | PE + FY | Begin consolidation, form items, complete treatment, request Finance and prepare successors | Certify/approve own work or alter upstream/downstream records |
| Head of Procurement Function | PE + FY + professional-validation capability | Validate the complete Plan Version professionally or return it | Final approval by implication or submitted-snapshot edit |
| Budget Officer | PE + FY + funding scope + Finance capability | Confirm all-source full funding or return an item | Plan approval, inline Budget edit or partial confirmation |
| Accounting Officer | PE + effective AO capability | Certify exact professionally validated version and submit onward, or return it | Final approval unless the approved route expressly assigns it; snapshot edit |
| Statutory Approving Authority | PE + FY + configured approval capability | Approve or return the AO-certified version | Certified-content edit or publication as a side effect |
| Publication Operator | PE + FY + publication capability | Transmit/retry exact approved payload and view acknowledgement | Payload change, self-declared success or Tender advertisement |
| Monitoring Officer | PE + FY + monitoring capability | Append actual milestone/progress evidence | Planned-baseline or downstream-record edit |
| Auditor / Oversight | Lawful oversight scope | Read immutable evidence | Any Planning command |
| System Administrator | Audited support scope | Labelled read-only projection and technical diagnostics | Business decision, impersonation or authority substitution |

The server shall authorize each read and command at execution time using the same predicate: exact effective capability, matching PE/FY, matching department or funding scope where applicable, valid delegation, command-permitted record state, maker-checker compliance, current optimistic version/task/source-set, and all lower-level invariants. A role label, selected context, known identifier, hidden control or administrator privilege grants no authority.

The following separations are mandatory:

- a DPP submitter cannot validate or accept that submission;
- a material Plan Version preparer cannot professionally validate it;
- the professional validator cannot AO-certify or finally approve that version in MVP-1;
- the AO cannot finally approve unless the approved PE-type route names the AO as the authority;
- Finance confirmation grants no Planning approval authority; and
- unauthorized task forms and controls are omitted, while direct access is denied before protected data is serialized.

## 6. Authoritative inputs and ownership

| Input or fact | Authoritative owner | Planning use | Planning prohibition |
| --- | --- | --- | --- |
| PE/FY context, PE type, FY dates/timezone, departments | Configuration & Governance | Context declaration, scope, display and snapshots | Generate undeclared combinations or shadow masters |
| Departmental Plan submission window | Configuration & Governance | Derived Scheduled/Open/Closed behavior and decision snapshot | Manual status or reuse of Needs intake window |
| Assignments and delegations | IAM / Access Governance | Live read/command authority and immutable decision snapshot | Client-supplied authority or generic fallback |
| Method catalogue | Configuration & Governance | Server allow-list and basis | Persist an unconfigured method |
| Reservation rules | Configuration & Governance | Calculation and validation | Manual pass flag |
| Approval route | Configuration & Governance | Named professional, AO and final authority sequence | Generic approval substitution |
| Publication destination | Integration Configuration | Exact destination/profile/configuration evidence | Production transmission before held assumptions close |
| Need ID/version/hash/state/context/department/title/description/unit/quantity/required-by/strategy/budget/funding/source evidence | Departmental Needs and its authoritative upstream owners | Idempotent DPP projection, immutable snapshots, staleness and lineage | Edit, duplicate, partially include, inflate or silently repair |
| Budget lines, funding sources, ceilings, availability and reservations | Budget & Funding | Read, reconcile, reserve through governed service and snapshot evidence | Create/approve Budget or mutate ledger inline |
| Requisition and downstream milestones | Owning downstream module | Drawdown and neutral monitoring projections | Create or alter downstream transactional records |

Planning accepts a Need only through a trusted versioned event or equivalent authoritative pull. It must be exactly **Accepted for planning**, match a declared PE/FY/department, carry a stable four-digit NDS identifier and exact current version/hash, have a positive governed unit/quantity, have required-by inside the supported FY, and have current required Strategy/Budget/funding references. Any ineligible or cross-context source fails closed.

## 7. Functional records and global invariants

### 7.1 Planning-owned records

| Record | Minimum business attributes | Mandatory invariant |
| --- | --- | --- |
| Planning Cycle | Cycle ID; declared context ID; created actor/time; audit metadata | Unique by context; read never creates it; may exist without an Annual Plan |
| Departmental Procurement Plan | DPP ID/reference; cycle/context; department; current projection; current accepted submission; optimistic version | Unique by cycle + department; stable root; no hard delete after first submission |
| DPP Entry | Entry ID; DPP; source Need/version/hash; projection status; professional requirement type | Unique by DPP + Need; one current projection; source facts read-only |
| DPP Submission | Submission ID/number; initial or amendment purpose; predecessor; payload/source-set hashes; HoD/recipient/window snapshots; submitted time | Immutable, monotonic and exact as to actor, authority, recipient and sources |
| DPP Submission Entry | Submission; Need/version; description, unit, quantity, required-by, Strategy, Budget and funding snapshots; source hash | Exactly one per included current Need; values equal the authoritative accepted version used |
| DPP Validation | Submission; validator/assignment; start/end; outcome; validation hash | At most one terminal outcome per submission; terminal outcome immutable |
| DPP Entry Classification | Validation; submission entry; governed requirement type; actor/time | Exactly Goods, Works, Non-consulting services or Consulting services; no free text |
| DPP Validation Issue | Submission; optional affected entry; code; owner module/record; explanation; required action; actor/time; resolution source version | Actionable structure; no generic reason alone or self-declared upstream resolution |
| DPP Decision | DPP/submission; command; from/to; actor/assignment/delegation; reason; time; idempotency key | Append-only; authority effective at decision time; reason required where specified |
| Accepted DPP Projection | Current accepted submission; source-set hash; current eligibility; blocker codes | Computed output, not a writable master; consumption names the exact submission/hash |
| Annual Procurement Plan | Plan ID; cycle; reference; current Active version | Exactly one per Planning Cycle; read never creates it; stable across amendments |
| Plan Version | Version ID; plan; number; predecessor; purpose; state; source-set hash; submitted/decision snapshots; totals; optimistic version | Monotonic; at most one Active and one open Draft successor; immutable after submission except named decisions |
| Plan Item | Stable item identity/reference; owner scope; treatment; schedule; value; version | Never blank; belongs to one version snapshot; source allocations reconcile exactly |
| Plan Source Allocation | Item; DPP submission entry; Need/version; quantity/value; Budget/funding lineage; allocation state | No source over-allocation or duplicate/conflicting current consumption |
| Draft Source Hold | Draft/item/allocation identity; held source quantity/value | Draft only; released on eligible removal/cancellation; source approval unchanged |
| Finance Task Iteration | Version/item; source funding allocations; assigned capability; prior iteration; state; concurrency token | At most one actionable iteration; protected content; linked history |
| Finance Decision | Task/item; every funding allocation/version; amount; actor/assignment; outcome; note/reason; time | Full-value, all-source, immutable and idempotent; no partial success |
| Funding Reservation Reference | Authoritative Budget reservation identity; source allocation; Finance decision | Created/released through the Budget service; never duplicated or forged locally |
| Professional Review Task | Exact submitted Plan Version; assigned capability; iteration; state; prior return | One actionable current iteration; immutable submitted snapshot |
| Planning Decision | Named decision type; version/item; actor/authority; from/to; reason/note; time; input hash; idempotency key | No generic approval flag; returns preserve prior evidence |
| Plan Publication | Approved version; payload hash; destination/configuration version; request; response; attempt/time | Exact approved payload; success only with authoritative acknowledgement; immutable evidence |
| Requisition Eligibility Projection | Active item; source/allocation lineage; remaining quantity/value; blockers; As-at | Read-only computed output; Planning creates no Requisition/Tender |
| Requisition Drawdown Reference | Authoritative Requisition ID and consumed amount/quantity | Prevents overdraw; owned by Requisitions and projected into Planning |
| Plan Monitoring Entry | Version/item; milestone; planned baseline reference; actual date/status; evidence; actor/time; correction link | Append-only; actuals never overwrite approved planned values |
| Workspace Projection | Authorised context; cycle/Plan summary; action queue; waiting queue; exact commands | Computed per request; common authorization predicate; no stored duplicate counters |

### 7.2 Global functional invariants

- Reads, context changes, counts, lists and detail opens create no business record.
- Submitted, returned, validated, certified, approved, active, superseded and cancelled evidence is never edited in place.
- Each eligible accepted Need appears exactly once and at full quantity in the current DPP before submission.
- Every consumed DPP submission entry retains exact lineage through Plan Source Allocations and Requisition drawdown.
- Allocation quantity/value never exceeds the authoritative source, and no effective allocation or Draft hold conflicts with another current use.
- The Active version remains operational while a successor is Draft, Returned, certified, approved or awaiting publication.
- Statutory approval alone never activates a Plan Version; exact-payload acknowledgement activates it and supersedes the predecessor atomically.
- Monitoring and downstream projections never rewrite the approved baseline.
- No Planning command creates a Requisition, Tender, bid window, tender notice or supplier-facing record.

## 8. Functional field and validation contract

### 8.1 DPP fields

| Value | Owner / entry rule | Submission and operational rule |
| --- | --- | --- |
| DPP reference | Planning-generated, read-only | Immutable stable root reference |
| PE, department and FY | Configuration-derived, read-only | Exact scope; snapshotted at submission |
| Submission window | Configuration-derived, read-only | Identifier, open/close and evaluated instant captured |
| HoD/delegate | IAM-resolved at command | Actor, assignment/delegation and effective dates captured |
| Accounting Officer recipient | Approval configuration, resolved at command | Exact assignment and display snapshot; no generic mailbox |
| Need reference, title and description | Departmental Needs, read-only | Exact current accepted version; no Planning edit |
| Unit, quantity and required-by | Departmental Needs, read-only | Full accepted quantity and required-by within FY |
| Strategy/programme/project | Strategy through Need, read-only | Present only when authoritative/required; no placeholder |
| Budget line, funding source and governed amount | Budget/Need, read-only | Same PE/FY; DPP validation does not confirm funding |
| Requirement type | Procurement DPP Validator | Exactly Goods, Works, Non-consulting services or Consulting services; required before acceptance |
| Source and issue state | Derived, read-only | Exact current/stale/blocker result; no percentage or manual checklist |

### 8.2 Annual Plan header

| Value | Source / entry rule | Evidence rule |
| --- | --- | --- |
| Ministry/parent institution | PE hierarchy | Snapshot on submitted version |
| Procuring Entity | Authorised selected context | Reference plus immutable display snapshot |
| Project name | Governed project reference only where applicable | Nullable reference/snapshot; no compulsory free text |
| Financial year | Context | FY reference, label, dates and timezone snapshot |
| Plan reference and version | Planning-generated | Stable root plus monotonic version |
| Plan purpose and change reason | Planning; reason required for successor | Initial, addition, removal or source amendment; concise business reason |
| Current decision owner and state | Derived | Exact capability/state; never generic **In review** |
| Total planned value and item count | Derived | Exact reconciliation to included items and allocations |

### 8.3 Plan Item and Annual Plan output fields

| Field | Owner / presentation | Operational rule |
| --- | --- | --- |
| Item number | System-generated in submitted version | Deterministic sequence; not business identity |
| Source breakdown | DPP submission entries/allocations, read-only | Every department, Need, quantity, value, Budget and source version visible |
| Procurement-facing description | Procurement Planner, required | Comprehensive planning description; not a tender specification and must not contradict source scope |
| Requirement type/category | DPP classification/governed catalogue | No free text; drives output validation |
| Unit and quantity | Derived from allocations | Exact reconciliation; combined sources require compatible treatment |
| Planned value | Derived full-precision KES allocation total | Reconciles to governed sources and applicable incidental procurement costs |
| Recommended method and basis | Governed derived result | Explain configured basis; no opaque automated decision |
| Planned procurement method | Governed select | MVP-1 accepts configured Open Tender only |
| Contract period | Governed value | **Single year** only |
| Indicative lotting | Governed value | **No lots expected** only |
| Aggregation decision | Procurement Planner when sources are combined | Concise professional reason and compatibility evidence; no source loss |
| Source of funds | Derived per funding allocation | Show every source; no inline substitution |
| Invitation/advertisement date | Procurement Planner | Required planned milestone within supported period |
| Bid opening date | Procurement Planner | Required and after invitation |
| Evaluation completion date | Procurement Planner | Required and after bid opening |
| Tender award approval date | Procurement Planner | Required planned date only; not an award decision |
| Notification of award date | Procurement Planner | Required and after award approval |
| Contract signing date | Procurement Planner | Required and after notification |
| Delivery/implementation/completion date | Procurement Planner | Required and at/before source required-by for the single-year case |
| Planned days to contract signature | Derived | Contract-signing date minus invitation date |
| Finance state | Derived from current Finance evidence | Not requested, Awaiting confirmation, Returned by Finance, Confirmed or Stale |
| Actual dates and variance | Monitoring projection | Append-only evidence; approved baseline unchanged |

The item mutation command accepts only procurement-facing description, permitted governed category where not fixed by DPP classification, planned method identifier, contract period, lotting decision, permitted aggregation reason and the seven planned milestone dates. It rejects attempts to write PE, FY, department, Need/version, source description, unit, quantity, required-by, Strategy, Budget line, funding source, allocation value, state, completeness, decision, reservation, version ownership or unknown fields.

For MVP-1 the only admitted values are an active configured Open Tender method, **Single year** and **No lots expected**. All seven dates are required for Finance request and later submission, must be chronological, must fit the governed FY and required-by constraints, and must satisfy configured legal-policy rules.

### 8.4 Combined-formation validation

A combined item is permitted only when all selected sources share the same PE and FY; are current, accepted and unconsumed; have compatible governed requirement type, unit, description and delivery obligations; support one coherent single-year schedule; permit atomic all-source funding without prohibited substitution; do not conceal splitting or a separation duty; have no financing, legal, donor, security, confidentiality or contractual separation restriction; and carry a concise professional common-supply, market, delivery or operational reason. Failure blocks combined formation but not otherwise valid separate formation. Department identity alone is not an incompatibility rule, and the system does not make the professional procurement decision automatically.

## 9. State and command contract

### 9.1 Derived Planning Cycle states

| Derived state | Condition | Functional effect |
| --- | --- | --- |
| No authorised context | Actor has no effective Planning visibility assignment | Return the no-access projection and disclose no selector, count or Plan existence |
| Scheduled | Context is valid but the DPP submission window is not open | Read-only timing; no submission action |
| Open for departmental planning | Window is open and initial DPP work is permitted | Capability-specific DPP tasks may appear |
| Consolidation / approval in progress | Eligible accepted DPP work or Annual Plan workflow exists | Exact current decision owner and authorised work appear |
| Active plan | One approved and acknowledged version is Active | Operational baseline and Requisition eligibility are available |
| Active plan with Draft successor | Active version coexists with one open successor | Active baseline stays operational and Draft actions remain separate |
| Closed / historical | No current action and cycle is outside active operation | Authorised read-only evidence only |

No client or user maintains a cycle status, and there is no open-cycle approval command.

### 9.2 Departmental Procurement Plan states and commands

| From | Command | Actor | Mandatory guard | Atomic successful outcome |
| --- | --- | --- | --- | --- |
| Draft | Submit departmental plan | HoD or valid delegate | Window open; current exact scope; complete full source coverage; no blocker | Submitted state and immutable submission, recipient, authority, attestation and source snapshot |
| Returned | Resubmit departmental plan | HoD or valid delegate | Corrected accepted source projection; complete current coverage; current predecessor | New Submitted snapshot/number linked to predecessor |
| Submitted | Return to department | Assigned DPP Validator | Non-self; at least one complete structured issue | Returned state, terminal return decision and immutable issue set; submitted payload unchanged |
| Submitted | Accept for consolidation | Assigned DPP Validator | Non-self; current sources; every entry classified; no blocker | Accepted for consolidation, terminal validation and computed eligible source; no Annual Plan approval |
| Draft or Returned | Withdraw departmental plan | HoD or valid delegate | Reason and no accepted downstream consumption | Withdrawn state and preserved history |
| Accepted for consolidation | Reopen for source correction | Assigned DPP Validator | Source changed and no consolidation consumption | Returned state with reason/change evidence; prior accepted evidence preserved |
| Consumed accepted submission | Prepare departmental plan update | Trusted source projection plus HoD workflow | New accepted source version/change | Amendment Draft projection with predecessor; Active Plan unchanged |

The submit attestation must be presented verbatim with the resolved department and financial year:

> **I certify that this Departmental Procurement Plan contains the current accepted procurement needs of {department} for {financial_year}, and that the descriptions, units, quantities and required-by dates shown are the authoritative departmental records submitted for consolidation. I understand that source corrections must be made in the owning module and resubmitted.**

A deterministic validation failure creates blocker evidence only; it never performs a return, acceptance, withdrawal or reopen.

### 9.3 Annual Plan Version states

| State | Meaning and editability | Next decision owner |
| --- | --- | --- |
| Draft | Initial or successor is being prepared; only planner-owned fields are editable and source facts remain read-only | Procurement Planner |
| Awaiting Finance reconciliation | One or more complete items have current Finance tasks; awaiting items are not planner-editable | Budget Officer |
| Returned by Finance | Finance returned at least one item; only affected planner-owned fields reopen | Procurement Planner |
| Ready for professional validation | All items are complete with current Finance evidence and no blocker; submission freezes the snapshot | Head of Procurement Function |
| Awaiting AO certification | Professional validation passed on the exact immutable version | Accounting Officer |
| Awaiting statutory approval | AO certified and submitted the exact immutable version | Configured statutory approving authority |
| Returned | A named authority returned immutable evidence; the returned snapshot is not edited | Procurement Planner or prior workflow owner through the governed correction path |
| Approved - publication pending | Configured authority approved the exact version; content is immutable | Publication Operator |
| Publication failed | Latest exact-payload attempt failed; approval remains valid and payload cannot change | Publication Operator retry |
| Active | Exact approved payload was acknowledged and is the operational baseline | Monitoring, Requisitions and amendment actors |
| Superseded | A successor activated; content remains immutable | Historical readers only |
| Cancelled | Draft/Returned successor was cancelled with reason | Historical readers only |

Finance confirmation, professional validation, AO certification, statutory approval and publication acknowledgement are immutable decisions or evidence, not editable state fields. A generic persisted **In review** state is prohibited.

### 9.4 Annual Plan Version commands and transitions

| From | Command | Actor | Mandatory guard | Atomic successful outcome |
| --- | --- | --- | --- | --- |
| No Annual Plan root | Begin consolidation | Procurement Planner | Authorised context and at least one eligible accepted DPP source | One Annual Plan root and Draft Version 1, created or reused idempotently |
| Active with no successor | Begin plan update | Procurement Planner | Eligible accepted change source or eligible whole-item removal | One Draft successor; predecessor remains Active |
| Draft | Save Plan Item draft | Procurement Planner | Mutation allow-list and current optimistic version | Allowed fields saved; completeness recalculated; no Finance task |
| Draft or Returned by Finance | Request Finance confirmation | Procurement Planner | Complete item, current source/allocation set and no blocker | Fields saved and one current protected Finance task created/reused in one transaction |
| Awaiting Finance reconciliation | Confirm funding | Assigned Budget Officer | Full live all-source availability and current task/source locks | All reservations, one immutable Finance decision and task completion; Plan remains Draft |
| Awaiting Finance reconciliation | Return to planner | Assigned Budget Officer | Required reason and current task | No reservation; immutable return; affected planner fields reopen; linked iteration retained |
| Draft with all gates ready | Submit for professional validation | Procurement Planner | Effective change, complete items, current full Finance, complete allocations, supported treatment and no blocker | Immutable submitted version snapshot and one protected professional task |
| Submitted for professional validation | Validate and submit to Accounting Officer | Head of Procurement Function | Non-self material-preparation check and complete live revalidation | Immutable professional decision and Awaiting AO certification; no approval/activation |
| Submitted for professional validation | Return to planner | Head of Procurement Function | Required actionable reason | Returned outcome; task completed; active predecessor and submitted evidence unchanged |
| Awaiting AO certification | Certify and submit | Accounting Officer | Exact professionally validated version, current funding/sources/output and effective AO authority | Immutable AO certification and Awaiting statutory approval |
| Awaiting AO certification | Return for correction | Accounting Officer | Required actionable reason | Returned outcome; exact snapshot preserved |
| Awaiting statutory approval | Approve Annual Procurement Plan | Configured statutory authority | Exact route/assignment, maker-checker and current certified version | Immutable approval and Approved - publication pending; no publication/activation |
| Awaiting statutory approval | Return for correction | Configured statutory authority | Required actionable reason | Returned outcome; no edit or silent correction |
| Approved - publication pending or Publication failed | Publish Annual Procurement Plan / Retry publication | Publication Operator | Production gate open; exact approved payload/hash; current destination configuration | Attempt evidence; Active only on exact authoritative acknowledgement, otherwise retryable failed/indeterminate state |
| Active predecessor plus acknowledged successor | Activate successor | System within publication transaction | Exact acknowledged successor and one-active invariant | Successor Active, predecessor Superseded and approved additions/removals/allocations applied once |
| Draft or Returned successor | Cancel plan update | Procurement Planner with capability | Required reason and eligible cancellation | Cancelled successor; Draft holds/effects reversed; Active predecessor unchanged |

Every state-changing command requires an idempotency key and current optimistic version or task token. Source-sensitive commands also validate the exact source-set hash. Failed guards roll back the whole command and create no partial item, allocation, reservation, task, decision, version or publication effect.

## 10. Detailed functional requirements

### 10.1 Context, workspace and cycle controls

| ID | Actor / record | Preconditions and trigger | Required functional result | Primary acceptance |
| --- | --- | --- | --- | --- |
| CAN-FR-001 | Authenticated actor; Planning context projection | Actor requests Planning entry or context list | Return only active declared PE/FY contexts within effective Planning visibility. Zero contexts disclose no Planning data; one auto-selects; many require deliberate selection. | CAN-AC-001; CAN-SEC-001, 008 |
| CAN-FR-002 | Actor; remembered context | Client presents a remembered context | Revalidate it against current server authority. It is convenience only, creates no authority and never falls back to a broader default. | CAN-AC-001; CAN-SEC-003 |
| CAN-FR-003 | Actor; Workspace Projection | Authorised context is resolved | Derive summary, counts, action queue, waiting queue, links and commands with one common authorization predicate; counts reconcile to visible rows. | CAN-SEC-002, 008 |
| CAN-FR-004 | System; Planning Cycle | Configuration prerequisites pass and an authorised materialisation command occurs | Create/reuse exactly one cycle for the declared context idempotently. Workspace reads never create it. | CAN-AC-002; CAN-SEC-007 |
| CAN-FR-005 | Procurement Planner; Annual Plan root | Begin consolidation has at least one eligible accepted DPP source | Create the unique Annual Plan root only within the guarded command; no read or empty registration creates it. | CAN-AC-002, 010 |
| CAN-FR-006 | Actor; configuration projection | Required Planning configuration is absent or invalid | Return a safe business-unavailable state with a stable support reference; disclose diagnostic detail only to authorised support. | CAN-SEC-001, 004, 008 |
| CAN-FR-007 | Actor; context surface | Context control is presented | Present exactly: **These controls define the workspace view; they do not change record ownership or grant operational authority.** | UI evidence in later Stitch Contract; CAN-AC-001 |
| CAN-FR-008 | Actor; workspace | Planning workspace is presented | Present exactly: **Turn accepted departmental plans into funded, approved Plan Items ready for requisitioning.** | UI evidence in later Stitch Contract |

### 10.2 Accepted Need projection and DPP submission

| ID | Actor / record | Preconditions and trigger | Required functional result | Primary acceptance |
| --- | --- | --- | --- | --- |
| CAN-FR-010 | Trusted Departmental Needs producer; DPP/DPP Entry | Current accepted Need event or authoritative pull matches one cycle/department | Create/reuse one DPP root and one current entry idempotently; do not create an Annual Plan. | CAN-AC-003 |
| CAN-FR-011 | HoD/delegate; DPP current projection | Submit or resubmit is requested | Require every current eligible accepted Need exactly once and at full quantity. Block omission, duplication, partial quantity or local inflation without creating a submission. | CAN-AC-004 |
| CAN-FR-012 | Departmental actor or Procurement DPP Validator; source facts | Any Planning write attempts to change Need-owned description, unit, quantity, required-by, Strategy, Budget or funding fact | Reject the mutation and preserve the authoritative source. | CAN-AC-012; CAN-SEC-006 |
| CAN-FR-013 | HoD/delegate; DPP readiness | DPP readiness or submission eligibility is evaluated | Return an exact blocker set covering source currency, context, coverage, required data, Budget reference and window; never a score or percentage. | CAN-AC-004, 005 |
| CAN-FR-014 | HoD/delegate; DPP Submission | Submit/resubmit passes full guards | Atomically record exact payload, source versions/hashes, window, PE/FY/department, HoD authority, AO recipient, attestation hash, predecessor and idempotency key. | CAN-AC-005, 007 |
| CAN-FR-015 | Procurement DPP Validator; DPP issue/return | Validator returns a Submitted DPP | Require issue code, affected entry where applicable, owning module/record, concise defect and exact required action; preserve the submitted snapshot unchanged. | CAN-AC-007 |
| CAN-FR-016 | Assigned Procurement DPP Validator; classifications/validation | Submitted DPP is current; actor did not submit it | Permit only the four governed requirement types and allow acceptance only when all entries are classified and the submission is issue-free. | CAN-AC-006, 008 |
| CAN-FR-017 | Assigned Procurement DPP Validator; Accepted DPP Projection | Accept for consolidation passes all current-source and segregation guards | Publish a computed eligible source for consolidation and state that the action does not approve the Annual Procurement Plan. | CAN-AC-008 |
| CAN-FR-018 | System plus HoD workflow; DPP amendment | An authoritative source changes after its accepted DPP submission was consumed | Create a new amendment submission path under the stable DPP root; never rewrite prior DPP or Active Plan evidence. | CAN-AC-009 |

### 10.3 Consolidation and Plan Item formation

| ID | Actor / record | Preconditions and trigger | Required functional result | Primary acceptance |
| --- | --- | --- | --- | --- |
| CAN-FR-020 | Procurement Planner; Annual Plan/Draft Version | Begin consolidation receives current eligible accepted DPP sources | Atomically create/reuse one Annual Plan root and Draft Version and associate the selected exact sources. | CAN-AC-010 |
| CAN-FR-021 | Procurement Planner; source-selection projection | Authorised planner opens or refreshes source selection | List only current, accepted, unconsumed departmental entries for the selected PE/FY and consolidation scope. | CAN-AC-011; CAN-SEC-001, 008 |
| CAN-FR-022 | Procurement Planner; one selected DPP entry | One eligible entry is submitted for formation | Form one Proposed Plan Item and one exact Plan Source Allocation without a second formation choice. | CAN-AC-011 |
| CAN-FR-023 | Procurement Planner; multiple selected entries | More than one eligible entry is selected | Require exactly **One Plan Item for each selected requirement** or **One combined Plan Item for all selected requirements** and preview exact result item/source counts and total value. | CAN-AC-011 |
| CAN-FR-024 | Procurement Planner; formed items/allocations | Selected formation mode passes guards | Separate mode creates one item per entry. Combined mode creates one item with all allocations and requires a concise professional aggregation reason. | CAN-AC-011 |
| CAN-FR-025 | Procurement Planner; combined cross-department item | Selected entries cross departments | Permit only same-PE/FY sources satisfying every section 8.4 compatibility control. Assign mixed-department ownership to the PE-level Procurement Function and retain every source department visibly. | CAN-AC-011 |
| CAN-FR-026 | Procurement Planner/System; formation transaction | Form command carries current token/source set and idempotency key | Form items, allocations and Draft holds atomically and concurrency-safely. Holds prevent duplicate selection but do not change DPP or Need state. | CAN-AC-010, 011; CAN-SEC-007 |
| CAN-FR-027 | Procurement Planner; formation result | Formation succeeds | One created item opens its existing editor. Multiple separate results return to the Draft workbench with all results visible. Source selection is not repeated in the editor. | CAN-AC-011; later Stitch evidence |
| CAN-FR-028 | Actor; Draft workbench projection | Authorised workbench is read | Derive item count, total, Finance progress, validation blockers and commands from authoritative items, allocations and decisions. | CAN-SEC-002 |

### 10.4 Plan Item completion and Finance request

| ID | Actor / record | Preconditions and trigger | Required functional result | Primary acceptance |
| --- | --- | --- | --- | --- |
| CAN-FR-030 | Procurement Planner; Plan Item editor | Planner opens an existing Proposed Plan Item | Load exactly that item and every source allocation read-only. Never create a blank item, select sources or regroup allocations. | CAN-AC-011, 012 |
| CAN-FR-031 | Procurement Planner; item mutation | Save or Finance request carries item fields | Enforce the section 8 allow-list server-side; derive planned value, method basis, days to signature, completeness and source context. | CAN-AC-012, 013; CAN-SEC-006 |
| CAN-FR-032 | Procurement Planner; method/period/lotting values | Item is saved or submitted | Accept only active configured Open Tender, **Single year** and **No lots expected**. Omit unavailable values from the UI and reject them before persistence. | CAN-AC-012; negative build checks |
| CAN-FR-033 | Procurement Planner; seven planned milestones | Finance request or later Plan submission is evaluated | Require a complete chronological schedule coherent with FY, completion/required-by and configured legal-policy constraints. | CAN-AC-013, 017 |
| CAN-FR-034 | Procurement Planner; Plan Item Draft | Save draft passes field and concurrency validation | Persist only allowed fields and recalculate completeness; create no Finance task. | CAN-AC-013 |
| CAN-FR-035 | Procurement Planner; item/Finance task | Request Finance confirmation passes complete live validation | Atomically save allowed fields, reload and validate source/allocation/completeness, and create/reuse one protected Finance task. Roll back all task effects on failure. | CAN-AC-013; CAN-SEC-007 |
| CAN-FR-036 | Procurement Planner or authorised non-Finance viewer; item projection | Finance task is pending | Return neutral read-only item detail and waiting ownership/status; do not return the Budget Officer form or disabled decision controls. | CAN-AC-017; CAN-SEC-005 |

### 10.5 Finance reconciliation

| ID | Actor / record | Preconditions and trigger | Required functional result | Primary acceptance |
| --- | --- | --- | --- | --- |
| CAN-FR-040 | Assigned Budget Officer; Finance task | Actor lists, opens or decides a Finance task | Authorize exact Finance capability, PE/FY, funding scope and task assignment before any protected funding data is returned. | CAN-SEC-001, 005, 008 |
| CAN-FR-041 | Assigned Budget Officer; funding projection | Protected task access succeeds | Show every source allocation, Budget Line, approved/reserved/committed/available amount, required amount, after-confirmation balance and authoritative As-at time read-only. | CAN-AC-014, 015 |
| CAN-FR-042 | Assigned Budget Officer; Finance decision/reservations | Confirm command is current and every source has full live availability | Lock and reload every affected source, item, task and allocation; atomically create/resolve all reservations, create one immutable Finance decision and complete the task. | CAN-AC-014; CAN-SEC-007 |
| CAN-FR-043 | Assigned Budget Officer; shortfall projection | Any source has insufficient live availability | Omit Confirm, reject direct confirmation, return the exact current shortfall and create no partial reservation. | CAN-AC-015; CAN-SEC-006 |
| CAN-FR-044 | Assigned Budget Officer; task navigation | Open Budget & Funding is invoked | Preserve the same Finance task; enforce Budget authority independently; create no Planning or Finance mutation from navigation. | CAN-AC-015; CAN-SEC-005 |
| CAN-FR-045 | Assigned Budget Officer; Finance return | Return to planner is invoked with a valid reason | Create no reservation, record immutable return, reopen only planner-owned fields and create one linked task iteration on a later valid re-request. | CAN-AC-016 |
| CAN-FR-046 | System; Finance evidence freshness | Funding, source or value changes materially after confirmation | Mark prior Finance evidence **Stale** and require a new current confirmation before Plan submission. | CAN-AC-015, 017 |
| CAN-FR-047 | Budget Officer/System; boundary | Finance decision completes | Do not approve/activate a Plan Version, amend a Need, edit a Budget Line or create a Requisition or Tender. | CAN-AC-014; boundary tests |

### 10.6 Professional validation, AO certification and statutory approval

| ID | Actor / record | Preconditions and trigger | Required functional result | Primary acceptance |
| --- | --- | --- | --- | --- |
| CAN-FR-050 | Procurement Planner; Plan Version | Submit for professional validation is invoked | Require an effective change, complete items, current full Finance decisions, complete allocations, supported treatment and no blocking/stale issue. | CAN-AC-017 |
| CAN-FR-051 | Procurement Planner/System; submitted version/task | Submission passes all guards | Create one immutable version snapshot and one protected Head of Procurement Function task. Give non-task viewers neutral read-only detail only. | CAN-AC-017; CAN-SEC-005 |
| CAN-FR-052 | Head of Procurement Function; review task | Protected professional task opens | Present exact Plan/version, predecessor, change reason, submitter/time, item/source/funding summaries, validation results and decision history; permit no snapshot edit. | CAN-AC-018; CAN-SEC-005 |
| CAN-FR-053 | Head of Procurement Function; professional decision | Validate and submit command passes full revalidation and segregation | Create one immutable professional decision and route the exact version to AO certification; do not approve, activate or publish it. | CAN-AC-018; CAN-SEC-007 |
| CAN-FR-054 | Head of Procurement Function; return decision | Professional return is invoked | Require actionable reason, preserve Active predecessor/current evidence, complete the task and reopen only the governed correction path. | CAN-AC-018 |
| CAN-FR-055 | Accounting Officer; certification task | Exact professionally validated version is authorised and current | Present exact version, accountability statement, Budget/funding evidence, output preview and history. **Certify and submit** creates immutable certification and onward submission. | CAN-AC-019; CAN-SEC-005 |
| CAN-FR-056 | Accounting Officer; return decision | AO return is invoked | Require actionable reason and preserve the exact submitted snapshot; make no silent edit or approval. | CAN-AC-019 |
| CAN-FR-057 | Configured statutory authority; approval task | Exact AO-certified version is routed to the effective authority | Identify the configured authority and permit only **Approve Annual Procurement Plan** or **Return for correction**. | CAN-AC-020; CAN-SEC-005 |
| CAN-FR-058 | Configured statutory authority; approval decision | Approval passes route, assignment, segregation and current-version guards | Create an immutable decision and set **Approved - publication pending**. Do not activate or publish the version. | CAN-AC-020; CAN-SEC-007 |

### 10.7 Publication, activation and Requisition eligibility

| ID | Actor / record | Preconditions and trigger | Required functional result | Primary acceptance |
| --- | --- | --- | --- | --- |
| CAN-FR-060 | Publication Operator; Plan Publication | Production hold is cleared and publish/retry is invoked | Serialize and transmit only the exact approved payload through the configured adapter; record destination, configuration version, request, payload hash, attempt, response and timestamps. | CAN-AC-021 |
| CAN-FR-061 | Publication adapter/System; Plan Version | Publication response is received or retried | Activate only after authoritative acknowledgement of the exact approved payload. Failed/indeterminate attempts remain retryable and create no new approval. | CAN-AC-021; CAN-SEC-007 |
| CAN-FR-062 | System; predecessor/successor versions | Exact successor payload is acknowledged | Atomically make the successor the sole Active version, supersede the predecessor and apply approved additions/removals/allocations exactly once. | CAN-AC-022; CAN-SEC-007 |
| CAN-FR-063 | Authorised reader; Approved/Active Plan projection | Plan detail is opened | Return read-only version, approval/publication evidence, item baseline, Finance coverage, Requisition eligibility/drawdown and later downstream status as neutral projections. | CAN-AC-021 to 024; CAN-SEC-001, 008 |
| CAN-FR-064 | Requisitions consumer; eligibility projection | Eligibility is requested As-at a current time | Expose only Active, unblocked items with remaining quantity/value and exact Plan/version/item/source lineage and As-at time. | CAN-AC-023, 024 |
| CAN-FR-065 | Requisitions producer/System; drawdown reference | Authoritative Requisition drawdown is received | Record the authoritative reference, reconcile remaining quantity/value and prevent overdraw; never create the Requisition or Tender. | CAN-AC-024 |

### 10.8 Amendments, removals and monitoring

| ID | Actor / record | Preconditions and trigger | Required functional result | Primary acceptance |
| --- | --- | --- | --- | --- |
| CAN-FR-070 | Procurement Planner/System; Draft successor | Accepted departmental amendment, new accepted DPP source or eligible removal is acted on | Create/reuse one Draft successor only through the guarded command; opening a surface creates nothing. | CAN-AC-009, 022; CAN-SEC-007 |
| CAN-FR-071 | Procurement Planner; draft-only item | Remove from Draft is requested with reason | Retain history, cancel open tasks and reverse Draft-stage reservations/holds through governed services. | CAN-AC-025 |
| CAN-FR-072 | Procurement Planner; Active item | Whole-item removal is proposed | Permit only when no Requisition drawdown, Tender handoff, commitment or downstream execution exists. Keep the item operational until successor activation. | CAN-AC-025 |
| CAN-FR-073 | Procurement Planner; combined item | Removal is requested for an item with multiple sources | Permit whole-item removal only; do not offer or accept source-level detachment. | CAN-AC-025 |
| CAN-FR-074 | Procurement Planner; removal-only successor | Eligible whole-item removal is the only change | Require one item-level reason as the update reason and do not require new Finance confirmation. | CAN-AC-025 |
| CAN-FR-075 | Procurement Planner; no-effective-change Draft successor | Cancel update is invoked with reason | Cancel the successor, release Draft holds/effects and leave the Active baseline unchanged. | CAN-AC-022; CAN-SEC-007 |
| CAN-FR-076 | Monitoring Officer/System; monitoring evidence | Actual milestone/progress or correction is submitted | Append actual and variance evidence. A correction appends a replacement/correction link and never overwrites planned dates or the downstream source. | CAN-AC-026 |

### 10.9 Logical query and command inventory

These names are stable logical business contracts. The Implementation Pack may assign transport-specific routes or handlers but may not merge named decisions, bypass their controls or expose an equivalent Planning command for Requisition/Tender creation.

| Logical contract | Minimum functional input | Successful result | Non-bypassable control |
| --- | --- | --- | --- |
| ResolvePlanningContexts | Authenticated actor; evaluation time | Zero/one/many authorised declared contexts | Effective assignments only; no client PE/role grant |
| GetPlanningWorkspace | Authorised context ID | Coherent summary, action queue, waiting queue and commands | Same authorization predicate for counts, rows, links and actions |
| ProjectAcceptedNeed | Trusted event ID; Need/version/hash | Existing or one DPP root/entry projection | Source eligibility, uniqueness, idempotency and no Annual Plan creation |
| SubmitDepartmentalPlan | DPP ID; expected version/source set; idempotency key | Immutable submission and decision | HoD/delegation, window, exact coverage, current sources and AO recipient |
| ReturnDepartmentalPlan | Submission ID; structured issues; expected version; idempotency key | Returned decision and immutable issue set | Assigned non-self validator and actionable issue contract |
| AcceptDepartmentalPlan | Submission ID; classifications; expected version/source set; idempotency key | Terminal validation and Accepted DPP Projection | Current sources, complete classification, segregation and no blocker |
| ReopenDepartmentalPlan | Accepted submission; changed source; reason; expected version | Returned state and preserved accepted evidence | No consolidation consumption |
| BeginConsolidation | Context; selected accepted DPP sources; expected source set; idempotency key | One Annual Plan root and Draft Version, existing or created | Exact capability, eligibility, uniqueness and protected concurrency |
| FormPlanItems | Plan/Draft; source entry IDs; mode; combined reason where required; token/key | Proposed items, allocations and Draft holds | Server reload, compatibility, atomicity and idempotency |
| SavePlanItemDraft | Item/Draft; allow-listed fields; token/key | Updated Draft and completeness result | Mutation allow-list and source immutability |
| RequestFinanceConfirmation | Item/Draft; allow-listed fields; token/key | One current Finance task iteration | Item/source completeness and atomic save/task boundary |
| GetFinanceTask | Task ID | Protected current funding projection and available commands | Assignment, PE/FY and funding scope before serialization |
| ConfirmFunding | Task ID; token; optional note; key | All reservations, one decision and completed task | Locked live funding and full all-source atomicity |
| ReturnFromFinance | Task ID; token; reason; key | Return decision, completed iteration and reopened planner fields | No reservation or Budget mutation |
| SubmitProfessionalValidation | Plan Version; change reason; token/key | Immutable submitted snapshot and protected task | Complete effective change and current Finance/source controls |
| ProfessionallyValidate | Review task; token; optional note; key | Professional decision and Awaiting AO certification | Task authority, segregation and full revalidation |
| CertifyAndSubmit | AO task; token; optional certification note; key | AO certification and Awaiting statutory approval | AO authority and exact immutable version |
| ApproveAnnualPlan | Approval task; token; optional note; key | Approval and publication-pending state | Configured route/assignment and maker-checker |
| PublishAnnualPlan | Approved version; destination configuration; token/key | Attempt and acknowledgement/failure; activation only on acknowledgement | Exact approved-payload hash and production integration gate |
| ProposeOrApplyRemoval | Plan/item; reason; token/key | Immediate Draft exclusion or proposed successor removal | Whole-item eligibility and downstream recheck |
| CancelPlanUpdate | Draft successor; reason; token/key | Cancelled successor and released Draft effects | No effect on Active predecessor |
| GetRequisitionEligibility | Active Plan Item; As-at | Remaining quantity/value and lineage, or exact blocker | No read mutation; current Active/funding/drawdown checks |
| RecordMonitoringEvidence | Active/superseded item; milestone; evidence; token/key | Append-only actual/variance entry | Monitoring capability and immutable baseline |

## 11. Source change, freshness and correction requirements

| Current condition | Authoritative change | Required Planning response | Prohibited response |
| --- | --- | --- | --- |
| DPP Draft or Returned and not consumed | New accepted Need version | Refresh the current projection, expose a changed-source summary and require a new HoD certification | Silent acceptance, local correction or preservation of an obsolete current projection |
| DPP Submitted | New accepted Need version | Keep the submission immutable, mark source stale, block acceptance and require authorised return | Rewrite snapshot or auto-return |
| DPP Accepted and not consumed | New accepted Need version | Preserve accepted evidence, set current eligibility false and permit assigned-validator reopen | Automatic reopen or continued consolidation eligibility |
| Accepted DPP submission consumed | New accepted Need version | Create a DPP amendment projection with predecessor and change reason, eligible only for an Annual Plan successor | Reopen consumed submission or rewrite Active Plan evidence |
| DPP Withdrawn | Event replay or new source version | Preserve history and remain withdrawn | Reactivation by replay |
| Finance confirmed | Material source, value or live funding change | Mark evidence Stale and require a new Finance confirmation | Treat stale evidence as current |
| Version submitted for a governance decision | Upstream or funding change | Preserve exact submitted snapshot, surface blockers/current projection and use the governed return/correction path | Silent snapshot edit or automatic decision |
| Active baseline | Monitoring or downstream change | Append neutral actual/variance/drawdown projection | Rewrite approved planned values |

Trusted events may be duplicated, replayed or arrive out of order. Reprocessing must be idempotent and may not produce a different business outcome or silently repair immutable evidence.

### 11.1 Canonical event effects

| Event | Authoritative producer | Planning effect |
| --- | --- | --- |
| DepartmentalNeedAccepted.v1 | Departmental Needs | Idempotent DPP projection or amendment-impact evaluation |
| DepartmentalNeedSuperseded.v1 | Departmental Needs | Stale-source blocker; no snapshot rewrite or automatic business return |
| BudgetAllocationChanged.v1 | Budget & Funding | Re-evaluate open Finance-task and evidence freshness; never auto-confirm |
| BudgetReservationChanged.v1 | Budget & Funding | Refresh availability/freshness and monitoring projection |
| AnnualPlanPublicationAcknowledged.v1 | Publication adapter | Verify version, payload and attempt, then activate atomically |
| AnnualPlanPublicationFailed.v1 | Publication adapter | Persist failure evidence; remain approved-pending/failed and retryable |
| ProcurementRequisitionAuthorised.v1 | Procurement Requisitions | Record read-only drawdown reference and recalculate remaining eligibility |
| DownstreamMilestoneChanged.v1 | Requisitions/Tender/Contract owner | Refresh neutral actual/variance projection; never rewrite baseline |

## 12. Business-surface obligations for the later Stitch Contract

This section identifies the admitted actor/state surfaces and functional commands. It is not a Stitch prompt and deliberately contains no geometry, spacing, component selector, pixel, screenshot or responsive-layout instruction. The later Stitch Contract must bind every listed variant to the canonical UI preservation and anti-invention controls and must provide a complete screen-specific visible contract.

| Surface family | Canonical screen IDs | Functional state/actor obligation | Commands that may be represented |
| --- | --- | --- | --- |
| Planning entry and workspace | PLN-UI-00; PLN-UI-01A to 01G; PLN-UI-SUP-01 | Separate no-context, no-root, Draft, Active-plus-successor, Finance-owned, professional/AO-owned, approval/publication-owned, Active-no-work and read-only support projections | Begin consolidation, view active/update, open exact assigned task, publish/retry, view evidence; only where current authorization permits |
| DPP preparation and submission | P3-UI-DPP-01; 02; 02A | Separate preparer, HoD-ready and confirmation states; source facts remain read-only; exact recipient/window/readiness and fixed attestation are business data | Submit departmental plan; cancel confirmation without mutation |
| DPP validation and neutral waiting | P3-UI-DPP-03A to 03D; 04 | Separate missing-classification, ready, structured-return, acceptance-confirmation and department-waiting states | Governed classification; return; accept; cancel without mutation |
| DPP correction, accepted and amendment | P3-UI-DPP-05A, 05B, 06, 06A, 06B, 07, 09 | Separate upstream correction outstanding, corrected/resubmittable, accepted-current, stale-before-consumption, changed-after-consumption, withdrawn and amendment variants | Open owning source; resubmit; eligible validator reopen; no local source edit/reactivation |
| Consolidation and workbench | PLN-UI-02 to 05B | Separate begin confirmation, empty Draft, source selection, populated/successor Draft, removal confirmation and no-effective-change cancellation | Begin consolidation; add accepted sources; choose separate/combined; view/edit item; eligible removal; submit ready version; cancel eligible update |
| Plan Item | PLN-UI-06 | One existing Proposed item with immutable source allocations, allow-listed professional treatment and derived values | Back; Save draft; Request Finance confirmation |
| Finance | PLN-UI-07; 07A-1; 07A-2; 07B | Separate sufficient, insufficient, return-confirmation and neutral planner-waiting states; protected funding content only for assigned Finance actor | Confirm funding only when full availability; return; open Budget & Funding; close/cancel without mutation |
| Professional validation | PLN-UI-08; 08R | Exact Head of Procurement Function task and separate return confirmation; no final-approval semantics | Validate and submit to Accounting Officer; Return to planner |
| AO certification | PLN-UI-08A; 08AR | Exact Accounting Officer task and separate return confirmation | Certify and submit; Return for correction |
| Statutory approval | PLN-UI-08B; 08BR | Exact configured authority task and separate return confirmation; certified content immutable | Approve Annual Procurement Plan; Return for correction |
| Publication | PLN-UI-08C; 08CA | Separate publication-pending/failed operator task and acknowledged result; exact payload immutable | Publish or retry; View evidence; View active plan after acknowledgement |
| Active Plan and downstream | PLN-UI-09; 09A | Read-only Active baseline, successor notice, exact Requisition eligibility/drawdown and neutral later downstream references | Add accepted change source; eligible whole-item removal; view item/Requisition; no create Requisition/Tender |
| Monitoring and evidence | PLN-UI-09M; PLN-UI-EVD-01 | Append-only monitoring entry/history and scope-limited immutable evidence | Record actual milestone where authorised; read evidence |

Functional UI controls are a projection of current server-authorized commands. Hiding, disabling or showing a control is never authorization. An unauthorized protected-task surface must not be serialized and must not be represented as a disabled task form. Opening, cancelling or navigating a surface is mutation-free unless the user confirms a named command.

The existing KenTender Planning shell and constructed composition are reused by default, but the later Stitch Contract must record **Keep**, **Correct** or **Retire** for each implemented component. Mandatory semantic corrections include accepted Need/DPP lineage, **Begin consolidation**, **ready for requisitioning**, separate governance stages, separate publication-pending and Active states, Requisition as the first downstream consumer, removal of unsupported method/period/lotting controls, readable source facts and omission of unauthorized controls.

## 13. Stable error and outcome contract

A failed validation or guard shall return the stable code applicable to the authoritative failure, sufficient lawful remediation guidance and a support/correlation reference where required. It shall not perform a partial business effect, disclose another scope or silently choose a different path.

| Code | Trigger and required response |
| --- | --- |
| PLN_NO_AUTHORISED_CONTEXT | No effective Planning context. Return no PE/FY, counts or Plan data. |
| PLN_CONTEXT_SCOPE_DENIED | Supplied context is unauthorized. Deny without confirming existence. |
| PLN_CONFIGURATION_INCOMPLETE | Required configuration is absent/invalid. Return safe unavailable state and stable support reference. |
| DPP_WINDOW_NOT_OPEN | DPP submission window is not open. Block submit. |
| DPP_SOURCE_NOT_ACCEPTED | Source is not currently Accepted for planning. Direct correction to Departmental Needs. |
| DPP_SOURCE_VERSION_STALE | A newer accepted source version exists. Preserve snapshot and use governed correction. |
| DPP_SOURCE_CONTEXT_MISMATCH | Source PE/FY/department does not match. Fail closed without cross-scope disclosure. |
| DPP_SOURCE_COVERAGE_MISMATCH | Eligible source is omitted, duplicated or not fully represented. Block submission. |
| DPP_REQUIRED_BY_OUTSIDE_FY | Required-by falls outside the supported FY. Correct upstream; no multi-year fallback. |
| DPP_BUDGET_REFERENCE_STALE | Required Budget/funding reference is absent or inactive. Correct the owning source. |
| DPP_REQUIREMENT_TYPE_MISSING | At least one entry lacks governed classification. Block acceptance. |
| DPP_SEGREGATION_DENIED | Actor/decision history violates DPP separation. Deny and audit. |
| DPP_ALREADY_CONSUMED | Accepted submission is consumed. Use DPP amendment and Annual Plan successor. |
| PLN_NO_ELIGIBLE_DPP_SOURCE | No current accepted source is available. Create no Annual Plan. |
| PLN_SOURCE_ALREADY_ALLOCATED | Source is held or effectively allocated in another current use. Refresh selection. |
| PLN_COMBINATION_INCOMPATIBLE | Combined formation fails one or more compatibility controls. Permit valid separate formation. |
| PLN_STALE_COMMAND | Record version, task iteration or source-set hash is stale. Return current safe projection; do not replay silently. |
| PLN_ITEM_INCOMPLETE | Required treatment or schedule is incomplete. Return exact field issues. |
| PROCUREMENT_METHOD_NOT_CONFIGURED | Return exactly: **The selected procurement method is not enabled in the current catalogue.** |
| PLANNING_MULTI_YEAR_NOT_AVAILABLE_MVP1 | Return exactly: **Multi-year Plan Items are not available in this release.** |
| PLANNING_LOTS_NOT_AVAILABLE_MVP1 | Return exactly: **Plan Items requiring lots are not available in this release.** |
| FINANCE_TASK_ACCESS_DENIED | Actor lacks protected Finance authority. Return no protected funding data. |
| FINANCE_INSUFFICIENT_FUNDING | Full funding is unavailable. Return exact shortfall and create no partial reservation. |
| FINANCE_CONFIRMATION_STALE | Funding evidence changed. Require a new current Finance confirmation. |
| PLAN_VALIDATION_BLOCKED | Version has current blockers. Identify affected records and remediation owners lawfully. |
| PLAN_SEGREGATION_DENIED | Preparation/decision history prohibits this decision. Deny and audit. |
| PLAN_APPROVAL_ROUTE_INVALID | Effective approving authority/assignment is missing or expired. Deny. |
| PLAN_PUBLICATION_CONFIGURATION_HELD | Production publication authority/integration is not approved. Do not transmit. |
| PLAN_PUBLICATION_PAYLOAD_MISMATCH | Serialized payload differs from the approved version. Block publication and activation. |
| PLAN_PUBLICATION_NOT_ACKNOWLEDGED | Acknowledgement is absent or indeterminate. Remain pending/failed and permit governed retry. |
| PLAN_ITEM_REMOVAL_BLOCKED_DOWNSTREAM | Downstream drawdown, handoff, commitment or execution exists. Block removal without partial effects. |
| PLAN_REQUISITION_NOT_ELIGIBLE | Item/version/funding/remaining amount is ineligible. Return exact lawful blockers. |
| PLN_SUPPORT_READ_ONLY | Support actor attempted a business command. Deny and audit. |

## 14. Security, privacy, transaction and evidence requirements

1. List, count, search, workspace, detail, evidence, notification, route and command evaluation shall use the same server policy inputs.
2. Unauthorized access shall return the minimum safe result and no signal that another PE/FY, Plan, task, source or identifier exists.
3. Protected Finance, professional, AO, approval and publication task content shall be loaded only after task-specific authorization succeeds.
4. Support access shall be visibly labelled, read-only and purpose-audited where required; it cannot be converted into a business assignment.
5. Every state-changing command shall be atomic, idempotent and concurrency-protected. A stale or losing command receives a stable outcome and creates no duplicate evidence.
6. Immutable submissions, snapshots, decisions, publication evidence and monitoring history shall be append-only. Correction uses a predecessor/successor, task iteration, reversal service or correction link.
7. Audit evidence shall capture actor, effective assignment/delegation, capability, context, object, command, state, expected/current version, source-set hash, timestamp, idempotency key, outcome and correlation reference. Denied privileged attempts are recorded without sensitive or cross-scope payloads.
8. Stable identifiers shall link Need event, DPP projection/submission/validation, Plan formation/allocation, Finance reservation/decision, professional validation, AO certification, statutory approval, publication, activation, Requisition drawdown and monitoring.
9. Direct client state, approval, allocation, funding, ownership and source mutation shall be rejected as a whole.
10. The build shall contain no legacy Demand/DMD or direct Demand-to-Plan behavior, no legacy Planning Home/contribution/release-package/direct Plan-to-Tender dependency, no compatibility path, no automatic Plan creation on read, no automatic business decision from an event, no wildcard administrator authority and no unsupported hidden value.

## 15. Functional acceptance contract

Each acceptance test must assert the business result and the absence of unauthorized, duplicate or partial side effects. A passing visible screen without the corresponding server result is insufficient; a passing command without the correct scoped projection and evidence is also insufficient.

| ID | Given / when | Required observable result | Functional coverage |
| --- | --- | --- | --- |
| CAN-AC-001 | Actor has zero, one or many authorised contexts | Exact authorised selector behavior; no authority expansion or data disclosure | CAN-FR-001, 002, 007 |
| CAN-AC-002 | Workspace opens before an Annual Plan root exists | No record is created; eligible DPP work is accurate | CAN-FR-004, 005 |
| CAN-AC-003 | Accepted Need projection is replayed or concurrent | One DPP root and one entry; stable idempotent result | CAN-FR-010 |
| CAN-AC-004 | DPP submission omits, duplicates or partially includes an eligible Need | Exact coverage blocker; no submission snapshot | CAN-FR-011, 013 |
| CAN-AC-005 | Effective HoD submits within the correct window with current sources | Immutable payload, recipient, authority, attestation and source evidence | CAN-FR-013, 014 |
| CAN-AC-006 | Wrong HoD, expired delegate or submitter attempts validation | Server denial and audit; no protected cross-scope payload | CAN-FR-016 |
| CAN-AC-007 | Validator returns with structured issues and source is later corrected | Immutable return; upstream correction; new predecessor-linked submission; V1 unchanged | CAN-FR-014, 015, 018 |
| CAN-AC-008 | Assigned non-self validator accepts a current fully classified submission | Terminal validation and consolidation eligibility; no Annual Plan approval | CAN-FR-016, 017 |
| CAN-AC-009 | Authoritative source changes before or after consolidation consumption | Pre-consumption governed reopen only; post-consumption amendment path; no evidence rewrite | CAN-FR-018, 070 |
| CAN-AC-010 | Two planners invoke Begin consolidation concurrently | One Annual Plan root and Draft Version; stable result | CAN-FR-020, 026 |
| CAN-AC-011 | One/many entries form separate or combined items | Exact item/allocation/hold counts, compatibility enforcement and no source loss | CAN-FR-021 to 027 |
| CAN-AC-012 | Client mutates source-owned or unknown fields | Stable whole-payload rejection; no silent ignore or source change | CAN-FR-012, 030 to 032 |
| CAN-AC-013 | Save draft is compared with Request Finance confirmation | Save creates no task; valid request creates exactly one protected task | CAN-FR-031 to 035 |
| CAN-AC-014 | Every source has sufficient funding | Full atomic reservations, one Finance decision and task completion; no Plan approval | CAN-FR-041, 042, 047 |
| CAN-AC-015 | Any source is short or funding changes concurrently | Exact shortfall; no Confirm control, partial reservation or negative availability | CAN-FR-041 to 044, 046 |
| CAN-AC-016 | Finance returns, planner corrects and re-requests | Required reason; no reservation; one linked new iteration and retained history | CAN-FR-045 |
| CAN-AC-017 | Complete effective-change Plan is submitted for professional validation | Immutable submitted version and one protected task; neutral view for non-task users | CAN-FR-033, 036, 050, 051 |
| CAN-AC-018 | Head of Procurement Function validates or returns | Separate immutable professional decision; no approval/activation; governed return evidence | CAN-FR-052 to 054 |
| CAN-AC-019 | Accounting Officer certifies or returns | Immutable AO decision and onward route; no silent edit or automatic approval | CAN-FR-055, 056 |
| CAN-AC-020 | Configured authority approves or returns | Immutable statutory decision; publication-pending state; no Active state | CAN-FR-057, 058 |
| CAN-AC-021 | Publication payload mismatches, fails or is acknowledged | Mismatch blocked; failure retryable; exact acknowledgement activates once | CAN-FR-060, 061, 063 |
| CAN-AC-022 | Acknowledged successor activates | One Active successor; predecessor Superseded; effects applied once | CAN-FR-062, 070, 075 |
| CAN-AC-023 | Active item has remaining eligibility | Exact eligibility projection exists; Planning creates no Requisition/Tender | CAN-FR-063, 064 |
| CAN-AC-024 | Requisition drawdown consumes part or all | Remaining quantity/value reconciles; overdraw denied | CAN-FR-063 to 065 |
| CAN-AC-025 | Active whole-item removal is proposed before/after downstream use | Allowed only before downstream execution; invalid direct command has no partial effect | CAN-FR-071 to 074 |
| CAN-AC-026 | Monitoring evidence is recorded and corrected | Append-only actual/variance and correction history; baseline unchanged | CAN-FR-076 |

## 16. Negative-security and isolation acceptance

| ID | Attack or adverse condition | Required result | Principal controls |
| --- | --- | --- | --- |
| CAN-SEC-001 | User supplies another PE/FY context or known Plan/task ID | Denied before data serialization; no existence signal | Common authorization predicate; protected-task pre-authorization |
| CAN-SEC-002 | Counts, queues, search, detail and commands are compared for one actor | Identical scope and reconciled counts | One policy input set; derived workspace projection |
| CAN-SEC-003 | Assignment/delegation expires between read and command | Command denied after server revalidation; safe current projection | Live authority and delegation check at execution |
| CAN-SEC-004 | System Administrator opens support view then calls a business command | Labelled read-only data where authorised; command denied and audited | No wildcard administrator authority |
| CAN-SEC-005 | Planner, HoD or viewer directly opens Finance/professional/AO/approval/publication task | No protected payload or decision form is returned | Task-specific authorization before serialization |
| CAN-SEC-006 | Client sends direct state, approval, allocation, funding or source mutation | Payload rejected as a whole; no partial state | Mutation allow-list and service-owned transitions |
| CAN-SEC-007 | Confirm/return, approve/return, publication retry or successor-creation race | One terminal effect; stale loser receives stable outcome; no duplicate evidence | Transactions, locks, uniqueness, tokens and idempotency |
| CAN-SEC-008 | MOH, NSSF and CGK isolation suite traverses rows/counts/details/commands | No cross-PE data, action or existence signal | Exact PE/FY scope across every projection and command |

## 17. Required command and evidence test matrix

The Implementation Pack may choose technical test organization but must prove every named command below through positive, negative, authorization, stale-version, duplicate-delivery and rollback paths where applicable.

| Command or service | Success evidence | Mandatory adverse evidence |
| --- | --- | --- |
| Resolve Planning contexts / Get workspace | Exact authorised projection and reconciled counts | Zero context, unauthorized supplied context, expired assignment, configuration unavailable, no read mutation |
| Project accepted Need | One DPP root/entry and source version/hash lineage | Duplicate, concurrent, out-of-order, ineligible/cross-context and replay cases |
| Submit / Resubmit DPP | Immutable submission, actor/delegation, recipient, window, attestation and source-set hashes | Coverage mismatch, stale source, closed window, wrong HoD, stale token, duplicate delivery |
| Return / Accept / Reopen DPP | Immutable structured issue or terminal acceptance/reopen decision | Self-validation, incomplete classification, stale source, already consumed, wrong task/scope |
| Begin consolidation | One root/Draft and selected accepted-source lineage | No eligible source, concurrent creation, wrong PE/FY, read-only opening |
| Form Plan Items | Exact item/allocation/hold arithmetic and deterministic result routing | Already held/allocated source, incompatible combination, stale source set, duplicate/concurrent command |
| Save Plan Item draft | Only allow-listed fields persist and completeness recalculates | Source/unknown/direct-state field, unsupported value, stale version, blank item creation |
| Request Finance confirmation | Atomic field save and one current protected task | Incomplete schedule/treatment, stale source, task creation failure, duplicate request |
| Get / Confirm / Return Finance task | Protected projection; atomic all-source reservation or reasoned no-reservation return | Unassigned actor, cross-funding scope, any shortfall, concurrent change, confirm/return race, partial reservation |
| Submit professional validation | Immutable exact version and one protected task | No effective change, stale Finance, incomplete item/allocation, unsupported treatment, duplicate task |
| Professional validate / return | Immutable named professional decision and exact route/outcome | Material preparer, wrong actor, stale task, validate/return race, snapshot mutation |
| AO certify / return | Immutable certification or reasoned return | Wrong/expired AO, stale version, missing professional/funding evidence, concurrent decision |
| Statutory approve / return | Immutable configured-authority decision and publication-pending outcome | Invalid route, maker-checker failure, edit attempt, approve/return race, automatic activation |
| Publish / retry / activate | Deterministic exact payload, hashes, attempt/acknowledgement and one-active transition | Open production hold, payload mismatch, failed/indeterminate response, duplicate acknowledgement/retry, two-active race |
| Propose/apply removal / cancel update | Preserved history, governed reversals and unchanged Active predecessor until activation | Downstream use, partial combined-source removal, stale eligibility, partial reversal |
| Get Requisition eligibility / record drawdown | Exact remaining amount and lineage | Inactive/stale/blocked item, overdraw, cross-context access, Planning-side Requisition creation |
| Record monitoring evidence | Append-only actual/variance/correction chain | Baseline edit, downstream-source mutation, unauthorized actor, stale correction link |

## 18. Traceability and completeness controls

### 18.1 Canonical requirement coverage

This derivative contains exactly the 63 canonical functional requirement IDs admitted by PLN-CAN-001 v0.1:

- CAN-FR-001 to 008;
- CAN-FR-010 to 018;
- CAN-FR-020 to 028;
- CAN-FR-030 to 036;
- CAN-FR-040 to 047;
- CAN-FR-050 to 058;
- CAN-FR-060 to 065; and
- CAN-FR-070 to 076.

No additional product-behavior requirement ID is introduced. Sections 4 to 9 and 11 to 17 restate canonical lifecycle, actor, record, state, validation, surface, error, security and acceptance controls needed to make those requirements testable.

### 18.2 Required downstream traceability

Each later derivative and implementation traceability report shall map, at minimum:

`canonical fingerprint -> CAN-FR requirement -> actor/capability -> record and owner -> pre-state -> command/query -> guards and validation -> transaction/evidence -> post-state/outcome -> stable error -> business surface -> seed scenario -> acceptance/security test`.

No downstream row may leave a required link blank or point to a historical Planning document. A fingerprint mismatch, orphan requirement, unresolved command, untested state transition, missing protected-task denial or missing business-surface variant blocks release.

### 18.3 Functional approval checklist

Approval of PLN-FR-001 requires confirmation that:

1. all 63 `CAN-FR-*`, 26 `CAN-AC-*` and eight `CAN-SEC-*` identifiers are present once in their controlling tables and are traceable;
2. the four governance stages and publication acknowledgement are distinct;
3. no record owner or mutation authority is duplicated;
4. every state-changing command has actor, guards, atomic outcome, idempotency/concurrency and error behavior;
5. no source correction, approval, activation or downstream transaction can occur silently;
6. screen geometry, seed instances and technical implementation decisions have not leaked into this derivative; and
7. open authority assumptions and production holds remain explicit.

## 19. Authority limitation, assumptions and release holds

PLN-CAN-001 adopts the historically regulation-derived departmental-planning, Annual Plan output and publication workflow as bounded KenTender MVP-1 product policy. This derivative does not describe those regulation-dependent rules as settled current law and does not label the Annual Procurement Plan output as a current prescribed statutory form.

| Control | Functional consequence |
| --- | --- |
| LEG-AUTH-001 | No requirement, screen or implementation may assert settled current subsidiary-law status or enable production publication until legal/policy closure is recorded. |
| ASMP-001 | The DPP/HoD/Procurement validation route is implemented as approved product policy pending formal current-route confirmation. |
| ASMP-002 | Final approval is always resolved from the approved PE-type authority catalogue; AO is not assumed to be final approver. |
| ASMP-003 | Publication uses the exact approved-payload and acknowledgement model, but production adapter execution remains held pending destination/protocol/legal confirmation. |
| ASMP-004 | Need intake must use the exact approved upstream interface reflected in PLN-CAN-001; interface mismatch blocks implementation rather than triggering local reinterpretation. |

## 20. MVP-1 exclusions

The following are not admitted by this derivative: multi-year Plan Items; lots; unconfigured methods; partial Need inclusion; Planning quantity override; partial Finance confirmation; source-level detachment from combined items; direct Procurement Requisition or Tender creation; supplier-facing bidding; advanced strategy/performance dashboards; Approved Plan export; interactive historical-version detail; production publication before hold closure; legacy migration or compatibility; generic approval engines; and automatic business decisions from source events.

A later desire for any excluded or ambiguous behavior must be raised against PLN-CAN-001 and approved in a new canonical version before this derivative, the Stitch Contract, Seed Contract, Implementation Pack or code changes.

## 21. Approval and next controlled derivative

| Decision item | Value |
| --- | --- |
| Product-owner decision | Approved |
| Decision date | 21 August 2026 |
| Approved version | 0.1 |
| Canonical fingerprint verified | Yes — `sha256:2e8e8790309b4d738ab80934f609111753f94766aab8e4bf2d3313146289e879` |
| Conditions or recorded exceptions | None beyond the authority assumptions and production holds already stated in sections 1 and 19 |

Approval of PLN-FR-001 confirms functional completeness against PLN-CAN-001 v0.1 only. It does not approve screen composition, seed fixtures, technical implementation or production publication. After approval, the next controlled derivative is the Stitch Contract, produced against the same canonical fingerprint and this approved functional baseline.
