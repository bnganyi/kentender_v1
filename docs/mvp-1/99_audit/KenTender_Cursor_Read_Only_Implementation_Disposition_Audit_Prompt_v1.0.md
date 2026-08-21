# KenTender Cursor Read-Only Implementation Disposition Audit Prompt

**Document ID:** KENTENDER-CURSOR-ROIDA-1.0  
**Version:** 1.0  
**Date:** 11 August 2026  
**Status:** Draft for execution after operating-model validation  
**Mode:** Read-only investigation — make no implementation changes

## 1. Instruction to Cursor

Audit the current KenTender repository implementation for Strategy Alignment, Budget & Funding, Demands and Procurement Planning against these controlling draft documents:

1. `KenTender_MVP_Cross_Module_Operating_Model_v1.0.md`
2. `KenTender_MVP_Semantic_and_Workflow_Assurance_Audit_v1.1.md`

This pass is evidence gathering only.

Do not:

- edit application code;
- create or run migrations;
- change DocTypes or database records;
- modify fixtures or seed scripts;
- rewrite requirements, Stitch prompts or Cursor packs;
- rename or delete files;
- change permissions;
- add compatibility shims;
- infer approval from document filenames; or
- propose a large redesign before inventorying what exists.

If a controlling statement is ambiguous, record it as an open decision. Do not resolve it by inventing a field, role, state or service.

## 2. Audit objective

Produce a repository-grounded disposition of the current implementation so that sound work can be preserved and unsupported concepts can be removed safely.

Every relevant artifact must receive one disposition:

| Disposition | Meaning |
|---|---|
| Keep | Correct and consistent with the operating model |
| Correct | Valid capability implemented with incorrect semantics, placement, naming or access |
| Remove | Unsupported, duplicated or prohibited capability |
| Defer | Potentially useful but outside the accepted MVP |
| Investigate | Evidence is insufficient to classify safely |

Do not classify an artifact from its name alone. Read its fields, callers, state effects, permissions, tests and consumers.

## 3. Repository baseline

Before module analysis, report:

- repository and app structure;
- current branch and commit;
- dirty-worktree status without changing it;
- Frappe/ERPNext versions detected;
- relevant installed apps;
- migration state visible from repository files;
- seed/fixture entry points;
- test commands and Playwright projects relevant to these modules; and
- any missing controlling documents.

Do not run a destructive command or mutate the database. Where a command could write caches, fixtures or generated files, do not run it in this pass.

## 4. Shared inventory

Inventory shared components before individual modules.

### 4.1 Organisation and scope

Find and report:

- Procuring Entity and Organisation Unit DocTypes/tables;
- User Scope Assignment or equivalent;
- capability/role definitions;
- PE/OU resolution services;
- default/fallback logic;
- list-query filters;
- counts, queues, exports and notification scoping;
- direct-route guards; and
- Administrator special cases.

Explicitly identify:

- first-assignment fallbacks;
- first-row fallbacks;
- hard-coded Ministry of Health fallbacks;
- hidden PE/OU form values;
- scope inferred only from workspace filters; and
- paths where multiple eligible scopes are not resolved deliberately.

### 4.2 Authorisation surfaces

For every workflow task, distinguish:

- record visibility;
- task/action visibility;
- task-route access;
- field projection;
- mutation authority;
- API authority; and
- notification/work-queue eligibility.

Identify every case where an unauthorised user can open an approval, review, activation or return form even though the action is disabled.

### 4.3 Reference generation

Inventory user-editable code/reference fields and every generator. Identify where a user is required to maintain plan, target, Budget, Demand, Plan Item or hierarchy codes.

## 5. Per-module inventory

Perform the following for each module in this order:

1. Strategy Alignment
2. Budget & Funding
3. Demands
4. Procurement Planning

### 5.1 Domain and persistence

List every relevant:

- DocType/table;
- child table;
- field, type, required/default/read-only state and options;
- link and ownership field;
- unique constraint;
- status/state field;
- version/supersession field;
- audit/event record; and
- integration reference.

For each non-obvious field, identify:

- who writes it;
- when it is written;
- whether it is entered, inherited, calculated or integrated;
- what consumes it; and
- whether tests prove that consequence.

### 5.2 Services and transitions

List every relevant:

- create/update service;
- submit/review/approve/return/activate action;
- reservation/commitment action;
- revision/version action;
- aggregation/lotting action;
- Tender handoff action;
- scheduled/background job; and
- notification producer.

For each action, show:

- caller(s);
- required capability;
- scope check;
- pre-state;
- validations;
- writes performed;
- post-state;
- audit event;
- idempotency/concurrency protection; and
- tests.

### 5.3 Screens and routes

List every module route and screen, including:

- landing/workspace;
- create/edit forms;
- neutral detail views;
- review/approval task forms;
- dashboards;
- modals/drawers;
- direct URLs; and
- route aliases.

For each, state:

- intended actor inferred from code;
- entry point;
- record read;
- record written;
- visible actions;
- route guard; and
- whether it is necessary under the operating model.

### 5.4 Seed and fixtures

Identify:

- canonical seed commands/scripts;
- execution order;
- idempotency method;
- stable business identities;
- personas and PE/OU assignments;
- cross-module links;
- financial arithmetic; and
- test-specific fixtures or page-local mock data.

Report divergences from the canonical story, but do not edit them.

### 5.5 Tests

Inventory unit, integration and Playwright coverage for:

- happy paths;
- state transitions;
- negative permissions;
- direct-route denial;
- API denial;
- multi-PE/OU selection;
- entity isolation;
- version immutability;
- reservation arithmetic;
- approved-plan revision; and
- seed repeatability.

