**CHANGE UNIT**

**NDS-CHG-002**

**Departmental Need capture, items and submission**

**Module:** Departmental Needs

**Status:** Proposed for approval

**Version:** 0.1

**Dependency:** Approved NDS-CHG-001 v0.2

**Documentation standard:** Integrated revision-ledger change unit

**Build posture:** Greenfield implementation; no legacy data migration

**Controlling decision:** Ordinary departmental users capture a simple, plain-language planning input. Procurement classifications, formal specifications and statutory requisition controls are deliberately deferred to the later Procurement Requisition module.

# 1\. Purpose and scope

This change unit defines how a Departmental Need is created, saved, edited, submitted and reviewed. It governs the Need header, simple item lines, supporting documents, validation, state transitions, permissions, audit controls, exact static screen specifications, clean-build implementation and deterministic seed data.

It does not define Procurement Planning allocation, Procurement Requisition preparation, budget confirmation, procurement-method selection or tender preparation.

# 2\. Legal and procedural boundary

The User Department initiates requirements and prepares its departmental procurement plan under regulations 34 and 40. The formal electronic procurement requisition under regulation 52 occurs later, after an approved Plan Item is available. Departmental Needs is therefore an internal planning aid, not a prescribed requisition form or authority to procure.

**No legal substitution:** Accepting or submitting a Departmental Need does not replace departmental procurement planning, financial-year budget controls, a Procurement Requisition, Accounting Officer authority or any tender-stage approval.

# 3\. Canonical data model

## 3.1 DepartmentalNeed

| **Field**                 | **Type and rule**                                                                                             |
| ------------------------- | ------------------------------------------------------------------------------------------------------------- |
| need_id                   | Immutable UUID; internal primary key.                                                                         |
| need_reference            | Generated after the first successful save: NDS-{PE code}-{FY start}-{4-digit sequence}; immutable and unique. |
| pe_id                     | Required; fixed from effective assignment or explicit scoped selection.                                       |
| org_unit_id               | Required; the owning User Department or organisational unit.                                                  |
| target_fy_id              | Required; enabled intake year, including a future year where the intake window is open.                       |
| submitter_user_id         | Required; immutable creator identity.                                                                         |
| title                     | Required for first save; 5–160 Unicode characters after trimming.                                             |
| business_justification    | Required for submission; 50–2,000 Unicode characters after trimming.                                          |
| required_by_date          | Required for submission; must fall within the target financial year.                                          |
| delivery_use_location     | Required for submission; 2–300 Unicode characters after trimming.                                             |
| indicative_total_estimate | Optional positive decimal; maximum two fractional digits; not a budget commitment.                            |
| currency_code             | KES; fixed and not editable in MVP-1.                                                                         |
| status                    | Draft, Submitted, Returned, Accepted for planning, Not taken forward or Withdrawn.                            |
| revision_no               | Starts at 1 on first submission; increments on each resubmission.                                             |
| record_version            | Monotonic optimistic-concurrency token.                                                                       |
| created_at / updated_at   | Server timestamps in UTC; display in the user's configured timezone.                                          |

## 3.2 DepartmentalNeedItem

| **Field**             | **Type and rule**                                                                                      |
| --------------------- | ------------------------------------------------------------------------------------------------------ |
| need_item_id          | Immutable UUID.                                                                                        |
| need_id               | Required foreign key to DepartmentalNeed.                                                              |
| line_no               | Positive integer; unique within the Need; displayed in ascending order.                                |
| narrative_description | Required for a complete line; 5–1,000 Unicode characters after trimming.                               |
| indicative_quantity   | Required for a complete line; decimal greater than zero; up to three fractional digits.                |
| unit_code             | Required; one controlled unit: Each, Set, Lot, Person, Staff, Month, Day, Service, Programme or Other. |
| other_unit            | Required only when unit_code is Other; 2–50 Unicode characters.                                        |

## 3.3 Supporting documents

- Attachments are optional. A Need may contain no more than 10 active files; each file is limited to 20 MB.
- Permitted file types are PDF, DOCX, XLSX, PNG and JPG/JPEG. Extension, MIME type and file signature must agree.
- Each upload is assigned an immutable identifier and records the original filename, size, MIME type, SHA-256 digest, uploader and timestamps.
- Files remain quarantined until malware scanning succeeds. A quarantined, failed or unscanned file blocks submission but not draft save.
- Deleting a draft attachment is a logical removal recorded in the audit trail; submitted snapshots retain their attachment references.

