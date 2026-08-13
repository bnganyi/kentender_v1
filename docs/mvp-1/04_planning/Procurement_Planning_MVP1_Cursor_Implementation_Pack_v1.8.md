# KenTender Procurement Planning — Cursor Implementation Pack

**Document ID:** PLANNING-MVP1-CURSOR-1.8  
**Version:** 1.8  
**Status:** Approved implementation baseline for direct MVP correction  
**Date:** 12 August 2026  
**Supersedes:** `PLANNING-MVP1-CURSOR-1.7`  
**Requirements:** `Procurement_Planning_MVP1_Requirements_v1.9.md`  
**Design:** `Procurement_Planning_MVP1_Stitch_Prompts_v2.0.md` and approved outputs PLN-UI-01 through PLN-UI-10, including PLN-UI-05A and PLN-UI-07A  
**Operating model:** `KenTender_MVP_Cross_Module_Operating_Model_v1.1.md`

**Revision 1.8:** Implements controlled whole-Plan-Item removal. Draft-only items are removed from the Draft with preserved history and immediate task/funding reversal; eligible Active items are proposed for removal in a Draft successor and become Removed only on successor approval. Executed items are protected. All v1.7 Finance-shortfall and earlier workflow corrections remain in force.

## 1. How to use this pack

Run the prompts below in order as focused implementation sections. Each prompt must change the product, run relevant tests and return one concise completion report. Do not create another audit pack, recovery programme, migration study or replacement PRD.

For every section Cursor shall:

1. read the controlling documents completely;
2. inspect the relevant repository code before editing;
3. implement only the stated section and its necessary dependencies;
4. preserve unrelated Frappe/ERPNext apps, credentials, site configuration and user files;
5. use an ordinary quick checkpoint only if immediately available before destructive schema/seed changes;
6. run focused automated tests; and
7. report changed files, schema changes, tests and genuine blockers concisely.

MVP seed data is disposable. Prefer a clean teardown/reseed to dual-write, aliases or compatibility scaffolding.

## 2. Authority and conflict order

Use this order:

1. `KENTENDER-MVP-CMOM-1.1`
2. `PLANNING-MVP1-REQ-1.9`
3. `PLANNING-MVP1-STITCH-2.0` for visible screen composition
4. this Cursor pack
5. the canonical seed contract only where it does not conflict with the above
6. existing repository conventions that do not conflict

Stitch does not define persistence, workflow, security or service behaviour. Older Requirements, Stitch and Cursor versions are not implementation authorities.

## 3. Required end state

The implemented sequence shall be:

> **Requester → HoD Demand approval → Procurement Planner → Finance/Budget Officer → Head of Procurement → Tender-ready Plan Item**

Non-negotiable results:

- HoD approval in Demands creates Planning Ready source evidence.
- PLN-UI-04 selects one or more Approved Demands once.
- One selection forms one Proposed Plan Item; multiple selections require separate or compatible combined formation.
- PLN-UI-06 completes each resulting existing item without selecting or regrouping sources again.
- Finance confirms/reserves once after Plan Item completion.
- Head of Procurement reviews only after current Finance confirmation.
- No Departmental Contribution, Departmental Submission or routine second HoD sign-off remains.
- Approved Plan Versions are immutable.
- Adding to an Approved Plan quietly creates/reuses one Draft successor.
- A planner can remove a draft-only item or propose eligible Active-item removal without deleting history or editing the Approved baseline.
- The current Approved Version and existing Tender handoffs remain operational until successor approval.
- Restricted task actions and task routes are absent for unauthorised users, not merely disabled.

## 4. Clean implementation boundary

### 4.1 Retain

- Procurement Plan
- Procurement Plan Version
- Procurement Plan Item
- Procurement Plan Item Version
- Plan Demand Allocation
- Plan Decision
- Plan Validation Result
- Publication Event/evidence
- Planning Handoff Snapshot
- existing PE/OU scope foundation
- existing Demand Funding Allocation and Budget reservation foundation
- existing decision/audit/notification infrastructure where semantically correct

### 4.2 Remove

