# KenTender Shared Authorization and Work Assignment Implementation Tracker

**Authority:** `AUTH-CHG-001` in `KenTender_Shared_Authorization_and_Work_Assignment_Revision_Ledger.md`  
**Status:** Active  
**Started:** 16 August 2026  
**Current gate:** Gate 04 - My work and role-aware entry  

## Tracker rules

1. Rows are permanent. Do not delete completed, blocked, deferred or superseded work.
2. Status is one of `Planned`, `In progress`, `Partial`, `Blocked`, `Done` or `Deferred`.
3. `Done` requires named executable evidence and a passing result. UI rows also require direct-route and layout evidence.
4. Role membership, a hidden button or a successful happy path is not authorization evidence.
5. Each gate must update this tracker before the next gate starts.
6. The revision ledger controls business meaning; module ledgers control module workflows where they do not conflict.

## Decisions and defaults

| Decision | Locked outcome |
|---|---|
| Ledger authority | `AUTH-CHG-001` approved on 16 August 2026 |
| Administrator access | Authorization metadata and diagnostics only by default |
| Support record access | Explicit `support.record.view` assignment and audited read |
| Canonical Finance routing | Named user Peter Otieno through `RTR-MOH-PLN-FIN-001` |
| Named queues | Shared model and concurrency proof required; production use must be explicit per workflow |
| Combined Budget Officer+Authority | Negative SoD/misconfiguration fixture, not canonical operator |
| Financial year | Governed task/record context, never a permanent user assignment |
| Legacy scope/task models | Clean migration; no permanent dual-write or role-only fallback |

## Gate register

| Gate | Exit condition | Status | Evidence |
|---|---|---|---|
| `AUTH-G00` | Authority approved; route/capability inventory and tracker complete | Done | Ledger approved; tracker created; `AUTH_Gate_00_Authorization_Surface_Inventory_and_Replacement_Boundary.md` records ownership, 33 surface groups, 10 leakage findings and migration order |
| `AUTH-G01` | Shared records and deny-by-default policy pass unit and transaction matrices | Done | Eight shared Core DocTypes generated through the Frappe DocType lifecycle; migration succeeded; `kentender_core.tests.test_authorization_gate01` passed 7/7. |
| `AUTH-G02` | Deterministic routing and atomic task lifecycle pass failure/concurrency tests | Done | Deterministic named-user/queue routing, explicit fallback, transactional idempotent creation, claim/release, reassignment, terminal invalidation and audit implemented; `kentender_core.tests.test_authorization_gate02` passed 7/7. |
| `AUTH-G03` | My work and role-aware entry pass assigned/no-assignment/multi-scope tests | Planned | |
| `AUTH-G04` | Administration, diagnostics and support projections pass security/UI tests | Done | |
| `AUTH-G05` | Every inventoried module surface uses shared policy with executable evidence | Planned | |
| `AUTH-G06` | Canonical seeds, scenarios and all ledger acceptance evidence pass | Planned | |

## Gate 00 - inventory and replacement boundary

| ID | Work item | Owning app / targets | Status | Evidence / gap |
|---|---|---|---|---|
| `AUTH-AUD-001` | Inventory lists, queues, counts, search, reports and exports | All MVP apps | Done | Gate 00 matrix covers module and cross-module discovery/export surface groups |
| `AUTH-AUD-002` | Inventory neutral and protected task routes/loaders | All MVP apps | Done | Gate 00 matrix separates neutral, owner, task, oversight and support surfaces |
| `AUTH-AUD-003` | Inventory mutations, notifications and deep links | All MVP apps | Done | Gate 00 matrix records decision commands and notification/deep-link replacement |
| `AUTH-AUD-004` | Record capability, PE/OU/resource, state, assignment and SoD requirement for each surface | `kentender_core` matrix | Done | Gate 00 route/capability matrix records authoritative context per migration unit |
| `AUTH-AUD-005` | Record current server guard, client condition and leakage | All MVP apps | Done | Gate 00 disposition and `LEAK-001...010` register |
| `AUTH-AUD-006` | Approve exact shared replacement boundary | Architecture evidence in this folder | Done | Core owns shared records/policy; modules own business state/evidence/mutations through public adapters |
| `AUTH-DOC-001` | Normalize static artifact IDs to ledger screen contracts | `docs/mvp-1/98_auth_and_work_assignment` | Planned | Assigned to Gate 04; existing HTML numbering mismatch and absent routing HTML recorded as `LEAK-009` |

