# AUTH Gate 00 - Authorization Surface Inventory and Replacement Boundary

**Authority:** `AUTH-CHG-001`  
**Date:** 16 August 2026  
**Status:** Approved Gate 00 baseline  

## 1. Decision

`kentender_core` owns the shared capability vocabulary, effective operational scope, routing rules, workflow tasks, queues, delegation, separation-of-duties policy, authorization decisions and audit contracts.

Participating modules continue to own their business records, workflow states, task evidence and business mutations. They call the public Core authorization interface with stable identifiers and never import another module's internal policy implementation.

`kentender_governance` may consume the published interface for governance projections. It is not the shared record owner because doing so would introduce reverse dependencies from Strategy, Budget and Procurement.

No module-local role table, saved workspace selection, generic role assignee, client action, Administrator status or fixture account remains a source of operational authority after migration.

## 2. Existing shared infrastructure disposition

| Existing component | Current use | Gate 00 decision |
|---|---|---|
| `User Scope Assignment` | User + role + PE/OU rows; incomplete lifecycle and no capability/resource semantics | Replace through a clean migration to Operational Scope Assignment; no permanent dual-write |
| `org_scope_access.py` | PE/OU resolution with Administrator and User Permission fallbacks | Replace internals with effective-assignment resolver; retain a compatibility facade only while callers migrate |
| Planning `planning_permissions.py` | Planning-local roles, capabilities and available actions | Move vocabulary/mapping into governed Core profiles; retain module business action definitions only |
| Planning `planning_tasks.py` | Selects one role-bearing user and creates embedded identities | Replace with governed routing-rule and Workflow Task services |
| Plan Item/Version task fields | Finance/review assignee, state, token and predecessor embedded in business records | Migrate to shared Workflow Task; business records may retain a non-authoritative current-task reference |
| Static `My Work` Workspace | Links to raw Demand and Plan lists | Replace with server-authorized `/desk/my-work` projection and exact AUTH-UI-01/01A states |
| Tender authorization packages | Several local object, publication and workbench policies | Adapt to Core decisions while preserving sealed-bid and tender-specific constraints |

## 3. Route and capability matrix

Each row is a migration unit. Gate 05 must expand the row to endpoint-level evidence before marking it Done.

