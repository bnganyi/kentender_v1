# Procurement Planning — MVP 1 Stitch Prompts

**Document ID:** PLANNING-MVP1-STITCH-2.0  
**Version:** 2.0  
**Status:** Approved design baseline for direct MVP correction  
**Date:** 12 August 2026  
**Controlling authority:** `KENTENDER-MVP-CMOM-1.1` and `PLANNING-MVP1-REQ-1.9`  
**Supersedes:** `PLANNING-MVP1-STITCH-1.9`  
**Module:** Procurement Planning

**Revision 2.0:** Adds the missing Plan Item removal journey. PLN-UI-05 and PLN-UI-10 expose a restrained row menu; PLN-UI-05A confirms whole-item removal with one required reason and explains the immediate or approval-time effect. Active items with Tender/downstream execution never show removal. No deletion screen, source-editing workbench or extra approval is introduced. All v1.9 Finance-shortfall and earlier workflow corrections remain in force.

## 1. Purpose

Use these prompts to design the minimum Procurement Planning screens for this journey:

> **Approved Demand → Planner completes Plan Item → Finance confirms funding → Head of Procurement approves Plan Version → Tender take-up**

These are **Stitch screen-design prompts**. They define visible layout, hierarchy, labels, representative states and screen boundaries. They do not implement permissions, services, calculations or transitions; those belong in Cursor.

## 2. Non-negotiable operating model

1. HoD approval occurs in Demands and makes the Demand Planning Ready.
2. Planning does not request a second routine HoD sign-off.
3. PLN-UI-04 may select one or more Approved Demands. One selection creates one Plan Item; multiple selections require an explicit separate-or-combined formation choice.
4. The Plan Item editor completes the already-created item; it does not select the Demand(s) again.
5. Finance confirms funding once, after the Plan Item is complete.
6. Head-of-Procurement review requires current Finance confirmation.
7. The Plan Item is the execution unit; Plan Versioning provides approval and immutability.
8. Adding an item to an Approved Plan quietly creates or reuses one Draft successor. The current Approved Version stays operational.
9. Combined formation appears only when multiple compatible Demands are selected and is decided in PLN-UI-04.
10. Planning cannot change HoD-owned facts. Material changes are made by amending and reapproving the Demand.
11. Plan Item removal starts from the Plan builder/update view. Draft-only items leave the Draft immediately; eligible Active items are only proposed for removal until the Draft successor is approved.

## 3. How to use

1. Generate Prompt 01 first to establish the module’s visual language.
2. Generate each remaining prompt as a separate screen or focused state in the same Stitch project.
3. Preserve the existing KenTender Procurement shell, navigation, top bar and branding.
4. Review each generated screen before generating the next.
5. Do not allow Stitch to invent additional fields, approvals, workbenches or workflow stages.

## 4. Shared design contract

Apply these instructions to every prompt:

- Design the **main content area only** for a desktop public-sector procurement application.
- Use a clear page title, a short task description and one obvious primary action.
- Prefer compact tables, short forms, restrained status chips and plain-language messages.
- Use cards only to group a real decision or task. Do not create decorative KPI-card grids.
- Use drawers or dialogs only for short, focused tasks.
- Keep inherited data readable but visually secondary to the actor’s current task.
- Do not show database field names, hashes, rule codes, audit payloads or internal object names.
- Human-readable references may appear as quiet secondary text.
- Do not ask users to enter Plan, Plan Item, Demand, Budget or Strategy codes.
- Do not expose Planning Inclusion, Procurement Package, Package Line, Release Package or Consumption objects.
- Do not show compliance scores or labels such as Passed, Failed, Qualified or Compliant.
- State the control type for every input. Mark inherited, calculated and historical content read-only or derived.
- Hide inapplicable controls. Do not use blank selects, unexplained dashes or zero-filled fields to represent absence.
- Do not show a disabled approval form to an unauthorised role. That role sees a neutral detail screen without the task action.
- Do not show Departmental Contribution, OU contribution, Departmental Submission or routine planning-stage HoD sign-off.
- Do not show generic statutory treatment, Strategy treatment, treatment rationale or planned-treatment-value fields.
- Strategy appears only as inherited read-only source context.
- Funding confirmation is a distinct Finance task after Plan Item completion, not a duplicate Demand approval.
- Plan-level preference and reservation coverage may appear only as a derived read-only review result. Do not add item-level treatment inputs.
- Use **Remove from draft** for a draft-only Proposed item and **Propose removal** for an eligible Active item. Never use Delete.
- Do not expose item removal when a Tender handoff or other downstream execution exists.

### 4.1 Status vocabulary

Use only the values relevant to the screen:

- Logical Plan: Open, Closed, Cancelled
- Plan Version: Draft, In review, Returned, Approved, Superseded, Cancelled
- Plan Item: Proposed, Active, Removed
- Draft change labels: Added, Changed, Proposed removal
- Validation: Not run, Ready, Needs attention, Blocked, Stale
- Finance confirmation: Not requested, Awaiting confirmation, Confirmed, Returned, Stale
- Publication: Not submitted, Queued, Published, Failed, Not applicable
- Tender take-up: Not taken up, Tender in preparation, Tender active, Contracted, Closed downstream

### 4.2 Canonical design data

Use this story consistently:

- Procuring Entity: Ministry of Health
- Secondary accessible Procuring Entity: County Government of Kisumu
- Financial year: 2027/28
- Plan title: Ministry of Health Annual Procurement Plan 2027/28
- Coordinating procurement unit: Supply Chain Management Services
- Owner Organisation Unit: Directorate of Digital Health and Policy
- Approved Demand: National digital health infrastructure upgrade
- Demand reference: DMD-MOH-2027-014
- Plan Item reference: PPI-MOH-2027-021
- Approved amount: KES 455,000,000
- Proposed Budget Line: Digital clinical systems infrastructure
- Budget Line allocation before confirmation: KES 480,000,000
- Finance confirms and reserves: KES 455,000,000
- Primary Strategy target: At least 99.9% annual availability by 30 June 2028
- Supporting Strategy target: Restore critical services within four hours by 30 June 2028
- Category: ICT infrastructure and services
- Procurement method: Open tender
- Broad STD family: Information Technology
- Arrangement: Single year
- Later Tender reference: TND-MOH-2027-008

Post-approval addition story:

- Corrected Approved Demand: Digital health technical staff certification programme
- Owner OU: Human Resources Management and Development
- Corrected approved amount: KES 80,000,000
- New Plan Item: PPI-MOH-2027-022
- Approved Version 1 value: KES 455,000,000
- Draft Version 2 value: KES 535,000,000
- Approved Version 1 remains operational while Draft Version 2 is reviewed

Do not create unrelated ministries, hospitals, budget lines or legacy District Hospital Renovation examples.

---

## Stitch Prompt 01 — PLN-UI-01 Procurement Planning workspace

**Screen contract**

- **Purpose:** Give the planner a scoped landing page and the next planning tasks.
- **Primary actor:** Procurement Planner.
- **Entry point:** Procurement navigation → Procurement Planning.
- **Reads:** Authorised PE scope, financial years, current Plan and eligible Approved Demands.
- **Writes:** Nothing.
- **Primary outcomes:** Open the current Plan or begin adding an Approved Demand.
- **Exit:** Plan builder or Add approved Demands dialog.
- **Exclude:** Analytics dashboard, approvals, Finance task form and contribution workbench.

```text
Design the main content area for the Procurement Planning landing page.

Keep the existing Procurement navigation, top bar and branding unchanged.

Header:
- Title: Procurement Planning
- Description: “Turn approved needs into funded, approved Plan Items ready for tendering.”
- Required searchable Procuring Entity select with “Ministry of Health” selected
- Required Financial year select with “2027/28” selected
- Helper text: “These controls define the workspace scope; they do not assign ownership to records.”
- Primary button: Open current plan

Show one compact read-only current-plan panel:
- Ministry of Health Annual Procurement Plan 2027/28
- Plan lifecycle: Open
- Current version: Draft Version 1
- 0 Plan Items
- KES 0 planned
- Validation: Not run
- Button: Continue planning

Below it, show a compact read-only “Work requiring action” table with columns:
- Work item
- Organisation Unit
- Amount
- Reason
- Status
- Action

Include one row:
- National digital health infrastructure upgrade
- Directorate of Digital Health and Policy
- KES 455,000,000
- Approved Demand ready for planning
- Ready
- Button: Add to plan

Add a compact filter row above the table:
- Work type select: All work, Approved Demands, Plan Items returned by Finance, Plan Items needing attention
- Search input: Search work

Keep this task-oriented. Do not use charts, decorative KPI cards, package queues, contribution statuses or technical evidence panels.
```

---

## Stitch Prompt 02 — PLN-UI-02 Create annual procurement plan

**Screen contract**

- **Purpose:** Register one annual Plan for a deliberate PE and financial year.
- **Primary actor:** Procurement Planner with create-plan authority.
- **Entry point:** Planning workspace → Create annual plan.
- **Reads:** Authorised PEs, configured financial years, currencies and coordinating procurement units.
- **Writes:** PE, financial year, title, currency and coordinating procurement unit.
- **Primary outcome:** Create Draft Plan Version 1.
- **Exit:** Empty Plan builder.
- **Exclude:** Budget context, approval settings, uploads and integration setup.

```text
Design the main content area for creating an annual Procurement Plan when the user can access more than one Procuring Entity.

Header:
- Breadcrumb: Procurement Planning / New annual plan
- Title: Create annual procurement plan
- Description: “Register the plan that will contain approved needs for one Procuring Entity and financial year.”

Use one compact form, not a wizard.

Section: Plan ownership
- Procuring Entity: required searchable select with Ministry of Health and County Government of Kisumu
- Helper text: “Choose the entity that owns this Plan. It cannot be changed after creation.”
- Financial year: required select with 2027/28 selected
- Read-only derived text: “Plan period: 1 July 2027 – 30 June 2028”

Section: Plan details
- Plan title: text input prefilled with “Ministry of Health Annual Procurement Plan 2027/28”
- Currency: required select with KES selected
- Coordinating procurement unit: required searchable Organisation Unit select with “Supply Chain Management Services” selected
- Helper text: “This is the unit authorised to coordinate procurement for the entity. It need not be the lowest Organisation Unit.”

Footer buttons:
- Cancel
- Create plan

Make PE selection explicit. Planning period is derived, Currency is a controlled select and Budget context is absent. Do not show technical PE/OU codes.
```

**Required design states**

