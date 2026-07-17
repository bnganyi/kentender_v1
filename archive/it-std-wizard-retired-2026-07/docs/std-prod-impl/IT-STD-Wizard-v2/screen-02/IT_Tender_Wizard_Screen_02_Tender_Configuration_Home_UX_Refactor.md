# IT Tender Wizard Screen 02 — Tender Configuration Home UX Refactor

**Project:** KenTender e-Procurement System  
**Module:** IT Tender Configuration Wizard  
**Screen:** 02 — Tender Configuration Home  
**Status:** Revised UX requirements  
**Design mode:** Simplicity-first, user-decision-first  

---

## 1. Purpose

This screen helps a procurement user continue configuring one selected IT tender.

It is a **home page and work plan**, not a configuration form, legal model viewer, validation report, approval screen, or workflow dashboard.

---

## 2. Single User Decision

> Which configuration step should I work on next?

Every visible element must support that decision.

---

## 3. Correction: Tender Profile Is Retained

**Tender Profile was not intentionally dropped.** It remains the first configuration step because the user still needs a focused place to confirm the tender identity, scope summary, lot structure, and basic participation settings before completing the Tender Data Sheet.

Screen numbering and configuration-step numbering are different:

| Type | Meaning |
|---|---|
| Screen 02 | The home/work-plan page for one IT tender configuration |
| Configuration Step 01 | Tender Profile |
| Configuration Step 02 | Tender Data Sheet |

Tender Profile must not be merged into Tender Data Sheet. Tender Profile answers **“What tender am I configuring?”** Tender Data Sheet answers **“What tender-specific instructions and parameters apply?”**

---

## 4. IT STD Grounding

Screen 02 is not itself an IT STD section. It routes the user into focused configuration steps that produce the tender-specific parts of the IT Standard Tender Document.

| Configuration step | IT STD / workflow grounding |
|---|---|
| Tender Profile | Tender shell/context used to identify the tender configuration; prepares the user for TDS configuration but is not a legal clause-editing screen |
| Tender Data Sheet | Tender Data Sheet values that customize ITT instructions |
| IT Requirements | Section V — Requirements of the Information System; Section VI — Technical Requirements |
| Implementation Schedule | Section VII — Implementation Schedule |
| System Inventory | Section VIII — System Inventory Tables; Section IX only for bidder background context |
| Price Schedule | Section IV — Tendering Forms / Price Schedule forms, informed by inventory and requirements |
| Evaluation Setup | Section III — Evaluation and Qualification Criteria |
| Forms & Evidence | Section IV — Tendering Forms and bidder submission requirements |
| SCC / Contract Values | Special Conditions of Contract and contract-specific tender values |
| Validation | Cross-check that the configured tender package is complete and internally consistent |
| Review & Approval | Governance review of the Tender STD Configuration, not tender publication |
| Final Preview | Read-only preview of the generated tender package |
| Publication Readiness | Handoff to Tender Management publication workflow |

Do not expose legal clause trees, hashes, rule IDs, schema internals, source anchors, or render diagnostics on this screen.

---

## 5. Screen Ownership

| Item | Requirement |
|---|---|
| Screen owns | Navigation, step progress, next best action |
| Primary object | `TenderSTDConfigurationHome` |
| Editable here | Nothing |
| Permitted actions | Open step, continue step, fix step, review step, run validation when eligible, submit for review when eligible |
| Read-only context | Tender Ref, Tender Title, Planning Package Ref, Procuring Entity, Procurement Method, Wizard State, issue summary |
| Must not own | Tender Profile fields, TDS values, requirements, schedule rows, inventory rows, price lines, scoring, evidence rules, SCC values, approvals, publication |

---

## 6. Status Model

Use exactly these status labels on step cards:

| Status | Meaning | Button label |
|---|---|---|
| Not started | The user has not entered meaningful configuration for this step | Start |
| In progress | The user has started the step but required items remain incomplete | Continue |
| Needs attention | The step has blockers or returned corrections | Fix |
| Complete | The step is complete enough to proceed | Review |
| Available later | The step depends on an earlier step that is not yet sufficiently complete | View dependency |

Do **not** use these labels on Screen 02:

| Forbidden label | Reason |
|---|---|
| Locked | Confuses sequencing with legal/governance lock. Reserve “locked” for approved, published, or legally immutable content. |
| Ready | Ambiguous. It does not say ready for editing, review, validation, preview, or publication. |

---

## 7. Page Layout

### 7.1 Header

**Title:**

```text
Tender Configuration Home
```

**Subtitle:**

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

