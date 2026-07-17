# Tender Configurations WG-01 — Readiness Check & Report v6

**Project:** KenTender e-Procurement System  
**Area:** Tender Configurations  
**Surface type:** Workflow gate / report  
**Position:** After CFG-01 to CFG-09; before Review & Approval  
**Status:** Revised v6 specification  
**Design principle:** Simple gate, clear defects, no new configuration editing

---

## 1. Purpose

The Readiness Check confirms whether a tender configuration is complete enough to submit for review.

It checks the outputs of CFG-01 to CFG-09 and tells the user what must be fixed before review.

This is **not** a configuration screen.

---

## 2. User Decision

> Can this tender configuration be submitted for review, or must I fix something first?

Everything on the screen must support that decision.

---

## 3. Lifecycle Position

```text
Approved Procurement Package
→ Create Tender Configuration
→ Configuration Home
→ CFG-01 to CFG-09
→ WG-01 Readiness Check & Report
→ WG-02 Review & Approval
→ WG-03 Tender Document Preview
→ WG-04 Publication Handoff
→ Tender Management publication workflow
```

---

## 4. Entry Conditions

The user may run the Readiness Check from:

- Tender Configuration Home;
- footer action on any CFG screen;
- Completion & Handoff panel.

The check may run before all CFG steps are complete, but submission for review is allowed only when there are **zero blockers**.

---

## 5. Exit Conditions

| Result | System behavior |
|---|---|
| Blockers exist | User must fix blockers before review. |
| Warnings only | User may submit for review if policy allows warning acknowledgement. |
| No blockers or warnings | User may submit for review. |

---

## 6. Screen Ownership

| Item | Rule |
|---|---|
| Screen owns | Readiness check run, readiness result, issue summary, deep links to owning screens |
| Screen does not own | TDS values, requirements, schedule rows, inventory rows, price lines, evaluation criteria, forms, contract values |
| Editable here | Nothing except optional warning acknowledgement if allowed |
| Primary action | Fix blockers / Submit for Review |
| Secondary actions | Re-run Check, Export Readiness Report, Return to Configuration Home |

---

## 7. STD Grounding

The Readiness Check validates that the configured tender package is complete across the applicable Standard Tender Document structure.

For the IT STD, it checks coverage across:

- Tender identity and procurement context;
- Tender Data Sheet;
- Evaluation and Qualification Criteria;
- Tendering Forms and bidder evidence;
- Requirements of the Information System;
- Technical Requirements;
- Implementation Schedule;
- System Inventory Tables;
- Background and Informational Materials;
- SCC / contract-specific values.

Locked ITT and GCC text are not edited here. They are rendered from the STD Engine and checked for inclusion, consistency, and correct parameterization.

---

## 8. Default Layout

### 8.1 Header

Title:

```text
Readiness Check & Report
```

Subtitle:

```text
Check whether this tender configuration is complete enough for review.
```

Header actions:

```text
Re-run Check
Export Report
Return to Configuration Home
```

Do not use:

```text
Validation Console
Rule Engine Output
Schema Diagnostics
STD Compliance Matrix
```

---

### 8.2 Context Strip

Show only:

| Field | Example |
|---|---|
| Configuration Ref | TC-2026-0042 |
| Procurement Package Ref | PP-ICT-2026-014 |
| Tender Title | Data Center Hardware Refresh |
| STD Family | Information Technology |
| Standard Tender Document | IT Standard Tender Document — April 2022 |
| Procuring Entity | National Treasury |
| Configuration Status | In Progress |

Do not show hashes, internal binding IDs, schema IDs, rule IDs, or source anchors.

---

### 8.3 Readiness Summary

Use four cards:

| Card | Example |
|---|---|
| Overall Result | Not ready for review |
| Blockers | 3 |
| Warnings | 5 |
| Last Checked | 2026-07-17 10:30 EAT |

Allowed overall result labels:

```text
Ready for Review
Not Ready for Review
Ready with Warnings
Check Not Run
```

---

### 8.4 Primary Guidance Panel

If blockers exist:

```text
This configuration cannot be submitted for review yet. Fix the blockers listed below, then re-run the readiness check.
```

If warnings only:

```text
This configuration has no blockers. Review the warnings before submitting for review.
```

If clear:

```text
This configuration is ready to submit for review.
```

---

## 9. Findings Table

The table must show only user-actionable findings.

| Column | Required wording / rule |
|---|---|
| Severity | Blocker / Warning |
| Area | User-facing CFG area |
| Issue | Exact plain-language issue |
| Why it matters | One sentence impact |
| Required action | Exact user action |
| Owner screen | CFG screen where correction must be made |
| Action | Fix / Review |

### Sample findings

