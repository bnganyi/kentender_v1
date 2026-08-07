# Demands — MVP 1 Stitch Prompts

**Document ID:** DEMAND-MVP1-STITCH-1.1  
**Status:** Design input  
**Date:** 7 August 2026  
**Requirements baseline:** `DEMAND-MVP1-REQ-1.1`  
**Application:** KenTender  
**Module label:** Demands  
**Primary fixture:** Ministry of Health  
**Secondary fixture:** County Government of Kisumu

## 1. How to use this document

1. Give Stitch the current KenTender visual reference before running these prompts.
2. Run Prompt 00 once to establish the common design contract.
3. Run each remaining prompt separately and in order.
4. Use the preceding approved output as the visual reference for the next prompt.
5. Generate only the requested content area or focused state. Do not combine the prompts into a large multi-screen generation.
6. Review each result against its acceptance check before continuing.
7. Treat all named records and amounts as stable KenTender demo fixtures, not statutory thresholds.

Stitch is designing the authenticated page content only. The real KenTender navigation rail, breadcrumb bar, global header, notifications and account controls remain supplied by the application.

## 2. Stable design fixtures

Use these fixtures consistently across all prompts.

### 2.1 Principal Demand

- Reference: DMD-MOH-2027-014
- Title: National digital health infrastructure upgrade
- Procuring entity: Ministry of Health
- Owning unit: Directorate of Digital Health and Policy
- Requester: Dr Miriam Njeri
- Business approver: James Mwangi
- Procurement Approval Authority: Grace Wanjiku
- Budget Officer: Peter Otieno
- Route: Standard
- Required by: 30 September 2027
- Delivery location: National Data Centre and designated health facilities
- Confirmed estimate: KES 455,000,000
- Primary Strategy target: At least 99.9% annual availability by 30 June 2028
- Budget line: Digital clinical systems infrastructure
- Budget line approved amount: KES 480,000,000
- Available before reservation: KES 480,000,000
- Available after reservation: KES 25,000,000
- Reservation: RSV-MOH-0001
- Downstream Plan Item: PPI-MOH-2027-021

Use the same Demand at different lifecycle snapshots. Do not present the snapshots as separate Demands.

### 2.2 Returned Ministry Demand

- Reference: DMD-MOH-2027-019
- Title: Digital health technical staff certification programme
- Procuring entity: Ministry of Health
- Owning unit: Human Resources Management and Development
- Requester: Anne Achieng
- Route: Standard
- Requester estimate: KES 95,000,000
- Relevant Budget line: Digital Health Workforce Capacity Development
- Available funding: KES 80,000,000
- Return reason: “The proposed scope exceeds available funding by KES 15,000,000. Revise the number of participants or provide a phased delivery approach.”

### 2.3 Minimal County Demand

- Reference: DMD-CGK-2027-006
- Title: Solar-powered vaccine refrigerators for rural health facilities
- Procuring entity: County Government of Kisumu
- Owning unit: Department of Medical Services, Public Health and Sanitation
- Route: Standard
- Status: Draft
- Requester estimate: KES 24,000,000

The County Demand shall never appear in a Ministry-only user view. It may appear only in a deliberately requested cross-entity or County-scoped state.

---

## Prompt 00 — Common design contract

