# Tender Configurations — CFG-01 Tender Profile UX Refactor v6

**Project:** KenTender e-Procurement System  
**Module:** Tender Configurations  
**Surface:** CFG-01 — Tender Profile  
**Status:** Revised specification  
**Design rule:** User-centric, simple, complete, and implementation-ready  

---

## 1. Canonical Position

| Item | Value |
|---|---|
| Parent menu | Tender Management → Tender Configurations |
| Entry surface | UI-01 — Tender Configuration Home |
| Configuration step | CFG-01 |
| Screen name | Tender Profile |
| Applies to | One created Tender Configuration |
| Current family context | Information Technology, but screen pattern must support other STD families later |
| Lifecycle stage | Configuration |

---

## 2. User Goal

The user confirms the basic identity and setup context for the tender configuration before completing detailed STD-specific sections.

---

## 3. Single User Decision

> Is this the correct procurement package and tender profile to configure?

Everything on this screen must support that decision.

---

## 4. What This Screen Owns

Tender Profile owns only high-level tender identity and configuration context.

| Owns | Does not own |
|---|---|
| Tender display title | Tender Data Sheet values |
| Short scope summary | IT requirements |
| Lot structure summary | Implementation schedule |
| Procurement category / STD family confirmation | System inventory |
| Standard Tender Document display | Price schedules |
| Basic configuration notes | Evaluation criteria |
| Read-only package context | Forms and evidence |
|  | Contract values |
|  | Review, preview, publication, award, or contract administration |

---

## 5. STD Grounding

This screen is not a detailed IT STD content section. It establishes the tender identity and context used by the later STD-controlled configuration screens.

For the Information Technology STD family, the detailed STD-controlled configuration is completed in later steps:

| Later step | STD area |
|---|---|
| CFG-02 — Tender Data Sheet | Section II — TDS |
| CFG-03 — IT Requirements | Requirements of the Information System and Technical Requirements |
| CFG-04 — Implementation Schedule | Implementation Schedule |
| CFG-05 — System Inventory & Bidder Background | System Inventory Tables and Background / Informational Materials |
| CFG-06 — Price Schedule | Price Schedule forms |
| CFG-07 — Evaluation Setup | Evaluation and Qualification Criteria |
| CFG-08 — Forms & Evidence | Non-price tendering forms and bidder evidence |
| CFG-09 — Contract Values | SCC and contract-facing values |

This screen must not expose locked ITT/GCC text, clause trees, hashes, rule IDs, schema metadata, or source anchors.

---

## 6. Entry Conditions

The screen may be opened only after a Tender Configuration has been created from an Approved Procurement Package.

Required context must already exist:

| Required context | Source |
|---|---|
| Procurement Package Ref | Approved Procurement Package |
| Package Title | Approved Procurement Package |
| Procuring Entity | Approved Procurement Package |
| Procurement Method | Approved Procurement Package |
| Procurement Category / STD Family | Approved Procurement Package or controlled classification |
| Applicable Standard Tender Document | STD selection logic |
| Tender Configuration Ref | Created Tender Configuration |

If the configuration has not been created, the user must be routed to UI-M01 — Create Tender Configuration.

---

## 7. Exit Conditions

The user may continue to CFG-02 — Tender Data Sheet when:

1. Tender title is confirmed.
2. Scope summary is present.
3. Lot structure is confirmed as single lot, multiple lots, or not applicable.
4. STD family is confirmed.
5. Applicable Standard Tender Document is selected or system-confirmed.
6. No blocker exists on tender identity consistency.

Warnings may remain if they do not prevent the user from starting TDS configuration.

---

## 8. Page Layout

### 8.1 Page Header

Title:

```text
Tender Profile
```

Subtitle:

```text
Confirm the tender identity, procurement context, lot structure, and applicable standard tender document.
```

Primary actions:

| Button | Rule |
|---|---|
| Save Profile | Enabled when editable fields have changes |
| Continue to Tender Data Sheet | Enabled only when exit conditions pass |

