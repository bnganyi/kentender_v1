# KenTender Cross-Module Authorization Surface Design and Cursor Pack

**Document ID:** KENTENDER-AUTH-SURFACE-1.0  
**Version:** 1.0  
**Date:** 10 August 2026  
**Status:** Implementation baseline  
**Scope:** Strategy, Budget & Funding, Demands, Procurement Planning, Tendering and later workflow-enabled modules

## 1. Decision

KenTender shall distinguish **permission to view a business record** from **permission to open and perform a workflow task**.

An unauthorized workflow action shall be **absent**, not merely disabled. Its task-specific form shall not render through navigation, a copied URL, an API call or a manipulated client payload.

A user who may legitimately view the underlying record but cannot act on it shall use a neutral read-only record surface such as **View**, **Track** or **View history**. They shall not see the reviewer or approver form.

Disabled buttons are permitted only where the user is authorized for the action but a non-security condition is temporarily unmet, such as incomplete required fields, a validation blocker or a stale task.

## 2. Problem being corrected

The current implementation blocks unauthorized state transitions but still leaks workflow surfaces. For example, a Requester can follow **Review** to the Budget approval screen and see the approval form with disabled actions.

This creates four problems:

1. It exposes functions and possibly evidence that do not belong to the user's role.
2. It gives a misleading impression that the user participates in that approval step.
3. It relies too heavily on disabled client controls instead of denying the workflow surface itself.
4. It makes role behaviour inconsistent across lists, queues, direct routes and APIs.

The correction is not another page-by-page conditional. It is a shared authorization pattern applied to discovery, viewing, task access and mutations.

## 3. Security basis

The design follows these principles:

- deny by default;
- validate permission on every request;
- centralize authorization decisions;
- enforce workflow state and sequencing server-side;
- apply least privilege; and
- evaluate user, resource, action and context attributes rather than role name alone.

