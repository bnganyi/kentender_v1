# Procurement Planning Revision Ledger

**Purpose:** Temporary assembly record for section-by-section review. It is not an implementation authority and does not replace the approved baselines.  
**Status:** Active review ledger  
**Started:** 14 August 2026  

## Locked baselines

| Layer | Baseline |
|---|---|
| Operating model | `KENTENDER-MVP-CMOM-1.1` |
| Requirements | `PLANNING-MVP1-REQ-1.9` |
| Stitch | `PLANNING-MVP1-STITCH-2.0` |
| Implementation | `PLANNING-MVP1-CURSOR-1.8` |
| Demo data | `KenTender MVP Canonical Demo Data Contract v2.7` |

The four baseline documents remain unchanged during review. Only change records marked **Approved** may be applied during final consolidation.

## Status vocabulary

- **Under review** — proposed wording is being discussed and must not be implemented as an approved change.
- **Approved** — exact delta has been accepted and shall be applied during consolidation.
- **Rejected** — not applicable.
- **Superseded** — replaced by a later change record.

## Change register

| Change ID | Subject | Requirements | Stitch | Implementation | Seed | Status |
|---|---|---:|---:|---:|---:|---|
| `PLN-CHG-001` | Procurement Planning workspace operational content | Yes | Yes | Yes | Assertions only | Approved |
| `PLN-CHG-002` | Annual Plan registration without duplicate or invented metadata | Yes | Yes | Yes | Existing record clarification | Approved |
| `PLN-CHG-003` | Separate static Stitch composition from executable behavior | No | Yes | Yes | No | Approved |
| `PLN-CHG-004` | Empty Draft Plan builder after registration | Yes | Yes | Yes | Isolated post-registration state | Approved |
| `PLN-CHG-005` | Approved Demand selection and one-step Plan Item formation | Yes | Yes | Yes | Existing scenario plus isolated fixtures | Approved |
| `PLN-CHG-006` | Populated initial Draft Plan builder | Yes | Yes | Yes | Isolated initial-Plan fixture | Approved |

---

## PLN-CHG-001 — Procurement Planning workspace operational content

**Status:** Approved  
**Approved:** 14 August 2026  
**Source:** Requirements §9.1; Stitch PLN-UI-01; Implementation Prompt 03  
**Problem:** Requirements §9.1 concentrates on scope restrictions and does not define the workspace's operational content, states or next actions. Stitch has a partial illustrative layout, while the implementation pack requires only a vague current-Plan projection and compact queue. A sparse workspace can therefore appear conformant without helping the planner understand the Plan or act on work.

### Locked design boundary

The correction shall remain a task-oriented planning workspace, not an analytics dashboard or a collection of decorative KPI cards. It shall answer:

1. Which Procuring Entity and financial year am I working in?
2. What is the state of the current Plan and any open update?
3. What requires my action now?
4. What work I initiated is waiting on Finance or professional review?
5. What is the correct next action?

The workspace is the Procurement Planner's operational landing page. Finance and Head-of-Procurement decision forms remain separate protected task surfaces. A neutral viewer may open permitted Plan detail but does not receive the planner workspace actions.

### A. Requirements delta

**Replace §9.1 in full with:**

#### 9.1 Workspace and scope

| ID | Requirement |
|---|---|
| `PLN-FR-001` | The module shall provide one role-aware, PE/FY-scoped Procurement Planning workspace as the Procurement Planner's operational landing page. |
| `PLN-FR-002` | The workspace shall require explicit authorised PE and financial-year context. Zero eligible PE scopes shall block operational use with a clear explanation; one eligible PE shall remain visibly selected; multiple eligible PEs shall require deliberate selection. No assignment-order, seed-fixture or Administrator fallback is permitted. |
| `PLN-FR-003` | For the selected PE/FY, the workspace shall show one current-Plan summary containing the Plan title and lifecycle, current Approved Version when one exists, open Draft successor when one exists, Plan Item count, approved and draft planned values where applicable, Finance-confirmation progress and current validation state. |
| `PLN-FR-004` | The workspace shall derive one capability- and state-appropriate primary next action: **Create annual plan**, **Continue planning**, **Continue plan update** or **View approved plan**. It shall not show competing primary actions or require manual version creation. |
| `PLN-FR-005` | The workspace shall provide a prioritised **Work requiring action** queue for the selected PE/FY. It shall include only work the current planner can act on: Approved Demands ready for planning, incomplete Proposed Plan Items, Finance returns, planner-remediable validation issues or stale items, Plans returned by the Head of Procurement and Draft updates with outstanding planner action. |
| `PLN-FR-006` | Work initiated by the planner but currently assigned to another actor shall appear separately as read-only **Waiting on others** context. MVP states include Awaiting Finance confirmation and Awaiting Head-of-Procurement review. These rows shall not expose the other actor's task form or decision actions. |
| `PLN-FR-007` | Each workspace row shall show work type, business title, owner Organisation Unit, amount where applicable, plain-language reason it appears, current status and one direct permitted action. Returned and blocking work shall sort before incomplete work, which shall sort before newly eligible Approved Demands. Generic **Review** actions shall not be used where a specific action is known. |
| `PLN-FR-008` | The workspace shall provide purposeful loading, failure and empty states for: no annual Plan, no actionable work, no work waiting on others, no eligible Approved Demands and no effective changes remaining in a Draft successor. A no-change Draft successor shall offer **Cancel update** and shall not be submittable. |
| `PLN-FR-009` | Current-Plan projections, queues, search, filters, counts, totals, exports, notifications and returned actions shall use the same server-side PE/OU scope and capability policy. Actions shall be absent when unauthorised, and direct route or mutation calls shall be rejected server-side. |

**Consequential requirements updates for final consolidation:**

- Add acceptance criteria proving the current-Plan states, both work sections, specific row actions and empty states.
- Keep §9.10 as the general authorization contract; §9.1 applies it specifically to the workspace projection.
- Do not introduce new Plan, task or queue records. Both workspace sections are projections over existing records and assignments.

### B. Stitch delta

**Replace the PLN-UI-01 screen contract and prompt with the following deterministic design specification.**

This prompt designs one exact reference state. Stitch shall not infer other Plan states, create substitute content or decide which data is present. Other lifecycle states shall be supplied as separately numbered variant prompts with their own complete data before they are designed.

#### Screen contract

- **Purpose:** Give the Procurement Planner an immediate view of the current Plan, work requiring their action and work waiting on another actor.
- **Primary actor:** Procurement Planner.
- **Entry point:** Procurement navigation → Procurement Planning.
- **Reads:** Authorised PE/FY scope, logical Plan, current Approved Version, open Draft successor, Plan Items, eligible Approved Demands, Finance tasks, validation issues and professional-review state.
- **Writes:** Nothing directly; actions route to the owning task or record.
- **Primary outcome:** Take the single correct next planning action.
- **Exit:** Create Plan, Plan builder, Draft update, Add approved Demands, Plan Item editor or neutral Approved Plan detail.
- **Exclude:** Finance and Head-of-Procurement decision forms, analytics dashboard, charts, contribution workbench, package abstractions and disabled unauthorised actions.

#### Prompt

Design the main content area for **PLN-UI-01 Procurement Planning workspace** using only the exact reference state below. Preserve the existing Procurement navigation, top bar and branding.

Do not create alternative data, extra rows, extra metrics, deadlines, alerts or controls. Do not use conditional phrases such as “if present.” Do not fill gaps from general procurement knowledge. If a value is not specified below, omit it.

Reference state:

- Signed-in user: Mercy Kilonzo
- Role: Procurement Planner
- Procuring Entity: Ministry of Health
- Financial year: 2027/28
- Logical Plan reference: PLN-MOH-2027-001
- Plan title: Ministry of Health Annual Procurement Plan 2027/28
- Plan lifecycle: Open
- Current Approved Version: Version 1
- Approved Version reference: PLN-MOH-2027-001-V1
- Open Draft update: None
- Active Plan Items: 1
- Approved planned value: KES 455,000,000
- Finance confirmed: 1 of 1 Plan Items
- Validation: Ready
- One Approved Demand is ready for Planning: DMD-MOH-2027-019

Header:

- Title: Procurement Planning
- Description: “Turn approved needs into funded, approved Plan Items ready for tendering.”
- Show **Procuring Entity** as visible read-only context with value **Ministry of Health**. Do not render a dropdown in this reference state because Mercy has one eligible PE.
- Show a **Financial year** select with **2027/28** selected. Do not add another financial year option to this design.
- Helper text: “These controls define the workspace view; they do not change record ownership.”
- Show one primary button: **View approved plan**.

Current Plan:

- Use one compact panel or summary strip, not a KPI-card grid.
- Panel heading: **Current Plan**
- Plan title: **Ministry of Health Annual Procurement Plan 2027/28**
- Quiet secondary reference: **PLN-MOH-2027-001**
- Status line: **Open Plan · Approved Version 1**
- Supporting text: **No plan update is currently in progress.**
- Summary values, in this order:
  - **Plan Items:** 1 active
  - **Approved value:** KES 455,000,000
  - **Finance confirmed:** 1 of 1
  - **Validation:** Ready
- Do not add another action inside the panel; the header already provides **View approved plan**.
- Do not show a Draft Version, draft value, Create Plan action, Continue update action or version selector in this reference state.

Section: Work requiring action

- Use a compact table with columns: Work item, Type, Organisation Unit, Amount, Why it needs action, Status, Action.
- Show a **Work type** select with **All work** selected and these options only: All work; Approved Demands; Plan Items; Returned work.
- Show a search input with placeholder **Search work**.
- Show exactly one row:
  - **Work item:** Digital health technical staff certification programme
  - Quiet secondary reference: **DMD-MOH-2027-019**
  - **Type:** Approved Demand
  - **Organisation Unit:** Human Resources Management and Development
  - **Amount:** KES 80,000,000
  - **Why it needs action:** HoD-approved Demand is ready to add to the FY 2027/28 Plan.
  - **Status:** Ready for planning
  - **Action:** Add to plan
- The **Add to plan** action opens PLN-UI-04 with DMD-MOH-2027-019 selected.
- Do not show the Active infrastructure Plan Item as actionable work. Do not show Finance, Head-of-Procurement, validation or stale-item rows in this reference state.

Section: Waiting on others

- Show the section heading **Waiting on others**.
- Do not render a table header or an empty row.
- Show exactly this empty-state text: **Nothing is currently waiting on another reviewer.**

Keep the page compact and task-oriented. Use business titles as primary text and the supplied record references only as quiet secondary text. Do not add charts, trends, decorative cards, generic Review buttons, creation shortcuts, activity feeds, another role's task controls or disabled unauthorised actions.

#### Separately specified Stitch variants required before final consolidation

PLN-UI-01 above covers only **Approved Plan with no Draft successor plus one Approved Demand ready for planning**. The following states remain requirements and implementation obligations, but shall not be sent to Stitch until each has an exact actor, point-in-time scenario boundary, Plan/version data, totals, rows, labels and actions:

1. `PLN-UI-01A` — no annual Plan;
2. `PLN-UI-01B` — initial Draft Plan;
3. `PLN-UI-01C` — Approved Plan with open Draft successor and planner-action work;
4. `PLN-UI-01D` — work awaiting Finance confirmation;
5. `PLN-UI-01E` — work awaiting Head-of-Procurement review; and
6. `PLN-UI-01F` — no actionable or waiting work.

No variant may be produced by asking Stitch to infer content from a conditional state description.

### C. Implementation delta

**Replace the PLN-UI-01 portion of Implementation Prompt 03 with:**

Implement PLN-UI-01 from the approved Stitch correction as one live server-scoped workspace projection.

The workspace loader shall return:

- explicit eligible/selected PE and financial year context;
- one current-Plan projection with logical lifecycle, current Approved Version, open Draft successor, item counts, approved/draft totals, Finance progress and validation;
- one server-derived primary action with label, permitted route and capability result;
- `work_requiring_action` rows containing stable work type, business title, owner OU, amount, reason, status, priority and one permitted action;
- `waiting_on_others` rows for Finance confirmation and professional review, with neutral view actions only;
- allowed filter options and purposeful state/error identifiers.

Derive the projection from live Plan, Version, Plan Item, Demand eligibility, Finance-task, validation and review-assignment records. Do not create a Workspace Work Item, duplicate task table or persisted dashboard counters.

Authorization and behavior:

- evaluate role capability, PE/OU scope, current assignment, record state and separation of duties server-side;
- never infer the first assignment or use Administrator/fixture fallback;
- never return another actor's task route or mutation action;
- revalidate every returned action on its target route/service;
- use the same predicates for rows, counts, totals, filters and search;
- use stable business-readable reasons, not client-derived interpretations;
- order returned/blocking rows before incomplete rows, then eligible Approved Demands;
- prevent duplicate rows when one record meets multiple conditions by returning the highest-priority actionable reason and retaining secondary issues in the record detail;
- load summary and both queues in one bounded projection or coordinated bounded calls; do not execute per-row queries.

Focused tests shall cover:

1. zero-, one- and multi-PE scope behavior;
2. no Plan, initial Draft, Approved-only and Approved-plus-Draft-successor states;
3. current Plan counts, totals, Finance progress and validation reconciliation;
4. each actionable work type and priority ordering;
5. Finance/review waiting rows without protected task actions;
6. specific permitted action labels and direct-route/API denial for other roles;
7. cross-PE/OU isolation, including Administrator without operational assignment;
8. loading, failure and all empty states;
9. no duplicate rows and no N+1 query pattern; and
10. responsive keyboard-accessible controls and table actions.

### D. Demo seed and scenario delta

**Permanent canonical records:** No new record is required.

During final Demo Contract consolidation, add workspace projection expectations to existing states:

| Existing state | Expected planner workspace behavior |
|---|---|
| Base Approved Version 1 | Shows the Approved current Plan and no invented actionable item; the principal Tender remains downstream context, not a planner task. |
| `SCN-PLN-ADD-001` after HoD reapproval and before source selection | `DMD-MOH-2027-019` appears once under Work requiring action with **Add to plan**. |
| `SCN-PLN-ADD-001` after Proposed item creation but before completion | `PPI-MOH-2027-022` appears once with **Complete item**. |
| After Finance confirmation is requested | The item leaves planner-action work and appears under Waiting on others as Awaiting Finance confirmation. |
| After submission for professional review | The Plan update appears under Waiting on others as Awaiting Head-of-Procurement review. |
| `SCN-PLN-REMOVE-001` after the only Draft addition is removed | Current Plan shows No changes remain and offers **Cancel update**. |

Finance-return and professional-return rows shall use isolated transactional/UI test fixtures unless an existing canonical scenario already produces them. Do not add permanent Demands, Plan Items, reservations or decisions solely to fill the workspace.

### E. Acceptance evidence

`PLN-CHG-001` may be marked implemented only when:

1. The Procurement Planner sees a current-Plan summary and one correct primary next action for every required Plan state.
2. Actionable work and waiting work are visibly separated.
3. Every row explains why it appears and offers at most one specific authorised action.
4. Finance and professional decision forms/actions remain absent from the planner workspace.
5. Counts and totals reconcile with the Plan builder for the same PE/FY.
6. Zero/single/multi-scope and cross-entity tests pass without silent defaults.
7. No new persistent queue, dashboard-counter or workspace-task record was introduced.
8. Existing canonical scenarios demonstrate the workspace without unrelated seed expansion.

### F. Open decisions

None proposed. The correction deliberately avoids charts, trend analytics, deadlines not already owned by source records and new workflow stages.

---

## PLN-CHG-002 — Annual Plan registration without duplicate or invented metadata

**Status:** Approved  
**Approved:** 14 August 2026  
**Source:** Requirements §9.2; Stitch PLN-UI-02; Implementation Prompt 03; Demo Contract §§7.5 and 7.6  
**Problem:** The current registration requirements and prompt ask the planner to enter a title and select currency and a coordinating procurement unit. The Plan title, period and reporting currency are already governed by the selected PE/FY context, while the canonical organisation data contains no `Supply Chain Management Services` Organisation Unit. The prompt therefore invites duplicate metadata and an invented organisation record. It also repeats PE/FY selection after the workspace has already established that context.

### Locked design boundary

Plan registration creates the stable annual Plan container; it does not collect Plan Item content, Budget context, workflow configuration or organisational ownership decisions. The planner deliberately selects PE/FY in PLN-UI-01, confirms the derived Plan identity in PLN-UI-02 and creates the logical Plan plus initial Draft Version 1 in one action.

