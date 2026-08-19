# KenTender Shared Authorization and Work Assignment Revision Ledger

**Purpose:** Integrated governing record for cross-module identity scope, operational assignment, workflow routing, work discovery, neutral visibility, support access and separation of duties. Each change unit keeps requirements, exact static screen design, implementation rules, deterministic seed evidence and acceptance criteria together.  
**Status:** Active integrated specification and review ledger  
**Started:** 16 August 2026  

## Documentation authority

1. `KENTENDER-MVP-CMOM-1.1` continues to control the cross-module operating model.
2. Approved records in this ledger control shared authorization, operational assignment, workflow routing, work discovery and support-access behavior across KenTender modules.
3. Module ledgers retain ownership of their business records, workflow decisions and task-specific screens. They shall reference the shared services and contracts approved here rather than define conflicting local authorization rules.
4. Under-review records are proposals and are not implementation authority.
5. Where an approved later record supersedes an earlier shared authorization rule, the later approved record controls.

The former standalone scope model, authorization-surface pack, module Requirements documents, static-design prompt packs, implementation packs and demo-data contracts are historical source evidence only. They shall not be revised or reissued as parallel authority. Future shared corrections shall use this integrated ledger structure.

## Status vocabulary

- **Under review** — proposed wording is being discussed and must not be implemented as an approved change.
- **Approved** — the exact integrated change has been accepted and is implementation authority.
- **Rejected** — the proposed change is not applicable.
- **Superseded** — the record has been replaced by a later approved record.

## Change register

| Change ID | Subject | Requirements | Static design | Implementation | Seed and tests | Status |
|---|---|---:|---:|---:|---:|---|
| `AUTH-CHG-001` | Operational scope, workflow routing, role-aware work discovery and support visibility | Yes | Yes | Yes | Canonical and isolated role/scope/task scenarios | Approved |

---

## AUTH-CHG-001 — Operational scope, workflow routing, role-aware work discovery and support visibility

**Status:** Approved  
**Proposed:** 16 August 2026  
**Approved:** 16 August 2026  
**Source:** Role-based MVP testing on 16 August 2026; approved cross-module operating model; approved Procurement Planning ledger; historical PE/OU scope and authorization-surface evidence  

**Observed defect:** A signed-in `MOH Budget Officer+Authority` account opens the Procurement Planning workspace without a resolved Procuring Entity or financial year and sees no actionable work. The same live Planning state shows an open Finance-confirmation task to the Procurement Planner as **Awaiting confirmation — With Budget Officer**. The canonical scenario, however, assigns that task specifically to Peter Otieno. The interface therefore allows one actor to see that work exists while the purported operational actor cannot discover whether it is assigned to them, to another user, to a queue or to nobody. The same access model prevents a System Administrator without an operational assignment from opening even a neutral Plan projection, while providing no sufficient assignment or routing diagnostic.

The defect is cross-module. It cannot be corrected safely by adding another role condition to the Planning page.

### Locked decision boundary

1. A role grants capabilities; it does not grant Procuring Entity, Organisation Unit, financial-year or record ownership.
2. An operational scope assignment grants an effective PE/OU boundary for named capabilities; it does not create or assign work.
3. A financial year is governed record and workspace context. It is not a permanent user assignment.
4. A workflow task is assigned to one named user or one named claimable queue through a governed routing rule. A generic role label is not a task assignee.
5. Assigned and claimable work shall be discoverable across all of the user's effective scopes before a PE/FY filter is selected. A workspace filter shall never be the source of task authority.
6. The Procurement Planning workspace remains the Procurement Planner's operational surface. Budget Officer, Budget Authority, Head-of-Procurement and other decision work shall be discovered from **My work** and opened on protected task surfaces.
7. Neutral record visibility, workflow decision authority, access administration and technical support visibility are separate capabilities.
8. System Administrator status shall never grant an operational review, return, confirmation or approval action. It shall grant configuration and authorization-diagnostic access. Neutral business-record support visibility shall use an explicit support profile and shall be audited.
9. Sealed, unopened or legally restricted information is not part of ordinary support visibility. No support or Administrator capability may bypass a statutory opening or disclosure boundary.
10. Conflicting roles shall not allow the same person to perform incompatible decisions on the same record or workflow instance.
11. MVP correction shall use a clean rebuild of disposable users, assignments, routing rules and task fixtures. It shall not preserve incorrect role-only or seed-order fallbacks.

### A. Requirements

#### A.1 Identity, role and capability

| ID | Requirement |
|---|---|
| `AUTH-FR-001` | Every authorization decision shall evaluate the authenticated user, active capability assignment, effective PE/OU scope, relevant record relationship, current workflow assignment, record and task state, active delegation and separation-of-duties rules. A role name alone shall not authorize discovery, viewing or mutation. |
| `AUTH-FR-002` | KenTender shall maintain module-qualified capabilities for record listing, neutral viewing, owner maintenance, submission, task viewing, task decision, oversight, support diagnostics and access administration. Generic capabilities such as `approve`, `review_anything` or `view_all` shall not be used for operational decisions. |
| `AUTH-FR-003` | A user may hold more than one functional role. The effective action set shall be calculated per record and task; the interface shall not ask the user to select an artificial role merely to obtain or suppress authority. |
| `AUTH-FR-004` | The server shall return permitted actions as part of an authorized projection. The client shall not construct an action from a role label, record status, visible field, selected filter or known identifier. |

#### A.2 Operational scope assignments

