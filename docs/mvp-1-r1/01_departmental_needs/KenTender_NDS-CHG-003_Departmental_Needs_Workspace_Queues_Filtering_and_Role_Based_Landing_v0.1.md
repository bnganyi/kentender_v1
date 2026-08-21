**CHANGE UNIT**

**NDS-CHG-003**

**Departmental Needs workspace, queues, filtering and role-based landing behaviour**

**Module:** Departmental Needs

**Status:** Proposed for approval

**Version:** 0.1

**Dependencies:** CFG-CHG-001; AUTH-CHG-001; NDS-CHG-001 v0.3; NDS-CHG-002 v0.2

**Documentation standard:** Integrated revision-ledger change unit

**Build posture:** Greenfield implementation; no legacy data migration

**Controlling decision:** The Departmental Needs workspace is a role-aware work surface over the approved Need lifecycle. It reveals only authorised records and valid next actions; it does not grant ownership, approval, funding or procurement authority.

# 1\. Decision and purpose

This change unit defines the canonical Departmental Needs landing page, context resolution, work queues, register, filtering, role-specific variants, read-only oversight and support access. It closes the workspace gap left deliberately open by NDS-CHG-001 and NDS-CHG-002.

It does not redesign the approved Need capture, correction, departmental-review or withdrawal-request screens. It does not change Need states, item fields, decision authority, planning usage or downstream boundaries.

**Completion standard:** Requirements, exact static screen designs, deterministic seed data, implementation controls, tests and acceptance criteria form one indivisible unit.

# 2\. Legal and procedural boundary

PPADA section 44 makes the Accounting Officer primarily responsible for the entity's compliance, including approved-budget and procurement-planning controls. Section 45 requires systematic, structured procedures and segregation of responsibilities. Regulations 34 and 40 allocate requirement initiation and departmental-plan responsibilities to the User Department and its head. Regulation 52 and regulation 71 place the formal Procurement Requisition later, through the procurement function and against the approved procurement plan.

The workspace is therefore a KenTender internal control that helps authorised actors find and process Departmental Needs. Queue placement is not a statutory decision, and a visible action is never sufficient authority. Every read and command remains subject to the approved role, assignment, maker-checker, state and scope controls.

**No legal substitution:** No workspace counter, queue, filter, badge or task assignment may be described as procurement approval, budget confirmation, authority to procure or tender initiation.

# 3\. Scope and exclusions

## 3.1 Included

- One canonical authenticated Desk route at /desk/departmental-needs.
- Role-aware landing variants for requester, departmental reviewer, Procurement Planner, read-only oversight and audited support.
- Effective Procuring Entity, organisational-unit and financial-year context resolution.
- Work requiring action, Waiting on others and scoped-register projections.
- Server-side search, filtering, sorting, counts and pagination.
- Loading, empty, no-scope, closed-intake, access-denied and service-error states.
- Deterministic seed contexts, assignments, records and expected counts.

## 3.2 Explicitly excluded

- A general Procurement Home dashboard or cross-module action centre.
- Need capture, item editing, review-decision or withdrawal-dialog redesign.
- Budget availability, funding reservation, commitment or Finance confirmation.
- Procurement classification, requirement type, method selection or tender preparation.
- BOQs, formal specifications, drawings, schedules of requirements or Terms of Reference.
- Procurement Requisition, Plan approval or Tender actions inside Departmental Needs.
- Charts, performance scoring, workload ranking or an advanced analytics dashboard.
- Any route, schema, query, label or compatibility behavior inherited from legacy Demands.

# 4\. Canonical workspace model

## 4.1 Workspace sections

| **Section**           | **Purpose**                                                                                     | **Rule**                                                                   |
| --------------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Context               | Shows the active PE, department and planning year.                                              | Selection filters authorised visibility; it never creates authority.       |
| Summary               | Shows compact counts for the active role and context.                                           | Counts use the same server-side scope predicate as the corresponding list. |
| Work requiring action | Shows records for which the current actor has a valid, immediate action.                        | No item appears merely because the actor has a similarly named role.       |
| Waiting on others     | Shows the actor's work currently assigned to another actor or blocked by a governed dependency. | Each row identifies stage and assignee or queue.                           |
| Needs register        | Shows the authorised record projection for the selected role and context.                       | Register access is read scope, not action authority.                       |

## 4.2 Canonical labels

