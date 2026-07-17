# IT Tender Wizard Screen 04 — Implementation Schedule

**Project:** KenTender e-Procurement System  
**Module:** IT Tender Configuration Wizard  
**Screen:** 04 — Implementation Schedule  
**Status:** Revised UX specification  
**Design rule:** Delivery schedule only; no project execution, payment certification, inspection records, pricing, scoring, or contract administration.

---

## 1. User Journey

A procurement user opens Implementation Schedule after defining the IT requirements.

The user should define how the solution is expected to be delivered, including delivery approach, milestones, durations, deliverables, and acceptance checkpoints.

This screen is a tender-configuration screen. It is not a project management screen, contract administration screen, inspection screen, payment screen, or evaluation screen.

---

## 2. Single User Decision

> How should the solution be delivered?

Everything on this screen must support that decision.

---

## 3. IT STD Grounding

Primary IT STD anchor:

| IT STD section | Relevance |
|---|---|
| Section VII — Implementation Schedule | Defines the delivery schedule, implementation milestones, deliverables, and acceptance checkpoints that bidders must understand and respond to |

Related but not owned here:

| Related section | Ownership |
|---|---|
| Section V — Requirements of the Information System | Owned by IT Requirements |
| Section VI — Technical Requirements | Owned by IT Requirements |
| Section VIII — System Inventory Tables | Owned by System Inventory |
| Section IV — Price Schedule Forms | Owned by Price Schedule |
| Section III — Evaluation and Qualification Criteria | Owned by Evaluation Setup |
| SCC / Contract Values | Owned by Contract Values |

Do not expose IT STD section numbers as the main user experience. Use task-based labels.

---

## 4. Screen Ownership

| Item | Rule |
|---|---|
| Screen owns | Delivery approach, delivery milestones, expected durations, start triggers, deliverables, acceptance expectations, and delivery evidence expectations |
| Primary object | Implementation Schedule |
| Editable here | Delivery approach, milestone title, sequence, expected duration, start trigger, key deliverable, acceptance expectation, evidence expectation, optional related requirement reference |
| Read-only references | Related IT requirement title, contract carry-forward summary, price schedule reference summary |
| Must not own | Requirement wording, price lines, payment percentages, evaluation scores, actual project progress, inspection records, acceptance certificates, SCC values, contract variations, approval decisions |

Hard rule:

```text
If the user is recording actual delivery progress, certifying completion, defining payment percentages, scoring bidders, or editing contract clauses, they are in the wrong screen.
```

---

## 5. Page Header

### Title

```text
Implementation Schedule
```

### Subtitle

```text
Define how the IT solution should be delivered, accepted, and handed over.
```

### Primary action

```text
Add Milestone
```

Secondary actions:

```text
Use Schedule Template
Run Check
Continue to System Inventory
```

Rules:

- `Continue to System Inventory` is enabled only when there are no schedule blockers.
- Warnings do not block continuation unless policy marks them as blocking.
- Do not show `Finalize`, `Submit for Review`, `Publish`, `Approve`, or `Mark Complete` on this screen.

---

## 6. Delivery Approach

Show one compact section titled:

```text
Delivery Approach
```

The user must choose one approach.

| Option | Exact label | Exact description | Behavior |
|---|---|---|---|
| Phased | `Phased delivery` | `Use when delivery is split into stages such as planning, build, testing, deployment, training, and handover.` | Shows a milestone table with multiple milestones |
| Single | `Single delivery` | `Use when the bidder delivers one complete solution by one expected delivery point.` | Shows one delivery milestone form instead of a phase table |

Do not use this label in the default UI:

```text
Single Turnkey Delivery
```

Use `Single delivery` unless the Procuring Entity explicitly requires the word `turnkey` in issued tender wording.

---

## 7. Behavior When Delivery Approach Changes

### Phased delivery selected

Show the milestone table.

The user may:

```text
Add Milestone
Edit Milestone
Duplicate Milestone
Remove draft milestone
Reorder milestones
```

