**Statutory Declarations**

**Objective**

Implement the IT STD Statutory Declarations as one electronic declaration screen with:

- Four separately preserved legal records
- One independent-tender determination response
- One authorized declarant
- One certification action
- One certification event covering all four records

Implement this section only. Do not implement unrelated checklist sections.

Use the approved Stitch screens as the visual reference.

**Rationale**

The canonical IT STD contains four relevant statutory records:

- Certificate of Independent Tender Determination
- SD1 - Self-Declaration that the Tenderer is Not Debarred
- SD2 - Self-Declaration that the Tenderer will not engage in Corruption or Fraud
- Code of Ethics Declaration, incorporating acknowledgement of the Fraud and Corruption Appendix

These are legally distinct records, but the paper separation does not justify four repetitive electronic workflows.

The only declaration containing a genuine bidder choice is the Certificate of Independent Tender Determination. SD1, SD2 and the Code of Ethics are fixed legal commitments.

The electronic system must therefore:

- Preserve each declaration as a separate legal record
- Present the obligations clearly
- Obtain one explicit certification covering all four
- Avoid repeated signatory details, signatures and confirmation dialogs
- Generate the complete declaration records internally

**Redesign ethos**

- Preserve every substantive legal declaration.
- Remove paper-driven repetition.
- Capture each value once.
- Reuse tender, Tenderer and declarant information from authoritative sources.
- Do not convert signature blocks, stamps, pagination or repeated form headings into user inputs.
- Do not create separate workflows merely because the STD uses separate paper forms.
- Do not claim that declarations are verified by PPRA.
- Do not expose hashes, schema identifiers, database IDs or template metadata.
- Do not render or require PDFs.
- Do not build a generic legal-document engine.
- Implement the manually configured IT STD declaration templates required for this task.
- NSSF remains test data only.
- Development data may be reset. Do not add production migration or compatibility complexity.

**1\. Inspect and reuse the existing implementation**

Before changing code:

- Locate the current Bidder Workspace checklist.
- Locate the CBQ authorized-signatory data.
- Locate the existing section-status and certification patterns.
- Locate the approved Statutory Declarations Stitch files.
- Reuse existing services, models, permissions, templates and shell components.

Do not create parallel readiness, authorization or audit systems.

Implement the feature after inspection; do not stop at a plan.

**2\. Position and checklist state**

Keep Statutory Declarations after CBQ.

Use the existing checklist states:

- Not Started
- In Progress
- Needs Attention
- Complete

The section is Complete only after the declaration bundle is certified.

If certification is invalidated by later changes, return the section to Needs Attention.

**3\. Authoritative data sources**

Use the following sources:

| **Declaration value**                        | **Source**             |
| -------------------------------------------- | ---------------------- |
| Tender name and reference                    | Published tender       |
| Procuring Entity                             | Published tender       |
| Tenderer legal name                          | CBQ                    |
| Tenderer office address, telephone and email | CBQ                    |
| Authorized declarant full name               | CBQ                    |
| Declarant title/designation                  | CBQ                    |
| Declarant postal address                     | CBQ                    |
| Declarant place of residence                 | CBQ                    |
| Declarant country of residence               | CBQ                    |
| Authority to bind the Tenderer               | CBQ                    |
| Declaration date/time                        | System                 |
| Independent-tender answer                    | Statutory Declarations |
| Competitor disclosures                       | Statutory Declarations |

Do not create editable declaration copies of derived values.

**4\. Close CBQ data gaps**

Inspect the current authorized-signatory fields.

If missing, add these fields once to the CBQ authorized-signatory section:

- Postal address
- Place of residence
- Country of residence

Ensure the CBQ authority confirmation states that the person is authorized to certify bid forms and bind the Tenderer.

Do not add these fields to Statutory Declarations.

If required declarant data is incomplete, show:

Complete the authorized declarant details in the CBQ.

Provide:

Edit in CBQ

Disable declaration certification until the missing information is completed.

**5\. Minimal persistence**

Use existing repository conventions.

Persist only what is necessary:

**Declaration bundle**

- Bid
- Status: draft, ready, certified or requires recertification
- Independent-tender response
- Certified by
- Certified at

**Competitor disclosures**

Repeatable rows containing:

- Competitor name
- Nature of interaction
- Reason
- Complete details

**Generated legal records**

At certification, preserve four separate records:

- Certificate of Independent Tender Determination
- SD1 - Not Debarred
- SD2 - No Corruption or Fraud
- Code of Ethics Declaration with Appendix acknowledgement

Each record must retain:

- Exact rendered legal text
- Tender and Tenderer particulars
- Declarant particulars
- Shared certification event
- Certifying user
- Certification date/time

Do not introduce content-addressing, digest systems or a generalized publication pipeline.

**6\. Implement the main screen**

Create one Statutory Declarations screen.

**Authorized Declarant**

Display once, read-only from CBQ:

- Full name
- Title/designation
- Postal address
- Place of residence
- Country of residence
- Authority to bind the Tenderer: Confirmed
- Edit in CBQ

Do not repeat the declarant under every declaration.

**Certificate of Independent Tender Determination**

Ask:

How was this tender prepared?

Provide two required choices with no default:

Independently, without consultation, communication, agreement or arrangement with any competitor.

Consultation, communication, agreement or arrangement with one or more competitors occurred and must be disclosed.

Do not infer or preselect an answer.

**SD1 - Not Debarred**

Display:

The Tenderer, its directors and subcontractors have not been debarred from participating in public procurement proceedings.

Do not add a Yes/No question.

**SD2 - No Corruption or Fraud**

Display:

The Tenderer, its agents and subcontractors have not and will not engage in corruption, fraud, inducement or collusion in this tender.

Do not add a Yes/No question.