| Severity | Area | Issue | Why it matters | Required action | Owner screen | Action |
|---|---|---|---|---|---|---|
| Blocker | IT Requirements | Two mandatory requirements are missing acceptance expectations. | Bidders and reviewers need to know how delivery will be accepted. | Add acceptance expectations for the affected requirements. | CFG-03 IT Requirements | Fix |
| Blocker | Price Schedule | One required inventory item is not linked to a price item. | Bidders may omit pricing for a required item. | Add or link the missing price item. | CFG-06 Price Schedule | Fix |
| Blocker | Evaluation Setup | Technical pass rule is not defined. | The tender cannot be evaluated consistently without a pass rule. | Define the technical pass rule. | CFG-07 Evaluation Setup | Fix |
| Warning | System Inventory & Bidder Background | One background item is marked “review before disclosure.” | Sensitive information may be exposed to bidders if not reviewed. | Confirm or revise the disclosure status. | CFG-05 System Inventory & Bidder Background | Review |
| Warning | Forms & Evidence | One optional evidence item has no bidder instruction. | Bidders may not understand whether the item is expected. | Add a short bidder instruction or mark it not applicable. | CFG-08 Forms & Evidence | Review |

---

## 10. Readiness Checklist

Show a compact checklist for CFG-01 to CFG-09.

| Area | Check result | Action |
|---|---|---|
| Tender Profile | Complete | Review |
| Tender Data Sheet | Complete | Review |
| IT Requirements | Needs attention | Fix |
| Implementation Schedule | Complete | Review |
| System Inventory & Bidder Background | Warnings | Review |
| Price Schedule | Needs attention | Fix |
| Evaluation Setup | Needs attention | Fix |
| Forms & Evidence | Warnings | Review |
| Contract Values | Complete | Review |

Do not display raw system validation rules in the checklist.

---

## 11. Severity Rules

### Blocker

A blocker prevents submission for review.

Examples:

- required TDS value missing;
- mandatory requirement lacks bidder response instruction;
- mandatory requirement lacks acceptance expectation;
- required price item missing;
- evaluation method incomplete;
- required form/evidence item missing;
- contract value required by SCC is missing;
- required section cannot be rendered.

### Warning

A warning does not always prevent review but must be visible.

Examples:

- optional background item needs disclosure review;
- evidence instruction is unclear;
- requirement may be too broad;
- price item may reduce comparability;
- contract carry-forward should be reviewed.

---

## 12. Actions and Enablement Rules

| Action | Enabled when | Result |
|---|---|---|
| Re-run Check | Always | Runs readiness validation again. |
| Fix | Finding has owner screen | Opens the owning CFG screen at the affected item. |
| Review | Warning has owner screen | Opens owning CFG screen or detail drawer. |
| Submit for Review | Blocker count = 0 | Opens review submission confirmation. |
| Export Report | Check has run at least once | Downloads readiness summary. |
| Return to Configuration Home | Always | Returns to UI-01. |

Primary button logic:

| Condition | Primary button |
|---|---|
| Blockers exist | Fix Blockers |
| No blockers, warnings exist | Submit for Review |
| No blockers or warnings | Submit for Review |
| Check not run | Run Readiness Check |

---

## 13. Submission Confirmation

When the user clicks `Submit for Review`, show a confirmation modal.

Title:

```text
Submit Tender Configuration for Review
```

Body:

```text
This will submit the tender configuration for formal review. Reviewers will be able to approve it, return it for correction, or request clarification.

This action does not publish the tender and does not open bid submission.
```

If warnings exist, show:

```text
This configuration has warnings. You may submit it for review, but reviewers will see the warnings.
```

Checkbox if warnings exist:

```text
I have reviewed the warnings and want to submit this configuration for review.
```

Buttons:

```text
Cancel
Submit for Review
```

---

## 14. Forbidden Content

Do not show:

- raw rule IDs;
- source-document hashes;
- clause hash mismatches unless transformed into user-facing issue text;
- schema diagnostics;
- backend object IDs;
- full tender document preview;
- approval decision forms;
- publication controls;
- editable configuration fields.

---

## 15. API Shape

```json
{
  "configuration_id": "TC-2026-0042",
  "configuration_ref": "TC-2026-0042",
  "procurement_package_ref": "PP-ICT-2026-014",
  "tender_title": "Data Center Hardware Refresh",
  "std_family": "Information Technology",
  "standard_tender_document": "IT Standard Tender Document — April 2022",
  "procuring_entity_name": "National Treasury",
  "configuration_status": "IN_PROGRESS",
  "readiness_status": "NOT_READY_FOR_REVIEW",
  "blocker_count": 3,
  "warning_count": 5,
  "last_checked_at": "2026-07-17T10:30:00+03:00",
  "primary_action": {
    "label": "Fix Blockers",
    "route": "/app/tender-configuration/TC-2026-0042/readiness"
  },
  "findings": [
    {
      "severity": "BLOCKER",
      "area": "IT Requirements",
      "issue": "Two mandatory requirements are missing acceptance expectations.",
      "why_it_matters": "Bidders and reviewers need to know how delivery will be accepted.",
      "required_action": "Add acceptance expectations for the affected requirements.",
      "owner_screen": "CFG-03 IT Requirements",
      "route": "/app/tender-configuration/TC-2026-0042/it-requirements?filter=missing_acceptance"
    }
  ],
  "checklist": [
    {
      "area": "Tender Profile",
      "result": "COMPLETE",
      "route": "/app/tender-configuration/TC-2026-0042/profile"
    }
  ]
}
```