- One eligible PE: show it read-only with “Assigned from your authorised scope.”
- Zero eligible PEs: replace the form with a blocked state explaining that operational scope is required.
- Multiple eligible PEs: require deliberate selection; never silently select the first PE.

---

## Stitch Prompt 03 — PLN-UI-03 Empty Draft Plan builder

**Screen contract**

- **Purpose:** Show the newly created Draft Plan and the single next action.
- **Primary actor:** Procurement Planner.
- **Entry point:** Create Plan or open current Draft Plan.
- **Reads:** Plan, Plan Version and scoped eligibility counts.
- **Writes:** Nothing on this screen.
- **Primary outcome:** Open Add approved Demands.
- **Exit:** PLN-UI-04.
- **Exclude:** Manual Plan Item entry, contribution submission and approval controls.

```text
Design the main content area for an empty Draft annual Procurement Plan.

Header:
- Breadcrumb: Procurement Planning / Ministry of Health / 2027/28
- Title: Ministry of Health Annual Procurement Plan 2027/28
- Secondary line: “Open Plan · Draft Version 1 · 1 July 2027 – 30 June 2028”
- Primary button: Add approved demands

Show one compact read-only summary strip:
- Plan Items: 0
- Planned value: KES 0
- Finance confirmed: 0 of 0
- Validation: Not run

Show a compact filter row:
- Organisation Unit select: All permitted units
- Category select: All categories
- Status select: All statuses
- Search input: Search Plan Items

Main panel title: Plan Items

Inside the empty table area show:
- Heading: No Plan Items yet
- Text: “Add an Approved Demand to begin building this annual Plan.”
- Primary button: Add approved demands
- Secondary link: View eligible Demands

Bottom action bar:
- Back to Planning
- Run validation, disabled
- Submit for review, disabled

Do not show blank packages, manual line-entry grids, tabs, departmental contributions or approval matrices.
```

---

## Stitch Prompt 04 — PLN-UI-04 Add approved Demands dialog

**Screen contract**

- **Purpose:** Select one or more eligible Approved Demands and decide how they form Plan Items.
- **Primary actor:** Procurement Planner.
- **Entry point:** Add approved demands from PLN-UI-03 or Add Plan Item from PLN-UI-09.
- **Reads:** Eligible Approved Demands, Need Item counts, proposed Budget Lines, source availability and formation compatibility.
- **Writes:** Selected Demand set, required formation choice and combination reason when applicable.
- **Primary outcome:** Create the selected separate or combined Proposed Plan Item(s) and continue to the result.
- **Exit:** PLN-UI-06 for one/combined item or PLN-UI-05/10 for multiple separate items.
- **Exclude:** Procurement method, schedule, Finance decision and version management.

```text
Design a large focused dialog titled “Add approved Demands” over the Procurement Plan.

Top controls:
- Search approved Demands: text input
- Organisation Unit: controlled select with All permitted units
- Category: controlled select with All categories
- Available to plan only: checked checkbox

Use a compact multi-select table with a checkbox at the start of each row and columns:
- Demand
- Organisation Unit
- Approved value
- Required by
- Proposed funding
- Status

Show these selectable rows:
- National digital health infrastructure upgrade
- Quiet reference: DMD-MOH-2027-014
- Directorate of Digital Health and Policy
- KES 455,000,000
- 31 March 2028
- Digital clinical systems infrastructure
- Planning Ready

- Digital health technical staff certification programme
- Human Resources Management and Development
- KES 80,000,000
- 31 March 2028
- Digital health workforce development
- Planning Ready

With one row selected, show a compact read-only selection summary:
- National digital health infrastructure upgrade
- 1 Approved Demand
- 2 Need Items
- KES 455,000,000 approved
- Proposed Budget Line: Digital clinical systems infrastructure
- Finance confirmation: Required after planning
- Link: View source breakdown
- Helper text: “One Plan Item will be created.”

Do not show Plan Item formation controls while only one Demand is selected.

When two or more rows are selected, replace the single-source summary with:
- Selection summary: “2 Approved Demands · 2 Organisation Units · KES 535,000,000”
- Section title: Plan Item formation
- Required radio group:
  - Create separate Plan Items
  - Combine into one Plan Item

For the illustrated mixed-OU selection:
- Show Create separate Plan Items as available.
- Show Combine into one Plan Item as disabled.
- Plain explanation: “These Demands have different owning Organisation Units and cannot be combined in MVP 1.”
- Read-only result preview: “2 Plan Items will be created.”

Add a same-OU compatible design state:
- Combine into one Plan Item is enabled and selected.
- Show a required multiline input labelled “Reason for combining these requirements”.
- Show a read-only result preview: “1 combined Plan Item will be created from 2 Approved Demands. Each source and funding allocation remains traceable.”

Formation controls are progressive disclosure: they appear only after multiple Demands are selected.

Footer buttons:
- Cancel
- Dynamic primary button for one selected: Add Demand and continue
- Dynamic primary button for multiple separate: Create 2 Plan Items
- Dynamic primary button for multiple combined: Create combined Plan Item and continue

For the Approved-Plan variant, show: “The current Approved Plan remains active while this addition is prepared.” The same one-or-more selection and formation rules apply.

Do not show Finance approval, revision fields, procurement method fields or schedule fields. Do not ask the user to create one Plan Item first and return later to add another Demand.
```

