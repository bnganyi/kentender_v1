# Strategy Alignment — MVP 1 Cursor Implementation Prompt

**Document ID:** STRATEGY-MVP1-CURSOR-1.1  
**Status:** Implementation input  
**Date:** 3 August 2026  
**Requirements baseline:** `STRATEGY-MVP1-REQ-1.1` — Locked and approved  
**Design baseline:** Approved Stitch outputs for `STR-UI-01` through `STR-UI-15`  
**Application:** KenTender  
**Module:** Strategy Alignment  
**Implementation strategy:** Clean rebuild inside the existing Strategy application boundary

## 1. Use of this document

This document contains two Cursor prompts:

1. **Prompt A — Impact scan and implementation plan.** Run this first. Cursor must inspect the repository, identify exact destructive targets and stop without changing files or data.
2. **Prompt B — Execute the approved clean rebuild.** Run this only after reviewing and approving Cursor’s Prompt A report.

Do not merge the two passes. The pause is a deletion-safety gate, not a request to reconsider the approved product design.

Before Prompt A, make the following inputs available to Cursor in the repository or its context:

- `Strategy_Alignment_MVP1_Requirements.md`
- Approved Stitch screen outputs for `STR-UI-01` through `STR-UI-15`
- Existing repository instructions and test commands

`Strategy_Alignment_MVP1_Stitch_Prompts.md` may be supplied as design rationale, but it is not a substitute for the approved Stitch outputs.

---

# Prompt A — Impact scan and implementation plan

