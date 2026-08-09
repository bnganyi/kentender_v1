# Procurement Planning — MVP 1 Stitch Prompts

**Document ID:** PLANNING-MVP1-STITCH-1.4  
**Status:** Approved Stitch design baseline  
**Date:** 9 August 2026  
**Source:** `PLANNING-MVP1-REQ-1.4`  
**Module:** Procurement Planning  

**Revision 1.4:** Retains the corrected registration and Plan Item editor and applies explicit field and evidence types to every remaining prompt.

**Approval note:** Version 1.4 and the HTML outputs `ui_design/PLN-UI-01.html` through `ui_design/PLN-UI-10.html` are the approved visual contract for Procurement Planning MVP 1. Hand-port main-content composition into the existing KenTender Desk shell; do not redesign shell, navigation or branding from these files.

## 1. Purpose

Use these prompts to design the minimum Procurement Planning screens for this journey:

> **Approved Demand → Plan Item → Consolidated Plan Approval → Tender take-up**

The designs must make this journey clear without recreating the previous Inclusion, Package, Release or Consumption workbenches.

These are **Stitch design prompts only**. They define visible layout, hierarchy, labels and representative states. They do not define APIs, validation logic, permissions, workflow implementation or data mutations; those belong in the later Cursor prompt.

## 2. How to use

1. Generate Prompt 01 first to establish the module's content style.
2. Generate each remaining prompt as a separate screen or focused state in the same Stitch project.
3. Keep the real KenTender Procurement shell, sidebar, top bar and branding when bringing the designs into the application.
4. Review one generated screen before moving to the next prompt.
5. Treat the exact business content below as authoritative; do not let Stitch invent extra workflow stages.

## 3. Shared design contract

Apply these instructions to every prompt:

- Design for a desktop public-sector procurement application.
- Focus on the **main content area only**.
- Do not redesign navigation, global toolbars, branding or the Procurement shell.
- Use a clear page title, one-line description and one obvious primary action.
- Prefer compact tables, short forms, restrained status chips and plain-language issue messages.
- Use cards only where they group a real decision or task. Do not create a grid of decorative KPI cards.
- Do not use charts unless a chart is explicitly requested.
- Keep source data readable but visually secondary to the user's current task.
- Use drawers or dialogs for small focused tasks; do not create another workbench.
- Do not show database names, hashes, internal IDs, technical rule codes or raw audit payloads.
- Human-readable references may appear as quiet secondary text.
- Do not ask users to enter Plan, Plan Item, Demand, Budget or Strategy codes.
- Do not expose separate objects named Planning Inclusion, Procurement Package, Package Line, Release Package or Consumption.
- Do not show Passed, Failed, Qualified, Compliant or numeric compliance scores.
- Use business statuses only.
- Identify every interactive element as a text input, multiline input, date input, checkbox, radio group, select, searchable select or button. Identify calculated and inherited content as read-only or derived.
- Treat table values, summary figures, statuses, audit trails and issue messages as read-only unless the prompt explicitly specifies a row-selection control or input.
- Treat every named primary, secondary, footer or row action as a button unless it is explicitly labelled as a link.

### Status vocabulary

Use only the relevant values:

- Logical Plan: Open, Closed, Cancelled
- Plan Version: Draft, In review, Returned, Approved, Superseded, Cancelled
- Plan Item baseline: Proposed, Active, Removed
- Validation: Not run, Ready, Needs attention, Blocked, Stale
- Departmental contribution: Preparing, Submitted, Returned
- Publication: Not submitted, Queued, Published, Failed, Not applicable
- Tender take-up: Not taken up, Tender in preparation, Tender active, Contracted, Closed downstream

### Canonical design data

Use the same story throughout:

- Procuring Entity: Ministry of Health
- Secondary accessible Procuring Entity: County Government of Kisumu
- Financial year: 2027/28
- Plan title: Ministry of Health Annual Procurement Plan 2027/28
- Owner Organisation Unit: Directorate of Digital Health and Policy
- Approved Demand: National digital health infrastructure upgrade
- Demand reference: DMD-MOH-2027-014
- Plan Item reference: PPI-MOH-2027-021
- Amount: KES 455,000,000
- Budget Line: Digital clinical systems infrastructure
- Funding status: Reserved
- Primary Strategy target: At least 99.9% annual availability by 30 June 2028
- Supporting Strategy target: Restore critical services within four hours by 30 June 2028
- Category: ICT infrastructure and services
- Procurement method: Open tender
- Broad STD family: Information Technology
- Arrangement: Single year
- Later Tender reference: TND-MOH-2027-008

Where the screen needs a returned or ineligible example, use:

- Returned Ministry Demand: Digital health technical staff certification programme
- Draft County Demand: Solar-powered vaccine refrigerators for rural health facilities

For the post-approval addition scenario, the returned Ministry Demand is corrected from KES 95,000,000 to KES 80,000,000, approved and added through Draft Revision 2 as Proposed Plan Item PPI-MOH-2027-022. Approved Version 1 remains operational until Revision 2 is approved.

Do not create unrelated ministries, hospitals, budget lines or legacy District Hospital Renovation examples.

---

## Stitch Prompt 01 — PLN-UI-01 Procurement Planning workspace

```text
Design the main content area for the Procurement Planning landing page in an enterprise public-procurement system.

Keep the existing Procurement navigation, top bar and branding unchanged. Do not design a new sidebar.

Header:
- Title: Procurement Planning
- Description: “Turn approved and funded needs into an approved annual procurement plan.”
- Context controls on the right: required searchable Procuring Entity select with “Ministry of Health” selected; required Financial year select with “2027/28” selected
- Helper text: “These controls filter the workspace; they do not assign ownership to new records.”
- Primary action: Open current plan

Immediately below the header, show one compact read-only current-plan panel with derived values:
- Ministry of Health Annual Procurement Plan 2027/28
- Plan lifecycle: Open
- Current version: Draft Version 1
- 0 Plan Items
- KES 0 planned
- Validation: Not run
- Departmental contributions: 0 of 1 submitted
- Action: Continue planning

Below that, show a compact read-only “Work requiring action” table with columns:
- Work item
- Organisation Unit
- Amount
- Reason
- Status
- Action

Include these rows:
1. National digital health infrastructure upgrade — Directorate of Digital Health and Policy — KES 455,000,000 — Approved Demand ready for planning — Ready — Add to plan
2. Digital health technical staff certification programme — Human Resources Management and Development — KES 95,000,000 — KES 15,000,000 funding shortfall — Returned — View return

Add a compact single-select filter bar above the table: All work, Approved Demands, Returned, Needs attention, Approved not started. Show All work selected. These controls filter the table; they are not page navigation.

Keep this as a task-oriented workspace, not an analytics dashboard. Do not use charts, large KPI cards, package queues, release queues or technical evidence panels.
```

---

## Stitch Prompt 02 — PLN-UI-02 Register annual plan with explicit entity scope

```text
Design the main content area for registering a Procurement Plan when the current user has access to more than one Procuring Entity.

Keep the existing Procurement navigation, top bar and branding unchanged.

Header:
- Breadcrumb: Procurement Planning / New annual plan
- Title: Create annual procurement plan
- Description: “Register the plan that will consolidate approved needs for one Procuring Entity and financial year.”

Use one compact form, not a wizard.

Section 1: Plan ownership
- Procuring Entity: required searchable select
- Show two eligible values: Ministry of Health; County Government of Kisumu
- Helper text: “Choose the entity that owns this plan. This cannot be changed after the plan is created.”
- Financial year: required select, value 2027/28
- Directly below Financial year, show read-only derived text: “Plan period: 1 July 2027 – 30 June 2028”
- Add quiet helper text: “Derived from the configured financial year.”

Section 2: Plan details
- Plan title: editable text field prefilled with “Ministry of Health Annual Procurement Plan 2027/28”
- Currency: required select with KES selected
- Coordinating procurement unit: required searchable Organisation Unit select with “Supply Chain Management Services” selected
- Helper text: “Choose the unit authorised to coordinate procurement for this entity. It does not have to be the lowest organisation unit.”

Footer actions:
- Cancel
- Create plan

Make the Procuring Entity choice visually explicit. Do not silently display a default entity as read-only when multiple eligible entities exist. The planning period is read-only derived information, not an input. Currency and coordinating procurement unit are controlled selects, not free-text fields. Do not show Budget context on this form. Do not show technical entity or Organisation Unit codes. Do not add steps, integration cards, upload options or approval settings.
```

