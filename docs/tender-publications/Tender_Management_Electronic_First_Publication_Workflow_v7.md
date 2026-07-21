# Tender Management — Electronic-First Publication Workflow v7

**Project:** KenTender e-Procurement System  
**Module:** Tender Management  
**Status:** Focused revision  
**Design rule:** Direct, user-focused, electronic-first, legally safe  
**Core correction:** Review the electronic tender package by exception. Do not duplicate configuration screens.

---

## 1. Design Ethos

KenTender is an electronic procurement system.

The system must help users advance the tender efficiently. It must not force users to re-review every record already captured in configuration screens, manage internal document packages, or treat the PDF as the controlling source of truth.

Every workflow screen must answer one practical question:

```text
What must I do next to move this tender forward safely?
```

The system should quietly preserve snapshots, schemas, hashes, generated documents, and audit records in the background.

---

## 2. Revised Big Picture Workflow

```text
Approved Procurement Package
→ Tender Configuration
→ Readiness Check
→ Review Approval
→ Electronic Tender Package Review
→ Confirm Tender Package
→ Publication Setup
→ Publish Tender
→ Bid Submissions
→ Evaluation
→ Award
```

Remove these workflow stops:

```text
Tender Documents
Send to Publication Workflow
Manual document package handoff
PDF-only confirmation
Duplicated configuration review
```

---

## 3. Revised Tender Management Menu

```text
Tender Management
  ├─ Procurement Packages
  ├─ Tender Configurations
  ├─ Publications
  ├─ Bid Submissions
  ├─ Evaluation
  └─ Awards
```

There is no primary **Tender Documents** workflow menu item.

Tender documents exist as artifacts, accessible where useful:

| Location | User access |
|---|---|
| Electronic Tender Package Review | View generated tender document, download PDF after confirmation |
| Publication Setup | View confirmed tender package and PDF |
| Published Tender | View published document |
| Audit Trail | View package integrity and event history |

---

## 4. Electronic-First Rule

```text
The electronic tender package is the operational source of truth.
The PDF is a generated legal-readable artifact.
The PDF must be accessible, but it must not be the sole basis for package confirmation.
```

The user confirms the tender package, not merely the PDF.

The electronic tender package includes:

| Package layer | Purpose |
|---|---|
| Structured tender data | Tender identity, procuring entity, procurement method, STD family, TDS/SCC values |
| Requirements schema | Requirements bidders must respond to electronically |
| Bidder submission schema | What bidders complete, upload, price, declare, and submit |
| Forms/evidence schema | Required forms, declarations, certificates, and uploads |
| Price schedule schema | Structured financial response model |
| Evaluation schema | Approved evaluation method and criteria structure |
| Generated tender document | Human-readable tender document generated from the same package |
| Integrity/audit record | Snapshot, version, lock, hash, approval trace |

---

## 5. Exception-Based Review Rule

Electronic Tender Package Review must not recreate configuration screens.

Use this rule:

```text
Show summaries by package area.
Provide one Open Full Configuration link for ordinary review.
Use direct configuration-screen links only for blockers, warnings, or specific callouts.
```

This avoids showing dozens of requirements, forms, or price lines again. Users configured those records already. Package Review checks whether the system successfully converted the approved configuration into a publishable electronic tender package.

---

## 6. How Users Land on Electronic Tender Package Review

Users should not open this screen from a main menu.

Primary entry path:

```text
Tender Configurations
→ Complete configuration
→ Run Readiness Check
→ Submit for Review
→ Review Approval
→ System generates Electronic Tender Package Review
→ User clicks Review Package
```

Also valid:

```text
Tender Configuration Home
→ Status: Package Review Generated
→ Primary action: Review Package
```

Task/notification entry:

```text
“ERP System tender package is ready for review”
→ Open task
→ Electronic Tender Package Review
```

This screen belongs to the end of Tender Configurations. Publications starts after **Confirm Tender Package**.

---

## 7. Surface 1 — Tender Configurations

### Purpose

Tender Configurations lets procurement users prepare, validate, review, and confirm the electronic tender package before publication setup.

### User Decision

```text
Is the tender ready to become the electronic package issued to bidders?
```

### Workflow

