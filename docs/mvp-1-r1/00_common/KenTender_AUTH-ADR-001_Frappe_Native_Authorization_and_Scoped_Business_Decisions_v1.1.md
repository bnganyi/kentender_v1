# AUTH-ADR-001 — Frappe-Native Authorization and Scoped Business Decisions

| Control | Value |
|---|---|
| Document ID | AUTH-ADR-001 |
| Version | 1.1 |
| Date | 27 August 2026 |
| Status | Proposed for approval |
| Applies to | All KenTender modules, business commands, lists, tasks and administration |
| Corrects | CFG-CHG-002 v0.3 custom permission mechanism, five-role Reference Data model and propagated “effective assignment” references |
| Implementation owner | `kentender_core` permission integration plus each domain service |

## 1. Decision

KenTender shall use Frappe's native authorization records as the authoritative source of user access:

- **Frappe Roles** define functional responsibility and DocType operations;
- **Frappe Role Permission Manager** defines DocType-level read, create, write, submit, cancel and related permissions;
- **Frappe User Permissions** restrict access to exact linked business scopes such as Procuring Entity, PE/FY Context and Organisation Unit; and
- **server-side domain commands** enforce record state, task responsibility, delegation validity, maker-checker, segregation of duties, concurrency and business invariants.

KenTender shall not maintain a parallel generic authorization store made from `Capability Profile` and `Operational Scope Assignment` records.

Native authorization shall not be used to preserve unnecessary business-role proliferation. A distinct Frappe Role requires a stable, recognisable business responsibility; it shall not be created merely to represent one step in a low-risk administrative workflow.

Reference Data maintenance uses one global business Role: **Reference Data Manager**. It replaces Central Reference Data Steward, Central Configuration Approver, PE Configuration Steward and Professional Configuration Reviewer for PE, FY and PE/FY Context maintenance. Accounting Officer and Head of Procurement Function retain their downstream procurement responsibilities but perform no Reference Data action by virtue of those roles.

The replacement rule is:

> Effective business authority = applicable Frappe Role + applicable Frappe User Permission scope + eligible record/task state + valid delegation where used + segregation and business-rule checks.

Frappe Role possession is necessary where a command requires that role, but it is not sufficient to bypass scope, state, task or segregation checks. Conversely, KenTender shall not deny a user who has the required native Role and scope merely because a separate custom capability record is absent.

## 2. Defect being corrected

CFG-CHG-002 v0.3 stated:

> Role labels alone are insufficient. The server shall resolve effective assignment, PE scope, optional FY scope, delegation, segregation and record state at command time.

The intended control was valid: a role must not authorize an action outside the user's scope or the record's lawful state.

The document did not define “effective assignment” through Frappe's native permission model. It also described command inputs and audits in terms of abstract capabilities and effective assignments. This permitted the implementation to introduce:

1. a Frappe Role used partly for Desk and DocType access;
2. a `Capability Profile` containing custom capability strings; and
3. an `Operational Scope Assignment` linking a user to that profile and resource scope.

The custom policy service then treated the third record as the actual grant. A user could therefore hold the visible Frappe Role and still receive `CAPABILITY_NOT_ASSIGNED` because the hidden parallel assignment was missing.

This is an architecture and provisioning defect, not merely incomplete seed data. The two grant systems can disagree, standard Frappe administration does not explain the resulting denial, and no invariant provisions or revokes both reliably.

## 3. Supersession and interpretation

If approved, this ADR has the following effect:

| Source | Effect |
|---|---|
| CFG-CHG-002 v0.3 role, lifecycle, permission, service, seed and acceptance text | Superseded. CFG-CHG-002 v0.4 retains canonical PE/FY references while replacing the five-role/two-chain model with one Reference Data Manager. |
| CFG-CHG-002 v0.4 | Aligned implementation contract for Reference Data authority and lifecycle; no `reference_data.*` capability strings. |
| PLN-GF-002 v0.2 and Planning documents | “Effective assignment” is reinterpreted under section 1 of this ADR; it is not a custom DocType. |
| Departmental Needs, Strategy, Budget, Requisition and later-module documents | Same reinterpretation. Roles, scope, task, delegation and segregation requirements remain; custom capability storage does not. |
| Existing Capability Profile and Operational Scope Assignment implementation | Not implementation authority for new work. Subject to the controlled migration in section 12. |
| Existing business decisions and audit history | Remain immutable. This ADR changes authorization resolution, not historical decision meaning. |

