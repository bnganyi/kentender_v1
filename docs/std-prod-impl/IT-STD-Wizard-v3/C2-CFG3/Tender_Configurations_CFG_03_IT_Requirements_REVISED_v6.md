# CFG-03 — IT Requirements v6

**Product:** KenTender  
**Area:** Tender Management → Tender Configurations  
**Surface type:** Configuration step  
**Configuration step:** CFG-03  
**Screen name:** IT Requirements  
**STD family:** Information Technology  
**Status:** Revised v6 specification  

---

## 1. Purpose

Define the IT requirements that bidders must respond to for this tender.

This screen helps the procurement user answer one question:

> What must bidders supply, deliver, integrate, support, or prove?

---

## 2. User-facing entry path

The user reaches this screen from:

`Tender Management → Tender Configurations → Tender Configuration Home → IT Requirements`

This screen is available after **CFG-02 — Tender Data Sheet** has enough required values to confirm the tender context, submission rules, participation rules, and any method-driven constraints.

---

## 3. STD grounding

This screen maps primarily to:

- **Section V — Requirements of the Information System**
- **Section VI — Technical Requirements**

It defines bidder-facing IT requirements. It must not configure evaluation marks, price lines, bidder submission forms, contract clauses, or implementation milestones.

---

## 4. Screen ownership

| Area | Rule |
|---|---|
| Owns | IT requirement items and bidder response expectations |
| Does not own | Tender identity, TDS values, implementation phases, inventory/background records, price schedule rows, evaluation marks, bidder form checklist, SCC values, review decisions, publication actions |
| Reads from | Approved Procurement Package, Tender Profile, Tender Data Sheet, selected IT Standard Tender Document |
| Feeds | Implementation Schedule, System Inventory & Bidder Background, Price Schedule, Evaluation Setup, Forms & Evidence, Contract Values, Readiness Check, Tender Document Preview |

---

## 5. Page header

**Title:**

`IT Requirements`

**Subtitle:**

`Define what bidders must supply, deliver, integrate, support, or prove.`

**Primary actions:**

- `Add Requirement`
- `Save Requirements`
- `Run Check`
- `Continue to Implementation Schedule`

**Secondary action:**

- `Back to Configuration Home`

Do not use:

- `Evaluation Matrix`
- `Scoring Requirements`
- `Compliance Results`
- `Supplier Responses`
- `Contract Obligations Editor`

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
| Issues | `2 Blockers / 1 Warning` |

Do not show hashes, rule IDs, binding IDs, schema versions, or internal object names.

---

## 7. Main layout

Use a requirements table with an optional right-side guidance panel and a row detail drawer.

Default view:

1. Page header and actions
2. Tender context strip
3. Requirements table
4. Requirements guidance panel
5. Footer action bar
6. Row drawer opened only when adding or editing a requirement

Do not show a permanent middle editor. Do not show full evaluation, pricing, forms, or contract configuration on this screen.

---

## 8. Requirements table

Use these exact columns:

| Column | Purpose |
|---|---|
| ID | Requirement reference, for example `REQ-001` |
| Requirement | Clear bidder-facing requirement title |
| Category | Requirement category |
| Treatment | Whether the requirement is mandatory, evaluation-linked, or informational |
| Bidder Response | How the bidder must respond |
| Evidence | What proof the bidder must provide |
| Acceptance | How delivery will later be confirmed |
| Status | Local completeness status |
| Actions | `Edit`, `Fix`, or `Review` |

Do not use `Type`; use `Treatment`.

Do not use `Valid`; use `Complete`.

Do not use `Scored`, `Evidence Set`, or `Acceptance Set`.

---

## 9. Approved requirement categories

Use only these category labels in the default UI:

- `Business Objective`
- `Functional Requirement`
- `Technical Requirement`
- `Security & Compliance`
- `Integration`
- `Implementation Support`
- `Support & Warranty`
- `Deliverable / Acceptance`
- `Background / Informational`

---

## 10. Treatment labels

Use only:

| Treatment | Meaning |
|---|---|
| Mandatory | Bidder must satisfy the requirement. |
| Evaluation-linked | Requirement will be considered in Evaluation Setup. No marks are shown here. |
| Informational | Context only; no direct bidder response is required unless specified. |

Do not show score percentages, pass marks, or evaluation formulas on this screen.

---

## 11. Bidder Response

**Bidder Response** means how the bidder is expected to answer the requirement in their tender submission.

It is not the bidder's actual response and it is not evaluation scoring.

Allowed labels:

- `Yes/No confirmation`
- `Compliance statement`
- `Numeric value`
- `Narrative response`
- `Completed table`
- `Not required`

---

## 12. Evidence

**Evidence** means the proof or supporting material expected from the bidder.

Allowed labels:

- `Evidence required`
- `Evidence optional`
- `No evidence required`
- `Missing evidence instruction`

Evidence item setup for the final submission checklist belongs in **CFG-08 — Forms & Evidence**. This screen only states the evidence expectation attached to the requirement.

---

## 13. Acceptance

**Acceptance** means how the procuring entity will confirm that the requirement has been delivered or satisfied after award.

Allowed labels:

- `Acceptance defined`
- `Missing acceptance`
- `Not applicable`

Do not create inspection records, acceptance certificates, or contract administration records on this screen.

---

## 14. Status labels

Use only:

| Status | Meaning |
|---|---|
| Complete | Requirement has enough text, bidder response instruction, evidence expectation, and acceptance expectation for its treatment. |
| Needs attention | Required requirement information is missing or inconsistent. |
| In progress | Requirement has been started but is not complete. |
| Not started | Placeholder requirement exists but has no meaningful content. |

Do not use:

- `Valid`
- `Ready`
- `Locked`
- `Scored`
- raw rule IDs
- clause IDs as default labels

---

## 15. Sample table rows

Use these sample rows in Stitch/Cursor fixtures unless a better approved seed fixture is supplied:

| ID | Requirement | Category | Treatment | Bidder Response | Evidence | Acceptance | Status | Action |
|---|---|---|---|---|---|---|---|---|
| REQ-001 | Compute Node Performance | Technical Requirement | Evaluation-linked | Numeric value and compliance statement | Manufacturer datasheet required | Acceptance defined | Complete | Edit |
| REQ-002 | Redundant Power Supply Units | Technical Requirement | Mandatory | Yes/No confirmation | Datasheet required | Missing acceptance | Needs attention | Fix |
| REQ-003 | Three-Year On-site Support | Support & Warranty | Mandatory | Narrative response | Support authorization letter required | Acceptance defined | Complete | Edit |
| REQ-004 | Data Migration Approach | Implementation Support | Evaluation-linked | Narrative response | Project methodology required | Acceptance defined | Complete | Edit |
| REQ-005 | User Training | Support & Warranty | Mandatory | Completed training plan table | Training sample material optional | Acceptance defined | Complete | Edit |
| REQ-006 | Integration with Existing Finance System | Integration | Mandatory | Compliance statement | Integration experience evidence required | Missing evidence instruction | Needs attention | Fix |
| REQ-007 | Data Residency | Security & Compliance | Mandatory | Yes/No confirmation and compliance statement | Compliance certificate required | Acceptance defined | Complete | Edit |
| REQ-008 | Existing System Context | Background / Informational | Informational | Not required | No evidence required | Not applicable | Complete | Review |

---

## 16. Add/Edit requirement drawer

The drawer must use this exact structure.

### 16.1 Requirement

| Field label | Type | Rule |
|---|---|---|
| Requirement Title | Text | Required |
| Requirement Description | Text area | Required unless informational context is deliberately brief |
| Category | Select | Required; use approved category labels |
| Treatment | Select | Required; Mandatory, Evaluation-linked, or Informational |

### 16.2 Bidder Response

| Field label | Type | Rule |
|---|---|---|
| Bidder Response Format | Select | Required unless Treatment is Informational |
| Bidder Response Instruction | Text area | Required unless response format is Not required |

Allowed response formats:

- `Yes/No confirmation`
- `Compliance statement`
- `Numeric value`
- `Narrative response`
- `Completed table`
- `Not required`

### 16.3 Evidence

| Field label | Type | Rule |
|---|---|---|
| Evidence Requirement | Select | Required |
| Evidence Instruction | Text area | Required if evidence is required or optional |

Allowed evidence requirement values:

- `Evidence required`
- `Evidence optional`
- `No evidence required`

### 16.4 Acceptance

| Field label | Type | Rule |
|---|---|---|
| Acceptance Expectation | Select | Required unless Treatment is Informational |
| Acceptance Description | Text area | Required if acceptance is defined |

Allowed acceptance expectation values:

- `Acceptance defined`
- `Not applicable`

### 16.5 References

Show only compact references:

| Label | Allowed text |
|---|---|
| Evaluation Setup | `Linked in Evaluation Setup` / `Not linked to evaluation` |
| Forms & Evidence | `Evidence item will be configured in Forms & Evidence` / `No evidence item required` |
| Contract Values | `May carry into contract values` / `No contract carry-forward expected` |