The statutory procurement function is an institutional role/capability. It shall be resolved through the PE's configuration and authorised assignments when work is routed. It shall not be represented by a planner-selected Plan-level Organisation Unit unless a separately governed organisation model later establishes that requirement.

### A. Requirements delta

**Replace §9.2 in full with:**

#### 9.2 Plan registration

| ID | Requirement |
|---|---|
| `PLN-FR-010` | PLN-UI-01 shall expose **Create annual plan** as the sole PLN-UI-02 entry point when the selected authorised PE/FY has no logical Plan and the current user has create-plan capability. No generic sidebar, list-page or standalone **New Plan** action shall be provided. |
| `PLN-FR-010A` | From that explicitly selected authorised PE/FY context, the planner shall be able to create one logical annual Procurement Plan and its initial Draft Version 1 in one atomic action. |
| `PLN-FR-010B` | The workspace financial-year control shall include the current year and configured future years that are open for planning. An existing Plan for another financial year shall not suppress **Create annual plan** for the selected future year. The one-Plan invariant applies to each PE/FY pair, not to the PE across all years. |
| `PLN-FR-011` | PLN-UI-02 shall display the selected Procuring Entity and financial year as read-only confirmation. The user shall return to PLN-UI-01 to change either value; the create surface shall not repeat PE/FY selection. |
| `PLN-FR-012` | The system shall derive the display title from the PE legal name and financial year, derive the Plan period from the governed financial-year record and derive the reporting currency from PE/financial configuration. These values shall be read-only at registration. |
| `PLN-FR-013` | The system shall generate the logical Plan reference and initial Version reference. Successful creation shall record the actor, PE, financial year and time in the audit trail. |
| `PLN-FR-014` | Registration shall not capture Budget context, coordinating/responsible procurement Organisation Unit, approval settings, uploads, integration settings, Plan Item content or free-text alternatives to derived identity fields. |
| `PLN-FR-015` | Procurement-function responsibility and downstream decision assignments shall be resolved from governed PE configuration, role assignments and the current workflow state; they shall not be copied into a planner-selected Plan owner field. |
| `PLN-FR-016` | The database and service shall transactionally enforce one logical Plan per PE/FY and at most one open Draft successor. Concurrent or repeated create requests shall not produce duplicates. |
| `PLN-FR-017` | If the Plan already exists, the service shall return the existing logical Plan without mutation and the UI shall route the planner to its current permitted view with a clear message. |
| `PLN-FR-018` | A direct route or service request without current create capability for the selected PE/FY shall be rejected server-side. Administrator status and client-supplied labels shall not confer authority. |

**Consequential domain clarification for final consolidation:**

- The logical Plan may retain derived title and reporting-currency snapshots for stable display/reporting, but the client does not author them.
- Financial-year start/end dates remain governed by the financial-year source and are not separate user-maintained Plan dates.
- Remove `coordinating_procurement_unit` or its equivalent from the MVP Plan registration contract and do not replace it with a renamed owner/function field.

### B. Stitch delta

**Replace PLN-UI-02 with the following deterministic specification.**

#### Static design prompt

Design the main content area for **PLN-UI-02 Create annual procurement plan** using only the exact pre-registration state below. Preserve the existing Procurement navigation, top bar and branding.

Reference state:

- Signed-in user: Mercy Kilonzo
- Role: Procurement Planner
- Selected Procuring Entity: Ministry of Health
- Selected financial year: 2028/29
- Existing logical Plan for this PE/FY: None
- Existing FY 2027/28 Plan: Open with Approved Version 1; outside this selected workspace year
- Derived Plan title: Ministry of Health Annual Procurement Plan 2028/29
- Derived Plan period: 1 July 2028 – 30 June 2029
- Derived reporting currency: KES

Header:

- Breadcrumb: **Procurement Planning / Create annual plan**
- Title: **Create annual procurement plan**
- Description: **“Confirm the annual Plan that will contain approved needs for this Procuring Entity and financial year.”**

The content area consists of one compact confirmation panel titled **Plan identity**. Display these label-value rows in this order:

1. **Procuring Entity** — Ministry of Health
2. **Financial year** — 2028/29
3. **Plan period** — 1 July 2028 – 30 June 2029
4. **Plan title** — Ministry of Health Annual Procurement Plan 2028/29
5. **Reporting currency** — KES

Present all five values as plain read-only label-value text.

Below the rows show exactly this supporting text:

**Creating the Plan will open Draft Version 1. You can then add approved Demands as Plan Items.**

Footer actions:

- Secondary button: **Cancel**
- Primary button: **Create plan**

### C. Implementation delta

**Replace the PLN-UI-02 portion of Implementation Prompt 03 with:**

Implement PLN-UI-02 as a confirmation-and-create surface entered from the authorised PLN-UI-01 PE/FY context.

Entry and route behavior:

- PLN-UI-01 returns **Create annual plan** as its primary action only when no logical Plan exists for the selected PE/FY and the current user has create-plan capability;
- populate the workspace financial-year control with authorised current and configured future years that are open for planning; evaluate Plan existence separately for each selected PE/FY pair;
- do not let the current FY 2027/28 Plan suppress creation for selected future FY 2028/29;
- selecting that action opens PLN-UI-02 bound to the same stable PE/FY identifiers;
- do not expose PLN-UI-02 through a generic sidebar, Planning list-page **New** action or unscoped creation shortcut; and
- a direct PLN-UI-02 route must resolve and re-authorise explicit PE/FY context before rendering, otherwise return to PLN-UI-01 without exposing the create surface.

Loader and page behavior:

- require a selected PE and financial year that the current user may use for Plan creation;
- return the PE legal name, financial-year label and dates, configured reporting currency, derived Plan title, existence result and create capability from the server;
- render exactly the five Plan identity values specified by the static design as read-only text;
- render no coordinating procurement unit, responsible function, Budget context, editable title, Currency select, approval-route control, attachment control, Plan reference or Version reference on PLN-UI-02;
- Cancel returns to PLN-UI-01 without creating or mutating a record;
- while creation is in flight, disable Cancel and Create plan, change the primary label to **Creating plan…**, prevent repeat submission and use accessible busy-state semantics; do not add a progress stepper;
- if the Plan already exists, route to its current permitted view and show **“The FY {financial_year} Plan already exists. It has been opened instead.”** using the governed selected-year label;
- if create authority or PE/FY context is no longer valid, return to PLN-UI-01 and show **“You no longer have permission to create this Plan in the selected workspace.”**; and
- if creation fails without creating a Plan, remain on PLN-UI-02, preserve the read-only context and show **“The Plan could not be created. Try again.”** through the standard accessible error treatment.

Create capability:

- accept only stable selected-context identifiers needed to identify PE/FY; do not trust client display labels;
- re-evaluate role capability, PE scope, FY eligibility and the existing-Plan invariant server-side;
- derive title, period and reporting currency from governed sources;
- atomically create the logical Plan in `Open` lifecycle, initial Plan Version 1 in `Draft` state and one audit event;
- generate internal Plan and Version references server-side;
- enforce a database uniqueness constraint for logical PE/FY identity and the open-Draft invariant;
- make repeat, refresh, double-click and concurrent requests idempotent: return the existing Plan with `created = false` rather than creating or mutating a duplicate;
- create no Plan Items, Demand allocations, Finance tasks, reservations, approval tasks or publication records;
- route a newly created Plan to PLN-UI-03.

Remove the current PLN-UI-02 `coordinating procurement unit` control and any client dependency on it. If an obsolete schema field exists, stop writing or requiring it; remove it only after repository impact inspection confirms no legitimate non-Planning consumer.

Focused tests shall cover:

1. exact derived Ministry of Health FY 2028/29 display values and coexistence with the FY 2027/28 Approved Plan;
2. successful atomic logical Plan plus Draft Version 1 creation;
3. no Plan Item, allocation, Finance or approval side effects;
4. the sole PLN-UI-01 entry action, absence of generic creation entry points, zero-, one- and multi-PE users, and deliberate selection of a configured future FY;
5. cross-PE and Administrator-without-assignment denial;
6. existing Plan, repeated request, double-click and concurrent-create idempotency;
7. rollback after injected failure between Plan and Version creation;
8. rejection or disregard of client-supplied title, dates, currency, procurement unit and generated references;
9. exact redirects/messages for existing Plan, lost authority and failure; and
10. keyboard focus, disabled in-flight actions and accessible error announcement.