# 4\. Functional requirements

| **ID**     | **Requirement**               | **Normative rule**                                                                                                                                           |
| ---------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| NDS-FR-020 | Create within effective scope | A requester may create a Need only for an effective PE and organisational-unit assignment and an enabled needs-intake financial year.                        |
| NDS-FR-021 | Resolve context               | One effective assignment is fixed automatically; multiple assignments require explicit selection; no assignment blocks creation.                             |
| NDS-FR-022 | Generate reference            | The service generates the canonical reference only after the first successful save and never reuses a committed sequence.                                    |
| NDS-FR-023 | Save an incomplete draft      | A requester may save a partial Draft after context and title are valid. Submission-only fields may remain incomplete.                                        |
| NDS-FR-024 | Capture simple items          | A Need contains one or more plain-language item lines with description, indicative quantity and unit; procurement classification is not captured.            |
| NDS-FR-025 | Edit only owned work          | Only the creator may edit their own Draft or Returned Need within the same effective assignment.                                                             |
| NDS-FR-026 | Validate submission           | Submission requires all header fields, at least one complete item, no incomplete item row, a valid date, a positive optional estimate and clean attachments. |
| NDS-FR-027 | Recheck authority             | The submit command rechecks assignment, intake window and current state on the server; UI visibility is not authorization.                                   |
| NDS-FR-028 | Create a submission snapshot  | Submission atomically records an immutable header, item and attachment snapshot and changes status to Submitted.                                             |
| NDS-FR-029 | Lock submitted content        | A Submitted Need is read-only to the requester until returned.                                                                                               |
| NDS-FR-030 | Route departmental review     | Submission creates review work for the effective HoUD and eligible departmental delegates for the same PE, department and target FY.                         |
| NDS-FR-031 | Enforce maker-checker         | The submitting user cannot decide their own Need. If the HoUD submitted it, an effective delegate or alternate reviewer must decide.                         |
| NDS-FR-032 | Return for correction         | Return requires a 20–1,000 character reason, creates an immutable review event, changes status to Returned and unlocks the requester.                        |
| NDS-FR-033 | Resubmit                      | A Returned Need may be edited and resubmitted; revision_no increments and the previous snapshot remains immutable.                                           |
| NDS-FR-034 | Accept for planning           | Acceptance records a reviewer decision and immutable accepted snapshot; it creates no Plan Item or financial effect.                                         |
| NDS-FR-035 | Do not take forward           | The reviewer may decline a Submitted Need with a mandatory 20–1,000 character reason; the result is terminal.                                                |
| NDS-FR-036 | Withdraw before review        | The requester may withdraw a Draft or Returned Need. A Submitted Need must first be returned.                                                                |
| NDS-FR-037 | Notify participants           | Successful submit, return, acceptance and decline commands create durable in-app notification events after commit.                                           |
| NDS-FR-038 | Protect attachments           | Only clean active attachments are exposed to authorized users or included in a snapshot.                                                                     |
| NDS-FR-039 | Audit commands                | Create, update, submit, return, accept, decline, withdraw and attachment actions record actor, assignment, scope, time, reason and before/after state.       |
| NDS-FR-040 | Prevent duplicate effects     | All state-changing commands are atomic and idempotent under a client request identifier.                                                                     |
| NDS-FR-041 | Detect stale edits            | A command with a stale record_version fails with a conflict and does not overwrite later data.                                                               |
| NDS-FR-042 | Preserve downstream boundary  | No action in this unit creates a planning allocation, Procurement Requisition, Tender or budget reservation.                                                 |

# 5\. Submission validation contract

| **Validation**                         | **Draft save**                    | **Submit / resubmit**                           |
| -------------------------------------- | --------------------------------- | ----------------------------------------------- |
| Effective PE, department and target FY | Required                          | Required and revalidated                        |
| Title                                  | Required                          | Required                                        |
| Business justification                 | May be incomplete                 | 50–2,000 characters                             |
| Items                                  | May be absent or incomplete       | At least one complete line; no incomplete lines |
| Required-by date                       | May be absent                     | Required and inside target FY                   |
| Delivery or use location               | May be absent                     | Required                                        |
| Indicative estimate                    | Optional                          | If present, positive and two decimals maximum   |
| Attachments                            | May be scanning                   | All active files must be clean                  |
| Intake window                          | Must permit draft creation/update | Must permit submission                          |
| record_version                         | Must match                        | Must match                                      |

