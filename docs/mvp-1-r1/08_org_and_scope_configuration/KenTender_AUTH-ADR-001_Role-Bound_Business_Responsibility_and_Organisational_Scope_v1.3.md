# AUTH-ADR-001 — Role-Bound Business Responsibility and Organisational Scope

| Control | Value |
|---|---|
| Document ID | AUTH-ADR-001 |
| Version | 1.3 |
| Date | 1 September 2026 |
| Status | Proposed for approval |
| Applies to | Every KenTender module, list, count, task, file, export, screen and business command |
| Change type | Complete consolidated successor to v1.2 |
| Corrects | Contradictory scope authorities, unbound Role and scope grants, inert organisation hierarchy, per-user Financial Year access, browser-context authority and the missing administration UI contract |
| Implementation owner | `kentender_core` for the shared assignment, resolver and administration surface; each domain app for record-state and business-rule checks |

## 1. Decision

KenTender shall use one role-bound record, **User Responsibility Assignment**, as the sole authority for a person's KenTender business responsibility and organisational scope.

An active assignment answers one complete question:

> Which business responsibility may this user exercise, for which Procuring Entity and Organisation Unit scope, and during what effective period?

The authoritative formula is:

> Effective business authority = one active User Responsibility Assignment matching the required business role and the record's PE/OU scope + eligible record, Financial Year, module window and task state + segregation and domain-rule checks.

The following are not independent authority sources:

- a Frappe Role by itself;
- a Frappe User Permission;
- `User Scope Assignment`;
- `Capability Profile` or `Operational Scope Assignment`;
- `kt_primary_department`;
- a browser, session or page context;
- a work task or notification; or
- a Financial Year assignment to a user.

There shall be no fallback chain in which any one of several stores may grant access. Every KenTender list and command shall call the same shared resolver.

## 2. Why v1.1 is insufficient

AUTH-ADR-001 v1.1 correctly removed Financial Year from user identity and rejected the old custom capability store. It incorrectly selected separate Frappe Role and User Permission records as the final business authority.

That creates two structural defects.

### 2.1 Two current scope mechanisms disagree

The implementation contains both:

- `User Scope Assignment`, which some read paths use to determine permitted PEs; and
- native Frappe `User Permission`, which protected commands use through the native authorization path.

A user can therefore see a record under the first mechanism and be denied every action under the second. An administrator cannot explain or fix the result through one coherent screen.

### 2.2 Separate Role and scope records lose the relationship between them

Separate Role and User Permission records form an unintended Cartesian product. For example, if one user is a Departmental Author in OU-A and an acting Head of User Department in OU-B, the system can see both Roles and both OUs but cannot prove which Role belongs to which OU. It may wrongly apply both responsibilities to both departments.

The same defect appears when a user has a PE-wide role such as Procurement Planner and an OU-scoped role such as Departmental Author. A separate OU restriction may incorrectly narrow the PE-wide responsibility, while omitting it may incorrectly broaden the departmental responsibility.

The relationship must therefore be stored directly: **User + Role + PE + OU + effective period**.

### 2.3 The organisation hierarchy exists only as data labels

KenTender currently carries parent references on organisational records but does not expose one authoritative nested-set organisation tree to the permission engine. Administrators must enumerate leaves, higher-level responsibility does not consistently cover descendants, and duplicate department concepts can disagree.

### 2.4 Access administration is not a usable product operation

Raw Role assignment, raw User Permission, custom scope rows, seed helpers and unused primary-department fields are not a manageable operating model. A normal KenTender administrator needs one understandable operation: assign a named responsibility to a user in a named organisational scope.

## 3. Supersession and precedence

This complete document supersedes AUTH-ADR-001 v1.2, v1.1 and v1.0 in full.

It also supersedes any statement in a KenTender requirements, design, implementation, seed or test document that treats any of the following as business authority:

- Frappe User Permission;
- `User Scope Assignment`;
- `Capability Profile`;
- `Operational Scope Assignment`;
- a per-user `Financial Year` or `PE Fiscal Year Context` permission;
- a browser-stored PE, OU or FY context;
- a task, menu item or queue by itself; or
- a role label without a matching role-bound assignment.

Module documents remain authoritative for business roles, record ownership, states, windows, tasks, approvals, segregation and domain invariants. This ADR alone controls how a user is bound to a role and organisational scope.

If a module document repeats a different assignment mechanism, this ADR prevails without adding an approval level or changing the module's approved business workflow.

## 4. One authoritative assignment

### 4.1 User Responsibility Assignment

`User Responsibility Assignment` is a governed DocType owned by `kentender_core`.