### Required state notes

- If only one eligible Procuring Entity exists, show it visibly as read-only with “Assigned from your authorised scope.”
- If only one currency or coordinating procurement unit is eligible, show the value visibly as read-only rather than presenting a redundant select.
- If none exists, replace the form with a blocked state explaining that an authorised Procuring Entity assignment is required.
- These are state requirements for later implementation; Prompt 02 should visually design the multi-entity case.

---

## Stitch Prompt 03 — PLN-UI-03 Plan builder before adding a Demand

```text
Design the main content area for an empty Draft annual Procurement Plan.

Keep the existing Procurement navigation, top bar and branding unchanged.

Header:
- Breadcrumb: Procurement Planning / Ministry of Health / 2027/28
- Title: Ministry of Health Annual Procurement Plan 2027/28
- Secondary line: read-only “Open Plan · Draft Version 1 · Plan period 1 July 2027 – 30 June 2028”
- Primary action: Add approved demand

Use a narrow read-only summary strip with derived values:
- Plan Items: 0
- Planned value: KES 0
- Departmental contributions: 0 submitted
- Validation: Not run

Below it, show a compact filter row:
- Organisation Unit: controlled select with “All permitted units” selected
- Category: controlled select with “All categories” selected
- Status: controlled select with “All statuses” selected
- Search plan items: text search input

Main panel title: Plan Items

Show a useful empty state inside the table area:
- Heading: No Plan Items yet
- Text: “Add an approved and funded Demand to begin building this annual plan.”
- Primary action: Add approved demand
- Secondary link: View eligible Demands

Use a simple bottom action bar:
- Back to Planning
- Run validation, disabled
- Submit for departmental sign-off, disabled

Do not add blank packages, manual line-entry grids, template selectors, tabs or readiness cards.
```

---

## Stitch Prompt 04 — PLN-UI-04 Add approved Demand dialog

```text
Design a large focused dialog titled “Add approved demand” over the Draft Plan builder.

The dialog selects approved source needs; it does not create or edit a Demand.

Top controls:
- Search approved Demands: text search input
- Organisation Unit: controlled select with “All permitted units” selected
- Category: controlled select with “All categories” selected
- Remaining availability only: checked checkbox

Use a compact selectable table with a checkbox at the start of each row and columns:
- Demand
- Organisation Unit
- Approved amount
- Already planned
- Available to plan
- Required by
- Funding

Show one selectable row:
- National digital health infrastructure upgrade
- Quiet secondary reference: DMD-MOH-2027-014
- Directorate of Digital Health and Policy
- KES 455,000,000 approved
- KES 0 planned
- KES 455,000,000 available
- Required by 31 March 2028
- Reserved

Below the selected row, show a small read-only derived selection summary:
- 1 Demand selected
- KES 455,000,000 to add
- Helper text: “Selecting this Demand includes its available Need Items and creates one Proposed Plan Item by default. The Plan Item editor confirms any aggregation or division decision.”

Footer actions:
- Cancel
- Add to plan

All Demand, amount, date and funding values are inherited and read-only. The only row interaction is selection. Do not display Draft, Returned, Rejected, Cancelled or fully planned Demands. Do not add editable Budget, Strategy or ownership fields. Do not expose allocation records or technical IDs.
```

