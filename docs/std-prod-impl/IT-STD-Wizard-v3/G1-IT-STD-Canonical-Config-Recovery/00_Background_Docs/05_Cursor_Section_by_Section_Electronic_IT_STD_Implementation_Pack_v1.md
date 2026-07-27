# KenTender e-Procurement System

# Cursor Section-by-Section Electronic IT STD Implementation Pack v1

## 1. Purpose

This pack divides the PPRA Information Technology STD bidder workspace into small Cursor implementation prompts.

Run only one prompt at a time. Each prompt must produce a working user-facing increment, focused tests and a short report before the next prompt begins.

This pack supersedes:

- `Cursor_Lean_Electronic_STD_Template_Delivery_Directive_v1.md`;
- `Cursor_Phase_5R_Simplified_Manifest_and_Publication_Baseline_v1.md`; and
- earlier Phase 4/5 BWMF implementation directions where they conflict with the lean manual-template approach.

The product objective is a legally faithful, fully electronic bidder experience. It is not an automated STD interpretation platform.

## 2. How to use this pack

### 2.1 Run the foundation once

Run prompt `F0` first.

### 2.2 Run one selected prompt

Start a fresh Cursor conversation for each prompt. Give Cursor this launcher:

```text
Read "Cursor_Section_by_Section_Electronic_IT_STD_Implementation_Pack_v1.md".

Apply the Common Control Rules and execute prompt [PROMPT ID] only.

Do not execute, plan or implement any other prompt in the pack.
Inspect the repository, implement the selected scope, run its tests and create its required report.
Stop after the report.
```

Replace `[PROMPT ID]` with the selected identifier, for example `S800`.

### 2.3 Review between prompts

After each Cursor run:

1. review the section in the browser;
2. review Cursor’s report;
3. provide the report and screenshots for independent review;
4. correct the section before starting another; and
5. do not combine unfinished section work.

### 2.4 Design prerequisite

Stitch owns design. Cursor owns system implementation.

Run a page prompt only after its Stitch design or approved shared layout is available. Cursor must preserve that design and must not redesign the screen.

## 3. Common Control Rules

These rules apply to every prompt.

### 3.1 Product and source rules

- The official PPRA IT STD is the legal source.
- The canonical obligation catalogue identifies required electronic obligations.
- The canonical section blueprint owns section boundaries and task groups.
- The manually curated electronic template owns the system representation.
- The confirmed tender configuration supplies tender-specific values.
- NSSF is calibration data only.
- No PDF page number or PDF form-filling workflow is a runtime dependency.

### 3.2 Lean implementation rules

- Reuse `Tender Configuration`, `Confirmed Tender Document Package`, `IT Tender Publication Record`, `Electronic Bid Submission`, `Electronic Bid Audit Event` and `File`.
- Add fields to existing records where practical.
- Do not add a general-purpose compiler, rules language, resource registry, content-addressed store, chunking, per-resource digests or template-authoring UI.
- Do not use legacy `10_NSSF_Electronic_Bidder_Submission_Schema.json` as production authority.
- Do not use `schema_compiler.SECTION_KEYS` as checklist authority.
- Do not repair or extend abandoned BWMF Phase 4/5 infrastructure.
- Disconnect obsolete infrastructure only where it blocks the selected section.
- Development data may be cleared and reseeded.
- Preserve unrelated repository changes.

### 3.3 Electronic and legal controls

- Locked legal text is read-only.
- Tender-owned values are read-only to bidders.
- Bidder-owned values are clearly identified.
- Every obligation, field and evidence requirement has a stable key.
- Material requirements retain source clause/form references.
- Draft Save is not confirmation, signature or submission.
- Completion and issue state are derived by the server.
- A bidder may access only its own bid.
- Submitted data is immutable.
- Published tender-template snapshots are immutable.
- Addenda create new versions; they never overwrite published history.
- Material actions are audited.

### 3.4 Standard section status

Use only:

- `not_started`;
- `in_progress`;
- `needs_attention`;
- `complete`; and
- `not_applicable`.