---

## Stitch Prompt 05 — PLN-UI-05 Draft Plan with Proposed Plan Item

**Screen contract**

- **Purpose:** Show the Plan after source selection and direct the planner to finish the new item.
- **Primary actor:** Procurement Planner.
- **Entry point:** Return from Add Demand or Plan Item editor.
- **Reads:** Draft Plan Version, Plan Items, validation and Finance status.
- **Writes:** Nothing until the planner confirms removal in PLN-UI-05A.
- **Primary outcomes:** Continue the item, remove it from the Draft, run validation or add another Demand.
- **Exit:** PLN-UI-06, PLN-UI-04, PLN-UI-05A or validation result.
- **Exclude:** HoD sign-off, contribution submission and editable Finance decisions.

```text
Design the main content area for Draft Version 1 after an Approved Demand has created one Proposed Plan Item.

Header:
- Breadcrumb: Procurement Planning / Ministry of Health / 2027/28
- Title: Ministry of Health Annual Procurement Plan 2027/28
- Secondary line: Open Plan · Draft Version 1
- Primary button: Add approved demands

Show one compact read-only summary strip:
- 1 Plan Item
- KES 455,000,000 planned
- Finance confirmed: 0 of 1
- Validation: Needs attention

Show a restrained issue strip:
- “Complete the Plan Item before requesting Finance confirmation.”
- Link: Review issue

Use a compact read-only Plan Items table with columns:
- Requirement
- Organisation Unit
- Planned value
- Method
- Schedule
- Finance
- Validation
- Action

One row:
- National digital health infrastructure upgrade
- Quiet reference: PPI-MOH-2027-021
- Directorate of Digital Health and Policy
- KES 455,000,000
- Not completed
- Not completed
- Not requested
- Needs attention
- Primary row link: Continue
- Overflow menu: Remove from draft

Bottom action bar:
- Back to Planning
- Run validation
- Submit for review, disabled

Do not use Delete. Do not expose source-level removal, packages, contribution status, routine HoD sign-off, release objects or charts.
```

---

## Stitch Prompt 05A — PLN-UI-05A Remove Plan Item confirmation

**Screen contract**

- **Purpose:** Confirm whole-item removal without creating another workflow step.
- **Primary actor:** Procurement Planner.
- **Entry point:** Remove from draft on PLN-UI-05/10, or Propose removal for an eligible Active item while preparing an update.
- **Reads:** Plan Item, Draft-change type, source Demand(s), value, Finance state and downstream take-up.
- **Writes:** Required removal reason and one removal command.
- **Primary outcome:** Remove the whole item from the Draft or record its proposed removal in the Draft successor.
- **Exit:** Return to the same Plan builder/update view.
- **Exclude:** Hard deletion, source editing, Demand cancellation, downstream Tender cancellation and extra approval.

```text
Design one compact confirmation dialog. Do not create a page, drawer, wizard or removal workbench.

Draft-only Proposed-item state:
- Title: Remove Plan Item from draft?
- Intro: “This removes the item from the current Draft Plan. The Approved Demand will be available for planning again.”
- Read-only item: Digital health technical staff certification programme
- Read-only Organisation Unit: Human Resources Management and Development
- Read-only planned value: KES 80,000,000
- Read-only approved sources: 1 Demand · 1 Need Item
- Read-only Finance effect: No funding confirmed; no reservation to release
- Required multiline input: Reason for removal
- Placeholder: “Briefly explain why this item should be removed from the draft.”
- Buttons: Keep item; Remove from draft

Finance-confirmed draft-only variant:
- Replace the Finance effect with: “Funding confirmation will be cancelled and KES 80,000,000 will be released.”
- Keep the same controls and button labels.

Eligible Active-item variant:
- Title: Propose Plan Item removal?
- Intro: “The item remains active in the current Approved Plan until this update is approved.”
- Read-only effective-on-approval note: “If approved, the item will be removed and its uncommitted reservation released.”
- Buttons: Keep item; Propose removal

Do not show the Active-item variant for an item with a Tender handoff or downstream execution. For a combined Plan Item, show every source Demand read-only and state: “The whole Plan Item and all its source allocations will be removed together.” Do not offer individual-source checkboxes.

After success, return to the builder, recalculate counts and totals, and show a quiet confirmation message. If no Draft changes remain, show “No changes remain” with Cancel update as the next action.

Never use Delete, destructive red-page styling, technical status codes or editable funding controls.
```

---

## Stitch Prompt 06 — PLN-UI-06 Plan Item editor

**Screen contract**

- **Purpose:** Complete procurement-owned decisions for the Proposed Plan Item.
- **Primary actor:** Procurement Planner.
- **Entry point:** Continue from PLN-UI-05 or immediately after PLN-UI-04.
- **Reads:** Approved Demand snapshot(s), Need Items, proposed funding and inherited Strategy context.
- **Writes:** Procurement description, category, confirmed method, arrangement, indicative lotting and milestone dates.
- **Primary outcomes:** Save draft or request Finance confirmation.
- **Exit:** Plan builder/update overview or Finance queue.
- **Exclude:** Demand reselection, upstream fact editing, generic treatment fields, Plan approval and Finance decision.

