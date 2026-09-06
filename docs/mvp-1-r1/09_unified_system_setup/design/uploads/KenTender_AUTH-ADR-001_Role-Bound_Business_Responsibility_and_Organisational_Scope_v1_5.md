# AUTH-ADR-001 — Role-Bound Business Responsibility and Organisational Scope

| Control | Value |
|---|---|
| Document ID | AUTH-ADR-001 |
| Version | 1.5 |
| Date | 2 September 2026 |
| Status | Proposed for approval |
| Change type | Complete consolidated successor to v1.4 |
| Applies to | Every KenTender module, list, count, detail, task, file, export, report, screen and business command |
| Implementation owner | `kentender_core` for the role registry, assignment, resolver and Users-and-responsibilities surface; Configuration & Governance for the site PE, Organisation Unit and Fiscal Year records; each domain app for record-state and business rules |

**Controlling decision:** One KenTender site represents exactly one Procuring Entity. Within that site, one role-bound record — **User Responsibility Assignment** — binds a user to a business responsibility, an organisational scope and an effective period. It is the sole source of KenTender business authority. Authorization is enforced through native Frappe permission hooks, not through a parallel permission framework.

---

## 1. Governing decision

The authoritative formula is:

> **Effective business authority = one Active User Responsibility Assignment matching the required business role and the record's Organisation Unit scope + eligible record, Fiscal Year, module flag and task state + segregation and domain-rule checks.**

None of the following is an authority source, alone or in combination: a Frappe Role, a Frappe User Permission, `User Scope Assignment`, `Capability Profile`, `Operational Scope Assignment`, `kt_primary_department`, an HRMS Department, an ERPNext Cost Center, a browser or session context, a work task, a notification, a menu entry, a route, or a Fiscal Year grant to a user.

There is no fallback chain. Where no Active assignment matches, the result is a stable denial and an administrator diagnostic.

### 1.1 Conflict and disposition register

| Earlier item | Disposition in v1.5 |
|---|---|
| Multiple Procuring Entities in one site | Remove. One site is exactly one PE, configured once and never selected. |
| `procuring_entity` field on Organisation Unit | Remove. Every OU is inherently part of the site PE; cross-PE parenting is impossible because no second PE exists. |
| `procuring_entity` field on User Responsibility Assignment | Remove. Scope is either site-wide or one Organisation Unit subtree. |
| `Global` scope type | Remove. It meant "across Procuring Entities" and has no meaning in a single-PE site. Replaced by **Site-wide**. |
| `Procuring Entity` scope type | Rename to **Site-wide**. The two were already the same set of records. |
| PE selector in the page header, register, dialogs and create screens | Remove. There is no PE choice to make. |
| `permitted_pe_scopes()` resolver operation | Remove. |
| `PE Fiscal Year Context` DocType | Remove. |
| Per-user Financial Year grant or `allowed_years` gate | Remove. Fiscal Year is record and configuration data, never a user permission dimension. |
| KenTender-owned `Financial Year` DocType | Replace with the canonical ERPNext `Fiscal Year`. |
| Resolver as a bespoke API that domain apps must remember to call | Replace. The resolver is registered as Frappe `permission_query_conditions` and `has_permission` hooks so scoping applies by default. A single explicit helper covers business commands. |
| Custom Vue Organisation Unit tree with search, expand/collapse and nested-set repair controls | Replace with the Frappe-supplied tree control inside the System setup section. Claude Design draws the section shell and detail panel only. |
| Blanket removal of Frappe User Permission rows at cutover | Correct. Cleanup is scoped to KenTender link doctypes only. ERPNext and HRMS User Permissions are load-bearing and are never touched. |
| `Procurement Department` as a scope hierarchy | Remove. Map each record to one exact Organisation Unit before cutover. |
| `kt_primary_department` | Remove. If retained for display, label it a default view and never read it in an authorization path. |
| Separate `/app/organisation-structure` and `/app/user-responsibilities` routes | Remove. Both are sections of `/app/system-setup` under CFG-CHG-002 v0.5. No alias or redirect is maintained after cutover. |
| Assignment approval, submission or review workflow | Remove. Setup writes take effect on save and are audited. |
| `Delegate`, `Acting Approver`, `Applicable final authority` or `Workflow approver` roles | Remove. An acting officer holds the same business role through one dated Acting assignment. |
| Bespoke access-diagnostics screen separate from the assignment record | Remove. Diagnostics are a collapsed section of the responsibility detail. |
| Role projection cleaned only on explicit revocation | Correct. Add scheduled reconciliation so time-expired assignments do not leave orphan Frappe Roles. |
| Reports and raw SQL implicitly assumed to be scoped | Correct. Query and Script Reports bypass permission query conditions; they must apply the shared match conditions or are prohibited over scoped data. |

---

## 2. Scope and non-goals

### 2.1 In scope

Binding a user to a business responsibility and organisational scope; resolving that binding consistently across every read and command surface; administering it through one setup surface; and migrating existing authority data to it.

### 2.2 Non-goals

This ADR governs authorization within a single KenTender site, which represents exactly one Procuring Entity. The following are explicitly out of scope and require separately named designs before any implementation work:

- **Cross-PE supplier identity.** A supplier bidding to more than one Procuring Entity holds a separate account per site. Federated supplier registration, single sign-on across PEs and consolidated bid history are not addressed here.
- **National reporting.** Aggregation of procurement data across Procuring Entities has no home in this model. Any national or sectoral reporting requires a separate data plane.
- **PPRA and other regulator oversight.** Cross-PE regulatory inspection, monitoring and intervention are not expressible as a responsibility assignment under this ADR. The `Global` scope type is removed precisely because it has no meaning within a single-PE site.

No part of this ADR shall be extended, reinterpreted or partially implemented to simulate any of the above. Multi-tenancy is a distinct architectural problem and shall be designed as one. In particular, no `procuring_entity` field, PE selector or PE-keyed permission shall be reintroduced "for future reporting".

### 2.3 Carried corrections owned by other documents

| Item | Owning document |
|---|---|
| Optional scheduled close instant on the Needs-submission flag, so an announced deadline closes without a manual action | CFG-CHG-002 v0.5 |
| Whether closing Needs submission freezes existing Drafts or only blocks creation and submission | NDS-CHG-001 |

Both are recorded here because they were raised during this review. Neither is decided by this ADR.

---

## 3. Ownership and dependency boundary

| Object or decision | Owner | This ADR's relationship |
|---|---|---|
| Site Procuring Entity identity | Configuration & Governance | Read only. Never selected, never a permission dimension. |
| Organisation Unit tree | Configuration & Governance | Sole valid business scope tree. This ADR defines the scope semantics; CFG owns the records. |
| ERPNext Fiscal Year | ERPNext, surfaced by Configuration & Governance | Read only. Never a user grant. |
| Needs-submission and other module flags | Configuration & Governance | Read only through the owning module. |
| Business-role registry | `kentender_core` | Defined here. Code-owned and reviewed. |
| User Responsibility Assignment | `kentender_core` | Defined here. |
| Scope resolution and permission hooks | `kentender_core` | Defined here. |
| Business roles, record states, tasks, approvals, domain invariants | Each module document | Unchanged. This ADR adds no approval stage. |
| ERPNext Company, Cost Center, HRMS Department, HRMS approver chains | ERPNext / HRMS | Never read in a KenTender authorization path. |

Module documents state their approved business roles, each role's scope classification, actions, states, task and segregation rules. They reference this ADR for assignment, hierarchy, resolution and administrator inspection, and shall not redefine those mechanisms.

---

## 4. Canonical domain model

All identifiers are server-generated. Framework audit fields remain framework-managed and are not repeated as user data.