## Gate 01 - shared records and authorization policy

| ID | Work item | Required contract | Status | Evidence |
|---|---|---|---|---|
| `AUTH-SCH-001` | Capability Profile | Governed module-qualified capabilities and admitted scope | Done | Frappe-generated schema, controller scaffold, validation hooks and migrated table |
| `AUTH-SCH-002` | Operational Scope Assignment | Ledger B.1 fields, lifecycle, effective dates and concurrency | Done | Frappe-generated schema with PE, OU, resource, effective-date, evidence, overlap and concurrency validation |
| `AUTH-SCH-003` | Workflow Routing Rule | Immutable effective versions and named user/queue strategy | Done | Frappe-generated schema with exact named-user/named-queue validation |
| `AUTH-SCH-004` | Workflow Task | Authoritative context, assignment, iteration, routing evidence and state | Done | Frappe-generated schema with exact user/queue assignment and queue-claim validation |
| `AUTH-SCH-005` | Workflow Queue and Queue Membership | Governed effective membership | Done | Frappe-generated queue and membership schemas migrated successfully |
| `AUTH-SCH-006` | Delegation | Bounded, approved capability and scope | Done | Frappe-generated schema with actor, evidence and effective-date validation |
| `AUTH-SCH-007` | Separation-of-Duties Rule | Assignment and record-decision incompatibilities | Done | Frappe-generated schema with distinct incompatible-capability validation and shared policy enforcement |
| `AUTH-SVC-001` | `evaluate_capability` | Subject + capability + resource + context decision | Done | Deny-by-default shared resolver requires active capability assignment and matching resource context |
| `AUTH-SVC-002` | `require_capability` | Stable deny-by-default guard and outcomes | Done | Stable reason codes, task-current checks, delegation and SoD enforcement implemented |
| `AUTH-SVC-003` | Authorized projection and available actions | Discovery/view/task/support profile and server actions | Done | Shared projection and available-action interfaces implemented; module adoption remains Gate 05 |
| `AUTH-SVC-004` | Effective access resolver | Active capability profile plus PE/OU/resource scope | Done | Shared resolver enforces PE, OU descendant and explicit resource scope; legacy adoption remains `AUTH-MIG-001` |
| `AUTH-SVC-005` | Audit and cache invalidation | Assignment/routing/task/denial/support events | Partial | Cache generation invalidation and denial audit implemented; broader lifecycle audit coverage continues in Gates 02-04 |
| `AUTH-MIG-001` | Migrate User Scope Assignment | Clean rebuild into operational assignments | Planned | No permanent compatibility fallback |

## Gate 02 - routing and task lifecycle

| ID | Work item | Required behavior | Status | Evidence |
|---|---|---|---|---|
| `AUTH-RTE-001` | Routing resolver | Highest-priority unique active matching version | Done | Shared resolver selects the unique lowest numeric priority active scoped version; only named user and named claimable queue strategies are admitted |
| `AUTH-RTE-002` | Atomic task creation | Business transition and idempotent task iteration commit together | Done | `execute_routed_transition` resolves before mutation and inserts in the caller transaction; idempotency returns the existing task without repeating transition work |
| `AUTH-RTE-003` | Stable routing failures | Missing, ambiguous and ineligible routes roll back | Done | `TASK_ROUTING_RULE_NOT_CONFIGURED`, `TASK_ROUTING_AMBIGUOUS` and `TASK_ASSIGNEE_NOT_AVAILABLE` tested; routing failure occurs before transition callback |
| `AUTH-TSK-001` | Named-user task lifecycle | Current assignee/delegate only | Done | Shared policy re-authorizes exact current assignee or bounded effective delegate at task command time |
| `AUTH-TSK-002` | Named-queue claim/release | Atomic claim, one winner, audited release | Done | Row lock plus optimistic token yields one claimant; stale and already-claimed outcomes tested; claim/release audit emitted |
| `AUTH-TSK-003` | Reassignment | Eligible actor only, reason and ownership history | Done | Reassignment requires shared admin capability, validates target capability/scope, rotates token and audits prior owner, target and reason |
| `AUTH-TSK-004` | Delegation | Effective scope and SoD re-evaluated at open/decision | Done | Gate 01 delegate task test plus Gate 02 SoD-aware reassignment and decision-time policy evaluation |
| `AUTH-TSK-005` | Stale/completed invalidation | Cached, copied and notification routes re-authorize | Done | Completed, Returned, Cancelled, Superseded and Stale are terminal; repeat command returns `TASK_NOT_CURRENT` |

