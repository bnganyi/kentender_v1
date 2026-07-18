# Tender Configurations — WG-03 Tender Document Preview v6

**Product area:** KenTender — Tender Management → Tender Configurations  
**Surface ID:** WG-03  
**Surface name:** Tender Document Preview  
**Surface type:** Workflow gate / generated-output review  
**Applies to:** Tender configurations created from approved procurement packages  
**Design principle:** Read-only confirmation of the generated tender document, not another configuration screen.

---

## 1. Purpose

The Tender Document Preview lets the user inspect the generated tender document after review approval and before publication handoff.

The user is answering one question:

> Does the generated tender document reflect the approved tender configuration and look ready to hand over for publication?

---

## 2. Lifecycle position

```text
Approved Procurement Package
→ Create Tender Configuration
→ Configure CFG-01 to CFG-09
→ WG-01 Readiness Check & Report
→ WG-02 Review & Approval Workspace
→ WG-03 Tender Document Preview
→ WG-04 Publication Handoff
→ Tender Management publication workflow
```

WG-03 is available only after the configuration is approved in WG-02.

---

## 3. What this surface owns

| Area | Rule |
|---|---|
| Owns | Preview generation, preview review, preview confirmation, exception reporting |
| Does not own | Editing configuration values, reviewer approval, publication, bidder notification, bid submission opening |
| User action | Confirm preview or return for correction |
| Output | Preview-confirmed tender package or returned correction state |

---

## 4. STD grounding

The preview renders the approved configuration against the applicable Standard Tender Document.

For the IT STD family, the generated package must include the relevant rendered content from:

- tender identity and invitation/front matter;
- Section I — Instructions to Tenderers, locked standard text;
- Section II — Tender Data Sheet;
- Section III — Evaluation and Qualification Criteria;
- Section IV — Tendering Forms, including price schedules and non-price forms/evidence;
- Part 2 — Procuring Entity’s Requirements, including IT requirements, technical requirements, implementation schedule, system inventory tables, and background materials;
- Part 3 — Contract, including GCC locked standard text, SCC, contract forms, securities, certificates, appendices, and contract values where applicable.

The preview must not allow direct editing of locked ITT/GCC text or approved configuration values.

---

## 5. Entry conditions

WG-03 may be opened when all are true:

| Condition | Required state |
|---|---|
| Readiness check | Passed or accepted with permitted warnings |
| Review status | Approved |
| Configuration state | Approved for preview |
| Render package | Generated or ready to generate |

If the preview cannot be generated, show a render exception state and direct the user back to WG-01 or the owning configuration step.

---

## 6. Default layout

### 6.1 Header

Title:

```text
Tender Document Preview
```

Subtitle:

```text
Review the generated tender document before marking it ready for publication handoff.
```

### 6.2 Context strip

Show only:

| Field | Example |
|---|---|
| Procurement Package Ref | `PP-ICT-2024-009` |
| Configuration Ref | `TC-2024-00128` |
| Tender Title | `Data Center Hardware Refresh` |
| STD Family | `Information Technology` |
| Standard Tender Document | `IT Standard Tender Document — April 2022` |
| Review Status | `Approved` |
| Preview Status | `Generated` / `Confirmed` / `Exception Found` |

Do not show schema versions, hashes, internal render IDs, binding IDs, or clause object IDs in the default UI.

---

## 7. Main content

Use three areas:

### A. Document outline

A left-side outline lets the user move through the generated document.

Required outline labels:

1. Cover and Invitation
2. Instructions to Tenderers
3. Tender Data Sheet
4. Evaluation and Qualification Criteria
5. Tendering Forms
6. Price Schedules
7. Requirements of the Information System
8. Technical Requirements
9. Implementation Schedule
10. System Inventory and Background
11. General Conditions of Contract
12. Special Conditions of Contract
13. Contract Forms and Appendices

### B. Document preview pane

The center pane shows the generated tender document.

Required behavior:

- Read-only preview.
- Clear page/document navigation.
- Search within preview.
- Download preview PDF.
- Watermark before final confirmation:

```text
PREVIEW — NOT FOR PUBLICATION
```

After preview confirmation, show:

```text
PREVIEW CONFIRMED — READY FOR PUBLICATION HANDOFF
```

### C. Confirmation panel

The right panel shows a concise confirmation checklist:

| Check | Label |
|---|---|
| Approved configuration | `Generated from approved configuration` |
| Read-only standard text | `Locked standard text preserved` |
| TDS and SCC | `Tender-specific values included` |
| Requirements and schedules | `Procuring Entity’s Requirements included` |
| Forms and price schedules | `Bidder submission forms included` |
| No publication action | `This action does not publish the tender` |

The user must check:

```text
I confirm that I have reviewed the generated tender document and it is ready for publication handoff.
```

Only then enable:

```text
Confirm Preview
```

---

## 8. Actions

| Action | When enabled | Result |
|---|---|---|
| Regenerate Preview | Approved configuration exists and user has permission | Regenerates preview from approved configuration |
| Download Preview PDF | Preview generated | Downloads watermarked preview before confirmation |
| Return for Correction | Preview generated and user finds issue | Requires reason and affected section; sends configuration back for correction |
| Confirm Preview | Confirmation checkbox checked and no render exception | Sets preview status to confirmed |
| Continue to Publication Handoff | Preview confirmed | Opens WG-04 |

Do not show:

```text
Publish Tender
Notify Bidders
Open Bid Submission
Edit Requirement
Edit TDS
Edit SCC
Approve Configuration
```

---

## 9. Return for correction modal

Title:

```text
Return Configuration for Correction
```