```text
Complete Configuration
→ Run Readiness Check
→ Submit for Review
→ Review Approval
→ Review Package
→ Confirm Tender Package
→ Continue to Publication Setup
```

---

## 8. Surface 2 — Electronic Tender Package Review

### Purpose

Electronic Tender Package Review lets the user confirm that the approved configuration has been converted into a complete, bidder-facing electronic tender package.

### Single User Decision

```text
Is this tender package complete enough to proceed to publication setup?
```

### Screen Title

```text
Electronic Tender Package Review
```

### Subtitle

```text
Review the package summary, bidder experience, generated tender document, and any issues before publication setup.
```

### Primary Actions

| Action | Rule |
|---|---|
| Confirm Tender Package | Enabled only when no blockers exist |
| Return for Correction | Available before confirmation |
| Open Full Configuration | Opens Tender Configuration Home |
| View Tender Document | Opens generated document viewer |
| Download PDF | Available after package confirmation, or before confirmation as preview PDF if explicitly labelled as preview |
| Back to Tender Configuration Home | Always available |

Do not show:

```text
Save as Draft
Regenerate Package
Send to Publication Workflow
Open Tender Documents
Create Publication
Edit Package
Publish Tender
```

---

## 9. Electronic Tender Package Review Layout

Use one focused review screen, not many duplicate review tabs.

Recommended sections:

```text
1. Package Readiness
2. Bidder Experience Summary
3. Tender Document Output
4. Issues & Audit
```

The screen may use anchor navigation or compact tabs for these four sections, but the sections must remain summaries, not duplicate configuration tables.

---

## 10. Context Strip

Show:

| Label |
|---|
| Tender Configuration Ref |
| Procurement Package Ref |
| Tender Title |
| Procuring Entity |
| Procurement Method |
| Standard Tender Document |
| Package Status |

Do not use ambiguous labels such as `Package Ref` where the value is actually the procurement package reference.

---

## 11. Section 1 — Package Readiness

### Purpose

Show whether each major configuration area was successfully compiled into the electronic tender package.

### Display

| Package Area | Status | Summary |
|---|---|---|
| Tender Profile | Ready / Needs attention | Core tender identity compiled |
| Tender Data Sheet | Ready / Needs attention | Tender instructions compiled |
| IT Requirements | Ready / Needs attention | Requirement set compiled; show count only |
| Implementation Schedule | Ready / Needs attention | Delivery schedule compiled |
| System Inventory & Bidder Background | Ready / Needs attention | Bidder background information compiled |
| Price Schedule | Ready / Needs attention | Price schedule compiled; show line count only |
| Evaluation Setup | Ready / Needs attention | Evaluation method compiled |
| Forms & Evidence | Ready / Needs attention | Forms and evidence requirements compiled |
| Contract Values | Ready / Needs attention | SCC and contract carry-forward values compiled |
| Tender Document | Available / Has render issues / Missing | Generated tender document status |

### Normal Review Action

```text
Open Full Configuration
```

This opens the Tender Configuration Home so the user can navigate to any detailed configuration screen from the existing configuration workflow.

Do not show direct source links for every row when all rows are ready.

---

## 12. Section 2 — Bidder Experience Summary

### Purpose

Show what bidders will experience electronically without duplicating the bidder workspace or configuration screens.

### Display

| Bidder Workspace Area | Status | Summary |
|---|---|---|
| Eligibility & Declarations | Ready / Needs attention | Required declarations generated |
| Technical Response | Ready / Needs attention | Requirement response matrix generated |
| Implementation Proposal | Ready / Needs attention | Delivery approach response area generated |
| Evidence Uploads | Ready / Needs attention | Upload controls generated |
| Price Schedule | Ready / Needs attention | Bidder price entry table generated |
| Final Submission | Ready / Needs attention | Certification and sealed submission flow prepared |

### Actions

| Action | Purpose |
|---|---|
| Preview Bidder Workspace | Show a read-only preview of what bidders will see |
| Open Full Configuration | Open the source configuration home |

Do not list every IT requirement, evidence item, form, price line, or bidder field. Show counts and readiness summaries only.

---

## 13. Section 3 — Tender Document Output

### Purpose

Give users access to the generated human-readable tender document without making the PDF the controlling workflow object.

### Display