Do not let the client set section status directly.

### 3.5 Standard implementation result

Every section prompt must deliver:

1. its manually curated template definition;
2. tender-specific population;
3. server read and save services;
4. validation and completion derivation;
5. bidder route/page implementation;
6. issue and evidence integration where applicable;
7. domain and integration tests;
8. browser/UI verification; and
9. the named completion report.

### 3.6 Standard stop rule

Do not implement the next section, final submission or unrelated architecture.

## 4. Recommended execution order

The canonical display order differs from the most efficient implementation order because Form of Tender derives values and completion from several later sections.

| Run order | Prompt | Scope | Main dependency |
|---:|---|---|---|
| 1 | `F0` | Lean template and workspace foundation | None |
| 2 | `S100` | Tender Documents & Addenda | F0 |
| 3 | `X100` | Evidence and Issues foundations | F0 |
| 4 | `S150` | Lots & Alternatives | F0; conditional |
| 5 | `S300` | Confidential Business Questionnaire | F0 |
| 6 | `S400` | Statutory Declarations | F0 |
| 7 | `S450` | Tender Security | X100; conditional |
| 8 | `S500` | Preliminary Requirements & Evidence | X100 |
| 9 | `S600` | Qualification & Capability | X100; S300 |
| 10 | `S700` | Technical Proposal & Implementation Plan | X100; S150 where applicable |
| 11 | `S800` | Requirements Compliance | X100; S150 where applicable |
| 12 | `S900` | Price Schedule | S150 where applicable |
| 13 | `S200` | Form of Tender | S100, S300, S400, S450 where applicable, S900 |
| 14 | `G100` | Review & Validate | All applicable content sections |
| 15 | `G200` | Submit, Seal & Receipt | G100 |
| 16 | `A100` | Addendum impact and reconfirmation | G100/G200 |
| 17 | `F900` | Final template approval and end-to-end gate | All applicable prompts |

`S150` and `S450` are conditional. NSSF omits Lots & Alternatives and includes Tender Security according to its controlled configuration decision.

---

# Prompt F0 — Lean Template and Workspace Foundation

## Outcome

Create the small shared foundation required by all section prompts.

## Cursor instructions

1. Read the official IT STD, obligation catalogue and section blueprint.
2. Create a manually curated, version-controlled PPRA IT STD template file.
3. Add the canonical section registry using stable keys, order, title, renderer and applicability:
   - `tender_documents_and_addenda`;
   - `lot_and_alternative_selection` when configured;
   - `form_of_tender`;
   - `confidential_business_questionnaire`;
   - `statutory_declarations`;
   - `tender_security` when configured;
   - `preliminary_requirements_and_evidence`;
   - `qualification_and_capability`;
   - `technical_proposal_and_implementation_plan`;
   - `requirements_compliance`; and
   - `price_schedule`.
4. Add a small readable template validator. Reject duplicate keys, missing source references, unsupported renderers and invalid ordering.
5. Add minimal template lifecycle metadata: `Draft → Reviewed → Approved → Retired`, with preparer, reviewer, approver, dates and template hash. The preparer must not approve.
6. Keep the template Draft while section prompts are incomplete. Permit development preview for section testing, but require Approved before ordinary bidder-visible publication.
7. Add a simple tender-instantiation service that combines the template with a confirmed configuration and produces one JSON snapshot plus one SHA-256 hash.
8. Store or bind that snapshot using `IT Tender Publication Record`; do not add BWMF manifest publication records.
9. Add a shared section-response envelope inside `Electronic Bid Submission`, keyed by stable section key.
10. Add shared server-derived status and issue-result interfaces without implementing section-specific logic.
11. Replace checklist authority with the electronic-template snapshot selected for the current development preview or approved publication.
12. Preserve the approved A2 checklist design.

Do not implement individual section fields or pages in this prompt.

## Tests

Prove:

- template validity;
- deterministic snapshot/hash;
- template maker-checker and Approved-only ordinary publication;
- no NSSF constants in the canonical template;
- NSSF resolves to its applicable section set;
- a second small IT tender uses the same template;
- checklist order/titles come from the snapshot;
- legacy `SECTION_KEYS` is not authoritative; and
- unsupported section renderers fail closed.

## Report

Create:

```text
LEAN_F0_TEMPLATE_AND_WORKSPACE_FOUNDATION_REPORT.md
```

Stop after the report.

---

# Prompt S100 — Tender Documents & Addenda

## Section

- Key: `tender_documents_and_addenda`
- Renderer: `document_acknowledgement`
- Display title: `Tender Documents & Addenda`

## Required task groups

1. Current Tender Package
2. Addenda Register
3. Required Acknowledgements

## Cursor instructions

Implement the section from the current confirmed package and issued addenda.

The bidder must be able to:

- see the exact current package version and publication date;
- access every current tender document;
- see every applicable addendum, issue date and summary;
- distinguish newly issued or changed material;
- acknowledge only items for which acknowledgement is required; and
- see whether all current acknowledgements are complete.

Acknowledgements must bind the bidder, tender publication and exact document/addendum version. A material addendum must invalidate affected acknowledgements without deleting history.

Do not duplicate the document list elsewhere in the workspace. Do not rely on PDF pages.

Preserve the approved A3 design.

## Tests

Prove current-package display, version-bound acknowledgement, missing-acknowledgement blocker, addendum invalidation, bidder isolation and derived completion.

## Report

Create:

```text
LEAN_S100_TENDER_DOCUMENTS_AND_ADDENDA_REPORT.md
```

Stop after this section.

---

# Prompt X100 — Evidence and Issues Foundations

## Scope

Implement the two cross-cutting facilities used by later sections. They are not checklist sections.

## Cursor instructions

### Evidence

Use `File` plus minimal structured metadata and stable links to obligations, criteria, requirements or response rows.

Support:

- upload;
- replacement before submission;
- file type/size/safety validation;
- issuer/reference/issue/expiry metadata where required;
- original-language and translation linkage;
- reuse of one evidence item across compatible obligations;
- bidder ownership and isolation; and
- exact evidence version retained at submission.

### Issues

Create a shared server-derived issue result containing:

- stable issue code;
- severity;
- section/task/field target;
- bidder-safe message;
- correction route; and
- resolved/unresolved state.

Use `blocker`, `warning` and `information`. The client must not create or clear authoritative blockers.

Add shared Evidence and Issues views using the approved workspace shell. Do not add them to checklist progress.

## Tests

Prove file validation, replacement/version behavior, evidence reuse, required metadata, cross-bidder denial, server-derived issues and correction routes.

## Report

Create:

```text
LEAN_X100_EVIDENCE_AND_ISSUES_FOUNDATION_REPORT.md
```

Stop after these cross-cutting foundations.

---

# Prompt S150 — Lots & Alternatives

## Section

- Key: `lot_and_alternative_selection`
- Renderer: `lot_selection`
- Conditional section

## Required task groups

1. Lots Included in This Bid
2. Alternative Tenders
3. Required Responses

## Cursor instructions

Render this section only when the tender permits bidder lot selection or alternatives.

Support:

- selection of permitted lots;
- mandatory-lot and combination constraints;
- base-offer requirements;
- separate identity for each permitted alternative;
- clear rejection when alternatives are prohibited;
- derived downstream scope for requirements, qualification, technical and price responses; and
- confirmation of selections before dependent section completion.

Changing the selection must recalculate downstream applicability and invalidate affected completion without deleting responses.

NSSF must omit this section unless its confirmed configuration expressly permits it.

## Tests

Prove conditional generation, lot rules, prohibited alternatives, base-offer dependency, downstream scope changes and invalidation.

## Report

Create:

```text
LEAN_S150_LOTS_AND_ALTERNATIVES_REPORT.md
```

Stop after this section.

---

# Prompt S200 — Form of Tender

## Section

- Key: `form_of_tender`
- Renderer: `declaration_form`
- Display title: `Form of Tender`

