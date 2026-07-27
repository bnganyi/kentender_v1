**Implement Qualification and Capability**

Implement the bidder-facing **Qualification and Capability** section.

Work only on this section and its checklist roll-up. Do not modify unrelated bidder-workspace sections, navigation or global styling.

**1\. Objective**

Digitize the configured qualification requirements of the canonical Information Technology STD.

The bidder must provide structured facts and evidence. The system must:

- Show only the categories configured for the published tender.
- Reuse authoritative information already collected elsewhere.
- Calculate completion and issues from saved responses.
- Prevent incomplete required categories from being treated as complete.
- Never calculate or display evaluator scores, Passed, Failed, Qualified or Compliant.

NSSF is test data only. Do not hard-code NSSF categories, values, counts, currencies, dates, roles or thresholds.

**2\. Inspect before changing**

Identify and document the existing:

- Published tender-configuration structure.
- Bidder-submission persistence model.
- Evidence/document records.
- Section checklist derivation.
- Validation conventions.
- Qualification routes, views, templates and tests.
- Final Stitch references under docs/bidder-workspace/, if present.

Reuse existing repository conventions. Do not introduce a second submission model, generic workflow engine or qualification microservice.

If development data prevents a clean implementation, reset or rebuild it. Do not add production migration complexity.

**3\. Configuration ownership**

Qualification categories are configured during STD-template preparation or tender preparation and are bound to the published tender.

The bidder cannot add, remove or change configured categories or criteria.

Each configured category must provide:

- Stable category key.
- Bidder-facing label.
- Renderer key.
- Display order.
- Requirement mode.
- Exact requirement summary.
- Configured criteria.
- Tender, lot or bidder-member scope where applicable.

Use these requirement modes:

- required
- optional
- conditional
- excluded

Rules:

- required: display and block submission until complete.
- optional: display with an "Optional" label but never block submission.
- conditional: evaluate its configured named condition.
- excluded: do not display or validate.
- A conditional category whose condition is false has status Not applicable and does not block submission.
- A conditional category whose condition becomes true follows its configured required or optional behaviour.
- A category with no configured criteria must not appear as an empty bidder screen. Treat this as a tender-configuration error.
- Do not infer applicability merely because the canonical STD contains a form.
- Do not build a general-purpose expression or rules engine. Use the condition mechanism already present in the repository. If none exists, implement only explicit named conditions required by the configured templates.

Examples of legitimate named conditions include:

- Key positions have been configured.
- Major subcontractor, vendor or manufacturer requirements have been configured.
- The bidder selected an external provider.
- The bidder is a joint venture.
- A foreign-bidder requirement applies.
- A selected lot contains the criterion.

The published tender configuration is authoritative.

**4\. Supported category renderers**

Implement the currently approved qualification categories.

**4.1 Contract performance and litigation**

Ground this category in the configured CON-1 requirements.

Support:

- Historical contract non-performance.
- Suspended or terminated contracts where configured.
- Pending litigation.
- Litigation history.
- Repeating disclosure records.
- Required explanations and evidence.

Use explicit questions and structured records. Do not represent this category as a certificate upload.

**4.2 Financial capability**

Support only the financial requirements enabled for the tender:

- Financial situation.
- Audited financial statements.
- Average annual turnover.
- Available financial resources.
- Current contract commitments where configured.
- JV-member-specific information where applicable.

Currencies, financial years, minimum periods and required evidence come from configuration.

Do not calculate an evaluator outcome.

**4.3 Experience**

Keep general experience and specific experience distinct.

General experience must support the configured EXP-1 information:

- Contract identification.
- Start month and year.
- End month and year.
- Brief description.
- Procuring entity.
- Procuring-entity address.
- Bidder role.
- Calculated qualifying calendar years.

Do not convert a required number of years into a required number of projects.

Where the STD rule is configured, count a calendar year only when contract activity covers at least nine months in that year.

Specific experience must support the configured EXP-2 information:

- Contract identification.
- Award date.
- Completion date.
- Role in the contract.
- Contract amount and currency.
- JV or subcontractor participation percentage and value.
- Procuring-entity contact details.
- Similarity against each configured dimension:
  - Amount.
  - Physical size.
  - Complexity.
  - Methods or technology.
  - Key activities.