| Field | Rule |
|---|---|
| `user` | Required Link to an enabled System User. |
| `business_role` | Required Link or governed code from the code-owned KenTender role registry. |
| `procuring_entity` | Required for PE- and OU-scoped roles; prohibited for Global roles. |
| `organisation_unit` | Required for OU-scoped roles; prohibited for PE- and Global roles. |
| `effective_from` | Optional UTC instant. Blank means effective immediately once Enabled. |
| `effective_to` | Optional UTC instant later than `effective_from`. Blank means no scheduled end. |
| `appointment_type` | `Permanent` or `Acting`. Required. This changes evidence, not capability. |
| `authority_reference` | Required for Acting assignments; optional for Permanent assignments according to administrative policy. |
| `status` | Stored value `Enabled` or `Revoked`. The server derives `Scheduled`, `Active`, `Expired` or `Revoked` for display. Only Active authorizes. There is no assignment-approval workflow. |
| `assigned_by` / `assigned_at` | Server-set audit fields. |
| `revoked_by` / `revoked_at` / `revocation_reason` | Server-set when revoked; reason required. |

No Financial Year, module, capability string, task, browser preference or arbitrary JSON policy belongs on the assignment.

### 4.2 Uniqueness and overlap

The same user shall not have overlapping Enabled assignments for the same `business_role + procuring_entity + organisation_unit` tuple. An idempotent request for the same assignment returns the existing record.

Different roles may be assigned in different scopes. Each command resolves only the assignment for the role it requires; other roles held by the user do not broaden that assignment.

### 4.3 Acting responsibility

An acting officer receives the same business role as the substantive officer, with the exact PE/OU scope and effective dates. KenTender shall not invent `Delegate`, `Acting Approver` or substitute approval levels.

When only one effective office-holder may act, the owning module or role registry shall enforce the no-overlap rule for that office. Expiry is evaluated at command time; a scheduled job may update display status but is not the security control.

### 4.4 Assignment audit snapshot

Every protected decision shall retain:

- assignment ID;
- user;
- business role;
- PE and OU scope;
- appointment type and authority reference where applicable;
- effective period evaluated;
- record and task state;
- decision time and correlation ID; and
- segregation result.

Later changes to the assignment shall not rewrite historical decision evidence.

## 5. Code-owned business-role registry

KenTender shall maintain one reviewed, code-owned registry. Administrators assign registered responsibilities; they do not define new roles, scope types or capability strings in production.

Each entry contains:

| Property | Meaning |
|---|---|
| `business_role` | Stable exact role code and display label. |
| `scope_type` | `Global`, `Procuring Entity` or `Organisation Unit`. |
| `frappe_roles` | Minimal framework Role projection needed for Desk/DocType access. |
| `exclusive_office` | Whether only one effective assignment may occupy this office for the same scope. |
| `allowed_assignment_admin` | Administrative responsibility allowed to grant/revoke it. |
| `sod_tags` | Stable categories used by domain segregation checks, never free-form capabilities. |

The registry does not list each command. Commands name the business role required by the approved module contract.

Initial scope classifications are:

| Scope type | Illustrative responsibilities |
|---|---|
| Global | Central reference/configuration stewardship and explicitly approved central oversight only. |
| Procuring Entity | Strategy Author/Approver, Budget roles, Procurement Planner, Head of Procurement Function, Accounting Officer and Tender roles whose approved work spans the PE. |
| Organisation Unit | Departmental Author, Head of User Department and Requisition Preparer. |
| Technical | Administrator and System Manager technical inspection/support under section 11; not business assignments. |

The applicable module document remains the source of the exact role names and business actions. The registry shall not invent another approval stage.

## 6. One organisation model

### 6.1 Authoritative tree

`Organisation Unit` shall be the only organisational hierarchy used for KenTender business scope.

It shall be a Frappe nested-set tree with:

- `is_tree = 1`;
- `parent_org_unit` as the parent field;

- framework-maintained `lft` and `rgt` values;
- one required `procuring_entity` on every node; and
- validation that a child and its parent belong to the same PE; and
- exactly one system-created root Organisation Unit for each active PE.

A PE is the hard tenant boundary. No root, parent, descendant traversal or assignment may cross a PE.

The PE root is created idempotently when the PE becomes active. Administrators add operational units beneath it; they do not create or select the PE root manually. `Organisation Unit Type` is not required for authorization or unit creation. It shall not block the structure unless a separately approved operational consumer is documented.

### 6.2 Descendant rule

An OU-scoped assignment covers the selected Organisation Unit and all of its descendants in the same PE. There is no `include descendants` switch.

To authorize one department only, assign its leaf node. To authorize a directorate and its branches, assign the directorate node once.

Hierarchy expands **where the assigned role applies**. It never creates another role. A Head of User Department assignment does not make the user a Departmental Author, Planner or Accounting Officer.

### 6.3 Duplicate and phantom fields

- Retire `Procurement Department` as a separate scope hierarchy. Existing records shall map to an exact Organisation Unit before cutover.
- Remove `kt_primary_department` if it has no approved display purpose. If retained as a user preference, label it as a default view only and never read it for authorization.
- Do not encode PE or OU scope in free text, email domain, job title, naming series or browser storage.

## 7. Frappe integration

### 7.1 Frappe Roles are a projection, not a grant

The assignment service shall add the minimal Frappe Role projection required by every active assignment. Revocation removes a projected Role only when no other active assignment still requires it.

Direct manual addition of a Frappe Role does not create KenTender business authority. Diagnostics shall report it as an orphan projection. Direct manual removal is repaired or reported according to the controlled reconciliation rule; it shall not silently invalidate an otherwise active assignment.