## Required task groups

1. Tender and Bidder Details
2. Offer and Price Summary
3. Declarations and Disclosures
4. Associated Forms
5. Special Particulars
6. Authorized Confirmation

## Prerequisite

Run after Price Schedule, CBQ, Statutory Declarations, Tender Documents and applicable Tender Security are functional.

## Cursor instructions

Implement the complete canonical PPRA IT Form of Tender using:

```text
KenTender_Form_of_Tender_Electronic_Section_Specification_v1.md
```

Show tender/bidder identity and commercial totals as derived read-only values. Implement all required locked declarations and structured disclosures, including commissions/fees and state-owned status.

Show current completion of associated forms. Do not duplicate their inputs.

Save may persist bidder-owned disclosures but must not create authorized confirmation.

Authorized confirmation must be a separate deliberate action using the current form digest and verified representative authority. Final whole-bid authorization remains in `G200`.

Do not use an uploaded signed Form of Tender as the primary response.

## Tests

Prove derived values, price reconciliation, associated-form dependencies, conditional disclosures, Save-versus-confirm separation, authority checks, digest invalidation and section completion.

## Report

Create:

```text
LEAN_S200_FORM_OF_TENDER_REPORT.md
```

Stop after this section.

---

# Prompt S300 — Confidential Business Questionnaire

## Section

- Key: `confidential_business_questionnaire`
- Renderer: `questionnaire`

## Required task groups

1. Tendering Entities
2. General Particulars
3. Business Registration & Capacity
4. Ownership & Management
5. Interests & Relationships
6. Conflict-of-Interest Disclosures
7. Questionnaire Certification

## Cursor instructions

Create one questionnaire instance for the bidder and every required JV entity.

Reuse verified organization data as read-only or through a governed correction route. Collect tender-specific details electronically.

Implement conditional branches for sole proprietors, partnerships and companies. Include ownership/management rows, listing information, relationship disclosures and the complete conflict-of-interest matrix.

Every yes/no disclosure must be answered. Details must become mandatory when a disclosure requires explanation.

Certification is deliberate and entity-scoped. Material identity or disclosure changes invalidate certification.

Do not insert NSSF vendor or product qualifications into this canonical questionnaire.

## Tests

Prove entity/JV repetition, entity-type branching, required disclosures, conflict-matrix completeness, profile correction boundary, certification invalidation and bidder isolation.

## Report

Create:

```text
LEAN_S300_CONFIDENTIAL_BUSINESS_QUESTIONNAIRE_REPORT.md
```

Stop after this section.

---

# Prompt S400 — Statutory Declarations

## Section

- Key: `statutory_declarations`
- Renderer: `declaration_bundle`

## Required task groups

1. Independent Tender Determination
2. Debarment Self-Declaration
3. Fraud and Corruption Self-Declaration
4. Code of Ethical Conduct
5. Fraud and Corruption Appendix

## Cursor instructions

Implement each declaration as a distinct governed electronic response.

Use the exact locked legal text from the approved IT STD template. Implement controlled options and conditional disclosure details for the Independent Tender Determination certificate.

Keep SD1, SD2 and the Ethics commitment separate. Display the Fraud and Corruption appendix read-only with its associated acknowledgement status.

Saving declaration data must not silently certify it. Each required declaration needs deliberate confirmation by an authorized actor. A legal-text version change or material response change invalidates the affected confirmation.

Do not collapse the declarations into one generic checkbox.

## Tests

Prove distinct declarations, locked text, conditional disclosures, required actor/authority, confirmation invalidation and completion only when every applicable declaration is current.

## Report

Create:

```text
LEAN_S400_STATUTORY_DECLARATIONS_REPORT.md
```

Stop after this section.

---

# Prompt S450 — Tender Security

## Section

- Key: `tender_security`
- Renderer: `security_instrument`
- Conditional section

## Required task groups

1. Security Requirements
2. Security Response
3. Security Validation

## Cursor instructions

Generate this section only from the confirmed tender-security configuration.

