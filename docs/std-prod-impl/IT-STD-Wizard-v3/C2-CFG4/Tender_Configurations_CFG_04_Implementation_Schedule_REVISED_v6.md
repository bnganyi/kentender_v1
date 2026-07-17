# CFG-04 — Implementation Schedule v6

**Product:** KenTender  
**Area:** Tender Management → Tender Configurations  
**Surface type:** Configuration step  
**Configuration step:** CFG-04  
**Screen name:** Implementation Schedule  
**STD family:** Information Technology  
**Status:** Revised v6 specification  

---

## 1. Purpose

Define how the IT solution will be delivered after contract award.

This screen helps the procurement user answer one question:

> How should the successful bidder deliver, install, configure, test, train, hand over, and support the solution?

---

## 2. User-facing entry path

The user reaches this screen from:

`Tender Management → Tender Configurations → Tender Configuration Home → Implementation Schedule`

This screen is available after **CFG-03 — IT Requirements** has enough requirement information to identify what must be delivered.

---

## 3. STD grounding

This screen maps primarily to:

- **Section VII — Implementation Schedule**

It defines bidder-facing delivery expectations, milestones, deliverables, timing, and acceptance checkpoints.

It must not become project execution, inspection management, payment certification, contract administration, or post-award monitoring.

---

## 4. Screen ownership

| Area | Rule |
|---|---|
| Owns | Delivery approach, delivery milestones, expected duration, milestone triggers, deliverables, acceptance expectations, schedule evidence expectations |
| Does not own | Tender identity, TDS values, detailed IT requirements, system inventory/background records, price schedule rows, evaluation marks, bidder form checklist, SCC values, review decisions, publication actions, post-award execution records |
| Reads from | Approved Procurement Package, Tender Profile, Tender Data Sheet, IT Requirements, selected IT Standard Tender Document |
| Feeds | System Inventory & Bidder Background, Price Schedule, Forms & Evidence, Contract Values, Readiness Check, Tender Document Preview |

---

## 5. Page header

**Title:**

`Implementation Schedule`

**Subtitle:**

`Define the delivery approach, milestones, deliverables, timing, and acceptance checkpoints for this IT tender.`

**Primary actions:**

- `Add Milestone`
- `Save Schedule`
- `Run Check`
- `Continue to System Inventory & Bidder Background`

**Secondary action:**

- `Back to Configuration Home`

Do not use:

- `Project Execution`
- `Payment Milestones`
- `Contract Administration`
- `Implementation Monitoring`
- `Inspection Records`
- `Work Progress`

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
| Issues | `1 Blocker / 2 Warnings` |

Do not show hashes, rule IDs, binding IDs, schema versions, internal object names, or technical metadata.

---

## 7. Main layout

Use a focused schedule configuration layout:

1. Page header and actions
2. Tender context strip
3. Delivery approach selector
4. Milestones table or single-delivery form
5. Schedule guidance panel
6. Footer action bar
7. Milestone drawer opened only when adding or editing a milestone

Do not show implementation execution dashboards, payment percentages, site inspection records, contract administration events, or actual completion statuses.

---

## 8. Delivery approach selector

The user must choose one delivery approach.

| Option | Meaning | UI behavior |
|---|---|---|
| `Phased Delivery` | The solution will be delivered through multiple milestones or phases. | Show the milestones table and `Add Milestone`. |
| `Single Turnkey Delivery` | The solution will be delivered as one complete package. | Hide the phase table and show a single-delivery configuration form. |

Default value:

`Phased Delivery`

unless an approved procurement package or prior configuration explicitly indicates single turnkey delivery.

Do not use delivery approach values as hidden logic without showing the selected approach to the user.

---

## 9. Phased Delivery table

When `Phased Delivery` is selected, show this exact table.

| Column | Purpose |
|---|---|
| ID | Milestone reference, for example `MS-001` |
| Milestone | Clear bidder-facing milestone name |
| Expected Duration | Expected duration for that milestone |
| Trigger | What starts the milestone |
| Key Deliverable | Main deliverable expected from the bidder |
| Acceptance | How the milestone will be accepted |
| Status | Local completeness status |
| Actions | `Edit`, `Fix`, or `Review` |