Validation failures return stable field or business-rule codes and do not change state, increment the revision number, dispatch work or send a notification.

# 6\. Roles and command authority

| **Actor**                    | **Read**                      | **Create / edit**           | **Submit**                 | **Review decision**        |
| ---------------------------- | ----------------------------- | --------------------------- | -------------------------- | -------------------------- |
| Departmental Need Requester  | Own Needs                     | Own Draft / Returned        | Own Draft / Returned       | No                         |
| Head of User Department      | Departmental scope            | Own Needs if also requester | Own Need if also requester | Yes, except own submission |
| Departmental Review Delegate | Assigned departmental scope   | Own Needs if also requester | Own Need if also requester | Yes, except own submission |
| Procurement Planner          | Accepted Needs in assigned PE | No                          | No                         | No                         |
| Budget Officer               | Relevant scoped read-only     | No                          | No                         | No                         |
| Accounting Officer           | Scoped oversight read-only    | No                          | No                         | No                         |
| System Administrator         | Audited support read-only     | No                          | No                         | No                         |

**Assignment rule:** A role label alone grants nothing. Every operational command requires an effective, time-bound PE and organisational-unit assignment covering the target record.

# 7\. Static Stitch screen specifications

**Stitch constraint:** The following are exact static screen fixtures. Stitch must render only the stated visible content and must not invent saving, validation, loading, routing, permissions or state-transition behavior.

## 7.1 NDS-UI-02A — Create Departmental Need

### Signed-in context

| **Field**        | **Exact visible value**                  |
| ---------------- | ---------------------------------------- |
| Signed-in user   | Grace Wanjiku                            |
| Role             | Departmental Need Requester              |
| Procuring Entity | Ministry of Health                       |
| Department       | Directorate of Digital Health and Policy |

### Header and context

- Breadcrumb: Home > Departmental Needs > Create need
- Title: Create departmental need
- Description: Describe what your department expects to require for the selected planning year.
- Context strip: Procuring Entity: Ministry of Health | Department: Directorate of Digital Health and Policy | Planning year: 2027/28 | Change

### Visible form content

| **Section / control**           | **Exact label or value**                                                                                                                   |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Need summary                    | Section heading                                                                                                                            |
| Need title                      | Digital health technical staff certification programme                                                                                     |
| Business justification          | Build internal capability to operate and support the Ministry's national digital-health platforms and reduce reliance on external support. |
| Items needed                    | Section heading                                                                                                                            |
| Item table columns              | Line \| Description \| Indicative quantity \| Unit \| Action                                                                               |
| Item row 1                      | 1 \| Professional certification training for digital health technical personnel \| 120 \| Staff \| Remove                                  |
| Item action                     | Add item                                                                                                                                   |
| Item helper                     | Use plain language. Detailed procurement specifications will be prepared later if the need is included in the approved Plan.               |
| Timing and location             | Section heading                                                                                                                            |
| Required by                     | 31 October 2027                                                                                                                            |
| Delivery or use location        | Ministry of Health headquarters and designated training centres                                                                            |
| Indicative cost                 | Section heading                                                                                                                            |
| Estimated total cost (optional) | KES 80,000,000.00                                                                                                                          |
| Supporting documents            | Section heading                                                                                                                            |
| Attachment                      | Digital-health-training-needs-assessment.pdf \| 1.8 MB                                                                                     |
| Footer actions                  | Cancel \| Save draft \| Submit for departmental review                                                                                     |

### Explicit exclusions

Do not show a Need reference before first save, requirement type, procurement category, procurement method, budget code, funding confirmation, unit price, BOQ, formal specification, Terms of Reference, approval route, Plan reference, Requisition reference, Tender reference or progress stepper.

## 7.2 NDS-UI-02B — Returned Need correction

- Signed-in user: Grace Wanjiku | Role: Departmental Need Requester
- Breadcrumb: Home > Departmental Needs > NDS-MOH-2027-0003
- Title: Regional health-facility connectivity equipment
- Context: Ministry of Health | Directorate of Digital Health and Policy | Planning year 2027/28
- Status: Returned

### Return notice