| **Concept**           | **Allowed values or wording**                                                   |
| --------------------- | ------------------------------------------------------------------------------- |
| Need state            | Draft; Submitted; Returned; Accepted for planning; Not taken forward; Withdrawn |
| Planning usage        | Not included; Partially included; Fully included                                |
| Work section          | Work requiring action                                                           |
| Waiting section       | Waiting on others                                                               |
| Primary create action | Create need                                                                     |
| Requester actions     | Continue; Correct and resubmit; View                                            |
| Reviewer action       | Review                                                                          |
| Read-only action      | View                                                                            |

Do not use Approved for a Need, and do not show Passed, Failed, Qualified, Compliant or scores. Status and planning usage remain separate fields and must never be combined into one inferred state.

# 5\. Context resolution and saved workspace state

| **Rule ID** | **Normative rule**                                                                                                                                                                                            |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| NDS-FR-050  | Derive eligible contexts only from effective, time-bound PE, organisational-unit and FY assignments plus active configuration.                                                                                |
| NDS-FR-051  | Restore the actor's last saved context only if it remains authorised and configured; otherwise discard it without broadening scope.                                                                           |
| NDS-FR-052  | If exactly one context is eligible, select it and display it explicitly. If more than one is eligible, require deliberate selection before loading records.                                                   |
| NDS-FR-053  | If no context is eligible, show the no-scope state. Do not fall back to the current FY, any open PE, record ownership, Administrator status or the first database row.                                        |
| NDS-FR-054  | Changing context refreshes all counts and lists from the server and persists only a user preference, not an assignment.                                                                                       |
| NDS-FR-055  | Requester and departmental-review contexts include PE, organisational unit and FY. Planner and entity-oversight contexts include PE and FY with an optional department filter restricted to authorised units. |
| NDS-FR-056  | Creation requires an open Departmental Needs intake configuration for the selected PE/FY and effective requester assignment. Existing authorised records remain readable when intake is closed.               |
| NDS-FR-057  | Every record route rechecks the active assignment and record scope independently of the workspace context.                                                                                                    |

## 5.1 Context precedence

1. Validate session and user status.
2. Load effective capability assignments for the requested workspace projection.
3. Intersect assignments with active PE, department, FY and intake configuration.
4. Validate a requested or saved context against that intersection.
5. Resolve the single eligible context or require explicit selection.
6. Apply record-scope predicates before counts, rows or record identifiers are materialised.

# 6\. Role-based landing and visibility matrix

| **Actor**                    | **Default landing projection** | **Action queue**                                                | **Register scope**                        | **Primary action**                                |
| ---------------------------- | ------------------------------ | --------------------------------------------------------------- | ----------------------------------------- | ------------------------------------------------- |
| Departmental Need Requester  | My needs                       | Own Draft and Returned Needs                                    | Own Needs in context                      | Create need, if intake open                       |
| Head of User Department      | Department review              | Submitted Needs and withdrawal decisions in assigned department | Departmental Needs in context             | Create need only if separately assigned requester |
| Departmental Review Delegate | Department review              | Explicitly routed review work in delegated scope                | Delegated departmental scope              | No create unless separately assigned requester    |
| Procurement Planner          | Accepted for planning          | None in Departmental Needs                                      | Accepted Needs in assigned PE/FY          | No Departmental Needs mutation                    |
| Budget Officer               | Read-only overview             | None                                                            | Relevant assigned PE/FY                   | View                                              |
| Accounting Officer           | Read-only oversight            | None                                                            | Assigned PE/FY oversight                  | View                                              |
| System Administrator         | Support lookup                 | None                                                            | Audited neutral read after support reason | View only                                         |

**Combined roles:** Evaluate each capability independently, union only the records each capability may read, and expose an action only where one effective assignment authorises that exact command. Never replace scope with the broadest role.

# 7\. Queue semantics

## 7.1 Work requiring action

| **Queue item**     | **Eligible actor**         | **Inclusion rule**                                                       | **Action**           |
| ------------------ | -------------------------- | ------------------------------------------------------------------------ | -------------------- |
| Draft Need         | Creator                    | Owned Draft in selected context                                          | Continue             |
| Returned Need      | Creator                    | Owned Returned Need in selected context                                  | Correct and resubmit |
| Submitted Need     | HoUD or effective delegate | Open review work explicitly routed within scope; maker-checker satisfied | Review               |
| Withdrawal request | HoUD or effective delegate | Open decision work explicitly routed within scope; requester excluded    | Review               |