- Departmental Submission DocType/table and controller
- Departmental Contribution UI/status/services/permissions/gates
- `submit_departmental_contribution` or equivalent public action
- routine Planning-stage HoD tasks and records
- generic statutory allocation treatment/rationale fields
- generic Strategy/value-treatment fields
- item-level preference/reservation scheme, target-group and planned-value controls introduced by the superseded design
- zero/placeholder treatment rows
- cosmetic default `Keep separate` aggregation state
- Demand-stage Finance approval retained as a duplicate of post-Planning confirmation
- silent PE/OU fallbacks and Administrator operational-role inflation
- restricted approval forms rendered with disabled actions

Do not replace removed concepts with renamed equivalents.

## 5. Service naming rule

Requirements define capabilities, not duplicate function aliases.

- Inspect current public Planning services and their callers.
- Keep an existing public name when its behaviour is semantically correct.
- Correct the implementation behind that service where required.
- Add a new public service only when no correct capability exists.
- Do not expose both `create_*` and `register_*`, `list_eligible_demands` and `list_eligible_demand_items`, or similar aliases solely to satisfy historic documents.
- Produce one final capability → actual service → tests mapping.

Internal helpers may follow repository conventions.

## 6. Canonical scenario

Preserve this repeatable story:

- Principal PE: Ministry of Health
- Secondary isolation PE: County Government of Kisumu
- FY: 2027/28
- Budget Line allocation: KES 480,000,000
- Approved Demand / principal Plan Item: KES 455,000,000
- Plan Item: PPI-MOH-2027-021
- Finance confirmation occurs after Plan Item completion and reserves KES 455,000,000
- Later commitment: KES 310,000,000
- Remaining reservation: KES 145,000,000
- Existing Tender: TND-MOH-2027-008
- Returned Demand history: KES 95,000,000
- Corrected HoD-approved Demand: KES 80,000,000
- New item: PPI-MOH-2027-022
- Approved Version 1 remains operational at KES 455,000,000
- Draft Version 2 totals KES 535,000,000

Do not seed treatment rows, contribution rows, routine Planning-stage HoD decisions or cosmetic `Keep separate` values.

Use isolated automated-test fixtures, rather than new permanent canonical seed records, to prove same-OU compatible combination and rejection of incompatible combinations.

---

# Cursor Prompt 01 — Scope, task authority and route protection

```text
Read completely:
- KenTender_MVP_Cross_Module_Operating_Model_v1.1.md
- Procurement_Planning_MVP1_Requirements_v1.9.md
- Procurement_Planning_MVP1_Stitch_Prompts_v2.0.md
- Procurement_Planning_MVP1_Cursor_Implementation_Pack_v1.8.md

Implement the Planning security correction first.

Inspect existing:
- PE/OU User Scope Assignment logic;
- Planning roles and capabilities;
- workspace/list/detail/task routes;
- whitelisted service methods;
- client action visibility;
- Administrator special cases; and
- role-based tests.

Implement one shared server-side authorisation pattern that distinguishes:
1. record visibility;
2. current task visibility; and
3. mutation authority.

PE/OU behaviour:
- zero eligible operational scopes blocks Planning use with a clear message;
- one eligible PE/OU remains visible and explicit;
- multiple eligible PEs require deliberate PE selection, followed by an eligible OU where the task requires it;
- never choose the first assignment silently;
- never fall back to PE-MOH or another seed fixture;
- Administrator status alone gives no operational scope or Planning authority;
- an Administrator may receive explicit operational assignments like any other user;
- lists, counts, queues, exports, reports and notifications use the same scope predicates;
- validate stored PE/OU against the actor's capability server-side on mutation.

Task protection:
- do not render Review, Approve, Return, Confirm funding or similar actions for users without the current task capability;
- reject direct task-route navigation server-side;
- reject direct API mutation calls server-side;
- permit neutral read-only detail only when record visibility exists;
- show permitted completed decision history on neutral detail, not a disabled task form.
- show Plan Item removal only to a scoped Procurement Planner with Draft mutation authority; reject direct removal calls for viewers, other roles, cross-scope records and executed items.

Cover PLN-UI-01, PLN-UI-02, PLN-UI-07, PLN-UI-07A and PLN-UI-08 route/action guards.

Add positive and negative tests for Requester, HoD, Planner, Budget Officer, Head of Procurement, Viewer and Administrator without operational assignment across MoH and Kisumu.

Do not implement the remaining workflow yet. Return changed files, the common guard used and focused test results.
```

