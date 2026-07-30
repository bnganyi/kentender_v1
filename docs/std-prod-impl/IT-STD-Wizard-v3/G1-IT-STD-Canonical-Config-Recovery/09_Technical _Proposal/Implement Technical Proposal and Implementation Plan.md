**Implement Technical Proposal and Implementation Plan**

Implement the bidder-facing **Technical Proposal and Implementation Plan** section.

This is a lean but complete implementation of the configured tender-stage Preliminary Project Plan. Do not create a generic document-management framework or modify unrelated checklist sections.

**1\. Objective**

Digitize the Preliminary Project Plan required by the canonical Information Technology STD.

The bidder must explain how it proposes to manage, coordinate and deliver the Information System if awarded the contract.

The system must:

- Collect the mandatory core information required by ITT 18.2.
- Render additional sub-plans only when configured in the TDS.
- Capture narrative and tabular responses electronically.
- Reuse information already owned by Qualification, Requirements Compliance, Lots and Pricing.
- Derive completion, issues and checklist readiness.
- Keep the plan editable until final bid submission.

This is the tender-stage **Preliminary Project Plan**. It is not the final Agreed Project Plan produced after contract award.

NSSF is test data only. Do not hard-code NSSF topics, schedules, roles, values or deliverables.

**2\. Legal and module boundaries**

The canonical IT STD requires:

- A Preliminary Project Plan covering:
  - Overall management and coordination.
  - Human and other resources.
  - Expected Procuring Entity and third-party inputs.
  - Coordination of all involved parties.
- Written confirmation that the bidder accepts responsibility for successful integration and interoperability.

Additional sub-plans become mandatory only when specified in TDS ITT 18.2(a).

Do not duplicate:

- Item-by-item technical commentary: owned by Requirements Compliance.
- Personnel profiles and qualifications: owned by Qualification and Capability.
- Delivery-partner information: owned by Qualification and Capability.
- Prices: owned by Price Schedule.
- Lot selection: owned by Lots and Alternatives.
- Final bid certification and sealing: owned by Final Declaration and Submission.

Supporting material may be referenced from this section, but it must not replace the required electronic responses.

**3\. Inspect before changing**

Identify the existing:

- Published tender-configuration model.
- Bidder-submission persistence.
- Evidence records.
- Section checklist derivation.
- Draft-save pattern.
- Validation conventions.
- Lots and bidder-member scoping.
- Qualification record references.
- Final Stitch designs under docs/bidder-workspace/.

Reuse existing repository conventions.

Do not introduce:

- A second submission model.
- A general-purpose workflow engine.
- A generic form-builder rewrite.
- A separate technical-proposal service.
- Manually maintained completion statuses.

Development data may be reset if necessary. Do not add production migration complexity.

**4\. Configuration approach**

The published tender configuration determines which proposal subsections appear.

Each configured subsection must provide:

- Stable subsection key.
- Bidder-facing title.
- Description.
- Renderer key.
- Display order.
- Requirement mode.
- Tender or lot scope.
- Exact configured questions.
- Required response type.
- Evidence requirements.
- Named activation condition where conditional.

Use these requirement modes:

- required
- optional
- conditional
- excluded

Rules:

- required: display and block section completion until complete.
- optional: display with an Optional label and never block completion.
- conditional: evaluate its configured named condition.
- excluded: do not display or validate.
- A conditional subsection whose condition is false is Not applicable and does not block completion.
- A conditional subsection whose condition becomes true follows its configured required or optional behaviour.
- An enabled subsection without a supported renderer or configured questions is a tender-configuration error.
- Do not generate empty placeholder screens.
- Do not infer applicability merely because a sample STD contains the topic.
- Do not infer applicability from NSSF.
- Do not create a general expression engine. Use existing named-condition support or add only the explicit named conditions required here.

For the canonical IT STD, the mandatory base configuration must include:

- project_organization_and_coordination
- integration_responsibility_confirmation

The following are candidate TDS-configured renderers, not universally mandatory:

- technical_approach
- implementation_work_plan
- training_and_knowledge_transfer
- testing_and_quality_assurance
- warranty_defect_repair_and_support
- transition_and_handover
- risks_assumptions_and_dependencies
- technical_alternatives