A planner's use of an accepted Need occurs in Procurement Planning and is not rendered as a Departmental Needs action task. Accepted Needs appear in the planner read projection only.

## 7.2 Waiting on others

| **Source**                       | **Waiting stage**     | **Visible to**                  | **Required display**                                            |
| -------------------------------- | --------------------- | ------------------------------- | --------------------------------------------------------------- |
| Submitted Need                   | Departmental review   | Creator                         | Status, submitted time and assigned reviewer or queue           |
| Accepted-Need withdrawal request | Departmental decision | Requester                       | Request status, dependency state and assigned reviewer or queue |
| Blocked withdrawal request       | Dependency clearance  | Requester and assigned reviewer | Blocking module and reference; no foreign-module action         |

## 7.3 Assignment and claim rules

- Submit creates one logical review work item addressed to the effective HoUD and eligible delegates in the same PE, department and FY.
- The response identifies whether the work is named, shared-queue or claimed; an unassigned task is never described as being 'with' a role.
- Claiming shared work is atomic, time-bound and audited. A second claimant receives a conflict and current assignee details.
- Assignment expiry, revocation or scope change removes action eligibility immediately and invokes configured reassignment or exception routing.
- Maker-checker exclusion is applied before routing and again when the decision command executes.
- Queue rows use stable work-item identifiers and deep links; status counts are not calculated from rendered rows.

# 8\. Register, search, filters and sorting

## 8.1 Register columns

| **Column**             | **Rule**                                                                                            |
| ---------------------- | --------------------------------------------------------------------------------------------------- |
| Need                   | Title on first line; canonical Need reference on second line.                                       |
| Indicative requirement | Human-readable aggregate such as 120 staff, 120 sets or 1 programme; no procurement classification. |
| Department             | Show for PE-wide roles; omit where the active context fixes one department.                         |
| Required by            | Display date in user locale; sort by canonical date.                                                |
| Status                 | Exact canonical Need state.                                                                         |
| Planning usage         | Exact separate planning-usage projection.                                                           |
| Updated                | User-timezone timestamp with accessible full date/time.                                             |
| Action                 | Continue, Correct and resubmit, Review or View according to current capability and state.           |

## 8.2 Filters

| **Filter**         | **Behavior**                                                                                                                |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| Search             | Case-insensitive title or exact/partial canonical reference; debounce client requests; search only inside authorised scope. |
| Status             | Multi-select canonical Need states.                                                                                         |
| Planning usage     | Not included, Partially included or Fully included.                                                                         |
| Department         | Only for PE-wide readers; options are limited to authorised departments.                                                    |
| Financial year     | Uses eligible contexts; changing it is a context change, not a record filter that bypasses context.                         |
| Required-by period | Inclusive from/to dates inside visible records.                                                                             |
| Submitted by       | Reviewer and oversight projections only; options resolved within current scope.                                             |

Default sort is action priority then oldest actionable timestamp for work queues; newest updated first for My needs and the register; required-by ascending for the planner projection. Users may choose only documented sorts. Server responses include sort keys, page size, total count and an opaque continuation cursor.

## 8.3 Query invariants

- Apply authorization predicates in the database query before count, aggregation, sorting or pagination.
- Use the identical scope predicate for summary counts, queue counts, register totals, export eligibility and row retrieval.
- Never accept client-supplied PE, department, FY, owner, role or work-item assignment as proof of access.
- Return Not found for an unauthorised record where revealing its existence would disclose protected metadata.
- Prevent timing, count and autocomplete side channels across PE or department boundaries.
- Use deterministic secondary sorting by canonical reference.

# 9\. Static screen specifications

**Stitch constraint:** NDS-UI-03A through NDS-UI-03F are exact static fixtures. Stitch renders only the stated visible content. Runtime loading, authorization, routing, assignment and mutation belong to implementation controls.

## 9.1 NDS-UI-03A — Requester landing

- Signed-in user: Grace Wanjiku | Role: Departmental Need Requester
- Browser route: /desk/departmental-needs
- Breadcrumb: Home > Departmental Needs
- Title: Departmental Needs
- Description: Capture and track the needs your department expects to include in procurement planning.
- Context: Procuring Entity: Ministry of Health | Department: Directorate of Digital Health and Policy | Planning year: 2027/28 | Change
- Primary action: Create need