Support the configured exclusive mode:

- tender security instrument;
- tender-securing declaration; or
- no bidder security response when the STD/configuration permits none.

For an instrument, capture issuer, instrument/reference number, amount, currency, issue date, expiry/validity, beneficiary, bidder/JV coverage and evidence.

For a declaration, render the exact locked declaration and collect deliberate confirmation.

Validate form, party identity, JV coverage, issuer class, amount, currency and required validity.

Do not classify professional indemnity insurance as tender security unless an approved tender decision expressly does so.

## Tests

Prove exclusive modes, conditional generation, instrument validation, JV identity, evidence linkage, declaration confirmation and NSSF’s controlled security decision.

## Report

Create:

```text
LEAN_S450_TENDER_SECURITY_REPORT.md
```

Stop after this section.

---

# Prompt S500 — Preliminary Requirements & Evidence

## Section

- Key: `preliminary_requirements_and_evidence`
- Renderer: `eligibility_checklist`

## Required task groups

1. Legal & Registration
2. Tax & Statutory Compliance
3. Mandatory Forms
4. Mandatory Authorizations
5. Additional Published Requirements

## Cursor instructions

Build the rows from the confirmed tender’s published preliminary criteria. Do not hard-code NSSF criteria into the template.

Each row must show:

- criterion/reference;
- requirement;
- applicability and scope;
- fulfilment type;
- authoritative form or evidence link;
- current status;
- issue; and
- correction action.

Where another section owns the value, show its current state and route there. Do not ask the bidder to upload a duplicate Form of Tender, CBQ or declaration.

Evidence-based rows must validate current evidence and required metadata. Completion requires every applicable mandatory criterion to be satisfied.

## Tests

Prove configured row generation, cross-section links, no duplicate response ownership, evidence requirements, missing mandatory blocker and NSSF’s nine preliminary criteria.

## Report

Create:

```text
LEAN_S500_PRELIMINARY_REQUIREMENTS_AND_EVIDENCE_REPORT.md
```

Stop after this section.

---

# Prompt S600 — Qualification & Capability

## Section

- Key: `qualification_and_capability`
- Renderer: `qualification_response`

## Required task groups

1. Entity Eligibility
2. Joint Venture
3. Contract History & Litigation
4. Financial Capacity
5. General Experience
6. Specific Experience
7. Key Personnel
8. Technical Capability
9. Subcontractors, Vendors & Manufacturers
10. Preference Information

## Cursor instructions

Build the response structure from the configured qualification criteria and canonical IT STD forms.

Use structured repeating records for:

- JV members and authority;
- contracts and litigation;
- financial statements, turnover and resources;
- general and similar-project experience;
- personnel positions and candidates;
- certifications and technical capability;
- subcontractors, vendors and manufacturers; and
- conditional preference information.

Link each configured criterion to its owning fields and evidence. The bidder supplies facts and evidence, not evaluator marks or pass/fail decisions.

Reuse CBQ/entity data where authoritative. Validate entity/lot scope, dates, currencies, totals, member rules and required evidence.

## Tests

Prove dynamic criteria, repeatable records, JV/member scope, evidence linkage, no bidder scoring fields, completion derivation, second-tender variability and NSSF’s nine qualification criteria.

## Report

Create:

```text
LEAN_S600_QUALIFICATION_AND_CAPABILITY_REPORT.md
```

Stop after this section.

---

# Prompt S700 — Technical Proposal & Implementation Plan

## Section

- Key: `technical_proposal_and_implementation_plan`
- Renderer: `technical_response`

## Required task groups

1. Technical Proposal
2. Project Organization & Management
3. Implementation Approach
4. Implementation Schedule
5. Training & Change Enablement
6. Testing & Quality Assurance
7. Warranty, Defect Repair & Support
8. Integration & Responsibilities
9. Offered System & Inventory
10. Software & Custom Materials
11. Substitutions & Technical Alternatives
12. Supporting Technical Evidence

## Cursor instructions