Secondary actions:

| Button | Rule |
|---|---|
| Back to Configuration Home | Always available |
| Run Readiness Check | Optional shortcut; summary only |

Do not show `Finalize`, `Submit for Review`, `Publish`, or `Create Tender` on this screen.

---

### 8.2 Context Strip

Show only:

| Label | Example | Editability |
|---|---|---|
| Procurement Package Ref | `PP-ICT-2024-009` | Read-only |
| Tender Configuration Ref | `TC-2024-00037` | Read-only |
| Procuring Entity | `National Treasury` | Read-only |
| Procurement Method | `Open National Tender` | Read-only |
| STD Family | `Information Technology` | Read-only unless controlled change is permitted before configuration starts |
| Standard Tender Document | `IT Standard Tender Document — April 2022` | Read-only unless multiple valid versions are available and user has permission |
| Status | `In progress` | Read-only |

Use full label `Procurement Package Ref`; do not use `Planning Pkg Ref` or `Tender Shell`.

---

## 9. Main Form Sections

### 9.1 Tender Identity

| Field | Required | Editable | Exact helper text |
|---|---:|---:|---|
| Tender Title | Yes | Yes, if policy allows | `Use a clear public-facing title for the tender.` |
| Short Scope Summary | Yes | Yes | `Summarize what is being procured in one or two sentences.` |
| Procuring Entity | Yes | No | `Taken from the approved procurement package.` |
| Procurement Method | Yes | No | `Taken from the approved procurement package.` |

Sample:

| Field | Value |
|---|---|
| Tender Title | `Data Center Hardware Refresh` |
| Short Scope Summary | `Procurement of server, storage, networking, installation, configuration, warranty, and support services for the data center refresh.` |

---

### 9.2 Lot Structure

| Field | Required | Editable | Exact helper text |
|---|---:|---:|---|
| Lot Structure | Yes | Yes | `Confirm whether this tender has one lot or multiple lots.` |
| Lot Summary | Conditional | Yes | `Describe each lot only if the tender has multiple lots.` |

Allowed values:

```text
Single lot
Multiple lots
Not applicable
```

If `Multiple lots` is selected, show a compact lot table:

| Column | Example |
|---|---|
| Lot No. | `Lot 1` |
| Lot Title | `Server and Storage Infrastructure` |
| Short Description | `Supply, installation, and configuration of server and storage equipment.` |

Do not configure price schedules, evaluation lots, or award strategy here. Those belong in later steps.

---

### 9.3 STD Context

| Field | Required | Editable | Exact helper text |
|---|---:|---:|---|
| STD Family | Yes | Usually no | `The STD family determines which configuration steps and rules apply.` |
| Standard Tender Document | Yes | Controlled | `The tender will be configured using this standard tender document.` |
| STD Version Label | Yes | No | `Shown for traceability; users do not edit the STD master here.` |

Sample:

| Field | Value |
|---|---|
| STD Family | `Information Technology` |
| Standard Tender Document | `IT Standard Tender Document — April 2022` |
| STD Version Label | `April 2022` |

Do not show hashes, package codes, source anchors, clause IDs, or schema versions in the default user interface.

---

### 9.4 Profile Notes

Optional field:

| Field | Required | Editable | Exact helper text |
|---|---:|---:|---|
| Configuration Note | No | Yes | `Add a short internal note for officers working on this configuration. Do not include bidder-facing requirements here.` |

This field is internal to the configuration workflow and must not be rendered into the tender document.

---

## 10. Validation Rules

Show calm validation only.

| Rule | Severity | User-facing message |
|---|---|---|
| Missing tender title | Blocker | `Add a tender title before continuing.` |
| Missing short scope summary | Blocker | `Add a short scope summary before continuing.` |
| Lot structure not confirmed | Blocker | `Confirm the lot structure before continuing.` |
| STD family missing | Blocker | `Confirm the STD family before continuing.` |
| Standard Tender Document missing | Blocker | `Confirm the standard tender document before continuing.` |
| Long or unclear title | Warning | `Review the tender title for clarity.` |
| Scope summary appears too vague | Warning | `Review the scope summary so officers can understand the tender context.` |