| **My needs** | **Draft or returned** | **Awaiting review** | **Accepted for planning** |
| ------------ | --------------------- | ------------------- | ------------------------- |
| 6            | 2                     | 1                   | 1                         |

### Work requiring action

| **Need**                                                                 | **Required by**  | **Status** | **Action**           |
| ------------------------------------------------------------------------ | ---------------- | ---------- | -------------------- |
| Regional health-facility connectivity equipment <br>NDS-MOH-2027-0003    | 15 January 2028  | Returned   | Correct and resubmit |
| County laboratory information-system user licences <br>NDS-MOH-2027-0004 | 29 February 2028 | Draft      | Continue             |

### Waiting on others

| **Work item**                                                                     | **Stage**            | **Status**         | **With**                |
| --------------------------------------------------------------------------------- | -------------------- | ------------------ | ----------------------- |
| Digital health technical staff certification programme <br>NDS-MOH-2027-0002      | Departmental review  | Submitted          | Department review queue |
| Withdraw National digital health infrastructure upgrade <br>NDS-WDR-MOH-2027-0001 | Dependency clearance | Awaiting clearance | Approved Plan amendment |

Below these sections, show My needs using the canonical register columns and all six seeded Needs. Do not show other requesters' records, Finance controls, procurement classifications, Plan actions or charts.

## 9.2 NDS-UI-03B — Head of User Department landing

- Signed-in user: Dr Peter Kimani | Role: Head of User Department
- Browser route: /desk/departmental-needs
- Title and description: same as NDS-UI-03A
- Context: Ministry of Health | Directorate of Digital Health and Policy | Planning year 2027/28 | Change
- Primary action: none, unless the user also has an effective requester assignment

| **Department needs** | **Awaiting review** | **Accepted for planning** | **Open withdrawal requests** |
| -------------------- | ------------------- | ------------------------- | ---------------------------- |
| 6                    | 1                   | 1                         | 1                            |

### Work requiring action

| **Work item**                                                                     | **Stage**           | **Status**                    | **Action** |
| --------------------------------------------------------------------------------- | ------------------- | ----------------------------- | ---------- |
| Digital health technical staff certification programme <br>NDS-MOH-2027-0002      | Departmental review | Submitted                     | Review     |
| Withdraw National digital health infrastructure upgrade <br>NDS-WDR-MOH-2027-0001 | Withdrawal decision | Awaiting dependency clearance | Review     |

Show the Department needs register with all six seeded records. NDS-WDR-MOH-2027-0001 remains reviewable even though approval is disabled by its approved-Plan dependency. Do not show an Approve shortcut in the queue.

## 9.3 NDS-UI-03C — Departmental Review Delegate landing

- Signed-in user: Julia Njeri | Role: Departmental Review Delegate
- Context: Ministry of Health | Directorate of Digital Health and Policy | Planning year 2027/28
- Summary: Assigned review work: 2 | Submitted Needs: 1 | Withdrawal requests: 1
- Work requiring action: the same two routed work items as NDS-UI-03B
- Register: only records within Julia Njeri's effective delegated scope
- Primary action: none

This variant proves that delegation is explicit and scoped. Do not infer all-department access from the role label, and do not expose work outside the delegation period.

## 9.4 NDS-UI-03D — Procurement Planner landing

- Signed-in user: Mercy Kilonzo | Role: Procurement Planner
- Context: Procuring Entity: Ministry of Health | Planning year: 2027/28 | Department: All authorised departments | Change
- Title: Departmental Needs
- Description: View accepted departmental needs available to procurement planning.
- Primary action: none

| **Accepted for planning** | **Not included** | **Partially included** | **Fully included** |
| ------------------------- | ---------------- | ---------------------- | ------------------ |
| 1                         | 0                | 0                      | 1                  |

### Accepted needs for planning

| **Need**                                                             | **Department**            | **Indicative requirement** | **Required by** | **Planning usage** | **Action** |
| -------------------------------------------------------------------- | ------------------------- | -------------------------- | --------------- | ------------------ | ---------- |
| National digital health infrastructure upgrade <br>NDS-MOH-2027-0001 | Digital Health and Policy | 1 programme                | 31 August 2027  | Fully included     | View       |

