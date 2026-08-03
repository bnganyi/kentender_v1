# Strategy Alignment — MVP 1 Stitch Prompts

**Document ID:** STRATEGY-MVP1-STITCH-1.0  
**Status:** Design input  
**Date:** 2 August 2026  
**Requirements baseline:** `STRATEGY-MVP1-REQ-1.0` — Locked and approved  
**Application:** KenTender  
**Module:** Strategy Alignment  
**Primary fixture:** Ministry of Health

## 1. How to use this document

1. Give Stitch the current KenTender visual reference before running these prompts.
2. Run Prompt 00 once to establish the common design contract.
3. Run Prompts 01–14 separately and in order. Each prompt should produce one screen or one focused interaction state.
4. Use the output of the preceding prompt as the visual reference for the next prompt so typography, spacing, tables, buttons and status treatments remain consistent.
5. Do not combine all prompts into one generation request.
6. Review each result against the acceptance checks beneath its prompt before proceeding.
7. Treat the Ministry of Health content as illustrative fixture data, not a statutory threshold.

Stitch is designing the authenticated application content area only. The real KenTender navigation rail, breadcrumb bar, global header and account controls are supplied by the application and are not part of these designs.

---

## Prompt 00 — Common design contract

```text
Establish the visual and interaction contract for the KenTender Strategy Alignment MVP 1 screens.

KenTender is an electronic public procurement system. Use a restrained, credible government-enterprise interface. Prioritise comprehension, completion, traceability and accessibility over decorative dashboard styling.

Design rules:
- Design only the page content area. Do not create or alter the application navigation rail, breadcrumb bar, global header, notifications, account controls or top toolbar.
- Use the existing KenTender typography, navy primary colour, neutral grey surfaces, compact spacing and modest borders from the supplied reference.
- Use a maximum content width consistent with the current application. Avoid oversized hero areas and decorative illustrations.
- Use compact tables, concise summaries and clear hierarchy. Do not create large KPI-card walls.
- Show codes and titles together wherever a business record is identified.
- Show status using text and a restrained badge or dot. Never rely on colour alone.
- Use these action labels consistently: Start, Continue, Review, Resolve and View.
- Use one clear primary action per screen. Secondary actions must be visually quieter.
- Use sentence case for headings and labels.
- Provide visible focus states, accessible labels, keyboard-operable controls and adequate contrast.
- Use inline validation beside the field or row requiring correction.
- Use “Needs attention” for performance requiring intervention. Do not use “Failed”.
- Do not show scores, weights, ranks, grades, pass/fail ratings or decorative progress rings.
- Do not imply that a strategy objective automatically becomes a tender requirement or evaluation criterion.
- Do not expose raw database or DocType terminology.
- Do not add unrequested analytics, settings, exports, imports, charts, AI suggestions or workflow steps.

Responsive behaviour:
- Optimise the primary design for a 1440 px desktop viewport.
- At narrower widths, stack summary and detail regions without hiding required actions.
- Tables may use controlled horizontal scrolling where necessary; preserve the first identifying column and action access.

Use the Ministry of Health fixture consistently:
- Plan: MOH-SP-2026-2030 — Ministry of Health Strategic Plan 2026–2030
- Version: 1
- Programme: MOH-PROG-DH — Digital Health Services
- Sub-programme: MOH-SUB-HIS — Health Information Systems
- Outcome: MOH-OUT-01 — Reliable and accessible digital clinical services
- Indicator: MOH-IND-01 — Availability of core clinical information systems
- Target: MOH-TGT-01 — At least 99.9% annual availability by 30 June 2028
- Baseline: 97.8% as at 30 June 2026

Use this contract for every subsequent Strategy Alignment screen. Do not generate a screen yet.
```

**Acceptance check:** Stitch acknowledges or applies the visual contract without inventing navigation, modules or functionality.

---

## Prompt 01 — STR-UI-01 Strategy Portfolio