```text
Design one focused page for completing a Proposed Plan Item. Do not use tabs or a multi-step wizard.

Header:
- Breadcrumb: Procurement Planning / 2027/28 Plan / National digital health infrastructure upgrade
- Title: National digital health infrastructure upgrade
- Secondary line: Directorate of Digital Health and Policy · KES 455,000,000
- Status chip: Proposed
- Context line for the initial plan: Draft Plan Version 1

Show a compact read-only panel titled “Approved source”:
- Demand: National digital health infrastructure upgrade
- Need Items: 2
- Approved value: KES 455,000,000
- Owner: Directorate of Digital Health and Policy
- Proposed Budget Line: Digital clinical systems infrastructure
- Finance confirmation: Not requested
- Strategy target: At least 99.9% annual availability by 30 June 2028
- Link: View Approved Demand
- Link: View source breakdown

For a combined Plan Item, reuse the source panel as “Approved sources”:
- Show each selected Demand as a compact read-only row with its owner, approved value, Need Item count and proposed Budget Line.
- Show the read-only combined total and the recorded reason for combining.
- Preserve a View source breakdown link for each Demand.
- Do not ask the planner to select, remove or combine the sources again in this editor.

Add a clear note: “Business scope, quantity, owner, delivery requirement and approved value come from the Approved Demand source(s) and cannot be changed here.”

Section: Procurement approach
- Plan Item description: editable multiline input prefilled with a concise procurement description
- Category: required searchable select with ICT infrastructure and services selected
- Governing regime: read-only PPADA
- Recommended method: read-only Open tender
- Confirmed method: required select with Open tender selected
- Method basis: read-only “Preferred competitive method under the applicable regime.”
- Arrangement: required select with Single year selected; Multi-year is the other permitted value

Section: Indicative lotting
- Helper text: “Indicate whether the eventual Tender may contain lots. Detailed lots are configured during Tender preparation.”
- Required radio group: Indicative lots expected; No lots expected
- Show Expected lot count as a number input only when lots are expected
- Show Indicative lot basis as a multiline input only when lots are expected

Section: Planned schedule
Use a compact table with columns Milestone and Planned date. Every date is a date input:
- Invitation published — 15 September 2027
- Tender opening — 20 October 2027
- Evaluation completed — 15 November 2027
- Award approval — 15 December 2027
- Contract signature — 15 January 2028
- Delivery and completion — 31 March 2028

Show one plain-language issue only when applicable:
- “Confirm all milestone dates before requesting Finance confirmation.”

Sticky footer buttons:
- Cancel
- Save draft
- Save and request Finance confirmation

For an item added to an Approved Plan, reuse this page with the quiet context line: “Draft Plan update · The current Approved Plan remains active.”

Remove completely:
- Aggregation decision in the ordinary editor
- Departmental contribution or HoD sign-off
- Statutory allocation treatment
- Statutory rationale
- Preference or reservation scheme inputs
- Planned treatment or reserved-value inputs
- Strategy treatment or value-treatment notes
- Plan-level coverage placeholders

Do not expose technical rules, version controls, Tender configuration, approval settings or editable upstream facts.
```

---

## Stitch Prompt 07 — PLN-UI-07 Finance funding confirmation — sufficient funds

**Screen contract**

- **Purpose:** Let the authorised Budget Officer confirm funding once for a completed Plan Item.
- **Primary actor:** Budget Officer or configured Finance authority.
- **Entry point:** Finance work queue or authorised Confirm funding action on a completed Plan Item.
- **Reads:** Plan Item, source Demand allocation, proposed Budget Line, amount and current availability.
- **Writes:** Finance decision and decision note only.
- **Primary outcomes:** Confirm fully available funding or return the item to the planner.
- **Exit:** Finance queue or read-only Plan Item detail.
- **Exclude:** Plan Item editing, Demand approval, Plan approval, generic Budget workbench and unauthorised disabled-form state.

```text
Design a focused right-side drawer titled “Confirm Plan Item funding”.

At the top show read-only task context:
- Plan Item: National digital health infrastructure upgrade
- Quiet reference: PPI-MOH-2027-021
- Plan: Ministry of Health Annual Procurement Plan 2027/28 · Draft Version 1
- Owner OU: Directorate of Digital Health and Policy
- Plan Item status: Proposed · Planning complete

Section: Funding to confirm
- Source Demand: National digital health infrastructure upgrade
- Proposed Budget Line: Digital clinical systems infrastructure
- Amount to confirm and reserve: KES 455,000,000
- Current available allocation: KES 480,000,000
- Derived balance after confirmation: KES 25,000,000
- Availability status: Sufficient

Show a compact read-only notice:
- “Confirming funding records the Finance decision and reserves this amount for the Plan Item.”

Decision comment:
- Multiline input labelled Decision note
- Helper text: “Optional when confirming; required when returning to the planner.”

Footer buttons:
- Cancel
- Return to planner
- Confirm funding

Keep this a single decision task. Do not add Budget creation, Budget Line editing, expenditure fields, Demand approval, Plan approval or a generic approval matrix.

“Confirm funding” is a Finance confirmation, not a generic approval. “Return to planner” is a remediable outcome, not final rejection.

Do not design a disabled version for Requesters or other unauthorised roles. They must not see the Confirm funding task action or this route; they may see only neutral read-only funding status where their record visibility permits it.
```

---

## Stitch Prompt 07A — PLN-UI-07A Finance funding confirmation — shortfall