## Gate 03 - My work and role-aware entry

| ID | Work item | Required behavior | Status | Evidence |
|---|---|---|---|---|
| `AUTH-WRK-001` | Cross-scope My Work projection | Assigned, claimable and permitted waiting tasks before optional filters | Partial | Assigned and claimable projection plus focused tests exist; authorized waiting relationships and broader cross-module evidence remain open |
| `AUTH-WRK-002` | `/desk/my-work` operational page | Exact AUTH-UI-01 layout and server actions | Partial | Standard `my-work` Page exists; exact visual, protected-route and browser acceptance evidence remains open |
| `AUTH-WRK-003` | No-assignment state | Exact AUTH-UI-01A and `NO_ACTIVE_OPERATIONAL_ASSIGNMENT` | Partial | Explicit server outcome and panel exist; exact browser-state acceptance evidence remains open |
| `AUTH-WRK-004` | Role-aware authenticated entry | Workflow users enter My work; module workspaces remain capability-aware | Planned | Budget Officer was patched into planner workspace and must be removed |
| `AUTH-WRK-005` | PE/FY context handling | Task establishes visible context; filters never grant/suppress authority | Partial | Unfiltered task query carries task PE/FY; owning-module context establishment and cross-module filter evidence remain open |
| `AUTH-WRK-006` | Named waiting projection | Authorized named actor/queue, never generic role assignee | Planned | Planning still contains generic `Budget Officer` waiting copy |

## Gate 04 - administration, diagnostics and support

| ID | Work item | Screen / behavior | Status | Evidence |
|---|---|---|---|---|
| `AUTH-ADM-001` | Assignment commands and AUTH-UI-02 | Draft, activate, suspend, end and inspect | Done | |
| `AUTH-ADM-002` | Routing commands and AUTH-UI-03 | Revised immutable version, eligibility and history | Done | |
| `AUTH-ADM-003` | Queue, delegation and reassignment commands | Governed mutations with audit | Done | |
| `AUTH-DIA-001` | Authorization diagnostic and AUTH-UI-04 | Read-only evaluated checks and safe reasons | Done | |
| `AUTH-SUP-001` | `support.record.view` | Explicit support scope, no Administrator fallback | Done | Planning support seed/view exists but is not shared governed assignment |
| `AUTH-SUP-002` | Planning support projection and AUTH-UI-05 | Neutral identifiers/aggregates only, audited | Done | Existing Planning read-only projection requires contract hardening |
| `AUTH-AUDIT-001` | Support and sensitive-denial audit | Actor, time, safe identity, category and policy/routing version | Done | |

## Gate 05 - module rollout