```text
Plan the clean rebuild of KenTender Strategy Alignment MVP 1.

AUTHORITATIVE INPUTS

1. Strategy_Alignment_MVP1_Requirements.md
   - Document ID: STRATEGY-MVP1-REQ-1.1
   - Status: Locked and approved
2. Approved Stitch outputs for screen IDs STR-UI-01 through STR-UI-15
3. Repository-level engineering instructions and established KenTender conventions

Read every authoritative input completely before planning. If the locked requirements or any approved screen required for implementation is unavailable, identify the missing input and stop. Do not infer it from legacy code.

DECISION ALREADY MADE

This is a clean rebuild inside the existing Strategy application/module boundary. Existing MVP Strategy records and Strategy-specific legacy structures are disposable. There is no production-data migration or compatibility requirement.

Do not propose:
- incremental refactoring of the legacy Strategy domain;
- a parallel V2 module, app, route, page, DocType or API;
- compatibility adapters, aliases, dual reads, dual writes or fallback queries;
- preservation of disposable fixture data;
- retaining obsolete fields “just in case”; or
- an iframe or static HTML workbench.

The new implementation must replace the existing Strategy implementation as one coherent domain. Reuse only established platform infrastructure and genuinely shared components that remain compatible with the locked design.

ARCHITECTURAL DIRECTION

- Keep the existing KenTender/Frappe application shell and real Procurement navigation.
- Implement Strategy as native Frappe domain records, server services and dedicated Desk pages following the repository’s established live-page pattern.
- Hand-port approved Stitch presentation into maintainable application CSS/JS/components. Do not ship Stitch’s fake shell, static data or iframe.
- Treat server-side permission, validation, workflow and derived-state calculation as authoritative.
- Treat the approved requirements as the product specification. Inspect legacy code only to discover dependencies and deletion impact, never to derive new behaviour.
- Keep production UI API-driven. Ministry of Health data belongs in repeatable fixtures, not hardcoded screen logic.

YOUR TASK IN THIS PASS

Perform a bounded read-only repository and schema impact scan. Do not edit files, create migrations, reset data, run destructive commands or implement code.

Inspect only what is needed to answer:

1. Where is the current Strategy domain implemented?
2. Which Strategy DocTypes, fields, child tables, pages, routes, services, hooks, fixtures, permissions, workflows and tests are legacy and must be removed or replaced?
3. Which Budget, Demand, Planning and Procurement Home paths consume the old Strategy hierarchy or selectors?
4. Which components are genuinely shared platform infrastructure and must be retained?
5. Are there uncommitted user changes overlapping the target files?
6. Which approved Stitch assets/screens are present, and how will each map to the application?
7. What exact test commands and fixture/reset mechanisms are established in the repository?

Search explicitly for the old conflated model and its active references, including:
- Strategy Objective used as an output indicator;
- embedded actual-result fields on targets;
- old Objective/Indicator aliases;
- five-field cascading Strategy selectors;
- legacy Strategy builder routes and APIs;
- compatibility redirects and fallback queries;
- old Strategy seed identifiers;
- downstream Budget, Demand and Planning fields that store the old cascade;
- tests that assert obsolete behaviour.

REQUIRED PLAN OUTPUT

Return one concrete implementation plan with these sections:

A. Input confirmation
- Confirm the exact requirements file and approved screen artifacts read.
- List any conflict between the locked requirements and approved design outputs. Do not resolve functional conflicts silently.

B. Current implementation map
- Existing Strategy app/module path.
- Relevant DocTypes and child tables.
- Pages, routes, APIs, hooks, workflows, fixtures and tests.
- Downstream consumers in Budget, Demand, Planning and Home.

C. Destructive target manifest
Provide a table with:
- Exact path or DocType
- Current purpose
- Action: Delete, Replace, Retain or Rewire
- Reason
- Known dependants
- Verification after change

The manifest must distinguish Strategy-owned targets from shared platform assets. Never propose deleting a whole site, database, repository, app or broad directory.

D. Clean target architecture
Map the locked domain to exact proposed DocTypes/modules/services/pages. Include:
- Strategic Plan version
- Programme
- optional Sub-programme
- Strategic Outcome
- Performance Indicator
- Performance Target
- Public Value Objective
- Objective Applicability Trigger
- Plan Value Commitment
- Plan Value Commitment Link
- Performance Measurement
- Strategy Corrective Action
- framework-native workflow/audit facilities where suitable
- downstream Strategy Reference contract owned by consuming records
- read-only Strategy Performance projection and controlled report export, without a manually maintained reporting ledger

Do not add records absent from the locked requirements without identifying a concrete framework necessity.

E. Integration rewiring
State exactly how Budget, Demand and Planning will move from the old cascade to the versioned Strategy Reference contract. Include:
- Active-only new selection;
- one primary Performance Target alignment in Demand;
- optional reasoned supporting alignments;
- immutable human-readable reference snapshot;
- historical resolution after plan supersession;
- applicable Plan Value Commitment retrieval;
- read-only downstream usage in Strategy.
- authoritative Budget, Demand, Planning, Tender and Contract inputs to Strategy Performance, with lifecycle values kept separate.

F. Screen implementation map
Map STR-UI-01 through STR-UI-15 to exact page/component/controller/service files. Confirm that the existing shell is retained and no iframe is used. Treat STR-UI-15 as a separate role-driven management entry view, not an eighth Plan workspace tab.

G. Execution sequence
Give a short atomic sequence covering:
1. clean domain replacement;
2. permissions and governance;
3. services and downstream contracts;
4. UI implementation;
5. Ministry of Health seed/reset;
6. automated tests;
7. absence searches for legacy behaviour.

H. Verification matrix
Map STR-AC-001 through STR-AC-030 and the required test matrix to exact test files or planned test files.

I. Risks and blockers
Report only repository-specific blockers. Do not reopen approved product choices. Distinguish blockers from ordinary implementation work.

J. Proposed change boundary
End with the exact file and data scope you will change after approval and the exact destructive operations you will perform.

STOP CONDITION

Stop after producing the report. Do not make any change. Wait for explicit approval to execute Prompt B.
```

## Prompt A approval checklist

Approve Cursor’s plan only if:

- It identifies exact legacy targets rather than broad directories.
- It does not propose a V2 implementation or compatibility layer.
- It identifies all Budget, Demand and Planning consumers.
- It preserves the real KenTender shell and shared platform infrastructure.
- Every locked screen and acceptance criterion has an implementation/test destination.
- It identifies overlapping uncommitted user changes.
- Its destructive operations are limited to Strategy-owned disposable MVP data and explicitly affected demo references.
- It does not introduce data migration solely to preserve disposable Strategy records.

If the plan satisfies these conditions, run Prompt B in the same Cursor context.

---

