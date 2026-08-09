# KenTender Procurement Planning — Cursor Implementation Pack

**Document ID:** PLANNING-MVP1-CURSOR-1.2  
**Date:** 9 August 2026  
**Status:** Approved implementation baseline  
**Requirements:** `Procurement_Planning_MVP1_Requirements_v1.4.md`  
**Design:** `Procurement_Planning_MVP1_Stitch_Prompts_v1.4.md` and approved Stitch outputs `PLN-UI-01` through `PLN-UI-10`  
**Seed:** `KenTender_MVP_Canonical_Demo_Data_Contract_v2.4.md`  
**Tracker:** `04_Procurement_Planning_MVP1_Implementation_Tracker.md`  
**Gate 00 boundary:** `GATE_00_REPLACEMENT_BOUNDARY.md` (Approved)  
**PP2 retirement:** `GATE_PP2_RETIREMENT.md` v1.1 — **full removal before Gate 01**; zero legacy Planning code; no temporary preserve

**Revision 1.2:** Retains the 1.1 document-hygiene decisions and makes the Requirements v1.4 service and business-record names authoritative. Repository conventions may determine code placement and language casing, but may not rename the approved service contract or domain records.

---

## 1. How to use this pack

Run the prompts below in order. Do not give Cursor the whole pack as one implementation request.

For every section Cursor must:

1. inspect the repository before proposing changes;
2. implement only the stated section;
3. preserve unrelated working code and the existing application shell;
4. run the relevant tests;
5. report changed files, migrations, tests and remaining blockers; and
6. stop at the section gate before proceeding.

If the repository conflicts with an approved requirement or canonical fixture, Cursor must report the conflict. It must not silently reinterpret the documents.

---

## 2. Authority and conflict order

Use this order:

1. `Procurement_Planning_MVP1_Requirements_v1.4.md`
2. this implementation pack;
3. `KenTender_MVP_Canonical_Demo_Data_Contract_v2.4.md`
4. approved Stitch outputs and `Procurement_Planning_MVP1_Stitch_Prompts_v1.4.md`;
5. existing repository conventions that do not conflict with the above.

Stitch defines screen composition, hierarchy and visible controls. It does not define persistence, permissions, workflow or validation.

---

## 3. Non-negotiable implementation decisions

### 3.1 Clean replacement boundary

- Existing MVP Planning data is disposable.
- Build the approved model cleanly; do not preserve obsolete Planning structures merely because they exist.
- Do not dual-write old and new Planning models.
- Do not add compatibility aliases, shadow DocTypes or translation layers unless an identified live dependency requires one and the user approves it.
- Inventory legacy Planning routes, DocTypes, services, tests and callers before removal.
- Retire obsolete Planning code only inside the approved boundary. Do not alter unrelated modules.

### 3.2 UI architecture

- Use native KenTender/Frappe Desk pages and the existing application shell.
- Hand-port the approved Stitch main-content design into repository-native CSS, templates and JavaScript.
- Do not use an iframe, static Stitch runtime or a second navigation shell.
- Do not change global navigation, branding or toolbars.
- Keep pages compact, task-oriented and server-backed.

### 3.3 Domain boundaries

Planning may read approved Demand, Budget, reservation, Strategy and Organisation data. It may not mutate those baselines.

Planning owns:

- the logical annual Procurement Plan;
- Plan Versions;
- stable Plan Items and Plan Item Versions;
- Draft and Effective Demand allocations;
- departmental submissions;
- Planning decisions and validation;
- publication evidence;
- Planning handoff snapshots; and
- Planning audit and notification events.

Planning does not own Demand approval, Budget approval, reservation creation, Strategy maintenance, Tender configuration, award, contract, commitment or expenditure.

### 3.4 Identity and versioning

- One logical Plan exists per Procuring Entity and financial year.
- A logical Plan is `Open`, `Closed` or `Cancelled`.
- Only one current Approved Plan Version may exist.
- At most one open Draft successor may exist.
- Approved, Superseded and Cancelled versions are immutable.
- A stable Plan Item carries operational identity across Plan Versions.
- Planning values belong to Plan Item Versions.
- A Draft Plan Item is `Proposed`; approval makes it `Active`.
- An Approved revision may mark an item `Removed` without deleting history.

### 3.5 Adding and revising Plan Items

The required post-approval path is:

> `PLN-UI-09 Add Plan Item` → `PLN-UI-04 eligible Demand selection` → create or reuse the single Draft successor and a Proposed Plan Item → `PLN-UI-06 Plan Item editor` → save to `PLN-UI-10 revision overview`

Rules:

- `PLN-UI-10` is a revision overview, not an item-selection screen.
- The user does not manually create a revision before selecting **Add Plan Item**.
- If no Draft successor exists, the service creates one.
- If one exists, the addition joins it.
- The current Approved version remains operational throughout.
- A compatible Demand may be added to an existing Proposed Plan Item while its Plan Version is Draft. This is a Draft edit, not a new revision.
- Adding a Demand to an Active item in an Approved version requires a Draft successor and a new Plan Item Version.
- Aggregation requires the same Procuring Entity, preserved funding/reservation lineage and an accountable reason.
- A taken-up Active item cannot be materially changed without the governed downstream correction process.

### 3.6 Source and field semantics

- Procuring Entity is explicitly selected when the user has more than one eligible scope.
- Never silently select the first scope or fall back to an Administrator fixture.
- Financial year is a controlled select.
- Planning period dates are derived from the selected financial year and read-only.
- Currency is controlled; show it read-only when only one value is eligible.
- Coordinating procurement unit is an authorised Organisation Unit select; it need not be the lowest unit.
- Do not capture a Budget context on the Plan header.
- Demand, Budget, reservation and Strategy information in the Plan Item editor is inherited and read-only.
- Users do not maintain business codes or statutory percentages.
- Actual milestones are downstream projections, not editable Planning fields.

### 3.7 Security and audit

- Every read, mutation, queue, total, report and export must enforce Procuring Entity and Organisation Unit scope server-side.
- A role without scope grants no operational access.
- Administrator status alone grants no Planning authority.
- State-changing services must validate role, scope, current version and transition server-side.
- Approval, supersession and effective allocation creation must be transactional and idempotent.
- Audit events retain actor, role, time, source, before/after values and reason.

---

## 4. Required domain records

Use the exact approved business-record names below. Repository conventions may determine module paths, class names and language casing only; they shall not create alternative business-record names.

| Record | Responsibility |
|---|---|
| Procurement Plan | Stable PE/FY container and lifecycle |
| Procurement Plan Version | Draft/review/approved immutable baseline |
| Procurement Plan Item | Stable operational identity |
| Procurement Plan Item Version | Version-specific planning decisions and snapshots |
| Plan Demand Allocation | Demand Item quantity/amount allocated to a Plan Item |
| Departmental Submission | Organisation Unit sign-off for one Plan Version |
| Plan Decision | Review, return, recommendation and approval evidence |
| Plan Validation Result | Current run and business-readable issues |
| Publication Event | Export/publication state and evidence |
| Planning Handoff Snapshot | Immutable approved input to Tender Management |

Do not create user-facing records named Planning Inclusion, Procurement Package, Package Line, Release Package or Consumption.

---

## 5. Service contract

Expose these exact server service names from Requirements v1.4. Do not substitute aliases. Internal helpers may follow repository conventions but must remain private implementation details.

- `create_procurement_plan`
- `get_planning_workspace`
- `list_eligible_demands`
- `add_demand_to_plan`
- `update_plan_item`
- `aggregate_plan_allocations`
- `validate_plan`
- `submit_departmental_contribution`
- `submit_plan_for_review`
- `record_plan_decision`
- `approve_plan_version`
- `open_or_create_plan_revision`
- `cancel_plan_revision`
- `publish_approved_plan`
- `create_tender_from_plan_item`
- `get_plan_implementation`
- `get_plan_audit`

Every mutation returns a fresh projection. Use stable business error codes for permission, scope, validation, stale version, funding, duplicate allocation and downstream-take-up conflicts.

---

## 6. Canonical scenario

Implement `KENTENDER_MVP_V1` exactly from Canonical Demo Data Contract 2.4.

Principal story:

- Procuring Entity: Ministry of Health
- Secondary accessible PE: County Government of Kisumu
- Logical Plan: `PLN-MOH-2027-001`, Open
- Current Approved version: `PLN-MOH-2027-001-V1`
- Active item: `PPI-MOH-2027-021`
- Requirement: National digital health infrastructure upgrade
- Owner: Directorate of Digital Health and Policy
- Amount: KES 455,000,000
- Budget Line: Digital clinical systems infrastructure
- Primary Strategy target: At least 99.9% annual availability by 30 June 2028
- Supporting target: Restore critical services within four hours by 30 June 2028
- Tender: `TND-MOH-2027-008`, active

Post-approval scenario `SCN-PLN-ADD-001`:

1. `DMD-MOH-2027-019` starts Returned at KES 95,000,000 with a KES 15,000,000 shortfall.
2. Its scope is corrected to KES 80,000,000 and passes the existing mandatory Demand approvals.
3. Final Demand approval creates exactly one `RSV-MOH-0002`.
4. **Add Plan Item** creates or opens Draft Version 2.
5. Proposed `PPI-MOH-2027-022` is created for the certification programme.
6. Version 1 and its active Tender remain operational.
7. Revised value becomes KES 535,000,000.
8. The 30% plan-allocation basis becomes KES 160,500,000.
9. Approval makes Version 2 current Approved, supersedes Version 1 and activates the new item.

The seed/reset and scenario runner must be idempotent. A second run creates no duplicate plan, version, item, allocation, reservation, decision, handoff or audit event.

Stitch screens represent journey states. Do not create contradictory permanent canonical records merely to make every mockup state coexist. Use isolated test fixtures for pre-approval UI states.

---

# Cursor Prompt 00 — Repository audit and replacement plan

```text
Read these files completely before acting:
- Procurement_Planning_MVP1_Requirements_v1.4.md
- Procurement_Planning_MVP1_Stitch_Prompts_v1.4.md
- Procurement_Planning_MVP1_Cursor_Implementation_Pack_v1.2.md
- KenTender_MVP_Canonical_Demo_Data_Contract_v2.4.md

Perform a read-only audit of the current Procurement Planning implementation.

Identify:
1. Planning DocTypes/tables, controllers, services, routes, pages, reports and tests.
2. Callers and dependencies from Demands, Budget, Strategy, Tender, notifications, audit and permissions.
3. Legacy concepts that conflict with the approved model.
4. Reusable shared infrastructure that already satisfies the requirements.
5. The exact clean replacement boundary.
6. Data/migrations that can be discarded and any non-disposable dependency that must be preserved.

Do not implement or edit files.

Return:
- current-state map;
- keep/replace/retire table;
- proposed target records and services;
- ordered implementation plan;
- risks or document conflicts;
- tests required at each gate.

Do not propose dual-write, iframe/static HTML, legacy adapters or additional workbenches unless a verified dependency makes one unavoidable.
```

**Gate 00:** Approve the exact replacement boundary before implementation.

---

# Cursor Prompt 01 — Clean domain and workflow foundation

```text
Implement the approved Procurement Planning domain foundation from Gate 00.

Create the clean persistence model for:
- logical Procurement Plan;
- Plan Version;
- stable Plan Item;
- Plan Item Version;
- Plan Demand Allocation;
- Departmental Submission;
- Plan Decision;
- Validation Result;
- Publication Evidence; and
- Planning Handoff Snapshot.

Implement server-side invariants:
- one logical Plan per Procuring Entity and financial year;
- at most one current Approved version;
- at most one open Draft successor;
- immutable Approved/Superseded/Cancelled versions;
- stable Plan Item identity across versions;
- Draft allocations do not consume Demand availability;
- approval makes allocations effective exactly once;
- same-PE enforcement for all Plan Item allocations;
- optimistic/stale-version protection;
- no Administrator fallback authority.

Implement the status vocabularies exactly as defined in the requirements. Keep validation, departmental submission, publication and Tender take-up as separate projections rather than Plan statuses.

Retire only the obsolete Planning structures approved in Gate 00. Do not modify unrelated domain data.

Add unit and transactional tests for all invariants. Stop after reporting migrations, records, services, retired code and test evidence.
```

**Gate 01:** Domain tests pass and no legacy dual-write remains.

---

# Cursor Prompt 02 — Scope, roles and canonical seed

```text
Implement Planning role/scope enforcement and the canonical seed contract.

Roles must support:
- Organisation Unit Planning Contributor;
- Head of User Department;
- Procurement Planner;
- Planning Reviewer / Head of Procurement;
- Accounting Officer or configured final authority;
- Tender Initiator;
- Manager/Auditor; and
- System Administrator configuration only.

Enforce Procuring Entity and Organisation Unit scope consistently in services, queues, totals, reports and exports.

Implement the zero-, single- and multi-scope selection pattern:
- zero eligible PE scopes blocks plan creation;
- one eligible PE is visible and read-only;
- multiple eligible PEs require explicit selection;
- never select the first assignment silently;
- Administrator status supplies neither scope nor authority.

Extend the central KENTENDER_MVP_V1 seed/reset using Canonical Demo Data Contract 2.4. Add deterministic SCN-PLN-ADD-001 setup/run/reset commands. Do not invent substitute names, values, dates or IDs.

Add seed validation that proves arithmetic, ownership, references, role scope, current version, reservation lineage and rerun idempotency.

Add role-matrix service tests and browser-login helpers for each operational role. Stop with the exact seed command, validation report and role test evidence.
```

**Gate 02:** The story resets repeatably and cross-entity access tests pass.

---