| ID | Requirement |
|---|---|
| `AUTH-FR-005` | Each operational scope assignment shall identify one user, one capability profile or functional role, one Procuring Entity, an optional Organisation Unit, descendant coverage, optional governed resource scope, effective dates, status and the assigning authority. |
| `AUTH-FR-006` | A blank Organisation Unit means entity-wide scope only when the assigned capability profile permits entity-wide operation. It shall not be interpreted as an accidental wildcard. |
| `AUTH-FR-007` | Optional resource scope may restrict a capability to governed funding structures, categories or other module-owned resources. Resource scope shall reference authoritative records and shall not be stored as free text. |
| `AUTH-FR-008` | Zero effective operational scopes shall not be presented as zero work. The user's landing page shall state **No active operational assignment is configured for this account** and shall provide the appropriate support path. |
| `AUTH-FR-009` | One effective PE scope may be selected visibly for a module workspace. Multiple effective PEs shall require deliberate workspace selection, but **My work** shall continue to aggregate assigned and claimable tasks across them. Assignment order, alphabetical order, seed order and Administrator status shall never select a PE. |
| `AUTH-FR-010` | Creating, changing, suspending or ending an assignment shall be authorized, audited and effective-dated. It shall invalidate affected authorization caches and shall not silently reassign open tasks. |
| `AUTH-FR-011` | Cross-PE access requires an explicit assignment. Organisation Unit scope and descendant coverage shall be enforced consistently on lists, counts, searches, neutral record loaders, task loaders, exports, notifications and commands. |

#### A.3 Financial-year context

| ID | Requirement |
|---|---|
| `AUTH-FR-012` | Financial year shall be derived from the governed record or task and from the module's configured financial-year periods. No general User-to-Financial-Year assignment shall be introduced. |
| `AUTH-FR-013` | A task shall carry its authoritative PE and financial-year identifiers. Opening a task from **My work** shall establish that request's visible record context after server authorization without changing the user's operational assignment. |
| `AUTH-FR-014` | A deliberately saved PE/FY workspace selection is a navigation preference only. It shall not grant access, alter a task assignment or suppress an assigned task from the unfiltered **My work** count. |
| `AUTH-FR-015` | Module-specific financial-year eligibility and defaulting rules remain owned by the relevant module ledger. The shared authorization layer shall validate the resulting stable PE/FY identifiers and shall not invent a year. |

#### A.4 Workflow routing and task assignment

| ID | Requirement |
|---|---|
| `AUTH-FR-016` | Each assignable workflow step shall use one active, versioned routing rule that identifies task type, owning module, PE, optional OU/resource scope, required capability, assignee strategy, effective dates, priority and fallback behavior. |
| `AUTH-FR-017` | The admitted assignee strategies are **Named user** and **Named claimable queue**. A generic role, email-domain match, first eligible user, creator, last actor, Administrator or fixture constant shall not be treated as an assignee. |
| `AUTH-FR-018` | A named-user routing rule shall resolve exactly one active user whose operational scope and capability cover the task's authoritative PE/OU/resource scope. A named-queue rule shall resolve one active queue whose membership is independently governed by effective assignments. |
| `AUTH-FR-019` | Task creation shall occur in the same transaction as the workflow transition that requires it. The transaction shall fail without changing the business state when the routing rule is missing, ambiguous, inactive or resolves no eligible actor or queue. |
| `AUTH-FR-020` | A created task shall retain task type, task iteration, business-record references, PE, financial year, OU/resource scope, routing-rule identity and version, assignee type, named user or queue, state, creation actor/time, due time when configured and predecessor task where applicable. |
| `AUTH-FR-021` | A named-user task is actionable only by its current assignee or an authorized effective delegate. A queue task is actionable only after a current queue member atomically claims it, unless the owning workflow explicitly admits a joint committee decision. |
| `AUTH-FR-022` | Claim, release, reassignment and delegation shall be concurrency-safe and audited. Reassignment shall retain prior ownership history and shall not change the underlying business record's ownership or approval state. |
| `AUTH-FR-023` | A workflow task shall never be left with a generic display value such as **Budget Officer** when its true state is named assignment, queue ownership, unassigned or routing failure. Permitted viewers shall see the named actor, named queue or a business-readable configuration exception according to their visibility profile. |
| `AUTH-FR-024` | A completed, returned, cancelled, superseded or stale task shall cease to be actionable immediately. Notification links, cached actions and copied URLs shall be re-authorized against current task state and assignment. |

#### A.5 My work and role-aware entry

| ID | Requirement |
|---|---|
| `AUTH-FR-025` | KenTender shall provide one **My work** landing route that aggregates every current named-user task and claimable-queue task the user can act on across all effective PE/FY scopes. It shall query authorization and task assignment before applying optional workspace filters. |
| `AUTH-FR-026` | Each **My work** row shall show task-specific action wording, business title and reference, module/stage, Procuring Entity, financial year, current assignment, status and received/updated time. Generic **Review** shall not replace a known action such as **Review funding** or **Review Plan update**. |
| `AUTH-FR-027` | The landing route shall distinguish **Assigned to me**, **Available to claim** and **Waiting on others**. Waiting rows shall be shown only when the current user has an authorized relationship to the originating work and shall contain no other actor's decision action. |
| `AUTH-FR-028` | A user with one operational role may receive a direct task-oriented summary, but the route and underlying query shall remain the shared **My work** contract. A multi-role user shall see one combined queue rather than an arbitrary role-selected landing page. |
| `AUTH-FR-029` | Opening a task shall route to the owning module's protected task surface. Opening a module from navigation shall route to that module's authorized neutral or operational workspace; it shall not substitute for **My work** task discovery. |
| `AUTH-FR-030` | A Budget Officer shall not depend on the Procurement Planner's PLN-UI-01 workspace to discover Finance confirmations. An authorized Budget Officer may neutrally view permitted Plan and Plan Item content, but only their current Finance task surface may expose **Confirm funding** or **Return to planner**. |

#### A.6 Neutral, oversight, support and administration access

