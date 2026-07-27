Preliminary Requirements and Evidence

**Purpose**

This section collects tender-specific preliminary evidence required by Section III, item 3 of the configured STD.

The canonical IT STD does not prescribe a fixed preliminary checklist. The Procuring Entity defines the criteria when preparing the tender.

Therefore:

- Render the published criteria dynamically.
- Do not hard-code the NSSF preliminary checklist.
- Treat NSSF as test data only.
- Do not automatically infer or reclassify criteria at runtime.
- Template preparation may classify each criterion manually.

This section records whether the bidder has supplied the required response. It does not determine whether the tender passes preliminary examination.

**Design source**

Use the latest Stitch design for "Preliminary Requirements and Evidence", including the final state corrections.

Implement only the core screen and response drawer. Reuse the existing KenTender workspace shell and components.

Do not expose:

- STD page numbers.
- PDF references.
- Requirement IDs.
- Schema names.
- Hashes or versions.
- Evaluator fields.
- Passed, Failed, Approved or Compliant statuses.

**Step 1 - Inspect the repository**

Before changing code, locate:

- Published tender-section configuration.
- Existing requirement and evidence models.
- Bidder document-upload storage.
- Any reusable bidder evidence or organisation-document records.
- Form of Tender, Statutory Declarations and Tender Security completion states.
- Checklist status and blocker calculation.
- Existing drawer and table components.

Reuse existing patterns. Do not create a parallel requirements engine, rules engine, evidence vault or publication architecture.

If the existing data can be simplified safely, development fixture data may be reset.

**Step 2 - Preliminary-requirement configuration**

Each published preliminary criterion needs only enough configuration to render and validate the bidder task.

Support:

- Display title.
- Exact evidence or response instruction.
- Required or conditional applicability.
- Configured response method.
- Optional validity rule.
- Optional accepted file types and size limit.
- Optional linked bidder-workspace section.
- Display order.

Supported response methods:

- Upload evidence.
- Select saved evidence or upload new evidence.
- Enter a verification reference.
- Provide a configured structured response.
- Satisfied through another bidder-workspace section.

Do not show every response method for every requirement. Render only the method configured for that criterion.

Do not build a generic expression language for applicability. Reuse the repository's existing condition mechanism or implement simple explicit conditions such as:

- Single bidder or Joint Venture.
- Local or foreign bidder.
- Selected lot.
- Selected alternative.
- Bidder entity type.

**Step 3 - Prevent duplication**

A preliminary criterion may depend on work completed elsewhere.

Examples include:

- Form of Tender.
- Statutory Declarations.
- Tender Security or Tender-Securing Declaration.
- Confidential Business Questionnaire.

When a criterion is mapped to another section:

- Do not collect another upload or declaration.
- Derive its status from the source section.
- Show the source section.
- Provide Start, Continue or Review according to the source section's state.
- Navigate the bidder to that section.
- Update the preliminary-requirement status when the source section changes.

Only display a linked criterion when the published preliminary configuration includes it. Do not add these examples automatically to every tender.

Qualification, experience, personnel, financial capacity and technical-compliance responses remain in their respective later sections unless the published tender explicitly classifies them as preliminary criteria.

**Step 4 - Main screen**

Implement the approved two-group layout.

Header:

- Title: "Preliminary Requirements and Evidence".
- Description: "Provide the documents and information required for preliminary examination."
- Progress: "X of Y requirements complete".

Group 1: "Evidence to provide"

Columns:

- Requirement.
- Evidence required.
- Status.
- Action.

Group 2: "Requirements handled in other sections"

Columns:

- Requirement.
- Source section.
- Status.
- Action.

Use exact tender-configured requirement titles and evidence instructions. Do not paraphrase them in application code.

Supported statuses:

- Not started.
- In progress.
- Complete.
- Needs attention.
- Not applicable.

Actions:

- Start.
- Continue.
- Replace.
- Review.
- No action for Not applicable.

Progress rules:

- Count only applicable requirements.
- Count a requirement as complete only when its response is complete.
- Include linked requirements in the same total.
- Exclude Not applicable requirements.
- Recalculate immediately after a response or linked-section status changes.

Show:

"All preliminary requirements have responses. Responsiveness is determined after tender opening."

Only show this message when every applicable requirement is Complete.

Do not show it when anything is Not started, In progress or Needs attention.

The main-page action is "Continue", not "Save & Continue". Responses are saved in their drawers.

Continuing with incomplete requirements may navigate away, but the section must remain incomplete and block final tender submission.

**Step 5 - Response drawer**

Open the selected requirement in a right-hand drawer.

Drawer header:

- Requirement title.
- Required or Conditional label.
- Exact configured requirement instruction.
- Current response status.
- Close action.

Drawer body must render only the configured response method.

Drawer footer:

- Cancel.
- Save response.

Do not preselect a response method, saved document or answer.

Disable "Save response" until a valid response has been explicitly selected or entered.

