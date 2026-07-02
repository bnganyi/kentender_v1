**Procurement Planning — Simplified UX and Workflow Specification**

**1\. Purpose of This Document**

This document defines the simplified user experience for the Procurement Planning module.

It is intended for UI/UX design and product refinement. It describes the full user journey, including procurement plan creation, demand planning, package creation, readiness, review, release to Tender Management, and the automatic creation of a tender shell.

The goal is to help designers create a coherent set of screens that are usable by normal procurement users while still preserving legal, audit, budget, and handoff controls underneath.

**2\. What Procurement Planning Is**

Procurement Planning is the module where approved, funded demands are converted into procurement packages that are ready to be released to Tender Management.

It answers:

What approved demands are ready for planning?

Is there an active procurement plan for this entity and fiscal year?

Which approved demands should be added to the plan?

Which planned demands should be grouped into a procurement package?

Is the package complete, funded, reviewed, and ready for release?

What package has been released to Tender Management?

Has a tender been created from the released package?

Procurement Planning is not Demand Approval and it is not Tender Management.

Demand Approval decides that a department’s need is valid and fundable.

Procurement Planning decides how that approved demand is organized into a procurement package.

Tender Management handles the supplier-facing tender process after Planning releases the package.

Simple lifecycle:

Strategy  
→ Budget  
→ Demand Intake and Approval  
→ Procurement Planning  
→ Tender Management  
→ Bid Submission  
→ Bid Opening  
→ Evaluation and Award  
→ Contract Management

**3\. Core Product Rule**

Procurement Planning should be designed around work, not internal records.

Normal users should see:

Needs planning

Added to active plan

Package in creation

Awaiting review

Ready for release

Released to Tender Management

Tender created

Blocked

Normal users should not need to understand:

Planning Inclusion Record

Planning Release Package

Tender Consumption Record

handoff object

source object

target object

technical reference

audit object

The system manages technical records silently.

The user manages the work.

**4\. Main Concepts**

Procurement Planning has three main business concepts:

Procurement Plan

Planned Demand

Procurement Package

Their relationship is:

Procurement Plan  
→ Planned Demands  
→ Procurement Packages  
→ Released Package  
→ Tender Shell

In plain language:

A Procurement Plan is the fiscal-year container.

A Planned Demand is an approved demand accepted into the active plan.

A Procurement Package is the actual procurement bundle prepared for tendering.

A Released Package is the approved package handed to Tender Management.

A Tender Shell is the Tender Management record created from the released package.

**5\. Recommended Main UI Surfaces**

Use three primary surfaces:

Planning Workbench

Procurement Plans

Released to Tender

**5.1 Planning Workbench**

The Workbench is the main daily screen.

It answers:

What planning work needs attention, and what should I do next?

It contains:

Active procurement plan card

Work queues

Demand/package cards

Selected work summary

Primary next action

Evidence drawer

**5.2 Procurement Plans**

Procurement Plans is for setup and oversight.

It answers:

Is there an active procurement plan?

Which plan owns this work?

What demands and packages belong to the plan?

What is the plan’s status?

**5.3 Released to Tender**

Released to Tender is for completed Planning outputs.

It answers:

Which packages have been released?

Was a tender created?

Can I open the tender?

Can I view release evidence?

**6\. Procurement Plan Creation and Activation**

**6.1 Why Plan Creation Matters**

A procurement plan must exist before approved demands can be planned and packaged.

The Planning Workbench must always show whether an active procurement plan exists.

Recommended rule:

One active master procurement plan per procuring entity per fiscal year.

Example:

Ministry of Health Procurement Plan FY 2026/2027

There may be revisions, departmental inputs, supplementary additions, or draft plans, but there should not be two competing active master plans for the same entity and fiscal year.

**6.2 If No Active Plan Exists**

The Workbench should show a setup gate:

No active procurement plan exists for FY 2026/2027.

Create or activate a procurement plan before planning approved demands.

Actions:

Create Plan

Activate Existing Plan

In this state, the user should not be able to create procurement packages.

**6.3 Create Plan Workflow**

Workflow:

Create Draft Plan  
→ Submit Plan  
→ Approve and Activate Plan  
→ Active Plan

For simple deployments, approval and activation can be one action:

Planning Authority approves = plan becomes active.

**Create Plan Data**

User-friendly fields:

| **Field** | **Meaning** |
| --- | --- |
| Plan Title | Name of the procurement plan |
| Procuring Entity | Organization that owns the plan |
| Fiscal Year | Planning year |
| Currency | Budget currency |
| Plan Type | Annual, Supplementary, Revision |
| Description | Optional plan description |
| Plan Owner | Responsible planning office/person |
| Status | Draft, Submitted, Active, Closed, Revised, Cancelled |

Example:

Plan Title: Ministry of Health Procurement Plan FY 2026/2027

Procuring Entity: Ministry of Health

Fiscal Year: 2026/2027

Currency: KES

Plan Type: Annual

Status: Active

**6.4 Plan Approval Roles**

| **Role** | **Responsibility** |
| --- | --- |
| Procurement Planner | Creates draft plan |
| Planning Reviewer | Checks plan completeness |
| Planning Authority | Approves and activates plan |
| System | Locks active baseline and records evidence |

Recommended simplified flow:

Planner creates plan  
→ Reviewer reviews  
→ Planning Authority approves and activates  
→ System records active plan evidence

**6.5 Procurement Plan Screen UX**

Procurement Plans screen should show:

Plan list

Active plan status

Plan totals

Included demands

Packages under the plan

Released packages

Plan evidence

Recommended actions:

Create Plan

Submit Plan

Approve and Activate

Close Plan

Request Revision

Open in Workbench

View Evidence

**7\. Active Plan Card in the Workbench**

The Planning Workbench must always show active plan context.

Example:

Active Procurement Plan

Ministry of Health Procurement Plan FY 2026/2027

Ministry of Health · 2026/2027 · KES

Actions:

Change Plan

View Plan

Request Revision

If no active plan exists, show the no-active-plan gate instead.

**8\. Work Queues**

The Planning Workbench should use status-based work queues.

Recommended queues:

Needs Planning

In Creation

Awaiting Review

Ready for Release

Blocked

Released

**8.1 Queue Meanings**

| **Queue** | **Meaning** | **Typical Item** | **Main Action** |
| --- | --- | --- | --- |
| Needs Planning | Approved funded demands not yet converted into planning/package work | Approved demand | Add to Active Plan or Create Package |
| In Creation | Draft packages being prepared | Procurement package | Open Package |
| Awaiting Review | Packages submitted for review | Procurement package | Review Package |
| Ready for Release | Packages approved and readiness-passed | Procurement package | Release to Tender Management |
| Blocked | Demands/packages with missing funding, scope, method, documents, or approval | Demand or package | Resolve Blocker |
| Released | Packages released to Tender Management | Released package / tender shell | Open Tender |

Queues are not separate modules. They are filters inside one Planning Workbench.

**9\. Full Workflow**

**9.1 End-to-End Flow**

The complete Procurement Planning flow is:

Active plan exists or is created  
→ Approved demand appears in Needs Planning  
→ Planner adds demand to active plan  
→ Planner creates package from planned demand  
→ Planner completes package details  
→ System/planner runs readiness checks  
→ Planner submits package for review  
→ Reviewer approves or returns package  
→ Procurement Authority releases package  
→ System locks released package baseline  
→ System creates tender shell automatically  
→ Tender Management takes over publication setup

**9.2 Step 1 — Confirm or Create Active Plan**

Actor:

Procurement Planner / Planning Authority

Action:

Create or activate procurement plan.

Result:

Active plan exists and Planning Workbench is enabled.

User-facing status:

Active plan available.

**9.3 Step 2 — Approved Demand Enters Planning**

Actor:

System

Source:

Demand Intake and Approval

Condition:

Demand must be approved and funding-cleared or funding-reserved.

Result:

Demand appears in Needs Planning.

User-facing status:

Needs planning

Main action:

Add to Active Plan

**9.4 Step 3 — Add Demand to Active Plan**

Actor:

Procurement Planner

Action:

Add approved demand to active procurement plan.

Result:

Demand becomes a planned demand.

User-facing status:

Added to active plan

Next action:

Create Package

Important UX rule:

After a demand is added to the active plan, it must no longer appear as if it still needs planning.

Do not continue showing:

Planning pending

Add to Active Plan

for a demand that has already been added to the active plan.

**9.5 Step 4 — Create Package**

Actor:

Procurement Planner

Action:

Create package from one or more eligible planned demands.

Result:

Draft package exists.

User-facing status:

Package in creation

Next action:

Open Package

Package creation must start from eligible planned demands, not from a blank package.

Eligibility:

approved demand

funding-cleared or funding-reserved

added to active procurement plan

not already fully packaged

within user’s entity/fiscal-year scope

**9.6 Step 5 — Complete Package**

Actor:

Procurement Planner

Action:

Complete package details.

The planner confirms:

package title

linked demand(s)

package lines

scope

category

method

estimated value

funding reference

attachments/specifications

standard tender document path where applicable

Result:

Package is ready for readiness checks.

User-facing status:

Package in creation

**9.7 Step 6 — Run Readiness Checks**

Actor:

Procurement Planner / System

Action:

Run package readiness.

Readiness checks confirm:

approved demand exists

demand is added to active plan

funding is linked or reserved

package lines exist

package lines map to demand items

package total is valid

category is selected

method is selected

required documents are attached or identified

review requirements are satisfied

release handoff can be generated

Result:

Readiness Passed or Readiness Failed.

If failed, item may appear in Blocked.

**9.8 Step 7 — Submit for Review**

Actor:

Procurement Planner

Action:

Submit package for review.

Result:

Package moves to Awaiting Review.

User-facing status:

Awaiting review

**9.9 Step 8 — Review Package**

Actor:

Planning Reviewer / Procurement Reviewer

Action:

Review package for completeness, funding traceability, method/category, scope, readiness, and compliance.

Possible decisions:

Approve

Return for Correction

Reject or Cancel, where allowed

Result:

Approved package or returned package.

User-facing status:

Ready for release, if approved and readiness-passed.

Returned, if corrections are needed.

**9.10 Step 9 — Release to Tender Management**

Actor:

Procurement Authority

Action:

Release approved and readiness-passed package to Tender Management.

Result:

Package baseline is locked.

Release evidence is created.

Tender shell is created automatically.

Planning ownership ends.

User-facing status:

Released to Tender Management

Tender created

Recommended UI message:

Package released to Tender Management.

Tender created.

Next: Continue in Tender Management.

Actions:

Open Tender

View Evidence

Do not make planners manually manage a “draft tender.”

Tender publication setup belongs to Tender Management.

**10\. User-Friendly Data Model**

**10.1 Procurement Plan**

A Procurement Plan is the annual/fiscal-year container for planning work.

User-friendly fields:

| **Field** | **Meaning** |
| --- | --- |
| Plan Title | Name of the plan |
| Procuring Entity | Organization that owns the plan |
| Fiscal Year | Year covered by the plan |
| Currency | Currency for planned values |
| Plan Type | Annual, Supplementary, Revision |
| Plan Owner | Responsible planning office/person |
| Status | Draft, Submitted, Active, Closed, Revised, Cancelled |
| Total Planned Value | Sum of planned package values |
| Number of Planned Demands | Count of demands added to the plan |
| Number of Packages | Count of packages under the plan |
| Number Released | Count of packages released to Tender Management |
| Created By / Date | Audit information |
| Approved By / Date | Approval information |
| Active From | When plan became active |
| Evidence | Approval, activation, revision, closure evidence |

**10.2 Planned Demand**

A Planned Demand is an approved demand that has been accepted into the active procurement plan.

User-friendly fields:

| **Field** | **Meaning** |
| --- | --- |
| Demand Title | Name of the approved demand |
| Requesting Department | Department that requested the need |
| Category | Goods, Works, Services, Consultancy |
| Estimated Value | Approved estimated value |
| Budget Status | Funding linked, reserved, insufficient, blocked |
| Budget Line | Linked funding source |
| Strategy Link | Strategic objective/programme reference |
| Planning Status | Needs planning, Added to active plan, Packaged, Released |
| Added to Plan By / Date | Who added it and when |
| Package Status | Not packaged, Partially packaged, Fully packaged |
| Attachments | Scope, specification, drawings, memos |
| Evidence | Demand approval, funding decision, planning inclusion evidence |

**10.3 Procurement Package**

A Procurement Package is the procurement bundle prepared for tendering.

User-friendly fields:

| **Field** | **Meaning** |
| --- | --- |
| Package Title | Human-readable package name |
| Active Plan | Procurement plan that owns the package |
| Linked Demand(s) | Planned demand(s) included |
| Procuring Entity | Owning entity |
| Fiscal Year | Planning year |
| Category | Goods, Works, Services, Consultancy |
| Procurement Method | Open tender, restricted tender, quotation, etc. |
| Estimated Value | Total planned value |
| Budget Status | Linked, reserved, insufficient, blocked |
| Package Status | In creation, Awaiting review, Ready for release, Released |
| Readiness Status | Not checked, Passed, Failed, Stale |
| Review Status | Not submitted, Awaiting review, Approved, Returned |
| Tender Status | Not created, Tender created, Published |
| Owner | Planner responsible |
| Attachments | Specifications, scope, supporting documents |
| Evidence | Package creation, readiness, review, release evidence |

