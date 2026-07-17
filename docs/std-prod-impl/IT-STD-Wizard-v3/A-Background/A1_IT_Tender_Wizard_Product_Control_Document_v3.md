# IT Tender Wizard Product Control Document v3

**Project:** KenTender e-Procurement System  
**Module:** IT Tender Configuration Wizard  
**Status:** Mandatory control document  
**Supersedes:** All earlier IT Tender Wizard control packs and screen-numbering documents  
**Design rule:** Keep the user journey simple. Legal and technical complexity stays behind focused configuration tasks and workflow gates.

---

## 1. Purpose

This document controls all IT Tender Wizard PRDs, UX specs, Stitch prompts, Cursor prompts, API contracts, and implementation screens.

No screen may be documented or implemented unless it is classified in the Complete Screen Registry.

---

## 2. Authoritative User Journey

Use this journey everywhere:

```text
Approved Procurement Package
→ Create IT Tender Configuration
→ Configuration Home
→ Complete CFG-01 to CFG-09
→ Run Readiness Check
→ Submit for Review
→ Preview Tender Document
→ Mark Ready for Publication
→ Tender Management publication workflow
```

The handoff from Planning is an **Approved Procurement Package**. The user does not select a Tender Shell or Tender to Configure.

---

## 3. Surface Types

The wizard has three kinds of user-facing surfaces.

| Type | Meaning | Numbering rule |
|---|---|---|
| Application surface | Entry, creation, or navigation surface | `UI-*` or `UI-M*` |
| Configuration step | User enters or confirms tender-specific information | `CFG-01` to `CFG-09` only |
| Workflow gate/view | System check, reviewer workflow, preview, or handoff | `WF-*`; never numbered as configuration steps |

Do not mix these categories.

---

## 4. Complete Surface Registry

### 4.1 Application surfaces

| ID | User-facing name | Purpose | User decision |
|---|---|---|---|
| UI-00 | IT Tender Configurations Dashboard | Shows approved packages and existing IT tender configurations | Which package/configuration should I open or create? |
| UI-M01 | Create IT Tender Configuration | Creates a configuration from an approved procurement package | Which approved procurement package needs IT tender configuration? |
| UI-01 | Tender Configuration Home | Shows progress for one configuration | What should I work on next? |

### 4.2 Configuration steps

Only these are numbered configuration steps:

| ID | User-facing name | User decision | Main PPRA IT STD coverage |
|---|---|---|---|
| CFG-01 | Tender Profile | Is the basic tender identity and setup context correct? | Tender identity, cover/invitation context |
| CFG-02 | Tender Data Sheet | What tender-specific instructions and parameters apply? | Section II — Tender Data Sheet; permitted ITT parameterization |
| CFG-03 | IT Requirements | What must bidders supply, deliver, integrate, support, or prove? | Sections V and VI |
| CFG-04 | Implementation Schedule | How should the solution be delivered? | Section VII |
| CFG-05 | System Inventory & Bidder Background | What bidder-relevant inventory, site, system, and background context must be disclosed? | Sections VIII and IX |
| CFG-06 | Price Schedule | How should bidders price the tender? | Section IV price schedule forms; supply/install and recurrent cost pricing |
| CFG-07 | Evaluation Setup | How will bids be evaluated? | Section III |
| CFG-08 | Forms & Evidence | What must bidders submit? | Section IV non-price tendering forms, declarations, qualification forms, and evidence |
| CFG-09 | Contract Values | What tender-specific contract values and obligations apply? | SCC, contract forms, contract-facing appendices |

### 4.3 Workflow gates/views

These functions may have views, modals, or task pages, but they are not configuration steps.

| ID | User-facing name | Trigger | Purpose |
|---|---|---|---|
| WF-01 | Readiness Report | User runs Readiness Check | Shows blockers/warnings and links to owning configuration steps |
| WF-02 | Review Workspace | User submits for review | Captures reviewer decisions, return reasons, and approval |
| WF-03 | Tender Document Preview | Review is approved | Lets the user confirm the generated tender package |
| WF-04 | Publication Handoff | Preview is confirmed | Marks the package ready for Tender Management publication workflow |

Do not call these `CFG-10`, `CFG-11`, `CFG-12`, or `CFG-13`.

---

## 5. User-Facing Vocabulary

