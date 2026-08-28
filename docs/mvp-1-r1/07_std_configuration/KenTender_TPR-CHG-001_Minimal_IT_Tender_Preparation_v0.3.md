# TPR-CHG-001 — Minimal IT Tender Preparation

| Control | Value |
|---|---|
| Document ID | TPR-CHG-001 |
| Version | 0.3 |
| Date | 28 August 2026 |
| Status | Proposed for approval and human walkthrough |
| First product pattern | `IT-EQUIPMENT-OPEN-V1` — PPRA Goods STD for straightforward IT equipment |
| Starts from | One authorised Procurement Requisition |
| Ends at | One approved, immutable publication handoff |
| Implementation authority | None |

## 1. Decision

MVP-1 Tender Preparation will begin with one small product: preparing a straightforward IT-equipment tender from one authorised Requisition.

The Procurement Officer will complete five tasks:

1. Tender details;
2. Goods and delivery;
3. Price schedule;
4. Submission and evaluation; and
5. Contract terms.

KenTender will then validate the Tender, generate one complete preview, route it to the Head of Procurement Function and create an immutable publication handoff after approval.

There is no STD Configuration module. Users cannot edit standard clauses, create fields, define schemas, configure mappings or design a Wizard. The supported template is part of a controlled software release.

### 1.1 Version 0.3 correction

Version 0.3 replaces the incomplete control guidance in v0.2. It now defines, for every value on the five tasks:

- the control type;
- source and editability;
- allowed values and default;
- required and conditional behaviour;
- validation; and
- supplier, Tender and contract use.

It also corrects the prototype price screen: unit prices, taxes and totals are supplier responses and are not entered during Tender Preparation.

## 2. Scope

### 2.1 Included

This version supports a Tender only when all of the following are true:

- the source is one unconsumed authorised Requisition;
- the requirement is straightforward IT equipment or goods;
- the approved procurement method is supported by the released template;
- the Tender has one award package and one currency;
- technical requirements are supplied through the authorised technical document;
- evaluation is pass/fail followed by financial evaluation; and
- no complex implementation, system integration, data migration, construction or professional-services model is required.

### 2.2 Not included

This version does not support:

- combining several Requisitions;
- lotting or multiple award packages;
- ERP, platform implementation or other complex IT-system tenders;
- WORKS, consulting services or non-consulting services;
- weighted technical scoring;
- alternative procurement methods not released with this template;
- editing official standard text;
- a generic specification composer;
- an STD package, manifest or mapping interface;
- bidder submission, evaluation, award or contract management; or
- publication itself.

An unsuitable Requisition must be stopped with a clear explanation. The officer must not be allowed to force it through this pattern.

## 3. Simple end-to-end journey

```text
Authorised Requisition
        ↓
Create Tender and bind released IT-equipment template
        ↓
Procurement Officer completes five tasks
        ↓
Readiness check and complete preview
        ↓
Head of Procurement Function returns or approves
        ↓
Immutable publication handoff
```

The Requisition remains unchanged throughout. Tender Preparation may copy inherited facts into its immutable snapshot, but it may not edit the authorised Requisition.

## 4. Responsibility boundary

| Responsibility | Owner |
|---|---|
| Quantity, authorised value, expected delivery and technical document | Authorised Requisition |
| Tender method and Planning lineage | Authorised Requisition, read-only |
| Supported template and locked standard text | Controlled KenTender software release |
| Tender dates, security, goods schedule, delivery treatment, evidence choices and contract values | Procurement Officer |
| Technical clarification | Requesting department or competent technical officer, outside a new KenTender workflow |
| Completeness and consistency checks | KenTender |
| Tender approval or return | Head of Procurement Function |
| Publication | Downstream publication process |

The Procurement Officer may ask the department for clarification. KenTender does not create contributor assignments, technical-review queues or a second Requisition workflow.

If clarification changes the authorised scope, quantity, value or expected delivery date, the Tender cannot proceed. It must use the Requisition return, revocation or replacement route.

## 5. Roles and access

Use ordinary Frappe Roles and User Permissions.

| Actor | Allowed actions |
|---|---|
| Procurement Officer | Start a Tender from an eligible handoff; edit a Draft; run readiness; submit for approval; view returned and approved Versions |
| Head of Procurement Function | Review the submitted Version and complete preview; return with one correction; approve for publication; reopen before publication handoff is consumed |
| Requesting department viewer | Read the inherited Requisition and neutral Tender status where already authorised; no Tender edit or decision |
| Internal Auditor | Read Tender Versions, decisions and publication evidence within native scope |
| System Manager | Technical administration only; no Tender business decision by virtue of the role |

The Procurement Officer who prepared a Tender cannot approve that Tender. No other Tender Preparation role is introduced.

## 6. The installed Tender template

### 6.1 Exact first template

The first template is:

| Property | Value |
|---|---|
| Template key | `IT-EQUIPMENT-OPEN-V1` |
| Display name | IT Equipment — Open Tender |
| KenTender template version | 1.0 |
| Official source | **PPRA Standard Tender Document for Procurement of Goods** |
| Intended use | Straightforward off-the-shelf IT equipment and related delivery services |
| Procurement method | Open Tender |
| Evaluation model | Pass/fail responsiveness and technical compliance, followed by financial evaluation |
| Award package | One |
| Currency | One Tender currency |

This pattern uses the Goods STD, not the Information Technology STD. The latter is reserved for a later complex-system pattern covering software, implementation, integration, migration and support.