| Output | Status | Action |
|---|---|---|
| Generated Tender Document | Available / Missing | View Tender Document |
| Render Validation | Passed / Has issues | View Render Issues |
| Preview PDF | Available before confirmation | Download Preview PDF |
| Confirmed PDF | Available after confirmation | Download Confirmed PDF |

### PDF Access Rule

Before confirmation, the PDF must be labelled clearly as:

```text
Preview PDF
```

After confirmation, the locked PDF must be labelled:

```text
Confirmed PDF
```

The user must always be able to view the generated tender document from this section.

The PDF is a generated artifact. It does not replace review of the electronic package summary and issue list.

---

## 14. Section 4 — Issues & Audit

### Purpose

Focus attention on blockers, warnings, and traceability.

If there are no issues, show:

```text
No blockers found.
The tender package can be confirmed.
```

If issues exist, show only issue-specific detail.

| Severity | Issue | Impact | Fix Action |
|---|---|---|---|
| Blocker | Price schedule has required lines without bidder entry rules | Bidders cannot price required items correctly | Open Price Schedule |
| Blocker | Evidence upload rule missing for required certificate | Bidders cannot submit required evidence | Open Forms & Evidence |
| Warning | Tender document render has table overflow | PDF may be hard to read | View Render Issues |
| Warning | Requirement group has long bidder instruction | Bidder workspace may be difficult to read | Open IT Requirements |

### Direct Link Rule

Direct configuration links appear only inside specific issues or callouts.

Allowed issue actions:

```text
Open Tender Profile
Open Tender Data Sheet
Open IT Requirements
Open Implementation Schedule
Open System Inventory & Bidder Background
Open Price Schedule
Open Evaluation Setup
Open Forms & Evidence
Open Contract Values
View Render Issues
View Readiness Report
View Approval Record
View Audit Trail
```

Do not create a permanent global sidebar containing every configuration link.

---

## 15. Confirm Tender Package

### Button

```text
Confirm Tender Package
```

### Enablement Rule

Enabled only when:

| Condition | Required |
|---|---:|
| Readiness check passed | Yes |
| Review approval exists | Yes |
| No blocking package issues | Yes |
| Bidder workspace summary ready | Yes |
| Generated tender document available | Yes |
| Package integrity check passed | Yes |

### Confirmation Modal

```text
Confirm Tender Package?

This confirms that the electronic tender package is ready for publication setup.

The package includes bidder submission requirements, forms and evidence, price schedule, evaluation setup, generated tender document, and audit record.

After confirmation, the tender will move to Publication Setup.

This action does not publish the tender, notify bidders, open bid submission, evaluate bids, approve an award, or create a contract.

[Cancel] [Confirm Tender Package]
```

### After Confirmation

Show:

```text
Tender package confirmed.
The tender is ready for publication setup.
```

Primary next action:

```text
Continue to Publication Setup
```

Secondary actions:

```text
View Tender Document
Download Confirmed PDF
View Audit
Back to Tender Configuration Home
```

---

## 16. Return for Correction

### Button

```text
Return for Correction
```

### Modal

```text
Return for Correction?

This will return the tender to Tender Configurations for correction.

A new readiness check, review approval, electronic tender package review, and package confirmation will be required before publication.

Reason for return
[textarea]

[Cancel] [Return for Correction]
```

The system must not allow casual editing from the review screen. Corrections must go back through the controlled configuration workflow.

---

## 17. Automatic System Behavior After Confirmation

After **Confirm Tender Package**, the system automatically:

| System action | Purpose |
|---|---|
| Locks the configuration snapshot | Prevent uncontrolled edits |
| Locks STD version reference | Preserve legal source |
| Locks bidder submission schema | Preserve electronic response structure |
| Locks requirements schema | Preserve compliance response structure |
| Locks forms/evidence schema | Preserve required evidence rules |
| Locks price schedule schema | Preserve financial response structure |
| Locks evaluation schema | Preserve evaluation method |
| Locks generated tender document | Preserve human-readable legal artifact |
| Creates or opens Publication Setup record | Let user continue immediately |
| Records audit event | Preserve who confirmed what and when |

The user should not perform these as separate manual handoff actions.

---

## 18. Surface 3 — Publications Dashboard

