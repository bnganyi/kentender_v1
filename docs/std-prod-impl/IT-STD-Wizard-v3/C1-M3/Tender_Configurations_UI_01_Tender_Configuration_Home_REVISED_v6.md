# UI-01 — Tender Configuration Home

**Project:** KenTender e-Procurement System  
**Module:** Tender Configurations  
**Canonical ID:** UI-01  
**Status:** Revised v6 specification  
**Design rule:** One-configuration work-plan page. Do not turn this into a configuration form, validation report, review workspace, or publication page.

---

## 1. Control Block

| Field | Value |
|---|---|
| User-facing name | Tender Configuration Home |
| Menu path | Tender Management → Tender Configurations → Open Configuration |
| Surface type | Application screen |
| Lifecycle position | After a tender configuration has been created from an approved procurement package |
| Source object | Existing Tender Configuration |
| Primary user decision | What should I work on next for this tender configuration? |
| Owns | Progress summary, next best action, routing to configuration steps, workflow-gate summary |
| Does not own | Tender Profile fields, TDS values, requirements, schedule details, inventory/background rows, price lines, evaluation criteria, forms/evidence rows, contract values, review decisions, generated document content, or publication actions |
| STD anchor | Not an STD content section. It routes to the applicable STD-family configuration steps. |
| Entry condition | A tender configuration exists for an approved procurement package |
| Exit condition | User opens a configuration step or an available workflow gate/action |
| Forbidden visible terms | Tender Shell, TenderSTDInstance, STD binding, STD package code, STD version hash, schema version, rule ID, source anchor, render block, clause hash, lifecycle enum, Ready, Locked, Finalize Configuration, Publish Tender |

---

## 2. User Goal

Help the user understand the remaining configuration work for one tender and continue the correct next action.

---

## 3. Page Header

### Title

```text
Tender Configuration Home
```

### Subtitle

```text
Complete the required configuration steps before review, preview, and publication handoff.
```

Do not include the STD family in the page title. The STD family is shown in the context strip.

---

## 4. Context Strip

Show exactly these fields.

| Field label | Example | Rule |
|---|---|---|
| Procurement Package Ref | `PP-ICT-2024-009` | Read-only; source is the approved procurement package |
| Procurement Title | `Data Center Hardware Refresh` | Read-only unless later changed in the owning Tender Profile step |
| Procuring Entity | `National Treasury` | Read-only |
| Procurement Method | `Open National Tender` | Read-only |
| STD Family | `Information Technology` | Read-only once configuration is created |
| Standard Tender Document | `IT Standard Tender Document — April 2022` | Read-only unless policy permits controlled change before configuration work starts |
| Configuration Status | `In progress` | Human-readable status only |
| Issues | `2 Blockers / 3 Warnings` | Summary only |

Do not show backend object names, source hashes, package codes, rule IDs, clause trees, schema versions, audit events, or raw lifecycle enums.

---

## 5. Next Best Action Panel

Show one prominent panel directly below the context strip.

### Exact format

```text
Next step: {action target}
Reason: {plain-language reason}
```

### Allowed examples

| Condition | Exact next-step text | Exact reason text | Button |
|---|---|---|---|
| Tender Profile incomplete | `Next step: Complete Tender Profile` | `Confirm the basic tender identity and setup context before completing detailed configuration.` | `Continue` |
| Tender Data Sheet incomplete | `Next step: Complete Tender Data Sheet` | `Tender-specific instructions and parameters are still missing.` | `Continue` |
| IT Requirements has blockers | `Next step: Fix IT Requirements` | `Some requirements are missing bidder response, evidence, or acceptance details.` | `Fix` |
| Implementation Schedule incomplete | `Next step: Complete Implementation Schedule` | `The delivery approach, milestones, or acceptance checkpoints are still incomplete.` | `Continue` |
| All configuration steps complete and readiness not run | `Next step: Run Readiness Check` | `Check the configuration for blockers and warnings before review.` | `Run Readiness Check` |
| Readiness passed and not submitted | `Next step: Submit for Review` | `The configuration has passed readiness checks and can be sent for review.` | `Submit for Review` |
| Review approved and preview not confirmed | `Next step: Open Tender Document Preview` | `Review is approved. Confirm the generated tender document before publication handoff.` | `Open Tender Document Preview` |
| Preview confirmed and not handed off | `Next step: Mark Ready for Publication` | `The package is confirmed and can be handed to Tender Management.` | `Mark Ready for Publication` |

