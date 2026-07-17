# CFG-02 — Tender Data Sheet v6

**Product:** KenTender  
**Area:** Tender Management → Tender Configurations  
**Surface type:** Configuration step  
**Configuration step:** CFG-02  
**Screen name:** Tender Data Sheet  
**STD family:** Information Technology  
**Status:** Revised v6 specification  

---

## 1. Purpose

Configure the tender-specific instructions and parameters that complete the Tender Data Sheet for the selected IT Standard Tender Document.

This screen helps the procurement user answer one question:

> What tender-specific instructions, dates, submission rules, eligibility settings, securities, and preference settings apply to this tender?

---

## 2. User-facing entry path

The user reaches this screen from:

`Tender Management → Tender Configurations → Tender Configuration Home → Tender Data Sheet`

This screen is available after **CFG-01 — Tender Profile** has enough confirmed context to identify the tender, procuring entity, procurement method, STD family, and selected Standard Tender Document.

---

## 3. STD grounding

This screen maps primarily to:

- **Section II — Tender Data Sheet**
- Tender-specific parameters that complete or modify the locked Instructions to Tenderers where the STD allows completion

The screen must not expose the full ITT clause tree. It should present practical user-facing fields grouped by tender task.

---

## 4. Screen ownership

| Area | Rule |
|---|---|
| Owns | Tender Data Sheet values for this tender configuration |
| Does not own | Tender identity, IT requirements, implementation schedule, system inventory, price schedule rows, scoring criteria, bidder submission forms, SCC values, review decisions, publication actions |
| Reads from | Approved Procurement Package, Tender Profile, selected Standard Tender Document, method rules |
| Feeds | Evaluation Setup, Forms & Evidence, Contract Values, Readiness Check, Tender Document Preview |

---

## 5. Page header

**Title:**

`Tender Data Sheet`

**Subtitle:**

`Set the tender-specific instructions, dates, submission rules, and allowed options for this IT tender.`

**Primary actions:**

- `Save Tender Data Sheet`
- `Run Check`
- `Continue to IT Requirements`

**Secondary action:**

- `Back to Configuration Home`

Do not use:

- `Edit ITT`
- `Clause Configuration`
- `Rule Matrix`
- `STD Parameter Editor`

---

## 6. Context strip

Show only:

| Label | Example |
|---|---|
| Procurement Package Ref | `PP-ICT-2024-009` |
| Tender Title | `Data Center Hardware Refresh` |
| Procuring Entity | `National Treasury` |
| Procurement Method | `Open National Tender` |
| STD Family | `Information Technology` |
| Standard Tender Document | `IT Standard Tender Document — April 2022` |
| Configuration Status | `In Progress` |
| Issues | `0 Blockers / 2 Warnings` |

Do not show hashes, rule IDs, binding IDs, schema versions, or internal object names.

---

## 7. Main layout

Use a simple grouped form with a right-side guidance panel.

Recommended groups:

1. **Tender Communication**
2. **Key Dates**
3. **Submission Rules**
4. **Eligibility and Participation**
5. **Tender Security**
6. **Preferences and Reservations**
7. **Bid Opening**

Do not show all TDS clauses as a legal document. Show fields the user must complete.

---

## 8. Field groups and exact fields

### 8.1 Tender Communication

| Field label | Type | Rule |
|---|---|---|
| Contact Officer | Text / user selector | Required |
| Contact Email | Email | Required |
| Clarification Submission Method | Select | Required |
| Clarification Deadline | Date/time | Required if clarifications are allowed |
| Pre-tender Meeting | Yes/No | Required |
| Pre-tender Meeting Details | Text area | Required if pre-tender meeting is Yes |

Allowed clarification methods:

- `E-Procurement Portal`
- `Official Email`
- `Physical Submission`
- `As stated in tender notice`

### 8.2 Key Dates

| Field label | Type | Rule |
|---|---|---|
| Tender Publication Date | Date/time | Read-only if owned by Tender Management publication workflow; otherwise planned date |
| Tender Submission Deadline | Date/time | Required |
| Tender Opening Date and Time | Date/time | Required |
| Bid Validity Period | Number + unit | Required |

Default unit for bid validity:

`days`

### 8.3 Submission Rules

| Field label | Type | Rule |
|---|---|---|
| Submission Channel | Select | Required |
| Submission Language | Select | Required |
| Tender Currency | Select | Required |
| Alternative Tenders Allowed | Yes/No | Required |
| Lots Allowed | Yes/No | Read from Tender Profile; editable only in Tender Profile |
| Joint Ventures Allowed | Yes/No | Required |

Allowed submission channels:

- `E-Procurement Portal`
- `Physical Submission`
- `Hybrid Submission`

### 8.4 Eligibility and Participation

| Field label | Type | Rule |
|---|---|---|
| Eligible Tenderers | Select | Required |
| Reserved Procurement | Yes/No | Required |
| Reservation Category | Select | Required if Reserved Procurement is Yes |
| Local Participation Requirement | Text area | Optional unless method/rule requires it |

Allowed reservation categories:

- `Youth`
- `Women`
- `Persons with Disabilities`
- `Local Contractors / Suppliers`
- `Other statutory reservation`

### 8.5 Tender Security

| Field label | Type | Rule |
|---|---|---|
| Tender Security Required | Yes/No | Required |
| Tender Security Type | Select | Required if security is required |
| Tender Security Amount | Money | Required if security is required |
| Tender Security Validity Period | Number + unit | Required if security is required |

Allowed security types:

- `Tender Security`
- `Tender-Securing Declaration`
- `Not Required`

### 8.6 Preferences and Reservations

| Field label | Type | Rule |
|---|---|---|
| Margin of Preference Applies | Yes/No | Required |
| Preference Basis | Select | Required if margin applies |
| Preference Evidence Required | Text area | Required if margin applies |

Allowed preference basis:

- `Local supplier / contractor preference`
- `Citizen contractor / supplier preference`
- `Other allowed statutory preference`

Do not calculate bidder preference adjustments here. Actual application belongs to bid evaluation.

### 8.7 Bid Opening

| Field label | Type | Rule |
|---|---|---|
| Opening Method | Select | Required |
| Opening Location / Portal | Text | Required |
| Opening Attendance Allowed | Yes/No | Required |
| Opening Notes | Text area | Optional |

Allowed opening methods:

- `Electronic Opening`
- `Physical Opening`
- `Hybrid Opening`

---

## 9. Status and validation labels

Use only:

| Label | Meaning |
|---|---|
| Complete | Required TDS values in this group are complete |
| Needs attention | Required value is missing or inconsistent |
| Not started | No values have been entered in this group |
| In progress | Some values are present but not complete |

Do not use:

- `Locked`
- `Ready`
- raw rule IDs
- clause IDs as default labels

---

## 10. Right guidance panel

Panel title:

`Tender Data Sheet Guidance`

Panel text:

`Complete only the tender-specific instructions required for this procurement. The standard Instructions to Tenderers remain controlled by the selected Standard Tender Document and are not edited here.`

Show compact guidance rows:

| Label | Text |
|---|---|
| What this affects | `Submission instructions, eligibility settings, securities, preference settings, and bid opening details.` |
| Used later by | `Evaluation Setup, Forms & Evidence, Contract Values, and Tender Document Preview.` |
| Not configured here | `Technical requirements, price items, evaluation scores, bidder forms, and SCC contract values.` |

---

## 11. Downstream impact

This screen feeds:

- **CFG-03 — IT Requirements** where method or participation rules affect requirement treatment
- **CFG-07 — Evaluation Setup** for preference, eligibility, and security-related evaluation rules
- **CFG-08 — Forms & Evidence** for required declarations, tender security, and eligibility evidence
- **CFG-09 — Contract Values** where TDS values affect contract-facing parameters
- **Readiness Check** for completeness and consistency
- **Tender Document Preview** for rendered TDS output

This screen must not configure:

- technical requirements
- delivery milestones
- inventory items
- price line items
- evaluation marks or pass scores
- actual bidder submissions
- approval workflow decisions
- publication actions

---

## 12. Sample table/card summary

If using a grouped summary table above the form, use this exact content:

| Group | Description | Status | Issues | Action |
|---|---|---|---|---|
| Tender Communication | Define contact officer, clarification method, and pre-tender meeting information. | Complete | — | Review |
| Key Dates | Set submission, opening, and validity dates for this tender. | Needs attention | Submission deadline missing | Fix |
| Submission Rules | Confirm channel, language, currency, alternatives, lots, and joint venture rules. | In progress | 1 warning | Continue |
| Eligibility and Participation | Confirm who may participate and whether any reservation applies. | Complete | — | Review |
| Tender Security | Define whether tender security is required and the accepted security type. | Not started | Required section not started | Start |
| Preferences and Reservations | State whether margin of preference applies and what evidence is required. | Complete | — | Review |
| Bid Opening | Confirm how and where the tender opening will take place. | In progress | Opening location missing | Continue |

---

## 13. API shape

```json
{
  "configuration_id": "TCFG-2024-0009",
  "procurement_package_ref": "PP-ICT-2024-009",
  "tender_title": "Data Center Hardware Refresh",
  "procuring_entity_name": "National Treasury",
  "procurement_method_label": "Open National Tender",
  "std_family_label": "Information Technology",
  "standard_tender_document_label": "IT Standard Tender Document — April 2022",
  "configuration_status_label": "In Progress",
  "blocker_count": 1,
  "warning_count": 2,
  "tds_groups": [
    {
      "group_key": "key_dates",
      "group_label": "Key Dates",
      "description": "Set submission, opening, and validity dates for this tender.",
      "status_label": "Needs attention",
      "issue_summary": "Submission deadline missing",
      "action_label": "Fix"
    }
  ],
  "tds_values": {
    "contact_officer": "Jane Wanjiru",
    "contact_email": "procurement@example.go.ke",
    "clarification_submission_method": "E-Procurement Portal",
    "clarification_deadline": "2024-06-10T17:00:00+03:00",
    "pre_tender_meeting": false,
    "submission_channel": "E-Procurement Portal",
    "submission_language": "English",
    "tender_currency": "KES",
    "alternative_tenders_allowed": false,
    "joint_ventures_allowed": true,
    "tender_security_required": true,
    "tender_security_type": "Tender Security",
    "tender_security_amount": 500000,
    "tender_security_currency": "KES",
    "margin_of_preference_applies": false,
    "opening_method": "Electronic Opening"
  }
}
```