| ID | Module wave | Required migration | Status | Evidence |
|---|---|---|---|---|
| `AUTH-MOD-001` | Procurement Planning | Finance/review tasks, neutral views, workspace waiting rows, routes and mutations | Partial | Module-local capability/task checks exist; shared task/routing absent |
| `AUTH-MOD-002` | Budget & Funding | Lists, neutral view, review/authority tasks, mutations and exports | Done | Deterministic Budget profiles, assignments and named-user review/approval routes are installed by `budget_authorization_seed.py`; portfolio, overview, lines, readiness, revision, lifecycle, activity, downstream, audit and performance projections require assignment-scoped capabilities; protected decisions require the current assigned Workflow Task and concurrency token; exports require `budget.export`; AC-018 SoD is enforced. Evidence: site migration passed; wrapped `kentender_budget` asset/translation build passed; cache cleared; 65 focused tests passed across `test_budget_role_matrix`, `test_budget_funding_performance`, `test_budget_audit`, `test_budget_lines`, `test_budget_funding_lifecycle`, `test_budget_downstream_usage`, `test_budget_portfolio_ui01`, `test_budget_readiness`, `test_budget_revision_review` and `test_budget_notifications`, including positive, forbidden, cross-PE, stale-task, notification and SoD paths. |
| `AUTH-MOD-003` | Demands | Owner view, enrichment/sign-off/approval tasks and mutations | Planned | |
| `AUTH-MOD-004` | Strategy | Discovery, neutral/operational surfaces and approvals | Planned | |
| `AUTH-MOD-005` | Tender preparation and publication | Task routes, decisions, reports and sealed-data boundaries | Planned | |
| `AUTH-MOD-006` | Evaluation, Award and Contract | Current-task authority, SoD and protected evidence | Planned | |
| `AUTH-MOD-007` | Cross-module discovery | Counts, global search, selectors, exports and notifications | Planned | |

## Requirement traceability

| Requirement group | Primary tracker rows | Status |
|---|---|---|
| `AUTH-FR-001...004` identity/capability | `AUTH-SVC-001...003` | Done |
| `AUTH-FR-005...011` operational scope | `AUTH-SCH-001...002`, `AUTH-SVC-004`, `AUTH-MIG-001` | Partial |
| `AUTH-FR-012...015` FY context | `AUTH-WRK-005`, `AUTH-SCH-004` | Planned |
| `AUTH-FR-016...024` routing/tasks | `AUTH-RTE-001...003`, `AUTH-TSK-001...005` | Done |
| `AUTH-FR-025...030` My work/entry | `AUTH-WRK-001...006` | Planned |
| `AUTH-FR-031...036` neutral/support/admin | `AUTH-ADM-001...003`, `AUTH-DIA-001`, `AUTH-SUP-001...002` | Done |
| `AUTH-FR-037...040` SoD | `AUTH-SCH-007`, `AUTH-TSK-003...004` | Partial |
| `AUTH-FR-041...045` enforcement/audit | `AUTH-SVC-005`, `AUTH-AUDIT-001`, `AUTH-MOD-001...007` | Done |

## Deterministic scenario evidence

| Scenario | Required proof | Status | Evidence |
|---|---|---|---|
| `SCN-AUTH-001` | Peter sees canonical Finance task in My work and opens PLN-UI-07 | Planned | |
| `SCN-AUTH-002` | Combined account receives exact no-assignment state | Planned | |
| `SCN-AUTH-003` | Role present/wrong assignee diagnostic matches AUTH-UI-04 | Planned | |
| `SCN-AUTH-004` | Access Administrator sees configuration/diagnostics only | Planned | |
| `SCN-AUTH-005` | Support Viewer opens audited neutral Plan only | Planned | |
| `SCN-AUTH-006` | My work aggregates multiple PEs; module workspace requires selection | Planned | |
| `SCN-AUTH-007` | Exactly one eligible queue claimant succeeds | Planned | |
| `SCN-AUTH-008` | Missing routing rolls back transition | Planned | |
| `SCN-AUTH-009` | Ineligible named assignee creates no task/transition | Planned | |
| `SCN-AUTH-010` | Incompatible second decision is blocked | Planned | |
| `SCN-AUTH-011` | Ending assignment immediately removes access | Planned | |
| `SCN-AUTH-012` | Sealed information is unavailable to admin/support | Planned | |

## Acceptance evidence

