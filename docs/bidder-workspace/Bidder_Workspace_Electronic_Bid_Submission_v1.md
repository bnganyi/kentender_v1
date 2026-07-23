# Bidder Workspace & Electronic Bid Submission — UX / Product Specification v1

**Project:** KenTender e-Procurement System  
**Module:** Bid Submissions  
**Audience:** Product, UX, engineering, QA  
**Status:** Initial focused specification  
**Design rule:** Electronic-first, schema-driven, simple for bidders, legally defensible for procurement.

---

## 1. Purpose

The Bidder Workspace lets bidders prepare and submit bids electronically for a published tender.

The workspace must not be a PDF-filling exercise. It must render the bidder-facing submission tasks from the published tender’s electronic submission schema.

The user should always understand:

```text
What must I complete before I can submit my bid?
```

---

## 2. Core Product Direction

```text
Build one universal bidder workspace shell.
Render tender-specific sections from the published tender schema.
Do not build separate bidder workspaces per STD family.
```

The workspace shell is stable across tenders. The internal sections vary by STD family, STD version, procurement method, lots, and tender configuration.

```text
Published Tender
→ Confirmed Electronic Tender Package
→ Bidder Workspace Manifest
→ Rendered Bidder Workspace
→ Bid Validation
→ Submit & Seal Bid
→ Submission Receipt
```

---

## 3. What This Module Owns

| Owns | Does not own |
|---|---|
| Bidder workspace access | Tender configuration |
| Electronic bid preparation | Tender publication |
| Bidder declarations and forms | Bid opening |
| Requirement responses | Bid evaluation |
| Evidence uploads | Award recommendation |
| Price schedule completion | Contract creation |
| Bid validation before submission | Contract management |
| Electronic submission and sealing | Post-award contract administration |
| Submission receipt | Editing published tender content |

---

## 4. End-to-End Workflow

```text
Published Tender
→ Bidder opens Tender Overview
→ Bidder opens Bidder Workspace
→ System creates draft bid workspace
→ Bidder completes required sections
→ System validates bid
→ Bidder submits and seals bid
→ System issues submission receipt
→ Bid waits for submission deadline and bid opening
```

The bidder must not need to understand internal tender package artifacts, render manifests, STD bindings, or schema IDs.

---

## 5. Fixed Workspace Shell

Every published tender uses the same broad workspace shell:

```text
Tender Overview
Tender Documents
Submission Checklist
Prepare Bid
Review & Validate
Submit & Seal Bid
Submission Receipt
```

The shell gives bidders a predictable experience across all STD families.

---

## 6. Dynamic Section Rendering

Inside **Prepare Bid**, the system renders sections from the tender’s bidder workspace manifest.

Reusable section types:

| Section Type | Purpose |
|---|---|
| `document_acknowledgement` | Bidder acknowledges tender documents and addenda. |
| `declaration_form` | Bidder completes declarations, certifications, and form fields. |
| `eligibility_checklist` | Bidder confirms eligibility and uploads required eligibility evidence. |
| `requirement_matrix` | Bidder responds to technical, goods, works, or service requirements. |
| `technical_response` | Bidder enters methodology, proposal narrative, work plan, or technical response. |
| `evidence_uploads` | Bidder uploads certificates, authorizations, brochures, CVs, licenses, or supporting files. |
| `price_schedule` | Bidder enters itemized prices, BOQ rates, lump sums, or financial offer. |
| `implementation_schedule` | Bidder provides delivery timeline, milestones, or implementation approach. |
| `lot_selection` | Bidder chooses which lots they are bidding for, where lots are enabled. |
| `final_confirmation` | Bidder confirms bid completeness and declarations before submission. |
| `sealed_submission` | Bidder submits and locks the electronic bid. |

The renderer must not hardcode NSSF, IT STD, or any specific tender.

---

## 7. Bidder Workspace Manifest

Each published tender produces a bidder workspace manifest.

The manifest controls:

| Manifest Element | Meaning |
|---|---|
| Workspace sections | What bidders must complete. |
| Section order | How the workspace is presented. |
| Required sections | What blocks submission if incomplete. |
| Field schemas | What inputs appear. |
| Upload rules | What evidence files are required or optional. |
| Validation rules | What must pass before submission. |
| Lot applicability | Which sections apply to which lots. |
| Deadlines | When bidders can submit or no longer submit. |
| Addendum effect | Whether bidder acknowledgement is required after an addendum. |

Example manifest shape:

```json
{
  "published_tender_ref": "PUB-2026-00018",
  "std_family": "Information Technology",
  "workspace_title": "Bidder Workspace",
  "submission_deadline": "2026-10-25T11:00:00+03:00",
  "sections": [
    {
      "section_key": "document_acknowledgement",
      "section_type": "document_acknowledgement",
      "title": "Tender Documents & Addenda",
      "required": true,
      "blocks_submission": true
    },
    {
      "section_key": "eligibility_declarations",
      "section_type": "declaration_form",
      "title": "Eligibility & Declarations",
      "required": true,
      "blocks_submission": true
    },
    {
      "section_key": "technical_requirements",
      "section_type": "requirement_matrix",
      "title": "Technical Requirements",
      "required": true,
      "blocks_submission": true
    },
    {
      "section_key": "price_schedule",
      "section_type": "price_schedule",
      "title": "Price Schedule",
      "required": true,
      "blocks_submission": true
    }
  ]
}
```

---

## 8. User-Facing Workspace States

| State | Meaning | Primary Action |
|---|---|---|
| Not Started | Bidder has not opened a workspace for this tender. | Start Bid |
| Draft | Workspace exists but no major sections are complete. | Continue Bid |
| In Progress | Some sections are complete and some remain. | Continue Bid |
| Needs Attention | Validation blockers or required omissions exist. | Fix Issues |
| Ready to Submit | All blockers are cleared. | Submit & Seal Bid |
| Submitted | Bid has been submitted and sealed. | View Receipt |
| Withdrawn | Bidder withdrew submission before deadline, if allowed. | Start Revised Bid / View History |
| Closed | Submission deadline has passed. | View Submission Status |

`Withdrawn` should appear only if the procurement rules for the tender allow withdrawal or replacement before the deadline.

---

## 9. Screen A — Published Tender Overview

### Purpose

Give bidders enough information to decide whether to start or continue a bid.

### User Decision

> Do I want to prepare a bid for this published tender?

### Required Content

| Area | Display |
|---|---|
| Tender title | Full published tender title |
| Procuring entity | Published procuring entity |
| Procurement method | Published method |
| STD family | Published STD family |
| Publication date/time | Published value |
| Clarification deadline | Published value, if applicable |
| Submission deadline | Published value |
| Opening date/time | Published value |
| Tender documents | View / Download |
| Addenda | View / Acknowledge, if present |
| Bidder workspace status | Not Started / Draft / In Progress / Submitted |

### Primary Action

```text
Start Bid
```

If a workspace already exists:

```text
Continue Bid
```

If already submitted:

```text
View Submission Receipt
```

---

## 10. Screen B — Bidder Workspace Home

### Purpose

Show the bidder what must be completed before submission.

### User Decision

> What remains before my bid can be submitted?

### Required Sections

```text
Tender Summary
Submission Deadline
Submission Progress
Section Checklist
Current Issues
Primary Next Action
```

### Submission Checklist Columns

| Column |
|---|
| Section |
| Required |
| Status |
| Issues |
| Last Updated |
| Action |

### Section Statuses

```text
Not Started
In Progress
Needs Attention
Complete
Not Applicable
```

### Primary Action Logic

| Workspace Condition | Primary Action |
|---|---|
| No section started | Start First Section |
| Incomplete sections exist | Continue Bid |
| Blockers exist | Fix Issues |
| No blockers | Review & Validate |
| Ready after validation | Submit & Seal Bid |
| Submitted | View Receipt |

---

## 11. Screen C — Tender Documents & Addenda

### Purpose

Let bidders view the tender documents and acknowledge current documents/addenda where required.

### User Decision

> Have I reviewed and acknowledged the documents required for this submission?