### Single delivery selected

Hide the multi-milestone table and show one form titled:

```text
Single Delivery Milestone
```

The form uses these exact fields:

```text
Expected Delivery Duration
Delivery Trigger
Key Deliverable
Acceptance Expectation
Evidence Expectation
Related Requirements
```

### Switching from phased delivery to single delivery

If phased milestones already exist, show this confirmation modal:

```text
Switch to Single Delivery?

This will replace the phased schedule with one delivery milestone for the tender package. Existing phased milestones will be kept as draft history and can be restored if you switch back before review.

Cancel
Switch to Single Delivery
```

### Switching from single delivery to phased delivery

If a single delivery milestone already exists, show this confirmation modal:

```text
Switch to Phased Delivery?

This will replace the single delivery milestone with a phased schedule. The current single delivery details will be kept as draft history and can be restored if you switch back before review.

Cancel
Switch to Phased Delivery
```

Do not silently delete user-entered schedule data.

---

## 8. Main Table for Phased Delivery

Show these columns only:

| Column | Exact label | Purpose |
|---|---|---|
| ID | `ID` | Milestone reference |
| Milestone | `Milestone` | Short milestone title |
| Duration | `Duration` | Expected duration for the milestone |
| Starts After | `Starts After` | Trigger or dependency for the milestone |
| Key Deliverable | `Key Deliverable` | Main output expected at the milestone |
| Acceptance | `Acceptance` | Acceptance expectation status |
| Status | `Status` | Milestone completeness |
| Actions | `Actions` | Edit, duplicate, remove where allowed |

Do not show payment percentages, live progress, inspection status, contract clause references, scoring references, or price values in this table.

---

## 9. Sample Rows for Stitch and Cursor

Use these rows as design fixtures only. Production values must come from the API.

| ID | Milestone | Duration | Starts After | Key Deliverable | Acceptance | Status | Action |
|---|---|---|---|---|---|---|---|
| MS-001 | Project planning and mobilisation | 1 month | Contract signing and notice to proceed | Approved project plan and delivery team mobilisation | Acceptance defined | Complete | Edit |
| MS-002 | Build, configuration, and integration | 3 months | Approval of project plan | Configured solution and completed integration setup | Acceptance defined | Complete | Edit |
| MS-003 | Testing and user acceptance | 1 month | Completion of build and integration | Test reports and user acceptance sign-off | Missing evidence | Needs attention | Fix |
| MS-004 | Training and handover | 2 weeks | User acceptance sign-off | Training records, admin handover, and final documentation | Acceptance defined | Complete | Edit |

Single delivery sample:

| Field | Sample value |
|---|---|
| Expected Delivery Duration | `6 months` |
| Delivery Trigger | `Contract signing and notice to proceed` |
| Key Deliverable | `Complete installed, configured, tested, documented, and handed-over IT solution` |
| Acceptance Expectation | `Procuring Entity confirms successful testing, training, documentation, and operational handover` |
| Evidence Expectation | `Completion report, test results, training attendance records, and handover certificate` |
| Status | `Complete` |

---

## 10. Milestone Status Values

Use these values only:

| Value | Meaning |
|---|---|
| Complete | Milestone has duration, trigger, deliverable, acceptance expectation, and evidence expectation where required |
| Needs attention | Required milestone details are missing |
| Draft | Milestone is saved but incomplete |
| Not applicable | Milestone is excluded with a reason |

Do not use:

```text
Ready
Locked
Approved
Submitted
In execution
Completed in field
Accepted
Paid
```

---

## 11. Acceptance Status Values

Use these values only:

| Value | Meaning |
|---|---|
| Acceptance defined | Acceptance expectation is clear |
| Missing acceptance | Acceptance expectation is missing |
| Not applicable | Acceptance is not applicable to this milestone |

---

## 12. Evidence Status Values

Use these values only:

| Value | Meaning |
|---|---|
| Evidence required | Supplier must provide delivery or acceptance evidence |
| Evidence optional | Evidence may be requested but is not mandatory |
| No evidence required | No separate evidence is required |
| Missing evidence | Evidence expectation has not been defined |

---

## 13. Milestone Drawer

Open a drawer or modal when the user creates or edits a milestone.

The drawer must use these sections only.

### Section A — Milestone

| Field | Required | Notes |
|---|---:|---|
| Milestone Title | Yes | Plain user-facing title |
| Milestone Description | Optional | Short explanation of the delivery milestone |
| Sequence | Yes for phased delivery | Integer order in the delivery schedule |
| Expected Duration | Yes | Editable; never locked just because a template filled it |
| Starts After | Yes | Trigger, dependency, or event that starts the milestone |

### Section B — Deliverable

| Field | Required | Notes |
|---|---:|---|
| Key Deliverable | Yes | Main output expected from this milestone |
| Deliverable Details | Optional | Additional detail if needed for bidder clarity |

### Section C — Acceptance

| Field | Required | Allowed values |
|---|---:|---|
| Acceptance Expectation | Yes | Acceptance defined; Not applicable |
| Acceptance Description | Conditional | Required when acceptance is defined |
| Acceptance Responsibility | Optional | Procuring Entity; Joint PE/Supplier; Independent reviewer |

### Section D — Evidence

| Field | Required | Allowed values |
|---|---:|---|
| Evidence Requirement | Yes | Evidence required; Evidence optional; No evidence required |
| Evidence Instruction | Conditional | Required when evidence is required or optional |

### Section E — References

Read-only, light references only:

| Reference | Display text |
|---|---|
| IT Requirements | `Related requirements selected` or `No related requirements selected` |
| Price Schedule | `Price schedule may reference this milestone` or `No price schedule reference yet` |
| Contract Values | `May carry into contract values` or `No contract carry-forward expected` |

Do not allow price configuration, payment percentages, acceptance certification, inspection records, or contract wording inside this drawer.

---

## 14. Template Behavior

Button:

```text
Use Schedule Template
```

Purpose:

```text
Prefill common IT delivery milestones for review and editing.
```

Rules:

- Template-filled values are editable.
- Show plain source text only where useful:

```text
Filled from schedule template
```

- Provide this action only inside the milestone drawer or template review modal:

```text
Reset to template
```

- Never show a realistic duration, deliverable, acceptance rule, site count, or dependency unless it comes from user input, an approved package, or an approved seed fixture.
- If a value is missing, show:

```text
Not configured
```

Do not show unexplained “system generated” or read-only schedule values.

---

## 15. Add Milestone Flow

### Button

```text
Add Milestone
```

### Modal title

```text
Add Delivery Milestone
```

### Default fields

```text
Milestone Title
Milestone Description
Sequence
Expected Duration
Starts After
Key Deliverable
Deliverable Details
Acceptance Expectation
Acceptance Description
Acceptance Responsibility
Evidence Requirement
Evidence Instruction
Related Requirements
```

### Buttons

```text
Cancel
Save Milestone
```

---

## 16. Guidance Panel

Use one compact guidance panel.

### Title

```text
Schedule Guidance
```

### Content

```text
Define the delivery milestones bidders must plan for. Keep the schedule clear enough for bidders to understand timing, deliverables, acceptance expectations, and required delivery evidence.
```

### Summary lines

```text
Milestones needing attention: [count]
Milestones missing duration: [count]
Milestones missing deliverable: [count]
Milestones missing acceptance expectation: [count]
Milestones missing evidence expectation: [count]
```

Do not show technical rule codes or legal diagnostics in this panel.

---

## 17. Validation Behavior

This screen may show local completeness only.

Allowed:

```text
2 milestones need attention
1 milestone missing duration
1 milestone missing acceptance expectation
```

Not allowed:

```text
RULE_IMPL_002 failed
Payment milestone percentage invalid
SCC payment schedule mismatch
Section VII schema invalid
Clause hash mismatch
```

Detailed cross-screen validation belongs in Validation.