The release evidence must record the exact PPRA source file used, any issue or revision date printed in it, retrieval date, source URL and SHA-256 digest. The source title alone is not enough to release the template.

### 6.2 What the code-owned bundle contains

`IT-EQUIPMENT-OPEN-V1` is a version-controlled bundle shipped with KenTender. It contains only these parts:

| Bundle part | Content |
|---|---|
| Metadata | Template key/version, official-source record, supported method/category, availability and bundle digest |
| Locked text | The applicable official standard sections and form wording that operational users cannot edit |
| Officer model | The five tasks, fields, choices and fixed tables in section 8 |
| Supplier package | Official forms, goods/price schedules and the response/evidence controls required by this pattern |
| Rules | Applicability, required fields, date checks, quantity checks, security checks, readiness and immutability |
| Renderer | Assembly order and placement of inherited facts, officer answers, schedules, forms and technical documents |
| Coverage register | Every official source section marked as locked text, generated content, officer input, supplier response, governed attachment or deliberately inapplicable |
| Fixture and tests | The KEBS-style fixture, exact expected output and focused validation/rendering tests |

The bundle may use ordinary typed Python plus version-controlled YAML, JSON and rendering files. It is not a user-authored runtime schema. Business rules that affect authority, readiness, calculations or state remain typed server-side code.

The bundle must generate one coherent publication package containing:

1. Invitation and Tender identity;
2. Instructions to Tenderers;
3. Tender Data Sheet;
4. Evaluation and Qualification Criteria;
5. Tendering Forms;
6. Goods, delivery and price schedules;
7. the authorised technical specification;
8. General and Special Conditions of Contract; and
9. Contract Forms.

Large standard sections remain locked text. Only values used by the five officer tasks, supplier response, evaluation or contract are structured.

### 6.3 How it is installed

Installation is part of a controlled KenTender software release:

1. The reviewed bundle is committed with the application code.
2. Automated tests verify its source record, coverage, fields, rules and rendered fixture.
3. An idempotent install/migration step validates the bundle digest.
4. The step creates or updates one read-only **Supported Tender Template** registry row.
5. The row becomes **Available for new Tenders** only when the installed bundle and recorded digest match.
6. Tender Preparation resolves the bundle by `template_key + template_version`; the registry row does not become an editable copy of the template.

The installed registry row contains:

| Field | Value for the first release |
|---|---|
| `template_key` | `IT-EQUIPMENT-OPEN-V1` |
| `template_version` | `1.0` |
| `display_name` | IT Equipment — Open Tender |
| `official_source_title` | PPRA Standard Tender Document for Procurement of Goods |
| `official_source_file_digest` | Exact digest recorded during release preparation |
| `supported_category` | Goods — IT equipment |
| `supported_method` | Open Tender |
| `availability_status` | Available for new Tenders |
| `bundle_digest` | Digest of the complete installed template bundle |

If the bundle is missing, invalid or does not match either digest, the template is unavailable and the deployment fails its release check. The system must not fall back to a partial template.

There is no Configurator role, configuration Draft, reviewer queue, activation screen or template-editing permission. System Manager cannot change the installed template through Desk.

### 6.4 How Tender Preparation uses it

For the first release, compatibility has only two results:

- one compatible template: show `IT-EQUIPMENT-OPEN-V1` for confirmation and create the Tender; or
- no compatible template: stop and explain that the Requisition is unsupported.

There is no multi-template comparison or structural choice. When the Tender is created, KenTender copies the template key, version, official-source digest and bundle digest into the immutable Tender binding. All five screens, rules and rendered sections then come from that exact installed release.

### 6.5 Reuse of earlier IT work

Earlier IT work is an input to preparing the bundle, not a runtime dependency.

| Earlier work | Treatment in `IT-EQUIPMENT-OPEN-V1` |
|---|---|
| Tender Data Sheet fields, labels and help text | Reuse after checking each item against the Goods STD |
| Goods, delivery and price schedules | Reuse or simplify where they match sections 8.2 and 8.3 |
| Forms, declarations, securities and contract values | Reuse after official-source and coverage review |
| Rendering layout and successful Wizard interactions | Reuse where they support the five-task journey |
| IT system requirements, implementation phases, integrations, migration, system inventory and service levels | Exclude from this template; reserve for the later complex-IT pattern |
| Parser, OCR and inferred-schema code | Retire from the production path |
| Generic manifests, package activation and schema editors | Do not reuse |
| Unverified extracted or previously configured content | Do not release until independently checked against the official source |

The reuse exercise produces one simple source-to-bundle checklist. It does not create a permanent transformation service or compatibility layer.

### 6.6 Template correction and later versions

An installed template is never edited in place.

- A correction or official-source revision creates a new code-owned bundle and template version.
- The new release repeats source, coverage, render and test review.
- The new registry row becomes available through deployment.
- The preceding row may become **Historical only** for new Tenders.
- Existing Tenders retain their original template and digests.

Operational users do not migrate, upgrade or rebind an existing Tender.

## 7. Tender data

Tender Preparation uses one root record, versioned snapshots and fixed child tables. It does not use a generic manifest.

### 7.1 Tender root

| Field | Purpose |
|---|---|
| Tender ID and reference | Stable generated identity |
| Source Requisition handoff | Proves the authorised starting point |
| PE/FY and Plan Item | Fixes scope and lineage |
| Template key, version and digest | Fixes the released Tender pattern |
| Current state and Version | Supports the lifecycle |
| Approved Version | Identifies the exact approved snapshot |
| Publication-handoff reference | Shows whether the approved package has been handed off |
| Record version | Prevents stale writes |