```text
Establish the common visual contract for the KenTender Demands MVP 1 screens.

KenTender is an electronic public procurement system. Design a restrained, credible government-enterprise interface that is strict underneath and simple on top. Prioritise clear ownership, the next required action, traceability and accessibility.

Design rules:
- Design only the main page content area. Do not create or modify the application navigation rail, breadcrumb bar, global header, notification controls, account controls or application branding.
- The user-facing module name is “Demands”. Do not use “Demand Intake and Approval” as a page or module title.
- Follow the supplied KenTender reference for typography, navy primary colour, neutral surfaces, borders, buttons, field styling and density.
- Use compact spacing, clear section headings, concise summaries and compact tables.
- Do not use oversized hero areas, decorative illustrations, glass effects, gradients or a wall of KPI cards.
- Show one clear primary action per screen. Keep secondary and destructive actions visually quieter.
- Use sentence case throughout.
- Show Demand reference as supporting context, not as the dominant title.
- Do not expose database identifiers, DocType names or technical integration language.
- Use status text with a restrained badge or dot and never rely on colour alone.
- Use only these Demand workflow statuses: Draft, In review, Returned, Approved, Rejected and Cancelled.
- When relevant, show the current stage separately: Request preparation, Business review, Procurement enrichment, Budget confirmation, Final approval or Complete.
- Use only these Planning-usage labels: Not taken up, Partially planned and Fully planned.
- Use only these Demand routes: Standard, Additional and Emergency.
- Emergency may be visually prominent but must not look like it bypasses review or funding controls.
- Users must not be asked to enter or maintain Demand, Strategy, Budget or organisation codes.
- Requester screens must not ask for a Budget line, Strategy target, procurement method, tender type or Planning data.
- Show automated Budget matching only as a recommendation. Never label it confirmed until a Budget Officer signs off.
- Do not add scores, ranks, pass/fail ratings, AI assistants, predictive recommendations, savings claims or unrequested analytics.
- Use visible focus states, accessible labels, keyboard-operable controls and adequate contrast.
- Show validation or returned-work guidance beside the affected section, not in a generic error wall.

Shared lifecycle treatment:
- Use one compact horizontal stage indicator when workflow context materially helps the user.
- Keep completed stages visually restrained, the current stage clear and later stages neutral.
- Do not turn the stage indicator into a second navigation system.
- Show the current owner and next action in plain language.

Responsive behaviour:
- Optimise for a 1440 px desktop viewport.
- Keep the content usable at tablet width by stacking summary and decision regions.
- Tables may use controlled horizontal scrolling where needed; keep the identifying column and action accessible.
- Avoid permanent side panels that make the central form too narrow.

Do not generate a screen yet. Apply this contract to every subsequent prompt.
```

**Acceptance check:** Stitch applies the visual contract without inventing an application shell, alternative navigation, new statuses or extra functionality.

---

## Prompt 01 — DEM-UI-01 Demands workspace

```text
Design the role-aware Demands workspace inside the established KenTender content area.

Purpose: let users find permitted Demands and see the work requiring their action without creating separate dashboards for every role.

Header:
- Title: Demands
- Description: “Capture, review and fund business needs before Procurement Planning.”
- Primary action: Create demand

Below the header, use one compact work-summary strip with:
- My drafts — 0
- Returned to me — 1
- My approvals — 1
- Budget confirmations — 1

Counts act as filters where the user has the relevant role. Do not use large cards.

Add a compact filter row:
- Search by Demand reference or title
- Status
- Current stage
- Owning unit
- Route
- Clear filters
- Show a procuring-entity selector only for a user with explicit cross-entity access

Use a compact table with columns:
- Demand
- Owning unit
- Required by
- Estimate
- Status
- Current stage or planning usage
- Current owner
- Action

Show these Ministry-scoped rows:
1. DMD-MOH-2027-014 — National digital health infrastructure upgrade | Directorate of Digital Health and Policy | 30 Sep 2027 | KES 455,000,000 | In review | Budget confirmation | Peter Otieno | Review
2. DMD-MOH-2027-019 — Digital health technical staff certification programme | Human Resources Management and Development | 31 Dec 2027 | KES 95,000,000 | Returned | Request preparation | Anne Achieng | Resolve

Keep the title visually primary within the Demand cell and the reference secondary.

Use a small inline marker for an Emergency route only if a row is Emergency; do not add an Emergency status.

Do not show the County Government of Kisumu fixture in this Ministry-scoped view. Do not add charts, recent activity, decorative totals, saved-view management or bulk workflow actions.

Include an empty filtered state: “No Demands match these filters.” with Clear filters as the only action.
```

**Acceptance check:** The page functions as a compact role-aware work queue, clearly separates status from stage, and does not expose records outside the user's scope.

---

## Prompt 02 — DEM-UI-02 Create or edit Demand