**Section acceptance**

- No silent scope fallback remains.
- Administrator has no implicit Planning persona.
- Requester cannot see or open Finance/review task forms.
- Cross-PE lists and direct URLs are denied.

---

# Cursor Prompt 02 — Remove superseded structures and restore the clean domain

```text
Inspect all schema, controllers, routes, services, fixtures, reports and tests referencing:
- Departmental Submission;
- Departmental Contribution;
- contribution status or submit contribution;
- planning-stage OU_SIGNOFF or routine HoD sign-off;
- statutory_allocation_treatment;
- statutory_rationale;
- planned_treatment_value;
- value_treatment_note;
- generic Strategy treatment;
- item-level preference/reservation scheme, target group or planned reserved value from the superseded editor; and
- default/cosmetic aggregation_decision = Keep separate.

Correct the MVP implementation directly:
- remove the Departmental Submission record and contribution workflow;
- remove its services, capability, hard readiness gate, queue actions, seed data and tests;
- remove generic treatment fields and persistence;
- remove item-level preference/reservation inputs from the Plan Item editor and payload;
- remove zero/placeholder treatment records;
- remove cosmetic Keep separate defaults;
- remove routine Planning-stage HoD task generation;
- remove duplicate Demand-stage Finance approval if it represents the same funding sign-off now required after Planning.

Retain and verify:
- Procurement Plan;
- Procurement Plan Version;
- Procurement Plan Item;
- Procurement Plan Item Version;
- Plan Demand Allocation;
- Plan Decision;
- Plan Validation Result;
- Publication Event/evidence; and
- Planning Handoff Snapshot.

Enforce domain invariants:
- one logical Plan per PE/FY;
- at most one current Approved Version;
- at most one open Draft successor;
- Approved/Superseded/Cancelled Versions immutable;
- stable Plan Item identity across Versions;
- Draft allocations do not consume planning availability;
- approval makes allocations effective exactly once;
- same-PE allocation enforcement;
- Proposed/Active/Removed item states;
- Proposed-removal as a Draft-Version change projection, not an in-place Active-item status mutation;
- optimistic concurrency and double-submit protection.

Use clean teardown/reseed for disposable MVP data. Do not build migration compatibility layers or aliases.

Add schema/invariant tests and a repository search proving the removed structures have no active callers. Report exact removals and retained records concisely.
```

**Section acceptance**

- No active contribution/treatment structure remains.
- No replacement workflow has been invented.
- Core Plan/version/item/allocation history model remains intact.

---

# Cursor Prompt 03 — Workspace, Plan registration and Plan formation

```text
Implement PLN-UI-01, PLN-UI-02, PLN-UI-03, PLN-UI-04 and PLN-UI-05 from Stitch v2.0 using native KenTender/Frappe pages and the existing shell.

PLN-UI-01:
- explicit authorised PE and FY context;
- current Plan projection;
- compact live work queue;
- no dashboard charts, contribution status or duplicate role workbenches.

PLN-UI-02:
- PE required searchable select for multi-scope user;
- one PE visible read-only; zero PE blocked;
- financial year controlled select;
- Plan period derived read-only;
- title text input;
- Currency controlled select/read-only for one option;
- coordinating procurement unit authorised OU select and not assumed to be the lowest OU;
- no Budget context field;
- internal references generated server-side.

PLN-UI-03/05:
- compact Plan Items table, totals, validation and Finance-confirmation projections;
- show Continue as the primary row link and a scoped overflow action Remove from draft for a removable draft-only Proposed item;
- open PLN-UI-05A for confirmation; never issue the mutation from the menu click itself;
- no Departmental Contribution or HoD sign-off action;
- no manual blank Plan Item grid or package/release objects.

PLN-UI-04 direct formation path:
- allow one or more authorised Approved, Planning Ready and not-fully-planned Demands to be selected with checkboxes;
- show owner OU, Approved value, requested date, proposed Budget Line and Planning Ready status read-only;
- do not require completed Finance approval or reservation for eligibility;
- source breakdown shows every selected Demand and its Need Items read-only;
- with one selected Demand, hide formation controls and form exactly one Proposed Plan Item with one Draft allocation per available Need Item;
- with multiple selected Demands, require `formation_mode = separate | combined` before confirmation;
- `separate` creates one actual Proposed Plan Item per selected Demand;
- `combined` creates one Proposed Plan Item whose allocations preserve every selected Demand and Need Item;
- enable `combined` only where all selected Demands share the Plan PE and owning OU and satisfy compatibility checks;
- disable or reject `combined` for mixed OUs, conflicting categories, incompatible timing or other configured incompatibility;
- require a concise formation reason when `combined` is selected;
- preview the exact resulting item count and value before confirmation;
- submit the whole selection through one server capability and one atomic transaction;
- on an Approved Plan, create or reuse the single Draft successor and create all resulting items/allocations in that same transaction;
- route a single or combined result to PLN-UI-06; route multiple separate results to PLN-UI-05 or PLN-UI-10 with the new items visible;
- no create-one-then-return, Add another Demand or later aggregation step;
- no method, schedule or lotting controls in the dialog.

Implement empty/loading/error states and browser tests for scope states, source eligibility, atomic formation, double-click and back/refresh behaviour.

Do not implement PLN-UI-06 yet. Return changed files, actual service names and test results.
```