**10.4 Package Line**

A Package Line is a specific item, work, service, lot, or scope component inside the package.

User-friendly fields:

| **Field** | **Meaning** |
| --- | --- |
| Line Title | Description of the line |
| Source Demand Item | Approved demand item it came from |
| Category | Goods, Works, Services, Consultancy |
| Estimated Value | Value of the line |
| Budget Line | Funding source |
| Location | Delivery or work location |
| Scope / Quantity | Quantity, scope, or work description |
| Lot Group | Lot or grouping, if used |
| Status | Draft, Complete, Released |
| Evidence | Traceability to demand and budget |

**10.5 Readiness Result**

Readiness Result records whether the package is complete enough to proceed.

User-friendly fields:

| **Field** | **Meaning** |
| --- | --- |
| Readiness Status | Not checked, Passed, Failed, Stale |
| Checks Passed | Number of passed checks |
| Checks Failed | Number of failed checks |
| Blockers | What must be fixed |
| Last Checked By | User/system that ran checks |
| Last Checked At | Timestamp |
| Next Action | Resolve blockers, submit review, or release |
| Evidence | Readiness record |

**10.6 Review Decision**

Review Decision records approval or return of a package.

User-friendly fields:

| **Field** | **Meaning** |
| --- | --- |
| Review Status | Not submitted, Awaiting review, Approved, Returned |
| Reviewer | Person who reviewed |
| Decision Date | When decision was made |
| Decision | Approved, Returned, Rejected |
| Comments | Reviewer note |
| Required Corrections | What must be fixed |
| Evidence | Review decision record |

**10.7 Release to Tender Management**

Release records the final Planning handoff.

User-friendly fields:

| **Field** | **Meaning** |
| --- | --- |
| Release Status | Not released, Released, Tender created |
| Released Package | Package handed to Tender Management |
| Released By | User who released |
| Released At | Timestamp |
| Locked Values | Scope, method, value, funding, package lines |
| Tender Created | Yes/No |
| Tender Reference | Linked tender record |
| Evidence | Release and handoff evidence |

**10.8 Tender Shell**

Tender Shell is the Tender Management record created after release.

User-friendly fields:

| **Field** | **Meaning** |
| --- | --- |
| Tender Title | Tender name |
| Tender Reference | Tender code/reference |
| Source Package | Released package |
| Status | Preparing for publication, Published, Closed, etc. |
| Tender Manager | User/team responsible |
| Publication Setup Status | Whether tender setup is complete |
| Open Tender Action | Link to Tender Management |

Planning users should only see that the tender was created and can be opened.

Tender Management owns publication setup.

**11\. Package Creation Wizard**

Package creation should be a guided wizard.

Recommended title:

Create Package

Recommended subtitle:

Create a procurement package from eligible planned demands.

**11.1 Step 1 — Select Demands**

Show only eligible demands.

Eligibility message:

Only approved, funded demands in the active procurement plan are shown.

Fields shown:

Demand title

Department

Category

Estimated value

Funding status

Planning status

Attachments indicator

Main action:

Select Demand

**11.2 Step 2 — Configure Package**

Fields:

Package title

Procurement category

Procurement method

Package lines/lots

Estimated value

STD/document path if required

Target release date

Package owner

Funding confirmation

Main action:

Continue

**11.3 Step 3 — Review and Create**

Show:

Selected demand(s)

Package title

Category

Method

Estimated value

Funding status

Readiness warnings

Attachments summary

Main action:

Create Package

Success message:

Package created.

Next: Complete package details and readiness.

Open Package

**12\. Package Detail UX**

Package Detail should answer:

What is this package?

What demand(s) does it contain?

Is funding linked?

Is the method/category correct?

What is missing?

Who needs to act?

What is the next action?

Recommended tabs:

Overview

Lines and Funding

Readiness

Review

Release

Do not use default tabs for:

Evidence

Technical Details

Audit Trail

Handoff History

Evidence should be opened through:

View Evidence

**13\. Package Detail Tab Content**

**13.1 Overview**

Shows:

package title

linked demand(s)

category

method

estimated value

status

owner

blockers

next action

**13.2 Lines and Funding**

Shows:

package lines

source demand items

budget line

reserved amount

estimated value

funding blockers

**13.3 Readiness**

Shows checks:

Demand approved

Demand added to active plan

Funding linked or reserved

Package lines complete

Method selected

Category selected

Tender document path identified