**Saved evidence**

When reusable evidence is allowed:

- List only evidence belonging to the bidder organisation.
- Show a user-readable document name.
- Show configured metadata such as certificate number, issuer and expiry date.
- Require explicit selection.
- Never select a document automatically.
- Evaluate its eligibility against the current tender's configured validity rule.
- Label expired or otherwise ineligible evidence clearly.
- Do not allow ineligible evidence to complete the requirement.

If reusable bidder evidence does not yet exist, add the smallest repository-aligned record required to store:

- Bidder organisation.
- Evidence type.
- Document.
- User-readable name.
- Configured metadata.
- Issue and expiry dates where applicable.

Do not create a separate document-management subsystem.

**Upload evidence**

When upload is permitted:

- Show only configured formats and size limits.
- Do not hard-code PDF or 10 MB.
- Do not use paper-oriented "scanned copy" wording unless it appears in the configured tender instruction.
- Allow the bidder to replace or remove an upload before final submission.
- Collect document metadata only when configured for that criterion.

**Verification reference**

When verification is configured:

- Render only the configured reference fields.
- Validate all required reference fields.
- Do not claim that the evidence has been independently verified unless an actual integration has verified it.

**Structured response**

Render only the configured fields.

Do not turn every evidence criterion into a generic Yes/No declaration.

**Step 6 - Validity rules**

Validity must come from the criterion configuration.

Examples may include:

- Valid on the tender submission deadline.
- Valid through the tender opening date.
- Issued within a configured number of months.
- No expiry requirement.

Do not assume one global validity rule.

Display the exact relevant date or rule in the drawer.

When evidence fails the configured rule:

- Status: Needs attention.
- Show a plain-language issue.
- Action: Replace.
- Do not count it as complete.

Ensure the row, drawer and progress summary always show the same status.

**Step 7 - Applicability**

Evaluate configured applicability from current bidder and tender data.

Example:

- A JV agreement criterion is Not applicable to a single bidder.
- The same criterion becomes required for a JV bidder when configured.

When a criterion changes to Not applicable:

- Exclude it from progress.
- Preserve any previously supplied response internally if necessary, but do not count or display it as active.
- Do not delete bidder evidence automatically.

When it becomes applicable again, restore its appropriate response status.

**Step 8 - Status calculation**

Calculate status consistently on the server.

- Not started: no response.
- In progress: some response data exists but required content is missing.
- Complete: all configured response requirements are satisfied.
- Needs attention: evidence exists but violates a validity rule, is missing its stored file, or has otherwise become unusable.
- Not applicable: applicability condition is false.

"Complete" means only submission completeness. It is not an evaluation result.

After final tender submission:

- Lock responses.
- Allow read-only review.
- Do not allow replacement or removal.

**Step 9 - Checklist integration**

The main bidder checklist must derive this section's status from all applicable preliminary requirements.

- Not started when no direct or linked requirement has progress.
- In progress when at least one response exists but blockers remain.
- Needs attention when any applicable requirement needs attention.
- Complete only when every applicable requirement is complete.
- Locked after final tender submission.

Final tender submission must be blocked when any applicable preliminary requirement is not complete.

Return specific, user-readable blocker messages identifying the requirement needing action.

**Step 10 - Permissions and security**

- Only authorised members of the bidder organisation may edit its draft responses.
- Prevent access to another bidder's saved evidence or uploads.
- Validate uploaded content using the application's existing upload controls.
- Validate all configured requirements server-side.
- Do not rely on hidden or disabled client controls for enforcement.

**Step 11 - Tests**

Add focused tests for:

- Dynamic criteria rendering.
- No NSSF-specific hard-coding.
- Exact configured requirement text.
- Each supported response method.
- Explicit saved-evidence selection.
- No magical defaults.
- Expired saved evidence.
- Configured validity dates.
- Configured file formats and limits.
- Upload replacement and removal.
- Linked-section status derivation.
- Start, Continue and Review actions.
- Single bidder and JV applicability.
- Not applicable exclusion from progress.
- Correct progress totals.
- Consistent row and drawer statuses.
- Completion message visibility.
- Checklist blocker calculation.
- Final-submission blocking.
- Read-only state after final submission.
- Bidder-organisation evidence isolation.
- Absence of evaluator outcomes and technical metadata from the UI.

Include a regression test for this exact inconsistent state:

- Tax Compliance row is Needs attention.
- The drawer must also show Needs attention.
- An expired saved certificate must show Expired.
- It must not be preselected.
- It must not complete the requirement.
- The completion message must remain hidden.

**Deliverable**

Implement only Preliminary Requirements and Evidence and its checklist integration.

Run the relevant tests and report:

- Files changed.
- Minimal model or configuration changes.
- Routes or endpoints changed.
- Tests added and results.
- Any unresolved repository blocker.

Do not implement preliminary evaluation, evaluator decisions, template-authoring screens or qualification requirements in this task.