Role Permission Manager continues to provide coarse DocType access. Record visibility and every business command remain subject to the shared KenTender resolver.

### 7.2 Frappe User Permission is not KenTender authority

KenTender shall not consult Frappe User Permission when resolving PE, OU, Financial Year or business-role authority.

Existing KenTender-related User Permission rows may remain temporarily for unrelated framework behaviour during migration, but they shall not grant or deny a KenTender list or command after cutover. They are removed only after the new resolver, query hooks and regression tests are active.

### 7.3 No alternate scope store

`User Scope Assignment`, `Capability Profile` and `Operational Scope Assignment` shall not appear in the production authorization read path. Existing records are migration input and then historical evidence or retired data according to section 15.

## 8. Shared authorization resolver

### 8.1 Ownership and public interface

`kentender_core` owns one public authorization service. Domain apps shall depend only on this public contract and shall not query the assignment DocType directly.

The service provides at least:

| Operation | Result |
|---|---|
| `resolve_assignments(user, business_role, at)` | Active assignments for one required role at one instant. |
| `permitted_pe_scopes(user, business_role, at)` | Exact PEs authorized by that role. |
| `permitted_ou_scopes(user, business_role, at)` | Exact assigned OUs and derived descendants, always within their PE. |
| `authorise_record(user, business_role, record_scope, at)` | One allow/deny result with the exact matching assignment ID. |
| `permission_query(user, business_role, scope_columns, at)` | Server-side predicate for permission-aware lists, counts and task queries. |
| `diagnose_user(user, at)` | Human-readable assignments, projections, conflicts and orphans for administration. |

The exact Python names may follow repository conventions, but there shall be one semantic implementation.

### 8.2 Resolution algorithm

For a protected command, the server shall:

1. authenticate an enabled System User;
2. load the registered required business role;
3. find active assignments for that user and role at the server clock instant;
4. match the record's PE and, for OU roles, the assigned OU subtree;
5. require the coarse Frappe DocType operation expected for the command;
6. check the record's Financial Year, configured module window and record state;
7. check the open task where the workflow uses one;
8. apply maker-checker and other segregation rules;
9. check optimistic concurrency and domain invariants; and
10. write the decision and assignment snapshot atomically.

The client never submits an assignment ID, effective role, permitted scope or available action as authority. If supplied as display data, the server ignores it and resolves again.

### 8.3 One predicate everywhere

The same resolver semantics shall govern:

- workspace rows and counts;
- ordinary lists and reports;
- review/task sections;
- direct record routes;
- detail reads;
- commands;
- file and attachment downloads;
- exports and print views;
- background jobs acting for a user; and
- public APIs.

A read path and command path may not call different scope mechanisms. Counts must not disclose records that rows cannot show. Files must not remain accessible after the parent record is denied.

### 8.4 Tasks and queues

A task routes eligible work; it never creates authority. The actor must still hold the matching active assignment.

Module work appears inside the module workspace, shared My Work and notifications. A module shall not create a sidebar menu entry merely to expose a role queue unless a separate approved navigation requirement explicitly says so.

## 9. Financial Year and operating context

Financial Year is record and configuration data, not identity and not an assignment dimension.

The allowed operation is determined by:

- the record's own Financial Year or PE/FY context;
- configured PE Fiscal Year Context records;
- the owning module's open/closed/scheduled window;
- the record's state; and
- the active PE/OU business-role assignment.

One assignment therefore works across every Financial Year that the owning module makes eligible. No annual user reprovisioning is permitted.

A PE, OU or FY selector is a visible, changeable view or create-target choice. It:

- does not grant access;
- is not required before opening a direct record or task;
- may be changed whenever more than one authorized option exists;
- is ignored when stale, invalid or absent; and
- shall never trap a user in a future or closed period.

Create screens shall show only targets derived from active assignments plus the module's eligible windows or records. Browsing may include historical authorized records even when creation is closed.

## 10. Business roles, approvals and segregation

This ADR does not add a business approval stage.

- A module command requires the role or legal capacity already named in that module's approved requirements.
- `Applicable final authority`, `approving authority`, `workflow approver` and similar generic labels are prohibited unless an approved source defines that distinct legal capacity.
- Where the Accounting Officer is the approved final authority, no further approval is inferred.
- Where another statutory decision is expressly required, the module records that exact legal capacity rather than a generic additional level.

Users may hold multiple assignments. Segregation is evaluated against the actual actions in the same evidence chain. Holding two roles is not itself a violation; performing incompatible decisions is.

## 11. Administrator and System Manager

Administrator and System Manager shall have technical read access to all KenTender records, tasks, decisions, files, configuration and audit evidence across PEs, OUs and Financial Years.

They shall not need a PE, OU or FY assignment for that inspection. The interface shall provide a changeable PE/OU/FY filter or direct search so technical users are never stranded on an empty page.

Technical status does not authorize a business mutation. To create, certify, approve, reject, submit or otherwise exercise a business responsibility, the person must have the same active User Responsibility Assignment and pass the same state and segregation checks as any other user.