---

## 18. Forbidden Content

Do not show or edit:

```text
evaluation marks
score percentages
technical pass marks
price line items
pricing quantities
payment percentages
payment certificates
actual project progress
inspection records
actual delivery status
actual acceptance certificates
supplier performance records
contract variations
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

## 19. Stitch Prompt

```text
Design Screen 04 for the KenTender IT Tender Configuration Wizard.

Screen name:
Implementation Schedule

User goal:
Define how the IT solution should be delivered, accepted, and handed over.

Single user decision:
How should the solution be delivered?

Use this exact subtitle:
Define how the IT solution should be delivered, accepted, and handed over.

Primary button:
Add Milestone

Secondary actions:
- Use Schedule Template
- Run Check
- Continue to System Inventory

Delivery approach section title:
Delivery Approach

Delivery approach options:
1. Phased delivery
Description: Use when delivery is split into stages such as planning, build, testing, deployment, training, and handover.

2. Single delivery
Description: Use when the bidder delivers one complete solution by one expected delivery point.

When Phased delivery is selected, show a milestone table.

Phased delivery table columns:
- ID
- Milestone
- Duration
- Starts After
- Key Deliverable
- Acceptance
- Status
- Actions

Use these sample rows:
- MS-001 | Project planning and mobilisation | 1 month | Contract signing and notice to proceed | Approved project plan and delivery team mobilisation | Acceptance defined | Complete | Edit
- MS-002 | Build, configuration, and integration | 3 months | Approval of project plan | Configured solution and completed integration setup | Acceptance defined | Complete | Edit
- MS-003 | Testing and user acceptance | 1 month | Completion of build and integration | Test reports and user acceptance sign-off | Missing evidence | Needs attention | Fix
- MS-004 | Training and handover | 2 weeks | User acceptance sign-off | Training records, admin handover, and final documentation | Acceptance defined | Complete | Edit

When Single delivery is selected, hide the table and show one form titled:
Single Delivery Milestone

Single delivery fields:
- Expected Delivery Duration
- Delivery Trigger
- Key Deliverable
- Acceptance Expectation
- Evidence Expectation
- Related Requirements

Milestone status values:
- Complete
- Needs attention
- Draft
- Not applicable

Acceptance status values:
- Acceptance defined
- Missing acceptance
- Not applicable

Evidence status values:
- Evidence required
- Evidence optional
- No evidence required
- Missing evidence

Milestone drawer sections:
A. Milestone
B. Deliverable
C. Acceptance
D. Evidence
E. References

Drawer fields:
- Milestone Title
- Milestone Description
- Sequence
- Expected Duration
- Starts After
- Key Deliverable
- Deliverable Details
- Acceptance Expectation
- Acceptance Description
- Acceptance Responsibility
- Evidence Requirement
- Evidence Instruction
- Related Requirements

References section must be read-only and show only:
- IT Requirements: Related requirements selected / No related requirements selected
- Price Schedule: Price schedule may reference this milestone / No price schedule reference yet
- Contract Values: May carry into contract values / No contract carry-forward expected

Guidance panel title:
Schedule Guidance

Guidance text:
Define the delivery milestones bidders must plan for. Keep the schedule clear enough for bidders to understand timing, deliverables, acceptance expectations, and required delivery evidence.

Do not show:
scores, marks, pass marks, price lines, payment percentages, payment certificates, actual project progress, inspection records, actual acceptance certificates, supplier performance records, contract variations, contract clause text, SCC values, approval controls, publication controls, hashes, source anchors, rule IDs, schema versions, Tender Shell, or TenderSTDInstance.
```

---

## 20. Cursor Prompt

```text
Refactor Screen 04 as Implementation Schedule.

Goal:
Let the user define how the IT solution should be delivered, accepted, and handed over.

Primary object:
Implementation_Schedule