### 4.1 Site Procuring Entity

Implemented as a **Frappe Single DocType**, so singularity is structural rather than enforced by a validation hook that a fixture or direct insert can bypass.

| Field | Rule |
|---|---|
| `pe_name` | Required legal name of the Procuring Entity. |
| `pe_code` | Required stable code, for example `PE-MOH`. |
| `ppra_registration` | Optional regulator reference. |
| `timezone` | Required. `Africa/Nairobi` by default. |

Because a Single cannot be the target of a `Link`, legal provenance on immutable evidence records is a **snapshot**, not a foreign key: a tender notice, award letter, contract or export stamps the PE name and code as they stood when the document was issued. A later rename of the entity does not rewrite historical evidence.

No transactional or configuration record carries a live `procuring_entity` link. Denormalising the PE onto ordinary records would create a second source of truth for the permission engine, which is the exact defect this ADR exists to remove.

### 4.2 Organisation Unit

`Organisation Unit` is the only organisational hierarchy used for KenTender business scope. It is a Frappe nested-set tree DocType.

| Field | Rule |
|---|---|
| `unit_name` | Required. 2–160 characters. Unique among active siblings after normalised comparison. |
| `unit_code` | Server-generated on insert. Stable. Never user-entered or edited. |
| `parent_organisation_unit` | Parent field. Blank only for the single site root. |
| `is_group` | Framework-managed. |
| `lft` / `rgt` | Framework-maintained. Never exposed in the UI. |
| `status` | `Active` or `Inactive`. |
| `hrms_department` | Optional display-only link. Never read in an authorization path. |

Rules:

- `is_tree = 1`; the framework maintains `lft` and `rgt`.
- Exactly one root Organisation Unit exists, created idempotently during initial site setup and named for the site PE. Administrators add units beneath it and never create or select the root.
- There is no `procuring_entity` field. Every unit belongs to the site PE by construction.
- `Organisation Unit Type` is not required for authorization or unit creation and shall not block the structure.
- Reparent and physical delete are not available. Deactivation preserves referenced history.

### 4.3 Descendant rule

An OU-scoped assignment covers the selected Organisation Unit and all of its descendants. There is no `include descendants` switch.

To authorise one department only, assign its leaf node. To authorise a directorate and its branches, assign the directorate node once.

Hierarchy expands **where the assigned role applies**. It never creates another role. A Head of User Department assignment does not make the holder a Departmental Author, Planner or Accounting Officer.

### 4.4 Business-role registry

One reviewed, code-owned registry. Administrators assign registered responsibilities; they do not define roles, scope types or capability strings in production.

| Property | Meaning |
|---|---|
| `business_role` | Stable exact role code and display label. |
| `scope_type` | `Site-wide` or `Organisation Unit`. No other value exists. |
| `frappe_roles` | Minimal framework Role projection needed for Desk and DocType access. |
| `exclusive_office` | Whether only one Active assignment may occupy this office for the same scope. |
| `allowed_assignment_admin` | Administrative responsibility permitted to grant and revoke it. |
| `sod_tags` | Stable categories consumed by domain segregation checks. Never free-form capabilities. |

The registry does not enumerate commands. Each module names the business role its commands require.

| Scope type | Illustrative responsibilities |
|---|---|
| Site-wide | Strategy Author and Approver, Budget roles, Procurement Planner, Head of Procurement Function, Accounting Officer, Auditor, Tender roles whose approved work spans the entity. |
| Organisation Unit | Departmental Author, Head of User Department, Requisition Preparer, and Auditor where an approved oversight scope is narrower than the site. |

Administrator and System Manager are technical roles under section 8. They are not business responsibilities and do not appear in the registry.

### 4.5 User Responsibility Assignment

| Field | Rule |
|---|---|
| `user` | Required Link to an enabled System User. |
| `business_role` | Required governed code from the registry. |
| `organisation_unit` | Required for `Organisation Unit` roles. Prohibited for `Site-wide` roles. |
| `effective_from` | Optional UTC instant. Blank means effective immediately once Enabled. |
| `effective_to` | Optional UTC instant later than `effective_from`. Blank means no scheduled end. |
| `appointment_type` | `Permanent` or `Acting`. Required. Changes evidence, not capability. |
| `authority_reference` | Required for Acting. Optional for Permanent per administrative policy. 2–160 characters. |
| `status` | Stored `Enabled` or `Revoked`. |
| `assigned_by` / `assigned_at` | Server-set. |
| `revoked_by` / `revoked_at` / `revocation_reason` | Server-set on revocation. Reason required, 10–500 characters. |

No Procuring Entity, Fiscal Year, module, capability string, task, browser preference or arbitrary JSON policy belongs on the assignment.

### 4.6 Derived status

The server derives the display status from stored `status` and the effective period at read time. Only **Active** authorises.

| Derived status | Condition |
|---|---|
| Scheduled | `status = Enabled` and `effective_from` is in the future. |
| Active | `status = Enabled` and now is within the effective period. |
| Expired | `status = Enabled` and `effective_to` has passed. |
| Revoked | `status = Revoked`. |

Expiry is evaluated at command time. A scheduled job may refresh display status and reconcile role projections, but is never the security control.

### 4.7 Uniqueness and overlap

The same user shall not hold overlapping Enabled assignments for the same `business_role + organisation_unit` tuple. An idempotent request for the same assignment returns the existing record.

Different roles may be held in different scopes. Each command resolves only the assignment for the role it requires; other roles held by the same user never broaden it.

Where the registry marks a role `exclusive_office`, the server rejects a second overlapping Active assignment for the same scope and returns the exact conflicting assignment. The UI never invents a precedence rule.

---

## 5. Authorization model

### 5.1 What Frappe already provides

The following are native and shall be used as-is rather than reimplemented:

| Concern | Frappe primitive |
|---|---|
| Coarse DocType access by role | DocPerm / Role Permission Manager |
| Row-level list, count and report filtering | `permission_query_conditions` hook |
| Per-document access check | `has_permission` hook |
| Hierarchy storage and descendant queries | `NestedSet`, `get_descendants_of` |
| Tree UI control | Frappe tree control |
| Field-level restriction | permlevel |
| Role bundles | Role Profile |
| Document versioning and change history | Version |

### 5.2 What KenTender adds, and why

Frappe's `User Permission` carries `user`, `allow`, `for_value`, `applicable_for`, `apply_to_all_doctypes`, `is_default` and `hide_descendants`. It has **no role field and no effective dates**. `applicable_for` narrows a permission to a DocType, not to a role, so User Permissions apply uniformly across every role a user holds.

Consequently a user who is Departmental Author in one unit and Head of User Department in another is, natively, both in both. That is the defect this ADR exists to correct, and no configuration of stock Frappe expresses it.

KenTender therefore adds exactly three things and nothing more:

1. `User Responsibility Assignment` — one DocType supplying the missing role-to-scope binding and effective dating.
2. One shared scope predicate, registered as Frappe hooks.
3. One explicit command-level helper, because Frappe cannot know which business role a given command requires.

Nothing else in this ADR is a new mechanism.

### 5.3 One predicate, registered as hooks

The predicate is registered for every scoped DocType through **both** hooks:

- `permission_query_conditions` — scopes list views, counts, link searches, report views, dashboards and `frappe.get_list`.
- `has_permission` — scopes direct document access.

Both are required. Permission query conditions only hide documents from lists; a user who follows a direct link or knows a document name can still open a record that is filtered out of the list. Registering only the query hook leaves a direct-route hole.

Because scoping is registered rather than called, ordinary `frappe.get_list` and `frappe.has_permission` return the correct result by default. Domain apps do not need to remember to call a bespoke API, and forgetting is not possible.