Distinguish tests that assert actual business behaviour from smoke tests that merely confirm a page renders.

## 6. Mandatory semantic searches

Search code, configuration, documents, fixtures and tests for these terms and semantic equivalents:

- `Departmental Submission`
- `Departmental Contribution`
- `Organisation Unit Planning Contributor`
- `OU_SIGNOFF`
- `submit_departmental_contribution`
- `record_ou_plan_signoff`
- `contribution`
- `Statutory allocation treatment`
- `Statutory rationale`
- `Plan-level coverage`
- `Planned treatment value`
- `Value treatment note`
- `Budget Value Treatment`
- `Demand Value Treatment`
- `Funding treatment`
- `Plan Value Commitment`
- `Strategy Value Commitment`
- `aggregation_decision`
- `Keep separate`
- `Combine in this Plan Item`
- Administrator fallback logic
- hard-coded `PE-MOH` or equivalent scope defaults
- first User Scope Assignment selection
- disabled approval actions rendered for unauthorised roles
- free-text Budget context
- user-maintained code fields

For every occurrence, report the exact file, symbol or schema path and its runtime consequence.

## 7. Critical journey traces

Trace these journeys end to end using actual code paths.

### Journey A — normal path

Requester creates Demand → HoD approves → Planner adds Approved Demand to Plan → Planner completes Plan Item → Finance confirms funding → Head of Procurement reviews/approves → authorised user starts Tender preparation.

Report every record created, state changed, service called, capability checked and screen visited.

### Journey B — add to Approved Plan

Planner opens Approved Plan → Add Plan Item → selects one eligible Approved Demand → system creates or reuses one Draft successor → system creates one Draft Plan Item → planner completes it → revision proceeds through applicable review.

Verify that:

- Approved Version 1 remains operational;
- no second Demand selection occurs in the editor;
- no default aggregation decision is required;
- no routine second HoD approval occurs; and
- existing Tender handoffs remain tied to the Approved version.

### Journey C — explicit aggregation

Planner edits one Draft Plan Item → explicitly chooses to add another compatible Approved Demand → system shows source allocations and an operational combine/separate choice.

Verify that “separate” creates actual separate Plan Items and does not merely store a radio value on one combined item.

### Journey D — material change

Planning changes a HoD-owned fact materially. Trace whether a targeted HoD reapproval exists. If not, record the gap. Do not create a universal reapproval as a substitute.

### Journey E — unauthorised task form

A Requester can view a neutral record but attempts to open a Budget approval, Demand approval or Planning approval route. Verify action absence, route denial, API denial and absence from task queues/notifications.

### Journey F — multiple scopes

A user with access to multiple PEs/OUs creates a Demand or Plan. Verify deliberate selection and server-side validation. Identify every silent fallback.

## 8. Required output files

Create analysis documents only. Do not change implementation.

### 8.1 `00_Implementation_Disposition_Executive_Summary.md`

Include:

- overall safety assessment;
- strongest foundations to preserve;
- highest-risk semantic defects;
- data-loss or migration risks;
- recommended correction waves; and
- explicit stop conditions.

### 8.2 `01_Shared_Scope_and_Authorisation_Inventory.md`

Include the complete shared inventory and a role/capability/route matrix.

### 8.3 `02_Strategy_Disposition_Matrix.md`

### 8.4 `03_Budget_and_Funding_Disposition_Matrix.md`

### 8.5 `04_Demands_Disposition_Matrix.md`

### 8.6 `05_Procurement_Planning_Disposition_Matrix.md`

Each module matrix must use:

| Artifact | Exact location | Current purpose/effect | Evidence | Disposition | Required correction | Dependencies | Migration/seed impact | Tests affected |
|---|---|---|---|---|---|---|---|---|

### 8.7 `06_Cross_Module_Journey_Trace.md`

Document Journeys A–F with exact code references.

### 8.8 `07_Seed_and_Test_Consistency_Audit.md`

Include canonical-story arithmetic, personas, scope assignments, idempotency and test coverage.

### 8.9 `08_Open_Decisions_and_Evidence_Gaps.md`

Include only decisions that cannot be resolved from controlling documents and implementation evidence. For each, state why it blocks classification or correction.

## 9. Evidence standard

Every conclusion must cite exact repository evidence:

- file path;
- class/function/service/DocType/field/test name;
- current runtime consequence; and
- relevant controlling rule.

Do not use statements such as “appears unused” without searching for callers, hooks, fixtures, reports, exports and tests.

Where a database record is necessary to prove behaviour but this read-only pass cannot inspect it safely, state the exact query or diagnostic needed for the later authorised pass. Do not execute a write.

## 10. Correction-wave recommendation

After completing the inventory, recommend small reversible waves in this order unless repository evidence justifies a different dependency:

1. shared PE/OU scope and task-surface authorisation;
2. Strategy semantics and generated references;
3. Budget & Funding simplification;
4. Demand ownership and approval boundary;
5. Procurement Planning journey and revision semantics;
6. canonical seed reconciliation; and
7. cross-module tests.

For every wave, identify:

- code retained;
- code corrected;
- code removed;
- schema/data implications;
- migration versus disposable-seed rebuild decision;
- rollback point; and
- acceptance tests.

Do not implement the waves in this audit pass.

## 11. Completion gate

The audit is complete only when:

- all four modules and shared foundations have inventories;
- every relevant artifact has a disposition or a documented evidence gap;
- Journeys A–F have been traced;
- prohibited concepts have repository-wide search results;
- seed and tests have been reconciled to the same story; and
- no application, schema, seed or test file has been modified.

End with the exact list of files inspected, commands run and files created so the audit is reproducible.