```text
Design the Strategy Portfolio screen inside the established KenTender content area.

Purpose: help an authorised user find strategic plans, see assigned governance work and identify measurement attention without turning the page into an analytics dashboard.

Header:
- Title: Strategy Alignment
- Description: “Govern strategic outcomes, public-value commitments and performance targets used across procurement.”
- Primary action: Create strategic plan

Below the header, use one compact summary strip with four items:
- Active plans — 2
- Awaiting review — 1
- Measurements due — 3
- Needs attention — 1

Each item is a simple count and label, not a large card. Counts act as filters where applicable.

Add a compact filter row:
- Search by plan code or title
- Plan type
- Period
- Status
- Entity selector only for users with cross-entity authority
- Clear filters

Main content: a compact table with columns:
- Plan
- Type
- Effective period
- Version
- Status
- Current attention
- Action

Use these rows:
1. MOH-SP-2026-2030 — Ministry of Health Strategic Plan 2026–2030 | Entity Strategic Plan | 1 Jul 2026–30 Jun 2030 | v1 | Active | 1 target needs attention | View
2. MOH-DHT-2026-2029 — Digital Health Transformation Strategy | Programme Strategy | 1 Jul 2026–30 Jun 2029 | v1 | Active | 2 measurements due | View
3. MOH-SP-2030-2034 — Ministry of Health Strategic Plan 2030–2034 | Entity Strategic Plan | 1 Jul 2030–30 Jun 2034 | v1 | Submitted | Awaiting review | Review

Show plan code above or beside the title. Use only these plan statuses where needed: Draft, Submitted, Returned, Approved, Active, Superseded and Archived.

Add a small “My work” section only if it remains compact. Show three linked rows: review submitted plan, submit overdue measurement, resolve off-track target. Do not duplicate the portfolio table.

Include an empty-state variant for no matching filters: “No strategic plans match these filters.” with Clear filters as the only action.

Do not add charts, trend graphics, recent-activity feeds, strategy scores, compliance percentages or global navigation.
```

**Acceptance check:** The page works as a portfolio and work-entry screen; the four counts remain compact and every row has one clear next action.

---

## Prompt 02 — STR-UI-02 Plan Overview

```text
Design the Plan Overview screen for the active Ministry of Health plan.

Use a compact plan workspace header:
- MOH-SP-2026-2030
- Ministry of Health Strategic Plan 2026–2030
- Version 1
- Active
- Effective 1 July 2026–30 June 2030

Use these workspace tabs and no others:
- Overview
- Structure
- Value Commitments
- Measurement
- Downstream Usage
- Review
- Audit

Overview is selected.

Main layout:
1. “Plan details” section with a clean two-column description list:
   - Plan type: Entity Strategic Plan
   - Procuring entity: Ministry of Health
   - Effective period: 1 July 2026–30 June 2030
   - Version: 1
   - Status: Active
   - Description: “Strategic direction for accessible, resilient and cost-effective national health services.”
2. “Plan structure” compact summary showing:
   - 2 programmes
   - 3 sub-programmes
   - 6 outcomes
   - 8 indicators
   - 10 targets
   Include a secondary View structure action.
3. “Public-value commitments” compact summary:
   - 8 commitments
   - 5 required considerations
   - 3 recommended considerations
   Include a secondary View commitments action.
4. “Performance attention” compact table with columns Target, Period, Result, Next action. Show:
   - MOH-TGT-01 — At least 99.9% annual availability by 30 June 2028 | September 2027 | At risk | View measurement
   - MOH-TGT-02 — Restore critical service within 4 hours | October 2027 | Measurement due | Submit measurement

Because this plan is Active, display all plan-definition fields as read-only. Show a quiet message: “Active plan versions are locked. Create a successor version to make material changes.” Provide Create successor version only to authorised users as a secondary action.

Do not create editable form fields, charts, scores or a second navigation system.
```

**Acceptance check:** Active-version immutability is obvious, and the page summarises rather than duplicates the detail tabs.

---

## Prompt 03 — STR-UI-03 Plan Structure