### 7.2 Tender Context Strip

Show only these fields:

| Field label | Example value | Rule |
|---|---|---|
| Tender Ref | `IT-2026-0007` | Read-only |
| Tender Title | `Enterprise Resource Planning System` | Read-only here; edit only in Tender Profile if supported |
| Planning Package Ref | `PP-2026-0142` | Read-only |
| Procuring Entity | `National Social Security Fund` | Read-only |
| Procurement Method | `Open National Tender` | Read-only |
| Wizard State | `In configuration` | Human-readable label, not enum |
| Issues | `2 Blockers / 1 Warning` | Summary count only |

Do not show STD hashes, schema versions, source anchors, rule IDs, package internals, or audit metadata.

### 7.3 Next Best Action Panel

Show exactly one prominent next-action panel.

**Format:**

```text
Next step: [action + step name]
Reason: [plain-language reason]
[Primary action button]
```

**Examples:**

```text
Next step: Start Tender Profile
Reason: Confirm the tender identity and scope before configuring tender instructions.
[Start Tender Profile]
```

```text
Next step: Fix IT Requirements
Reason: Two required requirements are missing bidder response instructions.
[Fix IT Requirements]
```

```text
Next step: Run Validation
Reason: All configuration steps are complete.
[Run Validation]
```

Do not show multiple competing primary actions.

---

## 8. Configuration Step Cards

Each card must show exactly:

1. Step number;
2. Step name;
3. Exact user-facing description from Section 9;
4. Status;
5. Issue count if non-zero;
6. Availability reason if status is `Available later`;
7. One action button.

No card may show detailed records, table rows, scoring marks, prices, requirement text, SCC values, validation rule codes, hashes, source anchors, or audit details.

---

## 9. Exact Step Card Content

Use these step names and descriptions exactly unless a future approved design change updates this document.

| Step | Step name | Exact card description | Availability rule |
|---:|---|---|---|
| 01 | Tender Profile | Confirm the tender title, scope summary, lot structure, participation settings, and basic context for this IT tender configuration. | Available immediately after the tender configuration is created. |
| 02 | Tender Data Sheet | Set tender-specific dates, submission rules, contacts, securities, currency, language, and other tender parameters. | Available after Tender Profile is started. |
| 03 | IT Requirements | Define the functional, technical, security, integration, support, warranty, deliverable, and acceptance requirements bidders must respond to. | Available after Tender Profile is started. |
| 04 | Implementation Schedule | Define whether delivery is phased or single-turnkey, then set delivery milestones, expected durations, deliverables, and acceptance checkpoints. | Available after IT Requirements are sufficiently defined. |
| 05 | System Inventory | Describe bidder-relevant existing systems, sites, users, integrations, data, infrastructure, licenses, and background context needed to understand the tender. | Available after IT Requirements are sufficiently defined. |
| 06 | Price Schedule | Define how bidders must price supply, installation, services, recurrent costs, optional items, taxes, currency, quantities, and evaluated price components. | Available after IT Requirements and System Inventory are sufficiently defined. |
| 07 | Evaluation Setup | Define responsiveness checks, qualification criteria, technical scoring, financial evaluation method, pass marks, preferences, and post-qualification rules. | Available after IT Requirements and Price Schedule are sufficiently defined. |
| 08 | Forms & Evidence | Define the forms, declarations, certificates, technical evidence, financial forms, and supporting documents bidders must submit. | Available after Tender Data Sheet, IT Requirements, and Evaluation Setup are sufficiently defined. |
| 09 | SCC / Contract Values | Confirm tender-specific contract values, SCC parameters, delivery obligations, warranty/support obligations, acceptance obligations, and contract attachments. | Available after Implementation Schedule, Price Schedule, Forms & Evidence, and Evaluation Setup are sufficiently defined. |
| 10 | Validation | Check whether the configured tender package is complete, internally consistent, and ready for formal review. | Available after all configuration steps are complete enough to validate. |
| 11 | Review & Approval | Submit the Tender STD Configuration for procurement, technical, legal/compliance, and final configuration review. | Available after validation has no blockers. |
| 12 | Final Preview | Review the generated tender package exactly as it will be handed forward, without editing configuration content on this screen. | Available after the configuration is approved for render. |
| 13 | Publication Readiness | Confirm that the approved and preview-confirmed package is ready to hand over to Tender Management for publication workflow. | Available after Final Preview is confirmed. |

---

## 10. Card Detail Drawer

A step card may open a lightweight drawer.

The drawer must answer only:

1. What is this step for?
2. What will the user configure there?
3. Why is the step available or unavailable?
4. What is the next action?

The drawer must not contain the full configuration form.

### 10.1 Drawer Fields

| Field | Requirement |
|---|---|
| Step name | Exact step name from Section 9 |
| Purpose | Exact drawer purpose from Section 10.2 |
| Configure there | Exact bullet list from Section 10.2 |
| Status | One of the five approved status labels |
| Issues | Summary only, for example `2 Blockers / 1 Warning`; omit if zero |
| Availability | Plain-language reason when status is `Available later` |
| Last updated | Show only if real data exists; otherwise omit |
| Primary action | Start / Continue / Fix / Review / View dependency |

### 10.2 Exact Drawer Content

| Step | Drawer purpose | Configure there |
|---:|---|---|
| 01 | Confirm the basic identity and scope of the IT tender before detailed STD configuration begins. | Tender display title; scope summary; lot structure; alternatives setting; joint venture setting; reserved procurement setting where applicable; tender security applicability indicator; basic participation context. |
| 02 | Set the tender-specific data that customizes the standard IT tender instructions. | Dates and deadlines; clarification rules; submission rules; tender security settings; contact details; currency and language; preference/reservation applicability where allowed. |
| 03 | Define what bidders must supply, implement, support, prove, and satisfy. | Functional requirements; technical requirements; security and compliance requirements; integration requirements; support and warranty requirements; deliverables; bidder response expectations; evidence instructions; acceptance criteria. |
| 04 | Define how the IT solution will be delivered. | Delivery approach; phased or single-turnkey delivery; milestones; expected durations; start triggers; deliverables; acceptance checkpoints; delivery evidence. |
| 05 | Provide the bidder-relevant context needed to understand the existing environment and scope. | Existing systems; sites and locations; user groups; integrations; data migration context; infrastructure context; licensing/support context; security disclosure context; background information. |
| 06 | Define how bidders must price the tender in a comparable way. | Supply and installation prices; recurrent costs; optional items; quantities and units; pricing basis; taxes and currency; evaluated price inclusion; bidder pricing instructions. |
| 07 | Define how bids will be assessed. | Preliminary responsiveness; eligibility and qualification checks; technical criteria; scoring weights; pass marks; financial evaluation method; preferences/reservations; post-qualification checks. |
| 08 | Define what bidders must submit with their bids. | Standard forms; declarations; eligibility evidence; qualification evidence; technical evidence; implementation evidence; financial forms; conditional or optional submissions. |
| 09 | Confirm which configured tender values become contract-facing obligations. | SCC parameters; delivery obligations; technical obligations; support and warranty obligations; acceptance obligations; contract schedules; contract attachments. |
| 10 | Check whether the tender configuration is complete and internally consistent. | Blockers; warnings; missing required values; inconsistent cross-links; readiness summary; links back to owning screens. |
| 11 | Route the completed configuration through formal review. | Reviewer stages; submitted package summary; reviewer comments; return reasons; approval status; review history. |
| 12 | Confirm the generated tender package before publication readiness. | Rendered tender document; generated schedules; generated forms; configuration comparison summary; preview confirmation checklist. |
| 13 | Mark the package ready for handoff to Tender Management. | Publication-readiness checklist; final package contents; handoff summary; next owner; Tender Management handoff action. |

---

## 11. Action Rules

| Situation | Next Best Action label | Button label |
|---|---|---|
| A step has blockers | `Fix [Step Name]` | Fix |
| A step is in progress without blockers | `Continue [Step Name]` | Continue |
| A step has not started and is available | `Start [Step Name]` | Start |
| A step is complete | `Review [Step Name]` | Review |
| A step is unavailable due to dependency | `Complete [Dependency Step] first` | View dependency |
| All configuration steps complete | `Run Validation` | Run Validation |
| Validation passed | `Submit for Review` | Submit for Review |
| Review approved | `Open Final Preview` | Open Final Preview |
| Final Preview confirmed | `Open Publication Readiness` | Open Publication Readiness |

Do not show `Finalize Configuration` on this screen.

---

## 12. Validation Behavior

Screen 02 may show only summary-level validation.

Allowed:

```text
2 Blockers / 1 Warning
Needs attention
Validation passed
```

Not allowed:

```text
RULE_EVAL_003 failed
Missing render block ITT_36
Clause hash mismatch
Section VIII schema invalid
```

Detailed findings belong only in the Validation screen.

---

## 13. Forbidden Content

Do not show on Screen 02:

- editable Tender Profile fields;
- editable TDS fields;
- requirement rows;
- implementation phases;
- inventory rows;
- price line items;
- evaluation marks, weights, pass marks, or scoring formulas;
- evidence checklist rows;
- SCC clauses or contract obligation text;
- approval decision forms;
- source-document hashes;
- clause trees;
- render-block diagnostics;
- audit event logs;
- publication controls.

---

## 14. Required API Shape

```json
{
  "configuration_id": "string",
  "tender_ref": "string",
  "tender_title": "string",
  "planning_package_ref": "string",
  "procuring_entity_name": "string",
  "procurement_method_label": "string",
  "wizard_state_label": "string",
  "blocker_count": 0,
  "warning_count": 0,
  "next_action": {
    "label": "Start Tender Profile",
    "reason": "Confirm the tender identity and scope before configuring tender instructions.",
    "button_label": "Start Tender Profile",
    "route": "/it-tender-wizard/{configuration_id}/profile"
  },
  "steps": [
    {
      "step_number": 1,
      "step_key": "tender_profile",
      "step_label": "Tender Profile",
      "card_description": "Confirm the tender title, scope summary, lot structure, participation settings, and basic context for this IT tender configuration.",
      "drawer_purpose": "Confirm the basic identity and scope of the IT tender before detailed STD configuration begins.",
      "configure_there": [
        "Tender display title",
        "Scope summary",
        "Lot structure",
        "Alternatives setting",
        "Joint venture setting",
        "Reserved procurement setting where applicable",
        "Tender security applicability indicator",
        "Basic participation context"
      ],
      "status_label": "Not started",
      "blocker_count": 0,
      "warning_count": 0,
      "availability_reason": null,
      "last_updated_at": null,
      "action_label": "Start",
      "route": "/it-tender-wizard/{configuration_id}/profile"
    }
  ]
}
```

Implementation note: use `status_label = "Available later"` and `availability_reason = "Complete IT Requirements first."` instead of `locked = true` or `lock_reason`.

---

## 15. Stitch Prompt

```text
Design Screen 02 for the KenTender IT Tender Configuration Wizard.

Screen name:
Tender Configuration Home

User goal:
Help a procurement user continue configuring one selected IT tender.

Single user decision:
Which configuration step should I work on next?

Design principle:
This is a home page and work plan, not a configuration form, validation report, legal model viewer, or workflow engine dashboard.

Page header:
Title: Tender Configuration Home
Subtitle: Complete the required setup steps for this IT tender configuration.

Tender context strip:
Show only these fields:
- Tender Ref
- Tender Title
- Planning Package Ref
- Procuring Entity
- Procurement Method
- Wizard State
- Issues

Next Best Action panel:
Show exactly one prominent next action using this format:
Next step: [action + step name]
Reason: [plain-language reason]
Primary button: [same action]

Use only these status labels:
- Not started
- In progress
- Needs attention
- Complete
- Available later

Do not use:
- Locked
- Ready
- Finalize Configuration

Step cards:
Each card must show only:
- Step number
- Step name
- Exact card description
- Status
- Issue count if non-zero
- Availability reason if status is Available later
- One action button

Exact step card content:
01 Tender Profile — Confirm the tender title, scope summary, lot structure, participation settings, and basic context for this IT tender configuration.
02 Tender Data Sheet — Set tender-specific dates, submission rules, contacts, securities, currency, language, and other tender parameters.
03 IT Requirements — Define the functional, technical, security, integration, support, warranty, deliverable, and acceptance requirements bidders must respond to.
04 Implementation Schedule — Define whether delivery is phased or single-turnkey, then set delivery milestones, expected durations, deliverables, and acceptance checkpoints.
05 System Inventory — Describe bidder-relevant existing systems, sites, users, integrations, data, infrastructure, licenses, and background context needed to understand the tender.
06 Price Schedule — Define how bidders must price supply, installation, services, recurrent costs, optional items, taxes, currency, quantities, and evaluated price components.
07 Evaluation Setup — Define responsiveness checks, qualification criteria, technical scoring, financial evaluation method, pass marks, preferences, and post-qualification rules.
08 Forms & Evidence — Define the forms, declarations, certificates, technical evidence, financial forms, and supporting documents bidders must submit.
09 SCC / Contract Values — Confirm tender-specific contract values, SCC parameters, delivery obligations, warranty/support obligations, acceptance obligations, and contract attachments.
10 Validation — Check whether the configured tender package is complete, internally consistent, and ready for formal review.
11 Review & Approval — Submit the Tender STD Configuration for procurement, technical, legal/compliance, and final configuration review.
12 Final Preview — Review the generated tender package exactly as it will be handed forward, without editing configuration content on this screen.
13 Publication Readiness — Confirm that the approved and preview-confirmed package is ready to hand over to Tender Management for publication workflow.

Button labels:
- Start
- Continue
- Fix
- Review
- View dependency
- Run Validation
- Submit for Review
- Open Final Preview
- Open Publication Readiness

Step detail drawer:
The drawer must stay lightweight. It may show:
- Step name
- Purpose
- What the user configures there
- Status
- Issue count
- Availability reason
- Last updated if real data exists
- One primary action

Do not put the full configuration form inside the drawer.
Do not show editable Tender Profile fields, editable TDS fields, requirements, implementation phases, inventory rows, price lines, evaluation marks, evidence rows, SCC values, approval forms, hashes, clause trees, render diagnostics, audit logs, or publication controls.
```