---

## Stitch Prompt 05 — PLN-UI-05 Plan builder with a Plan Item

```text
Design the main content area for the Draft Ministry of Health Annual Procurement Plan after an Approved Demand has been added.

Keep the existing Procurement navigation, top bar and branding unchanged.

Header:
- Breadcrumb: Procurement Planning / Ministry of Health / 2027/28
- Title: Ministry of Health Annual Procurement Plan 2027/28
- Secondary line: Open Plan · Draft Version 1
- Primary action: Add approved demand

Use one compact read-only summary strip with derived values:
- 1 Plan Item
- KES 455,000,000 planned
- 1 Organisation Unit
- Departmental contributions: Preparing
- Validation: Needs attention

Show a compact read-only Plan Items table with columns:
- Requirement
- Organisation Unit
- Category
- Planned value
- Method
- Schedule
- Validation
- Action

One row:
- National digital health infrastructure upgrade
- Quiet reference: PPI-MOH-2027-021
- Directorate of Digital Health and Policy
- ICT infrastructure and services
- KES 455,000,000
- Open tender
- Completion by 31 March 2028
- Needs attention
- Continue

Below the table, show the derived read-only plan total KES 455,000,000.

Add a restrained read-only yellow validation-issue strip above the table:
- “1 item needs attention before departmental sign-off.”
- Link: Review issue

Bottom action bar:
- Back to Planning
- Run validation
- Submit for departmental sign-off, disabled

Do not add package, lot, release or consumption tables. Do not add decorative charts or a second navigation system.
```

---

## Stitch Prompt 06 — PLN-UI-06 Plan Item editor

```text
Design the main content area for editing one Draft Plan Item. Keep it a single focused page with clear sections, not a many-tab workbench.

Keep the existing Procurement navigation, top bar and branding unchanged.

Header:
- Breadcrumb: Procurement Planning / 2027/28 Plan / National digital health infrastructure upgrade
- Title: National digital health infrastructure upgrade
- Secondary line: Directorate of Digital Health and Policy · KES 455,000,000
- Status chips: Draft; Needs attention

At the top, show a compact read-only source panel titled “Approved source” with:
- Demand: National digital health infrastructure upgrade
- Funding: Digital clinical systems infrastructure · KES 455,000,000 reserved
- Primary Strategy target: At least 99.9% annual availability by 30 June 2028
- Supporting Strategy target: Restore critical services within four hours by 30 June 2028
- Owner: Directorate of Digital Health and Policy
- Link: View approved Demand

Main form section: Planning approach
- Plan Item description: editable multiline field, prefilled with a concise planning description consistent with the Approved Demand
- Category: required searchable select with “ICT infrastructure and services” selected
- Governing regime: read-only value “PPADA” with helper text “Derived from the applicable legal and funding context.”
- Recommended method: read-only value “Open tender”
- Confirmed method: required select with “Open tender” selected
- Method basis: read-only text “Preferred competitive method under the applicable regime.”
- Do not show an override-reason field in this state because the recommended method is confirmed
- Arrangement: required select with “Single year” selected; other permitted value is “Multi-year”

Subsection: Aggregation and indicative lotting
- Source allocation: read-only summary “1 Approved Demand · 2 Need Items · KES 455,000,000” with a quiet “View source breakdown” button
- Aggregation decision: required radio group with “Combine in this Plan Item” selected and “Keep separate” as the other option
- Aggregation reason: required multiline field prefilled with “Single integrated infrastructure requirement with common delivery and interoperability dependencies.”
- Indicative lotting decision: required radio group with “Indicative lots expected” selected and “No lots expected” as the other option
- Expected lot count: optional number field, left blank
- Indicative lot basis: required multiline field prefilled with “Infrastructure supply, installation and support components.”

Second form section: Planned schedule
Use a compact milestone table with columns Milestone and Planned date. Every planned date is a date input, not free text:
- Invitation published — 15 September 2027
- Tender opening — 20 October 2027
- Evaluation completed — 15 November 2027
- Award approval — 15 December 2027
- Contract signature — 15 January 2028
- Delivery and completion — 31 March 2028
- Add quiet helper text: “Dates were proposed from the confirmed method and target completion. Changed dates require a planning reason.”

Third section: Statutory and strategy treatment
- Statutory allocation treatment: required select with “Contributes through indicative reserved lot(s)” selected
- Target group: required multi-select with three separately selected values: “Women”; “Youth”; “Persons with disabilities”
- Planned treatment value: currency amount input with KES 136,500,000
- Plan-level coverage: read-only text “KES 136,500,000 planned of KES 136,500,000 currently required”
- Add helper text: “The required value is calculated from the current statutory rule and Plan total. Users do not enter the percentage.”
- Strategy context: read-only summary showing the primary target “At least 99.9% annual availability by 30 June 2028” and the inherited commitments “Improve availability of critical health services”; “Reduce whole-life infrastructure cost”; “Improve continuity of critical services”; and “Ensure compliant handling of replaced ICT equipment”
- Value treatment note: editable multiline field prefilled with “Carry requirements into specifications, evaluation and contract performance measures.”

Show one business-readable issue at the bottom:
- Needs attention: “Confirm the indicative lot basis before departmental sign-off.”

Sticky footer actions:
- Cancel
- Save draft
- Save and return to plan

Keep inherited Demand, funding and Strategy details read-only. Keep the governing regime, method recommendation, legal basis and plan-level statutory requirement read-only. Use controlled selections for planning decisions and date inputs for milestones. Do not show internal allocation records, raw rule codes, user-maintained percentages, scoring, detailed Tender lots, STD configuration or approval workflow settings.
```