### 7.2 Tender Version

A Draft Version contains the five task values and child rows. Submission locks it. Return preserves the reviewed Version and creates a copied Draft successor.

### 7.3 Fixed child tables

Only these repeatable tables are required:

- Goods and delivery schedule;
- Related services, where used;
- Tender-specific evidence requirements; and
- Price schedule derived from the goods and related-services rows.

The authorised technical specification remains a governed Requisition file. The first pattern does not decompose every specification into database fields.

### 7.4 Decisions and publication package

Each submit, return, approve and pre-publication reopen action records the actor, time, Version, resulting state and required reason where applicable.

Approval creates one immutable package containing:

- the approved Tender Version;
- the bound template identity and digest;
- the complete rendered Tender;
- the structured goods, price and evidence schedules;
- the authorised technical-document references;
- the readiness result;
- the approval decision; and
- a package digest.

## 8. Five officer tasks and control contract

### 8.0 Rules for every control

The control type, source and editability are part of the product contract. An implementation may not replace a defined control with a generic text field.

| Value class | Required presentation |
|---|---|
| Inherited from the Requisition | Read-only value with source label **From authorised Requisition** |
| Fixed by the template release | Read-only value with source label **Fixed by IT Equipment template v1.0** |
| Generated by KenTender | Read-only value with source label **Generated by KenTender** |
| Officer decision with two choices | Yes/No radio group or switch; never text |
| Officer decision with finite choices | Select or radio group containing only the listed values |
| Governed reference | Frappe Link or autocomplete restricted to active records in the stated reference list |
| Date or time | Date or datetime picker; datetime values use `Africa/Nairobi` |
| Number, quantity, percentage or money | Numeric control with the stated unit, precision and limits |
| Genuine tender-specific wording | Constrained text with the stated maximum length; no HTML or Markdown |
| Supplier response | Read-only placeholder **Completed by Tenderer**; never an officer input |

Common rules:

- Required fields display **Required** before submission.
- Conditional fields remain hidden until their controlling answer makes them applicable.
- Read-only values are not styled as enabled text boxes.
- A disabled control is used only to show a fixed choice; inherited and calculated values use ordinary read-only display.
- The server enforces the same type, options, source, visibility and validation as the screen.
- Unknown values, user-created options and free-text substitutes are rejected.
- Help text states why the value is needed, not its database source or key.

### 8.1 Task 1 — Tender details

#### Read-only context

| Field | Control | Source | Value or rule |
|---|---|---|---|
| Procuring Entity | Read-only Link display | Requisition | Exact authorised PE |
| Plan Item | Read-only Link display | Requisition | Exact approved Plan Item |
| Requisition | Read-only Link display | Requisition | Exact authorised Requisition |
| Requirement type | Read-only text | Requisition | `Goods — IT equipment` |
| Procurement method | Read-only text | Requisition | `Open Tender` |
| Authorised quantity | Read-only quantity | Requisition | Used for reconciliation; not editable |
| Authorised value | Read-only currency | Requisition | Internal control value; not rendered publicly unless required |
| Expected delivery | Read-only date | Requisition | Latest permitted delivery date |
| Technical specification | Protected file card | Requisition | View/download only; show title, version, approval date and status |
| Template | Read-only text | Template | `IT Equipment — Open Tender · Version 1.0` |
| Tender reference | Read-only text | Generated | Generated once |
| Opening date and time | Read-only datetime | Generated | Same as submission deadline for this release |

#### Officer controls

| Field | Control | Allowed value/default | Required and validation |
|---|---|---|---|
| Tender title | Single-line text, maximum 160 characters | Default: Requisition requirement title | Required; trimmed; no markup; must differ from an empty or generic title |
| Issue date | Date picker | No free-text date | Required; not later than clarification or submission deadline |
| Clarification deadline | Datetime picker | `Africa/Nairobi` | Required; after issue date and before submission deadline |
| Submission deadline | Datetime picker | `Africa/Nairobi` | Required; after clarification deadline |
| Tender validity | Integer with suffix **days** | 1–365; default 120 | Required |
| Tender security treatment | Read-only choice | `Tender Security` | Fixed by Version 1.0; Tender-Securing Declaration and Not required are not offered |
| Tender security currency | Read-only currency | `KES` | Fixed by Version 1.0 |
| Tender security amount | Currency amount, 2 decimal places | Positive KES amount | Required and greater than zero |
| Pre-tender meeting | Yes/No switch | Default No | Required |
| Meeting date and time | Datetime picker | Visible only when meeting is Yes | Required when visible; after issue date and before submission deadline |
| Meeting mode | Radio group | `Physical`, `Online` | Required when meeting is Yes |
| Meeting venue | Governed PE Location Link | Active PE location only | Required for Physical meeting |
| Online joining information | Single-line text, maximum 240 characters | No markup | Required for Online meeting |

### 8.2 Task 2 — Goods and delivery

The authorised technical specification is shown first as a protected file. It is never replaced by an editable specification form.

#### Goods table