```text
Design the Plan Structure screen for a Draft successor version of the Ministry of Health plan.

Retain the established plan workspace header and tabs. Select Structure. Show status Draft and version 2.

Purpose: build and review the typed hierarchy Programme → optional Sub-programme → Strategic Outcome → Performance Indicator → Performance Target.

Use a two-region desktop layout:
- Left: a navigable hierarchy tree occupying about 40% of the content width.
- Right: a focused detail panel for the selected item occupying about 60%.

Tree behaviour and content:
- Show code and title at every level.
- Use distinct text labels or small type tags for Programme, Sub-programme, Outcome, Indicator and Target.
- Do not use icons alone to distinguish record types.
- Allow expand/collapse, keyboard navigation and selection.
- Include a compact Add menu that offers only valid child types for the selected item.
- Do not create a placeholder Sub-programme when none is needed.

Expanded sample branch:
- Programme — MOH-PROG-DH — Digital Health Services
  - Sub-programme — MOH-SUB-HIS — Health Information Systems
    - Outcome — MOH-OUT-01 — Reliable and accessible digital clinical services
      - Indicator — MOH-IND-01 — Availability of core clinical information systems
        - Target — MOH-TGT-01 — At least 99.9% annual availability by 30 June 2028

Select MOH-OUT-01. The right detail panel shows:
- Type: Strategic Outcome
- Code and title
- Description
- Responsible function: Directorate of Digital Health
- Executive owner: Director, Digital Health
- Linked value commitments: Service availability; Infrastructure resilience
- Child summary: 1 indicator, 1 target
- Actions: Edit and Add indicator

Show an inline warning on a second outcome in the tree: “Indicator required”. At the top of the content, show a compact status line: “1 structure issue to resolve before submission” with Resolve.

Editing is allowed only because the plan version is Draft. Do not use nested accordions, a giant editable table, drag-and-drop as the only reorder method, or raw database forms.
```

**Acceptance check:** Outcome, Indicator and Target are visibly distinct; optional Sub-programmes are supported; one selected node drives one adjacent detail panel.

---

## Prompt 04 — STR-UI-04 Structure Item Editor

```text
Starting from the approved Plan Structure screen, design the focused right-side drawer used to create or edit one hierarchy item. Show the “Add performance target” state.

Keep the hierarchy visible but dimmed behind the drawer. The drawer must be wide enough for a clear single-column form and must not become a full-page raw record editor.

Drawer header:
- Add performance target
- Parent path: Digital Health Services / Health Information Systems / Reliable and accessible digital clinical services / Availability of core clinical information systems

Fields in this order:
1. Target code — MOH-TGT-01
2. Target title — At least 99.9% annual availability by 30 June 2028
3. Comparison direction — At least
4. Target value — 99.9
5. Unit — % (read-only from the parent indicator)
6. Baseline status — Known
7. Baseline value — 97.8
8. Baseline as at — 30 June 2026
9. Baseline source — Approved infrastructure-monitoring report
10. Tolerance — 99.8
11. Period start — 1 July 2027
12. Period end — 30 June 2028
13. Benefit owner — Director, Digital Health
14. Measurement verifier — Head of Monitoring and Evaluation

Footer actions:
- Primary: Save target
- Secondary: Cancel

Interaction requirements:
- Fields change by hierarchy item type; do not show irrelevant target fields in Programme, Sub-programme, Outcome or Indicator editors.
- Type-compatible units and comparison directions only.
- If baseline status is “To be established” or “Not applicable”, hide Known-baseline fields and explain the consequence briefly.
- Show inline errors for missing or incompatible values.
- On successful save, close the drawer, select the new target in the tree and update counts.
- Prevent editing when the plan is Approved or Active.

Do not add an approval checkbox, completion declaration, score or separate Save draft step.
```

**Acceptance check:** The drawer captures exactly the target definition, handles conditional baseline fields and leaves actual results for the Measurement screens.

---

## Prompt 05 — STR-UI-05 Public Value Objective Catalogue