| ID | Requirement |
|---|---|
| `AUTH-FR-031` | Record discovery, neutral record viewing and workflow-task access are separate capabilities. A user may receive a read-only Plan, Budget, Demand or other record projection without receiving the current task form. |
| `AUTH-FR-032` | System Administrator status shall include access to identity, assignment, routing and authorization diagnostics. It shall not itself include any operational record mutation, review, return, funding confirmation or approval capability. |
| `AUTH-FR-033` | Neutral business-record support visibility shall use an explicit `support.record.view` assignment with PE scope or a separately governed national-support scope. The support projection shall be visibly labelled **Support read-only**, shall omit task decision controls and unreleased decision-only evidence, and shall be audited. |
| `AUTH-FR-034` | Every System Administrator may inspect non-sensitive authorization metadata needed to diagnose a reported access problem: stable record/task identity, PE/FY/OU scope, current task owner type, routing rule and version, required capability, evaluated assignment identifiers and a business-readable allow/deny reason. This metadata access shall not reveal sealed payloads or confidential bid content. |
| `AUTH-FR-035` | Oversight and audit profiles shall be explicitly assigned and shall receive their approved read-only evidence projection. Neither oversight, support nor Administrator status shall cause a workflow task to appear under **Assigned to me**. |
| `AUTH-FR-036` | Support access to a neutral record shall record viewer, time, PE, record identity and purpose category. Any future break-glass access to protected content is excluded from MVP and shall require a separately approved change. |

#### A.7 Separation of duties

| ID | Requirement |
|---|---|
| `AUTH-FR-037` | KenTender shall maintain a governed incompatibility policy for role/capability combinations and for incompatible actions within one workflow instance. |
| `AUTH-FR-038` | The access-administration command shall block an assignment combination that is categorically prohibited. Where roles may coexist for staffing reasons, the task router and decision command shall prevent the same user from performing incompatible decisions on the same record or workflow instance. |
| `AUTH-FR-039` | A combined **Budget Officer+Authority** account shall not be assumed safe. It may be used only where the configured Budget workflows prove that its capabilities are compatible or where record-level separation prevents the same person from confirming and approving the same financial decision. |
| `AUTH-FR-040` | Delegation and reassignment shall re-evaluate separation of duties against the creator, prior submitter, prior decision actors and configured incompatible actions before authority is granted. |

#### A.8 Shared enforcement and audit

| ID | Requirement |
|---|---|
| `AUTH-FR-041` | Lists, counts, global search, selectors, work queues, neutral loaders, task loaders, actions, reports, exports, notifications and mutation commands shall use the same server-side authorization decision service and stable identifiers. |
| `AUTH-FR-042` | Unauthorized actions shall be absent. Disabled controls may be used only when the user is authorized but a non-security prerequisite is unmet. |
| `AUTH-FR-043` | An unauthorized task route shall return no protected task projection. Where neutral viewing is permitted, the application may route to the neutral record with **You do not have access to this task**. An out-of-scope request shall not reveal the protected record's existence. |
| `AUTH-FR-044` | Assignment, routing, claim, release, delegation, support-view and authorization-denial events shall be attributable, timestamped and auditable. Audit evidence shall retain the evaluated policy and routing versions without exposing internal policy detail in ordinary denial messages. |
| `AUTH-FR-045` | Authorization and task projections shall be deterministic, optimistic-concurrency protected where mutable, and invalidated when relevant assignments, queue membership, delegation, task state or routing configuration changes. |

#### A.9 Stable outcomes

| Identifier | User-facing message |
|---|---|
| `NO_ACTIVE_OPERATIONAL_ASSIGNMENT` | **No active operational assignment is configured for this account. Contact your system access administrator.** |
| `WORK_CONTEXT_SELECTION_REQUIRED` | **Select a Procuring Entity and financial year to view this workspace. Your assigned work remains available under My work.** |
| `TASK_ROUTING_RULE_NOT_CONFIGURED` | **This work could not be submitted because no active routing rule is configured for the next step.** |
| `TASK_ASSIGNEE_NOT_AVAILABLE` | **This work could not be submitted because the configured assignee is not currently eligible.** |
| `TASK_ROUTING_AMBIGUOUS` | **This work could not be submitted because more than one routing rule has the same priority.** |
| `TASK_NOT_ASSIGNED_TO_USER` | **You do not have access to this task.** |
| `TASK_ALREADY_CLAIMED` | **This task has already been claimed by another authorised user.** |
| `TASK_NOT_CURRENT` | **This task is no longer current. Return to My work for the latest status.** |
| `SEPARATION_OF_DUTIES_BLOCKED` | **You cannot perform this decision because you completed an incompatible earlier action.** |
| `SUPPORT_RECORD_VIEW_NOT_ASSIGNED` | **You can inspect access configuration, but you do not have support permission to view this record.** |

### B. Domain and projection contracts

#### B.1 Persistent records

##### Operational Scope Assignment

| Field | Contract |
|---|---|
| `assignment_id` | Stable generated identifier |
| `user_id` | Required active user |
| `capability_profile_id` | Required governed profile; expands to module-qualified capabilities |
| `procuring_entity_id` | Required PE |
| `organisation_unit_id` | Optional; must belong to the PE |
| `include_descendants` | Required Boolean |
| `resource_scope_type` / `resource_scope_id` | Optional governed restriction |
| `effective_from` / `effective_to` | Required effective period; end may be open |
| `status` | Draft, Active, Suspended or Ended |
| `assigned_by` / `assigned_at` | Immutable activation evidence |
| `ended_by` / `ended_at` / `end_reason` | Required when ended |
| `concurrency_token` | Required for mutable administration |

##### Workflow Routing Rule