Seed and test data shall not add business roles to Administrator merely to make a journey pass.

## 12. Administration UI — complete contract

KenTender shall provide two ordinary Configuration and Governance administration surfaces:

| Surface | Route | Purpose |
|---|---|---|
| Organisation structure | `/app/organisation-structure` | Maintain the PE-bounded Organisation Unit tree used by assignments. |
| User responsibilities | `/app/user-responsibilities` | Assign, inspect and revoke one role-bound responsibility. |

These are configuration pages, not work queues. Both appear under the existing **Configuration and Governance** navigation group. Raw `/app/organisation-unit`, `/app/user-responsibility-assignment`, `/app/user-permission`, legacy operational-access and scope-assignment pages are not normal operating journeys.

Administrator and System Manager may use these surfaces. No additional business approval level or assignment-approval task is introduced.

Frappe supplies Desk navigation, shared header, breadcrumb, session controls, dialogs, toasts and accessibility primitives. The Vue page renders only the content canvas and uses the approved KenTender token chain and shared components.

### 12.1 AUTH-UI-01 — Organisation structure

#### 12.1.1 Page purpose and layout

The page manages one PE's organisational tree without exposing nested-set internals.

The page header contains:

- eyebrow **CONFIGURATION AND GOVERNANCE**;
- title **Organisation structure**;
- description **Maintain the departments and organisational units used to scope KenTender responsibilities.**; and
- a required, changeable **Procuring Entity** selector.

Below the header, use a two-column workspace:

- left: searchable Organisation Unit tree; and
- right: selected-unit details and available actions.

The tree shows the system-created PE root first. Each node shows unit name, stable code and `Active` or `Inactive`. Children are indented and may be expanded or collapsed. The UI never shows `lft`, `rgt`, `old_parent`, raw parent IDs or nested-set repair controls.

#### 12.1.2 Organisation Unit actions

| Action | Availability | Result |
|---|---|---|
| **Add organisation unit** | PE selected and its root exists | Opens the add dialog beneath the selected parent, or beneath the PE root when no child is selected. |
| **Edit name** | Non-root unit selected | Changes display name only; stable code and PE remain read-only. |
| **Deactivate** | Active non-root unit with no blocking active assignment or module rule | Marks the unit inactive after an impact confirmation. Historical records and assignments remain visible. |
| **Reactivate** | Inactive non-root unit and active parent | Restores availability for new assignments. |
| Reparent | Not available in this release | Omitted because it changes the effective scope of existing assignments. |
| Delete | Not available | Organisation Units are never physically deleted through the product UI. |

The add dialog contains exactly:

| Control | Type | Rule |
|---|---|---|
| Procuring Entity | Read-only | Inherited from the page. |
| Parent organisation unit | Tree path, read-only in the dialog | Selected before opening; defaults to PE root. |
| Organisation unit name | Text | Required; 2–160 characters; unique among active siblings after normalized comparison. |
| Organisation unit code | Read-only generated value | Generated on save and never user-entered. |

Buttons are **Cancel** and **Add organisation unit**. No Organisation Unit Type, Financial Year, role, manager, email, attachment, authority, permission or free-text scope field appears.

#### 12.1.3 Organisation structure states

| State | Exact user treatment |
|---|---|
| No PE exists | Heading **No Procuring Entity is configured**; text **Create and activate a Procuring Entity before maintaining its organisation structure.**; link **Open Procuring Entities**. |
| Active PE has no root because configuration is incomplete | Heading **Organisation structure needs repair**; text **The root organisation unit for this Procuring Entity is missing. Run the governed repair before assigning responsibilities.**; no child-create action. |
| Root exists with no children | Heading **No departments or units yet**; text **Add the first organisation unit beneath this Procuring Entity.**; primary action **Add organisation unit**. |
| Selected unit has active assignments | Show the count and a link **View affected responsibilities** before deactivation. |
| Load failure | Standard error state with correlation reference and **Try again**. Never show an empty tree as success. |

### 12.2 AUTH-UI-02 — User responsibilities register

#### 12.2.1 Page purpose and layout

The page header contains:

- eyebrow **CONFIGURATION AND GOVERNANCE**;
- title **User responsibilities**;
- description **Assign each user a business responsibility in its exact organisational scope.**; and
- primary action **Assign responsibility**.

One filter row contains:

- search **Search user or responsibility**;
- **Procuring Entity**;
- **Organisation Unit**;
- **Responsibility**;
- **Status** with `All statuses`, `Scheduled`, `Active`, `Expired`, `Revoked`; and
- **Clear filters**.

The register contains:

| Column | Content |
|---|---|
| User | Full name and login identifier. |
| Responsibility | Exact registry display label. |
| Procuring Entity | Name, or `Global`. |
| Organisation Unit | Exact unit name/path, or `—`. |
| Coverage | `This unit only` for a leaf, or `This unit and {n} descendants`. |
| Appointment | `Permanent` or `Acting`. |
| Effective period | Start/end display in `Africa/Nairobi`; `From now` and `No scheduled end` where applicable. |
| Status | Derived Scheduled, Active, Expired or Revoked badge. |
| Action | **View**. |