```text
Design the Create demand screen for a Ministry of Health Requester.

Purpose: capture the business need in one straightforward form without asking the Requester for specialist procurement, Strategy, Budget or Planning information.

Header:
- Title: Create demand
- Description: “Describe what is needed, why it is needed and when it is required.”
- Supporting context: Ministry of Health · Directorate of Digital Health and Policy

Use a single-page form with four compact sections.

Section 1 — Need
- Demand title
- What is needed? multiline field
- Why is it needed? multiline field
- Expected outcome multiline field
- Who will benefit? multiline field

Populate the fields for the principal fixture:
- Demand title: National digital health infrastructure upgrade
- What is needed?: “Upgrade resilient compute, storage, network and monitoring infrastructure supporting national digital health services.”
- Why is it needed?: “Existing infrastructure is approaching capacity and has recurring controller instability affecting service continuity.”
- Expected outcome: “Reliable and accessible digital clinical services with reduced service interruption and faster restoration.”
- Beneficiaries: “Public health facilities, clinical users and patients using national digital health services.”

Section 2 — Delivery need
- Required by: 30 September 2027
- Delivery location: National Data Centre and designated health facilities
- Demand route: Standard
- Technical contact: optional selector

Show short helper text under Demand route: “The route describes the need. Procurement Planning determines the procurement method later.”

Section 3 — Need items
Use an editable compact table with columns:
- Description
- Quantity
- Unit
- Estimated amount (optional)
- Remove

Rows:
1. Resilient compute and storage platform | 1 | Lot | KES 300,000,000
2. Network, monitoring and implementation services | 1 | Lot | KES 155,000,000

Use Add item as a quiet secondary action below the table.

Section 4 — Estimate and supporting information
- Requester estimate: KES 455,000,000
- Estimate basis: “Indicative market research and current infrastructure assessment”
- Confidence: Medium
- Supporting documents: compact attachment area labelled Optional

Do not show Budget line, Strategy target, procurement category, procurement method, tender details, scoring or approval fields.

Use a quiet bottom action bar:
- Cancel
- Save draft
- Submit for business review as the primary action

Do not turn this into a wizard, accordion maze or modal form.
```

**Acceptance check:** A non-specialist Requester can understand and complete the form; only business-owned information is requested.

---

## Prompt 03 — DEM-UI-03 Returned Demand correction state

```text
Design the Returned state of the Create/Edit Demand screen using DMD-MOH-2027-019.

Keep the same form structure and visual language as DEM-UI-02. Do not redesign the screen.

Header:
- Reference: DMD-MOH-2027-019
- Title: Digital health technical staff certification programme
- Status: Returned
- Current stage: Request preparation
- Primary action: Resubmit

Immediately below the header, show one restrained amber return notice:
- Returned by: Grace Wanjiku, Procurement Approval Authority
- Date: 18 August 2027
- Reason: “The proposed scope exceeds available funding by KES 15,000,000. Revise the number of participants or provide a phased delivery approach.”

Add a compact “What needs correction” list in the same notice:
- Need items and participant quantities
- Expected outcome for the revised scope
- Requester estimate

Show the existing Requester estimate of KES 95,000,000 and the stated available funding of KES 80,000,000 as read-only context near the estimate section. Do not expose the Budget Line selector to the Requester.

Visually mark only the affected fields or sections. Preserve the rest of the submitted information as normal form content.

Bottom action bar:
- Cancel demand as a quiet destructive action
- Save changes
- Resubmit as the primary action

Do not show internal validation codes, a full audit log, specialist editing controls or a generic red error banner.
```

**Acceptance check:** The Requester can immediately see who returned the Demand, why, exactly what must change and how to resubmit without being asked to manage funding.

---

## Prompt 04 — DEM-UI-04 Business review

```text
Design the Demand Review screen at the Business review stage for DMD-MOH-2027-014.

Purpose: allow the Business Approver to decide whether the need is legitimate, necessary, appropriately prioritised and owned by the correct unit.

Use a compact record header:
- DMD-MOH-2027-014
- National digital health infrastructure upgrade
- In review
- Standard
- KES 455,000,000 requester estimate
- Required by 30 September 2027

Below it, show the shared stage indicator:
- Request preparation — Complete
- Business review — Current
- Procurement enrichment — Not started
- Budget confirmation — Not started
- Final approval — Not started

Use a two-column desktop layout:

Main column:
1. Business need — read-only summary of what is needed, why, expected outcome and beneficiaries.
2. Need items — compact read-only table with the two principal fixture items.
3. Delivery — owning unit, delivery location, required date, route and technical contact.
4. Supporting information — estimate basis and attachments.

Decision column:
- Heading: Business review
- Review prompts shown as concise statements, not scored questions:
  - The need is necessary and supports the unit's responsibilities.
  - The expected outcome and beneficiaries are clear.
  - The timing and priority are justified.
  - The owning unit accepts accountability for the Demand.
- Optional comment field
- Primary action: Support demand
- Secondary actions: Return for correction and Reject demand

Use a quiet note: “Business support does not confirm funding or constitute final procurement approval.”

Do not show editable procurement category, Strategy, Budget, procurement method or Planning fields.
```

