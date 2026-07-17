# IT Tender Wizard Screen 02 — Tender Configuration Home

**Project:** KenTender e-Procurement System  
**Module:** IT Tender Configuration Wizard  
**Screen:** 02 — Tender Configuration Home  
**Status:** Revised UX specification  
**Design rule:** Work plan for one IT Tender Configuration.

---

## 1. User Journey

A procurement user opens one IT Tender Configuration created from an approved procurement package.

The user should immediately understand:

1. What configuration they are working on.
2. Which steps are complete, incomplete, or need attention.
3. The next best step.
4. Where to continue.

This screen is a home page, not a data-entry screen.

---

## 2. Single User Decision

> Which configuration step should I work on next?

Everything on the screen must support that decision.

---

## 3. Lifecycle Position

```text
Approved Procurement Package
→ IT Tender Configuration
→ Configure STD-controlled tender values
```

This screen is the home page for the IT Tender Configuration. It is not the place to create or edit detailed tender content.

---

## 4. IT STD Grounding

This screen is not itself an IT STD content section.

It routes the user into controlled configuration of:

| Step | IT STD anchor |
|---|---|
| Tender Profile | Tender identity and package context; not a standalone STD section |
| Tender Data Sheet | Tender Data Sheet |
| IT Requirements | Section V and Section VI |
| Implementation Schedule | Section VII |
| System Inventory | Section VIII and bidder-context parts of Section IX |
| Price Schedule | Section IV price schedule forms and Section VIII pricing linkage |
| Evaluation Setup | Section III |
| Forms & Evidence | Section IV and linked evidence requirements |
| Contract Values | SCC and contract-specific schedules |
| Validation | Cross-step readiness rules |
| Review & Approval | Governance workflow |
| Final Preview | Generated package from approved configuration |
| Publication Readiness | Handoff to Tender Management |

---

## 5. Screen Ownership

| Item | Rule |
|---|---|
| Screen owns | Step navigation, progress summary, next best action |
| Primary object | IT Tender Configuration Home |
| Editable here | Nothing |
| Actions here | Start, Continue, Fix, Review, Run Validation, Submit for Review, Open Final Preview, Open Publication Readiness |
| Read-only references | Tender Ref, Tender Title, Planning Package Ref, Procuring Entity, Procurement Method, Wizard State, issue count, step statuses |
| Must not own | Tender Profile fields, TDS values, requirements, phases, inventory rows, price lines, evaluation scoring, evidence rules, contract values, approval decisions, publication |

---

## 6. Page Header

### Title

```text
Tender Configuration Home
```

### Subtitle

```text
Complete the required setup steps for this IT tender configuration.
```

### Forbidden titles

```text
STD Configuration Overview
STD Control Center
Tender Model Explorer
Configuration Matrix
```

---

## 7. Context Strip

Show only:

| Field | Exact label |
|---|---|
| Tender Ref | `Tender Ref` |
| Tender Title | `Tender Title` |
| Planning Package Ref | `Planning Package Ref` |
| Procuring Entity | `Procuring Entity` |
| Procurement Method | `Procurement Method` |
| Wizard State | `Wizard State` |
| Issues | `Issues` |

Issue format:

```text
0 Blockers / 2 Warnings
```

Do not show hashes, schema versions, source anchors, rule IDs, STD package codes, or binding IDs.

---

## 8. Next Best Action Panel

Show one prominent panel.

### Format

```text
Next step: [Action + Step Name]
Reason: [Plain reason]
```

### Examples

```text
Next step: Continue IT Requirements
Reason: Required requirement details are still missing.
```

```text
Next step: Start Implementation Schedule
Reason: Requirements are complete enough to define delivery milestones.
```

```text
Next step: Run Validation
Reason: All configuration steps are complete.
```

There must be only one visually dominant primary action.

---

## 9. Step Cards

Each card must use this structure:

```text
[Step number]
[Step name]

[Exact one-line purpose]

Status: [status]
Issues: [count or "None"]
Action: [button]
```

### Allowed statuses

| Status | Meaning |
|---|---|
| Not started | No meaningful work has been done |
| In progress | Work has started but required items remain |
| Needs attention | Blockers, returned corrections, or important warnings require action |
| Complete | Required local setup is complete |
| Not available yet | A prior required step is incomplete |

Do not use `Ready` or `Locked`.

### Allowed card actions

