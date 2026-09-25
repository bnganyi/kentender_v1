Procurement Proceedings Module

## Functional Design Document

**1\. Purpose**

The Procurement Proceedings module provides a formal digital mechanism for recording, managing, and governing official meetings, deliberations, recommendations, resolutions, and follow-up actions that occur throughout the procurement and contract management lifecycle.

The module exists to ensure that key procurement interactions are:

- formally documented,
- legally defensible,
- auditable,
- traceable to procurement decisions,
- and linked to downstream financial and contractual actions.

This is necessary because the requirements explicitly call for formal recording of site meetings, meeting minutes, milestone completion minutes, inspection minutes, committee decisions, dispute stages, stop-work advice, and monthly monitoring reports, along with a complete audit trail for contract activities.

**2\. Objectives**

The module shall:

- provide a structured system for official procurement meetings and committee sittings,
- record attendance and quorum,
- capture agenda items and linked procurement references,
- record discussions and recommendations,
- generate formal resolutions,
- assign and track action items,
- preserve supporting evidence,
- support signed minutes and signed decisions,
- and provide traceable links to procurement, contract, finance, inspection, dispute, and termination workflows.

**3\. Scope**

The Procurement Proceedings module applies across the procurement lifecycle, especially where formal human deliberation influences contractual, financial, technical, or legal outcomes.

**In scope**

- Tender evaluation meetings
- Contract Implementation Team meetings
- Site meetings
- Inspection and Acceptance sittings
- Variation review sessions
- Claims review meetings
- Dispute sessions
- Termination review sessions
- Monthly contract monitoring review meetings

**Out of scope**

- General corporate calendar scheduling
- Informal chats or ad hoc discussions
- Generic enterprise board-management outside procurement
- Full document-signing platform by itself
- Generic task/project collaboration unrelated to procurement governance

**4\. Business Need**

The procurement lifecycle involves multiple committees and decision-making bodies whose actions have legal and financial consequences.

Examples include:

- a CIT recommending milestone completion,
- an inspection committee rejecting a delivery,
- a proceeding recommending a variation,
- a dispute meeting recommending stop-work,
- a termination review advising contract termination,
- a monitoring review escalating risks.

Without a formal proceedings module, these decisions risk being scattered across:

- email,
- attachments,
- chat,
- comments,
- or undocumented oral meetings.

That would weaken the platform's compliance, auditability, and legal defensibility.

**5\. Key Users**

The module supports the following users, depending on proceeding type:

- Head of Procurement
- Accounting Officer
- Contract Implementation Team members
- Inspection and Acceptance Committee members
- Head of User Department
- Head of Finance
- Supplier representatives
- Legal advisors
- Technical specialists
- System administrators

These align with the role structures defined in the contract management requirements.

**6\. Core Concepts**

**6.1 Proceeding**

A Proceeding is the formal record of one official procurement session or sitting.

It represents:

- one meeting,
- one inspection sitting,
- one review session,
- or one formal deliberative event.

**6.2 Agenda Item**

An Agenda Item is an issue or subject discussed within a proceeding.

It may be linked to a procurement artifact such as:

- Tender
- Contract
- Task / milestone
- Quality Inspection
- Acceptance Certificate
- Purchase Invoice
- Retention Release Request
- Contract Variation
- Claim
- Dispute Case
- Termination Record
- Monitoring Report

**6.3 Resolution**

A Resolution is the formal outcome or decision arising from an agenda item.

**6.4 Action Item**

An Action Item is a follow-up obligation assigned to a user or role after a proceeding.

**6.5 Evidence**

Evidence captures documents, reports, minutes attachments, legal opinions, images, technical reports, and other supporting records used during deliberation.

**6.6 Signature**

Signature records provide evidence that minutes, attendance, or resolutions were acknowledged, approved, or signed.

**7\. Functional Areas**

**7.1 Proceeding Management**

The system shall allow authorized users to create and manage official proceedings.

Each proceeding shall capture:

- proceeding type,
- title,
- company,
- linked tender or contract,
- linked project where applicable,
- meeting date and time,
- venue or mode,
- committee type,
- chairperson,
- secretary,
- quorum requirements,
- confidentiality level,
- proceeding status,
- minutes version and approval state.

**Example proceeding types**

