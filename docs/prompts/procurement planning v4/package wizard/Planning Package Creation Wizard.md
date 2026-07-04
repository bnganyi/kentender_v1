**Planning Package Creation Wizard — UX Design Specification**

**1\. Purpose**

The Planning Package Creation Wizard helps a procurement planner create a procurement package from eligible approved demands.

It should guide the planner through a simple, controlled process:

Approved funded demand  
→ active procurement plan  
→ selected demand(s)  
→ configured package  
→ reviewed package summary  
→ package created

The wizard must prevent users from creating unsupported, unfunded, or untraceable packages.

The wizard should feel like a guided procurement assistant, not a raw form.

**2\. What the Wizard Is For**

The wizard is used to create a procurement package.

A procurement package is the internal planning bundle that will later be reviewed, checked for readiness, and released to Tender Management.

The wizard answers:

Which approved demands should be packaged?

Are those demands eligible?

Which procurement plan owns the package?

What category and method should the package use?

What budget/funding will support the package?

What package lines or lots will be created?

Is the package ready to be created?

What happens next?

**3\. What the Wizard Is Not For**

The wizard is not for:

creating raw demands;

approving departmental demand;

creating a procurement plan;

approving a budget;

publishing tenders;

receiving bids;

evaluating bids;

creating contracts;

manually creating draft tenders.

The wizard only creates a planning package.

Tender Management takes over after the package is later approved and released.

**4\. Entry Points**

The wizard may be opened from several places, but the behavior should remain consistent.

| **Entry Point** | **Expected Context** |
| --- | --- |
| Planning Workbench → Create Package | Active plan already selected |
| Needs Planning queue → Create Package | Demand may already be selected |
| Added to Active Plan success state → Create Package | Demand is pre-selected |
| Procurement Plan detail → Create Package | Active plan or selected plan is known |
| Package dashboard / hub → Create Package | User must select active plan and eligible demand |

Preferred primary button label:

Create Package

Acceptable expanded label:

Create Package from Planned Demands

Avoid:

New Package

unless the wizard clearly explains that packages are created from eligible planned demands, not from nothing.

**5\. Eligibility Rule**

The wizard must only package eligible demands.

A demand is eligible if:

it is approved;

it is funding-cleared or funding-reserved;

it belongs to the selected procuring entity;

it belongs to the selected fiscal year;

it is added to the active procurement plan, or can be added as part of the wizard if the product allows that shortcut;

it has at least one approved demand item;

it is not already fully packaged;

it is not cancelled, rejected, superseded, or blocked by finance/governance.

Recommended eligibility message:

Only approved, funded demands in the active procurement plan are shown.

If the design allows “Add to Active Plan” inside the wizard, use:

Only approved and funded demands are shown. Demands not yet in the active plan will be added before the package is created.

However, the cleaner UX is:

Add demand to active plan first.

Then create package.

**6\. Recommended Wizard Steps**

Use a three-step wizard.

Step 1: Select Demands

Step 2: Configure Package

Step 3: Review and Create

Optional Step 4 may appear only after creation as a success screen:

Package Created

**7\. Wizard Header**

The wizard header should always show:

Wizard title

active procurement plan

fiscal year

procuring entity

current step

save draft option, if supported

Example:

Create Package

Active Plan: Ministry of Health Procurement Plan FY 2026/2027

Ministry of Health · FY 2026/2027 · KES

Step 1 of 3: Select Demands

Actions:

Cancel

Save Draft

Next

**8\. Step 1 — Select Demands**

**8.1 Purpose**

The planner selects one or more eligible demands to include in the package.

This step should make it easy to understand what can be packaged and why.

**8.2 Page Copy**

Title:

Select Demands

Subtitle:

Select approved, funded demands from the active procurement plan to include in this package.

Eligibility note:

Only approved, funded demands in the active procurement plan are shown.

**8.3 Demand Card Data**

Each demand card should show:

| **Field** | **User-Friendly Label** |
| --- | --- |
| Demand title | Demand |
| Demand reference | Ref |
| Requesting department | Department |
| Procurement category | Category |
| Estimated value | Estimated Value |
| Funding status | Funding |
| Strategy link | Strategy |
| Need-by date | Needed By |
| Attachments | Documents |
| Current planning status | Status |