| Field | Contract |
|---|---|
| `routing_rule_id` / `version` | Stable rule identity and immutable effective version |
| `module` / `task_type` | Required owning module and qualified task type |
| `procuring_entity_id` | Required PE; national rules require a separately governed scope |
| `organisation_unit_id` / `include_descendants` | Optional ownership restriction |
| `resource_scope_type` / `resource_scope_id` | Optional funding/category/resource restriction |
| `required_capability` | Required module-qualified task capability |
| `assignee_strategy` | Named user or Named claimable queue |
| `assignee_user_id` / `queue_id` | Exactly one according to strategy |
| `priority` | Required; ties within overlapping active scope are invalid |
| `effective_from` / `effective_to` | Required effective period |
| `fallback_rule_id` | Optional explicit fallback; no implicit first-user fallback |
| `status` | Draft, Active, Superseded or Ended |
| `approved_by` / `approved_at` | Required activation evidence |

##### Workflow Task

| Field | Contract |
|---|---|
| `task_id` / `task_iteration` | Stable task identity and iteration |
| `module` / `task_type` | Required owning module and qualified task type |
| `subject_type` / `subject_id` | Required principal business record |
| `related_record_refs` | Authoritative related records needed for the task |
| `procuring_entity_id` / `financial_year_id` | Required task context |
| `organisation_unit_id` | Optional record-owner context |
| `resource_scopes` | Authoritative funding/category/resource scopes |
| `routing_rule_id` / `routing_rule_version` | Immutable routing evidence |
| `assignee_type` | User or Queue |
| `assigned_user_id` / `queue_id` | Exactly one according to type |
| `claimed_by` / `claimed_at` | Queue-claim evidence where applicable |
| `state` | Open, Completed, Returned, Cancelled, Superseded or Stale |
| `predecessor_task_id` | Required for a later iteration after return where applicable |
| `created_by` / `created_at` / `due_at` | Task chronology |
| `concurrency_token` | Required for claim and decision commands |

##### Delegation

| Field | Contract |
|---|---|
| `delegation_id` | Stable generated identifier |
| `delegator_user_id` / `delegate_user_id` | Required distinct active users |
| `capability_profile_id` | Required governed delegated capability boundary |
| `procuring_entity_id` / optional `organisation_unit_id` | Required delegated scope |
| `effective_from` / `effective_to` | Required bounded period |
| `reason` | Required business reason |
| `status` | Scheduled, Active, Ended or Revoked |
| `approved_by` / `approved_at` | Required activation evidence |

#### B.2 Non-persistent projections

`EffectiveAccessContext`, `MyWorkProjection`, `AuthorizationDiagnostic` and `SupportRecordProjection` are calculated responses. They are not editable business records and shall not be stored as alternative sources of authority.

### C. Capability and visibility matrix

| Actor/profile | Manage assignments/routing | See My work | Neutral records | Protected task | Decide task | Access diagnostics |
|---|---:|---:|---:|---:|---:|---:|
| Operational user in effective scope | No | Own/claimable tasks | According to module capability | Current assigned/claimed task only | Current permitted decision only | Own effective access summary |
| Procurement Planner | No | Planning-owned tasks | Authorized Plan/Demand context | Planner tasks only | Planner commands only | Own effective access summary |
| Budget Officer | No | Assigned/claimable Finance tasks | Authorized Budget/Plan context | Current Finance task only | Confirm funding or Return where current | Own effective access summary |
| Budget Authority | No | Assigned/claimable Budget approval tasks | Authorized Budget evidence | Current authority task only | Configured Budget decision only | Own effective access summary |
| Head of Procurement | No | Assigned/claimable professional tasks | Authorized Plan/Tender evidence | Current professional task only | Configured professional decision only | Own effective access summary |
| Auditor/Oversight | No | No operational tasks | Assigned oversight projection | No | No | Assigned oversight diagnostics |
| System Access Administrator | Yes | No operational tasks from Administrator status | Configuration only unless support profile assigned | No | No | Yes |
| System Support Viewer | No unless separately assigned | No operational tasks | Support read-only projection in assigned support scope | No | No | Yes |
| User outside effective scope | No | No | No | No | No | Own denial summary only |

### D. Exact static screen design

The following are deterministic static reference frames. They contain only visible composition, exact reference data, controls and user-facing copy. Executable routing, assignment validation, queue claims, authorization, saving, task transitions and audit behavior are owned by Requirements and Implementation.

#### D.1 AUTH-UI-01 — My work with an assigned Finance task

**Screen contract**

- **Purpose:** Show the signed-in user every task they can currently perform or claim across effective scopes.
- **Primary actor:** Operational user with one or more current tasks.
- **Entry point:** Home → My work.
- **Writes:** None in this frame; row actions open protected task surfaces.
- **Primary outcome:** Open the correct current task.
- **Exclude:** Planning dashboard metrics, record editing, decision controls, inaccessible counts and role switcher.

Design the main content area for **AUTH-UI-01 My work**. Preserve the existing Procurement navigation, top bar and branding.

Use only this exact reference state:

- Signed-in user: **Peter Otieno**
- Active role: **Budget Officer**
- Effective scope: **Ministry of Health**
- As at: **20 August 2027, 10:00 EAT**

Header:

- Title: **My work**
- Description: **Tasks currently assigned to you or available for you to claim.**

Show one compact context line:

- **1 active assignment · Ministry of Health · All assigned units**
- Text action: **View my access**

Show tabs:

- **Assigned to me 1** — selected
- **Available to claim 0**
- **Waiting on others 0**

Show a compact table with columns:

- Task
- Stage
- Procuring Entity
- Financial year
- Status
- Received
- Action

Show exactly one row:

- Task: **Digital health technical staff certification programme**
- Quiet reference: **PPI-MOH-2027-022**
- Stage: **Finance confirmation**
- Procuring Entity: **Ministry of Health**
- Financial year: **2027/28**
- Status: **Awaiting confirmation**
- Received: **20 August 2027, 10:00 EAT**
- Action: **Review funding**

Below the table show: **Showing all work across your active assignments.**

Do not show PE/FY selectors as prerequisites, **View plan update**, **Continue planning**, Plan summary metrics, Confirm funding, Return to planner, Approve, Reject or another user's task.