| **Visible element** | **Exact content**                                                                                                |
| ------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Heading             | Returned for correction                                                                                          |
| Reason              | Clarify whether the 120 sets cover all regional referral facilities and attach the facilities distribution list. |
| Audit line          | Returned by Dr Peter Kimani on 14 May 2027 at 10:35                                                              |

### Editable content

| **Control**                     | **Exact visible value**                                                                                               |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Business justification          | Provide reliable connectivity equipment for regional referral facilities supporting national digital-health services. |
| Item description                | Managed connectivity equipment set for a regional referral facility                                                   |
| Indicative quantity             | 120                                                                                                                   |
| Unit                            | Set                                                                                                                   |
| Required by                     | 15 January 2028                                                                                                       |
| Delivery or use location        | Regional referral facilities                                                                                          |
| Estimated total cost (optional) | KES 24,000,000.00                                                                                                     |
| Attachment                      | Regional-facilities-distribution-list.xlsx \| 42 KB                                                                   |
| Footer actions                  | Withdraw need \| Save changes \| Resubmit for departmental review                                                     |

Keep the same explicit exclusions as NDS-UI-02A. Do not add a workflow history panel, procurement controls or an approval stepper.

## 7.3 NDS-UI-02C — Departmental review

- Signed-in user: Dr Peter Kimani | Role: Head of User Department
- Breadcrumb: Home > Departmental Needs > Review > NDS-MOH-2027-0002
- Title: Review departmental need
- Context: Ministry of Health | Directorate of Digital Health and Policy | Planning year 2027/28
- Status: Submitted
- Submitted by: Grace Wanjiku | Submitted: 12 May 2027 at 14:20 | Revision: 1

### Read-only Need content

| **Visible element**      | **Exact content**                                                                                                                          |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Need title               | Digital health technical staff certification programme                                                                                     |
| Business justification   | Build internal capability to operate and support the Ministry's national digital-health platforms and reduce reliance on external support. |
| Item                     | Professional certification training for digital health technical personnel \| 120 \| Staff                                                 |
| Required by              | 31 October 2027                                                                                                                            |
| Delivery or use location | Ministry of Health headquarters and designated training centres                                                                            |
| Indicative total cost    | KES 80,000,000.00                                                                                                                          |
| Attachment               | Digital-health-training-needs-assessment.pdf \| 1.8 MB                                                                                     |

### Decision area

Prompt: Confirm whether this need should be taken forward for departmental procurement planning.

Visible actions: Return for correction | Do not take forward | Accept for planning

Do not show editable Need fields, a reason field on the base screen, scoring, Finance approval, procurement method, Plan allocation, Requisition controls, Tender controls or an approval stepper.

# 8\. Implementation controls

## 8.1 Canonical routes and queries

| **Route**                                   | **Purpose**                                    |
| ------------------------------------------- | ---------------------------------------------- |
| /departmental-needs                         | Role-aware workspace and scoped list.          |
| /departmental-needs/new                     | Create a Need within resolved scope.           |
| /departmental-needs/{need_reference}        | Read-only detail or state-appropriate view.    |
| /departmental-needs/{need_reference}/edit   | Edit an owned Draft or Returned Need.          |
| /departmental-needs/{need_reference}/review | Review a Submitted Need within reviewer scope. |

## 8.2 Commands

| **Command**                         | **Required controls**                                                                         |
| ----------------------------------- | --------------------------------------------------------------------------------------------- |
| CreateDepartmentalNeedDraft         | Scope, title, intake window, idempotency and audit.                                           |
| UpdateDepartmentalNeedDraft         | Ownership, state, scope, record_version, validation and audit.                                |
| SubmitForDepartmentalReview         | Full validation, maker-checker route, snapshot, state change, work dispatch and notification. |
| ReturnDepartmentalNeedForCorrection | Reviewer assignment, non-self decision, reason, state, audit and notification.                |
| AcceptDepartmentalNeedForPlanning   | Reviewer assignment, non-self decision, accepted snapshot, audit and notification.            |
| DoNotTakeDepartmentalNeedForward    | Reviewer assignment, non-self decision, reason, terminal state, audit and notification.       |
| WithdrawDepartmentalNeed            | Creator ownership, Draft or Returned state, record_version and audit.                         |

## 8.3 Capabilities

- departmental_needs.create
- departmental_needs.edit_own
- departmental_needs.submit
- departmental_needs.review
- departmental_needs.read_accepted_for_planning
- departmental_needs.support_read

