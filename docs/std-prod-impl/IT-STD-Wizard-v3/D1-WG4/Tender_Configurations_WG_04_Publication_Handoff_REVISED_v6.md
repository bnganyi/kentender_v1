# Tender Configurations — WG-04 Publication Handoff v6

**Surface ID:** WG-04  
**Name:** Publication Handoff  
**Module:** Tender Configurations  
**Menu location:** Tender Management → Tender Configurations  
**Surface type:** Workflow gate, not a configuration step  
**Status:** Revised v6 specification  

---

## 1. Purpose

Publication Handoff marks an approved and preview-confirmed tender configuration as ready for the Tender Management publication workflow.

This surface does **not** publish the tender, notify bidders, open bid submission, approve award, or manage post-publication activity.

---

## 2. Single User Decision

> Is this approved tender package ready to be handed to Tender Management for publication processing?

Everything on this surface must support that decision.

---

## 3. Entry Conditions

The user may enter WG-04 only when:

| Requirement | Required state |
|---|---|
| Configuration steps | CFG-01 to CFG-09 complete or accepted with permitted warnings |
| Readiness check | Passed |
| Review & approval | Approved |
| Tender document preview | Confirmed |
| Blocking issues | None open |

If any condition is not met, show a read-only blocked state with the exact missing condition and a link to the owning surface.

---

## 4. Exit Conditions

Successful handoff changes the tender configuration state to:

```text
Ready for Publication
```

After handoff, the primary action becomes:

```text
Open in Tender Management
```

The configuration remains traceable but should not be edited directly unless formally returned for correction.

---

## 5. User-Facing Language

Use these terms:

| Use | Do not use |
|---|---|
| Publication Handoff | Publish Tender |
| Ready for Publication | Published |
| Tender Package | Tender shell |
| Tender Management | downstream engine |
| Approved Procurement Package | procurement initiation object |
| Standard Tender Document | STD package code |

---

## 6. Page Header

**Title:**

```text
Publication Handoff
```

**Subtitle:**

```text
Confirm that the approved tender package is ready for Tender Management publication processing.
```

---

## 7. Context Strip

Show only:

| Field | Example |
|---|---|
| Procurement Package Ref | PP-ICT-2024-009 |
| Tender Title | Data Center Hardware Refresh |
| STD Family | Information Technology |
| Standard Tender Document | IT Standard Tender Document — April 2022 |
| Procuring Entity | National Treasury |
| Procurement Method | Open National Tender |
| Configuration Status | Preview Confirmed |
| Issues | 0 Blockers / 0 Warnings |

Do not show hashes, schema versions, binding IDs, internal object names, or raw lifecycle enums.

---

## 8. Main Layout

Use four compact panels.

### 8.1 Handoff Readiness Summary

Show:

| Item | Display value |
|---|---|
| Configuration steps | Complete |
| Readiness check | Passed |
| Review approval | Approved |
| Tender document preview | Confirmed |
| Blocking issues | None |

### 8.2 Package Contents

Show a concise checklist:

| Package item | Status |
|---|---|
| Tender Profile | Included |
| Tender Data Sheet | Included |
| IT Requirements / applicable STD-family requirements | Included |
| Implementation Schedule | Included |
| System Inventory & Bidder Background | Included |
| Price Schedule | Included |
| Evaluation Setup | Included |
| Forms & Evidence | Included |
| Contract Values | Included |
| Rendered Tender Document | Included |
| Review Approval Record | Included |
| Readiness Report | Included |

For non-IT STD families, replace IT-specific labels with the applicable family configuration labels.

### 8.3 Publication Handoff Details

Show:

| Field | Behavior |
|---|---|
| Handoff destination | Read-only: Tender Management |
| Next owner | Required selector if not already assigned |
| Proposed publication workflow | Read-only or selected from permitted options |
| Handoff note | Optional text area |
| Confirmation checkbox | Required before final action |

Confirmation checkbox text:

```text
I confirm that this action marks the tender package as ready for publication processing. It does not publish the tender, notify bidders, or open bid submission.
```

### 8.4 Handoff History

Show only high-level history:

| Date/time | Actor | Action |
|---|---|---|
| 2026-07-17 10:15 EAT | Procurement Lead | Preview confirmed |
| 2026-07-17 11:20 EAT | Procurement Lead | Marked ready for publication |

Do not expose raw audit payloads.

---

## 9. Primary Actions

| State | Primary action | Enabled when |
|---|---|---|
| Not ready | View Missing Items | Any entry condition is unmet |
| Ready for handoff | Mark Ready for Publication | All entry conditions met and confirmation checked |
| Handoff complete | Open in Tender Management | Handoff completed |

Secondary actions:

```text
View Tender Preview
View Readiness Report
View Review Approval
Return for Correction
```

