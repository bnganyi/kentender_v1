# Tender Configurations WG-02 — Review & Approval Workspace v6

**Project:** KenTender e-Procurement System  
**Module:** Tender Configurations  
**Workflow gate:** WG-02 — Review & Approval Workspace  
**Status:** Revised v6 specification  
**Design mode:** User-centred, simplified, governance-safe  

---

## 1. Canonical Position

| Item | Value |
|---|---|
| Application area | Tender Management → Tender Configurations |
| Previous gate | WG-01 — Readiness Check & Report |
| Current gate | WG-02 — Review & Approval Workspace |
| Next gate | WG-03 — Tender Document Preview |
| Applies to | Existing Tender Configuration |
| User-facing object | Tender Configuration |
| Internal objects hidden from user | Tender shell, TenderSTDInstance, binding ID, hash, schema version, rule IDs |

---

## 2. User Goal

Allow assigned reviewers to review a completed tender configuration and either approve it for document preview or return it for correction.

---

## 3. Single User Decision

> Should this tender configuration be approved for document preview, or returned for correction?

Everything on this screen must support that decision.

---

## 4. What This Screen Is

This is a **governance review workspace** for one tender configuration after it has passed readiness check.

It is not a configuration screen, not a tender-publication screen, and not an award/evaluation screen.

---

## 5. Entry Conditions

The user can enter this screen only when:

| Condition | Required |
|---|---:|
| Tender configuration exists | Yes |
| CFG-01 to CFG-09 are saved | Yes |
| Readiness Check has been run | Yes |
| No blocking readiness issues remain | Yes |
| Configuration is submitted for review | Yes |

If blockers exist, route the user to **WG-01 — Readiness Check & Report**, not this screen.

---

## 6. Exit Conditions

| User action | Result |
|---|---|
| Approve review | Configuration moves to `Approved for Preview` |
| Return for correction | Configuration moves to `Returned for Correction` |
| Request clarification | Configuration remains `Under Review` |
| Cancel / close | No state change |

Approval does **not** publish the tender. Approval only permits generation or viewing of the tender document preview.

---

## 7. Screen Ownership

| Area | Rule |
|---|---|
| Owns | Review decision, reviewer comments, return reasons, clarification requests, review status |
| References | Configuration summary, readiness summary, issue summary, changed sections |
| Does not own | TDS values, requirements, schedule, inventory, prices, evaluation criteria, forms, contract values |
| May edit configuration data? | No |
| May publish tender? | No |
| May open bid submissions? | No |
| May approve award? | No |

---

## 8. Page Title and Subtitle

Title:

```text
Review & Approval
```

Subtitle:

```text
Review the completed tender configuration and decide whether it can proceed to document preview.
```

Do not use:

```text
Approval Console
STD Approval
Tender Publication Approval
Tender Shell Approval
Document Release Approval
```

---

## 9. Required Context Strip

Show only:

| Field | Example |
|---|---|
| Configuration Ref | TC-2024-00047 |
| Procurement Package Ref | PP-ICT-2024-009 |
| Tender Title | Data Center Hardware Refresh |
| STD Family | Information Technology |
| Procuring Entity | National Treasury |
| Procurement Method | Open National Tender |
| Review Status | Under Review |
| Readiness Result | Passed |

Do not show source hashes, schema versions, internal IDs, rule codes, or clause trees.

---

## 10. Main Layout

Use three simple sections:

1. **Review Summary**
2. **Reviewer Checklist**
3. **Decision Panel**

Do not show the full configuration forms here. Provide read-only links to the owning screens.

---

## 11. Review Summary

Show a compact summary:

| Summary item | Exact label | Example value |
|---|---|---|
| Configuration completeness | Configuration Steps | 9 of 9 complete |
| Readiness status | Readiness Check | Passed |
| Remaining warnings | Warnings | 2 accepted warnings |
| Last submitted | Submitted On | 2026-07-17 10:20 EAT |
| Submitted by | Submitted By | Procurement Officer |
| Current reviewer | Assigned Reviewer | Procurement Review Lead |

Do not use percentages unless they add value. Prefer exact counts.

---

## 12. Configuration Sections for Review

Show one read-only list of the configuration sections:

| Section | Review purpose | Status | Action |
|---|---|---|---|
| Tender Profile | Confirm tender identity and procurement context. | Complete | View |
| Tender Data Sheet | Confirm tender-specific instructions and parameters. | Complete | View |
| IT Requirements | Confirm bidder-facing requirements are clear and complete. | Complete | View |
| Implementation Schedule | Confirm delivery approach, milestones, and acceptance expectations. | Complete | View |
| System Inventory & Bidder Background | Confirm disclosed environment/context is useful and safe. | Complete | View |
| Price Schedule | Confirm bidder pricing structure is complete. | Complete | View |
| Evaluation Setup | Confirm evaluation method, criteria, and weights are clear. | Complete | View |
| Forms & Evidence | Confirm bidder submission requirements are complete. | Complete | View |
| Contract Values | Confirm tender-specific contract values are complete. | Complete | View |

The **View** action opens a read-only view or navigates to the owning screen in read-only review mode.

---