Do not include payment percentage, actual progress, completion date, inspection status, invoice status, or contract administration fields.

---

## 10. Sample phased-delivery rows

Use these sample rows in Stitch/Cursor fixtures unless a better approved seed fixture is supplied:

| ID | Milestone | Expected Duration | Trigger | Key Deliverable | Acceptance | Status | Action |
|---|---|---|---|---|---|---|---|
| MS-001 | Project Kick-off and Detailed Work Plan | 2 weeks | Contract signing and notice to proceed | Approved implementation work plan | Acceptance defined | Complete | Edit |
| MS-002 | Hardware Supply and Delivery | 8 weeks | Approved work plan | Delivered server and storage equipment | Acceptance defined | Complete | Edit |
| MS-003 | Installation and Configuration | 4 weeks | Delivery acceptance for equipment | Installed and configured infrastructure | Missing acceptance | Needs attention | Fix |
| MS-004 | Testing and Commissioning | 3 weeks | Installation completion | Test report and operational readiness confirmation | Acceptance defined | Complete | Edit |
| MS-005 | Training and Handover | 2 weeks | Commissioning acceptance | User training records and handover pack | Acceptance defined | Complete | Edit |
| MS-006 | Warranty and Support Start | Not time-bound | Final handover acceptance | Confirmed support commencement | Not applicable | Complete | Review |

---

## 11. Single Turnkey Delivery behavior

When `Single Turnkey Delivery` is selected, do not show the phased milestones table.

Show one form titled:

`Single Delivery Milestone`

Use these exact fields:

| Field label | Type | Rule |
|---|---|---|
| Expected Delivery Duration | Text / duration input | Required |
| Delivery Trigger | Text / select | Required |
| Key Deliverables | Text area | Required |
| Acceptance Expectation | Select | Required |
| Acceptance Description | Text area | Required if acceptance is defined |
| Evidence Expected | Text area | Required if evidence is required |
| Notes to Bidders | Text area | Optional |

Example values:

| Field | Example |
|---|---|
| Expected Delivery Duration | `6 months` |
| Delivery Trigger | `Contract signing and notice to proceed` |
| Key Deliverables | `Fully supplied, installed, configured, tested, documented, and handed-over IT solution` |
| Acceptance Expectation | `Acceptance defined` |
| Acceptance Description | `Procuring Entity confirms delivery, installation, testing, training, documentation, and operational readiness.` |
| Evidence Expected | `Completion report, test results, training records, and handover certificate.` |

---

## 12. Switching delivery approach

If the user switches from `Phased Delivery` to `Single Turnkey Delivery` after milestones already exist, show this confirmation modal.

**Modal title:**

`Switch to Single Turnkey Delivery?`

**Modal text:**

`This will replace the phased delivery view with one single delivery milestone. Existing milestone details will be kept in draft history and will be restored if you switch back before submission for review.`

**Buttons:**

- `Cancel`
- `Switch to Single Delivery`

If the user switches from `Single Turnkey Delivery` back to `Phased Delivery`, restore any previously saved draft milestones where available.

Do not silently delete milestone data.

---

## 13. Add/Edit milestone drawer

The drawer must use this exact structure.

### 13.1 Milestone

| Field label | Type | Rule |
|---|---|---|
| Milestone Name | Text | Required |
| Milestone Description | Text area | Required |
| Sequence | Number | Required; editable |
| Expected Duration | Text / duration input | Required; editable |
| Start Trigger | Text / select | Required; editable |

### 13.2 Deliverables

| Field label | Type | Rule |
|---|---|---|
| Key Deliverable | Text | Required |
| Deliverable Description | Text area | Required |
| Related IT Requirements | Multi-select / reference | Optional, but recommended |

### 13.3 Acceptance

| Field label | Type | Rule |
|---|---|---|
| Acceptance Expectation | Select | Required |
| Acceptance Description | Text area | Required if acceptance is defined |
| Evidence Expected | Text area | Required if evidence is expected |

Allowed acceptance expectation values:

- `Acceptance defined`
- `Not applicable`

### 13.4 References