**Section acceptance**

- Demand selection and formation happen once in PLN-UI-04.
- One selection creates one item; multiple selections create exactly the chosen separate or combined structure.
- Approved-Plan addition creates/reuses one Draft successor and all resulting items atomically.

---

# Cursor Prompt 04 — Focused Plan Item editor

```text
Implement PLN-UI-06 exactly from Stitch v2.0.

The page opens an existing Proposed Plan Item created by PLN-UI-04.

Read-only Approved source:
- one or more source Demands and their Need Items;
- owner OU;
- approved scope/value and requested delivery;
- proposed Budget Line and current Finance state;
- inherited Strategy targets and Strategy Value Commitments.

Editable procurement-owned fields only:
- Plan Item description, multiline;
- Category, governed searchable select;
- Confirmed method, governed select;
- Arrangement, governed select;
- indicative lotting decision;
- conditional expected lot count and lot basis;
- governed milestone date inputs.

Derived read-only fields:
- governing regime;
- recommended method; and
- method basis.

If confirmed method differs from the recommendation, show only the applicable configured grounds and required reason/evidence. Hide these fields when the recommendation is accepted.

Enforce:
- source Demand is not selected, recreated or reallocated on save;
- owner OU, business scope, quantity, delivery requirement and approved value cannot be changed;
- attempted material change returns a stable instruction to amend/reapprove the Demand;
- date chronology and required fields;
- no source-selection or formation decision in the editor;
- no Departmental Contribution or HoD sign-off;
- no generic statutory/Strategy treatment controls;
- no item-level preference/reservation scheme, target-group or planned-value controls;
- no Plan-level coverage placeholder;
- no detailed Tender lots, STD configuration or approval settings.

Footer actions:
- Save draft persists only the Draft Plan Item Version;
- Save and request Finance confirmation validates Planning completeness, creates/reuses one Finance task idempotently and returns the Plan/update projection.

For a combined Plan Item, show read-only source rows, the combined total and the formation reason recorded by PLN-UI-04. Do not allow sources to be selected, added, removed, regrouped or reallocated here.

Add unit, transaction and Playwright tests for the exact field register, input types, conditional fields, source immutability and save idempotency.
```

**Section acceptance**

- PLN-UI-06 contains only defensible planning fields.
- It never repeats Demand selection.
- Formation has already been completed once in PLN-UI-04.

---

# Cursor Prompt 05 — Finance confirmation and professional approval