- Tender Evaluation Meeting
- CIT Meeting
- Site Meeting
- Inspection Session
- Acceptance Committee Sitting
- Variation Review
- Claims Review
- Dispute Session
- Termination Review
- Monitoring Review

**7.2 Participant Management**

The system shall allow recording of all participants in a proceeding.

For each participant, the system shall capture:

- employee or external participant,
- role in the session,
- represented function,
- attendance status,
- attendance signature status,
- remarks.

Attendance statuses should include:

- Present
- Absent
- Excused
- Remote

This is necessary for governance and possible quorum validation.

**7.3 Agenda Management**

The system shall allow proceedings to be structured into agenda items.

Each agenda item shall capture:

- subject,
- agenda sequence,
- agenda type,
- linked reference doctype and record,
- presenter,
- discussion summary,
- recommendation summary,
- whether a decision is required,
- decision status.

This allows formal linking between deliberation and procurement records.

**7.4 Resolution Management**

The system shall allow one or more resolutions to be recorded against an agenda item.

Each resolution shall capture:

- resolution type,
- resolution text,
- whether it passed,
- effective date,
- approving authority,
- implementation status,
- implementation reference.

Example resolution types:

- Recommend Approval
- Approve
- Reject
- Recommend Penalty
- Recommend Acceptance
- Recommend Rejection
- Recommend Variation
- Recommend Stop Work
- Escalate
- Request Clarification
- Recommend Termination
- Endorse Payment
- Note for Record

This is critical because downstream processes often depend on formal committee outputs.

**7.5 Action Tracking**

The system shall allow action items to be raised from proceedings.

Each action item shall capture:

- proceeding,
- agenda item,
- assigned user,
- assigned role,
- due date,
- description,
- priority,
- status,
- linked Midas Task where applicable.

This ensures that meeting outcomes do not disappear into minutes without follow-up.

**7.6 Evidence Management**

The system shall support structured evidence registration for proceedings.

Evidence types may include:

- Minutes Attachment
- Inspection Evidence
- Technical Report
- Financial Analysis
- Legal Advice
- Supplier Submission
- Photos
- Signed Attendance
- Signed Resolution
- Supporting Memo

Each evidence record shall support:

- linkage to proceeding,
- optional linkage to agenda item,
- file attachment,
- reference record,
- summary,
- submitter,
- submission timestamp.

This supports transparency, legal defensibility, and audit review.

**7.7 Signed Minutes and Signed Decisions**

The system shall allow signature records for:

- minutes,
- attendance,
- resolutions.

Each signature record shall capture:

- signer,
- signer role,
- signature target,
- signature method,
- signature hash,
- signature timestamp,
- verification status.

This supports formal acknowledgment and evidentiary reliability.

**8\. Workflows**

**8.1 Proceeding Workflow**

**States**

- Draft
- Scheduled
- In Session
- Minutes Drafted
- Under Review
- Approved
- Locked
- Cancelled

**Meaning**

- **Draft**: proceeding being prepared
- **Scheduled**: participants and agenda prepared
- **In Session**: proceeding in progress
- **Minutes Drafted**: secretary has prepared minutes
- **Under Review**: chairperson or authority reviewing minutes
- **Approved**: minutes approved
- **Locked**: final record frozen
- **Cancelled**: session canceled

**Basic rules**

- Locked proceedings are immutable
- Approved proceedings may require signatures before locking
- Cancelled proceedings remain in audit history

**8.2 Resolution Workflow**

**States**

- Draft
- Proposed
- Approved
- Rejected
- Implemented
- Closed

**Meaning**

- **Draft**: not yet tabled
- **Proposed**: put forward for decision
- **Approved**: formally accepted
- **Rejected**: formally declined
- **Implemented**: downstream action executed
- **Closed**: no further activity required

**8.3 Action Item Workflow**

**States**

- Open
- In Progress
- Completed
- Overdue
- Cancelled

This allows operational follow-up from proceedings.

**9\. Quorum and Attendance Rules**

The module shall support quorum-sensitive proceedings.

Where quorum applies:

- proceedings cannot be formally approved unless quorum is met,
- binding resolutions cannot be approved without quorum,
- attendance shall be tied to participant records.

Quorum rules may differ depending on proceeding type or committee type.

Example:

- Inspection session may require chairperson plus minimum number of members.
- CIT milestone review may require at least one chairperson and one member.

This is important because committee validity may affect legal standing of decisions.