# Prompt B — Execute the approved clean rebuild

```text
Execute the approved Strategy Alignment MVP 1 clean-rebuild plan from the preceding impact scan.

Do not reopen the architecture choice. Do not ask whether to preserve the legacy model. Existing Strategy MVP data is disposable, and the approved plan defines the deletion boundary.

AUTHORITATIVE ORDER

When resolving implementation questions, use this precedence:
1. STRATEGY-MVP1-REQ-1.1 locked requirements
2. Approved Stitch outputs for STR-UI-01 through STR-UI-15
3. Approved impact-and-deletion plan from Prompt A
4. Current repository engineering conventions
5. Legacy code only as dependency evidence

If an actual contradiction exists between items 1 and 2, stop and report the exact conflict. Do not invent a compromise. A visual omission is not a contradiction; implement required behaviour using the approved design system without adding new workflow or scope.

CHANGE DISCIPLINE

- Work only inside the approved change boundary.
- Preserve unrelated user changes. Do not reset, overwrite or reformat unrelated files.
- Do not use destructive Git commands.
- Before deleting or resetting data, resolve exact named targets from the approved manifest.
- Never delete the whole database, site, repository, app or a broad directory.
- Use the repository’s established Frappe migration, schema-sync, fixture and test mechanisms.
- If an unexpected dependency expands the approved destructive boundary, stop and report it before proceeding.
- Continue through ordinary coding/test failures that remain inside scope; fix them rather than deferring them.

PROHIBITED LEGACY PATTERNS

The completed implementation must contain none of the following in an active MVP path:
- Strategy Objective acting as Output Indicator;
- embedded target actuals or latest-result fields used as measurement history;
- Objective/Indicator label aliases;
- five-field cascading Strategy selectors;
- legacy Strategy builder pages, APIs or redirects;
- legacy/new dual-read or dual-write logic;
- fallback queries to obsolete DocTypes or fields;
- `_v2`, `new_`, `legacy_`, `deprecated_` or equivalent parallel-model naming;
- compatibility adapters whose sole purpose is disposable MVP data;
- hardcoded Ministry of Health records in production UI or services;
- iframe/static Stitch HTML implementation;
- UI-only permission or workflow enforcement;
- combined workflow status and performance-result status;
- editable Approved, Active or Verified records;
- manually editable downstream usage counts;
- arbitrary formula, script or compound-rule builders;
- strategy scores, weights, rankings, grades or pass/fail labels;
- manually editable Strategy Performance values or reporting totals;
- summing Budget, Demand, Plan, Tender and Contract values as if lifecycle stages are additive;
- treating downstream consideration as verified public-value achievement;
- unverified savings, cost avoidance, benefits, forecasts or causal procurement claims;
- silent omission of unavailable or stale management-reporting sources.

IMPLEMENTATION REQUIREMENTS

1. Clean typed Strategy domain

Implement the locked hierarchy exactly:

Strategic Plan version
→ Programme
→ optional Sub-programme
→ Strategic Outcome
→ Performance Indicator
→ Performance Target

Enforce parent/version integrity server-side. A Strategic Outcome belongs to a Programme and may optionally belong to a Sub-programme from that Programme and plan version. Do not create placeholder Sub-programmes.

Implement separate governed records for:
- Public Value Objective and its immutable versions;
- simple inclusion-only Objective Applicability Triggers;
- Plan Value Commitment;
- Plan Value Commitment Link to Outcome or Performance Target;
- Performance Measurement as time-series actual evidence;
- Strategy Corrective Action.

Use the exact fields, controlled values, constraints and state models in sections 6–13 of STRATEGY-MVP1-REQ-1.1. Do not merge concepts to reduce table count.

2. Immutability, versioning and history

- One logical `plan_code` may have many versions but only one Active version per entity.
- Approved and Active plan versions are immutable.
- Active Public Value Objective versions are immutable.
- Material change creates a successor version.
- Activating a successor atomically supersedes the previous Active version.
- Codes become immutable after first approval.
- Referenced/approved records cannot be deleted.
- Historical downstream references and human-readable snapshots remain resolvable.
- Verified measurements are immutable. Corrections create a formally superseding measurement.
- A later measurement never overwrites or conceals an earlier period result.

3. Governance and permissions

Implement the exact transition tables and role/capability matrix in sections 11 and 12 of the locked requirements.

Enforce server-side:
- entity scoping;
- all valid and invalid state transitions;
- plan submitter/approver segregation;
- measurement submitter/verifier segregation;
- corrective-action owner/verifier segregation;
- required reasons for return, rejection, cancellation, archival and approval withdrawal where specified;
- effective-period and Active-version guards;
- evidence access restrictions;
- prevention of direct API/database writes that bypass state controls.

Hiding an action in the UI is not permission enforcement.

4. Readiness

Implement all readiness rules in section 13. Return structured issues grouped as:
- Structure
- Targets
- Value Commitments
- Governance

Each issue must include severity, code/title of the affected record, human-readable corrective message and a stable edit location that STR-UI-13 can use. Submission must be blocked while blockers exist. Warnings do not block unless the locked requirement explicitly says they do.

Do not add declarations or confirmation checkboxes to readiness or submission.

5. Measurement derivation

Keep target definition, measurement workflow and result derivation separate.

Implement type-compatible values for Numeric, Percentage, Currency, Duration, Count, Milestone and Boolean. Implement the compatible comparison directions and the calculation rules in section 10.

Quantitative behaviour:
- At least: actual at or above target = On track; below target but at or above tolerance = At risk; below tolerance = Off track.
- At most: inverse comparison.
- Missed target without explicit tolerance = Off track.

Implement appropriate Milestone and Boolean due-date behaviour. Result status must be derived, not selected by the submitter or verifier.

Result statuses:
- On track
- At risk
- Off track
- Not due
- No data

Workflow statuses:
- Draft
- Submitted
- Returned
- Verified
- Rejected

Prevent duplicate target-period measurements unless a formal superseding record is created. Verified Off track requires a corrective action or an authorised exception.

6. Public-value applicability and downstream meaning

Implement the controlled pillars, applicability modes, consideration levels and enforcement-guidance routes exactly as locked.

Applicability supports simple inclusion triggers only:
- Procurement Category
- Procurement Type
- Asset Condition

Required consideration means the consuming Procurement Value Case must include the objective or record an approved not-applicable reason. It does not automatically create a specification, bidder requirement, preliminary criterion, evaluation criterion or contract clause.

Strategy owns objective definitions and plan commitments. Demand owns procurement-specific Value Case treatment and exclusions.

7. Service contracts and integration

Implement and permission-test:
- `list_strategy_plans`
- `get_strategy_tree`
- `validate_strategy_reference`
- `list_active_targets`
- `list_applicable_value_commitments`
- `get_strategy_usage`
- `list_measurements`
- `get_strategy_portfolio`
- `get_strategy_performance`
- `export_strategy_performance_report`

Follow repository naming conventions only where they do not change contract semantics.

Rewire affected MVP integrations atomically:

Budget:
- store/use valid versioned Strategy references where the implemented Budget flow requires alignment;
- preserve human-readable snapshots for audit.

Demand:
- require one primary Active Performance Target alignment in the Procurement Value Case;
- allow optional supporting target alignments only with a reason;
- retrieve applicable Plan Value Commitments using structured demand context;
- own and approve inclusion or not-applicable treatment.

Planning:
- inherit and display valid approved alignment without rebuilding the legacy cascade;
- preserve version and snapshot traceability.

Procurement Home:
- update Strategy counts/work references only where the current implemented Home consumes them.

New selections use effective Active targets only. Historical valid references remain resolvable after supersession and must not be falsely flagged.

Do not create a manually maintained Strategy-owned usage register when authoritative consuming records can derive the usage.

7.1 Strategy Performance management projection

Implement Strategy Performance as a read-only, server-derived projection for the authorised entity, Active plan and reporting period. Do not create editable reporting totals or a separate shadow data warehouse for MVP 1.

Role routing and access:
- Strategy Viewer is the read-only management/senior-stakeholder profile and opens Strategy Performance by default.
- Authorised operational roles may open Strategy Performance and switch to the Strategy Portfolio.
- Strategy Viewer receives no plan create/edit/review/approval, measurement submission or evidence-management action.
- Enforce entity and report-export permissions server-side.
- Showing a derived status must not grant access to restricted underlying evidence.

Performance derivation:
- Use the latest applicable Verified measurement for each target and reporting period.
- Return On track, At risk, Off track, Not due and No data distributions without a composite score.
- Derive Outcome `Needs attention` when any current target is At risk, Off track or overdue without required data, while returning the underlying distribution.
- Keep missing/overdue, Returned and Rejected measurement workflow exceptions separate from Verified performance results.
- Return open and overdue corrective actions with owner, due date and authorised drill-down.
- A trend/direction may compare the current reporting period with the preceding equivalent period only; it is not a forecast.

Procurement contribution:
- Include only records with valid Strategy alignment references.
- Return Budget, approved Demand, approved Procurement Plan, Tender and Contract counts and values as separate lifecycle-stage measures.
- Never sum lifecycle-stage values into one procurement total.
- Calculate a funding gap or headroom only when budget and aligned demand/plan values have comparable period, currency and scope; return the calculation basis.
- Do not claim that aligned procurement caused a strategic result.
- Do not claim savings, cost avoidance or benefit achievement without an authoritative approved baseline, method and verified downstream value.

Public-value reporting:
- Report whether Required, Recommended or Available commitments were addressed in authorised downstream Value Cases.
- Keep `Addressed`, `Treated` and `Excluded with approval` separate from achievement.
- Report achievement only where a linked Verified target measurement or another authoritative verified outcome record exists.
- Return Required commitments with missing treatment or exclusion decisions as management exceptions; do not convert them into automatic tender criteria.

Lineage and freshness:
- Every projection response must include applied filters, reporting period, `as_at`, source coverage and unavailable/stale-source indicators.
- Every summary must drill down to the contributing target, measurement, corrective action or authorised downstream reference.
- If a source is unavailable, explicitly exclude and label it; do not present incomplete totals as complete.
- Use bounded aggregate queries and avoid per-target or per-downstream-record query loops.

Report export:
- Export the current authorised filtered projection, not a separately recomputed unscoped dataset.
- Include filters, reporting period, generation timestamp, `as_at`, source coverage and traceable references.
- Prevent formula injection and unsafe data exposure in tabular exports.
- Do not add an export declaration or confirmation step.

8. User interface

Implement all approved designs:
- STR-UI-01 Strategy Portfolio
- STR-UI-02 Plan Overview
- STR-UI-03 Plan Structure
- STR-UI-04 Structure Item Editor
- STR-UI-05 Public Value Objective Catalogue
- STR-UI-06 Public Value Objective Editor
- STR-UI-07 Plan Value Commitments
- STR-UI-08 Measurement Register
- STR-UI-09 Submit Measurement
- STR-UI-10 Verify Measurement
- STR-UI-11 Corrective Actions
- STR-UI-12 Downstream Usage
- STR-UI-13 Readiness and Review
- STR-UI-14 Audit History
- STR-UI-15 Strategy Performance

UI rules:
- retain the real KenTender Procurement rail, breadcrumb/header and account controls;
- use dedicated live Desk pages/components, not raw DocType lists as the primary experience;
- port the approved Stitch content-area design into maintainable application code;
- keep exactly these Plan workspace tabs: Overview, Structure, Value Commitments, Measurement, Downstream Usage, Review and Audit;
- implement Strategy Performance as a separate management entry view and never as an eighth Plan workspace tab;
- use a typed hierarchy tree and one adjacent detail region/drawer;
- show code and title together;
- use compact tables for catalogue, measurements, actions, usage and audit;
- use Start, Continue, Review, Resolve and View consistently;
- show status with text and non-colour cues;
- show inline correction links and return reasons;
- make Approved/Active/Verified content read-only;
- use “Needs attention”, never “Failed”, for underperformance requiring work;
- implement empty, loading, returned, read-only, no-permission and error states;
- implement keyboard navigation, visible focus, accessible labels and adequate contrast;
- do not add decorative dashboards, card walls, nested accordions, unapproved charts or extra tabs.
- keep management outcome results, workflow exceptions and corrective-action exceptions distinct;
- label procurement contribution by lifecycle stage and show the non-additivity note;
- distinguish public-value treatment from verified achievement;
- show reporting context, `As at`, source coverage and drill-downs;
- implement unavailable-source and no-Verified-measurement states without silently showing incomplete totals.

The UI must render live API data. Fixture values must not be embedded in page controllers or templates.

9. Ministry of Health fixture and reset

Replace obsolete Strategy seeds and affected demo references with repeatable fixtures from section 19 of the locked requirements.

At minimum seed:
- MOH-SP-2026-2030 v1, Active;
- MOH-PROG-DH;
- MOH-SUB-HIS;
- MOH-OUT-01;
- MOH-IND-01;
- MOH-TGT-01 with 97.8% baseline and ≥99.9% target;
- the eight specified Public Value Objectives;
- linked Plan Value Commitments sufficient to exercise Required and Recommended consideration;
- September 2027 verified 99.82% At risk measurement;
- October 2027 verified 99.96% On track measurement;
- the storage-controller corrective action, completed and verified;
- affected Budget, Demand and Planning references using the new Strategy Reference contract.
- sufficient illustrative targets, measurements, corrective actions and authorised downstream references to exercise Strategy Performance On track, At risk, Off track, No data, missing-treatment and lifecycle-stage contribution states without hardcoding them in the UI.

Fixtures must be idempotent or use the repository’s established deterministic reset pattern. They are illustrative and must not be presented as statutory thresholds.

Delete/reset only the approved Strategy-owned disposable data and explicitly affected demo references. Preserve unrelated master and transactional data.

10. Audit and notifications

Record the governed events required by section 18, including actor, timestamp, prior state, new state and reason where applicable. Use framework-native immutable audit/version facilities where they satisfy the locked requirements; do not duplicate audit data without need.

Implement the scoped notifications/work queues in section 17. Links must open the affected work item and must not disclose another entity’s data.

11. Tests

Implement the full section 22 test matrix and map tests to STR-AC-001 through STR-AC-030.

Required coverage includes:
- domain constraints and cross-version rejection;
- all valid and invalid workflows;
- segregation of duties;
- entity permission checks through both UI-facing services and direct API attempts;
- plan/objective immutability and supersession;
- target/measurement type compatibility;
- measurement derivation for every supported type;
- duplicate-period and superseding-measurement behaviour;
- corrective-action requirement and verification;
- applicability filtering and downstream treatment semantics;
- Active-only selection and historical reference resolution;
- tree ordering and typed path DTOs;
- derived usage and portfolio counts;
- all fifteen core screens and their essential states;
- Strategy Performance result distributions, Outcome attention derivation and preceding-period direction;
- distinct workflow, verified-result and corrective-action exceptions;
- lifecycle-stage contribution without double counting;
- funding comparison guards for period, currency and scope;
- public-value treatment versus verified achievement;
- Strategy Viewer default route, read-only controls and entity/API restrictions;
- management report filters, source coverage, lineage, export permission and export-safety behaviour;
- unavailable/stale-source and empty-period states;
- Budget, Demand, Planning and Home regression where affected;
- repeatable Ministry of Health fixture execution.

Do not skip or weaken existing relevant tests merely to obtain a passing suite. Delete tests only when they exclusively assert approved-for-removal legacy behaviour, and replace them with tests for the locked requirements.

EXECUTION ORDER

Follow this sequence unless the approved Prompt A plan established a repository-specific dependency order:

1. Record current worktree status and protect unrelated user changes.
2. Remove approved legacy Strategy domain artifacts and obsolete tests/routes/fixtures.
3. Implement the clean DocTypes/domain constraints.
4. Implement state transitions, permissions, immutability and audit guards.
5. Implement service contracts and readiness/measurement derivation.
6. Rewire Budget, Demand, Planning and Home consumers atomically.
7. Implement approved screens against live services.
8. Reset only approved disposable data and load repeatable fixtures.
9. Run focused domain, service and browser tests.
10. Run affected regression suites.
11. Run legacy-absence searches.
12. Inspect the final diff for scope and accidental compatibility code.

LEGACY-ABSENCE VERIFICATION

At completion, search the active codebase and report every remaining match for:
- removed legacy DocType names;
- old Strategy Objective/Output Indicator labels;
- embedded target-actual fields;
- five-field cascade selectors;
- obsolete routes and API names;
- legacy fixture identifiers;
- compatibility/fallback markers introduced or retained in Strategy paths.

For every remaining match, state why it is valid. Comments, documentation or migration cleanup references may remain only when they do not activate legacy behaviour.

DEFINITION OF DONE

The work is complete only when:
- all STR-AC-001 through STR-AC-030 pass;
- required backend, permission, service, browser and regression tests pass;
- all fifteen approved screens are implemented and API-driven;
- Budget, Demand and Planning use the new reference contract;
- Strategy Performance is read-only, entity-scoped, traceable and derived from Verified Strategy data plus authoritative aligned procurement records;
- management reporting does not double count lifecycle values or equate consideration with achievement;
- the Ministry of Health fixture loads repeatably;
- the active code contains no prohibited legacy pattern;
- no unrelated file or data has been changed;
- no unresolved blocker or skipped required test remains.

FINAL REPORT

Return a concise evidence-based report containing:
1. Outcome summary.
2. Domain records created, replaced and deleted.
3. Services and downstream integrations implemented.
4. Screen-ID-to-file mapping for STR-UI-01 through STR-UI-15.
5. Data reset and fixture result.
6. Tests run, with exact pass/fail counts and commands.
7. STR-AC-001 through STR-AC-030 result table.
8. Legacy-absence search results.
9. Changed-file summary.
10. Any remaining blocker. Do not classify ordinary deferred backlog from the locked requirements as an implementation blocker.

Do not claim completion if any required test was not run or any acceptance criterion is unverified.
```