Rules:

- Show one primary button only.
- Do not show `Finalize Configuration`.
- Do not show `Publish Tender`.
- Do not expose reviewer actions unless the current user is in the reviewer workflow context.

---

## 6. Configuration Steps

Section title:

```text
Configuration Steps
```

For the current Information Technology STD family, show exactly the following nine configuration cards in this order.

| ID | Card title | Exact card description | Typical action |
|---|---|---|---|
| CFG-01 | Tender Profile | Confirm the tender identity, procuring entity, procurement method, lot structure, planning reference, and basic setup context before detailed configuration. | Start / Continue / Review |
| CFG-02 | Tender Data Sheet | Enter the tender-specific instructions and parameters that complete the Instructions to Tenderers through the Tender Data Sheet. | Start / Continue / Review |
| CFG-03 | IT Requirements | Define what bidders must supply, deliver, integrate, support, or prove, including bidder response, evidence, and acceptance expectations. | Start / Continue / Fix / Review |
| CFG-04 | Implementation Schedule | Choose the delivery approach and define milestones, durations, deliverables, and acceptance checkpoints. | Start / Continue / Fix / Review |
| CFG-05 | System Inventory & Bidder Background | Describe bidder-relevant inventory, sites, existing systems, integrations, recurrent context, and background information without creating hidden requirements. | Start / Continue / Fix / Review |
| CFG-06 | Price Schedule | Define the supply, installation, and recurrent cost items bidders must price. | Start / Continue / Fix / Review |
| CFG-07 | Evaluation Setup | Set the preliminary, technical, financial, preference, qualification, and post-qualification evaluation rules. | Start / Continue / Fix / Review |
| CFG-08 | Forms & Evidence | Define all non-price forms, declarations, qualification documents, securities, and evidence bidders must submit. | Start / Continue / Fix / Review |
| CFG-09 | Contract Values | Confirm the Special Conditions of Contract values and contract-facing obligations that vary from the standard contract. | Start / Continue / Fix / Review |

### Future STD-family rule

This screen must load its configuration-step list from the selected STD family profile. Do not hardcode IT-only steps into the generic dashboard. For the current implementation, the IT family profile returns CFG-01 to CFG-09 exactly as listed above.

---

## 7. Configuration Card Fields

Each card must show only these fields.

| Field | Rule |
|---|---|
| Step ID | `CFG-01`, `CFG-02`, etc. |
| Card title | Exact title from the configuration step table |
| Description | Exact description from the configuration step table |
| Status | One allowed configuration-step status |
| Issues | Blank, or `{n} Blockers / {m} Warnings` |
| Last updated | Optional; show only if useful |
| Action | One button only |

Do not place forms, tables, detailed validation findings, legal clause content, or technical metadata inside the cards.

---

## 8. Allowed Configuration Step Statuses

Use only these labels.

| Status | Meaning | Button |
|---|---|---|
| Not started | No meaningful work has been done | Start |
| In progress | Work has started but required items remain | Continue |
| Needs attention | Blockers, returned corrections, or important warnings require action | Fix |
| Complete | Required local setup is complete | Review |
| Not available yet | A prior required step or policy condition prevents work | View required step |

Do not use `Ready` or `Locked`.

---

## 9. Completion & Handoff

Section title:

```text
Completion & Handoff
```

This section is not a configuration-step list. It shows workflow gates and their current availability.

