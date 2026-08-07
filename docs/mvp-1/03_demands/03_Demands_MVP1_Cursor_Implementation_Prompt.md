# Demands — MVP 1 Cursor Implementation Prompt

**Document ID:** DEMAND-MVP1-CURSOR-1.1  
**Status:** Implementation input  
**Date:** 7 August 2026  
**Requirements baseline:** `DEMAND-MVP1-REQ-1.1` — locked and approved  
**Design baseline:** Approved Stitch outputs for `DEM-UI-01` through `DEM-UI-10`, including `DEM-UI-05A`  
**Seed baseline:** `KENTENDER_MVP_V1`, Canonical Demo Data Contract version 2.1 — approved  
**Application:** KenTender  
**Module label:** Demands  
**Implementation strategy:** Clean rebuild inside the existing procurement application boundary

## 1. How to use this document

This document contains two Cursor prompts:

1. **Prompt A — Read-only impact scan and implementation plan.** Run first. Cursor must inspect the repository and stop without changing code, schema or data.
2. **Prompt B — Execute the approved implementation plan.** Run only after Prompt A has been reviewed and approved.

Do not combine the two passes. The first pass is the safety and scope-control gate for removing disposable legacy Demand structures.

Make these inputs available to Cursor:

- `Demands_MVP1_Requirements.md`
- approved Stitch outputs for `DEM-UI-01` through `DEM-UI-10`, including `DEM-UI-05A`
- `Demands_MVP1_Stitch_Prompts.md` as design rationale
- `KenTender_MVP_Canonical_Demo_Data_Contract_v2.1.md`
- `KenTender_Procuring_Entity_and_Organisation_Scope_Model.md`
- current Strategy and Budget service contracts
- repository engineering instructions and established test commands

The requirements define behaviour. Approved Stitch outputs define presentation. The canonical data contract defines shared fixture identities and values. Legacy Demand code is dependency evidence only.

---

# Prompt A — Read-only impact scan and implementation plan