| Use this | Do not use this in default procurement UI |
|---|---|
| Approved Procurement Package | Tender Shell |
| IT Tender Configuration | TenderSTDInstance |
| Standard Tender Document | STD package code |
| Planning Package Ref | Plan Item Ref, Procurement Initiation Ref |
| Tender Profile | Tender shell metadata |
| Tender Data Sheet | TDS schema object |
| IT Requirements | Requirement schema rows |
| Implementation Schedule | Schedule model |
| System Inventory & Bidder Background | Inventory/background schema |
| Price Schedule | Commercial pricing model |
| Evaluation Setup | Evaluation schema |
| Forms & Evidence | Evidence checklist engine |
| Contract Values | SCC parameter object |
| Readiness Check | Rule engine diagnostics |
| Readiness Report | Validation screen |
| Tender Document Preview | Render output object |
| Publication Handoff | Publication readiness state |

Forbidden default UI terms:

```text
Tender Shell
TenderSTDInstance
STD binding
STD package code
STD version hash
schema version
rule ID
source anchor
configuration object
render block
clause hash
lifecycle enum
Ready
Locked
```

`Locked` may be used only where there is real legal/governance immutability, not as a step status.

---

## 6. Screen 02 Mandatory Structure

`UI-01 — Tender Configuration Home` must show two areas.

### Configuration Steps

1. Tender Profile  
2. Tender Data Sheet  
3. IT Requirements  
4. Implementation Schedule  
5. System Inventory & Bidder Background  
6. Price Schedule  
7. Evaluation Setup  
8. Forms & Evidence  
9. Contract Values  

### Completion & Handoff

- Readiness Check
- Review Status
- Tender Document Preview
- Publication Handoff

Completion & Handoff items are status/action summaries, not editable configuration cards.

---

## 7. Status Labels

Use only these step-level status labels on configuration steps:

| Status | Meaning | Typical action |
|---|---|---|
| Not started | No meaningful work has been done | Start |
| In progress | Work has started but required items remain | Continue |
| Needs attention | Blockers, returned corrections, or important warnings require action | Fix |
| Complete | Required local setup is complete | Review |
| Not available yet | A prior required step is incomplete | View required step |

Do not use `Ready` or `Locked` on step cards.

---

## 8. Action Labels

Allowed main action labels:

```text
Create IT Tender Configuration
Create Configuration
Start
Continue
Fix
Review
Run Readiness Check
View Readiness Report
Submit for Review
Open Tender Document Preview
Confirm Preview
Mark Ready for Publication
Open in Tender Management
```

Do not use:

```text
Finalize Configuration
Start Configuration
Publish Tender
Tender Shell
Bind STD
Create Tender Shell
```

---

## 9. Create Configuration Modal

### Modal title

```text
Create IT Tender Configuration
```

### Helper text

```text
Select the approved procurement package that requires an IT tender configuration. The planning reference, procuring entity, procurement method, and applicable standard tender document will be filled from the package.
```

### Fields

| Field | Behavior |
|---|---|
| Approved Procurement Package | User selects this |
| Planning Package Ref | Read-only after package selection |
| Procuring Entity | Read-only after package selection |
| Procurement Method | Read-only after package selection |
| Standard Tender Document | Read-only unless more than one active IT STD is valid and the user is permitted to choose |

### Buttons

```text
Cancel
Create Configuration
```

Do not show internal object names such as Tender Shell, TenderSTDInstance, binding ID, schema version, or package code.

---

## 10. Ownership Matrix