---

## 16. Stitch Prompt

```text
Design WG-01 — Readiness Check & Report for KenTender Tender Configurations.

Purpose:
Check whether one tender configuration is complete enough to submit for review.

This is a workflow gate, not a configuration step.
Do not design it as a data-entry screen.

Page title:
Readiness Check & Report

Subtitle:
Check whether this tender configuration is complete enough for review.

Use a context strip with only:
- Configuration Ref
- Procurement Package Ref
- Tender Title
- STD Family
- Standard Tender Document
- Procuring Entity
- Configuration Status

Show four readiness cards:
- Overall Result
- Blockers
- Warnings
- Last Checked

Use this guidance text when blockers exist:
This configuration cannot be submitted for review yet. Fix the blockers listed below, then re-run the readiness check.

Use a findings table with columns:
- Severity
- Area
- Issue
- Why it matters
- Required action
- Owner screen
- Action

Use these sample findings:
1. Blocker | IT Requirements | Two mandatory requirements are missing acceptance expectations. | Bidders and reviewers need to know how delivery will be accepted. | Add acceptance expectations for the affected requirements. | CFG-03 IT Requirements | Fix
2. Blocker | Price Schedule | One required inventory item is not linked to a price item. | Bidders may omit pricing for a required item. | Add or link the missing price item. | CFG-06 Price Schedule | Fix
3. Warning | System Inventory & Bidder Background | One background item is marked review before disclosure. | Sensitive information may be exposed to bidders if not reviewed. | Confirm or revise the disclosure status. | CFG-05 System Inventory & Bidder Background | Review

Show a compact checklist for:
- Tender Profile
- Tender Data Sheet
- IT Requirements
- Implementation Schedule
- System Inventory & Bidder Background
- Price Schedule
- Evaluation Setup
- Forms & Evidence
- Contract Values

Primary button rules:
- If blockers exist: Fix Blockers
- If no blockers: Submit for Review
- If check not run: Run Readiness Check

Secondary actions:
- Re-run Check
- Export Report
- Return to Configuration Home

Do not show raw rule IDs, source hashes, schema diagnostics, approval forms, publication controls, or editable configuration fields.
```

---

## 17. Cursor Prompt

```text
Implement WG-01 — Readiness Check & Report for KenTender Tender Configurations.

This page is a workflow gate after CFG-01 to CFG-09 and before Review & Approval.
It must not render editable configuration fields.

Primary goal:
Help the user decide whether the tender configuration can be submitted for review or must be fixed first.

Required route:
/app/tender-configuration/:configuration_id/readiness

Required API:
GET /api/method/kentender_procurement.tender_configurations.api.get_readiness_report
POST /api/method/kentender_procurement.tender_configurations.api.run_readiness_check
POST /api/method/kentender_procurement.tender_configurations.api.submit_for_review

Render:
1. Page title: Readiness Check & Report
2. Subtitle: Check whether this tender configuration is complete enough for review.
3. Context strip: Configuration Ref, Procurement Package Ref, Tender Title, STD Family, Standard Tender Document, Procuring Entity, Configuration Status.
4. Summary cards: Overall Result, Blockers, Warnings, Last Checked.
5. Guidance panel based on readiness status.
6. Findings table with Severity, Area, Issue, Why it matters, Required action, Owner screen, Action.
7. CFG checklist covering CFG-01 to CFG-09 only.
8. Footer actions based on primary button rules.

Rules:
- Do not show raw backend rule IDs.
- Do not show hashes, schema diagnostics, source anchors, or internal object IDs.
- Do not show editable TDS, requirements, schedule, inventory, price, evaluation, forms, or contract fields.
- Findings must deep-link to the owning CFG screen.
- Submit for Review is disabled when blocker_count > 0.
- If warning_count > 0 and blocker_count = 0, require confirmation checkbox before submit.
- This action does not publish the tender.

Acceptance criteria:
- User can see within 10 seconds whether the configuration is ready for review.
- All blockers show exact correction action and owner screen.
- No configuration editing is possible on this page.
- Submit for Review is impossible while blockers exist.
- Report uses procurement-facing language only.
```

---

## 18. Acceptance Checklist

| Test | Pass condition |
|---|---|
| Lifecycle clarity | Page appears after CFG steps and before review. |
| User decision clarity | User can tell whether to fix or submit. |
| No configuration editing | No editable CFG fields appear. |
| Actionability | Every blocker has a clear correction action and owner screen. |
| No internal terminology | No raw rule IDs, hashes, schema names, or backend object names appear. |
| Review gate integrity | Submit for Review disabled when blockers exist. |
| Warning handling | Warnings are visible and acknowledged if required. |
| Deep linking | Fix/Review actions open the owning CFG screen. |
| STD coverage | Checklist covers CFG-01 to CFG-09 only. |

---

## 19. Final Rule

If an item does not help the user decide whether the configuration can be submitted for review, remove it from WG-01.