Registration is **declarative**. Each app declares which field carries the Organisation Unit on which DocTypes; one generic hook implementation reads that map. Adding a scoped DocType is a configuration line, not new SQL.

```
kentender_scope_map = {
    "Departmental Need": {"ou_field": "organisation_unit"},
    "Plan Item":         {"ou_field": "organisation_unit"},
}
```

### 5.4 Reports, exports and raw SQL

Query Reports and Script Reports execute raw SQL and bypass `permission_query_conditions` entirely. Pages and Reports carry their own role list, which is role-based only and therefore blind to Organisation Unit scope.

Any report, export or raw query over scoped data shall obtain its predicate from `frappe.desk.reportview.build_match_conditions` for each scoped DocType it touches, or it shall not be built. A report that cannot apply the shared conditions is prohibited, not exempt.

Counts shall not disclose records that rows cannot show. Files and attachments shall not remain reachable after the parent record is denied.

### 5.5 Business commands

A protected command calls one helper before it mutates:

```
require_responsibility(doc, "Head of User Department")
```

The helper resolves the Active assignment for that exact role, matches the document's Organisation Unit against the assignment's subtree, and raises the applicable error in section 10 on failure.

The client never supplies an assignment ID, effective role, permitted scope or available action as authority. If such values are sent as display data, the server ignores them and resolves again.

### 5.6 Resolution algorithm

For a protected command the server shall:

1. authenticate an enabled System User;
2. load the registered required business role;
3. find Active assignments for that user and role at the server clock instant;
4. match the record's Organisation Unit against the assigned subtree, or accept any record for a Site-wide role;
5. require the coarse Frappe DocType operation expected for the command;
6. check the record's Fiscal Year, module flag and record state;
7. check the open task where the workflow uses one;
8. apply maker-checker and other segregation rules;
9. check optimistic concurrency and domain invariants; and
10. write the decision and assignment snapshot atomically.

### 5.7 Frappe Role projection

The assignment service adds the minimal Frappe Role projection required by each Active assignment. Revocation removes a projected Role only when no other Active assignment still requires it.

Because assignments expire by time rather than by an explicit action, a scheduled reconciliation removes projections left by expired assignments. A lingering Role grants no business authority on its own — coarse DocType access without a scope match resolves to denial — but an unreconciled projection produces false orphan findings in diagnostics.

Direct manual addition of a Frappe Role creates no business authority and is reported as an orphan projection. Direct manual removal is repaired or reported by the same reconciliation; it never silently invalidates an otherwise Active assignment.

### 5.8 Segregation of duties

Users may hold multiple assignments. Holding two roles is not a violation; performing incompatible decisions in the same evidence chain is. Segregation is evaluated against actual actions using the registry's `sod_tags` and the owning module's rules.

This ADR adds no business approval stage. Where a module's approved requirements name the Accounting Officer as final authority, no further approval is inferred. Generic labels such as `approving authority` or `workflow approver` are prohibited unless an approved source defines that distinct legal capacity.

---

## 6. Fiscal Year and operating context

The canonical year structure is the **ERPNext `Fiscal Year`**. KenTender defines no parallel year DocType.

Fiscal Year is record and configuration data. It is never an assignment dimension and never a user grant. The permitted operation is determined by the record's own Fiscal Year, the owning module's open/closed flag, the record's state and the actor's Active assignment.

One assignment therefore works across every Fiscal Year the owning module makes eligible. Annual user reprovisioning is prohibited.

A Fiscal Year, department or status control in a module screen is a visible, changeable local filter. It does not grant access, is not required before opening a direct record or task, may be changed whenever more than one authorised option exists, is ignored when stale or invalid, and shall never trap a user in a future or closed period. A last-used filter may be remembered for convenience if it always has a visible reset, but it is never authority.

Create screens show only targets derived from Active assignments combined with the owning module's eligible flags or records. Browsing may include historical authorised records even when creation is closed.

---

## 7. Coexistence with ERPNext and HRMS

The site also runs ERPNext for accounting and HRMS for payroll. Four trees will exist in one database. Their boundaries are fixed as follows.

| Structure | Role | Rule |
|---|---|---|
| ERPNext `Company` | Legal and accounting entity | One Company, corresponding to the site PE. Never a KenTender scope dimension. |
| KenTender `Organisation Unit` | Business scope | The only tree read by KenTender authorization. |
| HRMS `Department` | HR administration | Independent. An OU may carry an optional display link to it. Never read in a KenTender authorization path. |
| ERPNext `Cost Center` | Financial dimension | Not a KenTender authorization scope in this release. Any Budget requirement to scope by Cost Center is a domain eligibility check inside the Budget module, resolved after the role check, never instead of it. |

HRMS approver chains — Leave Approver, Expense Approver and equivalents — are HR workflow constructs. They confer no KenTender business authority and shall not be read, mirrored or treated as a delegation mechanism.

**Frappe User Permission remains live and load-bearing** for ERPNext and HRMS on Company, Cost Center, Employee and Department. KenTender does not consult it for business authority, and the migration in section 11 never deletes rows outside KenTender's own link doctypes.

---

## 8. Administrator and System Manager

Administrator and System Manager hold technical read access to all KenTender records, tasks, decisions, files, configuration and audit evidence across every Organisation Unit and Fiscal Year, without any business assignment. Interfaces provide a changeable filter or direct search so a technical user is never stranded on an empty page.

They are authorised to create and maintain the site PE, Fiscal Year flags, Organisation Units and User Responsibility Assignments through **System setup**. These writes take effect on save. They require no submission, review, recommendation or approval state, and are validated and audited.

Setup authority is not business authority. To create, certify, approve, reject, submit or otherwise exercise a module responsibility, the person must hold the same Active assignment and pass the same state and segregation checks as any other user.

Seeds, fixtures and test profiles shall not grant business roles to Administrator to make a journey pass.

---

## 9. Service and command contracts

### 9.1 Resolver — `kentender_core.authorization`

| Operation | Result |
|---|---|
| `resolve_assignments(user, business_role, at)` | Active assignments for one required role at one instant. |
| `permitted_ou_scopes(user, business_role, at)` | Assigned Organisation Units and their derived descendants. |
| `scope_condition(doctype, user, business_role=None)` | SQL predicate used by both permission hooks and by report match conditions. |
| `authorise_record(user, business_role, doc, at)` | Allow or deny with the exact matching assignment ID. |
| `require_responsibility(doc, business_role)` | Raises the applicable section 10 error, or returns the assignment snapshot. |
| `diagnose_user(user, at)` | Assignments, projections, conflicts and orphans for administration. |

Exact Python names may follow repository conventions, but there shall be one semantic implementation and one predicate.

### 9.2 Administration commands

| Command | Required behaviour |
|---|---|
| `GetOrganisationStructure()` | Authorised tree projection, selected-node detail, assignment-impact counts and allowed actions. |
| `AddOrganisationUnit(parent_id, name, idempotency_key)` | Revalidate administrator, root existence, parent and sibling uniqueness; generate code and insert atomically. |
| `RenameOrganisationUnit(unit_id, name, expected_version)` | Change display name only. Code is immutable. |
| `SetOrganisationUnitActive(unit_id, active, expected_version)` | Recheck children, Active assignments and domain blockers. Never delete. |
| `ListUserResponsibilities(filters, paging)` | Rows and counts from one server predicate. Filters are non-authoritative. |
| `PreviewResponsibilityAssignment(user, role, ou, appointment, dates)` | Return required fields, exact scope and descendant count, overlap and exclusivity findings and the human summary. Create nothing. |
| `AssignResponsibility(...)` | Recompute the preview, validate, create the Enabled assignment, synchronise the Role projection and write audit — atomically and idempotently. |
| `GetResponsibilityAssignment(id)` | Full authorised detail, audit and diagnostics. |
| `RevokeResponsibility(id, reason, expected_version, idempotency_key)` | Recheck, revoke and reconcile the Role projection atomically. |