```text
Design the Public Value Objective Catalogue screen.

This is a reusable governed catalogue, separate from any one strategic-plan hierarchy. It does not automatically create tender criteria.

Header:
- Title: Public Value Objective Catalogue
- Description: “Maintain approved objectives that strategic plans may adopt and downstream value cases may consider.”
- Primary action: Create objective

Compact filters:
- Search by code or title
- Pillar
- Source type
- Applicability
- Scope
- Status
- Clear filters

Use a compact table with columns:
- Objective
- Pillar
- Source
- Applicability
- Default guidance
- Version
- Status
- Action

Show these rows:
- PVO-EFT-01 — Improve availability of critical health services | Strategic and service outcomes | Entity Strategy | Demand-selected | Strategic outcome | v1 | Active | View
- PVO-ECO-01 — Reduce whole-life infrastructure cost | Economy and whole-life value | Management Objective | Category-triggered | Demand gate | v1 | Active | View
- PVO-RES-01 — Improve continuity of critical services | Contract performance and resilience | Entity Strategy | Procurement-type-triggered | Contract obligation or KPI | v1 | Active | View
- PVO-SUS-02 — Ensure compliant handling of replaced ICT equipment | Sustainability and asset stewardship | Act | Asset-triggered | Asset or disposal control | v1 | Active | View
- PVO-INT-01 — Minimise uncontrolled contract changes | Integrity and accountability | Policy | Universal consideration | Reporting only | v1 | Submitted | Review

Show a short explanatory note near Default guidance: “Guidance suggests where an objective may be treated. Downstream approval is still required.”

Use the controlled pillars and statuses. Do not show weights, objective scores, legal-compliance percentages or every legal provision as a separate objective.

Include an empty-filter state with Clear filters. Do not add plan commitments to this screen.
```

**Acceptance check:** The catalogue is clearly reusable and governed, with no implication that an objective directly imposes bidder or tender treatment.

---

## Prompt 06 — STR-UI-06 Public Value Objective Editor

```text
Design the focused create/edit screen for one Public Value Objective. Show a Draft objective.

Header:
- Title: Create public value objective
- Description: “Define a reusable objective and the conditions under which it may be considered.”
- Status: Draft

Use four concise form sections on one page, not a multi-step wizard.

Section 1 — Objective
- Objective code: PVO-SUS-02
- Version: 1, system-controlled
- Title: Ensure compliant handling of replaced ICT equipment
- Pillar: Sustainability and asset stewardship
- Description
- Scope: Procuring entity
- Procuring entity: Ministry of Health

Section 2 — Authority and ownership
- Source type: Act
- Source reference: Public Procurement and Asset Disposal Act — applicable asset-disposal provisions
- Responsible function: Supply Chain Management Services
- Effective from: 1 July 2026
- Effective to: 30 June 2030

Add a quiet note: “The reference supports auditability and does not replace the authoritative legal source.”

Section 3 — Applicability
- Applicability mode: Asset-triggered
- Trigger rows with Trigger type and Trigger value
- Example trigger: Asset condition | Replacement or end of useful life
- Add trigger

Only simple inclusion triggers are allowed. Do not add a script editor, nested rule groups or AND/OR expression builder.

Section 4 — Guidance
- Measure guidance: “Track the proportion of replaced ICT equipment transferred, reused or disposed through an authorised route.”
- Evidence guidance: “Asset register update, inspection record, transfer or disposal approval and completion record.”
- Default enforcement guidance: Asset or disposal control

Footer:
- Primary: Save objective
- Secondary: Cancel
- Show Submit for review only after the draft saves and readiness passes.

Inline validation must identify missing fields or triggers. Approved and Active versions are read-only; material change uses Create successor version.

Do not add tender criteria, bidder evidence fields, weights, scoring or an automatic enforcement toggle.
```

**Acceptance check:** Source, applicability and guidance are separate; the trigger builder is deliberately simple; the screen does not author tender rules.

---

## Prompt 07 — STR-UI-07 Plan Value Commitments