The canonical replacement wording is:

> Business authority requires the applicable Frappe Role, Frappe User Permission scope, current record or task state, and server-side delegation, segregation and invariant checks. KenTender does not use a parallel generic capability-grant store.

## 4. Authorization layers

| Layer | Authoritative mechanism | Question answered |
|---|---|---|
| Authentication | Frappe User/session | Who is making the request? |
| Functional role | Frappe Role | What business responsibility may this user perform? |
| DocType permission | Role Permission Manager and DocType permission hooks | What operations may the role perform on this record type? |
| Business scope | Frappe User Permission | For which PE, PE/FY Context, OU or other governed Link value? |
| Record visibility | Frappe permission query conditions and `has_permission` integration | Which records may the user list or read? |
| Workflow/task eligibility | Domain record/task state and permitted role | Is this action currently available to this user? |
| Delegation | Governed, purpose-specific Delegation mechanism | Is the user temporarily acting for another office within an exact scope and period? |
| Segregation | Domain command checks against actor and prior decisions | Is this actor prohibited because of an earlier incompatible action? |
| Audit | Frappe audit plus immutable domain Decision records | Who acted, under which role/scope, when and with what result? |

No layer may silently grant broader authority than the preceding native role and scope permit.

## 5. Frappe Roles

### 5.1 Role purpose and restraint

Every named KenTender business responsibility shall be an ordinary Frappe Role with an exact, stable label. Examples include:

- Reference Data Manager;
- Head of User Department;
- Head of Procurement Function;
- Procurement Planner;
- Budget Officer;
- Accounting Officer;
- Internal Auditor; and
- Requisition Preparer.

Roles control more than menu visibility. Their DocType operations shall be configured through ordinary Frappe Role Permissions. Workspaces and pages may also use Roles for visibility, but hidden navigation is never security authority.

A new Role is justified only when all of the following are true:

1. a named business office or enduring responsibility exists;
2. the responsibility needs a materially different set of actions or scope;
3. the distinction will be provisioned and understood in ordinary administration; and
4. an existing Role plus record state and User Permission cannot express it safely.

Maker, reviewer and approver labels shall not automatically become three Roles. A canonical domain may require maker-checker or segregation for a material business decision, but Reference Data maintenance does not impose that pattern without a documented legal or policy requirement.

### 5.2 Global and scoped roles

Each role shall be classified explicitly as one of:

| Classification | Rule |
|---|---|
| Global central role | Role itself supplies the intended central scope for named central reference functions. No PE User Permission is required unless the role definition says otherwise. |
| PE/FY-scoped role | Role requires a User Permission for each permitted `PE Fiscal Year Context`. |
| OU-scoped role | Role requires the permitted PE/FY Context plus Organisation Unit User Permission. |
| Oversight role | Role requires the exact oversight scope and remains read-only unless a canonical module grants a decision. |

The classification is part of the role registry and test contract. It shall not be inferred from a display label at runtime.

**Reference Data Manager** is the approved global central Role for PE, FY and PE/FY Context maintenance. It requires no PE-specific User Permission and no hidden `REFDATA-*` or `reference_data.*` capability record. Downstream module roles remain scoped through exact native User Permissions.

### 5.3 Role combinations

Users may hold several Roles. Role union does not remove:

- User Permission scope;
- current task ownership;
- state-transition guards;
- maker-checker separation; or
- actor-specific segregation rules.

System Manager or Administrator technical access does not confer a business approval role.

## 6. Frappe User Permission scope

### 6.1 Primary scope records

KenTender shall use User Permissions on governed linked records:

| Scope | User Permission target | Use |
|---|---|---|
| Exact operating context | `PE Fiscal Year Context` | Preferred scope for PE/FY business records. Avoids accidental Cartesian PE/FY combinations. |
| Organisational unit | `Organisation Unit` | Restricts departmental preparation, review and operational access. |
| Procuring Entity | `Procuring Entity` | Used for PE master/reference access where no PE/FY record is applicable. |
| Other governed master | Exact linked DocType | Used only when a module's canonical contract requires it. |