Do not use the drawer to configure scoring, form checklist rows, price lines, contract clauses, or implementation phases.

---

## 17. Right guidance panel

Panel title:

`IT Requirements Guidance`

Panel text:

`Focus on what bidders must supply, deliver, integrate, support, or prove. Evaluation scores, price lines, submission checklist items, and contract values are configured in later steps.`

Show compact guidance rows:

| Label | Text |
|---|---|
| What this affects | `Bidder responses, evidence expectations, evaluation setup, forms, contract values, and tender preview.` |
| Used later by | `Implementation Schedule, System Inventory & Bidder Background, Price Schedule, Evaluation Setup, Forms & Evidence, and Contract Values.` |
| Not configured here | `Scores, prices, actual bidder submissions, contract clauses, delivery execution, and publication actions.` |

---

## 18. Downstream impact

This screen feeds:

- **CFG-04 — Implementation Schedule** for delivery phases, milestones, and acceptance planning
- **CFG-05 — System Inventory & Bidder Background** for inventory/context items linked to requirements
- **CFG-06 — Price Schedule** for price items that correspond to required supply, installation, support, or recurrent services
- **CFG-07 — Evaluation Setup** for criteria linked to evaluation-linked requirements
- **CFG-08 — Forms & Evidence** for bidder evidence and submission expectations
- **CFG-09 — Contract Values** for requirements that carry into contract obligations
- **Readiness Check** for completeness and consistency
- **Tender Document Preview** for rendered Requirements and Technical Requirements sections

This screen must not configure:

- evaluation marks, weights, pass marks, or formulas
- price quantities, currency, tax treatment, or evaluated-price inclusion
- implementation phase sequencing or duration
- system inventory tables or background materials
- formal bidder submission checklist rows
- SCC values or contract clause text
- review decisions
- publication actions

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
  "blocker_count": 2,
  "warning_count": 1,
  "requirements": [
    {
      "requirement_id": "REQ-001",
      "title": "Compute Node Performance",
      "description": "Bidder must propose compute nodes that meet the stated processor, memory, storage, and redundancy requirements.",
      "category_label": "Technical Requirement",
      "treatment_label": "Evaluation-linked",
      "bidder_response_label": "Numeric value and compliance statement",
      "evidence_label": "Manufacturer datasheet required",
      "acceptance_label": "Acceptance defined",
      "status_label": "Complete",
      "action_label": "Edit"
    },
    {
      "requirement_id": "REQ-002",
      "title": "Redundant Power Supply Units",
      "description": "Bidder must provide redundant hot-swappable power supply units for proposed server equipment.",
      "category_label": "Technical Requirement",
      "treatment_label": "Mandatory",
      "bidder_response_label": "Yes/No confirmation",
      "evidence_label": "Datasheet required",
      "acceptance_label": "Missing acceptance",
      "status_label": "Needs attention",
      "action_label": "Fix"
    }
  ]
}
```

---

## 20. Stitch prompt

```text
Design CFG-03 — IT Requirements for KenTender Tender Configurations.

Screen purpose:
Define what bidders must supply, deliver, integrate, support, or prove.

User decision:
What must bidders supply, deliver, integrate, support, or prove?

Header:
Title: IT Requirements
Subtitle: Define what bidders must supply, deliver, integrate, support, or prove.

Context strip fields:
- Procurement Package Ref
- Tender Title
- Procuring Entity
- Procurement Method
- STD Family
- Standard Tender Document
- Configuration Status
- Issues

Main table columns, exactly:
- ID
- Requirement
- Category
- Treatment
- Bidder Response
- Evidence
- Acceptance
- Status
- Actions

Use these table row examples:
1. REQ-001 | Compute Node Performance | Technical Requirement | Evaluation-linked | Numeric value and compliance statement | Manufacturer datasheet required | Acceptance defined | Complete | Edit
2. REQ-002 | Redundant Power Supply Units | Technical Requirement | Mandatory | Yes/No confirmation | Datasheet required | Missing acceptance | Needs attention | Fix
3. REQ-003 | Three-Year On-site Support | Support & Warranty | Mandatory | Narrative response | Support authorization letter required | Acceptance defined | Complete | Edit
4. REQ-004 | Data Migration Approach | Implementation Support | Evaluation-linked | Narrative response | Project methodology required | Acceptance defined | Complete | Edit
5. REQ-005 | User Training | Support & Warranty | Mandatory | Completed training plan table | Training sample material optional | Acceptance defined | Complete | Edit
6. REQ-006 | Integration with Existing Finance System | Integration | Mandatory | Compliance statement | Integration experience evidence required | Missing evidence instruction | Needs attention | Fix
7. REQ-007 | Data Residency | Security & Compliance | Mandatory | Yes/No confirmation and compliance statement | Compliance certificate required | Acceptance defined | Complete | Edit
8. REQ-008 | Existing System Context | Background / Informational | Informational | Not required | No evidence required | Not applicable | Complete | Review