```text
Implement PLN-UI-07, PLN-UI-07A and PLN-UI-08 and their workflow services.

PLN-UI-07 Finance task:
- task becomes available only after Plan Item Planning completeness;
- open from Finance work queue or authorised item task action;
- show Plan Item/version, source Demand allocation, proposed Budget Line, amount, current availability and derived post-confirmation balance;
- decisions: Confirm funding or Return to planner;
- return reason required; confirmation note optional;
- confirmation atomically revalidates availability, creates/confirms the reservation and records actor, role, time and Plan Item/version context;
- repeated identical confirmation is idempotent;
- allocation or relevant value change makes the confirmation Stale;
- do not retain an earlier Demand-stage decision as a second Finance sign-off;
- do not allow Requester, Planner, HoD, Viewer or Administrator-without-task to see/open/call this task.

PLN-UI-07A shortfall state of the same task:
- enter this state whenever live current availability is below the full amount required;
- show amount required, current availability and the exact calculated shortfall;
- keep Finance status Awaiting confirmation unless the officer returns the item;
- omit the Confirm funding action and reject direct confirmation API calls with a stable insufficient-funding error;
- do not partially confirm, create a partial reservation, permit a negative balance, override availability or silently reduce the Plan Item amount;
- provide a governed route to Budget & Funding for an authorised Budget Officer to resolve the allocation;
- do not mutate a Budget Line or allocation inline in the Planning task;
- opening Budget & Funding creates no Finance decision and no duplicate task;
- after governed funding resolution, revalidate this same task and expose the ordinary PLN-UI-07 state only when the full amount is available;
- permit Return to planner with a required reason; Return is remediable and is not a final rejection;
- if scope or approved value must change, direct the planner to the Demand amendment/reapproval path.

Use existing Demand Funding Allocation, Budget check/reservation service and decision/audit foundations. Do not create a generic Finance approval engine or another Finance workbench.

Validation:
- Plan Item source eligibility and allocation arithmetic;
- PE/OU scope;
- method/conditional basis;
- schedule chronology;
- aggregation/anti-splitting;
- current Finance confirmation;
- Plan/version concurrency and handoff integrity;
- derived preference/reservation coverage only when a governed supported source exists.

If no supported coverage source remains after the treatment cleanup, omit the coverage section and do not create a zero/Not applicable placeholder or block approval.

submit Plan for review:
- require every included item complete and valid;
- require current Finance confirmation for every applicable item;
- require no blocker;
- require post-approval-addition reason where applicable;
- do not require Departmental Submission, contribution or routine HoD sign-off.

PLN-UI-08 professional task:
- authorised Head of Procurement/configured professional authority only;
- show Plan/version summary, Plan Items, issues, Finance status, supported derived coverage and decision trail;
- decisions: Return to planner or Approve Plan;
- return reason required; approval comment optional;
- no editable Plan Item fields;
- neutral viewers use a separate read-only detail state without task buttons.

Approval must atomically:
- lock the Plan Version and Plan Item Versions;
- make Draft allocations effective exactly once;
- activate Proposed items;
- apply approved removals;
- supersede the previous current Approved Version when applicable;
- preserve unchanged item identity/handoffs; and
- create decision and audit evidence.

Add role/scope Playwright tests and transactional tests for sufficient confirmation, exact shortfall display, pending resolution, return, direct-API denial, no partial reservation, recovery on the same task, staleness, submission, approval, retries and concurrency.
```

**Section acceptance**

- Exactly one Finance confirmation follows Planning.
- A shortfall is an explicit non-confirmable state of that same task, not a second workflow.
- Head of Procurement cannot review stale/unconfirmed funding.
- No routine second HoD gate exists.
- Unauthorised task forms are inaccessible, not disabled.

---

# Cursor Prompt 06 — Approved Plan, Draft successor, publication and Tender handoff