Capabilities are necessary but never sufficient; the service must also evaluate current assignment, record scope, state, creator/reviewer separation and target-year intake rules.

## 8.4 Transaction, audit and security rules

- All commands run in one database transaction and use a caller-provided idempotency key unique to actor and command type.
- Outbox events for work routing and notifications are committed in the same transaction and dispatched asynchronously.
- record_version is checked on update and decision commands; conflicts return the current version without overwriting data.
- Server-side queries enforce scope before object materialization; UI filters never broaden access.
- Audit events are append-only and capture actor, effective assignment, request identifier, source IP/session, command, scope, reason and before/after state hashes.
- Attachments are served using short-lived authorized access, never public object URLs.
- System Administrator support reads require an explicit support reason and are separately audited; no operational command is inferred from the administrator role.

# 9\. Clean-build implementation constraint

**Mandatory:** Build Departmental Needs from a fresh schema and fresh seed data. There is no migration, preservation or compatibility requirement for the legacy Demands implementation.

- Do not import, copy, adapt or reference legacy Demand models, tables, services, repositories, routes, permissions, states, serializers, forms, tests or fixtures.
- Do not create a compatibility adapter, legacy alias, dual read/write path, bridge table or translation layer.
- Do not expose /demands or redirect it to /departmental-needs. The only canonical user-facing route is /departmental-needs.
- Do not retain legacy identifiers, field names or status values in the new schema or API.
- Create fresh database migrations only for the Departmental Needs model defined by NDS-CHG-001 and this unit.
- Bootstrap only the approved clean seed fixtures in section 10. Existing local data may be discarded by the implementation reset procedure.
- Tests must fail if legacy Demand modules, routes, database objects or fixtures are present in the fresh build.

# 10\. Deterministic seed data

## 10.1 Assignments

| **User**                         | **Role / assignment**        | **Scope**                                                |
| -------------------------------- | ---------------------------- | -------------------------------------------------------- |
| <grace.wanjiku@moh.example.test> | Departmental Need Requester  | MOH / Directorate of Digital Health and Policy / 2027/28 |
| <peter.kimani@moh.example.test>  | Head of User Department      | MOH / Directorate of Digital Health and Policy / 2027/28 |
| <julia.njeri@moh.example.test>   | Departmental Review Delegate | MOH / Directorate of Digital Health and Policy / 2027/28 |
| <mercy.kilonzo@moh.example.test> | Procurement Planner          | MOH / 2027/28; accepted Needs read-only                  |

## 10.2 Needs

| **Reference**     | **Title**                                              | **State**             | **Owner / decision fixture**                                      |
| ----------------- | ------------------------------------------------------ | --------------------- | ----------------------------------------------------------------- |
| NDS-MOH-2027-0001 | National digital health infrastructure upgrade         | Accepted for planning | Grace Wanjiku / accepted by Dr Peter Kimani                       |
| NDS-MOH-2027-0002 | Digital health technical staff certification programme | Submitted             | Grace Wanjiku / awaiting departmental review                      |
| NDS-MOH-2027-0003 | Regional health-facility connectivity equipment        | Returned              | Grace Wanjiku / return fixture in NDS-UI-02B                      |
| NDS-MOH-2027-0004 | County laboratory information-system user licences     | Draft                 | Grace Wanjiku / 300 / Other: Licence / KES 18,000,000             |
| NDS-MOH-2027-0005 | Replacement of recently supplied network switches      | Not taken forward     | Reason: Existing central stock is sufficient for the target year. |
| NDS-MOH-2027-0006 | Temporary document digitisation support                | Withdrawn             | Grace Wanjiku / withdrawn before departmental review              |

Seed timestamps are fixed UTC instants that render to the exact East Africa Time values used in the static screens. Seed scripts create no Plan allocation, Procurement Requisition, Tender or legacy Demand record.

# 11\. Acceptance criteria