| Action | Use when |
|---|---|
| Start | Step is available and not started |
| Continue | Step is in progress |
| Fix | Step needs attention |
| Review | Step is complete |
| View required step | Step is not available yet |
| Run Validation | Validation is available |
| Submit for Review | Validation passed |
| Open Final Preview | Review approved |
| Open Publication Readiness | Preview confirmed |

---

## 10. Exact Step Card Text

| Step | Card title | Exact purpose text |
|---:|---|---|
| 01 | Tender Profile | Confirm the tender title, scope summary, lot approach, and basic setup context. |
| 02 | Tender Data Sheet | Set tender-specific dates, submission rules, contacts, securities, and participation parameters. |
| 03 | IT Requirements | Define what bidders must supply, deliver, integrate, support, or prove. |
| 04 | Implementation Schedule | Define the delivery approach, milestones, timelines, deliverables, and acceptance checkpoints. |
| 05 | System Inventory | Describe the bidder-relevant environment, inventory, sites, integrations, and disclosure context. |
| 06 | Price Schedule | Define how bidders must price goods, services, recurrent costs, options, and evaluated price items. |
| 07 | Evaluation Setup | Define responsiveness checks, qualification criteria, technical scoring, and financial evaluation rules. |
| 08 | Forms & Evidence | Define the forms, declarations, certificates, documents, and evidence bidders must submit. |
| 09 | Contract Values | Confirm SCC values and tender-specific obligations that must carry into the contract. |
| 10 | Validation | Check whether the configuration is complete, consistent, and ready for review. |
| 11 | Review & Approval | Submit the configuration for formal procurement, technical, and compliance review. |
| 12 | Final Preview | Confirm that the generated tender package matches the approved configuration. |
| 13 | Publication Readiness | Mark the approved package ready for handoff to Tender Management. |

---

## 11. Step Detail Drawer

The drawer must stay lightweight. It must not contain the full configuration form.

### Drawer fields

| Field | Exact label |
|---|---|
| Step name | `Step` |
| Purpose | `Purpose` |
| Status | `Status` |
| Issues | `Issues` |
| Required next action | `Required Next Action` |
| Last updated | `Last Updated` |
| Button | Contextual action |

### Exact drawer content by step

| Step | Purpose | Required Next Action |
|---|---|---|
| Tender Profile | Confirm the tender title, scope summary, lot approach, and basic setup context. | Confirm the basic tender setup before completing the Tender Data Sheet. |
| Tender Data Sheet | Set tender-specific dates, submission rules, contacts, securities, and participation parameters. | Complete missing tender-specific instructions and parameters. |
| IT Requirements | Define what bidders must supply, deliver, integrate, support, or prove. | Add or fix mandatory requirement details. |
| Implementation Schedule | Define the delivery approach, milestones, timelines, deliverables, and acceptance checkpoints. | Define how delivery and acceptance will be structured. |
| System Inventory | Describe the bidder-relevant environment, inventory, sites, integrations, and disclosure context. | Add the environment and inventory context bidders need. |
| Price Schedule | Define how bidders must price goods, services, recurrent costs, options, and evaluated price items. | Complete the pricing structure after requirements and inventory are clear. |
| Evaluation Setup | Define responsiveness checks, qualification criteria, technical scoring, and financial evaluation rules. | Complete the evaluation approach after requirements and price structure are clear. |
| Forms & Evidence | Define the forms, declarations, certificates, documents, and evidence bidders must submit. | Confirm the submission requirements bidders must provide. |
| Contract Values | Confirm SCC values and tender-specific obligations that must carry into the contract. | Confirm the contract values and obligations derived from the configuration. |
| Validation | Check whether the configuration is complete, consistent, and ready for review. | Run validation and resolve blockers before review. |
| Review & Approval | Submit the configuration for formal procurement, technical, and compliance review. | Submit or track the formal review decision. |
| Final Preview | Confirm that the generated tender package matches the approved configuration. | Confirm the final rendered package before publication readiness. |
| Publication Readiness | Mark the approved package ready for handoff to Tender Management. | Confirm readiness and hand the package to Tender Management. |

---

## 12. Forbidden Content

Do not show on this screen:

```text
editable TDS fields
requirement rows
implementation phases
inventory tables
price line items
evaluation marks or pass marks
evidence checklist rows
SCC clauses
contract obligation text
approval decision forms
source-document hashes
clause trees
render-block diagnostics
audit event logs
publication controls
Tender Shell
TenderSTDInstance
STD binding
STD package code
schema version
rule ID
source anchor
```

---

## 13. Stitch Prompt

