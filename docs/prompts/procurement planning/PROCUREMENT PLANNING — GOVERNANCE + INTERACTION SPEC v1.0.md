Procurement Planning — Plan/Package Governance, Interaction, Approval & UI Specification v1.0

# Rationale

**1\. Purpose**

This document locks the interaction between **Procurement Plans** and **Procurement Packages**.

It answers:

-   who approves the package
-   who approves the plan
-   when a plan may be submitted
-   when a package may be marked ready
-   when a package may be released to Tendering
-   what each status means
-   what UI actions should appear or be blocked
-   how the workbench should explain blocked actions
-   how Cursor should implement this without weakening governance

This replaces any earlier ambiguous behavior.

**2\. Core decision**

A **Procurement Plan must not be submitted unless all packages in the plan are already approved**.

This is the strict governance model you selected.

That means:

Plan submission requires all packages to be Approved.

No plan should be escalated for institutional approval while it still contains draft, incomplete, submitted, returned, or unapproved packages.

**3\. Why this rule exists**

A procurement plan is not just a container. It is a governance artifact.

Submitting a plan with unapproved packages means asking an authority to approve a plan whose execution units are not yet technically validated.

That creates several risks:

-   weak audit trail
-   plan approval over incomplete work
-   packages changing materially after plan approval
-   unclear accountability
-   downstream tender release confusion
-   legal/procurement governance leakage

So the strict model is:

Package approval first.

Plan submission second.

Plan approval third.

Tender release last.

**4\. Conceptual separation**

**4.1 Plan approval**

Plan approval answers:

“Is this procurement plan institutionally authorized?”

It validates:

-   total planned value
-   fiscal year alignment
-   budget and strategy alignment
-   institutional priorities
-   aggregate risk
-   whether the procurement portfolio should proceed

Plan approval is a **governance / financial / institutional approval**.

**4.2 Package approval**

Package approval answers:

“Is this individual procurement package properly designed?”

It validates:

-   demand lines are correct
-   demand grouping is coherent
-   template is applied
-   procurement method is appropriate
-   contract type is appropriate
-   risk profile is acceptable
-   KPI profile is acceptable
-   decision criteria are appropriate
-   vendor management posture is adequate
-   estimated value matches package lines

Package approval is a **procurement / technical / execution-level approval**.

**5\. Who approves what?**

**5.1 Package approval**

Recommended owner:

Procurement Manager / Head of Procurement

Supported/reviewing roles:

-   Procurement Officer
-   Procurement Specialist
-   Technical Reviewer, if relevant
-   Compliance/Procurement Reviewer, if method override or high-risk package exists

Package approval should sit with the procurement function because it is about whether the procurement action is properly designed.

**Package approver validates**

| **Area** | **Question** |
| --- | --- |
| Scope | Are the demand lines appropriate and coherent? |
| Packaging | Are demands grouped correctly? |
| Method | Is RFQ/Open Tender/Direct Procurement justified? |
| Contract type | Is the contract model appropriate? |
| Risk | Are risks understood and mitigated? |
| Evaluation | Are decision criteria suitable? |
| Template | Has the correct procurement template been used? |
| Readiness | Is this package mature enough to form part of the plan? |

**5.2 Plan approval**

Recommended owner:

Approving Authority / Tender Board / Accounting Officer delegate

Supporting roles:

-   Finance Controller / Budget Owner
-   Program Director / Department Head
-   Procurement Head, if part of institutional approval
-   Senior Management / Approving Authority

Plan approval sits above the procurement team because it is about whether the organization authorizes the planned procurement portfolio.

**Plan approver validates**

| **Area** | **Question** |
| --- | --- |
| Budget | Is the total planned value acceptable? |
| Strategy | Does the plan align to institutional priorities? |
| Completeness | Are all packages already approved? |
| Timing | Is the procurement calendar acceptable? |
| Risk | Are high-risk packages visible and acceptable? |
| Governance | Should this plan proceed to tender release authority? |

**6\. Fundamental governance rule**

Package Approved ≠ Allowed to Tender.

Plan Approved + Package Ready = Allowed to Release to Tender.

This distinction is critical.