The initial register is not scoped by a remembered PE/FY browser context. Filters are visible, optional, changeable and non-authoritative.

### 12.3 AUTH-UI-03 — Assign responsibility dialog

The dialog title is **Assign responsibility**. It is a guided form whose fields change only from the selected registry role's scope classification.

| Order | Control | Type and rule |
|---:|---|---|
| 1 | User | Required Link search over enabled System Users. Display full name and login identifier. |
| 2 | Responsibility | Required governed select from the code-owned role registry. Display the exact label plus `Global`, `Procuring Entity` or `Organisation Unit` scope hint. |
| 3 | Procuring Entity | Required Link only for PE- and OU-scoped roles. Hidden for Global roles. |
| 4 | Organisation Unit | Required tree selector only for OU-scoped roles. Disabled until PE is selected and restricted to active units in that PE. |
| 5 | Appointment | Required segmented control: `Permanent` or `Acting`. |
| 6 | Effective from | Optional date/time for Permanent; required for Acting. Server interprets in PE timezone and stores UTC. |
| 7 | Effective to | Hidden for Permanent; required and later than start for Acting. |
| 8 | Authority reference | Hidden for Permanent; required structured reference text for Acting, 2–160 characters. A supporting private File may be attached only as evidence; it does not replace the structured assignment. |

There is no Financial Year, module, capability, arbitrary scope, User Permission, profile, task, approver or generic notes control.

After valid inputs, show a read-only **Responsibility summary**:

> {User} will be {Responsibility} for {scope description} {effective-period description}.

For an OU with descendants, add:

> This includes {n} subordinate organisation units. View included units.

If an exclusive responsibility would override or conflict with an existing assignment, the server returns the exact affected assignment before confirmation. The UI shall not invent a precedence rule or silently permit two effective office-holders.

Buttons are **Cancel** and **Assign responsibility**. The primary button remains disabled with a visible reason until every required value and server preview is valid.

Saving calls one idempotent administration command. It creates an Enabled assignment, synchronizes the Frappe Role projection and writes audit evidence atomically. A future start displays as Scheduled; there is no Draft or separate approval stage.

### 12.4 AUTH-UI-04 — Responsibility detail

The detail is opened from **View** and displays:

- user identity;
- responsibility and central scope classification;
- PE and Organisation Unit path;
- included descendant units;
- appointment type, effective period and authority reference;
- derived status;
- assignment reference;
- assigned by/at;
- revoked by/at/reason where applicable;
- synchronized Frappe Role projection status; and
- immutable administrative history.

For an Active or Scheduled assignment, show **Revoke responsibility**. Expired and Revoked assignments are read-only. There is no Edit action. Incorrect assignments are revoked and replaced so historical authority is never rewritten.

### 12.5 AUTH-UI-05 — Revoke responsibility dialog

Title: **Revoke responsibility?**

Body:

> {User} will immediately lose {Responsibility} authority for {scope}. Existing decisions and audit history will remain unchanged.

Require **Reason for revocation**, 10–500 characters. Buttons are **Cancel** and **Revoke responsibility**. The command rechecks current status and remaining Role projections, then revokes atomically. A successful result refreshes the register and detail; a concurrent result reloads the current state.

### 12.6 AUTH-UI-06 — Diagnostics

Diagnostics are part of the responsibility detail, not a separate legacy access screen. A collapsed **Access diagnostics** section shows:

- required and present Frappe Role projection;
- exact resolved PE/OU coverage;
- configuration conflicts or overlaps;
- orphan Frappe Roles;
- obsolete User Permission, User Scope Assignment or capability records awaiting migration; and
- a safe explanation of why a supplied record/action test is allowed or denied.

Diagnostics are read-only and do not silently repair or broaden access. Ordinary users never see internal permission details.

### 12.7 Menu, routing and registration

Both pages shall:

- appear under **Configuration and Governance**;
- use the existing KenTender/Frappe shell and header;
- register in `cl_surface_registry` and `STITCH_DESK_SURFACES`;
- use stable canonical routes and preserve them on refresh/back/forward;
- provide `data-testid="back-to-workbench"`;
- not create a second shell, global context selector or role-specific menu; and
- return to Configuration and Governance rather than raw `/desk`.

### 12.8 Static design fixtures

The Claude Design artboards are page-content canvases only. Do not draw the Frappe sidebar, header, breadcrumb, notifications, Help or user menu.

#### AUTH-DES-01 — Organisation structure

Fixture: Administrator · PE-MOH — Ministry of Health · 1 Sep 2026, 10:00 EAT · breadcrumb metadata **Home > Configuration and Governance > Organisation structure**.

Tree fixture:

- Ministry of Health `PE-MOH` — root, Active
  - Directorate of Digital Health and Policy `OU-MOH-DHP` — Active
    - Digital Health `OU-MOH-DHI` — Active
  - Human Resources Management and Development `OU-MOH-HRMD` — Active

Select **Directorate of Digital Health and Policy**. The right panel shows code, full path, Active status, `1 descendant`, buttons **Add organisation unit**, **Edit name**, **Deactivate**, and link **View 2 affected responsibilities**.

