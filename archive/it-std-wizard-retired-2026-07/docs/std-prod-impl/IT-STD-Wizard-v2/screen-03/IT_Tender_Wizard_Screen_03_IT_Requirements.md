# IT Tender Wizard Screen 03 — IT Requirements

**Project:** KenTender e-Procurement System  
**Module:** IT Tender Configuration Wizard  
**Screen:** 03 — IT Requirements  
**Status:** Revised UX specification  
**Design rule:** Requirements only; no scoring, pricing, contract administration, or evaluation results.

---

## 1. User Journey

A procurement user opens IT Requirements after confirming the tender profile and basic tender parameters.

The user should define the technical and service requirements that bidders must respond to.

---

## 2. Single User Decision

> What must bidders supply, deliver, integrate, support, or prove?

Everything on the screen must support that decision.

---

## 3. IT STD Grounding

Primary IT STD anchors:

| IT STD section | Relevance |
|---|---|
| Section V — Requirements of the Information System | Defines business, functional, operational, and implementation-facing requirements |
| Section VI — Technical Requirements | Defines technical specifications, standards, security, integration, performance, support, and service requirements |

Related but not owned here:

| Related section | Ownership |
|---|---|
| Section III — Evaluation and Qualification Criteria | Owned by Evaluation Setup |
| Section IV — Tendering Forms | Owned by Forms & Evidence |
| Section VII — Implementation Schedule | Owned by Implementation Schedule |
| Section VIII — System Inventory Tables | Owned by System Inventory |
| SCC / Contract Schedules | Owned by Contract Values |

---

## 4. Screen Ownership

| Item | Rule |
|---|---|
| Screen owns | IT requirement statements and bidder response expectations |
| Primary object | IT Requirement |
| Editable here | Requirement title, requirement description, category, treatment, bidder response format, bidder evidence instruction, acceptance expectation |
| Read-only references | Linked evaluation status, linked evidence status, linked contract carry-forward status |
| Must not own | Evaluation marks, pass marks, pricing, implementation phases, inventory rows, bidder submissions, bid evaluation results, SCC values, approval decisions |

---

## 5. Page Header

### Title

```text
IT Requirements
```

### Subtitle

```text
Define what bidders must supply, deliver, integrate, support, or prove.
```

### Primary action

```text
Add Requirement
```

Secondary actions:

```text
Import Requirements Template
Run Check
Continue to Implementation Schedule
```

---

## 6. Requirement Categories

Use these categories only:

| Category | Use when |
|---|---|
| Business Need | The requirement explains the business outcome or problem to be solved |
| Functional Requirement | The requirement describes a function the solution must perform |
| Technical Requirement | The requirement describes technical capability, performance, architecture, compatibility, or standards |
| Security & Compliance | The requirement describes security, access control, audit, data protection, legal, or compliance needs |
| Integration | The requirement describes connection to another system, data exchange, API, interface, or migration dependency |
| Implementation & Training | The requirement describes delivery, rollout, training, documentation, change management, or handover needs |
| Support & Warranty | The requirement describes support, maintenance, warranty, SLA, service desk, or post-implementation obligations |

Do not create separate categories for scoring, pricing, contract clauses, or evidence checklist administration.

---

## 7. Requirement Treatment

Use these values only:

| Treatment | Meaning |
|---|---|
| Mandatory | Bidder must satisfy this requirement |
| Evaluation-linked | Requirement will be considered in Evaluation Setup |
| Informational | Requirement provides context but is not directly evaluated or mandatory |

Do not show score percentages on this screen.

Forbidden examples:

```text
Scored 15%
10 marks
Pass mark
Weighted criterion
```

---

## 8. Main Table

Show these columns only:

| Column | Exact label | Purpose |
|---|---|---|
| ID | `ID` | Requirement reference |
| Requirement | `Requirement` | Short requirement title |
| Category | `Category` | One approved category |
| Treatment | `Treatment` | Mandatory, Evaluation-linked, or Informational |
| Bidder Response | `Bidder Response` | Required response format |
| Evidence | `Evidence` | Evidence instruction status |
| Acceptance | `Acceptance` | Acceptance expectation status |
| Status | `Status` | Requirement completeness |
| Actions | `Actions` | Edit, duplicate, remove where allowed |

### Evidence status values

| Value | Meaning |
|---|---|
| Evidence required | Bidder must submit supporting evidence |
| Evidence optional | Evidence may be submitted but is not mandatory |
| No evidence required | Requirement does not require separate evidence |
| Missing instruction | Evidence expectation has not been defined |