| Column | Control | Allowed value/source | Required and validation |
|---|---|---|---|
| Item number | Read-only integer | Generated row order | Always |
| Goods description | Single-line text, maximum 200 characters | Tender-specific plain description | Required; no brand/model unless the technical specification contains approved `or equivalent` treatment or justification |
| Quantity | Positive decimal, up to 3 decimal places | Officer value | Required; sum must equal authorised Requisition quantity |
| Unit | Governed UOM Link | Active UOM values only | Required |
| Delivery location | Governed PE Location Link | Active location for the Tender PE | Required |
| Latest delivery date | Date picker | Officer value | Required; not later than authorised expected delivery date |
| Minimum warranty | Positive integer with suffix **months** | 1–120 | Required |

Rows are added and removed only while the Version is Draft. Empty rows cannot be saved.

#### Related services

The section is shown only when the Requisition says related services are authorised.

| Column | Control | Allowed value/source | Required and validation |
|---|---|---|---|
| Description | Single-line text, maximum 240 characters | Plain description within the approved technical document | Required |
| Place of performance | Governed PE Location Link | Active PE location only | Required |
| Completion date | Date picker | Officer value | Required; not later than authorised expected delivery date |
| Quantity | Positive decimal, up to 3 decimal places | Officer value | Required |
| Unit | Governed UOM Link | Active UOM values only | Required |

### 8.3 Task 3 — Price schedule

Task 3 defines the blank schedule that suppliers will complete. It does not contain estimated, budget or illustrative prices.

#### Tender controls

| Field | Control | Allowed value | Editability |
|---|---|---|---|
| Price currency | Read-only currency | `KES` | Fixed by Version 1.0 |
| Prices fixed for contract period | Read-only choice | `Yes` | Fixed by Version 1.0 |
| Taxes shown separately | Read-only choice | `Yes` | Fixed by Version 1.0 |

#### Generated schedule

| Column | Source and presentation |
|---|---|
| Item, description, quantity and unit | Read-only; generated from Task 2 |
| Unit price | Read-only placeholder **Completed by Tenderer** |
| Line total | Read-only placeholder **Calculated from Tenderer response** |
| Tax | Read-only placeholder **Completed or calculated from Tenderer response** |
| Tender total | Read-only placeholder **Calculated from Tenderer response** |

The Procurement Officer cannot enter unit prices, taxes, line totals or Tender totals. The authorised value is not copied into the supplier price schedule.

### 8.4 Task 4 — Submission and evaluation

The evaluation sequence is fixed and read-only:

1. submission and eligibility check;
2. pass/fail technical compliance against the published specification;
3. arithmetic and financial evaluation; and
4. award to the lowest evaluated responsive Tender.

| Field | Control | Allowed value/default | Required and validation |
|---|---|---|---|
| Manufacturer authorisation required | Yes/No switch | Default Yes | Required; Yes adds the fixed Manufacturer Authorisation evidence row |
| Product datasheets or brochures required | Yes/No switch | Default Yes | Required; Yes adds the fixed product-literature evidence row |
| Warranty confirmation required | Read-only choice | `Yes — always required` | Fixed by the template |
| Past supply experience required | Yes/No switch | Default No | Required |
| Minimum comparable contracts | Select | `1`, `2`, `3` | Required only when past experience is Yes |
| Experience period | Select with suffix **years** | `3`, `5` | Required only when past experience is Yes |
| After-sales support evidence required | Yes/No switch | Default No | Required |
| After-sales evidence | Select | `Kenya service-centre details and escalation contacts`; `Manufacturer or authorised service-partner commitment`; `Both` | Required only when after-sales evidence is Yes |

Additional evidence is permitted only as a constrained row:

| Column | Control | Allowed value/source | Required and validation |
|---|---|---|---|
| Evidence label | Single-line text, maximum 160 characters | Plain description | Required |
| Evidence type | Select | `Declaration`, `Certificate`, `Datasheet or brochure`, `Schedule or form`, `Other document` | Required |
| Published requirement | Link/select | One visible Task 2 item or approved technical-specification section | Required |
| Mandatory | Yes/No switch | Default Yes | Required |

An additional evidence row cannot create a hidden evaluation criterion. Its linked requirement and label appear in the published Tender.

### 8.5 Task 5 — Contract terms

| Field | Control | Allowed value/source | Editability and validation |
|---|---|---|---|
| Delivery period | Read-only summary | Generated from Task 2 | Not editable |
| Inspection and acceptance location | Governed PE Location Link | Active PE location only | Required officer selection |
| Warranty period | Read-only item summary | Generated from Task 2 | Not editable |
| Payment timing | Select with suffix **days** | `30`, `45`, `60`; default 30 | Required; renders with the fixed delivery, inspection, acceptance and valid-invoice wording |
| Performance security required | Yes/No switch | Default Yes | Required |
| Performance security percentage | Decimal percentage | 1–10; default 10 | Required only when performance security is Yes |
| Delay damages per week | Decimal percentage | 0.1–1.0; default 0.5 | Required |
| Maximum delay damages | Integer percentage | 5–10; default 10 | Required; not less than weekly rate |
| Contract contact office | Governed PE Office Link | Active office for the Tender PE | Required; personal-user selection is not allowed |

The General Conditions remain locked. No field permits clause editing.

## 9. Readiness

Readiness is a check, not a workflow state. A Draft may be incomplete; submission may not.

A Tender is ready only when:

- the source Requisition remains authorised and unconsumed by another Tender;
- the bound template remains valid for the Tender;
- every required field is complete;
- clarification, meeting and submission dates are in the correct order;
- no unresolved tender-decision placeholder remains;
- goods quantities equal the authorised Requisition quantity;
- delivery dates do not exceed the authorised expected delivery date;
- the price schedule exactly matches the goods and related-services rows;
- security values are complete and consistent wherever security is required;
- every evidence row points to a visible Tender requirement;
- the technical specification is present and publishable;
- any brand or model reference has approved `or equivalent` treatment or is returned for correction;
- contract values are internally consistent; and
- the complete preview renders without missing sections or duplicate values.

Findings are either **Blocking** or **Warning**. Only Blocking findings prevent submission. Warnings remain visible to the approver and require no user-dismissal mechanism.

## 10. Lifecycle

| Current state | Action | Actor | Result |
|---|---|---|---|
| Ready Requisition handoff | Prepare Tender | Procurement Officer | Creates one Draft and consumes the handoff idempotently |
| Draft | Save | Procurement Officer | Saves incomplete or complete Draft; no decision task |
| Draft | Submit for approval | Procurement Officer | Requires zero Blocking findings; locks the Version and creates one approval task |
| Submitted for approval | Return for correction | Head of Procurement Function | Preserves the submitted Version and creates a copied Draft successor with one required correction |
| Submitted for approval | Approve for publication | Head of Procurement Function | Atomically creates the immutable approved Version, publication package and one ready publication handoff |
| Approved for publication | Reopen before publication | Head of Procurement Function | Allowed only while the publication handoff is unconsumed; requires a reason and creates a Draft successor |

No approved or handed-off Version is edited in place. Once the publication handoff is consumed, correction belongs to the later publication/addendum process.

## 11. Commands

| Command | Minimum effect |
|---|---|
| `PrepareTender` | Rechecks the handoff, confirms the single compatible template, creates or returns the same Draft idempotently, and binds the template version/digest |
| `SaveTenderDraft` | Validates only the fields supplied for the fixed five-task model and checks the expected record version |
| `RunTenderReadiness` | Validates the current Draft and stores the result against the exact Version digest |
| `SubmitTenderForApproval` | Re-runs readiness, locks the Version and creates one Head of Procurement Function task |
| `ReturnTenderForCorrection` | Requires one actionable correction and creates a copied Draft successor |
| `ApproveTenderForPublication` | Rechecks authority, segregation, readiness and the complete render; creates approval, publication package and ready handoff atomically |
| `ReopenApprovedTender` | Requires an unconsumed publication handoff and reason; preserves the approved Version and creates a Draft successor |

Every write uses an expected record version and idempotency key. The server derives state, actors, template binding, totals, digests and publication data.

## 12. Screens

All screens use the existing Frappe Desk shell, global context control and KenTender components. There is no separate STD workspace.

### 12.1 Screen registry

| ID | Screen | Primary actor |
|---|---|---|
| TPR-DES-01 | Tender Preparation workspace | Procurement Officer |
| TPR-DES-02 | Start IT-equipment Tender | Procurement Officer |
| TPR-DES-03 | Five-task Tender workspace | Procurement Officer |
| TPR-DES-04 | Review and readiness | Procurement Officer |
| TPR-DES-05 | Tender approval | Head of Procurement Function |
| TPR-DES-06 | Approved Tender | Procurement Officer and approver |
| TPR-DES-M01 | Return for correction | Head of Procurement Function |
| TPR-DES-M02 | Reopen before publication | Head of Procurement Function |
| TPR-DES-S01 | Empty, unsupported and error states | Applicable actor |

### 12.2 Shared fixture

The fixture is a product test, not a transcription of the KEBS source Tender.

| Item | Exact value |
|---|---|
| Procuring Entity | `PE-KEBS` — Kenya Bureau of Standards |
| Financial Year | `FY-2026-2027` |
| Department | `OU-KEBS-ICT` — Information and Communication Technology |
| Plan Item | `PPI-KEBS-2026-014` — Supply and delivery of ICT equipment |
| Requisition | `REQ-KEBS-2026-ICT-0001` · Authorised |
| Authorised quantity/value | 50 each · KES 18,000,000 |
| Expected delivery | 30 December 2026 |
| Technical document | ICT Equipment Technical Specifications v1.0.pdf |
| Tender | `TND-KEBS-2026-0001` |
| Template | `IT-EQUIPMENT-OPEN-V1` · Version 1.0 |
| Procurement Officer | Alice Wambui · `alice.wambui@kebs.example.test` |
| Head of Procurement Function | Samuel Otieno · `samuel.otieno@kebs.example.test` |

### 12.3 TPR-DES-01 — Tender Preparation workspace

Title: **Tender Preparation**  
Description: **Prepare Tenders from authorised Procurement Requisitions.**

Tabs: **Ready to prepare** and **My Tenders**.

**Ready to prepare** shows one row:

| Requisition | Requirement | Method | Quantity | Value | Expected delivery | Action |
|---|---|---|---:|---:|---|---|
| REQ-KEBS-2026-ICT-0001 | Supply and delivery of ICT equipment | Open Tender | 50 each | KES 18,000,000 | 30 Dec 2026 | Prepare Tender |

No dashboard cards, charts, STD library link or second creation action.

### 12.4 TPR-DES-02 — Start IT-equipment Tender

Dialog title: **Prepare IT-equipment Tender**.

Show read-only:

- Requisition: **REQ-KEBS-2026-ICT-0001**;
- Requirement: **Supply and delivery of ICT equipment**;
- Template: **IT Equipment — Open Tender · Version 1.0**; and
- Source: **PPRA Standard Tender Document for Procurement of Goods**.