Downstream business records shall carry formal Link fields to their governing PE/FY Context and OU where applicable. Scope shall not depend on free-text codes or generic references that Frappe cannot permission reliably.

### 6.2 Read, list and count consistency

- Frappe permission-aware ORM reads shall be used by default.
- Custom list or aggregation services shall apply the same Frappe User Permission and permission-query predicate as record reads.
- Direct document routes and File downloads shall recheck permission.
- A list, count, task queue and detail service shall not use different scope logic.
- Unauthorized records shall return the same not-found treatment as nonexistent records where existence is protected.

### 6.3 Scope selection

The global PE/FY selector filters among contexts already permitted by native authorization. Selecting or remembering a context never grants access. Every read and command revalidates the selected context.

## 7. Business-command authorization

Every material command shall perform these checks server-side in this order:

1. authenticated, enabled System User;
2. required Frappe Role;
3. required DocType permission;
4. matching User Permission scope, unless the role is explicitly global;
5. record belongs to that exact scope;
6. record and task are in the eligible state;
7. task is addressed to the actor's role/scope where a task exists;
8. delegation is valid where the actor relies on one;
9. maker-checker and segregation rules pass;
10. expected record version and decision token are current; and
11. all domain invariants pass.

The command returns a stable business error without exposing cross-scope data. The client cannot submit a role, scope, actor, available action or permission result as authority.

### 7.1 Available actions

The server computes available actions from the same predicate used by the command. The UI shall not show an action that the current server projection says is unavailable. Hiding or disabling the action remains usability only; the command repeats every check.

### 7.2 Policy helper

A shared `authorization_policy` helper may remain, but its permitted responsibility is limited to:

- reading Frappe Roles and native User Permissions;
- applying explicit global/scoped role definitions;
- checking current record/task state;
- checking purpose-specific delegation;
- applying segregation rules; and
- returning a safe allow/deny result.

It shall not query `Capability Profile` or `Operational Scope Assignment` as an authority grant and shall not maintain a second role-to-capability registry that administrators must provision.

## 8. Workflow and task authority

Frappe Role permissions establish eligibility to work with a DocType. A workflow transition or protected command also requires the exact state and, where applicable, the current task.

| Scenario | Required authority |
|---|---|
| Department user saves Draft | Requisition Preparer Role + PE/FY Context and OU User Permissions + editable Draft state |
| HoD submits Requisition | Head of User Department Role + matching context/OU + open HoD task or direct-HoD rule |
| Procurement authorises Requisition | Head of Procurement Function Role + matching PE/FY Context + open Procurement task + segregation pass |
| Reference Data Manager enables a PE/FY Context | Reference Data Manager Role + eligible reference state + uniqueness and prerequisite checks; no custom capability or separate Accounting Officer approval |
| Internal Auditor reads evidence | Internal Auditor Role + oversight User Permission scope + read-only permission |

No generic capability string such as `reference_data.pe.create_draft` is required to make these decisions.

## 9. Delegation

Delegation is the only authorized narrow extension where temporary acting responsibility cannot be represented safely by a permanent Role assignment.

A governed Delegation shall contain only:

- delegator and delegate;
- delegated Frappe Role/responsibility;
- exact PE/FY Context and OU scope where applicable;
- effective-from and effective-to instants;
- authority reference;
- status; and
- immutable activation, expiry and revocation evidence.

Delegation shall provision or resolve the same native Role and User Permission semantics. It shall not point to a Capability Profile.

Rules:

- delegation cannot exceed the delegator's own responsibility or scope;
- activation and expiry are fail-closed;
- a command relying on delegation revalidates its time and status;
- revocation takes effect immediately;
- one delegation cannot bypass maker-checker or segregation; and
- ordinary permanent access shall not be represented as a perpetual delegation.

If a module has no approved delegation requirement, no Delegation record or UI is implemented for it.

## 10. Segregation of duties

Segregation remains a domain rule, not a permission bundle.

The server shall inspect the current actor and immutable prior decisions for the same governed transaction. Examples:

- the creator of a proposal cannot approve it where maker-checker is required;
- one actor cannot perform both required independent decision stages;
- a preparer cannot act as HoD merely because they also hold a departmental role when the module prohibits that combination; and
- Administrator or System Manager cannot substitute for a named business decision role.

The denial identifies the incompatible earlier action without exposing protected content.

## 11. Access provisioning and administration

### 11.1 One governed operation

KenTender administration shall provide one coherent grant operation that writes only native Frappe access records:

1. select the user;
2. select one Frappe business Role;
3. select the exact required scope for scoped roles;
4. validate that the role classification and scope are compatible;
5. add the Role and required User Permission records in one transaction;
6. show the resulting effective access; and
7. record actor, time and authority/reference for audit.

Revocation removes only the access granted by the selected operation and preserves access independently justified by another active grant or delegation. Implementation shall not delete a shared User Permission or Role row without checking remaining sources.

This operation may be a small KenTender administrative service/UI over Frappe records. It is not a new authoritative `Access Grant`, Capability Profile or Operational Scope Assignment DocType.

### 11.2 Diagnostics

The administrator shall be able to see, for one user:

- assigned KenTender Roles;
- each Role's global/scoped classification;
- native User Permission scopes;
- current delegations;
- missing scope required by a scoped Role;
- expired or conflicting access; and
- the resulting permitted module contexts.

A role-without-required-scope condition shall be detected during administration, not discovered only when the user executes a command.

### 11.3 Direct Frappe administration

Direct use of standard Frappe Role and User Permission screens remains valid for authorized system administrators. KenTender's diagnostics shall identify incomplete combinations created through those screens. It shall not silently manufacture broad scope.

## 12. Controlled migration from the custom grant model

This section is a future implementation contract, not implementation authority. It applies only when migration is separately authorized. This ADR does not authorize immediate deletion of existing permission records. Any later migration must preserve least privilege and avoid accidental broadening.

### 12.1 Inventory and reconciliation

Before cutover, produce a read-only register containing:

- every KenTender Frappe Role assignment;
- every Capability Profile and capability string;
- every active, Draft, expired and ended Operational Scope Assignment;
- every current native User Permission;
- every user-to-role/profile/scope mismatch;
- every active delegation; and
- every business command or permission query that reads the custom grant model.

Classify each user as:

| Classification | Meaning |
|---|---|
| Matched | Role and custom authority agree and map unambiguously to native scope. |
| Role without custom authority | Visible/native Role exists but custom system denies or has no assignment. |
| Custom authority without Role | Custom grant exists without the required native functional Role. |
| Conflicting scope | Native and custom scopes differ. |
| Expired or inactive | No current authority should migrate. |
| Ambiguous | No deterministic least-privilege mapping exists. |

### 12.2 Mapping rules

- Map each active custom capability family to one exact Frappe Role from an approved mapping table.
- Map confirmed central PE/FY reference maintainers to **Reference Data Manager**.
- Do not automatically grant Reference Data Manager to every holder of Central Configuration Approver, PE Configuration Steward, Professional Configuration Reviewer, Head of Procurement Function or Accounting Officer. These roles do not establish continuing Reference Data responsibility.
- Retire Central Reference Data Steward, Central Configuration Approver, PE Configuration Steward and Professional Configuration Reviewer from the Reference Data path after explicit user-by-user reconciliation.
- Remove all `reference_data.*` capability strings from production authorization reads and provisioning.
- Map PE/FY authority to User Permission on the exact PE Fiscal Year Context where possible.
- Map OU authority to exact Organisation Unit User Permission.
- Do not migrate Draft, expired, ended or revoked assignments as active access.
- Do not infer a broad global scope from several partial assignments.
- Do not infer scope from a role label where the role classification requires native scope.
- A truly global central Role follows its approved role classification and needs no fabricated PE assignment.
- Ambiguous or conflicting users require explicit administrator resolution before cutover.

### 12.3 Cutover

1. Run the reconciliation in report-only mode.
2. Resolve every ambiguous or conflicting user.
3. Create missing native Roles and User Permissions idempotently.
4. Verify effective access for named positive and negative fixtures.
5. Deploy the native authorization policy and disable new custom capability assignments in the same controlled release.
6. Run cross-PE/FY/OU, workflow, task, delegation and segregation smoke tests.
7. Mark custom assignment records historical/read-only; do not delete them during initial cutover.
8. Remove custom authorization reads only after contract tests prove no consumer remains.