Do not show rule IDs, schema errors, clause errors, render-block errors, or audit logs on this screen.

---

## 11. Downstream Impact

Tender Profile feeds later screens as context only.

| Downstream surface | How it uses Tender Profile |
|---|---|
| Tender Data Sheet | Uses tender title, PE, method, STD family, and package context |
| IT Requirements | Uses scope and STD family context |
| Implementation Schedule | Uses lot structure and scope context where relevant |
| Price Schedule | Uses lot structure where pricing may be lot-specific |
| Evaluation Setup | Uses lot structure and procurement method context |
| Forms & Evidence | Uses STD family and method context |
| Contract Values | Uses tender identity, PE, method, and lot context |
| Readiness Check | Confirms profile completeness before review |
| Tender Preview | Renders tender title and identity context |

This screen must not make downstream decisions for these later areas.

---

## 12. Forbidden Content

Do not show or edit:

```text
Tender Shell
TenderSTDInstance
STD binding
STD package code
hash
schema version
source anchor
clause tree
ITT clause editor
GCC clause editor
price lines
evaluation marks
requirement rows
implementation milestones
inventory rows
forms checklist
SCC clause text
approval decision
publication controls
```

---

## 13. API Contract

Endpoint example:

```text
GET /api/tender-configurations/{configuration_id}/profile
```

Response shape:

```json
{
  "configuration_id": "TC-2024-00037",
  "procurement_package_ref": "PP-ICT-2024-009",
  "tender_configuration_ref": "TC-2024-00037",
  "tender_title": "Data Center Hardware Refresh",
  "short_scope_summary": "Procurement of server, storage, networking, installation, configuration, warranty, and support services for the data center refresh.",
  "procuring_entity_name": "National Treasury",
  "procurement_method_label": "Open National Tender",
  "std_family": "Information Technology",
  "standard_tender_document_label": "IT Standard Tender Document — April 2022",
  "std_version_label": "April 2022",
  "lot_structure": "Single lot",
  "lots": [],
  "configuration_note": "",
  "status_label": "In progress",
  "blocker_count": 0,
  "warning_count": 1,
  "can_continue": true
}
```

Save endpoint:

```text
POST /api/tender-configurations/{configuration_id}/profile
```

Editable payload:

```json
{
  "tender_title": "Data Center Hardware Refresh",
  "short_scope_summary": "Procurement of server, storage, networking, installation, configuration, warranty, and support services for the data center refresh.",
  "lot_structure": "Single lot",
  "lots": [],
  "configuration_note": ""
}
```

Do not allow the UI to post internal STD version hashes, binding IDs, or raw legal text edits.

---

## 14. Stitch Prompt

```text
Design CFG-01 — Tender Profile for the KenTender Tender Configurations module.

This screen is opened from Tender Configuration Home after a Tender Configuration has been created from an Approved Procurement Package.

Screen purpose:
Confirm the tender identity, procurement context, lot structure, and applicable standard tender document.

Single user decision:
Is this the correct procurement package and tender profile to configure?

Use procurement-facing language only. Do not use internal terms such as Tender Shell, TenderSTDInstance, STD binding, STD package code, schema version, hash, rule ID, or source anchor.

Page title:
Tender Profile

Subtitle:
Confirm the tender identity, procurement context, lot structure, and applicable standard tender document.

Context strip fields:
- Procurement Package Ref
- Tender Configuration Ref
- Procuring Entity
- Procurement Method
- STD Family
- Standard Tender Document
- Status

Main sections:
1. Tender Identity
   - Tender Title
   - Short Scope Summary
   - Procuring Entity, read-only
   - Procurement Method, read-only

2. Lot Structure
   - Lot Structure with options: Single lot, Multiple lots, Not applicable
   - If Multiple lots, show a compact lot table with Lot No., Lot Title, Short Description

3. Standard Tender Document
   - STD Family
   - Standard Tender Document
   - STD Version Label

4. Profile Notes
   - Configuration Note

Primary buttons:
- Save Profile
- Continue to Tender Data Sheet

Secondary button:
- Back to Configuration Home

Validation messages should be calm and user-facing:
- Add a tender title before continuing.
- Add a short scope summary before continuing.
- Confirm the lot structure before continuing.
- Confirm the standard tender document before continuing.

Do not show TDS fields, IT requirements, implementation milestones, inventory rows, price lines, evaluation marks, forms checklist, contract values, approval controls, publication controls, legal clause editors, hashes, rule IDs, or audit logs.
```