Notice: **This template is fixed for this Tender. A later template release will not change it.**

Buttons: **Cancel** and **Prepare Tender**.

Do not show another template, a schema, package, manifest, mapping or configuration option.

### 12.5 TPR-DES-03 — Five-task Tender workspace

Header:

- Eyebrow: **TENDER PREPARATION**;
- Title: **Supply and delivery of ICT equipment**;
- Reference: **TND-KEBS-2026-0001 · REQ-KEBS-2026-ICT-0001**; and
- Status: **Draft**.

Left navigation:

| Task | Fixture state |
|---|---|
| 1. Tender details | Complete |
| 2. Goods and delivery | Complete · 3 items |
| 3. Price schedule | Complete · Generated from 3 items |
| 4. Submission and evaluation | Complete |
| 5. Contract terms | Complete |
| Review and readiness | Ready · 0 Blocking · 1 Warning |

The selected task uses the exact controls from section 8. Shared footer: **Save draft** and the applicable **Continue** action. The last task uses **Review Tender**.

The visual language is fixed:

| Presentation | Meaning |
|---|---|
| Plain value with source caption | Read-only inherited, fixed or generated value |
| Select with chevron | Closed set of permitted choices |
| Yes/No switch or radio group | Boolean officer decision |
| Calendar or clock indicator | Date or datetime picker |
| Numeric field with visible suffix | Constrained quantity, days, months or percentage |
| Protected file card | Approved Requisition document; view/download only |
| **Completed by Tenderer** | Supplier-response value; never editable by Procurement Officer |

An editable control must not be represented by an unlabelled text box. A read-only value must not look editable.

Exact Tender-details values:

| Field | Exact value |
|---|---|
| Tender title | Supply and delivery of business ICT equipment |
| Issue date | 8 Oct 2026 |
| Clarification deadline | 19 Oct 2026, 17:00 EAT |
| Submission deadline | 29 Oct 2026, 11:00 EAT |
| Tender validity | 120 days |
| Tender security | KES 300,000 |
| Pre-tender meeting | No |

Exact goods rows:

| Item | Description | Quantity | Unit | Delivery location | Latest delivery | Warranty |
|---|---|---:|---|---|---|---:|
| 1 | Business laptops | 25 | Each | KEBS Coast Region Office, Mombasa | 30 Dec 2026 | 36 months |
| 2 | Business desktop computers with monitors | 15 | Each | KEBS Coast Region Office, Mombasa | 30 Dec 2026 | 36 months |
| 3 | Business tablets | 10 | Each | KEBS Coast Region Office, Mombasa | 30 Dec 2026 | 24 months |

Exact price-schedule values are read-only: **KES**, **Prices fixed: Yes**, and **Taxes shown separately: Yes**. The three supplier price rows are generated from the goods rows above. Unit price, tax, line total and Tender total show **Completed by Tenderer** or **Calculated from Tenderer response**; they contain no fixture prices.

Task 4 fixture controls:

- Manufacturer authorisation required: **Yes** switch;
- Product datasheets or brochures required: **Yes** switch;
- Warranty confirmation required: read-only **Yes — always required**;
- Past supply experience required: **Yes** switch;
- Minimum comparable contracts: select **2**;
- Experience period: select **5 years**;
- After-sales support evidence required: **Yes** switch; and
- After-sales evidence: select **Kenya service-centre details and escalation contacts**.

Task 5 fixture controls:

- Delivery period: read-only Task 2 summary;
- Inspection and acceptance location: governed selection **KEBS Coast Region Office, Mombasa**;
- Warranty period: read-only item summary;
- Payment timing: select **30 days**;
- Performance security required: **Yes** switch;
- Performance security percentage: numeric **10%**;
- Delay damages: numeric **0.5% per week**, maximum **10%**; and
- Contract contact office: governed selection **KEBS Contracts Office**.

### 12.6 TPR-DES-04 — Review and readiness

Title: **Review Tender**.  
Description: **Resolve Blocking findings and review the complete Tender before submission.**

Summary:

| Check | Result |
|---|---|
| Source Requisition | Complete |
| Tender details | Complete |
| Goods and delivery | Complete · 50 each |
| Price schedule | Complete · 3 generated rows |
| Submission and evaluation | Complete |
| Contract terms | Complete |
| Rendered Tender | Complete |

Show **0 Blocking** and **1 Warning**.

Warning: **Confirm that the manufacturer-authorisation requirement is proportionate for every listed item.**

Actions: **Preview complete Tender** and **Submit for approval**.

### 12.7 TPR-DES-05 — Tender approval

Header status: **Submitted for approval**.

Show:

- the inherited Requisition summary;
- the complete five-task summary;
- the readiness result;
- the full rendered Tender preview; and
- the exact template version and source reference in a quiet release-information panel.

The page contains no editable Tender fields.

Actions: **Return for correction** and **Approve for publication**.

### 12.8 TPR-DES-06 — Approved Tender

Header status: **Approved for publication**.

Green notice: **This Tender is approved. The publication package is ready.**

Show:

- Tender reference and approved Version;
- approved by and time;
- template version;
- package digest;
- complete Tender preview;
- technical-document list; and
- publication-handoff status.

There is no edit action. **Reopen before publication** is available only to the Head of Procurement Function while the handoff is unconsumed.

### 12.9 Dialogs and common states

**Return for correction**