| ID | Module / surface | Discovery or route | Required capability class | Authoritative context and relationship | Current guard/action source | Finding / required replacement |
|---|---|---|---|---|---|---|
| `SURF-CORE-001` | Authenticated landing | Desk boot/module registry | My work discovery | Effective assignments and current tasks | Role/module navigation | Workflow users can land on a functionally irrelevant module workspace; route operational users to `/desk/my-work` |
| `SURF-CORE-002` | My Work | Workspace `My Work` | Task list/claim | Current named task or eligible queue membership | Static shortcuts | No task query, assignment state, counts or protected server routes exist |
| `SURF-CORE-003` | Scope resolution | Shared scope services | Effective access | Active assignment, PE/OU descendants and resource scope | USA rows plus Administrator/User Permission fallbacks | Missing status, capability profile, resource scope, effective-time enforcement and safe cache invalidation |
| `SURF-STR-001` | Strategy workspace and lists | Strategy workspace/API list and context services | `strategy.list`, `strategy.view` | Plan PE/OU, ownership and state | Module role/scope services | Migrate discovery/counts and neutral projections to shared decision |
| `SURF-STR-002` | Strategy editing/submission | Builder/form mutation services | `strategy.edit`, `strategy.submit` | Owner relationship, PE/OU and editable state | Module transition checks | Retain state logic; replace subject/scope/action authority |
| `SURF-STR-003` | Strategy review/approval | Review routes and transition APIs | Qualified review/approval capability | Current task, assignment, state and SoD | Role/state logic; some work assigned from submitter/owner | Create governed tasks; remove inferred actor assignment and direct role action construction |
| `SURF-STR-004` | Strategy notifications | Notification service deep links | Current task view | Named task actor and current state | Module-selected recipients/routes | Generate only from authorized Workflow Task and re-authorize at open |
| `SURF-BUD-001` | Budget portfolio/list/count | Budget portfolio and list contracts | `budget.list`, `budget.view` | Effective PE/OU/resource scope and view profile | Role-visible statuses and scoped entity helpers | Status-derived visibility/actions can expose workflow affordances; use authorized projection |
| `SURF-BUD-002` | Budget neutral detail | Overview/activity/downstream/audit loaders | `budget.view` | In-scope Budget relationship and released evidence | Frappe read plus module role checks | Separate owner/oversight/support fields from protected review evidence |
| `SURF-BUD-003` | Budget registration/edit | Register, line and revision commands | `budget.create`, `budget.edit` | Effective assignment, ownership and editable state | `budget_permissions.py` role checks | Replace role-only capability source and preserve server business validation |
| `SURF-BUD-004` | Budget review/return | Readiness and revision review commands/routes | `budget.review`, `budget.return` | Current assigned task, PE/resource scope, Submitted state and SoD | `can_review_budget`/role and status | Role currently implies review across records; protect task loader and command with assignment |
| `SURF-BUD-005` | Budget authority activation/approval | Activation/apply revision commands | Qualified Budget authority capability | Current authority task, evidence, scope, state and SoD | Module role/status checks | Introduce routed authority task and prohibit combined-role self-decision |
| `SURF-BUD-006` | Funding check/reservation | Check/reserve services | Funding view/reserve command | Budget Line resource scope, source Demand/Plan Item and current task | Record/service checks | Apply effective resource assignment and task relationship; retain financial invariants |
| `SURF-BUD-007` | Budget exports/reports | Funding performance/export actions | `budget.export`/oversight | Authorized post-filter projection | Module export role helper | Filter rows/counts before export and prevent action construction from status |
| `SURF-DEM-001` | Demand workspace/list/count | Demand API/workspace | `demand.list`, `demand.view` | Owner/related actor, PE/OU and released state | Large module API with USA queries and role checks | Centralize discovery projection; no inaccessible count contribution |
| `SURF-DEM-002` | Demand owner form/detail | Demand form/detail routes and loaders | `demand.edit` or neutral `demand.view` | Creator/owner unit and current state | Module permission functions | Split neutral Track/View projection from editable owner surface |
| `SURF-DEM-003` | Enrichment and sign-off | Enrichment/Budget/HOD/Procurement task routes | Qualified task capability | Current task assignment, PE/OU/resource scope and state | Module stage/role conditions | Replace generic stage-driven Review links with server task actions |
| `SURF-DEM-004` | Demand decisions | Submit/review/return/approve mutations | Qualified task decision | Current assigned/claimed task, state and SoD | Module guards | Add task identity and shared decision at mutation boundary |
| `SURF-DEM-005` | Demand notifications/handoff | Notification and Planning handoff services | Current task view / downstream handoff | Authorized recipient and trusted approved record | Module-selected routes | Route notifications through Workflow Task; retain downstream artifact ownership |
| `SURF-PLN-001` | Planning workspace/list/count | `/desk/planning-workspace` and workspace service | `plan.list`, Planning operational actions | Planner assignment plus selected in-scope PE/FY preference | Local role/scope; Budget Officer patch | Remove decision-role work discovery; workspace remains Planner operational surface |
| `SURF-PLN-002` | Plan neutral view | Approved/implementation Plan routes | `plan.view` | PE/OU, relationship and view profile | Planning-local capability | Add neutral owner/oversight/support field projections and no task controls |
| `SURF-PLN-003` | Plan builder/item editor | Builder/editor loaders and mutations | `plan.edit`, `plan_item.edit`, `plan.submit` | Planner ownership/scope, Draft state | Local role map and route parameters | Consume shared decision; preserve Planning state/invariants |
| `SURF-PLN-004` | Plan Item Finance task | Finance loader, confirm and return commands | `plan.finance.task`, `plan.finance.confirm/return` | Current named/claimed task, PE/FY/resource scope, state and SoD | Embedded task fields plus exact assignee checks | First task migration: shared Workflow Task and canonical routing rule |
| `SURF-PLN-005` | Professional review task | Review loader, recommend/return/approve commands | Qualified professional task capability | Current assigned task, Version state and SoD | Embedded Version task fields and role search | Replace with routed Workflow Task and shared decision |
| `SURF-PLN-006` | Planner waiting projection | Planning workspace waiting rows | Authorized originating-work relationship | Current task owner visibility profile | Generic `Budget Officer` fallback | Show permitted named user/queue only; never expose decision route |
| `SURF-PLN-007` | Planning notifications | Finance/review notification services | Current task view | Named task/queue and current state | Embedded assignee and constructed deep link | Generate from task projection and carry stable task ID only |
| `SURF-PLN-008` | Planning support view | Read-only Planning projection | `support.record.view` | Explicit support scope and purpose | Planning support seed/local read-only behavior | Use shared support assignment and audit each read |
| `SURF-TND-001` | Tender workbench/list/count | Tender workbench queues and detail loaders | `tender.list`, `tender.view` | PE/OU, tender relationship, phase and confidentiality | Separate workbench/object-scope policies | Adapt to shared discovery while preserving tender object policy |
| `SURF-TND-002` | Tender preparation/edit | Configuration and preparation services | `tender.edit` | Current preparer task, ownership and Draft state | Frappe permissions/local security | Remove Administrator/test authority from production policy path |
| `SURF-TND-003` | Publication review/approval | Review, publication and approval commands | Qualified publication task capability | Current assignment, readiness, state and SoD | Independent publication authorization package | Make Core task decision mandatory; retain publication-specific readiness |
| `SURF-TND-004` | Addendum/cancel/retender/handoff | Lifecycle command services | Qualified lifecycle capability | Current task/authority, state and SoD | Local access-rule adapters | Map denials and authority through shared decision |
| `SURF-TND-005` | Tender evidence export | Evidence export service | `tender.export`/oversight | Authorized view profile and sealed-data corridor | Local authorization/redaction | Keep redaction; require shared record/support/oversight projection first |
| `SURF-TND-006` | Bid content/opening | Bid loaders/opening services | Legally qualified bid-open/view capability | Opening state, committee/current task and statutory boundary | Tender-specific hard denials | Shared policy must never weaken sealed/unopened protections |
| `SURF-XMOD-001` | Global counts/search/selectors | Home, sidebar, global search and link selectors | Module list/view capability | Effective assignment and authorized records | Mixed module queries | Apply shared post-authorization filtering before count or result creation |
| `SURF-XMOD-002` | Reports and exports | Module reports/export endpoints | Module export/oversight capability | Authorized row projection | Mixed Frappe/module checks | No inaccessible row/count/identifier leakage |
| `SURF-XMOD-003` | Notifications/deep links | Module notification services | Current record/task view | Current assignment/relationship and state | Module recipients and constructed routes | Build from authorized projection and re-authorize every open |