Show only compact references:

| Label | Allowed text |
|---|---|
| IT Requirements | `Linked to IT Requirements` / `No requirement link selected` |
| Price Schedule | `May require price schedule item` / `No price schedule link expected` |
| Contract Values | `May carry into contract values` / `No contract carry-forward expected` |

Do not use the drawer to configure price lines, evaluation marks, formal submission checklist rows, SCC clauses, payment certificates, inspection records, or actual project progress.

---

## 14. Template and source behavior

Template values may prefill the schedule, but they must not become magical or unexplained.

Every prefilled value must show a clear source internally and, where visible, a plain source label.

Allowed source labels:

| Source label | Meaning | Editable? |
|---|---|---|
| `User-entered` | User entered or changed the value. | Yes |
| `Suggested from IT Standard Tender Document` | Suggested by the applicable STD structure or template. | Yes |
| `Suggested from IT Requirements` | Suggested from configured requirements. | Yes |
| `Derived from milestone sequence` | Calculated from the current schedule order. | Usually no, but user may change the underlying sequence. |
| `Not configured` | No value exists yet. | User must complete it if required. |

Do not use `Locked` for template-prefilled durations, triggers, deliverables, or acceptance descriptions.

Use:

`Suggested from IT Standard Tender Document — Edit / Reset`

not:

`Locked`

---

## 15. Status labels

Use only:

| Status | Meaning |
|---|---|
| Complete | Milestone or single-delivery configuration has required duration, trigger, deliverable, and acceptance information. |
| Needs attention | Required delivery information is missing or inconsistent. |
| In progress | Milestone has been started but is not complete. |
| Not started | Placeholder milestone exists but has no meaningful content. |

Do not use:

- `Valid`
- `Ready`
- `Locked`
- `Executed`
- `In delivery`
- `Paid`
- `Certified`
- raw rule IDs

---

## 16. Right guidance panel

Panel title:

`Implementation Schedule Guidance`

Panel text:

`Define how the successful bidder will deliver the solution. Keep this focused on planned milestones, deliverables, timing, and acceptance checkpoints. Actual delivery, inspection, payment, and contract administration happen after award.`

Show compact guidance rows:

| Label | Text |
|---|---|
| What this affects | `Bidder delivery obligations, price schedule structure, contract values, and tender preview.` |
| Used later by | `System Inventory & Bidder Background, Price Schedule, Forms & Evidence, Contract Values, and Readiness Check.` |
| Not configured here | `Payment certificates, actual progress, inspection records, evaluation marks, price amounts, and contract administration.` |

---

## 17. Validation behavior

This screen may show only local summary validation.

Allowed messages:

- `1 milestone missing acceptance description.`
- `Expected duration is missing for 2 milestones.`
- `Single delivery milestone is incomplete.`
- `Schedule complete.`

Do not show rule IDs, clause IDs, render-block diagnostics, hashes, or schema errors in the default UI.

Detailed findings belong in the readiness report.

---

## 18. Downstream impact

This screen feeds:

- **CFG-05 — System Inventory & Bidder Background** for sites, locations, existing environment, bidder context, and implementation assumptions that relate to delivery
- **CFG-06 — Price Schedule** for price items that correspond to supply, installation, training, support, recurrent services, or milestone-linked deliverables
- **CFG-08 — Forms & Evidence** for bidder methodology, implementation plan, delivery evidence, training evidence, and support evidence expectations
- **CFG-09 — Contract Values** for delivery obligations, implementation timelines, acceptance checkpoints, handover obligations, warranty/support start, and contract appendices
- **Readiness Check** for completeness and consistency
- **Tender Document Preview** for rendered Section VII content and related contract schedules

This screen must not configure:

- tender identity or procurement package context
- Tender Data Sheet values
- detailed technical requirement text
- system inventory rows or background materials
- commercial price lines, quantities, currency, tax treatment, or evaluated-price inclusion
- evaluation marks, pass marks, or formulas
- bidder form checklist rows
- SCC clause text
- review decisions
- publication actions
- post-award project execution records

---

