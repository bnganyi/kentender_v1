**Implement Requirements Compliance**

Implement the bidder-facing **Requirements Compliance** section.

Keep the implementation simple and complete. Work only on this section, its checklist roll-up and its submission-readiness effect. Do not create an evaluation subsystem, generic rules engine or new document-management framework.

**1\. Objective**

Digitize the item-by-item commentary required by ITT 18.2(c) of the canonical Information Technology STD.

For every applicable published requirement, the bidder must provide the configured response and supporting evidence.

The system must:

- Render requirements from the published tender configuration.
- Support different response types.
- Group large requirement sets.
- Save bidder responses electronically.
- Link reusable evidence.
- Derive progress, issues and completion.
- Handle requirements changed by addenda.
- Block submission when applicable required responses are incomplete.

The bidder supplies facts, explanations and evidence. The system does not determine technical responsiveness.

NSSF is test data only. Do not hard-code NSSF requirement groups, references, counts, response types or evidence rules.

**2\. Module boundaries**

Requirements Compliance answers:

What is the bidder offering in response to this specific published requirement?

Do not duplicate:

- Overall methodology or implementation approach from Technical Proposal and Implementation Plan.
- Qualification evidence.
- Personnel profiles.
- Delivery-partner records.
- Prices.
- Evaluator comments, scores or decisions.
- Final bid certification.

Requirements may reference records owned by other sections, but must not copy them.

**3\. Inspect before changing**

Identify the existing:

- Published tender requirement model.
- Bidder-submission persistence.
- Evidence records.
- Conditional-field mechanism.
- Lot selection.
- Addendum handling.
- Draft-save pattern.
- Section checklist derivation.
- Submission-readiness validation.
- Approved Stitch designs under docs/bidder-workspace/.

Reuse existing repository conventions.

Do not introduce:

- A second requirement model.
- A second evidence repository.
- A generic expression engine.
- A technical-evaluation model.
- Manually editable completion statuses.

Development data may be reset if necessary. Do not add production migration complexity.

**4\. Published requirement configuration**

The published tender configuration is authoritative.

Each requirement must provide:

- Stable internal requirement key.
- Tender-facing reference, where configured.
- Requirement group.
- Display order.
- Exact published requirement statement.
- Requirement mode.
- Response renderer.
- Required response fields.
- Explanation requirement.
- Evidence requirement.
- Tender or lot scope.
- Named applicability condition where conditional.
- Whether a technical alternative is permitted.
- Current published revision.
- Bidder-facing change summary when amended.

Do not show the internal key or revision identifier to bidders.

Use these requirement modes:

- required
- optional
- conditional
- informational
- excluded

Rules:

- required: display and block completion until the configured response is complete.
- optional: display with an Optional label and never block completion.
- conditional: evaluate its configured named condition.
- informational: display for context but require no response.
- excluded: do not display or validate.
- A conditional requirement whose condition is false is Not applicable.
- An active conditional requirement follows its configured required or optional behaviour.
- An enabled requirement without a supported response renderer is a tender-publication configuration error.
- Do not infer requirement mode from words such as "must" or "should" at bidder runtime.
- Do not build a general-purpose rules language. Reuse existing named conditions or add only the explicit named conditions required by current tender templates.

**5\. Supported response renderers**

Support the following configured response types:

- Acknowledgement.
- Yes or No choice.
- Controlled single choice.
- Controlled multiple choice.
- Number.
- Percentage.
- Date.
- Period or duration.
- Short text.
- Narrative explanation.
- Structured repeating table.
- Evidence reference.
- Combined structured response, explanation and evidence.

Renderer rules:

- Render only the fields configured for the requirement.
- Do not prefill a bidder decision.
- Preserve zero and false as valid responses.
- Validate configured units, limits and formats.
- A professional-service requirement must not be reduced to a bare Yes where an explanation is required.
- Supporting evidence must not replace a required structured or narrative response.
- Do not require PDF page-number references.

**6\. Grouped requirements workspace**

Implement the approved **Requirements Compliance** workspace.

Header:

- Title: Requirements Compliance
- Description: Respond to each applicable requirement and provide the requested supporting evidence.

Show:

- Required-response progress.
- Configured requirement groups.
- Progress for each group.
- Selected group's requirements.

The progress label must say:

- {completed required responses} of {applicable required responses} required responses complete

Do not say "requirements met."

Use a compact table with:

- Tender-facing reference.
- Requirement.
- Requirement mode.
- Response summary.
- Status.
- Action.