### Required Content

| Item | Action |
|---|---|
| Confirmed tender document | View / Download PDF |
| Tender package summary | View summary |
| Addendum list | View / Download |
| Acknowledgement status | Acknowledge required documents |

### Rule

If a tender addendum requires acknowledgement, submission is blocked until acknowledgement is complete.

---

## 12. Screen D — Dynamic Section Screen

One reusable screen pattern renders declaration forms, requirement matrices, evidence uploads, technical responses, implementation schedules, and price schedules.

### Purpose

Let bidders complete one schema-generated section at a time.

### User Decision

> What must I enter or upload for this section to be complete?

### Required Layout

```text
Section title
Section instructions
Progress within section
Fields / rows / uploads generated from schema
Validation messages
Save Section
Save & Continue
Back to Workspace
```

### Field Behavior

| Field Type | Behavior |
|---|---|
| Text | Required or optional based on schema |
| Number / Money | Numeric validation, currency rules, precision rules |
| Date | Deadline and date range validation |
| Boolean / Yes-No | Conditional follow-up fields where configured |
| Select | Controlled options from schema |
| Requirement response | Compliance selection, explanation, evidence link |
| Upload | File type, size, required/optional, expiry metadata if required |
| Price line | Quantity, unit, rate, total, currency, tax treatment where configured |
| Declaration | Confirmation checkbox or signed declaration flow |

---

## 13. Requirement Matrix Behavior

The requirement matrix must handle large tenders without overwhelming bidders.

For tenders like NSSF with many IT requirements, use grouped navigation:

```text
Requirement Groups
→ Group Summary
→ Requirement Rows
→ Evidence Links
→ Save Group
```

Do not show all requirements as a single unstructured wall.

### Requirement Row Columns

| Column |
|---|
| Requirement ID |
| Requirement |
| Response Required |
| Bidder Response |
| Evidence Required |
| Status |

### Requirement Statuses

```text
Not Started
Answered
Needs Evidence
Needs Attention
Complete
Not Applicable
```

---

## 14. Evidence Upload Behavior

Evidence uploads may come from many schema sections but should be visible in one consolidated evidence view.

### Evidence Upload Columns

| Column |
|---|
| Evidence Item |
| Required |
| Related Section |
| File Uploaded |
| Expiry / Validity, if required |
| Status |
| Action |

### Rules

```text
A required evidence item blocks submission until uploaded and valid.
Evidence linked to a requirement should be visible from both the requirement row and the Evidence Uploads section.
```

---

## 15. Price Schedule Behavior

The price schedule must be structured and validated electronically.

### Price Schedule Columns

| Column |
|---|
| Line Item |
| Description |
| Quantity |
| Unit |
| Currency |
| Unit Price |
| Total |
| Status |

### Rules

```text
Required price lines must be completed before submission.
System-calculated totals must be read-only.
Bidder-entered price fields must preserve audit history.
Currency and tax behavior must follow the published tender schema.
```

---

## 16. Review & Validate Bid

### Purpose

Run final validation before submission.

### User Decision

> Is my bid complete enough to submit and seal?

### Required Sections

```text
Submission Summary
Completed Sections
Outstanding Blockers
Warnings
Declaration Before Submission
```

### Validation Result States

| State | Meaning | Action |
|---|---|---|
| Has Blockers | Required items are missing or invalid. | Fix Issues |
| Has Warnings Only | Bid can be submitted but user should review warnings. | Submit & Seal Bid enabled |
| Ready to Submit | All required validations passed. | Submit & Seal Bid |

---

## 17. Submit & Seal Bid

### Purpose

Let the authorized bidder submit the final electronic bid before the deadline.

### User Decision

> Do I want to submit and seal this bid now?

### Confirmation Modal

```text
Submit & Seal Bid?

This will submit your bid electronically for this tender.

After submission, your bid will be locked and a submission receipt will be issued.

You may not edit this submitted bid unless the tender rules allow withdrawal or replacement before the submission deadline.

This action does not open or evaluate your bid.

[Cancel] [Submit & Seal Bid]
```