**Screen contract**

- **Purpose:** Explain an exact funding shortfall and give the authorised Budget Officer the minimum valid next actions.
- **Primary actor:** Budget Officer or configured Finance authority.
- **Entry point:** The same Finance task as PLN-UI-07 when live availability is below the amount required.
- **Reads:** Plan Item, proposed Budget Line, amount required, current availability and calculated shortfall.
- **Writes:** A Return to planner decision only when that action is chosen. Opening Budget & Funding does not create a Finance decision.
- **Primary outcomes:** Keep the task Awaiting confirmation while resolving funding, or Return to planner with a reason.
- **Exit:** Governed Budget & Funding resolution route, Finance queue or read-only Plan Item detail.
- **Exclude:** Confirm funding, partial confirmation, override, inline Budget editing, value reduction and final rejection.

```text
Design the insufficient-funding state of the same right-side drawer. Title it “Funding shortfall”.

At the top show the same read-only task context as PLN-UI-07:
- Plan Item: Digital health technical staff certification programme
- Quiet reference: PPI-MOH-2027-022
- Plan: Ministry of Health Annual Procurement Plan 2027/28 · Draft Version 2
- Owner OU: Human Resources Management and Development
- Plan Item status: Proposed · Planning complete

Section: Funding required
- Proposed Budget Line: Digital Health Workforce Capacity Development
- Amount required: KES 80,000,000
- Current available allocation: KES 25,000,000
- Funding shortfall: KES 55,000,000
- Availability status: Insufficient funding

Use a restrained error notice:
- “This Plan Item cannot be confirmed because the Budget Line is short by KES 55,000,000.”
- “Resolve the allocation in Budget & Funding, or return the item to the planner if the requirement must be reconsidered.”

Below the notice, show two short action explanations under “Choose the next step”:
- Resolve funding — Review the Budget Line and address the shortfall in Budget & Funding.
- Return to planner — Send the item back if its funding source or requirement needs correction.

Do not display workflow-state instructions, screen IDs, implementation behaviour or Demand-amendment rules in this section. Those rules remain system behaviour and validation guidance, not interface copy.

Return reason:
- Multiline input labelled “Reason for returning”
- Hidden until Return to planner is chosen
- Required before confirming the return

Footer actions:
- Close
- Return to planner
- Prominent route action: Resolve in Budget & Funding

Do not show Confirm funding in this state. Do not show a disabled Confirm button. Do not permit partial confirmation, negative balance, availability override, inline Budget Line editing or manual reduction of the Plan Item amount.

Use this only as the optional `SCN-PLN-FUND-SHORT-001` state. The successful base story retains the fully available KES 80,000,000 workforce Budget Line.

Unauthorised users must not see this Finance task or route. Neutral record detail may show only “Funding confirmation: Awaiting confirmation”.
```

---

## Stitch Prompt 08 — PLN-UI-08 Head-of-Procurement review and approval

**Screen contract**

- **Purpose:** Review the complete Draft Plan Version and make the professional approval decision.
- **Primary actor:** Head of Procurement or configured professional authority.
- **Entry point:** Authorised Planning review queue after validation and Finance confirmation.
- **Reads:** Plan/version summary, Plan Items, validation, Finance confirmations, derived coverage and prior decisions.
- **Writes:** Approve or return decision and comment.
- **Primary outcomes:** Approve the Plan Version or return it to the planner.
- **Exit:** Approved Plan or review queue.
- **Exclude:** Departmental submission, HoD sign-off, item editing and generic statutory-treatment controls.

```text
Design the main content area for the authorised professional review of Draft Version 1.

Header:
- Breadcrumb: Procurement Planning / Ministry of Health / Review
- Title: Review and approve procurement plan
- Secondary line: Ministry of Health · FY 2027/28 · Draft Version 1
- Status chips: In review; Ready

Show one compact read-only summary strip:
- 1 Plan Item
- KES 455,000,000 planned
- Finance confirmed: 1 of 1
- Validation: Ready

Main area, section: Plan Items
Use a read-only compact table with columns:
- Requirement
- Organisation Unit
- Value
- Method
- Completion
- Finance
- Validation
- Action

Show:
- National digital health infrastructure upgrade
- Directorate of Digital Health and Policy
- KES 455,000,000
- Open tender
- 31 March 2028
- Confirmed
- Ready
- Link: View

Section: Preference and reservation coverage
- Show only a derived read-only result from the Plan’s supported source data.
- Use a compact table with columns: Coverage requirement, Required value, Derived planned coverage, Status.
- Do not show editable treatment, rationale, target-group or planned-value fields.
- If no supported designation data exists, omit this section rather than displaying blanks, dashes or zero-value inputs.

Section: Review issues
- Read-only message: “All required planning and funding checks are ready for decision.”

Right decision rail:
- Current task: Professional approval
- Prepared by: Supply Chain Management Services
- Finance confirmation: Complete
- Validation: Ready
- Multiline input: Decision comment
- Helper text: “Optional when approving; required when returning.”
- Buttons: Return to planner; Approve plan

Below the decision controls show a compact read-only prior-decision trail with actor, action and date.

Do not show Departmental Contribution, OU submission, HoD sign-off, approval matrix, analytics charts, generic statutory fields, package tabs or Tender configuration.

Do not design this task form for unauthorised users. A permitted viewer sees the neutral Approved/Draft Plan detail without decision buttons; direct access to this task route is not represented as an accessible disabled screen.
```