Implement structured responses for the configured technical topics. Attachments may support a response but must not replace the required structured content.

Populate the implementation schedule from configured milestones and allow bidder input only where explicitly permitted.

Support offered-system inventory, responsibility matrix, training, testing, migration, support, software/IP classifications and permitted substitutions or alternatives.

Link responses to applicable evaluation criteria, requirements, price items and evidence without exposing evaluator scores.

Fixed procuring-entity dates, responsibilities and contract terms remain read-only.

## Tests

Prove topic/configuration variability, structured-first responses, schedule rules, evidence links, inventory/IP rows, prohibited alternatives, no evaluator scoring inputs and NSSF’s six schedule rows.

## Report

Create:

```text
LEAN_S700_TECHNICAL_PROPOSAL_AND_IMPLEMENTATION_PLAN_REPORT.md
```

Stop after this section.

---

# Prompt S800 — Requirements Compliance

## Section

- Key: `requirements_compliance`
- Renderer: `requirement_matrix`
- Display title: `Requirements Compliance`

## Cursor instructions

Render every applicable response-bearing requirement from the tender configuration.

Support:

- grouped navigation;
- search and status filters;
- stable requirement identity;
- requirement text and context;
- mandatory/optional classification;
- lot/alternative scope;
- compliance choice;
- bidder explanation;
- offered value/model where requested;
- deviation/reservation details where permitted;
- evidence links;
- issues; and
- server-derived row and group status.

Use the approved Stitch A4 design with the right-hand response drawer. Keep the bidder in the matrix while editing.

Do not call the page “Technical Requirements.” Do not use PDF page references as the response mechanism.

NSSF must render 190 requirements in 23 groups, but those counts must come from fixture data.

## Tests

Prove arbitrary row counts, grouping, drawer save/reload, mandatory explanation/evidence rules, prohibited deviations, filters, status derivation, bidder isolation, NSSF counts and a smaller second tender.

## Report

Create:

```text
LEAN_S800_REQUIREMENTS_COMPLIANCE_REPORT.md
```

Stop after this section.

---

# Prompt S900 — Price Schedule

## Section

- Key: `price_schedule`
- Renderer: `price_schedule`

## Required task groups

1. Commercial Context
2. Supply & Installation
3. Recurrent Costs
4. Country of Origin
5. Discounts
6. Price Summary

## Cursor instructions

Implement the canonical PPRA IT price-table structure populated from configured price lines.

Use exact decimal calculations and explicit rounding. Present tender-owned quantities, units, currencies, tax rules, Incoterms and price basis as read-only.

Collect only permitted bidder price components. Calculate line totals, subtotals, tax, recurrent summaries, lot totals and grand total on the server.

Support configured discounts with an exact application method. Detect blank or omitted required lines according to the published rule.

Generate amount-in-words for Form of Tender where required. Do not hard-code KES, VAT rates or NSSF’s 22 lines.

## Tests

Prove decimal precision, calculations, currencies, taxes, discounts, omitted-line handling, lot totals, amount-in-words, immutable submitted prices, NSSF’s 22 lines and a different second tender.

## Report

Create:

```text
LEAN_S900_PRICE_SCHEDULE_REPORT.md
```

Stop after this section.

---

# Prompt G100 — Review & Validate

## Workflow gate

This is not a checklist content section.

## Cursor instructions

Implement a whole-bid Review & Validate page using current section responses, confirmations, evidence and dependencies.

Show:

- applicable section status;
- unresolved blockers;
- warnings;
- missing evidence;
- stale confirmations;
- document/addendum acknowledgement state;
- price/Form of Tender reconciliation;
- correction links; and
- last validation time.

Run server-authoritative current-version validation. A prior successful result becomes stale when any material response, evidence, template or addendum version changes.

Review must not submit the bid.

## Tests

Prove complete validation, stale-result invalidation, blocker/warning distinction, correction routing, current publication binding and no submission side effect.

## Report

Create:

```text
LEAN_G100_REVIEW_AND_VALIDATE_REPORT.md
```

Stop after this workflow gate.