These principles align with the [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html), [OWASP REST Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html), [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/) and [NIST SP 800-162](https://csrc.nist.gov/pubs/sp/800/162/upd2/final).

## 4. Authorization model

### 4.1 Authorization is capability-based

Do not authorize a screen using a role check such as `user has Budget Officer` alone.

For every requested operation, evaluate:

> **Role capability + Procuring Entity scope + Organisation Unit scope + record relationship + current workflow assignment + record state + separation-of-duties rules**

The relevant attributes are:

| Attribute | Examples |
|---|---|
| Subject | user, operational role, PE/OU assignments, delegated authority |
| Resource | Budget, Demand, Plan, Plan Item, Tender, workflow task |
| Relationship | creator, owner unit, assigned reviewer, configured approver, auditor |
| Action | view, edit, submit, review, return, approve, publish, create Tender |
| State | Draft, Submitted, Under review, Returned, Approved, Superseded |
| Context | current PE, financial year, current workflow step, active delegation |

Possession of a role does not authorize every record, and permission to view a record does not authorize its current task.

### 4.2 Capability vocabulary

Use a small shared vocabulary and module-qualified capability names.

| Capability class | Examples | Meaning |
|---|---|---|
| Record discovery | `budget.list`, `demand.list`, `plan.list` | Record may appear in an authorized list or count |
| Neutral viewing | `budget.view`, `demand.view`, `plan.view` | Open the ordinary read-only record detail |
| Owner maintenance | `budget.edit`, `demand.edit`, `plan_item.edit` | Edit within the permitted state and ownership scope |
| Submission | `budget.submit`, `demand.submit`, `plan.submit` | Submit the user's authorized work |
| Workflow task | `budget.review`, `budget.approve`, `demand.review`, `plan.approve` | Open the task surface and perform the current decision |
| Oversight | `audit.view`, `management.view` | Read an oversight projection without receiving operational actions |
| Support | `support.view` | Read the support projection without operational authority |

Avoid generic capabilities such as `review_anything` or `approve`. Use the module and business action explicitly.

### 4.3 Current-task rule

A workflow surface may open only when all of these are true:

1. the user has the required operational capability;
2. the record is within the user's PE and OU scope;
3. the record is at the workflow step governed by that capability;
4. the user is the assigned actor, belongs to the authorized claimable queue, or is the configured authority for that step;
5. separation-of-duties rules permit the user to act; and
6. the task is current and has not already been completed, replaced or invalidated.

Role membership without a current task shall not expose the task form.

## 5. Surface architecture

### 5.1 Neutral record surface

Every workflow-enabled business record shall have a neutral detail projection for users who may view it.

Examples:

- **View Budget** — header, amounts, funding context, owner, current status and released decision history.
- **Track Demand** — request content, enrichment status, Budget sign-off status and actionable return reasons.
- **View Procurement Plan** — approved or authorized Draft content without reviewer controls.

The neutral surface shall not contain:

- review or approval controls;
- unreleased internal reviewer notes;
- decision-only evidence outside the viewer's profile;
- hidden workflow fields merely rendered disabled; or
- task assignment controls.

### 5.2 Task surface

Review, return, recommend and approve surfaces are task-specific. They may include evidence and controls necessary for the current decision.

Examples:

- Budget review;
- Budget approval;
- Demand enrichment;
- Departmental sign-off;
- Procurement professional review;
- Accounting Officer approval.

The route loader and data endpoint must require the corresponding current-task capability before returning the task projection.

### 5.3 Oversight and support surfaces

Managers, auditors and support administrators may require broader visibility without operational authority.

Provide an explicit read-only profile:

- **Management/Audit view** may show authorized evidence and history.
- **Support view** may show troubleshooting context and identifiers required for support.

Neither profile inherits review, return or approval capability. System Administrator status alone shall never create an operational workflow task. If support visibility is required, grant `support.view` explicitly and use the neutral support projection.

## 6. Action and navigation rules

### 6.1 Render actions from a server projection

Lists, detail pages and work queues shall render actions returned by the authorization service. Do not construct **Review** or **Approve** from record status alone.

Example response fragment:

```json
{
  "record_view": {
    "allowed": true,
    "profile": "owner"
  },
  "available_actions": [
    {
      "code": "budget.view",
      "label": "View",
      "route": "/budget/BUD-0001"
    }
  ]
}
```

For an assigned Budget Officer, the same record may return `budget.review` with label **Review** and the protected task route.

The projection improves UX but is not the security boundary. Every route and mutation must independently enforce the capability.

### 6.2 Action labels

Use labels that describe what the current user can actually do:

| User relationship | Row action |
|---|---|
| Creator/owner with editable work | Continue or Edit |
| Creator/owner after submission | View or Track |
| Assigned reviewer | Review |
| Configured approver at current step | Approve |
| Manager, auditor or support viewer | View |
| No record-view permission | No row and no count contribution |

### 6.3 Disabled controls

Hide unauthorized actions completely.

Use a disabled action only when the user is authorized for it and the interface needs to explain a temporary business condition, for example:

- **Submit** disabled because required data is incomplete;
- **Approve** disabled because validation is Blocking;
- **Create Tender** disabled because the Plan Item is not Active.

Do not use disabled controls to represent missing role, scope, assignment or separation-of-duties authority.

## 7. Route and API enforcement

### 7.1 Shared authorization services

Implement one shared policy layer with repository-conformant names equivalent to:

```text
evaluate_capability(user, capability, resource, context)
require_capability(user, capability, resource, context)
get_authorized_record_projection(user, resource)
get_available_actions(user, resource)
```

The policy layer shall be used by:

- list and work-queue queries;
- counters and dashboard totals;
- record-detail endpoints;
- task-form loaders;
- workflow mutations;
- exports and reports; and
- notification/deep-link generation.

Do not maintain separate UI and API permission matrices.

### 7.2 Direct-route outcomes

| Condition | Required outcome |
|---|---|
| Not authenticated | Authentication response; do not render the surface |
| Record outside PE/OU or confidentiality scope | Not found response; do not reveal existence |
| Record view allowed but task capability denied | Task endpoint returns forbidden; client may redirect to neutral detail with “You do not have access to this task.” |
| Task was authorized but is now completed or stale | Conflict/stale-task response and return to neutral detail or current queue |
| Task and capability current | Return the task projection and permitted actions |

The server must not send the protected task form and rely on the browser to disable it.

### 7.3 Field-level projection

Use a view profile to control fields as well as actions:

- `owner` — business content, status, released decision trail and return reasons addressed to the owner;
- `reviewer` — owner content plus evidence needed for the current review;
- `approver` — review record, recommendation and evidence required for approval;
- `oversight` — authorized audit/management evidence, read-only;
- `support` — minimum troubleshooting data, read-only.

Do not fetch all fields and hide sensitive sections only with CSS or JavaScript.

## 8. Budget example

| User | Neutral Budget view | Budget review form | Budget approval form | Actions |
|---|---:|---:|---:|---|
| Requester/owner unit | Yes | No | No | View or Track |
| Assigned Budget Officer at review step | Yes | Yes | No | Review, Return or Sign off as configured |
| Configured Budget Approver at approval step | Yes | Review evidence read-only if required | Yes | Approve or Return |
| Manager/Auditor in scope | Yes, oversight profile | No | No | View |
| Support Administrator with `support.view` | Yes, support profile | No | No | View |
| User outside PE/OU scope | No | No | No | None |

The Requester may see that Budget review is pending and later see the released outcome. The Requester must not see the Budget Officer's task form through a **Review** link.

## 9. Queue, count and notification controls

- Work queues shall contain only tasks the user can currently perform or claim.
- General record lists may contain records the user may neutrally view, but their row action must be **View**, not **Review**.
- Counts must be calculated after authorization filtering; do not reveal inaccessible record counts.
- Search, export and report queries must apply the same policy.
- Notifications shall be generated only for authorized actors and shall deep-link to the surface they may open.
- When an assignment or delegation changes, cached actions and notifications must not bypass the current server decision.

## 10. Audit requirements

Audit successful workflow decisions and material authorization changes.

Record denied attempts to open sensitive task routes or call task mutations with:

- user;
- capability requested;
- resource type and safe identifier;
- time;
- denial category; and
- request correlation identifier.

Do not expose the policy internals or another user's assignment in the denial message.

## 11. Cursor implementation sequence

Run each prompt separately and stop at its gate.

# Cursor Prompt 00 — Authorization-surface audit

```text
Perform a read-only cross-module audit of KenTender authorization surfaces.

Inventory every:
- list, workspace, queue, count, report and export;
- row action labelled View, Continue, Review, Return, Recommend, Approve, Publish or Create Tender;
- neutral detail route;
- workflow task-form route and loader;
- workflow mutation endpoint;
- notification deep link; and
- client-side role or disabled-button condition.

For each surface, record:
- module and record type;
- capability it should require;
- PE/OU scope source;
- record-state requirement;
- assignment/authority requirement;
- separation-of-duties rule;
- current server guard;
- current UI condition; and
- identified leakage.

Demonstrate the reported Budget gap with a Requester test account, but do not change code.

Return a route/capability matrix, leakage list, reusable permission infrastructure and ordered replacement plan. Do not propose page-specific patches as the primary solution.
```

**Gate 00:** The route/capability matrix and exact shared replacement boundary are approved.

# Cursor Prompt 01 — Central capability policy and guards

```text
Implement the shared authorization policy approved at Gate 00.

The decision must evaluate:
- module-qualified capability;
- user operational role;
- PE and OU scope;
- record ownership/relationship;
- current workflow state;
- current assignment, claimable queue or configured authority;
- active delegation; and
- separation-of-duties constraints.

Implement shared equivalents of:
- evaluate_capability;
- require_capability;
- get_authorized_record_projection; and
- get_available_actions.

Enforce deny by default. Use the shared guard on list queries, counts, record loaders, task loaders, mutations, exports and notification links.

Do not trust hidden or disabled client controls. Do not grant operational capability from System Administrator status. Preserve explicit support_view as read-only where configured.

Add unit and transaction tests covering allow, deny, out-of-scope, wrong-state, wrong-assignment, stale-task, delegation and separation-of-duties cases.
```

**Gate 01:** Central policy tests pass and no audited task endpoint relies only on client authorization.

# Cursor Prompt 02 — Neutral and task-specific projections

```text
Implement separate authorized projections for neutral record viewing and workflow tasks.

Neutral detail:
- show business content, current status and the released decision trail permitted by the user's view profile;
- provide View or Track actions;
- never include reviewer/approver controls or unreleased internal evidence.

Task surface:
- require the module-qualified current-task capability before returning data or rendering the page;
- return only the evidence and actions required for the current decision;
- reject direct URL access when the capability, scope, assignment or state is invalid.

Lists and queues:
- render actions only from server-returned available_actions;
- omit unauthorized actions rather than disabling them;
- use disabled controls only for an authorized action blocked by a visible non-security condition;
- filter counts, search and exports through the same policy.

For a user who may view the record but not the task, return forbidden from the task endpoint and route the application to the neutral detail with a concise access message. For an out-of-scope record, do not reveal its existence.

Add Playwright tests using direct navigation as well as ordinary row actions.
```

**Gate 02:** A user cannot discover or render an unauthorized task surface but retains the correct neutral record view.

# Cursor Prompt 03 — Budget and Demand rollout

```text
Apply the shared authorization-surface pattern to Budget & Funding and Demands first.

Budget acceptance example:
- Requester can View/Track an owned in-scope Budget record;
- Requester does not receive a Review action;
- Requester cannot load the Budget review or approval task forms by direct URL;
- assigned Budget Officer receives Review only at the applicable current step;
- configured Budget Approver receives Approve only at the applicable current step;
- Manager/Auditor and explicit Support Viewer receive neutral read-only projections only;
- users outside PE/OU scope cannot list or view the record.

Apply the equivalent capability matrix to Demand enrichment, Budget sign-off, departmental approval and Procurement review tasks.

Remove duplicated page-level role checks replaced by the shared policy. Preserve business workflow rules and existing valid records.

Add role/state/scope Playwright matrices and negative API tests.
```

**Gate 03:** Budget and Demand matrices pass for discovery, direct routes, projections and mutations.

# Cursor Prompt 04 — Remaining module rollout

```text
Apply the approved shared pattern to Strategy, Procurement Planning, Tender preparation, evaluation, award and every remaining workflow-enabled module identified at Gate 00.

For each module:
- define module-qualified capabilities;
- distinguish neutral detail from task surfaces;
- filter lists, counts, exports and notifications;
- enforce current assignment/authority and state;
- preserve PE/OU scoping and separation of duties;
- remove unauthorized disabled actions; and
- add direct-route and mutation-denial tests.

Do not invent new workflow steps or change approved business semantics merely to apply the authorization layer.
```

**Gate 04:** Every audited workflow surface is migrated to the shared policy with automated evidence.

# Cursor Prompt 05 — Final authorization verification

```text
Run the complete cross-module authorization verification.

Produce a matrix whose rows are role + PE/OU scope + record relationship + workflow state and whose columns are:
- list visibility;
- neutral view;
- edit/continue;
- submit;
- review;
- return;
- approve;
- export/report; and
- direct task-route result.

Test at minimum:
1. normal navigation;
2. direct task URLs;
3. guessed record identifiers;
4. manipulated action payloads;
5. out-of-scope PE and OU access;
6. wrong workflow state;
7. wrong or completed assignment;
8. separation-of-duties conflicts;
9. stale browser tabs and cached actions;
10. notifications and deep links;
11. list/count/export leakage; and
12. Administrator without an operational role.

Run unit, transaction, API and Playwright suites. Report each audited route, its guard, test and result. Do not mark a surface complete because its button is disabled or hidden on one page.
```

**Gate 05:** No unauthorized workflow surface, data projection or mutation remains reachable.

## 12. Acceptance criteria

| ID | Acceptance criterion |
|---|---|
| AUTH-AC-001 | Unauthorized workflow actions are absent rather than disabled. |
| AUTH-AC-002 | A user with neutral record-view permission but no task capability cannot render the task form through navigation or direct URL. |
| AUTH-AC-003 | Every task loader and mutation validates capability, PE/OU scope, workflow state and current assignment server-side. |
| AUTH-AC-004 | Lists, queues, counts, search, exports and reports use the same authorization policy. |
| AUTH-AC-005 | Requesters see View/Track rather than Review for submitted Budget records. |
| AUTH-AC-006 | Assigned Budget Officers see Review only while the applicable task is current. |
| AUTH-AC-007 | Configured approvers see Approve only at their current step and cannot bypass separation of duties. |
| AUTH-AC-008 | Managers, auditors and support viewers use explicit read-only projections without acquiring operational authority. |
| AUTH-AC-009 | Out-of-scope users cannot discover the record through lists, counts, direct identifiers or exports. |
| AUTH-AC-010 | Task projections do not return protected fields to neutral viewers. |
| AUTH-AC-011 | Permission changes, completed assignments and stale pages are re-evaluated on every request. |
| AUTH-AC-012 | The cross-module role/state/scope matrix has automated unit, API and Playwright evidence. |

## 13. Definition of done

The gap is closed only when:

- unauthorized users cannot discover task actions;
- unauthorized task forms never receive their protected projection;
- neutral business-record visibility remains available where legitimate;
- list, route, API, export and notification behaviour agree;
- role, scope, relationship, assignment, state and separation of duties are evaluated centrally;
- the Requester/Budget review example passes through ordinary navigation and direct URL tests; and
- all migrated modules have negative authorization evidence, not merely successful-role smoke tests.