```text
Implement PLN-UI-09 and PLN-UI-10 plus the downstream boundaries.

PLN-UI-09:
- current Approved baseline read-only;
- implementation and actual milestones derived from downstream records;
- show reporting period, As at, totals, publication and variance as projections;
- Add Plan Item available only for an Open Plan and authorised planner;
- user never creates a revision manually;
- existing Draft successor shown as one Continue update / View changes notice;
- existing Active items and Tenders remain operational during revision.

Approved-Plan Add path:
1. PLN-UI-09 Add Plan Item opens ordinary PLN-UI-04.
2. The planner selects one or more eligible Approved Demands and, for multiple selections, chooses separate or compatible combined formation.
3. One atomic confirmation creates/reuses the Draft successor and creates every resulting Proposed Plan Item/allocation.
4. Open PLN-UI-06 for the single/combined item, or PLN-UI-10 with all separate items visible, without repeating source selection or formation.
5. Complete each new item and request Finance confirmation.
6. PLN-UI-10 shows each changed item as Awaiting confirmation until PLN-UI-07 confirms it.
7. Once all changed items are current and Finance-confirmed, PLN-UI-10 enables Submit for review.
8. PLN-UI-08 approves the successor.

PLN-UI-10:
- show Approved Version 1 and Draft Version 2 totals;
- make added/changed Plan Items primary;
- show unchanged operational items as collapsed read-only context;
- require one concise reason for the post-approval change;
- show Finance/validation per changed item;
- show Remove from update for a removable draft-only item and Proposed removal for an eligible carried-forward Active item;
- do not expose version-management controls, formation controls, raw diffs, second HoD sign-off or editable Approved fields.

PLN-UI-05A and removal service:
- use one compact confirmation dialog from PLN-UI-05/10 and from an eligible Active-item row on PLN-UI-09;
- require one non-empty business reason and show item, owner OU, value, all source Demands, Finance state and the exact lifecycle effect read-only;
- the public capability accepts Plan, Draft Version, Plan Item, expected version/concurrency token and reason; it derives the removal mode and financial effects server-side;
- never accept client-supplied release amount, Demand-eligibility flag, item status or `has_downstream` authority;
- for an item created only in the editable Draft, atomically mark it Removed/excluded, preserve an audit tombstone and source allocations, cancel any open Finance task, reverse any draft-stage Finance confirmation through the governed service, release its reservation once, and restore every source Demand allocation to Planning eligibility;
- for an Active item in the current Approved Version, create/reuse the Draft successor and record Proposed removal only; keep the current item, reservation and source ineligible/operational until successor approval;
- on successor approval, recheck there is no Tender handoff, commitment or other downstream execution, then atomically mark the item Removed in the successor, release only the unconsumed reservation and restore source eligibility;
- if downstream execution exists at request time, omit the action and reject direct calls with a stable business error; if it appears concurrently before approval, block successor approval and show a business-readable validation issue;
- remove a combined Plan Item only as a whole; do not add source-level removal to PLN-UI-06 or PLN-UI-05A;
- recalculate Draft counts, totals, Finance counts and validation after success;
- if no effective Draft changes remain, return `no_changes_remain = true`, block no-op submission and offer Cancel update;
- use idempotency and optimistic concurrency so retry/double-click cannot duplicate release, eligibility restoration or audit events;
- never hard-delete Plan Item, Plan Item Version, Plan Demand Allocation, Finance decision or audit evidence.

Publication:
- publish/export current Approved Version only;
- retain destination, status, time and evidence;
- publication failure creates an issue without reversing approval.

Tender handoff:
- eligible Active item in current Approved Version only;
- current funding/reservation and remaining take-up required;
- atomically create one immutable Planning Handoff Snapshot;
- preserve Plan/item/version, Demand allocations, Finance/reservation and Strategy lineage;
- do not create Release Package or manual Consumed actions.

Prove the canonical post-approval scenario:
- one Draft Version 2 at KES 535,000,000;
- PPI-MOH-2027-022 at KES 80,000,000;
- Approved Version 1, PPI-MOH-2027-021 and TND-MOH-2027-008 remain operational until approval;
- Finance confirmation follows new-item completion;
- successor approval supersedes V1 and activates the new item without duplicating unchanged handoffs.

Prove removal separately:
- run `SCN-PLN-REMOVE-001` before Finance confirmation and remove `PPI-MOH-2027-022` from Draft Version 2;
- Draft total returns from KES 535,000,000 to KES 455,000,000, `DMD-MOH-2027-019` is eligible again, and Approved Version 1 plus `TND-MOH-2027-008` remain unchanged;
- add transactional tests for the Finance-confirmed draft-only branch and the Active-item proposed-removal branch without altering the canonical base story.

Add service, transaction and Playwright tests for the complete route, removal variants, refresh/back, double-submit, concurrency and publication/Tender contracts.
```

**Section acceptance**

- Plan revision is quiet governance context, not a user workbench.
- Existing procurement execution is not suspended.
- Tender take-up uses immutable approved lineage.

---