---

## 14. Stitch prompt

```text
Design CFG-02 — Tender Data Sheet for KenTender Tender Configurations.

Screen purpose:
Set the tender-specific instructions, dates, submission rules, and allowed options for this IT tender.

User decision:
What tender-specific instructions, dates, submission rules, eligibility settings, securities, and preference settings apply to this tender?

Use a clean grouped form, not a clause editor.

Header:
Title: Tender Data Sheet
Subtitle: Set the tender-specific instructions, dates, submission rules, and allowed options for this IT tender.

Context strip fields:
- Procurement Package Ref
- Tender Title
- Procuring Entity
- Procurement Method
- STD Family
- Standard Tender Document
- Configuration Status
- Issues

Main groups:
1. Tender Communication
2. Key Dates
3. Submission Rules
4. Eligibility and Participation
5. Tender Security
6. Preferences and Reservations
7. Bid Opening

Use exact group descriptions:
- Tender Communication: Define contact officer, clarification method, and pre-tender meeting information.
- Key Dates: Set submission, opening, and validity dates for this tender.
- Submission Rules: Confirm channel, language, currency, alternatives, lots, and joint venture rules.
- Eligibility and Participation: Confirm who may participate and whether any reservation applies.
- Tender Security: Define whether tender security is required and the accepted security type.
- Preferences and Reservations: State whether margin of preference applies and what evidence is required.
- Bid Opening: Confirm how and where the tender opening will take place.

Right guidance panel:
Title: Tender Data Sheet Guidance
Text: Complete only the tender-specific instructions required for this procurement. The standard Instructions to Tenderers remain controlled by the selected Standard Tender Document and are not edited here.

Primary buttons:
- Save Tender Data Sheet
- Run Check
- Continue to IT Requirements

Do not show clause trees, raw ITT text editing, rule IDs, hash values, schema names, internal object names, technical requirements, price lines, evaluation marks, evidence forms, SCC values, review decisions, or publication controls.
```

---

## 15. Cursor prompt

```text
Implement CFG-02 — Tender Data Sheet in the Tender Configurations module.

This is a grouped form for TDS values, not a legal clause editor.

Route:
Tender Management → Tender Configurations → Tender Configuration Home → Tender Data Sheet

Primary object:
TenderDataSheetConfiguration

Screen owns:
- tender communication values
- key dates
- submission rules
- eligibility and participation settings
- tender security values
- preferences and reservations
- bid opening values

Screen does not own:
- Tender Profile identity values
- IT requirements
- implementation schedule
- system inventory
- price schedule
- evaluation scoring
- forms/evidence configuration
- SCC/contract values
- review decisions
- publication actions

Render:
1. Page header with title "Tender Data Sheet".
2. Subtitle exactly: "Set the tender-specific instructions, dates, submission rules, and allowed options for this IT tender."
3. Context strip with Procurement Package Ref, Tender Title, Procuring Entity, Procurement Method, STD Family, Standard Tender Document, Configuration Status, Issues.
4. Grouped form sections:
   - Tender Communication
   - Key Dates
   - Submission Rules
   - Eligibility and Participation
   - Tender Security
   - Preferences and Reservations
   - Bid Opening
5. Right guidance panel using the exact text in the specification.
6. Footer actions:
   - Save Tender Data Sheet
   - Run Check
   - Continue to IT Requirements

Validation:
- Show only summary labels: Complete, In progress, Needs attention, Not started.
- Do not show raw rule IDs or clause IDs in the default UI.
- Continue to IT Requirements is disabled if required TDS blockers remain.

Implementation constraints:
- Do not use Tailwind CDN in production.
- Use local KenTender UI styles/components.
- Do not hardcode realistic data except seed fixtures.
- Do not show internal terms such as binding, instance, shell, package code, schema version, rule hash, or source anchor.
```

---

## 16. Acceptance checklist

| Check | Pass condition |
|---|---|
| User decision clarity | User understands they are completing tender-specific TDS values. |
| STD grounding | Screen maps to Section II — Tender Data Sheet and does not edit locked ITT text. |
| Ownership clarity | Screen owns only TDS values. |
| Simplicity | Screen uses grouped task-based sections, not clause trees. |
| Downstream awareness | Screen states its effect on Evaluation, Forms, Contract Values, Readiness, and Preview. |
| No internal terminology | No shell, instance, binding, hash, schema, package code, or rule ID in default UI. |
| Status discipline | Only Complete, In progress, Needs attention, and Not started are used. |
| Implementation readiness | Stitch and Cursor prompts contain exact labels, descriptions, fields, actions, and exclusions. |

---

## 17. Final rule

If a field does not help the procurement user complete the Tender Data Sheet, remove it from CFG-02.