Every mutation is authorised and validated server-side. Options, summaries, descendant counts and available actions come from the server. Client controls are never authority.

---

## 10. Error contract

| Code | User-visible result |
|---|---|
| `AUTH_RESPONSIBILITY_REQUIRED` | You are not assigned the responsibility required for this action. |
| `AUTH_SCOPE_REQUIRED` | This record is outside the organisational scope of that responsibility. |
| `AUTH_ASSIGNMENT_INACTIVE` | Your responsibility assignment is not effective at this time. |
| `AUTH_TASK_REQUIRED` | This action is not currently assigned for decision. |
| `AUTH_SEGREGATION_BLOCKED` | You cannot perform this action because you completed an incompatible earlier step. |
| `AUTH_STATE_CHANGED` | This action is no longer available in the record's current state. |
| `AUTH_PERIOD_UNAVAILABLE` | This operation is not available for the record's Fiscal Year or current module state. |
| `AUTH_EXCLUSIVE_OFFICE_CONFLICT` | Another person already holds this responsibility for that scope during the selected period. |
| `AUTH_CONFIGURATION_INVALID` | The responsibility or organisational scope is not configured consistently. |

Cross-scope reads return Not found where existence itself is protected. Ordinary user messages shall not name internal tables, hooks or permission algorithms.

---

## 11. Controlled migration

One atomic cutover programme. No long-lived compatibility mode.

### 11.1 Inventory

Produce a read-only reconciliation of: Frappe KenTender Roles by user; Frappe User Permissions for Procuring Entity, Organisation Unit and Financial Year; every `User Scope Assignment`; every `Capability Profile` and `Operational Scope Assignment`; `kt_primary_department` values; Organisation Unit and Procurement Department hierarchies; active acting or delegation records; every code path that authorises from those stores; and the proposed User Responsibility Assignments with their source evidence.

### 11.2 Deterministic mapping

- Convert a row only when user, business role, Organisation Unit and effective period are unambiguous.
- Merge duplicate source rows into one assignment and retain all source references in the migration audit.
- Do not infer a role from access scope alone, or scope from a role alone.
- Do not create a Fiscal Year assignment.
- Do not broaden a leaf Organisation Unit to its parent to reduce row count.
- Map `Procurement Department` to one exact Organisation Unit or block that record.
- Mark every conflict and ambiguity for explicit administrator resolution. Migration creates no authority automatically for an ambiguous case.

### 11.3 Cutover order

1. Approve the role registry and Organisation Unit rules.
2. Confirm the site holds exactly one Procuring Entity. **If more than one PE is configured, stop.** Separating an existing multi-PE site is a data-partitioning exercise outside this plan and must be completed and evidenced before step 3.
3. Add the `User Responsibility Assignment` schema and administration service.
4. Add the shared predicate and register both hooks, with no production caller switched yet.
5. Build the two System setup sections, diagnostics and their exact empty and error states.
6. Run reconciliation and resolve every ambiguous case.
7. Create assignments idempotently and synchronise Role projections.
8. Switch list, count, detail, task, file, report and command authorization in one controlled release.
9. Stop all seeds and administration paths from creating old authority rows.
10. Run the cross-module authorization and user-journey gate.
11. Remove obsolete authorization reads, then clean obsolete rows idempotently.

### 11.4 Scoped cleanup

Step 11 removes User Permission rows **only** where `allow` is a KenTender-owned link doctype. Rows for `Company`, `Cost Center`, `Employee`, `Department` or any other ERPNext or HRMS doctype are load-bearing and are never touched. The cleanup script shall enumerate its permitted `allow` values explicitly rather than filter by exclusion.

Data cleanup never precedes code cutover and verification. Immutable migration evidence and historical business decisions are retained.

### 11.5 No fallback mode

After step 8, no production code may fall back to Frappe User Permission, `User Scope Assignment`, `Capability Profile`, `Operational Scope Assignment`, `kt_primary_department` or browser context when no assignment matches. The correct result is a stable denial plus an administrator diagnostic.

---

## 12. UI architecture, menu and routes

Authorization administration is two sections of the single Configuration & Governance **System setup** page defined by CFG-CHG-002 v0.5.

| Surface | Route | Purpose |
|---|---|---|
| System setup — Organisation structure | `/app/system-setup#organisation-structure` | Maintain the site's Organisation Unit tree. |
| System setup — Users and responsibilities | `/app/system-setup#users-and-responsibilities` | Grant, inspect and revoke role-bound responsibilities. |

This is a configuration page, not a work queue, and the only setup entry under Configuration & Governance. Raw `/app/organisation-unit`, `/app/user-responsibility-assignment`, `/app/user-permission` and legacy scope-assignment pages are not normal operating journeys. Legacy `/app/organisation-structure` and `/app/user-responsibilities` are removed without an alias.

Administrator and System Manager use this surface without any business assignment. No setup submission, approval level or assignment-approval task exists.

Frappe supplies the Desk header, breadcrumb, session controls, route lifecycle, dialogs, toasts, the tree control and accessibility primitives. KenTender supplies the approved tokens and shared Vue components. This document authorises no second application shell, custom header, breadcrumb or global context selector.

---

## 13. Static Claude Design contract

This section is the complete input to Claude Design. It defines static visual compositions only. Runtime behaviour belongs to section 14 and shall not be pasted into a design prompt.

### 13.1 Closed-input rules

- Produce desktop artboards at **1440 × 1024 px**. Dialogs are **520 px** wide over a dimmed parent artboard.
- Reuse the approved KenTender visual system, spacing, type scale, tokens, cards, badges, tables, fields, buttons, tabs, empty states and dialogs.
- The artboard starts below the Frappe Desk header. Do not draw Frappe navigation, the Desk header, breadcrumb, user menu, notifications, Help or global search.
- Breadcrumb text is fixture data outside the artboard, supplied to confirm location only.
- Use only the visible labels, values, badges, controls, sections and states stated for that artboard.
- Do not invent data. If a value or state is not stated, omit it.
- Do not encode behaviour, validation, permissions, APIs, routing, transitions, concurrency or implementation instructions in the visual output.
- Do not add summary cards, charts, percentages, trend arrows, illustrations, side panels, steppers, timelines, helper panels, action menus, metadata or table columns unless explicitly stated.
- **Do not show a Procuring Entity selector, PE switcher, PE column, Financial Year control, module control, capability control, User Permission control, arbitrary scope field, approver field, task field or generic notes field anywhere in this section.**
- Do not show `lft`, `rgt`, `old_parent`, raw parent identifiers or nested-set repair controls.
- Generated identifiers may be displayed on saved records but never as editable fields.

The approved desktop shell inside every full-page artboard is:

- full-width warm-white page background;
- a 1200 px maximum-width content column centred in the available page area;
- 32 px top and bottom page padding;
- page header followed by 24 px vertical spacing;
- 16 px gaps between cards or table sections; and
- no custom sidebar.

The Organisation Unit tree in AUTH-DES-01 is rendered at runtime by the Frappe tree control. Claude Design draws it as a static indented list using the approved list styling, to establish spacing and the surrounding composition only. It shall not design expand/collapse affordances, drag handles or tree toolbars.

### 13.2 AUTH-DES-01 — Organisation structure section

**Fixture context — outside the artboard:** Administrator · `administrator@moh.example.test` · Ministry of Health · 1 Sep 2026, 10:00 EAT · Frappe header breadcrumb: **Home > Configuration and Governance > System setup**.

**Section header**