#### AUTH-DES-02 — User responsibilities register

Fixture: Administrator · 1 Sep 2026, 10:10 EAT · breadcrumb metadata **Home > Configuration and Governance > User responsibilities**.

Rows:

| User | Responsibility | PE | Organisation Unit | Coverage | Appointment | Period | Status |
|---|---|---|---|---|---|---|---|
| Grace Wanjiku | Departmental Author | Ministry of Health | Digital Health | This unit only | Permanent | From 1 Sep 2026 · No scheduled end | Active |
| Dr Peter Kimani | Head of User Department | Ministry of Health | Human Resources Management and Development | This unit only | Permanent | From 1 Sep 2026 · No scheduled end | Active |
| Julia Njeri | Head of User Department | Ministry of Health | Digital Health | This unit only | Acting | 1 Oct–30 Nov 2026 | Scheduled |
| Mercy Kilonzo | Procurement Planner | Ministry of Health | — | Entire Procuring Entity | Permanent | From 1 Sep 2026 · No scheduled end | Active |

#### AUTH-DES-03 — Assign responsibility

Show the open dialog with Grace Wanjiku, Departmental Author, Ministry of Health, Digital Health, Permanent. Summary:

> Grace Wanjiku will be Departmental Author for Digital Health from now with no scheduled end.

#### AUTH-DES-04 — Acting assignment

Show Julia Njeri, Head of User Department, Ministry of Health, Digital Health, Acting, 1 Oct–30 Nov 2026, authority reference `MOH/HR/ACT/2026/041`. Show the conflict/override area only when returned by the server preview.

#### AUTH-DES-05 — Common states

Provide distinct variants for loading, empty register, no configured PE, missing PE root, no Organisation Units, forbidden, validation failure and server failure. Do not represent failure as an empty successful register.

### 12.9 Functional interaction and API contract

| API | Required result |
|---|---|
| `GetOrganisationStructure(pe_id)` | Authorized tree projection, selected-node details, assignment-impact counts and allowed actions. |
| `AddOrganisationUnit(pe_id, parent_id, name, idempotency_key)` | Revalidate administrator, PE root, parent and sibling uniqueness; generate code and insert atomically. |
| `RenameOrganisationUnit(unit_id, name, expected_version)` | Change display name only after exact checks. |
| `SetOrganisationUnitActive(unit_id, active, expected_version)` | Recheck children, assignments and domain blockers; never delete. |
| `ListUserResponsibilities(filters, paging)` | Rows and counts from one server predicate; no browser-context authority. |
| `PreviewResponsibilityAssignment(user, role, pe, ou, appointment, dates)` | Return required fields, exact scope/descendants, overlap/exclusivity findings and human summary; create nothing. |
| `AssignResponsibility(...)` | Recompute preview, validate, create Enabled assignment, synchronize Role projection and audit atomically/idempotently. |
| `GetResponsibilityAssignment(id)` | Full authorized detail, audit and diagnostics. |
| `RevokeResponsibility(id, reason, expected_version, idempotency_key)` | Recheck, revoke and safely reconcile the Role projection atomically. |

Every mutation is authorized and validated server-side. Options, summaries, included-unit counts and available actions come from the server. Client controls are never authority.

## 13. Errors

| Code | User result |
|---|---|
| `AUTH_RESPONSIBILITY_REQUIRED` | You are not assigned the responsibility required for this action. |
| `AUTH_SCOPE_REQUIRED` | This record is outside the Procuring Entity or department scope of that responsibility. |
| `AUTH_ASSIGNMENT_INACTIVE` | Your responsibility assignment is not effective at this time. |
| `AUTH_TASK_REQUIRED` | This action is not currently assigned for decision. |
| `AUTH_SEGREGATION_BLOCKED` | You cannot perform this action because you completed an incompatible earlier step. |
| `AUTH_STATE_CHANGED` | This action is no longer available in the record's current state. |
| `AUTH_PERIOD_UNAVAILABLE` | This operation is not available for the record's Financial Year or current module window. |
| `AUTH_CONFIGURATION_INVALID` | The responsibility or organisational scope is not configured consistently. |

Cross-scope record reads use Not found where existence is protected. Ordinary user messages shall not name internal tables or permission algorithms.

## 14. Module adoption rule

Every module requirements document shall state only:

- its approved business roles;
- whether each role is Global, PE- or OU-scoped as registered centrally;
- the business actions and record states for each role;
- task and segregation rules; and
- any domain-specific read-only oversight.

It shall reference this ADR for assignment, hierarchy, context, administrator inspection and resolver behaviour. It shall not redefine those mechanisms.

The immediate affected documents are:

| Document | Required correction |
|---|---|
| NDS-CHG-001 | Replace Role + User Permission language with OU-scoped responsibility assignments; acting HoD is a dated assignment; create targets combine assignments and intake windows. |
| PLN-CHG-001 | Replace PE/OU/Budget User Permission language with role-bound assignments; Planning Financial Year remains derived; Budget scope remains a record-domain eligibility check where required. |
| STR-CHG-001 | Bind Strategy Author/Approver to their approved PE scope; retain only approved workflow stages. |
| BUD-CHG-001 | Bind Budget responsibilities to PE scope; do not make Financial Year a user grant. |
| REQ-CHG-001 | Bind departmental and procurement responsibilities separately; preserve approved Requisition workflow without inventing approvers. |
| TPR-CHG-001 and later Tender modules | Bind each Tender responsibility to its approved PE/record scope; do not use page context or free-text roles as authority. |
| CFG-CHG-002 / CTX-CHG-001 | Replace contradictory User Permission/User Scope Assignment authority with this assignment and context model. |

Until a full module successor is issued, this ADR directly supersedes only its contradictory authorization-mechanism wording; approved domain workflow remains unchanged.

## 15. Controlled migration

There shall be one atomic cutover programme, not a long-lived compatibility mode.

### 15.1 Inventory

Produce a read-only reconciliation containing:

- Frappe KenTender Roles by user;
- Frappe User Permissions for PE, OU, Financial Year and PE/FY Context;
- every User Scope Assignment;
- every Capability Profile and Operational Scope Assignment;
- `kt_primary_department` values;
- Organisation Unit and Procurement Department hierarchies;
- active acting/delegation records;
- all code paths that authorize from any of those stores; and
- proposed User Responsibility Assignments with their source evidence.

### 15.2 Deterministic mapping

- Convert an existing row only when user, business role, PE, OU and effective period are unambiguous.
- Merge duplicate source rows into one assignment and retain all source references in the migration audit.
- Do not infer a role from access scope alone.
- Do not infer PE/OU scope from a Role alone.
- Do not create a Financial Year assignment.
- Do not broaden a leaf OU to its parent to reduce row count.
- Mark conflicts and ambiguous combinations for explicit administrator resolution.
- Map `Procurement Department` to one exact Organisation Unit or block that record.

### 15.3 Cutover order

1. Approve the role registry and Organisation Unit tree rules.
2. Add the User Responsibility Assignment schema and administration service.
3. Add the shared resolver and permission-query integration with no production caller switched yet.
4. Build the Organisation structure and User responsibilities screens, diagnostics and their exact empty/error states.
5. Run reconciliation and resolve every ambiguous assignment.
6. Create assignments idempotently and synchronize Frappe Role projections.
7. Switch list, count, detail, task, file and command authorization to the shared resolver in one controlled release.
8. Stop all seeds and administration paths from creating old authority rows.
9. Run the cross-module authorization and user-journey gate.
10. Remove obsolete authorization reads and then clean up obsolete rows idempotently.
11. Retain immutable migration evidence and historical business decisions.

Data cleanup shall never precede code cutover and verification.

### 15.4 No fallback mode

After step 7, no production code may fall back to Frappe User Permission, User Scope Assignment, Capability Profile, Operational Scope Assignment, `kt_primary_department` or browser context when no assignment matches. The correct result is a stable denial plus an administrator diagnostic.

## 16. Acceptance contract

| ID | Required result |
|---|---|
| AUTH-AC-001 | One User Responsibility Assignment binds user, business role, PE/OU scope and effective period. |
| AUTH-AC-002 | Separate Frappe Roles, User Permissions or scope rows cannot independently grant KenTender business authority. |
| AUTH-AC-003 | A Departmental Author in OU-A and HoD in OU-B can author only in OU-A and decide only in OU-B. |
| AUTH-AC-004 | A PE-wide Planner assignment and an OU-scoped Author assignment coexist without narrowing or broadening each other. |
| AUTH-AC-005 | One parent-OU assignment covers descendants in the same PE and never crosses PE. |
| AUTH-AC-006 | Assignment to a leaf covers only that leaf and any actual descendants. |
| AUTH-AC-007 | Holding a role projection without a matching assignment grants no business read or command. |
| AUTH-AC-008 | The same resolver scopes lists, counts, detail, tasks, files, exports and commands. |
| AUTH-AC-009 | Tasks route work but do not authorize an unassigned actor. |
| AUTH-AC-010 | Financial Year is absent from User Responsibility Assignment and all per-user grant flows. |
| AUTH-AC-011 | One PE/OU assignment works across every Financial Year eligible under domain records and windows. |
| AUTH-AC-012 | Changing, clearing or corrupting a browser context does not change authority. |
| AUTH-AC-013 | A future or closed FY selection never prevents later work in another eligible year. |
| AUTH-AC-014 | Acting responsibility starts and ends at the configured instants without a new role label. |
| AUTH-AC-015 | Administrator and System Manager can inspect all data without business assignments but cannot make business decisions without one. |
| AUTH-AC-016 | The User responsibilities screen completes a normal grant or revocation without raw User Permission or seed-script work. |
| AUTH-AC-017 | Organisation Unit is the sole valid scope tree and every parent/child relationship remains inside one PE. |
| AUTH-AC-018 | `Procurement Department` and `kt_primary_department` supply no authority after cutover. |
| AUTH-AC-019 | Migration reports every ambiguous or scope-broadening case and creates no authority for it automatically. |
| AUTH-AC-020 | No production authorization read references the retired stores after cutover. |
| AUTH-AC-021 | A module cannot introduce an additional approval stage through the authorization mechanism. |
| AUTH-AC-022 | Decision audit identifies the exact responsibility assignment exercised. |
| AUTH-AC-023 | Configuration and Governance exposes Organisation structure and User responsibilities as ordinary registered KenTender pages. |
| AUTH-AC-024 | An administrator can add an Organisation Unit beneath the system-created PE root without creating an Organisation Unit Type or using a raw DocType form. |
| AUTH-AC-025 | The Organisation structure tree exposes names, stable codes, status and hierarchy without exposing nested-set internals. |
| AUTH-AC-026 | Reparent and physical delete are absent; deactivation preserves referenced history and fails with exact blockers. |
| AUTH-AC-027 | The assignment dialog shows PE and OU controls only when required by the selected registry responsibility. |
| AUTH-AC-028 | The assignment dialog never shows Financial Year, module, capability, User Permission or arbitrary-scope controls. |
| AUTH-AC-029 | The server preview and saved assignment produce the same exact user, responsibility, scope, descendants and effective period. |
| AUTH-AC-030 | Saving creates an Enabled assignment directly; Scheduled, Active and Expired are derived without an invented approval workflow. |
| AUTH-AC-031 | Active assignments cannot be edited; revoke-and-replace preserves the original assignment and audit history. |
| AUTH-AC-032 | Empty, missing-root, forbidden and server-failure states are visibly distinct and never appear as an empty successful register. |
| AUTH-AC-033 | The administration pages work without a remembered PE/FY browser context and provide visible, changeable filters. |
| AUTH-AC-034 | Direct routes, refresh, back/forward and return to Configuration and Governance preserve a valid page state. |
| AUTH-AC-035 | An administrator can complete the full structure → assign → verify → revoke journey without raw Frappe administration or seed scripts. |