#### D.2 AUTH-UI-01A — no active operational assignment

Design the main content area for the no-assignment state of **My work**. Preserve the existing Procurement navigation, top bar and branding.

Use only this exact reference state:

- Signed-in account: **MOH Budget Officer+Authority**
- Displayed roles: **Budget Officer · Budget Authority**
- Active operational assignments: **0**
- Assigned tasks: **0**
- Claimable queues: **0**

Header:

- Title: **My work**
- Description: **Tasks currently assigned to you or available for you to claim.**

Show one restrained blocking panel:

- Title: **No active operational assignment**
- Message: **No active operational assignment is configured for this account. Your roles do not by themselves grant access to a Procuring Entity or workflow task.**
- Supporting text: **Contact your system access administrator and provide the account name shown above.**
- Button: **View my access**

Do not show **No work currently needs your action**, PE or FY selectors, Plan actions, zero KPI cards, workflow decisions or an Administrator fallback.

#### D.3 AUTH-UI-02 — user operational access administration

**Screen contract**

- **Purpose:** Allow an authorized System Access Administrator to inspect and maintain a user's operational scope assignments.
- **Primary actor:** System Access Administrator.
- **Entry point:** Administration → Access management → Users → Operational access.
- **Primary outcome:** Create or update an effective assignment without granting workflow work directly.
- **Exclude:** Task reassignment, decision controls, password management and business-record editing.

Design the main content area for **AUTH-UI-02 User operational access**.

Use only this exact reference state:

- User: **Peter Otieno**
- Account: **moh.budget.officer@example.test**
- Account status: **Active**
- As at: **16 August 2026**

Header:

- Breadcrumb: **Access management / Users / Peter Otieno**
- Title: **Peter Otieno**
- Description: **Operational roles and the Procuring Entity, Organisation Unit or governed resource scopes in which they apply.**

Show a summary strip:

- Account status: **Active**
- Active assignments: **1**
- Current open tasks: **1**
- Separation-of-duties issues: **0**

Section heading: **Operational assignments**

Show a table with columns:

- Role
- Procuring Entity
- Organisation scope
- Resource scope
- Effective period
- Status
- Action

Show exactly one row:

- Role: **Budget Officer**
- Procuring Entity: **Ministry of Health**
- Organisation scope: **All assigned Ministry units**
- Resource scope: **Budget Lines in assigned units**
- Effective period: **1 July 2026 — No end date**
- Status: **Active**
- Action: **View assignment**

Primary page action: **Add operational assignment**

Show one informational note: **Assignments grant scope and capabilities. Workflow tasks are assigned separately through routing rules.**

Do not show Finance decisions, task reassignment, Plan content, role-only access, financial-year assignment or **Act as user**.

#### D.4 AUTH-UI-03 — workflow routing rule detail

**Screen contract**

- **Purpose:** Show the governed rule that assigns a qualified workflow task.
- **Primary actor:** System Access Administrator.
- **Entry point:** Administration → Workflow routing → Finance confirmation — Ministry of Health.
- **Primary outcome:** Understand the exact routing owner and effective rule.
- **Exclude:** Business decision, task completion and free-text role matching.

Design the main content area for **AUTH-UI-03 Workflow routing rule**.

Use only this exact reference state:

- Rule reference: **RTR-MOH-PLN-FIN-001**
- Rule version: **Version 1**
- Status: **Active**

Header:

- Breadcrumb: **Workflow routing / Finance confirmation / RTR-MOH-PLN-FIN-001**
- Title: **Plan Item Finance confirmation — Ministry of Health**
- Status: **Active**

Show read-only rule context:

- Module: **Procurement Planning**
- Task type: **Plan Item Finance confirmation**
- Procuring Entity: **Ministry of Health**
- Organisation scope: **All assigned Ministry units**
- Resource scope: **Budget Lines in assigned units**
- Required capability: **Confirm Plan Item funding**
- Assignment method: **Named user**
- Assigned user: **Peter Otieno**
- Effective from: **1 July 2026**
- Effective to: **No end date**
- Priority: **100**
- Fallback: **None**

Show one eligibility result:

- **Eligible**
- **Peter Otieno has an active Budget Officer assignment covering Ministry of Health and the required funding scope.**

Header actions:

- Secondary: **View routing history**
- Primary: **Create revised rule**

Do not show task decision controls, direct editing of the active version, generic **Budget Officer** as assignee, automatic first-user selection or a financial-year field.

#### D.5 AUTH-UI-04 — authorization diagnostic

**Screen contract**

- **Purpose:** Explain why a user can or cannot discover and open a specific record or task.
- **Primary actor:** System Access Administrator or authorized support viewer.
- **Entry point:** Access diagnostics → inspect user and task.
- **Primary outcome:** Identify the failing authorization or routing condition without granting access.
- **Exclude:** Permission override, impersonation and workflow decision.

Design the main content area for **AUTH-UI-04 Access diagnostic**.

Use only this exact reference state:

- User tested: **MOH Budget Officer+Authority**
- Task: **Plan Item Finance confirmation**
- Task reference: **FT-MOH-2027-002**
- Plan Item: **PPI-MOH-2027-022**
- Procuring Entity: **Ministry of Health**
- Financial year: **2027/28**
- Current task assignee: **Peter Otieno**

Header:

- Title: **Access diagnostic**
- Description: **Read-only evaluation of the current authorization and task assignment.**
- Status: **Access denied**

Show a table with columns **Check**, **Required**, **Actual**, **Result**.

Show exactly these rows:

1. Capability — **Confirm Plan Item funding** — **Role present** — **Passed**
2. Procuring Entity scope — **Ministry of Health** — **No active operational assignment** — **Failed**
3. Financial-year context — **2027/28 from task** — **Available from task** — **Passed**
4. Current task assignment — **Assigned user or claimed queue task** — **Assigned to Peter Otieno** — **Failed**
5. Task state — **Open** — **Awaiting confirmation** — **Passed**
6. Separation of duties — **No incompatible prior action** — **No conflict found** — **Passed**

