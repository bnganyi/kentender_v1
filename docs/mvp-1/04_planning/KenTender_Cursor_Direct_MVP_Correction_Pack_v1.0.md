# KenTender Cursor Direct MVP Correction Pack

**Document ID:** KENTENDER-CURSOR-DIRECT-CORRECTION-1.0  
**Version:** 1.0  
**Date:** 11 August 2026  
**Status:** Approved for direct MVP implementation  
**Authority:** Approved Cross-Module Operating Model v1.0 and Direct Correction Backlog v1.1

## 1. Execute the correction

Correct the existing KenTender implementation directly. Do not produce another plan, audit pack, repository-baseline project or migration programme before editing the product.

The current seed data is disposable MVP data. Use clean teardown/reseed where this avoids compatibility scaffolding. Preserve the working domain foundations identified as `Keep` in the Cursor disposition audit.

Work only inside the KenTender source and its existing requirements/tests. Do not modify unrelated apps, site credentials or user files.

## 2. Controlling sources

Read and apply:

1. `KenTender_MVP_Cross_Module_Operating_Model_v1.0.md` — approved;
2. `KenTender_MVP_Correction_Control_and_Backlog_v1.1.md` — approved;
3. `KenTender_MVP_Semantic_and_Workflow_Assurance_Audit_v1.1.md` — accepted correction audit; and
4. the Cursor audit outputs `00`–`09` for exact implementation locations.

Where older requirements, Stitch prompts, Cursor packs, trackers or tests conflict, the approved Operating Model and Backlog prevail.

## 3. Working rules

- Implement changes; do not return another proposed plan.
- Do not preserve incorrect concepts through aliases, hidden fields or compatibility services.
- Use existing DocTypes and services where they remain semantically correct.
- Do not add a new module, workbench, dashboard or generic workflow engine.
- Do not ask the product owner to decide questions already closed in Backlog v1.1.
- Make the smallest coherent code change that produces the approved journey.
- Run the focused tests after each correction area and the cross-module tests at the end.
- If an ordinary quick backup/checkpoint already exists, use it without creating a side project. Do not block implementation on Wave 0A/0B.

## 4. Correction A — PE/OU scope and task authority

### 4.1 Remove fallbacks

Correct the actual implementations identified by the audit, including:

- `budget_permissions.entity_for_user`;
- Budget multi-PE sorted-first behaviour;
- Home PE-MOH/PE-MOE preference or fallback;
- Strategy list behaviour when PE cannot be resolved; and
- live JavaScript defaults that pin MoH Budget or Strategy records.

Required behaviour:

| Eligible operational scopes | Behaviour |
|---|---|
| Zero | Block the operational task and explain that scope assignment is required |
| One | Use it but display it explicitly |
| Multiple | Require deliberate PE and, where applicable, OU selection |

Never derive record ownership from the first assignment, first sorted PE, current workspace filter or Administrator status.

### 4.2 Remove Administrator role inflation

Administrator alone grants system administration, not Strategy, Budget, Demand or Planning business authority. Remove implicit module-role expansion in Strategy and Budget. An Administrator may act operationally only through an explicit role and User Scope Assignment.

### 4.3 Separate record view from task form

For Strategy, Budget, Demand and Planning:

- show workflow actions only when the actor has the current task capability;
- reject unauthorised task loaders and APIs server-side;
- do not render an approval/review form with disabled controls; and
- retain a separate neutral read-only detail route for users with record-view authority.

Add negative tests for direct URL, loader/API and action projection.

## 5. Correction B — remove unsupported structures

### 5.1 Budget

Remove:

- `Budget Line Value Treatment` DocType/child usage;
- Dedicated/Embedded/N/A treatment options;
- generic treatment rationale;
- activation/readiness rules requiring treatment rows;
- treatment UI; and
- treatment seed/test data.

Retain Budget, Budget Line, optional supported Strategy links, Reservation, Commitment foundation, activation arithmetic and revision.

### 5.2 Demands

Remove:

- `Demand Value Treatment`;
- generic value-treatment UI/services/seeds/tests;
- Demand-owned `aggregation_treatment` and package-formation rationale; and
- any Requester requirement to select Strategy, Budget, procurement method, aggregation or lots.