**Acceptance check:** The screen makes the Business Approver's responsibility clear without implying funding or final procurement authority.

---

## Prompt 05 — DEM-UI-05 Procurement enrichment

```text
Design the Demand Review screen at the Procurement enrichment stage for DMD-MOH-2027-014.

Purpose: let the Procurement Approval Authority refine the Demand, confirm its credible estimate and Strategy/public-value context, and identify duplication or aggregation considerations before Budget confirmation.

Keep the same record header and stage indicator used in DEM-UI-04. Procurement enrichment is Current; Request preparation and Business review are Complete.

Use a single scrollable review page with compact stacked sections.

Section 1 — Business request
- Read-only concise summary of the need, owning unit, required date, beneficiaries and Business Approver decision.
- Provide View full request as a quiet text action if needed.

Section 2 — Procurement classification and estimate
- Procurement category: ICT infrastructure and services
- Confirmed estimate: KES 455,000,000
- Estimate basis: Market research and infrastructure assessment
- Demand route: Standard
- Show Requester estimate and confirmed estimate together only to make any difference visible.

Section 3 — Need items
Use a compact editable specialist table showing the two principal fixture items, confirmed quantities, units and estimates. Avoid spreadsheet-like density.

Section 4 — Strategy alignment
Make the assignment state and action explicit. Do not show a pre-confirmed Strategy as though it appeared automatically.

Initial state:
- Heading: Strategy alignment
- Status: Not assigned
- Guidance: “Assign the primary Strategy target this Demand supports.”
- Action: Assign strategy

After assignment, replace the empty state with a compact summary:
- Primary target: At least 99.9% annual availability by 30 June 2028
- Outcome: Reliable and accessible digital clinical services
- Plan: Ministry of Health Strategic Plan 2026–2030
- Effective period: 2026–2030
- Supporting target: Restore critical services within four hours by 30 June 2028
- Status: Assigned
- Quiet actions: Change and Remove

The Assign strategy action opens the focused selector described in DEM-UI-05A. Do not use manual code entry, a large Strategy browser or an editable Strategy form on this page.

Section 5 — Public-value commitments
Use a compact table with columns Commitment, Why it applies, Proposed downstream treatment and Status.
Rows:
- Effective public services | Infrastructure supports reliable critical health services | Embedded in specification | Addressed
- Economy and efficiency | Whole-life cost, energy use and lifecycle optimisation apply | To be determined in Planning | Reason required
- Operational resilience | Redundancy, continuity and support requirements apply | Contract obligation | Addressed
- Sustainable asset lifecycle | End-of-life equipment will require controlled disposal | Delivery or disposal obligation | Addressed

Section 6 — Duplication and aggregation
- Potential duplicate: None found
- Related Demands: 2 infrastructure needs identified
- Aggregation treatment: Retain as one aggregation candidate for Planning
- Short rationale

Bottom action bar:
- Return for correction
- Save enrichment
- Send for Budget confirmation as the primary action

Do not add procurement method, tender type, evaluation criteria, supplier selection, scoring or generated tender clauses.
```

**Acceptance check:** Procurement enrichment is comprehensive but compact; Strategy is visibly unassigned or assigned, has a clear assignment action, and the screen stops before Budget confirmation and procurement-method selection.

---

## Prompt 05A — DEM-UI-05A Strategy target selector