### Acceptance status values

| Value | Meaning |
|---|---|
| Acceptance defined | Acceptance expectation is clear |
| Missing acceptance | Acceptance expectation is missing |
| Not applicable | Acceptance is not applicable to this requirement |

### Requirement status values

| Value | Meaning |
|---|---|
| Complete | Requirement has enough detail |
| Needs attention | Required details are missing |
| Draft | Requirement is incomplete but saved |
| Not applicable | Requirement has been excluded with reason |

---

## 9. Requirement Drawer

Open a drawer or modal when the user creates or edits a requirement.

The drawer must use these sections only:

### Section A — Requirement

| Field | Required | Notes |
|---|---:|---|
| Requirement Title | Yes | Plain user-facing title |
| Requirement Description | Yes | Clear bidder-facing description |
| Category | Yes | One approved category |
| Treatment | Yes | Mandatory, Evaluation-linked, or Informational |

### Section B — Bidder Response

| Field | Required | Allowed values |
|---|---:|---|
| Bidder Response Format | Yes | Narrative response; Yes/No confirmation; Compliance statement; Completed table; Uploaded document; Not required |
| Bidder Response Instruction | Conditional | Required unless response format is Not required |

### Section C — Evidence

| Field | Required | Allowed values |
|---|---:|---|
| Evidence Requirement | Yes | Evidence required; Evidence optional; No evidence required |
| Evidence Instruction | Conditional | Required when evidence is required or optional |

### Section D — Acceptance

| Field | Required | Allowed values |
|---|---:|---|
| Acceptance Expectation | Yes | Acceptance defined; Not applicable |
| Acceptance Description | Conditional | Required when acceptance is defined |

### Section E — References

Read-only, light references only:

| Reference | Display text |
|---|---|
| Evaluation Setup | `Linked in Evaluation Setup` or `Not linked to evaluation` |
| Forms & Evidence | `Evidence item will be configured in Forms & Evidence` or `No evidence item required` |
| Contract Values | `May carry into contract values` or `No contract carry-forward expected` |

Do not allow scoring, price setup, contract editing, or evidence checklist administration inside this drawer.

---

## 10. Add Requirement Flow

### Button

```text
Add Requirement
```

### Modal title

```text
Add IT Requirement
```

### Default fields

```text
Requirement Title
Requirement Description
Category
Treatment
Bidder Response Format
Bidder Response Instruction
Evidence Requirement
Evidence Instruction
Acceptance Expectation
Acceptance Description
```

### Buttons

```text
Cancel
Save Requirement
```

---

## 11. Guidance Panel

Use one compact guidance panel.

### Title

```text
Requirements Guidance
```

### Content

```text
Focus on what bidders must supply, deliver, integrate, support, or prove. Evaluation scores, price lines, submission checklist items, and contract values are configured in later steps.
```

### Summary lines

```text
Mandatory requirements missing details: [count]
Requirements missing bidder response instruction: [count]
Requirements missing evidence instruction: [count]
Requirements missing acceptance expectation: [count]
```

---

## 12. Validation Behavior

This screen may show local completeness only.

Allowed:

```text
3 requirements need attention
2 missing bidder response instructions
1 missing acceptance expectation
```

Not allowed:

```text
RULE_REQ_003 failed
Section VI hash mismatch
Evaluation score total invalid
Price item missing
SCC carry-forward unresolved
```

Detailed cross-screen validation belongs in Validation.

---

## 13. Forbidden Content

Do not show or edit:

```text
evaluation marks
score percentages
technical pass marks
financial evaluation method
price line items
pricing quantities
implementation phases
inventory tables
actual bidder submissions
bidder compliance results
contract clause text
SCC values
approval decisions
publication controls
STD hashes
source anchors
rule IDs
schema versions
Tender Shell
TenderSTDInstance
```

---

## 14. Stitch Prompt