### D. Demo seed and scenario delta

**Permanent canonical records:** No new record is required.

Clarify the existing `PLN-MOH-2027-001` seed contract with these derived registration values:

| Field | Value |
|---|---|
| Procuring Entity | `PE-MOH` — Ministry of Health |
| Financial year | 2027/28 |
| Plan period | 1 July 2027 – 30 June 2028 |
| Display title | Ministry of Health Annual Procurement Plan 2027/28 |
| Reporting currency | KES |
| Logical lifecycle | Open |
| Initial Version | `PLN-MOH-2027-001-V1` |

The canonical seeder shall create or resolve the logical Plan and initial Version through the same domain capability or domain invariant used by production registration; it shall not insert conflicting title, currency or procurement-unit data directly. Existing downstream Version 1 approval, Plan Item, reservation and Tender records remain unchanged.

Use isolated transactional tests for the pre-registration, duplicate, concurrency and rollback states. Do not add another permanent PE, annual Plan, procurement Organisation Unit or planning user solely to populate PLN-UI-02.

The existing Draft FY 2028/29 Budget provides governed advance-planning context. At the base boundary no FY 2028/29 Procurement Plan exists. Selecting Ministry of Health / FY 2028/29 shall therefore make **Create annual plan** available to Mercy Kilonzo without changing or superseding the FY 2027/28 Plan. The UI test may create the future Plan transactionally and roll it back; the canonical base seed remains unchanged.

### E. Acceptance evidence

`PLN-CHG-002` may be marked implemented only when:

1. PLN-UI-02 contains only the five specified read-only identity values and two footer actions.
2. No coordinating procurement unit, Budget context or editable derived identity field remains.
3. One action creates exactly one logical Plan and one Draft Version 1 with no downstream side effects.
4. Repeated and concurrent requests open the existing Plan without duplication.
5. Scope and direct-service denial tests pass server-side.
6. The canonical Plan values reconcile with the seed contract and PLN-UI-03.

### F. Open decisions

None proposed. Custom Plan titles, Plan-level multi-currency and planner-selected procurement-function ownership are outside MVP unless a later evidenced requirement introduces them.

---

## PLN-CHG-003 — Separate static Stitch composition from executable behavior

**Status:** Approved  
**Approved:** 14 August 2026  
**Source:** Documentation method; applies to PLN-CHG-001 and every subsequent Planning screen  
**Problem:** Stitch prompts have been carrying interaction, authorization, validation, routing, persistence, loading and exclusion rules. Stitch produces static designs and cannot enforce those rules. When executable behavior appears only or primarily in Stitch, implementation can omit it while still claiming alignment.

### Artifact responsibility rule

| Artifact | Owns |
|---|---|
| Requirements | Normative business behavior, required and prohibited data, state transitions, authority, validation, side effects and outcomes. |
| Stitch | One exact static visual composition: actor/context data visible in that frame, headings, labels, values, component types, hierarchy, order, copy and visual emphasis. |
| Implementation prompt | All executable behavior: data sources, services, permissions, mutations, routing, loading, disabled/busy states, validation, error handling, concurrency, idempotency, prohibited controls and tests. |
| Seed/test contract | Deterministic business records, scenario boundaries, expected projections and test assertions. |

### Stitch drafting rule

A Stitch prompt shall:

- describe one named static state at one exact scenario boundary;
- provide every visible business value and row needed for that frame;
- specify only visible components, labels, order, hierarchy and copy; and
- use separate prompts for materially different static states.

A Stitch prompt shall not specify clicks, saving, routing, mutations, conditional behavior, permissions, validation logic, loading behavior, disabled-state logic, errors, concurrency, idempotency, data-source logic, or product requirements expressed as a list of prohibited fields or controls.

### Consequential correction to approved PLN-CHG-001

The approved Section 9.1 business requirements remain unchanged. During final Stitch consolidation:

1. Remove the PLN-UI-01 screen-contract `Reads`, `Writes`, `Primary outcome`, `Exit` and `Exclude` clauses.
2. Retain only the exact reference-state data and visible workspace composition.
3. Remove action destinations, conditional behavior and negative product requirements from the Stitch prompt.
4. Keep **Add to plan**, **View approved plan**, filters and empty-state text only as visible static labels in the applicable frame.
5. Preserve all action routing, authorization, prohibited-control, state-projection and empty/error behavior in the Requirements and Implementation deltas.
6. Apply the same separation when PLN-UI-01A–F are specified: each prompt shows one static frame; the implementation prompt owns transitions between them.

### Consequential correction to PLN-CHG-002

The PLN-UI-02 Stitch delta has already been reduced to the exact static confirmation frame. Cancel/Create behavior, busy state, redirects, failures and prohibited controls are specified in the Requirements and Implementation deltas instead.

### Acceptance evidence

1. Every final Stitch prompt can be rendered as one static screen without interpreting an event or business rule.
2. Every removed behavioral statement is present in Requirements or the corresponding Implementation prompt and has test coverage where applicable.
3. No implementation requirement cites Stitch as its sole source of executable behavior.

### Open decisions

None proposed. This is a documentation responsibility correction, not a new workflow or feature.

---

## PLN-CHG-004 — Empty Draft Plan builder after registration

**Status:** Approved  
**Approved:** 14 August 2026  
**Source:** Requirements §9.2; Stitch PLN-UI-03; Implementation Prompt 03; Demo Contract §7.6  
**Problem:** PLN-UI-02 now creates the Ministry of Health FY2028/29 Plan, but the current PLN-UI-03 prompt unexpectedly shows FY2027/28. It also duplicates the primary **Add approved demands** action, shows filters over an empty table, exposes a redundant **View eligible Demands** link and displays disabled validation/submission actions before a Plan Item exists. The implementation pack treats PLN-UI-03 and PLN-UI-05 as one vague table contract and does not define the post-registration outcome.

### Locked design boundary

PLN-UI-03 is the zero-Plan-Item state of the ordinary Draft Plan builder. It is not a separate workflow, dashboard or data-entry form. It confirms that Plan registration succeeded and gives the planner one useful next action: add eligible Approved Demands.

The journey is:

`PLN-UI-02 Create plan → PLN-UI-03 Empty Draft Plan builder → PLN-UI-04 Add approved Demands`

PLN-UI-03 writes nothing. Plan Items are created only through PLN-UI-04.

### A. Requirements delta

**Insert the following at the end of §9.2:**

#### 9.2.1 Initial Draft Plan builder

| ID | Requirement |
|---|---|
| `PLN-FR-019` | Successful Plan registration shall open the current Draft Version in the ordinary Plan-builder route. When the Draft contains no Plan Items, that route shall render PLN-UI-03 as its empty state; it shall not create another page type or workflow record. |
| `PLN-FR-019A` | PLN-UI-03 shall show the derived Plan title and reference, logical lifecycle, Draft Version number and reference, financial-year period, Plan Item count, Draft planned value, eligible Approved Demand count and validation state from the live selected PE/FY context. |
| `PLN-FR-019B` | When one or more eligible Approved Demands exist, PLN-UI-03 shall provide one primary action, **Add approved Demands**, which opens PLN-UI-04 in the same Plan context. The action shall not create a Plan Item by itself. |
| `PLN-FR-019C` | When no eligible Approved Demand exists, the builder shall show **No Approved Demands are currently available to add** and shall not expose an empty selection task. Eligibility shall use the same server predicate as PLN-UI-04. |
| `PLN-FR-019D` | An empty Draft shall not show Plan Item filters, row actions, duplicate add actions, validation execution or submission actions. Validation and submission become applicable only after at least one Plan Item exists. |
| `PLN-FR-019E` | The Plan builder shall not support manual blank Plan Items, packages, contribution submission, approval matrices or direct entry of Demand-owned facts. Approved Demands enter the Plan only through PLN-UI-04. |
| `PLN-FR-019F` | Opening or refreshing PLN-UI-03 shall not mutate the Plan or Version. The route and its Add action shall be authorised server-side for the selected PE/FY; Administrator status without an operational Planning assignment shall not confer access. |

### B. Stitch delta

**Replace PLN-UI-03 with this exact static frame:**

Design the main content area for **PLN-UI-03 Empty Draft Plan builder** using only the exact post-registration state below. Preserve the existing Procurement navigation, top bar and branding.