### Purpose

Publications is the work queue for confirmed tenders that need publication setup, scheduling, or publishing.

### User Decision

```text
Which confirmed tender needs publication setup or publishing next?
```

### Tabs

```text
Awaiting Setup
Ready to Publish
Scheduled
Published
Returned
```

### Summary Cards

Use only workflow cards:

```text
Awaiting Setup
Ready to Publish
Scheduled
Returned
```

Do not show analytics cards such as:

```text
Average publication time
Publication quality
Active tenders
System health
```

### Table Columns

| Column |
|---|
| Publication Ref |
| Tender Title |
| Procuring Entity |
| Standard Tender Document |
| Status |
| Publication Date/Time |
| Submission Deadline |
| Opening Date/Time |
| Issues |
| Next Action |

### State-to-Action Mapping

| Status | Next Action |
|---|---|
| Awaiting Setup | Complete Setup |
| Ready to Publish | Publish Tender |
| Scheduled | Manage Schedule |
| Published | View Published Tender |
| Returned | Review Comments |

Each tab must show only matching records unless an explicit `All` tab exists.

---

## 19. Surface 4 — Publication Setup

### Purpose

Publication Setup lets authorized users set publication details and publish the confirmed electronic tender package.

### User Decision

```text
Are the publication details correct, and should this tender become visible to bidders?
```

### What Publications Owns

| Owns | Does not own |
|---|---|
| Publication Date/Time | Tender requirements |
| Tender Notice | Evaluation criteria |
| Clarification Deadline | Price schedule structure |
| Submission Deadline | Bidder forms/evidence rules |
| Opening Date/Time | Locked ITT/GCC text |
| Bidder Visibility | Tender configuration values |
| Bidder Workspace Activation | Contract values |
| Publish Tender action | Bid evaluation |

### Required Fields

| Field | Required | Helper text |
|---|---:|---|
| Publication Date/Time | Yes | Set when this tender becomes visible to bidders. |
| Tender Notice | Yes | Write the public notice shown to bidders. |
| Clarification Deadline | Conditional | Set the last date and time for clarification requests. |
| Submission Deadline | Yes | Set the final date and time for electronic bid submission. |
| Opening Date/Time | Yes | Set when submitted bids may be opened. |
| Bidder Visibility | Yes | Choose who can view the tender after publication. |
| Activate Bidder Workspace | Yes | Enable bidders to complete and submit responses electronically. |

### Helpful Context Links

| Link | Purpose |
|---|---|
| View Confirmed Tender Package | Open package summary |
| View Tender Document | Open generated document |
| Download Confirmed PDF | Download locked PDF |
| View Audit | Open audit trail |

---

## 20. Publish Tender

### Button

```text
Publish Tender
```

### Confirmation Modal

```text
Publish Tender?

This will make the tender visible to bidders and activate the electronic bidder workspace.

Bidders will be able to view the confirmed tender package, complete required forms, upload evidence, enter prices, and submit bids electronically until the submission deadline.

This action does not open bids, evaluate bids, approve an award, or create a contract.

[Cancel] [Publish Tender]
```

### System Behavior

Publishing must:

| Action | Result |
|---|---|
| Lock publication setup | No casual editing after publication |
| Set tender status to Published | Tender becomes active |
| Make tender visible | According to bidder visibility |
| Activate bidder workspace | Bidders can prepare submissions |
| Open bid submission window | According to configured dates |
| Record audit event | Publisher, timestamp, package snapshot |
| Link to Bid Submissions | Downstream monitoring begins |

---

## 21. Publication Validation

| Rule | Severity | User-facing message |
|---|---|---|
| Missing publication date/time | Blocker | Set the publication date and time before publishing. |
| Missing tender notice | Blocker | Add the tender notice before publishing. |
| Missing submission deadline | Blocker | Set the submission deadline before publishing. |
| Submission deadline before publication date | Blocker | Submission deadline must be after the publication date. |
| Opening date before submission deadline | Blocker | Opening date and time must not be before the submission deadline. |
| Bidder visibility missing | Blocker | Select who can view this tender after publication. |
| Bidder workspace not activated | Blocker | Activate the electronic bidder workspace before publishing. |
| Confirmed tender document missing | Blocker | Confirmed tender document is missing. Return the tender for correction. |
| Bidder submission schema missing | Blocker | Bidder submission setup is missing. Return the tender for correction. |
| Evaluation schema missing | Blocker | Evaluation setup is missing. Return the tender for correction. |
| Price schedule schema missing | Blocker | Price schedule is missing. Return the tender for correction. |
| Forms/evidence schema missing | Blocker | Forms and evidence setup is missing. Return the tender for correction. |
| Integrity check failed | Blocker | Tender integrity check failed. Return the tender for correction. |