### System Behavior

| System Action | Result |
|---|---|
| Re-run validation | Confirms no blockers at submission time |
| Lock bid responses | Prevents casual edits after submission |
| Seal submission | Preserves confidentiality until opening |
| Timestamp submission | Records exact submission time |
| Generate receipt | Gives bidder proof of submission |
| Record audit event | Preserves submission trace |
| Update submission status | Marks bid as Submitted |

---

## 18. Submission Receipt

### Purpose

Give the bidder verifiable proof that the bid was submitted.

### Receipt Content

| Field |
|---|
| Tender Ref |
| Bidder Organization |
| Submission Ref |
| Submission Timestamp |
| Submission Status |
| Submitted By |
| Section Completion Summary |
| Receipt Hash / Verification Code |
| Download Receipt |

### User Actions

```text
Download Receipt
Return to Tender Overview
View Submitted Bid Summary
```

---

## 19. Validation Model

Validation must be schema-driven.

### Validation Levels

| Level | Examples |
|---|---|
| Workspace | Submission deadline not passed, bidder eligible to submit |
| Section | Required section complete, required declaration accepted |
| Field | Required value present, valid format, valid range |
| Upload | File present, correct type, size acceptable, expiry valid if required |
| Requirement | Mandatory requirement answered, required evidence attached |
| Price | Required price line completed, totals valid, currency valid |
| Final submission | Declaration complete, no blockers, authorized submitter |

### User-Facing Severity

| Severity | Meaning |
|---|---|
| Blocker | Must be fixed before submission. |
| Warning | Should be reviewed, but does not block submission. |
| Information | Helpful context only. |

---

## 20. Roles and Permissions

| Role | Start Bid | Edit Draft | Upload Evidence | Enter Prices | Submit & Seal | View Receipt |
|---|---:|---:|---:|---:|---:|---:|
| Bidder Admin | Yes | Yes | Yes | Yes | Yes | Yes |
| Bid Preparer | Yes | Yes | Yes | Configurable | No | Yes |
| Financial Preparer | No | Configurable | Configurable | Yes | No | Yes |
| Authorized Submitter | Yes | Yes | Yes | Yes | Yes | Yes |
| Bidder Viewer | No | No | No | No | No | Yes |

A bidder organization may assign internal users, but the final submitter must be authorized according to bidder account rules.

---

## 21. Minimal Domain Model

### Published Tender

| Field | Notes |
|---|---|
| published_tender_ref | Public tender reference |
| tender_title | Published tender title |
| procuring_entity | Published procuring entity |
| std_family | STD family |
| submission_deadline | Deadline for electronic submission |
| opening_datetime | Scheduled opening time |
| bidder_workspace_manifest_ref | Manifest used to render workspace |
| status | Published / Closed / Cancelled / Addendum Issued |

### Bid Workspace

| Field | Notes |
|---|---|
| bid_workspace_ref | Workspace reference |
| published_tender_ref | Linked published tender |
| bidder_org_ref | Bidder organization |
| workspace_status | Draft / In Progress / Needs Attention / Ready to Submit / Submitted |
| manifest_version | Manifest version used |
| created_at | First workspace creation time |
| last_updated_at | Last bidder activity |

### Bid Section Instance

| Field | Notes |
|---|---|
| section_instance_ref | Section instance reference |
| bid_workspace_ref | Parent workspace |
| section_key | From manifest |
| section_type | Renderer type |
| section_status | Not Started / In Progress / Needs Attention / Complete |
| blocker_count | Current blockers |
| warning_count | Current warnings |

### Bid Submission

| Field | Notes |
|---|---|
| submission_ref | Submission reference |
| bid_workspace_ref | Linked workspace |
| submitted_by | Authorized submitting user |
| submitted_at | Timestamp |
| submission_status | Submitted / Withdrawn / Superseded / Opened |
| receipt_ref | Generated receipt |
| sealed_payload_ref | Sealed submission artifact |

---

## 22. API Contracts

### 22.1 Get Published Tender Overview

```text
GET /api/published-tenders/{published_tender_ref}
```