## 13. Reviewer Checklist

Use exact checklist items. Do not leave checklist wording to Stitch or Cursor.

| Checklist item | Required? |
|---|---:|
| I have reviewed the tender identity, procurement method, and procuring entity context. | Yes |
| I have reviewed the TDS values that control bidder instructions and submission rules. | Yes |
| I have reviewed the IT requirements for clarity, completeness, and bidder neutrality. | Yes |
| I have reviewed the implementation schedule and acceptance expectations. | Yes |
| I have reviewed bidder background and inventory disclosures for usefulness and sensitivity. | Yes |
| I have reviewed the price schedule structure for completeness and comparability. | Yes |
| I have reviewed the evaluation setup for clarity and consistency with the tender requirements. | Yes |
| I have reviewed the forms and evidence requirements for bidder submission completeness. | Yes |
| I have reviewed the contract values and carry-forward obligations. | Yes |
| I understand that approval here does not publish the tender. | Yes |

Approval is disabled until all required checklist items are checked.

---

## 14. Review Findings

Reviewers may add findings. Findings are not configuration edits.

Table columns:

| Column | Description |
|---|---|
| Finding | Short issue title |
| Section | Owning configuration section |
| Severity | Correction Required / Clarification / Note |
| Required Action | What must be corrected or clarified |
| Status | Open / Resolved / Accepted Note |
| Action | View / Add comment / Mark resolved where permitted |

Allowed finding severities:

| Severity | Meaning |
|---|---|
| Correction Required | Must be fixed before approval |
| Clarification | Reviewer needs explanation before deciding |
| Note | Non-blocking reviewer comment |

Do not use raw severity codes.

---

## 15. Decision Panel

The decision panel contains exactly these actions:

| Action | Button label | Enablement |
|---|---|---|
| Approve | Approve for Document Preview | Enabled only when checklist complete and no open correction-required findings exist |
| Return | Return for Correction | Enabled when reviewer provides return reason |
| Clarify | Request Clarification | Enabled when reviewer provides clarification question |
| Close | Close | Always enabled |

Do not use:

```text
Publish Tender
Release Tender
Approve Tender Publication
Finalize Tender
Approve Award
```

---

## 16. Approval Confirmation Modal

Modal title:

```text
Approve for Document Preview
```

Modal message:

```text
You are approving this tender configuration to proceed to document preview. This does not publish the tender, notify bidders, open bid submission, or approve any award.
```

Required checkbox:

```text
I confirm that this approval only allows the tender document preview to be generated or viewed.
```

Buttons:

```text
Cancel
Approve for Preview
```

---

## 17. Return for Correction Modal

Modal title:

```text
Return for Correction
```

Required fields:

| Field | Type | Required |
|---|---|---:|
| Affected section | Select CFG-01 to CFG-09 | Yes |
| Correction required | Text area | Yes |
| Reviewer note | Text area | Optional |

Modal message:

```text
Returning this configuration will send it back to the configuration team. The affected section must be corrected and the readiness check must pass again before it can be resubmitted for review.
```

Buttons:

```text
Cancel
Return for Correction
```

---

## 18. Request Clarification Modal

Modal title:

```text
Request Clarification
```

Required fields:

| Field | Type | Required |
|---|---|---:|
| Related section | Select CFG-01 to CFG-09 | Yes |
| Clarification question | Text area | Yes |

Modal message:

```text
Request a clarification without returning the configuration for correction. The configuration remains under review.
```

Buttons:

```text
Cancel
Send Clarification Request
```

---

## 19. Status Labels

Allowed screen-level status labels:

| Status | Meaning |
|---|---|
| Submitted for Review | Configuration has been submitted and review has not started |
| Under Review | At least one reviewer is reviewing |
| Clarification Requested | Reviewer has asked for clarification |
| Returned for Correction | Reviewer returned configuration for changes |
| Approved for Preview | Configuration can proceed to tender document preview |

Do not use `Ready`, `Locked`, `Approved for Publication`, or raw enum labels on this screen.

---

## 20. Downstream Impact

This screen feeds:

| Downstream surface | Impact |
|---|---|
| WG-03 — Tender Document Preview | Opens only after approval for preview |
| UI-01 — Tender Configuration Home | Updates review status and next action |
| UI-00 — Tender Configurations Dashboard | Moves configuration to next queue/status |
| Audit trail | Records reviewer decisions, timestamps, comments, and return reasons |

This screen must not publish the tender or create the final publication handoff.

---

## 21. Stitch Prompt