---

# Prompt G200 — Submit, Seal & Receipt

## Workflow gates

1. Submit & Seal Bid
2. Submission Receipt

## Cursor instructions

Implement final electronic submission using the existing `Electronic Bid Submission`.

Before submission, verify:

- the current tender publication/template version;
- all applicable sections complete;
- no unresolved blockers;
- current successful validation;
- current acknowledgements and confirmations;
- authorized submitter identity, capacity and authority;
- server deadline; and
- idempotency of the submission action.

Create one immutable submission snapshot containing responses, evidence-version links, legal-text/template version, tender publication, confirmations and totals.

Calculate one snapshot integrity hash. Persist and seal atomically. Do not describe the hash as encryption or a digital signature.

Preserve confidentiality until lawful opening using the system’s approved access controls.

Issue a receipt only after successful persistence. Show receipt reference, tender, bidder, server timestamp, submission version and verification value.

Implement withdrawal/replacement only when the published policy permits it.

## Tests

Prove deadline enforcement, authorization, no-blocker requirement, current validation, atomic failure rollback, idempotent retry, immutable submitted data, receipt-after-success only, bidder isolation and configured withdrawal/replacement.

## Report

Create:

```text
LEAN_G200_SUBMIT_SEAL_AND_RECEIPT_REPORT.md
```

Stop after these workflow gates.

---

# Prompt A100 — Addendum Impact and Reconfirmation

## Cursor instructions

Implement addendum handling against stable section, task, field, criterion, requirement and price-line keys.

When a new tender publication version is issued:

1. preserve the prior published snapshot;
2. create the new snapshot;
3. identify added, removed and changed obligations;
4. carry forward unaffected draft responses;
5. mark affected responses stale or incomplete;
6. invalidate affected acknowledgements and confirmations;
7. retain response/evidence history;
8. show a bidder-facing change summary and correction routes; and
9. prevent submission against the superseded version.

Do not use labels or array positions as identity. Do not silently discard bidder work.

## Tests

Prove unaffected carry-forward, material invalidation, acknowledgement reset, confirmation reset, removed-item retention in history, bidder notice and superseded-version submission rejection.

## Report

Create:

```text
LEAN_A100_ADDENDUM_IMPACT_AND_RECONFIRMATION_REPORT.md
```

Stop after addendum handling.

---

# Prompt F900 — Final Template Approval and End-to-End Gate

## Outcome

Approve and activate the complete manually curated PPRA IT STD electronic template after every applicable section and workflow prompt has passed.

## Cursor instructions

1. Verify complete obligation-to-section coverage.
2. Verify source clause/form references.
3. Verify every registered renderer is implemented.
4. Verify there are no hidden NSSF constants.
5. Verify the template maker-checker record and final approved hash.
6. Generate the complete NSSF published snapshot.
7. Generate a second different IT tender snapshot.
8. Run the full bidder journey for both:
   - open tender;
   - review documents/addenda;
   - complete every applicable section;
   - resolve issues;
   - review and validate;
   - authorize;
   - submit and seal; and
   - receive a receipt.
9. Confirm evaluation scores are not bidder inputs.
10. Confirm post-award forms are not bidder checklist sections.
11. Confirm the checklist is dynamic by tender applicability.
12. Confirm no abandoned BWMF Phase 4/5 component is required by runtime.

Do not add new architecture during this final gate. Correct only verified gaps.

## Tests

Run all focused section gates, integration gates and bidder UI journeys with non-zero test counts.

## Report

Create:

```text
LEAN_F900_IT_STD_END_TO_END_ACCEPTANCE_REPORT.md
```

The report must provide the final template version/hash, section/applicability table, obligation coverage, NSSF and second-tender results, full test commands/counts, screenshots and any remaining release blocker.

Stop after the report.

---

## 5. Final control statement

This pack deliberately moves KenTender forward one bidder task at a time.

Each completed prompt must leave a visible, testable improvement. Cursor must not use a section prompt to introduce speculative architecture or to implement unrelated sections.