# Cursor Prompt 03 — Workspace, plan registration and Draft builder

```text
Implement PLN-UI-01, PLN-UI-02 and PLN-UI-03 using the approved Stitch main-content designs and existing application shell.

Workspace:
- explicit PE and financial-year context filters;
- current Plan and open Draft-revision projection;
- compact action queue from live data;
- no dashboard charts or duplicate role workbenches.

Plan registration:
- PE is an explicit authorised searchable select for the multi-scope state;
- financial year is a controlled select;
- planning-period dates are derived read-only;
- title is a text input;
- currency is controlled or visibly read-only when only one value is permitted;
- coordinating procurement unit is an authorised Organisation Unit select and need not be the lowest unit;
- do not capture Budget context;
- generate internal Plan references server-side.

Draft builder:
- compact derived totals and filters;
- empty state with Add approved demand;
- no manual blank Plan Item grid;
- no package/release/consumption objects.

Implement live APIs, permission checks, empty/loading/error states and browser tests for zero-, single- and multi-PE users. Do not copy Stitch navigation or use an iframe.
```

**Gate 03:** Registration and workspace browser tests pass for every PE-scope state.

---

# Cursor Prompt 04 — Demand selection and focused Plan Item editor

```text
Implement PLN-UI-04, PLN-UI-05 and PLN-UI-06.

Eligible Demand selection:
- list only Approved, Planning Ready, authorised and not-fully-planned Demand Items;
- show approved, planned and available amounts, required-by date and funding read-only;
- selection must not edit the Demand;
- selecting one Approved Demand creates one Proposed Plan Item by default and includes its available Need Items as Draft allocations;
- partial allocation must remain within approved available quantity/amount.

Plan Item editor:
- inherited Demand, owner, funding, reservation and Strategy context is read-only;
- description is multiline input;
- category is searchable controlled selection;
- governing regime and method recommendation are derived read-only;
- confirmed method and arrangement are controlled selections;
- alternative method requires configured grounds, reason and evidence;
- aggregation and lotting use explicit decisions and accountable reasons;
- milestone values are date inputs with chronological validation;
- statutory treatment and target groups are controlled selections;
- statutory percentage and plan-level required amount are derived;
- Strategy targets and Plan Value Commitments are immutable snapshots;
- users may enter only the Planning treatment note.

Support adding another eligible Demand allocation to an existing Proposed Plan Item while its Plan Version remains Draft. Treat this as a Draft edit, not a new revision. Enforce compatible PE, funding/reservation lineage and required aggregation reason.

Material upstream changes must return a stable correction error instead of mutating Demand, Budget or Strategy.

Add unit, service and Playwright tests for eligibility, allocation arithmetic, aggregation, anti-splitting, read-only inheritance, field types and permissions.
```

**Gate 04:** A planner can create and complete one valid Proposed Plan Item without upstream mutation.

---

# Cursor Prompt 05 — Validation, departmental sign-off and approval

```text
Implement PLN-UI-07 and PLN-UI-08 plus the underlying validation and decision services.

Validation must run on material save, submission, approval and Tender take-up. Validate:
- Demand eligibility and allocation arithmetic;
- PE/OU ownership;
- current funding and reservation;
- method and basis;
- schedule chronology;
- aggregation/division and anti-splitting;
- statutory allocation coverage;
- Strategy/value treatment;
- departmental submission;
- approval authority; and
- handoff integrity.

Expose business-readable Ready, Needs attention and Blocking issues. Users cannot set Ready manually.

Departmental contribution:
- show one OU contribution and read-only derived items/totals;
- require the declaration checkbox;
- optional multiline submission note;
- retain actor, role and time.

Consolidated review:
- show derived totals, item evidence and statutory coverage;
- show only the current decision and prior decision trail;
- recommendation comment is optional;
- return comment is required;
- use the configured authority, not a hard-coded Ministry title.

Approval must atomically:
- lock the Plan Version and Plan Item Versions;
- make Draft allocations Effective exactly once;
- activate Proposed items;
- apply approved removals;
- supersede the previous current Approved version when applicable; and
- create the immutable approved snapshot and audit events.

Add role-based Playwright tests for Contributor, Head of Department, Planner, Reviewer, Approver, Viewer and Administrator-without-operational-role.
```

**Gate 05:** Approval is atomic, idempotent and demonstrably segregated by role.

---

# Cursor Prompt 06 — Approved Plan, implementation and controlled revision