Reference state:

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Procuring Entity: **Ministry of Health**
- Financial year: **2028/29**
- Plan title: **Ministry of Health Annual Procurement Plan 2028/29**
- Logical Plan reference: **PLN-MOH-2028-001**
- Plan lifecycle: **Open**
- Draft Version: **Version 1**
- Draft Version reference: **PLN-MOH-2028-001-V1**
- Plan period: **1 July 2028 – 30 June 2029**
- Plan Items: **0**
- Draft planned value: **KES 0**
- Eligible Approved Demands: **2**
- Validation: **Not run**

Header:

- Breadcrumb: **Procurement Planning / Ministry of Health Annual Procurement Plan 2028/29**
- Title: **Ministry of Health Annual Procurement Plan 2028/29**
- Quiet reference: **PLN-MOH-2028-001**
- Status line: **Open Plan · Draft Version 1**
- Supporting line: **1 July 2028 – 30 June 2029**
- Primary button: **Add approved Demands**

Below the header, show one compact summary strip with these values in this order:

1. **Plan Items** — 0
2. **Draft planned value** — KES 0
3. **Approved Demands available** — 2
4. **Validation** — Not run

Main panel:

- Heading: **Plan Items**
- Empty-state heading: **No Plan Items yet**
- Empty-state text: **“Two Approved Demands are ready to add to this annual Plan.”**

At the bottom-left of the content area show one text link: **Back to Procurement Planning**.

### C. Implementation delta

**Replace the empty-state portion of the PLN-UI-03/05 implementation contract with:**

Implement PLN-UI-03 as the zero-item rendering of the existing Draft Plan-builder route.

Loader and routing:

- after successful PLN-UI-02 creation, open the newly created Draft Version on the Plan-builder route;
- allow the authorised **Continue planning** action from PLN-UI-01 to open the same current Draft;
- resolve the logical Plan, current open Draft and capability from explicit selected PE/FY context;
- render PLN-UI-03 only when the Draft has zero included Plan Items; render the populated builder state when items exist;
- if no open Draft exists, return the state-appropriate Approved Plan or workspace route instead of manufacturing Draft Version 1;
- re-authorise direct routes and reject cross-PE, cross-FY and Administrator-without-assignment access.

Projection:

- return derived title, logical Plan reference/lifecycle, Draft Version number/reference, period, item count, Draft value, eligible Approved Demand count and validation state from live records;
- calculate the eligible count with the exact PLN-UI-04 eligibility predicate;
- do not persist counters, empty rows or a special empty-builder record;
- do not query per row or fabricate Finance progress for zero items.

Behavior:

- return **Add approved Demands** as the sole primary action only when the eligible count is greater than zero and the planner may add sources;
- the action opens PLN-UI-04 with stable Plan context and creates nothing before confirmation there;
- when the eligible count is zero, show the governed no-eligible-Demand message and no add action;
- omit filters, row controls, duplicate empty-state actions, validation execution and submission while the Draft has zero items;
- opening, refreshing, returning back or cancelling PLN-UI-04 shall leave the empty Draft unchanged;
- include no manual Plan Item creation, package grid, contribution or approval controls.

Focused tests shall cover:

1. successful FY2028/29 registration opening the exact Draft Version 1 empty state;
2. refresh/back producing no duplicate Plan or Version;
3. live reconciliation of zero items, KES 0 value, eligible count and Not run validation;
4. one Add action when eligible Demands exist and no mutation before PLN-UI-04 confirmation;
5. zero-eligible state with no unusable selection entry point;
6. automatic populated-builder rendering after the first Plan Item is formed;
7. absence of filters, validation, submission and duplicate actions in the empty state;
8. PE/FY scope and direct-route denial; and
9. keyboard focus and accessible empty-state/action labelling.

### D. Demo seed and scenario delta

**Permanent canonical records:** No new record is required.

Use the same isolated transaction introduced by `PLN-CHG-002` for future-year registration:

1. Start with no Ministry of Health FY2028/29 Procurement Plan.
2. Create the Plan through the production registration capability.
3. Assert logical Plan `PLN-MOH-2028-001`, Draft Version `PLN-MOH-2028-001-V1`, zero items, KES 0 Draft value and Not run validation.
4. Load the two isolated FY2028/29 Approved Demands specified for PLN-UI-04A/B so the eligible count is exactly 2.
5. Render PLN-UI-03, then continue to PLN-UI-04 through the single primary action.
6. Roll back or reset every fixture-owned FY2028/29 Plan, Version, Demand and allocation record.

The permanent canonical bundle remains centred on the existing FY2027/28 Approved Plan. It shall not seed a second annual Plan solely to populate this empty-state screen.

### E. Acceptance evidence

`PLN-CHG-004` may be marked implemented only when:

1. PLN-UI-02 lands on the exact newly created Draft Version 1.
2. The Plan identity and period remain consistent between PLN-UI-02 and PLN-UI-03.
3. The empty builder displays live zero-item, KES 0, eligibility and validation values.
4. Exactly one primary action continues to PLN-UI-04 and creates nothing prematurely.
5. Empty-table filters and disabled validation/submission controls are absent.
6. No separate empty-builder record, manual Plan Item path or permanent seed expansion exists.

### F. Open decisions

None proposed. PLN-UI-03 is deliberately a restrained empty state of the Plan builder.

---

## PLN-CHG-005 — Approved Demand selection and one-step Plan Item formation

**Status:** Approved  
**Approved:** 14 August 2026  
**Source:** Requirements §§9.3 and 9.5; Stitch PLN-UI-04; Implementation Prompt 03; Demo Contract §7.6  
**Problem:** The current documents correctly allow one or more Approved Demands to be selected, but the reference screen uses `DMD-MOH-2027-014` as selectable even though that Demand is already fully allocated to an Active Plan Item. The same screen mixes several conditional states into one Stitch prompt and places interaction rules in a static-design artifact. The requirements also prohibit cross-OU combination without a legal or operational basis. This turns Organisation Unit ownership into an artificial packaging boundary and frustrates consolidated or common-user procurement.

Kenya's Public Procurement and Asset Disposal Regulations require the consolidated annual Plan to identify items that may be aggregated into one procurement package or handled as common-user items. They do not make a shared owning Organisation Unit a condition of aggregation. The controlling boundaries are the Procuring Entity, lawful procurement design and retained source accountability, not an internal OU label. See [Regulations 40–41](https://new.kenyalaw.org/akn/ke/act/ln/2020/69/eng%402020-04-30).

### Locked design boundary

PLN-UI-04 is the only Demand-selection and Plan-Item-formation step:

1. The planner selects one or more eligible Approved Demands.
2. One selected Demand forms one Plan Item automatically.
3. For multiple selected Demands, the planner chooses either one Plan Item per Demand or one combined Plan Item for all selected Demands.
4. Creation happens once. PLN-UI-06 completes the resulting Plan Item; it does not select, add or regroup sources.

The dialog selects Demand records, not individual Need Items. Selecting a Demand includes every Need Item that is currently available for Planning. Source Demand, Need Item, owner OU, approved value and proposed funding lineage remain immutable and traceable.

### A. Requirements delta

**Replace §9.3 in full with:**

#### 9.3 Demand eligibility and Plan Item formation

