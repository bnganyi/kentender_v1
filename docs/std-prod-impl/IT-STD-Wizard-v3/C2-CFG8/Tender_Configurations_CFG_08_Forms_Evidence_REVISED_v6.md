# Tender Configurations — CFG-08 Forms & Evidence v6

**Surface ID:** CFG-08  
**User-facing name:** Forms & Evidence  
**Module area:** Tender Management → Tender Configurations  
**Configuration family for this spec:** Information Technology STD  
**Design mode:** Simple, user-centred, implementation-ready

---

## 1. Purpose

Help the procurement user decide **what bidders must submit with their tender**.

This screen configures bidder-facing submission forms, declarations, certificates, qualification evidence, technical evidence, and other non-price submission requirements.

It is **not** a document-upload screen for actual bidders. It is also not an evaluation screen.

---

## 2. Primary user decision

> What must bidders submit so their tender can be checked, evaluated, and considered complete?

Everything on the screen must support that decision.

---

## 3. STD grounding

This screen covers the non-price submission burden from **Section IV — Tendering Forms**, plus evidence requirements created by the Tender Data Sheet, IT Requirements, and Evaluation Setup.

It covers:

- Form of Tender;
- Confidential Business Questionnaire;
- Certificate of Independent Tender Determination;
- self-declaration forms;
- tender security or tender-securing declaration where applicable;
- qualification forms and supporting evidence;
- financial capacity evidence;
- personnel capability evidence;
- intellectual property and authorization evidence where applicable;
- conformance and technical evidence;
- other bidder submission evidence required by the configured tender.

Price forms are handled in **CFG-06 Price Schedule**. Actual bid submissions are handled later in the bid submission module.

---

## 4. Screen ownership

| Area | Rule |
|---|---|
| Owns | Bidder submission requirements, form requirements, evidence instructions, conditionality, and bidder-facing submission guidance |
| Does not own | Actual bidder uploads, evaluation scores, price schedules, requirement wording, contract values, approval workflow, publication |
| Primary object | `TenderSubmissionRequirement` |
| Source objects | Standard Tender Document, Tender Data Sheet, IT Requirements, Evaluation Setup, Price Schedule reference only |
| Output | Submission checklist and form/evidence requirements used in the rendered tender package |

---

## 5. User-facing screen title

Use:

```text
Forms & Evidence
```

Subtitle:

```text
Define the forms, declarations, certificates, and evidence bidders must submit.
```

Do not use:

```text
Evidence Matrix
Submission Schema
Bidder Upload Configuration
Form Rules Engine
```

---

## 6. Main layout

Use a simple three-part layout:

1. **Context strip** — tender and configuration context.
2. **Submission requirements table** — main working area.
3. **Guidance panel** — explains what belongs here and what does not.

Avoid multi-panel technical layouts.

---

## 7. Context strip

Show only:

| Field | Example |
|---|---|
| Procurement Package Ref | `PP-ICT-2024-009` |
| Tender Title | `Data Center Hardware Refresh` |
| STD Family | `Information Technology` |
| Standard Tender Document | `IT Standard Tender Document — April 2022` |
| Configuration Status | `In Progress` |
| Issues | `0 Blockers / 2 Warnings` |

Do not show hashes, rule IDs, schema versions, binding IDs, or internal object names.

---

## 8. Tabs / filters

Use these filters. They are filters, not separate complex screens.

| Filter | Meaning |
|---|---|
| All Items | All required, conditional, and optional submission items |
| Standard Forms | Forms coming from the Standard Tender Document |
| Declarations | bidder declarations and statutory forms |
| Qualification Evidence | legal, financial, experience, personnel, and capacity evidence |
| Technical Evidence | product, method, conformance, manufacturer, authorization, or technical proof |
| Tender Security | tender security or securing declaration where applicable |
| Conditional Items | items required only if a condition applies |

Default filter: **All Items**.

---

## 9. Main table

Required columns:

| Column | Exact label | Purpose |
|---|---|---|
| 1 | Submission Item | Form/evidence item bidders must submit |
| 2 | Category | Standard Form, Declaration, Qualification Evidence, Technical Evidence, Tender Security, Conditional Item |
| 3 | Source | STD, TDS, IT Requirements, Evaluation Setup, User Added |
| 4 | Requirement | Mandatory, Conditional, Optional, Not Applicable |
| 5 | Bidder Instruction | Plain-language instruction shown to bidders |
| 6 | Status | Complete, Needs attention, Not applicable |
| 7 | Actions | Edit, Mark Not Applicable, Review |