## 19. API shape

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
  "delivery_approach": "Phased Delivery",
  "milestones": [
    {
      "milestone_id": "MS-001",
      "name": "Project Kick-off and Detailed Work Plan",
      "description": "Supplier prepares and submits the detailed implementation work plan for approval.",
      "sequence": 1,
      "expected_duration": "2 weeks",
      "start_trigger": "Contract signing and notice to proceed",
      "key_deliverable": "Approved implementation work plan",
      "acceptance_label": "Acceptance defined",
      "status_label": "Complete",
      "action_label": "Edit"
    },
    {
      "milestone_id": "MS-003",
      "name": "Installation and Configuration",
      "description": "Supplier installs and configures the supplied IT infrastructure.",
      "sequence": 3,
      "expected_duration": "4 weeks",
      "start_trigger": "Delivery acceptance for equipment",
      "key_deliverable": "Installed and configured infrastructure",
      "acceptance_label": "Missing acceptance",
      "status_label": "Needs attention",
      "action_label": "Fix"
    }
  ],
  "single_delivery": null
}
```

For single delivery:

```json
{
  "delivery_approach": "Single Turnkey Delivery",
  "milestones": [],
  "single_delivery": {
    "expected_delivery_duration": "6 months",
    "delivery_trigger": "Contract signing and notice to proceed",
    "key_deliverables": "Fully supplied, installed, configured, tested, documented, and handed-over IT solution",
    "acceptance_label": "Acceptance defined",
    "acceptance_description": "Procuring Entity confirms delivery, installation, testing, training, documentation, and operational readiness.",
    "evidence_expected": "Completion report, test results, training records, and handover certificate.",
    "status_label": "Complete"
  }
}
```

---

## 20. Stitch prompt

```text
Design CFG-04 — Implementation Schedule for KenTender Tender Configurations.

Screen purpose:
Define the delivery approach, milestones, deliverables, timing, and acceptance checkpoints for this IT tender.

User decision:
How should the successful bidder deliver, install, configure, test, train, hand over, and support the solution?

Header:
Title: Implementation Schedule
Subtitle: Define the delivery approach, milestones, deliverables, timing, and acceptance checkpoints for this IT tender.

Context strip fields:
- Procurement Package Ref
- Tender Title
- Procuring Entity
- Procurement Method
- STD Family
- Standard Tender Document
- Configuration Status
- Issues

Delivery approach selector:
- Phased Delivery
- Single Turnkey Delivery

If Phased Delivery is selected, show a milestones table with these exact columns:
- ID
- Milestone
- Expected Duration
- Trigger
- Key Deliverable
- Acceptance
- Status
- Actions

Use these phased-delivery sample rows:
1. MS-001 | Project Kick-off and Detailed Work Plan | 2 weeks | Contract signing and notice to proceed | Approved implementation work plan | Acceptance defined | Complete | Edit
2. MS-002 | Hardware Supply and Delivery | 8 weeks | Approved work plan | Delivered server and storage equipment | Acceptance defined | Complete | Edit
3. MS-003 | Installation and Configuration | 4 weeks | Delivery acceptance for equipment | Installed and configured infrastructure | Missing acceptance | Needs attention | Fix
4. MS-004 | Testing and Commissioning | 3 weeks | Installation completion | Test report and operational readiness confirmation | Acceptance defined | Complete | Edit
5. MS-005 | Training and Handover | 2 weeks | Commissioning acceptance | User training records and handover pack | Acceptance defined | Complete | Edit
6. MS-006 | Warranty and Support Start | Not time-bound | Final handover acceptance | Confirmed support commencement | Not applicable | Complete | Review

If Single Turnkey Delivery is selected, hide the milestones table and show one form titled Single Delivery Milestone with these exact fields:
- Expected Delivery Duration
- Delivery Trigger
- Key Deliverables
- Acceptance Expectation
- Acceptance Description
- Evidence Expected
- Notes to Bidders

Right guidance panel:
Title: Implementation Schedule Guidance
Text: Define how the successful bidder will deliver the solution. Keep this focused on planned milestones, deliverables, timing, and acceptance checkpoints. Actual delivery, inspection, payment, and contract administration happen after award.