---

## Stitch Prompt 07 — PLN-UI-07 Departmental contribution sign-off

```text
Design a focused right-side drawer titled “Submit departmental contribution” over the Plan builder.

This is a compact business sign-off, not a separate departmental planning workbench.

Show:
- Read-only Organisation Unit: Directorate of Digital Health and Policy
- Read-only Financial year: 2027/28
- Derived Plan Items: 1
- Derived total planned value: KES 455,000,000
- Derived validation: Ready

Include one compact read-only item row:
- National digital health infrastructure upgrade
- KES 455,000,000
- Open tender
- Ready

Declaration:
- Required checkbox with text: “I confirm that these requirements represent this Organisation Unit’s planned procurement needs for the stated financial year.”

Optional comment field:
- Label: Submission note; multiline input
- Placeholder: Add context for Procurement, if needed

Footer actions:
- Cancel
- Submit contribution

Use a short confirmation-oriented layout. Do not show a workflow diagram, approval matrix, technical validation results or editable Plan Item fields.
```

---

## Stitch Prompt 08 — PLN-UI-08 Consolidated plan review and approval

```text
Design the main content area for reviewing the consolidated Ministry of Health Annual Procurement Plan 2027/28.

Keep the existing Procurement navigation, top bar and branding unchanged.

Header:
- Breadcrumb: Procurement Planning / Ministry of Health / Review
- Title: Review annual procurement plan
- Secondary line: Ministry of Health · FY 2027/28 · Version 1
- Status chips: In review; Ready

Use a compact read-only summary strip with derived values:
- 1 Plan Item
- KES 455,000,000 planned
- 1 of 1 departmental contributions submitted
- Open tender: KES 455,000,000
- Validation: Ready

Main left area:

Section: Plan Items
Read-only compact table with columns Requirement, Organisation Unit, Value, Method, Completion, Status, Action.
Show the National digital health infrastructure upgrade row with KES 455,000,000, Open tender, 31 March 2028, Ready and View.

Section: Statutory allocation coverage
Use a compact read-only table of calculated coverage, not a chart, with columns Obligation, Required treatment, Planned treatment, Status.
Show:
- Women, youth, persons with disabilities and disadvantaged groups — Minimum 30% plan allocation — KES 136,500,000 planned through reserved lot treatment — Ready
- County resident tenderers — Not applicable to this national Procuring Entity — Not applicable — Not applicable

Section: Review issues
Show one restrained read-only derived ready message:
- “All required planning checks are ready for this decision.”

Right review rail:
- Read-only current decision: Professional review
- Read-only prepared by: Supply Chain Management Services
- Read-only departmental submission: Submitted
- Read-only validation run: Ready
- Decision options displayed as buttons: Return plan; Recommend approval
- Decision comment: multiline input with helper text “Optional when recommending approval; required when returning the Plan.”

Below the current decision, show a compact read-only prior-decision trail with actor, action and date. Do not display a generic approval matrix.

Keep the screen focused on evidence needed for the current decision. Do not add analytics charts, raw rules, package tabs, document-generation panels or Tender configuration.
```