Do not include actual bidder upload status, evaluation result, score, pass/fail, or reviewer decision.

---

## 10. Sample table rows

| Submission Item | Category | Source | Requirement | Bidder Instruction | Status | Action |
|---|---|---|---|---|---|---|
| Form of Tender | Standard Form | STD | Mandatory | Bidder must complete and sign the Form of Tender. | Complete | Review |
| Confidential Business Questionnaire | Standard Form | STD | Mandatory | Bidder must provide ownership, registration, and business details. | Complete | Review |
| Certificate of Independent Tender Determination | Declaration | STD | Mandatory | Bidder must submit the signed certificate with the tender. | Complete | Review |
| Manufacturer Authorization for Servers | Technical Evidence | IT Requirements | Mandatory | Bidder must provide manufacturer authorization or equivalent proof of authority to supply and support the proposed equipment. | Needs attention | Fix |
| Technical Datasheets for Compute Nodes | Technical Evidence | IT Requirements | Mandatory | Bidder must attach datasheets showing processor, memory, storage, power, and redundancy specifications. | Complete | Edit |
| Tender Security | Tender Security | TDS | Conditional | Required only if tender security is enabled in the Tender Data Sheet. | Complete | Edit |
| Audited Financial Statements | Qualification Evidence | Evaluation Setup | Mandatory | Bidder must provide audited financial statements for the years specified in Evaluation Setup. | Complete | Edit |
| Key Personnel CVs | Qualification Evidence | Evaluation Setup | Conditional | Required only where personnel qualifications are evaluated. | Needs attention | Fix |
| Software Licence Authorization | Technical Evidence | IT Requirements | Conditional | Required where proprietary software licences are proposed. | Complete | Edit |
| Local Preference Evidence | Qualification Evidence | TDS / Evaluation Setup | Conditional | Required only if margin of preference or reservation rules apply. | Not applicable | Review |

---

## 11. Status vocabulary

Use only these statuses on this screen:

| Status | Meaning |
|---|---|
| Complete | The submission item has a clear requirement rule and bidder instruction |
| Needs attention | Required instruction, condition, or source link is missing |
| Not applicable | The item is intentionally excluded for this tender with a reason |

Do not use:

```text
Locked
Ready
Validated
Approved
Submitted
Received
Compliant
Failed
```

Those belong to other lifecycle stages.

---

## 12. Requirement values

Use only:

| Value | Meaning |
|---|---|
| Mandatory | Every bidder must submit this item |
| Conditional | Required only if a stated condition applies |
| Optional | Bidder may provide it, but it is not required for responsiveness |
| Not Applicable | This item is not used in this tender, with recorded reason |

Every conditional item must have a plain-language condition.

Example:

```text
Required only if the bidder proposes proprietary software that requires manufacturer or publisher authorization.
```

---

## 13. Drawer behavior

Open a drawer when the user clicks **Edit**, **Fix**, or **Review**.

Drawer title format:

```text
Edit Submission Item
```

Drawer sections and exact fields:

### A. Submission item

| Field | Editable? | Notes |
|---|---:|---|
| Submission item name | Yes, unless STD-fixed | Example: `Manufacturer Authorization for Servers` |
| Category | Yes for user-added items; read-only for STD forms | Use approved category list |
| Source | Read-only | STD, TDS, IT Requirements, Evaluation Setup, User Added |
| Requirement | Yes, subject to source rules | Mandatory, Conditional, Optional, Not Applicable |

### B. Bidder instruction

| Field | Editable? | Notes |
|---|---:|---|
| Bidder instruction | Yes | Exact text shown to bidders |
| Accepted response format | Yes | Form, PDF attachment, certificate, declaration, table, narrative, other |
| Accepted file type | Optional | Use only if relevant |

### C. Condition

Show only when `Requirement = Conditional`.

| Field | Editable? | Notes |
|---|---:|---|
| Condition text | Yes | Plain-language condition |
| Condition source | Read-only or selectable | TDS, IT Requirements, Evaluation Setup |

### D. Related configuration

| Field | Editable? | Notes |
|---|---:|---|
| Related IT Requirement | Optional | Reference only; requirement wording is not edited here |
| Related Evaluation Criterion | Optional | Reference only; scoring is not edited here |
| Related TDS value | Optional | Reference only |