Example card:

District Hospital Renovation Works

Ref: DEM-MOH-2026-001

Works · KES 98,000,000

Department: Infrastructure Services

Funding: Reserved

Strategy: Hospital Infrastructure Improvement

Status: Added to Active Plan

Needed by: Q2 FY 2026/2027

\[Select\]

**8.4 Selection Rules**

The user may select one or more demands if the system allows grouped packages.

For the baseline WORKS flow, one demand may create one package.

If multiple demands are selected, the system must check compatibility.

Compatibility checks:

same procuring entity;

same fiscal year;

compatible category;

compatible procurement method;

compatible funding source rules;

compatible delivery/procurement timeline;

no confidentiality conflict;

no donor/funding restriction conflict;

no package value threshold conflict.

If incompatible, show a clear message:

These demands cannot be packaged together because they use different procurement categories.

or:

These demands cannot be packaged together because one is donor-funded and requires a different procurement process.

**8.5 Right Pane: Selection Summary**

The right pane should summarize selected demands.

Show:

selected demand count;

total estimated value;

category mix;

funding status;

blockers or warnings;

recommended next step.

Example:

Package Selection Summary

Selected Demands: 1

Total Estimated Value: KES 98,000,000

Category: Works

Funding: Reserved

Blockers: None

Next: Configure package details.

**8.6 Empty State**

If no demands are available:

No eligible demands are available for packaging.

Possible reasons:

no approved demands;

no active procurement plan;

funding not confirmed;

all approved demands are already packaged;

your role does not have access.

Actions:

View Approved Demands

Open Workbench

Change Plan

**9\. Step 2 — Configure Package**

**9.1 Purpose**

The planner defines the procurement package details.

This step converts selected demand(s) into a package structure.

**9.2 Page Copy**

Title:

Configure Package

Subtitle:

Confirm the package title, method, category, funding, lots, and document path before creation.

**9.3 Package Identity Section**

Fields:

| **Field** | **Required** | **Notes** |
| --- | --- | --- |
| Package Title | Yes | Default from selected demand title |
| Package Description | Optional | Short business description |
| Package Owner | Yes | Defaults to current planner or planning unit |
| Target Release Date | Optional / Recommended | Used for planning schedule |
| Package Priority | Optional | Normal, High, Emergency |

Recommended default title:

District Hospital Renovation Works

**9.4 Category and Method Section**

Fields:

| **Field** | **Required** | **Notes** |
| --- | --- | --- |
| Procurement Category | Yes | Goods, Works, Services, Consultancy |
| Procurement Method | Yes | Open Tender, Restricted Tender, RFQ, etc. |
| Method Basis | Yes | System-derived, threshold-based, user-selected, override |
| Method Justification | Conditional | Required if user overrides recommended method |
| Contract Type Expectation | Optional | Works contract, supply contract, service contract, framework, etc. |

User-friendly labels:

Category

Procurement Method

Why this method?

Override Reason

Recommended copy:

Recommended method: Open Tender

Reason: Package value and category require an open competitive process.

**9.5 Funding Section**

Fields:

| **Field** | **Required** | **Notes** |
| --- | --- | --- |
| Budget Line | Yes | Inherited from selected demand |
| Funding Status | Yes | Reserved, available, insufficient, blocked |
| Reserved Amount | Conditional | If reservation exists |
| Package Estimated Value | Yes | Sum of package lines |
| Funding Difference | Yes | Shows over/under difference |
| Funding Blockers | Conditional | Shown if insufficient or missing |

Recommended display:

Funding

Budget line: Health Infrastructure Renovation

Reserved amount: KES 98,000,000

Package value: KES 98,000,000

Difference: KES 0

Status: Funding reserved

**9.6 Lines and Lots Section**

The wizard should create package lines from demand items.

Baseline behavior:

Each selected demand item becomes a package line unless the user intentionally groups or splits lines.

Fields:

| **Field** | **Required** | **Notes** |
| --- | --- | --- |
| Line Title | Yes | Defaults from demand item |
| Source Demand Item | Yes | Traceability required |
| Scope / Quantity | Yes | From demand item |
| Estimated Value | Yes | From demand item |
| Budget Line | Yes | Inherited |
| Lot Group | Optional | If lots are used |
| Delivery Location | Optional / Conditional | Useful for works/services |

User actions:

Edit line title;

confirm scope;

group into lot;

split line, if allowed;

remove line, if allowed and justified.

For baseline simplicity, avoid splitting demand items unless the system explicitly supports it.

**9.7 Document / STD Path Section**

Fields:

| **Field** | **Required** | **Notes** |
| --- | --- | --- |
| Required Document Family | Conditional | Works, Goods, Services, Consultancy |
| Standard Tender Document Path | Conditional | Required before release, may be selected later |
| Specification Attachments | Conditional | Inherited from demand |
| Missing Documents | Conditional | Shown as warnings/blockers |

Recommended copy:

Required document path: Works Open Tender

Specifications: 3 documents inherited from demand

Missing: None

**9.8 Configuration Warnings**

Warnings should be business-readable.

Examples:

Package value exceeds reserved funding.

Procurement method override requires justification.

One selected demand has missing specifications.

Tender document path has not been selected.

This demand is not yet added to the active plan.

Do not show raw technical codes as the main warning.

**10\. Step 3 — Review and Create**

**10.1 Purpose**

The planner reviews the package before creation.

This page should show a concise, confidence-building summary.

**10.2 Page Copy**

Title:

Review and Create Package

Subtitle:

Confirm the package details before creating the procurement package.

**10.3 Review Sections**

**Package Summary**

Show:

package title;

active procurement plan;

procuring entity;

fiscal year;

category;

method;

estimated value;

package owner;

target release date.

**Selected Demands**

Show:

number of selected demands;

demand titles;

departments;

estimated values;

funding status;

strategy links.

**Lines and Funding**

Show:

number of package lines;

total package value;

budget line;

reserved amount;

difference;

funding status.

**Readiness Preview**

Show pre-creation checks:

approved demand selected;

active procurement plan exists;

funding linked/reserved;

category selected;

method selected;

package lines will be created;

documents inherited or identified.

Use clear statuses:

Ready

Warning

Blocked

**10.4 Final Create Button**

Primary action:

Create Package

Secondary actions:

Back

Save Draft

Cancel

Disable Create Package if blocking issues exist.

**10.5 Blocking Conditions**

The Create Package button must be blocked if:

no demand selected;

no active procurement plan;

selected demand is not approved;

selected demand is not funding-cleared or funding-reserved;

selected demand is already fully packaged;

package title is missing;

procurement category is missing;

procurement method is missing;

package value exceeds allowed funding context;

package line cannot be created from demand item;

user lacks permission.

**11\. Success Screen — Package Created**

**11.1 Purpose**

The success screen should immediately tell the user what happened and what to do next.

**11.2 Success Message**

Package created.

District Hospital Renovation Works has been created as a procurement package under:

Ministry of Health Procurement Plan FY 2026/2027

Next step:

Complete package readiness and submit for review.

Actions:

Open Package

Back to Workbench

View Evidence

**11.3 Post-Creation State**

After package creation:

the selected demand should no longer appear as “Needs Planning”;

the created package should appear under “In Creation”;

the package should have status “Package in creation”;

the package should be linked to the active plan;

package lines should be linked to demand items and budget lines;

evidence should be recorded.

**12\. Data Created by the Wizard**

The wizard should create or update these user-facing records.

**12.1 Procurement Package**

User-friendly data:

| **Field** | **Meaning** |
| --- | --- |
| Package Title | Name of the package |
| Active Plan | Plan that owns the package |
| Linked Demand(s) | Approved demand(s) included |
| Category | Goods, Works, Services, Consultancy |
| Method | Procurement method |
| Estimated Value | Total planned value |
| Budget Status | Funding linked/reserved/blocked |
| Package Status | Package in creation |
| Owner | Planner responsible |
| Target Release Date | Intended release timing |
| Attachments | Documents inherited from demand |
| Evidence | Package creation record |

**12.2 Package Lines**

User-friendly data:

| **Field** | **Meaning** |
| --- | --- |
| Line Title | Name of the package line |
| Source Demand Item | Demand item the line came from |
| Scope / Quantity | What is being procured |
| Estimated Value | Line value |
| Budget Line | Funding source |
| Lot Group | Lot grouping, if applicable |
| Location | Delivery/work location |
| Status | Draft / Complete |

**12.3 Planning Evidence**

Evidence created:

package creation event;

selected demand reference;

active plan reference;

budget/funding reference;

package line creation event;

method/category decision;

wizard completion record;

audit timestamp and actor.

Do not show these technical records as the default UI.

Expose them through View Evidence.

**13\. Roles and Permissions**

| **Role** | **Wizard Access** |
| --- | --- |
| Procurement Planner | Can create packages from eligible planned demands |
| Planning Reviewer | Can view wizard output and package details; may not create unless configured |
| Procurement Authority | Can create or approve packages if configured |
| Finance / Budget User | Can view funding context and resolve funding blockers |
| Department User | Can view own demand’s planning status; cannot create package unless configured |
| Auditor | Can view evidence |
| Supplier | No access |

Permission rules:

Only authorized internal users can create packages.

Users can only package demands within their entity/access scope.

Users cannot package supplier-private or restricted records unless authorized.

Supplier users must never access internal planning package creation.

**14\. Validation and Error Messages**

Use simple business-readable messages.

| **Situation** | **Message** |
| --- | --- |
| No active plan | Create or activate a procurement plan before creating packages. |
| No demand selected | Select at least one eligible demand. |
| Demand not approved | This demand is not approved for planning yet. |
| Funding missing | Funding has not been confirmed for this demand. |
| Funding insufficient | Package value exceeds available or reserved funding. |
| Already packaged | This demand has already been fully packaged. |
| Incompatible demands | These demands cannot be grouped into one package. |
| Missing method | Select or confirm the procurement method. |
| Missing category | Select or confirm the procurement category. |
| Missing title | Enter a package title. |
| Permission denied | You do not have permission to create packages for this plan. |
| Save failed | Package could not be created. Try again or contact support. |

**15\. UX Design Rules**

The wizard should be:

guided;

calm;

short;

decision-oriented;

business-readable;

safe by default.

The wizard should not expose:

Planning Inclusion technical codes;

Release Package codes;

source object;

target object;

JSON data;

handoff IDs;

raw DocType names;

audit IDs as primary content.

Use business labels:

Active Plan

Selected Demands

Package Value

Funding Reserved

Procurement Method

Package Lines

Ready to Create

Create Package

Open Package

View Evidence

**16\. Recommended Layout Pattern**

Use a two-column wizard layout.

Left / Main Area:

current step content;

demand cards;

package fields;

review summary.

Right Pane:

selection summary;

package value;

funding status;

blockers/warnings;

next action.

Footer:

Back

Cancel

Save Draft

Next

Create Package

Example structure:

Header:  
Create Package  
Active Plan: Ministry of Health Procurement Plan FY 2026/2027

Stepper:  
1 Select Demands  
2 Configure Package  
3 Review and Create

Main:  
Step-specific content

Right Pane:  
Package Summary  
Selected Demands  
Estimated Value  
Funding Status  
Warnings

Footer:  
Back · Cancel · Save Draft · Next

**17\. No-Go Conditions**

The wizard fails if:

users can create packages from nothing;

users can package unapproved demands;

users can package unfunded demands without explicit exception handling;

users can package demands without an active procurement plan;

technical handoff records appear in the main wizard UI;

users are forced into raw Frappe forms;

the wizard creates a tender directly instead of a planning package;

the user finishes the wizard but does not know the next step;

the demand remains incorrectly shown as “Needs Planning” after package creation;

package lines are not traceable to demand items and budget lines.

**18\. Final Product Rule**

The Package Creation Wizard succeeds if a normal procurement planner can:

open Create Package;

see the active procurement plan;

select eligible approved funded demand(s);

confirm package title, category, method, lines, value, and funding;

review the package summary;

create the package;

open the package for readiness and review;

view evidence only when needed.

The wizard should make package creation feel controlled and simple, while the system silently preserves the legal traceability required for audit and downstream tendering.