Show this conclusion:

**This account cannot open the Finance task because it has no active Ministry of Health operational assignment and the task is assigned to Peter Otieno.**

Show text links:

- **View user assignments**
- **View routing rule RTR-MOH-PLN-FIN-001**
- **View task history**

Do not show **Grant access**, **Open task anyway**, impersonation, Confirm funding, Return to planner or protected Finance evidence.

#### D.6 AUTH-UI-05 — neutral support view of a Procurement Plan

**Screen contract**

- **Purpose:** Allow an explicitly authorized support viewer to inspect a neutral Plan projection without operational authority.
- **Primary actor:** System Support Viewer.
- **Entry point:** Authorized record search or access diagnostic → View support record.
- **Primary outcome:** Inspect identifiers and non-decision Plan state needed for support.
- **Exclude:** Planning edits, Finance task, professional review, approval and sealed information.

Design the main content area for **AUTH-UI-05 Support read-only Plan view**. Preserve the existing Procurement navigation, top bar and branding.

Use only this exact reference state:

- Signed-in user: **System Administrator**
- Access profile: **System Support Viewer**
- Procuring Entity: **Ministry of Health**
- Financial year: **2027/28**
- Logical Plan: **PLN-MOH-2027-001**
- Plan title: **Ministry of Health Annual Procurement Plan 2027/28**
- Lifecycle: **Open**
- Current Approved Version: **Version 1**
- Open update: **Draft Version 2**
- Approved value: **KES 455,000,000**
- Draft value: **KES 535,000,000**
- Finance confirmed: **1 of 2**
- Validation: **Needs attention**

At the top show a full-width restrained banner:

- Label: **Support read-only**
- Text: **You can inspect this neutral Plan projection for support. You cannot perform Planning, Finance or approval actions. This access is audited.**

Header:

- Quiet reference: **PLN-MOH-2027-001**
- Title: **Ministry of Health Annual Procurement Plan 2027/28**
- Context: **Open Plan · Approved Version 1 · Draft Version 2**

Show a compact summary strip:

- Approved value: **KES 455,000,000**
- Draft value: **KES 535,000,000**
- Finance confirmed: **1 of 2**
- Validation: **Needs attention**

Show a compact identifiers section:

- Procuring Entity: **Ministry of Health**
- Financial year: **2027/28**
- Current Approved Version reference: **PLN-MOH-2027-001-V1**
- Open Draft Version reference: **PLN-MOH-2027-001-V2**

Only page action: **Back to access diagnostic**

Do not show **Continue planning**, **View plan update**, **Add approved Demands**, Plan Item mutation, Finance decision, Head-of-Procurement decision, task notes, Approve, Return or impersonation.

### E. Implementation contract

#### E.1 Shared authorization decision service

Implement one server-side decision service used by every participating module. Its input shall contain stable subject, resource, action and request-context identifiers. Its result shall distinguish:

- record discovery;
- neutral record view;
- protected task view;
- permitted commands;
- oversight projection;
- support metadata diagnostic; and
- support record projection.

The service shall:

1. load the authenticated user and active capability profiles;
2. resolve effective operational and support scopes at the request time;
3. validate authoritative PE, OU, financial-year and resource ownership from server-loaded records;
4. resolve current task assignment, claim and delegation where a task action is requested;
5. enforce record state and separation of duties;
6. return only permitted projection profile and action descriptors; and
7. record access-sensitive denials and support views according to the audit contract.

No module shall accept client-supplied role, PE label, FY label, owner, assignee, queue, task state, balance or action as authority.

#### E.2 Effective-scope resolver

Create a shared resolver over active Operational Scope Assignments. It shall support entity-wide, exact-OU, descendant and governed resource restrictions without assuming a Ministry-specific hierarchy.

The resolver shall return stable eligible PE/OU/resource identifiers and the capability source. It shall not use role membership without assignment, the first assignment, a fixture account, Administrator status or a saved workspace selection as a scope fallback.

Assignment mutations shall use optimistic concurrency, effective-date validation and overlap checks. Activation shall validate that the OU and resource belong to the selected PE and that the capability profile admits the requested scope.

#### E.3 Routing resolver and atomic task creation

For each workflow transition requiring a new task:

1. lock and reload the business record and current workflow state;
2. derive task type, PE, FY, OU and resource scopes from authoritative records;
3. load active routing-rule versions whose effective scope contains the task;
4. select the one highest-priority non-ambiguous rule;
5. validate the named user or named queue and required effective capability/scope;
6. enforce separation of duties;
7. create or reuse exactly one idempotent task iteration with routing evidence; and
8. commit the business transition and task together.

Missing, ineligible or ambiguous routing shall roll back the transition and return the stable configuration outcome. It shall not create an unassigned task or fall back to a role search.

#### E.4 My work projection

Build **My work** from current Workflow Tasks, queue membership, delegation and authorization—not from a selected module workspace.

The base query shall:

- include open tasks assigned to the current user;
- include open, unclaimed tasks in named queues where the user is a current member;
- include authorized waiting relationships separately;
- apply task-state, PE/OU/resource and separation-of-duties checks before counts are calculated;
- aggregate across all effective PEs and financial years;
- allow optional PE, FY, module, stage and status filters after authorization; and
- return exact task-specific labels and protected target routes from the server.

Clicking an assigned task shall carry only the stable task identifier. The task loader shall derive PE/FY and related records and re-authorize before returning protected content.

#### E.5 Role-aware entry and module navigation

Make `/desk/my-work` the authenticated operational landing route for users with workflow capabilities. Do not route a Budget Officer or multi-role user automatically to the Procurement Planner's `/desk/planning-workspace`.