### E. Applicability decision

Show when user marks item as not applicable.

| Field | Editable? | Notes |
|---|---:|---|
| Not applicable reason | Required | Must explain why item is excluded |

Drawer buttons:

```text
Cancel
Save Submission Item
```

For items with blockers, use:

```text
Save Fix
```

---

## 14. Guidance panel

Title:

```text
Forms & Evidence Guidance
```

Body text:

```text
Use this screen to define what bidders must submit with their tender. Keep instructions clear, bidder-facing, and limited to forms, declarations, certificates, qualification evidence, and technical proof. Price forms are configured in Price Schedule. Evaluation scores are configured in Evaluation Setup.
```

Show compact counters:

| Counter | Example |
|---|---|
| Mandatory items | `8` |
| Conditional items | `4` |
| Items needing attention | `2` |
| Not applicable items | `1` |

---

## 15. Primary actions

Top actions:

```text
Add Submission Item
Import Standard Forms
Run Readiness Check
```

Footer actions:

```text
Save Forms & Evidence
Continue to Contract Values
```

Enablement rules:

| Action | Rule |
|---|---|
| Add Submission Item | Enabled while configuration is editable |
| Import Standard Forms | Enabled if standard forms have not already been imported or can be refreshed safely |
| Run Readiness Check | Always enabled in editable configuration states |
| Save Forms & Evidence | Enabled if changes exist |
| Continue to Contract Values | Disabled if mandatory submission items lack bidder instructions or required conditions |

---

## 16. Empty state

If no submission items exist:

Title:

```text
No submission items configured yet
```

Body:

```text
Start by importing the standard tender forms, then add any tender-specific evidence required by the Tender Data Sheet, IT Requirements, or Evaluation Setup.
```

Actions:

```text
Import Standard Forms
Add Submission Item
```

---

## 17. Downstream impact

This screen feeds:

- generated tender document submission checklist;
- bidder response package structure;
- readiness check;
- tender preview;
- publication package.

This screen is used by downstream modules to know what bidders are expected to submit, but it does **not** receive actual submissions.

---

## 18. Upstream dependencies

This screen may depend on:

| Upstream screen | Impact |
|---|---|
| CFG-02 Tender Data Sheet | tender security, margin of preference, submission conditions |
| CFG-03 IT Requirements | technical evidence instructions |
| CFG-07 Evaluation Setup | qualification and evaluation evidence requirements |
| CFG-06 Price Schedule | price forms are referenced but not configured here |

If upstream data is incomplete, show a simple warning:

```text
Some evidence items may change after Evaluation Setup is completed.
```

Do not block the user unless a required source is missing.

---

## 19. Forbidden content

Do not show or configure:

- actual bidder uploads;
- bidder submission status;
- compliance results;
- evaluation marks or pass/fail results;
- price line items;
- contract obligation text;
- approval workflow decisions;
- publication controls;
- STD hashes, rule IDs, schema versions, binding IDs, or internal object names.

---

## 20. API shape

```json
{
  "configuration_id": "TCFG-2024-0009",
  "procurement_package_ref": "PP-ICT-2024-009",
  "tender_title": "Data Center Hardware Refresh",
  "std_family": "Information Technology",
  "standard_tender_document": "IT Standard Tender Document — April 2022",
  "configuration_status": "In Progress",
  "blocker_count": 0,
  "warning_count": 2,
  "summary": {
    "mandatory_items": 8,
    "conditional_items": 4,
    "needs_attention": 2,
    "not_applicable": 1
  },
  "submission_items": [
    {
      "item_id": "FE-001",
      "item_name": "Form of Tender",
      "category": "Standard Form",
      "source": "STD",
      "requirement": "Mandatory",
      "bidder_instruction": "Bidder must complete and sign the Form of Tender.",
      "status": "Complete",
      "action_label": "Review"
    }
  ]
}
```

---

## 21. Stitch prompt