---

## 22. User-Facing State Model

| State | Meaning | User action |
|---|---|---|
| In Configuration | Tender-specific values are being completed | Continue Configuration |
| Ready for Review | Configuration is complete enough for review | Submit for Review |
| Approved for Package Review | Reviewer approved configuration for package review | Review Package |
| Package Review Generated | Electronic package and tender document are available | Confirm Tender Package |
| Awaiting Publication Setup | Package confirmed; publication setup is ready | Complete Publication Setup |
| Ready to Publish | Publication setup is complete | Publish Tender |
| Scheduled | Publication is scheduled for a future time | Manage Schedule |
| Published | Tender is visible to bidders | Monitor submissions |
| Returned for Correction | Tender must be corrected before publication | Correct Configuration |

---

## 23. Stitch Prompt

```text
Design the simplified electronic-first Tender Management publication flow for KenTender.

Ignore branding and left navigation.

Design ethos:
Direct, user-focused, serious, electronic-first, and legally safe.
Do not introduce unnecessary workflow steps.
Do not duplicate configuration records on package review screens.
Do not make the PDF the center of publisher decision-making.

Primary workflow:
Approved Procurement Package
→ Tender Configuration
→ Readiness Check
→ Review Approval
→ Electronic Tender Package Review
→ Confirm Tender Package
→ Publication Setup
→ Publish Tender
→ Bid Submissions
→ Evaluation
→ Award

Important removals:
- No Tender Documents work queue.
- No Send to Publication Workflow action.
- No PDF-only confirmation.
- No global sidebar containing every source configuration link.
- No repeated lists of all IT requirements, all forms, all price lines, or all criteria.

Screens to design:
1. Electronic Tender Package Review
2. Publications Dashboard
3. Publication Setup

Electronic Tender Package Review:
Title:
Electronic Tender Package Review

Subtitle:
Review the package summary, bidder experience, generated tender document, and any issues before publication setup.

How user arrives:
From Tender Configuration Home after Review Approval and package generation.
The entry action is Review Package.
This screen is not opened from Publications or from a main Tender Documents menu.

Main sections:
1. Package Readiness
2. Bidder Experience Summary
3. Tender Document Output
4. Issues & Audit

Context strip:
- Tender Configuration Ref
- Procurement Package Ref
- Tender Title
- Procuring Entity
- Procurement Method
- Standard Tender Document
- Package Status

Package Readiness section:
Show one summary row per package area only.
Do not show individual records.
Rows:
- Tender Profile
- Tender Data Sheet
- IT Requirements
- Implementation Schedule
- System Inventory & Bidder Background
- Price Schedule
- Evaluation Setup
- Forms & Evidence
- Contract Values
- Tender Document

Columns:
- Package Area
- Status
- Summary

Example summaries:
- Core tender identity compiled
- Tender instructions compiled
- 80 requirements compiled
- 2 delivery phases compiled
- Bidder background information compiled
- 22 price lines compiled
- Evaluation method compiled
- Forms and evidence requirements compiled
- SCC and contract carry-forward values compiled
- Generated tender document available

Normal action on this section:
Open Full Configuration

Do not put direct configuration links on every ready row.

Bidder Experience Summary section:
Show what bidders will experience electronically, as summaries only.
Rows:
- Eligibility & Declarations
- Technical Response
- Implementation Proposal
- Evidence Uploads
- Price Schedule
- Final Submission

Columns:
- Bidder Workspace Area
- Status
- Summary

Actions:
- Preview Bidder Workspace
- Open Full Configuration

Do not show all requirement rows, all evidence items, all forms, all price lines, or all bidder fields.

Tender Document Output section:
This is where the PDF/document belongs.
Rows:
- Generated Tender Document
- Render Validation
- Preview PDF
- Confirmed PDF

Actions:
- View Tender Document
- View Render Issues, only when issues exist
- Download Preview PDF before confirmation
- Download Confirmed PDF after confirmation

The PDF must be accessible, but it is a generated artifact, not the controlling source of truth.

Issues & Audit section:
If no issues, show:
No blockers found.
The tender package can be confirmed.

If issues exist, show an issue table:
- Severity
- Issue
- Impact
- Fix Action

Direct configuration-screen links appear only in issue rows or specific callouts.
Allowed issue actions:
- Open Tender Profile
- Open Tender Data Sheet
- Open IT Requirements
- Open Implementation Schedule
- Open System Inventory & Bidder Background
- Open Price Schedule
- Open Evaluation Setup
- Open Forms & Evidence
- Open Contract Values
- View Render Issues
- View Readiness Report
- View Approval Record
- View Audit Trail

Footer actions:
- Back to Tender Configuration Home
- Return for Correction
- Confirm Tender Package

Do not show:
- Save as Draft
- Regenerate Package
- Send to Publication Workflow
- Open Tender Documents
- Create Publication
- Edit Package
- Publish Tender

Confirm Tender Package modal:
Confirm Tender Package?

This confirms that the electronic tender package is ready for publication setup.

The package includes bidder submission requirements, forms and evidence, price schedule, evaluation setup, generated tender document, and audit record.

After confirmation, the tender will move to Publication Setup.

This action does not publish the tender, notify bidders, open bid submission, evaluate bids, approve an award, or create a contract.

[Cancel] [Confirm Tender Package]

After confirmation:
Show success message:
Tender package confirmed.
The tender is ready for publication setup.

Primary next action:
Continue to Publication Setup

Secondary actions:
- View Tender Document
- Download Confirmed PDF
- View Audit
- Back to Tender Configuration Home

Publications Dashboard:
Tabs:
- Awaiting Setup
- Ready to Publish
- Scheduled
- Published
- Returned

Summary cards:
- Awaiting Setup
- Ready to Publish
- Scheduled
- Returned

Table columns:
- Publication Ref
- Tender Title
- Procuring Entity
- Standard Tender Document
- Status
- Publication Date/Time
- Submission Deadline
- Opening Date/Time
- Issues
- Next Action

State-to-action:
- Awaiting Setup → Complete Setup
- Ready to Publish → Publish Tender
- Scheduled → Manage Schedule
- Published → View Published Tender
- Returned → Review Comments

Each tab must show only matching records unless an explicit All tab exists.

Publication Setup:
Purpose:
Set publication details and publish the confirmed electronic tender package.

Required fields:
- Publication Date/Time
- Tender Notice
- Clarification Deadline
- Submission Deadline
- Opening Date/Time
- Bidder Visibility
- Activate Bidder Workspace

Helpful context links:
- View Confirmed Tender Package
- View Tender Document
- Download Confirmed PDF
- View Audit

Primary action:
Publish Tender

Secondary actions:
- Save Setup
- Return for Correction
- Back to Publications

Publish modal:
Publish Tender?

This will make the tender visible to bidders and activate the electronic bidder workspace.

Bidders will be able to view the confirmed tender package, complete required forms, upload evidence, enter prices, and submit bids electronically until the submission deadline.

This action does not open bids, evaluate bids, approve an award, or create a contract.

[Cancel] [Publish Tender]
```