| ID | Requirement |
|---|---|
| `PLN-FR-020` | PLN-UI-04 shall list only Demands within the selected Plan's PE/FY for which the current user has Planning authority, the Demand is Approved and Planning Ready, and at least one Need Item is not held by another open Draft allocation or effectively allocated through an Approved Plan Version. |
| `PLN-FR-021` | Each row shall show the Demand title and reference, owner OU, available Need Item count, available approved value, required-by date, proposed funding context and Planning Ready status. A partially planned Demand shall show only its remaining available Need Items and value; a fully planned Demand shall not be selectable. |
| `PLN-FR-022` | The planner may select one or more eligible Demands using row checkboxes. Selecting a Demand shall include all of its currently available Need Items; MVP shall not add a second Need-Item selection step. The source breakdown shall expose the included Need Items read-only before confirmation. |
| `PLN-FR-023` | One selected Demand shall form exactly one Proposed Plan Item without asking a formation question. The system shall create one Draft Plan Demand Allocation for each included Need Item. |
| `PLN-FR-024` | When two or more Demands are selected, PLN-UI-04 shall require one plain-language choice before creation: **One Plan Item for each Demand** or **One combined Plan Item for all selected Demands**. The screen shall show the exact resulting Plan Item count, source count, Need Item count and total value. |
| `PLN-FR-025` | Separate formation shall create one Proposed Plan Item per selected Demand. Each item shall inherit that Demand's owner OU and contain allocations for that Demand's available Need Items only. |
| `PLN-FR-026` | Combined formation shall create one Proposed Plan Item containing allocations for every selected Demand and available Need Item. It shall require a concise reason explaining the common supply, market, delivery or operational basis for procuring the requirements together. |
| `PLN-FR-027` | Different source OUs within the same PE shall not, by themselves, prohibit combined formation. A same-OU combined item shall inherit that OU; a mixed-OU combined item shall be owned at PE level with no invented coordinating OU. Every allocation shall retain its source Demand and source OU. Demands from another PE shall never be combined into the Plan. |
| `PLN-FR-028` | Combined formation shall be unavailable when the selected sources do not belong to the same Plan PE/FY, a source is no longer eligible, or a governed funding, legal or contractual restriction requires separate procurement. A category, method or schedule that cannot be reconciled during Plan Item completion shall block later submission, not cause the UI to invent an OU-based rule. |
| `PLN-FR-029` | Forming Plan Items shall not change the Approved Demand's business scope, approval state or funding decision. Draft allocations shall hold included Need Items against duplicate Planning selection while the update is open but shall become effective Planning take-up only when the Plan Version is approved. Removing the Draft item or cancelling the update shall release the hold through the governed removal path. |
| `PLN-FR-029A` | Formation shall be one atomic, idempotent server action. For an Approved Plan, the action shall create or reuse its single Draft successor and create all selected items, allocations and Draft holds in the same transaction. Concurrent eligibility changes shall fail without partial creation. |
| `PLN-FR-029B` | After formation, a single or combined result shall open PLN-UI-06. Multiple separate results shall return to the Draft Plan builder with every new item visible. Source selection and formation shall not be repeated in PLN-UI-06, PLN-UI-10 or another aggregation screen. |

**Consequential conflict correction for §9.5 final consolidation:**

- Replace `PLN-FR-031` with the same-PE/FY and governed-restriction rule in `PLN-FR-028`.
- Delete `PLN-FR-033` (**Cross-OU aggregation shall be blocked in MVP**).
- Retain the anti-splitting and lotting requirements for the dedicated §9.5 review.

### B. Stitch delta

Replace the current conditional PLN-UI-04 prompt with three exact static frames. These prompts contain visible composition only; entry, selection, creation, routing, authorization and validation belong to the requirements and implementation sections.

#### PLN-UI-04 — one Approved Demand selected

Design the main content area as a large focused dialog titled **Add approved Demands** over the Ministry of Health FY 2027/28 Procurement Plan. Preserve the existing Procurement navigation, top bar and branding.

Reference state:

- Signed-in user: Mercy Kilonzo
- Role: Procurement Planner
- Plan: Ministry of Health Annual Procurement Plan 2027/28
- Plan lifecycle: Open
- Current Approved Version: Version 1
- Open Draft update: None
- Eligible Approved Demands: 1
- Selected Approved Demands: 1

Header context:

- **Ministry of Health Annual Procurement Plan 2027/28**
- **Open Plan · Approved Version 1**
- Supporting text: **“A Draft plan update will contain this addition. Approved Version 1 remains active.”**

Top controls, in one compact row:

- Search input labelled **Search approved Demands**, empty
- Select labelled **Organisation Unit**, value **All permitted units**
- Checkbox labelled **Available to plan only**, checked

Table columns:

- selection checkbox
- Demand
- Organisation Unit
- Available Need Items
- Available value
- Required by
- Proposed funding
- Status

Show exactly one checked row:

- Demand: **Digital health technical staff certification programme**
- Quiet reference: **DMD-MOH-2027-019**
- Organisation Unit: **Human Resources Management and Development**
- Available Need Items: **1**
- Available value: **KES 80,000,000**
- Required by: **31 March 2028**
- Proposed funding: **Digital health workforce development**
- Status: **Planning Ready**

Below the table show one compact panel titled **Selected source**:

- **1 Approved Demand · 1 Need Item · KES 80,000,000**
- Demand: **Digital health technical staff certification programme**
- Proposed Budget Line: **Digital health workforce development**
- Finance confirmation: **Required after Plan Item completion**
- Text link: **View source breakdown**
- Result: **1 Plan Item will be created.**

Footer buttons:

- **Cancel**
- **Add Demand and continue**

#### PLN-UI-04A — multiple Approved Demands selected for one combined Plan Item

Design the main content area as a large focused dialog titled **Add approved Demands** over the Ministry of Health FY 2028/29 Draft Procurement Plan. Preserve the existing Procurement navigation, top bar and branding.

Reference state:

- Signed-in user: Mercy Kilonzo
- Role: Procurement Planner
- Plan: Ministry of Health Annual Procurement Plan 2028/29
- Plan lifecycle: Open
- Draft Version: Version 1
- Eligible Approved Demands: 2
- Selected Approved Demands: 2

Header context:

- **Ministry of Health Annual Procurement Plan 2028/29**
- **Open Plan · Draft Version 1**

Use the same top-control row and table columns as PLN-UI-04. Show exactly two checked rows:

1. **Clinical training laptops for digital health rollout**
   - Quiet reference: **DMD-MOH-2028-001**
   - Organisation Unit: **Human Resources Management and Development**
   - Available Need Items: **2**
   - Available value: **KES 48,000,000**
   - Required by: **31 December 2028**
   - Proposed funding: **Digital health workforce development**
   - Status: **Planning Ready**
2. **Clinical deployment laptops for digital health rollout**
   - Quiet reference: **DMD-MOH-2028-002**
   - Organisation Unit: **Directorate of Digital Health and Policy**
   - Available Need Items: **2**
   - Available value: **KES 72,000,000**
   - Required by: **31 December 2028**
   - Proposed funding: **Digital clinical systems infrastructure**
   - Status: **Planning Ready**

Below the table show:

- Section heading: **Create Plan Items**
- Summary: **2 Approved Demands · 2 Organisation Units · 4 Need Items · KES 120,000,000**
- Question: **How should these Demands be added?**
- Unselected radio: **One Plan Item for each Demand**
- Supporting text: **Creates 2 separate Plan Items.**
- Selected radio: **One combined Plan Item for all selected Demands**
- Supporting text: **Creates 1 Plan Item while retaining both Demand and funding sources.**
- Multiline field label: **Why should these requirements be procured together?**
- Field value: **Procure one standard laptop specification and deployment service for the same national digital-health rollout.**
- Result panel: **1 combined Plan Item · KES 120,000,000 · 2 Demand sources · 4 Need Items**

Footer buttons:

- **Cancel**
- **Create combined Plan Item and continue**

#### PLN-UI-04B — multiple Approved Demands selected for separate Plan Items

Use the exact PLN-UI-04A actor, Plan, controls, rows and summary. In the **Create Plan Items** section show:

- Selected radio: **One Plan Item for each Demand**
- Supporting text: **Creates 2 separate Plan Items.**
- Unselected radio: **One combined Plan Item for all selected Demands**
- Supporting text: **Creates 1 Plan Item while retaining both Demand and funding sources.**
- Result panel: **2 Plan Items · KES 120,000,000 · 2 Demand sources · 4 Need Items**

Footer buttons:

- **Cancel**
- **Create 2 Plan Items**

### C. Implementation delta

**Replace the PLN-UI-04 portion of Implementation Prompt 03 with:**

Implement PLN-UI-04 as the sole source-selection and Plan-Item-formation task.

Entry and loader:

- accept an authorised Plan context and optional preselected Demand identifier from PLN-UI-01, PLN-UI-03/05 or PLN-UI-09;
- re-evaluate Plan PE/FY, planner capability and source eligibility server-side before rendering and again before creation;
- list only Approved, Planning Ready Demands in the Plan PE/FY with at least one Need Item not held by another open Draft allocation and not effectively allocated in an Approved Version;
- return for each row the stable Demand identifier, title/reference, owner OU, available Need Item count, available approved value, required-by date, proposed funding label and status;
- return the read-only source breakdown for the currently selected Demand identifiers;
- do not expose `DMD-MOH-2027-014` in the canonical post-approval addition state because it is fully allocated to Active `PPI-MOH-2027-021`.