There shall be no long-lived mode in which either native or custom authority independently grants access. The cutover point is explicit.

### 12.4 Amina Hassan case

The migration shall not create a special-case user fix. It shall resolve Amina through the general rules:

- Amina's Accounting Officer Role supplies only the business authority defined by the modules that use it;
- it gives her no PE, FY or PE/FY Context maintenance action;
- she receives Reference Data Manager only if an authorized administrator explicitly confirms that enduring responsibility; and
- unrelated `REFDATA-CTX-APPROVER` or other custom assignments are not migrated as Reference Data authority.

The positive Reference Data fixture is Lydia Mwangi with the Reference Data Manager Role. This is a normal role assignment, not a user-specific exception.

The post-cutover system shall never return `CAPABILITY_NOT_ASSIGNED` solely because a custom assignment is absent.

## 13. Document remediation

After approval, revise the canonical documents in this order:

1. CFG-CHG-002 v0.4 role, lifecycle, permission, resolver, screen, seed and acceptance sections;
2. shared Configuration/Governance and Planning context terminology;
3. Departmental Needs, Strategy, Budget, Planning and Requisition role/permission sections;
4. test packs and seed contracts; and
5. future Tender Preparation authority rules.

The revisions shall not redesign unrelated business workflows. They shall replace authorization-mechanism wording and remove the Reference Data role proliferation expressly corrected by CFG-CHG-002 v0.4.

Use this normalized phrase:

> The server resolves the actor's required Frappe Role, native User Permission scope, current task/state, valid delegation and segregation eligibility at command time.

Remove or replace references that require:

- Capability Profile;
- Operational Scope Assignment;
- capability JSON strings;
- `CAPABILITY_NOT_ASSIGNED`;
- custom assignment provisioning; or
- audit dependence on a custom assignment ID.

Decision audit shall instead retain actor, effective Frappe Role/responsibility, native scope, delegation reference where applicable, state transition, time and correlation.

## 14. Error contract

| Code | User result |
|---|---|
| `AUTH_ROLE_REQUIRED` | You do not have the required role for this action. |
| `AUTH_SCOPE_REQUIRED` | This record is not available in your assigned Procuring Entity, Financial Year or department scope. |
| `AUTH_TASK_REQUIRED` | This action is not assigned to you. |
| `AUTH_DELEGATION_INACTIVE` | The delegation for this action is not currently effective. |
| `AUTH_SEGREGATION_BLOCKED` | You cannot perform this action because you completed an incompatible earlier step. |
| `AUTH_STATE_CHANGED` | This action is no longer available in the record's current state. |
| `AUTH_CONTEXT_UNAVAILABLE` | The selected operating context is no longer available to you. |

Cross-scope reads return Not found where record existence is protected. Internal role and permission details are logged for support and not exposed to ordinary users.

## 15. Acceptance contract

| ID | Required result |
|---|---|
| AUTH-AC-001 | Role Permission Manager controls each KenTender DocType's allowed operations. |
| AUTH-AC-002 | User Permissions restrict scoped users to exact PE/FY Context and OU records. |
| AUTH-AC-003 | A global central Role works without a hidden custom capability assignment. |
| AUTH-AC-003A | Reference Data Manager alone supplies Reference Data maintenance eligibility; no separate steward, reviewer, central approver or Accounting Officer reference decision is required. |
| AUTH-AC-004 | A scoped Role without required native scope grants no cross-scope record access and is visible in administration diagnostics. |
| AUTH-AC-005 | Native scope without the required Role grants no protected business action. |
| AUTH-AC-006 | List, count, task, detail, direct route and File access use consistent scope. |
| AUTH-AC-007 | Every protected command repeats Role, scope, state, task, delegation and segregation checks server-side. |
| AUTH-AC-008 | UI available actions come from the same server predicate used by commands. |
| AUTH-AC-009 | Valid delegation grants only its exact Role, scope and effective period. |
| AUTH-AC-010 | Expired or revoked delegation fails immediately. |
| AUTH-AC-011 | Maker-checker and prior-action segregation remain enforced regardless of combined Roles. |
| AUTH-AC-012 | Administrator and System Manager cannot perform a business decision without the named business Role and scope. |
| AUTH-AC-013 | Access grant and revocation provision native Role/User Permission records coherently and idempotently. |
| AUTH-AC-014 | Migration broadens no user's access and reports every ambiguous or conflicting record. |
| AUTH-AC-015 | Custom Capability Profile and Operational Scope Assignment are absent from the post-cutover authorization read path. |
| AUTH-AC-016 | Historical custom assignments remain read-only until separately approved archival treatment. |
| AUTH-AC-017 | Amina Hassan and all other users are resolved through general role/scope rules, not user-specific patches. |
| AUTH-AC-018 | No production command returns `CAPABILITY_NOT_ASSIGNED`. |
| AUTH-AC-019 | No production Reference Data command reads a `reference_data.*` capability string. |
| AUTH-AC-020 | Holders of retired Reference Data roles receive no Reference Data maintenance authority unless explicitly reconciled to Reference Data Manager. |