```text
Design the focused Strategy target selector opened from the Strategy alignment section of Procurement enrichment for DMD-MOH-2027-014.

Use a right-side drawer or compact modal over the existing Demand Review page. Do not create a separate Strategy page.

Header:
- Title: Assign Strategy target
- Description: “Select the primary active target this Demand directly supports.”

Provide compact filters:
- Search target or outcome
- Strategic plan
- Effective period

Show only active targets available to the current procuring entity and owning unit. Do not expose internal codes.

List eligible results as selectable rows. Give the target the strongest visual emphasis and show its hierarchy below it.

Suggested result 1:
- Target: At least 99.9% annual availability by 30 June 2028
- Path: Ministry of Health Strategic Plan 2026–2030 > Digital Health Services > Health Information Systems > Reliable and accessible digital clinical services
- Why suggested: “Owned by the Directorate of Digital Health and Policy and relevant to ICT infrastructure and services.”
- Label: Suggested

Suggested result 2:
- Target: Restore critical services within four hours by 30 June 2028
- Path: Ministry of Health Strategic Plan 2026–2030 > Digital Health Services > Health Information Systems > Reliable and accessible digital clinical services
- Why suggested: “Related to service resilience and restoration.”

Allow exactly one Primary target using radio selection. After the primary target is selected, provide an optional Add supporting target action. Any supporting target shown must have a short Reason field.

Also provide a quiet “No direct Strategy alignment” option. If selected, show a required Reason field instead of target selection.

Footer actions:
- Cancel
- Assign target as the primary action

Do not design Strategy creation or editing, code entry, scoring, automatic confirmation or Budget selection in this drawer.
```

**Acceptance check:** A Procurement Approval Authority can see why targets were suggested, assign exactly one primary target, optionally add a justified supporting target, or record a justified absence of direct alignment.

---

## Prompt 06 — DEM-UI-06 Routine Budget confirmation

```text
Design the Demand Review screen at the mandatory Budget confirmation stage for DMD-MOH-2027-014.

Purpose: allow the Budget Officer to review and sign off the system-recommended allocation before the Demand proceeds to Final approval.

Keep the shared record header and stage indicator. Budget confirmation is Current. Clearly identify the current owner as Peter Otieno, Budget Officer.

Top summary:
- Confirmed Demand estimate: KES 455,000,000
- Proposed funding: KES 455,000,000
- Difference: KES 0
- Funding condition: Sufficient

Use a compact recommendation panel labelled “System-recommended allocation”. Do not label it Approved or Confirmed.

Show one allocation row:
- Budget: Ministry of Health Procurement Budget FY 2027/28
- Budget line: Digital clinical systems infrastructure
- Owning unit: Directorate of Digital Health and Policy
- Active
- Approved: KES 480,000,000
- Available before: KES 480,000,000
- Allocate to this Demand: KES 455,000,000
- Available after reservation: KES 25,000,000

Show a compact Strategy consistency check:
- Demand primary target: At least 99.9% annual availability by 30 June 2028
- Budget line primary target: At least 99.9% annual availability by 30 June 2028
- Result: Aligned

The Budget line must not assign, replace or silently change the Demand's Strategy target. For a mismatch state, show Needs attention and a clear Return to Procurement action instead of allowing confirmation.

Below the recommendation, show a plain confirmation statement:
“I confirm that the selected active Budget allocation is appropriate and sufficient for this Demand.”

Provide a visible confirmation checkbox or equivalent accountable sign-off control beside the statement.

Bottom actions:
- Return to Procurement
- Adjust allocation as a secondary action
- Confirm funding as the primary action

Add a quiet note: “Confirmation does not reserve funds or approve the Demand. Funding is rechecked and reserved during Final approval.”

Do not hide the Budget Officer stage because the recommendation is straightforward. Do not create a second budget dashboard, accounting entries or general-ledger fields.
```

**Acceptance check:** The distinction between recommendation, Budget Officer confirmation and later reservation is unmistakable.

---

## Prompt 07 — DEM-UI-07 Budget confirmation exception

```text
Design an exception variation of the Budget confirmation screen using DMD-MOH-2027-019.

Keep the structure and visual language of DEM-UI-06. Do not redesign the screen.

Record header:
- DMD-MOH-2027-019
- Digital health technical staff certification programme
- In review
- Current stage: Budget confirmation

Top summary:
- Confirmed Demand estimate: KES 95,000,000
- Available funding: KES 80,000,000
- Shortfall: KES 15,000,000
- Funding condition: Needs attention

Show one amber exception notice:
“Available funding does not cover the confirmed Demand estimate. Funding cannot be confirmed.”

Allocation row:
- Budget: Ministry of Health Procurement Budget FY 2027/28
- Budget line: Digital Health Workforce Capacity Development
- Active
- Available before: KES 80,000,000
- Proposed allocation: KES 80,000,000
- Unfunded amount: KES 15,000,000

Show a compact “Resolution” section with visually clear choices:
- Return for scope or estimate revision
- Select another eligible funding allocation
- Use split funding
- Record that an external Budget action is required

No option is preselected. Confirm funding is visibly unavailable in this state.

Primary action: Return to Procurement
Secondary action: Save resolution note

Include a required return note populated with:
“The proposed scope exceeds available funding by KES 15,000,000. Revise the number of participants or provide a phased delivery approach.”

Do not show a funds override, negative availability, placeholder Budget line or silent approval path.
```