```text
Design the Value Commitments tab for Draft version 2 of the Ministry of Health strategic plan.

Purpose: adopt selected Active Public Value Objectives into this plan without copying their definitions.

Header within the tab:
- Title: Plan value commitments
- Description: “Select the public-value objectives this plan will carry forward and connect each commitment to a strategic outcome or target.”
- Progress text: 7 of 8 commitments complete
- Primary action: Add commitment

Use a compact table with columns:
- Commitment
- Consideration level
- Plan rationale
- Linked strategy
- Owner
- Status
- Action

Rows:
- PVO-EFT-01 — Improve availability of critical health services | Required consideration | Protect continuity of essential digital clinical services | MOH-OUT-01 and MOH-TGT-01 | Director, Digital Health | Complete | Review
- PVO-ECO-01 — Reduce whole-life infrastructure cost | Required consideration | Ensure infrastructure decisions consider acquisition, energy, maintenance and disposal cost | MOH-OUT-01 | Head, ICT Infrastructure | Complete | Review
- PVO-SUS-02 — Ensure compliant handling of replaced ICT equipment | Required consideration | Connect ICT replacement to lawful asset stewardship | No link selected | Supply Chain Director | Needs attention | Resolve
- PVO-LOC-01 — Develop internal and local technical capability | Recommended consideration | Reduce dependency and strengthen service support | MOH-OUT-01 | Director, Digital Health | Complete | Review

Selecting Add commitment opens a focused selector drawer:
- Search and filters reduce the list to applicable Active objectives.
- Each result shows code, title, pillar, why applicable and default guidance.
- Already selected objectives cannot be selected again.
- After selecting an objective, require plan rationale, consideration level, responsible owner and at least one link to an Outcome or Performance Target.

Add explanatory text for Required consideration: “A downstream value case must include this objective or record an approved not-applicable reason.”

Make clear that Recommended and Available are different consideration levels, not scores. Do not display the whole catalogue by default, copy objective definitions into editable fields, or add tender-treatment controls.
```

**Acceptance check:** The page shows adoption and linkage, not duplication; the unresolved commitment visibly blocks readiness at its point of correction.

---

## Prompt 08 — STR-UI-08 Measurement Register

```text
Design the Measurement tab for the active Ministry of Health strategic plan.

Purpose: show periodic actual results separately from target definitions and route measurement work.

Header within the tab:
- Title: Performance measurements
- Description: “Submit and verify period results against approved performance targets.”
- Primary action: Submit measurement

Use four compact filter counts in one strip:
- Due — 2
- Submitted — 1
- Verified — 8
- Needs attention — 1

Add filters:
- Search target
- Programme
- Measurement period
- Workflow status
- Result status
- Clear filters

Use a compact table with columns:
- Target
- Period
- Target value
- Actual
- Result
- Workflow
- Corrective action
- Action

Rows:
- MOH-TGT-01 — At least 99.9% annual availability by 30 June 2028 | September 2027 | ≥99.9% | 99.82% | At risk | Verified | Open | View
- MOH-TGT-01 — At least 99.9% annual availability by 30 June 2028 | October 2027 | ≥99.9% | 99.96% | On track | Verified | None required | View
- MOH-TGT-02 — Restore critical service within 4 hours | October 2027 | ≤4 hours | — | No data | Due | — | Submit measurement
- MOH-TGT-03 — Complete regional deployment by 31 December 2027 | Q2 2027/28 | Achieve by date | 80% milestones | At risk | Submitted | Pending verification | Review

Keep workflow status separate from result status. Result statuses are On track, At risk, Off track, Not due or No data. Workflow statuses are Draft, Submitted, Returned, Verified or Rejected.

Verified rows are read-only. Corrections create a superseding measurement rather than editing the original. Use text as well as colour for every status.

Do not add target editing, a chart per row, performance scoring or a “mark complete” checkbox.
```

**Acceptance check:** Actuals are visibly period records, workflow and result states are distinct, and each row offers only the valid next action.

---

## Prompt 09 — STR-UI-09 Submit Measurement