Module navigation remains capability-aware:

- a Procurement Planner with operational Planning scope may open PLN-UI-01;
- a Budget Officer may open permitted neutral Plan/Plan Item detail and their protected Finance tasks;
- a support viewer may open only the support read-only projection;
- an Administrator without support-record scope receives diagnostics but no Plan content; and
- a user outside scope receives no record projection.

#### E.6 Queue, claim, delegation and reassignment

Queue membership shall be governed by effective assignments. Claim shall lock the open task and succeed for exactly one eligible user. A second claim shall return `TASK_ALREADY_CLAIMED` without changing ownership.

MVP shall support manual authorized reassignment of an open task only from one currently eligible user to another eligible user or from a named queue to an eligible user. Reassignment shall require a reason and retain history. Automatic load balancing, round-robin distribution and workload optimization are deferred.

Delegation shall be bounded by dates, capabilities and scope, require approval and be evaluated at task open and decision time. Delegation shall not bypass separation of duties.

#### E.7 Access administration and diagnostics

Implement separate protected administration commands for:

- create Draft assignment;
- activate assignment;
- suspend assignment;
- end assignment;
- create revised routing rule;
- activate revised routing rule and supersede the prior version;
- create/revise queue membership;
- create/revoke delegation; and
- authorized task reassignment.

Active assignments and routing-rule versions are not edited in place. A material change creates a revised effective record/version so historical authorization and routing remain reproducible.

The diagnostic endpoint shall accept a stable user and optional record/task identity, evaluate the current policy and return only the checks admitted by the administrator/support projection. It shall perform no grant, reassignment, impersonation or workflow mutation.

#### E.8 Support read-only projection

Provide module-qualified support projection builders. For Procurement Planning, the initial projection shall expose Plan identity, PE/FY, lifecycle, Version identities, aggregate values, Finance progress, validation state and non-sensitive identifiers. It shall exclude planner-owned edits, protected Finance evidence, professional-review material and all workflow commands.

Every support-record read shall require `support.record.view` in the relevant support scope and record an audit event. System Administrator status without that profile may inspect authorization metadata but shall receive `SUPPORT_RECORD_VIEW_NOT_ASSIGNED` for business content.

#### E.9 Separation-of-duties engine

Add governed incompatibility rules at both assignment and decision level. At minimum, test:

- requester versus approval of the same Demand;
- planner preparation versus professional approval of the same Plan Version;
- Finance confirmation versus any distinct configured Budget authority approval over the same financial event;
- tender preparation versus a legally separate approval where configured; and
- delegator/delegate combinations that would recreate self-approval.

Where a combined role account remains in test data, it shall prove that possessing both role labels does not bypass the record-level decision exclusion.

#### E.10 Migration and rollout

Because MVP fixture data is disposable:

1. rebuild operational assignments from the canonical user/role/PE/OU data;
2. create explicit routing rules for admitted workflow steps;
3. rebuild open tasks with named assignees and routing evidence;
4. remove generic role-assignee strings and role-only task discovery;
5. remove landing-page selection based on one displayed role;
6. remove PE/FY filtering as a prerequisite for **My work**;
7. add explicit support and access-administration profiles; and
8. verify every rebuilt task against current record ownership and separation of duties.

Do not dual-write old and new assignment models or preserve incorrect orphan tasks for compatibility.

### F. Deterministic seed and scenario contract

#### F.1 Canonical Ministry of Health assignments

| User | Capability profile | PE/organisation scope | Task consequence |
|---|---|---|---|
| Mercy Kilonzo — `moh.planning.officer@example.test` | Procurement Planner | `PE-MOH`, assigned Ministry units | Planner-owned Planning work only |
| Peter Otieno — `moh.budget.officer@example.test` | Budget Officer | `PE-MOH`, assigned Ministry units and their Budget Lines | Receives the Plan Item Finance-confirmation task |
| Grace Wanjiku — `moh.procurement.authority@example.test` | Head of Procurement | `PE-MOH`, assigned Ministry units | Receives the professional Plan-review task |
| `moh.budget.authority@example.test` | Budget Authority | `PE-MOH`, configured Budget authority scope | Receives only admitted Budget authority tasks |
| `system.access.admin@example.test` | System Access Administrator | National configuration scope | Manages assignments/routing and diagnostics; receives no operational task |
| `system.support.viewer@example.test` | System Support Viewer | Support read-only scope for `PE-MOH` | May open the audited neutral Plan support projection only |

The `MOH Budget Officer+Authority` combined account shall be retained only as an isolated negative/compatibility test until its business necessity and separation-of-duties treatment are approved. It shall not receive the canonical Peter Otieno task merely because it contains the words **Budget Officer**.

#### F.2 Canonical Finance task

At the approved PLN-CHG-009 pre-confirmation boundary:

- task reference: `FT-MOH-2027-002`;
- task type: Plan Item Finance confirmation;
- PE: `PE-MOH`;
- financial year: 2027/28;
- Plan: `PLN-MOH-2027-001`;
- Plan Version: `PLN-MOH-2027-001-V2`;
- Plan Item: `PPI-MOH-2027-022`;
- amount: KES 80,000,000;
- routing rule: `RTR-MOH-PLN-FIN-001`, Version 1;
- assignee type: User;
- assigned user: Peter Otieno;
- state: Open / Awaiting confirmation; and
- no `RSV-MOH-0002` exists before confirmation.

The Procurement Planner's waiting projection shall show **With Peter Otieno — Budget Officer** when the viewer is permitted to see the named actor. It shall show the named queue where a queue owns the task. It shall not display a generic role as if that were the assignment.

#### F.3 Isolated scenarios