### Design-state note

For the final approver state, reuse the same screen and replace the review rail action with **Return plan** and **Approve plan**. Show the applicable authority in plain language; do not hard-code a Ministry-only title into the reusable component.

---

## Stitch Prompt 09 — PLN-UI-09 Approved plan and implementation

```text
Design the main content area for an Approved annual Procurement Plan with implementation tracking.

Keep the existing Procurement navigation, top bar and branding unchanged.

Header:
- Breadcrumb: Procurement Planning / Ministry of Health / 2027/28
- Title: Ministry of Health Annual Procurement Plan 2027/28
- Secondary line: Open Plan · Approved Version 1 · Approved baseline is read-only
- Primary action: Add Plan Item
- Secondary action button: Export approved plan

Use a compact read-only summary strip with derived values:
- Approved plan value: KES 455,000,000
- Plan Items: 1
- Tender take-up: 1 of 1
- On schedule: 1
- Publication: Published

Below the summary, show a small reporting and filter row:
- Reporting period: required select with “Q2 · FY 2027/28” selected
- As at: read-only derived value “31 October 2027”
- Organisation Unit: controlled select with “All permitted units” selected
- Status: controlled select with “All statuses” selected

Main section: Plan implementation
Use a compact read-only table with columns:
- Requirement
- Organisation Unit
- Planned value
- Tender take-up
- Planned milestone
- Actual progress
- Variance
- Action

One row:
- National digital health infrastructure upgrade
- Directorate of Digital Health and Policy
- KES 455,000,000
- Tender active · TND-MOH-2027-008
- Evaluation by 15 November 2027
- Tender opened 20 October 2027; evaluation in progress
- On schedule
- View implementation

Second compact section: Publication
- Read-only destination: State Portal
- Derived status: Published
- Read-only published date: 25 August 2027
- Action: View publication evidence

Third compact section: Quarterly reporting
- Read-only selected reporting period: Q2 · FY 2027/28
- Derived: 1 item on schedule
- Derived: 0 overdue
- Button: Export quarterly report

Use helper text beside Add Plan Item: “Adds the requirement through a Draft revision; the Approved version remains operational.”

Do not allow editing of approved planning fields. Do not require the user to create a revision before adding an item. Do not use charts, realised-savings claims, expenditure figures, package/release tables or duplicate Tender data-entry controls.
```

---

## Stitch Prompt 10 — PLN-UI-10 Add Plan Item through a Draft revision