Retain Demand, Need Items, explicit PE/OU, Strategy references assigned by the authorised enrichment role, HoD decision history and proposed funding context.

### 5.3 Procurement Planning

Remove completely:

- `Departmental Submission` DocType and seed rows;
- `submit_departmental_contribution`;
- `get_departmental_contribution`;
- PLN-UI-07 contribution drawer/page bindings;
- Planning Contributor contribution capability;
- contribution prerequisite and error copy in `submit_plan_for_review`;
- contribution fixture preparation and helper calls;
- `ui-planning-contribution-gate`; and
- tests whose only purpose is to prove the removed workflow.

Do not create `OU_SIGNOFF`, `record_ou_plan_signoff` or a replacement contribution screen.

Finish removal of retired Plan Item statutory/treatment fields after confirming they contain only disposable MVP data. Preserve named preference/reservation fields that drive the concrete coverage projection.

## 6. Correction C — restore the actor flow

Implement exactly:

> Requester → HoD Demand approval → Procurement Planner → Finance/Budget Officer → Head of Procurement → Tender-ready Plan Item

### 6.1 Demand boundary

- Requester submits the business need.
- HoD approves or returns it.
- HoD approval makes the Demand Approved and Planning Ready.
- Finance confirmation is not a prerequisite for HoD approval or Planning selection.
- Demand may carry proposed funding context but not completed Finance approval before Planning.

### 6.2 Planning boundary

- Planner selects one eligible Approved Demand through Add Plan Item.
- One selection creates one Draft Plan Item and source allocation by default.
- The Plan Item editor shows the approved source read-only and does not select the Demand again.
- Planner completes procurement description, method, arrangement, schedule and indicative lots.
- Planning cannot edit owner OU, business scope, quantity, delivery requirement or approved estimated value.
- If those facts must change, direct the user to amend the Demand and repeat HoD approval. Do not build a Planning reapproval workflow.

### 6.3 Finance confirmation

Provide one Budget Officer task after Plan Item completion.

Use the existing Demand Funding Allocation, Budget check/reservation service and Demand Decision/audit foundations rather than introducing a new Finance workbench or generic approval engine.

The task shall:

- open from the completed Plan Item or Finance work queue;
- show the Plan Item, source Demand allocation, proposed Budget Line, amount and current availability;
- allow Confirm funding or Return to planner;
- create or confirm the reservation atomically on confirmation;
- record the Budget Officer, time and Plan Item/version context in the existing audit trail;
- invalidate confirmation when the funding allocation or relevant Plan Item value changes; and
- be inaccessible to Requesters and other unauthorised roles.

Reuse the existing Budget Confirmation UI/components where practical, but change its entry point, timing and task guard. Do not retain an earlier Demand-stage Finance approval as a second sign-off.

### 6.4 Professional review

`submit_plan_for_review` shall require:

- a complete and valid Plan Item/Version;
- current Finance confirmation and reservation for every applicable source allocation; and
- no unresolved blocking validation issue.

It shall not require Departmental Submission, contribution or routine HoD planning sign-off.

PLN-UI-08 remains the professional review/approval screen. It must show only:

- plan/version summary;
- Plan Items and validation issues;
- funding-confirmation status;
- derived **Preference and reservation coverage**; and
- authorised review/return/approve actions.

Remove contribution and generic statutory-treatment language.

## 7. Correction D — plan formation and revision

Retain:

- one Demand → one Plan Item by default;
- empty aggregation decision for the ordinary single-source case;
- explicit Combine only when another compatible Approved Demand is deliberately added;
- actual separate Plan Items when sources are kept separate;
- indicative lots within one Plan Item; and
- quiet creation/reuse of one Draft successor for an Approved Plan.

For MVP, permit aggregation only when Demands share the same PE and owner OU and are otherwise compatible with the same planned procurement. Reject or keep separate cross-OU candidates. Do not add a cross-OU approval workflow.

The current Approved Plan Version and existing Tender handoffs remain operational until the Draft successor is approved.

## 8. Correction E — Strategy