A saved project may support both general and specific experience. Reference the same project record; do not duplicate it.

**4.4 Key personnel**

Render only the positions configured for the tender.

For every position:

- Show the exact qualification and experience requirements.
- Assign one saved or newly created person.
- Show the bidder or JV member providing the person.
- Prevent assignment of an incomplete personnel profile.
- Prevent the same person from filling multiple positions unless the tender configuration permits it.
- Reuse personnel records without copying them.

The bidder supplies personnel facts and evidence. The system does not decide whether the candidate is technically qualified.

**4.5 Delivery partners**

Render only configured major items and services.

For goods, ask:

- "Who manufactures or produces this item?"

For services, ask:

- "Who will perform this service?"

Allow:

- Bidder.
- Another organization.

If another organization is selected:

- Select a saved organization or add one.
- Record its role as Manufacturer, Vendor or Subcontractor.
- Display every configured minimum criterion.
- Collect a response or evidence for every criterion.
- Derive role-specific requirements.

Manufacturer authorization and subcontractor agreements are tender-specific electronic records. They cannot be reused from another tender.

Reusable organization certificates may be referenced without uploading them again.

**5\. Reuse authoritative data**

Do not ask the bidder to re-enter:

- Bidder legal name.
- Bidder address.
- JV-member legal names.
- Tender reference.
- Tender title.
- Procuring entity.
- Authorized signatory information already captured authoritatively.

Read these values from the existing bidder, CBQ and tender records.

Allow editing only in the owning section. Qualification screens may link the bidder to that section when correction is required.

**6\. Qualification overview**

Implement the approved Qualification and Capability overview.

Show:

- Title: Qualification and Capability
- Description: Provide the information and evidence demonstrating your organisation's capacity to perform the contract.
- Required-category progress.
- Category.
- Requirement summary.
- Progress.
- Status.
- Current issue.
- Action.

The overall KPI must say:

- {completed required categories} of {applicable required categories} required categories complete

Do not include optional categories in this denominator.

Optional categories must display an Optional label.

Category names, counts, thresholds, periods and issue text must be derived from the published tender configuration and current bidder responses.

**7\. Derive completion and issue states**

Add derived completion and issue information to the existing Qualification and Capability category list used by:

- The Qualification and Capability overview.
- The bidder section checklist.
- Submission-readiness validation.

For every configured category, derive:

- Completed item count.
- Required item count.
- Progress text.
- Status.
- Current issue summary.
- Next action.

Use only:

- Not started
- In progress
- Complete
- Needs attention
- Not applicable

Derivation rules:

- Not applicable: the configured conditional rule evaluates false.
- Not started: the category applies but contains no saved bidder response.
- In progress: at least one response is saved, but required work remains and there is no blocking validation issue.
- Needs attention: a required response is invalid, contradictory, expired, incomplete after attempted completion, or has a blocking dependency.
- Complete: every applicable required item in the category is complete and no blocking validation issue remains.

Do not persist manually editable category statuses.

Derive them from:

- Published category configuration.
- Saved bidder responses.
- Evidence references.
- Validation results.

Issue summaries must be bidder-actionable, for example:

- Pending litigation response is incomplete.
- Financial statement for 2025 is missing.
- 1 qualifying year and 1 specific-experience record remaining.
- 2 required positions remain unassigned.
- Manufacturer authorization has not been completed.

Do not expose internal rule identifiers, hashes, schema keys, database IDs or technical validation messages.

**8\. Section and submission readiness**

Derive the Qualification and Capability checklist state as follows:

- Needs attention if any applicable required category needs attention.
- In progress if at least one applicable required category has started and required work remains.
- Not started if no applicable required category has started.
- Complete only when every applicable required category is complete.
- Not applicable only when the published tender contains no applicable required or optional qualification category.

Optional categories never block section completion or submission.

Conditional categories block only after their condition becomes true and only when configured as required.

Submission must be blocked when any applicable required qualification category is incomplete or needs attention.

The checklist must link directly to the category requiring action.

**9\. Lot and member scope**

Respect configured scope.

- Tender-level criteria are answered once.
- Lot-level criteria apply only to lots selected by the bidder.
- JV-member criteria must be completed for each required member.
- Lead-bidder-only criteria must not be duplicated for every JV member.
- Progress and issues must identify the affected lot or member in plain language.