```text
Design CFG-08 Forms & Evidence for the KenTender Tender Configurations module.

User goal:
Define the forms, declarations, certificates, and evidence bidders must submit with their tender.

Screen title:
Forms & Evidence

Subtitle:
Define the forms, declarations, certificates, and evidence bidders must submit.

Use procurement-facing language only. Do not show actual bidder uploads, evaluation scores, price lines, approval controls, publication controls, hashes, rule IDs, schema versions, or internal object names.

Layout:
1. Context strip with Procurement Package Ref, Tender Title, STD Family, Standard Tender Document, Configuration Status, and Issues.
2. Filter tabs: All Items, Standard Forms, Declarations, Qualification Evidence, Technical Evidence, Tender Security, Conditional Items.
3. Main table with columns: Submission Item, Category, Source, Requirement, Bidder Instruction, Status, Actions.
4. Right guidance panel titled Forms & Evidence Guidance.
5. Bottom action bar with Save Forms & Evidence and Continue to Contract Values.

Use these status labels only: Complete, Needs attention, Not applicable.
Use these requirement values only: Mandatory, Conditional, Optional, Not Applicable.

Top actions:
Add Submission Item, Import Standard Forms, Run Readiness Check.

Drawer sections:
Submission Item, Bidder Instruction, Condition, Related Configuration, Applicability Decision.

Sample rows:
- Form of Tender | Standard Form | STD | Mandatory | Bidder must complete and sign the Form of Tender. | Complete | Review
- Manufacturer Authorization for Servers | Technical Evidence | IT Requirements | Mandatory | Bidder must provide manufacturer authorization or equivalent proof of authority to supply and support the proposed equipment. | Needs attention | Fix
- Tender Security | Tender Security | TDS | Conditional | Required only if tender security is enabled in the Tender Data Sheet. | Complete | Edit
- Audited Financial Statements | Qualification Evidence | Evaluation Setup | Mandatory | Bidder must provide audited financial statements for the years specified in Evaluation Setup. | Complete | Edit
- Local Preference Evidence | Qualification Evidence | TDS / Evaluation Setup | Conditional | Required only if margin of preference or reservation rules apply. | Not applicable | Review
```

---

## 22. Cursor prompt

```text
Implement CFG-08 Forms & Evidence for the KenTender Tender Configurations module.

Primary user decision:
What must bidders submit so their tender can be checked, evaluated, and considered complete?

This screen owns bidder submission requirements only. It does not own actual bidder uploads, evaluation scores, price schedule items, contract values, approval workflow, publication, or STD technical metadata.

Render:
- title: Forms & Evidence
- subtitle: Define the forms, declarations, certificates, and evidence bidders must submit.
- context strip: Procurement Package Ref, Tender Title, STD Family, Standard Tender Document, Configuration Status, Issues
- filter tabs: All Items, Standard Forms, Declarations, Qualification Evidence, Technical Evidence, Tender Security, Conditional Items
- table columns: Submission Item, Category, Source, Requirement, Bidder Instruction, Status, Actions
- guidance panel with the exact guidance text from the spec
- footer actions: Save Forms & Evidence, Continue to Contract Values

Use only these statuses: Complete, Needs attention, Not applicable.
Use only these requirement values: Mandatory, Conditional, Optional, Not Applicable.

Drawer fields:
Submission item name, Category, Source, Requirement, Bidder instruction, Accepted response format, Accepted file type, Condition text, Condition source, Related IT Requirement, Related Evaluation Criterion, Related TDS value, Not applicable reason.

Conditional rule:
If Requirement is Conditional, require Condition text.
If Requirement is Not Applicable, require Not applicable reason.
Disable Continue to Contract Values if mandatory items lack bidder instructions or conditional items lack conditions.

Do not render actual bidder uploads, compliance statuses, scoring marks, price line details, contract obligation text, approval decisions, publication buttons, hashes, rule IDs, schema versions, binding IDs, or internal object names.
```

---

## 23. Acceptance checklist

| Check | Pass condition |
|---|---|
| User decision clarity | User understands this screen defines what bidders must submit |
| STD coverage | Non-price Section IV forms and evidence requirements are represented |
| Price separation | Price forms remain in CFG-06 Price Schedule |
| Evaluation separation | Evaluation scores and pass rules remain in CFG-07 Evaluation Setup |
| Submission separation | Actual bidder uploads are not shown here |
| Conditional clarity | Conditional items have plain-language conditions |
| No internal terms | No hashes, rule IDs, binding IDs, schemas, or internal object names appear |
| Downstream readiness | Output can feed tender preview and bidder response checklist |

---

## 24. Final rule

If a field does not help the user define what bidders must submit, remove it from CFG-08.