### 22.2 Start or Get Bid Workspace

```text
POST /api/published-tenders/{published_tender_ref}/bid-workspace
```

Behavior:

```text
If no workspace exists for the bidder organization, create one.
If a workspace exists, return it.
```

### 22.3 Get Bid Workspace

```text
GET /api/bid-workspaces/{bid_workspace_ref}
```

### 22.4 Save Section

```text
PATCH /api/bid-workspaces/{bid_workspace_ref}/sections/{section_key}
```

### 22.5 Upload Evidence

```text
POST /api/bid-workspaces/{bid_workspace_ref}/evidence
```

### 22.6 Validate Bid

```text
POST /api/bid-workspaces/{bid_workspace_ref}/validate
```

### 22.7 Submit and Seal Bid

```text
POST /api/bid-workspaces/{bid_workspace_ref}/submit-and-seal
```

### 22.8 Get Submission Receipt

```text
GET /api/bid-submissions/{submission_ref}/receipt
```

---

## 23. Stitch Prompt

```text
Design the Bidder Workspace and Electronic Bid Submission flow for KenTender.

Ignore visual branding and left navigation unless needed for context.

Design ethos:
Electronic-first, simple, schema-driven, bidder-friendly, and legally safe.
Do not design a PDF-filling workflow.
Do not hardcode the IT STD, NSSF, or any single STD family.

Core architecture:
One universal bidder workspace shell renders tender-specific sections from the published tender's bidder workspace manifest.

Fixed workspace shell:
- Tender Overview
- Tender Documents
- Submission Checklist
- Prepare Bid
- Review & Validate
- Submit & Seal Bid
- Submission Receipt

Dynamic section types:
- document_acknowledgement
- declaration_form
- eligibility_checklist
- requirement_matrix
- technical_response
- evidence_uploads
- price_schedule
- implementation_schedule
- lot_selection
- final_confirmation
- sealed_submission

Screens to design:
1. Published Tender Overview
2. Bidder Workspace Home
3. Tender Documents & Addenda
4. Dynamic Section Screen
5. Requirement Matrix section example
6. Evidence Uploads section example
7. Price Schedule section example
8. Review & Validate Bid
9. Submit & Seal Bid modal
10. Submission Receipt

Published Tender Overview:
Purpose: help bidder decide whether to start or continue a bid.
Primary action:
- Start Bid
- Continue Bid if workspace exists
- View Submission Receipt if submitted

Bidder Workspace Home:
Show:
- Tender Summary
- Submission Deadline
- Submission Progress
- Section Checklist
- Current Issues
- Primary Next Action

Checklist columns:
- Section
- Required
- Status
- Issues
- Last Updated
- Action

Statuses:
- Not Started
- In Progress
- Needs Attention
- Complete
- Not Applicable

Tender Documents & Addenda:
Show:
- Confirmed tender document: View / Download PDF
- Addenda: View / Download / Acknowledge if required
- Acknowledgement status

Dynamic Section Screen:
Show:
- Section title
- Section instructions
- Progress within section
- Fields/rows/uploads rendered from schema
- Validation messages
- Save Section
- Save & Continue
- Back to Workspace

Requirement Matrix:
Use grouped navigation for large requirement sets.
Do not show 80+ requirements as one wall.
Columns:
- Requirement ID
- Requirement
- Response Required
- Bidder Response
- Evidence Required
- Status

Evidence Uploads:
Columns:
- Evidence Item
- Required
- Related Section
- File Uploaded
- Expiry / Validity if required
- Status
- Action

Price Schedule:
Columns:
- Line Item
- Description
- Quantity
- Unit
- Currency
- Unit Price
- Total
- Status

Review & Validate Bid:
Show:
- Submission Summary
- Completed Sections
- Outstanding Blockers
- Warnings
- Declaration Before Submission

Submit & Seal modal:
Submit & Seal Bid?

This will submit your bid electronically for this tender.

After submission, your bid will be locked and a submission receipt will be issued.

You may not edit this submitted bid unless the tender rules allow withdrawal or replacement before the submission deadline.

This action does not open or evaluate your bid.

[Cancel] [Submit & Seal Bid]

Submission Receipt:
Show:
- Tender Ref
- Bidder Organization
- Submission Ref
- Submission Timestamp
- Submission Status
- Submitted By
- Section Completion Summary
- Receipt Hash / Verification Code
- Download Receipt

Important rules:
- PDF is reference only, not the submission surface.
- Submission is blocked while blockers exist.
- Warnings can allow submission if configured.
- Every dynamic section must come from schema.
- Bidders should always see the next practical action.
```

