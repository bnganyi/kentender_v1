# Procurement Planning Revision Ledger

**Purpose:** Integrated Procurement Planning governing record. Each change unit keeps requirements, exact static screen design, implementation rules, deterministic seed evidence and acceptance criteria together.  
**Status:** Active integrated specification and review ledger  
**Started:** 14 August 2026  

## Documentation authority

1. `KENTENDER-MVP-CMOM-1.1` controls the cross-module operating model.
2. Approved records in this ledger control Procurement Planning requirements, static design, implementation, seed and acceptance together.
3. Under-review records are proposals and are not implementation authority.
4. Where an approved later record supersedes an earlier ledger record, the later record controls.

The former standalone Requirements, Stitch, Cursor Implementation Pack and Demo Data Contract documents are retired from the Procurement Planning authority chain. They shall not be revised, reissued or treated as future consolidation targets. They may be retained only as historical source evidence. The final Procurement Planning issue shall preserve this integrated documentation structure rather than split the product contract back into separate layers.

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
| `PLN-CHG-007` | Whole Plan Item removal confirmation and lifecycle effects | Yes | Yes | Yes | Existing scenario plus isolated variants | Approved |
| `PLN-CHG-008` | Focused Plan Item editor and admitted annual-plan fields | Yes | Yes | Yes | Existing addition scenario clarified | Approved |
| `PLN-CHG-009` | Finance funding confirmation with sufficient current allocation | Yes | Yes | Yes | Existing addition scenario and arithmetic corrected | Approved |
| `PLN-CHG-010` | Finance funding shortfall and governed resolution path | Yes | Yes | Yes | Existing isolated shortfall scenario corrected | Approved |
| `PLN-CHG-011` | Head-of-Procurement review of a Finance-confirmed Plan update | Yes | Yes | Yes | Existing post-approval addition scenario completed | Approved |
| `PLN-CHG-012` | Current Approved Plan detail and Tender implementation handoff | Yes | Yes | Yes | Post-approval execution boundary | Approved |
| `PLN-CHG-013` | Draft successor overview and submission readiness | Yes | Yes | Yes | Replaced by consolidation into the ordinary Plan builder | Superseded |
| `PLN-CHG-014` | Consolidate Draft successors into PLN-UI-05 and retire PLN-UI-10 | Yes | Yes | Yes | Existing addition journey; no new records | Approved |
| `PLN-CHG-015` | Procurement Planning workspace deferred state variants PLN-UI-01A–F | Yes | Yes | Yes | Existing scenarios plus resettable boundaries | Approved |
| `PLN-CHG-016` | Financial-year context, Demand eligibility and lifecycle-state closure | Yes | Yes | Yes | Existing FY2027/28 and resettable FY2028/29 boundaries | Approved |
| `PLN-CHG-017` | Remaining reachable PLN-UI-05 Plan-builder states | Yes | Yes | Yes | Existing canonical journey plus resettable variant branches | Approved |
| `PLN-CHG-018` | MVP-1 release boundary, mandatory hardening and MVP-2 deferrals | Yes | Exact deltas and explicit no-new-frame decisions | Yes | Release smoke contract over canonical and isolated scenarios | Approved |

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

---

## PLN-CHG-007 — Whole Plan Item removal confirmation and lifecycle effects

**Status:** Approved  
**Approved:** 15 August 2026  
**Source:** Requirements §9.8; Stitch PLN-UI-05A; Implementation Prompt 06; demo scenario `SCN-PLN-REMOVE-001`  
**Problem:** The baseline establishes whole-item, non-destructive removal, but its Stitch prompt mixes four materially different static states with mutation, routing and post-success behaviour. It also leaves several workflow boundaries implicit: when an Active-item removal may create a Draft successor, whether opening the dialog itself mutates the Plan, whether Finance must approve a release, and whether the removal reason duplicates the Plan-update reason.

### Locked design boundary

1. Removal means excluding one whole Plan Item from the editable or next approved Plan Version. It never deletes the Plan Item, changes the Approved Demand or cancels a Tender.
2. Opening PLN-UI-05A performs no mutation. The confirmed command is the only mutation.
3. A draft-only Proposed item is removed immediately from the editable Draft and its Draft effects are reversed.
4. An eligible Active item remains operational until the Draft successor is approved. The successor is created or reused only when the planner confirms removal.
5. An item with a Tender handoff, commitment or downstream execution cannot be removed through Planning.
6. A combined Plan Item is removed only as a whole. Source-level detachment is outside MVP.
7. Removal does not introduce another Finance approval or another Plan approval stage. A removal-only successor uses the removal reason as its update reason so the planner is not asked for the same rationale twice.

### A. Requirements delta

**Replace `PLN-FR-066` through `PLN-FR-069A` in §9.8 with:**

| ID | Requirement |
|---|---|
| `PLN-FR-066` | A Procurement Planner with mutation authority for the Plan PE/FY may initiate whole-item removal only while the logical Plan is Open and the relevant Draft is editable. For a draft-only Proposed item, the item must belong only to the editable Draft. For an Active item, no Tender handoff, commitment or downstream execution may exist. |
| `PLN-FR-067` | PLN-UI-05A shall show the Plan Item identity, business title, ownership, planned value, every source Demand, included Need Item count, current Finance state and the exact lifecycle effect read-only. It shall require one non-empty business reason and shall never offer source-level removal, funding edits or hard deletion. |
| `PLN-FR-068` | Opening or cancelling PLN-UI-05A shall not create a Draft successor, change eligibility, cancel Finance work or mutate the Plan. Exactly one confirmed removal command shall perform the applicable state transition. |
| `PLN-FR-069` | Confirmed removal of a draft-only Proposed item shall atomically exclude it from the editable Draft, retain the Plan Item/version/allocation and audit history, cancel any open Finance task, reverse any Draft-stage Finance confirmation through the governed Finance service, release its reservation once and release every Draft allocation hold so its source Demand Need Items become Planning-eligible again. The current Approved Version, when one exists, shall remain unchanged. |
| `PLN-FR-069A` | Confirmed removal of an eligible Active item shall create or reuse one editable Draft successor and record a Proposed removal. The current Approved item, source allocation and reservation shall remain operational until successor approval. Opening the dialog shall not create the successor. |
| `PLN-FR-069B` | A removal-only Draft successor shall not create a Finance-confirmation task. Its removal reason shall serve as the Plan-update reason. If an editable successor already contains other changes, the removal reason shall remain the item-level rationale and the existing Plan-update reason shall not be overwritten. |
| `PLN-FR-069C` | Approval of a successor containing a Proposed removal shall recheck authority, current item identity and the absence of Tender handoff, commitment or downstream execution. It shall then mark the item Removed in the successor, release only its unconsumed reservation once and restore its source allocations to Planning eligibility atomically. If downstream execution now exists, approval shall be blocked with a business-readable issue and no removal or release shall occur. |
| `PLN-FR-069D` | A Plan Item with Tender handoff, commitment or downstream execution shall expose no removal action. Direct route and mutation attempts shall be rejected server-side. An In-review successor shall not be modified; the action shall remain unavailable until the successor is returned to an editable state or completed. |
| `PLN-FR-069E` | A combined Plan Item shall be removable only as a whole in MVP. Confirmation shall identify every source Demand and the total Need Item count. No individual Demand or Need Item checkbox shall be provided. |
| `PLN-FR-069F` | Removal shall be idempotent and concurrency-safe. A retry shall not duplicate Finance reversal, reservation release, eligibility restoration, successor creation or audit evidence. After removal, counts, totals, Finance progress and validation shall be recalculated from authoritative records. |

**Consequential requirements clarifications:**

- When the final item is removed from an initial Draft Version 1, the logical Plan remains Open and PLN-UI-03 is rendered with zero items.
- When removal eliminates the only effective change in a Draft successor, the successor shall be non-submittable and PLN-UI-10 shall show **No changes remain** with **Cancel update**.
- `PLN-FR-064` shall state that a removal-only successor uses the required removal reason as its concise update reason; no duplicate reason field is permitted.

### B. Stitch delta

Replace the baseline PLN-UI-05A prompt with the following separate static design prompts. Each prompt defines one exact frame. Stitch shall not simulate confirmation, saving, routing, permissions, validation, loading, success, failure or concurrent change.

#### PLN-UI-05A-1 — draft-only item before Finance confirmation

Design one compact modal dialog over the dimmed **Ministry of Health Annual Procurement Plan 2027/28 — Draft Version 2** update screen. Preserve the existing Procurement navigation, top bar and branding visible behind the overlay.

Use only this exact state:

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Logical Plan: **PLN-MOH-2027-001**
- Current Approved Version: **Version 1**
- Open update: **Draft Version 2**
- Plan Item reference: **PPI-MOH-2027-022**
- Plan Item title: **Digital health technical staff certification programme**
- Organisation Unit: **Human Resources Management and Development**
- Planned value: **KES 80,000,000**
- Source Demand: **DMD-MOH-2027-019**
- Included Need Items: **1**
- Finance status: **Not requested**
- Reservation: **None**

Dialog content, in this order:

- Title: **Remove Plan Item from draft?**
- Introductory copy: **This removes the item from Draft Version 2. Its Approved Demand will be available for planning again.**
- One read-only item summary containing the Plan Item reference, title, Organisation Unit, planned value, source Demand and **1 Need Item**.
- Read-only Finance effect: **No Finance confirmation or reservation will be reversed.**
- Required multiline field label: **Reason for removal**
- Placeholder: **Briefly explain why this item should be removed from the draft.**
- Secondary button: **Keep item**
- Restrained destructive confirmation button: **Remove from draft**

Do not show source checkboxes, editable funding, version controls, another update-reason field, technical status codes or post-confirmation messages.

#### PLN-UI-05A-2 — Finance-confirmed draft-only item

Use the exact PLN-UI-05A-1 modal, item, source and surrounding Draft Version 2 context with these replacements:

- Finance status: **Confirmed**
- Confirmed amount: **KES 80,000,000**
- Reservation reference: **RSV-MOH-0002**
- Introductory copy: **This removes the item from Draft Version 2 and makes its Approved Demand available for planning again.**
- Read-only Finance effect: **Finance confirmation will be reversed and reservation RSV-MOH-0002 for KES 80,000,000 will be released.**

Keep the same field and buttons: **Reason for removal**, **Keep item**, **Remove from draft**.

#### PLN-UI-05A-3 — eligible Active item

Design one compact modal dialog over the dimmed **Ministry of Health Annual Procurement Plan 2028/29 — Approved Version 1** screen. Preserve the existing Procurement navigation, top bar and branding visible behind the overlay.

Use only this isolated reference state:

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Logical Plan: **PLN-MOH-2028-001**
- Current Approved Version: **Version 1**
- Open Draft update: **None**
- Plan Item reference: **PPI-MOH-2028-002**
- Plan Item title: **Clinical deployment laptops for digital health rollout**
- Organisation Unit: **Directorate of Digital Health and Policy**
- Planned value: **KES 72,000,000**
- Source Demand: **DMD-MOH-2028-002**
- Included Need Items: **2**
- Finance status: **Confirmed**
- Unconsumed reservation: **KES 72,000,000**
- Tender handoff: **None**
- Downstream execution: **None**

Dialog content, in this order:

- Title: **Remove Plan Item from approved plan?**
- Introductory copy: **The item remains active until the plan update is approved.**
- One read-only item summary containing the Plan Item reference, title, Organisation Unit, planned value, source Demand and **2 Need Items**.
- Read-only approval effect: **If the update is approved, the item will be removed, KES 72,000,000 will be released and the source Demand will be available for planning again.**
- Required multiline field label: **Reason for removal**
- Placeholder: **Briefly explain why this item should be removed from the approved plan.**
- Secondary button: **Keep item**
- Restrained destructive confirmation button: **Add removal to plan update**

Do not show a manual revision control, Finance approval action, source checkboxes, Tender cancellation, another update-reason field or immediate-removal wording.

#### PLN-UI-05A-4 — combined draft-only Plan Item

Design one compact modal over the dimmed **Ministry of Health Annual Procurement Plan 2028/29 — Draft Version 1** builder.

Use only this isolated reference state:

- Plan Item reference: **PPI-MOH-2028-003**
- Plan Item title: **Clinical training and deployment laptops for digital health rollout**
- Ownership: **Ministry of Health**
- Planned value: **KES 120,000,000**
- Finance status: **Not requested**
- Source 1: **DMD-MOH-2028-001 — Clinical training laptops for digital health rollout — Human Resources Management and Development — 2 Need Items — KES 48,000,000**
- Source 2: **DMD-MOH-2028-002 — Clinical deployment laptops for digital health rollout — Directorate of Digital Health and Policy — 2 Need Items — KES 72,000,000**

Dialog content, in this order:

- Title: **Remove Plan Item from draft?**
- Introductory copy: **This removes the complete combined Plan Item from Draft Version 1.**
- One read-only item summary containing the Plan Item reference, title, ownership and total planned value.
- Section heading: **Included Demand sources**
- Show both exact source rows above.
- Read-only effect: **The whole Plan Item and all 4 source allocations will be removed together. Both Approved Demands will be available for planning again.**
- Required multiline field label: **Reason for removal**
- Placeholder: **Briefly explain why this item should be removed from the draft.**
- Secondary button: **Keep item**
- Restrained destructive confirmation button: **Remove from draft**

Do not show Demand or Need Item checkboxes and do not offer partial removal.

### C. Implementation delta

Implement PLN-UI-05A as one capability-backed confirmation surface with server-derived lifecycle mode and effects.

**Projection and entry:**

- expose a removal action only when the server returns an item-specific removal capability for the authenticated user, PE/FY scope, Plan lifecycle, editable state and downstream condition;
- use **Remove from draft** for a draft-only item and **Remove from plan** for an eligible Active item;
- omit the action for Closed Plans, In-review Drafts, unauthorised users and items with Tender handoff, commitment or downstream execution;
- opening the modal shall read a fresh confirmation projection and shall not create/reuse a Draft successor or mutate any record;
- return authoritative item identity, title, ownership, value, every source Demand and Need Item count, Finance state, reservation effect, removal mode and exact effect copy;
- do not rely on row-state fields supplied by the browser as authority.

**Command:**

- accept logical Plan identifier, Plan Item identifier, editable Draft Version identifier when the item is draft-only, expected concurrency token, trimmed non-empty reason and idempotency key;
- do not require or accept a client-created Draft successor for an Active item;
- derive current item state, Draft-successor use, release amount, Finance reversal, source eligibility, downstream condition and resulting totals server-side;
- reject client-supplied release amounts, source identifiers, eligibility flags, item state, downstream flags or update-reason overrides.

**Draft-only transaction:**

- lock the Plan, Draft Version, item/version, allocations, Finance task/decision and reservation records needed by the command;
- exclude/mark the Proposed item Removed without hard deletion;
- retain source allocations as audit lineage while releasing their Draft holds;
- cancel an open Finance task or reverse a completed Draft-stage Finance confirmation through its governed service;
- release the associated reservation once;
- restore the source Need Items to Planning eligibility;
- recalculate the Draft projection and return PLN-UI-03 when an initial Draft becomes empty, or PLN-UI-10 with `no_changes_remain = true` when a successor has no effective changes.

**Active-item transaction and approval:**

- on confirmed removal, lock and re-evaluate the current Approved item, then create or reuse one editable Draft successor and record one Proposed removal with the supplied reason;
- when the removal is the only change, use that same reason as the successor update reason and do not prompt again;
- do not create a Finance task for a removal-only change and do not release the current reservation before approval;
- keep the current Approved item, source ineligibility, reservation and permitted operations unchanged while the successor is Draft, Returned or In review;
- on successor approval, recheck the absence of Tender handoff, commitment and downstream execution under lock, then apply removal, release the full unconsumed reservation and restore source eligibility once;
- if downstream execution appeared after proposal, block approval with a stable business issue and perform no partial release or eligibility change.

**Response and resilience:**

- return the correct builder destination, business-readable confirmation, recalculated item count/value/Finance/validation state and `no_changes_remain` when applicable;
- use optimistic concurrency and idempotency across removal, Finance reversal, reservation release, source restoration, successor creation and audit evidence;
- preserve all Plan Item, Version, allocation, Finance and audit records;
- make Cancel, browser Back and refresh mutation-free.

**Focused tests:**

1. canonical draft-only removal before Finance confirmation;
2. Finance-confirmed draft-only reversal and one-time reservation release;
3. eligible Active-item proposal creating one Draft successor only on confirmation;
4. removal-only successor using one reason and creating no Finance task;
5. existing editable successor reuse without overwriting its overall update reason;
6. In-review successor action omission and server rejection;
7. Tender, commitment and downstream action omission plus direct-route/API rejection;
8. downstream creation between proposal and approval blocking approval without partial effects;
9. combined whole-item removal and rejection of source-level input;
10. last-item initial Draft returning PLN-UI-03;
11. last effective successor change returning **No changes remain** and blocking submission;
12. double submission, idempotent retry, stale token and competing-update tests;
13. cross-PE/OU and unauthorised-role negative tests; and
14. accessible focus, labels, error association and focus return to the invoking row.

### D. Demo seed and scenario delta

**Permanent canonical records:** No new record is required.

Retain `SCN-PLN-REMOVE-001` as the canonical PLN-UI-05A-1 state:

- start from Proposed `PPI-MOH-2027-022` in Draft Version 2 before Finance confirmation;
- use reason **Added for demonstration; remove from this draft**;
- restore Draft total from KES 535,000,000 to KES 455,000,000;
- restore `DMD-MOH-2027-019` to Planning eligibility;
- preserve Approved Version 1, Active `PPI-MOH-2027-021` and `TND-MOH-2027-008` unchanged; and
- leave the successor with **No changes remain** and **Cancel update**.

Use resettable isolated UI/transaction branches for:

1. **PLN-UI-05A-2:** advance `PPI-MOH-2027-022` through Finance confirmation, create `RSV-MOH-0002` once, then prove reversal/release without changing the successful canonical base.
2. **PLN-UI-05A-3:** advance isolated FY2028/29 `PPI-MOH-2028-002` to Active in Approved Version 1 with a fully unconsumed KES 72,000,000 reservation and no Tender, commitment or downstream execution.
3. **PLN-UI-05A-4:** form isolated combined `PPI-MOH-2028-003` from `DMD-MOH-2028-001` and `DMD-MOH-2028-002`, retaining 4 Need Item allocations and KES 120,000,000 total value.

The canonical Active `PPI-MOH-2027-021` shall remain the protected negative fixture because `TND-MOH-2027-008` exists. It shall never expose or accept removal.

Every isolated branch shall own and reset only its records, rerun without duplicates and leave the canonical FY2027/28 successful story unchanged.

### E. Acceptance evidence

`PLN-CHG-007` may be marked implemented only when:

1. Opening or cancelling PLN-UI-05A creates no state change or Draft successor.
2. The four static variants render only their exact authoritative data and effect copy.
3. Draft-only removal reverses Draft effects once without hard deletion.
4. Active removal remains proposed until Plan-update approval and does not create another Finance task.
5. A removal-only update asks for one reason, not two.
6. Executed items are protected by both action omission and server rejection.
7. Combined items can be removed only as a whole.
8. Empty/no-change destinations and totals reconcile exactly.
9. Canonical and isolated scenarios reset without duplicates or cross-fixture mutation.

### F. Open decisions

None proposed.

---

## PLN-CHG-008 — Focused Plan Item editor and admitted annual-plan fields

**Status:** Approved  
**Approved:** 15 August 2026  
**Source:** Requirements §§9.4–9.5; Stitch PLN-UI-06; Implementation Prompt 04; demo scenario `SCN-PLN-ADD-001`  
**Problem:** The baseline uses Active `PPI-MOH-2027-021` as though it were an editable Proposed item in Draft Version 1, even though the canonical record is already in Approved Version 1 and has a Tender. The field register also exposes a generic governing-regime field, omits the notification-of-award milestone required by the annual-plan format, and does not clearly define editor locking, Finance-request atomicity or the upstream-value boundary.

### Evidence and field-admission rule

