# STD-ST-001 — Practical STD and Tender-Preparation Stress Test

| Control | Value |
|---|---|
| Document ID | STD-ST-001 |
| Version | 0.2 |
| Date | 27 August 2026 |
| Status | Comparative desk test complete; human walkthrough pending |
| Decision under test | STD-ADR-002 v1.0 |
| Comparative examples | NSSF ERP tender; KEBS laptops/desktops/iPad tender; Kenya eGP desktop-computer tender export |
| Implementation authority | None |

## 1. Purpose

This stress test asks a practical question:

> Can KenTender help a Procurement Officer prepare a complete, legally safe tender without making the officer configure an STD, reproduce the official document field by field, or operate a generic schema platform?

Version 0.1 used the NSSF ERP tender as its main example. That was useful for exposing difficult cases, but it overcorrected by allowing one complex system procurement to shape the general product. Version 0.2 adds:

- a KEBS procurement of laptops, desktops and iPads as a comparatively straightforward IT-goods example; and
- a Kenya eGP tender export for desktop computers as evidence of both a useful standard-text principle and an impractical digitisation approach.

This remains a document-only test. It creates no code, DocTypes, APIs, records, migrations or permission model, and it does not authorise implementation.

## 2. Corrected interpretation of the examples

The three examples serve different purposes. None is the KenTender model.

| Example | What it proves | What must not be copied |
|---|---|---|
| NSSF ERP | Complex system tenders may need requirements, phases, integrations, migration, acceptance, support and detailed contract obligations | Do not make ERP-specific structures mandatory for ordinary IT goods |
| KEBS laptops/desktops/iPad | A goods tender can be prepared mainly through TDS decisions, goods/specification rows, delivery, price, evaluation, forms and SCC values | Do not copy unresolved placeholders, inconsistent dates, or potentially restrictive specifications as product rules |
| Kenya eGP desktop export | Standard text can be held centrally and assembled with tender-specific values | Do not expose clause text as data-entry rows, export fragmented forms, or turn every template prompt into a generic parameter |

The NSSF tender is therefore an **adversarial complex-case fixture**, not the default IT tender.

## 3. Minimal product decision under test

KenTender should not build an operational STD Configuration module for ordinary users. It should release a small number of **code-owned tender patterns** based on the applicable official STD.

For the current IT scope, the desk test needs only these two patterns:

| Product pattern | Intended use | Included only where relevant |
|---|---|---|
| IT equipment/goods | Laptops, desktops, peripherals and other defined equipment | Goods/specification schedule, delivery schedule, price schedule, evaluation, forms and contract variables |
| Complex IT system/implementation | ERP, integrated platforms and implementation-heavy procurements | Adds requirements conformance, phases, integrations, migration, acceptance milestones, service levels and system-specific contract obligations |

These are released product patterns, not user-configurable profiles. The applicable official STD and procurement treatment determine which pattern is used. A Procurement Officer does not add steps, define schemas or turn complex-system sections on for an equipment tender.

The system must remain capable of adding another product pattern later, but it must not build a generic framework in anticipation of one.

## 4. How standardized text should work

The eGP export establishes one good principle: official standard text should be controlled centrally and assembled into each tender. KenTender should retain that principle but use a much simpler implementation.

### 4.1 Required treatment

For each supported official STD version, the product release contains:

- the locked standard sections, including applicable ITT and GCC text;
- the official forms and declarations;
- the finite set of tender-specific questions;
- the fixed schedules used by that tender pattern;
- the rules that place answers into the correct TDS, SCC, notice, form or schedule location; and
- the completeness and consistency checks required before approval.

The Procurement Officer works with business questions such as **Tender closing date**, **Tender validity**, **Tender security**, **Delivery location** and **Warranty period**. The officer does not see a legal-text editor, placeholder registry, mapping screen, manifest or schema.

The preview presents one coherent tender. It must not print internal authoring labels such as `Manual Input`, `Auto Populate`, field codes or unresolved insertion instructions.

### 4.2 What the eGP export teaches us not to do

The inspected eGP package converts much of the official document into generic tables and downloadable files. The result includes:

- long ITT clauses repeated beside individual TDS values;
- `Manual Input` and `Auto Populate` metadata printed in the tender;
- numerous irrelevant provisions completed as `NOT APPLICABLE`;
- visible ellipses and template prompts;
- price and requirement schedules separated from an otherwise generated tender;
- duplicate logical content across the PDF, spreadsheets and Word files;
- spreadsheet instructions that use artificial values such as `0.1` when an answer is not applicable;
- default `YES` answers in bidder questionnaires;
- formulas described as text rather than implemented calculations; and
- a main tender PDF containing headings or blank pages where the actual content exists only in a separate attachment.

These are not merely presentation defects. They show what happens when the document's authoring structure is mistaken for the user's task.

KenTender must maintain one source for each fact and generate all required representations from it. It must never require users or suppliers to reconcile competing PDF, Word and spreadsheet versions of the same schedule.

## 5. The parameter rule

A tender value should become structured data only if at least one of the following is true:

1. it changes for a particular tender and must render into the tender;
2. the system must validate it for legal or internal consistency;
3. a supplier must respond to it in a structured way;
4. an evaluator must apply it; or
5. it must carry into award or contract administration.

If none applies, the content stays in the locked standard text or in an authorised supporting document.

### 5.1 Five simple content classes

| Content class | Example | Treatment |
|---|---|---|
| Inherited fact | Procuring Entity, plan item, approved method | Read-only from the authorised upstream record |
| Officer decision | Closing date, security, lots, delivery point, evaluation threshold | Plain-language field in the applicable product pattern |
| Repeatable business data | Goods, quantities, delivery dates, price lines, scored criteria | Fixed table with add-row, bulk paste and controlled import |
| Locked standard content | ITT, GCC, statutory wording and official form language | Versioned with the product release; not edited during tender preparation |
| Supplier response/evidence | Offered price, compliance answer, declaration, certificate or catalogue | Captured only to the degree needed for responsiveness, evaluation and contract formation |

The following must not become parameters:

- whole paragraphs of standard text;
- template directions such as `[insert name]`;
- `N/A` stored as a fake number or required text value;
- authoring metadata such as who fills the field;
- duplicated values maintained independently in several sections;
- a generic row for every possible official clause; or
- narrative background that creates hidden supplier obligations.

Not applicable is a state, not a value. Where a conditional provision does not apply, KenTender should omit its completion control and render the legally appropriate result without asking the officer to type `NOT APPLICABLE` repeatedly.

## 6. Forms and attachments: a deliberate hybrid

Simplicity does not require every official form to become hundreds of web fields. Nor should the supplier be sent a loose folder of disconnected Word and Excel templates.

KenTender should use this hybrid rule:

| Material | Minimal treatment |
|---|---|
| Tender and supplier identity used repeatedly | Capture once and populate into applicable forms |
| Prices, quantities, delivery offers and scored responses | Structured, because the system must validate and evaluate them |
| Statutory declarations | Preserve official wording; prefill known identity; require the supplier's explicit confirmation/signature and any required upload |
| Evidence such as certificates, authorisations and catalogues | Checklist plus upload/reference; do not decompose the document into unnecessary fields |
| Detailed drawings or specialist specifications | Governed attachment where a fixed table is inadequate; any binding obligation must still be visible in the tender scope or schedule |

The published package may offer convenient spreadsheet import/export for large fixed tables, but the platform record remains the source of truth. An exported spreadsheet is not a parallel tender document.

## 7. Practical officer journey

Both product patterns should use the same five-task shell. The content changes; the user does not configure that change.

| Task | IT equipment/goods example | Complex IT system example |
|---|---|---|
| 1. Tender details | Identity, dates, communication, lots, validity and security | Same |
| 2. What is required and when | Goods, minimum specifications, quantities, destination and delivery | Scope, requirement rows, implementation phases, integrations and acceptance |
| 3. How suppliers price | Goods and related-service price rows | Implementation, licence, migration, training, support and recurrent-cost rows |
| 4. How tenders are submitted and evaluated | Mandatory evidence, permitted technical checks and award basis | Adds qualification and scored technical criteria only where justified |
| 5. Contract-specific terms | Warranty, delivery, inspection, payment and performance security | Adds milestones, service levels, IP, support and other justified system obligations |

The system then provides:

```text
Readiness report
→ independent review and return/approve
→ complete tender preview
→ approval and immutable publication package
```

This is tender preparation, not STD configuration.

## 8. Worked comparison

### 8.1 KEBS equipment tender

The KEBS document shows the smaller path clearly:

- the TDS is a compact ITT-reference/value table;
- the purchase is expressed through equipment groups, quantities and minimum specifications;
- manufacturer authorisation, warranty and datasheets/brochures are submission requirements;
- tender validity, security, destination and other tender choices are finite; and
- the applicable forms, GCC/SCC and contract forms remain part of the standard document.

A Procurement Officer should therefore complete a short TDS form and a small number of fixed schedules. The officer should not see ERP phases, system inventory, data migration, escrow, service-level design or a generic conformance engine unless the applicable tender pattern genuinely requires them.

The example also exposes readiness checks KenTender should perform:

| Observed issue | Minimal system response |
|---|---|
| Different closing times appear in different parts of the document | Store the deadline once and render it everywhere; block conflicting output |
| An `[insert figure]` placeholder remains in the TDS | Block approval while any active placeholder remains |
| Blank official Schedule of Requirements templates remain after detailed specifications | Require one completed goods/delivery source and suppress unused template rows |
| Product-specific characteristics are used | Ask for `or equivalent` treatment and any required justification; route to review |

### 8.2 NSSF ERP tender

The NSSF example remains valuable because it shows when the larger pattern is justified:

- a multi-module system scope;
- phased implementation;
- platform and integration dependencies;
- data migration, testing and training;
- technical qualification and scoring;
- acceptance-linked payment and warranty; and
- support and system-specific contract obligations.

Even here, the requesting department should supply the business need, technical facts and constraints—not draft every supplier obligation. Procurement owns the tender-facing treatment and obtains technical, legal or finance clarification where required.

Fixed tables and bulk import are still sufficient. The officer must not design a requirements schema, response model, evaluation engine or contract mapping.

### 8.3 Kenya eGP tender export

The eGP example is useful as a negative supplier-experience test. A supplier should not have to discover that:

- the main tender PDF has an empty price or requirements section;
- the operative table is in a separate spreadsheet;
- another copy of the same material appears elsewhere;
- a questionnaire is prefilled with assumed answers;
- an irrelevant rule requires an artificial numeric response; or
- totals must be calculated manually although the platform already has the quantities and prices.

KenTender should publish one internally consistent package. Structured response forms, human-readable PDF and permitted downloads must all be generated from the same approved snapshot.

## 9. Readiness and responsibility

Readiness must identify a small number of meaningful problems, not produce hundreds of warnings from unused clauses.

| Check | Owner and correction route |
|---|---|
| Missing or conflicting tender identity/date/value | Procurement Officer corrects the tender field |
| Missing goods, delivery or price rows | Procurement Officer completes them with requesting-department/finance clarification |
| Incomplete or ambiguous technical requirement | Return to the requesting department or technical adviser for clarification |
| Unjustified restrictive product requirement | Procurement Officer obtains justification or neutralises the requirement; reviewer decides |
| Required official form or declaration absent | Product defect if deterministic; officer resolves only a genuine tender choice |
| Price total, Form of Tender and award basis disagree | System blocks approval and shows the one owning source to correct |
| Supplier obligation exists only in background narrative | Move it into the visible requirement, schedule or contract term before approval |
| Conditional provision does not apply | System handles the condition; do not require a typed placeholder |

The requesting department is not required to specify procurement securities, official forms, bidder declarations, evaluation mechanics or final contract clause placement. Procurement remains accountable for a complete tender and may seek specialist input without transferring ownership of the process.

## 10. Permissions and segregation boundary

This document specifies outcomes, not a new authorization layer.

| Attempt | Required outcome |
|---|---|
| Requesting-department user changes an authorised need | Use the governed Requisition return/amendment route |
| Procurement Officer prepares and submits the tender | Allowed for an assigned record within the user's permitted entity scope |
| Drafter approves the same tender | Denied where maker-checker segregation applies |
| Reviewer edits the officer's tender silently | Denied; return with a reason |
| Supplier accesses internal planning, budget, review or approval material | Denied |
| Evaluator changes published criteria | Denied |
| Officer edits a published tender | Denied; use an approved addendum |