## 16. Minimum test contract

1. Global-role positive test without custom assignment.
2. Scoped-role positive test for one PE/FY Context.
3. Cross-PE, cross-FY and cross-OU negative tests.
4. Role-without-scope and scope-without-role negative tests.
5. List/count/detail/direct-route consistency tests.
6. File-download and task-queue scope tests.
7. Correct-state and stale-state command tests.
8. Task-assigned and task-not-assigned tests.
9. Active, future, expired and revoked delegation tests.
10. Creator/approver and multi-stage segregation tests.
11. System Manager/Administrator business-decision negative tests.
12. Idempotent grant, revoke and reconciliation tests.
13. Migration equivalence tests for every mapped existing capability family and explicit non-migration tests for retired Reference Data actors.
14. No-authority-broadening comparison before and after cutover.
15. Repository search proving no production read depends on Capability Profile, Operational Scope Assignment or capability strings.

## 17. Implementation constraints

- Use supported Frappe permission APIs and permission-aware ORM reads.
- Keep record-level business checks in owning domain services.
- Do not implement permission logic only in Vue, page visibility or disabled buttons.
- Do not add another generic authorization DocType under a different name.
- Do not patch Frappe framework code.
- Do not encode roles or scope in client-posted values.
- Do not use raw SQL that bypasses Frappe permission filtering for user-facing lists.
- Do not grant broad access to make a failing test pass.
- Do not delete custom assignment data until migration evidence and a separate archival decision permit it.
- Use focused TDD for each mapping, permission predicate and command guard.

## 18. Source grounding

Frappe documents Role Permission Manager as the standard role-based DocType permission mechanism and User Permissions as per-user restrictions on records containing specific Link values: [Frappe Users and Permissions](https://docs.frappe.io/framework/user/en/basics/users-and-permissions).

Frappe's permission-aware list APIs apply user permissions for the session user: [Frappe Database API](https://docs.frappe.io/framework/user/en/api/database).

KenTender-specific workflow, segregation, task and audit controls remain necessary domain behaviour layered on those native permissions. They do not require a second generic grant store.

## 19. Approval effect and next work

Approval of AUTH-ADR-001 v1.1 shall:

- supersede the custom authorization mechanism implied by CFG-CHG-002 v0.3;
- supersede the five-role Reference Data model in CFG-CHG-002 v0.3;
- establish Frappe Roles and User Permissions as KenTender's authoritative access records;
- prohibit new Capability Profile and Operational Scope Assignment dependencies;
- establish Reference Data Manager as the only Reference Data maintenance Role;
- require affected canonical documents to adopt the normalized authority wording; and
- block further Tender Preparation implementation until its permission model follows this ADR.

This ADR and CFG-CHG-002 v0.4 are documentation authority only. They do not authorize repository changes, role deletion, data migration or cutover. Implementation requires a separate instruction after the documents are approved and the section 12 inventory is complete.

When separately instructed after approval, the next work is the read-only authorization inventory required by section 12. No Minimal IT Tender Preparation implementation resumes until the Reference Data and native-authorization correction is separately authorized and verified.