- Eyebrow: **SYSTEM SETUP**
- Title: **Organisation structure**
- Description: **Maintain the departments and organisational units used to scope KenTender responsibilities.**
- No header action button

**Two-column workspace**

Left column, 40% width. Static indented list:

| Level | Unit | Code | Status |
|---|---|---|---|
| 1 | Ministry of Health | PE-MOH | Active |
| 2 | Directorate of Digital Health and Policy | OU-MOH-DHP | Active |
| 3 | Digital Health | OU-MOH-DHI | Active |
| 2 | Human Resources Management and Development | OU-MOH-HRMD | Active |

The row for **Directorate of Digital Health and Policy** is shown selected.

Right column, 60% width. Selected-unit detail card:

| Label | Value |
|---|---|
| Unit name | Directorate of Digital Health and Policy |
| Code | OU-MOH-DHP |
| Path | Ministry of Health › Directorate of Digital Health and Policy |
| Status | Active |
| Included units | 1 descendant |

Below the detail card:

- Primary button: **Add organisation unit**
- Secondary button: **Edit name**
- Secondary button: **Deactivate**
- Text link: **View 2 affected responsibilities**

Do not show a reparent control, delete control, Organisation Unit Type, manager, email, attachment or free-text scope field.

### 13.3 AUTH-DES-02 — Add organisation unit dialog

520 px modal over a dimmed AUTH-DES-01.

- Title: **Add organisation unit**

| Field label | Displayed value | Component |
|---|---|---|
| Parent organisation unit | Ministry of Health › Directorate of Digital Health and Policy | Read-only field |
| Organisation unit name | Health Information Systems | Single-line input |

Help text beneath the name input: **The unit code is generated when you save.**

- Footer buttons: **Cancel** and primary **Add organisation unit**

Do not show a Procuring Entity row, code input, Organisation Unit Type, Financial Year, role, manager or permission field.

### 13.4 AUTH-DES-03 — Users and responsibilities register

**Fixture context — outside the artboard:** Administrator · `administrator@moh.example.test` · Ministry of Health · 1 Sep 2026, 10:10 EAT · Frappe header breadcrumb: **Home > Configuration and Governance > System setup**.

**Section header**

- Eyebrow: **SYSTEM SETUP**
- Title: **Users and responsibilities**
- Description: **Assign each user a business responsibility in its exact organisational scope.**
- Right-aligned primary button: **Assign responsibility**

**Filter row**

- Search input with placeholder: **Search user or responsibility**
- Organisation Unit select showing: **All organisation units**
- Responsibility select showing: **All responsibilities**
- Status select showing: **All statuses**
- Secondary button: **Clear filters**

**Register table**

| User | Responsibility | Scope | Coverage | Appointment | Effective period | Status | Action |
|---|---|---|---|---|---|---|---|
| Grace Wanjiku · grace.wanjiku@moh.example.test | Departmental Author | Digital Health | This unit only | Permanent | From now · No scheduled end | Active | View |
| Dr Peter Kimani · peter.kimani@moh.example.test | Head of User Department | Human Resources Management and Development | This unit only | Permanent | From now · No scheduled end | Active | View |
| Julia Njeri · julia.njeri@moh.example.test | Head of User Department | Digital Health | This unit only | Acting | 1 Oct 2026 – 30 Nov 2026 | Scheduled | View |
| Mercy Kilonzo · mercy.kilonzo@moh.example.test | Procurement Planner | Site-wide | Entire entity | Permanent | From now · No scheduled end | Active | View |
| Samuel Otieno · samuel.otieno@moh.example.test | Head of User Department | Directorate of Digital Health and Policy | This unit and 1 descendant | Permanent | From 1 Jan 2026 · Until 31 Aug 2026 | Expired | View |

Below the table: **5 responsibilities** on the left. No pagination control.

Status badges use the approved state hues: Active, Scheduled, Expired, Revoked. Do not add a Procuring Entity column, Financial Year column, assignee avatar, summary card or action menu.

### 13.5 AUTH-DES-04 — Assign responsibility, Organisation Unit scope

520 px modal over a dimmed AUTH-DES-03.

- Title: **Assign responsibility**

| Order | Field label | Displayed value | Component |
|---|---|---|---|
| 1 | User | Grace Wanjiku · grace.wanjiku@moh.example.test | Link search |
| 2 | Responsibility | Departmental Author · Organisation Unit | Select |
| 3 | Organisation Unit | Ministry of Health › Directorate of Digital Health and Policy › Digital Health | Tree select |
| 4 | Appointment | Permanent | Segmented control with **Permanent** and **Acting** |
| 5 | Effective from | Leave blank to start immediately | Optional date and time input, empty |

**Responsibility summary** — read-only panel below the fields:

> Grace Wanjiku will be Departmental Author for Digital Health from now with no scheduled end.

- Footer buttons: **Cancel** and primary **Assign responsibility**

Do not show Effective to, Authority reference, a Procuring Entity field, Financial Year, module, capability, User Permission, profile, task, approver or notes control.

### 13.6 AUTH-DES-05 — Assign responsibility, Acting variant with descendants

520 px modal over a dimmed AUTH-DES-03.

- Title: **Assign responsibility**

| Order | Field label | Displayed value | Component |
|---|---|---|---|
| 1 | User | Julia Njeri · julia.njeri@moh.example.test | Link search |
| 2 | Responsibility | Head of User Department · Organisation Unit | Select |
| 3 | Organisation Unit | Ministry of Health › Directorate of Digital Health and Policy | Tree select |
| 4 | Appointment | Acting | Segmented control, **Acting** selected |
| 5 | Effective from | 1 Oct 2026, 00:00 | Date and time input |
| 6 | Effective to | 30 Nov 2026, 23:59 | Date and time input |
| 7 | Authority reference | MOH/HR/ACT/2026/041 | Single-line input |

**Responsibility summary** — read-only panel:

> Julia Njeri will be Head of User Department for Directorate of Digital Health and Policy from 1 Oct 2026 until 30 Nov 2026.
>
> This includes 1 subordinate organisation unit. **View included units.**

**Exclusive office notice** — shown between the summary and the footer:

- Heading: **This office is already held**
- Text: **Dr Peter Kimani holds Head of User Department for this scope until 30 Nov 2026. Revoke that assignment before creating an overlapping one.**

- Footer buttons: **Cancel** and primary **Assign responsibility**, shown disabled

### 13.7 AUTH-DES-06 — Responsibility detail

**Fixture context — outside the artboard:** Administrator · `administrator@moh.example.test` · Ministry of Health · 1 Sep 2026, 10:20 EAT · Frappe header breadcrumb: **Home > Configuration and Governance > System setup**.

**Page content header**

- Eyebrow: **URA-2026-0001**
- Title: **Grace Wanjiku — Departmental Author**
- Status badge: **Active**
- No header action button

**Assignment card**

| Label | Value |
|---|---|
| User | Grace Wanjiku · grace.wanjiku@moh.example.test |
| Responsibility | Departmental Author |
| Scope classification | Organisation Unit |
| Organisation Unit | Ministry of Health › Directorate of Digital Health and Policy › Digital Health |
| Included units | This unit only |
| Appointment | Permanent |
| Effective period | From 1 Sep 2026, 09:00 EAT · No scheduled end |

**Audit card**

| Label | Value |
|---|---|
| Assigned by | Administrator |
| Assigned at | 1 Sep 2026, 09:00 EAT |
| Frappe role projection | Synchronised |

**Access diagnostics** — collapsed section, shown in its collapsed state with the heading **Access diagnostics** and a chevron. Do not draw the expanded contents.

**Administrative history** — table:

| When | Actor | Event |
|---|---|---|
| 1 Sep 2026, 09:00 EAT | Administrator | Responsibility assigned |

**Sticky page footer**

- Right-aligned destructive secondary button: **Revoke responsibility**

Do not show an Edit action, a Procuring Entity row, a Financial Year row or an approval trail.

### 13.8 AUTH-DES-07 — Revoke responsibility dialog

520 px modal over a dimmed AUTH-DES-06.

- Title: **Revoke responsibility?**
- Text: **Grace Wanjiku will immediately lose Departmental Author authority for Digital Health. Existing decisions and audit history will remain unchanged.**
- Field label: **Reason for revocation**
- Exact value: **Officer has transferred to the Directorate of Preventive Health with effect from 1 September 2026.**
- Footer buttons: **Cancel** and destructive **Revoke responsibility**

### 13.9 AUTH-DES-08 — Common states

Produce five separate variants using the AUTH-DES-03 shell, section header and content position.

| Variant | Exact visible content |
|---|---|
| Loading | Table card with the text **Loading responsibilities…** and approved skeleton rows. |
| Empty register | Heading **No responsibilities assigned yet**; text **Assign the first business responsibility for this entity.**; primary button **Assign responsibility**. |
| Organisation structure missing root | In the AUTH-DES-01 shell: heading **Organisation structure needs repair**; text **The root organisation unit is missing. Run the governed repair before assigning responsibilities.**; no create action. |
| Organisation structure empty | In the AUTH-DES-01 shell: heading **No departments or units yet**; text **Add the first organisation unit beneath Ministry of Health.**; primary button **Add organisation unit**. |
| Forbidden | Heading **System setup is not available**; text **You do not have the technical access required to maintain responsibilities.**; no table or action. |
| Error | Heading **Responsibilities could not be loaded**; text **Try again. If the problem continues, contact support.**; secondary button **Try again**. |

Never represent a failure, a forbidden result or a missing configuration as an empty successful register.

### 13.10 Existing Frappe and KenTender controls

Frappe supplies the Desk header, breadcrumb, session controls, route lifecycle, dialogs, toasts, the tree control and accessibility primitives. KenTender supplies the established tokens and shared Vue components. Claude Design supplies only the page content defined in sections 13.2–13.9.

---

## 14. Functional interaction requirements — excluded from design prompts

### 14.1 Organisation structure section

- Load the whole tree from the root in one authorised call. There is no Procuring Entity resolution step and no PE selector.
- The tree is the Frappe tree control mounted inside the section. Do not reimplement expand, collapse, search or keyboard traversal.
- **Add organisation unit** opens the dialog beneath the selected node, or beneath the root when nothing is selected. It is unavailable while the root is missing.
- **Edit name** is available for a non-root unit and changes the display name only. The code and the parent are immutable.
- **Deactivate** is available for an Active non-root unit and requires an impact confirmation showing the count of affected Active assignments. It fails with exact blockers rather than a generic message. Historical records and assignments remain visible.
- **Reactivate** is available for an Inactive non-root unit whose parent is Active.
- Reparent and physical delete are not implemented in any form.
- `AddOrganisationUnit` revalidates administrator, root existence, parent and sibling uniqueness server-side and generates the code within the insert transaction.

### 14.2 Users and responsibilities section

- The register uses one server predicate for rows and counts. Filters are optional, changeable and non-authoritative.
- Derived status is computed server-side at read time from stored status and the effective period. The client never computes it.
- **View** routes to the responsibility detail. There is no inline edit and no bulk action.
- Search matches user full name, login identifier and responsibility label.

### 14.3 Assign responsibility dialog

- Fields 3 to 7 appear only as required by the selected registry role's `scope_type` and `appointment_type`. Selecting a Site-wide role hides the Organisation Unit control entirely; selecting Permanent hides Effective to and Authority reference.
- The Organisation Unit tree select is restricted to Active units.
- The summary and descendant count come from `PreviewResponsibilityAssignment`. The client never composes the summary sentence or counts descendants locally.
- The primary button stays disabled with a visible reason until every required value is present and the server preview is valid.
- Where the registry marks the role `exclusive_office`, the preview returns the exact conflicting assignment before confirmation. The UI shows it and blocks the save. It never invents a precedence rule or silently permits two effective office-holders.
- Saving calls one idempotent command that creates the Enabled assignment, synchronises the Frappe Role projection and writes audit atomically. A future start displays as Scheduled. There is no Draft, submission or approval stage.
- The UI disables the initiating button while the command is pending and reuses one idempotency key for retries.

### 14.4 Responsibility detail and revocation

- Active and Scheduled assignments show **Revoke responsibility**. Expired and Revoked assignments are read-only.
- There is no Edit action in any state. An incorrect assignment is revoked and replaced so historical authority is never rewritten.
- Revocation requires a reason of 10 to 500 characters, rechecks current status and remaining Role projections, then revokes atomically. A concurrent result reloads current state rather than reporting a failure.
- **Access diagnostics** is read-only. It reports the required and present Frappe Role projection, resolved Organisation Unit coverage, configuration conflicts, orphan Frappe Roles, obsolete User Permission or scope records awaiting migration, and a safe explanation of why a supplied record and action test resolves as it does. It never repairs or broadens access silently. Ordinary users never see it.

### 14.5 Routing and page behaviour

- `/app/system-setup` is the single setup entry under Configuration & Governance. Section anchors, direct load, refresh and browser back and forward all preserve a valid page state.
- The page registers in `cl_surface_registry` and `STITCH_DESK_SURFACES` and provides `data-testid="back-to-workbench"`, returning to Configuration & Governance rather than raw `/desk`.
- No remembered browser context is required to open the page, and none grants or restricts authority.

### 14.6 Common page behaviour and accessibility

- Use semantic headings, labels, tables, status text and keyboard-operable controls. Colour is never the only carrier of state.
- Dialog focus is trapped and restored. Validation focus moves to the first invalid control or the error summary.
- Loading, empty, missing-root, forbidden and error states use the exact copy in AUTH-DES-08.
- All dates display in the site timezone. Service and audit instants remain UTC.
- Do not wait for `networkidle` on a Frappe Desk page. Tests wait for DOM content plus the exact page-ready selector.
- Route changes unmount the Vue app and cancel stale requests.

---

## 15. Audit and historical integrity

Every protected decision retains: assignment ID; user; business role; Organisation Unit scope; appointment type and authority reference where applicable; effective period evaluated; record and task state; decision time and correlation ID; and segregation result.

- Later changes to an assignment never rewrite historical decision evidence.
- Assignment records are never physically deleted. Revocation is a state change with a reason and an actor.
- Timestamps and actors are system-generated. A client cannot supply or amend them.
- Administrative history on an assignment is append-only.
- Administrator and System Manager reads do not imply a business action. Standard technical access logging applies; no support-reason form is required.

---

## 16. Deterministic seed contract

### 16.1 Configuration prerequisites

| Object | Seeded value |
|---|---|
| Site Procuring Entity | `PE-MOH` — Ministry of Health, timezone `Africa/Nairobi` |
| Root Organisation Unit | Ministry of Health, code `PE-MOH`, Active |
| Organisation Units | `OU-MOH-DHP` Directorate of Digital Health and Policy; `OU-MOH-DHI` Digital Health beneath it; `OU-MOH-HRMD` Human Resources Management and Development |
| ERPNext Fiscal Years | FY 2026/27 and FY 2027/28 |

### 16.2 Actors and assignments

