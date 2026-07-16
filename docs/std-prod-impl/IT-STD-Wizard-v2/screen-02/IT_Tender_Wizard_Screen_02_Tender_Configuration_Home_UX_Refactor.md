# IT Tender Wizard Screen 02 — Tender Configuration Home UX Refactor

**Project:** KenTender e-Procurement System  
**Module:** IT Tender Configuration Wizard  
**Screen:** 02 — Tender Configuration Home  
**Status:** UX refactor specification  
**Design mode:** Simplification-first  

---

## 1. User Journey

A procurement user opens one selected IT tender configuration after choosing it from the dashboard.

The user should immediately understand:

1. What tender they are configuring.
2. Which configuration steps are complete, incomplete, or need attention.
3. What the next best action is.
4. Where to continue.

This screen is a **configuration home page**, not a data-entry screen.

---

## 2. Single User Decision

> Which configuration step should I work on next?

Everything on the screen must support that decision.

---

## 3. IT STD Grounding

This screen is not itself an IT STD content section. It is the navigation and progress screen for configuring the tender-specific parts of the IT Standard Tender Document.

It routes the user into controlled configuration of:

- Tender Data Sheet;
- Section III — Evaluation and Qualification Criteria;
- Section IV — Tendering Forms;
- Section V — Requirements of the Information System;
- Section VI — Technical Requirements;
- Section VII — Implementation Schedule;
- Section VIII — System Inventory Tables;
- Section IX — Background and Informational Materials;
- SCC / contract-specific values.

The screen must not expose the full legal structure. It should show simple steps that correspond to user tasks.

---

## 4. Screen Ownership

| Item | Decision |
|---|---|
| Screen owns | Step navigation, progress summary, next action |
| Primary object | `TenderSTDConfigurationHome` |
| Editable here | Nothing except optional note/view preference if later approved |
| Actions here | Continue step, open step, run validation, submit for review when eligible |
| Read-only references | Tender Ref, Tender Title, Planning Package Ref, Procuring Entity, Procurement Method, Wizard State, issue count, step statuses |
| Must not own | TDS values, requirements, schedule details, inventory rows, price lines, evaluation scoring, evidence rules, SCC values, approval decision content, publication |

---

## 5. Default Layout

### Header

Title:

```text
Tender Configuration Home
```

Subtitle:

```text
Complete the required setup steps for this IT tender configuration.
```

Do not use:

```text
STD Configuration Overview
STD Control Center
Configuration Matrix
Tender Model Explorer
```

---

### Tender Context Strip

Show only these fields:

| Field | Rule |
|---|---|
| Tender Ref | Read-only |
| Tender Title | Read-only or editable only if owned by Tender Profile |
| Planning Package Ref | Read-only |
| Procuring Entity | Read-only |
| Procurement Method | Read-only label, for example `Open National Tender` |
| Wizard State | Human-readable label |
| Issues | Simple count only, for example `0 Blockers / 2 Warnings` |

Do not show STD hashes, rule IDs, source anchors, schema versions, or technical package metadata.

---

### Next Best Action

Show one prominent next-action panel.

Example:

```text
Next step: Continue IT Requirements
Reason: Required requirement details are still missing.
```

Allowed actions:

```text
Start Step
Continue Step
Review Step
Fix Blockers
Run Validation
Submit for Review
Open Final Preview
Open Publication Readiness
```

Do not show multiple competing primary actions.

---

### Configuration Steps

Use a simple checklist or card list.

Recommended columns per step:

| Field | Example |
|---|---|
| Step | IT Requirements |
| Purpose | Define what bidders must supply or satisfy |
| Status | Not started / In progress / Complete / Needs attention |
| Issues | `0 Blockers / 1 Warning` or blank |
| Action | Start / Continue / Review |

Recommended step list:

| Step | User purpose |
|---|---|
| Tender Data Sheet | Set tender-specific rules, dates, submission details, and basic parameters |
| IT Requirements | Define what bidders must supply or satisfy |
| Implementation Schedule | Define how the project will be delivered |
| System Inventory | Describe the bidder-relevant environment and inventory context |
| Price Schedule | Define how bidders price the tender |
| Evaluation Setup | Define how bids will be evaluated |
| Forms & Evidence | Define what bidders must submit |
| SCC / Contract Values | Confirm tender-specific contract values and obligations |
| Validation | Check whether the configuration is ready |
| Review & Approval | Submit and track formal review |
| Final Preview | Confirm the generated tender package |
| Publication Readiness | Hand the package to Tender Management |

Keep the wording task-based, not STD-section-based.

---

## 6. Step Status Labels

Use calm labels:

| Status | Meaning |
|---|---|
| Not started | User has not configured the step |
| In progress | User has started but required items remain |
| Complete | Required local setup is complete |
| Needs attention | Blockers or returned corrections exist |
| Locked | Step cannot begin until earlier dependency is met |
| Ready | Step can now be opened |

Avoid raw enum labels in the default UI.

---

## 7. Validation Behavior

This screen may show only summary-level validation.

Allowed:

```text
0 Blockers / 2 Warnings
Needs attention
Ready for review
```

Not allowed:

```text
RULE_EVAL_003 failed
Missing render block ITT_36
Clause hash mismatch
Section VIII schema invalid
```

Detailed findings belong in the Validation Report screen.

---

## 8. Forbidden Complexity

Do not show on this screen:

- editable TDS fields;
- requirement rows;
- implementation phases;
- inventory tables;
- price line items;
- evaluation marks, weights, or pass marks;
- evidence checklist rows;
- SCC clauses or contract obligation text;
- approval decision forms;
- source-document hashes;
- clause trees;
- render-block diagnostics;
- audit event logs;
- publication controls.

This screen is orientation and navigation only.

---

## 9. Drawer / Details Behavior

A step may have a lightweight details drawer.

Allowed drawer content:

- step purpose;
- owner screen;
- status;
- blocker/warning count;
- last updated;
- primary action;
- link to Validation Report if issues exist.

Do not put full step configuration inside the drawer.

---

## 10. Stitch Prompt

```text
Design Screen 02 for the KenTender IT Tender Configuration Wizard.

Screen name: Tender Configuration Home
User goal: Understand what remains to be configured for one selected IT tender and continue the right step.
Single user decision: Which configuration step should I work on next?

Keep the screen simple. This is a home page for one configuration, not a data-entry screen.

Use this layout:
1. Page title: "Tender Configuration Home".
2. Subtitle: "Complete the required setup steps for this IT tender configuration."
3. Tender context strip with only:
   - Tender Ref
   - Tender Title
   - Planning Package Ref
   - Procuring Entity
   - Procurement Method
   - Wizard State
   - Issues
4. One prominent "Next step" panel.
5. A simple configuration checklist/card list.

Configuration steps:
- Tender Data Sheet — Set tender-specific rules, dates, submission details, and basic parameters.
- IT Requirements — Define what bidders must supply or satisfy.
- Implementation Schedule — Define how the project will be delivered.
- System Inventory — Describe the bidder-relevant environment and inventory context.
- Price Schedule — Define how bidders price the tender.
- Evaluation Setup — Define how bids will be evaluated.
- Forms & Evidence — Define what bidders must submit.
- SCC / Contract Values — Confirm tender-specific contract values and obligations.
- Validation — Check whether the configuration is ready.
- Review & Approval — Submit and track formal review.
- Final Preview — Confirm the generated tender package.
- Publication Readiness — Hand the package to Tender Management.

Each step card should show only:
- Step name
- One-line purpose
- Status
- Issue count if any
- One action: Start, Continue, Review, or Fix

Allowed status labels:
- Not started
- In progress
- Complete
- Needs attention
- Locked
- Ready

Do not show editable TDS fields, requirements, phases, inventory rows, price lines, evaluation marks, evidence rows, SCC values, approval forms, hashes, clause trees, render diagnostics, audit logs, or publication controls.

If a user opens step details, use a lightweight drawer with step purpose, status, issue count, last updated, and action. Do not place the full configuration form inside the drawer.
```

---

## 11. Cursor Prompt

```text
Refactor Screen 02 of the IT Tender Configuration Wizard as a focused Tender Configuration Home.

Goal:
Help the user decide which configuration step to work on next.

Primary object:
TenderSTDConfigurationHome

Required API shape:
{
  configuration_id,
  tender_ref,
  tender_title,
  planning_package_ref,
  procuring_entity_name,
  procurement_method_label,
  wizard_state,
  wizard_state_label,
  blocker_count,
  warning_count,
  next_step_key,
  next_step_label,
  next_step_reason,
  steps: [
    {
      step_key,
      step_label,
      purpose,
      status,
      status_label,
      blocker_count,
      warning_count,
      locked,
      lock_reason,
      last_updated_at,
      action_label,
      route
    }
  ]
}

Screen behavior:
1. Render title: Tender Configuration Home.
2. Render tender context strip with Tender Ref, Tender Title, Planning Package Ref, Procuring Entity, Procurement Method, Wizard State, and Issues only.
3. Render one Next Step panel using next_step_label and next_step_reason.
4. Render configuration steps as checklist/cards.
5. Each step shows only label, purpose, status, issue count, and one action.
6. Clicking a step action navigates to that owning screen.
7. Step details drawer, if used, must stay lightweight and must not contain the full configuration form.

Rules:
- This screen owns navigation, progress, and next action only.
- Do not render editable configuration fields here.
- Do not render detailed validation findings here.
- Do not render STD hashes, source anchors, clause trees, render diagnostics, schema metadata, or audit events.
- Do not show scoring marks, price lines, SCC clauses, requirements, inventory rows, or implementation phases.
- Use human-readable labels, not raw enum names.
- If a step is locked, show a short lock reason and the dependency step.
- No hardcoded realistic values outside approved seed fixtures.

Acceptance criteria:
- A user can identify the next step in under 10 seconds.
- The screen has exactly one primary action emphasis: the next best action.
- No detailed configuration fields appear on this screen.
- Every step links to its owning screen.
- Validation remains summary-level only.
```

---

## 12. Acceptance Checklist

| Test | Pass condition |
|---|---|
| User decision clarity | User can tell what to work on next. |
| STD grounding | Screen routes to IT STD-controlled configuration sections without exposing legal complexity. |
| Ownership clarity | Screen owns navigation and progress only. |
| Simplicity | No detailed configuration data appears. |
| No magical values | All displayed values come from the configuration home API or explicit seed fixtures. |
| Validation calmness | Only blocker/warning counts appear. |
| Step routing | Every step action opens the owning screen. |
| Progressive disclosure | Step drawer is light and does not become a hidden data-entry form. |

---

## 13. Final Rule

If a field does not help the user decide which configuration step to work on next, remove it from Screen 02.