Actions:

- Start.
- Continue.
- Review.
- Resolve.

Group names, references, counts and order must come from the published tender.

Provide requirement search within the current section. Do not expose advanced internal filters or technical metadata.

**7\. Requirement response drawer**

Open one requirement in a right-hand drawer.

Show:

- Tender-facing reference.
- Required, Optional, Conditional or Informational.
- Current status.
- Exact requirement statement.
- Configured response controls.
- Explanation where configured.
- Linked evidence.
- Add evidence.
- Use existing evidence.
- Previous.
- Save response.
- Save and next.
- Close.

Evidence must be displayed using readable names.

Provide:

- View.
- Replace.
- Remove.

Do not display:

- Storage paths.
- File hashes.
- Database IDs.
- Schema keys.
- MIME internals.
- PDF page fields.

Saving one response must not submit or complete the entire section.

**8\. Response summaries**

Generate plain-language response summaries for the group table.

Examples:

- 500 concurrent users
- Explanation provided
- 3 schedule rows completed
- Response and evidence provided
- No response
- Review required after addendum

Do not use:

- Compliant.
- Non-compliant.
- Meets requirement.
- Passed.
- Failed.
- Technically responsive.

**9\. Evidence behaviour**

Reuse the existing evidence repository.

Support:

- Selecting existing evidence owned by the bidder.
- Adding new evidence.
- Linking one evidence item to multiple requirements where permitted.
- Viewing linked evidence.
- Replacing or removing a link before submission.
- Configured evidence validity or expiry checks.

Do not duplicate the underlying file when it is reused.

Evidence selection means that the bidder has completed the configured submission requirement. It does not mean the evidence has passed evaluation.

**10\. Status derivation**

Use only:

- Not started
- In progress
- Complete
- Needs attention
- Not applicable

Derive status from configuration, saved responses, evidence and validation.

Rules:

- Not applicable: a conditional requirement is inactive.
- Not started: the requirement applies but no bidder response is saved.
- In progress: some response exists but required content remains incomplete.
- Needs attention: the response is invalid, contradictory, affected by an addendum, has invalid evidence or contains an incomplete attempted record.
- Complete: every configured required response field and evidence item is present and valid.

Do not persist a manually editable status.

"Complete" means submission completeness only. It is not an evaluation decision.

**11\. Group and section completion**

For each requirement group, derive:

- Applicable required count.
- Completed required count.
- Needs-attention count.
- Not-started count.
- Group status.

For the overall section:

- Needs attention if any applicable required requirement needs attention.
- In progress if at least one applicable required response has started and required work remains.
- Not started if no applicable required response has started.
- Complete only when every applicable required response is complete.
- Not applicable only when the published tender contains no applicable requirements.

Optional requirements do not block group or section completion.

Informational requirements do not count in progress.

The bidder checklist must link directly to the requirement or group requiring action.

**12\. Review screen**

Implement **Review Requirements Compliance**.

Show summary counts:

- Required responses.
- Complete.
- In progress.
- Needs attention.
- Not started.

Show group summaries with:

- Group.
- Required responses.
- Complete.
- Issues.
- Status.
- Action.

Show an actionable list of unresolved requirements:

- Reference.
- Requirement summary.
- Issue.
- Group.
- Resolve action.

Issue examples:

- Required explanation is missing.
- Supporting evidence has not been added.
- Required table contains an incomplete row.
- Response must be reviewed after Addendum 2.
- This conditional requirement is now applicable.

Provide:

- Back.
- Save draft.
- Complete section.

Complete section must remain disabled while any applicable required response is incomplete or needs attention.

Completing the section must not submit or seal the bid.

**13\. Addendum handling**

When an addendum changes a published requirement:

- Preserve the previous requirement statement and bidder response for history.
- Present the current requirement statement as authoritative.
- Mark the current response Needs attention.
- Show Updated by Addendum {number}.
- Show the configured bidder-facing change summary.
- Require the bidder to review and resave the response.
- Retain compatible response content where safe.
- Revalidate configured fields and evidence.
- Do not silently mark the amended response complete.

If a new required requirement is introduced:

- Add it to the correct group.
- Set it to Not started.
- Include it in required progress.

If a requirement is withdrawn:

- Remove it from active required progress.
- Preserve the prior response for history.
- Do not require bidder action.

Do not expose internal version hashes or technical revision IDs.

**14\. Lot scope**

Respect configured requirement scope.