```text
Design the focused Submit Measurement screen for MOH-TGT-01.

Header:
- Title: Submit performance measurement
- Target: MOH-TGT-01 — At least 99.9% annual availability by 30 June 2028
- Parent path: Digital Health Services / Health Information Systems / Reliable and accessible digital clinical services

At the top, show a compact read-only target reference:
- Indicator: Availability of core clinical information systems
- Target: At least 99.9%
- Tolerance: 99.8%
- Baseline: 97.8% as at 30 June 2026
- Frequency: Monthly
- Data source: Approved infrastructure-monitoring report

Form fields:
1. Measurement period — September 2027
2. Actual value — 99.82
3. Unit — % and read-only
4. Measurement date — 3 October 2027
5. Evidence source — Infrastructure monitoring platform
6. Evidence reference — Select or attach existing authorised evidence
7. Commentary — optional

After the actual value is entered, show a derived preview:
- Variance: −0.08 percentage points
- Result: At risk
- Explanation: “Actual is below the 99.9% target but remains within the 99.8% tolerance.”

Actions:
- Primary: Submit measurement
- Secondary: Save draft
- Tertiary: Cancel

Validation:
- Prevent a duplicate measurement for the same target and period.
- Require a type-compatible value, measurement date, evidence source and evidence reference.
- If correcting a prior Verified record, show the prior record and require Create corrected measurement with a supersession reason; never edit the verified result.

Do not ask the submitter to declare that the result is correct, select the result status manually or approve their own evidence.
```

**Acceptance check:** The system derives the result, collects one evidence reference and prevents duplicate or in-place historical changes.

---

## Prompt 10 — STR-UI-10 Verify Measurement

```text
Design the Verify Measurement screen for the submitted September 2027 result against MOH-TGT-01.

Header:
- Title: Verify performance measurement
- Target: MOH-TGT-01 — At least 99.9% annual availability by 30 June 2028
- Workflow status: Submitted
- Derived result: At risk

Use a clear two-column comparison region:

Left — Approved target
- Indicator
- Target: ≥99.9%
- Tolerance: 99.8%
- Baseline: 97.8% as at 30 June 2026
- Period: September 2027
- Expected data source

Right — Submitted result
- Actual: 99.82%
- Variance: −0.08 percentage points
- Measurement date: 3 October 2027
- Evidence source
- Submitted by and submitted date
- Commentary

Below the comparison, show an embedded evidence viewer or a View evidence action that opens the existing authorised evidence. Do not require a duplicate upload.

Decision area:
- Verification comments
- Primary action: Verify
- Secondary actions: Return for correction and Reject

Interaction rules:
- Return and Reject require comments.
- Verify may accept optional comments.
- The verifier cannot be the submitter; if they are the same user, disable all decisions and explain the segregation rule.
- Verifying an Off track result must open a corrective-action requirement before completion unless an authorised exception is recorded.
- For this At risk example, offer “Create corrective action after verification” as a clear follow-up, not a mandatory declaration.

Do not allow editing of the submitted actual, selecting a different result status or replacing evidence from this screen.
```

**Acceptance check:** Verification compares approved target and submitted evidence, enforces segregation, and never permits the verifier to rewrite the result.

---

## Prompt 11 — STR-UI-11 Corrective Actions

```text
Design the Corrective Actions view reached from the Measurement tab.

Header:
- Title: Strategy corrective actions
- Description: “Track and verify actions raised from measured strategic underperformance.”
- Primary action: Create corrective action, shown only to authorised users

Add compact filters:
- Search target or action
- Owner
- Due status
- Action status
- Clear filters

Use a compact table with columns:
- Target and measurement
- Corrective action
- Owner
- Due date
- Status
- Due state
- Action

Rows:
- MOH-TGT-01 / September 2027 | Resolve storage-controller instability and confirm service stability | Head, ICT Infrastructure | 31 October 2027 | In progress | Due in 8 days | Continue
- MOH-TGT-04 / Q1 2027/28 | Validate regional network redundancy plan | Infrastructure Programme Lead | 15 October 2027 | Submitted for verification | Awaiting verification | Review
- MOH-TGT-05 / August 2027 | Complete delayed energy baseline assessment | Facilities Director | 30 September 2027 | Open | Overdue | Start

Selecting the first row opens a focused detail panel showing:
- Affected target and measurement
- Action
- Expected result
- Owner
- Due date
- Timeline of status changes
- Completion evidence area
- Valid next action based on role and state

Use only these statuses: Open, In progress, Submitted for verification, Verified complete and Cancelled.

The action owner cannot verify their own action. Cancellation requires an authorised reason and approver. Overdue is a derived due state, not an action status.

Do not add action scoring, percentage-complete sliders, chat threads or generic project-management functionality.
```