| Surface | Owns | Feeds downstream | Must not contain |
|---|---|---|---|
| UI-00 Dashboard | Work queue and creation entry | Create Configuration modal, Configuration Home | Detailed configuration fields |
| UI-M01 Create IT Tender Configuration | Package selection and configuration creation | Tender Profile, Configuration Home | Tender Shell, STD binding, hashes |
| UI-01 Configuration Home | Step progress and next action | All configuration steps and workflow gates | Configuration forms or detailed findings |
| CFG-01 Tender Profile | Basic identity and setup context | TDS, generated tender cover/context, handoff | Technical requirements, pricing, scoring, contract values |
| CFG-02 Tender Data Sheet | Tender-specific instructions and parameters | Evaluation Setup, Forms & Evidence, Contract Values, Readiness Check | Technical specifications, price rows, review decisions |
| CFG-03 IT Requirements | Requirement statements, bidder response expectations, evidence expectations, acceptance expectations | Implementation Schedule, Price Schedule, Evaluation Setup, Forms & Evidence, Contract Values, Preview | Scores, price lines, actual bid evaluation, contract administration |
| CFG-04 Implementation Schedule | Delivery approach, milestones, durations, deliverables, acceptance checkpoints | System Inventory & Bidder Background, Price Schedule, Contract Values, Preview | Project execution, inspections, payment certification |
| CFG-05 System Inventory & Bidder Background | Bidder-relevant environment, inventory, sites, systems, and background context | Price Schedule, Preview, requirement references | Full pricing setup, scoring, hidden obligations in background |
| CFG-06 Price Schedule | Pricing structure, quantities, units, pricing instructions | Evaluation Setup, bidder price schema, Preview | Technical requirement wording, inventory editing, scoring |
| CFG-07 Evaluation Setup | Evaluation stages, criteria, weights, pass rules, financial evaluation basis | Forms & Evidence, Readiness Check, Preview | Actual bid evaluation, award recommendation |
| CFG-08 Forms & Evidence | Bidder submission requirements and non-price forms | Bidder submission schema, Readiness Check, Preview | Actual bidder uploads, evidence verification, scoring |
| CFG-09 Contract Values | SCC values and contract-facing obligations | Preview, publication package, downstream contract preparation | Post-award contract administration, change orders, inspections |
| WF-01 Readiness Report | Findings summary and links to owning steps | Review submission | Editing configuration fields |
| WF-02 Review Workspace | Review decisions and return comments | Tender Document Preview | Configuration editing, publication |
| WF-03 Tender Document Preview | Read-only preview confirmation | Publication Handoff | Editing or fixing content |
| WF-04 Publication Handoff | Publication-ready handoff confirmation | Tender Management publication workflow | Publishing the tender |

---

## 11. PPRA IT STD Coverage Rule

The simplified wizard must still cover the full IT STD.

| IT STD area | Wizard treatment |
|---|---|
| Tender identity / cover / invitation context | CFG-01 Tender Profile; publication details handed to Tender Management where applicable |
| Section I — Instructions to Tenderers | Locked STD text rendered by STD Engine; configured only through permitted CFG-02 TDS values |
| Section II — Tender Data Sheet | CFG-02 Tender Data Sheet |
| Section III — Evaluation and Qualification Criteria | CFG-07 Evaluation Setup |
| Section IV — Tendering Forms | CFG-08 Forms & Evidence, except price schedule forms |
| Section IV — Price Schedule Forms | CFG-06 Price Schedule |
| Section V — Requirements of the Information System | CFG-03 IT Requirements |
| Section VI — Technical Requirements | CFG-03 IT Requirements |
| Section VII — Implementation Schedule | CFG-04 Implementation Schedule |
| Section VIII — System Inventory Tables | CFG-05 System Inventory & Bidder Background |
| Section IX — Background and Informational Materials | CFG-05 System Inventory & Bidder Background |
| General Conditions of Contract | Locked STD text rendered by STD Engine; configured only through permitted CFG-09 Contract Values |
| Special Conditions of Contract | CFG-09 Contract Values |
| Contract Forms and appendices | CFG-09 Contract Values and downstream generated package outputs |
| Securities, beneficial ownership, declarations, qualification evidence | CFG-08 Forms & Evidence or CFG-09 Contract Values depending on tender/submission vs contract stage |
| Change-order forms and post-award administration forms | Downstream contract administration output, not an IT Tender Configuration screen |

---

## 12. Non-Negotiable Documentation Rule

Every future screen spec must include this control block:

```text
Canonical ID:
User-facing name:
Surface type:
Lifecycle position:
Primary user decision:
Owns:
Feeds downstream:
Does not own:
PPRA IT STD anchor:
Entry condition:
Exit condition:
Allowed statuses:
Allowed actions:
Forbidden UI terms/content:
```

If any line is vague, the screen spec fails.

---

## 13. Final Control Statement

The wizard has:

- 3 application surfaces;
- 9 configuration steps;
- 4 workflow gate/views.

Only `CFG-01` to `CFG-09` are configuration steps. Workflow gates are still required functions, but they must not be presented as numbered configuration steps.