Typical conditions include:

- Technical alternatives are permitted by TDS ITT 15.4.
- Alternatives to the time schedule are permitted.
- Training is included in the configured TDS topics.
- Data migration is included in the Procuring Entity's Requirements.
- Warranty or support sub-plans are expressly required.
- A topic applies only to a selected lot.

If an additional topic is specified in the TDS, template preparation must assign it to an approved renderer before publication.

**5\. Overview screen**

Implement the **Technical Proposal and Implementation Plan** overview.

Header:

- Title: Technical Proposal and Implementation Plan
- Description: Explain how you will manage, deliver, test and hand over the proposed system.

Show:

- Required-subsection progress.
- Subsection.
- What the bidder must provide.
- Required or Optional.
- Progress.
- Status.
- Current issue.
- Action.

The KPI must say:

- {completed required subsections} of {applicable required subsections} required subsections complete

Optional subsections do not count in the denominator.

Use only:

- Not started
- In progress
- Complete
- Needs attention
- Not applicable

Actions:

- Start
- Continue
- Resolve
- Review

Do not show evaluator points, scores, Passed, Failed, Responsive or Compliant.

**6\. Mandatory project organization and coordination**

Implement the mandatory core renderer.

Collect:

**6.1 Management and coordination approach**

Configured narrative questions covering:

- Overall project-management approach.
- Reporting arrangements.
- Communication arrangements.
- Decision-making and escalation.
- Coordination between involved parties.

**6.2 Human and other resources**

Reference existing records rather than duplicating them.

Show:

- Project role.
- Assigned Key Personnel record.
- Providing bidder or JV member.
- Responsibility in the proposed plan.
- Decision authority.
- Planned involvement.

Do not repeat:

- CVs.
- Qualifications.
- Employment history.
- Personnel evidence.

Those remain owned by Qualification and Capability.

Allow other configured non-personnel resources to be entered where required.

**6.3 Responsibility and coordination matrix**

Use structured repeating records:

- Activity or deliverable.
- Bidder responsibility.
- Procuring Entity responsibility.
- Third-party responsibility.
- Coordination method.
- Required input.
- Required timing.

The bidder must identify what it expects the Procuring Entity and involved third parties to provide.

**7\. Technical approach renderer**

Render only when configured.

Collect configured narrative responses covering relevant topics such as:

- Proposed solution overview.
- Technical architecture.
- Major solution components.
- Delivery methodology.
- Integration approach.
- Interoperability approach.
- Use of existing infrastructure.
- Configured technology-specific topics.

This screen must not contain the item-by-item requirements matrix.

Allow supporting materials to be attached to a specific response. Attachments are supplementary.

**8\. Implementation work-plan renderer**

Render only when configured.

Capture the work plan as structured activities.

For each activity record:

- Phase.
- Activity.
- Deliverable.
- Start week from Contract Effective Date.
- Duration in weeks.
- Calculated completion week.
- Dependency.
- Milestone.
- Acceptance point where configured.
- Responsible project role.
- Applicable lot where relevant.

Rules:

- Calculate completion week.
- Validate start, duration and dependency ordering.
- Identify circular or missing dependencies.
- Identify work extending beyond the configured completion period.
- Reference assigned project roles rather than duplicating personnel.
- Generate any timeline or Gantt presentation from structured activity data.
- Do not require a Gantt file as the primary response.

The configured Implementation Schedule remains authoritative. The bidder's work plan must not silently overwrite contractual milestone requirements.

**9\. Training and knowledge-transfer renderer**

Render only when configured.

For each activity collect:

- Audience.
- Topic.
- Learning objective.
- Delivery method.
- Location or delivery channel.
- Duration.
- Planned work-plan timing.
- Materials or outputs.
- Responsible person.
- Expected completion evidence.

Reference Key Personnel without copying their profiles.

Configured training audiences, minimum curricula, modes and deliverables must be shown exactly.

**10\. Testing and quality-assurance renderer**

Render only when configured.

Collect configured narrative responses for:

- Quality assurance.
- Configuration control.
- Change control.
- Defect management.
- Commissioning.
- Operational-acceptance preparation.

Capture test stages as structured records:

- Test stage.
- Scope.
- Responsible party.
- Entry criteria.
- Expected output.
- Procuring Entity participation.
- Planned work-plan activity.
- Acceptance reference.
- Supporting material.

The bidder proposes its method. This section must not record an evaluator or Procuring Entity acceptance decision.

**11\. Warranty, defect-repair and support renderer**

Render only when configured.

Collect:

- Warranty-support approach.
- Defect-reporting process.
- Response and restoration arrangements.
- Escalation.
- Support channels.
- Support hours.
- Planned support resources.
- Knowledge and documentation handover.
- Configured service-level responses.

Do not collect recurrent-cost prices here. Reference the owning Price Schedule where required.

**12\. Transition and handover renderer**

Render only when configured.

Support configured topics such as:

- Data migration.
- Cutover.
- Service continuity.
- Operational transition.
- Documentation handover.
- Administrator handover.
- Support transition.
- Decommissioning where applicable.

Use structured activities where timing and ownership are required.

Do not create a migration screen when migration is not part of the tender requirements.

**13\. Risks, assumptions and dependencies renderer**

Render only when expressly configured.

Risk records:

- Risk.
- Potential effect.
- Proposed mitigation.
- Responsible party.
- Related work-plan activity.

Assumption records:

- Assumption.
- Responsible party.
- Effect if incorrect.

Dependency records:

- Required input or dependency.
- Responsible party.
- Required by.
- Affected activity.
- Proposed coordination action.

Do not introduce evaluator risk scores.

**14\. Technical-alternatives renderer**

Render only when the TDS permits technical alternatives.

The base proposal remains mandatory.

For every alternative collect:

- Alternative title.
- Permitted system part.
- Description.
- Difference from the base proposal.
- Technical effect.
- Schedule effect.
- Price Schedule reference.
- Supporting information.

Rules:

- An alternative must not replace the base response.
- Do not collect duplicate prices.
- Link to the corresponding alternative Price Schedule.
- Do not show this subsection when alternatives are prohibited.

**15\. Integration and interoperability confirmation**

Place one confirmation on the section review screen:

I confirm that the bidder accepts responsibility for the successful integration and interoperability of the proposed system components.

Rules:

- Required for the canonical IT STD.
- Do not repeat it on individual subsection screens.
- Record the confirming user and timestamp.
- This is section completion, not final bid submission or sealing.
- Do not ask the bidder to re-enter an authorized signatory already owned elsewhere.

**16\. Evidence and cross-section references**

Support:

- Selecting suitable existing evidence.
- Adding new supporting evidence.
- Viewing, replacing and removing evidence before submission.
- Linking evidence to a specific response.

References to other sections must remain references:

- Key Personnel.
- Delivery Partners.
- Lots.
- Requirements Compliance.
- Price Schedules.

Do not copy the underlying records.

Do not expose:

- File hashes.
- Storage paths.
- Schema IDs.
- Package artifacts.
- Internal validation codes.
- PDF page references.

**17\. Completion and issues**

Derive subsection state from:

- Published configuration.
- Saved responses.
- Required structured records.
- Evidence references.
- Validation results.

Rules:

- Not applicable: conditional rule is false.
- Not started: applicable but no response is saved.
- In progress: some response exists but required work remains.
- Needs attention: an attempted response is invalid or has a blocking dependency.
- Complete: all applicable required content is complete and valid.

Do not persist a manually editable status.

Issue text must be actionable, for example:

- Management responsibilities are incomplete.
- Two work-plan activities have no responsible role.
- The proposed schedule exceeds the permitted completion period.
- Testing approach has not been provided.
- Integration responsibility has not been confirmed.

**18\. Section checklist and submission readiness**

Derive the section state as follows:

- Needs attention when any applicable required subsection needs attention.
- In progress when required work has started but remains incomplete.
- Not started when no required subsection has started.
- Complete only when every applicable required subsection is complete and integration responsibility is confirmed.
- Not applicable only if a lawful configured template excludes the entire section.

Optional subsections never block section completion.

Conditional subsections block only when activated and configured as required.

The bidder checklist must link to the subsection requiring action.

**19\. Tender and lot scope**

Support:

- Tender-level proposal topics answered once.
- Lot-level topics answered separately for selected lots.
- Shared responses only where configuration explicitly permits them.
- Alternative proposals associated with the correct lot or system part.
- Work-plan activities associated with the correct scope.

Do not mix responses between tenders, bidders, submissions or lots.

**20\. Validation**

Validate on the server.

At minimum validate:

- Required applicable subsections.
- Required configured questions.
- Required repeating-record minimums.
- Narrative responses are not empty.
- Activity dates and durations.
- Dependency ordering.
- Completion-period limits.
- Required project roles.
- Cross-section reference ownership.
- Selected-lot scope.
- Required testing stages.
- Required training activities.
- Technical-alternative permission and scope.
- Integration-responsibility confirmation.
- Evidence ownership and accessibility.

Client-side validation is supplementary.

**21\. UI implementation**

Use the approved Stitch designs as visual references.

Implement the approved content and interaction behaviour rather than copying prototype HTML blindly.

Requirements:

- Use the existing bidder-workspace shell.
- Keep the interface electronic and task-focused.
- Use focused subsection pages.
- Use drawers for contextual activity or record editing.
- Use full pages for substantial reusable records.
- Preserve drafts.
- Return to the overview after completing a subsection.
- Keep the section editable until final bid submission.

Do not show:

- Technical IDs.
- Hashes.
- Audit logs.
- Internal rule labels.
- Evaluator scores.
- Pass/fail results.
- Document-page instructions.
- A requirement to upload one complete technical-proposal PDF.

**22\. Implementation order**

- Inspect existing repository patterns and document what will be reused.
- Add the minimum missing proposal-subsection configuration.
- Implement applicability resolution.
- Implement mandatory project organization and coordination.
- Implement configured sub-plan renderers.
- Implement work-plan calculations and validation.
- Implement cross-section references.
- Implement integration-responsibility confirmation.
- Implement derived status and issue summaries.
- Implement overview and checklist roll-up.
- Add fixtures and tests.
- Produce the implementation report.

Do not perform unrelated refactoring.

**23\. Required fixtures**

Create three generic development fixtures:

**Core IT plan**

- Mandatory project organization and coordination.
- Mandatory integration responsibility.
- All additional sub-plans excluded.

**Full IT plan**

- Technical approach.
- Project organization and coordination.
- Implementation work plan.
- Training.
- Testing and quality assurance.
- Warranty and support.
- Risks and dependencies.
- Integration responsibility.

**Conditional plan**

- Core topics required.
- Training optional.
- Migration excluded.
- Technical alternatives conditional on TDS permission.
- One lot-specific implementation topic.

Do not use NSSF as the canonical fixture.

**24\. Required tests**

Prove that:

- Core mandatory topics always appear for the canonical IT STD.
- TDS-configured sub-plans appear and block completion when required.
- Excluded sub-plans do not appear or validate.
- Optional sub-plans do not block completion.
- Conditional alternatives are hidden or Not applicable when prohibited.
- Permitted technical alternatives remain separate from the base proposal.
- Required progress excludes optional and inactive conditional subsections.
- Personnel records are referenced without duplication.
- Price information is not duplicated.
- Requirements Compliance responses are not duplicated.
- Work-plan completion weeks are calculated correctly.
- Invalid activity dependencies produce Needs attention.
- Work beyond the configured completion period produces an actionable issue.
- Lot-specific responses remain within the correct lot.
- Integration responsibility is confirmed once.
- Section completion does not submit or seal the bid.
- Two tenders based on the same STD can use different TDS topic configurations.
- No bidder-facing response exposes scores, hashes or internal IDs.
- The renderer works without NSSF-specific data.

**25\. Completion report**

Create:

docs/bidder-workspace/TECHNICAL_PROPOSAL_AND_IMPLEMENTATION_PLAN_IMPLEMENTATION_REPORT.md

Include:

- Existing components reused.
- Files changed.
- Configuration fields added.
- Supported subsection and condition keys.
- Mandatory-core rules.
- TDS applicability rules.
- Renderers implemented.
- Cross-section references.
- Validation implemented.
- Status derivation.
- Fixtures created.
- Tests and results.
- Explicitly deferred edge cases.

Stop after this section is implemented, tested and documented.