| Item | Exact description | Status examples | Action examples |
|---|---|---|---|
| Readiness Check | Checks all configuration steps and shows blockers or warnings before review. | `Not run`, `Blockers found`, `Passed` | `Run Readiness Check`, `View Readiness Report` |
| Review Status | Shows whether the configuration has been submitted, returned, or approved by reviewers. | `Not submitted`, `Under review`, `Returned`, `Approved` | `Submit for Review`, `Open Review Workspace` |
| Tender Document Preview | Opens the generated tender document after review approval so the package can be confirmed before handoff. | `Available after review`, `Not confirmed`, `Confirmed` | `Open Tender Document Preview`, `Confirm Preview` |
| Publication Handoff | Marks the approved and confirmed package ready for Tender Management; this does not publish the tender. | `Available after preview`, `Ready for handoff`, `Handed off` | `Mark Ready for Publication`, `Open in Tender Management` |

Rules:

- Do not show these as numbered configuration cards.
- Do not call them CFG-10 to CFG-13.
- Do not expose publication controls.
- `Publication Handoff` means handoff to Tender Management; it does not publish the tender.

---

## 10. Step Details Drawer

A configuration card may open a lightweight drawer. The drawer must not contain the full configuration form.

### Drawer fields

| Field | Required text source |
|---|---|
| Title | Card title |
| Purpose | Exact card description |
| Status | Current status label |
| Issues | Summary count only |
| What you will configure | Exact text from the table below |
| What this step does not configure | Exact text from the table below |
| Primary action | Same as card action |

### Exact drawer content

| Step | What you will configure | What this step does not configure |
|---|---|---|
| Tender Profile | Tender identity, procuring entity, procurement method, lot structure, planning reference, and basic setup context. | TDS parameters, technical requirements, pricing, evaluation, contract values, review, preview, or publication. |
| Tender Data Sheet | Tender-specific instructions, deadlines, submission rules, securities, language, currency, and permitted ITT parameters. | Technical specifications, price rows, evaluation scores, bidder submissions, contract administration, or publication. |
| IT Requirements | Requirement statements, bidder response instructions, evidence expectations, and acceptance expectations. | Scoring marks, price lines, actual bidder responses, evaluation results, contract administration, or publication. |
| Implementation Schedule | Delivery approach, milestones, durations, deliverables, start triggers, and acceptance checkpoints. | Live project execution, inspection records, payment certification, contract administration, or publication. |
| System Inventory & Bidder Background | Bidder-relevant inventory, sites, existing systems, integrations, recurrent context, and background materials. | Full pricing setup, evaluation scoring, hidden requirements in background text, contract administration, or publication. |
| Price Schedule | Supply, installation, and recurrent cost items, pricing basis, units, quantities, and pricing instructions. | Technical requirement wording, actual bid prices, evaluation scoring, contract administration, or publication. |
| Evaluation Setup | Preliminary, technical, financial, preference, qualification, and post-qualification evaluation rules. | Actual bid evaluation, award recommendation, requirement drafting, price entry, or publication. |
| Forms & Evidence | Non-price forms, declarations, qualification forms, securities, evidence instructions, and submission requirements. | Actual bidder uploads, evidence verification, evaluation scoring, price schedule forms, or publication. |
| Contract Values | SCC values, contract-facing parameters, obligations, warranties, securities, and contract appendices carried from the configuration. | Post-award contract administration, change orders, inspections, payment certification, or publication. |

---

## 11. Data Contract

The Configuration Home API must provide this shape.