Implementation should use Frappe's native Roles, DocType permissions, User Permissions, Workflow and record-state checks wherever they are sufficient. STD-ST-001 creates no Capability Profile, Operational Scope Assignment, parallel role grant or new permission architecture.

## 11. Revised decision against the hypotheses

| Hypothesis | Result | Comparative evidence |
|---|---|---|
| A generic STD Configuration platform is required | Fail | The finite examples can be served by released, code-owned patterns |
| One NSSF-derived IT pattern is sufficient | Fail | The KEBS equipment tender does not need most ERP structures |
| Official standard text should be centrally controlled | Pass | The eGP principle is sound; the output and authoring experience need correction |
| Every official prompt should become a parameter | Fail | eGP demonstrates the volume, irrelevance, duplication and poor output this creates |
| A small set of explicit business fields and fixed tables is enough | Conditional pass | It covers both examples on paper; practising users must validate it |
| All supplier forms should be decomposed into fields | Fail | A hybrid of structured responses, locked official wording and evidence uploads is simpler and safer |
| Requisition can remain minimal | Pass | Procurement can complete tender treatment with targeted clarification |
| The model is ready for implementation | Fail | No human walkthrough or prototype implementation has been authorised |

## 12. Stress-test verdict

### Decision: RETAIN THE SIMPLE DIRECTION, CORRECT THE PRODUCT SHAPE

STD-ADR-002's rejection of a generic STD Configuration engine remains correct. The comparative evidence makes the intended replacement clearer:

- support official STD versions through controlled software releases;
- provide code-owned tender patterns, beginning with simple IT equipment and complex IT implementation;
- keep locked standard text out of operational data entry;
- digitize only a finite set of tender decisions and repeatable schedules;
- preserve official form language while structuring only what must be validated, evaluated or carried forward;
- generate one coherent tender and supplier-response package from one approved source; and
- use readiness checks to catch contradictions, unresolved placeholders and missing operative schedules.

The system must not preserve configurability merely because a future tender might use it. A new need should first be handled as a deliberate product change. Generalisation is justified only after more than one implemented pattern proves the same stable structure.

## 13. Required human validation before any implementation decision

Run two static, no-code walkthroughs:

1. **Simple goods:** recreate the KEBS laptop/desktop/iPad tender using the five-task shell.
2. **Complex system:** recreate the NSSF ERP tender using the same shell with the complex pattern's additional fixed tables.

Include one practising Procurement Officer, one requesting-department representative, one procurement/legal reviewer and, if possible, one supplier-side tender preparer.

The exercise passes only if:

- the KEBS example remains visibly simple;
- the NSSF example can express its necessary complexity without schema or mapping concepts;
- no participant must reconcile duplicate PDF, Word and spreadsheet sources;
- every entered value has a visible tender, validation, supplier-response, evaluation or contract purpose;
- no supplier obligation is assigned solely to a requesting department that cannot reliably determine it;
- the preview contains all operative schedules and no unresolved placeholders;
- standard text is present in the final tender but absent from routine data entry; and
- each participant can identify who corrects every blocker.

Record observed time, unclear questions, duplicate entry, off-system work and missing decisions. The result should produce v0.3 with a `GO`, `SIMPLIFY FURTHER` or `REJECT` recommendation.

## 14. Artifact disposition and source boundary

This stress test:

- does not approve or amend STD-ADR-002;
- does not authorise a new STD Configuration module;
- does not amend the Requisition requirements;
- does not authorise Tender Preparation design or implementation;
- does not establish the legal applicability of a particular STD to a procurement; and
- does not replace review of the official source documents by authorised procurement/legal personnel.

The comparative desk test used:

- the NSSF Staff Pension Scheme ERP calibration and earlier IT Wizard material;
- `TENDER-FOR-LAPTOPS-MOMBASA-2026-JUNE-02-FINAL.pdf` supplied for the KEBS comparison;
- the supplied Kenya eGP export bundle `27378_27-08-2026.zip`, including its generated tender PDF, schedules and official-form attachments;
- STD-ADR-002 v1.0; and
- the existing Requisition decision boundary.

The examples are evidence, not authorities for copying an entity's wording, omissions, defaults or procurement choices.