Required API shape:
{
  configuration_id,
  tender_ref,
  tender_title,
  planning_package_ref,
  procuring_entity_name,
  procurement_method_label,
  wizard_state_label,
  blocker_count,
  warning_count,
  delivery_approach,
  delivery_approach_label,
  can_continue_to_system_inventory,
  continue_blocker_reason,
  schedule_summary: {
    milestone_count,
    complete_count,
    needs_attention_count,
    missing_duration_count,
    missing_deliverable_count,
    missing_acceptance_expectation_count,
    missing_evidence_expectation_count
  },
  milestones: [
    {
      milestone_id,
      display_id,
      title,
      description,
      sequence,
      expected_duration_value,
      expected_duration_unit,
      starts_after,
      key_deliverable,
      deliverable_details,
      acceptance_expectation,
      acceptance_description,
      acceptance_responsibility,
      evidence_requirement,
      evidence_instruction,
      acceptance_status_label,
      evidence_status_label,
      status_label,
      related_requirements_label,
      price_schedule_reference_label,
      contract_values_reference_label,
      source_label,
      editable,
      route_or_drawer_action
    }
  ],
  single_delivery_milestone: {
    expected_delivery_duration,
    delivery_trigger,
    key_deliverable,
    acceptance_expectation,
    evidence_expectation,
    related_requirements_label,
    status_label
  }
}

Behavior:
1. Render title "Implementation Schedule".
2. Render subtitle "Define how the IT solution should be delivered, accepted, and handed over."
3. Render primary button "Add Milestone".
4. Render secondary actions "Use Schedule Template", "Run Check", and "Continue to System Inventory".
5. Render Delivery Approach with exactly two options: Phased delivery and Single delivery.
6. If delivery_approach is phased, render the milestone table.
7. If delivery_approach is single, render the Single Delivery Milestone form and hide the milestone table.
8. Do not silently delete existing schedule data when the delivery approach changes. Show the required confirmation modal and preserve prior data as draft history.
9. Table columns must be ID, Milestone, Duration, Starts After, Key Deliverable, Acceptance, Status, Actions.
10. Template-filled values must remain editable and may show source_label "Filled from schedule template".
11. Missing values must show "Not configured".
12. Add/edit drawer must include only Milestone, Deliverable, Acceptance, Evidence, and References sections.
13. References are read-only and light. They must not become price, payment, contract, or project execution forms.
14. Local validation messages must stay schedule-focused.
15. No scoring, pricing, payment percentages, payment certificates, project progress, inspection records, acceptance certificates, contract clauses, approval, publication, hashes, source anchors, schema versions, or internal object names may be shown.

Acceptance criteria:
- User can choose phased delivery or single delivery without seeing pricing, scoring, contract, or project execution fields.
- User can add or edit delivery milestones with duration, start trigger, deliverable, acceptance expectation, and evidence expectation.
- Template-filled values are editable and not treated as locked.
- Switching delivery approach requires confirmation and preserves previous schedule data as draft history.
- The screen does not contain price lines, payment percentages, inspection records, actual progress, contract clauses, or bidder evaluation data.
```

---

## 21. Acceptance Checklist

| Test | Pass condition |
|---|---|
| User decision clarity | Screen answers only how the solution should be delivered |
| STD grounding | Anchored to Section VII — Implementation Schedule |
| No project execution leakage | No actual progress, inspection, completion, or acceptance records appear |
| No payment leakage | No payment percentages, certificates, or payment conditions appear |
| No scoring leakage | No score, mark, pass mark, or weighting appears |
| No pricing leakage | No price line, quantity, or evaluated price field appears |
| No contract leakage | No SCC value or contract clause editing appears |
| Exact labels | Delivery approach labels, table columns, drawer sections, statuses, and actions are specified |
| Template behavior | Template-filled values are editable and may be reset to template |
| Single delivery behavior | Single delivery replaces the milestone table with one delivery milestone form |
| Data preservation | Switching approaches does not silently delete prior schedule data |
| Simplicity | Drawer contains only delivery-schedule fields |
| References | Requirements, price schedule, and contract values references are read-only summaries |