Do not show Draft, Submitted, Returned, Not taken forward or Withdrawn Needs to the planner by virtue of the planner role. Do not show edit, accept, return, funding or direct allocation actions in this workspace.

## 9.5 NDS-UI-03E — Read-only oversight landing

- Signed-in user: Peter Otieno | Role: Budget Officer
- Context: Procuring Entity: Ministry of Health | Planning year: 2027/28 | Department: All authorised departments | Change
- Title: Departmental Needs
- Description: Read-only view of departmental needs in your assigned scope.
- Banner: Read-only view. Departmental Needs has no Finance confirmation or funding action.
- Primary action: none

| **Scoped needs** | **Submitted** | **Accepted for planning** | **Closed** |
| ---------------- | ------------- | ------------------------- | ---------- |
| 6                | 1             | 1                         | 2          |

Show the scoped Needs register with View as the only action. The Accounting Officer uses the same neutral pattern with role-appropriate wording. Do not show Work requiring action, approval, confirmation or escalation controls.

## 9.6 NDS-UI-03F — System Administrator support lookup

- Signed-in user: System Administrator | Role: System Administrator
- Initial state: no business records loaded
- Heading: Departmental Needs support access
- Explanation: Administrator status does not grant operational authority. Enter a support reason and select an authorised support scope to inspect records read-only.
- Required controls: Support reason | Procuring Entity | Financial year | Open read-only support view
- After access: persistent Audited support view banner, selected scope, expiry time and View-only register

Do not show Create, Continue, Correct and resubmit, Review, Accept, Return, Withdraw, Finance or Planning actions. Every support lookup, search and record open is separately audited.

# 10\. Non-happy states

| **State**           | **Exact user-facing content**                                                                            | **Controls**                            |
| ------------------- | -------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| No eligible context | No Departmental Needs scope is assigned to your account. Contact your Procuring Entity administrator.    | No record data; Retry                   |
| Multiple contexts   | Select a Procuring Entity, department and planning year to continue.                                     | Scoped selectors; Continue              |
| Closed intake       | The Departmental Needs intake window for 2027/28 is closed. Existing records remain available read-only. | No Create need; authorised View actions |
| No actionable work  | No Departmental Needs work currently requires your action.                                               | Register remains available              |
| No waiting work     | Nothing is currently waiting on another reviewer or dependency.                                          | No placeholder rows                     |
| No register results | No Departmental Needs match the selected filters.                                                        | Clear filters                           |
| Access denied       | You do not have access to this Departmental Needs view.                                                  | Return to Departmental Needs            |
| Service unavailable | Departmental Needs could not be loaded. No changes were made.                                            | Retry                                   |

Loading placeholders must preserve the final page structure, announce progress to assistive technology and never display stale records from the previous context. An error in one projection must not silently replace it with an empty-state message.

# 11\. API and projection contract

## 11.1 Authenticated queries

| **Query**                       | **Purpose**                                                  | **Mandatory controls**                                         |
| ------------------------------- | ------------------------------------------------------------ | -------------------------------------------------------------- |
| GetDepartmentalNeedsContexts    | Eligible PE/department/FY contexts and intake state          | Session, effective assignments, active configuration           |
| GetDepartmentalNeedsWorkspace   | Resolved context, role variant, summaries and queue previews | Server resolution, shared scope predicate, capped preview      |
| ListDepartmentalNeedsWork       | Paged action or waiting work                                 | Assignment, capability, state, maker-checker, cursor           |
| ListDepartmentalNeeds           | Paged register projection                                    | Read scope, filters, sort allowlist, cursor                    |
| OpenDepartmentalNeedSupportView | Time-limited audited neutral support projection              | Administrator, support profile, reason, selected scope, expiry |

Frappe methods used by the authenticated Desk page must be explicitly whitelisted for authenticated calls and must enforce authorization inside the service. A missing whitelist, guest-only method, route mismatch or client call to an internal function is an implementation defect; it must not surface as Method Not Allowed to an authorised user.

## 11.2 Response invariants

- Return canonical IDs and display values separately; display labels are never query keys.
- Return role_variant, resolved_context, context_options, permissions, summaries, queue previews and register metadata from one consistent projection version.
- Include server_time_utc and projection_version so the client can reject stale cross-context responses.
- Do not return hidden actions, inaccessible row counts, forbidden filter options or foreign-scope autocomplete values.
- Use stable business error codes for no_scope, context_required, intake_closed, forbidden, not_found, stale_context and service_unavailable.
- Cache only per user, capability set and resolved context; invalidate on assignment, configuration, state, routing or planning-usage changes.