| User | Responsibility | Scope | Appointment | Period |
|---|---|---|---|---|
| Grace Wanjiku | Departmental Author | `OU-MOH-DHI` | Permanent | From seed instant, no end |
| Dr Peter Kimani | Head of User Department | `OU-MOH-HRMD` | Permanent | From seed instant, no end |
| Julia Njeri | Head of User Department | `OU-MOH-DHI` | Acting | 1 Oct 2026 – 30 Nov 2026 |
| Mercy Kilonzo | Procurement Planner | Site-wide | Permanent | From seed instant, no end |
| Samuel Otieno | Head of User Department | `OU-MOH-DHP` | Permanent | 1 Jan 2026 – 31 Aug 2026, expired |

Grace additionally holds Head of User Department in `OU-MOH-HRMD` in the Cartesian-product fixture, so the regression test in section 18 has a concrete subject.

### 16.3 Seed execution rules

- Seeds create User Responsibility Assignments through the same administration command as the UI. They never write the DocType directly.
- Seeds create no Frappe User Permission, `User Scope Assignment`, `Capability Profile`, Fiscal Year grant or `kt_primary_department` value as KenTender authority.
- Seeds never grant a business role to Administrator.
- Seeds are idempotent. Re-running produces no duplicate assignment and no duplicate Organisation Unit.

---

## 17. Acceptance contract

| ID | Required result |
|---|---|
| AUTH-AC-001 | One User Responsibility Assignment binds user, business role, organisational scope and effective period. |
| AUTH-AC-002 | Separate Frappe Roles, User Permissions or scope rows cannot independently grant KenTender business authority. |
| AUTH-AC-003 | A Departmental Author in Digital Health who is also Head of User Department in HRMD can author only in Digital Health and decide only in HRMD. |
| AUTH-AC-004 | A Site-wide Planner assignment and an OU-scoped Author assignment coexist without narrowing or broadening each other. |
| AUTH-AC-005 | One parent-OU assignment covers its descendants and never a sibling outside that subtree. |
| AUTH-AC-006 | Assignment to a leaf covers only that leaf and any actual descendants. |
| AUTH-AC-007 | Holding a Frappe Role projection without a matching Active assignment grants no business read or command. |
| AUTH-AC-008 | The same predicate scopes lists, counts, detail, tasks, files, exports, reports and commands. A record hidden from a list is unreachable by direct route. |
| AUTH-AC-009 | A Query or Script Report over scoped data returns the same rows as the equivalent list, and one built without the shared match conditions fails the release gate. |
| AUTH-AC-010 | Tasks route work but do not authorise an unassigned actor. |
| AUTH-AC-011 | Fiscal Year is absent from User Responsibility Assignment and from every per-user grant flow. |
| AUTH-AC-012 | One assignment works across every Fiscal Year eligible under domain records and module flags, with no annual edit. |
| AUTH-AC-013 | Changing, clearing or corrupting a browser context does not change authority. |
| AUTH-AC-014 | A future or closed Fiscal Year selection never prevents later work in another eligible year. |
| AUTH-AC-015 | Acting responsibility starts and ends at the configured instants without a new role label, and is enforced at command time rather than by a scheduled job. |
| AUTH-AC-016 | An expired assignment leaves no orphan Frappe Role projection after reconciliation runs. |
| AUTH-AC-017 | An exclusive office rejects a second overlapping Active assignment and returns the exact conflicting record. |
| AUTH-AC-018 | Administrator and System Manager inspect all data without business assignments but cannot make a business decision without one. |
| AUTH-AC-019 | System setup completes a grant and a revocation without raw User Permission editing or a seed script. |
| AUTH-AC-020 | Organisation Unit is the sole business scope tree; exactly one root exists and no `procuring_entity` field is present on any Organisation Unit or assignment. |
| AUTH-AC-021 | No Procuring Entity selector, switcher or column appears on any screen, and creating a second Procuring Entity is structurally impossible. |
| AUTH-AC-022 | An immutable legal record carries a PE name and code snapshot that survives a later rename of the entity. |
| AUTH-AC-023 | Reparent and physical delete are absent; deactivation preserves referenced history and fails with exact blockers. |
| AUTH-AC-024 | An administrator adds an Organisation Unit beneath the root without creating an Organisation Unit Type or using a raw DocType form. |
| AUTH-AC-025 | The tree exposes names, codes, status and hierarchy without exposing nested-set internals. |
| AUTH-AC-026 | The assignment dialog shows the Organisation Unit control only for OU-scoped responsibilities and the Acting fields only for Acting appointments. |
| AUTH-AC-027 | The assignment dialog never shows a Procuring Entity, Fiscal Year, module, capability, User Permission or arbitrary-scope control. |
| AUTH-AC-028 | The server preview and the saved assignment produce the same user, responsibility, scope, descendant set and effective period. |
| AUTH-AC-029 | Saving creates an Enabled assignment directly; Scheduled, Active and Expired are derived without any approval workflow. |
| AUTH-AC-030 | Active assignments cannot be edited; revoke-and-replace preserves the original assignment and its audit history. |
| AUTH-AC-031 | Loading, empty, missing-root, forbidden and server-failure states are visibly distinct and never appear as an empty successful register. |
| AUTH-AC-032 | Direct route, refresh, back, forward and return to Configuration and Governance preserve a valid page state. |
| AUTH-AC-033 | An administrator completes structure → assign → verify → revoke on one route without raw Frappe administration or a seed script. |
| AUTH-AC-034 | `Procurement Department` and `kt_primary_department` supply no authority after cutover. |
| AUTH-AC-035 | Migration reports every ambiguous or scope-broadening case and creates no authority for it automatically. |
| AUTH-AC-036 | Cleanup removes only KenTender-owned User Permission rows; ERPNext and HRMS User Permissions for Company, Cost Center, Employee and Department remain intact and payroll and accounting continue to function. |
| AUTH-AC-037 | No KenTender authorization path reads HRMS Department, an HRMS approver chain, ERPNext Cost Center or ERPNext Company. |
| AUTH-AC-038 | No production authorization read references a retired store after cutover. |
| AUTH-AC-039 | A module cannot introduce an additional approval stage through the authorization mechanism. |
| AUTH-AC-040 | Decision audit identifies the exact responsibility assignment exercised. |

---

## 18. Implementation and test constraints

### 18.1 Frappe and UI implementation

- Implement `Organisation Unit` as a proper Frappe tree DocType. Do not hand-roll parent traversal, descendant queries or tree rendering.
- Register the shared predicate through `permission_query_conditions` and `has_permission` for every DocType in `kentender_scope_map`. Domain apps then use ordinary `frappe.get_list` and `frappe.has_permission`.
- Domain apps call `require_responsibility()` only for business commands. They never query the assignment DocType directly and never write module-local scope logic.
- Mount Vue 3 pages through the existing `frappe.ui.make_app_page()` → built bundle → `createApp().mount()` pattern. Mount the Frappe tree control inside the Organisation structure section rather than rebuilding it in Vue.
- Port Claude Design markup and tokens into scoped Vue single-file components. Design export runtime files remain design evidence under `docs/` and are never imported into production.
- Keep component styles scoped beneath one System setup root. Do not add Tailwind Preflight, a CDN, global element resets or rules that restyle Frappe Desk.
- Use Frappe RPC or resource APIs for authorised services. Do not expose writable DocType endpoints that bypass the administration commands.
- Add stable accessible test selectors to page-ready state, tree nodes, field controls, tables, dialogs and primary commands. Do not select by visual CSS classes.

### 18.2 Minimum automated coverage