Right guidance panel:
Title: IT Requirements Guidance
Text: Focus on what bidders must supply, deliver, integrate, support, or prove. Evaluation scores, price lines, submission checklist items, and contract values are configured in later steps.

Drawer sections:
1. Requirement
2. Bidder Response
3. Evidence
4. Acceptance
5. References

Primary buttons:
- Add Requirement
- Save Requirements
- Run Check
- Continue to Implementation Schedule

Do not show evaluation marks, scoring percentages, price lines, supplier submissions, implementation phases, contract clause editing, SCC values, approval workflow, publication controls, hashes, rule IDs, binding IDs, schema versions, or internal object names.
```

---

## 21. Cursor prompt

```text
Implement CFG-03 — IT Requirements in the Tender Configurations module.

This screen defines bidder-facing IT requirements. It is not an evaluation screen, price schedule, submission checklist, contract editor, or project execution screen.

Route:
Tender Management → Tender Configurations → Tender Configuration Home → IT Requirements

Primary object:
ITRequirementConfiguration

Screen owns:
- requirement title
- requirement description
- requirement category
- requirement treatment
- bidder response format
- bidder response instruction
- evidence expectation
- evidence instruction
- acceptance expectation
- acceptance description

Screen does not own:
- Tender Profile values
- Tender Data Sheet values
- implementation phases
- system inventory/background records
- price schedule rows
- evaluation marks or pass scores
- bidder submission checklist rows
- SCC/contract values
- review decisions
- publication actions

Render:
1. Page header with title "IT Requirements".
2. Subtitle exactly: "Define what bidders must supply, deliver, integrate, support, or prove."
3. Context strip with Procurement Package Ref, Tender Title, Procuring Entity, Procurement Method, STD Family, Standard Tender Document, Configuration Status, Issues.
4. Requirements table with exact columns:
   - ID
   - Requirement
   - Category
   - Treatment
   - Bidder Response
   - Evidence
   - Acceptance
   - Status
   - Actions
5. Right guidance panel using the exact text in the specification.
6. Row drawer with sections:
   - Requirement
   - Bidder Response
   - Evidence
   - Acceptance
   - References
7. Footer actions:
   - Save Requirements
   - Run Check
   - Continue to Implementation Schedule

Validation:
- Status labels may only be Complete, In progress, Needs attention, or Not started.
- Continue to Implementation Schedule is disabled if required requirement blockers remain.
- Do not show raw rule IDs, clause IDs, hashes, or schema details in the default UI.

Implementation constraints:
- Do not use Tailwind CDN in production.
- Use local KenTender UI styles/components.
- Do not hardcode realistic data except approved seed fixtures.
- Do not show internal terms such as shell, instance, binding, package code, schema version, rule hash, or source anchor.
```

---

## 22. Acceptance checklist

| Check | Pass condition |
|---|---|
| User decision clarity | User understands they are defining what bidders must supply, deliver, integrate, support, or prove. |
| STD grounding | Screen maps to Section V and Section VI of the IT STD. |
| Ownership clarity | Screen owns only IT requirement content and bidder response expectations. |
| Table completeness | Table includes Requirement, Treatment, Bidder Response, Evidence, and Acceptance. |
| No scoring leakage | No marks, percentages, pass marks, or evaluation formulas appear. |
| No pricing leakage | No price rows, quantities, currency, taxes, or evaluated-price settings appear. |
| No contract leakage | Only compact contract references appear; no SCC or contract clause editing. |
| Downstream awareness | Screen explicitly feeds schedule, inventory/background, price, evaluation, forms, contract values, readiness, and preview. |
| Status discipline | Only Complete, In progress, Needs attention, and Not started are used. |
| Implementation readiness | Stitch and Cursor prompts contain exact labels, descriptions, table rows, drawer sections, actions, and exclusions. |

---

## 23. Final rule

If a field does not help the procurement user define what bidders must supply, deliver, integrate, support, or prove, remove it from CFG-03.