---

## 16. Cursor Prompt

```text
Refactor Screen 02 of the IT Tender Configuration Wizard as a focused Tender Configuration Home.

Goal:
Help the user decide which configuration step to work on next.

Primary object:
TenderSTDConfigurationHome

Hard rules:
1. This screen owns navigation, progress, and next best action only.
2. It must not render editable configuration fields.
3. It must not render detailed validation findings.
4. It must not render STD hashes, source anchors, clause trees, schema metadata, render diagnostics, or audit events.
5. It must not render scoring marks, price lines, SCC clauses, Tender Profile fields, TDS values, requirement rows, inventory rows, or implementation phases.
6. Use exact labels and descriptions from this specification.
7. Do not use status labels Locked or Ready.
8. Do not use a Finalize Configuration button.
9. Use Available later for dependency sequencing.
10. Every step action must navigate to the owning screen.

Required UI:
- Page title: Tender Configuration Home
- Subtitle: Complete the required setup steps for this IT tender configuration.
- Context strip: Tender Ref, Tender Title, Planning Package Ref, Procuring Entity, Procurement Method, Wizard State, Issues.
- One Next Best Action panel.
- Configuration step cards using the exact step content from this specification.
- Optional lightweight step detail drawer.

Status labels:
- Not started
- In progress
- Needs attention
- Complete
- Available later

API contract:
Return a TenderSTDConfigurationHome object with:
- configuration_id
- tender_ref
- tender_title
- planning_package_ref
- procuring_entity_name
- procurement_method_label
- wizard_state_label
- blocker_count
- warning_count
- next_action { label, reason, button_label, route }
- steps[] with step_number, step_key, step_label, card_description, drawer_purpose, configure_there[], status_label, blocker_count, warning_count, availability_reason, last_updated_at, action_label, route

Exact step keys:
- tender_profile
- tender_data_sheet
- it_requirements
- implementation_schedule
- system_inventory
- price_schedule
- evaluation_setup
- forms_evidence
- scc_contract_values
- validation
- review_approval
- final_preview
- publication_readiness

Availability handling:
If a step is not yet available, set:
status_label = "Available later"
availability_reason = "Complete [dependency step] first."
action_label = "View dependency"

Do not implement:
locked = true
lock_reason
ready = true
status_label = "Locked"
status_label = "Ready"

Acceptance criteria:
- A user can identify the next step in under 10 seconds.
- There is exactly one prominent primary action.
- Every step card uses the exact description in this specification.
- Tender Profile appears as Configuration Step 01.
- No detailed configuration data appears on Screen 02.
- Every step links to its owning screen.
- Dependency sequencing uses Available later, not Locked.
- Validation is summary-level only.
```

---

## 17. Acceptance Checklist

| Test | Pass condition |
|---|---|
| User decision clarity | The user can tell what to work on next without reading detailed configuration data. |
| Tender Profile retained | Tender Profile appears as Configuration Step 01. |
| Status clarity | No card uses `Locked` or `Ready`. |
| Single primary action | Only one next-best-action panel is visually dominant. |
| Exact copy | Every step uses the exact card description in Section 9. |
| Drawer restraint | The drawer explains the step but does not contain the full configuration form. |
| STD grounding | The screen routes to IT STD-controlled configuration areas without exposing legal internals. |
| Ownership clarity | Screen owns navigation and progress only. |
| No magical values | All displayed values come from the configuration home API or approved seed fixtures. |
| Calm validation | Only blocker/warning counts appear. |
| Route correctness | Every card action opens the owning screen. |

---

## 18. Final Rule

If a field does not help the user decide which configuration step to work on next, remove it from Screen 02.