Client request:

- submit Plan identifier, expected Plan/Version concurrency token, selected Demand identifiers, `formation_mode` only for a multi-Demand selection, combination reason only for combined formation and one idempotency key;
- never accept client-supplied Need Item identifiers, available values, source OUs, funding allocations, resulting Plan Item count, Draft Version identifier or ownership result as authority.

Formation service:

- reload every selected Demand and its available Need Items under lock;
- reject zero selection, duplicate identifiers, another PE/FY, unauthorised sources, lost approval/readiness or any source that became held/effectively allocated;
- for one selected Demand, ignore/reject a supplied formation mode and create exactly one Proposed Plan Item;
- for multiple selected Demands, require `separate` or `combined`;
- for `separate`, create one Proposed Plan Item per Demand and inherit that Demand's owner OU;
- for `combined`, require a non-empty concise reason and create one Proposed Plan Item with all sources; inherit the OU only when all sources share it, otherwise set Plan Item ownership to the Plan PE with `owner_org_unit = null`;
- do not treat mixed OUs as an incompatibility; reject combination only for a different PE/FY or an explicit governed funding, legal or contractual separation restriction;
- create one immutable Draft allocation per available Need Item and retain Demand, Need Item, source OU, approved quantity/value and proposed funding lineage;
- mark those source Need Items unavailable to another open Draft selection without changing the Approved Demand or treating the allocation as effective Approved-Plan take-up;
- on an Approved Plan, create or reuse the single Draft successor and create every item/allocation/hold in the same transaction;
- on any failure, create nothing; on an idempotent repeat, return the original result;
- route a one-item result to PLN-UI-06 and a multiple-separate result to the Draft Plan builder with all created items visible.

UI behavior:

- keep selected rows and totals synchronized with the server-returned available values;
- show no formation control for zero/one selected Demand;
- for multiple selections, require one formation choice and show the exact result preview;
- show the combination-reason field only for combined formation;
- prevent repeat submission and announce loading and errors accessibly;
- if eligibility changes before confirmation, keep the dialog open, identify the unavailable Demand and refresh the selection instead of partially creating items;
- include no category, method, schedule, lotting, Finance-decision, version-management or source-editing controls.

Focused tests shall cover:

1. canonical single selection of `DMD-MOH-2027-019` and exclusion of allocated `DMD-MOH-2027-014`;
2. partial-Demand projection using only remaining Need Items/value;
3. one selection creating one item without formation mode;
4. two selections creating exactly two separate items;
5. two same-OU selections creating one combined OU-owned item;
6. two mixed-OU selections creating one combined PE-owned item with complete source-OU lineage;
7. cross-PE, lost-eligibility and governed-separation rejection;
8. Draft holds preventing duplicate selection while Approved Demand state remains unchanged;
9. Draft removal/cancellation releasing the hold and restoring eligibility;
10. Approved-Plan Draft-successor creation/reuse, rollback, idempotency and concurrent requests;
11. exact post-formation destinations with no second source-selection or aggregation step; and
12. keyboard selection, focus, accessible summaries and error association.

### D. Demo seed and scenario delta

**Permanent canonical records:** No new record is required.

Retain `SCN-PLN-ADD-001` as the canonical one-Demand path:

- immediately after HoD reapproval, PLN-UI-04 lists `DMD-MOH-2027-019` once with one available Need Item and KES 80,000,000;
- `DMD-MOH-2027-014` is not listed because its Need Items are already allocated to Active `PPI-MOH-2027-021`;
- confirmation creates/reuses Draft Version 2 and Proposed `PPI-MOH-2027-022` once;
- Draft allocation makes `DMD-MOH-2027-019` unavailable to a second open selection while preserving its Approved state; and
- `SCN-PLN-REMOVE-001` releases that Draft hold and restores Planning eligibility without hard deletion.

Use one resettable isolated UI/transaction fixture for PLN-UI-04A/B; do not add it to the permanent canonical bundle:

| Field | First source | Second source |
|---|---|---|
| Demand | `DMD-MOH-2028-001` — Clinical training laptops for digital health rollout | `DMD-MOH-2028-002` — Clinical deployment laptops for digital health rollout |
| Owner OU | `MOH-DIR-HRMD` | `MOH-DIR-DHP` |
| Available Need Items | 2 | 2 |
| Available value | KES 48,000,000 | KES 72,000,000 |
| Required by | 31 December 2028 | 31 December 2028 |
| Proposed funding label | Digital health workforce development | Digital clinical systems infrastructure |
| State | Approved; Planning Ready | Approved; Planning Ready |

The fixture shall use a transactionally created Ministry of Health FY 2028/29 Draft Plan and the exact combination reason shown in PLN-UI-04A. It shall prove both separate and mixed-OU combined formation, reset all fixture-owned records and leave the canonical base unchanged.

### E. Acceptance evidence

`PLN-CHG-005` may be marked implemented only when:

1. The canonical dialog lists only genuinely available Approved Demands and values.
2. One selected Demand creates one Plan Item without a formation question.
3. Multiple selected Demands create exactly the confirmed separate or combined structure in one action.
4. Mixed-OU combination is supported within the same PE without losing source OU or funding lineage.
5. PLN-UI-06 never repeats source selection, formation or aggregation.
6. Draft allocation holds prevent duplicate Planning selection and are released by the governed removal/cancellation path.
7. Approved-Plan addition creates/reuses one Draft successor without interrupting the current Approved Plan.
8. No permanent canonical record was added solely to populate a design variant.

### F. Open decisions

None proposed. Detailed anti-splitting validation and indicative lotting remain the subject of §9.5; this change only removes the unsupported OU barrier and fixes the one-step formation journey.

---

## PLN-CHG-006 — Populated initial Draft Plan builder

**Status:** Approved  
**Approved:** 15 August 2026  
**Source:** Requirements §§9.3 and 9.7; Stitch PLN-UI-05; Implementation Prompt 03; Demo Contract §7.6  
**Problem:** The current PLN-UI-05 prompt shows `PPI-MOH-2027-021` as a Proposed item in Draft Version 1. Canonical data instead defines that item as Active in Approved Version 1 with an operational Tender. The screen therefore contradicts the source data. It also overlaps with PLN-UI-10, which already owns the Draft-successor update against an Approved Plan, and exposes method/schedule columns, duplicate status signals and premature disabled submission controls instead of directing the planner to the next item-completion task.

### Locked design boundary

PLN-UI-05 is the populated state of an **initial Draft Plan with no Approved predecessor**. It lists the Proposed Plan Items created through PLN-UI-04 and directs the planner to complete them.

PLN-UI-10 remains the distinct update view for a Draft successor to an already Approved Plan. It focuses on additions, changes and proposed removals against the operational Approved baseline. PLN-UI-05 shall not duplicate that comparison model.

The initial-Plan journey is:

`PLN-UI-03 Empty Draft → PLN-UI-04 form Plan Items → PLN-UI-05 populated Draft builder → PLN-UI-06 complete each item`

### A. Requirements delta

**Insert the following after §9.3:**

#### 9.3.1 Populated initial Draft Plan builder

| ID | Requirement |
|---|---|
| `PLN-FR-029C` | The ordinary Plan-builder route shall render PLN-UI-05 when an initial Draft Version has one or more included Proposed Plan Items and no Approved predecessor. PLN-UI-05 is a populated state of the same builder used by PLN-UI-03, not a separate workflow record. |
| `PLN-FR-029D` | PLN-UI-05 shall show the Plan and Draft identity, Plan Item count, Draft planned value, Planning-completeness progress, Finance-confirmation progress and current validation state from live records. |
| `PLN-FR-029E` | Each Plan Item row shall show the business title, reference, owner OU or PE-level ownership, planned value, Planning status, Finance status, validation status and one state-specific primary action. Detailed method and schedule fields belong in PLN-UI-06 and shall not be expanded into builder columns. |
| `PLN-FR-029F` | For an incomplete Proposed Plan Item, the primary row action shall be **Complete item** or **Continue item** and shall open PLN-UI-06. A waiting or completed item shall use a state-appropriate neutral action and shall never expose another actor's Finance or professional decision form. |
| `PLN-FR-029G` | **Add approved Demands** shall open PLN-UI-04 in the same initial Draft context. It shall not create blank Plan Items or repeat sources already held by the Draft. |
| `PLN-FR-029H` | A removable draft-only item shall expose a restrained row-menu action leading to PLN-UI-05A. The menu shall not issue the removal mutation directly. Whole-item removal behavior remains governed by §9.8. |
| `PLN-FR-029I` | Validation and submission controls shall be state-appropriate. An initial Draft with incomplete items shall explain the outstanding work and shall not present submission as an available action. Submission shall appear only when the complete §10.2 readiness predicate is satisfied. |
| `PLN-FR-029J` | PLN-UI-05 shall not show Approved-Version comparison, change reasons, raw version diffs or unchanged operational items. Those concepts belong only to PLN-UI-10 when an Approved predecessor exists. |
| `PLN-FR-029K` | Opening, filtering, searching or refreshing the builder shall not mutate Plan or item state. All counts, totals, statuses, rows and actions shall apply the same server-side PE/FY scope and capability policy. |