A package may be approved by procurement, but it still cannot be released unless the plan is approved.

The clean mental model is:

Package approval = “This procurement action is correctly designed.”

Plan approval = “The institution authorizes this procurement plan.”

Release to Tender = “This package may now enter the tendering module.”

**7\. State models**

**7.1 Procurement Plan states**

| **State** | **Meaning** | **Editable?** | **Main actor** |
| --- | --- | --- | --- |
| Draft | Plan is being prepared | Yes | Planner |
| Submitted | Plan is awaiting institutional approval | No ordinary edits | Planner / Authority |
| Approved | Plan is authorized | Locked | Approving Authority |
| Returned | Plan requires correction | Yes, controlled | Approving Authority / Planner |
| Rejected | Plan rejected | No ordinary progression | Approving Authority |
| Locked | Optional final lock after approval/release | No | System/Admin |

Recommended v1 states:

Draft

Submitted

Approved

Returned

Rejected

Locked may be added later if needed, but Approved should already behave as locked.

**7.2 Procurement Package states**

| **State** | **Meaning** | **Editable?** | **Main actor** |
| --- | --- | --- | --- |
| Draft | Basic package shell exists | Yes | Planner |
| Completed | Package is structurally complete | Limited edits | Planner |
| Submitted | Package submitted for package approval | No ordinary edits | Planner / Package Approver |
| Approved | Package approved by procurement authority | Locked except readiness action | Package Approver |
| Ready for Tender | Package prepared for tender release | Locked | Procurement Officer / Authority |
| Released to Tender | Package handed to Tendering module | No | System / Procurement Officer |
| Returned | Package returned for correction | Yes, controlled | Package Approver / Planner |
| Rejected | Package rejected | No ordinary progression | Package Approver |

Recommended v1 states:

Draft

Completed

Submitted

Approved

Ready for Tender

Released to Tender

Returned

Rejected

**8\. Correct end-to-end flow**

The strict flow is:

1\. Create Procurement Plan

Plan = Draft

2\. Create Procurement Packages

Packages = Draft

3\. Add Demand Lines

Packages now have actual content

4\. Complete Packages

Package = Completed only if completeness rules pass

5\. Submit Packages

Package = Submitted

6\. Approve Packages

Package = Approved

7\. Submit Plan

Allowed only if ALL packages are Approved

8\. Approve Plan

Plan = Approved

9\. Mark Packages Ready for Tender

Package = Ready for Tender

10\. Release Packages to Tendering

Allowed only if:

\- Plan = Approved

\- Package = Ready for Tender

**9\. Package completeness rule**

A package may move from Draft to Completed only if it is structurally complete.

Minimum completeness requirements:

| **Requirement** | **Mandatory?** | **Notes** |
| --- | --- | --- |
| Package name | Yes | Meaningful business name |
| Procurement plan | Yes | Parent plan selected |
| Procurement template | Yes | Package must be template-driven |
| Procurement method | Yes | Derived or selected with valid justification |
| Contract type | Yes | Derived or selected |
| Demand lines | Yes | At least one approved/eligible DIA demand |
| Estimated value | Yes | Derived from demand lines and > 0 |
| Risk profile | Yes | Derived from template or selected |
| KPI profile | Yes | Derived from template or selected |
| Decision criteria profile | Yes | Especially for competitive methods |
| Vendor management profile | Yes | Required for downstream supplier management |
| Schedule | Preferred / required by template | Required if template requires schedule |
| Method override reason | Conditional | Required if method differs from template/default |

Recommended function:

def is\_package\_complete(pkg):

checks = \[

bool(pkg.package\_name),

bool(pkg.plan\_id),

bool(pkg.template\_id),

bool(pkg.procurement\_method),

bool(pkg.contract\_type),

pkg.estimated\_value and pkg.estimated\_value > 0,

pkg.has\_active\_demand\_lines,

bool(pkg.risk\_profile\_id),

bool(pkg.kpi\_profile\_id),

bool(pkg.decision\_criteria\_profile\_id),

bool(pkg.vendor\_management\_profile\_id),

\]

if pkg.method\_override\_flag:

checks.append(bool(pkg.method\_override\_reason))

if pkg.template\_requires\_schedule:

checks.append(bool(pkg.schedule\_start and pkg.schedule\_end))

return all(checks)

**10\. Plan submission rule**

A plan may be submitted only if:

Plan status = Draft or Returned

AND plan has at least one package

AND every active package status = Approved

Hard block if any package is:

-   Draft
-   Completed
-   Submitted
-   Returned
-   Rejected
-   Ready for Tender but not approved through proper path
-   missing approval metadata

Recommended function:

def can\_submit\_plan(plan):

packages = get\_active\_packages(plan)

if not packages:

return False, \["NO\_PACKAGES"\]

blockers = \[\]

for pkg in packages:

if pkg.status != "Approved":

blockers.append({

"code": "PACKAGE\_NOT\_APPROVED",

"package\_code": pkg.package\_code,

"package\_name": pkg.package\_name,

"status": pkg.status,

})

return len(blockers) == 0, blockers

UI message:

Cannot submit plan. All packages must be approved before the procurement plan can be submitted.

If showing details:

The following packages are not approved:

\- PKG-MOH-2026-001 — Completed

\- PKG-MOH-2026-002 — Submitted

**11\. Plan approval rule**

A plan may be approved only if:

Plan status = Submitted

AND all active packages are still Approved

AND no package has been materially changed after package approval

This second check matters. If a package was approved, then someone changed demand lines or method afterward, the package approval should be invalidated or blocked.

Recommended rule:

Any material edit to an Approved package should either:

1\. be blocked, or

2\. move package back to Draft/Completed and require re-approval.

For v1, prefer blocking material edits after package approval.

Material fields include:

-   demand lines
-   estimated value
-   procurement method
-   contract type
-   template
-   risk profile
-   KPI profile
-   decision criteria
-   vendor management profile
-   schedule if schedule is governance-relevant

**12\. Ready for Tender rule**

A package may be marked Ready for Tender only if:

Package status = Approved

AND package completeness still valid

Plan approval is not strictly required to mark readiness if you want readiness to mean “operationally prepared.”

But the UI must make clear:

Ready for Tender does not mean released.

If the plan is not approved, show:

Ready for Tender — blocked by plan approval

**13\. Release to Tender rule**

A package may be released to Tendering only if:

Plan status = Approved

AND Package status = Ready for Tender

AND Package has not already been released

AND Package still passes release validation

Mandatory release validation:

| **Check** | **Required** |
| --- | --- |
| Parent plan approved | Yes |
| Package ready for tender | Yes |
| Package approved | Yes, implied by Ready |
| Package has demand lines | Yes |
| Package estimated value > 0 | Yes |
| Template exists | Yes |
| Procurement method exists | Yes |
| Contract type exists | Yes |
| Decision criteria exists | Yes |
| No rejected/returned state | Yes |
| Not already released | Yes |

Recommended function:

def can\_release\_to\_tender(pkg):

blockers = \[\]

if pkg.plan.status != "Approved":

blockers.append("PLAN\_NOT\_APPROVED")

if pkg.status != "Ready for Tender":

blockers.append("PACKAGE\_NOT\_READY\_FOR\_TENDER")

if not is\_package\_complete(pkg):

blockers.append("PACKAGE\_INCOMPLETE")

if pkg.released\_to\_tender:

blockers.append("ALREADY\_RELEASED")

return len(blockers) == 0, blockers

UI message if blocked:

This package cannot be released to tender because the procurement plan is not approved.

**14\. Action matrix**

**14.1 Package action matrix**