Do not combine records belonging to different bidders, submissions, tenders or lots.

**10\. Evidence behaviour**

Evidence must be electronic and referenced from the owning response.

Support:

- Selecting suitable existing evidence.
- Adding new evidence.
- Viewing the selected evidence.
- Replacing or removing evidence before submission.
- Tender-specific electronic authorizations and agreements.

Do not expose file hashes, storage paths, MIME internals, schema IDs or package artifacts.

Selecting evidence does not mean the bidder has passed the criterion. It means the required response is complete enough for submission.

**11\. Validation**

Validate on the server.

At minimum validate:

- Required applicable categories.
- Required configured fields.
- Repeating-record minimums.
- Date ordering.
- Financial-year coverage.
- Currency and amount formats.
- General-experience year calculation.
- Specific-experience record count.
- Lot scope.
- JV-member scope.
- Personnel assignment completeness.
- Duplicate personnel restrictions.
- Delivery-partner criteria.
- Tender-specific authorizations and agreements.
- Evidence ownership and accessibility.

Client-side validation may improve feedback but must not be authoritative.

**12\. UI requirements**

Use the final approved Stitch designs as visual references, including the latest reviewed corrections.

Do not copy prototype defects or hard-coded examples into production.

The UI must:

- Remain concise and task-focused.
- Use the existing bidder-workspace shell.
- Show exact configured requirements.
- Use drawers only for contextual record editing.
- Use full pages for substantial reusable records.
- Preserve drafts.
- Return users to the category overview after saving.
- Show plain-language issues beside the affected category or requirement.

Do not show:

- Evaluator scores.
- Pass/fail outcomes.
- Technical IDs.
- Hashes.
- Audit logs.
- Internal compliance-rule labels.
- PDF-page references.
- Package or schema artifacts.

**13\. Implementation order**

- Inspect the repository and identify reusable models, routes and components.
- Add the minimum missing category-configuration fields.
- Implement applicability resolution.
- Implement the five approved category renderers.
- Implement server-side validation.
- Implement category progress, status, issues and next actions.
- Implement the Qualification and Capability overview.
- Roll the derived state into the bidder checklist and submission readiness.
- Add fixtures for multiple tender configurations.
- Run tests and produce the implementation report.

Do not perform unrelated refactoring.

**14\. Required tests**

Add tests proving:

- A tender may require all five categories.
- A tender may require only Financial Capability and Experience.
- An optional Key Personnel category does not block submission.
- An excluded Delivery Partners category is not rendered or validated.
- A conditional Delivery Partners category is Not applicable until its trigger becomes true.
- Once that required condition becomes true, incomplete delivery-partner responses block submission.
- Category status changes from Not started to In progress to Complete.
- Invalid attempted responses produce Needs attention with a plain-language issue.
- General-experience years are not treated as project counts.
- A project can support general and specific experience without duplication.
- Personnel cannot be assigned twice unless configuration permits it.
- Existing reusable evidence can be selected without copying the underlying file.
- Tender-specific authorization cannot be reused across tenders.
- Lot-specific criteria affect only selected lots.
- JV-member criteria are enforced only for the configured members.
- Optional categories are excluded from the required-category progress denominator.
- No bidder-facing response contains scores, pass/fail results, hashes or internal IDs.
- Two tenders using the same IT STD can publish different qualification configurations.
- No NSSF-specific value is required for the renderer to work.

**15\. Development fixtures**

Create at least three development fixtures:

- Full IT qualification configuration.
- Reduced configuration with only Financial Capability and Experience required.
- Conditional configuration with optional personnel and externally triggered delivery-partner requirements.

Use realistic but generic test data. Do not make NSSF the canonical fixture.

**16\. Completion report**

Create:

docs/bidder-workspace/QUALIFICATION_AND_CAPABILITY_IMPLEMENTATION_REPORT.md

Include:

- Existing components reused.
- Files changed.
- Configuration fields added.
- Supported category and condition keys.
- Applicability rules.
- Status derivation rules.
- Validation implemented.
- Routes and screens implemented.
- Tests added and results.
- Fixture configurations.
- Known limitations requiring a future approved renderer.

Stop after Qualification and Capability is implemented, tested and documented.