**Acceptance check:** The shortfall and valid resolution paths are clear, and the design offers no way to confirm insufficient funding.

---

## Prompt 08 — DEM-UI-08 Final approval

```text
Design the Demand Review screen at the Final approval stage for DMD-MOH-2027-014.

Purpose: give the Procurement Approval Authority a concise, evidence-backed final decision view after Business support, Procurement enrichment and Budget Officer confirmation.

Keep the shared record header and stage indicator. Final approval is Current. The earlier four stages are Complete.

Use one compact readiness summary with four rows:
- Business review — Supported by James Mwangi on 12 August 2027
- Procurement enrichment — Complete by Grace Wanjiku on 14 August 2027
- Budget confirmation — Confirmed by Peter Otieno on 15 August 2027
- Blocking issues — None

Main content should summarise, not repeat entire forms:

1. Demand summary
- Need and expected outcome
- Owning unit
- Required by
- Standard route
- Confirmed estimate: KES 455,000,000

2. Strategy and public value
- Primary target: At least 99.9% annual availability by 30 June 2028
- 4 applicable commitments: 3 addressed, 1 carried to Planning with reason
- View details as a quiet action

3. Funding confirmation
- Budget line: Digital clinical systems infrastructure
- Confirmed allocation: KES 455,000,000
- Budget Officer: Peter Otieno
- Available after reservation: KES 25,000,000
- Show “Funds will be rechecked on approval.”

4. Planning hand-off
- On approval: Planning Ready
- Reservation identity will carry forward to Planning and Tendering
- Procurement method will be determined in Planning

Decision section:
- Confirmation text: “I approve this Demand for Procurement Planning and authorise the system to reserve KES 455,000,000 against the confirmed Budget allocation.”
- Provide an accountable confirmation checkbox or equivalent control.
- Primary action: Approve and reserve funding
- Secondary actions: Return and Reject

Do not create a generic legal declaration, procurement-method selector, tender action or celebratory approval graphic.
```

**Acceptance check:** The final approver can verify the complete control chain without rereading every form, and the financial effect of approval is explicit.

---

## Prompt 09 — DEM-UI-09 Approved Demand detail

```text
Design the read-only Approved Demand detail screen for DMD-MOH-2027-014 after downstream Planning use.

Header:
- DMD-MOH-2027-014
- National digital health infrastructure upgrade
- Approved
- Standard
- Confirmed estimate: KES 455,000,000
- Planning usage: Fully planned

Show a quiet message: “The approved Demand baseline is locked. Material change requires cancellation and a linked replacement Demand.”

Use compact tabs or anchor sections:
- Overview
- Items
- Strategy and value
- Funding
- Downstream usage
- Decisions and audit

Overview is selected.

Overview content:
1. Need — concise description, expected outcome, beneficiaries, owning unit, location and required date.
2. Approval chain — Requester, Business Approver, Budget Officer and Procurement Approval Authority with decision dates.
3. Funding — confirmed KES 455,000,000, reservation RSV-MOH-0001, and current condition Partially converted.
4. Downstream usage — compact table:
   - Procurement Plan Item PPI-MOH-2027-021 | KES 455,000,000 | Fully planned | View
   - Tender TND-MOH-2027-008 | KES 455,000,000 | Reservation carried forward | View
   - Contract CTR-MOH-2027-005 | KES 310,000,000 | Committed | View
5. Current funding position:
   - Original reservation: KES 455,000,000
   - Converted to commitment: KES 310,000,000
   - Remaining reserved: KES 145,000,000

Use View actions only. Do not make approved fields editable and do not provide a manual Planning Ready action.

Keep Cancel remaining Demand as a quiet authorised action only if it can be placed without competing with the primary read-only purpose. Do not add change-order or contract-management controls.
```

**Acceptance check:** The screen clearly separates the locked approved baseline from downstream usage and preserves one funding-reservation story.

---

## Prompt 10 — DEM-UI-10 Demand performance