---

## 24. Cursor Prompt

```text
Implement the simplified electronic-first Tender Management publication flow.

Core rules:
1. The user confirms the electronic tender package, not merely the PDF.
2. Electronic Tender Package Review is exception-based.
3. Do not duplicate configuration screens or records.
4. Provide one Open Full Configuration link for ordinary review.
5. Provide direct configuration-screen links only for blockers, warnings, or specific callouts.
6. The PDF must be accessible but is not the source of truth.

Do not implement:
- Tender Documents as a workflow module
- Send to Publication Workflow
- PDF-only confirmation
- Global source-link sidebar
- Repeated lists of all requirements/forms/price lines/criteria on package review

Required workflow:
Approved Procurement Package
→ Tender Configuration
→ Readiness Check
→ Review Approval
→ Electronic Tender Package Review
→ Confirm Tender Package
→ Publication Setup
→ Publish Tender

Electronic Tender Package Review must include sections:
- Package Readiness
- Bidder Experience Summary
- Tender Document Output
- Issues & Audit

Package Readiness:
Show one row per package area only.
Use summary counts and readiness status.
Do not show child records.
Provide Open Full Configuration.

Bidder Experience Summary:
Show high-level bidder workspace areas only.
Provide Preview Bidder Workspace and Open Full Configuration.
Do not show all generated bidder fields.

Tender Document Output:
Provide View Tender Document.
Provide Download Preview PDF before confirmation, clearly labelled as preview.
Provide Download Confirmed PDF after confirmation.
Provide View Render Issues only if render issues exist.

Issues & Audit:
Show no issue rows when no issues exist.
If issues exist, show issue-specific direct actions such as Open IT Requirements, Open Price Schedule, Open Forms & Evidence, View Render Issues, View Readiness Report, View Approval Record, or View Audit Trail.

Footer actions before confirmation:
- Back to Tender Configuration Home
- Return for Correction
- Confirm Tender Package

After confirmation:
- Continue to Publication Setup
- View Tender Document
- Download Confirmed PDF
- View Audit
- Back to Tender Configuration Home

Remove:
- Save as Draft
- Regenerate Package
- Send to Publication Workflow
- Open Tender Documents
- Create Publication
- Edit Package
- Publish Tender from package review

After Confirm Tender Package:
1. Lock configuration snapshot.
2. Lock STD version reference.
3. Lock bidder submission schema.
4. Lock requirements schema.
5. Lock forms/evidence schema.
6. Lock price schedule schema.
7. Lock evaluation schema.
8. Lock generated tender document.
9. Create or open Publication Setup record.
10. Record audit event.
11. Show Continue to Publication Setup.

Publication Setup owns only:
- publication_datetime
- tender_notice
- clarification_deadline
- submission_deadline
- opening_datetime
- bidder_visibility
- activate_bidder_workspace
- acknowledgement_confirmed

Publication Setup must not edit:
- tender configuration values
- requirements
- evaluation criteria
- price schedule structure
- forms/evidence requirements
- STD locked text
- contract values

Publish Tender behavior:
1. Validate publication setup.
2. Lock publication setup.
3. Set tender status to Published.
4. Make tender visible according to bidder_visibility.
5. Activate bidder workspace.
6. Open bid submission window according to deadlines.
7. Record audit event.
8. Route downstream to Bid Submissions.

Acceptance criteria:
- User can review package readiness without duplicated configuration data.
- User can open the full configuration for ordinary review.
- User sees direct section links only when an issue needs fixing.
- User can access the generated tender document and PDF.
- User can confirm package readiness from one focused screen.
- User can move directly from package confirmation to Publication Setup.
- No extra handoff step exists.
- No Tender Documents workflow exists.
- Publication setup cannot alter tender content.
- Publish Tender activates bidder access and bid submissions.
```

---

## 25. Acceptance Checklist

| Test | Pass condition |
|---|---|
| Direct workflow | Confirm Tender Package leads directly to Publication Setup. |
| Electronic-first | User reviews package readiness, bidder experience, issues, and document output. |
| No duplicated configuration | Review screen does not repeat all requirements, forms, price lines, or criteria. |
| Normal source access | User can open the full configuration from the review screen. |
| Issue-specific deep links | Direct CFG links appear only for blockers, warnings, or callouts. |
| PDF access | User can view the tender document and download preview/confirmed PDF with correct labels. |
| PDF not controlling | PDF is accessible but not treated as the only review object. |
| No dead-end module | Tender Documents is not a primary workflow surface. |
| No artificial handoff | There is no Send to Publication Workflow action. |
| User can advance work | Every primary action moves the tender forward. |
| Governance retained | Package layers, document, schemas, snapshot, and audit are locked automatically. |
| Publication is narrow | Publications only sets publication details and publishes. |
| Correction is controlled | Return for Correction requires a reason before publication. |

---

## 26. Final Rule

If a screen or section does not help the user confirm the package, resolve an issue, access the document, proceed to publication setup, or publish the tender, remove it.