**Acceptance check:** The screen remains a controlled corrective-action register, with status and due state separate and one valid action per row.

---

## Prompt 12 — STR-UI-12 Downstream Usage

```text
Design the Downstream Usage tab for the active Ministry of Health strategic plan.

Purpose: show read-only traceability from approved strategy to procurement and later lifecycle records. Counts and references are system-derived and cannot be edited here.

Header within the tab:
- Title: Downstream usage
- Description: “See where this plan’s targets and value commitments are referenced across procurement.”

Use one compact summary strip:
- Budget — 3 references
- Demand — 5 references
- Planning — 4 references
- Tender — 2 references
- Contract — 1 reference
- Asset — 0 references
- Disposal — 0 references

Below it, use filters:
- Module
- Strategy target
- Reference type: Primary alignment, Supporting alignment or Value commitment
- Status
- Search record reference
- Clear filters

Use a compact table with columns:
- Downstream record
- Module
- Strategy reference
- Reference type
- Current status
- Last updated
- Action

Rows:
- DEM-MOH-2027-014 — Clinical systems infrastructure refresh | Demand | MOH-TGT-01 — At least 99.9% availability | Primary alignment | Approved | 12 Sep 2027 | View
- BUD-MOH-2027-008 — Digital health infrastructure allocation | Budget | MOH-TGT-01 | Supporting alignment | Approved | 28 Aug 2027 | View
- TND-MOH-ICT-042 — Supply and installation of resilient clinical systems infrastructure | Tender | PVO-RES-01 — Improve continuity of critical services | Value commitment | Configuration | 20 Sep 2027 | View
- CTR-MOH-ICT-018 — Clinical systems infrastructure support | Contract | MOH-TGT-01 | Supporting alignment | Active | 15 Oct 2027 | View

Show a quiet note: “Historical references remain valid when a strategy version is superseded. Only references requiring remediation appear as issues.”

Add an empty-state pattern for Asset and Disposal: “No references yet. Usage will appear when authoritative downstream records link to this plan.” Do not add a manual Link record action.

Do not show attributed spend or benefits unless a valid alignment exists. Do not allow editing, deleting or relinking downstream records from this screen.
```

**Acceptance check:** Traceability is read-only and derived; empty future modules are handled honestly without appearing broken.

---

## Prompt 13 — STR-UI-13 Readiness and Review

```text
Design the Review tab for Draft version 2 of the Ministry of Health strategic plan.

Purpose: consolidate readiness issues, link users directly to correction points and present only the workflow actions allowed for the current state and role.

Header within the tab:
- Title: Readiness and review
- Description: “Resolve the required plan-definition and governance issues before submission.”
- Status: Draft
- Summary: 3 blockers, 1 warning

Use four grouped issue sections:
1. Structure — 1 blocker
2. Targets — 1 blocker
3. Value Commitments — 1 blocker
4. Governance — 1 warning

Each issue row must contain:
- Severity text: Blocker or Warning
- Specific issue
- Affected code and title
- Direct correction action: Resolve

Use these issues:
- Structure / Blocker: MOH-OUT-04 — Improve regional data exchange has no performance indicator.
- Targets / Blocker: MOH-TGT-06 — Reduce service-restoration time is missing a measurement verifier.
- Value Commitments / Blocker: PVO-SUS-02 — Ensure compliant handling of replaced ICT equipment is not linked to an outcome or target.
- Governance / Warning: Executive owner is not assigned to MOH-OUT-03.

At the bottom, show a concise readiness statement: “Submission is blocked until all blockers are resolved.”

Actions in Draft state:
- Primary: Run readiness check
- Submit for review is visible but disabled while blockers remain, with an explanation.
- Secondary: Return to overview

Also design a compact alternative state after blockers are resolved:
- “Ready for submission”
- Primary: Submit for review

Workflow action rules to preserve in later states:
- Submitted: reviewer may Return for correction; Planning Authority may Approve if review is complete.
- Approved: Planning Authority may Activate.
- Return requires a reason.
- Approver cannot be the submitter.
- Active versions are read-only.

Do not add multiple declarations, legal confirmations, completion checkboxes or a readiness score.
```