**10\. Minutes and Version Control**

The module shall support formal minutes handling.

**Rules**

- minutes are drafted after the proceeding,
- minutes are reviewed and approved,
- approved minutes shall not be overwritten,
- corrections shall create a new version,
- previous versions shall remain visible and auditable.

This mirrors the same version-control principle already needed for contract documents.

**11\. Integration with Procurement and Contract Lifecycle Management (CLM)**

The module shall integrate with the procurement and contract management layers, not operate in isolation.

**11.1 Tender Evaluation**

Proceedings may record tender evaluation meetings and outcomes.

**11.2 Contract Implementation**

Proceedings may record:

- milestone verification minutes,
- site meetings,
- implementation issues,
- delay recommendations.

This supports the requirement for site meetings, MoM, and milestone completion minutes.

**11.3 Inspection and Acceptance**

Proceedings may record:

- inspection minutes,
- test deliberations,
- acceptance or rejection recommendations,
- penalty recommendations.

This supports the inspection/testing requirements.

**11.4 Certification**

Proceedings may form the evidentiary basis for issuance of certificates.

**11.5 Payment and Finance**

Proceedings may include endorsement of payment-related decisions.

**11.6 Variations**

Proceedings may record technical and financial review deliberations leading to variation approval or rejection.

**11.7 Claims and Disputes**

Proceedings may record:

- negotiation sessions,
- mediation discussions,
- escalation recommendations,
- stop-work recommendations.

This supports the dispute lifecycle and stop-work requirement.

**11.8 Termination**

Proceedings may record:

- legal advice discussion,
- settlement review,
- handover review,
- recommendation for termination.

This supports the termination requirement.

**11.9 Monitoring**

Proceedings may support monthly contract monitoring reviews and associated escalations.

**12\. Downstream Automation**

The module may trigger or enable downstream processes, but only through controlled rules.

**Examples**

Approved resolutions may:

- advance a milestone workflow,
- create a draft Acceptance Certificate,
- recommend a Contract Variation,
- create or escalate a Claim,
- create or escalate a Dispute Case,
- recommend stop-work,
- recommend payment endorsement,
- recommend termination.

Not every resolution should auto-execute.  
In many cases, the approved resolution should only **unlock** the next workflow step.

**13\. Security and Confidentiality**

The module shall support secure access control based on:

- company,
- role,
- committee/proceeding type,
- linked record context,
- confidentiality level.

**Confidentiality levels**

- Public
- Internal
- Restricted

**Supplier access**

Supplier representatives shall only access proceedings where:

- they are explicit participants, or
- the proceeding is designated as supplier-facing.

Internal deliberative sessions shall remain restricted.

**14\. Reporting**

The module should provide at least the following reports:

- Proceedings Register
- Attendance Register
- Resolution Register
- Action Item Tracker
- Pending Minutes Report
- Overdue Action Items Report
- Committee Quorum Compliance Report

These are complementary to the financial and contract monitoring reports already required by CLM.

**15\. Data Model Summary**

The recommended first-class entities are:

- Procurement Proceeding
- Proceeding Participant
- Agenda Item
- Proceeding Resolution
- Proceeding Action Item
- Proceeding Evidence
- Proceeding Signature

**16\. MVP vs Full Version**

**MVP**

- Proceeding
- Participant
- Agenda Item
- Resolution
- Action Item
- basic workflows
- links to procurement and CLM records

**Full Version**

- quorum engine
- signed attendance
- signed minutes
- evidence registry
- versioned minutes
- downstream automation hooks
- confidentiality enforcement
- supplier-safe external participation

**17\. Implementation Guidance**

The module should be implemented as a **custom governance module**, while reusing Midas masters such as:

- Employee
- User
- Department
- Company
- Project
- Task
- Supplier

It should not rely on Midas Event/Calendar as the primary engine, because those models do not adequately support:

- quorum,
- agenda structure,
- resolutions,
- legal-grade minutes,
- evidence-linked decisions,
- signed formal proceedings.

**18\. Strategic Note**

Although this document is written for procurement, the underlying design is structurally reusable beyond procurement. That said, this version remains intentionally procurement-specific so that legal, technical, and financial requirements remain clear before any generalization or renaming is done.

context_type  
context_reference_doctype  
context_reference_name

This is what makes the system reusable without rewriting logic.