| **Package State** | **Plan State** | **Allowed Actions** | **Blocked Actions** |
| --- | --- | --- | --- |
| Draft | Draft | Edit Package, Add Demand Lines, Complete Package | Submit Package, Mark Ready, Release |
| Draft | Submitted | View only or controlled correction if plan returned | Submit Package, Release |
| Draft | Approved | Usually invalid; should not happen | Release |
| Completed | Draft | Edit, Add/Remove Demand Lines, Submit Package | Release |
| Completed | Submitted | View only unless plan returned | Release |
| Submitted | Draft | Package Approver: Approve / Return / Reject | Edit by Planner, Release |
| Approved | Draft | Mark Ready for Tender | Release |
| Approved | Submitted | Mark Ready optional, but release blocked | Release |
| Approved | Approved | Mark Ready for Tender | — |
| Ready for Tender | Draft | View, show “Blocked by Plan Approval” | Release |
| Ready for Tender | Submitted | View, show “Blocked by Plan Approval” | Release |
| Ready for Tender | Approved | Release to Tender | Edit |
| Released to Tender | Approved | View handoff record | Edit, Re-release |
| Returned | Draft / Returned | Edit, resubmit | Release |
| Rejected | Any | View, clone/recreate if allowed | Release |

**14.2 Plan action matrix**

| **Plan State** | **Package Conditions** | **Allowed Plan Actions** | **Blocked Plan Actions** |
| --- | --- | --- | --- |
| Draft | No packages | Edit Plan, Add Packages | Submit Plan |
| Draft | Some packages not Approved | Edit Plan, Add/Edit Packages | Submit Plan |
| Draft | All packages Approved | Submit Plan | — |
| Submitted | All packages Approved | Approve Plan, Return Plan, Reject Plan | Edit Plan |
| Submitted | Any package no longer Approved | Return Plan / block approval | Approve Plan |
| Approved | Packages Ready | Allow package release | Edit Plan |
| Returned | Corrections needed | Edit Plan / packages as needed | Approve Plan |
| Rejected | Terminal or controlled reopen | View / Admin reopen | Submit without correction |

**15\. Role matrix**

**15.1 Package-level roles**

| **Role** | **Responsibility** | **Allowed Package Actions** |
| --- | --- | --- |
| Planner | Build package | Create, edit Draft/Returned, add demand lines, complete, submit |
| Procurement Officer | Review/support readiness | Review, mark ready if policy allows |
| Procurement Manager / Head of Procurement | Package approval authority | Approve, return, reject package |
| Technical Reviewer | Optional technical input | View/comment/recommend |
| Auditor | Oversight | View only |
| Admin | Controlled support | Override with audit |

**15.2 Plan-level roles**

| **Role** | **Responsibility** | **Allowed Plan Actions** |
| --- | --- | --- |
| Planner | Prepare plan | Create, edit Draft/Returned, submit when all packages approved |
| Finance Controller / Budget Owner | Budget review | View/recommend/validate financial alignment |
| Program Director / Department Head | Program alignment | View/recommend/validate priorities |
| Approving Authority / Tender Board | Plan approval | Approve, return, reject plan |
| Auditor | Oversight | View only |
| Admin | Controlled support | Exceptional override with audit |

**16\. Separation of duties**

Recommended enforcement:

| **Rule** | **Enforcement** |
| --- | --- |
| Planner should not approve own package | Prefer enforced |
| Package approver should not be the creator | Prefer enforced |
| Plan approver should not be the package preparer | Prefer enforced |
| Admin override must be audited | Mandatory |
| Auditor cannot mutate states | Mandatory |

For v1, if full separation-of-duty enforcement is too heavy, at least log and warn.

**17\. UI model**

**17.1 Plan context bar**

The plan is context, not just another card.

Show:

PP-MOH-2026 · FY2026 Procurement Plan · Ministry of Health

Status: Draft

\[Submit Plan\]

Rules:

-   Plan status must always be visible.
-   Plan actions live in the plan context bar.
-   Plan actions must not be mixed with package actions.
-   Submit Plan is disabled unless all packages are approved.

If disabled:

Submit Plan disabled

Reason: All packages must be approved first.

Optional helper:

0 of 3 packages approved

or

3 of 3 packages approved

Ready to submit plan

**17.2 Plan summary KPI strip**

KPIs are plan-level.

Recommended cards:

-   Total Packages
-   Approved Packages
-   Total Planned Value
-   High-Risk Packages
-   Ready for Tender

Avoid ambiguous numbers.

Currency rule:

-   Do not repeat currency in every card.
-   State once: “All monetary figures in KES.”

**17.3 Package work area**

Package work should remain the primary operational area.

Layout:

Package queues + search + filters

Package list | Package detail

Package queues should be package-state based:

-   Draft
-   Completed
-   Submitted
-   Approved
-   Ready for Tender
-   Released
-   Returned
-   Rejected

**17.4 Package detail actions**

Show only state-valid actions.

Examples:

**Draft package**

\[Edit Package\] \[Add Demand Lines\] \[Complete Package\]

**Completed package**

\[Submit Package\]

**Submitted package, package approver**

\[Approve Package\] \[Return\] \[Reject\]

**Approved package**

\[Mark Ready for Tender\]

**Ready for Tender, plan not approved**

Release blocked

Reason: Plan is not approved.

**Ready for Tender, plan approved**

\[Release to Tender\]

**17.5 Add Demand Lines action**

This is mandatory.

The system must expose a clear action:

Add Demand Lines

Where:

-   package detail panel
-   package empty demand-line state
-   package builder “Demand Assignment” tab, as a link to workbench action

**Modal behavior**

Open:

Add Demand Lines to Package

Show:

Left side: Available demands

-   Approved / Planning Ready DIA demands only
-   not already fully assigned
-   matching entity/fiscal year/plan constraints
-   show demand ID, title, department, amount, budget line, priority

Right side: Selected demands

-   selected demand list
-   total selected value

Actions:

\[Cancel\] \[Add to Package\]

On confirm:

-   create Procurement Package Line records
-   update estimated value
-   update completeness state
-   refresh package detail

**Empty state**

If no lines:

No demand lines added yet.

Add approved demand to structure this package.

\[Add Demand Lines\]

This is better than passive guidance.

**18\. Package form vs workbench responsibility**

**18.1 Package form**

Purpose:

Define the package.

Responsible for:

-   package name
-   package code display
-   parent plan
-   template
-   method
-   contract type
-   schedule
-   risk profile
-   KPI profile
-   decision criteria
-   vendor management profile
-   workflow status display

Demand lines should not be deeply edited in the form.

The form may show:

Demand Assignment

Assigned demands: 3

Total assigned value: 5,000,000

\[Open Planning Workbench\]

If unsaved:

Save this package before assigning demand.

**18.2 Planning workbench**

Purpose:

Operate on packages.

Responsible for:

-   assigning demand lines
-   removing demand lines
-   package queues
-   package approval workflow
-   readiness and release actions
-   plan submission/approval context

This prevents duplicate controls and confusion.

**19\. Naming rules**

Use clear labels.

| **Avoid** | **Use** |
| --- | --- |
| Structure | Complete Package |
| Ready | Ready for Tender |
| Release | Release to Tender |
| Approved | Approved Package / Approved Plan, where context may be ambiguous |
| Demand Lines tab | Demand Assignment |

**20\. Status display rules**

Always show both statuses when relevant:

Plan Status: Draft

Package Status: Approved

If package is blocked by plan status:

Ready for Tender — blocked by plan approval

If plan submission is blocked:

Plan cannot be submitted until all packages are approved.

Do not leave users guessing.

**21\. Blocker messages**

**21.1 Plan submission blocked**

Cannot submit plan.

All packages must be approved before submitting the procurement plan.

Detailed:

Unapproved packages:

\- PKG-MOH-2026-001 — Completed

\- PKG-MOH-2026-002 — Submitted

**21.2 Complete package blocked**

Cannot complete package.

Missing: Demand lines, decision criteria, risk profile.

**21.3 Submit package blocked**

Cannot submit package.

Package must be completed before submission.

**21.4 Mark ready blocked**

Cannot mark ready for tender.

Package must be approved first.

**21.5 Release blocked**

Cannot release to tender.

The procurement plan must be approved first.

**22\. Backend enforcement rules**

Do not rely on UI.

Server-side must enforce:

-   package completeness
-   package transitions
-   plan submission conditions
-   plan approval conditions
-   release-to-tender conditions
-   role permission checks
-   separation-of-duty rules if implemented
-   audit history for all transitions

**23\. Audit rules**

Every state transition must record:

-   object type: Plan or Package
-   object code
-   previous state
-   new state
-   actor
-   timestamp
-   reason, if required
-   blocker reasons, if failed attempt logging is implemented