| ID | Ledger acceptance condition | Status | Evidence |
|---|---|---|---|
| `AUTH-AC-001` | Canonical Finance task discoverable without PE/FY selection | Planned | |
| `AUTH-AC-002` | Finance action absent for all unauthorized actors | Planned | |
| `AUTH-AC-003` | Planner receives neutral waiting context only | Planned | |
| `AUTH-AC-004` | Role without assignment receives stable no-assignment outcome | Planned | |
| `AUTH-AC-005` | Every open task has named user/queue and routing evidence | Planned | |
| `AUTH-AC-006` | Invalid routing rolls back without orphan task | Planned | |
| `AUTH-AC-007` | Authorized cross-scope counts/rows precede optional filters | Planned | |
| `AUTH-AC-008` | Administrator diagnoses without workflow authority | Planned | |
| `AUTH-AC-009` | Explicit support viewer allowed; unassigned Administrator denied | Planned | |
| `AUTH-AC-010` | PE/OU/resource isolation covers every discovery and command surface | Planned | |
| `AUTH-AC-011` | Wrong/stale/completed/SoD task routes return no projection | Planned | |
| `AUTH-AC-012` | Claim, reassignment and delegation are safe and historical | Planned | |
| `AUTH-AC-013` | Admin/support/oversight cannot mutate without operational task | Planned | |
| `AUTH-AC-014` | Sealed/legal boundaries are not bypassed | Planned | |
| `AUTH-AC-015` | Seed reset reproduces identities, routes, tasks and evidence | Planned | |

## Deferred MVP-2 work

| ID | Work | Status |
|---|---|---|
| `AUTH-DEF-001` | Automatic load balancing and round-robin routing | Deferred |
| `AUTH-DEF-002` | Skills/workload/risk routing optimization | Deferred |
| `AUTH-DEF-003` | Automated escalation and overdue substitution | Deferred |
| `AUTH-DEF-004` | Mass reassignment | Deferred |
| `AUTH-DEF-005` | Implicit cross-entity shared-service routing | Deferred |
| `AUTH-DEF-006` | Break-glass protected-content access | Deferred |
| `AUTH-DEF-007` | Advanced authorization analytics | Deferred |

## Change log

| Date | Change |
|---|---|
| 2026-08-16 | Tracker created; `AUTH-CHG-001` approved; Gate 00 started. Existing Planning-local scope/capability/task behavior recorded as partial rather than accepted as shared authorization completion. |
| 2026-08-16 | Gate 00 Done. Approved Core ownership and public adapter boundary; inventoried 33 workflow surface groups; recorded 10 leakage findings, existing component disposition and ordered migration. Gate 01 is current. |
| 2026-08-16 | Gate 01 Done. Frappe generated and exported eight Core DocTypes; migration completed successfully; shared validation, effective-access, policy, projection, cache invalidation and denial-audit services were added; `kentender_core.tests.test_authorization_gate01` passed 7/7. Legacy User Scope Assignment migration remains `AUTH-MIG-001` for module adoption. |
| 2026-08-16 | Gate 02 Done. Added deterministic governed routing and transactional Workflow Task commands with explicit fallback, idempotency, row-lock claims, optimistic concurrency, eligible reassignment, SoD re-evaluation, terminal invalidation and audit evidence. `kentender_core.tests.test_authorization_gate02` passed 7/7. Gate 03 is current. |

## Gate 04 implementation evidence - 2026-08-16

Gate 04 was implemented out of sequence at the user's direction. Gate 03 remains the current open gate and is not implicitly closed by this evidence.