Drawer sections for milestone add/edit:
1. Milestone
2. Deliverables
3. Acceptance
4. References

Primary buttons:
- Add Milestone
- Save Schedule
- Run Check
- Continue to System Inventory & Bidder Background

Do not show payment percentages, actual progress, inspection records, invoices, contract administration events, evaluation marks, price amounts, SCC clause editing, publication controls, hashes, rule IDs, binding IDs, schema versions, or internal object names.
```

---

## 21. Cursor prompt

```text
Implement CFG-04 — Implementation Schedule in the Tender Configurations module.

This screen defines planned delivery approach, milestones, deliverables, timing, and acceptance checkpoints. It is not a project execution screen, payment screen, inspection screen, contract administration screen, evaluation screen, or price schedule screen.

Route:
Tender Management → Tender Configurations → Tender Configuration Home → Implementation Schedule

Primary object:
ImplementationScheduleConfiguration

Screen owns:
- delivery approach
- milestone name
- milestone description
- milestone sequence
- expected duration
- start trigger
- key deliverable
- deliverable description
- related IT requirement references
- acceptance expectation
- acceptance description
- evidence expected
- notes to bidders

Screen does not own:
- Tender Profile values
- Tender Data Sheet values
- IT requirement text
- system inventory/background records
- price schedule rows
- evaluation marks or pass scores
- bidder submission checklist rows
- SCC values or contract clause text
- review decisions
- publication actions
- post-award delivery execution records
- inspection records
- payment certification

Data rules:
- Support delivery_approach values: Phased Delivery and Single Turnkey Delivery.
- If delivery_approach is Phased Delivery, render milestones table and Add Milestone action.
- If delivery_approach is Single Turnkey Delivery, hide milestones table and render Single Delivery Milestone form.
- Do not silently delete milestone data when switching delivery approaches.
- Preserve prior phased milestones in draft history if user switches to single delivery.
- Restore prior draft milestones if user switches back before submission for review.
- Expected Duration must be editable unless a real governance rule prevents editing.
- Template-prefilled values must show clear source behavior and must be editable with reset-to-suggestion support.
- Do not use Locked for template-prefilled durations, triggers, deliverables, or acceptance descriptions.

Required table columns for phased delivery:
- ID
- Milestone
- Expected Duration
- Trigger
- Key Deliverable
- Acceptance
- Status
- Actions

Status labels:
- Complete
- Needs attention
- In progress
- Not started

Do not use:
- Valid
- Ready
- Locked
- Executed
- In delivery
- Paid
- Certified

Primary buttons:
- Add Milestone
- Save Schedule
- Run Check
- Continue to System Inventory & Bidder Background

Acceptance criteria:
- User can understand whether the tender uses phased delivery or single turnkey delivery.
- Phased delivery shows milestone rows with duration, trigger, deliverable, acceptance, status, and action.
- Single turnkey delivery shows one simple delivery milestone form.
- Switching delivery approach requires confirmation and does not silently delete data.
- No payment, inspection, actual progress, evaluation, pricing, SCC, review, publication, hash, rule ID, schema version, binding ID, or internal system object appears in the default UI.
```

---

## 22. Acceptance checklist

| Test | Pass condition |
|---|---|
| User decision clarity | User can tell the screen is for deciding delivery approach and milestones. |
| STD grounding | Screen maps to Section VII — Implementation Schedule. |
| Ownership clarity | Screen owns delivery approach and planned milestone information only. |
| No magical values | Durations, triggers, and deliverables are editable or clearly source-labeled. |
| Phased delivery | Milestones table appears with exact approved columns. |
| Single delivery | Phase table is hidden and one single delivery milestone form is shown. |
| Switching behavior | Switching approach confirms the change and preserves prior draft data. |
| Downstream awareness | Screen references downstream use without configuring price, forms, contract, or evaluation details. |
| Simplicity | No project execution, payment, inspection, or contract administration content appears. |
| Prompt precision | Stitch and Cursor prompts contain exact labels, columns, sample rows, actions, and forbidden content. |

---

## 23. Final rule

If a field does not help the user define how the successful bidder will deliver the IT solution, remove it from CFG-04.