### 8.1 Terminology and domain

Replace `Plan Value Commitment` with **Strategy Value Commitment** across:

- DocType and child-link names where applicable;
- Python and JavaScript APIs/symbols;
- routes and user-facing copy;
- Budget and Demand references;
- seeds; and
- tests.

Because this is MVP with disposable seed data, perform a clean rename/rebuild. Do not create a permanent dual-name compatibility layer.

### 8.2 Codes and scope

- keep server-generated references;
- remove code entry from ordinary user forms;
- display titles and hierarchy paths; and
- allow external source references only when provided by an authoritative source.

### 8.3 Active-plan rule

In MVP, allow only one Active primary Strategic Plan for the same PE where effective dates overlap. Activation of a competing overlapping primary plan must be blocked or explicitly supersede the current plan according to the existing controlled transition.

Supporting-plan overlap is deferred; do not add plan-type complexity merely to support it now.

### 8.4 Deferred Strategy scope

Remove generic PVO applicability and advanced Strategy Performance surfaces from ordinary MVP navigation. Do not delete Strategy Value Commitments, targets, measurements or existing core performance evidence.

## 9. Correction F — canonical seed

Update the existing canonical orchestrator and validators directly.

Preserve:

- MoH principal Budget Line: KES 480,000,000;
- principal Demand/Plan Item: KES 455,000,000;
- commitment fixture: KES 310,000,000;
- remaining reservation fixture: KES 145,000,000;
- returned Demand history: KES 95,000,000;
- corrected current Demand: KES 80,000,000;
- Draft Revision 2: KES 535,000,000 while Version 1 remains operational; and
- minimal County Government of Kisumu isolation story.

Change:

- remove Budget/Demand treatment rows;
- remove Departmental Submission/contribution rows;
- rename Strategy Value Commitment fixtures;
- make `kentender_mvp_v1_strategy` the canonical Strategy seed;
- make works-master Strategy data opt-in only;
- seed HoD approval before Planning;
- seed Finance confirmation after Plan Item completion; and
- ensure Requester, HoD, Planner, Budget Officer and Head-of-Procurement personas have explicit roles and scope.

Run the canonical seed twice and prove idempotency and arithmetic.

## 10. Tests and acceptance

Update or replace tests that assert removed behaviour. Do not simply delete coverage.

At minimum prove:

1. zero/one/multiple PE/OU behaviour;
2. Administrator without operational assignment cannot act;
3. unauthorised task route and API denial;
4. Requester creates and HoD approves a Demand without Finance approval;
5. one Demand creates one Plan Item without aggregation controls;
6. Budget Officer confirms funding after Plan Item completion;
7. Head of Procurement cannot review before current Finance confirmation;
8. contribution and treatment structures are absent;
9. explicit same-OU aggregation works and separate creates actual Plan Items;
10. Approved Version 1 remains operational during Draft Revision 2;
11. Strategy Value Commitment links survive the clean seed rebuild;
12. overlapping Active primary Strategy plans are prevented; and
13. two consecutive seed runs produce identical canonical results with MoH/Kisumu isolation.

Run the focused Strategy, Budget, Demand, Planning and cross-module suites. Report failures honestly; do not weaken assertions to obtain green tests.

## 11. Documentation cleanup

Update only the existing affected requirements, Stitch/Cursor references and trackers necessary to prevent the removed concepts from remaining authoritative.

Mark superseded Planning contribution and treatment instructions clearly. Do not generate a new family of process documents, audits or screen packs during this correction.

## 12. Completion report

Return one concise implementation report containing:

- files changed;
- structures removed;
- retained foundations;
- final workflow implemented;
- seed result;
- tests run and results;
- any genuine blocker; and
- any deferred item from section 13.

Do not create multiple audit reports.

## 13. Explicitly deferred

- annual departmental-plan certification;
- Planning contribution replacement;
- cross-OU aggregation;
- targeted HoD reapproval inside Planning;
- generic PVO rules engine;
- advanced Strategy/Demand/Funding dashboards;
- manual expenditure entry; and
- live reservation-to-commitment conversion before Tender/Contract work.