```json
{
  "configuration_id": "TCFG-0001",
  "procurement_package_ref": "PP-ICT-2024-009",
  "procurement_title": "Data Center Hardware Refresh",
  "procuring_entity_name": "National Treasury",
  "procurement_method_label": "Open National Tender",
  "std_family_label": "Information Technology",
  "standard_tender_document_label": "IT Standard Tender Document — April 2022",
  "configuration_status_label": "In progress",
  "blocker_count": 2,
  "warning_count": 3,
  "next_action": {
    "label": "Fix IT Requirements",
    "reason": "Some requirements are missing bidder response, evidence, or acceptance details.",
    "button_label": "Fix",
    "route": "/app/tender-configuration/TCFG-0001/it-requirements"
  },
  "configuration_steps": [
    {
      "id": "CFG-03",
      "title": "IT Requirements",
      "description": "Define what bidders must supply, deliver, integrate, support, or prove, including bidder response, evidence, and acceptance expectations.",
      "status_label": "Needs attention",
      "blocker_count": 2,
      "warning_count": 1,
      "last_updated_label": "2026-07-17 10:30 EAT",
      "action_label": "Fix",
      "route": "/app/tender-configuration/TCFG-0001/it-requirements"
    }
  ],
  "handoff": {
    "readiness_check": {
      "label": "Readiness Check",
      "description": "Checks all configuration steps and shows blockers or warnings before review.",
      "status_label": "Blockers found",
      "action_label": "View Readiness Report",
      "route": "/app/tender-configuration/TCFG-0001/readiness-report"
    },
    "review_status": {
      "label": "Review Status",
      "description": "Shows whether the configuration has been submitted, returned, or approved by reviewers.",
      "status_label": "Not submitted",
      "action_label": "Submit for Review",
      "route": null
    },
    "tender_document_preview": {
      "label": "Tender Document Preview",
      "description": "Opens the generated tender document after review approval so the package can be confirmed before handoff.",
      "status_label": "Available after review",
      "action_label": null,
      "route": null
    },
    "publication_handoff": {
      "label": "Publication Handoff",
      "description": "Marks the approved and confirmed package ready for Tender Management; this does not publish the tender.",
      "status_label": "Available after preview",
      "action_label": null,
      "route": null
    }
  }
}
```

---

## 12. Stitch Prompt

```text
Design UI-01 — Tender Configuration Home for KenTender.

User goal:
Understand the remaining work for one tender configuration and open the right next step.

This is a work-plan page. It is not a configuration form, readiness report, review workflow, document preview, or publication page.

Page title:
Tender Configuration Home

Subtitle:
Complete the required configuration steps before review, preview, and publication handoff.

Context strip fields only:
- Procurement Package Ref
- Procurement Title
- Procuring Entity
- Procurement Method
- STD Family
- Standard Tender Document
- Configuration Status
- Issues

Do not show Tender Shell, TenderSTDInstance, STD binding, STD package code, STD version hash, schema version, rule ID, source anchor, render block, clause hash, lifecycle enum, Ready, Locked, Finalize Configuration, or Publish Tender.

Add one prominent Next Best Action panel with this exact format:
Next step: {action target}
Reason: {plain-language reason}

Below it, show a section titled:
Configuration Steps

For the Information Technology STD family, show exactly nine cards in this order:
1. CFG-01 Tender Profile — Confirm the tender identity, procuring entity, procurement method, lot structure, planning reference, and basic setup context before detailed configuration.
2. CFG-02 Tender Data Sheet — Enter the tender-specific instructions and parameters that complete the Instructions to Tenderers through the Tender Data Sheet.
3. CFG-03 IT Requirements — Define what bidders must supply, deliver, integrate, support, or prove, including bidder response, evidence, and acceptance expectations.
4. CFG-04 Implementation Schedule — Choose the delivery approach and define milestones, durations, deliverables, and acceptance checkpoints.
5. CFG-05 System Inventory & Bidder Background — Describe bidder-relevant inventory, sites, existing systems, integrations, recurrent context, and background information without creating hidden requirements.
6. CFG-06 Price Schedule — Define the supply, installation, and recurrent cost items bidders must price.
7. CFG-07 Evaluation Setup — Set the preliminary, technical, financial, preference, qualification, and post-qualification evaluation rules.
8. CFG-08 Forms & Evidence — Define all non-price forms, declarations, qualification documents, securities, and evidence bidders must submit.
9. CFG-09 Contract Values — Confirm the Special Conditions of Contract values and contract-facing obligations that vary from the standard contract.

Each card shows only:
- CFG ID
- Card title
- Exact card description
- Status
- Issue count if any
- One action button

Allowed configuration step statuses:
- Not started
- In progress
- Needs attention
- Complete
- Not available yet

Do not use Ready or Locked.

Below the cards, show a section titled:
Completion & Handoff

Show four compact status items, not configuration cards:
- Readiness Check — Checks all configuration steps and shows blockers or warnings before review.
- Review Status — Shows whether the configuration has been submitted, returned, or approved by reviewers.
- Tender Document Preview — Opens the generated tender document after review approval so the package can be confirmed before handoff.
- Publication Handoff — Marks the approved and confirmed package ready for Tender Management; this does not publish the tender.

Do not label these as configuration steps.
```