Reason required for:

-   return package
-   reject package
-   return plan
-   reject plan
-   admin override
-   release reversal, if ever supported

# Cursor Implementation Pack

**Global instruction**

Implement the Procurement Planning Plan/Package governance model exactly as specified.

This is a governance, workflow, validation, and UI-action correction.

Do NOT weaken the strict rule:  
A procurement plan cannot be submitted unless all active packages in that plan are Approved.

Do NOT allow Release to Tender unless:

-   parent plan is Approved
-   package is Ready for Tender

Do NOT rely only on frontend disabling. Enforce all rules server-side.

**Ticket 1 — Normalize package statuses and labels**

Normalize package statuses and user-facing labels.

Required package states:

-   Draft
-   Completed
-   Submitted
-   Approved
-   Ready for Tender
-   Released to Tender
-   Returned
-   Rejected

Rename user-facing action:

-   Structure → Complete Package
-   Release → Release to Tender
-   Demand Lines tab → Demand Assignment

Ensure status labels distinguish package status from plan status where ambiguity exists.

Acceptance:

-   no user-facing "Structure" label remains
-   package and plan approvals are not visually confused

**Ticket 2 — Implement package completeness validation**

Implement package completeness validation.

A package can become Completed only if:

-   package name exists
-   procurement plan exists
-   template exists
-   procurement method exists
-   contract type exists
-   at least one active demand line exists
-   estimated value > 0
-   risk profile exists
-   KPI profile exists
-   decision criteria profile exists
-   vendor management profile exists
-   method override reason exists if method\_override\_flag is true
-   schedule exists if required by template

Return specific missing items when validation fails.

Acceptance:

-   incomplete packages cannot become Completed
-   error message lists missing requirements

**Ticket 3 — Implement Add Demand Lines workflow**

Implement Add Demand Lines as a first-class package workbench action.

Add visible action:

-   Add Demand Lines

Places:

-   package detail panel
-   demand lines empty state
-   optional link from package form Demand Assignment tab

Behavior:

-   open modal/side panel
-   list eligible DIA demands
-   allow multi-select
-   create Procurement Package Line records
-   prevent duplicate assignment
-   update package estimated value
-   refresh package completeness

Eligible demands:

-   approved / planning-ready DIA demands only
-   same entity/fiscal year context
-   not already fully assigned to another package
-   valid budget line linkage

Acceptance:

-   planner can add demand lines from workbench
-   package estimated value updates immediately
-   no duplicate demand assignment

**Ticket 4 — Enforce package workflow transitions**

Implement package workflow transition rules.

Allowed transitions:

-   Draft → Completed
-   Completed → Submitted
-   Submitted → Approved
-   Submitted → Returned
-   Submitted → Rejected
-   Returned → Completed or Submitted, depending correction flow
-   Approved → Ready for Tender
-   Ready for Tender → Released to Tender, only if parent plan Approved

Rules:

-   Submitted packages locked to planner edits
-   Approved packages locked against material edits
-   Ready packages locked
-   Released packages locked

Acceptance:

-   invalid package transitions blocked server-side
-   valid transitions update audit/status history

**Ticket 5 — Enforce strict plan submission rule**

Enforce strict plan submission rule.

A plan can be submitted only if:

-   plan status is Draft or Returned
-   plan has at least one active package
-   every active package has status Approved

If any package is not Approved:

-   block submission
-   return list of blocking packages with code, name, and status

UI:

-   Submit Plan button disabled when blocked
-   tooltip/message:  
    "All packages must be approved before submitting the procurement plan."

Acceptance:

-   plan cannot be submitted with Draft/Completed/Submitted/Returned/Rejected packages
-   backend blocks direct API attempts too

**Ticket 6 — Enforce plan approval validation**

Enforce plan approval validation.

A plan can be approved only if:

-   plan status is Submitted
-   all active packages are still Approved
-   no package has been materially changed after approval

Material package fields include:

-   demand lines
-   estimated value
-   template
-   method
-   contract type
-   risk profile
-   KPI profile
-   decision criteria
-   vendor management profile