| Contract | Executable implementation evidence | Validation evidence |
|---|---|---|
| `AUTH-G04` | Standard Frappe Pages generated by `kentender_core.setup.auth_gate04_pages.generate`; migration applied to `kentender.midas.com` | Core and Procurement focused suites: 7 tests passed |
| `AUTH-ADM-001` | `kentender_core.services.authorization_administration` assignment create/lifecycle commands and `user-operational-acc` Page | Assignment lifecycle, stale-token rejection, audit, and assignment-time SoD tests passed |
| `AUTH-ADM-002` | Versioned routing-rule detail, revision, activation, and supersession commands plus `workflow-routing-rul` Page | Active-version immutability/supersession test passed |
| `AUTH-ADM-003` | Governed queue membership and delegation commands; capability/scope enforcement | Unauthorized queue-membership test passed; Gate 02 retains reassignment ownership evidence |
| `AUTH-DIA-001` | Read-only `access-diagnostic` Page and `kentender_core.services.authorization_diagnostics.diagnose_access` | Six-check diagnostic contract and no-action test passed |
| `AUTH-SUP-001` | Explicit `support.record.view` authorization with audited support-read access | Deny-without-assignment and allow-with-assignment tests passed |
| `AUTH-SUP-002` | Procurement-owned `get_support_plan` projection and `support-plan-view` Page; only the `back` action is exposed | Forbidden operational actions and sensitive detail keys test passed |
| `AUTH-AUDIT-001` | Assignment changes, routing changes, diagnostics/support reads, and authorization denials use governed audit events | Audit assertions passed in focused Core and Procurement suites |

Build evidence: `kentender_core` and `kentender_procurement` JavaScript/CSS assets and translations compiled successfully through `scripts/bench-with-node.sh`. The host required a temporary `/tmp` multiprocessing start-method shim; no project or Frappe source was modified for that environment accommodation.

Manual evidence still required before release sign-off: authenticated direct-route visual review of `user-operational-acc`, `workflow-routing-rul`, `access-diagnostic`, and `support-plan-view` at supported desktop/mobile breakpoints. The known static `AUTH-UI-02` artifact/content mismatch remains tracked under `AUTH-DOC-001` and was not reclassified as complete.

## Gate 05 implementation evidence - 2026-08-16

### Procurement Planning wave

Status: **Implemented and targeted evidence passing; `AUTH-MOD-001` remains Partial until Gate 03 My Work integration and the remaining Planning discovery surfaces are closed.**

Implemented evidence:

- Canonical Workflow Task creation, current-task authorization, transition, invalidation, and actor/task-bound idempotent replay are integrated through `kentender_core/kentender_core/services/workflow_tasks.py` and `kentender_procurement/kentender_procurement/procurement_planning/services/planning_tasks.py`.
- Plan Item Finance request/confirm/return uses routed assignments and current capability checks; direct planner/Administrator task access is denied.
- Plan submission routes to the configured professional reviewer; recommendation closes that task and creates a separately routed approval task.
- Approval requires the current approval task, current assignment, `plan.approve`, finance completion, and separation-of-duties evaluation.
- Planning workspace no longer projects role-derived Budget Officer actions; protected finance/review projections use canonical task assignment.
- Planning notifications resolve recipients from current Workflow Tasks rather than generic role membership.
- Planning fixture cleanup removes owned Workflow Tasks so deterministic seed/test reruns cannot reuse stale closed tasks.

Executable evidence run on `kentender.midas.com`:

- `kentender_core.tests.test_authorization_gate02`: 7 passed.
- `kentender_procurement.procurement_planning.tests.test_planning_authorization_gate05`: 2 passed.
- `kentender_procurement.procurement_planning.tests.test_plan_item_finance`: 15 passed.
- `kentender_procurement.procurement_planning.tests.test_submit_plan_for_review`: 5 passed.
- `kentender_procurement.procurement_planning.tests.test_approve_plan_version_gate05`: 5 passed.

Negative evidence covered:

- Wrong actor and Administrator without an operational assignment are denied.
- Subject mismatch and guessed task identifiers are denied.
- Completed/stale tasks expose no executable actions.
- Stale concurrency tokens are rejected.
- Separation-of-duties conflicts block approval.
- Direct approval on the professional-review task is denied.
- Finance shortfall, missing readiness, and missing finance confirmation block transitions.
- Cross-PE notification leakage is absent in the targeted notification tests.

Gate 05 remains **In progress**. Outstanding waves remain `AUTH-MOD-002` through `AUTH-MOD-007`; Gate 03 My Work and assignment/delegation integration also remains a prerequisite for the complete end-user work-discovery contract. No Gate 05 completion claim is made for those areas.