---

## Stitch Prompt 09 — PLN-UI-09 Approved Plan and implementation

**Screen contract**

- **Purpose:** Show the operational Approved Plan and downstream take-up without allowing baseline edits.
- **Primary actor:** Procurement Planner or authorised viewer.
- **Entry point:** Planning workspace → current Approved Plan.
- **Reads:** Approved Plan Version, Active Plan Items, Tender take-up, publication and reporting projections.
- **Writes:** Nothing to the Approved baseline.
- **Primary outcomes:** View implementation, begin adding a new Plan Item, or propose removal of an eligible Active item through a Draft successor.
- **Exit:** PLN-UI-04, PLN-UI-05A, Tender/implementation detail or export.
- **Exclude:** In-place editing, revision setup, aggregation and duplicated Tender data entry.

```text
Design the main content area for an Approved annual Procurement Plan.

Header:
- Breadcrumb: Procurement Planning / Ministry of Health / 2027/28
- Title: Ministry of Health Annual Procurement Plan 2027/28
- Secondary line: Open Plan · Approved Version 1 · Approved baseline is read-only
- Primary button: Add Plan Item
- Secondary button: Export approved plan
- Helper text: “Add an Approved Demand as a new Plan Item. The current Approved Version remains active while the update is reviewed.”

Show one compact read-only summary strip:
- Approved plan value: KES 455,000,000
- Plan Items: 1
- Tender take-up: 1 of 1
- On schedule: 1
- Publication: Published

Show a compact filter row:
- Reporting period select: Q2 · FY 2027/28
- Read-only As at: 31 October 2027
- Organisation Unit select: All permitted units
- Status select: All statuses

Section: Plan implementation
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
- Link: View implementation

The illustrated item has an active Tender, so do not show Propose removal for this row. For an Active item with no Tender handoff or downstream execution, add a restrained overflow-row action labelled Propose removal; it opens PLN-UI-05A and quietly creates or reuses the Draft successor.

Section: Publication
- Destination: State Portal
- Status: Published
- Published date: 25 August 2027
- Link: View publication evidence

If an update exists, show one compact notice:
- “Draft Version 2 in progress · 1 new Plan Item · Approved Version 1 remains operational.”
- Buttons: Continue update; View changes

Do not allow editing of Approved planning fields. Do not require the user to create a revision before adding or proposing removal of an item. Do not show removal for an executed item, aggregation controls, expenditure entry, package/release tables or duplicated Tender controls.
```

---

## Stitch Prompt 10 — PLN-UI-10 Draft Plan update overview

**Screen contract**

- **Purpose:** Show only the changes being prepared against an operational Approved Plan.
- **Primary actor:** Procurement Planner.
- **Entry point:** Return after completing a Plan Item added through PLN-UI-09 → PLN-UI-04 → PLN-UI-06.
- **Reads:** Approved Version 1, Draft Version 2, changed Plan Items, validation and Finance status.
- **Writes:** One concise update reason and, through PLN-UI-05A, a Plan Item removal reason.
- **Primary outcomes:** Save the update, remove a draft-only item, propose eligible Active-item removal, follow the Finance task or submit the ready update for review.
- **Exit:** PLN-UI-05A, PLN-UI-07, PLN-UI-08 or Approved Plan.
- **Exclude:** Full version-management workbench, routine HoD sign-off, aggregation and editing unchanged items.

```text
Design the main content area for Draft Version 2 after a new Plan Item has been added to an already Approved Plan.

Header:
- Breadcrumb: Procurement Planning / Ministry of Health / 2027/28 / Plan update
- Title: Plan update
- Secondary line: Ministry of Health Annual Procurement Plan 2027/28
- Status chips: Draft; Needs attention
- Primary button: Run validation

Show a restrained information banner:
- “Approved Version 1 remains active until this update is approved.”

Show a compact read-only change summary:
- Approved Version 1 value: KES 455,000,000
- Draft Version 2 value: KES 535,000,000
- Change: KES 80,000,000 added
- Changed Plan Items: 1
- Unchanged operational Plan Items: 1

Section: Update context
- Read-only Change type: Additional approved need
- Required multiline input: Reason for adding after approval
- Placeholder: “Briefly explain why this requirement is being added after Plan approval.”
- Read-only initiated by: Supply Chain Management Services
- Read-only created: 5 November 2027

Section: Changes in this update
Use a compact table with columns:
- Change
- Plan Item
- Organisation Unit
- Value
- Finance
- Validation
- Action

Show:
- Added
- Digital health technical staff certification programme
- Human Resources Management and Development
- KES 80,000,000
- Awaiting confirmation
- Ready
- Primary row link: View
- Overflow menu: Remove from update

Below the table show a collapsed read-only summary:
- “1 existing Plan Item remains unchanged and operational.”
- Link: View unchanged item

Show one restrained issue:
- “Finance confirmation is required for the added Plan Item before this update can be submitted for review.”

Show only a derived read-only preference and reservation coverage result when supported source data exists. Omit it entirely when no supported data exists.

Bottom action bar:
- Cancel update
- Save draft
- Submit update for review, disabled in the illustrated Awaiting confirmation state

Add a design-state note: after Finance confirms the added item and validation is Ready, show Finance as Confirmed, remove the issue and enable Submit update for review.

Add a removal design state:
- A removed draft-only addition disappears from the Changes table after confirmation and totals recalculate immediately.
- An eligible carried-forward Active item selected for removal remains listed as Change: Proposed removal, with its current Approved value and Status: Active until approval.
- If removal leaves no effective changes, replace validation/submission controls with the message “No changes remain in this update.” and the primary action Cancel update.
- Do not show removal for an item with Tender take-up or downstream execution.

Do not show a second HoD sign-off, Departmental Contribution, aggregation controls, source-level removal, suspended existing items, duplicated complete plans, raw diffs or editable fields from Approved Version 1.
```

