**Electronic Form of Tender**

**Objective**

Implement the canonical IT STD Form of Tender as a single electronic **Review and Certify** section.

Implement this section only. Do not implement unrelated checklist sections.

Use the approved Stitch FoT screens as the visual reference.

**Rationale**

The printed Form of Tender appears early in Section IV of the STD, but printed document order is not the correct electronic workflow.

The FoT is not a bidder-data collection form. It is the final legal expression of the completed offer.

The previous multi-step FoT design was incorrect because it duplicated:

- Tenderer details from the CBQ
- Lots and alternatives
- Tender prices and discounts
- Tender configuration
- Declarations completed elsewhere

Duplicating these values creates inconsistency and legal risk.

**Redesign ethos**

Implement the FoT as a derived legal instrument:

- Each value has one owning section.
- The FoT displays material terms without reproducing entire source sections.
- Derived values are read-only.
- Corrections are made in the owning section.
- The only FoT-owned response is the commissions, gratuities and fees disclosure.
- Certification creates the complete legal FoT record.
- Do not recreate the paper form as a wizard.
- Do not require uploads of letterheads, signatures, stamps or PDFs.
- Do not expose hashes, schema identifiers, database IDs or technical metadata.
- Do not build a generic legal-document engine or new architectural layer.
- Use the existing models, services, permissions and UI shell.
- NSSF is test data only. Do not hard-code NSSF values or structure.
- Development data may be reset. Do not add production migration or backward-compatibility complexity.

**1\. Correct the checklist position**

Move Form of Tender to:

After Price Schedule

Before Final Declaration and Submission

The checklist order must follow bidder task dependencies rather than the printed STD order.

The FoT may be opened before it is ready, but certification must remain unavailable until its prerequisites are complete.

**2\. Use single-source data**

Build the FoT view from existing bid data.

| **FoT value**                               | **Authoritative source**       |
| ------------------------------------------- | ------------------------------ |
| Tender name, reference and Procuring Entity | Published tender               |
| Tender validity period                      | Published TDS configuration    |
| Tenderer legal name                         | CBQ                            |
| State-owned enterprise status               | CBQ                            |
| Authorized signatory name and title         | CBQ                            |
| Authority to bind the Tenderer              | CBQ                            |
| Base or alternative offer                   | Lots & Alternatives            |
| Selected/applicable lots                    | Lots & Alternatives            |
| Tender price and currencies                 | Price Schedule                 |
| Discounts and calculation method            | Price Schedule                 |
| Addenda acknowledgement                     | Tender Documents & Addenda     |
| Eligibility and integrity declarations      | CBQ and Statutory Declarations |
| Commissions, gratuities and fees            | Form of Tender                 |
| Certification date and certifying user      | System-generated               |

Do not create editable FoT copies of derived values.

**3\. Close source-data gaps**

Inspect the existing CBQ and Price Schedule implementation.

If missing, add only these minimal source fields:

**CBQ**

- Is the Tenderer a state-owned enterprise or institution? Yes/No
- If Yes: confirmation that the applicable ITT 4.7 conditions are met
- Authorized signatory full name
- Title/designation
- Confirmation that the signatory is authorized to certify bid forms and bind the Tenderer

Do not duplicate these fields in the FoT.

**Price Schedule**

Ensure discounts are captured once:

- Are discounts offered? Yes/No
- Discount description
- Applicable lot or entire tender
- Amount or percentage
- Currency, where applicable
- Exact calculation method

Do not duplicate discount entry in the FoT.

**4\. Implement FoT readiness**

Use the existing checklist/readiness mechanism.

FoT certification is ready only when:

- All required Prepare Bid sections except FoT are complete
- Tender Documents and the latest required addenda are acknowledged
- Lots & Alternatives is confirmed, where applicable
- CBQ is certified
- Statutory Declarations are complete
- Price Schedule is complete
- The commissions disclosure has been answered
- The current user has the existing authority required to certify for the bidder

Do not create another readiness framework.

Return a concise list of incomplete source sections with direct UI links.

**5\. Implement the main screen**

Create one **Form of Tender - Review and Certify** screen.

**Ready state**

Show:

Ready to certify

**Not-ready state**

Show:

Complete the following requirements before certifying.

List only incomplete source sections. Do not reproduce their missing fields in the FoT.

**Material Offer Summary**

Display only:

- Tenderer
- Tender title and reference
- Procuring Entity
- Offer type
- Selected lots, where applicable
- Total tender price by currency
- Discounts: None or declared
- Tender validity period

Place source actions beside the values they control:

- Tenderer and signatory → Edit in CBQ
- Offer and selected lots → Edit in Lots & Alternatives
- Price and discounts → Edit in Price Schedule

Do not show:

- Business addresses
- Directors or ownership details
- Technical responses
- Qualification evidence
- Uploaded documents
- Price line items
- Internal metadata

**6\. Handle base and alternative offers**

Use the offer records already produced by Lots & Alternatives.

- If there are no alternatives, render one FoT for the base offer.
- If alternatives exist, render one FoT instance for the base offer and one for each confirmed alternative.
- Use a compact offer selector.
- Show the alternative identifier and applicable lots for an alternative FoT.
- Never ask the bidder to select or rename the offer inside the FoT.
- The checklist section is complete only when every required FoT instance is certified.

Do not create new alternative-tender architecture.

**7\. Implement the commissions disclosure**

Ask:

Have any commissions, gratuities or fees been paid or are to be paid to agents or any other party relating to this Tender?

Do not preselect Yes or No.

If No:

None declared.

If Yes, require at least one complete repeatable row:

- Recipient's complete name
- Full address
- Reason for payment
- Amount
- Currency

Support Add recipient and Remove.

Allow this disclosure to be saved while the FoT is otherwise not ready.

**8\. Implement legal terms presentation**

Add:

Read full Form of Tender terms

Open the approved right-hand drawer.

Render the exact configured IT STD FoT clauses.

Requirements:

- Preserve legal wording.
- Preserve clause letters and headings.
- Insert the appropriate configured or derived values.
- Do not paraphrase.
- Do not make clauses editable.
- Do not render the source PDF.
- Do not show technical template metadata.

Implement the IT STD FoT template required for this task. Do not build a generic legal-form authoring engine.

**9\. Implement authorized signatory display**

Display read-only from CBQ:

- Full name
- Title/designation
- Authority to bind: Confirmed
- Edit in CBQ

Do not ask the bidder to re-enter signatory details in the FoT.

Use the existing authorized submitter/signatory permission rules. Do not introduce a new permissions subsystem.

**10\. Implement certification**

Enable:

Certify Form of Tender

only when the current FoT instance is ready.

Open the approved confirmation dialog:

By certifying, you confirm that the material terms shown are correct, that you accept the complete Form of Tender terms, and that you are authorized to bind the Tenderer.

Show:

- Tenderer
- Tender reference
- Offer type
- Total price by currency
- Authorized signatory

Actions:

- Cancel
- Certify Form of Tender

Do not request another password, typed signature, stamp or uploaded signature.

**11\. Store the legal record**

At certification, atomically store:

- Material offer values shown to the bidder
- Exact rendered FoT legal text
- Commissions disclosure and rows
- Authorized signatory name and title
- Certifying user
- Certification date/time
- Offer identity: base or alternative
- Certification status

Keep this implementation simple.

Do not introduce content-addressing, digest orchestration or publication pipelines.

**12\. Invalidate certification on changes**

If any FoT source value changes after certification:

- Withdraw the current FoT certification
- Set the FoT status to Requires recertification
- Preserve the previous certification in audit history
- Require the bidder to review and certify again

For simplicity, invalidate all FoT instances for the bid when any relevant source section changes. Do not build field-level dependency tracking.

Relevant sources include:

- CBQ
- Lots & Alternatives
- Price Schedule
- Tender/addenda acknowledgement
- Statutory Declarations
- FoT commissions disclosure

**13\. Certified state**

After certification show:

Form of Tender certified

Display:

- Tenderer
- Offer type
- Authorized signatory
- Title/designation
- Certification date/time

Show:

If information used by this Form of Tender changes, certification will be withdrawn and the form must be certified again.

Primary action:

Return to Checklist

Do not expose internal audit identifiers.

**14\. Validation and tests**

Add tests for:

- FoT appears after Price Schedule.
- Derived values come from their owning sections.
- FoT contains no duplicate legal-name, address, price, discount or signatory inputs.
- Commissions Yes/No has no default.
- Yes requires at least one complete payment row.
- No records "None declared".
- Certification is blocked when a prerequisite is incomplete.
- Missing prerequisites link to the correct source sections.
- Certification is blocked for an unauthorized user.
- Certification stores the rendered legal record and certification event.
- A relevant source change invalidates certification.
- No relevant change leaves certification intact.
- Base and alternative FoTs use the correct offer data.
- The checklist completes only when all required FoT instances are certified.
- No NSSF-specific values are hard-coded.
- No technical identifiers appear in the bidder UI.

Run the relevant existing test suite plus the new FoT tests.

**15\. Completion report**

Implement the feature; do not stop after producing a plan.

When complete, provide a focused report containing:

- Files changed
- Data-model changes
- Checklist-order changes
- Source-data gaps corrected
- FoT states implemented
- Certification and invalidation behaviour
- Tests added and results
- Any deviation from this prompt and why

Stop after completing the Form of Tender implementation.