1. Positive and negative resolution for each scope type.
2. Cartesian-product regression: same user, different roles, different Organisation Units.
3. Site-wide and OU-scoped responsibilities held simultaneously without interference.
4. Parent, leaf, sibling and deep-descendant tree tests.
5. Current, scheduled, expired and revoked assignments at boundary instants.
6. Exclusive-office overlap and Acting-period tests.
7. Role projection present without assignment, and assignment present without projection.
8. Equivalence across list, count, detail, task, file, export, report and command.
9. Report and raw-SQL scoping test proving `build_match_conditions` is applied.
10. Direct-route access to a record excluded from the actor's list.
11. Stale, cleared and corrupted browser context.
12. Multi-Fiscal-Year test proving no annual user grant is required.
13. Task present, task absent and task without assignment.
14. Maker-checker and evidence-chain segregation.
15. Administrator and System Manager read-all with business mutation denied.
16. Idempotent grant, revoke, role synchronisation and migration.
17. Projection reconciliation after time expiry.
18. ERPNext and HRMS non-interference: payroll and accounting User Permissions survive cleanup and remain effective.
19. Repository scan proving retired authority stores and Fiscal Year user grants are absent from production authorization reads, and that `ignore_permissions=True` does not appear in a scoped read path.
20. Browser journey: a departmental user creates a record from one ordinary assignment with no pre-entry context step.
21. Administration journey: grant, inspect, act, revoke and verify immediate denial.
22. Component tests for tree section, add dialog, assignment dialog variants, descendant preview, Acting fields and validation copy.
23. Register and detail tests for filters, derived status, immutable history, diagnostics and revoke-and-replace.
24. UI state tests proving loading, empty, missing-root, forbidden and server failure are distinct.
25. Route tests for the single setup entry, direct load, section anchors, refresh, back, forward and return path.

### 18.3 TDD and efficient verification

For each behaviour change: write or identify the smallest failing test; run that exact test node; implement the minimum coherent fix; rerun the same test; run the directly affected group; run the one relevant browser smoke and screenshot where UI changed; then run the authorization module suite once the focused group is green.

Do not rerun the whole repository suite, all browser tests or every screenshot after each small fix. Because this is shared infrastructure, the release gate additionally requires affected-module tests and cross-app contract tests. A happy-path module test alone is insufficient.

When a failure occurs, preserve the first useful traceback, server response, browser console error and screenshot. Classify it as product, fixture, selector, environment or unrelated before changing code.

### 18.4 Required release evidence

- Targeted red-green record for every acceptance criterion changed during implementation.
- Clean authorization module suite and clean cross-app contract tests.
- Successful production-mode asset build.
- Scripted browser smoke with zero System setup console errors and zero failed own requests.
- Visual comparison for all approved artboards at 1440 × 1024.
- Schema scan proving `procuring_entity` is absent from Organisation Unit and User Responsibility Assignment, and that every prohibited field, object and legacy route is absent.
- Cleanup dry-run output enumerating exactly which User Permission rows would be deleted, reviewed before execution.

---

## 19. Prohibited shortcuts

- Do not keep `User Scope Assignment` and `User Responsibility Assignment` both active.
- Do not treat Frappe User Permission as a KenTender fallback.
- Do not pair independent Role and scope rows at runtime.
- Do not add a Procuring Entity field, selector, column or permission anywhere, including "for future reporting".
- Do not create a second Procuring Entity record or simulate multi-tenancy inside one site.
- Do not add Fiscal Year to an assignment.
- Do not store authoritative context in local storage, session defaults or a user profile.
- Do not add module-specific scope resolvers or query the assignment DocType from a domain app.
- Do not call `authorise_record()` in place of registering the permission hooks.
- Do not write a Query or Script Report over scoped data without the shared match conditions.
- Do not use `ignore_permissions=True` in a scoped read path.
- Do not authorise from a task, queue, menu, route or UI button.
- Do not read HRMS Department, an HRMS approver chain, ERPNext Cost Center or ERPNext Company in an authorization path.
- Do not delete ERPNext or HRMS User Permission rows during cleanup.
- Do not grant Administrator business roles in fixtures to bypass setup.
- Do not broaden a user's Organisation Unit to a parent during migration.
- Do not add an approval level while translating a role.
- Do not implement reparent or physical delete for Organisation Units.
- Do not rebuild the Frappe tree control in Vue.
- Do not copy runtime rules from section 14 into a Claude Design prompt, or infer runtime behaviour from generated HTML.
- Do not import Claude Design canvas runtime files into production.
- Do not create a second Frappe header, breadcrumb, shell or global context selector.
- Do not delete old authority records before cutover evidence is complete.
- Do not change any production permission mechanism piecemeal before the schema, hooks, migration report and focused tests are ready for one controlled cutover.

---

## 20. Traceability and precedence

This document is the single KenTender authorization authority. Its model, resolver, design, interaction, seed and implementation sections are mutually controlling parts of one specification.

Where another approved document owns a value or decision, its domain authority prevails for that value:

1. **CFG-CHG-002 v0.5** for the site Procuring Entity record, ERPNext Fiscal Year surfacing, module flags, Organisation Unit identity, unit catalogue and the System setup page shell.
2. **This document** for role-bound assignment, organisational scope semantics, resolution, administrator inspection and the two System setup sections listed in section 12.
3. **Each module document** for its approved business roles, record ownership, states, tasks, approvals, segregation and domain invariants.

This ADR supersedes any statement in a KenTender requirements, design, implementation, seed or test document that treats a Frappe User Permission, `User Scope Assignment`, `Capability Profile`, `Operational Scope Assignment`, a per-user Fiscal Year grant, a browser-stored context, a task, a menu item or a bare role label as business authority. It supersedes that wording only; approved domain workflow is unchanged.

The immediate affected documents are:

| Document | Required correction |
|---|---|
| NDS-CHG-001 | Already aligned at v1.4. Confirm the `Site-wide` scope label and the removal of `permitted_pe_scopes`. |
| PLN-CHG-001 | Replace PE, OU and Budget User Permission language with role-bound assignments. Planning Fiscal Year remains derived. Budget scope remains a record-domain eligibility check. |
| STR-CHG-001 | Bind Strategy Author and Approver to Site-wide scope. Retain only approved workflow stages. |
| BUD-CHG-001 | Bind Budget responsibilities to Site-wide scope. Do not make Fiscal Year a user grant. Record the Cost Center boundary in section 7. |
| REQ-CHG-001 | Bind departmental and procurement responsibilities separately. Preserve the approved Requisition workflow without inventing approvers. |
| TPR-CHG-001 and later Tender modules | Bind each Tender responsibility to its approved scope. Do not use page context or free-text roles as authority. |
| CFG-CHG-002 / CTX-CHG-001 | Adopt the one-site-one-PE model, remove `PE Fiscal Year Context`, and own the Fiscal Year module flags. |

If an implementation ambiguity would add a field, action, screen, object or role, the default answer is **omit it** until a current operational purpose, named consumer, validation and effect are approved.

---

## 21. Approval effect

On approval, AUTH-ADR-001 v1.5 supersedes v1.4, v1.3, v1.2, v1.1 and v1.0 in full and becomes the only KenTender authorization document to consult.

Approval authorises: the `User Responsibility Assignment` DocType and the two System setup sections in section 12; the code-owned role registry with two scope types; the site Procuring Entity as a Single DocType; `Organisation Unit` as the single site-local nested-set tree without a PE field; the shared predicate registered through both Frappe permission hooks; Frappe Role synchronisation as a projection with expiry reconciliation; adoption of the ERPNext `Fiscal Year`; retirement of Frappe User Permission, `User Scope Assignment` and the older capability stores as KenTender authority; removal of per-user Fiscal Year grants, `PE Fiscal Year Context`, PE selectors and authoritative browser context; the controlled migration and scoped cleanup in section 11; and full successor versions of the affected module documents in section 20.

Implementers shall not retain v1.4's separate Organisation structure and User responsibilities routes, its Procuring Entity scope dimension, its `Global` scope type or its bespoke resolver API as active product surfaces.
