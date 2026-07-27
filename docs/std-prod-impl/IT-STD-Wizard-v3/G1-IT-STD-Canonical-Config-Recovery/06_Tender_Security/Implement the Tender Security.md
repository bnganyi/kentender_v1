Implement the Tender Security bidder-workspace section

**Objective**

Provide one simple electronic task generated from the published tender configuration.

A tender may require exactly one of:

- Tender Security instrument.
- Tender-Securing Declaration.
- Neither.

Never require both. NSSF is test data only; derive the screen from the applicable STD/TDS configuration.

Use the official IT STD as the legal source:

- ITT 22.
- Section IV Tender Security forms.
- Tender-Securing Declaration Form under Regulations 46 and 155(2).

Do not create a template compiler, manifest pipeline, digest workflow or template-authoring interface. Templates may be prepared manually. Use the simplest structures already present in the repository.

**Design sources**

- Use the latest approved Tender Security Stitch screen as the visual reference.
- Use the Tender-Securing Declaration Stitch screen as a visual starting point only.
- Apply the legal corrections below before implementing it.
- Reuse the application's existing workspace shell. Do not copy Stitch navigation or toolbars.
- Do not expose hashes, schema names, internal IDs, versions or technical metadata.

**Step 1 - Inspect the existing implementation**

Before changing code:

- Locate the current checklist section configuration.
- Locate bidder-section routing and persistence.
- Locate file-upload handling.
- Locate the tender-wide authorised-signatory source used by the Form of Tender.
- Locate checklist completion and blocker calculation.
- Reuse existing patterns and components.
- Do not introduce a parallel architecture.

**Step 2 - Resolve the configured mode**

Implement a simple published requirement with these modes:

- tender_security
- tender_securing_declaration
- none

Checklist behaviour:

- tender_security: label the section "Tender Security".
- tender_securing_declaration: label it "Tender-Securing Declaration".
- none: do not create a bidder task. If the existing checklist requires the row, show "Not applicable".
- Never display both security tasks.

The requirement and all legal text must come from the published tender configuration, not hard-coded NSSF data.

**Step 3 - Tender Security instrument screen**

Display read-only tender requirements:

- Required amount and currency.
- Required validity date.
- Permitted instrument types.
- Beneficiary.
- Required applicant name.
- Exact configured issuer-eligibility conditions.
- Tender-level or lot-specific coverage, when applicable.
- Permitted electronic submission routes.

The applicant name must come from the tenderer identity:

- Single bidder: registered legal name.
- Constituted JV: JV legal name.
- Intended JV: all future members named in the letter of intent.

Bidder-entered instrument details:

- Instrument type.
- Instrument or guarantee number.
- Issuing institution's legal name.
- Issuer registered address.
- Issuer country.
- Issue date.
- Expiry date.
- Guaranteed amount.
- Currency.
- Electronic submission route.

Do not default country, instrument type or submission route.

Currency behaviour:

- One permitted currency: show it read-only.
- Multiple permitted currencies: require a selection from the configured list only.

Instrument types must come from the tender configuration. Do not hard-code only bank guarantee and insurance bond.

**Electronic submission routes**

Render only routes permitted by the tender.

**Upload electronic guarantee**

- Require the issuer-issued electronic guarantee.
- Show only configured formats and size limits.
- Do not describe a scanned paper document as an electronic original.
- Do not invent PDF, signature-file or size restrictions.

**Use issuer-hosted guarantee**

- If a registry or platform is configured, display it read-only.
- Otherwise require the configured verification location or URL.
- Require the guarantee reference number.
- The reference must identify the actual guarantee and its complete terms.

Do not ask for the issuing institution twice.

**Foreign non-bank issuer condition**

When the issuer is a non-bank financial institution outside Kenya:

- Require the Kenyan correspondent financial institution details; or
- Require the configured evidence/reference showing that the Procuring Entity waived this requirement before tender submission.

Do not show these fields in other cases.

**Instrument validation**

Validate server-side:

- Instrument type is permitted.
- Amount meets the configured requirement.
- Currency is permitted.
- Expiry is on or after the required security-validity date.
- Issue date is valid.
- Issuer is not the tenderer.
- Required electronic evidence or hosted-guarantee reference is present.
- Foreign non-bank correspondent or waiver requirements are satisfied.
- Required lot coverage is complete.

