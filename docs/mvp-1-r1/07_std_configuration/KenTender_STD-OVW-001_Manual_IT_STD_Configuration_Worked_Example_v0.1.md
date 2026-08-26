# STD-OVW-001 — Manual IT STD Configuration: Worked Example

| Control | Value |
|---|---|
| Document ID | STD-OVW-001 |
| Version | 0.1 |
| Date | 24 August 2026 |
| Status | Illustrative overview |
| Example procurement | National Digital Health Infrastructure Upgrade |
| STD family | Procurement of Information Technology |

## 1. The idea in one view

```text
Official PPRA IT STD
        │
        │ Human interpretation and controlled configuration — once per STD version
        ▼
Manually curated IT STD package
  ├─ locked standard text
  ├─ allowed tender parameters
  ├─ structured requirement schema
  ├─ price, evaluation and form schemas
  ├─ contract parameters
  └─ validation, rendering and downstream mappings
        │
        ├──────── generates the Requisition Requirements Composer
        │
        └──────── generates the Tender Configuration Wizard
                           │
                           ▼
                 One configured IT tender
                  ├─ rendered tender document
                  ├─ bidder response workspace
                  ├─ evaluation workspace
                  └─ contract obligations
```

The official PDF is read by people when configuring and reviewing the package. KenTender does not parse it at runtime, infer rules from it or regenerate the package from it.

## 2. Step A — Configure the IT STD once

An authorised STD Configurator creates package **KE-PPRA-IT · Version 1**. A separate STD Reviewer checks it against the official PPRA IT STD and activates it.

### 2.1 What is stored as locked content

| IT STD area | Manual treatment |
|---|---|
| Instructions to Tenderers | Entered once as locked render blocks. Tender users cannot edit it. |
| General Conditions of Contract | Entered once as locked render blocks. Tender users cannot edit it. |
| Standard declarations and form wording | Entered once as locked form definitions and text. |
| Standard tender and contract clauses | Entered once, ordered and versioned. |

Static text is not decomposed into hundreds of fields. It becomes structured only where KenTender must collect a value, apply a rule or use the result downstream.

### 2.2 What is configured as schemas

| Package component | Example configuration | Runtime consumer |
|---|---|---|
| Tender Data Sheet parameters | Submission deadline; tender validity; clarification deadline; tender security rule | Tender Configuration Wizard and rendered TDS |
| Requirement categories | Functional; architecture; performance; security; integration; data; training; support; testing and acceptance | Requisition Requirements Composer |
| Bidder response definitions | Compliance choice; explanation; proposed value; required evidence | Supplier response workspace |
| Implementation schedule schema | Milestone; deliverable; duration; dependency; acceptance checkpoint | Requisition and tender schedule screens |
| Price schedule schema | One-time supply; implementation services; training; recurrent support | Tender price setup and supplier pricing workspace |
| Evaluation schema | Preliminary checks; technical pass/fail or scored criteria; financial evaluation basis | Tender configuration and evaluation workspace |
| Forms and evidence schema | Tender form; confidential business questionnaire; beneficial ownership; qualification evidence | Supplier response workspace |
| Contract parameter schema | Performance security; payment milestones; warranty; support period | Tender configuration and contract formation |
| Render map | Which locked block and configured value appears in each STD section | Preview and final tender document |

The package contains no Ministry of Health requirement, date, budget or supplier response. It is a reusable definition of what an IT tender may collect and produce.

## 3. Step B — Capture the requirement in the Requisition

The Digital Health department starts a Requisition from its Active Plan Item. Planning supplies the title, method, approved value, schedule, Strategic Objective and funding lineage.

Because the procurement uses the IT requirement profile, KenTender opens the IT Requirements Composer generated from **KE-PPRA-IT · Version 1**.

### 3.1 Example requirement rows

| ID | Category | Supplier obligation | Bidder response | Evidence required | Acceptance condition |
|---|---|---|---|---|---|
| FUN-001 | Functional | The solution shall maintain one longitudinal patient record for each registered patient. | Comply / Does not comply plus explanation | Demonstration during acceptance testing | A user retrieves the same patient record from two authorised facilities. |
| INT-001 | Integration | The solution shall exchange patient and encounter data through the Ministry interoperability interface. | Comply / Does not comply plus interface approach | Proposed integration design | A test encounter is transmitted and acknowledged without manual re-entry. |
| SEC-001 | Security | The solution shall enforce multi-factor authentication for privileged users. | Comply / Does not comply plus proposed method | Product security documentation | A privileged login is rejected when the second factor is absent. |
| SUP-001 | Support | The supplier shall restore a critical production service within four hours of confirmed incident notification. | Confirm plus service approach | Draft support procedure | A simulated critical incident meets the four-hour restoration requirement. |

Every column has a current effect:

- category controls grouping and rendering;
- supplier obligation becomes tender and contract content;
- bidder response defines the supplier portal field;
- evidence defines what the bidder must submit or demonstrate; and
- acceptance condition feeds evaluation or later contract acceptance.