Acceptance:

-   stale or changed packages block plan approval
-   approved plan is locked

**Ticket 7 — Enforce Ready for Tender and Release to Tender gating**

Implement readiness and release gating.

Mark Ready for Tender allowed only if:

-   package status = Approved
-   package completeness still valid

Release to Tender allowed only if:

-   parent plan status = Approved
-   package status = Ready for Tender
-   package has not already been released
-   package still passes release validation

If plan is not approved:

-   show "Ready for Tender — blocked by plan approval"
-   hide or disable Release to Tender

Acceptance:

-   Ready for Tender does not release package
-   Release to Tender is impossible before plan approval

**Ticket 8 — Separate plan actions from package actions in UI**

Refactor UI action placement.

Plan actions belong only in the plan context bar:

-   Submit Plan
-   Approve Plan
-   Return Plan
-   Reject Plan

Package actions belong only in package detail/work area:

-   Edit Package
-   Add Demand Lines
-   Complete Package
-   Submit Package
-   Approve Package
-   Return Package
-   Reject Package
-   Mark Ready for Tender
-   Release to Tender

Do not mix plan-level and package-level actions.

Acceptance:

-   user can clearly distinguish plan action vs package action
-   no duplicate or misplaced action buttons

**Ticket 9 — Improve blocked-action messaging**

Implement clear blocked-action messaging.

Required messages:

-   Plan submit blocked:  
    "All packages must be approved before submitting the procurement plan."
-   Package complete blocked:  
    "Cannot complete package. Missing: ..."
-   Package submit blocked:  
    "Package must be completed before submission."
-   Ready blocked:  
    "Package must be approved before it can be marked Ready for Tender."
-   Release blocked:  
    "Procurement plan must be approved before releasing packages to tender."

Acceptance:

-   disabled actions explain why
-   backend errors return actionable blocker codes

**Ticket 10 — Add governance audit/history**

Add or verify governance audit/history for plan and package transitions.

Each transition must record:

-   object type
-   object code
-   previous state
-   new state
-   actor
-   timestamp
-   reason if applicable

Reasons required for:

-   return package
-   reject package
-   return plan
-   reject plan
-   admin override

Acceptance:

-   transition history is complete and visible to authorized users

**Ticket 11 — Role and permission enforcement**

Enforce role permissions for plan/package governance.

Package:

-   Planner creates/edits Draft/Returned and submits
-   Procurement Manager / Head of Procurement approves/returns/rejects packages
-   Procurement Officer may mark Ready for Tender if allowed
-   Auditor read-only
-   Admin override audited

Plan:

-   Planner submits only when all packages Approved
-   Finance/Program reviewers may view/recommend if implemented
-   Approving Authority approves/returns/rejects plan
-   Auditor read-only
-   Admin override audited

Acceptance:

-   unauthorized transitions blocked server-side
-   UI shows only valid actions by role/state

**Ticket 12 — Smoke tests for plan/package governance**

Implement smoke tests for the plan/package governance model.

Test scenarios:

1.  cannot complete package without demand lines
2.  can add demand lines from workbench
3.  package value recalculates from demand lines
4.  can complete package when required fields exist
5.  can submit completed package
6.  package approver can approve package
7.  plan submission blocked if any package not Approved
8.  plan submission allowed when all packages Approved
9.  plan approval succeeds after valid submission
10.  package can be marked Ready for Tender only after package approval
11.  Release to Tender blocked if plan not Approved
12.  Release to Tender allowed only when plan Approved + package Ready
13.  returned/rejected actions require reason
14.  approved package cannot be materially edited
15.  plan/package action visibility respects roles

Acceptance:

-   all tests pass
-   no direct API bypass is possible

**Final acceptance gate**

This governance refactor is complete only if:

-   no plan can be submitted with unapproved packages
-   no package can release to tender before plan approval
-   package approval and plan approval are clearly distinct
-   Add Demand Lines is visible and functional
-   Complete Package replaces ambiguous “Structure”
-   blocked actions provide clear reasons
-   plan actions and package actions are visually separated
-   server-side validation enforces all rules
-   smoke tests cover the key failures and happy paths