```text
Design the main content area immediately after a user adds a Plan Item to an already Approved Procurement Plan.

Keep the existing Procurement navigation, top bar and branding unchanged.

Header:
- Breadcrumb: Procurement Planning / Ministry of Health / 2027/28 / Revision 2
- Title: Ministry of Health Annual Procurement Plan 2027/28
- Secondary line: Approved Version 1 remains operational
- Status chips: Open Plan; Draft Revision 2 in progress; Needs attention
- Primary action: Run validation

Show a prominent but restrained information banner:
- “You are adding this item through Draft Revision 2. Approved Version 1 remains active until this revision is approved.”

Top revision summary:
- Read-only Approved Version 1 value: KES 455,000,000
- Derived Draft Revision 2 value: KES 535,000,000
- Derived change: KES 80,000,000 added
- Derived changed items: 1
- Derived unchanged items: 1

Revision context:
- Revision reason: required controlled select with “Additional approved need” selected
- Revision note: required empty multiline input with placeholder “Explain why this requirement is being added after Plan approval.”
- Read-only initiated by: Supply Chain Management Services
- Read-only created: 5 November 2027

Main section: Changes in this revision
Use a compact read-only comparison table with columns:
- Plan Item
- Change
- Approved Version 1
- Draft Revision 2
- Impact
- Action

Show the existing digital-health Plan Item as Unchanged:
- National digital health infrastructure upgrade
- Unchanged
- KES 455,000,000; Open tender; completion 31 March 2028
- Same
- Existing Tender TND-MOH-2027-008 remains active
- View

Show the added Plan Item:
- Digital health technical staff certification programme
- Added
- Not in Version 1
- KES 80,000,000; Open tender; owner Human Resources Management and Development
- Proposed; departmental sign-off and plan-level revalidation required
- Complete item

Below the table, show two read-only derived validation issues:
- “The added Organisation Unit contribution requires Head of Department sign-off.”
- “Recalculate the plan-level statutory allocation against the revised value of KES 535,000,000.”

Below the table, show a restrained notice:
- “Only changed items and affected plan-level checks require active review. Approved Version 1 remains unchanged until Revision 2 is approved.”

Bottom action bar:
- Cancel revision
- Save draft
- Submit revision, disabled until Ready

Only the revision reason and note are editable on this screen; Plan Item corrections open the focused Plan Item editor. Do not make existing operational Plan Items appear suspended. Do not display side-by-side raw JSON, audit hashes, duplicated complete plans, package/release objects or editable fields for the prior Approved version.
```

---

## 4. Design acceptance checklist

Approve the Stitch set only if:

1. The user can see the complete journey from Approved Demand to Tender take-up.
2. The Procurement Planning workspace is the clear module entry point.
3. Users with multiple Procuring Entity scopes must make an explicit choice when creating a plan.
4. One consolidated annual plan contains Organisation Unit-owned Plan Items.
5. The Plan Item editor contains planning decisions only; Demand, Budget and Strategy context is read-only.
6. Departmental sign-off is a focused drawer, not another workbench.
7. Review screens show the current decision, issues and evidence without a generic approval matrix.
8. Approved plans are visually read-only and implementation is shown as a downstream projection.
9. Add Plan Item automatically presents a Draft-revision state while the current Approved version remains visibly operational.
10. Revisions focus attention on changed items and affected plan-level controls without making unchanged operational items appear suspended.
11. No design introduces Planning Inclusion, Procurement Package, Package Line, Release Package or manual Consumption screens.
12. No screen exposes technical identifiers, hashes, rule codes or backend object names.
13. No screen uses decorative dashboards, unnecessary tabs or invented workflow stages.
14. Every interactive element has an explicit control type, and every inherited, calculated or historical value is visibly read-only or derived.

## 5. Explicitly leave for Cursor

Do not ask Stitch to implement:

- role and scope enforcement;
- zero-, one- and multi-entity selection logic;
- Demand eligibility filtering;
- allocation arithmetic;
- funding or reservation revalidation;
- method recommendation rules;
- anti-splitting checks;
- milestone calculation;
- statutory allocation calculations;
- state transitions and approvals;
- version locking and revision creation;
- publication integration;
- Tender handoff creation;
- notifications, audit or reporting calculations; or
- canonical seed/reset scripts and automated tests.

These belong in the Procurement Planning Cursor implementation document after the Stitch screens are approved.