---

## 24. Cursor Prompt

```text
Implement the Bidder Workspace and Electronic Bid Submission module.

Core rule:
Build one universal bidder workspace shell that renders sections from the published tender bidder_workspace_manifest.
Do not hardcode STD family-specific screens.
Do not build a PDF-filling submission workflow.

Implement screens:
1. Published Tender Overview
2. Bidder Workspace Home
3. Tender Documents & Addenda
4. Dynamic Section Renderer
5. Requirement Matrix Renderer
6. Evidence Upload Renderer
7. Price Schedule Renderer
8. Review & Validate Bid
9. Submit & Seal Bid flow
10. Submission Receipt

Implement section renderer types:
- document_acknowledgement
- declaration_form
- eligibility_checklist
- requirement_matrix
- technical_response
- evidence_uploads
- price_schedule
- implementation_schedule
- lot_selection
- final_confirmation
- sealed_submission

Implement workspace statuses:
- Not Started
- Draft
- In Progress
- Needs Attention
- Ready to Submit
- Submitted
- Withdrawn
- Closed

Implement section statuses:
- Not Started
- In Progress
- Needs Attention
- Complete
- Not Applicable

Implement validation severities:
- Blocker
- Warning
- Information

Submission rules:
- Do not allow Submit & Seal Bid if blockers exist.
- Do not allow submission after submission deadline.
- Re-run validation immediately before submission.
- Lock bid responses after submission.
- Seal submission payload.
- Generate submission receipt.
- Record audit events for save, validate, submit, seal, receipt generation, withdrawal where enabled.

PDF behavior:
- Show tender PDF as a downloadable reference document.
- Do not use PDF as the bid submission surface.

Requirement matrix behavior:
- Support grouped navigation for large requirement sets.
- Support compliance responses, narratives, attachments, evidence links, and status per requirement.

Evidence upload behavior:
- Validate file type, size, required status, expiry where configured, and linkage to section/requirement.

Price schedule behavior:
- Validate required lines, currency, numeric precision, calculated totals, and missing values.

Acceptance criteria:
- A bidder can start a workspace from a published tender.
- The workspace renders from manifest sections.
- The bidder can complete declarations, requirements, evidence, and prices electronically.
- The bidder can view/download the tender PDF as reference.
- The bidder can run validation and see blockers.
- Submit & Seal is disabled while blockers exist.
- Successful submission locks the bid and generates a receipt.
- The implementation supports multiple STD families through schema, not separate hardcoded screens.
```

---

## 25. Acceptance Checklist

| Test | Pass condition |
|---|---|
| Electronic-first | Bidder submits through structured sections, not a filled PDF. |
| Schema-driven | Workspace sections render from manifest. |
| STD-variable | IT, works, goods, consultancy, and future STD families can use the same shell. |
| Clear progress | Bidder always sees completion status and next action. |
| Large requirements manageable | Requirement matrix supports grouped navigation. |
| Evidence controlled | Required uploads block submission until complete. |
| Price schedule controlled | Required price lines and totals are validated. |
| PDF available | Bidder can view/download tender document as reference. |
| Validation enforced | Blockers prevent submission. |
| Submission sealed | Submitted bid is locked and sealed. |
| Receipt issued | Bidder receives verifiable receipt. |
| Downstream safe | Evaluation receives structured bid data after opening. |

---

## 26. Final Rule

```text
The bidder workspace is a universal electronic submission shell powered by the published tender schema.
STD families define the content and rules.
The workspace renders, validates, seals, and receipts the bid.
```