```text
Design Screen 03 for the KenTender IT Tender Configuration Wizard.

Screen name:
IT Requirements

User goal:
Define what bidders must supply, deliver, integrate, support, or prove.

Single user decision:
What must bidders supply, deliver, integrate, support, or prove?

Use this exact subtitle:
Define what bidders must supply, deliver, integrate, support, or prove.

Primary button:
Add Requirement

Secondary actions:
- Import Requirements Template
- Run Check
- Continue to Implementation Schedule

Use these requirement categories only:
- Business Need
- Functional Requirement
- Technical Requirement
- Security & Compliance
- Integration
- Implementation & Training
- Support & Warranty

Use these treatment values only:
- Mandatory
- Evaluation-linked
- Informational

Main table columns:
- ID
- Requirement
- Category
- Treatment
- Bidder Response
- Evidence
- Acceptance
- Status
- Actions

Evidence status values:
- Evidence required
- Evidence optional
- No evidence required
- Missing instruction

Acceptance status values:
- Acceptance defined
- Missing acceptance
- Not applicable

Requirement status values:
- Complete
- Needs attention
- Draft
- Not applicable

Requirement drawer sections:
A. Requirement
B. Bidder Response
C. Evidence
D. Acceptance
E. References

Drawer fields:
- Requirement Title
- Requirement Description
- Category
- Treatment
- Bidder Response Format
- Bidder Response Instruction
- Evidence Requirement
- Evidence Instruction
- Acceptance Expectation
- Acceptance Description

References section must be read-only and show only:
- Evaluation Setup: Linked in Evaluation Setup / Not linked to evaluation
- Forms & Evidence: Evidence item will be configured in Forms & Evidence / No evidence item required
- Contract Values: May carry into contract values / No contract carry-forward expected

Guidance panel title:
Requirements Guidance

Guidance text:
Focus on what bidders must supply, deliver, integrate, support, or prove. Evaluation scores, price lines, submission checklist items, and contract values are configured in later steps.

Do not show:
scores, marks, pass marks, price lines, implementation phases, inventory tables, actual bidder submissions, evaluation results, contract clause text, SCC values, approval controls, publication controls, hashes, source anchors, rule IDs, schema versions, Tender Shell, or TenderSTDInstance.
```

---

## 15. Cursor Prompt

```text
Refactor Screen 03 as IT Requirements.

Goal:
Let the user define what bidders must supply, deliver, integrate, support, or prove.

Primary object:
IT_Requirement

Required API shape:
{
  configuration_id,
  tender_ref,
  tender_title,
  planning_package_ref,
  wizard_state_label,
  blocker_count,
  warning_count,
  requirements_summary: {
    total_count,
    complete_count,
    needs_attention_count,
    missing_bidder_response_instruction_count,
    missing_evidence_instruction_count,
    missing_acceptance_expectation_count
  },
  requirements: [
    {
      requirement_id,
      display_id,
      title,
      description,
      category,
      treatment,
      bidder_response_format,
      bidder_response_instruction,
      evidence_requirement,
      evidence_instruction,
      acceptance_expectation,
      acceptance_description,
      evidence_status_label,
      acceptance_status_label,
      status_label,
      evaluation_reference_label,
      forms_evidence_reference_label,
      contract_values_reference_label,
      editable,
      route_or_drawer_action
    }
  ]
}

Behavior:
1. Render title "IT Requirements".
2. Render subtitle "Define what bidders must supply, deliver, integrate, support, or prove."
3. Render primary button "Add Requirement".
4. Render secondary actions "Import Requirements Template", "Run Check", and "Continue to Implementation Schedule".
5. Render only approved categories.
6. Render only approved treatment values: Mandatory, Evaluation-linked, Informational.
7. Do not render scoring marks or score percentages.
8. Table columns must be ID, Requirement, Category, Treatment, Bidder Response, Evidence, Acceptance, Status, Actions.
9. Add/edit drawer must include only Requirement, Bidder Response, Evidence, Acceptance, and References sections.
10. References are read-only and light. They must not become configuration forms.
11. Local validation messages must stay requirement-focused.
12. No pricing, scoring, implementation schedule, system inventory, contract values, approval, publication, hashes, source anchors, schema versions, or internal object names may be shown.

Acceptance criteria:
- User can add or edit a requirement without seeing evaluation scores or price data.
- Every requirement has category, treatment, bidder response expectation, evidence expectation, and acceptance expectation.
- Evaluation references are read-only and do not expose marks.
- The screen does not contain price lines, implementation phases, inventory tables, contract clauses, or bidder submissions.
```

---

## 16. Acceptance Checklist

| Test | Pass condition |
|---|---|
| User decision clarity | Screen answers only what bidders must supply, deliver, integrate, support, or prove |
| STD grounding | Anchored to Sections V and VI |
| No scoring leakage | No score, mark, pass mark, or weighting appears |
| No pricing leakage | No price line, quantity, or evaluated price field appears |
| No contract leakage | No SCC value or contract clause editing appears |
| Exact labels | All categories, statuses, and fields are specified |
| Simplicity | Requirement drawer contains only requirement-related fields |
| References | Evaluation, evidence, and contract links are read-only summaries |