```text
Design WG-02 — Review & Approval Workspace for KenTender Tender Configurations.

User goal:
Allow assigned reviewers to review a completed tender configuration and decide whether it can proceed to document preview or must be returned for correction.

Single user decision:
Should this tender configuration be approved for document preview, or returned for correction?

Page title:
Review & Approval

Subtitle:
Review the completed tender configuration and decide whether it can proceed to document preview.

Context strip fields only:
- Configuration Ref
- Procurement Package Ref
- Tender Title
- STD Family
- Procuring Entity
- Procurement Method
- Review Status
- Readiness Result

Main sections:
1. Review Summary
2. Configuration Sections for Review
3. Reviewer Checklist
4. Review Findings
5. Decision Panel

Review Summary labels and examples:
- Configuration Steps: 9 of 9 complete
- Readiness Check: Passed
- Warnings: 2 accepted warnings
- Submitted On: 2026-07-17 10:20 EAT
- Submitted By: Procurement Officer
- Assigned Reviewer: Procurement Review Lead

Configuration sections table:
- Tender Profile — Confirm tender identity and procurement context. — Complete — View
- Tender Data Sheet — Confirm tender-specific instructions and parameters. — Complete — View
- IT Requirements — Confirm bidder-facing requirements are clear and complete. — Complete — View
- Implementation Schedule — Confirm delivery approach, milestones, and acceptance expectations. — Complete — View
- System Inventory & Bidder Background — Confirm disclosed environment/context is useful and safe. — Complete — View
- Price Schedule — Confirm bidder pricing structure is complete. — Complete — View
- Evaluation Setup — Confirm evaluation method, criteria, and weights are clear. — Complete — View
- Forms & Evidence — Confirm bidder submission requirements are complete. — Complete — View
- Contract Values — Confirm tender-specific contract values are complete. — Complete — View

Reviewer checklist exact items:
- I have reviewed the tender identity, procurement method, and procuring entity context.
- I have reviewed the TDS values that control bidder instructions and submission rules.
- I have reviewed the IT requirements for clarity, completeness, and bidder neutrality.
- I have reviewed the implementation schedule and acceptance expectations.
- I have reviewed bidder background and inventory disclosures for usefulness and sensitivity.
- I have reviewed the price schedule structure for completeness and comparability.
- I have reviewed the evaluation setup for clarity and consistency with the tender requirements.
- I have reviewed the forms and evidence requirements for bidder submission completeness.
- I have reviewed the contract values and carry-forward obligations.
- I understand that approval here does not publish the tender.

Review Findings table columns:
- Finding
- Section
- Severity
- Required Action
- Status
- Action

Allowed severity labels:
- Correction Required
- Clarification
- Note

Decision Panel buttons:
- Approve for Document Preview
- Return for Correction
- Request Clarification
- Close

Do not show editable configuration fields. Do not show Tender Shell, TenderSTDInstance, binding ID, schema version, hash, rule ID, clause tree, publication controls, bid submission controls, evaluation results, or award controls.
```

---

## 22. Cursor Prompt

```text
Implement WG-02 — Review & Approval Workspace for KenTender Tender Configurations.

This is a workflow gate, not a configuration step.

Primary user decision:
Should this tender configuration be approved for document preview, or returned for correction?

Required route:
/tender-configurations/:configuration_id/review

Required API payload:
{
  configuration_ref,
  procurement_package_ref,
  tender_title,
  std_family_label,
  procuring_entity_name,
  procurement_method_label,
  review_status,
  review_status_label,
  readiness_result_label,
  submitted_on,
  submitted_by,
  assigned_reviewer,
  accepted_warning_count,
  sections: [
    {
      section_key,
      section_label,
      review_purpose,
      status_label,
      read_only_route
    }
  ],
  checklist: [
    {
      checklist_key,
      label,
      required,
      checked
    }
  ],
  findings: [
    {
      finding_id,
      title,
      section_label,
      severity_label,
      required_action,
      status_label
    }
  ],
  actions: {
    approve_enabled,
    approve_disabled_reason,
    return_enabled,
    request_clarification_enabled
  }
}

Render:
1. Page title: Review & Approval.
2. Subtitle: Review the completed tender configuration and decide whether it can proceed to document preview.
3. Context strip with only the specified fields.
4. Review Summary.
5. Configuration Sections for Review table.
6. Reviewer Checklist.
7. Review Findings table.
8. Decision Panel.

Decision behavior:
- Approve for Document Preview is enabled only when all required checklist items are checked and no open Correction Required findings exist.
- Return for Correction requires affected section and correction required text.
- Request Clarification requires related section and clarification question.
- Approval confirmation must state that approval does not publish the tender, notify bidders, open bid submission, or approve an award.

Forbidden:
- No editable configuration fields on this screen.
- No Tender Shell, TenderSTDInstance, binding ID, schema version, hash, rule ID, or clause tree.
- No Publish Tender, Release Tender, Approve Tender Publication, Approve Award, or Open Bid Submission actions.
- No raw enum labels.
```

---

## 23. Acceptance Checklist

| Test | Pass condition |
|---|---|
| Single decision clarity | User knows the screen is for approve / return / clarify only. |
| No configuration editing | No CFG-01 to CFG-09 fields are editable here. |
| Publication boundary | UI states approval does not publish the tender. |
| Review completeness | Checklist covers all nine configuration sections. |
| Finding clarity | Findings identify affected section and required action. |
| Approval gate | Approval disabled while required checklist items or correction findings remain open. |
| Return control | Return requires affected section and correction reason. |
| Terminology | No internal architecture terms appear. |
| Downstream consistency | Approval leads to WG-03 Tender Document Preview only. |

---

## 24. Final Rule

If a UI element does not help the reviewer decide whether to approve, return, or request clarification, remove it from WG-02.