[Regulation 41 and the Third Schedule of the Public Procurement and Asset Disposal Regulations, 2020](https://new.kenyalaw.org/akn/ke/act/ln/2020/69/eng%402020-04-30) require the consolidated annual Plan to cover the requirement, delivery/implementation/completion schedule, single- or multi-year treatment, aggregation, lotting, estimated package value and funding source, and procurement method. The Third Schedule provides the operational annual-plan columns for item description, unit, quantity, method, source of funds, estimated cost and procurement milestones.

Every PLN-UI-06 field must therefore satisfy at least one of these tests:

1. it is required annual-plan content;
2. it is approved source evidence needed to understand that content;
3. it drives a governed validation, Finance decision or Tender handoff; or
4. it records a necessary exception to a governed recommendation.

Fields that merely restate technical configuration, anticipate Tender configuration or collect generic rationale are not admitted.

### Locked design boundary

1. PLN-UI-06 edits one existing Proposed Plan Item already formed by PLN-UI-04. It never selects, adds, removes, combines, separates or reallocates source Demands or Need Items.
2. Approved business scope, unit, quantity, required-by date, owner, proposed funding and approved value remain read-only source evidence.
3. The planner completes only the procurement-facing description, governed category, planned method, annual/multi-year treatment, indicative lotting and statutory annual-plan schedule.
4. The source-approved value is the Plan Item estimated cost for MVP and shall already include applicable incidental procurement costs. PLN-UI-06 does not invent an editable value uplift. A missing or materially incorrect approved value is corrected through the Demand amendment/reapproval path, not by silently changing it in Planning.
5. The editor does not show a generic **Governing regime** field. Applicable rules may drive the method recommendation server-side and appear only as a concise recommendation basis.
6. **Request Finance confirmation** is one atomic save-and-submit action after Planning completeness. It does not perform the Finance decision.
7. Stitch receives one exact canonical static frame. Conditional multi-year, lotting, method-exception, combined-source and Finance-return frames will be specified separately during the approved post-journey variant pass; Stitch shall not infer them from this prompt.

### A. Requirements delta

**Replace §9.4 and §9.5 in full with:**

#### 9.4 Plan Item editor and field register

| ID | Requirement |
|---|---|
| `PLN-FR-030` | PLN-UI-06 shall open one existing Proposed Plan Item created by PLN-UI-04. The page shall receive the Plan Item identity and shall never create a blank item, select another Demand or repeat formation. |
| `PLN-FR-031` | The editor shall show every Approved source Demand and included Need Item read-only, including source reference/title, owner OU, item description, unit, quantity, required-by date, approved value, proposed Budget Line and inherited Strategy lineage where present. A combined Plan Item shall show every source and the recorded formation reason without editable source controls. |
| `PLN-FR-032` | The editable field set shall be limited to the admitted field register below. Owner, source scope, unit, quantity, required-by date, approved value, source funding and Strategy lineage shall not be accepted in the mutation payload. |
| `PLN-FR-033` | The system shall derive a recommended procurement method and concise basis from the governed method catalogue, category, value, funding and applicable rules. The planner shall select the planned procurement method from the permitted governed set. When it differs from the recommendation, the applicable configured ground and a concise justification shall be required. No free-form method code or unsupported ground is permitted. |
| `PLN-FR-034` | The planner shall identify the item as **Single year** or **Multi-year**. Multi-year treatment shall require a concise justification and a completion date consistent with the governed multi-year planning period. The screen shall not create another Plan or Version for each contract year. |
| `PLN-FR-035` | The planner shall indicate **No lots expected** or **Lots expected**. When lots are expected, an estimated lot count greater than one and a concise lotting basis shall be required. This remains indicative annual-plan content; detailed Tender lots are not created in PLN-UI-06. |
| `PLN-FR-036` | The planned schedule shall contain Invitation/advertisement, Bid opening, Evaluation completion, Tender award, Notification of award, Contract signing and Contract completion dates. The system shall derive total planned days to contract signature and shall validate chronological order, Plan-period compatibility, the source required-by date and multi-year treatment. |
| `PLN-FR-037` | The Plan Item planned value shall equal the sum of its source-approved allocations and shall be read-only in PLN-UI-06. The source-approved estimate shall include applicable insurance, clearing and forwarding, demurrage, warehousing, advertisement and other incidental procurement costs. If the planner identifies a missing or materially incorrect source value, the item shall not be sent to Finance; the source Demand shall be amended and reapproved through its governed route. |
| `PLN-FR-038` | **Save draft** shall persist only the editable Draft Plan Item Version, retain source allocations unchanged and recalculate Planning completeness without creating a Finance task. |
| `PLN-FR-039` | **Request Finance confirmation** shall atomically save the submitted editable fields, validate current source approval and allocation, enforce the complete field and schedule rules, mark Planning complete and create or reuse exactly one actionable Finance task. Validation failure shall create no Finance task and shall return business-readable field issues. |
| `PLN-FR-039A` | A newly formed or Finance-returned item in an editable Draft shall be editable by an authorised Procurement Planner. While a Finance task is awaiting action, PLN-UI-06 shall be a neutral read-only item detail for the planner. It shall not expose the Budget Officer's task form or disabled Finance actions. |
| `PLN-FR-039B` | Finance confirmation shall not make the Approved Demand editable. If a later governed Plan return reopens procurement fields, any change that affects planned value or funding lineage shall make Finance confirmation Stale and require confirmation again; other changes shall follow the configured Finance-freshness rule. |
| `PLN-FR-039C` | Save and Finance-request commands shall be PE/FY-scoped, capability-checked, optimistic-concurrency protected and idempotent. Back, refresh, opening source detail and leaving the editor shall not mutate the item or create a task. |

**Admitted field register:**

| Field | Presentation and owner | Source or condition | Operational effect |
|---|---|---|---|
| Approved source breakdown | Read-only | Plan Demand Allocations and Approved Demand snapshots | Preserves approved scope, unit, quantity, value, timing, OU and funding lineage |
| Procurement-facing item description | Required multiline; Planner | Always | Supplies the comprehensive annual-plan item description without becoming a Tender specification |
| Procurement category | Required governed searchable select; Planner | Always | Classifies goods, works or services and drives method/STD recommendation and reporting |
| Source-approved planned value | Read-only derived total | Always | Supplies estimated package cost and amount passed to Finance |
| Recommended method and basis | Read-only derived | Always | Explains the governed default method |
| Planned procurement method | Required governed select; Planner | Always | Records annual-plan procurement method |
| Alternative-method ground and justification | Required governed ground plus multiline justification; Planner | Only when planned method differs from recommendation | Records the reviewed exception without inventing a method |
| Contract period | Required **Single year** or **Multi-year**; Planner | Always | Records annual or multi-year treatment |
| Multi-year justification | Required multiline; Planner | Multi-year only | Explains why performance crosses the annual period |
| Indicative lotting | Required **No lots expected** or **Lots expected**; Planner | Always | Records whether the eventual procurement is expected to use lots |
| Estimated lot count and lotting basis | Required integer and multiline basis; Planner | Lots expected only | Supports annual-plan lotting and anti-splitting review without creating Tender lots |
| Planned milestone dates | Required dates; Planner | Always | Supplies the annual-plan procurement and completion schedule |
| Planned days to contract signature | Read-only derived | Always | Reconciles the schedule to the Third Schedule timing measure |

**Explicit exclusions:**

- generic governing-regime field;
- aggregation or separation decision;
- source selection, removal, regrouping or value allocation;
- editable owner OU, business scope, unit, quantity, required-by date, source value, Budget Line or Strategy target;
- Departmental Contribution, Departmental Submission or routine HoD planning sign-off;
- generic statutory/Strategy treatment, preference/reservation scheme or planned reserved-value inputs;
- Plan-level coverage placeholders;
- Tender specifications, detailed lot construction, STD selection/configuration or approval-route settings;
- attachments without a requirement-specific evidence purpose; and
- technical version-management controls.

**Consequential cross-module requirement:** The Demands confirmed-estimate contract shall state that the approved estimate includes every applicable incidental procurement cost required for the estimated package cost. If this is not already enforced upstream, it shall be corrected in the Demands requirement and seed contract during final consolidation; Planning shall not compensate through an unapproved value field.

#### 9.5 Planning-completeness and editor state

| ID | Requirement |
|---|---|
| `PLN-FR-039D` | Planning completeness requires approved source integrity, a procurement-facing description, governed category, permitted planned method, any required method exception, contract period, any required multi-year justification, lotting decision, any required lot details and a valid complete milestone schedule. |
| `PLN-FR-039E` | The page shall distinguish **Not started**, **In progress**, **Planning complete**, **Awaiting Finance confirmation**, **Returned by Finance** and **Finance confirmed** without collapsing Planning and Finance into one status. |
| `PLN-FR-039F` | A Finance return shall show the returning actor, time and reason as read-only task context and shall reopen only the planner-owned fields. Re-requesting Finance shall create one new actionable task iteration linked to the prior return without duplicating the Plan Item or prior decision evidence. |
| `PLN-FR-039G` | A combined item shall use the same editor and field register. Its description, category, method, period, lotting and schedule apply to the whole item; every source allocation remains independently traceable and immutable. |

### B. Stitch delta

Replace the baseline PLN-UI-06 prompt with this one exact static reference frame. The prompt contains presentation data only. It does not instruct Stitch to save, validate, create tasks, conditionally reveal controls, enforce permissions or simulate state transitions.

#### PLN-UI-06 — completed Proposed Plan Item before Finance request

Design the main content area for **PLN-UI-06 Plan Item editor**. Preserve the existing Procurement navigation, top bar and branding. Use a single focused page with a comfortable form width; do not use tabs, a stepper or a multi-step wizard.

Use only this exact reference state:

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Procuring Entity: **Ministry of Health**
- Financial year: **2027/28**
- Logical Plan: **PLN-MOH-2027-001**
- Current Approved Version: **Version 1**
- Open update: **Draft Version 2**
- Draft context: **Added Plan Item**
- Plan Item reference: **PPI-MOH-2027-022**
- Plan Item title: **Digital health technical staff certification programme**
- Plan Item lifecycle: **Proposed**
- Planning status: **Planning complete**
- Finance status: **Not requested**
- Planned value: **KES 80,000,000**

Header, in this order:

- Breadcrumb: **Procurement Planning / Ministry of Health Annual Procurement Plan 2027/28 / PPI-MOH-2027-022**
- Title: **Digital health technical staff certification programme**
- Quiet reference: **PPI-MOH-2027-022**
- Context line: **Draft Version 2 · Added Plan Item · Current Approved Version 1 remains active**
- Status chips: **Proposed** and **Planning complete**
- Value: **KES 80,000,000**

Show one compact read-only section titled **Approved requirement** with:

- Demand: **DMD-MOH-2027-019 — Digital health technical staff certification programme**
- Owner Organisation Unit: **Human Resources Management and Development**
- Need Item: **Accredited digital-health technical staff certification programme**
- Quantity and unit: **1 Programme**
- Required by: **31 December 2027**
- Approved value: **KES 80,000,000**
- Proposed Budget Line: **MOH-BL-HWD-2027 — Digital Health Workforce Capacity Development**
- Strategy alignment: **MOH-TGT-SKILLS-2029 — Train and certify 150 digital-health technical staff by 30 June 2029**
- Finance confirmation: **Not requested**
- Text link: **View Approved Demand**

Below the source section, show this quiet note:

**The Approved Demand controls the business scope, quantity, required-by date, owner and planned value. Amend and reapprove the Demand if any of these must change.**

Section heading: **Procurement approach**

- Required multiline field: **Plan Item description**
- Field value: **Procure one accredited digital-health certification programme, including training and examinations, for the FY 2027/28 workforce-development requirement.**
- Required searchable select: **Procurement category**
- Selected value: **Training and professional development services**
- Read-only value: **Planned value — KES 80,000,000**

Show one compact recommendation strip:

- Label: **Recommended procurement method**
- Value: **Open tender**
- Supporting text: **Configured competitive method for this service category and planned value.**

Below the strip show:

- Required select: **Planned procurement method**
- Selected value: **Open tender**
- Required select: **Contract period**
- Selected value: **Single year**

Section heading: **Indicative lotting**

- Supporting text: **Detailed lots are defined during Tender preparation.**
- Selected radio: **No lots expected**
- Unselected radio: **Lots expected**

Section heading: **Planned schedule**

Use one compact two-column table with headings **Milestone** and **Planned date**. Show these exact populated date inputs:

| Milestone | Planned date |
|---|---|
| Invitation or advertisement | **8 November 2027** |
| Bid opening | **29 November 2027** |
| Evaluation completion | **8 December 2027** |
| Tender award | **13 December 2027** |
| Notification of award | **15 December 2027** |
| Contract signing | **20 December 2027** |
| Contract completion | **31 December 2027** |

Below the table show one read-only summary: **Planned time to contract signature — 42 days**.

Sticky footer actions, left to right:

- Text button: **Back to plan update**
- Secondary button: **Save draft**
- Primary button: **Request Finance confirmation**

Do not show aggregation, source editing, a generic governing regime, alternative-method fields, multi-year justification, lot-count fields, statutory/Strategy treatment, preference/reservation inputs, Plan-level coverage, attachments, Tender configuration, approval settings, disabled Finance actions or technical version controls in this reference frame.

### C. Implementation delta

Implement PLN-UI-06 as a capability-backed editor for one existing Draft Plan Item Version.

**Route and projection:**

- require an authorised Plan Item identity and resolve its Plan, editable Version, PE/FY scope, lifecycle and mutation capability server-side;
- return Approved source snapshots and allocations separately from editable Plan Item Version fields;
- return exact Planning and Finance statuses, method recommendation/basis, permitted method values and grounds, derived planned value, milestone validation and state-appropriate actions;
- route initial-Draft items back to PLN-UI-05 and post-approval additions back to PLN-UI-10;
- never create a Plan Item or Draft successor when PLN-UI-06 is opened.

**Mutation allow-list:**

- accept only description, governed category identifier, planned method identifier, configured alternative-method ground and justification when applicable, contract period, multi-year justification when applicable, lotting decision, estimated lot count and lotting basis when applicable, and the seven milestone dates;
- reject or ignore no unknown field silently: owner, source Demand/Need Item identifiers, unit, quantity, required-by date, source value, Budget Line, Strategy lineage, formation mode, source allocation and Plan/Version lifecycle fields shall return a stable validation error if supplied as mutation authority;
- derive method recommendation, planned value, days to contract signature, completeness and all source context server-side.

**Validation:**

- require all always-applicable fields and only the conditional fields for the selected method, period and lotting state;
- allow only methods and grounds permitted by the current governed catalogue and recommendation context;
- require lot count greater than one when lots are expected;
- enforce the seven-date chronology and source required-by date; allow completion outside the annual period only for a valid Multi-year item;
- reject a description or category change that attempts to replace the approved business requirement and return a stable instruction to amend/reapprove the Demand;
- do not permit an editable Plan Item value or source-funding change in this service.

**Commands and state:**

- **Save draft** shall use optimistic concurrency and idempotency, persist the allowed Draft fields and return recalculated completeness without creating or changing a Finance task;
- **Request Finance confirmation** shall perform one transaction that locks and reloads the Draft item and sources, saves the submitted allowed fields, validates current completeness and source approval, marks Planning complete, creates one actionable Finance task and records audit evidence;
- if task creation fails, roll back the item submission state; if the same idempotency key is repeated, return the original task and result;
- while Finance is Awaiting, return neutral read-only detail to the planner rather than disabled editable controls or the Budget Officer form;
- a Finance return shall reopen planner fields with immutable return context and shall preserve earlier decisions; one re-request creates one linked actionable task iteration;
- refresh, source-detail navigation, browser Back and leaving with no save shall create no mutation.

**Focused tests:**

1. canonical `PPI-MOH-2027-022` projection and exact source lineage;
2. mutation allow-list and rejection of owner/source/value/funding/formation fields;
3. required and conditional method, period and lotting fields;
4. complete seven-date schedule, chronology, derived 42 days and required-by validation;
5. source-value mismatch and material-scope change directing Demand amendment rather than silent Planning edits;
6. Save draft without Finance task creation;
7. atomic Request Finance confirmation and rollback on task failure;
8. duplicate click/idempotent retry producing one Finance task;
9. Awaiting Finance planner read-only state without Finance task controls;
10. Finance return, correction and one linked re-request iteration;
11. combined-item source immutability and whole-item field application;
12. initial-Draft versus Draft-successor return routing;
13. cross-PE/OU and unauthorised-role read/mutation denial; and
14. keyboard navigation, date-input labels, issue association and accessible status announcement.

### D. Demo seed and scenario delta

**Permanent canonical records:** No new Plan, Version, Demand or Plan Item is required.

Clarify the corrected and reapproved `DMD-MOH-2027-019` branch in `SCN-PLN-ADD-001` with:

| Field | Value |
|---|---|
| Need Item reference | `DNI-MOH-2027-019-01` |
| Need Item | Accredited digital-health technical staff certification programme |
| Quantity | 1 |
| Unit | Programme |
| Confirmed value | KES 80,000,000 |
| Required by | 31 December 2027 |
| Procurement category on completed Plan Item | Training and professional development services |

Complete Proposed `PPI-MOH-2027-022` through the production editor capability with the exact PLN-UI-06 description, Open tender method, Single-year period, No-lots decision and seven milestone dates above. Before the Finance request, assert **Planning complete**, **Finance Not requested**, no Finance task and no reservation.

Invoke the production Finance-request capability once and assert:

- the same `PPI-MOH-2027-022` and Draft Version 2 remain in place;
- Planning is complete and Finance is Awaiting confirmation;
- exactly one actionable Finance task exists for Peter Otieno;
- no Finance decision or reservation exists before Peter acts;
- Approved Version 1, Active `PPI-MOH-2027-021` and `TND-MOH-2027-008` remain unchanged; and
- rerunning with the same idempotency key creates no duplicate item, task or audit event.

Reset shall remove only scenario-owned editor/task state and restore the post-formation Proposed item without touching the canonical Approved baseline.

### E. Acceptance evidence

`PLN-CHG-008` may be marked implemented only when:

1. PLN-UI-06 opens canonical Proposed `PPI-MOH-2027-022`, not Active `PPI-MOH-2027-021` presented under a false Draft state.
2. Every visible field passes the field-admission rule and has a defined owner and operational effect.
3. The exact annual-plan schedule includes Notification of award and derives 42 days to contract signature.
4. Approved sources and value remain immutable and are not duplicated into editable payload fields.
5. Save draft creates no Finance task; Request Finance is atomic and creates exactly one task.
6. Awaiting Finance does not expose another actor's form or disabled decision actions.
7. No source-selection, aggregation, generic treatment, contribution, routine HoD or Tender-configuration control remains.
8. The canonical scenario is repeatable and leaves Approved Version 1 plus its Tender operational.

### F. Open decisions

No business decision is open. Exact static variants for combined-source context, multi-year treatment, lots expected, alternative method and Finance return remain scheduled for the post-journey variant pass. They shall not be inferred by Stitch or populated with ad hoc data before that pass.

---

## PLN-CHG-009 — Finance funding confirmation with sufficient current allocation

**Status:** Approved  
**Approved:** 15 August 2026  
**Source:** Requirements §9.6; Stitch PLN-UI-07; Implementation Prompt 05; demo scenario `SCN-PLN-ADD-001`  
**Scope:** PLN-UI-07 sufficient-funding state only. PLN-UI-07A shortfall is the next separate review slice.  
**Problem:** The baseline Finance screen presents Active `PPI-MOH-2027-021`, its KES 455,000,000 infrastructure Budget Line and a false Draft Version 1 context even though that item is already in Approved Version 1 and has an active Tender. It therefore does not continue the approved PLN-UI-06 journey. The requirements also omit allocation freshness, full-value confirmation, combined-source atomicity, task-iteration rules and the boundary between funding confirmation and Plan approval. The demo arithmetic prematurely treats the workforce amount as reserved before the Budget Officer acts.

### Locked decision boundary

PLN-UI-07 is one protected Finance task for the completed Proposed Plan Item. It answers one question: **is the full source-approved Plan Item value currently available on its governed funding allocation, and may that full amount now be reserved?**

It is not:

- another Demand approval;
- Plan approval;
- a Budget Line editor;
- a partial-funding or value-negotiation screen;
- a generic approval form; or
- a read-only form shown with disabled actions to unauthorised users.

### A. Requirements delta

**Replace `PLN-FR-040` through `PLN-FR-046` in §9.6 with:**

| ID | Requirement |
|---|---|
| `PLN-FR-040` | A successful **Request Finance confirmation** command for a Planning-complete Plan Item shall create or reuse exactly one actionable Finance task iteration. The task shall reference the logical Plan, editable Plan Version, Plan Item Version and every source funding allocation, and shall be assigned through the configured Finance routing policy. |
| `PLN-FR-041` | Only the assigned Budget Officer or another actor holding the explicit Finance-confirmation capability for the same PE and funding scope may list, open or decide the task. Record visibility, Administrator status or Planning authority alone shall not expose the task form. Direct route and command attempts shall be denied before protected task data is returned. |
| `PLN-FR-042` | The task projection shall show the Plan and Draft Version, Plan Item identity and lifecycle, owner OU, every source Demand and Need Item allocation, proposed Budget Line, full amount required, live Approved/Reserved/Committed/Available allocation values, the allocation **As at** time, the derived available balance after confirmation and a business-readable availability status. All funding and Planning data shall be read-only. |
| `PLN-FR-043` | The available actions shall be **Confirm funding**, **Return to planner** and a mutation-free exit. A confirmation note is optional. Return to planner requires a non-empty Finance reason and is a remediable return, not a rejection of the Demand or Plan. |
| `PLN-FR-044` | **Confirm funding** shall confirm only the full source-approved Plan Item value. In one transaction it shall lock and reload the task, Plan Item Version and funding allocations; recheck task authority, task currency, allocation ownership and live availability; create or resolve exactly one reservation for the full amount; record the Finance decision, actor, role and time; mark the task completed; and mark the Plan Item Finance state **Confirmed**. Any failed check shall create no partial reservation, decision or task completion. |
| `PLN-FR-045` | Finance confirmation shall not approve the logical Plan or Draft Version, activate the Proposed item, change the Approved Demand, edit a Budget Line, change the Plan Item value or disturb the current Approved Version and its operational handoffs. The Proposed item becomes eligible for professional Plan review only after the remaining Plan validation requirements are met. |
| `PLN-FR-046` | **Return to planner** shall record the reason and actor/time, close the current task iteration, mark the Plan Item **Returned by Finance**, create no reservation and reopen only the planner-owned fields in the editable Draft. One later valid Finance request shall create one new task iteration linked to the return and shall retain all prior task and decision evidence. |
| `PLN-FR-046A` | A funding-line, allocation, source-approved value or governed Plan Item change that affects the confirmed funding basis shall make the Finance confirmation **Stale**. Submission for professional review shall require a current confirmation; historical confirmation and reservation evidence shall remain auditable and any reversal or replacement shall use the governed Finance service. |
| `PLN-FR-046B` | For a combined Plan Item, one Finance task shall show every source allocation and confirm all source amounts atomically. If any source cannot fund its full allocation, no source shall be confirmed or reserved in isolation and the task shall use the PLN-UI-07A shortfall state. |
| `PLN-FR-046C` | Task creation, confirmation, return, reservation creation and re-request shall be idempotent and concurrency-safe. Repeated commands shall return the original result without duplicate tasks, task iterations, decisions, reservations or audit events. A concurrency change that removes sufficient funding shall produce the governed insufficient-funding outcome without partial mutation. |

`PLN-FR-047` through `PLN-FR-049` remain under the separate PLN-UI-07A review and are not changed by this record.

### B. Stitch delta

Replace the baseline PLN-UI-07 prompt with the following one exact static reference frame. It contains only composition, visible data, controls and user-facing copy. It does not instruct Stitch to perform confirmation, return, routing, validation, reservation, permission checks or state changes.

#### PLN-UI-07 — sufficient funding available

Design a focused right-side drawer over the dimmed **Finance work queue**. Preserve the existing Procurement navigation, top bar and branding visible behind the drawer.

Use only this exact reference state:

- Signed-in user: **Peter Otieno**
- Role: **Budget Officer**
- Procuring Entity: **Ministry of Health**
- Financial year: **2027/28**
- Logical Plan: **PLN-MOH-2027-001**
- Current Approved Version: **Version 1**
- Open update: **Draft Version 2**
- Plan Item: **PPI-MOH-2027-022 — Digital health technical staff certification programme**
- Plan Item lifecycle: **Proposed**
- Planning status: **Planning complete**
- Finance status: **Awaiting confirmation**
- Availability status: **Sufficient funding**

Drawer header:

- Title: **Confirm Plan Item funding**
- Quiet reference: **PPI-MOH-2027-022**
- Context line: **Ministry of Health Annual Procurement Plan 2027/28 · Draft Version 2**
- Status chips: **Awaiting confirmation** and **Sufficient funding**
- Close icon labelled **Close**

Section heading: **Plan Item**

- Title: **Digital health technical staff certification programme**
- Owner Organisation Unit: **Human Resources Management and Development**
- Source Demand: **DMD-MOH-2027-019 — Digital health technical staff certification programme**
- Need Item: **Accredited digital-health technical staff certification programme**
- Quantity and unit: **1 Programme**
- Required by: **31 December 2027**
- Amount requiring confirmation: **KES 80,000,000**
- Text link: **View Plan Item**

Section heading: **Funding position**

- Budget Line: **MOH-BL-HWD-2027 — Digital Health Workforce Capacity Development**
- Approved allocation: **KES 80,000,000**
- Reserved: **KES 0**
- Committed: **KES 0**
- Available now: **KES 80,000,000**
- Amount to reserve: **KES 80,000,000**
- Available after confirmation: **KES 0**
- As at: **20 August 2027, 10:00 EAT**
- Text link: **View Budget Line**

Show one compact informational notice with this exact copy:

**Confirming funding will reserve KES 80,000,000 on MOH-BL-HWD-2027 for this Plan Item. It does not approve Draft Version 2.**

Show one empty multiline field:

- Label: **Finance note**
- Helper text: **Optional when confirming. Required when returning to the planner.**

Drawer footer buttons, left to right:

- Text button: **Cancel**
- Secondary button: **Return to planner**
- Primary button: **Confirm funding**

Do not show editable funding values, a Budget Line selector, partial amount, override, Approve, Reject, Demand decision, Plan approval, Plan Item editor, reservation reference, post-confirmation message, disabled unauthorised state or generic approval matrix in this frame.

### C. Implementation delta

Implement PLN-UI-07 as a protected projection and two explicit commands over one current Finance task iteration.

**Task route and projection:**

- resolve the task by stable task identity and derive Plan, Version, Plan Item, source allocations and Finance routing server-side;
- require task-view capability, current assignment/configured delegation, matching PE and funding scope before returning protected task data;
- do not infer Finance capability from Administrator, Requester, Planner, HoD, Viewer or ordinary record-view roles;
- return the exact Plan/Version/item identity and statuses, immutable source snapshots, live funding arithmetic, authoritative `as_at`, post-confirmation balances and only the commands currently permitted;
- calculate all totals and availability server-side from the governed Budget and reservation records; do not accept client-provided balances, reservation values, source identifiers or status flags;
- keep permitted neutral Plan/Plan Item detail separate from the protected Finance task projection.

**Confirm-funding command:**

- accept task identity, expected concurrency token, optional trimmed note and idempotency key only;
- in one transaction, lock and reload the task, current Plan Item Version, source allocations, affected Budget Lines and reservations;
- reject a completed, returned, superseded, stale, unassigned or unauthorised task with a stable outcome;
- revalidate Planning completeness, Approved source integrity, Plan Item/source arithmetic, current proposed funding lineage and the full available amount;
- create or resolve one reservation per governed source allocation while treating the whole Plan Item confirmation as one atomic decision;
- create one Finance decision and audit event, complete the task and set the Plan Item Finance state to **Confirmed** only after every reservation succeeds;
- return the same successful result on retry; never reserve twice or decrement availability twice;
- if live availability is now insufficient, roll back all attempted changes and return the PLN-UI-07A projection and stable insufficient-funding code.

**Return-to-planner command:**

- accept task identity, expected concurrency token, required trimmed reason and idempotency key;
- atomically record one return decision, complete the task iteration and mark the item **Returned by Finance**;
- create no reservation and change no Budget allocation;
- retain the Plan Item, sources, Draft Version and prior evidence, and expose the planner-owned editor state defined by PLN-CHG-008;
- link one later Finance task iteration to this return when the planner validly requests confirmation again.

**State and downstream boundary:**

- after successful confirmation, keep Draft Version 2 Draft and `PPI-MOH-2027-022` Proposed; do not invoke professional approval or activate the item;
- keep current Approved Version 1, Active `PPI-MOH-2027-021`, `RSV-MOH-0001` and `TND-MOH-2027-008` unchanged;
- make a confirmation Stale through the governed Finance-freshness service when its material basis changes;
- prevent Plan submission while any applicable included item lacks a current full confirmation;
- expose no inline Budget mutation or partial-confirmation path.

**Focused tests:**

1. exact canonical PLN-UI-07 projection for `PPI-MOH-2027-022` and `MOH-BL-HWD-2027`;
2. assigned Budget Officer access and denial before data return for Requester, Planner, HoD, Viewer, unassigned Budget Officer and Administrator-without-task;
3. read-only source and allocation projection with authoritative `as_at` and exact pre/post arithmetic;
4. full KES 80,000,000 atomic reservation and one decision/task completion;
5. no Plan approval, item activation, Demand mutation or change to the Approved Version 1 handoff;
6. optional confirmation note and mandatory return reason;
7. Return to planner with no reservation and one linked re-request task iteration;
8. duplicate click, idempotent retry and replay after completion;
9. concurrent funding consumption changing the task to PLN-UI-07A without any partial reservation or decision;
10. stale task, stale token and material-basis change behavior;
11. combined-source all-or-nothing confirmation and exact source lineage; and
12. accessible drawer title, focus containment/return, labelled values, note error association and keyboard actions.

### D. Demo seed and scenario delta

**Permanent canonical records:** No new Plan, Version, Demand, Plan Item, Budget Line or user is required.

Correct the `SCN-PLN-ADD-001` arithmetic boundary as follows:

| Boundary | Committed | Remaining reserved | Available | Explanation |
|---|---:|---:|---:|---|
| After corrected Demand approval and before Planning Finance confirmation | KES 310,000,000 | KES 145,000,000 | KES 105,000,000 | `MOH-BL-HWD-2027` remains fully available; Demand approval creates no reservation |
| After Peter confirms `PPI-MOH-2027-022` | KES 310,000,000 | KES 225,000,000 | KES 25,000,000 | `RSV-MOH-0002` reserves the workforce line's full KES 80,000,000 once |

At the post-PLN-UI-06 Finance-task boundary, assert:

- one actionable Finance task exists for Peter Otieno and references `PLN-MOH-2027-001-V2`, `PPI-MOH-2027-022`, `DMD-MOH-2027-019` and `MOH-BL-HWD-2027`;
- the task projection uses **20 August 2027, 10:00 EAT** as the deterministic allocation `as_at` time;
- the workforce line is Approved KES 80,000,000, Reserved KES 0, Committed KES 0 and Available KES 80,000,000;
- the Plan Item requires the full KES 80,000,000 and the derived available-after value is KES 0;
- no `RSV-MOH-0002` or Finance decision exists yet; and
- current Approved Version 1, Active `PPI-MOH-2027-021`, `RSV-MOH-0001` and `TND-MOH-2027-008` remain unchanged.

Invoke the production confirm-funding capability once as Peter Otieno and assert:

- exactly one `RSV-MOH-0002` exists for KES 80,000,000 and retains Plan/Version/item/Demand/Need Item/Budget Line lineage;
- `MOH-BL-HWD-2027` becomes Reserved KES 80,000,000, Committed KES 0 and Available KES 0;
- the Ministry totals reconcile to KES 310,000,000 committed, KES 225,000,000 remaining reserved and KES 25,000,000 available;
- exactly one Finance decision and one completed task iteration exist;
- Draft Version 2 remains Draft and `PPI-MOH-2027-022` remains Proposed with Finance **Confirmed**; and
- no Plan approval or second Finance sign-off is created.

Rerunning the request or confirmation with the same idempotency key shall return the original task/result and shall not duplicate `RSV-MOH-0002`, a decision, an audit event or an availability decrement.

Use a resettable isolated return branch from the same pre-confirmation boundary to prove that a required Finance reason returns the item to the planner, creates no reservation and permits exactly one linked re-request task iteration. Do not add another permanent Demand, Plan Item or Budget Line for this branch.

### E. Acceptance evidence

`PLN-CHG-009` may be marked implemented only when:

1. PLN-UI-07 continues the approved journey with Proposed `PPI-MOH-2027-022`, not the already operational `PPI-MOH-2027-021`.
2. The task is invisible and inaccessible to actors lacking task-specific Finance authority, rather than rendered with disabled decisions.
3. The screen shows exact source, live allocation, freshness and derived full-confirmation arithmetic without editable Finance or Planning data.
4. Confirm funding reserves the entire KES 80,000,000 once and does not approve the Plan or activate the item.
5. Return to planner requires a reason, creates no reservation and preserves linked task history.
6. Concurrent loss of availability produces no partial mutation and moves the same task to the governed shortfall state.
7. Combined-source confirmation is all-or-nothing.
8. The seed distinguishes the pre-confirmation KES 105,000,000 Ministry availability from the post-confirmation KES 25,000,000 availability and reruns without duplication.

### F. Open decisions

No business decision is proposed for PLN-UI-07. The exact PLN-UI-07A shortfall frame and its Budget & Funding resolution route remain the next review slice. The exact combined-source static presentation remains deferred to the approved post-journey variant pass and shall not be inferred by Stitch.

---

## PLN-CHG-010 — Finance funding shortfall and governed resolution path

**Status:** Approved  
**Approved:** 15 August 2026  
**Source:** Requirements §9.6; Stitch PLN-UI-07A; Implementation Prompt 05; demo scenario `SCN-PLN-FUND-SHORT-001`  
**Scope:** Insufficient-funding state of the existing PLN-UI-07 Finance task and its return-reason confirmation.  
**Problem:** The baseline identifies the correct arithmetic but mixes static screen content with instructions about hidden fields, workflow transitions, task persistence, permissions and Demand amendment. It also uses explanatory copy that describes implementation behavior rather than helping the Budget Officer decide what to do. The governed Budget resolution destination, preservation of the same Finance task and the boundary between Planning, Budget and Demand changes require explicit implementation ownership.

### Locked decision boundary

PLN-UI-07A is not a second approval or a new workflow stage. It is the insufficient-funding presentation of the same current Finance task used by PLN-UI-07.

The Budget Officer has two legitimate choices:

1. open the governed Budget & Funding context for the affected Budget Line while leaving the Finance task pending; or
2. return the Plan Item to the planner with a reason.

Planning shall not offer partial confirmation, inline Budget edits, manual availability overrides or an editable Plan Item value. Funding resolution remains owned by Budget & Funding. A material requirement or approved-value correction remains owned by the Demand amendment and reapproval process.

### A. Requirements delta

**Replace `PLN-FR-047` through `PLN-FR-049` in §9.6 with:**

| ID | Requirement |
|---|---|
| `PLN-FR-047` | Whenever live available funding for any required source allocation is less than that allocation's full amount, the current Finance task shall use the **Insufficient funding** state. Its projection shall show every affected Budget Line, Approved/Reserved/Committed/Available values, authoritative **As at** time, amount required and exact shortfall. A combined Plan Item shall show the overall status and each short source separately. |
| `PLN-FR-048` | The insufficient-funding state shall expose no **Confirm funding** command. Direct confirmation shall repeat the locked live-funding check and fail with the stable insufficient-funding outcome. No partial reservation, negative availability, manual override, funding-line substitution or silent reduction of the source-approved Plan Item value is permitted. |
| `PLN-FR-049` | An authorised Budget Officer may leave the same task **Awaiting confirmation** and open the governed Budget & Funding detail for an affected Budget Line. Opening or returning from that route shall create no Finance decision, reservation, task iteration or Planning mutation. Budget changes shall be performed only through Budget & Funding capabilities and approvals. |
| `PLN-FR-049A` | The Budget & Funding route shall preserve the originating Finance task identity and provide a return path to that task. Task assignment does not itself grant Budget mutation authority; the destination shall independently enforce Budget Line visibility and mutation capabilities. |
| `PLN-FR-049B` | The task shall re-evaluate live availability when opened or refreshed and after a governed funding event affecting its source allocations. When every full source amount becomes available, the same task shall present the sufficient-funding PLN-UI-07 state. It shall not confirm automatically and shall not create a replacement task. |
| `PLN-FR-049C` | The Budget Officer may instead choose **Return to planner**. A separate confirmation shall require one non-empty business reason, state that no funding will be reserved, and use the return command defined by `PLN-FR-046`. Return shall not reject or amend the Approved Demand, change funding, or create a reservation. |
| `PLN-FR-049D` | The planner may correct planner-owned procurement fields after a Finance return. A proposed funding-source, approved-scope or approved-value change shall be rejected by Planning and directed through the governed Demand amendment and reapproval route. Any later Finance request shall create exactly one linked task iteration as defined by `PLN-FR-046`. |
| `PLN-FR-049E` | Shortfall detection, Budget-route navigation, funding-event re-evaluation, return and subsequent confirmation shall be idempotent and concurrency-safe. Repeated events or requests shall not duplicate the Finance task, return decision, reservation or audit evidence. |

### B. Stitch delta

Replace the baseline PLN-UI-07A prompt with the following two exact static reference frames. They contain only visible data, hierarchy, controls and user-facing copy. They do not instruct Stitch to calculate a shortfall, navigate, mutate Budget data, return an item, reveal a field or change task state.

#### PLN-UI-07A-1 — insufficient funding

Design a focused right-side drawer over the dimmed **Finance work queue**. Preserve the existing Procurement navigation, top bar and branding visible behind the drawer. Use the same drawer dimensions and information hierarchy as PLN-UI-07.

Use only this exact isolated reference state:

- Signed-in user: **Peter Otieno**
- Role: **Budget Officer**
- Procuring Entity: **Ministry of Health**
- Financial year: **2027/28**
- Logical Plan: **PLN-MOH-2027-001**
- Current Approved Version: **Version 1**
- Open update: **Draft Version 2**
- Plan Item: **PPI-MOH-2027-022 — Digital health technical staff certification programme**
- Plan Item lifecycle: **Proposed**
- Planning status: **Planning complete**
- Finance status: **Awaiting confirmation**
- Availability status: **Insufficient funding**

Drawer header:

- Title: **Funding shortfall**
- Quiet reference: **PPI-MOH-2027-022**
- Context line: **Ministry of Health Annual Procurement Plan 2027/28 · Draft Version 2**
- Status chips: **Awaiting confirmation** and **Insufficient funding**
- Close icon labelled **Close**

Section heading: **Plan Item**

- Title: **Digital health technical staff certification programme**
- Owner Organisation Unit: **Human Resources Management and Development**
- Source Demand: **DMD-MOH-2027-019 — Digital health technical staff certification programme**
- Need Item: **Accredited digital-health technical staff certification programme**
- Quantity and unit: **1 Programme**
- Required by: **31 December 2027**
- Amount requiring confirmation: **KES 80,000,000**
- Text link: **View Plan Item**

Section heading: **Funding position**

- Budget Line: **MOH-BL-HWD-2027 — Digital Health Workforce Capacity Development**
- Approved allocation: **KES 80,000,000**
- Reserved: **KES 55,000,000**
- Committed: **KES 0**
- Available now: **KES 25,000,000**
- Amount required: **KES 80,000,000**
- Funding shortfall: **KES 55,000,000**
- As at: **20 August 2027, 10:05 EAT**
- Text link: **View Budget Line**

Show one restrained warning notice with this exact copy:

**KES 25,000,000 is currently available. A further KES 55,000,000 is required before funding can be confirmed.**

Below the notice show this exact supporting line:

**Review the Budget Line in Budget & Funding, or return the Plan Item to the planner.**

Drawer footer buttons, left to right:

- Text button: **Close**
- Secondary button: **Return to planner**
- Primary route button: **Open Budget & Funding**

Do not show a Finance note, return-reason field, Confirm funding button, disabled confirmation button, editable funding value, Budget Line selector, partial amount, override, Approve, Reject, Demand amendment instruction, workflow explanation, screen identifier or developer-oriented “what happens next” section in this frame.

#### PLN-UI-07A-2 — confirm return to planner

Design one compact modal dialog over the dimmed PLN-UI-07A-1 drawer.

Use the same Peter Otieno, Ministry of Health, Draft Version 2 and `PPI-MOH-2027-022` context.

Modal content, in this order:

- Title: **Return Plan Item to planner?**
- Introductory copy: **The Plan Item will return to the planner for correction. No funding will be reserved.**
- Read-only item: **PPI-MOH-2027-022 — Digital health technical staff certification programme**
- Read-only shortfall: **KES 55,000,000**
- Required multiline field label: **Reason for return**
- Placeholder: **Explain what the planner needs to address.**
- Secondary button: **Cancel**
- Primary restrained button: **Return to planner**

Do not show Budget editing, Confirm funding, Reject, Plan approval, Demand amendment controls, reservation fields or post-return messages in the modal.

### C. Implementation delta

Implement PLN-UI-07A as a state-specific projection of the protected task service defined by PLN-CHG-009, plus context-preserving Budget navigation and the existing return command.

**Projection and state selection:**

- use the same task route, assignment, PE/funding scope and protected-data checks as PLN-UI-07;
- load authoritative current allocation values and calculate each source shortfall server-side whenever the task is opened or refreshed;
- select PLN-UI-07A when at least one source lacks its full required amount; return every short source and overall **Insufficient funding** status;
- omit the confirm capability and command descriptor entirely in this state rather than returning a disabled action;
- keep the task current and **Awaiting confirmation** while no Finance decision has been made;
- do not persist the presentation state as a second task, decision or approval stage.

**Budget & Funding route:**

- construct the destination from the authoritative affected Budget Line identity and originating Finance task identity; do not accept a client-supplied cross-PE Budget Line destination;
- route to the governed Budget Line/allocation detail, not an inline Planning editor or generic unscoped landing page;
- independently enforce Budget module visibility and mutation capabilities at the destination; Finance-task authority alone shall not grant Budget mutation;
- preserve a safe return target to the same Finance task;
- opening, cancelling or returning from Budget & Funding shall create no Finance decision, reservation, task iteration or Planning mutation.

**Re-evaluation:**

- consume or query governed Budget funding events using Plan Item/source/Budget Line identities rather than display labels;
- re-evaluate the same open task after a relevant event and on explicit refresh/open;
- when all full source amounts are available, return the ordinary PLN-UI-07 projection with **Confirm funding** available to the authorised officer;
- never auto-confirm, auto-reserve, close or duplicate the task after funding resolution;
- if funding remains insufficient, update the same projection and exact shortfall without creating history noise.

**Return path:**

- opening or cancelling PLN-UI-07A-2 is mutation-free;
- submit only task identity, expected concurrency token, trimmed required reason and idempotency key;
- use the PLN-CHG-009 return transaction to create one return decision, close the current task iteration, create no reservation and reopen the planner-owned item fields;
- if an upstream funding/value/scope amendment is needed, enforce that boundary in the planner command service; do not mutate the Approved Demand or Budget Line from the return modal.

**Direct command and concurrency protection:**

- a confirm request against a task whose live allocation is insufficient shall return the stable insufficient-funding outcome and current shortfall projection;
- lock/reload before any confirmation or return mutation;
- no race may create a partial reservation, negative availability, duplicate decision or simultaneous completed/returned task state;
- make repeated Budget events, refreshes, return commands and later Finance requests idempotent.

**Focused tests:**

1. exact PLN-UI-07A-1 projection for the KES 55,000,000 scenario hold;
2. no confirm action in the projection and stable rejection of direct confirm attempts;
3. exact Approved/Reserved/Committed/Available/required/shortfall arithmetic and `as_at` value;
4. same protected-task access denials as PLN-UI-07;
5. context-preserving Budget Line route and independent Budget capability enforcement;
6. opening and returning from Budget & Funding without Finance or Planning mutation;
7. governed release of the hold changing the same task to PLN-UI-07 without automatic confirmation;
8. continued shortfall updating the same task without duplication;
9. exact PLN-UI-07A-2 modal, mandatory reason and mutation-free Cancel;
10. Return to planner with no reservation or Budget change and one retained decision;
11. combined-source task listing every short source and permitting no isolated source confirmation;
12. duplicate events, commands, stale token and concurrent allocation changes; and
13. accessible warning semantics, drawer/modal focus handling, labels, error association and focus restoration.

### D. Demo seed and scenario delta

Retain `SCN-PLN-FUND-SHORT-001` as an isolated resettable scenario. It shall not alter the canonical successful `SCN-PLN-ADD-001` outcome.

**Preparation boundary:**

1. Start from the approved PLN-CHG-009 pre-confirmation state: one open Finance task for Peter Otieno, `PPI-MOH-2027-022` Proposed and Planning complete, workforce line Available KES 80,000,000, and no `RSV-MOH-0002`.
2. At **20 August 2027, 10:05 EAT**, create exactly one scenario-owned governed hold `RSV-MOH-SHORT-001` for KES 55,000,000 against `MOH-BL-HWD-2027` through the production reservation capability.
3. Label it **Concurrent workforce funding hold — scenario only** and retain fixture ownership so reset can remove only this record.

Assert the exact PLN-UI-07A-1 state:

| Field | Value |
|---|---:|
| Budget Line Approved | KES 80,000,000 |
| Reserved | KES 55,000,000 |
| Committed | KES 0 |
| Available now | KES 25,000,000 |
| Amount required | KES 80,000,000 |
| Funding shortfall | KES 55,000,000 |
| Finance task | Same iteration; Awaiting confirmation |
| `RSV-MOH-0002` | Absent |
| Plan/version/item | Draft Version 2; `PPI-MOH-2027-022` Proposed |

Opening the contextual Budget & Funding route and returning without a governed change shall leave this state unchanged.

**Deterministic resolution branch:**

- release `RSV-MOH-SHORT-001` once through the production Budget & Funding/reservation capability;
- re-evaluate the same Finance task to PLN-UI-07 with KES 80,000,000 available;
- create no Finance decision, replacement task or `RSV-MOH-0002` during re-evaluation;
- allow Peter Otieno to confirm later through the production PLN-UI-07 command, creating `RSV-MOH-0002` exactly once.

**Isolated return branch:**

- begin again from the shortfall state;
- submit **Funding is not currently sufficient on the proposed Budget Line. Review the funding source before requesting confirmation again.** as the exact return reason;
- assert one return decision, no `RSV-MOH-0002`, no change to `RSV-MOH-SHORT-001`, the item **Returned by Finance**, and no Plan approval;
- a later valid planner re-request creates one linked Finance task iteration and retains the prior reason.

Repeated scenario preparation, route navigation, release, re-evaluation, return and reset shall not duplicate a hold, task, decision, reservation or audit event. Reset shall remove only scenario-owned shortfall records and restore the approved PLN-CHG-009 pre-confirmation state.

### E. Acceptance evidence

`PLN-CHG-010` may be marked implemented only when:

1. PLN-UI-07A is demonstrably the insufficient-funding state of the same protected Finance task, not another approval or task.
2. The screen shows exact live allocation arithmetic, freshness and shortfall for `PPI-MOH-2027-022`.
3. Confirm funding is absent and direct confirmation cannot create a partial or negative reservation.
4. Budget resolution occurs only in the governed Budget & Funding context with independent capability enforcement.
5. Budget navigation creates no Finance decision or Planning mutation and preserves a return path to the same task.
6. Funding resolution changes the same task to PLN-UI-07 without automatic confirmation.
7. Return uses its own exact static confirmation frame, requires a reason and creates no reservation or Budget change.
8. Stitch contains no hidden-field behavior, screen IDs, workflow instructions, Demand-amendment rules or developer-oriented “what happens next” copy.
9. The isolated seed scenario resets without altering the canonical successful funding story.

### F. Open decisions

No business decision is proposed. Exact combined-source shortfall presentation remains deferred to the approved post-journey variant pass and shall not be inferred by Stitch.

---

## PLN-CHG-011 — Head-of-Procurement review of a Finance-confirmed Plan update

**Status:** Approved  
**Approved:** 15 August 2026  
**Source:** Requirements §9.7; Stitch PLN-UI-08; Implementation Prompt 05; demo scenario `SCN-PLN-ADD-001`  
**Scope:** Ready-for-decision professional review of Draft Version 2 and the separate return-reason confirmation.  
**Problem:** The baseline PLN-UI-08 reviews Draft Version 1 and only `PPI-MOH-2027-021`, repeating an already approved historical state rather than continuing the post-approval addition journey. It does not show the submitted change against the operational Approved baseline, identifies the preparer as a generic function instead of the responsible planner, and leaves submission locking, protected task visibility, revalidation, return effects and atomic successor approval incomplete. The screen must not reintroduce Organisation Unit contributions or routine HoD planning sign-off.

### Locked decision boundary

PLN-UI-08 is the single professional approval task after the planner has submitted a complete Plan Version whose applicable Plan Items have current Finance confirmation and no blocking validation issue.

For the canonical update, Grace Wanjiku decides whether Draft Version 2 should replace current Approved Version 1. She reviews the whole submitted Version and the exact change, but edits nothing. Her decision is **Approve plan update** or **Return to planner**—not approval of the Demand, Budget, Finance confirmation, Tender or individual Organisation Unit contribution.

Approval makes the submitted Version the current Approved planning baseline and activates its Proposed item. It does not create a Tender, duplicate a reservation, repeat HoD approval or edit the predecessor Version.

### A. Requirements delta

**Replace §9.7 with:**

#### 9.7 Validation, submission and professional approval

| ID | Requirement |
|---|---|
| `PLN-FR-050` | Plan validation shall be calculated from authoritative Plan Version, Plan Item Version, source-allocation, Finance-confirmation, removal and handoff records. It shall present business-readable issues using only **Not run**, **Ready**, **Needs attention**, **Blocked** and **Stale**, and each non-ready issue shall identify the affected record and permitted remediation owner. |
| `PLN-FR-051` | **Submit for review** shall require one editable Draft with at least one effective change, every included item Planning complete, every applicable item holding current full Finance confirmation, no blocking or stale issue, and the required Plan-update reason. Submission shall revalidate under lock, change the Version to **In review**, make the submitted snapshot read-only, and create or reuse exactly one actionable professional-review task. |
| `PLN-FR-052` | Submission and approval shall not require Departmental Submission, Organisation Unit contribution, routine HoD planning sign-off or another Budget approval. The earlier HoD decision remains part of each Approved Demand's source history and is not repeated in Planning. |
| `PLN-FR-053` | Only the assigned Head of Procurement or another actor holding the explicit professional Plan-approval capability for the same PE may list, open or decide the review task. Record visibility, Administrator status, Procurement Planner authority or Head-of-Department status alone shall not expose the task form. Direct route and decision attempts shall be denied before protected task data is returned. |
| `PLN-FR-054` | The PLN-UI-08 projection shall show the logical Plan and submitted Version, current Approved predecessor, exact update type/reason, submitter/time, approved-versus-submitted values, every included Plan Item and its change/lifecycle state, owner OU, planned value, method, completion date, Finance state, validation state, source and reservation lineage available through read-only detail, and the prior decision trail. It shall show no editable Planning, Finance, Demand, Budget or Tender field. |
| `PLN-FR-055` | The professional authority may **Approve plan update** or **Return to planner**. An approval note is optional. Return shall use a separate confirmation with one required non-empty business reason. Opening, cancelling or viewing either decision surface shall not mutate the Plan or task. |
| `PLN-FR-056` | **Approve plan update** shall revalidate authority, task currency, Version state, effective changes, Plan and item completeness, current full Finance confirmations, source/allocation integrity, proposed removals and downstream constraints under lock. Any failed check shall leave the current Approved Version and all submitted records unchanged and shall return business-readable issues. |
| `PLN-FR-057` | Successful approval shall atomically record one professional decision; lock the submitted Plan and Plan Item Version snapshots; make Draft Version 2 the current **Approved** Version; mark the predecessor Version **Superseded**; activate each added Proposed Plan Item; apply any valid proposed removals; make submitted allocations effective once; complete the review task; and retain all Version, item, source, Finance, reservation and decision lineage. |
| `PLN-FR-058` | Approval of a successor shall preserve the stable identity, Active state, reservation and Tender/downstream handoffs of every unchanged carried-forward Plan Item. It shall not create or duplicate a Finance reservation, Tender, publication record, Demand approval or HoD decision. |
| `PLN-FR-059` | **Return to planner** shall atomically record one return decision, complete the current review-task iteration, change the submitted Version to **Returned**, preserve current Approved Version 1 as operational, preserve existing Finance confirmations and reservations unless their governed basis later changes, and reopen only the planner-owned Draft/update fields. One later valid resubmission shall create one linked review-task iteration without losing prior evidence. |
| `PLN-FR-059A` | Preference/reservation coverage shall appear in professional review only when it is derived from a governed supported source. If no such source exists, the section shall be absent, shall not display zero/Not applicable placeholders and shall not block approval. |
| `PLN-FR-059B` | Submission, approval, return, successor replacement, item activation/removal and review-task iteration creation shall be optimistic-concurrency protected and idempotent. Repeated or concurrent commands shall not duplicate decisions, allocations, activations, removals, tasks or audit events, and shall never leave two current Approved Versions. |

**Consequential clarification:** `PLN-FR-065` in §9.8 shall reference the atomic successor-approval behavior in `PLN-FR-056` through `PLN-FR-059B` rather than define a second approval mechanism.

### B. Stitch delta

Replace the baseline PLN-UI-08 prompt with the following two exact static frames. They contain only visible data, layout, controls and user-facing copy. They do not instruct Stitch to submit, approve, return, validate, activate, supersede, route, enforce permissions or reveal fields.

#### PLN-UI-08-1 — ready professional review

Design the main content area for **PLN-UI-08 Procurement Plan review**. Preserve the existing Procurement navigation, top bar and branding. Use a wide read-only review page with a restrained decision rail on the right. Do not use tabs, a stepper or a wizard.

Use only this exact reference state:

- Signed-in user: **Grace Wanjiku**
- Role: **Head of Procurement**
- Procuring Entity: **Ministry of Health**
- Financial year: **2027/28**
- Logical Plan: **PLN-MOH-2027-001**
- Current Approved Version: **Version 1**
- Submitted Version: **Version 2**
- Submitted Version state: **In review**
- Validation: **Ready**
- Submitted by: **Mercy Kilonzo, Procurement Planner**
- Submitted at: **20 August 2027, 10:30 EAT**

Header, in this order:

- Breadcrumb: **Procurement Planning / Review queue / PLN-MOH-2027-001-V2**
- Title: **Review procurement plan update**
- Context line: **Ministry of Health Annual Procurement Plan 2027/28 · Version 2**
- Status chips: **In review** and **Ready**
- Quiet notice: **Approved Version 1 remains active until this review is completed.**

Show one compact summary strip:

- **Current approved value:** KES 455,000,000
- **Submitted value:** KES 535,000,000
- **Change:** KES 80,000,000 added
- **Plan Items:** 2
- **Finance confirmed:** 2 of 2
- **Validation:** Ready

Section heading: **Update context**

- Change type: **Additional approved need**
- Reason: **Add the approved digital-health technical staff certification programme to the FY 2027/28 Plan so delivery can begin before 31 December 2027.**
- Submitted by: **Mercy Kilonzo, Procurement Planner**
- Submitted at: **20 August 2027, 10:30 EAT**

Section heading: **Plan Items in submitted Version 2**

Use one compact read-only table with columns:

- Change
- Plan Item
- Organisation Unit
- Planned value
- Method
- Contract completion
- Finance
- Validation
- Action

Show exactly these two rows:

1. **Unchanged** — **PPI-MOH-2027-021 · National digital health infrastructure upgrade** — **Directorate of Digital Health and Policy** — **KES 455,000,000** — **Open tender** — **31 March 2028** — **Confirmed** — **Ready** — text link **View Plan Item**.
2. **Added** — **PPI-MOH-2027-022 · Digital health technical staff certification programme** — **Human Resources Management and Development** — **KES 80,000,000** — **Open tender** — **31 December 2027** — **Confirmed** — **Ready** — text link **View Plan Item**.

Below the first row show the quiet supporting text: **Existing Tender TND-MOH-2027-008 remains operational.**

Section heading: **Review checks**

Show one restrained success notice with this exact copy:

**All required Planning validation and Finance confirmations are ready for decision.**

Do not show a preference/reservation coverage section in this reference frame.

Section heading: **Decision history**

Use a compact read-only list with these exact entries:

- **Draft Version 2 created** — Mercy Kilonzo — **19 August 2027, 09:00 EAT**
- **Funding confirmed for PPI-MOH-2027-022** — Peter Otieno — **20 August 2027, 10:15 EAT**
- **Submitted for professional review** — Mercy Kilonzo — **20 August 2027, 10:30 EAT**

Right decision rail:

- Heading: **Decision**
- Task: **Professional Plan review**
- Submitted Version: **Version 2**
- Finance confirmation: **Complete**
- Validation: **Ready**
- Empty multiline field label: **Approval note**
- Helper text: **Optional**
- Secondary button: **Return to planner**
- Primary button: **Approve plan update**

End the frame after the decision rail and decision history. Add no Organisation Unit contribution, Departmental Submission, HoD planning sign-off, approval matrix, editable Plan Item field, editable funding control, generic statutory-treatment section, Tender configuration or disabled unauthorised state.

#### PLN-UI-08-2 — confirm return to planner

Design one compact modal dialog over the dimmed PLN-UI-08-1 review page.

Use the same Grace Wanjiku, Ministry of Health, `PLN-MOH-2027-001-V2` and Version 1 predecessor context.

Modal content, in this order:

- Title: **Return plan update to planner?**
- Introductory copy: **Version 2 will return to Mercy Kilonzo for correction. Approved Version 1 will remain active.**
- Read-only submitted Version: **PLN-MOH-2027-001-V2**
- Read-only submitted value: **KES 535,000,000**
- Required multiline field label: **Reason for return**
- Placeholder: **Explain what must be corrected before resubmission.**
- Secondary button: **Cancel**
- Primary restrained button: **Return to planner**

End the modal after these controls. Add no item-editing, Finance, Budget, Demand, HoD, Tender or approval-matrix controls.

### C. Implementation delta

Implement PLN-UI-08 as a protected professional-review task projection and two explicit commands over one submitted Plan Version.

**Submission boundary:**

- implement submission from the editable Draft overview, not from PLN-UI-08;
- require planner mutation capability for the same PE/FY, a current editable Draft with at least one effective change, complete included items, current full Finance confirmation for every applicable item, no blocking/stale issue and the required update reason;
- in one transaction, lock and reload the Plan/Draft/items/allocations/Finance state, rerun validation, set the Version **In review**, persist the immutable submitted snapshot and create or reuse one professional-review task through configured routing;
- roll back the submission state if task creation fails and return the original task/result for an idempotent retry;
- while In review, expose neutral read-only Plan detail to permitted non-task viewers and no edit/mutation actions to the planner.

**Task route and projection:**

- resolve the review task by stable identity and derive the Plan, submitted Version, predecessor, included item versions, changes, source/Finance/reservation lineage and decision history server-side;
- require current task assignment/configured delegation, explicit professional Plan-approval capability and matching PE before returning protected task data;
- do not infer task access from Administrator, Planner, HoD, Budget Officer, Requester, Viewer or general Plan visibility;
- return exact submitted-versus-approved totals, update context, item states, current Finance/validation results and only the currently permitted decision commands;
- provide read-only item-detail links without exposing planner mutation controls or other actors' task forms;
- omit unsupported preference/reservation coverage rather than manufacturing zero or Not applicable values.

**Approve command:**

- accept task identity, expected concurrency token, optional trimmed approval note and idempotency key only;
- lock and reload the logical Plan, current Approved predecessor, submitted Version, item versions, effective changes, source allocations, Finance confirmations/reservations, removal candidates, downstream handoffs, review task and competing successors;
- revalidate authority, task/Version currency, effective-change set, completeness, validation, current full Finance confirmation, source integrity and removal eligibility;
- on any failure, perform no partial Version, item, allocation, task or decision mutation and return stable business-readable issues;
- on success, create one approval decision, mark Version 2 current **Approved**, mark Version 1 **Superseded**, activate `PPI-MOH-2027-022`, apply any validated proposed removals, make Draft allocations effective once, lock submitted snapshots and complete the task atomically;
- preserve `PPI-MOH-2027-021`, `RSV-MOH-0001`, `TND-MOH-2027-008` and every unchanged handoff without cloning or relinking;
- preserve `RSV-MOH-0002` as the current reservation for `PPI-MOH-2027-022`; do not create a second reservation;
- create no Tender, publication, Demand/HoD decision or Finance decision;
- route the successful result to neutral current Approved Plan detail, PLN-UI-09.

**Return command:**

- opening or cancelling PLN-UI-08-2 is mutation-free;
- accept task identity, expected concurrency token, required trimmed reason and idempotency key only;
- atomically create one return decision, complete the task iteration and set Version 2 **Returned**;
- keep Version 1 current Approved and all existing operational handoffs unchanged;
- retain current Finance confirmations/reservations and reopen only planner-owned Draft/update fields;
- make Finance stale only when a later governed change affects its confirmation basis;
- create one linked review task iteration on one later valid resubmission and preserve the prior return.

**Concurrency, idempotency and downstream boundary:**

- enforce the invariant of one current Approved Version and at most one open successor at database/service level;
- repeat approve, return and submit commands safely without duplicate task, decision, activation, allocation, removal or audit effects;
- reject approve-versus-return races and stale review tasks without partial mutation;
- prevent Tender take-up of `PPI-MOH-2027-022` before successful approval and permit it only from the resulting Active item through the governed Planning handoff service.

**Focused tests:**

1. exact PLN-UI-08-1 projection for submitted Version 2 with two items and KES 535,000,000 total;
2. one current professional-review task created by atomic submission and immutable In-review state;
3. task visibility and direct-route/command denial for Planner, HoD, Budget Officer, Requester, Viewer, unassigned authority and Administrator-without-task;
4. exact approved-versus-submitted change, update reason, submitter/time, item states, Finance/validation and decision history;
5. absence of OU contribution, Departmental Submission, routine HoD sign-off, editable fields and unsupported coverage;
6. revalidation immediately before approval, including stale Finance, changed source, blocking issue and concurrent successor failures;
7. atomic Version 2 approval, Version 1 supersession and `PPI-MOH-2027-022` activation;
8. preservation of unchanged `PPI-MOH-2027-021`, `RSV-MOH-0001` and `TND-MOH-2027-008` identity/links;
9. preservation without duplication of `RSV-MOH-0002` and absence of Tender/publication/Demand/HoD/Finance side effects;
10. exact PLN-UI-08-2 modal, mandatory reason and mutation-free Cancel;
11. return preserving Version 1 and current Finance evidence while reopening only planner-owned fields;
12. linked resubmission after return without task or decision duplication;
13. duplicate click, retry, stale token, approve/return race and one-current-Approved invariant; and
14. accessible page landmarks, table headers, status announcements, decision controls, modal focus and error association.

### D. Demo seed and scenario delta

Use the canonical successful `SCN-PLN-ADD-001` branch after approved PLN-CHG-009 funding confirmation. No new permanent user, Plan, Version, Demand, Plan Item, reservation or Tender record is required.

**Submitted review boundary:**

1. Fix Draft Version 2 creation at **19 August 2027, 09:00 EAT**.
2. Fix Peter Otieno's `PPI-MOH-2027-022` Finance confirmation at **20 August 2027, 10:15 EAT** and retain exactly one `RSV-MOH-0002` for KES 80,000,000.
3. Store this exact update reason: **Add the approved digital-health technical staff certification programme to the FY 2027/28 Plan so delivery can begin before 31 December 2027.**
4. Submit Version 2 through the production submission capability as Mercy Kilonzo at **20 August 2027, 10:30 EAT**.

Assert:

- exactly one review task is assigned to Grace Wanjiku;
- Version 2 is **In review**, read-only and totals KES 535,000,000;
- Version 1 remains current Approved at KES 455,000,000;
- `PPI-MOH-2027-021` remains Active with `RSV-MOH-0001` and `TND-MOH-2027-008` unchanged;
- `PPI-MOH-2027-022` remains Proposed with current `RSV-MOH-0002` and no Tender;
- both included items are Finance **Confirmed** and validation is **Ready**;
- no Departmental Submission, Organisation Unit contribution/sign-off, routine HoD planning decision or preference/reservation coverage record exists; and
- repeating submission creates no second task or audit event.

**Canonical approval branch:**

Approve once through the production professional command as Grace Wanjiku at **20 August 2027, 11:00 EAT** and assert:

- one professional approval decision and one completed task iteration;
- Version 2 becomes the sole current **Approved** Version at KES 535,000,000;
- Version 1 becomes **Superseded** and remains immutable/auditable;
- `PPI-MOH-2027-022` becomes Active and retains `RSV-MOH-0002` without duplication;
- `PPI-MOH-2027-021`, `RSV-MOH-0001` and `TND-MOH-2027-008` retain their stable identities and operational links;
- no Tender is created for `PPI-MOH-2027-022` by Plan approval; and
- rerunning approval returns the original result without another decision, activation, allocation effect or audit event.

**Isolated return branch:**

Restart from the submitted review boundary and submit **Clarify the planned delivery sequence for the added certification programme before approval.** as the exact return reason at **20 August 2027, 11:00 EAT**. Assert one return decision, Version 2 **Returned**, Version 1 still current Approved, both reservations unchanged, no item activation and one linked task iteration only after a later valid resubmission.

Reset shall remove only scenario-owned Version 2 submission/decision state and restore the approved PLN-CHG-009 pre-review boundary without modifying the current Version 1 operational records.

### E. Acceptance evidence

`PLN-CHG-011` may be marked implemented only when:

1. PLN-UI-08 reviews submitted Version 2 at KES 535,000,000 with both the unchanged operational item and the added Proposed item.
2. Only the assigned professional authority can see, open or decide the task; permitted non-task viewers receive neutral detail instead.
3. No Organisation Unit contribution, Departmental Submission or routine HoD planning sign-off exists.
4. Approval revalidates and atomically replaces the current Approved Version without duplicating items, allocations, reservations or handoffs.
5. The unchanged Active item and Tender remain operational and retain stable identity.
6. The added item becomes Active only on Plan approval, retains its existing reservation and receives no automatic Tender.
7. Return requires a reason, keeps Version 1 operational, retains current Finance evidence and reopens only planner-owned fields.
8. Unsupported preference/reservation coverage is omitted and does not block approval.
9. Submission, approval, return and reset are deterministic, concurrency-safe and idempotent.

### F. Open decisions

No business decision is proposed. Exact blocked/stale review, initial-Plan approval and post-return/resubmission static variants remain scheduled for the approved post-journey variant pass and shall not be inferred by Stitch.

---

## PLN-CHG-012 — Current Approved Plan detail and Tender implementation handoff

**Status:** Approved  
**Approved:** 15 August 2026  
**Source:** Requirements §9.9; Stitch PLN-UI-09; Implementation Prompt 06; approved PLN-CHG-001 and PLN-CHG-011  
**Scope:** The route from **View approved plan**, the current Approved Plan projection and downstream Tender-preparation/implementation visibility.  
**Problem:** The baseline PLN-UI-09 is still fixed to Approved Version 1 at KES 455,000,000 even though the approved journey now makes Version 2 current at KES 535,000,000. The workspace action **View approved plan** has no explicit route contract, so an implementation can incorrectly open a Draft update or create one as a side effect. The screen also fails to show the newly Active item that has not yet entered Tender Management. The baseline additionally introduced Plan publication without a confirmed MVP requirement and used terminology that could be confused with publishing a Tender for bid submission.

### Locked decision boundary

PLN-UI-09 is the neutral operational detail for the one current Approved Version of the selected logical Plan. **View approved plan** opens it without creating or reusing a Draft successor. Approved content is read-only.

The Procurement Planner can begin a separate Plan update from this page through **Add Plan Item** or, for an eligible Active item, **Propose removal**. Merely opening either entry surface is mutation-free; the governed confirmation creates or reuses the Draft successor.

After approval, each Active Plan Item becomes available to the separately authorised Tender Management preparation process. PLN-UI-09 shows the resulting take-up and implementation state but does not give the Procurement Planner an unauthorised Tender action. Planning contains no Plan-publication/disclosure capability in MVP. **Publish** is reserved for the Tender Management action that makes a configured Tender available for bid submission.

### A. Requirements delta

**Replace §9.9 with:**

#### 9.9 Current Approved Plan, Tender handoff and monitoring

| ID | Requirement |
|---|---|
| PLN-FR-070 | The Planning workspace action **View approved plan** shall open PLN-UI-09 for the current Approved Version of the selected PE, financial year and logical Plan. Opening the route shall create no Draft successor, update reason, allocation, task, decision or audit mutation. The action shall be absent when no Approved Version exists. |
| PLN-FR-070A | PLN-UI-09 shall resolve the current Approved Version server-side and show its Plan reference, Version, approval state/time, approved value, Active Plan Items, owner OUs, current Finance coverage, Tender take-up, planned milestones, downstream actual progress and variance. It shall not edit Approved fields or behave as a review task. |
| PLN-FR-070B | A permitted viewer may open neutral PLN-UI-09. Add, removal, export and downstream actions shall each be evaluated from their own capability and scope; record visibility alone shall not grant a mutation. Unavailable mutations shall not be presented as disabled task forms. |
| PLN-FR-070C | **Add Plan Item** shall open PLN-UI-04 without mutation. **Propose removal** shall be available only for an Active item with no Tender handoff, commitment or downstream execution and shall open the approved PLN-UI-05A confirmation without mutation. The confirmed commands shall create or reuse one Draft successor under §9.8. |
| PLN-FR-071 | Procurement Planning shall not publish or publicly disclose an Approved Plan in MVP. It shall expose no Plan-publication action, status, destination, evidence, capability, command or seed record. **Publish** shall be reserved for Tender Management when a configured and authorised Tender is made available for bid submission. |
| PLN-FR-072 | Tender take-up shall require a separate authorised Tender Management command over an Active Plan Item in the current Approved Version with current funding and remaining take-up. PLN-UI-09 shall not expose Tender initiation to an actor who lacks that capability. |
| PLN-FR-073 | Tender take-up shall atomically create one immutable Planning Handoff Snapshot and shall be concurrency protected and idempotent. |
| PLN-FR-074 | The handoff shall preserve logical Plan, Approved Version, Plan Item/version, Demand allocations, Finance/reservation and Strategy lineage. |
| PLN-FR-075 | Implementation and actual milestones shall be derived from downstream records. Absence of a Tender shall be shown as **Not started** and shall not be represented as failure while the next planned milestone is not overdue. |
| PLN-FR-076 | Reporting shall show the selected scope, reporting period, **As at** time, approved value, Finance coverage, Tender take-up and schedule variance without claiming realised value unsupported by downstream evidence. Derived counts and variance shall reconcile to the visible item rows. |

### B. Stitch delta

Replace the baseline PLN-UI-09 prompt with this one exact static frame. It contains visible data, layout, controls and user-facing copy only.

#### PLN-UI-09 — current Approved Plan and implementation

Design the main content area for **PLN-UI-09 Approved Plan and implementation**. Preserve the existing Procurement navigation, top bar and branding. Use a wide operational detail page, not a dashboard, task form, wizard or editable Plan builder.

Use only this exact reference state:

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Procuring Entity: **Ministry of Health**
- Financial year: **2027/28**
- Logical Plan: **PLN-MOH-2027-001**
- Plan lifecycle: **Open**
- Current Approved Version: **Version 2**
- Approved by: **Grace Wanjiku, Head of Procurement**
- Approved at: **20 August 2027, 11:00 EAT**
- Reporting period: **Q1 · FY 2027/28**
- As at: **20 August 2027, 11:05 EAT**

Header, in this order:

- Breadcrumb: **Procurement Planning / Ministry of Health / 2027/28**
- Title: **Ministry of Health Annual Procurement Plan 2027/28**
- Context line: **Open Plan · Approved Version 2**
- Quiet supporting line: **Approved by Grace Wanjiku on 20 August 2027 at 11:00 EAT**
- Primary button: **Add Plan Item**
- Secondary button: **Export approved plan**

Show one compact summary strip:

- **Approved plan value:** KES 535,000,000
- **Active Plan Items:** 2
- **Finance confirmed:** 2 of 2
- **Tender take-up:** 1 of 2

Show one compact filter row:

- Reporting period select: **Q1 · FY 2027/28**
- Read-only **As at:** **20 August 2027, 11:05 EAT**
- Organisation Unit select: **All permitted units**
- Status select: **All statuses**

Section heading: **Plan implementation**

Use a compact read-only table with columns:

- Requirement
- Organisation Unit
- Approved value
- Tender take-up
- Next planned milestone
- Actual progress
- Variance
- Action

Show exactly these two rows:

1. **PPI-MOH-2027-021 · National digital health infrastructure upgrade** — **Directorate of Digital Health and Policy** — **KES 455,000,000** — **Tender active · TND-MOH-2027-008** — **Evaluation complete by 15 November 2027** — **Tender in progress** — **On schedule** — text link **View implementation**.
2. **PPI-MOH-2027-022 · Digital health technical staff certification programme** — **Human Resources Management and Development** — **KES 80,000,000** — **Not started** — **Tender advertisement by 8 November 2027** — **No Tender started** — **On schedule** — text link **View Plan Item**, followed by a restrained overflow action labelled **Propose removal**.

Section heading: **Version history**

Use a compact read-only two-row list:

- **Version 2** — **Approved** — KES 535,000,000 — Approved 20 August 2027
- **Version 1** — **Superseded** — KES 455,000,000 — text link **View historical version**

End the frame after Version history. Do not show Plan publication/disclosure, a Draft-update notice, editable Approved field, approval/return action, Organisation Unit contribution, HoD planning sign-off, aggregation control, expenditure entry, Release Package, duplicated Tender control or disabled unauthorised task.

### C. Implementation delta

Implement PLN-UI-09 as a current-Approved projection with separately authorised Plan-update and Tender boundaries.

**Route and projection:**

- make the PLN-UI-01 **View approved plan** route carry only the selected PE, financial year and logical Plan identity;
- resolve the one current Approved Version under scope on the server; never accept a client claim that a particular Version is current;
- return not found/no-access without exposing another PE's Plan when no permitted current Approved Version exists;
- load Plan/version approval evidence, Active item versions, owner OUs, Finance confirmations, reservations, downstream handoffs and planned/actual milestones in a consistent **As at** projection;
- derive all summary values from the same item set used by the table;
- return neutral read-only detail to permitted viewers and expose each action only when its independent capability, scope and record preconditions hold;
- opening or refreshing PLN-UI-09 shall create no Draft, task, decision or audit mutation;
- remove Plan-publication/disclosure actions, states, destinations, evidence, capabilities, services and issues from Procurement Planning.

**Plan-update entry points:**

- **Add Plan Item** opens PLN-UI-04 with the logical Plan context and creates no successor until the approved formation confirmation succeeds;
- **Propose removal** appears only for a server-derived eligible Active item and opens PLN-UI-05A without mutation;
- direct removal calls for PPI-MOH-2027-021 shall fail because TND-MOH-2027-008 exists;
- PPI-MOH-2027-022 may expose the action while no Tender/downstream execution exists; the server shall recheck eligibility under lock at confirmation.

**Tender and reporting boundary:**

- treat Tender data as a downstream projection and link to neutral implementation detail only;
- never infer Tender authority from Procurement Planner or general Planning authority;
- enforce the approved Active/current-Version/current-funding/remaining-take-up conditions in the Tender Management handoff service;
- show **Not started** for PPI-MOH-2027-022 and calculate **On schedule** from the 8 November 2027 milestone and the 20 August 2027 As-at time;
- do not add manual actual-progress, realised-value, expenditure or package fields to Planning.

**Focused tests:**

1. PLN-UI-01 **View approved plan** resolves PLN-UI-09 Version 2 and creates no Draft or audit mutation.
2. Exact KES 535,000,000, two-item, 2-of-2 Finance and 1-of-2 Tender-take-up projection.
3. Approved Version 2 and Superseded Version 1 history with no editable baseline fields.
4. Neutral view for a permitted non-mutating viewer and independent action visibility for add, export and removal.
5. No Approved action when no Approved Version exists and no cross-PE disclosure on direct navigation.
6. PPI-MOH-2027-021 has no removal action; direct calls fail because its Tender exists.
7. PPI-MOH-2027-022 can open PLN-UI-05A without mutation and is rechecked at confirmation.
8. Add Plan Item opens PLN-UI-04 without creating a successor.
9. Absence of Plan-publication/disclosure UI, capability, command, state, issue and seed data.
10. Planner cannot initiate or publish a Tender without the separate Tender capability.
11. Summary/table reconciliation, deterministic As-at variance and accessible table, controls and status copy.

### D. Demo seed and scenario delta

Use the approved PLN-CHG-011 canonical approval result as the PLN-UI-09 boundary:

- Version 2 is the sole current Approved Version at **20 August 2027, 11:00 EAT**;
- Version 1 is Superseded;
- PPI-MOH-2027-021 and PPI-MOH-2027-022 are Active;
- RSV-MOH-0001 and RSV-MOH-0002 remain current without duplication;
- TND-MOH-2027-008 remains linked only to PPI-MOH-2027-021;
- no Tender exists for PPI-MOH-2027-022.

At **20 August 2027, 11:05 EAT**, assert the exact PLN-UI-09 reference projection: KES 535,000,000, two Active items, Finance 2 of 2 and Tender take-up 1 of 2.

Assert that Procurement Planning contains no Plan-publication/disclosure fixture, destination, status, evidence, capability, scenario or issue. Existing Tender publication fixtures, if any, remain owned by Tender Management and shall not be displayed as Plan publication.

### E. Acceptance evidence

PLN-CHG-012 may be marked implemented only when:

1. **View approved plan** opens the current Approved Version in PLN-UI-09 without creating a Draft successor.
2. PLN-UI-09 shows Approved Version 2 at KES 535,000,000 with both Active items and reconciled Finance/Tender counts.
3. Approved fields are read-only and the page is not an approval task or Tender-entry surface.
4. Add and eligible removal entry points are mutation-free until their governed confirmations.
5. Procurement Planning contains no Plan-publication/disclosure action, state, capability, command or seed record.
6. Tender take-up and Tender publication remain separately authorised Tender Management functions using the immutable Planning handoff boundary.
7. The seeded PLN-UI-09 projection is deterministic and contains no misleading Plan-publication data.

### F. Open decisions

No business decision remains open. Plan-publication/disclosure is excluded from Procurement Planning MVP. Open-Draft notice, viewer-only and overdue-milestone static variants remain scheduled for the approved post-journey variant pass and shall not be inferred by Stitch.

---

## PLN-CHG-013 — Draft successor overview and submission readiness

**Status:** Superseded  
**Superseded by:** PLN-CHG-014  
**Source:** Requirements §§9.7–9.8; Stitch PLN-UI-10; Implementation Prompt 06; approved PLN-CHG-007, PLN-CHG-009, PLN-CHG-011 and PLN-CHG-012  
**Scope:** The planner's overview of one Draft successor before Finance confirmation and when ready for professional review.  
**Problem:** The baseline PLN-UI-10 uses inconsistent November dates, identifies the initiator as a generic department, labels the changed item both Finance **Awaiting confirmation** and validation **Ready**, and embeds conditional behavior and several later design states inside one Stitch prompt. It also exposes **Cancel update** without defining its confirmation boundary. The screen must clearly distinguish the operational Approved Version from the proposed Draft changes without becoming a version-management workbench or another approval stage.

### Locked decision boundary

PLN-UI-10 is the planner-owned overview of the one open successor to a current Approved Version. It is not a duplicate Plan builder, Finance task, professional-review task or version-management screen.

The page makes only effective changes primary. The current Approved Version, unchanged Active item and existing Tender remain operational and read-only until successor approval. The planner can edit an added Plan Item through PLN-UI-06, remove it through PLN-UI-05A, save the single Plan-update reason, run validation and—only when the whole Draft is ready—submit it to the protected professional-review process defined by PLN-CHG-011.

### A. Requirements delta

**Replace PLN-FR-060 through PLN-FR-065 in §9.8 with:**

| ID | Requirement |
|---|---|
| PLN-FR-060 | An Approved Version shall be immutable. A logical Plan shall have no more than one editable successor at a time, and that successor shall carry one stable identity through Draft, In review, Returned and final decision. |
| PLN-FR-061 | PLN-UI-10 shall resolve the current Approved predecessor and the one open successor server-side. Opening or refreshing the page shall create no Version, Plan Item, allocation, Finance task, decision or audit mutation. |
| PLN-FR-062 | PLN-UI-10 shall show the logical Plan, predecessor and successor references/states, approved-versus-Draft totals, effective change count, required update reason, each changed Plan Item's change type, owner OU, value, Planning completeness, Finance state and validation state, and compact read-only context for unchanged operational items and Tender handoffs. |
| PLN-FR-063 | Added or changed items shall be the primary editable scope. Unchanged Active items, Approved predecessor fields, existing reservations and Tender handoffs shall remain read-only and operational while the successor is Draft, In review or Returned. |
| PLN-FR-064 | A post-approval successor shall hold one concise non-empty business reason describing the Plan-level change. A scoped Procurement Planner may save that reason while the Version is Draft or Returned. Saving shall not submit the Version, create a Finance decision or change the current Approved baseline. |
| PLN-FR-064A | The overview shall derive a whole-Version readiness result from authoritative item, allocation, Finance, removal and validation records. **Submit update for review** shall be available only when there is at least one effective change, every included changed item is Planning complete, every applicable item has current full Finance confirmation, the update reason is present and no blocking or stale issue exists. |
| PLN-FR-064B | When the Version is not ready, the overview shall show business-readable issues identifying the affected Plan Item and responsible next actor. It shall not expose a disabled professional-review form or permit the planner to make a Finance or approval decision. |
| PLN-FR-065 | Submission from PLN-UI-10 shall use the atomic, locked and idempotent submission boundary in PLN-CHG-011. Success shall make the submitted Version **In review**, preserve the current Approved predecessor as operational and route to neutral submitted detail; it shall not approve the Plan, activate Proposed items, duplicate reservations or create a Tender. |
| PLN-FR-065A | If removal leaves no effective change, submission shall be unavailable and the overview shall show **No changes remain in this update.** Cancelling that empty successor shall require a separate confirmation and shall preserve the Approved predecessor and all audit/removal evidence. A populated successor shall not expose an unqualified one-click **Cancel update** action. |

Retain PLN-FR-066 through PLN-FR-069A as corrected by approved PLN-CHG-007. Successor approval remains governed exclusively by PLN-CHG-011.

### B. Stitch delta

Replace the baseline PLN-UI-10 prompt with these two exact static frames. They contain visible data, layout, controls and user-facing copy only. They do not instruct Stitch to save, calculate, validate, create tasks, enable controls, remove items, submit or change state.

#### PLN-UI-10-1 — update awaiting Finance confirmation

Design the main content area for **PLN-UI-10 Plan update overview**. Preserve the existing Procurement navigation, top bar and branding. Use a wide, compact planner workspace. Do not use tabs, a stepper, a wizard or a side-by-side full-Version diff.

Use only this exact reference state:

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Procuring Entity: **Ministry of Health**
- Financial year: **2027/28**
- Logical Plan: **PLN-MOH-2027-001**
- Current Approved Version: **Version 1**
- Open successor: **Draft Version 2**
- Draft created by: **Mercy Kilonzo**
- Draft created at: **19 August 2027, 09:00 EAT**
- As at: **20 August 2027, 10:00 EAT**

Header, in this order:

- Breadcrumb: **Procurement Planning / Ministry of Health / 2027/28 / Plan update**
- Title: **Plan update**
- Context line: **Ministry of Health Annual Procurement Plan 2027/28 · Draft Version 2**
- Status chips: **Draft** and **Needs attention**
- Primary button: **Run validation**

Show one restrained information notice:

**Approved Version 1 remains active while this update is prepared and reviewed.**

Show one compact change summary:

- **Current approved value:** KES 455,000,000
- **Draft value:** KES 535,000,000
- **Net change:** KES 80,000,000 added
- **Changed Plan Items:** 1
- **Unchanged operational Plan Items:** 1

Section heading: **Update context**

- Read-only Change type: **Additional approved need**
- Multiline field label: **Reason for Plan update**
- Field value: **Add the approved digital-health technical staff certification programme to the FY 2027/28 Plan so delivery can begin before 31 December 2027.**
- Helper text: **Explain why the Approved Plan needs to change.**
- Read-only Created by: **Mercy Kilonzo, Procurement Planner**
- Read-only Created at: **19 August 2027, 09:00 EAT**

Section heading: **Changes in this update**

Use one compact table with columns:

- Change
- Plan Item
- Organisation Unit
- Draft value
- Planning
- Finance
- Validation
- Action

Show exactly one row:

- **Added**
- **PPI-MOH-2027-022 · Digital health technical staff certification programme**
- **Human Resources Management and Development**
- **KES 80,000,000**
- **Complete**
- **Awaiting confirmation**
- **Needs attention**
- Text link **Edit Plan Item** and restrained overflow action **Remove from update**

Show one restrained issue immediately below the table:

**Funding confirmation is still required for PPI-MOH-2027-022 before this update can be submitted for review.**

Section heading: **Unchanged operational item**

Use one compact read-only row:

- **PPI-MOH-2027-021 · National digital health infrastructure upgrade**
- **Active**
- **KES 455,000,000**
- **Finance confirmed**
- **Tender active · TND-MOH-2027-008**
- Text link **View Plan Item**

Bottom action bar:

- Secondary button: **Back to Approved Plan**
- Primary button: **Save draft**

End the frame after the action bar. Do not show **Submit update for review**, **Cancel update**, preference/reservation coverage, a Finance decision, an approval/return decision, Departmental Submission, Organisation Unit contribution, HoD planning sign-off, aggregation controls, source-level removal, editable Approved fields, Plan publication or Tender configuration.

#### PLN-UI-10-2 — update ready for professional review

Design the same PLN-UI-10 page using the same Mercy Kilonzo, Ministry of Health, FY 2027/28, logical Plan, Version 1 predecessor, Draft Version 2, update reason, summary values and item identities.

Use this exact later reference state:

- As at: **20 August 2027, 10:20 EAT**
- Draft status chips: **Draft** and **Ready**

In **Changes in this update**, show the same one added row with:

- Planning: **Complete**
- Finance: **Confirmed**
- Validation: **Ready**
- Action: text link **View Plan Item** and restrained overflow action **Remove from update**

Replace the funding issue with one restrained success notice:

**All required Planning validation and Finance confirmations are ready.**

Keep the unchanged operational row exactly as shown in PLN-UI-10-1.

Bottom action bar:

- Secondary button: **Back to Approved Plan**
- Secondary button: **Save draft**
- Primary button: **Submit update for review**

End the frame after the action bar. Add no submission-result message, review task, Head-of-Procurement decision controls, editable Finance fields, approval matrix, Departmental/OU sign-off, Plan publication or Tender configuration.

### C. Implementation delta

Implement PLN-UI-10 as the authoritative projection and planner command surface for one open successor.

**Route and projection:**

- resolve the logical Plan, current Approved predecessor and one open successor from trusted route context and scope; do not accept client-supplied current-Version claims;
- require matching PE scope and planner record visibility before returning the projection, then evaluate reason-save, item-edit, removal and submission capabilities separately;
- derive effective changes by stable Plan Item identity and lifecycle records, not display labels or a client-generated diff;
- load Planning completeness, current Finance confirmation/freshness, source-allocation integrity, removals, blocking issues and unchanged Tender handoffs from authoritative services in one consistent projection;
- derive summary totals and counts from the same included item set used by the rows;
- opening, refreshing, navigating back or viewing unchanged context creates no mutation.

**Reason and item commands:**

- save the one trimmed non-empty Plan-update reason through an optimistic-concurrency and idempotency protected Draft command;
- permit reason and added-item editing only while the successor is Draft or Returned and the actor has planner mutation capability for the same PE;
- route added-item editing to PLN-UI-06 and whole-item removal to PLN-UI-05A without mutating merely by opening either screen;
- expose no mutation on an unchanged Approved item and preserve PPI-MOH-2027-021, RSV-MOH-0001 and TND-MOH-2027-008 unchanged;
- recalculate the overview after any governed item, Finance or removal event.

**Readiness and submission:**

- calculate whole-Version readiness server-side and return stable business-readable issues per affected item;
- omit the submit capability while PPI-MOH-2027-022 is Awaiting confirmation, Stale, Returned by Finance, Planning incomplete or otherwise blocked;
- after the current KES 80,000,000 Finance confirmation, show Confirmed/Ready without activating the item or changing Version 1;
- on submit, use the locked transaction defined by PLN-CHG-011, rerun all readiness checks and create/reuse exactly one professional-review task;
- reject stale projection/token, concurrent edit, no-effective-change and lost-Finance races without partial state changes;
- after successful submission, make Version 2 In review and read-only, preserve Version 1 as current Approved and do not create a Tender, publication/disclosure record, reservation or second HoD decision.

**Empty-update boundary:**

- when no effective changes remain, return no_changes_remain and the exact empty-update message;
- expose a separate empty-successor cancellation confirmation only in that state;
- cancellation shall preserve the immutable Approved predecessor, removed-item tombstones/source history and audit evidence and shall never be a one-click action on a populated successor.

**Focused tests:**

1. Exact PLN-UI-10-1 projection at 20 August 2027, 10:00 EAT.
2. Exact PLN-UI-10-2 projection at 20 August 2027, 10:20 EAT.
3. One Approved predecessor and one open successor resolved server-side with no mutation on view/refresh/back.
4. Exact totals: KES 455,000,000 Approved, KES 535,000,000 Draft and KES 80,000,000 net addition.
5. Mercy Kilonzo identity, exact update reason and deterministic dates.
6. Awaiting-Finance state omits submission and identifies PPI-MOH-2027-022 and the Finance next actor.
7. Confirmed-Finance state shows Ready and exposes submission without activating the item.
8. Separate visibility and mutation denials for Viewer, Requester, HoD, Budget Officer, Head of Procurement and Administrator without planner scope.
9. Save-reason concurrency/idempotency and no approval/Finance/Tender side effects.
10. Item editor/removal routes are mutation-free until their governed commands.
11. Atomic submission, one task, In-review immutability and preservation of Version 1/PPI-MOH-2027-021/Tender.
12. No-effective-change, empty-successor cancellation and stale/concurrent submission races.
13. Absence of Departmental/OU/HoD planning sign-off, preference placeholders, Plan publication and Tender configuration.
14. Accessible headings, table labels, issue/success semantics, action names, keyboard order and error association.

### D. Demo seed and scenario delta

Use the existing SCN-PLN-ADD-001 records and the approved PLN-CHG-009/011 timestamps. No new permanent Plan, Version, Demand, Plan Item, reservation, Tender or user is required.

**PLN-UI-10-1 boundary — 20 August 2027, 10:00 EAT:**

- PLN-MOH-2027-001-V1 remains current Approved at KES 455,000,000;
- PLN-MOH-2027-001-V2 is the one Draft successor, created by Mercy Kilonzo at 19 August 2027, 09:00 EAT;
- store the exact approved update reason shown in the Stitch frame;
- PPI-MOH-2027-021 remains Active with RSV-MOH-0001 and TND-MOH-2027-008 unchanged;
- PPI-MOH-2027-022 is Proposed, Planning complete, Finance **Awaiting confirmation**, validation **Needs attention** and has no RSV-MOH-0002;
- exactly one Finance task is assigned to Peter Otieno; and
- totals reconcile to KES 455,000,000 Approved, KES 535,000,000 Draft and KES 80,000,000 added.

**PLN-UI-10-2 boundary — 20 August 2027, 10:20 EAT:**

- invoke the approved production Finance command at 10:15 EAT;
- retain exactly one RSV-MOH-0002 for KES 80,000,000;
- PPI-MOH-2027-022 remains Proposed but Finance becomes **Confirmed** and validation becomes **Ready**;
- Version 2 remains Draft and Version 1 remains current Approved;
- submission has not yet occurred and no professional-review task exists; and
- no Tender, publication/disclosure record, HoD decision or duplicate Finance evidence is created.

At 10:30 EAT, the existing PLN-CHG-011 submission scenario continues from PLN-UI-10-2. Repeating preparation or Finance confirmation shall not duplicate the Draft successor, task, reservation, decision or audit event.

### E. Acceptance evidence

PLN-CHG-013 may be marked implemented only when:

1. PLN-UI-10 presents one Draft successor as a change-focused planner overview, not a duplicate Approved Plan or version workbench.
2. The exact pre-Finance and ready-to-submit static frames continue the approved canonical journey.
3. Changed and unchanged items, totals, statuses, identities and dates reconcile to authoritative records.
4. Submission is absent until the whole Version is ready and creates no approval or Tender.
5. The operational Approved Version, reservation and Tender remain unchanged throughout Draft preparation and review submission.
6. Stitch contains no behavioral transition notes, conditional design instructions or invented preference/statutory fields.
7. A populated update has no unqualified one-click cancellation; an empty successor uses a separate governed confirmation.
8. Seed setup, Finance transition and submission handoff are deterministic and idempotent.

### F. Open decisions

No business decision is proposed. Returned, stale/blocked, multiple-change, proposed-removal and no-effective-change static variants remain scheduled for the approved post-journey variant pass and shall not be inferred by Stitch.

---

## PLN-CHG-014 — Consolidate Draft successors into PLN-UI-05 and retire PLN-UI-10

**Status:** Approved  
**Approved:** 15 August 2026  
**Source:** Approved operating simplification; PLN-CHG-004, PLN-CHG-006 and superseded PLN-CHG-013  
**Scope:** Reuse the ordinary Plan-builder route for both initial Drafts and Draft successors; remove PLN-UI-10 from the product and documentation.  
**Problem:** PLN-UI-10 duplicates the Plan builder solely because the editable Version has an Approved predecessor. Version succession is a lifecycle condition, not a separate user task. Sending the planner through a second overview after PLN-UI-04 and PLN-UI-06 complicates the core journey, duplicates status/readiness logic and creates another surface that can drift from PLN-UI-05.

### Locked decision boundary

The system has one ordinary Plan-builder route:

- PLN-UI-03 is its zero-item initial-Draft state.
- PLN-UI-05 is its populated editable-Draft state.
- When the editable Draft is a successor to an Approved Version, PLN-UI-05 adds concise predecessor/change context while retaining the same table, readiness and submission model.

PLN-UI-10 is retired. No redirect, alias, hidden route, projection, component, seed state or implementation task shall preserve it.

The corrected post-approval journey is:

**PLN-UI-09 Approved Plan → PLN-UI-04 Add approved Demands → PLN-UI-06 complete Plan Item → PLN-UI-05 Plan builder → PLN-UI-07 Finance confirmation → PLN-UI-05 Plan builder → PLN-UI-08 professional review → PLN-UI-09 current Approved Plan**

### A. Requirements delta

#### Consequential correction to §9.3.1

Replace PLN-FR-029C and PLN-FR-029J from PLN-CHG-006:

| ID | Requirement |
|---|---|
| PLN-FR-029C | The ordinary Plan-builder route shall render PLN-UI-05 whenever the current editable Draft contains one or more effective Plan Items. This applies both to an initial Draft with no Approved predecessor and to a Draft successor of an Approved Version. It shall not create a separate workflow record or screen because a predecessor exists. |
| PLN-FR-029J | For an initial Draft, PLN-UI-05 shall show the included Proposed Plan Items. For a Draft successor, the same screen shall show concise Approved-predecessor context, the Plan-level update reason and effective changed items as the actionable rows, with unchanged operational items represented only by compact read-only context. It shall not show a raw full-Version diff or duplicate the Approved Plan. |

Retain the remaining PLN-FR-029D through PLN-FR-029I and PLN-FR-029K, applying their builder totals, item states, actions, validation and submission rules to both Draft types.

#### Replace PLN-FR-060 through PLN-FR-065 in §9.8

| ID | Requirement |
|---|---|
| PLN-FR-060 | Approved Versions shall remain immutable. A logical Plan shall have no more than one editable successor, which shall retain one stable identity through Draft, In review, Returned and final decision. |
| PLN-FR-061 | Adding an Approved Demand to a Plan that already has a current Approved Version shall create or reuse the single Draft successor only when the PLN-UI-04 formation confirmation succeeds. The result shall use the ordinary Plan-builder route; no manual revision step or separate update overview shall exist. |
| PLN-FR-062 | When PLN-UI-05 represents a Draft successor, it shall show the current Approved predecessor and Draft references/states, approved and Draft totals, net change, required update reason, changed-item count, Planning/Finance/validation state for each effective change and compact read-only confirmation that unchanged Active items and Tender handoffs remain operational. |
| PLN-FR-063 | The planner may edit only the Draft successor and its effective changed items. Approved predecessor fields, unchanged Active items, reservations and Tender handoffs shall remain read-only and operational until successor approval. |
| PLN-FR-064 | A post-approval successor shall hold one concise non-empty Plan-level update reason. A scoped Procurement Planner may save it while the Version is Draft or Returned. Saving shall not submit or approve the Version, create a Finance decision or alter the current Approved baseline. |
| PLN-FR-064A | PLN-UI-05 shall derive whole-Version readiness from authoritative item, allocation, Finance, removal and validation records. Submission shall be available only when at least one effective change exists, the update reason is present, every included item is Planning complete, every applicable item has current full Finance confirmation and no blocking or stale issue exists. |
| PLN-FR-064B | When the successor is not ready, PLN-UI-05 shall show business-readable issues identifying the affected item and responsible next actor. It shall not expose another actor's Finance or approval decision form. |
| PLN-FR-065 | Submission from PLN-UI-05 shall use the atomic submission boundary in PLN-CHG-011. Success shall make the Version In review, preserve the current Approved predecessor as operational and create or reuse one professional-review task. It shall not approve the Plan, activate Proposed items, duplicate a reservation or create a Tender. |
| PLN-FR-065A | If removal leaves no effective change, submission shall be unavailable. Cancelling an empty successor shall use a separate governed confirmation; a populated successor shall not expose an unqualified one-click cancellation. |
| PLN-FR-065B | PLN-UI-10 is not part of the MVP screen inventory. All entry points, requirements, routes, tests and seed references that formerly targeted PLN-UI-10 shall target the state-appropriate PLN-UI-05 Plan-builder projection. |

Retain PLN-FR-066 through PLN-FR-069A as corrected by PLN-CHG-007. Approval remains governed exclusively by PLN-CHG-011.

### B. Stitch delta

1. Retain the approved PLN-UI-03 empty initial-Draft frame.
2. Retain the approved PLN-UI-05 populated initial-Draft frame.
3. Add the following two exact successor states to PLN-UI-05.
4. Delete the entire PLN-UI-10 prompt and every PLN-UI-10 journey reference.

#### PLN-UI-05 — successor Draft awaiting Finance confirmation

Design the populated Plan builder using the existing PLN-UI-05 layout, navigation, toolbar and table density. Do not create a separate update page, comparison workbench, stepper, tab set or wizard.

Use only this exact state:

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Procuring Entity: **Ministry of Health**
- Financial year: **2027/28**
- Plan: **PLN-MOH-2027-001**
- Current Approved Version: **Version 1**
- Editable Version: **Draft Version 2**
- Draft created: **19 August 2027, 09:00 EAT**
- As at: **20 August 2027, 10:00 EAT**

Header:

- Breadcrumb: **Procurement Planning / Ministry of Health Annual Procurement Plan 2027/28**
- Title: **Ministry of Health Annual Procurement Plan 2027/28**
- Quiet reference: **PLN-MOH-2027-001**
- Status line: **Open Plan · Draft Version 2**
- Supporting line: **Approved Version 1 remains active while this update is prepared and reviewed.**
- Button: **Add approved Demands**

Compact summary strip:

1. **Draft Plan Items** — 2
2. **Draft planned value** — KES 535,000,000
3. **Net change** — KES 80,000,000 added
4. **Planning complete** — 2 of 2
5. **Finance confirmed** — 1 of 2
6. **Validation** — Needs attention

Section: **Update reason**

- Multiline field label: **Reason for Plan update**
- Field value: **Add the approved digital-health technical staff certification programme to the FY 2027/28 Plan so delivery can begin before 31 December 2027.**
- Helper text: **Explain why the Approved Plan needs to change.**

Show one restrained issue:

**Funding confirmation is still required for PPI-MOH-2027-022 before this Plan can be submitted for review.**

Section: **Plan Items requiring action**

Use the existing PLN-UI-05 columns:

- Plan Item
- Organisation Unit
- Planned value
- Planning
- Finance
- Validation
- Action

Show exactly one actionable row:

- **PPI-MOH-2027-022 · Digital health technical staff certification programme**
- **Human Resources Management and Development**
- **KES 80,000,000**
- **Complete**
- **Awaiting confirmation**
- **Needs attention**
- Text link **View Plan Item** and restrained overflow action **Remove from draft**

Below the table show one compact read-only line:

**1 unchanged Active Plan Item remains operational in Approved Version 1 · Tender TND-MOH-2027-008 remains active**

Text link: **View Approved Plan**

Bottom action bar:

- Secondary button: **Back to Procurement Planning**
- Primary button: **Save draft**

Do not show Submit for review, Cancel update, full Approved-Version rows, raw diffs, Finance decisions, professional approval controls, Departmental/OU/HoD planning sign-off, Plan publication or Tender configuration.

#### PLN-UI-05 — successor Draft ready for review

Design the same PLN-UI-05 Plan builder with the same Plan, Versions, reason, values and item identity.

Use only this later state:

- As at: **20 August 2027, 10:20 EAT**
- Finance confirmed: **2 of 2**
- Validation: **Ready**

Replace the issue with:

**All required Planning validation and Finance confirmations are ready.**

Show the same actionable row with:

- Planning: **Complete**
- Finance: **Confirmed**
- Validation: **Ready**
- Action: text link **View Plan Item** and restrained overflow action **Remove from draft**

Bottom action bar:

- Secondary button: **Back to Procurement Planning**
- Secondary button: **Save draft**
- Primary button: **Submit for review**

Do not show a submission result, review task, Head-of-Procurement controls, Plan publication or Tender configuration.

### C. Implementation delta

#### Retire PLN-UI-10

- delete the PLN-UI-10 route, screen/component, projection, navigation entry, prompt, tests and seed-specific identifiers;
- do not retain an alias or redirect whose continued use conceals stale callers;
- update route and integration tests so any direct legacy PLN-UI-10 URL returns the normal not-found outcome;
- remove PLN-UI-10 from the screen inventory and cross-screen journey.

#### Extend the ordinary Plan builder

- render PLN-UI-03 only for a zero-item initial Draft;
- render PLN-UI-05 for every populated editable Draft;
- when no Approved predecessor exists, use the already approved initial-Draft projection;
- when an Approved predecessor exists, return predecessor identity, Draft identity, approved/Draft totals, net change, one update reason, effective changed-item rows and compact unchanged-operational context;
- derive the variant from authoritative Plan/Version state rather than a client route flag;
- keep one loader and readiness service for both Draft types and avoid parallel status calculations.

#### Update existing routes

- PLN-UI-01 **Continue planning** opens the ordinary Plan-builder route and resolves PLN-UI-03 or PLN-UI-05 from live state;
- PLN-UI-04 successful single/combined formation opens PLN-UI-06; successful separate formation with multiple resulting items opens PLN-UI-05;
- PLN-UI-06 Save/return opens PLN-UI-05 for any populated Draft;
- PLN-UI-07 successful Finance confirmation and Finance return use PLN-UI-05 as the planner return destination without exposing the protected Finance task to the planner;
- PLN-UI-08 successful approval opens PLN-UI-09; Return to planner makes the successor editable and the planner resumes it through PLN-UI-05;
- PLN-UI-09 **Add Plan Item** still opens PLN-UI-04 without mutation; after confirmed formation the editing journey resolves through PLN-UI-06 and PLN-UI-05.

#### Readiness, submission and preservation

- save the successor update reason using optimistic concurrency and idempotency;
- calculate builder totals, effective changes, Planning completeness, Finance freshness and validation from authoritative records;
- omit submission while any readiness condition fails; expose the approved submit command only in the Ready state;
- submit through PLN-CHG-011 and create/reuse exactly one professional-review task;
- preserve Approved Version 1, PPI-MOH-2027-021, RSV-MOH-0001 and TND-MOH-2027-008 throughout Draft editing and review;
- create no Tender, publication/disclosure record, second HoD decision or duplicate Finance reservation.

#### Focused redevelopment tests

1. Existing PLN-UI-03 zero-item initial Draft remains unchanged.
2. Existing PLN-UI-05 initial-Draft state remains unchanged.
3. Post-approval Draft successor renders through PLN-UI-05, never PLN-UI-10.
4. Exact awaiting-Finance and Ready successor projections.
5. All prior UI-10 entry points now resolve through the ordinary builder route.
6. Legacy UI-10 route is absent and stale callers fail visibly.
7. One readiness calculation drives initial and successor Drafts.
8. Finance confirmation returns the planner to the Ready PLN-UI-05 state.
9. Submit creates one review task and preserves the Approved predecessor/Tender.
10. Role/scope denial remains separate from neutral Plan visibility.
11. Refresh/back and repeated routing create no Draft, item, task or audit mutation.
12. No Plan-publication/disclosure or unauthorised Tender action exists.

### D. Demo seed delta

No new permanent or scenario-owned record is required.

Reuse the approved SCN-PLN-ADD-001 boundaries:

- at **20 August 2027, 10:00 EAT**, render the successor through PLN-UI-05 with Version 1 Approved, Version 2 Draft, KES 535,000,000 total, PPI-MOH-2027-022 Planning complete and Finance Awaiting confirmation;
- at **20 August 2027, 10:20 EAT**, render the same PLN-UI-05 after the 10:15 Finance confirmation with exactly one RSV-MOH-0002, Finance 2 of 2 and validation Ready;
- at **20 August 2027, 10:30 EAT**, submit from PLN-UI-05 into the existing PLN-CHG-011 review boundary.

Remove every PLN-UI-10 screen expectation from seed verification and journey scripts. No database record uses a screen identifier, so no domain-data migration is required.

### E. Acceptance evidence

PLN-CHG-014 is complete only when:

1. PLN-UI-10 is absent from requirements, Stitch inventory, implementation routes, tests, journey diagrams and seed assertions.
2. PLN-UI-05 supports both populated initial Drafts and populated Draft successors without duplicating Plan-builder logic.
3. Existing PLN-UI-03 and initial PLN-UI-05 behavior remains intact.
4. All post-addition, post-item-edit, post-Finance-return and post-Finance-confirmation routes return to the ordinary builder.
5. Successor context is concise: predecessor, Draft, net change, update reason, changed items and unchanged-operational notice.
6. Submission occurs from PLN-UI-05 only when the entire Draft is ready and routes to the existing PLN-UI-08 professional review.
7. The Approved predecessor and its Tender remain operational until successor approval.
8. No additional workflow, approval, persistent screen state or seed record is introduced.

### F. Open decisions

None. PLN-UI-10 is retired and PLN-CHG-013 is superseded.

---

## PLN-CHG-015 — Procurement Planning workspace deferred state variants PLN-UI-01A–F

**Status:** Approved  
**Approved:** 15 August 2026  
**Source:** Approved PLN-CHG-001, PLN-CHG-002, PLN-CHG-004, PLN-CHG-005, PLN-CHG-009, PLN-CHG-011, PLN-CHG-012 and PLN-CHG-014  
**Problem:** PLN-CHG-001 approved the operational workspace and one exact PLN-UI-01 reference frame, but deferred six materially different workspace states. Without exact state selection, data, copy and actions, the implementation can show the wrong primary action, expose another actor's task or leave the workspace sparse. Stitch would also have to infer missing records and presentation.

### Locked design boundary

PLN-UI-01 and PLN-UI-01A–F are mutually exclusive projections of one Procurement Planning workspace route. They are not separate workflows or persisted screen states.

The approved base PLN-UI-01 remains the reference state for an Approved Plan with no open Draft and one Approved Demand ready for Planning. The six variants cover the remaining workspace states:

| Variant | Governed state | Primary action |
|---|---|---|
| `PLN-UI-01A` | No logical annual Plan for the selected authorised PE/FY | **Create annual plan** |
| `PLN-UI-01B` | Initial Draft Version 1 exists and has no Plan Items | **Continue planning** |
| `PLN-UI-01C` | Current Approved Version plus an editable Draft successor with planner-action work | **Continue plan update** |
| `PLN-UI-01D` | Draft successor has no planner-action work and is awaiting Finance confirmation | **View plan update** |
| `PLN-UI-01E` | Draft successor is submitted and awaiting Head-of-Procurement review | **View approved plan** |
| `PLN-UI-01F` | Current Approved Plan has no open Draft, actionable work or waiting work | **View approved plan** |

The workspace may explain that work is with Finance or the Head of Procurement, but it shall never link the Procurement Planner to PLN-UI-07 or PLN-UI-08. The planner may view the current Approved Plan through PLN-UI-09 and may view an editable Draft through the ordinary PLN-UI-03/05 Plan-builder route. The submitted Version in PLN-UI-01E remains represented as neutral waiting context; the planner receives no professional-review form or decision action.

### A. Requirements delta

**Add the following after approved §9.1 and treat these rules as the authoritative workspace-state selection contract.**

#### 9.1.1 Workspace state resolution

| ID | Requirement |
|---|---|
| `PLN-FR-009A` | For the explicitly selected authorised PE/FY, the system shall derive one workspace state from authoritative Plan, Version, Plan Item, Demand, Finance-task and professional-review records. The client shall not select a variant or infer it from display labels. |
| `PLN-FR-009B` | The state precedence shall be: no logical Plan → PLN-UI-01A; initial zero-item Draft → PLN-UI-01B; submitted Version awaiting professional review → PLN-UI-01E; open Draft with any planner-action work → PLN-UI-01C; open Draft with no planner-action work and one or more Finance confirmations outstanding → PLN-UI-01D; Approved Plan with eligible Approved Demand work → base PLN-UI-01; Approved Plan with no actionable or waiting work → PLN-UI-01F. |
| `PLN-FR-009C` | A returned Finance task, returned professional review, incomplete Proposed Plan Item, planner-remediable validation issue or editable Draft with another outstanding planner correction shall resolve to PLN-UI-01C, not to a waiting state. If several Plan Items are at different stages, any planner-action work takes precedence while other actors' work remains visible only in **Waiting on others**. |
| `PLN-FR-009D` | PLN-UI-01A shall show that no annual Plan exists, the count of Approved Demands that will be eligible after registration and one **Create annual plan** action. Approved Demands shall not appear as actionable rows until the annual Plan exists. |
| `PLN-FR-009E` | PLN-UI-01B shall show the initial Draft identity, zero Plan Items, KES 0 Draft value, eligible Approved Demand count and Not run validation. **Continue planning** shall open the same Draft in PLN-UI-03; opening the workspace shall not create or change the Plan. |
| `PLN-FR-009F` | PLN-UI-01C shall show both the current Approved predecessor and open Draft successor, approved and Draft values, net change, the highest-priority planner-action row and any separate neutral waiting rows. **Continue plan update** shall open the current Draft on the ordinary PLN-UI-05 route. |
| `PLN-FR-009G` | PLN-UI-01D shall show the current Approved predecessor, open Draft successor, Draft value, Finance progress, validation state and one neutral waiting row for each outstanding Finance confirmation. It shall not expose a Finance decision action or route. **View plan update** shall open the exact approved PLN-UI-05 awaiting-Finance state; that builder may retain its permitted Draft update-reason save action but shall expose no Finance decision control. |
| `PLN-FR-009H` | PLN-UI-01E shall show that the submitted Draft successor is awaiting Head-of-Procurement review and that the current Approved predecessor remains operational. It shall not expose the professional task, PLN-UI-08 or any Approve/Return action. The only header action shall be **View approved plan**, opening PLN-UI-09. |
| `PLN-FR-009I` | PLN-UI-01F shall show the current Approved Plan and exact empty messages for both work sections. It shall not show **Add Plan Item** or open PLN-UI-04 when no eligible Approved Demand exists. **View approved plan** shall open PLN-UI-09. |
| `PLN-FR-009J` | **Work requiring action** rows shall contain exactly one authorised specific action. **Waiting on others** rows are informational and shall contain no row action unless a separately approved neutral view exists. A disabled decision control shall not be used as a substitute for authorization. |
| `PLN-FR-009K` | Counts, totals, Finance progress, validation, eligible-Demand count and queue membership shall be calculated from one consistent as-at projection and shall reconcile with PLN-UI-03/05, PLN-UI-07, PLN-UI-08 and PLN-UI-09 at the same scenario boundary. |
| `PLN-FR-009L` | Opening, refreshing, changing the selected financial year or returning to any workspace variant shall perform no domain mutation, create no task, Version, reservation or audit decision and shall not change the selected record's workflow state. |

**Consequential correction to approved PLN-CHG-001:**

- Replace its blanket requirement that every workspace row has an action with `PLN-FR-009J`: actionable rows have one action; waiting rows are informational unless an approved neutral target exists.
- Extend the permitted primary-action vocabulary with **View plan update** for a Draft whose next decision belongs to Finance.
- Keep all Finance and Head-of-Procurement decision surfaces route-protected and absent for the Procurement Planner.

### B. Stitch delta

Each prompt below is one static desktop reference frame. Stitch shall preserve the existing Procurement navigation, top bar, branding and the same workspace layout established for PLN-UI-01. Stitch shall not design transitions, busy states, permissions, hidden states, alternate data or controls not explicitly listed.

Across all six frames:

- title: **Procurement Planning**;
- description: **“Turn approved needs into funded, approved Plan Items ready for tendering.”**;
- visible read-only Procuring Entity: **Ministry of Health**;
- helper text below PE/FY context: **“These controls define the workspace view; they do not change record ownership.”**;
- use one compact **Current Plan** panel, never a KPI-card grid;
- use business titles as primary text and references as quiet secondary text;
- do not add charts, trends, activity feeds, generic Review buttons, contribution workbenches, another actor's task controls or disabled unauthorised actions.

#### PLN-UI-01A — no annual Plan

Design the Procurement Planning workspace using only this exact state:

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Procuring Entity: **Ministry of Health**
- Financial year selected: **2028/29**
- Logical Plan: **None**
- Approved Demands that will be eligible after Plan creation: **2**

Header context:

- Financial year select: **2028/29**
- Primary button: **Create annual plan**

Current Plan panel:

- Heading: **Current Plan**
- Empty-state heading: **No annual Procurement Plan**
- Text: **“No Procurement Plan has been registered for Ministry of Health for FY 2028/29.”**
- Supporting text: **“Create the annual Plan before adding the 2 Approved Demands ready for Planning.”**

Section **Work requiring action**:

- Do not render filters or a table.
- Text: **“Create the annual Plan to begin Planning approved requirements.”**

Section **Waiting on others**:

- Text: **“Nothing is currently waiting on another reviewer.”**

Do not show a Plan title, Plan reference, Version, Plan value, validation, Finance progress, Demand rows, **Add to plan**, **Continue planning** or **View approved plan**.

#### PLN-UI-01B — initial Draft Plan

Design the Procurement Planning workspace using only this exact post-registration state:

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Procuring Entity: **Ministry of Health**
- Financial year selected: **2028/29**
- Plan title: **Ministry of Health Annual Procurement Plan 2028/29**
- Logical Plan reference: **PLN-MOH-2028-001**
- Plan lifecycle: **Open**
- Draft Version: **Version 1**
- Draft Version reference: **PLN-MOH-2028-001-V1**
- Plan Items: **0**
- Draft planned value: **KES 0**
- Approved Demands available: **2**
- Validation: **Not run**

Header context:

- Financial year select: **2028/29**
- Primary button: **Continue planning**

Current Plan panel:

- Plan title: **Ministry of Health Annual Procurement Plan 2028/29**
- Quiet reference: **PLN-MOH-2028-001**
- Status line: **Open Plan · Draft Version 1**
- Supporting text: **“The annual Plan is ready for its first Approved Demands.”**
- Summary values, in this order:
  - **Plan Items:** 0
  - **Draft planned value:** KES 0
  - **Approved Demands available:** 2
  - **Validation:** Not run

Section **Work requiring action**:

- Use the same compact table style as base PLN-UI-01 with columns: Work item, Type, Organisation Unit, Amount, Why it needs action, Status, Action.
- Show exactly two rows:
  1. **Clinical training laptops for digital health rollout**
     - Quiet reference: **DMD-MOH-2028-001**
     - Type: **Approved Demand**
     - Organisation Unit: **Human Resources Management and Development**
     - Amount: **KES 48,000,000**
     - Why it needs action: **Approved Demand is ready to add to the FY 2028/29 Plan.**
     - Status: **Ready for planning**
     - Action: **Add to plan**
  2. **Clinical deployment laptops for digital health rollout**
     - Quiet reference: **DMD-MOH-2028-002**
     - Type: **Approved Demand**
     - Organisation Unit: **Directorate of Digital Health and Policy**
     - Amount: **KES 72,000,000**
     - Why it needs action: **Approved Demand is ready to add to the FY 2028/29 Plan.**
     - Status: **Ready for planning**
     - Action: **Add to plan**

Section **Waiting on others**:

- Text: **“Nothing is currently waiting on another reviewer.”**

Do not show an Approved Version, Finance progress, **View approved plan**, submission controls or a second Draft action.

#### PLN-UI-01C — Approved Plan with open Draft successor and planner-action work

Design the Procurement Planning workspace using only this exact state:

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Procuring Entity: **Ministry of Health**
- Financial year selected: **2027/28**
- Plan title: **Ministry of Health Annual Procurement Plan 2027/28**
- Logical Plan reference: **PLN-MOH-2027-001**
- Plan lifecycle: **Open**
- Current Approved Version: **Version 1**
- Approved Version reference: **PLN-MOH-2027-001-V1**
- Approved planned value: **KES 455,000,000**
- Open Draft successor: **Version 2**
- Draft Version reference: **PLN-MOH-2027-001-V2**
- Draft created: **19 August 2027, 09:00 EAT**
- As at: **19 August 2027, 09:05 EAT**
- Draft Plan Items: **2**
- Draft planned value: **KES 535,000,000**
- Net change: **KES 80,000,000 added**
- Planning complete: **1 of 2**
- Finance confirmed: **1 of 2**
- Validation: **Needs attention**

Header context:

- Financial year select: **2027/28**
- Primary button: **Continue plan update**

Current Plan panel:

- Plan title: **Ministry of Health Annual Procurement Plan 2027/28**
- Quiet reference: **PLN-MOH-2027-001**
- Status line: **Open Plan · Approved Version 1 · Draft Version 2**
- Supporting text: **“Approved Version 1 remains active while Draft Version 2 is prepared.”**
- Summary values, in this order:
  - **Approved value:** KES 455,000,000
  - **Draft value:** KES 535,000,000
  - **Net change:** KES 80,000,000 added
  - **Planning complete:** 1 of 2
  - **Finance confirmed:** 1 of 2
  - **Validation:** Needs attention

Section **Work requiring action**:

- Use the standard compact table columns.
- Show exactly one row:
  - Work item: **Digital health technical staff certification programme**
  - Quiet reference: **PPI-MOH-2027-022**
  - Type: **Plan Item**
  - Organisation Unit: **Human Resources Management and Development**
  - Amount: **KES 80,000,000**
  - Why it needs action: **Complete the procurement method and schedule before requesting Finance confirmation.**
  - Status: **Planning incomplete**
  - Action: **Complete item**

Section **Waiting on others**:

- Text: **“Nothing is currently waiting on another reviewer.”**

Do not show Finance task controls, professional-review controls, submission, the full Approved Plan Item table or raw Version diffs.

#### PLN-UI-01D — work awaiting Finance confirmation

Design the Procurement Planning workspace using only this exact state:

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Procuring Entity: **Ministry of Health**
- Financial year selected: **2027/28**
- Plan title: **Ministry of Health Annual Procurement Plan 2027/28**
- Logical Plan reference: **PLN-MOH-2027-001**
- Current Approved Version: **Version 1**
- Open Draft successor: **Version 2**
- As at: **20 August 2027, 10:00 EAT**
- Draft Plan Items: **2**
- Draft planned value: **KES 535,000,000**
- Net change: **KES 80,000,000 added**
- Planning complete: **2 of 2**
- Finance confirmed: **1 of 2**
- Validation: **Needs attention**

Header context:

- Financial year select: **2027/28**
- Primary button: **View plan update**

Current Plan panel:

- Plan title: **Ministry of Health Annual Procurement Plan 2027/28**
- Quiet reference: **PLN-MOH-2027-001**
- Status line: **Open Plan · Approved Version 1 · Draft Version 2**
- Supporting text: **“Approved Version 1 remains active while Finance reviews the added Plan Item.”**
- Summary values, in this order:
  - **Draft Plan Items:** 2
  - **Draft planned value:** KES 535,000,000
  - **Net change:** KES 80,000,000 added
  - **Planning complete:** 2 of 2
  - **Finance confirmed:** 1 of 2
  - **Validation:** Needs attention

Section **Work requiring action**:

- Do not render filters or a table.
- Text: **“No planning work currently needs your action.”**

Section **Waiting on others**:

- Use a compact table with columns: Work item, Stage, Status, With.
- Show exactly one row:
  - Work item: **Digital health technical staff certification programme**
  - Quiet reference: **PPI-MOH-2027-022**
  - Stage: **Finance confirmation**
  - Status: **Awaiting confirmation**
  - With: **Budget Officer**

Do not add a row action, Finance form link, Confirm, Return, disabled control, Budget allocation arithmetic or **Submit for review**.

#### PLN-UI-01E — work awaiting Head-of-Procurement review

Design the Procurement Planning workspace using only this exact state:

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Procuring Entity: **Ministry of Health**
- Financial year selected: **2027/28**
- Plan title: **Ministry of Health Annual Procurement Plan 2027/28**
- Logical Plan reference: **PLN-MOH-2027-001**
- Current Approved Version: **Version 1**
- Submitted successor: **Version 2**
- Submitted Version reference: **PLN-MOH-2027-001-V2**
- Version state: **In review**
- Submitted at: **20 August 2027, 10:30 EAT**
- Submitted by: **Mercy Kilonzo**
- Submitted planned value: **KES 535,000,000**
- Net change: **KES 80,000,000 added**
- Finance confirmed: **2 of 2**
- Validation: **Ready**

Header context:

- Financial year select: **2027/28**
- Primary button: **View approved plan**

Current Plan panel:

- Plan title: **Ministry of Health Annual Procurement Plan 2027/28**
- Quiet reference: **PLN-MOH-2027-001**
- Status line: **Open Plan · Approved Version 1 · Version 2 in review**
- Supporting text: **“Approved Version 1 remains active while Version 2 awaits Head-of-Procurement review.”**
- Summary values, in this order:
  - **Submitted value:** KES 535,000,000
  - **Net change:** KES 80,000,000 added
  - **Finance confirmed:** 2 of 2
  - **Validation:** Ready

Section **Work requiring action**:

- Do not render filters or a table.
- Text: **“No planning work currently needs your action.”**

Section **Waiting on others**:

- Use a compact table with columns: Work item, Stage, Status, With.
- Show exactly one row:
  - Work item: **Ministry of Health Annual Procurement Plan 2027/28 — Version 2**
  - Quiet reference: **PLN-MOH-2027-001-V2**
  - Stage: **Professional review**
  - Status: **Awaiting review**
  - With: **Head of Procurement**

Do not add a row action, PLN-UI-08 link, Approve, Return, disabled decision control, editable Draft field or Tender action.

#### PLN-UI-01F — no actionable or waiting work

Design the Procurement Planning workspace using only this exact post-approval state:

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Procuring Entity: **Ministry of Health**
- Financial year selected: **2027/28**
- Plan title: **Ministry of Health Annual Procurement Plan 2027/28**
- Logical Plan reference: **PLN-MOH-2027-001**
- Plan lifecycle: **Open**
- Current Approved Version: **Version 2**
- Approved Version reference: **PLN-MOH-2027-001-V2**
- Approved at: **20 August 2027, 11:00 EAT**
- As at: **20 August 2027, 11:05 EAT**
- Open Draft successor: **None**
- Active Plan Items: **2**
- Approved planned value: **KES 535,000,000**
- Finance confirmed: **2 of 2**
- Validation: **Ready**
- Eligible Approved Demands: **0**

Header context:

- Financial year select: **2027/28**
- Primary button: **View approved plan**

Current Plan panel:

- Plan title: **Ministry of Health Annual Procurement Plan 2027/28**
- Quiet reference: **PLN-MOH-2027-001**
- Status line: **Open Plan · Approved Version 2**
- Supporting text: **“No plan update is currently in progress.”**
- Summary values, in this order:
  - **Plan Items:** 2 active
  - **Approved value:** KES 535,000,000
  - **Finance confirmed:** 2 of 2
  - **Validation:** Ready

Section **Work requiring action**:

- Do not render filters or a table.
- Text: **“No planning work currently needs your action.”**

Section **Waiting on others**:

- Do not render a table.
- Text: **“Nothing is currently waiting on another reviewer.”**

Do not show **Add Plan Item**, **Add to plan**, a Demand row, Draft Version, Tender take-up, Plan publication or Tender preparation action.

### C. Implementation delta

Extend the approved PLN-UI-01 implementation as one server-derived workspace projection.

#### Projection contract

Return one `workspace_state` enum with only:

- `NO_PLAN` → PLN-UI-01A;
- `INITIAL_DRAFT_EMPTY` → PLN-UI-01B;
- `APPROVED_WITH_ACTIONABLE_WORK` → base PLN-UI-01;
- `DRAFT_WITH_PLANNER_ACTION` → PLN-UI-01C;
- `DRAFT_AWAITING_FINANCE` → PLN-UI-01D;
- `VERSION_AWAITING_PROFESSIONAL_REVIEW` → PLN-UI-01E; and
- `APPROVED_NO_WORK` → PLN-UI-01F.

The response shall include:

- selected authorised PE/FY context and available financial-year options;
- logical Plan and current Approved/open Draft/submitted Version identities applicable to that state;
- summary values applicable to that state;
- one server-authorised primary action or no action;
- ordered `work_requiring_action` rows;
- ordered informational `waiting_on_others` rows;
- one consistent `as_at` value and projection version/token.

Do not persist `workspace_state`, variant identifiers, queue rows, counters or empty-state flags.

#### State algorithm

Within one consistent read boundary:

1. Resolve the explicitly selected PE/FY and current user's Planning capability.
2. If no logical Plan exists, return `NO_PLAN`.
3. If the only open Version is initial Draft Version 1 with zero effective Plan Items, return `INITIAL_DRAFT_EMPTY`.
4. If the successor Version is In review with an open professional-review task, return `VERSION_AWAITING_PROFESSIONAL_REVIEW`.
5. Derive planner-action rows from incomplete items, Finance returns, professional returns, planner-remediable validation and other editable Draft corrections. If at least one exists, return `DRAFT_WITH_PLANNER_ACTION`.
6. If an open Draft has no planner-action row and at least one open Finance task, return `DRAFT_AWAITING_FINANCE`.
7. If no open Draft exists and at least one Approved Demand is eligible for Planning, return `APPROVED_WITH_ACTIONABLE_WORK`.
8. Otherwise, return `APPROVED_NO_WORK`.

For mixed Draft work, return PLN-UI-01C and include its planner-action rows plus informational Finance-waiting rows. Deduplicate each source record and retain only its highest-priority actionable reason.

#### Actions and authorization

- `NO_PLAN`: return **Create annual plan** only with create-plan capability; route to PLN-UI-02.
- `INITIAL_DRAFT_EMPTY`: return **Continue planning**; route to the ordinary Plan-builder, which resolves PLN-UI-03.
- `APPROVED_WITH_ACTIONABLE_WORK`: return **View approved plan** in the header and the specific **Add to plan** Demand-row action; route to PLN-UI-09 and PLN-UI-04 respectively.
- `DRAFT_WITH_PLANNER_ACTION`: return **Continue plan update** and one specific action per actionable row; route to PLN-UI-05 or PLN-UI-06 as appropriate.
- `DRAFT_AWAITING_FINANCE`: return **View plan update**; route to the exact approved PLN-UI-05 awaiting-Finance projection. Return no Finance task URL or decision action; retain only the Draft controls already authorised in that approved builder state.
- `VERSION_AWAITING_PROFESSIONAL_REVIEW`: return **View approved plan** only; route to PLN-UI-09. Return no PLN-UI-08 URL or submitted-Version decision action.
- `APPROVED_NO_WORK`: return **View approved plan** only; route to PLN-UI-09.

Every target service shall re-evaluate capability, PE/FY scope, record state and assignment. A hidden or omitted client action is not authorization. Administrator status without operational assignment shall confer neither planner actions nor protected Finance/review task access.

#### Data and behavior

- Use the same Demand eligibility predicate as PLN-UI-04 and PLN-UI-03.
- Use the same effective-Draft, Finance-freshness and validation predicates as PLN-UI-05.
- Use the same current Approved-Version and Active-item predicates as PLN-UI-09.
- Waiting rows shall disclose only business work, stage, neutral status and responsible role. Do not disclose protected decision-form payloads, comments or actions.
- Do not create a neutral submitted-Version screen solely for PLN-UI-01E in MVP. The planner continues to view the operational Approved predecessor until the decision completes or the successor is returned.
- Preserve the selected FY in the URL or governed user workspace preference. When absent, apply the approved financial-year defaulting rule; do not persist a variant choice.
- Loading, empty and error states shall be accessible and shall not flash an unauthorised action before the server projection resolves.
- Refresh, browser back/forward and repeated loader calls shall be read-only and idempotent.

#### Focused tests

1. Exact state selection and exact primary action for all seven workspace states, including the base PLN-UI-01 state.
2. Precedence when planner-action and Finance-waiting work coexist.
3. Finance-return and professional-return resolving to PLN-UI-01C.
4. Exact PLN-UI-01A–F data, copy, rows and totals at their deterministic seed boundaries.
5. PLN-UI-01D exposes no PLN-UI-07 route, allocation decision or Finance comment.
6. PLN-UI-01E exposes no PLN-UI-08 route, submitted-Version decision or approval control.
7. PLN-UI-01F exposes no unusable Add action when eligible Approved Demand count is zero.
8. Reconciliation with PLN-UI-03/05/07/08/09 at the same `as_at` boundary.
9. PE/FY, role, assignment and direct-route authorization, including cross-PE and Administrator-without-assignment denial.
10. Refresh, re-entry and financial-year changes create no Plan, Version, item, task, reservation, decision or audit mutation.
11. Bounded projection/query behavior without per-row queries or persisted counters.
12. Keyboard navigation, screen-reader labels, responsive tables and purposeful loading/failure states.

### D. Demo seed and scenario delta

No new permanent record is required. Use resettable scenario boundaries and existing approved identities.

| Variant | Exact seed boundary | Required assertions |
|---|---|---|
| `PLN-UI-01A` | Isolated Ministry of Health FY2028/29 pre-registration boundary from PLN-CHG-002 | No logical Plan; exactly two isolated Approved Demands will be eligible after registration; no workspace load creates the Plan. |
| `PLN-UI-01B` | Same isolated transaction immediately after production registration and before source selection | `PLN-MOH-2028-001`; Draft `PLN-MOH-2028-001-V1`; zero items; KES 0; two exact eligible Approved Demands; validation Not run. |
| `PLN-UI-01C` | `SCN-PLN-ADD-001` at 19 August 2027, 09:05 EAT after formation of `PPI-MOH-2027-022` and before completion | Version 1 remains current Approved; Version 2 Draft; KES 535,000,000; `PPI-MOH-2027-022` Planning incomplete; one **Complete item** row; no Finance task yet. |
| `PLN-UI-01D` | Existing PLN-CHG-009 pre-confirmation boundary at 20 August 2027, 10:00 EAT | `PPI-MOH-2027-022` Planning complete; exactly one open Finance task; no `RSV-MOH-0002`; Finance 1 of 2; one informational Finance waiting row. |
| `PLN-UI-01E` | Existing PLN-CHG-011 submitted boundary at 20 August 2027, 10:30 EAT | Version 2 In review; exactly one professional-review task for the Head of Procurement; Version 1 remains current Approved; Finance 2 of 2; no planner decision action. |
| `PLN-UI-01F` | Existing PLN-CHG-012 post-approval boundary at 20 August 2027, 11:05 EAT, with no additional eligible Approved Demand in this resettable projection | Version 2 current Approved; Version 1 Superseded; two Active items; KES 535,000,000; Finance 2 of 2; no Draft, actionable row or waiting row. |

The FY2028/29 fixture shall use the exact `DMD-MOH-2028-001` and `DMD-MOH-2028-002` records approved in PLN-CHG-005 and shall reset the Plan, Version, Demands and related allocations. The FY2027/28 boundaries shall reuse `SCN-PLN-ADD-001`; repeated preparation shall not duplicate Version 2, `PPI-MOH-2027-022`, Finance tasks, `RSV-MOH-0002`, review tasks or decisions.

The PLN-UI-01F fixture may suppress unrelated later test Demands only by resetting to its declared scenario boundary. It shall not change an Approved Demand's state or introduce a stored `no_work` flag to force the screen.

### E. Acceptance evidence

`PLN-CHG-015` may be marked implemented only when:

1. Each of PLN-UI-01A–F renders from exact authoritative data without a client-supplied variant flag.
2. The seven-state precedence is deterministic and covers mixed planner/Finance work.
3. Every frame has one correct header action and no competing, disabled or unauthorised decision action.
4. PLN-UI-01D and PLN-UI-01E communicate waiting ownership without exposing protected task surfaces.
5. PLN-UI-01F contains no false **Add Plan Item** path when nothing is eligible.
6. All totals and statuses reconcile with the owning planning, Finance, review and Approved Plan screens.
7. Workspace loading and navigation are mutation-free.
8. Seed preparation is resettable, introduces no permanent screen-state record and leaves the canonical successful journey unchanged.

### F. Open decisions

None proposed. This record completes the workspace variant family without introducing a new workflow, task type, screen route or persistent status.

---

## PLN-CHG-016 — Financial-year context, Demand eligibility and lifecycle-state closure

**Status:** Approved  
**Approved:** 15 August 2026  
**Source:** Approved Procurement Planning operating decisions, PLN-CHG-002, PLN-CHG-005, PLN-CHG-007, PLN-CHG-014, PLN-CHG-015 and closure findings `CL-01`/`CL-02`  
**Problem:** The approved workspace requires an explicit PE/FY context and refers to an approved financial-year defaulting rule, but the rule is not yet authoritative. Demand eligibility also requires the Plan PE/FY without defining how an Approved Demand is assigned to a financial year. Separately, the inherited state model contains Logical Plan **Closed** and **Cancelled** states with no admitted MVP operation, while an empty Draft successor needs one governed cancellation outcome. Leaving these gaps encourages silent defaults, duplicate FY fields and unreachable lifecycle states.

### Locked design boundary

1. A user's explicit authorised context controls. Saved context is a convenience, never authority.
2. A Demand maps to one Plan financial year from its approved required-by date and the governed, non-overlapping financial-year period. Planning does not add an editable Demand financial-year field.
3. Future financial years that are configured and open for Planning remain selectable even when another year already has a Plan.
4. The Logical Plan has one MVP lifecycle state: **Open**. No unsupported close/cancel workflow is introduced.
5. **Cancelled** is retained only as an immutable Plan Version outcome when an empty Draft successor to an Approved Version is deliberately cancelled.
6. Cancelling an empty successor is cleanup of an ineffective Draft, not another approval or a cancellation of the annual Plan. It requires one compact confirmation and no extra business-reason field.

### A. Requirements

#### A.1 Explicit and default workspace context

| ID | Requirement |
|---|---|
| `PLN-FR-009M` | Every Planning request shall resolve the current user's authorised PE and configured financial-year context server-side. An explicit valid PE/FY route context shall apply to that request. It shall not become a saved preference unless the user deliberately selects or confirms it through the workspace context control. |
| `PLN-FR-009N` | When no explicit context is supplied, the workspace shall restore the user's last deliberately saved PE/FY only when the user still has Planning visibility for the PE and the financial year remains configured and available for Planning or contains a permitted existing Plan. A stale, disabled or unauthorised saved context shall be ignored without granting access. |
| `PLN-FR-009O` | If no valid explicit or saved PE exists, one eligible PE shall remain visibly selected and multiple eligible PEs shall require deliberate selection. Assignment order, alphabetical order, Administrator status, seed identity and list-filter state shall not select a PE. Zero eligible PEs shall block operational use with a clear explanation. |
| `PLN-FR-009P` | After a PE is resolved and no valid explicit or saved FY exists, the system shall select a configured FY by this order: (1) the FY containing the current date when it has an Open Plan; (2) the nearest future FY with an Open Plan; (3) the most recent past FY with an Open Plan; (4) the FY containing the current date when it is enabled for Planning even though no Plan exists. If none applies, the user shall deliberately choose from configured FYs that are open for Planning. |
| `PLN-FR-009Q` | The workspace financial-year control shall include the current enabled FY, configured future FYs whose Planning window is open and prior FYs containing a permitted Open Plan. An existing Plan for one year shall not suppress selection or Plan registration for another year. |
| `PLN-FR-009R` | Changing PE or FY shall reload the workspace from that authorised context without creating or changing a Plan, Version, task, reservation, decision or audit event. A deliberate valid selection may update the user's workspace preference only after successful server validation. |
| `PLN-FR-009S` | Every list, count, total, queue, action, export and direct route shall use the same resolved PE/FY context. Client display labels, cached rows or a saved preference shall never be accepted as mutation authority. |

For FY ordering, **nearest future** means the configured open-for-Planning period with the earliest start date after the current date. **Most recent past** means the eligible period with the latest end date before the current date. Configured financial-year periods shall not overlap.

#### A.2 Demand-to-Plan financial-year eligibility

| ID | Requirement |
|---|---|
| `PLN-FR-020A` | An Approved Demand shall map to the one governed financial-year period whose inclusive start and end dates contain the Demand's approved `required_by_date`. The containing period supplies Planning FY eligibility; the user shall not select or edit a separate Demand financial year in Planning. |
| `PLN-FR-020B` | PLN-UI-04 shall include a Demand only when its required-by-derived FY equals the selected Plan FY and all other approved eligibility conditions remain true. A Demand shall not appear in two Plan years, even when the resulting contract is multi-year. |
| `PLN-FR-020C` | A missing required-by date, a date outside every configured financial-year period or overlapping financial-year configuration shall make the Demand unavailable for Planning and return a stable business-readable issue. Planning shall not guess the year or silently use the current FY. |
| `PLN-FR-020D` | Correcting a Demand's required-by date is an upstream Demand amendment subject to its governed approval. Planning shall not move an allocated source to another FY by editing a Plan Item or allocation. |
| `PLN-FR-020E` | A technical derived/indexed FY key may be maintained for bounded querying only when it is reproducible from the governed required-by date and financial-year periods. It shall not become a user-authored business field or override the source date. |
| `PLN-FR-020F` | The required-by-derived FY controls source eligibility only. The planner's **Single year** or **Multi-year** contract-period decision and contract-completion date remain procurement-owned Plan Item treatment and shall not remap the source Demand to another annual Plan. |

Stable issue identifiers:

| Identifier | User-facing message |
|---|---|
| `DEMAND_REQUIRED_BY_MISSING` | **This Demand has no approved required-by date and cannot be added to a Plan. Amend and reapprove the Demand.** |
| `DEMAND_REQUIRED_BY_OUTSIDE_CONFIGURED_FY` | **The approved required-by date does not fall within a configured Planning financial year.** |
| `FINANCIAL_YEAR_CONFIGURATION_OVERLAP` | **Financial-year configuration overlaps and must be corrected before Planning can continue.** |
| `DEMAND_FINANCIAL_YEAR_MISMATCH` | **This Demand belongs to a different financial year and cannot be added to the selected Plan.** |

**Consequential current-state data correction:** The approved and corrected `DMD-MOH-2027-019` required-by date is **31 December 2027**, as used by PLN-CHG-008 through PLN-CHG-012 and the canonical source record. This later correction supersedes the **31 March 2028** value shown in the earlier PLN-CHG-005 PLN-UI-04 reference row. The current PLN-UI-04 frame, implementation projection and seed assertion shall use **31 December 2027**. The **31 March 2028** date belongs to the separate infrastructure Demand/Plan Item and shall not be copied to `DMD-MOH-2027-019`.

#### A.3 Admitted lifecycle states

| ID | Requirement |
|---|---|
| `PLN-FR-060A` | The Logical Plan shall use **Open** as its only MVP lifecycle state. **Closed** and **Cancelled** shall be removed from the MVP requirements, UI, commands, fixtures and tests until an evidenced Plan-level close/cancel operation is admitted. |
| `PLN-FR-060B` | Plan Version states shall be **Draft**, **In review**, **Returned**, **Approved**, **Superseded** and **Cancelled**. A Cancelled Version shall be immutable and shall not count as the one open Draft successor. |
| `PLN-FR-065C` | **Cancel empty update** shall be available only for a Draft or Returned successor to a current Approved Version when authoritative recalculation finds zero effective additions, changes or proposed removals. It shall not be available for initial Draft Version 1, an In-review Version, a Version with an effective change or a user without update-cancellation capability. |
| `PLN-FR-065D` | Opening the cancellation confirmation shall perform no mutation. Confirmation shall lock and revalidate the logical Plan, current Approved predecessor, successor, effective changes, tasks, Draft holds and reservations. If any effective change, active Finance/review task or residual Draft hold/reservation exists, cancellation shall fail with a stable conflict and preserve the Version. The owning removal/correction command shall resolve that inconsistency; cancellation shall not conceal it. |
| `PLN-FR-065E` | Successful cancellation shall atomically mark only the already-empty successor **Cancelled**, retain all prior decisions and removal evidence, and record actor and time once. It shall not close unrelated work, perform another release, change the Open logical Plan, current Approved Version, Active items, current Approved reservations, Demand approvals or Tender handoffs. |
| `PLN-FR-065F` | Empty-successor cancellation shall not require another business reason. The authoritative audit reason shall be **No effective changes remained in the Draft update.** Existing Plan-update and item-removal reasons shall remain in history and shall not be overwritten. |
| `PLN-FR-065G` | An idempotent repeat shall return the same Cancelled Version result without another event or release. A successful UI action shall open PLN-UI-09 for the unchanged current Approved Version; the restored eligible Demand may then appear in the Planning workspace through the normal live projection. |

Stable cancellation conflicts:

| Identifier | User-facing message |
|---|---|
| `PLAN_UPDATE_NOT_EMPTY` | **This Plan update contains effective changes and cannot be cancelled as empty.** |
| `PLAN_UPDATE_HAS_ACTIVE_TASK` | **This Plan update still has active work. Resolve that work before cancelling the update.** |
| `PLAN_UPDATE_HAS_RESIDUAL_HOLD` | **This Plan update still has a funding or allocation hold that must be resolved before cancellation.** |

### B. Exact static screen design

#### B.1 Workspace context impact

No new PLN-UI-01 variant is required. Approved PLN-UI-01 and PLN-UI-01A–F already show the visible PE/FY context. Their exact frames remain unchanged.

The FY-selection/default rules above are executable behaviour owned by Requirements and Implementation. Stitch shall not be asked to simulate saved context, URL precedence, default selection, authorization changes or persistence.

#### B.2 PLN-UI-05B — cancel empty Plan update confirmation

Design one compact confirmation modal over the dimmed ordinary PLN-UI-05 Plan builder. Preserve the existing Procurement navigation, top bar, Plan header and page density behind the overlay.

Use only this exact resettable state:

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Procuring Entity: **Ministry of Health**
- Financial year: **2027/28**
- Logical Plan: **PLN-MOH-2027-001**
- Logical Plan lifecycle: **Open**
- Current Approved Version: **Version 1**
- Approved value: **KES 455,000,000**
- Draft successor: **Version 2**
- Draft Version reference: **PLN-MOH-2027-001-V2**
- Effective changes: **0**
- Draft planned value: **KES 455,000,000**
- Active Plan Items retained: **1**
- Existing Tender retained: **TND-MOH-2027-008**
- As at: **19 August 2027, 09:15 EAT**

Modal content:

- Title: **Cancel empty Plan update?**
- Text: **“Draft Version 2 no longer contains any changes. Cancelling it will remove the empty Draft from current work and keep Approved Version 1 active.”**

Show one compact summary:

- **Current Approved Version:** Version 1
- **Approved value:** KES 455,000,000
- **Draft Version:** Version 2
- **Effective changes:** 0

Show this restrained information message:

**This does not cancel the annual Plan or affect the Approved Plan Item, its funding or Tender TND-MOH-2027-008.**

Footer buttons:

- Secondary: **Keep draft**
- Destructive confirmation: **Cancel empty update**

Do not show a reason field, deletion language, Plan cancellation, item selection, reservation control, Finance decision, professional approval action, publication or Tender action.

### C. Implementation contract

#### C.1 Context resolver

Implement one shared Planning context resolver used by workspace, Plan, Version, item, Finance/review projection and mutation entry points.

The resolver shall:

- accept optional stable PE/FY identifiers, never labels, from the route;
- load current Planning visibility/capability assignments and configured financial-year periods;
- validate explicit context first, then saved context, then apply the approved PE/FY selection order;
- return `selection_required` rather than choosing among multiple PEs or when no safe FY default exists;
- return `no_scope` when no PE is eligible;
- expose the allowed FY options with stable identifiers, labels, period dates, `planning_open` and permitted Plan presence;
- update saved context only through a deliberate successful context-selection command;
- never use Administrator status, assignment order, seed constants, browser list state or the first query result as a default; and
- apply the same resolved identifiers to rows, counts, actions and target services.

Recommended response shape:

```text
planning_context
  selected_pe_id
  selected_financial_year_id
  selection_source: explicit | saved | current_open_plan | future_open_plan | past_open_plan | current_enabled | user_required
  eligible_pe_options[]
  eligible_financial_year_options[]
  selection_required
  no_scope
```

The response shape is a projection contract, not a new persistent domain record.

#### C.2 Demand FY eligibility

Use the governed financial-year period containing `required_by_date` as an inclusive date-range predicate in PLN-UI-04 eligibility and workspace eligible-Demand counts.

- Validate that configured financial-year periods do not overlap before deriving eligibility.
- Do not accept a client FY, derived FY key or available-value claim as authority.
- Recheck required-by date, source approval, PE, FY and allocation availability under lock during Plan Item formation.
- If the approved date changed after the selection projection, keep the selection surface open, remove the ineligible source and return the stable mismatch issue; create no partial Plan Item.
- If an indexed derived FY key is used, provide a deterministic rebuild and reconciliation test against the date-range predicate.
- Use inclusive boundaries: a required-by date equal to the FY start or FY end belongs to that FY.

#### C.3 Empty-successor cancellation

Implement one governed `cancel_empty_plan_update` capability or map that semantic capability to one existing correctly named service.

Request authority shall consist only of:

- logical Plan identifier;
- expected successor Version identifier;
- expected concurrency token; and
- idempotency key.

The command shall not accept a client effective-change count, current Approved Version claim, Plan lifecycle result, release amount or audit reason.

Under one transaction:

1. authorize the planner for the Plan PE/FY and cancellation capability;
2. lock the logical Plan, current Approved predecessor and successor;
3. require an Open logical Plan and a Draft/Returned successor with an Approved predecessor;
4. recalculate effective additions, changes and proposed removals;
5. reject a non-empty or In-review successor;
6. reject any active Finance/review task or residual Draft hold/reservation as an inconsistent empty-successor state;
7. mark the successor Cancelled and immutable;
8. record one event with the fixed audit reason and actor/time; and
9. return the unchanged current Approved Version route.

Do not hard-delete the Version, Plan Item, allocation, task, decision, reason or audit history. Do not release Approved/current reservations or disturb a Tender handoff.

#### C.4 Focused tests

1. Explicit valid route context takes precedence for the request and is re-authorized.
2. Valid saved context restores; stale/disabled/unauthorised saved context does not.
3. One PE remains visible; multiple PEs require choice; zero PEs block; Administrator gives no default.
4. Current Open-Plan FY, nearest future Open-Plan FY, most recent past Open-Plan FY and current enabled no-Plan FY resolve in the approved order.
5. Future FY remains selectable and can show PLN-UI-01A even when FY2027/28 has an Approved Plan.
6. Changing context is mutation-free except for the deliberate validated preference update.
7. FY periods reject overlap and include exact start/end boundary dates.
8. A Demand appears in exactly one Plan FY from `required_by_date` and never from a client/saved FY claim.
9. Missing, out-of-period and mismatched dates return the exact stable issues and create no Plan Item.
10. A multi-year Plan Item remains sourced from the required-by-derived annual Plan.
11. PLN-UI-05B opens without mutation only for an empty Draft/Returned successor with an Approved predecessor.
12. Initial Draft Version 1, In-review, non-empty, unauthorised and stale-token cancellation requests fail.
13. Successful cancellation preserves Approved Version 1, `PPI-MOH-2027-021`, `RSV-MOH-0001` and `TND-MOH-2027-008`.
14. Cancellation produces one immutable Cancelled Version and one audit event; retry duplicates nothing.
15. No Logical Plan Closed/Cancelled command, action, fixture or unreachable state remains.

### D. Deterministic seed and scenario contract

#### D.1 Financial-year context

Use existing governed FY periods:

| Financial year | Start | End | Planning use |
|---|---|---|---|
| FY 2027/28 | 1 July 2027 | 30 June 2028 | Contains current canonical Approved/Open Plan |
| FY 2028/29 | 1 July 2028 | 30 June 2029 | Configured future year open for advance Planning in the resettable fixture |

Assert:

- `DMD-MOH-2027-019` required by 31 December 2027 maps to FY2027/28;
- `DMD-MOH-2028-001` and `DMD-MOH-2028-002` required by 31 December 2028 map to FY2028/29;
- a resettable boundary-date fixture at 1 July 2028 maps to FY2028/29;
- a resettable boundary-date fixture at 30 June 2028 maps to FY2027/28; and
- missing/out-of-period fixtures remain unavailable and are fully reset.

Do not add an editable `financial_year` property to the canonical Demand fixture. If a derived index is used, assert that it rebuilds to the values above.

#### D.2 Empty-successor cancellation

Extend `SCN-PLN-REMOVE-001` with a resettable post-removal boundary at **19 August 2027, 09:15 EAT**:

- Version 1 remains current Approved at KES 455,000,000;
- Draft Version 2 has zero effective changes and KES 455,000,000 effective total;
- `PPI-MOH-2027-022` is excluded/Removed from the Draft with its evidence retained;
- `DMD-MOH-2027-019` is Planning eligible again;
- no open Finance task or `RSV-MOH-0002` exists;
- `PPI-MOH-2027-021`, `RSV-MOH-0001` and `TND-MOH-2027-008` remain operational; and
- the logical Plan remains Open.

Open PLN-UI-05B and assert no mutation. Confirm once as Mercy Kilonzo and assert:

- Version 2 becomes immutable Cancelled;
- Version 1 remains the sole current Approved Version;
- no open successor remains;
- the fixed cancellation audit reason is recorded once;
- `DMD-MOH-2027-019` remains eligible for a later new update;
- no approved reservation or Tender changes; and
- an idempotent retry returns the same result.

Reset shall restore the declared post-removal empty Draft boundary without duplicating Version, item, task, release or audit records.

### E. Acceptance evidence

`PLN-CHG-016` may be marked implemented only when:

1. PE/FY context selection is explicit, deterministic, re-authorized and free of assignment/Administrator/seed fallbacks.
2. Future-year advance Planning remains possible without disrupting the current year's Plan.
3. Every Approved Demand maps to exactly one Plan FY from the governed required-by date and cannot be silently moved by Planning.
4. Missing, out-of-period, mismatched and overlapping-FY cases fail with exact stable issues and no partial creation.
5. The Logical Plan exposes only the admitted Open lifecycle in MVP.
6. Cancelled Version is used only for a governed empty-successor cancellation.
7. PLN-UI-05B contains exact static content, no reason field and no executable design instructions.
8. Cancellation is atomic, immutable, scoped, concurrency-safe and idempotent and preserves all Approved/Tender operation.
9. The integrated record supplies requirements, exact screen design, implementation, seed and tests without relying on a retired standalone document.

### F. Open decisions

None proposed. The unit deliberately removes unsupported Logical Plan close/cancel states and uses the approved required-by-date rule without adding another Demand field or approval.

---

## PLN-CHG-017 — Remaining reachable PLN-UI-05 Plan-builder states

**Status:** Approved  
**Approved:** 15 August 2026  
**Source:** Approved PLN-CHG-007, PLN-CHG-008, PLN-CHG-009, PLN-CHG-011, PLN-CHG-014, PLN-CHG-016 and closure finding `CL-05`  
**Problem:** The ordinary PLN-UI-05 Plan builder is authoritative for every populated editable Plan Version, but only the populated initial Draft, successor awaiting Finance and successor Ready frames are exact. Returned, Finance-stale, validation-blocked, multiple-change and removal-only successors are reachable under approved behaviour but have no exact static presentation. Stitch must not infer these states, and implementation must not encode separate readiness calculations or hidden workflow records to produce them.

### Locked design boundary

1. PLN-UI-05 remains one ordinary Plan-builder route. These are projections of authoritative Plan, Version, item, Finance, validation and removal records—not new screens, workflows or persistent UI states.
2. The current Approved Version remains operational throughout every successor state.
3. A Head-of-Procurement return reopens the same successor; it does not create another Version or approval stage.
4. A stale Finance confirmation and a blocked Planning validation are different conditions and shall be described separately.
5. Additions, changes and proposed removals may coexist in one successor. Whole-Version totals and readiness shall account for each change exactly once.
6. A proposed removal does not require another Planning-completeness or Finance-confirmation task. Its existing Approved reservation remains operational until approval applies the removal.
7. Empty-successor cancellation remains governed exclusively by PLN-CHG-016 and PLN-UI-05B; it is not repeated here.

### A. Requirements

| ID | Requirement |
|---|---|
| `PLN-FR-064C` | The ordinary Plan-builder projection shall derive one primary presentation state from authoritative records using this precedence: unresolved professional return; stale Finance basis; blocking validation; incomplete Planning; awaiting Finance; Ready. It shall also return every material issue so a lower-priority issue is not concealed. The state shall not be accepted from the route or stored as a UI flag. |
| `PLN-FR-064D` | A Returned successor shall show the returning professional authority, return time and exact immutable return reason. The same Version shall become editable. Submission shall remain unavailable until the planner makes and successfully saves at least one permitted Draft correction after the return and current whole-Version readiness is recalculated. No separate response-to-return field is required. |
| `PLN-FR-064E` | A current Finance confirmation whose governed basis no longer matches the item, source allocation or funding basis shall be shown as **Stale**, not Confirmed or Returned. The issue shall identify the affected Plan Item and state that Finance confirmation is required again. Historical confirmation and reservation evidence shall remain auditable; the builder shall expose no Budget Officer decision control. |
| `PLN-FR-064F` | A Planning validation failure shall be shown as **Blocked** when submission cannot proceed until a planner-owned correction is made. The issue shall identify the affected Plan Item, exact business-readable correction and direct permitted Plan Item action. A blocking issue shall not silently invalidate an unrelated current Finance confirmation unless the governed Finance-freshness rule says its basis changed. |
| `PLN-FR-064G` | A successor containing several effective changes shall show each actionable addition, changed item and proposed removal once. The summary shall show current Approved value, effective Draft value, additions, removals and net change. Changed-item count includes proposed removals; Planning and Finance denominators include only additions or changed items for which those controls are applicable. |
| `PLN-FR-064H` | A proposed-removal row shall show the unchanged Approved item reference, title, owner, Approved planned value, **Proposed removal**, current Finance evidence and the effect that will occur only if the successor is approved. It shall not show the item as already Removed, release funding early, restore the source early or request another Finance confirmation. |
| `PLN-FR-064I` | A removal-only successor may be Ready when it has one or more valid proposed removals, the required Plan-level reason, no downstream prohibition and no other blocking/stale issue. Planning-complete and Finance-confirmed denominators shall display **Not applicable** rather than `0 of 0`. Submission shall use the existing professional-review boundary. |
| `PLN-FR-064J` | PLN-UI-05 actions shall remain state-specific and capability-backed. Returned, stale, blocked and incomplete rows shall route only to the permitted ordinary Plan Item detail/editor. Proposed-removal rows shall use neutral Plan Item detail. The builder shall never expose Finance decisions, professional decisions, Budget mutation, Tender preparation, Plan publication or routine OU/HoD Planning sign-off. |

The approved ready-state submission rules, update-reason rules, removal rules and PLN-UI-05B empty-successor cancellation rules remain unchanged.

### B. Exact static screen designs

All five frames use the existing Procurement navigation, top bar, typography, table density and sticky footer of approved PLN-UI-05. They are separate static reference frames. Do not add tabs, a stepper, a version workbench, a raw diff, a workflow diagram or a second Plan-update screen.

#### B.1 PLN-UI-05 — Returned successor requiring planner correction

Use only this exact state:

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Procuring Entity: **Ministry of Health**
- Financial year: **2027/28**
- Plan: **PLN-MOH-2027-001**
- Current Approved Version: **Version 1**
- Editable Version: **Returned Version 2**
- Returned by: **Grace Wanjiku · Head of Procurement**
- Returned at: **20 August 2027, 11:00 EAT**
- As at: **20 August 2027, 11:05 EAT**

Header:

- Breadcrumb: **Procurement Planning / Ministry of Health Annual Procurement Plan 2027/28**
- Title: **Ministry of Health Annual Procurement Plan 2027/28**
- Quiet reference: **PLN-MOH-2027-001**
- Status line: **Open Plan · Returned Version 2**
- Supporting line: **Approved Version 1 remains active while the returned update is corrected.**
- Button: **Add approved Demands**

Summary strip:

1. **Draft Plan Items** — 2
2. **Draft planned value** — KES 535,000,000
3. **Net change** — KES 80,000,000 added
4. **Planning complete** — 2 of 2
5. **Finance confirmed** — 2 of 2
6. **Validation** — Needs attention

Section **Update reason** shows the approved existing reason:

**Add the approved digital-health technical staff certification programme to the FY 2027/28 Plan so delivery can begin before 31 December 2027.**

Show one prominent but restrained return notice:

- Heading: **Returned for correction**
- Metadata: **Grace Wanjiku · 20 August 2027, 11:00 EAT**
- Reason: **Clarify the planned delivery sequence for the added certification programme before approval.**

Section **Plan Items requiring action** shows exactly one row:

- Plan Item: **PPI-MOH-2027-022 · Digital health technical staff certification programme**
- Organisation Unit: **Human Resources Management and Development**
- Planned value: **KES 80,000,000**
- Planning: **Complete**
- Finance: **Confirmed**
- Validation: **Needs attention**
- Action: **Edit Plan Item**

Below the table show:

**1 unchanged Active Plan Item remains operational in Approved Version 1 · Tender TND-MOH-2027-008 remains active**

Text link: **View Approved Plan**

Sticky footer:

- Text button: **Back to Procurement Planning**
- Primary button: **Save draft**

Do not show **Submit for review**, a response field, Finance controls, Head-of-Procurement controls or cancellation.

#### B.2 PLN-UI-05 — Finance confirmation stale

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Procuring Entity: **Ministry of Health**
- Financial year: **2027/28**
- Plan: **PLN-MOH-2027-001**
- Current Approved Version: **Version 1**
- Editable Version: **Draft Version 2**
- As at: **20 August 2027, 10:25 EAT**

Header:

- Breadcrumb: **Procurement Planning / Ministry of Health Annual Procurement Plan 2027/28**
- Title: **Ministry of Health Annual Procurement Plan 2027/28**
- Quiet reference: **PLN-MOH-2027-001**
- Status line: **Open Plan · Draft Version 2**
- Supporting line: **Approved Version 1 remains active while this update is prepared and reviewed.**
- Button: **Add approved Demands**

Summary strip:

1. **Draft Plan Items** — 2
2. **Draft planned value** — KES 535,000,000
3. **Net change** — KES 80,000,000 added
4. **Planning complete** — 2 of 2
5. **Finance confirmed** — 1 of 2
6. **Validation** — Stale

Section **Update reason** shows:

**Add the approved digital-health technical staff certification programme to the FY 2027/28 Plan so delivery can begin before 31 December 2027.**

Show this issue:

**Finance confirmation for PPI-MOH-2027-022 is stale because its confirmed funding basis changed. Request Finance confirmation again before submitting this Plan update.**

Show exactly one actionable row:

- Plan Item: **PPI-MOH-2027-022 · Digital health technical staff certification programme**
- Organisation Unit: **Human Resources Management and Development**
- Planned value: **KES 80,000,000**
- Planning: **Complete**
- Finance: **Stale**
- Validation: **Stale**
- Action: **View Plan Item**

Below the table show:

**1 unchanged Active Plan Item remains operational in Approved Version 1 · Tender TND-MOH-2027-008 remains active**

Text link: **View Approved Plan**

Sticky footer:

- Text button: **Back to Procurement Planning**
- Primary button: **Save draft**

Do not show **Submit for review**, the superseded Finance decision as current, a Budget Line editor or any Finance decision action.

#### B.3 PLN-UI-05 — Planning validation blocked

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Procuring Entity: **Ministry of Health**
- Financial year: **2027/28**
- Plan: **PLN-MOH-2027-001**
- Current Approved Version: **Version 1**
- Editable Version: **Draft Version 2**
- As at: **20 August 2027, 10:25 EAT**

Header:

- Breadcrumb: **Procurement Planning / Ministry of Health Annual Procurement Plan 2027/28**
- Title: **Ministry of Health Annual Procurement Plan 2027/28**
- Quiet reference: **PLN-MOH-2027-001**
- Status line: **Open Plan · Draft Version 2**
- Supporting line: **Approved Version 1 remains active while this update is prepared and reviewed.**
- Button: **Add approved Demands**

Summary strip:

1. **Draft Plan Items** — 2
2. **Draft planned value** — KES 535,000,000
3. **Net change** — KES 80,000,000 added
4. **Planning complete** — 1 of 2
5. **Finance confirmed** — 2 of 2
6. **Validation** — Blocked

Section **Update reason** shows:

**Add the approved digital-health technical staff certification programme to the FY 2027/28 Plan so delivery can begin before 31 December 2027.**

Show this issue:

**PPI-MOH-2027-022 cannot proceed because its planned contract completion date is 15 January 2028, after the Approved Demand required-by date of 31 December 2027. Correct the planned schedule.**

Show exactly one actionable row:

- Plan Item: **PPI-MOH-2027-022 · Digital health technical staff certification programme**
- Organisation Unit: **Human Resources Management and Development**
- Planned value: **KES 80,000,000**
- Planning: **In progress**
- Finance: **Confirmed**
- Validation: **Blocked**
- Action: **Correct schedule**

Below the table show:

**1 unchanged Active Plan Item remains operational in Approved Version 1 · Tender TND-MOH-2027-008 remains active**

Text link: **View Approved Plan**

Sticky footer:

- Text button: **Back to Procurement Planning**
- Primary button: **Save draft**

Do not show **Submit for review**, another reason field or a disabled submission button.

#### B.4 PLN-UI-05 — successor with an addition and a proposed removal

Use only this resettable isolated state:

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Procuring Entity: **Ministry of Health**
- Financial year: **2028/29**
- Plan: **PLN-MOH-2028-001**
- Current Approved Version: **Version 1**
- Editable Version: **Draft Version 2**
- As at: **10 September 2028, 09:00 EAT**
- Current Approved value: **KES 72,000,000**
- Effective Draft value: **KES 48,000,000**
- Additions: **KES 48,000,000**
- Proposed removals: **KES 72,000,000**
- Net change: **KES 24,000,000 reduction**

Header:

- Breadcrumb: **Procurement Planning / Ministry of Health Annual Procurement Plan 2028/29**
- Title: **Ministry of Health Annual Procurement Plan 2028/29**
- Quiet reference: **PLN-MOH-2028-001**
- Status line: **Open Plan · Draft Version 2**
- Supporting line: **Approved Version 1 remains active while this update is prepared and reviewed.**
- Button: **Add approved Demands**

Summary strip:

1. **Effective changes** — 2
2. **Approved value** — KES 72,000,000
3. **Draft value** — KES 48,000,000
4. **Additions** — KES 48,000,000
5. **Proposed removals** — KES 72,000,000
6. **Net change** — KES 24,000,000 reduction
7. **Validation** — Needs attention

Section **Update reason** shows:

**Replace the clinical deployment laptop requirement with the approved clinical training laptop requirement for the FY 2028/29 rollout.**

Show this issue:

**Complete Planning and Finance confirmation for PPI-MOH-2028-001 before submitting this Plan update.**

Section **Plan Items requiring action** shows exactly two rows:

1. **PPI-MOH-2028-001 · Clinical training laptops for digital health rollout**
   - Organisation Unit: **Human Resources Management and Development**
   - Planned value: **KES 48,000,000**
   - Change: **Added**
   - Planning: **Not started**
   - Finance: **Not requested**
   - Validation: **Needs attention**
   - Action: **Complete item**
2. **PPI-MOH-2028-002 · Clinical deployment laptops for digital health rollout**
   - Organisation Unit: **Directorate of Digital Health and Policy**
   - Planned value: **KES 72,000,000**
   - Change: **Proposed removal**
   - Planning: **Not applicable**
   - Finance: **Confirmed**
   - Validation: **Ready**
   - Action: **View Plan Item**

Use these table columns:

- Plan Item
- Organisation Unit
- Planned value
- Change
- Planning
- Finance
- Validation
- Action

Sticky footer:

- Text button: **Back to Procurement Planning**
- Primary button: **Save draft**

Do not show **Submit for review**, an immediate funding release, a restored Demand, source checkboxes or an **Undo** action.

#### B.5 PLN-UI-05 — removal-only successor ready for review

Use only this resettable isolated state:

- Signed-in user: **Mercy Kilonzo**
- Role: **Procurement Planner**
- Procuring Entity: **Ministry of Health**
- Financial year: **2028/29**
- Plan: **PLN-MOH-2028-001**
- Current Approved Version: **Version 1**
- Editable Version: **Draft Version 2**
- As at: **10 September 2028, 09:10 EAT**
- Current Approved value: **KES 72,000,000**
- Effective Draft value: **KES 0**
- Proposed removals: **KES 72,000,000**
- Net change: **KES 72,000,000 reduction**

Header:

- Breadcrumb: **Procurement Planning / Ministry of Health Annual Procurement Plan 2028/29**
- Title: **Ministry of Health Annual Procurement Plan 2028/29**
- Quiet reference: **PLN-MOH-2028-001**
- Status line: **Open Plan · Draft Version 2**
- Supporting line: **Approved Version 1 remains active while this update is prepared and reviewed.**
- Button: **Add approved Demands**

Summary strip:

1. **Effective changes** — 1
2. **Approved value** — KES 72,000,000
3. **Draft value** — KES 0
4. **Net change** — KES 72,000,000 reduction
5. **Planning complete** — Not applicable
6. **Finance confirmation** — Not required
7. **Validation** — Ready

Section **Update reason** shows:

**Remove the clinical deployment laptop Plan Item because the approved requirement is no longer required and no Tender or downstream execution has started.**

Show this readiness message:

**The proposed removal is ready for Head-of-Procurement review. The item remains active until this Plan update is approved.**

Show exactly one row:

- Plan Item: **PPI-MOH-2028-002 · Clinical deployment laptops for digital health rollout**
- Organisation Unit: **Directorate of Digital Health and Policy**
- Planned value: **KES 72,000,000**
- Change: **Proposed removal**
- Planning: **Not applicable**
- Finance: **Confirmed**
- Validation: **Ready**
- Action: **View Plan Item**

Below the table show:

**If this update is approved, KES 72,000,000 will be released and Demand DMD-MOH-2028-002 will become available for Planning again.**

Sticky footer:

- Text button: **Back to Procurement Planning**
- Secondary button: **Save draft**
- Primary button: **Submit update for review**

Do not show the item as Removed, release funding, restore the Demand, create a Tender or expose a second removal/update reason.

### C. Implementation contract

#### C.1 One authoritative builder projection

Extend the existing PLN-UI-05 projection; do not add variant routes or stored presentation states.

The projection shall return:

- Plan, current Approved Version and editable successor identities;
- successor lifecycle and latest professional return evidence;
- current Approved value, effective Draft value, addition value, removal value and net change;
- one Plan-level update reason;
- effective change rows with change type `added`, `changed` or `proposed_removal`;
- applicable Planning and Finance denominators and statuses;
- all current validation issues with severity, affected record and remediation owner;
- compact unchanged-Approved operational context; and
- state-appropriate capabilities and destinations.

Calculate values from Version/item/allocation/removal records. Do not accept client totals, change types, readiness, return resolution, Finance freshness or validation state.

#### C.2 State and readiness rules

Apply the precedence in PLN-FR-064C only to the primary presentation. Retain all current issues in the projection and use the most severe applicable row status.

- **Returned:** require the same Version in Returned state and its latest completed return decision. A post-return correction is satisfied only by a successful save of at least one admitted Draft field after `returned_at`; opening, refresh, navigation or saving an unchanged payload does not satisfy it.
- **Stale:** compare current item/source/funding basis with the basis recorded by the latest Finance confirmation through the existing Finance-freshness service. A stale historical confirmation shall not count in the current denominator.
- **Blocked:** use authoritative validation issues. The example required-by failure blocks submission but does not itself erase historical Finance evidence.
- **Multiple change:** count every effective item once; calculate additions and removals separately; calculate `draft_value = approved_value + additions + approved changed-item deltas - removals`.
- **Proposed removal:** exclude removal-only rows from Planning and new-Finance denominators. Preserve Active state and reservation until professional approval.
- **Removal-only Ready:** require a current eligible removal, no downstream prohibition, non-empty Plan-level reason and no other blocking/stale issue.

Submission shall continue to call the approved PLN-CHG-011 command under lock. A stale projection, unresolved return, lost Finance confirmation, new downstream handoff or invalid removal shall fail without partial mutation.

#### C.3 Actions and authorization

- Resolve each row destination server-side from the Plan Item and current capability.
- **Edit Plan Item**, **Correct schedule** and **Complete item** open the existing PLN-UI-06 route for the same Draft item.
- **View Plan Item** opens the existing neutral Plan Item projection and shall not expose editable Draft fields to a viewer lacking mutation capability.
- **View Approved Plan** opens PLN-UI-09 for the current Approved Version.
- **Submit update for review** is returned only for a Ready successor and never as a disabled control in other frames.
- Direct mutation and route requests shall re-authorize PE/FY, Plan, Version and item scope.

No action may decide Finance, decide professional review, mutate Budget, prepare a Tender, publish a Plan or repeat OU/HoD approval.

#### C.4 Focused tests

1. Exact B.1–B.5 projections and arithmetic.
2. Primary-state precedence with all secondary issues retained.
3. Return actor/time/reason are immutable and the same Version reopens.
4. Refresh or unchanged save does not mark a return addressed; one admitted saved correction does.
5. Stale Finance evidence remains historical and does not count as current confirmation.
6. Required-by schedule failure is Blocked and routes to the affected item.
7. Multiple additions/removals reconcile Approved value, Draft value and net change exactly once.
8. Removal rows are excluded from inapplicable Planning/Finance denominators.
9. Proposed removal keeps the Active item, reservation and source ineligibility until approval.
10. Removal-only Ready submits through the existing professional-review command and creates one task.
11. Concurrent Tender handoff, reservation consumption, stale token or changed removal eligibility rejects submission atomically.
12. Cross-PE, unauthorised-role and direct-route attempts return no protected mutation surface.
13. No new workflow record, persistent UI-state flag, response field, cancellation path or approval gate exists.
14. Static designs contain no loading, save-transition or other executable simulation instruction for Stitch.

### D. Deterministic seed and scenario contract

No new permanent Plan, Version, Demand, Plan Item, Budget Line or user record is required.

#### D.1 Returned successor

Reuse the approved isolated return branch of `SCN-PLN-ADD-001`. Return Version 2 once at **20 August 2027, 11:00 EAT** with the exact approved reason. At **11:05 EAT**, assert B.1, Version 1 still current Approved, both reservations unchanged, no item activation and no new review task until a valid later resubmission.

#### D.2 Finance-stale and validation-blocked branches

Use two independently resettable branches from the approved **20 August 2027, 10:20 EAT** Ready boundary:

1. Invoke the existing Finance-freshness test fixture to create one material mismatch between the basis recorded by the current confirmation for `PPI-MOH-2027-022` and the current governed funding basis. Preserve the KES 80,000,000 Plan Item value and historical `RSV-MOH-0002`; mark the confirmation Stale once and assert B.2. Reset restores the exact Ready boundary.
2. Save contract completion **15 January 2028** for the Single-year `PPI-MOH-2027-022` while its Approved required-by date remains **31 December 2027**. Assert the exact Blocked issue and B.3. This schedule-only branch retains historical Finance evidence and creates no Finance task, reservation, review task or approval. Reset restores **31 December 2027**.

The stale branch is implementation evidence for the already approved Finance-freshness rule. It shall not add a user-editable funding field, a synthetic business status or a second Budget Line.

#### D.3 Multiple-change and removal-only branches

Reuse the resettable FY2028/29 records:

- current Approved Version 1 contains Active `PPI-MOH-2028-002` at KES 72,000,000 with one current unconsumed reservation and no Tender/downstream execution;
- Draft Version 2 adds `PPI-MOH-2028-001` at KES 48,000,000 and proposes removal of `PPI-MOH-2028-002` for B.4;
- the B.4 projection reconciles KES 72,000,000 Approved, KES 48,000,000 Draft, KES 48,000,000 additions, KES 72,000,000 removals and KES 24,000,000 reduction; and
- the independent B.5 branch contains only the proposed removal, reconciles Draft value KES 0 and KES 72,000,000 reduction, and remains Ready without a new Finance task.

Preparing or resetting either branch shall not change canonical FY2027/28 records or duplicate Version, item, allocation, reservation, removal, task or audit evidence.

### E. Acceptance evidence

`PLN-CHG-017` may be marked implemented only when:

1. every reachable populated Draft/Returned PLN-UI-05 state resolves through the one ordinary builder route;
2. B.1–B.5 render the exact identities, values, reasons, statuses, actions and exclusions specified above;
3. return, stale Finance and blocked validation remain distinct and route only to the permitted remediation;
4. additions and proposed removals reconcile to the effective Draft total without double counting;
5. inapplicable removal-only Planning/Finance counts display **Not applicable**;
6. no removal effect occurs before professional approval;
7. submission is absent from every non-ready frame and present for the exact Ready removal-only frame;
8. all mutations and destinations are capability-, PE/FY-, Version- and item-scoped;
9. canonical and isolated scenarios reset idempotently without cross-fixture changes; and
10. requirements, exact static design, implementation, seed and tests remain together in this ledger record without reliance on retired standalone documents.

### F. Open decisions

The Finance-stale frame relies on the already approved Finance-freshness service. No new funding-line edit or Budget workflow is proposed. No other business decision is open.

---

## PLN-CHG-018 — MVP-1 release boundary, mandatory hardening and MVP-2 deferrals

**Status:** Approved  
**Source:** Approved PLN-CHG-001 through PLN-CHG-017 and closure findings `CL-03` through `CL-06`  
**Purpose:** Establish the smallest complete, truthful and secure Procurement Planning product that can ship as MVP-1. Replace the remaining variant-by-variant design programme with an explicit release profile, mandatory hardening, deterministic smoke contract and governed MVP-2 backlog.  
**Problem:** Remaining audit items mix material functional boundaries with optional presentation variants. Treating every possible state as a separate MVP-1 design blocks shipment without improving the core product. Conversely, simply deferring reachable negative paths, authorization checks or visible dead-end actions would ship known defects. The release must distinguish these categories explicitly.

### Locked release decision

1. MVP-1 ships the complete ordinary annual-Plan journey for governed configured procurement methods, with Open tender as the safe baseline, Single-year and no-lots Plan Items.
2. Single- and multi-Demand Plan Item formation, including mixed-OU combination, remain in MVP-1 because they are already approved user-facing capabilities.
3. Finance confirmation, Finance shortfall, Finance return/re-request, initial Plan approval, successor approval, professional return/resubmission, whole-item removal and empty-update cancellation remain in MVP-1.
4. Legal grounds and methods not enabled by the governed catalogue, Multi-year treatment, Lots expected, Approved-Plan export, historical-Version detail, ungoverned implementation links and overdue-milestone presentation are deferred to MVP-2.
5. Deferred capabilities shall be absent from MVP-1 UI and command allow-lists. They shall not be displayed as disabled controls, placeholders, “coming soon” cards or partially functional fields.
6. No new Stitch screen is required merely because an existing data-driven component contains several source rows or a known lifecycle state. Exact component deltas below are sufficient.
7. Procurement Planning is documentation-closed for MVP-1 when this record is approved. Product release remains conditional on the smoke contract passing against production services and protected routes.

### A. MVP-1 requirements and scope

#### A.1 Supported release profile

| ID | MVP-1 requirement |
|---|---|
| `PLN-RLS-001` | The MVP-1 Planning method allow-list shall be derived from the active governed catalogue. **Open tender** remains the safe fallback when catalogue/schema configuration is incomplete. Planning shall not create a local method or legal-grounds catalogue. |
| `PLN-RLS-002` | PLN-UI-06 shall present the resolved governed method values and a recommendation reason code. Values outside that resolved allow-list fail with `PROCUREMENT_METHOD_NOT_CONFIGURED`. No local alternative-method ground or justification control shall appear in MVP-1. |
| `PLN-RLS-003` | The MVP-1 contract-period allow-list shall contain **Single year** only, and the indicative-lotting allow-list shall contain **No lots expected** only. Both decisions shall be explicitly selected and persisted; neither shall be silently defaulted. |
| `PLN-RLS-004` | A Plan Item shall not proceed to Finance unless its contract completion is within the selected Plan financial year and on or before the approved source required-by date, and the planner has explicitly selected **Single year** and **No lots expected**. |
| `PLN-RLS-005` | Direct or stale-client requests for an unavailable method, Multi-year treatment, Lots expected, alternative-method ground or alternative-method justification shall be rejected server-side with stable release-scope outcomes and no partial save or task creation. |
| `PLN-RLS-006` | Single-Demand, separate multi-Demand and combined multi-Demand formation remain supported. Combined items shall retain every Demand, Need Item, source OU, approved value and proposed funding allocation and shall be edited, funded, reviewed and approved as one Plan Item without losing source-level lineage. |
| `PLN-RLS-007` | One combined Plan Item Finance task shall show every source funding allocation and confirm all source amounts atomically. Any short source shall produce the existing PLN-UI-07A insufficient-funding result and no source reservation or Finance decision shall be created in isolation. |
| `PLN-RLS-008` | Finance **Return to planner** and one later re-request are mandatory MVP-1 paths. The returned item shall reopen only planner-owned fields, retain return evidence and create one linked task iteration only after a valid re-request. |
| `PLN-RLS-009` | Head-of-Procurement approval and return shall work for both initial Version 1 and a successor Version. Initial approval has no predecessor panel or supersession effect. Successor approval preserves and supersedes the predecessor as already specified. Return/resubmission shall reuse the same Version and linked task history. |
| `PLN-RLS-010` | Stale Finance, blocked validation, stale task, lost eligibility, concurrent handoff and unauthorized direct-route conditions shall remain server-enforced release blockers. A dedicated Stitch frame is not required when the existing component can present the approved status and issue contract. |
| `PLN-RLS-011` | PLN-UI-09 shall retain only governed destinations: **Add Plan Item** for an authorized planner when eligible sources exist; eligible **Propose removal**; and neutral **View Plan Item**. Tender reference and status may remain visible. |
| `PLN-RLS-012` | MVP-1 PLN-UI-09 shall remove **Export approved plan**, **View implementation** and **View historical version** as actions. Version-history rows and Tender references remain read-only text. No placeholder or disabled replacement shall be shown. |
| `PLN-RLS-013` | Every retained list, task, detail and command route shall re-authorize user, role/capability, PE/FY, record ownership and current task/Version state before protected data or actions are returned. Administrator status, record visibility or knowledge of an identifier shall grant no workflow authority. |
| `PLN-RLS-014` | The MVP-1 release shall contain no PLN-UI-10, Plan-publication concept, intermediate OU/HoD Planning sign-off, local legal catalogue, partial Finance confirmation, editable Approved Plan field or unsupported action destination. |

Stable release-scope outcomes:

| Identifier | User-facing message |
|---|---|
| `PROCUREMENT_METHOD_NOT_CONFIGURED` | **The selected procurement method is not enabled in the current catalogue.** |
| `PLANNING_MULTI_YEAR_NOT_AVAILABLE_MVP1` | **Multi-year Plan Items are not available in this release. Leave this requirement out of the current Plan if it cannot be completed within the financial year.** |
| `PLANNING_LOTS_NOT_AVAILABLE_MVP1` | **Plan Items requiring lots are not available in this release. Leave this requirement out of the current Plan if it cannot be procured without lots.** |
| `PROCUREMENT_METHOD_FALLBACK_OPEN_TENDER` | **The governed method configuration is incomplete. Open tender remains available as the degraded fallback.** |

These messages may appear only after a relevant rejected request or configuration failure. Do not add a permanent developer-oriented limitations panel to the workspace.

#### A.2 Explicit MVP-2 deferrals

| Deferred capability | MVP-1 treatment | MVP-2 admission condition |
|---|---|---|
| Procurement methods absent from the governed catalogue and legal grounds | No UI option or accepted command value | Governed method/threshold/grounds catalogue, legal ownership, exact UI and tests approved |
| Multi-year Plan Item | No UI option or accepted command value | Period rules, funding-year treatment, schedule validation, exact UI and seed approved |
| Lots expected | No UI option or accepted command value | Lot count/basis rules, anti-splitting controls, Tender handoff and exact UI approved |
| Approved Plan export | Action absent | Format, fields, redaction, scope, authorization and audit contract approved |
| Historical Version detail | History remains text only; link absent | Neutral immutable historical projection and route authorization approved |
| View implementation link | Tender reference/status remains text only | Governed downstream neutral-detail destination and cross-module authorization approved |
| Open-Draft notice on PLN-UI-09 | Deferred presentation | Exact non-mutating presentation admitted if user testing shows need |
| Overdue-milestone presentation | Deferred presentation | Reporting-period, calendar, variance and downstream-actual rules approved |
| Dedicated viewer-only screen variant | No separate layout; same neutral projection with actions omitted | Separate frame admitted only if usability testing requires it |

Deferral does not permit a hidden route, accepted payload value, seed fixture or partially implemented command.

### B. Exact static-design disposition

#### B.1 PLN-UI-06 release delta

Retain the approved canonical PLN-UI-06 layout and exact `PPI-MOH-2027-022` reference frame. Apply only these MVP-1 changes:

- **Planned procurement method** remains a required select showing the resolved governed catalogue options, including the Open tender fallback.
- **Contract period** remains required and shows one option: **Single year**.
- **Indicative lotting** remains required and shows one option: **No lots expected**.
- The three controls are empty until the planner selects their available value.
- Remove **Multi-year**, **Lots expected**, estimated lot count, lotting basis, alternative-method ground and alternative-method justification from the MVP-1 composition.
- Retain the seven milestone dates, planned-value read-only field, approved source section, description, category, Save draft and Request Finance confirmation.

For combined `PPI-MOH-2028-003`, use the same PLN-UI-06 composition. Replace the one-source **Approved requirement** block with one section titled **Approved requirements** containing exactly:

1. **DMD-MOH-2028-001 · Clinical training laptops for digital health rollout** — Human Resources Management and Development — 2 Need Items — KES 48,000,000 — Proposed funding: Digital health workforce development.
2. **DMD-MOH-2028-002 · Clinical deployment laptops for digital health rollout** — Directorate of Digital Health and Policy — 2 Need Items — KES 72,000,000 — Proposed funding: Digital clinical systems infrastructure.

Below the two sources show:

- **Combined planned value:** KES 120,000,000
- **Formation reason:** Procure one standard laptop specification and deployment service for the same national digital-health rollout.

Do not add source editing, allocation controls, per-source method/schedule fields or a separate combined-item screen.

#### B.2 PLN-UI-07/07A combined-source release delta

Retain the approved PLN-UI-07 and PLN-UI-07A drawer composition. For combined `PPI-MOH-2028-003`, the **Plan Item** section shows both source rows from B.1 and **Amount requiring confirmation — KES 120,000,000**.

The **Funding position** section shows exactly two read-only rows:

1. **Digital health workforce development** — Required KES 48,000,000 — Available KES 48,000,000 — After confirmation KES 0.
2. **Digital clinical systems infrastructure** — Required KES 72,000,000 — Available KES 72,000,000 — After confirmation KES 0.

Summary: **Total required — KES 120,000,000 · Total available — KES 120,000,000 · Sufficient funding**.

The isolated shortfall state changes only the second row to **Available KES 60,000,000 — Shortfall KES 12,000,000** and the summary to **Total available — KES 108,000,000 · Shortfall — KES 12,000,000 · Insufficient funding**. It shows the approved PLN-UI-07A actions only and no disabled **Confirm funding** button.

No new drawer, tab, accordion or per-source decision action is permitted.

#### B.3 PLN-UI-08 release delta

Retain the approved PLN-UI-08 professional-review layout.

- For initial Version 1, show **Submitted Version — Version 1**, omit the Approved-predecessor comparison entirely, show the submitted total and included items, and retain **Approve Plan** and **Return to planner**.
- For a successor, retain the approved predecessor comparison and **Approve plan update**.
- A Returned/resubmitted Version uses the same task layout and shows prior return evidence in the existing decision-history area.
- A blocked or stale task uses the same read-only task layout, shows the authoritative issues and exposes no Approve action.

No separate initial-approval, resubmission or blocked-review Stitch screen is required for MVP-1.

#### B.4 PLN-UI-09 release delta

Consequentially correct the approved PLN-UI-09 frame:

- Remove the header button **Export approved plan**.
- For `PPI-MOH-2027-021`, show **Tender active · TND-MOH-2027-008** as text and show no **View implementation** action.
- Retain **View Plan Item** for `PPI-MOH-2027-022` and the authorized **Propose removal** overflow action.
- In Version history, show Version 1 as **Superseded — KES 455,000,000 — Approved 18 August 2027** with no **View historical version** link.
- Retain **Add Plan Item** only in the authorized planner reference frame.
- A neutral viewer receives the same information architecture with every mutation action omitted; do not create a separate disabled-action frame.

No new PLN-UI-09 static variant is required for MVP-1.

### C. Implementation and release-hardening contract

#### C.1 Release allow-lists

Apply a server-owned MVP-1 release profile in the existing method, Plan Item validation and command services. It is configuration of admitted product capability, not a user-editable feature flag or domain status.

- Resolve active governed catalogue values first, then schema Select options, then the Open tender fallback.
- Return `PROCUREMENT_METHOD_FALLBACK_OPEN_TENDER` when configuration is degraded and `PROCUREMENT_METHOD_NOT_CONFIGURED` for payload values outside the resolved allow-list.
- Validate the resolved method, Single year and No lots expected against the server-owned allow-list.
- Reject unavailable values before persistence and before Finance-task creation.
- Do not retain hidden alternative fields, accept-and-ignore behavior or client-only option filtering.
- Preserve the deferred requirements as MVP-2 backlog; they are superseded only for the MVP-1 release profile.

#### C.2 Combined-source hardening

Use the already approved formation, item and Finance services.

- PLN-UI-06 shall render all immutable source allocations and one whole-item editable procurement treatment.
- One Finance task shall load every source funding allocation and authoritative balance.
- Confirm funding shall lock all affected allocations and create all reservations in one transaction.
- Any short, stale or unauthorized source shall roll back the entire confirmation.
- Return to planner shall return the whole Plan Item once, create no reservation and retain every source row.
- Plan approval shall activate the combined item once and retain all source/reservation lineage.

#### C.3 Mandatory negative and return paths

- Execute Finance return, planner correction and one linked Finance re-request through the existing production commands.
- Execute initial Plan approval and initial Plan return/resubmission through the same professional-task service without a fabricated predecessor.
- Execute successor return/resubmission through the same Version and linked task iterations.
- Revalidate task currency, Finance freshness, Plan readiness, removal eligibility and Tender handoff immediately before each decision.
- Reject direct routes before protected Finance/review data is serialized.
- Never substitute disabled decision controls for denied task access.

#### C.4 PLN-UI-09 route cleanup

- Remove export, historical-detail and implementation-detail routes, controls, tests and seed expectations from MVP-1 Planning.
- Do not leave aliases, empty handlers or placeholder modals.
- Retain neutral Plan Item detail and authorized Add/removal routes only.
- Tender reference/status is projection data; it shall not imply Tender access.

#### C.5 Release evidence and failure policy

MVP-1 is not releasable when any smoke test below fails, any deferred action remains visible/callable, a protected route leaks task data, combined funding partially reserves, or canonical arithmetic does not reconcile.

A failure shall be corrected in the existing owning service or UI component. It shall not create another approval, workaround field, manual database step or new Planning screen.

### D. Deterministic MVP-1 seed and smoke contract

#### D.1 Canonical release journey

Run the approved canonical FY2027/28 journey through production services:

1. Resolve Mercy Kilonzo's authorized Ministry of Health FY2027/28 workspace.
2. Open the current Plan or create the resettable initial Plan as applicable without navigation mutation.
3. Add Approved `DMD-MOH-2027-019` to the existing Approved Plan and create/reuse Draft Version 2 and `PPI-MOH-2027-022` once.
4. Complete PLN-UI-06 using explicitly selected Open tender, Single year and No lots expected plus the approved seven-date schedule.
5. Request Finance once; exercise sufficient-funding confirmation and the independent shortfall and return/re-request branches.
6. Submit once; exercise professional approval and the independent return/correction/resubmission branch.
7. Assert current Approved Version 2 at KES 535,000,000, two Active items, Finance 2 of 2 and one existing Tender handoff.
8. Exercise eligible removal and empty-successor cancellation without disturbing `PPI-MOH-2027-021`, `RSV-MOH-0001` or `TND-MOH-2027-008`.

#### D.2 Combined-source release fixture

Reuse `DMD-MOH-2028-001`, `DMD-MOH-2028-002` and combined `PPI-MOH-2028-003` with four immutable Need Item allocations and KES 120,000,000 total.

Create these resettable scenario-owned governed funding lines only for the isolated release fixture:

| Funding line | Approved | Reserved | Committed | Available |
|---|---:|---:|---:|---:|
| `MOH-BL-DHWD-2028` — Digital health workforce development | KES 48,000,000 | KES 0 | KES 0 | KES 48,000,000 |
| `MOH-BL-DCSI-2028` — Digital clinical systems infrastructure | KES 72,000,000 | KES 0 | KES 0 | KES 72,000,000 |

Assert:

- the combined editor shows both source rows, four Need Items, the exact formation reason and KES 120,000,000 read-only value;
- one Finance task shows both funding rows and KES 120,000,000 total;
- successful confirmation creates exactly two source reservations and one Finance decision atomically;
- an isolated shortfall branch applies one scenario-owned KES 12,000,000 hold to `MOH-BL-DCSI-2028`, displays KES 60,000,000 available and KES 12,000,000 shortfall on that row, and creates no reservation on either line; and
- reset removes only fixture-owned Plan/Version/item/allocation/funding/task/reservation/decision records.

#### D.3 Initial-Plan and route-security fixture

Use resettable FY2028/29 Version 1 with separate `PPI-MOH-2028-001` and `PPI-MOH-2028-002`, both complete and fully Finance-confirmed under the MVP-1 treatment.

- Submit Version 1 and assert one professional task with no Approved predecessor.
- Return once with a required reason; correct and resubmit the same Version; assert linked history and one current task.
- Approve once; assert Version 1 becomes current Approved and both Proposed items become Active without creating a Tender.
- As Requester, HoD, Planner, Viewer and Administrator without explicit task authority, assert that Finance and professional-task routes return no protected task payload or decision form.
- As a neutral permitted viewer, assert PLN-UI-09 read-only data with Add/removal actions omitted.

#### D.4 Deferred-capability absence

Assert across UI inventory, route inventory, command registry, seed and API tests:

- no alternative-method, method-ground, Multi-year or Lots expected control/value is available;
- direct payload attempts return the exact stable release-scope outcome and create no partial Draft/Finance state;
- no Export approved plan, View historical version or View implementation action/route exists in Procurement Planning;
- no PLN-UI-10, Plan-publication or intermediate OU/HoD Planning sign-off exists; and
- repeated setup and smoke execution are idempotent.

### E. MVP-1 release acceptance

Procurement Planning may be marked **MVP-1 release-ready** only when:

1. all approved PLN-UI-01 through PLN-UI-09 core routes load from authoritative PE/FY and record state;
2. only resolved governed method values, Single year and No lots expected are admitted treatment values;
3. single, separate multi-Demand and combined formation complete without lost source lineage;
4. combined Finance confirmation is full-value, multi-source and atomic, including the shortfall rollback test;
5. Finance return/re-request, initial Plan approval, successor approval and both professional-return/resubmission paths pass;
6. stale, blocked, concurrent and unauthorized attempts fail without partial mutation or protected-data disclosure;
7. Approved Version, reservation, removal and Tender-handoff invariants reconcile after every branch;
8. every deferred control, command and route is absent rather than disabled or partially implemented;
9. the exact canonical and isolated arithmetic, dates, identities and idempotency assertions pass; and
10. no retired standalone document is needed to implement or test the release.

Documentation approval of this record closes Procurement Planning scope for MVP-1. Implementation completion is evidenced by the smoke results; approval alone shall not claim that code has passed.

### F. Governed MVP-2 backlog

Carry forward only these explicit Procurement Planning candidates:

1. legal grounds and procurement methods not enabled by the governed catalogue;
2. Multi-year Plan Items and funding-period treatment;
3. Lots expected and Tender-lot handoff;
4. Approved Plan export;
5. immutable historical-Version detail;
6. governed downstream implementation-detail link;
7. overdue-milestone presentation; and
8. open-Draft or dedicated viewer presentation only if user testing demonstrates a need.

Each candidate requires its own approved integrated ledger record before implementation. No deferred candidate is an implied MVP-1 requirement.

### G. Open decisions

None proposed. Approval of this record approves the stated MVP-1 limitation and defers the listed capabilities to MVP-2.

## PLN-CHG-018 implementation closure evidence

Status: implementation complete; release smoke validation remains a separate gate.

| Closure item | Production evidence | Executable evidence | State / contract |
|---|---|---|---|
| `CL-01` | `planning_context.py`, `demand_financial_year.py`, `list_eligible_demands.py` | `test_planning_context_chg016.py` | selected / saved-default / legacy / demand-date FY mapping |
| `CL-02` | `remove_plan_item.py`, `plan_builder_successor.py` | `test_remove_plan_item.py` | PLN-UI-05B to terminal Cancelled Version and PLN-UI-09 |
| `CL-03` | `procurement_method_catalogue.py`, `get_plan_item_editor.py`, `update_plan_item.py` | `test_get_plan_item_editor.py`, `test_update_plan_item.py` | catalogue, schema-option and Open-tender fallback allow-list |
| `CL-04` | `get_plan_implementation.py`, `planning_approved_bind.js` | `test_get_plan_implementation.py`, `test_planning_ui_stitch_layout_guard.py` | UI-09 server action and destination contract |
| `CL-05` | `planning_ui_fixtures/*.js` | `test_planning_ui_stitch_layout_guard.py` revision variant matrix | PLN-UI-01 through PLN-UI-09 artifact coverage |
| `CL-06` | this ledger plus the state, implementation and audit documents | the same CL-focused tests above | integrated handoff evidence |

This evidence closes implementation traceability only. Procurement Planning is not MVP-1 release-ready until the named focused tests, asset build and protected-route smoke contract have passed and their results are recorded.