Completion means only that required information and evidence are present. It does not mean that the instrument is legally responsive, verified or approved.

Use these states:

- Not started.
- In progress.
- Needs attention.
- Complete.
- Locked after final tender submission.

Do not show "Verified", "Approved" or "Responsive" in the bidder workspace.

**Step 4 - Tender-Securing Declaration screen**

The declaration is an electronic execution of the configured STD form. It is not a questionnaire and should require almost no manual data entry.

Display:

- Tenderer identity.
- Procuring Entity.
- Tender title and reference.
- Tender validity period calculated from the submission deadline.
- Exact tender-validity end date.
- Configured suspension period.
- Configured suspension commencement date.
- Exact declaration-expiry conditions.
- Link or action to read the complete configured declaration.

Use only the official triggering events:

- Withdrawal during tender validity.
- Failure or refusal to execute the contract when required.
- Failure or refusal to furnish the performance security.

Do not include JV-name changes as a suspension trigger.

Remove:

- "Compliant with Section 51".
- Any unsupported compliance claim.
- References to an "Electronic Transactions Act" unless approved legal copy explicitly supplies that wording.
- "Edit in CBQ".
- Automatic claims that authority to bind has been confirmed.

Status before execution must be "Not certified".

**Authorised signatory**

Use the tender-wide authorised signatory already used by the Form of Tender.

Do not create a declaration-specific signatory or treat CBQ certification as proof of authority.

If the current code stores the signatory only inside CBQ, extract it into the simplest submission-level source and let FoT, CBQ and this declaration reuse it.

Display:

- Full name.
- Capacity/title.
- "Change signatory".
- Authorisation status based on actual supporting evidence.

Do not expose technical identity data.

**Electronic certification**

The primary action is "Certify declaration".

It must open one final confirmation dialog showing:

- Tenderer name.
- Declaration being certified.
- Signatory name and capacity.
- Plain statement that certification records the person's identity, authority, date and time as part of the tender submission.
- Cancel.
- Certify declaration.

Do not add another checkbox or multiple confirmation steps.

On confirmation:

- Store the certifier, capacity, authenticated user, certification timestamp and exact declaration content/configuration used.
- Keep audit metadata internal.
- Show a legally clear confirmation panel containing the certifier's name, capacity and certification date/time.
- Never show hashes or internal IDs.

System-populate workflow dates. Do not ask the bidder to type signing or submission dates. Preserve the certification timestamp and populate the final tender-submission date in the sealed submission record.

If the tenderer identity, signatory, legal text or configured declaration values change, set the declaration to "Needs recertification".

After final tender submission, lock the declaration.

**Step 5 - Full declaration text**

The "Read full declaration" action must display the complete configured legal text in an accessible application view.

- Do not replace the legal text with the summary.
- Do not require the bidder to download or edit a paper form.
- Do not expose template placeholders.
- Populate the legal text from tender and submission data.
- Preserve the canonical STD wording unless the published tender configuration contains an authorised variation.

**Step 6 - Checklist integration**

The checklist row must reflect the selected mode and actual section state.

Block final submission when:

- A required instrument section is incomplete.
- Instrument validation has blockers.
- A required declaration has not been certified.
- A certified declaration needs recertification.

Checklist completion must update immediately after saving or certification.

**Step 7 - Tests**

Add focused tests covering:

- Each requirement mode.
- Mutual exclusivity of instrument and declaration.
- No task when mode is none.
- Dynamic instrument types and currencies.
- No magical defaults.
- Upload and issuer-hosted routes.
- Foreign non-bank correspondent requirement and waiver.
- Amount, currency and expiry validation.
- Tender-level and lot-specific coverage.
- Single bidder, constituted JV and intended JV identity.
- Exact three declaration triggers.
- Declaration expiry terms.
- Tender validity calculated from the submission deadline.
- Tender-wide signatory reuse.
- Certification confirmation.
- Recertification after material changes.
- Checklist blockers and completion.
- Locking after final submission.
- Absence of hashes, technical IDs and unsupported compliance claims from bidder-facing pages.

**Deliverable**

Implement only this section and its checklist integration.

Run the relevant tests and provide a short report containing:

- Files changed.
- Data-model changes.
- Routes or endpoints changed.
- Tests added and results.
- Any remaining blocker grounded in the official IT STD or existing repository constraints.

Do not implement evaluator review, procurement-officer approval or template-authoring screens in this task.