## 17. Minimum test contract

1. Role-bound positive and negative tests for each scope type.
2. Same-user, different-role, different-OU Cartesian-product regression test.
3. Same-user PE-wide and OU-scoped responsibility regression test.
4. Parent, leaf, sibling and cross-PE OU-tree tests.
5. Current, future, expired and revoked assignment tests at boundary instants.
6. Exclusive-office overlap and acting-period tests.
7. Role-projection-without-assignment and assignment-with-missing-projection tests.
8. List/count/detail/task/file/export/command equivalence tests.
9. Direct-route and stale-browser-context tests.
10. Multi-FY test proving no annual user grant is required.
11. Open, scheduled and closed module-window tests.
12. Task-present/absent and task-without-assignment tests.
13. Maker-checker and evidence-chain segregation tests.
14. Administrator/System Manager read-all and business-mutation-denied tests.
15. Idempotent grant, revoke, role synchronization and migration tests.
16. Repository search proving retired authority stores and FY user grants are absent from production authorization reads.
17. Browser journey: create a departmental Need from one normal assignment without a pre-entry context hoop.
18. Administration journey: grant, inspect, act, revoke and verify immediate denial.
19. Organisation structure component and browser tests for root, child, rename, deactivate, missing-root and cross-PE denial.
20. Assignment-dialog component tests for Global, PE and OU field variants, descendant preview, Acting dates and validation copy.
21. Register/detail tests for filters, derived status, immutable history, diagnostics and revoke-and-replace.
22. UI state tests proving loading, empty, configuration failure, forbidden and server failure are distinct.
23. Route tests for menu entry, direct load, refresh, browser back/forward and return path.

Because this is shared authorization infrastructure, release requires focused tests, affected-module tests, cross-app contract tests and the full permission/UI gate. A happy-path module test alone is insufficient.

## 18. Prohibited shortcuts

- Do not keep both User Scope Assignment and User Responsibility Assignment active.
- Do not treat Frappe User Permission as a fallback.
- Do not pair independent Role and scope rows at runtime.
- Do not add Financial Year to an assignment.
- Do not store authoritative context in local storage, session defaults or a user profile.
- Do not add module-specific scope resolvers.
- Do not authorize from a task, queue, menu, route or UI button.
- Do not grant Administrator business roles in fixtures to bypass setup.
- Do not collapse PE and OU into one cross-tenant hierarchy.
- Do not broaden a user's OU to a parent during migration.
- Do not add an approval level while translating a role.
- Do not delete old records before cutover evidence is complete.

## 19. Implementation authority and next work

Approval of this document authorizes:

- the User Responsibility Assignment DocType and the complete Organisation structure and User responsibilities administration surfaces in section 12;
- the code-owned role registry;
- conversion of Organisation Unit to the authoritative PE-bounded nested set;
- the shared authorization resolver and permission-query integration;
- Frappe Role synchronization as a projection;
- retirement of Frappe User Permission, User Scope Assignment and the older custom capability stores as KenTender authority;
- removal of per-user Financial Year grants and authoritative browser context;
- the controlled migration and cross-module verification in sections 15–17; and
- full successor versions of affected module documents that reference this ADR rather than redefining authorization.

No production permission mechanism should be changed piecemeal before the assignment schema, resolver, migration report and focused tests are ready for one controlled cutover.