Review complete

**13.4 Review**

Shows:

review status

reviewer comments

approve/return action

approval history

**13.5 Release**

Shows:

ready to release yes/no

what will be locked

what will be sent to Tender Management

release warning

release action

after release: tender created and open tender action

**14\. Roles and Responsibilities**

| **Role** | **Main Responsibility** |
| --- | --- |
| Procurement Planner | Creates plan, adds demands, creates packages, completes package details |
| Planning Reviewer | Reviews packages and returns or approves |
| Procurement Authority | Approves release to Tender Management |
| Finance / Budget User | Resolves budget blockers and funding questions |
| Department User | Clarifies demand scope or specifications |
| Tender Manager | Takes over after release and prepares tender publication |
| System | Runs checks, locks baselines, creates evidence, creates tender shell |
| Auditor | Reviews evidence and audit trail |

Recommended simplified approval path:

Planner prepares package  
→ Reviewer reviews package  
→ Procurement Authority releases package

**15\. Status Labels**

Use normal-user status labels.

| **Backend Concept** | **User-Friendly Label** |
| --- | --- |
| Approved demand not planned | Needs planning |
| Demand included in plan | Added to active plan |
| Package draft | Package in creation |
| Package submitted | Awaiting review |
| Package returned | Returned |
| Package approved and checks passed | Ready for release |
| Package handed off | Released to Tender Management |
| Tender record created | Tender created |
| Missing required data | Blocked |

Avoid showing technical labels as primary UI:

Planning Inclusion

Planning Release Package

Tender Consumption

Source object

Target object

Technical refs

JSON

Audit object

**16\. Linkages and Handoffs**

**16.1 Upstream Inputs**

Planning receives:

approved demand

demand items

budget line

funding status

reserved amount, if applicable

strategy link

attachments/specifications

approval evidence

**16.2 Downstream Output**

Planning releases:

package title

linked demand(s)

package lines

method

category

estimated value

budget reference

reserved amount

readiness result

review approval

attachments/specifications

release evidence

**16.3 Tender Management Handoff**

On release:

Planning locks package baseline.

System creates tender shell.

Tender Management owns publication setup.

Planning UI shows:

Package released to Tender Management.

Tender created.

Open Tender.

View Evidence.

**17\. Budget Behavior in Planning**

Planning inherits funding status from Demand and Budget.

The planner should see:

Budget linked

Funding reserved

Funding insufficient

Budget blocker

Planning should not perform budget accounting.

Budget controls:

Package value must not exceed funding context.

Funding blockers prevent release.

Budget changes must be handled through Budget Management.

Released package must carry budget reference to Tender Management.

If a budget revision makes funding insufficient:

package becomes Blocked;

blocker explains the issue;

Finance/Budget must resolve it before release.

**18\. Evidence and Audit**

Evidence should exist but should not dominate the UI.

Ordinary users see:

View Evidence

Evidence should include:

demand approval

budget/funding decision

planning inclusion

package creation

package line creation

readiness result

review decision

release to Tender Management

tender shell creation

audit events

Technical users may expand Technical Details if authorized.

Technical Details may show:

internal record IDs

handoff references

locked baseline snapshot

source object

target object

audit reference

**19\. Required User Experience**

The UX should feel like:

one workbench

clear active plan

clear queues

clear package cards

one next action per item

package creation from eligible planned demands

evidence available on request

The UX should not feel like:

a raw Frappe form list

a handoff registry

an audit log

a lifecycle debugger

a set of disconnected menus

a place where users must understand backend object names

**20\. No-Go Conditions**

The UX fails if:

users can create blank packages disconnected from approved demands;

users can package demands without an active procurement plan;

a demand already added to the plan still shows “Add to Active Plan”;

planners must manually create or manage draft tenders;

Planning shows technical handoff records as primary content;

evidence appears before the user asks for it;

there are separate confusing menus for Planning Home, Approved Demands, and Packages;

the active procurement plan is not visible in the Workbench;

the user must understand Planning Inclusion or Release Package to continue.

**21\. Final Product Rule**

Procurement Planning succeeds if a normal procurement planner can:

open the Planning Workbench;

see or create the active procurement plan;

find approved funded demands;

add demand to the active plan;

create a package from eligible planned demands;

complete package details;

run readiness checks;

submit for review;

release the approved package to Tender Management;

open the created tender;

view evidence only when needed.

The UI fails if the user must ask:

Is this a demand screen, a plan screen, a package screen, or a tender screen?

Procurement Planning should hide object complexity and expose the work.