| Scenario | Required proof |
|---|---|
| `SCN-AUTH-001` — canonical Budget Officer | Peter sees `FT-MOH-2027-002` in My work without selecting PE/FY and opens PLN-UI-07. |
| `SCN-AUTH-002` — combined account without scope | Account sees the exact no-assignment state and no protected task or Plan projection. |
| `SCN-AUTH-003` — role present, wrong assignee | Diagnostic passes capability but fails PE scope and current task assignment exactly as AUTH-UI-04. |
| `SCN-AUTH-004` — System Access Administrator | Administrator sees assignments, routing and diagnostic metadata but no Plan business content or workflow action. |
| `SCN-AUTH-005` — System Support Viewer | Support viewer opens AUTH-UI-05, creates one support-view audit event and receives no task or mutation action. |
| `SCN-AUTH-006` — multiple PEs | My work aggregates authorized tasks across PEs; module workspace requires deliberate PE selection; cross-PE records remain isolated. |
| `SCN-AUTH-007` — named queue | Two eligible queue members see one claimable task; exactly one claim succeeds; the other receives `TASK_ALREADY_CLAIMED`. |
| `SCN-AUTH-008` — missing routing | Workflow submission returns `TASK_ROUTING_RULE_NOT_CONFIGURED` and leaves the business record in its pre-transition state. |
| `SCN-AUTH-009` — ineligible named assignee | Submission returns `TASK_ASSIGNEE_NOT_AVAILABLE`; no task or partial business transition exists. |
| `SCN-AUTH-010` — SoD conflict | A user with two role labels cannot perform an incompatible second decision on the same workflow instance. |
| `SCN-AUTH-011` — stale access | Ending an assignment immediately removes queue/list/task access and invalidates cached actions without completing or reassigning the task. |
| `SCN-AUTH-012` — sealed information | Administrator and support viewer receive no unopened bid payload or statutory-opening bypass. |

Each scenario shall reset only its own assignments, routing versions, queue claims, delegations and tasks. Repeated preparation shall not duplicate assignments, rule versions, task iterations, claims or audit events.

### G. Acceptance evidence

`AUTH-CHG-001` may be marked implemented only when:

1. Peter Otieno sees the canonical Finance task under **My work** without first selecting Ministry of Health or FY2027/28.
2. The Budget Officer task action opens PLN-UI-07 and is absent for the Procurement Planner, Budget Authority, combined unassigned account and System Administrator.
3. The Procurement Planner sees the same task only as neutral **Waiting on others** context and never receives the Finance task route or decision projection.
4. A role label without an effective operational assignment produces `NO_ACTIVE_OPERATIONAL_ASSIGNMENT`, not a misleading empty-work state.
5. Every open workflow task has a named user or named queue and immutable routing-rule evidence; no task is assigned to a generic role string.
6. Missing, ambiguous and ineligible routing failures roll back the owning workflow transition and create no orphan task.
7. My work counts and rows are calculated after authorization across all effective scopes; PE/FY filters cannot grant or suppress base task authority.
8. System Access Administrators can diagnose scope, routing and assignment failures without acquiring workflow authority.
9. An explicitly assigned System Support Viewer can open the neutral audited Plan projection, while an Administrator without support-record scope cannot see the business projection.
10. Cross-PE/OU/resource isolation is enforced on lists, counts, search, selectors, record loaders, task loaders, exports, notifications and commands.
11. Direct task URLs return no protected projection to the wrong assignee, wrong queue member, wrong scope, stale assignment, completed task or SoD-conflicted user.
12. Named-queue claim is atomic and idempotent; reassignment and delegation retain history and re-evaluate capability, scope and SoD.
13. No Administrator, support or oversight profile can Confirm funding, Return, Approve or otherwise mutate a business workflow unless separately and validly assigned an operational capability and current task.
14. Sealed or legally restricted information remains inaccessible through administration, diagnostics and ordinary support visibility.
15. Canonical and isolated seed resets reproduce the same identities, scopes, routing versions, tasks, counts, denials and audit evidence.

### H. MVP-1 boundary and deferrals

The following are mandatory MVP-1 corrections because their absence can hide or orphan governed work:

- effective PE/OU/resource assignments;
- deterministic named-user or named-queue routing;
- atomic task creation failure on invalid routing;
- My work independent of PE/FY filter selection;
- role-appropriate landing;
- exact assignment visibility and diagnostics;
- neutral support projection and explicit support scope;
- separation-of-duties enforcement;
- server enforcement across all discovery, view and task surfaces; and
- canonical role/scope/task seeds and tests.

The following may be deferred to MVP-2:

- automatic load balancing and round-robin assignment;
- skills-, workload- or risk-based routing optimization;
- automated escalation and overdue substitution;
- mass reassignment;
- cross-entity shared-service routing beyond explicit assignments;
- break-glass protected-content access; and
- advanced authorization analytics.

### I. Consequential module corrections

Upon approval:

1. Procurement Planning shall reference this change for PLN-UI-01 discovery, PLN-UI-07 Finance-task access, PLN-UI-08 professional-task access and neutral Plan support visibility.
2. The Planning waiting row shall replace generic **With Budget Officer** with the authorized named actor or named queue.
3. Budget & Funding and Demands shall adopt the same My work, routing, neutral-view and task-surface contracts during their integrated-ledger revision.
4. Later Tender, Evaluation, Award and Contract modules shall use the same assignment and routing records rather than introduce module-local role routing.
5. The historical PE/OU scope model and cross-module authorization pack shall remain evidence only and shall not be reissued.

### J. Open decisions

1. Whether the production System Administrator receives only authorization metadata by default, as proposed, or also receives a default national `support.record.view` assignment. The safer proposed rule is explicit support-record assignment; the deterministic test environment includes a separate System Support Viewer account.
2. Whether any MVP workflow requires a named claimable queue rather than a named user. The shared model admits both; every admitted module route must choose explicitly.
3. Whether the `MOH Budget Officer+Authority` account has a legitimate production use. Until proved, it remains a negative SoD and misconfiguration test rather than a canonical operator.