## 11.3 Accessibility and usability

- All status, planning-usage and queue meanings are expressed in text; color is supplementary.
- Context changes and queue refreshes announce completion and result counts without moving keyboard focus unexpectedly.
- Tables have real headers, logical reading order and keyboard-accessible row actions.
- Long Need titles wrap; references remain copyable; truncation exposes the full accessible name.
- Empty and error states use text plus iconography and retain a recovery control where recovery is possible.

# 12\. Security, privacy and audit controls

- Authenticate every workspace and query request; do not allow guest access.
- Authorize at PE, organisational unit, FY, capability, assignment period, record state and work-assignment level.
- Enforce row-level predicates before database aggregation or materialisation.
- Record context changes, work claims, support-view creation, support searches and support record opens in immutable audit events.
- Never log business justification, attachment contents or search terms containing protected information in application error logs.
- Rate-limit search, support lookup and repeated denied record probes without blocking ordinary paging.
- End a support view on expiry, logout, role change or scope revocation and clear cached rows immediately.
- No System Administrator, Budget Officer, Accounting Officer or Procurement Planner action is inferred from neutral read visibility.

# 13\. Deterministic seed contract

## 13.1 Configuration contexts

| **Context**                                              | **Configuration**                                        | **Purpose**                             |
| -------------------------------------------------------- | -------------------------------------------------------- | --------------------------------------- |
| MOH / Directorate of Digital Health and Policy / 2027/28 | FY 1 Jul 2027–30 Jun 2028; intake open 1 Apr–30 Jun 2027 | Positive requester and reviewer context |
| MOH / 2027/28 / all authorised departments               | Active entity view                                       | Planner and read-only oversight context |
| NSSF / 2027/28                                           | Active but not assigned to MOH personas                  | Cross-PE denial and filter-option test  |

These are fresh CFG-owned configuration fixtures referenced by Departmental Needs. This unit must not synthesize a PE, financial year or intake window from transaction data.

## 13.2 Personas and assignments

| **Principal**                         | **Role / assignment**                                                  | **Expected landing** |
| ------------------------------------- | ---------------------------------------------------------------------- | -------------------- |
| <grace.wanjiku@moh.example.test>      | Departmental Need Requester; MOH / Digital Health and Policy / 2027/28 | NDS-UI-03A           |
| <peter.kimani@moh.example.test>       | Head of User Department; same scope                                    | NDS-UI-03B           |
| <julia.njeri@moh.example.test>        | Departmental Review Delegate; same scope and effective period          | NDS-UI-03C           |
| <mercy.kilonzo@moh.example.test>      | Procurement Planner; MOH / 2027/28                                     | NDS-UI-03D           |
| <moh.budget.officer@example.test>     | Peter Otieno; Budget Officer read-only; MOH / 2027/28                  | NDS-UI-03E           |
| <amina.hassan@moh.example.test>       | Accounting Officer read-only oversight; MOH                            | NDS-UI-03E pattern   |
| <kentender.system.admin@example.test> | System Administrator; no operational assignment; support profile       | NDS-UI-03F           |

## 13.3 Need and work fixtures

| **Reference**         | **Title**                                              | **State**                     | **Planning usage / work**                          |
| --------------------- | ------------------------------------------------------ | ----------------------------- | -------------------------------------------------- |
| NDS-MOH-2027-0001     | National digital health infrastructure upgrade         | Accepted for planning         | Fully included; pending blocked withdrawal request |
| NDS-MOH-2027-0002     | Digital health technical staff certification programme | Submitted                     | Not included; departmental review queue            |
| NDS-MOH-2027-0003     | Regional health-facility connectivity equipment        | Returned                      | Not included; requester correction                 |
| NDS-MOH-2027-0004     | County laboratory information-system user licences     | Draft                         | Not included; requester continuation               |
| NDS-MOH-2027-0005     | Replacement of recently supplied network switches      | Not taken forward             | Not included                                       |
| NDS-MOH-2027-0006     | Temporary document digitisation support                | Withdrawn                     | Not included                                       |
| NDS-WDR-MOH-2027-0001 | Withdraw NDS-MOH-2027-0001                             | Awaiting dependency clearance | Blocking Approved Plan PLN-MOH-2027-001 Version 1  |