```text
Design the manager-facing Demand performance screen inside the Demands module.

Purpose: show whether business needs are moving efficiently, receiving accountable funding confirmation and reaching Procurement Planning. This is a value and intervention view, not a decorative analytics dashboard.

Header:
- Title: Demand performance
- Description: “Monitor demand flow, funding confirmation and uptake into Procurement Planning.”
- Reporting context: Ministry of Health · FY 2027/28 · As at 31 October 2027

Add compact filters:
- Period
- Owning unit
- Demand route
- Status
- Current stage
- Apply
- Clear

Use one compact summary strip:
- Demands — 2
- Approved value — KES 455,000,000
- Returned — 1
- Awaiting action — 1
- Approved taken into Planning — 1 of 1

Do not use large KPI cards.

Section 1 — Flow and ageing
Use a compact table with columns Stage, Demands, Oldest waiting, Current attention and Action.
Rows:
- Request preparation | 1 | 13 days | Returned scope correction | View
- Business review | 0 | — | No action | —
- Procurement enrichment | 0 | — | No action | —
- Budget confirmation | 0 | — | No action | —
- Final approval | 0 | — | No action | —
- Approved | 1 | — | Fully planned | View

Section 2 — Funding control
Use a concise table or description list:
- Automatically recommended matches: 2
- Budget Officer confirmations: 1
- Recommendations adjusted: 0
- Funding exceptions: 1
- Unfunded amount requiring resolution: KES 15,000,000
Add View funding exception as the only row-level action.

Section 3 — Planning uptake
Use a compact table:
- DMD-MOH-2027-014 — National digital health infrastructure upgrade | Approved KES 455,000,000 | Fully planned | PPI-MOH-2027-021 | View

Section 4 — Strategy and public-value coverage
Show a compact table with columns Strategy outcome, Approved Demand value, Required commitments, Addressed or carried forward, Attention.
Use one row:
- Reliable and accessible digital clinical services | KES 455,000,000 | 4 | 4 | No action

Add a quiet methodology note:
“Demand value and Strategy alignment show planned support. They do not prove realised savings, benefits or outcomes.”

Do not add procurement scores, league tables, unexplained red/amber/green ratings, speculative savings, AI insights, maps or decorative charts.
```

**Acceptance check:** Managers can identify delays, funding-control performance and Planning uptake, and every figure can be traced to a small underlying record set.

---

## 3. Cross-screen review checklist

Before accepting the Stitch designs, confirm that:

1. The visible module name is **Demands** everywhere.
2. The real KenTender shell and navigation were not redesigned.
3. The five screen families remain recognisable: workspace, create/edit, review, detail and performance.
4. Review-stage outputs reuse one Demand Review layout rather than becoming unrelated pages.
5. Requesters are never asked for Strategy, Budget, procurement method or Planning codes.
6. Procurement enrichment clearly shows whether Strategy is unassigned or assigned and provides Assign, Change and Remove actions.
7. Exactly one primary Strategy target is assigned; supporting targets are optional and require reasons.
8. Strategy selection is scoped to eligible active targets and never requires manual code entry.
9. Budget matching is labelled recommended until the Budget Officer confirms it.
10. Budget confirmation checks Strategy consistency but never assigns or overwrites the Demand target.
11. Budget confirmation appears as a mandatory stage in routine and exception cases.
12. Final approval explicitly rechecks and reserves funding.
13. Approved and Planning usage are shown as separate concepts.
14. Emergency is a route, not an approval status or procurement method.
15. The approved Demand detail is read-only.
16. No screen creates a duplicate reservation or implies that Demand approval creates a commitment.
17. No screen claims realised savings, compliance, qualification or Strategy achievement without evidence.
18. Ministry-only views do not expose the County fixture.
19. The designs are compact, accessible and practical at 1440 px and tablet widths.

## 4. Explicit exclusions for Stitch

Do not design:

- application navigation, branding or account controls;
- backend workflow configuration;
- permission-rule editors;
- API or integration-management screens;
- procurement-method selection;
- statutory purchase requisition screens;
- Procurement Planning screens;
- Budget creation, revision or general-ledger screens;
- Tender, supplier, evaluation, award or contract workflows;
- automated approval or Budget Officer bypass;
- a generic workflow builder;
- a large multi-step Demand wizard;
- technical identifiers or database fields;
- separate dashboards for every role; or
- unrequested settings, exports, imports or analytics.