```text
Plan the clean implementation of KenTender Demands MVP 1.

AUTHORITATIVE INPUTS

Read completely before planning:

1. Demands_MVP1_Requirements.md
   - Document ID: DEMAND-MVP1-REQ-1.1
   - Status: Locked and approved
2. Approved Stitch outputs for DEM-UI-01 through DEM-UI-10, including DEM-UI-05A
3. Demands_MVP1_Stitch_Prompts.md
   - Document ID: DEMAND-MVP1-STITCH-1.1
4. KenTender_MVP_Canonical_Demo_Data_Contract_v2.1.md
   - Fixture bundle: KENTENDER_MVP_V1
   - Version: 2.1
   - Status: Approved baseline for implementation
5. KenTender_Procuring_Entity_and_Organisation_Scope_Model.md
6. Current Strategy and Budget service contracts and repository engineering instructions

If the locked requirements or any approved screen needed for implementation is unavailable, list the missing input and stop. Do not reconstruct it from legacy code.

DECISIONS ALREADY MADE

- The visible module name is Demands, not Demand Intake and Approval.
- This is a clean rebuild within the existing procurement module boundary.
- Existing MVP Demand records and conflicting Demand-specific legacy structures are disposable.
- The generic Procuring Entity and Organisation Unit model is mandatory.
- Requesters describe the business need and do not select Strategy, Budget, Planning or procurement-method codes.
- Business review is mandatory.
- Procurement enrichment assigns the Strategy target and public-value treatments.
- Budget matching may be automated, but a Budget Officer must confirm every funding assignment.
- Final approval is performed by the Procurement Approval Authority and atomically reserves funding.
- Approved Demands flow automatically to Planning; Planning usage does not rewrite Demand approval status.
- The shared KENTENDER_MVP_V1 fixture tells one cross-module story and must not be replaced by page-local seed data.

DO NOT PROPOSE

- an incremental legacy refactor merely to preserve disposable Demand data;
- a parallel V2 module, route, page, DocType, API or workflow;
- compatibility adapters, dual reads, dual writes or fallback queries;
- Ministry-, State-Department- or Directorate-specific schema fields;
- requester-owned Budget or Strategy selection;
- optional Budget Officer confirmation;
- an 11-step wizard or separate page for every review stage;
- an iframe, static Stitch HTML or page-level mock JSON;
- Administrator as the default operational approver;
- Demand approval creating a commitment, expenditure or procurement method; or
- duplicate fixtures for the same Demand at different lifecycle stages.

ARCHITECTURAL DIRECTION

- Keep the real KenTender/Frappe shell and Procurement navigation.
- Implement native Frappe records, server services and dedicated Desk pages using established repository patterns.
- Keep DocType controllers thin. Put cross-record business rules and lifecycle mutations in service modules.
- Enforce permissions, entity scope, organisational scope, transitions, validations and derived values server-side.
- Consume Strategy and Budget through their owned service contracts. Do not write Strategy or Budget records directly from Demand UI code.
- Use immutable approved snapshots and append-only decision/audit records.
- Use one Demand Review page whose sections and actions adapt to the current stage.
- Hand-port approved Stitch presentation into maintainable application components. Do not ship the generated shell or static fixtures.

YOUR TASK IN THIS PASS

Perform a bounded, read-only repository impact scan. Do not edit files, create migrations, reset data or run destructive commands.

Inspect only what is needed to answer:

1. Where is the current Demand domain implemented?
2. Which DocTypes, child tables, fields, routes, pages, APIs, hooks, permissions, workflows, notifications, fixtures and tests are obsolete or conflicting?
3. Which Strategy, Budget, Planning, Procurement Home and Analytics paths consume the current Demand model?
4. Which shared components and infrastructure should be retained?
5. Are there overlapping uncommitted user changes?
6. Where are the approved Stitch outputs and how will each screen map into the real application?
7. What repository-native migration, seed/reset and test mechanisms exist?
8. Does the current KENTENDER_MVP_V1 script already contain Demand records, and do they match the canonical references below?

Search explicitly for:

- Demand Intake and Approval labels;
- requesting_department, owner_state_department and owner_directorate fields;
- Pending HoD Approval and Pending Finance Approval workflows;
- requester Budget Line and Strategy selectors;
- Planned, Unplanned and Emergency route values;
- manual Planning Ready transitions;
- Demand-level procurement-method selection;
- direct Budget balance writes or commitment creation;
- duplicate reservation paths;
- Administrator-only test journeys;
- page-local Ministry mock JSON;
- obsolete Demand codes and fixtures; and
- Planning consumers that mutate Demand status or approved fields.

REQUIRED OUTPUT

Return one implementation plan with these sections:

A. Input confirmation
- Exact files and approved screen artifacts read.
- Any genuine conflict between requirements, approved design and the canonical data contract.
- Treat a visual omission as an implementation detail, not a functional contradiction.

B. Current implementation map
- Exact Demand module/app paths.
- DocTypes, child tables, controllers, services, pages, APIs, hooks, permissions, workflows, notifications, fixtures and tests.
- Strategy, Budget, Planning, Home and Analytics consumers.

C. Destructive target manifest
Provide a table containing:
- exact path or DocType;
- current purpose;
- action: Delete, Replace, Retain or Rewire;
- reason;
- known dependants; and
- post-change verification.

Do not target a whole site, database, repository, application or broad directory.

D. Clean target architecture
Map the locked domain to exact proposed records, services and pages. Include only the smallest framework-native structure required for:
- Demand;
- Demand Item;
- Demand Strategy Reference;
- Demand Value Treatment;
- Demand Funding Allocation;
- Funding Exception;
- Demand Decision;
- Planning Consumption; and
- immutable approved snapshot and append-only audit.

E. Workflow and permission map
Map Draft, In review, Returned, Approved, Rejected and Cancelled separately from Request preparation, Business review, Procurement enrichment, Budget confirmation, Final approval and Complete.

Show exact server-side action permissions for Requester, Business Approver, Procurement Approval Authority, Budget Officer, Planning Officer and Viewer/Auditor.

F. Integration contracts
Identify exact Strategy, Budget, Planning, core scope, notification and audit functions to reuse or implement. Confirm:
- Strategy suggests only active targets permitted by Strategy Scope Assignment;
- Procurement assigns one primary target or a controlled no-direct-alignment reason;
- Budget matching uses but never overwrites the Demand Strategy assignment;
- Budget Officer confirmation does not reserve funds;
- final approval uses the Budget-owned atomic reservation service; and
- Planning carries the same reservation identity forward.

G. Screen implementation map
Map each approved screen to exact files/components/controllers/services:
- DEM-UI-01 Demands workspace
- DEM-UI-02 Create/Edit Demand
- DEM-UI-03 Returned correction state
- DEM-UI-04 Business review
- DEM-UI-05 Procurement enrichment
- DEM-UI-05A Strategy target selector
- DEM-UI-06 Routine Budget confirmation
- DEM-UI-07 Budget exception
- DEM-UI-08 Final approval
- DEM-UI-09 Approved Demand detail
- DEM-UI-10 Demand performance

Confirm that DEM-UI-03 through DEM-UI-08 reuse shared form/review components rather than becoming unrelated pages.

H. Canonical fixture implementation plan
Map the approved version 2.1 records to the existing KENTENDER_MVP_V1 orchestrator and module-owned seed functions. Do not revise, reinterpret or duplicate the canonical fixture values. Identify any repository conflict with the approved contract and stop rather than silently changing the contract.

I. Execution sequence
Provide a short atomic sequence covering:
1. clean domain replacement;
2. permissions and workflow;
3. service integrations;
4. UI implementation;
5. canonical version 2.1 seed implementation;
6. automated tests; and
7. absence searches for legacy behaviour.

J. Verification matrix
Map every defined Demand acceptance criterion in the locked requirements (`DIA-AC-001` through `DIA-AC-024`; no `DIA-AC-009` is assigned) and the locked NFRs to exact unit, service, permission and browser test files.

K. Risks and blockers
Report only repository-specific blockers. Do not reopen approved product decisions.

L. Proposed change boundary
List exact files, DocTypes and fixture records to change, replace or delete after approval.

STOP CONDITION

Stop after the report. Make no code, schema, data or documentation change. Wait for explicit approval before Prompt B.
```