There is no generic note, source reference, optional narrative or duplicate PDF specification.

### 3.2 Example implementation schedule

| Milestone | Required deliverable | Latest completion | Acceptance checkpoint |
|---|---|---|---|
| Design confirmation | Approved solution and integration design | 30 days after contract start | Ministry approval of the design baseline |
| Pilot deployment | Working pilot in two facilities | 90 days after contract start | Pilot acceptance tests passed |
| National rollout | Production deployment to the agreed facilities | 240 days after contract start | Rollout acceptance tests passed |
| Knowledge transfer | Administrator and user training completed | 250 days after contract start | Training attendance and competency checks accepted |

### 3.3 Requisition approval and handoff

The HoD and Head of Procurement Function review the actual structured requirements and schedule on screen. On authorisation, KenTender freezes **Requirement Package Version 1** and hands these machine-readable records to Tender Preparation.

Only inherently external artefacts may accompany the package—for example an existing network diagram. No supplier obligation may exist only in that file.

## 4. Step C — Configure this Tender

Tender Preparation creates the Tender from the authorised Requisition and binds it to the same active IT STD package.

The wizard does not ask the Procurement Officer to type the requirements again.

| Wizard area | Source or user action in this example |
|---|---|
| Tender identity | Generated from the Tender shell and inherited Plan/Requisition context |
| IT requirements | Inherited read-only from Requirement Package Version 1 |
| Implementation schedule | Inherited from the Requisition; tender-permitted completion details added only where required |
| Tender Data Sheet | Procurement Officer enters the permitted tender-specific dates and values |
| Price schedule | Procurement Officer activates the package's implementation and recurrent-support structures and adds the exact priced lines derived from the scope |
| Evaluation setup | Procurement Officer maps approved requirements to the package-permitted evaluation treatment and completes qualification criteria |
| Forms and evidence | System activates standard forms; Procurement selects only package-permitted conditional evidence |
| Contract values | Procurement enters the permitted Special Conditions values that are not inherited or derived |

### 4.1 Example price structure

| Price section | Bidder must price |
|---|---|
| Software and infrastructure | Required platform components and licences |
| Implementation services | Configuration, integration, migration and rollout |
| Training | Administrator and user training |
| Recurrent support | Annual support for each required year |

The bidder enters prices into generated system tables. No bidder uploads an Excel price schedule as the authoritative bid.

### 4.2 Example requirement-to-evaluation mapping

| Requirement | Tender treatment | Evaluation effect |
|---|---|---|
| FUN-001 | Mandatory | Non-compliance fails the applicable technical check. |
| INT-001 | Evaluated technical response | Evaluators assess the response against the configured integration criterion. |
| SEC-001 | Mandatory | Required response and evidence must be present and compliant. |
| SUP-001 | Contract obligation | The accepted response is carried into the support obligations. |

Tender Preparation owns this evaluation treatment. The user department defines the operational requirement and acceptance condition; it does not assign scores in the Requisition.

## 5. Step D — Generate four consistent outputs

One approved Tender configuration produces:

### 5.1 Tender document

The renderer combines:

- locked IT STD text;
- Tender Data Sheet values;
- inherited structured requirements and schedule;
- configured price structures;
- evaluation and qualification criteria;
- activated forms; and
- Special Conditions values.

The PDF is a generated presentation of authoritative system data, not the data source.

### 5.2 Supplier response workspace

For `INT-001`, the bidder sees:

- the exact obligation;
- **Comply** or **Does not comply**;
- an **Integration approach** response field; and
- the exact requested design evidence control.

The supplier does not upload one undifferentiated technical proposal in place of these responses.

### 5.3 Evaluation workspace

Evaluators see the same requirement, bidder response, evidence and configured evaluation rule together. They do not reconstruct criteria from a PDF or spreadsheet.

### 5.4 Contract formation

The winning accepted obligations, implementation milestones, support requirement and acceptance conditions are carried into the contract dataset. Contract staff do not retype them from the tender document.

## 6. What changes when PPRA revises the IT STD

1. The active package remains unchanged for existing tenders.
2. An STD Configurator creates **KE-PPRA-IT · Version 2** manually.
3. Only changed locked blocks, parameters, rules, schemas or mappings are amended.
4. A separate reviewer compares Version 2 with the new official STD and the previous package.
5. Automated package consistency and rendering tests run.
6. Version 2 is activated for new Tenders; existing Tenders remain bound to Version 1.

There is no PDF extraction or automatic legal interpretation step.

## 7. Practical build boundary

The first implementation need only prove this vertical path:

```text
Manually curated IT STD package
→ IT Requirements Composer
→ authorised structured Requisition package
→ IT Tender Configuration Wizard
→ generated bidder response schema
→ evaluation view
→ contract-obligation handoff
```

After this path is stable, Goods, Works, Non-consulting and Consulting packages can be added manually using the same runtime contracts.