**Code of Ethics**

Display:

The Tenderer has read and understood the applicable procurement legislation and Code of Ethics and commits to comply with them.

Display:

Fraud and Corruption Appendix acknowledged.

The Appendix is not a fifth declaration.

**Legal text actions**

Provide Read full legal text for each of the four records.

Use one primary action:

Certify Statutory Declarations

Do not add:

- Individual certification buttons
- Individual confirmation dialogs
- Per-form signature fields
- Per-form progress steps
- Uploaded signatures
- Stamp uploads

**7\. Implement competitor disclosures**

When the second independent-tender option is selected, reveal a required repeatable table containing:

- Competitor name
- Nature of interaction
- Reason
- Complete details
- Remove

Provide:

Add another disclosure

Require at least one complete row.

Show:

Complete disclosure required before certification.

Do not require a supporting PDF. The structured electronic disclosure replaces the paper attachment.

If the bidder changes back to the independent option, require explicit confirmation before discarding any existing disclosure rows.

**8\. Implement the legal-text drawer**

Open the approved right-hand drawer from Read full legal text.

The drawer title must match the selected record.

Render the exact configured legal text from the canonical IT STD.

Requirements:

- Preserve approved wording.
- Preserve headings, paragraphs and numbering.
- Insert the tender, Procuring Entity, Tenderer and declarant values.
- Incorporate the independent-tender answer and disclosures where applicable.
- Keep the content read-only.
- Do not paraphrase.
- Do not display PDF pages.
- Do not show technical metadata.

For Code of Ethics, provide access to the complete Fraud and Corruption Appendix.

**9\. Certification readiness**

Enable certification only when:

- CBQ is certified
- Required declarant information is complete
- The declarant's authority to bind is confirmed
- The independent-tender question is answered
- Required competitor disclosures are complete
- The current user has the existing permission to certify for the bidder

Use the existing authorization model.

Do not introduce another permission subsystem.

**10\. Implement one certification dialog**

Open one dialog:

Certify Statutory Declarations?

State that the certification covers:

- Certificate of Independent Tender Determination
- SD1 - Not Debarred
- SD2 - No Corruption or Fraud
- Code of Ethics Declaration and Fraud and Corruption Appendix acknowledgement

Show:

By certifying, you confirm that each listed declaration is true and complete and that you are authorized to make these declarations on behalf of the Tenderer.

Display:

- Tenderer
- Tender reference
- Authorized declarant
- Title/designation

Actions:

- Cancel
- Certify Statutory Declarations

Do not request the declarant's details, password, signature, stamp or four separate confirmations.

**11\. Certification transaction**

Certification must be atomic.

In one transaction:

- Revalidate all source data and permissions.
- Render all four exact legal records.
- Store the declaration bundle response.
- Store any competitor disclosures.
- Store the four legal-record snapshots.
- Record the authenticated certifying user and date/time.
- Mark the declaration bundle certified.
- Mark the checklist section Complete.

If any step fails, do not partially certify the bundle.

**12\. Certified state**

After certification show:

Statutory Declarations certified

Display:

- Tenderer
- Authorized declarant
- Title/designation
- Certification date/time

List as Certified:

- Certificate of Independent Tender Determination
- SD1 - Not Debarred
- SD2 - No Corruption or Fraud
- Code of Ethics Declaration

Keep Read full legal text available for each record.

Primary action:

Return to Checklist

Do not display internal audit identifiers.

**13\. Recertification**

Invalidate the entire declaration bundle when any relevant source changes:

- Tender or Procuring Entity particulars
- Tenderer legal name
- Declarant identity or contact particulars
- Declarant authority
- Independent-tender answer
- Competitor disclosures
- Configured legal declaration text

On invalidation:

- Preserve the previous certified records in audit history
- Change status to Requires recertification
- Mark the checklist section Needs Attention
- Require one new bundle certification

Do not build field-level invalidation. Invalidate the complete bundle.

**14\. Witness boundary**

Do not implement an external witness workflow in this task.

Do not add:

- Witness name fields
- Witness email fields
- Witness invitation
- Bidder-entered witness signatures
- Witness status

The paper Code of Ethics witness block remains an explicit legal-template decision for pre-production review.

Record this unresolved point in the implementation report. Do not represent it as legally resolved.

For the current development implementation, the authenticated declaration-bundle certification is the only bidder certification event.

**15\. Tests**

Add tests for:

- Statutory Declarations appears after CBQ.
- Declarant particulars are sourced from CBQ.
- Missing declarant details block certification.
- No declarant fields are duplicated in the declaration screen.
- Independent-tender choices have no default.
- The independent option requires no disclosure rows.
- The consultation option requires at least one complete disclosure row.
- Incomplete disclosure rows block certification.
- SD1, SD2 and Code of Ethics have no unnecessary Yes/No inputs.
- Only one certification action and dialog exist.
- Unauthorized users cannot certify.
- Certification atomically creates four separate legal records.
- Every record contains the correct tender, Tenderer and declarant values.
- The Fraud and Corruption Appendix is incorporated but not treated as a fifth declaration.
- A relevant source change invalidates the whole bundle.
- Previous certification records remain in audit history.
- No NSSF-specific values are hard-coded.
- No hashes or internal identifiers appear in the bidder UI.
- No witness workflow is introduced.

Run the relevant existing test suite and the new Statutory Declarations tests.

**16\. Completion report**

Implement the feature; do not stop after producing a plan.

When complete, report:

- Files changed
- Data-model changes
- CBQ source fields added or reused
- Declaration templates implemented
- Certification transaction
- Invalidation behaviour
- Tests added and results
- Witness decision recorded as unresolved
- Any deviation from this prompt and why

Stop after completing Statutory Declarations.