Use fixed UTC timestamps that render the dates and East Africa Time values defined in NDS-CHG-002. Create no Procurement Requisition, Tender, legacy Demand record or additional synthetic Need.

# 14\. Greenfield implementation work plan

**Mandatory:** Implement the workspace against the fresh Departmental Needs and shared authorization/configuration contracts only. There is no migration, compatibility, fallback or seed-repair work.

1. Register only the departmental-needs Frappe Desk page and /desk/departmental-needs browser route.
2. Implement one server projection layer shared by summaries, queues, registers and deep-link authorization.
3. Implement explicit authenticated whitelisted query methods and keep command methods separate.
4. Create database indexes for PE, department, target FY, creator, state, planning usage, updated time and open work assignment.
5. Implement context resolution using CFG-owned PE/FY/intake records and AUTH-owned effective assignments.
6. Implement requester, reviewer, delegate, planner, read-only oversight and support projections without a legacy-role switch statement.
7. Implement work-item assignment, claim, reassign, expiry and maker-checker tests through the shared assignment service.
8. Seed the exact configuration references, personas, assignments, Needs and withdrawal request in section 13.
9. Remove any imports, queries, routes, fixtures, dashboards or Home widgets that reference the retired Demands module.
10. Do not rebuild Procurement Home as part of this unit; Departmental Needs must operate independently of Home.

## 14.1 Prohibited implementation

- No legacy Demand model, table, field, route, service, permission, status, test or fixture.
- No /demands, /departmental-needs or /app/departmental-needs route and no redirect from them.
- No generic Administrator bypass, first-PE fallback, current-FY fallback or client-side-only authorization.
- No workspace-owned copy of PE, FY, department, role, assignment or intake configuration.
- No counts from unscoped tables, post-query filtering, hidden unauthorized rows or cached cross-context responses.
- No separate queue truth, duplicated lifecycle state or action inferred from a display label.

# 15\. Acceptance criteria

| **ID**     | **Acceptance criterion**                                                                                                                      |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| NDS-AC-050 | The only canonical browser route is /desk/departmental-needs and it loads through an authenticated, explicitly whitelisted server contract.   |
| NDS-AC-051 | A valid single context resolves explicitly; multiple contexts require selection; no context shows the no-scope state.                         |
| NDS-AC-052 | A saved context is restored only while still authorised and configured.                                                                       |
| NDS-AC-053 | Changing context refreshes all projections and never grants new record or action authority.                                                   |
| NDS-AC-054 | Summary counts, queues and register totals use the same server-side scope predicate.                                                          |
| NDS-AC-055 | Grace Wanjiku sees exactly the requester counts and queue rows in NDS-UI-03A and no other requester's Needs.                                  |
| NDS-AC-056 | Dr Peter Kimani sees exactly the review work and departmental counts in NDS-UI-03B, subject to maker-checker.                                 |
| NDS-AC-057 | Julia Njeri sees review work only while her exact delegation is effective.                                                                    |
| NDS-AC-058 | Mercy Kilonzo sees only accepted Needs in her planner projection and has no source-Need mutation action.                                      |
| NDS-AC-059 | Budget Officer and Accounting Officer receive scoped read-only views with no confirmation or approval action.                                 |
| NDS-AC-060 | System Administrator initially sees no business data and must establish an audited, expiring support view with a reason.                      |
| NDS-AC-061 | Requester, reviewer, planner, oversight and support variants never infer authority from role name alone.                                      |
| NDS-AC-062 | Submitted work identifies an actual named assignee or shared queue; no row says only 'with Budget Officer', 'with HoUD' or another role.      |
| NDS-AC-063 | Claiming or reassigning work is atomic, audited and maker-checker safe.                                                                       |
| NDS-AC-064 | Search, filters, autocomplete, counts and pagination disclose nothing outside authorised scope.                                               |
| NDS-AC-065 | Status and planning usage remain distinct canonical values in every projection.                                                               |
| NDS-AC-066 | Closed intake removes Create need and submission authority without hiding existing authorised records.                                        |
| NDS-AC-067 | Loading, no-work, no-results, no-scope, access-denied and service-error states render the exact recovery semantics in section 10.             |
| NDS-AC-068 | No screen shows requirement type, procurement method, formal specification, funding confirmation, Procurement Requisition or Tender controls. |
| NDS-AC-069 | The fresh build boots from section 13 only and contains no legacy Demand import, schema, route, compatibility layer or fallback.              |
| NDS-AC-070 | Direct record and work-item URLs enforce the same scope and assignment checks as the workspace.                                               |
| NDS-AC-071 | All role variants and error states meet keyboard, screen-reader, text-label and focus-management requirements.                                |