- Tender-level requirements are answered once.
- Lot-level requirements apply only to lots selected by the bidder.
- A shared response may be reused across lots only where configuration permits it.
- Progress must count only requirements applicable to selected lots.
- Issues must name the affected lot in plain language.
- Responses must not leak between tenders, bidders, submissions or lots.

**15\. Technical alternatives**

If a requirement permits a technical alternative:

- The base requirement response remains mandatory.
- Allow the bidder to link a configured Technical Alternative record.
- Do not overwrite the base response.
- Do not collect alternative prices here.
- Reference the owning alternative Price Schedule where applicable.

If alternatives are prohibited, do not show alternative controls.

**16\. Validation**

Validate on the server.

At minimum validate:

- Requirement applicability.
- Required response fields.
- Controlled-option membership.
- Numeric and percentage limits.
- Date and period rules.
- Required narrative responses.
- Required repeating-record minimums.
- Incomplete repeating rows.
- Required evidence.
- Evidence ownership and accessibility.
- Configured evidence validity.
- Lot scope.
- Conditional activation.
- Addendum review requirement.
- Technical-alternative permission.

Client-side validation is supplementary.

Return plain-language field and requirement issues.

**17\. UI rules**

Use the approved Stitch designs as visual references.

Implement their content and interaction behaviour; do not copy prototype defects or hard-coded examples.

Requirements:

- Use the existing bidder-workspace shell.
- Keep the interface focused on completing requirements.
- Use group navigation for large tenders.
- Use a right-hand drawer for one response.
- Preserve drafts.
- Support Save and next.
- Keep responses editable until final bid submission.

Do not show:

- Evaluator scores.
- Evaluator comments.
- Pass/fail outcomes.
- "Requirements met."
- Internal IDs.
- Hashes.
- Audit logs.
- Package artifacts.
- PDF page instructions.
- A requirement to upload a single compliance-matrix document.

**18\. Implementation order**

- Inspect and document existing reusable models, routes and components.
- Add only the missing requirement-configuration fields.
- Implement applicability and lot scoping.
- Implement the configured response renderers.
- Implement response and evidence persistence.
- Implement server-side validation.
- Implement status and progress derivation.
- Implement grouped workspace and response drawer.
- Implement the review screen.
- Implement addendum impact handling.
- Roll section state into checklist and submission readiness.
- Add fixtures and tests.
- Produce the implementation report.

Do not perform unrelated refactoring.

**19\. Development fixtures**

Create three generic fixtures:

**Standard IT requirements**

- Multiple requirement groups.
- Required, optional and informational requirements.
- Numeric, narrative, table and evidence responses.

**Conditional and lot-scoped requirements**

- Two lots.
- Conditional requirements.
- One shared response.
- One lot-specific response.
- Technical alternatives permitted for one system part.

**Amended requirements**

- One unchanged requirement.
- One changed requirement.
- One newly introduced requirement.
- One withdrawn requirement.
- Existing bidder responses demonstrating each addendum state.

Do not use NSSF as the canonical fixture.

**20\. Required tests**

Prove that:

- Requirement groups and rows come from published configuration.
- Required, optional, conditional, informational and excluded modes behave correctly.
- Only applicable required responses count in progress.
- Every supported response renderer saves and reloads correctly.
- False and zero values are preserved.
- Missing required explanations block completion.
- Missing required evidence blocks completion.
- Existing evidence is reused without copying the file.
- Completion does not produce an evaluator outcome.
- Professional-service requirements can require narrative explanations.
- Lot-scoped requirements affect only selected lots.
- Conditional requirements enter and leave applicability correctly.
- Base responses remain separate from technical alternatives.
- Changed addendum requirements become Needs attention.
- New addendum requirements become Not started.
- Withdrawn requirements stop affecting progress.
- Previous responses remain available for history.
- Completing this section does not submit or seal the bid.
- No UI or API response exposes internal IDs, hashes or evaluator scores.
- Two tenders based on the same STD can publish different requirement groups and response types.
- The renderer works without NSSF-specific data.

**21\. Completion report**

Create:

docs/bidder-workspace/REQUIREMENTS_COMPLIANCE_IMPLEMENTATION_REPORT.md

Include:

- Existing components reused.
- Files changed.
- Configuration fields added.
- Supported requirement modes.
- Supported response renderers.
- Applicability and lot rules.
- Evidence behaviour.
- Status derivation.
- Addendum handling.
- Routes and screens implemented.
- Fixtures created.
- Tests and results.
- Explicitly deferred edge cases.

Stop after Requirements Compliance is implemented, tested and documented.