```text
Implement PLN-UI-09 and PLN-UI-10 with the corrected routing.

Approved Plan view:
- approved baseline is read-only;
- implementation status and actual milestones are derived from downstream records;
- reporting period is a controlled select;
- As-at, totals, publication and variance are derived;
- Add Plan Item is available only on an Open Plan with suitable authority;
- existing Active items and Tenders remain operational while a Draft revision exists.

Add Plan Item route:
1. Open the PLN-UI-04 eligible Demand selection modal from PLN-UI-09.
2. On confirmed selection, call open_or_create_plan_revision.
3. Create or reuse the Proposed Plan Item and Draft allocation.
4. Open PLN-UI-06 to complete that item.
5. Save back to PLN-UI-10, the revision overview.

Revision overview:
- show Approved Version 1 and Draft Revision 2 concurrently;
- reason is a required controlled selection;
- explanation is a required user-entered multiline field, not prefilled evidence;
- show changed and unchanged items read-only;
- revalidate only changed items and affected plan-level controls while retaining the complete consolidated snapshot;
- do not suspend unchanged Active items or downstream Tenders.

For SCN-PLN-ADD-001 prove:
- one Draft Version 2 is created/reused;
- PPI-MOH-2027-022 is Proposed at KES 80,000,000;
- total becomes KES 535,000,000;
- statutory basis becomes KES 160,500,000;
- Version 1 and TND-MOH-2027-008 remain operational;
- approval supersedes V1, activates the new item and preserves the unchanged handoff;
- rerun creates no duplicates.

Add service, transaction and Playwright tests for the complete route and concurrency conflicts.
```

**Gate 06:** The post-approval addition scenario passes end to end and remains idempotent.

---

# Cursor Prompt 07 — Publication, Tender handoff, reporting and support controls

```text
Complete the Planning integration boundary without rebuilding downstream modules.

Publication:
- expose structured current-Approved-plan data;
- retain destination, status, time and evidence;
- publication failure creates an operational issue and does not change approval status.

Tender handoff:
- permit take-up only from an Active item in the current Approved version;
- revalidate scope, method, funding/reservation and remaining take-up;
- create an immutable handoff snapshot atomically;
- preserve Demand allocation and reservation lineage;
- do not require a user-managed Release Package or Consumed action.

Monitoring:
- derive Tender take-up and actual milestones;
- include reporting period, As-at, scope and drill-down basis;
- do not claim realised savings or public-value achievement from plans alone.

Notifications and audit:
- reuse shared infrastructure where compliant;
- notify responsible users for submission, return, approval, blocker, publication failure, approaching milestone and overdue take-up;
- audit every material planning and decision event.

Add contract tests across Demands, Budget, Core Scope and Tender boundaries. Do not create fake downstream records for unimplemented modules.
```

**Gate 07:** Integration contracts pass without duplicate lifecycle ownership.

---

# Cursor Prompt 08 — Final verification and close-out

```text
Perform the final Procurement Planning MVP 1 verification against:
- Procurement_Planning_MVP1_Requirements_v1.4.md
- Procurement_Planning_MVP1_Stitch_Prompts_v1.4.md
- Procurement_Planning_MVP1_Cursor_Implementation_Pack_v1.2.md
- KenTender_MVP_Canonical_Demo_Data_Contract_v2.4.md

Run:
1. schema/migration checks;
2. unit and transactional tests;
3. role/scope matrix tests;
4. canonical seed/reset twice;
5. SCN-PLN-ADD-001 twice;
6. service/API contract tests;
7. Playwright journeys for PLN-UI-01 through PLN-UI-10;
8. cross-entity isolation tests;
9. accessibility checks for labels, keyboard operation, focus, error association and disabled actions; and
10. legacy-reference search proving retired Planning code is no longer called.

Produce a requirements traceability table with requirement/acceptance ID, implementation location, automated test and result.

Report separately:
- passed requirements;
- genuine deferred integrations;
- defects;
- obsolete code removed;
- remaining legacy dependencies;
- commands for reset, scenario execution and full verification.

Do not mark a requirement complete based only on a screen rendering, a specification note or an Administrator smoke test.
```

**Gate 08:** No blocker remains; all claimed completions have automated evidence.

---

## 7. Definition of done

MVP 1 is complete when:

- the clean domain model and invariants are live;
- the ten approved UI states are backed by live services;
- the full user journey is navigable without hidden manual setup;
- PE/OU scope and role segregation are enforced server-side;
- Approved versions are immutable;
- Draft edits and post-approval revisions behave differently and correctly;
- the canonical story resets and reruns without duplication;
- unchanged Active items and Tenders survive a Draft revision;
- Planning never mutates upstream baselines;
- Tender handoff uses an immutable approved snapshot;
- audit, notification, publication and reporting projections are traceable; and
- the traceability report proves each implemented requirement.