## 4. Leakage and correctness register

| ID | Severity | Finding | Consequence | Owning migration |
|---|---|---|---|---|
| `LEAK-001` | Critical | Generic roles and module-local role maps are used as capability authority | Possessing a role can expose actions without governed assignment | Gate 01 policy and scope migration |
| `LEAK-002` | Critical | Planning chooses an assignee by eligible role rather than a governed routing-rule version | Seed/order changes can route work to the wrong person with no reproducible rule | Gate 02 routing |
| `LEAK-003` | Critical | Workflow task authority is embedded in business records | No cross-module queue, routing evidence or coherent task discovery | Gate 01/02 Workflow Task migration |
| `LEAK-004` | High | Budget action DTOs are constructed from record status | Neutral viewers may receive misleading Review actions | Budget Gate 05 migration |
| `LEAK-005` | High | My Work is a static list shortcut | Assigned actors cannot discover work across scopes; role users see useless landing pages | Gate 03 |
| `LEAK-006` | High | Administrator/System Manager exceptions exist in several Tender paths | Technical privilege can become operational authority | Tender Gate 05 migration |
| `LEAK-007` | High | Notifications carry module-constructed task routes and embedded assignees | Reassignment/stale state may leave misleading deep links | Gate 02 and cross-module notifications |
| `LEAK-008` | High | Support behavior is Planning-local rather than an explicit shared support profile | Administrator/support record visibility is inconsistent and under-audited | Gate 04 |
| `LEAK-009` | Medium | Static authorization artifact filenames do not match ledger IDs and routing-rule HTML is absent | Traceability and literal UI verification are ambiguous | Gate 04 UI artifact normalization |
| `LEAK-010` | Critical | Multiple independent authorization engines exist in Tender | Equivalent actions can produce inconsistent allow/deny decisions | Shared adapter rollout with sealed-data constraints |

## 5. Public replacement boundary

Core will publish stable service interfaces without importing module internals:

```text
evaluate_capability(user, capability, resource_ref, context_ref=None)
require_capability(user, capability, resource_ref, context_ref=None)
resolve_effective_access(user, capability=None, at_time=None)
get_authorized_record_projection(user, resource_ref, requested_profile=None)
get_available_actions(user, resource_ref, task_ref=None)
resolve_routing(task_spec)
create_task_for_transition(task_spec, idempotency_key)
get_my_work(user, filters=None)
```

Modules provide registered resource adapters that derive authoritative PE/FY/OU/resource, state, relationships, confidential-field profile and module actions. The shared service evaluates authority; module services execute business transitions after `require_capability` succeeds.

## 6. Migration order

1. Core records, decision service, audit and compatibility facade.
2. Routing, named-user tasks, queue claim, delegation and SoD.
3. My Work and role-aware entry.
4. Procurement Planning Finance task as the first end-to-end task migration.
5. Planning professional review and support projections.
6. Budget and Demand task surfaces.
7. Strategy workflow surfaces.
8. Tender surfaces, retaining sealed-data and publication constraints.
9. Cross-module counts, search, exports and notifications.
10. Remove compatibility fallbacks only after endpoint-level tests prove each migrated surface.

## 7. Gate 00 exit

- Shared owner and dependency boundary: approved.
- Existing infrastructure disposition: approved.
- MVP workflow surface matrix: recorded.
- Leakage register and migration order: recorded.
- Runtime behavior: intentionally unchanged in Gate 00.

Gate 01 may begin with standard Frappe-generated Core DocTypes and the shared deny-by-default policy contract.