| **ID**     | **Acceptance criterion**                                                                                                 |
| ---------- | ------------------------------------------------------------------------------------------------------------------------ |
| NDS-AC-020 | A valid requester assignment can create a draft at /departmental-needs/new.                                              |
| NDS-AC-021 | No assignment blocks creation; multiple assignments require explicit selection.                                          |
| NDS-AC-022 | The first successful save creates one immutable canonical Need reference.                                                |
| NDS-AC-023 | A partial draft can be saved after context and title are valid.                                                          |
| NDS-AC-024 | Submit rejects a missing justification, missing complete item, incomplete row, out-of-year date or non-clean attachment. |
| NDS-AC-025 | Submit rechecks current assignment and intake state on the server.                                                       |
| NDS-AC-026 | A successful submit creates one immutable revision snapshot and one review work item.                                    |
| NDS-AC-027 | Submitted content is read-only to the requester.                                                                         |
| NDS-AC-028 | A submitter cannot make the departmental decision on their own Need.                                                     |
| NDS-AC-029 | Return requires a reason, preserves the submitted snapshot and unlocks the requester.                                    |
| NDS-AC-030 | Resubmission increments the revision number without modifying earlier snapshots.                                         |
| NDS-AC-031 | Acceptance creates an accepted snapshot but no Plan Item or budget effect.                                               |
| NDS-AC-032 | Do not take forward requires a reason and creates a terminal state.                                                      |
| NDS-AC-033 | Only Draft and Returned Needs may be withdrawn by the requester.                                                         |
| NDS-AC-034 | Duplicate command delivery creates no duplicate state change, snapshot, work item or notification.                       |
| NDS-AC-035 | A stale record_version fails without overwriting current data.                                                           |
| NDS-AC-036 | A cross-PE, cross-department or expired assignment is denied server-side.                                                |
| NDS-AC-037 | The Budget Officer, Accounting Officer and System Administrator have only the prescribed audited read access.            |
| NDS-AC-038 | NDS-UI-02A, B and C render their exact fixtures and exclusions.                                                          |
| NDS-AC-039 | No screen captures procurement type, method, BOQ, formal specification, budget confirmation or tender data.              |
| NDS-AC-040 | A fresh environment boots from approved seed data without importing legacy data.                                         |
| NDS-AC-041 | The build contains no /demands route, compatibility layer or legacy Demand schema object.                                |
| NDS-AC-042 | All state-changing and support-read actions produce complete immutable audit events.                                     |

# 12\. Role-based smoke scenarios

| **Scenario**                                          | **Expected result**                                                      |
| ----------------------------------------------------- | ------------------------------------------------------------------------ |
| Requester creates and saves NDS-MOH-2027-0004         | Draft persists with canonical reference; no review work exists.          |
| Requester submits complete NDS-MOH-2027-0002          | Revision 1 snapshot, Submitted state and one scoped review item.         |
| Requester submits an incomplete item row              | Stable validation error; no state, snapshot or notification side effect. |
| HoUD opens NDS-MOH-2027-0002                          | Read-only NDS-UI-02C fixture and permitted decision actions.             |
| HoUD attempts to decide their own submitted Need      | Denied by maker-checker control.                                         |
| HoUD returns NDS-MOH-2027-0003                        | Mandatory reason recorded; requester can edit and resubmit.              |
| Requester resubmits returned Need                     | Revision increments; prior snapshot remains unchanged.                   |
| Delegate accepts a submitted Need                     | Accepted snapshot created; Planner can read it; no Plan Item exists.     |
| Budget Officer opens a relevant Need                  | Read-only; no review or funding action.                                  |
| System Administrator opens a Need with support reason | Audited read-only view; no operational action.                           |
| Requester crosses PE or department scope              | Not found or denied without data disclosure.                             |
| Client repeats the same submit request                | Original result returned; no duplicate effect.                           |
| Two tabs save the same record version                 | Second save receives a conflict with current version.                    |
| User requests /demands                                | No route exists; no redirect or compatibility behavior.                  |

# 13\. Delivery and approval gate

NDS-CHG-002 is ready for implementation only after product approval of its requirements, exact static screens, implementation controls, clean-build rule, seed fixtures and acceptance criteria as one indivisible unit.

The next planned change unit is NDS-CHG-003 — Departmental Needs workspace, queues, filtering and role-based landing behavior.

# 14\. Authoritative sources

**Public Procurement and Asset Disposal Act, 2015 (Kenya Law):** [official consolidated text](https://new.kenyalaw.org/akn/ke/act/2015/33/eng@2022-12-31)

**Public Procurement and Asset Disposal Regulations, 2020 (Kenya Law):** [official consolidated text](https://new.kenyalaw.org/akn/ke/act/ln/2020/69/eng@2022-12-31)