## Prompt A approval checklist

Approve the plan only if it:

- identifies exact legacy targets and downstream consumers;
- does not propose a parallel module or compatibility layer;
- preserves shared Strategy, Budget, Planning and core-scope infrastructure;
- maps every approved screen and acceptance criterion;
- preserves the real KenTender shell;
- extends `KENTENDER_MVP_V1` rather than inventing a Demand-only seed;
- treats the three named Demands as different stories, not duplicated screen mocks;
- identifies overlapping uncommitted user changes; and
- limits destructive work to exact Demand-owned disposable MVP structures and records.

---

# Prompt B — Execute the approved Demands clean implementation

```text
Execute the approved KenTender Demands MVP 1 implementation plan from the preceding impact scan.

Do not reopen the architecture decision or ask whether disposable legacy Demand data should be preserved. Work within the exact approved change boundary.

AUTHORITATIVE PRECEDENCE

1. DEMAND-MVP1-REQ-1.1 locked requirements
2. Approved Stitch outputs for DEM-UI-01 through DEM-UI-10, including DEM-UI-05A
3. Approved Prompt A impact and deletion plan
4. KENTENDER_MVP_V1 Canonical Demo Data Contract version 2.1
5. KenTender Procuring Entity and Organisation Scope Model
6. Current repository engineering conventions
7. Legacy Demand code only as dependency evidence

If requirements and an approved screen genuinely contradict each other, stop and report the exact conflict. Do not silently invent a compromise.

CHANGE DISCIPLINE

- Preserve unrelated user changes. Do not reset, overwrite or reformat unrelated files.
- Do not use destructive Git commands.
- Remove or replace only exact items approved in Prompt A.
- Never delete the whole site, database, repository, application or a broad directory.
- If an unexpected dependency expands the deletion boundary, stop and report it.
- Continue through ordinary implementation and test failures that remain inside scope.
- Do not leave TODOs, dead routes, parallel implementations or compatibility fallbacks for locked MVP requirements.

IMPLEMENTATION BOUNDARY

Implement:

- role-scoped Demands workspace;
- compact business-need capture and Need Items;
- Business review;
- Procurement enrichment;
- explicit Strategy target assignment and value-treatment confirmation;
- automatic Budget matching plus mandatory Budget Officer confirmation;
- Funding Exception resolution;
- final approval with atomic reservation;
- approved snapshot, cancellation/replacement and reservation release;
- Planning hand-off and usage projection;
- in-app work notifications and append-only audit;
- Demand Performance reporting;
- canonical deterministic seed data and tests.

Do not implement:

- procurement planning decisions or final procurement method;
- tender configuration, publication, bid, evaluation, award or contract workflow;
- Budget formulation, revision or accounting;
- Strategy maintenance inside Demands;
- contract commitment or expenditure mutation;
- email/SMS integration beyond established shared notification facilities;
- generic workflow builders, configurable approval chains or speculative analytics; or
- UI for technical identifiers and generated codes.

TARGET DOMAIN

Use the exact requirements as the field-level authority. Implement the smallest clean model that provides:

1. Demand
   - generated immutable reference;
   - procuring_entity and owner_org_unit;
   - optional delivery_org_unit;
   - requester, technical contact and business need fields;
   - route, dates, locations and requester estimate;
   - confirmed procurement category, estimate, currency and estimate basis;
   - workflow status, current stage and current owner;
   - approved baseline version/snapshot;
   - derived Planning Ready and Planning usage; and
   - original/replacement links and lifecycle metadata.

2. Demand Item
   - immutable child identity;
   - business description, quantity, unit, estimate, required date/location overrides;
   - procurement-confirmed values; and
   - derived planned and remaining quantity/amount.

3. Demand Strategy Reference
   - Primary or Supporting;
   - Strategy internal IDs, plan/version and full hierarchy path;
   - immutable human-readable snapshot;
   - selection source, actor, time and reason.

4. Demand Value Treatment
   - Plan Value Commitment identity/version/snapshot;
   - applicability, treatment, rationale, actor and time.

5. Demand Funding Allocation
   - Budget and Budget Line identities;
   - amount/currency;
   - Automatic or Budget Officer source;
   - check result/time and source freshness;
   - Budget Officer confirmation details;
   - reservation identity/status after approval; and
   - availability snapshots.

6. Funding Exception
   - type, candidate lines, diagnostics, owner, status, resolution and timestamps.

7. Demand Decision
   - stage, decision, actor/role, timestamp, comment/reason and decision-input snapshot.

8. Planning Consumption
   - Demand/Item, Plan Item/package, quantity/amount, reservation reference and reversal metadata.

Do not duplicate Frappe workflow/audit facilities where they satisfy the locked contract. Do create explicit domain records where immutable decision inputs, funding allocation history or cross-module traceability require them.

IDENTITY AND CODES

- Users never enter or maintain Demand, Strategy, Budget, organisation or item codes.
- Generate production Demand references server-side using the repository's entity-prefix and non-reusable sequence conventions.
- The named canonical references below are deterministic fixture values, not evidence that users maintain codes.
- Use internal immutable IDs for relationships and retain human-readable snapshots for historical display.

WORKFLOW

Keep status and stage distinct.

Statuses:
- Draft
- In review
- Returned
- Approved
- Rejected
- Cancelled

Stages:
- Request preparation
- Business review
- Procurement enrichment
- Budget confirmation
- Final approval
- Complete

Implement the standard path:

Request preparation -> Business review -> Procurement enrichment -> Budget confirmation -> Final approval -> Approved/Complete

Required controls:

- Return identifies the correction owner, affected section and reason.
- Resubmission preserves prior decisions and audit history.
- Business support is not final approval.
- Procurement enrichment must be complete before Budget confirmation.
- Budget Officer sign-off is mandatory for routine and exception matches.
- Material funding-relevant changes invalidate sign-off and return to Budget confirmation.
- Final approval and all reservations occur in one transaction.
- Failed reservation leaves the Demand unapproved with no partial reservation.
- Repeated approval is idempotent.
- Approved Demand baseline is immutable.
- Approved cancellation releases only unconsumed reservation through Budget services.
- Material post-approval change uses cancellation plus a linked replacement Demand.

SERVER SERVICE CONTRACTS

Implement or reuse repository-conformant services for:

- create_or_update_demand
- submit_demand
- record_business_decision
- enrich_demand
- suggest_strategy_context
- validate_strategy_reference
- suggest_funding_allocations
- confirm_demand_funding
- resolve_funding_exception
- approve_and_reserve_demand
- cancel_and_release_demand
- consume_demand_in_planning
- get_demand_audit

All mutations must:

- validate role, entity and Organisation Unit scope server-side;
- validate current status/stage and optimistic version;
- use stable error codes;
- write lifecycle decisions/audit in the same transaction where required; and
- return a fresh server projection for the UI.

Do not allow client code to mutate workflow fields, Budget balances, reservations, Strategy records or Planning consumption directly.

STRATEGY ASSIGNMENT

Implement the approved explicit assignment pattern:

- Procurement enrichment starts with Strategy alignment = Not assigned.
- Assign strategy opens the approved scoped target selector.
- Query only active/effective targets permitted through Strategy Scope Assignments for the Demand's procuring entity and owner Organisation Unit.
- Rank suggestions using entity, organisational scope, category and eligible Budget context, but do not auto-confirm.
- Show Why suggested from deterministic rule evidence, not generative text.
- Permit exactly one Primary target.
- Permit Supporting targets only with a reason.
- Permit No direct Strategy alignment only with a controlled reason.
- Snapshot the selected plan/version, full hierarchy and display text.
- Retrieve applicable Plan Value Commitments through Strategy services.
- Require treatment and rationale according to DIA-FR-067 through DIA-FR-069.

The later Budget recommendation may use the confirmed Strategy reference but must never assign, replace or silently change it. A mismatch is Needs attention and returns to Procurement for resolution.

BUDGET CONFIRMATION AND RESERVATION

- Call the Budget-owned matching service using entity, fiscal period, owner unit, category, currency, confirmed estimate and Strategy context.
- Store the recommendation separately from Budget Officer confirmation.
- Route every enriched Demand to a Budget Officer, even for one exact sufficient match.
- Mark no match, ambiguity, split funding or insufficient funding as a Funding Exception.
- Do not allow negative availability, placeholder lines, cross-entity lines or inactive lines.
- Require confirmed allocations to equal the approved estimate.
- Do not reserve funds during Budget confirmation.
- At Final approval, recheck the sign-off, scope, Strategy/value completeness, active line status and current availability.
- Reserve all allocations atomically through the Budget service.
- Reuse the Budget service's idempotency and concurrency controls; do not implement a second reservation ledger.

PLANNING HAND-OFF

- Approved Demands automatically appear in the permitted Planning intake projection.
- Carry the approved snapshot, remaining items/amount, Strategy/value context and the same reservation identity.
- Derive Not taken up, Partially planned or Fully planned from Planning Consumption records.
- Planning must not rewrite Demand status or approved baseline.
- Prevent over-consumption.
- Reversal returns unconsumed scope without duplicating or replacing the reservation.

PERMISSIONS AND SEGREGATION OF DUTIES

- Requester: create, edit and submit only owned Draft/Returned business fields; no specialist mutations.
- Business Approver: Support, Return or Reject assigned Demands; no funding or final approval.
- Procurement Approval Authority: enrich, assign Strategy/value context, send for Budget confirmation, make the final decision and authorise approved cancellation within scope.
- Budget Officer: review/adjust/confirm allocations and resolve/return funding exceptions; cannot approve the business need or final Demand.
- Planning Officer: consume only Approved, Planning Ready Demands in scope; no Demand baseline edits.
- Viewer/Auditor: authorised read-only views and audit.
- Administrator without an operational role: no business decision action.

Enforce procuring_entity and owner_org_unit on every server read and mutation. Do not rely on filtered lists or hidden buttons for security.

UI IMPLEMENTATION

Keep the real KenTender shell. Implement the approved main content only.

- DEM-UI-01: one role-aware workspace with compact filters, queues and next actions.
- DEM-UI-02 and DEM-UI-03: one compact Create/Edit form with a Returned correction state.
- DEM-UI-04 through DEM-UI-08: one shared Demand Review framework with stage-specific editable/read-only sections and actions.
- DEM-UI-05A: focused Strategy target drawer or modal using live Strategy search.
- DEM-UI-09: read-only approved/terminal detail with funding, Strategy, Planning usage and audit.
- DEM-UI-10: manager performance view backed by traceable queries and drill-down.

Do not reproduce Stitch's navigation, branding, static data or inactive fake controls. Use API-driven data, loading, permission, empty, error, returned and concurrency-conflict states.

CANONICAL SEED IMPLEMENTATION

Implement `KenTender_MVP_Canonical_Demo_Data_Contract_v2.1.md` exactly. It is an authoritative input, not a document for Cursor to redesign.

The three Demand anchors are:

- `DMD-MOH-2027-014` — approved Ministry digital-health infrastructure Demand, KES 455,000,000, linked to the approved Strategy targets, `MOH-BL-DHI-2027` and exactly one `RSV-MOH-0001`;
- `DMD-MOH-2027-019` — returned Ministry workforce Demand with a KES 15,000,000 funding shortfall and no confirmation or reservation; and
- `DMD-CGK-2027-006` — County Government of Kisumu Draft with no Strategy or Budget assignment.

All actors, Need Items, decisions, value treatments, amounts, dates, ownership, scope and downstream relationships must come from version 2.1. If implementation requires a different canonical value, stop and report the conflict; do not edit the approved contract inside this task.

FIXTURE ORCHESTRATION

- Extend the existing central KENTENDER_MVP_V1 orchestrator.
- Add module-owned Demand seed functions after Strategy and Budget and before Planning/Tender/Contract.
- Provide a supported “through Demands” seed boundary for Demand browser tests if the repository's fixture framework permits staged execution.
- A full bundle run must extend DMD-MOH-2027-014 using PPI-MOH-2027-021 and later downstream records rather than duplicate it.
- Lifecycle screen tests may transition or reset the same canonical Demand to deterministic checkpoints. They must not create separate page-local copies of DMD-MOH-2027-014.
- Reset fixture-owned records in reverse dependency order and preserve unrelated records.
- Rerun deterministically without duplicate Demands, decisions, allocations, reservations, consumptions, notifications or audit events.
- Print created, updated, skipped and failed counts plus invariant PASS/FAIL.

IMPLEMENTATION ORDER

1. Apply the approved destructive manifest and remove conflicting Demand-only legacy data/structures.
2. Implement clean schema and migrations.
3. Implement roles, permissions, scope and workflow validation.
4. Implement Demand-owned services and audit/decision records.
5. Wire Strategy suggestions and immutable references.
6. Wire Budget matching, mandatory confirmation and atomic reservation.
7. Wire Planning intake and consumption projections.
8. Implement DEM-UI-01 through DEM-UI-10 using shared review components.
9. Extend the central KENTENDER_MVP_V1 seed/reset and validation report from the approved version 2.1 contract.
10. Add unit, service, permission, concurrency and browser tests.
11. Run legacy-absence searches and produce the implementation report.

TEST REQUIREMENTS

Domain and workflow:

- reference generation and uniqueness;
- status/stage transition matrix, including invalid transitions;
- returned correction ownership and preserved history;
- approved baseline immutability;
- cancellation/replacement and partial release rules;
- Planning usage derivation and over-consumption prevention.

Strategy and value:

- active/effective scoped target search;
- cross-entity and unrelated-unit target exclusion;
- one primary target and reasoned supporting target rules;
- controlled no-direct-alignment reason;
- immutable snapshot after Strategy supersession;
- commitment applicability and required treatment validation;
- Budget context cannot overwrite the Demand target.

Funding:

- routine single match still requires Budget Officer confirmation;
- ambiguous, split, no-match and insufficient-funding exceptions;
- allocations equal approved estimate;
- inactive, stale-period, cross-entity and insufficient lines rejected;
- sign-off invalidation after material change;
- confirmation creates no reservation;
- final approval rechecks and reserves atomically;
- concurrent/repeated approval creates one reservation;
- failed multi-allocation reservation leaves no partial balance change;
- approved cancellation releases only unconsumed reservation.

Permissions:

- each role can see and perform only permitted actions;
- Administrator without an operational role cannot approve;
- Ministry unit isolation for protected Draft records;
- Ministry-to-Kisumu and Kisumu-to-Ministry UI/API denial;
- report/export scope matches record scope.

Canonical fixture:

- DMD-MOH-2027-014 resolves once and links to existing Strategy, Budget and reservation records;
- KES 455,000,000 equals the two Need Items and confirmed allocation;
- RSV-MOH-0001 is not duplicated;
- DMD-MOH-2027-019 produces exactly KES 15,000,000 shortfall and no reservation;
- DMD-CGK-2027-006 is Draft with no Strategy or Budget assignment;
- Demands-only boundary shows the principal Demand as Not taken up;
- full bundle uses the same Demand and reservation in downstream records;
- a second seed run changes no identities or counts;
- reset removes only fixture-owned Demand records;
- no page-local canonical fixtures remain.

Browser journeys:

- Requester creates and submits without Strategy/Budget/Planning codes;
- Business Approver supports and returns;
- Procurement enriches and explicitly assigns Strategy through DEM-UI-05A;
- routine Budget Officer confirmation;
- insufficient-funding exception and return;
- Final approval and atomic reservation;
- Approved Demand detail and Planning usage;
- role-scoped workspace counts and empty state;
- Demand Performance drill-down and As at context;
- County user cannot see Ministry Demand and vice versa.

Map every defined Demand acceptance criterion (`DIA-AC-001` through `DIA-AC-024`; no `DIA-AC-009` is assigned) to at least one automated test. Do not mark an acceptance criterion complete because a field or button exists.

LEGACY ABSENCE CHECKS

After migration and tests, search active code, schema, UI and fixtures for prohibited legacy concepts. Exclude archived reports and migration history from runtime absence claims.

Verify absence of:

- Demand Intake and Approval visible labels;
- Ministry-specific ownership fields;
- requester Strategy/Budget selectors;
- Pending Finance Approval as the operative workflow;
- Planned/Unplanned routes;
- manual Planning Ready mutation;
- Demand procurement-method selection;
- direct Demand writes to Budget balances;
- duplicate reservation services;
- page-local canonical fixture JSON;
- Administrator-only operational tests;
- legacy dual reads/writes and fallback queries.

FINAL VERIFICATION

Run repository-native:

- migrations/schema sync;
- targeted Demand unit and service tests;
- Strategy/Budget integration tests;
- role and cross-entity permission tests;
- fixture reset, seed, validation and repeatability tests;
- Playwright journeys for approved screens; and
- relevant existing regression suites.

Do not weaken tests or change expected values merely to obtain green results.

IMPLEMENTATION REPORT

Return a concise report containing:

1. Requirements and approved screens implemented.
2. Exact legacy items removed/replaced/rewired.
3. Final records, services, pages and routes.
4. Strategy, Budget and Planning integration contracts used.
5. Canonical contract version 2.1 implementation and seed validation summary.
6. Tests run with exact commands and PASS/FAIL results.
7. Legacy-absence search results.
8. Remaining blockers, if any, with exact evidence.
9. Files changed.

Do not call the module complete while any locked acceptance criterion is unimplemented, untested or represented only by static UI.
```

## 2. Final review checklist

Before accepting Cursor’s implementation, confirm that:

1. The module is labelled **Demands**.
2. Requesters enter only business-owned information.
3. Strategy assignment is explicit during Procurement enrichment.
4. The Budget Line cannot silently assign or replace the Demand target.
5. Every funding assignment receives Budget Officer sign-off.
6. Final approval and reservation are atomic and idempotent.
7. Planning carries the approved snapshot and existing reservation identity.
8. Generic Procuring Entity and Organisation Unit scope is enforced server-side.
9. `DMD-MOH-2027-014`, `DMD-MOH-2027-019` and `DMD-CGK-2027-006` extend one repeatable fixture story.
10. No page-local duplicate canonical fixtures exist.
11. Ministry and County records remain isolated.
12. Approved Demand baselines and decision history remain immutable and auditable.
13. Every management metric has `As at`, scope, calculation basis and drill-down.
14. No realised savings, benefits or Strategy achievement are claimed without evidence.
15. Every `DIA-AC` acceptance criterion has automated evidence.