**Acceptance check:** Every blocker states what is wrong, identifies the affected record and links to its correction; submission uses one governance action without frivolous confirmations.

---

## Prompt 14 — STR-UI-14 Audit History

```text
Design the Audit tab for the active Ministry of Health strategic plan.

Purpose: provide an authorised, readable record of version, workflow, material edit and downstream-usage events without exposing raw database logs.

Header within the tab:
- Title: Audit history
- Description: “Review governed changes, decisions and usage events for this plan version.”

Add compact filters:
- Event type
- Actor
- Date range
- Record type
- Search code or reason
- Clear filters

Use a chronological compact table with columns:
- Date and time
- Event
- Record
- Actor
- State change or summary
- Reason
- Action

Rows:
- 1 Jul 2026, 09:15 | Plan activated | MOH-SP-2026-2030 v1 | Principal Secretary, Health | Approved → Active | — | View
- 28 Jun 2026, 14:40 | Plan approved | MOH-SP-2026-2030 v1 | Planning Authority | Submitted → Approved | Review complete | View
- 25 Jun 2026, 11:05 | Plan submitted | MOH-SP-2026-2030 v1 | Strategy Manager | Draft → Submitted | — | View
- 3 Oct 2027, 16:20 | Measurement submitted | MOH-TGT-01 / Sep 2027 | Performance Officer | Draft → Submitted | — | View
- 5 Oct 2027, 10:10 | Measurement verified | MOH-TGT-01 / Sep 2027 | Performance Verifier | Submitted → Verified | Evidence confirmed | View
- 12 Sep 2027, 13:30 | Downstream reference created | DEM-MOH-2027-014 | Demand Intake service | Primary alignment to MOH-TGT-01 | — | View reference

Selecting View opens a read-only detail drawer with timestamp, actor, affected record, prior state, new state, reason where required and a concise changed-fields comparison for material edits.

Show version and supersession events clearly. Preserve historical human-readable snapshots even if a successor version uses a different title.

Do not expose internal database identifiers as primary labels, raw JSON, stack traces, confidential downstream content or an undo action.
```

**Acceptance check:** The history is understandable to reviewers and auditors, distinguishes workflow from usage events, and exposes only authorised detail.

---

## 2. Cross-screen design verification

Approve the Stitch set only when all of the following are true:

- The real KenTender shell remains outside the generated designs.
- Portfolio and plan workspace patterns are consistent.
- The Plan workspace contains exactly seven tabs: Overview, Structure, Value Commitments, Measurement, Downstream Usage, Review and Audit.
- Programme, optional Sub-programme, Strategic Outcome, Performance Indicator and Performance Target are distinct.
- Public Value Objectives are a separate governed catalogue.
- Plan Value Commitments adopt catalogue objectives without copying or rewriting them.
- Enforcement guidance is presented as guidance, not an automatic tender rule.
- Target definitions and periodic measurements are separate.
- Workflow status and performance-result status are separate.
- Verified measurements are immutable; correction creates a superseding record.
- Off-track or at-risk work uses Needs attention and routes to corrective action.
- Downstream usage is derived and read-only.
- Readiness issues identify both the problem and the exact correction location.
- Approval and verification segregation is reflected in the interaction states.
- Screens use compact tables and focused drawers rather than card walls, nested accordions or raw record forms.
- Status never depends on colour alone.
- No score, weighting, ranking, pass/fail grade, AI feature or unapproved analytics has been introduced.
- Empty, returned, read-only and needs-attention states explain the next valid action.

## 3. Design handoff rule

The approved Stitch outputs are visual and interaction specifications for `STRATEGY-MVP1-REQ-1.0`. They may clarify layout and presentation but may not change the locked functional scope. Any design that introduces a new record, state, role, rule, workflow step or downstream responsibility must be rejected or handled through formal requirements change control before implementation.