---

## 15. Cursor Prompt

```text
Implement CFG-01 — Tender Profile for the KenTender Tender Configurations module.

The screen is part of a created Tender Configuration and must be reachable from UI-01 Tender Configuration Home.

Use the v6 control model:
- UI-00 Dashboard is generic across STD families.
- UI-M01 creates a Tender Configuration from an Approved Procurement Package.
- UI-01 is the configuration home.
- CFG-01 Tender Profile confirms identity/context only.

Primary object:
TenderConfigurationProfile

Screen owns:
- tender_title
- short_scope_summary
- lot_structure
- lots summary when multiple lots are used
- configuration_note

Screen references read-only:
- procurement_package_ref
- tender_configuration_ref
- procuring_entity_name
- procurement_method_label
- std_family
- standard_tender_document_label
- std_version_label
- status_label

Screen must not render or edit:
- TDS values
- requirement rows
- implementation milestones
- inventory rows
- price lines
- evaluation criteria or marks
- forms/evidence checklist
- SCC/contract values
- approval decisions
- publication controls
- ITT/GCC legal text
- internal terms or metadata such as Tender Shell, TenderSTDInstance, STD binding, STD package code, hash, schema version, source anchor, or rule ID

Required layout:
1. Header
   Title: Tender Profile
   Subtitle: Confirm the tender identity, procurement context, lot structure, and applicable standard tender document.

2. Context strip
   Fields: Procurement Package Ref, Tender Configuration Ref, Procuring Entity, Procurement Method, STD Family, Standard Tender Document, Status.

3. Form sections
   Tender Identity, Lot Structure, Standard Tender Document, Profile Notes.

4. Footer actions
   Back to Configuration Home, Save Profile, Continue to Tender Data Sheet.

Validation:
- Block Continue if tender_title is missing.
- Block Continue if short_scope_summary is missing.
- Block Continue if lot_structure is missing.
- Block Continue if std_family or standard_tender_document_label is missing.
- Show only user-facing validation messages, not rule IDs.

Acceptance criteria:
- A procurement user can confirm the tender profile without seeing technical STD internals.
- The screen does not ask the user to configure TDS, requirements, pricing, evaluation, forms, or contract values.
- Continue routes to CFG-02 Tender Data Sheet only when profile blockers are cleared.
- All labels match this specification exactly.
```

---

## 16. Acceptance Checklist

| Test | Pass condition |
|---|---|
| User decision clarity | User can confirm whether this is the correct tender profile to configure. |
| Lifecycle accuracy | Screen opens only after configuration creation from an Approved Procurement Package. |
| Ownership clarity | Screen owns only profile fields. |
| No internal terminology | No `Tender Shell`, `binding`, `instance`, `hash`, or `package code` appears. |
| Simplicity | No downstream configuration tables are shown. |
| STD coverage | STD family and standard tender document are visible as context. |
| Downstream safety | Later screens receive context without this screen making their decisions. |
| Implementation readiness | Stitch and Cursor prompts include exact labels, text, fields, and exclusions. |

---

## 17. Final Rule

If a field does not help the user confirm tender identity, context, lot structure, or standard tender document, remove it from CFG-01 Tender Profile.