---

## 2. Owner verification after Cursor completes

Perform these checks before accepting the implementation:

1. Open the Strategy Portfolio and confirm it is a live entity-scoped page, not a static mock.
2. Create a Draft plan and build a branch both with and without a Sub-programme.
3. Confirm Outcome, Indicator, Target and Measurement remain distinct records and labels.
4. Run readiness with each blocker type and follow every Resolve link.
5. Submit, return, resubmit, approve and activate a plan using separate authorised users.
6. Confirm an Active plan cannot be edited and successor activation supersedes the prior version.
7. Create and activate a Public Value Objective, add simple applicability triggers and adopt it as a Plan Value Commitment.
8. Confirm Required consideration reaches Demand as “include or record approved not applicable”, not as an automatic tender criterion.
9. Submit and verify a measurement using different users; confirm the result is derived.
10. Confirm a verified historical measurement cannot be edited and a correction creates a superseding record.
11. Verify an Off track result and confirm corrective action or authorised exception is required.
12. Open Downstream Usage and confirm counts/records are derived and read-only.
13. Supersede a plan and confirm existing Budget/Demand/Planning snapshots remain readable while new selectors show only Active targets.
14. Test a user from another entity through both the UI and direct API request.
15. Open Strategy Performance as Strategy Viewer and confirm it is the default read-only view with no maintenance actions.
16. Reconcile target distributions against Verified measurements and confirm workflow exceptions remain separate.
17. Drill from an Outcome to its targets, measurements, corrective actions and authorised downstream references.
18. Confirm Budget, Demand, Plan, Tender and Contract values remain separate and are never summed.
19. Confirm a funding comparison appears only for matching period, currency and scope and exposes its basis.
20. Confirm public-value treatment is not labelled as achievement without Verified outcome evidence.
21. Simulate an unavailable source and confirm the page and export disclose the exclusion.
22. Export a filtered management report and confirm filters, period, generation time, source coverage and references are present.
23. Compare all fifteen screens with the approved Stitch outputs.
24. Review Cursor’s changed-file and legacy-absence reports before merging.

## 3. Change-control rule

Cursor may implement, test and correct the locked Strategy MVP 1 scope. It may not add a new domain concept, status, workflow step, role, configurable rule type, screen, tab, integration responsibility or compatibility layer without an approved requirements change. Repository discoveries that affect technical implementation should be resolved within the locked behaviour; discoveries that materially change product behaviour must be reported as blockers rather than implemented by assumption.