# 16\. Verification scenarios

| **Scenario**                                         | **Expected result**                                                                                          |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Requester opens the workspace                        | NDS-UI-03A; two action rows, two waiting rows and six own Needs.                                             |
| HoUD opens the workspace                             | NDS-UI-03B; one Submitted review and one blocked withdrawal review.                                          |
| Delegate assignment expires                          | Review rows disappear on next request; direct review URL is denied.                                          |
| Planner opens the workspace                          | NDS-UI-03D; only NDS-MOH-2027-0001 is visible and View is the only row action.                               |
| Budget Officer opens the workspace                   | NDS-UI-03E; read-only register, no action queue and no Finance control.                                      |
| System Administrator opens the workspace             | NDS-UI-03F initial state; no business rows before support reason and scope.                                  |
| Administrator support view expires                   | Rows and cached results are cleared; subsequent reads require a new reasoned support view.                   |
| User selects NSSF context without assignment         | Context rejected; no NSSF counts, filter options, references or row existence disclosed.                     |
| Requester repeats a slow search after context change | Stale prior-context response is discarded using projection version.                                          |
| User opens /departmental-needs                       | No route exists; no redirect or compatibility response.                                                      |
| Authenticated page calls workspace query             | Method is whitelisted, session-authenticated and returns the scoped response rather than Method Not Allowed. |
| Intake window closes                                 | Existing authorised records remain readable; Create need and submit are unavailable with explanatory text.   |
| Queue and register are counted concurrently          | Counts and rows are consistent for the same projection version.                                              |
| Fresh site is installed and seeded                   | All section 13 fixtures load without any legacy module, data or repair script.                               |

# 17\. Traceability and release gate

| **Control source**         | **This unit's implementation consequence**                                                                                                                                   |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PPADA sections 44–45       | Preserve Accounting Officer accountability, systematic procedures, approved-budget boundaries and segregation; do not convert neutral visibility into routine Need approval. |
| PPADA section 53           | Keep Needs as planning inputs; no procurement proceeding or funding effect.                                                                                                  |
| PPAD Regulations 34 and 40 | Route initiation and departmental review through configured User Department responsibilities.                                                                                |
| PPAD Regulations 52 and 71 | Keep the formal Procurement Requisition later and outside this workspace.                                                                                                    |
| CFG-CHG-001                | Consume governed PE/FY/intake configuration; never synthesize it from transactions.                                                                                          |
| AUTH-CHG-001               | Use effective scoped assignments, explicit task routing and audited support visibility.                                                                                      |
| NDS-CHG-001                | Preserve module boundary, lifecycle, role authority and planning-usage separation.                                                                                           |
| NDS-CHG-002                | Preserve capture fields, command rules, exact six Needs and withdrawal fixture.                                                                                              |

**Release gate:** NDS-CHG-003 may be implemented only after product approval of the complete unit. Departmental Needs is not complete for MVP-1 until sections 14–16 pass in a fresh environment.

# 18\. Approval record

| **Role**                             | **Name** | **Decision**           | **Date** |
| ------------------------------------ | -------- | ---------------------- | -------- |
| Product owner                        |          | Pending                |          |
| Procurement legal / compliance owner |          | Pending                |          |
| Implementation owner                 |          | Acknowledged / pending |          |
| QA owner                             |          | Acknowledged / pending |          |

# 19\. Authoritative sources

**Public Procurement and Asset Disposal Act, 2015 (Kenya Law):** [official consolidated text](https://new.kenyalaw.org/akn/ke/act/2015/33/eng@2022-12-31)

**Public Procurement and Asset Disposal Regulations, 2020 (Kenya Law):** [official consolidated text](https://new.kenyalaw.org/akn/ke/act/ln/2020/69/eng@2022-12-31)

_Legal references establish system-control boundaries and do not replace entity-specific legal advice, current PPRA instruments, approved delegations or release-time legal review._