`Return for Correction` must require a reason and must send the user back to the owning configuration surface or reviewer workflow.

---

## 10. Forbidden Content

Do not show or allow:

- Publish Tender button;
- bidder notification controls;
- bid submission opening controls;
- award controls;
- contract execution controls;
- raw STD hashes;
- raw schema metadata;
- internal tender shell or binding terminology;
- editable CFG-01 to CFG-09 fields;
- reviewer approval decisions.

---

## 11. API Shape

```json
{
  "configuration_id": "TCFG-2026-00034",
  "procurement_package_ref": "PP-ICT-2024-009",
  "tender_title": "Data Center Hardware Refresh",
  "std_family": "Information Technology",
  "standard_tender_document_label": "IT Standard Tender Document — April 2022",
  "procuring_entity_name": "National Treasury",
  "procurement_method_label": "Open National Tender",
  "configuration_status_label": "Preview Confirmed",
  "blocker_count": 0,
  "warning_count": 0,
  "handoff_ready": true,
  "handoff_completed": false,
  "readiness_summary": {
    "configuration_steps": "Complete",
    "readiness_check": "Passed",
    "review_approval": "Approved",
    "document_preview": "Confirmed",
    "blocking_issues": "None"
  },
  "package_contents": [
    {"label": "Tender Profile", "status": "Included"},
    {"label": "Tender Data Sheet", "status": "Included"},
    {"label": "Rendered Tender Document", "status": "Included"}
  ],
  "handoff_destination_label": "Tender Management",
  "next_owner_options": [
    {"value": "publication_officer", "label": "Publication Officer"}
  ],
  "selected_next_owner": null,
  "handoff_note": null,
  "history": []
}
```

---

## 12. Stitch Prompt

```text
Design WG-04 — Publication Handoff for the KenTender Tender Configurations workflow.

This is a workflow gate, not a configuration step.

Page title: Publication Handoff
Subtitle: Confirm that the approved tender package is ready for Tender Management publication processing.

Single user decision: Is this approved tender package ready to be handed to Tender Management for publication processing?

Use a calm, simple layout with four panels:
1. Handoff Readiness Summary
2. Package Contents
3. Publication Handoff Details
4. Handoff History

Context strip fields:
- Procurement Package Ref
- Tender Title
- STD Family
- Standard Tender Document
- Procuring Entity
- Procurement Method
- Configuration Status
- Issues

Primary action:
- Mark Ready for Publication

After handoff, replace the primary action with:
- Open in Tender Management

Confirmation checkbox text:
I confirm that this action marks the tender package as ready for publication processing. It does not publish the tender, notify bidders, or open bid submission.

Do not show Publish Tender, bidder notification controls, bid submission controls, award controls, contract execution controls, STD hashes, schema metadata, tender shell, binding IDs, or editable configuration fields.
```

---

## 13. Cursor Prompt

```text
Implement WG-04 — Publication Handoff for Tender Configurations.

This is not a configuration step. It is the workflow gate that marks an approved and preview-confirmed tender package as ready for Tender Management publication processing.

Use user-facing procurement language only.
Do not use internal terms such as tender shell, binding, instance, package code, hash, or schema version.

Render:
- page title: Publication Handoff
- subtitle: Confirm that the approved tender package is ready for Tender Management publication processing.
- context strip with procurement package, tender title, STD family, standard tender document, procuring entity, method, configuration status, and issue count
- handoff readiness summary
- package contents checklist
- publication handoff details
- handoff history

Primary action rules:
- If handoff_ready is false, show View Missing Items.
- If handoff_ready is true and handoff_completed is false, show Mark Ready for Publication.
- Enable Mark Ready for Publication only after the user selects required next owner if needed and checks the confirmation checkbox.
- If handoff_completed is true, show Open in Tender Management.

Mark Ready for Publication must not publish the tender, notify bidders, or open bid submission. It only changes the configuration state to Ready for Publication and hands the package to Tender Management.

Do not render editable CFG fields, publish controls, bidder notification controls, bid submission controls, award controls, contract execution controls, raw audit payloads, hashes, schema metadata, or internal object names.
```

---

## 14. Acceptance Criteria

| Test | Pass condition |
|---|---|
| Purpose clarity | User understands this is a handoff, not publication. |
| Gate integrity | Handoff is blocked unless readiness, review, and preview are complete. |
| No configuration editing | CFG fields are not editable here. |
| No publication action | There is no Publish Tender button. |
| Confirmation | Final action requires explicit confirmation checkbox. |
| User language | No internal system terminology appears. |
| Downstream boundary | Successful action sends package to Tender Management publication workflow. |

---

## 15. Final Rule

If a control would publish the tender, notify bidders, open bid submission, award a tender, or administer a contract, it does not belong on WG-04.