```text
Design Screen 02 for the KenTender IT Tender Configuration Wizard.

Screen name: Tender Configuration Home
User goal: Understand what remains to be configured for one IT tender configuration and continue the right step.
Single user decision: Which configuration step should I work on next?

Use this exact title:
Tender Configuration Home

Use this exact subtitle:
Complete the required setup steps for this IT tender configuration.

Context strip fields:
- Tender Ref
- Tender Title
- Planning Package Ref
- Procuring Entity
- Procurement Method
- Wizard State
- Issues

Show one Next step panel using:
Next step: [Action + Step Name]
Reason: [Plain reason]

Use these exact step cards:
01 Tender Profile — Confirm the tender title, scope summary, lot approach, and basic setup context.
02 Tender Data Sheet — Set tender-specific dates, submission rules, contacts, securities, and participation parameters.
03 IT Requirements — Define what bidders must supply, deliver, integrate, support, or prove.
04 Implementation Schedule — Define the delivery approach, milestones, timelines, deliverables, and acceptance checkpoints.
05 System Inventory — Describe the bidder-relevant environment, inventory, sites, integrations, and disclosure context.
06 Price Schedule — Define how bidders must price goods, services, recurrent costs, options, and evaluated price items.
07 Evaluation Setup — Define responsiveness checks, qualification criteria, technical scoring, and financial evaluation rules.
08 Forms & Evidence — Define the forms, declarations, certificates, documents, and evidence bidders must submit.
09 Contract Values — Confirm SCC values and tender-specific obligations that must carry into the contract.
10 Validation — Check whether the configuration is complete, consistent, and ready for review.
11 Review & Approval — Submit the configuration for formal procurement, technical, and compliance review.
12 Final Preview — Confirm that the generated tender package matches the approved configuration.
13 Publication Readiness — Mark the approved package ready for handoff to Tender Management.

Allowed status labels:
- Not started
- In progress
- Needs attention
- Complete
- Not available yet

Do not use Ready or Locked.

Allowed card actions:
- Start
- Continue
- Fix
- Review
- View required step
- Run Validation
- Submit for Review
- Open Final Preview
- Open Publication Readiness

Do not show detailed configuration data, legal metadata, internal object names, hashes, schema versions, clause trees, render diagnostics, audit logs, or publication controls.
```

---

## 14. Cursor Prompt

```text
Refactor Screen 02 as Tender Configuration Home.

Goal:
Help the user decide which configuration step to work on next.

Primary object:
IT_Tender_Configuration_Home

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
  next_step_key,
  next_step_action_label,
  next_step_label,
  next_step_reason,
  steps: [
    {
      step_number,
      step_key,
      step_label,
      purpose_text,
      status_label,
      blocker_count,
      warning_count,
      required_next_action_text,
      last_updated_at,
      last_updated_by,
      action_label,
      route
    }
  ]
}

Behavior:
1. Render title "Tender Configuration Home".
2. Render subtitle "Complete the required setup steps for this IT tender configuration."
3. Render context strip with Tender Ref, Tender Title, Planning Package Ref, Procuring Entity, Procurement Method, Wizard State, Issues.
4. Render one Next step panel only.
5. Render exactly 13 step cards in this order:
   - Tender Profile
   - Tender Data Sheet
   - IT Requirements
   - Implementation Schedule
   - System Inventory
   - Price Schedule
   - Evaluation Setup
   - Forms & Evidence
   - Contract Values
   - Validation
   - Review & Approval
   - Final Preview
   - Publication Readiness
6. Use only approved status labels:
   - Not started
   - In progress
   - Needs attention
   - Complete
   - Not available yet
7. Do not use Ready or Locked.
8. The step drawer must show only Step, Purpose, Status, Issues, Required Next Action, Last Updated, and contextual action.
9. Do not render any detailed configuration fields on this screen.
10. Do not render internal system terms or diagnostic metadata.

Acceptance criteria:
- User can identify the next step in under 10 seconds.
- Tender Profile appears as Step 01.
- There is exactly one primary action emphasis.
- No step card uses Ready or Locked.
- No detailed configuration fields appear.
- Every step links to its owning screen.
```

---

## 15. Acceptance Checklist

| Test | Pass condition |
|---|---|
| Lifecycle correctness | Screen represents one IT Tender Configuration created from an Approved Procurement Package |
| Tender Profile retained | Tender Profile appears as Step 01 |
| Decision clarity | User can tell which step to work on next |
| Status clarity | No Ready or Locked labels appear |
| Exact text | Every card and drawer purpose has exact wording |
| Simplicity | No detailed configuration data appears |
| Ownership | Screen owns navigation and progress only |