### B. Stitch delta

**Replace PLN-UI-05 with this exact static frame:**

Design the main content area for **PLN-UI-05 Populated Draft Plan builder** using only the exact initial-Plan state below. Preserve the existing Procurement navigation, top bar and branding.

Reference state:

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Procuring Entity: **Ministry of Health**
- Financial year: **2028/29**
- Plan title: **Ministry of Health Annual Procurement Plan 2028/29**
- Logical Plan reference: **PLN-MOH-2028-001**
- Plan lifecycle: **Open**
- Draft Version: **Version 1**
- Draft Version reference: **PLN-MOH-2028-001-V1**
- Approved predecessor: **None**
- Plan Items: **2**
- Draft planned value: **KES 120,000,000**
- Planning complete: **0 of 2**
- Finance confirmed: **0 of 2**
- Validation: **Not run**

Header:

- Breadcrumb: **Procurement Planning / Ministry of Health Annual Procurement Plan 2028/29**
- Title: **Ministry of Health Annual Procurement Plan 2028/29**
- Quiet reference: **PLN-MOH-2028-001**
- Status line: **Open Plan · Draft Version 1**
- Supporting line: **1 July 2028 – 30 June 2029**
- Button: **Add approved Demands**

Below the header, show one compact summary strip with these values in this order:

1. **Plan Items** — 2
2. **Draft planned value** — KES 120,000,000
3. **Planning complete** — 0 of 2
4. **Finance confirmed** — 0 of 2
5. **Validation** — Not run

Show one restrained information strip:

- **2 Plan Items need planning details before Finance confirmation can be requested.**

Above the table show one compact toolbar:

- Select labelled **Organisation Unit**, value **All permitted units**
- Select labelled **Status**, value **All statuses**
- Search input labelled **Search Plan Items**, empty

Section heading: **Plan Items**

Use a compact table with these columns:

- Plan Item
- Organisation Unit
- Planned value
- Planning
- Finance
- Validation
- Action

Show exactly two rows:

1. Plan Item: **Clinical training laptops for digital health rollout**
   - Quiet reference: **PPI-MOH-2028-001**
   - Organisation Unit: **Human Resources Management and Development**
   - Planned value: **KES 48,000,000**
   - Planning: **Not started**
   - Finance: **Not requested**
   - Validation: **Not run**
   - Primary row action: **Complete item**
   - Restrained overflow icon at the end of the row
2. Plan Item: **Clinical deployment laptops for digital health rollout**
   - Quiet reference: **PPI-MOH-2028-002**
   - Organisation Unit: **Directorate of Digital Health and Policy**
   - Planned value: **KES 72,000,000**
   - Planning: **Not started**
   - Finance: **Not requested**
   - Validation: **Not run**
   - Primary row action: **Complete item**
   - Restrained overflow icon at the end of the row

At the bottom-left of the content area show one text link: **Back to Procurement Planning**.

### C. Implementation delta

**Replace the populated initial-Draft portion of the PLN-UI-03/05 implementation contract with:**

Implement PLN-UI-05 as the populated initial-Draft rendering of the ordinary Plan-builder route.

Route and projection:

- render PLN-UI-05 only when the current editable Version has included Proposed Plan Items and no Approved predecessor;
- route a Draft successor with an Approved predecessor to PLN-UI-10 instead of rendering an initial-Plan screen;
- load Plan/Version identity, live item count and Draft value, Planning-completeness progress, Finance-confirmation progress, validation state, eligible-Demand count and permitted actions in one bounded server projection;
- return each row's stable Plan Item identity, business title, ownership display, value, Planning status, Finance status, validation status and one permitted primary action;
- derive all projections from Plan, Version, item, allocation, Finance and validation records; do not persist UI status copies or dashboard counters.

Actions and behavior:

- use **Complete item** for a not-started item and **Continue item** for an in-progress or returned item; both open authorised PLN-UI-06;
- use neutral view actions for waiting/completed states and never return Finance or professional task mutations to the planner;
- open PLN-UI-04 from **Add approved Demands** with the same Plan/Draft context;
- expose **Remove from draft** only in the restrained overflow menu when the server returns the draft-only removal capability; open PLN-UI-05A and do not mutate from the menu selection itself;
- filter and search using the same scoped server projection and return only permitted Organisation Unit/status options;
- show a business-readable outstanding-work message while items are incomplete;
- return **Run validation** only when it is useful for the current state; return **Submit for review** only when §10.2 is currently satisfied, rather than exposing an unusable submission action;
- after formation, save, Finance return/confirmation or removal, recalculate the whole builder projection from authoritative records;
- when the last included item is removed from an initial Draft, render PLN-UI-03 and restore any released source eligibility through the governed removal service;
- never render Approved-baseline comparison, update reason, raw diff or unchanged operational items on PLN-UI-05.

Focused tests shall cover:

1. exact two-row FY2028/29 initial Draft after separate formation;
2. item, value and progress reconciliation with the source allocations;
3. Not started and In progress primary action labels and authorised routing to PLN-UI-06;
4. waiting-state rows without another actor's task action;
5. Add approved Demands returning to PLN-UI-04 without duplicate sources;
6. scoped filtering/search and cross-PE/OU isolation;
7. state-appropriate validation/submission actions;
8. removal-menu capability, PLN-UI-05A handoff and empty-state return after the final removal;
9. routing a post-approval Draft successor to PLN-UI-10; and
10. refresh/back producing no state mutation or duplicate work.

### D. Demo seed and scenario delta

**Permanent canonical records:** No new record is required.

Extend the isolated FY2028/29 initial-Plan fixture used by PLN-UI-03 and PLN-UI-04B:

1. Create `PLN-MOH-2028-001` and Draft `PLN-MOH-2028-001-V1` through the production registration capability.
2. Load the two exact Approved Demands specified in PLN-UI-04A/B.
3. Select **One Plan Item for each Demand** in PLN-UI-04B.
4. Assert Proposed `PPI-MOH-2028-001` at KES 48,000,000 and `PPI-MOH-2028-002` at KES 72,000,000 with the exact source OU and allocation lineage.
5. Assert the PLN-UI-05 projection: 2 items, KES 120,000,000, 0 of 2 Planning complete, 0 of 2 Finance confirmed and Not run validation.
6. Reset every fixture-owned FY2028/29 Plan, Version, Demand, Plan Item and allocation record.

The canonical FY2027/28 `PPI-MOH-2027-021` shall never be used as a Proposed PLN-UI-05 row. It remains Active in Approved Version 1. The canonical post-approval addition of `PPI-MOH-2027-022` belongs to PLN-UI-10 because its Draft Version 2 has an Approved predecessor.

### E. Acceptance evidence

`PLN-CHG-006` may be marked implemented only when:

1. PLN-UI-05 renders only a populated initial Draft with no Approved predecessor.
2. The reference rows and totals reconcile exactly to the isolated source Demands and allocations.
3. Every incomplete row provides one direct item-completion action.
4. Method and schedule detail remain in PLN-UI-06 rather than widening the builder table.
5. Submission is not exposed until the complete readiness predicate is satisfied.
6. PLN-UI-05 and PLN-UI-10 no longer duplicate initial-Plan and post-approval-update responsibilities.
7. No permanent canonical record or parallel builder record was introduced.

### F. Open decisions

None proposed. PLN-UI-05A removal confirmation is intentionally deferred to the next review slice.