# Cursor Prompt 07 — Canonical seed, regression suite and close-out

```text
Rebuild and verify the canonical Strategy → Budget → Demand → Planning story against `KenTender_MVP_Canonical_Demo_Data_Contract_v2.7.md` and the approved operating model.

Seed:
- make the approved canonical Strategy seed the single ordinary source;
- preserve Ministry of Health principal story and minimal Kisumu isolation story;
- preserve KES 480m Budget Line, KES 455m principal Demand/item, KES 310m commitment and KES 145m remaining reservation;
- preserve KES 95m Returned history and KES 80m corrected Demand;
- preserve Draft Version 2 at KES 535m while Approved Version 1 remains operational;
- seed explicit PE/OU assignments for Requester, HoD, Planner, Budget Officer, Head of Procurement and Viewer;
- seed HoD approval before Planning;
- seed Finance confirmation after Plan Item completion;
- implement optional resettable `SCN-PLN-FUND-SHORT-001` exactly as defined in the canonical contract: KES 80m required, KES 25m available and KES 55m shortfall on `PPI-MOH-2027-022`;
- implement optional resettable `SCN-PLN-REMOVE-001` exactly as defined in the canonical contract: remove Proposed `PPI-MOH-2027-022` before Finance confirmation, return `DMD-MOH-2027-019` to eligibility and restore the Draft total to KES 455m without changing Approved Version 1 or its Tender;
- keep the shortfall hold scenario-owned and absent from the successful base seed;
- remove all treatment, contribution, routine Planning-HoD and cosmetic Keep separate fixtures;
- keep unrelated works-master data opt-in.

Run the seed/reset twice and prove idempotency and arithmetic.

Run final verification:
1. schema and active-reference search for removed structures;
2. unit and transactional tests;
3. role/scope matrix including negative direct-route/API tests;
4. service contract tests;
5. Playwright journeys PLN-UI-01 through PLN-UI-10;
6. initial Plan journey;
7. post-approval-addition journey;
8. multi-Demand separate formation, compatible same-OU combined formation and cross-OU combined rejection;
9. Finance confirmation/staleness;
10. Head-of-Procurement approval and unauthorised viewer behaviour;
11. publication and Tender handoff;
12. PLN-UI-07A shortfall, no-override/no-partial-confirmation and same-task recovery tests;
13. accessibility checks for labels, keyboard, focus and error association.
14. draft-only removal before/after Finance confirmation, Active-item proposed removal, executed-item denial, whole-combined-item removal, no-op Draft handling, double-submit and approval-time race tests.

Produce one concise completion report only:
- capability → actual public service name;
- requirement/acceptance ID → implementation location → automated test/result;
- changed/removed files and schema;
- commands used;
- genuine deferred integrations or blockers.

Do not create another audit directory or documentation-recovery project. Do not mark completion from an Administrator smoke test or screen rendering alone.
```

**Section acceptance**

- Seed is repeatable and entity-isolated.
- Removed concepts have no active references.
- Positive and negative tests prove the complete actor journey.

## 7. Definition of done

Procurement Planning MVP 1 is corrected when:

- the complete Stitch v2.0 set, including PLN-UI-05A removal and PLN-UI-07A shortfall states, is backed by live scoped services;
- one selected Demand creates one Plan Item, while multiple selected Demands create exactly the confirmed separate or compatible combined structure;
- PLN-UI-06 never repeats source selection;
- Plan Items contain only admitted planning fields;
- Finance confirms once after Planning only when the full amount is available; shortfalls cannot be overridden or partially confirmed;
- Head of Procurement reviews only current, Finance-confirmed work;
- no contribution, routine second HoD or generic treatment structure remains;
- restricted task forms/actions are absent and server-denied for unauthorised roles;
- Approved Versions are immutable and remain operational during revision;
- Plan Item removal is whole-item, audited and version-correct; draft-only removal reverses draft effects, Active removal waits for successor approval, and executed items are protected;
- compatible combination is explicit in PLN-UI-04 and cross-OU combination is rejected;
- Tender handoff uses one immutable approved snapshot;
- canonical seed and post-approval scenario rerun without duplicates; and
- the final traceability report proves every claimed requirement with automated evidence.