Message:

```text
Returning this configuration will stop the publication handoff until the issue is corrected, readiness is rechecked where required, and review approval is refreshed if the correction affects approved content.
```

Required fields:

| Field | Required |
|---|---:|
| Affected document section | Yes |
| Correction reason | Yes |
| Severity | Yes |
| Suggested owning configuration step | Optional |

Buttons:

```text
Cancel
Return for Correction
```

---

## 10. Status model

Use only these preview statuses:

| Status | Meaning |
|---|---|
| Not generated | Preview has not been generated |
| Generated | Preview exists but has not been confirmed |
| Exception found | Preview generation failed or output has blocking issue |
| Confirmed | User confirmed the preview for publication handoff |

Do not use `Ready`, `Locked`, or raw enum labels in the UI.

---

## 11. API shape

```json
{
  "configuration_id": "TC-2024-00128",
  "procurement_package_ref": "PP-ICT-2024-009",
  "configuration_ref": "TC-2024-00128",
  "tender_title": "Data Center Hardware Refresh",
  "std_family": "Information Technology",
  "standard_tender_document_label": "IT Standard Tender Document — April 2022",
  "review_status": "approved",
  "review_status_label": "Approved",
  "preview_status": "generated",
  "preview_status_label": "Generated",
  "generated_at": "2026-07-17T10:15:00+03:00",
  "generated_by": "Procurement Officer",
  "outline": [
    {"key": "cover_invitation", "label": "Cover and Invitation", "page_start": 1},
    {"key": "itt", "label": "Instructions to Tenderers", "page_start": 5},
    {"key": "tds", "label": "Tender Data Sheet", "page_start": 28}
  ],
  "preview_pdf_url": "/api/method/...",
  "can_regenerate_preview": true,
  "can_return_for_correction": true,
  "can_confirm_preview": true,
  "render_exception": null
}
```

---

## 12. Stitch prompt

```text
Design WG-03 — Tender Document Preview for KenTender Tender Configurations.

This is a workflow gate after Review & Approval, not a configuration screen.

User decision:
Does the generated tender document reflect the approved tender configuration and look ready for publication handoff?

Use the page title:
Tender Document Preview

Use the subtitle:
Review the generated tender document before marking it ready for publication handoff.

Layout:
1. Header and context strip.
2. Left document outline.
3. Center read-only document preview pane.
4. Right preview confirmation panel.
5. Bottom action bar.

Context strip fields:
- Procurement Package Ref
- Configuration Ref
- Tender Title
- STD Family
- Standard Tender Document
- Review Status
- Preview Status

Document outline labels:
- Cover and Invitation
- Instructions to Tenderers
- Tender Data Sheet
- Evaluation and Qualification Criteria
- Tendering Forms
- Price Schedules
- Requirements of the Information System
- Technical Requirements
- Implementation Schedule
- System Inventory and Background
- General Conditions of Contract
- Special Conditions of Contract
- Contract Forms and Appendices

Center preview pane:
- Read-only document preview.
- Show watermark: PREVIEW — NOT FOR PUBLICATION.
- Include Search and Download Preview PDF controls.

Right confirmation panel checklist:
- Generated from approved configuration
- Locked standard text preserved
- Tender-specific values included
- Procuring Entity’s Requirements included
- Bidder submission forms included
- This action does not publish the tender

Required checkbox:
I confirm that I have reviewed the generated tender document and it is ready for publication handoff.

Actions:
- Regenerate Preview
- Download Preview PDF
- Return for Correction
- Confirm Preview
- Continue to Publication Handoff

Do not show editing fields. Do not show Publish Tender, Notify Bidders, Open Bid Submission, internal render IDs, hashes, schema versions, or binding IDs.
```

---

## 13. Cursor prompt

```text
Implement WG-03 — Tender Document Preview for KenTender Tender Configurations.

Use this as a workflow gate after Review & Approval. Do not implement it as a configuration step.

Primary object:
TenderConfigurationPreview

Required behavior:
1. Fetch preview data from the tender configuration preview API.
2. Render header and context strip.
3. Render a left document outline.
4. Render a read-only document preview pane.
5. Render a right confirmation checklist.
6. Disable Confirm Preview until the required checkbox is checked and no render exception exists.
7. Enable Continue to Publication Handoff only after preview_status is confirmed.
8. Return for Correction must open a modal requiring affected section, severity, and reason.
9. Returning for correction must not silently edit configuration values.
10. Do not expose internal IDs, hashes, schema versions, binding IDs, or render block diagnostics in the default UI.

Forbidden UI terms:
- Tender Shell
- TenderSTDInstance
- STD binding
- render block ID
- schema version
- hash
- Publish Tender
- Notify Bidders
- Open Bid Submission

Accepted statuses:
- Not generated
- Generated
- Exception found
- Confirmed

Acceptance criteria:
- User can review the generated document without editing it.
- User can clearly see that confirmation does not publish the tender.
- User can return for correction with a mandatory reason.
- Continue to Publication Handoff is unavailable until preview is confirmed.
- No configuration form fields appear on this screen.
```

---

## 14. Acceptance checklist

| Test | Pass condition |
|---|---|
| Read-only preview | No configuration field can be edited here |
| Lifecycle correctness | Surface appears after review approval only |
| No publication confusion | UI clearly states confirmation does not publish |
| Correction governance | Return for correction requires reason and affected section |
| STD coverage | Outline covers IT STD rendered package areas |
| Simplicity | User sees preview, confirmation, and next action without workflow clutter |
| No internal terms | No shell, binding, hash, schema, or render IDs in default UI |