- Required field: **Correction required**;
- exact fixture: **Confirm whether manufacturer authorisation is necessary for the tablet item and update the evidence requirement.**;
- buttons: **Cancel** and **Return Tender**.

**Reopen before publication**

- Required field: **Reason for reopening**;
- exact fixture: **The submission deadline must be corrected before publication.**;
- buttons: **Cancel** and **Reopen Tender**.

| State | Message | Action |
|---|---|---|
| No ready Requisitions | No authorised Requisitions are ready for Tender Preparation. | None |
| Unsupported requirement | This Requisition is not supported by the IT-equipment Tender pattern. | Return to workspace |
| Handoff already consumed | This Requisition is already linked to a Tender. | View Tender |
| Requisition changed or revoked | The source Requisition is no longer available for Tender Preparation. | Return to workspace |
| Template unavailable | This Tender template is not available for new Tenders. | Return to workspace |
| Stale write | Another user changed this Tender. Reload before continuing. | Reload |
| Load failure | Tender Preparation could not be loaded. | Try again |

## 13. Deterministic lifecycle fixture

| Event | Actor | Exact time and result |
|---|---|---|
| Requisition handoff consumed and Draft created | Alice Wambui | 5 Oct 2026, 09:00 EAT · Draft Version 1 |
| Five tasks completed | Alice Wambui | 5 Oct 2026, 11:30 EAT |
| Readiness run | Alice Wambui | 5 Oct 2026, 11:35 EAT · 0 Blocking · 1 Warning |
| Submitted for approval | Alice Wambui | 5 Oct 2026, 11:40 EAT |
| Returned for correction | Samuel Otieno | 5 Oct 2026, 14:00 EAT · Draft Version 2 created |
| Corrected and resubmitted | Alice Wambui | 6 Oct 2026, 09:15 EAT |
| Approved for publication | Samuel Otieno | 6 Oct 2026, 10:00 EAT |
| Publication handoff created | System | 6 Oct 2026, 10:00 EAT · Ready |

Seeds and retries must not duplicate a Tender, Version, task, decision, render or publication handoff.

## 14. Acceptance contract

| ID | Required result |
|---|---|
| TPR-AC-001 | Only an authorised, unconsumed and compatible Requisition can create a Tender. |
| TPR-AC-002 | Preparing twice from the same handoff returns the same Tender and creates no duplicate. |
| TPR-AC-003 | One Tender consumes one Requisition; no grouping or lotting control exists. |
| TPR-AC-004 | The Tender binds one immutable template version and digest. |
| TPR-AC-005 | No screen permits standard-text, schema, mapping, step or validation configuration. |
| TPR-AC-006 | Officer input is limited to the fields and fixed tables in section 8. |
| TPR-AC-007 | The authorised technical specification remains immutable and is included in the publication package. |
| TPR-AC-008 | Goods quantity must equal the authorised Requisition quantity. |
| TPR-AC-009 | A later delivery date or material scope/value change is blocked and requires the upstream route. |
| TPR-AC-010 | The price schedule is generated from the goods and related-services rows without duplicate quantity entry. |
| TPR-AC-011 | The first pattern contains no weighted scoring or arbitrary criterion builder. |
| TPR-AC-012 | Submission requires zero Blocking findings and a complete render. |
| TPR-AC-013 | The preparing Procurement Officer cannot approve the same Tender. |
| TPR-AC-014 | Return preserves the reviewed Version and creates a copied Draft successor. |
| TPR-AC-015 | Approval creates the decision, approved Version, rendered package and handoff atomically. |
| TPR-AC-016 | A later template release does not change an existing Tender or render. |
| TPR-AC-017 | Approved and handed-off Versions cannot be edited in place. |
| TPR-AC-018 | Cross-PE/FY access and direct routes fail without disclosing the Tender. |
| TPR-AC-019 | Complex IT and WORKS Requisitions are rejected as unsupported rather than forced through this pattern. |
| TPR-AC-020 | The fixture reproduces the same fields, rows, readiness results and digests on every clean run. |
| TPR-AC-021 | The installed bundle identifies the exact PPRA Goods STD source file, source digest, bundle digest and complete coverage register. |
| TPR-AC-022 | A clean install creates exactly one read-only `IT-EQUIPMENT-OPEN-V1` registry row; a second install creates no duplicate or semantic change. |
| TPR-AC-023 | A missing bundle, invalid coverage register or digest mismatch prevents the template from becoming available. |
| TPR-AC-024 | No Desk screen, API or ordinary administrator action can edit the installed template content, rules or digests. |
| TPR-AC-025 | Every section of the official source has an explicit treatment and appears in the expected complete render or approved supporting package. |
| TPR-AC-026 | Every value shown on the five tasks uses the control, source, editability, allowed values and validation stated in section 8. |
| TPR-AC-027 | Inherited, fixed and generated values are visibly read-only and cannot be changed through UI or API payloads. |
| TPR-AC-028 | Boolean and finite-choice decisions reject free text and unknown values. |
| TPR-AC-029 | Conditional fields are hidden and not accepted until their controlling decision makes them applicable. |
| TPR-AC-030 | Currency, UOM, PE Location and PE Office values come only from their stated fixed or governed source. |
| TPR-AC-031 | Task 3 contains no officer-entered, fixture or estimated unit price, tax, line total or Tender total. |
| TPR-AC-032 | Supplier-response values are marked for the Tenderer and remain blank in Tender Preparation. |
| TPR-AC-033 | An additional evidence row is rejected unless it links to a visible published requirement. |
| TPR-AC-034 | Read-only and editable controls remain visually distinguishable in Draft, review and approval screens. |