---

## 13. Cursor Prompt

```text
Implement UI-01 — Tender Configuration Home as a focused work-plan page for one Tender Configuration.

The screen answers one question:
What should I work on next?

Render these areas only:
1. Header with title and subtitle.
2. Context strip.
3. One Next Best Action panel.
4. Configuration Steps section using the STD-family step profile returned by the API.
5. Completion & Handoff section with exactly four workflow gate summaries.

Context strip labels:
- Procurement Package Ref
- Procurement Title
- Procuring Entity
- Procurement Method
- STD Family
- Standard Tender Document
- Configuration Status
- Issues

For the current Information Technology STD family, configuration cards must be exactly:
- CFG-01 Tender Profile
- CFG-02 Tender Data Sheet
- CFG-03 IT Requirements
- CFG-04 Implementation Schedule
- CFG-05 System Inventory & Bidder Background
- CFG-06 Price Schedule
- CFG-07 Evaluation Setup
- CFG-08 Forms & Evidence
- CFG-09 Contract Values

Use the exact card descriptions from the screen specification. Do not invent descriptions.

Allowed step statuses:
Not started, In progress, Needs attention, Complete, Not available yet.

Allowed card actions:
Start, Continue, Fix, Review, View required step.

Completion & Handoff items:
- Readiness Check
- Review Status
- Tender Document Preview
- Publication Handoff

These are not configuration steps. Do not render them as CFG-10 to CFG-13.

Forbidden visible UI terms:
Tender Shell, TenderSTDInstance, STD binding, STD package code, STD version hash, schema version, rule ID, source anchor, render block, clause hash, lifecycle enum, Ready, Locked, Finalize Configuration, Publish Tender.

Do not render configuration forms, detailed validation findings, review decision forms, generated document content, audit logs, or publication controls on this screen.

A drawer may be used for step details, but it must only show the exact purpose, status, issue count, what the user will configure, what the step does not configure, and the primary action. It must not contain the full form.
```

---

## 14. Acceptance Criteria

| Test | Pass condition |
|---|---|
| Sequence integrity | Only CFG-01 to CFG-09 appear as configuration steps for the IT STD family. |
| Workflow distinction | Readiness Check, Review Status, Tender Document Preview, and Publication Handoff appear only in Completion & Handoff. |
| Generic dashboard alignment | Context uses Procurement Package Ref and STD Family, not IT-only dashboard naming. |
| Terminology | No forbidden internal terms or old labels appear. |
| Single decision | The screen helps the user decide what to work on next. |
| No configuration leakage | No detailed TDS, requirements, schedule, inventory/background, pricing, evaluation, form, or contract fields appear on the home screen. |
| Exact descriptions | Every card uses the exact description in this spec. |
| Status discipline | Step statuses use only allowed labels and never use Ready or Locked. |
| Downstream clarity | Each card routes to its owning CFG screen; handoff items route only when available. |
| Simplicity | There is one primary next-action panel and no competing primary action. |

---

## 15. Final Rule

If an element does not help the user decide what to work on next, remove it from UI-01.
