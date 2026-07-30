**Implement Review, Validation and Final Submission workflow**.

**1\. Objective**

Provide a simple path from a completed bidder checklist to a formally submitted electronic bid:

- Checklist
- Review & Validate
- Final Bid Review
- Submit Bid
- Submission Receipt

This is a workflow, not another tender-response section.

Do not add "Final Review," "Final Declaration" or "Submission" as rows inside the section checklist.

**2\. Entry points and action placement**

**2.1 Primary workflow entry point**

The primary entry point is the existing **Bidder Workspace Checklist**.

Place a primary action directly below the section checklist:

Review & Validate Bid

This button becomes active when all applicable required sections are complete.

Do not place this action inside an individual section row.

When activated, it opens the Review & Validate screen.

**2.2 Sidebar entry point**

Enable the existing Review & Validate sidebar item at the same time.

The checklist button is the primary next-step action. The sidebar item is secondary navigation to the same screen.

Do not create competing entry points in the page header or tender overview.

**2.3 Final Bid Review entry point**

The entry point to **Final Bid Review** is the primary footer action on the Review & Validate screen:

Review Final Bid

Enable it only when validation returns no blocking issues.

Do not add Final Bid Review to the section checklist.

**2.4 Submission entry point**

The primary footer action on Final Bid Review is:

Continue to Submit Bid

This opens the Submit Bid screen.

Enable the existing Submit & Seal sidebar item only when the bid has passed validation and is ready to submit.

The visible screen and button labels should use plain language such as Submit Bid. Technical sealing remains a system operation.

**3\. Implementation principles**

- Reuse existing bidder-workspace layout, section status, permissions and submission models.
- Do not create another manifest compiler, workflow engine or parallel readiness system.
- The configured tender sections are authoritative.
- Validate only applicable sections.
- Omit configuration-excluded sections.
- NSSF remains a fixture only.
- Final review must read current responses directly. Do not create editable copies.
- Submission must use server-side validation and server time.
- Do not display internal IDs, hashes, schema names, package versions or encryption details.
- Do not show evaluation outcomes or scores.

**4\. Readiness service**

Implement or extend one server-side readiness service for the bidder submission.

It must return:

- Overall readiness
- Applicable section statuses
- Blocking issues
- Affected section or response
- User-facing issue message
- Route for resolving the issue
- Current Form of Tender totals
- Current Price Schedule totals by currency
- Addenda acknowledgement status
- Submission permission status
- Deadline status

Do not maintain a separate manually editable readiness flag.

Derived overall states:

- In progress
- Needs attention
- Ready to submit
- Submitted

The service must use the same section-completion and validation rules already used by each bidder module.

**5\. Review & Validate screen**

Implement the approved Review & Validate screen.

Header:

- Title: Review & Validate
- Description: Check that every required section is complete before submitting your bid.
- Overall readiness status
- Blocking-issue count

Show blocking issues first.

Each issue must include:

- Clear user-facing message
- Affected section or item
- Resolve action linking directly to the problem

Examples:

- Form of Tender requires review after Price Schedule changes.
- Country of origin is missing for Price Schedule item 1.4.
- One required declaration is incomplete.

Below the issues, show a section table with:

- Section
- Status
- Issues
- Last updated
- Action

Use only:

- Complete
- Needs attention
- Not applicable

Actions:

- Review
- Resolve

Footer actions:

- Back to Checklist
- Validate again
- Review Final Bid

Disable Review Final Bid while blocking issues remain.

Validate again must rerun the server-side readiness service. It must not rely only on browser state.

**6\. Validation coverage**

At minimum, validate:

- Every applicable required section is complete
- Conditional requirements are evaluated correctly
- Required electronic declarations are complete
- Required tender-specific evidence is present
- Addenda requiring acknowledgement are acknowledged
- Tender Security is complete when required
- Price Schedule has no blocking issues
- Price totals remain separated by currency
- Form of Tender reflects the current Price Schedule totals
- Any section invalidated by a downstream change has been reviewed again
- The submission deadline has not passed

Do not require document uploads for requirements fulfilled by dedicated electronic sections.

Do not duplicate validation logic. Call existing module validators and aggregate their results.

**7\. Final Bid Review**

Implement a read-only Final Bid Review screen.

Header:

- Title: Final Bid Review
- Description: Review the information that will form your electronic bid.
- Status: Ready to submit

Show:

- Tender reference
- Procuring entity
- Bidder legal name
- Submission deadline
- Applicable lots
- Main offer and permitted alternatives, when applicable

Show the configured bidder sections in checklist order.

For each section, show:

- Section name
- Completion status
- Concise response summary
- Supplied evidence names, when applicable
- Review action

The Review action opens that completed section in read-only mode.

Do not reproduce every field on the main Final Bid Review screen.

For Price Schedule:

- Show calculated totals by currency
- Do not combine different currencies

For Form of Tender:

- Show the current price values derived from the Price Schedule
- Do not expose a second independently stored tender total

Footer actions:

- Back to Review & Validate
- Continue to Submit Bid

Do not add a declaration or confirmation checkbox on this screen.

**8\. Submit Bid screen**

Implement the approved Submit Bid screen.

Show:

- Tender
- Tender reference
- Procuring entity
- Bidder legal name
- Applicable lots
- Bid totals by currency
- Submission deadline
- Readiness status

Show the authenticated submitter as read-only:

- Full name
- Organisation
- Role or designation
- Account email

Do not ask the user to type identity information already known by the authenticated account.

Use one final declaration:

I confirm that I am authorised to submit this bid on behalf of the bidder and that the electronic bid reviewed above is the bid being submitted.

Require one checkbox:

I confirm and submit this bid on behalf of the bidder.

Actions:

- Back to Final Review
- Submit Bid

Enable Submit Bid only when:

- Readiness remains valid
- No blocking issues exist
- The deadline has not passed
- The user has submission permission
- The final declaration is confirmed

Do not repeat the Form of Tender, CBQ or Statutory Declaration confirmations.

**9\. Submission permission**

Use the existing bidder-team permission model.

Users with editing access may prepare and review the bid.

Only a user with the existing bid-submission permission may execute Submit Bid.

If the authenticated user lacks permission:

- Keep the bid review accessible
- Disable the submission action
- Display: You do not have permission to submit this bid.
- Do not provide a manual name or designation workaround

Do not invent a separate bidder approval workflow unless one already exists in the repository or tender configuration.

**10\. Confirmation dialog**

Clicking Submit Bid must open a confirmation dialog.

Title:

Submit this bid?

Message:

This will formally submit the current electronic bid. After submission, it cannot be edited unless the tender rules permit withdrawal or revision before the deadline.

Show:

- Tender reference
- Bidder legal name
- Applicable lots
- Bid totals by currency
- Submission deadline

Actions:

- Cancel
- Submit Bid

Do not require another checkbox.

Do not require the user to type the tender reference.

Closing or cancelling the dialog must not submit the bid.

**11\. Server-side submission operation**

On final confirmation:

- Acquire the appropriate submission lock or transaction.
- Confirm the tender is still open using server time.
- Confirm the authenticated user still has submission permission.
- Rerun the complete readiness validation.
- Reject submission if any blocker now exists.
- Capture the current electronic bid as the submitted version.
- Record the authenticated submitter.
- Record the server submission timestamp and timezone.
- Change the submission state to Submitted.
- Prevent further editing under the existing submission lifecycle.
- Generate a human-readable submission receipt reference.
- Return the submission receipt screen.

The client must not be able to supply:

- Submission time
- Submitted status
- Calculated totals
- Readiness result
- Submitter identity override

Use existing internal integrity controls if available. Do not introduce a new content-addressing or cryptographic architecture for this task.

**12\. Submission receipt**

Implement the successful submission screen.

Header:

- Status: Bid submitted
- Message: Your bid has been formally submitted.
- Receipt reference
- Submitted date and time with timezone

Show:

- Tender
- Tender reference
- Procuring entity
- Bidder legal name
- Submitted by
- Applicable lots
- Bid totals by currency
- Submission status: Submitted

Show:

This receipt confirms that the electronic bid was received by KenTender at the date and time shown above.

Actions:

- Download receipt
- Print receipt
- Return to My Bids

The downloadable and printable receipt must contain the same user-facing information.

Do not include hashes, database IDs, package versions or schema names.

**13\. Revision and withdrawal boundary**

Use the existing tender rules and submission lifecycle.

If withdrawal or revision is already permitted before the deadline:

- A submitted bid remains locked until the bidder explicitly starts the permitted withdrawal or revision process.
- A revised bid must pass Review & Validate again.
- It must be formally resubmitted.
- The new receipt must clearly identify the latest submission.
- The previous submission record must remain auditable.

Do not implement a new withdrawal or revision module in this task if the repository does not already support it. Report that as a separate follow-on scope.

**14\. State transitions**

Implement the following effective flow using existing state fields where possible:

- Bid sections incomplete → In progress
- All applicable sections complete → Review & Validate available
- Validation blockers found → Needs attention
- Validation succeeds → Ready to submit
- Any response changes after validation → In progress or Needs attention
- Submission succeeds → Submitted

Any change to a validated bid must invalidate readiness.

Any change to Price Schedule totals must also invalidate Form of Tender review.

Do not allow the client to set these states directly.

**15\. Tests**

Add tests for:

- Checklist displays Review & Validate Bid below the section list
- Entry action activates when all applicable required sections are complete
- Sidebar Review & Validate state matches workflow availability
- Validation aggregates configured sections only
- Excluded sections do not block submission
- Blocking issues link to the affected section or item
- Review Final Bid remains disabled while blockers exist
- Final Bid Review is read-only
- Final review uses current response data
- Price Schedule and Form of Tender totals remain synchronized
- Totals remain separated by currency
- Editing after validation invalidates readiness
- Submit & Seal navigation activates only when ready
- User without submission permission cannot submit
- Confirmation dialog is required
- Cancelling the dialog does not submit
- Deadline and readiness are rechecked on the server
- Client cannot override totals, submitter, time or submission state
- Successful submission locks the submitted bid
- Receipt contains the required user-facing information
- Cross-bidder access is rejected
- No hashes or technical identifiers appear in any bidder-facing screen

**16\. Delivery steps**

Before implementation, inspect:

- Existing checklist and sidebar enablement logic
- Current section completion and issue aggregation
- Existing bidder roles and submission permission
- Existing submission status model
- Existing deadline enforcement
- Form of Tender and Price Schedule integration
- Approved Stitch designs for Review & Validate, Final Bid Review, Submit Bid, confirmation dialog and receipt

Reuse the existing architecture.

Implement:

- Entry-point actions
- Routes
- Readiness aggregation
- Read-only final review
- Submission permission enforcement
- Confirmation dialog
- Atomic server-side submission
- Receipt display and download
- Tests
- Checklist and sidebar integration

Finish with a concise report containing:

- Files changed
- Entry points implemented
- Validation rules aggregated
- Permission rules enforced
- Submission state changes
- Receipt implementation
- Tests executed and results
- Any genuine follow-on gaps

Do not expand this task into evaluator access, bid opening, tender evaluation, bid comparison, withdrawal redesign, PDF bid generation or a new cryptographic architecture.