## 15. Smoke contract

| Smoke | Proof |
|---|---|
| TPR-SMOKE-01 | Consume the authorised KEBS fixture handoff and create one bound Draft. |
| TPR-SMOKE-02 | Complete the five tasks and generate the three-row price schedule. |
| TPR-SMOKE-03 | Make goods quantity 51; readiness blocks submission and commits no approval task. |
| TPR-SMOKE-04 | Set delivery after 30 Dec 2026; readiness blocks and points to the upstream requirement. |
| TPR-SMOKE-05 | Return the submitted Version; verify it is unchanged and Draft Version 2 is created. |
| TPR-SMOKE-06 | Attempt self-approval as Alice Wambui; deny it. Approve as Samuel Otieno. |
| TPR-SMOKE-07 | Verify approval creates one immutable render and publication handoff; retry creates no duplicate. |
| TPR-SMOKE-08 | Release template Version 1.1; verify the existing Tender remains on Version 1.0. |
| TPR-SMOKE-09 | Present the NSSF ERP Requisition; show unsupported complex-IT result and create nothing. |
| TPR-SMOKE-10 | Present the Adole Footbridge WORKS Requisition; show unsupported WORKS result and create nothing. |
| TPR-SMOKE-11 | Install the released bundle twice; verify one identical Supported Tender Template row and one resolvable bundle. |
| TPR-SMOKE-12 | Alter the installed bundle after its digest is recorded; verify the release check fails and no new Tender can bind it. |
| TPR-SMOKE-13 | Send free text such as `Yes — evidence added automatically` to a Boolean field; reject it. |
| TPR-SMOKE-14 | Send an inactive UOM, a location from another PE and a personal user as the contract office; reject all three. |
| TPR-SMOKE-15 | Set pre-tender meeting to No and submit hidden meeting details; reject the hidden values. |
| TPR-SMOKE-16 | Open Task 3 and verify all price-response cells are blank supplier placeholders; attempt to save a unit price as the officer and reject it. |
| TPR-SMOKE-17 | Compare the five Draft screens with the section 8 control contract and verify every field's control, source label and editability. |

## 16. Required walkthrough before implementation

Use a practising Procurement Officer, one requesting-department representative and the Head of Procurement Function or procurement reviewer.

Run three no-code checks:

1. **KEBS-style equipment:** complete all five tasks and review the generated Tender.
2. **NSSF ERP:** confirm the first pattern rejects it and identify only the additional fixed content needed by a future complex-IT pattern.
3. **Adole Footbridge WORKS:** confirm the first pattern rejects it and that WORKS remains a separate product.

Record only:

- time taken;
- unclear questions;
- duplicate entry;
- information the officer could not reliably provide;
- missing Tender content;
- unnecessary fields; and
- blockers with a named correction owner.

The walkthrough result is **GO**, **SIMPLIFY FURTHER** or **REJECT**. Implementation remains unauthorised until the result and this document are approved.

## 17. Implementation constraints

If later approved for implementation:

- implement this module in `kentender_procurement` using ordinary Frappe records, permissions, private Files, transactions and audit;
- use one code-owned IT-equipment template, not a generic engine;
- keep the reviewed template bundle under version control with one idempotent loader and one read-only Supported Tender Template registry;
- reuse verified earlier IT Wizard content, labels, validation and rendering where it fits this narrower pattern;
- do not reuse parser/OCR services, inferred-schema logic, legacy generic runtime objects or compatibility layers;
- use server-side rules for scope, state, readiness, totals, approval and immutability;
- use the existing Vue 3/Frappe Desk shell and KenTender components;
- test the focused domain and contract first, then screens and the complete smoke contract; and
- remove a field or step that has no current Tender, validation, supplier-response, evaluation, contract or publication use.

## 18. Explicit exclusions

Do not add:

- an STD Library administration screen;
- Configurator or STD Reviewer roles;
- runtime package activation;
- manifests, schema editors or clause editors;
- generic requirement, form, evaluation or contract designers;
- AI or PDF parsing in the production path;
- seven runtime manifests;
- user-defined workflow states;
- a second permission system;
- a separate technical-contributor workflow;
- optional fields for possible future reporting; or
- complex IT or WORKS controls hidden behind feature flags.

## 19. Sources and precedence

This document follows:

- **STD-ST-001 v0.3 — Approved**, which locks the simple productised-template direction;
- **STD-ADR-002 v1.0**, which replaces the generic STD engine with released templates; and
- **REQ-CHG-001 v1.0 — Approved**, which supplies the immutable authorised Requisition handoff.

The first template uses the **PPRA Standard Tender Document for Procurement of Goods**, published through the [PPRA Standard Tender Documents register](https://ppra.go.ke/standard-tender-documents/). The exact downloaded file and digest recorded in the release evidence control the locked standard content; this document controls the KenTender user journey.

## 20. Approval effect

Approval of TPR-CHG-001 v0.3 will authorise implementation of the focused pack for this one IT-equipment vertical slice and its code-owned `IT-EQUIPMENT-OPEN-V1` bundle. Version 0.3 supersedes the incomplete field and screen-control contract in v0.2. It does not authorise complex IT, WORKS, a generic STD platform, Bidder Response, Evaluation, Award, Contract Management or production deployment.