---

## 5. Cross-screen journey

### 5.1 Initial Plan

`PLN-UI-01 → PLN-UI-02 → PLN-UI-03 → PLN-UI-04 → PLN-UI-06 → PLN-UI-07 → PLN-UI-08 → PLN-UI-09`

Shortfall branch: `PLN-UI-07A → resolve in Budget & Funding → same Finance task revalidates → PLN-UI-07`, or `PLN-UI-07A → Return to planner`.

PLN-UI-05 is the Plan-builder state used while the new Plan Item remains incomplete or after the planner returns to the Plan.

### 5.2 Add to an Approved Plan

`PLN-UI-09 Add Plan Item → PLN-UI-04 select Demand(s) and formation → PLN-UI-06 complete one/combined item or PLN-UI-10 review separate items → PLN-UI-07 Finance confirmation → PLN-UI-10 Ready state → PLN-UI-08 review → PLN-UI-09 Approved successor`

If Finance detects a shortfall, PLN-UI-07A replaces the confirmation state until the funding issue is governed and resolved or the item is returned.

The user does not create a revision manually. The Plan Item remains the operational focus; versioning is quiet governance context.

### 5.3 Remove a Plan Item

- Draft-only item: `PLN-UI-05/10 Remove from draft → PLN-UI-05A confirm → recalculated PLN-UI-05/10`.
- Eligible Active item: `PLN-UI-09 Propose removal → PLN-UI-05A confirm → PLN-UI-10 Proposed removal → PLN-UI-08 review → PLN-UI-09 Approved successor`.
- An item with Tender/downstream execution has no removal path.
- Removal does not open PLN-UI-06 and does not ask the user to edit source allocations.

## 6. Design acceptance checklist

Approve the Stitch set only if:

1. The visible journey is Approved Demand → Plan Item → Finance → Head of Procurement → Tender take-up.
2. The Planning workspace is the clear entry point.
3. PE selection is explicit for multi-PE users; zero scope blocks and one scope remains visible.
4. One selected Approved Demand creates one Proposed Plan Item without showing formation controls.
5. Multiple selected Demands require an explicit separate-or-combined formation choice in PLN-UI-04.
6. PLN-UI-06 edits only procurement-owned planning decisions.
7. HoD-owned facts are visibly inherited and read-only.
8. Compatible combination is completed directly in PLN-UI-04; there is no create-then-add aggregation step.
9. Cross-OU aggregation is absent.
10. PLN-UI-07 and PLN-UI-07A are sufficient-funding and shortfall states of the same single Finance task after Plan Item completion.
11. No routine planning-stage HoD sign-off or Departmental Contribution remains.
12. PLN-UI-08 is accessible only as the authorised professional review task; viewers use neutral detail.
13. Approved Plan fields are read-only.
14. Adding to an Approved Plan quietly creates or reuses one Draft successor.
15. Approved Version 1 and its existing Tender handoffs remain visibly operational during the update.
16. Generic statutory treatment, Strategy treatment, rationale and planned-treatment-value controls are absent.
17. Preference and reservation coverage is derived, read-only and shown only when supported data exists.
18. Strategy context is inherited and never rewritten in Planning.
19. Every input has a stated actor, source and operational outcome.
20. No screen introduces a package/release workbench, internal identifiers, decorative dashboards or invented workflow stages.
21. PLN-UI-05/10 exposes Remove from draft for a draft-only item and uses PLN-UI-05A for one compact confirmation with a required reason.
22. Eligible Active-item removal is shown as Proposed removal until successor approval; the current Approved item remains operational meanwhile.
23. Items with Tender/downstream execution have no removal action, and combined Plan Items can be removed only as a whole.
24. Removal never uses Delete and never introduces a source-allocation editor or extra approval.

## 7. Explicitly leave for Cursor

Do not ask Stitch to implement:

- PE/OU scope enforcement;
- record visibility, task visibility or mutation authority;
- direct-route rejection for unauthorised actors;
- Demand eligibility filtering;
- Demand Allocation creation;
- Budget availability and reservation arithmetic;
- Finance confirmation, shortfall, governed resolution, return or staleness transitions;
- method recommendation rules;
- milestone validation;
- aggregation compatibility checks;
- Plan validation and approval transitions;
- Draft successor creation or Approved-Version locking;
- whole-item removal, Finance-task cancellation, reservation release, source-eligibility restoration and removal concurrency checks;
- derived preference/reservation coverage calculations;
- publication integration;
- Tender handoff creation;
- notifications and audit events;
- seed/reset scripts; or
- automated positive and negative permission tests.

These belong in the approved direct MVP Cursor correction pack.
